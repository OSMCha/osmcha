import requests

import xml.etree.ElementTree as ET


class ChangesetDownload(object):
    """Class to Download OSM Changesets"""

    def __init__(self, start, end):

        self.url = 'https://api.openstreetmap.org/api/0.6/changesets/?' + \
            'bbox=-73.9830625,-33.8689056,0.0,5.2842873&' + \
            'time=%s,%s&closed=true' % (start, end)
        self.download = requests.get(self.url)
        self.xml = ET.fromstring(self.download.content)
        self.changesets = [changeset.get('uid') for changeset in self.xml.getchildren()]

    def get_changeset(self, changeset):
        url = 'http://www.openstreetmap.org/api/0.6/changeset/%s/download' % changeset
        return ET.fromstring(requests.get(url).content)


