"""This is an automatically generated stub for `service.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator, Sequence
from contextlib import contextmanager
from io import BufferedWriter
from typing import Any, BinaryIO, Generic, Literal, NamedTuple, Protocol, TypeVar

from capnp import _DynamicListBuilder

from .common_capnp import Identifiable, Pair, PairBuilder, PairReader

Factory_Payload = TypeVar("Factory_Payload")

class Admin(Identifiable, Protocol):
    class HeartbeatResultsBuilder(Protocol): ...

    class HeartbeatCallContext(Protocol):
        results: Admin.HeartbeatResultsBuilder

    def heartbeat(self) -> Awaitable[None]: ...
    class HeartbeatRequest(Protocol):
        def send(self) -> Awaitable[None]: ...

    def heartbeat_request(self) -> HeartbeatRequest: ...
    class SettimeoutResultsBuilder(Protocol): ...

    class SettimeoutCallContext(Protocol):
        results: Admin.SettimeoutResultsBuilder

    def setTimeout(self, seconds: int) -> Awaitable[None]: ...
    class SettimeoutRequest(Protocol):
        seconds: int
        def send(self) -> Awaitable[None]: ...

    def setTimeout_request(self) -> SettimeoutRequest: ...
    class StopResultsBuilder(Protocol): ...

    class StopCallContext(Protocol):
        results: Admin.StopResultsBuilder

    def stop(self) -> Awaitable[None]: ...
    class StopRequest(Protocol):
        def send(self) -> Awaitable[None]: ...

    def stop_request(self) -> StopRequest: ...
    class IdentitiesResult(Awaitable[IdentitiesResult], Protocol):
        infos: Any

    class IdentitiesResultsBuilder(Protocol):
        infos: Any

    class IdentitiesCallContext(Protocol):
        results: Admin.IdentitiesResultsBuilder

    def identities(self) -> IdentitiesResult: ...
    class IdentitiesRequest(Protocol):
        def send(self) -> Admin.IdentitiesResult: ...

    def identities_request(self) -> IdentitiesRequest: ...
    class UpdateidentityResultsBuilder(Protocol): ...

    class UpdateidentityCallContext(Protocol):
        results: Admin.UpdateidentityResultsBuilder

    def updateIdentity(self, oldId: str, newInfo: Any) -> Awaitable[None]: ...
    class UpdateidentityRequest(Protocol):
        oldId: str
        newInfo: Any
        def send(self) -> Awaitable[None]: ...

    def updateIdentity_request(self) -> UpdateidentityRequest: ...
    @classmethod
    def _new_client(cls, server: Admin.Server | Identifiable.Server) -> Admin: ...
    class Server(Identifiable.Server):
        def heartbeat(
            self, _context: Admin.HeartbeatCallContext, **kwargs: Any
        ) -> Awaitable[None]: ...
        def setTimeout(
            self, seconds: int, _context: Admin.SettimeoutCallContext, **kwargs: Any
        ) -> Awaitable[None]: ...
        def stop(
            self, _context: Admin.StopCallContext, **kwargs: Any
        ) -> Awaitable[None]: ...
        def identities(
            self, _context: Admin.IdentitiesCallContext, **kwargs: Any
        ) -> Awaitable[Any]: ...
        def updateIdentity(
            self,
            oldId: str,
            newInfo: Any,
            _context: Admin.UpdateidentityCallContext,
            **kwargs: Any,
        ) -> Awaitable[None]: ...

class SimpleFactory(Identifiable, Protocol):
    class CreateResult(Awaitable[CreateResult], Protocol):
        caps: Sequence[Identifiable]

    class CreateResultsBuilder(Protocol):
        caps: Sequence[Identifiable]

    class CreateCallContext(Protocol):
        results: SimpleFactory.CreateResultsBuilder

    def create(self) -> CreateResult: ...
    class CreateRequest(Protocol):
        def send(self) -> SimpleFactory.CreateResult: ...

    def create_request(self) -> CreateRequest: ...
    @classmethod
    def _new_client(
        cls, server: SimpleFactory.Server | Identifiable.Server
    ) -> SimpleFactory: ...
    class Server(Identifiable.Server):
        def create(
            self, _context: SimpleFactory.CreateCallContext, **kwargs: Any
        ) -> Awaitable[Sequence[Identifiable]]: ...

class Factory(Identifiable, Protocol):
    class CreateParams(Generic[Factory_Payload]):
        @property
        def timeoutSeconds(self) -> int: ...
        @property
        def interfaceNameToRegistrySR(self) -> Sequence[Pair]: ...
        @property
        def msgPayload(self) -> Factory_Payload: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Factory.CreateParamsReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Factory.CreateParamsReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            timeoutSeconds: int | None = None,
            interfaceNameToRegistrySR: Sequence[PairBuilder]
            | Sequence[dict[str, Any]]
            | None = None,
            msgPayload: Factory_Payload | None = None,
        ) -> Factory.CreateParamsBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Factory.CreateParamsReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Factory.CreateParamsReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class CreateParamsReader(Factory.CreateParams, Generic[Factory_Payload]):
        @property
        def interfaceNameToRegistrySR(self) -> Sequence[PairReader]: ...
        def as_builder(self) -> Factory.CreateParamsBuilder: ...

    class CreateParamsBuilder(Factory.CreateParams, Generic[Factory_Payload]):
        @property
        def timeoutSeconds(self) -> int: ...
        @timeoutSeconds.setter
        def timeoutSeconds(self, value: int) -> None: ...
        @property
        def interfaceNameToRegistrySR(self) -> Sequence[PairBuilder]: ...
        @interfaceNameToRegistrySR.setter
        def interfaceNameToRegistrySR(
            self,
            value: Sequence[Pair | PairBuilder | PairReader] | Sequence[dict[str, Any]],
        ) -> None: ...
        @property
        def msgPayload(self) -> Factory_Payload: ...
        @msgPayload.setter
        def msgPayload(self, value: Factory_Payload) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Factory.CreateParamsBuilder: ...
        def init(
            self, name: Literal["interfaceNameToRegistrySR"], size: int = ...
        ) -> _DynamicListBuilder[PairBuilder]: ...
        def copy(self) -> Factory.CreateParamsBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Factory.CreateParamsReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class AccessInfo:
        @property
        def adminCap(self) -> Any: ...
        @property
        def serviceCaps(self) -> Sequence[Identifiable]: ...
        @property
        def error(self) -> str: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Factory.AccessInfoReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Factory.AccessInfoReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            adminCap: Any | None = None,
            serviceCaps: Sequence[Identifiable] | None = None,
            error: str | None = None,
        ) -> Factory.AccessInfoBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Factory.AccessInfoReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Factory.AccessInfoReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class AccessInfoReader(Factory.AccessInfo):
        def as_builder(self) -> Factory.AccessInfoBuilder: ...

    class AccessInfoBuilder(Factory.AccessInfo):
        @property
        def adminCap(self) -> Any: ...
        @adminCap.setter
        def adminCap(self, value: Any) -> None: ...
        @property
        def serviceCaps(self) -> Sequence[Identifiable]: ...
        @serviceCaps.setter
        def serviceCaps(self, value: Sequence[Identifiable]) -> None: ...
        @property
        def error(self) -> str: ...
        @error.setter
        def error(self, value: str) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Factory.AccessInfoBuilder: ...
        def init(
            self, name: Literal["serviceCaps"], size: int = ...
        ) -> _DynamicListBuilder[Identifiable]: ...
        def copy(self) -> Factory.AccessInfoBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Factory.AccessInfoReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class CreateResult(Protocol):
        adminCap: Any
        serviceCaps: Sequence[Identifiable]
        error: str

    class CreateCallContext(Protocol):
        results: Factory.CreateResult

    def create(
        self,
        timeoutSeconds: int,
        interfaceNameToRegistrySR: Sequence[Pair[str, str]],
        msgPayload: Any,
    ) -> Awaitable[Factory.CreateResult]: ...
    class CreateRequest(Protocol):
        timeoutSeconds: int
        interfaceNameToRegistrySR: Sequence[Pair[str, str]]
        msgPayload: Any
        def send(self) -> Awaitable[Factory.CreateResult]: ...

    def create_request(self) -> CreateRequest: ...
    class ServiceinterfacenamesResult(Awaitable[ServiceinterfacenamesResult], Protocol):
        names: Sequence[str]

    class ServiceinterfacenamesResultsBuilder(Protocol):
        names: Sequence[str]

    class ServiceinterfacenamesCallContext(Protocol):
        results: Factory.ServiceinterfacenamesResultsBuilder

    def serviceInterfaceNames(self) -> ServiceinterfacenamesResult: ...
    class ServiceinterfacenamesRequest(Protocol):
        def send(self) -> Factory.ServiceinterfacenamesResult: ...

    def serviceInterfaceNames_request(self) -> ServiceinterfacenamesRequest: ...
    @classmethod
    def _new_client(cls, server: Factory.Server | Identifiable.Server) -> Factory: ...
    class Server(Identifiable.Server):
        class CreateResult(NamedTuple):
            adminCap: Any
            serviceCaps: Sequence[Identifiable]
            error: str

        def create(
            self,
            timeoutSeconds: int,
            interfaceNameToRegistrySR: Sequence[Pair[str, str]],
            msgPayload: Any,
            _context: Factory.CreateCallContext,
            **kwargs: Any,
        ) -> Awaitable[Factory.Server.CreateResult]: ...
        def serviceInterfaceNames(
            self, _context: Factory.ServiceinterfacenamesCallContext, **kwargs: Any
        ) -> Awaitable[Sequence[str]]: ...

class Stoppable(Protocol):
    class StopResult(Awaitable[StopResult], Protocol):
        success: bool

    class StopResultsBuilder(Protocol):
        success: bool

    class StopCallContext(Protocol):
        results: Stoppable.StopResultsBuilder

    def stop(self) -> StopResult: ...
    class StopRequest(Protocol):
        def send(self) -> Stoppable.StopResult: ...

    def stop_request(self) -> StopRequest: ...
    @classmethod
    def _new_client(cls, server: Stoppable.Server) -> Stoppable: ...
    class Server:
        def stop(
            self, _context: Stoppable.StopCallContext, **kwargs: Any
        ) -> Awaitable[bool]: ...
