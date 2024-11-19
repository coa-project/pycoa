# -*- coding: utf-8 -*-

"""
Project : pyvoa
Date :    april 2020 - november 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa.fr
License:  See joint LICENSE file

About : mandatory setup file
"""
from setuptools import setup, find_packages

# For reading requirements.txt
def read_requirements(file_path):
    with open(file_path) as f:
        return f.read().splitlines()

setup(
    name="pyvoa",
    version="3.0.1",
    description="Une courte description de votre programme.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Votre Nom",
    author_email="votre.email@example.com",
    url="https://github.com/to_be_defined",
    license="MIT",
    packages=find_packages(),
    install_requires=read_requirements("requirements.txt"),  #
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)


