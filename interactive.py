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
a.savefig(path+'plot.png')
<<<<<<< HEAD
pycoa.plot(where='Europe',which='total_vaccinations_per_hundred')
a.savefig(path+'plot.png')
=======
'''
>>>>>>> 9b711bfea68844b699cdf27247071cb03747189a
a=pycoa.map(where='France')
a.savefig(path+'map.png')
a=pycoa.plot(where=[['Europe'],['Italy']],option='sumall')
a.savefig(path+'plot.png')
a=pycoa.hist(where='France')
a.savefig(path+'hist.png')
#code.interact(local=globals())
'''
'''
#matplotlib.pyplot.show()
