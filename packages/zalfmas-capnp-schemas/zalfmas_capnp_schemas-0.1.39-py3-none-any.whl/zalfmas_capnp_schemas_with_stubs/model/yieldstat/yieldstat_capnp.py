"""This is an automatically generated stub for `yieldstat.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(
    os.path.join(
        here, "../../../../zalfmas_capnp_schemas/model/yieldstat/yieldstat.capnp"
    )
)
import_path = [here, os.path.join(here, "../../../../zalfmas_capnp_schemas")]
RestInput = capnp.load(module_file, imports=import_path).RestInput
RestInputBuilder = RestInput
RestInputReader = RestInput
Result = capnp.load(module_file, imports=import_path).Result
ResultBuilder = Result
ResultReader = Result
Output = capnp.load(module_file, imports=import_path).Output
OutputBuilder = Output
OutputReader = Output
