import requests

import xml.etree.ElementTree as ET


class ChangesetDownload(object):
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
        self.changesets = [self.get_id_editor(changeset) for changeset in self.xml.getchildren()]

    def get_id_editor(self, changeset):
        editor = ''
        for tag in changeset.getchildren():
            if tag.attrib.get('k') == 'created_by':
                editor = tag.attrib.get('v')

        return [changeset.get('id'), editor]

    def get_changeset(self, changeset):
        url = 'http://www.openstreetmap.org/api/0.6/changeset/%s/download' % changeset
        return ET.fromstring(requests.get(url).content)


