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
import time
import os.path
import requests
from tempfile import gettempdir
from getpass import getuser
from zlib import crc32
from urllib.parse import urlparse

from coa.error import CoaKeyError,CoaTypeError,CoaConnectionError,CoaNotManagedError

_verbose_mode = 1 # default

def get_verbose_mode():
    """Return the verbose mode
    """
    return _verbose_mode

def set_verbose_mode(v):
    """Set the verbose mode
    """
    global _verbose_mode
    _verbose_mode=v
    return get_verbose_mode()

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
        return datetime.date(int(year),int(month),int(day))
    except ValueError:
        raise CoaTypeError("Check consistancy of the given date. e.g. the day (btw 1 and 31), " \
            "the month (btw 1 and 12) and the year value.")

def extract_dates(when):
    """Expecting None or 1 or 2 dates separated by :. The format is a string.
    If 2 dates are given, they must be ordered.
    When 1 date is given, assume that's the latest which is given.
    When None date is give, the oldest date is 01/01/0001, the newest is now.

    It returns 2 datetime object. If nothing given, the oldest date is 01/01/0001,
    """
    #w0=datetime.datetime(1,1,1) # minimal year is 1
    #w1=datetime.datetime.now()
    w0=datetime.date(1,1,1) # minimal year is 1
    w1=datetime.date.today()
    if when:  # when input is not None, assume min and max date
        if type(when) != type(str()):
            raise CoaTypeError("Date expected as string.")
        w=when.split(':')

        if len(w)>2 :
            raise CoaTypeError("Too many dates given. Expecting 1 or 2 with : as a separator. ")
        if len(w) == 1:
            w1=check_valid_date(w[0])
        if len(w) > 1:
            if w[1] != '':
                w1=check_valid_date(w[1])
            if w[0] != '':
                w0=check_valid_date(w[0])

        if w0>w1:
            raise CoaTypeError("First date must occur before the second one.")

    return w0,w1

def get_local_from_url(url,expiration_time=0,suffix=''):
    """"Download data from the given url and store it into a local file.

    If the expiration time is 0 (default), the data will never be downloaded anymore if available.
    If the expiration time is < 0, it forces to download the file.
    If the expiration time (in seconds) is lower than time difference between now and last modification
    time of the file, the file is downloaded.

    One may add a suffix to the local filename if known.
    """

    tmpdir=os.path.join(gettempdir(),"pycoa_data"+"_"+getuser())
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    local_filename=os.path.join(tmpdir,urlparse(url).netloc+"_"+str(crc32(bytes(url,'utf-8')))+suffix)

    local_file_exists=os.path.exists(local_filename)

    if expiration_time >=0 and local_file_exists:
        if expiration_time==0 or time.time()-os.path.getmtime(local_filename)<expiration_time:
            verb('Using locally stored data for '+url)
            return local_filename

    # if not : download the file
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        urlfile = requests.get(url, allow_redirects=True,headers=headers) # adding headers for server which does not accept no browser presentation
        fp=open(local_filename,'wb')
        fp.write(urlfile.content)
        fp.close()
        verb('Download content of '+url+' . Locally stored as cached data in '+local_filename)
    except requests.exceptions.RequestException :
        if local_file_exists and expiration_time >=0 :
            info('Cannot access to '+url+' . Will use locally stored cached version.')
            pass
        else:
            raise CoaConnectionError('Cannot access to the url '+\
                url+' . Please check your internet connection or url path.')
    except Exception as e2:
        raise CoaNotManagedError(type(e2).__name__+" : "+str(e2))

    return local_filename

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    