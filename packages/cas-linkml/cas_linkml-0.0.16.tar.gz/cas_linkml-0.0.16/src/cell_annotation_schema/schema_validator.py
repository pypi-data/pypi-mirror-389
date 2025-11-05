import glob
import sys
import os
import warnings

from pathlib import Path
from typing import List
from ruamel.yaml import YAML

from cell_annotation_schema.file_utils import get_json_from_file
from cell_annotation_schema.ontology.schema import decorate_linkml_schema

from linkml.validator import validate


warnings.filterwarnings("always")


def validate_data(schema, test_path):
    """
    Validates all json files located in the test path with the given schema.
    Parameters:
        schema: json schema object
        test_path: path to the data files. If path is a folder, validates all json files inside. If path is a json file,
        validates it.
    Returns:
        'True' if all test files are valid, 'False' otherwise. Logs the validation errors if any.
    """
    # sv = get_validator(schema, schema_name)
    if os.path.isdir(test_path):
        test_files = glob.glob(pathname=test_path + "/*.json")
    else:
        if Path(test_path).suffix == ".json":
            test_files = [test_path]
        else:
            raise Exception("Test file extension not supported: {}".format(test_path))
    validation_status: List[bool] = []
    print("Found %s test files in %s" % (str(len(test_files)), test_path))
    for instance_file in test_files:
        i = get_json_from_file(instance_file)
        print("Testing: %s" % instance_file)
        report = validate(i, schema)
        if report.results:
            for result in report.results:
                print("Validation ERROR: " + result.message)
        validation_status.append(False if report.results else True)
    return False not in validation_status


def get_schema(file_path):
    """
    Reads the json schema from the given location
    """
    with open(file_path, "r") as fs:
        try:
            ryaml = YAML(typ="safe")
            return ryaml.load(fs)
        except Exception as e:
            raise Exception("Yaml read failed:" + file_path + " " + str(e))


def run_validator(path_to_schema_dir, schema_file, path_to_test_dir):
    """Tests all instances in a test_folder against a single schema.
    Assumes all schema files in single dir.
    Assumes all *.json files in the test_dir should validate against the schema.
       * path_to_schema_dir:  Absolute or relative path to schema dir
       * schema_file: schema file name
       * test_dir: path to test directory (absolute or local to schema dir)
    """
    # Getting script directory, schema directory and test directory
    script_folder = Path(os.path.dirname(os.path.realpath(__file__)))
    schema_dir = Path(os.path.dirname(path_to_schema_dir))
    test_path = os.path.join(script_folder, os.path.dirname(path_to_test_dir))
    if not os.path.exists(os.path.join(script_folder, schema_dir)):
        raise Exception("Please provide valid path_to_schema_dir")
    if not os.path.exists(test_path):
        raise Exception("Please provide valid path_to_test_dir")
    else:
        schema_file_path = os.path.join(script_folder, schema_dir, schema_file)
        schema = get_schema(schema_file_path)
        schema = decorate_linkml_schema(schema)

        result = validate_data(schema, test_path)
        if not result:
            raise Exception("Validation Failed")


if __name__ == "__main__":
    run_validator(
        path_to_schema_dir="../../build/", schema_file="general_schema.yaml", path_to_test_dir="../../examples/"
    )
    run_validator(
        path_to_schema_dir="../../build/", schema_file="BICAN_schema.yaml", path_to_test_dir="../../examples/BICAN_schema_specific_examples/"
    )
    run_validator(
        path_to_schema_dir="../../build/", schema_file="CAP_schema.yaml", path_to_test_dir="../../examples/CAP_schema_specific_files/"
        # Need to simplify names
    )
