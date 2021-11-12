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
import types

from coa.tools import kwargs_test, extract_dates, get_db_list_dict, info
import coa.covid19 as coco
from coa.error import *
import coa._version
import coa.geo as coge

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
_gi = None

_dict_bypop = {'no':0,'100':100,'1k':1e3,'100k':1e5,'1M':1e6}

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

def listwhom(detailed=False):
    """Return the list of currently avalailable databases for covid19
     data in PyCoA.
     The first one is the default one.

     If detailed=True, gives information location of each given database.
    """
    try:
        if int(detailed):
            df = pd.DataFrame(get_db_list_dict())
            df = df.T.reset_index()
            df.index = df.index+1
            df = df.rename(columns={'index':'Database',0: "WW/iso3",1:'Granularité',2:'WW/Name'})
            return df
        else:
            return _db.get_available_database()
    except:
        raise CoaKeyError('Waiting for a boolean !')


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
    return _cocoplot.tiles_list()


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
# --- listwhere() ------------------------------------------------------
# ----------------------------------------------------------------------
def listwhere(clustered = False):
    """Get the list of available regions/subregions managed by the current database
    """
    def clust():
        r = _db.geo.get_region_list()
        if isinstance(r, list):
            return r
        else:
            return sorted(r['name_region'].to_list())

    if clustered:
        return clust()
    else:
        if _db.db_world == True:
            r = _db.geo.get_GeoRegion().get_countries_from_region('world')
            r = [_db.geo.to_standard(c)[0] for c in r]
        else:
            if get_db_list_dict()[_whom][1] == 'subregion':
                pan = _db.geo.get_subregion_list()
                r = list(pan.name_subregion.unique())
            else:
                r = clust()
        return r

# ----------------------------------------------------------------------
# --- listbypop() ------------------------------------------------------
# ----------------------------------------------------------------------

def listbypop():
    """Get the list of available population normalization
    """
    return list(_dict_bypop.keys())

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
                where keyword. If using double bracket notation, the sumall
                option is applied for each bracketed member of the where arg.

                By default : no option.
                See listoption().
    bypop --    normalize by population (if available for the selected database).
                * by default, 'no' normalization
                * can normalize by '100', '1k', '100k' or '1M'
    """
    kwargs_test(kwargs, ['where', 'what', 'which', 'whom', 'when', 'output', 'option', 'bins', 'title',\
                        'visu', 'tile','typeofplot','dateslider','maplabel','typeofhist','mode','bypop'],
                'Bad args used in the pycoa.get() function.')
    # no dateslider currently

    global _db, _whom, _gi
    where = kwargs.get('where', None)
    what = kwargs.get('what', listwhat()[0])
    which = kwargs.get('which', None)
    whom = kwargs.get('whom', None)
    option = kwargs.get('option', None)
    when = kwargs.get('when', None)
    if 'mode' in kwargs:
        kwargs.pop('mode')
    option = kwargs.get('option', None)
    bypop = kwargs.get('bypop','no')

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
    if bypop not in listbypop():
        raise CoaKeyError('The bypop arg should be selected in '+str(listbypop)+' only.')

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
    # manage pop norm if asked
    if bypop != 'no':
        if _db.db_world == True:
            if not isinstance(_gi,coa.geo.GeoInfo):
                _gi = coge.GeoInfo()
            pop_field='population'
            pandy=_gi.add_field(input=pandy,field=pop_field,geofield='codelocation')
        else:
            if not isinstance(_gi,coa.geo.GeoCountry):
                _gi=None
            else:
                if _gi.get_country() != _db.geo.get_country():
                    _gi=None

            if _gi == None :
                _gi = _db.geo
            pop_field='population_subregion'
            if pop_field not in _gi.get_list_properties():
                raise CoaKeyError('The population information not available for this country. No normalization possible')

            pandy=_gi.add_field(input=pandy,field=pop_field,input_key='codelocation')

        pandy[which+' per '+bypop]=pandy[which]/pandy[pop_field]*_dict_bypop[bypop]
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
# --- chartsinput_deco(f)
# ------  with wraps
# ----------  wrapper(*args, **kwargs)
#---------------------------------------
# ----------------------------------------------------------------------
def chartsinput_deco(f):
    '''
        Main decorator it mainly deals with arg testings
    '''
    @wraps(f)
    def wrapper(*args, **kwargs):
        '''
            wrapper dealing with arg testing
        '''
        kwargs_test(kwargs,
                    ['where', 'what', 'which', 'whom', 'when', 'input', 'input_field',\
                    'title','typeofplot','typeofhist','visu','tile','dateslider','maplabel','option','mode','bypop'],
                    'Bad args used in the pycoa function.')
        input_arg = kwargs.get('input', None)
        input_field = kwargs.get('input_field')
        where = kwargs.get('where', None)
        what = kwargs.get('what', None)
        option = kwargs.get('option', None)

        if isinstance(input_arg, pd.DataFrame):
            input_field = kwargs.get('input_field', listwhich()[0])
            #if input_field not in input_arg.columns:
            #    raise CoaKeyError("Cannot find " + str(input_field) + " field in the pandas data. "
            #                                                          "Set a proper input_field key.")
            if 'option' in kwargs:
                raise CoaKeyError("Cannot use option with input pandas data. "
                                  "Use option within the get() function instead.")
            kwargs['input'] = input_arg
        elif input_arg == None:
            kwargs['input'] = get(**kwargs,output='pandas')
            which = kwargs.get('which', listwhich()[0])
            what = kwargs.get('what', listwhat()[0])
            option = kwargs.get('option', None)
        else:
            raise CoaTypeError('Waiting input as valid pycoa pandas '
                               'dataframe. See help.')

        bypop=kwargs.pop('bypop','no')
        if bypop != 'no':
            kwargs['which']=which+' per '+bypop
            input_field=kwargs['which']
        kwargs['input_field'] = input_field
        when = kwargs.get('when', None)
        return f(**kwargs)

    return wrapper
# ----------------------------------------------------------------------
# --- map(**kwargs) ----------------------------------------------------
# ----------------------------------------------------------------------
@chartsinput_deco
def map(**kwargs):
    """
    Create a map according to arguments and options.
    See help(map).
    - 2 types of visu are avalailable so far : bokeh or folium (see listvisu())
    by default visu='bokeh'
    - In the default case (i.e visu='bokeh') available option are :
        - dateslider=True: a date slider is called and displayed on the right part of the map
        - maplabel = text, value are displayed directly on the map
                   = spark, sparkline are displayed directly on the map
    """
    visu = kwargs.get('visu', listvisu()[0])
    input = kwargs.pop('input')
    input_field = kwargs.pop('input_field')
    dateslider = kwargs.get('dateslider', None)
    maplabel = kwargs.get('maplabel', None)
    sparkline = False
    if dateslider is not None:
        del kwargs['dateslider']
        kwargs['cursor_date'] = dateslider
    if maplabel is not None:
        kwargs['maplabel'] = False
        if maplabel == 'text':
            kwargs['maplabel'] = True
        elif maplabel == 'spark':
            sparkline = True
        else:
            raise CoaTypeError('Waiting for a valide label visualisation: text or spark')

    if visu == 'bokeh':
        if sparkline == False:
            return show(_cocoplot.pycoa_map(input, input_field, **kwargs))
        else:
            return show(_cocoplot.pycoa_sparkmap(input, input_field, **kwargs))
    elif visu == 'folium':
        if dateslider or maplabel:
            raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
        return _cocoplot.pycoa_mapfolium(input, input_field, **kwargs)
    else:
        raise CoaTypeError('Waiting for a valid visualisation. So far: \'bokeh\' or \'folium\'.See help.')
# ----------------------------------------------------------------------
# --- hist(**kwargs) ---------------------------------------------------
# ----------------------------------------------------------------------
@chartsinput_deco
def hist(**kwargs):
    """
    Create histogram according to arguments.
    See help(hist).
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
    input = kwargs.pop('input')
    input_field = kwargs.pop('input_field')
    dateslider = kwargs.get('dateslider', None)
    typeofhist = kwargs.pop('typeofhist', 'bylocation')

    if dateslider is not None:
        del kwargs['dateslider']
        kwargs['cursor_date'] = dateslider

    if typeofhist == 'bylocation':
        if 'bins' in kwargs:
            raise CoaKeyError("The bins keyword cannot be set with histograms by location. See help.")
        fig = _cocoplot.pycoa_horizonhisto(input, input_field, **kwargs)
    elif typeofhist == 'byvalue':
        if dateslider:
            info('dateslider not implemented for typeofhist=\'byvalue\'.')
            fig = _cocoplot.pycoa_horizonhisto(input, input_field, **kwargs)
        else:
            fig = _cocoplot.pycoa_histo(input, input_field, **kwargs)
    elif typeofhist == 'pie':
        fig = _cocoplot.pycoa_pie(input, input_field, **kwargs)

    else:
        raise CoaKeyError('Unknown typeofhist value. Should be bylocation or byvalue.')
    show(fig)

# ----------------------------------------------------------------------
# --- plot(**kwargs) ---------------------------------------------------
# ----------------------------------------------------------------------
@chartsinput_deco
def plot(**kwargs):
    """
    Create a date plot according to arguments. See help(plot).
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
    input = kwargs.pop('input')
    input_field = kwargs.pop('input_field')
    typeofplot = kwargs.get('typeofplot', 'date')

    if 'typeofplot' in kwargs:
        typeofplot = kwargs.pop('typeofplot')

    if typeofplot == 'date':
        fig = _cocoplot.pycoa_date_plot(input,input_field, **kwargs)
    elif typeofplot == 'versus':
        if input_field is not None and len(input_field) == 2:
            fig = _cocoplot.pycoa_plot(input, input_field,**kwargs)
        else:
            print('typeofplot is versus but dim(input_field)!=2, versus has not effect ...')
            fig = _cocoplot.pycoa_date_plot(input, input_field, **kwargs)
    elif typeofplot == 'menulocation':
        if input_field is not None and len(input_field) > 1:
            print('typeofplot is menulocation but dim(input_field)>1, menulocation has not effect ...')
        fig = _cocoplot.pycoa_scrollingmenu(input, input_field, **kwargs)
    else:
        raise CoaKeyError('Unknown typeofplot value. Should be date, versus or menulocation.')
    show(fig)
