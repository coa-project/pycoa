# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april-november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : coa.front

About :
-------

This is the PyCoA front end functions. It provides easy access and
use of the whole PyCoA framework in a simplified way.
The use can change the database, the type of data, the output format
with keywords (see help of functions below).

Basic usage
-----------
** plotting covid deaths (default value) vs. time **
    import coa.coa as cc
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
import pandas as pd
import inspect
from functools import wraps
import numpy as np
from bokeh.io import show, output_notebook

from coa.tools import kwargs_test,extract_dates
import coa.covid19 as coco
from coa.error import *
import coa.display as cd

output_notebook(hide_banner=True)

# --- Needed global private variables ----------------------------------
_listwhom=['jhu',    # John Hopkins University first base, default
            'owid', # Our World in Data
            'jhu-usa',
            'spf',   # Sante publique France
            'opencovid19'] #  see data.gouv.fr

if 'coa_db' in __builtins__.keys():
    if not  __builtins__['coa_db'] in _listwhom:
        raise CoaDbError("The variable __builtin__.coa_db set to "+str(__builtins__['coa_db'])+" which is an invalid db. Error.")
    _whom = __builtins__['coa_db']
else:
    _whom = _listwhom[0] # default base

_db,_cocoplot = coco.DataBase.factory(_whom) # initialization with default


_listwhat=['cumul',  # first one is default, nota:  we must avoid uppercases
            'daily',
            'weekly']

_listoutput=['list','dict','array','pandas'] # first one is default for get

_listvisu=['bokeh','folium']

# --- Front end functions ----------------------------------------------

# ----------------------------------------------------------------------
# --- listoutput() -----------------------------------------------------
# ----------------------------------------------------------------------
def listoutput():
    """Return the list of currently available output types for the
    get() function. The first one is the default output given if
    not specified.
    """
    return _listoutput

# ----------------------------------------------------------------------
# --- listvisu() -------------------------------------------------------
# ----------------------------------------------------------------------
def listvisu():
    """Return the list of currently available visualization for the
    map() function. The first one is the default output given if
    not specified.
    """
    return _listvisu

# ----------------------------------------------------------------------
# --- listwhom() -------------------------------------------------------
# ----------------------------------------------------------------------

def listwhom():
    """Return the list of currently avalailable databases for covid19
     data in PyCoA.
     The first one is the default one.
    """
    return _db.get_available_database()

# ----------------------------------------------------------------------
# --- listwhat() -------------------------------------------------------
# ----------------------------------------------------------------------

def listwhat():
    """Return the list of currently avalailable type of series available.
     The first one is the default one.
    """
    return _listwhat

# ----------------------------------------------------------------------
# --- listoption() -----------------------------------------------------
# ----------------------------------------------------------------------

def listoption():
    """Return the list of currently avalailable option apply to data.
     Default is no option.
    """
    return _db.get_available_options()

# ----------------------------------------------------------------------
# --- listtile() -------------------------------------------------------
# ----------------------------------------------------------------------

def listtile():
    """Return the list of currently avalailable tile option for map()
     Default is the first one.
    """
    return _cocoplot.tiles_listing

# ----------------------------------------------------------------------
# --- listwhich() ------------------------------------------------------
# ----------------------------------------------------------------------

def listwhich():
    """Get which are the available fields for the current base.
    Output is a list of string.
    By default, the listwhich()[0] is the default which field in other
    functions.
    """
    return _db.get_available_keys_words()

# ----------------------------------------------------------------------
# --- listregion() ------------------------------------------------------
# ----------------------------------------------------------------------

def listregion():
    """Get the list of available regions managed by the current database
    """
    r=_db.geo.get_region_list()
    if isinstance(r,list):
        return r
    else:
        return sorted(r['name_region'].to_list())

# ----------------------------------------------------------------------
# --- setwhom() --------------------------------------------------------
# ----------------------------------------------------------------------

def setwhom(base):
    """Set the covid19 database used, given as a string.
    Please see pycoa.listbase() for the available current list.

    By default, the listbase()[0] is the default base used in other
    functions.
    """
    global _whom,_db,_cocoplot
    if base not in listwhom():
        raise CoaDbError(base+' is not a supported database. '
            'See pycoa.listbase() for the full list.')
    if True: #force the init #_whom != base:
        _db,_cocoplot = coco.DataBase.factory(base)
        _whom = base

    return listwhich()

# ----------------------------------------------------------------------
# --- getwhom() --------------------------------------------------------
# ----------------------------------------------------------------------
def getwhom():
    """Return the current base which is used
    """
    return _whom

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
                ('cumul', default value), or 'daily' (diff with previous day
                and 'weekly' (diff with previous week). See
                listwhich() for fullist of available
                Full list of which keyword with the listwhich() function.
    whom   --   Database specification (overload the setbase()
                function). See listwhom() for supported list
                function). See listwhom() for supported list
    when   --   dates are given under the format dd/mm/yyyy. In the when
                option, one can give one date which will be the end of
                the data slice. Or one can give two dates separated with
                ":", which will define the time cut for the output data
                btw those two dates.

    output --   output format returned ( list (default), array (numpy.array),
                dict or pandas)

    option --   pre-computing option.
                * nonneg means that negative daily balance is pushed back
                to previousdays in order to have a cumulative function which is
                monotonous increasing.
                * nofillnan means that nan value won't be filled.
                * smooth7 will perform a 7 day window average of data
                * sumall will return integrated over locations given via the
                where keyword, the data
                is available. By default : no option.
    """
    kwargs_test(kwargs,['where','what','which','whom','when','output','option','bins','title','visu','tile','cursor_date'],
            'Bad args used in the pycoa.get() function.')

    global _db,_whom
    where=kwargs.get('where',None)
    what=kwargs.get('what',listwhat()[0])
    which=kwargs.get('which',None)
    whom=kwargs.get('whom',None)
    option = kwargs.get('option',None)
    when=kwargs.get('when',None)

    output=kwargs.get('output',listoutput()[0])

    if output not in listoutput():
        raise CoaKeyError('Output option '+output+' not supported. See help().')

    if whom == None:
        whom=_whom
    if whom != _whom:
        setwhom(whom)
    when_beg,when_end=extract_dates(when)

    if not bool([s for s in listwhat() if what.startswith(s)]):
        raise CoaKeyError('What option '+ what +' not supported. '
                            'See listwhat() for full list.')

    if not which:
        which=listwhich()[0]
    elif which not in listwhich():
        raise CoaKeyError('Which option '+which+' not supported. '
                            'See listwhich() for list.')
    pandy = _db.get_stats(which=which,location=where,option=option).rename(columns={'location': 'where'})
    db_first_date = pandy.date.min()
    db_last_date = pandy.date.max()
    if when_beg < db_first_date:
        when_beg = db_first_date
    if when_end > db_last_date:
        when_end=db_last_date

    # when cut
    pandy=pandy[(pandy.date>=when_beg) & (pandy.date<=when_end)]
    pandy.reset_index()
    casted_data = None
    if output == 'pandas':
         pandy = pandy.drop(columns=['cumul'])
         pandy['cumul'] = pandy[which]
         casted_data = pandy
    else:
        # col_name = ''
        # if what == 'daily':
        #     col_name = 'daily'
        # if what == 'cumul' and _whom == 'jhu':
        #     col_name = which
        # if what == 'weekly':
        #     col_name = 'weekly'
        # else:
        #     col_name = 'daily'
        #casted_data = pd.pivot_table(pandy, index='date',columns='where',values=col_name).to_dict('series')
        if output == 'dict':
            casted_data = pandy.to_dict('split')
        if output == 'list' or output == 'array':
            my_list = []
            for keys,values in pandy.items():
                vc=[]
                vc=[i for i in values]
                my_list.append(vc)
            casted_data = my_list
            if output == 'array':
                casted_data = np.array(pandy)

    return casted_data

# ----------------------------------------------------------------------
# --- plot(**kwargs) ---------------------------------------------------
# ----------------------------------------------------------------------

def decoplot(func):
    def generic_plot(**kwargs):
        """
        Decorator Plot data according to arguments (same as the get function)
        and options.

        Keyword arguments
        -----------------

        where (mandatory), what, which, whom, when : (see help(get))

        input       --  input data to plot within the pycoa framework (e.g.
                        after some analysis or filtering). Default is None which
                        means that we use the basic raw data through the get
                        function.
                        When the 'input' keyword is set, where, what, which,
                        whom when keywords are ignored.
                        input should be given as valid pycoa pandas dataframe.

        input_field --  is the name of the field of the input pandas to plot.
                        Default is 'deaths/cumul', the default output field of
                        the get() function.

        width_height : width and height of the picture .
                    If specified should be a list of width and height.
                    For instance width_height=[400,500]

        title       --  to force the title of the plot

        - Two methods from this decorators can be used:
            * plot : date chart  according to location
            * scrollmenu_plot: two date charts which can be selected from scroll menu,
                                according to the locations which were selected
        """
        kwargs_test(kwargs,['where','what','which','whom','when', \
            'input','input_field','width_height','option','title'],
            'Bad args used in the pycoa.plot() function.')

        input_arg=kwargs.get('input',None)

        which=''
        width_height=kwargs.get('width_height',None)
        what=kwargs.get('what',None)

        if isinstance(input_arg,pd.DataFrame):
            t=input_arg
            which=kwargs.get('input_field',listwhich()[0]+'/cumul')
            option=kwargs.get('option',None)
        elif input_arg==None:
            t=get(**kwargs,output='pandas')
            which=kwargs.get('which',listwhich()[0])
            if what == 'cumul' and _whom == 'jhu':
                what = which
            option=kwargs.get('option',None)
        else:
            raise CoaTypeError('Waiting input as valid pycoa pandas '
                    'dataframe. See help.')
        return func(t,**kwargs)
    return generic_plot

@decoplot
def plot(t,**kwargs):
    input_arg=kwargs.get('input',None)
    input_fied=kwargs.get('input_field')
    if isinstance(input_arg,pd.DataFrame) and len(input_fied)==2:
        fig = _cocoplot.pycoa_plot(t,[input_fied[0],input_fied[1]])
    else:
        fig = _cocoplot.pycoa_date_plot(t,**kwargs)
    show(fig)

@decoplot
def scrollmenu_plot(t,**kwargs):
    fig = _cocoplot.scrolling_menu(t,**kwargs)
    show(fig)

# ----------------------------------------------------------------------
# --- hist(**kwargs) ---------------------------------------------------
# ----------------------------------------------------------------------

def hist(**kwargs):
    """Create histogram according to arguments (same as the get
    function) and options.

    Keyword arguments
    -----------------

    where (mandatory if no input), what, which, whom, when : (see help(get))

    input       --  input data to plot within the pycoa framework (e.g.
                    after some analysis or filtering). Default is None which
                    means that we use the basic raw data through the get
                    function.
                    When the 'input' keyword is set, where, what, which,
                    whom when keywords are ignored.
                    input should be given as valid pycoa pandas dataframe.

    input_field --  is the name of the field of the input pandas to plot.
                    Default is 'deaths/cumul', the default output field of
                    the get() function.

    width_height : width and height of the picture .
                If specified should be a list of width and height.
                For instance width_height=[400,500]

    typeofhist  --  'bylocation' (default) or 'byvalue'

    bins        --  number of bins used, only available for 'byvalue' type of
                    histograms.
                    If none provided, a default value will be used.

    """
    kwargs_test(kwargs,['where','what','which','whom','when','input','input_field','bins','title',
                        'typeofhist','cursor_date','option'],
            'Bad args used in the pycoa.hist() function.')

    when=kwargs.get('when',None)
    input_field=None
    input_arg=kwargs.get('input',None)
    typeofhist=kwargs.pop('typeofhist','bylocation')
    cursor_date=kwargs.get('cursor_date',None)

    if isinstance(input_arg,pd.DataFrame):
        t=input_arg
        input_field=kwargs.get('input_field')
        kwargs={}
    elif input_arg==None:
        t=get(**kwargs,output='pandas')
        which=kwargs.get('which',listwhich()[0])
        what=kwargs.get('what',listwhat()[0])
        option=kwargs.get('option',None)
    else:
        raise CoaTypeError('Waiting input as valid pycoa pandas '
            'dataframe. See help.')


    if typeofhist == 'bylocation':
        if 'bins' in kwargs:
            raise CoaKeyError("The bins keyword cannot be set with histograms by location. See help.")
        fig=_cocoplot.pycoa_horizonhisto(t,input_field,**kwargs)
    elif typeofhist == 'byvalue':
        fig=_cocoplot.pycoa_histo(t,input_field,**kwargs)
    else:
        raise CoaKeyError('Unknown typeofhist value. Should be bylocation or byvalue.')

    show(fig)

# ----------------------------------------------------------------------
# --- deco_pycoa_graph(**kwargs) ---------------------------------------
# ----------------------------------------------------------------------

def deco_pycoa_graph(f):
    '''Main decorator for graphical output function calls
    It mainlydeals with arg testings.
    '''
    @wraps(f)
    def wrapper(*args, **kwargs):
        kwargs_test(kwargs,['where','what','which','whom','when','input','visu','input_field','option','tile','cursor_date'],
                'Bad args used in the pycoa.map() function.')
        which=''
        input_arg=kwargs.get('input',None)
        where=kwargs.get('where',None)
        what=kwargs.get('what',None)
        option = kwargs.get('option',None)

        input_field = None
        if isinstance(input_arg,pd.DataFrame):
            input_field=kwargs.get('input_field',input_field)
            kwargs={}
            kwargs['t']=input_arg
        elif input_arg==None:
            kwargs['t']=get(**kwargs,output='pandas')
        else:
            raise CoaTypeError('Waiting input as valid pycoa pandas '
                'dataframe. See help.')
        kwargs['input_field']=input_field
        return f(**kwargs)
    return wrapper

# ----------------------------------------------------------------------
# --- map(**kwargs) ----------------------------------------------------
# ----------------------------------------------------------------------

@deco_pycoa_graph
def map(**kwargs):
    """Create a map according to arguments and options.
    See help(hist).
    """
    visu = kwargs.get('visu',listvisu()[0])
    t=kwargs.pop('t')
    input_field=kwargs.pop('input_field')
    cursor_date=kwargs.get('cursor_date',None)

    if visu == 'bokeh':
        return show(_cocoplot.bokeh_map(t,input_field,**kwargs))
    elif visu == 'folium':
        return _cocoplot.map_folium(t,input_field,**kwargs)
    else:
        raise CoaTypeError('Waiting for a valid visualisation. So far: \'bokeh\' or \'folium\'.See help.')
