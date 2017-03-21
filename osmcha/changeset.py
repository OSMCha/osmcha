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
WORDS = yaml.load(open(SUSPECT_WORDS_FILE, 'r').read())
OSM_USERS_API = environ.get(
    'OSM_USERS_API',
    'https://osm-comments-api.mapbox.com/api/v1/users/name/{username}'
    )


class InvalidChangesetError(Exception):
    pass


def changeset_info(changeset):
    """Return a dictionary with id, user, user_id, bounds, date of creation
    and all the tags of the changeset.
    """
    keys = [tag.attrib.get('k') for tag in changeset.getchildren()]
    keys += ['id', 'user', 'uid', 'bbox', 'created_at']
    values = [tag.attrib.get('v') for tag in changeset.getchildren()]
    values += [
        changeset.get('id'), changeset.get('user'), changeset.get('uid'),
        get_bounds(changeset), changeset.get('created_at')
        ]

    return dict(zip(keys, values))


def get_changeset(changeset):
    """Get the changeset using the OSM API and return the content as a XML
    ElementTree.
    """
    url = 'http://www.openstreetmap.org/api/0.6/changeset/{}/download'.format(
        changeset
        )
    return ET.fromstring(requests.get(url).content)


def get_metadata(changeset):
    """Get the metadata of a changeset using the OSM API and return it as a XML
    ElementTree.
    """
    url = 'http://www.openstreetmap.org/api/0.6/changeset/{}'.format(changeset)
    return ET.fromstring(requests.get(url).content).getchildren()[0]


def get_bounds(changeset):
    """Get the bounds of the changeset and return it as a Polygon object. If
    the changeset has not coordinates (case of the changesets that deal only
    with relations), it returns an empty Polygon."""
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
    """Concatenate a list of words in a regular expression that detects any
    word that starts with some of the words in a text.
    """
    return r'|'.join(
        ["^{word}\.*|\.* {word}\.*".format(word=word) for word in words]
        )


def find_words(text, suspect_words, excluded_words=[]):
    """Check if a text has some of the suspect words (or words that starts with
    one of the suspect words). You can set words to be excluded of the search,
    so you can remove false positives like 'important' be detected when you
    search by 'import'. Return True if the number of suspect words found is
    greater than the number of excluded words.
    """
    text = text.lower()
    suspect_found = [i for i in re.finditer(make_regex(suspect_words), text)]
    if len(excluded_words) > 0:
        excluded_found = [i for i in re.finditer(make_regex(excluded_words), text)]
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
    each changeset. You can filter the changesets by passing a geojson file with
    a Polygon of your area of interest.
    """

    def __init__(self, changeset_file, geojson=None):
        self.read_file(changeset_file)
        if geojson:
            self.get_area(geojson)
            self.filter()
        else:
            self.content = self.xml.getchildren()
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
        self.area = Polygon(geojson['features'][0]['geometry']['coordinates'][0])

    def filter(self):
        """Filter the changesets that intersects with the geojson geometry."""
        self.content = [
            ch
            for ch in self.xml.getchildren()
            if get_bounds(ch).intersects(self.area)
            ]


class Analyse(object):
    """Analyse a changeset and define if it is suspect."""
    def __init__(self, changeset, create_threshold=200, modify_threshold=200,
            delete_threshold=30, percentage=0.7, top_threshold=1000,
            suspect_words=WORDS['common'] + WORDS['sources'],
            illegal_sources=WORDS['sources'], excluded_words=WORDS['exclude']):
        if type(changeset) in [int, str]:
            changeset_details = changeset_info(get_metadata(changeset))
            self.set_fields(changeset_details)
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

    def full_analysis(self):
        """Execute the count and verify_words methods."""
        self.count()
        self.verify_words()
        self.changeset_by_new_mapper()

    def changeset_by_new_mapper(self):
        reason = 'New mapper'

        try:
            # Convert username to ASCII and quote any special characters.
            url = OSM_USERS_API.format(
                username=requests.compat.quote(self.user)
                )
            print(url)
            user_details = json.loads(requests.get(url).content)
        except Exception as e:
            print(
                'changeset_by_new_mapper failed for: {}, {}'.format(self.id, str(e))
                )
        else:
            if user_details['changeset_count'] <= 5:
                self.suspicion_reasons.append(reason)
                self.is_suspect = True

    def verify_words(self):
        """Verify the fields source, imagery_used and comment of the changeset
        for some suspect words.
        """

        if self.comment:
            if find_words(self.comment, self.suspect_words, self.excluded_words):
                self.is_suspect = True
                self.suspicion_reasons.append('suspect_word')

        if self.source:
            for word in self.illegal_sources:
                if word in self.source.lower():
                    self.is_suspect = True
                    self.suspicion_reasons.append('suspect_word')
                    break

        if self.imagery_used:
            for word in self.illegal_sources:
                if word in self.imagery_used.lower():
                    self.is_suspect = True
                    self.suspicion_reasons.append('suspect_word')
                    break

        self.suspicion_reasons = list(set(self.suspicion_reasons))

    def verify_editor(self):
        """Verify if the software used in the changeset is a powerfull_editor.
        """
        if self.editor is not None:
            for editor in ['josm', 'level0', 'merkaartor', 'qgis', 'arcgis']:
                if editor in self.editor.lower():
                    self.powerfull_editor = True
                    break

            if 'iD' in self.editor:
                trusted_hosts = [
                    'http://www.openstreetmap.org/id',
                    'https://www.openstreetmap.org/id',
                    'http://improveosm.org/',
                    'https://strava.github.io/iD/'
                    ]
                if self.host not in trusted_hosts:
                    self.is_suspect = True
                    self.suspicion_reasons.append('Unknown iD instance')
        else:
            self.is_suspect = True
            self.powerfull_editor = True
            self.suspicion_reasons.append('Software editor was not declared')

    def count(self):
        """Count the number of elements created, modified and deleted by the
        changeset and analyses if it is a possible import, mass modification or
        a mass deletion.
        """
        xml = get_changeset(self.id)
        actions = [action.tag for action in xml.getchildren()]
        self.create = actions.count('create')
        self.modify = actions.count('modify')
        self.delete = actions.count('delete')
        self.verify_editor()

        try:
            if (self.create / len(actions) > self.percentage and
                    self.create > self.create_threshold and
                    (self.powerfull_editor or self.create > self.top_threshold)):
                self.is_suspect = True
                self.suspicion_reasons.append('possible import')
            elif (self.modify / len(actions) > self.percentage and
                    self.modify > self.modify_threshold):
                self.is_suspect = True
                self.suspicion_reasons.append('mass modification')
            elif ((self.delete / len(actions) > self.percentage and
                    self.delete > self.delete_threshold) or
                    self.delete > self.top_threshold):
                self.is_suspect = True
                self.suspicion_reasons.append('mass deletion')
        except ZeroDivisionError:
            print('It seems this changeset was redacted')

    def get_dict(self):
        ch_dict = self.__dict__.copy()
        for key in self.__dict__:
            if self.__dict__.get(key) == '':
                ch_dict.pop(key)

        fields_to_remove = [
            'create_threshold', 'modify_threshold', 'illegal_sources',
            'delete_threshold', 'percentage', 'top_threshold', 'suspect_words',
            'excluded_words', 'host'
            ]
        for field in fields_to_remove:
            ch_dict.pop(field)
        return ch_dict
