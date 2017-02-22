from codecs import open as codecs_open
from setuptools import setup, find_packages

import osmcha

# Get the long description from the relevant file
with codecs_open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(name='osmcha',
      version=osmcha.__version__,
      description="Python package to detect suspicious OpenStreetMap changesets",
      long_description=long_description,
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Topic :: Scientific/Engineering :: GIS',
          'Topic :: Utilities',
      ],
      keywords=['openstreetmap', 'osm', 'QA', 'gis'],
      author="Wille Marcel",
      author_email='wille@wille.blog.br',
      url='https://github.com/willemarcel/osmcha',
      license='GPLv3+',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click',
          'requests',
          'homura',
          'shapely',
          'python-dateutil',
          'PyYAML'
      ],
      extras_require={
          'test': ['pytest'],
      },
      entry_points="""
      [console_scripts]
      osmcha=osmcha.scripts.cli:cli
      """
      )
