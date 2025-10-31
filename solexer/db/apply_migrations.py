import os
import subprocess

import click
import yaml


@click.command()
@click.argument('helm_values_file_path', type=click.Path(exists=True))
def run_alembic_upgrade(helm_values_file_path):
    """
    Runs alembic upgrade head with CLICKHOUSE_URL set for each chain in the YAML file.
    """
    with open(helm_values_file_path) as file:
        data = yaml.safe_load(file)

    output_data = data.get('chainEnv', {})
    output_data = output_data.get('OUTPUT', {})

    for key, value in output_data.items():
        if key != 'default':
            clickhouse_url = value.split(',')[0]  # Assuming we only need the first URL
            click.echo(f"Running alembic upgrade for {key} with CLICKHOUSE_URL={clickhouse_url}")
            os.environ['CLICKHOUSE_URL'] = clickhouse_url
            subprocess.run(["alembic", "upgrade", "head"])


if __name__ == '__main__':
    run_alembic_upgrade()
