"""This is an automatically generated stub for `monica_state.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../../zalfmas_capnp_schemas/model/monica/monica_state.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../../zalfmas_capnp_schemas/model/monica"),
]
MaybeBool = capnp.load(module_file, imports=import_path).MaybeBool
MaybeBoolBuilder = MaybeBool
MaybeBoolReader = MaybeBool
RuntimeState = capnp.load(module_file, imports=import_path).RuntimeState
RuntimeStateBuilder = RuntimeState
RuntimeStateReader = RuntimeState
MonicaModelState = capnp.load(module_file, imports=import_path).MonicaModelState
MonicaModelStateBuilder = MonicaModelState
MonicaModelStateReader = MonicaModelState
SoilColumnState = capnp.load(module_file, imports=import_path).SoilColumnState
SoilColumnStateBuilder = SoilColumnState
SoilColumnStateReader = SoilColumnState
CropModuleState = capnp.load(module_file, imports=import_path).CropModuleState
CropModuleStateBuilder = CropModuleState
CropModuleStateReader = CropModuleState
SoilLayerState = capnp.load(module_file, imports=import_path).SoilLayerState
SoilLayerStateBuilder = SoilLayerState
SoilLayerStateReader = SoilLayerState
AOMProperties = capnp.load(module_file, imports=import_path).AOMProperties
AOMPropertiesBuilder = AOMProperties
AOMPropertiesReader = AOMProperties
SoilTemperatureModuleState = capnp.load(
    module_file, imports=import_path
).SoilTemperatureModuleState
SoilTemperatureModuleStateBuilder = SoilTemperatureModuleState
SoilTemperatureModuleStateReader = SoilTemperatureModuleState
SoilMoistureModuleState = capnp.load(
    module_file, imports=import_path
).SoilMoistureModuleState
SoilMoistureModuleStateBuilder = SoilMoistureModuleState
SoilMoistureModuleStateReader = SoilMoistureModuleState
FrostModuleState = capnp.load(module_file, imports=import_path).FrostModuleState
FrostModuleStateBuilder = FrostModuleState
FrostModuleStateReader = FrostModuleState
SnowModuleState = capnp.load(module_file, imports=import_path).SnowModuleState
SnowModuleStateBuilder = SnowModuleState
SnowModuleStateReader = SnowModuleState
SoilOrganicModuleState = capnp.load(
    module_file, imports=import_path
).SoilOrganicModuleState
SoilOrganicModuleStateBuilder = SoilOrganicModuleState
SoilOrganicModuleStateReader = SoilOrganicModuleState
SoilTransportModuleState = capnp.load(
    module_file, imports=import_path
).SoilTransportModuleState
SoilTransportModuleStateBuilder = SoilTransportModuleState
SoilTransportModuleStateReader = SoilTransportModuleState
CropState = capnp.load(module_file, imports=import_path).CropState
CropStateBuilder = CropState
CropStateReader = CropState
ICData = capnp.load(module_file, imports=import_path).ICData
ICDataBuilder = ICData
ICDataReader = ICData
