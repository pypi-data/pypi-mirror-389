-- # Class: "Cap_Taxonomy" Description: ""
--     * Slot: id Description: 
--     * Slot: cap_publication_title Description: The title of the publication on CAP (i.e. a published collection of datasets, the \"CAP Workspace\".). The title of the publication on CAP. (NOTE: the term \"publication\" refers to the workspace published on CAP with a version and timestamp.) This MUST be less than or equal to N characters, and this MUST be encoded as a single string.
--     * Slot: cap_publication_description Description: The description of the publication on CAP. The description of the publication on CAP. (NOTE: the term \"publication\" refers to the workspace published on CAP with a version and timestamp.) This MUST be less than or equal to N characters, and this MUST be encoded as a single string.
--     * Slot: cap_publication_url Description: A persistent URL of the publication on CAP. (NOTE: the term \"publication\" refers to the workspace published on CAP with a version and timestamp.)
--     * Slot: cap_dataset_url Description: A persistent URL of the dataset on CAP.
--     * Slot: publication_timestamp Description: The timestamp of the CAP publication. This MUST be a string in the format %yyyy-%MM-%dd'T'%hh:%mm:%ss. This value will be overwritten by the newest timestamp upon a new publication.
--     * Slot: publication_version Description: The (latest) version of the CAP publication. This value will be overwritten by the newest version upon a new publication (and automatically incremented). This versioning MUST follow the format 'v' + '[integer]', whereby newer versions must be naturally incremented.
--     * Slot: matrix_file_id Description: A resolvable ID for a cell by gene matrix file in the form namespace:accession, e.g. CellXGene_dataset:8e10f1c4-8e98-41e5-b65f-8cd89a887122.  Please see https://github.com/cellannotation/cell-annotation-schema/registry/registry.json for supported namespaces.
--     * Slot: title Description: The title of the dataset. This MUST be less than or equal to 200 characters. e.g. 'Human retina cell atlas - retinal ganglion cells'.
--     * Slot: description Description: The description of the dataset. e.g. 'A total of 15 retinal ganglion cell clusters were identified from over 99K retinal ganglion cell nuclei in the current atlas. Utilizing previous characterized markers from macaque, 5 clusters can be annotated.'
--     * Slot: cellannotation_schema_version Description: The schema version, the cell annotation open standard. Current version MUST follow 0.1.0This versioning MUST follow the format `'[MAJOR].[MINOR].[PATCH]'` as defined by Semantic Versioning 2.0.0, https://semver.org/
--     * Slot: cellannotation_timestamp Description: The timestamp of all cell annotations published (per dataset). This MUST be a string in the format `'%yyyy-%mm-%dd %hh:%mm:%ss'`
--     * Slot: cellannotation_version Description: The version for all cell annotations published (per dataset). This MUST be a string. The recommended versioning format is `'[MAJOR].[MINOR].[PATCH]'` as defined by Semantic Versioning 2.0.0, https://semver.org/
--     * Slot: cellannotation_url Description: A persistent URL of all cell annotations published (per dataset).
--     * Slot: author_list Description: This field stores a list of users who are included in the project as collaborators, regardless of their specific role. An example list; '['John Smith', 'Cody Miller', 'Sarah Jones']'
--     * Slot: author_name Description: Primary author's name. This MUST be a string in the format `[FIRST NAME] [LAST NAME]`
--     * Slot: author_contact Description: Primary author's contact. This MUST be a valid email address of the author
--     * Slot: orcid Description: Primary author's orcid. This MUST be a valid ORCID for the author
-- # Class: "Cap_Annotation" Description: ""
--     * Slot: id Description: 
--     * Slot: cell_ontology_exists Description: Decision by user whether this biological entity exists in the current Cell Ontology or not (at the given time of publication).
--     * Slot: category_fullname Description: Any term denoting a biological entity which the author associates as the nearest \"class\" or \"broader term\" (or \"parent term\") for the value/term in the field.
--     * Slot: category_cell_ontology_exists Description: Decision by user whether this biological entity exists in the current Cell Ontology or not (at the given time of publication).
--     * Slot: category_cell_ontology_term_id Description: The ID from either the Cell Ontology or from some ontology that extends it by classifying cell types under terms from the Cell Ontology.
--     * Slot: category_cell_ontology_term Description: The human-readable name assigned to the value of 'category_cell_ontology_term_id'.
--     * Slot: cell_ontology_assessment Description: Free-text field for researchers to express disagreements with any aspect of the Cell Ontology for this cell annotation.
--     * Slot: labelset Description: The unique name of the set of cell annotations. Each cell within the AnnData/Seurat file MUST be associated with a 'cell_label' value in order for this to be a valid 'cellannotation_setname'.
--     * Slot: cell_label Description: This denotes any free-text term which the author uses to annotate cells, i.e. the preferred cell label name used by the author. Abbreviations are exceptable in this field; refer to 'cell_fullname' for related details. Certain key words have been reserved:- `'doublets'` is reserved for encoding cells defined as doublets based on some computational analysis- `'junk'` is reserved for encoding cells that failed sequencing for some reason, e.g. few genes detected, high fraction of mitochondrial reads- `'unknown'` is explicitly reserved for unknown or 'author does not know'- `'NA'` is incomplete, i.e. no cell annotation was provided
--     * Slot: cell_fullname Description: This MUST be the full-length name for the biological entity listed in `cell_label` by the author. (If the value in `cell_label` is the full-length term, this field will contain the same value.) NOTE: any reserved word used in the field 'cell_label' MUST match the value of this field. EXAMPLE 1: Given the matching terms 'LC' and 'luminal cell' used to annotate the same cell(s), then users could use either terms as values in the field 'cell_label'. However, the abbreviation 'LC' CANNOT be provided in the field 'cell_fullname'. EXAMPLE 2: Either the abbreviation 'AC' or the full-length term intended by the author 'GABAergic amacrine cell' MAY be placed in the field 'cell_label', but as full-length term naming this biological entity, 'GABAergic amacrine cell' MUST be placed in the field 'cell_fullname'.
--     * Slot: cell_ontology_term_id Description: This MUST be a term from either the Cell Ontology (https://www.ebi.ac.uk/ols/ontologies/cl) or from some ontology that extends it by classifying cell types under terms from the Cell Ontologye.g. the Provisional Cell Ontology (https://www.ebi.ac.uk/ols/ontologies/pcl) or the Drosophila Anatomy Ontology (DAO) (https://www.ebi.ac.uk/ols4/ontologies/fbbt).NOTE: The closest available ontology term matching the value within the field 'cell_label' (at the time of publication) MUST be used.For example, if the value of 'cell_label' is 'relay interneuron', but this entity does not yet exist in the ontology, users must choose the closest available term in the CL ontology. In this case, it's the broader term 'interneuron' i.e.  https://www.ebi.ac.uk/ols/ontologies/cl/terms?obo_id=CL:0000099.
--     * Slot: cell_ontology_term Description: This MUST be the human-readable name assigned to the value of 'cell_ontology_term_id'
--     * Slot: rationale Description: The free-text rationale which users provide as justification/evidence for their cell annotations. Researchers are encouraged to use this field to cite relevant publications in-line using standard academic citations of the form `(Zheng et al., 2020)` This human-readable free-text MUST be encoded as a single string.All references cited SHOULD be listed using DOIs under rationale_dois. There MUST be a 2000-character limit.
--     * Slot: Cap_Taxonomy_id Description: Autocreated FK slot
--     * Slot: author_annotation_fields_id Description: A dictionary of author defined key value pairs annotating the cell set. The names and aims of these fields MUST not clash with official annotation fields.
-- # Class: "Any" Description: ""
--     * Slot: id Description: 
-- # Class: "Review" Description: ""
--     * Slot: id Description: 
--     * Slot: datestamp Description: Time and date review was last edited.
--     * Slot: reviewer Description: Review Author
--     * Slot: review Description: Reviewer's verdict on the annotation.  Must be 'Agree' or 'Disagree'
--     * Slot: explanation Description: Free-text review of annotation. This is required if the verdict is disagree and should include reasons for disagreement.
-- # Class: "Labelset" Description: ""
--     * Slot: id Description: 
--     * Slot: name Description: name of annotation key
--     * Slot: description Description: The description of the dataset. e.g. 'A total of 15 retinal ganglion cell clusters were identified from over 99K retinal ganglion cell nuclei in the current atlas. Utilizing previous characterized markers from macaque, 5 clusters can be annotated.'
--     * Slot: annotation_method Description: The method used for creating the cell annotations. This MUST be one of the following strings: `'algorithmic'`, `'manual'`, or `'both'`
--     * Slot: Cap_Taxonomy_id Description: Autocreated FK slot
--     * Slot: Taxonomy_id Description: Autocreated FK slot
--     * Slot: automated_annotation_id Description: 
-- # Class: "AutomatedAnnotation" Description: "A set of fields for recording the details of the automated annotation algorithm used. (Common 'automated annotation methods' would include PopV, Azimuth, CellTypist, scArches, etc.)"
--     * Slot: id Description: 
--     * Slot: algorithm_name Description: The name of the algorithm used. It MUST be a string of the algorithm's name.
--     * Slot: algorithm_version Description: The version of the algorithm used (if applicable). It MUST be a string of the algorithm's version, which is typically in the format '[MAJOR].[MINOR]', but other versioning systems are permitted (based on the algorithm's versioning).
--     * Slot: algorithm_repo_url Description: This field denotes the URL of the version control repository associated with the algorithm used (if applicable). It MUST be a string of a valid URL.
--     * Slot: reference_location Description: This field denotes a valid URL of the annotated dataset that was the source of annotated reference data. This MUST be a string of a valid URL. The concept of a 'reference' specifically refers to 'annotation transfer' algorithms, whereby a 'reference' dataset is used to transfer cell annotations to the 'query' dataset.
-- # Class: "Annotation" Description: "A collection of fields recording a cell type/class/state annotation on some set of cells, supporting evidence and provenance. As this is intended as a general schema, compulsory fields are kept to a minimum. However, tools using this schema are encouarged to specify a larger set of compulsory fields for publication.    Note: This schema deliberately allows for additional fields in order to support ad hoc user fields, new formal schema extensions and project/tool specific metadata."
--     * Slot: id Description: 
--     * Slot: labelset Description: The unique name of the set of cell annotations. Each cell within the AnnData/Seurat file MUST be associated with a 'cell_label' value in order for this to be a valid 'cellannotation_setname'.
--     * Slot: cell_label Description: This denotes any free-text term which the author uses to annotate cells, i.e. the preferred cell label name used by the author. Abbreviations are exceptable in this field; refer to 'cell_fullname' for related details. Certain key words have been reserved:- `'doublets'` is reserved for encoding cells defined as doublets based on some computational analysis- `'junk'` is reserved for encoding cells that failed sequencing for some reason, e.g. few genes detected, high fraction of mitochondrial reads- `'unknown'` is explicitly reserved for unknown or 'author does not know'- `'NA'` is incomplete, i.e. no cell annotation was provided
--     * Slot: cell_fullname Description: This MUST be the full-length name for the biological entity listed in `cell_label` by the author. (If the value in `cell_label` is the full-length term, this field will contain the same value.) NOTE: any reserved word used in the field 'cell_label' MUST match the value of this field. EXAMPLE 1: Given the matching terms 'LC' and 'luminal cell' used to annotate the same cell(s), then users could use either terms as values in the field 'cell_label'. However, the abbreviation 'LC' CANNOT be provided in the field 'cell_fullname'. EXAMPLE 2: Either the abbreviation 'AC' or the full-length term intended by the author 'GABAergic amacrine cell' MAY be placed in the field 'cell_label', but as full-length term naming this biological entity, 'GABAergic amacrine cell' MUST be placed in the field 'cell_fullname'.
--     * Slot: cell_ontology_term_id Description: This MUST be a term from either the Cell Ontology (https://www.ebi.ac.uk/ols/ontologies/cl) or from some ontology that extends it by classifying cell types under terms from the Cell Ontologye.g. the Provisional Cell Ontology (https://www.ebi.ac.uk/ols/ontologies/pcl) or the Drosophila Anatomy Ontology (DAO) (https://www.ebi.ac.uk/ols4/ontologies/fbbt).NOTE: The closest available ontology term matching the value within the field 'cell_label' (at the time of publication) MUST be used.For example, if the value of 'cell_label' is 'relay interneuron', but this entity does not yet exist in the ontology, users must choose the closest available term in the CL ontology. In this case, it's the broader term 'interneuron' i.e.  https://www.ebi.ac.uk/ols/ontologies/cl/terms?obo_id=CL:0000099.
--     * Slot: cell_ontology_term Description: This MUST be the human-readable name assigned to the value of 'cell_ontology_term_id'
--     * Slot: rationale Description: The free-text rationale which users provide as justification/evidence for their cell annotations. Researchers are encouraged to use this field to cite relevant publications in-line using standard academic citations of the form `(Zheng et al., 2020)` This human-readable free-text MUST be encoded as a single string.All references cited SHOULD be listed using DOIs under rationale_dois. There MUST be a 2000-character limit.
--     * Slot: Taxonomy_id Description: Autocreated FK slot
--     * Slot: author_annotation_fields_id Description: A dictionary of author defined key value pairs annotating the cell set. The names and aims of these fields MUST not clash with official annotation fields.
-- # Class: "Taxonomy" Description: ""
--     * Slot: id Description: 
--     * Slot: matrix_file_id Description: A resolvable ID for a cell by gene matrix file in the form namespace:accession, e.g. CellXGene_dataset:8e10f1c4-8e98-41e5-b65f-8cd89a887122.  Please see https://github.com/cellannotation/cell-annotation-schema/registry/registry.json for supported namespaces.
--     * Slot: title Description: The title of the dataset. This MUST be less than or equal to 200 characters. e.g. 'Human retina cell atlas - retinal ganglion cells'.
--     * Slot: description Description: The description of the dataset. e.g. 'A total of 15 retinal ganglion cell clusters were identified from over 99K retinal ganglion cell nuclei in the current atlas. Utilizing previous characterized markers from macaque, 5 clusters can be annotated.'
--     * Slot: cellannotation_schema_version Description: The schema version, the cell annotation open standard. Current version MUST follow 0.1.0This versioning MUST follow the format `'[MAJOR].[MINOR].[PATCH]'` as defined by Semantic Versioning 2.0.0, https://semver.org/
--     * Slot: cellannotation_timestamp Description: The timestamp of all cell annotations published (per dataset). This MUST be a string in the format `'%yyyy-%mm-%dd %hh:%mm:%ss'`
--     * Slot: cellannotation_version Description: The version for all cell annotations published (per dataset). This MUST be a string. The recommended versioning format is `'[MAJOR].[MINOR].[PATCH]'` as defined by Semantic Versioning 2.0.0, https://semver.org/
--     * Slot: cellannotation_url Description: A persistent URL of all cell annotations published (per dataset).
--     * Slot: author_list Description: This field stores a list of users who are included in the project as collaborators, regardless of their specific role. An example list; '['John Smith', 'Cody Miller', 'Sarah Jones']'
--     * Slot: author_name Description: Primary author's name. This MUST be a string in the format `[FIRST NAME] [LAST NAME]`
--     * Slot: author_contact Description: Primary author's contact. This MUST be a valid email address of the author
--     * Slot: orcid Description: Primary author's orcid. This MUST be a valid ORCID for the author
-- # Class: "Cap_Annotation_canonical_marker_genes" Description: ""
--     * Slot: Cap_Annotation_id Description: Autocreated FK slot
--     * Slot: canonical_marker_genes Description: A list of gene names considered to be canonical markers for the biological entity used in the cell annotation.
-- # Class: "Cap_Annotation_cell_ids" Description: ""
--     * Slot: Cap_Annotation_id Description: Autocreated FK slot
--     * Slot: cell_ids Description: Cell barcode sequences/UUIDs used to uniquely identify the cells within the AnnData/Seurat matrix. Any and all cell barcode sequences/UUIDs MUST be included in the AnnData/Seurat matrix.
-- # Class: "Cap_Annotation_rationale_dois" Description: ""
--     * Slot: Cap_Annotation_id Description: Autocreated FK slot
--     * Slot: rationale_dois Description: 
-- # Class: "Cap_Annotation_marker_gene_evidence" Description: ""
--     * Slot: Cap_Annotation_id Description: Autocreated FK slot
--     * Slot: marker_gene_evidence Description: Gene names explicitly used as evidence, which MUST be in the matrix of the AnnData/Seurat file
-- # Class: "Cap_Annotation_synonyms" Description: ""
--     * Slot: Cap_Annotation_id Description: Autocreated FK slot
--     * Slot: synonyms Description: List of synonyms
-- # Class: "Cap_Annotation_reviews" Description: ""
--     * Slot: Cap_Annotation_id Description: Autocreated FK slot
--     * Slot: reviews_id Description: 
-- # Class: "Annotation_cell_ids" Description: ""
--     * Slot: Annotation_id Description: Autocreated FK slot
--     * Slot: cell_ids Description: Cell barcode sequences/UUIDs used to uniquely identify the cells within the AnnData/Seurat matrix. Any and all cell barcode sequences/UUIDs MUST be included in the AnnData/Seurat matrix.
-- # Class: "Annotation_rationale_dois" Description: ""
--     * Slot: Annotation_id Description: Autocreated FK slot
--     * Slot: rationale_dois Description: 
-- # Class: "Annotation_marker_gene_evidence" Description: ""
--     * Slot: Annotation_id Description: Autocreated FK slot
--     * Slot: marker_gene_evidence Description: Gene names explicitly used as evidence, which MUST be in the matrix of the AnnData/Seurat file
-- # Class: "Annotation_synonyms" Description: ""
--     * Slot: Annotation_id Description: Autocreated FK slot
--     * Slot: synonyms Description: List of synonyms
-- # Class: "Annotation_reviews" Description: ""
--     * Slot: Annotation_id Description: Autocreated FK slot
--     * Slot: reviews_id Description: 

CREATE TABLE "Cap_Taxonomy" (
	id INTEGER NOT NULL, 
	cap_publication_title TEXT, 
	cap_publication_description TEXT, 
	cap_publication_url TEXT, 
	cap_dataset_url TEXT, 
	publication_timestamp TEXT, 
	publication_version TEXT, 
	matrix_file_id TEXT, 
	title TEXT NOT NULL, 
	description TEXT, 
	cellannotation_schema_version TEXT NOT NULL, 
	cellannotation_timestamp TEXT NOT NULL, 
	cellannotation_version TEXT NOT NULL, 
	cellannotation_url TEXT NOT NULL, 
	author_list TEXT, 
	author_name TEXT NOT NULL, 
	author_contact TEXT, 
	orcid TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE "Any" (
	id INTEGER NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE "Review" (
	id INTEGER NOT NULL, 
	datestamp TEXT NOT NULL, 
	reviewer TEXT, 
	review VARCHAR(8), 
	explanation TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE "AutomatedAnnotation" (
	id INTEGER NOT NULL, 
	algorithm_name TEXT NOT NULL, 
	algorithm_version TEXT NOT NULL, 
	algorithm_repo_url TEXT NOT NULL, 
	reference_location TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE "Taxonomy" (
	id INTEGER NOT NULL, 
	matrix_file_id TEXT, 
	title TEXT NOT NULL, 
	description TEXT, 
	cellannotation_schema_version TEXT, 
	cellannotation_timestamp TEXT, 
	cellannotation_version TEXT, 
	cellannotation_url TEXT, 
	author_list TEXT, 
	author_name TEXT NOT NULL, 
	author_contact TEXT, 
	orcid TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE "Cap_Annotation" (
	id INTEGER NOT NULL, 
	cell_ontology_exists BOOLEAN, 
	category_fullname TEXT, 
	category_cell_ontology_exists BOOLEAN, 
	category_cell_ontology_term_id TEXT, 
	category_cell_ontology_term TEXT, 
	cell_ontology_assessment TEXT, 
	labelset TEXT NOT NULL, 
	cell_label TEXT NOT NULL, 
	cell_fullname TEXT, 
	cell_ontology_term_id VARCHAR(10), 
	cell_ontology_term TEXT, 
	rationale TEXT, 
	"Cap_Taxonomy_id" INTEGER, 
	author_annotation_fields_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY("Cap_Taxonomy_id") REFERENCES "Cap_Taxonomy" (id), 
	FOREIGN KEY(author_annotation_fields_id) REFERENCES "Any" (id)
);
CREATE TABLE "Labelset" (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	description TEXT, 
	annotation_method VARCHAR(11), 
	"Cap_Taxonomy_id" INTEGER, 
	"Taxonomy_id" INTEGER, 
	automated_annotation_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY("Cap_Taxonomy_id") REFERENCES "Cap_Taxonomy" (id), 
	FOREIGN KEY("Taxonomy_id") REFERENCES "Taxonomy" (id), 
	FOREIGN KEY(automated_annotation_id) REFERENCES "AutomatedAnnotation" (id)
);
CREATE TABLE "Annotation" (
	id INTEGER NOT NULL, 
	labelset TEXT NOT NULL, 
	cell_label TEXT NOT NULL, 
	cell_fullname TEXT, 
	cell_ontology_term_id VARCHAR(10), 
	cell_ontology_term TEXT, 
	rationale TEXT, 
	"Taxonomy_id" INTEGER, 
	author_annotation_fields_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY("Taxonomy_id") REFERENCES "Taxonomy" (id), 
	FOREIGN KEY(author_annotation_fields_id) REFERENCES "Any" (id)
);
CREATE TABLE "Cap_Annotation_canonical_marker_genes" (
	"Cap_Annotation_id" INTEGER, 
	canonical_marker_genes TEXT, 
	PRIMARY KEY ("Cap_Annotation_id", canonical_marker_genes), 
	FOREIGN KEY("Cap_Annotation_id") REFERENCES "Cap_Annotation" (id)
);
CREATE TABLE "Cap_Annotation_cell_ids" (
	"Cap_Annotation_id" INTEGER, 
	cell_ids TEXT, 
	PRIMARY KEY ("Cap_Annotation_id", cell_ids), 
	FOREIGN KEY("Cap_Annotation_id") REFERENCES "Cap_Annotation" (id)
);
CREATE TABLE "Cap_Annotation_rationale_dois" (
	"Cap_Annotation_id" INTEGER, 
	rationale_dois TEXT, 
	PRIMARY KEY ("Cap_Annotation_id", rationale_dois), 
	FOREIGN KEY("Cap_Annotation_id") REFERENCES "Cap_Annotation" (id)
);
CREATE TABLE "Cap_Annotation_marker_gene_evidence" (
	"Cap_Annotation_id" INTEGER, 
	marker_gene_evidence TEXT, 
	PRIMARY KEY ("Cap_Annotation_id", marker_gene_evidence), 
	FOREIGN KEY("Cap_Annotation_id") REFERENCES "Cap_Annotation" (id)
);
CREATE TABLE "Cap_Annotation_synonyms" (
	"Cap_Annotation_id" INTEGER, 
	synonyms TEXT, 
	PRIMARY KEY ("Cap_Annotation_id", synonyms), 
	FOREIGN KEY("Cap_Annotation_id") REFERENCES "Cap_Annotation" (id)
);
CREATE TABLE "Cap_Annotation_reviews" (
	"Cap_Annotation_id" INTEGER, 
	reviews_id INTEGER, 
	PRIMARY KEY ("Cap_Annotation_id", reviews_id), 
	FOREIGN KEY("Cap_Annotation_id") REFERENCES "Cap_Annotation" (id), 
	FOREIGN KEY(reviews_id) REFERENCES "Review" (id)
);
CREATE TABLE "Annotation_cell_ids" (
	"Annotation_id" INTEGER, 
	cell_ids TEXT, 
	PRIMARY KEY ("Annotation_id", cell_ids), 
	FOREIGN KEY("Annotation_id") REFERENCES "Annotation" (id)
);
CREATE TABLE "Annotation_rationale_dois" (
	"Annotation_id" INTEGER, 
	rationale_dois TEXT, 
	PRIMARY KEY ("Annotation_id", rationale_dois), 
	FOREIGN KEY("Annotation_id") REFERENCES "Annotation" (id)
);
CREATE TABLE "Annotation_marker_gene_evidence" (
	"Annotation_id" INTEGER, 
	marker_gene_evidence TEXT, 
	PRIMARY KEY ("Annotation_id", marker_gene_evidence), 
	FOREIGN KEY("Annotation_id") REFERENCES "Annotation" (id)
);
CREATE TABLE "Annotation_synonyms" (
	"Annotation_id" INTEGER, 
	synonyms TEXT, 
	PRIMARY KEY ("Annotation_id", synonyms), 
	FOREIGN KEY("Annotation_id") REFERENCES "Annotation" (id)
);
CREATE TABLE "Annotation_reviews" (
	"Annotation_id" INTEGER, 
	reviews_id INTEGER, 
	PRIMARY KEY ("Annotation_id", reviews_id), 
	FOREIGN KEY("Annotation_id") REFERENCES "Annotation" (id), 
	FOREIGN KEY(reviews_id) REFERENCES "Review" (id)
);