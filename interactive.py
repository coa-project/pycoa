''' Interactive Pycoa '''
import sys
sys.path.append('coabook/')      

from coabook.coaenv import *
import coa.front as pycoa

# import vars and methods in the global name space
globals().update(vars(pycoa))

import code
sys.ps1 = "pycoa >>> "
code.interact(local=globals())



