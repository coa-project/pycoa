#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april-december 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Tool : ./list_requires.py

About
-----
This small tool is for internal use in order to properly maintain the updated list of requires of the coa module.
"""

import os

stdlist=['base64','collections','getpass','inspect','io','itertools',\
        'json','math','os','PIL','random','sys','tempfile','time','urllib',\
        'warnings','zlib',\
        'coa']

for i in os.popen("cat coa/*.py | grep \"^from\|^import\" | awk '{print $2}' | awk -F. '{print $1}' | sort -u"):
    li=i.rstrip()
    if not li in stdlist:
        print("'"+li+"',\\")
