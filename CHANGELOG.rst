Change Log
==========

[0.4.4] - 2017-10-10

- Add mapcat as a trusted host

[0.4.3] - 2017-09-15

- Add yandex and 2gis as suspect sources

[0.4.2] - 2017-08-29

- Add 'hey.mapbox.com/iD-internal/' and 'projets.pavie.info/id-indoor/' to the trusted hosts

[0.4.1] - 2017-08-17

- Flag changesets with the tag 'review_requested=yes'
- Add preview.ideditor.com to trusted hosts

[0.4.0] - 2017-07-28

- Flag changesets whose user has been blocked more than once
- add 'upload.py', 'osmapi' and 'Services_OpenStreetMap' to the list of powerful editors
- uses label_suspicious method to flag a changeset as suspicious

[0.3.9] - 2017-07-14
--------------------

- Add http://strava.github.io/iD/ as a trusted host.
- Remove 'fix' from suspect_words list

[0.3.8] - 2017-05-10
--------------------

- Add https://www.openstreetmap.org/edit as a trusted host.

[0.3.7] - 2017-04-18
--------------------

- Remove area field and calculate the area in django when saving a changeset.

[0.3.6] - 2017-04-18
--------------------

- Add area field to changeset Analyse class.
- Flag changes with "test" in comment

[0.3.5] - 2017-03-24
--------------------

- Set the changeset as a new mapper edit if the request to the users API fails
- Improvements on documentation

[0.3.4] - 2017-03-22
--------------------

- Fix bugs of the last version in Python 3.4 and 3.5

[0.3.3] - 2017-03-21
--------------------

- Mark changesets made by users that has less than 5 changesets as suspicious

[0.3.2] - 2017-03-17
--------------------

- Analyse changesets without any tags and mark it as suspicious

[0.3.1] - 2017-02-23
--------------------

- Include ``suspect_words.yaml`` in pypi package

[0.3] - 2017-02-22
--------------------

- Improve README and add detection rules information
- load suspect words from yaml file and make it customizable
- avoid errors in python 2 by importing unicode_literals
- add 'geofiction' in suspect words list
- examine 'host' field in edits made in iD
- add ``get_dict()`` method in Analyse class

[0.2] - 2017-02-13
--------------------

- First version that was published on Pypi
- Merge many contributions from Mapbox
- New suspect words and improvements in the examination
- Makes Analyse class configurable
- Handle redacted changesets

[0.1] - 2015-12-23
--------------------

- Initial version, this was not published on Pypi, but it is `tagged in Github<https://github.com/willemarcel/osmcha/commits/v0.2>`_
