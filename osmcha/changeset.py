import requests
from homura import download

from os.path import basename, join
from tempfile import mkdtemp
import gzip
import xml.etree.ElementTree as ET


def changeset_info(changeset):
    """Return a dictionary with the id and all the tags of the changeset."""
    keys = [tag.attrib.get('k') for tag in changeset.getchildren()]
    keys += ['id', 'user']
    values = [tag.attrib.get('v') for tag in changeset.getchildren()]
    values += [changeset.get('id'), changeset.get('user')]

    return dict(zip(keys, values))


def get_changeset(changeset):
    url = 'http://www.openstreetmap.org/api/0.6/changeset/%s/download' % changeset
    return ET.fromstring(requests.get(url).content)


class ChangesetQuery(object):
    """Class to Download OSM Changesets"""

    def __init__(self, bbox, start, end):
        """
        @params
        bbox - tuple containing the coordinates in the following order: left,bottom,right,top
        start - start date of the query in the format 20150427T000000
        end - end date of the query in the same format of start
        """

        self.url = 'https://api.openstreetmap.org/api/0.6/changesets/?' + \
            'bbox=%s,%s,%s,%s&' % bbox + \
            'time=%s,%s&closed=true' % (start, end)
        self.download = requests.get(self.url)
        self.xml = ET.fromstring(self.download.content)
        self.changesets = [changeset_info(changeset) for changeset in self.xml.getchildren()]



class ChangesetList(object):

    def __init__(self, url):
        self.path = mkdtemp()
        self.filename = join(self.path, basename(url))
        download(url, self.path)
        self.xml = ET.fromstring(gzip.open(self.filename).read())
        self.changesets = [changeset_info(changeset) for changeset in self.xml.getchildren()]




