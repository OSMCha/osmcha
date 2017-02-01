import gzip
import json
from datetime import datetime
from os.path import basename, join, isfile
from shutil import rmtree
from tempfile import mkdtemp
import xml.etree.ElementTree as ET

import requests
from homura import download
from shapely.geometry import Polygon


class InvalidChangesetError(Exception):
    pass


def changeset_info(changeset):
    """Return a dictionary with id, user, user_id, bounds and date of creation
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
    """Get the changeset using OSM API and return the content as a XML
    ElementTree.
    """
    url = 'http://www.openstreetmap.org/api/0.6/changeset/{}/download'.format(
        changeset
        )
    return ET.fromstring(requests.get(url).content)


def get_metadata(changeset):
    """Get the metadata of the changeset using OSM API and return it as a XML
    ElementTree.
    """
    url = 'http://www.openstreetmap.org/api/0.6/changeset/{}'.format(changeset)
    return ET.fromstring(requests.get(url).content).getchildren()[0]


def get_bounds(changeset):
    """Get the bounds of the changeset and return it as a Polygon object. If
    the changeset has not coordinates (case of the changesets that deal only
    with relations), return a empty Polygon."""
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


class ChangesetList(object):
    """Read replication changeset file  and return a list with information about
    all changesets.
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
    def __init__(self, changeset):
        if type(changeset) in [int, str]:
            # self.set_fields(changeset_info(get_metadata(changeset)))
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

    def set_fields(self, changeset):
        """Set the fields of this class with the metadata of the analysed
        changeset.
        """
        self.id = int(changeset.get('id'))
        self.user = changeset.get('user')
        self.uid = changeset.get('uid')
        self.editor = changeset.get('created_by')
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
        """Execute count and verify_words functions."""
        self.count()
        self.verify_words()

    def verify_words(self):
        """Verify the fields source and comment of the changeset for some
        suspect words.
        """
        suspect_words = [
            'google',
            'nokia',
            ' here',
            'waze',
            'apple',
            'tomtom',
            'import',
            'wikimapia',
            ]

        if self.source:
            for word in suspect_words:
                if word in self.source.lower():
                    self.is_suspect = True
                    self.suspicion_reasons.append('suspect_word')
                    break

        if self.comment:
            for word in suspect_words:
                if word in self.comment.lower():
                    self.is_suspect = True
                    self.suspicion_reasons.append('suspect_word')
                    break

        if self.imagery_used:
            for word in suspect_words:
                if word in self.imagery_used.lower():
                    self.is_suspect = True
                    self.suspicion_reasons.append('suspect_word')
                    break

        self.suspicion_reasons = list(set(self.suspicion_reasons))

    def verify_editor(self):
        """Verify if the software used in the changeset is a powerfull_editor.
        """
        for editor in ['josm', 'level0', 'merkaartor', 'qgis', 'arcgis']:
            if editor in self.editor.lower():
                self.powerfull_editor = True
                break

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

        if (self.create / len(actions) > 0.7 and self.create > 200 and
                (self.powerfull_editor or self.create > 1000)):
            self.is_suspect = True
            self.suspicion_reasons.append('possible import')
        elif self.modify / len(actions) > 0.7 and self.modify > 200:
            self.is_suspect = True
            self.suspicion_reasons.append('mass modification')
        elif ((self.delete / len(actions) > 0.7 and self.delete > 30) or
                self.delete > 1000):
            self.is_suspect = True
            self.suspicion_reasons.append('mass deletion')
