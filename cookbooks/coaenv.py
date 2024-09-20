#Welcome to coa env
import sys
sys.path.insert(1, '..')

#succes or error message after importing pycoa
#commentaire
try:
    import coaenv
except ImportError as e:
    print("Error when importing pycoa:", e)
    print("Make sure the pycoa module is installed correctly.")

#from src import *
from src.front import *
#import src.front 
