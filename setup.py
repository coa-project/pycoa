# -*- coding: utf-8 -*-

""" 
Project : PyCoA
Date :    april/november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License:  See joint LICENSE file

About : mandatory setup file
"""

from setuptools import setup, find_packages

pkg_vars  = {}
with open("coa/_version.py") as fp:
    exec(fp.read(), pkg_vars)

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='PyCoA',
    url='https://github.com/coa-project/pycoa',
    version=pkg_vars['__version__'],
    author=pkg_vars['__author__'],
    author_email=pkg_vars['__email__'],
    # Needed to actually package something
    packages=['coa'],
    # Needed for dependencies
    install_requires=[ \
        'altair',\
        'bokeh',\
        'branca',\
        #'collections',\   std
        #'copy',\  std
        'datetime',\
        'folium',\
        'geopandas',\
        'geopy',\
        #'itertools',\  std
        #'json',\  std
        #'math',\   std
        'matplotlib',\
        'numpy',\
        'pandas',\
        'pycountry',\
        'pycountry_convert',\
        'pyproj',\
        #'random',\   std
        'requests',\
        'scipy',\
        'shapely',\
        #'sys',\   std
        #'warnings',\  std
        ],
    # The license can be anything you like
    license='MIT',
    description='PyCoA stands for Python COvid19 Analysis project, which is an open source project initially designed to run in the Google colab environment. See pycoa.fr website.',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
)
