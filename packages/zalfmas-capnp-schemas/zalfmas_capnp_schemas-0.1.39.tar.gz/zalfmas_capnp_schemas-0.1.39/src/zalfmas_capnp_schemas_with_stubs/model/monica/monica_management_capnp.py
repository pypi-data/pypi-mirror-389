"""This is an automatically generated stub for `monica_management.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(
        here, "../../../../zalfmas_capnp_schemas/model/monica/monica_management.capnp"
    )
)
import_path = [
    here,
    os.path.join(here, "../../../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../../../zalfmas_capnp_schemas"),
]
ILRDates = capnp.load(module_file, imports=import_path).ILRDates
ILRDatesBuilder = ILRDates
ILRDatesReader = ILRDates
Event = capnp.load(module_file, imports=import_path).Event
EventBuilder = Event
EventReader = Event
Params = capnp.load(module_file, imports=import_path).Params
ParamsBuilder = Params
ParamsReader = Params
Service = capnp.load(module_file, imports=import_path).Service
ServiceBuilder = Service
ServiceReader = Service
