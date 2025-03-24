# Example using sentinellesIRA database
import pyvoa.front as pv
import matplotlib
matplotlib.use('Agg')
#from pyvoa.front import front
def test_pyvoa():
    pyvoa = front()
    pyvoa.setvisu(vis='matplotlib')
    pyvoa.setwhom('spf',reload=False)
    pyvoa.plot() #mapoption='dense',tile='esri')
    return pyvoa 
def test2():
    #pyvoa = front()
    pv.setwhom('owid',reload=False)
    pv.setvisu(vis='matplotlib')
    #pyvoa.plot(where='France',option='sumall')
    pv.map(where='Europe')
    return pv
#pl = test_pyvoa()
pl = test2()
pl.savefig('mapspf.png')
