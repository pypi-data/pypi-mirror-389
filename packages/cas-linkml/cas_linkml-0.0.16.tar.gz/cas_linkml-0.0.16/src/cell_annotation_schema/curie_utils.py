import os
import json
from pathlib import Path

from importlib import resources
from cell_annotation_schema import resource


class CurieToIriConverter:

    DEFAULT_JSONLD_FILE_NAME = 'prefixes.jsonld'

    def __init__(self, jsonld_file=DEFAULT_JSONLD_FILE_NAME):
        self.jsonld_file = jsonld_file
        self.prefix_mappings = self.load_prefix_mappings(self.jsonld_file)

    @staticmethod
    def load_prefix_mappings(jsonld_file_name):
        prefix_resource_file = resources.files(resource) / jsonld_file_name
        if os.path.exists(jsonld_file_name):
            # read from the path provided by the user
            with open(jsonld_file_name, 'r') as file:
                prefixes = json.load(file)
        elif os.path.exists(prefix_resource_file):
            # read from importlib.resources (resource) package
            prefixes = json.loads(Path(prefix_resource_file).read_text())
        else:
            # read from resource folder
            resource_dir = os.path.join(os.path.dirname(__file__), "./resource")
            prefixes_path = os.path.join(resource_dir, jsonld_file_name)
            prefixes = json.loads(Path(prefixes_path).read_text())
        return prefixes.get('@context', {})

    def curie_to_iri(self, curie):
        prefix, reference = curie.split(':', 1)
        if prefix in self.prefix_mappings:
            return self.prefix_mappings[prefix] + reference
        else:
            raise ValueError(f"Prefix '{prefix}' not found in prefix mappings.")
