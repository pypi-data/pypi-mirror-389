r"""
Aidge Export for CPP standalone projects

"""
from pathlib import Path

# Constants
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]

from .export_registry import ExportLibCpp
from .export_utils import *
from .operators import *
from .export import *

import aidge_export_cpp.benchmark.registrations.extensions_inference
