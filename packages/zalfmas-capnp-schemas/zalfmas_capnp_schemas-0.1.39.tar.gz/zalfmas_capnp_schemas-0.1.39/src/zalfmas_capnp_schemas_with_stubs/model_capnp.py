"""This is an automatically generated stub for `model.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/model.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
XYResult = capnp.load(module_file, imports=import_path).XYResult
XYResultBuilder = XYResult
XYResultReader = XYResult
Stat = capnp.load(module_file, imports=import_path).Stat
StatBuilder = Stat
StatReader = Stat
XYPlusResult = capnp.load(module_file, imports=import_path).XYPlusResult
XYPlusResultBuilder = XYPlusResult
XYPlusResultReader = XYPlusResult
ClimateInstance = capnp.load(module_file, imports=import_path).ClimateInstance
ClimateInstanceBuilder = ClimateInstance
ClimateInstanceReader = ClimateInstance
Env = capnp.load(module_file, imports=import_path).Env
EnvBuilder = Env
EnvReader = Env
EnvInstance = capnp.load(module_file, imports=import_path).EnvInstance
EnvInstanceBuilder = EnvInstance
EnvInstanceReader = EnvInstance
EnvInstanceProxy = capnp.load(module_file, imports=import_path).EnvInstanceProxy
EnvInstanceProxyBuilder = EnvInstanceProxy
EnvInstanceProxyReader = EnvInstanceProxy
InstanceFactory = capnp.load(module_file, imports=import_path).InstanceFactory
InstanceFactoryBuilder = InstanceFactory
InstanceFactoryReader = InstanceFactory

InstanceFactory.Server.ModelinfoResult = NamedTuple(
    "ModelinfoResult", [("id", object), ("name", object), ("description", object)]
)
