# Example using sentinellesIRA database
from src.front import bfront

def test_pyvoa():
    pyvoa = bfront()
    pyvoa.setwhom('sentinellesIRA')
    print(pyvoa.get())

pl = test_pyvoa()    
