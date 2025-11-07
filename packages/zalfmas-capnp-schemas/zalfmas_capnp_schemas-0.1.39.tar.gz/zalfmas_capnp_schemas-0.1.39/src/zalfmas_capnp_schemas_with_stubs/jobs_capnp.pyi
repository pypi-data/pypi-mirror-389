"""This is an automatically generated stub for `jobs.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator
from contextlib import contextmanager
from io import BufferedWriter
from typing import Any, BinaryIO, Generic, Protocol, TypeVar

from .common_capnp import Identifiable
from .persistence_capnp import Persistent

_Payload = TypeVar("_Payload")

class Job(Generic[_Payload]):
    @property
    def data(self) -> _Payload: ...
    @property
    def noFurtherJobs(self) -> bool: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[JobReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> JobReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        data: _Payload | None = None,
        noFurtherJobs: bool | None = None,
    ) -> JobBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> JobReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> JobReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class JobReader(Job, Generic[_Payload]):
    def as_builder(self) -> JobBuilder: ...

class JobBuilder(Job, Generic[_Payload]):
    @property
    def data(self) -> _Payload: ...
    @data.setter
    def data(self, value: _Payload) -> None: ...
    @property
    def noFurtherJobs(self) -> bool: ...
    @noFurtherJobs.setter
    def noFurtherJobs(self, value: bool) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> JobBuilder: ...
    def copy(self) -> JobBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> JobReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class Service(Identifiable, Persistent, Protocol):
    class NextjobResult(Awaitable[NextjobResult], Protocol):
        job: JobReader

    class NextjobResultsBuilder(Protocol):
        job: JobBuilder

    class NextjobCallContext(Protocol):
        results: Service.NextjobResultsBuilder

    def nextJob(self) -> NextjobResult: ...
    class NextjobRequest(Protocol):
        def send(self) -> Service.NextjobResult: ...

    def nextJob_request(self) -> NextjobRequest: ...
    @classmethod
    def _new_client(
        cls, server: Service.Server | Identifiable.Server | Persistent.Server
    ) -> Service: ...
    class Server(Identifiable.Server, Persistent.Server):
        def nextJob(
            self, _context: Service.NextjobCallContext, **kwargs: Any
        ) -> Awaitable[Job]: ...
