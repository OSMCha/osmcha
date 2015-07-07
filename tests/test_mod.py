from osmcha.changeset import ChangesetList


#def test_query():
    #d = ChangesetQuery((-73.9830625, -33.8689056, 0.0, 5.2842873),
        #'20150427T000000', '20150427T000400')
    #assert d.url == 'https://api.openstreetmap.org/api/0.6/changesets/' + \
        #'?bbox=-73.9830625,-33.8689056,0.0,5.2842873&' + \
        #'time=20150427T000000,20150427T000400&closed=true'
    #assert d.download.status_code == 200
    #assert len(d.changesets) == 26
    #assert d.changesets[0]['id'] == '30521534'
    #assert d.changesets[0]['user'] == 'Voliva'
    #assert d.changesets[0]['created_by'] == 'Potlatch 2'
    #assert d.changesets[0]['comment'] == 'ajustando'


def test_changeset_list():
    c = ChangesetList('http://planet.openstreetmap.org/replication/changesets/001/361/245.osm.gz')
    c.changesets[0]['id'] = '31982803'