''' Interactive Pycoa '''
import sys
sys.path.append('coabook/')      

from coabook.coaenv import *
import coa.front as pycoa
import matplotlib
import code
import os
# import vars and methods in the global name space
globals().update(vars(pycoa))

sys.ps1 = "pycoa >>> "
#matplotlib.rcParams['backend'] 
#matplotlib.use('TkAgg') 
path = "fig/"
if not os.path.exists(path):
    os.makedirs(path)

pycoa.setvisu(vis='mplt')
pycoa.setwhom('owid',reload=False)
a=pycoa.plot(where='Europe')
'''
a=pycoa.map(where='France')
a.savefig(path+'map.png')
a=pycoa.plot(where='France')
a.savefig(path+'plot.png')
a=pycoa.hist(where='Europe')
a.savefig(path+'hist.png')
#code.interact(local=globals())
'''
