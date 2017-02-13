osmcha
============

OSM Changeset Analyser, ``osmcha``, a Python package to detect suspicious OSM changesets.
It was made to use with `osmcha-django <https://github.com/willemarcel/osmcha-django>`_,
but also can be used standalone or in other projects.

.. image:: https://travis-ci.org/willemarcel/osmcha.svg
    :target: https://travis-ci.org/willemarcel/osmcha

.. image:: https://coveralls.io/repos/willemarcel/osmcha/badge.svg
    :target: https://coveralls.io/r/willemarcel/osmcha


Installation
============

    pip install osmcha

Usage
=====

Python Library
--------------

You can read a `replication changeset file <https://planet.openstreetmap.org/replication/changesets/>`_
directly from the web:

.. code-block:: python

  c = ChangesetList('https://planet.openstreetmap.org/replication/changesets/002/236/374.osm.gz')

or from your local filesystem.

.. code-block:: python

  c = ChangesetList('tests/245.osm.gz')


``c.changesets`` will return a list containing data of all the changesets listed in the file.

You can filter the changesets passing a `GeoJSON` file with a polygon with your interest area to `ChangesetList` as the second argument.

Finally, to analyse an especific changeset, do:

.. code-block:: python

  ch = Analyse(changeset_id)
  ch.full_analysis()

Command Line Interface
----------------------

The command line interface can be used to verify an especific changeset directly
from the terminal.

Usage: ``osmcha <changeset_id>``


Tests
======

To run the tests on `osmcha`:

.. code-block:: console

  git clone https://github.com/willemarcel/osmcha.git
  cd osmcha
  pip install -e .[test]
  py.test -v


License
=======

GPLv3
