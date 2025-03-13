# Example using sentinellesIRA database
from pyvoa.front import front
def test_pyvoa():
    pyvoa = front()
    pyvoa.setvisu(vis='matplotlib')
    pyvoa.setwhom('spf',reload=False)
    pyvoa.plot() #mapoption='dense',tile='esri')
    return pyvoa 
def test2():
    pyvoa = front()
    pyvoa.setwhom('owid',reload=True)
    pyvoa.setvisu(vis='matplotlib')
    #pyvoa.plot(where='France',option='sumall')
    pyvoa.hist(where='Europe')
    return pyvoa
#pl = test_pyvoa()
pl = test2()
pl.savefig('mapspf.png')
