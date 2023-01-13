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
        'bokeh==2.4.0',\
        'branca==0.4.2',\
        'bs4==0.0.1',\
        'datascroller==1.4.1',\
        'datetime==4.3',\
        'folium==0.12.1',\
        'geopandas==0.10.2',\
        'matplotlib==3.6.2 ',\
        'numpy==1.22.3',\
        'pandas==1.4.2',\
        'pycountry==20.7.3',\
        'pycountry_convert==0.7.2',\
        'requests==2.25.1',\
        'scipy==1.7.0',\
        'shapely==1.7.1',\
        'pytest==6.2.4',\
        'pandas-flavor==0.3.0',\
        'openpyxl==3.0.9',\
        'unidecode==1.3.2',\
        'openpyxl==3.0.9',\
        ],
    dependency_links=['git+https://github.com/Toblerity/Fiona.git'],
    # The license can be anything you like
    license='MIT',
    description='PyCoA stands for Python COvid19 Analysis project, which is an open source project initially designed to run in the Google colab environment. See pycoa.fr website.',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
)
