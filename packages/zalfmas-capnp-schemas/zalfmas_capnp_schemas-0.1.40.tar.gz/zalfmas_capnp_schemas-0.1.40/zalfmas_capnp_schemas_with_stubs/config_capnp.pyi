"""This is an automatically generated stub for `config.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator
from typing import Any, Protocol

class Service(Protocol):
    class NextconfigResult(Awaitable[NextconfigResult], Protocol):
        config: Any
        noFurtherConfigs: bool

    class NextconfigResultsBuilder(Protocol):
        config: Any
        noFurtherConfigs: bool

    class NextconfigCallContext(Protocol):
        results: Service.NextconfigResultsBuilder

    def nextConfig(self) -> NextconfigResult: ...
    class NextconfigRequest(Protocol):
        def send(self) -> Service.NextconfigResult: ...

    def nextConfig_request(self) -> NextconfigRequest: ...
    @classmethod
    def _new_client(cls, server: Service.Server) -> Service: ...
    class Server:
        def nextConfig(
            self, _context: Service.NextconfigCallContext, **kwargs: Any
        ) -> Awaitable[tuple[Any, bool]]: ...
