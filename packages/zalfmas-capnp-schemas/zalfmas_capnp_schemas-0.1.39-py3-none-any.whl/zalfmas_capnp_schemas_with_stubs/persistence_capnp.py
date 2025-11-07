"""This is an automatically generated stub for `persistence.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/persistence.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
VatId = capnp.load(module_file, imports=import_path).VatId
VatIdBuilder = VatId
VatIdReader = VatId
Address = capnp.load(module_file, imports=import_path).Address
AddressBuilder = Address
AddressReader = Address
VatPath = capnp.load(module_file, imports=import_path).VatPath
VatPathBuilder = VatPath
VatPathReader = VatPath
SturdyRef = capnp.load(module_file, imports=import_path).SturdyRef
SturdyRefBuilder = SturdyRef
SturdyRefReader = SturdyRef
Heartbeat = capnp.load(module_file, imports=import_path).Heartbeat
HeartbeatBuilder = Heartbeat
HeartbeatReader = Heartbeat
Persistent = capnp.load(module_file, imports=import_path).Persistent
PersistentBuilder = Persistent
PersistentReader = Persistent
Restorer = capnp.load(module_file, imports=import_path).Restorer
RestorerBuilder = Restorer
RestorerReader = Restorer
HostPortResolver = capnp.load(module_file, imports=import_path).HostPortResolver
HostPortResolverBuilder = HostPortResolver
HostPortResolverReader = HostPortResolver
Gateway = capnp.load(module_file, imports=import_path).Gateway
GatewayBuilder = Gateway
GatewayReader = Gateway

Gateway.Server.RegisterResult = NamedTuple(
    "RegisterResult",
    [("sturdyRef", object), ("heartbeat", object), ("secsHeartbeatInterval", object)],
)
Persistent.Server.SaveResult = NamedTuple(
    "SaveResult", [("sturdyRef", object), ("unsaveSR", object)]
)
