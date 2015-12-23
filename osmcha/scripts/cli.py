# Skeleton of a CLI

import click

from osmcha.changeset import Analyse


@click.command('osmcha')
@click.argument('id', type=int, metavar='changeset_id')
def cli(id):
    """Analyse an OpenStreetMap changeset."""
    ch = Analyse(id)
    ch.full_analysis()
    click.echo(
        'Created: %s. Modified: %s. Deleted: %s' % (ch.create, ch.modify, ch.delete)
    )
    if ch.is_suspect:
        click.echo('The changeset %s is suspect!' % id)
    else:
        click.echo('The changeset %s is not suspect!' % id)
