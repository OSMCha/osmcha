# Skeleton of a CLI

import click

import osmdetective


@click.command('osmdetective')
@click.argument('count', type=int, metavar='N')
def cli(count):
    """Echo a value `N` number of times"""
    for i in range(count):
        click.echo(osmdetective.has_legs)
