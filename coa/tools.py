# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april-november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : coa.tools

About
-----
This is the PyCoA tools module to be considered as a swiss knife list of functions.
One find function for 
 - verbose or warning mode management.
 - kwargs analysis 

The _verbose_mode variable should be set to 0 if no printing output needed. The
default value is 1 (print information to stdout). The 2 value grants a debug level information
printing.
"""

import datetime
from coa.error import CoaKeyError,CoaTypeError

_verbose_mode = 1 # default

def info(*args):
    """Print to stdout with similar args as the builtin print function,
    if _verbose_mode > 0
    """
    if _verbose_mode > 0:
        print(*args)
        
def verb(*args):
    """Print to stdout with similar args as the builtin print function,
    if _verbose_mode > 1
    """
    if _verbose_mode > 1:
        print(*args)
        
def kwargs_test(given_args,expected_args,error_string):
    """Test that the list of kwargs is compatible with expected args. If not
    it raises a CoaKeyError with error_string.
    """

    if type(given_args)!=dict:
        raise CoaKeyError("kwargs_test error, the given args are not a dict type.")
    if type(expected_args)!=list:
        raise CoaKeyError("kwargs_test error, the expected args are not a list type")

    bad_kwargs=[a for a in list(given_args.keys()) if a not in expected_args ]
    if len(bad_kwargs) != 0 :
        raise CoaKeyError(error_string+' Unrecognized args are '+str(bad_kwargs)+'.')

    return True

def check_valid_date(date):
    """Check if a string is compatible with a valid date under the format day/month/year
    with 2 digits for day, 2 digits for month and 4 digits for year.
    """
    raise_error=False
    if type(date) != type(str()):
        raise CoaTypeError('Expecting date given as string.')

    d=date.split('/')
    if len(d)!=3:
        raise_error=True
    else:
        if len(d[0])!=2 or len(d[1])!=2 or len(d[2])!=4:
            raise_error=True
        else:
            try:
                year=int(d[2])
                month=int(d[1])
                day=int(d[0])
            except ValueError:
                raise_error=True

    if raise_error:
        raise CoaTypeError("Not a valid date should be : day/month/year, with 2 digits " \
            "for month or day, 4 digits for year.")

    try:
        return datetime.datetime(int(year),int(month),int(day))
    except ValueError:
        raise CoaTypeError("Check consistancy of the given date. e.g. the day (btw 1 and 31), " \
            "the month (btw 1 and 12) and the year value.")

def extract_dates(when):
    """Expecting None or 1 or 2 dates separated by :. The format is a string. 
    If 2 dates are given, they must be ordered.
    It returns 2 datetime object. If nothing given, the oldest date is 01/01/0001, 
    the newest is now.
    """
    w0=datetime.datetime(1,1,1) # minimal year is 1
    w1=datetime.datetime.now()

    if when:  # when input is not None, assume min and max date
        if type(when) != type(str()):
            raise CoaTypeError("Date expected as string.")
        w=when.split(':')

        if len(w)>2 :
            raise CoaTypeError("Too many dates given. Expecting 1 or 2 with : as a separator. ")
        if len(w) > 0:
            w0=check_valid_date(w[0])
        if len(w) > 1:
            w1=check_valid_date(w[1])

        if w0>w1:
            raise CoaTypeError("First date must occur before the second one.")

    return w0,w1
