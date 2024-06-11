''' Interactive Pycoa '''
import sys
sys.path.append('coabook/')      

from coabook.coaenv import *
import coa.front as pycoa
import matplotlib
import code
# import vars and methods in the global name space
globals().update(vars(pycoa))

sys.ps1 = "pycoa >>> "
#matplotlib.rcParams['backend'] 
#matplotlib.use('TkAgg') 
pycoa.setwhom('owid',reload=False)
a=pycoa.map(where='France')
pycoa.setvisu(vis='mplt')
a=pycoa.map(where='France')
a.savefig('fig/map.png')
a=pycoa.plot(where='France')
a.savefig('fig/plot.png')
a=pycoa.hist(where='Europe')
a.savefig('fig/hist.png')
#code.interact(local=globals())
