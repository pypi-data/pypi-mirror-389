"""This is an automatically generated stub for `monica_params.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(
        here, "../../../../zalfmas_capnp_schemas/model/monica/monica_params.capnp"
    )
)
import_path = [
    here,
    os.path.join(here, "../../../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../../../zalfmas_capnp_schemas/model/monica"),
]
CropSpec = capnp.load(module_file, imports=import_path).CropSpec
CropSpecBuilder = CropSpec
CropSpecReader = CropSpec
CropParameters = capnp.load(module_file, imports=import_path).CropParameters
CropParametersBuilder = CropParameters
CropParametersReader = CropParameters
SpeciesParameters = capnp.load(module_file, imports=import_path).SpeciesParameters
SpeciesParametersBuilder = SpeciesParameters
SpeciesParametersReader = SpeciesParameters
CultivarParameters = capnp.load(module_file, imports=import_path).CultivarParameters
CultivarParametersBuilder = CultivarParameters
CultivarParametersReader = CultivarParameters
YieldComponent = capnp.load(module_file, imports=import_path).YieldComponent
YieldComponentBuilder = YieldComponent
YieldComponentReader = YieldComponent
CropResidueParameters = capnp.load(
    module_file, imports=import_path
).CropResidueParameters
CropResidueParametersBuilder = CropResidueParameters
CropResidueParametersReader = CropResidueParameters
AutomaticHarvestParameters = capnp.load(
    module_file, imports=import_path
).AutomaticHarvestParameters
AutomaticHarvestParametersBuilder = AutomaticHarvestParameters
AutomaticHarvestParametersReader = AutomaticHarvestParameters
NMinCropParameters = capnp.load(module_file, imports=import_path).NMinCropParameters
NMinCropParametersBuilder = NMinCropParameters
NMinCropParametersReader = NMinCropParameters
NMinApplicationParameters = capnp.load(
    module_file, imports=import_path
).NMinApplicationParameters
NMinApplicationParametersBuilder = NMinApplicationParameters
NMinApplicationParametersReader = NMinApplicationParameters
SoilParameters = capnp.load(module_file, imports=import_path).SoilParameters
SoilParametersBuilder = SoilParameters
SoilParametersReader = SoilParameters
AutomaticIrrigationParameters = capnp.load(
    module_file, imports=import_path
).AutomaticIrrigationParameters
AutomaticIrrigationParametersBuilder = AutomaticIrrigationParameters
AutomaticIrrigationParametersReader = AutomaticIrrigationParameters
SiteParameters = capnp.load(module_file, imports=import_path).SiteParameters
SiteParametersBuilder = SiteParameters
SiteParametersReader = SiteParameters
EnvironmentParameters = capnp.load(
    module_file, imports=import_path
).EnvironmentParameters
EnvironmentParametersBuilder = EnvironmentParameters
EnvironmentParametersReader = EnvironmentParameters
MeasuredGroundwaterTableInformation = capnp.load(
    module_file, imports=import_path
).MeasuredGroundwaterTableInformation
MeasuredGroundwaterTableInformationBuilder = MeasuredGroundwaterTableInformation
MeasuredGroundwaterTableInformationReader = MeasuredGroundwaterTableInformation
SimulationParameters = capnp.load(module_file, imports=import_path).SimulationParameters
SimulationParametersBuilder = SimulationParameters
SimulationParametersReader = SimulationParameters
CropModuleParameters = capnp.load(module_file, imports=import_path).CropModuleParameters
CropModuleParametersBuilder = CropModuleParameters
CropModuleParametersReader = CropModuleParameters
SoilMoistureModuleParameters = capnp.load(
    module_file, imports=import_path
).SoilMoistureModuleParameters
SoilMoistureModuleParametersBuilder = SoilMoistureModuleParameters
SoilMoistureModuleParametersReader = SoilMoistureModuleParameters
SoilOrganicModuleParameters = capnp.load(
    module_file, imports=import_path
).SoilOrganicModuleParameters
SoilOrganicModuleParametersBuilder = SoilOrganicModuleParameters
SoilOrganicModuleParametersReader = SoilOrganicModuleParameters
SticsParameters = capnp.load(module_file, imports=import_path).SticsParameters
SticsParametersBuilder = SticsParameters
SticsParametersReader = SticsParameters
SoilTemperatureModuleParameters = capnp.load(
    module_file, imports=import_path
).SoilTemperatureModuleParameters
SoilTemperatureModuleParametersBuilder = SoilTemperatureModuleParameters
SoilTemperatureModuleParametersReader = SoilTemperatureModuleParameters
SoilTransportModuleParameters = capnp.load(
    module_file, imports=import_path
).SoilTransportModuleParameters
SoilTransportModuleParametersBuilder = SoilTransportModuleParameters
SoilTransportModuleParametersReader = SoilTransportModuleParameters
Voc = capnp.load(module_file, imports=import_path).Voc
VocBuilder = Voc
VocReader = Voc
