![Schema Validation](https://github.com/Cellular-Semantics/cell-annotation-schema/actions/workflows/schema_validator.yaml/badge.svg?branch=main)

**_DRAFT: LinkML based [schema](https://cellular-semantics.github.io/cell-annotation-schema/) for cell annotations._**

**_For the original/working repo visit https://github.com/cellannotation/cell-annotation-schema_**



# Cell Annotation Schema

A general, open-standard schema for cell annotations and related metadata.

This effort is part of [scFAIR](https://sc-fair.org/), an initiative to standardize single-cell genomics metadata.

## Motivation

Annotation of single cell transcriptomics data with cell types/classes is inherently variable. The reasons authors choose to annotate a set of cells with a particular label are not typically represented in annotated data and there is no established standard for doing so.  For relatively simple datasets it may be possible to reconstruct this information by reading an associated publication, but as single cell transcriptomics datasets and accompanying publications become increasingly complex, doing so is becoming increasingly difficult and in many cases publications lack the necessary detail.

CAS provides a programmatically accessible standard designed to solve this problem by allowing users to record additional metadata about individual cell type annotations, including marker genes used as evidence and details of automated annotation transfer.  The standard is represented as LinkML schema as this allows all metadata to be gathered in a single, compact validatable file - which includes a link to a cell by gene matrix file of annotated data. However, the schema is designed so that it can be decomposed into individual tables suitable for use in dataframes/TSVs and flattened onto obs in AnnData format.

## User stories: 

https://github.com/cellannotation/cell-annotation-schema/blob/main/docs/user_stories.md

## Examples

Examples used in testing can be browsed under: https://github.com/Cellular-Semantics/cell-annotation-schema/tree/main/examples

brain-bican contains a growing set of working taxonomies including: 

- https://github.com/brain-bican/human-brain-cell-atlas_v1_neurons
- https://github.com/brain-bican/human-brain-cell-atlas_v1_non-neuronal
- https://github.com/brain-bican/human-neocortex-middle-temporal-gyrus

## Overview

The top level of the LinkML schema is used to store metadata about the annotations: Author details; links to the annotated matrix file, version information etc.  This can be thought of as a table that links to a set of subtables.

The top level wraps other JSON objects (sub-tables):

1. A list of annotation objects (a table of annotations). Each annotation belongs to a named `labelset`
2. A table of labelsets - recording names, and additional metadata including a description and provenance (manual vs automated) and if automated, details of automated annotation algorithms etc.

## Core schema vs extensions

We define a core schema with a very limited set of compulsory fields.  The core schema avoids specifying that additional fields are forbidden, allowing extensions to be built and for any users to add their own customs fields as long as they don't stomp on existing fields in the specification. 

Documentation for the core and extension schemas is available at:

- [general_schema](https://cellular-semantics.github.io/cell-annotation-schema/); Derived from [general_schema.yaml](https://github.com/Cellular-Semantics/cell-annotation-schema/blob/main/src/cell_annotation_schema/schema/cell_annotation_schema.yaml)
  - [BICAN_schema](https://cellular-semantics.github.io/cell-annotation-schema/bican/); Derived from [BICAN_schema.yaml](https://github.com/Cellular-Semantics/cell-annotation-schema/blob/main/src/cell_annotation_schema/schema/BICAN/BICAN_schema.yaml)
  - [CAP_schema](https://cellular-semantics.github.io/cell-annotation-schema/cap/); Derived from [CAP_schema.yaml](https://github.com/Cellular-Semantics/cell-annotation-schema/blob/main/src/cell_annotation_schema/schema/cell_annotation_schema.yaml)

Merged LinkML schemas are available at [build](https://github.com/Cellular-Semantics/cell-annotation-schema/tree/main/build) folder

This repo also contains the [CAP AnnData Specification](https://github.com/cellannotation/cell-annotation-schema/blob/main/docs/cap_anndata_schema.md). 

## Editing the schema

1. Schema editing is done in the [src/cell_annotation_schema/schema](src/cell_annotation_schema/schema) folder.
2. Dataclasses needs to be updated to reflect the changes in the schema. This is done by running `make build` command in the project root folder. (see [project.Makefile](project.Makefile)
_Note: this will require creating a poetry virtual env and install dependencies via `poetry install`_

## Releases

We publish both versioned releases and a nightly snapshot at https://github.com/Cellular-Semantics/cell-annotation-schema/releases

Release assets include a core schema file and extensions (currently for BICAN and the Cell Annotation Platform).

PyPI release is at https://pypi.org/project/cell-annotation-schema/

You can discover instructions on utilizing the PyPI package by visiting the following link https://github.com/cellannotation/cell-annotation-schema/blob/main/docs/pypi_package.md.
