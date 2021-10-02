# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - march 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : coa.ffront

About :
-------

This file is an alias of the coa.front file with default db being spf.
It should be used just like the coa.front file.
"""

import builtins
__builtins__["coa_db"] = 'spf'

from coa.front import *
import coa.front
