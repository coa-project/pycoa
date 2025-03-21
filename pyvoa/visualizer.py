# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visualizer

About :
-------

An interface module to easily plot pycoa_data with bokeh

"""
from functools import wraps
import datetime as dt
from pyvoa.tools import (
    kwargs_keystesting,
    extract_dates,
    verb,
    fill_missing_dates
)
import geopandas as gpd
import pandas as pd
from pyvoa.jsondb_parser import MetaInfo
from pyvoa.visu_matplotlib import visu_matplotlib
from pyvoa.visu_seaborn import visu_seaborn
from pyvoa.visu_bokeh import visu_bokeh
from pyvoa.kwarg_options import InputOption

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
            if len(kwargs['which'])>1:
                PyvoaInfo("Only one variable could be displayed, take the first one ...")
            kwargs['which'] = kwargs.get('which')[0]
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
            input_others['where'] = 'SumOthers'
            input_others['code'] = 'SumOthers'
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
            PyvoaWarning('Yearly plot can display only one country,\
                    take the most import one')
            first=kwargs['input'].where.unique()[0]
            kwargs['input'] =  kwargs['input'].loc[kwargs['input'].where.isin([first])]

        if typeofplot == 'versus':
            if len(kwargs.get('which')) != 2:
                raise PyvoaError("Can't make versus plot in this condition len("+str(kwargs.get('which'))+")!=2")

        if vis == 'matplotlib':
            if typeofplot == 'date':
                fig = visu_matplotlib().matplotlib_date_plot(**kwargs)
            elif typeofplot == 'versus':
                fig = visu_matplotlib().matplotlib_versus_plot(**kwargs)
            elif typeofplot == 'yearly':
                fig = visu_matplotlib().matplotlib_yearly_plot(**kwargs)
            else:
                raise PyvoaError('For display: '+ vis +' unknown type of plot '+typeofplot)
        elif vis =='seaborn':
            if typeofplot == 'date':
                fig = visu_seaborn().seaborn_date_plot(**kwargs)
            elif  typeofplot == 'versus':
                fig = visu_seaborn().seaborn_versus_plot(**kwargs)
            else:
                PyvoaError(typeofplot + ' not implemented in ' + vis)
        elif vis == 'bokeh':
            if typeofplot == 'date':
                fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_date_plot(**kwargs)
            elif typeofplot == 'spiral':
                fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_spiral_plot(**kwargs)
            elif typeofplot == 'versus':
                if isinstance(which,list) and len(which) == 2:
                    fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_plot(**kwargs)
                else:
                    print('typeofplot is versus but dim(which)!=2, versus has not effect ...')
                    fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_date_plot(**kwargs)
            elif typeofplot == 'menulocation':
                if self.granularity == 'nation' and self.granularity != 'World':
                    print('typeofplot is menulocation with a national DB granularity, use date plot instead ...')
                    fig = visu_bokeh(InputOption().d_graphicsinput_args).plot(*kwargs)
                else:
                    if len(kwargs['which']) > 1:
                        PyvoaWarning('typeofplot is menulocation but dim(which)>1, take first one '+kwargs['which'][0])
                    fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_menu_plot(**kwargs)
            elif typeofplot == 'yearly':
                if input.date.max()-input.date.min() <= dt.timedelta(days=365):
                    print("Yearly will not be used since the time covered is less than 1 year")
                    fig = visu_matplotlib().bokeh_date_plot(**kwargs)
                else:
                    fig = visu_matplotlib().bokeh_yearly_plot(**kwargs)
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
                fig = visu_matplotlib().matplotlib_horizontal_histo(**kwargs)
            elif typeofhist == 'byvalue':
                fig = visu_matplotlib().matplotlib_histo(**kwargs)
            elif typeofhist == 'pie':
                fig = visu_matplotlib().matplotlib_pie(**kwargs)
            else:
                raise PyvoaError(typeofhist + ' not implemented in ' + vis)
        elif vis == 'bokeh':
            if typeofhist == 'bylocation':
                fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_horizonhisto(**kwargs)
            elif typeofhist == 'byvalue':
                fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_histo( **kwargs)
            elif typeofhist == 'pie':
                fig = visu_bokeh(InputOption().d_graphicsinput_args).bokeh_pie(**kwargs)
        elif vis == 'seaborn':
            if typeofhist == 'bylocation':
                fig = visu_seaborn().seaborn_hist_horizontal(**kwargs)
            elif typeofhist == 'pie':
                fig = visu_seaborn().seaborn_pie(**kwargs)
            elif typeofhist == 'byvalue':
                fig = visu_seaborn().seaborn_hist_value( **kwargs)
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
            fig = visu_matplotlib().matplotlib_map(**kwargs)
        elif vis == 'seaborn':
            fig = visu_seaborn().seaborn_heatmap(**kwargs)
        elif vis == 'bokeh':
            if mapoption:
                if 'spark' in mapoption or 'spiral' in mapoption:
                    fig = visu_bokeh().pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in mapoption:
                    fig = visu_bokeh().bokeh_map(**kwargs)
                else:
                    PyvoaError("What kind of pimp map you want ?!")
            else:
                fig = visu_bokeh().bokeh_map(**kwargs)
        elif vis == 'folium':
            fig = visu_matplotlib().bokeh_mapfolium(**kwargs)
        else:
            raise PyvoaError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'matplotlib\' \
            aka matplotlib .See help.')
        return fig    
