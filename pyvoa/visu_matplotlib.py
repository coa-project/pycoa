# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visu_matplotlib

About :
-------


"""
from pyvoa.tools import (
    extract_dates,
    debug,
    verb,
    fill_missing_dates
)
from pyvoa.error import *
import math
import pandas as pd
import geopandas as gpd
import numpy as np

import json
import io
import copy

import datetime as dt
import matplotlib.dates as mdates
from pyvoa.jsondb_parser import MetaInfo
import matplotlib.pyplot as plt
from IPython.terminal.embed import InteractiveShellEmbed
shell = InteractiveShellEmbed()
shell.enable_gui('tk')
class visu_matplotlib:
    '''
        MATPLOTLIB chart drawing methods ...
    '''
    def __init__(self,):
        import matplotlib
        pass

    def decomatplotlib(func):
        def wrapper(self,**kwargs):

            fig, ax = plt.subplots(1, 1,figsize=(12, 8))
            kwargs['fig'] = fig
            kwargs['ax'] = ax
            kwargs['plt'] = plt
            return func(self,**kwargs)
        return wrapper

    @decomatplotlib
    def matplotlib_date_plot(self,**kwargs):
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')

        plt = kwargs['plt']
        ax = kwargs['ax']
        plt.xlabel("Date", fontsize=10)
        plt.ylabel(which, fontsize=10)
        #for val in which:
        df = pd.pivot_table(input,index='date', columns='where', values=which)
        leg=[]
        for col in df.columns:
            lines = plt.plot(df.index, df[col],label=f'{col}')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.legend(title="where", loc="upper left", fontsize=8, title_fontsize=10)
        plt.title(title)
        plt.show()
        return plt

    @decomatplotlib
    def matplotlib_versus_plot(self,**kwargs):
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']

        loc = list(input['where'].unique())
        plt.xlabel(which[0], fontsize=10)
        plt.ylabel(which[1], fontsize=10)
        leg=[]
        for col in loc:
            pandy=input.loc[input['where']==col]
            lines=plt.plot(pandy[which[0]], pandy[which[1]])
            leg.append(col)
        plt.legend(leg)
        plt.title(title)
        plt.show()
        return plt

    @decomatplotlib
    def matplotlib_yearly_plot(self,**kwargs):
        '''
         matplotlib date yearly plot chart
         Max display defined by Max_Countries_Default
        '''
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)

        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)

        loc = input['where'][0]
        d = input.allyears.unique()
        for i in d:
            df = pd.pivot_table(input.loc[input.allyears==i],index='dayofyear', columns='where', values=which)
            ax = plt.plot(df.index,df,label=f'{i}')
        plt.legend(d)
        plt.title(title)
        plt.show()
        return plt

    @decomatplotlib
    def matplotlib_pie(self,**kwargs):
        '''
         matplotlib pie chart
         Max display defined by Max_Countries_Default
        '''
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')

        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        input = input.set_index('where')
        ax = input.plot(kind="pie",y=which, autopct='%1.1f%%', legend=True,
        title=title, ylabel='where', labeldistance=None)
        ax.legend(bbox_to_anchor=(0.75, 1.2), loc='upper left')
        ax.set_title(title)
        plt.show()
        return plt

    @decomatplotlib
    def matplotlib_horizontal_histo(self,**kwargs):
        '''
        matplotlib horizon histo
        '''
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        cmap = plt.get_cmap('Paired')
        ax = kwargs.get('ax')
        fig = kwargs.get('fig')
        bar = ax.barh(input['where'], input[which],color=cmap.colors)
        ax.set_title(title)
        plt.show()
        return plt

    @decomatplotlib
    def matplotlib_histo(self,**kwargs):
        '''
        matplotlib vertical histo
        '''
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        bins=len(input['where'])+1
        input= pd.pivot_table(input,index='date', columns='where', values=which)
        ax = input.plot.hist(bins=bins, alpha=0.5,title = title)
        plt.show()
        return plt

    @decomatplotlib
    def matplotlib_map(self,**kwargs):
        '''
         matplotlib map display
        '''
        from matplotlib.colors import Normalize
        from matplotlib import cm
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        import contextily as cx
        import xyzservices
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        plt.axis('off')
        input = kwargs.get('input')
        which = kwargs.get('which')
        mapoption = kwargs.get('mapoption')
        title = kwargs.get('title')
        tile = kwargs.get('tile')

        input.plot(column = which, ax=ax,legend=True,
                                legend_kwds={'label': which,
                                'orientation': "horizontal","pad": 0.001})

        if tile == 'openstreet':
            input = input.to_crs(epsg=3857)
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.OpenStreetMap.Mapnik)
        elif tile == 'esri':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Esri.WorldImagery)
        elif tile == 'stamen':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Esri.WorldImagery)
            PyvoaWarning("Couldn't find stamen for matplolib use esri ....")
            input = input.to_crs(epsg=4326)
        elif tile == 'positron':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.CartoDB.PositronNoLabels)
        else:
            PyvoaError("Don't know what kind of tile is it ...")

        if 'text' in mapoption:
            centroids = input['geometry'].centroid
            for idx, centroid in enumerate(centroids):
                if centroid:
                    x, y = centroid.x, centroid.y
                    annotation = input.iloc[idx][which]
                    annotation =  annotation.round(2)

        ax.set_axis_off()
        ax.set_title(title)
        plt.show()
        return plt
