# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from pytest import raises
from shapely.geometry import Polygon

from osmcha.changeset import ChangesetList
from osmcha.changeset import Analyse
from osmcha.changeset import WORDS
from osmcha.changeset import find_words
from osmcha.changeset import InvalidChangesetError


def test_find_words():
    """Test the changeset.find_words function and the regular expressions."""
    suspect_words = WORDS['sources'] + WORDS['common']
    excluded_words = WORDS['exclude']

    assert find_words('import buildings', suspect_words)
    assert find_words('imported Importação unimportant', suspect_words, excluded_words)
    assert not find_words('important edit', suspect_words, excluded_words)
    assert not find_words('Where is here?', suspect_words, excluded_words)
    assert find_words('GooGle is not important', suspect_words, excluded_words)
    assert not find_words('somewhere in the world', suspect_words, excluded_words)
    assert find_words('дані по імпорту', suspect_words, excluded_words)
    assert find_words('places from яндекс', suspect_words, excluded_words)
    assert find_words('places from 2gis', suspect_words, excluded_words)
    assert find_words('places from 2гис', suspect_words, excluded_words)
    assert find_words('places from yandex', suspect_words, excluded_words)
    assert not find_words('Yandex Panorama', suspect_words, excluded_words)


def test_changeset_list():
    """Test ChangesetList class."""
    c = ChangesetList('tests/245.osm.gz')
    assert len(c.changesets) == 25
    assert c.changesets[0]['id'] == '31982803'
    assert c.changesets[0]['created_by'] == 'Potlatch 2'
    assert c.changesets[0]['user'] == 'GarrettB'
    assert c.changesets[0]['uid'] == '352373'
    assert c.changesets[0]['comment'] == 'Added Emerald Pool Waterfall'
    assert c.changesets[0]['bbox'] == Polygon([
        (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
        (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
        (-71.0646843, 44.2371354)
        ])


def test_changeset_list_with_filters():
    """Test ChangesetList class filter method."""
    c = ChangesetList('tests/245.osm.gz', 'tests/map.geojson')
    assert len(c.changesets) == 1
    assert c.changesets[0]['id'] == '31982803'


def test_invalid_changeset_error():
    with raises(InvalidChangesetError):
        Analyse([999])


def test_analyse_init():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Put data from Google',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
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
    assert ch.uid == '123123'
    assert ch.date == datetime(2015, 4, 25, 18, 8, 46)


def test_analyse_label_suspicious():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Put data from Google',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.label_suspicious('some reason')
    assert 'some reason' in ch.suspicion_reasons
    assert ch.is_suspect


def test_changeset_without_coords():
    """Changeset deleted a relation, so it has not a bbox."""
    ch = Analyse(33624206)
    assert ch.bbox == 'GEOMETRYCOLLECTION EMPTY'


def test_analyse_verify_words():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Put data from Google',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
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
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'source': 'Waze',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
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
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'imagery_used': 'Custom (http://{switch:a,b,c}.tiles.googlemaps.com/{zoom}/{x}/{y}.png)',
        'source': 'Bing',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
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
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Somewhere in Brazil',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_words()
    assert not ch.is_suspect

    ch_dict = {
        'created_by': 'Potlatch 2',
        'created_at': '2015-04-25T18:08:46Z',
        'build': '2.3-650-gad99430',
        'version': '2.3',
        'comment': 'Somewhere in Brazil',
        'source': 'Yandex Panorama',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_words()
    assert not ch.is_suspect


def test_analyse_verify_editor_josm():
    """Test if JOSM is a powerfull_editor."""
    ch_dict = {
        'created_by': 'JOSM/1.5 (8339 en)',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor


def test_analyse_verify_editor_merkaartor():
    """Test if Merkaartor is a powerfull_editor."""
    ch_dict = {
        'created_by': 'Merkaartor 0.18 (de)',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor


def test_analyse_verify_editor_level0():
    """Test if Level0 is a powerfull_editor."""
    ch_dict = {
        'created_by': 'Level0 v1.1',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor


def test_analyse_verify_editor_qgis():
    """Test if QGIS is a powerfull_editor."""
    ch_dict = {
        'created_by': 'QGIS plugin',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor


def test_analyse_verify_editor_id_osm():
    """Test if iD is not a powerfull_editor and if https://www.openstreetmap.org/edit
    is a trusted instance.
    """
    ch_dict = {
        'created_by': 'iD 1.7.3',
        'host': 'https://www.openstreetmap.org/edit',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert ch.suspicion_reasons == []


def test_analyse_verify_editor_id_improveosm():
    """Test if iD is not a powerfull_editor and if http://improveosm.org
    is a trusted instance.
    """
    ch_dict = {
        'created_by': 'iD 1.7.3',
        'host': 'http://improveosm.org/',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert ch.suspicion_reasons == []


def test_analyse_verify_editor_id_strava():
    """Test if iD is not a powerfull_editor and if https://strava.github.io/iD/
    is a trusted instance.
    """
    ch_dict = {
        'created_by': 'iD 1.7.3',
        'host': 'https://strava.github.io/iD/',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert ch.suspicion_reasons == []


def test_analyse_verify_editor_rapid():
    """Test if RapiD is not a powerfull_editor and a trusted instance."""
    ch_dict = {
        'created_by': 'RapiD 0.9.0',
        'host': 'https://mapwith.ai/rapid',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert ch.suspicion_reasons == []


def test_analyse_verify_editor_rapid_test():
    """Test if RapiD test is not a powerfull_editor and a trusted instance."""
    ch_dict = {
        'created_by': 'RapiD 0.9.0',
        'host': 'https://mapwith.ai/rapidtest',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert ch.suspicion_reasons == []


def test_verify_editor_id_unknown_instance():
    """Test if iD is not a powerfull_editor and if 'Unknown iD instance' is added
    to suspicion_reasons.
    """
    ch_dict = {
        'created_by': 'iD 1.7.3',
        'host': 'http://anotherhost.com/iD',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert 'Unknown iD instance' in ch.suspicion_reasons
    assert ch.is_suspect


def test_verify_editor_id_is_known_instance():
    """Test if iD is not a powerfull_editor and if 'Unknown iD instance' is added
    to suspicion_reasons.
    """
    ch_dict = {
        'created_by': 'iD 1.7.3',
        'host': 'https://www.openstreetmap.org/iD',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    ch = Analyse(ch_dict)
    ch.verify_editor()
    assert ch.powerfull_editor is False
    assert 'Unknown iD instance' not in ch.suspicion_reasons
    assert ch.is_suspect is False


def test_analyse_verify_editor_Potlatch2():
    """Test if Potlatch 2 is not a powerfull_editor."""
    ch_dict = {
        'created_by': 'Potlatch 2',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
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
    """Created: 1900. Modified: 16. Deleted: 320 / JOSM"""
    ch = Analyse(10013029)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'possible import' in ch.suspicion_reasons


def test_new_user_custom_create_value():
    """Created: 1900. Modified: 16. Deleted: 320 / JOSM"""
    ch = Analyse(10013029, create_threshold=2000)
    ch.full_analysis()
    assert ch.is_suspect is True
    assert 'possible import' not in ch.suspicion_reasons
    assert 'New mapper' in ch.suspicion_reasons
    assert len(ch.suspicion_reasons) == 1


def test_analyse_mass_modification():
    """Created: 322. Modified: 1115. Deleted: 140 / Potlatch 2"""
    ch = Analyse(19863853)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'mass modification' in ch.suspicion_reasons


def test_custom_modify_value():
    """Created: 322. Modified: 1115. Deleted: 140 / Potlatch 2"""
    ch = Analyse(19863853, modify_threshold=1200)
    ch.full_analysis()
    assert ch.is_suspect is False
    assert len(ch.suspicion_reasons) == 0


def test_analyse_mass_deletion():
    """Created: 0. Modified: 0. Deleted: 1019 / Potlatch 2"""
    ch = Analyse(31450443)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'mass deletion' in ch.suspicion_reasons


def test_custom_delete_value():
    """C/M/D = 0 0 61 / iD"""
    ch = Analyse(45901540, delete_threshold=100)
    ch.full_analysis()
    assert ch.is_suspect is False
    assert len(ch.suspicion_reasons) == 0


def test_custom_percentage():
    """C/M/D = 481 620 80 / JOSM"""
    ch = Analyse(45082154)
    ch.full_analysis()
    assert ch.is_suspect is False
    assert len(ch.suspicion_reasons) == 0

    ch = Analyse(45082154, percentage=0.5)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'mass modification' in ch.suspicion_reasons


def test_custom_top_threshold():
    """C/M/D = 1072 124 282 / made with iD"""
    ch = Analyse(45862717)
    ch.full_analysis()
    assert ch.is_suspect
    assert 'possible import' in ch.suspicion_reasons

    ch = Analyse(45862717, top_threshold=1100)
    ch.full_analysis()
    assert ch.is_suspect is False
    assert len(ch.suspicion_reasons) == 0


def test_no_duplicated_reason():
    """Changeset with word import in comment and source fields."""
    ch = Analyse(45632780)
    ch.full_analysis()
    assert ch.is_suspect
    assert ch.suspicion_reasons == ['suspect_word']


def test_redacted_changeset():
    """Redacted changesets have no metadata so those cases need to be threated
    to avoid a ZeroDivisionError in the Analyse.count() method.
    """
    ch = Analyse(34495147)
    ch.full_analysis()
    assert ch.is_suspect is False


def test_get_dict():
    """Test if get_dict function return only the fields that osmcha-django needs
    to save in the database.
    """
    # An iD changeset
    ch = Analyse(46286980)
    ch.full_analysis()
    assert 'id' in ch.get_dict().keys()
    assert 'user' in ch.get_dict().keys()
    assert 'uid' in ch.get_dict().keys()
    assert 'editor' in ch.get_dict().keys()
    assert 'bbox' in ch.get_dict().keys()
    assert 'date' in ch.get_dict().keys()
    assert 'comment' in ch.get_dict().keys()
    assert 'source' in ch.get_dict().keys()
    assert 'imagery_used' in ch.get_dict().keys()
    assert 'is_suspect' in ch.get_dict().keys()
    assert 'powerfull_editor' in ch.get_dict().keys()
    assert 'suspicion_reasons' in ch.get_dict().keys()
    assert 'create' in ch.get_dict().keys()
    assert 'modify' in ch.get_dict().keys()
    assert 'delete' in ch.get_dict().keys()
    assert len(ch.get_dict().keys()) == 15

    # An iD changeset with warnings:
    ch = Analyse(72783703)
    ch.full_analysis()
    assert 'id' in ch.get_dict().keys()
    assert 'user' in ch.get_dict().keys()
    assert 'uid' in ch.get_dict().keys()
    assert 'editor' in ch.get_dict().keys()
    assert 'bbox' in ch.get_dict().keys()
    assert 'date' in ch.get_dict().keys()
    assert 'comment' in ch.get_dict().keys()
    assert 'source' in ch.get_dict().keys()
    assert 'imagery_used' in ch.get_dict().keys()
    assert 'is_suspect' in ch.get_dict().keys()
    assert 'powerfull_editor' in ch.get_dict().keys()
    assert 'suspicion_reasons' in ch.get_dict().keys()
    assert 'create' in ch.get_dict().keys()
    assert 'modify' in ch.get_dict().keys()
    assert 'delete' in ch.get_dict().keys()
    assert len(ch.get_dict().keys()) == 15

    # A JOSM changeset
    ch = Analyse(46315321)
    ch.full_analysis()
    assert 'id' in ch.get_dict().keys()
    assert 'user' in ch.get_dict().keys()
    assert 'uid' in ch.get_dict().keys()
    assert 'editor' in ch.get_dict().keys()
    assert 'bbox' in ch.get_dict().keys()
    assert 'date' in ch.get_dict().keys()
    assert 'comment' in ch.get_dict().keys()
    assert 'source' in ch.get_dict().keys()
    assert 'imagery_used' in ch.get_dict().keys()
    assert 'is_suspect' in ch.get_dict().keys()
    assert 'powerfull_editor' in ch.get_dict().keys()
    assert 'suspicion_reasons' in ch.get_dict().keys()
    assert 'create' in ch.get_dict().keys()
    assert 'modify' in ch.get_dict().keys()
    assert 'delete' in ch.get_dict().keys()
    assert len(ch.get_dict().keys()) == 15


def test_changeset_without_tags():
    ch = Analyse(46755934)
    ch.full_analysis()
    assert ch.powerfull_editor
    assert ch.is_suspect
    assert 'Software editor was not declared' in ch.suspicion_reasons


def test_changeset_by_user_with_more_than_one_block():
    changeset = Analyse(34879408)
    changeset.full_analysis()
    assert 'User has multiple blocks' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_by_new_mapper():
    changeset = Analyse(46756461)
    changeset.full_analysis()
    assert 'New mapper' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_by_new_mapper():
    changeset = Analyse(36700893)
    changeset.full_analysis()
    print(changeset.suspicion_reasons)
    assert 'New mapper' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_with_6_mapping_days():
    changeset = Analyse(13523366)
    changeset.full_analysis()
    assert 'New mapper' not in changeset.suspicion_reasons
    assert not changeset.is_suspect


def test_changeset_by_old_mapper_with_unicode_username():
    changeset = Analyse(46790192)
    changeset.full_analysis()
    assert 'New mapper' not in changeset.suspicion_reasons
    assert not changeset.is_suspect


def test_changeset_by_old_mapper_with_special_character_username():
    changeset = Analyse(46141825)
    changeset.full_analysis()
    assert 'New mapper' not in changeset.suspicion_reasons
    assert not changeset.is_suspect


def test_changeset_with_review_requested():
    ch_dict = {
        'created_by': 'Potlatch 2',
        'created_at': '2015-04-25T18:08:46Z',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'review_requested': 'yes',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert 'Review requested' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_with_warning_tag_almost_junction():
    ch_dict = {
        'created_by': 'iD',
        'created_at': '2019-04-25T18:08:46Z',
        'host': 'https://www.openstreetmap.org/edit',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'warnings:almost_junction': '1',
        'warnings:missing_role': '1',
        'warnings:missing_tag': '1',
        'warnings:private_data': '1',
        'warnings:tag_suggests_area': '1',
        'warnings:unsquare_way': '1',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert 'Almost junction' in changeset.suspicion_reasons
    assert 'Missing role' in changeset.suspicion_reasons
    assert 'Missing tag' in changeset.suspicion_reasons
    assert 'Private information' in changeset.suspicion_reasons
    assert 'Line tagged as area' in changeset.suspicion_reasons
    assert 'Unsquare corners' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_with_warning_tag_close_nodes():
    ch_dict = {
        'created_by': 'iD',
        'created_at': '2019-04-25T18:08:46Z',
        'host': 'https://www.openstreetmap.org/edit',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'warnings:close_nodes': '1',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert 'Very close points' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_with_warning_tag_crossing_ways():
    ch_dict = {
        'created_by': 'iD',
        'created_at': '2019-04-25T18:08:46Z',
        'host': 'https://www.openstreetmap.org/edit',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'warnings:crossing_ways': '1',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert 'Crossing ways' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_with_warning_tag_disconnected_way():
    ch_dict = {
        'created_by': 'iD',
        'created_at': '2019-04-25T18:08:46Z',
        'host': 'https://www.openstreetmap.org/edit',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'warnings:disconnected_way': '4',
        'warnings:generic_name': '4',
        'warnings:impossible_oneway': '4',
        'warnings:incompatible_source': '4',
        'warnings:outdated_tags': '9',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert 'Disconnected way' in changeset.suspicion_reasons
    assert 'Generic name' in changeset.suspicion_reasons
    assert 'Impossible oneway' in changeset.suspicion_reasons
    assert 'suspect_word' in changeset.suspicion_reasons
    assert 'Outdated tags' in changeset.suspicion_reasons
    assert changeset.is_suspect


def test_changeset_with_warning_tag_fix_me():
    ch_dict = {
        'created_by': 'iD',
        'created_at': '2019-04-25T18:08:46Z',
        'host': 'https://www.openstreetmap.org/edit',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'warnings:fix_me': '0',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert changeset.suspicion_reasons == []
    assert not changeset.is_suspect


def test_changeset_with_warning_tag_invalid_format():
    ch_dict = {
        'created_by': 'iD',
        'created_at': '2019-04-25T18:08:46Z',
        'host': 'https://www.openstreetmap.org/edit',
        'comment': 'add pois',
        'id': '1',
        'user': 'JustTest',
        'uid': '123123',
        'warnings:invalid_format': '0',
        'bbox': Polygon([
            (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
            (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
            (-71.0646843, 44.2371354)
            ])
        }
    changeset = Analyse(ch_dict)
    changeset.full_analysis()
    assert changeset.suspicion_reasons == []
    assert not changeset.is_suspect
