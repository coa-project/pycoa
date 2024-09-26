from src.front import Front

def test_pyvoa():
    pyvoa = Front()
    pyvoa.setwhom('spfnational')
    pyvoa.setvisu(vis='mplt')
    return  pyvoa.plot()

pl = test_pyvoa()    
pl.savefig('test_pyvoa.png')
