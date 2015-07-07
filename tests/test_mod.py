from osmcha.changeset import ChangesetList


def test_changeset_list():
    c = ChangesetList('tests/245.osm.gz')
    assert c.changesets[0]['id'] == '31982803'
    assert c.changesets[0]['created_by'] == 'Potlatch 2'
    assert c.changesets[0]['user'] == 'GarrettB'
    assert c.changesets[0]['comment'] == 'Added Emerald Pool Waterfall'