# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - may 2022
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : coa.mpfront

About :
-------

This file is an alias of the coa.front file with default db being mpoxgh.
It should be used just like the coa.front file.
"""

import builtins
__builtins__["coa_db"] = 'mpoxgh'

from coa.front import *
import coa.front
