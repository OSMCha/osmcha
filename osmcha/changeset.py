import requests
from homura import download

from os.path import basename, join, isfile
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


class ChangesetList(object):
    """Read replication changeset and return a list with information of all
    changesets.
    """

    def __init__(self, url):
        self.read_file(url)
        self.changesets = [changeset_info(ch) for ch in self.xml.getchildren()]

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