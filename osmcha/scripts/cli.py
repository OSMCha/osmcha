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
        reasonDescriptions = [formatted_reason(reason) for reason in ch.detailed_reasons.values()]
        click.echo('The changeset {} is suspect! Reasons: {}'.format(
            id,
            ', '.join(reasonDescriptions)
            ))
    else:
        click.echo('The changeset %s is not suspect!' % id)

def formatted_reason(reason):
  """
  Generate a formatted description of the reason using its label and appending
  the source of the reason if it was not from osmcha (e.g. if it originated
  from an editor warning)
  """
  sourceLabel = ' ({})'.format(reason.source) if reason.source != 'osmcha' else ''
  return '{}{}'.format(reason.label, sourceLabel)
