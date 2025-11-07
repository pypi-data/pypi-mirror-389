"""This is an automatically generated stub for `fbp.capnp`."""

import os
from typing import NamedTuple

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(here, "../../zalfmas_capnp_schemas/fbp.capnp")
)
import_path = [
    here,
    os.path.join(here, "../../zalfmas_capnp_schemas"),
    os.path.join(here, "../../zalfmas_capnp_schemas"),
]
IP = capnp.load(module_file, imports=import_path).IP
IPBuilder = IP
IPReader = IP
IIP = capnp.load(module_file, imports=import_path).IIP
IIPBuilder = IIP
IIPReader = IIP
Channel = capnp.load(module_file, imports=import_path).Channel
ChannelBuilder = Channel
ChannelReader = Channel
StartChannelsService = capnp.load(module_file, imports=import_path).StartChannelsService
StartChannelsServiceBuilder = StartChannelsService
StartChannelsServiceReader = StartChannelsService
PortInfos = capnp.load(module_file, imports=import_path).PortInfos
PortInfosBuilder = PortInfos
PortInfosReader = PortInfos
Component = capnp.load(module_file, imports=import_path).Component
ComponentBuilder = Component
ComponentReader = Component

Channel.Reader.Server.ReadResult = NamedTuple(
    "ReadResult", [("value", object), ("done", object), ("noMsg", object)]
)
Channel.Reader.Server.ReadifmsgResult = NamedTuple(
    "ReadifmsgResult", [("value", object), ("done", object), ("noMsg", object)]
)
