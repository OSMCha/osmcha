# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals
import gzip
import json
import re
from os import environ
from datetime import datetime
from os.path import basename, join, isfile, dirname, abspath
from shutil import rmtree
from tempfile import mkdtemp
import xml.etree.ElementTree as ET

import yaml
import requests
from homura import download
from shapely.geometry import Polygon

from osmcha.warnings import Warnings


# Python 2 has 'failobj' instead of 'default'
try:
    SUSPECT_WORDS_FILE = environ.get(
        'SUSPECT_WORDS',
        default=join(dirname(abspath(__file__)), 'suspect_words.yaml')
        )
except TypeError:
    SUSPECT_WORDS_FILE = environ.get(
        'SUSPECT_WORDS',
        failobj=join(dirname(abspath(__file__)), 'suspect_words.yaml')
        )
WORDS = yaml.safe_load(open(SUSPECT_WORDS_FILE, 'r').read())
OSM_USERS_API = environ.get(
    'OSM_USERS_API',
    'https://www.openstreetmap.org/api/0.6/user/{user_id}'
    )
MAPBOX_USERS_API = environ.get(
    'MAPBOX_USERS_API',
    'https://osm-comments-api.mapbox.com/api/v1/users/id/{user_id}?extra=true'
    )
MANDATORY_TAGS = ['id', 'user', 'uid', 'bbox', 'created_at']
# fields that will be removed on the Analyse.get_dict() method
FIELDS_TO_REMOVE = [
    'create_threshold', 'modify_threshold', 'illegal_sources',
    'delete_threshold', 'percentage', 'top_threshold', 'suspect_words',
    'excluded_words', 'warning_tags', 'host', 'review_requested'
    ]


class InvalidChangesetError(Exception):
    pass


def get_user_details(user_id):
    """Get information about number of changesets, blocks and mapping days of a
    user, using both the OSM API and the Mapbox comments APIself.
    """
    reasons = []
    try:
        url = OSM_USERS_API.format(user_id=requests.compat.quote(user_id))
        user_request = requests.get(url)
        if user_request.status_code == 200:
            user_data = user_request.content
            xml_data = ET.fromstring(user_data)[0]
            changesets = [i for i in xml_data if i.tag == 'changesets'][0]
            blocks = [i for i in xml_data if i.tag == 'blocks'][0]
            if int(changesets.get('count')) <= 5:
                reasons.append('New mapper')
            elif int(changesets.get('count')) <= 30:
                url = MAPBOX_USERS_API.format(
                    user_id=requests.compat.quote(user_id)
                    )
                user_request = requests.get(url)
                if user_request.status_code == 200:
                    mapping_days = int(
                        user_request.json().get('extra').get('mapping_days')
                        )
                    if mapping_days <= 5:
                        reasons.append('New mapper')
            if int(blocks[0].get('count')) > 1:
                reasons.append('User has multiple blocks')
    except Exception as e:
        message = 'Could not verify user of the changeset: {}, {}'
        print(message.format(user_id, str(e)))
    return reasons


def changeset_info(changeset):
    """Return a dictionary with id, user, user_id, bounds, date of creation
    and all the tags of the changeset.

    Args:
        changeset: the XML string of the changeset.
    """
    keys = [tag.attrib.get('k') for tag in changeset]
    keys += MANDATORY_TAGS
    values = [tag.attrib.get('v') for tag in changeset]
    values += [
        changeset.get('id'), changeset.get('user'), changeset.get('uid'),
        get_bounds(changeset), changeset.get('created_at')
        ]

    return dict(zip(keys, values))


def get_changeset(changeset):
    """Get the changeset using the OSM API and return the content as a XML
    ElementTree.

    Args:
        changeset: the id of the changeset.
    """
    url = 'https://www.openstreetmap.org/api/0.6/changeset/{}/download'.format(
        changeset
        )
    return ET.fromstring(requests.get(url).content)


def get_metadata(changeset):
    """Get the metadata of a changeset using the OSM API and return it as a XML
    ElementTree.

    Args:
        changeset: the id of the changeset.
    """
    url = 'https://www.openstreetmap.org/api/0.6/changeset/{}'.format(changeset)
    return ET.fromstring(requests.get(url).content)[0]


def get_bounds(changeset):
    """Get the bounds of the changeset and return it as a Polygon object. If
    the changeset has not coordinates (case of the changesets that deal only
    with relations), it returns an empty Polygon.

    Args:
        changeset: the XML string of the changeset.
    """
    try:
        return Polygon([
            (float(changeset.get('min_lon')), float(changeset.get('min_lat'))),
            (float(changeset.get('max_lon')), float(changeset.get('min_lat'))),
            (float(changeset.get('max_lon')), float(changeset.get('max_lat'))),
            (float(changeset.get('min_lon')), float(changeset.get('max_lat'))),
            (float(changeset.get('min_lon')), float(changeset.get('min_lat'))),
            ])
    except TypeError:
        return Polygon()


def make_regex(words):
    """Concatenate a list of words in a regular expression. The regex is made to
    check if a text has words that starts with any word in the list.

    Args:
        words: a list or tuple of strings,
    """
    return r'|'.join(
        [r"^{word}\.*|\.* {word}\.*".format(word=word) for word in words]
        )


def find_words(text, suspect_words, excluded_words=[]):
    """Check if a text has some of the suspect words (or words that starts with
    one of the suspect words). You can set some words to be excluded of the
    search, so you can remove false positives like 'important' be detected when
    you search by 'import'. It will return True if the number of suspect words
    found is greater than the number of excluded words. Otherwise, it will
    return False.

    Args:
        text (str): a string with the text to be analysed. It will be converted
            to lowercase.
        suspect_words: a list of strings that you want to check the presence in
            the text.
        excluded_words: a list of strings to be whitelisted.
    """
    text = text.lower()
    suspect_found = [i for i in re.finditer(make_regex(suspect_words), text)]
    if len(excluded_words) > 0:
        excluded_found = [
            i for i in re.finditer(make_regex(excluded_words), text)
            ]
        if len(suspect_found) > len(excluded_found):
            return True
        else:
            return False
    else:
        if len(suspect_found) > 0:
            return True
        else:
            return False


class ChangesetList(object):
    """Read replication changeset file and return a list with the XML data of
    each changeset. You can filter the changesets by passing a geojson file
    with a Polygon of your area of interest.
    """

    def __init__(self, changeset_file, geojson=None):
        """Read the changeset replication file, filter it you define a polygon
        with your area of interest in a geojson file and define the .changesets
        with the data of all changesets included in the replication file.

        Args:
            changeset_file (str): it can be the URL of a replication file in
                https://planet.openstreetmap.org/replication/changesets/ or the
                path to a local replication file.
            geojson (str): path to a local geojson file containing a polygon.
                The area of the polygon will be used to filter the changesets,
                returning only the ones that intersect with it.
        """
        self.read_file(changeset_file)
        if geojson:
            self.get_area(geojson)
            self.filter()
        else:
            self.content = self.xml
        self.changesets = [changeset_info(ch) for ch in self.content]

    def read_file(self, changeset_file):
        """Download the replication changeset file or read it directly from the
        filesystem (to test purposes).
        """
        if isfile(changeset_file):
            self.filename = changeset_file
        else:
            self.path = mkdtemp()
            self.filename = join(self.path, basename(changeset_file))
            download(changeset_file, self.path)

        self.xml = ET.fromstring(gzip.open(self.filename).read())

        # delete folder created to download the file
        if not isfile(changeset_file):
            rmtree(self.path)

    def get_area(self, geojson):
        """Read the first feature from the geojson and return it as a Polygon
        object.
        """
        geojson = json.load(open(geojson, 'r'))
        self.area = Polygon(
            geojson['features'][0]['geometry']['coordinates'][0]
            )

    def filter(self):
        """Filter the changesets that intersects with the geojson geometry."""
        self.content = [
            ch
            for ch in self.xml
            if get_bounds(ch).intersects(self.area)
            ]


class Analyse(object):
    """Analyse a changeset and define if it is suspect."""
    def __init__(self, changeset, create_threshold=200, modify_threshold=200,
            delete_threshold=30, percentage=0.7, top_threshold=1000,
            suspect_words=WORDS['common'] + WORDS['sources'],
            illegal_sources=WORDS['sources'], excluded_words=WORDS['exclude']):
        if type(changeset) in [int, str]:
            self.set_fields(changeset_info(get_metadata(changeset)))
        elif type(changeset) == dict:
            self.set_fields(changeset)
        else:
            raise InvalidChangesetError(
                """The changeset param needs to be a changeset id or a dict
                returned by the changeset_info function
                """
                )
        self.create_threshold = create_threshold
        self.modify_threshold = modify_threshold
        self.delete_threshold = delete_threshold
        self.percentage = percentage
        self.top_threshold = top_threshold
        self.excluded_words = excluded_words
        self.illegal_sources = illegal_sources
        self.suspect_words = suspect_words

    def set_fields(self, changeset):
        """Set the fields of this class with the metadata of the analysed
        changeset.
        """
        self.id = int(changeset.get('id'))
        self.user = changeset.get('user')
        self.uid = changeset.get('uid')
        self.editor = changeset.get('created_by', None)
        self.review_requested = changeset.get('review_requested', False)
        self.host = changeset.get('host', 'Not reported')
        self.bbox = changeset.get('bbox').wkt
        self.comment = changeset.get('comment', 'Not reported')
        self.source = changeset.get('source', 'Not reported')
        self.imagery_used = changeset.get('imagery_used', 'Not reported')
        self.date = datetime.strptime(
            changeset.get('created_at'),
            '%Y-%m-%dT%H:%M:%SZ'
            )
        self.suspicion_reasons = []
        self.is_suspect = False
        self.powerfull_editor = False
        self.warning_tags = [
            i for i in changeset.keys() if i.startswith('warnings:')
            ]
        self.metadata = {}
        # host key is a special case
        if changeset.get('host'):
            self.metadata['host'] = changeset.get('host')
        metadata_keys = [
            key for key in changeset.keys()
            if key not in self.__dict__.keys()
            and key not in MANDATORY_TAGS + ['created_by']
            and key not in FIELDS_TO_REMOVE
            ]
        for key in metadata_keys:
            try:
                self.metadata[key] = int(changeset.get(key))
            except ValueError:
                self.metadata[key] = changeset.get(key)

    def label_suspicious(self, reason):
        """Add suspicion reason and set the suspicious flag."""
        self.suspicion_reasons.append(reason)
        self.is_suspect = True

    def full_analysis(self):
        """Execute the count and verify_words methods."""
        self.count()
        self.verify_words()
        self.verify_user()
        self.verify_warning_tags()

        if self.review_requested == 'yes':
            self.label_suspicious('Review requested')

    def verify_warning_tags(self):
        w = Warnings()
        for item in [w.is_enabled(reason) for reason in self.warning_tags]:
            if item is not None:
                self.label_suspicious(item)

    def verify_user(self):
        """Verify if the changeset was made by a inexperienced mapper (anyone
        with less than 5 edits) or by a user that was blocked more than once.
        """
        user_reasons = get_user_details(self.uid)
        [self.label_suspicious(reason) for reason in user_reasons]

    def verify_words(self):
        """Verify the fields source, imagery_used and comment of the changeset
        for some suspect words.
        """
        if self.comment:
            if find_words(self.comment, self.suspect_words, self.excluded_words):
                self.label_suspicious('suspect_word')

        if self.source:
            for word in self.illegal_sources:
                if word in self.source.lower():
                    if word == 'yandex' and 'yandex panorama' in self.source.lower():
                        pass
                    else:
                        self.label_suspicious('suspect_word')
                        break

        if self.imagery_used:
            for word in self.illegal_sources:
                if word in self.imagery_used.lower():
                    self.label_suspicious('suspect_word')
                    break

        self.suspicion_reasons = list(set(self.suspicion_reasons))

    def verify_editor(self):
        """Verify if the software used in the changeset is a powerfull_editor.
        """
        powerful_editors = [
            'josm', 'level0', 'merkaartor', 'qgis', 'arcgis', 'upload.py',
            'osmapi', 'Services_OpenStreetMap'
            ]
        if self.editor is not None:
            for editor in powerful_editors:
                if editor in self.editor.lower():
                    self.powerfull_editor = True
                    break

            if 'iD' in self.editor:
                trusted_hosts = [
                    'www.openstreetmap.org',
                    'improveosm.org',
                    'strava.github.io',
                    'preview.ideditor.com',
                    'ideditor.netlify.app',
                    'hey.mapbox.com',
                    'projets.pavie.info',
                    'maps.mapcat.com',
                    'id.softek.ir',
                    'mapwith.ai',
                    'tasks.teachosm.org',
                    'tasks-stage.hotosm.org',
                    'tasks.hotosm.org',
                    ]
                if self.host.split('://')[-1].split('/')[0] not in trusted_hosts:
                    self.label_suspicious('Unknown iD instance')
        else:
            self.powerfull_editor = True
            self.label_suspicious('Software editor was not declared')

    def count(self):
        """Count the number of elements created, modified and deleted by the
        changeset and analyses if it is a possible import, mass modification or
        a mass deletion.
        """
        xml = get_changeset(self.id)
        actions = [action.tag for action in xml]
        self.create = actions.count('create')
        self.modify = actions.count('modify')
        self.delete = actions.count('delete')
        self.verify_editor()

        try:
            if (self.create / len(actions) > self.percentage and
                    self.create > self.create_threshold and
                    (self.powerfull_editor or self.create > self.top_threshold)):
                self.label_suspicious('possible import')
            elif (self.modify / len(actions) > self.percentage and
                    self.modify > self.modify_threshold):
                self.label_suspicious('mass modification')
            elif ((self.delete / len(actions) > self.percentage and
                    self.delete > self.delete_threshold) or
                    self.delete > self.top_threshold):
                self.label_suspicious('mass deletion')
        except ZeroDivisionError:
            print('It seems this changeset was redacted')

    def get_dict(self):
        ch_dict = self.__dict__.copy()
        for key in self.__dict__:
            if self.__dict__.get(key) == '':
                ch_dict.pop(key)

        for field in FIELDS_TO_REMOVE:
            ch_dict.pop(field)
        return ch_dict
