"""This is an automatically generated stub for `crop.capnp`."""

from __future__ import annotations

from collections.abc import Awaitable, Iterator
from typing import Any, Protocol

from .common_capnp import Identifiable
from .persistence_capnp import Persistent
from .registry_capnp import Registry

class Crop(Identifiable, Persistent, Protocol):
    class ParametersResult(Awaitable[ParametersResult], Protocol):
        params: Any

    class ParametersResultsBuilder(Protocol):
        params: Any

    class ParametersCallContext(Protocol):
        results: Crop.ParametersResultsBuilder

    def parameters(self) -> ParametersResult: ...
    class ParametersRequest(Protocol):
        def send(self) -> Crop.ParametersResult: ...

    def parameters_request(self) -> ParametersRequest: ...
    class CultivarResult(Awaitable[CultivarResult], Protocol):
        info: Any

    class CultivarResultsBuilder(Protocol):
        info: Any

    class CultivarCallContext(Protocol):
        results: Crop.CultivarResultsBuilder

    def cultivar(self) -> CultivarResult: ...
    class CultivarRequest(Protocol):
        def send(self) -> Crop.CultivarResult: ...

    def cultivar_request(self) -> CultivarRequest: ...
    class SpeciesResult(Awaitable[SpeciesResult], Protocol):
        info: Any

    class SpeciesResultsBuilder(Protocol):
        info: Any

    class SpeciesCallContext(Protocol):
        results: Crop.SpeciesResultsBuilder

    def species(self) -> SpeciesResult: ...
    class SpeciesRequest(Protocol):
        def send(self) -> Crop.SpeciesResult: ...

    def species_request(self) -> SpeciesRequest: ...
    @classmethod
    def _new_client(
        cls, server: Crop.Server | Identifiable.Server | Persistent.Server
    ) -> Crop: ...
    class Server(Identifiable.Server, Persistent.Server):
        def parameters(
            self, _context: Crop.ParametersCallContext, **kwargs: Any
        ) -> Awaitable[Any]: ...
        def cultivar(
            self, _context: Crop.CultivarCallContext, **kwargs: Any
        ) -> Awaitable[Any]: ...
        def species(
            self, _context: Crop.SpeciesCallContext, **kwargs: Any
        ) -> Awaitable[Any]: ...

class Service(Registry, Protocol):
    @classmethod
    def _new_client(
        cls, server: Service.Server | Identifiable.Server | Registry.Server
    ) -> Service: ...
    class Server(Registry.Server): ...
