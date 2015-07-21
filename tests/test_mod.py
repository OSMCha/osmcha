from pytest import raises
from shapely.geometry import MultiPoint

from osmcha.changeset import ChangesetList
from osmcha.changeset import Analyse
from osmcha.changeset import get_metadata, changeset_info, InvalidChangesetError


def test_changeset_list():
    c = ChangesetList('tests/245.osm.gz')
    assert len(c.changesets) == 25
    assert c.changesets[0]['id'] == '31982803'
    assert c.changesets[0]['created_by'] == 'Potlatch 2'
    assert c.changesets[0]['user'] == 'GarrettB'
    assert c.changesets[0]['comment'] == 'Added Emerald Pool Waterfall'
    assert c.changesets[0]['bounds'] == MultiPoint([
        (-71.0646843, 44.2371354), (-71.0048652, 44.2430624)])


def test_changeset_list_with_filters():
    c = ChangesetList('tests/245.osm.gz', 'tests/map.geojson')
    assert len(c.changesets) == 1
    assert c.changesets[0]['id'] == '31982803'


def test_invalid_changeset_error():
    with raises(InvalidChangesetError):
        Analyse([999])


def test_analyse_verify_words():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Put data from Google',
        'id': '1',
        'user': 'JustTest'
    }

    ch = Analyse(ch_dict)
    assert ch.is_suspect
    assert 'suspect_word' in ch.reasons

    ch_dict = {
        'created_by': 'Potlatch 2',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'source': 'Waze',
        'id': '1',
        'user': 'JustTest'
    }

    ch = Analyse(ch_dict)
    assert ch.is_suspect
    assert 'suspect_word' in ch.reasons


def test_changeset_count():
    ch = Analyse(32663070)
    assert ch.count() == {'create': 8, 'modify': 3, 'delete': 2}