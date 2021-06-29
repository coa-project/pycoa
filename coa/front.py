# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - march 2021
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
    import coa.front as cf

    cf.plot(where='France')  # where keyword is mandatory
** getting recovered data for some countries **

    cf.get(where=['Spain','Italy'],which='recovered')
** listing available database and which data can be used **
    cf.listwhom()
    cf.setwhom('jhu') # return available keywords (aka 'which' data)
    cf.listwhich()   # idem
    cf.listwhat()    # return available time series type (weekly,
                     # daily...)
    cf.plot(option='sumall') # return the cumulative plot for all countries
                     # for default which keyword. See cf.listwhich() and
                     # and other cf.list**() function (see below)

"""

# --- Imports ----------------------------------------------------------
import pandas as pd
from functools import wraps
import numpy as np
from bokeh.io import show, output_notebook

from coa.tools import kwargs_test, extract_dates, get_db_list_dict, info
import coa.covid19 as coco
from coa.error import *
import coa._version

output_notebook(hide_banner=True)

# --- Needed global private variables ----------------------------------
_listwhom = list(get_db_list_dict().keys())

if 'coa_db' in __builtins__.keys():
    if not __builtins__['coa_db'] in _listwhom:
        raise CoaDbError("The variable __builtin__.coa_db set to " + str(__builtins__['coa_db']) +
                         " which is an invalid db. Error.")
    _whom = __builtins__['coa_db']
else:
    _whom = _listwhom[0]  # default base

_db, _cocoplot = coco.DataBase.factory(_whom)  # initialization with default

_listwhat = ['cumul',  # first one is default, nota:  we must avoid uppercases
             'daily',
             'weekly']

_listoutput = ['pandas','list', 'dict', 'array']  # first one is default for get

_listvisu = ['bokeh', 'folium']


# --- Front end functions ----------------------------------------------

# ----------------------------------------------------------------------
# --- getversion() -----------------------------------------------------
# ----------------------------------------------------------------------
def getversion():
    """Return the current running version of pycoa.
    """
    return coa._version.__version__


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
    r = _db.geo.get_region_list()
    if isinstance(r, list):
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
    global _whom, _db, _cocoplot
    if base not in listwhom():
        raise CoaDbError(base + ' is not a supported database. '
                                'See pycoa.listbase() for the full list.')
    if True:  # force the init #_whom != base:
        _db, _cocoplot = coco.DataBase.factory(base)
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

def getinfo(which):
    """
        Return keyword_definition for the db selected
    """
    #if not which:
        #which = listwhich()[0]
    #    print('Load default which:',which)
    #elif which not in listwhich():
    #    raise CoaKeyError('Which option ' + which + ' not supported. '
    #                                                'See listwhich() for list.')
    print(_db.get_keyword_definition(which),'\nurl:', _db.get_keyword_url(which)[0],'\n(more info ',_db.get_keyword_url(which)[1],')')

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
                'recovered' for 'jhu' default database). See listwhich() function
                for full list according to the used database.

    what   --   which data are computed, either in cumulative mode
                ('cumul', default value), or 'daily' (diff with previous day
                and 'weekly' (diff with previous week). See
                listwhich() for fullist of available
                Full list of what keyword with the listwhat() function.

    whom   --   Database specification (overload the setbase()
                function). See listwhom() for supported list

    when   --   dates are given under the format dd/mm/yyyy. In the when
                option, one can give one date which will be the end of
                the data slice. Or one can give two dates separated with
                ":", which will define the time cut for the output data
                btw those two dates.

    output --   output format returned ( pandas (default), array (numpy.array),
                dict or list). See listoutput() function.

    option --   pre-computing option.
                * nonneg means that negative daily balance is pushed back
                to previousdays in order to have a cumulative function which is
                monotonous increasing.
                * nofillnan means that nan value won't be filled.
                * smooth7 will perform a 7 day window average of data
                * sumall will return integrated over locations given via the
                where keyword, the data
                is available. By default : no option.
                See listoption().
    """
    kwargs_test(kwargs, ['where', 'what', 'which', 'whom', 'when', 'output', 'option', 'bins', 'title', 'visu', 'tile','dateslider','maplabel'],
                'Bad args used in the pycoa.get() function.')
    # no dateslider currently

    global _db, _whom
    where = kwargs.get('where', None)
    what = kwargs.get('what', listwhat()[0])
    which = kwargs.get('which', None)
    whom = kwargs.get('whom', None)
    option = kwargs.get('option', None)
    when = kwargs.get('when', None)

    output = kwargs.get('output', listoutput()[0])

    if output not in listoutput():
        raise CoaKeyError('Output option ' + output + ' not supported. See help().')

    if whom is None:
        whom = _whom
    if whom != _whom:
        setwhom(whom)
    when_beg, when_end = extract_dates(when)

    if not bool([s for s in listwhat() if what.startswith(s)]):
        raise CoaKeyError('What option ' + what + ' not supported. '
                                                  'See listwhat() for full list.')

    if not which:
        which = listwhich()[0]
    elif which not in listwhich():
        raise CoaKeyError('Which option ' + which + ' not supported. '
                                                    'See listwhich() for list.')
    pandy = _db.get_stats(which=which, location=where, option=option).rename(columns={'location': 'where'})
    db_first_date = pandy.date.min()
    db_last_date = pandy.date.max()
    if when_beg < db_first_date:
        when_beg = db_first_date
    if when_end > db_last_date:
        when_end = db_last_date
    # when cut
    pandy = pandy[(pandy.date >= when_beg) & (pandy.date <= when_end)]
    pandy.reset_index()
    # casted_data = None
    if output == 'pandas':
        pandy = pandy.drop(columns=['cumul'])
        pandy['cumul'] = pandy[which]
        casted_data = pandy
    # print(pandy)
    # casted_data = pd.pivot_table(pandy, index='date',columns='where',values=col_name).to_dict('series')
    # print(pandy)
    elif output == 'dict':
        casted_data = pandy.to_dict('split')
    elif output == 'list' or output == 'array':
        my_list = []
        for keys, values in pandy.items():
            vc = [i for i in values]
            my_list.append(vc)
        casted_data = my_list
        if output == 'array':
            casted_data = np.array(pandy)
    else:
        raise CoaKeyError('Unknown output.')
    return casted_data

def export(**kwargs):
    '''
    Export pycoas pandas as an output file selected by output argument
    'pandas': pycoa pandas
    'format': excel or csv
    '''
    global _db
    kwargs_test(kwargs, ['format','pandas'])
    pandy = kwargs.get('pandas', listwhat()[0])
    format = kwargs.get('format', 'excel')
    _db.export(pandas=pandy,format=format)


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
                    If specified should be a list of width and height. For instance width_height=[400,500]

        title       --  to force the title of the plot

        typeofplot  -- 'date' (default), 'menulocation' or 'versus'
                       'date':date plot
                       'menulocation': date plot with two scroll menu locations.
                                        Usefull to study the behaviour of a variable for two different countries.
                       'versus': plot variable against an other one.
                                 For this type of plot one should used 'input' and 'input_field' (not fully tested).
                                 Moreover dim(input_field) must be 2.

        """
        kwargs_test(kwargs, ['where', 'what', 'which', 'whom', 'when',
                             'input', 'input_field', 'width_height', 'title', 'option','typeofplot'],
                    'Bad args used in the pycoa.plot() function.')

        when = kwargs.get('when', None)
        input_field = None
        input_arg = kwargs.get('input', None)
        dateslider = kwargs.get('dateslider', None)
        typeofplot = kwargs.pop('typeofplot', 'date')

        if isinstance(input_arg, pd.DataFrame):
            t = input_arg
            input_field = kwargs.get('input_field', listwhich()[0])
            #if not all([i in t.columns for i in input_field]):
            if input_field not in t.columns:
                raise CoaKeyError("Cannot find " + str(input_field) + " field in the pandas data. "
                                                                      "Set a proper input_field key.")
            if 'option' in kwargs:
                raise CoaKeyError("Cannot use option with input pandas data. "
                                  "Use option within the get() function instead.")
            kwargs = {}
        elif input_arg == None:
            t = get(**kwargs, output='pandas')
            which = kwargs.get('which', listwhich()[0])
            what = kwargs.get('what', listwhat()[0])
            option = kwargs.get('option', None)
        else:
            raise CoaTypeError('Waiting input as valid pycoa pandas '
                               'dataframe. See help.')

        return func(t,input_field,typeofplot, **kwargs)
    return generic_plot

@decoplot
def plot(t,input_field,typeofplot, **kwargs):
    if typeofplot == 'date':
        fig = _cocoplot.pycoa_date_plot(t,input_field, **kwargs)
    elif typeofplot == 'versus':
        if input_field is not None and len(input_field) == 2:
            fig = _cocoplot.pycoa_plot(t, input_field,**kwargs)
        else:
            print('typeofplot is versus but dim(input_field)!=2, versus has not effect ...')
            fig = _cocoplot.pycoa_date_plot(t, input_field, **kwargs)
    elif typeofplot == 'menulocation':
        if input_field is not None and len(input_field) > 1:
            print('typeofplot is menulocation but dim(input_field)>1, menulocation has not effect ...')
        fig = _cocoplot.pycoa_scrollingmenu(t, **kwargs)
    else:
        raise CoaKeyError('Unknown typeofplot value. Should be date, versus or menulocation.')
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

    typeofhist  --  'bylocation' (default), 'byvalue' or pie

    bins        --  number of bins used, only available for 'byvalue' type of
                    histograms.
                    If none provided, a default value will be used.
    """

    # not currently supported : dateslider  -- boolean value. Caution : experimental feature.
    #               If True, add a date vertical cursor bar to the left of the figure
    #               to dislay histo/map to a particular date (default false)
    #               Warning : this coud be time consuming when one use it with map bokeh
    #               preferable to use this option with folium map
    # """
    kwargs_test(kwargs, ['where', 'what', 'which', 'whom', 'when', 'input', 'input_field', 'bins', 'title',
                         'typeofhist', 'option','dateslider'],
                'Bad args used in the pycoa.hist() function.')
    # no 'dateslider' currently

    when = kwargs.get('when', None)
    input_field = None
    input_arg = kwargs.get('input', None)
    typeofhist = kwargs.pop('typeofhist', 'bylocation')
    dateslider = kwargs.get('dateslider', None)

    if isinstance(input_arg, pd.DataFrame):
        t = input_arg
        input_field = kwargs.get('input_field', listwhich()[0])
        if input_field not in t.columns:
            raise CoaKeyError("Cannot find " + str(input_field) + " field in the pandas data. "
                                                                  "Set a proper input_field key.")
        if 'option' in kwargs:
            raise CoaKeyError("Cannot use option with input pandas data. "
                              "Use option within the get() function instead.")
        kwargs = {}
    elif input_arg == None:
        t = get(**kwargs, output='pandas')
        which = kwargs.get('which', listwhich()[0])
        what = kwargs.get('what', listwhat()[0])
        option = kwargs.get('option', None)
    else:
        raise CoaTypeError('Waiting input as valid pycoa pandas '
                           'dataframe. See help.')

    if dateslider is not None:
        del kwargs['dateslider']
        kwargs['cursor_date'] = dateslider

    if typeofhist == 'bylocation':
        if 'bins' in kwargs:
            raise CoaKeyError("The bins keyword cannot be set with histograms by location. See help.")
        fig = _cocoplot.pycoa_horizonhisto(t, input_field, **kwargs)
    elif typeofhist == 'byvalue':
        if dateslider:
            info('dateslider not implemented for typeofhist=\'byvalue\'.')
            fig = _cocoplot.pycoa_horizonhisto(t, input_field, **kwargs)
        else:
            fig = _cocoplot.pycoa_histo(t, input_field, **kwargs)
    elif typeofhist == 'pie':
        fig = _cocoplot.pycoa_pie(t, input_field, **kwargs)

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
        kwargs_test(kwargs,
                    ['where', 'what', 'which', 'whom', 'when', 'input', 'visu', 'input_field', 'option', 'tile','dateslider','maplabel'],
                    'Bad args used in the pycoa.map() function.')
        # no 'dateslider' currently.
        which = ''
        input_arg = kwargs.get('input', None)
        where = kwargs.get('where', None)
        what = kwargs.get('what', None)
        option = kwargs.get('option', None)

        input_field = None
        if isinstance(input_arg, pd.DataFrame):
            input_field = kwargs.get('input_field', listwhich()[0])
            if input_field not in input_arg.columns:
                raise CoaKeyError("Cannot find " + str(input_field) + " field in the pandas data. "
                                                                      "Set a proper input_field key.")
            if 'option' in kwargs:
                raise CoaKeyError("Cannot use option with input pandas data. "
                                  "Use option within the get() function instead.")
            kwargs = {}
            kwargs['t'] = input_arg
        elif input_arg == None:
            kwargs['t'] = get(**kwargs, output='pandas')
        else:
            raise CoaTypeError('Waiting input as valid pycoa pandas '
                               'dataframe. See help.')
        kwargs['input_field'] = input_field
        return f(**kwargs)

    return wrapper


# ----------------------------------------------------------------------
# --- map(**kwargs) ----------------------------------------------------
# ----------------------------------------------------------------------

@deco_pycoa_graph
def map(**kwargs):
    """
    Create a map according to arguments and options.
    See help(hist).
    - 2 types of visu are avalailable so far : bokeh or folium (see listvisu())
    by default visu='bokeh'
    - In the default case (i.e visu='bokeh') available option are :
        - dateslider=True: a date slider is called and displayed on the right part of the map
        - maplabel=True: value are displayed directly on the map
    """
    visu = kwargs.get('visu', listvisu()[0])
    t = kwargs.pop('t')
    input_field = kwargs.pop('input_field')
    dateslider = kwargs.get('dateslider', None)
    maplabel = kwargs.get('maplabel', None)

    if dateslider is not None:
        del kwargs['dateslider']
        kwargs['cursor_date'] = dateslider
    if maplabel is not None:
        del kwargs['maplabel']
        kwargs['maplabel'] = maplabel

    if visu == 'bokeh':
        return show(_cocoplot.pycoa_map(t, input_field, **kwargs))
    elif visu == 'folium':
        if dateslider or maplabel:
            raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
        return _cocoplot.pycoa_mapfolium(t, input_field, **kwargs)
    else:
        raise CoaTypeError('Waiting for a valid visualisation. So far: \'bokeh\' or \'folium\'.See help.')
