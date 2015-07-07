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
    keys += ['id', 'user']
    values = [tag.attrib.get('v') for tag in changeset.getchildren()]
    values += [changeset.get('id'), changeset.get('user')]

    return dict(zip(keys, values))


def get_bounds(changeset):
    return MultiPoint([
        (float(changeset.get('min_lon')), float(changeset.get('min_lat'))),
        (float(changeset.get('max_lon')), float(changeset.get('max_lat')))
    ])


def get_changeset(changeset):
    url = 'http://www.openstreetmap.org/api/0.6/changeset/%s/download' % changeset
    return ET.fromstring(requests.get(url).content)


class ChangesetList(object):
    """Read replication changeset and return a list with information of all
    changesets.
    """

    def __init__(self, url, geojson=None):
        self.read_file(url)
        if geojson:
            self.get_area(geojson)
            self.filter()
        else:
            self.content = self.xml.getchildren()
        self.changesets = [changeset_info(ch) for ch in self.content]

    def read_file(self, url):
        """Download the replicate_changeset file or read it directly from the
        filesystem (to test purposes)."""
        if isfile(url):
            self.filename = url
        else:
            self.path = mkdtemp()
            self.filename = join(self.path, basename(url))
            download(url, self.path)

        self.xml = ET.fromstring(gzip.open(self.filename).read())

    def get_area(self, geojson):
        geojson = json.load(open(geojson, 'r'))
        self.area = Polygon(geojson['features'][0]['geometry']['coordinates'][0])

    def filter(self):
        self.content = [ch for ch in self.xml.getchildren() if get_bounds(ch).intersects(self.area)]