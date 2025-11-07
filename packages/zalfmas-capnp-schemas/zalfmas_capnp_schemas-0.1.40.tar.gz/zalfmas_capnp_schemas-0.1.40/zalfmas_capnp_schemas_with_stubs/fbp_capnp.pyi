"""This is an automatically generated stub for `fbp.capnp`."""

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

from .common_capnp import (
    Identifiable,
    IdInformation,
    IdInformationBuilder,
    IdInformationReader,
)
from .persistence_capnp import Persistent

Channel_V = TypeVar("Channel_V")

class IP:
    class KV:
        @property
        def key(self) -> str: ...
        @property
        def desc(self) -> str: ...
        @property
        def value(self) -> Any: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[IP.KVReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> IP.KVReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            key: str | None = None,
            desc: str | None = None,
            value: Any | None = None,
        ) -> IP.KVBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> IP.KVReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> IP.KVReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class KVReader(IP.KV):
        def as_builder(self) -> IP.KVBuilder: ...

    class KVBuilder(IP.KV):
        @property
        def key(self) -> str: ...
        @key.setter
        def key(self, value: str) -> None: ...
        @property
        def desc(self) -> str: ...
        @desc.setter
        def desc(self, value: str) -> None: ...
        @property
        def value(self) -> Any: ...
        @value.setter
        def value(self, value: Any) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> IP.KVBuilder: ...
        def copy(self) -> IP.KVBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> IP.KVReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class Type(Enum):
        standard = "standard"
        openBracket = "openBracket"
        closeBracket = "closeBracket"

    @property
    def attributes(self) -> Sequence[IP.KV]: ...
    @property
    def content(self) -> Any: ...
    @property
    def type(self) -> IP.Type: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[IPReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> IPReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        attributes: Sequence[IP.KVBuilder] | Sequence[dict[str, Any]] | None = None,
        content: Any | None = None,
        type: IP.Type
        | Literal["standard", "openBracket", "closeBracket"]
        | None = None,
    ) -> IPBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> IPReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> IPReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class IPReader(IP):
    @property
    def attributes(self) -> Sequence[IP.KVReader]: ...
    def as_builder(self) -> IPBuilder: ...

class IPBuilder(IP):
    @property
    def attributes(self) -> Sequence[IP.KVBuilder]: ...
    @attributes.setter
    def attributes(
        self,
        value: Sequence[IP.KV | IP.KVBuilder | IP.KVReader] | Sequence[dict[str, Any]],
    ) -> None: ...
    @property
    def content(self) -> Any: ...
    @content.setter
    def content(self, value: Any) -> None: ...
    @property
    def type(self) -> IP.Type: ...
    @type.setter
    def type(
        self, value: IP.Type | Literal["standard", "openBracket", "closeBracket"]
    ) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> IPBuilder: ...
    def init(
        self, name: Literal["attributes"], size: int = ...
    ) -> _DynamicListBuilder[IP.KVBuilder]: ...
    def copy(self) -> IPBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> IPReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class IIP:
    @property
    def content(self) -> Any: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[IIPReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> IIPReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        content: Any | None = None,
    ) -> IIPBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> IIPReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> IIPReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class IIPReader(IIP):
    def as_builder(self) -> IIPBuilder: ...

class IIPBuilder(IIP):
    @property
    def content(self) -> Any: ...
    @content.setter
    def content(self, value: Any) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> IIPBuilder: ...
    def copy(self) -> IIPBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> IIPReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class Channel(Identifiable, Persistent, Protocol):
    class CloseSemantics(Enum):
        fbp = "fbp"
        no = "no"

    class Msg(Generic[Channel_V]):
        @property
        def value(self) -> Channel_V: ...
        @property
        def done(self) -> None: ...
        @property
        def noMsg(self) -> None: ...
        def which(self) -> Literal["value", "done", "noMsg"]: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Channel.MsgReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Channel.MsgReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            value: Channel_V | None = None,
            done: None | None = None,
            noMsg: None | None = None,
        ) -> Channel.MsgBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Channel.MsgReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Channel.MsgReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class MsgReader(Channel.Msg, Generic[Channel_V]):
        def as_builder(self) -> Channel.MsgBuilder: ...

    class MsgBuilder(Channel.Msg, Generic[Channel_V]):
        @property
        def value(self) -> Channel_V: ...
        @value.setter
        def value(self, value: Channel_V) -> None: ...
        @property
        def done(self) -> None: ...
        @done.setter
        def done(self, value: None) -> None: ...
        @property
        def noMsg(self) -> None: ...
        @noMsg.setter
        def noMsg(self, value: None) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Channel.MsgBuilder: ...
        def copy(self) -> Channel.MsgBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Channel.MsgReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class Reader(Identifiable, Persistent, Protocol):
        class ReadResult(Protocol):
            value: Any
            done: None
            noMsg: None
            def which(self) -> Literal["value", "done", "noMsg"]: ...

        class ReadCallContext(Protocol):
            results: Channel.Reader.ReadResult

        def read(self) -> Awaitable[Channel.Reader.ReadResult]: ...
        class ReadRequest(Protocol):
            def send(self) -> Awaitable[Channel.Reader.ReadResult]: ...

        def read_request(self) -> ReadRequest: ...
        class CloseResultsBuilder(Protocol): ...

        class CloseCallContext(Protocol):
            results: Channel.Reader.CloseResultsBuilder

        def close(self) -> Awaitable[None]: ...
        class CloseRequest(Protocol):
            def send(self) -> Awaitable[None]: ...

        def close_request(self) -> CloseRequest: ...
        class ReadifmsgResult(Protocol):
            value: Any
            done: None
            noMsg: None
            def which(self) -> Literal["value", "done", "noMsg"]: ...

        class ReadifmsgCallContext(Protocol):
            results: Channel.Reader.ReadifmsgResult

        def readIfMsg(self) -> Awaitable[Channel.Reader.ReadifmsgResult]: ...
        class ReadifmsgRequest(Protocol):
            def send(self) -> Awaitable[Channel.Reader.ReadifmsgResult]: ...

        def readIfMsg_request(self) -> ReadifmsgRequest: ...
        @classmethod
        def _new_client(
            cls, server: Channel.Reader.Server | Identifiable.Server | Persistent.Server
        ) -> Channel.Reader: ...
        class Server(Identifiable.Server, Persistent.Server):
            class ReadResult(NamedTuple):
                value: Any
                done: None
                noMsg: None

            class ReadifmsgResult(NamedTuple):
                value: Any
                done: None
                noMsg: None

            def read(
                self, _context: Channel.Reader.ReadCallContext, **kwargs: Any
            ) -> Awaitable[Channel.Reader.Server.ReadResult]: ...
            def close(
                self, _context: Channel.Reader.CloseCallContext, **kwargs: Any
            ) -> Awaitable[None]: ...
            def readIfMsg(
                self, _context: Channel.Reader.ReadifmsgCallContext, **kwargs: Any
            ) -> Awaitable[Channel.Reader.Server.ReadifmsgResult]: ...

    class Writer(Identifiable, Persistent, Protocol):
        class WriteResultsBuilder(Protocol): ...

        class WriteCallContext(Protocol):
            results: Channel.Writer.WriteResultsBuilder

        def write(self, value: Any, done: None, noMsg: None) -> Awaitable[None]: ...
        class WriteRequest(Protocol):
            value: Any
            done: None
            noMsg: None
            def send(self) -> Awaitable[None]: ...

        def write_request(self) -> WriteRequest: ...
        class CloseResultsBuilder(Protocol): ...

        class CloseCallContext(Protocol):
            results: Channel.Writer.CloseResultsBuilder

        def close(self) -> Awaitable[None]: ...
        class CloseRequest(Protocol):
            def send(self) -> Awaitable[None]: ...

        def close_request(self) -> CloseRequest: ...
        class WriteifspaceResult(Awaitable[WriteifspaceResult], Protocol):
            success: bool

        class WriteifspaceResultsBuilder(Protocol):
            success: bool

        class WriteifspaceCallContext(Protocol):
            results: Channel.Writer.WriteifspaceResultsBuilder

        def writeIfSpace(
            self, value: Any, done: None, noMsg: None
        ) -> WriteifspaceResult: ...
        class WriteifspaceRequest(Protocol):
            value: Any
            done: None
            noMsg: None
            def send(self) -> Channel.Writer.WriteifspaceResult: ...

        def writeIfSpace_request(self) -> WriteifspaceRequest: ...
        @classmethod
        def _new_client(
            cls, server: Channel.Writer.Server | Identifiable.Server | Persistent.Server
        ) -> Channel.Writer: ...
        class Server(Identifiable.Server, Persistent.Server):
            def write(
                self,
                value: Any,
                done: None,
                noMsg: None,
                _context: Channel.Writer.WriteCallContext,
                **kwargs: Any,
            ) -> Awaitable[None]: ...
            def close(
                self, _context: Channel.Writer.CloseCallContext, **kwargs: Any
            ) -> Awaitable[None]: ...
            def writeIfSpace(
                self,
                value: Any,
                done: None,
                noMsg: None,
                _context: Channel.Writer.WriteifspaceCallContext,
                **kwargs: Any,
            ) -> Awaitable[bool]: ...

    class StartupInfo:
        @property
        def bufferSize(self) -> int: ...
        @property
        def closeSemantics(self) -> Channel.CloseSemantics: ...
        @property
        def channelSR(self) -> str: ...
        @property
        def readerSRs(self) -> Sequence[str]: ...
        @property
        def writerSRs(self) -> Sequence[str]: ...
        @property
        def channel(self) -> Channel: ...
        @property
        def readers(self) -> Sequence[Channel.Reader]: ...
        @property
        def writers(self) -> Sequence[Channel.Writer]: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Channel.StartupInfoReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Channel.StartupInfoReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            bufferSize: int | None = None,
            closeSemantics: Channel.CloseSemantics | Literal["fbp", "no"] | None = None,
            channelSR: str | None = None,
            readerSRs: Sequence[str] | None = None,
            writerSRs: Sequence[str] | None = None,
            channel: Channel | Channel.Server | None = None,
            readers: Sequence[Channel.Reader] | None = None,
            writers: Sequence[Channel.Writer] | None = None,
        ) -> Channel.StartupInfoBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Channel.StartupInfoReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Channel.StartupInfoReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class StartupInfoReader(Channel.StartupInfo):
        def as_builder(self) -> Channel.StartupInfoBuilder: ...

    class StartupInfoBuilder(Channel.StartupInfo):
        @property
        def bufferSize(self) -> int: ...
        @bufferSize.setter
        def bufferSize(self, value: int) -> None: ...
        @property
        def closeSemantics(self) -> Channel.CloseSemantics: ...
        @closeSemantics.setter
        def closeSemantics(
            self, value: Channel.CloseSemantics | Literal["fbp", "no"]
        ) -> None: ...
        @property
        def channelSR(self) -> str: ...
        @channelSR.setter
        def channelSR(self, value: str) -> None: ...
        @property
        def readerSRs(self) -> Sequence[str]: ...
        @readerSRs.setter
        def readerSRs(self, value: Sequence[str]) -> None: ...
        @property
        def writerSRs(self) -> Sequence[str]: ...
        @writerSRs.setter
        def writerSRs(self, value: Sequence[str]) -> None: ...
        @property
        def channel(self) -> Channel: ...
        @channel.setter
        def channel(self, value: Channel | Channel.Server) -> None: ...
        @property
        def readers(self) -> Sequence[Channel.Reader]: ...
        @readers.setter
        def readers(self, value: Sequence[Channel.Reader]) -> None: ...
        @property
        def writers(self) -> Sequence[Channel.Writer]: ...
        @writers.setter
        def writers(self, value: Sequence[Channel.Writer]) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Channel.StartupInfoBuilder: ...
        @overload
        def init(
            self: Any, name: Literal["readerSRs"], size: int = ...
        ) -> _DynamicListBuilder[str]: ...
        @overload
        def init(
            self: Any, name: Literal["writerSRs"], size: int = ...
        ) -> _DynamicListBuilder[str]: ...
        @overload
        def init(
            self: Any, name: Literal["readers"], size: int = ...
        ) -> _DynamicListBuilder[Channel.Reader]: ...
        @overload
        def init(
            self: Any, name: Literal["writers"], size: int = ...
        ) -> _DynamicListBuilder[Channel.Writer]: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        def copy(self) -> Channel.StartupInfoBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Channel.StartupInfoReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class SetbuffersizeResultsBuilder(Protocol): ...

    class SetbuffersizeCallContext(Protocol):
        results: Channel.SetbuffersizeResultsBuilder

    def setBufferSize(self, size: int) -> Awaitable[None]: ...
    class SetbuffersizeRequest(Protocol):
        size: int
        def send(self) -> Awaitable[None]: ...

    def setBufferSize_request(self) -> SetbuffersizeRequest: ...
    class ReaderResult(Awaitable[ReaderResult], Protocol):
        r: Channel.Reader

    class ReaderResultsBuilder(Protocol):
        r: Channel.Reader

    class ReaderCallContext(Protocol):
        results: Channel.ReaderResultsBuilder

    def reader(self) -> ReaderResult: ...
    class ReaderRequest(Protocol):
        def send(self) -> Channel.ReaderResult: ...

    def reader_request(self) -> ReaderRequest: ...
    class WriterResult(Awaitable[WriterResult], Protocol):
        w: Channel.Writer

    class WriterResultsBuilder(Protocol):
        w: Channel.Writer

    class WriterCallContext(Protocol):
        results: Channel.WriterResultsBuilder

    def writer(self) -> WriterResult: ...
    class WriterRequest(Protocol):
        def send(self) -> Channel.WriterResult: ...

    def writer_request(self) -> WriterRequest: ...
    class EndpointsResult(Awaitable[EndpointsResult], Protocol):
        r: Channel.Reader
        w: Channel.Writer

    class EndpointsResultsBuilder(Protocol):
        r: Channel.Reader
        w: Channel.Writer

    class EndpointsCallContext(Protocol):
        results: Channel.EndpointsResultsBuilder

    def endpoints(self) -> EndpointsResult: ...
    class EndpointsRequest(Protocol):
        def send(self) -> Channel.EndpointsResult: ...

    def endpoints_request(self) -> EndpointsRequest: ...
    class SetautoclosesemanticsResultsBuilder(Protocol): ...

    class SetautoclosesemanticsCallContext(Protocol):
        results: Channel.SetautoclosesemanticsResultsBuilder

    def setAutoCloseSemantics(
        self, cs: Channel.CloseSemantics | Literal["fbp", "no"]
    ) -> Awaitable[None]: ...
    class SetautoclosesemanticsRequest(Protocol):
        cs: Channel.CloseSemantics
        def send(self) -> Awaitable[None]: ...

    def setAutoCloseSemantics_request(self) -> SetautoclosesemanticsRequest: ...
    class CloseResultsBuilder(Protocol): ...

    class CloseCallContext(Protocol):
        results: Channel.CloseResultsBuilder

    def close(self, waitForEmptyBuffer: bool) -> Awaitable[None]: ...
    class CloseRequest(Protocol):
        waitForEmptyBuffer: bool
        def send(self) -> Awaitable[None]: ...

    def close_request(self) -> CloseRequest: ...
    @classmethod
    def _new_client(
        cls, server: Channel.Server | Identifiable.Server | Persistent.Server
    ) -> Channel: ...
    class Server(Identifiable.Server, Persistent.Server):
        def setBufferSize(
            self, size: int, _context: Channel.SetbuffersizeCallContext, **kwargs: Any
        ) -> Awaitable[None]: ...
        def reader(
            self, _context: Channel.ReaderCallContext, **kwargs: Any
        ) -> Awaitable[Channel.Reader | Channel.Reader.Server]: ...
        def writer(
            self, _context: Channel.WriterCallContext, **kwargs: Any
        ) -> Awaitable[Channel.Writer | Channel.Writer.Server]: ...
        def endpoints(
            self, _context: Channel.EndpointsCallContext, **kwargs: Any
        ) -> Awaitable[tuple[Channel.Reader, Channel.Writer]]: ...
        def setAutoCloseSemantics(
            self,
            cs: Channel.CloseSemantics | Literal["fbp", "no"],
            _context: Channel.SetautoclosesemanticsCallContext,
            **kwargs: Any,
        ) -> Awaitable[None]: ...
        def close(
            self,
            waitForEmptyBuffer: bool,
            _context: Channel.CloseCallContext,
            **kwargs: Any,
        ) -> Awaitable[None]: ...

class StartChannelsService(Identifiable, Protocol):
    class Params:
        @property
        def name(self) -> str: ...
        @property
        def noOfChannels(self) -> int: ...
        @property
        def noOfReaders(self) -> int: ...
        @property
        def noOfWriters(self) -> int: ...
        @property
        def readerSrts(self) -> Sequence[str]: ...
        @property
        def writerSrts(self) -> Sequence[str]: ...
        @property
        def bufferSize(self) -> int: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[StartChannelsService.ParamsReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> StartChannelsService.ParamsReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            name: str | None = None,
            noOfChannels: int | None = None,
            noOfReaders: int | None = None,
            noOfWriters: int | None = None,
            readerSrts: Sequence[str] | None = None,
            writerSrts: Sequence[str] | None = None,
            bufferSize: int | None = None,
        ) -> StartChannelsService.ParamsBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> StartChannelsService.ParamsReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> StartChannelsService.ParamsReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class ParamsReader(StartChannelsService.Params):
        def as_builder(self) -> StartChannelsService.ParamsBuilder: ...

    class ParamsBuilder(StartChannelsService.Params):
        @property
        def name(self) -> str: ...
        @name.setter
        def name(self, value: str) -> None: ...
        @property
        def noOfChannels(self) -> int: ...
        @noOfChannels.setter
        def noOfChannels(self, value: int) -> None: ...
        @property
        def noOfReaders(self) -> int: ...
        @noOfReaders.setter
        def noOfReaders(self, value: int) -> None: ...
        @property
        def noOfWriters(self) -> int: ...
        @noOfWriters.setter
        def noOfWriters(self, value: int) -> None: ...
        @property
        def readerSrts(self) -> Sequence[str]: ...
        @readerSrts.setter
        def readerSrts(self, value: Sequence[str]) -> None: ...
        @property
        def writerSrts(self) -> Sequence[str]: ...
        @writerSrts.setter
        def writerSrts(self, value: Sequence[str]) -> None: ...
        @property
        def bufferSize(self) -> int: ...
        @bufferSize.setter
        def bufferSize(self, value: int) -> None: ...
        @staticmethod
        def from_dict(
            dictionary: dict[str, Any],
        ) -> StartChannelsService.ParamsBuilder: ...
        @overload
        def init(
            self: Any, name: Literal["readerSrts"], size: int = ...
        ) -> _DynamicListBuilder[str]: ...
        @overload
        def init(
            self: Any, name: Literal["writerSrts"], size: int = ...
        ) -> _DynamicListBuilder[str]: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        def copy(self) -> StartChannelsService.ParamsBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> StartChannelsService.ParamsReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class StartResult(Awaitable[StartResult], Protocol):
        startupInfos: Sequence[Channel.StartupInfoReader]
        stop: Any

    class StartResultsBuilder(Protocol):
        startupInfos: Sequence[Channel.StartupInfoBuilder]
        stop: Any

    class StartCallContext(Protocol):
        results: StartChannelsService.StartResultsBuilder

    def start(
        self,
        name: str,
        noOfChannels: int,
        noOfReaders: int,
        noOfWriters: int,
        readerSrts: Sequence[str],
        writerSrts: Sequence[str],
        bufferSize: int,
    ) -> StartResult: ...
    class StartRequest(Protocol):
        name: str
        noOfChannels: int
        noOfReaders: int
        noOfWriters: int
        readerSrts: Sequence[str]
        writerSrts: Sequence[str]
        bufferSize: int
        def send(self) -> StartChannelsService.StartResult: ...

    def start_request(self) -> StartRequest: ...
    @classmethod
    def _new_client(
        cls, server: StartChannelsService.Server | Identifiable.Server
    ) -> StartChannelsService: ...
    class Server(Identifiable.Server):
        def start(
            self,
            name: str,
            noOfChannels: int,
            noOfReaders: int,
            noOfWriters: int,
            readerSrts: Sequence[str],
            writerSrts: Sequence[str],
            bufferSize: int,
            _context: StartChannelsService.StartCallContext,
            **kwargs: Any,
        ) -> Awaitable[Any]: ...

class PortInfos:
    class NameAndSR:
        @property
        def name(self) -> str: ...
        @property
        def sr(self) -> str: ...
        @property
        def srs(self) -> Sequence[str]: ...
        def which(self) -> Literal["sr", "srs"]: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[PortInfos.NameAndSRReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> PortInfos.NameAndSRReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            name: str | None = None,
            sr: str | None = None,
            srs: Sequence[str] | None = None,
        ) -> PortInfos.NameAndSRBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> PortInfos.NameAndSRReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> PortInfos.NameAndSRReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class NameAndSRReader(PortInfos.NameAndSR):
        def as_builder(self) -> PortInfos.NameAndSRBuilder: ...

    class NameAndSRBuilder(PortInfos.NameAndSR):
        @property
        def name(self) -> str: ...
        @name.setter
        def name(self, value: str) -> None: ...
        @property
        def sr(self) -> str: ...
        @sr.setter
        def sr(self, value: str) -> None: ...
        @property
        def srs(self) -> Sequence[str]: ...
        @srs.setter
        def srs(self, value: Sequence[str]) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> PortInfos.NameAndSRBuilder: ...
        def init(
            self, name: Literal["srs"], size: int = ...
        ) -> _DynamicListBuilder[str]: ...
        def copy(self) -> PortInfos.NameAndSRBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> PortInfos.NameAndSRReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    @property
    def inPorts(self) -> Sequence[PortInfos.NameAndSR]: ...
    @property
    def outPorts(self) -> Sequence[PortInfos.NameAndSR]: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[PortInfosReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> PortInfosReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        inPorts: Sequence[PortInfos.NameAndSRBuilder]
        | Sequence[dict[str, Any]]
        | None = None,
        outPorts: Sequence[PortInfos.NameAndSRBuilder]
        | Sequence[dict[str, Any]]
        | None = None,
    ) -> PortInfosBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> PortInfosReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> PortInfosReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class PortInfosReader(PortInfos):
    @property
    def inPorts(self) -> Sequence[PortInfos.NameAndSRReader]: ...
    @property
    def outPorts(self) -> Sequence[PortInfos.NameAndSRReader]: ...
    def as_builder(self) -> PortInfosBuilder: ...

class PortInfosBuilder(PortInfos):
    @property
    def inPorts(self) -> Sequence[PortInfos.NameAndSRBuilder]: ...
    @inPorts.setter
    def inPorts(
        self,
        value: Sequence[
            PortInfos.NameAndSR | PortInfos.NameAndSRBuilder | PortInfos.NameAndSRReader
        ]
        | Sequence[dict[str, Any]],
    ) -> None: ...
    @property
    def outPorts(self) -> Sequence[PortInfos.NameAndSRBuilder]: ...
    @outPorts.setter
    def outPorts(
        self,
        value: Sequence[
            PortInfos.NameAndSR | PortInfos.NameAndSRBuilder | PortInfos.NameAndSRReader
        ]
        | Sequence[dict[str, Any]],
    ) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> PortInfosBuilder: ...
    @overload
    def init(
        self: Any, name: Literal["inPorts"], size: int = ...
    ) -> _DynamicListBuilder[PortInfos.NameAndSRBuilder]: ...
    @overload
    def init(
        self: Any, name: Literal["outPorts"], size: int = ...
    ) -> _DynamicListBuilder[PortInfos.NameAndSRBuilder]: ...
    def init(self: Any, name: str, size: int = ...) -> Any: ...
    def copy(self) -> PortInfosBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> PortInfosReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...

class Component:
    class Runnable(Identifiable, Protocol):
        class StartResult(Awaitable[StartResult], Protocol):
            success: bool

        class StartResultsBuilder(Protocol):
            success: bool

        class StartCallContext(Protocol):
            results: Component.Runnable.StartResultsBuilder

        def start(self, portInfosReaderSr: str, name: str) -> StartResult: ...
        class StartRequest(Protocol):
            portInfosReaderSr: str
            name: str
            def send(self) -> Component.Runnable.StartResult: ...

        def start_request(self) -> StartRequest: ...
        class StopResult(Awaitable[StopResult], Protocol):
            success: bool

        class StopResultsBuilder(Protocol):
            success: bool

        class StopCallContext(Protocol):
            results: Component.Runnable.StopResultsBuilder

        def stop(self) -> StopResult: ...
        class StopRequest(Protocol):
            def send(self) -> Component.Runnable.StopResult: ...

        def stop_request(self) -> StopRequest: ...
        @classmethod
        def _new_client(
            cls, server: Component.Runnable.Server | Identifiable.Server
        ) -> Component.Runnable: ...
        class Server(Identifiable.Server):
            def start(
                self,
                portInfosReaderSr: str,
                name: str,
                _context: Component.Runnable.StartCallContext,
                **kwargs: Any,
            ) -> Awaitable[bool]: ...
            def stop(
                self, _context: Component.Runnable.StopCallContext, **kwargs: Any
            ) -> Awaitable[bool]: ...

    class ComponentType(Enum):
        standard = "standard"
        iip = "iip"
        subflow = "subflow"
        view = "view"

    class Port:
        class PortType(Enum):
            standard = "standard"

        class ContentType(Enum):
            structuredText = "structuredText"

        @property
        def name(self) -> str: ...
        @property
        def contentType(self) -> str: ...
        @property
        def type(self) -> Component.Port.PortType: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Component.PortReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Component.PortReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            name: str | None = None,
            contentType: str | None = None,
            type: Component.Port.PortType | Literal["standard"] | None = None,
        ) -> Component.PortBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Component.PortReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Component.PortReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class PortReader(Component.Port):
        def as_builder(self) -> Component.PortBuilder: ...

    class PortBuilder(Component.Port):
        @property
        def name(self) -> str: ...
        @name.setter
        def name(self, value: str) -> None: ...
        @property
        def contentType(self) -> str: ...
        @contentType.setter
        def contentType(self, value: str) -> None: ...
        @property
        def type(self) -> Component.Port.PortType: ...
        @type.setter
        def type(
            self, value: Component.Port.PortType | Literal["standard"]
        ) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Component.PortBuilder: ...
        def copy(self) -> Component.PortBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Component.PortReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    @property
    def info(self) -> IdInformation: ...
    @property
    def type(self) -> Component.ComponentType: ...
    @property
    def inPorts(self) -> Sequence[Component.Port]: ...
    @property
    def outPorts(self) -> Sequence[Component.Port]: ...
    @property
    def run(self) -> Component.Runnable: ...
    @property
    def defaultConfig(self) -> str: ...
    def init(self, name: Literal["info"]) -> IdInformation: ...
    @staticmethod
    @contextmanager
    def from_bytes(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> Iterator[ComponentReader]: ...
    @staticmethod
    def from_bytes_packed(
        data: bytes,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> ComponentReader: ...
    @staticmethod
    def new_message(
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Any = None,
        info: IdInformationBuilder | dict[str, Any] | None = None,
        type: Component.ComponentType
        | Literal["standard", "iip", "subflow", "view"]
        | None = None,
        inPorts: Sequence[Component.PortBuilder]
        | Sequence[dict[str, Any]]
        | None = None,
        outPorts: Sequence[Component.PortBuilder]
        | Sequence[dict[str, Any]]
        | None = None,
        run: Component.Runnable | Component.Runnable.Server | None = None,
        defaultConfig: str | None = None,
    ) -> ComponentBuilder: ...
    @staticmethod
    def read(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> ComponentReader: ...
    @staticmethod
    def read_packed(
        file: BinaryIO,
        traversal_limit_in_words: int | None = ...,
        nesting_limit: int | None = ...,
    ) -> ComponentReader: ...
    def to_dict(self) -> dict[str, Any]: ...

class ComponentReader(Component):
    @property
    def info(self) -> IdInformationReader: ...
    @property
    def inPorts(self) -> Sequence[Component.PortReader]: ...
    @property
    def outPorts(self) -> Sequence[Component.PortReader]: ...
    def as_builder(self) -> ComponentBuilder: ...

class ComponentBuilder(Component):
    @property
    def info(self) -> IdInformationBuilder: ...
    @info.setter
    def info(
        self,
        value: IdInformation
        | IdInformationBuilder
        | IdInformationReader
        | dict[str, Any],
    ) -> None: ...
    @property
    def type(self) -> Component.ComponentType: ...
    @type.setter
    def type(
        self,
        value: Component.ComponentType | Literal["standard", "iip", "subflow", "view"],
    ) -> None: ...
    @property
    def inPorts(self) -> Sequence[Component.PortBuilder]: ...
    @inPorts.setter
    def inPorts(
        self,
        value: Sequence[Component.Port | Component.PortBuilder | Component.PortReader]
        | Sequence[dict[str, Any]],
    ) -> None: ...
    @property
    def outPorts(self) -> Sequence[Component.PortBuilder]: ...
    @outPorts.setter
    def outPorts(
        self,
        value: Sequence[Component.Port | Component.PortBuilder | Component.PortReader]
        | Sequence[dict[str, Any]],
    ) -> None: ...
    @property
    def run(self) -> Component.Runnable: ...
    @run.setter
    def run(self, value: Component.Runnable | Component.Runnable.Server) -> None: ...
    @property
    def defaultConfig(self) -> str: ...
    @defaultConfig.setter
    def defaultConfig(self, value: str) -> None: ...
    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> ComponentBuilder: ...
    @overload
    def init(self: Any, name: Literal["info"]) -> IdInformationBuilder: ...
    @overload
    def init(
        self: Any, name: Literal["inPorts"], size: int = ...
    ) -> _DynamicListBuilder[Component.PortBuilder]: ...
    @overload
    def init(
        self: Any, name: Literal["outPorts"], size: int = ...
    ) -> _DynamicListBuilder[Component.PortBuilder]: ...
    def init(self: Any, name: str, size: int = ...) -> Any: ...
    def copy(self) -> ComponentBuilder: ...
    def to_bytes(self) -> bytes: ...
    def to_bytes_packed(self) -> bytes: ...
    def to_segments(self) -> list[bytes]: ...
    def as_reader(self) -> ComponentReader: ...
    @staticmethod
    def write(file: BufferedWriter) -> None: ...
    @staticmethod
    def write_packed(file: BufferedWriter) -> None: ...
