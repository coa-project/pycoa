# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.allvisu

About :
-------

An interface module to easily plot pycoa data with bokeh

"""
from coa.tools import (
    kwargs_test,
    extract_dates,
    verb,
    fill_missing_dates
)
from coa.error import *
from coa.dbparser import _db_list_dict
import math
import pandas as pd
import geopandas as gpd
import numpy as np
import seaborn as sns
from collections import defaultdict
import itertools
import json
import io
from io import BytesIO
import base64
from IPython import display
import copy
import locale
import inspect

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
from bokeh.models.widgets import (
    Tabs,
    Panel,
    Button,
    TableColumn,
    Toggle
)
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

import branca.colormap
from branca.colormap import LinearColormap
from branca.element import (
    Element,
    Figure
)
import folium

import shapely.geometry as sg
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['backend']
import datetime as dt
import bisect
from functools import wraps
from IPython.core.display import (
    display,
    HTML
)

width_height_default = [500, 380]
MAXCOUNTRIESDISPLAYED = 24
class AllVisu:
    """
        All visualisation should be implemented here !
    """
    def __init__(self, db = None, kindgeo = None):
        if kindgeo is None:
            pass
        else:
            self.kindgeo = kindgeo

        verb("Init of AllVisu() with db=" + str(db))
        self.database_name = db
        self.dbld = _db_list_dict
        self.lcolors = Category20[20]
        self.scolors = Category10[5]
        self.pycoageopandas = False
        self.ax_type = ['linear', 'log']
        self.geom = []
        self.geopan = gpd.GeoDataFrame()
        self.listfigs = []

        self.setchartsfunctions = [method for method in dir(AllVisu) if callable(getattr(AllVisu, method)) and method.startswith("pycoa_") and not method.startswith("__")]
        self._dict_bypop = {'no':0,'100':100,'1k':1e3,'100k':1e5,'1M':1e6,'pop':1.}

        self.dicochartargs  = {
                                'where':None,\
                                'option':['nonneg', 'nofillnan', 'smooth7', 'sumall'],\
                                'which':None,\
                                'what':['standard', 'daily', 'weekly'],\
                                'when':None,\
                                'input':None,\
                                'input_field':None,\
                                'typeofhist':['bylocation','byvalue','pie'],\
                                'typeofplot':['date','menulocation','versus','spiral','yearly'],\
                                'bins':10,\
                                'bypop':list(self._dict_bypop.keys()),\
                                'dateslider':[False,True],\
                                'output':['pandas','geopandas','list', 'dict', 'array']
                                }
        self.listchartkargs = list(self.dicochartargs.keys())

        self.dicofigureargs = {
                                'plot_height':width_height_default[1],\
                                'plot_width':width_height_default[0],\
                                'title':None,\
                                'copyright': None
                                }
        self.dicovisuargs =  {
                             'vis':['bokeh','folium','seaborn','mplt'],
                             'mode':['mouse','vline','hline'],\
                             'tile' : ['openstreet','esri','stamen'],\
                             'orientation':['horizontal','vertical'],\
                             'dateslider':[False,True],\
                             'maplabel':['text','textinteger','spark','label%','log','unsorted','exploded','dense'],\
                             'guideline':[False,True],\
                             }
        self.listviskargs = list(self.dicovisuargs.keys())

        self.when_beg = dt.date(1, 1, 1)
        self.when_end = dt.date(1, 1, 1)

        try:
            self.iso3country = self.dbld[self.database_name][0]
            self.granularity = self.dbld[self.database_name][1]
            self.namecountry = self.dbld[self.database_name][2]
        except:
            pass

        self.dicokfront = {}
        self.dchartkargs = {}
        self.dvisukargs = {}
        self.uptitle, self.subtitle = ' ',' '


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
            - add kwargs set in the setvisu front end to global kwargs variable : kwargs.update(self.getkwargsfront())
            """
            if not isinstance(kwargs['input'], pd.DataFrame):
                raise CoaTypeError(input + 'Must be a pandas, with pycoa structure !')

            kwargs_test(kwargs, self.listchartkargs, 'Bad args used in the display function.')
            kwargs.update(self.getkwargsfront())

            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            which = kwargs.get('which', input.columns[2])
            when = kwargs.get('when', None)
            option = kwargs.get('option', None)
            #bins = kwargs.get('bins', self.dicochartargs['bins'])

            tile = kwargs.get('tile', self.dicovisuargs['tile'])
            titlesetted = kwargs.get('title', self.dicofigureargs['title'])
            maplabel = kwargs.get('maplabel', self.dicovisuargs['maplabel'])
            if isinstance(which,list):
                which = input.columns[2]
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

            if type(input)==gpd.geodataframe.GeoDataFrame:
               self.pycoageopandas = True

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

            for i in input_field:
                if input[i].isnull().all():
                    #raise CoaTypeError("Sorry all data are NaN for " + i)
                    print("Sorry all data are NaN for " + i)
                else:
                    when_end_change = min(when_end_change,AllVisu.changeto_nonull_date(input, when_end, i))

            if func.__name__ not in ['pycoa_date_plot', 'pycoa_plot', 'pycoa_menu_plat', 'pycoa_spiral_plot','pycoa_yearly_plot','pycoa_mpltdate_plot']:
                if len(input_field) > 1:
                    print(str(input_field) + ' is dim = ' + str(len(input_field)) + '. No effect with ' + func.__name__ + '! Take the first input: ' + input_field[0])
                input_field = input_field[0]

            if when_end_change != when_end:
                when_end = when_end_change

            self.when_beg = when_beg
            self.when_end = when_end
            input = input.loc[(input['date'] >=  self.when_beg) & (input['date'] <=  self.when_end)]

            title_temporal = ' (' + 'between ' + when_beg.strftime('%d/%m/%Y') + ' and ' + when_end.strftime('%d/%m/%Y') + ')'
            if func.__name__ not in ['pycoa_date_plot', 'pycoa_plot', 'pycoa_menu_plat', 'pycoa_spiral_plot','pycoa_yearly_plot']:
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
                copyright = '©pycoa.fr ' + copyright + title_temporal
            else:
                copyright = '©pycoa.fr data from: {}'.format(self.database_name)+' '+title_temporal
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

    def set_tile(self,tile):
        if tile in list(self.dicovisuargs['tile']):
            self.tile = tile
        else:
            raise CoaTypeError('Don\'t know the tile you want. So far:' + str(list(self.dicovisuargs['tile'])))

    def setkwargsfront(self,kw):
        kwargs_test(kw, list(self.dicovisuargs.keys())+list(self.dicofigureargs.keys()), 'Error with this resquest (not available in setvisu)')
        self.dicokfront = kw

    def getkwargsfront(self):
        return self.dicokfront

    ''' FIGURE COMMUN FOR ALL Bokeh Figure'''
    def standardfig(self, **kwargs):
        """
         Create a standard Bokeh figure, with pycoa.fr copyright, used in all the bokeh charts
         """
        copyright = kwargs.get('copyright',self.dicofigureargs['copyright'])
        plot_width = kwargs.get('plot_width',self.dicofigureargs['plot_width'])
        plot_height = kwargs.get('plot_height',self.dicofigureargs['plot_height'])
        copyright = kwargs.get('copyright',self.dicofigureargs['copyright'])

        citation = Label(x=0.65 * plot_width - len(copyright), y=0.01 *plot_height,
                                          x_units='screen', y_units='screen',
                                          text_font_size='1.5vh', background_fill_color='white', background_fill_alpha=.75,
                                          text=copyright)

        fig = figure(plot_width=plot_width,plot_height=plot_height, tools=['save', 'box_zoom,reset'], toolbar_location="right")
        #fig.add_layout(citation)
        fig.add_layout(Title(text=self.uptitle, text_font_size="10pt"), 'above')
        if 'innerdecomap' not in inspect.stack()[1].function:
            fig.add_layout(Title(text=self.subtitle, text_font_size="8pt", text_font_style="italic"), 'below')
        return fig

    def get_listfigures(self):
        return  self.listfigs

    def set_listfigures(self,fig):
            if not isinstance(fig,list):
                fig = [fig]
            self.listfigs = fig

    @decowrapper
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
            col=[i for i in list(input.columns) if i not in ['clustername','where','codelocation']]
            col.insert(0,'clustername')
            input = input[col]
            input=input.set_index('clustername')
        else:
           input = input.drop(columns='clustername')
           input=input.set_index('where')

        return input.to_html(escape=False,formatters=dict(resume=path_to_image_html))

    ''' DECORATORS FOR PLOT: DATE, VERSUS, SCROLLINGMENU '''
    def decoplot(func):
        """
        decorator for plot purpose
        """
        @wraps(func)
        def inner_plot(self ,**kwargs):
            input = kwargs.get('input')
            input_field = [kwargs.get('input_field')]
            if isinstance(input_field[0],list):
                input_field = input_field[0]
            typeofplot = kwargs.get('typeofplot',self.dicochartargs['typeofplot'][0])
            if 'where' in input.columns:
                location_ordered_byvalues = list(
                    input.loc[input.date == self.when_end].sort_values(by=input_field, ascending=False)['clustername'].unique())
                input = input.copy()  # needed to avoid warning
                #input[inputtmp['clustername']] = pd.Categorical(input.clustername,
                #                                        categories=location_ordered_byvalues, ordered=True)
                #print("------------>>>input.clustername.unique()",input.clustername.unique(),input.clustername.isna().any())
                #input.loc[:,'clustername']
                input['clustername']  = pd.Categorical(input.clustername,
                                                       categories=location_ordered_byvalues, ordered=True)
                input = input.sort_values(by=['clustername', 'date']).reset_index(drop = True)
                if func.__name__ != 'pycoa_menu_plat' :
                    if len(location_ordered_byvalues) >= MAXCOUNTRIESDISPLAYED:
                        input = input.loc[input.clustername.isin(location_ordered_byvalues[:MAXCOUNTRIESDISPLAYED])]
                list_max = []
                for i in input_field:
                    list_max.append(max(input.loc[input.clustername.isin(location_ordered_byvalues)][i]))

                if len([x for x in list_max if not np.isnan(x)]) > 0:
                    amplitude = (np.nanmax(list_max) - np.nanmin(list_max))
                    if amplitude > 10 ** 4:
                        self.ax_type.reverse()
                if func.__name__ == 'pycoa_menu_plat' :
                    if isinstance(input_field,list):
                        if len(input_field) > 1:
                            print(str(input_field) + ' is dim = ' + str(len(input_field)) + '. No effect with ' + func.__name__ + '! Take the first input: ' + input_field[0])
                        input_field = input_field[0]
                    if self.dbld[self.database_name][1] == 'nation' and self.dbld[self.database_name][0] != 'WW':
                        func.__name__ = 'pycoa_date_plot'
                kwargs['input'] = input.reset_index(drop=True)
            return func(self, **kwargs)
        return inner_plot

    ''' PLOT VERSUS '''
    @decowrapper
    @decoplot
    def pycoa_plot(self,**kwargs):
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

        if len(input_field) != 2:
            raise CoaTypeError('Two variables are needed to plot a versus chart ... ')
        panels = []
        cases_custom = AllVisu.rollerJS()
        if self.get_listfigures():
            self.set_listfigures([])
        listfigs=[]
        for axis_type in self.ax_type:
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
    @decowrapper
    @decoplot
    def pycoa_date_plot(self,**kwargs):
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

        mode = kwargs.get('mode',list(self.dicovisuargs['mode'])[0])
        guideline = kwargs.get('guideline',list(self.dicovisuargs['guideline'])[0])

        panels = []
        listfigs = []
        cases_custom = AllVisu.rollerJS()
        if 'which' in kwargs and not isinstance(kwargs['which'],list):
            kwargs['which'] = [kwargs['which']]
            input_field = kwargs['which']

        if isinstance(input['rolloverdisplay'].iloc[0],list):
            input['rolloverdisplay'] = input['clustername']
        for axis_type in self.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type, x_axis_type = 'datetime',**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
            lcolors = iter(self.lcolors)
            line_style = ['solid', 'dashed', 'dotted', 'dotdash','dashdot']
            maxou,minou=0,0
            tooltips=[]

            for val in input_field:
                for loc in list(input.clustername.unique()):
                    input_filter = input.loc[input.clustername == loc].reset_index(drop = True)
                    src = ColumnDataSource(input_filter)
                    leg = input_filter.clustername[0]
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
    @decowrapper
    @decoplot
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

        cases_custom = AllVisu.rollerJS()
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
    @decowrapper
    @decoplot
    def pycoa_menu_plat(self, **kwargs):
        '''
        -----------------
        Create a date plot, with a scrolling menu location, according to arguments.
        See help(pycoa_menu_plat).
        Keyword arguments
        -----------------
        len(location) > 2
        - input = None : if None take first element. A DataFrame with a Pycoa struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|codelocation|clustername|permanentdisplay|rolloverdisplay|
        - input_field = if None take second element could be a list
        - plot_heigh= width_height_default[1]
        - plot_width = width_height_default[0]
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
        guideline = kwargs.get('guideline',self.dicovisuargs['guideline'][0])
        mode = kwargs.get('guideline',self.dicovisuargs['mode'][0])
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

        cases_custom = AllVisu.rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               mode = mode, point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in self.ax_type:
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
    @decowrapper
    @decoplot
    def pycoa_yearly_plot(self,**kwargs):
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
        guideline = kwargs.get('guideline',self.dicovisuargs['guideline'][0])
        mode = kwargs.get('mode',self.dicovisuargs['mode'][0])

        if len(input.clustername.unique()) > 1 :
            CoaWarning('Can only display yearly plot for ONE location. I took the first one:'+ input.clustername[0])
        if isinstance(input_field[0],list):
            input_field = input_field[0][0]
            CoaWarning('Can only display yearly plot for ONE which value. I took the first one:'+ input_field)

        input = input.loc[input.clustername == input.clustername[0]].copy()

        panels = []
        listfigs = []
        cases_custom = AllVisu.rollerJS()
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
        for axis_type in self.ax_type:
            standardfig = self.standardfig( y_axis_type = axis_type,**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
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

            orientation = kwargs.get('orientation', list(self.dicovisuargs['orientation'])[0])
            dateslider = kwargs.get('dateslider',list(self.dicovisuargs['dateslider'])[0])
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
                if dateslider:
                    dateslider = DateSlider(title = "Date: ", start = started, end = ended,
                                         value = started, step=24 * 60 * 60 * 1000, orientation = orientation)
                    #wanted_date = dateslider.value_as_datetime.date()

                #if func.__name__ == 'pycoa_mapfolium' or func.__name__ == 'pycoa_map' or func.__name__ == 'innerdecomap' or func.__name__ == 'innerdecopycoageo':
                if func.__name__ in ['pycoa_mapfolium','pycoa_map','pycoageo' ,'pycoa_pimpmap','pycoa_mpltmap']:
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
                    '''
                    if self.iso3country in ['FRA','USA']:
                        self.geo = copy.deepcopy(self.geo)
                        d = self.geo._list_translation
                        if func.__name__ != 'pycoa_mapfolium':
                            if any(i in list(geopdwd.codelocation.unique()) for i in d.keys()) \
                            or any(True for i in d.keys() if ''.join(list(geopdwd.codelocation.unique())).find(i)!=-1):
                                if maplabel:
                                    if 'dense' in maplabel:
                                        self.geo.set_dense_geometry()
                                    elif 'exploded' in maplabel:
                                        self.geo.set_exploded_geometry()
                                    else:
                                        print('don\'t know ')
                                else:
                                    if any([len(i)==3 for i in geopdwd.codelocation.unique()]):
                                        self.geo.set_dense_geometry()
                            else:
                                self.geo.set_main_geometry()
                                d = {}
                            new_geo = geo.get_data()[['name_'+self.granularity,'geometry']]
                            new_geo = new_geo.rename(columns={'name_'+self.granularity:'where'})
                            new_geo = new_geo.set_index('where')['geometry'].to_dict()
                            geopdwd['geometry'] = geopdwd['where'].map(new_geo)
                    '''
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

    ''' VERTICAL HISTO '''
    @decowrapper
    @decohistomap
    def pycoa_histo(self, **kwargs):
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
            plot_width = kwargs.get('plot_width',self.dicofigureargs['plot_width'])
            plot_height = kwargs.get('plot_height',self.dicofigureargs['plot_height'])

            geopdwd['cases'] = geopdwd[input_field]
            geopdwd_filter = geopdwd.loc[geopdwd.date == self.when_end]
            geopdwd_filter = geopdwd_filter.reset_index(drop = True)
            geopdwd_filter['cases'] = geopdwd_filter[input_field]
            dateslider = kwargs.get('dateslider',self.dicovisuargs['dateslider'][0])
            maplabel = kwargs.get('maplabel',self.dicovisuargs['maplabel'][0])
            my_date = geopdwd.date.unique()
            dico_utc = {i: DateSlider(value=i).value for i in my_date}
            geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
            #geopdwd = geopdwd.drop_duplicates(["date", "codelocation","clustername"])#for sumall avoid duplicate
            #geopdwd_filter = geopdwd_filter.drop_duplicates(["date", "codelocation","clustername"])
            geopdwd = geopdwd.drop_duplicates(["date","clustername"])#for sumall avoid duplicate
            geopdwd_filter = geopdwd_filter.drop_duplicates(["date","clustername"])
            locunique = geopdwd_filter.clustername.unique()#geopdwd_filtered['where'].unique()
            geopdwd_filter = geopdwd_filter.copy()
            nmaxdisplayed = MAXCOUNTRIESDISPLAYED
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
                    geopdwd_filter_other['codelocation'] = 'others'
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
                ymax = self.dicofigureargs['plot_height']

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
            if func.__name__  in ['pycoa_pie','pycoa_mpltpie']  :
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
            min_value_gt0 = min(input_filter[input_filter['cases'] >= 0]['cases'])
            panels = []
            kwargs.pop('dateslider')
            for axis_type in self.ax_type:
                standardfig = self.standardfig( x_axis_type = axis_type,  x_range = (1.05*min_value, 1.05 * max_value),**kwargs)
                if maplabel and 'label%' in maplabel:
                    standardfig.x_range = Range1d(0.01, 1.2 * max_value*100)
                    standardfig.xaxis.axis_label = 'percentage(%)'
                    standardfig.xaxis.formatter = BasicTickFormatter(use_scientific=False)
                else:
                    standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
                    standardfig.x_range = Range1d(max_value/100., 1.2 * max_value)
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
                                standardfig.x_range = Range1d(max_value/100., 50 * max_value)

                            srcfiltered.data['left'] = [min(srcfiltered.data['right'])/100.] * len(srcfiltered.data['right'])

                if func.__name__ == 'pycoa_pie':
                    if not input_filter[input_filter[input_field] < 0.].empty:
                        raise CoaKeyError('Some values are negative, can\'t display a Pie chart, try histo by location')
                    standardfig.plot_width = plot_width
                    standardfig.plot_height = plot_height

                if dateslider:
                    dateslider.width = int(0.8*plot_width)
                    callback = CustomJS(args = dict(source = source,
                                                  source_filter = srcfiltered,
                                                  dateslider = dateslider,
                                                  ylabel = standardfig.yaxis[0],
                                                  title = standardfig.title,
                                                  x_range = standardfig.x_range,
                                                  x_axis_type = axis_type,
                                                  figure = standardfig),
                            code = """
                            var date_slide = dateslider.value;
                            var dates = source.data['date_utc'];
                            var val = source.data['cases'];
                            var loc = source.data['clustername'];
                            //var loc = source.data['where'];
                            var subregion = source.data['name_subregion'];
                            var codeloc = source.data['codelocation'];
                            var colors = source.data['colors'];
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
                            source_filter.data['colors'] = ordercolors;

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
                                labeldic[parseInt(ymax*(n-i)/n)] = orderloc[i];//ordercodeloc[i];

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
                            source_filter.data['permanentdisplay'] = orderloc;//ordercodeloc;
                            source_filter.data['textdisplayed'] = textdisplayed;
                            source_filter.data['textdisplayed2'] = textdisplayed2;
                            var maxx = Math.max.apply(Math, right_quad);
                            var minx = Math.min.apply(Math, left_quad);

                            ylabel.major_label_overrides = labeldic;
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
                            //title.text = tmp + dmy+")";

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

                cases_custom = AllVisu.rollerJS()
                if min(srcfiltered.data['cases'])<0.01:
                    tooltips=[('where', '@rolloverdisplay'), (input_field, '@cases'), ]
                else:
                    tooltips=[('where', '@rolloverdisplay'), (input_field, '@cases{0,0.0}'), ],
                if isinstance(tooltips,tuple):
                    tooltips = tooltips[0]
                if func.__name__ == 'pycoa_pie' :
                    standardfig.add_tools(HoverTool(
                        tooltips = tooltips,
                        formatters = {'where': 'printf', '@{' + 'cases' + '}': cases_custom, '%':'printf'},
                        point_policy = "snap_to_data"))  # ,PanTool())
                else:
                    standardfig.add_tools(HoverTool(
                        tooltips = tooltips,
                        formatters = {'where': 'printf', '@{' + 'cases' + '}': cases_custom, },
                        point_policy = "snap_to_data"))  # ,PanTool())
                panel = Panel(child = standardfig, title = axis_type)
                panels.append(panel)
            kwargs['srcfiltered']=srcfiltered
            kwargs['panels']=panels
            kwargs['dateslider']=dateslider
            kwargs['toggl']=toggl
            kwargs['geopdwd']=geopdwd
            kwargs['geopdwd_filter']=geopdwd_filter
            return func(self,**kwargs)
        return inner_decohistopie

    ''' VERTICAL HISTO '''
    @decowrapper
    @decohistomap
    @decohistopie
    def pycoa_horizonhisto(self, **kwargs):
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
                raise CoaError("Locale setting problem. Please contact support@pycoa.fr")

        df['textdisplayed2'] =  ['      '+str(round(100*i,1))+'%' for i in df['percentage']]
        df.loc[df['diff'] <= np.pi/20,'textdisplayed']=''
        df.loc[df['diff'] <= np.pi/20,'textdisplayed2']=''
        return df

    @decowrapper
    @decohistomap
    @decohistopie
    def pycoa_pie(self, **kwargs):
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

    ''' MAP FOLIUM '''
    @decowrapper
    @decohistomap
    def pycoa_mapfolium(self, **kwargs):
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
        title=kwargs.get('title')
        tile = AllVisu.convert_tile(kwargs.get('tile',self.dicovisuargs['tile']), 'folium')
        maplabel = kwargs.get('maplabel',self.dicovisuargs['maplabel'])
        plot_width = kwargs.get('plot_width',self.dicofigureargs['plot_width'])
        plot_height = kwargs.get('plot_height',self.dicofigureargs['plot_height'])
        geopdwd = kwargs.get('geopdwd')
        input_field = kwargs.get('input_field')

        geopdwd['cases'] = geopdwd[input_field]
        geopdwd_filtered = geopdwd.loc[geopdwd.date == self.when_end]
        geopdwd_filtered = geopdwd_filtered.reset_index(drop = True)
        geopdwd_filtered['cases'] = geopdwd_filtered[input_field]
        my_date = geopdwd.date.unique()
        dico_utc = {i: DateSlider(value=i).value for i in my_date}
        geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
        #geopdwd = geopdwd.drop_duplicates(["date", "codelocation","clustername"])#for sumall avoid duplicate
        #geopdwd_filtered = geopdwd_filtered.sort_values(by='cases', ascending = False).reset_index()
        #locunique = geopdwd_filtered.clustername.unique()#geopdwd_filtered['where'].unique()
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
        min_col, max_col = AllVisu.min_max_range(np.nanmin(geopdwd_filtered[input_field]),
                                                     np.nanmax(geopdwd_filtered[input_field]))
        min_col_non0 = (np.nanmin(geopdwd_filtered.loc[geopdwd_filtered['cases']>0.]['cases']))

        invViridis256 = Viridis256[::-1]
        if maplabel and 'log' in maplabel:
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

        map_dict = geopdwd_filtered.set_index('where')[input_field].to_dict()
        if np.nanmin(geopdwd_filtered[input_field]) == np.nanmax(geopdwd_filtered[input_field]):
            map_dict['FakeCountry'] = 0.

        if maplabel and 'log' in maplabel:
            color_scale =  branca.colormap.LinearColormap(color_mapper.palette).to_step(data=list(geopdwd_filtered['cases']),n=10,method='log')
        else:
            color_scale = LinearColormap(color_mapper.palette, vmin=min(map_dict.values()), vmax=max(map_dict.values()))

        def get_color(feature):
            value = map_dict.get(feature['properties']['where'])
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
                                                   aliases=['where' + ':', input_field + ":"],
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

    ''' RETURN GEOMETRY, LOCATIO + CASES '''
    def decomap(func):
        @wraps(func)
        def innerdecomap(self,**kwargs):
            geopdwd_filtered=kwargs.get('geopdwd_filtered')
            geopdwd=kwargs.get('geopdwd')
            title = kwargs.get('title',self.dicovisuargs['title'])
            maplabel = kwargs.get('maplabel',list(self.dicovisuargs['maplabel'])[0])
            tile = kwargs.get('tile',list(self.dicovisuargs['tile'])[0])
            tile = AllVisu.convert_tile(tile, 'bokeh')
            uniqloc = list(geopdwd_filtered.clustername.unique())
            dfLabel = pd.DataFrame()
            sourcemaplabel = ColumnDataSource(dfLabel)
            if maplabel or func.__name__ in ['pycoa_pimpmap','pycoa_map','pycoa_mapfolium']:
                locsum = geopdwd_filtered.clustername.unique()
                numberpercluster = geopdwd_filtered['clustername'].value_counts().to_dict()
                sumgeo = geopdwd_filtered.copy()
                if self.pycoageopandas == True:
                    sumgeo = sumgeo.to_crs(3035)
                else:
                    sumgeo['geometry'] = sumgeo['geometry'].buffer(0.001) #needed with geopandas 0.10.2

                sumgeo.loc[:,'centroidx'] = sumgeo['geometry'].centroid.x
                sumgeo.loc[:,'centroidy'] = sumgeo['geometry'].centroid.y
                clust=sumgeo.clustername.unique()

                centrosx = [sumgeo.loc[sumgeo.clustername==i]['centroidx'].mean() for i in clust]
                centrosy = [sumgeo.loc[sumgeo.clustername==i]['centroidy'].mean() for i in clust]
                sumgeo = sumgeo.dissolve(by='clustername', aggfunc='sum').reset_index()
                sumgeo['nb'] = sumgeo['clustername'].map(numberpercluster)
                cases = sumgeo['cases']/sumgeo['nb']

                dfLabel=pd.DataFrame({'clustername':sumgeo.clustername,'centroidx':centrosx,'centroidy':centrosy,'cases':cases,'geometry':sumgeo['geometry']})

                if maplabel:
                    if 'spark' in maplabel:
                        sparkos = {i: AllVisu.sparkline(geopdwd.loc[ (geopdwd.clustername==i) &
                                    (geopdwd.date >= self.when_beg) &
                                    (geopdwd.date <= self.when_end)].sort_values(by='date')['cases']) for i in locsum }
                        dfpimp = pd.DataFrame(list(sparkos.items()), columns=['clustername', 'pimpmap'])
                        dfLabel=pd.merge(dfLabel,dfpimp,on=['clustername'],how="inner")
                    if 'spiral' in maplabel:
                        sparkos = {i: AllVisu.spiral(geopdwd.loc[ (geopdwd.clustername==i) &
                                    (geopdwd.date >= self.when_beg) &
                                    (geopdwd.date <= self.when_end)].sort_values(by='date')[['date','cases','clustername']]) for i in locsum }
                        dfpimp = pd.DataFrame(list(sparkos.items()), columns=['clustername', 'pimpmap'])
                        dfLabel=pd.merge(dfLabel,dfpimp,on=['clustername'],how="inner")

                dfLabel['cases'] = dfLabel['cases'].round(2)
                # Converting links to html tags
                if maplabel and 'label%' in maplabel:
                    dfLabel['cases'] = [str(round(float(i*100),2))+'%' for i in dfLabel['cases']]
                else:
                    dfLabel['cases']=[str(i) for i in dfLabel['cases']]
                sourcemaplabel = ColumnDataSource(dfLabel.drop(columns='geometry'))
            minx, miny, maxx, maxy =  geopdwd_filtered.total_bounds #self.boundary


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

            geopdwd_filtered = geopdwd_filtered[['cases','geometry','where','clustername','codelocation','rolloverdisplay']]
            if not dfLabel.empty:
                geopdwd_filtered = geopdwd_filtered.drop(columns = 'geometry')
                geopdwd_filtered = pd.merge(geopdwd_filtered, dfLabel[['clustername','geometry']], on = 'clustername')
                geopdwd_filtered = geopdwd_filtered.drop_duplicates(subset = ['clustername'])
            if self.dbld[self.database_name][0] == 'BEL' :
                reorder = list(geopdwd_filtered['where'].unique())
                geopdwd_filtered = geopdwd_filtered.set_index('where')
                geopdwd_filtered = geopdwd_filtered.reindex(index = reorder)
                geopdwd_filtered = geopdwd_filtered.reset_index()

            if self.dbld[self.database_name][0] == 'GBR' :
                geopdwd = geopdwd.loc[~geopdwd.cases.isnull()]
                geopdwd_filtered  = geopdwd_filtered.loc[~geopdwd_filtered.cases.isnull()]
            kwargs['geopdwd']=geopdwd
            kwargs['geopdwd_filtered']= geopdwd_filtered
            kwargs['sourcemaplabel']=sourcemaplabel
            kwargs['standardfig']=standardfig
            return func(self,**kwargs)
        return innerdecomap

    ''' MAP BOKEH '''
    @decowrapper
    @decohistomap
    @decopycoageo
    @decomap
    def pycoa_map(self,**kwargs):
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
        dateslider = kwargs.get('dateslider',list(self.dicovisuargs['dateslider'])[0])
        maplabel = kwargs.get('maplabel',list(self.dicovisuargs['maplabel'])[0])
        min_col, max_col, min_col_non0 = 3*[0.]
        try:
            if dateslider:
                min_col, max_col = AllVisu.min_max_range(np.nanmin(geopdwd['cases']),
                                                         np.nanmax(geopdwd['cases']))
                min_col_non0 = (np.nanmin(geopdwd.loc[geopdwd['cases']>0.]['cases']))
            else:
                min_col, max_col = AllVisu.min_max_range(np.nanmin(geopdwd_filtered['cases']),
                                                         np.nanmax(geopdwd_filtered['cases']))
                min_col_non0 = (np.nanmin(geopdwd_filtered.loc[geopdwd_filtered['cases']>0.]['cases']))
        except ValueError:  #raised if `geopdwd_filtered` is empty.
            pass
        #min_col, max_col = np.nanmin(geopdwd_filtered['cases']),np.nanmax(geopdwd_filtered['cases'])

        json_data = json.dumps(json.loads(geopdwd_filtered.to_json()))
        geopdwd_filtered = GeoJSONDataSource(geojson=json_data)

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

        standardfig.add_layout(color_bar, 'below')
        standardfig.add_layout(Title(text=self.subtitle, text_font_size="8pt", text_font_style="italic"), 'below')
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
        self.pycoageopandas = False
        return standardfig

    ''' PIMPMAP BOKEH '''
    @decowrapper
    @decohistomap
    @decopycoageo
    @decomap
    def pycoa_pimpmap(self,**kwargs):
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

        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None

        min_col, max_col = AllVisu.min_max_range(np.nanmin(geopdwd_filtered['cases']),
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
    def get_tile(self):
        return self.tile
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

    '''
        MATPLOTLIB chart drawing methods ...
    '''

    @decowrapper
    @decoplot
    def pycoa_mpltdate_plot(self,**kwargs):
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        fig, ax = plt.subplots(1, 1,figsize=(12, 8))

        if not isinstance(input_field,list):
            input_field=[input_field]

        loc = input['clustername'].unique()
        for val in input_field:
            df = pd.pivot_table(input,index='date', columns='clustername', values=val)
            for col in loc:
                ax=plt.plot(df.index, df[col])
                plt.legend(loc+val)
        plt.title(title)
        return fig

    @decowrapper
    @decoplot
    def pycoa_mpltyearly_plot(self,**kwargs):
        '''
         matplotlib date yearly plot chart
         Max display defined by MAXCOUNTRIESDISPLAYED
        '''
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        input['date']=pd.to_datetime(input["date"])
        title = kwargs.get('title')
        #drop bissextile fine tuning in needed in the future

        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)

        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        fig, ax = plt.subplots(1, 1,figsize=(12, 8))
        loc = input['clustername'][0]
        d = input.allyears.unique()
        for i in d:
            df = pd.pivot_table(input.loc[input.allyears==i],index='dayofyear', columns='clustername', values=input_field)
            ax = plt.plot(df.index, df[loc])
        plt.legend(d)
        plt.title(title)
        return fig


    @decowrapper
    @decohistomap
    @decohistopie
    def pycoa_mpltpie(self,**kwargs):
        '''
         matplotlib pie chart
         Max display defined by MAXCOUNTRIESDISPLAYED
        '''
        geopdwd_filter = kwargs.get('geopdwd_filter')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        geopdwd_filter = geopdwd_filter.sort_values(by=[input_field]).set_index('clustername')
        fig, ax = plt.subplots(1, 1,figsize=(12, 8))
        ax = geopdwd_filter.plot(kind="pie",y=input_field, autopct='%1.1f%%', legend=True,
        title=input_field, ylabel=input_field, labeldistance=None)
        ax.legend(bbox_to_anchor=(1, 1.02), loc='upper left')
        ax.set_title(title)
        return fig

    @decowrapper
    @decohistomap
    @decohistopie
    def pycoa_mplthorizontalhisto(self,**kwargs):
        '''
        matplotlib horizon histo
        '''
        import matplotlib as mpl
        from matplotlib.cm import get_cmap
        geopdwd_filter = kwargs.get('geopdwd_filter')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        geopdwd_filter = geopdwd_filter.sort_values(by=[input_field])
        fig, ax = plt.subplots(1, 1,figsize=(12, 8))
        cmap = plt.get_cmap('Paired')
        bar = ax.barh(geopdwd_filter['clustername'], geopdwd_filter[input_field],color=cmap.colors)
        ax.set_title(title)
        return fig

    @decowrapper
    def pycoa_mplthisto(self,**kwargs):
        '''
        matplotlib horizon histo
        '''
        import matplotlib as mpl
        from matplotlib.cm import get_cmap
        input = kwargs.get('input')
        input_field = kwargs.get('input_field')
        title = kwargs.get('title')
        #fig, ax = plt.subplots(1, 1,figsize=(12, 8))
        fig, ax = plt.subplots(1, 1,figsize=(12, 8))
        input = input.loc[input.date==input.date.max()][:MAXCOUNTRIESDISPLAYED]
        loc = input['where'].unique()[:MAXCOUNTRIESDISPLAYED]
        bins=len(input['where'])+1
        input= pd.pivot_table(input,index='date', columns='where', values=input_field)
        fig = input.plot.hist(bins=bins, alpha=0.5,title = title)
        return fig

    @decowrapper
    @decohistomap
    def pycoa_mpltmap(self,**kwargs):
        '''
         matplotlib map display
        '''
        from matplotlib.colors import Normalize
        from matplotlib import cm
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        fig, ax = plt.subplots(1, 1,figsize=(8, 12))
        title = kwargs.get('title')
        plt.axis('off')
        geopdwd = kwargs.get('geopdwd')
        input_field = kwargs.get('input_field')
        #geopdwd = pd.merge(geopdwd, self.kindgeo, on='where')
        geopdwd = gpd.GeoDataFrame(geopdwd.loc[geopdwd.date==geopdwd.date.max()])
        ax = geopdwd.plot(column=input_field, ax=ax,legend=True,
                                legend_kwds={'label': input_field,
                                'orientation': "horizontal","pad": 0.001})
        ax.set_title(title)
        return fig

    ######SEABORN#########
    ######################
    def decoplotseaborn(func):
        """
        decorator for seaborn plot
        """
        @wraps(func)
        def inner_plot(self, **kwargs):
            input = kwargs.get('input')
            input_field = kwargs.get('input_field')
            title = f"Graphique de {input_field}"
            if 'where' in kwargs:
                title += f" - {kwargs.get('where')}"
            kwargs['title'] = title

            top_countries = (input.groupby('where')[input_field].sum()
                         .nlargest(MAXCOUNTRIESDISPLAYED).index.tolist())
            filtered_input = input[input['where'].isin(top_countries)]

            kwargs['filtered_input'] = filtered_input

            return func(self, **kwargs)
        return inner_plot

    def decohistseaborn(func):
        """
        decorator for seaborn histogram
        """
        @wraps(func)
        def inner_hist(self,**kwargs):
            filtered_input = kwargs.get('filtered_input')
            input_field = kwargs.get('input_field')

            filtered_input = (filtered_input.sort_values('date')
                  .drop_duplicates('where', keep='last')    #garde le last en terme de date
                  .drop_duplicates(['where', input_field])  #quand une ligne avec where et input est pareil on drop
                  .sort_values(by=input_field, ascending=False) #trier
                  .reset_index(drop=True))

            kwargs['filtered_input'] = filtered_input
            return func(self, **kwargs)
        return inner_hist


    ######SEABORN PLOT#########
    @decowrapper
    @decoplotseaborn
    def pycoa_date_plot_seaborn(self, **kwargs):
        """
        Create a seaborn line plot with date on x-axis and input_field on y-axis.
        """
        input = kwargs['input']
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')
        # Créer le graphique
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=filtered_input, x='date', y=input_field, hue='where')
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel(input_field)
        plt.xticks(rotation=45)
        #permet de placer la légend 4% à gauche
        plt.legend(bbox_to_anchor=(1.04, 1))
        plt.show()

    ######################
    ######SEABORN HIST VERTICALE#########

    ###NOT USED####
    @decowrapper
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

    ###BY_VALUE###
    @decowrapper
    @decoplotseaborn
    @decohistseaborn
    def pycoa_hist_seaborn_value(self, **kwargs):
        """
        Create a seaborn vertical histogram where the x-axis represents a numerical field.
        """
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.histplot(data=filtered_input, x=input_field, bins=24, color='blue', kde=True)
        plt.title(title)
        plt.xlabel(input_field)
        plt.ylabel('Fréquence')
        plt.show()


    ######SEABORN HIST HORIZONTALE#########
    @decowrapper
    @decoplotseaborn
    @decohistseaborn
    def pycoa_hist_seaborn_hori(self, **kwargs):
        """
        Create a seaborn horizontal histogram with input_field on x-axis.
        """
        filtered_input = kwargs['filtered_input']
        input_field = kwargs['input_field']
        title = kwargs.get('title')

        # Créer le graphique
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.barplot(data=filtered_input, x=input_field, y='where', palette="viridis", ci=None)
        plt.title(title)
        plt.xlabel(input_field)
        plt.ylabel('')
        plt.xticks(rotation=45)
        plt.show()

    ######SEABORN BOXPLOT#########
    @decowrapper
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
    @decowrapper
    @decoplotseaborn
    def pycoa_heatmap_seaborn(self, **kwargs):
        """
        Create a seaborn heatmap
        """
        input_field = kwargs['input_field']
        # Convertir la colonne 'date' en datetime si nécessaire
        if not pd.api.types.is_datetime64_any_dtype(input['date']):
            input['date'] = pd.to_datetime(input['date'])

        df=input
        df.date=pd.to_datetime(df.date)
        a=df.groupby(pd.Grouper(key='date', freq='1M'))['daily'].sum()
        a=a.reset_index()

        # On inclut que les premiers 24 pays uniques
        # top_locations = input['where'].unique()[:MAXCOUNTRIESDISPLAYED]
        # filtered_input = input[input['where'].isin(top_locations)]

        a['month'] = [m.month for m in a['date']]
        a['year'] = [m.year for m in a['date']]

        data_pivot = a.pivot_table(index='month', columns='year', values='daily')

        total = data_pivot.sum().sum()
        # Créer une nouvelle figure
        plt.figure(figsize=(15, 10))

        # Créer une heatmap à partir du tableau croisé dynamique
        sns.heatmap(data_pivot, annot=True, fmt=".1f", linewidths=.5, cmap='plasma')

        # Ajouter un titre
        plt.title(f'Heatmap of {input_field.replace("_", " ").capitalize()} by Month and Year')
        plt.xlabel('Year')
        plt.ylabel('Month')

        # Afficher le total en dehors du graphique
        plt.text(0, data_pivot.shape[0] + 1, f'Total: {total}', fontsize=12)
        # Afficher la heatmap
        plt.show()
