"""This is an automatically generated stub for `soil_params.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(
        here, "../../../../zalfmas_capnp_schemas/model/monica/soil_params.capnp"
    )
)
import_path = [here, os.path.join(here, "../../../../zalfmas_capnp_schemas")]
SoilCharacteristicData = capnp.load(
    module_file, imports=import_path
).SoilCharacteristicData
SoilCharacteristicDataBuilder = SoilCharacteristicData
SoilCharacteristicDataReader = SoilCharacteristicData
SoilCharacteristicModifier = capnp.load(
    module_file, imports=import_path
).SoilCharacteristicModifier
SoilCharacteristicModifierBuilder = SoilCharacteristicModifier
SoilCharacteristicModifierReader = SoilCharacteristicModifier
CapillaryRiseRate = capnp.load(module_file, imports=import_path).CapillaryRiseRate
CapillaryRiseRateBuilder = CapillaryRiseRate
CapillaryRiseRateReader = CapillaryRiseRate
