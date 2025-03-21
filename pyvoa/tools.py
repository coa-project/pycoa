# -*- coding: utf-8 -*-
"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.tools

About
-----
This is the PyCoA tools module to be considered as a swiss knife list of functions.
One find function for
 - verbose or warning mode management.
 - kwargs analysis
 - filling nan values of given pandas
 - date parsing validation
 - automatic file caching system

The _verbose_mode variable should be set to 0 if no printing output needed. The
default value is 1 (print information to stdout). The 2 value grants a debug level information
printing.
"""

import pandas as pd
import numpy
import datetime
import time
import os.path
import requests
from tempfile import gettempdir
from getpass import getuser
from zlib import crc32
from urllib.parse import urlparse
import unidecode
import datetime as dt
import numpy as np
from pyvoa.error import PyvoaError, PyvoaConnectionError, PyvoaNotManagedError


# testing if pyvoa.ata is available
import importlib
_coacache_folder=''
_coacache_module_info = importlib.util.find_spec("coacache")
if _coacache_module_info != None:
    _coacache_folder = _coacache_module_info.submodule_search_locations[0]

# Verbosity of pycoa
_verbose_mode = 1 # default

# ----------------------------------------------------
# --- Usefull functions for pycoa.--------------------
# ----------------------------------------------------
def get_verbose_mode():
    """Return the verbose mode
    """
    return _verbose_mode

def set_verbose_mode(v):
    """Set the verbose mode
    """
    global _verbose_mode
    _verbose_mode=v
    if (v < 2) :
        pd.options.mode.chained_assignment = None  # default='warn'
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

def kwargs_keystesting(given_args, expected_args, error_string):
    """Test that the list of kwargs is compatible with expected args. If not
    it raises a PyvoaKeyError with error_string.
    """

    if type(given_args)!=dict:
        raise PyvoaError("kwargs_keystesting error, the given args are not a dict type.")
    if type(expected_args)!=list:
        raise PyvoaError("kwargs_keystesting error, the expected args are not a list type")

    bad_kwargs=[a for a in list(given_args.keys()) if a not in expected_args ]
    if len(bad_kwargs) != 0 :
        raise PyvoaError(error_string+' Unrecognized args are '+str(bad_kwargs)+'.')

    return True

def debug(value,message=''):
    if message:
        message = message
    else:
        message = ''
    print("\n------------------------\n")
    print(" ---- " , message ,  " ->>>>>>>>       ",value)
    print("\n------------------------\n")

def kwargs_test(given_args, expected_args, error_string):
    """Test that the list of kwargs is compatible with expected args. If not
    it raises a PyvoaKeyError with error_string.
    """

    if type(given_args)!=dict:
        raise PyvoaKeyError("kwargs_test error, the given args are not a dict type.")
    if type(expected_args)!=list:
        raise PyvoaKeyError("kwargs_test error, the expected args are not a list type")

    bad_kwargs=[a for a in list(given_args.keys()) if a not in expected_args ]
    if len(bad_kwargs) != 0 :
        raise PyvoaKeyError(error_string+' Unrecognized args are '+str(bad_kwargs)+'.')

    return True

def kwargs_valuestesting(given_values, expected_values, error_string):
    ''' test if the values in the list given_values are in the expected_values '''
    if not isinstance(expected_values,list):
        raise PyvoaError("kwargs_fulltest error, the given args are not a list type.")

    if expected_values is not None and given_values is not None:
        if isinstance(given_values,list):
            if isinstance(given_values[0],list):
                for a in given_values:
                    bad_values = [i for i in a if i not in expected_values ]
                    if len(bad_values) != 0 :
                        raise PyvoaError(error_string+' unrecognized values '+str(bad_values))
            else:
                bad_values = [a for a in given_values if a not in expected_values ]
                if len(bad_values) != 0 :
                    raise PyvoaError(error_string+' unrecognized values '+str(bad_values))
        else:
            if given_values not in expected_values:
                raise PyvoaError(error_string+' unrecognized values '+str(given_values))
    else:
        pass

def kwargs_keyvaluestesting(given_kargs, expected_kargs, hiddenkeys,error_string):
    """Test that the list of kwargs is compatible with expected args. If not
    it raises a PyvoaKeyError with error_string.
    """
    if not isinstance(given_kargs,dict) or not isinstance(expected_kargs,dict):
        raise PyvoaError("kwargs_fulltest error, the given args are not a dict type.")

    bad_kwargs = [a for a in list(given_kargs.keys()) if a not in list(expected_kargs.keys()) ]
    if len(bad_kwargs) != 0 :
        raise PyvoaError(error_string+' Unrecognized args are '+str(bad_kwargs)+'.')
    else:
        if hiddenkeys:
            [expected_kargs.pop(i) for i in hiddenkeys]
            [given_kargs.pop(i) for i in hiddenkeys ]
        for a in list(given_kargs.values()):
            if isinstance(a,list):
                for i in a:
                    expected = [i for i in flat_list(list(expected_kargs.values())) if i != '']
                    print("%%%",expected)
                    if i not in flat_list(expected) and list(expected_kargs.values()):
                        raise PyvoaError(error_string+' %%%Unrecognized argument '+i+'.')
            else:
                if a not in list(expected_kargs.values()):
                    raise PyvoaError(error_string+' Unrecognized argument '+a+'.')
    return True

def tostdstring(s):
    """Standardization of string for country,region or subregion tests
    """
    return unidecode.unidecode(' '.join(s.replace('-',' ').split())).upper()

def fill_missing_dates(p, date_field='date', loc_field='where', d1=None, d2=None):
    """Filling the input pandas dataframe p with missing dates
    """
    if not isinstance(p, pd.DataFrame):
        raise PyvoaTypeError("Expecting input p as a pandas dataframe.")
    if not date_field in p.columns:
        raise PyvoaKeyError("The date_field is not a proper column of input pandas dataframe.")
    if not loc_field in p.columns:
        raise PyvoaKeyError("The loc_field is not a proper column of input pandas dataframe.")
    # datatoilettage :)
    p = p.loc[~p[loc_field].isin([''])]

    if d2==None:
        d2=p[date_field].max()
    if d1==None:
        d1=p[date_field].min()

    if not all(isinstance(d, datetime.date) for d in [d1,d2]):
        raise PyvoaTypeError("Waiting for dates as datetime.date.")
    if d1 > d2:
        raise PyvoaKeyError("Dates should be ordered as d1<d2.")

    idx = pd.date_range(d1, d2, freq = "D")
    idx = idx.date
    all_loc=list(p[loc_field].unique())

    pfill=pd.DataFrame()
    for l in all_loc:
        pp=p.loc[p[loc_field]==l]
        pp2=pp.set_index([date_field])
        pp2.index = pd.DatetimeIndex(pp2.index)
        pp3 = pp2.reindex(idx,fill_value=pd.NA)#numpy.nan)#
        pp3[loc_field] = pp3[loc_field].fillna(l)  #pp3['location'].fillna(method='bfill')
        #pp3['isowhere'] = pp3['isowhere'].fillna(method='bfill')
        #pp3['isowhere'] = pp3['isowhere'].fillna(method='ffill')
        pfill=pd.concat([pfill, pp3])
    pfill.reset_index(inplace=True)
    return pfill

def check_valid_date(date):
    """Check if a string is compatible with a valid date under the format day/month/year
    with 2 digits for day, 2 digits for month and 4 digits for year.
    """
    raise_error=False
    if type(date) != type(str()):
        raise PyvoaTypeError('Expecting date given as string.')

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
        raise PyvoaTypeError("Not a valid date should be : day/month/year, with 2 digits " \
            "for month or day, 4 digits for year.")

    try:
        return datetime.date(int(year),int(month),int(day))
    except ValueError:
        raise PyvoaTypeError("Check consistancy of the given date. e.g. the day (btw 1 and 31), " \
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
    if when and when != ['']:  # when input is not None, assume min and max date
        if type(when) != type(str()):
            raise PyvoaError("Date expected as string.")
        w=when.split(':')

        if len(w)>2 :
            raise PyvoaError("Too many dates given. Expecting 1 or 2 with : as a separator. ")
        if len(w) == 1:
            w1=check_valid_date(w[0])
        if len(w) > 1:
            if w[1] != '':
                w1=check_valid_date(w[1])
            if w[0] != '':
                w0=check_valid_date(w[0])

        if w0>w1:
            raise PyvoaError("First date must occur before the second one.")
    return w0, w1

def week_to_date(whenstr):
    """
    convert week to date.
    2 cases:
    - Rolling week
        if format is Y-M-D-Y-M-D: return middle dates
    - One week data Wnumber: return monday correction to the week number
    """
    convertion = 0
    if len(whenstr) == 21:
        firstday = datetime.date(int(whenstr.split('-')[0]),int(whenstr.split('-')[1]),int(whenstr.split('-')[2]))
        lastday  = datetime.date(int(whenstr.split('-')[3]),int(whenstr.split('-')[4]),int(whenstr.split('-')[5]))
        convertion = firstday + (lastday - firstday)/2
    elif len(whenstr) == 10:
        firstday = datetime.date(int(whenstr.split('-')[0]),int(whenstr.split('-')[1]),int(whenstr.split('-')[2]))
        convertion = firstday+datetime.timedelta(days=3)
    elif len(whenstr) == 6:
        year = whenstr[:4]
        week = '-S'+whenstr[4:]
        whenstr = year + week
        convertion = datetime.datetime.strptime(whenstr  + '-1' , "%G-S%V-%u")+datetime.timedelta(days = 7)
    else:
        convertion = datetime.datetime.strptime(whenstr  + '-1' , "%G-S%V-%u")+datetime.timedelta(days = 7)
    return convertion

def exists_from_url(path):
    """"Check if url for files responds
    Boolean return
    """
    r = requests.head(path)
    return r.status_code == requests.codes.ok

def get_local_from_url(url,expiration_time=0,suffix=''):
    """"Download data from the given url and store it into a local file.

    If the expiration time is 0 (default), the data will never be downloaded anymore if available.
    If the expiration time is < 0, it forces to download the file.
    If the expiration time (in seconds) is lower than time difference between now and last modification
    time of the file, the file is downloaded.

    One may add a suffix to the local filename if known.
    """

    tmpdir=os.path.join(gettempdir(),"pycoa.data"+"_"+getuser())
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    local_base_filename=urlparse(url).netloc+"_"+str(crc32(bytes(url,'utf-8')))+suffix
    local_tmp_filename=os.path.join(tmpdir,local_base_filename)

    local_file_exists=False

    if _coacache_folder  != '':
        local_cached_filename=os.path.join(_coacache_folder,local_base_filename)
        local_file_exists=os.path.exists(local_cached_filename)
        local_filename=local_cached_filename

    if os.path.exists(local_tmp_filename):
        if local_file_exists: # prefering the file in tmp if more recent
            if os.path.getmtime(local_tmp_filename) > os.path.getmtime(local_filename):
                local_filename = local_tmp_filename
        else:
            local_file_exists=True
            local_filename=local_tmp_filename

    if expiration_time >=0 and local_file_exists:
        if expiration_time==0 or time.time()-os.path.getmtime(local_filename)<expiration_time:
            verb('Using locally stored data for '+url+' stored as '+local_filename)
            return local_filename

    # if not : download the file in tmp area
    local_filename=local_tmp_filename
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
            raise PyvoaConnectionError('Cannot access to the url '+\
                url+' . Please check your internet connection or url path.')
    except Exception as e2:
        raise PyvoaNotManagedError(type(e2).__name__+" : "+str(e2))

    return local_filename

def testsublist(lst1, lst2):
    '''
       test if lst1 is in lst2 list
    '''
    test=False
    extract = [el for el in lst1 if el in lst2]
    if len(extract)==len(lst1):
        test=True
    return test

def flat_list(matrix):
     ''' Flatten list function used in covid19 methods'''
     flatten_matrix = []
     for sublist in matrix:
         if isinstance(sublist,list):
             for val in sublist:
                 flatten_matrix.append(val)
         else:
             flatten_matrix.append(sublist)
     return flatten_matrix

def all_or_none_lists(my_list):
    # Vérifie s'il existe au moins une liste dans les éléments
    has_list = any(isinstance(x, list) for x in my_list)
    # Si oui, vérifie que tous les éléments sont des listes
    if has_list and not all(isinstance(x, list) for x in my_list):
        return False
    return True

def getnonnegfunc(mypd,which):
    '''
    From a mypd pandas and a which value return non negative values
    '''
    if isinstance(which,list):
        raise PyvoaError('getnonnegfunc do not accepte a list ...')
    else:
        whichvalues = mypd[which]
        reconstructed = pd.DataFrame()
        try:
            y0 = whichvalues.values[0] # integrated offset at t=0
        except:
            y0 = 0
        if np.isnan(y0):
            y0 = 0
        pa = whichvalues.diff()
        yy = pa.values
        ind = list(pa.index)
        where_nan = np.isnan(yy)
        yy[where_nan] = 0.
        indices=np.where(yy < 0)[0]
        for kk in np.where(yy < 0)[0]:
            k = int(kk)
            val_to_repart = -yy[k]
            if k < np.size(yy)-1:
                yy[k] = (yy[k+1]+yy[k-1])/2
            else:
                yy[k] = yy[k-1]
            val_to_repart = val_to_repart + yy[k]
            s = np.nansum(yy[0:k])
            if not any([i !=0 for i in yy[0:k]]) == True and s == 0:
                yy[0:k] = 0.
            elif s == 0:
                yy[0:k] = np.nan*np.ones(k)
            else:
                yy[0:k] = yy[0:k]*(1-float(val_to_repart)/s)
        whichvalues = whichvalues.copy()
        whichvalues.loc[ind] = np.cumsum(yy)+y0 # do not forget the offset
        if reconstructed.empty:
            reconstructed = mypd
        else:
            reconstructed = pd.concat([mypd,whichvalues])
    return reconstructed

def return_nonan_dates_pandas(df = None, field = None):
   ''' Check if for last date all values are nan, if yes check previous date and loop until false'''
   watchdate = df.date.max()
   boolval = True
   j = 0
   while (boolval):
       boolval = df.loc[df.date == (watchdate - dt.timedelta(days=j))][field].dropna().empty
       j += 1
   df = df.loc[df.date <= watchdate - dt.timedelta(days=j - 1)]
   boolval = True
   j = 0
   watchdate = df.date.min()
   while (boolval):
       boolval = df.loc[df.date == (watchdate + dt.timedelta(days=j))][field].dropna().empty
       j += 1
   df = df.loc[df.date >= watchdate - dt.timedelta(days=j - 1)]
   return df

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
