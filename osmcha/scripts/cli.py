# -*- coding: utf-8 -*-
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
        click.echo('The changeset {} is suspect! Reasons: {}'.format(
            id,
            ', '.join(ch.suspicion_reasons)
            ))
    else:
        click.echo('The changeset %s is not suspect!' % id)
