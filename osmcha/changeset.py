import requests
from homura import download
from shapely.geometry import Polygon, MultiPoint

from os.path import basename, join, isfile
from tempfile import mkdtemp
import gzip
import xml.etree.ElementTree as ET
import json


def changeset_info(changeset):
    """Return a dictionary with the id and all the tags of the changeset."""
    keys = [tag.attrib.get('k') for tag in changeset.getchildren()]
    keys += ['id', 'user', 'bounds']
    values = [tag.attrib.get('v') for tag in changeset.getchildren()]
    values += [changeset.get('id'), changeset.get('user'), get_bounds(changeset)]

    return dict(zip(keys, values))


def get_bounds(changeset):
    """Get the bounds of the changeset and return it as a MultiPoint object."""
    return MultiPoint([
        (float(changeset.get('min_lon')), float(changeset.get('min_lat'))),
        (float(changeset.get('max_lon')), float(changeset.get('max_lat')))
    ])


def get_changeset(changeset):
    """Get the changeset using OSM API and return the content as a XML
    ElementTree.
    """
    url = 'http://www.openstreetmap.org/api/0.6/changeset/%s/download' % changeset
    return ET.fromstring(requests.get(url).content)


def get_metadata(changeset):
    """Get the metadata of the changeset using OSM API and return it as a XML
    ElementTree.
    """
    url = 'http://www.openstreetmap.org/api/0.6/changeset/%s' % changeset
    return ET.fromstring(requests.get(url).content).getchildren()[0]


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

    def get_area(self, geojson):
        """Read the first feature from the geojson and return it as a Polygon
        object.
        """
        geojson = json.load(open(geojson, 'r'))
        self.area = Polygon(geojson['features'][0]['geometry']['coordinates'][0])

    def filter(self):
        """Filter the changesets """
        self.content = [
            ch for ch in self.xml.getchildren() if get_bounds(ch).intersects(self.area)
        ]


class Analyse(object):
    """Analyse a changeset and define if it is suspect."""
    def __init__(self, changeset):
        self.changeset = changeset
        self.reasons = []
        self.is_suspect = False
        self.verify_words()

    def verify_words(self):
        """Verify the fields source and comment of the changeset for some
        suspect words.
        """
        suspect_words = [
            'google',
            'nokia',
            'here',
            'waze',
            'apple',
            'tomtom',
            'import'
        ]

        if 'source' in self.changeset.keys():
            for word in suspect_words:
                if word in self.changeset.get('source').lower():
                    self.is_suspect = True
                    self.reasons.append('suspect_word')
                    break

        if 'comment' in self.changeset.keys():
            for word in suspect_words:
                if word in self.changeset.get('comment').lower():
                    self.is_suspect = True
                    self.reasons.append('suspect_word')
                    break

    def count(self):
        """Count the number of elements created, modified and deleted by the
        changeset.
        """
        xml = get_changeset(self.changeset.get('id'))
        actions = [action.tag for action in xml.getchildren()]
        return {
            'create': actions.count('create'),
            'modify': actions.count('modify'),
            'delete': actions.count('delete')
        }

