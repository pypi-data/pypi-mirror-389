import click

from linkml_runtime.utils.schema_as_dict import schema_as_dict
from schema_automator.utils.schemautils import write_schema

from cell_annotation_schema.file_utils import read_schema
from cell_annotation_schema.ontology.schema import expand_schema


@click.group()
def cli():
    pass


@cli.command()
@click.option('-i', '--input', type=click.Path(exists=True), help='Input schema path.')
@click.option('-o', '--output', type=click.Path(), help='Output file path.')
def expand(input, output):
    schema_obj = read_schema(input)
    input_schema = schema_as_dict(schema_obj)
    expanded_schema = expand_schema(
        config=None, yaml_obj=input_schema, value_set_names=["CellTypeEnum"]
    )
    write_schema(expanded_schema, output)




if __name__ == '__main__':
    cli()