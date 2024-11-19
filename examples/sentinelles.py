# Example using sentinellesIRA database
from src.front import bfront

def test_pyvoa():
    pyvoa = bfront()
    pyvoa.setwhom('sentinellesIRA')
    print(pyvoa.get())
    pyvoa.setvisu(vis='mplt')
    return  pyvoa.plot()

pl = test_pyvoa()    
pl.savefig('test_pyvoa.png')
