"""This is an automatically generated stub for `registry.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator, Sequence
from contextlib import contextmanager
from io import BufferedWriter
from typing import Any, BinaryIO, Literal, NamedTuple, Protocol

from .common_capnp import (
    Identifiable,
    IdInformation,
    IdInformationBuilder,
    IdInformationReader,
)
from .persistence_capnp import Restorer, VatId, VatIdBuilder, VatIdReader

class Admin(Identifiable, Protocol):
    class AddcategoryResult(Awaitable[AddcategoryResult], Protocol):
        success: bool

    class AddcategoryResultsBuilder(Protocol):
        success: bool

    class AddcategoryCallContext(Protocol):
        results: Admin.AddcategoryResultsBuilder

    def addCategory(self, category: Any, upsert: bool) -> AddcategoryResult: ...
    class AddcategoryRequest(Protocol):
        category: Any
        upsert: bool
        def send(self) -> Admin.AddcategoryResult: ...

    def addCategory_request(self) -> AddcategoryRequest: ...
    class RemovecategoryResult(Awaitable[RemovecategoryResult], Protocol):
        removedObjects: Sequence[Identifiable]

    class RemovecategoryResultsBuilder(Protocol):
        removedObjects: Sequence[Identifiable]

    class RemovecategoryCallContext(Protocol):
        results: Admin.RemovecategoryResultsBuilder

    def removeCategory(
        self, categoryId: str, moveObjectsToCategoryId: str
    ) -> RemovecategoryResult: ...
    class RemovecategoryRequest(Protocol):
        categoryId: str
        moveObjectsToCategoryId: str
        def send(self) -> Admin.RemovecategoryResult: ...

    def removeCategory_request(self) -> RemovecategoryRequest: ...
    class MoveobjectsResult(Awaitable[MoveobjectsResult], Protocol):
        movedObjectIds: Sequence[str]

    class MoveobjectsResultsBuilder(Protocol):
        movedObjectIds: Sequence[str]

    class MoveobjectsCallContext(Protocol):
        results: Admin.MoveobjectsResultsBuilder

    def moveObjects(
        self, objectIds: Sequence[str], toCatId: str
    ) -> MoveobjectsResult: ...
    class MoveobjectsRequest(Protocol):
        objectIds: Sequence[str]
        toCatId: str
        def send(self) -> Admin.MoveobjectsResult: ...

    def moveObjects_request(self) -> MoveobjectsRequest: ...
    class RemoveobjectsResult(Awaitable[RemoveobjectsResult], Protocol):
        removedObjects: Sequence[Identifiable]

    class RemoveobjectsResultsBuilder(Protocol):
        removedObjects: Sequence[Identifiable]

    class RemoveobjectsCallContext(Protocol):
        results: Admin.RemoveobjectsResultsBuilder

    def removeObjects(self, objectIds: Sequence[str]) -> RemoveobjectsResult: ...
    class RemoveobjectsRequest(Protocol):
        objectIds: Sequence[str]
        def send(self) -> Admin.RemoveobjectsResult: ...

    def removeObjects_request(self) -> RemoveobjectsRequest: ...
    class RegistryResult(Awaitable[RegistryResult], Protocol):
        registry: Any

    class RegistryResultsBuilder(Protocol):
        registry: Any

    class RegistryCallContext(Protocol):
        results: Admin.RegistryResultsBuilder

    def registry(self) -> RegistryResult: ...
    class RegistryRequest(Protocol):
        def send(self) -> Admin.RegistryResult: ...

    def registry_request(self) -> RegistryRequest: ...
    @classmethod
    def _new_client(cls, server: Admin.Server | Identifiable.Server) -> Admin: ...
    class Server(Identifiable.Server):
        def addCategory(
            self,
            category: Any,
            upsert: bool,
            _context: Admin.AddcategoryCallContext,
            **kwargs: Any,
        ) -> Awaitable[bool]: ...
        def removeCategory(
            self,
            categoryId: str,
            moveObjectsToCategoryId: str,
            _context: Admin.RemovecategoryCallContext,
            **kwargs: Any,
        ) -> Awaitable[Sequence[Identifiable]]: ...
        def moveObjects(
            self,
            objectIds: Sequence[str],
            toCatId: str,
            _context: Admin.MoveobjectsCallContext,
            **kwargs: Any,
        ) -> Awaitable[Sequence[str]]: ...
        def removeObjects(
            self,
            objectIds: Sequence[str],
            _context: Admin.RemoveobjectsCallContext,
            **kwargs: Any,
        ) -> Awaitable[Sequence[Identifiable]]: ...
        def registry(
            self, _context: Admin.RegistryCallContext, **kwargs: Any
        ) -> Awaitable[Any]: ...

class Registry(Identifiable, Protocol):
    class Entry:
        @property
        def categoryId(self) -> str: ...
        @property
        def ref(self) -> Identifiable: ...
        @property
        def name(self) -> str: ...
        @property
        def id(self) -> str: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Registry.EntryReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registry.EntryReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            categoryId: str | None = None,
            ref: Identifiable | Identifiable.Server | None = None,
            name: str | None = None,
            id: str | None = None,
        ) -> Registry.EntryBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registry.EntryReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registry.EntryReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class EntryReader(Registry.Entry):
        def as_builder(self) -> Registry.EntryBuilder: ...

    class EntryBuilder(Registry.Entry):
        @property
        def categoryId(self) -> str: ...
        @categoryId.setter
        def categoryId(self, value: str) -> None: ...
        @property
        def ref(self) -> Identifiable: ...
        @ref.setter
        def ref(self, value: Identifiable | Identifiable.Server) -> None: ...
        @property
        def name(self) -> str: ...
        @name.setter
        def name(self, value: str) -> None: ...
        @property
        def id(self) -> str: ...
        @id.setter
        def id(self, value: str) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Registry.EntryBuilder: ...
        def copy(self) -> Registry.EntryBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Registry.EntryReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class SupportedcategoriesResult(Awaitable[SupportedcategoriesResult], Protocol):
        cats: Any

    class SupportedcategoriesResultsBuilder(Protocol):
        cats: Any

    class SupportedcategoriesCallContext(Protocol):
        results: Registry.SupportedcategoriesResultsBuilder

    def supportedCategories(self) -> SupportedcategoriesResult: ...
    class SupportedcategoriesRequest(Protocol):
        def send(self) -> Registry.SupportedcategoriesResult: ...

    def supportedCategories_request(self) -> SupportedcategoriesRequest: ...
    class CategoryinfoResult(Protocol):
        id: str
        name: str
        description: str

    class CategoryinfoCallContext(Protocol):
        results: Registry.CategoryinfoResult

    def categoryInfo(
        self, categoryId: str
    ) -> Awaitable[Registry.CategoryinfoResult]: ...
    class CategoryinfoRequest(Protocol):
        categoryId: str
        def send(self) -> Awaitable[Registry.CategoryinfoResult]: ...

    def categoryInfo_request(self) -> CategoryinfoRequest: ...
    class EntriesResult(Awaitable[EntriesResult], Protocol):
        entries: Sequence[Registry.EntryReader]

    class EntriesResultsBuilder(Protocol):
        entries: Sequence[Registry.EntryBuilder]

    class EntriesCallContext(Protocol):
        results: Registry.EntriesResultsBuilder

    def entries(self, categoryId: str) -> EntriesResult: ...
    class EntriesRequest(Protocol):
        categoryId: str
        def send(self) -> Registry.EntriesResult: ...

    def entries_request(self) -> EntriesRequest: ...
    @classmethod
    def _new_client(cls, server: Registry.Server | Identifiable.Server) -> Registry: ...
    class Server(Identifiable.Server):
        class CategoryinfoResult(NamedTuple):
            id: str
            name: str
            description: str

        def supportedCategories(
            self, _context: Registry.SupportedcategoriesCallContext, **kwargs: Any
        ) -> Awaitable[Any]: ...
        def categoryInfo(
            self,
            categoryId: str,
            _context: Registry.CategoryinfoCallContext,
            **kwargs: Any,
        ) -> Awaitable[Registry.Server.CategoryinfoResult]: ...
        def entries(
            self, categoryId: str, _context: Registry.EntriesCallContext, **kwargs: Any
        ) -> Awaitable[Sequence[Registry.Entry]]: ...

class Registrar(Identifiable, Protocol):
    class CrossDomainRestore:
        @property
        def vatId(self) -> VatId: ...
        @property
        def restorer(self) -> Restorer: ...
        def init(self, name: Literal["vatId"]) -> VatId: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Registrar.CrossDomainRestoreReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registrar.CrossDomainRestoreReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            vatId: VatIdBuilder | dict[str, Any] | None = None,
            restorer: Restorer | Restorer.Server | None = None,
        ) -> Registrar.CrossDomainRestoreBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registrar.CrossDomainRestoreReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registrar.CrossDomainRestoreReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class CrossDomainRestoreReader(Registrar.CrossDomainRestore):
        @property
        def vatId(self) -> VatIdReader: ...
        def as_builder(self) -> Registrar.CrossDomainRestoreBuilder: ...

    class CrossDomainRestoreBuilder(Registrar.CrossDomainRestore):
        @property
        def vatId(self) -> VatIdBuilder: ...
        @vatId.setter
        def vatId(
            self, value: VatId | VatIdBuilder | VatIdReader | dict[str, Any]
        ) -> None: ...
        @property
        def restorer(self) -> Restorer: ...
        @restorer.setter
        def restorer(self, value: Restorer | Restorer.Server) -> None: ...
        @staticmethod
        def from_dict(
            dictionary: dict[str, Any],
        ) -> Registrar.CrossDomainRestoreBuilder: ...
        def init(self, name: Literal["vatId"]) -> VatIdBuilder: ...
        def copy(self) -> Registrar.CrossDomainRestoreBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Registrar.CrossDomainRestoreReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class RegParams:
        @property
        def cap(self) -> Identifiable: ...
        @property
        def regName(self) -> str: ...
        @property
        def categoryId(self) -> str: ...
        @property
        def xDomain(self) -> Registrar.CrossDomainRestore: ...
        def init(self, name: Literal["xDomain"]) -> Registrar.CrossDomainRestore: ...
        @staticmethod
        @contextmanager
        def from_bytes(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Iterator[Registrar.RegParamsReader]: ...
        @staticmethod
        def from_bytes_packed(
            data: bytes,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registrar.RegParamsReader: ...
        @staticmethod
        def new_message(
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Any = None,
            cap: Identifiable | Identifiable.Server | None = None,
            regName: str | None = None,
            categoryId: str | None = None,
            xDomain: Registrar.CrossDomainRestoreBuilder | dict[str, Any] | None = None,
        ) -> Registrar.RegParamsBuilder: ...
        @staticmethod
        def read(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registrar.RegParamsReader: ...
        @staticmethod
        def read_packed(
            file: BinaryIO,
            traversal_limit_in_words: int | None = ...,
            nesting_limit: int | None = ...,
        ) -> Registrar.RegParamsReader: ...
        def to_dict(self) -> dict[str, Any]: ...

    class RegParamsReader(Registrar.RegParams):
        @property
        def xDomain(self) -> Registrar.CrossDomainRestoreReader: ...
        def as_builder(self) -> Registrar.RegParamsBuilder: ...

    class RegParamsBuilder(Registrar.RegParams):
        @property
        def cap(self) -> Identifiable: ...
        @cap.setter
        def cap(self, value: Identifiable | Identifiable.Server) -> None: ...
        @property
        def regName(self) -> str: ...
        @regName.setter
        def regName(self, value: str) -> None: ...
        @property
        def categoryId(self) -> str: ...
        @categoryId.setter
        def categoryId(self, value: str) -> None: ...
        @property
        def xDomain(self) -> Registrar.CrossDomainRestoreBuilder: ...
        @xDomain.setter
        def xDomain(
            self,
            value: Registrar.CrossDomainRestore
            | Registrar.CrossDomainRestoreBuilder
            | Registrar.CrossDomainRestoreReader
            | dict[str, Any],
        ) -> None: ...
        @staticmethod
        def from_dict(dictionary: dict[str, Any]) -> Registrar.RegParamsBuilder: ...
        def init(
            self, name: Literal["xDomain"]
        ) -> Registrar.CrossDomainRestoreBuilder: ...
        def copy(self) -> Registrar.RegParamsBuilder: ...
        def to_bytes(self) -> bytes: ...
        def to_bytes_packed(self) -> bytes: ...
        def to_segments(self) -> list[bytes]: ...
        def as_reader(self) -> Registrar.RegParamsReader: ...
        @staticmethod
        def write(file: BufferedWriter) -> None: ...
        @staticmethod
        def write_packed(file: BufferedWriter) -> None: ...

    class Unregister(Protocol):
        class UnregisterResult(Awaitable[UnregisterResult], Protocol):
            success: bool

        class UnregisterResultsBuilder(Protocol):
            success: bool

        class UnregisterCallContext(Protocol):
            results: Registrar.Unregister.UnregisterResultsBuilder

        def unregister(self) -> UnregisterResult: ...
        class UnregisterRequest(Protocol):
            def send(self) -> Registrar.Unregister.UnregisterResult: ...

        def unregister_request(self) -> UnregisterRequest: ...
        @classmethod
        def _new_client(
            cls, server: Registrar.Unregister.Server
        ) -> Registrar.Unregister: ...
        class Server:
            def unregister(
                self,
                _context: Registrar.Unregister.UnregisterCallContext,
                **kwargs: Any,
            ) -> Awaitable[bool]: ...

    class RegisterResult(Awaitable[RegisterResult], Protocol):
        unreg: Registrar.Unregister
        reregSR: Any

    class RegisterResultsBuilder(Protocol):
        unreg: Registrar.Unregister
        reregSR: Any

    class RegisterCallContext(Protocol):
        results: Registrar.RegisterResultsBuilder

    def register(
        self,
        cap: Identifiable,
        regName: str,
        categoryId: str,
        xDomain: Registrar.CrossDomainRestore | dict[str, Any],
    ) -> RegisterResult: ...
    class RegisterRequest(Protocol):
        cap: Identifiable
        regName: str
        categoryId: str
        xDomain: Registrar.CrossDomainRestoreBuilder
        def send(self) -> Registrar.RegisterResult: ...

    def register_request(self) -> RegisterRequest: ...
    @classmethod
    def _new_client(
        cls, server: Registrar.Server | Identifiable.Server
    ) -> Registrar: ...
    class Server(Identifiable.Server):
        def register(
            self,
            cap: Identifiable,
            regName: str,
            categoryId: str,
            xDomain: Registrar.CrossDomainRestoreReader,
            _context: Registrar.RegisterCallContext,
            **kwargs: Any,
        ) -> Awaitable[Any]: ...
