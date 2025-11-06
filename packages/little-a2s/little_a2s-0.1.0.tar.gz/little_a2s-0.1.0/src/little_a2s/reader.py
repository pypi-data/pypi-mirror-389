import struct
from io import BytesIO
from typing import Literal, Protocol, runtime_checkable


@runtime_checkable
class Readable(Protocol):
    def read(self, n: int = -1, /) -> bytes: ...


class Reader:
    """A simple reader for parsing serialized data."""

    def __init__(self, data: bytes | Readable) -> None:
        if not isinstance(data, Readable):
            data = BytesIO(data)

        self._file = data

    def read(self, n: int = -1, /) -> bytes:
        data = self._file.read(n)
        if n >= 0 and len(data) < n:
            raise EOFError
        return data

    def read_byte(self) -> int:
        return self.read(1)[0]

    def read_char(self) -> str:
        return self.read(1).decode("ascii")

    def read_null(self) -> Literal[0]:
        n = self.read_byte()
        if n != 0:
            raise ValueError(f"Expected null byte, got {n!r}")
        return n

    def read_short(self) -> int:
        return int.from_bytes(self.read(2), "little", signed=True)

    def read_ushort(self) -> int:
        return int.from_bytes(self.read(2), "little")

    def read_long(self) -> int:
        return int.from_bytes(self.read(4), "little", signed=True)

    def read_ulong(self) -> int:
        return int.from_bytes(self.read(4), "little")

    def read_float(self) -> float:
        return struct.unpack("<f", self.read(4))[0]

    def read_uint64(self) -> int:
        return int.from_bytes(self.read(8), "little")

    def read_null_string(self) -> bytes:
        return self.read_until(0)

    def read_null_utf8(self) -> str:
        s = self.read_null_string()
        return s.decode()

    def read_until(self, sep: int) -> bytes:
        """Read until the sep character is found and return all bytes before sep."""
        if not 0x00 <= sep < 0xFF:
            raise ValueError(f"Expected sep in range [0, 255], got {sep!r}")

        # FIXME: is this hot loop slow?
        data = bytearray()
        while (char := self.read_byte()) != sep:
            data.append(char)

        return bytes(data)

    def read_varchar1(self) -> bytes:
        length = self.read_byte()
        return self.read(length)

    def read_varchar2(self) -> bytes:
        length = self.read_ushort()
        return self.read(length)

    def read_varchar4(self) -> bytes:
        length = self.read_ulong()
        return self.read(length)

    def read_varchar8(self) -> bytes:
        length = self.read_uint64()
        return self.read(length)
