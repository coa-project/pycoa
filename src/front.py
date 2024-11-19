# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : src.front

About :
-------

This is the PyCoA front end functions. It provides easy access and
use of the whole PyCoA framework in a simplified way.
The use can change the VirusStat, the type of data, the output format
with keywords (see help of functions below).

Basic usage
-----------
** plotting covid deaths (default value) vs. time **
    import src.front as cf

    cf.plot(where='France')  # where keyword is mandatory
** getting recovered data for some countries **

    cf.get(where=['Spain','Italy'],which='recovered')
** listing available VirusStat and which data can be used **
    cf.listwhom()
    cf.setwhom('jhu',reload=True) # return available keywords (aka 'which' data), reload DB is True by default
    cf.listwhich()   # idem
    cf.lwhat()    # return available time series type (weekly,
                     # daily...)
    cf.plot(option='sumall') # return the cumulative plot for all countries
                     # for default which keyword. See cf.listwhich() and
                    # and other cf.list**() function (see below)

"""

# --- Imports ----------------------------------------------------------
import pandas as pd
from functools import wraps
import numpy as np

import datetime as dt
from src.tools import (
    kwargs_test,
    extract_dates,
    info,
    flat_list,
)

import src.covid19 as coco
from src.dbparser import MetaInfo
from src.error import *
import src.geo as coge

import geopandas as gpd
from src.output import OptionVisu

class __front__:
    """
        front Class
    """
    def __init__(self,visu = True):
        self.meta = MetaInfo()
        self.av = OptionVisu()
        #if visu:
        #    output_notebook(hide_banner=True)
        #    from bokeh.io import (
        #        show,
        #        output_notebook,
        #    )

        self.lwhat = list(self.av.dicochartargs['what'])
        self.lhist = list(self.av.dicochartargs['typeofhist'])
        self.loption = list(self.av.dicochartargs['option'])

        self.lmaplabel = list(self.av.dicovisuargs['maplabel'])
        self.lvisu = list(self.av.dicovisuargs['vis'])
        self.ltiles = list(self.av.dicovisuargs['tile'])

        self.lchartkargs = self.av.listchartkargs+['bypop']
        self.dict_bypop = coco.VirusStat.dictbypop()

        self.db = ''
        self.virus = ''
        self.vis = None
        self.cocoplot = None
        self.namefunction = None

    def whattodo(self,):
        '''
        list all the keys, values from kwargs
        avalailable with the chart methods et setoptvis
        '''
        dico1 = {k:str(v) for k,v in self.av.dicochartargs.items()}
        dico2 = {k:str(v) for k,v in self.av.dicofigureargs.items()}
        dico3 = {k:str(v) for k,v in self.av.dicovisuargs.items()}
        dv = dict(list(dico2.items()) + list(dico3.items()))

        def df(d,k):
            m = pd.DataFrame.from_dict(d.items())
            m['index'] = len(m)*[k]
            m=m.set_index('index')
            m.columns = ['Arguments', 'Available options']
            return m
        pd1 = df(dico1,'get, hist, map, plot, ')
        pd1.index = np.where(pd1.Arguments=='dateslider','hist, map', pd1.index)
        pd1.index = np.where(pd1.Arguments=='output','get', pd1.index)
        pd1.index = np.where(pd1.Arguments=='typeofhist','hist',pd1.index)
        pd1.index = np.where(pd1.Arguments=='typeofplot','plot', pd1.index)
        pd2 = df(dv,'setoptvis')
        pd1=pd.concat([pd1,pd2])
        pd1.index = pd1.index.rename('Methods')
        pd1 = pd1.sort_values(by='Arguments',ascending = False)
        return pd1

    def setoptvis(self,**kwargs):
        '''
            define visualization and associated options
        '''
        vis = kwargs.get('vis', None)
        if not self.cocoplot:
            self.cocoplot = self.av
        if vis:
            tile = kwargs.get('tile','openstreet')
            dateslider = kwargs.get('dateslider',False)
            maplabel =  kwargs.get('maplabel','text')
            guideline = kwargs.get('guideline','False')
            title = kwargs.get('title',None)
            self.cocoplot.setkwargsfront(kwargs)
            if vis not in self.lvisu:
                raise CoaError("Sorry but " + visu + " visualisation isn't implemented ")
            else:
                self.setdisplay(vis)
                print(f"The visualization has been set correctly to: {vis}")
                try:
                    f = self.gatenamefunction()
                    if f == 'Charts Function Not Registered':
                        raise CoaError("Sorry but " + f + ". Did you draw it ? ")
                    return f(**self.getkwargs())
                except:
                    pass
        else:
            CoaWarning("No Graphics loaded ! Only geopandas can be asked")
        self.vis = vis

    def setnamefunction(self,name):
        '''
        Name chart function setter
        '''
        # self.namefunction = name : it updates the visu + redraws the last chart
        self.namefunction = name.__name__

    def gatenamefunction(self,):
        '''
        Name chart function getter
        '''
        return self.namefunction

    def setdisplay(self,vis):
       '''
        Visualization seter
       '''
       if vis not in self.lvisu:
            raise CoaError("Visualisation "+ visu + " not implemented setting problem. Please contact support@pycoa.fr")
       else:
            self.vis = vis

    def getdisplay(self,):
        '''
        Visualization Getter
        '''
        return self.vis

    def getversion(self,):
        """Return the current running version of pycoa.
        """
        return src._version.__version__

    def listoutput(self,):
        """Return the list of currently available output types for the
        get() function. The first one is the default output given if
        not specified.
        """
        return list(self.av.dicochartargs['output'])

    def listvisu(self,):
        """Return the list of currently available visualization for the
        map() function. The first one is the default output given if
        not specified.
        """
        return self.lvisu

    def listwhom(self, detailed = False):
        """Return the list of currently avalailable VirusStats for covid19
         data in PyCoA.
         Only GOOD json description database is returned !
         If detailed=True, gives information location of each given VirusStat.
        """
        allpd  = self.meta.getallmetadata()
        namedb = allpd.name.to_list()

        if detailed:
            dico = {}
            namels, iso3ls, grls, varls = [],[],[],[]
            for i in namedb:

                mypd = allpd.loc[allpd.name.isin([i])]
                if mypd.validejson.values  == 'GOOD':
                    namels.append(i)
                    iso3 = mypd.parsingjson.values[0]['geoinfo']['iso3']
                    iso3ls.append(iso3)
                    gr = mypd.parsingjson.values[0]['geoinfo']['granularity']
                    grls.append(gr)
                    for datasets in mypd.parsingjson.values[0]['datasets']:
                        pdata = pd.DataFrame(datasets['columns'])
                    varls.append(self.listwhich(i))

            dico.update({'dbname': namels})
            dico.update({'iso3': iso3ls})
            dico.update({'granularity': grls})
            dico.update({'variables': varls})
            return pd.DataFrame.from_dict(dico, orient='index').T.reset_index(drop=True).set_index('dbname')
        else:
            return namedb
        '''
        db_list_dict = self.meta.getallmetadata()
        df = pd.DataFrame(db_list_dict)
        df = df.T.reset_index()
        df.index = df.index+1
        df = df.rename(columns={'index':'VirusStat',0: "WW/iso3",1:'Granularité',2:'WW/Name'})
        df = df.sort_values(by='VirusStat').reset_index(drop=True)
        try:
            if int(detailed):
                df = (df.style.set_table_styles([{'selector' : '','props' : [('border','3px solid green')]}]))
                print("Pandas has been pimped, use '.data' to get a pandas dataframe")
                return df
            else:
                return list(df['VirusStat'])
        except:
            raise CoaKeyError('Waiting for a boolean !')
        '''

    def listwhat(self,):
        """Return the list of currently avalailable type of series available.
         The first one is the default one.
        """
        return self.lwhat

    def listhist(self,):
        """Return the list of currently avalailable type of hist available.
         The first one is the default one.
        """
        return self.lhist

    def listplot(self,):
        """Return the list of currently avalailable type of plots available.
         The first one is the default one.
        """
        return list(self.av.dicochartargs['typeofplot'])

    def listoption(self,):
        """Return the list of currently avalailable option apply to data.
         Default is no option.
        """
        return self.loption

    def listchartkargs(self,):
        """Return the list of avalailable kargs for chart functions
        """
        return self.lchartkargs

    def listtiles(self,):
        """Return the list of currently avalailable tile option for map()
         Default is the first one.
        """
        return self.ltiles

    def listwhich(self,dbname):
        """Get which are the available fields for base 'dbname'
        if dbname is omitted current dabatase used (i.e self.db)
        Output is a list of string.
        By default, the listwhich()[0] is the default which field in other
        functions.
        """
        if dbname:
            dic = self.meta.getcurrentmetadata(dbname)
        else:
            dic = self.meta.getcurrentmetadata(self.db)
        return sorted(self.meta.getcurrentmetadatawhich(dic))

    def listwhere(self,clustered = False):
        """Get the list of available regions/subregions managed by the current VirusStat
        """
        granularity = self.meta.getcurrentmetadata(self.db)['geoinfo']['granularity']
        code = self.meta.getcurrentmetadata(self.db)['geoinfo']['iso3']
        def clust():
            if granularity == 'country' and code not in ['WLD','EUR']:
                return  self.virus.geo.to_standard(code)
            else:
                r = self.virus.geo.get_region_list()
                if not isinstance(r, list):
                    r=sorted(r['name_region'].to_list())
                r.append(code)
                if code  == 'EUR':
                    r.append('European Union')
                return r

        if granularity == 'country' and code not in ['WLD','EUR']:
            return code
        if clustered:
            return clust()
        else:
            if self.virus.db_world == True:
                if granularity == 'country' and code not in ['WLD','EUR'] :
                    r =  self.virus.to_standard(code)
                else:
                    if code == 'WLD':
                        r = self.virus.geo.get_GeoRegion().get_countries_from_region('World')
                    else:
                        r = self.virus.geo.get_GeoRegion().get_countries_from_region('Europe')
                    r = [self.virus.geo.to_standard(c)[0] for c in r]
            else:
                if granularity == 'subregion':
                    pan = self.virus.geo.get_subregion_list()
                    r = list(pan.name_subregion.unique())
                elif granularity == 'country':
                    r = clust()
                    r.append(code)
                else:
                    raise CoaKeyError('What is the granularity of your DB ?')
            return r

    def listbypop(self):
        """Get the list of available population normalization
        """
        return list(self.dict_bypop.keys())

    def listmaplabel(self):
        """Get the list of available population normalization
        """
        return self.lmaplabel

    def setwhom(self,base,**kwargs):
        """Set the covid19 VirusStat used, given as a string.
        Please see pycoa.listbase() for the available current list.

        By default, the listbase()[0] is the default base used in other
        functions.
        """
        reload = kwargs.get('reload', True)
        if reload not in [0,1]:
            raise CoaError('reload must be a boolean ... ')
        if base not in self.listwhom():
            raise CoaDbError(base + ' is not a supported VirusStat. '
                                    'See pycoa.listbase() for the full list.')
        # Check if the current base is already set to the requested base
        visu = self.getdisplay()
        if self.db == base:
            info(f"The VirusStat '{base}' is already set as the current database")
            return
        else:
            if reload:
                self.virus, self.cocoplot = coco.VirusStat.factory(db_name=base,reload=reload,vis=visu)
            else:
                self.virus = coco.VirusStat.readpekl('.cache/'+base+'.pkl')
                pandy = self.virus.getwheregeometrydescription()
                self.cocoplot = output.AllVisu(base, pandy)
                coge.GeoManager('name')
        self.db = base

    def getwhom(self,return_error=True):
        """Return the current base which is used
        """
        return self.whom

    def getkeywordinfo(self, which=None):
        """
            Return keyword_definition for the db selected
        """
        if which:
            if which in self.listwhich():
                print(self.virus.get_parserdb().get_keyword_definition(which))
                print('Parsed from this url:',self.virus.get_parserdb().get_keyword_url(which))
            else:
                raise CoaKeyError('This value do not exist please check.'+'Available variable so far in this db ' + str(listwhich()))
        else:
            df = self.virus.get_parserdb().get_dbdescription()
            return df

    def getrawdb(self, **kwargs):
        """
            Return the main pandas i.e with all the which values loaded from the VirusStat selected
        """
        col = list(self.virus.get_fulldb().columns)
        mem='{:,}'.format(self.virus.get_fulldb()[col].memory_usage(deep=True).sum())
        info('Memory usage of all columns: ' + mem + ' bytes')
        df = self.virus.get_fulldb(**kwargs)
        return df

    def setkwargs(self,**kwargs):
        self._setkwargs=kwargs

    def getkwargs(self,):
        return self._setkwargs

    def chartsinput_deco(f):
        '''
            Main decorator it mainly deals with arg testings
        '''
        @wraps(f)
        def wrapper(self,**kwargs):
            '''
                wrapper dealing with arg testing
            '''
            if self.db == '':
                raise CoaKeyError('Something went wrong ... does a db has been loaded ? (setwhom)')
                #self.db, self.cocoplot = coco.VirusStat.factory(db_name = self.whom)
            for i in self.av.listviskargs:
                try:
                    kwargs.pop(i)
                except:
                    pass

            kwargs_test(kwargs,self.lchartkargs,'Bad args used ! please check ')
            where = kwargs.get('where', None)
            which = kwargs.get('which', None)
            if which and not isinstance(which,list):
                which=[which]
            what = kwargs.get('what', None)

            whom = kwargs.get('whom', None)
            option = kwargs.get('option', None)
            when = kwargs.get('when', None)
            input_arg = kwargs.get('input', None)
            input_field = kwargs.get('input_field',None)
            #if (option != None) and (isinstance(input_field,list) or isinstance(which,list)):
            #    raise CoaKeyError('option not compatible when input_fied/which is a list')
            if 'input_field' not in kwargs:
                input_field = which
            else:
                which = kwargs['input_field']
            #if input_field:
            #    which = input_field
            if what:
                if what not in self.lwhat:
                    raise CoaKeyError('What = ' + what + ' not supported. '
                                                              'See lwhat() for full list.')
                if 'what'=='sandard':
                    what = which
            else:
                what = self.lwhat[0]

            option = kwargs.get('option', None)
            bypop = kwargs.get('bypop','no')

            kwargs['output'] = kwargs.get('output', self.listoutput()[0])

            if kwargs['output'] not in self.listoutput():
                raise CoaKeyError('Output option ' + kwargs['output'] + ' not supported. See help().')

            if bypop not in self.listbypop():
                raise CoaKeyError('The bypop arg should be selected in '+str(self.listbypop())+' only.')

            if isinstance(input_arg, pd.DataFrame):
                if input_arg is not None and not input_arg.empty:
                    pandy = input_arg
                    pandy = self.virus.get_stats(**kwargs)
                else:
                    pandy=pd.DataFrame()
                    input_field = which
                    for i in which:
                        tmp = self.virus.get_stats(which=i,where=where, option=option)
                        if len(which)>1:
                            tmp = tmp.rename(columns={'daily':'daily_'+i,'weekly':'weekly_'+i})
                        if pandy.empty:
                            pandy = tmp
                        else:
                            tmp = tmp[[i,'daily_'+i,'weekly_'+i,'date','clustername']]
                            pandy = pd.merge(pandy, tmp, on=['date','clustername'],how='inner')
                    input_arg = pandy
                if bypop != 'no':
                    input_arg = self.virus.normbypop(pandy,input_field,bypop)
                    if bypop=='pop':
                        input_field = input_field+' per total population'
                    else:
                        input_field = input_field+' per '+ bypop + ' population'
                    pandy = input_arg
                if isinstance(input_field,list):
                    which = input_field[0]
                pandy.loc[:,'standard'] = pandy[pandy.columns[2]]
                if 'input_field' not in kwargs:
                    kwargs['input_field'] = input_field
            elif input_arg == None :
                pandy = self.virus.get_stats(**kwargs)
                if which :
                    pandy['standard'] = pandy[which[0]]
                else:
                    pandy['standard'] = pandy[pandy.columns[2]]
                    which = list(pandy.columns)[2]
                input_field = what

                if pandy[[pandy.columns[2],'date']].isnull().values.all():
                    info('--------------------------------------------')
                    info('All values for '+ which + ' is nan nor empty')
                    info('--------------------------------------------')
                    pandy['date']=len(where)*[dt.date(2020,1,1),dt.date.today()]
                    lwhere=flat_list([[i,i] for i in where])
                    pandy['where']=lwhere
                    pandy['clustername']=lwhere
                    pandy['code']=len(pandy)*['000']
                    pandy=pandy.fillna(0)
                    bypop = 'no'
                if bypop != 'no':
                    if what:
                        val = what
                    else:
                        val = _lwhat[0]
                    pandy = self.virus.normbypop(pandy , val, bypop)
                    if bypop=='pop':
                        input_field = input_field+' per total population'
                    else:
                        input_field = input_field+' per '+ bypop + ' population'
                kwargs['input_field'] = input_field
                option = kwargs.get('option', None)
            else:
                raise CoaTypeError('Waiting input as valid pycoa.pandas '
                                   'dataframe. See help.')
            when_beg, when_end = extract_dates(when)
            onedate = False
            if when and ':' not in when:
                onedate = True
            if pandy[[pandy.columns[2],'date']].isnull().values.all():
                info('--------------------------------------------')
                info('All values for '+ which + ' is nan nor empty')
                info('--------------------------------------------')
                pandy['date']=len(where)*[dt.date(2020,1,1),dt.date.today()]
                lwhere=flat_list([[i,i] for i in where])
                pandy['where']=lwhere
                pandy['clustername']=lwhere
                pandy['code']=len(pandy)*['000']
                pandy=pandy.fillna(0)
                bypop = 'no'

            db_first_date = pandy.date.min()
            db_last_date = pandy.date.max()

            if when_beg < db_first_date:
                when_beg = db_first_date

            if when_end > db_last_date:
                when_end = db_last_date

            if when_end < db_first_date:
                raise CoaNoData("No available data before "+str(db_first_date))
            # when cut
            if when_beg >  db_last_date or when_end >  db_last_date:
                raise CoaNoData("No available data after "+str(db_last_date))

            if onedate:
                pandy = pandy[pandy.date == when_end]
            else:
                pandy = pandy[(pandy.date >= when_beg) & (pandy.date <= when_end)]
            if bypop != 'no':
                kwargs['input_field'] = [i for i in pandy.columns if ' per ' in i]
                #name = [i for i in list(pandy.columns) if ' per ' in i]
                if bypop=='pop':
                    bypop='total population'
                else:
                    bypop+=' population'
                if isinstance(which,list):
                    which=which[0]
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
            self.setkwargs(**kwargs)
            return f(self,**kwargs)
        return wrapper

    @chartsinput_deco
    def get(self,**kwargs):
        """Return covid19 data in specified format output (default, by list)
        for specified locations ('where' keyword).
        The used VirusStat is set by the setbase() function but can be
        changed on the fly ('whom' keyword)
        Keyword arguments
        -----------------

        where  --   a single string of location, or list of (mandatory,
                    no default value)
        which  --   what sort of data to deliver ( 'death','confirmed',
                    'recovered' for 'jhu' default VirusStat). See listwhich() function
                    for full list according to the used VirusStat.

        what   --   which data are computed, either in standard mode
                    ('standard', default value), or 'daily' (diff with previous day
                    and 'weekly' (diff with previous week). See
                    listwhich() for fullist of available
                    Full list of what keyword with the lwhat() function.

        whom   --   VirusStat specification (overload the setbase()
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
                    See loption().
        bypop --    normalize by population (if available for the selected VirusStat).
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
            casted_data = pd.merge(pandy, self.virus.getwheregeometrydescription(), on='where')
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
            Export pycoa. pandas as an output file selected by output argument
            'pandas': pandas to save
            'saveformat': excel (default) or csv
            'savename': None (default pycoa.ut+ '.xlsx/.csv')
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
        Merge two or more pycoa.pandas from get_stats operation
        'src.andas': list (min 2D) of pandas from stats
        'whichcol': list variable associate to the src.andas list to be retrieve
        '''
        global _db
        kwargs_test(kwargs,['coapandas'], 'Bad args used in the pycoa.merger function.')
        listpandy = kwargs.get('coapandas',[])
        return _db.merger(coapandas = listpandy)

    def decomap(func):
        def inner(self,**kwargs):
            """
            Create a map according to arguments and options.
            See help(map).
            - 2 types of visu are avalailable so far : bokeh or folium (see lvisu())
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
            #if not input.empty:
            #    kwargs.pop('input')
            #    kwargs.pop('input_field')
            if 'output' in kwargs:
                kwargs.pop('output')
            if 'bypop' in kwargs:
                kwargs.pop('bypop')
            dateslider = kwargs.get('dateslider', None)
            maplabel = kwargs.get('maplabel', None)
            lmaplabel=self.lmaplabel
            if maplabel is not None:
                if not isinstance(maplabel,list):
                    maplabel = [maplabel]
                if  [a for a in maplabel if a not in lmaplabel]:
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
                for i in lmaplabel:
                    if i in maplabel and i not in ['text','textinteger']:
                        kwargs['maplabel'].append(i)
                #if all([ True if i in ['text','spark','label%','log'] else False for i in kwargs['maplabel'] ]) :
                #    CoaKeyError('Waiting for a valide label visualisation: text, spark or label%')
                input.loc[:,input_field]=input[input_field].fillna(0) #needed in the case where there are nan else js pb

            return func(self,**kwargs)
        return inner

    @chartsinput_deco
    @decomap
    def figuremap(self,**kwargs):
        dateslider = kwargs.get('dateslider', None)
        maplabel = kwargs.get('maplabel', None)
        visu = self.getdisplay()
        if visu == 'bokeh':
            if maplabel:
                if 'spark' in maplabel or 'spiral' in maplabel:
                    return self.cocoplot.pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in maplabel:
                    return self.cocoplot.pycoa_map(**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                return self.cocoplot.pycoa_map(**kwargs)

    @chartsinput_deco
    @decomap
    def map(self,**kwargs):
        self.setnamefunction(self.map)
        dateslider = kwargs.get('dateslider', None)
        maplabel = kwargs.get('maplabel', None)
        visu = self.getdisplay()
        if visu == 'bokeh':
            if maplabel:
                if 'spark' in maplabel or 'spiral' in maplabel:
                    fig = self.cocoplot.pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in maplabel:
                    fig = self.cocoplot.pycoa_map(**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                fig = self.cocoplot.pycoa_map(**kwargs)
            return show(fig)
        elif visu == 'folium':
            if dateslider is not None :
                raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
            if  maplabel and set(maplabel) != set(['log']):
                raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
            return self.cocoplot.pycoa_mapfolium(**kwargs)
        elif visu == 'mplt':
            return self.cocoplot.pycoa_mpltmap(**kwargs)
        elif visu == 'seaborn':
            return self.cocoplot.pycoa_heatmap_seaborn(**kwargs)
        else:
            self.setdisplay('bokeh')
            raise CoaTypeError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'mplt\' \
            aka matplotlib .See help.')

    def decohist(func):
        def inner(self,**kwargs):
            """
            Create histogram according to arguments.
            See help(hist).
            Keyword arguments
            -----------------

            where (mandatory if no input), what, which, whom, when : (see help(get))

            input       --  input data to plot within the pycoa.framework (e.g.
                            after some analysis or filtering). Default is None which
                            means that we use the basic raw data through the get
                            function.
                            When the 'input' keyword is set, where, what, which,
                            whom when keywords are ignored.
                            input should be given as valid pycoa.pandas dataframe.

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
            typeofhist = kwargs.get('typeofhist',self.listhist()[0])
            kwargs.pop('output')
            if kwargs.get('bypop'):
              kwargs.pop('bypop')
            if self.getdisplay() == 'bokeh':
                if typeofhist == 'bylocation':
                    if 'bins' in kwargs:
                        raise CoaKeyError("The bins keyword cannot be set with histograms by location. See help.")
                    fig = self.cocoplot.pycoa_horizonhisto(**kwargs)
                elif typeofhist == 'byvalue':
                    if dateslider:
                        info('dateslider not implemented for typeofhist=\'byvalue\'.')
                        fig = self.cocoplot.pycoa_horizonhisto(**kwargs)
                    else:
                        fig = self.cocoplot.pycoa_histo( **kwargs)
                elif typeofhist == 'pie':
                    fig = self.cocoplot.pycoa_pie(**kwargs)
            elif self.getdisplay() == 'seaborn':
                if typeofhist == 'bylocation':
                    fig = self.cocoplot.pycoa_hist_seaborn_hori( **kwargs)
                elif typeofhist == 'pie':
                    fig = self.cocoplot.pycoa_pairplot_seaborn(**kwargs)
                elif typeofhist == 'byvalue':
                    fig = self.cocoplot.pycoa_hist_seaborn_value( **kwargs)
                else:
                    print(typeofhist + ' not implemented in ' + self.getdisplay())
                    self.setdisplay('bokeh')
                    fig = self.cocoplot.pycoa_horizonhisto(**kwargs)
            elif self.getdisplay() == 'mplt':
                if typeofhist == 'bylocation':
                    fig = self.cocoplot.pycoa_mplthorizontalhisto(**kwargs)
                elif typeofhist == 'byvalue':
                    fig = self.cocoplot.pycoa_mplthisto(**kwargs)
                elif typeofhist == 'pie':
                    fig = self.cocoplot.pycoa_mpltpie(**kwargs)
                else:
                    print(typeofhist + ' not implemented in ' + self.getdisplay())
                    self.setdisplay('bokeh')
                    fig = self.cocoplot.pycoa_horizonhisto(**kwargs)
            else:
                self.setdisplay('bokeh')
                raise CoaKeyError('Unknown typeofhist value. Available value : lthist().')
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
        self.setnamefunction(self.hist)
        if self.getdisplay() == 'bokeh':
            show(fig)
        else:
            return fig

    def decoplot(func):
        def inner(self,**kwargs):
            """
            Create a date plot according to arguments. See help(plot).
            Keyword arguments
            -----------------

            where (mandatory), what, which, whom, when : (see help(get))

            input       --  input data to plot within the pycoa.framework (e.g.
                            after some analysis or filtering). Default is None which
                            means that we use the basic raw data through the get
                            function.
                            When the 'input' keyword is set, where, what, which,
                            whom when keywords are ignored.
                            input should be given as valid pycoa.pandas dataframe.

            input_field --  is the name of the field of the input pandas to plot.
                            Default is 'deaths/standard', the default output field of
                            the get() function.

            width_height : width and height of the picture .
                        If specified should be a list of width and height. For instance width_height=[400,500]

            title       --  to force the title of the plot

            copyright - to force the copyright lower left of the graph

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
            typeofplot = kwargs.get('typeofplot',self.listplot()[0])
            kwargs.pop('output')
            fig = self.cocoplot
            if kwargs.get('bypop'):
                kwargs.pop('bypop')
            if self.getdisplay() == 'bokeh':
                if typeofplot == 'date':
                    fig = self.cocoplot.pycoa_date_plot(**kwargs)
                elif typeofplot == 'spiral':
                    fig = self.cocoplot.pycoa_spiral_plot(**kwargs)
                elif typeofplot == 'versus':
                    if isinstance(input_field,list) and len(input_field) == 2:
                        fig = self.cocoplot.pycoa_plot(**kwargs)
                    else:
                        print('typeofplot is versus but dim(input_field)!=2, versus has not effect ...')
                        fig = self.cocoplot.pycoa_date_plot(**kwargs)
                elif typeofplot == 'menulocation':
                    if _db_list_dict[self.whom][1] == 'nation' and _db_list_dict[self.whom][2] != 'World':
                        print('typeofplot is menulocation with a national DB granularity, use date plot instead ...')
                        fig = self.cocoplot.pycoa_date_plot(*kwargs)
                    else:
                        if isinstance(input_field,list) and len(input_field) > 1:
                            CoaWarning('typeofplot is menulocation but dim(input_field)>1, take first one '+input_field[0])
                        fig = self.cocoplot.pycoa_menu_plot(**kwargs)
                elif typeofplot == 'yearly':
                    if input.date.max()-input.date.min() <= dt.timedelta(days=365):
                        print("Yearly will not be used since the time covered is less than 1 year")
                        fig = self.cocoplot.pycoa_date_plot(**kwargs)
                    else:
                        fig = self.cocoplot.pycoa_yearly_plot(**kwargs)
            elif self.getdisplay() == 'mplt':
                if typeofplot == 'date':
                    fig = self.cocoplot.pycoa_mpltdate_plot(**kwargs)
                elif typeofplot == 'versus':
                    fig = self.cocoplot.pycoa_mpltversus_plot(**kwargs)
                elif typeofplot == 'yearly':
                    fig = self.cocoplot.pycoa_mpltyearly_plot(**kwargs)
                else:
                    raise CoaKeyError('For display: '+self.getdisplay() +' unknown type of plot '+typeofplot)
            elif self.getdisplay() == 'seaborn':
                if typeofplot == 'date':
                    fig = self.cocoplot.pycoa_date_plot_seaborn(**kwargs)
                else:
                    print(typeofplot + ' not implemented in ' + self.getdisplay())
                    fig = self.cocoplot.pycoa_spiral_plot(**kwargs)
            elif self.getdisplay() == None:
                CoaWarning('Visualisation has not been defined ... not displayed')
                pass
            else:
                self.setdisplay('bokeh')
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
        self.setnamefunction(self.plot)
        ''' show plot '''
        if self.getdisplay() == 'bokeh' and self.plot != '':
            return show(fig)
        else:
            return fig

def front():
    ''' This public function returns front class '''
    fr = __front__()
    return fr

def bfront():
    ''' This public function returns batch front class '''
    fr = __front__(visu=False)
    return fr
