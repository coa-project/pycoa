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
    kwargs_keystesting,
    kwargs_valuestesting,
    debug,
    info,
    flat_list,
    all_or_none_lists,
)

import src.covid19 as coco
from src.dbparser import MetaInfo
from src.error import *
import src.geo as coge

import geopandas as gpd
from src.output import InputOption, AllVisu


class __front__:
    """
        front Class
    """
    def __init__(self):
        self.meta = MetaInfo()
        self.av = InputOption()
        self.lvisu = list(self.av.d_graphicsinput_args['vis'])
        available_libs = self.av.test_add_graphics_libraries(self.lvisu)
        for lib, available in available_libs.items():
            if not available:
                self.lvisu.remove(lib)
        CoaInfo("Available graphicals librairies : " + str(self.lvisu))

        self.lwhat = list(self.av.d_batchinput_args['what'])
        self.lhist = list(self.av.d_graphicsinput_args['typeofhist'])
        self.loption = list(self.av.d_batchinput_args['option'])

        self.lmapoption = list(self.av.d_graphicsinput_args['mapoption'])
        self.ltiles = list(self.av.d_graphicsinput_args['tile'])

        self.lchartkargskeys = self.av.listchartkargskeys
        self.listchartkargsvalues = self.av.listchartkargsvalues
        self.listviskargskeys = self.av.listviskargskeys

        self.dict_bypop = coco.VirusStat.dictbypop()

        self.db = ''
        self.virus = ''
        self.vis = None
        self.allvisu = None
        self.charts = None
        self.namefunction = None
        self._setkwargsvisu = None

    def whattodo(self,):
        '''
        list all the keys, values from kwargs
        avalailable with the chart methods et setoptvis
        '''
        dico1 = {k:str(v) for k,v in self.av.d_batchinput_args.items()}
        dico2 = {k:str(v) for k,v in self.av.d_graphicsinput_args.items()}
        dico2['vis'] = self.lvisu
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
        pd2 = df(dico2,'setoptvis')
        pd1=pd.concat([pd1,pd2])
        pd1.index = pd1.index.rename('Methods')
        pd1 = pd1.sort_values(by='Arguments',ascending = False)
        return pd1

    def setoptvis(self,**kwargs):
        '''
            define visualization and associated options
        '''
        vis = kwargs.get('vis', None)
        if not self.allvisu:
            self.allvisu = self.av
        if vis:
            tile = kwargs.get('tile','openstreet')
            dateslider = kwargs.get('dateslider',False)
            mapoption =  kwargs.get('mapoption','text')
            guideline = kwargs.get('guideline','False')
            title = kwargs.get('title',None)
            self.allvisu.setkwargsfront(kwargs)
            if vis not in self.lvisu:
                raise CoaError("Sorry but " + visu + " visualisation isn't implemented ")
            else:
                self.setdisplay(vis)
                print(f"The visualization has been set correctly to: {vis}")
                try:
                    f = self.getnamefunction()
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

    def getnamefunction(self,):
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
        return list(self.av.d_batchinput_args['output'])

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
            raise CoaError('Waiting for a boolean !')
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
        return list(self.av.d_graphicsinput_args['typeofplot'])

    def listoption(self,):
        """Return the list of currently avalailable option apply to data.
         Default is no option.
        """
        return self.loption

    def listchartkargskeys(self,):
        """Return the list of avalailable kargs keys for chart functions
        """
        return self.lchartkargskeys

    def listchartkargskeys(self,):
        """Return the list of avalailable kargs values for chart functions
        """
        return self.lchartkargsvalues

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
                    raise CoaError('What is the granularity of your DB ?')
            return r

    def listbypop(self):
        """Get the list of available population normalization
        """
        return list(self.dict_bypop.keys())

    def listmapoption(self):
        """Get the list of available population normalization
        """
        return self.lmapoption

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
                self.virus, self.allvisu = coco.VirusStat.factory(db_name=base,reload=reload,vis=visu)
            else:
                self.virus = coco.VirusStat.readpekl('.cache/'+base+'.pkl')
                pandy = self.virus.getwheregeometrydescription()
                self.allvisu = AllVisu(base, pandy)
                coge.GeoManager('name')
        self.db = base

    def getwhom(self,return_error=True):
        """Return the current base which is used
        """
        return self.db

    def getkeywordinfo(self, which=None):
        """
            Return keyword_definition for the db selected
        """
        if which:
            if which in self.listwhich():
                print(self.virus.get_parserdb().get_keyword_definition(which))
                print('Parsed from this url:',self.virus.get_parserdb().get_keyword_url(which))
            else:
                raise CoaError('This value do not exist please check.'+'Available variable so far in this db ' + str(listwhich()))
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

    def setkwargsvisu(self,**kwargs):
        '''
            Update visu option , if a key exist update it else take default
        '''
        if self._setkwargsvisu:
            for k,v in kwargs.items():
                if v:
                    self._setkwargsvisu[k] = v
        else:
            self._setkwargsvisu = kwargs

    def getvisukwargs(self,):
        return self._setkwargsvisu

    def input_wrapper(func):
        '''
            Main decorator it mainly deals with arg testings
        '''
        @wraps(func)
        def wrapper(self,**kwargs):
            '''
                Wrapper input function .
                Wrap and format the user input argument for covid19 class
                if argument is missing fill with the default value
                Transforms 'where', 'which', and 'option' into lists if they are not already.
                order position of the items in 'option'
            '''
            if self.db == '':
                raise CoaError('Something went wrong ... does a db has been loaded ? (setwhom)')
            mustbealist = ['where','which','option']
            kwargs_keystesting(kwargs,self.lchartkargskeys + self.listviskargskeys,' kwargs keys not recognized ...')
            default = { k:[v[0]] if isinstance(v,list) else v for k,v in self.av.d_batchinput_args.items()}

            dicovisu = {k:kwargs.get(k) for k,v in self.av.d_graphicsinput_args.items()}
            self.setkwargsvisu(**dicovisu)
            [kwargs_valuestesting(dicovisu[i],self.av.d_graphicsinput_args[i],'value of '+ i +' not correct')
                for i in ['typeofhist','typeofplot']]

            for k,v in default.items():
                if k in kwargs.keys():
                    if isinstance(kwargs[k],list):
                        default[k] = kwargs[k]
                    else:
                        default[k] = [kwargs[k]]
            kwargs = default

            for k,v in kwargs.items():
                if k not in mustbealist:
                    kwargs[k]=v[0]

            if kwargs['where'][0] == '':
                kwargs['where'] = list(self.virus.get_fulldb()['where'].unique())

            if not all_or_none_lists(kwargs['where']):
                raise CoaError('For coherence all the element in where must have the same type list or not list ...')

            if 'sumall' in kwargs['option']:
                kwargs['option'].remove('sumall')
                kwargs['option'].append('sumall')

            if 'fillnan' not in kwargs['option']:
                kwargs['option'].insert(0,'fillnan')

            if 'nofillnan' in kwargs['option']:
                kwargs['option'].remove('fillnan')
                kwargs['option'].insert(0,'nofillnan')

            if 'sumall' in kwargs['option'] and len(kwargs['which'])>1:
                raise CoaError('sumall option incompatible with multile values ... remove one please')

            if  func.__name__ == 'get':
                if dicovisu['typeofplot']:
                    raise CoaError("'typeofplot' not compatible with get ...")
                if  dicovisu['typeofhist']:
                    raise CoaError("'typeofhist' not compatible with get ...")
            elif func.__name__ == 'plot':
                if dicovisu['typeofhist']:
                    raise CoaError("'typeofhist' option not compatible with plot ...")
            elif func.__name__ in ['hist','map']:
                if dicovisu['typeofplot']:
                    raise CoaError("'typeofplot' option not compatible with " + func.__name__ )
            elif func.__name__ in ['save']:
                pass
            else:
                raise CoaError(" What does " + func.__name__ + ' is supposed to be ... ?')

            if self.getvisukwargs()['vis']:
                pass
            if kwargs['input'].empty:
                    kwargs = self.virus.get_stats(**kwargs)

            found_bypop = None
            for w in kwargs['option']:
                if w.startswith('bypop='):
                    found_bypop = w
                    kwargs['which'] = [i+ ' ' +found_bypop for i in kwargs['which']]
                    break

            return func(self,**kwargs)
        return wrapper

    def setvisu(self,**kwargs):
        '''
            define visualization and associated options
        '''
        kwargs_keystesting(kwargs,self.listviskargskeys,'Bad args used ! please check ')
        default = { k:v[0] if isinstance(v,list) else v for k,v in self.av.d_graphicsinput_args.items()}
        vis = kwargs.get('vis')
        for k,v in default.items():
            kwargs[k] = v

        if vis not in self.lvisu:
            raise CoaError("Sorry but " + vis + " visualisation isn't implemented ")
        else:
            self.setdisplay(vis)
            kwargs['vis'] = vis
            CoaInfo(f"The visualization has been set correctly to: {vis}")
        self.setkwargsvisu(**kwargs)

    @input_wrapper
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

        self.setnamefunction(self.get)
        if output == 'pandas':
            def color_df(val):
                if val.columns=='date':
                    return 'blue'
                elif val.columns=='where':
                    return 'red'
                else:
                    return black

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
            raise CoaError('Unknown output.')
        self.outcome = casted_data
        return casted_data

    def saveoutput(self,**kwargs):
        '''
            Export pycoa. pandas as an output file selected by output argument
            'pandas': pandas to save
            'saveformat': excel (default) or csv
            'savename': None (default pycoa.ut+ '.xlsx/.csv')
        '''
        global _db
        kwargs_keystesting(kwargs, ['pandas','saveformat','savename'], 'Bad args used in the pycoa.saveoutput function.')
        pandy = kwargs.get('pandas', pd.DataFrame())
        saveformat = kwargs.get('saveformat', 'excel')
        savename = kwargs.get('savename', '')
        if pandy.empty:
            raise CoaError('Pandas to save is mandatory there is not default !')
        else:
            _db.saveoutput(pandas=pandy,saveformat=saveformat,savename=savename)

    def merger(self,**kwargs):
        '''
        Merge two or more pycoa.pandas from get_stats operation
        'src.andas': list (min 2D) of pandas from stats
        'whichcol': list variable associate to the src.andas list to be retrieve
        '''
        global _db
        kwargs_keystesting(kwargs,['coapandas'], 'Bad args used in the pycoa.merger function.')
        listpandy = kwargs.get('coapandas',[])
        return _db.merger(coapandas = listpandy)

    def decomap(func):
        @wraps(func)
        def inner(self,**kwargs):
            """
            Create a map according to arguments and options.
            See help(map).
            - 2 types of visu are avalailable so far : bokeh or folium (see lvisu())
            by default visu='bokeh'
            - In the default case (i.e visu='bokeh') available option are :
                - dateslider=True: a date slider is called and displayed on the right part of the map
                - mapoption = text, values are displayed directly on the map
                           = textinter, values as an integer are displayed directly on the map
                           = spark, sparkline are displayed directly on the map
                           = spiral, spiral are displayed directly on the map
                           = label%, label are in %
                           = exploded/dense, when available exploded/dense map geometry (for USA & FRA sor far)
            """
            input = kwargs.get('input')
            where = kwargs.get('where')

            if 'output' in kwargs:
                kwargs.pop('output')
            if 'bypop' in kwargs:
                kwargs.pop('bypop')
            dateslider = kwargs.get('dateslider', None)
            mapoption = kwargs.get('mapoption', None)
            if 'dense' in mapoption:
                if not self.virus.gettypeofgeometry().is_dense_geometry():
                    self.virus.gettypeofgeometry().set_dense_geometry()
                    new_geo = self.virus.geo.get_data()
                    granularity = self.meta.getcurrentmetadata(self.db)['geoinfo']['granularity']
                    new_geo = new_geo.rename(columns={'name_'+granularity:'where'})
                    new_geo['where'] = new_geo['where'].apply(lambda x: x.upper())

                    new_geo = new_geo.set_index('where')['geometry'].to_dict()

                    input['geometry'] = input['where'].apply(lambda x: x.upper()).map(new_geo)
                    input['where'] = input['where'].apply(lambda x: x.title())
                    kwargs['input'] = input
            return func(self,**kwargs)
        return inner

    def input_visuwrapper(func):
        '''
            Basicaly return one variable for histo and map when several which have been requested ...
        '''
        @wraps(func)
        def inner(self,**kwargs):
            if not 'get' in func.__name__:
                z = {**self.getvisukwargs(), **kwargs}
            if func.__name__ in ['hist','map']:
                if len(z['which'])>1:
                    raise CoaError("Histo and map available only for ONE variable ...")
                else:
                    z['which'] = z['which'][0]
                z['input'] = z['input'].loc[z['input'].date==z['input'].date.max()].reset_index(drop=True)
                z['input'] = z['input'].sort_values(by=kwargs['which'], ascending=False)
            return func(self,**z)
        return inner

    @input_wrapper
    @decomap
    def figuremap(self,**kwargs):
        dateslider = kwargs.get('dateslider', None)
        mapoption = kwargs.get('mapoption', None)
        visu = self.getdisplay()
        if visu == 'bokeh':
            if mapoption:
                if 'spark' in mapoption or 'spiral' in mapoption:
                    return self.allvisu.pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in mapoption:
                    return self.allvisu.pycoa_map(**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                return self.allvisu.pycoa_map(**kwargs)

    @input_wrapper
    @input_visuwrapper
    @decomap
    def map(self,**kwargs):
        self.setnamefunction(self.map)
        if self.getdisplay():
            z = {**self.getvisukwargs(), **kwargs}
            self.outcome = self.allvisu.map(**z)
            return self.outcome
        else:
            CoaError(" No visualization has been set up !")

    def decohist(func):
        @wraps(func)
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

            which --  is the name of the field of the input pandas to plot.
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
            dateslider = kwargs.get('dateslider')
            typeofhist = kwargs.get('typeofhist')
            kwargs.pop('output')
            if kwargs.get('bypop'):
              kwargs.pop('bypop')
            if self.getdisplay():
                self.outcome = self.allvisu.hist(**kwargs)
                return func(self,self.outcome)
            else:
                raise CoaError(" No visualization has been set up !")
        return inner

    @input_wrapper
    @decohist
    def figurehist(fig):
        ''' Return fig Bohek object '''
        return fig

    @input_wrapper
    @input_visuwrapper
    @decohist
    def hist(self,fig):
        ''' show hist '''
        self.setnamefunction(self.hist)
        self.outcome = fig
        if self.getdisplay() == 'bokeh':
            from bokeh.io import (
            show,
            output_notebook,
            )
            output_notebook(hide_banner=True)
            show(fig)
            return fig
        else:
            return fig

    def decoplot(func):
        @wraps(func)
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

            which --  is the name of the field of the input pandas to plot.
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
                                     For this type of plot one should used 'input' and 'which' (not fully tested).
                                     Moreover dim(which) must be 2.
                            'spiral' : plot variable as a spiral angular plot, angle being the date
                            'yearly' : same as date but modulo 1 year

            guideline add a guideline for the plot. False by default
            """
            input = kwargs.get('input')
            which = kwargs.get('which')
            typeofplot = kwargs.get('typeofplot',self.listplot()[0])
            kwargs.pop('output')

            if typeofplot == 'versus' and len(which)>2:
                CoaError(" versu can be used with 2 variables and only 2 !")
            if kwargs.get('bypop'):
                kwargs.pop('bypop')

            if self.getdisplay():
                z = {**self.getvisukwargs(), **kwargs}
                self.outcome = self.allvisu.plot(**z)

                return func(self,self.outcome)
            else:
                CoaError(" No visualization has been set up !")
        return inner

    @input_wrapper
    @decoplot
    def figureplot(self,fig):
        ''' Return fig Bohek object '''
        return fig

    @input_wrapper
    @input_visuwrapper
    @decoplot
    def plot(self,fig):
        self.setnamefunction(self.plot)
        ''' show plot '''
        if self.getdisplay() == 'bokeh' and self.plot != '':
            from bokeh.io import (
            show,
            output_notebook,
            )
            output_notebook(hide_banner=True)
            show(fig)
            return fig
        else:
            return fig

    def savefig(self,name):
        if  self.getnamefunction() != 'get':
            if self.getdisplay() == 'bokeh':
                bokeh_visu.bokeh_savefig(self.outcome,name)
            else:
                self.outcome.savefig(name)
        else:
            CoaError('savefig can\'t be used to store a panda DataFrame')

from src.__version__ import __version__,__author__,__email__
def front():
    ''' This public function returns front class '''
    fr = __front__()
    fr.__version__ = __version__
    fr.__author__ = __author__
    fr.__email__ = __email__
    return fr
