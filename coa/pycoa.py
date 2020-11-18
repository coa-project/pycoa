# -*- coding: utf-8 -*-
"""Project : CoCoA - Copyright © CoCoa-team-17
Date :    april-november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file
About
-----
This is the CoCoA front end functions. It provides easy access and
use of the whole CoCoA framework in a simplified way.
The use can change the database, the type of data, the output format
with keywords (see help of functions below).
Basic usage
-----------
** plotting covid deaths (default value) vs. time **
    import pycoa.pycoa as cc
    cc.plot(where='France')  # where keyword is mandatory
** getting recovered data for some countries **

    cc.get(where=['Spain','Italy'],which='recovered')
** listing available database and which data can be used **
    cc.listwhom()
    cc.setwhom('JHU') # return available keywords (aka 'which' data)
    cc.listwhich()   # idem
    cc.listwhat()    # return available time serie type (total,
                     # daily...)

"""

# --- Imports ----------------------------------------------------------
import warnings
from copy import copy
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import inspect

from pycoa.tools import kwargs_test
import pycoa.covid19 as coco
import pycoa.geo as coge
from pycoa.error import *
import pycoa.display as cd

from bokeh.io import show, output_notebook
output_notebook(hide_banner=True)

from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, HoverTool
from bokeh.palettes import brewer
import json

# --- Needed global private variables ----------------------------------
_listwhom=['jhu',    # John Hopkins University first base, default
            'owid', # Our World in Data
            'spf',   # Sante publique France
            'opencovid19'] #  see data.gouv.fr
_whom = _listwhom[0] # default base

_db = coco.DataBase(_whom) # initialization with default
_cocoplot = cd.CocoDisplay(_db)

#_info = coge.GeoInfo() # will be the info (pseudo) private variable
#_reg = coge.GeoRegion()

_listwhat=['cumul','diff',  # first one is default but we must avoid uppercases
            'daily',
            'weekly',
            'date']

# --- Front end functions ----------------------------------------------


# ----------------------------------------------------------------------
# --- listwhom() -------------------------------------------------------
# ----------------------------------------------------------------------

def listwhom():
    """Return the list of currently avalailable databases for covid19
     data in CoCoA.
     The first one is the default one.
    """
    return _listwhom

# ----------------------------------------------------------------------
# --- listwhat() -------------------------------------------------------
# ----------------------------------------------------------------------

def listwhat():
    """Return the list of currently avalailable type of series available.
     The first one is the default one.
    """
    return _listwhat

# ----------------------------------------------------------------------
# --- setwhom() --------------------------------------------------------
# ----------------------------------------------------------------------

def setwhom(base):
    """Set the covid19 database used, given as a string.
    Please see pycoa.listbase() for the available current list.

    By default, the listbase()[0] is the default base used in other
    functions.
    """
    global _whom,_db
    if base not in listwhom():
        raise CocoaDbError(base+' is not a supported database. '
            'See pycoa.listbase() for the full list.')
    if _whom != base:
        _db = coco.DataBase(base)
    return _db.get_available_keys_words()

# ----------------------------------------------------------------------
# --- listwhich() ------------------------------------------------------
# ----------------------------------------------------------------------

def listwhich(dbname=None):
    """Get which are the available fields for the current or specified
    base. Output is a list of string.
    By default, the listwhich()[0] is the default which field in other
    functions.
    """

    if dbname == None:
        dbname=_whom
    if dbname not in listwhom():
        raise CocoaDbError(dbname+' is not a supported database name. '
            'See pycoa.listwhom() for the full list.')
    return _db.get_available_keys_words()


# ----------------------------------------------------------------------
# --- get(**kwargs) ----------------------------------------------------
# ----------------------------------------------------------------------

def get(**kwargs):
    """Return covid19 data in specified format output (default, by list)
    for specified locations ('where' keyword).
    The used database is set by the setbase() function but can be
    changed on the fly ('whom' keyword)
    Keyword arguments
    -----------------

    where  --   a single string of location, or list of (mandatory,
                no default value)
    which  --   what sort of data to deliver ( 'death','confirmed',
                'recovered' …). See listwhat() function for full
                list according to the used database.
    what   --   which data are computed, either in cumulative mode
                ( 'cumul', default value) or 'daily' or other. See
                listwhich() for fullist of available
                Full list of which keyword with the listwhich() function.
    whom   --   Database specification (overload the setbase()
                function). See listwhom() for supported list
                function). See listwhom() for supported list

    output --   output format returned ( list (default), dict or pandas)
    """
    kwargs_test(kwargs,['where','what','which','whom','output'],
            'Bad args used in the pycoa.get() function.')

    global _db,_whom
    where=kwargs.get('where',None)
    what=kwargs.get('what',None)
    which=kwargs.get('which',None)
    whom=kwargs.get('whom',None)

    output=kwargs.get('output',None)

    if not where:
        raise CocoaKeyError('No where keyword given')

    if not whom:
        whom=_whom
    if whom != _whom:
        setwhom(whom)

    if not what:
        what=listwhat()[0]
    #elif what not in listwhat():
    if not bool([s for s in listwhat() if s in what]):
        raise CocoaKeyError('What option '+what+' not supported'
                            'See listwhat() for list.')

    if not which:
        which=listwhich()[0]
    elif which not in setwhom(whom):
        raise CocoaKeyError('Which option '+which+' not supported. '
                            'See listwhich() for list.')
    pandy = _db.get_stats(which=which,location=where)
    if inspect.stack()[1].function == '<module>':
        pandy = _db.get_stats(which=which,location=where).rename(columns={'location': 'where'})
    return pandy



# ----------------------------------------------------------------------
# --- plot(**kwargs) ---------------------------------------------------
# ----------------------------------------------------------------------

def plot(**kwargs):
    """Plot data according to arguments (same as the get function)
    and options.

    Keyword arguments
    -----------------

    where (mandatory), what, which, whom : (see help(get))

    input  --   input data to plot within the pycoa framework (e.g.
                after some analysis or filtering). Default is None which
                means that we use the basic raw data through the get
                function.
                When the 'input' keyword is set, where, what, which,
                whom keywords are ignored.
                input should be given as valid pycoa pandas dataframe.
    """
    kwargs_test(kwargs,['where','what','which','whom','input','width_height'],
            'Bad args used in the pycoa.plot() function.')

    input_arg=kwargs.get('input',None)
    if input_arg != None:
        if not isinstance(input_arg,pd.DataFrame):
            raise CocoaTypeError('Waiting input as valid pycoa pandas '
                'dataframe. See help.')
        t=input_arg
    else:
        t=get(**kwargs,output='pandas')

    which=kwargs.get('which',listwhich()[0])
    what=kwargs.get('what',None)

    title=kwargs.get('title',None)
    width_height=kwargs.get('width_height',None)

    if what:
        which_init = which
        if what == 'daily' or  what == 'diff':
            which = 'diff'
        if what == 'cumul' and _whom == 'jhu':
            which = which_init
        if  what == 'weekly':
            t['weekly'] = t['diff'].rolling(7).mean()
            which = 'weekly'
    fig = _cocoplot.pycoa_basic_plot(t,which,title,width_height)
    show(fig)

# ----------------------------------------------------------------------
# --- hist(**kwargs) ---------------------------------------------------
# ----------------------------------------------------------------------

def hist(**kwargs):
    """Create histogram according to arguments (same as the get
    function) and options.

    Keyword arguments
    -----------------

    where (mandatory), what, which, whom : (see help(get))
    input  --   input data to plot within the pycoa framework (e.g.
                after some analysis or filtering). Default is None which
                means that we use the basic raw data through the get
                function.
                When the 'input' keyword is set, where, what, which,
                whom keywords are ignored.
    """
    kwargs_test(kwargs,['where','what','which','whom','input','bins'],
            'Bad args used in the pycoa.hist() function.')

    input_arg=kwargs.get('input',None)
    if input_arg != None:
        if not isinstance(input_arg,pd.DataFrame):
            raise CocoaTypeError('Waiting input as valid pycoa pandas '
                'dataframe. See help.')
        t=input_arg
    else:
        t=get(**kwargs,output='pandas')

    which=kwargs.get('which',listwhich()[0])
    bins=kwargs.get('bins',None)
    title=kwargs.get('title',None)
    width_height=kwargs.get('width_height',None)
    what=kwargs.get('what',None)
    date=kwargs.get('date','last')

    if type(what) is not None.__class__:
        which_init = which
        if what == 'daily' or  what == 'diff':
            which = 'diff'
        if what == 'cumul' and _whom == 'jhu':
            which = which_init
        if  what == 'weekly':
            t['weekly'] = t['diff'].rolling(7).mean()
            which = 'weekly'
        if what[:5] == 'date:':
            date = what[5:]

    fig=_cocoplot.pycoa_histo(t,which,bins,title,width_height,date)

    show(fig)

# ----------------------------------------------------------------------
# --- map(**kwargs) ----------------------------------------------------
# ----------------------------------------------------------------------

def map(**kwargs):
    """Create a map according to arguments and options.
    See help(hist).
    """
    kwargs_test(kwargs,['where','what','which','whom','input'],
            'Bad args used in the pycoa.map() function.')

    input_arg=kwargs.get('input',None)
    where=kwargs.get('where',None)

    if input_arg != None:
        if not isinstance(input_arg,pd.DataFrame):
            raise CocoaTypeError('Waiting input as valid pycoa pandas '
                'dataframe. See help.')
        t=input_arg
    else:
        t=get(**kwargs,output='pandas')

    which=kwargs.get('which',listwhich()[0])
    what=kwargs.get('what',None)
    if what:
        which_init = which
        if what == 'daily' or  what == 'diff':
            which = 'diff'
        if what == 'cumul' and _whom == 'jhu':
            which = which_init
        if  what == 'weekly':
            t['weekly'] = t['diff'].rolling(7).mean()
            which = 'weekly'

    return _cocoplot.return_map(t,which)
