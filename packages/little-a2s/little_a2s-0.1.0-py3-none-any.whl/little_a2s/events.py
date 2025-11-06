from dataclasses import dataclass
from enum import IntEnum
from typing import Self

from little_a2s.enums import _EnumReprMixin
from little_a2s.reader import Reader


# ClientEventInfo types
class ServerType(_EnumReprMixin, IntEnum):
    DEDICATED = ord("d")
    LISTEN = ord("l")
    RELAY = ord("p")


class Environment(_EnumReprMixin, IntEnum):
    LINUX = ord("l")
    WINDOWS = ord("w")
    MACOS_M = ord("m")  # Ergh, can this be combined?
    MACOS_O = ord("o")


class Visibility(_EnumReprMixin, IntEnum):
    PUBLIC = 0
    PRIVATE = 1


class VAC(_EnumReprMixin, IntEnum):
    INSECURE = 0
    SECURE = 1


@dataclass(kw_only=True)
class ExtraInfo:
    """Extra data included with an A2S_INFO response."""

    port: int | None = None
    steam_id: int | None = None
    spectator_port: int | None = None
    spectator_name: str | None = None
    keywords: str | None = None
    game_id: int | None = None

    @classmethod
    def from_reader(cls, reader: Reader, flag: int) -> Self:
        extra = cls()
        if flag & 0x80:
            extra.port = reader.read_ushort()
        if flag & 0x10:
            extra.steam_id = reader.read_uint64()
        if flag & 0x40:
            extra.spectator_port = reader.read_ushort()
            extra.spectator_name = reader.read_null_utf8()
        if flag & 0x20:
            extra.keywords = reader.read_null_utf8()
        if flag & 0x01:
            extra.game_id = reader.read_uint64()
        return extra


# ClientEventGoldsourceInfo types
class GoldsourceModType(_EnumReprMixin, IntEnum):
    SINGLE_AND_MULTIPLAYER = 0
    MULTIPLAYER_ONLY = 1


class GoldsourceModDLL(_EnumReprMixin, IntEnum):
    NATIVE = 0
    """This mod uses the Half-Life DLL."""

    EXTENSION = 1
    """This mod provides its own DLL."""


@dataclass(kw_only=True)
class GoldsourceMod:
    """Extra data included with an A2S_INFO response."""

    link: str
    download_link: str
    version: int
    size: int
    type: GoldsourceModType
    dll: GoldsourceModDLL

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        link = reader.read_null_utf8()
        download_link = reader.read_null_utf8()
        reader.read_null()
        version = reader.read_ulong()
        size = reader.read_ulong()
        type = GoldsourceModType(reader.read_byte())
        dll = GoldsourceModDLL(reader.read_byte())

        return cls(
            link=link,
            download_link=download_link,
            version=version,
            size=size,
            type=type,
            dll=dll,
        )


# ClientEventPlayer types
@dataclass(kw_only=True)
class Player:
    """A player returned in the A2S_PLAYER response."""

    index: int
    name: str
    score: int
    duration: float


# Event types
@dataclass(kw_only=True)
class Event:
    """The base class for all A2S protocol events."""


@dataclass(kw_only=True)
class ClientEvent(Event):
    """An A2S client protocol event."""


@dataclass(kw_only=True)
class ClientEventInfo(ClientEvent):
    """An A2S_INFO client protocol event.

    This follows the Source format. For the Goldsource equivalent,
    see :class:`ClientEventGoldsourceInfo`.

    """

    protocol: int
    name: str
    map: str
    folder: str
    game: str
    id: int
    players: int
    max_players: int
    bots: int
    type: ServerType
    environment: Environment
    visibility: Visibility
    vac: VAC
    version: str
    extra: ExtraInfo | None

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        protocol = reader.read_byte()
        name = reader.read_null_utf8()
        map = reader.read_null_utf8()
        folder = reader.read_null_utf8()
        game = reader.read_null_utf8()
        id = reader.read_ushort()
        players = reader.read_byte()
        max_players = reader.read_byte()
        bots = reader.read_byte()
        type = ServerType(reader.read_byte())
        environment = Environment(reader.read_byte())
        visibility = Visibility(reader.read_byte())
        vac = VAC(reader.read_byte())
        # Extra data will be here for The Ship
        version = reader.read_null_utf8()

        try:
            extra_flag = reader.read_byte()
        except EOFError:
            extra = None
        else:
            extra = ExtraInfo.from_reader(reader, extra_flag)

        return cls(
            protocol=protocol,
            name=name,
            map=map,
            folder=folder,
            game=game,
            id=id,
            players=players,
            max_players=max_players,
            bots=bots,
            type=type,
            environment=environment,
            visibility=visibility,
            vac=vac,
            version=version,
            extra=extra,
        )


@dataclass(kw_only=True)
class ClientEventGoldsourceInfo(ClientEvent):
    """An A2S_INFO Goldsource client protocol event."""

    address: str
    name: str
    map: str
    folder: str
    game: str
    players: int
    max_players: int
    protocol: int
    type: ServerType
    environment: Environment
    visibility: Visibility
    mod: GoldsourceMod | None
    vac: VAC
    bots: int

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        address = reader.read_null_utf8()
        name = reader.read_null_utf8()
        map = reader.read_null_utf8()
        folder = reader.read_null_utf8()
        game = reader.read_null_utf8()
        players = reader.read_byte()
        max_players = reader.read_byte()
        protocol = reader.read_byte()
        type = ServerType(ord(reader.read_char().lower()))
        environment = Environment(ord(reader.read_char().lower()))
        visibility = Visibility(reader.read_byte())
        mod = GoldsourceMod.from_reader(reader) if reader.read_byte() == 1 else None
        vac = VAC(reader.read_byte())
        bots = reader.read_byte()

        return cls(
            address=address,
            name=name,
            map=map,
            folder=folder,
            game=game,
            players=players,
            max_players=max_players,
            protocol=protocol,
            type=type,
            environment=environment,
            visibility=visibility,
            mod=mod,
            vac=vac,
            bots=bots,
        )


@dataclass(kw_only=True)
class ClientEventPlayers(ClientEvent):
    """An A2S_PLAYER client protocol event."""

    players: list[Player]

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        players = []
        for _ in range(reader.read_byte()):
            index = reader.read_byte()
            name = reader.read_null_utf8()
            score = reader.read_long()
            duration = reader.read_float()
            # Extra data will be here for The Ship
            player = Player(index=index, name=name, score=score, duration=duration)
            players.append(player)

        return cls(players=players)


@dataclass(kw_only=True)
class ClientEventRules(ClientEvent):
    """An A2S_RULES client protocol event."""

    # While documented to be strings, some games might provide binary data
    # *cough Arma* which may not decode correctly as UTF-8.
    rules: dict[bytes, bytes]

    def decode(self) -> dict[str, str]:
        """Return all rules decoded in UTF-8."""
        return {k.decode(): v.decode() for k, v in self.rules.items()}

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        rules = {}
        for _ in range(reader.read_byte()):
            name = reader.read_null_string()
            value = reader.read_null_string()
            rules[name] = value

        return cls(rules=rules)


@dataclass(kw_only=True)
class ClientEventChallenge(ClientEvent):
    """An S2C_CHALLENGE client protocol event."""

    challenge: int

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        return cls(challenge=reader.read_long())
