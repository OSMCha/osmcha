import requests
from homura import download
from shapely.geometry import Polygon

from os.path import basename, join, isfile
from datetime import datetime
from tempfile import mkdtemp
import gzip
import xml.etree.ElementTree as ET
import json
from shutil import rmtree
import dateutil.parser


class InvalidChangesetError(Exception):
    pass


def changeset_info(changeset):
    """Return a dictionary with id, user, user_id, bounds and date of creation
    and all the tags of the changeset.
    """
    keys = [tag.attrib.get('k') for tag in changeset.getchildren()]
    keys += ['id', 'user', 'uid', 'bbox', 'created_at']
    values = [tag.attrib.get('v') for tag in changeset.getchildren()]
    values += [changeset.get('id'), changeset.get('user'), changeset.get('uid'),
        get_bounds(changeset), changeset.get('created_at')]

    return dict(zip(keys, values))


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


def get_user_details(user):
    """Takes a user's name as input and returns user details as a dictionary.

    API used: http://hdyc.neis-one.org/
    """
    ## TODO: This is a hack. We need to think through this scenario well.
    try:
        url = 'http://hdyc.neis-one.org/user/%s' % user
        user_details = json.loads(requests.get(url).content)
        print 'user_details: ' + json.dumps(user_details)
        print "user_details['changesets']': " + str(user_details['changesets'])

        return {
            'contributor_uid': int(user_details['contributor']['uid']),
            'contributor_name': user_details['contributor']['name'],
            'contributor_blocks': int(user_details['contributor']['blocks']),
            'contributor_since': dateutil.parser.parse(user_details['contributor']['since']),
            'contributor_traces': int(user_details['contributor']['traces']),
            'contributor_img': user_details['contributor'].get('img', None),

            'nodes_c': int(user_details['nodes']['c']),
            'nodes_m': int(user_details['nodes']['m']),
            'nodes_d': int(user_details['nodes']['d']),
            'nodes_rank': int(user_details['nodes']['r']),

            'ways_c': int(user_details['ways']['c']),
            'ways_m': int(user_details['ways']['m']),
            'ways_d': int(user_details['ways']['d']),
            'ways_rank': int(user_details['ways']['r']),

            'relations_c': int(user_details['relations']['c']),
            'relations_m': int(user_details['relations']['m']),
            'relations_d': int(user_details['relations']['d']),
            'relations_rank': int(user_details['relations']['r']),

            'notes_opened': int(user_details['notes']['op']),
            'notes_commented': int(user_details['notes']['co']),
            'notes_closed': int(user_details['notes']['cl']),

            'changesets_no': int(user_details['changesets']['no']) if user_details['changesets'].has_key('no') else None,
            'changesets_changes': int(user_details['changesets']['changes']) if user_details['changesets'].has_key('changes') else None,
            'changesets_f_tstamp': dateutil.parser.parse(user_details['changesets']['f_tstamp']) if user_details['changesets'].has_key('f_tstamp') else None,
            'changesets_l_tstamp': dateutil.parser.parse(user_details['changesets']['l_tstamp']) if user_details['changesets'].has_key('l_tstamp') else None,
            'changesets_mapping_days': user_details['changesets']['mapping_days'] if user_details['changesets'].has_key('mapping_days') else None,  # Format: 2012=6;2013=9;2014=4
        }
    except Exception:
        return dict()

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
            ch for ch in self.xml.getchildren() if get_bounds(ch).intersects(self.area)
        ]


class Analyse(object):
    """Analyse a changeset and define if it is suspect."""
    def __init__(self, changeset):
        if type(changeset) in [int, str]:
            # self.set_fields(changeset_info(get_metadata(changeset)))
            changeset_details = changeset_info(get_metadata(changeset))
            user = changeset_details['user']
            changeset_details['user_details'] = get_user_details(user)
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
        self.user_score = 0
        self.changeset_score = 0
        self.uid = changeset.get('uid')
        self.editor = changeset.get('created_by')
        self.bbox = changeset.get('bbox').wkt
        self.comment = changeset.get('comment', 'Not reported')
        self.source = changeset.get('source', 'Not reported')
        self.imagery_used = changeset.get('imagery_used', 'Not reported')
        self.date = datetime.strptime(changeset.get('created_at'), '%Y-%m-%dT%H:%M:%SZ')
        self.suspicion_reasons = []
        self.is_suspect = False
        self.powerfull_editor = False
        self.user_details = changeset.get('user_details')

    def full_analysis(self):
        """Execute count and verify_words functions."""
        self.count()
        self.calc_user_score()
        self.calc_changeset_score()
        self.verify_words()

    def calc_user_score(self):
        user_details = self.user_details
        if not user_details:
            return
        if user_details['contributor_blocks'] > 0:
            self.user_score = self.user_score - (user_details['contributor_blocks'] * 500)
        if user_details['contributor_img']:
            self.user_score = self.user_score + 50
        else:
            self.user_score = self.user_score - 25
        if user_details['contributor_traces'] and user_details['contributor_traces'] > 0:
            self.user_score = self.user_score + 25
        mapping_days = self.get_mapping_days()
        if mapping_days <= 10:
            self.user_score = self.user_score - 25
        if mapping_days > 200:
            self.user_score = self.user_score + 25
        if user_details['changesets_changes'] > 10000:
            self.user_score = self.user_score + 50
        if user_details['notes_opened'] > 50:
            self.user_score = self.user_score + 50
        if user_details['notes_commented'] > 10:
            self.user_score = self.user_score + 50
        if user_details['notes_closed'] > 10:
            self.user_score = self.user_score + 50
        if user_details['nodes_rank'] < 5000:
            self.user_score = self.user_score + 50
        if user_details['ways_rank'] < 5000:
            self.user_score = self.user_score + 50
        if user_details['relations_rank'] < 5000:
            self.user_score = self.user_score + 50
        return

    def get_mapping_days(self):
        mapping_days_string = self.user_details['changesets_mapping_days']
        years = mapping_days_string.split(';')
        total_days = 0
        for year in years:
            days = int(year.split('=')[1])
            total_days = total_days + days
        return total_days

    def calc_changeset_score(self):
        total_changes = self.create + self.modify + self.delete
        if total_changes > 3000:
            self.changeset_score = self.changeset_score - 100
        if self.delete > 200 and self.create == 0 and self.modify == 0:
            self.changeset_score = self.changeset_score - 50
        is_whitelisted_editor = self.is_whitelisted_editor()
        if not is_whitelisted_editor:
            self.changeset_score = self.changeset_score - 100
        if self.comment == '' or self.comment == 'Not reported':
            self.changeset_score = self.changeset_score - 50
        if 'google' in self.imagery_used.lower():
            self.changeset_score = self.changeset_score - 100
        if 'google' in self.source.lower():
            self.changeset_score = self.changeset_score - 100
        return

    def is_whitelisted_editor(self):
        whitelist = ['josm', 'id', 'portlatch', 'vespucci']
        if self.editor is None:
            return False
        editor_lower = self.editor.lower()
        is_whitelisted = False
        for w in whitelist:
            if w in editor_lower:
                is_whitelisted = True
        return is_whitelisted


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

        if self.create / len(actions) > 0.7 and \
            self.create > 200 and \
            (self.powerfull_editor or self.create > 1000):
            self.is_suspect = True
            self.suspicion_reasons.append('possible import')
        elif self.modify / len(actions) > 0.7 and self.modify > 200:
            self.is_suspect = True
            self.suspicion_reasons.append('mass modification')
        elif (self.delete / len(actions) > 0.7 and self.delete > 30) or \
            self.delete > 1000:
            self.is_suspect = True
            self.suspicion_reasons.append('mass deletion')
