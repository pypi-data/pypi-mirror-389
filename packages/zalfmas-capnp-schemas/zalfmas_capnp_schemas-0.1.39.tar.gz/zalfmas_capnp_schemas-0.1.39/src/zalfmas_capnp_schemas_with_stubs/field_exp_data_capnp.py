"""This is an automatically generated stub for `field_exp_data.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/field_exp_data.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
WeatherStation = capnp.load(module_file, imports=import_path).WeatherStation
WeatherStationBuilder = WeatherStation
WeatherStationReader = WeatherStation
SoilMetadata = capnp.load(module_file, imports=import_path).SoilMetadata
SoilMetadataBuilder = SoilMetadata
SoilMetadataReader = SoilMetadata
Field = capnp.load(module_file, imports=import_path).Field
FieldBuilder = Field
FieldReader = Field
ExperimentDescription = capnp.load(
    module_file, imports=import_path
).ExperimentDescription
ExperimentDescriptionBuilder = ExperimentDescription
ExperimentDescriptionReader = ExperimentDescription
Treatment = capnp.load(module_file, imports=import_path).Treatment
TreatmentBuilder = Treatment
TreatmentReader = Treatment
Plot = capnp.load(module_file, imports=import_path).Plot
PlotBuilder = Plot
PlotReader = Plot
Cultivar = capnp.load(module_file, imports=import_path).Cultivar
CultivarBuilder = Cultivar
CultivarReader = Cultivar
Residue = capnp.load(module_file, imports=import_path).Residue
ResidueBuilder = Residue
ResidueReader = Residue
InitialConditionsLayer = capnp.load(
    module_file, imports=import_path
).InitialConditionsLayer
InitialConditionsLayerBuilder = InitialConditionsLayer
InitialConditionsLayerReader = InitialConditionsLayer
PlantingEvent = capnp.load(module_file, imports=import_path).PlantingEvent
PlantingEventBuilder = PlantingEvent
PlantingEventReader = PlantingEvent
HarvestEvent = capnp.load(module_file, imports=import_path).HarvestEvent
HarvestEventBuilder = HarvestEvent
HarvestEventReader = HarvestEvent
IrrigationEvent = capnp.load(module_file, imports=import_path).IrrigationEvent
IrrigationEventBuilder = IrrigationEvent
IrrigationEventReader = IrrigationEvent
FertilizerEvent = capnp.load(module_file, imports=import_path).FertilizerEvent
FertilizerEventBuilder = FertilizerEvent
FertilizerEventReader = FertilizerEvent
EnvironmentModification = capnp.load(
    module_file, imports=import_path
).EnvironmentModification
EnvironmentModificationBuilder = EnvironmentModification
EnvironmentModificationReader = EnvironmentModification
