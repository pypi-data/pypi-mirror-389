"""This is an automatically generated stub for `web-berest-data-import.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator
from typing import Any, Protocol

class DWLABImport(Protocol):
    class ImportdataResult(Awaitable[ImportdataResult], Protocol):
        id: str
        successA: bool
        successB: bool

    class ImportdataResultsBuilder(Protocol):
        id: str
        successA: bool
        successB: bool

    class ImportdataCallContext(Protocol):
        results: DWLABImport.ImportdataResultsBuilder

    def importData(self, id: str, dwla: bytes, dwlb: bytes) -> ImportdataResult: ...
    class ImportdataRequest(Protocol):
        id: str
        dwla: bytes
        dwlb: bytes
        def send(self) -> DWLABImport.ImportdataResult: ...

    def importData_request(self) -> ImportdataRequest: ...
    @classmethod
    def _new_client(cls, server: DWLABImport.Server) -> DWLABImport: ...
    class Server:
        def importData(
            self,
            id: str,
            dwla: bytes,
            dwlb: bytes,
            _context: DWLABImport.ImportdataCallContext,
            **kwargs: Any,
        ) -> Awaitable[tuple[str, bool, bool]]: ...
