"""This is an automatically generated stub for `jobs.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(os.path.join(here, "../zalfmas_capnp_schemas/jobs.capnp"))
import_path = [
    here,
    os.path.join(here, "../zalfmas_capnp_schemas"),
    os.path.join(here, "../zalfmas_capnp_schemas"),
]
Job = capnp.load(module_file, imports=import_path).Job
JobBuilder = Job
JobReader = Job
Service = capnp.load(module_file, imports=import_path).Service
ServiceBuilder = Service
ServiceReader = Service
