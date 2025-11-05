from pathlib import Path
from .cell_annotation_schema import *

THIS_PATH = Path(__file__).parent

SCHEMA_DIRECTORY = THIS_PATH.parent / "schema"
MAIN_SCHEMA_PATH = SCHEMA_DIRECTORY / "cell_annotation_schema_default.yaml"
