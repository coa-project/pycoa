# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa_fr
License: See joint LICENSE file

Module : src.allvisu

About :
-------

An interface module to easily plot pycoa_data with bokeh

"""
from src.tools import (
    kwargs_test,
    extract_dates,
    verb,
    fill_missing_dates
)
from src.error import *
import math
import pandas as pd
import geopandas as gpd
import numpy as np

from collections import defaultdict
import itertools
import json
import io
from io import BytesIO
import base64
import copy
import locale
import inspect
import importlib

import shapely.geometry as sg

import datetime as dt
import bisect
from functools import wraps

from src.dbparser import MetaInfo

Width_Height_Default = [500, 380]
Max_Countries_Default = 24

__all__ = ['InputOption']

class InputOption():
    """
        Option visualisation !
    """
    def __init__(self):
        self.ax_type = ['linear', 'log']

        self.d_batchinput_args  = {
                                'where':None,\
                                'option':['nonneg', 'nofillnan', 'smooth7', 'sumall'],\
                                'which':None,\
                                'what':['standard', 'daily', 'weekly'],\
                                'when':None,\
                                'input':None,\
                                'input_field':None,\
                                #'dateslider':[False,True],\
                                'output':['pandas','geopandas','list', 'dict', 'array']
                              }
        self.listchartkargs = list(self.d_batchinput_args.keys())

        self.d_graphicsinput_args = {
                                 'plot_height':Width_Height_Default[1],\
                                 'plot_width':Width_Height_Default[0],\
                                 'title':'',\
                                 'copyright': 'pyvoa',\
                                 'mode':['mouse','vline','hline'],\
                                 'typeofhist':['bylocation','byvalue','pie'],\
                                 'typeofplot':['date','menulocation','versus','spiral','yearly'],\
                                 'bins':10,\
                                 'vis':['matplotlib','bokeh','folium','seaborn'],\
                                 'tile' : ['openstreet','esri','stamen'],\
                                 'orientation':['horizontal','vertical'],\
                                 'dateslider':[False,True],\
                                 'maplabel':['text','textinteger','spark','label%','log','unsorted','exploded','dense'],\
                                 'guideline':[False,True],\
                              }
        self.listviskargs = list(self.d_graphicsinput_args.keys())
        self.dicokfront = {}

        graphics_libs = self.d_graphicsinput_args['vis']


    def test_add_graphics_libraries(self,libraries):
        '''
            Tests the presence of the specified graphical libraries
        '''
        results = {}
        for lib in libraries:
            try:
                importlib.import_module(lib)
                results[lib] = True
            except ImportError:
                results[lib] = False
        return results
    def setkwargsfront(self,kw):
        kwargs_test(kw, list(self.d_graphicsinput_args.keys())+list(self.d_graphicsinput_args.keys()), 'Error with this resquest (not available in setoptvis)')
        self.dicokfront = kw

    def getkwargsfront(self):
        return self.dicokfront

class AllVisu():
    """
        All visualisation should be implemented here !
    """
    def __init__(self, db_name = None, kindgeo = None):
        self.lcolors = ['red', 'blue', 'green', 'orange', 'purple',
          'brown', 'pink', 'gray', 'yellow', 'cyan']
        self.scolors = self.lcolors[:5]

        if kindgeo is None:
            pass
        else:
            self.kindgeo = kindgeo
        self.when_beg = dt.date(1, 1, 1)
        self.when_end = dt.date(1, 1, 1)
        #if  available_libs['bokeh']:
        #    self.scolors = Category10[5]
        #    self.lcolors = Category20[20]

        self.database_name = None
        verb("Init of AllVisu() with db=" + str(db_name))
        self.database_name = db_name
        self.currentmetadata = MetaInfo().getcurrentmetadata(db_name)
        self.setchartsfunctions = [method for method in dir(AllVisu) if callable(getattr(AllVisu, method)) and method.startswith("pycoa_") and not method.startswith("__")]
        self.geopan = gpd.GeoDataFrame()
        self.pycoa_geopandas = False
        self.geom = []
        self.listfigs = []
        self.dchartkargs = {}
        self.dvisukargs = {}
        self.uptitle, self.subtitle = ' ',' '
        self.code = self.currentmetadata['geoinfo']['iso3']
        self.granularity = self.currentmetadata['geoinfo']['granularity']
        self.namecountry = self.currentmetadata['geoinfo']['iso3']

    ''' WRAPPER COMMUN FOR ALL'''
    def decowrapper(func):
        '''
            Main decorator it mainly deals with arg testings
        '''
        @wraps(func)
        def wrapper(self,**kwargs):
            """
            Parse a standard input, return :
                - pandas: with location keyword (eventually force a column named 'where' to 'where')
                - kwargs:
                    * keys = [plot_width, plot_width, title, when, title_temporal,bins, what, which]
            Note that method used only the needed variables, some of them are useless
            - add kwargs set in the setoptvis front end to global kwargs variable : kwargs.update(self.getkwargsfront())
            """
            if not isinstance(kwargs['input'], pd.DataFrame):
                raise CoaTypeError(input + 'Must be a pandas, with pycoa_structure !')
            inputopt = InputOption()
            #kwargs_test(kwargs, inputopt.listchartkargs, 'Bad args used in the display function.')
            kwargs.update(inputopt.getkwargsfront())

            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            which = kwargs.get('which', input.columns[2])
            when = kwargs.get('when', None)
            option = kwargs.get('option', None)
            #bins = kwargs.get('bins', self.d_batchinput_args['bins'])

            tile = kwargs.get('tile', inputopt.d_graphicsinput_args['tile'])
            titlesetted = kwargs.get('title', inputopt.d_graphicsinput_args['title'])
            maplabel = kwargs.get('maplabel', inputopt.d_graphicsinput_args['maplabel'])
            if isinstance(which,list):
                which = input.columns[2]
            if input_field and 'cur_' in input_field:
                what =  which
            else:
                what = kwargs.get('what', which)

            if input_field is None:
                input_field = which

            if isinstance(input_field,list):
                test = input_field[0]
            else:
                test = input_field
            if input[[test,'date']].isnull().values.all():
                raise CoaKeyError('All values for '+ which + ' is nan nor empty')

            if type(input) == gpd.geodataframe.GeoDataFrame:
               self.pycoa_geopandas = True

            if maplabel and 'unsorted' in maplabel:
                pass
            else:
                input = input.sort_values(by=input_field, ascending = False).reset_index(drop=True)

            uniqloc = input.clustername.unique()

            if len(uniqloc) < 5:
                colors = self.scolors
            else:
                colors = self.lcolors
            colors = itertools.cycle(colors)
            dico_colors = {i: next(colors) for i in uniqloc}

            input = input.copy()
            if not 'colors' in input.columns:
                input.loc[:,'colors'] = input['clustername'].map(dico_colors)#(pd.merge(input, country_col, on='where'))
            if not isinstance(input_field, list):
                  input_field = [input_field]
            else:
                  input_field = input_field

            col2=which
            when_beg = input[[col2,'date']].date.min()
            when_end = input[[col2,'date']].date.max()

            if when:
                when_beg, when_end = extract_dates(when)
                if when_end > input[[col2,'date']].date.max():
                    when_end = input[[col2,'date']].date.max()

                if when_beg == dt.date(1, 1, 1):
                    when_beg = input[[col2,'date']].date.min()

                if not isinstance(when_beg, dt.date):
                    raise CoaNoData("With your current cuts, there are no data to plot.")

                if when_end <= when_beg:
                    print('Requested date below available one, take', when_beg)
                    when_end = when_beg
                if when_beg > input[[col2,'date']].date.max() or when_end > input[[col2,'date']].date.max():
                    raise CoaNoData("No available data after "+str(input[[input_field[0],'date']].date.max()))
            when_end_change = when_end
            '''
            for i in input_field:
                if input[i].isnull().all():
                    #raise CoaTypeError("Sorry all data are NaN for " + i)
                    print("Sorry all data are NaN for " + i)
                else:
                    when_end_change = min(when_end_change,AllVisu.changeto_nonull_date(input, when_end, i))
            '''
            if func.__name__ not in ['pycoa_date_plot', 'pycoa_plot', 'pycoa_menu_plot', 'pycoa_spiral_plot',\
                'pycoa_yearly_plot','pycoa_mpltdate_plot','pycoa_mpltversus_plot','pycoa_date_plot_seaborn']:
                if len(input_field) > 1:
                    print(str(input_field) + ' is dim = ' + str(len(input_field)) + '. No effect with ' + func.__name__ + '! Take the first input: ' + input_field[0])
                input_field = input_field[0]

            if when_end_change != when_end:
                when_end = when_end_change

            self.when_beg = when_beg
            self.when_end = when_end
            input = input.loc[(input['date'] >=  self.when_beg) & (input['date'] <=  self.when_end)]

            title_temporal = ' (' + 'between ' + when_beg.strftime('%d/%m/%Y') + ' and ' + when_end.strftime('%d/%m/%Y') + ')'
            if func.__name__ not in ['pycoa_date_plot', 'pycoa_plot', 'pycoa_menu_plot', 'pycoa_spiral_plot','pycoa_yearly_plot']:
                title_temporal = ' (' + when_end.strftime('%d/%m/%Y')  + ')'
            title_option=''
            if option:
                if 'sumallandsmooth7' in option:
                    if not isinstance(option,list):
                        option = ['sumallandsmooth7']
                    option.remove('sumallandsmooth7')
                    option += ['sumall','smooth7']
                title_option = ' (option: ' + str(option)+')'

            input_field_tostring = str(input_field).replace('[', '').replace(']', '').replace('\'', '')
            whichtitle = which
            if 'pop' in input_field_tostring:
                whichtitle = input_field_tostring.replace('weekly ','').replace('daily ','')

            if 'daily' in input_field_tostring:
                titlefig = whichtitle + ', ' + 'day to day difference' + title_option
            elif 'weekly' in input_field_tostring:
                titlefig = whichtitle + ', ' + 'week to week difference' + title_option
            else:
                if 'cur_' in  which or 'idx_' in  which:
                    #titlefig = which + ', ' + 'current ' + which.replace('cur_','').replace('idx_','')+ title_option
                    titlefig = whichtitle + ', current value' + title_option
                else:
                    titlefig = whichtitle + ', cumulative'+ title_option

            copyright = kwargs.get('copyright', None)
            if copyright:
                copyright = '©pycoa_fr ' + copyright + title_temporal
            else:
                copyright = '©pycoa_fr data from: {}'.format(self.database_name)+' '+title_temporal
            kwargs['copyright'] = copyright

            self.subtitle = copyright
            if titlesetted:
                title = titlesetted + title_temporal
                self.uptitle = title
                titlefig = titlesetted
            else:
                title = which + title_temporal
                self.uptitle = title
                titlefig = title
            kwargs['title'] = titlefig
            kwargs['input'] = input
            return func(self,**kwargs)
        return wrapper

    ''' DECORATORS FOR PLOT: DATE, VERSUS, SCROLLINGMENU '''
    def decoplot(func):
        """
        decorator for plot purpose
        """
        @wraps(func)
        def inner_plot(self ,**kwargs):
            input = kwargs.get('input')
            input_field = [kwargs.get('input_field')]
            where = kwargs.get('input',None)
            if isinstance(input_field[0],list):
                input_field = input_field[0]
            typeofplot = kwargs.get('typeofplot',InputOption().d_graphicsinput_args['typeofplot'][0])
            location_ordered_byvalues = list(
                input.loc[input.date == self.when_end].sort_values(by=input_field, ascending=False)['clustername'].unique())
            input['clustername']  = pd.Categorical(input.clustername,
                                                   categories=location_ordered_byvalues, ordered=True)

            input = input.sort_values(by=['clustername', 'date']).reset_index(drop = True)
            if 'sumall' in kwargs['option'] and  'where' not in kwargs.keys():
                input['clustername'] = 'sumall'
            else:
                if func.__name__ != 'pycoa_menu_plot' :
                    if len(location_ordered_byvalues) >= Max_Countries_Default:
                        input = input.loc[input.clustername.isin(location_ordered_byvalues[:Max_Countries_Default])]
                list_max = []
                for i in input_field:
                    list_max.append(max(input.loc[input.clustername.isin(location_ordered_byvalues)][i]))

                if len([x for x in list_max if not np.isnan(x)]) > 0:
                    amplitude = (np.nanmax(list_max) - np.nanmin(list_max))
                    if amplitude > 10 ** 4:
                        InputOption().ax_type.reverse()

            if func.__name__ == 'pycoa_menu_plot' :
                if isinstance(input_field,list):
                    if len(input_field) > 1:
                        print(str(input_field) + ' is dim = ' + str(len(input_field)) + '. No effect with ' + func.__name__ + '! Take the first input: ' + input_field[0])
                    input_field = input_field[0]
                if self.granularity == 'country' and self.code != 'WW':
                    func.__name__ = 'pycoa_date_plot'
            kwargs['input'] = input.reset_index(drop=True)
            kwargs['typeofplot']=typeofplot
            return func(self, **kwargs)
        return inner_plot

        ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE & MAP'''
    def decohistomap(func):
        """
        Decorator function used for histogram and map
        """
        @wraps(func)
        def inner_hm(self, **kwargs):
            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            maplabel = kwargs.get('maplabel', None)
            if maplabel :
                if not isinstance(maplabel,list):
                    maplabel = [maplabel]
            #if maplabel:
            #    maplabel = maplabel
            if 'map' in func.__name__:
                kwargs['maplabel'] = maplabel

            orientation = kwargs.get('orientation', list(InputOption().d_graphicsinput_args['orientation'])[0])
            dateslider = kwargs.get('dateslider',list(InputOption().d_graphicsinput_args['dateslider'])[0])
            #if orientation:
            #    kwargs['orientation'] = orientation
            #kwargs['dateslider'] = kwargs.get('dateslider',  self.dvisu_default['dateslider'])
            if isinstance(input['where'].iloc[0],list):
                input['rolloverdisplay'] = input['clustername']
                input = input.explode('where')
            else:
                input['rolloverdisplay'] = input['where']

            uniqloc = input.clustername.unique()

            geopdwd = input
            if type(geopdwd) != gpd.geodataframe.GeoDataFrame:
                if maplabel and 'unsorted' in maplabel:
                    pass
                else:
                    geopdwd = geopdwd.sort_values(by=input_field, ascending = False).reset_index(drop=True)

                started = geopdwd.date.min()
                ended = geopdwd.date.max()
                if func.__name__ in ['map']:
                    if isinstance(input['where'].iloc[0],list):
                        geom = self.kindgeo
                        geodic={}
                        for uclust in geopdwd['clustername'].unique():
                            loc = geopdwd.loc[geopdwd.clustername==uclust]['where'].iloc[0]
                            cumulgeo = list(geom.loc[geom['where'].isin(loc)]['geometry'])
                            geodic[uclust]=cumulgeo
                        #geodic={loc:geom.loc[geom['where']==loc]['geometry'].values[0] for loc in geopdwd['where'].unique()}
                        geopdwd.loc[:,'geometry'] = geopdwd.clustername.map(geodic)
                    else:
                        geopdwd = pd.merge(geopdwd, self.kindgeo, on='where')
                    geopdwd = gpd.GeoDataFrame(geopdwd, geometry=geopdwd.geometry, crs="EPSG:4326")
            if func.__name__ == 'pycoa_histo':
                pos = {}
                new = pd.DataFrame()
                n = 0
                for i in uniqloc:
                    perloc = geopdwd.loc[geopdwd.clustername == i]
                    if all(perloc != 0):
                        pos = perloc.index[0]
                        if new.empty:
                            new = perloc
                        else:
                            new = pd.concat([new,perloc])
                        n += 1
                geopdwd = new.reset_index(drop=True)
            if dateslider:
                dateslider = dateslider
            else:
                dateslider = None
            kwargs['dateslider'] = dateslider
            kwargs['geopdwd'] = geopdwd.sort_values(by=input_field, ascending = False).reset_index()
            return func(self, **kwargs)
        return inner_hm
    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE '''
    def decohistopie(func):
        @wraps(func)
        def inner_decohistopie(self, **kwargs):
            """
            Decorator for Horizontal histogram & Pie Chart
            It put in the kwargs:
            kwargs['geopdwd']-> pandas for input_field asked (all dates)
            kwargs['geopdwd_filter']-> pandas for input_field asked last dates
            kwargs['srcfiltered']-> a ColumnDataSource base on kwargs['geopdwd_filter'] this is only used for Bokeh
            """
            geopdwd = kwargs.get('geopdwd')
            input_field = kwargs.get('input_field')
            if isinstance(input_field,list):
                input_field = input_field[0]
            plot_width = kwargs.get('plot_width',InputOption().d_graphicsinput_args['plot_width'])
            plot_height = kwargs.get('plot_height',InputOption().d_graphicsinput_args['plot_height'])

            geopdwd['cases'] = geopdwd[input_field]
            geopdwd_filter = geopdwd.loc[geopdwd.date == self.when_end]
            geopdwd_filter = geopdwd_filter.reset_index(drop = True)
            geopdwd_filter['cases'] = geopdwd_filter[input_field]
            dateslider = kwargs.get('dateslider',InputOption().d_graphicsinput_args['dateslider'][0])
            maplabel = kwargs.get('maplabel',InputOption().d_graphicsinput_args['maplabel'][0])
            my_date = geopdwd.date.unique()

            if kwargs['vis']=='bokeh':
                dico_utc = {i: DateSlider(value=i).value for i in my_date}
                geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
            #geopdwd = geopdwd.drop_duplicates(["date", "code","clustername"])#for sumall avoid duplicate
            #geopdwd_filter = geopdwd_filter.drop_duplicates(["date", "code","clustername"])
            geopdwd = geopdwd.drop_duplicates(["date","clustername"])#for sumall avoid duplicate
            geopdwd_filter = geopdwd_filter.drop_duplicates(["date","clustername"])
            locunique = geopdwd_filter.clustername.unique()#geopdwd_filtered['where'].unique()
            geopdwd_filter = geopdwd_filter.copy()
            nmaxdisplayed = Max_Countries_Default
            toggl = None

            if len(locunique) >= nmaxdisplayed :#and func.__name__ != 'pycoa_pie' :
                if func.__name__ != 'pycoa_pie' :
                    geopdwd_filter = geopdwd_filter.loc[geopdwd_filter.clustername.isin(locunique[:nmaxdisplayed])]
                else:
                    geopdwd_filter_first = geopdwd_filter.loc[geopdwd_filter.clustername.isin(locunique[:nmaxdisplayed-1])]
                    geopdwd_filter_other = geopdwd_filter.loc[geopdwd_filter.clustername.isin(locunique[nmaxdisplayed-1:])]
                    geopdwd_filter_other = geopdwd_filter_other.groupby('date').sum()
                    geopdwd_filter_other['where'] = 'others'
                    geopdwd_filter_other['clustername'] = 'others'
                    geopdwd_filter_other['code'] = 'others'
                    geopdwd_filter_other['permanentdisplay'] = 'others'
                    geopdwd_filter_other['rolloverdisplay'] = 'others'
                    geopdwd_filter_other['colors'] = '#FFFFFF'

                    geopdwd_filter = geopdwd_filter_first
                    geopdwd_filter = pd.concat([geopdwd_filter,geopdwd_filter_other])
            if func.__name__ == 'pycoa_horizonhisto' :
                #geopdwd_filter['bottom'] = geopdwd_filter.index
                geopdwd_filter['left'] = geopdwd_filter['cases']
                geopdwd_filter['right'] = geopdwd_filter['cases']
                geopdwd_filter['left'] = geopdwd_filter['left'].apply(lambda x: 0 if x > 0 else x)
                geopdwd_filter['right'] = geopdwd_filter['right'].apply(lambda x: 0 if x < 0 else x)

                n = len(geopdwd_filter.index)
                ymax = InputOption().d_graphicsinput_args['plot_height']

                geopdwd_filter['top'] = [ymax*(n-i)/n + 0.5*ymax/n   for i in range(n)]
                geopdwd_filter['bottom'] = [ymax*(n-i)/n - 0.5*ymax/n for i in range(n)]
                geopdwd_filter['horihistotexty'] = geopdwd_filter['bottom'] + 0.5*ymax/n
                geopdwd_filter['horihistotextx'] = geopdwd_filter['right']

                if 'label%' in maplabel:
                    geopdwd_filter['right'] = geopdwd_filter['right'].apply(lambda x: 100.*x)
                    geopdwd_filter['horihistotextx'] = geopdwd_filter['right']
                    geopdwd_filter['horihistotext'] = [str(round(i))+'%' for i in geopdwd_filter['right']]
                if 'textinteger' in maplabel:
                    geopdwd_filter['horihistotext'] = geopdwd_filter['right'].astype(float).astype(int).astype(str)
                else:
                    geopdwd_filter['horihistotext'] = [ '{:.3g}'.format(float(i)) if float(i)>1.e4 or float(i)<0.01 else round(float(i),2) for i in geopdwd_filter['right'] ]
                    geopdwd_filter['horihistotext'] = [str(i) for i in geopdwd_filter['horihistotext']]

            if maplabel and 'label%' in maplabel:
                geopdwd_filter['textdisplayed2'] = geopdwd_filter['percentage']
                geopdwd['textdisplayed2'] =  geopdwd['percentage']
            input_filter = geopdwd_filter

            #kwargs['srcfiltered']=srcfiltered
            #kwargs['panels']=panels
            #kwargs['dateslider']=dateslider
            #kwargs['toggl']=toggl
            kwargs['geopdwd']=geopdwd
            kwargs['geopdwd_filter']=geopdwd_filter
            return func(self,**kwargs)
        return inner_decohistopie

    @decowrapper
    @decoplot
    def plot(self,**kwargs):
        typeofplot = kwargs.get('typeofplot')
        vis = kwargs.get('vis')
        if vis == 'matplotlib':
            if typeofplot == 'date':
                fig = matplotlib_visu().pycoa_mpltdate_plot(**kwargs)
            elif typeofplot == 'versus':
                fig = matplotlib_visu().pycoa_mpltversus_plot(**kwargs)
            elif typeofplot == 'yearly':
                fig = matplotlib_visu().pycoa_mpltyearly_plot(**kwargs)
            else:
                raise CoaKeyError('For display: '+self.getdisplay() +' unknown type of plot '+typeofplot)
        elif vis =='seaborn':
            if typeofplot == 'date':
                fig = seaborn_visu().pycoa_date_plot_seaborn(**kwargs)
            else:
                print(typeofplot + ' not implemented in ' + self.getdisplay())
        elif vis == 'bokeh':
            if typeofplot == 'date':
                fig = bokeh_visu().pycoa_date_plot(**kwargs)
            elif typeofplot == 'spiral':
                fig = bokeh_visu().pycoa_spiral_plot(**kwargs)
            elif typeofplot == 'versus':
                if isinstance(input_field,list) and len(input_field) == 2:
                    fig = bokeh_visu().pycoa_plot(**kwargs)
                else:
                    print('typeofplot is versus but dim(input_field)!=2, versus has not effect ...')
                    fig = bokeh_visu().pycoa_date_plot(**kwargs)
            elif typeofplot == 'menulocation':
                if _db_list_dict[self.db][1] == 'nation' and _db_list_dict[self.db][2] != 'World':
                    print('typeofplot is menulocation with a national DB granularity, use date plot instead ...')
                    fig = bokeh_visu().plot(*kwargs)
                else:
                    if isinstance(input_field,list) and len(input_field) > 1:
                        CoaWarning('typeofplot is menulocation but dim(input_field)>1, take first one '+input_field[0])
                    fig = bokeh_visu().pycoa_menu_plot(**kwargs)
            elif typeofplot == 'yearly':
                if input.date.max()-input.date.min() <= dt.timedelta(days=365):
                    print("Yearly will not be used since the time covered is less than 1 year")
                    fig = matplotlib_visu().pycoa_date_plot(**kwargs)
                else:
                    fig = matplotlib_visu().pycoa_yearly_plot(**kwargs)
        else:
            print(" Not implemented yet ")
        return fig

    @decowrapper
    @decohistomap
    @decohistopie
    def hist(self,**kwargs):
        typeofhist = kwargs.get('typeofhist')
        vis = kwargs.get('vis')
        if vis == 'matplotlib':
            if typeofhist == 'bylocation':
                fig = matplotlib_visu().pycoa_mplthorizontalhisto(**kwargs)
            elif typeofhist == 'byvalue':
                fig = matplotlib_visu().pycoa_mplthisto(**kwargs)
            elif typeofhist == 'pie':
                fig = matplotlib_visu().pycoa_mpltpie(**kwargs)
            else:
                raise CoaError(typeofhist + ' not implemented in ' + self.getdisplay())
        elif vis == 'bokeh':
            if typeofhist == 'bylocation':
                if 'bins' in kwargs:
                    raise CoaKeyError("The bins keyword cannot be set with histograms by location. See help.")
                fig = self.allvisu.pycoa_horizonhisto(**kwargs)
            elif typeofhist == 'byvalue':
                if dateslider:
                    info('dateslider not implemented for typeofhist=\'byvalue\'.')
                    fig = self.allvisu.pycoa_horizonhisto(**kwargs)
                else:
                    fig = self.allvisu.pycoa_histo( **kwargs)
            elif typeofhist == 'pie':
                fig = self.allvisu.pycoa_pie(**kwargs)
        elif vis == 'seaborn':
            if typeofhist == 'bylocation':
                fig = seaborn_visu().pycoa_hist_seaborn_hori( **kwargs)
            elif typeofhist == 'pie':
                fig = seaborn_visu().pycoa_pairplot_seaborn(**kwargs)
            elif typeofhist == 'byvalue':
                fig = seaborn_visu().pycoa_hist_seaborn_value( **kwargs)
            else:
                print(typeofhist + ' not implemented in ' + vis)
        else:
            print( "\n not yet implemented \n")
        return fig

    @decowrapper
    @decohistomap
    def map(self,**kwargs):
        dateslider = kwargs.get('dateslider')
        vis = kwargs.get('vis')
        maplabel = kwargs.get('maplabel')
        geopdwd = kwargs.get('geopdwd')
        if vis == 'matplotlib':
            return matplotlib_visu().pycoa_mpltmap(**kwargs)
        elif vis == 'seaborn':
            return seaborn_visu().pycoa_heatmap_seaborn(**kwargs)
        elif vis == 'bokeh':
            if maplabel:
                if 'spark' in maplabel or 'spiral' in maplabel:
                    fig = bokeh_visu().pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in maplabel:
                    fig = bokeh_visu().pycoa_map(**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                fig = bokeh_visu().pycoa_map(**kwargs)
            return show(fig)
        elif vis == 'folium':
            if dateslider is not None :
                raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
            if  maplabel and set(maplabel) != set(['log']):
                raise CoaKeyError('Not available with folium map, you should considere to use bokeh map visu in this case')
            return matplotlib_visu().pycoa_mapfolium(**kwargs)
        else:
            self.setdisplay('matplotlib')
            raise CoaTypeError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'mplt\' \
            aka matplotlib .See help.')

##### MATPLOLIB VISUALISATION #####
class matplotlib_visu():
    '''
        MATPLOTLIB chart drawing methods ...
    '''
    def __init__(self,):
        pass

    def decomatplotlib(func):
        def wrapper(self,**kwargs):
            import matplotlib.pyplot as plt
            kwargs['plt'] = plt
            fig, ax = plt.subplots(1, 1,figsize=(12, 8))
            kwargs['fig'] = fig
            kwargs['ax']=ax
            return func(self,**kwargs)
        return wrapper

    @decomatplotlib
    def pycoa_mpltdate_plot(self,**kwargs):
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        if not isinstance(input_field,list):
            input_field=[input_field]
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        loc = list(input['clustername'].unique())
        for val in input_field:
            df = pd.pivot_table(input,index='date', columns='clustername', values=val)
            leg=[]
            for col in loc:
                ax = plt.plot(df.index, df[col])
                leg.append(val+' '+col)
            plt.legend(leg)
        plt.title(title)
        return plt

    @decomatplotlib
    def pycoa_mpltversus_plot(self,**kwargs):
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        if len(input_field) != 2:
            CoaError("Can't make versus plot in the condition len("+input_field+")!=2")

        loc = list(input['clustername'].unique())
        leg=[]
        for col in loc:
            pandy=input.loc[input.clustername.isin([col])]
            ax=plt.plot(pandy[input_field[0]], pandy[input_field[1]])
            leg.append(col)
        plt.legend(leg)
        plt.title(title)
        return

    @decomatplotlib
    def pycoa_mpltyearly_plot(self,**kwargs):
        '''
         matplotlib date yearly plot chart
         Max display defined by Max_Countries_Default
        '''
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        input['date']=pd.to_datetime(input["date"])
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)

        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)

        loc = input['clustername'][0]
        d = input.allyears.unique()
        for i in d:
            df = pd.pivot_table(input.loc[input.allyears==i],index='dayofyear', columns='clustername', values=input_field)
            ax = plt.plot(df.index, df[loc])
        plt.legend(d)
        plt.title(title)
        return plt

    @decomatplotlib
    def pycoa_mpltpie(self,**kwargs):
        '''
         matplotlib pie chart
         Max display defined by Max_Countries_Default
        '''
        geopdwd_filter = kwargs.get('geopdwd_filter')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        geopdwd_filter = geopdwd_filter.sort_values(by=[input_field]).set_index('clustername')
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        ax = geopdwd_filter.plot(kind="pie",y=input_field, autopct='%1.1f%%', legend=True,
        title=input_field, ylabel=input_field, labeldistance=None)
        ax.legend(bbox_to_anchor=(1, 1.02), loc='upper left')
        ax.set_title(title)
        return plt

    @decomatplotlib
    def pycoa_mplthorizontalhisto(self,**kwargs):
        '''
        matplotlib horizon histo
        '''
        geopdwd_filter = kwargs.get('geopdwd_filter')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        geopdwd_filter = geopdwd_filter.sort_values(by=[input_field])
        plt = kwargs.get('plt')
        cmap = plt.get_cmap('Paired')
        ax = kwargs.get('ax')
        fig = kwargs.get('fig')
        bar = ax.barh(geopdwd_filter['clustername'], geopdwd_filter[input_field],color=cmap.colors)
        ax.set_title(title)
        return fig

    @decomatplotlib
    def pycoa_mplthisto(self,**kwargs):
        '''
        matplotlib vertical histo
        '''
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        input = input.loc[input.date==input.date.max()][:Max_Countries_Default]
        loc = input['where'].unique()[:Max_Countries_Default]
        bins=len(input['where'])+1
        input= pd.pivot_table(input,index='date', columns='where', values=input_field)
        ax = input.plot.hist(bins=bins, alpha=0.5,title = title)
        return plt

    @decomatplotlib
    def pycoa_mpltmap(self,**kwargs):
        '''
         matplotlib map display
        '''
        from matplotlib.colors import Normalize
        from matplotlib import cm
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        plt.axis('off')
        geopdwd = kwargs.get('geopdwd')
        input_field = kwargs.get('input_field')
        geopdwd = gpd.GeoDataFrame(geopdwd.loc[geopdwd.date==geopdwd.date.max()])
        fig = geopdwd.plot(column=input_field, ax=ax,legend=True,
                                legend_kwds={'label': input_field,
                                'orientation': "horizontal","pad": 0.001})
        ax.set_title(title)
        return plt
##### SEABORN VISUALISATION #####
class seaborn_visu():
    ######SEABORN#########
    ######################
    def __init__(self,):
        pass

    def decoplotseaborn(func):
        """
        decorator for seaborn plot
        """
        @wraps(func)
        def inner_plot(self, **kwargs):
            import matplotlib.pyplot as plt
            import seaborn as sns
            fig, ax = plt.subplots(1, 1,figsize=(12, 8))
            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            title = f"Graphique de {input_field}"
            if 'where' in kwargs:
                title += f" - {kwargs.get('where')}"
            kwargs['title'] = title
            # top_countries = (input.groupby('where')[input_field].sum()
            #              .nlargest(Max_Countries_Default).index.tolist())
            # filtered_input = input[input['where'].isin(top_countries)]

            loc = list(input['clustername'].unique())
            kwargs['plt'] = plt
            kwargs['sns'] = sns
            return func(self, **kwargs)
        return inner_plot

    def decohistseaborn(func):
        """
        decorator for seaborn histogram
        """
        @wraps(func)
        def inner_hist(self,**kwargs):
            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            if isinstance(input_field, list):
                input_field = input_field[0]

            input = (input.sort_values('date')
                  .drop_duplicates('clustername', keep='last')
                  .drop_duplicates(['clustername', input_field])
                  .sort_values(by=input_field, ascending=False)
                  .reset_index(drop=True))

            kwargs['input'] = input
            return func(self, **kwargs)
        return inner_hist

    #####SEABORN PLOT#########
    @decoplotseaborn
    def pycoa_date_plot_seaborn(self, **kwargs):
        """
        Create a seaborn line plot with date on x-axis and input_field on y-axis.
        """
        input = kwargs['input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        st=['-','--',':']
        sns.lineplot(data=input, x='date', y=input_field, hue='clustername')#,linestyle=st[k%len(st)])

        plt.legend(title= "Species", loc= "upper right",bbox_to_anchor=(1.04, 1))
        plt.title(title)
        plt.xlabel('Date')
        #plt.ylabel(', '.join(input_field))
        plt.xticks(rotation=45)
        return plt

    @decoplotseaborn
    def pycoa_versus_plot_seaborn(self, **kwargs):
        input = kwargs['input']
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')
        if isinstance(input_field, list):
            input_field = input_field
        if not isinstance(input_field, list) or len(input_field) != 2:
            raise ValueError("input_field should be a list of two variables.")
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(12, 8))

        loc = list(input['clustername'].unique())
        leg = []
        for col in loc:
            pandy = input.loc[input.clustername == col]
            sns.lineplot(data=pandy, x=input_field[0], y=input_field[1], label=col)
            leg.append(col)

        plt.legend()
        plt.title(title)
        plt.xlabel(input_field[0])
        plt.ylabel(input_field[1])
        plt.show()

    @decoplotseaborn
    @decohistseaborn
    def pycoa_hist_seaborn_verti(self, **kwargs):
        """
        Create a seaborn vertical histogram with input_field on y-axis.
        """
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')

        # Créer le graphique
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.barplot(data=filtered_input, x='where', y=input_field, palette="viridis")
        plt.title(title)
        plt.xlabel('')  # Suppression de l'étiquette de l'axe x
        plt.ylabel(input_field)
        plt.xticks(rotation=70, ha='center')  # Rotation à 70 degrés et alignement central
        plt.show()

    @decohistseaborn
    def pycoa_hist_seaborn_value(self, **kwargs):
        """
        Create a seaborn vertical histogram where the x-axis represents a numerical field.
        """
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')
        if isinstance(input_field, list):
            input_field = input_field[0]

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.histplot(data=filtered_input, x=input_field, bins=24, color='blue', kde=True)
        plt.title(title)
        plt.xlabel(input_field)
        plt.ylabel('Fréquence')
        plt.show()

    ######SEABORN HIST HORIZONTALE#########
    @decoplotseaborn
    @decohistseaborn
    def pycoa_hist_seaborn_hori(self, **kwargs):
        """
        Create a seaborn horizontal histogram with input_field on x-axis.
        """
        input = kwargs['input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        if isinstance(input_field, list):
            input_field = input_field[0]

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.barplot(data=input, x=input_field, y='clustername', palette="viridis", errorbar=None)
        plt.title(title)
        plt.xlabel(input_field)
        plt.ylabel('')
        plt.xticks(rotation=45)
        return plt

    ######SEABORN BOXPLOT#########
    @decoplotseaborn
    def pycoa_pairplot_seaborn(self, **kwargs):
        """
        Create a seaborn pairplot
        """
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        # Créer le graphique
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.pairplot(data=filtered_input, hue='where')
        plt.xlabel(input_field)
        plt.ylabel('')
        plt.xticks(rotation=45)
        plt.show()

    ######SEABORN heatmap#########
    @decoplotseaborn
    def pycoa_heatmap_seaborn(self, **kwargs):
        """
        Create a seaborn heatmap
        """
        CoaWarning("BEWARE !!! THIS visulasation need to be checked !!!")
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        # Convertir la colonne 'date' en datetime si nécessaire
        #if not pd.api.types.is_datetime64_any_dtype(input['date']):
        #    input['date'] = pd.to_datetime(input['date'])

        #df=input
        #df.date=pd.to_datetime(df.date)
        #input = input.groupby(pd.Grouper(key='date', freq='1M'))['daily'].sum().reset_index

        # On inclut que les premiers 24 pays uniques
        # top_locations = input['where'].unique()[:Max_Countries_Default]
        # filtered_input = input[input['where'].isin(top_locations)]

        input['month'] = [m.month for m in input['date']]
        input['year'] = [m.year for m in input['date']]

        data_pivot = input.pivot_table(index='month', columns='year', values='daily')

        total = data_pivot.sum().sum()

        sns.heatmap(data_pivot, annot=True, fmt=".1f", linewidths=.5, cmap='plasma')
        plt.title(f'Heatmap of {input_field.replace("_", " ").capitalize()} by Month and Year')
        plt.xlabel('Year')
        plt.ylabel('Month')

        # Afficher le total en dehors du graphique
        plt.text(0, data_pivot.shape[0] + 1, f'Total: {total}', fontsize=12)
        return plt
##### BOKEH VISUALISATION #####
class bokeh_visu():
    def __init__(self,):
        self.pycoageopandas = False
        if type(input)==gpd.geodataframe.GeoDataFrame:
            self.pycoageopandas = True
        self.when_beg = dt.date(1, 1, 1)
        self.when_end = dt.date(1, 1, 1)

    @staticmethod
    def min_max_range(a_min, a_max):
        """ Return a cleverly rounded min and max giving raw min and raw max of data.
        Usefull for hist range and colormap
        """
        min_p = 0
        max_p = 0
        if a_min != 0:
            min_p = math.floor(math.log10(math.fabs(a_min)))  # power
        if a_max != 0:
            max_p = math.floor(math.log10(math.fabs(a_max)))

        if a_min == 0:
            if a_max == 0:
                p = 0
            else:
                p = max_p
        else:
            if a_max == 0:
                p = min_p
            else:
                p = max(min_p, max_p)

        if a_min != 0:
            min_r = math.floor(a_min / 10 ** (p - 1)) * 10 ** (p - 1)  # min range rounded
        else:
            min_r = 0

        if a_max != 0:
            max_r = math.ceil(a_max / 10 ** (p - 1)) * 10 ** (p - 1)
        else:
            max_r = 0

        if min_r == max_r:
            if min_r == 0:
                min_r = -1
                max_r = 1
                k = 0
            elif max_r > 0:
                k = 0.1
            else:
                k = -0.1
            max_r = (1 + k) * max_r
            min_r = (1 - k) * min_r

        return (min_r, max_r)

    @staticmethod
    def rollerJS():
        from bokeh.models import CustomJSHover
        return CustomJSHover(code="""
                var value;
                 //   if(Math.abs(value)>100000 || Math.abs(value)<0.001)
                 //       return value.toExponential(2);
                 //   else
                 //       return value.toFixed(2);
                 if(value>10000 || value <0.01)
                    value =  Number.parseFloat(value).toExponential(2);
                 else
                     value = Number.parseFloat(value).toFixed(2);
                return value.toString();
                /*  var s = value;
                  var s0=s;
                  var sp1=s.split(".");
                  var p1=sp1[0].length
                  if (sp1.length>1) {
                    var sp2=s.split("e");
                    var p2=sp2[0].length
                    var p3=p2
                    while(s[p2-1]=="0" && p2>p1) {
                        p2=p2-1;
                    }
                    s=s0.substring(0,p2)+s0.substring(p3,s0.length);
                  }
                  if (s.split(".")[0].length==s.length-1) {
                    s=s.substring(0,s.length-1);
                  }
                  return s;*/
                """)

    def importbokeh(func):
        def wrapper(self,**kwargs):
            """
            ALL Librairies (and more) needs by bokeh
            """
            from bokeh.models import (
            ColumnDataSource,
            TableColumn,
            DataTable,
            ColorBar,
            LogTicker,
            HoverTool,
            CrosshairTool,
            BasicTicker,
            GeoJSONDataSource,
            LinearColorMapper,
            LogColorMapper,
            Label,
            PrintfTickFormatter,
            BasicTickFormatter,
            NumeralTickFormatter,
            CustomJS,
            CustomJSHover,
            Select,
            Range1d,
            DatetimeTickFormatter,
            Legend,
            LegendItem,
            Text
            )
            from bokeh.models.layouts import TabPanel, Tabs
            from bokeh.plotting import figure
            from bokeh.layouts import (
            row,
            column,
            gridplot
            )
            from bokeh.palettes import (
            Category10,
            Category20,
            Viridis256
            )
            from bokeh.models import Title

            from bokeh.io import export_png
            from bokeh import events
            from bokeh.models.widgets import DateSlider
            from bokeh.models import (
            LabelSet,
            WMTSTileSource
            )
            from bokeh.transform import (
            transform,
            cumsum
            )
            kwargs['GeoJSONDataSource'] = GeoJSONDataSource
            kwargs['Viridis256'] = Viridis256
            kwargs['LinearColorMapper'] = LinearColorMapper
            kwargs['ColorBar'] = ColorBar
            kwargs['BasicTicker'] = BasicTicker
            kwargs['BasicTickFormatter'] = BasicTickFormatter
            kwargs['Label'] = Label
            kwargs['figure'] = 'figure'
            return func(self,**kwargs)
        return wrapper

    def standardfig(self, **kwargs):
        """
         Create a standard Bokeh figure, with pycoa_fr copyright, used in all the bokeh charts
        """
        print("------>>",kwargs)
        copyright = kwargs.get('copyright',InputOption().d_graphicsinput_args['copyright'])
        plot_width = kwargs.get('plot_width',InputOption().d_graphicsinput_args['plot_width'])
        plot_height = kwargs.get('plot_height',InputOption().d_graphicsinput_args['plot_height'])
        Label = kwargs.get('Label')
        figure = kwargs.get('figure')
        print('copyright\n',copyright)
        #citation = Label(x=0.65 * plot_width - len(copyright), y=0.01 *plot_height,
        #                                  x_units='screen', y_units='screen',
        #                                  text_font_size='1.5vh', background_fill_color='white',
        #                                  background_fill_alpha=.75,
        #                                  text=copyright)

        fig = figure(plot_width=plot_width,plot_height=plot_height, tools=['save', 'box_zoom,reset'],
                        toolbar_location="right", sizing_mode="stretch_width")
        #fig.add_layout(citation)
        fig.add_layout(Title(text=self.uptitle, text_font_size="10pt"), 'above')
        if 'innerdecomap' not in inspect.stack()[1].function:
            fig.add_layout(Title(text=self.subtitle, text_font_size="8pt", text_font_style="italic"), 'below')
        return fig

    def set_tile(self,tile):
        if tile in list(InputOption().d_graphicsinput_args['tile']):
            self.tile = tile
        else:
            raise CoaTypeError('Don\'t know the tile you want. So far:' + str(list(InputOption().d_graphicsinput_args['tile'])))

    def get_listfigures(self):
        return  self.listfigs

    def set_listfigures(self,fig):
            if not isinstance(fig,list):
                fig = [fig]
            self.listfigs = fig

    def pycoa_resume_data(self,**kwargs):
        loc=list(input['clustername'].unique())
        input['cases'] = input[input_field]
        resumetype = kwargs.get('resumetype','spiral')
        if resumetype == 'spiral':
            dspiral={i:AllVisu.spiral(input.loc[ (input.clustername==i) &
                        (input.date >= self.when_beg) &
                        (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
            input['resume']=input['clustername'].map(dspiral)
        elif resumetype == 'spark':
            spark={i:AllVisu.sparkline(input.loc[ (input.clustername==i) &
                        (input.date >= self.when_beg) &
                        (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
            input['resume']=input['clustername'].map(spark)
        else:
            raise CoaError('pycoa_resume_data can use spiral or spark ... here what ?')
        input = input.loc[input.date==input.date.max()].reset_index(drop=True)
        def path_to_image_html(path):
            return '<img src="'+ path + '" width="60" >'

        input=input.drop(columns=['permanentdisplay','rolloverdisplay','colors','cases'])
        input=input.apply(lambda x: x.round(2) if x.name in [input_field,'daily','weekly'] else x)
        if isinstance(input['where'][0], list):
            col=[i for i in list(input.columns) if i not in ['clustername','where','code']]
            col.insert(0,'clustername')
            input = input[col]
            input=input.set_index('clustername')
        else:
           input = input.drop(columns='clustername')
           input=input.set_index('where')

        return input.to_html(escape=False,formatters=dict(resume=path_to_image_html))

    ''' PLOT VERSUS '''
    def pycoa_plot(self,**kwargs):
        '''
        -----------------
        Create a versus plot according to arguments.
        See help(pycoa_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element. It should be a list dim=2. Moreover the 2 variables must be present
        in the DataFrame considered.
        - plot_heigh = Width_Height_Default[1]
        - plot_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        mode = kwargs.get('mode',list(self.d_graphicsinput_args['mode'])[0])
        if len(input_field) != 2:
            raise CoaTypeError('Two variables are needed to plot a versus chart ... ')
        panels = []
        cases_custom = bokeh_visu().rollerJS()
        if self.get_listfigures():
            self.set_listfigures([])
        listfigs=[]
        for axis_type in self.optionvisu.ax_type:
            standardfig = self.standardfig( x_axis_label = input_field[0], y_axis_label = input_field[1],
                                                y_axis_type = axis_type, **kwargs )

            standardfig.add_tools(HoverTool(
                tooltips=[('where', '@rolloverdisplay'), ('date', '@date{%F}'),
                          (input_field[0], '@{casesx}' + '{custom}'),
                          (input_field[1], '@{casesy}' + '{custom}')],
                formatters={'where': 'printf', '@{casesx}': cases_custom, '@{casesy}': cases_custom,
                            '@date': 'datetime'}, mode = mode,
                point_policy="snap_to_data"))  # ,PanTool())

            for loc in input.clustername.unique():
                pandaloc = input.loc[input.clustername == loc].sort_values(by='date', ascending=True)
                pandaloc.rename(columns={input_field[0]: 'casesx', input_field[1]: 'casesy'}, inplace=True)
                standardfig.line(x='casesx', y='casesy',
                                 source=ColumnDataSource(pandaloc), legend_label=pandaloc.clustername.iloc[0],
                                 color=pandaloc.colors.iloc[0], line_width=3, hover_line_width=4)

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig, title=axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "top_left"
            listfigs.append(standardfig)
            AllVisu.bokeh_legend(standardfig)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' DATE PLOT '''
    def pycoa_date_plot(self,**kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(pycoa_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - plot_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - guideline = False
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        if not isinstance(kwargs.get('input_field'),list):
            input_field = [input_field]

        mode = kwargs.get('mode',list(InputOption().d_graphicsinput_args['mode'])[0])
        guideline = kwargs.get('guideline',list(InputOption().d_graphicsinput_args['guideline'])[0])

        panels = []
        listfigs = []
        cases_custom = bokeh_visu().rollerJS()

        if isinstance(input['rolloverdisplay'].iloc[0],list):
            input['rolloverdisplay'] = input['clustername']
        for axis_type in InputOption().ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type, x_axis_type = 'datetime',**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
            lcolors = iter(InputOption().lcolors)
            line_style = ['solid', 'dashed', 'dotted', 'dotdash','dashdot']
            maxou,minou=0,0
            tooltips=[]
            for val in input_field:
                for loc in list(input.clustername.unique()):
                    input_filter = input.loc[input.clustername == loc].reset_index(drop = True)
                    src = ColumnDataSource(input_filter)
                    leg = loc
                    #leg = input_filter.permanentdisplay[0]
                    if len(input_field)>1:
                        leg = input_filter.permanentdisplay[0] + ', ' + val
                    if len(list(input.clustername.unique())) == 1:
                        color = next(lcolors)
                    else:
                        color = input_filter.colors[0]

                    r = standardfig.line(x = 'date', y = val, source = src,
                                     color = color, line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = val, line_dash=line_style[i%4])
                    r_list.append(r)
                    maxou=max(maxou,np.nanmax(input_filter[val].values))
                    minou=max(minou,np.nanmin(input_filter[val].values))

                    if minou <0.01:
                        tooltips.append([('where', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name')])
                    else:
                        tooltips.append([('where', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')])
                    if isinstance(tooltips,tuple):
                        tooltips = tooltips[0]
                i += 1
            for i,r in enumerate(r_list):
                label = r.name
                tt = tooltips[i]
                formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
                hover=HoverTool(tooltips = tt, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
                standardfig.add_tools(hover)

                if guideline:
                    cross= CrosshairTool()
                    standardfig.add_tools(cross)

            if axis_type == 'linear':
                if maxou  < 1e4 :
                    standardfig.yaxis.formatter = BasicTickFormatter(use_scientific=False)

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig, title = axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location  = "top_left"
            standardfig.legend.click_policy="hide"
            standardfig.legend.label_text_font_size = '8pt'
            if len(input_field) > 1 and len(input_field)*len(input.clustername.unique())>16:
                CoaWarning('To much labels to be displayed ...')
                standardfig.legend.visible=False
            standardfig.xaxis.formatter = DatetimeTickFormatter(
                days = ["%d/%m/%y"], months = ["%d/%m/%y"], years = ["%b %Y"])
            AllVisu.bokeh_legend(standardfig)
            listfigs.append(standardfig)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' SPIRAL PLOT '''
    def pycoa_spiral_plot(self, **kwargs):
        panels = []
        listfigs = []
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')

        if isinstance(input['rolloverdisplay'].iloc[0],list):
            input['rolloverdisplay'] = input['clustername']
        borne = 300

        standardfig = self.standardfig(x_range=[-borne, borne], y_range=[-borne, borne], match_aspect=True,**kwargs)

        if len(input.clustername.unique()) > 1 :
            print('Can only display spiral for ONE location. I took the first one:', input.clustername[0])
            input = input.loc[input.clustername == input.clustername[0]].copy()
        input['date']=pd.to_datetime(input["date"])
        input["dayofyear"]=input.date.dt.dayofyear
        input['year']=input.date.dt.year
        input['cases'] = input[input_field]

        K = 2*input[input_field].max()
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input["dayofyear_angle"] = input["dayofyear"]*2 * np.pi/365
        input["r_baseline"] = input.apply(lambda x : ((x["year"]-2020)*2 * np.pi + x["dayofyear_angle"])*K,axis=1)
        size_factor = 16
        input["r_cas_sup"] = input.apply(lambda x : x["r_baseline"] + 0.5*x[input_field]*size_factor,axis=1)
        input["r_cas_inf"] = input.apply(lambda x : x["r_baseline"] - 0.5*x[input_field]*size_factor,axis=1)

        radius = 200
        def polar(theta,r,norm=radius/input["r_baseline"].max()):
            x = norm*r*np.cos(theta)
            y = norm*r*np.sin(theta)
            return x,y
        x_base,y_base=polar(input["dayofyear_angle"],input["r_baseline"])
        x_cas_sup,y_cas_sup=polar(input["dayofyear_angle"],input["r_cas_sup"])
        x_cas_inf,y_cas_inf=polar(input["dayofyear_angle"],input["r_cas_inf"])

        xcol,ycol=[],[]
        [ xcol.append([i,j]) for i,j in zip(x_cas_inf,x_cas_sup)]
        [ ycol.append([i,j]) for i,j in zip(y_cas_inf,y_cas_sup)]
        standardfig.patches(xcol,ycol,color='blue',fill_alpha = 0.5)

        src = ColumnDataSource(data=dict(
        x=x_base,
        y=y_base,
        date=input['date'],
        cases=input['cases']
        ))
        standardfig.line( x = 'x', y = 'y', source = src, legend_label = input.clustername[0],
                        line_width = 3, line_color = 'blue')
        circle = standardfig.circle('x', 'y', size=2, source=src)

        cases_custom = bokeh_visu().rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               renderers=[circle],
                               point_policy="snap_to_data")
        standardfig.add_tools(hover_tool)

        outer_radius=250
        [standardfig.annular_wedge(
            x=0, y=0, inner_radius=0, outer_radius=outer_radius, start_angle=i*np.pi/6,\
            end_angle=(i+1)*np.pi/6,fill_color=None,line_color='black',line_dash='dotted')
        for i in range(12)]

        label = ['January','February','March','April','May','June','July','August','September','October','November','December']
        xr,yr = polar(np.linspace(0, 2 * np.pi, 13),outer_radius,1)
        standardfig.text(xr[:-1], yr[:-1], label,text_font_size="9pt", text_align="center", text_baseline="middle")

        standardfig.legend.background_fill_alpha = 0.6
        standardfig.legend.location = "top_left"
        standardfig.legend.click_policy="hide"
        return standardfig

    ''' SCROLLINGMENU PLOT '''
    def pycoa_menu_plot(self, **kwargs):
        '''
        -----------------
        Create a date plot, with a scrolling menu location, according to arguments.
        See help(pycoa_menu_plot).
        Keyword arguments
        -----------------
        len(location) > 2
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - plot_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - guideline = False
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''

        input = kwargs.get('input')
        input_field= kwargs.get('input_field')
        guideline = kwargs.get('guideline',self.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('guideline',self.d_graphicsinput_args['mode'][0])
        if isinstance(input_field,list):
            input_field=input_field[0]

        uniqloc = list(input.clustername.unique())
        uniqloc.sort()
        if 'where' in input.columns:
            if len(uniqloc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                   'There is no sens to use this method. See help.')
        input = input[['date', 'clustername', input_field]]
        input = input.sort_values(by='clustername', ascending = True).reset_index(drop=True)

        mypivot = pd.pivot_table(input, index='date', columns='clustername', values=input_field)
        column_order = uniqloc
        mypivot = mypivot.reindex(column_order, axis=1)
        source = ColumnDataSource(mypivot)

        filter_data1 = mypivot[[uniqloc[0]]].rename(columns={uniqloc[0]: 'cases'})
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = mypivot[[uniqloc[1]]].rename(columns={uniqloc[1]: 'cases'})
        src2 = ColumnDataSource(filter_data2)

        cases_custom = bokeh_visu().rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               mode = mode, point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in self.optionvisu.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type, x_axis_type = 'datetime', **kwargs)

            standardfig.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            standardfig.xaxis.formatter = DatetimeTickFormatter(
                days = ["%d/%m/%y"], months = ["%d/%m/%y"], years = ["%b %Y"])

            standardfig.add_tools(hover_tool)
            if guideline:
                cross= CrosshairTool()
                standardfig.add_tools(cross)
            def add_line(src, options, init, color):
                s = Select(options = options, value = init)
                r = standardfig.line(x = 'date', y = 'cases', source = src, line_width = 3, line_color = color)
                li = LegendItem(label = init, renderers = [r])
                s.js_on_change('value', CustomJS(args=dict(s0=source, s1=src, li=li),
                                                 code="""
                                            var c = cb_obj.value;
                                            var y = s0.data[c];
                                            s1.data['cases'] = y;
                                            li.label = {value: cb_obj.value};
                                            s1.change.emit();
                                     """))
                return s, li

            s1, li1 = add_line(src1, uniqloc, uniqloc[0], self.scolors[0])
            s2, li2 = add_line(src2, uniqloc, uniqloc[1], self.scolors[1])
            standardfig.add_layout(Legend(items = [li1, li2]))
            standardfig.legend.location = 'top_left'
            layout = row(column(row(s1, s2), row(standardfig)))
            panel = Panel(child = layout, title = axis_type)
            panels.append(panel)

        tabs = Tabs(tabs = panels)
        label = standardfig.title
        return tabs

    ''' YEARLY PLOT '''
    def pycoa_yearly_plot(self,**kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(pycoa_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - plot_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - guideline = False
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        input = kwargs['input']
        input_field = kwargs['input_field']
        guideline = kwargs.get('guideline',self.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('mode',self.d_graphicsinput_args['mode'][0])

        if len(input.clustername.unique()) > 1 :
            CoaWarning('Can only display yearly plot for ONE location. I took the first one:'+ input.clustername[0])
        if isinstance(input_field[0],list):
            input_field = input_field[0][0]
            CoaWarning('Can only display yearly plot for ONE which value. I took the first one:'+ input_field)

        input = input.loc[input.clustername == input.clustername[0]].copy()

        panels = []
        listfigs = []
        cases_custom = bokeh_visu().rollerJS()
        input['date']=pd.to_datetime(input["date"])
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        allyears = list(input.allyears.unique())
        if isinstance(input['rolloverdisplay'].iloc[0],list):
            input['rolloverdisplay'] = input['clustername']
        #if len(input_field)>1:
        #    CoaError('Only one variable could be displayed')
        #else:
        #    input_field=input_field[0]
        for axis_type in self.optionvisu.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type,**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
            input['cases']=input[input_field]
            line_style = ['solid', 'dashed', 'dotted', 'dotdash']
            colors = itertools.cycle(self.optionvisu.lcolors)
            for loc in list(input.clustername.unique()):
                for year in allyears:
                    input_filter = input.loc[(input.clustername == loc) & (input['date'].dt.year.eq(year))].reset_index(drop = True)
                    src = ColumnDataSource(input_filter)
                    leg = str(year) + ' ' + loc
                    r = standardfig.line(x = 'dayofyear', y = input_field, source = src,
                                     color = next(colors), line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = input_field)
                    maxou=max(maxou,np.nanmax(input_filter[input_field].values))

            label = input_field
            tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), ('Cases', '@cases{0,0.0}')]
            formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
            hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = mode)  # ,PanTool())
            standardfig.add_tools(hover)
            if guideline:
                cross= CrosshairTool()
                standardfig.add_tools(cross)

            if axis_type == 'linear':
                if maxou  < 1e4 :
                    standardfig.yaxis.formatter = BasicTickFormatter(use_scientific=False)

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig, title = axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "top_left"
            standardfig.legend.click_policy="hide"

            minyear=input.date.min().year
            labelspd=input.loc[(input.allyears.eq(2023)) & (input.date.dt.day.eq(1))]
            standardfig.xaxis.ticker = list(labelspd['dayofyear'].astype(int))
            replacelabelspd =  labelspd['date'].apply(lambda x: str(x.strftime("%b")))
            #label_dict = dict(zip(input.loc[input.allyears.eq(minyear)]['daymonth'],input.loc[input.allyears.eq(minyear)]['date'].apply(lambda x: str(x.day)+'/'+str(x.month))))
            standardfig.xaxis.major_label_overrides = dict(zip(list(labelspd['dayofyear'].astype(int)),list(replacelabelspd)))

            AllVisu.bokeh_legend(standardfig)
            listfigs.append(standardfig)

        tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')]
        formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
        hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
        standardfig.add_tools(hover)
        if guideline:
            cross= CrosshairTool()
            standardfig.add_tools(cross)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs


    ''' VERTICAL HISTO '''
    def pycoa_histo(self, **kwargs):
        '''
            -----------------
            Create 1D histogramme by value according to arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - geopdwd : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - plot_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - when : default min and max according to the inpude DataFrame.
                     Dates are given under the format dd/mm/yyyy.
                     when format [dd/mm/yyyy : dd/mm/yyyy]
                     if [:dd/mm/yyyy] min date up to
                     if [dd/mm/yyyy:] up to max date
        '''
        geopdwd=kwargs.get('geopdwd')
        input_field=kwargs.get('input_field')
        geopdwd_filter = geopdwd.loc[geopdwd.date == self.when_end]
        geopdwd_filter = geopdwd_filter.reset_index(drop = True)

        input = geopdwd_filter.rename(columns = {'cases': input_field})
        bins = kwargs.get('bins', self.dicochartargs['bins'])

        if 'where' in input.columns:
            uniqloc = list(input.clustername.unique())
            allval  = input.loc[input.clustername.isin(uniqloc)][['clustername', input_field,'permanentdisplay']]
            min_val = allval[input_field].min()
            max_val = allval[input_field].max()

            if bins:
                bins = bins
            else:
                if len(uniqloc) == 1:
                    bins = 2
                    min_val = 0.
                else:
                    bins = 11

            delta = (max_val - min_val ) / bins
            interval = [ min_val + i*delta for i in range(bins+1)]

            contributors = {  i : [] for i in range(bins+1)}
            for i in range(len(allval)):
                rank = bisect.bisect_left(interval, allval.iloc[i][input_field])
                if rank == bins+1:
                    rank = bins
                contributors[rank].append(allval.iloc[i]['clustername'])

            colors = itertools.cycle(self.optionvisu.lcolors)
            lcolors = [next(colors) for i in range(bins+1)]
            contributors = dict(sorted(contributors.items()))
            frame_histo = pd.DataFrame({
                              'left': [0]+interval[:-1],
                              'right':interval,
                              'middle_bin': [format((i+j)/2, ".1f") for i,j in zip([0]+interval[:-1],interval)],
                              'top': [len(i) for i in list(contributors.values())],
                              'contributors': [', '.join(i) for i in contributors.values()],
                              'colors': lcolors})
        #tooltips = """
        #<div style="width: 400px">
        #<b>Middle value:</b> @middle_bin <br>
        #<b>Contributors:</b> @contributors{safe} <br>
        #</div>
        #"""
        tooltips = """
        <b>Middle value:</b> @middle_bin <br>
        <b>Contributors:</b> @contributors{safe} <br>
        """
        hover_tool = HoverTool(tooltips = tooltips)
        panels = []
        bottom = 0
        x_axis_type, y_axis_type, axis_type_title = 3 * ['linear']
        for axis_type in ["linear", "linlog", "loglin", "loglog"]:
            if axis_type == 'linlog':
                y_axis_type, axis_type_title = 'log', 'logy'
            if axis_type == 'loglin':
                x_axis_type, y_axis_type, axis_type_title = 'log', 'linear', 'logx'
            if axis_type == 'loglog':
                x_axis_type, y_axis_type = 'log', 'log'
                axis_type_title = 'loglog'

            try:
                kwargs.pop('dateslider')
            except:
                pass
            standardfig = self.standardfig(x_axis_type=x_axis_type, y_axis_type=y_axis_type, **kwargs)

            standardfig.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            standardfig.add_tools(hover_tool)
            standardfig.x_range = Range1d(1.05 * interval[0], 1.05 * interval[-1])
            standardfig.y_range = Range1d(0, 1.05 * frame_histo['top'].max())
            if x_axis_type == "log":
                left = 0.8
                if frame_histo['left'][0] <= 0:
                    frame_histo.at[0, 'left'] = left
                else:
                    left  = frame_histo['left'][0]
                standardfig.x_range = Range1d(left, 10 * interval[-1])

            if y_axis_type == "log":
                bottom = 0.0001
                standardfig.y_range = Range1d(0.001, 10 * frame_histo['top'].max())

            standardfig.quad(source=ColumnDataSource(frame_histo), top='top', bottom=bottom, left='left', \
                             right='right', fill_color='colors')
            panel = Panel(child=standardfig, title=axis_type_title)
            panels.append(panel)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' VERTICAL HISTO '''
    def pycoa_horizonhisto(self, **kwargs):
        '''
            -----------------
            Create 1D histogramme by location according to arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - plot_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - mode = mouse
            - dateslider = None if True
                    - orientation = horizontal
            - when : default min and max according to the inpude DataFrame.
                         Dates are given under the format dd/mm/yyyy.
                         when format [dd/mm/yyyy : dd/mm/yyyy]
                         if [:dd/mm/yyyy] min date up to
                         if [dd/mm/yyyy:] up to max date
        '''
        srcfiltered=kwargs.get('srcfiltered')
        panels=kwargs.get('panels')
        dateslider=kwargs.get('dateslider')
        toggl=kwargs.get('toggl')
        n = len(panels)
        new_panels = []
        for i in range(n):
            fig = panels[i].child
            fig.y_range = Range1d(min(srcfiltered.data['bottom']), max(srcfiltered.data['top']))
            fig.yaxis[0].formatter = NumeralTickFormatter(format="0.0")
            ytick_loc = [int(i) for i in srcfiltered.data['horihistotexty']]
            fig.yaxis.ticker  = ytick_loc
            label_dict = dict(zip(ytick_loc,srcfiltered.data['permanentdisplay']))
            fig.yaxis.major_label_overrides = label_dict

            fig.quad(source = srcfiltered,
                top='top', bottom = 'bottom', left = 'left', right = 'right', color = 'colors', line_color = 'black',
                line_width = 1, hover_line_width = 2)

            labels = LabelSet(
                    x = 'horihistotextx',
                    y = 'horihistotexty',
                    x_offset=5,
                    y_offset=-4,
                    text = 'horihistotext',
                    source = srcfiltered,text_font_size='10px',text_color='black')
            fig.add_layout(labels)

            panel = Panel(child = fig, title = panels[i].title)
            new_panels.append(panel)
        tabs = Tabs(tabs = new_panels)
        if dateslider:
                tabs = column(dateslider,tabs,toggl)
        return tabs

    ''' PIE '''
    def add_columns_for_pie_chart(self,df,column_name):
        df = df.copy()
        column_sum = df[column_name].sum()
        df['percentage'] = df[column_name]/column_sum

        percentages = [0]  + df['percentage'].cumsum().tolist()
        df['angle'] = (df[column_name]/column_sum)*2 * np.pi
        df['starts'] = [p * 2 * np.pi for p in percentages[:-1]]
        df['ends'] = [p * 2 * np.pi for p in percentages[1:]]
        df['diff'] = (df['ends'] - df['starts'])
        df['middle'] = df['starts']+np.abs(df['ends']-df['starts'])/2.
        df['cos'] = np.cos(df['middle']) * 0.9
        df['sin'] = np.sin(df['middle']) * 0.9

        df['text_size'] = '8pt'

        df['textdisplayed'] = df['permanentdisplay'].str.pad(36, side = "left")
        try:
            locale.setlocale(locale.LC_ALL, 'en_US')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            except:
                raise CoaError("Locale setting problem. Please contact support@pycoa_fr")

        df['textdisplayed2'] =  ['      '+str(round(100*i,1))+'%' for i in df['percentage']]
        df.loc[df['diff'] <= np.pi/20,'textdisplayed']=''
        df.loc[df['diff'] <= np.pi/20,'textdisplayed2']=''
        return df

    def pycoa_pie(self, **kwargs):
        '''
            -----------------
            Create a pie chart according to arguments.
            See help(pycoa_pie).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - plot_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - mode = mouse
            - dateslider = None if True
                    - orientation = horizontal
        '''
        srcfiltered=kwargs.get('srcfiltered')
        panels=kwargs.get('panels')
        dateslider=kwargs.get('dateslider')
        toggl=kwargs.get('toggl')
        standardfig = panels[0].child
        standardfig.plot_height=400
        standardfig.plot_width=400
        standardfig.x_range = Range1d(-1.1, 1.1)
        standardfig.y_range = Range1d(-1.1, 1.1)
        standardfig.axis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None

        standardfig.wedge(x=0, y=0, radius=1.,line_color='#E8E8E8',
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'), fill_color='colors',
        legend_label='clustername', source=srcfiltered)
        standardfig.legend.visible = False

        labels = LabelSet(x=0, y=0,text='textdisplayed',angle=cumsum('angle', include_zero=True),
        text_font_size="10pt",source=srcfiltered,render_mode='canvas')

        labels2 = LabelSet(x=0, y=0, text='textdisplayed2',
        angle=cumsum('angle', include_zero=True),text_font_size="8pt",source=srcfiltered)

        standardfig.add_layout(labels)
        standardfig.add_layout(labels2)
        if dateslider:
            standardfig = column(dateslider,standardfig)
        return standardfig

    def decopycoageo(func):
        @wraps(func)
        def innerdecopycoageo(self,**kwargs):
            geopdwd = kwargs.get('geopdwd')
            input_field = kwargs.get("input_field")
            geopdwd['cases'] = geopdwd[input_field]
            loca=geopdwd['where'].unique()

            if self.pycoageopandas:
                locgeo=geopdwd.loc[geopdwd['where'].isin(loca)].drop_duplicates('where').set_index('where')['geometry']
                geopdwd=fill_missing_dates(geopdwd)
                geopdwd_filtered = geopdwd.loc[geopdwd.date == self.when_end]
                geopdwd_filtered_cp = geopdwd_filtered.copy()
                geopdwd_filtered_cp.loc[:,'geometry']=geopdwd_filtered_cp['where'].map(locgeo)
                geopdwd_filtered_cp.loc[:,'geometry']=geopdwd_filtered_cp['geometry'].to_crs(crs="EPSG:4326")
                geopdwd_filtered_cp.loc[:,'clustername']=geopdwd_filtered_cp['where']
                geopdwd_filtered = geopdwd_filtered_cp
            else:
                geopdwd_filtered = geopdwd.loc[geopdwd.date == self.when_end]
                geopdwd_filtered = geopdwd_filtered.reset_index(drop = True)
                geopdwd_filtered = gpd.GeoDataFrame(geopdwd_filtered, geometry=geopdwd_filtered.geometry, crs="EPSG:4326")
                geopdwd = geopdwd.sort_values(by=['clustername', 'date'], ascending = [True, False])
                geopdwd_filtered = geopdwd_filtered.sort_values(by=['clustername', 'date'], ascending = [True, False]).drop(columns=['date', 'colors'])
                new_poly = []
                geolistmodified = dict()

                for index, row in geopdwd_filtered.iterrows():
                    split_poly = []
                    new_poly = []
                    if row['geometry']:
                        for pt in self.get_polycoords(row):
                            if type(pt) == tuple:
                                new_poly.append(AllVisu.wgs84_to_web_mercator(pt))
                            elif type(pt) == list:
                                shifted = []
                                for p in pt:
                                    shifted.append(AllVisu.wgs84_to_web_mercator(p))
                                new_poly.append(sg.Polygon(shifted))
                            else:
                                raise CoaTypeError("Neither tuple or list don't know what to do with \
                                    your geometry description")

                        if type(new_poly[0]) == tuple:
                            geolistmodified[row['where']] = sg.Polygon(new_poly)
                        else:
                            geolistmodified[row['where']] = sg.MultiPolygon(new_poly)
                ng = pd.DataFrame(geolistmodified.items(), columns=['where', 'geometry'])
                geolistmodified = gpd.GeoDataFrame({'where': ng['where'], 'geometry': gpd.GeoSeries(ng['geometry'])}, crs="epsg:3857")
                geopdwd_filtered = geopdwd_filtered.drop(columns='geometry')
                geopdwd_filtered = pd.merge(geolistmodified, geopdwd_filtered, on='where')

                kwargs['geopdwd']=geopdwd
                kwargs['geopdwd_filtered']=geopdwd_filtered
            return func(self, **kwargs)
        return innerdecopycoageo

    @importbokeh
    @decopycoageo
    def pycoa_map(self,**kwargs):
        '''
            -----------------
            Create a map bokeh with arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - plot_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - mode = mouse
            - dateslider = None if True
                    - orientation = horizontal
            - when : default min and max according to the inpude DataFrame.
                         Dates are given under the format dd/mm/yyyy.
                         when format [dd/mm/yyyy : dd/mm/yyyy]
                         if [:dd/mm/yyyy] min date up to
                         if [dd/mm/yyyy:] up to max date
            - maplabel: False
        '''
        geopdwd=kwargs.get('geopdwd')
        geopdwd_filtered=kwargs.get('geopdwd_filtered')
        sourcemaplabel=kwargs.get('sourcemaplabel')
        standardfig=kwargs.get('standardfig')
        dateslider = kwargs.get('dateslider',list(InputOption().d_graphicsinput_args['dateslider'])[0])
        maplabel = kwargs.get('maplabel',list(InputOption().d_graphicsinput_args['maplabel'])[0])
        min_col, max_col, min_col_non0 = 3*[0.]
        try:
            if dateslider:
                min_col, max_col = bokeh_visu().min_max_range(np.nanmin(geopdwd['cases']),
                                                         np.nanmax(geopdwd['cases']))
                min_col_non0 = (np.nanmin(geopdwd.loc[geopdwd['cases']>0.]['cases']))
            else:
                min_col, max_col = bokeh_visu().min_max_range(np.nanmin(geopdwd_filtered['cases']),
                                                         np.nanmax(geopdwd_filtered['cases']))
                min_col_non0 = (np.nanmin(geopdwd_filtered.loc[geopdwd_filtered['cases']>0.]['cases']))
        except ValueError:  #raised if `geopdwd_filtered` is empty.
            pass
        #min_col, max_col = np.nanmin(geopdwd_filtered['cases']),np.nanmax(geopdwd_filtered['cases'])
        GeoJSONDataSource = kwargs['GeoJSONDataSource']
        json_data = json.dumps(json.loads(geopdwd_filtered.to_json()))
        geopdwd_filtered = GeoJSONDataSource(geojson=json_data)


        LinearColorMapper = kwargs.get('LinearColorMapper')
        ColorBar = kwargs.get('ColorBar')
        Viridis256 = kwargs.get('Viridis256')
        BasicTicker = kwargs.get('BasicTicker')
        BasicTickFormatter = kwargs.get('BasicTickFormatter')
        invViridis256 = Viridis256[::-1]
        if maplabel and 'log' in maplabel:
            color_mapper = LogColorMapper(palette=invViridis256, low=min_col_non0, high=max_col, nan_color='#ffffff')
        else:
            color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#ffffff')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4, bar_line_cap='round',
                             border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))

        if maplabel and 'label%' in maplabel:
            color_bar.formatter = BasicTickFormatter(use_scientific=False)
            color_bar.formatter = NumeralTickFormatter(format="0.0%")

        self.standardfig().add_layout(color_bar, 'below')
        self.standardfig().add_layout(Title(text=self.subtitle, text_font_size="8pt", text_font_style="italic"), 'below')
        if dateslider:
            allcases_location, allcases_dates = pd.DataFrame(), pd.DataFrame()
            allcases_location = geopdwd.groupby('where')['cases'].apply(list)
            geopdwd_tmp = geopdwd.drop_duplicates(subset = ['where']).drop(columns = 'cases')
            geopdwd_tmp = pd.merge(geopdwd_tmp, allcases_location, on = 'where')
            geopdwd_tmp  = geopdwd_tmp.drop_duplicates(subset = ['clustername'])
            geopdwd_tmp = ColumnDataSource(geopdwd_tmp.drop(columns=['geometry']))

            sourcemaplabel.data['rolloverdisplay'] = sourcemaplabel.data['clustername']

            callback = CustomJS(args =  dict(source = geopdwd_tmp, source_filter = geopdwd_filtered,
                                          datesliderjs = dateslider, title=standardfig.title,
                                          color_mapperjs = color_mapper, maplabeljs = sourcemaplabel),
                        code = """
                        var ind_date_max = (datesliderjs.end-datesliderjs.start)/(24*3600*1000);
                        var ind_date = (datesliderjs.value-datesliderjs.start)/(24*3600*1000);
                        var new_cases = [];
                        var dict = {};
                        var iloop = source_filter.data['clustername'].length;

                        function form(value) {
                             if(value>10000 || value <0.01)
                                value =  Number.parseFloat(value).toExponential(2);
                             else
                                 value = Number.parseFloat(value).toFixed(2);
                            return value;
                         }
                        for (var i = 0; i < source.get_length(); i++)
                        {
                                var val=form(source.data['cases'][i][ind_date_max-ind_date]);
                                new_cases.push(val);
                        }
                        if(source.get_length() == 1 && iloop>1)
                            for(var i = 0; i < iloop; i++)
                                for(var j = 0; j < new_cases.length; j++){
                                source_filter.data['cases'][i][j] = new_cases[j];
                                }
                        else{
                            source_filter.data['cases'] = new_cases;
                            }

                        if (maplabeljs.get_length() !== 0){
                            maplabeljs.data['cases'] = source_filter.data['cases'];
                            }
                        for (var i = 0; i < maplabeljs.get_length(); i++)
                        {
                            maplabeljs.data['cases'][i] = form(maplabeljs.data['cases'][i]).toString();
                            maplabeljs.data['rolloverdisplay'][i] = source_filter.data['rolloverdisplay'][i];
                        }

                        var tmp = title.text;
                        tmp = tmp.slice(0, -11);
                        var dateconverted = new Date(datesliderjs.value);
                        var dd = String(dateconverted.getDate()).padStart(2, '0');
                        var mm = String(dateconverted.getMonth() + 1).padStart(2, '0'); //January is 0!
                        var yyyy = dateconverted.getFullYear();
                        var dmy = dd + '/' + mm + '/' + yyyy;
                        title.text = tmp + dmy+")";

                        if (maplabeljs.get_length() !== 0)
                            maplabeljs.change.emit();

                        color_mapperjs.high=Math.max.apply(Math, new_cases);
                        color_mapperjs.low=Math.min.apply(Math, new_cases);
                        console.log(maplabeljs.data['cases']);
                        source_filter.change.emit();
                    """)
            dateslider.js_on_change('value', callback)
            # Set up Play/Pause button/toggle JS
            date_list = pd.date_range(geopdwd.date.min(),geopdwd.date.max()-dt.timedelta(days=1),freq='d').to_list()
            indexCDS = ColumnDataSource(dict(date=date_list))
            toggl_js = CustomJS(args=dict(dateslider=dateslider,indexCDS=indexCDS),code="""
            // A little lengthy but it works for me, for this problem, in this version.
                var check_and_iterate = function(date){
                    var slider_val = dateslider.value;
                    var toggle_val = cb_obj.active;
                    if(toggle_val == false) {
                        cb_obj.label = '► Play';
                        clearInterval(looop);
                        }
                    else if(slider_val == date[date.length - 1]) {
                        cb_obj.label = '► Play';
                        //dateslider.value = date[0];
                        cb_obj.active = false;
                        clearInterval(looop);
                        }
                    else if(slider_val !== date[date.length - 1]){
                        dateslider.value = date.filter((item) => item > slider_val)[0];
                        }
                    else {
                    clearInterval(looop);
                        }
                }
                if(cb_obj.active == false){
                    cb_obj.label = '► Play';
                    clearInterval(looop);
                }
                else {
                    cb_obj.label = '❚❚ Pause';
                    var looop = setInterval(check_and_iterate, 10, indexCDS.data['date']);
                };
            """)

            toggl = Toggle(label='► Play',active=False, button_type="success",height=30,width=10)
            toggl.js_on_change('active',toggl_js)


        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.patches('xs', 'ys', source = geopdwd_filtered,
                            fill_color = {'field': 'cases', 'transform': color_mapper},
                            line_color = 'black', line_width = 0.25, fill_alpha = 1)
        if maplabel:
            if 'text' in maplabel or 'textinteger' in maplabel:

                if 'textinteger' in maplabel:
                    sourcemaplabel.data['cases'] = sourcemaplabel.data['cases'].astype(float).astype(int).astype(str)
                labels = LabelSet(
                    x = 'centroidx',
                    y = 'centroidy',
                    text = 'cases',
                    source = sourcemaplabel, text_font_size='10px',text_color='white',background_fill_color='grey',background_fill_alpha=0.5)
                standardfig.add_layout(labels)

        #cases_custom = AllVisu.rollerJS()
        callback = CustomJS(code="""
        //document.getElementsByClassName('bk-tooltip')[0].style.backgroundColor="transparent";
        document.getElementsByClassName('bk-tooltip')[0].style.opacity="0.7";
        """ )
        tooltips = """
                    <b>location: @rolloverdisplay<br>
                    cases: @cases{0,0.0} </b>
                    """

        standardfig.add_tools(HoverTool(tooltips = tooltips,
        formatters = {'where': 'printf', 'cases': 'printf',},
        point_policy = "snap_to_data",callback=callback))  # ,PanTool())
        if dateslider:
            standardfig = column(dateslider, standardfig,toggl)
        self.pycoa_geopandas = False
        return standardfig
