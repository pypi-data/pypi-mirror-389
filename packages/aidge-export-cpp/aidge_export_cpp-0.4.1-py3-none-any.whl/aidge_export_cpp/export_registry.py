from aidge_core.export_utils import ExportLib
from aidge_export_cpp import ROOT

class ExportLibCpp(ExportLib):
    _name="export_cpp"
    static_files={
        str(ROOT / "static" / "Makefile"): "",
        str(ROOT / "static" / "typedefs.hpp"): "dnn/include/utils/cpp",
        str(ROOT / "static" / "utils.hpp"): "dnn/include/utils/cpp",
        str(ROOT / "static" / "rescaling_utils.hpp"): "dnn/include/utils/cpp",
        str(ROOT / "static" / "activation_utils.hpp"): "dnn/include/utils/cpp",
    }
