import rdflib

from pathlib import Path
from typing import Union, Optional, List

from cell_annotation_schema.file_utils import read_schema, get_json_from_file
from cell_annotation_schema.ontology.schema import (
    decorate_linkml_ontology_schema,
    expand_schema,
)
from cell_annotation_schema.ontology.data import dump_to_rdf, populate_ids


def export_to_rdf(
    cas_schema: Optional[Union[str, dict]],
    data: Union[str, dict],
    ontology_namespace: str,
    ontology_iri: str,
    output_path: str = None,
    validate: bool = True,
    include_cells: bool = True,
) -> rdflib.Graph:
    """
    Generates and returns an RDF graph from the provided data and CAS schema, with an option to write the RDF graph to a file.
    Args:
        cas_schema (Optional[Union[str, dict]]):
            Name of the CAS release (such as `base`, `cap`, `bican`), path to the CAS schema file, or CAS schema Yaml dict.
            If not provided, reads the `base` CAS schema.
        data (Union[str, dict]):
            The data JSON file path or JSON object dictionary.
        ontology_namespace (str):
            Ontology namespace (e.g., `MTG`).
        ontology_iri (str):
            Ontology IRI (e.g., `https://purl.brain-bican.org/ontology/AIT_MTG/`).
        labelsets (Optional[List[str]]):
            Labelsets used in the taxonomy, such as `["Cluster", "Subclass", "Class"]`.
        output_path (Optional[str]):
            Path to the output RDF file, if specified.
        validate (bool):
            Determines if data-schema validation checks will be performed. True by default.
        include_cells (bool):
            Determines if cell data will be included in the RDF output. True by default.
    Returns:
        An RDFlib graph object.
    """
    if not cas_schema:
        cas_schema = "base"
    base_linkml_schema = read_schema(cas_schema)

    data = get_instance_data(data)

    decorated_schema = decorate_linkml_ontology_schema(
        base_linkml_schema,
        ontology_namespace=ontology_namespace,
        ontology_iri=ontology_iri,
        labelsets=get_labelsets(data),
    )
    expanded_schema = expand_schema(
        config=None, yaml_obj=decorated_schema, value_set_names=["CellTypeEnum"]
    )

    # Prepare the data
    instance = populate_ids(
        data,
        ontology_namespace=ontology_namespace,
        ontology_id=ontology_namespace,
    )
    rdf_graph = dump_to_rdf(
        schema=expanded_schema,
        instance=instance,
        ontology_namespace=ontology_namespace,
        ontology_iri=ontology_iri,
        schema_name=get_schema_name(cas_schema),
        validate=validate,
        include_cells=include_cells,
        output_path=output_path,
    )

    return rdf_graph


def get_instance_data(data: Union[str, dict]):
    """
    Reads the data from the file or returns the data as is.
    Args:
        data: The data JSON file path or JSON object dictionary.
    Returns: The data as a dictionary.
    """
    if isinstance(data, Path):
        data = str(data)
    if isinstance(data, str):
        data = get_json_from_file(data)
        if data is None:
            raise ValueError("No such file: " + str(data))
    return data


def get_schema_name(cas_schema: str) -> str:
    """
    Returns the schema name based on the CAS schema name.
    Args:
        cas_schema (str): Name of the CAS schema.
    Returns:
        str: The schema name.
    """
    if isinstance(cas_schema, str):
        if cas_schema.lower() == "base" or cas_schema.endswith("general_schema.yaml"):
            return "base"
        elif cas_schema.lower() == "bican" or cas_schema.endswith("BICAN_schema.yaml"):
            return "bican"
        elif cas_schema.lower() == "cap" or cas_schema.endswith("CAP_schema.yaml"):
            return "cap"
    return ""


def get_labelsets(instance):
    """
    Gets the labelsets from the instance data.
    Args:
        instance: The instance data.
    Returns: The labelsets to be used.
    """
    ranked_lblsets = (ls for ls in instance["labelsets"] if "rank" in ls)
    if ranked_lblsets:
        labelset_objects = sorted(ranked_lblsets, key=lambda x: x["rank"])
    else:
        labelset_objects = instance["labelsets"]
    return [ls["name"] for ls in labelset_objects]
