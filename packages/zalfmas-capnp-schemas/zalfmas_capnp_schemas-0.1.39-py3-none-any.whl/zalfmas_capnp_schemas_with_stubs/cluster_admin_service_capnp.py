"""This is an automatically generated stub for `cluster_admin_service.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/cluster_admin_service.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
Cluster = capnp.load(module_file, imports=import_path).Cluster
ClusterBuilder = Cluster
ClusterReader = Cluster
