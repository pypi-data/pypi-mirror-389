"""Console script for consdata"""

import click

from .core import list_cons
from .config import find_config


@click.group()
def main():
    pass


@main.command()
def config():
    """Print the path to the config file"""
    click.echo(find_config())


@main.command()
def list():
    """List all cons"""
    items = list_cons()
    for item in items:
        click.echo(item)


if __name__ == "__main__":
    main()
