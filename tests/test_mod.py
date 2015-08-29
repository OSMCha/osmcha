from pytest import raises
from shapely.geometry import Polygon

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
    assert c.changesets[0]['bbox'] == Polygon([
        (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
        (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
        (-71.0646843, 44.2371354)
    ])


def test_changeset_list_with_filters():
    c = ChangesetList('tests/245.osm.gz', 'tests/map.geojson')
    assert len(c.changesets) == 1
    assert c.changesets[0]['id'] == '31982803'


def test_invalid_changeset_error():
    with raises(InvalidChangesetError):
        Analyse([999])


def test_analyse_init():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Put data from Google',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    assert ch.id == 1
    assert ch.editor == 'Potlatch 2'
    assert ch.comment == 'Put data from Google'
    assert ch.user == 'JustTest'


def test_analyse_verify_words():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Put data from Google',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_words()
    assert ch.is_suspect
    assert 'suspect_word' in ch.suspicion_reasons

    ch_dict = {
        'created_by': 'Potlatch 2',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'source': 'Waze',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_words()
    assert ch.is_suspect
    assert 'suspect_word' in ch.suspicion_reasons

    ch_dict = {
        'created_by': 'Potlatch 2',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'imagery_used': 'Custom (http://{switch:a,b,c}.tiles.googlemaps.com/{zoom}/{x}/{y}.png)',
        'source': 'Bing',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_words()
    assert ch.is_suspect
    assert 'suspect_word' in ch.suspicion_reasons


def test_analyse_verify_editor():
    ch_dict = {
        'created_by': 'JOSM/1.5 (8339 en)',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor

    ch_dict = {
        'created_by': 'Merkaartor 0.18 (de)',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor

    ch_dict = {
        'created_by': 'Level0 v1.1',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor

    ch_dict = {
        'created_by': 'QGIS plugin',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor

    ch_dict = {
        'created_by': 'iD 1.7.3',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False

    ch_dict = {
        'created_by': 'Potlatch 2',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
        ])
    }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False


def test_analyse_count():
    ch = Analyse(32663070)
    ch.full_analysis()
    assert ch.create == 8
    assert ch.modify == 3
    assert ch.delete == 2
    assert ch.is_suspect is False
    assert len(ch.suspicion_reasons) == 0


def test_analyse_import():
    ch = Analyse(10013029)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'possible import' in ch.suspicion_reasons


def test_analyse_mass_modification():
    ch = Analyse(19863853)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'mass modification' in ch.suspicion_reasons


def test_analyse_mass_deletion():
    ch = Analyse(31450443)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'mass deletion' in ch.suspicion_reasons
