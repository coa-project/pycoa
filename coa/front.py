# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - november 2023
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
    cf.setwhom('jhu',reload=True) # return available keywords (aka 'which' data), reload DB is True by default
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
from bokeh.io import (
    show,
    output_notebook,
)
import datetime as dt
from coa.tools import (
    kwargs_test,
    extract_dates,
    info,
    flat_list,
)
import coa.display as display
import coa.covid19 as coco
from coa.error import *
import coa._version
import coa.geo as coge
from coa.dbparser import _db_list_dict
import geopandas as gpd
output_notebook(hide_banner=True)

class Front:
    """
    Front class
    FrontEnd
    """
    def __init__(self,):
        self._listwhom = list(_db_list_dict.keys())
        self._gi = coge.GeoInfo()
        self._dict_bypop = {'no':0,'100':100,'1k':1e3,'100k':1e5,'1M':1e6,'pop':1.}
        self._listwhat = [ 'standard', 'daily', 'weekly']
        self._listoutput = ['pandas','geopandas','list', 'dict', 'array']  # first one is default for get
        self._listvisu = ['bokeh', 'folium', 'seaborn','mplt']
        self._listhist = ['bylocation','byvalue','pie']
        self._listplot = ['date','menulocation','versus','spiral','yearly']
        self._listmaplabel = ['text','textinteger','spark','spiral','label%','log','unsorted','exploded','dense']
        self._listoption = ['nonneg', 'nofillnan', 'smooth7', 'sumall']
        self._listallkargs = ['where', 'what', 'which', 'whom','reload','when', 'input', 'input_field','output',\
             'title','typeofplot','typeofhist','bins','tile','dateslider','maplabel','option',\
             'mode','guideline','bypop', 'plot_width','plot_height','textcopyright','cursor_date']
        self._db = ''
        self._whom = ''
        self.vis = 'bokeh'
        self._cocoplot = None


    def setvisu(self,visu):
        vis=self._listvisu
        if visu not in vis:
            raise CoaError("Sorry but " + visu + " visualisation isn't implemented ")
        else:
            self.vis = visu
            if not self._cocoplot is None:
                    self._cocoplot.setvisu(visu)
            print('Visu has been set to ', visu)

    def getvisu(self,):
        return self.vis
    # ----------------------------------------------------------------------
    # --- getversion() -----------------------------------------------------
    # ----------------------------------------------------------------------
    def getversion(self,):
        """Return the current running version of pycoa.
        """
        return coa._version.__version__
    # ----------------------------------------------------------------------
    # --- listoutput() -----------------------------------------------------
    # ----------------------------------------------------------------------
    def listoutput(self,):
        """Return the list of currently available output types for the
        get() function. The first one is the default output given if
        not specified.
        """
        return self._listoutput
    # ----------------------------------------------------------------------
    # --- listvisu() -------------------------------------------------------
    # ----------------------------------------------------------------------
    def listvisu(self,):
        """Return the list of currently available visualization for the
        map() function. The first one is the default output given if
        not specified.
        """
        return self._listvisu
    # ----------------------------------------------------------------------
    # --- listwhom() -------------------------------------------------------
    # ----------------------------------------------------------------------
    def listwhom(self, detailed = False):
        """Return the list of currently avalailable databases for covid19
         data in PyCoA.
         The first one is the default one.

         If detailed=True, gives information location of each given database.
        """
        df = pd.DataFrame(_db_list_dict)
        df = df.T.reset_index()
        df.index = df.index+1
        df = df.rename(columns={'index':'Database',0: "WW/iso3",1:'Granularité',2:'WW/Name'})
        df = df.sort_values(by='Database').reset_index(drop=True)
        try:
            if int(detailed):
                df = (df.style.set_table_styles([{'selector' : '','props' : [('border','3px solid green')]}]))
                print("Pandas has been pimped, use '.data' to get a pandas dataframe")
                return df
            else:
                return list(df['Database'])
        except:
            raise CoaKeyError('Waiting for a boolean !')
    # --- listwhat() -------------------------------------------------------
    # ----------------------------------------------------------------------
    def listwhat(self,):
        """Return the list of currently avalailable type of series available.
         The first one is the default one.
        """
        return self._listwhat
    # ----------------------------------------------------------------------
    # --- listhist() -------------------------------------------------------
    # ----------------------------------------------------------------------
    def listhist(self,):
        """Return the list of currently avalailable type of hist available.
         The first one is the default one.
        """
        return self._listhist
    # ----------------------------------------------------------------------
    # --- listplot() -------------------------------------------------------
    # ----------------------------------------------------------------------
    def listplot(self,):
        """Return the list of currently avalailable type of plots available.
         The first one is the default one.
        """
        return self._listplot
    # ----------------------------------------------------------------------
    # --- listoption() -----------------------------------------------------
    # ----------------------------------------------------------------------
    def listoption(self,):
        """Return the list of currently avalailable option apply to data.
         Default is no option.
        """
        return self._listoption

    # ----------------------------------------------------------------------
    # --- listallkargs() -----------------------------------------------------
    # ----------------------------------------------------------------------
    def listallkargs(self,):
        """Return the list of currently avalailable kargs
        """
        return self._listallkargs
    # ----------------------------------------------------------------------
    # --- listtile() -------------------------------------------------------
    # ----------------------------------------------------------------------
    def listtile(self,):
        """Return the list of currently avalailable tile option for map()
         Default is the first one.
        """
        return self._cocoplot.tiles_list()
    # ----------------------------------------------------------------------
    # --- listwhich() ------------------------------------------------------
    # ----------------------------------------------------------------------
    def listwhich(self,):
        """Get which are the available fields for the current base.
        Output is a list of string.
        By default, the listwhich()[0] is the default which field in other
        functions.
        """
        return sorted(self._db.get_parserdb().get_available_keywords())
    # ----------------------------------------------------------------------
    # --- listwhere() ------------------------------------------------------
    # ----------------------------------------------------------------------
    def listwhere(self,clustered = False):
        """Get the list of available regions/subregions managed by the current database
        """
        def clust():
            if _db_list_dict[self._whom][1] == 'nation' and _db_list_dict[self._whom][2] not in ['World','Europe']:
                return  self._db.geo.to_standard(_db_list_dict[_whom][0])
            else:
                r = self._db.geo.get_region_list()
                if not isinstance(r, list):
                    r=sorted(r['name_region'].to_list())
                r.append(_db_list_dict[self._whom][2])
                if _db_list_dict[self._whom][2] == 'Europe':
                    r.append('European Union')
                return r
        if _db_list_dict[self._whom][1] == 'nation' and _db_list_dict[self._whom][2] not in ['World','Europe']:
            return [ _db_list_dict[self._whom][2] ]
        if clustered:
            return clust()
        else:
            if self._db.db_world == True:
                if _db_list_dict[self._whom][1] == 'nation' and _db_list_dict[self._whom][2] not in ['World','Europe']:
                    r =  _db.geo.to_standard(_db_list_dict[self._whom][0])
                else:
                    if _db_list_dict[self._whom][2]=='World':
                        r = self._db.geo.get_GeoRegion().get_countries_from_region('world')
                    else:
                        r = self._db.geo.get_GeoRegion().get_countries_from_region('europe')
                    r = [self._db.geo.to_standard(c)[0] for c in r]
            else:
                if _db_list_dict[self._whom][1] == 'subregion':
                    pan = self._db.geo.get_subregion_list()
                    r = list(pan.name_subregion.unique())
                elif _db_list_dict[self._whom][1] == 'region':
                    r = clust()
                    r.append(_db_list_dict[self._whom][2])
                else:
                    raise CoaKeyError('What is the granularity of your DB ?')
            return r
    # ----------------------------------------------------------------------
    # --- listbypop() ------------------------------------------------------
    # ----------------------------------------------------------------------
    def listbypop(self):
        """Get the list of available population normalization
        """
        return list(self._dict_bypop.keys())
    # ----------------------------------------------------------------------
    # --- listmaplabel() ------------------------------------------------------
    # ----------------------------------------------------------------------
    def listmaplabel(self):
        """Get the list of available population normalization
        """
        return self._listmaplabel
    # ----------------------------------------------------------------------
    # --- setwhom() --------------------------------------------------------
    # ----------------------------------------------------------------------
    def setwhom(self,base,**kwargs):
        """Set the covid19 database used, given as a string.
        Please see pycoa.listbase() for the available current list.

        By default, the listbase()[0] is the default base used in other
        functions.
        """
        #kwargs_test(kwargs, ['reload'], 'Bad args used in the pycoa.saveoutput function.')
        reload = kwargs.get('reload', True)
        visu = True
        if reload not in [0,1]:
            raise CoaError('reload must be a boolean ... ')
        if base not in self.listwhom():
            raise CoaDbError(base + ' is not a supported database. '
                                    'See pycoa.listbase() for the full list.')
        else:
            if reload:
                self._db, self._cocoplot = coco.DataBase.factory(db_name=base,reload=reload)
            else:
                self._db = coco.DataBase.readpekl('.cache/'+base+'.pkl')
                pandy = self._db.getwheregeometrydescription()
                self._cocoplot = display.Display(base, pandy)
                self._cocoplot.setvisu(self.getvisu())
                coge.GeoManager('name')
        self._whom = base
    # ----------------------------------------------------------------------
    # --- getwhom() --------------------------------------------------------
    # ----------------------------------------------------------------------
    def getwhom(self,return_error=True):
        """Return the current base which is used
        """
        return self._whom

    # ----------------------------------------------------------------------
    # --- get(**kwargs) ----------------------------------------------------
    # ----------------------------------------------------------------------
    def getkeywordinfo(self, which=None):
        """
            Return keyword_definition for the db selected
        """
        if which:
            if which in self.listwhich():
                print(self._db.get_parserdb().get_keyword_definition(which))
                print('Parsed from this url:',self._db.get_parserdb().get_keyword_url(which))
            else:
                raise CoaKeyError('This value do not exist please check.'+'Available variable so far in this db ' + str(listwhich()))
        else:
            df = self._db.get_parserdb().get_dbdescription()
            return df

    def getrawdb(self, **kwargs):
        """
            Return the main pandas i.e with all the which values loaded from the database selected
        """
        col = list(self._db.get_fulldb().columns)
        mem='{:,}'.format(self._db.get_fulldb()[col].memory_usage(deep=True).sum())
        info('Memory usage of all columns: ' + mem + ' bytes')
        df = self._db.get_fulldb(**kwargs)
        return df
    # ----------------------------------------------------------------------
    # --- Normalisation by pop input pandas return pandas whith by pop new column
    # ---------------------------------------------------------------------
    def normbypop(self, pandy, val2norm,bypop):
        """
            Return a pandas with a normalisation column add by population
            * can normalize by '100', '1k', '100k' or '1M'
        """
        if pandy.empty:
            raise CoaKeyError('Seems to be an empty field')
        if isinstance(pandy['codelocation'].iloc[0],list):
            pandy = pandy.explode('codelocation')

        if self._db.db_world == True:
            pop_field='population'
            pandy = self._gi.add_field(input=pandy,field=pop_field,geofield='codelocation')
        else:
            if not isinstance(self._gi,coa.geo.GeoCountry):
                self._gi=None
            else:
                if self._gi.get_country() != self._db.geo.get_country():
                    self._gi=None

            if self._gi == None :
                self._gi = self._db.geo
            pop_field='population_subregion'
            if pop_field not in self._gi.get_list_properties():
                raise CoaKeyError('The population information not available for this country. No normalization possible')

            pandy=self._gi.add_field(input=pandy,field=pop_field,input_key='codelocation')

        clust = pandy['clustername'].unique()
        df = pd.DataFrame()
        for i in clust:
            pandyi = pandy.loc[ pandy['clustername'] == i ].copy()
            pandyi.loc[:,pop_field] = pandyi.groupby('codelocation')[pop_field].first().sum()
            if len(pandyi.groupby('codelocation')['codelocation'].first().tolist()) == 1:
                cody = pandyi.groupby('codelocation')['codelocation'].first().tolist()*len(pandyi)
            else:
                cody = [pandyi.groupby('codelocation')['codelocation'].first().tolist()]*len(pandyi)
            pandyi = pandyi.assign(codelocation=cody)
            if df.empty:
                df = pandyi
            else:
                df = pd.concat([df,pandyi])

        df = df.drop_duplicates(['date','clustername'])
        pandy = df

        pandy=pandy.copy()
        pandy[pop_field]=pandy[pop_field].replace(0., np.nan)
        if bypop == 'pop':
            pandy.loc[:,val2norm+' per total population']=pandy[val2norm]/pandy[pop_field]*self._dict_bypop[bypop]
        else:
            pandy.loc[:,val2norm+' per '+bypop + ' population']=pandy[val2norm]/pandy[pop_field]*self._dict_bypop[bypop]
        return pandy
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
        def wrapper(self,**kwargs):
            '''
                wrapper dealing with arg testing
            '''
            if self._db == '':
                self._db, self._cocoplot = coco.DataBase.factory(db_name = self._whom)

                kwargs_test(kwargs,self._listallkargs,'Bad args used ! please check your '+kwargs)

            where = kwargs.get('where', None)
            which = kwargs.get('which', None)
            what = kwargs.get('what', None)

            whom = kwargs.get('whom', None)
            option = kwargs.get('option', None)
            when = kwargs.get('when', None)
            input_arg = kwargs.get('input', None)
            input_field = kwargs.get('input_field',None)

            if (option != None or what != None) and (isinstance(input_field,list) or isinstance(which,list)):
                raise CoaKeyError('option/what not compatible when input_fied/which is a list')

            if 'input_field' not in kwargs:
                which = input_field
            else:
                which = kwargs['input_field']

            if what:
                if what not in self.listwhat():
                    raise CoaKeyError('What option ' + what + ' not supported. '
                                                              'See listwhat() for full list.')
                if 'what'=='sandard':
                    what = which
            else:
                what = self._listwhat[0]

            option = kwargs.get('option', None)
            bypop = kwargs.get('bypop','no')

            kwargs['output'] = kwargs.get('output', self.listoutput()[0])

            if kwargs['output'] not in self.listoutput():
                raise CoaKeyError('Output option ' + kwargs['output'] + ' not supported. See help().')
            if whom is None:
                whom = self._whom
            if whom != self._whom:
                setwhom(whom)

            if bypop not in self.listbypop():
                raise CoaKeyError('The bypop arg should be selected in '+str(self.listbypop())+' only.')
            if isinstance(input_arg, pd.DataFrame) or isinstance(which, list):
                if input_arg is not None and not input_arg.empty:
                    pandy = input_arg
                    pandy = self._db.get_stats(**kwargs)
                else:
                    pandy=pd.DataFrame()
                    input_field = which
                    for k,i in enumerate(which):
                        tmp = self._db.get_stats(input_field=input_field, which=i, where=where, option=option)
                        if pandy.empty:
                            pandy = tmp
                        else:
                            tmp = tmp.drop(columns=['daily','weekly','codelocation','clustername'])
                        pandy = pd.merge(pandy, tmp, on=['date','where'])
                    input_arg = pandy
                if bypop != 'no':
                    input_arg = self.normbypop(pandy,input_field,bypop)
                    if bypop=='pop':
                        input_field = input_field+' per total population'
                    else:
                        input_field = input_field+' per '+ bypop + ' population'
                    pandy = input_arg

                if isinstance(input_field,list):
                    which = input_field[0]
                #else:
                #    which = input_field
                #if which is None:
                #    which = pandy.columns[2]

                pandy.loc[:,'standard'] = pandy[which]
                if 'input_field' not in kwargs:
                    kwargs['input_field'] = input_field
                #if option:
                #    print('option has no effect here, please try do it when you construct your input pandas ')
            elif input_arg == None :
                #kwargs.pop('input_field')
                pandy = self._db.get_stats(**kwargs)
                if which != None:
                    pandy['standard'] = pandy[which]
                else:
                    pandy['standard'] = pandy[pandy.columns[2]]
                    which = list(pandy.columns)[2]
                input_field = what

                if pandy[[which,'date']].isnull().values.all():
                    info('--------------------------------------------')
                    info('All values for '+ which + ' is nan nor empty')
                    info('--------------------------------------------')
                    pandy['date']=len(where)*[dt.date(2020,1,1),dt.date.today()]
                    lwhere=flat_list([[i,i] for i in where])
                    pandy['where']=lwhere
                    pandy['clustername']=lwhere
                    pandy['codelocation']=len(pandy)*['000']
                    pandy=pandy.fillna(0)
                    bypop = 'no'
                if bypop != 'no':
                    if what:
                        val = what
                    else:
                        val = _listwhat[0]
                    pandy = self.normbypop(pandy , val, bypop)
                    if bypop=='pop':
                        input_field = input_field+' per total population'
                    else:
                        input_field = input_field+' per '+ bypop + ' population'
                kwargs['input_field'] = input_field
                option = kwargs.get('option', None)
            else:
                raise CoaTypeError('Waiting input as valid pycoa pandas '
                                   'dataframe. See help.')
            when_beg, when_end = extract_dates(when)

            if pandy[[which,'date']].isnull().values.all():
                info('--------------------------------------------')
                info('All values for '+ which + ' is nan nor empty')
                info('--------------------------------------------')
                pandy['date']=len(where)*[dt.date(2020,1,1),dt.date.today()]
                lwhere=flat_list([[i,i] for i in where])
                pandy['where']=lwhere
                pandy['clustername']=lwhere
                pandy['codelocation']=len(pandy)*['000']
                pandy=pandy.fillna(0)
                bypop = 'no'

            db_first_date = pandy[[which,'date']].date.min()
            db_last_date = pandy[[which,'date']].date.max()

            if when_beg < db_first_date:
                when_beg = db_first_date

            if when_end > db_last_date:
                when_end = db_last_date

            if when_end < db_first_date:
                raise CoaNoData("No available data before "+str(db_first_date))
            # when cut
            if when_beg >  pandy[[which,'date']].date.max() or when_end >  pandy[[which,'date']].date.max():
                raise CoaNoData("No available data after "+str( pandy[[which,'date']].date.max()))
            pandy = pandy[(pandy.date >= when_beg) & (pandy.date <= when_end)]
            if bypop != 'no':
                kwargs['input_field'] = [i for i in pandy.columns if ' per ' in i]
                #name = [i for i in list(pandy.columns) if ' per ' in i]
                if bypop=='pop':
                    bypop='total population'
                else:
                    bypop+=' population'
                if 'tot_' and not what or what=='standard':
                    renamed = which + ' per '+ bypop
                else:
                    renamed = which + ' '+ what +' per '+ bypop
                pandy = pandy.rename(columns={kwargs['input_field'][0]:renamed})
                kwargs['input_field'] = renamed
                pass
            else:
                if not input_field or input_field == 'standard':
                    kwargs['input_field'] = pandy.columns[2]
            kwargs['input'] = pandy
            return f(self,**kwargs)
        return wrapper
    # ----------------------------------------------------------------------
    # --- get(**kwargs) ----------------------------------------------------
    # ----------------------------------------------------------------------
    @chartsinput_deco
    def get(self,**kwargs):
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

        what   --   which data are computed, either in standard mode
                    ('standard', default value), or 'daily' (diff with previous day
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
        output = kwargs.get('output')
        pandy = kwargs.get('input')
        input_field  = kwargs.get('input_field')
        pandy = pandy.drop(columns='standard')
        if output == 'pandas':
            def color_df(val):
                if val.columns=='date':
                    return 'blue'
                elif val.columns=='where':
                    return 'red'
                else:
                    return black
            #if 'option' in kwargs:
            #    raise CoaKeyError("Cannot use option with input pandas data. "
            #                      "Use option within the get() function instead.")
            #pandy = pandy.drop_duplicates(['date','clustername'])
            #pandy = pandy.drop(columns=['cumul'])
            #pandy['cumul'] = pandy[which]
            casted_data = pandy
            col=list(casted_data.columns)
            mem='{:,}'.format(casted_data[col].memory_usage(deep=True).sum())
            info('Memory usage of all columns: ' + mem + ' bytes')

        elif output == 'geopandas':
            casted_data = pd.merge(pandy, self._db.getwheregeometrydescription(), on='where')
            casted_data=gpd.GeoDataFrame(casted_data)
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

    def saveoutput(self,**kwargs):
        '''
            Export pycoas pandas as an output file selected by output argument
            'pandas': pandas to save
            'saveformat': excel (default) or csv
            'savename': None (default pycoaout+ '.xlsx/.csv')
        '''
        global _db
        kwargs_test(kwargs, ['pandas','saveformat','savename'], 'Bad args used in the pycoa.saveoutput function.')
        pandy = kwargs.get('pandas', pd.DataFrame())
        saveformat = kwargs.get('saveformat', 'excel')
        savename = kwargs.get('savename', '')
        if pandy.empty:
            raise CoaKeyError('Pandas to save is mandatory there is not default !')
        else:
            _db.saveoutput(pandas=pandy,saveformat=saveformat,savename=savename)

    def merger(self,**kwargs):
        '''
        Merge two or more pycoa pandas from get_stats operation
        'coapandas': list (min 2D) of pandas from stats
        'whichcol': list variable associate to the coapandas list to be retrieve
        '''
        global _db
        kwargs_test(kwargs,['coapandas'], 'Bad args used in the pycoa.merger function.')
        listpandy = kwargs.get('coapandas',[])
        return _db.merger(coapandas = listpandy)

    # ----------------------------------------------------------------------
    # --- map(**kwargs) ----------------------------------------------------
    # ----------------------------------------------------------------------
    def decomap(func):
        def inner(self,**kwargs):
            """
            Create a map according to arguments and options.
            See help(map).
            - 2 types of visu are avalailable so far : bokeh or folium (see listvisu())
            by default visu='bokeh'
            - In the default case (i.e visu='bokeh') available option are :
                - dateslider=True: a date slider is called and displayed on the right part of the map
                - maplabel = text, values are displayed directly on the map
                           = textinter, values as an integer are displayed directly on the map
                           = spark, sparkline are displayed directly on the map
                           = spiral, spiral are displayed directly on the map
                           = label%, label are in %
                           = exploded/dense, when available exploded/dense map geometry (for USA & FRA sor far)
            """
            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            if not input.empty:
                kwargs.pop('input')
                kwargs.pop('input_field')
            if 'output' in kwargs:
                kwargs.pop('output')
            if 'bypop' in kwargs:
                kwargs.pop('bypop')

            dateslider = kwargs.get('dateslider', None)
            maplabel = kwargs.get('maplabel', None)
            listmaplabel=self._listmaplabel
            if maplabel is not None:
                if not isinstance(maplabel,list):
                    maplabel = [maplabel]
                if  [a for a in maplabel if a not in listmaplabel]:
                    raise CoaTypeError('Waiting a correct maplabel value. See help.')
            sparkline = False
            if dateslider is not None:
                del kwargs['dateslider']
                kwargs['cursor_date'] = dateslider
            if maplabel is not None:
                kwargs['maplabel'] = []
                if 'text' in maplabel:
                    kwargs['maplabel'] = ['text']
                if 'textinteger' in maplabel:
                    kwargs['maplabel'] = ['textinteger']
                for i in listmaplabel:
                    if i in maplabel and i not in ['text','textinteger']:
                        kwargs['maplabel'].append(i)
                #if all([ True if i in ['text','spark','label%','log'] else False for i in kwargs['maplabel'] ]) :
                #    CoaKeyError('Waiting for a valide label visualisation: text, spark or label%')
                input.loc[:,input_field]=input[input_field].fillna(0) #needed in the case where there are nan else js pb

            return func(self,input,input_field,**kwargs)
        return inner

    @chartsinput_deco
    @decomap
    def figuremap(self,input,input_field,**kwargs):
        dateslider = kwargs.get('dateslider', None)
        maplabel = kwargs.get('maplabel', None)
        if visu == 'bokeh':
            if maplabel:
                if 'spark' in maplabel or 'spiral' in maplabel:
                    return self._cocoplot.pycoa_pimpmap(input,input_field,**kwargs)
                elif 'text' or 'exploded' or 'dense' in maplabel:
                    return self._cocoplot.pycoa_map(input,input_field,**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                return self._cocoplot.pycoa_map(input,input_field,**kwargs)

    @chartsinput_deco
    @decomap
    def map(self,input,input_field,**kwargs):
        dateslider = kwargs.get('dateslider', None)
        maplabel = kwargs.get('maplabel', None)
        visu = self.getvisu()
        if visu == 'bokeh':
            if maplabel:
                if 'spark' in maplabel or 'spiral' in maplabel:
                    fig = self._cocoplot.pycoa_pimpmap(input,input_field,**kwargs)
                elif 'text' or 'exploded' or 'dense' in maplabel:
                    fig = self._cocoplot.pycoa_map(input,input_field,**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                fig = self._cocoplot.pycoa_map(input,input_field,**kwargs)
            if self.getvisu()=='bokeh':
                return show(fig)
            else:
                return fig
        elif visu == 'folium':
            if dateslider is not None :
                raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
            if  maplabel and set(maplabel) != set(['log']):
                raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
            return self._cocoplot.pycoa_mapfolium(input,input_field,**kwargs)
        else:
            raise CoaTypeError('Waiting for a valid visualisation. So far: \'bokeh\' or \'folium\'.See help.')

    # ----------------------------------------------------------------------
    # --- hist(**kwargs) ---------------------------------------------------
    # ----------------------------------------------------------------------
    def decohist(func):
        def inner(self,**kwargs):
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
                            Default is 'deaths/standard', the default output field of
                            the get() function.

            width_height : width and height of the picture .
                        If specified should be a list of width and height.
                        For instance width_height=[400,500]

            typeofhist  --  'bylocation' (default), 'byvalue' or pie

            bins        --  number of bins used, only available for 'byvalue' type of
                            histograms.
                            If none provided, a default value will be used.
            """
            #input = kwargs.pop('input')
            #input_field = kwargs.pop('input_field')
            dateslider = kwargs.get('dateslider', None)
            typeofhist = kwargs.pop('typeofhist',self.listhist()[0])
            kwargs.pop('output')
            if kwargs.get('bypop'):
              kwargs.pop('bypop')

            if dateslider is not None:
                del kwargs['dateslider']
                kwargs['cursor_date'] = dateslider

            if typeofhist == 'bylocation':
                if 'bins' in kwargs:
                    raise CoaKeyError("The bins keyword cannot be set with histograms by location. See help.")

                fig = self._cocoplot.pycoa_horizonhisto(**kwargs)
            elif typeofhist == 'byvalue':
                if dateslider:
                    info('dateslider not implemented for typeofhist=\'byvalue\'.')
                    fig = self._cocoplot.pycoa_horizonhisto(**kwargs)
                else:
                    fig = self._cocoplot.pycoa_histo( **kwargs)
            elif typeofhist == 'pie':
                fig = self._cocoplot.pycoa_pie(**kwargs)
            else:
                raise CoaKeyError('Unknown typeofhist value. Available value : listhist().')
            return func(self,fig)
        return inner

    @chartsinput_deco
    @decohist
    def figurehist(fig):
        ''' Return fig Bohek object '''
        return fig

    @chartsinput_deco
    @decohist
    def hist(self,fig):
        ''' show hist '''
        if self._cocoplot.getvisu() == 'bokeh':
            show(fig)
        else:
            fig

    # ----------------------------------------------------------------------
    # --- plot(**kwargs) ---------------------------------------------------
    # ----------------------------------------------------------------------
    def decoplot(func):
        def inner(self,**kwargs):
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
                            Default is 'deaths/standard', the default output field of
                            the get() function.

            width_height : width and height of the picture .
                        If specified should be a list of width and height. For instance width_height=[400,500]

            title       --  to force the title of the plot

            textcopyright - to force the copyright lower left of the graph

            typeofplot  -- 'date' (default), 'menulocation' or 'versus'
                           'date':date plot
                           'spiral': spiral plot if several location only the first one
                           'menulocation': date plot with two scroll menu locations.
                                            Usefull to study the behaviour of a variable for two different countries.
                           'versus': plot variable against an other one.
                                     For this type of plot one should used 'input' and 'input_field' (not fully tested).
                                     Moreover dim(input_field) must be 2.
                            'spiral' : plot variable as a spiral angular plot, angle being the date
                            'yearly' : same as date but modulo 1 year

            guideline add a guideline for the plot. False by default
            """
            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            if not input.empty:
                kwargs.pop('input')
                kwargs.pop('input_field')
            typeofplot = kwargs.get('typeofplot',self.listplot()[0])
            kwargs.pop('output')
            if kwargs.get('bypop'):
                kwargs.pop('bypop')

            if 'typeofplot' in kwargs:
                typeofplot = kwargs.pop('typeofplot')
            if typeofplot == 'date':
                fig = self._cocoplot.pycoa_date_plot(input, input_field,**kwargs)
            elif typeofplot == 'spiral':
                fig = self._cocoplot.pycoa_spiral_plot(input, input_field,**kwargs)
            elif typeofplot == 'versus':
                if isinstance(input_field,list) and len(input_field) == 2:
                    fig = self._cocoplot.pycoa_plot(**kwargs)
                else:
                    print('typeofplot is versus but dim(input_field)!=2, versus has not effect ...')
                    fig = self._cocoplot.pycoa_date_plot(input, input_field,**kwargs)
            elif typeofplot == 'menulocation':
                if _db_list_dict[self._whom][1] == 'nation' and _db_list_dict[self._whom][2] != 'World':
                    print('typeofplot is menulocation with a national DB granularity, use date plot instead ...')
                    fig = self._cocoplot.pycoa_date_plot(input, input_field,*kwargs)
                else:
                    if isinstance(input_field,list) and len(input_field) > 1:
                        print('typeofplot is menulocation but dim(input_field)>1, menulocation has not effect ...')
                    fig = self._cocoplot.pycoa_scrollingmenu(input, input_field,**kwargs)
            elif typeofplot == 'yearly':
                if input.date.max()-input.date.min() <= dt.timedelta(days=365):
                    print("Yearly will not be used since the time covered is less than 1 year")
                    fig = self._cocoplot.pycoa_date_plot(input, input_field,**kwargs)
                else:
                    fig = self._cocoplot.pycoa_yearly_plot(input, input_field,**kwargs)
            else:
                raise CoaKeyError('Unknown typeofplot value. Should be date, versus, menulocation, spiral or yearly.')
            return func(self,fig)
        return inner

    @chartsinput_deco
    @decoplot
    def figureplot(self,fig):
        ''' Return fig Bohek object '''
        return fig

    @chartsinput_deco
    @decoplot
    def plot(self,fig):
        ''' show plot '''
        if self._cocoplot.getvisu() == 'bokeh':
            return show(fig)
        else:
            return fig
    # ----------------------------------------------------------------------

pycoa=Front()
