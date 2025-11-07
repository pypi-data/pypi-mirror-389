"""This is an automatically generated stub for `grid.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator, Sequence
from contextlib import contextmanager
from enum import Enum
from io import BufferedWriter
from typing import Any, BinaryIO, Literal, Protocol, overload

from .common_capnp import Identifiable
from .geo_capnp import LatLonCoord, LatLonCoordBuilder, LatLonCoordReader
from .persistence_capnp import Persistent

class Aggregation(Enum):
    none = "none"
    wAvg = "wAvg"
    wMedian = "wMedian"
    min = "min"
    max = "max"
    sum = "sum"
    iAvg = "iAvg"
    iMedian = "iMedian"
    avg = "avg"
    median = "median"
    wSum = "wSum"
    iSum = "iSum"
    wMin = "wMin"
    iMin = "iMin"
    wMax = "wMax"
    iMax = "iMax"

class Grid(Identifiable, Persistent, Protocol):
    class Value:
        @property
        def f(self) -> float: ...
        @property
        def i(self) -> int: ...
        @property
        def ui(self) -> int: ...
        @property
        def no(self) -> bool: ...
        def which(self) -> Literal["f", "i", "ui", "no"]: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Grid.ValueReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.ValueReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            f: float | None = None,
            i: int | None = None,
            ui: int | None = None,
            no: bool | None = None,
        ) -> Grid.ValueBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.ValueReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.ValueReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class ValueReader(Grid.Value):
        def as_builder(self) -> Grid.ValueBuilder: ...

    class ValueBuilder(Grid.Value):
        @property
        def f(self) -> float: ...
        @f.setter
        def f(self, value: float) -> None: ...
        @property
        def i(self) -> int: ...
        @i.setter
        def i(self, value: int) -> None: ...
        @property
        def ui(self) -> int: ...
        @ui.setter
        def ui(self, value: int) -> None: ...
        @property
        def no(self) -> bool: ...
        @no.setter
        def no(self, value: bool) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Grid.ValueBuilder: ...
        def copy(self) -> Grid.ValueBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Grid.ValueReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class Resolution:
        @property
        def meter(self) -> int: ...
        @property
        def degree(self) -> float: ...
        def which(self) -> Literal["meter", "degree"]: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Grid.ResolutionReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.ResolutionReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            meter: int | None = None,
            degree: float | None = None,
        ) -> Grid.ResolutionBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.ResolutionReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.ResolutionReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class ResolutionReader(Grid.Resolution):
        def as_builder(self) -> Grid.ResolutionBuilder: ...

    class ResolutionBuilder(Grid.Resolution):
        @property
        def meter(self) -> int: ...
        @meter.setter
        def meter(self, value: int) -> None: ...
        @property
        def degree(self) -> float: ...
        @degree.setter
        def degree(self, value: float) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Grid.ResolutionBuilder: ...
        def copy(self) -> Grid.ResolutionBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Grid.ResolutionReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class RowCol:
        @property
        def row(self) -> int: ...
        @property
        def col(self) -> int: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Grid.RowColReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.RowColReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            row: int | None = None,
            col: int | None = None,
        ) -> Grid.RowColBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.RowColReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.RowColReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class RowColReader(Grid.RowCol):
        def as_builder(self) -> Grid.RowColBuilder: ...

    class RowColBuilder(Grid.RowCol):
        @property
        def row(self) -> int: ...
        @row.setter
        def row(self, value: int) -> None: ...
        @property
        def col(self) -> int: ...
        @col.setter
        def col(self, value: int) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Grid.RowColBuilder: ...
        def copy(self) -> Grid.RowColBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Grid.RowColReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class AggregationPart:
        @property
        def value(self) -> Grid.Value: ...
        @property
        def rowCol(self) -> Grid.RowCol: ...
        @property
        def areaFrac(self) -> float: ...
        @property
        def iValue(self) -> float: ...
        @overload
        def init(self, name: Literal["value"]) -> Grid.Value: ...
        @overload
        def init(self, name: Literal["rowCol"]) -> Grid.RowCol: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Grid.AggregationPartReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.AggregationPartReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            value: Grid.ValueBuilder | dict[str, Any] | None = None,
            rowCol: Grid.RowColBuilder | dict[str, Any] | None = None,
            areaFrac: float | None = None,
            iValue: float | None = None,
        ) -> Grid.AggregationPartBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.AggregationPartReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.AggregationPartReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class AggregationPartReader(Grid.AggregationPart):
        @property
        def value(self) -> Grid.ValueReader: ...
        @property
        def rowCol(self) -> Grid.RowColReader: ...
        def as_builder(self) -> Grid.AggregationPartBuilder: ...

    class AggregationPartBuilder(Grid.AggregationPart):
        @property
        def value(self) -> Grid.ValueBuilder: ...
        @value.setter
        def value(
            self,
            value: Grid.Value | Grid.ValueBuilder | Grid.ValueReader | dict[str, Any],
        ) -> None: ...
        @property
        def rowCol(self) -> Grid.RowColBuilder: ...
        @rowCol.setter
        def rowCol(
            self,
            value: Grid.RowCol
            | Grid.RowColBuilder
            | Grid.RowColReader
            | dict[str, Any],
        ) -> None: ...
        @property
        def areaFrac(self) -> float: ...
        @areaFrac.setter
        def areaFrac(self, value: float) -> None: ...
        @property
        def iValue(self) -> float: ...
        @iValue.setter
        def iValue(self, value: float) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Grid.AggregationPartBuilder: ...
        @overload
        def init(self: Any, name: Literal["value"]) -> Grid.ValueBuilder: ...
        @overload
        def init(self: Any, name: Literal["rowCol"]) -> Grid.RowColBuilder: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        def copy(self) -> Grid.AggregationPartBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Grid.AggregationPartReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class Location:
        @property
        def latLonCoord(self) -> LatLonCoord: ...
        @property
        def rowCol(self) -> Grid.RowCol: ...
        @property
        def value(self) -> Grid.Value: ...
        @overload
        def init(self, name: Literal["latLonCoord"]) -> LatLonCoord: ...
        @overload
        def init(self, name: Literal["rowCol"]) -> Grid.RowCol: ...
        @overload
        def init(self, name: Literal["value"]) -> Grid.Value: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Grid.LocationReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.LocationReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            latLonCoord: LatLonCoordBuilder | dict[str, Any] | None = None,
            rowCol: Grid.RowColBuilder | dict[str, Any] | None = None,
            value: Grid.ValueBuilder | dict[str, Any] | None = None,
        ) -> Grid.LocationBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.LocationReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Grid.LocationReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class LocationReader(Grid.Location):
        @property
        def latLonCoord(self) -> LatLonCoordReader: ...
        @property
        def rowCol(self) -> Grid.RowColReader: ...
        @property
        def value(self) -> Grid.ValueReader: ...
        def as_builder(self) -> Grid.LocationBuilder: ...

    class LocationBuilder(Grid.Location):
        @property
        def latLonCoord(self) -> LatLonCoordBuilder: ...
        @latLonCoord.setter
        def latLonCoord(
            self,
            value: LatLonCoord
            | LatLonCoordBuilder
            | LatLonCoordReader
            | dict[str, Any],
        ) -> None: ...
        @property
        def rowCol(self) -> Grid.RowColBuilder: ...
        @rowCol.setter
        def rowCol(
            self,
            value: Grid.RowCol
            | Grid.RowColBuilder
            | Grid.RowColReader
            | dict[str, Any],
        ) -> None: ...
        @property
        def value(self) -> Grid.ValueBuilder: ...
        @value.setter
        def value(
            self,
            value: Grid.Value | Grid.ValueBuilder | Grid.ValueReader | dict[str, Any],
        ) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Grid.LocationBuilder: ...
        @overload
        def init(self: Any, name: Literal["latLonCoord"]) -> LatLonCoordBuilder: ...
        @overload
        def init(self: Any, name: Literal["rowCol"]) -> Grid.RowColBuilder: ...
        @overload
        def init(self: Any, name: Literal["value"]) -> Grid.ValueBuilder: ...
        def init(self: Any, name: str, size: int = ...) -> Any: ...
        def copy(self) -> Grid.LocationBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Grid.LocationReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class Callback(Protocol):
        class SendcellsResult(Awaitable[SendcellsResult], Protocol):
            locations: Sequence[Grid.LocationReader]

        class SendcellsResultsBuilder(Protocol):
            locations: Sequence[Grid.LocationBuilder]

        class SendcellsCallContext(Protocol):
            results: Grid.Callback.SendcellsResultsBuilder

        def sendCells(self, maxCount: int) -> SendcellsResult: ...
        class SendcellsRequest(Protocol):
            maxCount: int
            def send(self) -> Grid.Callback.SendcellsResult: ...

        def sendCells_request(self) -> SendcellsRequest: ...
        @classmethod
        def _new_client(cls, server: Grid.Callback.Server) -> Grid.Callback: ...
        class Server:
            def sendCells(
                self,
                maxCount: int,
                _context: Grid.Callback.SendcellsCallContext,
                **kwargs: Any,
            ) -> Awaitable[Sequence[Grid.Location]]: ...

    class ClosestvalueatResult(Awaitable[ClosestvalueatResult], Protocol):
        val: Grid.ValueReader
        tl: Grid.RowColReader
        br: Grid.RowColReader
        aggParts: Sequence[Grid.AggregationPartReader]

    class ClosestvalueatResultsBuilder(Protocol):
        val: Grid.ValueBuilder
        tl: Grid.RowColBuilder
        br: Grid.RowColBuilder
        aggParts: Sequence[Grid.AggregationPartBuilder]

    class ClosestvalueatCallContext(Protocol):
        results: Grid.ClosestvalueatResultsBuilder

    def closestValueAt(
        self,
        latlonCoord: LatLonCoord | dict[str, Any],
        ignoreNoData: bool,
        resolution: Grid.Resolution | dict[str, Any],
        agg: Aggregation
        | Literal[
            "none",
            "wAvg",
            "wMedian",
            "min",
            "max",
            "sum",
            "iAvg",
            "iMedian",
            "avg",
            "median",
            "wSum",
            "iSum",
            "wMin",
            "iMin",
            "wMax",
            "iMax",
        ],
        returnRowCols: bool,
        includeAggParts: bool,
    ) -> ClosestvalueatResult: ...
    class ClosestvalueatRequest(Protocol):
        latlonCoord: LatLonCoordBuilder
        ignoreNoData: bool
        resolution: Grid.ResolutionBuilder
        agg: Aggregation
        returnRowCols: bool
        includeAggParts: bool
        def send(self) -> Grid.ClosestvalueatResult: ...

    def closestValueAt_request(self) -> ClosestvalueatRequest: ...
    class ResolutionResult(Awaitable[ResolutionResult], Protocol):
        res: Grid.ResolutionReader

    class ResolutionResultsBuilder(Protocol):
        res: Grid.ResolutionBuilder

    class ResolutionCallContext(Protocol):
        results: Grid.ResolutionResultsBuilder

    def resolution(self) -> ResolutionResult: ...
    class ResolutionRequest(Protocol):
        def send(self) -> Grid.ResolutionResult: ...

    def resolution_request(self) -> ResolutionRequest: ...
    class DimensionResult(Awaitable[DimensionResult], Protocol):
        rows: int
        cols: int

    class DimensionResultsBuilder(Protocol):
        rows: int
        cols: int

    class DimensionCallContext(Protocol):
        results: Grid.DimensionResultsBuilder

    def dimension(self) -> DimensionResult: ...
    class DimensionRequest(Protocol):
        def send(self) -> Grid.DimensionResult: ...

    def dimension_request(self) -> DimensionRequest: ...
    class NodatavalueResult(Awaitable[NodatavalueResult], Protocol):
        nodata: Grid.ValueReader

    class NodatavalueResultsBuilder(Protocol):
        nodata: Grid.ValueBuilder

    class NodatavalueCallContext(Protocol):
        results: Grid.NodatavalueResultsBuilder

    def noDataValue(self) -> NodatavalueResult: ...
    class NodatavalueRequest(Protocol):
        def send(self) -> Grid.NodatavalueResult: ...

    def noDataValue_request(self) -> NodatavalueRequest: ...
    class ValueatResult(Awaitable[ValueatResult], Protocol):
        val: Grid.ValueReader
        aggParts: Sequence[Grid.AggregationPartReader]

    class ValueatResultsBuilder(Protocol):
        val: Grid.ValueBuilder
        aggParts: Sequence[Grid.AggregationPartBuilder]

    class ValueatCallContext(Protocol):
        results: Grid.ValueatResultsBuilder

    def valueAt(
        self,
        row: int,
        col: int,
        resolution: Grid.Resolution | dict[str, Any],
        agg: Aggregation
        | Literal[
            "none",
            "wAvg",
            "wMedian",
            "min",
            "max",
            "sum",
            "iAvg",
            "iMedian",
            "avg",
            "median",
            "wSum",
            "iSum",
            "wMin",
            "iMin",
            "wMax",
            "iMax",
        ],
        includeAggParts: bool,
    ) -> ValueatResult: ...
    class ValueatRequest(Protocol):
        row: int
        col: int
        resolution: Grid.ResolutionBuilder
        agg: Aggregation
        includeAggParts: bool
        def send(self) -> Grid.ValueatResult: ...

    def valueAt_request(self) -> ValueatRequest: ...
    class LatlonboundsResult(Awaitable[LatlonboundsResult], Protocol):
        tl: LatLonCoordReader
        tr: LatLonCoordReader
        br: LatLonCoordReader
        bl: LatLonCoordReader

    class LatlonboundsResultsBuilder(Protocol):
        tl: LatLonCoordBuilder
        tr: LatLonCoordBuilder
        br: LatLonCoordBuilder
        bl: LatLonCoordBuilder

    class LatlonboundsCallContext(Protocol):
        results: Grid.LatlonboundsResultsBuilder

    def latLonBounds(self, useCellCenter: bool) -> LatlonboundsResult: ...
    class LatlonboundsRequest(Protocol):
        useCellCenter: bool
        def send(self) -> Grid.LatlonboundsResult: ...

    def latLonBounds_request(self) -> LatlonboundsRequest: ...
    class StreamcellsResult(Awaitable[StreamcellsResult], Protocol):
        callback: Grid.Callback

    class StreamcellsResultsBuilder(Protocol):
        callback: Grid.Callback

    class StreamcellsCallContext(Protocol):
        results: Grid.StreamcellsResultsBuilder

    def streamCells(
        self,
        topLeft: Grid.RowCol | dict[str, Any],
        bottomRight: Grid.RowCol | dict[str, Any],
    ) -> StreamcellsResult: ...
    class StreamcellsRequest(Protocol):
        topLeft: Grid.RowColBuilder
        bottomRight: Grid.RowColBuilder
        def send(self) -> Grid.StreamcellsResult: ...

    def streamCells_request(self) -> StreamcellsRequest: ...
    class UnitResult(Awaitable[UnitResult], Protocol):
        unit: str

    class UnitResultsBuilder(Protocol):
        unit: str

    class UnitCallContext(Protocol):
        results: Grid.UnitResultsBuilder

    def unit(self) -> UnitResult: ...
    class UnitRequest(Protocol):
        def send(self) -> Grid.UnitResult: ...

    def unit_request(self) -> UnitRequest: ...
    @classmethod
    def _new_client(
        cls, server: Grid.Server | Identifiable.Server | Persistent.Server
    ) -> Grid: ...
    class Server(Identifiable.Server, Persistent.Server):
        def closestValueAt(
            self,
            latlonCoord: LatLonCoordReader,
            ignoreNoData: bool,
            resolution: Grid.ResolutionReader,
            agg: Aggregation
            | Literal[
                "none",
                "wAvg",
                "wMedian",
                "min",
                "max",
                "sum",
                "iAvg",
                "iMedian",
                "avg",
                "median",
                "wSum",
                "iSum",
                "wMin",
                "iMin",
                "wMax",
                "iMax",
            ],
            returnRowCols: bool,
            includeAggParts: bool,
            _context: Grid.ClosestvalueatCallContext,
            **kwargs: Any,
        ) -> Awaitable[
            tuple[Grid.Value, Grid.RowCol, Grid.RowCol, Sequence[Grid.AggregationPart]]
        ]: ...
        def resolution(
            self, _context: Grid.ResolutionCallContext, **kwargs: Any
        ) -> Awaitable[Grid.Resolution]: ...
        def dimension(
            self, _context: Grid.DimensionCallContext, **kwargs: Any
        ) -> Awaitable[tuple[int, int]]: ...
        def noDataValue(
            self, _context: Grid.NodatavalueCallContext, **kwargs: Any
        ) -> Awaitable[Grid.Value]: ...
        def valueAt(
            self,
            row: int,
            col: int,
            resolution: Grid.ResolutionReader,
            agg: Aggregation
            | Literal[
                "none",
                "wAvg",
                "wMedian",
                "min",
                "max",
                "sum",
                "iAvg",
                "iMedian",
                "avg",
                "median",
                "wSum",
                "iSum",
                "wMin",
                "iMin",
                "wMax",
                "iMax",
            ],
            includeAggParts: bool,
            _context: Grid.ValueatCallContext,
            **kwargs: Any,
        ) -> Awaitable[tuple[Grid.Value, Sequence[Grid.AggregationPart]]]: ...
        def latLonBounds(
            self,
            useCellCenter: bool,
            _context: Grid.LatlonboundsCallContext,
            **kwargs: Any,
        ) -> Awaitable[tuple[LatLonCoord, LatLonCoord, LatLonCoord, LatLonCoord]]: ...
        def streamCells(
            self,
            topLeft: Grid.RowColReader,
            bottomRight: Grid.RowColReader,
            _context: Grid.StreamcellsCallContext,
            **kwargs: Any,
        ) -> Awaitable[Grid.Callback | Grid.Callback.Server]: ...
        def unit(
            self, _context: Grid.UnitCallContext, **kwargs: Any
        ) -> Awaitable[str]: ...
