osmcha
=======

OSM Changeset Analyser, ``osmcha``, is a Python package to detect suspicious OSM changesets.
It was designed to be used with `osmcha-django <https://github.com/osmcha/osmcha-django>`_,
but also can be used standalone or in other projects.

You can report issues or request new features in the the
`osmcha-frontend repository <https://github.com/osmcha/osmcha-frontend>`_.

.. image:: https://badge.fury.io/py/osmcha.svg
    :target: http://badge.fury.io/py/osmcha

.. image:: https://coveralls.io/repos/OSMCha/osmcha/badge.svg
    :target: https://coveralls.io/r/willemarcel/osmcha

.. image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
    :target: CODE_OF_CONDUCT.md

Installation
============

.. code-block:: console

    pip install osmcha

Usage
=====

Python Library
--------------

You can read a `replication changeset file <https://planet.openstreetmap.org/replication/changesets/>`_
directly from the web:

.. code-block:: python

  from osmcha.changeset import ChangesetList
  c = ChangesetList('https://planet.openstreetmap.org/replication/changesets/002/236/374.osm.gz')

or from your local filesystem.

.. code-block:: python

  c = ChangesetList('tests/245.osm.gz')


``c.changesets`` will return a list containing data of all the changesets listed in the file.

You can filter the changesets passing a `GeoJSON` file with a polygon with your
interest area to `ChangesetList` as the second argument.

Finally, to analyse an especific changeset, do:

.. code-block:: python

  from osmcha.changeset import Analyse
  ch = Analyse(changeset_id)
  ch.full_analysis()

Customizing Detection Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can customize the detection rules by defining your prefered values when
initializing the ``Analyze`` class. See below the default values.

.. code-block:: python

  ch = Analyse(changeset_id, create_threshold=200, modify_threshold=200,
    delete_threshold=30, percentage=0.7, top_threshold=1000,
    suspect_words=[...], illegal_sources=[...], excluded_words=[...])

Command Line Interface
----------------------

The command line interface can be used to verify an especific changeset directly
from the terminal.

Usage: ``osmcha <changeset_id>``

Detection Rules
===============

``osmcha`` works by analysing how many map features the changeset created, modified
or deleted, and by verifying the presence of some suspect words in the ``comment``,
``source`` and ``imagery_used`` fields of the changeset. Furthermore, we also
consider if the software editor used allows to import data or to do mass edits.
We consider ``powerfull editors``: JOSM, Merkaartor, level0, QGIS and ArcGis.

In the ``Usage`` section, you can see how to customize some of these detection rules.

Possible Import
---------------

We tag a changeset as a ``possible import`` if the number of created elements is
greater than 70% of the sum of elements created, modified and deleted and if it
creates more than 1000 elements or 200 elements case it used one of the ``powerfull editors``.

Mass Modification
-----------------

We consider a changeset as a ``mass modification`` if the number of modified elements
is greater than 70% of the sum of elements created, modified and deleted and if it
modifies more than 200 elements.

Mass Deletion
-------------

All changesets that delete more than 1000 elements are considered a ``mass deletion``.
If the changeset deletes between 200 and 1000 elements and the number of deleted
elements is greater than 70% of the sum of elements created, modified and deleted
it's also tagged as a ``mass deletion``.

Suspect words
-------------

The suspect words are loaded from a `yaml file <osmcha/suspect_words.yaml>`_.
You can customize the words by setting another default file with a environment
variable:

.. code-block:: console

  export SUSPECT_WORDS=<path_to_the_file>

or pass a list of words to the ``Analyse`` class, more information on the section
``Customizing Detection Rules``. We use a list of illegal sources to analyse the
``source`` and ``imagery_used`` fields and another more general list to examine
the comment field. We have also a list of excluded words to avoid false positives.


New mapper
-----------

Verify if the user has less than 50 changesets.


User has multiple blocks
------------------------

Changesets created by users that has received more than one block will be
flagged.

OSM Server Configuration
------------------------

If you need to use OSMCha with another OSM server instance, you need to configure the OSM_SERVER_URL environment variable, without trailing slash. Example:

.. code-block:: console

  export OSM_SERVER_URL='https://www.openhistoricalmap.org'

Tests
======

To run the tests on `osmcha`:

.. code-block:: console

  git clone https://github.com/osmcha/osmcha.git
  cd osmcha
  pip install -e .[test]
  py.test -v

Publishing a new version
=========================

Update the version number in ``osmcha/__init__.py`` and execute
the following commands:

.. code-block:: console

  python setup.py bdist_wheel
  twine upload dist/osmcha-{version}...

Changelog
=========

Check `CHANGELOG <CHANGELOG.rst>`_ for the version history.

Related projects
================

* `osmcha-django <https://github.com/osmcha/osmcha-django>`_ - backend and API
* `osmcha-frontend <https://github.com/osmcha/osmcha-frontend>`_ - frontend of the `OSMCha <https://osmcha.org>`_ application
* `osm-compare <https://github.com/mapbox/osm-compare>`_ - library that analyse OSM features to input it to OSMCha

License
=======

GPLv3
