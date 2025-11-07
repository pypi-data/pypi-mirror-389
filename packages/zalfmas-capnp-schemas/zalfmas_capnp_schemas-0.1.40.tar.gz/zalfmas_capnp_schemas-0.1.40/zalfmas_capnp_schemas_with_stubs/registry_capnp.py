"""This is an automatically generated stub for `registry.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../zalfmas_capnp_schemas/registry.capnp")
)
import_path = [
    here,
    os.path.join(here, "../zalfmas_capnp_schemas"),
    os.path.join(here, "../zalfmas_capnp_schemas"),
]
Admin = capnp.load(module_file, imports=import_path).Admin
AdminBuilder = Admin
AdminReader = Admin
Registry = capnp.load(module_file, imports=import_path).Registry
RegistryBuilder = Registry
RegistryReader = Registry
Registrar = capnp.load(module_file, imports=import_path).Registrar
RegistrarBuilder = Registrar
RegistrarReader = Registrar

Registry.Server.CategoryinfoResult = NamedTuple(
    "CategoryinfoResult", [("id", object), ("name", object), ("description", object)]
)
