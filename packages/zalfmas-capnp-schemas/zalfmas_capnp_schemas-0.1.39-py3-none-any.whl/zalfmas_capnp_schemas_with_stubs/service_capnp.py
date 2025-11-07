"""This is an automatically generated stub for `service.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/service.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
Admin = capnp.load(module_file, imports=import_path).Admin
AdminBuilder = Admin
AdminReader = Admin
SimpleFactory = capnp.load(module_file, imports=import_path).SimpleFactory
SimpleFactoryBuilder = SimpleFactory
SimpleFactoryReader = SimpleFactory
Factory = capnp.load(module_file, imports=import_path).Factory
FactoryBuilder = Factory
FactoryReader = Factory
Stoppable = capnp.load(module_file, imports=import_path).Stoppable
StoppableBuilder = Stoppable
StoppableReader = Stoppable

Factory.Server.CreateResult = NamedTuple(
    "CreateResult", [("adminCap", object), ("serviceCaps", object), ("error", object)]
)
