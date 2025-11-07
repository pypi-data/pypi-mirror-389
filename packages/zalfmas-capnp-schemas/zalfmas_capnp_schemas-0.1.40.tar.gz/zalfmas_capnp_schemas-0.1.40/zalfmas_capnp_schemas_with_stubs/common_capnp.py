"""This is an automatically generated stub for `common.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../zalfmas_capnp_schemas/common.capnp")
)
import_path = [here, os.path.join(here, "../zalfmas_capnp_schemas")]
IdInformation = capnp.load(module_file, imports=import_path).IdInformation
IdInformationBuilder = IdInformation
IdInformationReader = IdInformation
Identifiable = capnp.load(module_file, imports=import_path).Identifiable
IdentifiableBuilder = Identifiable
IdentifiableReader = Identifiable
StructuredText = capnp.load(module_file, imports=import_path).StructuredText
StructuredTextBuilder = StructuredText
StructuredTextReader = StructuredText
Value = capnp.load(module_file, imports=import_path).Value
ValueBuilder = Value
ValueReader = Value
Pair = capnp.load(module_file, imports=import_path).Pair
PairBuilder = Pair
PairReader = Pair
Holder = capnp.load(module_file, imports=import_path).Holder
HolderBuilder = Holder
HolderReader = Holder
IdentifiableHolder = capnp.load(module_file, imports=import_path).IdentifiableHolder
IdentifiableHolderBuilder = IdentifiableHolder
IdentifiableHolderReader = IdentifiableHolder

Identifiable.Server.InfoResult = NamedTuple(
    "InfoResult", [("id", object), ("name", object), ("description", object)]
)
