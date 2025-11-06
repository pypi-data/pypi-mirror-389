# https://developer.valvesoftware.com/wiki/Server_queries
from dataclasses import dataclass
from enum import IntEnum

from little_a2s.enums import _EnumReprMixin


class HeaderType(_EnumReprMixin, IntEnum):
    SIMPLE = -1
    MULTI = -2


@dataclass(kw_only=True)
class Compression:
    """The compression header for Source games. Mostly present in ~2006-era engines."""

    size: int
    checksum: int


@dataclass(kw_only=True)
class Header:
    """An A2S response header."""


@dataclass(kw_only=True)
class SimpleHeader(Header):
    """An single-packet A2S response header."""


@dataclass(kw_only=True)
class MultiHeader(Header):
    """A multi-packet A2S response header for Source games."""

    id: int
    current: int
    total: int
    size: int  # Some games omit this field!
    compressed: Compression | None


@dataclass(kw_only=True)
class MultiGoldsourceHeader(Header):
    """A multi-packet A2S response header for Goldsource games."""

    id: int
    current: int
    total: int
