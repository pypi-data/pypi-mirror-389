import dataclasses

from jsonasobj2 import JsonObj


def asdict(taxonomy):
    """
    Convert a taxonomy python object to a dictionary.
    :param taxonomy: taxonomy object
    :return: dictionary
    """
    taxon_dict = dataclasses.asdict(taxonomy)

    for annotation in taxon_dict["annotations"]:
        # Convert JsonObj to dict
        if annotation.get("author_annotation_fields") and isinstance(
                annotation["author_annotation_fields"], JsonObj):
            annotation["author_annotation_fields"] = annotation["author_annotation_fields"]._as_dict

        # Convert CellTypeEnum to string
        if annotation.get("cell_ontology_term_id"):
            if type(annotation["cell_ontology_term_id"]).__name__ == "CellTypeEnum":
                annot_obj = get_annotation_with_name(taxonomy, annotation["cell_label"],
                                                     annotation["labelset"])
                annotation["cell_ontology_term_id"] = str(annot_obj.cell_ontology_term_id.code.text)

    # Remove None values
    def remove_none_values(d):
        if not isinstance(d, dict):
            return d
        return {k: remove_none_values(v) for k, v in d.items() if v is not None}
    taxon_dict = remove_none_values(taxon_dict)

    return taxon_dict


def get_annotation_with_name(taxonomy, cell_label, labelset, compare_func=None):
    """
    Get an annotation with a given cell label and labelset in the given taxonomy.
    :param taxonomy: taxonomy object
    :param cell_label: cell label
    :param labelset: labelset
    :param compare_func: optional function to compare cell labels (such as `lambda x, y: x.endswith(y)`)
    :return: annotation object. None if not found
    """
    cell_label = str(cell_label).strip()
    for annotation in taxonomy.annotations:
        if annotation.labelset == labelset:
            if compare_func:
                if compare_func(annotation.cell_label, cell_label):
                    return annotation
            else:
                if annotation.cell_label == cell_label:
                    return annotation
    return None
