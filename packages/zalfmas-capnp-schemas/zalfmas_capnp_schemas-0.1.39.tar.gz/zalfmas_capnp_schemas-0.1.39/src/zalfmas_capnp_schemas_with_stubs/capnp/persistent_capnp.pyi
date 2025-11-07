"""This is an automatically generated stub for `persistent.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator
from contextlib import contextmanager
from io import BufferedWriter
from typing import Any, BinaryIO, Generic, NamedTuple, Protocol, TypeVar

Persistent_Owner = TypeVar("Persistent_Owner")
Persistent_SturdyRef = TypeVar("Persistent_SturdyRef")

class Persistent(Protocol):
    class SaveParams(Generic[Persistent_Owner]):
        @property
        def sealFor(self) -> Any: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Persistent.SaveParamsReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Persistent.SaveParamsReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            sealFor: Any | None = None,
        ) -> Persistent.SaveParamsBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Persistent.SaveParamsReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Persistent.SaveParamsReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class SaveParamsReader(Persistent.SaveParams, Generic[Persistent_Owner]):
        def as_builder(self) -> Persistent.SaveParamsBuilder: ...

    class SaveParamsBuilder(Persistent.SaveParams, Generic[Persistent_Owner]):
        @property
        def sealFor(self) -> Any: ...
        @sealFor.setter
        def sealFor(self, value: Any) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Persistent.SaveParamsBuilder: ...
        def copy(self) -> Persistent.SaveParamsBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Persistent.SaveParamsReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class SaveResults(Generic[Persistent_SturdyRef]):
        @property
        def sturdyRef(self) -> Persistent_SturdyRef: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Persistent.SaveResultsReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Persistent.SaveResultsReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            sturdyRef: Persistent_SturdyRef | None = None,
        ) -> Persistent.SaveResultsBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Persistent.SaveResultsReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Persistent.SaveResultsReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class SaveResultsReader(Persistent.SaveResults, Generic[Persistent_SturdyRef]):
        def as_builder(self) -> Persistent.SaveResultsBuilder: ...

    class SaveResultsBuilder(Persistent.SaveResults, Generic[Persistent_SturdyRef]):
        @property
        def sturdyRef(self) -> Persistent_SturdyRef: ...
        @sturdyRef.setter
        def sturdyRef(self, value: Persistent_SturdyRef) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Persistent.SaveResultsBuilder: ...
        def copy(self) -> Persistent.SaveResultsBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Persistent.SaveResultsReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class SaveResult(Protocol):
        sturdyRef: Any

    class SaveCallContext(Protocol):
        results: Persistent.SaveResult

    def save(self, sealFor: Any) -> Awaitable[Persistent.SaveResult]: ...
    class SaveRequest(Protocol):
        sealFor: Any
        def send(self) -> Awaitable[Persistent.SaveResult]: ...

    def save_request(self) -> SaveRequest: ...
    @classmethod
    def _new_client(cls, server: Persistent.Server) -> Persistent: ...
    class Server:
        class SaveResult(NamedTuple):
            sturdyRef: Any

        def save(
            self, sealFor: Any, _context: Persistent.SaveCallContext, **kwargs: Any
        ) -> Awaitable[Persistent.Server.SaveResult]: ...
