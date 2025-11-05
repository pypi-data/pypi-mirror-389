# Auto generated from None by pythongen.py version: 0.0.1
# Generation date: 2025-06-13T12:55:33
# Schema: General_Cell_Annotation_Open_Standard
#
# id: https://cellular-semantics.sanger.ac.uk/ontology/CAS
# description: General, open-standard schema for cell annotations
# license: GNU GPL v3.0

import dataclasses
import re
from jsonasobj2 import JsonObj, as_dict
from typing import Optional, List, Union, Dict, ClassVar, Any
from dataclasses import dataclass
from datetime import date, datetime, time
from linkml_runtime.linkml_model.meta import EnumDefinition, PermissibleValue, PvFormulaOptions

from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.metamodelcore import empty_list, empty_dict, bnode
from linkml_runtime.utils.yamlutils import YAMLRoot, extended_str, extended_float, extended_int
from linkml_runtime.utils.dataclass_extensions_376 import dataclasses_init_fn_with_kwargs
from linkml_runtime.utils.formatutils import camelcase, underscore, sfx
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from rdflib import Namespace, URIRef
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.metamodelcore import Bool, Curie, Decimal, ElementIdentifier, NCName, NodeIdentifier, URI, URIorCURIE, XSDDate, XSDDateTime, XSDTime

metamodel_version = "1.7.0"
version = None

# Overwrite dataclasses _init_fn to add **kwargs in __init__
dataclasses._init_fn = dataclasses_init_fn_with_kwargs

# Namespaces
CAS = CurieNamespace('CAS', 'https://purl.brain-bican.org/taxonomy/')
CL = CurieNamespace('CL', 'http://purl.obolibrary.org/obo/CL_')
CELLXGENE_DATASET = CurieNamespace('CellXGene_dataset', 'https://cellxgene.cziscience.com/datasets/')
IAO = CurieNamespace('IAO', 'http://purl.obolibrary.org/obo/IAO_')
PCL = CurieNamespace('PCL', 'http://purl.obolibrary.org/obo/PCL_')
RO = CurieNamespace('RO', 'http://purl.obolibrary.org/obo/RO_')
CELL_ANNOTATION_SCHEMA = CurieNamespace('cell_annotation_schema', 'https://purl.brain-bican.org/taxonomy/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
OBO = CurieNamespace('obo', 'http://purl.obolibrary.org/obo/')
RDFS = CurieNamespace('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
SCHEMA = CurieNamespace('schema', 'http://schema.org/')
SHEX = CurieNamespace('shex', 'http://www.w3.org/ns/shex#')
SKOS = CurieNamespace('skos', 'http://www.w3.org/2004/02/skos/core#')
XSD = CurieNamespace('xsd', 'http://www.w3.org/2001/XMLSchema#')
DEFAULT_ = CELL_ANNOTATION_SCHEMA


# Types
class String(str):
    """ A character string """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "string"
    type_model_uri = CELL_ANNOTATION_SCHEMA.String


class Integer(int):
    """ An integer """
    type_class_uri = XSD["integer"]
    type_class_curie = "xsd:integer"
    type_name = "integer"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Integer


class Boolean(Bool):
    """ A binary (true or false) value """
    type_class_uri = XSD["boolean"]
    type_class_curie = "xsd:boolean"
    type_name = "boolean"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Boolean


class Float(float):
    """ A real number that conforms to the xsd:float specification """
    type_class_uri = XSD["float"]
    type_class_curie = "xsd:float"
    type_name = "float"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Float


class Double(float):
    """ A real number that conforms to the xsd:double specification """
    type_class_uri = XSD["double"]
    type_class_curie = "xsd:double"
    type_name = "double"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Double


class Decimal(Decimal):
    """ A real number with arbitrary precision that conforms to the xsd:decimal specification """
    type_class_uri = XSD["decimal"]
    type_class_curie = "xsd:decimal"
    type_name = "decimal"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Decimal


class Time(XSDTime):
    """ A time object represents a (local) time of day, independent of any particular day """
    type_class_uri = XSD["time"]
    type_class_curie = "xsd:time"
    type_name = "time"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Time


class Date(XSDDate):
    """ a date (year, month and day) in an idealized calendar """
    type_class_uri = XSD["date"]
    type_class_curie = "xsd:date"
    type_name = "date"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Date


class Datetime(XSDDateTime):
    """ The combination of a date and time """
    type_class_uri = XSD["dateTime"]
    type_class_curie = "xsd:dateTime"
    type_name = "datetime"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Datetime


class DateOrDatetime(str):
    """ Either a date or a datetime """
    type_class_uri = LINKML["DateOrDatetime"]
    type_class_curie = "linkml:DateOrDatetime"
    type_name = "date_or_datetime"
    type_model_uri = CELL_ANNOTATION_SCHEMA.DateOrDatetime


class Uriorcurie(URIorCURIE):
    """ a URI or a CURIE """
    type_class_uri = XSD["anyURI"]
    type_class_curie = "xsd:anyURI"
    type_name = "uriorcurie"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Uriorcurie


class Curie(Curie):
    """ a compact URI """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "curie"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Curie


class Uri(URI):
    """ a complete URI """
    type_class_uri = XSD["anyURI"]
    type_class_curie = "xsd:anyURI"
    type_name = "uri"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Uri


class Ncname(NCName):
    """ Prefix part of CURIE """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "ncname"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Ncname


class Objectidentifier(ElementIdentifier):
    """ A URI or CURIE that represents an object in the model. """
    type_class_uri = SHEX["iri"]
    type_class_curie = "shex:iri"
    type_name = "objectidentifier"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Objectidentifier


class Nodeidentifier(NodeIdentifier):
    """ A URI, CURIE or BNODE that represents a node in a model. """
    type_class_uri = SHEX["nonLiteral"]
    type_class_curie = "shex:nonLiteral"
    type_name = "nodeidentifier"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Nodeidentifier


class Jsonpointer(str):
    """ A string encoding a JSON Pointer. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to a valid object within the current instance document when encoded in tree form. """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "jsonpointer"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Jsonpointer


class Jsonpath(str):
    """ A string encoding a JSON Path. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded in tree form. """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "jsonpath"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Jsonpath


class Sparqlpath(str):
    """ A string encoding a SPARQL Property Path. The value of the string MUST conform to SPARQL syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded as RDF. """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "sparqlpath"
    type_model_uri = CELL_ANNOTATION_SCHEMA.Sparqlpath


# Class references



@dataclass(repr=False)
class AnnotationTransfer(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["AnnotationTransfer"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:AnnotationTransfer"
    class_name: ClassVar[str] = "AnnotationTransfer"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.AnnotationTransfer

    transferred_cell_label: Optional[str] = None
    source_taxonomy: Optional[Union[str, URIorCURIE]] = None
    source_node_accession: Optional[str] = None
    algorithm_name: Optional[str] = None
    comment: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.transferred_cell_label is not None and not isinstance(self.transferred_cell_label, str):
            self.transferred_cell_label = str(self.transferred_cell_label)

        if self.source_taxonomy is not None and not isinstance(self.source_taxonomy, URIorCURIE):
            self.source_taxonomy = URIorCURIE(self.source_taxonomy)

        if self.source_node_accession is not None and not isinstance(self.source_node_accession, str):
            self.source_node_accession = str(self.source_node_accession)

        if self.algorithm_name is not None and not isinstance(self.algorithm_name, str):
            self.algorithm_name = str(self.algorithm_name)

        if self.comment is not None and not isinstance(self.comment, str):
            self.comment = str(self.comment)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Cell(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["Cell"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:Cell"
    class_name: ClassVar[str] = "Cell"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.Cell

    cell_id: str = None
    confidence: Optional[float] = None
    author_categories: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.cell_id):
            self.MissingRequiredField("cell_id")
        if not isinstance(self.cell_id, str):
            self.cell_id = str(self.cell_id)

        if self.confidence is not None and not isinstance(self.confidence, float):
            self.confidence = float(self.confidence)

        if self.author_categories is not None and not isinstance(self.author_categories, str):
            self.author_categories = str(self.author_categories)

        super().__post_init__(**kwargs)


Any = Any

@dataclass(repr=False)
class Review(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["Review"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:Review"
    class_name: ClassVar[str] = "Review"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.Review

    datestamp: str = None
    reviewer: Optional[str] = None
    review: Optional[Union[str, "ReviewOptions"]] = None
    explanation: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.datestamp):
            self.MissingRequiredField("datestamp")
        if not isinstance(self.datestamp, str):
            self.datestamp = str(self.datestamp)

        if self.reviewer is not None and not isinstance(self.reviewer, str):
            self.reviewer = str(self.reviewer)

        if self.review is not None and not isinstance(self.review, ReviewOptions):
            self.review = ReviewOptions(self.review)

        if self.explanation is not None and not isinstance(self.explanation, str):
            self.explanation = str(self.explanation)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Labelset(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["Labelset"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:Labelset"
    class_name: ClassVar[str] = "Labelset"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.Labelset

    name: str = None
    description: Optional[str] = None
    annotation_method: Optional[Union[str, "AnnotationMethodOptions"]] = None
    automated_annotation: Optional[Union[dict, "AutomatedAnnotation"]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, str):
            self.name = str(self.name)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.annotation_method is not None and not isinstance(self.annotation_method, AnnotationMethodOptions):
            self.annotation_method = AnnotationMethodOptions(self.annotation_method)

        if self.automated_annotation is not None and not isinstance(self.automated_annotation, AutomatedAnnotation):
            self.automated_annotation = AutomatedAnnotation(**as_dict(self.automated_annotation))

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class BicanLabelset(Labelset):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["Labelset"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:Labelset"
    class_name: ClassVar[str] = "Bican_Labelset"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.BicanLabelset

    name: str = None
    rank: Optional[int] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.rank is not None and not isinstance(self.rank, int):
            self.rank = int(self.rank)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class AutomatedAnnotation(YAMLRoot):
    """
    A set of fields for recording the details of the automated annotation algorithm used. (Common 'automated
    annotation methods' would include PopV, Azimuth, CellTypist, scArches, etc.)
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["AutomatedAnnotation"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:AutomatedAnnotation"
    class_name: ClassVar[str] = "AutomatedAnnotation"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.AutomatedAnnotation

    algorithm_version: str = None
    algorithm_repo_url: str = None
    algorithm_name: Optional[str] = None
    reference_location: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.algorithm_version):
            self.MissingRequiredField("algorithm_version")
        if not isinstance(self.algorithm_version, str):
            self.algorithm_version = str(self.algorithm_version)

        if self._is_empty(self.algorithm_repo_url):
            self.MissingRequiredField("algorithm_repo_url")
        if not isinstance(self.algorithm_repo_url, str):
            self.algorithm_repo_url = str(self.algorithm_repo_url)

        if self.algorithm_name is not None and not isinstance(self.algorithm_name, str):
            self.algorithm_name = str(self.algorithm_name)

        if self.reference_location is not None and not isinstance(self.reference_location, str):
            self.reference_location = str(self.reference_location)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Annotation(YAMLRoot):
    """
    A collection of fields recording a cell type/class/state annotation on some set of cells, supporting evidence and
    provenance. As this is intended as a general schema, compulsory fields are kept to a minimum. However, tools using
    this schema are encouarged to specify a larger set of compulsory fields for publication. Note: This schema
    deliberately allows for additional fields in order to support ad hoc user fields, new formal schema extensions and
    project/tool specific metadata.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = PCL["0010001"]
    class_class_curie: ClassVar[str] = "PCL:0010001"
    class_name: ClassVar[str] = "Annotation"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.Annotation

    labelset: str = None
    cell_label: str = None
    cell_fullname: Optional[str] = None
    cell_ontology_term_id: Optional[Union[str, "CellTypeEnum"]] = None
    cell_ontology_term: Optional[str] = None
    cell_ids: Optional[Union[str, List[str]]] = empty_list()
    rationale: Optional[str] = None
    rationale_dois: Optional[Union[str, List[str]]] = empty_list()
    marker_gene_evidence: Optional[Union[str, List[str]]] = empty_list()
    synonyms: Optional[Union[str, List[str]]] = empty_list()
    reviews: Optional[Union[Union[dict, Review], List[Union[dict, Review]]]] = empty_list()
    author_annotation_fields: Optional[Union[dict, Any]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.labelset):
            self.MissingRequiredField("labelset")
        if not isinstance(self.labelset, str):
            self.labelset = str(self.labelset)

        if self._is_empty(self.cell_label):
            self.MissingRequiredField("cell_label")
        if not isinstance(self.cell_label, str):
            self.cell_label = str(self.cell_label)

        if self.cell_fullname is not None and not isinstance(self.cell_fullname, str):
            self.cell_fullname = str(self.cell_fullname)

        if self.cell_ontology_term_id is not None and not isinstance(self.cell_ontology_term_id, CellTypeEnum):
            self.cell_ontology_term_id = CellTypeEnum(self.cell_ontology_term_id)

        if self.cell_ontology_term is not None and not isinstance(self.cell_ontology_term, str):
            self.cell_ontology_term = str(self.cell_ontology_term)

        if not isinstance(self.cell_ids, list):
            self.cell_ids = [self.cell_ids] if self.cell_ids is not None else []
        self.cell_ids = [v if isinstance(v, str) else str(v) for v in self.cell_ids]

        if self.rationale is not None and not isinstance(self.rationale, str):
            self.rationale = str(self.rationale)

        if not isinstance(self.rationale_dois, list):
            self.rationale_dois = [self.rationale_dois] if self.rationale_dois is not None else []
        self.rationale_dois = [v if isinstance(v, str) else str(v) for v in self.rationale_dois]

        if not isinstance(self.marker_gene_evidence, list):
            self.marker_gene_evidence = [self.marker_gene_evidence] if self.marker_gene_evidence is not None else []
        self.marker_gene_evidence = [v if isinstance(v, str) else str(v) for v in self.marker_gene_evidence]

        if not isinstance(self.synonyms, list):
            self.synonyms = [self.synonyms] if self.synonyms is not None else []
        self.synonyms = [v if isinstance(v, str) else str(v) for v in self.synonyms]

        self._normalize_inlined_as_dict(slot_name="reviews", slot_type=Review, key_name="datestamp", keyed=False)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class BicanAnnotation(Annotation):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = PCL["0010001"]
    class_class_curie: ClassVar[str] = "PCL:0010001"
    class_name: ClassVar[str] = "Bican_Annotation"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.BicanAnnotation

    labelset: str = None
    cell_label: str = None
    cell_set_accession: str = None
    parent_cell_set_accession: Optional[str] = None
    transferred_annotations: Optional[Union[Union[dict, AnnotationTransfer], List[Union[dict, AnnotationTransfer]]]] = empty_list()
    cells: Optional[Union[Union[dict, Cell], List[Union[dict, Cell]]]] = empty_list()
    negative_marker_gene_evidence: Optional[Union[str, List[str]]] = empty_list()
    neurotransmitter_accession: Optional[str] = None
    neurotransmitter_rationale: Optional[str] = None
    neurotransmitter_marker_gene_evidence: Optional[Union[str, List[str]]] = empty_list()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.cell_set_accession):
            self.MissingRequiredField("cell_set_accession")
        if not isinstance(self.cell_set_accession, str):
            self.cell_set_accession = str(self.cell_set_accession)

        if self.parent_cell_set_accession is not None and not isinstance(self.parent_cell_set_accession, str):
            self.parent_cell_set_accession = str(self.parent_cell_set_accession)

        if not isinstance(self.transferred_annotations, list):
            self.transferred_annotations = [self.transferred_annotations] if self.transferred_annotations is not None else []
        self.transferred_annotations = [v if isinstance(v, AnnotationTransfer) else AnnotationTransfer(**as_dict(v)) for v in self.transferred_annotations]

        self._normalize_inlined_as_dict(slot_name="cells", slot_type=Cell, key_name="cell_id", keyed=False)

        if not isinstance(self.negative_marker_gene_evidence, list):
            self.negative_marker_gene_evidence = [self.negative_marker_gene_evidence] if self.negative_marker_gene_evidence is not None else []
        self.negative_marker_gene_evidence = [v if isinstance(v, str) else str(v) for v in self.negative_marker_gene_evidence]

        if self.neurotransmitter_accession is not None and not isinstance(self.neurotransmitter_accession, str):
            self.neurotransmitter_accession = str(self.neurotransmitter_accession)

        if self.neurotransmitter_rationale is not None and not isinstance(self.neurotransmitter_rationale, str):
            self.neurotransmitter_rationale = str(self.neurotransmitter_rationale)

        if not isinstance(self.neurotransmitter_marker_gene_evidence, list):
            self.neurotransmitter_marker_gene_evidence = [self.neurotransmitter_marker_gene_evidence] if self.neurotransmitter_marker_gene_evidence is not None else []
        self.neurotransmitter_marker_gene_evidence = [v if isinstance(v, str) else str(v) for v in self.neurotransmitter_marker_gene_evidence]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Taxonomy(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["Taxonomy"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:Taxonomy"
    class_name: ClassVar[str] = "Taxonomy"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.Taxonomy

    title: str = None
    author_name: str = None
    labelsets: Union[Union[dict, Labelset], List[Union[dict, Labelset]]] = None
    matrix_file_id: Optional[Union[str, URIorCURIE]] = None
    description: Optional[str] = None
    cellannotation_schema_version: Optional[str] = None
    cellannotation_timestamp: Optional[str] = None
    cellannotation_version: Optional[str] = None
    cellannotation_url: Optional[str] = None
    author_list: Optional[str] = None
    author_contact: Optional[str] = None
    orcid: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.title):
            self.MissingRequiredField("title")
        if not isinstance(self.title, str):
            self.title = str(self.title)

        if self._is_empty(self.author_name):
            self.MissingRequiredField("author_name")
        if not isinstance(self.author_name, str):
            self.author_name = str(self.author_name)

        if self._is_empty(self.labelsets):
            self.MissingRequiredField("labelsets")
        if not isinstance(self.labelsets, list):
            self.labelsets = [self.labelsets] if self.labelsets is not None else []
        self.labelsets = [v if isinstance(v, Labelset) else Labelset(**as_dict(v)) for v in self.labelsets]

        if self.matrix_file_id is not None and not isinstance(self.matrix_file_id, URIorCURIE):
            self.matrix_file_id = URIorCURIE(self.matrix_file_id)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.cellannotation_schema_version is not None and not isinstance(self.cellannotation_schema_version, str):
            self.cellannotation_schema_version = str(self.cellannotation_schema_version)

        if self.cellannotation_timestamp is not None and not isinstance(self.cellannotation_timestamp, str):
            self.cellannotation_timestamp = str(self.cellannotation_timestamp)

        if self.cellannotation_version is not None and not isinstance(self.cellannotation_version, str):
            self.cellannotation_version = str(self.cellannotation_version)

        if self.cellannotation_url is not None and not isinstance(self.cellannotation_url, str):
            self.cellannotation_url = str(self.cellannotation_url)

        if self.author_list is not None and not isinstance(self.author_list, str):
            self.author_list = str(self.author_list)

        if self.author_contact is not None and not isinstance(self.author_contact, str):
            self.author_contact = str(self.author_contact)

        if self.orcid is not None and not isinstance(self.orcid, str):
            self.orcid = str(self.orcid)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class BicanTaxonomy(Taxonomy):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA["Taxonomy"]
    class_class_curie: ClassVar[str] = "cell_annotation_schema:Taxonomy"
    class_name: ClassVar[str] = "Bican_Taxonomy"
    class_model_uri: ClassVar[URIRef] = CELL_ANNOTATION_SCHEMA.BicanTaxonomy

    title: str = None
    author_name: str = None
    annotations: Union[Union[dict, BicanAnnotation], List[Union[dict, BicanAnnotation]]] = None
    labelsets: Union[Union[dict, BicanLabelset], List[Union[dict, BicanLabelset]]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.annotations):
            self.MissingRequiredField("annotations")
        if not isinstance(self.annotations, list):
            self.annotations = [self.annotations] if self.annotations is not None else []
        self.annotations = [v if isinstance(v, BicanAnnotation) else BicanAnnotation(**as_dict(v)) for v in self.annotations]

        if self._is_empty(self.labelsets):
            self.MissingRequiredField("labelsets")
        if not isinstance(self.labelsets, list):
            self.labelsets = [self.labelsets] if self.labelsets is not None else []
        self.labelsets = [v if isinstance(v, BicanLabelset) else BicanLabelset(**as_dict(v)) for v in self.labelsets]

        super().__post_init__(**kwargs)


# Enumerations
class ReviewOptions(EnumDefinitionImpl):

    Agree = PermissibleValue(text="Agree")
    Disagree = PermissibleValue(text="Disagree")

    _defn = EnumDefinition(
        name="ReviewOptions",
    )

class AnnotationMethodOptions(EnumDefinitionImpl):

    algorithmic = PermissibleValue(text="algorithmic")
    manual = PermissibleValue(text="manual")
    both = PermissibleValue(text="both")

    _defn = EnumDefinition(
        name="AnnotationMethodOptions",
    )

class CellTypeEnum(EnumDefinitionImpl):

    _defn = EnumDefinition(
        name="CellTypeEnum",
    )

    @classmethod
    def _addvals(cls):
        setattr(cls, "CL:0011105",
            PermissibleValue(
                text="CL:0011105",
                description="""A type of interneuron in the retinal inner nuclear layer which carries information from the inner plexiform layer and the outer plexiform layer, using dopamine.""",
                meaning=CL["0011105"]))
        setattr(cls, "CL:0000057",
            PermissibleValue(
                text="CL:0000057",
                description="""A connective tissue cell which secretes an extracellular matrix rich in collagen and other macromolecules. Flattened and irregular in outline with branching processes; appear fusiform or spindle-shaped.""",
                meaning=CL["0000057"]))
        setattr(cls, "CL:0002656",
            PermissibleValue(
                text="CL:0002656",
                description="""A glandular epithelial cell of the endometrium. Following ovulation, these cells secrete a glycogen-rich substance known as histotroph or uterine milk, which nourishes the embryo if implantation occurs.""",
                meaning=CL["0002656"]))
        setattr(cls, "CL:4033014",
            PermissibleValue(
                text="CL:4033014",
                description="""A small, narrow, peg-shaped epithelial cell with little cytoplasm that is part of oviduct epithelium. This cell is rarer than the ciliated and secretory epithelial cells of the fallopian tube epithelium and is often found intercalated between them. Peg cells are generally distributed basally along the epithelium and have been found in high concentrations at the fimbriated, distal end of the fallopian tube in humans. It may have a regenerative/stem-cell function. In humans, markers include EPCAM, CD44, and ITGA6.""",
                meaning=CL["4033014"]))
        setattr(cls, "CL:0002224",
            PermissibleValue(
                text="CL:0002224",
                description="""A cell of the cuboidal epithelium that covers the lens. The cells of the lens epithelium regulate most of the homeostatic functions of the lens. As ions, nutrients, and liquid enter the lens from the aqueous humor, Na+/K+ ATPase pumps in the lens epithelial cells pump ions out of the lens to maintain appropriate lens osmolarity and volume, with equatorially positioned lens epithelium cells contributing most to this current. The activity of the Na+/K+ ATPases keeps water and current flowing through the lens from the poles and exiting through the equatorial regions. The cells of the lens epithelium also serve as the progenitors for new lens fibers. It constantly lays down fibers in the embryo, fetus, infant, and adult, and continues to lay down fibers for lifelong growth.""",
                meaning=CL["0002224"]))
        setattr(cls, "CL:4030031",
            PermissibleValue(
                text="CL:4030031",
                description="""Any cell that is located within the interstitium between the cells most prominent in defining a given tissue. \"Interstitial cell\" is a morphological term and refers to a variety of cells with differing origins and phenotypes.""",
                meaning=CL["4030031"]))
        setattr(cls, "CL:4052036",
            PermissibleValue(
                text="CL:4052036",
                description="""A tuft cell that is part of the nasal cavity epithelium, located in both the respiratory and olfactory epithelia of the nose. This cell plays key roles in chemosensation, lipid mediator production, immune responses, and epithelial homeostasis.""",
                meaning=CL["4052036"]))
        setattr(cls, "CL:0002625",
            PermissibleValue(
                text="CL:0002625",
                description="A cell of the seminiferous tubule epithelium.",
                meaning=CL["0002625"]))
        setattr(cls, "CL:1000490",
            PermissibleValue(
                text="CL:1000490",
                description="A mesothelial cell that is part of the peritoneum.",
                meaning=CL["1000490"]))
        setattr(cls, "CL:0000801",
            PermissibleValue(
                text="CL:0000801",
                description="""A mature gamma-delta T cell that is found in the columnar epithelium of the gastrointestinal tract. These cells participate in mucosal immune responses.""",
                meaning=CL["0000801"]))
        setattr(cls, "CL:0002116",
            PermissibleValue(
                text="CL:0002116",
                description="""A B220-low CD38-positive unswitched memory B cell is a CD38-positive unswitched memory B cell that has the phenotype B220-low, CD38-positive, IgD-positive, CD138-negative, and IgG-negative.""",
                meaning=CL["0002116"]))
        setattr(cls, "CL:0000578",
            PermissibleValue(
                text="CL:0000578",
                description="""A cell in vitro that has undergone physical changes as a consequence of a deliberate and specific experimental procedure.""",
                meaning=CL["0000578"]))
        setattr(cls, "CL:0000618",
            PermissibleValue(
                text="CL:0000618",
                meaning=CL["0000618"]))
        setattr(cls, "CL:0000435",
            PermissibleValue(
                text="CL:0000435",
                meaning=CL["0000435"]))
        setattr(cls, "CL:0000654",
            PermissibleValue(
                text="CL:0000654",
                description="A primary oocyte is an oocyte that has not completed female meosis I.",
                meaning=CL["0000654"]))
        setattr(cls, "CL:0002130",
            PermissibleValue(
                text="CL:0002130",
                description="A cardiac myocyte of the interatrial region of the heart.",
                meaning=CL["0002130"]))
        setattr(cls, "CL:0017003",
            PermissibleValue(
                text="CL:0017003",
                description="An epithelial cell that is part of the prostatic urethra.",
                meaning=CL["0017003"]))
        setattr(cls, "CL:0002038",
            PermissibleValue(
                text="CL:0002038",
                description="""A CD4-positive, CXCR5-positive, CCR7-negative alpha-beta T cell located in follicles of secondary lymph nodes that is BCL6-high, ICOS-high and PD1-high, and stimulates follicular B cells to undergo class-switching and antibody production.""",
                meaning=CL["0002038"]))
        setattr(cls, "CL:0002311",
            PermissibleValue(
                text="CL:0002311",
                description="An acidophilic cell of the anterior pituitary that produces prolactin.",
                meaning=CL["0002311"]))
        setattr(cls, "CL:0000722",
            PermissibleValue(
                text="CL:0000722",
                meaning=CL["0000722"]))
        setattr(cls, "CL:0000059",
            PermissibleValue(
                text="CL:0000059",
                description="""Skeletogenic cell that produces enamel, overlies the odontogenic papilla, and arises from the differentiation of a preameloblast cell.""",
                meaning=CL["0000059"]))
        setattr(cls, "CL:0000160",
            PermissibleValue(
                text="CL:0000160",
                description="""A specialized, columnar, mucus secreting epithelial cell shaped like a flask or goblet. A narrow basal end contains the nucleus while the apical end is swollen by the accumulation of mucus laden secretory granules.  Short microvilli project from the apical plasma membrane.""",
                meaning=CL["0000160"]))
        setattr(cls, "CL:0002680",
            PermissibleValue(
                text="CL:0002680",
                description="A PP cell found in intestine.",
                meaning=CL["0002680"]))
        setattr(cls, "CL:0002382",
            PermissibleValue(
                text="CL:0002382",
                description="A conidium that has more than one nucleus.",
                meaning=CL["0002382"]))
        setattr(cls, "CL:0002027",
            PermissibleValue(
                text="CL:0002027",
                description="A megakaryocyte cell with is CD9-positive and CD41-positive.",
                meaning=CL["0002027"]))
        setattr(cls, "CL:4033024",
            PermissibleValue(
                text="CL:4033024",
                description="A basal cell that is part of a duct of an airway submucosal gland.",
                meaning=CL["4033024"]))
        setattr(cls, "CL:4042034",
            PermissibleValue(
                text="CL:4042034",
                description="""An interneuron neuron characterized by the expression of calcitonin gene-related peptide (CGRP), a 37-amino acid neuropeptide. This neuron type is involved in nociception and pain modulation by facilitating the transmission of nociceptive signals from peripheral sensory nerve endings to central nervous system structures. This neuron type is found in the dorsal root ganglia (DRG) and trigeminal ganglion, and the spinal cord dorsal horn.""",
                meaning=CL["4042034"]))
        setattr(cls, "CL:0019019",
            PermissibleValue(
                text="CL:0019019",
                description="A smooth muscle cell that is part of the tracheobronchial tree.",
                meaning=CL["0019019"]))
        setattr(cls, "CL:0010017",
            PermissibleValue(
                text="CL:0010017",
                description="A zygote in a plant or an animal.",
                meaning=CL["0010017"]))
        setattr(cls, "CL:0000815",
            PermissibleValue(
                text="CL:0000815",
                description="""A T cell which regulates overall immune responses as well as the responses of other T cell subsets through direct cell-cell contact and cytokine release.""",
                meaning=CL["0000815"]))
        setattr(cls, "CL:0002319",
            PermissibleValue(
                text="CL:0002319",
                description="A cell that is part of the nervous system.",
                meaning=CL["0002319"]))
        setattr(cls, "CL:0011113",
            PermissibleValue(
                text="CL:0011113",
                description="Neuron found in the spiral ganglion.",
                meaning=CL["0011113"]))
        setattr(cls, "CL:0000662",
            PermissibleValue(
                text="CL:0000662",
                meaning=CL["0000662"]))
        setattr(cls, "CL:0002292",
            PermissibleValue(
                text="CL:0002292",
                description="""A round or oval neuroepithelial cell that contacts other type I cells or capillaries. They occur in clusters that are surrounded by sheath cells (type-II cells) in the carotid body. This cell type is capable of secreting a number of neurotransmitters.""",
                meaning=CL["0002292"]))
        setattr(cls, "CL:4052051",
            PermissibleValue(
                text="CL:4052051",
                description="""​​A uterine natural killer subset that is present in the endometrial lining during the non-pregnant state (Garcia-Alonso et al., 2021) and in the decidua during pregnancy (Vento-Tormo et al., 2018). It expresses the uterine resident marker CD49a and is distinguished from uNK2 and uNK3 by CD39 expression and the absence of CD103 (Whettlock et al., 2022) and CD160 (Marečková et al., 2024). It also expresses higher levels of killer-cell immunoglobulin-like receptors (KIRs) and leukocyte immunoglobulin-like receptor B1 (LILRB1), which facilitate interaction with human leukocyte antigens (HLAs) on extravillous trophoblast cells, promoting immune tolerance and implantation. Enriched in the endometrium post-ovulation (Marečková et al., 2024) and prominent in early pregnancy (Whettlock et al., 2022), uNK1 regulates trophoblast invasion and spiral artery remodeling (Zhang & Wei, 2021).""",
                meaning=CL["4052051"]))
        setattr(cls, "CL:0000067",
            PermissibleValue(
                text="CL:0000067",
                description="An epithelial cell that has a cilia.",
                meaning=CL["0000067"]))
        setattr(cls, "CL:0002181",
            PermissibleValue(
                text="CL:0002181",
                description="""A columnar epithelial mucous secreting cell located in the neck of the gastric glands. These cells have numerous apical secretory vesicles containing mucins and a basally displaced nucleus. The mucous they secrete is distinct histochemically from that of the surface mucous cells of stomach.""",
                meaning=CL["0002181"]))
        setattr(cls, "CL:4070010",
            PermissibleValue(
                text="CL:4070010",
                description="A motor neuron that moves the medial tooth forward",
                meaning=CL["4070010"]))
        setattr(cls, "CL:0004214",
            PermissibleValue(
                text="CL:0004214",
                description="A type of type 3 cone bipolar cell with distinctive crescent-shaped dendrites.",
                meaning=CL["0004214"]))
        setattr(cls, "CL:0000594",
            PermissibleValue(
                text="CL:0000594",
                description="""An elongated, spindle-shaped, cell that is located between the basal lamina and the plasmalemma of a muscle fiber. These cells are mostly quiescent, but upon activation they divide to produce cells that generate new muscle fibers.""",
                meaning=CL["0000594"]))
        setattr(cls, "CL:0002520",
            PermissibleValue(
                text="CL:0002520",
                description="""An insect excretory cell that regulates hemolymph composition by filtration and filtrate endocytosis.""",
                meaning=CL["0002520"]))
        setattr(cls, "CL:0002627",
            PermissibleValue(
                text="CL:0002627",
                description="A mature astrocyte that is capable of producing cytokines.",
                meaning=CL["0002627"]))
        setattr(cls, "CL:0004225",
            PermissibleValue(
                text="CL:0004225",
                description="""A broadly stratifying amacrine cell with a small dendritic field, straight dendrites and post-synaptic terminals in S1, S2, and S3.""",
                meaning=CL["0004225"]))
        setattr(cls, "CL:0002422",
            PermissibleValue(
                text="CL:0002422",
                description="""A reticulocyte lacking a nucleus and showing a basophilic reticulum under vital staining due to the presence of ribosomes.""",
                meaning=CL["0002422"]))
        setattr(cls, "CL:0000570",
            PermissibleValue(
                text="CL:0000570",
                description="""A neuroepithelial cells that occurs singly or in small groups, close to the outer follicular borders but within the follicular basement membrane of the thyroid. Expresses a form of the neural cell adhesion molecule (N-CAM) on their surface. Secretes calcitonin, 5-hydroxytryptamine and dopamine.""",
                meaning=CL["0000570"]))
        setattr(cls, "CL:0000599",
            PermissibleValue(
                text="CL:0000599",
                description="""An asexual, nonmotile spore formed by higher fungi; conidia are usually made from the side or tip of specialized sporogenous cells and do not form by progressive cleavage of the cytoplasm.""",
                meaning=CL["0000599"]))
        setattr(cls, "CL:0002570",
            PermissibleValue(
                text="CL:0002570",
                description="A mesenchymal stem cell of adipose tissue.",
                meaning=CL["0002570"]))
        setattr(cls, "CL:0000499",
            PermissibleValue(
                text="CL:0000499",
                description="A connective tissue cell of an organ found in the loose connective tissue.",
                meaning=CL["0000499"]))
        setattr(cls, "CL:0000077",
            PermissibleValue(
                text="CL:0000077",
                description="""A flat, squamous-like epithelial cell of mesodermal origin. It forms the mesothelium, which lines the body's serous cavities including the pleural, peritoneal, and pericardial spaces. This cell plays a crucial role in synthesizing and secreting lubricants, such as glycosaminoglycans and surfactants, which minimize friction between adjacent tissues during movement.""",
                meaning=CL["0000077"]))
        setattr(cls, "CL:1000337",
            PermissibleValue(
                text="CL:1000337",
                description="An enterocyte that is part of the epithelium of duodenal gland.",
                meaning=CL["1000337"]))
        setattr(cls, "CL:0002283",
            PermissibleValue(
                text="CL:0002283",
                description="An epithelial cell of the mucosa associated with facial skeleton.",
                meaning=CL["0002283"]))
        setattr(cls, "CL:0002457",
            PermissibleValue(
                text="CL:0002457",
                description="""A Langerhans cell that is in the epidermis and is CD45-positive, MHCII-positive, and CD11b-positive.""",
                meaning=CL["0002457"]))
        setattr(cls, "CL:0002556",
            PermissibleValue(
                text="CL:0002556",
                description="A fibroblast of the periodontium.",
                meaning=CL["0002556"]))
        setattr(cls, "CL:0002155",
            PermissibleValue(
                text="CL:0002155",
                description="""A crenated erythrocyte with 30+ crenations, bumps or spurs that are the result of damage due to age or disease.""",
                meaning=CL["0002155"]))
        setattr(cls, "CL:0002406",
            PermissibleValue(
                text="CL:0002406",
                description="""A double negative post-natal thymocyte that has a T cell receptor consisting of a gamma chain containing a Vgamma2 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-positive.""",
                meaning=CL["0002406"]))
        setattr(cls, "CL:0001072",
            PermissibleValue(
                text="CL:0001072",
                description="""An innate lymphoid cell in the human with the phenotype CD34-negative, CD117-positive, and a precusor to NK cells, ILC2 cells, and ILC3 cells.""",
                meaning=CL["0001072"]))
        setattr(cls, "CL:0009035",
            PermissibleValue(
                text="CL:0009035",
                description="A stromal cell found in the lamina propria of the vermiform appendix.",
                meaning=CL["0009035"]))
        setattr(cls, "CL:0000109",
            PermissibleValue(
                text="CL:0000109",
                meaning=CL["0000109"]))
        setattr(cls, "CL:0000518",
            PermissibleValue(
                text="CL:0000518",
                description="A phagocyte in vertebrates that is able to phagocytosis.",
                meaning=CL["0000518"]))
        setattr(cls, "CL:4023010",
            PermissibleValue(
                text="CL:4023010",
                description="""A GABAergic cortical interneuron that is strongly labelled for α7 nAChRs. These cells have soma found in L1 and have multipolar dendrites with vertically descending axonal collaterals that project deep into the column, usually branching and terminating in L5A.""",
                meaning=CL["4023010"]))
        setattr(cls, "CL:1001428",
            PermissibleValue(
                text="CL:1001428",
                description="A urothelial cell that is part of the urothelium of the urinary bladder.",
                meaning=CL["1001428"]))
        setattr(cls, "CL:0000611",
            PermissibleValue(
                text="CL:0000611",
                description="""Any granulocytopoietic cell that has part some transcription factor PU.1 and has part some CCAAT/enhancer-binding protein alpha and has part some erythroid transcription factor and lacks plasma membrane part some CD19 molecule and lacks plasma membrane part some CD4 molecule and lacks plasma membrane part some integrin alpha-M and lacks plasma membrane part some CD3 epsilon and lacks plasma membrane part some neural cell adhesion molecule 1 and lacks plasma membrane part some CD2 molecule and lacks plasma membrane part some T-cell surface glycoprotein CD8 alpha chain and lacks plasma membrane part some membrane-spanning 4-domains subfamily A member 1 and lacks plasma membrane part some T-cell surface glycoprotein CD5 and lacks plasma membrane part some CD14 molecule and lacks plasma membrane part some lymphocyte antigen 6G and lacks plasma membrane part some lymphocyte antigen 76 (mouse) and has plasma membrane part some CD34 molecule and has plasma membrane part some ADP-ribosyl cyclase/cyclic ADP-ribose hydrolase 1 and has plasma membrane part some interleukin-3 receptor class 2 alpha chain and has plasma membrane part some interleukin-5 receptor subunit alpha and has plasma membrane part some mast/stem cell growth factor receptor and is capable of some eosinophil differentiation.""",
                meaning=CL["0000611"]))
        setattr(cls, "CL:4042021",
            PermissibleValue(
                text="CL:4042021",
                description="""A progenitor cell of the central nervous system that differentiates exclusively onto neurons. This progenitor cell is found in a hippocampus subventricular zone, developing cortex and spinal cord of the central nervous system.""",
                meaning=CL["4042021"]))
        setattr(cls, "CL:1000597",
            PermissibleValue(
                text="CL:1000597",
                description="A cell that is part of a tip of a renal papilla.",
                meaning=CL["1000597"]))
        setattr(cls, "CL:4052009",
            PermissibleValue(
                text="CL:4052009",
                description="""A subepithelial intestinal fibroblast that is located adjacent to the top of the crypt of Lieberkuhn. Characterized by high experession of PDGFRα, this cell secretes a range of signaling factors, including WNTs and BMPs, that drive epithelial differentiation, creating a gradient that regulates the balance between stem cell maintenance and differentiation.""",
                meaning=CL["4052009"]))
        setattr(cls, "CL:0000198",
            PermissibleValue(
                text="CL:0000198",
                description="""The peripheral receptor for pain. Includes receptors which are sensitive to painful mechanical stimuli, extreme heat or cold, and chemical stimuli. All mammalian nociceptors are free nerve endings.""",
                meaning=CL["0000198"]))
        setattr(cls, "CL:0002622",
            PermissibleValue(
                text="CL:0002622",
                description="A stromal cell of the prostate.",
                meaning=CL["0002622"]))
        setattr(cls, "CL:0000759",
            PermissibleValue(
                text="CL:0000759",
                description="""An ON-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the inner half of the inner plexiform layer. The axon terminal is narrowly stratified and are found just below a calretinin-expressing band in sublamina 4 of the inner plexiform layer.""",
                meaning=CL["0000759"]))
        setattr(cls, "CL:0002342",
            PermissibleValue(
                text="CL:0002342",
                description="""A circulating endothelial cell of the phenotype CD146-positive, CD105-positive, CD45-negative. This cell type is indicative of recent vascular damage.""",
                meaning=CL["0002342"]))
        setattr(cls, "CL:0000357",
            PermissibleValue(
                text="CL:0000357",
                meaning=CL["0000357"]))
        setattr(cls, "CL:1000368",
            PermissibleValue(
                text="CL:1000368",
                description="""A transitional myocyte that is part of the anterior division of left branch of atrioventricular bundle.""",
                meaning=CL["1000368"]))
        setattr(cls, "CL:0005025",
            PermissibleValue(
                text="CL:0005025",
                description="""A motor neuron that synapses to parasympathetic neurons that innervate tear glands, sweat glands, and the smooth muscles and glands of the pulmonary, cardiovascular, and gastrointestinal systems.""",
                meaning=CL["0005025"]))
        setattr(cls, "CL:1000279",
            PermissibleValue(
                text="CL:1000279",
                description="A smooth muscle cell that is part of the large intestine.",
                meaning=CL["1000279"]))
        setattr(cls, "CL:0002140",
            PermissibleValue(
                text="CL:0002140",
                description="""An acinar cell that is part of a skin sebaceous gland. This cell produces and secretes sebum into hair follicles.""",
                meaning=CL["0002140"]))
        setattr(cls, "CL:1000376",
            PermissibleValue(
                text="CL:1000376",
                description="A Purkinje myocyte that is part of the interventricular septum.",
                meaning=CL["1000376"]))
        setattr(cls, "CL:2000085",
            PermissibleValue(
                text="CL:2000085",
                description="Any mononuclear cell that is part of a umbilical cord.",
                meaning=CL["2000085"]))
        setattr(cls, "CL:0000775",
            PermissibleValue(
                text="CL:0000775",
                description="""Any of the immature or mature forms of a granular leukocyte that in its mature form has a nucleus with three to five lobes connected by slender threads of chromatin, and cytoplasm containing fine inconspicuous granules and stainable by neutral dyes.""",
                meaning=CL["0000775"]))
        setattr(cls, "CL:0000748",
            PermissibleValue(
                text="CL:0000748",
                description="""A bipolar neuron found in the retina and having connections with photoreceptors cells and neurons in the inner plexiform layer.""",
                meaning=CL["0000748"]))
        setattr(cls, "CL:0002026",
            PermissibleValue(
                text="CL:0002026",
                description="""A megakaryocyte progenitor cell that is CD34-negative, CD41-positive and CD42-positive.""",
                meaning=CL["0002026"]))
        setattr(cls, "CL:0002451",
            PermissibleValue(
                text="CL:0002451",
                description="""A multi-fate stem cell that is the source of cells for growth of the mammary gland during puberty and gestation. This cell type gives rise to both the luminal and myoepithelial cell types of the gland, and have been shown to have the ability to regenerate the entire organ in mice. This cell type also plays an important role in carcinogenesis of the breast. This cell type is Lin-, CD24-positive, CD29-hi.""",
                meaning=CL["0002451"]))
        setattr(cls, "CL:0002404",
            PermissibleValue(
                text="CL:0002404",
                description="A thymocyte found in the fetal thymus.",
                meaning=CL["0002404"]))
        setattr(cls, "CL:4047052",
            PermissibleValue(
                text="CL:4047052",
                description="""An enterocyte of the human colon expressing bestrophin-4 (BEST4) calcium-activated ion channels.  These cells have a distinct transcriptomic profile compared to other enterocytes and are scattered through the colon epithelium.""",
                meaning=CL["4047052"]))
        setattr(cls, "CL:0002243",
            PermissibleValue(
                text="CL:0002243",
                description="""A circular smooth muscle cell of the iris, innervated by the ciliary nerves (parasympathetic), and acting to contract the pupil. This muscle cell derives from neuroectoderm. This smooth muscle cell results from transformation of epithelial cells to smooth muscle cells.""",
                meaning=CL["0002243"]))
        setattr(cls, "CL:0002546",
            PermissibleValue(
                text="CL:0002546",
                description="An endothelial progenitor cell that participates in angiogenesis during development.",
                meaning=CL["0002546"]))
        setattr(cls, "CL:0002493",
            PermissibleValue(
                text="CL:0002493",
                description="""A polarized cell that is juxtaposed to fibrocytes in the underlying spiral ligament. This cell type secretes potassium ions derived from fibrocytes through gap junctions.""",
                meaning=CL["0002493"]))
        setattr(cls, "CL:1001124",
            PermissibleValue(
                text="CL:1001124",
                description="An endothelial cell that is part of the peritubular capillary of the renal cortex.",
                meaning=CL["1001124"]))
        setattr(cls, "CL:0000112",
            PermissibleValue(
                text="CL:0000112",
                description="""A neuron of the invertebrate central nervous system. This neuron innervates the central complex (CX) of an invertebrate brain and it forms columnar patterns with its dendrites. It is involved in navigation and spatial processing.""",
                meaning=CL["0000112"]))
        setattr(cls, "CL:4023123",
            PermissibleValue(
                text="CL:4023123",
                description="""A kisspeptin neuron that is located in the hypothalamus. These neurons project to and activate gonadotrophin-releasing hormone neurons (acting via the kisspeptin receptor) in the hypothalamus and stimulate the secretion of gonadotrophin-releasing hormone.""",
                meaning=CL["4023123"]))
        setattr(cls, "CL:0000352",
            PermissibleValue(
                text="CL:0000352",
                description="""A cell of the outer layer of a blastula that gives rise to the ectoderm after gastrulation.""",
                meaning=CL["0000352"]))
        setattr(cls, "CL:1001109",
            PermissibleValue(
                text="CL:1001109",
                description="""An epithelial cell that is part of some loop of Henle thick ascending limb segment located in the renal cortex.""",
                meaning=CL["1001109"]))
        setattr(cls, "CL:2000095",
            PermissibleValue(
                text="CL:2000095",
                description="Any hematopoietic stem cell that is part of a umbilical cord blood.",
                meaning=CL["2000095"]))
        setattr(cls, "CL:4033056",
            PermissibleValue(
                text="CL:4033056",
                description="""A differentiated flat keratinocyte that is part of a nail plate. An onychocyte is firmly adherent and does not desquamate.""",
                meaning=CL["4033056"]))
        setattr(cls, "CL:0002280",
            PermissibleValue(
                text="CL:0002280",
                description="An enteroendocrine cell found in the ileum and jejunum that produces neurotensin.",
                meaning=CL["0002280"]))
        setattr(cls, "CL:1000465",
            PermissibleValue(
                text="CL:1000465",
                description="A chromaffin cell that is part of the ovary.",
                meaning=CL["1000465"]))
        setattr(cls, "CL:0000889",
            PermissibleValue(
                text="CL:0000889",
                description="""An immature myeloid leukocyte of heterogeneous phenotype found particularly in cancer and sepsis patients that is capable of suppressing activity of T cells in ex vivo assays. This cell type is CD45-positive, CD11b-positive.""",
                meaning=CL["0000889"]))
        setattr(cls, "CL:4042026",
            PermissibleValue(
                text="CL:4042026",
                description="""A GABAergic interneuron that has its soma in the anterior section of the substantia nigra pars reticulata. This GABAergic interneuron is characterized by the expression of Six3 and Foxp1 and it develops from Nkx6-2 expressing neuronal progenitors in the ventrolateral midbrain-diencephalon region.""",
                meaning=CL["4042026"]))
        setattr(cls, "CL:0002008",
            PermissibleValue(
                text="CL:0002008",
                description="""A lineage marker-negative, CD34-positive, CD38-positive, IL3r-alpha-positive, IL5r-alpha-positive, and CD45RA-negative eosinophil progenitor cell.""",
                meaning=CL["0002008"]))
        setattr(cls, "CL:4030033",
            PermissibleValue(
                text="CL:4030033",
                description="""An endothelial cell that lines a surface of a cardiac valve leaflet. Along with valve interstitial cells, a valve endothelial cell maintains tissue homeostasis for the function of cardiac valves through secreting biochemical signals, matrix proteins and matrix remodeling enzymes.""",
                meaning=CL["4030033"]))
        setattr(cls, "CL:0000632",
            PermissibleValue(
                text="CL:0000632",
                description="""A cell that is found in the perisinusoidal space of the liver that is capable of multiple roles including storage of retinol, presentation of antigen to T cells (including CD1d-restricted NKT cells), and upon activation, production of extracellular matrix components that can contribute to liver fibrosis. This activated state has a myofibroblast-like phenotype, though it's not clear in the literature if this is terminally differentiated. This cell type comprises approximately 8-15% of total cells in the liver.""",
                meaning=CL["0000632"]))
        setattr(cls, "CL:0000342",
            PermissibleValue(
                text="CL:0000342",
                description="Any animal cell containing pigment granules.",
                meaning=CL["0000342"]))
        setattr(cls, "CL:0000832",
            PermissibleValue(
                text="CL:0000832",
                description="A myeloblast committed to the eosinophil lineage.",
                meaning=CL["0000832"]))
        setattr(cls, "CL:4042008",
            PermissibleValue(
                text="CL:4042008",
                description="""A cell type located in the first layer of the neocortex with radial protrusions extending transversely into the deeper cortex layers, herby facilitating communication across neurons, astrocytes, capillaries, meninges and cerebrospinal fluid through contact with neurons, pia mater and capillaries.""",
                meaning=CL["4042008"]))
        setattr(cls, "CL:1001451",
            PermissibleValue(
                text="CL:1001451",
                description="""A sensory neuron of the dorsal root ganglia that senses body position and sends information about how much the muscle is stretched to the spinal cord.""",
                meaning=CL["1001451"]))
        setattr(cls, "CL:0002607",
            PermissibleValue(
                text="CL:0002607",
                description="A neural crest cell that gives rise to cells of the enteric nervous system.",
                meaning=CL["0002607"]))
        setattr(cls, "CL:4033062",
            PermissibleValue(
                text="CL:4033062",
                description="""A trophoblast cell that invades the uterine wall to anchor the placenta to the uterus. An interstitial extravillous trophoblast cell differentiates from an extravillous trophoblast cell, becoming hyperchromatic and changing its morphology to a fibroblast-like spindle-shaped cell. In humans, this cell can be distinguished by the expression of placental-specific protein 8, which stimulates migration.""",
                meaning=CL["4033062"]))
        setattr(cls, "CL:1000437",
            PermissibleValue(
                text="CL:1000437",
                description="An epithelial cell that is part of the nasolacrimal duct.",
                meaning=CL["1000437"]))
        setattr(cls, "CL:0011106",
            PermissibleValue(
                text="CL:0011106",
                description="""A type of interneuron in the retinal inner nuclear layer which carries information from the inner plexiform layer and the outer plexiform layer using GABA.""",
                meaning=CL["0011106"]))
        setattr(cls, "CL:1000312",
            PermissibleValue(
                text="CL:1000312",
                description="A goblet cell that is part of the epithelium of bronchus.",
                meaning=CL["1000312"]))
        setattr(cls, "CL:1000327",
            PermissibleValue(
                text="CL:1000327",
                description="A goblet cell that is part of the epithelium proper of appendix.",
                meaning=CL["1000327"]))
        setattr(cls, "CL:0008048",
            PermissibleValue(
                text="CL:0008048",
                description="""A glutamatergic motor neuron with a soma in the brainstem or cerebral cortex.  They do not synapse directly to muscles but rather to lower motor neurons, which do.  They are the main controllers of voluntary movement.""",
                meaning=CL["0008048"]))
        setattr(cls, "CL:0000857",
            PermissibleValue(
                text="CL:0000857",
                description="A skeletal muscle myoblast that differentiates into slow muscle fibers.",
                meaning=CL["0000857"]))
        setattr(cls, "CL:1000239",
            PermissibleValue(
                text="CL:1000239",
                description="Any glial cell that is part of some anterior lateral line nerve.",
                meaning=CL["1000239"]))
        setattr(cls, "CL:0002329",
            PermissibleValue(
                text="CL:0002329",
                description="""An epithelial cell type that lacks the columnar shape typical for other respiratory epithelial cells. This cell type is able to differentiate into other respiratory epithelial cells in response to injury.""",
                meaning=CL["0002329"]))
        setattr(cls, "CL:0004230",
            PermissibleValue(
                text="CL:0004230",
                description="""A bistratified amacrine cell with a small dendritic field that has post-synaptic terminals in S1 and the border of S1-S2, and termination of a second arbor within the border of S2-S3 and S3.""",
                meaning=CL["0004230"]))
        setattr(cls, "CL:0002144",
            PermissibleValue(
                text="CL:0002144",
                description="An endothelial cell found in capillaries.",
                meaning=CL["0002144"]))
        setattr(cls, "CL:1001021",
            PermissibleValue(
                text="CL:1001021",
                description="""Any kidney loop of Henle epithelial cell that is part of some descending limb of loop of Henle.""",
                meaning=CL["1001021"]))
        setattr(cls, "CL:0008010",
            PermissibleValue(
                text="CL:0008010",
                description="""A cranial motor neuron whose soma is located in the midbrain andor hindbrain and which innervates the skeletal muscles of the eye or tongue.""",
                meaning=CL["0008010"]))
        setattr(cls, "CL:0002118",
            PermissibleValue(
                text="CL:0002118",
                description="""A CD38-negative IgG-negative memory B cell is a IgG-negative class switched memory B cell that lacks IgG on the cell surface with the phenotype CD38-negative and IgG-negative.""",
                meaning=CL["0002118"]))
        setattr(cls, "CL:4033075",
            PermissibleValue(
                text="CL:4033075",
                description="A(n) CD4-positive, alpha-beta T cell that is cycling.",
                meaning=CL["4033075"]))
        setattr(cls, "CL:4023064",
            PermissibleValue(
                text="CL:4023064",
                description="An interneuron that is derived from the caudal ganglionic eminence.",
                meaning=CL["4023064"]))
        setattr(cls, "CL:0000878",
            PermissibleValue(
                text="CL:0000878",
                description="A tissue-resident macrophage found in the central nervous system.",
                meaning=CL["0000878"]))
        setattr(cls, "CL:0009051",
            PermissibleValue(
                text="CL:0009051",
                description="A T cell that is located in the anorectum.",
                meaning=CL["0009051"]))
        setattr(cls, "CL:0019001",
            PermissibleValue(
                text="CL:0019001",
                description="Any serous secreting cell that is part of the tracheobronchial epithelium.",
                meaning=CL["0019001"]))
        setattr(cls, "CL:4042019",
            PermissibleValue(
                text="CL:4042019",
                description="""A type of tanycyte located in ventral part of the lateral wall of the third ventricle and in the lateral infundibular recess of the brain. This tanycyte has an elongated morphology with multiple microvilli extending into the median eminence. This type of tanycyte expresses FGF receptors 1 and 2, is in contact with GnRH neurons, and is involved in the release of gonadotropin-releasing hormone (GnRH).""",
                meaning=CL["4042019"]))
        setattr(cls, "CL:1001100",
            PermissibleValue(
                text="CL:1001100",
                description="Any smooth muscle cell that is part of some renal efferent arteriole.",
                meaning=CL["1001100"]))
        setattr(cls, "CL:0002571",
            PermissibleValue(
                text="CL:0002571",
                description="A mesenchymal stem cell of liver.",
                meaning=CL["0002571"]))
        setattr(cls, "CL:0008035",
            PermissibleValue(
                text="CL:0008035",
                description="""Any vascular associated smooth muscle cell that is part of some microcirculatory vessel.""",
                meaning=CL["0008035"]))
        setattr(cls, "CL:0003045",
            PermissibleValue(
                text="CL:0003045",
                description="""A bistratified ganglion cell with larger, asymetric dendritic fields that terminate in S2 and S4.""",
                meaning=CL["0003045"]))
        setattr(cls, "CL:0002666",
            PermissibleValue(
                text="CL:0002666",
                description="""An otic fibrocyte that underlies the spiral prominence and is part of a mesenchymal gap junction network that regulates ionic homeostasis of the endolymph.""",
                meaning=CL["0002666"]))
        setattr(cls, "CL:4023044",
            PermissibleValue(
                text="CL:4023044",
                description="""An extratelencephalic-projecting glutamatergic neuron located in layer 5b of the primary motor cortex that does not project to the medulla. Non-MY ET cells are large, big-tufted cells with the apical dendrite often bifurcating close to the soma, suggesting they are corticospinal cells. Non-MY ET cells have bigger hyperpolarization sag, lower input resistance, and smaller AP width, compared to L5 IT neurons.""",
                meaning=CL["4023044"]))
        setattr(cls, "CL:0002085",
            PermissibleValue(
                text="CL:0002085",
                description="""A specialized elongated ventricular ependymal cell with one or more processes that extend into the brain parenchyma or associated blood vessels where they contact blood vessel endothelial cells and/or neurons. These cells are found in the ventricles and circumventricular organs of the brain. They are involved in hormonal regulation, gatekeeping molecules between the bloodstream and cerebrospinal fluid, metabolic sensing, and regulating food intake.""",
                meaning=CL["0002085"]))
        setattr(cls, "CL:1001142",
            PermissibleValue(
                text="CL:1001142",
                description="Any kidney cortex vein cell that is part of some kidney arcuate vein.",
                meaning=CL["1001142"]))
        setattr(cls, "CL:0002661",
            PermissibleValue(
                text="CL:0002661",
                description="""A luminal cell of terminal ducts, i.e.e the terminal branch of a lactiferous duct which alveolar cells drain into.""",
                meaning=CL["0002661"]))
        setattr(cls, "CL:4033083",
            PermissibleValue(
                text="CL:4033083",
                description="""A granulosa cell that has a squamous morphology and form a single layer around the oocyte in primordial follicles. This cell develops directly into a cuboidal granulosa cell during the primordial-to-primary follicle transition.""",
                meaning=CL["4033083"]))
        setattr(cls, "CL:0000146",
            PermissibleValue(
                text="CL:0000146",
                meaning=CL["0000146"]))
        setattr(cls, "CL:4052029",
            PermissibleValue(
                text="CL:4052029",
                description="""A fibroblast that is located beneath the visceral pleura of the lung. This cell contributes to the development of idiopathic pulmonary fibrosis (IPF) by forming fibrotic lesions that originate subpleurally and extend into lung tissue through activation, proliferation, migration, and differentiation into a myofibroblast.""",
                meaning=CL["4052029"]))
        setattr(cls, "CL:0002089",
            PermissibleValue(
                text="CL:0002089",
                description="""A group 2 innate lymphoid cell in the mouse capable of secreting IL-13 in response to a helminth infection. This cell is lineage-negative, ICOS-positive, IL1RL1-positive, IL7Ralpha-positive, and IL17Br-positive.""",
                meaning=CL["0002089"]))
        setattr(cls, "CL:0000507",
            PermissibleValue(
                text="CL:0000507",
                description="A peptide hormone secreting cell that secretes endorphin.",
                meaning=CL["0000507"]))
        setattr(cls, "CL:0000246",
            PermissibleValue(
                text="CL:0000246",
                meaning=CL["0000246"]))
        setattr(cls, "CL:0002016",
            PermissibleValue(
                text="CL:0002016",
                description="A polychromatiic erythroblast that is Gly-A-positive and CD71-low.",
                meaning=CL["0002016"]))
        setattr(cls, "CL:0002526",
            PermissibleValue(
                text="CL:0002526",
                description="A dermal dendritic cell that is CD1a-negative and CD14-positive.",
                meaning=CL["0002526"]))
        setattr(cls, "CL:0002514",
            PermissibleValue(
                text="CL:0002514",
                description="""A CD8-alpha alpha positive gamma-delta intraepithelial T cell that does not express a TCR partially encoded by the Vgamma5 gene segment.""",
                meaning=CL["0002514"]))
        setattr(cls, "CL:0011102",
            PermissibleValue(
                text="CL:0011102",
                description="""Parasympathetic neurons are part of the parasympathetic nervous sysem and the cell bodies lie in the brain and sacral region of the spinal cord. The neurons are mainly cholinergic.""",
                meaning=CL["0011102"]))
        setattr(cls, "CL:4033094",
            PermissibleValue(
                text="CL:4033094",
                description="""A transcriptionally distinct memory B cell whose presence increases with age, during infections, and in autoimmune diseases. In humans and mice, this cell type can be identified by the expression of T-bet, CD11c, CD11b, and the lack of CD21. An age-associated B cell responds to TLR stimuli, may produce autoantibodies, and participates in antiviral responses and pathogen clearance.""",
                meaning=CL["4033094"]))
        setattr(cls, "CL:0004232",
            PermissibleValue(
                text="CL:0004232",
                description="""An amacrine cell with a flat dendritic arbor and a medium dendritic field. Starburst amacrine cells have post-synaptic terminals in S2. This cell type releases the neurotransmitters gamma-aminobutyric acid (GABA) and acetylcholine.""",
                meaning=CL["0004232"]))
        setattr(cls, "CL:0001006",
            PermissibleValue(
                text="CL:0001006",
                description="""Dermal dendritic cell is a conventional dendritic cell that is CD11b-positive, CD205-positive and CD8 alpha-negative.""",
                meaning=CL["0001006"]))
        setattr(cls, "CL:0009081",
            PermissibleValue(
                text="CL:0009081",
                description="""The human equivalent of a DN2 thymocyte; typically contains two phases, in the latter of which these thymocytes begin the process of beta selection.""",
                meaning=CL["0009081"]))
        setattr(cls, "CL:0008004",
            PermissibleValue(
                text="CL:0008004",
                description="A muscle cell that is part of some somatic muscle.",
                meaning=CL["0008004"]))
        setattr(cls, "CL:1001582",
            PermissibleValue(
                text="CL:1001582",
                description="Neuron of lateral ventricle.",
                meaning=CL["1001582"]))
        setattr(cls, "CL:1000350",
            PermissibleValue(
                text="CL:1000350",
                description="A basal cell that is part of the epithelium of terminal bronchiole.",
                meaning=CL["1000350"]))
        setattr(cls, "CL:0000416",
            PermissibleValue(
                text="CL:0000416",
                meaning=CL["0000416"]))
        setattr(cls, "CL:0000199",
            PermissibleValue(
                text="CL:0000199",
                description="""A cell specialized to transduce mechanical stimuli and relay that information centrally in the nervous system.""",
                meaning=CL["0000199"]))
        setattr(cls, "CL:0000208",
            PermissibleValue(
                text="CL:0000208",
                meaning=CL["0000208"]))
        setattr(cls, "CL:1000271",
            PermissibleValue(
                text="CL:1000271",
                description="""An epithelial cell that is part of the lung epithelium. This cell is characterised by the presence of cilia on its apical surface.""",
                meaning=CL["1000271"]))
        setattr(cls, "CL:0000421",
            PermissibleValue(
                text="CL:0000421",
                description="""A free floating cell, including amebocytes and eleocytes, in the coelom of certain animals, especially annelids.""",
                meaning=CL["0000421"]))
        setattr(cls, "CL:2000043",
            PermissibleValue(
                text="CL:2000043",
                description="Any pericyte cell that is part of a brain.",
                meaning=CL["2000043"]))
        setattr(cls, "CL:0002606",
            PermissibleValue(
                text="CL:0002606",
                description="An astrocyte of the spinal cord.",
                meaning=CL["0002606"]))
        setattr(cls, "CL:0000214",
            PermissibleValue(
                text="CL:0000214",
                description="A cell located in the synovial joint.",
                meaning=CL["0000214"]))
        setattr(cls, "CL:0000605",
            PermissibleValue(
                text="CL:0000605",
                description="A spore formed following mitosis or mitoses.",
                meaning=CL["0000605"]))
        setattr(cls, "CL:0001087",
            PermissibleValue(
                text="CL:0001087",
                description="""A CD4-positive, alpha beta memory T cell with the phenotype CD45RA-positive, CD45RO-negative, and CCR7-negative.""",
                meaning=CL["0001087"]))
        setattr(cls, "CL:0002096",
            PermissibleValue(
                text="CL:0002096",
                description="""A specialised myocyte that lies between the sinoatrial node and the atrioventricular node and is involved in the conduction of electrical signals.""",
                meaning=CL["0002096"]))
        setattr(cls, "CL:1000493",
            PermissibleValue(
                text="CL:1000493",
                description="A mesothelial cell that is part of the visceral pleura.",
                meaning=CL["1000493"]))
        setattr(cls, "CL:0002478",
            PermissibleValue(
                text="CL:0002478",
                description="""An adipose macrophage that does not express F4/80but is MHC-II-positive. This cell type exhibits autofluorescence under typical flow cyometry conditions.""",
                meaning=CL["0002478"]))
        setattr(cls, "CL:4033013",
            PermissibleValue(
                text="CL:4033013",
                description="""A keratinocyte of the epidermis suprabasal layer. This cell may express the differentiation markers keratin 10 and keratin 1.""",
                meaning=CL["4033013"]))
        setattr(cls, "CL:4033048",
            PermissibleValue(
                text="CL:4033048",
                description="""A respiratory epithelial cell derived from a basal cell, with a topographic nuclear position between the basal and luminal cells of the airway epithelium. This non-basal, intermediate progenitor cell has limited proliferative capacity and can differentiate into multiciliated, secretory, or rare airway cells (ionocytes, tuft cells, neuroendocrine cells). It shares some ultrastructural features with basal cells but lacks the defined characteristics of fully differentiated cellular phenotypes.""",
                meaning=CL["4033048"]))
        setattr(cls, "CL:1000428",
            PermissibleValue(
                text="CL:1000428",
                description="A somatic stem cell that is part of the epidermis.",
                meaning=CL["1000428"]))
        setattr(cls, "CL:4030013",
            PermissibleValue(
                text="CL:4030013",
                description="""Epithelial cell of the descending thin limb of the long loop (juxtamedullary) nephron that spans the outer medulla (inner stripe). It is known in some mammalian species that the long descending limb of the loop of Henle in the outer medulla selectively expresses the secreted activin-antagonist protein follistatin (Fst), the GPI-linked adhesion protein Cdh13, and the protein kinase Stk32a.""",
                meaning=CL["4030013"]))
        setattr(cls, "CL:0000019",
            PermissibleValue(
                text="CL:0000019",
                description="A mature male germ cell that develops from a spermatid.",
                meaning=CL["0000019"]))
        setattr(cls, "CL:0002228",
            PermissibleValue(
                text="CL:0002228",
                description="""An elongating cell that rapidly obliterates the lumen of the lens vesicle. Subsequently, differentiation of this cell type at the lens equator leads to the formation of secondary fiber cells that come to overlie the primary fibers.""",
                meaning=CL["0002228"]))
        setattr(cls, "CL:4028006",
            PermissibleValue(
                text="CL:4028006",
                description="""A pulmonary interstitial fibroblast that is part of the alveolus and localizes to vascular adventitia.""",
                meaning=CL["4028006"]))
        setattr(cls, "CL:0002129",
            PermissibleValue(
                text="CL:0002129",
                description="Regular cardiac myocyte of a cardiac atrium.",
                meaning=CL["0002129"]))
        setattr(cls, "CL:0001021",
            PermissibleValue(
                text="CL:0001021",
                description="""A common lymphoid progenitor that is CD10-positive, CD45RA-positive, CD34-positive and CD38-positive.""",
                meaning=CL["0001021"]))
        setattr(cls, "CL:1001610",
            PermissibleValue(
                text="CL:1001610",
                description="""Hematopoietic cells resident in the bone marrow. Include: hematopoietic stem cells (lymphoid stem cells and myeloid stem cells) and the precursor cells for thrombocytes, erythrocytes, basophils, neutrophils, eosinophils, monocytes and lymphocytes.""",
                meaning=CL["1001610"]))
        setattr(cls, "CL:4033086",
            PermissibleValue(
                text="CL:4033086",
                description="""A tissue-resident macrophage that is associated with lipids. This cell responsible of anti-inflammatory functions, lipid accumulation and enhancing phagocytosis (Wculek et al., 2022, Liu et al., 2022). In mice and humans, a lipid-associated macrophage is characterized by the marker Trem2 (Jaitlin et al., 2019).""",
                meaning=CL["4033086"]))
        setattr(cls, "CL:1000909",
            PermissibleValue(
                text="CL:1000909",
                description="Any nephron tubule epithelial cell that is part of some loop of Henle.",
                meaning=CL["1000909"]))
        setattr(cls, "CL:0000410",
            PermissibleValue(
                text="CL:0000410",
                meaning=CL["0000410"]))
        setattr(cls, "CL:4023025",
            PermissibleValue(
                text="CL:4023025",
                description="""A sst GABAergic cortical interneuron that is both an interneuron and a projecting neuron. They are found in all layers from upper L2/3 down to the bottom of L6. They have long-range projections, some with axons fading into white matter. These cells have low rebound potential, low hyperpolarization sag, and high variability in membrane time constant.""",
                meaning=CL["4023025"]))
        setattr(cls, "CL:0000130",
            PermissibleValue(
                text="CL:0000130",
                meaning=CL["0000130"]))
        setattr(cls, "CL:0000864",
            PermissibleValue(
                text="CL:0000864",
                description="""A macrophage constitutively resident in a particular tissue under non-inflammatory conditions, and capable of phagocytosing a variety of extracellular particulate material, including immune complexes, microorganisms, and dead cells.""",
                meaning=CL["0000864"]))
        setattr(cls, "CL:0000048",
            PermissibleValue(
                text="CL:0000048",
                description="A stem cell that can give rise to multiple lineages of cells.",
                meaning=CL["0000048"]))
        setattr(cls, "CL:0002357",
            PermissibleValue(
                text="CL:0002357",
                description="""A fetal liver derived enucleated erythrocyte. This erythrocyte resembles adult erythrocytes in that they are small (3- to 6- times smaller than primitive erythrocytes) and produce adult hemaglobins.""",
                meaning=CL["0002357"]))
        setattr(cls, "CL:4033090",
            PermissibleValue(
                text="CL:4033090",
                description="""A granulosa cell that is undergoing atresia. This cell type displays distinct morphological alterations compared with a healthy granulosa cell, including pyknosis (nuclear condensation) and cellular shrinkage.""",
                meaning=CL["4033090"]))
        setattr(cls, "CL:0002560",
            PermissibleValue(
                text="CL:0002560",
                description="An epithelial cell that resides in the inner root sheath of the hair follicle.",
                meaning=CL["0002560"]))
        setattr(cls, "CL:0000964",
            PermissibleValue(
                text="CL:0000964",
                description="""A germinal center B cell that founds a germinal center, and has the phenotype IgD-positive, CD38-positive, and CD23-negative.""",
                meaning=CL["0000964"]))
        setattr(cls, "CL:0009005",
            PermissibleValue(
                text="CL:0009005",
                description="Any cell in a salivary gland.",
                meaning=CL["0009005"]))
        setattr(cls, "CL:0000483",
            PermissibleValue(
                text="CL:0000483",
                description="A peptide hormone secreting cell that secretes bombesin stimulating hormone.",
                meaning=CL["0000483"]))
        setattr(cls, "CL:0000185",
            PermissibleValue(
                text="CL:0000185",
                description="""Contractile cells resembling smooth muscle cells that are present in glands, notably the mammary gland, and aid in secretion. This cell has long weaving dendritic processes containing myofilament.""",
                meaning=CL["0000185"]))
        setattr(cls, "CL:0000956",
            PermissibleValue(
                text="CL:0000956",
                description="""A pre-B-I cell is a precursor B cell that expresses CD34 and surrogate immunoglobulin light chain (VpreB , Lambda 5 (mouse)/14.1 (human)) on the cell surface, and TdT, Rag1,and Rag2 intracellularly. Cell type carries a D-JH DNA rearrangement, and lacks expression of immunglobulin heavy chain protein.""",
                meaning=CL["0000956"]))
        setattr(cls, "CL:4030049",
            PermissibleValue(
                text="CL:4030049",
                description="A DRD2-expressing medium spiny neuron that is part of a striosome of dorsal striatum.",
                meaning=CL["4030049"]))
        setattr(cls, "CL:0002326",
            PermissibleValue(
                text="CL:0002326",
                description="""A mammary epithelial cell that occurs in the lumen of the ductal and alveoli structure in the breast.""",
                meaning=CL["0002326"]))
        setattr(cls, "CL:0000028",
            PermissibleValue(
                text="CL:0000028",
                meaning=CL["0000028"]))
        setattr(cls, "CL:0000847",
            PermissibleValue(
                text="CL:0000847",
                description="""An olfactory receptor cell in which the apical ending of the dendrite is a pronounced ciliated olfactory knob.""",
                meaning=CL["0000847"]))
        setattr(cls, "CL:1000323",
            PermissibleValue(
                text="CL:1000323",
                description="A goblet cell that is part of the epithelium of pyloric gland.",
                meaning=CL["1000323"]))
        setattr(cls, "CL:0010006",
            PermissibleValue(
                text="CL:0010006",
                description="Any blood vessel endothelial cell that is part of some heart.",
                meaning=CL["0010006"]))
        setattr(cls, "CL:4033018",
            PermissibleValue(
                text="CL:4033018",
                description="A megakaryocyte that is resident in the lung connective tissue.",
                meaning=CL["4033018"]))
        setattr(cls, "CL:1000182",
            PermissibleValue(
                text="CL:1000182",
                description="Any tip cell that is part of some Malpighian tubule.",
                meaning=CL["1000182"]))
        setattr(cls, "CL:0000233",
            PermissibleValue(
                text="CL:0000233",
                description="""A non-nucleated disk-shaped cell formed by extrusion from megakaryocytes, found in the blood of all mammals, and mainly involved in blood coagulation.""",
                meaning=CL["0000233"]))
        setattr(cls, "CL:1001567",
            PermissibleValue(
                text="CL:1001567",
                description="Any endothelial cell of vascular tree that is part of some lung.",
                meaning=CL["1001567"]))
        setattr(cls, "CL:0000443",
            PermissibleValue(
                text="CL:0000443",
                description="Any secretory cell that is capable of some calcitonin secretion.",
                meaning=CL["0000443"]))
        setattr(cls, "CL:0000474",
            PermissibleValue(
                text="CL:0000474",
                description="""An insect renal cell that filters hemolymph and is found with other pericardial nephrocytes in two rows flanking the dorsal vessel.""",
                meaning=CL["0000474"]))
        setattr(cls, "CL:4023168",
            PermissibleValue(
                text="CL:4023168",
                description="""A neuron that is part of the somatic sensory system. Somatosensory neurons innervate the skin or integument to detect different types of thermal, chemical, and mechanical touch stimuli.""",
                meaning=CL["4023168"]))
        setattr(cls, "CL:0000204",
            PermissibleValue(
                text="CL:0000204",
                meaning=CL["0000204"]))
        setattr(cls, "CL:1000478",
            PermissibleValue(
                text="CL:1000478",
                description="A transitional myocyte that is part of the sinoatrial node.",
                meaning=CL["1000478"]))
        setattr(cls, "CL:0000557",
            PermissibleValue(
                text="CL:0000557",
                description="""A hematopoietic progenitor cell that is committed to the granulocyte and monocyte lineages. These cells are CD123-positive, and do not express Gata1 or Gata2 but do express C/EBPa, and Pu.1.""",
                meaning=CL["0000557"]))
        setattr(cls, "CL:0002456",
            PermissibleValue(
                text="CL:0002456",
                description="A CD11c-low plasmacytoid dendritic cell that is CD8-alpha-positive and CD4-positive.",
                meaning=CL["0002456"]))
        setattr(cls, "CL:0000501",
            PermissibleValue(
                text="CL:0000501",
                description="""A supporting cell for the developing female gamete in the ovary of mammals. They develop from the coelomic epithelial cells of the gonadal ridge. Granulosa cells form a single layer around the mammalian oocyte in the primordial ovarian follicle and advance to form a multilayered cumulus oophorus surrounding the ovum in the Graafian follicle. The major functions of granulosa cells include the production of steroids and LH receptors.""",
                meaning=CL["0000501"]))
        setattr(cls, "CL:4023075",
            PermissibleValue(
                text="CL:4023075",
                description="""A sst GABAergic cortical interneuron found in L6 that expresses tyrosine hydroxylase. L6 Th+ SST cells have mostly local axonal arborization within L6.""",
                meaning=CL["4023075"]))
        setattr(cls, "CL:0002278",
            PermissibleValue(
                text="CL:0002278",
                description="""An enteroendocrine cell of duodenum and jejunum that produces gastric inhibitory peptide.""",
                meaning=CL["0002278"]))
        setattr(cls, "CL:4033045",
            PermissibleValue(
                text="CL:4033045",
                description="""A dendritic cell that captures antigens in a lung and migrates to a lymph node or to the spleen to activate T cells.""",
                meaning=CL["4033045"]))
        setattr(cls, "CL:1001576",
            PermissibleValue(
                text="CL:1001576",
                description="Squamous cell of oral epithelium.",
                meaning=CL["1001576"]))
        setattr(cls, "CL:1001435",
            PermissibleValue(
                text="CL:1001435",
                description="""The small neuron in the glomerular layer of the olfactory bulb whose dendrites arborize within a glomerulus, where it receives synaptic input from olfactory receptor cell axon terminals, and also engages in dendrodendritic interactions with mitral and tufted cell dendrites; uses both GABA and dopamine as a neurotransmitter.""",
                meaning=CL["1001435"]))
        setattr(cls, "CL:0002681",
            PermissibleValue(
                text="CL:0002681",
                description="A cell that is part of a cortex of kidney.",
                meaning=CL["0002681"]))
        setattr(cls, "CL:0002083",
            PermissibleValue(
                text="CL:0002083",
                description="A chromaffin cell of the adrenal medulla that produces norepinephrine.",
                meaning=CL["0002083"]))
        setattr(cls, "CL:1001123",
            PermissibleValue(
                text="CL:1001123",
                description="""An endothelial cell that is part of the peritubular capillary of the outer renal medulla.""",
                meaning=CL["1001123"]))
        setattr(cls, "CL:0009095",
            PermissibleValue(
                text="CL:0009095",
                description="An endothelial cell that is part of a uterus.",
                meaning=CL["0009095"]))
        setattr(cls, "CL:0001052",
            PermissibleValue(
                text="CL:0001052",
                description="""A CD8-positive, alpha-beta T cell that has the phenotype CXCR3-negative, CCR6-negative.""",
                meaning=CL["0001052"]))
        setattr(cls, "CL:1000304",
            PermissibleValue(
                text="CL:1000304",
                description="A fibroblast that is part of the connective tissue of nonglandular part of prostate.",
                meaning=CL["1000304"]))
        setattr(cls, "CL:0002165",
            PermissibleValue(
                text="CL:0002165",
                description="""A supporting cell that is attached to the basement membrane and forms rows that support the hair cells.""",
                meaning=CL["0002165"]))
        setattr(cls, "CL:1000418",
            PermissibleValue(
                text="CL:1000418",
                description="A myoepithelial cell that is part of the mammary gland alveolus.",
                meaning=CL["1000418"]))
        setattr(cls, "CL:0002489",
            PermissibleValue(
                text="CL:0002489",
                description="A thymocyte that lacks expression of CD4 and CD8.",
                meaning=CL["0002489"]))
        setattr(cls, "CL:0002270",
            PermissibleValue(
                text="CL:0002270",
                description="""A type EC enteroendocrine cell in the duodenum and jejunum that stores and secretes motilin and 5-hydroxytryptamine.""",
                meaning=CL["0002270"]))
        setattr(cls, "CL:4023189",
            PermissibleValue(
                text="CL:4023189",
                description="""A retinal ganglion cell located in the ganglion cell layer of the retina. This cell projects to magnocellular cells in the lateral geniculate nucleus (LGN). They have large cell bodies and extensive, branching dendritic networks that contribute to their large receptive fields.""",
                meaning=CL["4023189"]))
        setattr(cls, "CL:0003042",
            PermissibleValue(
                text="CL:0003042",
                description="""An M9 retinal ganglion cell with synaptic terminals in S4 that is depolarized by decreased illumination of their receptive field center""",
                meaning=CL["0003042"]))
        setattr(cls, "CL:0000901",
            PermissibleValue(
                text="CL:0000901",
                description="CD4-positive alpha-beta T cell with regulatory function that produces IL-10.",
                meaning=CL["0000901"]))
        setattr(cls, "CL:0002107",
            PermissibleValue(
                text="CL:0002107",
                description="""An IgD-negative CD38-positive IgG memory B cell is a CD38-positive IgG-positive that has class switched and lacks expression of IgD on the cell surface with the phenotype IgD-negative, CD38-positive, and IgG-positive.""",
                meaning=CL["0002107"]))
        setattr(cls, "CL:1000472",
            PermissibleValue(
                text="CL:1000472",
                description="A myoepithelial cell that is part of the tertiary lactiferous duct.",
                meaning=CL["1000472"]))
        setattr(cls, "CL:0005011",
            PermissibleValue(
                text="CL:0005011",
                description="""A cuboidal epithelial cell of the kidney which secretes acid and reabsorbs base to regulate acid/base balance.""",
                meaning=CL["0005011"]))
        setattr(cls, "CL:0000929",
            PermissibleValue(
                text="CL:0000929",
                description="A mature NK T cell that secretes interferon-gamma and enhances Th1 immune responses.",
                meaning=CL["0000929"]))
        setattr(cls, "CL:4023007",
            PermissibleValue(
                text="CL:4023007",
                description="""A VIP GABAergic cortical interneuron with bipolar morphology, with a soma found in L2/3. L2/3 bipolar VIP cells have extending axons across all layers (with preferences for layers II/III and Va) and a dendritic tree that is vertically more restricted than deeper layer VIP cells and extend fewer dendrites into the layers outside their home layer (location of soma). L2/3 bipolar VIP cells have great variability in firing patterns, though most are continuous adapting. L2/3 bipolar VIP cells are more depolarized in their resting state, had less fast rectification, and had smaller after hyperpolarization than deeper VIP cells.""",
                meaning=CL["4023007"]))
        setattr(cls, "CL:0009049",
            PermissibleValue(
                text="CL:0009049",
                description="""A layer of smooth muscle cells that forms the outer layer of the high endothelial venule of lymph node and pumps to allow flow of lymph fluid carrying lymphocytes.""",
                meaning=CL["0009049"]))
        setattr(cls, "CL:0000188",
            PermissibleValue(
                text="CL:0000188",
                description="A somatic cell located in skeletal muscle.",
                meaning=CL["0000188"]))
        setattr(cls, "CL:2000093",
            PermissibleValue(
                text="CL:2000093",
                description="Any fibroblast of lung that is part of a bronchus.",
                meaning=CL["2000093"]))
        setattr(cls, "CL:1001474",
            PermissibleValue(
                text="CL:1001474",
                description="""An inhibitory, GABAergic projection neuron in the striatum that integrates glutamatergic signals arising from the cerebral cortex and thalamus.""",
                meaning=CL["1001474"]))
        setattr(cls, "CL:1000414",
            PermissibleValue(
                text="CL:1000414",
                description="An endothelial cell that is part of the venule.",
                meaning=CL["1000414"]))
        setattr(cls, "CL:1001318",
            PermissibleValue(
                text="CL:1001318",
                description="A pericyte cell located in the kidney interstitium.",
                meaning=CL["1001318"]))
        setattr(cls, "CL:0000777",
            PermissibleValue(
                text="CL:0000777",
                description="""A tissue-resident macrophage of the renal glomerular mesangium involved in the disposal and degradation of filtration residues, presentation of antigen to T cells and in tissue remodeling.""",
                meaning=CL["0000777"]))
        setattr(cls, "CL:0002103",
            PermissibleValue(
                text="CL:0002103",
                description="""An IgG-positive double negative memory B cell is a double negative memory B cell with the phenotype IgG-positive, IgD-negative, and CD27-negative.""",
                meaning=CL["0002103"]))
        setattr(cls, "CL:1001580",
            PermissibleValue(
                text="CL:1001580",
                description="A glial cell that is part of the hippocampus.",
                meaning=CL["1001580"]))
        setattr(cls, "CL:0000020",
            PermissibleValue(
                text="CL:0000020",
                description="An euploid male germ cell of an early stage of spermatogenesis.",
                meaning=CL["0000020"]))
        setattr(cls, "CL:0002530",
            PermissibleValue(
                text="CL:0002530",
                description="An immature CD1a-positive dermal dendritic cell is CD80-low, CD86-low, and MHCII-low.",
                meaning=CL["0002530"]))
        setattr(cls, "CL:0000708",
            PermissibleValue(
                text="CL:0000708",
                description="""Stromal cell that forms the internal covering of the vertebrate brain and produces ECM for this and the choroid plexus.""",
                meaning=CL["0000708"]))
        setattr(cls, "CL:4023046",
            PermissibleValue(
                text="CL:4023046",
                description="""An excitatory glutamatergic neuron transcriptomically related to the CT subclass, with a soma preferentially located in the bottom of L6 of the primary motor cortex.""",
                meaning=CL["4023046"]))
        setattr(cls, "CL:0000659",
            PermissibleValue(
                text="CL:0000659",
                description="An extracellular matrix secreting cell that secretes eggshell.",
                meaning=CL["0000659"]))
        setattr(cls, "CL:4023158",
            PermissibleValue(
                text="CL:4023158",
                description="""A neuron in the posterior ventral cochlear nucleus that is distinguished by their long, thick and tentacle-shaped dendrites that typically emanate from one side of the cell body.""",
                meaning=CL["4023158"]))
        setattr(cls, "CL:1001433",
            PermissibleValue(
                text="CL:1001433",
                description="An epithelial cell of the exocrine pancreas.",
                meaning=CL["1001433"]))
        setattr(cls, "CL:4042009",
            PermissibleValue(
                text="CL:4042009",
                description="""An astrocyte type that presents radial protrusions across the layers of a cortex. The soma of this astrocyte is part of the first layer of a neocortex. This astrocyte extents its protrusions transversally to the deeper layers of a cortex and it creates contact with neurons, the pia matter and capillaries. This astrocyte is involved in facilitating the communication across neurons, astrocytes, capillaries, meninges and the cerebrospinal fluid.""",
                meaning=CL["4042009"]))
        setattr(cls, "CL:0002667",
            PermissibleValue(
                text="CL:0002667",
                description="""An otic fibrocyte that resides above the stria vasularis and is part of a mesenchymal gap junction network that regulates ionic homeostasis of the endolymph.""",
                meaning=CL["0002667"]))
        setattr(cls, "CL:0000489",
            PermissibleValue(
                text="CL:0000489",
                meaning=CL["0000489"]))
        setattr(cls, "CL:0000962",
            PermissibleValue(
                text="CL:0000962",
                description="""A follicular B cell that is IgD-positive and CD23-positive and CD38-positive. This naive cell type is activated in the extrafollicular areas via interaction with dendritic cells and antigen specific T cells.""",
                meaning=CL["0000962"]))
        setattr(cls, "CL:0000743",
            PermissibleValue(
                text="CL:0000743",
                description="""Chondrocyte that is terminally differentiated, produces type X collagen, is large in size, and often associated with the replacement of cartilage by bone (endochondral ossification).""",
                meaning=CL["0000743"]))
        setattr(cls, "CL:0000545",
            PermissibleValue(
                text="CL:0000545",
                description="""A CD4-positive, alpha-beta T cell that has the phenotype T-bet-positive, CXCR3-positive, CCR6-negative, and is capable of producing interferon-gamma.""",
                meaning=CL["0000545"]))
        setattr(cls, "CL:0000603",
            PermissibleValue(
                text="CL:0000603",
                description="A fungal cell with two genetically distinct haploid nuclei.",
                meaning=CL["0000603"]))
        setattr(cls, "CL:1000458",
            PermissibleValue(
                text="CL:1000458",
                description="A melanocyte that is part of the skin of body.",
                meaning=CL["1000458"]))
        setattr(cls, "CL:0000037",
            PermissibleValue(
                text="CL:0000037",
                description="""A stem cell from which all cells of the lymphoid and myeloid lineages develop, including blood cells and cells of the immune system. Hematopoietic stem cells lack cell markers of effector cells (lin-negative). Lin-negative is defined by lacking one or more of the following cell surface markers: CD2, CD3 epsilon, CD4, CD5 ,CD8 alpha chain, CD11b, CD14, CD19, CD20, CD56, ly6G, ter119.""",
                meaning=CL["0000037"]))
        setattr(cls, "CL:0000711",
            PermissibleValue(
                text="CL:0000711",
                description="""Cumulus cell is a specialized granulosa cell that surrounds and nourishes the oocyte. This cell-type surrounds the fully-grown oocyte to form a cumulus-oocyte complex (abbr. COC). The terms cumulus oophorus cells, cumulus granulosa cells, cumulus oophorous granulosa cells, granulosa-cumulus cells are used to make a distinction between this cell and the other functionally different subpopulation of granulosa cells at the wall of the Graafian follicle.""",
                meaning=CL["0000711"]))
        setattr(cls, "CL:0007019",
            PermissibleValue(
                text="CL:0007019",
                meaning=CL["0007019"]))
        setattr(cls, "CL:0002651",
            PermissibleValue(
                text="CL:0002651",
                description="""An endothelial cell that is part of the venous sinus of spleen. This endothelial cell has an elongated, spindle-shaped, flattened morphology that is parallel to long axis of sinus. This cell type rests on a basement membrane interrupted by numerous narrow slits.""",
                meaning=CL["0002651"]))
        setattr(cls, "CL:4033063",
            PermissibleValue(
                text="CL:4033063",
                description="""A trophoblast cell that invades the maternal spiral arteries and replace the endothelial lining, remodeling the vessels and allowing for adequate blood transport into the placenta. An endovascular extravillous trophoblast cell differentiates from an extravillous trophoblast cell. In humans, this cell can be distinguished by the expression of CD56.""",
                meaning=CL["4033063"]))
        setattr(cls, "CL:0010013",
            PermissibleValue(
                text="CL:0010013",
                meaning=CL["0010013"]))
        setattr(cls, "CL:0000752",
            PermissibleValue(
                text="CL:0000752",
                description="""A bipolar neuron found in the retina and having connections with cone photoreceptor cells and neurons in the inner plexiform layer.""",
                meaning=CL["0000752"]))
        setattr(cls, "CL:0009111",
            PermissibleValue(
                text="CL:0009111",
                description="A germinal center B cell found in a lymph node germinal center light zone.",
                meaning=CL["0009111"]))
        setattr(cls, "CL:0002384",
            PermissibleValue(
                text="CL:0002384",
                description="A macroconidium that has only one nucleus.",
                meaning=CL["0002384"]))
        setattr(cls, "CL:0000102",
            PermissibleValue(
                text="CL:0000102",
                description="""A neuron type that respond to multiple stimuli such as mechanical, thermal and chemical. This neuron type is responsible for integrating different types of sensory inputs, allowing organisms to respond appropriately to diverse environmental challenges.""",
                meaning=CL["0000102"]))
        setattr(cls, "CL:4023055",
            PermissibleValue(
                text="CL:4023055",
                description="""A corticothalamic-projecting glutamatergic neuron that is located in L6 and lower L5 of the primary motor cortex, with a pyramidal morphology and mostly untufted apical dendrites terminating in midcortical layers. CT VAL/VM (ventroanterior-ventrolateral complex/ventromedial nucleus) cells have a near tonic firing pattern and are distinguished from L6 IT neurons by a lower inter-spike interval adaptation index.""",
                meaning=CL["4023055"]))
        setattr(cls, "CL:0002205",
            PermissibleValue(
                text="CL:0002205",
                description="A brush cell found in the epithelium of lobular bronchiole.",
                meaning=CL["0002205"]))
        setattr(cls, "CL:0002251",
            PermissibleValue(
                text="CL:0002251",
                description="""An epithelial cell of the musculomembranous digestive tube extending from the mouth to the anus.""",
                meaning=CL["0002251"]))
        setattr(cls, "CL:4033006",
            PermissibleValue(
                text="CL:4033006",
                description="A(n) endothelial cell that is part of a(n) efferent lymphatic vessel.",
                meaning=CL["4033006"]))
        setattr(cls, "CL:0000667",
            PermissibleValue(
                text="CL:0000667",
                description="An extracellular matrix secreting cell that secretes collagen.",
                meaning=CL["0000667"]))
        setattr(cls, "CL:4047029",
            PermissibleValue(
                text="CL:4047029",
                description="""An endothelial cell forming the walls of capillaries immediately downstream from arterioles, facilitating the exchange of substances between blood and interstitial fluid. This cell is characterized by a small diameter and may be continuous, fenestrated, or sinusoidal, depending on their location and function. This cell plays a crucial role in tissue oxygenation, nutrient delivery, and maintaining homeostasis within the microvascular network.""",
                meaning=CL["4047029"]))
        setattr(cls, "CL:0000157",
            PermissibleValue(
                text="CL:0000157",
                description="A cell that specializes in secretion of surfactant in the alveoli of the lung.",
                meaning=CL["0000157"]))
        setattr(cls, "CL:0002235",
            PermissibleValue(
                text="CL:0002235",
                description="A cell of the luminal layer of the epithelium in the prostatic acinus.",
                meaning=CL["0002235"]))
        setattr(cls, "CL:0009011",
            PermissibleValue(
                text="CL:0009011",
                description="""A rapidly proliferating population of cells that differentiate from stem cells of the intestinal crypt of the colon. Stem cells located in the crypts of Lieberkühn give rise to proliferating progenitor or transit amplifying cells that differentiate into the four major epithelial cell types. These include columnar absorptive cells or enterocytes, mucous secreting goblet cells, enteroendocrine cells and paneth cells.""",
                meaning=CL["0009011"]))
        setattr(cls, "CL:1000504",
            PermissibleValue(
                text="CL:1000504",
                description="A cell that is part of a renal medulla.",
                meaning=CL["1000504"]))
        setattr(cls, "CL:4006001",
            PermissibleValue(
                text="CL:4006001",
                description="A fibroblast that is part of the skin of scalp.",
                meaning=CL["4006001"]))
        setattr(cls, "CL:0000241",
            PermissibleValue(
                text="CL:0000241",
                description="""A stratified epithelial cell that is part of cuboidal epithelium, characterized by multiple layers of cuboidal cells forming the apical layer. This provides a protective lining for ducts in large glands, such as sweat glands.""",
                meaning=CL["0000241"]))
        setattr(cls, "CL:0000463",
            PermissibleValue(
                text="CL:0000463",
                description="An epidermal cell that secretes chitinous cuticle from its apical side.",
                meaning=CL["0000463"]))
        setattr(cls, "CL:0001063",
            PermissibleValue(
                text="CL:0001063",
                description="""An abnormal cell exhibiting dysregulation of cell proliferation or programmed cell death and capable of forming a neoplasm, an aggregate of cells in the form of a tumor mass or an excess number of abnormal cells (liquid tumor) within an organism.""",
                meaning=CL["0001063"]))
        setattr(cls, "CL:0010000",
            PermissibleValue(
                text="CL:0010000",
                description="""A hair follicle matrix region cell which synthesizes keratin and undergoes a characteristic change as it moves upward from the hair bulb to become the hair medulla cortex and hair root sheath.""",
                meaning=CL["0010000"]))
        setattr(cls, "CL:0002465",
            PermissibleValue(
                text="CL:0002465",
                description="A conventional dendritic cell that expresses CD11b (ITGAM).",
                meaning=CL["0002465"]))
        setattr(cls, "CL:0000719",
            PermissibleValue(
                text="CL:0000719",
                meaning=CL["0000719"]))
        setattr(cls, "CL:4023036",
            PermissibleValue(
                text="CL:4023036",
                description="""A transcriptomically distinct pvalb GABAergic cortical interneuron that is recognizable by the straight terminal axonal 'cartridges' of vertically oriented strings of synaptic boutons. Chandelier PV cells' boutons target exclusively the axon initial segment (AIS) of pyramidal cells, with a single cell innervating hundreds of pyramidal cells in a clustered manner. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: CGE-derived interneurons', Author Categories: 'CrossArea_subclass', clusters Chandelier.""",
                meaning=CL["4023036"]))
        setattr(cls, "CL:2000048",
            PermissibleValue(
                text="CL:2000048",
                description="""A lower motor neuron whose soma is located in the anterior horn. Anterior horn motor neurons project from the anterior portion of the grey matter in the spinal cord to some skeletal muscles.""",
                meaning=CL["2000048"]))
        setattr(cls, "CL:0000388",
            PermissibleValue(
                text="CL:0000388",
                description="""An elongated fibrocyte that is part of a tendon. The cytoplasm is stretched between the collagen fibres of the tendon. They have a central cell nucleus with a prominent nucleolus. Tendon cells have a well-developed rough endoplasmic reticulum and they are responsible for synthesis and turnover of tendon fibres and ground substance.""",
                meaning=CL["0000388"]))
        setattr(cls, "CL:0000826",
            PermissibleValue(
                text="CL:0000826",
                description="""A progenitor cell of the B cell lineage, with some lineage specific activity such as early stages of recombination of B cell receptor genes, but not yet fully committed to the B cell lineage until the expression of PAX5 occurs.""",
                meaning=CL["0000826"]))
        setattr(cls, "CL:0000589",
            PermissibleValue(
                text="CL:0000589",
                description="""A bulbous cell that is medially placed in one row in the organ of Corti. In contrast to the outer hair cells, the inner hair cells are fewer in number, have fewer sensory hairs, and are less differentiated.""",
                meaning=CL["0000589"]))
        setattr(cls, "CL:1001593",
            PermissibleValue(
                text="CL:1001593",
                description="Glandular (secretory) cell of parathyroid epithelium.",
                meaning=CL["1001593"]))
        setattr(cls, "CL:1000473",
            PermissibleValue(
                text="CL:1000473",
                description="A myoepithelial cell that is part of the quarternary lactiferous duct.",
                meaning=CL["1000473"]))
        setattr(cls, "CL:4033089",
            PermissibleValue(
                text="CL:4033089",
                description="""A follicular cell of ovary that has begun to degenerate and undergo atresia, a specialized apoptosis. This cell is found in an atretic follicle, which is an ovarian follicle that started to mature but failed to reach full development and instead regresses.""",
                meaning=CL["4033089"]))
        setattr(cls, "CL:0000106",
            PermissibleValue(
                text="CL:0000106",
                description="Neuron with one neurite that extends from the cell body.",
                meaning=CL["0000106"]))
        setattr(cls, "CL:0002562",
            PermissibleValue(
                text="CL:0002562",
                description="An epidermal cell that is part of the germinal matrix.",
                meaning=CL["0002562"]))
        setattr(cls, "CL:2000008",
            PermissibleValue(
                text="CL:2000008",
                description="Any blood vessel endothelial cell that is part of a microvascular endothelium.",
                meaning=CL["2000008"]))
        setattr(cls, "CL:4047005",
            PermissibleValue(
                text="CL:4047005",
                description="A(n) neuroblast (sensu Vertebrata) that is cycling.",
                meaning=CL["4047005"]))
        setattr(cls, "CL:4023110",
            PermissibleValue(
                text="CL:4023110",
                description="A pyramidal neuron with soma located in the amygdala.",
                meaning=CL["4023110"]))
        setattr(cls, "CL:4070016",
            PermissibleValue(
                text="CL:4070016",
                description="Pyloric pacemaker neuron that provides feedback to commissural ganglia (CoG) neurons.",
                meaning=CL["4070016"]))
        setattr(cls, "CL:0002210",
            PermissibleValue(
                text="CL:0002210",
                description="""A slow muscle cell that contains high levels of myoglobin and oxygen storing proteins giving the cell a red appearance.""",
                meaning=CL["0002210"]))
        setattr(cls, "CL:0002509",
            PermissibleValue(
                text="CL:0002509",
                description="A langerin-positive lymph node dendritic cell that is CD103-positive and CD11b-low.",
                meaning=CL["0002509"]))
        setattr(cls, "CL:0002154",
            PermissibleValue(
                text="CL:0002154",
                description="""A promyelocyte with a nucleus that is indented and contains more marginated heterochromatin compared to its precursor cell (myeloblast); cytoplasm is deeply basophilic and contains numerous mitochondria and meandering cysternae of endoplasmic reticulum; largest of the granulocyte lineages.""",
                meaning=CL["0002154"]))
        setattr(cls, "CL:0000341",
            PermissibleValue(
                text="CL:0000341",
                meaning=CL["0000341"]))
        setattr(cls, "CL:0000581",
            PermissibleValue(
                text="CL:0000581",
                description="""A macrophage resident in the peritoneum under non-inflammatory conditions. Markers include F4/80-high, CD11b-high, CD68-positive, SIGNR1-positive, CD115-high, MHC-II-negative, and Dectin-1-positive.""",
                meaning=CL["0000581"]))
        setattr(cls, "CL:0002337",
            PermissibleValue(
                text="CL:0002337",
                description="""A stem cell located in the bulge of the hair follicle that can give rise to regenerate the new follicle with each hair cycle and to reepithelialize the epidermis during wound repair.""",
                meaning=CL["0002337"]))
        setattr(cls, "CL:4052018",
            PermissibleValue(
                text="CL:4052018",
                description="Any epithelial cell that is part of the fallopian tube.",
                meaning=CL["4052018"]))
        setattr(cls, "CL:4030016",
            PermissibleValue(
                text="CL:4030016",
                description="An epithelial cell located in the early distal convoluted tubule.",
                meaning=CL["4030016"]))
        setattr(cls, "CL:4030019",
            PermissibleValue(
                text="CL:4030019",
                description="A renal intercalated cell that is part of the renal connecting tubule.",
                meaning=CL["4030019"]))
        setattr(cls, "CL:4023121",
            PermissibleValue(
                text="CL:4023121",
                description="""A transcriptomically distinct sst GABAergic cortical interneuron that also expresses Chodl. These neurons are rare and correspond to the only known cortical interneurons with long-range projection. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: MGE-derived interneurons', Author Categories: 'CrossArea_subclass', clusters Sst Chodl.""",
                meaning=CL["4023121"]))
        setattr(cls, "CL:0000824",
            PermissibleValue(
                text="CL:0000824",
                description="""A natural killer cell that is developmentally mature and expresses a variety of inhibitory and activating receptors that recognize MHC class I and other stress related molecules.""",
                meaning=CL["0000824"]))
        setattr(cls, "CL:2000011",
            PermissibleValue(
                text="CL:2000011",
                description="Any endothelial cell of lymphatic vessel that is part of a dermis.",
                meaning=CL["2000011"]))
        setattr(cls, "CL:4042041",
            PermissibleValue(
                text="CL:4042041",
                description="""A type of primary motor neuron located in the middle region of the spinal cord. This primary motor neuron type is characterized by their distinct axonal pathways that innervate the middle trunk muscles.""",
                meaning=CL["4042041"]))
        setattr(cls, "CL:1001225",
            PermissibleValue(
                text="CL:1001225",
                description="A cell that is part of a collecting duct of renal tubule.",
                meaning=CL["1001225"]))
        setattr(cls, "CL:0000010",
            PermissibleValue(
                text="CL:0000010",
                description="""A cell in vitro that is or has been maintained or propagated as part of a cell culture.""",
                meaning=CL["0000010"]))
        setattr(cls, "CL:0009079",
            PermissibleValue(
                text="CL:0009079",
                description="A fibroblast located between thymic lobules.",
                meaning=CL["0009079"]))
        setattr(cls, "CL:0011015",
            PermissibleValue(
                text="CL:0011015",
                description="""A motile sperm cell that contain no F-actin, and their motility is powered by a dynamic filament system.""",
                meaning=CL["0011015"]))
        setattr(cls, "CL:0002482",
            PermissibleValue(
                text="CL:0002482",
                description="A melanocyte that produces pigment in the dermis.",
                meaning=CL["0002482"]))
        setattr(cls, "CL:1000329",
            PermissibleValue(
                text="CL:1000329",
                description="A goblet cell that is part of the epithelium of trachea.",
                meaning=CL["1000329"]))
        setattr(cls, "CL:4023004",
            PermissibleValue(
                text="CL:4023004",
                description="""A type of intrafusal muscle fiber that lies in the center of a muscle spindle. Nuclei are clustered centrally and give the equatorial region a swollen appearance. They are associated with associated with dynamic gamma motor neurons, and the stretching of the equatorial region of the nuclear bag fibers results in an increase in the firing rate of type Ia sensory fibers.""",
                meaning=CL["4023004"]))
        setattr(cls, "CL:1000447",
            PermissibleValue(
                text="CL:1000447",
                description="A basal cell that is part of the epithelium of esophagus.",
                meaning=CL["1000447"]))
        setattr(cls, "CL:0001061",
            PermissibleValue(
                text="CL:0001061",
                description="""A cell found in an organism or derived from an organism exhibiting a phenotype that deviates from the expected phenotype of any native cell type of that organism. Abnormal cells are typically found in disease states or disease models.""",
                meaning=CL["0001061"]))
        setattr(cls, "CL:0000460",
            PermissibleValue(
                text="CL:0000460",
                description="Any secretory cell that is capable of some glucocorticoid secretion.",
                meaning=CL["0000460"]))
        setattr(cls, "CL:1001068",
            PermissibleValue(
                text="CL:1001068",
                meaning=CL["1001068"]))
        setattr(cls, "CL:0000098",
            PermissibleValue(
                text="CL:0000098",
                description="""A specialized epithelial cell involved in sensory perception. Restricted to special sense organs of the olfactory, gustatory, and vestibulocochlear receptor systems; contain sensory cells surrounded by supportive, non-receptive cells.""",
                meaning=CL["0000098"]))
        setattr(cls, "CL:0000935",
            PermissibleValue(
                text="CL:0000935",
                description="""A CD4-negative, CD8-negative, alpha-beta intraepithelial T cell that is found in the columnar epithelium of the gastrointestinal tract.""",
                meaning=CL["0000935"]))
        setattr(cls, "CL:0009043",
            PermissibleValue(
                text="CL:0009043",
                description="An intestinal crypt stem cell that is located in the crypt of Lieberkuhn of colon.",
                meaning=CL["0009043"]))
        setattr(cls, "CL:0004244",
            PermissibleValue(
                text="CL:0004244",
                description="""An amacrine cell with a wide dendritic field, dendrites in S4, and post-synaptic terminals in S4.""",
                meaning=CL["0004244"]))
        setattr(cls, "CL:1000448",
            PermissibleValue(
                text="CL:1000448",
                description="An epithelial cell that is part of the sweat gland.",
                meaning=CL["1000448"]))
        setattr(cls, "CL:0001059",
            PermissibleValue(
                text="CL:0001059",
                description="""A progenitor cell committed to myeloid lineage, including the megakaryocyte and erythroid lineages. These cells are CD34-positive, and express Gata1, Gata2, C/EBPa, and Pu.1.""",
                meaning=CL["0001059"]))
        setattr(cls, "CL:0000945",
            PermissibleValue(
                text="CL:0000945",
                description="A lymphocyte of B lineage with the commitment to express an immunoglobulin complex.",
                meaning=CL["0000945"]))
        setattr(cls, "CL:0001057",
            PermissibleValue(
                text="CL:0001057",
                description="A myeloid dendritic cell with the phenotype HLA-DRA-positive.",
                meaning=CL["0001057"]))
        setattr(cls, "CL:1001224",
            PermissibleValue(
                text="CL:1001224",
                description="Any smooth muscle cell that is part of some renal interlobular vein.",
                meaning=CL["1001224"]))
        setattr(cls, "CL:0005005",
            PermissibleValue(
                text="CL:0005005",
                description="""A non-terminally differentiated cell that originates from the neural crest and differentiates into a cyanophore.""",
                meaning=CL["0005005"]))
        setattr(cls, "CL:0000649",
            PermissibleValue(
                text="CL:0000649",
                description="""A cell with delicate radiating processes known as desmosomes that form intercellular bridges between other cells of this type. This cell type forms the stratum spinosum (prickle cell layer). A function of this cell is to generate keratin.""",
                meaning=CL["0000649"]))
        setattr(cls, "CL:2000025",
            PermissibleValue(
                text="CL:2000025",
                description="Any oligodendrocyte that is part of a spinal cord.",
                meaning=CL["2000025"]))
        setattr(cls, "CL:0000996",
            PermissibleValue(
                text="CL:0000996",
                description="""Mature CD11c-negative plasmacytoid dendritic cell is a CD11c-negative plasmacytoid dendritic cell is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0000996"]))
        setattr(cls, "CL:4023169",
            PermissibleValue(
                text="CL:4023169",
                description="""A neuron that is responsible for sensation in the face or motor functions such as biting and chewing. Trigeminal neurons extend a single axon shaft along the lateral white matter of the hindbrain and spinal cord. The highly branched axons innervate the integument of the head.""",
                meaning=CL["4023169"]))
        setattr(cls, "CL:0000989",
            PermissibleValue(
                text="CL:0000989",
                description="""CD11c-low plasmacytoid dendritic cell is a leukocyte that is CD11c-low, CD45R-positive, GR1-positive and CD11b-negative.""",
                meaning=CL["0000989"]))
        setattr(cls, "CL:0002373",
            PermissibleValue(
                text="CL:0002373",
                description="A peptide hormone secreting cell that secretes growth hormone releasing hormone.",
                meaning=CL["0002373"]))
        setattr(cls, "CL:4030057",
            PermissibleValue(
                text="CL:4030057",
                description="""A medium spiny neuron that exhibits transcriptional divergence from direct and indirect spiny projection neurons, for example, enrichment in Casz1, Otof, Cacng5 and Pcdh8 noted in mice. Whilst in general medium spiny neurons have been found to be differentially distributed across the basal ganglia, the eccentric medium spiny neuron cell type has been found to be more evenly distributed throughout cerebral nuclei.""",
                meaning=CL["4030057"]))
        setattr(cls, "CL:0000597",
            PermissibleValue(
                text="CL:0000597",
                description="""The smaller of two types of asexual spores formed by some fungi. An ovoid to pear-shaped asexual spore that contains very little cytoplasm and organelles, is uninucleate, and forms in vegetative hypae within a mycelium. Micronidia are extruded from the hyphal cell wall.""",
                meaning=CL["0000597"]))
        setattr(cls, "CL:0002108",
            PermissibleValue(
                text="CL:0002108",
                description="""A CD38-negative IgG memory B cell is a IgG-positive class switched memory B cell that has class switched and expresses IgG on the cell surface with the phenotype CD38-negative, IgD-negative, and IgG-positive.""",
                meaning=CL["0002108"]))
        setattr(cls, "CL:0001049",
            PermissibleValue(
                text="CL:0001049",
                description="""A recently activated CD8-positive, alpha-beta T cell with the phenotype HLA-DRA-positive, CD38-positive, CD69-positive, CD62L-negative, CD127-negative, CCR7-negative, and CD25-positive.""",
                meaning=CL["0001049"]))
        setattr(cls, "CL:0002407",
            PermissibleValue(
                text="CL:0002407",
                description="""A thymocyte that has a T cell receptor consisting of a gamma chain containing Vgamma2 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-negative.""",
                meaning=CL["0002407"]))
        setattr(cls, "CL:0000552",
            PermissibleValue(
                text="CL:0000552",
                description="""The final stage of the nucleated, immature erythrocyte, before nuclear loss. Typically the cytoplasm is described as acidophilic, but it still shows a faint polychromatic tint. The nucleus is small and initially may still have coarse, clumped chromatin, as in its precursor, the polychromatophilic erythroblast, but ultimately it becomes pyknotic, and appears as a deeply staining, blue-black, homogeneous structureless mass. The nucleus is often eccentric and sometimes lobulated.""",
                meaning=CL["0000552"]))
        setattr(cls, "CL:0000980",
            PermissibleValue(
                text="CL:0000980",
                description="""An activated mature (naive or memory) B cell that is secreting immunoglobulin, typified by being CD27-positive, CD38-positive, CD138-negative.""",
                meaning=CL["0000980"]))
        setattr(cls, "CL:0002598",
            PermissibleValue(
                text="CL:0002598",
                description="Any smooth muscle cell that is part of some bronchus.",
                meaning=CL["0002598"]))
        setattr(cls, "CL:0001034",
            PermissibleValue(
                text="CL:0001034",
                description="""A cell that is maintained or propagated in a controlled artificial environment for use in an investigation.""",
                meaning=CL["0001034"]))
        setattr(cls, "CL:1001006",
            PermissibleValue(
                text="CL:1001006",
                description="""An endothelial cell which is part of the afferent arteriole in the kidney. This cell is  responsible for maintaining renal blood flow and glomerular filtration rate.""",
                meaning=CL["1001006"]))
        setattr(cls, "CL:2000037",
            PermissibleValue(
                text="CL:2000037",
                description="Any neuromast hair cell that is part of a posterior lateral line.",
                meaning=CL["2000037"]))
        setattr(cls, "CL:1000326",
            PermissibleValue(
                text="CL:1000326",
                description="A goblet cell that is part of the epithelium proper of ileum.",
                meaning=CL["1000326"]))
        setattr(cls, "CL:4033030",
            PermissibleValue(
                text="CL:4033030",
                description="""An OFF calbindin-negative bipolar cell that has a large dendritic field and stratifies narrowly close to the middle of the inner plexiform layer. Its axon terminal is characterized by regularly branching and varicose processes resembling beads on a string. Most of DB3b contacts with cones are non-triad-associated.""",
                meaning=CL["4033030"]))
        setattr(cls, "CL:0002318",
            PermissibleValue(
                text="CL:0002318",
                description="""A mesothelial cell capable of circulating in the blood by first losing its squamous character. This cell can incorporate into the regenerating mesothelium.""",
                meaning=CL["0002318"]))
        setattr(cls, "CL:0000919",
            PermissibleValue(
                text="CL:0000919",
                description="""A CD8-positive alpha beta-positive T cell with the phenotype FoxP3-positive and having suppressor function.""",
                meaning=CL["0000919"]))
        setattr(cls, "CL:0002341",
            PermissibleValue(
                text="CL:0002341",
                description="An undifferentiated cell of the prostate epithelium that lacks secretory activity.",
                meaning=CL["0002341"]))
        setattr(cls, "CL:0000638",
            PermissibleValue(
                text="CL:0000638",
                description="An acidophilic chromophil cell that of the anterior pituitary gland.",
                meaning=CL["0000638"]))
        setattr(cls, "CL:1000854",
            PermissibleValue(
                text="CL:1000854",
                description="A blood vessel cell that is part of a kidney.",
                meaning=CL["1000854"]))
        setattr(cls, "CL:1000123",
            PermissibleValue(
                text="CL:1000123",
                description="Any epithelial cell that is part of some metanephric nephron tubule.",
                meaning=CL["1000123"]))
        setattr(cls, "CL:1001214",
            PermissibleValue(
                text="CL:1001214",
                description="Any smooth muscle cell that is part of some kidney arcuate artery.",
                meaning=CL["1001214"]))
        setattr(cls, "CL:0000031",
            PermissibleValue(
                text="CL:0000031",
                description="A cell that will develop into a neuron often after a migration phase.",
                meaning=CL["0000031"]))
        setattr(cls, "CL:0000312",
            PermissibleValue(
                text="CL:0000312",
                description="""An epidermal cell which synthesizes keratin and undergoes a characteristic change as it moves upward from the basal layers of the epidermis to the cornified (horny) layer of the skin. Successive stages of differentiation of the keratinocytes forming the epidermal layers are basal cell, spinous or prickle cell, and the granular cell.""",
                meaning=CL["0000312"]))
        setattr(cls, "CL:4023059",
            PermissibleValue(
                text="CL:4023059",
                description="An oligodendrocyte precursor cell that is committed to differentiate.",
                meaning=CL["4023059"]))
        setattr(cls, "CL:0000432",
            PermissibleValue(
                text="CL:0000432",
                description="""A fibroblast that synthesizes collagen and uses it to produce reticular fibers, thus providing structural support. Reticular cells are found in many organs, including the spleen, lymph nodes and kidneys. Subtypes of reticular cells include epithelial, mesenchymal, and fibroblastic reticular cells. Fibroblastic reticular cells are involved in directing B cells and T cells to specific regions within a tissue, whereas epithelial and mesenchymal reticular cells are associated with certain areas of the brain.""",
                meaning=CL["0000432"]))
        setattr(cls, "CL:0000129",
            PermissibleValue(
                text="CL:0000129",
                description="""A transcriptomically distinct central nervous system macrophage found in the parenchyma of the central nervous system. Marker include CD11b-positive, F4/80-positive, and CD68-positive.""",
                meaning=CL["0000129"]))
        setattr(cls, "CL:0002310",
            PermissibleValue(
                text="CL:0002310",
                description="""An acidophil cell of the anterior pituitary gland that produces both prolactin and growth hormone.""",
                meaning=CL["0002310"]))
        setattr(cls, "CL:2000001",
            PermissibleValue(
                text="CL:2000001",
                description="""A leukocyte with a single non-segmented nucleus in the mature form found in the circulatory pool of blood.""",
                meaning=CL["2000001"]))
        setattr(cls, "CL:0008046",
            PermissibleValue(
                text="CL:0008046",
                description="""A skeletal muscle fiber that is innervated by alpha motor neuron and generates tension by contracting, thereby allowing for skeletal movement. These fibers make up the large mass of skeletal muscle tissue and are attached to bones by tendons.""",
                meaning=CL["0008046"]))
        setattr(cls, "CL:0000636",
            PermissibleValue(
                text="CL:0000636",
                description="""Astrocyte-like radial glial cell that extends vertically throughout the retina, with the nucleus are usually in the middle of the inner nuclear layer.""",
                meaning=CL["0000636"]))
        setattr(cls, "CL:4042032",
            PermissibleValue(
                text="CL:4042032",
                description="""A transcriptomically distinct GABAergic neuron located in the cerebral cortex that expresses the transcript PAX6. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: CGE-derived interneurons', Author Categories: 'CrossArea_subclass', clusters PAX6.""",
                meaning=CL["4042032"]))
        setattr(cls, "CL:1000695",
            PermissibleValue(
                text="CL:1000695",
                meaning=CL["1000695"]))
        setattr(cls, "CL:0002554",
            PermissibleValue(
                text="CL:0002554",
                description="A fibroblast of the lymphatic system.",
                meaning=CL["0002554"]))
        setattr(cls, "CL:0000056",
            PermissibleValue(
                text="CL:0000056",
                description="""A cell that is commited to differentiating into a muscle cell.  Embryonic myoblasts develop from the mesoderm. They undergo proliferation, migrate to their various sites, and then differentiate into the appropriate form of myocytes.  Myoblasts also occur as transient populations of cells in muscles undergoing repair.""",
                meaning=CL["0000056"]))
        setattr(cls, "CL:4047019",
            PermissibleValue(
                text="CL:4047019",
                description="""An enterocyte in the early stages of development, located above the transit-amplifying cell zone in the intestinal crypt-villus axis.""",
                meaning=CL["4047019"]))
        setattr(cls, "CL:0009004",
            PermissibleValue(
                text="CL:0009004",
                description="""Any cell in the retina, the innermost layer or coating at the back of the eyeball, which is sensitive to light and in which the optic nerve terminates.""",
                meaning=CL["0009004"]))
        setattr(cls, "CL:2000014",
            PermissibleValue(
                text="CL:2000014",
                description="Any skin fibroblast that is part of a upper leg skin.",
                meaning=CL["2000014"]))
        setattr(cls, "CL:1000042",
            PermissibleValue(
                text="CL:1000042",
                description="Any neuroblast (sensu Vertebrata) that is part of some forebrain.",
                meaning=CL["1000042"]))
        setattr(cls, "CL:0000039",
            PermissibleValue(
                text="CL:0000039",
                description="""A cell that is within the developmental lineage of gametes and is able to pass along its genetic material to offspring.""",
                meaning=CL["0000039"]))
        setattr(cls, "CL:0008041",
            PermissibleValue(
                text="CL:0008041",
                description="A mesothelial cell that is part of the intestinal serosa.",
                meaning=CL["0008041"]))
        setattr(cls, "CL:4030064",
            PermissibleValue(
                text="CL:4030064",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in cortical layer 5. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: IT-projecting excitatory neurons', Author Categories: 'CrossArea_subclass', L5 IT.""",
                meaning=CL["4030064"]))
        setattr(cls, "CL:0002597",
            PermissibleValue(
                text="CL:0002597",
                description="A smooth muscle cell of the bladder.",
                meaning=CL["0002597"]))
        setattr(cls, "CL:0000365",
            PermissibleValue(
                text="CL:0000365",
                description="Diploid cell produced by the fusion of sperm cell nucleus and egg cell.",
                meaning=CL["0000365"]))
        setattr(cls, "CL:4033070",
            PermissibleValue(
                text="CL:4033070",
                description="A(n) dendritic cell that is cycling.",
                meaning=CL["4033070"]))
        setattr(cls, "CL:0000621",
            PermissibleValue(
                text="CL:0000621",
                description="""A myoblast that is committed to a myotube-specific program of differentiation but not yet fused. It undergoes very limited additional proliferation. After fusion, it will take on a muscle identity specified by a `muscle founder cell` (CL:0008006).""",
                meaning=CL["0000621"]))
        setattr(cls, "CL:0008037",
            PermissibleValue(
                text="CL:0008037",
                description="""A lower motor neuron that innervates only intrafusal muscle fibers. Unlike the alpha motor neurons, gamma motor neurons do not directly adjust the lengthening or shortening of muscles but function in adjusting the sensitivity of muscle spindles and in keeping muscle spindles taut, thereby allowing the continued firing of alpha neurons.""",
                meaning=CL["0008037"]))
        setattr(cls, "CL:0003035",
            PermissibleValue(
                text="CL:0003035",
                description="A monostratified retinal ganglion cell that contains opsin.",
                meaning=CL["0003035"]))
        setattr(cls, "CL:0000586",
            PermissibleValue(
                text="CL:0000586",
                description="The reproductive cell in multicellular organisms.",
                meaning=CL["0000586"]))
        setattr(cls, "CL:0002291",
            PermissibleValue(
                text="CL:0002291",
                description="""A sperm bearing an X chromosome. Chromosomal and genetic sex is established at fertilization in mammals and depends upon whether an X-bearing sperm or a Y-bearing sperm fertilizes the X-bearing ovum.""",
                meaning=CL["0002291"]))
        setattr(cls, "CL:4047036",
            PermissibleValue(
                text="CL:4047036",
                description="""A smooth muscle cell located in the middle layer of the muscularis externa of the stomach wall. This cell is arranged concentrically with the stomach's longitudinal axis, forming a continuous sheet of contractile tissue. It is fusiform in shape, containing actin and myosin filaments that enable contraction without striations. This cell contributes to the mechanical digestion and movement of food within the stomach through coordinated contractions, and plays a role in forming the pyloric sphincter in the pyloric region.""",
                meaning=CL["4047036"]))
        setattr(cls, "CL:1001585",
            PermissibleValue(
                text="CL:1001585",
                description="""Glandular cell of appendix epithelium. Example: Goblet cells; enterocytes or absorptive cells; enteroendocrine and M cells.""",
                meaning=CL["1001585"]))
        setattr(cls, "CL:0000029",
            PermissibleValue(
                text="CL:0000029",
                description="Any neuron that develops from some migratory neural crest cell.",
                meaning=CL["0000029"]))
        setattr(cls, "CL:0002574",
            PermissibleValue(
                text="CL:0002574",
                description="A stromal cell of the pancreas.",
                meaning=CL["0002574"]))
        setattr(cls, "CL:0002541",
            PermissibleValue(
                text="CL:0002541",
                description="A mesenchymal stem cell of the chorionic membrane.",
                meaning=CL["0002541"]))
        setattr(cls, "CL:0000885",
            PermissibleValue(
                text="CL:0000885",
                description="""A mucosa-associated lymphoid tissue macrophage found in the mucosa-associated lymphoid tissues of the gut.""",
                meaning=CL["0000885"]))
        setattr(cls, "CL:0000937",
            PermissibleValue(
                text="CL:0000937",
                description="""Cell committed to natural killer cell lineage that has the phenotype CD122-positive, CD34-positive, and CD117-positive. This cell type lacks expression of natural killer receptor proteins.""",
                meaning=CL["0000937"]))
        setattr(cls, "CL:0002173",
            PermissibleValue(
                text="CL:0002173",
                description="""A cell that is a specialized type of pericyte providing structural support for the capillary loops of kidney. A flat, elongated cell with extensive fine cytoplasmic processes found outside the kidney glomerulus near the macula densa and bound laterally by afferent and efferent arterioles. Being phagocytic, this cell participates in the continuous turnover of the basal lamina by removing its outer portion containing residues of filtration, while the lamina is renewed on its inner surface by the endothelial cells.""",
                meaning=CL["0002173"]))
        setattr(cls, "CL:4047054",
            PermissibleValue(
                text="CL:4047054",
                description="""A dendritic cell capable of capturing antigens in peripheral tissues and migrating through blood or lymphatic vessels to secondary lymphoid organs, where it presents processed antigens to T cells. It expresses MHC class II molecules and lacks lineage markers associated with other leukocyte populations, distinguishing it as a member of the dendritic cell lineage. This cell plays a pivotal role in initiating and regulating adaptive immune responses by linking peripheral antigen capture with T cell activation in lymphoid tissues.""",
                meaning=CL["4047054"]))
        setattr(cls, "CL:4040006",
            PermissibleValue(
                text="CL:4040006",
                description="A chromatophore that is part of the dermis.",
                meaning=CL["4040006"]))
        setattr(cls, "CL:2000088",
            PermissibleValue(
                text="CL:2000088",
                description="Any basket cell that is part of a Ammon's horn.",
                meaning=CL["2000088"]))
        setattr(cls, "CL:0000811",
            PermissibleValue(
                text="CL:0000811",
                description="""An immature alpha-beta T cell that is located in the thymus and is CD8-positive and CD4-negative.""",
                meaning=CL["0000811"]))
        setattr(cls, "CL:4042031",
            PermissibleValue(
                text="CL:4042031",
                description="""An oligodendrocyte of the central nervous system that exhibits immune properties such as self-presentation and non-self antigen presentation to T cells, phagocytosis of debris, and cytokine and chemokine production. Immune oligodendroglia is immunoreactive during inflammation, neurodegenerative disorders, chronic stress and major depressive disorder.""",
                meaning=CL["4042031"]))
        setattr(cls, "CL:0005023",
            PermissibleValue(
                text="CL:0005023",
                description="""Cranial motor neuron which innervates muscles derived from the branchial (pharyngeal) arches.""",
                meaning=CL["0005023"]))
        setattr(cls, "CL:4047043",
            PermissibleValue(
                text="CL:4047043",
                description="""An enteric glial cell that is associated with neuron cell bodies within submucosal ganglia of the gastrointestinal tract. This cell is located in the submucosa, a layer of connective tissue beneath the intestinal mucosa. This cell plays a role in modulating secretomotor neuron activity and contributes to the regulation of digestive fluid secretion and absorption.""",
                meaning=CL["4047043"]))
        setattr(cls, "CL:0002336",
            PermissibleValue(
                text="CL:0002336",
                description="""An endothelial cell that lines the oral cavitiy including the mucosa of the gums, the palate, the lip, and the cheek.""",
                meaning=CL["0002336"]))
        setattr(cls, "CL:0009097",
            PermissibleValue(
                text="CL:0009097",
                description="""A skeletal muscle fiber found in an embryo. In mammalian embryos, skeletal muscle expresses myosin heavy chain-embryonic (MyHC-emb, encoded by the MYH3 gene), which regulates skeletal muscle development.""",
                meaning=CL["0009097"]))
        setattr(cls, "CL:0000946",
            PermissibleValue(
                text="CL:0000946",
                description="""A lymphocyte of B lineage that is devoted to secreting large amounts of immunoglobulin.""",
                meaning=CL["0000946"]))
        setattr(cls, "CL:4033038",
            PermissibleValue(
                text="CL:4033038",
                description="An alpha-beta CD4 T cell that resides in the lung.",
                meaning=CL["4033038"]))
        setattr(cls, "CL:0000120",
            PermissibleValue(
                text="CL:0000120",
                description="""A neuron of the vertebrate central nervous system that is small in size. This general class includes small neurons in the granular layer of the cerebellar cortex, cerebral cortex neurons that are not pyramidal cells and small neurons without axons found in the olfactory bulb.""",
                meaning=CL["0000120"]))
        setattr(cls, "CL:4023009",
            PermissibleValue(
                text="CL:4023009",
                description="""A glutamatergic neuron located in the cerebral cortex that projects to structures not derived from telencephalon.""",
                meaning=CL["4023009"]))
        setattr(cls, "CL:0002233",
            PermissibleValue(
                text="CL:0002233",
                description="An epithelial cell of the prostatic acinus.",
                meaning=CL["0002233"]))
        setattr(cls, "CL:0000647",
            PermissibleValue(
                text="CL:0000647",
                description="""A phagocytic syncytial cell formed by the fusion of macrophages, occurs in chronic inflammatory responses to persistent microorganism such as M.tuberculosis, component of granulomas. Sometimes used to refer to megakaryocytes.""",
                meaning=CL["0000647"]))
        setattr(cls, "CL:0000977",
            PermissibleValue(
                text="CL:0000977",
                description="A short lived plasma cell that secretes IgG.",
                meaning=CL["0000977"]))
        setattr(cls, "CL:0000078",
            PermissibleValue(
                text="CL:0000078",
                description="Any squamous epithelial cell that is part of some periderm.",
                meaning=CL["0000078"]))
        setattr(cls, "CL:0002106",
            PermissibleValue(
                text="CL:0002106",
                description="""An IgD-positive CD38-positive IgG memory B cell is a CD38-positive IgG-positive class switched memory B cell that has class switched and expresses IgD on the cell surface with the phenotype IgD-positive, CD38-positive, and IgG-positive.""",
                meaning=CL["0002106"]))
        setattr(cls, "CL:0002387",
            PermissibleValue(
                text="CL:0002387",
                description="""Cylindrical spore formed by development and compartmentation of hyphae; the hyphae are often supporting blastoconidiophores.""",
                meaning=CL["0002387"]))
        setattr(cls, "CL:4052035",
            PermissibleValue(
                text="CL:4052035",
                description="""A tuft cell that is part of the epithelium of pancreatic duct. Present in humans and rats, this cell is absent in the murine pancreas under normal conditions but emerges during acinar-to-ductal metaplasia triggered by injury, inflammation, or oncogenic mutations. It modulates the immune response and protects against pancreatic ductal adenocarcinoma progression by producing suppressive eicosanoids, such as prostaglandin D2. A tuft cell in the pancreatic duct highly expresses the transcription factor POU2F3, which is essential for its development and presence.""",
                meaning=CL["4052035"]))
        setattr(cls, "CL:0002219",
            PermissibleValue(
                text="CL:0002219",
                description="""A trophoblast found at the junction of the placenta. This cell type makes a unique fibronectin-trophouteronectin junction that helps mediate attachment of the placenta to the uterus. This cell type is also found junction of the chorion layer of the external membranes and the decidua.""",
                meaning=CL["0002219"]))
        setattr(cls, "CL:4030036",
            PermissibleValue(
                text="CL:4030036",
                description="""A spermatid in an early stage of maturation that has a round morphology and is transcriptionally active.""",
                meaning=CL["4030036"]))
        setattr(cls, "CL:0002516",
            PermissibleValue(
                text="CL:0002516",
                description="""A chromaffin cell interspersed among the interrenal epithelial layer of the anterior kidney of teloest fish.""",
                meaning=CL["0002516"]))
        setattr(cls, "CL:0002636",
            PermissibleValue(
                text="CL:0002636",
                description="A nonkeratinized cell epithleial cell of the inferior part of the anal canal.",
                meaning=CL["0002636"]))
        setattr(cls, "CL:0001039",
            PermissibleValue(
                text="CL:0001039",
                description="""Osteoblast that is terminally differentiated, located adjacent to acellular or cellular bone tissue within periosteum, and is capable of mineralizing the matrix.""",
                meaning=CL["0001039"]))
        setattr(cls, "CL:0002588",
            PermissibleValue(
                text="CL:0002588",
                description="A smooth muscle cell of the umbilical vein.",
                meaning=CL["0002588"]))
        setattr(cls, "CL:1000398",
            PermissibleValue(
                text="CL:1000398",
                description="""An endothelial cell that is part of the hepatic sinusoid. These cells possess flattened areas containing perforations about 0.1 micrometers in diameter, known as fenestrae. The fenestrae are arranged in groups known as sieve plates.""",
                meaning=CL["1000398"]))
        setattr(cls, "CL:4033017",
            PermissibleValue(
                text="CL:4033017",
                description="A smooth muscle cell that is part of a bronchiole.",
                meaning=CL["4033017"]))
        setattr(cls, "CL:0000861",
            PermissibleValue(
                text="CL:0000861",
                description="""A macrophage which develops from an inflammatory monocyte and is recruited into the tissues in response to injury and infection as part of an inflammatory response. Markers include CD11b-positive, CD68-positive, and F4/80-positive.""",
                meaning=CL["0000861"]))
        setattr(cls, "CL:0000372",
            PermissibleValue(
                text="CL:0000372",
                description="""An epidermal cell that is part of a cell cluster organ of the insect integument (such as a sensillum) and that secretes a cuticular specialization that forms a socket around the base of a cuticular specialization produced by a trichogen cell.""",
                meaning=CL["0000372"]))
        setattr(cls, "CL:0000753",
            PermissibleValue(
                text="CL:0000753",
                description="""An OFF-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the outer half of the inner plexiform layer. The cell body of these cells is in the middle of the inner plexiform layer. The dendritic tree is stout and the axon terminates in sublamina 1. The axonal terminal is wide and has only a few varicosities.""",
                meaning=CL["0000753"]))
        setattr(cls, "CL:0000066",
            PermissibleValue(
                text="CL:0000066",
                description="""A cell that is usually found in a two-dimensional sheet with a free surface. The cell has a cytoskeleton that allows for tight cell to cell contact and for cell polarity where apical part is directed towards the lumen and the basal part to the basal lamina.""",
                meaning=CL["0000066"]))
        setattr(cls, "CL:1000681",
            PermissibleValue(
                text="CL:1000681",
                description="A cell that is part of an interstitial compartment of a renal cortex.",
                meaning=CL["1000681"]))
        setattr(cls, "CL:0000819",
            PermissibleValue(
                text="CL:0000819",
                description="""A B cell of distinct lineage and surface marker expression. B-1 B cells are thought to be the primary source of natural IgM immunoglobulin, that is, IgM produced in large quantities without prior antigenic stimulation and generally reactive against various microorganisms, as well as the source of T-independent IgA immunoglobulin in the mucosal areas. These cells are CD43-positive.""",
                meaning=CL["0000819"]))
        setattr(cls, "CL:0000221",
            PermissibleValue(
                text="CL:0000221",
                description="A cell of the outer of the three germ layers of the embryo.",
                meaning=CL["0000221"]))
        setattr(cls, "CL:0000842",
            PermissibleValue(
                text="CL:0000842",
                description="A leukocyte with a single non-segmented nucleus in the mature form.",
                meaning=CL["0000842"]))
        setattr(cls, "CL:0001031",
            PermissibleValue(
                text="CL:0001031",
                description="""An excitatory granule cell with a soma located in the granular layer of cerebellar cortex. A mature cerebellar granule cell has short dendrites with a characteristic claw-like appearance and a long axon that ascends to the molecular layer where it bifurcates (except in non-teleost fish, where it does not bifurcate) and extends mediolaterally to form parallel fibers.""",
                meaning=CL["0001031"]))
        setattr(cls, "CL:0000097",
            PermissibleValue(
                text="CL:0000097",
                description="""A cell that is found in almost all tissues containing numerous basophilic granules and capable of releasing large amounts of histamine and heparin upon activation. Progenitors leave bone marrow and mature in connective and mucosal tissue. Mature mast cells are found in all tissues, except the bloodstream. Their phenotype is CD117-high, CD123-negative, CD193-positive, CD200R3-positive, and FceRI-high. Stem-cell factor (KIT-ligand; SCF) is the main controlling signal of their survival and development.""",
                meaning=CL["0000097"]))
        setattr(cls, "CL:0000408",
            PermissibleValue(
                text="CL:0000408",
                description="""Any male germ cell that has characteristic some haploid and is capable of some fertilization.""",
                meaning=CL["0000408"]))
        setattr(cls, "CL:0002204",
            PermissibleValue(
                text="CL:0002204",
                description="""An epithelial cell found in various organs, including the gastrointestinal and respiratory tracts, characterized by a tuft of 120-140 blunt microvilli on its apical surface. This cell exhibits diverse functions depending on its location, which includes chemosensation, initiation of immune responses, contribution to mucociliary clearance, and defense against parasites.""",
                meaning=CL["0002204"]))
        setattr(cls, "CL:0004215",
            PermissibleValue(
                text="CL:0004215",
                description="A type 5 cone bipolar cell with narrowly stratified post synaptic terminals.",
                meaning=CL["0004215"]))
        setattr(cls, "CL:0000110",
            PermissibleValue(
                text="CL:0000110",
                description="A neuron that uses neuropeptides as transmitters.",
                meaning=CL["0000110"]))
        setattr(cls, "CL:2000040",
            PermissibleValue(
                text="CL:2000040",
                description="Any microvascular endothelial cell that is part of a urinary bladder.",
                meaning=CL["2000040"]))
        setattr(cls, "CL:1000454",
            PermissibleValue(
                text="CL:1000454",
                description="An epithelial cell that is part of the collecting duct of renal tubule.",
                meaning=CL["1000454"]))
        setattr(cls, "CL:0000822",
            PermissibleValue(
                text="CL:0000822",
                description="""A conventional B cell subject to antigenic stimulation and dependent on T cell help and with a distinct surface marker expression pattern from B-1 B cells. These cells are CD43-negative.""",
                meaning=CL["0000822"]))
        setattr(cls, "CL:0000925",
            PermissibleValue(
                text="CL:0000925",
                description="""A type I NK T cell that has been recently activated, secretes interferon-gamma and IL-4, and has the phenotype CD4-positive, CD69-positive, and downregulated NK markers.""",
                meaning=CL["0000925"]))
        setattr(cls, "CL:0002218",
            PermissibleValue(
                text="CL:0002218",
                description="""A double negative thymocyte that has a T cell receptor consisting of a gamma chain that has as part a Vgamma3 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-positive. This cell-type is found in the fetal thymus with highest numbers occurring at E17-E18.""",
                meaning=CL["0002218"]))
        setattr(cls, "CL:0002412",
            PermissibleValue(
                text="CL:0002412",
                description="""A gamma-delta receptor that expresses Vgamma1.1-Vdelta6.3 chains in the T-cell receptor.""",
                meaning=CL["0002412"]))
        setattr(cls, "CL:0004124",
            PermissibleValue(
                text="CL:0004124",
                description="A retinal ganglion cell C inner that has medium dendritic diversity.",
                meaning=CL["0004124"]))
        setattr(cls, "CL:4023039",
            PermissibleValue(
                text="CL:4023039",
                description="""Any neuron that has its soma located in some amygdala and is capable of some glutamate secretion, neurotransmission.""",
                meaning=CL["4023039"]))
        setattr(cls, "CL:0000584",
            PermissibleValue(
                text="CL:0000584",
                description="""An epithelial cell that has its apical plasma membrane folded into microvilli to provide ample surface for the absorption of nutrients from the intestinal lumen.""",
                meaning=CL["0000584"]))
        setattr(cls, "CL:2000024",
            PermissibleValue(
                text="CL:2000024",
                description="Any neuron that is part of a spinal cord medial motor column.",
                meaning=CL["2000024"]))
        setattr(cls, "CL:0000023",
            PermissibleValue(
                text="CL:0000023",
                description="A female germ cell that has entered meiosis.",
                meaning=CL["0000023"]))
        setattr(cls, "CL:0009008",
            PermissibleValue(
                text="CL:0009008",
                description="A macrophage which is resident in the lamina propria of the large intestine.",
                meaning=CL["0009008"]))
        setattr(cls, "CL:4023163",
            PermissibleValue(
                text="CL:4023163",
                description="""A bushy cell that receives only few large excitatory endbulb synapses from auditory nerves. Spherical bush cells give excitatory input to the lateral and medial parts of the superior olive.""",
                meaning=CL["4023163"]))
        setattr(cls, "CL:0000893",
            PermissibleValue(
                text="CL:0000893",
                description="An immature T cell located in the thymus.",
                meaning=CL["0000893"]))
        setattr(cls, "CL:0011000",
            PermissibleValue(
                text="CL:0011000",
                description="A CNS interneuron located in the dorsal horn of the spinal cord.",
                meaning=CL["0011000"]))
        setattr(cls, "CL:0000602",
            PermissibleValue(
                text="CL:0000602",
                description="""A receptor in the vascular system, particularly the aorta and carotid sinus, which is sensitive to stretch of the vessel walls.""",
                meaning=CL["0000602"]))
        setattr(cls, "CL:0000211",
            PermissibleValue(
                text="CL:0000211",
                description="""A cell whose function is determined by the generation or the reception of an electric signal.""",
                meaning=CL["0000211"]))
        setattr(cls, "CL:0017006",
            PermissibleValue(
                text="CL:0017006",
                description="A lymphocyte of B lineage that has gotten larger after being stimulated by an antigen.",
                meaning=CL["0017006"]))
        setattr(cls, "CL:1000507",
            PermissibleValue(
                text="CL:1000507",
                description="A cell that is part of a nephron tubule.",
                meaning=CL["1000507"]))
        setattr(cls, "CL:0000766",
            PermissibleValue(
                text="CL:0000766",
                description="A cell of the monocyte, granulocyte, or mast cell lineage.",
                meaning=CL["0000766"]))
        setattr(cls, "CL:0000362",
            PermissibleValue(
                text="CL:0000362",
                description="An epithelial cell of the integument (the outer layer of an organism).",
                meaning=CL["0000362"]))
        setattr(cls, "CL:0000022",
            PermissibleValue(
                text="CL:0000022",
                description="A stem cell that is the precursor of female gametes.",
                meaning=CL["0000022"]))
        setattr(cls, "CL:1000891",
            PermissibleValue(
                text="CL:1000891",
                description="Any kidney blood vessel cell that is part of some kidney arterial blood vessel.",
                meaning=CL["1000891"]))
        setattr(cls, "CL:1000391",
            PermissibleValue(
                text="CL:1000391",
                description="A melanocyte that is part of the eyelid.",
                meaning=CL["1000391"]))
        setattr(cls, "CL:0002631",
            PermissibleValue(
                text="CL:0002631",
                description="Any epithelial cell that is part of some upper respiratory tract epithelium.",
                meaning=CL["0002631"]))
        setattr(cls, "CL:0000941",
            PermissibleValue(
                text="CL:0000941",
                description="""A dendritic cell arising in thymus that has the phenotype CD11c-positive, CD11b-negative, and CD45RA-negative.""",
                meaning=CL["0000941"]))
        setattr(cls, "CL:0000240",
            PermissibleValue(
                text="CL:0000240",
                description="""A stratified epithelial cell that is part of squamous epithelium, characterized by multiple layers of cells. The basal layer is directly attached to the basement membrane and the apical layer consists of flattened squamous cells. This provides a protective barrier, commonly found in areas subject to abrasion, such as the skin, oral cavity, and esophagus.""",
                meaning=CL["0000240"]))
        setattr(cls, "CL:1000358",
            PermissibleValue(
                text="CL:1000358",
                description="A M cell that is part of the epithelium proper of ileum.",
                meaning=CL["1000358"]))
        setattr(cls, "CL:0001050",
            PermissibleValue(
                text="CL:0001050",
                description="A CD8-positive, alpha-beta T cell with the phenotype CCR7-negative, CD45RA-positive.",
                meaning=CL["0001050"]))
        setattr(cls, "CL:4033068",
            PermissibleValue(
                text="CL:4033068",
                description="A(n) B cell that is cycling.",
                meaning=CL["4033068"]))
        setattr(cls, "CL:0002528",
            PermissibleValue(
                text="CL:0002528",
                description="""A mature CD14-positive dermal dendritic cell is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0002528"]))
        setattr(cls, "CL:0002303",
            PermissibleValue(
                text="CL:0002303",
                description="""A cell that is part of pigmented ciliary epithelium. This cell type uptakes sodium and chloride ions from stromal interstitium and passes the ions to non-pigmented ciliary epithelial cells via gap junctions.""",
                meaning=CL["0002303"]))
        setattr(cls, "CL:0002445",
            PermissibleValue(
                text="CL:0002445",
                description="A NK1.1-positive T cell that is Ly49D-negative.",
                meaning=CL["0002445"]))
        setattr(cls, "CL:0000033",
            PermissibleValue(
                text="CL:0000033",
                description="""An exocrine cell characterized by loss of part of the cytoplasm during the process of secretion. The secreted substance is accumulated at the apical end and is either budded off through the plasma membrane producing secreted vesicles or dissolved in the cytoplasm that is lost during secretion.""",
                meaning=CL["0000033"]))
        setattr(cls, "CL:4070012",
            PermissibleValue(
                text="CL:4070012",
                description="A motor neuron that controls ventral stomach grooves leading to pyloric filter.",
                meaning=CL["4070012"]))
        setattr(cls, "CL:1000486",
            PermissibleValue(
                text="CL:1000486",
                description="""A basal cell that is part of the urothelium. Compared to other urothelial cell types, a basal cell of the urothelium is positioned along the basement membrane, is the most undifferentiated and serves a progenitor role.""",
                meaning=CL["1000486"]))
        setattr(cls, "CL:0000839",
            PermissibleValue(
                text="CL:0000839",
                description="A progenitor cell restricted to the myeloid lineage.",
                meaning=CL["0000839"]))
        setattr(cls, "CL:0003016",
            PermissibleValue(
                text="CL:0003016",
                description="""A G11 retinal ganglion cell that has post synaptic terminals in sublaminar layer S2 and is depolarized by decreased illumination of their receptive field center""",
                meaning=CL["0003016"]))
        setattr(cls, "CL:2000080",
            PermissibleValue(
                text="CL:2000080",
                description="Any mesenchymal stem cell of adipose tissue that is part of an abdomen.",
                meaning=CL["2000080"]))
        setattr(cls, "CL:0000898",
            PermissibleValue(
                text="CL:0000898",
                description="""Mature T cell not yet exposed to antigen with the phenotype CCR7-positive, CD45RA-positive, and CD127-positive. This cell type is also described as being CD25-negative, CD62L-high and CD44-low.""",
                meaning=CL["0000898"]))
        setattr(cls, "CL:0002113",
            PermissibleValue(
                text="CL:0002113",
                description="""A B220-low CD38-negative unswitched memory B cell is a CD38-negative unswitched memory B cell that has the phenotype B220-low, CD38-negative, IgD-positive, CD138-negative, and IgG-negative.""",
                meaning=CL["0002113"]))
        setattr(cls, "CL:0009038",
            PermissibleValue(
                text="CL:0009038",
                description="A macrophage that is located in the colon.",
                meaning=CL["0009038"]))
        setattr(cls, "CL:0000051",
            PermissibleValue(
                text="CL:0000051",
                description="A oligopotent progenitor cell committed to the lymphoid lineage.",
                meaning=CL["0000051"]))
        setattr(cls, "CL:0000060",
            PermissibleValue(
                text="CL:0000060",
                description="""Skeletogenic cell that secretes dentine matrix, is derived from the odontogenic papilla, and develops from a preodontoblast cell.""",
                meaning=CL["0000060"]))
        setattr(cls, "CL:0000720",
            PermissibleValue(
                text="CL:0000720",
                meaning=CL["0000720"]))
        setattr(cls, "CL:0000123",
            PermissibleValue(
                text="CL:0000123",
                meaning=CL["0000123"]))
        setattr(cls, "CL:1000347",
            PermissibleValue(
                text="CL:1000347",
                description="""An enterocyte (absorptive epithelial cell) of the colonic epithelium, characterized by a columnar shape. This cell is responsible for the absorption, transport, and metabolization of short-chain fatty acids (SCFAs) produced by gut bacteria, as well as the transport and absorption of water and electrolytes.""",
                meaning=CL["1000347"]))
        setattr(cls, "CL:0000149",
            PermissibleValue(
                text="CL:0000149",
                meaning=CL["0000149"]))
        setattr(cls, "CL:0009106",
            PermissibleValue(
                text="CL:0009106",
                description="A specialized fibroblast found in the medulla of lymph node.",
                meaning=CL["0009106"]))
        setattr(cls, "CL:1000360",
            PermissibleValue(
                text="CL:1000360",
                description="A M cell that is part of the epithelium proper of large intestine.",
                meaning=CL["1000360"]))
        setattr(cls, "CL:0000613",
            PermissibleValue(
                text="CL:0000613",
                description="""A progenitor cell committed to the basophil lineage. This cell lacks hematopoietic lineage markers (lin-negative) and is CD34-positive, T1/ST2-low, CD117-negative, and FceRIa-high. This cell also expresses Gata-1, Gata-2 and C/EBPa.""",
                meaning=CL["0000613"]))
        setattr(cls, "CL:4033055",
            PermissibleValue(
                text="CL:4033055",
                description="""A multi-ciliated epithelial cell located in ciliated duct of an airway submucosal gland, characterized by a columnar shape and motile cilia on its apical surface.""",
                meaning=CL["4033055"]))
        setattr(cls, "CL:0009074",
            PermissibleValue(
                text="CL:0009074",
                description="""A thymic medullary epithelial cell that expresses typical tuft cell markers instead of classical mTEC or cTEC markers. This population has a bulbous-like structure.""",
                meaning=CL["0009074"]))
        setattr(cls, "CL:0000688",
            PermissibleValue(
                text="CL:0000688",
                description="""A fibroblast-like cell that provides support at neuromuscular junctions in vertebrates and are localized outside the synaptic basal lamina.""",
                meaning=CL["0000688"]))
        setattr(cls, "CL:0000991",
            PermissibleValue(
                text="CL:0000991",
                description="""CD11c-negative plasmacytoid dendritic cell is a leukocyte is CD11c-negative, CD45RA-positive, CD85g-positive(ILT7), CD123-positive, CD303-positive.""",
                meaning=CL["0000991"]))
        setattr(cls, "CL:0000790",
            PermissibleValue(
                text="CL:0000790",
                description="""An alpha-beta T cell that has an immature phenotype and has not completed T cell selection.""",
                meaning=CL["0000790"]))
        setattr(cls, "CL:1000191",
            PermissibleValue(
                text="CL:1000191",
                description="""A rod-like cell in the inner ear, having their heads joined and their bases on the basilar membrane widely separated so as to form a spiral tunnel known as the tunnel of Corti.""",
                meaning=CL["1000191"]))
        setattr(cls, "CL:0000710",
            PermissibleValue(
                text="CL:0000710",
                description="Epithelial cells derived from neural plate and neural crest.",
                meaning=CL["0000710"]))
        setattr(cls, "CL:0002153",
            PermissibleValue(
                text="CL:0002153",
                description="""The dead keratin-filled squamous cell of the stratum corneum. This cell type lacks a nucleus.""",
                meaning=CL["0002153"]))
        setattr(cls, "CL:0005002",
            PermissibleValue(
                text="CL:0005002",
                description="A non-terminally differentiated cell that differentiates into a xanthophore.",
                meaning=CL["0005002"]))
        setattr(cls, "CL:4047056",
            PermissibleValue(
                text="CL:4047056",
                description="""A columnar, mucin-producing cholangiocyte that lines large bile ducts, including the hilar bile duct, right and left hepatic bile ducts, and large intrahepatic bile ducts. This cell expresses phosphorylated STAT3 and TFF-3 in humans and mice.""",
                meaning=CL["4047056"]))
        setattr(cls, "CL:0001013",
            PermissibleValue(
                text="CL:0001013",
                description="""Mature interstitial dendritic cell is a interstitial dendritic cell that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001013"]))
        setattr(cls, "CL:0009017",
            PermissibleValue(
                text="CL:0009017",
                description="""An intestinal stem cell that is located in the small intestine crypt of Liberkuhn. These stem cells reside at the bottom of crypts in the small intestine and are highly proliferative. They either differentiate into transit amplifying cells or self-renew to form new stem cells.""",
                meaning=CL["0009017"]))
        setattr(cls, "CL:0008040",
            PermissibleValue(
                text="CL:0008040",
                description="""An endothelial cell of the venule that is squamous shaped. This is in contrast to the cubodial shape of high endothelial venule cells.""",
                meaning=CL["0008040"]))
        setattr(cls, "CL:0002110",
            PermissibleValue(
                text="CL:0002110",
                description="""A B220-low CD38-positive naive B cell is a CD38-positive naive B cell that has the phenotype B220-low, CD38-positive, surface IgD-positive, surface IgM-positive, and CD27-negative, that has not yet been activated by antigen in the periphery.""",
                meaning=CL["0002110"]))
        setattr(cls, "CL:0000255",
            PermissibleValue(
                text="CL:0000255",
                description="Any cell that in taxon some Eukaryota.",
                meaning=CL["0000255"]))
        setattr(cls, "CL:1000612",
            PermissibleValue(
                text="CL:1000612",
                description="Any renal cortical epithelial cell that is part of some renal corpuscle.",
                meaning=CL["1000612"]))
        setattr(cls, "CL:3000001",
            PermissibleValue(
                text="CL:3000001",
                description="""A tissue-resident macrophage that is part of the placenta. A Hofbauer cell expresses high levels of growth factors and metalloproteinases that support vasculogenesis, angiogenesis, branching morphogenesis and tissue remodeling. A Hofbauer cell has a fetal origin, is found in the villous stroma, chorion, and amnion, and is present throughout pregnancy.""",
                meaning=CL["3000001"]))
        setattr(cls, "CL:0002274",
            PermissibleValue(
                text="CL:0002274",
                description="A cell type that secretes histamine.",
                meaning=CL["0002274"]))
        setattr(cls, "CL:0002048",
            PermissibleValue(
                text="CL:0002048",
                description="A pre-B cell precursor is CD19-low, CD22-positive , CD34-positive, CD38-positive.",
                meaning=CL["0002048"]))
        setattr(cls, "CL:0000761",
            PermissibleValue(
                text="CL:0000761",
                description="""An ON-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the inner half of the inner plexiform layer. The dendritic tree is wide and the dendritic convergence indicates cone selectivity. The axon terminal is sparsely branched and terminates in sublamina 5 of the inner plexiform layer.""",
                meaning=CL["0000761"]))
        setattr(cls, "CL:0001019",
            PermissibleValue(
                text="CL:0001019",
                meaning=CL["0001019"]))
        setattr(cls, "CL:0002269",
            PermissibleValue(
                text="CL:0002269",
                description="An endocrine cell that secretes vasoactive intestinal peptide.",
                meaning=CL["0002269"]))
        setattr(cls, "CL:0009009",
            PermissibleValue(
                text="CL:0009009",
                description="A paneth cell that is located in the epithelium of the colon.",
                meaning=CL["0009009"]))
        setattr(cls, "CL:0010016",
            PermissibleValue(
                text="CL:0010016",
                description="""A cell with a flagellum surrounded by a collar of microvilli. The motion of the flagellum draws water past the microvilli, serving either a feeding or sensory function. Collar cells are found in multiple animals, including sponges, echinoderms, and cnidarians. They are also found outside animals in the choanoflagellates. Although collar cells are superficially similar, their cytoskeletal structure and functional biology are different in different groups of organisms.""",
                meaning=CL["0010016"]))
        setattr(cls, "CL:1001603",
            PermissibleValue(
                text="CL:1001603",
                description="Circulating macrophages and tissue macrophages (alveolar macrophages) of lung.",
                meaning=CL["1001603"]))
        setattr(cls, "CL:0004217",
            PermissibleValue(
                text="CL:0004217",
                description="""A horizontal cell with a large cell body, thick dendrites, and a large dendritic arbor.""",
                meaning=CL["0004217"]))
        setattr(cls, "CL:0001040",
            PermissibleValue(
                text="CL:0001040",
                description="""Osteoblast that is non-terminally differentiated and located in cellular bone tissue or under the periosteum in acellular bone.""",
                meaning=CL["0001040"]))
        setattr(cls, "CL:0002669",
            PermissibleValue(
                text="CL:0002669",
                description="An otic fibrocyte that lines the otic capsule.",
                meaning=CL["0002669"]))
        setattr(cls, "CL:0000205",
            PermissibleValue(
                text="CL:0000205",
                description="""A cellular receptor which mediates the sense of temperature. Thermoreceptor cells in vertebrates are mostly located under the skin. In mammals there are separate types of thermoreceptors for cold and for warmth and pain receptor cells which detect cold or heat extreme enough to cause pain.""",
                meaning=CL["0000205"]))
        setattr(cls, "CL:0002294",
            PermissibleValue(
                text="CL:0002294",
                description="""An epithelial cell with a well defined Golgi apparatus that makes up the continuous layer of cells bordering the thymic tissue beneath the capsule.""",
                meaning=CL["0002294"]))
        setattr(cls, "CL:1000345",
            PermissibleValue(
                text="CL:1000345",
                description="""A paneth cell that is part of the epithelium of crypt of Lieberkuhn of small intestine.""",
                meaning=CL["1000345"]))
        setattr(cls, "CL:0009077",
            PermissibleValue(
                text="CL:0009077",
                description="A thymic epithelial cell located within the subcapsular region of the thymus.",
                meaning=CL["0009077"]))
        setattr(cls, "CL:0001201",
            PermissibleValue(
                text="CL:0001201",
                description="A B cell that is CD19-positive.",
                meaning=CL["0001201"]))
        setattr(cls, "CL:0002600",
            PermissibleValue(
                text="CL:0002600",
                description="A smooth muscle cell of the trachea.",
                meaning=CL["0002600"]))
        setattr(cls, "CL:4023030",
            PermissibleValue(
                text="CL:4023030",
                description="""A sst GABAergic cortical interneuron that has \"fanning-out' Martinotti morphology that is found in layer 2/3/5 of the cerebral cortex. They have local axon arbor and long ascending axons that spreads horizontally and arborizes significantly in L1.""",
                meaning=CL["4023030"]))
        setattr(cls, "CL:0000361",
            PermissibleValue(
                text="CL:0000361",
                description="""A cell of the embryo in the early stage following the blastula, characterized by morphogenetic cell movements, cell differentiation, and the formation of the three germ layers.""",
                meaning=CL["0000361"]))
        setattr(cls, "CL:0019022",
            PermissibleValue(
                text="CL:0019022",
                description="""An endothelial cell found in the centrilobular region hepatic sinusoid, near the central vein. The fenestrae of these cells are smaller but more numerous compared with those of endothelial cells near the periportal region of the hepatic sinusoid.""",
                meaning=CL["0019022"]))
        setattr(cls, "CL:4023170",
            PermissibleValue(
                text="CL:4023170",
                description="A trigeminal neuron that is responsible for sensation in the face.",
                meaning=CL["4023170"]))
        setattr(cls, "CL:0002475",
            PermissibleValue(
                text="CL:0002475",
                description="""A MHC-II-negative classical monocyte located in lymphoid tissue that is F4/80-positive, CD11c-intermediate, and CD11b-high.""",
                meaning=CL["0002475"]))
        setattr(cls, "CL:0000677",
            PermissibleValue(
                text="CL:0000677",
                description="""Cell of the intestinal epithelium with a brush border made up of many parallel packed microvilli; associated with absorption, particularly of macromolecules.""",
                meaning=CL["0000677"]))
        setattr(cls, "CL:0002017",
            PermissibleValue(
                text="CL:0002017",
                description="An orthochromatophilic erythroblast that is ter119-high, CD71-low, and Kit-negative.",
                meaning=CL["0002017"]))
        setattr(cls, "CL:0000680",
            PermissibleValue(
                text="CL:0000680",
                description="A non-terminally differentiated cell that is capable of developing into a muscle cell.",
                meaning=CL["0000680"]))
        setattr(cls, "CL:0003011",
            PermissibleValue(
                text="CL:0003011",
                description="""A mono-stratified retinal ganglion cell that has a large dendritic field and a sparse dendritic arbor with post synaptic terminals in sublaminar layer S4.""",
                meaning=CL["0003011"]))
        setattr(cls, "CL:1000363",
            PermissibleValue(
                text="CL:1000363",
                description="A transitional myocyte that is part of the atrial branch of anterior internodal tract.",
                meaning=CL["1000363"]))
        setattr(cls, "CL:0002220",
            PermissibleValue(
                text="CL:0002220",
                description="A cell located between the pinealocytes.",
                meaning=CL["0002220"]))
        setattr(cls, "CL:4023108",
            PermissibleValue(
                text="CL:4023108",
                description="""A magnocellular neurosecretory cell that is capable of producing and secreting oxytocin.""",
                meaning=CL["4023108"]))
        setattr(cls, "CL:0010014",
            PermissibleValue(
                text="CL:0010014",
                meaning=CL["0010014"]))
        setattr(cls, "CL:0000315",
            PermissibleValue(
                text="CL:0000315",
                description="""A cell secreting tears, the fluid secreted by the lacrimal glands. This fluid moistens the conjunctiva and cornea.""",
                meaning=CL["0000315"]))
        setattr(cls, "CL:0000155",
            PermissibleValue(
                text="CL:0000155",
                description="""An epithelial cell of the stomach that is part of the fundic gastric gland. This cell is characterized by a basally located nucleus, abundant rough endoplasmic reticulum, and large apical secretory granules. It produces and secretes pepsinogen, the inactive precursor of the digestive enzyme pepsin.""",
                meaning=CL["0000155"]))
        setattr(cls, "CL:0009022",
            PermissibleValue(
                text="CL:0009022",
                description="A stromal cell found in the lamina propria of the small intestine.",
                meaning=CL["0009022"]))
        setattr(cls, "CL:0001022",
            PermissibleValue(
                text="CL:0001022",
                description="CD115-positive monocyte is a monocyte that is CD115-positive and CD11b-positive.",
                meaning=CL["0001022"]))
        setattr(cls, "CL:1000289",
            PermissibleValue(
                text="CL:1000289",
                description="A muscle cell that is part of the atrial septal branch of anterior internodal tract.",
                meaning=CL["1000289"]))
        setattr(cls, "CL:0002076",
            PermissibleValue(
                text="CL:0002076",
                description="An epithelial cell derived from endoderm.",
                meaning=CL["0002076"]))
        setattr(cls, "CL:0001005",
            PermissibleValue(
                text="CL:0001005",
                description="""Mature CD8-alpha-positive CD11b-negative dendritic cell is a CD8-alpha-positive CD11b-negative dendritic cell that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001005"]))
        setattr(cls, "CL:0001080",
            PermissibleValue(
                text="CL:0001080",
                description="""A group 3 innate lymphoid cell in the human with the phenotype IL-7Ralpha-positive, and NKp44-negative.""",
                meaning=CL["0001080"]))
        setattr(cls, "CL:0003024",
            PermissibleValue(
                text="CL:0003024",
                description="A retinal ganglion cell C with medium cell bodies and large dendritic field.",
                meaning=CL["0003024"]))
        setattr(cls, "CL:0002448",
            PermissibleValue(
                text="CL:0002448",
                description="A NK1.1-positive T cell that is Ly49H-negative.",
                meaning=CL["0002448"]))
        setattr(cls, "CL:0009061",
            PermissibleValue(
                text="CL:0009061",
                description="An intestinal crypt stem cell that is located in the anorectum.",
                meaning=CL["0009061"]))
        setattr(cls, "CL:0000486",
            PermissibleValue(
                text="CL:0000486",
                description="""A large binucleate cell that forms a 'garland' around the anterior end of the proventriculus (cardia) at its junction with the esophagus in both adults and larvae flies. Each cell is surrounded by a basement membrane and there are numerous micro-invaginations (lacunae) extending from the surface into the cytoplasm. At the mouth of each lacuna is a doubled filament forming a specialised filtration system (diaphragm). The filtrate is endocytosed from the lacunae.""",
                meaning=CL["0000486"]))
        setattr(cls, "CL:1000372",
            PermissibleValue(
                text="CL:1000372",
                description="A transitional myocyte that is part of the atrial part of atrioventricular bundle.",
                meaning=CL["1000372"]))
        setattr(cls, "CL:0002352",
            PermissibleValue(
                text="CL:0002352",
                description="A hematopoietic stem cell that exists during embryogenesis.",
                meaning=CL["0002352"]))
        setattr(cls, "CL:1000698",
            PermissibleValue(
                text="CL:1000698",
                description="A tissue-resident macrophage that is part of some kidney.",
                meaning=CL["1000698"]))
        setattr(cls, "CL:1001436",
            PermissibleValue(
                text="CL:1001436",
                description="The subcutaneous mechanoreceptors that innervate tylotrich hair follicles.",
                meaning=CL["1001436"]))
        setattr(cls, "CL:0002347",
            PermissibleValue(
                text="CL:0002347",
                description="""A mature natural killer cell that is CD27-high and CD11b-high. This cell type is capable of interferon-gamma secretion.""",
                meaning=CL["0002347"]))
        setattr(cls, "CL:2000035",
            PermissibleValue(
                text="CL:2000035",
                description="Any neuromast mantle cell that is part of an anterior lateral line.",
                meaning=CL["2000035"]))
        setattr(cls, "CL:0009069",
            PermissibleValue(
                text="CL:0009069",
                description="""An unconventional T lymphocyte population within the thymic medulla that expresses both alpha/beta and gamma/delta T cell signatures.""",
                meaning=CL["0009069"]))
        setattr(cls, "CL:0002281",
            PermissibleValue(
                text="CL:0002281",
                description="""Scattered in duodenojejunal mucosa, this enteroendocrine cell secretes secretin and serotonin.""",
                meaning=CL["0002281"]))
        setattr(cls, "CL:4033073",
            PermissibleValue(
                text="CL:4033073",
                description="A(n) monocyte that is cycling.",
                meaning=CL["4033073"]))
        setattr(cls, "CL:0009115",
            PermissibleValue(
                text="CL:0009115",
                description="An endothelial cell located in a lymph node lymphatic vessel.",
                meaning=CL["0009115"]))
        setattr(cls, "CL:0002604",
            PermissibleValue(
                text="CL:0002604",
                description="An astrocyte that is part of the hippocampus.",
                meaning=CL["0002604"]))
        setattr(cls, "CL:0000534",
            PermissibleValue(
                text="CL:0000534",
                description="A primary neuron (sensu Teleostei) that is neither a sensory neuron or a motor neuron.",
                meaning=CL["0000534"]))
        setattr(cls, "CL:4052041",
            PermissibleValue(
                text="CL:4052041",
                description="""A tuft cell that is part of the epithelium of the pharyngotympanic (auditory) tube. This chemosensory cell is often positioned near cholinoreceptive sensory nerve fibers, suggesting a role in neuroimmune communication. It detects chemical signals and releases neuropeptides, such as acetylcholine (ACh) and CGRP, which contribute to inflammatory responses that help protect deeper tissues from harmful substances.""",
                meaning=CL["4052041"]))
        setattr(cls, "CL:0002256",
            PermissibleValue(
                text="CL:0002256",
                description="""A supportive cell that has characteristics of glial cell. Processes of this cell envelope the junctions between glomus cells and nerve endings.""",
                meaning=CL["0002256"]))
        setattr(cls, "CL:0002599",
            PermissibleValue(
                text="CL:0002599",
                description="A smooth muscle cell of the esophagus.",
                meaning=CL["0002599"]))
        setattr(cls, "CL:0002620",
            PermissibleValue(
                text="CL:0002620",
                description="A fibroblast of skin.",
                meaning=CL["0002620"]))
        setattr(cls, "CL:0000082",
            PermissibleValue(
                text="CL:0000082",
                description="An epithelial cell of the lung.",
                meaning=CL["0000082"]))
        setattr(cls, "CL:0002321",
            PermissibleValue(
                text="CL:0002321",
                description="A cell of the embryo.",
                meaning=CL["0002321"]))
        setattr(cls, "CL:0009033",
            PermissibleValue(
                text="CL:0009033",
                description="A plasma cell that is located in a vermiform appendix.",
                meaning=CL["0009033"]))
        setattr(cls, "CL:0002289",
            PermissibleValue(
                text="CL:0002289",
                description="""A densely staining taste receptor cell that contains many dense vacuoles in their apical regions which project into the apical space and bear microvilli. This cell type serves as a supporting cell by surrounding and isolating the other cell types from each other; secrete a dense amorphous material that surrounds the microvilli in the taste pore. This cell type expresses a glial glutumate transporter, GLAST.""",
                meaning=CL["0002289"]))
        setattr(cls, "CL:4033079",
            PermissibleValue(
                text="CL:4033079",
                description="A(n) endothelial cell of lymphatic vessel that is cycling.",
                meaning=CL["4033079"]))
        setattr(cls, "CL:0009058",
            PermissibleValue(
                text="CL:0009058",
                description="An enterocyte that is located in the anorectum.",
                meaning=CL["0009058"]))
        setattr(cls, "CL:4052034",
            PermissibleValue(
                text="CL:4052034",
                description="""A tuft cell that is part of the medullary epithelium of the thymus, characterized by lateral microvilli and specific markers, including L1CAM in both mice (Zhang et al., 2022) and humans (Sun et al., 2023), as well as MHC II in mice (Miller et al., 2018). This cell is pivotal in immune functions such as antigen presentation, central tolerance, and type 2 immunity. A tuft cell in the thymus exhibits characteristics of both a medullary thymic epithelial cell (mTEC) and a peripheral tuft cell. Its development is governed by transcription factors such as POU2F3.""",
                meaning=CL["4052034"]))
        setattr(cls, "CL:0000336",
            PermissibleValue(
                text="CL:0000336",
                description="""A cell found within the adrenal medulla that secrete biogenic amine hormones upon stimulation.""",
                meaning=CL["0000336"]))
        setattr(cls, "CL:4040003",
            PermissibleValue(
                text="CL:4040003",
                description="""Precursor of type II pneumocyte. These cells do not have lamellar bodies, which are a marker of type II pneumocyte maturity.""",
                meaning=CL["4040003"]))
        setattr(cls, "CL:4030006",
            PermissibleValue(
                text="CL:4030006",
                description="""An epithelial cell that is part of the fallopian tube that secretes mucus and oviduct-specific products in response to hormonal stimulation from estrogen and luteinizing hormone. This fallopian tube secretory cell is similar in height to the ciliated cell, but typically exhibits a more narrow, columnar shape. Its nucleus is ovoid and oriented perpendicular to the cell's long axis, with denser chromatin and a smaller nucleolus compared to the ciliated cell.""",
                meaning=CL["4030006"]))
        setattr(cls, "CL:0000653",
            PermissibleValue(
                text="CL:0000653",
                description="""A specialized kidney epithelial cell, contained within a glomerulus, that contains \"feet\" that interdigitate with the \"feet\" of other podocytes.""",
                meaning=CL["0000653"]))
        setattr(cls, "CL:0009066",
            PermissibleValue(
                text="CL:0009066",
                description="A stratified squamous epithelial cell that is part of the anal canal.",
                meaning=CL["0009066"]))
        setattr(cls, "CL:4023081",
            PermissibleValue(
                text="CL:4023081",
                description="""a L6 intratelencephalic projecting glutamatergic neuron of the primary motor cortex that has inverted pyramidal morphology.""",
                meaning=CL["4023081"]))
        setattr(cls, "CL:1000280",
            PermissibleValue(
                text="CL:1000280",
                description="A smooth muscle cell that is part of the colon.",
                meaning=CL["1000280"]))
        setattr(cls, "CL:2000019",
            PermissibleValue(
                text="CL:2000019",
                description="Any photoreceptor cell that is part of a compound eye.",
                meaning=CL["2000019"]))
        setattr(cls, "CL:0002064",
            PermissibleValue(
                text="CL:0002064",
                description="""A secretory cell found in pancreatic acini that secretes digestive enzymes and mucins. This cell is a typical zymogenic cell, have a basal nucleus and basophilic cytoplasm consisting of regular arrays of granular endoplasmic reticulum with mitochondria and dense secretory granules.""",
                meaning=CL["0002064"]))
        setattr(cls, "CL:0000703",
            PermissibleValue(
                text="CL:0000703",
                description="""Cell that provides some or all mechanical, nutritional and phagocytic support to their neighbors.""",
                meaning=CL["0000703"]))
        setattr(cls, "CL:1000456",
            PermissibleValue(
                text="CL:1000456",
                description="A mesothelial cell that is part of the parietal peritoneum.",
                meaning=CL["1000456"]))
        setattr(cls, "CL:0000293",
            PermissibleValue(
                text="CL:0000293",
                description="""A cell whose primary function is to provide structural support, to provide strength and physical integrity to the organism.""",
                meaning=CL["0000293"]))
        setattr(cls, "CL:4029003",
            PermissibleValue(
                text="CL:4029003",
                description="""A gamete-nursing cell that derives from the somatic tissues of the gonad (del Pino, 2021).""",
                meaning=CL["4029003"]))
        setattr(cls, "CL:0002207",
            PermissibleValue(
                text="CL:0002207",
                description="Brush cell of the epithelium in the trachea.",
                meaning=CL["0002207"]))
        setattr(cls, "CL:0000173",
            PermissibleValue(
                text="CL:0000173",
                description="""A D cell located in the pancreas. Peripherally placed within the islets like type A cells; contains somatostatin.""",
                meaning=CL["0000173"]))
        setattr(cls, "CL:0004116",
            PermissibleValue(
                text="CL:0004116",
                description="A retinal ganglion with cell medium cell bodies and medium to large dendritic fields.",
                meaning=CL["0004116"]))
        setattr(cls, "CL:0002518",
            PermissibleValue(
                text="CL:0002518",
                description="An epithelial cell of the kidney.",
                meaning=CL["0002518"]))
        setattr(cls, "CL:0002147",
            PermissibleValue(
                text="CL:0002147",
                description="""A chief cell of parathyroid glands that does not stain with hematoxylin or eosin. This cell is larger, has a larger nucleus and fewer secretory granules than dark chief cells.""",
                meaning=CL["0002147"]))
        setattr(cls, "CL:0009025",
            PermissibleValue(
                text="CL:0009025",
                description="A mesothelial cell that is part of the colon.",
                meaning=CL["0009025"]))
        setattr(cls, "CL:0000745",
            PermissibleValue(
                text="CL:0000745",
                description="""A neuron that laterally connects other neurons in the inner nuclear layer of the retina.""",
                meaning=CL["0000745"]))
        setattr(cls, "CL:4023181",
            PermissibleValue(
                text="CL:4023181",
                description="""A neurecto-epithelial cell that is part of the basal layer of the subcommissural organ and specializes in the secretion of proteins into the subarachnoid space. Hypendymal cells have similar characteristics to ependymal cells and express SCO-spondin.""",
                meaning=CL["4023181"]))
        setattr(cls, "CL:0002123",
            PermissibleValue(
                text="CL:0002123",
                description="""A B220-low CD38-positive IgG-negative memory B cell is a CD38-positive IgG-negative class switched memory B cell that lacks IgG on the cell surface with the phenotype B220-low, CD38-positive, and IgG-positive.""",
                meaning=CL["0002123"]))
        setattr(cls, "CL:0002450",
            PermissibleValue(
                text="CL:0002450",
                description="""A specialized hair cell that has an elongated kinocilium upon which an otolith accretes. The tether cell then anchors the otolith in place.""",
                meaning=CL["0002450"]))
        setattr(cls, "CL:0002093",
            PermissibleValue(
                text="CL:0002093",
                description="""A small cell formed by the second meiotic division of oocytes. In mammals, the second polar body may fail to form unless the ovum has been penetrated by a sperm cell.""",
                meaning=CL["0002093"]))
        setattr(cls, "CL:0002060",
            PermissibleValue(
                text="CL:0002060",
                description="""A melanin-containing macrophage that obtains the pigment by phagocytosis of melanosomes.""",
                meaning=CL["0002060"]))
        setattr(cls, "CL:0002142",
            PermissibleValue(
                text="CL:0002142",
                description="""A cell pyramidal in shape, with their broad ends facing and forming the greater extent of the lining of the main lumen. Secretes glycoproteins associated with mucus.""",
                meaning=CL["0002142"]))
        setattr(cls, "CL:4023114",
            PermissibleValue(
                text="CL:4023114",
                description="""A vestibular afferent neuron which posseses a unique postsynaptic terminal, the calyx, which completely covers the basolateral walls of type I hair cells and receives input from multiple ribbon synapses.""",
                meaning=CL["4023114"]))
        setattr(cls, "CL:0002287",
            PermissibleValue(
                text="CL:0002287",
                description="""A rounded, mitotically active stem cell which is the source of new cells of the taste bud; located basally.""",
                meaning=CL["0002287"]))
        setattr(cls, "CL:0000502",
            PermissibleValue(
                text="CL:0000502",
                description="""A cell found throughout the gastrointestinal tract and in the pancreas. They secrete somatostatin in both an endocrine and paracrine manner. Somatostatin inhibits gastrin, cholecystokinin, insulin, glucagon, pancreatic enzymes, and gastric hydrochloric acid. A variety of substances which inhibit gastric acid secretion (vasoactive intestinal peptide, calcitonin gene-related peptide, cholecystokinin, beta-adrenergic agonists, and gastric inhibitory peptide) are thought to act by releasing somatostatin.""",
                meaning=CL["0000502"]))
        setattr(cls, "CL:0011007",
            PermissibleValue(
                text="CL:0011007",
                description="""A cell in the area of mesoderm in the neurulating embryo that flanks and forms simultaneously with the neural tube. The cells of this region give rise to somites.""",
                meaning=CL["0011007"]))
        setattr(cls, "CL:0009054",
            PermissibleValue(
                text="CL:0009054",
                description="A microfold cell (M cell) that is part of the anorectum.",
                meaning=CL["0009054"]))
        setattr(cls, "CL:0000026",
            PermissibleValue(
                text="CL:0000026",
                description="""A germline cell that contributes to the development of the oocyte by transferring cytoplasm directly to oocyte.""",
                meaning=CL["0000026"]))
        setattr(cls, "CL:0009092",
            PermissibleValue(
                text="CL:0009092",
                description="An endothelial cell that is part of a placenta.",
                meaning=CL["0009092"]))
        setattr(cls, "CL:0002348",
            PermissibleValue(
                text="CL:0002348",
                description="""A CD27-low, CD11b-high natural killer cell that has a higher threshold of activation due to higher expression of inhibitory receptors.""",
                meaning=CL["0002348"]))
        setattr(cls, "CL:0001028",
            PermissibleValue(
                text="CL:0001028",
                description="""CD7-positive lymphoid progenitor cell is a lymphoid progenitor cell that is CD34-positive, CD7-positive and is CD45RA-negative.""",
                meaning=CL["0001028"]))
        setattr(cls, "CL:4033012",
            PermissibleValue(
                text="CL:4033012",
                description="""A(n) smooth muscle cell that is part of a(n) large intestine smooth muscle longitudinal layer.""",
                meaning=CL["4033012"]))
        setattr(cls, "CL:1000245",
            PermissibleValue(
                text="CL:1000245",
                description="""Any peripheral nervous system neuron that has its soma located in some posterior lateral line ganglion.""",
                meaning=CL["1000245"]))
        setattr(cls, "CL:0002458",
            PermissibleValue(
                text="CL:0002458",
                description="A dermal dendritic cell that is langerin-positive and CD103-positive.",
                meaning=CL["0002458"]))
        setattr(cls, "CL:0000780",
            PermissibleValue(
                text="CL:0000780",
                description="""A specialized multinuclear osteoclast associated with the absorption and removal of cementum.""",
                meaning=CL["0000780"]))
        setattr(cls, "CL:1001217",
            PermissibleValue(
                text="CL:1001217",
                description="Any smooth muscle cell that is part of some interlobular artery.",
                meaning=CL["1001217"]))
        setattr(cls, "CL:1000309",
            PermissibleValue(
                text="CL:1000309",
                description="An adipocyte that is part of the epicardial fat.",
                meaning=CL["1000309"]))
        setattr(cls, "CL:4033025",
            PermissibleValue(
                text="CL:4033025",
                description="""A fibroblast that is part of the fibrous layer of the perichondrium. This cell is responsible for collagen fiber production.""",
                meaning=CL["4033025"]))
        setattr(cls, "CL:0000309",
            PermissibleValue(
                text="CL:0000309",
                meaning=CL["0000309"]))
        setattr(cls, "CL:0002659",
            PermissibleValue(
                text="CL:0002659",
                description="A glandular epithelial cell that is part of the stomach.",
                meaning=CL["0002659"]))
        setattr(cls, "CL:0000982",
            PermissibleValue(
                text="CL:0000982",
                description="A plasmablast that secretes IgG.",
                meaning=CL["0000982"]))
        setattr(cls, "CL:4023160",
            PermissibleValue(
                text="CL:4023160",
                description="""A neuron of the dorsal cochlear nucleus with spiny dendrites that receive input from the axons of granule cells and with axons that release GABA and glycine onto cartwheel, pyramidal and giant cell targets.""",
                meaning=CL["4023160"]))
        setattr(cls, "CL:0000969",
            PermissibleValue(
                text="CL:0000969",
                description="""A mature B cell that has the phenotype CD1d-positive and expresses interleukin-10. This cell type has been associated with suppression of chronic inflammatory responses and T cell responses.""",
                meaning=CL["0000969"]))
        setattr(cls, "CL:0001020",
            PermissibleValue(
                text="CL:0001020",
                description="""Mature CD8-alpha-low Langerhans cell is a CD8-alpha-low Langerhans cell that that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001020"]))
        setattr(cls, "CL:2000055",
            PermissibleValue(
                text="CL:2000055",
                description="Any dendritic cell that is part of a liver.",
                meaning=CL["2000055"]))
        setattr(cls, "CL:0002267",
            PermissibleValue(
                text="CL:0002267",
                description="A type D cell found in the stomach.",
                meaning=CL["0002267"]))
        setattr(cls, "CL:0000553",
            PermissibleValue(
                text="CL:0000553",
                description="""The earliest cytologically identifiable precursor in the thrombocytic series. This cell is capable of endomitosis and lacks expression of hematopoieitic lineage markers (lin-negative).""",
                meaning=CL["0000553"]))
        setattr(cls, "CL:4023013",
            PermissibleValue(
                text="CL:4023013",
                description="A glutamatergic neuron located in the cerebral cortex that projects to the thalamus.",
                meaning=CL["4023013"]))
        setattr(cls, "CL:2000027",
            PermissibleValue(
                text="CL:2000027",
                description="Any basket cell that is part of a cerebellum.",
                meaning=CL["2000027"]))
        setattr(cls, "CL:0002401",
            PermissibleValue(
                text="CL:0002401",
                description="""A thymocyte that has a T cell receptor consisting of a gamma chain that has as part a Vgamma3 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-negative. This cell-type is found in the fetal thymus with highest numbers occurring at E17-E18.""",
                meaning=CL["0002401"]))
        setattr(cls, "CL:0002094",
            PermissibleValue(
                text="CL:0002094",
                description="A cell that makes up the loose connective tissue of the ovary.",
                meaning=CL["0002094"]))
        setattr(cls, "CL:0007001",
            PermissibleValue(
                text="CL:0007001",
                description="""Cell that has the potential to form a skeletal cell type (e.g. cells in periosteum, cells in marrow) and produce extracellular matrix (often mineralized) and skeletal tissue (often mineralized).""",
                meaning=CL["0007001"]))
        setattr(cls, "CL:0002279",
            PermissibleValue(
                text="CL:0002279",
                description="""A enteroendocrine cell type that is numerous in ileum, present in jejunum and large intestine, few in duodenum. This cell type produces glucagon-like immunoreactants (glicentin, glucagon-37, glucagon-29, GLP-1 and -2) and PYY.""",
                meaning=CL["0002279"]))
        setattr(cls, "CL:0000858",
            PermissibleValue(
                text="CL:0000858",
                description="A skeletal muscle myoblast that differentiates into fast muscle fibers.",
                meaning=CL["0000858"]))
        setattr(cls, "CL:2000044",
            PermissibleValue(
                text="CL:2000044",
                description="Any microvascular endothelial cell that is part of a brain.",
                meaning=CL["2000044"]))
        setattr(cls, "CL:0002531",
            PermissibleValue(
                text="CL:0002531",
                description="""A mature CD1a-positive dermal dendritic cell is CD80-high, CD83-positive, CD86-high, and MHCII-high.""",
                meaning=CL["0002531"]))
        setattr(cls, "CL:0002358",
            PermissibleValue(
                text="CL:0002358",
                description="""Derived from the Greek word pyren (the pit of a stone fruit), this is a transient nucleated cell type that results from exclusion of the nucleus from the primitive erythrocyte.""",
                meaning=CL["0002358"]))
        setattr(cls, "CL:0002430",
            PermissibleValue(
                text="CL:0002430",
                description="""A double-positive thymocyte that is undergoing positive selection, has high expression of the alpha-beta T cell receptor, is CD69-positive, and is in the process of down regulating the CD4 co-receptor.""",
                meaning=CL["0002430"]))
        setattr(cls, "CL:4030067",
            PermissibleValue(
                text="CL:4030067",
                description="A near-projecting glutamatergic neuron with a soma found in cortical layer 5/6.",
                meaning=CL["4030067"]))
        setattr(cls, "CL:0002411",
            PermissibleValue(
                text="CL:0002411",
                description="""A gamma-delta receptor that expresses Vgamma1.1 but does not express Vdelta6.3 chains in the T-cell receptor.""",
                meaning=CL["0002411"]))
        setattr(cls, "CL:0008028",
            PermissibleValue(
                text="CL:0008028",
                description="Any neuron that is capable of part of some visual perception.",
                meaning=CL["0008028"]))
        setattr(cls, "CL:0000894",
            PermissibleValue(
                text="CL:0000894",
                description="""A pro-T cell that has the phenotype CD4-negative, CD8-negative, CD44-positive, and CD25-negative.""",
                meaning=CL["0000894"]))
        setattr(cls, "CL:4023047",
            PermissibleValue(
                text="CL:4023047",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in cortical layer 2/3 of the primary motor cortex.""",
                meaning=CL["4023047"]))
        setattr(cls, "CL:0000985",
            PermissibleValue(
                text="CL:0000985",
                description="A fully differentiated plasma cell that secretes IgG.",
                meaning=CL["0000985"]))
        setattr(cls, "CL:0002538",
            PermissibleValue(
                text="CL:0002538",
                description="""An epithelial cell of the intrahepatic portion of the bile duct. These cells are flattened or cuboidal in shape, and have a small nuclear-to-cytoplasmic ratio relative to large/extrahepatic cholangiocytes.""",
                meaning=CL["0002538"]))
        setattr(cls, "CL:0002557",
            PermissibleValue(
                text="CL:0002557",
                description="A fibroblast of pulmonary artery.",
                meaning=CL["0002557"]))
        setattr(cls, "CL:0009112",
            PermissibleValue(
                text="CL:0009112",
                description="A germinal center B cell found in a lymph node germinal center dark zone.",
                meaning=CL["0009112"]))
        setattr(cls, "CL:0000921",
            PermissibleValue(
                text="CL:0000921",
                description="""An alpha-beta T cell expressing NK cell markers that is CD1d restricted and expresses specific V-alpha chains. NK T cells of this type recognize the glycolipid alpha-galactosylceramide in the context of CD1d.""",
                meaning=CL["0000921"]))
        setattr(cls, "CL:0002160",
            PermissibleValue(
                text="CL:0002160",
                description="""A cell type found in the basal epithelial layer on the external side of the tympanic membrane. Cell type is flattened with intracellular spaces of variable dimensions.""",
                meaning=CL["0002160"]))
        setattr(cls, "CL:4047018",
            PermissibleValue(
                text="CL:4047018",
                description="""An enterocyte that is part of the colon, in the early stages of differentiation, located in the intestinal crypt-villus axis.""",
                meaning=CL["4047018"]))
        setattr(cls, "CL:0002300",
            PermissibleValue(
                text="CL:0002300",
                description="""A small medullary thymic epithelial cell with a spindle shape, often arranged in groups and connected to each other by large desmosomes and interdigitations. The cytoplasm is sparse, with scanty organelles and thick bundles of cytokeratin.""",
                meaning=CL["0002300"]))
        setattr(cls, "CL:0009007",
            PermissibleValue(
                text="CL:0009007",
                description="A macrophage which is resident in the lamina propria of the small intestine.",
                meaning=CL["0009007"]))
        setattr(cls, "CL:0000768",
            PermissibleValue(
                text="CL:0000768",
                description="""Any of the immature forms of a basophil, in which basophilic specific granules are present but other phenotypic features of the mature form may be lacking.""",
                meaning=CL["0000768"]))
        setattr(cls, "CL:0000036",
            PermissibleValue(
                text="CL:0000036",
                meaning=CL["0000036"]))
        setattr(cls, "CL:0000693",
            PermissibleValue(
                text="CL:0000693",
                description="""An interneuron that has spider-like appearance with a small round soma, a large number (7-10) of short, smooth, or slightly beaded primary dendrites that give rise to only a few secondary branches, and a branched axon that establishes a dense axonal mesh with thin shafts.""",
                meaning=CL["0000693"]))
        setattr(cls, "CL:0002295",
            PermissibleValue(
                text="CL:0002295",
                description="""A thymic epithelial cell that has an eccentric, round, or irregularly shaped hetero or euchromatic nucleus. The hallmark of this cell type is the presence of vacuoles, which are clustered in one area of the cytoplasm in the vicinity of the nucleus. The vacuoles are small and acquire a grape-like form, occasionally showing delicate internal microvillous projections.""",
                meaning=CL["0002295"]))
        setattr(cls, "CL:0002388",
            PermissibleValue(
                text="CL:0002388",
                description="An arthroconidium that has more than one nucleus.",
                meaning=CL["0002388"]))
        setattr(cls, "CL:0000909",
            PermissibleValue(
                text="CL:0000909",
                description="A CD8-positive, alpha-beta T cell that has differentiated into a memory T cell.",
                meaning=CL["0000909"]))
        setattr(cls, "CL:0019020",
            PermissibleValue(
                text="CL:0019020",
                description="""An epithelial cell of the extrahepatic bile ducts, including the left and right hepatic duct, common hepatic duct, and common bile duct. They are columnar in shape, and have a large nuclear-to-cytoplasmic ratio relative to small/intrahepatic cholangiocytes.""",
                meaning=CL["0019020"]))
        setattr(cls, "CL:4052052",
            PermissibleValue(
                text="CL:4052052",
                description="""A uterine natural killer subset that is present in the endometrial lining during the non-pregnant state (Garcia-Alonso et al., 2021) and in the decidua during pregnancy (Vento-Tormo et al., 2018), peaking in the first trimester. It expresses the uterine resident marker CD49a and is distinguished from uNK1 and uNK3 by the absence of CD39, CD103 (Whettlock et al., 2022), and CD160 (Marečková et al., 2024), with ITGB2 serving as a defining marker (Vento-Tormo et al., 2018). Functionally, it produces more cytokines upon stimulation than uNK1, suggesting a role in immune defense, and secretes XCL1 chemokines, facilitating interactions with maternal dendritic cells and fetal extravillous trophoblasts (Vento-Tormo et al., 2018).""",
                meaning=CL["4052052"]))
        setattr(cls, "CL:4023074",
            PermissibleValue(
                text="CL:4023074",
                description="A neuron that has its soma located in the mammillary body.",
                meaning=CL["4023074"]))
        setattr(cls, "CL:4023109",
            PermissibleValue(
                text="CL:4023109",
                description="""A magnocellular neurosecretory cell that is capable of producing and secreting vasopressin.""",
                meaning=CL["4023109"]))
        setattr(cls, "CL:0013000",
            PermissibleValue(
                text="CL:0013000",
                description="Any radial glial cell that is part of some forebrain.",
                meaning=CL["0013000"]))
        setattr(cls, "CL:0000583",
            PermissibleValue(
                text="CL:0000583",
                description="""A tissue-resident macrophage found in the alveoli of the lungs. Ingests small inhaled particles resulting in degradation and presentation of the antigen to immunocompetent cells. Markers include F4/80-positive, CD11b-/low, CD11c-positive, CD68-positive, sialoadhesin-positive, dectin-1-positive, MR-positive, CX3CR1-negative.""",
                meaning=CL["0000583"]))
        setattr(cls, "CL:4042017",
            PermissibleValue(
                text="CL:4042017",
                description="""The dorsal-most tanycyte type of the third venticle.  These cells projects into the ventromedial or dorsomedial nucleus of the hypothalamus. This type of tanycyte extends its protrusions close to parenchymal neurons without contacting blood vessels. It expresses the glial marker S-100β.""",
                meaning=CL["4042017"]))
        setattr(cls, "CL:0000694",
            PermissibleValue(
                text="CL:0000694",
                meaning=CL["0000694"]))
        setattr(cls, "CL:0002050",
            PermissibleValue(
                text="CL:0002050",
                description="""A pre-BCR-positive precursor B cell that is CD24-high, CD25-positive, CD43-positive, CD45R-positive and BP-positive.""",
                meaning=CL["0002050"]))
        setattr(cls, "CL:0003027",
            PermissibleValue(
                text="CL:0003027",
                description="""A bistratified retinal ganglion cell D cell that has medium dendritic arbor and a large dendritic field that terminates in S2 and S4.""",
                meaning=CL["0003027"]))
        setattr(cls, "CL:0001044",
            PermissibleValue(
                text="CL:0001044",
                description="A CD4-positive, alpha-beta T cell with the phenotype CCR7-negative, CD45RA-positive.",
                meaning=CL["0001044"]))
        setattr(cls, "CL:0000348",
            PermissibleValue(
                text="CL:0000348",
                description="A structural cell that is part of optic choroid.",
                meaning=CL["0000348"]))
        setattr(cls, "CL:0000001",
            PermissibleValue(
                text="CL:0000001",
                description="""A cultured cell that is freshly isolated from a organismal source, or derives in culture from such a cell prior to the culture being passaged.""",
                meaning=CL["0000001"]))
        setattr(cls, "CL:0002640",
            PermissibleValue(
                text="CL:0002640",
                description="An epithelial fate stem cell derived form the amnion membrane.",
                meaning=CL["0002640"]))
        setattr(cls, "CL:1001430",
            PermissibleValue(
                text="CL:1001430",
                description="""A urothelial cell that is part of the urethra urothelium. This cell plays a crucial role in maintaining the urethral barrier function, protecting against toxic substances in urine, sensing environmental changes, and defending against pathogen entry.""",
                meaning=CL["1001430"]))
        setattr(cls, "CL:1000085",
            PermissibleValue(
                text="CL:1000085",
                meaning=CL["1000085"]))
        setattr(cls, "CL:4030025",
            PermissibleValue(
                text="CL:4030025",
                description="A fibroblast that is located in the renal cortical interstitium.",
                meaning=CL["4030025"]))
        setattr(cls, "CL:0011017",
            PermissibleValue(
                text="CL:0011017",
                description="""Cell that is part of the vagal neural crest population. The vagal neural crest arises from the axial level of somites 1-7 and has been described as a hybrid between the head and the trunk populations.""",
                meaning=CL["0011017"]))
        setattr(cls, "CL:0000990",
            PermissibleValue(
                text="CL:0000990",
                description="Conventional dendritic cell is a dendritic cell that is CD11c-high.",
                meaning=CL["0000990"]))
        setattr(cls, "CL:0010021",
            PermissibleValue(
                text="CL:0010021",
                description="Any myoblast that develops into some cardiac muscle cell.",
                meaning=CL["0010021"]))
        setattr(cls, "CL:0000509",
            PermissibleValue(
                text="CL:0000509",
                description="A peptide hormone secreting cell that secretes gastrin.",
                meaning=CL["0000509"]))
        setattr(cls, "CL:0009068",
            PermissibleValue(
                text="CL:0009068",
                description="""An unconventional T lymphocyte population within the thymic medulla that is potentially a thymic resident population.""",
                meaning=CL["0009068"]))
        setattr(cls, "CL:0000131",
            PermissibleValue(
                text="CL:0000131",
                description="""An endothelial cell that lines the blood and lymphatic vessels of the digestive tract. This cell forms the gut–vascular barrier (GVB) through tight junctions and crosstalk with pericytes and enteric glial cells, regulating the passage of nutrients and immune cells while restricting microbial translocation into the bloodstream.""",
                meaning=CL["0000131"]))
        setattr(cls, "CL:4052016",
            PermissibleValue(
                text="CL:4052016",
                description="""A capillary endothelial cell that is part of the pituitary gland. This cell is characterized by its fenestrated structure which facilitates the efficient transport of hormones and other signaling molecules, essential for endocrine signalling.""",
                meaning=CL["4052016"]))
        setattr(cls, "CL:4033088",
            PermissibleValue(
                text="CL:4033088",
                description="""A resident macrophage that is part of the decidua. Some decidual macrophages are derived from maternal blood monocytes that are recruited to the uterus shortly after conception. The main functions of a decidual macrophage are implantation, placental development, immune regulation and vascular remodeling.""",
                meaning=CL["4033088"]))
        setattr(cls, "CL:4023124",
            PermissibleValue(
                text="CL:4023124",
                description="A kisspeptin neuron that is located in the dentate gyrus of the hippocampus.",
                meaning=CL["4023124"]))
        setattr(cls, "CL:0002105",
            PermissibleValue(
                text="CL:0002105",
                description="""A CD38-positive IgG memory B cell is a class switched memory B cell that expresses IgG on the cell surface with the phenotype CD38-positive and IgG-positive.""",
                meaning=CL["0002105"]))
        setattr(cls, "CL:0002112",
            PermissibleValue(
                text="CL:0002112",
                description="""A B220-positive CD38-negative unswitched memory B cell is a CD38-negative unswitched memory B cell that has the phenotype B220-positive, CD38-negative, IgD-positive, CD138-negative, and IgG-negative.""",
                meaning=CL["0002112"]))
        setattr(cls, "CL:1000333",
            PermissibleValue(
                text="CL:1000333",
                description="A serous secreting cell that is part of the epithelium of bronchiole.",
                meaning=CL["1000333"]))
        setattr(cls, "CL:1000714",
            PermissibleValue(
                text="CL:1000714",
                description="Any renal principal cell that is part of some cortical collecting duct.",
                meaning=CL["1000714"]))
        setattr(cls, "CL:0000165",
            PermissibleValue(
                text="CL:0000165",
                description="A neuron that is capable of some hormone secretion in response to neuronal signals.",
                meaning=CL["0000165"]))
        setattr(cls, "CL:0002602",
            PermissibleValue(
                text="CL:0002602",
                description="""Any connective tissue cell that is part of some annulus fibrosus disci intervertebralis.""",
                meaning=CL["0002602"]))
        setattr(cls, "CL:2000096",
            PermissibleValue(
                text="CL:2000096",
                description="Any fibroblast that is part of a reticular layer of dermis.",
                meaning=CL["2000096"]))
        setattr(cls, "CL:0002596",
            PermissibleValue(
                text="CL:0002596",
                description="Smooth muscle cell of the carotid artery.",
                meaning=CL["0002596"]))
        setattr(cls, "CL:0002564",
            PermissibleValue(
                text="CL:0002564",
                description="A connective tissue cell of the nucleus pulposus cell of intervertebral disc.",
                meaning=CL["0002564"]))
        setattr(cls, "CL:0000563",
            PermissibleValue(
                text="CL:0000563",
                description="""A rounded, inactive form that certain bacteria assume under conditions of extreme temperature, dryness, or lack of food. The bacterium develops a waterproof cell wall that protects it from being dried out or damaged.""",
                meaning=CL["0000563"]))
        setattr(cls, "CL:0002045",
            PermissibleValue(
                text="CL:0002045",
                description="""A pro-B cell that is CD45R/B220-positive, CD43-positive, HSA-low, BP-1-negative and Ly6c-negative. This cell type is also described as being lin-negative, AA4-positive, Kit-positive, IL7Ra-positive and CD45R-positive.""",
                meaning=CL["0002045"]))
        setattr(cls, "CL:0000313",
            PermissibleValue(
                text="CL:0000313",
                description="""Columnar glandular cell with irregular nucleus, copious granular endoplasmic reticulum and supranuclear granules. Secretes a watery fluid containing proteins known as serous fluid.""",
                meaning=CL["0000313"]))
        setattr(cls, "CL:1000457",
            PermissibleValue(
                text="CL:1000457",
                description="A mesothelial cell that is part of the visceral peritoneum.",
                meaning=CL["1000457"]))
        setattr(cls, "CL:0000560",
            PermissibleValue(
                text="CL:0000560",
                description="""A late neutrophilic metamyelocyte in which the nucleus is indented to more than half the distance to the farthest nuclear margin but in no area being condensed to a single filament. The nucleus is in the form of a curved or coiled band, not having acquired the typical multilobar shape of the mature neutrophil. These cells are fMLP receptor-positive, CD11b-positive, CD35-negative, and CD49d-negative.""",
                meaning=CL["0000560"]))
        setattr(cls, "CL:0000813",
            PermissibleValue(
                text="CL:0000813",
                description="""A long-lived, antigen-experienced T cell that has acquired a memory phenotype including distinct surface markers and the ability to differentiate into an effector T cell upon antigen reexposure.""",
                meaning=CL["0000813"]))
        setattr(cls, "CL:0011100",
            PermissibleValue(
                text="CL:0011100",
                description="Neuron that secretes the neurotransmitter galanin.",
                meaning=CL["0011100"]))
        setattr(cls, "CL:0002513",
            PermissibleValue(
                text="CL:0002513",
                description="""A CD8-alpha alpha positive gamma-delta intraepithelial T cell that expresses a TCR encoded in part by the Vgamma5 gene segment.""",
                meaning=CL["0002513"]))
        setattr(cls, "CL:4023125",
            PermissibleValue(
                text="CL:4023125",
                description="""A hypothalamus kisspeptin neuron that coexpresses kisspeptin, neurokinin B and dynorphin.""",
                meaning=CL["4023125"]))
        setattr(cls, "CL:0001076",
            PermissibleValue(
                text="CL:0001076",
                description="""An innate lymphoid cell in the human with the phenotype NKp46-positive that is a precusor for NK cells and ILC3 cells.""",
                meaning=CL["0001076"]))
        setattr(cls, "CL:0000897",
            PermissibleValue(
                text="CL:0000897",
                description="A CD4-positive, alpha-beta T cell that has differentiated into a memory T cell.",
                meaning=CL["0000897"]))
        setattr(cls, "CL:4033051",
            PermissibleValue(
                text="CL:4033051",
                description="""A parasol ganglion cell that depolarizes in response to decreased light intensity in the center of its receptive field. The majority of input that this cell receives comes from DB3a bipolar cells.""",
                meaning=CL["4033051"]))
        setattr(cls, "CL:0002677",
            PermissibleValue(
                text="CL:0002677",
                description="A regulatory T cell that has not encountered antigen.",
                meaning=CL["0002677"]))
        setattr(cls, "CL:0002250",
            PermissibleValue(
                text="CL:0002250",
                description="""A stem cell located in epithelium the based of the crypt of Lieberkuhn. Division of these cells serve both to maintain the stem cell population and produce the transit amplifying cells that are all precursors of all cell types that populate the intestinal epithelium.""",
                meaning=CL["0002250"]))
        setattr(cls, "CL:4052008",
            PermissibleValue(
                text="CL:4052008",
                description="""A subepithelial intestinal fibroblast that is located adjacent to the base of the crypt of Lieberkühn, near the intestinal stem cells. Characterized by low PDGFRα expression, this cell is crucial for maintaining the intestinal stem cell niche. Crypt-bottom fibroblast secretes key signaling molecules including canonical Wnt ligands (Wnt2, Wnt2b), Wnt potentiators (Rspo3), and BMP inhibitors (Grem1), which collectively regulate intestinal stem cell function and epithelial homeostasis.""",
                meaning=CL["4052008"]))
        setattr(cls, "CL:2000051",
            PermissibleValue(
                text="CL:2000051",
                description="Any fibroblast that is part of a spleen.",
                meaning=CL["2000051"]))
        setattr(cls, "CL:0000172",
            PermissibleValue(
                text="CL:0000172",
                description="Any secretory cell that is capable of some somatostatin secretion.",
                meaning=CL["0000172"]))
        setattr(cls, "CL:0000641",
            PermissibleValue(
                text="CL:0000641",
                description="A cell that is resistant to stains.",
                meaning=CL["0000641"]))
        setattr(cls, "CL:4042006",
            PermissibleValue(
                text="CL:4042006",
                description="""A border associated macrophage which is part of a dura matter. This macrophage phagocytoses intruding pathogens and foreign molecules detected in the bloodstream or in the cerebrospinal fluid. This cell has an amoeboid body with dynamic protrusions in homeostasis.""",
                meaning=CL["4042006"]))
        setattr(cls, "CL:0004241",
            PermissibleValue(
                text="CL:0004241",
                description="""An amacrine cell with a wide dendritic field, dendrites in S2, and post-synaptic terminals in S1.""",
                meaning=CL["0004241"]))
        setattr(cls, "CL:0008002",
            PermissibleValue(
                text="CL:0008002",
                description="""A transversely striated, synctial cell of skeletal muscle. It is formed when proliferating myoblasts exit the cell cycle, differentiate and fuse.""",
                meaning=CL["0008002"]))
        setattr(cls, "CL:4023028",
            PermissibleValue(
                text="CL:4023028",
                description="""A sst GABAergic cortical interneuron with a soma found in lower L5 with mostly local axonal arborization but with some sparse ascending axons. L5 non-Martinotti sst cells show somatic localization and local axon plexus in L5b and L5b/6 and substantial innervation of L3 and L4, and receive thalamic input from the ventral posteromedial nucleus and specifically target L4 neurons, avoiding L5 pyramidal cells. L5 non-Martinotti sst cells tend to show a higher input resistance and seem to be less stuttering.""",
                meaning=CL["4023028"]))
        setattr(cls, "CL:4030032",
            PermissibleValue(
                text="CL:4030032",
                description="""An interstitial cell that is part of a cardiac valve leaflet. Along with valve endothelial cells, a valve interstitial cell maintains tissue homeostasis for the function of cardiac valves through secreting biochemical signals, matrix proteins and matrix remodeling enzymes.""",
                meaning=CL["4030032"]))
        setattr(cls, "CL:0011110",
            PermissibleValue(
                text="CL:0011110",
                description="Neuron that secretes histamine.",
                meaning=CL["0011110"]))
        setattr(cls, "CL:4033081",
            PermissibleValue(
                text="CL:4033081",
                description="A(n) myeloid cell that is cycling.",
                meaning=CL["4033081"]))
        setattr(cls, "CL:2000000",
            PermissibleValue(
                text="CL:2000000",
                description="Any melanocyte that is part of a epidermis.",
                meaning=CL["2000000"]))
        setattr(cls, "CL:0011030",
            PermissibleValue(
                text="CL:0011030",
                description="Any microvascular endothelial cell that is part of the dermis.",
                meaning=CL["0011030"]))
        setattr(cls, "CL:1000383",
            PermissibleValue(
                text="CL:1000383",
                description="""A type II vestibular sensory cell that is part of the epithelium of macula of utricle of membranous labyrinth.""",
                meaning=CL["1000383"]))
        setattr(cls, "CL:0000571",
            PermissibleValue(
                text="CL:0000571",
                description="""A pigment cell derived from the neural crest. Contains uric acid or other purine crystals deposited in stacks called leucosomes. The crystals reflect light and this gives a white appearance under white light.""",
                meaning=CL["0000571"]))
        setattr(cls, "CL:0002583",
            PermissibleValue(
                text="CL:0002583",
                description="A preadipocyte that is part of subcutaneous tissue.",
                meaning=CL["0002583"]))
        setattr(cls, "CL:0000735",
            PermissibleValue(
                text="CL:0000735",
                description="A hemocyte that derives from the larval lymph gland.",
                meaning=CL["0000735"]))
        setattr(cls, "CL:0000762",
            PermissibleValue(
                text="CL:0000762",
                description="""A nucleated blood cell involved in coagulation, typically seen in birds and other non-mammalian vertebrates.""",
                meaning=CL["0000762"]))
        setattr(cls, "CL:1000850",
            PermissibleValue(
                text="CL:1000850",
                description="""An epithelial cell that is part of the macula densa, characterized by a tightly packed arrangement, apically positioned nuclei, and prominent primary cilia, creating a distinctive 'dense spot' appearance under microscopy. It is involved in regulating renal blood flow, glomerular filtration rate, and renin release.""",
                meaning=CL["1000850"]))
        setattr(cls, "CL:0000311",
            PermissibleValue(
                text="CL:0000311",
                meaning=CL["0000311"]))
        setattr(cls, "CL:0000128",
            PermissibleValue(
                text="CL:0000128",
                description="""A class of large neuroglial (macroglial) cells in the central nervous system. Form the insulating myelin sheath of axons in the central nervous system.""",
                meaning=CL["0000128"]))
        setattr(cls, "CL:1000322",
            PermissibleValue(
                text="CL:1000322",
                description="A goblet cell that is part of the epithelium of pancreatic duct.",
                meaning=CL["1000322"]))
        setattr(cls, "CL:0000569",
            PermissibleValue(
                text="CL:0000569",
                description="""A mesenchymal cell found in the developing heart and that develops into some part of the heart.  These cells derive from intra- and extra-cardiac sources, including the endocardium, epicardium, neural crest, and second heart field.""",
                meaning=CL["0000569"]))
        setattr(cls, "CL:1000365",
            PermissibleValue(
                text="CL:1000365",
                description="""A transitional myocyte that is part of the atrial septal branch of anterior internodal tract.""",
                meaning=CL["1000365"]))
        setattr(cls, "CL:0000629",
            PermissibleValue(
                text="CL:0000629",
                description="""A cell that is specialized to store a particular substance(s), which is(are) later released from the store for a particular purpose.""",
                meaning=CL["0000629"]))
        setattr(cls, "CL:0000751",
            PermissibleValue(
                text="CL:0000751",
                description="""A bipolar neuron found in the retina that is synapsed by rod photoreceptor cells but not by cone photoreceptor cells.  These neurons depolarize in response to light.""",
                meaning=CL["0000751"]))
        setattr(cls, "CL:0000219",
            PermissibleValue(
                text="CL:0000219",
                description="A cell that moves by its own activities.",
                meaning=CL["0000219"]))
        setattr(cls, "CL:2000052",
            PermissibleValue(
                text="CL:2000052",
                description="Any endothelial cell of artery that is part of a umbilical cord.",
                meaning=CL["2000052"]))
        setattr(cls, "CL:0002068",
            PermissibleValue(
                text="CL:0002068",
                description="""Specialized cardiac myocyte that is subendocardially interspersed with the regular cardiac muscle cell. They are uninucleate cylindrical cells, associated end-to-end in long rows, continue from the node to the atrioventricular bundle; relatively short compared to ordinary myocytes but are nearly twice their diameter.""",
                meaning=CL["0002068"]))
        setattr(cls, "CL:0000373",
            PermissibleValue(
                text="CL:0000373",
                description="""A progenitor cell found in the larval epidermis of insects and that gives rise to the adult abdominal epidermis.""",
                meaning=CL["0000373"]))
        setattr(cls, "CL:1000550",
            PermissibleValue(
                text="CL:1000550",
                description="Any kidney cell that is part of some papillary duct.",
                meaning=CL["1000550"]))
        setattr(cls, "CL:0002490",
            PermissibleValue(
                text="CL:0002490",
                description="A supporting cell of the organ of Corti.",
                meaning=CL["0002490"]))
        setattr(cls, "CL:4023093",
            PermissibleValue(
                text="CL:4023093",
                description="""A pyramidal neuron which lacks a tuft formation but extends small radial distances forming a star-like shape.""",
                meaning=CL["4023093"]))
        setattr(cls, "CL:0002192",
            PermissibleValue(
                text="CL:0002192",
                description="""A eosinophil precursor in the granulocytic series, being a cell intermediate in development between a myelocyte and a band form cell. The nucleus becomes indented where the indentation is smaller than half the distance to the farthest nuclear margin; chromatin becomes coarse and clumped; specific granules predominate while primary granules are rare.""",
                meaning=CL["0002192"]))
        setattr(cls, "CL:3000002",
            PermissibleValue(
                text="CL:3000002",
                description="Sympathetic noradrenergic neuron.",
                meaning=CL["3000002"]))
        setattr(cls, "CL:0007016",
            PermissibleValue(
                text="CL:0007016",
                description="""Muscle precursor cell that is adjacent to the notochord and part of the presomitic mesoderm.""",
                meaning=CL["0007016"]))
        setattr(cls, "CL:0000883",
            PermissibleValue(
                text="CL:0000883",
                description="A thymic macrophage found in the thymic cortex.",
                meaning=CL["0000883"]))
        setattr(cls, "CL:1000284",
            PermissibleValue(
                text="CL:1000284",
                description="A smooth muscle cell that is part of the descending colon.",
                meaning=CL["1000284"]))
        setattr(cls, "CL:0002039",
            PermissibleValue(
                text="CL:0002039",
                description="A CD24-high, CD4-low, CD8-low, CD44-negative, NK1.1-negative NK T cell.",
                meaning=CL["0002039"]))
        setattr(cls, "CL:0000307",
            PermissibleValue(
                text="CL:0000307",
                description="An epithelial cell found in the trachea.",
                meaning=CL["0000307"]))
        setattr(cls, "CL:1000373",
            PermissibleValue(
                text="CL:1000373",
                description="""A transitional myocyte that is part of the ventricular part of atrioventricular bundle.""",
                meaning=CL["1000373"]))
        setattr(cls, "CL:0007003",
            PermissibleValue(
                text="CL:0007003",
                description="""Skeletogenic cell that has the potential to form an odontoblast, deposits predentine, and arises from a cranial neural crest cell.""",
                meaning=CL["0007003"]))
        setattr(cls, "CL:0011025",
            PermissibleValue(
                text="CL:0011025",
                description="""An effector T cell that displays impaired effector functions (e.g., rapid production of effector cytokines, cytotoxicity) and has limited proliferative potential.""",
                meaning=CL["0011025"]))
        setattr(cls, "CL:0002307",
            PermissibleValue(
                text="CL:0002307",
                description="""A brush border epithelial cell located in the proximal tubule of the kidney, essential for reabsorbing substances like glucose and amino acids from the glomerular filtrate. These cells also secrete organic ions, playing a crucial role in maintaining kidney homeostasis, including electrolyte and acid-base balance, and excreting metabolic waste.""",
                meaning=CL["0002307"]))
        setattr(cls, "CL:1001286",
            PermissibleValue(
                text="CL:1001286",
                description="""Any vasa recta descending limb cell that is part of some inner medulla descending vasa recta.""",
                meaning=CL["1001286"]))
        setattr(cls, "CL:0004245",
            PermissibleValue(
                text="CL:0004245",
                description="""An amacrine cell with a wide dendritic field and post-synaptic terminals in S5. This cell type releases the neurotransmitters gamma-aminobutyric acid (GABA) and serotonin.""",
                meaning=CL["0004245"]))
        setattr(cls, "CL:4052003",
            PermissibleValue(
                text="CL:4052003",
                description="""A capillary endothelial cell that is part of the intestinal villus. This cell is highly fenestrated, with fenestrations most numerous at the villus tips, and plays a vital role in nutrient absorption and maintaining the selective permeability of the intestinal barrier.""",
                meaning=CL["4052003"]))
        setattr(cls, "CL:0000072",
            PermissibleValue(
                text="CL:0000072",
                meaning=CL["0000072"]))
        setattr(cls, "CL:0000183",
            PermissibleValue(
                text="CL:0000183",
                description="A cell whose primary function is to shorten.",
                meaning=CL["0000183"]))
        setattr(cls, "CL:0002248",
            PermissibleValue(
                text="CL:0002248",
                description="""A pluripotent stem cell has the ability to form cells from all three germ layers (ectoderm, mesoderm, and endoderm). However, unlike totipotent stem cells, they cell can not generate all the cells of the whole organism such as placenta.""",
                meaning=CL["0002248"]))
        setattr(cls, "CL:4033052",
            PermissibleValue(
                text="CL:4033052",
                description="""A parasol ganglion cell that depolarizes in response to increased light intensity in the center of its receptive field. The majority of input that this cell receives comes from DB4 bipolar cells.""",
                meaning=CL["4033052"]))
        setattr(cls, "CL:0002126",
            PermissibleValue(
                text="CL:0002126",
                description="""A CD25-positive, CD27-positive immature gamma-delta T cell found in the thymus that has an immature phenotype (i.e. CD24-high, CD25-high, CD62L-high, CD44-high, CD2-low, CD5-low).""",
                meaning=CL["0002126"]))
        setattr(cls, "CL:0002523",
            PermissibleValue(
                text="CL:0002523",
                description="""A specialized epithelial cell that contains \"feet\" that interdigitate with the \"feet\" of other glomerular epithelial cells in the mesonephros.""",
                meaning=CL["0002523"]))
        setattr(cls, "CL:1000409",
            PermissibleValue(
                text="CL:1000409",
                description="A muscle cell that is part of the sinoatrial node.",
                meaning=CL["1000409"]))
        setattr(cls, "CL:0000425",
            PermissibleValue(
                text="CL:0000425",
                description="Forms the terminal part of the cuticle-lined excretory duct of C. elegans.",
                meaning=CL["0000425"]))
        setattr(cls, "CL:0000237",
            PermissibleValue(
                text="CL:0000237",
                meaning=CL["0000237"]))
        setattr(cls, "CL:0004250",
            PermissibleValue(
                text="CL:0004250",
                description="An amicrine that stratifies dendrites at two and only two locations.",
                meaning=CL["0004250"]))
        setattr(cls, "CL:0002517",
            PermissibleValue(
                text="CL:0002517",
                description="""An interrenal chromaffin cell found in teleosts that contain small, homogeneous electron-lucent granules that are separated from the vesicular membrane by a visible halo.""",
                meaning=CL["0002517"]))
        setattr(cls, "CL:0002053",
            PermissibleValue(
                text="CL:0002053",
                description="A small pre-B cell that is CD22-positive and CD38-low.",
                meaning=CL["0002053"]))
        setattr(cls, "CL:4030041",
            PermissibleValue(
                text="CL:4030041",
                description="""A ciliated cell of the endometrial luminal epithelium. This cell is characterized by the presence of motile cilia on its apical surface.""",
                meaning=CL["4030041"]))
        setattr(cls, "CL:0000911",
            PermissibleValue(
                text="CL:0000911",
                description="""A differentiated T cell with ability to traffic to peripheral tissues and is capable of mounting a specific immune response.""",
                meaning=CL["0000911"]))
        setattr(cls, "CL:4030043",
            PermissibleValue(
                text="CL:4030043",
                description="""A DRD1-expressing medium spiny neuron that is part of a matrix compartment of dorsal striatum.""",
                meaning=CL["4030043"]))
        setattr(cls, "CL:4023041",
            PermissibleValue(
                text="CL:4023041",
                description="""A transcriptomically distinct glutamatergic neuron, with a soma found in the deeper portion of L5, that has long-range axonal projections including deep subcortical targets outside of the telencephalon and, in some cases, the spinal cord. While the L5 ET neuron projections are not limited to ET targets, they are clearly differentiated from the neuron subclasses whose projections are constrained to intratelencephalic (IT) targets.  L5 ET neurons are generally the largest excitatory cortical neurons, typically having a thick apical dendrite with a prominent dendritic tuft in layer 1 and displaying burst-firing physiological characteristics. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: Deep layer (non-IT) excitatory neurons ', Author Categories: 'CrossArea_subclass', clusters L5 ET.""",
                meaning=CL["4023041"]))
        setattr(cls, "CL:0000795",
            PermissibleValue(
                text="CL:0000795",
                description="""A CD8-positive, alpha-beta T cell that regulates overall immune responses as well as the responses of other T cell subsets through direct cell-cell contact and cytokine release.""",
                meaning=CL["0000795"]))
        setattr(cls, "CL:0001077",
            PermissibleValue(
                text="CL:0001077",
                description="""An ILC1 cell in the human with the phenotype CD56-negative, IL-7Ralpha-positive, T-bet-positive.""",
                meaning=CL["0001077"]))
        setattr(cls, "CL:0009101",
            PermissibleValue(
                text="CL:0009101",
                description="""A reticular cell involved in directing B cells and T cells to specific regions within a tissue.""",
                meaning=CL["0009101"]))
        setattr(cls, "CL:1000143",
            PermissibleValue(
                text="CL:1000143",
                description="Any goblet cell that is part of some lung epithelium.",
                meaning=CL["1000143"]))
        setattr(cls, "CL:1001602",
            PermissibleValue(
                text="CL:1001602",
                description="""A distinct endothelial cell forming the walls of the capillaries within the cerebral cortex.""",
                meaning=CL["1001602"]))
        setattr(cls, "CL:2000016",
            PermissibleValue(
                text="CL:2000016",
                description="Any lung endothelial cell that is part of a microvascular endothelium.",
                meaning=CL["2000016"]))
        setattr(cls, "CL:0000844",
            PermissibleValue(
                text="CL:0000844",
                description="""A rapidly cycling mature B cell that has distinct phenotypic characteristics and is involved in T-dependent immune responses and located typically in the germinal centers of lymph nodes. This cell type expresses Ly77 after activation.""",
                meaning=CL["0000844"]))
        setattr(cls, "CL:0000787",
            PermissibleValue(
                text="CL:0000787",
                description="""A memory B cell is a mature B cell that is long-lived, readily activated upon re-encounter of its antigenic determinant, and has been selected for expression of higher affinity immunoglobulin. This cell type has the phenotype CD19-positive, CD20-positive, MHC Class II-positive, and CD138-negative.""",
                meaning=CL["0000787"]))
        setattr(cls, "CL:1000299",
            PermissibleValue(
                text="CL:1000299",
                description="A fibroblast that is part of the connective tissue of prostate.",
                meaning=CL["1000299"]))
        setattr(cls, "CL:0003001",
            PermissibleValue(
                text="CL:0003001",
                description="""A retinal ganglion cell that has dendrites stratified in two layers of the inner-plexiform layer.""",
                meaning=CL["0003001"]))
        setattr(cls, "CL:0001071",
            PermissibleValue(
                text="CL:0001071",
                description="""An innate lymphoid cell that constituitively expresses RORgt and is capable of expressing IL17A and/or IL-22.""",
                meaning=CL["0001071"]))
        setattr(cls, "CL:0000127",
            PermissibleValue(
                text="CL:0000127",
                description="""A class of large neuroglial (macroglial) cells in the central nervous system - the largest and most numerous neuroglial cells in the brain and spinal cord. Astrocytes (from 'star' cells) are irregularly shaped with many long processes, including those with 'end feet' which form the glial (limiting) membrane and directly and indirectly contribute to the blood-brain barrier. They regulate the extracellular ionic and chemical environment, and 'reactive astrocytes' (along with microglia) respond to injury.""",
                meaning=CL["0000127"]))
        setattr(cls, "CL:0000809",
            PermissibleValue(
                text="CL:0000809",
                description="""A thymocyte expressing the alpha-beta T cell receptor complex as well as both the CD4 and CD8 coreceptors.""",
                meaning=CL["0000809"]))
        setattr(cls, "CL:0002025",
            PermissibleValue(
                text="CL:0002025",
                description="""A megakaryocyte progenitor cell that is CD34-positive, CD41-positive, and CD42-negative.""",
                meaning=CL["0002025"]))
        setattr(cls, "CL:0002323",
            PermissibleValue(
                text="CL:0002323",
                description="""A cell of a fetus which is suspended in the amniotic fluid. Amniocytes are considered to arise from several tissues including fetal skin, the fetal urinary tract, umbilical cord, and the inner amniotic surface.""",
                meaning=CL["0002323"]))
        setattr(cls, "CL:4052030",
            PermissibleValue(
                text="CL:4052030",
                description="""A fibroblast of the adventitia of a blood vessel. This cell contributes to vascular homeostasis, remodeling, and inflammation by producing extracellular matrix components, cytokines, and growth factors. Adventitial fibroblast can transition into an activated state during injury or disease, marked by increased proliferation, migration, matrix deposition, and contractile protein expression""",
                meaning=CL["4052030"]))
        setattr(cls, "CL:0000626",
            PermissibleValue(
                text="CL:0000626",
                description="""A granule cell that has a soma located in an olfactory bulb granule cell layer. An olfactory granule cell is an interneuron that lacks an axon, makes reciprocal dendro-dendritic synapses with mitral cells and tufted cells and is involved in the fine spatio-temporal tuning of the responses of these principal olfactory bulb neurons to odors.""",
                meaning=CL["0000626"]))
        setattr(cls, "CL:0000427",
            PermissibleValue(
                text="CL:0000427",
                description="""A scaffolding cell type found in C. elegans, this cell plays a supportive role to the muscle arms. May also have an endocrine role.""",
                meaning=CL["0000427"]))
        setattr(cls, "CL:0001026",
            PermissibleValue(
                text="CL:0001026",
                description="""A common myeloid progenitor that is CD34-positive, CD38-positive, IL3ra-low, CD10-negative, CD7-negative, CD45RA-negative, and IL-5Ralpha-negative.""",
                meaning=CL["0001026"]))
        setattr(cls, "CL:0000480",
            PermissibleValue(
                text="CL:0000480",
                description="A peptide hormone secreting cell that secretes secretin stimulating hormone",
                meaning=CL["0000480"]))
        setattr(cls, "CL:0000892",
            PermissibleValue(
                text="CL:0000892",
                description="""A type of foam cell derived from a smooth muscle cell containing lipids in small vacuoles and typically seen in atherolosclerotic lesions, as well as other conditions.""",
                meaning=CL["0000892"]))
        setattr(cls, "CL:0000506",
            PermissibleValue(
                text="CL:0000506",
                description="An endorphine cell that secretes enkephalin.",
                meaning=CL["0000506"]))
        setattr(cls, "CL:0019018",
            PermissibleValue(
                text="CL:0019018",
                description="A smooth muscle cell that is part of any blood vessel.",
                meaning=CL["0019018"]))
        setattr(cls, "CL:4033058",
            PermissibleValue(
                text="CL:4033058",
                description="""A luminal epithelial cell of the mammary gland that transduces endocrine cues to orchestrate proliferation, architectural remodeling, and differentiation of other cells in the mammary gland via paracrine signaling. This cell expresses high levels of estrogen receptors. In humans, a luminal hormone-sensing cell can be identified by high levels of EpCAM and low levels of CD49f, and in mice it can be identified by low levels of CD29 and high levels of Foxa1, CD133, and Sca1 (Ly6a).""",
                meaning=CL["4033058"]))
        setattr(cls, "CL:0012000",
            PermissibleValue(
                text="CL:0012000",
                description="An astrocyte of the forebrain.",
                meaning=CL["0012000"]))
        setattr(cls, "CL:1000022",
            PermissibleValue(
                text="CL:1000022",
                description="Any epithelial cell that is part of some mesonephric nephron tubule.",
                meaning=CL["1000022"]))
        setattr(cls, "CL:1000488",
            PermissibleValue(
                text="CL:1000488",
                description="""An epithelial cell that is part of the bile duct. Cholangiocytes contribute to bile secretion via net release of bicarbonate and water. They are cuboidal epithelium in the small interlobular bile ducts, but become columnar and mucus secreting in larger bile ducts approaching the porta hepatis and the extrahepatic ducts.""",
                meaning=CL["1000488"]))
        setattr(cls, "CL:0002284",
            PermissibleValue(
                text="CL:0002284",
                description="""An enteroendocrine cell found in the fundus and pylorus; this cell type has dense round secretory granules that contain ghrelin.""",
                meaning=CL["0002284"]))
        setattr(cls, "CL:4033091",
            PermissibleValue(
                text="CL:4033091",
                description="An amacrine cell that uses both GABA and glycine as neurotransmitters.",
                meaning=CL["4033091"]))
        setattr(cls, "CL:4042029",
            PermissibleValue(
                text="CL:4042029",
                description="""An immature neuron of a cerebral cortex. This neuron develops prenatally and remains in an immature state throughout the lifespan of the organism.""",
                meaning=CL["4042029"]))
        setattr(cls, "CL:0000423",
            PermissibleValue(
                text="CL:0000423",
                meaning=CL["0000423"]))
        setattr(cls, "CL:4033027",
            PermissibleValue(
                text="CL:4033027",
                description="""An OFF diffuse bipolar cell that makes synaptic contact with both L/M and S-cone photoreceptors and only minimal contact with rod photoreceptors.""",
                meaning=CL["4033027"]))
        setattr(cls, "CL:0000154",
            PermissibleValue(
                text="CL:0000154",
                description="Any secretory cell that is capable of some protein secretion.",
                meaning=CL["0000154"]))
        setattr(cls, "CL:4042011",
            PermissibleValue(
                text="CL:4042011",
                description="""An interlaminar astrocyte type whose soma is part of the upper first layer of the neocortex and its processes extend to a pia surface.""",
                meaning=CL["4042011"]))
        setattr(cls, "CL:0000236",
            PermissibleValue(
                text="CL:0000236",
                description="A lymphocyte of B lineage that is capable of B cell mediated immunity.",
                meaning=CL["0000236"]))
        setattr(cls, "CL:2000047",
            PermissibleValue(
                text="CL:2000047",
                description="Any motor neuron that is part of a brainstem.",
                meaning=CL["2000047"]))
        setattr(cls, "CL:0001079",
            PermissibleValue(
                text="CL:0001079",
                description="""A group 3 innate lymphoid cell in the human with the phenotype IL-7Ralpha-positive, and NKp44-positive.""",
                meaning=CL["0001079"]))
        setattr(cls, "CL:4033029",
            PermissibleValue(
                text="CL:4033029",
                description="""An OFF calbindin-positive bipolar cell that has a large dendritic field and stratifies narrowly close to the middle of the inner plexiform layer. Its axon terminal is characterized by regularly branching and varicose processes resembling beads on a string. Most of DB3a contacts with cones are triad-associated.""",
                meaning=CL["4033029"]))
        setattr(cls, "CL:0002575",
            PermissibleValue(
                text="CL:0002575",
                description="A pericyte of the central nervous system.",
                meaning=CL["0002575"]))
        setattr(cls, "CL:0002054",
            PermissibleValue(
                text="CL:0002054",
                description="""An immature B cell that is IgM-positive, CD45R-positive, CD43-low, CD25-negative, and CD127-negative. This cell type has also been described as being AA4-positive, IgM-positive, CD19-positive, CD43-low/negative, and HSA-positive.""",
                meaning=CL["0002054"]))
        setattr(cls, "CL:0001030",
            PermissibleValue(
                text="CL:0001030",
                meaning=CL["0001030"]))
        setattr(cls, "CL:0002042",
            PermissibleValue(
                text="CL:0002042",
                description="A CD24-low, CD44-positive, DX5-high, NK1.1-negative NK T cell.",
                meaning=CL["0002042"]))
        setattr(cls, "CL:1000283",
            PermissibleValue(
                text="CL:1000283",
                description="A smooth muscle cell that is part of the transverse colon.",
                meaning=CL["1000283"]))
        setattr(cls, "CL:0002202",
            PermissibleValue(
                text="CL:0002202",
                description="An epithelial cell of the tracheobronchial tree.",
                meaning=CL["0002202"]))
        setattr(cls, "CL:0000225",
            PermissibleValue(
                text="CL:0000225",
                description="A cell that lacks a nucleus.",
                meaning=CL["0000225"]))
        setattr(cls, "CL:0002265",
            PermissibleValue(
                text="CL:0002265",
                description="A D cell located in the colon.",
                meaning=CL["0002265"]))
        setattr(cls, "CL:0002031",
            PermissibleValue(
                text="CL:0002031",
                description="""A hematopoietic progenitor cell that is capable of developing into only one lineage of hematopoietic cells.""",
                meaning=CL["0002031"]))
        setattr(cls, "CL:2000041",
            PermissibleValue(
                text="CL:2000041",
                description="""Any dermis lymphatic vessel endothelial cell that is part of a microvascular endothelium.""",
                meaning=CL["2000041"]))
        setattr(cls, "CL:0000069",
            PermissibleValue(
                text="CL:0000069",
                meaning=CL["0000069"]))
        setattr(cls, "CL:0002498",
            PermissibleValue(
                text="CL:0002498",
                description="""A trophoblast giant cell that is derived from ectoplacental cone and, later in gestation, the spongiotrophoblast.""",
                meaning=CL["0002498"]))
        setattr(cls, "CL:1001608",
            PermissibleValue(
                text="CL:1001608",
                description="Fibroblast from foreskin.",
                meaning=CL["1001608"]))
        setattr(cls, "CL:0002355",
            PermissibleValue(
                text="CL:0002355",
                description="""A large nucleated basophilic erythrocyte found in mammalian embryos. This cell type arises from the blood islands of yolk sacs and expresses different types of hemoglobins (beta-H1, gamma-1 and zeta) than adult erythrocytes. Considered a type of erythroblast as this cell type can enucleate in circulation.""",
                meaning=CL["0002355"]))
        setattr(cls, "CL:0000776",
            PermissibleValue(
                text="CL:0000776",
                description="""Any of the immature forms of a neutrophil in which neutrophilic specific granules are present but other phenotypic features of the mature form may be lacking.""",
                meaning=CL["0000776"]))
        setattr(cls, "CL:0004233",
            PermissibleValue(
                text="CL:0004233",
                description="""An amacrine cell with a medium dendritic field and post-synaptic terminals that stratify at S2, with a second stratification that occurs in S3 and S4. This cell type releases the neurotransmitter glycine.""",
                meaning=CL["0004233"]))
        setattr(cls, "CL:4030056",
            PermissibleValue(
                text="CL:4030056",
                description="""A urothelial cell that is terminally differentiated and part of the urothelial apical surface that forms the high-resistance barrier of urothelium. Umbrella cells have been described as the largest of urothelial cell types, highly polarized, and, in some species, multinucleated. In the relaxed state, these cells form a dome-shaped structure at the apical pole and can also cover multiple underlying intermediate cells, leading to the name umbrella cells. In contrast, these cells flatten when the bladder is filled.""",
                meaning=CL["4030056"]))
        setattr(cls, "CL:0000437",
            PermissibleValue(
                text="CL:0000437",
                description="""A rounded cell that is usually situated next to sinusoids; secretes follicular stimulating hormone (FSH) and luteinizing hormone (LH).""",
                meaning=CL["0000437"]))
        setattr(cls, "CL:4052045",
            PermissibleValue(
                text="CL:4052045",
                description="""A stromal cell that is part of the ovarian stroma, characterized by its ability to synthesize steroid hormones.""",
                meaning=CL["4052045"]))
        setattr(cls, "CL:0001029",
            PermissibleValue(
                text="CL:0001029",
                description="""Common dendritic precursor is a hematopoietic progenitor cell that is CD117-low, CD135-positive, CD115-positive and lacks plasma membrane parts for hematopoietic lineage markers.""",
                meaning=CL["0001029"]))
        setattr(cls, "CL:4030002",
            PermissibleValue(
                text="CL:4030002",
                description="An alpha-beta memory T cell with the phenotype CD45RA-positive.",
                meaning=CL["4030002"]))
        setattr(cls, "CL:0002481",
            PermissibleValue(
                text="CL:0002481",
                description="""The flattened smooth myoepithelial cells of mesodermal origin that lie just outside the basal lamina of the seminiferous tubule.""",
                meaning=CL["0002481"]))
        setattr(cls, "CL:0002410",
            PermissibleValue(
                text="CL:0002410",
                description="""A cell that is found in the periacinar space of the exocrine pancreas and in perivascular and periductal regions of the pancreas, and has long cytoplasmic processes that encircle the base of the acinus. Expresses several intermediate filament proteins including vimentin and nestin. Shares many of the characteristics of hepatatic stellate cells, but not stellate cells of the central nervous system. Upon activation, this cell type undergoes morphological and gene expression changes that make the cell suggestive of being a type of myofibroblast.""",
                meaning=CL["0002410"]))
        setattr(cls, "CL:1000275",
            PermissibleValue(
                text="CL:1000275",
                description="A smooth muscle cell that is part of the small intestine.",
                meaning=CL["1000275"]))
        setattr(cls, "CL:0002630",
            PermissibleValue(
                text="CL:0002630",
                description="A spore formed from bacteria in the order Actinomycetales.",
                meaning=CL["0002630"]))
        setattr(cls, "CL:0002024",
            PermissibleValue(
                text="CL:0002024",
                description="""A megakaryocyte progenitor cell that is Kit-positive, CD41-positive, CD9-positive, Sca-1-negative, IL7ralpha-negative, CD150-negative, and Fcgamma receptor II/III-low.""",
                meaning=CL["0002024"]))
        setattr(cls, "CL:4030030",
            PermissibleValue(
                text="CL:4030030",
                description="A blood lymphocyte located in the flowing, circulating blood of the body.",
                meaning=CL["4030030"]))
        setattr(cls, "CL:4023049",
            PermissibleValue(
                text="CL:4023049",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in L5 of the primary motor cortex.""",
                meaning=CL["4023049"]))
        setattr(cls, "CL:0007000",
            PermissibleValue(
                text="CL:0007000",
                description="""Skeletogenic cell that has the potential to develop into an ameloblast. Located in the inner enamel epithelium, these cells elongate, their nuclei shift distally (away from the dental papilla), and their cytoplasm becomes filled with organelles needed for synthesis and secretion of enamel proteins.""",
                meaning=CL["0007000"]))
        setattr(cls, "CL:0002223",
            PermissibleValue(
                text="CL:0002223",
                description="""A cell of the transparent layer of simple cuboidal epithelium over the anterior surface of the lens; transform into lens fiber(s).""",
                meaning=CL["0002223"]))
        setattr(cls, "CL:0004243",
            PermissibleValue(
                text="CL:0004243",
                description="""An amacrine cell with a wild dendritic field, dendrites in S3, and post-synaptic terminals in S3. Dendrites have spikes, cross over each other, and cover a larger volume than dendrties of W3-1 retinal amacrine cells.""",
                meaning=CL["0004243"]))
        setattr(cls, "CL:1000394",
            PermissibleValue(
                text="CL:1000394",
                description="""A myoepithelial cell that is part of the intralobular part of terminal lactiferous duct.""",
                meaning=CL["1000394"]))
        setattr(cls, "CL:0000884",
            PermissibleValue(
                text="CL:0000884",
                description="A tissue-resident macrophage found in the mucosa associated lymphoid tissue.",
                meaning=CL["0000884"]))
        setattr(cls, "CL:0000358",
            PermissibleValue(
                text="CL:0000358",
                description="""A smooth muscle cell that is part of a sphincter. A sphincter is a typically circular muscle that normally maintains constriction of a natural body passage or orifice and which relaxes as required by normal physiological functioning.""",
                meaning=CL["0000358"]))
        setattr(cls, "CL:0008036",
            PermissibleValue(
                text="CL:0008036",
                description="A trophoblast cell that is not part of a placental villous.",
                meaning=CL["0008036"]))
        setattr(cls, "CL:1001561",
            PermissibleValue(
                text="CL:1001561",
                description="""Chemosensitive cells that innervate the vomernasal organ epithelium and are responsible for receiving and transmitting pheromone signals.""",
                meaning=CL["1001561"]))
        setattr(cls, "CL:0009036",
            PermissibleValue(
                text="CL:0009036",
                description="A macrophage located in the vermiform appendix.",
                meaning=CL["0009036"]))
        setattr(cls, "CL:0002626",
            PermissibleValue(
                text="CL:0002626",
                description="An immature astrocyte.",
                meaning=CL["0002626"]))
        setattr(cls, "CL:1001066",
            PermissibleValue(
                text="CL:1001066",
                meaning=CL["1001066"]))
        setattr(cls, "CL:0000948",
            PermissibleValue(
                text="CL:0000948",
                description="A class switched memory B cell that expresses IgE on the cell surface.",
                meaning=CL["0000948"]))
        setattr(cls, "CL:0000168",
            PermissibleValue(
                text="CL:0000168",
                description="Any secretory cell that is capable of some insulin secretion.",
                meaning=CL["0000168"]))
        setattr(cls, "CL:0002273",
            PermissibleValue(
                text="CL:0002273",
                description="""A type EC enteroendocrine cell type that is numerous in the fundus of the stomach; stores 5-hydroxytryptamine and histamine.""",
                meaning=CL["0002273"]))
        setattr(cls, "CL:0000470",
            PermissibleValue(
                text="CL:0000470",
                meaning=CL["0000470"]))
        setattr(cls, "CL:0000356",
            PermissibleValue(
                text="CL:0000356",
                meaning=CL["0000356"]))
        setattr(cls, "CL:0002075",
            PermissibleValue(
                text="CL:0002075",
                description="""A rare type of columnar epithelial cell that is part of the tracheobronchial epithelium. This cell is characterized by a distinctive tuft of apical microvilli, which extends into the cytoplasm, and a pear-shaped morphology, broad at the base and tapering to a narrow apex. It plays vital roles in chemosensation, producing cytokines like IL-25, and enhancing mucociliary clearance through acetylcholine release to support mucus movement and airway defense.""",
                meaning=CL["0002075"]))
        setattr(cls, "CL:4023005",
            PermissibleValue(
                text="CL:4023005",
                description="A nuclear bag fiber that is sensitive mainly to the rate of change in muscle length.",
                meaning=CL["4023005"]))
        setattr(cls, "CL:0000855",
            PermissibleValue(
                text="CL:0000855",
                description="""Hair cell is a mechanoreceptor cell that is sensitive to movement of the hair-like projections (stereocilia and kinocilia) which relay the information centrally in the nervous system.""",
                meaning=CL["0000855"]))
        setattr(cls, "CL:0000226",
            PermissibleValue(
                text="CL:0000226",
                description="A cell with a single nucleus.",
                meaning=CL["0000226"]))
        setattr(cls, "CL:0000930",
            PermissibleValue(
                text="CL:0000930",
                description="A mature NK T cell that secretes interleukin-4 and enhances Th2 immune responses.",
                meaning=CL["0000930"]))
        setattr(cls, "CL:4052019",
            PermissibleValue(
                text="CL:4052019",
                description="Any epithelial cell that is part of the fallopian tube and lacks cilia.",
                meaning=CL["4052019"]))
        setattr(cls, "CL:0000678",
            PermissibleValue(
                text="CL:0000678",
                description="""A neuron with soma location in the central nervous system that project its axon to the contralateral side of a central nervous system. This neuron can have its soma in the spinal cord, in the hemisphere of the brain, in the retina or in the ventral nerve cord of invertebrates.""",
                meaning=CL["0000678"]))
        setattr(cls, "CL:0000772",
            PermissibleValue(
                text="CL:0000772",
                description="""Any of the immature forms of an eosinophil, in which eosinophilic specific granules are present but other phenotypic features of the mature form may be lacking.""",
                meaning=CL["0000772"]))
        setattr(cls, "CL:0002455",
            PermissibleValue(
                text="CL:0002455",
                description="A CD11c-low plasmacytoid dendritic cell that is CD8-alpha-negative and CD4-positive.",
                meaning=CL["0002455"]))
        setattr(cls, "CL:0002479",
            PermissibleValue(
                text="CL:0002479",
                description="An adipose macrophage that does not express MHC-II but is F4/80-positive.",
                meaning=CL["0002479"]))
        setattr(cls, "CL:0000068",
            PermissibleValue(
                text="CL:0000068",
                description="An epithelial cell that is part of a duct.",
                meaning=CL["0000068"]))
        setattr(cls, "CL:4047032",
            PermissibleValue(
                text="CL:4047032",
                description="""A specialized pericyte located within the basement membrane of a blood capillary. This cell is characterized by its ability to produce and release a variety of bioactive molecules, collectively known as the pericyte secretome, including cytokines and regulators of angiogenesis.""",
                meaning=CL["4047032"]))
        setattr(cls, "CL:0011103",
            PermissibleValue(
                text="CL:0011103",
                description="""Sympathetic neurons are part of the sympathetic nervous system and are primarily adrenergic producing the neurotransmitter noradrenalin along with other neuropeptides.""",
                meaning=CL["0011103"]))
        setattr(cls, "CL:0002633",
            PermissibleValue(
                text="CL:0002633",
                description="A basal cell in the respiratory tract.",
                meaning=CL["0002633"]))
        setattr(cls, "CL:0008011",
            PermissibleValue(
                text="CL:0008011",
                description="""A skeletal muscle satellite cell that divides by stem cell division.  A proportion of this population undergoes symmetric stem cell division, producing two skeletal muscle satellite stem cells. The rest undergo asymmetric stem cell division - retaining their identity while budding off a daughter cell that differentiates into an adult skeletal muscle myoblast.""",
                meaning=CL["0008011"]))
        setattr(cls, "CL:4042018",
            PermissibleValue(
                text="CL:4042018",
                description="""Tanycyte of the third ventricle, located immediately ventral to alpha-1 tanycytes. These cells project to the ventromedial and arcuate nuclei of the hypothalamus and express the glial marker S-100β.""",
                meaning=CL["4042018"]))
        setattr(cls, "CL:0000891",
            PermissibleValue(
                text="CL:0000891",
                description="""A type of cell containing lipids in small vacuoles and typically seen in atherolosclerotic lesions, as well as other conditions.""",
                meaning=CL["0000891"]))
        setattr(cls, "CL:2000033",
            PermissibleValue(
                text="CL:2000033",
                description="Any basal cell of epidermis that is part of a limb.",
                meaning=CL["2000033"]))
        setattr(cls, "CL:0000147",
            PermissibleValue(
                text="CL:0000147",
                description="A pigment cell is a cell that contains pigment granules.",
                meaning=CL["0000147"]))
        setattr(cls, "CL:0002665",
            PermissibleValue(
                text="CL:0002665",
                description="A fibrocyte of the cochlea that has specialized structural and molecular adaptions.",
                meaning=CL["0002665"]))
        setattr(cls, "CL:4033095",
            PermissibleValue(
                text="CL:4033095",
                description="""An ON bipolar cell that has high expression of DIRC3, KCNJ3, LINC01915, PTPRK compared with other bipolar cells.""",
                meaning=CL["4033095"]))
        setattr(cls, "CL:0002470",
            PermissibleValue(
                text="CL:0002470",
                description="Gr1-high monocyte that has a MHC-II receptor complex.",
                meaning=CL["0002470"]))
        setattr(cls, "CL:0002594",
            PermissibleValue(
                text="CL:0002594",
                description="A smooth muscle cell of the umbilical artery.",
                meaning=CL["0002594"]))
        setattr(cls, "CL:0004222",
            PermissibleValue(
                text="CL:0004222",
                description="""A flag amacrine cell with post-synaptic terminals in S3, S4, and S5. This cell type releases the neurotransmitter glycine.""",
                meaning=CL["0004222"]))
        setattr(cls, "CL:0000103",
            PermissibleValue(
                text="CL:0000103",
                description="""A type of interneuron that has two neurites, usually an axon and a dendrite, extending from opposite poles of an ovoid cell body.""",
                meaning=CL["0000103"]))
        setattr(cls, "CL:1000746",
            PermissibleValue(
                text="CL:1000746",
                description="Any kidney corpuscule cell that is part of some renal glomerulus.",
                meaning=CL["1000746"]))
        setattr(cls, "CL:0000377",
            PermissibleValue(
                text="CL:0000377",
                meaning=CL["0000377"]))
        setattr(cls, "CL:0002139",
            PermissibleValue(
                text="CL:0002139",
                description="""An endothelial cell of the vascular tree, which includes blood vessels and lymphatic vessels.""",
                meaning=CL["0002139"]))
        setattr(cls, "CL:0000071",
            PermissibleValue(
                text="CL:0000071",
                description="An endothelial cell that lines the vasculature.",
                meaning=CL["0000071"]))
        setattr(cls, "CL:0000852",
            PermissibleValue(
                text="CL:0000852",
                description="""Neuromast support cell is a non-sensory cell of the neuromast that extend between the sensory hair cells from the basement membrane to the apical surface; neuromast support cells are surrounded by neuromast mantle cells.""",
                meaning=CL["0000852"]))
        setattr(cls, "CL:0000723",
            PermissibleValue(
                text="CL:0000723",
                description="""A stem cell that can give rise to cell types of the body other than those of the germ-line.""",
                meaning=CL["0000723"]))
        setattr(cls, "CL:0002007",
            PermissibleValue(
                text="CL:0002007",
                description="""A lineage marker-negative, CD34-positive, IL5r-alpha-positive, and Sca1-negative eosinophil progenitor cell.""",
                meaning=CL["0002007"]))
        setattr(cls, "CL:0000606",
            PermissibleValue(
                text="CL:0000606",
                description="""The larger of two types of asexual spores formed by some fungi; usually round or oblong.""",
                meaning=CL["0000606"]))
        setattr(cls, "CL:0000609",
            PermissibleValue(
                text="CL:0000609",
                description="""A mechanoreceptor located in the acoustic maculae and the semicircular canals that mediates the sense of balance, movement, and head position. The vestibular hair cells are connected to accessory structures in such a way that movements of the head displace their stereocilia. This influences the membrane potential of the cells which relay information about movements via the vestibular part of the vestibulocochlear nerve to the brain stem.""",
                meaning=CL["0000609"]))
        setattr(cls, "CL:0001053",
            PermissibleValue(
                text="CL:0001053",
                description="A memory B cell that lacks expression of surface IgD.",
                meaning=CL["0001053"]))
        setattr(cls, "CL:0000781",
            PermissibleValue(
                text="CL:0000781",
                description="""A specialized mononuclear osteoclast associated with the absorption and removal of cementum.""",
                meaning=CL["0000781"]))
        setattr(cls, "CL:0009059",
            PermissibleValue(
                text="CL:0009059",
                description="A plasma cell that is located in the medullary sinus of the lymph node.",
                meaning=CL["0009059"]))
        setattr(cls, "CL:0002121",
            PermissibleValue(
                text="CL:0002121",
                description="""A CD24-negative CD38-negative IgG-negative memory B cell is a CD38-negative IgG-negative class switched memory B cell that lacks IgG on the cell surface with the phenotype CD24-negative, CD38-negative, and IgG-negative.""",
                meaning=CL["0002121"]))
        setattr(cls, "CL:0000747",
            PermissibleValue(
                text="CL:0000747",
                description="""A pigment cell derived from the neural crest. Contains blue pigment of unknown chemical composition in fibrous organelles termed cyanosomes. This gives a blue appearance.""",
                meaning=CL["0000747"]))
        setattr(cls, "CL:0011020",
            PermissibleValue(
                text="CL:0011020",
                description="""An undifferentiated cell derived from a neural stem cell, with a limited capacity to self-renew (Dibajnia and Morshead, 2013) and the ability to generate multiple types of lineage-restricted progenitors, contributing to the formation of neurons, astrocytes, and oligodendrocytes.""",
                meaning=CL["0011020"]))
        setattr(cls, "CL:4033020",
            PermissibleValue(
                text="CL:4033020",
                description="A mucus secreting cell that is part of a submucosal gland of the trachea.",
                meaning=CL["4033020"]))
        setattr(cls, "CL:1000276",
            PermissibleValue(
                text="CL:1000276",
                description="A smooth muscle cell that is part of the duodenum.",
                meaning=CL["1000276"]))
        setattr(cls, "CL:0011028",
            PermissibleValue(
                text="CL:0011028",
                description="""A neural-crest derived glial cell that supports the growth and survival of primary olfactory neuroons from the neuroepithelium in the nasal cavity to the brain by encasing large bundles of numerous unmyelinated axons.""",
                meaning=CL["0011028"]))
        setattr(cls, "CL:4030065",
            PermissibleValue(
                text="CL:4030065",
                description="""A transcriptomically distinct intratelencephalic-projecting glutamatergic neuron with a soma found in L6 of the primary motor cortex. These cells are short untufted pyramidal cells, which could be stellate or inverted.  The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: IT-projecting excitatory neurons', Author Categories: 'CrossArea_subclass', L6 IT.""",
                meaning=CL["4030065"]))
        setattr(cls, "CL:2000010",
            PermissibleValue(
                text="CL:2000010",
                description="Any blood vessel endothelial cell that is part of a dermis.",
                meaning=CL["2000010"]))
        setattr(cls, "CL:0000802",
            PermissibleValue(
                text="CL:0000802",
                description="A gamma-delta intraepithelial T cell that has the phenotype CD8-alpha alpha-positive.",
                meaning=CL["0000802"]))
        setattr(cls, "CL:0002115",
            PermissibleValue(
                text="CL:0002115",
                description="""A B220-positive CD38-positive unswitched memory B cell is a CD38-positive unswitched memory B cell that has the phenotype B220-positive, CD38-positive, IgD-positive, CD138-negative, and IgG-negative.""",
                meaning=CL["0002115"]))
        setattr(cls, "CL:1001223",
            PermissibleValue(
                text="CL:1001223",
                description="Any endothelial cell that is part of some renal interlobular vein.",
                meaning=CL["1001223"]))
        setattr(cls, "CL:0002152",
            PermissibleValue(
                text="CL:0002152",
                description="A simple columnar epithelial cell located in the endocervix.",
                meaning=CL["0002152"]))
        setattr(cls, "CL:0000234",
            PermissibleValue(
                text="CL:0000234",
                description="Any cell capable of ingesting particulate matter via phagocytosis.",
                meaning=CL["0000234"]))
        setattr(cls, "CL:0001081",
            PermissibleValue(
                text="CL:0001081",
                description="""A group 2 innate lymphoid cell in the human with the phenotype CD25-positive, CD127-positive, CD161-positive, and GATA-3-positive.""",
                meaning=CL["0001081"]))
        setattr(cls, "CL:0000340",
            PermissibleValue(
                text="CL:0000340",
                description="A precursor of the central nervous system that gives rise to glial cells only.",
                meaning=CL["0000340"]))
        setattr(cls, "CL:0000738",
            PermissibleValue(
                text="CL:0000738",
                description="""An achromatic cell of the myeloid or lymphoid lineages capable of ameboid movement, found in blood or other tissue.""",
                meaning=CL["0000738"]))
        setattr(cls, "CL:0002506",
            PermissibleValue(
                text="CL:0002506",
                description="""A CD11b-positive dendritic cell that is CD11b-low, CD45-positive, MHC-II-high and CD103-positive that is located in the liver.""",
                meaning=CL["0002506"]))
        setattr(cls, "CL:0000396",
            PermissibleValue(
                text="CL:0000396",
                description="A hemocyte found in immuno-stimulated larvae.",
                meaning=CL["0000396"]))
        setattr(cls, "CL:0000040",
            PermissibleValue(
                text="CL:0000040",
                description="""A myeloid progenitor cell committed to the monocyte lineage. This cell is CD11b-positive, has basophilic cytoplasm, euchromatin, and the presence of a nucleolus.""",
                meaning=CL["0000040"]))
        setattr(cls, "CL:4023054",
            PermissibleValue(
                text="CL:4023054",
                description="""A mesothelial cell that has undergone mesothelial-to-mesenchymal transition (MMT) to become a fibroblast cell.""",
                meaning=CL["4023054"]))
        setattr(cls, "CL:0000347",
            PermissibleValue(
                text="CL:0000347",
                description="A cell of the sclera of the eye.",
                meaning=CL["0000347"]))
        setattr(cls, "CL:0009048",
            PermissibleValue(
                text="CL:0009048",
                description="A macrophage that is located in the anorectum.",
                meaning=CL["0009048"]))
        setattr(cls, "CL:0000798",
            PermissibleValue(
                text="CL:0000798",
                description="A T cell that expresses a gamma-delta T cell receptor complex.",
                meaning=CL["0000798"]))
        setattr(cls, "CL:1001590",
            PermissibleValue(
                text="CL:1001590",
                description="Glandular cell of epididymal epithelium.",
                meaning=CL["1001590"]))
        setattr(cls, "CL:0000476",
            PermissibleValue(
                text="CL:0000476",
                description="""A basophil cell of the anterior pituitary that produces thyroid stimulating hormone, thyrotrophin. This cell type is elongated, polygonal and lie in clusters towards the adenohypophyseal center.""",
                meaning=CL["0000476"]))
        setattr(cls, "CL:0002293",
            PermissibleValue(
                text="CL:0002293",
                description="""An epithelial cell of the thymus. Epithelial reticular cells are pleomorphic, stellate, non-phagocytic cells which seem to be supportive in function and are held together by desmosomes. They replace the fibroblastoid reticular cells found in other lymphoid organs. Other epithelial cells in the medulla have the ultrastructure of secretory cells. Although different epithelial cells throughout the thymus appear alike by light microscopy their ultrastructure and function varies.""",
                meaning=CL["0002293"]))
        setattr(cls, "CL:4033047",
            PermissibleValue(
                text="CL:4033047",
                description="""A midget ganglion cell that depolarizes in response to decreased light intensity in the center of its receptive field. The majority of input that this cell receives comes from flat midget bipolar cells.""",
                meaning=CL["4033047"]))
        setattr(cls, "CL:0001082",
            PermissibleValue(
                text="CL:0001082",
                description="An innate lyphoid cell with an immature phenotype.",
                meaning=CL["0001082"]))
        setattr(cls, "CL:1000324",
            PermissibleValue(
                text="CL:1000324",
                description="A goblet cell that is part of the epithelium proper of duodenum.",
                meaning=CL["1000324"]))
        setattr(cls, "CL:0000535",
            PermissibleValue(
                text="CL:0000535",
                description="""A neuron of teleosts that develops later than a primary neuron, typically during the larval stages.""",
                meaning=CL["0000535"]))
        setattr(cls, "CL:1001107",
            PermissibleValue(
                text="CL:1001107",
                description="An epithelial cell that is part of some loop of Henle thin ascending limb.",
                meaning=CL["1001107"]))
        setattr(cls, "CL:0001041",
            PermissibleValue(
                text="CL:0001041",
                description="""A CD8-positive alpha-beta-positive T cell with the phenotype CXCR3-positive and having suppressor function. They are capable of producing IL-10, suppressing proliferation, and suppressing IFN-gamma production.""",
                meaning=CL["0001041"]))
        setattr(cls, "CL:4030066",
            PermissibleValue(
                text="CL:4030066",
                description="""An epithelial cell that is part of a ureteric bud. A ureteric bud cell has the potential to induce metanephric mesenchymal cells to proliferate and convert to epithelia that form renal tubules via: (1) the secretion of multiple diffusible growth factors that rescue renal progenitors from apoptosis and stimulate them to proliferate and (2) contact-dependent mechanisms that induce mesenchymal-epithelial conversion.""",
                meaning=CL["4030066"]))
        setattr(cls, "CL:0008031",
            PermissibleValue(
                text="CL:0008031",
                description="An interneuron that has its soma located in the cerebral cortex.",
                meaning=CL["0008031"]))
        setattr(cls, "CL:0002363",
            PermissibleValue(
                text="CL:0002363",
                description="""A keratocyte is a specialized fibroblast residing in the cornea stroma that has a flattened, dendritic morphology; located between the lamellae with a large flattened nucleus, and lengthy processes which communicate with neighboring cells. This corneal layer, representing about 85-90% of corneal thickness, is built up from highly regular collagenous lamellae and extracellular matrix components. Keratocytes play the major role in keeping it transparent, healing its wounds, and synthesizing its components. This cell type secretes collagen I, V, VI, and keratan sulfate.""",
                meaning=CL["0002363"]))
        setattr(cls, "CL:0004219",
            PermissibleValue(
                text="CL:0004219",
                description="""A bistratifed retinal amacrine cell with a small dendritic field, dendrite stratification in S1-S2, and a second dendrite stratification in S5. This cell type releases the neurotransmitter glycine.""",
                meaning=CL["0004219"]))
        setattr(cls, "CL:0011004",
            PermissibleValue(
                text="CL:0011004",
                description="""A vetebrate lens cell that is any of the elongated, tightly packed cells that make up the bulk of the mature lens in a camera-type eye.""",
                meaning=CL["0011004"]))
        setattr(cls, "CL:0002149",
            PermissibleValue(
                text="CL:0002149",
                description="An epithelial cell of the uterus. This cell has a mesodermal origin.",
                meaning=CL["0002149"]))
        setattr(cls, "CL:0000582",
            PermissibleValue(
                text="CL:0000582",
                description="""A neutrophil precursor in the granulocytic series, being a cell intermediate in development between a myelocyte and the band form neutrophil. The protein synthesis seen in earlier stages decreases or stops; the nucleus becomes indented where the indentation is smaller than half the distance to the farthest nuclear margin; chromatin becomes coarse and clumped; specific granules predominate while primary granules are rare; and the cytoplasm becomes amphophilic like that of a mature granulocyte. This cell type is integrin alpha-M-positive, CD13-negative, CD15-positive, CD16-positive, CD33-positive, CD24-positive, fMLP receptor-negative and has expression of C/EBP-a, C/EBP-e, PU.1 transcription factor, lactotransferrin, myeloperoxidase and neutrophil gelatinase associated lipocalin.""",
                meaning=CL["0000582"]))
        setattr(cls, "CL:4033096",
            PermissibleValue(
                text="CL:4033096",
                description="""An ON bipolar cell that has high expression of NOS1AP compared with other bipolar cells.""",
                meaning=CL["4033096"]))
        setattr(cls, "CL:0002014",
            PermissibleValue(
                text="CL:0002014",
                description="A basophilic erythroblast that is Lyg 76-high and is Kit-negative.",
                meaning=CL["0002014"]))
        setattr(cls, "CL:1001052",
            PermissibleValue(
                text="CL:1001052",
                description="Any kidney venous blood vessel cell that is part of some renal cortex vein.",
                meaning=CL["1001052"]))
        setattr(cls, "CL:0009103",
            PermissibleValue(
                text="CL:0009103",
                description="A fibroblastic reticular cell found in the lymph node subcapsular sinus.",
                meaning=CL["0009103"]))
        setattr(cls, "CL:0000987",
            PermissibleValue(
                text="CL:0000987",
                description="A fully differentiated plasma cell that secretes IgA.",
                meaning=CL["0000987"]))
        setattr(cls, "CL:0002511",
            PermissibleValue(
                text="CL:0002511",
                description="A langerin-negative lymph node dendritic cell that is CD103-negative and CD11b-low.",
                meaning=CL["0002511"]))
        setattr(cls, "CL:0000617",
            PermissibleValue(
                text="CL:0000617",
                description="A neuron that uses GABA as a vesicular neurotransmitter",
                meaning=CL["0000617"]))
        setattr(cls, "CL:0002464",
            PermissibleValue(
                text="CL:0002464",
                description="An adipose dendritic cell that is SIRPa-negative.",
                meaning=CL["0002464"]))
        setattr(cls, "CL:1000432",
            PermissibleValue(
                text="CL:1000432",
                description="An epithelial cell that is part of the conjunctiva.",
                meaning=CL["1000432"]))
        setattr(cls, "CL:1001503",
            PermissibleValue(
                text="CL:1001503",
                description="""The principal glutaminergic neuron located in the outer third of the external plexiform layer of the olfactory bulb; a single short primary dendrite traverses the outer external plexiform layer and terminates within an olfactory glomerulus in a tuft of branches, where it receives the input from olfactory receptor neuron axon terminals; axons of the tufted cells transfer information to a number of areas in the brain, including the piriform cortex, entorhinal cortex, olfactory tubercle, and amygdala.""",
                meaning=CL["1001503"]))
        setattr(cls, "CL:2000086",
            PermissibleValue(
                text="CL:2000086",
                description="Any basket cell that is part of a neocortex.",
                meaning=CL["2000086"]))
        setattr(cls, "CL:0003010",
            PermissibleValue(
                text="CL:0003010",
                description="""A bistratified retinal ganglion cell that has a dendrite field that terminates in sublaminar layer S2 and a second dendrite field that terminates in sublaminar layer S4.""",
                meaning=CL["0003010"]))
        setattr(cls, "CL:0002128",
            PermissibleValue(
                text="CL:0002128",
                description="""A CD8-positive, alpha-beta T cell that has the phenotype CXCR3-negative, CCR6-positive, CCR5-high, CD45RA-negative, and capable of producing IL-17 and some IFNg.""",
                meaning=CL["0002128"]))
        setattr(cls, "CL:0002408",
            PermissibleValue(
                text="CL:0002408",
                description="""A double negative post-natal thymocyte that has a T cell receptor consisting of a gamma chain that does not contain a Vgamma2 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-positive.""",
                meaning=CL["0002408"]))
        setattr(cls, "CL:0002662",
            PermissibleValue(
                text="CL:0002662",
                description="""A luminal epithelial cell of the lactiferous duct. This cuboidal epithelial cell expresses keratin-18 and is estrogen-receptor alpha positive.""",
                meaning=CL["0002662"]))
        setattr(cls, "CL:4033066",
            PermissibleValue(
                text="CL:4033066",
                description="""A supporting cell that is part of the ovary and differentiates into a granulosa cell. A pre-granulosa cell develops from an early supporting gonadal cell by repressing testis determination, which can then proliferate to form primordial follicles.""",
                meaning=CL["4033066"]))
        setattr(cls, "CL:4033085",
            PermissibleValue(
                text="CL:4033085",
                description="""An ON diffuse bipolar cell that stratifies in the stratum 3 of the inner plexiform layer to make synapses with ON parasol ganglion cells. A diffuse bipolar 5 cell has high expression of MYO16 compared with other bipolar cells.""",
                meaning=CL["4033085"]))
        setattr(cls, "CL:0000197",
            PermissibleValue(
                text="CL:0000197",
                description="A cell that is capable of detection of a stimulus involved in sensory perception.",
                meaning=CL["0000197"]))
        setattr(cls, "CL:0000015",
            PermissibleValue(
                text="CL:0000015",
                description="""A germ cell that supports male gamete production. In some species, non-germ cells known as Sertoli cells also play a role in spermatogenesis.""",
                meaning=CL["0000015"]))
        setattr(cls, "CL:4023038",
            PermissibleValue(
                text="CL:4023038",
                description="""A glutamatergic neuron with a soma found in cortical layer 6b. They are transcriptomically related to corticothalamic-projecting neurons but have differential projections to the thalamus or anterior cingulate. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: Deep layer (non-IT) excitatory neuron', Author Categories: 'CrossArea_subclass', cluster L6b.""",
                meaning=CL["4023038"]))
        setattr(cls, "CL:1001009",
            PermissibleValue(
                text="CL:1001009",
                description="Any kidney arterial blood vessel cell that is part of some renal efferent arteriole.",
                meaning=CL["1001009"]))
        setattr(cls, "CL:0002394",
            PermissibleValue(
                text="CL:0002394",
                description="""A myeloid dendritic cell found in the blood, lymph nodes, tonsil, bone marrow, and spleen that is CD141-positive (BDCA-3), XCR1-positive, and Clec9A-positive. This cell-type can cross-present antigen to CD8-positive T cells and can produce inteferon-beta.""",
                meaning=CL["0002394"]))
        setattr(cls, "CL:0002313",
            PermissibleValue(
                text="CL:0002313",
                description="An ecto-epithelial cell of the prostate gland that secretes hormones.",
                meaning=CL["0002313"]))
        setattr(cls, "CL:0000006",
            PermissibleValue(
                text="CL:0000006",
                description="""Any sensory receptor cell that is a(n) neuron and is capable of some detection of stimulus involved in sensory perception.""",
                meaning=CL["0000006"]))
        setattr(cls, "CL:0000988",
            PermissibleValue(
                text="CL:0000988",
                description="A cell of a hematopoietic lineage.",
                meaning=CL["0000988"]))
        setattr(cls, "CL:0000444",
            PermissibleValue(
                text="CL:0000444",
                description="""A muscle cell in which the fibers are organised into sarcomeres but in which adjacent myofibrils are offset from each other, producing an oblique banding pattern.""",
                meaning=CL["0000444"]))
        setattr(cls, "CL:4033011",
            PermissibleValue(
                text="CL:4033011",
                description="""A(n) smooth muscle cell that is part of a(n) large intestine smooth muscle circular layer.""",
                meaning=CL["4033011"]))
        setattr(cls, "CL:0002673",
            PermissibleValue(
                text="CL:0002673",
                description="A skeletal muscle cell that is part of the tongue.",
                meaning=CL["0002673"]))
        setattr(cls, "CL:0009082",
            PermissibleValue(
                text="CL:0009082",
                description="""The human equivalent of a DN3 thymocyte; these thymocytes finish the process of beta selection.""",
                meaning=CL["0009082"]))
        setattr(cls, "CL:4023116",
            PermissibleValue(
                text="CL:4023116",
                description="""A spiral ganglion neuron that innervates outer hair cells. Type 1 spiral ganglion neurons are unmyelinated and unipolar.""",
                meaning=CL["4023116"]))
        setattr(cls, "CL:0002102",
            PermissibleValue(
                text="CL:0002102",
                description="""A CD38-negative naive B cell is a mature B cell that has the phenotype CD38-negative, surface IgD-positive, surface IgM-positive, and CD27-negative, that has not yet been activated by antigen in the periphery.""",
                meaning=CL["0002102"]))
        setattr(cls, "CL:0000782",
            PermissibleValue(
                text="CL:0000782",
                description="A dendritic cell of the myeloid lineage.",
                meaning=CL["0000782"]))
        setattr(cls, "CL:0004162",
            PermissibleValue(
                text="CL:0004162",
                description="""A cone whose sensitivity measurements have an average spectral peak of 358.2 nm. These cones are described in rat.""",
                meaning=CL["0004162"]))
        setattr(cls, "CL:1001432",
            PermissibleValue(
                text="CL:1001432",
                description="Any renal intercalated cell that is part of some collecting duct of renal tubule.",
                meaning=CL["1001432"]))
        setattr(cls, "CL:4052012",
            PermissibleValue(
                text="CL:4052012",
                description="""A specialized theca cell that forms the inner, highly vascularized layer of the theca surrounding ovarian follicles. Originating from progenitor theca cells, the theca interna cell is steroidogenic, playing a crucial role in the production of androgens, which serves as a precursor for estrogen synthesis in granulosa cells. This cell expresses luteinizing hormone receptors, enabling it to respond to hormonal signals that regulate steroidogenesis.""",
                meaning=CL["4052012"]))
        setattr(cls, "CL:0005012",
            PermissibleValue(
                text="CL:0005012",
                description="""A columnar/cuboidal epithelial cell with multiple motile cilia on its apical surface. These cells facilitate the movement of liquids such as mucus or cerebrospinal fluid across the epithelial surface.""",
                meaning=CL["0005012"]))
        setattr(cls, "CL:4033093",
            PermissibleValue(
                text="CL:4033093",
                description="""A stem cell that is part of the corneo-scleral limbus. This cell type resides at the basal layer of the epithelium and has a small size and high nuclear to cytoplasmatic ratio (Secker and Daniels, 2009). A limbal stem cell is responsible for corneal epithelial renewal and repair (Li et al., 2023), and to help maintain a clear corneal surface by preventing conjunctival epithelial cells from migrating onto the cornea (Wang et al., 2023).""",
                meaning=CL["4033093"]))
        setattr(cls, "CL:4033008",
            PermissibleValue(
                text="CL:4033008",
                description="A(n) vein endothelial cell that is part of a(n) respiratory system.",
                meaning=CL["4033008"]))
        setattr(cls, "CL:2000013",
            PermissibleValue(
                text="CL:2000013",
                description="Any skin fibroblast that is part of a skin of abdomen.",
                meaning=CL["2000013"]))
        setattr(cls, "CL:0009072",
            PermissibleValue(
                text="CL:0009072",
                description="""A thymic medullary epithelial cell that expresses AIRE or other canonical markers of mature mTECs like Fezf2.""",
                meaning=CL["0009072"]))
        setattr(cls, "CL:4030000",
            PermissibleValue(
                text="CL:4030000",
                description="""A melanocyte located in the vascular uvea and involved in photoprotection, regulation of oxidative damage and immune responses.""",
                meaning=CL["4030000"]))
        setattr(cls, "CL:0000576",
            PermissibleValue(
                text="CL:0000576",
                description="""Myeloid mononuclear recirculating leukocyte that can act as a precursor of tissue macrophages, osteoclasts and some populations of tissue dendritic cells.""",
                meaning=CL["0000576"]))
        setattr(cls, "CL:0005008",
            PermissibleValue(
                text="CL:0005008",
                description="An auditory hair cell located in the macula that is sensitive to auditory stimuli.",
                meaning=CL["0005008"]))
        setattr(cls, "CL:4023035",
            PermissibleValue(
                text="CL:4023035",
                description="A neuron that is derived from a precursor cell in the lateral ganglion eminence.",
                meaning=CL["4023035"]))
        setattr(cls, "CL:0002098",
            PermissibleValue(
                text="CL:0002098",
                description="""A cardiac myocyte that is connected to other cardiac myocytes by transverse intercalated discs (GO:0014704) at a regular interval.""",
                meaning=CL["0002098"]))
        setattr(cls, "CL:4023065",
            PermissibleValue(
                text="CL:4023065",
                description="A GABAergic cell located in the cerebral cortex that expresses meis2.",
                meaning=CL["4023065"]))
        setattr(cls, "CL:0000395",
            PermissibleValue(
                text="CL:0000395",
                description="A precursor of mature crystal cells.",
                meaning=CL["0000395"]))
        setattr(cls, "CL:0000170",
            PermissibleValue(
                text="CL:0000170",
                description="A cell that secretes glucagon.",
                meaning=CL["0000170"]))
        setattr(cls, "CL:4023020",
            PermissibleValue(
                text="CL:4023020",
                description="""A gamma motor neuron that innervates dynamic nuclear bag fibers (bag1 fibers) and enhances the sensitivities of Ia sensory neurons. They alter muscle spindle sensitivity and increases its discharge in response to velocity of muscle length (rather than just magnitude).""",
                meaning=CL["4023020"]))
        setattr(cls, "CL:0009013",
            PermissibleValue(
                text="CL:0009013",
                description="""A progenitor cell with hepatic and biliary lineage potential, identified in mouse and human, and anatomically restricted to the ductal plate of fetal liver.""",
                meaning=CL["0009013"]))
        setattr(cls, "CL:0001004",
            PermissibleValue(
                text="CL:0001004",
                description="""Immature CD8-alpha-positive CD11b-negative dendritic cell is a CD8-alpha-positive CD11b-negative dendritic cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0001004"]))
        setattr(cls, "CL:0009031",
            PermissibleValue(
                text="CL:0009031",
                description="A T cell that is located in a vermiform appendix.",
                meaning=CL["0009031"]))
        setattr(cls, "CL:4023111",
            PermissibleValue(
                text="CL:4023111",
                description="A pyramidal neuron with soma located in the cerebral cortex.",
                meaning=CL["4023111"]))
        setattr(cls, "CL:2000077",
            PermissibleValue(
                text="CL:2000077",
                description="Any striated muscle cell that is part of a skeletal muscle tissue of pectoralis major.",
                meaning=CL["2000077"]))
        setattr(cls, "CL:0002519",
            PermissibleValue(
                text="CL:0002519",
                description="""An interrenal epithelial kidney cell is an epithelial cell found in the anterior kidney of teleosts fish. This cell type is arranged in layers around the posterior cardinal vein and contains many mitochondria with tubulovesicular cristae. Interrenal chromaffin cells are interspersed among the tissue layer created by this cell type.""",
                meaning=CL["0002519"]))
        setattr(cls, "CL:0002425",
            PermissibleValue(
                text="CL:0002425",
                description="""A pro-T cell that is lin-negative, CD25-negative, CD127-negative, CD44-positive and kit-positive.""",
                meaning=CL["0002425"]))
        setattr(cls, "CL:4033080",
            PermissibleValue(
                text="CL:4033080",
                description="A(n) pulmonary alveolar type 2 cell that is cycling.",
                meaning=CL["4033080"]))
        setattr(cls, "CL:0002577",
            PermissibleValue(
                text="CL:0002577",
                description="An epithelial cell of the placenta.",
                meaning=CL["0002577"]))
        setattr(cls, "CL:4030028",
            PermissibleValue(
                text="CL:4030028",
                description="An amacrine cell that uses glycine as a neurotransmitter.",
                meaning=CL["4030028"]))
        setattr(cls, "CL:4030037",
            PermissibleValue(
                text="CL:4030037",
                description="""A spermatid in a late stage of maturation that has an elongated morphology and is transcriptionally inert when the acrosome is fully developed.""",
                meaning=CL["4030037"]))
        setattr(cls, "CL:0002350",
            PermissibleValue(
                text="CL:0002350",
                description="""An endothelial cell that lines the intracavitary lumen of the heart, separating the circulating blood from the underlying myocardium. This cell type releases a number of vasoactive substances including prostacyclin, nitrous oxide and endothelin.""",
                meaning=CL["0002350"]))
        setattr(cls, "CL:0000644",
            PermissibleValue(
                text="CL:0000644",
                description="""Type of radial astrocyte in the cerebellar cortex that have their cell bodies in the Purkinje cell layer and processes that extend into the molecular layer, terminating with bulbous endfeet at the pial surface. Bergmann glia express high densities of glutamate transporters that limit diffusion of the neurotransmitter glutamate during its release from synaptic terminals. Besides their role in early development of the cerebellum, Bergmann glia are also required for the pruning or addition of synapses.""",
                meaning=CL["0000644"]))
        setattr(cls, "CL:4033041",
            PermissibleValue(
                text="CL:4033041",
                description="An alveolar macrophage that expresses CCL3.",
                meaning=CL["4033041"]))
        setattr(cls, "CL:0007011",
            PermissibleValue(
                text="CL:0007011",
                description="Neuron that is part of the enteric nervous system.",
                meaning=CL["0007011"]))
        setattr(cls, "CL:0000650",
            PermissibleValue(
                text="CL:0000650",
                description="""A cell type that encapsulates the capillaries and venules in the kidney. This cell secretes mesangial matrix that provides the structural support for the capillaries.""",
                meaning=CL["0000650"]))
        setattr(cls, "CL:0000995",
            PermissibleValue(
                text="CL:0000995",
                meaning=CL["0000995"]))
        setattr(cls, "CL:0002525",
            PermissibleValue(
                text="CL:0002525",
                description="""A specialized epithelial cell that contains \"feet\" that interdigitate with the \"feet\" of other glomerular epithelial cells in the metanephros.""",
                meaning=CL["0002525"]))
        setattr(cls, "CL:1000434",
            PermissibleValue(
                text="CL:1000434",
                description="An epithelial cell that is part of the external acoustic meatus.",
                meaning=CL["1000434"]))
        setattr(cls, "CL:0002141",
            PermissibleValue(
                text="CL:0002141",
                description="""A parathyroid chief cell that is actively secreting hormone. Have large Golgi complexes with numerous vesicles and small membrane-bound granules; secretory granules are rare, cytoplasmic glycogen sparse, much of the cytoplasm being occupied by flat sacs of granular endoplasmic reticulum in parallel arrays; in normal humans, inactive chief cells outnumber active chief cells in a ratio of 3-5:1""",
                meaning=CL["0002141"]))
        setattr(cls, "CL:1000381",
            PermissibleValue(
                text="CL:1000381",
                description="""A type I vestibular sensory cell that is part of the epithelium of crista of ampulla of semicircular duct of membranous labyrinth.""",
                meaning=CL["1000381"]))
        setattr(cls, "CL:0000189",
            PermissibleValue(
                text="CL:0000189",
                description="A muscle cell that develops tension more slowly than a fast-twitch fiber.",
                meaning=CL["0000189"]))
        setattr(cls, "CL:0007006",
            PermissibleValue(
                text="CL:0007006",
                description="Mesodermal cell that is axially located and gives rise to the cells of the notochord.",
                meaning=CL["0007006"]))
        setattr(cls, "CL:4052028",
            PermissibleValue(
                text="CL:4052028",
                description="""A natural killer cell that is part of the uterus, specifically within the endometrium during the non-pregnant state and in the decidua during pregnancy. This cell exhibits dynamic changes in frequency throughout the menstrual cycle, with lower levels during menstruation and a significant increase during the mid-secretory phase and early pregnancy.""",
                meaning=CL["4052028"]))
        setattr(cls, "CL:4033026",
            PermissibleValue(
                text="CL:4033026",
                description="A perichondrial fibroblast that is part of the lung.",
                meaning=CL["4033026"]))
        setattr(cls, "CL:0001204",
            PermissibleValue(
                text="CL:0001204",
                description="""CD4-positive, alpha-beta long-lived T cell with the phenotype CD45RO-positive and CD127-positive. This cell type is also described as being CD25-negative, CD44-high, and CD122-high.""",
                meaning=CL["0001204"]))
        setattr(cls, "CL:0002296",
            PermissibleValue(
                text="CL:0002296",
                description="""An epithelial cell with high nuclear and cytoplasmic electron-density. This cell type is found in the deeper portions of the cortex but is more abundant in the medulla of the thymus.""",
                meaning=CL["0002296"]))
        setattr(cls, "CL:0003006",
            PermissibleValue(
                text="CL:0003006",
                description="""A G4 retinal ganglion cell that has post sympatic terminals in sublaminar layers S3 and S4 and is depolarized by illumination of its receptive field center.""",
                meaning=CL["0003006"]))
        setattr(cls, "CL:0002427",
            PermissibleValue(
                text="CL:0002427",
                description="A double-positive, alpha-beta thymocyte that is small and not proliferating.",
                meaning=CL["0002427"]))
        setattr(cls, "CL:0000963",
            PermissibleValue(
                text="CL:0000963",
                description="""A germinal center B cell that develops from a Bm3 B cell. This cell has the phenotype IgM-negative, IgD-positive, and CD38-positive.""",
                meaning=CL["0000963"]))
        setattr(cls, "CL:0002497",
            PermissibleValue(
                text="CL:0002497",
                description="A trophoblast giant cell derived from the mural trophectoderm.",
                meaning=CL["0002497"]))
        setattr(cls, "CL:0008045",
            PermissibleValue(
                text="CL:0008045",
                description="""A tanycyte of the subcommisural organ (SCO).  These cells extend long and slender fibers extending from their cell bodies in the ependyma toward fenestrated capillaries associated with the SCO, where they form a dense network surrounding these capillaries.""",
                meaning=CL["0008045"]))
        setattr(cls, "CL:4040002",
            PermissibleValue(
                text="CL:4040002",
                description="""Glial cell that provides support to the enteric nervous system. It is involved in enteric neurotransmission, in maintaining the integrity of the mucosal barrier of the gut and serves as a link between the nervous and immune systems of the gut. In enteric nerve strands, glial processes ensheath multiaxonal bundles which distinguishes enteric glia from all other peripheral glia. Ultrastructurally, the most conspicuous trait of an enteroglial cell is the presence of 10 nm filaments, which criss-cross the cell body, form axial bundles in the processes and appear to firmly anchor the cells to the ganglionic surfaces. Similar to astrocytes, their main constituent is glial fibrillary acidic protein (GFAP).""",
                meaning=CL["4040002"]))
        setattr(cls, "CL:0002086",
            PermissibleValue(
                text="CL:0002086",
                description="""A cardiac myocyte that is an excitable cells in the myocardium, specifically in the conducting system of heart.""",
                meaning=CL["0002086"]))
        setattr(cls, "CL:0000162",
            PermissibleValue(
                text="CL:0000162",
                description="""An epithelial cell of the stomach that is part of the fundic gastric gland. This cell is characterized by its pyramidal shape, abundant mitochondria, and a complex network of secretory canaliculi lined with microvilli. It secretes hydrochloric acid into the stomach lumen and produces intrinsic factor, essential for vitamin B12 absorption.""",
                meaning=CL["0000162"]))
        setattr(cls, "CL:1001033",
            PermissibleValue(
                text="CL:1001033",
                description="""An endothelial cell that is part of the peritubular capillary of the kidney. This cell is highly fenestrated and plays a vital role in the kidney's filtration process, enabling the exchange of materials between the blood and the renal tubules.""",
                meaning=CL["1001033"]))
        setattr(cls, "CL:0000992",
            PermissibleValue(
                text="CL:0000992",
                description="""Immature CD11c-low plasmacytoid dendritic cell is a CD11c-low plasmacytoid dendritic cell that is CD80-low and CD86-low.""",
                meaning=CL["0000992"]))
        setattr(cls, "CL:2000072",
            PermissibleValue(
                text="CL:2000072",
                description="Any microvascular endothelial cell that is part of a adipose tissue.",
                meaning=CL["2000072"]))
        setattr(cls, "CL:4033072",
            PermissibleValue(
                text="CL:4033072",
                description="A(n) gamma-delta T cell that is cycling.",
                meaning=CL["4033072"]))
        setattr(cls, "CL:0000900",
            PermissibleValue(
                text="CL:0000900",
                description="""A CD8-positive, alpha-beta T cell that has not experienced activation via antigen contact and has the phenotype CD45RA-positive, CCR7-positive and CD127-positive. This cell type is also described as being CD25-negative, CD62L-high and CD44-low.""",
                meaning=CL["0000900"]))
        setattr(cls, "CL:0002305",
            PermissibleValue(
                text="CL:0002305",
                description="""An epithelial cell of the distal convoluted tubule of the kidney that helps regulate systemic levels of potassium, sodium, calcium, and pH.""",
                meaning=CL["0002305"]))
        setattr(cls, "CL:4028001",
            PermissibleValue(
                text="CL:4028001",
                description="Any capillary endothelial cell that is part of a lung.",
                meaning=CL["4028001"]))
        setattr(cls, "CL:0002466",
            PermissibleValue(
                text="CL:0002466",
                description="""A CD11b-positive dendritic cell located in the serosal portion of the small intestine epithelium. This cell type is CD45-positive, MHC-II-positive, CD11c-low, CD103-negative.""",
                meaning=CL["0002466"]))
        setattr(cls, "CL:4052032",
            PermissibleValue(
                text="CL:4052032",
                description="""A CD8 T cell characterized by high expression of Granzyme H (GZMH). This cell exhibits a restricted TCR repertoire and elevated expression of cytotoxic, exhaustion, and type I interferon-stimulated gene signatures compared to controls.""",
                meaning=CL["4052032"]))
        setattr(cls, "CL:0000595",
            PermissibleValue(
                text="CL:0000595",
                description="An erythrocyte lacking a nucleus.",
                meaning=CL["0000595"]))
        setattr(cls, "CL:0000906",
            PermissibleValue(
                text="CL:0000906",
                description="""A CD8-positive, alpha-beta T cell with the phenotype CD69-positive, CD62L-negative, CD127-negative, CD25-positive, and CCR7-negative.""",
                meaning=CL["0000906"]))
        setattr(cls, "CL:0002639",
            PermissibleValue(
                text="CL:0002639",
                description="""An amniotic stem cell is a mesenchymalstem cell extracted from amniotic fluid. Amniotic stem cells are able to differentiate into various tissue type such as skin, cartilage, cardiac tissue, nerves, muscle, and bone""",
                meaning=CL["0002639"]))
        setattr(cls, "CL:1000510",
            PermissibleValue(
                text="CL:1000510",
                description="Any kidney epithelial cell that is part of some glomerular epithelium.",
                meaning=CL["1000510"]))
        setattr(cls, "CL:0000527",
            PermissibleValue(
                text="CL:0000527",
                description="A neuron which sends impulses peripherally to activate muscles or secretory cells.",
                meaning=CL["0000527"]))
        setattr(cls, "CL:1000721",
            PermissibleValue(
                text="CL:1000721",
                description="Any renal principal cell that is part of some papillary duct.",
                meaning=CL["1000721"]))
        setattr(cls, "CL:0000633",
            PermissibleValue(
                text="CL:0000633",
                description="""A tall supporting cell that is arranged in rows adjacent to the last row of outer phalangeal cells. This cell type constitutes the outer border of the organ of Corti.""",
                meaning=CL["0000633"]))
        setattr(cls, "CL:0002374",
            PermissibleValue(
                text="CL:0002374",
                description="A hair cell of the ear that contains the organs of balance and hearing.",
                meaning=CL["0002374"]))
        setattr(cls, "CL:1000424",
            PermissibleValue(
                text="CL:1000424",
                description="A chromaffin cell that is part of the paraaortic body.",
                meaning=CL["1000424"]))
        setattr(cls, "CL:0000017",
            PermissibleValue(
                text="CL:0000017",
                description="""A male germ cell that develops from spermatogonia. The euploid primary spermatocytes undergo meiosis and give rise to the haploid secondary spermatocytes which in turn give rise to spermatids.""",
                meaning=CL["0000017"]))
        setattr(cls, "CL:0019017",
            PermissibleValue(
                text="CL:0019017",
                description="A smooth muscle cell that is part of any lymphatic vessel.",
                meaning=CL["0019017"]))
        setattr(cls, "CL:0000257",
            PermissibleValue(
                text="CL:0000257",
                description="Any cell that in taxon some Eumycetozoa.",
                meaning=CL["0000257"]))
        setattr(cls, "CL:1000356",
            PermissibleValue(
                text="CL:1000356",
                description="A M cell that is part of the epithelium proper of duodenum.",
                meaning=CL["1000356"]))
        setattr(cls, "CL:0009042",
            PermissibleValue(
                text="CL:0009042",
                description="An enteroendocrine cell that is located in the colon.",
                meaning=CL["0009042"]))
        setattr(cls, "CL:0009027",
            PermissibleValue(
                text="CL:0009027",
                description="A transit amplifying cell that is part of a crypt of Lieberkuhn of large intestine.",
                meaning=CL["0009027"]))
        setattr(cls, "CL:0008022",
            PermissibleValue(
                text="CL:0008022",
                description="""A mesenchymal cell of the endocardial cushion.   These cells develop via an epithelial to mesenchymal transition when endocardial cells break cell-to-cell contacts and migrate into the cardiac jelly. Cells from this population form the heart septa and valves.""",
                meaning=CL["0008022"]))
        setattr(cls, "CL:1001568",
            PermissibleValue(
                text="CL:1001568",
                description="Any endothelial cell of vascular tree that is part of some pulmonary artery.",
                meaning=CL["1001568"]))
        setattr(cls, "CL:4023092",
            PermissibleValue(
                text="CL:4023092",
                description="""A pyramidal neuron which has an apical tree which is oriented towards the white matter.""",
                meaning=CL["4023092"]))
        setattr(cls, "CL:4023018",
            PermissibleValue(
                text="CL:4023018",
                description="""A transcriptomically distinct GABAergic interneuron with a soma located in a cerebral cortex and it expresses Parvalbumin. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: MGE-derived interneurons', Author Categories: 'CrossArea_subclass', cluster Pvalb.""",
                meaning=CL["4023018"]))
        setattr(cls, "CL:0000442",
            PermissibleValue(
                text="CL:0000442",
                description="""A cell with extensive dendritic processes found in the B cell areas (primary follicles and germinal centers) of lymphoid tissue. They are unrelated to the dendritic cell associated with T cells. Follicular dendritic cells have Fc receptors and C3b receptors, but unlike other dendritic cells, they do not process or present antigen in a way that allows recognition by T cells. Instead, they hold antigen in the form of immune complexes on their surfaces for long periods and can present antigen to B cells during an immune response.""",
                meaning=CL["0000442"]))
        setattr(cls, "CL:0001058",
            PermissibleValue(
                text="CL:0001058",
                description="""A plasmacytoid dendritic cell with the phenotype HLA-DRA-positive, CD123-positive, and CD11c-negative.""",
                meaning=CL["0001058"]))
        setattr(cls, "CL:0007010",
            PermissibleValue(
                text="CL:0007010",
                description="""Skeletogenic cell that has the potential to transform into an osteoblast, and develops from neural crest or mesodermal cells.""",
                meaning=CL["0007010"]))
        setattr(cls, "CL:4047051",
            PermissibleValue(
                text="CL:4047051",
                description="""An enterocyte of the human small intestine expressing bestrophin-4 (BEST4) calcium-activated ion channels.  These enterocytes have a disinctive transcriptomic profile and are scattered through the small intestine epithelium.""",
                meaning=CL["4047051"]))
        setattr(cls, "CL:0000574",
            PermissibleValue(
                text="CL:0000574",
                description="""A pigment cell derived from the neural crest. Contains pteridine and/or carotenoid pigments in structures called pterinosomes or erythrosomes. This gives an orange to red appearance.""",
                meaning=CL["0000574"]))
        setattr(cls, "CL:0011029",
            PermissibleValue(
                text="CL:0011029",
                description="""An explosive cell containing one giant secretory organelle called a cnidocyst (also known as a cnida (plural cnidae) or nematocyst) that contains a toxin responsible for the stings delivered by a cnidarian to other organisms. Cnidae are used to capture prey and as a defense against predators. The presence of cnidocytes defines the phylum Cnidaria (corals, sea anemones, hydrae, jellyfish, etc.).""",
                meaning=CL["0011029"]))
        setattr(cls, "CL:1001573",
            PermissibleValue(
                text="CL:1001573",
                description="Cell of the nasopharyngeal epithelium.",
                meaning=CL["1001573"]))
        setattr(cls, "CL:0000481",
            PermissibleValue(
                text="CL:0000481",
                description="A peptide hormone secreting cell that secretes cholecystokin stimulating hormone.",
                meaning=CL["0000481"]))
        setattr(cls, "CL:1000691",
            PermissibleValue(
                text="CL:1000691",
                meaning=CL["1000691"]))
        setattr(cls, "CL:0005024",
            PermissibleValue(
                text="CL:0005024",
                description="""A motor neuron that innervates a skeletal muscle.  These motor neurons are all excitatory and cholinergic.""",
                meaning=CL["0005024"]))
        setattr(cls, "CL:0000118",
            PermissibleValue(
                text="CL:0000118",
                description="""Basket cells are inhibitory GABAergic interneurons of the brain. In general, dendrites of basket cells are free branching and contain smooth spines. Axons are highly branched. The branched axonal arborizations give rise to basket-like structures that surround the soma of the target cell. Basket cells form axo-somatic synapses, meaning their synapses target somas of other cells.""",
                meaning=CL["0000118"]))
        setattr(cls, "CL:1001606",
            PermissibleValue(
                text="CL:1001606",
                description="Keratinocyte from foreskin.",
                meaning=CL["1001606"]))
        setattr(cls, "CL:0002641",
            PermissibleValue(
                text="CL:0002641",
                description="An epithelial cell of the esophageal gland proper.",
                meaning=CL["0002641"]))
        setattr(cls, "CL:0011022",
            PermissibleValue(
                text="CL:0011022",
                description="A fibroblast that is part of skin of back.",
                meaning=CL["0011022"]))
        setattr(cls, "CL:0000058",
            PermissibleValue(
                text="CL:0000058",
                description="""Skeletogenic cell that is typically non-terminally differentiated, secretes an avascular, GAG rich matrix; is not buried in cartilage tissue matrix, retains the ability to divide, located adjacent to cartilage tissue (including within the perichondrium), and develops from prechondroblast (and thus prechondrogenic) cell.""",
                meaning=CL["0000058"]))
        setattr(cls, "CL:4023056",
            PermissibleValue(
                text="CL:4023056",
                description="""A type of mouse mesothelial fibroblast that is derived from the neural crest, is localized on blood vessels, and is a key component of the pia and arachnoid membranes surrounding the brain.""",
                meaning=CL["4023056"]))
        setattr(cls, "CL:4023188",
            PermissibleValue(
                text="CL:4023188",
                description="""A retinal ganglion cell that originate in the ganglion cell layer of the retina, and project to the parvocellular layers of the lateral geniculate nucleus (LGN). These cells are known as midget retinal ganglion cells due to the small sizes of their dendritic trees and cell bodies.""",
                meaning=CL["4023188"]))
        setattr(cls, "CL:0000107",
            PermissibleValue(
                text="CL:0000107",
                description="A neuron whose cell body is within an autonomic ganglion.",
                meaning=CL["0000107"]))
        setattr(cls, "CL:0000955",
            PermissibleValue(
                text="CL:0000955",
                description="""A pre-B-II cell is a precursor B cell that expresses immunoglobulin mu heavy chain (IgHmu+), and lack expression of CD34, TdT, immunoglobulin kappa light chain and immunoglobulin lambda light chain.""",
                meaning=CL["0000955"]))
        setattr(cls, "CL:0002354",
            PermissibleValue(
                text="CL:0002354",
                description="""A hematopoietic stem found in the yolk sac. In mice, this cell type is Sca-1-negative, CD45-negative, MHC-negative, HSA-positive, AA4.1-positive, CD44-positive.""",
                meaning=CL["0002354"]))
        setattr(cls, "CL:0000936",
            PermissibleValue(
                text="CL:0000936",
                description="""A lymphoid progenitor cell that is found in bone marrow, gives rise to B cells, T cells, natural killer cells and dendritic cells, and has the phenotype Lin-negative, Kit-positive, Sca-1-positive, FLT3-positive, CD34-positive, CD150 negative, and GlyA-negative.""",
                meaning=CL["0000936"]))
        setattr(cls, "CL:0000468",
            PermissibleValue(
                text="CL:0000468",
                description="""A precursor of the central nervous system that gives rise to both neurons and glial cells.""",
                meaning=CL["0000468"]))
        setattr(cls, "CL:0000740",
            PermissibleValue(
                text="CL:0000740",
                description="""The set of neurons that receives neural inputs via bipolar, horizontal and amacrine cells. The axons of these cells make up the optic nerve.""",
                meaning=CL["0000740"]))
        setattr(cls, "CL:0002550",
            PermissibleValue(
                text="CL:0002550",
                description="A fibroblast that is part of the conjuctiva of the eye.",
                meaning=CL["0002550"]))
        setattr(cls, "CL:0008038",
            PermissibleValue(
                text="CL:0008038",
                description="""A large, multipolar lower motor neuron of the brainstem and spinal cord that innervates the extrafusal muscle fibers of skeletal muscle and are directly responsible for initiating their contraction. While their cell bodies are in the CNS (in the anterior gray horn of the spinal cord), they are part of the somatic nervous system - a branch of the PNS.""",
                meaning=CL["0008038"]))
        setattr(cls, "CL:4033064",
            PermissibleValue(
                text="CL:4033064",
                description="A tissue-resident macrophage that is part of the uterus.",
                meaning=CL["4033064"]))
        setattr(cls, "CL:4042022",
            PermissibleValue(
                text="CL:4042022",
                description="""A progenitor cell of the central nervous system that differentiates exclusively onto astrocytes. This progenitor cell expresses CD44 and S100 calcium-binding protein B.""",
                meaning=CL["4042022"]))
        setattr(cls, "CL:0000544",
            PermissibleValue(
                text="CL:0000544",
                meaning=CL["0000544"]))
        setattr(cls, "CL:0002539",
            PermissibleValue(
                text="CL:0002539",
                description="A smooth muscle cell of the aorta.",
                meaning=CL["0002539"]))
        setattr(cls, "CL:4023033",
            PermissibleValue(
                text="CL:4023033",
                description="""A retinal ganglion cell that is depolarized by decreased illumination of their receptive field center.""",
                meaning=CL["4023033"]))
        setattr(cls, "CL:4033016",
            PermissibleValue(
                text="CL:4033016",
                description="""A myofibroblast that is part of an alveoli during alveolarization. The contractile force of this cell elongates the secondary crest, while producing a framework of elastin and tenascin. During the maturation of the septa, secondary crest myofibroblasts, together with matrix fibroblasts, secrete metalloproteinases and other ECM‐remodeling proteins to thin the septal tip ECM. The secondary crest myofibroblast continues producing elastin, eventually undergoing apoptosis during adulthood.""",
                meaning=CL["4033016"]))
        setattr(cls, "CL:0001051",
            PermissibleValue(
                text="CL:0001051",
                description="""A CD4-positive, alpha-beta T cell that has the phenotype CXCR3-negative, CCR6-negative.""",
                meaning=CL["0001051"]))
        setattr(cls, "CL:2000002",
            PermissibleValue(
                text="CL:2000002",
                description="""A specialized, enlarged, connective tissue cell of the decidua with enlarged nucleus, dense membrane‐bound secretory granules and cytoplasmic accumulation of glycogen and lipid droplets. These cells develop by the transformation of endometrial stromal cells during decidualization.""",
                meaning=CL["2000002"]))
        setattr(cls, "CL:4033082",
            PermissibleValue(
                text="CL:4033082",
                description="A(n) basal cell that is cycling.",
                meaning=CL["4033082"]))
        setattr(cls, "CL:2000007",
            PermissibleValue(
                text="CL:2000007",
                description="Chondrocyte forming the hyaline cartilage found in the knee joint.",
                meaning=CL["2000007"]))
        setattr(cls, "CL:1001036",
            PermissibleValue(
                text="CL:1001036",
                description="A cell that is part of a vasa recta.",
                meaning=CL["1001036"]))
        setattr(cls, "CL:1000286",
            PermissibleValue(
                text="CL:1000286",
                description="A smooth muscle cell that is part of the rectum.",
                meaning=CL["1000286"]))
        setattr(cls, "CL:0002381",
            PermissibleValue(
                text="CL:0002381",
                description="A conidium that has only one nucleus.",
                meaning=CL["0002381"]))
        setattr(cls, "CL:0000867",
            PermissibleValue(
                text="CL:0000867",
                description="A tissue-resident macrophage found in a secondary lymphoid organ.",
                meaning=CL["0000867"]))
        setattr(cls, "CL:0002242",
            PermissibleValue(
                text="CL:0002242",
                description="A cell containing at least one nucleus.",
                meaning=CL["0002242"]))
        setattr(cls, "CL:0002180",
            PermissibleValue(
                text="CL:0002180",
                description="An epithelial cell of the stomach. This cell produces mucous.",
                meaning=CL["0002180"]))
        setattr(cls, "CL:2000020",
            PermissibleValue(
                text="CL:2000020",
                description="Any native cell that is part of a inner cell mass.",
                meaning=CL["2000020"]))
        setattr(cls, "CL:0002558",
            PermissibleValue(
                text="CL:0002558",
                description="A fibroblast that is part of villous mesenchyme.",
                meaning=CL["0002558"]))
        setattr(cls, "CL:2000083",
            PermissibleValue(
                text="CL:2000083",
                description="Any hair follicle dermal papilla cell that is part of a scalp.",
                meaning=CL["2000083"]))
        setattr(cls, "CL:0000696",
            PermissibleValue(
                text="CL:0000696",
                description="A cell that stores and secretes pancreatic polypeptide hormone.",
                meaning=CL["0000696"]))
        setattr(cls, "CL:0002365",
            PermissibleValue(
                text="CL:0002365",
                description="""An epithelial cell of the medullary thymus. This cell type expresses a diverse range of tissue-specific antigens. This promiscuous gene expression is a cell-autonomous property of medullary epithelial cells and is maintained during the entire period of thymic T cell output.""",
                meaning=CL["0002365"]))
        setattr(cls, "CL:1000332",
            PermissibleValue(
                text="CL:1000332",
                description="A serous secreting cell that is part of the epithelium of terminal bronchiole.",
                meaning=CL["1000332"]))
        setattr(cls, "CL:0002338",
            PermissibleValue(
                text="CL:0002338",
                description="""A natural killer cell that is developmentally immature, has the phenotype CD34-negative, CD56-positive, CD117-positive, CD122-positive,and CD161-positive.""",
                meaning=CL["0002338"]))
        setattr(cls, "CL:0009087",
            PermissibleValue(
                text="CL:0009087",
                description="An extravillous trophoblast that is polynuclear.",
                meaning=CL["0009087"]))
        setattr(cls, "CL:4030020",
            PermissibleValue(
                text="CL:4030020",
                description="A renal alpha-intercalated cell that is part of the renal connecting tubule.",
                meaning=CL["4030020"]))
        setattr(cls, "CL:0009041",
            PermissibleValue(
                text="CL:0009041",
                description="""A tuft cell that is part of the colonic epithelium, primarily adapted for microbial sensing in the dense colonic microbiota. Unlike its small intestinal counterpart, it does not participate in parasite-driven tuft cell–ILC2 circuits. Instead, it detects bacterial metabolites via taste-signaling pathways (Strine and Craig, 2022). The colonic tuft cell plays a key role in epithelial repair, modulates inflammatory responses through IL-25 secretion, and contributes to intestinal homeostasis by balancing microbiome interactions (Sebastian et al., 2021).""",
                meaning=CL["0009041"]))
        setattr(cls, "CL:4033019",
            PermissibleValue(
                text="CL:4033019",
                description="An ON bipolar cell type with dendrites selectively contacting S-cones.",
                meaning=CL["4033019"]))
        setattr(cls, "CL:0000577",
            PermissibleValue(
                text="CL:0000577",
                description="""A subtype of enteroendocrine cells found in the gastrointestinal mucosa, particularly in the glands of pyloric antrum; duodenum; and ileum. These cell type secretes serotonin and some neurotransmitters including enkephalins and substance P. Their secretory granules stain readily with silver (argentaffin stain).""",
                meaning=CL["0000577"]))
        setattr(cls, "CL:0000389",
            PermissibleValue(
                text="CL:0000389",
                meaning=CL["0000389"]))
        setattr(cls, "CL:0000136",
            PermissibleValue(
                text="CL:0000136",
                description="""A fat-storing cell found mostly in the abdominal cavity and subcutaneous tissue of mammals. Fat is usually stored in the form of triglycerides.""",
                meaning=CL["0000136"]))
        setattr(cls, "CL:0019026",
            PermissibleValue(
                text="CL:0019026",
                description="""Any hepatocyte that is part of the liver lobule periportal region. These cells are primarily involved in oxidative energy metabolism.""",
                meaning=CL["0019026"]))
        setattr(cls, "CL:4030004",
            PermissibleValue(
                text="CL:4030004",
                description="""A large epithelial cell found in the thymus. This cell type may internalize thymocytes through extensions of plasma membrane. The cell surface and cytoplasmic vacuoles of a thymic nurse cell express MHC Class I and MHC Class II antigens. The interaction of these antigens with a developing thymocyte determines whether the thymocyte undergoes positive or negative selection.""",
                meaning=CL["4030004"]))
        setattr(cls, "CL:0002419",
            PermissibleValue(
                text="CL:0002419",
                description="A T cell that expresses a T cell receptor complex and has completed T cell selection.",
                meaning=CL["0002419"]))
        setattr(cls, "CL:0010001",
            PermissibleValue(
                text="CL:0010001",
                description="A stromal cell that is part_of a bone marrow.",
                meaning=CL["0010001"]))
        setattr(cls, "CL:0000418",
            PermissibleValue(
                text="CL:0000418",
                description="""An epithelial cell found in C. elegans that firmly hold the outer body wall and the lips to the inner cylinder of the pharynx in a manner that keeps these organs from breaking apart, while still giving each organ freedom of movement during feeding.""",
                meaning=CL["0000418"]))
        setattr(cls, "CL:0000186",
            PermissibleValue(
                text="CL:0000186",
                description="""An animal cell that has characteristics of both a fibroblast cell and a smooth muscle cell.""",
                meaning=CL["0000186"]))
        setattr(cls, "CL:0000675",
            PermissibleValue(
                text="CL:0000675",
                description="A mature sexual reproductive cell of the female germline.",
                meaning=CL["0000675"]))
        setattr(cls, "CL:0008055",
            PermissibleValue(
                text="CL:0008055",
                description="""A secretory epithelial cell of the respiratory tract epithelium.  These cells have an endodermal origin.""",
                meaning=CL["0008055"]))
        setattr(cls, "CL:0011027",
            PermissibleValue(
                text="CL:0011027",
                description="Any fibroblast that is part of skeletal muscle tissue.",
                meaning=CL["0011027"]))
        setattr(cls, "CL:0002416",
            PermissibleValue(
                text="CL:0002416",
                description="A Vgamma1.1-positive, Vdelta6.3-positive thymocyte that is CD24-negative.",
                meaning=CL["0002416"]))
        setattr(cls, "CL:0002379",
            PermissibleValue(
                text="CL:0002379",
                description="""A neurecto-epithelial cell found in the arachnoid villi of dura mater. This cell type facilitates flow of cerebrospinal fluid into the blood.""",
                meaning=CL["0002379"]))
        setattr(cls, "CL:4052027",
            PermissibleValue(
                text="CL:4052027",
                description="""A theca cell undergoing atresia, characterized by distinct morphological changes including hypertrophy, altered cell shape, and disrupted layered organization. This cell exhibits reduced steroidogenic capacity and changes in surrounding vascularization. The onset of theca cell atresia can vary, occurring at different stages of follicle atresia depending on the phase of folliculogenesis.""",
                meaning=CL["4052027"]))
        setattr(cls, "CL:1001575",
            PermissibleValue(
                text="CL:1001575",
                description="Squamous cell of uterine cervix epithelium.",
                meaning=CL["1001575"]))
        setattr(cls, "CL:0000932",
            PermissibleValue(
                text="CL:0000932",
                description="""A type II NK T cell that has been recently activated, secretes interferon-gamma, and has the phenotype CD69-positive and downregulated NK markers.""",
                meaning=CL["0000932"]))
        setattr(cls, "CL:0002435",
            PermissibleValue(
                text="CL:0002435",
                description="""A CD8-positive, CD4-negative thymocyte that expresses high levels of the alpha-beta T cell receptor and is CD69-positive.""",
                meaning=CL["0002435"]))
        setattr(cls, "CL:0011108",
            PermissibleValue(
                text="CL:0011108",
                description="Epithelial cell that is part of the colon epithelium.",
                meaning=CL["0011108"]))
        setattr(cls, "CL:4030048",
            PermissibleValue(
                text="CL:4030048",
                description="A DRD1-expressing medium spiny neuron that is part of a striosome of dorsal striatum.",
                meaning=CL["4030048"]))
        setattr(cls, "CL:0000961",
            PermissibleValue(
                text="CL:0000961",
                description="""A follicular B cell that is IgD-positive, CD23-negative, and CD38-negative. This naive cell type is activated in the extrafollicular areas through interaction with interdigitating dendritic cells and antigen-specific CD4-positive T cells.""",
                meaning=CL["0000961"]))
        setattr(cls, "CL:0009099",
            PermissibleValue(
                text="CL:0009099",
                description="""A progenitor cell that is a tissue-resident mesenchymal cell, important for skeletal muscle regeneration, and able to differentiate into both adipocytes or fibroblasts.""",
                meaning=CL["0009099"]))
        setattr(cls, "CL:1000325",
            PermissibleValue(
                text="CL:1000325",
                description="A goblet cell that is part of the epithelium proper of jejunum.",
                meaning=CL["1000325"]))
        setattr(cls, "CL:0002184",
            PermissibleValue(
                text="CL:0002184",
                description="""A flat or angular epithelial cell with condensed nuclei and darkly staining cytoplasm containing numerous intermediate filaments inserted into desmosomes contacting surrounding supporting cells; lie in contact with the basal lamina of olfactory epithelium.""",
                meaning=CL["0002184"]))
        setattr(cls, "CL:0000706",
            PermissibleValue(
                text="CL:0000706",
                description="""A specialized ependymal cell that is part of the choroid plexus epithelium, responsible for producing cerebrospinal fluid (CSF) by selectively filtering and modifying blood plasma components before secreting it into the brain and spinal cord. This cell is characterized by a brush border on its apical surface, which enhances the secretion of CSF.""",
                meaning=CL["0000706"]))
        setattr(cls, "CL:0000642",
            PermissibleValue(
                text="CL:0000642",
                description="""An agranular supporting cell of the anterior pituitary (adenohypophysis) that is characterized by a star-like morphology and ability to form follicles. Folliculostellate cells communicate with each other and with endocrine cells via gap junctions.""",
                meaning=CL["0000642"]))
        setattr(cls, "CL:0002618",
            PermissibleValue(
                text="CL:0002618",
                description="An endothelial cell of the umbilical vein.",
                meaning=CL["0002618"]))
        setattr(cls, "CL:4040005",
            PermissibleValue(
                text="CL:4040005",
                description="A mesenchymal stem cell that is part of the apical papilla tooth root.",
                meaning=CL["4040005"]))
        setattr(cls, "CL:0008025",
            PermissibleValue(
                text="CL:0008025",
                description="A neuron that release noradrenaline (noriphinephrine) as a neurotransmitter.",
                meaning=CL["0008025"]))
        setattr(cls, "CL:0002035",
            PermissibleValue(
                text="CL:0002035",
                description="""A hematopoietic progenitor that has restricted self-renewal capability. Cell is Kit-positive, Ly6-positive, CD150-negative and Flt3-negative.""",
                meaning=CL["0002035"]))
        setattr(cls, "CL:0002559",
            PermissibleValue(
                text="CL:0002559",
                description="An animal cell that is part of a hair follicle.",
                meaning=CL["0002559"]))
        setattr(cls, "CL:0000810",
            PermissibleValue(
                text="CL:0000810",
                description="""An immature alpha-beta T cell that is located in the thymus and is CD4-positive and CD8-negative.""",
                meaning=CL["0000810"]))
        setattr(cls, "CL:0005003",
            PermissibleValue(
                text="CL:0005003",
                description="""A non-terminally differentiated cell that originates from the neural crest and differentiates into a leucophore.""",
                meaning=CL["0005003"]))
        setattr(cls, "CL:0002581",
            PermissibleValue(
                text="CL:0002581",
                description="A preadipocyte that is part of a perirenal fat tissue.",
                meaning=CL["0002581"]))
        setattr(cls, "CL:0002533",
            PermissibleValue(
                text="CL:0002533",
                description="An immature CD16-positive myeloid dendritic cell is CD80-low, CD86-low, and MHCII-low.",
                meaning=CL["0002533"]))
        setattr(cls, "CL:0002088",
            PermissibleValue(
                text="CL:0002088",
                description="""This is a cell found in the gastrointestinal tract of mammals and serves as a pacemaker that triggers gut contraction. ICCs mediate inputs from the enteric nervous system to smooth muscle cells and are thought to be the cells from which gastrointestinal stromal tumors (GISTs) arise.""",
                meaning=CL["0002088"]))
        setattr(cls, "CL:4033039",
            PermissibleValue(
                text="CL:4033039",
                description="An alpha-beta CD8 T cell that resides in the lung.",
                meaning=CL["4033039"]))
        setattr(cls, "CL:1000342",
            PermissibleValue(
                text="CL:1000342",
                description="An enterocyte that is part of the epithelium proper of ileum.",
                meaning=CL["1000342"]))
        setattr(cls, "CL:0004125",
            PermissibleValue(
                text="CL:0004125",
                description="A retinal ganglion cell C inner that has dense dendritic diversity.",
                meaning=CL["0004125"]))
        setattr(cls, "CL:0002672",
            PermissibleValue(
                text="CL:0002672",
                description="""A multi-fate stem cell that can give rise to different retinal cell types including rod and cone cells.""",
                meaning=CL["0002672"]))
        setattr(cls, "CL:0000485",
            PermissibleValue(
                text="CL:0000485",
                description="""Mast cell subtype that contains only the serine protease trypase in its granules. These cells are primarily found in mucosal tissue, such as intestinal mucosa and alveoli. They depend upon T-cells for development of phenotype.""",
                meaning=CL["0000485"]))
        setattr(cls, "CL:0000940",
            PermissibleValue(
                text="CL:0000940",
                description="""An alpha-beta T cell that is found in the lamina propria of mucosal tissues and is restricted by the MR-1 molecule.""",
                meaning=CL["0000940"]))
        setattr(cls, "CL:0002240",
            PermissibleValue(
                text="CL:0002240",
                description="A fibroblast in the bone marrow.",
                meaning=CL["0002240"]))
        setattr(cls, "CL:1000702",
            PermissibleValue(
                text="CL:1000702",
                description="Any smooth muscle cell that is part of some kidney pelvis smooth muscle.",
                meaning=CL["1000702"]))
        setattr(cls, "CL:0000683",
            PermissibleValue(
                text="CL:0000683",
                description="""A cell that transports hormones from neurosecretory cells. This nerve cell is characterized by bipolar shape and endfeet that contact a basal lamina around blood vessels, and/or the pia mater or vitreous body of the eye and additionally contact the ventricular surface or sub-retinal space.""",
                meaning=CL["0000683"]))
        setattr(cls, "CL:0002483",
            PermissibleValue(
                text="CL:0002483",
                description="A melanocyte that produces pigment within the hair follicle.",
                meaning=CL["0002483"]))
        setattr(cls, "CL:0010011",
            PermissibleValue(
                text="CL:0010011",
                description="A GABAergic interneuron whose soma is located in the cerebral cortex.",
                meaning=CL["0010011"]))
        setattr(cls, "CL:0009052",
            PermissibleValue(
                text="CL:0009052",
                description="A smooth muscle cell that is located in the anorectum.",
                meaning=CL["0009052"]))
        setattr(cls, "CL:0000827",
            PermissibleValue(
                text="CL:0000827",
                description="""A lymphoid progenitor cell of the T cell lineage, with some lineage specific marker expression, but not yet fully committed to the T cell lineage.""",
                meaning=CL["0000827"]))
        setattr(cls, "CL:1000549",
            PermissibleValue(
                text="CL:1000549",
                description="An epithelial cell that is part of a cortical collecting duct.",
                meaning=CL["1000549"]))
        setattr(cls, "CL:4023008",
            PermissibleValue(
                text="CL:4023008",
                description="""A glutamatergic neuron located in the cerebral cortex that projects to structures of telencephalic origins.""",
                meaning=CL["4023008"]))
        setattr(cls, "CL:0002138",
            PermissibleValue(
                text="CL:0002138",
                description="""A endothelial cell of a lymphatic vessel. The border of the oak leaf-shaped endothelial cell of initial lymphatics are joined by specialized buttons. The discontinuous feature of buttons distinguishes them from zippers in collecting lymphatics, but both types of junctions are composed of proteins typical of adherens junctions and tight junctions found in the endothelium of blood vessels. Buttons seal the sides of flaps of the oak leaf-shaped endothelial cell, leaving open the tips of flaps as routes for fluid entry without disassembly and reformation of intercellular junctions.""",
                meaning=CL["0002138"]))
        setattr(cls, "CL:1001111",
            PermissibleValue(
                text="CL:1001111",
                description="An epithelial cell that is part of some loop of Henle thin descending limb.",
                meaning=CL["1001111"]))
        setattr(cls, "CL:1001505",
            PermissibleValue(
                text="CL:1001505",
                description="""The secretory neurons of the paraventricular nucleus that synthesize and secrete vasopressin, corticotropin-releasing factor (CRF) and thyrotropin-releasing hormone (TRH) into blood vessels in the hypothalamo-pituitary portal system.""",
                meaning=CL["1001505"]))
        setattr(cls, "CL:0000619",
            PermissibleValue(
                text="CL:0000619",
                meaning=CL["0000619"]))
        setattr(cls, "CL:0000730",
            PermissibleValue(
                text="CL:0000730",
                description="A cell at the front of a migrating epithelial sheet.",
                meaning=CL["0000730"]))
        setattr(cls, "CL:0000407",
            PermissibleValue(
                text="CL:0000407",
                description="A cell that anchors the cell body of a scolopidial neuron to the integument.",
                meaning=CL["0000407"]))
        setattr(cls, "CL:0000024",
            PermissibleValue(
                text="CL:0000024",
                description="An undifferentiated germ cell that proliferates rapidly and gives rise to oocytes.",
                meaning=CL["0000024"]))
        setattr(cls, "CL:4047034",
            PermissibleValue(
                text="CL:4047034",
                description="""A smooth muscle cell that is part of the muscularis externa of the stomach wall. It is characterized by its fusiform shape, involuntary control, and ability to generate slow, sustained contractions. This cell is organized in distinct layers and is essential for gastric motility and digestion.""",
                meaning=CL["4047034"]))
        setattr(cls, "CL:0000041",
            PermissibleValue(
                text="CL:0000041",
                description="""A fully differentiated eosinophil, a granular leukocyte with a nucleus that usually has two lobes connected by one or more slender threads, and cytoplasm containing coarse, round granules that are uniform in size and which can be stained by the dye eosin. Cells are also differentiated from other granulocytes by a small nuclear-to-cytoplasm ratio (1:3). This cell type is CD49d-positive.""",
                meaning=CL["0000041"]))
        setattr(cls, "CL:1000839",
            PermissibleValue(
                text="CL:1000839",
                description="Any epithelial cell of proximal tubule that is part of some proximal straight tubule.",
                meaning=CL["1000839"]))
        setattr(cls, "CL:0002540",
            PermissibleValue(
                text="CL:0002540",
                description="A mesenchymal stem cell that is part of the bone marrow.",
                meaning=CL["0002540"]))
        setattr(cls, "CL:0005019",
            PermissibleValue(
                text="CL:0005019",
                description="Ghrelin secreting cells found in the endocrine pancreas.",
                meaning=CL["0005019"]))
        setattr(cls, "CL:0000966",
            PermissibleValue(
                text="CL:0000966",
                description="""A germinal center B cell that has the phenotype CD77-negative, IgD-negative, and CD38-positive. These cells have undergone somatic mutation of the B cell receptor.""",
                meaning=CL["0000966"]))
        setattr(cls, "CL:0011032",
            PermissibleValue(
                text="CL:0011032",
                description="""An enterocyte that possesses a large supranuclear vacuolar system that preferentially internalizes dietary protein via receptor-mediated and fluid-phase endocytosis for intracellular digestion and trans-cellular transport. In zebrafish these cells are located in the posterior region of the mid intestine throughout life. In mammals they are found in the ileum pre-weaning and later are replaced by mature enterocytes.""",
                meaning=CL["0011032"]))
        setattr(cls, "CL:0004235",
            PermissibleValue(
                text="CL:0004235",
                description="""An amacrine cell with a medium dendritic field and post-synaptic terminals in S2 and S3. This cell type releases the neurotransmitter gamma-aminobutyric acid (GABA).""",
                meaning=CL["0004235"]))
        setattr(cls, "CL:0004252",
            PermissibleValue(
                text="CL:0004252",
                description="An amicrine that has a medium dendritic field.",
                meaning=CL["0004252"]))
        setattr(cls, "CL:0000913",
            PermissibleValue(
                text="CL:0000913",
                description="""CD8-positive, alpha-beta memory T cell with the phenotype CCR7-negative, CD127-positive, CD45RA-negative, CD45RO-positive, and CD25-negative.""",
                meaning=CL["0000913"]))
        setattr(cls, "CL:4042001",
            PermissibleValue(
                text="CL:4042001",
                description="""A GABAergic interneuron that has its soma located in the striatum and that has an enriched expression of the genes TAC3 and LHX6.""",
                meaning=CL["4042001"]))
        setattr(cls, "CL:0019032",
            PermissibleValue(
                text="CL:0019032",
                description="""A tuft cell that is part of the intestinal epithelium, characterized by a distinctive apical tuft and lateral cytospinules connecting to neighbouring cells. This cell senses luminal stimuli via taste receptors and succinate signalling, initiating type 2 immune responses through the secretion of interleukin-25 while modulating epithelial regeneration through prostaglandin synthesis. It expresses key molecular markers such as doublecortin-like kinase 1 (DCLK1) in mice (Hendel et al., 2022), and KIT proto-oncogene in humans (Huang et al., 2024). Developed from intestinal crypt stem cells, this cell requires transcription factor POU2F3 for its development.""",
                meaning=CL["0019032"]))
        setattr(cls, "CL:0000121",
            PermissibleValue(
                text="CL:0000121",
                description="""An inhibitory neuron and the sole output neuron of the cerebellar cortex, the Purkinje cell's soma is located between the granular and molecular layers of the cerebellum. It is one of the largest neural cells in the mammalian brain, ranging from 50 to 80 micrometres in diameter. Purkinje cells have planar, fan-shaped dendrites that branch extensively with little overlap. This cell type receives synaptic input from parallel fibres, which modulate high-frequency spike activity known as \"simple spikes,\" and climbing fibres, which modulate infrequent calcium spike activity known as \"complex spikes\". Purkinje cells are involved in motor coordination, particularly in correcting movements in progress.""",
                meaning=CL["0000121"]))
        setattr(cls, "CL:0000587",
            PermissibleValue(
                text="CL:0000587",
                description="A thermoreceptor cell that detects reduced temperatures.",
                meaning=CL["0000587"]))
        setattr(cls, "CL:0002306",
            PermissibleValue(
                text="CL:0002306",
                description="An epithelial cell of the proximal tubule of the kidney.",
                meaning=CL["0002306"]))
        setattr(cls, "CL:4033001",
            PermissibleValue(
                text="CL:4033001",
                description="A(n) endothelial cell that is part of a(n) arteriole of lymph node.",
                meaning=CL["4033001"]))
        setattr(cls, "CL:0002203",
            PermissibleValue(
                text="CL:0002203",
                description="A tuft cell that is part of the epithelium of large intestine.",
                meaning=CL["0002203"]))
        setattr(cls, "CL:0003004",
            PermissibleValue(
                text="CL:0003004",
                description="""A bistratified retinal ganglion cell that has a small dendritic field with sparse density that terminates at the intersection of the S4-S5 sublaminar level, and a second dendrite field that is medium in size and degree of arborization that terminates in sublaminar layer S2.""",
                meaning=CL["0003004"]))
        setattr(cls, "CL:0002006",
            PermissibleValue(
                text="CL:0002006",
                description="""A megakaryocyte erythroid progenitor cell that is Kit-positive and is Sca1-negative, CD34-negative, CD90-negative, IL7r-alpha-negative and Fcgr II/III-low.""",
                meaning=CL["0002006"]))
        setattr(cls, "CL:0000860",
            PermissibleValue(
                text="CL:0000860",
                description="""A monocyte that responds rapidly to microbial stimuli by secreting cytokines and antimicrobial factors and which is characterized by high expression of CCR2 in both rodents and humans, negative for the lineage markers CD3, CD19, and CD20, and of larger size than non-classical monocytes.""",
                meaning=CL["0000860"]))
        setattr(cls, "CL:4070011",
            PermissibleValue(
                text="CL:4070011",
                description="A motor neuron that closes the lateral teeth.",
                meaning=CL["4070011"]))
        setattr(cls, "CL:0001035",
            PermissibleValue(
                text="CL:0001035",
                description="A connective tissue cell found in bone.",
                meaning=CL["0001035"]))
        setattr(cls, "CL:4033065",
            PermissibleValue(
                text="CL:4033065",
                description="""A mature B cell that serves as an intermediate stage in the differentiation of naive B cells into a plasmablast. A preplasmablast expresses CD30 and IL-6R and lacks expression of CD20, CD23, CD38 and CD138.""",
                meaning=CL["4033065"]))
        setattr(cls, "CL:0009105",
            PermissibleValue(
                text="CL:0009105",
                description="A fibroblastic reticular cell found in the lymph node T cell domain.",
                meaning=CL["0009105"]))
        setattr(cls, "CL:0000374",
            PermissibleValue(
                text="CL:0000374",
                description="""An epidermal cell that is part of a cell cluster organ of the insect integument (such as a sensillum) and that secretes a cuticular specialization, often in the form of a hair, bristle, peg or scale. The base of this specialization is often surrounded by a socket produced by a closely associated tormogen cell.""",
                meaning=CL["0000374"]))
        setattr(cls, "CL:1000718",
            PermissibleValue(
                text="CL:1000718",
                description="Any renal principal cell that is part of some inner medullary collecting duct.",
                meaning=CL["1000718"]))
        setattr(cls, "CL:1001434",
            PermissibleValue(
                text="CL:1001434",
                description="""A neuron residing in the olfactory bulb that serve to process and refine signals arising from olfactory sensory neurons""",
                meaning=CL["1001434"]))
        setattr(cls, "CL:0002375",
            PermissibleValue(
                text="CL:0002375",
                description="""A multipotent progenitor cell that develops from a migratory neural crest cell. The schwann cell precursor is embedded among axons, with minimal extracellular space separating them from nerve cell membranes. This cell lacks a basal lamina, which distinguishes it from more mature Schwann cells. In rodents, cadherin-19 (Cdh19) serves as a specific marker for this developmental stage.""",
                meaning=CL["0002375"]))
        setattr(cls, "CL:0017000",
            PermissibleValue(
                text="CL:0017000",
                description="""An ionocyte that is part of the lung epithelium. The cells from this type are major sources of the CFTR protein in human and mice.""",
                meaning=CL["0017000"]))
        setattr(cls, "CL:0000008",
            PermissibleValue(
                text="CL:0000008",
                description="""Cell that is part of the migratory cranial neural crest population. Migratory cranial neural crest cells develop from premigratory cranial neural crest cells and have undergone epithelial to mesenchymal transition and delamination.""",
                meaning=CL["0000008"]))
        setattr(cls, "CL:0002037",
            PermissibleValue(
                text="CL:0002037",
                description="""Intraepithelial T cells with a memory phenotype of CD2-positive, CD5-positive, and CD44-positive.""",
                meaning=CL["0002037"]))
        setattr(cls, "CL:0002344",
            PermissibleValue(
                text="CL:0002344",
                description="""A natural killer cell that is developmentally immature, has the phenotype CD34-negative, CD56-negative, CD117-positive, CD122-positive,and CD161-positive.""",
                meaning=CL["0002344"]))
        setattr(cls, "CL:0009075",
            PermissibleValue(
                text="CL:0009075",
                description="A thymic medullary epithelial cell that expresses muscle-specific biomarkers.",
                meaning=CL["0009075"]))
        setattr(cls, "CL:0000084",
            PermissibleValue(
                text="CL:0000084",
                description="""A type of lymphocyte whose defining characteristic is the expression of a T cell receptor complex.""",
                meaning=CL["0000084"]))
        setattr(cls, "CL:0000190",
            PermissibleValue(
                text="CL:0000190",
                description="""A muscle cell that can develop high tension rapidly. It is usually innervated by a single alpha neuron.""",
                meaning=CL["0000190"]))
        setattr(cls, "CL:0000116",
            PermissibleValue(
                text="CL:0000116",
                description="""Pioneer neurons establish a pathway in the developing central nervous system and then undergo programmed cell death once the adult axons, which follow them, have made connections with the target site. Thus, they are a transient cell type involved in axon guidance.""",
                meaning=CL["0000116"]))
        setattr(cls, "CL:0002302",
            PermissibleValue(
                text="CL:0002302",
                description="""A synovial cell that is macrophage-like, characterized by surface ruffles or lamellipodia, plasma membrane invaginations and associated micropinocytotic vesicles, Golgi apparatus and little granular endoplasmic reticulum.""",
                meaning=CL["0002302"]))
        setattr(cls, "CL:4023029",
            PermissibleValue(
                text="CL:4023029",
                description="""A medium spiny neuron that expresses dopamine type 2 receptors and projects to the external globus pallidus.""",
                meaning=CL["4023029"]))
        setattr(cls, "CL:0002125",
            PermissibleValue(
                text="CL:0002125",
                description="""A circulating gamma-delta T cell that expresses RORgamma(t), is CD27-negative and is capable of IL-17 secretion.""",
                meaning=CL["0002125"]))
        setattr(cls, "CL:0000767",
            PermissibleValue(
                text="CL:0000767",
                description="""Any of the immature or mature forms of a granular leukocyte that in its mature form has an irregularly shaped, pale-staining nucleus that is partially constricted into two lobes, and with cytoplasm that contains coarse, bluish-black granules of variable size. Basophils contain vasoactive amines such as histamine and serotonin, which are released on appropriate stimulation. A basophil is CD123-positive, CD193-positive, CD203c-positive, and FceRIa-positive.""",
                meaning=CL["0000767"]))
        setattr(cls, "CL:0000922",
            PermissibleValue(
                text="CL:0000922",
                description="""An alpha-beta T cell expressing NK call markers that is CD1d restricted and expresses a diverse TCR repertoire. Type II NKT cells do not become activated by alpha-galactosylceramide when presented by CD1d.""",
                meaning=CL["0000922"]))
        setattr(cls, "CL:0000030",
            PermissibleValue(
                text="CL:0000030",
                description="""A non-terminally differentiated cell that develops form the neuroectoderm. Glioblast has the potential to differentiate into various types of glial cells, including astrocytes and oligodendrocytes.""",
                meaning=CL["0000030"]))
        setattr(cls, "CL:0000774",
            PermissibleValue(
                text="CL:0000774",
                description="""A late eosinophilic metamyelocyte in which the nucleus is in the form of a curved or coiled band, not having acquired the typical multilobar shape of the mature eosinophil.""",
                meaning=CL["0000774"]))
        setattr(cls, "CL:1000441",
            PermissibleValue(
                text="CL:1000441",
                description="An epithelial cell that is part of the viscerocranial mucosa.",
                meaning=CL["1000441"]))
        setattr(cls, "CL:0000845",
            PermissibleValue(
                text="CL:0000845",
                description="""A mature B cell that is located in the marginal zone of the spleen with the phenotype CD23-negative and CD21-positive and expressing a B cell receptor usually reactive to bacterial cell wall components or senescent self components such as oxidized-LDL. This cell type is also described as being CD19-positive, B220-positive, IgM-high, AA4-negative, CD35-high.""",
                meaning=CL["0000845"]))
        setattr(cls, "CL:1000803",
            PermissibleValue(
                text="CL:1000803",
                description="A cell that is part of an interstitial compartment of an inner renal medulla.",
                meaning=CL["1000803"]))
        setattr(cls, "CL:0002446",
            PermissibleValue(
                text="CL:0002446",
                description="A NK1.1-positive T cell that is Ly49Cl-negative.",
                meaning=CL["0002446"]))
        setattr(cls, "CL:4033067",
            PermissibleValue(
                text="CL:4033067",
                description="""A follicular cell of ovary that differentiates from a cuboidal granulosa cell during the secondary follicle stage. Mural granulosa cells line the inner surface of the follicle wall, surrounding the fluid-filled antral cavity. These cells produce oestrogen during the follicular phase in response to follicle-stimulating hormone (FSH), and progesterone after ovulation in response to luteinizing hormone (LH).""",
                meaning=CL["4033067"]))
        setattr(cls, "CL:0000153",
            PermissibleValue(
                text="CL:0000153",
                description="A cell that secretes glycosaminoglycans.",
                meaning=CL["0000153"]))
        setattr(cls, "CL:0002052",
            PermissibleValue(
                text="CL:0002052",
                description="""A pre-B cell that is pre-BCR-negative, and the kappa- and lambda- light immunoglobulin light chain-negative, CD43-low, and is BP-1-positive, CD45R-positive and CD25-positive. This cell type is also described as being AA4-positive, IgM-negative, CD19-positive, CD43-low/negative, and HSA-positive.""",
                meaning=CL["0002052"]))
        setattr(cls, "CL:0002046",
            PermissibleValue(
                text="CL:0002046",
                description="""A pro-B cell that is CD22-positive, CD34-positive, CD38-positive and TdT-positive (has TdT activity). Pre-BCR is expressed on the cell surface. Cell is CD19-negative, CD20-negative, complement receptor type 2-negative and CD10-low. D-to-J recombination of the heavy chain occurs at this stage.""",
                meaning=CL["0002046"]))
        setattr(cls, "CL:4042038",
            PermissibleValue(
                text="CL:4042038",
                description="""A type of primary motor neuron situated in the rostral region of the spinal cord. RoP neurons extend their axons to innervate the ventral trunk musculature.""",
                meaning=CL["4042038"]))
        setattr(cls, "CL:0000670",
            PermissibleValue(
                text="CL:0000670",
                description="""A primordial germ cell is a diploid germ cell precursors that transiently exist in the embryo before they enter into close association with the somatic cells of the gonad and become irreversibly committed as germ cells.""",
                meaning=CL["0000670"]))
        setattr(cls, "CL:0000504",
            PermissibleValue(
                text="CL:0000504",
                description="""A enteroendocrine cell part of the glands of the gastric mucosa. They produce histamine and peptides such as chromogranins. This cell type respond to gastrin by releasing histamine which acts as a paracrine stimulator of the release of hydrochloric acid from the gastric parietal cells.""",
                meaning=CL["0000504"]))
        setattr(cls, "CL:0000807",
            PermissibleValue(
                text="CL:0000807",
                description="""A thymocyte that has the phenotype CD4-negative, CD8-negative, CD44-negative, and CD25-positive and expressing the T cell receptor beta-chain in complex with the pre-T cell receptor alpha chain.""",
                meaning=CL["0000807"]))
        setattr(cls, "CL:1000413",
            PermissibleValue(
                text="CL:1000413",
                description="A blood vessel endothelial cell that is part of an arterial endothelium.",
                meaning=CL["1000413"]))
        setattr(cls, "CL:0002312",
            PermissibleValue(
                text="CL:0002312",
                description="""An acidophilic cell of the anterior pituitary that produces growth hormone, somatotropin.""",
                meaning=CL["0002312"]))
        setattr(cls, "CL:0002282",
            PermissibleValue(
                text="CL:0002282",
                description="""An enteroendocrine cell which produces a gastrin- and cholecystokinin-like peptide. The apical microvilli-rich plasma membrane is in open contact with the small intestine mucosa. This cell type is devoid of gastrin-17 but contains other fragments of the gastrin polypeptide.""",
                meaning=CL["0002282"]))
        setattr(cls, "CL:2000031",
            PermissibleValue(
                text="CL:2000031",
                description="Any neuron that is part of a lateral line ganglion.",
                meaning=CL["2000031"]))
        setattr(cls, "CL:0009062",
            PermissibleValue(
                text="CL:0009062",
                description="""A specialized type of CD4 positive T cell, the follicular helper T cell (TFH cell), that upregulates CXCR5 expression to enable its follicular localization. These specialised T cells reside in the germinal center of the lymph node.""",
                meaning=CL["0009062"]))
        setattr(cls, "CL:0000397",
            PermissibleValue(
                text="CL:0000397",
                description="Any interneuron that has its soma located in some ganglion.",
                meaning=CL["0000397"]))
        setattr(cls, "CL:0002612",
            PermissibleValue(
                text="CL:0002612",
                description="A neuron of the ventral spinal cord.",
                meaning=CL["0002612"]))
        setattr(cls, "CL:0000496",
            PermissibleValue(
                text="CL:0000496",
                description="A photoreceptor cell that is sensitive to green light.",
                meaning=CL["0000496"]))
        setattr(cls, "CL:4033054",
            PermissibleValue(
                text="CL:4033054",
                description="""A cell that is adjacent to a vessel. A perivascular cell plays a crucial role in maintaining vascular function and tissue homeostasis. This cell type regulates vessel integrity and flow dynamics.""",
                meaning=CL["4033054"]))
        setattr(cls, "CL:4052048",
            PermissibleValue(
                text="CL:4052048",
                description="""A cuboidal epithelial cell that is part of the intercalated duct of salivary gland. This cell expresses proteins commonly associated with acinar cells and displays calcium signaling characteristics similar to secretory cells, indicating an active role in the secretory process rather than ion reabsorption.""",
                meaning=CL["4052048"]))
        setattr(cls, "CL:2000090",
            PermissibleValue(
                text="CL:2000090",
                description="Any stellate cell that is part of a dentate gyrus of hippocampal formation.",
                meaning=CL["2000090"]))
        setattr(cls, "CL:0000350",
            PermissibleValue(
                text="CL:0000350",
                description="Any extraembryonic cell that is part of some amnioserosa.",
                meaning=CL["0000350"]))
        setattr(cls, "CL:0002436",
            PermissibleValue(
                text="CL:0002436",
                description="""A mature CD4-positive, CD8-negative alpha-beta T cell found in the thymus that is CD24-low and has high expression of the T cell receptor.""",
                meaning=CL["0002436"]))
        setattr(cls, "CL:0003017",
            PermissibleValue(
                text="CL:0003017",
                description="A retinal ganglion B cell that has post synaptic terminals in S2.",
                meaning=CL["0003017"]))
        setattr(cls, "CL:0002179",
            PermissibleValue(
                text="CL:0002179",
                description="""A simple columnar cell that populates the entire luminal surface including the gastric pits. This cell types secrete mucus to form a thick protective, lubricant layer over the gastric wall.""",
                meaning=CL["0002179"]))
        setattr(cls, "CL:0000079",
            PermissibleValue(
                text="CL:0000079",
                description="""An epithelial cell, organized into multiple layers, with only the basal layer being in contact with the basement membrane.""",
                meaning=CL["0000079"]))
        setattr(cls, "CL:0004216",
            PermissibleValue(
                text="CL:0004216",
                description="A type 5 cone bipolar cell with diffuse axonal branches.",
                meaning=CL["0004216"]))
        setattr(cls, "CL:3000004",
            PermissibleValue(
                text="CL:3000004",
                description="""A neuron type that is located in a peripheral nervous system and it transmits sensory information from the peripheral (PNS) to the central nervous system (CNS). A sensory neuron converts physical (light, sound, touch) or chemical (such as taste and smell) stimuli into an electrical signal through a process known as sensory transduction. The function of a sensory neuron is to carry informations from the external environment and internal body conditions to the central nervous system for further processing.""",
                meaning=CL["3000004"]))
        setattr(cls, "CL:0001056",
            PermissibleValue(
                text="CL:0001056",
                description="A dendritic cell with the phenotype HLA-DRA-positive.",
                meaning=CL["0001056"]))
        setattr(cls, "CL:0000521",
            PermissibleValue(
                text="CL:0000521",
                description="Any cell that in taxon some Fungi.",
                meaning=CL["0000521"]))
        setattr(cls, "CL:0011010",
            PermissibleValue(
                text="CL:0011010",
                description="A cell derived from the mesoderm that is found at the periphery of the embryo.",
                meaning=CL["0011010"]))
        setattr(cls, "CL:1000344",
            PermissibleValue(
                text="CL:1000344",
                description="A Paneth cell that is part of the epithelium proper of small intestine.",
                meaning=CL["1000344"]))
        setattr(cls, "CL:0000249",
            PermissibleValue(
                text="CL:0000249",
                meaning=CL["0000249"]))
        setattr(cls, "CL:0002474",
            PermissibleValue(
                text="CL:0002474",
                description="""A MHC-II-negative classical monocyte located in lymphoid tissue that is F4/80-positive, CD11c-negative, and CD11b-high.""",
                meaning=CL["0002474"]))
        setattr(cls, "CL:0002069",
            PermissibleValue(
                text="CL:0002069",
                description="""Mostly cylindrical, resemble Type 1 in their contents and the presence of a kinocilium and stereocilium apically; much greater variation in size, some almost span the entire thickness of the sensory epithelium, while others are smaller than Type 1; receive multiple efferent nerve boutons around their bases as well as afferent endings, which are small expansions rather than chalices.""",
                meaning=CL["0002069"]))
        setattr(cls, "CL:4028004",
            PermissibleValue(
                text="CL:4028004",
                description="""A pulmonary interstitial fibroblast that is part of the alveolus and contains lipid droplets.""",
                meaning=CL["4028004"]))
        setattr(cls, "CL:0003025",
            PermissibleValue(
                text="CL:0003025",
                description="""A retinal ganglion cell C inner that has sparse dendritic density, and large dendritic field.""",
                meaning=CL["0003025"]))
        setattr(cls, "CL:0009015",
            PermissibleValue(
                text="CL:0009015",
                description="""A follicular dendritic cell located in the Peyer's patch. These cells from a meshwork in which Peyer's patch B cells reside.""",
                meaning=CL["0009015"]))
        setattr(cls, "CL:0002551",
            PermissibleValue(
                text="CL:0002551",
                description="Any skin fibroblast that is part of some dermis.",
                meaning=CL["0002551"]))
        setattr(cls, "CL:0009044",
            PermissibleValue(
                text="CL:0009044",
                description="""A lymphocyte that resides in the lamina propria of the small intestine. Lamina propria leukocytes and intraepithelial lymphocytes are the effector compartments of the gut mucosal immune system. Lymphocytes circulate through gut associated lymphoid tissues until recruitment by intestinal antigens. They are involved in the gut immune response.""",
                meaning=CL["0009044"]))
        setattr(cls, "CL:0002503",
            PermissibleValue(
                text="CL:0002503",
                description="""A cell of the adventitial layer of ductal structures such as the uterer, defent duct, biliary duct, etc""",
                meaning=CL["0002503"]))
        setattr(cls, "CL:0017005",
            PermissibleValue(
                text="CL:0017005",
                description="A lymphocyte that has gotten larger after being stimulated by an antigen.",
                meaning=CL["0017005"]))
        setattr(cls, "CL:0001048",
            PermissibleValue(
                text="CL:0001048",
                description="""A CD4-positive, CD25-positive, CCR4-positive, alpha-beta T regulatory cell with the phenotype HLA-DRA-positive, indicating recent activation.""",
                meaning=CL["0001048"]))
        setattr(cls, "CL:0001032",
            PermissibleValue(
                text="CL:0001032",
                description="Granule cell that is part of the cerebral cortex.",
                meaning=CL["0001032"]))
        setattr(cls, "CL:0002157",
            PermissibleValue(
                text="CL:0002157",
                description="""A cell type that makes up the highly vascular membrane lining the marrow cavity of long bones.""",
                meaning=CL["0002157"]))
        setattr(cls, "CL:0000394",
            PermissibleValue(
                text="CL:0000394",
                description="""A phagocytic hemocyte, responsible for the engulfment of small particles, microbes, and apoptotic tissue debris. It may also secretes antimicrobial peptides and contribute to the production and secretion of proteins of the hemolymph.""",
                meaning=CL["0000394"]))
        setattr(cls, "CL:4033037",
            PermissibleValue(
                text="CL:4033037",
                description="A mucus secreting cell of a submucosal gland of the tracheobronchial tree.",
                meaning=CL["4033037"]))
        setattr(cls, "CL:4047023",
            PermissibleValue(
                text="CL:4047023",
                description="""A fibroblast located in the lamina propria of the intestinal mucosa. This cell expresses PDGFRα and CD81 and is negative for α-smooth muscle actin (α-SMA). This cell is predominantly located in the small intestine adjacent to myofibroblasts surrounding the crypts. It is capable of synthesizing extracellular matrix components and structural proteins such as collagen and elastin.""",
                meaning=CL["4047023"]))
        setattr(cls, "CL:2000094",
            PermissibleValue(
                text="CL:2000094",
                description="""Any epithelial cell of viscerocranial mucosa that is part of a nasal cavity respiratory epithelium.""",
                meaning=CL["2000094"]))
        setattr(cls, "CL:0002051",
            PermissibleValue(
                text="CL:0002051",
                description="A pre-BCR positive B cell that is CD38-high.",
                meaning=CL["0002051"]))
        setattr(cls, "CL:0000601",
            PermissibleValue(
                text="CL:0000601",
                description="""A mechanoreceptor in the organ of Corti. In mammals the outer hair cells are arranged in three rows which are further from the modiolus than the single row of inner hair cells. The motile properties of the outer hair cells may contribute actively to tuning the sensitivity and frequency selectivity of the cochlea.""",
                meaning=CL["0000601"]))
        setattr(cls, "CL:0000838",
            PermissibleValue(
                text="CL:0000838",
                description="A progenitor cell restricted to the lymphoid lineage.",
                meaning=CL["0000838"]))
        setattr(cls, "CL:4030017",
            PermissibleValue(
                text="CL:4030017",
                description="An epithelial cell located in the late distal convoluted tubule.",
                meaning=CL["4030017"]))
        setattr(cls, "CL:0004224",
            PermissibleValue(
                text="CL:0004224",
                description="""A broadly stratifying amacrine cell that has a small dendritic field and post-synaptic terminals in S2 and S3. This cell type releases the neurotransmitter glycine.""",
                meaning=CL["0004224"]))
        setattr(cls, "CL:1000420",
            PermissibleValue(
                text="CL:1000420",
                description="A myoepithelial cell that is part of the terminal lactiferous duct.",
                meaning=CL["1000420"]))
        setattr(cls, "CL:0000295",
            PermissibleValue(
                text="CL:0000295",
                description="A peptide hormone secreting cell that produces growth hormone, somatotropin.",
                meaning=CL["0000295"]))
        setattr(cls, "CL:4033043",
            PermissibleValue(
                text="CL:4033043",
                description="""A macrophage that is part of the lung connective tissue (pulmonary interstitium). This cell performs tissue remodeling and contributes to barrier immunity through antigen presentation.""",
                meaning=CL["4033043"]))
        setattr(cls, "CL:0000202",
            PermissibleValue(
                text="CL:0000202",
                description="""A mechanoreceptor cell of the auditory or vestibular system that is sensitive to auditory stimuli. The accessory sensory structures are arranged so that appropriate stimuli cause movement of the hair-like projections (stereocilia and kinocilia) which relay the information centrally in the nervous system.""",
                meaning=CL["0000202"]))
        setattr(cls, "CL:0009018",
            PermissibleValue(
                text="CL:0009018",
                description="A lymphocyte that resides in the lamina propria of the large intestine.",
                meaning=CL["0009018"]))
        setattr(cls, "CL:2000078",
            PermissibleValue(
                text="CL:2000078",
                description="Any pericyte cell that is part of a placenta.",
                meaning=CL["2000078"]))
        setattr(cls, "CL:1000272",
            PermissibleValue(
                text="CL:1000272",
                description="Any secretory cell that is part of some lung.",
                meaning=CL["1000272"]))
        setattr(cls, "CL:0009034",
            PermissibleValue(
                text="CL:0009034",
                description="A dendritic cell that is located in a vermiform appendix.",
                meaning=CL["0009034"]))
        setattr(cls, "CL:0000721",
            PermissibleValue(
                text="CL:0000721",
                meaning=CL["0000721"]))
        setattr(cls, "CL:0000196",
            PermissibleValue(
                text="CL:0000196",
                description="""A muscle cell that is involved in the mechanism of insect flight. This encompasses both, cells that power flight and cells that control flight.""",
                meaning=CL["0000196"]))
        setattr(cls, "CL:1001319",
            PermissibleValue(
                text="CL:1001319",
                description="Any cell that is part of some urinary bladder.",
                meaning=CL["1001319"]))
        setattr(cls, "CL:0000339",
            PermissibleValue(
                text="CL:0000339",
                description="An early neural cell developing from the early ependymal cell of the neural tube.",
                meaning=CL["0000339"]))
        setattr(cls, "CL:0000631",
            PermissibleValue(
                text="CL:0000631",
                description="""Cells forming a framework supporting the organ of Corti. Specific cells are those of Claudius, Deiters and Hensen.""",
                meaning=CL["0000631"]))
        setattr(cls, "CL:0008027",
            PermissibleValue(
                text="CL:0008027",
                description="""A bipolar neuron found in the retina that is synapsed by rod photoreceptor cells.  These neurons have axons that arborize and synapse to targets in inner plexiform layers 4 and 5 and depolarize in response to light.""",
                meaning=CL["0008027"]))
        setattr(cls, "CL:0004238",
            PermissibleValue(
                text="CL:0004238",
                description="""A bistratified amacrine cell with a medium dendritic field, a flat and sparse dendritic arbor, and post-synaptic terminals at the intersections of S1 and S2, and S3 and S4.""",
                meaning=CL["0004238"]))
        setattr(cls, "CL:0000035",
            PermissibleValue(
                text="CL:0000035",
                description="A stem cell that self-renews as well as give rise to a single mature cell type.",
                meaning=CL["0000035"]))
        setattr(cls, "CL:1001097",
            PermissibleValue(
                text="CL:1001097",
                description="""A smooth muscle cell found in the wall of the afferent arteriole. This cell contracts and relaxes in response to changes in blood pressure, a process known as a myogenic response, to alter artery diameter and regulate blood flow into the glomeruli.""",
                meaning=CL["1001097"]))
        setattr(cls, "CL:1000838",
            PermissibleValue(
                text="CL:1000838",
                description="""Any epithelial cell of proximal tubule that is part of some proximal convoluted tubule and has part some brush border.""",
                meaning=CL["1000838"]))
        setattr(cls, "CL:3000000",
            PermissibleValue(
                text="CL:3000000",
                description="A ciliated epithelial cell of the esophagus.",
                meaning=CL["3000000"]))
        setattr(cls, "CL:0000881",
            PermissibleValue(
                text="CL:0000881",
                description="""A border associated macrophage that is adjacent to a small blood vessel of a brain. A perivascular macrophage expresses the markers CD14, CD16 and CD163. In homeostatic conditions, this central nervous system macrophage has a non-motile cell body with extending and retracting projections through the blood vessel wall.""",
                meaning=CL["0000881"]))
        setattr(cls, "CL:0002437",
            PermissibleValue(
                text="CL:0002437",
                description="""A mature CD8-positive, CD4-negative alpha-beta T cell found in the thymus that is CD24-low and has high expression of the T cell receptor.""",
                meaning=CL["0002437"]))
        setattr(cls, "CL:0002320",
            PermissibleValue(
                text="CL:0002320",
                description="""A cell of the supporting or framework tissue of the body, arising chiefly from the embryonic mesoderm and including adipose tissue, cartilage, and bone.""",
                meaning=CL["0002320"]))
        setattr(cls, "CL:1000616",
            PermissibleValue(
                text="CL:1000616",
                description="Any kidney medulla cell that is part of some outer medulla of kidney.",
                meaning=CL["1000616"]))
        setattr(cls, "CL:0003015",
            PermissibleValue(
                text="CL:0003015",
                description="""A G11 retinal ganglion cell that has post synaptic terminals in sublaminar layer S4 and is depolarized by illumination of its receptive field center.""",
                meaning=CL["0003015"]))
        setattr(cls, "CL:0002359",
            PermissibleValue(
                text="CL:0002359",
                description="""A hematopoietic stem cell of the placenta. This cell type is first observed E10.5 This cell type may give rise to fetal liver hematopoietic stem cells.""",
                meaning=CL["0002359"]))
        setattr(cls, "CL:4052011",
            PermissibleValue(
                text="CL:4052011",
                description="""An enterocyte found in the follicle-associated epithelium (FAE) that covers Peyer's patches and other mucosa-associated lymphoid tissues. This cell has reduced absorptive capacity and expresses higher levels of chemokines CCL20 and CXCL16, compared to regular villus enterocytes. It contributes to antigen sampling and immune interactions, supporting the specialized function of the FAE in mucosal immunity.""",
                meaning=CL["4052011"]))
        setattr(cls, "CL:4052040",
            PermissibleValue(
                text="CL:4052040",
                description="""A tuft cell that is part of the epithelium of the stomach. This cell is characterized by gastric chemosensation and immune regulation through IL-25 secretion, which activates ILC2s to produce IL-13, driving epithelial remodelling and tuft cell expansion. Unlike intestinal tuft cells, which are primarily involved in helminth defense and type 2 immunity, the tuft cell of the stomach is primarily involved in inflammation, metaplasia, and hyperplasia.""",
                meaning=CL["4052040"]))
        setattr(cls, "CL:0005010",
            PermissibleValue(
                text="CL:0005010",
                description="A cuboidal epithelial cell of the kidney that regulates acid/base balance.",
                meaning=CL["0005010"]))
        setattr(cls, "CL:0002623",
            PermissibleValue(
                text="CL:0002623",
                description="An acinar cell of salivary gland.",
                meaning=CL["0002623"]))
        setattr(cls, "CL:1001516",
            PermissibleValue(
                text="CL:1001516",
                description="""The various hormone- or neurotransmitter-secreting cells present throughout the mucosa of the intestinal tract.""",
                meaning=CL["1001516"]))
        setattr(cls, "CL:0000713",
            PermissibleValue(
                text="CL:0000713",
                meaning=CL["0000713"]))
        setattr(cls, "CL:0009116",
            PermissibleValue(
                text="CL:0009116",
                description="""A progenitor cell with the potential to differentiate into luminal epithelial cells of mammary glands. In mouse, CD61 and c-kit were found to be coexpressed by the majority of, but not all, committed luminal progenitor cells.""",
                meaning=CL["0009116"]))
        setattr(cls, "CL:0011002",
            PermissibleValue(
                text="CL:0011002",
                description="""A motor neuron that is generated only on limb levels and send axons into the limb mesenchyme.""",
                meaning=CL["0011002"]))
        setattr(cls, "CL:4023080",
            PermissibleValue(
                text="CL:4023080",
                description="""a L6 intratelencephalic projecting glutamatergic neuron of the primary motor cortex that has stellate pyramidal morphology.""",
                meaning=CL["4023080"]))
        setattr(cls, "CL:0009071",
            PermissibleValue(
                text="CL:0009071",
                description="A thymic medullary epithelial cell considered to be a pre-AIRE mTEC population.",
                meaning=CL["0009071"]))
        setattr(cls, "CL:0000652",
            PermissibleValue(
                text="CL:0000652",
                description="""This cell type produces and secretes melatonin and forms the pineal parenchyma. Extending from each cell body, which has a spherical, oval or lobulated mucleus, are one or more tortuous basophilic processes, containing parallel microtubules known as synaptic ribbons. These processes end in expanded terminal buds near capillaries or less, frequently, ependymal cells of the pineal recess. The terminal buds contain granular endoplasmic reticulum, mitochondria and electron-dense cored vesicles, which store monoamines and polypeptide hormones, release of which appears to require sympathetic innervation.""",
                meaning=CL["0000652"]))
        setattr(cls, "CL:4023127",
            PermissibleValue(
                text="CL:4023127",
                description="a KNDy neuron that is located in the arcuate nucleus of the hypothalamus.",
                meaning=CL["4023127"]))
        setattr(cls, "CL:0000862",
            PermissibleValue(
                text="CL:0000862",
                description="A macrophage that suppresses immune responses.",
                meaning=CL["0000862"]))
        setattr(cls, "CL:0000993",
            PermissibleValue(
                text="CL:0000993",
                description="""Mature CD11c-low plasmacytoid dendritic cell is a CD11c-low plasmacytoid dendritic cell that is CD83-high and is CD80-positive, CD86-positive, and MHCII-positive.""",
                meaning=CL["0000993"]))
        setattr(cls, "CL:0002009",
            PermissibleValue(
                text="CL:0002009",
                description="""A progenitor cell that can give rise to plasmacytoid and myeloid dendritic cells, and to monocytes and macrophages.""",
                meaning=CL["0002009"]))
        setattr(cls, "CL:0002603",
            PermissibleValue(
                text="CL:0002603",
                description="An astrocyte of the cerebellum.",
                meaning=CL["0002603"]))
        setattr(cls, "CL:0009060",
            PermissibleValue(
                text="CL:0009060",
                description="A mature B cell located in the marginal zone of the lymph node.",
                meaning=CL["0009060"]))
        setattr(cls, "CL:0002254",
            PermissibleValue(
                text="CL:0002254",
                description="An epithelial cell of the lining of the small intestine.",
                meaning=CL["0002254"]))
        setattr(cls, "CL:0009055",
            PermissibleValue(
                text="CL:0009055",
                description="A paneth cell that is located in the anorectum.",
                meaning=CL["0009055"]))
        setattr(cls, "CL:0000818",
            PermissibleValue(
                text="CL:0000818",
                description="""An immature B cell of an intermediate stage between the pre-B cell stage and the mature naive stage with the phenotype surface IgM-positive and CD19-positive, and are subject to the process of B cell selection. A transitional B cell migrates from the bone marrow into the peripheral circulation, and then to the spleen.""",
                meaning=CL["0000818"]))
        setattr(cls, "CL:0000998",
            PermissibleValue(
                text="CL:0000998",
                description="""CD8-alpha-negative CD11b-negative dendritic cell is a conventional dendritic cell that is CD11b-negative, CD4-negative CD8-alpha-negative and is CD205-positive. This cell is able to cross- present antigen to CD8-alpha-positive T cells.""",
                meaning=CL["0000998"]))
        setattr(cls, "CL:0001043",
            PermissibleValue(
                text="CL:0001043",
                description="""A recently activated CD4-positive, alpha-beta T cell with the phenotype HLA-DRA-positive, CD38-positive, CD69-positive, CD62L-negative, CD127-negative, and CD25-positive.""",
                meaning=CL["0001043"]))
        setattr(cls, "CL:0009078",
            PermissibleValue(
                text="CL:0009078",
                description="A fibroblast located in the thymic capsule.",
                meaning=CL["0009078"]))
        setattr(cls, "CL:0000314",
            PermissibleValue(
                text="CL:0000314",
                meaning=CL["0000314"]))
        setattr(cls, "CL:0000608",
            PermissibleValue(
                text="CL:0000608",
                description="""A thick walled, sexual, resting spore formed by Zygomycetes; sometimes refers to the spore and the multi-layered cell wall that encloses the spore, the zygosporangium.""",
                meaning=CL["0000608"]))
        setattr(cls, "CL:0000744",
            PermissibleValue(
                text="CL:0000744",
                description="""A columnar chondrocyte that differentiates in the late embryonic growth plate of bone. Columnar chondrocytes vigorously proliferate and form columns in the growth plate.""",
                meaning=CL["0000744"]))
        setattr(cls, "CL:0002259",
            PermissibleValue(
                text="CL:0002259",
                description="The stem cell from which glial precursor cell arises from.",
                meaning=CL["0002259"]))
        setattr(cls, "CL:0002004",
            PermissibleValue(
                text="CL:0002004",
                description="A proerythoblast that is CD34-negative and GlyA-negative.",
                meaning=CL["0002004"]))
        setattr(cls, "CL:1000433",
            PermissibleValue(
                text="CL:1000433",
                description="An epithelial cell that is part of the lacrimal canaliculus.",
                meaning=CL["1000433"]))
        setattr(cls, "CL:0004227",
            PermissibleValue(
                text="CL:0004227",
                description="""A bistratified amacrine cell with a small dendritic field. Flat bistratified amacrine cells have post-synaptic terminals both on the border of S1 and S2, and on the border of S3 and S4. This cell type releases the neurotransmitter glycine.""",
                meaning=CL["0004227"]))
        setattr(cls, "CL:4033022",
            PermissibleValue(
                text="CL:4033022",
                description="A mucus secreting cell of a submucosal gland of the bronchus.",
                meaning=CL["4033022"]))
        setattr(cls, "CL:0003048",
            PermissibleValue(
                text="CL:0003048",
                description="""A cone cell that detects long wavelength light. Exact peak of spectra detected differs between species. In humans, spectra peaks at 564-580 nm.""",
                meaning=CL["0003048"]))
        setattr(cls, "CL:0009080",
            PermissibleValue(
                text="CL:0009080",
                description="A tuft cell located in the small intestine.",
                meaning=CL["0009080"]))
        setattr(cls, "CL:0002569",
            PermissibleValue(
                text="CL:0002569",
                description="A mesenchymal stem cell of the umbilical cord.",
                meaning=CL["0002569"]))
        setattr(cls, "CL:0000235",
            PermissibleValue(
                text="CL:0000235",
                description="""A mononuclear phagocyte present in variety of tissues, typically differentiated from monocytes, capable of phagocytosing a variety of extracellular particulate material, including immune complexes, microorganisms, and dead cells.""",
                meaning=CL["0000235"]))
        setattr(cls, "CL:0002176",
            PermissibleValue(
                text="CL:0002176",
                description="A cell of a secondary follicile within the ovary.",
                meaning=CL["0002176"]))
        setattr(cls, "CL:4030005",
            PermissibleValue(
                text="CL:4030005",
                description="""A renal beta-intercalated cell that is part of the cortical collecting duct. The medullary collecting duct does not contain the renal beta-intercalated cell type.""",
                meaning=CL["4030005"]))
        setattr(cls, "CL:0000999",
            PermissibleValue(
                text="CL:0000999",
                description="""CD8-alpha-negative CD11b-positive dendritic cell is a conventional dendritic cell that is CD11b-positive, CD4-positive and is CD205-negative and CD8-alpha-negative.""",
                meaning=CL["0000999"]))
        setattr(cls, "CL:0002472",
            PermissibleValue(
                text="CL:0002472",
                description="""Gr1-low non-classical monocyte that has low to intermediate expression of the MHC-II complex.""",
                meaning=CL["0002472"]))
        setattr(cls, "CL:0003021",
            PermissibleValue(
                text="CL:0003021",
                description="""A retinal ganglion cell C outer that has a medium dendritic field and a dense dendritic arbor.""",
                meaning=CL["0003021"]))
        setattr(cls, "CL:4023000",
            PermissibleValue(
                text="CL:4023000",
                description="""A motor neuron that innervates both intrafusal and extrafusal muscle fibers. Low abundancy. They control both muscle contraction and responsiveness of the sensory feedback from muscle spindles.""",
                meaning=CL["4023000"]))
        setattr(cls, "CL:0002657",
            PermissibleValue(
                text="CL:0002657",
                description="A glandular epithelial cell of the esophagus.",
                meaning=CL["0002657"]))
        setattr(cls, "CL:0000514",
            PermissibleValue(
                text="CL:0000514",
                description="A precursor cell destined to differentiate into smooth muscle myocytes.",
                meaning=CL["0000514"]))
        setattr(cls, "CL:0000349",
            PermissibleValue(
                text="CL:0000349",
                description="Any cell that is part of some extraembryonic structure.",
                meaning=CL["0000349"]))
        setattr(cls, "CL:0002190",
            PermissibleValue(
                text="CL:0002190",
                description="A flat keratinocyte immediately below the cornified layer.",
                meaning=CL["0002190"]))
        setattr(cls, "CL:4030035",
            PermissibleValue(
                text="CL:4030035",
                description="""A dental pulp cell that possesses stem-cell-like qualities, including self-renewal capability and multi-lineage differentiation.""",
                meaning=CL["4030035"]))
        setattr(cls, "CL:0002067",
            PermissibleValue(
                text="CL:0002067",
                description="An enteroendocrine cell that produces glucagon.",
                meaning=CL["0002067"]))
        setattr(cls, "CL:0009114",
            PermissibleValue(
                text="CL:0009114",
                description="""A B cell found in the perisinusoidal area of a lymph node. In humans, monocytoid B cells are a morphologically distinct B cell population (oval nuclei, abundant cytoplasm, monocyte-like appearance), share many similarities with marginal zone B cells including marker expression, and are increased in disease settings.""",
                meaning=CL["0009114"]))
        setattr(cls, "CL:1001517",
            PermissibleValue(
                text="CL:1001517",
                description="""The various hormone- or neurotransmitter-secreting cells present throughout the mucosa of the stomach.""",
                meaning=CL["1001517"]))
        setattr(cls, "CL:0000137",
            PermissibleValue(
                text="CL:0000137",
                description="""A mature osteoblast that has become embedded in the bone matrix. They occupy a small cavity, called lacuna, in the matrix and are connected to adjacent osteocytes via protoplasmic projections called canaliculi.""",
                meaning=CL["0000137"]))
        setattr(cls, "CL:0009024",
            PermissibleValue(
                text="CL:0009024",
                description="A mesothelial cell that is part of the small intestine.",
                meaning=CL["0009024"]))
        setattr(cls, "CL:4040004",
            PermissibleValue(
                text="CL:4040004",
                description="Any mesenchymal stem cell of adipose tissue that is part of an orbital region.",
                meaning=CL["4040004"]))
        setattr(cls, "CL:0002367",
            PermissibleValue(
                text="CL:0002367",
                description="""A cell that lines the trabecular meshwork, which is an area of tissue in the eye located around the base of the cornea, near the ciliary body, and is responsible for draining the aqueous humor from the eye via the anterior chamber (the chamber on the front of the eye covered by the cornea). This cell may play a role in regulating intraocular pressure.""",
                meaning=CL["0002367"]))
        setattr(cls, "CL:0002062",
            PermissibleValue(
                text="CL:0002062",
                description="""A squamous pulmonary alveolar epithelial cell that is flattened and branched. A pulmonary alveolar type 1 cell covers more than 98% of the alveolar surface. This large cell has thin (50-100 nm) cytoplasmic extensions to form the air-blood barrier essential for normal gas exchange.""",
                meaning=CL["0002062"]))
        setattr(cls, "CL:0000724",
            PermissibleValue(
                text="CL:0000724",
                description="""A differentiated cell that functions as a site of nitrogen fixation under aerobic conditions.""",
                meaning=CL["0000724"]))
        setattr(cls, "CL:1001598",
            PermissibleValue(
                text="CL:1001598",
                description="""A glandular cell found in the epithelium of the small intestine. Example: Enterocytes, Goblet cells, enteroendocrine cells; Paneth cells; M cells; Somatostatin-secreting Cells (D-cells) .""",
                meaning=CL["1001598"]))
        setattr(cls, "CL:1001589",
            PermissibleValue(
                text="CL:1001589",
                description="""Glandular cell of duodenal epithelium. Example: Enterocytes, Goblet cells, enteroendocrine cells; Paneth cells; M cells; Brunner's gland cell.""",
                meaning=CL["1001589"]))
        setattr(cls, "CL:1000147",
            PermissibleValue(
                text="CL:1000147",
                description="A cell that is part of a cardiac valve.",
                meaning=CL["1000147"]))
        setattr(cls, "CL:0002402",
            PermissibleValue(
                text="CL:0002402",
                description="""A resting mature B cell within the Peyer's patch that is CD19-positive, B220-positive, IgM-positive, AA4-negative, CD23-positive, CD43-negative, and CD5-negative.""",
                meaning=CL["0002402"]))
        setattr(cls, "CL:1001126",
            PermissibleValue(
                text="CL:1001126",
                description="Any vasa recta cell that is part of some inner renal medulla vasa recta.",
                meaning=CL["1001126"]))
        setattr(cls, "CL:0002608",
            PermissibleValue(
                text="CL:0002608",
                description="A neuron with a soma found in the hippocampus.",
                meaning=CL["0002608"]))
        setattr(cls, "CL:0002011",
            PermissibleValue(
                text="CL:0002011",
                description="""A progenitor cell that can give rise to plasmacytoid and myeloid dendritic cells, and to monocytes and macrophages. Marker for this cell is Kit-high, CD115-positive, CD135-positive, Cx3cr1-positive, and is Il7ra-negative.""",
                meaning=CL["0002011"]))
        setattr(cls, "CL:4023012",
            PermissibleValue(
                text="CL:4023012",
                description="""A glutamatergic neuron located in the cerebral cortex that projects axons locally rather than distantly.""",
                meaning=CL["4023012"]))
        setattr(cls, "CL:0005014",
            PermissibleValue(
                text="CL:0005014",
                description="""A non-sensory cell that extends from the basement membrane to the apical surface of the auditory epithelium and provides support for auditory hair cells.""",
                meaning=CL["0005014"]))
        setattr(cls, "CL:0002249",
            PermissibleValue(
                text="CL:0002249",
                description="A stem cell that can differentiate into a cardiac myocyte.",
                meaning=CL["0002249"]))
        setattr(cls, "CL:0002675",
            PermissibleValue(
                text="CL:0002675",
                description="A S. pombe cell type determined by mat1-Pc and mat1-Pi on the mat1 locus.",
                meaning=CL["0002675"]))
        setattr(cls, "CL:0000025",
            PermissibleValue(
                text="CL:0000025",
                description="""A female gamete where meiosis has progressed to metaphase II and is able to participate in fertilization.""",
                meaning=CL["0000025"]))
        setattr(cls, "CL:2000021",
            PermissibleValue(
                text="CL:2000021",
                description="Any native cell that is part of a sebaceous gland.",
                meaning=CL["2000021"]))
        setattr(cls, "CL:0002120",
            PermissibleValue(
                text="CL:0002120",
                description="""An CD24-positive CD38-negative IgG-negative memory B cell is a CD38-negative IgG-negative class switched memory B cell that lacks IgG on the cell surface with the phenotype CD24-positive, CD38-negative, and IgG-negative.""",
                meaning=CL["0002120"]))
        setattr(cls, "CL:0008005",
            PermissibleValue(
                text="CL:0008005",
                description="""A somatic muscle cell that is obliquely striated and mononucleated. Examples include the somatic muscles of nematodes.""",
                meaning=CL["0008005"]))
        setattr(cls, "CL:0002654",
            PermissibleValue(
                text="CL:0002654",
                description="An epithelial cell of stratum corneum of esophageal epithelium.",
                meaning=CL["0002654"]))
        setattr(cls, "CL:0011018",
            PermissibleValue(
                text="CL:0011018",
                description="""A group 3 innate lymphoid cell that express ROR gamma t and IL-7R alpha in the absence of lineage markers (e.g. CD3, CD19, B220, CD11c, Gr-1), with the functional ability to interact with mesenchymal cells through lymphotoxin and tumor necrosis factor. Lymphoid tissue-inducer cells are key to the development of lymph nodes and Peyer’s patches.""",
                meaning=CL["0011018"]))
        setattr(cls, "CL:0000660",
            PermissibleValue(
                text="CL:0000660",
                description="An extracellular matrix secreting cell that secretes glycocalyx.",
                meaning=CL["0000660"]))
        setattr(cls, "CL:0000763",
            PermissibleValue(
                text="CL:0000763",
                description="A cell of the monocyte, granulocyte, mast cell, megakaryocyte, or erythroid lineage.",
                meaning=CL["0000763"]))
        setattr(cls, "CL:0002199",
            PermissibleValue(
                text="CL:0002199",
                description="An oncocyte located in the parathyroid gland.",
                meaning=CL["0002199"]))
        setattr(cls, "CL:0001018",
            PermissibleValue(
                text="CL:0001018",
                description="""Immature CD8-alpha-low Langerhans cell is a CD8-alpha-low Langerhans cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0001018"]))
        setattr(cls, "CL:0003009",
            PermissibleValue(
                text="CL:0003009",
                description="""A mono-stratified retinal ganglion cell that has a medium dendritic field and a sparse dendritic arbor with post sympatic terminals in sublaminar layer S4 and S5.""",
                meaning=CL["0003009"]))
        setattr(cls, "CL:0000180",
            PermissibleValue(
                text="CL:0000180",
                description="A steroid hormone secreting cell that secretes estradiol.",
                meaning=CL["0000180"]))
        setattr(cls, "CL:0002308",
            PermissibleValue(
                text="CL:0002308",
                description="An epithelial cell of a skin gland.",
                meaning=CL["0002308"]))
        setattr(cls, "CL:0002543",
            PermissibleValue(
                text="CL:0002543",
                description="An endothelial cell that is part of the vein.",
                meaning=CL["0002543"]))
        setattr(cls, "CL:0008032",
            PermissibleValue(
                text="CL:0008032",
                description="""A GABAergic interneuron in human cortical layer 1 that has large rosehip-shaped axonal boutons and compact arborization.""",
                meaning=CL["0008032"]))
        setattr(cls, "CL:1000442",
            PermissibleValue(
                text="CL:1000442",
                description="An urothelial cell that is part of the trigone of urinary bladder.",
                meaning=CL["1000442"]))
        setattr(cls, "CL:0002488",
            PermissibleValue(
                text="CL:0002488",
                description="""A trophoblast cell that has a large volume of cytoplasm, is polyploid and is usually mononuclear but is also occasionally multi-nucleate. This cell type is important in establishing maternal physiology and remodeling of the vasculature of the placenta.""",
                meaning=CL["0002488"]))
        setattr(cls, "CL:0000014",
            PermissibleValue(
                text="CL:0000014",
                description="A stem cell that is the precursor of gametes.",
                meaning=CL["0000014"]))
        setattr(cls, "CL:0004242",
            PermissibleValue(
                text="CL:0004242",
                description="""An amacrine cell with a wide dendritic field, dendrites in S3, and post-synaptic terminals in S3. Dendrites of this cell type are straight and minimally branched.""",
                meaning=CL["0004242"]))
        setattr(cls, "CL:1000050",
            PermissibleValue(
                text="CL:1000050",
                description="Any glial cell that is part of some lateral line nerve.",
                meaning=CL["1000050"]))
        setattr(cls, "CL:1001572",
            PermissibleValue(
                text="CL:1001572",
                description="A vascular endothelial cell found in colon blood vessels.",
                meaning=CL["1001572"]))
        setattr(cls, "CL:0000984",
            PermissibleValue(
                text="CL:0000984",
                description="A plasmablast that secretes IgA.",
                meaning=CL["0000984"]))
        setattr(cls, "CL:0000104",
            PermissibleValue(
                text="CL:0000104",
                description="A neuron with three or more neurites, usually an axon and multiple dendrites.",
                meaning=CL["0000104"]))
        setattr(cls, "CL:1001285",
            PermissibleValue(
                text="CL:1001285",
                description="A cell that is part of some vasa recta descending limb.",
                meaning=CL["1001285"]))
        setattr(cls, "CL:1000419",
            PermissibleValue(
                text="CL:1000419",
                description="A myoepithelial cell that is part of the lactiferous duct.",
                meaning=CL["1000419"]))
        setattr(cls, "CL:0000417",
            PermissibleValue(
                text="CL:0000417",
                meaning=CL["0000417"]))
        setattr(cls, "CL:0002146",
            PermissibleValue(
                text="CL:0002146",
                description="""A sweat producing cell of eccrine sweat glands. Pyramidal in shape, with its base resting on the basal lamina or myoepitheliocytes, and its microvillus-covered apical plasma membrane line up the intercellular canaliculi. Cell is not stained by hematoxylin or eosin.""",
                meaning=CL["0002146"]))
        setattr(cls, "CL:0002122",
            PermissibleValue(
                text="CL:0002122",
                description="""A B220-positive CD38-positive IgG-negative memory B cell is a CD38-positive IgG-negative class switched memory B cell that lacks IgG on the cell surface with the phenotype B220-positive, CD38-positive, and IgG-negative.""",
                meaning=CL["0002122"]))
        setattr(cls, "CL:0000695",
            PermissibleValue(
                text="CL:0000695",
                description="""A neuron of the human embryonic marginal zone which display, as a salient feature, radial ascending processes that contact the pial surface, and a horizontal axon plexus located in the deep marginal zone. One feature of these cells in mammals is that they express the Reelin gene.""",
                meaning=CL["0000695"]))
        setattr(cls, "CL:0002070",
            PermissibleValue(
                text="CL:0002070",
                description="""Bottle-shaped with narrow neck; broad, rounded basal portion where nucleus is located; stereocilia and a single kinocilium is present apically; receive nerve bouton at their base from an afferent cup-shaped (chalice or calyx) nerve ending.""",
                meaning=CL["0002070"]))
        setattr(cls, "CL:4023083",
            PermissibleValue(
                text="CL:4023083",
                description="""A GABAergic interneuron that selectively innervates the axon initial segment of pyramidal cells. Their local axonal clusters are formed by high-frequency branching at shallow angles, often ramifying around, above or below their somata with a high bouton density. The characteristic terminal portions of the axon form short vertical rows of boutons, resembling the candlesticks and candles of a chandelier. Chandelier cells can be multipolar or bitufted.""",
                meaning=CL["4023083"]))
        setattr(cls, "CL:1000366",
            PermissibleValue(
                text="CL:1000366",
                description="A transitional myocyte that is part of the middle internodal tract.",
                meaning=CL["1000366"]))
        setattr(cls, "CL:0003014",
            PermissibleValue(
                text="CL:0003014",
                description="""A mono-stratified retinal ganglion cell that has a large dendritic field, a medium dendritic arbor, and a medium length secondary dendrite shaft.""",
                meaning=CL["0003014"]))
        setattr(cls, "CL:0002512",
            PermissibleValue(
                text="CL:0002512",
                description="A langerin-negative lymph node dendritic cell that is CD103-negative and CD11b-high.",
                meaning=CL["0002512"]))
        setattr(cls, "CL:0002595",
            PermissibleValue(
                text="CL:0002595",
                description="A smooth muscle cell of the subclavian artery.",
                meaning=CL["0002595"]))
        setattr(cls, "CL:0002078",
            PermissibleValue(
                text="CL:0002078",
                description="Epithelial cell derived from mesoderm or mesenchyme.",
                meaning=CL["0002078"]))
        setattr(cls, "CL:0002420",
            PermissibleValue(
                text="CL:0002420",
                description="A T cell that has not completed T cell selection.",
                meaning=CL["0002420"]))
        setattr(cls, "CL:0000503",
            PermissibleValue(
                text="CL:0000503",
                description="""A specialized stromal cell that forms the theca layer outside the basal lamina lining the ovarian follicle, appearing during the secondary follicle stage.""",
                meaning=CL["0000503"]))
        setattr(cls, "CL:0000908",
            PermissibleValue(
                text="CL:0000908",
                description="""A CD8-positive, alpha-beta T cell with the phenotype CD69-positive, CD62L-negative, CD127-negative, and CD25-positive, that secretes cytokines.""",
                meaning=CL["0000908"]))
        setattr(cls, "CL:0002664",
            PermissibleValue(
                text="CL:0002664",
                description="""A stem cell that can give rise to multiple cell types (i.e. smooth muscle, endothelial) in the developing heart.""",
                meaning=CL["0002664"]))
        setattr(cls, "CL:4023057",
            PermissibleValue(
                text="CL:4023057",
                description="Any GABAergic interneuron that has its soma located in some cerebellar cortex.",
                meaning=CL["4023057"]))
        setattr(cls, "CL:0002532",
            PermissibleValue(
                text="CL:0002532",
                description="A myeloid dendritic cell found in the blood that is CD16-positive.",
                meaning=CL["0002532"]))
        setattr(cls, "CL:0008001",
            PermissibleValue(
                text="CL:0008001",
                description="Any hematopoietic cell that is a precursor of some other hematopoietic cell type.",
                meaning=CL["0008001"]))
        setattr(cls, "CL:0000206",
            PermissibleValue(
                text="CL:0000206",
                description="""A cell specialized to detect chemical substances and relay that information centrally in the nervous system. Chemoreceptors may monitor external stimuli, as in taste and olfaction, or internal stimuli, such as the concentrations of oxygen and carbon dioxide in the blood.""",
                meaning=CL["0000206"]))
        setattr(cls, "CL:2000065",
            PermissibleValue(
                text="CL:2000065",
                description="Any microvascular endothelial cell that is part of a female urethra.",
                meaning=CL["2000065"]))
        setattr(cls, "CL:0000957",
            PermissibleValue(
                text="CL:0000957",
                description="""A large pre-B-II cell is a pre-B-II cell that is proliferating and is Rag1-negative and Rag2-negative.""",
                meaning=CL["0000957"]))
        setattr(cls, "CL:0000986",
            PermissibleValue(
                text="CL:0000986",
                description="A fully differentiated plasma cell that secretes IgM.",
                meaning=CL["0000986"]))
        setattr(cls, "CL:0000792",
            PermissibleValue(
                text="CL:0000792",
                description="""A CD4-positive, CD25-positive, alpha-beta T cell that regulates overall immune responses as well as the responses of other T cell subsets through direct cell-cell contact and cytokine release.""",
                meaning=CL["0000792"]))
        setattr(cls, "CL:0002194",
            PermissibleValue(
                text="CL:0002194",
                description="A cell involved in the formation of a monocyte (monopoiesis).",
                meaning=CL["0002194"]))
        setattr(cls, "CL:0002496",
            PermissibleValue(
                text="CL:0002496",
                description="""A T cell that is located in the intestinal epithelium and is capable of a mucosal immune response.""",
                meaning=CL["0002496"]))
        setattr(cls, "CL:0000600",
            PermissibleValue(
                text="CL:0000600",
                description="A fungal cell with two or more genetically distinct nuclei.",
                meaning=CL["0000600"]))
        setattr(cls, "CL:0000355",
            PermissibleValue(
                text="CL:0000355",
                description="""A multifate stem cell found in skeletal muscle than can differentiate into many different cell types, including muscle. Distinct cell type from satellite cell.""",
                meaning=CL["0000355"]))
        setattr(cls, "CL:1000893",
            PermissibleValue(
                text="CL:1000893",
                description="Any kidney blood vessel cell that is part of some renal vein.",
                meaning=CL["1000893"]))
        setattr(cls, "CL:0002044",
            PermissibleValue(
                text="CL:0002044",
                description="""A basophil mast progenitor cell that is Beta-7 integrin-high, Kit-positive FcRgammaII/III-positive and Sca1-negative.""",
                meaning=CL["0002044"]))
        setattr(cls, "CL:0002246",
            PermissibleValue(
                text="CL:0002246",
                description="""A hematopoeitic stem cell found in the blood. Normally found in very limited numbers in the peripheral circulation (less than 0.1% of all nucleated cells).""",
                meaning=CL["0002246"]))
        setattr(cls, "CL:0009098",
            PermissibleValue(
                text="CL:0009098",
                description="""A skeletal muscle fiber found at the fetal and neonatal stages. In mammalian fetuses and neonates, skeletal muscle expresses myosin heavy chain-neonatal (MyHC-neo, encoded by the MYH8 gene). This expression disappears shortly after birth and is replaced by expression of adult heavy chain myosins.""",
                meaning=CL["0009098"]))
        setattr(cls, "CL:1000720",
            PermissibleValue(
                text="CL:1000720",
                description="Any renal intercalated cell that is part of some papillary duct.",
                meaning=CL["1000720"]))
        setattr(cls, "CL:0000975",
            PermissibleValue(
                text="CL:0000975",
                description="A fully differentiated plasma cell that lives for months.",
                meaning=CL["0000975"]))
        setattr(cls, "CL:0000367",
            PermissibleValue(
                text="CL:0000367",
                meaning=CL["0000367"]))
        setattr(cls, "CL:0009045",
            PermissibleValue(
                text="CL:0009045",
                description="A B cell found in the lymph node medullary sinus.",
                meaning=CL["0009045"]))
        setattr(cls, "CL:0002443",
            PermissibleValue(
                text="CL:0002443",
                description="A NK1.1-positive T cell that is Ly49Cl-positive.",
                meaning=CL["0002443"]))
        setattr(cls, "CL:0000446",
            PermissibleValue(
                text="CL:0000446",
                description="""An epithelial cell of the parathyroid gland that is arranged in wide, irregular interconnecting columns; responsible for the synthesis and secretion of parathyroid hormone.""",
                meaning=CL["0000446"]))
        setattr(cls, "CL:0000916",
            PermissibleValue(
                text="CL:0000916",
                description="A mature gamma-delta T cell located in the epidermis that regulates wound healing.",
                meaning=CL["0000916"]))
        setattr(cls, "CL:0000561",
            PermissibleValue(
                text="CL:0000561",
                description="""Interneuron of the vertebrate retina. They integrate, modulate, and interpose a temporal domain in the visual message presented to the retinal ganglion cells, with which they synapse in the inner plexiform layer. They lack large axons.""",
                meaning=CL["0000561"]))
        setattr(cls, "CL:0002143",
            PermissibleValue(
                text="CL:0002143",
                description="""A chief cell that is smaller than light chief cells and has a smaller and darker nucleus and a finely granular cytoplasm with many granules.""",
                meaning=CL["0002143"]))
        setattr(cls, "CL:0000566",
            PermissibleValue(
                text="CL:0000566",
                description="A mesenchymal stem cell capable of developing into blood vessel endothelium.",
                meaning=CL["0000566"]))
        setattr(cls, "CL:0019021",
            PermissibleValue(
                text="CL:0019021",
                description="""An endothelial cell found in the periportal region hepatic sinusoid, near the portal triad. The fenestrae of these cells are larger but fewer in number compared with those of endothelial cells near the centrilobular region of the hepatic sinusoid.""",
                meaning=CL["0019021"]))
        setattr(cls, "CL:1001145",
            PermissibleValue(
                text="CL:1001145",
                description="Any kidney cortex vein cell that is part of some renal interlobular vein.",
                meaning=CL["1001145"]))
        setattr(cls, "CL:0008012",
            PermissibleValue(
                text="CL:0008012",
                description="""A skeletal muscle satellite cell that is mitotically quiescent.  These cells are wedge shaped and have a large nuclear to cytoplasmic ratio with few organelles, a small nucleus and condensed interphase chromatin. Satellite cells typically remain in this state until activated following muscle damage.""",
                meaning=CL["0008012"]))
        setattr(cls, "CL:0000142",
            PermissibleValue(
                text="CL:0000142",
                description="""A cell occurring in the peripheral part of the vitreous body of the eye that may be responsible for production of hyaluronic acid and collagen.""",
                meaning=CL["0000142"]))
        setattr(cls, "CL:2000017",
            PermissibleValue(
                text="CL:2000017",
                description="Any fibroblast that is part of a periodontal ligament.",
                meaning=CL["2000017"]))
        setattr(cls, "CL:0004115",
            PermissibleValue(
                text="CL:0004115",
                description="""A monostratified retinal ganglion cell with small to medium soma and small to medium dendritic field.""",
                meaning=CL["0004115"]))
        setattr(cls, "CL:0000424",
            PermissibleValue(
                text="CL:0000424",
                description="""A cell involved in the elimination of metabolic and foreign toxins, and in maintaining the ionic, acid-base and water balance of biological fluids.""",
                meaning=CL["0000424"]))
        setattr(cls, "CL:0000568",
            PermissibleValue(
                text="CL:0000568",
                description="""A cell that originates in the neural crest, that has certain cytochemical and ultrastructural characteristics and is found scattered throughout the body; types include melanocytes, the cells of the chromaffin system, and cells in the hypothalamus, hypophysis, thyroid, parathyroids, lungs, gastrointestinal tract, and pancreas. This cell type concentrates the amino acid precursors of certain amines and decarboxylate them, forming amines that function as regulators and neurotransmitters. This cell type produces substances such as epinephrine, norepinephrine, dopamine, serotonin, enkephalin, somatostatin, neurotensin, and substance P, the actions of which may affect contiguous cells, nearby groups of cells, or distant cells, thus functioning as local or systemic hormones. The name is an acronym for amine precursor uptake and decarboxylation cell.""",
                meaning=CL["0000568"]))
        setattr(cls, "CL:0002642",
            PermissibleValue(
                text="CL:0002642",
                description="""An epithelial cell of the esophageal cardiac gland that occurs both in the proximal and distal esophagus, within the lamina propia.""",
                meaning=CL["0002642"]))
        setattr(cls, "CL:0002349",
            PermissibleValue(
                text="CL:0002349",
                description="A natural killer cell that is CD27-high and CD11b-low.",
                meaning=CL["0002349"]))
        setattr(cls, "CL:0002522",
            PermissibleValue(
                text="CL:0002522",
                description="""A renal filtration cell is a specialized cell of the renal system that filter fluids by charge, size or both.""",
                meaning=CL["0002522"]))
        setattr(cls, "CL:0002501",
            PermissibleValue(
                text="CL:0002501",
                description="""A P/D1 enteroendocrine cell that is argyrophilic and stores vasoactive intestinal polypeptide.""",
                meaning=CL["0002501"]))
        setattr(cls, "CL:0000817",
            PermissibleValue(
                text="CL:0000817",
                description="A precursor B cell is a B cell with the phenotype CD10-positive.",
                meaning=CL["0000817"]))
        setattr(cls, "CL:0000429",
            PermissibleValue(
                text="CL:0000429",
                description="A columnar epithelial cell that is part of an insect imaginal disc.",
                meaning=CL["0000429"]))
        setattr(cls, "CL:1001431",
            PermissibleValue(
                text="CL:1001431",
                description="Any renal principal cell that is part of some collecting duct of renal tubule.",
                meaning=CL["1001431"]))
        setattr(cls, "CL:0002567",
            PermissibleValue(
                text="CL:0002567",
                description="A melanocyte that appears lighter in color.",
                meaning=CL["0002567"]))
        setattr(cls, "CL:0000853",
            PermissibleValue(
                text="CL:0000853",
                description="""Olfactory epithelial support cell is a columnar cell that extends from the epithelial free margin to the basement membrane of the olfactory epithelium. This cell type has a large, vertically, elongate, euchromatic nucleus, along with other nuclei, forms a layer superficial to the cell body of the receptor cell; sends long somewhat irregular microvilli into the mucus layer; at the base, with expanded end-feet containing numerous lamellated dense bodies resembling lipofuscin of neurons.""",
                meaning=CL["0000853"]))
        setattr(cls, "CL:0002217",
            PermissibleValue(
                text="CL:0002217",
                description="""A trophoblast that leaves the placenta and invades the endometrium and myometrium. This cell type is crucial in increasing blood flow to the fetus.""",
                meaning=CL["0002217"]))
        setattr(cls, "CL:4023062",
            PermissibleValue(
                text="CL:4023062",
                description="A neuron with its soma located in the dentate gyrus of the hippocampus.",
                meaning=CL["4023062"]))
        setattr(cls, "CL:1000281",
            PermissibleValue(
                text="CL:1000281",
                description="A smooth muscle cell that is part of the cecum.",
                meaning=CL["1000281"]))
        setattr(cls, "CL:4052039",
            PermissibleValue(
                text="CL:4052039",
                description="""A tuft cell that is part of the epithelium of the submandibular gland, localized to the striated ducts in mice, pigs, and humans, and to the main excretory ducts in rats. This cell is characterized by chemosensory functions, potential roles in immune regulation, and possible involvement in salivary secretion via acetylcholine release.""",
                meaning=CL["4052039"]))
        setattr(cls, "CL:0002368",
            PermissibleValue(
                text="CL:0002368",
                description="""An epithelial cell of the respiratory tract epithelium.  These cells have an endodermal origin.""",
                meaning=CL["0002368"]))
        setattr(cls, "CL:0000749",
            PermissibleValue(
                text="CL:0000749",
                description="""A bipolar neuron found in the retina and having connections with photoreceptors cells and neurons in the inner half of the inner plexiform layer. These cells depolarize in response to light stimulation of their corresponding photoreceptors.""",
                meaning=CL["0000749"]))
        setattr(cls, "CL:0002225",
            PermissibleValue(
                text="CL:0002225",
                description="""A lens fiber cell that develops from primary lens fiber; located towards the center of lens; cell organelles are normally degraded or in the process of being degraded.""",
                meaning=CL["0002225"]))
        setattr(cls, "CL:4030062",
            PermissibleValue(
                text="CL:4030062",
                description="""An intratelencephalic-projecting glutamatergic with a soma located in cortical layer 4/5.""",
                meaning=CL["4030062"]))
        setattr(cls, "CL:2000006",
            PermissibleValue(
                text="CL:2000006",
                description="Any germinal center B cell that is part of a tonsil.",
                meaning=CL["2000006"]))
        setattr(cls, "CL:0000334",
            PermissibleValue(
                text="CL:0000334",
                meaning=CL["0000334"]))
        setattr(cls, "CL:4052055",
            PermissibleValue(
                text="CL:4052055",
                description="A mature NK T cell that can be identified by the expression of CD56 in humans.",
                meaning=CL["4052055"]))
        setattr(cls, "CL:1000335",
            PermissibleValue(
                text="CL:1000335",
                description="An enterocyte that is part of the epithelium of intestinal villus.",
                meaning=CL["1000335"]))
        setattr(cls, "CL:1000285",
            PermissibleValue(
                text="CL:1000285",
                description="A smooth muscle cell that is part of the sigmoid colon.",
                meaning=CL["1000285"]))
        setattr(cls, "CL:0000043",
            PermissibleValue(
                text="CL:0000043",
                description="""A fully differentiated basophil, a granular leukocyte with an irregularly shaped, pale-staining nucleus that is partially constricted into two lobes, and with cytoplasm that contains coarse granules of variable size. Basophils contain vasoactive amines such as histamine and serotonin, which are released on appropriate stimulation.""",
                meaning=CL["0000043"]))
        setattr(cls, "CL:4042005",
            PermissibleValue(
                text="CL:4042005",
                description="A choroid plexus macrophage that is part of a choroid plexus stroma.",
                meaning=CL["4042005"]))
        setattr(cls, "CL:0003034",
            PermissibleValue(
                text="CL:0003034",
                description="""A monostratified retinal ganglion cell that has a small soma, an assymetric dendritic field with post synaptic terminals in sublaminar layer S3.""",
                meaning=CL["0003034"]))
        setattr(cls, "CL:1000849",
            PermissibleValue(
                text="CL:1000849",
                description="Any epithelial cell of distal tubule that is part of some distal convoluted tubule.",
                meaning=CL["1000849"]))
        setattr(cls, "CL:0007008",
            PermissibleValue(
                text="CL:0007008",
                description="""Notochordal cell that is inner portion of the notochord and becomes vacuolated as development proceeds.""",
                meaning=CL["0007008"]))
        setattr(cls, "CL:0000457",
            PermissibleValue(
                text="CL:0000457",
                meaning=CL["0000457"]))
        setattr(cls, "CL:1000317",
            PermissibleValue(
                text="CL:1000317",
                description="A goblet cell that is part of the epithelium of intestinal villus.",
                meaning=CL["1000317"]))
        setattr(cls, "CL:0000325",
            PermissibleValue(
                text="CL:0000325",
                description="A cell that is specialised to accumulate a particular substance(s).",
                meaning=CL["0000325"]))
        setattr(cls, "CL:0011031",
            PermissibleValue(
                text="CL:0011031",
                description="A dendritic cell that develops from a monocyte.",
                meaning=CL["0011031"]))
        setattr(cls, "CL:0002417",
            PermissibleValue(
                text="CL:0002417",
                description="""An immature or mature cell of the first erythroid lineage to arise during embryonic development.""",
                meaning=CL["0002417"]))
        setattr(cls, "CL:0002584",
            PermissibleValue(
                text="CL:0002584",
                description="An epithelial cell of the kidney cortex.",
                meaning=CL["0002584"]))
        setattr(cls, "CL:1000487",
            PermissibleValue(
                text="CL:1000487",
                description="A smooth muscle cell that is part of the prostate gland.",
                meaning=CL["1000487"]))
        setattr(cls, "CL:0000338",
            PermissibleValue(
                text="CL:0000338",
                description="A neural precursor of the central nervous system.",
                meaning=CL["0000338"]))
        setattr(cls, "CL:0002183",
            PermissibleValue(
                text="CL:0002183",
                description="""A stomach epithelial cell that is olumnar in form with a few short apical microvilli; relatively undifferentiated mitotic cell from which other types of gland are derived; few in number, situated in the isthmus region of the gland and base of the gastric pit.""",
                meaning=CL["0002183"]))
        setattr(cls, "CL:0000637",
            PermissibleValue(
                text="CL:0000637",
                description="A cell that stains readily in the anterior pituitary gland.",
                meaning=CL["0000637"]))
        setattr(cls, "CL:4052002",
            PermissibleValue(
                text="CL:4052002",
                description="""A multinucleate cell formed by the fusion of multiple uninuclear cells through plasma membrane fusion. This process leads to a single large cell containing multiple nuclei within a shared cytoplasm.""",
                meaning=CL["4052002"]))
        setattr(cls, "CL:0002549",
            PermissibleValue(
                text="CL:0002549",
                description="A fibroblast that is part of the choroid plexus.",
                meaning=CL["0002549"]))
        setattr(cls, "CL:0002257",
            PermissibleValue(
                text="CL:0002257",
                description="An epithelial cell of thyroid gland.",
                meaning=CL["0002257"]))
        setattr(cls, "CL:4047042",
            PermissibleValue(
                text="CL:4047042",
                description="""An enteric glial cell located within the myenteric ganglia of the gastrointestinal tract. This cell has a small somata and has very short, irregularly branched processes that surround neuron cell bodies, giving it a protoplasmic-like appearance. It plays crucial roles in modulating myenteric neuron activity, regulating oxidative stress, and influencing neuroinflammation and neurogenesis.""",
                meaning=CL["4047042"]))
        setattr(cls, "CL:1000296",
            PermissibleValue(
                text="CL:1000296",
                description="An epithelial cell that is part of the urethra.",
                meaning=CL["1000296"]))
        setattr(cls, "CL:4030058",
            PermissibleValue(
                text="CL:4030058",
                description="A macrophage that expresses the T cell receptor complex at the cell surface.",
                meaning=CL["4030058"]))
        setattr(cls, "CL:1000979",
            PermissibleValue(
                text="CL:1000979",
                description="Any smooth muscle cell that is part of some muscular coat of ureter.",
                meaning=CL["1000979"]))
        setattr(cls, "CL:0000939",
            PermissibleValue(
                text="CL:0000939",
                description="""A mature natural killer cell that has the phenotype CD56-low, CD16-positive and which is capable of cytotoxicity and cytokine production.""",
                meaning=CL["0000939"]))
        setattr(cls, "CL:0000032",
            PermissibleValue(
                text="CL:0000032",
                description="""A cell of a platelike structure, especially a thickened plate of ectoderm in the early embryo, from which a sense organ develops.""",
                meaning=CL["0000032"]))
        setattr(cls, "CL:0002150",
            PermissibleValue(
                text="CL:0002150",
                description="""Epithelioid macrophage is an activated macrophage that resembles an epithelial cell with finely granular, pale eosinophilic cytoplasm and central, ovoid nucleus (oval or elongate). This cell type is able to merge into one another to form aggregates. The presence of such aggregates may characterize some pathologic conditions, mainly granulomatous inflammation.""",
                meaning=CL["0002150"]))
        setattr(cls, "CL:0009006",
            PermissibleValue(
                text="CL:0009006",
                description="An enteroendocrine cell that is located in the small intestine.",
                meaning=CL["0009006"]))
        setattr(cls, "CL:0000579",
            PermissibleValue(
                text="CL:0000579",
                description="""A follicle cell that migrates from the anterior pole of the insect egg chamber to the anterior of the oocyte where they participate in the formation of the micropyle.""",
                meaning=CL["0000579"]))
        setattr(cls, "CL:0000406",
            PermissibleValue(
                text="CL:0000406",
                meaning=CL["0000406"]))
        setattr(cls, "CL:1000405",
            PermissibleValue(
                text="CL:1000405",
                description="An epithelial cell that is part of the appendix.",
                meaning=CL["1000405"]))
        setattr(cls, "CL:1000355",
            PermissibleValue(
                text="CL:1000355",
                description="A M cell that is part of the epithelium proper of small intestine.",
                meaning=CL["1000355"]))
        setattr(cls, "CL:0000968",
            PermissibleValue(
                text="CL:0000968",
                description="A mature B cell that produces cytokines that can influence CD4 T cell differentiation.",
                meaning=CL["0000968"]))
        setattr(cls, "CL:0002383",
            PermissibleValue(
                text="CL:0002383",
                description="""A uninucleate spore formed on specialized cells or projections, sterigma, of a conidiophore head.""",
                meaning=CL["0002383"]))
        setattr(cls, "CL:4029002",
            PermissibleValue(
                text="CL:4029002",
                description="A gamete-nursing cell that derives from a germline cell (del Pino, 2021).",
                meaning=CL["4029002"]))
        setattr(cls, "CL:4052004",
            PermissibleValue(
                text="CL:4052004",
                description="""A specialized fibroblastic reticular cell that is part of gut-associated lymphoid tissue (GALT), responsible for forming a structural network that facilitates immune cell interactions. This cell is found in Peyer's patches, cryptopatches, and isolated lymphoid follicles. It plays crucial roles in maintaining intestinal immunity by controlling innate lymphoid cell homeostasis and function, organizing lymphoid structures, and contributing to intestinal microbiome balance.""",
                meaning=CL["4052004"]))
        setattr(cls, "CL:4023088",
            PermissibleValue(
                text="CL:4023088",
                description="""A basket cell that is large, and typically ascends to give rise to many long horizontally and vertically projecting axon collaterals that traverse neighboring columns and can extend through all cortical layers.""",
                meaning=CL["4023088"]))
        setattr(cls, "CL:4033053",
            PermissibleValue(
                text="CL:4033053",
                description="""A bistratfied retinal ganglion cell with a small dendritic field that has dendrites in the ON and OFF sublamina of the retinal inner plexiform layer and carries blue-ON/yellow-OFF signals. This cell receives bipolar and amacrine input to both the OFF and ON dendritic tree.""",
                meaning=CL["4033053"]))
        setattr(cls, "CL:2000046",
            PermissibleValue(
                text="CL:2000046",
                description="Any cardiac muscle cell that is part of a cardiac ventricle.",
                meaning=CL["2000046"]))
        setattr(cls, "CL:4023072",
            PermissibleValue(
                text="CL:4023072",
                description="A cell that is part of the brain vasculature.",
                meaning=CL["4023072"]))
        setattr(cls, "CL:0002236",
            PermissibleValue(
                text="CL:0002236",
                description="A cell that constitutes the basal layer of epithelium in the prostatic duct.",
                meaning=CL["0002236"]))
        setattr(cls, "CL:0000519",
            PermissibleValue(
                text="CL:0000519",
                description="A phagocyte from organisms in the Nematoda or Protostomia clades.",
                meaning=CL["0000519"]))
        setattr(cls, "CL:0002670",
            PermissibleValue(
                text="CL:0002670",
                description="""An otic fibrocyte that underlies the stria vascularis and is part of a mesenchymal gap junction network that regulates ionic homeostasis of the endolymph.""",
                meaning=CL["0002670"]))
        setattr(cls, "CL:1000480",
            PermissibleValue(
                text="CL:1000480",
                description="A transitional myocyte that is part of the internodal tract.",
                meaning=CL["1000480"]))
        setattr(cls, "CL:1000308",
            PermissibleValue(
                text="CL:1000308",
                description="A fibrocyte that is part of the adventitia of ureter.",
                meaning=CL["1000308"]))
        setattr(cls, "CL:0000308",
            PermissibleValue(
                text="CL:0000308",
                meaning=CL["0000308"]))
        setattr(cls, "CL:0000422",
            PermissibleValue(
                text="CL:0000422",
                description="""A cell whose primary function is to cause growth by stimulating cell division in its immediate cellular environment.""",
                meaning=CL["0000422"]))
        setattr(cls, "CL:4006000",
            PermissibleValue(
                text="CL:4006000",
                description="A fibroblast that is part of the breast.",
                meaning=CL["4006000"]))
        setattr(cls, "CL:0000182",
            PermissibleValue(
                text="CL:0000182",
                description="""The main structural component of the liver. They are specialized epithelial cells that are organized into interconnected plates called lobules. Majority of cell population of liver, polygonal in shape, arranged in plates or trabeculae between sinusoids; may have single nucleus or binucleated.""",
                meaning=CL["0000182"]))
        setattr(cls, "CL:0002095",
            PermissibleValue(
                text="CL:0002095",
                description="A cell in the hilum of the ovary that produces androgens.",
                meaning=CL["0002095"]))
        setattr(cls, "CL:4052013",
            PermissibleValue(
                text="CL:4052013",
                description="""A specialized theca cell that forms the outer layer of the theca surrounding the ovarian follicle, appearing at the antral follicle. Originating from progenitor theca cells, theca externa cell is characterized by its fibroblast-like appearance and primarily function to provide structural support to the developing follicle. This cell produces collagen fibers and extracellular matrix components such as Col1a1 and Col1a2.""",
                meaning=CL["4052013"]))
        setattr(cls, "CL:0002398",
            PermissibleValue(
                text="CL:0002398",
                description="An intermediate monocyte that is Gr1-positive, CD43-positive.",
                meaning=CL["0002398"]))
        setattr(cls, "CL:0000335",
            PermissibleValue(
                text="CL:0000335",
                description="""A mesenchymal cell in embryonic development found in a contracting mass and that gives rise to osteoprogenitors.""",
                meaning=CL["0000335"]))
        setattr(cls, "CL:1000482",
            PermissibleValue(
                text="CL:1000482",
                description="A myocardial endocrine cell that is part of the interventricular septum.",
                meaning=CL["1000482"]))
        setattr(cls, "CL:0019031",
            PermissibleValue(
                text="CL:0019031",
                description="""Goblet cells reside throughout the length of the small and large intestine and are responsible for the production and maintenance of the protective mucus blanket by synthesizing and secreting high-molecular-weight glycoproteins known as mucins. Human intestinal goblet cells secrete the MUC2 mucin, as well as a number of typical mucus components: CLCA1, FCGBP, AGR2, ZG16, and TFF3.""",
                meaning=CL["0019031"]))
        setattr(cls, "CL:0002030",
            PermissibleValue(
                text="CL:0002030",
                description="""A lineage negative, Sca1-negative basophil progenitor cell that is Fc epsilon RIalpha-high.""",
                meaning=CL["0002030"]))
        setattr(cls, "CL:0002582",
            PermissibleValue(
                text="CL:0002582",
                description="A preadipocyte that is part of visceral tissue.",
                meaning=CL["0002582"]))
        setattr(cls, "CL:0002440",
            PermissibleValue(
                text="CL:0002440",
                description="A NK1.1-positive T cell that is Ly49D-positive.",
                meaning=CL["0002440"]))
        setattr(cls, "CL:1001509",
            PermissibleValue(
                text="CL:1001509",
                description="The neurons that utilize glycine as a neurotransmitter.",
                meaning=CL["1001509"]))
        setattr(cls, "CL:0002453",
            PermissibleValue(
                text="CL:0002453",
                description="""A progenitor cell of the central nervous system that can differentiate into oligodendrocytes or type-2 astrocytes. This cell originates from multiple structures within the developing brain including the medial ganglion eminence and the lateral ganglionic eminence. These cells migrate throughout the central nervous system and persist into adulthood where they play an important role in remyelination of injured neurons.""",
                meaning=CL["0002453"]))
        setattr(cls, "CL:0000488",
            PermissibleValue(
                text="CL:0000488",
                description="A photoreceptor cell that detects visible light.",
                meaning=CL["0000488"]))
        setattr(cls, "CL:1000090",
            PermissibleValue(
                text="CL:1000090",
                description="Any epithelial cell that is part of some pronephric nephron tubule.",
                meaning=CL["1000090"]))
        setattr(cls, "CL:0004126",
            PermissibleValue(
                text="CL:0004126",
                description="""A retinal ganglion cell C outer that has symmetrical and dense dendritic dendritic tree with a large dendritic field.""",
                meaning=CL["0004126"]))
        setattr(cls, "CL:0002159",
            PermissibleValue(
                text="CL:0002159",
                description="Epithelial cells derived from general body ectoderm and ectoderm placodes.",
                meaning=CL["0002159"]))
        setattr(cls, "CL:0000096",
            PermissibleValue(
                text="CL:0000096",
                description="""A fully differentiated neutrophil, a granular leukocyte having a nucleus with three to five lobes connected by slender threads, and cytoplasm containing fine inconspicuous granules and stainable by neutral dyes. They are produced in bone marrow at a rate of 5e10-10e10/day and have a half-life of 6-8 hours. Neutrophils are CD15-positive, CD16-positive, CD32-positive, CD43-positive, CD181-positive, and CD182-positive.""",
                meaning=CL["0000096"]))
        setattr(cls, "CL:0000872",
            PermissibleValue(
                text="CL:0000872",
                description="""A splenic macrophage found in the marginal zone of the spleen, involved in recognition and clearance of particulate material from the splenic circulation. Markers include F4/80-negative, MARCO-positive, SR-A-positive, SIGN-R1-positive, and Dectin2-positive.""",
                meaning=CL["0000872"]))
        setattr(cls, "CL:0002201",
            PermissibleValue(
                text="CL:0002201",
                description="""A renal intercalated cell that secretes base and reabsorbs acid in the distal segments of the kidney tubule to maintain acid/base balance.""",
                meaning=CL["0002201"]))
        setattr(cls, "CL:0000244",
            PermissibleValue(
                text="CL:0000244",
                description="""A cell characteristically found lining hollow organs that are subject to great mechanical change due to contraction and distention; originally thought to represent a transition between stratified squamous and columnar epithelium.""",
                meaning=CL["0000244"]))
        setattr(cls, "CL:4033002",
            PermissibleValue(
                text="CL:4033002",
                description="A(n) neuroendocrine cell that is part of a(n) epithelium of crypt of Lieberkuhn.",
                meaning=CL["4033002"]))
        setattr(cls, "CL:1000606",
            PermissibleValue(
                text="CL:1000606",
                description="Any neuron that has its soma located in some kidney.",
                meaning=CL["1000606"]))
        setattr(cls, "CL:4033059",
            PermissibleValue(
                text="CL:4033059",
                description="""A lactocyte that highly expresses genes associated with transcription, immune cell function, and cellular stress. A lactocyte type 1 also expresses genes involved in milk component biosynthesis (e.g., LALBA and CSNs), albeit at lower levels than a lactocyte type 2.""",
                meaning=CL["4033059"]))
        setattr(cls, "CL:0003039",
            PermissibleValue(
                text="CL:0003039",
                description="""A monostratified retinal ganglion cell with large soma and medium dendritic field, with dense dendritic arbor.""",
                meaning=CL["0003039"]))
        setattr(cls, "CL:0000871",
            PermissibleValue(
                text="CL:0000871",
                description="A secondary lymphoid organ macrophage found in the spleen.",
                meaning=CL["0000871"]))
        setattr(cls, "CL:0000353",
            PermissibleValue(
                text="CL:0000353",
                description="An undifferentiated cell produced by early cleavages of the fertilized egg (zygote).",
                meaning=CL["0000353"]))
        setattr(cls, "CL:0002074",
            PermissibleValue(
                text="CL:0002074",
                description="""The myoendocrine cellis a specialized myocyte localized mainly in the right and left atrial appendages, and also scattered within other areas of the atria and along the conductive system in the ventricular septum. The most conspicuous feature distinguishing myoendocrine cells from other atrial myoctyes is the presence of membane-bounded secretory granules (these granules contain precursor of cardiodilatins or atrial natriuretic polypeptides).""",
                meaning=CL["0002074"]))
        setattr(cls, "CL:0002614",
            PermissibleValue(
                text="CL:0002614",
                description="A neuron of the substantia nigra.",
                meaning=CL["0002614"]))
        setattr(cls, "CL:0000716",
            PermissibleValue(
                text="CL:0000716",
                description="A crystal cell that derives from the larval lymph gland.",
                meaning=CL["0000716"]))
        setattr(cls, "CL:0012001",
            PermissibleValue(
                text="CL:0012001",
                description="A CNS neuron of the forebrain.",
                meaning=CL["0012001"]))
        setattr(cls, "CL:0002266",
            PermissibleValue(
                text="CL:0002266",
                description="A type D cell of the small intestine.",
                meaning=CL["0002266"]))
        setattr(cls, "CL:0000126",
            PermissibleValue(
                text="CL:0000126",
                description="""A neuroglial cell of ectodermal origin, i.e., the astrocytes and oligodendrocytes considered together.""",
                meaning=CL["0000126"]))
        setattr(cls, "CL:0002652",
            PermissibleValue(
                text="CL:0002652",
                description="""A venule endothelial cell that is cubodial, expresses leukocyte-specific receptors, and allows for passage of lymphocytes into bloodstream.""",
                meaning=CL["0002652"]))
        setattr(cls, "CL:0000547",
            PermissibleValue(
                text="CL:0000547",
                description="""An immature, nucleated erythrocyte occupying the stage of erythropoeisis that follows formation of erythroid progenitor cells. This cell is CD71-positive, has both a nucleus and a nucleolus, and lacks hematopoeitic lineage markers.""",
                meaning=CL["0000547"]))
        setattr(cls, "CL:0000737",
            PermissibleValue(
                text="CL:0000737",
                description="Muscle cell which has as its direct parts myofilaments organized into sarcomeres.",
                meaning=CL["0000737"]))
        setattr(cls, "CL:4023042",
            PermissibleValue(
                text="CL:4023042",
                description="""A transcriptomically distinct corticothalamic-projecting neuron with a soma found in cortical layer 6. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: Deep layer (non-IT) excitatory neurons', Author Categories: 'CrossArea_subclass', clusters L6 CT.""",
                meaning=CL["4023042"]))
        setattr(cls, "CL:1001127",
            PermissibleValue(
                text="CL:1001127",
                description="Any vasa recta cell that is part of some outer renal medulla vasa recta.",
                meaning=CL["1001127"]))
        setattr(cls, "CL:0008013",
            PermissibleValue(
                text="CL:0008013",
                description="""A visceromotor motor neuron whose soma is located in the hindbrain, and which synapses to parasympathetic neurons that innervate tear glands, sweat glands, and the smooth muscles of the head.""",
                meaning=CL["0008013"]))
        setattr(cls, "CL:0002578",
            PermissibleValue(
                text="CL:0002578",
                description="A preadipocyte found in mesenteric tissue.",
                meaning=CL["0002578"]))
        setattr(cls, "CL:0009086",
            PermissibleValue(
                text="CL:0009086",
                description="An endothelial cell that is part of a respiratory system lymphatic vessel.",
                meaning=CL["0009086"]))
        setattr(cls, "CL:0000177",
            PermissibleValue(
                text="CL:0000177",
                description="Any secretory cell that is capable of some testosterone secretion.",
                meaning=CL["0000177"]))
        setattr(cls, "CL:0002643",
            PermissibleValue(
                text="CL:0002643",
                description="An epithelial cell of stratum corneum of esophageal epithelium that lacks keratin.",
                meaning=CL["0002643"]))
        setattr(cls, "CL:0002022",
            PermissibleValue(
                text="CL:0002022",
                description="An enucleate erythrocyte that is Lyg-76-high.",
                meaning=CL["0002022"]))
        setattr(cls, "CL:0002632",
            PermissibleValue(
                text="CL:0002632",
                description="Any epithelial cell that is part of some lower respiratory tract epithelium.",
                meaning=CL["0002632"]))
        setattr(cls, "CL:0000055",
            PermissibleValue(
                text="CL:0000055",
                description="A precursor cell with a limited number of potential fates.",
                meaning=CL["0000055"]))
        setattr(cls, "CL:0002535",
            PermissibleValue(
                text="CL:0002535",
                description="An epithelial cell of the cervix.",
                meaning=CL["0002535"]))
        setattr(cls, "CL:2000091",
            PermissibleValue(
                text="CL:2000091",
                description="Any microvascular endothelial cell that is part of a endometrial blood vessel.",
                meaning=CL["2000091"]))
        setattr(cls, "CL:0000251",
            PermissibleValue(
                text="CL:0000251",
                meaning=CL["0000251"]))
        setattr(cls, "CL:0001016",
            PermissibleValue(
                text="CL:0001016",
                description="""Immature CD1a-positive Langerhans cell is a CD1a-positive Langerhans cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0001016"]))
        setattr(cls, "CL:1001587",
            PermissibleValue(
                text="CL:1001587",
                description="Glandular cell of uterine cervix epithelium.",
                meaning=CL["1001587"]))
        setattr(cls, "CL:0002162",
            PermissibleValue(
                text="CL:0002162",
                description="""An extremely flattened cell type found on the inner side of the tympanic membrane. The surface of this cell type carries sparse pleomorphic microvilli that are more common near the junctional zones.""",
                meaning=CL["0002162"]))
        setattr(cls, "CL:0002576",
            PermissibleValue(
                text="CL:0002576",
                description="""A glial cell that is part of the perineurium. This cell type has thin long bipolar cytoplasmic processes, pinocytotic vesicles, fragments of external lamina and/or external lamina-like material, attachment plaques, and desmosome-like junctions. Perineurial cells historically have been referred to as fibroblasts because of shape; however, unlike fibroblasts, a perineurial cell: does not have a compact nucleus and large endoplasmic reticulum; does have a double basement membrane opposed to a single basal lamina; is carefully joined to other perineurial cells by tight junctions into a single sheet as opposed to arranged in a large mass; and finally, can surround a small axon bundle at a nerve terminal whereas a fibroblast cannot.""",
                meaning=CL["0002576"]))
        setattr(cls, "CL:0000624",
            PermissibleValue(
                text="CL:0000624",
                description="""A mature alpha-beta T cell that expresses an alpha-beta T cell receptor and the CD4 coreceptor.""",
                meaning=CL["0000624"]))
        setattr(cls, "CL:0000523",
            PermissibleValue(
                text="CL:0000523",
                description="""A cell from the inner layer of the trophoblast of the early mammalian embryo that gives rise to the outer surface and villi of the chorion. Mononuclear crytoblasts fuse to give rise to a multinuclear cytotrophoblast.""",
                meaning=CL["0000523"]))
        setattr(cls, "CL:0002151",
            PermissibleValue(
                text="CL:0002151",
                description="""A promyelocyte that is considerably smaller, with more condensed chromatin, and nucleoli are no longer conspicuous.""",
                meaning=CL["0002151"]))
        setattr(cls, "CL:4023090",
            PermissibleValue(
                text="CL:4023090",
                description="""A basket cell with axonal arbors composed of frequent, short, curvy axonal branches that tend to be near their somata and within the same layer.""",
                meaning=CL["4023090"]))
        setattr(cls, "CL:4023032",
            PermissibleValue(
                text="CL:4023032",
                meaning=CL["4023032"]))
        setattr(cls, "CL:4052015",
            PermissibleValue(
                text="CL:4052015",
                description="Any capillary endothelial cell that is part of an endocrine gland.",
                meaning=CL["4052015"]))
        setattr(cls, "CL:1000353",
            PermissibleValue(
                text="CL:1000353",
                description="A M cell that is part of the epithelium of small intestine.",
                meaning=CL["1000353"]))
        setattr(cls, "CL:0000256",
            PermissibleValue(
                text="CL:0000256",
                meaning=CL["0000256"]))
        setattr(cls, "CL:0003031",
            PermissibleValue(
                text="CL:0003031",
                description="""A monostratified retinal ganglion cell that has post synaptic terminals in sublaminar layer S4 and is depolarized by illumination of its receptive field center.""",
                meaning=CL["0003031"]))
        setattr(cls, "CL:2000032",
            PermissibleValue(
                text="CL:2000032",
                description="A neuron that is part of a peripheral nervous system.",
                meaning=CL["2000032"]))
        setattr(cls, "CL:0000428",
            PermissibleValue(
                text="CL:0000428",
                meaning=CL["0000428"]))
        setattr(cls, "CL:0010004",
            PermissibleValue(
                text="CL:0010004",
                description="A mononuclear cell that is part_of a bone marrow.",
                meaning=CL["0010004"]))
        setattr(cls, "CL:4047004",
            PermissibleValue(
                text="CL:4047004",
                description="A(n) type EC enteroendocrine cell that is cycling.",
                meaning=CL["4047004"]))
        setattr(cls, "CL:0005000",
            PermissibleValue(
                text="CL:0005000",
                description="A CNS interneuron located in the spinal cord.",
                meaning=CL["0005000"]))
        setattr(cls, "CL:0000836",
            PermissibleValue(
                text="CL:0000836",
                description="""A precursor in the granulocytic series, being a cell intermediate in development between a myeloblast and myelocyte, that has distinct nucleoli, a nuclear-to-cytoplasmic ratio of 5:1 to 3:1, and containing a few primary cytoplasmic granules. Markers for this cell are fucosyltransferase FUT4-positive, CD33-positive, integrin alpha-M-negative, low affinity immunoglobulin gamma Fc region receptor III-negative, and CD24-negative.""",
                meaning=CL["0000836"]))
        setattr(cls, "CL:1001106",
            PermissibleValue(
                text="CL:1001106",
                description="""An epithelial cell that is part of some loop of Henle thick ascending limb. It is known in some mammalian species that this cell may express the Na+-K+-2Cl− cotransporter (NKCC2) apically.""",
                meaning=CL["1001106"]))
        setattr(cls, "CL:0000467",
            PermissibleValue(
                text="CL:0000467",
                description="A peptide hormone secreting cell that produces adrenocorticotropin, or corticotropin.",
                meaning=CL["0000467"]))
        setattr(cls, "CL:0000431",
            PermissibleValue(
                text="CL:0000431",
                description="""A pigment cell derived from the neural crest. The cell contains flat light-reflecting platelets, probably of guanine, in stacks called reflecting platelets or iridisomes. The color-generating components produce a silver, gold, or iridescent color.""",
                meaning=CL["0000431"]))
        setattr(cls, "CL:0002390",
            PermissibleValue(
                text="CL:0002390",
                description="A blastoconidium that has only one nucleus.",
                meaning=CL["0002390"]))
        setattr(cls, "CL:4033035",
            PermissibleValue(
                text="CL:4033035",
                description="An ON bipolar cell that has large dendritic and axonal fields.",
                meaning=CL["4033035"]))
        setattr(cls, "CL:0000614",
            PermissibleValue(
                text="CL:0000614",
                description="""A basophil precursor in the granulocytic series, being a cell intermediate in development between a promyelocyte and a metamyelocyte; in this stage, production of primary granules is complete and basophil-specific granules has started. No nucleolus is present. Markers are being integrin alpha-M-positive, fucosyltransferase FUT4-positive, CD33-positive, CD24-positive, aminopeptidase N-positive.""",
                meaning=CL["0000614"]))
        setattr(cls, "CL:0000080",
            PermissibleValue(
                text="CL:0000080",
                description="""A cell which moves among different tissues of the body, via blood, lymph, or other medium.""",
                meaning=CL["0000080"]))
        setattr(cls, "CL:0002439",
            PermissibleValue(
                text="CL:0002439",
                description="A NK1.1-positive T cell that is NKGA2-positive.",
                meaning=CL["0002439"]))
        setattr(cls, "CL:4033003",
            PermissibleValue(
                text="CL:4033003",
                description="A(n) myoepithelial cell that is part of a(n) bronchus submucosal gland.",
                meaning=CL["4033003"]))
        setattr(cls, "CL:0009029",
            PermissibleValue(
                text="CL:0009029",
                description="A mesothelial cell that is located in a vermiform appendix.",
                meaning=CL["0009029"]))
        setattr(cls, "CL:0000478",
            PermissibleValue(
                text="CL:0000478",
                description="A peptide hormone secreting cell that secretes oxytocin stimulating hormone",
                meaning=CL["0000478"]))
        setattr(cls, "CL:0004001",
            PermissibleValue(
                text="CL:0004001",
                description="""An interneuron whose axon stays entirely within the gray matter region where the cell body resides.""",
                meaning=CL["0004001"]))
        setattr(cls, "CL:0000797",
            PermissibleValue(
                text="CL:0000797",
                description="""A mature alpha-beta T cell of the columnar epithelium of the gastrointestinal tract. Intraepithelial T cells often have distinct developmental pathways and activation requirements.""",
                meaning=CL["0000797"]))
        setattr(cls, "CL:0005021",
            PermissibleValue(
                text="CL:0005021",
                description="""Mesenchymal derived lymphatic progenitor cells that give rise to the superficial lymphatics.""",
                meaning=CL["0005021"]))
        setattr(cls, "CL:1000338",
            PermissibleValue(
                text="CL:1000338",
                description="""An enterocyte that is part of the epithelium of crypt of Lieberkuhn of small intestine.""",
                meaning=CL["1000338"]))
        setattr(cls, "CL:0000746",
            PermissibleValue(
                text="CL:0000746",
                description="""Cardiac muscle cells are striated muscle cells that are responsible for heart contraction. In mammals, the contractile fiber resembles those of skeletal muscle but are only one third as large in diameter, are richer in sarcoplasm, and contain centrally located instead of peripheral nuclei.""",
                meaning=CL["0000746"]))
        setattr(cls, "CL:0000958",
            PermissibleValue(
                text="CL:0000958",
                description="""A transitional stage B cell that migrates from the bone marrow into the peripheral circulation, and finally to the spleen. This cell type has the phenotype surface IgM-positive, surface IgD-negative, CD21-negative, CD23-negative, and CD62L-negative, and CD93-positive. This cell type has also been described as IgM-high, CD19-positive, B220-positive, AA4-positive, and CD23-negative.""",
                meaning=CL["0000958"]))
        setattr(cls, "CL:4047047",
            PermissibleValue(
                text="CL:4047047",
                description="""An enteric glial cell located within the ganglia of the enteric nervous system. This cell is characterized by it’s small somata and short, irregularly branched processes that surround neuronal cell bodies in the myenteric and submucosal ganglia. This cell plays important roles in modulating neuronal activity and neurogenesis in the gastrointestinal tract.""",
                meaning=CL["4047047"]))
        setattr(cls, "CL:0002428",
            PermissibleValue(
                text="CL:0002428",
                description="""A double-positive thymocyte that is large (i.e. has a high forward scatter signal in flow cytometry) and is actively proliferating.""",
                meaning=CL["0002428"]))
        setattr(cls, "CL:0002433",
            PermissibleValue(
                text="CL:0002433",
                description="""A CD4-positive, CD8-negative thymocyte that expresses high levels of the alpha-beta T cell receptor and is CD69-positive.""",
                meaning=CL["0002433"]))
        setattr(cls, "CL:0000890",
            PermissibleValue(
                text="CL:0000890",
                description="""An elicited macrophage characterized by low production of pro-inflammatory and Th1 polarizing cytokines and high expression of arginase-1, and associated with tissue remodelling.""",
                meaning=CL["0000890"]))
        setattr(cls, "CL:0000169",
            PermissibleValue(
                text="CL:0000169",
                description="""A cell that secretes insulin and is located towards the center of the islets of Langerhans.""",
                meaning=CL["0000169"]))
        setattr(cls, "CL:4047003",
            PermissibleValue(
                text="CL:4047003",
                description="A(n) plasma cell that is cycling.",
                meaning=CL["4047003"]))
        setattr(cls, "CL:4023063",
            PermissibleValue(
                text="CL:4023063",
                description="An interneuron that is derived from the medial ganglionic eminence.",
                meaning=CL["4023063"]))
        setattr(cls, "CL:0001003",
            PermissibleValue(
                text="CL:0001003",
                description="""Mature CD8-alpha-negative CD11b-positive dendritic cell is a CD8-alpha-negative CD11b-positive dendritic cell that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001003"]))
        setattr(cls, "CL:4047030",
            PermissibleValue(
                text="CL:4047030",
                description="""A specialized endothelial cell located in the transition zone between capillaries and small venules in the microvascular system. It exhibits characteristics of both capillary and venous cells, expressing markers from both types. This cell plays a role in regulating blood flow and substance exchange between blood and tissues.""",
                meaning=CL["4047030"]))
        setattr(cls, "CL:4033046",
            PermissibleValue(
                text="CL:4033046",
                description="""A midget ganglion cell that depolarizes in response to increased light intensity in the center of its receptive field. The majority of input that this cell receives comes from invaginating midget bipolar cells.""",
                meaning=CL["4033046"]))
        setattr(cls, "CL:0008019",
            PermissibleValue(
                text="CL:0008019",
                description="""A non-polarised cell precursor cell that is part of some mesenchyme, is associated with the cell matrix but is not connected to other cells and is capable of migration.""",
                meaning=CL["0008019"]))
        setattr(cls, "CL:0002275",
            PermissibleValue(
                text="CL:0002275",
                description="A PP cell located in the islets of the pancreas.",
                meaning=CL["0002275"]))
        setattr(cls, "CL:0002548",
            PermissibleValue(
                text="CL:0002548",
                description="A fibroblast that is part of the heart.",
                meaning=CL["0002548"]))
        setattr(cls, "CL:0000732",
            PermissibleValue(
                text="CL:0000732",
                meaning=CL["0000732"]))
        setattr(cls, "CL:4023164",
            PermissibleValue(
                text="CL:4023164",
                description="""A bushy cell that receives a large number of medium-sized synapses, called modified endbulbs. Globular bushy cells extend to the superior olive on both sides of the brainstem where they give input to the bipolar neurons.""",
                meaning=CL["4023164"]))
        setattr(cls, "CL:0004221",
            PermissibleValue(
                text="CL:0004221",
                description="""A flag amacrine cell with post-synaptic terminals in S2 and S3. This cell type releases the neurotransmitter glycine.""",
                meaning=CL["0004221"]))
        setattr(cls, "CL:4033028",
            PermissibleValue(
                text="CL:4033028",
                description="""An OFF diffuse bipolar cell that predominantly connects to ON parasol cells and lateral amacrine cells. This cell contains a large number of synaptic ribbons and a small axon arbor area.""",
                meaning=CL["4033028"]))
        setattr(cls, "CL:4030054",
            PermissibleValue(
                text="CL:4030054",
                description="""A DRD1-expressing medium spiny neuron that is part of dense, RXFP1-positive cell islands throughout the nucleus accumbens, putamen, and near the adjacent septal nuclei.""",
                meaning=CL["4030054"]))
        setattr(cls, "CL:0002322",
            PermissibleValue(
                text="CL:0002322",
                description="A stem cell of embryonic origin.",
                meaning=CL["0002322"]))
        setattr(cls, "CL:0000451",
            PermissibleValue(
                text="CL:0000451",
                description="""A cell of hematopoietic origin, typically resident in particular tissues, specialized in the uptake, processing, and transport of antigens to lymph nodes for the purpose of stimulating an immune response via T cell activation. These cells are lineage negative (CD3-negative, CD19-negative, CD34-negative, and CD56-negative).""",
                meaning=CL["0000451"]))
        setattr(cls, "CL:4023016",
            PermissibleValue(
                text="CL:4023016",
                description="""A transcriptomically distinct cortical GABAergic neuron that expresses the vasocactive intestinal polypeptide and that has its soma located in the cerebral cortex. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: CGE-derived interneurons', Author Categories: 'CrossArea_subclass', cluster Vip.""",
                meaning=CL["4023016"]))
        setattr(cls, "CL:0009073",
            PermissibleValue(
                text="CL:0009073",
                description="""A thymic medullary epithelial cell considered to be a post-AIRE cell. This group of AIRE-mTECs is heterogeneous and also includes mTECs within Hassall's Corpuscles.""",
                meaning=CL["0009073"]))
        setattr(cls, "CL:1000282",
            PermissibleValue(
                text="CL:1000282",
                description="A smooth muscle cell that is part of the ascending colon.",
                meaning=CL["1000282"]))
        setattr(cls, "CL:1000315",
            PermissibleValue(
                text="CL:1000315",
                description="A goblet cell that is part of the epithelium of principal gastric gland.",
                meaning=CL["1000315"]))
        setattr(cls, "CL:0002148",
            PermissibleValue(
                text="CL:0002148",
                description="A cell found within the dental pulp.",
                meaning=CL["0002148"]))
        setattr(cls, "CL:0000530",
            PermissibleValue(
                text="CL:0000530",
                description="""A neuron that develops during the early segmentation stages in teleosts, before the neural tube is formed.""",
                meaning=CL["0000530"]))
        setattr(cls, "CL:0000439",
            PermissibleValue(
                text="CL:0000439",
                description="A peptide hormone cell that secretes prolactin.",
                meaning=CL["0000439"]))
        setattr(cls, "CL:0002409",
            PermissibleValue(
                text="CL:0002409",
                description="""A thymocyte that has a T cell receptor consisting of a gamma chain that does not contain the Vgamma2 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-negative.""",
                meaning=CL["0002409"]))
        setattr(cls, "CL:4052049",
            PermissibleValue(
                text="CL:4052049",
                description="""An columnar/cuboidal epithelial cell that is part of the striated duct of salivary gland, characterized by basal striations formed by infoldings of the plasma membrane. This cell play a crucial role in modifying the electrolyte composition and concentration of saliva through active ion transport, particularly the absorption of sodium and secretion of potassium.""",
                meaning=CL["4052049"]))
        setattr(cls, "CL:1001210",
            PermissibleValue(
                text="CL:1001210",
                description="""Any vasa recta ascending limb cell that is part of some outer medulla ascending vasa recta.""",
                meaning=CL["1001210"]))
        setattr(cls, "CL:0002221",
            PermissibleValue(
                text="CL:0002221",
                description="A squamous cell that has keratin in the esophagus.",
                meaning=CL["0002221"]))
        setattr(cls, "CL:4047011",
            PermissibleValue(
                text="CL:4047011",
                description="An endothelial cell that lines the veins in the fetal circulatory system.",
                meaning=CL["4047011"]))
        setattr(cls, "CL:0003020",
            PermissibleValue(
                text="CL:0003020",
                description="A retinal ganglion cell C that has post-synaptic terminals in S2.",
                meaning=CL["0003020"]))
        setattr(cls, "CL:1000489",
            PermissibleValue(
                text="CL:1000489",
                description="A reticular cell that is part of the splenic cord.",
                meaning=CL["1000489"]))
        setattr(cls, "CL:0000376",
            PermissibleValue(
                text="CL:0000376",
                meaning=CL["0000376"]))
        setattr(cls, "CL:0009000",
            PermissibleValue(
                text="CL:0009000",
                description="""A sensory neuron of the spinal nerve that senses body position and sends information about how much the muscle is stretched to the spinal cord.""",
                meaning=CL["0009000"]))
        setattr(cls, "CL:0000757",
            PermissibleValue(
                text="CL:0000757",
                description="""An ON-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the inner half of the inner plexiform layer. The axon terminal is restricted to sublamina 3 of the inner plexiform layer. It is narrowly stratified and branched. The dendritic tree has many delicate branches.""",
                meaning=CL["0000757"]))
        setattr(cls, "CL:0002012",
            PermissibleValue(
                text="CL:0002012",
                description="A proerythoblast that is Kit-low, Lyg76-positive, and CD71-positive.",
                meaning=CL["0002012"]))
        setattr(cls, "CL:0000794",
            PermissibleValue(
                text="CL:0000794",
                description="""A CD8-positive, alpha-beta T cell that is capable of killing target cells in an antigen specific manner with the phenotype perforin-positive and granzyme B-positive.""",
                meaning=CL["0000794"]))
        setattr(cls, "CL:0000223",
            PermissibleValue(
                text="CL:0000223",
                description="A cell of the inner of the three germ layers of the embryo.",
                meaning=CL["0000223"]))
        setattr(cls, "CL:0000134",
            PermissibleValue(
                text="CL:0000134",
                description="""A connective tissue cell that normally gives rise to other cells that are organized as three-dimensional masses. In humans, this cell type is CD73-positive, CD90-positive, CD105-positive, CD45-negative, CD34-negative, and MHCII-negative. They may further differentiate into osteoblasts, adipocytes, myocytes, neurons, or chondroblasts in vitro. Originally described as residing in the bone marrow, this cell type is now known to reside in many, if not all, adult organs.""",
                meaning=CL["0000134"]))
        setattr(cls, "CL:1000307",
            PermissibleValue(
                text="CL:1000307",
                description="A fibroblast that is part of the dense regular elastic tissue.",
                meaning=CL["1000307"]))
        setattr(cls, "CL:0000971",
            PermissibleValue(
                text="CL:0000971",
                description="""An IgM memory B cell is an unswitched memory B cell with the phenotype IgM-positive and IgD-negative.""",
                meaning=CL["0000971"]))
        setattr(cls, "CL:0011009",
            PermissibleValue(
                text="CL:0011009",
                description="A plasmatocyte derived from the embryonic head mesoderm.",
                meaning=CL["0011009"]))
        setattr(cls, "CL:0000462",
            PermissibleValue(
                text="CL:0000462",
                description="""A cell of mesodermal origin that is closely associated with the epithelium of an imaginal disc. It is a precursor of some of the insect's adult muscles.""",
                meaning=CL["0000462"]))
        setattr(cls, "CL:0001065",
            PermissibleValue(
                text="CL:0001065",
                description="""A lymphocyte that lacks characteristic T cell, B cell, myeloid cell, and dendritic cell markers, that functions as part of the innate immune response to produce cytokines and other effector responses.""",
                meaning=CL["0001065"]))
        setattr(cls, "CL:0000997",
            PermissibleValue(
                text="CL:0000997",
                description="""Immature CD8-alpha-negative CD11b-positive dendritic cell is a CD8-alpha-negative CD11b-positive dendritic cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0000997"]))
        setattr(cls, "CL:0003028",
            PermissibleValue(
                text="CL:0003028",
                description="""A monostratified retinal ganglion cell that has a small dendrite field with a dense dendrite arbor with post synaptic terminals in sublaminer layer S4.""",
                meaning=CL["0003028"]))
        setattr(cls, "CL:0000854",
            PermissibleValue(
                text="CL:0000854",
                description="""Interneuromast cell is a neuroectodermal cell deposited by the migrating lateral line primordium between the neuromasts. Interneuromast cells proliferate and migrate to form additional neuromasts.""",
                meaning=CL["0000854"]))
        setattr(cls, "CL:0002333",
            PermissibleValue(
                text="CL:0002333",
                description="An adipocyte derived from a neural crest cell.",
                meaning=CL["0002333"]))
        setattr(cls, "CL:0002616",
            PermissibleValue(
                text="CL:0002616",
                description="An adipocyte of perirenal fat tissue.",
                meaning=CL["0002616"]))
        setattr(cls, "CL:0007012",
            PermissibleValue(
                text="CL:0007012",
                description="""Odontoblast that non-terminally differentiated, located in the odontogenic papilla and dentine tissue, and transforms from a odontoblast cell.""",
                meaning=CL["0007012"]))
        setattr(cls, "CL:1000083",
            PermissibleValue(
                text="CL:1000083",
                meaning=CL["1000083"]))
        setattr(cls, "CL:0002415",
            PermissibleValue(
                text="CL:0002415",
                description="A Vgamma1.1-positive, Vdelta6.3-positive thymocyte that is CD24-positive.",
                meaning=CL["0002415"]))
        setattr(cls, "CL:2000062",
            PermissibleValue(
                text="CL:2000062",
                description="Any capillary endothelial cell that is part of a placenta.",
                meaning=CL["2000062"]))
        setattr(cls, "CL:1001221",
            PermissibleValue(
                text="CL:1001221",
                description="Any smooth muscle cell that is part of some kidney arcuate vein.",
                meaning=CL["1001221"]))
        setattr(cls, "CL:4030053",
            PermissibleValue(
                text="CL:4030053",
                description="""A DRD1-expressing, medium spiny neuron-like granule cell that is part of an Island of Calleja.""",
                meaning=CL["4030053"]))
        setattr(cls, "CL:0001027",
            PermissibleValue(
                text="CL:0001027",
                description="""CD7-negative lymphoid progenitor cell is a lymphoid progenitor cell that is CD34-positive, CD7-negative and CD45RA-negative.""",
                meaning=CL["0001027"]))
        setattr(cls, "CL:4030055",
            PermissibleValue(
                text="CL:4030055",
                description="""A urothelial cell that is part of the regenerative layer(s) of cells directly superficial to basal cells in urothelium. The layer of intermediate cells in the urothelium ranges from one to several layers thick depending on the species with intermediate cells attached to adjacent cell layers and one another via desmosomes.""",
                meaning=CL["4030055"]))
        setattr(cls, "CL:2000060",
            PermissibleValue(
                text="CL:2000060",
                description="""A trophoblast of placental villi.  These cells fuse to form synctial  trophoplast - the placental side of the interface between the placenta and maternal blood sinusoids in the decidua.""",
                meaning=CL["2000060"]))
        setattr(cls, "CL:1000682",
            PermissibleValue(
                text="CL:1000682",
                description="A cell that is part of an interstitum of a renal medulla.",
                meaning=CL["1000682"]))
        setattr(cls, "CL:1000291",
            PermissibleValue(
                text="CL:1000291",
                description="A muscle cell that is part of the posterior internodal tract.",
                meaning=CL["1000291"]))
        setattr(cls, "CL:0009108",
            PermissibleValue(
                text="CL:0009108",
                description="""A lymphatic endothelial cell located in the subcapsular sinus floor of a lymph node. In human, it's characterized by a unique marker expression (TNFRSF9+).""",
                meaning=CL["0009108"]))
        setattr(cls, "CL:1000301",
            PermissibleValue(
                text="CL:1000301",
                description="A fibroblast that is part of the subepithelial connective tissue of prostatic gland.",
                meaning=CL["1000301"]))
        setattr(cls, "CL:0009065",
            PermissibleValue(
                text="CL:0009065",
                description="An intestinal tuft cell that is located in the anorectum.",
                meaning=CL["0009065"]))
        setattr(cls, "CL:0000681",
            PermissibleValue(
                text="CL:0000681",
                description="""A cell present in the developing CNS. Functions as both a precursor cell and as a scaffold to support neuronal migration.""",
                meaning=CL["0000681"]))
        setattr(cls, "CL:0002593",
            PermissibleValue(
                text="CL:0002593",
                description="A smooth muscle of the internal thoracic artery.",
                meaning=CL["0002593"]))
        setattr(cls, "CL:4023112",
            PermissibleValue(
                text="CL:4023112",
                description="""An afferent neuron of the vestibular system that innervate the base of the hair cell and increase or decrease their neural firing rate as the receptor cell is excited or inhibited.""",
                meaning=CL["4023112"]))
        setattr(cls, "CL:0002023",
            PermissibleValue(
                text="CL:0002023",
                description="""A megakaroycotye progenitor cell that is CD34-positive, CD41-positive and CD42-positive on the cell surface.""",
                meaning=CL["0002023"]))
        setattr(cls, "CL:0000458",
            PermissibleValue(
                text="CL:0000458",
                description="A cell type that secretes 5-Hydroxytryptamine (serotonin).",
                meaning=CL["0000458"]))
        setattr(cls, "CL:0002029",
            PermissibleValue(
                text="CL:0002029",
                description="""A lineage-negative, Kit-positive, CD45-positive mast cell progenitor that is Fc-epsilon RIalpha-low.""",
                meaning=CL["0002029"]))
        setattr(cls, "CL:0000178",
            PermissibleValue(
                text="CL:0000178",
                description="""A Leydig cell is a testosterone-secreting cell in the interstitial area, between the seminiferous tubules, in the testis.""",
                meaning=CL["0000178"]))
        setattr(cls, "CL:1000804",
            PermissibleValue(
                text="CL:1000804",
                description="A kidney cell that is part of an interstitial compartment of an outer renal medulla.",
                meaning=CL["1000804"]))
        setattr(cls, "CL:0000384",
            PermissibleValue(
                text="CL:0000384",
                meaning=CL["0000384"]))
        setattr(cls, "CL:1000497",
            PermissibleValue(
                text="CL:1000497",
                description="A cell that is part of a kidney.",
                meaning=CL["1000497"]))
        setattr(cls, "CL:0000949",
            PermissibleValue(
                text="CL:0000949",
                description="""A plasmablast that secretes IgD, and which occur in a small proportion of B cells in the adult.""",
                meaning=CL["0000949"]))
        setattr(cls, "CL:0011019",
            PermissibleValue(
                text="CL:0011019",
                description="A mesothelial cell that is part of the epicardium.",
                meaning=CL["0011019"]))
        setattr(cls, "CL:0000469",
            PermissibleValue(
                text="CL:0000469",
                description="""A neural progenitor cell that is the daughter of a neuroblast (sensu arthopoda).  The progeny of ganglion mother cells develop into neurons, glia and (occasionally) epithelial cells.""",
                meaning=CL["0000469"]))
        setattr(cls, "CL:4030060",
            PermissibleValue(
                text="CL:4030060",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in cortical layer 2.""",
                meaning=CL["4030060"]))
        setattr(cls, "CL:4030003",
            PermissibleValue(
                text="CL:4030003",
                description="A cell that makes up the loose connective tissue of the thymus.",
                meaning=CL["4030003"]))
        setattr(cls, "CL:0002471",
            PermissibleValue(
                text="CL:0002471",
                description="Gr1-low non-classical monocyte that lacks expression of a MHC-II complex.",
                meaning=CL["0002471"]))
        setattr(cls, "CL:2000042",
            PermissibleValue(
                text="CL:2000042",
                description="Any fibroblast that is part of a embryo.",
                meaning=CL["2000042"]))
        setattr(cls, "CL:0000346",
            PermissibleValue(
                text="CL:0000346",
                description="""A specialized mesenchymal cell that resides in the dermal papilla located at the bottom of hair follicles. This cell plays a pivotal roles in hair formation, growth, and cycling.""",
                meaning=CL["0000346"]))
        setattr(cls, "CL:1001571",
            PermissibleValue(
                text="CL:1001571",
                description="A pyramidal neuron with a soma found in the hippocampus.",
                meaning=CL["1001571"]))
        setattr(cls, "CL:0002463",
            PermissibleValue(
                text="CL:0002463",
                description="An adipose dendritic cell that is SIRPa-positive.",
                meaning=CL["0002463"]))
        setattr(cls, "CL:0000415",
            PermissibleValue(
                text="CL:0000415",
                description="A cell whose nucleus has two haploid genomes.",
                meaning=CL["0000415"]))
        setattr(cls, "CL:0002507",
            PermissibleValue(
                text="CL:0002507",
                description="""A dermal dendritic cell isolated from skin draining lymph nodes that is langerin-positive, MHC-II-positive, and CD4-negative and CD8a-negative.""",
                meaning=CL["0002507"]))
        setattr(cls, "CL:0000210",
            PermissibleValue(
                text="CL:0000210",
                description="A cell specialized in detecting light stimuli that are involved in visual perception.",
                meaning=CL["0000210"]))
        setattr(cls, "CL:0002036",
            PermissibleValue(
                text="CL:0002036",
                description="""A hematopoietic progenitor that has some limited self-renewal capability. Cells are lin-negative, Kit-positive, CD34-positive, and Slamf1-positive.""",
                meaning=CL["0002036"]))
        setattr(cls, "CL:1000361",
            PermissibleValue(
                text="CL:1000361",
                description="A transitional myocyte that is part of the interatrial septum.",
                meaning=CL["1000361"]))
        setattr(cls, "CL:0000101",
            PermissibleValue(
                text="CL:0000101",
                description="Any neuron having a sensory function; an afferent neuron conveying sensory impulses.",
                meaning=CL["0000101"]))
        setattr(cls, "CL:1001220",
            PermissibleValue(
                text="CL:1001220",
                description="Any endothelial cell that is part of some kidney arcuate vein.",
                meaning=CL["1001220"]))
        setattr(cls, "CL:0003033",
            PermissibleValue(
                text="CL:0003033",
                description="""A monostratified retinal ganglion cell that has a large soma, a medium dendritic field with post synaptic terminals in sublaminar layer S3.""",
                meaning=CL["0003033"]))
        setattr(cls, "CL:0002351",
            PermissibleValue(
                text="CL:0002351",
                description="""A progenitor cell that is able to differentiate into the pancreas alpha, beta and delta endocrine cells. This cell type expresses neurogenin-3 and Isl-1.""",
                meaning=CL["0002351"]))
        setattr(cls, "CL:0000725",
            PermissibleValue(
                text="CL:0000725",
                description="Any cell that is capable of some nitrogen fixation.",
                meaning=CL["0000725"]))
        setattr(cls, "CL:1001209",
            PermissibleValue(
                text="CL:1001209",
                description="""Any vasa recta ascending limb cell that is part of some inner medulla ascending vasa recta.""",
                meaning=CL["1001209"]))
        setattr(cls, "CL:0002002",
            PermissibleValue(
                text="CL:0002002",
                description="""A granulocyte monocyte progenitor that is Kit-positive, CD34-positive, Fc-gamma receptor II/II-positive, and is Sca-1-negative, Il7ra-negative, Cxc3r1-negative, and CD90-negative.""",
                meaning=CL["0002002"]))
        setattr(cls, "CL:4033092",
            PermissibleValue(
                text="CL:4033092",
                description="""An enterocyte that is part of a duodenal epithelium and expresses beta-1,3-glucuronyltransferase 1 (B3GAT1), also known as CD57 or HNK-1.""",
                meaning=CL["4033092"]))
        setattr(cls, "CL:0000536",
            PermissibleValue(
                text="CL:0000536",
                description="A secondary neuron (sensu Teleostei) that has a motor function.",
                meaning=CL["0000536"]))
        setattr(cls, "CL:4042023",
            PermissibleValue(
                text="CL:4042023",
                description="""A GABAergic interneuron expressing PTHLH and PVALB that has its soma in a striatum. This GABAergic interneuron type presents a spatial expression gradient of PVALB in the mouse striatum.""",
                meaning=CL["4042023"]))
        setattr(cls, "CL:0011024",
            PermissibleValue(
                text="CL:0011024",
                description="""A double negative thymocyte that is CD3-positive, CD4-negative, CD8-negative, that that are present in the periphery in very low numbers and predominantly produce INF-gamma, TNF-alpha, and a low amount of TGF-beta, but not IL-2, IL-4, IL-10 or IL-13 upon activation.""",
                meaning=CL["0011024"]))
        setattr(cls, "CL:0000529",
            PermissibleValue(
                text="CL:0000529",
                meaning=CL["0000529"]))
        setattr(cls, "CL:0002678",
            PermissibleValue(
                text="CL:0002678",
                description="""A CD4-positive, CD25-positive alpha-beta regulatory T cell that has encountered antigen.""",
                meaning=CL["0002678"]))
        setattr(cls, "CL:0000764",
            PermissibleValue(
                text="CL:0000764",
                description="A immature or mature cell in the lineage leading to and including erythrocytes.",
                meaning=CL["0000764"]))
        setattr(cls, "CL:4023060",
            PermissibleValue(
                text="CL:4023060",
                description="A neuron that has its soma located in CA1-3 of the hippocampus.",
                meaning=CL["4023060"]))
        setattr(cls, "CL:0009021",
            PermissibleValue(
                text="CL:0009021",
                description="A stromal cell found in the lamina propria of the large intestine.",
                meaning=CL["0009021"]))
        setattr(cls, "CL:2000074",
            PermissibleValue(
                text="CL:2000074",
                description="Any leukocyte that is part of a spleen.",
                meaning=CL["2000074"]))
        setattr(cls, "CL:0009104",
            PermissibleValue(
                text="CL:0009104",
                description="""A fibroblastic reticular cell found in the lymph node germinal center dark zone (B cell zone).""",
                meaning=CL["0009104"]))
        setattr(cls, "CL:1000397",
            PermissibleValue(
                text="CL:1000397",
                description="An endothelial cell that is part of the venous sinus of red pulp of spleen.",
                meaning=CL["1000397"]))
        setattr(cls, "CL:0001017",
            PermissibleValue(
                text="CL:0001017",
                description="""Mature CD1a-positive Langerhans cell is a CD1a-positive Langerhans cell that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001017"]))
        setattr(cls, "CL:0004236",
            PermissibleValue(
                text="CL:0004236",
                description="""An amacrine cell with a medium dendritic field and post-synaptic terminals in S2, S3, and S4. This cell type releases the neurotransmitter gamma-aminobutyric acid (GABA).""",
                meaning=CL["0004236"]))
        setattr(cls, "CL:4042012",
            PermissibleValue(
                text="CL:4042012",
                description="""An L2 intratelencephalic projecting glutamatergic neuron with a soma on the L1-L2 border. This neuron type has small apical dendrites projecting to L1.""",
                meaning=CL["4042012"]))
        setattr(cls, "CL:0000676",
            PermissibleValue(
                text="CL:0000676",
                meaning=CL["0000676"]))
        setattr(cls, "CL:0002261",
            PermissibleValue(
                text="CL:0002261",
                description="An endothelial cell found in the mucosa associated with the facial skeleton.",
                meaning=CL["0002261"]))
        setattr(cls, "CL:4047101",
            PermissibleValue(
                text="CL:4047101",
                description="""A natural killer cell resident to the liver, located in the hepatic sinusoids. In humans this cell type is distinguished from circulating natural killer cells by CD49a or CD69 gene expression. Liver-resident natural killer cells have also been shown to express CCR5, EOMES, KLRB1, GZMK, and CXCR6 in humans.""",
                meaning=CL["4047101"]))
        setattr(cls, "CL:1001591",
            PermissibleValue(
                text="CL:1001591",
                description="Glandular cell of oviduct epithelium. Example: peg cells, ciliated cells.",
                meaning=CL["1001591"]))
        setattr(cls, "CL:0000942",
            PermissibleValue(
                text="CL:0000942",
                description="""A plasmacytoid dendritic cell developing in the thymus with phenotype CD11c-negative or low, CD45RA-positive, CD11b-negative, and CD123-positive.""",
                meaning=CL["0000942"]))
        setattr(cls, "CL:4030009",
            PermissibleValue(
                text="CL:4030009",
                description="""A brush border cell that is part of segment 1 (S1) of the proximal tubule epithelium, located in the renal cortex.""",
                meaning=CL["4030009"]))
        setattr(cls, "CL:0002362",
            PermissibleValue(
                text="CL:0002362",
                description="""A cell located in the outermost proliferative zone of the external germinal layer that can differentiate into astroglial cells and granule cells. This cell type is glial fibrillary acidic protein-positive and HNK1-positive.""",
                meaning=CL["0002362"]))
        setattr(cls, "CL:1000617",
            PermissibleValue(
                text="CL:1000617",
                description="Any kidney medulla cell that is part of some inner medulla of kidney.",
                meaning=CL["1000617"]))
        setattr(cls, "CL:0002380",
            PermissibleValue(
                text="CL:0002380",
                description="An asexual spore formed by Oomycetes; formed upon fertilization of an oosphere.",
                meaning=CL["0002380"]))
        setattr(cls, "CL:4040001",
            PermissibleValue(
                text="CL:4040001",
                description="""A horse-specific, highly invasive trophoblast cell that invades the endometrium where it forms endometrial cups.""",
                meaning=CL["4040001"]))
        setattr(cls, "CL:0000163",
            PermissibleValue(
                text="CL:0000163",
                description="""A cell of an endocrine gland, ductless glands that secrete substances which are released directly into the circulation and which influence metabolism and other body functions.""",
                meaning=CL["0000163"]))
        setattr(cls, "CL:0000634",
            PermissibleValue(
                text="CL:0000634",
                description="""A cuboidal cell which along with Boettcher's cells form the floor of the external spiral sulcus, external to the organ of Corti.""",
                meaning=CL["0000634"]))
        setattr(cls, "CL:0003041",
            PermissibleValue(
                text="CL:0003041",
                description="""An M9 retinal ganglion cells with synaptic terminals in S2 and is depolarized by illumination of its receptive field center.""",
                meaning=CL["0003041"]))
        setattr(cls, "CL:0000905",
            PermissibleValue(
                text="CL:0000905",
                description="""CD4-positive, alpha-beta memory T cell with the phenotype CCR7-negative, CD127-positive, CD45RA-negative, CD45RO-positive, and CD25-negative.""",
                meaning=CL["0000905"]))
        setattr(cls, "CL:4023128",
            PermissibleValue(
                text="CL:4023128",
                description="""a KNDy neuron that is located in the rostral periventricular region of the third ventricle.""",
                meaning=CL["4023128"]))
        setattr(cls, "CL:0000951",
            PermissibleValue(
                text="CL:0000951",
                description="A short lived plasma cell that secretes IgE.",
                meaning=CL["0000951"]))
        setattr(cls, "CL:0000607",
            PermissibleValue(
                text="CL:0000607",
                description="""A thick walled spore that stores and protects one or more nuclei following sexual reproduction in an Ascomycete.""",
                meaning=CL["0000607"]))
        setattr(cls, "CL:0000145",
            PermissibleValue(
                text="CL:0000145",
                description="""A cell capable of processing and presenting lipid and protein antigens to T cells in order to initiate an immune response.""",
                meaning=CL["0000145"]))
        setattr(cls, "CL:0000805",
            PermissibleValue(
                text="CL:0000805",
                description="""A thymocyte that has the phenotype CD4-negative, CD8-positive, CD44-negative, CD25-negative, and pre-TCR-positive.""",
                meaning=CL["0000805"]))
        setattr(cls, "CL:4030001",
            PermissibleValue(
                text="CL:4030001",
                description="A stromal cell that is part of the thymus.",
                meaning=CL["4030001"]))
        setattr(cls, "CL:0002252",
            PermissibleValue(
                text="CL:0002252",
                description="An epithelial cell of the lining of the esophagus.",
                meaning=CL["0002252"]))
        setattr(cls, "CL:4042016",
            PermissibleValue(
                text="CL:4042016",
                description="""A serous secreting cell that is part of a submucosal gland in the nasal cavity respiratory epithelium.""",
                meaning=CL["4042016"]))
        setattr(cls, "CL:0009003",
            PermissibleValue(
                text="CL:0009003",
                description="Any cell in the midgut (middle subdivision of a digestive tract) of an insect larva.",
                meaning=CL["0009003"]))
        setattr(cls, "CL:0002197",
            PermissibleValue(
                text="CL:0002197",
                description="""A parathyroid chief cell that is not actively secreting hormone. Contains small Golgi complexes with only a few grouped vesicles and membrane-bound secretory granules; glycogen and many lipofuscin granules abound but sacs of granular endoplasmic reticulum are rare and dispersed. In normal humans, inactive chief cells out number active chief cells in a ratio of 3-5:1.""",
                meaning=CL["0002197"]))
        setattr(cls, "CL:0007018",
            PermissibleValue(
                text="CL:0007018",
                description="Ciliated cell of the embryonic epidermis and functions in embryonic movements.",
                meaning=CL["0007018"]))
        setattr(cls, "CL:0008021",
            PermissibleValue(
                text="CL:0008021",
                description="""Any peripheral nervous system neuron that has its soma located in some anterior lateral line ganglion.""",
                meaning=CL["0008021"]))
        setattr(cls, "CL:0000886",
            PermissibleValue(
                text="CL:0000886",
                description="""A mucosa-associated lymphoid tissue macrophage found in the nasal and bronchial mucosa-associated lymphoid tissues.""",
                meaning=CL["0000886"]))
        setattr(cls, "CL:2000067",
            PermissibleValue(
                text="CL:2000067",
                description="Any fibroblast that is part of a cardiac atrium.",
                meaning=CL["2000067"]))
        setattr(cls, "CL:4070017",
            PermissibleValue(
                text="CL:4070017",
                description="""A motor neuron that controls pyloric filter movements; innervates the lateral pyloric muscle.""",
                meaning=CL["4070017"]))
        setattr(cls, "CL:0002241",
            PermissibleValue(
                text="CL:0002241",
                description="""A fibroblasts found in interstitial spaces in the pulmonary tract. Greater numbers of these cells are found in idiopathic pulmonary fibrosis.""",
                meaning=CL["0002241"]))
        setattr(cls, "CL:0000135",
            PermissibleValue(
                text="CL:0000135",
                description="""An inactive fibroblast; cytoplasm is sparse, endoplasmic reticulum is scanty with flattened nucleus. Term used by some histologists; when fibroblasts become relatively inactive in fiber formation. However, this cell has the potential for fibrogenesis in quiescent connective tissue of the adult, as well as during development, other histologists prefer to use the term fibroblast in all circumstances. These cells represent ~0.5% of peripheral blood leukocytes.""",
                meaning=CL["0000135"]))
        setattr(cls, "CL:0004218",
            PermissibleValue(
                text="CL:0004218",
                description="A horizontal cell with a small cell body, thin dendrites, and small dendritic arbor.",
                meaning=CL["0004218"]))
        setattr(cls, "CL:0000005",
            PermissibleValue(
                text="CL:0000005",
                description="Any fibroblast that is derived from the neural crest.",
                meaning=CL["0000005"]))
        setattr(cls, "CL:0009093",
            PermissibleValue(
                text="CL:0009093",
                description="A smooth muscle cell that is part of a placenta.",
                meaning=CL["0009093"]))
        setattr(cls, "CL:0000686",
            PermissibleValue(
                text="CL:0000686",
                description="A columnar/cuboidal epithelial cell that secretes cerebrospinal fluid.",
                meaning=CL["0000686"]))
        setattr(cls, "CL:0000081",
            PermissibleValue(
                text="CL:0000081",
                description="A cell found predominately in the blood.",
                meaning=CL["0000081"]))
        setattr(cls, "CL:4023079",
            PermissibleValue(
                text="CL:4023079",
                description="A GABAergic inhibitory neuron that is derived from the midbrain.",
                meaning=CL["4023079"]))
        setattr(cls, "CL:0000907",
            PermissibleValue(
                text="CL:0000907",
                description="""CD8-positive, alpha-beta memory T cell with the phenotype CCR7-positive, CD127-positive, CD45RA-negative, CD45RO-positive, and CD25-negative.""",
                meaning=CL["0000907"]))
        setattr(cls, "CL:1001578",
            PermissibleValue(
                text="CL:1001578",
                description="Squamous cell of vaginal epithelium.",
                meaning=CL["1001578"]))
        setattr(cls, "CL:0000850",
            PermissibleValue(
                text="CL:0000850",
                description="A neuron that releases serotonin as a neurotransmitter.",
                meaning=CL["0000850"]))
        setattr(cls, "CL:0001054",
            PermissibleValue(
                text="CL:0001054",
                description="""A monocyte that expresses CD14 and is negative for the lineage markers CD3, CD19, and CD20.""",
                meaning=CL["0001054"]))
        setattr(cls, "CL:0008015",
            PermissibleValue(
                text="CL:0008015",
                description="A motor neuron that is capable of directly inhibiting muscle contraction.",
                meaning=CL["0008015"]))
        setattr(cls, "CL:4033049",
            PermissibleValue(
                text="CL:4033049",
                description="A taste receptor cell that is part of a taste bud of a tongue.",
                meaning=CL["4033049"]))
        setattr(cls, "CL:0000788",
            PermissibleValue(
                text="CL:0000788",
                description="""A naive B cell is a mature B cell that has the phenotype surface IgD-positive, surface IgM-positive, CD20-positive, CD27-negative and that has not yet been activated by antigen in the periphery.""",
                meaning=CL["0000788"]))
        setattr(cls, "CL:0002239",
            PermissibleValue(
                text="CL:0002239",
                description="A primordial cell from which an oocyte (ovum) ultimately is developed.",
                meaning=CL["0002239"]))
        setattr(cls, "CL:0000513",
            PermissibleValue(
                text="CL:0000513",
                description="A precursor cell destined to differentiate into cardiac muscle cell.",
                meaning=CL["0000513"]))
        setattr(cls, "CL:0000592",
            PermissibleValue(
                text="CL:0000592",
                description="""A large, progesterone secreting cell in the corpus luteum that develops from the granulosa cells.""",
                meaning=CL["0000592"]))
        setattr(cls, "CL:4023129",
            PermissibleValue(
                text="CL:4023129",
                description="A retinal cell that is immature or undifferentiated.",
                meaning=CL["4023129"]))
        setattr(cls, "CL:4023019",
            PermissibleValue(
                text="CL:4023019",
                description="""A VIP GABAergic cortical interneuron that expresses cck. L5/6 cck cells have soma found mainly in L5 and L6 and have large axonal arborization.""",
                meaning=CL["4023019"]))
        setattr(cls, "CL:0000404",
            PermissibleValue(
                text="CL:0000404",
                description="A cell that initiates an electrical signal and passes that signal to another cell.",
                meaning=CL["0000404"]))
        setattr(cls, "CL:0002545",
            PermissibleValue(
                text="CL:0002545",
                description="An endothelial cell that is part of the thoracic endothelium.",
                meaning=CL["0002545"]))
        setattr(cls, "CL:0007023",
            PermissibleValue(
                text="CL:0007023",
                description="Epidermal cell rich in mitochondria. In amphibians, appears during metamorphosis.",
                meaning=CL["0007023"]))
        setattr(cls, "CL:0000200",
            PermissibleValue(
                text="CL:0000200",
                description="""Any neuron that is capable of some detection of mechanical stimulus involved in sensory perception of touch.""",
                meaning=CL["0000200"]))
        setattr(cls, "CL:4070014",
            PermissibleValue(
                text="CL:4070014",
                description="A motor neuron that controls pyloric filter movements; innervates the pyloric muscle.",
                meaning=CL["4070014"]))
        setattr(cls, "CL:0001074",
            PermissibleValue(
                text="CL:0001074",
                description="""An innate lymphoid cell precursor in the human with the phenotype CD34-positive, CD56-positive, CD117-positive.Thie cell type may include precusors to NK cells and ILC3 cells.""",
                meaning=CL["0001074"]))
        setattr(cls, "CL:4052047",
            PermissibleValue(
                text="CL:4052047",
                description="""A luteal cell that is part of the older, regressing corpus luteum. This cell exhibits increased expression of genes involved in progesterone metabolism - Akr1c18 in mice (Lan et al., 2024), cell cycle arrest, and apoptosis. A late luteal cell contributes to corpus luteum regression and eventual clearance from the ovary through luteolysis.""",
                meaning=CL["4052047"]))
        setattr(cls, "CL:0000843",
            PermissibleValue(
                text="CL:0000843",
                description="""A resting mature B cell that has the phenotype IgM-positive, IgD-positive, CD23-positive and CD21-positive, and found in the B cell follicles of the white pulp of the spleen or the corticol areas of the peripheral lymph nodes. This cell type is also described as being CD19-positive, B220-positive, AA4-negative, CD43-negative, and CD5-negative.""",
                meaning=CL["0000843"]))
        setattr(cls, "CL:2000076",
            PermissibleValue(
                text="CL:2000076",
                description="Any vein endothelial cell that is part of a hindlimb stylopod.",
                meaning=CL["2000076"]))
        setattr(cls, "CL:0000910",
            PermissibleValue(
                text="CL:0000910",
                description="""A mature T cell that differentiated and acquired cytotoxic function with the phenotype perforin-positive and granzyme-B positive.""",
                meaning=CL["0000910"]))
        setattr(cls, "CL:0002524",
            PermissibleValue(
                text="CL:0002524",
                description="""A disseminated nephrocyte is a nephrocyte that filters hemolymph and is found at scattered locations in the fat body or other tissues.""",
                meaning=CL["0002524"]))
        setattr(cls, "CL:0000715",
            PermissibleValue(
                text="CL:0000715",
                description="A crystal cell that derives from the embryonic head mesoderm.",
                meaning=CL["0000715"]))
        setattr(cls, "CL:0000875",
            PermissibleValue(
                text="CL:0000875",
                description="""A type of monocyte characterized by low expression of CCR2, low responsiveness to monocyte chemoattractant CCL2/MCP1, low phagocytic activity, and decrease size relative to classical monocytes, but increased co-stimulatory activity. May also play a role in tissue repair.""",
                meaning=CL["0000875"]))
        setattr(cls, "CL:0002332",
            PermissibleValue(
                text="CL:0002332",
                description="""A multi-ciliated epithelial cell located in the bronchus epithelium, characterized by a columnar shape and motile cilia on its apical surface.""",
                meaning=CL["0002332"]))
        setattr(cls, "CL:0009110",
            PermissibleValue(
                text="CL:0009110",
                description="A lymphatic endothelial cell located in the ceiling part of a lymph node medulla.",
                meaning=CL["0009110"]))
        setattr(cls, "CL:0002485",
            PermissibleValue(
                text="CL:0002485",
                description="""A melanocyte of the retina. This cell type is distinct from pigmented retinal epithelium.""",
                meaning=CL["0002485"]))
        setattr(cls, "CL:1001135",
            PermissibleValue(
                text="CL:1001135",
                description="Any kidney cortex artery cell that is part of some kidney arcuate artery.",
                meaning=CL["1001135"]))
        setattr(cls, "CL:0002467",
            PermissibleValue(
                text="CL:0002467",
                description="A myeloid suppressor cell that is Gr1-high and CD11c-negative.",
                meaning=CL["0002467"]))
        setattr(cls, "CL:0009076",
            PermissibleValue(
                text="CL:0009076",
                description="A thymic medullary epithelial cell that expresses neuroendocrine biomarkers.",
                meaning=CL["0009076"]))
        setattr(cls, "CL:0004161",
            PermissibleValue(
                text="CL:0004161",
                description="""A cone whose sensitivity measurements have an average spectral peak of 510 nm. These cones are described in rat.""",
                meaning=CL["0004161"]))
        setattr(cls, "CL:0000380",
            PermissibleValue(
                text="CL:0000380",
                description="""The support cell that makes the thecogen dendritic cap - a cuticle-like matrix around the tip of the eo-dendrite and which encloses the soma of the eo-neuron.""",
                meaning=CL["0000380"]))
        setattr(cls, "CL:0000301",
            PermissibleValue(
                text="CL:0000301",
                description="""A primordial germ cell of insects. Such cells form at the posterior pole of the early embryo.""",
                meaning=CL["0000301"]))
        setattr(cls, "CL:4030012",
            PermissibleValue(
                text="CL:4030012",
                description="""Epithelial cell of the descending thin limb of the short loop (cortical) nephron limited to the outer medulla (mainly inner strip). It is known in some mammalian species that the short descending limb of the loop of Henle selectively expresses the serine protease Corin, the homeobox TF Uncx, and the urea channel Slc14a2.""",
                meaning=CL["4030012"]))
        setattr(cls, "CL:1000348",
            PermissibleValue(
                text="CL:1000348",
                description="A basal cell that is part of the epithelium of trachea.",
                meaning=CL["1000348"]))
        setattr(cls, "CL:0000441",
            PermissibleValue(
                text="CL:0000441",
                description="""A stem cell that gives rise to the follicle cells that surround the oocyte in female arthropods.""",
                meaning=CL["0000441"]))
        setattr(cls, "CL:4023118",
            PermissibleValue(
                text="CL:4023118",
                description="""A sst GABAergic interneuron does not have Martinotti morphology with a soma found in L5/6 of the cerebral cortex.""",
                meaning=CL["4023118"]))
        setattr(cls, "CL:4023053",
            PermissibleValue(
                text="CL:4023053",
                description="A Betz cell that syanpses with spinal interneurons.",
                meaning=CL["4023053"]))
        setattr(cls, "CL:0002393",
            PermissibleValue(
                text="CL:0002393",
                description="A monocyte that has characteristics of both patrolling and inflammatory monocytes.",
                meaning=CL["0002393"]))
        setattr(cls, "CL:0010015",
            PermissibleValue(
                text="CL:0010015",
                description="""A highly specialized cell type exclusive to and forming neuroepithelium of the Saccus vasculosus, covering the caudal diverticulum of the infundibular recess.""",
                meaning=CL["0010015"]))
        setattr(cls, "CL:0002454",
            PermissibleValue(
                text="CL:0002454",
                description="""CD4-negative, CD8-alpha-negative, CD11b-positive dendritic cell is a conventional dendritic cell that is CD11b-positive, CD4-negative, CD8-alpha-negative and is CD205-positive.""",
                meaning=CL["0002454"]))
        setattr(cls, "CL:4052038",
            PermissibleValue(
                text="CL:4052038",
                description="""A tuft cell that is part of the nasal cavity respiratory epithelium. Acting as a chemosensor, it detects bitter taste ligands and bacterial signals via taste receptors, maintaining epithelial-microbial homeostasis by stimulating antimicrobial peptide secretion from adjacent epithelial cells. This cell is a major source of IL-25, promoting type 2 immune responses and potentially contributing to chronic rhinosinusitis (O'Leary et al., 2019).""",
                meaning=CL["4052038"]))
        setattr(cls, "CL:1001596",
            PermissibleValue(
                text="CL:1001596",
                description="""Glandular cell of salivary gland. Example: Serous cells, mucous cells, cuboidal epithelial cells of the intercalated ducts, simple cuboidal epithelium of the striated ducts, epithelial cells of excretory ducts.""",
                meaning=CL["1001596"]))
        setattr(cls, "CL:1000357",
            PermissibleValue(
                text="CL:1000357",
                description="A M cell that is part of the epithelium proper of jejunum.",
                meaning=CL["1000357"]))
        setattr(cls, "CL:0002133",
            PermissibleValue(
                text="CL:0002133",
                description="A stromal cell of the ovarian cortex.",
                meaning=CL["0002133"]))
        setattr(cls, "CL:0007005",
            PermissibleValue(
                text="CL:0007005",
                description="Cell that is part of the notochord.",
                meaning=CL["0007005"]))
        setattr(cls, "CL:0000837",
            PermissibleValue(
                text="CL:0000837",
                description="""A hematopoietic multipotent progenitor cell is multipotent, but not capable of long-term self-renewal. These cells are characterized as lacking lineage cell surface markers and being CD34-positive in both mice and humans.""",
                meaning=CL["0000837"]))
        setattr(cls, "CL:0002304",
            PermissibleValue(
                text="CL:0002304",
                description="""A cell that is part of non-pigmented ciliary epithelium. This cell type participates in aqueous humor formation by releasing solute, principally sodium and chloride ions received from pigmented epithelial cells via gap junctions, into the aqueous humor of the eye.""",
                meaning=CL["0002304"]))
        setattr(cls, "CL:0002395",
            PermissibleValue(
                text="CL:0002395",
                description="""A resident monocyte that is Gr-1 high, CD43-negative, CX3CR1-negative, CD115-positive, and B220-negative.""",
                meaning=CL["0002395"]))
        setattr(cls, "CL:0000784",
            PermissibleValue(
                text="CL:0000784",
                description="""A dendritic cell type of distinct morphology, localization, and surface marker expression (CD123-positive) from other dendritic cell types and associated with early stage immune responses, particularly the release of physiologically abundant amounts of type I interferons in response to infection.""",
                meaning=CL["0000784"]))
        setattr(cls, "CL:0002215",
            PermissibleValue(
                text="CL:0002215",
                description="""A type II muscle cell that contains a low content of myoglobin, relatively few mitochondria, relatively few blood capillaries and large amounts of glycogen. Type II B fibres are white, geared to generate ATP by anaerobic metabolic processes, not able to supply skeletal muscle fibres continuously with sufficient ATP, fatigue easily, split ATP at a fast rate and have a fast contraction velocity.""",
                meaning=CL["0002215"]))
        setattr(cls, "CL:0002200",
            PermissibleValue(
                text="CL:0002200",
                description="An oncocyte located in the thyroid.",
                meaning=CL["0002200"]))
        setattr(cls, "CL:0017010",
            PermissibleValue(
                text="CL:0017010",
                description="A hillock cell that is part of the urethra.",
                meaning=CL["0017010"]))
        setattr(cls, "CL:0000152",
            PermissibleValue(
                text="CL:0000152",
                description="A cell of an exocrine gland; i.e. a gland that discharges its secretion via a duct.",
                meaning=CL["0000152"]))
        setattr(cls, "CL:1001213",
            PermissibleValue(
                text="CL:1001213",
                description="Any endothelial cell that is part of some kidney arcuate artery.",
                meaning=CL["1001213"]))
        setattr(cls, "CL:0000117",
            PermissibleValue(
                text="CL:0000117",
                meaning=CL["0000117"]))
        setattr(cls, "CL:4042010",
            PermissibleValue(
                text="CL:4042010",
                description="""An interlaminar astrocyte whose soma is part of the first layer of a neocortex and is in contact with a pia surface.""",
                meaning=CL["4042010"]))
        setattr(cls, "CL:0009014",
            PermissibleValue(
                text="CL:0009014",
                description="""A lymphocyte that is part of a Peyer's patch. These cells have a major role in driving the immune response to antigens sampled from the intestinal lumen, and in regulating the formation of follicle-associated epithelium and M cells in Peyer's patches by converting intestitial enterocytes into M cells.""",
                meaning=CL["0009014"]))
        setattr(cls, "CL:0003007",
            PermissibleValue(
                text="CL:0003007",
                description="""A G4 retinal ganglion cell that has post sympatic terminals in sublaminar layers S2 and S3 and is depolarized by decreased illumination of their receptive field center""",
                meaning=CL["0003007"]))
        setattr(cls, "CL:0000931",
            PermissibleValue(
                text="CL:0000931",
                description="""A type II NK T cell that has been recently activated, secretes interferon-gamma and interleukin-4, and has the phenotype CD69-positive and downregulated NK markers.""",
                meaning=CL["0000931"]))
        setattr(cls, "CL:0009040",
            PermissibleValue(
                text="CL:0009040",
                description="A stromal cell found in the lamina propria of the colon.",
                meaning=CL["0009040"]))
        setattr(cls, "CL:0000868",
            PermissibleValue(
                text="CL:0000868",
                description="A secondary lymphoid organ macrophage found in a lymph node. This cell is CD169-high.",
                meaning=CL["0000868"]))
        setattr(cls, "CL:0000390",
            PermissibleValue(
                text="CL:0000390",
                meaning=CL["0000390"]))
        setattr(cls, "CL:1000425",
            PermissibleValue(
                text="CL:1000425",
                description="A chromaffin cell that is part of the paraganglion.",
                meaning=CL["1000425"]))
        setattr(cls, "CL:2000058",
            PermissibleValue(
                text="CL:2000058",
                description="Any osteoblast that is part of a skull.",
                meaning=CL["2000058"]))
        setattr(cls, "CL:4023026",
            PermissibleValue(
                text="CL:4023026",
                description="""A medium spiny neuron that expresses dopamine type 1 receptors and projects to the globus pallidus internus or the substantia nigra pars reticulata.""",
                meaning=CL["4023026"]))
        setattr(cls, "CL:0011021",
            PermissibleValue(
                text="CL:0011021",
                description="A fibroblast that is part of upper back skin.",
                meaning=CL["0011021"]))
        setattr(cls, "CL:4042036",
            PermissibleValue(
                text="CL:4042036",
                description="""A neuron of the central nervous system with its soma primarily located in the lateral hypothalamic area and surrounding regions, including the zona incerta. This neuron type expresses melanin-concentrating hormone and is involved in regulating various physiological processes, including sleep, feeding behavior, and energy homeostasis.""",
                meaning=CL["4042036"]))
        setattr(cls, "CL:1000382",
            PermissibleValue(
                text="CL:1000382",
                description="A type II vestibular sensory cell that is part of the stato-acoustic epithelium.",
                meaning=CL["1000382"]))
        setattr(cls, "CL:4023002",
            PermissibleValue(
                text="CL:4023002",
                description="A beta motor neuron that innervates the nuclear bag fibers of muscle spindles.",
                meaning=CL["4023002"]))
        setattr(cls, "CL:2000012",
            PermissibleValue(
                text="CL:2000012",
                description="Any skin fibroblast that is part of a pedal digit skin.",
                meaning=CL["2000012"]))
        setattr(cls, "CL:0000960",
            PermissibleValue(
                text="CL:0000960",
                description="""A transitional stage B cell that expresses surface IgM and IgD, and CD62L. This cell type appears to be an anergic B cell that does not proliferate upon BCR signaling, is found in the spleen and lymph nodes, and has the phenotype surface IgM-positive, surface IgD-positive, CD21-positive, CD23-positive, CD62L-positive, and CD93-positive. This cell type has also been described as IgM-low, CD19-positive, B220-positive, AA4-positive, and CD23-positive (i.e. this cell-type is distinguished from T2 cells by surface expression of IgM).""",
                meaning=CL["0000960"]))
        setattr(cls, "CL:2000059",
            PermissibleValue(
                text="CL:2000059",
                description="Any microvascular endothelial cell that is part of a prostate gland.",
                meaning=CL["2000059"]))
        setattr(cls, "CL:0002297",
            PermissibleValue(
                text="CL:0002297",
                description="""A thymic epithelial cell with moderate nuclear and cytoplasmic electron-density. Scattered in the cortex, this cell type is predominant in the mid and deep cortex.""",
                meaning=CL["0002297"]))
        setattr(cls, "CL:0000575",
            PermissibleValue(
                text="CL:0000575",
                description="An epithelial cell of the cornea.",
                meaning=CL["0000575"]))
        setattr(cls, "CL:0000923",
            PermissibleValue(
                text="CL:0000923",
                description="A type I NK T cell that has the phenotype CD4-positive.",
                meaning=CL["0000923"]))
        setattr(cls, "CL:0000482",
            PermissibleValue(
                text="CL:0000482",
                description="An endocrine cell that secretes juvenile hormone.",
                meaning=CL["0000482"]))
        setattr(cls, "CL:0002364",
            PermissibleValue(
                text="CL:0002364",
                description="""An epithelial cell of the cortical portion of the thymus. Epithelial cells in this region are required for positive selection of CD8-positive T cells.""",
                meaning=CL["0002364"]))
        setattr(cls, "CL:0007009",
            PermissibleValue(
                text="CL:0007009",
                description="""Skeletogenic cell that has the potential to develop into a chondroblast; and arises from neural crest, meseosdermal and notochordal and connective tissue cells.""",
                meaning=CL["0007009"]))
        setattr(cls, "CL:0000828",
            PermissibleValue(
                text="CL:0000828",
                description="""A progenitor cell of the thrombocyte, a nucleated blood cell involved in coagulation typically seen in birds and other non-mammalian vertebrates.""",
                meaning=CL["0000828"]))
        setattr(cls, "CL:0002114",
            PermissibleValue(
                text="CL:0002114",
                description="""A CD38-positive unswitched memory B cell is an unswitched memory B cell that has the phenotype CD38-positive, IgD-positive, CD138-negative, and IgG-negative.""",
                meaning=CL["0002114"]))
        setattr(cls, "CL:0000924",
            PermissibleValue(
                text="CL:0000924",
                description="A type I NK T cell that has the phenotype CD4-negative and CD8-negative.",
                meaning=CL["0000924"]))
        setattr(cls, "CL:1000290",
            PermissibleValue(
                text="CL:1000290",
                description="A muscle cell that is part of the middle internodal tract.",
                meaning=CL["1000290"]))
        setattr(cls, "CL:4052053",
            PermissibleValue(
                text="CL:4052053",
                description="""A uterine natural killer subset found in the endometrial lining during the non-pregnant state (Garcia-Alonso et al., 2021) and in the decidua during pregnancy (Vento-Tormo et al., 2018), becoming the dominant uNK subset late in pregnancy. It expresses the uterine resident marker CD49a and is distinguished from uNK1 and uNK2 by CD160 (Marečková et al., 2024) and CD103 expression, the absence of CD39, and low KIR levels (Whettlock et al., 2022). Resembling intraepithelial ILC1 cells, uNK3 primarily supports uterine immune defense (Huhn et al., 2020) and indirectly influences trophoblast behavior through chemokine secretion, such as CCL5 (Vento-Tormo et al., 2018).""",
                meaning=CL["4052053"]))
        setattr(cls, "CL:0002314",
            PermissibleValue(
                text="CL:0002314",
                description="""An auditory epithelial support cell located in the vestibular epithelium that has many hallmarks of glial cells. This cell type express glial markers such as vimentin, S100, glutamate-aspartate transporter, low affinity neurotrophin receptor p75, glial fibrillary acidic protein, and proteolipid protein.""",
                meaning=CL["0002314"]))
        setattr(cls, "CL:1000287",
            PermissibleValue(
                text="CL:1000287",
                description="A muscle cell that is part of the anterior internodal tract.",
                meaning=CL["1000287"]))
        setattr(cls, "CL:2000075",
            PermissibleValue(
                text="CL:2000075",
                description="Any endodermal cell that is part of a anterior visceral endoderm.",
                meaning=CL["2000075"]))
        setattr(cls, "CL:0002077",
            PermissibleValue(
                text="CL:0002077",
                description="An epithelial cell derived from ectoderm.",
                meaning=CL["0002077"]))
        setattr(cls, "CL:4028002",
            PermissibleValue(
                text="CL:4028002",
                description="""An alveolar capillary endothelial cell that is located distally to alveolar capillary type 2 endothelial cells.""",
                meaning=CL["4028002"]))
        setattr(cls, "CL:0000187",
            PermissibleValue(
                text="CL:0000187",
                description="""A mature contractile cell, commonly known as a myocyte. This cell has as part of its cytoplasm myofibrils organized in various patterns.""",
                meaning=CL["0000187"]))
        setattr(cls, "CL:4040000",
            PermissibleValue(
                text="CL:4040000",
                description="""A glial precursor cell that generates oligodendrocytes and type-1 and type-2 astrocytes. It has been shown in some mammals that this cell type may express A2B5, nestin, FGFR-1, FGFR-2, FGFR-3, PLP, and DM-20 antigens. Unlike oligodendrocyte precursor cell, it does not initially express PDGFR-alpha and can differentiate into both type-1 and type-2 astrocytes.""",
                meaning=CL["4040000"]))
        setattr(cls, "CL:1000379",
            PermissibleValue(
                text="CL:1000379",
                description="""A type I vestibular sensory cell that is part of the epithelium of macula of utricle of membranous labyrinth.""",
                meaning=CL["1000379"]))
        setattr(cls, "CL:0002360",
            PermissibleValue(
                text="CL:0002360",
                description="""A hematopoietic stem cell from the aorta-gonad-mesonephros region of the developing embryo. First seen at E10.5 in mouse embryos. May give rise to fetal liver HSC.""",
                meaning=CL["0002360"]))
        setattr(cls, "CL:4052007",
            PermissibleValue(
                text="CL:4052007",
                description="""A fibroblast located adjacent to the intestinal epithelium in both the small intestine and colon, specifically around the crypts. This cell is characterized by the expression of  PDGFRα and various collagen isoforms, including COL4A5 and COL4A6. It secretes signalling molecules like TGF-β, Wnt ligands, and BMPs, which are crucial for epithelial homeostasis, intestinal stem cell support, and basement membrane formation.""",
                meaning=CL["4052007"]))
        setattr(cls, "CL:0000783",
            PermissibleValue(
                text="CL:0000783",
                description="A phagocyte formed by the fusion of mononuclear phagocytes.",
                meaning=CL["0000783"]))
        setattr(cls, "CL:0004117",
            PermissibleValue(
                text="CL:0004117",
                description="A monostratified retinal ganglion cell with large soma and large dendritic field.",
                meaning=CL["0004117"]))
        setattr(cls, "CL:0004213",
            PermissibleValue(
                text="CL:0004213",
                description="A type of type 3 cone bipolar cell with distinctive curly dendrites.",
                meaning=CL["0004213"]))
        setattr(cls, "CL:1000699",
            PermissibleValue(
                text="CL:1000699",
                description="A resident-dendritic cell that is part of a kidney.",
                meaning=CL["1000699"]))
        setattr(cls, "CL:0004251",
            PermissibleValue(
                text="CL:0004251",
                description="An amicrine that has a narrow dendritic field.",
                meaning=CL["0004251"]))
        setattr(cls, "CL:0002505",
            PermissibleValue(
                text="CL:0002505",
                description="""A CD11b-positive dendritic cell that is CD11b-high, CD45-positive, MHC-II-positive and CD103-negative.""",
                meaning=CL["0002505"]))
        setattr(cls, "CL:0001045",
            PermissibleValue(
                text="CL:0001045",
                description="""A naive regulatory T cell with the phenotype CD4-positive, CD25-positive, CD127lo, CCR4-positive, and CD45RO-negative.""",
                meaning=CL["0001045"]))
        setattr(cls, "CL:0000756",
            PermissibleValue(
                text="CL:0000756",
                description="""An OFF-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the outer half of the inner plexiform layer. The cell has a diffuse axon terminal with varicosities in sublaminae 1 and 2 of the inner plexiform layer.""",
                meaning=CL["0000756"]))
        setattr(cls, "CL:4030038",
            PermissibleValue(
                text="CL:4030038",
                description="""A CD24-positive, CD-133-positive, vimentin-positive cell found scattered throughout a renal proximal tubule and that may participate in tubular regeneration. Compared to other proximal tubular cell types, this cell contains less cytoplasm, fewer mitochondria and no brush border.""",
                meaning=CL["4030038"]))
        setattr(cls, "CL:0002272",
            PermissibleValue(
                text="CL:0002272",
                description="""A cell that secretes motilin, a gastric hormone that at low pH inhibits gastric motor activity, whereas at high pH has a stimulating effect.""",
                meaning=CL["0002272"]))
        setattr(cls, "CL:2000073",
            PermissibleValue(
                text="CL:2000073",
                description="Any migratory neural crest cell that is part of a cardiac neural crest.",
                meaning=CL["2000073"]))
        setattr(cls, "CL:1001437",
            PermissibleValue(
                text="CL:1001437",
                description="The subcutaneous mechanoreceptors that innervate vellus hairs.",
                meaning=CL["1001437"]))
        setattr(cls, "CL:0002418",
            PermissibleValue(
                text="CL:0002418",
                description="""A pluripotent cell in the yolk sac that can give rise to mesenchymal cells including erythrocytes and endothelial cells.""",
                meaning=CL["0002418"]))
        setattr(cls, "CL:4023021",
            PermissibleValue(
                text="CL:4023021",
                description="""A gamma motor neuron that innervates static nuclear bag fibers (bag2 fibers) and increases their firing, in response to an increase in the magnitude of change in length, and controls the static sensitivity of the stretch reflex.""",
                meaning=CL["4023021"]))
        setattr(cls, "CL:0000554",
            PermissibleValue(
                text="CL:0000554",
                description="A peptide hormone secreting cell that secretes gastrin stimulating hormone.",
                meaning=CL["0000554"]))
        setattr(cls, "CL:4030027",
            PermissibleValue(
                text="CL:4030027",
                description="An amacrine cell that uses GABA as a neurotransmitter.",
                meaning=CL["4030027"]))
        setattr(cls, "CL:0000524",
            PermissibleValue(
                text="CL:0000524",
                description="A cell, usually of bacteria or yeast, which has partially lost its cell wall.",
                meaning=CL["0000524"]))
        setattr(cls, "CL:0000516",
            PermissibleValue(
                text="CL:0000516",
                description="A non-neuronal cell that surrounds the neuronal cell bodies of the ganglia.",
                meaning=CL["0000516"]))
        setattr(cls, "CL:0002353",
            PermissibleValue(
                text="CL:0002353",
                description="""A hematopoietic stem cell that resides in the fetal liver. In mice, this cell type is first observed at E10.5. This cell type is MHC-positive, HSA-positive, AA4.1-positive, CD45-positive, Sca-1 positive, CD150-positive, CD48-negative and CD244-negative.""",
                meaning=CL["0002353"]))
        setattr(cls, "CL:0001046",
            PermissibleValue(
                text="CL:0001046",
                description="""A memory regulatory T cell with phenotype CD4-positive, CD25-positive, CD127lo, CCR4-positive, and CD45RO-positive.""",
                meaning=CL["0001046"]))
        setattr(cls, "CL:4033007",
            PermissibleValue(
                text="CL:4033007",
                description="A(n) brush cell that is part of a(n) epithelium of lobar bronchus.",
                meaning=CL["4033007"]))
        setattr(cls, "CL:0009039",
            PermissibleValue(
                text="CL:0009039",
                description="A goblet cell that is located in the colon.",
                meaning=CL["0009039"]))
        setattr(cls, "CL:0002119",
            PermissibleValue(
                text="CL:0002119",
                description="""A CD38-positive IgG-negative memory B cell is an IgG-negative class switched memory B cell that lacks IgG on the cell surface with the phenotype CD38-positive and IgG-negative.""",
                meaning=CL["0002119"]))
        setattr(cls, "CL:0005009",
            PermissibleValue(
                text="CL:0005009",
                description="""A cuboidal epithelial cell of the kidney which regulates sodium and potassium balance. The activity of sodium and potassium channels on the apical membrane of the cell is regulated by aldosterone and vasopressin. In mammals this cell type is located in the renal collecting duct system.""",
                meaning=CL["0005009"]))
        setattr(cls, "CL:4042027",
            PermissibleValue(
                text="CL:4042027",
                description="""A GABAergic interneuron that has its soma in the posterior section of the substantia nigra pars reticulata. This GABAergic interneuron is characterised by the expression of the transcription factors Pax5, Ctip2 and Pou6f2 and it develops from the ventrolateral r1 neuroepithelium expresing NKX61.""",
                meaning=CL["4042027"]))
        setattr(cls, "CL:2000049",
            PermissibleValue(
                text="CL:2000049",
                description="Any pyramidal cell that is part of a primary motor cortex.",
                meaning=CL["2000049"]))
        setattr(cls, "CL:0000799",
            PermissibleValue(
                text="CL:0000799",
                description="A gamma-delta T cell that has an immature phenotype.",
                meaning=CL["0000799"]))
        setattr(cls, "CL:4033010",
            PermissibleValue(
                text="CL:4033010",
                description="A(n) neuroendocrine cell that is part of a(n) epithelium of lobar bronchus.",
                meaning=CL["4033010"]))
        setattr(cls, "CL:0007007",
            PermissibleValue(
                text="CL:0007007",
                description="""Notochordal cell that is part of the outer epithelium of the notochord and surrounds the vacuolated notochord cells.""",
                meaning=CL["0007007"]))
        setattr(cls, "CL:0000541",
            PermissibleValue(
                text="CL:0000541",
                description="A cell that originates from the neural crest and differentiates into a pigment cell.",
                meaning=CL["0000541"]))
        setattr(cls, "CL:0000564",
            PermissibleValue(
                text="CL:0000564",
                description="""A promyelocyte committed to the neutrophil lineage. This cell type is GATA-1-positive, C/EBPa-positive, AML-1-positive, MPO-positive, has low expression of PU.1 transcription factor and lacks lactotransferrin expression.""",
                meaning=CL["0000564"]))
        setattr(cls, "CL:0000497",
            PermissibleValue(
                text="CL:0000497",
                description="A photoreceptor cell that is sensitive to red light.",
                meaning=CL["0000497"]))
        setattr(cls, "CL:0003049",
            PermissibleValue(
                text="CL:0003049",
                description="""A cone cell that detects medium wavelength light. Exact peak of spectra detected differs between species. In humans, spectra peaks at 534-545 nm.""",
                meaning=CL["0003049"]))
        setattr(cls, "CL:0000556",
            PermissibleValue(
                text="CL:0000556",
                description="""A large hematopoietic cell (50 to 100 micron) with a lobated nucleus. Once mature, this cell undergoes multiple rounds of endomitosis and cytoplasmic restructuring to allow platelet formation and release.""",
                meaning=CL["0000556"]))
        setattr(cls, "CL:0000876",
            PermissibleValue(
                text="CL:0000876",
                description="""A splenic macrophage found in the white pulp of the spleen. Markers include F4/80-negative, CD68-positive, and macrosialin-positive.""",
                meaning=CL["0000876"]))
        setattr(cls, "CL:0002399",
            PermissibleValue(
                text="CL:0002399",
                description="A myeloid dendritic cell that is CD1c-positive.",
                meaning=CL["0002399"]))
        setattr(cls, "CL:4023048",
            PermissibleValue(
                text="CL:4023048",
                description="""An intratelencephalic-projecting glutamatergic with a soma located in upper L5 of the primary motor cortex. These cells have thin untufted apical dendrites.""",
                meaning=CL["4023048"]))
        setattr(cls, "CL:0009046",
            PermissibleValue(
                text="CL:0009046",
                description="A T cell found in the lymph node medullary sinus.",
                meaning=CL["0009046"]))
        setattr(cls, "CL:1000298",
            PermissibleValue(
                text="CL:1000298",
                description="A mesothelial cell that is part of the dura mater.",
                meaning=CL["1000298"]))
        setattr(cls, "CL:0008039",
            PermissibleValue(
                text="CL:0008039",
                description="""The motor neurons of vertebrates that directly innervate skeletal muscles. They receive input from upper motor neurons.""",
                meaning=CL["0008039"]))
        setattr(cls, "CL:0000387",
            PermissibleValue(
                text="CL:0000387",
                description="A blood cell of the circulatory system of arthropods.",
                meaning=CL["0000387"]))
        setattr(cls, "CL:1001609",
            PermissibleValue(
                text="CL:1001609",
                description="Fibroblast from muscle organ.",
                meaning=CL["1001609"]))
        setattr(cls, "CL:1000601",
            PermissibleValue(
                text="CL:1000601",
                description="Any cell that is part of some ureter.",
                meaning=CL["1000601"]))
        setattr(cls, "CL:0000140",
            PermissibleValue(
                text="CL:0000140",
                description="""Skeletogenic cell that secretes dentine matrix, is derived from odontogenic papilla. Embedded in dentine tissue, and is the transformation of a non-terminally differentiated odontoblast cell.""",
                meaning=CL["0000140"]))
        setattr(cls, "CL:0000505",
            PermissibleValue(
                text="CL:0000505",
                description="A peptide hormone secreting cell that secretes substance P.",
                meaning=CL["0000505"]))
        setattr(cls, "CL:0002434",
            PermissibleValue(
                text="CL:0002434",
                description="""A CD8-positive, CD4-negative thymocyte that is CD24-positive and expresses high levels of the alpha-beta T cell receptor.""",
                meaning=CL["0002434"]))
        setattr(cls, "CL:0000531",
            PermissibleValue(
                text="CL:0000531",
                description="A primary neuron (sensu Teleostei) that has a sensory function.",
                meaning=CL["0000531"]))
        setattr(cls, "CL:1000278",
            PermissibleValue(
                text="CL:1000278",
                description="A smooth muscle cell that is part of the ileum.",
                meaning=CL["1000278"]))
        setattr(cls, "CL:1001586",
            PermissibleValue(
                text="CL:1001586",
                description="""Glandular cell of mammary epithelium. Example: glandular cells of large and intermediate ducts, glandular cells in terminal ducts.""",
                meaning=CL["1001586"]))
        setattr(cls, "CL:0001008",
            PermissibleValue(
                text="CL:0001008",
                description="""A hematopoietic stem cell that has plasma membrane part Kit-positive, SCA-1-positive, CD150-positive and CD34-negative.""",
                meaning=CL["0001008"]))
        setattr(cls, "CL:0002166",
            PermissibleValue(
                text="CL:0002166",
                description="""An epithelial cell that remains from the disintegration of the epithelial root sheath involved in the development of teeth.""",
                meaning=CL["0002166"]))
        setattr(cls, "CL:0000216",
            PermissibleValue(
                text="CL:0000216",
                description="""A supporting cell projecting inward from the basement membrane of seminiferous tubules. They surround and nourish the developing male germ cells and secrete androgen binding protein. Their tight junctions with the spermatogonia and spermatocytes provide a blood-testis barrier.""",
                meaning=CL["0000216"]))
        setattr(cls, "CL:0002391",
            PermissibleValue(
                text="CL:0002391",
                description="A blastoconidium that has more than one nucleus.",
                meaning=CL["0002391"]))
        setattr(cls, "CL:2000084",
            PermissibleValue(
                text="CL:2000084",
                description="""A goblet cell that is part of the conjunctival epithelium, characterized by apical accumulation of mucin granules (containing MUC5AC in humans; Muc5ac/Muc5b in mice). These gel-forming mucins support tear film stability, ocular lubrication, and pathogen defence. The conjunctival goblet cell forms tight junctions with neighbouring epithelial cells via species-specific claudins (claudin-10 in humans, claudin-2 in mice) and regulates immune homeostasis by facilitating soluble antigen transport to dendritic cells through goblet cell-associated antigen passages (GAPs) (Barbosa et al., 2017). The transcription factor SPDEF is essential for its differentiation.""",
                meaning=CL["2000084"]))
        setattr(cls, "CL:0011012",
            PermissibleValue(
                text="CL:0011012",
                description="""A cell of the neural crest. Neural crest cells are multipotent. Premigratory neural crest cells are found at the neural plate boarder, some of which will undergo ectomesynchymal transition and delamination to form migratory neural crest cells.""",
                meaning=CL["0011012"]))
        setattr(cls, "CL:0009028",
            PermissibleValue(
                text="CL:0009028",
                description="""An intestinal crypt stem cell that is located in the vermiform appendix. These stem cells reside at the bottom of crypts in the appendix and are highly proliferative. They either differentiate into transit amplifying cells or self-renew to form new stem cells.""",
                meaning=CL["0009028"]))
        setattr(cls, "CL:0002196",
            PermissibleValue(
                text="CL:0002196",
                description="""A transient hepatic stem cell observed after liver injury with a high nuclear to cytoplasm ratio that can differentiate into mature hepatocytes and bile duct cells. Arises from more than one tissue.""",
                meaning=CL["0002196"]))
        setattr(cls, "CL:0002072",
            PermissibleValue(
                text="CL:0002072",
                description="""A specialized cardiac myocyte in the sinoatrial and atrioventricular nodes. The cell is slender and fusiform confined to the nodal center, circumferentially arranged around the nodal artery.""",
                meaning=CL["0002072"]))
        setattr(cls, "CL:0002534",
            PermissibleValue(
                text="CL:0002534",
                description="""A mature CD16-positive myeloid dendritic cell is CD80-high, CD83-positive, CD86-high, and MHCII-high.""",
                meaning=CL["0002534"]))
        setattr(cls, "CL:0000820",
            PermissibleValue(
                text="CL:0000820",
                description="A B-1 B cell that has the phenotype CD5-positive.",
                meaning=CL["0000820"]))
        setattr(cls, "CL:0000038",
            PermissibleValue(
                text="CL:0000038",
                description="A progenitor cell committed to the erythroid lineage.",
                meaning=CL["0000038"]))
        setattr(cls, "CL:0009094",
            PermissibleValue(
                text="CL:0009094",
                description="An endothelial cell that is part of a hepatic portal vein.",
                meaning=CL["0009094"]))
        setattr(cls, "CL:4047048",
            PermissibleValue(
                text="CL:4047048",
                description="""An enteric glial cell characterized by a small central soma that extends long, thin, bipolar projections. This cell is primarily located along small nerve fibers within the muscle layers of the gastrointestinal tract and is known for its unbranching processes that closely follow these nerve fibers in the muscularis.""",
                meaning=CL["4047048"]))
        setattr(cls, "CL:4042002",
            PermissibleValue(
                text="CL:4042002",
                description="""A nucleus accumbens shell and olfactory tubercle D1 medium spiny neuron that co-expresses TAC3 and the DRD1 receptor.""",
                meaning=CL["4042002"]))
        setattr(cls, "CL:0000452",
            PermissibleValue(
                text="CL:0000452",
                meaning=CL["0000452"]))
        setattr(cls, "CL:0002376",
            PermissibleValue(
                text="CL:0002376",
                description="""A glial cell that ensheaths multiple small diameter axons in the peripheral nervous system. The non-myelinating Schwann cell is embedded among neurons (axons) with minimal extracellular spaces separating them from nerve cell membranes and has a basal lamina. Cells can survive without an axon present. These cells can de-differentiate into immature Schwann cells.""",
                meaning=CL["0002376"]))
        setattr(cls, "CL:0002495",
            PermissibleValue(
                text="CL:0002495",
                description="""A fetal and neonatal heart cell that undergoes proliferation and is not yet terminally differentiated into a binucleate or a multinucleate cardiac myocyte.""",
                meaning=CL["0002495"]))
        setattr(cls, "CL:0000773",
            PermissibleValue(
                text="CL:0000773",
                description="""A eosinophil precursor in the granulocytic series, being a cell intermediate in development between a eosinophilic myelocyte and a band form eosinophil. The nucleus becomes indented where the indentation is smaller than half the distance to the farthest nuclear margin; chromatin becomes coarse and clumped; specific granules predominate while primary granules are rare. Markers are integrin alpha-M-positive, fucosyltransferase FUT4-positive, low affinity immunoglobulin gamma Fc region receptor III-positive, CD33-positive, CD24-positive and aminopeptidase N-negative.""",
                meaning=CL["0000773"]))
        setattr(cls, "CL:0000393",
            PermissibleValue(
                text="CL:0000393",
                description="A cell whose function is determined by its response to an electric signal.",
                meaning=CL["0000393"]))
        setattr(cls, "CL:1000450",
            PermissibleValue(
                text="CL:1000450",
                description="An epithelial cell that is part of the glomerular capsule.",
                meaning=CL["1000450"]))
        setattr(cls, "CL:1001287",
            PermissibleValue(
                text="CL:1001287",
                description="""Any vasa recta descending limb cell that is part of some outer medulla descending vasa recta.""",
                meaning=CL["1001287"]))
        setattr(cls, "CL:0009056",
            PermissibleValue(
                text="CL:0009056",
                description="A transit amplifying cell that is located in the anorectum.",
                meaning=CL["0009056"]))
        setattr(cls, "CL:0000934",
            PermissibleValue(
                text="CL:0000934",
                description="A CD4-positive, alpha-beta T cell that has cytotoxic function.",
                meaning=CL["0000934"]))
        setattr(cls, "CL:4052020",
            PermissibleValue(
                text="CL:4052020",
                description="""A granzyme K-associated CD8 T cell that resides in the lung, characterized by the expression of granzyme K (GZMK), and tissue residency markers CD103 and CD49a. This cell exhibits cytotoxic potential through its expression of multiple granzymes (GZMA, GZMB, GZMH, GZMM) in addition to GZMK.""",
                meaning=CL["4052020"]))
        setattr(cls, "CL:0000771",
            PermissibleValue(
                text="CL:0000771",
                description="""Any of the immature or mature forms of a granular leukocyte with a nucleus that usually has two lobes connected by one or more slender threads of chromatin, and cytoplasm containing coarse, round granules that are uniform in size and which can be stained by the dye eosin. Eosinophils are CD9-positive, CD191-positive, and CD193-positive.""",
                meaning=CL["0000771"]))
        setattr(cls, "CL:0003046",
            PermissibleValue(
                text="CL:0003046",
                description="""A bistratifed retinal ganglion cell that has small, symmetric dendritic fields that terminate in S2 and S4.""",
                meaning=CL["0003046"]))
        setattr(cls, "CL:4023017",
            PermissibleValue(
                text="CL:4023017",
                description="""A transcriptomically distinct GABAergic neuron located in the cerebral cortex that expresses somatostatin (sst). The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: MGE-derived interneurons', Author Categories: 'CrossArea_subclass', cluster Sst.""",
                meaning=CL["4023017"]))
        setattr(cls, "CL:0002591",
            PermissibleValue(
                text="CL:0002591",
                description="A smooth muscle of the pulmonary artery.",
                meaning=CL["0002591"]))
        setattr(cls, "CL:4070013",
            PermissibleValue(
                text="CL:4070013",
                description="A motor neuron that controls  ventral stomach grooves leading to pyloric filter.",
                meaning=CL["4070013"]))
        setattr(cls, "CL:0002423",
            PermissibleValue(
                text="CL:0002423",
                description="A DN2 thymocyte that is Kit-hi.",
                meaning=CL["0002423"]))
        setattr(cls, "CL:0000697",
            PermissibleValue(
                text="CL:0000697",
                meaning=CL["0000697"]))
        setattr(cls, "CL:0000856",
            PermissibleValue(
                text="CL:0000856",
                description="""Neuromast hair cell is a hair cell that acts as a sensory receptor of the neuromast; it is morphologically polarized as a result of the relative position of the single kinocilium and the clusters of stereocilia on its apical surface.""",
                meaning=CL["0000856"]))
        setattr(cls, "CL:2000057",
            PermissibleValue(
                text="CL:2000057",
                description="Any osteoblast that is part of a femur.",
                meaning=CL["2000057"]))
        setattr(cls, "CL:1000436",
            PermissibleValue(
                text="CL:1000436",
                description="An epithelial cell that is part of the lacrimal sac.",
                meaning=CL["1000436"]))
        setattr(cls, "CL:0000062",
            PermissibleValue(
                text="CL:0000062",
                description="""Skeletogenic cell that secretes osteoid, is capable of producing mineralized (hydroxyapatite) matrix, is located adjacent to or within osteoid tissue, and arises from the transformation of a preosteoblast cell.""",
                meaning=CL["0000062"]))
        setattr(cls, "CL:2000063",
            PermissibleValue(
                text="CL:2000063",
                description="Any fibroblast that is part of a female gonad.",
                meaning=CL["2000063"]))
        setattr(cls, "CL:4052046",
            PermissibleValue(
                text="CL:4052046",
                description="""A luteal cell that is part of the young, developing corpus luteum. This cell promotes progesterone synthesis, marked by high Parm1 expression in mice (Lan et al., 2024). An early luteal cell is associated with steroidogenesis and cell growth, contributing to early corpus luteum function and maturation.""",
                meaning=CL["4052046"]))
        setattr(cls, "CL:4032001",
            PermissibleValue(
                text="CL:4032001",
                description="A GABAergic interneuron located in the cerebral cortex that expresses reelin (rln).",
                meaning=CL["4032001"]))
        setattr(cls, "CL:0000835",
            PermissibleValue(
                text="CL:0000835",
                description="""The most primitive precursor in the granulocytic series, having fine, evenly distributed chromatin, several nucleoli, a high nuclear-to-cytoplasmic ration (5:1-7:1), and a nongranular basophilic cytoplasm. They reside in the bone marrow.""",
                meaning=CL["0000835"]))
        setattr(cls, "CL:4023086",
            PermissibleValue(
                text="CL:4023086",
                description="""A Martinotti neuron that has axons that form a horizontal ramification, making it T-shaped.""",
                meaning=CL["4023086"]))
        setattr(cls, "CL:0002315",
            PermissibleValue(
                text="CL:0002315",
                description="An epithelial supporting cell located in the cochlea.",
                meaning=CL["0002315"]))
        setattr(cls, "CL:0000658",
            PermissibleValue(
                text="CL:0000658",
                description="An epithelial cell that secretes cuticle.",
                meaning=CL["0000658"]))
        setattr(cls, "CL:0000166",
            PermissibleValue(
                text="CL:0000166",
                description="""A cell that stores epinephrine secretory vesicles. During times of stress, the nervous system signals the vesicles to secrete their hormonal content. Their name derives from their ability to stain a brownish color with chromic salts. Characteristically, they are located in the adrenal medulla and paraganglia of the sympathetic nervous system.""",
                meaning=CL["0000166"]))
        setattr(cls, "CL:0000978",
            PermissibleValue(
                text="CL:0000978",
                description="A short lived plasma cell that secretes IgM.",
                meaning=CL["0000978"]))
        setattr(cls, "CL:1000692",
            PermissibleValue(
                text="CL:1000692",
                description="A fibroblast that is part of an interstitial compartment of a kidney.",
                meaning=CL["1000692"]))
        setattr(cls, "CL:0002624",
            PermissibleValue(
                text="CL:0002624",
                description="A paneth cell of the appendix.",
                meaning=CL["0002624"]))
        setattr(cls, "CL:4047037",
            PermissibleValue(
                text="CL:4047037",
                description="""A smooth muscle cell found in the innermost layer of the muscularis externa of the stomach wall. This cell forms a unique layer of smooth muscle fibers oriented obliquely to the stomach's longitudinal axis. It is responsible for aiding in the mixing and churning of gastric contents, contributing to mechanical digestion within the stomach.""",
                meaning=CL["4047037"]))
        setattr(cls, "CL:0000419",
            PermissibleValue(
                text="CL:0000419",
                description="An epithelial fate stem cell found in flatworms.",
                meaning=CL["0000419"]))
        setattr(cls, "CL:0009096",
            PermissibleValue(
                text="CL:0009096",
                description="""Any cell that is part of the esophageal non-keratinized stratified squamous epithelium. In humans, the esophagus, which requires flexibility to accommodate swallowing of a bolus, is covered with a non-keratinized epithelium.""",
                meaning=CL["0009096"]))
        setattr(cls, "CL:1000369",
            PermissibleValue(
                text="CL:1000369",
                description="""A transitional myocyte that is part of the septal division of left branch of atrioventricular bundle.""",
                meaning=CL["1000369"]))
        setattr(cls, "CL:4030022",
            PermissibleValue(
                text="CL:4030022",
                description="A fibroblast that is located in the renal medulla interstitium.",
                meaning=CL["4030022"]))
        setattr(cls, "CL:0000115",
            PermissibleValue(
                text="CL:0000115",
                description="""An endothelial cell comprises the outermost layer or lining of anatomical structures and can be squamous or cuboidal. In mammals, endothelial cell has vimentin filaments and is derived from the mesoderm.""",
                meaning=CL["0000115"]))
        setattr(cls, "CL:1000426",
            PermissibleValue(
                text="CL:1000426",
                description="A chromaffin cell that is part of the adrenal gland.",
                meaning=CL["1000426"]))
        setattr(cls, "CL:0004121",
            PermissibleValue(
                text="CL:0004121",
                description="""A retinal ganglion cell B that has a very small but very dense dendritic field, and has post synaptic terminals in S2.""",
                meaning=CL["0004121"]))
        setattr(cls, "CL:1000371",
            PermissibleValue(
                text="CL:1000371",
                description="A transitional myocyte that is part of the right branch of atrioventricular bundle.",
                meaning=CL["1000371"]))
        setattr(cls, "CL:0009102",
            PermissibleValue(
                text="CL:0009102",
                description="""A specialized, fibroblastic reticular cell of mesenchymal origin found in lymph nodes. In human, it expresses several markers common to myofibroblasts (desmin, vimentin, CD73, CD90, α-smooth muscle actin (αSMA)), and can be differentiated from endothelial cells by its lack of CD31 expression. These cells are critical for the overall organization and function of the lymph node. Lymph node fibroblastic reticular cells (FRCs) can be further classified based on their location, function, and unique marker expression.""",
                meaning=CL["0009102"]))
        setattr(cls, "CL:0002635",
            PermissibleValue(
                text="CL:0002635",
                description="A nonkeratinized epithelial cell of the anal canal.",
                meaning=CL["0002635"]))
        setattr(cls, "CL:0002189",
            PermissibleValue(
                text="CL:0002189",
                description="""A keratinocyte of the epidermis that is characterized by containing granules of keratohyalin and lamellar granules.""",
                meaning=CL["0002189"]))
        setattr(cls, "CL:0000042",
            PermissibleValue(
                text="CL:0000042",
                description="""A myeloblast committed to the neutrophil lineage. This cell type is GATA-1 positive, C/EBPa-positive, AML-1-positive, c-myb-positive and has low expression of PU.1 transcription factor.""",
                meaning=CL["0000042"]))
        setattr(cls, "CL:4033044",
            PermissibleValue(
                text="CL:4033044",
                description="""An epithelial cell part of respiratory tract epithelium that is a precursor of a multi-ciliated cell. This cell actively amplifies centrioles, a required step for multiciliogenesis.""",
                meaning=CL["4033044"]))
        setattr(cls, "CL:0000520",
            PermissibleValue(
                text="CL:0000520",
                meaning=CL["0000520"]))
        setattr(cls, "CL:1000341",
            PermissibleValue(
                text="CL:1000341",
                description="An enterocyte that is part of the epithelium proper of jejunum.",
                meaning=CL["1000341"]))
        setattr(cls, "CL:4052023",
            PermissibleValue(
                text="CL:4052023",
                description="""An epithelial cell that is part of the endometrial luminal epithelium, forming a continuous layer lining the uterine cavity. This cell undergoes cyclical changes during the menstrual cycle, proliferating under estrogen in the proliferative phase, and differentiating under progesterone in the secretory phase to prepare for potential implantation. During the window of implantation, this cell changes from a tall columnar shape to a shorter columnar or cuboidal form, loses polarity, and becomes receptive to blastocyst implantation.""",
                meaning=CL["4052023"]))
        setattr(cls, "CL:0000950",
            PermissibleValue(
                text="CL:0000950",
                description="A plasmablast that secretes IgE.",
                meaning=CL["0000950"]))
        setattr(cls, "CL:0000049",
            PermissibleValue(
                text="CL:0000049",
                description="""A progenitor cell committed to myeloid lineage, including the megakaryocyte and erythroid lineages.""",
                meaning=CL["0000049"]))
        setattr(cls, "CL:0000831",
            PermissibleValue(
                text="CL:0000831",
                description="""A progenitor cell of the mast cell lineage. Markers for this cell are FceRIa-low, CD117-positive, CD9-positive, T1/ST2-positive, SCA1-negative, and lineage-negative.""",
                meaning=CL["0000831"]))
        setattr(cls, "CL:4023119",
            PermissibleValue(
                text="CL:4023119",
                description="""A subpopulation of amacrine cell that migrate further than other amacrine cells, and come to lie basal to the inner plexiform layer (IPL) in the ganglion cell layer. Displaced amacrine cells still have their neurites extending apically into the IPL, and therefore exhibit an inverted polarity with respect to the other amacrine cells.""",
                meaning=CL["4023119"]))
        setattr(cls, "CL:0000645",
            PermissibleValue(
                text="CL:0000645",
                description="""A glial cell of astrocytic lineage with long processes running parallel to adjacent axons in the proximal infundibulum of the neurohypophysis. These processes form a three-dimensional network among the axons of the hypothalamic neurosecretory cells and are connected by gap junctions which provide for their metabolic coupling. This cell type constitutes most of the nonexcitable tissue in the neurohypophsis; function may include possibly acting as an intermediate in the modulation of oxytocin and vasopressin release. This cell type is highly variable in size and shape and commonly contain lipid droplets and deposits of lipochrome pigment.""",
                meaning=CL["0000645"]))
        setattr(cls, "CL:0000755",
            PermissibleValue(
                text="CL:0000755",
                description="""An OFF-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the outer half of the inner plexiform layer. The dendritic tree is delicate and the dendritic tips appear small when compared with type 1 cells. The axon terminal is stratified and restricted to sublamina 2 of the inner plexiform layer.""",
                meaning=CL["0000755"]))
        setattr(cls, "CL:0002290",
            PermissibleValue(
                text="CL:0002290",
                description="""A sperm bearing a Y chromosome. Chromosomal and genetic sex is established at fertilization in mammals and depends upon whether an X-bearing sperm or a Y-bearing sperm fertilizes the X-bearing ovum.""",
                meaning=CL["0002290"]))
        setattr(cls, "CL:0000866",
            PermissibleValue(
                text="CL:0000866",
                description="""A tissue-resident macrophage resident found in the thymus, involved in the clearance of apoptotic thymocytes.""",
                meaning=CL["0000866"]))
        setattr(cls, "CL:0000382",
            PermissibleValue(
                text="CL:0000382",
                description="""A cell that is part of a scolopidium and surrounds the dendrite of a scolopidial neuron.""",
                meaning=CL["0000382"]))
        setattr(cls, "CL:4023043",
            PermissibleValue(
                text="CL:4023043",
                description="""A transcriptomically distinct near-projecting glutamatergic neuron with a soma found in layer 5/6 of the primary motor cortex. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: Deep layer (non-IT) excitatory neurons', Author Categories: 'CrossArea_subclass', cluster L5/6 NP.""",
                meaning=CL["4023043"]))
        setattr(cls, "CL:0002132",
            PermissibleValue(
                text="CL:0002132",
                description="A stomal cell of the ovary",
                meaning=CL["0002132"]))
        setattr(cls, "CL:0000947",
            PermissibleValue(
                text="CL:0000947",
                description="A long lived plasma cell that secretes IgE.",
                meaning=CL["0000947"]))
        setattr(cls, "CL:0002034",
            PermissibleValue(
                text="CL:0002034",
                description="""A hematopoietic stem cell with long term self renewal capability. This cell is Kit-positive, Sca1-positive, CD150-positive, CD90-low, CD34-negative and Flt3-negative.""",
                meaning=CL["0002034"]))
        setattr(cls, "CL:0008024",
            PermissibleValue(
                text="CL:0008024",
                description="An endocrine cell that is part of the pancreas.",
                meaning=CL["0008024"]))
        setattr(cls, "CL:0002552",
            PermissibleValue(
                text="CL:0002552",
                description="Any fibroblast that is part of some gingiva.",
                meaning=CL["0002552"]))
        setattr(cls, "CL:0000227",
            PermissibleValue(
                text="CL:0000227",
                description="Any cell that has characteristic some binucleate.",
                meaning=CL["0000227"]))
        setattr(cls, "CL:2000071",
            PermissibleValue(
                text="CL:2000071",
                description="Any microvascular endothelial cell that is part of a breast.",
                meaning=CL["2000071"]))
        setattr(cls, "CL:0000882",
            PermissibleValue(
                text="CL:0000882",
                description="A thymic macrophage found in the thymic medulla.",
                meaning=CL["0000882"]))
        setattr(cls, "CL:0000551",
            PermissibleValue(
                text="CL:0000551",
                meaning=CL["0000551"]))
        setattr(cls, "CL:0000926",
            PermissibleValue(
                text="CL:0000926",
                description="""A mature NK T cell that secretes interferon-gamma and enhances type 1 immune responses.""",
                meaning=CL["0000926"]))
        setattr(cls, "CL:0002124",
            PermissibleValue(
                text="CL:0002124",
                description="""A circulating gamma-delta T cell that is CD27-positive and capable of producing IFN-gamma.""",
                meaning=CL["0002124"]))
        setattr(cls, "CL:0010008",
            PermissibleValue(
                text="CL:0010008",
                description="Any endothelial cell that is part of some heart.",
                meaning=CL["0010008"]))
        setattr(cls, "CL:0000731",
            PermissibleValue(
                text="CL:0000731",
                description="""A cell of a layer of transitional epithelium in the wall of the proximal urethra, bladder, ureter or renal pelvis, external to the lamina propria.""",
                meaning=CL["0000731"]))
        setattr(cls, "CL:0009090",
            PermissibleValue(
                text="CL:0009090",
                description="""An adult endothelial progenitor cell that is resident of adult vasculature and capable of differentiating to regenerate endothelial cell populations. Endothelial colony forming cells are characterised in vivo by clonal proliferative status, de novo vessel formation, homing to ischemic sites and paracrine support of angiogenesis. These cells are phenotypically similar to endothelial cells.""",
                meaning=CL["0009090"]))
        setattr(cls, "CL:0002477",
            PermissibleValue(
                text="CL:0002477",
                description="""A macrophage located in adipose tissue that is CD45-positive, CD11c-positive, and SIRPa-positive.""",
                meaning=CL["0002477"]))
        setattr(cls, "CL:0009067",
            PermissibleValue(
                text="CL:0009067",
                description="""An enterocyte found in the small intestine of newborn mammals and characterized by the presence of an apical canalicular system (ACS) leading to production of large vacuoles, important for colostral macromolecule uptake. After birth, the vacuolated fetal-type enterocytes are replaced with enterocytes lacking an ACS.""",
                meaning=CL["0009067"]))
        setattr(cls, "CL:0002059",
            PermissibleValue(
                text="CL:0002059",
                description="A conventional thymic dendritic cell that is CD8-alpha-positive.",
                meaning=CL["0002059"]))
        setattr(cls, "CL:0002460",
            PermissibleValue(
                text="CL:0002460",
                description="A conventional thymic dendritic cell that is CD8-alpha-negative.",
                meaning=CL["0002460"]))
        setattr(cls, "CL:0000286",
            PermissibleValue(
                text="CL:0000286",
                description="A cell of a filament of a fungal mycelium.",
                meaning=CL["0000286"]))
        setattr(cls, "CL:4023154",
            PermissibleValue(
                text="CL:4023154",
                description="A glial cell that myelinates axonal processes.",
                meaning=CL["4023154"]))
        setattr(cls, "CL:0004253",
            PermissibleValue(
                text="CL:0004253",
                description="An amicrine that has a wide dendritic field.",
                meaning=CL["0004253"]))
        setattr(cls, "CL:0019015",
            PermissibleValue(
                text="CL:0019015",
                description="""An eosinophil with a ring-shaped nucleus that is resident in the lung parenchyma. In mouse, lung parenchyma resident eosinophils are IL-5-independent Siglec-F(intermediate) CD62L+ CD101(low). In human, they are Siglec-8+ CD62L+ IL-3R(low).""",
                meaning=CL["0019015"]))
        setattr(cls, "CL:1001096",
            PermissibleValue(
                text="CL:1001096",
                description="""An endothelial cell that lines the interior surface of the afferent arteriole and maintains vascular tone. This cell responds to changing ion concentrations and blood pressure by releasing vasoactive substances, in order to regulate blood flow into the glomeruli, which is essential for glomerular filtration.""",
                meaning=CL["1001096"]))
        setattr(cls, "CL:0000192",
            PermissibleValue(
                text="CL:0000192",
                description="""A non-striated, elongated, spindle-shaped cell found lining the digestive tract, uterus, and blood vessels. They develop from specialized myoblasts (smooth muscle myoblast).""",
                meaning=CL["0000192"]))
        setattr(cls, "CL:1000719",
            PermissibleValue(
                text="CL:1000719",
                description="Any renal intercalated cell that is part of some inner medullary collecting duct.",
                meaning=CL["1000719"]))
        setattr(cls, "CL:1000343",
            PermissibleValue(
                text="CL:1000343",
                description="A paneth cell that is part of the epithelium of small intestine.",
                meaning=CL["1000343"]))
        setattr(cls, "CL:0000590",
            PermissibleValue(
                text="CL:0000590",
                description="A progesterone secreting cell in the corpus luteum that develops from theca cells.",
                meaning=CL["0000590"]))
        setattr(cls, "CL:0000533",
            PermissibleValue(
                text="CL:0000533",
                description="A primary neuron (sensu Teleostei) that has a motor function.",
                meaning=CL["0000533"]))
        setattr(cls, "CL:4042039",
            PermissibleValue(
                text="CL:4042039",
                description="""A neuron of the central nervous system that develops from a caudal ganglionic eminence.""",
                meaning=CL["4042039"]))
        setattr(cls, "CL:0001011",
            PermissibleValue(
                text="CL:0001011",
                description="""Immature interstitial dendritic cell is a interstitial dendritic cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0001011"]))
        setattr(cls, "CL:0000718",
            PermissibleValue(
                text="CL:0000718",
                description="A cell of an ommatidium that secretes lens materials.",
                meaning=CL["0000718"]))
        setattr(cls, "CL:0000684",
            PermissibleValue(
                text="CL:0000684",
                meaning=CL["0000684"]))
        setattr(cls, "CL:4030068",
            PermissibleValue(
                text="CL:4030068",
                description="""A transcriptomically distinct intratelencepalic-projecting glutamatergic neuron that expresses Car3 with a soma found in L6 . The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: IT-projecting excitatory neurons', Author Categories: 'CrossArea_cluster', L6 IT Car3.""",
                meaning=CL["4030068"]))
        setattr(cls, "CL:0002087",
            PermissibleValue(
                text="CL:0002087",
                description="A leukocyte that lacks granules.",
                meaning=CL["0002087"]))
        setattr(cls, "CL:0000952",
            PermissibleValue(
                text="CL:0000952",
                description="""An preBRC-positive large pre-B-II cell is a large pre-B-II cell that is pre-B cell receptor-positive, composed of surrogate light chain protein (SL), which is composed of VpreB , Lambda 5/14.1, in complex with immunoglobulin mu heavy chain (IgHmu) on the cell surface.""",
                meaning=CL["0000952"]))
        setattr(cls, "CL:1000300",
            PermissibleValue(
                text="CL:1000300",
                description="A fibroblast that is part of the outer membrane of prostatic capsule.",
                meaning=CL["1000300"]))
        setattr(cls, "CL:0000526",
            PermissibleValue(
                text="CL:0000526",
                description="A neuron which conveys sensory information centrally from the periphery.",
                meaning=CL["0000526"]))
        setattr(cls, "CL:0002537",
            PermissibleValue(
                text="CL:0002537",
                description="A mesenchymal stem cell of the amnion membrane.",
                meaning=CL["0002537"]))
        setattr(cls, "CL:1000481",
            PermissibleValue(
                text="CL:1000481",
                description="A transitional myocyte that is part of the atrioventricular bundle.",
                meaning=CL["1000481"]))
        setattr(cls, "CL:0002000",
            PermissibleValue(
                text="CL:0002000",
                description="""An erythroid progenitor cell is Kit-positive, Ly6A-negative, CD41-negative, CD127-negative, and CD123-negative. This cell type is also described as being lin-negative, Kit-positive, CD150-negative, CD41-negative, CD105-positive, and FcgR-negative.""",
                meaning=CL["0002000"]))
        setattr(cls, "CL:4042028",
            PermissibleValue(
                text="CL:4042028",
                description="""A neuron in the central nervous system that is not committed to a differentiated fate, has not been newly derived from neurogenesis, and does not integrate into any circuit.""",
                meaning=CL["4042028"]))
        setattr(cls, "CL:0004138",
            PermissibleValue(
                text="CL:0004138",
                description="A retinal ganglion A cell with dense arbor near soma.",
                meaning=CL["0004138"]))
        setattr(cls, "CL:0000700",
            PermissibleValue(
                text="CL:0000700",
                description="A neuron that releases dopamine as a neurotransmitter.",
                meaning=CL["0000700"]))
        setattr(cls, "CL:0000863",
            PermissibleValue(
                text="CL:0000863",
                description="""An elicited macrophage that is recruited into the tissues in response to injury and infection as part of an inflammatory response, expresses high levels of pro-inflammatory cytokines, ROS and NO, and shows potent microbicidal activity.""",
                meaning=CL["0000863"]))
        setattr(cls, "CL:0000333",
            PermissibleValue(
                text="CL:0000333",
                description="""A cell derived from the specialized ectoderm flanking each side of the embryonic neural plate, which after the closure of the neural tube, forms masses of cells that migrate out from the dorsal aspect of the neural tube to spread throughout the body.""",
                meaning=CL["0000333"]))
        setattr(cls, "CL:0002345",
            PermissibleValue(
                text="CL:0002345",
                description="""An immature natural killer cell that is NK1.1-positive, DX5-positive, Ly49-positive, CD27-low and CD11b-low. This cell type is found in high numbers in the liver.""",
                meaning=CL["0002345"]))
        setattr(cls, "CL:0002090",
            PermissibleValue(
                text="CL:0002090",
                description="One of two small cells formed by the first and second meiotic division of oocytes.",
                meaning=CL["0002090"]))
        setattr(cls, "CL:0002615",
            PermissibleValue(
                text="CL:0002615",
                description="An adipocyte that is part of omentum tissue.",
                meaning=CL["0002615"]))
        setattr(cls, "CL:0001042",
            PermissibleValue(
                text="CL:0001042",
                description="CD4-positive, alpha-beta T cell that produces IL-22.",
                meaning=CL["0001042"]))
        setattr(cls, "CL:0009010",
            PermissibleValue(
                text="CL:0009010",
                description="""Transit-amplifying cells (TACs) are an undifferentiated population in transition between stem cells and differentiated cells.""",
                meaning=CL["0009010"]))
        setattr(cls, "CL:4030029",
            PermissibleValue(
                text="CL:4030029",
                description="A lymphocyte located in blood.",
                meaning=CL["4030029"]))
        setattr(cls, "CL:1000708",
            PermissibleValue(
                text="CL:1000708",
                description="Any ureteral cell that is part of some adventitia of ureter.",
                meaning=CL["1000708"]))
        setattr(cls, "CL:0000707",
            PermissibleValue(
                text="CL:0000707",
                meaning=CL["0000707"]))
        setattr(cls, "CL:0009100",
            PermissibleValue(
                text="CL:0009100",
                description="""A fibroblast located in the portal triad. Hepatic portal fibroblast are a non-parenchymal cell population located adjacent to bile duct epithelia in liver and are distinct from stellate cells. They differentiate into fibrogenic myofibroblasts during chronic injury states producing high levels of collagen.""",
                meaning=CL["0009100"]))
        setattr(cls, "CL:0011001",
            PermissibleValue(
                text="CL:0011001",
                description="""A motor neuron that passes from the spinal cord toward or to a muscle and conducts an impulse that causes movement.""",
                meaning=CL["0011001"]))
        setattr(cls, "CL:0011111",
            PermissibleValue(
                text="CL:0011111",
                description="""A neuroendocrine cell that secretes gonadotropin-releasing hormone (GnRH). A GnRH neuron is born in the nasal placode during embryonic development and migrates through the nose and forebrain to the hypothalamus. This cell regulates reproduction by secreting GnRH into the pituitary portal vessels to induce the release of gonadotropins into the general circulation.""",
                meaning=CL["0011111"]))
        setattr(cls, "CL:1001320",
            PermissibleValue(
                text="CL:1001320",
                description="Any cell that is part of some urethra.",
                meaning=CL["1001320"]))
        setattr(cls, "CL:1000311",
            PermissibleValue(
                text="CL:1000311",
                description="An adipocyte that is part of the epicardial fat of left ventricle.",
                meaning=CL["1000311"]))
        setattr(cls, "CL:0002484",
            PermissibleValue(
                text="CL:0002484",
                description="A melanocyte that produces pigment in the epithelium.",
                meaning=CL["0002484"]))
        setattr(cls, "CL:0000326",
            PermissibleValue(
                text="CL:0000326",
                meaning=CL["0000326"]))
        setattr(cls, "CL:0001055",
            PermissibleValue(
                text="CL:0001055",
                description="An intermediate monocyte that is CD14-positive and with low amounts of CD16.",
                meaning=CL["0001055"]))
        setattr(cls, "CL:0000750",
            PermissibleValue(
                text="CL:0000750",
                description="""A bipolar neuron found in the retina and having connections with photoreceptors cells and neurons in the outer half of the inner plexiform layer. These cells depolarize in response to light to dark transition.""",
                meaning=CL["0000750"]))
        setattr(cls, "CL:4042013",
            PermissibleValue(
                text="CL:4042013",
                description="""A transcriptomically distinct lamp5 GABAergic cortical interneuron located in the cerebral cortex that expresses Lamp5 and Lhx6. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: CGE-derived interneurons', Author Categories: 'CrossArea_subclass', Lamp5 Lhx6.""",
                meaning=CL["4042013"]))
        setattr(cls, "CL:1000443",
            PermissibleValue(
                text="CL:1000443",
                description="A smooth muscle cell that is part of the ciliary body.",
                meaning=CL["1000443"]))
        setattr(cls, "CL:0000709",
            PermissibleValue(
                text="CL:0000709",
                meaning=CL["0000709"]))
        setattr(cls, "CL:0000083",
            PermissibleValue(
                text="CL:0000083",
                description="An epithelial cell of the pancreas.",
                meaning=CL["0000083"]))
        setattr(cls, "CL:4030047",
            PermissibleValue(
                text="CL:4030047",
                description="""A DRD2-expressing medium spiny neuron that is part of a matrix compartment of dorsal striatum.""",
                meaning=CL["4030047"]))
        setattr(cls, "CL:0000007",
            PermissibleValue(
                text="CL:0000007",
                description="A cell found in the embryo before the formation of all the gem layers is complete.",
                meaning=CL["0000007"]))
        setattr(cls, "CL:0008026",
            PermissibleValue(
                text="CL:0008026",
                description="""An epithelial cell that is part of the epithelium of a tracheal tube in an open tracheal system, such as that found in insects.""",
                meaning=CL["0008026"]))
        setattr(cls, "CL:0002486",
            PermissibleValue(
                text="CL:0002486",
                description="""A melanocyte located between the epithelial marginal cell layer and the mesodermal basal cell layer within the intrastrial space; the predominant cellular component of the electrogenic machinery that generates an endocochlear potential (80-100 mV) .""",
                meaning=CL["0002486"]))
        setattr(cls, "CL:0002213",
            PermissibleValue(
                text="CL:0002213",
                description="""A muscle cell with low content of myoglobin and other oxygen storing proteins. This muscle cell has a white appearance.""",
                meaning=CL["0002213"]))
        setattr(cls, "CL:4047007",
            PermissibleValue(
                text="CL:4047007",
                description="""A pericyte that is in an early stage of development, found in newly forming or remodeling blood vessels. An immature pericyte is characterized by it's mesenchymal stem cell-like properties and high proliferative capacity, which allows it to differentiate into various types of pericytes and contribute to the structural and functional maturation of the vasculature. Immature pericytes are stellate in new vessels and elongated with less protrusions in remodeling vessels.""",
                meaning=CL["4047007"]))
        setattr(cls, "CL:0009083",
            PermissibleValue(
                text="CL:0009083",
                description="The human equivalent of a DN4 thymocyte.",
                meaning=CL["0009083"]))
        setattr(cls, "CL:2000038",
            PermissibleValue(
                text="CL:2000038",
                description="Any neuromast mantle cell that is part of a posterior lateral line.",
                meaning=CL["2000038"]))
        setattr(cls, "CL:0003013",
            PermissibleValue(
                text="CL:0003013",
                description="""A mono-stratified retinal ganglion cell that has a large dendritic field, a medium dendritic arbor, and a long secondary dendrite shaft with post synaptic terminals in sublaminar layer S4.""",
                meaning=CL["0003013"]))
        setattr(cls, "CL:1000445",
            PermissibleValue(
                text="CL:1000445",
                description="A myoepithelial cell that is part of the dilatator pupillae.",
                meaning=CL["1000445"]))
        setattr(cls, "CL:4033033",
            PermissibleValue(
                text="CL:4033033",
                description="""An OFF bipolar cell with a small dendritic tree that provides most of the triad-associated basal (flat) contacts at cone pedicles.""",
                meaning=CL["4033033"]))
        setattr(cls, "CL:0000825",
            PermissibleValue(
                text="CL:0000825",
                description="""A lymphoid progenitor cell that is committed to the natural killer cell lineage, expressing CD122 (IL-15) receptor, but lacking many of the phenotypic characteristics of later stages of natural killer cell development such as expression of NK activating and inhibitory molecules. In human this cell has the phenotype CD34-positive, CD45RA-positive, CD10-positive, CD117-negative, and CD161 negative.""",
                meaning=CL["0000825"]))
        setattr(cls, "CL:1000495",
            PermissibleValue(
                text="CL:1000495",
                description="A goblet cell that is part of the small intestine.",
                meaning=CL["1000495"]))
        setattr(cls, "CL:2000068",
            PermissibleValue(
                text="CL:2000068",
                description="Any fibroblast that is part of a pericardium.",
                meaning=CL["2000068"]))
        setattr(cls, "CL:0004228",
            PermissibleValue(
                text="CL:0004228",
                description="""An amacrine cell with a small dendritic field that has post-synaptic terminals in S1, S2, S3, and S4.""",
                meaning=CL["0004228"]))
        setattr(cls, "CL:1001607",
            PermissibleValue(
                text="CL:1001607",
                description="Chondrocyte forming the hyaline cartilage found in joints.",
                meaning=CL["1001607"]))
        setattr(cls, "CL:4028003",
            PermissibleValue(
                text="CL:4028003",
                description="""An alveolar capillary endothelial cell that is located proximally to alveolar capillary type 1 endothelial cells and in close apposition to alveolar type 1 epithelial cells (also known as type I pneumocytes).""",
                meaning=CL["4028003"]))
        setattr(cls, "CL:0000247",
            PermissibleValue(
                text="CL:0000247",
                description="""Type of neuron that is a primary mechanosensory cell, with peripheral neurites innervating the skin with free nerve endings.""",
                meaning=CL["0000247"]))
        setattr(cls, "CL:0005006",
            PermissibleValue(
                text="CL:0005006",
                description="""Specialized epithelial cells involved in the maintenance of osmotic homeostasis. They are characterized by abundant mitochondria and ion transporters. In amniotes, they are present in the renal system. In freshwater fish, ionocytes in the skin and gills help maintain osmotic homeostasis by absorbing salt from the external environment.""",
                meaning=CL["0005006"]))
        setattr(cls, "CL:0002061",
            PermissibleValue(
                text="CL:0002061",
                description="""A T-helper cell that is characterized by secreting interleukin 9 and responding to helminth infections. This cell-type can derives from Th2 cells in the presence of TGF-beta and IL-4. Th2 cytokine production is surpressed.""",
                meaning=CL["0002061"]))
        setattr(cls, "CL:0002580",
            PermissibleValue(
                text="CL:0002580",
                description="A preadipocyte that is part of the breast.",
                meaning=CL["0002580"]))
        setattr(cls, "CL:0002229",
            PermissibleValue(
                text="CL:0002229",
                description="""A chief cell that is bigger than dark chief cells and has a larger and lighter nucleus and a cytoplasm with few granules.""",
                meaning=CL["0002229"]))
        setattr(cls, "CL:1001064",
            PermissibleValue(
                text="CL:1001064",
                meaning=CL["1001064"]))
        setattr(cls, "CL:4030021",
            PermissibleValue(
                text="CL:4030021",
                description="A renal beta-intercalated cell that is part of the renal connecting tubule.",
                meaning=CL["4030021"]))
        setattr(cls, "CL:0000846",
            PermissibleValue(
                text="CL:0000846",
                description="""An epithelial cell of the vestibular sensory organ that is characterized by intense enzymatic activities and numerous basal membrane infoldings.""",
                meaning=CL["0000846"]))
        setattr(cls, "CL:0002469",
            PermissibleValue(
                text="CL:0002469",
                description="Gr1-high monocyte that lacks MHC-II receptor complex.",
                meaning=CL["0002469"]))
        setattr(cls, "CL:1000466",
            PermissibleValue(
                text="CL:1000466",
                description="A chromaffin cell that is part of the right ovary.",
                meaning=CL["1000466"]))
        setattr(cls, "CL:0005013",
            PermissibleValue(
                text="CL:0005013",
                description="A ciliated epithelial cell with a single cilium.",
                meaning=CL["0005013"]))
        setattr(cls, "CL:0000176",
            PermissibleValue(
                text="CL:0000176",
                description="Any secretory cell that is capable of some ecdysteroid secretion.",
                meaning=CL["0000176"]))
        setattr(cls, "CL:0009050",
            PermissibleValue(
                text="CL:0009050",
                description="A B cell that is located in the anorectum.",
                meaning=CL["0009050"]))
        setattr(cls, "CL:1000305",
            PermissibleValue(
                text="CL:1000305",
                description="A fibroblast that is part of the connective tissue of glandular part of prostate.",
                meaning=CL["1000305"]))
        setattr(cls, "CL:0002003",
            PermissibleValue(
                text="CL:0002003",
                description="An erythroid progenitor cell that is CD34-positive and is GlyA-negative.",
                meaning=CL["0002003"]))
        setattr(cls, "CL:0002164",
            PermissibleValue(
                text="CL:0002164",
                description="""A rod-shaped cell found in 3 or 4 rows that lie adjacent to and support the outer hair cells.""",
                meaning=CL["0002164"]))
        setattr(cls, "CL:0002135",
            PermissibleValue(
                text="CL:0002135",
                description="""Epidermal cells that do not contain keratin. Cell type is usually associated with moist epidermal tissues.""",
                meaning=CL["0002135"]))
        setattr(cls, "CL:4023027",
            PermissibleValue(
                text="CL:4023027",
                description="""A sst GABAergic cortical interneuron with a soma found in L5 and possesses 'T-shaped' Martinotti morphologies with local axonal plexus in L5a and translaminar axons restricted to the uppermost part of L1. They show low-threshold spiking patterns with strong rebound firing, and inhibit the L1 apical tuft of nearby pyramidal cells.""",
                meaning=CL["4023027"]))
        setattr(cls, "CL:0000179",
            PermissibleValue(
                text="CL:0000179",
                description="Any secretory cell that is capable of some progesterone secretion.",
                meaning=CL["0000179"]))
        setattr(cls, "CL:0002082",
            PermissibleValue(
                text="CL:0002082",
                description="A chromaffin cell of the adrenal medulla that produces epinephrine.",
                meaning=CL["0002082"]))
        setattr(cls, "CL:0000094",
            PermissibleValue(
                text="CL:0000094",
                description="A leukocyte with abundant granules in the cytoplasm.",
                meaning=CL["0000094"]))
        setattr(cls, "CL:0003038",
            PermissibleValue(
                text="CL:0003038",
                description="""An M7 retinal ganglion cells with synaptic terminals in S2 and is depolarized by decreased illumination of their receptive field center""",
                meaning=CL["0003038"]))
        setattr(cls, "CL:0002369",
            PermissibleValue(
                text="CL:0002369",
                description="""A differentiated form of a fungus produced during or as a result of an asexual or sexual reproductive process; usually a cell with a thick cell wall that stores and protects one or more nuclei. Spores may be produced in response to, and are characteristically resistant to, adverse environmental conditions.""",
                meaning=CL["0002369"]))
        setattr(cls, "CL:1000716",
            PermissibleValue(
                text="CL:1000716",
                description="""Principal cell that is part of some outer medullary collecting duct. It is known in some mammalian species that this cell may express the epithelial sodium channel (ENaC).""",
                meaning=CL["1000716"]))
        setattr(cls, "CL:0000970",
            PermissibleValue(
                text="CL:0000970",
                description="""An unswitched memory B cell is a memory B cell that has the phenotype IgM-positive, IgD-positive, CD27-positive, CD138-negative, IgG-negative, IgE-negative, and IgA-negative.""",
                meaning=CL["0000970"]))
        setattr(cls, "CL:0003002",
            PermissibleValue(
                text="CL:0003002",
                description="""A retinal ganglion cell that has a small dendritic field and a medium dendritic arbor with post sympatic terminals in sublaminar layer S3.""",
                meaning=CL["0003002"]))
        setattr(cls, "CL:0000454",
            PermissibleValue(
                text="CL:0000454",
                description="""A cell capable of producing epinephrine. Epiniphrine is synthesized from norepiniphrine by the actions of the phenylethanolamine N-methyltransferase enzyme, which is expressed in the adrenal glands, androgenic neurons, and in other cell types.""",
                meaning=CL["0000454"]))
        setattr(cls, "CL:0002561",
            PermissibleValue(
                text="CL:0002561",
                description="An epithelial cell that is part of the outer root sheath.",
                meaning=CL["0002561"]))
        setattr(cls, "CL:0000477",
            PermissibleValue(
                text="CL:0000477",
                description="A somatic epithelial cell of the insect egg chamber.",
                meaning=CL["0000477"]))
        setattr(cls, "CL:0000674",
            PermissibleValue(
                text="CL:0000674",
                description="A follicle cell that is part of the stalk connecting adjacent egg chambers.",
                meaning=CL["0000674"]))
        setattr(cls, "CL:0003029",
            PermissibleValue(
                text="CL:0003029",
                description="""A monostratified retinal ganglion cell that has a small soma, a small dendrite field with a dense dendrite arbor, and post synaptic terminals in sublaminer layer S2 and S3.""",
                meaning=CL["0003029"]))
        setattr(cls, "CL:4023162",
            PermissibleValue(
                text="CL:4023162",
                description="""A neuron found in the anterior part of the ventral cochlear nucleus that has the appearance of bushes, having short dendrites. Bushy cells give outputs to different parts of the superior olivary complex.""",
                meaning=CL["4023162"]))
        setattr(cls, "CL:1001599",
            PermissibleValue(
                text="CL:1001599",
                description="""Glandular cell of exocrine pancreas epithelium. Example: pancreatic acinar cell, glandular cells in pancreatic canaliculi, glandular cells in pancreatic ducts.""",
                meaning=CL["1001599"]))
        setattr(cls, "CL:1001577",
            PermissibleValue(
                text="CL:1001577",
                description="Squamous cell of tonsil epithelium.",
                meaning=CL["1001577"]))
        setattr(cls, "CL:0008009",
            PermissibleValue(
                text="CL:0008009",
                description="""A visceral muscle that is transversely striated.  Examples include the visceral muscle cells of arthropods.""",
                meaning=CL["0008009"]))
        setattr(cls, "CL:0003030",
            PermissibleValue(
                text="CL:0003030",
                description="""A monostratified retinal ganglion cell that has a medium soma and a small dendrite field.""",
                meaning=CL["0003030"]))
        setattr(cls, "CL:0003022",
            PermissibleValue(
                text="CL:0003022",
                description="A retinal ganglion cell C outer that has medium dendritic density and field size.",
                meaning=CL["0003022"]))
        setattr(cls, "CL:0002101",
            PermissibleValue(
                text="CL:0002101",
                description="""A CD38-positive naive B cell is a mature B cell that has the phenotype CD38-positive, surface IgD-positive, surface IgM-positive, and CD27-negative, and that has not yet been activated by antigen in the periphery.""",
                meaning=CL["0002101"]))
        setattr(cls, "CL:0009032",
            PermissibleValue(
                text="CL:0009032",
                description="A B cell that is located in a vermiform appendix.",
                meaning=CL["0009032"]))
        setattr(cls, "CL:1001138",
            PermissibleValue(
                text="CL:1001138",
                description="Any kidney cortex artery cell that is part of some interlobular artery.",
                meaning=CL["1001138"]))
        setattr(cls, "CL:0002461",
            PermissibleValue(
                text="CL:0002461",
                description="""A conventional dendritic cell that is CD103-positive. This cell type is usually found in non-lymphoid tissue.""",
                meaning=CL["0002461"]))
        setattr(cls, "CL:0000635",
            PermissibleValue(
                text="CL:0000635",
                description="""The outer phalangeal cells of the organ of Corti. This cell holds the base of the hair cell in a cup-shaped depression.""",
                meaning=CL["0000635"]))
        setattr(cls, "CL:0002366",
            PermissibleValue(
                text="CL:0002366",
                description="""A smooth muscle cell of the myometrium that enlarges and stretches during pregnancy, and contracts in response to oxytocin.""",
                meaning=CL["0002366"]))
        setattr(cls, "CL:0002441",
            PermissibleValue(
                text="CL:0002441",
                description="A NK1.1-positive T cell that is CD94-positive.",
                meaning=CL["0002441"]))
        setattr(cls, "CL:0002079",
            PermissibleValue(
                text="CL:0002079",
                description="""Epithelial cell found in the ducts of the pancreas. This cell type contributes to the high luminal pH.""",
                meaning=CL["0002079"]))
        setattr(cls, "CL:0002655",
            PermissibleValue(
                text="CL:0002655",
                description="An epithelial cell of stratum spinosum of esophageal epithelium.",
                meaning=CL["0002655"]))
        setattr(cls, "CL:4033036",
            PermissibleValue(
                text="CL:4033036",
                description="An OFF bipolar cell that is fovea-specific and expresses FEZF1, NXPH1 and NXPH2.",
                meaning=CL["4033036"]))
        setattr(cls, "CL:0002255",
            PermissibleValue(
                text="CL:0002255",
                description="""A stromal cell of the endometrium, characterized by its fibroblast-like morphology, regenerative capacity, and ability to undergo decidualization. It differentiates into a decidual stromal cell during pregnancy, essential for embryo implantation and maintenance. This cell is involved in tissue proliferation, remodeling, and breakdown, responding to hormonal changes, particularly estrogen and progesterone.""",
                meaning=CL["0002255"]))
        setattr(cls, "CL:0002553",
            PermissibleValue(
                text="CL:0002553",
                description="A fibroblast that is part of lung.",
                meaning=CL["0002553"]))
        setattr(cls, "CL:0002476",
            PermissibleValue(
                text="CL:0002476",
                description="""A tissue-resident macrophage located in the bone marrow. This cell type is B220-negative, CD3e-negative, Ly-6C-negative, CD115-positive, F4/80-positive.""",
                meaning=CL["0002476"]))
        setattr(cls, "CL:0002568",
            PermissibleValue(
                text="CL:0002568",
                description="A mesenchymal stem cell that is part of Wharton's jelly.",
                meaning=CL["0002568"]))
        setattr(cls, "CL:0017001",
            PermissibleValue(
                text="CL:0017001",
                description="A mesodermal cell that is part of the splanchnic layer of lateral plate mesoderm.",
                meaning=CL["0017001"]))
        setattr(cls, "CL:0002071",
            PermissibleValue(
                text="CL:0002071",
                description="""Columnar cell which populate the epithelium of large intestine and absorb water. This cell is the most numerous of the epithelial cell types in the large intestine; bear apical microvilli, contain secretory granules in their apical cytoplasm; secretion appears to be largely mucins, but is also rich in antibodies of the IgA type.""",
                meaning=CL["0002071"]))
        setattr(cls, "CL:4030010",
            PermissibleValue(
                text="CL:4030010",
                description="""A brush border cell that is part of segment 2 (S2) of the proximal tubule epithelium, located in the renal cortex. In addition to its reabsorptive functions, it is also specialized in the secretion of organic anions and cations, including para-aminohippurate.""",
                meaning=CL["4030010"]))
        setattr(cls, "CL:0000869",
            PermissibleValue(
                text="CL:0000869",
                description="A gut-associated lymphoid tissue macrophage found in tonsils.",
                meaning=CL["0000869"]))
        setattr(cls, "CL:0000903",
            PermissibleValue(
                text="CL:0000903",
                description="""CD4-positive alpha-beta T cell with the phenotype FoxP3-positive, CD25-positive, CD62L-positive, and CTLA-4 positive with regulatory function.""",
                meaning=CL["0000903"]))
        setattr(cls, "CL:4023069",
            PermissibleValue(
                text="CL:4023069",
                description="""A GABAergic cortical interneuron that develops from the medial ganglionic eminence and has migrated to the cerebral cortex.""",
                meaning=CL["4023069"]))
        setattr(cls, "CL:0002226",
            PermissibleValue(
                text="CL:0002226",
                description="A secondary lens fiber cell that lacks a nucleus.",
                meaning=CL["0002226"]))
        setattr(cls, "CL:0000448",
            PermissibleValue(
                text="CL:0000448",
                description="""An adipocyte with light coloration and few mitochondria. It contains a scant ring of cytoplasm surrounding a single large lipid droplet or vacuole.""",
                meaning=CL["0000448"]))
        setattr(cls, "CL:0000630",
            PermissibleValue(
                text="CL:0000630",
                description="A cell whose primary function is to support other cell types.",
                meaning=CL["0000630"]))
        setattr(cls, "CL:0002585",
            PermissibleValue(
                text="CL:0002585",
                description="A blood vessel endothelial cell that is part of the retina.",
                meaning=CL["0002585"]))
        setattr(cls, "CL:0000976",
            PermissibleValue(
                text="CL:0000976",
                description="""A short lived plasma cell that secretes IgA. These cells may be found in the bone marrow as well as in the mucosal immune system.""",
                meaning=CL["0000976"]))
        setattr(cls, "CL:0008006",
            PermissibleValue(
                text="CL:0008006",
                description="""A myoblast that detemines the properties (size, shape and attachment to the epidermis) of a `somatic muscle myotube` (CL:0008003) .  It develops into a somatic muscle myotube via fusion with `fusion component myoblasts` (CL:0000621).""",
                meaning=CL["0008006"]))
        setattr(cls, "CL:0002487",
            PermissibleValue(
                text="CL:0002487",
                description="A neuronal receptor that respond to mechanical pressure or distortion in the skin.",
                meaning=CL["0002487"]))
        setattr(cls, "CL:1000547",
            PermissibleValue(
                text="CL:1000547",
                description="An epithelial cell that is part of some inner medullary collecting duct.",
                meaning=CL["1000547"]))
        setattr(cls, "CL:0001202",
            PermissibleValue(
                text="CL:0001202",
                description="A plasmablast that is CD86-positive.",
                meaning=CL["0001202"]))
        setattr(cls, "CL:4023071",
            PermissibleValue(
                text="CL:4023071",
                description="""A GABAergic cortical interneuron that expresses cck. L5/6 cck cells have soma found mainly in L5 and L6 and have large axonal arborization.""",
                meaning=CL["4023071"]))
        setattr(cls, "CL:0011006",
            PermissibleValue(
                text="CL:0011006",
                description="""A cerebellar interneuron characterized by a spindle-shaped or triangular soma, parasagittally oriented and located at the border between the granular layer and the Purkinje cell layer. The Lugaro cell extends dendrites predominantly in the parasagittal plane, forming synaptic interactions with basket, stellate, and Golgi cells. Its axonal projections extend upward into the molecular layer, where they form a parasagittal plexus and emit long transverse collaterals that run parallel to the long axis of the cerebellar folia. The Lugaro cell is capable of co-releasing GABA and glycine, as evidenced by the expression of glutamate decarboxylase (GAD65/67) and the glycine transporter GlyT2.""",
                meaning=CL["0011006"]))
        setattr(cls, "CL:0002134",
            PermissibleValue(
                text="CL:0002134",
                description="A stromal cell of the ovarian medulla.",
                meaning=CL["0002134"]))
        setattr(cls, "CL:0002500",
            PermissibleValue(
                text="CL:0002500",
                description="""A P/D1 enteroendocrine cell that is Grimelius positive and stores bombesin-like polypeptide.""",
                meaning=CL["0002500"]))
        setattr(cls, "CL:0000666",
            PermissibleValue(
                text="CL:0000666",
                description="""An endothelial cell that has small pores, or fenestrations, which allow for the efficient exchange of substances between the blood and surrounding tissues.""",
                meaning=CL["0000666"]))
        setattr(cls, "CL:0002663",
            PermissibleValue(
                text="CL:0002663",
                description="A myocardial endocrine cell that is part of the atrium.",
                meaning=CL["0002663"]))
        setattr(cls, "CL:0000329",
            PermissibleValue(
                text="CL:0000329",
                description="Any cell that is capable of some oxygen transport.",
                meaning=CL["0000329"]))
        setattr(cls, "CL:0000494",
            PermissibleValue(
                text="CL:0000494",
                description="A photoreceptor cell that detects ultraviolet light.",
                meaning=CL["0000494"]))
        setattr(cls, "CL:0002277",
            PermissibleValue(
                text="CL:0002277",
                description="""An enteroendocrine cell commonest in the duodenum and jejunum, rare in ileum, that secretes cholecystokinin. This cell type is involved in the regulation of digestive enzymes and bile.""",
                meaning=CL["0002277"]))
        setattr(cls, "CL:0002010",
            PermissibleValue(
                text="CL:0002010",
                description="""A lin-negative, MHC-II-negative, CD11c-positive, FLT3-positive cell with intermediate expression of SIRP-alpha.""",
                meaning=CL["0002010"]))
        setattr(cls, "CL:0002161",
            PermissibleValue(
                text="CL:0002161",
                description="""A cell type found on the superficial layer of the external side of the tympanic membrane. This cell-type lacks a nucleus.""",
                meaning=CL["0002161"]))
        setattr(cls, "CL:4033069",
            PermissibleValue(
                text="CL:4033069",
                description="A(n) T cell that is cycling.",
                meaning=CL["4033069"]))
        setattr(cls, "CL:0002231",
            PermissibleValue(
                text="CL:0002231",
                description="An epithelial cell of the prostate.",
                meaning=CL["0002231"]))
        setattr(cls, "CL:4030014",
            PermissibleValue(
                text="CL:4030014",
                description="""Epithelial cell of the descending thin limb of the long loop (juxtamedullary) nephron that spans the inner medulla. It is known in some mammalian species that the long descending limb of the loop of Henle in the inner medulla selectively expresses the nuclear receptor Nr2e3, the Ig kappa chain Igkc, and the secreted protein dermokine (Dmkn). SLC14A2, which expresses a urea transporter, is also expressed in the inner medulla.""",
                meaning=CL["4030014"]))
        setattr(cls, "CL:1000334",
            PermissibleValue(
                text="CL:1000334",
                description="An enterocyte that is part of the epithelium of small intestine.",
                meaning=CL["1000334"]))
        setattr(cls, "CL:1001045",
            PermissibleValue(
                text="CL:1001045",
                description="Any kidney arterial blood vessel cell that is part of some renal cortex artery.",
                meaning=CL["1001045"]))
        setattr(cls, "CL:0002015",
            PermissibleValue(
                text="CL:0002015",
                description="A polychromatophilic erythroblast that is Lyg 76-high and is Kit-negative.",
                meaning=CL["0002015"]))
        setattr(cls, "CL:1001588",
            PermissibleValue(
                text="CL:1001588",
                description="""Glandular cell of colon epithelium. Example: Goblet cells; enterocytes or absorptive cells; enteroendocrine and M cells.""",
                meaning=CL["1001588"]))
        setattr(cls, "CL:0002193",
            PermissibleValue(
                text="CL:0002193",
                description="""A cell type that is the first of the maturation stages of the granulocytic leukocytes normally found in the bone marrow. Granules are seen in the cytoplasm. The nuclear material of the myelocyte is denser than that of the myeloblast but lacks a definable membrane. The cell is flat and contains increasing numbers of granules as maturation progresses.""",
                meaning=CL["0002193"]))
        setattr(cls, "CL:0001658",
            PermissibleValue(
                text="CL:0001658",
                meaning=CL["0001658"]))
        setattr(cls, "CL:0002169",
            PermissibleValue(
                text="CL:0002169",
                description="An epithelial cell located on the basal lamina of the olfactory epithelium.",
                meaning=CL["0002169"]))
        setattr(cls, "CL:0002405",
            PermissibleValue(
                text="CL:0002405",
                description="""A post-natal thymocyte expressing components of the gamma-delta T cell receptor. This cell type is always double-negative (i.e. CD4-negative, CD8-negative).""",
                meaning=CL["0002405"]))
        setattr(cls, "CL:1000768",
            PermissibleValue(
                text="CL:1000768",
                description="Any nephron tubule epithelial cell that is part of some renal connecting tubule.",
                meaning=CL["1000768"]))
        setattr(cls, "CL:4030052",
            PermissibleValue(
                text="CL:4030052",
                description="""A DRD2-expressing medium spiny neuron that is part of a nucleus accumbens shell or olfactory tubercle.""",
                meaning=CL["4030052"]))
        setattr(cls, "CL:0001066",
            PermissibleValue(
                text="CL:0001066",
                description="""A progenitor cell committed to the erythroid lineage. This cell is ter119-positive but lacks expression of other hematopoietic lineage markers (lin-negative).""",
                meaning=CL["0001066"]))
        setattr(cls, "CL:4023011",
            PermissibleValue(
                text="CL:4023011",
                description="""A transcriptomically distinct GABAergic neuron located in the cerebral cortex that expresses Lamp5. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: CGE-derived interneurons', Author Categories: 'CrossArea_subclass', clusters Lamp5.""",
                meaning=CL["4023011"]))
        setattr(cls, "CL:1000415",
            PermissibleValue(
                text="CL:1000415",
                description="An epithelial cell that is part of the gallbladder.",
                meaning=CL["1000415"]))
        setattr(cls, "CL:4033009",
            PermissibleValue(
                text="CL:4033009",
                description="A(n) goblet cell that is part of a(n) epithelium of lobar bronchus.",
                meaning=CL["4033009"]))
        setattr(cls, "CL:0009085",
            PermissibleValue(
                text="CL:0009085",
                description="""An adult endothelial progenitor cell characterised in vivo by homing to ischemic sites and paracrine support of angiogenesis. They may form discrete colonies.""",
                meaning=CL["0009085"]))
        setattr(cls, "CL:0004137",
            PermissibleValue(
                text="CL:0004137",
                description="A retinal ganglion A2 cell with dendrites terminating in S4.",
                meaning=CL["0004137"]))
        setattr(cls, "CL:1000477",
            PermissibleValue(
                text="CL:1000477",
                description="A nodal myocyte that is part of the sinoatrial node.",
                meaning=CL["1000477"]))
        setattr(cls, "CL:0002158",
            PermissibleValue(
                text="CL:0002158",
                description="Epithelial cell found on the external side of the tympanic membrane",
                meaning=CL["0002158"]))
        setattr(cls, "CL:0000967",
            PermissibleValue(
                text="CL:0000967",
                description="""A memory B cell arising in the germinal center that is IgD-negative and has undergone somatic mutation of the variable region of the immunoglobulin heavy and light chain genes.""",
                meaning=CL["0000967"]))
        setattr(cls, "CL:0010012",
            PermissibleValue(
                text="CL:0010012",
                description="A CNS neuron of the cerebral cortex.",
                meaning=CL["0010012"]))
        setattr(cls, "CL:1000703",
            PermissibleValue(
                text="CL:1000703",
                description="Any kidney epithelial cell that is part of some kidney pelvis urothelium.",
                meaning=CL["1000703"]))
        setattr(cls, "CL:0004240",
            PermissibleValue(
                text="CL:0004240",
                description="""An amacrine cell with a wide dendritic field, dendrites in S1, and post-synaptic terminals in S1.""",
                meaning=CL["0004240"]))
        setattr(cls, "CL:0000726",
            PermissibleValue(
                text="CL:0000726",
                description="""An asexual 1-celled spore (primarily for perennation, not dissemination). Originates endogenously and singly within part of a pre-existing cell by the contraction of the protoplast. Possesses an inner secondary and often thickened hyaline or brown wall, usually impregnated with hydrophobic material.""",
                meaning=CL["0000726"]))
        setattr(cls, "CL:4023003",
            PermissibleValue(
                text="CL:4023003",
                description="""A type of intrafusal muscle fiber that has nuclei arranged in a linear row. Unlike nuclear bag fibers, the equatorial region of these fibers (in the centre of the spindle) is not expanded. These fibers are responsible for the detection of changes in muscle length. They are innervated by static gamma motor neurons and are principally associated with type II sensory fibers.""",
                meaning=CL["4023003"]))
        setattr(cls, "CL:0000915",
            PermissibleValue(
                text="CL:0000915",
                description="""An alpha-beta intraepithelial T cell with the phenotype CD8-alpha-alpha-positive located in the columnar epithelium of the gastrointestinal tract. These cells have a memory phenotype of CD2-negative and CD5-negative.""",
                meaning=CL["0000915"]))
        setattr(cls, "CL:0000434",
            PermissibleValue(
                text="CL:0000434",
                description="A secretory cell that discharges its product without loss of cytoplasm.",
                meaning=CL["0000434"]))
        setattr(cls, "CL:0002444",
            PermissibleValue(
                text="CL:0002444",
                description="A NK1.1-positive T cell that is Ly49H-positive.",
                meaning=CL["0002444"]))
        setattr(cls, "CL:0002234",
            PermissibleValue(
                text="CL:0002234",
                description="A cell of the basal layer of the epithelium in the prostatic acinus.",
                meaning=CL["0002234"]))
        setattr(cls, "CL:4030063",
            PermissibleValue(
                text="CL:4030063",
                description="""A transcriptomically distinct intratelencephalic-projecting glutamatergic neuron with a soma found in cortical layer 3-4. This neuron type can have a pyramidal, star-pyramidal or spiny stellate morphology and projects its output to L2/3 and L5A/B. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: IT-projecting excitatory neurons', Author Categories: 'CrossArea_subclass', L4 IT.""",
                meaning=CL["4030063"]))
        setattr(cls, "CL:0000324",
            PermissibleValue(
                text="CL:0000324",
                meaning=CL["0000324"]))
        setattr(cls, "CL:1000492",
            PermissibleValue(
                text="CL:1000492",
                description="A mesothelial cell that is part of the parietal pleura.",
                meaning=CL["1000492"]))
        setattr(cls, "CL:0000627",
            PermissibleValue(
                text="CL:0000627",
                description="""A cell involved in transporting nutrients, minerals, water, gases and other chemicals between cells for a variety of purposes including conveying nutrition to other tissues, removing waste products from the tissues, conveying gases for respiration, distributing heat and repelling invasion of foreign substances.""",
                meaning=CL["0000627"]))
        setattr(cls, "CL:0002617",
            PermissibleValue(
                text="CL:0002617",
                description="An adipocyte that is part of the breast.",
                meaning=CL["0002617"]))
        setattr(cls, "CL:0001001",
            PermissibleValue(
                text="CL:0001001",
                description="""Immature CD8-alpha-negative CD11b-negative dendritic cell is a CD8-alpha-negative CD11b-negative dendritic cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0001001"]))
        setattr(cls, "CL:0011023",
            PermissibleValue(
                text="CL:0011023",
                description="A mast cell that is CD25+.",
                meaning=CL["0011023"]))
        setattr(cls, "CL:2000005",
            PermissibleValue(
                text="CL:2000005",
                description="Any macroglial cell that is part of a brain.",
                meaning=CL["2000005"]))
        setattr(cls, "CL:0000105",
            PermissibleValue(
                text="CL:0000105",
                description="""Neuron with two neurites that are fused grossly when they protrude from the soma and bifurcate a short distance from the soma.""",
                meaning=CL["0000105"]))
        setattr(cls, "CL:2000066",
            PermissibleValue(
                text="CL:2000066",
                description="Any fibroblast that is part of a cardiac ventricle.",
                meaning=CL["2000066"]))
        setattr(cls, "CL:0000877",
            PermissibleValue(
                text="CL:0000877",
                description="""A splenic white pulp macrophage found in and around the germinal centers of the white pulp of the spleen that participates in phagocytosis of apoptotic B cells from the germinal centers. A marker for a cell of this type is Mertk-positive.""",
                meaning=CL["0000877"]))
        setattr(cls, "CL:0002343",
            PermissibleValue(
                text="CL:0002343",
                description="""A natural killer cell subset that is found in the decidual of the uterus and is CD56-high, Galectin-1-positive and CD16-negative. This cell type represents the most abundant immune cell type in the decidual during the first trimester of pregnancy.""",
                meaning=CL["0002343"]))
        setattr(cls, "CL:1000217",
            PermissibleValue(
                text="CL:1000217",
                description="Any chondrocyte that is part of some growth plate cartilage.",
                meaning=CL["1000217"]))
        setattr(cls, "CL:1000354",
            PermissibleValue(
                text="CL:1000354",
                description="A M cell that is part of the epithelium of intestinal villus.",
                meaning=CL["1000354"]))
        setattr(cls, "CL:0000345",
            PermissibleValue(
                text="CL:0000345",
                description="""A mesenchymal cell that is part of a small mass of condensed mesenchyme in the enamel organ; it differentiates into the dentin and dental pulp.""",
                meaning=CL["0000345"]))
        setattr(cls, "CL:4033077",
            PermissibleValue(
                text="CL:4033077",
                description="A(n) alveolar macrophage that is cycling.",
                meaning=CL["4033077"]))
        setattr(cls, "CL:0000322",
            PermissibleValue(
                text="CL:0000322",
                description="""An epithelial cell that lines the peripheral gas exchange region of the lungs of air-breathing vertebrates.""",
                meaning=CL["0000322"]))
        setattr(cls, "CL:2000045",
            PermissibleValue(
                text="CL:2000045",
                description="Any melanocyte of skin that is part of a skin of prepuce of penis.",
                meaning=CL["2000045"]))
        setattr(cls, "CL:0000887",
            PermissibleValue(
                text="CL:0000887",
                description="""A lymph node macrophage found in the subcapsular sinus of lymph nodes that participates in sensing, clearance, and antigen presentation of lymph-borne particulate antigens. This macrophage is capable of activating invaraint NKT cells and is CD169-positive.""",
                meaning=CL["0000887"]))
        setattr(cls, "CL:0000465",
            PermissibleValue(
                text="CL:0000465",
                description="A precursor of the cells that form the dorsal vessel of arthropods.",
                meaning=CL["0000465"]))
        setattr(cls, "CL:0002356",
            PermissibleValue(
                text="CL:0002356",
                description="""A primitive erythrocyte that has undergone enucleation. This cell type is 3-6 fold bigger than the fetal derived erythrocytes that they co-circulate with during fetal development. Expresses epsilon-gamma hemoglobin chains.""",
                meaning=CL["0002356"]))
        setattr(cls, "CL:1000330",
            PermissibleValue(
                text="CL:1000330",
                description="A serous secreting cell that is part of the epithelium of trachea.",
                meaning=CL["1000330"]))
        setattr(cls, "CL:0002285",
            PermissibleValue(
                text="CL:0002285",
                description="""A taste receptor cell that is characterized by morphologically identifiable synaptic contacts with the gustatory nerve fibers and expression of the synaptic membrane protein-25 (SNAP-25) and NCAM.""",
                meaning=CL["0002285"]))
        setattr(cls, "CL:0017004",
            PermissibleValue(
                text="CL:0017004",
                description="""A supportive cell with a small, oval-shaped body and one to five telopodes. Telopodes are cytoplasmic protrusions from tens to hundreds of micrometers long and mostly below 0.2 microns of caliber.""",
                meaning=CL["0017004"]))
        setattr(cls, "CL:0002043",
            PermissibleValue(
                text="CL:0002043",
                description="""A hematopoietic multipotent progenitor cell that is CD34-positive, CD38-negative, CD45RA-negative, and CD90-negative.""",
                meaning=CL["0002043"]))
        setattr(cls, "CL:0001047",
            PermissibleValue(
                text="CL:0001047",
                description="""A CD4-positive, CD25-positive, alpha-beta regulatory T cell with the additional phenotype CCR4-positive.""",
                meaning=CL["0001047"]))
        setattr(cls, "CL:1000468",
            PermissibleValue(
                text="CL:1000468",
                description="A myoepithelial cell that is part of the acinus of lactiferous gland.",
                meaning=CL["1000468"]))
        setattr(cls, "CL:0000459",
            PermissibleValue(
                text="CL:0000459",
                description="""A cell capable of producting norepiniphrine. Norepiniphrine is a catecholamine with multiple roles including as a hormone and a neurotransmitter. In addition, epiniphrine is synthesized from norepiniphrine by the actions of the phenylethanolamine N-methyltransferase enzyme.""",
                meaning=CL["0000459"]))
        setattr(cls, "CL:0000765",
            PermissibleValue(
                text="CL:0000765",
                description="A nucleated precursor of an erythrocyte that lacks hematopoietic lineage markers.",
                meaning=CL["0000765"]))
        setattr(cls, "CL:1000340",
            PermissibleValue(
                text="CL:1000340",
                description="An enterocyte that is part of the epithelium proper of duodenum.",
                meaning=CL["1000340"]))
        setattr(cls, "CL:4033034",
            PermissibleValue(
                text="CL:4033034",
                description="""An ON bipolar cell with a small dendritic tree that forms most of the central (invaginating) elements opposite the synaptic ribbon at the cone triad.""",
                meaning=CL["4033034"]))
        setattr(cls, "CL:0002171",
            PermissibleValue(
                text="CL:0002171",
                description="""A rounded or elliptical epithelial cell, with pale-staining open face nucleus and pale cytoplasm rich in free ribosomes and clusters of centrioles; form a distinct basal zone spaced slightly from the basal surface of the epithelium.""",
                meaning=CL["0002171"]))
        setattr(cls, "CL:0000318",
            PermissibleValue(
                text="CL:0000318",
                description="""A cell secreting sweat, the fluid excreted by the sweat glands of mammals. It consists of water containing sodium chloride, phosphate, urea, ammonia, and other waste products.""",
                meaning=CL["0000318"]))
        setattr(cls, "CL:1000615",
            PermissibleValue(
                text="CL:1000615",
                description="Any kidney tubule cell that is part of some renal cortex tubule.",
                meaning=CL["1000615"]))
        setattr(cls, "CL:4052014",
            PermissibleValue(
                text="CL:4052014",
                description="""A capillary endothelial cell that is part of islet of Langerhans, characterized by a high density of fenestrations —approximately ten times greater than those in exocrine pancreatic capillaries. These fenestrations facilitate efficient hormone exchange, which is essential for maintaining glucose homeostasis. The cell's structure and function are regulated by the local production of vascular endothelial growth factor-A (VEGF-A), which maintains its fenestrated architecture.""",
                meaning=CL["4052014"]))
        setattr(cls, "CL:4052005",
            PermissibleValue(
                text="CL:4052005",
                description="""A fibroblast that is part of the subserosa of intestine. This cell interacts with immune cells and play roles in inflammation and fibrosis. In certain conditions, such as Crohn's disease, subserosal fibroblast may differentiate into myofibroblasts.""",
                meaning=CL["4052005"]))
        setattr(cls, "CL:0002005",
            PermissibleValue(
                text="CL:0002005",
                description="""A megakaryocyte erythroid progenitor cell is CD34-positive, CD38-positive and is IL3-receptor alpha-negative and CD45RA-negative.""",
                meaning=CL["0002005"]))
        setattr(cls, "CL:0002377",
            PermissibleValue(
                text="CL:0002377",
                description="""A glial cell that develops from a Schwann cell precursor. The immature Schwann cell is embedded among neurons (axons) with minimal extracellular spaces separating them from nerve cell membranes and has a basal lamina. Cells can survive without an axon present. Immature Schwann cell can be found communally ensheathing large groups of axons.""",
                meaning=CL["0002377"]))
        setattr(cls, "CL:0009047",
            PermissibleValue(
                text="CL:0009047",
                description="A macrophage found in the medullary sinus of the lymph node.",
                meaning=CL["0009047"]))
        setattr(cls, "CL:0002309",
            PermissibleValue(
                text="CL:0002309",
                description="""A basophil chromphil cell of the anterior pitiutary gland that produce adrenocorticotropic hormone, melanocyte-stimulating hormone and lipotropin. This cell type is irregular in shape and has short dendritic processes which are inserted among other neighboring cells;""",
                meaning=CL["0002309"]))
        setattr(cls, "CL:0000412",
            PermissibleValue(
                text="CL:0000412",
                description="A cell that contains more than two haploid sets of chromosomes.",
                meaning=CL["0000412"]))
        setattr(cls, "CL:4047002",
            PermissibleValue(
                text="CL:4047002",
                description="A(n) glial cell that is cycling.",
                meaning=CL["4047002"]))
        setattr(cls, "CL:1000412",
            PermissibleValue(
                text="CL:1000412",
                description="An endothelial cell that is part of the arteriole.",
                meaning=CL["1000412"]))
        setattr(cls, "CL:0002049",
            PermissibleValue(
                text="CL:0002049",
                description="""A precursor B cell that is CD45R-positive, CD43-positive, CD24-positive, and BP-positive. Intracellularly expression of surrogate light chain, Rag1 and Rag2, TdT, occurs while there is no expression of mu heavy chain.""",
                meaning=CL["0002049"]))
        setattr(cls, "CL:0000034",
            PermissibleValue(
                text="CL:0000034",
                description="""A relatively undifferentiated cell that retains the ability to divide and proliferate throughout life to provide progenitor cells that can differentiate into specialized cells.""",
                meaning=CL["0000034"]))
        setattr(cls, "CL:0002325",
            PermissibleValue(
                text="CL:0002325",
                description="""A milk-producing glandular epithelial cell that is part of a mammary gland alveolus and differentiates from a luminal adaptive secretory precursor cell during secretory differentiation (also termed lactogenesis I). Following secretory activation (also termed lactogenesis II), a lactocyte is involved in the synthesis and/or transport of milk constituents including proteins, oligosaccharides, lactose, micronutrients, fat, hormones, immunoglobulins, and cytokines into the lumen of the lactating mammary gland.""",
                meaning=CL["0002325"]))
        setattr(cls, "CL:2000004",
            PermissibleValue(
                text="CL:2000004",
                description="Any cell that is part of a pituitary gland.",
                meaning=CL["2000004"]))
        setattr(cls, "CL:0002330",
            PermissibleValue(
                text="CL:0002330",
                description="An undifferentiated columnar cell of the bronchus epithelium",
                meaning=CL["0002330"]))
        setattr(cls, "CL:0002400",
            PermissibleValue(
                text="CL:0002400",
                description="""A precursor B cell that is AA4-positive, IgM-negative, CD19-positive, CD43-positive and HSA-positive.""",
                meaning=CL["0002400"]))
        setattr(cls, "CL:4023001",
            PermissibleValue(
                text="CL:4023001",
                description="A beta motor neuron that innervates nuclear chain fibers.",
                meaning=CL["4023001"]))
        setattr(cls, "CL:2000022",
            PermissibleValue(
                text="CL:2000022",
                description="Any native cell that is part of a cardiac septum.",
                meaning=CL["2000022"]))
        setattr(cls, "CL:4030061",
            PermissibleValue(
                text="CL:4030061",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in cortical layer 3.""",
                meaning=CL["4030061"]))
        setattr(cls, "CL:0000879",
            PermissibleValue(
                text="CL:0000879",
                description="""A border associated macrophage that is part of a meninx. This macrophage type is elongated and amoeboid spindle-shaped with limited mobility. This macrophage is highly phagocytic, expresses scavenger receptors, has dynamic protrusions and extends its processes during inflammation.""",
                meaning=CL["0000879"]))
        setattr(cls, "CL:4023052",
            PermissibleValue(
                text="CL:4023052",
                description="A Betz cell that synapses with lower motor neurons directly.",
                meaning=CL["4023052"]))
        setattr(cls, "CL:0000800",
            PermissibleValue(
                text="CL:0000800",
                description="""A gamma-delta T cell that has a mature phenotype. These cells can be found in tissues and circulation where they express unique TCR repertoire depending on their location.""",
                meaning=CL["0000800"]))
        setattr(cls, "CL:0002566",
            PermissibleValue(
                text="CL:0002566",
                description="A melanocyte that appears darker due to content or amount of melanin granules.",
                meaning=CL["0002566"]))
        setattr(cls, "CL:0002216",
            PermissibleValue(
                text="CL:0002216",
                description="""An intermediate muscle cell that has characteristics of both fast and slow muscle cells.""",
                meaning=CL["0002216"]))
        setattr(cls, "CL:0000808",
            PermissibleValue(
                text="CL:0000808",
                description="""A thymocyte that has the phenotype CD4-negative, CD8-negative, CD44-negative, CD25-negative, and pre-TCR-positive.""",
                meaning=CL["0000808"]))
        setattr(cls, "CL:4042003",
            PermissibleValue(
                text="CL:4042003",
                description="""A central nervous system macrophage that is part of a choroid plexus, a meninx and a perivascular space. A border associated macrophage interacts with various components of the CNS vasculature and meninges, it participates in immune surveillance and in the regulation of the blood brain barrier.""",
                meaning=CL["4042003"]))
        setattr(cls, "CL:0000673",
            PermissibleValue(
                text="CL:0000673",
                description="""An intrinsic neuron of the mushroom body of arthropods and annelids. They have tightly packed, cytoplasm-poor cell bodies.""",
                meaning=CL["0000673"]))
        setattr(cls, "CL:2000034",
            PermissibleValue(
                text="CL:2000034",
                description="Any neuromast hair cell that is part of a anterior lateral line.",
                meaning=CL["2000034"]))
        setattr(cls, "CL:0000143",
            PermissibleValue(
                text="CL:0000143",
                meaning=CL["0000143"]))
        setattr(cls, "CL:0000625",
            PermissibleValue(
                text="CL:0000625",
                description="A T cell expressing an alpha-beta T cell receptor and the CD8 coreceptor.",
                meaning=CL["0000625"]))
        setattr(cls, "CL:1000693",
            PermissibleValue(
                text="CL:1000693",
                meaning=CL["1000693"]))
        setattr(cls, "CL:0000567",
            PermissibleValue(
                text="CL:0000567",
                meaning=CL["0000567"]))
        setattr(cls, "CL:1001597",
            PermissibleValue(
                text="CL:1001597",
                description="Glandular cell of seminal vesicle epithelium.",
                meaning=CL["1001597"]))
        setattr(cls, "CL:1000223",
            PermissibleValue(
                text="CL:1000223",
                description="""A neuroendocrine cell that is part of respiratory epithelium of the lung and is involved in the sensory detection of environmental stimuli, including hypoxia, nicotine and air pressure. Ultrastructurally, this cell type is characterized by the presence of cytoplasmic dense core granules, which are considered the storage sites of amine and peptide hormones. Pulmonary neuroendocrine cells are innervated and appear as solitary cells or as clustered masses, localized at airway bifurcation sites, called neuroepithelial bodies that can release serotonin in response to hypoxia and interact with sensory nerve terminals. Pulmonary neuroendocrine cells also function as reserve stem cells that repair the surrounding epithelium after injury.""",
                meaning=CL["1000223"]))
        setattr(cls, "CL:0000445",
            PermissibleValue(
                text="CL:0000445",
                meaning=CL["0000445"]))
        setattr(cls, "CL:4023089",
            PermissibleValue(
                text="CL:4023089",
                description="""A basket cell which has simpler dendritic arbors (compared to small or large basket cells), and an axonal plexus of intermediate density, composed of a few long, smooth axonal branches.""",
                meaning=CL["4023089"]))
        setattr(cls, "CL:0002579",
            PermissibleValue(
                text="CL:0002579",
                description="A preadipocyte that is part of an omentum.",
                meaning=CL["0002579"]))
        setattr(cls, "CL:1000314",
            PermissibleValue(
                text="CL:1000314",
                description="A goblet cell that is part of the epithelium of gastric cardiac gland.",
                meaning=CL["1000314"]))
        setattr(cls, "CL:0004237",
            PermissibleValue(
                text="CL:0004237",
                description="""A retinal amacrine cell with a medium dendritic field and post-synaptic terminals in S1, S2, S3, and S4. This cell type releases the neurotransmitter gamma-aminobutyric acid (GABA).""",
                meaning=CL["0004237"]))
        setattr(cls, "CL:1000479",
            PermissibleValue(
                text="CL:1000479",
                description="A Purkinje myocyte that is part of the atrioventricular node.",
                meaning=CL["1000479"]))
        setattr(cls, "CL:0007004",
            PermissibleValue(
                text="CL:0007004",
                description="""Cell that is part of the neural crest region of the neuroepithelium, prior to migration. Note that not all premigratory neural crest cells may become migratory neural crest cells.""",
                meaning=CL["0007004"]))
        setattr(cls, "CL:4030042",
            PermissibleValue(
                text="CL:4030042",
                description="""A ciliated cell of the endometrial glandular epithelium. This cell is characterized by the presence of motile cilia on its apical surface.""",
                meaning=CL["4030042"]))
        setattr(cls, "CL:0000354",
            PermissibleValue(
                text="CL:0000354",
                meaning=CL["0000354"]))
        setattr(cls, "CL:0000793",
            PermissibleValue(
                text="CL:0000793",
                description="""A CD4-positive, alpha-beta T cell that is found in the columnar epithelium of the gastrointestinal tract.""",
                meaning=CL["0000793"]))
        setattr(cls, "CL:1000362",
            PermissibleValue(
                text="CL:1000362",
                description="A transitional myocyte that is part of the interventricular septum.",
                meaning=CL["1000362"]))
        setattr(cls, "CL:0002339",
            PermissibleValue(
                text="CL:0002339",
                description="""A prostate epithelial cell that is CD133-positive, CD44-positive, integrin A2beta3-high. This cell is a stem cell for the prostate epithelium.""",
                meaning=CL["0002339"]))
        setattr(cls, "CL:0002247",
            PermissibleValue(
                text="CL:0002247",
                description="A tissue macrophage that is in the pleural space.",
                meaning=CL["0002247"]))
        setattr(cls, "CL:0002211",
            PermissibleValue(
                text="CL:0002211",
                description="""A slow muscle cell that has large amounts of myoglobin, stores energy as triglycerides, generates ATP by the oxidative method and is resistant to fatigue.""",
                meaning=CL["0002211"]))
        setattr(cls, "CL:0000655",
            PermissibleValue(
                text="CL:0000655",
                description="A secondary oocyte is an oocyte that has not completed meiosis II.",
                meaning=CL["0000655"]))
        setattr(cls, "CL:4023015",
            PermissibleValue(
                text="CL:4023015",
                description="""A transcriptomically distinct GABAergic neuron located in the cerebral cortex that expresses Gamma-synuclein. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: CGE-derived interneurons', Author Categories: 'CrossArea_subclass', clusters Sncg.""",
                meaning=CL["4023015"]))
        setattr(cls, "CL:0000814",
            PermissibleValue(
                text="CL:0000814",
                description="""A mature alpha-beta T cell of a distinct lineage that bears natural killer markers and a T cell receptor specific for a limited set of ligands. NK T cells have activation and regulatory roles particularly early in an immune response.""",
                meaning=CL["0000814"]))
        setattr(cls, "CL:0002298",
            PermissibleValue(
                text="CL:0002298",
                description="""A thymic epithelial cell type with low nuclear and cytoplasmic electrondensity; has a round, euchromatic nucleus and occurs in small groups at the corticomedullary junction or scattered singly in the medulla.""",
                meaning=CL["0002298"]))
        setattr(cls, "CL:0000011",
            PermissibleValue(
                text="CL:0000011",
                description="""Cell that is part of the migratory trunk neural crest population. Migratory trunk neural crest cells develop from premigratory trunk neural crest cells and have undergone epithelial to mesenchymal transition and delamination.""",
                meaning=CL["0000011"]))
        setattr(cls, "CL:0000669",
            PermissibleValue(
                text="CL:0000669",
                description="""An elongated, contractile cell found wrapped about precapillary arterioles outside the basement membrane. Pericytes are present in capillaries where proper adventitia and muscle layer are missing (thus distingushing this cell type from adventitial cells). They are relatively undifferentiated and may become fibroblasts, macrophages, or smooth muscle cells.""",
                meaning=CL["0000669"]))
        setattr(cls, "CL:0000125",
            PermissibleValue(
                text="CL:0000125",
                description="""A non-neuronal cell of the nervous system. They not only provide physical support, but also respond to injury, regulate the ionic and chemical composition of the extracellular milieu. Guide neuronal migration during development, and exchange metabolites with neurons.""",
                meaning=CL["0000125"]))
        setattr(cls, "CL:1000453",
            PermissibleValue(
                text="CL:1000453",
                description="An epithelial cell that is part of the intermediate tubule.",
                meaning=CL["1000453"]))
        setattr(cls, "CL:0002028",
            PermissibleValue(
                text="CL:0002028",
                description="""A cell type that can give rise to basophil and mast cells. This cell is CD34-positive, CD117-positive, CD125-positive, FceRIa-negative, and T1/ST2-negative, and expresses Gata-1, Gata-2, C/EBPa""",
                meaning=CL["0002028"]))
        setattr(cls, "CL:0000222",
            PermissibleValue(
                text="CL:0000222",
                description="A cell of the middle germ layer of the embryo.",
                meaning=CL["0000222"]))
        setattr(cls, "CL:0002397",
            PermissibleValue(
                text="CL:0002397",
                description="A CD14-positive monocyte that is also CD16-positive and CCR2-negative.",
                meaning=CL["0002397"]))
        setattr(cls, "CL:1000618",
            PermissibleValue(
                text="CL:1000618",
                description="Any kidney cortical cell that is part of some juxtaglomerular apparatus.",
                meaning=CL["1000618"]))
        setattr(cls, "CL:0002634",
            PermissibleValue(
                text="CL:0002634",
                description="An epithelial cell of the anal column.",
                meaning=CL["0002634"]))
        setattr(cls, "CL:4033040",
            PermissibleValue(
                text="CL:4033040",
                description="A lung resident memory CD8-positive, alpha-beta T cell that is CD103-positive.",
                meaning=CL["4033040"]))
        setattr(cls, "CL:0011003",
            PermissibleValue(
                text="CL:0011003",
                description="""A neurosecretory neuron residing mainly in the hypothalamic supraoptic and paraventricular nuclei and in a number of smaller accessory cell groups between these two nuclei, that is capable of secreting the hormones oxytocin or vasopressin, and sometimes both, into the systemic circulation.""",
                meaning=CL["0011003"]))
        setattr(cls, "CL:0002459",
            PermissibleValue(
                text="CL:0002459",
                description="A dermal dendritic cell that is langerin-negative, CD103-negative, and CD11b-positive.",
                meaning=CL["0002459"]))
        setattr(cls, "CL:0002237",
            PermissibleValue(
                text="CL:0002237",
                description="A cell that constitutes the luminal layer of epithelium of prostatic duct.",
                meaning=CL["0002237"]))
        setattr(cls, "CL:0002521",
            PermissibleValue(
                text="CL:0002521",
                description="An adipocyte that is part of subcutaneous adipose tissue.",
                meaning=CL["0002521"]))
        setattr(cls, "CL:0002244",
            PermissibleValue(
                text="CL:0002244",
                description="A stratified squamous epithelial cell located in the ectocervix.",
                meaning=CL["0002244"]))
        setattr(cls, "CL:0000498",
            PermissibleValue(
                text="CL:0000498",
                description="""An interneuron (also called relay neuron, association neuron or local circuit neuron) is a multipolar neuron which connects afferent neurons and efferent neurons in neural pathways. Like motor neurons, interneuron cell bodies are always located in the central nervous system (CNS).""",
                meaning=CL["0000498"]))
        setattr(cls, "CL:0002547",
            PermissibleValue(
                text="CL:0002547",
                description="A fibroblast of the aortic adventitia.",
                meaning=CL["0002547"]))
        setattr(cls, "CL:0017002",
            PermissibleValue(
                text="CL:0017002",
                description="A neuroendocrine cell that is part of the prostate epithelium.",
                meaning=CL["0017002"]))
        setattr(cls, "CL:0002421",
            PermissibleValue(
                text="CL:0002421",
                description="""A reticulocyte that retains the nucleus and other organelles. Found in birds, fish, amphibians and reptiles.""",
                meaning=CL["0002421"]))
        setattr(cls, "CL:4033057",
            PermissibleValue(
                text="CL:4033057",
                description="""A luminal epithelial cell of the mammary gland that can proliferate and has the potential to differentiate into a lactocyte during pregnancy. In humans, a luminal adaptive secretory precursor cell can be identified by high levels of the markers EpCAM and CD49f, and in mice it can be identified by low levels of CD29 and high levels of CD14, Kit, CD61, and Tspan8.""",
                meaning=CL["4033057"]))
        setattr(cls, "CL:1001016",
            PermissibleValue(
                text="CL:1001016",
                description="""Any kidney loop of Henle epithelial cell that is part of some ascending limb of loop of Henle.""",
                meaning=CL["1001016"]))
        setattr(cls, "CL:0002109",
            PermissibleValue(
                text="CL:0002109",
                description="""A B220-positive CD38-positive naive B cell is a CD38-positive naive B cell that has the phenotype B220-positive, CD38-positive, surface IgD-positive, surface IgM-positive, and CD27-negative, and that has not yet been activated by antigen in the periphery.""",
                meaning=CL["0002109"]))
        setattr(cls, "CL:1000274",
            PermissibleValue(
                text="CL:1000274",
                description="""An extraembryonic cell that is part of the trophectoderm, representing the first lineage to differentiate in the embryo. This cell is crucial for implantation into the uterine wall and differentiates into trophoblast cells, which contribute to placenta formation and facilitate maternal-fetal nutrient and signal exchange.""",
                meaning=CL["1000274"]))
        setattr(cls, "CL:0000591",
            PermissibleValue(
                text="CL:0000591",
                description="A thermoreceptor cell that detects increased temperatures.",
                meaning=CL["0000591"]))
        setattr(cls, "CL:0000699",
            PermissibleValue(
                text="CL:0000699",
                description="A type of glomus or chief cell, is sensitive to hypoxia and produce catecholamines.",
                meaning=CL["0000699"]))
        setattr(cls, "CL:0002644",
            PermissibleValue(
                text="CL:0002644",
                description="""An endothelial cell of viscerocranial mucosa that is part of the tympanic region of the viscerocranial mucosa.""",
                meaning=CL["0002644"]))
        setattr(cls, "CL:0000319",
            PermissibleValue(
                text="CL:0000319",
                description="Any cell that is capable of some mucus secretion.",
                meaning=CL["0000319"]))
        setattr(cls, "CL:0002137",
            PermissibleValue(
                text="CL:0002137",
                description="A cell in the zona reticularis that produce sex hormones.",
                meaning=CL["0002137"]))
        setattr(cls, "CL:4047044",
            PermissibleValue(
                text="CL:4047044",
                description="""An enteric glial cell that has an elongated, fibrous morphology with long processes that run parallel to nerve fibers connecting enteric myenteric ganglia. This cell is located in the interganglionic fiber tracts of the enteric nervous system.""",
                meaning=CL["4047044"]))
        setattr(cls, "CL:0000413",
            PermissibleValue(
                text="CL:0000413",
                description="A cell whose nucleus contains a single haploid genome.",
                meaning=CL["0000413"]))
        setattr(cls, "CL:0000100",
            PermissibleValue(
                text="CL:0000100",
                description="""An efferent neuron that passes from the central nervous system or a ganglion toward or to a muscle and conducts an impulse that causes or inhibits movement.""",
                meaning=CL["0000100"]))
        setattr(cls, "CL:0000490",
            PermissibleValue(
                text="CL:0000490",
                meaning=CL["0000490"]))
        setattr(cls, "CL:0002628",
            PermissibleValue(
                text="CL:0002628",
                description="An immature microglial cell with a ramified morphology.",
                meaning=CL["0002628"]))
        setattr(cls, "CL:0000933",
            PermissibleValue(
                text="CL:0000933",
                description="""A type II NK T cell that has been recently activated, secretes interleukin-4, and has the phenotype CD69-positive and downregulated NK markers.""",
                meaning=CL["0000933"]))
        setattr(cls, "CL:0000679",
            PermissibleValue(
                text="CL:0000679",
                description="A neuron that is capable of some neurotansmission by glutamate secretion.",
                meaning=CL["0000679"]))
        setattr(cls, "CL:0002572",
            PermissibleValue(
                text="CL:0002572",
                description="A mesenchymal stem cell of the vertebrae.",
                meaning=CL["0002572"]))
        setattr(cls, "CL:0010022",
            PermissibleValue(
                text="CL:0010022",
                description="A neuron that has its soma in the heart.",
                meaning=CL["0010022"]))
        setattr(cls, "CL:0004239",
            PermissibleValue(
                text="CL:0004239",
                description="""A bistratified amacrine cell with a medium dendritic field and post-synaptic terminals in S1-S2, and S4.""",
                meaning=CL["0004239"]))
        setattr(cls, "CL:0005001",
            PermissibleValue(
                text="CL:0005001",
                description="""A non-terminally differentiated cell that originates from the neural crest and differentiates into an iridophore.""",
                meaning=CL["0005001"]))
        setattr(cls, "CL:0000691",
            PermissibleValue(
                text="CL:0000691",
                description="Any interneuron that has characteristic some stellate morphology.",
                meaning=CL["0000691"]))
        setattr(cls, "CL:2000015",
            PermissibleValue(
                text="CL:2000015",
                description="Any skin fibroblast that is part of a arm.",
                meaning=CL["2000015"]))
        setattr(cls, "CL:0002586",
            PermissibleValue(
                text="CL:0002586",
                description="An epithelial cell of the retinal pigmented epithelium.",
                meaning=CL["0002586"]))
        setattr(cls, "CL:1000696",
            PermissibleValue(
                text="CL:1000696",
                meaning=CL["1000696"]))
        setattr(cls, "CL:0008053",
            PermissibleValue(
                text="CL:0008053",
                description="""A capillary endothelial cell that is part of the circumventricular organs (CVOs), characterized by fenestrations that facilitate selective permeability to molecules, distinguishing it from the non-fenestrated endothelial cells of the blood-brain barrier. This cell is integral to the unique vascular structure of CVOs, which lack a traditional blood-brain barrier. It enables bidirectional exchange of polar molecules between blood and neural tissue, supporting neuroendocrine signaling, fluid balance, and immune responses. It is marked by the expression of PLVAP, a component of the fenestral diaphragm, in both rodents and humans.""",
                meaning=CL["0008053"]))
        setattr(cls, "CL:0000453",
            PermissibleValue(
                text="CL:0000453",
                description="""Langerhans cell is a conventional dendritic cell that has plasma membrane part CD207. A Langerhans cell is a stellate dendritic cell of myeloid origin, that appears clear on light microscopy and has a dark-staining, indented nucleus and characteristic inclusions (Birbeck granules) in the cytoplasm; Langerhans cells are found principally in the stratum spinosum of the epidermis, but they also occur in other stratified epithelia and have been identified in the lung, lymph nodes, spleen, and thymus.""",
                meaning=CL["0000453"]))
        setattr(cls, "CL:0002222",
            PermissibleValue(
                text="CL:0002222",
                description="""A cell comprising the transparent, biconvex body separating the posterior chamber and vitreous body, and constituting part of the refracting mechanism of the mammalian eye.""",
                meaning=CL["0002222"]))
        setattr(cls, "CL:4033084",
            PermissibleValue(
                text="CL:4033084",
                description="""A granulosa cell that has a cuboidal morphology and develops from squamous granulosa cell during the transition between primordial follicle to primary follicle. Cuboidal granulosa cells proliferate to form a second layer within secondary follicles.""",
                meaning=CL["4033084"]))
        setattr(cls, "CL:0000770",
            PermissibleValue(
                text="CL:0000770",
                description="""A late basophilic metamyelocyte in which the nucleus is in the form of a curved or coiled band, not having acquired the typical multilobar shape of the mature basophil.""",
                meaning=CL["0000770"]))
        setattr(cls, "CL:0000823",
            PermissibleValue(
                text="CL:0000823",
                description="""A natural killer cell that is developmentally immature and expresses natural killer cell receptors (NKR).""",
                meaning=CL["0000823"]))
        setattr(cls, "CL:0005018",
            PermissibleValue(
                text="CL:0005018",
                description="A cell that secretes ghrelin, the peptide hormone that stimulates hunger.",
                meaning=CL["0005018"]))
        setattr(cls, "CL:1000378",
            PermissibleValue(
                text="CL:1000378",
                description="A type I vestibular sensory cell that is part of the stato-acoustic epithelium.",
                meaning=CL["1000378"]))
        setattr(cls, "CL:0002536",
            PermissibleValue(
                text="CL:0002536",
                description="An epithelial cell that is part of the amnion.",
                meaning=CL["0002536"]))
        setattr(cls, "CL:0000758",
            PermissibleValue(
                text="CL:0000758",
                description="""An ON-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the inner half of the inner plexiform layer. The cell has a loose, delicate axon terminal that opens in sublamina 3 of the inner plexiform layer and descends into sublamina 4.""",
                meaning=CL["0000758"]))
        setattr(cls, "CL:2000036",
            PermissibleValue(
                text="CL:2000036",
                description="Any neuromast support cell that is part of a anterior lateral line.",
                meaning=CL["2000036"]))
        setattr(cls, "CL:0002610",
            PermissibleValue(
                text="CL:0002610",
                description="A neuron of the raphe nuclei.",
                meaning=CL["0002610"]))
        setattr(cls, "CL:4023031",
            PermissibleValue(
                text="CL:4023031",
                description="""A sst GABAergic cortical interneuron with a soma found in lower L2/3 and upper 5, L4 Sst cells have Martinotti morphology with ascending axons but denser local axons and sparser ‘fanning-out’ projections to L1. L4 sst cells have smaller membrane time constant to calb2 (L2/3/5 fan Martinotti Cell) and non-zero afterdepolarization (ADP).""",
                meaning=CL["4023031"]))
        setattr(cls, "CL:0002145",
            PermissibleValue(
                text="CL:0002145",
                description="""A multi-ciliated epithelial cell located in the trachea and bronchi, characterized by a columnar shape and motile cilia on its apical surface. These cilia facilitate mucociliary clearance by moving mucus and trapped particles toward the pharynx.""",
                meaning=CL["0002145"]))
        setattr(cls, "CL:0000965",
            PermissibleValue(
                text="CL:0000965",
                description="""A germinal center B cell that is rapidly dividing and has the phenotype IgD-negative, CD38-positive, and CD77-positive. Somatic hypermutation of the immunoglobulin V gene region can occur during proliferation of this cell type.""",
                meaning=CL["0000965"]))
        setattr(cls, "CL:1000494",
            PermissibleValue(
                text="CL:1000494",
                description="An epithelial cell that is part of a nephron tubule.",
                meaning=CL["1000494"]))
        setattr(cls, "CL:0011115",
            PermissibleValue(
                text="CL:0011115",
                description="""A cell that, by division or terminal differentiation, can give rise to other cell types.""",
                meaning=CL["0011115"]))
        setattr(cls, "CL:0002527",
            PermissibleValue(
                text="CL:0002527",
                description="An immature CD14-positive dermal dendritic cell is CD80-low, CD86-low, and MHCII-low.",
                meaning=CL["0002527"]))
        setattr(cls, "CL:0009113",
            PermissibleValue(
                text="CL:0009113",
                description="""A regulatory T cell present in the B cell follicles and germinal centers of lymphoid tissues. In humans, it is CXCR5+.""",
                meaning=CL["0009113"]))
        setattr(cls, "CL:0009012",
            PermissibleValue(
                text="CL:0009012",
                description="""A rapidly proliferating population of cells that differentiate from stem cells of the intestinal crypt of the small intestine. Stem cells located in the crypts of Lieberkühn give rise to proliferating progenitor or transit amplifying cells that differentiate into the four major epithelial cell types. These include columnar absorptive cells or enterocytes, mucous secreting goblet cells, enteroendocrine cells and paneth cells.""",
                meaning=CL["0009012"]))
        setattr(cls, "CL:0000628",
            PermissibleValue(
                text="CL:0000628",
                description="""A cell that can perform photosynthesis, in which carbohydrates are synthesized from carbon dioxide and water, using light as the energy source.""",
                meaning=CL["0000628"]))
        setattr(cls, "CL:0000712",
            PermissibleValue(
                text="CL:0000712",
                description="Any epidermal cell that is part of some stratum granulosum of epidermis.",
                meaning=CL["0000712"]))
        setattr(cls, "CL:0000099",
            PermissibleValue(
                text="CL:0000099",
                description="""Most generally any neuron which is not motor or sensory. Interneurons may also refer to neurons whose axons remain within a particular brain region as contrasted with projection neurons which have axons projecting to other brain regions.""",
                meaning=CL["0000099"]))
        setattr(cls, "CL:4023024",
            PermissibleValue(
                text="CL:4023024",
                description="""A lamp5 GABAergic cortical interneuron with layer-adapting morphology. NGC lamp5 cells have a small round soma, short dendrites, and a wide dense axonal arbor that tends to establish a dense axonal mesh with high connection probability both to themselves and L2 pyramidal cells. NGC lamp5 cells have unique synaptic properties that distinguish them from other GABAergic interneurons, including the release of GABA to the extracellular space via volume transmission, and the ability to produce GABA-B responses in connected postsynaptic targets.""",
                meaning=CL["4023024"]))
        setattr(cls, "CL:4023095",
            PermissibleValue(
                text="CL:4023095",
                description="""A pyramidal neuron which lacks a clear tuft formation but extends to large radial distances.""",
                meaning=CL["4023095"]))
        setattr(cls, "CL:0000639",
            PermissibleValue(
                text="CL:0000639",
                description="A basophilic chromophil cell that of the anterior pituitary gland.",
                meaning=CL["0000639"]))
        setattr(cls, "CL:0002104",
            PermissibleValue(
                text="CL:0002104",
                description="""An IgG-negative double negative memory B cell is a double negative memory B cell with the phenotype IgG-negative, IgD-negative, and CD27-negative.""",
                meaning=CL["0002104"]))
        setattr(cls, "CL:0000385",
            PermissibleValue(
                text="CL:0000385",
                description="A precursor of mature hemocytes.",
                meaning=CL["0000385"]))
        setattr(cls, "CL:0000359",
            PermissibleValue(
                text="CL:0000359",
                description="A smooth muscle cell associated with the vasculature.",
                meaning=CL["0000359"]))
        setattr(cls, "CL:0002619",
            PermissibleValue(
                text="CL:0002619",
                description="""An adult angioblastic cell released from the bone marrow, or from the kidney in some teleost species, capable of blood circulation and participation in angiogenesis by differentiating into blood vessel endothelial cells.""",
                meaning=CL["0002619"]))
        setattr(cls, "CL:0009107",
            PermissibleValue(
                text="CL:0009107",
                description="""A lymphatic endothelial cell located in the subcapsular sinus ceiling of a lymph node. In human, it's characterized by a unique marker expression (NT5e+ and Caveolin-1+).""",
                meaning=CL["0009107"]))
        setattr(cls, "CL:4042024",
            PermissibleValue(
                text="CL:4042024",
                description="A pthlh-expressing interneuron that expresses MOXD1 and has its soma in a striatum.",
                meaning=CL["4042024"]))
        setattr(cls, "CL:4023045",
            PermissibleValue(
                text="CL:4023045",
                description="""An extratelencephalic-projecting glutamatergic neuron located in layer 5b of the primary motor cortex that projects to the medulla. MY ET cells are large, big-tufted cells with the apical dendrite often bifurcating close to the soma, suggesting they are corticospinal cells. MY ET cells have bigger hyperpolarization sag, lower input resistance, and smaller AP width, compared to L5 IT neurons.""",
                meaning=CL["4023045"]))
        setattr(cls, "CL:4033023",
            PermissibleValue(
                text="CL:4033023",
                description="An epithelial cell that is part of a collecting duct of an airway submucosal gland.",
                meaning=CL["4033023"]))
        setattr(cls, "CL:4033015",
            PermissibleValue(
                text="CL:4033015",
                description="""A star-shaped glial cell that is part of some retina. This cell links neurons to blood vessels and may provide structural and physiological support to optic nerve head axons.""",
                meaning=CL["4033015"]))
        setattr(cls, "CL:0000528",
            PermissibleValue(
                text="CL:0000528",
                description="A nerve cell where transmission is mediated by nitric oxide.",
                meaning=CL["0000528"]))
        setattr(cls, "CL:0002032",
            PermissibleValue(
                text="CL:0002032",
                description="""A hematopoietic oligopotent progenitor cell that has the ability to differentiate into limited cell types but lacks lineage cell markers and self renewal capabilities.""",
                meaning=CL["0002032"]))
        setattr(cls, "CL:0002605",
            PermissibleValue(
                text="CL:0002605",
                description="A transcriptomically distinct astrocyte that is found in the cerebral cortex.",
                meaning=CL["0002605"]))
        setattr(cls, "CL:0011114",
            PermissibleValue(
                text="CL:0011114",
                description="""A segmented neutrophilic cell of the bone marrow reserve pool that expresses CD11b (integrin alpha-M) and high levels of CD16 (low affinity immunoglobulin gamma Fc region receptor III) on its cell surface.""",
                meaning=CL["0011114"]))
        setattr(cls, "CL:0001000",
            PermissibleValue(
                text="CL:0001000",
                description="""CD8-alpha-positive CD11b-negative dendritic cell is a conventional dendritic cell that is CD11b-negative, CD4-negative and is CD205-positive and CD8-alpha-positive.""",
                meaning=CL["0001000"]))
        setattr(cls, "CL:4042025",
            PermissibleValue(
                text="CL:4042025",
                description="""A midbrain dopaminergic neuron that has its soma located in a substantia nigra. This dopaminergic neuron type is highly metabolically active and it is involved in the regulation of movement, cognition, motivation and reward. Neurodegeneration of this dopaminergic neuronal type causes loss in fine motor control in Parkinson's Disease.""",
                meaning=CL["4042025"]))
        setattr(cls, "CL:0002021",
            PermissibleValue(
                text="CL:0002021",
                description="An enucleate erythrocyte that is GlyA-positive.",
                meaning=CL["0002021"]))
        setattr(cls, "CL:0007022",
            PermissibleValue(
                text="CL:0007022",
                description="""A specialized pore forming cell of the follicle, located adjacent to the animal pole of the oocyte. The micropylar cell makes the single micropyle (pore) through the chorion through which the sperm fertilizes the egg.""",
                meaning=CL["0007022"]))
        setattr(cls, "CL:0008044",
            PermissibleValue(
                text="CL:0008044",
                description="""A tanycyte of the area postrema (AP).  These cells extend long and slender fibers extending from their cell bodies in the ependyma toward fenestrated capillaries associated with the AP, where they form a dense network surrounding these capillaries.""",
                meaning=CL["0008044"]))
        setattr(cls, "CL:2000030",
            PermissibleValue(
                text="CL:2000030",
                description="Any native cell that is part of a hypothalamus.",
                meaning=CL["2000030"]))
        setattr(cls, "CL:0002081",
            PermissibleValue(
                text="CL:0002081",
                description="""This cell resembles a glia cell, express the glial marker S100 and act as a supporting cell to type I cell. This cell is located in a small cluster of type I and type II cells near the fork of the carotid artery.""",
                meaning=CL["0002081"]))
        setattr(cls, "CL:0000138",
            PermissibleValue(
                text="CL:0000138",
                description="""Skeletogenic cell that is terminally differentiated, secretes an avascular, GAG-rich matrix, is embedded in cartilage tissue matrix, retains the ability to divide, and develops from a chondroblast cell.""",
                meaning=CL["0000138"]))
        setattr(cls, "CL:0000943",
            PermissibleValue(
                text="CL:0000943",
                description="""A Be cell that facilitates development of T-helper 1 (Th1) phenotype in CD4-positive T cells, and secretes high levels of interleukin-2, tumor necrosis factor-alpha and interferon-gamma.""",
                meaning=CL["0000943"]))
        setattr(cls, "CL:0004234",
            PermissibleValue(
                text="CL:0004234",
                description="""An amacrine cell with a medium dendritic field and post-synaptic terminals in S2, and in S3-S4.""",
                meaning=CL["0004234"]))
        setattr(cls, "CL:0000119",
            PermissibleValue(
                text="CL:0000119",
                description="""Large intrinsic neuron located in the granule layer of the cerebellar cortex that extends its dendrites into the molecular layer where they receive contact from parallel fibers. The axon of the Golgi cell ramifies densely in the granule layer and enters into a complex arrangement with mossy fiber terminals and granule cell dendrites to form the cerebellar glomerulus. Llinas, Walton and Lang. In The Synaptic Organization of the Brain. 5th ed. 2004.""",
                meaning=CL["0000119"]))
        setattr(cls, "CL:1000339",
            PermissibleValue(
                text="CL:1000339",
                description="An enterocyte that is part of the epithelium proper of small intestine.",
                meaning=CL["1000339"]))
        setattr(cls, "CL:4042014",
            PermissibleValue(
                text="CL:4042014",
                description="""A VIP GABAergic cortical interneuron with a soma located in L1-3 of some neocortex in Mmus. This neuron has a multipolar morphology with spiny dendrites concentrating on L1 of the cortex, and has a burst firing electrophysiological signature with highly dynamic dendritic spines.""",
                meaning=CL["4042014"]))
        setattr(cls, "CL:0000959",
            PermissibleValue(
                text="CL:0000959",
                description="""A transitional stage B cell that has the phenotype surface IgM-positive, surface IgD-postive, CD21-positive, CD23-positive, CD62L-negative, CD93-positive and is located in the splenic B follicles. This cell type has also been described as IgM-high, CD19-positive, B220-positive, AA4-positive, and CD23-positive.""",
                meaning=CL["0000959"]))
        setattr(cls, "CL:0010005",
            PermissibleValue(
                text="CL:0010005",
                description="""A specialized cardiomyocyte that transmit signals from the AV node to the cardiac Purkinje fibers.""",
                meaning=CL["0010005"]))
        setattr(cls, "CL:0002020",
            PermissibleValue(
                text="CL:0002020",
                description="A reticulocyte that is GlyA-positive.",
                meaning=CL["0002020"]))
        setattr(cls, "CL:4023058",
            PermissibleValue(
                text="CL:4023058",
                description="A mesothelial fibroblast found in the leptomeninx.",
                meaning=CL["4023058"]))
        setattr(cls, "CL:0010002",
            PermissibleValue(
                text="CL:0010002",
                description="An epithelial cell that is part_of a umbilical artery.",
                meaning=CL["0010002"]))
        setattr(cls, "CL:4042035",
            PermissibleValue(
                text="CL:4042035",
                description="""A type of cerebellar inhibitory GABAergic interneuron that is located in the molecular layer of the cerebellum. This cell type inhibits Purkinje cells and other molecular layer interneurons. This interneuron plays a crucial role in regulating cerebellar output through feedforward inhibition and is characterized by its fast-spiking properties.""",
                meaning=CL["4042035"]))
        setattr(cls, "CL:0009064",
            PermissibleValue(
                text="CL:0009064",
                description="""A T cell located in the lymph node paracortex, where macrophages and dendritic cells present antigenic peptides to these naïve T cells, stimulating them to become activated helper T cells or cytotoxic T lymphocytes.""",
                meaning=CL["0009064"]))
        setattr(cls, "CL:4033004",
            PermissibleValue(
                text="CL:4033004",
                description="A(n) smooth muscle cell that is part of a(n) taenia coli.",
                meaning=CL["4033004"]))
        setattr(cls, "CL:0000449",
            PermissibleValue(
                text="CL:0000449",
                description="""A cell from the thermogenic form of adipose tissue found in many species,  particularly in newborns and hibernating mammals, but also in lesser amounts in adults of other mammals including humans. Brown fat is capable of rapid liberation of energy and seems to be important in the maintenance of body temperature immediately after birth and upon waking from hibernation.""",
                meaning=CL["0000449"]))
        setattr(cls, "CL:0000689",
            PermissibleValue(
                text="CL:0000689",
                description="A cell with both myofibrils and secretory granules.",
                meaning=CL["0000689"]))
        setattr(cls, "CL:0002334",
            PermissibleValue(
                text="CL:0002334",
                description="An undifferentiated fibroblast that can be stimulated to form a fat cell.",
                meaning=CL["0002334"]))
        setattr(cls, "CL:1000596",
            PermissibleValue(
                text="CL:1000596",
                description="Any kidney cell that is part of some juxtamedullary cortex.",
                meaning=CL["1000596"]))
        setattr(cls, "CL:0000343",
            PermissibleValue(
                text="CL:0000343",
                description="""A pigment cell that is capable of detecting light stimulus that is involved in visual perception.""",
                meaning=CL["0000343"]))
        setattr(cls, "CL:4023077",
            PermissibleValue(
                text="CL:4023077",
                description="""A type of interneuron that has two clusters of dendritic branches that originate directly from the soma and extend in opposite directions and axons that form a plexus which spreads widely. Compared to bipolar neurons, bitufted neurons have branching that occur close to the soma.""",
                meaning=CL["4023077"]))
        setattr(cls, "CL:4033074",
            PermissibleValue(
                text="CL:4033074",
                description="A(n) CD8-positive, alpha-beta T cell that is cycling.",
                meaning=CL["4033074"]))
        setattr(cls, "CL:0002316",
            PermissibleValue(
                text="CL:0002316",
                description="A supporting cell of the vestibular epithelium.",
                meaning=CL["0002316"]))
        setattr(cls, "CL:1000351",
            PermissibleValue(
                text="CL:1000351",
                description="A basal cell that is part of the epithelium of respiratory bronchiole.",
                meaning=CL["1000351"]))
        setattr(cls, "CL:0000517",
            PermissibleValue(
                text="CL:0000517",
                description="""A type of foam cell derived from a macrophage containing lipids in small vacuoles and typically seen in atherolosclerotic lesions, as well as other conditions.""",
                meaning=CL["0000517"]))
        setattr(cls, "CL:0000047",
            PermissibleValue(
                text="CL:0000047",
                description="""An undifferentiated neural cell that originates from the neuroectoderm and has the capacity both to perpetually self-renew without differentiating and to generate multiple central nervous system neuronal and glial cell types.""",
                meaning=CL["0000047"]))
        setattr(cls, "CL:0009001",
            PermissibleValue(
                text="CL:0009001",
                description="Any cell in the compound eye, a light sensing organ composed of ommatidia.",
                meaning=CL["0009001"]))
        setattr(cls, "CL:0002674",
            PermissibleValue(
                text="CL:0002674",
                description="A S. pombe mating type determined by the mat1-Mc and mat1-Mi on the mat1 locus.",
                meaning=CL["0002674"]))
        setattr(cls, "CL:0019002",
            PermissibleValue(
                text="CL:0019002",
                description="Any chondrocyte that is part of the tracheobronchial tree.",
                meaning=CL["0019002"]))
        setattr(cls, "CL:0002001",
            PermissibleValue(
                text="CL:0002001",
                description="""A granulocyte monocyte progenitor is CD34-positive, CD38-positive, IL-3receptor-alpha-positive and is CD45RA-negative.""",
                meaning=CL["0002001"]))
        setattr(cls, "CL:0002163",
            PermissibleValue(
                text="CL:0002163",
                description="""A rod-shpaed cell that forms a single row adjacent to and supporting the inner hair cells.""",
                meaning=CL["0002163"]))
        setattr(cls, "CL:0009053",
            PermissibleValue(
                text="CL:0009053",
                description="A stromal cell found in the lamina propria of the anorectum.",
                meaning=CL["0009053"]))
        setattr(cls, "CL:0000411",
            PermissibleValue(
                text="CL:0000411",
                description="An epithelial cell of the hypodermis of Caenorhabditis.",
                meaning=CL["0000411"]))
        setattr(cls, "CL:0005020",
            PermissibleValue(
                text="CL:0005020",
                description="Lymphatic progenitor cells.",
                meaning=CL["0005020"]))
        setattr(cls, "CL:0000785",
            PermissibleValue(
                text="CL:0000785",
                description="""A B cell that is mature, having left the bone marrow. Initially, these cells are IgM-positive and IgD-positive, and they can be activated by antigen.""",
                meaning=CL["0000785"]))
        setattr(cls, "CL:0008016",
            PermissibleValue(
                text="CL:0008016",
                description="""A skeletal muscle satellite cell that has become mitotically active - typically following muscle damage.""",
                meaning=CL["0008016"]))
        setattr(cls, "CL:0002438",
            PermissibleValue(
                text="CL:0002438",
                description="A mature NK cell that is NK1.1-positive.",
                meaning=CL["0002438"]))
        setattr(cls, "CL:0002328",
            PermissibleValue(
                text="CL:0002328",
                description="An epithelial cell of the bronchus.",
                meaning=CL["0002328"]))
        setattr(cls, "CL:0000253",
            PermissibleValue(
                text="CL:0000253",
                meaning=CL["0000253"]))
        setattr(cls, "CL:0004220",
            PermissibleValue(
                text="CL:0004220",
                description="An amacrine cell with a small, asymteric dendritic field.",
                meaning=CL["0004220"]))
        setattr(cls, "CL:0000075",
            PermissibleValue(
                text="CL:0000075",
                description="""A columnar/cuboidal epithelial cell is a cell usually found in a two dimensional sheet with a free surface. Columnar/cuboidal epithelial cells take on the shape of a column or cube.""",
                meaning=CL["0000075"]))
        setattr(cls, "CL:0002555",
            PermissibleValue(
                text="CL:0002555",
                description="A fibroblast that is part of the mammary gland.",
                meaning=CL["0002555"]))
        setattr(cls, "CL:0000379",
            PermissibleValue(
                text="CL:0000379",
                meaning=CL["0000379"]))
        setattr(cls, "CL:0000108",
            PermissibleValue(
                text="CL:0000108",
                description="A neuron that uses acetylcholine as a vesicular neurotransmitter.",
                meaning=CL["0000108"]))
        setattr(cls, "CL:0004226",
            PermissibleValue(
                text="CL:0004226",
                description="""An amacrine cell with a small dendritic field with post-synaptic terminals in S3 and S4.""",
                meaning=CL["0004226"]))
        setattr(cls, "CL:4033060",
            PermissibleValue(
                text="CL:4033060",
                description="""A lactocyte that highly expresses genes associated with lipid production and milk component biosynthesis.""",
                meaning=CL["4033060"]))
        setattr(cls, "CL:0002019",
            PermissibleValue(
                text="CL:0002019",
                description="A reticulocyte that is Ly76-high and is Kit-negative.",
                meaning=CL["0002019"]))
        setattr(cls, "CL:0000232",
            PermissibleValue(
                text="CL:0000232",
                description="""A red blood cell. In mammals, mature erythrocytes are biconcave disks containing hemoglobin whose function is to transport oxygen.""",
                meaning=CL["0000232"]))
        setattr(cls, "CL:0000704",
            PermissibleValue(
                text="CL:0000704",
                description="""A specialized endothelial cell that senses extracellular signals and guides the directed growth of blood vessels.""",
                meaning=CL["0000704"]))
        setattr(cls, "CL:0011008",
            PermissibleValue(
                text="CL:0011008",
                description="""A hemocyte derived from the embryonic head mesoderm, which enters the hemolymph as a circulating cell.""",
                meaning=CL["0011008"]))
        setattr(cls, "CL:1000303",
            PermissibleValue(
                text="CL:1000303",
                description="A fibroblast that is part of the areolar connective tissue.",
                meaning=CL["1000303"]))
        setattr(cls, "CL:0000018",
            PermissibleValue(
                text="CL:0000018",
                description="""A male germ cell that develops from the haploid secondary spermatocytes. Without further division, spermatids undergo structural changes and give rise to spermatozoa.""",
                meaning=CL["0000018"]))
        setattr(cls, "CL:0009088",
            PermissibleValue(
                text="CL:0009088",
                description="""An adult endothelial progenitor cell characterised in vivo by homing to ischemic sites and paracrine support of angiogenesis. These cells do not form colonies.""",
                meaning=CL["0009088"]))
        setattr(cls, "CL:0008034",
            PermissibleValue(
                text="CL:0008034",
                description="""Mural cells are pericytes and the vascular smooth muscle cells (vSMCs) of the microcirculation.""",
                meaning=CL["0008034"]))
        setattr(cls, "CL:1001611",
            PermissibleValue(
                text="CL:1001611",
                description="Neuron of the cerebellum.",
                meaning=CL["1001611"]))
        setattr(cls, "CL:0009020",
            PermissibleValue(
                text="CL:0009020",
                description="An intestinal tuft cell that is a part of a vermiform appendix.",
                meaning=CL["0009020"]))
        setattr(cls, "CL:2000061",
            PermissibleValue(
                text="CL:2000061",
                description="Any mesenchymal stem cell that is part of a placenta.",
                meaning=CL["2000061"]))
        setattr(cls, "CL:0000207",
            PermissibleValue(
                text="CL:0000207",
                description="""Any neuron that is capable of some detection of chemical stimulus involved in sensory perception of smell.""",
                meaning=CL["0000207"]))
        setattr(cls, "CL:0002117",
            PermissibleValue(
                text="CL:0002117",
                description="A class switched memory B cell that lacks IgG on the cell surface.",
                meaning=CL["0002117"]))
        setattr(cls, "CL:0000371",
            PermissibleValue(
                text="CL:0000371",
                description="The cell protoplasm after removal of the cell wall.",
                meaning=CL["0000371"]))
        setattr(cls, "CL:0002174",
            PermissibleValue(
                text="CL:0002174",
                description="A cell within the follicle of an ovary.",
                meaning=CL["0002174"]))
        setattr(cls, "CL:0001015",
            PermissibleValue(
                text="CL:0001015",
                description="""CD8-alpha-low Langerhans cell is a Langerhans cell that is CD205-high and is CD8-alpha-low.""",
                meaning=CL["0001015"]))
        setattr(cls, "CL:0000848",
            PermissibleValue(
                text="CL:0000848",
                description="""An olfactory receptor cell in which the apical ending of the dendrite is a knob that bears numerous microvilli.""",
                meaning=CL["0000848"]))
        setattr(cls, "CL:1001502",
            PermissibleValue(
                text="CL:1001502",
                description="""The large glutaminergic nerve cells whose dendrites synapse with axons of the olfactory receptor neurons in the glomerular layer of the olfactory bulb, and whose axons pass centrally in the olfactory tract to the olfactory cortex.""",
                meaning=CL["1001502"]))
        setattr(cls, "CL:4042007",
            PermissibleValue(
                text="CL:4042007",
                description="""An astrocyte with highly branched protrusions, found in neocortex layers 2-6. It is involved with the formation and elimination of synapses, glutamate clearance, modulation of synaptic functions and regulation of blood flow in response to synaptic activity.""",
                meaning=CL["4042007"]))
        setattr(cls, "CL:0010007",
            PermissibleValue(
                text="CL:0010007",
                description="Any cell that is part of some His-Purkinje system.",
                meaning=CL["0010007"]))
        setattr(cls, "CL:0008018",
            PermissibleValue(
                text="CL:0008018",
                description="A myoblast that is commited to developing into a somatic muscle.",
                meaning=CL["0008018"]))
        setattr(cls, "CL:0002097",
            PermissibleValue(
                text="CL:0002097",
                description="""A cell of the adrenal cortex. Cell types include those that synthesize and secrete chemical derivatives (steroids) of cholesterol.""",
                meaning=CL["0002097"]))
        setattr(cls, "CL:0002175",
            PermissibleValue(
                text="CL:0002175",
                description="A cell within the primary follicle of the ovary.",
                meaning=CL["0002175"]))
        setattr(cls, "CL:4052026",
            PermissibleValue(
                text="CL:4052026",
                description="""A fast type II muscle cell that is part of the skeletal muscle tissue. This cell is characterized by its intermediate metabolic profile, utilizing both glycolytic and oxidative pathways for energy production. In humans, it is distinguished by the expression of myosin heavy chain 1 (MYH1).""",
                meaning=CL["4052026"]))
        setattr(cls, "CL:1000410",
            PermissibleValue(
                text="CL:1000410",
                description="A muscle cell that is part of the atrioventricular node.",
                meaning=CL["1000410"]))
        setattr(cls, "CL:0008033",
            PermissibleValue(
                text="CL:0008033",
                description="A pericyte of the decidual vasculature.",
                meaning=CL["0008033"]))
        setattr(cls, "CL:0000209",
            PermissibleValue(
                text="CL:0000209",
                description="A specialized cell involved in gustatory sensory perception.",
                meaning=CL["0000209"]))
        setattr(cls, "CL:0003018",
            PermissibleValue(
                text="CL:0003018",
                description="A retinal ganglion B3 cell with dentrites terminating in S4.",
                meaning=CL["0003018"]))
        setattr(cls, "CL:0000027",
            PermissibleValue(
                text="CL:0000027",
                description="A smooth muscle cell derived from the neural crest.",
                meaning=CL["0000027"]))
        setattr(cls, "CL:0002170",
            PermissibleValue(
                text="CL:0002170",
                description="A keratinized cell located in the hard palate or gingiva.",
                meaning=CL["0002170"]))
        setattr(cls, "CL:0002262",
            PermissibleValue(
                text="CL:0002262",
                description="""An endothelial cell that lines any of the venous cavities through which blood passes in various glands and organs such as the spleen and liver.""",
                meaning=CL["0002262"]))
        setattr(cls, "CL:0000796",
            PermissibleValue(
                text="CL:0000796",
                description="""A alpha-beta intraepithelial T cell found in the columnar epithelium of the gastrointestinal tract. Intraepithelial T cells often have distinct developmental pathways and activation requirements.""",
                meaning=CL["0000796"]))
        setattr(cls, "CL:0007017",
            PermissibleValue(
                text="CL:0007017",
                description="""An epidermal cell with apical microvilli or a single apical projection have synaptic associations with nerve fibres in the epidermis.""",
                meaning=CL["0007017"]))
        setattr(cls, "CL:0002668",
            PermissibleValue(
                text="CL:0002668",
                description="""An otic fibrocyte that is lateral to the basilar membrane and anchoris it to the lateral wall.""",
                meaning=CL["0002668"]))
        setattr(cls, "CL:1000470",
            PermissibleValue(
                text="CL:1000470",
                description="A myoepithelial cell that is part of the primary lactiferous duct.",
                meaning=CL["1000470"]))
        setattr(cls, "CL:0000682",
            PermissibleValue(
                text="CL:0000682",
                description="""An absorptive cell of the gut epithelium that endocytoses microorganisms and intact macromolecules from the gut lumen and transports them to the subepithelial space where they are presented to antigen-presenting cells and lymphocytes.""",
                meaning=CL["0000682"]))
        setattr(cls, "CL:0005026",
            PermissibleValue(
                text="CL:0005026",
                description="""Multi fate stem cell that gives rise to both hepatocytes and cholangiocytes as descendants. The term often refers to fetal precursors of hepatocytes (differently from 'hepatic stem cell', usually applied to the self-renewing pool of hepatocyte precursors in the adult liver). Hepatoblasts may also be endogenous, as some stem cells found in the liver come from the bone marrow via blood circulation.""",
                meaning=CL["0005026"]))
        setattr(cls, "CL:0011011",
            PermissibleValue(
                text="CL:0011011",
                description="""A cell derived from the mesoderm that is located between the paraxial mesoderm and the lateral plate.""",
                meaning=CL["0011011"]))
        setattr(cls, "CL:0005015",
            PermissibleValue(
                text="CL:0005015",
                description="""An auditory epithelial support cell that surrounds the nerve fibers and synapses of the auditory inner hair cells.""",
                meaning=CL["0005015"]))
        setattr(cls, "CL:4033071",
            PermissibleValue(
                text="CL:4033071",
                description="A(n) natural killer cell that is cycling.",
                meaning=CL["4033071"]))
        setattr(cls, "CL:0000954",
            PermissibleValue(
                text="CL:0000954",
                description="""A small pre-B-II cell is a pre-B-II cell that is Rag1-positive, Rag2-positive, pre-BCR-negative, and BCR-negative, is not proliferating, and carries a DNA rearrangement of one or more immunoglobulin light chain genes.""",
                meaning=CL["0000954"]))
        setattr(cls, "CL:0000972",
            PermissibleValue(
                text="CL:0000972",
                description="""A class switched memory B cell is a memory B cell that has undergone Ig class switching and therefore is IgM-negative on the cell surface. These cells are CD27-positive and have either IgG, IgE, or IgA on the cell surface.""",
                meaning=CL["0000972"]))
        setattr(cls, "CL:0000789",
            PermissibleValue(
                text="CL:0000789",
                description="A T cell that expresses an alpha-beta T cell receptor complex.",
                meaning=CL["0000789"]))
        setattr(cls, "CL:0009019",
            PermissibleValue(
                text="CL:0009019",
                description="A kidney cortical cell that is part of the nephrogenic zone.",
                meaning=CL["0009019"]))
        setattr(cls, "CL:0017011",
            PermissibleValue(
                text="CL:0017011",
                description="A hillock cell that is part of the prostatic urethra.",
                meaning=CL["0017011"]))
        setattr(cls, "CL:4052037",
            PermissibleValue(
                text="CL:4052037",
                description="""A tuft cell that is part of the olfactory epithelium, characterized by a globular body and the expression of neurogranin (Nrgn) in mice. This cell plays a crucial role in allergen recognition and regulating olfactory stem cell proliferation via TRPM5-dependent ATP sensing and cysteinyl leukotriene production. Unlike nasal respiratory tuft cells, it has low to absent expression of taste receptors, including the G protein Gα gustducin, and rarely contacts olfactory sensory neurons directly.""",
                meaning=CL["4052037"]))
        setattr(cls, "CL:0000904",
            PermissibleValue(
                text="CL:0000904",
                description="""CD4-positive, alpha-beta memory T cell with the phenotype CCR7-positive, CD127-positive, CD45RA-negative, CD45RO-positive, and CD25-negative.""",
                meaning=CL["0000904"]))
        setattr(cls, "CL:0004139",
            PermissibleValue(
                text="CL:0004139",
                description="A retinal ganglion A2 cell with dendrites terminating in S2.",
                meaning=CL["0004139"]))
        setattr(cls, "CL:0009016",
            PermissibleValue(
                text="CL:0009016",
                description="""An intestinal stem cell that is located in the large intestine crypt of Liberkuhn. These stem cells reside at the bottom of crypts in the large intestine and are highly proliferative. They either differentiate into transit amplifying cells or self-renew to form new stem cells.""",
                meaning=CL["0009016"]))
        setattr(cls, "CL:4023087",
            PermissibleValue(
                text="CL:4023087",
                description="A Martinotti neuron that has axons that form a fan-like plexus.",
                meaning=CL["4023087"]))
        setattr(cls, "CL:0000840",
            PermissibleValue(
                text="CL:0000840",
                description="""An immature cell of the conventional dendritic cell lineage, characterized by high levels of antigen uptake via endocytosis, macropinocytosis, and phagocytosis, and typically found resident in the tissues. Markers for this cell are CD80-low, CD86-low, and MHC-II-low.""",
                meaning=CL["0000840"]))
        setattr(cls, "CL:0008049",
            PermissibleValue(
                text="CL:0008049",
                description="""A giant pyramidal neuron with a soma in layer Vb of the primary motor cortex that sends its axons down the spinal cord via the corticospinal tract, either synapsing directly with alpha motor neurons, or targeting interneurons in the spinal cord. In humans, Betz cells are the largest known in the central nervous system.""",
                meaning=CL["0008049"]))
        setattr(cls, "CL:0002473",
            PermissibleValue(
                text="CL:0002473",
                description="Gr1-low non-classical monocyte that has high surface expression of a MHC-II complex.",
                meaning=CL["0002473"]))
        setattr(cls, "CL:0010009",
            PermissibleValue(
                text="CL:0010009",
                description="Any photoreceptor cell that is part of some camera-type eye.",
                meaning=CL["0010009"]))
        setattr(cls, "CL:0002206",
            PermissibleValue(
                text="CL:0002206",
                description="A brush cell of the epithelium in the terminal bronchiole.",
                meaning=CL["0002206"]))
        setattr(cls, "CL:0000287",
            PermissibleValue(
                text="CL:0000287",
                description="Any photoreceptor cell that is part of some eye.",
                meaning=CL["0000287"]))
        setattr(cls, "CL:0009063",
            PermissibleValue(
                text="CL:0009063",
                description="An enteroendocrine cell that is located in the anorectum.",
                meaning=CL["0009063"]))
        setattr(cls, "CL:0002370",
            PermissibleValue(
                text="CL:0002370",
                description="""A simple columnar epithelial cell that secretes mucin. Rough endoplasmic reticulum, mitochondria, the nucleus, and other organelles are concentrated in the basal portion. The apical plasma membrane projects microvilli to increase surface area for secretion.""",
                meaning=CL["0002370"]))
        setattr(cls, "CL:0000851",
            PermissibleValue(
                text="CL:0000851",
                description="""Neuromast mantle cell is a non-sensory cell. Neuromast mantle cells surround the neuromast support cells and neuromast hair cells, separating the neuromast from the epidermis, and secrete cupula in which the ciliary bundles of all the hair cells are embedded.""",
                meaning=CL["0000851"]))
        setattr(cls, "CL:0000701",
            PermissibleValue(
                text="CL:0000701",
                description="Supports paraganglial type 1 cell.",
                meaning=CL["0000701"]))
        setattr(cls, "CL:1001595",
            PermissibleValue(
                text="CL:1001595",
                description="""Glandular cell of rectal epithelium. Example: Goblet cell; enterocytes or absorptive cells; enteroendocrine and M cells.""",
                meaning=CL["1001595"]))
        setattr(cls, "CL:4030026",
            PermissibleValue(
                text="CL:4030026",
                description="""An enterocyte of the human intestine expressing bestrophin-4 (BEST4) calcium-activated ion channels.""",
                meaning=CL["4030026"]))
        setattr(cls, "CL:0000456",
            PermissibleValue(
                text="CL:0000456",
                description="Any secretory cell that is capable of some mineralocorticoid secretion.",
                meaning=CL["0000456"]))
        setattr(cls, "CL:0002449",
            PermissibleValue(
                text="CL:0002449",
                description="A NK1.1-positive T cell that is CD94-positive and Ly49Cl-positive.",
                meaning=CL["0002449"]))
        setattr(cls, "CL:0000742",
            PermissibleValue(
                text="CL:0000742",
                description="""A round chondrocyte that first differentiates in the late embryonic growth plate of bone.""",
                meaning=CL["0000742"]))
        setattr(cls, "CL:1000385",
            PermissibleValue(
                text="CL:1000385",
                description="""A type II vestibular sensory cell that is part of the epithelium of crista of ampulla of semicircular duct of membranous labyrinth.""",
                meaning=CL["1000385"]))
        setattr(cls, "CL:0002327",
            PermissibleValue(
                text="CL:0002327",
                description="An epithelial cell of the mammary gland.",
                meaning=CL["0002327"]))
        setattr(cls, "CL:0002013",
            PermissibleValue(
                text="CL:0002013",
                description="A basophilic erythroblast that is GlyA-positive.",
                meaning=CL["0002013"]))
        setattr(cls, "CL:0002361",
            PermissibleValue(
                text="CL:0002361",
                description="""A progenitor cell that is capable of forming colonies of primitive erythrocytes in the blood island of the yolk sac. First arrive at E7.5 in mouse and expresses CD41.""",
                meaning=CL["0002361"]))
        setattr(cls, "CL:1000082",
            PermissibleValue(
                text="CL:1000082",
                meaning=CL["1000082"]))
        setattr(cls, "CL:1001581",
            PermissibleValue(
                text="CL:1001581",
                description="Glial cell of lateral ventricle.",
                meaning=CL["1001581"]))
        setattr(cls, "CL:1000302",
            PermissibleValue(
                text="CL:1000302",
                description="A fibroblast that is part of the papillary layer of dermis.",
                meaning=CL["1000302"]))
        setattr(cls, "CL:0003032",
            PermissibleValue(
                text="CL:0003032",
                description="""A monostratified retinal ganglion cell that has post synaptic terminals in sublaminar layer S2 and is depolarized by decreased illumination of their receptive field center""",
                meaning=CL["0003032"]))
        setattr(cls, "CL:0002502",
            PermissibleValue(
                text="CL:0002502",
                description="An enteroendocrine cell of the small intestine that secretes motilin.",
                meaning=CL["0002502"]))
        setattr(cls, "CL:4023022",
            PermissibleValue(
                text="CL:4023022",
                description="""A Lamp5 GABAergic cortical interneuron that has extended axons in the surface of L1. Canopy Lamp5 cells resemble neurogliaform cells in having elongated horizontal axonal arbors largely confined to L1; but the dendritic arbors are wider and have fewer branches, while the axon is less tortuous and extends further from the soma""",
                meaning=CL["4023022"]))
        setattr(cls, "CL:0019028",
            PermissibleValue(
                text="CL:0019028",
                description="""Any hepatocyte that is part of the liver lobule midzonal region. These cells have mixed functionality in comparison with those in the other two regions of the liver lobule.""",
                meaning=CL["0019028"]))
        setattr(cls, "CL:0000803",
            PermissibleValue(
                text="CL:0000803",
                description="""A gamma-delta intraepithelial T cell that has the phenotype CD4-negative and CD8-negative.""",
                meaning=CL["0000803"]))
        setattr(cls, "CL:0002335",
            PermissibleValue(
                text="CL:0002335",
                description="""A preadipocyte that is capable of differentiating into a brown adipocyte. This cell type expresses uncoupling protein-1, PPAR-gamma, PR-domain-containing 16; and PGC-1alpha (peroxisome proliferator-activated receptor-gamma (PPARgamma) coactivator-1alpha).""",
                meaning=CL["0002335"]))
        setattr(cls, "CL:0004223",
            PermissibleValue(
                text="CL:0004223",
                description="""A amacrine cell with a small dendritic field and post-synaptic terminals in S1, S2, S3, and S4. AB diffuse-1 amacrine cells have a tent-shaped dendritic arbor and undulate dendrites.""",
                meaning=CL["0004223"]))
        setattr(cls, "CL:0000484",
            PermissibleValue(
                text="CL:0000484",
                description="""Mast cell subtype whose granules contain both the serine proteases tryptase and chymase. These cells are primarily found in connective tissue, such as the peritoneal cavity, skin, and intestinal submucosa. Their development is T-cell independent.""",
                meaning=CL["0000484"]))
        setattr(cls, "CL:1001579",
            PermissibleValue(
                text="CL:1001579",
                description="Glial cell of cerebral cortex.",
                meaning=CL["1001579"]))
        setattr(cls, "CL:0002653",
            PermissibleValue(
                text="CL:0002653",
                description="A squamous shaped endothelial cell.",
                meaning=CL["0002653"]))
        setattr(cls, "CL:0002340",
            PermissibleValue(
                text="CL:0002340",
                description="""The exocrine cell of the prostate, this epithelial cell secretes prostatic acid phosphotase and PSA, and is dependent on androgen hormones for survival.""",
                meaning=CL["0002340"]))
        setattr(cls, "CL:0002258",
            PermissibleValue(
                text="CL:0002258",
                description="""A cell type that varies from squamous to columnar, depending on their activity with microvillus directed luminally. This cell produces and secretes thyroid hormones.""",
                meaning=CL["0002258"]))
        setattr(cls, "CL:0002414",
            PermissibleValue(
                text="CL:0002414",
                description="A Vgamma1.1-positive, Vdelta6.3-negative thymocyte that is CD24-positive.",
                meaning=CL["0002414"]))
        setattr(cls, "CL:4030059",
            PermissibleValue(
                text="CL:4030059",
                description="""A transcriptomically distinct intratelencephalic-projecting glutamatergic neuron with a soma found between cortical layer 2-4. This intratelencephalic-projecting glutamatergic neuron has thin-tufted apical dendrites and extends its axonal projection into L5 in the neocortex. This neuronal type has a hyperpolarised resting membrane potential. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: IT-projecting excitatory neurons', Author Categories: 'CrossArea_subclass', clusters L2/3 IT.""",
                meaning=CL["4030059"]))
        setattr(cls, "CL:1000706",
            PermissibleValue(
                text="CL:1000706",
                description="A urothelial cell that is part of the urothelium of ureter.",
                meaning=CL["1000706"]))
        setattr(cls, "CL:4030015",
            PermissibleValue(
                text="CL:4030015",
                description="""A renal alpha-intercalated cell that is part of the collecting duct of the renal tubule.""",
                meaning=CL["4030015"]))
        setattr(cls, "CL:0000310",
            PermissibleValue(
                text="CL:0000310",
                meaning=CL["0000310"]))
        setattr(cls, "CL:0002679",
            PermissibleValue(
                text="CL:0002679",
                description="""A lymphocyte found in adipose tissue that lacks lineage markers of other lymphocytes but is capable of mediating TH2 cytokine responses. This cell type is found in fat associated lymphoid clusters, proliferates in response to IL2 and produce large amounts of TH2 cytokines such as IL5, IL6 and IL13""",
                meaning=CL["0002679"]))
        setattr(cls, "CL:0002080",
            PermissibleValue(
                text="CL:0002080",
                description="""A cubodial epithelial cell that is continuous with the lining of intercalated ducts that drain the acinus. This cell type secretes a high pH solution to aid in activation of zymogens, and can differentiate into endocrine and exocrine pancreatic cell types.""",
                meaning=CL["0002080"]))
        setattr(cls, "CL:0003005",
            PermissibleValue(
                text="CL:0003005",
                description="""A mono-stratified retinal ganglion cell that has a small dendritic field and dense dendritic arbor.""",
                meaning=CL["0003005"]))
        setattr(cls, "CL:0000974",
            PermissibleValue(
                text="CL:0000974",
                description="""A fully differentiated plasma cell that lives for years, as opposed to months, secretes immunoglobulin, and has the phenotype weakly CD19-positive, CD20-negative, CD38-negative, strongly CD138-positive, MHC Class II-negative, surface immunoglobulin-negative, IgD-negative, and strongly CXCR4-positive. The majority of these cells of this type reside in the bone marrow.""",
                meaning=CL["0000974"]))
        setattr(cls, "CL:0000133",
            PermissibleValue(
                text="CL:0000133",
                description="Ectoderm destined to be nervous tissue.",
                meaning=CL["0000133"]))
        setattr(cls, "CL:0002468",
            PermissibleValue(
                text="CL:0002468",
                description="A myeloid suppressor cell that is Gr1-low and CD11c-positive.",
                meaning=CL["0002468"]))
        setattr(cls, "CL:0002177",
            PermissibleValue(
                text="CL:0002177",
                description="""A supporting cell of the anterior pituitary gland involved in trophic and catabolic processes; expresses a broad spectrum of cytokeratins indicative of their epithelial nature.""",
                meaning=CL["0002177"]))
        setattr(cls, "CL:4030050",
            PermissibleValue(
                text="CL:4030050",
                description="""A medium spiny neuron that expresses both DRD1 and DRD2 and is part of an extra-striosomal part of dorsal striatum.""",
                meaning=CL["4030050"]))
        setattr(cls, "CL:0000300",
            PermissibleValue(
                text="CL:0000300",
                description="A mature sexual reproductive cell having a single set of unpaired chromosomes.",
                meaning=CL["0000300"]))
        setattr(cls, "CL:2000092",
            PermissibleValue(
                text="CL:2000092",
                description="Any keratinocyte that is part of a hair follicle.",
                meaning=CL["2000092"]))
        setattr(cls, "CL:4033061",
            PermissibleValue(
                text="CL:4033061",
                description="An endothelial cell that is part of a central vein of liver.",
                meaning=CL["4033061"]))
        setattr(cls, "CL:0000656",
            PermissibleValue(
                text="CL:0000656",
                description="""A diploid cell that has derived from a spermatogonium and can subsequently begin meiosis and divide into two haploid secondary spermatocytes.""",
                meaning=CL["0000656"]))
        setattr(cls, "CL:0000150",
            PermissibleValue(
                text="CL:0000150",
                description="""An epithelial cell, located in a gland, that is specialised for the synthesis and secretion of specific biomolecules, such as hormones, or mucous.""",
                meaning=CL["0000150"]))
        setattr(cls, "CL:0000549",
            PermissibleValue(
                text="CL:0000549",
                description="""A nucleated immature erythrocyte, having cytoplasm generally similar to that of the earlier proerythroblast but sometimes even more basophilic, and usually regular in outline. The nucleus is still relatively large, but the chromatin strands are thicker and more deeply staining, giving a coarser appearance; the nucleoli have disappeared. This cell is CD71-positive and lacks hematopoeitic lineage markers.""",
                meaning=CL["0000549"]))
        setattr(cls, "CL:0000902",
            PermissibleValue(
                text="CL:0000902",
                description="""CD4-positive alpha-beta T cell with the phenotype CD25-positive, CTLA-4-positive, and FoxP3-positive with regulatory function.""",
                meaning=CL["0000902"]))
        setattr(cls, "CL:0000944",
            PermissibleValue(
                text="CL:0000944",
                description="""A Be cell that facilitates development of T-helper 2 (Th2) phenotype T cells, and secretes high levels of interleukin-2, interleukin-10, interleukin-4, and interleukin-6.""",
                meaning=CL["0000944"]))
        setattr(cls, "CL:0002544",
            PermissibleValue(
                text="CL:0002544",
                description="An arterial endothelial cell that is part of the aorta endothelium.",
                meaning=CL["0002544"]))
        setattr(cls, "CL:0000833",
            PermissibleValue(
                text="CL:0000833",
                description="A promyelocyte committed to the eosinophil lineage.",
                meaning=CL["0000833"]))
        setattr(cls, "CL:4023122",
            PermissibleValue(
                text="CL:4023122",
                description="""An interneuron located in the cerebral cortex that expresses the oxytocin receptor. These interneurons also express somatostatin.""",
                meaning=CL["4023122"]))
        setattr(cls, "CL:0000158",
            PermissibleValue(
                text="CL:0000158",
                description="""A non-mucous, epithelial secretory cell that is part of the tracheobronchial tree. A club cell has short microvilli but no cilia. A club cell is able to multiply and differentiate into ciliated cells to regenerate the bronchiolar epithelium and it also protects the tracheobronchial epithelium.""",
                meaning=CL["0000158"]))
        setattr(cls, "CL:0003043",
            PermissibleValue(
                text="CL:0003043",
                description="""A monostratified retinal ganglion cell with large soma and large dendritic field, with dense dendritic arbor.""",
                meaning=CL["0003043"]))
        setattr(cls, "CL:0002613",
            PermissibleValue(
                text="CL:0002613",
                description="A neuron of the striatum.",
                meaning=CL["0002613"]))
        setattr(cls, "CL:0008003",
            PermissibleValue(
                text="CL:0008003",
                description="""A myotube that is part of some somatic muscle.  Examples include arthropod somatic muscle cells.""",
                meaning=CL["0008003"]))
        setattr(cls, "CL:4023061",
            PermissibleValue(
                text="CL:4023061",
                description="A neuron that has its soma located in CA4 of the hippocampus.",
                meaning=CL["4023061"]))
        setattr(cls, "CL:0002227",
            PermissibleValue(
                text="CL:0002227",
                description="A secondary fiber cell that contains a nucleus.",
                meaning=CL["0002227"]))
        setattr(cls, "CL:1000449",
            PermissibleValue(
                text="CL:1000449",
                description="An epithelial cell that is part of the nephron.",
                meaning=CL["1000449"]))
        setattr(cls, "CL:1000427",
            PermissibleValue(
                text="CL:1000427",
                description="A chromaffin cell that is part of the adrenal cortex.",
                meaning=CL["1000427"]))
        setattr(cls, "CL:0000546",
            PermissibleValue(
                text="CL:0000546",
                description="""A CD4-positive, alpha-beta T cell that has the phenotype GATA-3-positive, CXCR3-negative, CCR6-negative, and is capable of producing interleukin-4.""",
                meaning=CL["0000546"]))
        setattr(cls, "CL:0001002",
            PermissibleValue(
                text="CL:0001002",
                description="""Mature CD8-alpha-negative CD11b-negative dendritic cell is a CD8-alpha-negative CD11b-negative dendritic cell that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001002"]))
        setattr(cls, "CL:0000159",
            PermissibleValue(
                text="CL:0000159",
                meaning=CL["0000159"]))
        setattr(cls, "CL:0002385",
            PermissibleValue(
                text="CL:0002385",
                description="An oblong or round asexual spore formed from conidial chains.",
                meaning=CL["0002385"]))
        setattr(cls, "CL:0000928",
            PermissibleValue(
                text="CL:0000928",
                description="""A type I NK T cell that has been recently activated, secretes interferon-gamma and interleukin-4, and has phenotype CD4-negative, CD8-negative, CD69-positive, and downregulated NK markers.""",
                meaning=CL["0000928"]))
        setattr(cls, "CL:0001062",
            PermissibleValue(
                text="CL:0001062",
                description="""A CD8-positive, alpha beta memory T cell with the phenotype CD45RA-positive, CD45RO-negative, and CCR7-negative.""",
                meaning=CL["0001062"]))
        setattr(cls, "CL:1001108",
            PermissibleValue(
                text="CL:1001108",
                description="""An epithelial cell that is part of some loop of Henle thick ascending limb segment located in the renal medulla.""",
                meaning=CL["1001108"]))
        setattr(cls, "CL:0002092",
            PermissibleValue(
                text="CL:0002092",
                description="""A cell found in the bone marrow. This can include fibroblasts, macrophages, adipocytes, osteoblasts, osteoclasts, endothelial cells and hematopoietic cells.""",
                meaning=CL["0002092"]))
        setattr(cls, "CL:4047040",
            PermissibleValue(
                text="CL:4047040",
                description="""A smooth muscle cell that is found in the inner muscular layer of hollow organs. It is characterized by its spiral/helical arrangement around organ lumens. This cell is crucial for peristaltic movements in organs.""",
                meaning=CL["4047040"]))
        setattr(cls, "CL:0009002",
            PermissibleValue(
                text="CL:0009002",
                description="""Any cell participating in the inflammatory response to a foreign substance, e.g. neutrophil, macrophage.""",
                meaning=CL["0009002"]))
        setattr(cls, "CL:2000018",
            PermissibleValue(
                text="CL:2000018",
                description="Any endothelial cell of artery that is part of a coronary artery.",
                meaning=CL["2000018"]))
        setattr(cls, "CL:0009089",
            PermissibleValue(
                text="CL:0009089",
                description="A pericyte cell that is part of a lung.",
                meaning=CL["0009089"]))
        setattr(cls, "CL:1001592",
            PermissibleValue(
                text="CL:1001592",
                description="Glandular cell of gallbladder epithelium.",
                meaning=CL["1001592"]))
        setattr(cls, "CL:0002590",
            PermissibleValue(
                text="CL:0002590",
                description="A vascular associated smooth muscle cell of the brain vasculature.",
                meaning=CL["0002590"]))
        setattr(cls, "CL:0000113",
            PermissibleValue(
                text="CL:0000113",
                description="A vertebrate phagocyte with a single nucleus.",
                meaning=CL["0000113"]))
        setattr(cls, "CL:4052006",
            PermissibleValue(
                text="CL:4052006",
                description="""An epithelial cell that is part of the crypt of Lieberkuhn, originating from intestinal stem cells and giving rise to enteroendocrine cells (EECs). In mouse and human, this cell can be characterized by the expression of Neurog3, and has the ability to proliferate and differentiate into multiple EEC subtypes. Its proliferative potential contributes to crypt growth, distinguishing it from fully differentiated EECs.""",
                meaning=CL["4052006"]))
        setattr(cls, "CL:0000203",
            PermissibleValue(
                text="CL:0000203",
                description="""Any neuronal receptor cell that is capable of some detection of mechanical stimulus involved in sensory perception of gravity.""",
                meaning=CL["0000203"]))
        setattr(cls, "CL:0002563",
            PermissibleValue(
                text="CL:0002563",
                description="An epithelial cell of the lining of the intestine.",
                meaning=CL["0002563"]))
        setattr(cls, "CL:0002403",
            PermissibleValue(
                text="CL:0002403",
                description="""A thymocyte that has a T cell receptor consisting of a gamma chain containing Vgamma2 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-negative. This cell-type is found in the fetal thymus.""",
                meaning=CL["0002403"]))
        setattr(cls, "CL:0002611",
            PermissibleValue(
                text="CL:0002611",
                description="A CNS neuron of the dorsal spinal cord.",
                meaning=CL["0002611"]))
        setattr(cls, "CL:4030008",
            PermissibleValue(
                text="CL:4030008",
                description="""A specialized epithelial cell that contains \"feet\" that interdigitate with the \"feet\" of other glomerular epithelial cells in the pronephros.""",
                meaning=CL["4030008"]))
        setattr(cls, "CL:0009091",
            PermissibleValue(
                text="CL:0009091",
                description="""A stem cell found in the interstitial compartment of the neonatal testis; it is capable of self-renewal as well as differentiation into steroidogenic cells (adult Leydig cells). Intermediate stages of development include progenitor Leydig cells and immature Leydig cells.""",
                meaning=CL["0009091"]))
        setattr(cls, "CL:0000806",
            PermissibleValue(
                text="CL:0000806",
                description="""A thymocyte that has the phenotype CD4-negative, CD8-negative, CD44-positive, and CD25-positive.""",
                meaning=CL["0000806"]))
        setattr(cls, "CL:4023076",
            PermissibleValue(
                text="CL:4023076",
                description="""An interneuron that has Martinotti morphology. These interneurons are scattered throughout various layers of the cerebral cortex, sending their axons up to the cortical layer I where they form axonal arborization.""",
                meaning=CL["4023076"]))
        setattr(cls, "CL:0000392",
            PermissibleValue(
                text="CL:0000392",
                description="""A hemocyte that synthesizes and secretes melanins as part of the antimicrobial immune response. It is characterized morphologically by crystal inclusions of phenoloxidases in its cytoplasm, hence its name.""",
                meaning=CL["0000392"]))
        setattr(cls, "CL:4023187",
            PermissibleValue(
                text="CL:4023187",
                description="""A neuron with a small cell body that is located in a koniocellular layer of the lateral geniculate nucleus (LGN).""",
                meaning=CL["4023187"]))
        setattr(cls, "CL:4052017",
            PermissibleValue(
                text="CL:4052017",
                description="""A capillary endothelial cell that is part of the choroid plexus, characterized by its fenestrated nature with 60 to 80 nm fenestrations and lack of tight junctions. This fenestrated structure allows for the rapid delivery of water and other components, aiding in the production of cerebrospinal fluid (CSF).""",
                meaning=CL["4052017"]))
        setattr(cls, "CL:0000874",
            PermissibleValue(
                text="CL:0000874",
                description="""A splenic macrophage found in the red-pulp of the spleen, and involved in immune responses to blood-borne pathogens and in the clearance of senescent erythrocytes. Markers include F4/80-positive, CD68-positive, MR-positive, Dectin2-positive, macrosialin-positive, and sialoadhesin-low.""",
                meaning=CL["0000874"]))
        setattr(cls, "CL:1000435",
            PermissibleValue(
                text="CL:1000435",
                description="An epithelial cell that is part of the lacrimal drainage system.",
                meaning=CL["1000435"]))
        setattr(cls, "CL:1000717",
            PermissibleValue(
                text="CL:1000717",
                description="""Intercalated cell that is part of some outer medullary collecting duct. It is known in some mammalian species that this cell may contribute in the maintenance of acid/base homeostasis.""",
                meaning=CL["1000717"]))
        setattr(cls, "CL:0000239",
            PermissibleValue(
                text="CL:0000239",
                description="""An epithelial cell characterized by the presence of a brush border on its apical surface, which increases the surface area for absorption.""",
                meaning=CL["0000239"]))
        setattr(cls, "CL:0000511",
            PermissibleValue(
                text="CL:0000511",
                description="A peptide hormone secreting cell that secretes androgen binding protein.",
                meaning=CL["0000511"]))
        setattr(cls, "CL:4030039",
            PermissibleValue(
                text="CL:4030039",
                description="""An extratelencephalic-projecting glutamatergic cortical neuron that is morphologically-defined with a large, spindle-shaped cell body, thick bipolar dendrites with limited branching and a moderate density of spines, and often an axon initial segment that emanates from the side of the cell body. This cell type is associated with markers POU3F, BMP3 and ITGA4.""",
                meaning=CL["4030039"]))
        setattr(cls, "CL:0000550",
            PermissibleValue(
                text="CL:0000550",
                description="""A nucleated, immature erythrocyte in which the nucleus occupies a relatively smaller part of the cell than in its precursor, the basophilic erythroblast. The cytoplasm is beginning to acquire hemoglobin and thus is no longer a purely basophilic, but takes on acidophilic aspects, which becomes progressively more marked as the cell matures. The chromatin of the nucleus is arranged in coarse, deeply staining clumps. This cell is CD71-positive and lacks hematopoeitic lineage markers.""",
                meaning=CL["0000550"]))
        setattr(cls, "CL:4042040",
            PermissibleValue(
                text="CL:4042040",
                description="""A glutametergic neuron with its soma located in a basal ganglia. This neuron type is involved in motor control, decision making and learning.""",
                meaning=CL["4042040"]))
        setattr(cls, "CL:0000525",
            PermissibleValue(
                text="CL:0000525",
                description="""A cell from the outer syncytial layer of the trophoblast of an early mammalian embryo, directly associated with the maternal blood supply. It secretes hCG in order to maintain progesterone secretion and sustain a pregnancy.""",
                meaning=CL["0000525"]))
        setattr(cls, "CL:0019003",
            PermissibleValue(
                text="CL:0019003",
                description="Any goblet cell that is part of the tracheobronchial epithelium.",
                meaning=CL["0019003"]))
        setattr(cls, "CL:0000438",
            PermissibleValue(
                text="CL:0000438",
                description="A peptide hormone secreting cell pituitary that produces luteinizing hormone.",
                meaning=CL["0000438"]))
        setattr(cls, "CL:0000052",
            PermissibleValue(
                text="CL:0000052",
                description="A stem cell from which all cells of the body can form.",
                meaning=CL["0000052"]))
        setattr(cls, "CL:4042020",
            PermissibleValue(
                text="CL:4042020",
                description="""A type of tanycyte located in the floor of third ventricle and the infindibular recess. This tanycyte has an elongated morphology with multiple microvilli extending medially and ventrally to the median eminence, contacting the pial surface and blood vessels. This type of tanycyte expresses FGF receptors 1 and 2, is in contact with GnRH neurons, and is involved in the release of gonadotropin-releasing hormone (GnRH).""",
                meaning=CL["4042020"]))
        setattr(cls, "CL:0000981",
            PermissibleValue(
                text="CL:0000981",
                description="A memory B cell with the phenotype IgD-negative and CD27-negative.",
                meaning=CL["0000981"]))
        setattr(cls, "CL:4023066",
            PermissibleValue(
                text="CL:4023066",
                description="""A pyramidal neuron which has an apical tree which is oriented parallel to the pia. This is unlike typical pyramidal neurons which have its apical dendrite aligned vertically.""",
                meaning=CL["4023066"]))
        setattr(cls, "CL:0011101",
            PermissibleValue(
                text="CL:0011101",
                description="""Cells of the uterine chorion that acquire specialized structural and/or functional features that characterize chorionic trophoblasts. These cells will migrate towards the spongiotrophoblast layer and give rise to syncytiotrophoblasts of the labyrinthine layer.""",
                meaning=CL["0011101"]))
        setattr(cls, "CL:4033031",
            PermissibleValue(
                text="CL:4033031",
                description="""An ON diffuse bipolar cell that predominantly connects to ON parasol cells and lateral amacrine cells.""",
                meaning=CL["4033031"]))
        setattr(cls, "CL:0000151",
            PermissibleValue(
                text="CL:0000151",
                description="A cell that specializes in controlled release of one or more substances.",
                meaning=CL["0000151"]))
        setattr(cls, "CL:1000374",
            PermissibleValue(
                text="CL:1000374",
                description="""A transitional myocyte that is part of the posterior division of left branch of atrioventricular bundle.""",
                meaning=CL["1000374"]))
        setattr(cls, "CL:0008042",
            PermissibleValue(
                text="CL:0008042",
                description="""A tanycyte of the subfornical organ (SFO).  These cells extend long and slender fibers extending from their cell bodies in the ependyma toward fenestrated capillaries associated with the SFO, where they form a dense network surrounding these capillaries.""",
                meaning=CL["0008042"]))
        setattr(cls, "CL:0000542",
            PermissibleValue(
                text="CL:0000542",
                description="""A lymphocyte is a leukocyte commonly found in the blood and lymph that has the characteristics of a large nucleus, a neutral staining cytoplasm, and prominent heterochromatin.""",
                meaning=CL["0000542"]))
        setattr(cls, "CL:4030011",
            PermissibleValue(
                text="CL:4030011",
                description="""A brush border cell that is part of segment 3 (S3) of the proximal tubule epithelium, which extends from the medullary rays of the renal cortex into the outer medulla.""",
                meaning=CL["4030011"]))
        setattr(cls, "CL:0000540",
            PermissibleValue(
                text="CL:0000540",
                description="""The basic cellular unit of nervous tissue. Each neuron consists of a body, an axon, and dendrites. Their purpose is to receive, conduct, and transmit impulses in the nervous system.""",
                meaning=CL["0000540"]))
        setattr(cls, "CL:0000580",
            PermissibleValue(
                text="CL:0000580",
                description="""A neutrophil precursor in the granulocytic series, being a cell intermediate in development between a promyelocyte and a metamyelocyte; in this stage, production of primary granules is complete and neutrophil-specific granules has started. No nucleolus is present. This cell type is CD13-positive, CD16-negative, integrin alpha-M-positive, CD15-positive, CD33-positive, CD24-positive, C/EBP-a-positive, C/EBPe-positive, PU.1-positive, lactotransferrin-positive, myeloperoxidase-positive and NGAL-positive.""",
                meaning=CL["0000580"]))
        setattr(cls, "CL:4042033",
            PermissibleValue(
                text="CL:4042033",
                description="""A neuron of the central nervous system that expresses POMC and synthesizes the POMC precursor polypeptide. This neuron type is located in the arcuate nucleus of the hypothalamus and in the nucleus tractus solitarius of the brainstem. The pro-opiomelanocortin neuron is part of the central melanocortin system and it is involved in regulating energy homeostasis, metabolism, and appetite. This neuronal type responds to hormonal signals such as levels of leptin and insulin, and its activation results in the release of α-melanocyte-stimulating hormone (α-MSH), which acts on melanocortin receptors to suppress food intake and increase energy expenditure.""",
                meaning=CL["4042033"]))
        setattr(cls, "CL:0008020",
            PermissibleValue(
                text="CL:0008020",
                description="""A skeletal muscle satellite cell that undergoes symmetric division to produce two adult skeleltal muscle myoblasts.""",
                meaning=CL["0008020"]))
        setattr(cls, "CL:0001009",
            PermissibleValue(
                text="CL:0001009",
                description="""Immature dermal dendritic cell is a dermal dendritic cell that is CD80-low, CD86-low, and MHCII-low.""",
                meaning=CL["0001009"]))
        setattr(cls, "CL:0000588",
            PermissibleValue(
                text="CL:0000588",
                description="A specialized osteoclast associated with the absorption and removal of cementum.",
                meaning=CL["0000588"]))
        setattr(cls, "CL:0011014",
            PermissibleValue(
                text="CL:0011014",
                description="A sperm cell that is not cabaple of motion (motility).",
                meaning=CL["0011014"]))
        setattr(cls, "CL:4033042",
            PermissibleValue(
                text="CL:4033042",
                description="An alveolar macrophage that expresses metallothionein.",
                meaning=CL["4033042"]))
        setattr(cls, "CL:0000914",
            PermissibleValue(
                text="CL:0000914",
                description="""An immature alpha-beta T-cell that express Egr2. These cells give rise to T cells expressing NK markers.""",
                meaning=CL["0000914"]))
        setattr(cls, "CL:4070015",
            PermissibleValue(
                text="CL:4070015",
                description="A motor neuron that controls the cardiopyloric valve.",
                meaning=CL["4070015"]))
        setattr(cls, "CL:0000816",
            PermissibleValue(
                text="CL:0000816",
                description="""An immature B cell is a B cell that has the phenotype surface IgM-positive and surface IgD-negative, and have not undergone class immunoglobulin class switching or peripheral encounter with antigen and activation.""",
                meaning=CL["0000816"]))
        setattr(cls, "CL:0000558",
            PermissibleValue(
                text="CL:0000558",
                description="""An immature erythrocyte that changes the protein composition of its plasma membrane by exosome formation and extrusion. The types of protein removed differ between species though removal of the transferrin receptor is apparent in mammals and birds.""",
                meaning=CL["0000558"]))
        setattr(cls, "CL:0000778",
            PermissibleValue(
                text="CL:0000778",
                description="""A specialized mononuclear osteoclast associated with the absorption and removal of bone, precursor of multinuclear osteoclasts.""",
                meaning=CL["0000778"]))
        setattr(cls, "CL:0000500",
            PermissibleValue(
                text="CL:0000500",
                description="An epithelial somatic cell associated with a maturing oocyte.",
                meaning=CL["0000500"]))
        setattr(cls, "CL:0009030",
            PermissibleValue(
                text="CL:0009030",
                description="An intestinal enteroendocrine cell that is located in a vermiform appendix.",
                meaning=CL["0009030"]))
        setattr(cls, "CL:0008017",
            PermissibleValue(
                text="CL:0008017",
                description="""A skeletal muscle myoblast that is part of a skeletal mucle.  These cells are formed following acivation and division of skeletal muscle satellite cells. They form a transient population that is lost when they fuse to form skeletal muscle fibers.""",
                meaning=CL["0008017"]))
        setattr(cls, "CL:4023159",
            PermissibleValue(
                text="CL:4023159",
                description="An interneuron that has double bouquet morphology.",
                meaning=CL["4023159"]))
        setattr(cls, "CL:0002504",
            PermissibleValue(
                text="CL:0002504",
                description="A smooth muscle cell of the intestine.",
                meaning=CL["0002504"]))
        setattr(cls, "CL:0000690",
            PermissibleValue(
                text="CL:0000690",
                meaning=CL["0000690"]))
        setattr(cls, "CL:0002317",
            PermissibleValue(
                text="CL:0002317",
                description="An external limiting cell found in the vestibular epithelium.",
                meaning=CL["0002317"]))
        setattr(cls, "CL:2000079",
            PermissibleValue(
                text="CL:2000079",
                description="Any mesenchymal stem cell of the bone marrow that is part of a femur.",
                meaning=CL["2000079"]))
        setattr(cls, "CL:4023120",
            PermissibleValue(
                text="CL:4023120",
                description="An auditory hair cell found in the cochlea.",
                meaning=CL["4023120"]))
        setattr(cls, "CL:0002629",
            PermissibleValue(
                text="CL:0002629",
                description="""A mature microglial cell that has changed shape to an amoeboid morphology and is capable of cytokine production and antigen presentation.""",
                meaning=CL["0002629"]))
        setattr(cls, "CL:0017009",
            PermissibleValue(
                text="CL:0017009",
                description="A human dendritic cell that expresses the AXL and SIGLEC6 genes.",
                meaning=CL["0017009"]))
        setattr(cls, "CL:1100001",
            PermissibleValue(
                text="CL:1100001",
                description="""An epithelial cell that is specialised for the synthesis and secretion of specific biomolecules.""",
                meaning=CL["1100001"]))
        setattr(cls, "CL:4052050",
            PermissibleValue(
                text="CL:4052050",
                description="An epithelial cell that is part of an endometrium luminal epithelium.",
                meaning=CL["4052050"]))
        setattr(cls, "CL:0000573",
            PermissibleValue(
                text="CL:0000573",
                description="""One of the two photoreceptor cell types in the vertebrate retina. In cones the photopigment is in invaginations of the cell membrane of the outer segment. Cones are less sensitive to light than rods, but they provide vision with higher spatial and temporal acuity, and the combination of signals from cones with different pigments allows color vision.""",
                meaning=CL["0000573"]))
        setattr(cls, "CL:1000313",
            PermissibleValue(
                text="CL:1000313",
                description="A goblet cell that is part of the epithelium of stomach.",
                meaning=CL["1000313"]))
        setattr(cls, "CL:0002253",
            PermissibleValue(
                text="CL:0002253",
                description="An epithelial cell of the lining of the large intestine.",
                meaning=CL["0002253"]))
        setattr(cls, "CL:0019029",
            PermissibleValue(
                text="CL:0019029",
                description="""Any hepatocyte that is part of the liver lobule centrilobular region. These cells are the primary location for the biotransformation of drugs.""",
                meaning=CL["0019029"]))
        setattr(cls, "CL:0000648",
            PermissibleValue(
                text="CL:0000648",
                description="""A smooth muscle cell that synthesizes, stores, and secretes the enzyme renin. This cell type are located in the wall of the afferent arteriole at the entrance to the glomerulus. While having a different origin than other kidney smooth muscle cells, this cell type expresses smooth muscle actin upon maturation.""",
                meaning=CL["0000648"]))
        setattr(cls, "CL:0000870",
            PermissibleValue(
                text="CL:0000870",
                description="A gut-associated lymphoid tissue macrophage found in the Peyer's patches.",
                meaning=CL["0000870"]))
        setattr(cls, "CL:1000236",
            PermissibleValue(
                text="CL:1000236",
                description="Any glial cell that is part of some posterior lateral line nerve.",
                meaning=CL["1000236"]))
        setattr(cls, "CL:0001069",
            PermissibleValue(
                text="CL:0001069",
                description="""An innate lymphoid cell that is capable of producing T-helper 2-cell associated cytokines upon stimulation.""",
                meaning=CL["0001069"]))
        setattr(cls, "CL:0002084",
            PermissibleValue(
                text="CL:0002084",
                description="""A Boettcher cell is a polyhedral cells on the basilar membrane of the cochlea, and is located beneath Claudius cells. A Boettcher cell is considered a supporting cell for the organ of Corti, and is present only in the lower turn of the cochlea. These cells interweave with each other, and project microvilli into the intercellular space. Because of their structural specialization, a Boettcher cell is believed to play a significant role in the function of the cochlea. They demonstrate high levels of calmodulin, and may be involved in mediating Ca(2+) regulation and ion transport.""",
                meaning=CL["0002084"]))
        setattr(cls, "CL:4047012",
            PermissibleValue(
                text="CL:4047012",
                description="""A specialized pericyte that actively participates in the formation of new blood vessels during angiogenesis by undergoing phenotypic changes, increasing proliferation, and interacting closely with endothelial cells.""",
                meaning=CL["4047012"]))
        setattr(cls, "CL:1000367",
            PermissibleValue(
                text="CL:1000367",
                description="A transitional myocyte that is part of the posterior internodal tract.",
                meaning=CL["1000367"]))
        setattr(cls, "CL:4029001",
            PermissibleValue(
                text="CL:4029001",
                description="""A cell that supports the development of a gamete by providing it cytoplasmic material (including entire organelles) by direct cross-membrane channels (del Pino, 2021).""",
                meaning=CL["4029001"]))
        setattr(cls, "CL:4033000",
            PermissibleValue(
                text="CL:4033000",
                description="A(n) endothelial cell that is part of a(n) venule of lymph node.",
                meaning=CL["4033000"]))
        setattr(cls, "CL:0002658",
            PermissibleValue(
                text="CL:0002658",
                description="A glandular epithelial cell of the large intestine.",
                meaning=CL["0002658"]))
        setattr(cls, "CL:0000565",
            PermissibleValue(
                text="CL:0000565",
                description="A cell found in fat bodies whose primary function is intermediary metabolism.",
                meaning=CL["0000565"]))
        setattr(cls, "CL:0001033",
            PermissibleValue(
                text="CL:0001033",
                description="Granule cell with a soma found in the hippocampus.",
                meaning=CL["0001033"]))
        setattr(cls, "CL:0000479",
            PermissibleValue(
                text="CL:0000479",
                description="A peptide hormone secreting cell that secretes vasopressin stimulating hormone",
                meaning=CL["0000479"]))
        setattr(cls, "CL:0002508",
            PermissibleValue(
                text="CL:0002508",
                description="""A dermal dendritic cell isolated from skin draining lymph nodes that is langerin-negative, MHC-II-positive, and CD4-negative and CD8a-negative.""",
                meaning=CL["0002508"]))
        setattr(cls, "CL:0000141",
            PermissibleValue(
                text="CL:0000141",
                description="""An osteocytelike cell with numerous processes, trapped in a lacuna in the cement of the tooth.""",
                meaning=CL["0000141"]))
        setattr(cls, "CL:0002592",
            PermissibleValue(
                text="CL:0002592",
                description="A smooth muscle cell of the coronary artery.",
                meaning=CL["0002592"]))
        setattr(cls, "CL:1001131",
            PermissibleValue(
                text="CL:1001131",
                description="A cell that is part of some vasa recta ascending limb.",
                meaning=CL["1001131"]))
        setattr(cls, "CL:0000849",
            PermissibleValue(
                text="CL:0000849",
                description="""An olfactory receptor cell with short cilia growing in an invagination bordered by microvilli.""",
                meaning=CL["0000849"]))
        setattr(cls, "CL:0009109",
            PermissibleValue(
                text="CL:0009109",
                description="A lymphatic endothelial cell located in a lymph node trabecula.",
                meaning=CL["0009109"]))
        setattr(cls, "CL:4042030",
            PermissibleValue(
                text="CL:4042030",
                description="""A GABAergic interneuron located in the Purkinje layer of the cerebellar cortex. This GABAergic interneuron type has a distinct morphology, it presents a small cell soma near the Purkinje cell layer (PCL), dendrites that extend to the surface of the molecular layer, and beaded axons that make local synapses contacts within the molecular layer. A candelabrum cell is excited by mossy fibers and granule cells but inhibited by Purkinje cells, and it inhibits molecular layer interneurons, which leads to the disinhibition of Purkinje cells.""",
                meaning=CL["4042030"]))
        setattr(cls, "CL:4030023",
            PermissibleValue(
                text="CL:4030023",
                description="""A hillock cell that is located in respiratory epithelium. In some mammalian species, this cell type has been noted to express KRT13 and KRT4 and is postulated to play a role in squamous barrier function and immunomodulation.""",
                meaning=CL["4030023"]))
        setattr(cls, "CL:0004247",
            PermissibleValue(
                text="CL:0004247",
                description="A neuron that stratifies dendrites at two and only two locations.",
                meaning=CL["0004247"]))
        setattr(cls, "CL:0000091",
            PermissibleValue(
                text="CL:0000091",
                description="""A tissue-resident macrophage of the reticuloendothelial system found on the luminal surface of the hepatic sinusoids involved in erythrocyte clearance. Markers include F4/80+, CD11b-low, CD68-positive, sialoadhesin-positive, CD163/SRCR-positive. Irregular, with long processes including lamellipodia extending into the sinusoid lumen, have flattened nucleus with cytoplasm containing characteristic invaginations of the plasma membrane (vermiform bodies); lie within the sinusoid lumen attached to the endothelial surface; derived from the bone marrow, form a major part of the body's mononuclear phagocyte system.""",
                meaning=CL["0000091"]))
        setattr(cls, "CL:0000122",
            PermissibleValue(
                text="CL:0000122",
                description="""A neuron that has dendritic processes radiating from the cell body forming a star-like shape.""",
                meaning=CL["0000122"]))
        setattr(cls, "CL:0000741",
            PermissibleValue(
                text="CL:0000741",
                description="""A motor neuron that is located in the cervical region of the spinal cord and selectively innervates the sternocleidmastoid or trapezius muscle. Unlike other motor neurons, they extend axons dorsally along lateral margins of the spinal cord.""",
                meaning=CL["0000741"]))
        setattr(cls, "CL:1001005",
            PermissibleValue(
                text="CL:1001005",
                description="An endothelial cell that is part of the glomerular capillary of the kidney.",
                meaning=CL["1001005"]))
        setattr(cls, "CL:0001023",
            PermissibleValue(
                text="CL:0001023",
                description="""A common myeloid progenitor that is Kit-positive and CD34-positive, Il7ra-negative, and is SCA1-low and Fcgr2-low and Fcgr3-low.""",
                meaning=CL["0001023"]))
        setattr(cls, "CL:0000065",
            PermissibleValue(
                text="CL:0000065",
                description="""A neuroepithelial glial cell, derived from a radial glial cell originating from the neuroectoderm, lines the ventricles of the brain and the central canal of the spinal cord. This cell is characterized by the presence of cilia on its apical surface, which can be motile or non-motile.""",
                meaning=CL["0000065"]))
        setattr(cls, "CL:2000089",
            PermissibleValue(
                text="CL:2000089",
                description="""A granule cell that has soma location in the dentate gyrus cell layer of the hippocampal formation and has an elliptical cell body and characteristic cone-shaped tree of spiny apical dendrites. The branches extend throughout the molecular layer and the distal tips of the dendritic tree end just at the hippocampal fissure or at the ventricular surface. The dentate gyrus granule cell is the principal cell type of the dentate gyrus.""",
                meaning=CL["2000089"]))
        setattr(cls, "CL:1000505",
            PermissibleValue(
                text="CL:1000505",
                description="A cell that is part of a renal pelvis.",
                meaning=CL["1000505"]))
        setattr(cls, "CL:0002178",
            PermissibleValue(
                text="CL:0002178",
                description="An epithelial cell found in the lining of the stomach.",
                meaning=CL["0002178"]))
        setattr(cls, "CL:0003008",
            PermissibleValue(
                text="CL:0003008",
                description="""A mono-stratified retinal ganglion cell that has a medium dendritic field and a medium dendritic arbor with post sympatic terminals in sublaminar layer S2.""",
                meaning=CL["0003008"]))
        setattr(cls, "CL:0002209",
            PermissibleValue(
                text="CL:0002209",
                description="""An epithelial cell present in the trachea and bronchi; columnar in shape; generally lack cilia; immature forms of ciliated or secretory cells which have been formed from stem cells.""",
                meaning=CL["0002209"]))
        setattr(cls, "CL:4023006",
            PermissibleValue(
                text="CL:4023006",
                description="""A nuclear bag fiber that is sensitive only changes in muscle length but not the rate of that change.""",
                meaning=CL["4023006"]))
        setattr(cls, "CL:0000754",
            PermissibleValue(
                text="CL:0000754",
                description="""An OFF-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the outer half of the inner plexiform layer. The dendritic tree is not well filled and the dendrites are more delicate than in type 1 cells. The axon terminal is bushier and exhibits a dense plexus of varicosities in the inner part of sublamina 1 (Ghosh et al., 2004).  It can be differentiated from other retinal bipolar neurons by its expression of marker genes: Neto1, Lhx3 and Irx-6 (Shekhar, 2016).""",
                meaning=CL["0000754"]))
        setattr(cls, "CL:0000841",
            PermissibleValue(
                text="CL:0000841",
                description="""A mature cell of the conventional dendritic cell lineage, characterized by a high capacity for antigen presentation and typically found in a lymph node.""",
                meaning=CL["0000841"]))
        setattr(cls, "CL:0000175",
            PermissibleValue(
                text="CL:0000175",
                description="""A progesterone secreting cell in the corpus luteum. The large luteal cells develop from the granulosa cells. The small luteal cells develop from the theca cells.""",
                meaning=CL["0000175"]))
        setattr(cls, "CL:0004120",
            PermissibleValue(
                text="CL:0004120",
                description="""A retinal ganglion A cell found in the retina with large somata, often polygonal in shape. The dendritic fields consist of three to seven stout dendrites that are sparce near soma. Dendrites terminate in S4.""",
                meaning=CL["0004120"]))
        setattr(cls, "CL:0002424",
            PermissibleValue(
                text="CL:0002424",
                description="A DN2 thymocyte that is Kit-low.",
                meaning=CL["0002424"]))
        setattr(cls, "CL:0000865",
            PermissibleValue(
                text="CL:0000865",
                description="A gut-associated lymphoid tissue macrophage found in lamina propria of the gut.",
                meaning=CL["0000865"]))
        setattr(cls, "CL:1000600",
            PermissibleValue(
                text="CL:1000600",
                description="Any cell that is part of some lower urinary tract.",
                meaning=CL["1000600"]))
        setattr(cls, "CL:1000321",
            PermissibleValue(
                text="CL:1000321",
                description="""A goblet cell that is part of the epithelium of crypt of Lieberkuhn of large intestine.""",
                meaning=CL["1000321"]))
        setattr(cls, "CL:0002063",
            PermissibleValue(
                text="CL:0002063",
                description="""A pulmonary alveolar epithelial cell that modulates the fluid surrounding the alveolar epithelium by secreting and recycling surfactants. This cell type also contributes to tissue repair and can differentiate after injury into a pulmonary alveolar type 1 cell. This cuboidal cell is thicker than squamous alveolar cells, have a rounded apical surface that projects above the level of surrounding epithelium. The free surface is covered by short microvilli.""",
                meaning=CL["0002063"]))
        setattr(cls, "CL:4033076",
            PermissibleValue(
                text="CL:4033076",
                description="A(n) macrophage that is cycling.",
                meaning=CL["4033076"]))
        setattr(cls, "CL:4023097",
            PermissibleValue(
                text="CL:4023097",
                description="""A mesothelial fibroblast of the arachnoid barrier layer. Arachnoid barrier cells make up the tight-junctioned layer in the leptomeninx that functions as the physiologic barrier between the cerebrospinal fluid in the subarachnoid space and the fenestrated capillaries in the dura.""",
                meaning=CL["4023097"]))
        setattr(cls, "CL:0002198",
            PermissibleValue(
                text="CL:0002198",
                description="""A large epithelial cell with an extremely acidophilic and granular cytoplasm, containing vast numbers of mitochondria; such cells may undergo neoplastic transformation. From the Greek word onkos meaning swelling, this cell type is found in parathyroid, salivary and thyroid glands.""",
                meaning=CL["0002198"]))
        setattr(cls, "CL:4030007",
            PermissibleValue(
                text="CL:4030007",
                description="""A multi-ciliated epithelial cell that is part of the fallopian tube, mainly found on the apex of the mucosal folds. This cell exhibits a columnar shape with an oval nucleus and is characterized by the presence of cilia on its surface. The coordinated beating of these cilia, together with peristaltic contractions, contributes to the self-propulsion of spermatozoa, the transport of ovum during ovulation and the transport of the fertilized ovum to the intramural fallopian tube.""",
                meaning=CL["4030007"]))
        setattr(cls, "CL:4023161",
            PermissibleValue(
                text="CL:4023161",
                description="""An excitatory glutamatergic interneuron found in the granular layer of the cerebellar cortex and also in the granule cell domain of the cochlear nucleus. Unipolar brush cells have a round or oval cell body with usually a single short dendrite that ends in a brush-like tuft of short dendrites unique to them known as dendrioles.""",
                meaning=CL["4023161"]))
        setattr(cls, "CL:0000218",
            PermissibleValue(
                text="CL:0000218",
                description="""A neuroglial cell of the peripheral nervous system which forms the insulating myelin sheaths of peripheral axons.""",
                meaning=CL["0000218"]))
        setattr(cls, "CL:0000021",
            PermissibleValue(
                text="CL:0000021",
                description="Female germ cell is a germ cell that supports female gamete production.",
                meaning=CL["0000021"]))
        setattr(cls, "CL:0000064",
            PermissibleValue(
                text="CL:0000064",
                description="A cell that has a filiform extrusion of the cell surface.",
                meaning=CL["0000064"]))
        setattr(cls, "CL:1000352",
            PermissibleValue(
                text="CL:1000352",
                description="A basal cell that is part of the epithelium of bronchiole.",
                meaning=CL["1000352"]))
        setattr(cls, "CL:1000417",
            PermissibleValue(
                text="CL:1000417",
                description="A myoepithelial cell that is part of the sweat gland.",
                meaning=CL["1000417"]))
        setattr(cls, "CL:0000167",
            PermissibleValue(
                text="CL:0000167",
                description="Any secretory cell that is capable of some peptide hormone secretion.",
                meaning=CL["0000167"]))
        setattr(cls, "CL:2000069",
            PermissibleValue(
                text="CL:2000069",
                description="Any fibroblast that is part of a gallbladder.",
                meaning=CL["2000069"]))
        setattr(cls, "CL:0002040",
            PermissibleValue(
                text="CL:0002040",
                description="A CD24-low, CD44-negative, NK1.1-negative NK T cell.",
                meaning=CL["0002040"]))
        setattr(cls, "CL:4030018",
            PermissibleValue(
                text="CL:4030018",
                description="A renal principal cell located in the connecting tubule.",
                meaning=CL["4030018"]))
        setattr(cls, "CL:0004231",
            PermissibleValue(
                text="CL:0004231",
                description="""A broadly stratifying amacrine cell with a small dendritic field and a complex dendritic arbor. Recurving diffuse amacrine cells have post-synaptic terminals in S2, S3, and S4.""",
                meaning=CL["0004231"]))
        setattr(cls, "CL:0000054",
            PermissibleValue(
                text="CL:0000054",
                meaning=CL["0000054"]))
        setattr(cls, "CL:0000532",
            PermissibleValue(
                text="CL:0000532",
                description="""A primary motor neuron with its soma in the caudal region of a spinal cord. The axon of this motoneuron exit the spinal cord from one single point and innervates the lateral surface of ventral axial muscles""",
                meaning=CL["0000532"]))
        setattr(cls, "CL:1000500",
            PermissibleValue(
                text="CL:1000500",
                description="A cell that is part of kidney interstitium.",
                meaning=CL["1000500"]))
        setattr(cls, "CL:0000830",
            PermissibleValue(
                text="CL:0000830",
                description="A promyelocyte committed to the basophil lineage.",
                meaning=CL["0000830"]))
        setattr(cls, "CL:4052001",
            PermissibleValue(
                text="CL:4052001",
                description="""An ependymal cell that lines the lateral, third, and fourth ventricles of the brain. The cell is characterized by multiple motile cilia on its apical surface, which beats in a coordinated manner to facilitate the movement of cerebrospinal fluid (CSF), contributing to brain homeostasis.""",
                meaning=CL["4052001"]))
        setattr(cls, "CL:4023171",
            PermissibleValue(
                text="CL:4023171",
                description="""A trigeminal neuron that is responsible for motor functions such as biting and chewing.""",
                meaning=CL["4023171"]))
        setattr(cls, "CL:0000114",
            PermissibleValue(
                text="CL:0000114",
                description="""An ectodermal cell that is part of the external ectoderm, forming the outermost layer of the developing embryo. It is characterized by its polarized nature, with distinct apical and basal surfaces (Ferrante Jr., Reinke, & Stanley, 1995). Surface ectodermal cell gives rise to the epidermis, hair follicles, nails, sensory organs, and specialized structures like the apical ectodermal ridge crucial for limb development (Skoufa et al., 2024).""",
                meaning=CL["0000114"]))
        setattr(cls, "CL:0000622",
            PermissibleValue(
                text="CL:0000622",
                description="""A secretory cell that is grouped together with other cells of the same type to form grape shaped clusters known as acini (singular acinus).""",
                meaning=CL["0000622"]))
        setattr(cls, "CL:0002429",
            PermissibleValue(
                text="CL:0002429",
                description="A double-positive thymocyte that is CD69-positive and has begun positive selection.",
                meaning=CL["0002429"]))
        setattr(cls, "CL:0001067",
            PermissibleValue(
                text="CL:0001067",
                description="""An innate lymphoid cell that is capable of producing the type 1 cytokine IFN-gamma, but not Th2 or Th17 cell-associated cytokines.""",
                meaning=CL["0001067"]))
        setattr(cls, "CL:0002047",
            PermissibleValue(
                text="CL:0002047",
                description="""A precursor B cell that is CD45RA-positive, CD43-positive, CD24-positive and BP-1-negative.""",
                meaning=CL["0002047"]))
        setattr(cls, "CL:0007013",
            PermissibleValue(
                text="CL:0007013",
                description="""Odontoblast that is terminally differentiated and derived from an odontogenic papilla and associated with dentine.""",
                meaning=CL["0007013"]))
        setattr(cls, "CL:0002638",
            PermissibleValue(
                text="CL:0002638",
                description="""A respiratory stem cell found at the junction of the terminal (conductive) bronchiole and the respiratory bronchiole. This cell types gives rise to alveolar cell types and club cells in response to lung injury. This cell type expresses markers Scgb1a1 and Sftpc.""",
                meaning=CL["0002638"]))
        setattr(cls, "CL:0000646",
            PermissibleValue(
                text="CL:0000646",
                description="""Undifferentiated; mitotic stem cell for other epithelial cell types; rounded or elliptical with little cytoplasm and few organelles; contain cytokeratin intermediate filament.""",
                meaning=CL["0000646"]))
        setattr(cls, "CL:1000484",
            PermissibleValue(
                text="CL:1000484",
                description="A Purkinje myocyte that is part of the atrioventricular bundle.",
                meaning=CL["1000484"]))
        setattr(cls, "CL:1000892",
            PermissibleValue(
                text="CL:1000892",
                description="An endothelial cell that is part of the capillary of the kidney.",
                meaning=CL["1000892"]))
        setattr(cls, "CL:0002172",
            PermissibleValue(
                text="CL:0002172",
                description="""A long, spindle-shaped supporting cells arranged in parallel rows that secretes components of the tectorial membrane and potassium ions into the endolymph.""",
                meaning=CL["0002172"]))
        setattr(cls, "CL:0000228",
            PermissibleValue(
                text="CL:0000228",
                description="A cell with more than one nucleus.",
                meaning=CL["0000228"]))
        setattr(cls, "CL:0000174",
            PermissibleValue(
                text="CL:0000174",
                description="Any secretory cell that is capable of some steroid hormone secretion.",
                meaning=CL["0000174"]))
        setattr(cls, "CL:0002212",
            PermissibleValue(
                text="CL:0002212",
                description="""A fast muscle fiber cell that stores energy in the form of glycogen and creatine phosphate.""",
                meaning=CL["0002212"]))
        setattr(cls, "CL:1000380",
            PermissibleValue(
                text="CL:1000380",
                description="""A type I vestibular sensory cell that is part of the epithelium of macula of saccule of membranous labyrinth.""",
                meaning=CL["1000380"]))
        setattr(cls, "CL:1000438",
            PermissibleValue(
                text="CL:1000438",
                description="An epithelial cell that is part of the wall of inferior part of anal canal.",
                meaning=CL["1000438"]))
        setattr(cls, "CL:4023094",
            PermissibleValue(
                text="CL:4023094",
                description="A pyramidal neuron which has a distinctive tuft formation, distal from the soma.",
                meaning=CL["4023094"]))
        setattr(cls, "CL:0002066",
            PermissibleValue(
                text="CL:0002066",
                description="""A neuroendocrine cell found in the epithelium of the lungs and respiratory tract. This cell type is rounded or elliptical in shape, situated mainly in the basal part of the epithelium; regulates bronchial secretion, smooth muscle contraction, lobular growth, ciliary activity and chemoreception. Cell has an electron-lucent cytoplasm, contains numerous dense-cored vesicles with a clear halo between the core and the limiting membrane.""",
                meaning=CL["0002066"]))
        setattr(cls, "CL:0009084",
            PermissibleValue(
                text="CL:0009084",
                description="An epithelial cell that is part of an endometrium glandular epithelium.",
                meaning=CL["0009084"]))
        setattr(cls, "CL:2000023",
            PermissibleValue(
                text="CL:2000023",
                description="Any interneuron that is part of a spinal cord ventral column.",
                meaning=CL["2000023"]))
        setattr(cls, "CL:0004229",
            PermissibleValue(
                text="CL:0004229",
                description="""A bistratified amacrine cell with a small dendritic field that has dendrite stratification in S2, and in S3 and S4.""",
                meaning=CL["0004229"]))
        setattr(cls, "CL:0002676",
            PermissibleValue(
                text="CL:0002676",
                description="A neuroblast derived from a neural crest cell.",
                meaning=CL["0002676"]))
        setattr(cls, "CL:0002091",
            PermissibleValue(
                text="CL:0002091",
                description="A small cell formed by the first meiotic division of oocytes.",
                meaning=CL["0002091"]))
        setattr(cls, "CL:0001064",
            PermissibleValue(
                text="CL:0001064",
                description="A neoplastic cell that is capable of entering a surrounding tissue",
                meaning=CL["0001064"]))
        setattr(cls, "CL:4047038",
            PermissibleValue(
                text="CL:4047038",
                description="""A multipolar neuron in the myenteric plexus of the gastrointestinal tract, characterized by a small to medium-sized cell body and multiple short dendrites.  This neuron exhibits fast excitatory postsynaptic potentials and can be classified into stubby, spiny and hairy subtypes based on dendritic morphology. (Brehmer, 2021)""",
                meaning=CL["4047038"]))
        setattr(cls, "CL:0000615",
            PermissibleValue(
                text="CL:0000615",
                description="""A thick walled spore containing one or more haploid nuclei produced by sexual reproduction in an Basidiomycete; formed externally on extrusions of the basidium.""",
                meaning=CL["0000615"]))
        setattr(cls, "CL:0005007",
            PermissibleValue(
                text="CL:0005007",
                description="""Kolmer-Agduhr neurons are ciliated GABAergic neurons that contact the central canal of the spinal cord and have ipsilateral ascending axons.""",
                meaning=CL["0005007"]))
        setattr(cls, "CL:0001012",
            PermissibleValue(
                text="CL:0001012",
                meaning=CL["0001012"]))
        setattr(cls, "CL:1000346",
            PermissibleValue(
                text="CL:1000346",
                description="An enterocyte that is part of the epithelium proper of large intestine.",
                meaning=CL["1000346"]))
        setattr(cls, "CL:0000061",
            PermissibleValue(
                text="CL:0000061",
                description="""Skeletogenic cell that produces cementum (a bony substance that covers the root of a tooth), is part of the odontogenic papilla, and develops from a precementoblast cell.""",
                meaning=CL["0000061"]))
        setattr(cls, "CL:0000687",
            PermissibleValue(
                text="CL:0000687",
                meaning=CL["0000687"]))
        setattr(cls, "CL:0000148",
            PermissibleValue(
                text="CL:0000148",
                description="""A pigment cell derived from the neural crest. Contains melanin-filled pigment granules, which gives a brown to black appearance.""",
                meaning=CL["0000148"]))
        setattr(cls, "CL:1000370",
            PermissibleValue(
                text="CL:1000370",
                description="A transitional myocyte that is part of the left branch of atrioventricular bundle.",
                meaning=CL["1000370"]))
        setattr(cls, "CL:0002372",
            PermissibleValue(
                text="CL:0002372",
                description="""A transversely striated, multinucleated syncytial muscle cell, formed by the fusion of myoblasts during muscle development.""",
                meaning=CL["0002372"]))
        setattr(cls, "CL:0000430",
            PermissibleValue(
                text="CL:0000430",
                description="""A pigment cell derived from the neural crest. Contains cartenoid pigments in structures called pterinosomes or xanthosomes. This gives an appearance ranging from a golden yellow to orange and red.""",
                meaning=CL["0000430"]))
        setattr(cls, "CL:0009026",
            PermissibleValue(
                text="CL:0009026",
                description="An enterocyte that is a part of a vermiform appendix.",
                meaning=CL["0009026"]))
        setattr(cls, "CL:1001569",
            PermissibleValue(
                text="CL:1001569",
                description="An interneuron with a soma found in the hippocampus.",
                meaning=CL["1001569"]))
        setattr(cls, "CL:0002386",
            PermissibleValue(
                text="CL:0002386",
                description="A macroconidium that has more than one nucleus.",
                meaning=CL["0002386"]))
        setattr(cls, "CL:0002299",
            PermissibleValue(
                text="CL:0002299",
                description="""An epithelial cell scattered in the cortex, predominant in the outer cortex with a large pale nucleus and a prominent nucleolus.""",
                meaning=CL["0002299"]))
        setattr(cls, "CL:0000383",
            PermissibleValue(
                text="CL:0000383",
                meaning=CL["0000383"]))
        setattr(cls, "CL:0002127",
            PermissibleValue(
                text="CL:0002127",
                description="""A T cell with a receptor of limited diversity that is capable of immediate effector functions upon stimulation.""",
                meaning=CL["0002127"]))
        setattr(cls, "CL:0003044",
            PermissibleValue(
                text="CL:0003044",
                description="""A bistratified ganglion cell with small, dense dendritic fields that terminate in S1 and S3.""",
                meaning=CL["0003044"]))
        setattr(cls, "CL:1000444",
            PermissibleValue(
                text="CL:1000444",
                description="A mesothelial cell that is part of the anterior chamber of eyeball.",
                meaning=CL["1000444"]))
        setattr(cls, "CL:0002195",
            PermissibleValue(
                text="CL:0002195",
                description="""A stem cell that can give rise to the cells of the liver. The term usually refers to the self-renewing pool of hepatocyte precursors in the adult liver (differently from 'hepatoblast', often used for fetal precursors of hepatocytes).""",
                meaning=CL["0002195"]))
        setattr(cls, "CL:0003050",
            PermissibleValue(
                text="CL:0003050",
                description="""A cone cell that detects short wavelength light. Exact peak of spectra detected differs between species. In humans, spectra peaks at 420-440 nm.""",
                meaning=CL["0003050"]))
        setattr(cls, "CL:0000873",
            PermissibleValue(
                text="CL:0000873",
                description="""A splenic macrophage found in the areas surrounding the white pulp of the spleen, adjacent to the marginal sinus. Markers include F4/80-negative, Dectin2-low, sialoadhesin-positive.""",
                meaning=CL["0000873"]))
        setattr(cls, "CL:0002589",
            PermissibleValue(
                text="CL:0002589",
                description="A smooth muscle cell of the bachiocephalic vasculature.",
                meaning=CL["0002589"]))
        setattr(cls, "CL:0009037",
            PermissibleValue(
                text="CL:0009037",
                description="""A B lymphocyte that resides in the mantle zone of the lymph node germinal center. These are generally IgM and IgD positive activated B cells that form a 'corona' around the germinal center and are part of the establishment of a secondary lymphatic follicule.""",
                meaning=CL["0009037"]))
        setattr(cls, "CL:0005022",
            PermissibleValue(
                text="CL:0005022",
                description="""Lymphatic progenitor cells, derived from the veins, that give rise to lymphatic endothelial cells.""",
                meaning=CL["0005022"]))
        setattr(cls, "CL:0002099",
            PermissibleValue(
                text="CL:0002099",
                description="""A small, polyhedral, cell found in rounded groups or curved columns with deeply staining nuclei, scanty basophilic cytoplasm and a few lipid droplets. This cell in the zona glomerulosa produces mineralocorticoids.""",
                meaning=CL["0002099"]))
        setattr(cls, "CL:0000242",
            PermissibleValue(
                text="CL:0000242",
                description="""A modified epidermal cell located in the stratum basale. They are found mostly in areas where sensory perception is acute. Merkel cells are closely associated with an expanded terminal bulb of an afferent myelinated nerve fiber.""",
                meaning=CL["0000242"]))
        setattr(cls, "CL:0000829",
            PermissibleValue(
                text="CL:0000829",
                description="A myeloblast committed to the basophil lineage.",
                meaning=CL["0000829"]))
        setattr(cls, "CL:0003047",
            PermissibleValue(
                text="CL:0003047",
                description="""A bistratifed retinal ganglion cell that has small, symmetric dendritic fields that terminate in S1 and S4-S5.""",
                meaning=CL["0003047"]))
        setattr(cls, "CL:1000546",
            PermissibleValue(
                text="CL:1000546",
                description="An epithelial cell that is part of a renal medulla collecting duct.",
                meaning=CL["1000546"]))
        setattr(cls, "CL:0000464",
            PermissibleValue(
                text="CL:0000464",
                description="""An epidermal progenitor cell that arises from neuroectoderm and in turn gives rise to the epidermal sheath of ventral and cephalic regions.""",
                meaning=CL["0000464"]))
        setattr(cls, "CL:0002413",
            PermissibleValue(
                text="CL:0002413",
                description="A Vgamma1.1-positive, Vdelta6.3-negative thymocyte that is CD24-negative.",
                meaning=CL["0002413"]))
        setattr(cls, "CL:4047006",
            PermissibleValue(
                text="CL:4047006",
                description="An endothelial cell that lines an artery in the fetal circulatory system.",
                meaning=CL["4047006"]))
        setattr(cls, "CL:0002515",
            PermissibleValue(
                text="CL:0002515",
                description="""An interrenal chromaffin cell found in teleosts that contain heterogeneous vesicles with electron-dense granules located asymmetrically within the vesicular membrane.""",
                meaning=CL["0002515"]))
        setattr(cls, "CL:4052033",
            PermissibleValue(
                text="CL:4052033",
                description="""A tuft cell that is part of the extrahepatic biliary tree, including the gallbladder and extrahepatic bile ducts. It shares a core genetic program with intestinal tuft cells but has unique tissue-specific genes. Biliary tuft cell functions as a bile acid-sensitive regulator, suppressing inflammation and modulating microbiome-dependent neutrophil infiltration in biliary tissues. Unlike its intestinal counterparts, this cell decreases in number postnatally as bile acid production matures, with its abundance negatively regulated by bile acids.""",
                meaning=CL["4052033"]))
        setattr(cls, "CL:0002492",
            PermissibleValue(
                text="CL:0002492",
                description="""A polarized columnar cell that covesr the lateral surface of the cochlear duct, secretes potassium ions and forms a continuous sheet in contact with the endolymph; marginal cells form extensive interdigitations with the basal and intermediate cells in the normal adult stria.""",
                meaning=CL["0002492"]))
        setattr(cls, "CL:0002073",
            PermissibleValue(
                text="CL:0002073",
                description="""Specialized cardiac myocyte which is in the internodal tract and atrioventricular node. The cell is more slender than ordinary atrial myocytes and has more myofibrils than nodal myocytes.""",
                meaning=CL["0002073"]))
        setattr(cls, "CL:1000377",
            PermissibleValue(
                text="CL:1000377",
                description="A Feyrter cell that is part of the epithelium of trachea.",
                meaning=CL["1000377"]))
        setattr(cls, "CL:1000155",
            PermissibleValue(
                text="CL:1000155",
                description="""A specialized epithelial secretory cell that moves chloride ions and water across the tubule epithelium.""",
                meaning=CL["1000155"]))
        setattr(cls, "CL:0003036",
            PermissibleValue(
                text="CL:0003036",
                description="""A monostratified retinal ganglion cell with large soma and large dendritic field, with medium dendritic arbor, and has dendrites in layers 2 and 5.""",
                meaning=CL["0003036"]))
        setattr(cls, "CL:1000742",
            PermissibleValue(
                text="CL:1000742",
                description="A mesangial cell located among the glomerular capillaries in a renal corpuscle.",
                meaning=CL["1000742"]))
        setattr(cls, "CL:0001025",
            PermissibleValue(
                text="CL:0001025",
                description="""A common lymphoid progenitor that is Kit-low, FLT3-positive, IL7ralpha-positive, and SCA1-low.""",
                meaning=CL["0001025"]))
        setattr(cls, "CL:0004183",
            PermissibleValue(
                text="CL:0004183",
                description="""A monostratified retinal ganglion cell with medium soma, sparse dendritic tree, and medium dendritic field.""",
                meaning=CL["0004183"]))
        setattr(cls, "CL:1000288",
            PermissibleValue(
                text="CL:1000288",
                description="A muscle cell that is part of the atrial branch of anterior internodal tract.",
                meaning=CL["1000288"]))
        setattr(cls, "CL:0002510",
            PermissibleValue(
                text="CL:0002510",
                description="A langerin-positive lymph node dendritic cell that is CD103-negative and CD11b-high.",
                meaning=CL["0002510"]))
        setattr(cls, "CL:0002494",
            PermissibleValue(
                text="CL:0002494",
                description="A cell located in the heart, including both muscle and non muscle cells.",
                meaning=CL["0002494"]))
        setattr(cls, "CL:2000070",
            PermissibleValue(
                text="CL:2000070",
                description="Any fibroblast that is part of a optic choroid.",
                meaning=CL["2000070"]))
        setattr(cls, "CL:0002131",
            PermissibleValue(
                text="CL:0002131",
                description="Regular cardiac myocyte of a cardiac ventricle.",
                meaning=CL["0002131"]))
        setattr(cls, "CL:0001073",
            PermissibleValue(
                text="CL:0001073",
                description="""An innate lymphoid cell in the human with the phenotype CD34-negative, CD56-positive, CD117-positive.Thie cell type may include precusors to NK cells and ILC3 cells.""",
                meaning=CL["0001073"]))
        setattr(cls, "CL:4023050",
            PermissibleValue(
                text="CL:4023050",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in L6 of the primary motor cortex. These cells are short untufted pyramidal cells, which could be stellate or inverted.""",
                meaning=CL["4023050"]))
        setattr(cls, "CL:0002426",
            PermissibleValue(
                text="CL:0002426",
                description="A mature natural killer cell that is CD11b-positive and CD27-positive.",
                meaning=CL["0002426"]))
        setattr(cls, "CL:0002167",
            PermissibleValue(
                text="CL:0002167",
                description="A specialized cell involved in sensory perception of smell.",
                meaning=CL["0002167"]))
        setattr(cls, "CL:1000001",
            PermissibleValue(
                text="CL:1000001",
                description="Any neuron that has its soma located in some retrotrapezoid nucleus.",
                meaning=CL["1000001"]))
        setattr(cls, "CL:0000604",
            PermissibleValue(
                text="CL:0000604",
                description="""One of the two photoreceptor cell types of the vertebrate retina. In rods the photopigment is in stacks of membranous disks separate from the outer cell membrane. Rods are more sensitive to light than cones, but rod mediated vision has less spatial and temporal resolution than cone vision.""",
                meaning=CL["0000604"]))
        setattr(cls, "CL:0009057",
            PermissibleValue(
                text="CL:0009057",
                description="A goblet cell that is located in the anorectum.",
                meaning=CL["0009057"]))
        setattr(cls, "CL:0000702",
            PermissibleValue(
                text="CL:0000702",
                meaning=CL["0000702"]))
        setattr(cls, "CL:0003037",
            PermissibleValue(
                text="CL:0003037",
                description="""An M7 retinal ganglion cells with synaptic terminals in S4 and is depolarized by illumination of its receptive field center.""",
                meaning=CL["0003037"]))
        setattr(cls, "CL:4023107",
            PermissibleValue(
                text="CL:4023107",
                description="""A neuron with soma location in the reticular formation with axons that extend into the spinal cord such. Reticulospinal neuron activity can lead to a variety of motor behaviors.""",
                meaning=CL["4023107"]))
        setattr(cls, "CL:0002057",
            PermissibleValue(
                text="CL:0002057",
                description="""A classical monocyte that is CD14-positive, CD16-negative, CD64-positive, CD163-positive.""",
                meaning=CL["0002057"]))
        setattr(cls, "CL:4033032",
            PermissibleValue(
                text="CL:4033032",
                description="""An ON diffuse bipolar cell that has a large dendritic field and large axon terminals, which show little or no overlap. This cell predominantly connects to narrow thorny ganglion cells.""",
                meaning=CL["4033032"]))
        setattr(cls, "CL:4033005",
            PermissibleValue(
                text="CL:4033005",
                description="A(n) serous secreting cell that is part of a(n) bronchus submucosal gland.",
                meaning=CL["4033005"]))
        setattr(cls, "CL:0000917",
            PermissibleValue(
                text="CL:0000917",
                description="""A CD8-positive, alpha-beta positive T cell that has the phenotype T-bet-positive, eomesodermin-positive, CXCR3-positive, CCR6-negative, and is capable of producing interferon-gamma.""",
                meaning=CL["0000917"]))
        setattr(cls, "CL:0002431",
            PermissibleValue(
                text="CL:0002431",
                description="""A double-positive thymocyte that is undergoing positive selection, has high expression of the alpha-beta T cell receptor, is CD69-positive, and is in the process of down regulating the CD8 co-receptor.""",
                meaning=CL["0002431"]))
        setattr(cls, "CL:4052031",
            PermissibleValue(
                text="CL:4052031",
                description="A secretory epithelial cell of the respiratory and terminal bronchioles.",
                meaning=CL["4052031"]))
        setattr(cls, "CL:4047045",
            PermissibleValue(
                text="CL:4047045",
                description="""An enteric glial cell located in the lamina propria of the intestinal mucosa. This cell plays important roles in maintaining gut barrier function, regulating intestinal homeostasis, and mediating interactions between the enteric nervous system and the immune system.""",
                meaning=CL["4047045"]))
        setattr(cls, "CL:0011013",
            PermissibleValue(
                text="CL:0011013",
                description="A sperm cell that is cabaple of motion (motility).",
                meaning=CL["0011013"]))
        setattr(cls, "CL:4052022",
            PermissibleValue(
                text="CL:4052022",
                description="""A smooth muscle cell that is part of the fallopian tube. This cell is responsible for peristaltic contractions that facilitate gamete and embryo transport, fluid mixing, and embryo admission to the uterus.""",
                meaning=CL["4052022"]))
        setattr(cls, "CL:0000821",
            PermissibleValue(
                text="CL:0000821",
                description="""A B-1 B cell that has the phenotype CD5-negative, but having other phenotypic attributes of a B-1 B cell.""",
                meaning=CL["0000821"]))
        setattr(cls, "CL:0000973",
            PermissibleValue(
                text="CL:0000973",
                description="A class switched memory B cell that expresses IgA.",
                meaning=CL["0000973"]))
        setattr(cls, "CL:0000671",
            PermissibleValue(
                text="CL:0000671",
                description="""A follicle cell that migrates from the dorso-anterior part of the oocyte associated follicular epithelium, in between the nurse cells and the oocyte, and participates in the formation of the operculum.""",
                meaning=CL["0000671"]))
        setattr(cls, "CL:1000359",
            PermissibleValue(
                text="CL:1000359",
                description="A M cell that is part of the epithelium proper of appendix.",
                meaning=CL["1000359"]))
        setattr(cls, "CL:1000320",
            PermissibleValue(
                text="CL:1000320",
                description="A goblet cell that is part of the epithelium of large intestine.",
                meaning=CL["1000320"]))
        setattr(cls, "CL:0000657",
            PermissibleValue(
                text="CL:0000657",
                description="""One of the two haploid cells into which a primary spermatocyte divides, and which in turn gives origin to spermatids.""",
                meaning=CL["0000657"]))
        setattr(cls, "CL:0000705",
            PermissibleValue(
                text="CL:0000705",
                meaning=CL["0000705"]))
        setattr(cls, "CL:0002601",
            PermissibleValue(
                text="CL:0002601",
                description="A smooth muscle cell of the uterus.",
                meaning=CL["0002601"]))
        setattr(cls, "CL:0000598",
            PermissibleValue(
                text="CL:0000598",
                description="""Pyramidal neurons have a pyramid-shaped soma with a single axon, a large apical dendrite and multiple basal dendrites. The apex and an apical dendrite typically point toward the pial surface and other dendrites and an axon emerging from the base. The axons may have local collaterals but also project outside their region. Pyramidal neurons are found in the cerebral cortex, the hippocampus, and the amygdala.""",
                meaning=CL["0000598"]))
        setattr(cls, "CL:0000327",
            PermissibleValue(
                text="CL:0000327",
                meaning=CL["0000327"]))
        setattr(cls, "CL:1000471",
            PermissibleValue(
                text="CL:1000471",
                description="A myoepithelial cell that is part of the secondary lactiferous duct.",
                meaning=CL["1000471"]))
        setattr(cls, "CL:1000310",
            PermissibleValue(
                text="CL:1000310",
                description="An adipocyte that is part of the epicardial fat of right ventricle.",
                meaning=CL["1000310"]))
        setattr(cls, "CL:4032000",
            PermissibleValue(
                text="CL:4032000",
                description="""An epithelial cell of the urethra that has an expression profile similar to lung club cells. Club-like cells of the urethra epithelium are similar to lung club cells in their expression of SCGB1A1 and in their enrichment of immunomodulatory programs.""",
                meaning=CL["4032000"]))
        setattr(cls, "CL:0000016",
            PermissibleValue(
                text="CL:0000016",
                description="A stem cell that is the precursor of male gametes.",
                meaning=CL["0000016"]))
        setattr(cls, "CL:0002645",
            PermissibleValue(
                text="CL:0002645",
                description="An endocranial viscerocranial mucosa cell that is part of viscerocranial mucosa.",
                meaning=CL["0002645"]))
        setattr(cls, "CL:0015000",
            PermissibleValue(
                text="CL:0015000",
                description="""Motor neuron that innervate muscles that control eye, jaw, and facial movements of the vertebrate head and parasympathetic neurons that innervate certain glands and organs.""",
                meaning=CL["0015000"]))
        setattr(cls, "CL:1001099",
            PermissibleValue(
                text="CL:1001099",
                description="Any endothelial cell that is part of some renal efferent arteriole.",
                meaning=CL["1001099"]))
        setattr(cls, "CL:2000029",
            PermissibleValue(
                text="CL:2000029",
                description="Any neuron that is part of a central nervous system.",
                meaning=CL["2000029"]))
        setattr(cls, "CL:0000733",
            PermissibleValue(
                text="CL:0000733",
                description="A plasmatocyte that derives from the larval lymph gland.",
                meaning=CL["0000733"]))
        setattr(cls, "CL:4033021",
            PermissibleValue(
                text="CL:4033021",
                description="A myoepithelial cell that is part of a submucosal gland of the trachea.",
                meaning=CL["4033021"]))
        setattr(cls, "CL:0002462",
            PermissibleValue(
                text="CL:0002462",
                description="A F4/80-negative dendritic cell located in adipose tissue.",
                meaning=CL["0002462"]))
        setattr(cls, "CL:0000596",
            PermissibleValue(
                text="CL:0000596",
                description="""A spore formed following meiosis. Sometimes following meiosis, prospores may undergo one or more rounds of mitosis before they are fully mature.""",
                meaning=CL["0000596"]))
        setattr(cls, "CL:0009070",
            PermissibleValue(
                text="CL:0009070",
                description="A thymic epithelial cell located at the corticomedullary junction.",
                meaning=CL["0009070"]))
        setattr(cls, "CL:2000054",
            PermissibleValue(
                text="CL:2000054",
                description="""A large, granular, liver specific natural killer cell that adheres to the endothelial cells of the hepatic sinusoid.""",
                meaning=CL["2000054"]))
        setattr(cls, "CL:4030034",
            PermissibleValue(
                text="CL:4030034",
                description="""A multiciliated epithelial cell located in the respiratory tract epithelium, characterized by a columnar shape and motile cilia on its apical surface. This cell develops through a highly orchestrated process, transitioning from a basal progenitor via an intermediate deuterosomal cell stage that generates centrioles essential for ciliogenesis.""",
                meaning=CL["4030034"]))
        setattr(cls, "CL:0002033",
            PermissibleValue(
                text="CL:0002033",
                description="""A hematopoietic stem cell capable of rapid replenishment of myeloerythroid progenitors and limited self renewal capability. This cell is Kit-positive, Sca1-positive, CD34-positive, CD150-positive, and is Flt3-negative.""",
                meaning=CL["0002033"]))
        setattr(cls, "CL:0004119",
            PermissibleValue(
                text="CL:0004119",
                description="""A retinal ganglion cell B that has medium body size, medium dendritic field and dense dendritic arbor, and has post synaptic terminals in S2.""",
                meaning=CL["0004119"]))
        setattr(cls, "CL:0000360",
            PermissibleValue(
                text="CL:0000360",
                description="""A cell of the early embryo at the developmental stage in which the blastomeres, resulting from repeated mitotic divisions of the fertilized ovum (zygote), form a compact cell mass.""",
                meaning=CL["0000360"]))
        setattr(cls, "CL:0000515",
            PermissibleValue(
                text="CL:0000515",
                description="A myoblast that differentiates into skeletal muscle fibers.",
                meaning=CL["0000515"]))
        setattr(cls, "CL:2000056",
            PermissibleValue(
                text="CL:2000056",
                description="Any pyramidal cell that is part of a regional part of cerebral cortex.",
                meaning=CL["2000056"]))
        setattr(cls, "CL:0007020",
            PermissibleValue(
                text="CL:0007020",
                description="""Characteristic early embryonic cell with a bottle or flask shape that is first to migrate inwards at the blastopore during gastrulation in amphibians.""",
                meaning=CL["0007020"]))
        setattr(cls, "CL:0002018",
            PermissibleValue(
                text="CL:0002018",
                description="An erythroblast that is GlyA-positive and CD71-negative.",
                meaning=CL["0002018"]))
        setattr(cls, "CL:2000081",
            PermissibleValue(
                text="CL:2000081",
                description="Any melanocyte of skin that is part of a skin of face.",
                meaning=CL["2000081"]))
        setattr(cls, "CL:4023068",
            PermissibleValue(
                text="CL:4023068",
                description="""An excitatory neuron that has its soma located in the thalamic complex. This neuron type can be involved in a series of circuits related to sensory integration, motor integration, pain processing, social behaviour and reward response.""",
                meaning=CL["4023068"]))
        setattr(cls, "CL:1001216",
            PermissibleValue(
                text="CL:1001216",
                description="Any endothelial cell that is part of some interlobular artery.",
                meaning=CL["1001216"]))
        setattr(cls, "CL:0000000",
            PermissibleValue(
                text="CL:0000000",
                description="""A material entity of anatomical origin (part of or deriving from an organism) that has as its parts a maximally connected cell compartment surrounded by a plasma membrane.""",
                meaning=CL["0000000"]))
        setattr(cls, "CL:1000364",
            PermissibleValue(
                text="CL:1000364",
                description="A transitional myocyte that is part of the anterior internodal tract.",
                meaning=CL["1000364"]))
        setattr(cls, "CL:0000238",
            PermissibleValue(
                text="CL:0000238",
                meaning=CL["0000238"]))
        setattr(cls, "CL:0003040",
            PermissibleValue(
                text="CL:0003040",
                description="""A monostratified retinal ganglion cell with large soma and large dendritic field, with medium dendritic arbor, and has dendrites in layers 1 and 5.""",
                meaning=CL["0003040"]))
        setattr(cls, "CL:0009023",
            PermissibleValue(
                text="CL:0009023",
                description="A T cell which resides in the Peyer's patch of the small intestine.",
                meaning=CL["0009023"]))
        setattr(cls, "CL:0000593",
            PermissibleValue(
                text="CL:0000593",
                description="A steroid hormone secreting cell that secretes androgen.",
                meaning=CL["0000593"]))
        setattr(cls, "CL:4047001",
            PermissibleValue(
                text="CL:4047001",
                description="A(n) stromal cell that is cycling.",
                meaning=CL["4047001"]))
        setattr(cls, "CL:0002447",
            PermissibleValue(
                text="CL:0002447",
                description="A NK1.1-positive T cell that is CD94-negative.",
                meaning=CL["0002447"]))
        setattr(cls, "CL:1000411",
            PermissibleValue(
                text="CL:1000411",
                description="An endothelial cell that is part of the small intestine Peyer's patch.",
                meaning=CL["1000411"]))
        setattr(cls, "CL:4052042",
            PermissibleValue(
                text="CL:4052042",
                description="""A tuft cell that is part of the epithelium of the urethra. This cell monitors urethral contents by detecting chemical stimuli, such as bitter compounds and sugars. Upon activation, it stimulates sensory nerve fibres and triggers detrusor muscle contraction, likely aiding in pathogen clearance by promoting bladder emptying.""",
                meaning=CL["4052042"]))
        setattr(cls, "CL:0000420",
            PermissibleValue(
                text="CL:0000420",
                description="""An epithelial cell that forms a syncytium, which is a multinucleated cell resulting from the fusion of multiple cells.""",
                meaning=CL["0000420"]))
        setattr(cls, "CL:1000375",
            PermissibleValue(
                text="CL:1000375",
                description="""A myocardial endocrine cell that is part of the septal division of left branch of atrioventricular bundle.""",
                meaning=CL["1000375"]))
        setattr(cls, "CL:0000834",
            PermissibleValue(
                text="CL:0000834",
                description="A progenitor cell of the neutrophil lineage.",
                meaning=CL["0000834"]))
        setattr(cls, "CL:0000994",
            PermissibleValue(
                text="CL:0000994",
                description="""Immature CD11c-negative plasmacytoid dendritic cell is a CD11c-negative plasmacytoid dendritic cell is CD80-negative, CD86-low and MHCII-low.""",
                meaning=CL["0000994"]))
        setattr(cls, "CL:0002268",
            PermissibleValue(
                text="CL:0002268",
                description="An enteroendocrine cell that stores and secretes Ghrelin.",
                meaning=CL["0002268"]))
        setattr(cls, "CL:0000880",
            PermissibleValue(
                text="CL:0000880",
                description="""A border associated macrophage found at the interface between the blood and the cerebrospinal fluid in the brain. This central nervous system macrophage has a star-like shaped body and expresses scavenger receptors.""",
                meaning=CL["0000880"]))
        setattr(cls, "CL:4052021",
            PermissibleValue(
                text="CL:4052021",
                description="""A CD8 T cell characterized by high expression of Granzyme K (GZMK). This cell is enriched in both inflamed tissues, such as synovial tissue in rheumatoid arthritis and respiratory tissues during COVID-19, as well as non-inflamed tissues like the gut and kidneys. Unlike highly cytotoxic GZMB+ CD8+ T cell, GZMK+ CD8+ T cell exhibits lower direct cytotoxic potential, and is involved in producing pro-inflammatory cytokines such as IFN-γ and TNF-α.""",
                meaning=CL["4052021"]))
        setattr(cls, "CL:0002168",
            PermissibleValue(
                text="CL:0002168",
                description="""A border cell is a slender columnar cell on the medial portion of the basilar membrane.""",
                meaning=CL["0002168"]))
        setattr(cls, "CL:0000351",
            PermissibleValue(
                text="CL:0000351",
                description="""An extraembryonic cell that develops from a trophectodermal cell. This cell is found in the outer layer of the blastocyst and can invade other structures in the uterus once the blastocyst implants into the uterine wall. A trophoblast cell is involved in the implantation of the embryo into the uterine wall, placental formation, remodelling of maternal vasculature in the uterus, nutrient and gas exchange, hormone production, and immune modulation to support fetal development.""",
                meaning=CL["0000351"]))
        setattr(cls, "CL:0000896",
            PermissibleValue(
                text="CL:0000896",
                description="""A recently activated CD4-positive, alpha-beta T cell with the phenotype CD69-positive, CD62L-negative, CD127-negative, and CD25-positive.""",
                meaning=CL["0000896"]))
        setattr(cls, "CL:0000095",
            PermissibleValue(
                text="CL:0000095",
                meaning=CL["0000095"]))
        setattr(cls, "CL:0002208",
            PermissibleValue(
                text="CL:0002208",
                description="A brush cell found in the epithelium of bronchus.",
                meaning=CL["0002208"]))
        setattr(cls, "CL:0004246",
            PermissibleValue(
                text="CL:0004246",
                description="A central nervous system neuron that stratifies at one and only one location.",
                meaning=CL["0004246"]))
        setattr(cls, "CL:0002491",
            PermissibleValue(
                text="CL:0002491",
                description="A specialized cell involved in auditory sensory perception.",
                meaning=CL["0002491"]))
        setattr(cls, "CL:0000508",
            PermissibleValue(
                text="CL:0000508",
                description="""An endocrine cell found in the stomach and duodenum and is responsible for the secretion of gastrin and enkephalin. Most abundant in pyloric antrum, pyramidal in form with a narrow apex bearing long microvilli.""",
                meaning=CL["0000508"]))
        setattr(cls, "CL:0002660",
            PermissibleValue(
                text="CL:0002660",
                description="A luminal epithelial cell of mammary gland located in acinus of structure.",
                meaning=CL["0002660"]))
        setattr(cls, "CL:4023113",
            PermissibleValue(
                text="CL:4023113",
                description="A vestibular afferent neuron that makes bouton synapses to type II hair cells.",
                meaning=CL["4023113"]))
        setattr(cls, "CL:0001010",
            PermissibleValue(
                text="CL:0001010",
                description="""Mature dermal dendritic cell is a dermal dendritic cell that is CD80-high, CD86-high, MHCII-high and is CD83-positive.""",
                meaning=CL["0001010"]))
        setattr(cls, "CL:4023014",
            PermissibleValue(
                text="CL:4023014",
                description="""A VIP GABAergic cortical interneuron with a soma found in L5. L5 VIP cells have mostly local morphology with some deep-projecting axons. They show only moderate resistance, comparable to that of sst subclass and unlike typical VIP subclass cells that tend to show high input resistance. L5 VIP cells show particularly low resting membrane potential.""",
                meaning=CL["4023014"]))
        setattr(cls, "CL:0002214",
            PermissibleValue(
                text="CL:0002214",
                description="""A type II muscle cell that contains large amounts of myoglobin, has many mitochondria and very many blood capillaries. Type II A cells are red, have a very high capacity for generating ATP by oxidative metabolic processes, split ATP at a very rapid rate, have a fast contraction velocity and are resistant to fatigue.""",
                meaning=CL["0002214"]))
        setattr(cls, "CL:0000378",
            PermissibleValue(
                text="CL:0000378",
                meaning=CL["0000378"]))
        setattr(cls, "CL:1000491",
            PermissibleValue(
                text="CL:1000491",
                description="A mesothelial cell that is part of the pleura.",
                meaning=CL["1000491"]))
        setattr(cls, "CL:0001007",
            PermissibleValue(
                text="CL:0001007",
                description="""Interstitial dendritic cell is a conventional dendritic cell that is CD11b-positive, CD1a-positive, CD206-positive, CD209-positive, and CD36-positive.""",
                meaning=CL["0001007"]))
        setattr(cls, "CL:0000612",
            PermissibleValue(
                text="CL:0000612",
                description="""A eosinophil precursor in the granulocytic series, being a cell intermediate in development between a promyelocyte and a metamyelocyte;in this stage, production of primary granules is complete and eosinophil-specific granules has started. No nucleolus is present. These cells are integrin alpha-M-positive, CD13-positive, CD15-positive, CD16-negative, CD24-positive, and CD33-positive.""",
                meaning=CL["0000612"]))
        setattr(cls, "CL:0002136",
            PermissibleValue(
                text="CL:0002136",
                description="A cell in the zona fasciculata that produce glucocorticoids, e.g cortisol.",
                meaning=CL["0002136"]))
        setattr(cls, "CL:0002100",
            PermissibleValue(
                text="CL:0002100",
                description="A regular cardiac myocyte of the interventricular region of the heart.",
                meaning=CL["0002100"]))
        setattr(cls, "CL:4033087",
            PermissibleValue(
                text="CL:4033087",
                description="""A tissue-resident macrophage that is part of the placenta. This cell helps preventing immunological rejection of the fetus by modulating the immune environment. A placental resident macrophage has high plasticity to adapt to the changing needs of each phase of pregnancy.""",
                meaning=CL["4033087"]))
        setattr(cls, "CL:0008047",
            PermissibleValue(
                text="CL:0008047",
                description="""A skeletal muscle fiber that is part of a muscle spindle. These are specialized muscle fibers that serve as proprioceptors, detecting the amount and rate of change in length of a muscle. They are innervated by both sensory neurons and motor neurons (gamma and beta motorneurons, collectively referred to as fusimotor neurons).""",
                meaning=CL["0008047"]))
        setattr(cls, "CL:0002056",
            PermissibleValue(
                text="CL:0002056",
                description="""A mature B cell subset originally defined as having being CD45R-positive, IgM-positive, IgD-positive and CD43-negative. Subsequent research demonstrated being CD21-positive and CD23-negative and CD93 negative.""",
                meaning=CL["0002056"]))
        setattr(cls, "CL:0002442",
            PermissibleValue(
                text="CL:0002442",
                description="A NK1.1-positive T cell that is CD94-negative and Ly49Cl-negative.",
                meaning=CL["0002442"]))
        setattr(cls, "CL:0002058",
            PermissibleValue(
                text="CL:0002058",
                description="A resident monocyte that is Gr-1 low, CD43-positive, and CX3CR1-positive.",
                meaning=CL["0002058"]))
        setattr(cls, "CL:0010020",
            PermissibleValue(
                text="CL:0010020",
                description="Any glial cell that is part of some heart.",
                meaning=CL["0010020"]))
        setattr(cls, "CL:0002238",
            PermissibleValue(
                text="CL:0002238",
                description="A primordial germ cell that is destined to become a male germ cell.",
                meaning=CL["0002238"]))
        setattr(cls, "CL:0000440",
            PermissibleValue(
                text="CL:0000440",
                description="A cell of the intermediate pituitary that produces melanocyte stimulating hormone.",
                meaning=CL["0000440"]))
        setattr(cls, "CL:1000469",
            PermissibleValue(
                text="CL:1000469",
                description="A myoepithelial cell that is part of the main lactiferous duct.",
                meaning=CL["1000469"]))
        setattr(cls, "CL:1000222",
            PermissibleValue(
                text="CL:1000222",
                description="""A specialised neuroendocrine cell located in the gastric mucosa that regulates digestive processes including acid secretion and gut motility. This cell stores hormones in large dense core vesicles and synaptic-like microvesicles.""",
                meaning=CL["1000222"]))
        setattr(cls, "CL:0000164",
            PermissibleValue(
                text="CL:0000164",
                description="""An endocrine cell that is located in the epithelium of the gastrointestinal tract or in the pancreas.""",
                meaning=CL["0000164"]))
        setattr(cls, "CL:4023051",
            PermissibleValue(
                text="CL:4023051",
                description="""A transcriptomically distinct type of mesothelial fibroblast that is derived from the neural crest, is localized on blood vessels, and is a key component of the pia and arachnoid membranes surrounding the brain. The standard transcriptomic reference data for this cell type can be found on the CellxGene census under the collection: 'Transcriptomic cytoarchitecture reveals principles of human neocortex organization', dataset: 'Supercluster: Non-neuronal cells', Author Categories: 'CrossArea_subclass', clusters VLMC.""",
                meaning=CL["4023051"]))
        setattr(cls, "CL:1000331",
            PermissibleValue(
                text="CL:1000331",
                description="A serous secreting cell that is part of the epithelium of bronchus.",
                meaning=CL["1000331"]))
        setattr(cls, "CL:0000092",
            PermissibleValue(
                text="CL:0000092",
                description="""A specialized phagocytic cell associated with the absorption and removal of the mineralized matrix of bone tissue, which typically differentiates from monocytes. This cell has the following markers: tartrate-resistant acid phosphatase type 5-positive, PU.1-positive, c-fos-positive, nuclear factor NF-kappa-B p100 subunit-positive, tumor necrosis factor receptor superfamily member 11A-positive and macrophage colony-stimulating factor 1 receptor-positive.""",
                meaning=CL["0000092"]))
        setattr(cls, "CL:0002565",
            PermissibleValue(
                text="CL:0002565",
                description="A pigment cell located in the epithelium of the iris.",
                meaning=CL["0002565"]))
        setattr(cls, "CL:0000895",
            PermissibleValue(
                text="CL:0000895",
                description="""An antigen inexperienced CD4-positive, alpha-beta T cell with the phenotype CCR7-positive, CD127-positive and CD62L-positive. This cell type develops in the thymus. This cell type is also described as being CD25-negative, CD62L-high, and CD44-low.""",
                meaning=CL["0000895"]))
        setattr(cls, "CL:0001075",
            PermissibleValue(
                text="CL:0001075",
                description="""An innate lymphoid cell in the human with the phenotype KLRG1-positive that is a precusor for ILC2 cells.""",
                meaning=CL["0001075"]))
        setattr(cls, "CL:0001200",
            PermissibleValue(
                text="CL:0001200",
                description="A lymphocyte of B lineage that is CD19-positive.",
                meaning=CL["0001200"]))
        setattr(cls, "CL:0002188",
            PermissibleValue(
                text="CL:0002188",
                description="""An endothelial cell that is part of the glomerulus of the kidney. This cell is flattened, highly fenestrated, and plays a vital role in the formation of glomerular ultrafiltrate.""",
                meaning=CL["0002188"]))
        setattr(cls, "CL:0003026",
            PermissibleValue(
                text="CL:0003026",
                description="""A bistratified retinal ganglion cell that has a small dendrite fields with a sparse dendrite arbor terminating in S2 and S3.""",
                meaning=CL["0003026"]))
        setattr(cls, "CL:0002271",
            PermissibleValue(
                text="CL:0002271",
                description="""A type EC enteredocrine cell in the intestines that stores and secretes substance P and 5-hydroxytryptamine.""",
                meaning=CL["0002271"]))
        setattr(cls, "CL:4052010",
            PermissibleValue(
                text="CL:4052010",
                description="""A stromal cell that serves as a precursor to the theca cell layers in the ovary growing follicles. This cell is present in the early stages of follicular growth, particularly in smaller follicles. Unlike mature theca cell, a pre-theca cell is initially non-steroidogenic and lacks luteinizing hormone receptors.""",
                meaning=CL["4052010"]))
        setattr(cls, "CL:0002499",
            PermissibleValue(
                text="CL:0002499",
                description="A trophoblast cell that arises in the junctional zone (basal plate) of the placenta.",
                meaning=CL["0002499"]))
        setattr(cls, "CL:0000786",
            PermissibleValue(
                text="CL:0000786",
                description="""A terminally differentiated, post-mitotic, antibody secreting cell of the B cell lineage with the phenotype CD138-positive, surface immunonoglobulin-negative, and MHC Class II-negative. Plasma cells are oval or round with extensive rough endoplasmic reticulum, a well-developed Golgi apparatus, and a round nucleus having a characteristic cartwheel heterochromatin pattern and are devoted to producing large amounts of immunoglobulin.""",
                meaning=CL["0000786"]))
        setattr(cls, "CL:0000983",
            PermissibleValue(
                text="CL:0000983",
                description="A plasmablast that secretes IgM.",
                meaning=CL["0000983"]))
        setattr(cls, "CL:4047017",
            PermissibleValue(
                text="CL:4047017",
                description="""A transit amplifying cell of the gut epithelium, located in the wall of the intestinal crypt, just above intestinal stem cells from which they derive. These are rapidly dividing cells, capable of multiple rounds of division before differentiating into the various cell types of the gut epithelium (enterocyte, goblet, eneterodendocrine, paneth cells).""",
                meaning=CL["4047017"]))
        setattr(cls, "CL:0000760",
            PermissibleValue(
                text="CL:0000760",
                description="""An ON-bipolar neuron found in the retina and having connections with cone photoreceptors cells and neurons in the inner half of the inner plexiform layer. This cell has the widest dendritic field and the widest axon terminal of all retinal bipolar cells. The axon terminal is delicate and stratified through sublaminae 4 and 5 of the inner plexiform layer.""",
                meaning=CL["0000760"]))
        setattr(cls, "CL:0000447",
            PermissibleValue(
                text="CL:0000447",
                meaning=CL["0000447"]))
        setattr(cls, "CL:0002263",
            PermissibleValue(
                text="CL:0002263",
                description="""One of three types of epithelial cells that populate the parathyroid gland; cytological characteristics intermediate between those of the chief cell and of the oxyphil cell. Because only one hormone is produced, the three cell forms are widely believed to be different phases in the life cycle of a single cell type, with the chief cell being its physiologically active stage.""",
                meaning=CL["0002263"]))
        setattr(cls, "CL:0002288",
            PermissibleValue(
                text="CL:0002288",
                description="A cell type that forms the boundary with the surrounding epithelium.",
                meaning=CL["0002288"]))
        setattr(cls, "CL:2000053",
            PermissibleValue(
                text="CL:2000053",
                description="Any endothelial cell that is part of a spleen.",
                meaning=CL["2000053"]))
        setattr(cls, "CL:0002671",
            PermissibleValue(
                text="CL:0002671",
                description="""An endothelial stalk cell is a specialized endothelial cell that follows behind the tip cell of an angiogenic sprout.""",
                meaning=CL["0002671"]))
        setattr(cls, "CL:0000912",
            PermissibleValue(
                text="CL:0000912",
                description="""A effector T cell that provides help in the form of secreted cytokines to other immune cells.""",
                meaning=CL["0000912"]))
        setattr(cls, "CL:0002187",
            PermissibleValue(
                text="CL:0002187",
                description="""A basally situated, mitotically active, columnar-shaped keratinocyte attached to the basement membrane.""",
                meaning=CL["0002187"]))
        setattr(cls, "CL:0000692",
            PermissibleValue(
                text="CL:0000692",
                description="""A neuroglial cell of the peripheral nervous system inside the basal lamina of the neuromuscular junction providing chemical and physical support to the synapse.""",
                meaning=CL["0000692"]))
        setattr(cls, "CL:0000193",
            PermissibleValue(
                text="CL:0000193",
                description="A striated muscle cell of an arthropod heart that participates in heart contraction.",
                meaning=CL["0000193"]))
        setattr(cls, "CL:0002301",
            PermissibleValue(
                text="CL:0002301",
                description="""A resident stromal cell located in the synovial membrane and responsible for the production of immune-related cytokines and chemokines. This cell type secretes glycoproteins and hyaluronic acid, has abundant granular endoplasmic reticulum, but contains fewer vacuoles and vesicles.""",
                meaning=CL["0002301"]))
        setattr(cls, "CL:0001014",
            PermissibleValue(
                text="CL:0001014",
                description="""CD1a-positive Langerhans cell is a Langerhans_cell that is CD1a-positive and CD324-positive.""",
                meaning=CL["0001014"]))
        setattr(cls, "CL:0002346",
            PermissibleValue(
                text="CL:0002346",
                description="An immature natural killer cell that is NK1.1-positive and DX-5 negative.",
                meaning=CL["0002346"]))
        setattr(cls, "CL:0000495",
            PermissibleValue(
                text="CL:0000495",
                description="A photoreceptor cell that is sensitive to blue light.",
                meaning=CL["0000495"]))
        setattr(cls, "CL:0011016",
            PermissibleValue(
                text="CL:0011016",
                description="""A motile sperm cell that contains a slender threadlike microscopic appendage that enables motion.""",
                meaning=CL["0011016"]))
        setattr(cls, "CL:0005004",
            PermissibleValue(
                text="CL:0005004",
                description="""A non-terminally differentiated cell that originates from the neural crest and differentiates into an erythrophore.""",
                meaning=CL["0005004"]))
        setattr(cls, "CL:4030024",
            PermissibleValue(
                text="CL:4030024",
                description="""An epithelial, transitional cell type between basal and secretory; located in stratified, non-ciliated structures (called hillocks) with high cell turnover in epithelium. In some mammalian species, this cell type has been noted to express KRT13 and is postulated to play a role in squamous barrier function and immunomodulation.""",
                meaning=CL["4030024"]))
        setattr(cls, "CL:0000769",
            PermissibleValue(
                text="CL:0000769",
                description="""A basophil precursor in the granulocytic series, being a cell intermediate in development between a basophilic myelocyte and a band form basophil. The nucleus becomes indented where the indentation is smaller than half the distance to the farthest nuclear margin; chromatin becomes coarse and clumped; specific granules predominate while primary granules are rare. Markers are CD11b-positive, CD15-positive, CD16-positive, CD24-positive, CD33-positive, and CD13-positive.""",
                meaning=CL["0000769"]))
        setattr(cls, "CL:4047053",
            PermissibleValue(
                text="CL:4047053",
                description="""A macrophage characterized by high expression of Triggering Receptor Expressed on Myeloid cells 2 (TREM2), found in various tissues including the liver, adipose tissue, bone, gut (Colonna, 2023), and tumor microenvironments, where it is associated with immunosuppressive and anti-inflammatory activity (Colmenares, 2024; Khantakova, 2022). This cell exhibits a distinct gene expression profile in the tumor microenvironment, including overexpression of complement system genes (C1QA, C1QB, C1QC, C3), and SPP1 in both mice and humans (Xiong, 2020; Khantakova, 2022). It is involved in phagocytosis, tissue repair, and modulation of immune responses (Coeho, 2021).""",
                meaning=CL["4047053"]))
        setattr(cls, "CL:2000028",
            PermissibleValue(
                text="CL:2000028",
                description="Any glutamatergic neuron that is part of a cerebellum.",
                meaning=CL["2000028"]))
        setattr(cls, "CL:0002389",
            PermissibleValue(
                text="CL:0002389",
                description="An arthroconidium that has only one nucleus.",
                meaning=CL["0002389"]))
        setattr(cls, "CL:0002260",
            PermissibleValue(
                text="CL:0002260",
                description="An epithelial cell of the parathyroid gland.",
                meaning=CL["0002260"]))
        setattr(cls, "CL:0000171",
            PermissibleValue(
                text="CL:0000171",
                description="""A type A enteroendocrine cell found in the periphery of the islets of Langerhans that secretes glucagon.""",
                meaning=CL["0000171"]))
        setattr(cls, "CL:0000323",
            PermissibleValue(
                text="CL:0000323",
                meaning=CL["0000323"]))
        setattr(cls, "CL:0008007",
            PermissibleValue(
                text="CL:0008007",
                description="A muscle cell that is part of some visceral muscle.",
                meaning=CL["0008007"]))
        setattr(cls, "CL:4033078",
            PermissibleValue(
                text="CL:4033078",
                description="A(n) mononuclear phagocyte that is cycling.",
                meaning=CL["4033078"]))
        setattr(cls, "CL:0002432",
            PermissibleValue(
                text="CL:0002432",
                description="""A CD4-positive, CD8-negative thymocyte that is CD24-positive and expresses high levels of the alpha-beta T cell receptor.""",
                meaning=CL["0002432"]))
        setattr(cls, "CL:0000979",
            PermissibleValue(
                text="CL:0000979",
                description="""An IgG memory B cell is a class switched memory B cell that is class switched and expresses IgG on the cell surface.""",
                meaning=CL["0000979"]))
        setattr(cls, "CL:0001024",
            PermissibleValue(
                text="CL:0001024",
                description="""CD133-positive hematopoietic stem cell is a hematopoietic stem cell that is CD34-positive, CD90-positive, and CD133-positive.""",
                meaning=CL["0001024"]))
        setattr(cls, "CL:0000899",
            PermissibleValue(
                text="CL:0000899",
                description="""CD4-positive, alpha-beta T cell with the phenotype RORgamma-t-positive, CXCR3-negative, CCR6-positive, and capable of producing IL-17.""",
                meaning=CL["0000899"]))
        setattr(cls, "CL:0000076",
            PermissibleValue(
                text="CL:0000076",
                meaning=CL["0000076"]))
        setattr(cls, "CL:0001078",
            PermissibleValue(
                text="CL:0001078",
                description="A group 3 innate lymphoid cell in the human with the phenotype IL-7Ralpha-positive.",
                meaning=CL["0001078"]))
        setattr(cls, "CL:0001060",
            PermissibleValue(
                text="CL:0001060",
                description="""A hematopoietic oligopotent progenitor cell that has the ability to differentiate into limited cell types but lacks lineage cell markers and self renewal capabilities. Cell lacks hematopoeitic lineage markers.""",
                meaning=CL["0001060"]))
        setattr(cls, "CL:0007002",
            PermissibleValue(
                text="CL:0007002",
                description="Skeletogenic cell that has the potential to develop into a cementoblast.",
                meaning=CL["0007002"]))
        setattr(cls, "CL:0008000",
            PermissibleValue(
                text="CL:0008000",
                description="Any muscle cell in which the fibers are not organised into sarcomeres.",
                meaning=CL["0008000"]))
        setattr(cls, "CL:0002621",
            PermissibleValue(
                text="CL:0002621",
                description="Any stratified squamous epithelial cell that is part of some gingival epithelium.",
                meaning=CL["0002621"]))
        setattr(cls, "CL:1001601",
            PermissibleValue(
                text="CL:1001601",
                description="""Hormone secreting cell located in the cortex of adrenal gland. Glandular cells in the adrenal cortex secrete mineralocorticoids, glucocorticoids and androgens.""",
                meaning=CL["1001601"]))
        setattr(cls, "CL:0002637",
            PermissibleValue(
                text="CL:0002637",
                description="""An epithelial cell of the anal canal that is keratinized. This cell type is found towards the lower, rectal end of the anal canal.""",
                meaning=CL["0002637"]))
        setattr(cls, "CL:2000039",
            PermissibleValue(
                text="CL:2000039",
                description="Any neuromast support cell that is part of a posterior lateral line.",
                meaning=CL["2000039"]))
        setattr(cls, "CL:1000306",
            PermissibleValue(
                text="CL:1000306",
                description="A fibroblast that is part of the tunica adventitia of artery.",
                meaning=CL["1000306"]))
        setattr(cls, "CL:0001203",
            PermissibleValue(
                text="CL:0001203",
                description="""A CD8-positive, alpha-beta T cell with memory phenotype indicated by being CD45RO and CD127-positive. This cell type is also described as being CD25-negative, CD44-high, and CD122-high.""",
                meaning=CL["0001203"]))
        setattr(cls, "CL:1000467",
            PermissibleValue(
                text="CL:1000467",
                description="A chromaffin cell that is part of the left ovary.",
                meaning=CL["1000467"]))
        setattr(cls, "CL:0000888",
            PermissibleValue(
                text="CL:0000888",
                description="""A lymph node macrophage found in the cortex of lymph nodes, in particular in and around the germinal centers, and that participates in phagocytosis of apoptotic B cells from the germinal centers.""",
                meaning=CL["0000888"]))
        setattr(cls, "CL:0000050",
            PermissibleValue(
                text="CL:0000050",
                description="A progenitor cell committed to the megakaryocyte and erythroid lineages.",
                meaning=CL["0000050"]))
        setattr(cls, "CL:0002191",
            PermissibleValue(
                text="CL:0002191",
                description="A cell involved in the formation of a granulocyte.",
                meaning=CL["0002191"]))
        setattr(cls, "CL:0010010",
            PermissibleValue(
                text="CL:0010010",
                description="""A GABAergic interneuron that is located in the molecular layer of the cerebellum. This cell receives excitatory inputs primarily from parallel fibers and plays a crucial role in feed-forward inhibition by suppressing the activity of Purkinje cells and modulating the output of the cerebellar cortex. The stellate cell is part of the local circuitry that contributes to the fine-tuning of motor coordination and a regulator of cerebellar blood flow via neurovascular coupling.""",
                meaning=CL["0010010"]))
        setattr(cls, "CL:0000436",
            PermissibleValue(
                text="CL:0000436",
                meaning=CL["0000436"]))
        setattr(cls, "CL:0011109",
            PermissibleValue(
                text="CL:0011109",
                description="A neuron that releases hypocretin as a neurotransmitter.",
                meaning=CL["0011109"]))
        setattr(cls, "CL:4047025",
            PermissibleValue(
                text="CL:4047025",
                description="Any type G enteroendocrine cell that is part of some epithelium of stomach.",
                meaning=CL["4047025"]))
        setattr(cls, "CL:0001068",
            PermissibleValue(
                text="CL:0001068",
                description="A group 1 innate lymphoid cell that is non-cytotoxic.",
                meaning=CL["0001068"]))
        setattr(cls, "CL:0002286",
            PermissibleValue(
                text="CL:0002286",
                description="""A taste receptor cell that has a short microvilli, a projecting apical region, a large rounded nucleus, and expresses taste chemoreceptors thus making them the transducing cell for taste qualities.""",
                meaning=CL["0002286"]))
        setattr(cls, "CL:0000132",
            PermissibleValue(
                text="CL:0000132",
                description="""An hexagonal, flattened, mitochondria-rich endothelial cell that forms a monolayer on the posterior surface of the cornea (the corneal endothelium). Corneal endothelial cells are derived from the neural crest and are responsible for keeping the cornea transparent by maintaining the tissue in a semi-dry state through the action of their ionic pumps and tight junction barrier.""",
                meaning=CL["0000132"]))
        setattr(cls, "CL:2000087",
            PermissibleValue(
                text="CL:2000087",
                description="Any basket cell that is part of a dentate gyrus of hippocampal formation.",
                meaning=CL["2000087"]))
        setattr(cls, "CL:2000097",
            PermissibleValue(
                text="CL:2000097",
                description="Any dopaminergic neuron that is part of a midbrain.",
                meaning=CL["2000097"]))
        setattr(cls, "CL:0003003",
            PermissibleValue(
                text="CL:0003003",
                description="""A mono-stratified retinal ganglion cell that has a small dendritic field and a sparse dendritic arbor with post sympatic terminals in sublaminar layer S3.""",
                meaning=CL["0003003"]))
        setattr(cls, "CL:0000492",
            PermissibleValue(
                text="CL:0000492",
                description="""A CD4-positive, alpha-beta T cell that cooperates with other lymphocytes via direct contact or cytokine release to initiate a variety of immune functions.""",
                meaning=CL["0000492"]))
        setattr(cls, "CL:1000452",
            PermissibleValue(
                text="CL:1000452",
                description="An epithelial cell that is part of the glomerular parietal epithelium.",
                meaning=CL["1000452"]))
        setattr(cls, "CL:0000510",
            PermissibleValue(
                text="CL:0000510",
                description="""An epithelial cell found in the basal part of the intestinal glands (crypts of Lieberkuhn) including the appendix. Paneth cells synthesize and secrete lysozyme and cryptdins. Numerous in the deeper parts of the intestinal crypts, particularly in the duodenum, rich in zinc, contain large acidophilic granules, with irregular apical microvilli and prominent membrane-bound vacuoles containing matrix.""",
                meaning=CL["0000510"]))
        setattr(cls, "CL:0002232",
            PermissibleValue(
                text="CL:0002232",
                description="An epithelial cell of prostatic duct.",
                meaning=CL["0002232"]))
        setattr(cls, "CL:4023115",
            PermissibleValue(
                text="CL:4023115",
                description="""A spiral ganglion neuron that innervates inner hair cells. Type 1 spiral ganglion neurons are myelinated and bipolar.""",
                meaning=CL["4023115"]))
        setattr(cls, "CL:0002041",
            PermissibleValue(
                text="CL:0002041",
                description="A CD24-low, CD44-positive, DX5-low, NK1.1-negative NK T cell.",
                meaning=CL["0002041"]))
        setattr(cls, "CL:4042015",
            PermissibleValue(
                text="CL:4042015",
                description="""A VIP GABAergic cortical interneuron expressing vasoactive intestinal polypeptide and choline acetyltransferase in the Mmus neocortex. This interneuron releases both γ-aminobutyric acid and acetylcholine.""",
                meaning=CL["4042015"]))
        setattr(cls, "CL:4047035",
            PermissibleValue(
                text="CL:4047035",
                description="""A specialized smooth muscle cell located in the outermost layer of the muscularis externa of the stomach wall. This cell is arranged longitudinally along the stomach's axis and is responsible for the contractions that facilitate food movement toward the pylorus.""",
                meaning=CL["4047035"]))
        setattr(cls, "CL:0000661",
            PermissibleValue(
                text="CL:0000661",
                meaning=CL["0000661"]))
        setattr(cls, "CL:2000064",
            PermissibleValue(
                text="CL:2000064",
                description="""A meso-epithelial cell of the ovarian surface epithelium, varying in shape from flat to cuboidal to pseudostratified columnar. This cell plays a crucial role in ovulation by producing proteolytic enzymes in response to gonadotropins, facilitating follicle rupture through tissue breakdown and TNF-alpha signaling. Additionally, this cell contributes to post-ovulatory wound repair (Morris et al., 2022) and exhibits stem cell-like properties (Flesken-Nikitin et al., 2013; Wang et al., 2019).""",
                meaning=CL["2000064"]))
        setattr(cls, "CL:0002573",
            PermissibleValue(
                text="CL:0002573",
                description="A glial cell that myelinates or ensheathes axons in the peripheral nervous system.",
                meaning=CL["0002573"]))
        setattr(cls, "CL:0000779",
            PermissibleValue(
                text="CL:0000779",
                description="""A specialized multinuclear osteoclast, forming a syncytium through the fusion of mononuclear precursor cells, associated with the absorption and removal of bone.""",
                meaning=CL["0000779"]))
        setattr(cls, "CL:1000277",
            PermissibleValue(
                text="CL:1000277",
                description="A smooth muscle cell that is part of the jejunum.",
                meaning=CL["1000277"]))
        setattr(cls, "CL:0000487",
            PermissibleValue(
                text="CL:0000487",
                description="""A secretory cell of ectodermal origin. This cell may have important functions in fatty acid and hydrocarbon metabolism and is metabolically linked to the fat body and tracheae. This cell is exclusive of arthropods.""",
                meaning=CL["0000487"]))
        setattr(cls, "CL:0000559",
            PermissibleValue(
                text="CL:0000559",
                description="""A precursor in the monocytic series, being a cell intermediate in development between the monoblast and monocyte. This cell is CD11b-positive and has fine azurophil granules.""",
                meaning=CL["0000559"]))
        setattr(cls, "CL:0000920",
            PermissibleValue(
                text="CL:0000920",
                description="""CD8-positive, alpha-beta positive regulatory T cell with the phenotype CD28-negative and FoxP3-positive.""",
                meaning=CL["0000920"]))
        setattr(cls, "CL:0000562",
            PermissibleValue(
                text="CL:0000562",
                description="An erythrocyte having a nucleus.",
                meaning=CL["0000562"]))
        setattr(cls, "CL:0003012",
            PermissibleValue(
                text="CL:0003012",
                description="""A mono-stratified retinal ganglion cell that has a large dendritic field and a medium dendritic arbor with post synaptic terminals in sublaminar layer S1 and S2.""",
                meaning=CL["0003012"]))
        setattr(cls, "CL:0008008",
            PermissibleValue(
                text="CL:0008008",
                description="""A visceral muscle cell that is striated.  Examples include the visceral muscle cells of arhtropods.""",
                meaning=CL["0008008"]))
        setattr(cls, "CL:0002480",
            PermissibleValue(
                text="CL:0002480",
                description="A goblet cell located in the nasal epithelium.",
                meaning=CL["0002480"]))
        setattr(cls, "CL:4030040",
            PermissibleValue(
                text="CL:4030040",
                description="""A multi-ciliated cell of the endometrial epithelium. This cell is characterized by the presence of 9+2 motile cilia on its apical surface, which facilitates the movement of mucus across the endometrial surface.""",
                meaning=CL["4030040"]))
        setattr(cls, "CL:4023023",
            PermissibleValue(
                text="CL:4023023",
                description="""A lamp 5 GABAergic cortical interneuron with neurogliaform morphology with a soma found in L5,6. L5,6 NGC lamp5 have deep afterhyperpolarization (AHP) but narrow action potentials (APs). Unlike other deep neurogliaform cells (which are caudal ganglionic eminence (CGE) derived), L5,6 NGC lamp5 cells are medial ganglionic eminence (MGE)-derived""",
                meaning=CL["4023023"]))
        setattr(cls, "CL:0011104",
            PermissibleValue(
                text="CL:0011104",
                description="""A type of interneuron in the retinal inner nuclear layer which carries information from the inner plexiform layer and the outer plexiform layer.""",
                meaning=CL["0011104"]))
        setattr(cls, "CL:0000918",
            PermissibleValue(
                text="CL:0000918",
                description="A CD8-positive, alpha-beta positive T cell expressing GATA-3 and secreting IL-4.",
                meaning=CL["0000918"]))
        setattr(cls, "CL:0000938",
            PermissibleValue(
                text="CL:0000938",
                description="""NK cell that has the phenotype CD56-bright, CD16-negative, and CD84-positive with the function to secrete interferon-gamma but is not cytotoxic.""",
                meaning=CL["0000938"]))
        setattr(cls, "CL:4023130",
            PermissibleValue(
                text="CL:4023130",
                description="""A neuron that expresses kisspeptin. These neurons are predominantly located in the hypothalamus, but also found in other parts of the brain including the hippocampal dentate gyrus.""",
                meaning=CL["4023130"]))
        setattr(cls, "CL:4030051",
            PermissibleValue(
                text="CL:4030051",
                description="""A DRD1-expressing medium spiny neuron that is part of a nucleus accumbens shell or olfactory tubercle.""",
                meaning=CL["4030051"]))
        setattr(cls, "CL:0002111",
            PermissibleValue(
                text="CL:0002111",
                description="""An CD38-negative unswitched memory B cell is an unswitched memory B cell that has the phenotype CD38-negative, IgD-positive, CD138-negative, and IgG-negative.""",
                meaning=CL["0002111"]))
        setattr(cls, "CL:1000349",
            PermissibleValue(
                text="CL:1000349",
                description="A basal cell found in the bronchus epithelium.",
                meaning=CL["1000349"]))
        setattr(cls, "CL:4033050",
            PermissibleValue(
                text="CL:4033050",
                description="A neuron that releases catecholamine as a neurotransmitter.",
                meaning=CL["4033050"]))
        setattr(cls, "CL:0000927",
            PermissibleValue(
                text="CL:0000927",
                description="""A mature NK T cell that predominantly secretes type 2 cytokines such as interleukin-4 and interleukin-13 and enhances type 2 immune responses.""",
                meaning=CL["0000927"]))
        setattr(cls, "CL:0011026",
            PermissibleValue(
                text="CL:0011026",
                description="""A precursor cell that has a tendency to differentiate into a specific type of cell. They are descendants of stem cells, only they are more constrained in their differentiation potential or capacity for self-renewal, and are often more limited in both senses.""",
                meaning=CL["0011026"]))
        setattr(cls, "CL:4042037",
            PermissibleValue(
                text="CL:4042037",
                description="""A interneuron of the striatum expressing gamma-aminobutyric acid and somatostatin. This interneuron has a fusiform soma with a diameter between 9 - 25 µm, it has a long axon up to the length of 1mm. This neuron type displays a low threshold Ca2+ spike (LTS), a high input resistance, and the expression of long-lasting plateau potentials following depolarization from rest.""",
                meaning=CL["4042037"]))
        setattr(cls, "CL:0002529",
            PermissibleValue(
                text="CL:0002529",
                description="A dermal dendritic cell that is CD1a-positive and CD14-negative.",
                meaning=CL["0002529"]))
        setattr(cls, "CL:0000623",
            PermissibleValue(
                text="CL:0000623",
                description="""A lymphocyte that can spontaneously kill a variety of target cells without prior antigenic activation via germline encoded activation receptors and also regulate immune responses via cytokine release and direct contact with other cells.""",
                meaning=CL["0000623"]))
        setattr(cls, "CL:0000791",
            PermissibleValue(
                text="CL:0000791",
                description="A alpha-beta T cell that has a mature phenotype.",
                meaning=CL["0000791"]))
        setattr(cls, "CL:1000073",
            PermissibleValue(
                text="CL:1000073",
                description="Any radial glial cell that is part of some spinal cord.",
                meaning=CL["1000073"]))
        setattr(cls, "CL:0000317",
            PermissibleValue(
                text="CL:0000317",
                description="""An epithelial cell that is part of a sebaceous gland. This cell produces and secretes sebum, an oily, lipid-rich substance, through holocrine secretion where the entire cell ruptures to release its contents.""",
                meaning=CL["0000317"]))
        setattr(cls, "CL:0000953",
            PermissibleValue(
                text="CL:0000953",
                description="""A pre-BCR-negative large pre-B-II cell is a large pre-B-II cell that is pre-B cell receptor-negative, composed of surrogate light chain protein (SL), which is composed of VpreB and Lambda 5/14.1, in complex with immunoglobulin mu heavy chain (IgHmu), on the cell surface, and lack a DNA rearrangement of immunoglobulin light chain genes.""",
                meaning=CL["0000953"]))
        setattr(cls, "CL:1000548",
            PermissibleValue(
                text="CL:1000548",
                description="An epithelial cell that is part of an outer medullary collecting duct.",
                meaning=CL["1000548"]))
        setattr(cls, "CL:1000483",
            PermissibleValue(
                text="CL:1000483",
                description="A Purkinje myocyte that is part of the internodal tract.",
                meaning=CL["1000483"]))
        setattr(cls, "CL:0001070",
            PermissibleValue(
                text="CL:0001070",
                description="""An adipocyte that is beige in color, thermogenic, and which differentiates in white fat tissue from a Myf5-negative progenitor.""",
                meaning=CL["0001070"]))
        setattr(cls, "CL:0003051",
            PermissibleValue(
                text="CL:0003051",
                description="A cone cell that detects ultraviolet (UV) wavelength light.",
                meaning=CL["0003051"]))
        setattr(cls, "CL:0011005",
            PermissibleValue(
                text="CL:0011005",
                description="""An interneuron that uses GABA as a vesicular neurotransmitter.  These interneurons are inhibitory""",
                meaning=CL["0011005"]))
        setattr(cls, "CL:0002055",
            PermissibleValue(
                text="CL:0002055",
                description="An immature B cell that is CD38-negative, CD10-low, CD21-low, and CD22-high.",
                meaning=CL["0002055"]))
        setattr(cls, "CL:1000715",
            PermissibleValue(
                text="CL:1000715",
                description="Any renal intercalated cell that is part of some cortical collecting duct.",
                meaning=CL["1000715"]))
        setattr(cls, "CL:0002324",
            PermissibleValue(
                text="CL:0002324",
                description="""A myoepithelial cell that is part of a mammary gland and is located in the basal layer. During lactation, a basal-myoepithelial cell of mammary gland contracts under the stimulation of oxytocin. In humans, a basal-myoepithelial cell of mammary gland can be identified by high levels of CD49f and low levels of EpCAM.""",
                meaning=CL["0002324"]))
        setattr(cls, "CL:0002378",
            PermissibleValue(
                text="CL:0002378",
                description="""A double negative thymocyte that has a T cell receptor consisting of a gamma chain containing a Vgamma2 segment, and a delta chain. This cell type is CD4-negative, CD8-negative and CD24-positive and is found in the fetal thymus.""",
                meaning=CL["0002378"]))
        setattr(cls, "CL:1000384",
            PermissibleValue(
                text="CL:1000384",
                description="""A type II vestibular sensory cell that is part of the epithelium of macula of saccule of membranous labyrinth.""",
                meaning=CL["1000384"]))
        setattr(cls, "CL:3000003",
            PermissibleValue(
                text="CL:3000003",
                description="A type of autonomic neuron that releases acetylcholine.",
                meaning=CL["3000003"]))
        setattr(cls, "CL:4042004",
            PermissibleValue(
                text="CL:4042004",
                description="""A choroid plexus macrophage that is part of the apical surface of some choroid plexus epithelium. This macrophage has a star-like shaped body.""",
                meaning=CL["4042004"]))
        setattr(cls, "CL:0003023",
            PermissibleValue(
                text="CL:0003023",
                description="A retinal ganglion cell C outer that has dense dendritic diversity.",
                meaning=CL["0003023"]))
        setattr(cls, "CL:0002396",
            PermissibleValue(
                text="CL:0002396",
                description="A patrolling monocyte that is CD14-low and CD16-positive.",
                meaning=CL["0002396"]))
        setattr(cls, "CL:1000697",
            PermissibleValue(
                text="CL:1000697",
                meaning=CL["1000697"]))
        setattr(cls, "CL:0000306",
            PermissibleValue(
                text="CL:0000306",
                meaning=CL["0000306"]))
        setattr(cls, "CL:0002264",
            PermissibleValue(
                text="CL:0002264",
                description="A type of enteroendocrine cell found in the stomach that secretes glucagon.",
                meaning=CL["0002264"]))
        setattr(cls, "CL:4023040",
            PermissibleValue(
                text="CL:4023040",
                description="""An intratelencephalic-projecting glutamatergic neuron with a soma found in cortical layers L2/3-6.""",
                meaning=CL["4023040"]))

# Slots
class slots:
    pass

slots.cell_set_accession = Slot(uri=CELL_ANNOTATION_SCHEMA.cell_set_accession, name="cell_set_accession", curie=CELL_ANNOTATION_SCHEMA.curie('cell_set_accession'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_set_accession, domain=None, range=str)

slots.parent_cell_set_accession = Slot(uri=RO['0015003'], name="parent_cell_set_accession", curie=RO.curie('0015003'),
                   model_uri=CELL_ANNOTATION_SCHEMA.parent_cell_set_accession, domain=None, range=Optional[str])

slots.transferred_annotations = Slot(uri=CELL_ANNOTATION_SCHEMA.transferred_annotations, name="transferred_annotations", curie=CELL_ANNOTATION_SCHEMA.curie('transferred_annotations'),
                   model_uri=CELL_ANNOTATION_SCHEMA.transferred_annotations, domain=None, range=Optional[Union[Union[dict, AnnotationTransfer], List[Union[dict, AnnotationTransfer]]]])

slots.cells = Slot(uri=CELL_ANNOTATION_SCHEMA.cells, name="cells", curie=CELL_ANNOTATION_SCHEMA.curie('cells'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cells, domain=None, range=Optional[Union[Union[dict, Cell], List[Union[dict, Cell]]]])

slots.negative_marker_gene_evidence = Slot(uri=CELL_ANNOTATION_SCHEMA.negative_marker_gene_evidence, name="negative_marker_gene_evidence", curie=CELL_ANNOTATION_SCHEMA.curie('negative_marker_gene_evidence'),
                   model_uri=CELL_ANNOTATION_SCHEMA.negative_marker_gene_evidence, domain=None, range=Optional[Union[str, List[str]]])

slots.rank = Slot(uri=CELL_ANNOTATION_SCHEMA.rank, name="rank", curie=CELL_ANNOTATION_SCHEMA.curie('rank'),
                   model_uri=CELL_ANNOTATION_SCHEMA.rank, domain=None, range=Optional[int])

slots.transferred_cell_label = Slot(uri=CELL_ANNOTATION_SCHEMA.transferred_cell_label, name="transferred_cell_label", curie=CELL_ANNOTATION_SCHEMA.curie('transferred_cell_label'),
                   model_uri=CELL_ANNOTATION_SCHEMA.transferred_cell_label, domain=None, range=Optional[str])

slots.source_taxonomy = Slot(uri=CELL_ANNOTATION_SCHEMA.source_taxonomy, name="source_taxonomy", curie=CELL_ANNOTATION_SCHEMA.curie('source_taxonomy'),
                   model_uri=CELL_ANNOTATION_SCHEMA.source_taxonomy, domain=None, range=Optional[Union[str, URIorCURIE]])

slots.source_node_accession = Slot(uri=CELL_ANNOTATION_SCHEMA.source_node_accession, name="source_node_accession", curie=CELL_ANNOTATION_SCHEMA.curie('source_node_accession'),
                   model_uri=CELL_ANNOTATION_SCHEMA.source_node_accession, domain=None, range=Optional[str])

slots.algorithm_name = Slot(uri=CELL_ANNOTATION_SCHEMA.algorithm_name, name="algorithm_name", curie=CELL_ANNOTATION_SCHEMA.curie('algorithm_name'),
                   model_uri=CELL_ANNOTATION_SCHEMA.algorithm_name, domain=None, range=Optional[str])

slots.comment = Slot(uri=IAO['0000115'], name="comment", curie=IAO.curie('0000115'),
                   model_uri=CELL_ANNOTATION_SCHEMA.comment, domain=None, range=Optional[str])

slots.cell_id = Slot(uri=CELL_ANNOTATION_SCHEMA.cell_id, name="cell_id", curie=CELL_ANNOTATION_SCHEMA.curie('cell_id'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_id, domain=None, range=str)

slots.confidence = Slot(uri=CELL_ANNOTATION_SCHEMA.confidence, name="confidence", curie=CELL_ANNOTATION_SCHEMA.curie('confidence'),
                   model_uri=CELL_ANNOTATION_SCHEMA.confidence, domain=None, range=Optional[float])

slots.author_categories = Slot(uri=CELL_ANNOTATION_SCHEMA.author_categories, name="author_categories", curie=CELL_ANNOTATION_SCHEMA.curie('author_categories'),
                   model_uri=CELL_ANNOTATION_SCHEMA.author_categories, domain=None, range=Optional[str])

slots.neurotransmitter_accession = Slot(uri=CELL_ANNOTATION_SCHEMA.neurotransmitter_accession, name="neurotransmitter_accession", curie=CELL_ANNOTATION_SCHEMA.curie('neurotransmitter_accession'),
                   model_uri=CELL_ANNOTATION_SCHEMA.neurotransmitter_accession, domain=None, range=Optional[str])

slots.neurotransmitter_rationale = Slot(uri=CELL_ANNOTATION_SCHEMA.neurotransmitter_rationale, name="neurotransmitter_rationale", curie=CELL_ANNOTATION_SCHEMA.curie('neurotransmitter_rationale'),
                   model_uri=CELL_ANNOTATION_SCHEMA.neurotransmitter_rationale, domain=None, range=Optional[str])

slots.neurotransmitter_marker_gene_evidence = Slot(uri=CELL_ANNOTATION_SCHEMA.neurotransmitter_marker_gene_evidence, name="neurotransmitter_marker_gene_evidence", curie=CELL_ANNOTATION_SCHEMA.curie('neurotransmitter_marker_gene_evidence'),
                   model_uri=CELL_ANNOTATION_SCHEMA.neurotransmitter_marker_gene_evidence, domain=None, range=Optional[Union[str, List[str]]])

slots.datestamp = Slot(uri=CELL_ANNOTATION_SCHEMA.datestamp, name="datestamp", curie=CELL_ANNOTATION_SCHEMA.curie('datestamp'),
                   model_uri=CELL_ANNOTATION_SCHEMA.datestamp, domain=None, range=str)

slots.reviewer = Slot(uri=CELL_ANNOTATION_SCHEMA.reviewer, name="reviewer", curie=CELL_ANNOTATION_SCHEMA.curie('reviewer'),
                   model_uri=CELL_ANNOTATION_SCHEMA.reviewer, domain=None, range=Optional[str])

slots.review = Slot(uri=CELL_ANNOTATION_SCHEMA.review, name="review", curie=CELL_ANNOTATION_SCHEMA.curie('review'),
                   model_uri=CELL_ANNOTATION_SCHEMA.review, domain=None, range=Optional[Union[str, "ReviewOptions"]])

slots.explanation = Slot(uri=IAO['0000115'], name="explanation", curie=IAO.curie('0000115'),
                   model_uri=CELL_ANNOTATION_SCHEMA.explanation, domain=None, range=Optional[str])

slots.name = Slot(uri=RDFS.label, name="name", curie=RDFS.curie('label'),
                   model_uri=CELL_ANNOTATION_SCHEMA.name, domain=None, range=str)

slots.description = Slot(uri=IAO['0000115'], name="description", curie=IAO.curie('0000115'),
                   model_uri=CELL_ANNOTATION_SCHEMA.description, domain=None, range=Optional[str])

slots.annotation_method = Slot(uri=CELL_ANNOTATION_SCHEMA.annotation_method, name="annotation_method", curie=CELL_ANNOTATION_SCHEMA.curie('annotation_method'),
                   model_uri=CELL_ANNOTATION_SCHEMA.annotation_method, domain=None, range=Optional[Union[str, "AnnotationMethodOptions"]])

slots.automated_annotation = Slot(uri=CELL_ANNOTATION_SCHEMA.automated_annotation, name="automated_annotation", curie=CELL_ANNOTATION_SCHEMA.curie('automated_annotation'),
                   model_uri=CELL_ANNOTATION_SCHEMA.automated_annotation, domain=None, range=Optional[Union[dict, AutomatedAnnotation]])

slots.algorithm_version = Slot(uri=CELL_ANNOTATION_SCHEMA.algorithm_version, name="algorithm_version", curie=CELL_ANNOTATION_SCHEMA.curie('algorithm_version'),
                   model_uri=CELL_ANNOTATION_SCHEMA.algorithm_version, domain=None, range=str)

slots.algorithm_repo_url = Slot(uri=CELL_ANNOTATION_SCHEMA.algorithm_repo_url, name="algorithm_repo_url", curie=CELL_ANNOTATION_SCHEMA.curie('algorithm_repo_url'),
                   model_uri=CELL_ANNOTATION_SCHEMA.algorithm_repo_url, domain=None, range=str)

slots.reference_location = Slot(uri=CELL_ANNOTATION_SCHEMA.reference_location, name="reference_location", curie=CELL_ANNOTATION_SCHEMA.curie('reference_location'),
                   model_uri=CELL_ANNOTATION_SCHEMA.reference_location, domain=None, range=Optional[str])

slots.labelset = Slot(uri=CAS.has_labelset, name="labelset", curie=CAS.curie('has_labelset'),
                   model_uri=CELL_ANNOTATION_SCHEMA.labelset, domain=None, range=str)

slots.cell_label = Slot(uri=RDFS.label, name="cell_label", curie=RDFS.curie('label'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_label, domain=None, range=str)

slots.cell_fullname = Slot(uri=SKOS.preflabel, name="cell_fullname", curie=SKOS.curie('preflabel'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_fullname, domain=None, range=Optional[str])

slots.cell_ontology_term_id = Slot(uri=RO['0002473'], name="cell_ontology_term_id", curie=RO.curie('0002473'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_ontology_term_id, domain=None, range=Optional[Union[str, "CellTypeEnum"]])

slots.cell_ontology_term = Slot(uri=CELL_ANNOTATION_SCHEMA.cell_ontology_term, name="cell_ontology_term", curie=CELL_ANNOTATION_SCHEMA.curie('cell_ontology_term'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_ontology_term, domain=None, range=Optional[str])

slots.cell_ids = Slot(uri=CAS.has_cellid, name="cell_ids", curie=CAS.curie('has_cellid'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cell_ids, domain=None, range=Optional[Union[str, List[str]]])

slots.rationale = Slot(uri=CELL_ANNOTATION_SCHEMA.rationale, name="rationale", curie=CELL_ANNOTATION_SCHEMA.curie('rationale'),
                   model_uri=CELL_ANNOTATION_SCHEMA.rationale, domain=None, range=Optional[str])

slots.rationale_dois = Slot(uri=CELL_ANNOTATION_SCHEMA.rationale_dois, name="rationale_dois", curie=CELL_ANNOTATION_SCHEMA.curie('rationale_dois'),
                   model_uri=CELL_ANNOTATION_SCHEMA.rationale_dois, domain=None, range=Optional[Union[str, List[str]]])

slots.marker_gene_evidence = Slot(uri=CELL_ANNOTATION_SCHEMA.marker_gene_evidence, name="marker_gene_evidence", curie=CELL_ANNOTATION_SCHEMA.curie('marker_gene_evidence'),
                   model_uri=CELL_ANNOTATION_SCHEMA.marker_gene_evidence, domain=None, range=Optional[Union[str, List[str]]])

slots.marker_gene_context = Slot(uri=CELL_ANNOTATION_SCHEMA.marker_gene_context, name="marker_gene_context", curie=CELL_ANNOTATION_SCHEMA.curie('marker_gene_context'),
                   model_uri=CELL_ANNOTATION_SCHEMA.marker_gene_context, domain=None, range=Optional[Union[str, List[str]]])

slots.synonyms = Slot(uri=CELL_ANNOTATION_SCHEMA.synonyms, name="synonyms", curie=CELL_ANNOTATION_SCHEMA.curie('synonyms'),
                   model_uri=CELL_ANNOTATION_SCHEMA.synonyms, domain=None, range=Optional[Union[str, List[str]]])

slots.reviews = Slot(uri=CELL_ANNOTATION_SCHEMA.reviews, name="reviews", curie=CELL_ANNOTATION_SCHEMA.curie('reviews'),
                   model_uri=CELL_ANNOTATION_SCHEMA.reviews, domain=None, range=Optional[Union[Union[dict, Review], List[Union[dict, Review]]]])

slots.author_annotation_fields = Slot(uri=CELL_ANNOTATION_SCHEMA.author_annotation_fields, name="author_annotation_fields", curie=CELL_ANNOTATION_SCHEMA.curie('author_annotation_fields'),
                   model_uri=CELL_ANNOTATION_SCHEMA.author_annotation_fields, domain=None, range=Optional[Union[dict, Any]])

slots.matrix_file_id = Slot(uri=CELL_ANNOTATION_SCHEMA.matrix_file_id, name="matrix_file_id", curie=CELL_ANNOTATION_SCHEMA.curie('matrix_file_id'),
                   model_uri=CELL_ANNOTATION_SCHEMA.matrix_file_id, domain=None, range=Optional[Union[str, URIorCURIE]])

slots.title = Slot(uri=CELL_ANNOTATION_SCHEMA.title, name="title", curie=CELL_ANNOTATION_SCHEMA.curie('title'),
                   model_uri=CELL_ANNOTATION_SCHEMA.title, domain=None, range=str)

slots.cellannotation_schema_version = Slot(uri=CELL_ANNOTATION_SCHEMA.cellannotation_schema_version, name="cellannotation_schema_version", curie=CELL_ANNOTATION_SCHEMA.curie('cellannotation_schema_version'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cellannotation_schema_version, domain=None, range=Optional[str])

slots.cellannotation_timestamp = Slot(uri=CELL_ANNOTATION_SCHEMA.cellannotation_timestamp, name="cellannotation_timestamp", curie=CELL_ANNOTATION_SCHEMA.curie('cellannotation_timestamp'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cellannotation_timestamp, domain=None, range=Optional[str])

slots.cellannotation_version = Slot(uri=CELL_ANNOTATION_SCHEMA.cellannotation_version, name="cellannotation_version", curie=CELL_ANNOTATION_SCHEMA.curie('cellannotation_version'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cellannotation_version, domain=None, range=Optional[str])

slots.cellannotation_url = Slot(uri=CELL_ANNOTATION_SCHEMA.cellannotation_url, name="cellannotation_url", curie=CELL_ANNOTATION_SCHEMA.curie('cellannotation_url'),
                   model_uri=CELL_ANNOTATION_SCHEMA.cellannotation_url, domain=None, range=Optional[str])

slots.author_list = Slot(uri=CELL_ANNOTATION_SCHEMA.author_list, name="author_list", curie=CELL_ANNOTATION_SCHEMA.curie('author_list'),
                   model_uri=CELL_ANNOTATION_SCHEMA.author_list, domain=None, range=Optional[str])

slots.author_name = Slot(uri=CELL_ANNOTATION_SCHEMA.author_name, name="author_name", curie=CELL_ANNOTATION_SCHEMA.curie('author_name'),
                   model_uri=CELL_ANNOTATION_SCHEMA.author_name, domain=None, range=str)

slots.author_contact = Slot(uri=CELL_ANNOTATION_SCHEMA.author_contact, name="author_contact", curie=CELL_ANNOTATION_SCHEMA.curie('author_contact'),
                   model_uri=CELL_ANNOTATION_SCHEMA.author_contact, domain=None, range=Optional[str])

slots.orcid = Slot(uri=CELL_ANNOTATION_SCHEMA.orcid, name="orcid", curie=CELL_ANNOTATION_SCHEMA.curie('orcid'),
                   model_uri=CELL_ANNOTATION_SCHEMA.orcid, domain=None, range=Optional[str])

slots.labelsets = Slot(uri=CELL_ANNOTATION_SCHEMA.labelsets, name="labelsets", curie=CELL_ANNOTATION_SCHEMA.curie('labelsets'),
                   model_uri=CELL_ANNOTATION_SCHEMA.labelsets, domain=None, range=Union[Union[dict, Labelset], List[Union[dict, Labelset]]])

slots.annotations = Slot(uri=CELL_ANNOTATION_SCHEMA.annotations, name="annotations", curie=CELL_ANNOTATION_SCHEMA.curie('annotations'),
                   model_uri=CELL_ANNOTATION_SCHEMA.annotations, domain=None, range=Union[Union[dict, Annotation], List[Union[dict, Annotation]]])

slots.id = Slot(uri=CELL_ANNOTATION_SCHEMA.id, name="id", curie=CELL_ANNOTATION_SCHEMA.curie('id'),
                   model_uri=CELL_ANNOTATION_SCHEMA.id, domain=None, range=URIRef)

slots.Bican_Taxonomy_labelsets = Slot(uri=CELL_ANNOTATION_SCHEMA.labelsets, name="Bican_Taxonomy_labelsets", curie=CELL_ANNOTATION_SCHEMA.curie('labelsets'),
                   model_uri=CELL_ANNOTATION_SCHEMA.Bican_Taxonomy_labelsets, domain=BicanTaxonomy, range=Union[Union[dict, BicanLabelset], List[Union[dict, BicanLabelset]]])

slots.Bican_Taxonomy_annotations = Slot(uri=CELL_ANNOTATION_SCHEMA.annotations, name="Bican_Taxonomy_annotations", curie=CELL_ANNOTATION_SCHEMA.curie('annotations'),
                   model_uri=CELL_ANNOTATION_SCHEMA.Bican_Taxonomy_annotations, domain=BicanTaxonomy, range=Union[Union[dict, BicanAnnotation], List[Union[dict, BicanAnnotation]]])