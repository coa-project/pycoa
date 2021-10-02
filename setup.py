# -*- coding: utf-8 -*-

""" 
Project : PyCoA
Date :    april 2020 - march 2021
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
        'bisect'
        'bokeh',\
        'branca',\
        'bs4',\
        'datascroller',\
        'datetime',\
        'folium ~=0.12.1',\
        'geopandas',\
        'matplotlib',\
        'numpy',\
        'pandas',\
        'pycountry',\
        'pycountry_convert',\
        'requests',\
        'scipy',\
        'shapely',\
        'pytest >=5.0',\
        'pandas-flavor',\
        'openpyxl',\
        'unidecode',\
        ],
    # The license can be anything you like
    license='MIT',
    description='PyCoA stands for Python COvid19 Analysis project, which is an open source project initially designed to run in the Google colab environment. See pycoa.fr website.',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
)
