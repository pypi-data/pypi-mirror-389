"""This is an automatically generated stub for `grid.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/grid.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
Grid = capnp.load(module_file, imports=import_path).Grid
GridBuilder = Grid
GridReader = Grid
