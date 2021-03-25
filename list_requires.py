#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - march 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Tool : ./list_requires.py

About
-----
This small tool is for internal use in order to properly maintain the updated list of requires of the coa module.
"""

import os

stdlist=['base64','collections','functools','getpass','inspect','io','itertools','importlib',\
        'json','math','os','PIL','random','sys','tempfile','time','urllib',\
        'warnings','zlib',\
        'coa']

byhandlist=['lxml']
extractedlist=list(os.popen("cat coa/*.py | grep \"^from\|^import\" | awk '{print $2}' | awk -F. '{print $1}' | sort -u"))

for i in extractedlist + byhandlist:
    li=i.rstrip()
    if not li in stdlist:
        print("'"+li+"',\\")


