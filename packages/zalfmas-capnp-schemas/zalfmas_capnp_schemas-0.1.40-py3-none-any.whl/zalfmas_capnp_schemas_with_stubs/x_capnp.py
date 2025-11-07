"""This is an automatically generated stub for `x.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(os.path.join(here, "../zalfmas_capnp_schemas/x.capnp"))
import_path = [here, os.path.join(here, "../zalfmas_capnp_schemas")]
S = capnp.load(module_file, imports=import_path).S
SBuilder = S
SReader = S
X = capnp.load(module_file, imports=import_path).X
XBuilder = X
XReader = X
Y = capnp.load(module_file, imports=import_path).Y
YBuilder = Y
YReader = Y
Z = capnp.load(module_file, imports=import_path).Z
ZBuilder = Z
ZReader = Z
