#Welcome to coa env
import sys
sys.path.insert(1, '..')

#succes or error message after importing pycoa
#commen
try:
    import coaenv
    print("Import of pycoa successful!")
except ImportError as e:
    print("Error when importing pycoa:", e)
    print("Make sure the pycoa module is installed correctly.")
    
#from coa import *
from coa.front import * 
