"""This is an automatically generated stub for `persistent.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../../zalfmas_capnp_schemas/capnp/persistent.capnp")
)
import_path = [here, os.path.join(here, "../../../zalfmas_capnp_schemas")]
Persistent = capnp.load(module_file, imports=import_path).Persistent
PersistentBuilder = Persistent
PersistentReader = Persistent

Persistent.Server.SaveResult = NamedTuple("SaveResult", [("sturdyRef", object)])
