"""This is an automatically generated stub for `crop.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(os.path.join(here, "../zalfmas_capnp_schemas/crop.capnp"))
import_path = [
    here,
    os.path.join(here, "../zalfmas_capnp_schemas"),
    os.path.join(here, "../zalfmas_capnp_schemas"),
]
Crop = capnp.load(module_file, imports=import_path).Crop
CropBuilder = Crop
CropReader = Crop
Service = capnp.load(module_file, imports=import_path).Service
ServiceBuilder = Service
ServiceReader = Service
