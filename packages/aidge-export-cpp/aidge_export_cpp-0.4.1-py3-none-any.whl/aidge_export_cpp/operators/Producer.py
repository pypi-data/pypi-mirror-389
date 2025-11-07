import os
from pathlib import Path
import numpy as np
import aidge_core
from aidge_core.export_utils import ExportNodeCpp, generate_file, aidge2c
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

def export_params(name: str,
                  output: aidge_core.Tensor,
                  filepath: str):

    # Get directory name of the file
    dirname = os.path.dirname(filepath)

    # If directory doesn't exist, create it
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    generate_file(
        filepath,
        str(ROOT / "templates" / "data" / "parameters.jinja"),
        name=name,
        dims=output.dims,
        dtype=aidge2c(output.dtype),
        values=np.array(output).tolist()
    )

@ExportLibCpp.register("Producer", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)))
class ProducerCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.output = self.operator.get_output(0)
        self.ignore = node.attributes().has_attr("ignore")

    def export(self, export_folder: Path):
        if self.ignore:
            return []

        path_to_definition = f"{self.config_path}/{self.attributes['name']}.{self.config_extension}"

        try:
            aidge_core.export_utils.code_generation.generate_file(
                str(export_folder / path_to_definition),
                str(ROOT / "templates" / "configuration" / "producer_config.jinja"),
                **self.attributes
            )
        except Exception as e:
            raise RuntimeError(f"Error when creating config file for {self.node.name()}[{self.node.type()}].") from e

        header_path = f"include/parameters/{self.attributes['name']}.h"
        export_params(
            self.attributes['out_name'][0],
            self.output,
            str(export_folder / header_path))
        return [path_to_definition, header_path]

    def forward(self):
        # A Producer does nothing during forward
        return []
