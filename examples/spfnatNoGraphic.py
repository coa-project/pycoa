# Example using sentinellesIRA database
from src.front import front

def test_pyvoa():
    pyvoa = front()
    pyvoa.setwhom('spfnational')
    return pyvoa.get()

pandy = test_pyvoa()    
display(pandy)
