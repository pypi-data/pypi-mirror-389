import requests

from typing import Union, Optional, List
from ruamel.yaml import YAML

from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.utils.schema_as_dict import schema_as_dict
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.dumpers import json_dumper

from schema_automator.utils.schemautils import write_schema
from schema_automator.importers.jsonschema_import_engine import JsonSchemaImportEngine

from oaklib.utilities.subsets.value_set_expander import (
    ValueSetExpander,
    ValueSetConfiguration,
)


CAS_ROOT_CLASS = "Taxonomy"

# CAS_NAMESPACE = "https://cellular-semantics.sanger.ac.uk/ontology/CAS"
CAS_ROOT_NS = "cell_annotation_schema"
DEFAULT_PREFIXES = {
    # CAS_ROOT_NS: CAS_NAMESPACE + "/",
    # "CAS": CAS_NAMESPACE + "/",
    "obo": "http://purl.obolibrary.org/obo/",
    "CL": "http://purl.obolibrary.org/obo/CL_",
    "PCL": "http://purl.obolibrary.org/obo/PCL_",
    "RO": "http://purl.obolibrary.org/obo/RO_",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}


def decorate_linkml_schema(
    schema_obj: Union[dict, SchemaDefinition],
    output_path: Optional[str] = None,
) -> dict:
    """
    Adds additional properties to the LinkML schema necessary for Python conversion.
    Args:
        schema_obj (Union[dict, SchemaDefinition]): The LinkML schema object, either as a dictionary or a
        SchemaDefinition.
        output_path (Optional[str]): Path to the output schema file, if specified.
    Returns:
        dict: The schema decorated with additional properties for Python conversion.
    """
    if isinstance(schema_obj, SchemaDefinition):
        schema_obj = schema_as_dict(schema_obj)
    # schema_obj["id"] = CAS_NAMESPACE

    # this is a workaround for lack of annotation ids in the base schema
    if "Bican_Taxonomy" in schema_obj["classes"]:
        taxonomy_slots = list(schema_obj["classes"]["Taxonomy"]["slots"])
        taxonomy_slots.remove("annotations")
        schema_obj["classes"]["Taxonomy"]["slots"] = taxonomy_slots
        bican_annotation_slots = schema_obj["classes"]["Bican_Taxonomy"].get("slots", list())
        bican_annotation_slots.append("annotations")
        schema_obj["classes"]["Bican_Taxonomy"]["slots"] = bican_annotation_slots
    if "Cap_Taxonomy" in schema_obj["classes"]:
        taxonomy_slots = list(schema_obj["classes"]["Taxonomy"]["slots"])
        taxonomy_slots.remove("annotations")
        schema_obj["classes"]["Taxonomy"]["slots"] = taxonomy_slots
        cap_annotation_slots = schema_obj["classes"]["Cap_Taxonomy"].get("slots", list())
        cap_annotation_slots.append("annotations")
        schema_obj["classes"]["Cap_Taxonomy"]["slots"] = cap_annotation_slots

    for class_name in schema_obj["classes"]:
        if "attributes" in schema_obj["classes"][class_name]:
            clazz = schema_obj["classes"][class_name]
            del clazz["attributes"]

    if output_path:
        write_schema(schema_obj, output_path)

    return schema_obj


def decorate_linkml_ontology_schema(schema_obj: Union[dict, SchemaDefinition], ontology_iri: str, ontology_namespace: str, labelsets: Optional[List[str]] = None):
    """
    Decorates the LinkML schema with additional properties for OWL conversion.
    Args:
        schema_obj (Union[dict, SchemaDefinition]): The LinkML schema object, either as a dictionary or a
        SchemaDefinition.
        ontology_namespace (str): The namespace of the ontology (e.g., 'MTG').
        ontology_iri (str): The ontology IRI (e.g., 'https://purl.brain-bican.org/ontology/AIT_MTG/').
        labelsets (Optional[List[str]]): Labelsets used in the taxonomy, such as ['Cluster', 'Subclass', 'Class'].
    Returns:
        dict: The schema decorated with additional properties for OWL conversion.
    """
    if isinstance(schema_obj, SchemaDefinition):
        schema_obj = schema_as_dict(schema_obj)

    # these only required for ontology conversion
    ontology_namespace = ontology_namespace.upper()
    # prefixes = DEFAULT_PREFIXES.copy()
    # prefixes["linkml"] = "https://w3id.org/linkml/"
    prefixes = schema_obj["prefixes"]
    prefixes["_base"] = ontology_iri
    prefixes[ontology_namespace] = ontology_iri
    labelsets = labelsets or []
    for labelset in labelsets:
        prefixes[labelset] = ontology_iri + f"{labelset}#"
    schema_obj["prefixes"] = prefixes
    schema_obj["slots"]["id"] = {"identifier": True, "range": "uriorcurie"}
    schema_obj["classes"]["Labelset"]["slots"] = list(schema_obj["classes"]["Labelset"]["slots"]) + ["id"]
    schema_obj["classes"]["Taxonomy"]["slots"] = list(schema_obj["classes"]["Taxonomy"]["slots"]) + ["id"]
    # schema_obj["slots"]["cell_id"]["identifier"] = True   # TODO
    is_bican = "Bican_Taxonomy" in schema_obj["classes"]
    is_cap = "Cap_Taxonomy" in schema_obj["classes"]
    if "cell_set_accession" in schema_obj["slots"]:
        schema_obj["slots"]["cell_set_accession"]["identifier"] = True
    if "parent_cell_set_accession" in schema_obj["slots"]:
        schema_obj["slots"]["parent_cell_set_accession"]["range"] = "Bican_Annotation"
    if is_bican and "labelset" in schema_obj["slots"]:
        schema_obj["slots"]["labelset"]["range"] = "Bican_Labelset"

    schema_obj = decorate_linkml_schema(schema_obj)
    return schema_obj


def expand_schema(
    config: Optional[str],
    yaml_obj: dict,
    value_set_names: List[str],
    output_path: Optional[str] = None,
):
    """
    Dynamically expands the yaml_obj schema in-place using specified value set names.
    Args:
        config (Optional[str]): Path to the configuration file. If None, a default configuration is used.
        yaml_obj (dict): YAML schema object that will be expanded.
        value_set_names (List[str]): Names of the value sets to be included in the expansion.
        output_path (Optional[str]): Path where the expanded schema file will be saved, if specified.
    Note:
        Source code referenced from: https://github.com/INCATools/ontology-access-kit/blob/main/src/oaklib/utilities/subsets/value_set_expander.py
    """
    expander = ValueSetExpander()
    if config:
        expander.configuration = yaml_loader.load(
            config, target_class=ValueSetConfiguration
        )

    yaml = YAML()
    schema = yaml_loader.load(yaml_obj, target_class=SchemaDefinition)
    if value_set_names is None:
        value_set_names = list(schema.enums.keys())
    for value_set_name in value_set_names:
        if value_set_name not in schema.enums:
            raise ValueError(f"Unknown value set: {value_set_name}")
        value_set = schema.enums[value_set_name]
        pvs = list(expander.expand_value_set(value_set, schema=schema))
        yaml_obj["enums"][value_set_name]["permissible_values"] = {
            str(pv.text): json_dumper.to_dict(pv) for pv in pvs
        }
    if output_path:
        with open(output_path, "w", encoding="UTF-8") as file:
            yaml.dump(yaml_obj, stream=file)
    return yaml_obj
