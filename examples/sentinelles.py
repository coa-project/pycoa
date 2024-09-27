from src.front import front

def test_pyvoa():
    pyvoa = front()
    pyvoa.setwhom('sentinellesIRA')
    display(pyvoa.get())
    pyvoa.setvisu(vis='mplt')
    return  pyvoa.plot()

pl = test_pyvoa()    
pl.savefig('test_pyvoa.png')
