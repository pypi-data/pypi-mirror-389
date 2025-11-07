"""This is an automatically generated stub for `x.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator
from contextlib import contextmanager
from io import BufferedWriter
from typing import Any, BinaryIO, Protocol

class X(Protocol):
    class MResult(Awaitable[MResult], Protocol):
        t: str

    class MResultsBuilder(Protocol):
        t: str

    class MCallContext(Protocol):
        results: X.MResultsBuilder

    def m(self, i: int) -> MResult: ...
    class MRequest(Protocol):
        i: int
        def send(self) -> X.MResult: ...

    def m_request(self) -> MRequest: ...
    @classmethod
    def _new_client(cls, server: X.Server) -> X: ...
    class Server:
        def m(
            self, i: int, _context: X.MCallContext, **kwargs: Any
        ) -> Awaitable[str]: ...

class S:
    @property
    def c(self) -> X: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[SReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> SReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        c: X | X.Server | None = None,
    ) -> SBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> SReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> SReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class SReader(S):
    def as_builder(self) -> SBuilder: ...

class SBuilder(S):
    @property
    def c(self) -> X: ...
    @c.setter
    def c(self, value: X | X.Server) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> SBuilder: ...
    def copy(self) -> SBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> SReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class Y(Protocol):
    class MResultsBuilder(Protocol): ...

    class MCallContext(Protocol):
        results: Y.MResultsBuilder

    def m(self, hello: str) -> Awaitable[None]: ...
    class MRequest(Protocol):
        hello: str
        def send(self) -> Awaitable[None]: ...

    def m_request(self) -> MRequest: ...
    @classmethod
    def _new_client(cls, server: Y.Server) -> Y: ...
    class Server:
        def m(
            self, hello: str, _context: Y.MCallContext, **kwargs: Any
        ) -> Awaitable[None]: ...

class Z(Protocol):
    class MResult(Awaitable[MResult], Protocol):
        r: float

    class MResultsBuilder(Protocol):
        r: float

    class MCallContext(Protocol):
        results: Z.MResultsBuilder

    def m(self, n: int) -> MResult: ...
    class MRequest(Protocol):
        n: int
        def send(self) -> Z.MResult: ...

    def m_request(self) -> MRequest: ...
    @classmethod
    def _new_client(cls, server: Z.Server) -> Z: ...
    class Server:
        def m(
            self, n: int, _context: Z.MCallContext, **kwargs: Any
        ) -> Awaitable[float]: ...
