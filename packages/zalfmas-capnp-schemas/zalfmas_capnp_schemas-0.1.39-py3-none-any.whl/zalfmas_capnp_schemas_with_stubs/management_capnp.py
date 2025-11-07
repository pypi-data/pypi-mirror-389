"""This is an automatically generated stub for `management.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/management.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
Event = capnp.load(module_file, imports=import_path).Event
EventBuilder = Event
EventReader = Event
Params = capnp.load(module_file, imports=import_path).Params
ParamsBuilder = Params
ParamsReader = Params
Fertilizer = capnp.load(module_file, imports=import_path).Fertilizer
FertilizerBuilder = Fertilizer
FertilizerReader = Fertilizer
Nutrient = capnp.load(module_file, imports=import_path).Nutrient
NutrientBuilder = Nutrient
NutrientReader = Nutrient
FertilizerService = capnp.load(module_file, imports=import_path).FertilizerService
FertilizerServiceBuilder = FertilizerService
FertilizerServiceReader = FertilizerService
Service = capnp.load(module_file, imports=import_path).Service
ServiceBuilder = Service
ServiceReader = Service
