Change Log
==========

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
