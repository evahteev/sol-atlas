import logging
from pathlib import Path

import click

from ethereumetl import clickhouse


@click.command()
@click.option('-u', '--clickhouse-url', envvar='CLICKHOUSE_URL', required=True)
def cli(clickhouse_url):
    logging.basicConfig(level=logging.INFO, format='%(levelname)-5.5s [%(name)s] %(message)s')

    output_file_path = (
        clickhouse.SCHEMA_FILE_PATH.relative_to(Path.cwd())
        if clickhouse.SCHEMA_FILE_PATH.is_relative_to(Path.cwd())
        else clickhouse.SCHEMA_FILE_PATH.absolute()
    )

    clickhouse.dump_migration_schema(clickhouse_url, output_file_path)

    logging.info(f'Done. Schema DDL is written to "{output_file_path}".')


if __name__ == '__main__':
    cli()
