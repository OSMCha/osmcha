# Skeleton of a CLI

import click

import osmcha


@click.command('osmcha')
@click.argument('count', type=int, metavar='N')
def cli(count):
    """Echo a value `N` number of times"""
    for i in range(count):
        click.echo(osmcha.has_legs)
