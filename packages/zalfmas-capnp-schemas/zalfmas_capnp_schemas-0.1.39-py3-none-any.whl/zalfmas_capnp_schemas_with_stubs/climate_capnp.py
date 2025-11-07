"""This is an automatically generated stub for `climate.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/climate.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
EnsembleMember = capnp.load(module_file, imports=import_path).EnsembleMember
EnsembleMemberBuilder = EnsembleMember
EnsembleMemberReader = EnsembleMember
Metadata = capnp.load(module_file, imports=import_path).Metadata
MetadataBuilder = Metadata
MetadataReader = Metadata
Dataset = capnp.load(module_file, imports=import_path).Dataset
DatasetBuilder = Dataset
DatasetReader = Dataset
Location = capnp.load(module_file, imports=import_path).Location
LocationBuilder = Location
LocationReader = Location
TimeSeries = capnp.load(module_file, imports=import_path).TimeSeries
TimeSeriesBuilder = TimeSeries
TimeSeriesReader = TimeSeries
MetaPlusData = capnp.load(module_file, imports=import_path).MetaPlusData
MetaPlusDataBuilder = MetaPlusData
MetaPlusDataReader = MetaPlusData
TimeSeriesData = capnp.load(module_file, imports=import_path).TimeSeriesData
TimeSeriesDataBuilder = TimeSeriesData
TimeSeriesDataReader = TimeSeriesData
Service = capnp.load(module_file, imports=import_path).Service
ServiceBuilder = Service
ServiceReader = Service
CSVTimeSeriesFactory = capnp.load(module_file, imports=import_path).CSVTimeSeriesFactory
CSVTimeSeriesFactoryBuilder = CSVTimeSeriesFactory
CSVTimeSeriesFactoryReader = CSVTimeSeriesFactory
AlterTimeSeriesWrapper = capnp.load(
    module_file, imports=import_path
).AlterTimeSeriesWrapper
AlterTimeSeriesWrapperBuilder = AlterTimeSeriesWrapper
AlterTimeSeriesWrapperReader = AlterTimeSeriesWrapper
AlterTimeSeriesWrapperFactory = capnp.load(
    module_file, imports=import_path
).AlterTimeSeriesWrapperFactory
AlterTimeSeriesWrapperFactoryBuilder = AlterTimeSeriesWrapperFactory
AlterTimeSeriesWrapperFactoryReader = AlterTimeSeriesWrapperFactory

Dataset.Server.MetadataResult = NamedTuple(
    "MetadataResult", [("entries", object), ("info", object)]
)
Dataset.GetLocationsCallback.Server.LocationResult = NamedTuple(
    "LocationResult",
    [
        ("id", object),
        ("heightNN", object),
        ("latlon", object),
        ("timeSeries", object),
        ("customData", object),
    ],
)
Dataset.GetLocationsCallback.Server.MetadataResult = NamedTuple(
    "MetadataResult", [("entries", object), ("info", object)]
)
Metadata.Information.Server.ForoneResult = NamedTuple(
    "ForoneResult", [("id", object), ("name", object), ("description", object)]
)
TimeSeries.Server.LocationResult = NamedTuple(
    "LocationResult",
    [
        ("id", object),
        ("heightNN", object),
        ("latlon", object),
        ("timeSeries", object),
        ("customData", object),
    ],
)
TimeSeries.Server.MetadataResult = NamedTuple(
    "MetadataResult", [("entries", object), ("info", object)]
)
