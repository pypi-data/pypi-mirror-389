"""This is an automatically generated stub for `storage.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator, Sequence
from contextlib import contextmanager
from io import BufferedWriter
from typing import Any, BinaryIO, Literal, Protocol, overload

from capnp import _DynamicListBuilder

from .common_capnp import (
    Identifiable,
    IdInformation,
    IdInformationBuilder,
    IdInformationReader,
    Pair,
    PairBuilder,
    PairReader,
)
from .persistence_capnp import Persistent

class Store(Identifiable, Persistent, Protocol):
    class Container(Identifiable, Persistent, Protocol):
        class Entry(Protocol):
            class Value:
                @property
                def boolValue(self) -> bool: ...
                @property
                def boolListValue(self) -> Sequence[bool]: ...
                @property
                def int8Value(self) -> int: ...
                @property
                def int8ListValue(self) -> Sequence[int]: ...
                @property
                def int16Value(self) -> int: ...
                @property
                def int16ListValue(self) -> Sequence[int]: ...
                @property
                def int32Value(self) -> int: ...
                @property
                def int32ListValue(self) -> Sequence[int]: ...
                @property
                def int64Value(self) -> int: ...
                @property
                def int64ListValue(self) -> Sequence[int]: ...
                @property
                def uint8Value(self) -> int: ...
                @property
                def uint8ListValue(self) -> Sequence[int]: ...
                @property
                def uint16Value(self) -> int: ...
                @property
                def uint16ListValue(self) -> Sequence[int]: ...
                @property
                def uint32Value(self) -> int: ...
                @property
                def uint32ListValue(self) -> Sequence[int]: ...
                @property
                def uint64Value(self) -> int: ...
                @property
                def uint64ListValue(self) -> Sequence[int]: ...
                @property
                def float32Value(self) -> float: ...
                @property
                def float32ListValue(self) -> Sequence[float]: ...
                @property
                def float64Value(self) -> float: ...
                @property
                def float64ListValue(self) -> Sequence[float]: ...
                @property
                def textValue(self) -> str: ...
                @property
                def textListValue(self) -> Sequence[str]: ...
                @property
                def dataValue(self) -> bytes: ...
                @property
                def dataListValue(self) -> Sequence[bytes]: ...
                @property
                def anyValue(self) -> Any: ...
                def which(
                    self,
                ) -> Literal[
                    "boolValue",
                    "boolListValue",
                    "int8Value",
                    "int8ListValue",
                    "int16Value",
                    "int16ListValue",
                    "int32Value",
                    "int32ListValue",
                    "int64Value",
                    "int64ListValue",
                    "uint8Value",
                    "uint8ListValue",
                    "uint16Value",
                    "uint16ListValue",
                    "uint32Value",
                    "uint32ListValue",
                    "uint64Value",
                    "uint64ListValue",
                    "float32Value",
                    "float32ListValue",
                    "float64Value",
                    "float64ListValue",
                    "textValue",
                    "textListValue",
                    "dataValue",
                    "dataListValue",
                    "anyValue",
                ]: ...
                @staticmethod
                @contextmanager
                def from_bytes(
                    data: bytes,
                    traversal_limit_in_words: int | None = ...,
                    nesting_limit: int | None = ...,
                ) -> Iterator[Store.Container.Entry.ValueReader]: ...
                @staticmethod
                def from_bytes_packed(
                    data: bytes,
                    traversal_limit_in_words: int | None = ...,
                    nesting_limit: int | None = ...,
                ) -> Store.Container.Entry.ValueReader: ...
                @staticmethod
                def new_message(
                    num_first_segment_words: int | None = None,
                    allocate_seg_callable: Any = None,
                    boolValue: bool | None = None,
                    boolListValue: Sequence[bool] | None = None,
                    int8Value: int | None = None,
                    int8ListValue: Sequence[int] | None = None,
                    int16Value: int | None = None,
                    int16ListValue: Sequence[int] | None = None,
                    int32Value: int | None = None,
                    int32ListValue: Sequence[int] | None = None,
                    int64Value: int | None = None,
                    int64ListValue: Sequence[int] | None = None,
                    uint8Value: int | None = None,
                    uint8ListValue: Sequence[int] | None = None,
                    uint16Value: int | None = None,
                    uint16ListValue: Sequence[int] | None = None,
                    uint32Value: int | None = None,
                    uint32ListValue: Sequence[int] | None = None,
                    uint64Value: int | None = None,
                    uint64ListValue: Sequence[int] | None = None,
                    float32Value: float | None = None,
                    float32ListValue: Sequence[float] | None = None,
                    float64Value: float | None = None,
                    float64ListValue: Sequence[float] | None = None,
                    textValue: str | None = None,
                    textListValue: Sequence[str] | None = None,
                    dataValue: bytes | None = None,
                    dataListValue: Sequence[bytes] | None = None,
                    anyValue: Any | None = None,
                ) -> Store.Container.Entry.ValueBuilder: ...
                @staticmethod
                def read(
                    file: BinaryIO,
                    traversal_limit_in_words: int | None = ...,
                    nesting_limit: int | None = ...,
                ) -> Store.Container.Entry.ValueReader: ...
                @staticmethod
                def read_packed(
                    file: BinaryIO,
                    traversal_limit_in_words: int | None = ...,
                    nesting_limit: int | None = ...,
                ) -> Store.Container.Entry.ValueReader: ...
                def to_dict(self) -> dict[str, Any]: ...

            class ValueReader(Store.Container.Entry.Value):
                def as_builder(self) -> Store.Container.Entry.ValueBuilder: ...

            class ValueBuilder(Store.Container.Entry.Value):
                @property
                def boolValue(self) -> bool: ...
                @boolValue.setter
                def boolValue(self, value: bool) -> None: ...
                @property
                def boolListValue(self) -> Sequence[bool]: ...
                @boolListValue.setter
                def boolListValue(self, value: Sequence[bool]) -> None: ...
                @property
                def int8Value(self) -> int: ...
                @int8Value.setter
                def int8Value(self, value: int) -> None: ...
                @property
                def int8ListValue(self) -> Sequence[int]: ...
                @int8ListValue.setter
                def int8ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def int16Value(self) -> int: ...
                @int16Value.setter
                def int16Value(self, value: int) -> None: ...
                @property
                def int16ListValue(self) -> Sequence[int]: ...
                @int16ListValue.setter
                def int16ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def int32Value(self) -> int: ...
                @int32Value.setter
                def int32Value(self, value: int) -> None: ...
                @property
                def int32ListValue(self) -> Sequence[int]: ...
                @int32ListValue.setter
                def int32ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def int64Value(self) -> int: ...
                @int64Value.setter
                def int64Value(self, value: int) -> None: ...
                @property
                def int64ListValue(self) -> Sequence[int]: ...
                @int64ListValue.setter
                def int64ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def uint8Value(self) -> int: ...
                @uint8Value.setter
                def uint8Value(self, value: int) -> None: ...
                @property
                def uint8ListValue(self) -> Sequence[int]: ...
                @uint8ListValue.setter
                def uint8ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def uint16Value(self) -> int: ...
                @uint16Value.setter
                def uint16Value(self, value: int) -> None: ...
                @property
                def uint16ListValue(self) -> Sequence[int]: ...
                @uint16ListValue.setter
                def uint16ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def uint32Value(self) -> int: ...
                @uint32Value.setter
                def uint32Value(self, value: int) -> None: ...
                @property
                def uint32ListValue(self) -> Sequence[int]: ...
                @uint32ListValue.setter
                def uint32ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def uint64Value(self) -> int: ...
                @uint64Value.setter
                def uint64Value(self, value: int) -> None: ...
                @property
                def uint64ListValue(self) -> Sequence[int]: ...
                @uint64ListValue.setter
                def uint64ListValue(self, value: Sequence[int]) -> None: ...
                @property
                def float32Value(self) -> float: ...
                @float32Value.setter
                def float32Value(self, value: float) -> None: ...
                @property
                def float32ListValue(self) -> Sequence[float]: ...
                @float32ListValue.setter
                def float32ListValue(self, value: Sequence[float]) -> None: ...
                @property
                def float64Value(self) -> float: ...
                @float64Value.setter
                def float64Value(self, value: float) -> None: ...
                @property
                def float64ListValue(self) -> Sequence[float]: ...
                @float64ListValue.setter
                def float64ListValue(self, value: Sequence[float]) -> None: ...
                @property
                def textValue(self) -> str: ...
                @textValue.setter
                def textValue(self, value: str) -> None: ...
                @property
                def textListValue(self) -> Sequence[str]: ...
                @textListValue.setter
                def textListValue(self, value: Sequence[str]) -> None: ...
                @property
                def dataValue(self) -> bytes: ...
                @dataValue.setter
                def dataValue(self, value: bytes) -> None: ...
                @property
                def dataListValue(self) -> Sequence[bytes]: ...
                @dataListValue.setter
                def dataListValue(self, value: Sequence[bytes]) -> None: ...
                @property
                def anyValue(self) -> Any: ...
                @anyValue.setter
                def anyValue(self, value: Any) -> None: ...
                @staticmethod
                def from_dict(
                    dictionary: dict[str, Any],
                ) -> Store.Container.Entry.ValueBuilder: ...
                @overload
                def init(
                    self: Any, name: Literal["boolListValue"], size: int = ...
                ) -> _DynamicListBuilder[bool]: ...
                @overload
                def init(
                    self: Any, name: Literal["int8ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["int16ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["int32ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["int64ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["uint8ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["uint16ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["uint32ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["uint64ListValue"], size: int = ...
                ) -> _DynamicListBuilder[int]: ...
                @overload
                def init(
                    self: Any, name: Literal["float32ListValue"], size: int = ...
                ) -> _DynamicListBuilder[float]: ...
                @overload
                def init(
                    self: Any, name: Literal["float64ListValue"], size: int = ...
                ) -> _DynamicListBuilder[float]: ...
                @overload
                def init(
                    self: Any, name: Literal["textListValue"], size: int = ...
                ) -> _DynamicListBuilder[str]: ...
                @overload
                def init(
                    self: Any, name: Literal["dataListValue"], size: int = ...
                ) -> _DynamicListBuilder[bytes]: ...
                def init(self: Any, name: str, size: int = ...) -> Any: ...
                def copy(self) -> Store.Container.Entry.ValueBuilder: ...
                def to_bytes(self) -> bytes: ...
                def to_bytes_packed(self) -> bytes: ...
                def to_segments(self) -> list[bytes]: ...
                def as_reader(self) -> Store.Container.Entry.ValueReader: ...
                @staticmethod
                def write(file: BufferedWriter) -> None: ...
                @staticmethod
                def write_packed(file: BufferedWriter) -> None: ...

            class GetkeyResult(Awaitable[GetkeyResult], Protocol):
                key: str

            class GetkeyResultsBuilder(Protocol):
                key: str

            class GetkeyCallContext(Protocol):
                results: Store.Container.Entry.GetkeyResultsBuilder

            def getKey(self) -> GetkeyResult: ...
            class GetkeyRequest(Protocol):
                def send(self) -> Store.Container.Entry.GetkeyResult: ...

            def getKey_request(self) -> GetkeyRequest: ...
            class GetvalueResult(Awaitable[GetvalueResult], Protocol):
                value: Store.Container.Entry.ValueReader
                isUnset: bool

            class GetvalueResultsBuilder(Protocol):
                value: Store.Container.Entry.ValueBuilder
                isUnset: bool

            class GetvalueCallContext(Protocol):
                results: Store.Container.Entry.GetvalueResultsBuilder

            def getValue(self) -> GetvalueResult: ...
            class GetvalueRequest(Protocol):
                def send(self) -> Store.Container.Entry.GetvalueResult: ...

            def getValue_request(self) -> GetvalueRequest: ...
            class SetvalueResult(Awaitable[SetvalueResult], Protocol):
                success: bool

            class SetvalueResultsBuilder(Protocol):
                success: bool

            class SetvalueCallContext(Protocol):
                results: Store.Container.Entry.SetvalueResultsBuilder

            def setValue(
                self, value: Store.Container.Entry.Value | dict[str, Any]
            ) -> SetvalueResult: ...
            class SetvalueRequest(Protocol):
                value: Store.Container.Entry.ValueBuilder
                def send(self) -> Store.Container.Entry.SetvalueResult: ...

            def setValue_request(self) -> SetvalueRequest: ...
            @classmethod
            def _new_client(
                cls, server: Store.Container.Entry.Server
            ) -> Store.Container.Entry: ...
            class Server:
                def getKey(
                    self,
                    _context: Store.Container.Entry.GetkeyCallContext,
                    **kwargs: Any,
                ) -> Awaitable[str]: ...
                def getValue(
                    self,
                    _context: Store.Container.Entry.GetvalueCallContext,
                    **kwargs: Any,
                ) -> Awaitable[tuple[Store.Container.Entry.Value, bool]]: ...
                def setValue(
                    self,
                    value: Store.Container.Entry.ValueReader,
                    _context: Store.Container.Entry.SetvalueCallContext,
                    **kwargs: Any,
                ) -> Awaitable[bool]: ...

        class KeyAndEntry:
            @property
            def key(self) -> str: ...
            @property
            def entry(self) -> Store.Container.Entry: ...
            @staticmethod
            @contextmanager
            def from_bytes(
                data: bytes,
                traversal_limit_in_words: int | None = ...,
                nesting_limit: int | None = ...,
            ) -> Iterator[Store.Container.KeyAndEntryReader]: ...
            @staticmethod
            def from_bytes_packed(
                data: bytes,
                traversal_limit_in_words: int | None = ...,
                nesting_limit: int | None = ...,
            ) -> Store.Container.KeyAndEntryReader: ...
            @staticmethod
            def new_message(
                num_first_segment_words: int | None = None,
                allocate_seg_callable: Any = None,
                key: str | None = None,
                entry: Store.Container.Entry
                | Store.Container.Entry.Server
                | None = None,
            ) -> Store.Container.KeyAndEntryBuilder: ...
            @staticmethod
            def read(
                file: BinaryIO,
                traversal_limit_in_words: int | None = ...,
                nesting_limit: int | None = ...,
            ) -> Store.Container.KeyAndEntryReader: ...
            @staticmethod
            def read_packed(
                file: BinaryIO,
                traversal_limit_in_words: int | None = ...,
                nesting_limit: int | None = ...,
            ) -> Store.Container.KeyAndEntryReader: ...
            def to_dict(self) -> dict[str, Any]: ...

        class KeyAndEntryReader(Store.Container.KeyAndEntry):
            def as_builder(self) -> Store.Container.KeyAndEntryBuilder: ...

        class KeyAndEntryBuilder(Store.Container.KeyAndEntry):
            @property
            def key(self) -> str: ...
            @key.setter
            def key(self, value: str) -> None: ...
            @property
            def entry(self) -> Store.Container.Entry: ...
            @entry.setter
            def entry(
                self, value: Store.Container.Entry | Store.Container.Entry.Server
            ) -> None: ...
            @staticmethod
            def from_dict(
                dictionary: dict[str, Any],
            ) -> Store.Container.KeyAndEntryBuilder: ...
            def copy(self) -> Store.Container.KeyAndEntryBuilder: ...
            def to_bytes(self) -> bytes: ...
            def to_bytes_packed(self) -> bytes: ...
            def to_segments(self) -> list[bytes]: ...
            def as_reader(self) -> Store.Container.KeyAndEntryReader: ...
            @staticmethod
            def write(file: BufferedWriter) -> None: ...
            @staticmethod
            def write_packed(file: BufferedWriter) -> None: ...

        class ExportResult(Awaitable[ExportResult], Protocol):
            json: str

        class ExportResultsBuilder(Protocol):
            json: str

        class ExportCallContext(Protocol):
            results: Store.Container.ExportResultsBuilder

        def export(self) -> ExportResult: ...
        class ExportRequest(Protocol):
            def send(self) -> Store.Container.ExportResult: ...

        def export_request(self) -> ExportRequest: ...
        class DownloadentriesResult(Awaitable[DownloadentriesResult], Protocol):
            entries: Any

        class DownloadentriesResultsBuilder(Protocol):
            entries: Any

        class DownloadentriesCallContext(Protocol):
            results: Store.Container.DownloadentriesResultsBuilder

        def downloadEntries(self) -> DownloadentriesResult: ...
        class DownloadentriesRequest(Protocol):
            def send(self) -> Store.Container.DownloadentriesResult: ...

        def downloadEntries_request(self) -> DownloadentriesRequest: ...
        class ListentriesResult(Awaitable[ListentriesResult], Protocol):
            entries: Sequence[Store.Container.KeyAndEntryReader]

        class ListentriesResultsBuilder(Protocol):
            entries: Sequence[Store.Container.KeyAndEntryBuilder]

        class ListentriesCallContext(Protocol):
            results: Store.Container.ListentriesResultsBuilder

        def listEntries(self) -> ListentriesResult: ...
        class ListentriesRequest(Protocol):
            def send(self) -> Store.Container.ListentriesResult: ...

        def listEntries_request(self) -> ListentriesRequest: ...
        class GetentryResult(Awaitable[GetentryResult], Protocol):
            entry: Store.Container.Entry

        class GetentryResultsBuilder(Protocol):
            entry: Store.Container.Entry

        class GetentryCallContext(Protocol):
            results: Store.Container.GetentryResultsBuilder

        def getEntry(self, key: str) -> GetentryResult: ...
        class GetentryRequest(Protocol):
            key: str
            def send(self) -> Store.Container.GetentryResult: ...

        def getEntry_request(self) -> GetentryRequest: ...
        class RemoveentryResult(Awaitable[RemoveentryResult], Protocol):
            success: bool

        class RemoveentryResultsBuilder(Protocol):
            success: bool

        class RemoveentryCallContext(Protocol):
            results: Store.Container.RemoveentryResultsBuilder

        def removeEntry(self, key: str) -> RemoveentryResult: ...
        class RemoveentryRequest(Protocol):
            key: str
            def send(self) -> Store.Container.RemoveentryResult: ...

        def removeEntry_request(self) -> RemoveentryRequest: ...
        class ClearResult(Awaitable[ClearResult], Protocol):
            success: bool

        class ClearResultsBuilder(Protocol):
            success: bool

        class ClearCallContext(Protocol):
            results: Store.Container.ClearResultsBuilder

        def clear(self) -> ClearResult: ...
        class ClearRequest(Protocol):
            def send(self) -> Store.Container.ClearResult: ...

        def clear_request(self) -> ClearRequest: ...
        class AddentryResult(Awaitable[AddentryResult], Protocol):
            entry: Store.Container.Entry
            success: bool

        class AddentryResultsBuilder(Protocol):
            entry: Store.Container.Entry
            success: bool

        class AddentryCallContext(Protocol):
            results: Store.Container.AddentryResultsBuilder

        def addEntry(
            self,
            key: str,
            value: Store.Container.Entry.Value | dict[str, Any],
            replaceExisting: bool,
        ) -> AddentryResult: ...
        class AddentryRequest(Protocol):
            key: str
            value: Store.Container.Entry.ValueBuilder
            replaceExisting: bool
            def send(self) -> Store.Container.AddentryResult: ...

        def addEntry_request(self) -> AddentryRequest: ...
        @classmethod
        def _new_client(
            cls,
            server: Store.Container.Server | Identifiable.Server | Persistent.Server,
        ) -> Store.Container: ...
        class Server(Identifiable.Server, Persistent.Server):
            def export(
                self, _context: Store.Container.ExportCallContext, **kwargs: Any
            ) -> Awaitable[str]: ...
            def downloadEntries(
                self,
                _context: Store.Container.DownloadentriesCallContext,
                **kwargs: Any,
            ) -> Awaitable[Any]: ...
            def listEntries(
                self, _context: Store.Container.ListentriesCallContext, **kwargs: Any
            ) -> Awaitable[Sequence[Store.Container.KeyAndEntry]]: ...
            def getEntry(
                self,
                key: str,
                _context: Store.Container.GetentryCallContext,
                **kwargs: Any,
            ) -> Awaitable[Store.Container.Entry | Store.Container.Entry.Server]: ...
            def removeEntry(
                self,
                key: str,
                _context: Store.Container.RemoveentryCallContext,
                **kwargs: Any,
            ) -> Awaitable[bool]: ...
            def clear(
                self, _context: Store.Container.ClearCallContext, **kwargs: Any
            ) -> Awaitable[bool]: ...
            def addEntry(
                self,
                key: str,
                value: Store.Container.Entry.ValueReader,
                replaceExisting: bool,
                _context: Store.Container.AddentryCallContext,
                **kwargs: Any,
            ) -> Awaitable[tuple[Store.Container.Entry, bool]]: ...

    class InfoAndContainer:
        @property
        def id(self) -> str: ...
        @property
        def name(self) -> str: ...
        @property
        def container(self) -> Store.Container: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Store.InfoAndContainerReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Store.InfoAndContainerReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            id: str | None = None,
            name: str | None = None,
            container: Store.Container | Store.Container.Server | None = None,
        ) -> Store.InfoAndContainerBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Store.InfoAndContainerReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Store.InfoAndContainerReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class InfoAndContainerReader(Store.InfoAndContainer):
        def as_builder(self) -> Store.InfoAndContainerBuilder: ...

    class InfoAndContainerBuilder(Store.InfoAndContainer):
        @property
        def id(self) -> str: ...
        @id.setter
        def id(self, value: str) -> None: ...
        @property
        def name(self) -> str: ...
        @name.setter
        def name(self, value: str) -> None: ...
        @property
        def container(self) -> Store.Container: ...
        @container.setter
        def container(
            self, value: Store.Container | Store.Container.Server
        ) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Store.InfoAndContainerBuilder: ...
        def copy(self) -> Store.InfoAndContainerBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Store.InfoAndContainerReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class ImportExportData:
        @property
        def info(self) -> IdInformation: ...
        @property
        def entries(self) -> Sequence[Pair]: ...
        @property
        def isAnyValue(self) -> Sequence[bool]: ...
        def init(self, name: Literal["info"]) -> IdInformation: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Store.ImportExportDataReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Store.ImportExportDataReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            info: IdInformationBuilder | dict[str, Any] | None = None,
            entries: Sequence[PairBuilder] | Sequence[dict[str, Any]] | None = None,
            isAnyValue: Sequence[bool] | None = None,
        ) -> Store.ImportExportDataBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Store.ImportExportDataReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Store.ImportExportDataReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class ImportExportDataReader(Store.ImportExportData):
        @property
        def info(self) -> IdInformationReader: ...
        @property
        def entries(self) -> Sequence[PairReader]: ...
        def as_builder(self) -> Store.ImportExportDataBuilder: ...

    class ImportExportDataBuilder(Store.ImportExportData):
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
        def entries(self) -> Sequence[PairBuilder]: ...
        @entries.setter
        def entries(
            self,
            value: Sequence[Pair | PairBuilder | PairReader] | Sequence[dict[str, Any]],
        ) -> None: ...
        @property
        def isAnyValue(self) -> Sequence[bool]: ...
        @isAnyValue.setter
        def isAnyValue(self, value: Sequence[bool]) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Store.ImportExportDataBuilder: ...
        @overload
        def init(self: Any, name: Literal["info"]) -> IdInformationBuilder: ...
        @overload
        def init(
            self: Any, name: Literal["entries"], size: int = ...
        ) -> _DynamicListBuilder[PairBuilder]: ...
        @overload
        def init(
            self: Any, name: Literal["isAnyValue"], size: int = ...
        ) -> _DynamicListBuilder[bool]: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        def copy(self) -> Store.ImportExportDataBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Store.ImportExportDataReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class NewcontainerResult(Awaitable[NewcontainerResult], Protocol):
        container: Store.Container

    class NewcontainerResultsBuilder(Protocol):
        container: Store.Container

    class NewcontainerCallContext(Protocol):
        results: Store.NewcontainerResultsBuilder

    def newContainer(self, name: str, description: str) -> NewcontainerResult: ...
    class NewcontainerRequest(Protocol):
        name: str
        description: str
        def send(self) -> Store.NewcontainerResult: ...

    def newContainer_request(self) -> NewcontainerRequest: ...
    class ContainerwithidResult(Awaitable[ContainerwithidResult], Protocol):
        container: Store.Container

    class ContainerwithidResultsBuilder(Protocol):
        container: Store.Container

    class ContainerwithidCallContext(Protocol):
        results: Store.ContainerwithidResultsBuilder

    def containerWithId(self, id: str) -> ContainerwithidResult: ...
    class ContainerwithidRequest(Protocol):
        id: str
        def send(self) -> Store.ContainerwithidResult: ...

    def containerWithId_request(self) -> ContainerwithidRequest: ...
    class ListcontainersResult(Awaitable[ListcontainersResult], Protocol):
        containers: Sequence[Store.InfoAndContainerReader]

    class ListcontainersResultsBuilder(Protocol):
        containers: Sequence[Store.InfoAndContainerBuilder]

    class ListcontainersCallContext(Protocol):
        results: Store.ListcontainersResultsBuilder

    def listContainers(self) -> ListcontainersResult: ...
    class ListcontainersRequest(Protocol):
        def send(self) -> Store.ListcontainersResult: ...

    def listContainers_request(self) -> ListcontainersRequest: ...
    class RemovecontainerResult(Awaitable[RemovecontainerResult], Protocol):
        success: bool

    class RemovecontainerResultsBuilder(Protocol):
        success: bool

    class RemovecontainerCallContext(Protocol):
        results: Store.RemovecontainerResultsBuilder

    def removeContainer(self, id: str) -> RemovecontainerResult: ...
    class RemovecontainerRequest(Protocol):
        id: str
        def send(self) -> Store.RemovecontainerResult: ...

    def removeContainer_request(self) -> RemovecontainerRequest: ...
    class ImportcontainerResult(Awaitable[ImportcontainerResult], Protocol):
        container: Store.Container

    class ImportcontainerResultsBuilder(Protocol):
        container: Store.Container

    class ImportcontainerCallContext(Protocol):
        results: Store.ImportcontainerResultsBuilder

    def importContainer(self, json: str) -> ImportcontainerResult: ...
    class ImportcontainerRequest(Protocol):
        json: str
        def send(self) -> Store.ImportcontainerResult: ...

    def importContainer_request(self) -> ImportcontainerRequest: ...
    @classmethod
    def _new_client(
        cls, server: Store.Server | Identifiable.Server | Persistent.Server
    ) -> Store: ...
    class Server(Identifiable.Server, Persistent.Server):
        def newContainer(
            self,
            name: str,
            description: str,
            _context: Store.NewcontainerCallContext,
            **kwargs: Any,
        ) -> Awaitable[Store.Container | Store.Container.Server]: ...
        def containerWithId(
            self, id: str, _context: Store.ContainerwithidCallContext, **kwargs: Any
        ) -> Awaitable[Store.Container | Store.Container.Server]: ...
        def listContainers(
            self, _context: Store.ListcontainersCallContext, **kwargs: Any
        ) -> Awaitable[Sequence[Store.InfoAndContainer]]: ...
        def removeContainer(
            self, id: str, _context: Store.RemovecontainerCallContext, **kwargs: Any
        ) -> Awaitable[bool]: ...
        def importContainer(
            self, json: str, _context: Store.ImportcontainerCallContext, **kwargs: Any
        ) -> Awaitable[Store.Container | Store.Container.Server]: ...
