"""
Linkml data class generator (gen-python) is generating problematic code because of the subclass and id mechanism we use.

Details of the issue:
Taxonomy-annotations doesn't have a id field so it uses the first slot as id slot (which is labelset).
BicanTaxonomy-annotations (with range Bican Annotations) has a id field so it uses the cell_set_accession field as id slot and works fine.

When we use the gen-python command on the schema, BicanTaxonomy dataclass post_init normalisation code is generated correctly as follows:
```
_normalize_inlined_as_dict(slot_name="annotations", slot_type=BicanAnnotation, key_name="cell_set_accession", keyed=True)
```

But the Taxonomy dataclass post_init normalisation code is generated as follows (expectedly but not correctly):
```
_normalize_inlined_as_dict(slot_name="annotations", slot_type=Annotation, key_name="labelset", keyed=False)
```

And since the BicanTaxonomy post_init is calling the super.post_init, it is trying to normalise the Annotation dataclass
 with the labelset field as id field which is not correct.

Solution this code applies:

We read schema into memory and remove `annotations` slot from the Taxonomy class and add it to BicanTaxonomy
(as if it is not inherited but its own slot) so that the problematic normalisation code is not generated.
"""
import os
import json

from pathlib import Path
from typing import Union
from linkml import generators
from dacite import from_dict

from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.utils.compile_python import compile_python

from cell_annotation_schema.file_utils import read_schema
from cell_annotation_schema.ontology.schema import decorate_linkml_schema
from cell_annotation_schema.datamodel.cell_annotation_schema import Taxonomy
from cell_annotation_schema.datamodel.bican.cell_annotation_schema import BicanTaxonomy
from cell_annotation_schema.datamodel.cap.cell_annotation_schema import CapTaxonomy

SOURCE_DIR = Path(__file__).parent.parent


def generate_data_class(cas_schema: Union[str, dict], class_path: str):
    """
    Generate data class from CAS schema.

    Args:
        cas_schema: CAS schema path or dict representing it.
        class_path: Output class path.
    Returns:
        str: Data class string.
    """
    schema_def = read_schema(cas_schema)
    schema_dict = decorate_linkml_schema(schema_def)
    schema_def = yaml_loader.load(schema_dict, target_class=SchemaDefinition)
    gen = generators.PythonGenerator(schema_def)
    output = gen.serialize()
    with open(class_path, "w") as class_file:
        class_file.write(output)


def get_py_instance(instance_dict, schema_name, schema_def, root_class=None):
    """
    Returns a Python instance of the schema class from the given data instance.
    Args:
        instance_dict: The data instance dictionary.
        schema_name: The name of the schema to be used for RDF generation.
        schema_def: The schema definition object.
        root_class: The root class of the schema if this is not a core (base,cap or bican) schema.
    Returns:
        The Python instance of the schema class.
    """
    fix_author_annotation_fields(instance_dict)
    for annotation in instance_dict.get("annotations", []):
        # remove empty cell_ontology_term_id to prevent enum value failure
        if annotation.get("cell_ontology_term_id", None) == "":
            annotation.pop("cell_ontology_term_id", None)
            annotation.pop("cell_ontology_term", None)

    py_inst = None
    if isinstance(schema_name, str):
        if schema_name.lower() == "base":
            py_inst = from_dict(data_class=Taxonomy, data=instance_dict)
        elif schema_name.lower() == "bican":
            py_inst = from_dict(data_class=BicanTaxonomy, data=instance_dict)
        elif schema_name.lower() == "cap":
            py_inst = from_dict(data_class=CapTaxonomy, data=instance_dict)

    if not py_inst:
        # unknown schema, dynamically generate the python module and instantiate the class
        gen = generators.PythonGenerator(schema_def)
        output = gen.serialize()
        python_module = compile_python(output)
        py_target_class = getattr(python_module, root_class)
        py_inst = py_target_class(**instance_dict)

    for annotation in py_inst.annotations:
        # fix the author_annotation_fields in the json representation to be a string
        if annotation.author_annotation_fields and isinstance(annotation.author_annotation_fields, str):
            deserialised = json.loads(annotation.author_annotation_fields)
            annotation.author_annotation_fields = deserialised
    return py_inst


def fix_author_annotation_fields(json_obj):
    """
    Fix the author_annotation_fields in the json representation to be a string.
    Args:
        json_obj: json_obj dictionary.
    """
    for annotation in json_obj["annotations"]:
        if annotation.get("author_annotation_fields", None):
            annotation["author_annotation_fields"] = json.dumps(annotation["author_annotation_fields"])


def get_root_class(schema_name):
    """
    Returns the root class of the schema based on the schema name.
    Args:
        schema_name: The name of the schema.
    Returns: The root class of the schema.
    """
    root_class = None
    if schema_name.lower() == "base":
        root_class = "Taxonomy"
    elif schema_name.lower() == "bican":
        root_class = "BicanTaxonomy"
    elif schema_name.lower() == "cap":
        root_class = "CapTaxonomy"
    return root_class


if __name__ == "__main__":
    generate_data_class("base", os.path.join(SOURCE_DIR, "datamodel/cell_annotation_schema.py"))
    generate_data_class("bican", os.path.join(SOURCE_DIR, "datamodel/bican/cell_annotation_schema.py"))
    generate_data_class("cap", os.path.join(SOURCE_DIR, "datamodel/cap/cell_annotation_schema.py"))
