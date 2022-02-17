# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - march 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.display

About :
-------

An interface module to easily plot pycoa data with bokeh

"""

from coa.tools import kwargs_test, extract_dates, verb, get_db_list_dict
from coa.error import *

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
from IPython import display
import copy
import locale

from bokeh.models import ColumnDataSource, TableColumn, DataTable, ColorBar, LogTicker,\
    HoverTool, CrosshairTool, BasicTicker, GeoJSONDataSource, LinearColorMapper, LogColorMapper,Label, \
    PrintfTickFormatter, BasicTickFormatter, NumeralTickFormatter, CustomJS, CustomJSHover, Select, \
    Range1d, DatetimeTickFormatter, Legend, LegendItem, Text
from bokeh.models.widgets import Tabs, Panel
from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Category10, Category20, Viridis256
from bokeh.models import Title

from bokeh.io import export_png
from bokeh import events
from bokeh.models.widgets import DateSlider
from bokeh.models import LabelSet, WMTSTileSource
from bokeh.transform import transform, cumsum

import shapely.geometry as sg

import branca.colormap
from branca.colormap import LinearColormap
from branca.element import Element, Figure
import folium
from PIL import Image
import coa.geo as coge
import matplotlib.pyplot as plt
import datetime as dt
import bisect
from functools import wraps
from IPython.core.display import display, HTML

width_height_default = [500, 380]

MAXCOUNTRIESDISPLAYED = 27
class CocoDisplay:
    def __init__(self, db=None, geo = None):
        verb("Init of CocoDisplay() with db=" + str(db))
        self.database_name = db
        self.dbld = get_db_list_dict()
        self.lcolors = Category20[20]
        self.scolors = Category10[5]
        self.ax_type = ['linear', 'log']
        self.geom = []
        self.geopan = gpd.GeoDataFrame()
        self.location_geometry = None
        self.boundary_metropole = None
        self.listfigs = []
        self.options_stats  = ['when','input','input_field']
        self.options_charts = [ 'bins']
        self.options_front = ['where','option','which','what','visu']
        self.available_tiles = ['openstreet','esri','stamen']
        self.available_modes = ['mouse','vline','hline']
        self.uptitle, self.subtitle = ' ',' '

        self.dfigure_default = {'plot_height':width_height_default[1] ,'plot_width':width_height_default[0],'title':None,'textcopyright':'default'}
        self.dvisu_default = {'mode':'mouse','tile':self.available_tiles[0],'orientation':'horizontal','cursor_date':None,'maplabel':None,'guideline':False}

        self.when_beg = dt.date(1, 1, 1)
        self.when_end = dt.date(1, 1, 1)

        self.alloptions =  self.options_stats + self.options_charts + self.options_front + list(self.dfigure_default.keys()) + list(self.dvisu_default.keys())

        self.iso3country = self.dbld[self.database_name][0]
        self.granularity = self.dbld[self.database_name][1]
        self.namecountry = self.dbld[self.database_name][2]
        try:
            if self.granularity != 'nation':
                self.geo = coge.GeoCountry(self.iso3country)
                if self.granularity == 'region':
                    self.location_geometry = self.geo.get_region_list()[['code_region', 'name_region', 'geometry']]
                    self.location_geometry = self.location_geometry.rename(columns={'name_region': 'location'})
                    if self.iso3country == 'PRT':
                         tmp=self.location_geometry.rename(columns={'name_region': 'location'})
                         tmp = tmp.loc[tmp.code_region=='PT.99']
                         self.boundary_metropole =tmp['geometry'].total_bounds
                    if self.iso3country == 'FRA':
                         tmp=self.location_geometry.rename(columns={'name_region': 'location'})
                         tmp = tmp.loc[tmp.code_region=='999']
                         self.boundary_metropole =tmp['geometry'].total_bounds
                elif self.granularity == 'subregion':
                    list_dep_metro = None
                    self.location_geometry = self.geo.get_subregion_list()[['code_subregion', 'name_subregion', 'geometry']]
                    self.location_geometry = self.location_geometry.rename(columns={'name_subregion': 'location'})
                    #if country == 'FRA':
                    #     list_dep_metro =  geo.get_subregions_from_region(name='Métropole')
                    #elif country == 'ESP':
                    #     list_dep_metro =  geo.get_subregions_from_region(name='España peninsular')
                    #if list_dep_metro:
                    #    self.boundary_metropole = self.location_geometry.loc[self.location_geometry.code_subregion.isin(list_dep_metro)]['geometry'].total_bounds
            else:
                   self.geo=coge.GeoManager('name')
                   geopan = gpd.GeoDataFrame()#crs="EPSG:4326")
                   info = coge.GeoInfo()
                   allcountries = self.geo.get_GeoRegion().get_countries_from_region('world')
                   geopan['location'] = [self.geo.to_standard(c)[0] for c in allcountries]
                   geopan = info.add_field(field=['geometry'],input=geopan ,geofield='location')
                   geopan = gpd.GeoDataFrame(geopan, geometry=geopan.geometry, crs="EPSG:4326")
                   geopan = geopan[geopan.location != 'Antarctica']
                   geopan = geopan.dropna().reset_index(drop=True)
                   self.location_geometry  = geopan
        except:
            raise CoaTypeError('What data base are you looking for ?')

    ''' FIGURE COMMUN FOR ALL '''
    def standardfig(self, **kwargs):
        """
         Create a standard Bokeh figure, with pycoa.fr copyright, used in all the bokeh charts
         """
        plot_width = kwargs.get('plot_width', self.dfigure_default['plot_width'])
        plot_height = kwargs.get('plot_height', self.dfigure_default['plot_height'])
        textcopyright = kwargs.get('textcopyright', self.dfigure_default['textcopyright'])

        if textcopyright  == 'default':
                textcopyright = '©pycoa.fr (data from: {})'.format(self.database_name)
        else:
                textcopyright = '©pycoa.fr ' + textcopyright

        citation = Label(x=0.65 * plot_width - len(textcopyright), y=0.01 * plot_height,
                                          x_units='screen', y_units='screen',
                                          text_font_size='1.5vh', background_fill_color='white', background_fill_alpha=.75,
                                          text=textcopyright)

        for i in list(self.dvisu_default.keys())  + self.options_front + self.options_charts + ['textcopyright'] + self.options_stats + ['date_slider']:
            if i in kwargs.keys():
                kwargs.pop(i)
        kwargs.pop('title')
        fig = figure(**kwargs, tools=['save', 'box_zoom,reset'], toolbar_location="right")
        #fig.add_layout(citation)
        fig.add_layout(Title(text=self.uptitle, text_font_size="10pt"), 'above')
        fig.add_layout(Title(text=self.subtitle, text_font_size="8pt", text_font_style="italic"), 'below')
        return fig

    def get_listfigures(self):
        return  self.listfigs
    def set_listfigures(self,fig):
            if not isinstance(fig,list):
                fig = [fig]
            self.listfigs = fig
    ''' WRAPPER COMMUN FOR ALL'''
    def decowrapper(func):
        '''
            Main decorator it mainly deals with arg testings
        '''
        @wraps(func)
        def wrapper(self, input = None, input_field = None, **kwargs):
            """
            Parse a standard input, return :
                - pandas: with location keyword (eventually force a column named 'where' to 'location')
                - kwargs:
                    * keys = [plot_width, plot_width, title, when, title_temporal,bins, what, which]
            Note that method used only the needed variables, some of them are useless
            """
            if not isinstance(input, pd.DataFrame):
                raise CoaTypeError(input + 'Must be a pandas, with pycoa structure !')

            kwargs_test(kwargs, self.alloptions, 'Bad args used in the display function.')
            when = kwargs.get('when', None)
            which = kwargs.get('which', input.columns[2])
            if input_field and 'cur_' in input_field:
                what =  which
            else:
                 # cumul is the default
                what = kwargs.get('what', which)

            if input_field is None:
                input_field = which

            if isinstance(input_field,list):
                test = input_field[0]
            else:
                test = input_field
            if input[[test,'date']].isnull().values.all():
                raise CoaKeyError('All values for '+ which + ' is nan nor empty')

            option = kwargs.get('option', None)
            bins = kwargs.get('bins', 10)
            title = kwargs.get('title', None)
            #textcopyright = kwargs.get('textcopyright', 'default')
            kwargs['plot_width'] = kwargs.get('plot_width', self.dfigure_default['plot_width'])
            kwargs['plot_height'] = kwargs.get('plot_height', self.dfigure_default['plot_height'])

            if 'where' in input.columns:
                input = input.rename(columns={'where': 'location'})

            if 'codelocation' and 'clustername' not in input.columns:
                input['codelocation'] = input['location']
                input['clustername'] = input['location']
                input['rolloverdisplay'] = input['location']
                input['permanentdisplay'] = input['location']
            else:
                if self.granularity == 'nation' :
                    #input['codelocation'] = input['codelocation'].apply(lambda x: str(x).replace('[', '').replace(']', '') if len(x)< 10 else x[0]+'...'+x[-1] )
                    input['permanentdisplay'] = input.apply(lambda x: x.clustername if self.geo.get_GeoRegion().is_region(x.clustername) else str(x.codelocation), axis = 1)
                else:
                    if self.granularity == 'subregion' :
                        input = input.reset_index(drop=True)
                        if isinstance(input['codelocation'][0],list):
                            input['codelocation'] = input['codelocation'].apply(lambda x: str(x).replace("'", '')\
                                                         if len(x)<5 else '['+str(x[0]).replace("'", '')+',...,'+str(x[-1]).replace("'", '')+']')

                        trad={}
                        cluster = input.clustername.unique()
                        if isinstance(input.location[0],list):
                           cluster = [i for i in cluster]
                        for i in cluster:
                            if i == self.namecountry:
                                input['permanentdisplay'] = input.clustername #[self.dbld[self.database_name][2]]*len(input)
                            else:
                                if self.geo.is_region(i):
                                    trad[i] = self.geo.is_region(i)
                                elif self.geo.is_subregion(i):
                                    trad[i] = self.geo.is_subregion(i)#input.loc[input.clustername==i]['codelocation'].iloc[0]
                                else:
                                    trad[i] = i
                                trad={k:(v[:3]+'...'+v[-3:] if len(v)>8 else v) for k,v in trad.items()}
                                if ',' in input.codelocation[0]:
                                    input['permanentdisplay'] = input.clustername
                                else:
                                    input['permanentdisplay'] = input.codelocation#input.clustername.map(trad)
                    elif self.granularity == 'region' :
                        if all(i == self.namecountry for i in input.clustername.unique()):
                            input['permanentdisplay'] = [self.namecountry]*len(input)
                        else:
                            input['permanentdisplay'] = input.codelocation
                input['rolloverdisplay'] = input['location']

            maplabel = kwargs.get('maplabel', None)
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
                input.loc[:,'colors'] = input['clustername'].map(dico_colors)#(pd.merge(input, country_col, on='location'))

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

            for i in input_field:
                if input[i].isnull().all():
                    raise CoaTypeError("Sorry all data are NaN for " + i)
                else:
                    when_end_change = min(when_end_change,CocoDisplay.changeto_nonull_date(input, when_end, i))

            if func.__name__ not in ['pycoa_date_plot', 'pycoa_plot', 'pycoa_scrollingmenu', 'pycoa_spiral_plot','pycoa_yearly_plot']:
                if len(input_field) > 1:
                    print(str(input_field) + ' is dim = ' + str(len(input_field)) + '. No effect with ' + func.__name__ + '! Take the first input: ' + input_field[0])
                input_field = input_field[0]

            if when_end_change != when_end:
                when_end = when_end_change

            self.when_beg = when_beg
            self.when_end = when_end
            input = input.loc[(input['date'] >=  self.when_beg) & (input['date'] <=  self.when_end)]

            title_temporal = ' (' + 'between ' + when_beg.strftime('%d/%m/%Y') + ' and ' + when_end.strftime('%d/%m/%Y') + ')'
            if func.__name__ != 'pycoa_date_plot' and func.__name__ != 'pycoa_yearly_plot'  and func.__name__ != 'pycoa_plot':
                title_temporal = ' (' + when_end.strftime('%d/%m/%Y')  + ')'
            title_option=''
            if option:
                if 'sumallandsmooth7' in option:
                    option.remove('sumallandsmooth7')
                    option += ['sumall','smooth7']
                title_option = ' (option: ' + str(option)+')'

            input_field_tostring = str(input_field).replace('[', '').replace(']', '').replace('\'', '')
            if input_field_tostring == 'daily':
                titlefig = which + ', ' + 'day to day difference' + title_option
            elif input_field_tostring == 'weekly':
                titlefig = which + ', ' + 'week to week difference' + title_option

            elif input_field_tostring == input.columns[2]:
                if 'cur_' in  which or 'idx_' in  which:
                    #titlefig = which + ', ' + 'current ' + which.replace('cur_','').replace('idx_','')+ title_option
                    titlefig = which + ', ' + 'current value' + title_option
                else:
                    titlefig = which + ', ' + 'cumulative'+ title_option
            else:
                titlefig = input_field_tostring + title_option

            if title:
                title = title
            else:
                title  = titlefig
            self.uptitle = title

            textcopyright = kwargs.get('textcopyright', None)
            if textcopyright:
                textcopyright = '©pycoa.fr ' + textcopyright + title_temporal
                kwargs.pop('textcopyright')
            else:
                textcopyright = '©pycoa.fr data from: {}'.format(self.database_name)+' '+title_temporal

            self.subtitle = textcopyright
            kwargs['title'] = title+title_temporal
            return func(self, input, input_field, **kwargs)
        return wrapper

    @decowrapper
    def pycoa_resume_data(self, input, input_field, **kwargs):
        loc=list(input['clustername'].unique())
        input['cases'] = input[input_field]
        dspiral={i:CocoDisplay.spiral(input.loc[ (input.clustername==i) &
                    (input.date >= self.when_beg) &
                    (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
        input['resume']=input['clustername'].map(dspiral)
        input = input.loc[input.date==input.date.max()].reset_index(drop=True)
        def path_to_image_html(path):
            return '<img src="'+ path + '" width="60" >'

        input=input.drop(columns=['permanentdisplay','rolloverdisplay','colors','cases'])
        input=input.apply(lambda x: x.round(2) if x.name in [input_field,'daily','weekly'] else x)
        if isinstance(input['location'][0], list):
            col=[i for i in list(input.columns) if i not in ['clustername','location','codelocation']]
            col.insert(0,'clustername')
            input = input[col]
            input=input.set_index('clustername')
        else:
           input = input.drop(columns='clustername')
           input=input.set_index('location')

        return input.to_html(escape=False,formatters=dict(resume=path_to_image_html))

    ''' DECORATORS FOR PLOT: DATE, VERSUS, SCROLLINGMENU '''
    def decoplot(func):
        """
        decorator for plot purpose
        """
        @wraps(func)
        def inner_plot(self, input = None, input_field = None, **kwargs):
            mode = kwargs.get('mode', None)
            if mode:
                mode = mode
            else:
                mode = self.dvisu_default['mode']
            if mode not in self.available_modes:
                raise CoaTypeError('Don\'t know the mode wanted. So far:' + str(self.available_modes))
            kwargs['mode'] = mode

            if 'location' in input.columns:
                location_ordered_byvalues = list(
                    input.loc[input.date == self.when_end].sort_values(by=input_field, ascending=False)['clustername'].unique())
                input = input.copy()  # needed to avoid warning
                input.loc[:,'clustername'] = pd.Categorical(input.clustername,
                                                       categories=location_ordered_byvalues, ordered=True)

                input = input.sort_values(by=['clustername', 'date']).reset_index(drop = True)

                if len(location_ordered_byvalues) >= MAXCOUNTRIESDISPLAYED:
                    input = input.loc[input.clustername.isin(location_ordered_byvalues[:MAXCOUNTRIESDISPLAYED])]
                list_max = []
                for i in input_field:
                    list_max.append(max(input.loc[input.clustername.isin(location_ordered_byvalues)][i]))
                if len([x for x in list_max if not np.isnan(x)]) > 0:
                    amplitude = (np.nanmax(list_max) - np.nanmin(list_max))
                    if amplitude > 10 ** 4:
                        self.ax_type.reverse()
                if func.__name__ == 'pycoa_scrollingmenu' :
                    if isinstance(input_field,list):
                        if len(input_field) > 1:
                            print(str(input_field) + ' is dim = ' + str(len(input_field)) + '. No effect with ' + func.__name__ + '! Take the first input: ' + input_field[0])
                        input_field = input_field[0]
                    print(self.dbld[self.database_name][1],self.dbld[self.database_name][0])
                    if self.dbld[self.database_name][1] == 'nation' and self.dbld[self.database_name][0] != 'WW':
                        func.__name__ = 'pycoa_date_plot'
            return func(self, input, input_field, **kwargs)
        return inner_plot

    ''' PLOT VERSUS '''
    @decowrapper
    @decoplot
    def pycoa_plot(self, input = None, input_field = None ,**kwargs):
        '''
        -----------------
        Create a versus plot according to arguments.
        See help(pycoa_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pycoa struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element. It should be a list dim=2. Moreover the 2 variables must be present
        in the DataFrame considered.
        - plot_heigh = width_height_default[1]
        - plot_width = width_height_default[0]
        - title = None
        - textcopyright = default
        - mode = mouse
        - cursor_date = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        if len(input_field) != 2:
            raise CoaTypeError('Two variables are needed to plot a versus chart ... ')
        panels = []
        cases_custom = CocoDisplay.rollerJS()
        if self.get_listfigures():
            self.set_listfigures([])
        listfigs=[]
        for axis_type in self.ax_type:
            standardfig = self.standardfig( x_axis_label = input_field[0], y_axis_label = input_field[1],
                                                y_axis_type = axis_type, **kwargs )

            standardfig.add_tools(HoverTool(
                tooltips=[('Location', '@rolloverdisplay'), ('date', '@date{%F}'),
                          (input_field[0], '@{casesx}' + '{custom}'),
                          (input_field[1], '@{casesy}' + '{custom}')],
                formatters={'location': 'printf', '@{casesx}': cases_custom, '@{casesy}': cases_custom,
                            '@date': 'datetime'}, mode = kwargs['mode'],
                point_policy="snap_to_data"))  # ,PanTool())

            for loc in input.clustername.unique():
                pandaloc = input.loc[input.clustername == loc].sort_values(by='date', ascending='True')
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
            CocoDisplay.bokeh_legend(standardfig)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' DATE PLOT '''
    @decowrapper
    @decoplot
    def pycoa_date_plot(self, input = None, input_field = None, **kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(pycoa_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pycoa struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= width_height_default[1]
        - plot_width = width_height_default[0]
        - title = None
        - textcopyright = default
        - mode = mouse
        - guideline = False
        - cursor_date = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        guideline = kwargs.get('guideline',self.dvisu_default['guideline'])
        panels = []
        listfigs = []
        cases_custom = CocoDisplay.rollerJS()
        if isinstance(input['rolloverdisplay'][0],list):
            input['rolloverdisplay'] = input['clustername']
        for axis_type in self.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type, x_axis_type = 'datetime',**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
            smcolors = iter(self.scolors)
            for val in input_field:
                line_style = ['solid', 'dashed', 'dotted', 'dotdash']
                for loc in list(input.clustername.unique()):
                    input_filter = input.loc[input.clustername == loc].reset_index(drop = True)

                    src = ColumnDataSource(input_filter)
                    leg = input_filter.clustername[0]
                    #leg = input_filter.permanentdisplay[0]
                    if len(input_field)>1:
                        leg = input_filter.permanentdisplay[0] + ', ' + val
                    if len(list(input.clustername.unique())) == 1:
                        color = next(smcolors)
                    else:
                        color = input_filter.colors[0]
                    r = standardfig.line(x = 'date', y = val, source = src,
                                     color = color, line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = val, line_dash=line_style[i])
                    r_list.append(r)
                    maxou=max(maxou,np.nanmax(input_filter[val].values))
                i += 1
            for r in r_list:
                label = r.name
                tooltips = [('Location', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')]
                formatters = {'location': 'printf', '@date': 'datetime', '@name': 'printf'}
                hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = kwargs['mode'], renderers=[r])  # ,PanTool())
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
            if len(input_field) > 1 and len(input_field)*len(input.clustername.unique())>9:
                standardfig.legend.visible=False
            standardfig.xaxis.formatter = DatetimeTickFormatter(
                days = ["%d/%m/%y"], months = ["%d/%m/%y"], years = ["%b %Y"])
            CocoDisplay.bokeh_legend(standardfig)
            listfigs.append(standardfig)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' SPIRAL PLOT '''
    @decowrapper
    @decoplot
    def pycoa_spiral_plot(self, input = None, input_field = None, **kwargs):
        guideline = kwargs.get('guideline',self.dvisu_default['guideline'])
        panels = []
        listfigs = []
        cases_custom = CocoDisplay.rollerJS()
        if isinstance(input['rolloverdisplay'][0],list):
            input['rolloverdisplay'] = input['clustername']
        borne=300
        kwargs.pop('plot_width')
        standardfig = self.standardfig(y_axis_type = None, x_axis_type = None,**kwargs
        ,width=kwargs['plot_height'],
        x_range=[-borne, borne], y_range=[-borne, borne],match_aspect=True)

        if len(input.clustername.unique()) > 1 :
            print('Can only display spiral for ONE location. I took the first one:', input.clustername[0])
            input = input.loc[input.clustername == input.clustername[0]].copy()
        input['date']=pd.to_datetime(input["date"])
        input["dayofyear"]=input.date.dt.dayofyear
        input['year']=input.date.dt.year

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

        outer_radius=250
        standardfig.multi_line([x_base,x_cas_sup,x_cas_inf],[y_base,y_cas_sup,y_cas_inf],color=["firebrick", "navy","navy"])
        xcol,ycol=[],[]
        [ xcol.append([i,j]) for i,j in zip(x_cas_inf,x_cas_sup)]
        [ ycol.append([i,j]) for i,j in zip(y_cas_inf,y_cas_sup)]
        standardfig.patches(xcol,ycol,color='blue',fill_alpha = 0.5)

        [standardfig.annular_wedge(
            x=0, y=0, inner_radius=0, outer_radius=outer_radius, start_angle=i*np.pi/6,\
            end_angle=(i+1)*np.pi/6,fill_color=None,line_color='black',line_dash='dotted')
        for i in range(12)]

        label = ['January','February','March','April','May','June','July','August','September','October','November','December']
        xr,yr = polar(np.linspace(0, 2 * np.pi, 13),outer_radius,1)

        standardfig.text(xr[:-1], yr[:-1], label,text_font_size="9pt", text_align="center", text_baseline="middle")
        #standardfig.text(300/np.sqrt(2),300/np.sqrt(2),input.clustername.unique())
        return standardfig

    ''' SCROLLINGMENU PLOT '''
    @decowrapper
    @decoplot
    def pycoa_scrollingmenu(self, input = None, input_field = None, **kwargs):
        '''
        -----------------
        Create a date plot, with a scrolling menu location, according to arguments.
        See help(pycoa_scrollingmenu).
        Keyword arguments
        -----------------
        len(location) > 2
        - input = None : if None take first element. A DataFrame with a Pycoa struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= width_height_default[1]
        - plot_width = width_height_default[0]
        - title = None
        - textcopyright = default
        - mode = mouse
        -guideline = False
        - cursor_date = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        mode = kwargs.get('mode',self.dvisu_default['mode'])
        guideline = kwargs.get('guideline',self.dvisu_default['guideline'])

        uniqloc = input.clustername.unique().to_list()
        if 'location' in input.columns:
            if len(uniqloc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                   'There is no sens to use this method. See help.')
        input = input[['date', 'clustername', input_field]]

        mypivot = pd.pivot_table(input, index='date', columns='clustername', values=input_field)
        source = ColumnDataSource(mypivot)

        filter_data1 = mypivot[[uniqloc[0]]].rename(columns={uniqloc[0]: 'cases'})
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = mypivot[[uniqloc[1]]].rename(columns={uniqloc[1]: 'cases'})
        src2 = ColumnDataSource(filter_data2)

        cases_custom = CocoDisplay.rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'}, mode = mode,
                               point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in self.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type, x_axis_type = 'datetime', **kwargs)

            standardfig.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")

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
    @decowrapper
    @decoplot
    def pycoa_yearly_plot(self, input = None, input_field = None, **kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(pycoa_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pycoa struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= width_height_default[1]
        - plot_width = width_height_default[0]
        - title = None
        - textcopyright = default
        - mode = mouse
        - guideline = False
        - cursor_date = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        guideline = kwargs.get('guideline',self.dvisu_default['guideline'])
        if len(input.clustername.unique()) > 1 :
            print('Can only display yearly plot for ONE location. I took the first one:', input.clustername[0])
        input = input.loc[input.clustername == input.clustername[0]].copy()

        panels = []
        listfigs = []
        cases_custom = CocoDisplay.rollerJS()
        input['date']=pd.to_datetime(input["date"])
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        allyears = list(input.allyears.unique())
        if isinstance(input['rolloverdisplay'][0],list):
            input['rolloverdisplay'] = input['clustername']
        for axis_type in self.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type,**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
            if len(input_field)>1:
                CoaError('Only one variable could be displayed')
            else:
                input_field=input_field[0]
            input['cases']=input[input_field]

            line_style = ['solid', 'dashed', 'dotted', 'dotdash']
            colors = itertools.cycle(self.lcolors)
            for loc in list(input.clustername.unique()):
                for year in allyears:
                    input_filter = input.loc[(input.clustername == loc) & (input['date'].dt.year.eq(year))].reset_index(drop = True)
                    src = ColumnDataSource(input_filter)
                    leg = loc + ' ' + str(year)
                    r = standardfig.line(x = 'dayofyear', y = input_field, source = src,
                                     color = next(colors), line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = input_field)
                    maxou=max(maxou,np.nanmax(input_filter[input_field].values))

            label = input_field
            tooltips = [('Location', '@rolloverdisplay'), ('date', '@date{%F}'), ('Cases', '@cases{0,0.0}')]
            formatters = {'location': 'printf', '@date': 'datetime', '@name': 'printf'}
            hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = kwargs['mode'])  # ,PanTool())
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

            labelspd=input.loc[(input.allyears.eq(2021)) & (input.date.dt.day.eq(1))]
            standardfig.xaxis.ticker = list(labelspd['dayofyear'].astype(int))
            replacelabelspd =  labelspd['date'].apply(lambda x: str(x.strftime("%b")))
            #label_dict = dict(zip(input.loc[input.allyears.eq(2020)]['daymonth'],input.loc[input.allyears.eq(2020)]['date'].apply(lambda x: str(x.day)+'/'+str(x.month))))
            standardfig.xaxis.major_label_overrides = dict(zip(list(labelspd['dayofyear'].astype(int)),list(replacelabelspd)))

            CocoDisplay.bokeh_legend(standardfig)
            listfigs.append(standardfig)

        tooltips = [('Location', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')]
        formatters = {'location': 'printf', '@date': 'datetime', '@name': 'printf'}
        hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = kwargs['mode'], renderers=[r])  # ,PanTool())
        standardfig.add_tools(hover)
        if guideline:
            cross= CrosshairTool()
            standardfig.add_tools(cross)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE & MAP'''
    def decohistomap(func):
        """
        Decorator function used for histogram and map
        """
        @wraps(func)
        def inner_hm(self, input = None, input_field = None, **kwargs):
            tile = kwargs.get('tile', self.dvisu_default['tile'])

            maplabel = kwargs.get('maplabel', None)
            if not isinstance(maplabel,list):
                    maplabel=[maplabel]
            #if maplabel:
            #    maplabel = maplabel

            if 'map' in func.__name__:
                kwargs['maplabel'] = maplabel

            orientation = kwargs.get('orientation', self.dvisu_default['orientation'])
            cursor_date = kwargs.get('cursor_date', None)
            #if orientation:
            #    kwargs['orientation'] = orientation
            #kwargs['cursor_date'] = kwargs.get('cursor_date',  self.dvisu_default['cursor_date'])
            if isinstance(input['location'].iloc[0],list):
                input['rolloverdisplay'] = input['clustername']
                input = input.explode('location')
            else:
                input['rolloverdisplay'] = input['location']

            uniqloc = input.clustername.unique()

            geopdwd = input
            if maplabel and 'unsorted' in maplabel:
                pass
            else:
                geopdwd = geopdwd.sort_values(by=input_field, ascending = False).reset_index(drop=True)

            started = geopdwd.date.min()
            ended = geopdwd.date.max()
            if cursor_date:
                date_slider = DateSlider(title = "Date: ", start = started, end = ended,
                                     value = ended, step=24 * 60 * 60 * 1000, orientation = orientation)
                #wanted_date = date_slider.value_as_datetime.date()

            #if func.__name__ == 'pycoa_mapfolium' or func.__name__ == 'pycoa_map' or func.__name__ == 'innerdecomap' or func.__name__ == 'innerdecopycoageo':
            if func.__name__ in ['pycoa_mapfolium','pycoa_map','pycoageo' ,'pycoa_pimpmap']:
                if isinstance(input.location.to_list()[0],list):
                    geom = self.location_geometry
                    geodic={loc:geom.loc[geom.location==loc]['geometry'].values[0] for loc in geopdwd.location.unique()}
                    geopdwd['geometry'] = geopdwd['location'].map(geodic)
                else:
                    geopdwd = pd.merge(geopdwd, self.location_geometry, on='location')

                kwargs['tile'] = tile
                if self.iso3country in ['USA']:#['FRA','USA']
                    geo = copy.deepcopy(self.geo)
                    d = geo._list_translation
                    if func.__name__ != 'pycoa_mapfolium':
                        if any(i in list(geopdwd.codelocation.unique()) for i in d.keys()) \
                        or any(True for i in d.keys() if ''.join(list(geopdwd.codelocation.unique())).find(i)!=-1):
                            geo.set_dense_geometry()
                            kwargs.pop('tile')
                        else:
                            geo.set_main_geometry()
                            d = {}
                        new_geo = geo.get_data()[['name_'+self.granularity,'geometry']]
                        new_geo = new_geo.rename(columns={'name_'+self.granularity:'location'})
                        new_geo = new_geo.set_index('location')['geometry'].to_dict()

                        geopdwd['geometry'] = geopdwd['location'].map(new_geo)
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
                            new = new.append(perloc)
                        n += 1
                geopdwd = new.reset_index(drop=True)
            if cursor_date:
                date_slider = date_slider
            else:
                date_slider = None
            kwargs['date_slider'] = date_slider
            return func(self, geopdwd, input_field, **kwargs)
        return inner_hm

    ''' VERTICAL HISTO '''
    @decowrapper
    @decohistomap
    def pycoa_histo(self,  geopdwd, input_field = None, **kwargs):
        '''
            -----------------
            Create 1D histogramme by value according to arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - geopdwd : A DataFrame with a Pycoa struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= width_height_default[1]
            - plot_width = width_height_default[0]
            - title = None
            - textcopyright = default
            - when : default min and max according to the inpude DataFrame.
                     Dates are given under the format dd/mm/yyyy.
                     when format [dd/mm/yyyy : dd/mm/yyyy]
                     if [:dd/mm/yyyy] min date up to
                     if [dd/mm/yyyy:] up to max date
        '''
        geopdwd_filter = geopdwd.loc[geopdwd.date == self.when_end]
        geopdwd_filter = geopdwd_filter.reset_index(drop = True)

        input = geopdwd_filter.rename(columns = {'cases': input_field})
        bins = kwargs.get('bins', None)

        if 'location' in input.columns:
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
                contributors[rank].append(allval.iloc[i]['clustername'])

            colors = itertools.cycle(self.lcolors)
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

    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE '''
    def decohistopie(func):
        @wraps(func)
        def inner_decohistopie(self, geopdwd, input_field, **kwargs):
            """
            Decorator for
            Horizontal histogram & Pie Chart
            """
            geopdwd['cases'] = geopdwd[input_field]
            maplabel = kwargs.get('maplabel',None)
            plot_width = kwargs.get('plot_width',self.dfigure_default['plot_width'])
            plot_height = kwargs.get('plot_height',self.dfigure_default['plot_height'])

            geopdwd_filter = geopdwd.loc[geopdwd.date == self.when_end]
            geopdwd_filter = geopdwd_filter.reset_index(drop = True)
            geopdwd_filter['cases'] = geopdwd_filter[input_field]
            cursor_date = kwargs.get('cursor_date',self.dvisu_default['cursor_date'])
            date_slider = kwargs['date_slider']
            my_date = geopdwd.date.unique()
            dico_utc = {i: DateSlider(value=i).value for i in my_date}
            geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
            #geopdwd = geopdwd.drop_duplicates(["date", "codelocation","clustername"])#for sumall avoid duplicate
            #geopdwd_filter = geopdwd_filter.drop_duplicates(["date", "codelocation","clustername"])
            geopdwd = geopdwd.drop_duplicates(["date","clustername"])#for sumall avoid duplicate
            geopdwd_filter = geopdwd_filter.drop_duplicates(["date","clustername"])
            locunique = geopdwd_filter.clustername.unique()#geopdwd_filtered.location.unique()
            geopdwd_filter = geopdwd_filter.copy()
            nmaxdisplayed = MAXCOUNTRIESDISPLAYED


            if len(locunique) >= nmaxdisplayed :#and func.__name__ != 'pycoa_pie' :
                if func.__name__ != 'pycoa_pie' :
                    geopdwd_filter = geopdwd_filter.loc[geopdwd_filter.clustername.isin(locunique[:nmaxdisplayed])]
                else:
                    geopdwd_filter_first = geopdwd_filter.loc[geopdwd_filter.clustername.isin(locunique[:nmaxdisplayed-1])]
                    geopdwd_filter_other = geopdwd_filter.loc[geopdwd_filter.clustername.isin(locunique[nmaxdisplayed-1:])]
                    geopdwd_filter_other = geopdwd_filter_other.groupby('date').sum()
                    geopdwd_filter_other['location'] = 'others'
                    geopdwd_filter_other['clustername'] = 'others'
                    geopdwd_filter_other['codelocation'] = 'others'
                    geopdwd_filter_other['permanentdisplay'] = 'others'
                    geopdwd_filter_other['rolloverdisplay'] = 'others'
                    geopdwd_filter_other['colors'] = '#FFFFFF'

                    geopdwd_filter = geopdwd_filter_first
                    geopdwd_filter = geopdwd_filter.append(geopdwd_filter_other)
            if func.__name__ == 'pycoa_horizonhisto' :
                #geopdwd_filter['bottom'] = geopdwd_filter.index
                geopdwd_filter['left'] = geopdwd_filter['cases']
                geopdwd_filter['right'] = geopdwd_filter['cases']
                geopdwd_filter['left'] = geopdwd_filter['left'].apply(lambda x: 0 if x > 0 else x)
                geopdwd_filter['right'] = geopdwd_filter['right'].apply(lambda x: 0 if x < 0 else x)

                n = len(geopdwd_filter.index)
                d =  plot_height / n
                ymax = plot_height

                geopdwd_filter['top'] = [ymax*(n-i)/n + d/2   for i in range(n)]
                geopdwd_filter['bottom'] = [ymax*(n-i)/n - d/2 for i in range(n)]
                geopdwd_filter['horihistotexty'] = geopdwd_filter['bottom'] + d/2
                geopdwd_filter['horihistotextx'] = geopdwd_filter['right']
                if maplabel and 'label%' in maplabel:
                    geopdwd_filter['right'] = geopdwd_filter['right'].apply(lambda x: 100.*x)
                    geopdwd_filter['horihistotextx'] = geopdwd_filter['right']
                    geopdwd_filter['horihistotext'] = [str(round(i))+'%' for i in geopdwd_filter['right']]
                else:
                    geopdwd_filter['horihistotext'] = [ '{:.3g}'.format(float(i)) if float(i)>1.e4 else round(float(i),2) for i in geopdwd_filter['right'] ]
                    geopdwd_filter['horihistotext'] = [str(i) for i in geopdwd_filter['horihistotext']]
            if func.__name__ == 'pycoa_pie' :
                geopdwd_filter = self.add_columns_for_pie_chart(geopdwd_filter,input_field)
                geopdwd = self.add_columns_for_pie_chart(geopdwd,input_field)
                if maplabel and 'label%' in maplabel:
                    geopdwd_filter['textdisplayed2'] = geopdwd_filter['percentage']
                    geopdwd['textdisplayed2'] =  geopdwd['percentage']

            source = ColumnDataSource(data = geopdwd)
            input_filter = geopdwd_filter
            srcfiltered = ColumnDataSource(data = input_filter)
            max_value = max(input_filter['cases'])
            min_value = min(input_filter['cases'])
            min_value_gt0 = min(input_filter[input_filter['cases'] > 0]['cases'])
            panels = []
            for axis_type in self.ax_type:
                plot_width = kwargs['plot_width']
                plot_height = kwargs['plot_height']
                standardfig = self.standardfig( x_axis_type = axis_type,  x_range = (1.05*min_value, 1.05 * max_value),**kwargs)
                if maplabel and 'label%' in maplabel:
                    standardfig.x_range = Range1d(0.01, 1.2 * max_value*100)
                    standardfig.xaxis.axis_label = 'percentage(%)'
                    standardfig.xaxis.formatter = BasicTickFormatter(use_scientific=False)
                else:
                    standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
                    standardfig.x_range = Range1d(0.01, 1.2 * max_value)
                if not input_filter[input_filter[input_field] < 0.].empty:
                    standardfig.x_range = Range1d(1.2 * min_value, 1.2 * max_value)

                if axis_type == "log":
                    if not input_filter[input_filter[input_field] < 0.].empty:
                        print('Some value are negative, can\'t display log scale in this context')
                    else:
                        if func.__name__ == 'pycoa_horizonhisto' :
                            if maplabel and 'label%' in maplabel:
                                standardfig.x_range = Range1d(0.01, 50 * max_value*100)
                            else:
                                standardfig.x_range = Range1d(0.01, 50 * max_value)
                            srcfiltered.data['left'] = [0.01] * len(srcfiltered.data['right'])

                if func.__name__ == 'pycoa_pie':
                    if not input_filter[input_filter[input_field] < 0.].empty:
                        raise CoaKeyError('Some values are negative, can\'t display a Pie chart, try histo by location')
                    standardfig.plot_width = plot_height
                    standardfig.plot_height = plot_height

                if date_slider:
                    date_slider.width = int(0.8*plot_width)
                    callback = CustomJS(args = dict(source = source,
                                                  source_filter = srcfiltered,
                                                  date_slider = date_slider,
                                                  ylabel = standardfig.yaxis[0],
                                                  title = standardfig.title,
                                                  x_range = standardfig.x_range,
                                                  x_axis_type = axis_type,
                                                  figure = standardfig),
                            code = """
                            var date_slide = date_slider.value;
                            var dates = source.data['date_utc'];
                            var val = source.data['cases'];
                            var loc = source.data['clustername'];
                            //var loc = source.data['location'];
                            var subregion = source.data['name_subregion'];
                            var codeloc = source.data['codelocation'];
                            var colors = source.data['colors'];

                            var newval = [];
                            var newloc = [];
                            var newcolors = [];
                            var newcodeloc = [];
                            var newname_subregion = [];
                            var labeldic = {};
                            for (var i = 0; i < dates.length; i++){
                            if (dates[i] == date_slide){
                                newval.push(parseFloat(val[i]));
                                newloc.push(loc[i]);
                                newcodeloc.push(codeloc[i]);
                                newcolors.push(colors[i]);
                                if(typeof subregion !== 'undefined')
                                    newname_subregion.push(subregion[i]);

                                }
                            }
                            var len = source_filter.data['clustername'].length;

                            var indices = new Array(len);
                            for (var i = 0; i < len; i++) indices[i] = i;

                            indices.sort(function (a, b) { return newval[a] > newval[b] ? -1 : newval[a] < newval[b] ? 1 : 0; });
                            var orderval = [];
                            var orderloc = [];
                            var ordercodeloc = [];
                            var ordername_subregion = [];
                            var ordercolors = [];
                            var textdisplayed = [];
                            for (var i = 0; i < len; i++)
                            {
                                orderval.push(newval[indices[i]]);
                                orderloc.push(newloc[indices[i]]);
                                ordercodeloc.push(newcodeloc[indices[i]]);

                                if(typeof subregion !== 'undefined')
                                    ordername_subregion.push(newname_subregion[i]);
                                ordercolors.push(newcolors[indices[i]]);
                                //labeldic[len-indices[i]] = newcodeloc[indices[i]];
                                textdisplayed.push(newcodeloc[indices[i]].padStart(40,' '));
                            }


                            source_filter.data['cases'] = orderval;
                            const reducer = (accumulator, currentValue) => accumulator + currentValue;
                            var tot = orderval.reduce(reducer);
                            var top = [];
                            var bottom = [];
                            var starts = [];
                            var ends = [];
                            var middle = [];
                            var text_x = [];
                            var text_y = [];
                            var r = 0.7;
                            var bthick = 0.95;
                            var cumul = 0.;
                            var percentage = [];
                            var angle = [];
                            var text_size = [];
                            var left_quad = [];
                            var right_quad = [];

                            for(var i = 0; i < orderval.length; i++)
                            {
                                cumul += ((orderval[i] / tot) * 2 * Math.PI);
                                ends.push(cumul);
                                if(i==0)
                                    starts.push(0);
                                else
                                    starts.push(ends[i-1]);
                                middle.push((ends[i]+starts[i])/2);
                                text_x.push(r*Math.cos(middle[i]));
                                text_y.push(r*Math.sin(middle[i]));
                                percentage.push(String(100.*orderval[i] / tot).slice(0, 4));
                                angle.push((orderval[i] / tot) * 2 * Math.PI)
                                /*if ((ends[i]-starts[i]) > 0.08*(2 * Math.PI))
                                    text_size.push('10pt');
                                else
                                    text_size.push('6pt');*/

                                //top.push((orderval.length-i) + bthick/2);
                                //bottom.push((orderval.length-i) - bthick/2);

                                if (isNaN(orderval[i])) orderval[i] = 0.;
                                if(orderval[i]<=0.)
                                {
                                    left_quad.push(orderval[i]);
                                    right_quad.push(0.);
                                }
                                else
                                {
                                    left_quad.push(0);
                                    right_quad.push(orderval[i]);
                                }
                            }

                            source_filter.data['clustername'] = orderloc;
                            source_filter.data['codelocation'] = ordercodeloc;
                            //source_filter.data['colors'] = ordercolors;

                            if(typeof subregion !== 'undefined')
                                source_filter.data['rolloverdisplay'] = ordername_subregion;
                            else
                                source_filter.data['rolloverdisplay'] = orderloc;

                            source_filter.data['ends'] = ends;
                            source_filter.data['starts'] = starts;
                            source_filter.data['middle'] = middle;
                            source_filter.data['text_x'] = text_x;
                            source_filter.data['text_y'] = text_y;
                            //source_filter.data['text_size'] = text_size;
                            source_filter.data['percentage'] = percentage;
                            source_filter.data['angle'] = angle;


                            source_filter.data['left'] = left_quad;
                            source_filter.data['right'] = right_quad;

                            var mid =[];
                            var ht = [];
                            var textdisplayed2 = [];

                            var n = right_quad.length;
                            var d = figure.plot_height / n;
                            var ymax = figure.plot_height;

                            for(i=0; i<right_quad.length;i++){
                                top.push(parseInt(ymax*(n-i)/n+d/2));
                                bottom.push(parseInt(ymax*(n-i)/n-d/2));
                                mid.push(parseInt(ymax*(n-i)/n));
                                labeldic[parseInt(ymax*(n-i)/n)] = ordercodeloc[i];

                                ht.push(right_quad[i].toFixed(2).toString());
                                var a=new Intl.NumberFormat().format(right_quad[i])
                                textdisplayed2.push(a.toString().padStart(26,' '));
                                //textdisplayed2.push(right_quad[i].toFixed(2).toString().padStart(40,' '));

                            }
                            source_filter.data['top'] = top;
                            source_filter.data['bottom'] = bottom;

                            source_filter.data['horihistotextxy'] =  mid;
                            source_filter.data['horihistotextx'] =  right_quad;
                            source_filter.data['horihistotext'] =  ht;
                            source_filter.data['permanentdisplay'] = ordercodeloc;
                            source_filter.data['textdisplayed'] = textdisplayed;
                            source_filter.data['textdisplayed2'] = textdisplayed2;
                            var maxx = Math.max.apply(Math, right_quad);
                            var minx = Math.min.apply(Math, left_quad);

                            ylabel.major_label_overrides = labeldic;
                            console.log(labeldic);
                            x_range.end =  1.2 * maxx;
                            x_range.start =  1.05 * minx;
                            if(minx >= 0){
                                x_range.start =  0.01;
                                source_filter.data['left'] = Array(left_quad.length).fill(0.01);
                                }
                            var tmp = title.text;
                            tmp = tmp.slice(0, -11);
                            var dateconverted = new Date(date_slide);
                            var dd = String(dateconverted.getDate()).padStart(2, '0');
                            var mm = String(dateconverted.getMonth() + 1).padStart(2, '0'); //January is 0!
                            var yyyy = dateconverted.getFullYear();
                            var dmy = dd + '/' + mm + '/' + yyyy;
                            title.text = tmp + dmy+")";

                            source_filter.change.emit();
                        """)
                    date_slider.js_on_change('value', callback)
                cases_custom = CocoDisplay.rollerJS()
                if func.__name__ == 'pycoa_pie' :
                    standardfig.add_tools(HoverTool(
                        tooltips=[('Location', '@rolloverdisplay'), (input_field, '@cases{0,0.0}'), ('%','@percentage'), ],
                        formatters={'location': 'printf', '@{' + 'cases' + '}': cases_custom, '%':'printf'},
                        point_policy="snap_to_data"))  # ,PanTool())
                else:
                    standardfig.add_tools(HoverTool(
                        tooltips=[('Location', '@rolloverdisplay'), (input_field, '@cases{0,0.0}'), ],
                        formatters={'location': 'printf', '@{' + 'cases' + '}': cases_custom, },
                        point_policy="snap_to_data"))  # ,PanTool())
                panel = Panel(child = standardfig, title = axis_type)
                panels.append(panel)
            return func(self, srcfiltered, panels, date_slider)
        return inner_decohistopie

    ''' VERTICAL HISTO '''
    @decowrapper
    @decohistomap
    @decohistopie
    def pycoa_horizonhisto(self, srcfiltered, panels, date_slider):
        '''
            -----------------
            Create 1D histogramme by location according to arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pycoa struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= width_height_default[1]
            - plot_width = width_height_default[0]
            - title = None
            - textcopyright = default
            - mode = mouse
            - cursor_date = None if True
                    - orientation = horizontal
            - when : default min and max according to the inpude DataFrame.
                         Dates are given under the format dd/mm/yyyy.
                         when format [dd/mm/yyyy : dd/mm/yyyy]
                         if [:dd/mm/yyyy] min date up to
                         if [dd/mm/yyyy:] up to max date
        '''
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

            #print(fig.y_range ,fig.yaxis.major_label_overrides)
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
        if date_slider:
                tabs = column(date_slider,tabs)
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
        locale.setlocale(locale.LC_ALL, 'en_US')
        df['textdisplayed2'] = [ locale.format("%d", i, grouping=True)\
                for i in df[column_name]]
        #df['textdisplayed2'] = df[column_name].astype(str) #[i.str for i in df[column_name]]
        df['textdisplayed2'] = df['textdisplayed2'].str.pad(26, side = "left")
        #df['textdisplayed2']  = df[column_name].str.pad(26, side = "left")
        df.loc[df['diff'] <= np.pi/20,'textdisplayed']=''
        df.loc[df['diff'] <= np.pi/20,'textdisplayed2']=''
        df['percentage'] = 100.*df['percentage']
        return df

    @decowrapper
    @decohistomap
    @decohistopie
    def pycoa_pie(self, srcfiltered, panels, date_slider):
        '''
            -----------------
            Create a pie chart according to arguments.
            See help(pycoa_pie).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pycoa struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= width_height_default[1]
            - plot_width = width_height_default[0]
            - title = None
            - textcopyright = default
            - mode = mouse
            - cursor_date = None if True
                    - orientation = horizontal
        '''
        standardfig = panels[0].child
        standardfig.plot_height=400
        standardfig.plot_width=400
        standardfig.x_range = Range1d(-1.1, 1.1)
        standardfig.y_range = Range1d(-1.1, 1.1)
        standardfig.axis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None

        standardfig.wedge(x=0, y=0, radius=1.,line_color='#E8E8E8',
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        fill_color='colors', legend_label='clustername', source=srcfiltered)
        standardfig.legend.visible = False

        labels = LabelSet(x=0, y=0,text='textdisplayed',angle=cumsum('angle', include_zero=True),
        text_font_size="10pt",source=srcfiltered,render_mode='canvas')

        labels2 = LabelSet(x=0, y=0, text='textdisplayed2',
        angle=cumsum('angle', include_zero=True),text_font_size="8pt",source=srcfiltered)

        standardfig.add_layout(labels)
        standardfig.add_layout(labels2)
        if date_slider:
            standardfig = column(date_slider,standardfig)
        return standardfig

    ''' MAP FOLIUM '''
    @decowrapper
    @decohistomap
    def pycoa_mapfolium(self, geopdwd, input_field, **kwargs):
        '''
            -----------------
            Create a map folium to arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pycoa struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= width_height_default[1]
            - plot_width = width_height_default[0]
            - title = None
            - textcopyright = default
            - mode = mouse
            - cursor_date = None if True
                    - orientation = horizontal
            - when : default min and max according to the inpude DataFrame.
                         Dates are given under the format dd/mm/yyyy.
                         when format [dd/mm/yyyy : dd/mm/yyyy]
                         if [:dd/mm/yyyy] min date up to
                         if [dd/mm/yyyy:] up to max date
        '''
        title = kwargs.get('title', None)
        tile =  kwargs.get('tile', self.dvisu_default['tile'])
        tile = CocoDisplay.convert_tile(tile, 'folium')
        maplabel = kwargs.get('maplabel',self.dvisu_default['maplabel'])
        plot_width = kwargs.get('plot_width',self.dfigure_default['plot_width'])
        plot_height = kwargs.get('plot_height',self.dfigure_default['plot_height'])

        geopdwd['cases'] = geopdwd[input_field]
        geopdwd_filtered = geopdwd.loc[geopdwd.date == self.when_end]
        geopdwd_filtered = geopdwd_filtered.reset_index(drop = True)
        geopdwd_filtered['cases'] = geopdwd_filtered[input_field]
        my_date = geopdwd.date.unique()
        dico_utc = {i: DateSlider(value=i).value for i in my_date}
        geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
        #geopdwd = geopdwd.drop_duplicates(["date", "codelocation","clustername"])#for sumall avoid duplicate
        #geopdwd_filtered = geopdwd_filtered.sort_values(by='cases', ascending = False).reset_index()
        #locunique = geopdwd_filtered.clustername.unique()#geopdwd_filtered.location.unique()
        if self.database_name == 'risklayer':
            geopdwd_filtered = geopdwd_filtered.loc[geopdwd_filtered.geometry.notna()]

        uniqloc = list(geopdwd_filtered.codelocation.unique())
        geopdwd_filtered = geopdwd_filtered.drop(columns=['date', 'colors'])

        msg = "(data from: {})".format(self.database_name)

        minx, miny, maxx, maxy =  geopdwd_filtered.total_bounds

        mapa = folium.Map(tiles=tile, attr='<a href=\"http://pycoa.fr\"> ©pycoa.fr </a>' + msg)
        #min_lat=minx, max_lat=maxx, min_lon=miny, max_lon=maxy)
        #location=[geopdwd_filtered.centroid.y.mean(),geopdwd_filtered.centroid.x.mean()],)
        if self.dbld[self.database_name][0] != 'WW':
            mapa.fit_bounds([(miny, minx), (maxy, maxx)])

        fig = Figure(width=plot_width, height=plot_height)
        fig.add_child(mapa)
        min_col, max_col = CocoDisplay.min_max_range(np.nanmin(geopdwd_filtered[input_field]),
                                                     np.nanmax(geopdwd_filtered[input_field]))
        min_col_non0 = (np.nanmin(geopdwd_filtered.loc[geopdwd_filtered['cases']>0.]['cases']))

        invViridis256 = Viridis256[::-1]
        if 'log' in maplabel:
            geopdwd_filtered['cases'] = geopdwd_filtered.loc[geopdwd_filtered['cases']>0]['cases']
            color_mapper = LinearColorMapper(palette=invViridis256, low=min_col_non0, high=max_col, nan_color='#d9d9d9')
            colormap =  branca.colormap.LinearColormap(color_mapper.palette).to_step(data=list(geopdwd_filtered['cases']),n=10,method='log')
        else:
            color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#d9d9d9')
            colormap = branca.colormap.LinearColormap(color_mapper.palette).scale(min_col, max_col)
        colormap.caption =  title
        colormap.add_to(mapa)
        map_id = colormap.get_name()

        custom_label_colorbar_js = """
        var div = document.getElementById('legend');
        var ticks = document.getElementsByClassName('tick')
        for(var i = 0; i < ticks.length; i++){
        var values = ticks[i].textContent.replace(',','')
        val = parseFloat(values).toExponential(1).toString().replace("+", "")
        if(parseFloat(ticks[i].textContent) == 0) val = 0.
        div.innerHTML = div.innerHTML.replace(ticks[i].textContent,val);
        }
        """
        e = Element(custom_label_colorbar_js)
        html = colormap.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e
        geopdwd_filtered[input_field + 'scientific_format'] = \
            (['{:.5g}'.format(i) for i in geopdwd_filtered['cases']])
        # (['{:.3g}'.format(i) if i>100000 else i for i in geopdwd_filter[input_field]])

        map_dict = geopdwd_filtered.set_index('location')[input_field].to_dict()
        if np.nanmin(geopdwd_filtered[input_field]) == np.nanmax(geopdwd_filtered[input_field]):
            map_dict['FakeCountry'] = 0.

        if 'log' in maplabel:
            color_scale =  branca.colormap.LinearColormap(color_mapper.palette).to_step(data=list(geopdwd_filtered['cases']),n=10,method='log')
        else:
            color_scale = LinearColormap(color_mapper.palette, vmin=min(map_dict.values()), vmax=max(map_dict.values()))

        def get_color(feature):
            value = map_dict.get(feature['properties']['location'])
            if value is None or np.isnan(value):
                return '#8c8c8c'  # MISSING -> gray
            else:
                return color_scale(value)

        displayed = 'rolloverdisplay'
        folium.GeoJson(
            geopdwd_filtered,
            style_function=lambda x:
            {
                'fillColor': get_color(x),
                'fillOpacity': 0.8,
                'color': None
            },
            highlight_function=lambda x: {'weight': 2, 'color': 'green'},
            tooltip=folium.features.GeoJsonTooltip(fields=[displayed, input_field + 'scientific_format'],
                                                   aliases=['location' + ':', input_field + ":"],
                                                   style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                        opacity: 0.2;
                        """),
            # '<div style="barialckground-color: royalblue 0.2; color: black; padding: 2px; border: 1px solid black; border-radius: 2px;">'+input_field+'</div>'])
        ).add_to(mapa)
        return mapa

    ''' DECORATOR FOR MAP BOKEH '''
    def decopycoageo(func):
        @wraps(func)
        def innerdecopycoageo(self, geopdwd, input_field, **kwargs):
            geopdwd['cases'] = geopdwd[input_field]
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
                            new_poly.append(CocoDisplay.wgs84_to_web_mercator(pt))
                        elif type(pt) == list:
                            shifted = []
                            for p in pt:
                                shifted.append(CocoDisplay.wgs84_to_web_mercator(p))
                            new_poly.append(sg.Polygon(shifted))
                        else:
                            raise CoaTypeError("Neither tuple or list don't know what to do with \
                                your geometry description")

                    if type(new_poly[0]) == tuple:
                        geolistmodified[row['location']] = sg.Polygon(new_poly)
                    else:
                        geolistmodified[row['location']] = sg.MultiPolygon(new_poly)
            ng = pd.DataFrame(geolistmodified.items(), columns=['location', 'geometry'])
            geolistmodified = gpd.GeoDataFrame({'location': ng['location'], 'geometry': gpd.GeoSeries(ng['geometry'])}, crs="epsg:3857")
            geopdwd_filtered = geopdwd_filtered.drop(columns='geometry')
            geopdwd_filtered = pd.merge(geolistmodified, geopdwd_filtered, on='location')
            #if kwargs['wanted_dates']:
            #    kwargs.pop('wanted_dates')
            return func(self, geopdwd, geopdwd_filtered, **kwargs)
        return innerdecopycoageo

    ''' RETURN GEOMETRY, LOCATIO + CASES '''
    @decowrapper
    @decohistomap
    @decopycoageo
    def pycoageo(self, geopdwd, geopdwd_filtered, **kwargs):
        return geopdwd_filtered

    def decomap(func):
        @wraps(func)
        def innerdecomap(self, geopdwd, geopdwd_filtered, **kwargs):
            title = kwargs.get('title', None)
            maplabel = kwargs.get('maplabel',self.dvisu_default['maplabel'])
            tile =  kwargs.get('tile', None)
            if tile:
                tile = CocoDisplay.convert_tile(tile, 'bokeh')

            uniqloc = list(geopdwd_filtered.clustername.unique())
            dfLabel = pd.DataFrame()
            sourcemaplabel = ColumnDataSource(dfLabel)
            if maplabel or func.__name__ == 'pycoa_pimpmap':
                locsum = geopdwd_filtered.clustername.unique()
                numberpercluster = geopdwd_filtered['clustername'].value_counts().to_dict()
                sumgeo = geopdwd_filtered.copy()
                sumgeo['geometry'] = sumgeo['geometry'].buffer(0.001) #needed with geopandas 0.10.2
                sumgeo = sumgeo.dissolve(by='clustername', aggfunc='sum').reset_index()
                sumgeo['nb'] = sumgeo['clustername'].map(numberpercluster)
                #print(geopdwd_filtered.loc[geopdwd_filtered.clustername=='Île-de-France'].reset_index(drop=True).explode(index_parts=False))
                centrosx = sumgeo['geometry'].centroid.x
                centrosy = sumgeo['geometry'].centroid.y
                cases = sumgeo['cases']/sumgeo['nb']
                dfLabel=pd.DataFrame({'clustername':sumgeo.clustername,'centroidx':centrosx,'centroidy':centrosy,'cases':cases,'geometry':sumgeo['geometry']})

                if 'spark' in maplabel:
                    sparkos = {i: CocoDisplay.sparkline(geopdwd.loc[ (geopdwd.clustername==i) &
                                (geopdwd.date >= self.when_beg) &
                                (geopdwd.date <= self.when_end)].sort_values(by='date')['cases']) for i in locsum }
                    dfpimp = pd.DataFrame(list(sparkos.items()), columns=['clustername', 'pimpmap'])
                    dfLabel=pd.merge(dfLabel,dfpimp,on=['clustername'],how="inner")
                if 'spiral' in maplabel:
                    sparkos = {i: CocoDisplay.spiral(geopdwd.loc[ (geopdwd.clustername==i) &
                                (geopdwd.date >= self.when_beg) &
                                (geopdwd.date <= self.when_end)].sort_values(by='date')[['date','cases','clustername']]) for i in locsum }
                    dfpimp = pd.DataFrame(list(sparkos.items()), columns=['clustername', 'pimpmap'])
                    dfLabel=pd.merge(dfLabel,dfpimp,on=['clustername'],how="inner")

                dfLabel['cases'] = dfLabel['cases'].round(2)
                # Converting links to html tags
                if 'label%' in maplabel:
                    dfLabel['cases'] = [str(round(float(i*100),2))+'%' for i in dfLabel['cases']]
                else:
                    dfLabel['cases']=[str(i) for i in dfLabel['cases']]
                sourcemaplabel = ColumnDataSource(dfLabel.drop(columns='geometry'))
            minx, miny, maxx, maxy =  geopdwd_filtered.total_bounds #self.boundary
            #if self.dbld[self.database_name][0] != 'WW':
            #    ratio = 0.05
            #    minx -= ratio*minx
            #    maxx += ratio*maxx
            #    miny -= ratio*miny
            #    maxy += ratio*maxy
            #if func.__name__ == 'pycoa_pimpmap':
            #    dico['titlebar']=tit[:-12]+' [ '+dico['when_beg'].strftime('%d/%m/%Y')+ '-'+ tit[-12:-1]+'])'

            kwargs['plot_width']=kwargs['plot_height']
            x_range=(minx,maxx)
            y_range=(miny,maxy)
            if func.__name__ == 'pycoa_pimpmap':
                standardfig = self.standardfig(x_range=x_range, y_range=y_range, x_axis_type="mercator", y_axis_type="mercator",**kwargs,match_aspect=True)
            else:
                standardfig = self.standardfig(x_axis_type="mercator", y_axis_type="mercator",**kwargs,match_aspect=True)

            if tile:
                wmt = WMTSTileSource(
                            url=tile)
                standardfig.add_tile(wmt)
            else:
                standardfig.background_fill_color = "lightgrey"

            geopdwd_filtered = geopdwd_filtered[['cases','geometry','location','clustername','codelocation','rolloverdisplay']]
            if not dfLabel.empty:
                geopdwd_filtered = geopdwd_filtered.drop(columns = 'geometry')
                geopdwd_filtered = pd.merge(geopdwd_filtered, dfLabel[['clustername','geometry']], on = 'clustername')
                geopdwd_filtered = geopdwd_filtered.drop_duplicates(subset = ['clustername'])
            if self.dbld[self.database_name][0] == 'BEL' :
                reorder = list(geopdwd_filtered.location.unique())
                geopdwd_filtered = geopdwd_filtered.set_index('location')
                geopdwd_filtered = geopdwd_filtered.reindex(index = reorder)
                geopdwd_filtered = geopdwd_filtered.reset_index()

            if self.dbld[self.database_name][0] == 'GBR' :
                geopdwd = geopdwd.loc[~geopdwd.cases.isnull()]
                geopdwd_filtered  = geopdwd_filtered.loc[~geopdwd_filtered.cases.isnull()]
            return func(self, geopdwd, geopdwd_filtered, sourcemaplabel, standardfig,**kwargs)
        return innerdecomap

    ''' MAP BOKEH '''
    @decowrapper
    @decohistomap
    @decopycoageo
    @decomap
    def pycoa_map(self, geopdwd, geopdwd_filtered, sourcemaplabel, standardfig,**kwargs):
        '''
            -----------------
            Create a map bokeh with arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pycoa struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= width_height_default[1]
            - plot_width = width_height_default[0]
            - title = None
            - textcopyright = default
            - mode = mouse
            - cursor_date = None if True
                    - orientation = horizontal
            - when : default min and max according to the inpude DataFrame.
                         Dates are given under the format dd/mm/yyyy.
                         when format [dd/mm/yyyy : dd/mm/yyyy]
                         if [:dd/mm/yyyy] min date up to
                         if [dd/mm/yyyy:] up to max date
            - tile : tile
            - maplabel: False
        '''

        date_slider = kwargs['date_slider']
        maplabel = kwargs.get('maplabel',self.dvisu_default['maplabel'])
        min_col, max_col = CocoDisplay.min_max_range(np.nanmin(geopdwd_filtered['cases']),
                                                     np.nanmax(geopdwd_filtered['cases']))

        min_col_non0 = (np.nanmin(geopdwd_filtered.loc[geopdwd_filtered['cases']>0.]['cases']))

        json_data = json.dumps(json.loads(geopdwd_filtered.to_json()))
        geopdwd_filtered = GeoJSONDataSource(geojson=json_data)

        invViridis256 = Viridis256[::-1]
        if 'log' in maplabel:
            color_mapper = LogColorMapper(palette=invViridis256, low=min_col_non0, high=max_col, nan_color='#ffffff')
        else:
            color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#ffffff')
            color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4, width=standardfig.plot_width, bar_line_cap='round',
                             border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))

        if 'label%' in maplabel:
            color_bar.formatter = BasicTickFormatter(use_scientific=False)
            color_bar.formatter = NumeralTickFormatter(format="0.0%")

        standardfig.add_layout(color_bar, 'below')

        if date_slider:
            allcases_location, allcases_dates = pd.DataFrame(), pd.DataFrame()
            allcases_location = geopdwd.groupby('location')['cases'].apply(list)
            geopdwd_tmp = geopdwd.drop_duplicates(subset = ['location']).drop(columns = 'cases')
            geopdwd_tmp = pd.merge(geopdwd_tmp, allcases_location, on = 'location')
            geopdwd_tmp  = geopdwd_tmp.drop_duplicates(subset = ['clustername'])
            geopdwd_tmp = ColumnDataSource(geopdwd_tmp.drop(columns=['geometry']))

            sourcemaplabel.data['rolloverdisplay'] = sourcemaplabel.data['clustername']
            callback = CustomJS(args =  dict(source = geopdwd_tmp, source_filter = geopdwd_filtered,
                                          date_sliderjs = date_slider, title=standardfig.title,
                                          maplabeljs = sourcemaplabel),
                        code = """
                        var ind_date_max = (date_sliderjs.end-date_sliderjs.start)/(24*3600*1000);
                        var ind_date = (date_sliderjs.value-date_sliderjs.start)/(24*3600*1000);
                        var new_cases = [];
                        var dict = {};
                        var iloop = source_filter.data['clustername'].length;

                        function form(value) {
                             if(value>10000 || value <0.01)
                                value =  Number.parseFloat(value).toExponential(2);
                             else
                                 value = Number.parseFloat(value).toFixed(2);
                            console.log(value);
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
                        var dateconverted = new Date(date_sliderjs.value);
                        var dd = String(dateconverted.getDate()).padStart(2, '0');
                        var mm = String(dateconverted.getMonth() + 1).padStart(2, '0'); //January is 0!
                        var yyyy = dateconverted.getFullYear();
                        var dmy = dd + '/' + mm + '/' + yyyy;
                        title.text = tmp + dmy+")";
                        if (maplabeljs.get_length() !== 0)
                            maplabeljs.change.emit();

                        console.log(maplabeljs.data['cases']);
                        source_filter.change.emit();
                    """)
            date_slider.js_on_change('value', callback)


        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.patches('xs', 'ys', source = geopdwd_filtered,
                            fill_color = {'field': 'cases', 'transform': color_mapper},
                            line_color = 'black', line_width = 0.25, fill_alpha = 1)

        if 'text' in maplabel :
            labels = LabelSet(
                x = 'centroidx',
                y = 'centroidy',
                text = 'cases',
                source = sourcemaplabel, text_font_size='10px',text_color='white',background_fill_color='grey',background_fill_alpha=0.5)
            standardfig.add_layout(labels)

        #cases_custom = CocoDisplay.rollerJS()
        callback = CustomJS(code="""
        //document.getElementsByClassName('bk-tooltip')[0].style.backgroundColor="transparent";
        document.getElementsByClassName('bk-tooltip')[0].style.opacity="0.7";
        """ )
        tooltips = """
                    <b>location: @rolloverdisplay<br>
                    cases: @cases{0,0.0}</b>
                   """
        standardfig.add_tools(HoverTool(tooltips = tooltips,
        formatters = {'location': 'printf', 'cases': 'printf',},
        point_policy = "snap_to_data",callback=callback))  # ,PanTool())
        if date_slider:
            standardfig = column(date_slider, standardfig)
        return standardfig

    ''' PIMPMAP BOKEH '''
    @decowrapper
    @decohistomap
    @decopycoageo
    @decomap
    def pycoa_pimpmap(self, geopdwd, geopdwd_filtered, sourcemaplabel, standardfig,**kwargs):
        '''
            -----------------
            Create a bokeh map with pimpline label and with to arguments.
            See help(pycoa_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pycoa struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
            - input_field = if None take second element could be a list
            - plot_heigh= width_height_default[1]
            - plot_width = width_height_default[0]
            - title = None
            - textcopyright = default
            - mode = mouse
            - cursor_date = None if True
                    - orientation = horizontal
            - when : default min and max according to the inpude DataFrame.
                         Dates are given under the format dd/mm/yyyy.
                         when format [dd/mm/yyyy : dd/mm/yyyy]
                         if [:dd/mm/yyyy] min date up to
                         if [dd/mm/yyyy:] up to max date
            - tile : tile
            - maplabel: False
        '''
        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None

        min_col, max_col = CocoDisplay.min_max_range(np.nanmin(geopdwd_filtered['cases']),
                                                     np.nanmax(geopdwd_filtered['cases']))

        json_data = json.dumps(json.loads(geopdwd_filtered.to_json()))
        geopdwd_filtered = GeoJSONDataSource(geojson=json_data)

        invViridis256 = Viridis256[::-1]
        color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#ffffff')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4,
                             border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))
        standardfig.add_layout(color_bar, 'below')
        standardfig.patches('xs', 'ys', source = geopdwd_filtered,
                                    fill_color = {'field': 'cases', 'transform': color_mapper},
                                    line_color = 'black', line_width = 0.25, fill_alpha = 1)
        standardfig.image_url(url='pimpmap', x='centroidx', y='centroidy',source=sourcemaplabel,anchor="center")
        return standardfig
    ######################
    def tiles_list(self):
        return self.available_tiles
    ###################### BEGIN Static Methods ##################
    @staticmethod
    def convert_tile(tilename, which = 'bokeh'):
        ''' Return tiles url according to folium or bokeh resquested'''
        tile = 'openstreet'
        if tilename == 'openstreet':
            if which == 'folium':
                tile = r'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            else:
                tile = r'http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png'
        elif tilename == 'positron':
            print('Problem with positron tile (huge http resquest need to check), esri is then used ...')
            tile = r'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'
        #    tile = 'https://tiles.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
        elif tilename == 'esri':
            tile = r'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'
        elif tilename == 'stamen':
            tile = r'http://tile.stamen.com/toner/{z}/{x}/{y}.png'
        else:
            print('Don\'t know you tile ... take default one: ')
        return tile
    #####################
    @staticmethod
    def dict_shorten_loc(toshort):
        '''
            return a shorten name location
        '''
        s = []
        if type(toshort) == np.ndarray:
            toshort = list(toshort)
            toshort = [toshort]
            s = ''
        elif type(toshort) == str:
            toshort = [toshort]
            s = ''
        #if type(toshort) != list:
        #    print('That is weird ...', toshort, 'not str nor list')
        for val in toshort:
            if not isinstance(val,str):
                val= str(val)
            if type(val) == list:
                val = val[0]
            if val.find(',') == -1:
                A = val
            else:
                txt = val.split(',')
                if len(txt[0]) < 4 and len(txt[-1]) < 4:
                    A = [txt[0] + '...' + txt[-1]]
                else:
                    A = txt[0][:5] + '...' + txt[-1][-5:]
            if type(s) == list:
                s.append(A)
            else:
                s = A
            if isinstance(s, list):
                s=s[0]
        return s
    ######################
    @staticmethod
    def bokeh_legend(bkfigure):
        toggle_legend_js = CustomJS(args=dict(leg=bkfigure.legend[0]),
                                    code="""
        if(leg.visible)
        {
            leg.visible = false;
        }
        else
        {
            leg.visible = true;
        }
        """)
        bkfigure.js_on_event(events.DoubleTap, toggle_legend_js)
    ######################
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
    ######################
    @staticmethod
    def save_map2png(map=None, pngfile='map.png'):
        """
        Save map as png geckodriver and PIL packages are needed
        """
        size = width_height_default[0], width_height_default[1]
        if pngfile:
            pngfile = pngfile
        img_data = map._to_png(5)
        img = Image.open(io.BytesIO(img_data))
        img.thumbnail(size, Image.ANTIALIAS)
        img.save(pngfile)
        print(pngfile, ' is now save ...')
    ######################
    @staticmethod
    def save_pandas_as_png(df=None, pngfile='pandas.png'):
        source = ColumnDataSource(df)
        df_columns = [df.index.name]
        df_columns.extend(df.columns.values)
        columns_for_table = []
        for column in df_columns:
            if column is not None:
                columns_for_table.append(TableColumn(field=column, title=column))
                # width_height_default
        data_table = DataTable(source=source, columns=columns_for_table,
                               height_policy="auto", width_policy="auto", index_position=None)
        export_png(data_table, filename=pngfile)
    ######################
    @staticmethod
    def changeto_nonan_date(df=None, when_end=None, field=None):
        if not isinstance(when_end, dt.date):
            raise CoaTypeError(' Not a valid data ... ')

        boolval = True
        j = 0
        while (boolval):
            boolval = df.loc[df.date == (when_end - dt.timedelta(days=j))][field].dropna().empty
            j += 1
        if j > 1:
            verb(str(when_end) + ': all the value seems to be nan! I will find an other previous date.\n' +
                 'Here the date I will take: ' + str(when_end - dt.timedelta(days=j - 1)))
        return when_end - dt.timedelta(days=j - 1)
    ######################
    @staticmethod
    def changeto_nonull_date(df=None,when_end = None, field=None):
        if not isinstance(when_end, dt.date):
            raise CoaTypeError(' Not a valid data ... ')
        boolval = True
        j = 0
        #df = df.fillna(0)
        if all(df[field] == 0):
            print('all value is null for all date !')
            return when_end
        else:
            while(boolval):
                boolval = all(v == 0. or np.isnan(v) for v in df.loc[df.date == (when_end - dt.timedelta(days=j))][field].values)
                j += 1
            if j > 1:
                verb(str(when_end) + ': all the value seems to be 0! I will find an other previous date.\n' +
                     'Here the date I will take: ' + str(when_end - dt.timedelta(days=j - 1)))
            return when_end - dt.timedelta(days=j - 1)
    ######################
    @staticmethod
    def get_utcdate(date):
        return (date - dt.date(1970, 1, 1)).total_seconds() * 1000.
    ######################
    @staticmethod
    def test_all_val_null(s):
        a = s.to_numpy()
        return (a == 0).all()
    ######################
    @staticmethod
    def get_polycoords(geopandasrow):
        """
        Take a row of a geopandas as an input (i.e : for index, row in geopdwd.iterrows():...)
            and returns a tuple (if the geometry is a Polygon) or a list (if the geometry is a multipolygon)
            of an exterior.coords
        """
        geometry = geopandasrow['geometry']
        all = []
        if geometry.type == 'Polygon':
            return list(geometry.exterior.coords)
        if geometry.type == 'MultiPolygon':
            for ea in geometry.geoms:
                all.append(list(ea.exterior.coords))
            return all
    ######################
    @staticmethod
    def wgs84_to_web_mercator(tuple_xy):
        """
        Take a tuple (longitude,latitude) from a coordinate reference system crs=EPSG:4326
         and converts it to a  longitude/latitude tuple from to Web Mercator format
        """
        k = 6378137
        x = tuple_xy[0] * (k * np.pi / 180.0)
        if tuple_xy[1] == -90:
            lat = -89.99
        else:
            lat = tuple_xy[1]
        y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
        return x, y
    ######################
    @staticmethod
    def rollerJS():
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
    ######################
    @staticmethod
    def sparkline(data, figsize=(0.5, 0.5), **kwags):
        """
        Returns a HTML image tag containing a base64 encoded sparkline style plot
        """
        data = list(data)
        fig, ax = plt.subplots(1, 1, figsize=figsize, **kwags)
        ax.patch.set_alpha(0.3)
        ax.plot(data)
        for k,v in ax.spines.items():
            v.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.plot(len(data) - 1, data[len(data) - 1], 'r.')

        #ax.fill_between(range(len(data)), data, len(data)*[min(data)], color='green',alpha=0.1)
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        plt.close()
        return 'data:image/png;base64,' + "{}".format(base64.b64encode(img.read()).decode())
    ###################### END Static Methods ##################
    @staticmethod
    def spiral(data, figsize=(0.5, 0.5), **kwags):
        """
        Returns a HTML image tag containing a base64 encoded spiral style plot
        https://github.com/emilienschultz/researchnotebooks/blob/master/20220116%20-%20Visualisation%20polaire%20cas%20COVID-19.ipynb
        """
        data["date"] = pd.to_datetime(data["date"])
        # Utiliser des méthodes de l'objet date de Pandas pour créer de nouvelles colonnes
        data["dayofyear"] = data["date"].dt.dayofyear # j'ai cherché comment faire dayofyear et il se trouve qu'il y a une fonction
        data["year"] = data["date"].dt.year

        K = 2*data['cases'].max()
        data["dayofyear_angle"] = data["dayofyear"]*2 * np.pi/365 # gérer plus finement l'année bissextile
        data["r_baseline"] = data.apply(lambda x : ((x["year"]-2020)*2 * np.pi + x["dayofyear_angle"])*K,axis=1)

        E = 8 # facteur d'expansion des données
        data["r_cas_sup"] = data.apply(lambda x : x["r_baseline"] + E*x["cases"],axis=1)
        data["r_cas_inf"] = data.apply(lambda x : x["r_baseline"] - E*x["cases"],axis=1)

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'},figsize=(1,1))

        #ax.set_xticklabels(['     january', '', 'april', '', 'july    ', '', 'october', ''])
        ax.plot(data["dayofyear_angle"], data["r_baseline"])
        ax.plot(data["dayofyear_angle"], data["r_cas_sup"],color="black")
        ax.plot(data["dayofyear_angle"], data["r_cas_inf"],color="black")

        ax.plot(data["dayofyear_angle"], data["r_cas_sup"],color="lightblue")
        ax.plot(data["dayofyear_angle"], data["r_cas_inf"],color="lightblue")

        ax.fill_between(data["dayofyear_angle"],data["r_baseline"], data["r_cas_sup"],color="lightblue")
        ax.fill_between(data["dayofyear_angle"],data["r_baseline"], data["r_cas_inf"],color="lightblue")
        ax.set_rticks([])
        ax.grid(False)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        #ax.fill_between(range(len(data)), data, len(data)*[min(data)], color='green',alpha=0.1)
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        plt.close()
        return 'data:image/png;base64,' + "{}".format(base64.b64encode(img.read()).decode())
