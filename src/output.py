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
    kwargs_keystesting,
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
from src.matplotlib_visu import matplotlib_visu
from src.seaborn_visu import seaborn_visu
from src.bokeh_visu import bokeh_visu


__all__ = ['InputOption']

class InputOption():
    """
        Option visualisation !
    """
    def __init__(self):
        self.ax_type = ['linear', 'log']

        self.d_batchinput_args  = {
                                'where':[''],\
                                'option':['nonneg','smooth7','sumall',
                                'bypop=0','bypop=100', 'bypop=1k', 'bypop=100k','bypop=1M'],\
                                'which':[''],\
                                'what':['current','daily','weekly'],\
                                'when':[''],\
                                'input':[pd.DataFrame()],\
                                'output':['pandas','geopandas','list','dict','array']
                              }
        self.listchartkargskeys = list(self.d_batchinput_args.keys())
        self.listchartkargsvalues = list(self.d_batchinput_args.values())

        self.d_graphicsinput_args = {
                                 'title':'',\
                                 'copyright': 'pyvoa',\
                                 'mode':['mouse','vline','hline'],\
                                 'typeofhist':['bylocation','byvalue','pie'],\
                                 'typeofplot':['date','menulocation','versus','spiral','yearly'],\
                                 'bins':10,\
                                 'vis':['matplotlib','bokeh','folium','seaborn'],\
                                 'tile' : ['openstreet','esri','stamen','positron'],\
                                 'orientation':['horizontal','vertical'],\
                                 'dateslider':[False,True],\
                                 'mapoption':['text','textinteger','spark','label%','log','unsorted','dense'],\
                                 'guideline':[False,True],\
                              }
        self.listviskargskeys = list(self.d_graphicsinput_args.keys())
        self.dicokfront = {}


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
        kwargs_keystesting(kw, list(self.d_graphicsinput_args.keys())+list(self.d_graphicsinput_args.keys()), 'Error with this resquest (not available in setoptvis)')
        self.dicokfront = kw

    def getkwargsfront(self):
        return self.dicokfront

Max_Countries_Default  = 12
class AllVisu:
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
        self.when_beg, self.when_end = dt.date(1, 1, 1), dt.date(1, 1, 1)

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

    ''' DECORATORS FOR PLOT: DATE, VERSUS, SCROLLINGMENU '''
    def decoplot(func):
        """
        decorator for plot purpose
        """
        @wraps(func)
        def inner_plot(self ,**kwargs):
            input = kwargs.get('input')
            locunique = list(input['where'].unique())[:Max_Countries_Default]
            input = input.loc[input['where'].isin(locunique)]
            kwargs['input'] = input
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
            which = kwargs.get('which')

            return func(self, **kwargs)
        return inner_hm
    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE '''
    def decohistopie(func):
        @wraps(func)
        def inner_decohistopie(self, **kwargs):
            """
            Decorator for Horizontal histogram & Pie Chart
            It put in the kwargs:
            kwargs['geopdwd']-> pandas for which asked (all dates)
            kwargs['geopdwd_filtered']-> pandas for which asked last dates
            """
            input = kwargs.get('input')
            which = kwargs.get('which')
            locunique = input['where'].unique()

            input_first = input.loc[input['where'].isin(locunique[:Max_Countries_Default-1])]
            input_others = input.loc[input['where'].isin(locunique[Max_Countries_Default-1:])]

            input_others[which] = input_others[which].sum()
            input_others['where'] = 'Others'
            input_others['code'] = 'Others'
            input_others['colors'] = '#FFFFFF'
            input_others = input_others.drop_duplicates(['where','code'])
            input = pd.concat([input_first,input_others])
            input = input.sort_values(by=which, ascending=False).reset_index(drop=True)
            kwargs['input'] = input
            return func(self,**kwargs)
        return inner_decohistopie

    @decoplot
    def plot(self,**kwargs):
        typeofplot = kwargs.get('typeofplot')
        vis = kwargs.get('vis')
        if typeofplot == 'yearly' and len(kwargs['input']['where'].unique())>1:
            CoaWarning('Yearly plot can display only one country,\
                    take the most import one')
            first=kwargs['input'].where.unique()[0]
            kwargs['input'] =  kwargs['input'].loc[kwargs['input'].where.isin([first])]

        if typeofplot == 'versus':
            if len(kwargs.get('which')) != 2:
                raise CoaError("Can't make versus plot in this condition len("+str(kwargs.get('which'))+")!=2")

        if vis == 'matplotlib':
            if typeofplot == 'date':
                fig = matplotlib_visu().matplotlib_date_plot(**kwargs)
            elif typeofplot == 'versus':
                fig = matplotlib_visu().matplotlib_versus_plot(**kwargs)
            elif typeofplot == 'yearly':
                fig = matplotlib_visu().matplotlib_yearly_plot(**kwargs)
            else:
                raise CoaError('For display: '+ vis +' unknown type of plot '+typeofplot)
        elif vis =='seaborn':
            if typeofplot == 'date':
                fig = seaborn_visu().seaborn_date_plot(**kwargs)
            elif  typeofplot == 'versus':
                fig = seaborn_visu().seaborn_versus_plot(**kwargs)
            else:
                CoaError(typeofplot + ' not implemented in ' + vis)
        elif vis == 'bokeh':
            if typeofplot == 'date':
                fig = bokeh_visu().bokeh_date_plot(**kwargs)
            elif typeofplot == 'spiral':
                fig = bokeh_visu().bokeh_spiral_plot(**kwargs)
            elif typeofplot == 'versus':
                if isinstance(which,list) and len(which) == 2:
                    fig = bokeh_visu().bokeh_plot(**kwargs)
                else:
                    print('typeofplot is versus but dim(which)!=2, versus has not effect ...')
                    fig = bokeh_visu().bokeh_date_plot(**kwargs)
            elif typeofplot == 'menulocation':
                if _db_list_dict[self.db][1] == 'nation' and _db_list_dict[self.db][2] != 'World':
                    print('typeofplot is menulocation with a national DB granularity, use date plot instead ...')
                    fig = bokeh_visu().plot(*kwargs)
                else:
                    if isinstance(which,list) and len(which) > 1:
                        CoaWarning('typeofplot is menulocation but dim(which)>1, take first one '+which[0])
                    fig = bokeh_visu().bokeh_menu_plot(**kwargs)
            elif typeofplot == 'yearly':
                if input.date.max()-input.date.min() <= dt.timedelta(days=365):
                    print("Yearly will not be used since the time covered is less than 1 year")
                    fig = matplotlib_visu().bokeh_date_plot(**kwargs)
                else:
                    fig = matplotlib_visu().bokeh_yearly_plot(**kwargs)
        else:
            print(" Not implemented yet ")
        return fig

    @decohistomap
    @decohistopie
    def hist(self,**kwargs):
        '''
        FILL IT
        '''
        typeofhist = kwargs.get('typeofhist')
        vis = kwargs.get('vis')

        if vis == 'matplotlib':
            if typeofhist == 'bylocation':
                fig = matplotlib_visu().matplotlib_horizontal_histo(**kwargs)
            elif typeofhist == 'byvalue':
                fig = matplotlib_visu().matplotlib_histo(**kwargs)
            elif typeofhist == 'pie':
                fig = matplotlib_visu().matplotlib_pie(**kwargs)
            else:
                raise CoaError(typeofhist + ' not implemented in ' + vis)
        elif vis == 'bokeh':
            if typeofhist == 'bylocation':
                if 'bins' in kwargs:
                    raise CoaError("The bins keyword cannot be set with histograms by location. See help.")
                fig = bokeh_visu().bokeh_horizonhisto(**kwargs)
            elif typeofhist == 'byvalue':
                fig = bokeh_visu().bokeh_histo( **kwargs)
            elif typeofhist == 'pie':
                fig = bokeh_visu().bokeh_pie(**kwargs)
        elif vis == 'seaborn':
            if typeofhist == 'bylocation':
                fig = seaborn_visu().seaborn_hist_horizontal(**kwargs)
            elif typeofhist == 'pie':
                fig = seaborn_visu().seaborn_pie(**kwargs)
            elif typeofhist == 'byvalue':
                fig = seaborn_visu().seaborn_hist_value( **kwargs)
            else:
                print(typeofhist + ' not implemented in ' + vis)
        else:
            print( "\n not yet implemented \n")
        return fig

    @decohistomap
    def map(self,**kwargs):
        '''
        FILL IT
        '''
        vis = kwargs.get('vis')
        mapoption = kwargs.get('mapoption')
        input = kwargs.get('input')
        if vis == 'matplotlib':
            return matplotlib_visu().matplotlib_map(**kwargs)
        elif vis == 'seaborn':
            return seaborn_visu().seaborn_heatmap(**kwargs)
        elif vis == 'bokeh':
            if mapoption:
                if 'spark' in mapoption or 'spiral' in mapoption:
                    fig = bokeh_visu().pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in mapoption:
                    fig = bokeh_visu().bokeh_map(**kwargs)
                else:
                    CoaError("What kind of pimp map you want ?!")
            else:
                fig = bokeh_visu().bokeh_map(**kwargs)
            return fig
        elif vis == 'folium':
            return matplotlib_visu().bokeh_mapfolium(**kwargs)
        else:
            raise CoaError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'matplotlib\' \
            aka matplotlib .See help.')
