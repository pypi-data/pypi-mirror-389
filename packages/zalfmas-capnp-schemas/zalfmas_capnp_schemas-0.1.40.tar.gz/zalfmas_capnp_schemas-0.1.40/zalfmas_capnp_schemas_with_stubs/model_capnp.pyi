"""This is an automatically generated stub for `model.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator, Sequence
from contextlib import contextmanager
from enum import Enum
from io import BufferedWriter
from typing import (
    Any,
    BinaryIO,
    Generic,
    Literal,
    NamedTuple,
    Protocol,
    TypeVar,
    overload,
)

from capnp import _DynamicListBuilder

from .climate_capnp import TimeSeries
from .common_capnp import (
    Identifiable,
    IdInformation,
    IdInformationBuilder,
    IdInformationReader,
)
from .management_capnp import Event, EventBuilder, EventReader
from .persistence_capnp import Persistent
from .service_capnp import Stoppable
from .soil_capnp import Profile

_RestInput = TypeVar("_RestInput")

class XYResult:
    @property
    def xs(self) -> Sequence[float]: ...
    @property
    def ys(self) -> Sequence[float]: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[XYResultReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> XYResultReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        xs: Sequence[float] | None = None,
        ys: Sequence[float] | None = None,
    ) -> XYResultBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> XYResultReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> XYResultReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class XYResultReader(XYResult):
    def as_builder(self) -> XYResultBuilder: ...

class XYResultBuilder(XYResult):
    @property
    def xs(self) -> Sequence[float]: ...
    @xs.setter
    def xs(self, value: Sequence[float]) -> None: ...
    @property
    def ys(self) -> Sequence[float]: ...
    @ys.setter
    def ys(self, value: Sequence[float]) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> XYResultBuilder: ...
    @overload
    def init(
        self: Any, name: Literal["xs"], size: int = ...
    ) -> _DynamicListBuilder[float]: ...
    @overload
    def init(
        self: Any, name: Literal["ys"], size: int = ...
    ) -> _DynamicListBuilder[float]: ...
    def init(self: Any, name: str, size: int = ...) -> Any: ...
    def copy(self) -> XYResultBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> XYResultReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class Stat:
    class Type(Enum):
        min = "min"
        max = "max"
        sd = "sd"
        avg = "avg"
        median = "median"

    @property
    def type(self) -> Stat.Type: ...
    @property
    def vs(self) -> Sequence[float]: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[StatReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> StatReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        type: Stat.Type | Literal["min", "max", "sd", "avg", "median"] | None = None,
        vs: Sequence[float] | None = None,
    ) -> StatBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> StatReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> StatReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class StatReader(Stat):
    def as_builder(self) -> StatBuilder: ...

class StatBuilder(Stat):
    @property
    def type(self) -> Stat.Type: ...
    @type.setter
    def type(
        self, value: Stat.Type | Literal["min", "max", "sd", "avg", "median"]
    ) -> None: ...
    @property
    def vs(self) -> Sequence[float]: ...
    @vs.setter
    def vs(self, value: Sequence[float]) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> StatBuilder: ...
    def init(
        self, name: Literal["vs"], size: int = ...
    ) -> _DynamicListBuilder[float]: ...
    def copy(self) -> StatBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> StatReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class XYPlusResult:
    @property
    def xy(self) -> XYResult: ...
    @property
    def stats(self) -> Sequence[Stat]: ...
    def init(self, name: Literal["xy"]) -> XYResult: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[XYPlusResultReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> XYPlusResultReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        xy: XYResultBuilder | dict[str, Any] | None = None,
        stats: Sequence[StatBuilder] | Sequence[dict[str, Any]] | None = None,
    ) -> XYPlusResultBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> XYPlusResultReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> XYPlusResultReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class XYPlusResultReader(XYPlusResult):
    @property
    def xy(self) -> XYResultReader: ...
    @property
    def stats(self) -> Sequence[StatReader]: ...
    def as_builder(self) -> XYPlusResultBuilder: ...

class XYPlusResultBuilder(XYPlusResult):
    @property
    def xy(self) -> XYResultBuilder: ...
    @xy.setter
    def xy(
        self, value: XYResult | XYResultBuilder | XYResultReader | dict[str, Any]
    ) -> None: ...
    @property
    def stats(self) -> Sequence[StatBuilder]: ...
    @stats.setter
    def stats(
        self,
        value: Sequence[Stat | StatBuilder | StatReader] | Sequence[dict[str, Any]],
    ) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> XYPlusResultBuilder: ...
    @overload
    def init(self: Any, name: Literal["xy"]) -> XYResultBuilder: ...
    @overload
    def init(
        self: Any, name: Literal["stats"], size: int = ...
    ) -> _DynamicListBuilder[StatBuilder]: ...
    def init(self: Any, name: str, size: int = ...) -> Any: ...
    def copy(self) -> XYPlusResultBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> XYPlusResultReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class ClimateInstance(Identifiable, Protocol):
    class RunResult(Awaitable[RunResult], Protocol):
        result: XYResultReader

    class RunResultsBuilder(Protocol):
        result: XYResultBuilder

    class RunCallContext(Protocol):
        results: ClimateInstance.RunResultsBuilder

    def run(self, timeSeries: Any) -> RunResult: ...
    class RunRequest(Protocol):
        timeSeries: Any
        def send(self) -> ClimateInstance.RunResult: ...

    def run_request(self) -> RunRequest: ...
    class RunsetResult(Awaitable[RunsetResult], Protocol):
        result: XYPlusResultReader

    class RunsetResultsBuilder(Protocol):
        result: XYPlusResultBuilder

    class RunsetCallContext(Protocol):
        results: ClimateInstance.RunsetResultsBuilder

    def runSet(self, dataset: Any) -> RunsetResult: ...
    class RunsetRequest(Protocol):
        dataset: Any
        def send(self) -> ClimateInstance.RunsetResult: ...

    def runSet_request(self) -> RunsetRequest: ...
    @classmethod
    def _new_client(
        cls, server: ClimateInstance.Server | Identifiable.Server
    ) -> ClimateInstance: ...
    class Server(Identifiable.Server):
        def run(
            self,
            timeSeries: Any,
            _context: ClimateInstance.RunCallContext,
            **kwargs: Any,
        ) -> Awaitable[XYResult]: ...
        def runSet(
            self,
            dataset: Any,
            _context: ClimateInstance.RunsetCallContext,
            **kwargs: Any,
        ) -> Awaitable[XYPlusResult]: ...

class Env(Generic[_RestInput]):
    @property
    def rest(self) -> _RestInput: ...
    @property
    def timeSeries(self) -> TimeSeries: ...
    @property
    def soilProfile(self) -> Profile: ...
    @property
    def mgmtEvents(self) -> Sequence[Event]: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[EnvReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> EnvReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        rest: _RestInput | None = None,
        timeSeries: TimeSeries | TimeSeries.Server | None = None,
        soilProfile: Profile | Profile.Server | None = None,
        mgmtEvents: Sequence[EventBuilder] | Sequence[dict[str, Any]] | None = None,
    ) -> EnvBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> EnvReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> EnvReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class EnvReader(Env, Generic[_RestInput]):
    @property
    def mgmtEvents(self) -> Sequence[EventReader]: ...
    def as_builder(self) -> EnvBuilder: ...

class EnvBuilder(Env, Generic[_RestInput]):
    @property
    def rest(self) -> _RestInput: ...
    @rest.setter
    def rest(self, value: _RestInput) -> None: ...
    @property
    def timeSeries(self) -> TimeSeries: ...
    @timeSeries.setter
    def timeSeries(self, value: TimeSeries | TimeSeries.Server) -> None: ...
    @property
    def soilProfile(self) -> Profile: ...
    @soilProfile.setter
    def soilProfile(self, value: Profile | Profile.Server) -> None: ...
    @property
    def mgmtEvents(self) -> Sequence[EventBuilder]: ...
    @mgmtEvents.setter
    def mgmtEvents(
        self,
        value: Sequence[Event | EventBuilder | EventReader] | Sequence[dict[str, Any]],
    ) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> EnvBuilder: ...
    def init(
        self, name: Literal["mgmtEvents"], size: int = ...
    ) -> _DynamicListBuilder[EventBuilder]: ...
    def copy(self) -> EnvBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> EnvReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class EnvInstance(Identifiable, Persistent, Stoppable, Protocol):
    class RunResult(Awaitable[RunResult], Protocol):
        result: Any

    class RunResultsBuilder(Protocol):
        result: Any

    class RunCallContext(Protocol):
        results: EnvInstance.RunResultsBuilder

    def run(self, env: Env[Any] | dict[str, Any]) -> RunResult: ...
    class RunRequest(Protocol):
        env: EnvBuilder[Any]
        def send(self) -> EnvInstance.RunResult: ...

    def run_request(self) -> RunRequest: ...
    @classmethod
    def _new_client(
        cls,
        server: EnvInstance.Server
        | Identifiable.Server
        | Persistent.Server
        | Stoppable.Server,
    ) -> EnvInstance: ...
    class Server(Identifiable.Server, Persistent.Server, Stoppable.Server):
        def run(
            self,
            env: EnvReader[Any],
            _context: EnvInstance.RunCallContext,
            **kwargs: Any,
        ) -> Awaitable[Any]: ...

class EnvInstanceProxy(EnvInstance, Protocol):
    class Unregister(Protocol):
        class UnregisterResult(Awaitable[UnregisterResult], Protocol):
            success: bool

        class UnregisterResultsBuilder(Protocol):
            success: bool

        class UnregisterCallContext(Protocol):
            results: EnvInstanceProxy.Unregister.UnregisterResultsBuilder

        def unregister(self) -> UnregisterResult: ...
        class UnregisterRequest(Protocol):
            def send(self) -> EnvInstanceProxy.Unregister.UnregisterResult: ...

        def unregister_request(self) -> UnregisterRequest: ...
        @classmethod
        def _new_client(
            cls, server: EnvInstanceProxy.Unregister.Server
        ) -> EnvInstanceProxy.Unregister: ...
        class Server:
            def unregister(
                self,
                _context: EnvInstanceProxy.Unregister.UnregisterCallContext,
                **kwargs: Any,
            ) -> Awaitable[bool]: ...

    class RegisterenvinstanceResult(Awaitable[RegisterenvinstanceResult], Protocol):
        unregister: EnvInstanceProxy.Unregister

    class RegisterenvinstanceResultsBuilder(Protocol):
        unregister: EnvInstanceProxy.Unregister

    class RegisterenvinstanceCallContext(Protocol):
        results: EnvInstanceProxy.RegisterenvinstanceResultsBuilder

    def registerEnvInstance(
        self, instance: EnvInstance
    ) -> RegisterenvinstanceResult: ...
    class RegisterenvinstanceRequest(Protocol):
        instance: EnvInstance
        def send(self) -> EnvInstanceProxy.RegisterenvinstanceResult: ...

    def registerEnvInstance_request(self) -> RegisterenvinstanceRequest: ...
    @classmethod
    def _new_client(
        cls,
        server: EnvInstanceProxy.Server
        | EnvInstance.Server
        | Identifiable.Server
        | Persistent.Server
        | Stoppable.Server,
    ) -> EnvInstanceProxy: ...
    class Server(EnvInstance.Server):
        def registerEnvInstance(
            self,
            instance: EnvInstance,
            _context: EnvInstanceProxy.RegisterenvinstanceCallContext,
            **kwargs: Any,
        ) -> Awaitable[
            EnvInstanceProxy.Unregister | EnvInstanceProxy.Unregister.Server
        ]: ...

class InstanceFactory(Identifiable, Protocol):
    class ModelinfoResult(Protocol):
        id: str
        name: str
        description: str

    class ModelinfoCallContext(Protocol):
        results: InstanceFactory.ModelinfoResult

    def modelInfo(self) -> Awaitable[InstanceFactory.ModelinfoResult]: ...
    class ModelinfoRequest(Protocol):
        def send(self) -> Awaitable[InstanceFactory.ModelinfoResult]: ...

    def modelInfo_request(self) -> ModelinfoRequest: ...
    class NewinstanceResult(Awaitable[NewinstanceResult], Protocol):
        instance: Identifiable

    class NewinstanceResultsBuilder(Protocol):
        instance: Identifiable

    class NewinstanceCallContext(Protocol):
        results: InstanceFactory.NewinstanceResultsBuilder

    def newInstance(self) -> NewinstanceResult: ...
    class NewinstanceRequest(Protocol):
        def send(self) -> InstanceFactory.NewinstanceResult: ...

    def newInstance_request(self) -> NewinstanceRequest: ...
    class NewinstancesResult(Awaitable[NewinstancesResult], Protocol):
        instances: Sequence[Identifiable]

    class NewinstancesResultsBuilder(Protocol):
        instances: Sequence[Identifiable]

    class NewinstancesCallContext(Protocol):
        results: InstanceFactory.NewinstancesResultsBuilder

    def newInstances(self, numberOfInstances: int) -> NewinstancesResult: ...
    class NewinstancesRequest(Protocol):
        numberOfInstances: int
        def send(self) -> InstanceFactory.NewinstancesResult: ...

    def newInstances_request(self) -> NewinstancesRequest: ...
    @classmethod
    def _new_client(
        cls, server: InstanceFactory.Server | Identifiable.Server
    ) -> InstanceFactory: ...
    class Server(Identifiable.Server):
        class ModelinfoResult(NamedTuple):
            id: str
            name: str
            description: str

        def modelInfo(
            self, _context: InstanceFactory.ModelinfoCallContext, **kwargs: Any
        ) -> Awaitable[InstanceFactory.Server.ModelinfoResult]: ...
        def newInstance(
            self, _context: InstanceFactory.NewinstanceCallContext, **kwargs: Any
        ) -> Awaitable[Identifiable | Identifiable.Server]: ...
        def newInstances(
            self,
            numberOfInstances: int,
            _context: InstanceFactory.NewinstancesCallContext,
            **kwargs: Any,
        ) -> Awaitable[Sequence[Identifiable]]: ...
