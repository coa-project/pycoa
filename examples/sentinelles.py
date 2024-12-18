# Example using sentinellesIRA database
from src.front import front

def test_pyvoa():
    pyvoa = front()
    pyvoa.setvisu(vis='matplotlib')
    pyvoa.setwhom('spf',reload=False)
    pyvoa.map(mapoption='dense',tile='esri')
    return pyvoa 

pl = test_pyvoa()
pl.savefig('mapspf.png')
