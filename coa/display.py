# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april-november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.display

About :
-------

An interface module to easily plot pycoa data with bokeh

"""

import random
import math
import pandas as pd
import geopandas as gpd

import datetime
from datetime import datetime as dt
from collections import defaultdict
from coa.error import *
import bokeh
from bokeh.io import show, output_notebook
from bokeh.models import ColumnDataSource, TableColumn, DataTable,ColorBar, HoverTool, Legend
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import brewer
from bokeh.layouts import row, column, gridplot
from bokeh.models import CustomJS, Slider, Select, Plot, \
    Button, LinearAxis, Range1d, DatetimeTickFormatter
from bokeh.models import CheckboxGroup, RadioGroup, Toggle, RadioGroup
from bokeh.palettes import Paired12
from bokeh.models.widgets import Tabs, Panel
from bokeh.models import Label, LabelSet
from bokeh.models import ColumnDataSource, Grid, Line, LinearAxis, Plot
from bokeh.models import DataRange1d
from bokeh.models import LogScale
from bokeh.models import PrintfTickFormatter
from bokeh.models import PolyDrawTool
from bokeh.io import export_png, export_svgs

import bokeh.palettes
import itertools
import sys

import coa.geo as coge
from coa.tools import info,verb,check_valid_date

from pyproj import CRS
#import plotly.express as px
#import plotly.graph_objects as go
#from branca.colormap import LinearColormap
import branca.colormap
from branca.element import Figure
import folium
import json
from geopy.geocoders import Nominatim
import altair as alt
import numpy as np
from shapely.ops import unary_union
import io
from PIL import Image

width_height_default = [500,400]
class CocoDisplay():
    def __init__(self,db=None):
        verb("Init of CocoDisplay()")
        self.colors = itertools.cycle(Paired12)
        self.coco_circle = []
        self.coco_line = []
        self.base_fig = None
        self.hover_tool = None
        self.increment = 1
        if db == None:
            self.info = coge.GeoInfo()
        else:
            self.info = coge.GeoInfo(db.geo)

    def standardfig(self,title=None, axis_type='linear',x_axis_type='datetime'):
         return figure(title=title,plot_width=400, plot_height=300,y_axis_type=axis_type,x_axis_type=x_axis_type,
         tools=['save','box_zoom,box_select,crosshair,reset'])

    @staticmethod
    def pycoa_date_plot(babepandas, input_names_data = None,title = None, width_height = None):
        """Create a Bokeh date chart from pandas input (x axis is a date format)

        Keyword arguments
        -----------------
        - babepandas : pandas where the data is considered
        - input_names_data : variable from pandas data.
          * variable or list of variables available in babepandas (i.e available in the babepandas columns name  )
          * If pandas is produced from pycoa get_stat method 'diff' or 'cumul' variable are available
        - title: title for the figure , no title by default
        - width_height : width and height of the figure,  default [400,300]

        Note
        -----------------
        HoverTool is available it returns location, date and value
        """

        dict_filter_data = defaultdict(list)
        tooltips='Date: @date{%F} <br>  $name: @$name'

        if type(input_names_data) is None.__class__:
            print("Need variable to plot", file=sys.stderr)

        if not isinstance(input_names_data, list):
           input_names_data=[input_names_data]

        if 'where' in babepandas.columns:
            babepandas = babepandas.rename(columns={'where':'location'})
        if 'location' in babepandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = babepandas['location'].unique()
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]
            for i in input_names_data:
                dict_filter_data[i] =  \
                    dict(babepandas.loc[babepandas['location'].isin(loc)].groupby('location').__iter__())
                for j in range(len(loc)):
                    dict_filter_data[i][shorten_loc[j]] = dict_filter_data[i].pop(loc[j])

        else:
            for i in input_names_data:
                dict_filter_data[i] = {i:babepandas}

        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})

        panels = []
        for axis_type in ["linear", "log"]:
            if width_height:
                plot_width  = width_height[0]
                plot_height = width_height[1]
            else :
                plot_width  = width_height_default[0]
                plot_height = width_height_default[1]
            standardfig = figure(plot_width=plot_width, plot_height=plot_height,y_axis_type=axis_type, x_axis_type='datetime',
            tools=['save','box_zoom,box_select,crosshair,reset'],toolbar_location="below")
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            if title:
                standardfig.title.text = title
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(Paired12)
            for i in input_names_data:
                p = [standardfig.line(x='date', y=i, source=ColumnDataSource(value),
                color=next(colors), line_width=3, legend_label=key,
                name=i,hover_line_width=4) for key,value in dict_filter_data[i].items()]

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig , title=axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "bottom_left"

        standardfig.xaxis.formatter = DatetimeTickFormatter(
        days=["%d %B %Y"], months=["%d %B %Y"], years=["%d %B %Y"])
        tabs = Tabs(tabs=panels)
        return tabs

    @staticmethod
    def min_max_range(a_min,a_max):
        """Return a cleverly rounded min and max giving raw min and raw max of data.
        Usefull for hist range and colormap
        """
        min_p=0
        max_p=0
        if a_min!=0:
            min_p=math.floor(math.log10(math.fabs(a_min)))   # power
        if a_max!=0:
            max_p=math.floor(math.log10(math.fabs(a_max)))

        p=max(min_p,max_p)

        if a_min!=0:
            min_r=math.floor(a_min/10**(p-1))*10**(p-1) # min range rounded
        else:
            min_r=0

        if a_max!=0:
            max_r=math.ceil(a_max/10**(p-1))*10**(p-1)

        if min_r==max_r:
            if min_r==0:
                min_r=-1
                max_r=1
                k=0
            elif max_r>0:
                k=0.1
            else:
                k=-0.1
            max_r=(1+k)*max_r
            min_r=(1-k)*min_r

        return (min_r,max_r)

    @staticmethod
    def pycoa_histo(babepandas, input_names_data = None, bins=None,title = None, width_height = None, date='last'):
        """Create a Bokeh histogram from a pandas input

        Keyword arguments
        -----------------
        babepandas : pandas consided
        input_names_data : variable from pandas data. If pandas is produced from pycoa get_stat method
        then 'diff' and 'cumul' can be also used
        title: title for the figure , no title by default
        width_height : as a list of width and height of the histo, default [500,400]
        bins : number of bins of the hitogram default 50
        date : - default 'last'
               Value at the last date (from database point of view) and for all the location defined in
               the pandas will be computed
               - date
               Value at date (from database point of view) and for all the location defined in the pandas
               will be computed
               - 'all'
               Value for all the date and for all the location will be computed
        Note
        -----------------
        HoverTool is available it returns position of the middle of the bin and the value. In the case where
        date='all' i.e all the date for all the location then location name is provided
        """

        dict_histo = defaultdict(list)

        if type(input_names_data) is None.__class__:
            print("Need variable to plot", file=sys.stderr)

        if 'where' in babepandas.columns:
            babepandas = babepandas.rename(columns={'where':'location'})
        if 'location' in babepandas.columns:
            tooltips='Value at around @middle_bin : @val'
            loc = babepandas['location'].unique()
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]

            if date == 'all':
                if bins:
                    bins = bins
                else:
                    bins = 50

                tooltips='Location: @location <br> Value at around @middle_bin : @val'
                for w in loc:
                    histo,edges = np.histogram((babepandas.loc[babepandas['location'] == w][input_names_data]),density=False, bins=bins)
                    dict_histo[w] = pd.DataFrame({'location':w,'val': histo,
                       'left': edges[:-1],
                       'right': edges[1:],
                       'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2)})
                for j in range(len(loc)):
                    dict_histo[shorten_loc[j]] = dict_histo.pop(loc[j])
            else:
               tooltips = 'Contributors : @contributors'
               if date == "last" :
                   when = babepandas['date'].max()
                   when = when.strftime('%m/%d/%y')
               else:
                   when = date
               
               val_per_country = defaultdict(list)
               for w in loc:
                   retrieved_at = babepandas.loc(babepandas['date'] == when)
                   if retrieved_at.empty:
                     raise CoaTypeError('Noting to retrieve at this date:', when)
                   else:
                       val = babepandas.loc[(babepandas['location'] == w) & (babepandas['date'] == when)][input_names_data].values
                   #val_per_country.append(val)
                   val_per_country[w]=val
               if type(when) != str:
                   when = when.strftime('%d-%m-%Y')
               l_data=list(val_per_country.values())

               # good nb of bins
               l_n=len(l_data)
               if bins:
                  bins = bins
               else:
                  bins = math.ceil(2*l_n**(1./3))# Rice rule
                  if bins<8:
                     bins=8

               histo,edges = np.histogram(l_data,density=False, bins=bins,range=CocoDisplay.min_max_range(np.min(l_data),np.max(l_data)))

               contributors=[]
               for i,j in zip(edges[:-1],edges[1:]):
                   res = [key for key, val in filter(lambda sub: int(sub[1]) >= i and
                                   int(sub[1]) <= j, val_per_country.items())]
                   contributors.append(res)
               frame_histo = pd.DataFrame({'val': histo,'left': edges[:-1],'right': edges[1:],
               'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2),
               'contributors':contributors})

        hover_tool = HoverTool(tooltips=tooltips)
        panels = []
        bottom=0


        for axis_type in ["linear", "log"]:
            if width_height:
                plot_width  = width_height[0]
                plot_height = width_height[1]
            else :
                plot_width  = width_height_default[0]
                plot_height = width_height_default[1]
            standardfig = figure(plot_width=plot_width, plot_height=plot_height,y_axis_type=axis_type,
            tools=['save','box_zoom,box_select,crosshair,reset'],toolbar_location="below")
            standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            if title:
                standardfig.title.text = title
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(Paired12)

            if axis_type=="log":
                bottom=1
            label = []
            if date == 'all' :
                p=[standardfig.quad(source=ColumnDataSource(value),top='val', bottom=bottom, left='left', right='right',name=key,
                    fill_color=next(colors),legend_label=key) for key,value in dict_histo.items()]
            else:
                if input_names_data == babepandas.columns[2]:
                    label = input_names_data + ' @ ' + when
                else:
                    label = babepandas.columns[2] + ' (' +input_names_data + ') @ ' + when
                p=standardfig.quad(source=ColumnDataSource(frame_histo),top='val', bottom=bottom, left='left', right='right',
                fill_color=next(colors),legend_label=label)

            #legend = Legend(items=[(list(standardfig.legend.items[p.index(i)].label.values())[0],[i]) for i in p],location="center")
            #standardfig.add_layout(legend,'right')
            standardfig.legend.label_text_font_size = "12px"

            panel = Panel(child=standardfig , title=axis_type)
            panels.append(panel)
        tabs = Tabs(tabs=panels)
        return tabs


    @staticmethod
    def scrolling_menu(babepandas, input_names_data = None,title = None, width_height = None):
        """Create a Bokeh plot with a date axis from pandas input

        Keyword arguments
        -----------------
        babepandas : pandas where the data is considered
        input_names_data : variable from pandas data . If pandas is produced from cocoas get_stat method
        the 'diff' or 'cumul' are available
        A list of names_data can be given
        title: title for the figure , no title by default
        width_height : width and height of the figure,  default [400,300]

        Note
        -----------------
        HoverTool is available it returns location, date and value
        """
        tooltips='Date: @date{%F} <br>  $name: @$name'
        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})

        if type(input_names_data) is None.__class__:
            print("Need variable to plot", file=sys.stderr)
        if 'where' in babepandas.columns:
            babepandas = babepandas.rename(columns={'where':'location'})
        if 'location' in babepandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = list(babepandas['location'].unique())
            loc = sorted(loc)
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]


        data  = pd.pivot_table(babepandas,index='date',columns='location',values=input_names_data)
        [data.rename(columns={i:j},inplace=True) for i,j in zip(loc,shorten_loc)]
        data=data.reset_index()
        source = ColumnDataSource(data)

        filter_data1 = data[['date', shorten_loc[0]]].rename(columns={shorten_loc[0]: 'cases'})
        name1=shorten_loc[0]
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = data[['date', shorten_loc[1]]].rename(columns={shorten_loc[1]: 'cases'})
        name2=shorten_loc[1]
        src2 = ColumnDataSource(filter_data2)

        hover_tool = HoverTool(tooltips=[
                        ("Cases", '@cases'),
                        ('date', '@date{%F}')],
                        formatters={'@date': 'datetime'},mode='vline')
        panels = []
        for axis_type in ["linear", "log"]:
            if width_height:
                plot_width  = width_height[0]
                plot_height = width_height[1]
            else :
                plot_width  = width_height_default[0]
                plot_height = width_height_default[1]

            standardfig = figure(plot_width=plot_width, plot_height=plot_height,y_axis_type=axis_type,
            x_axis_type='datetime',tools=[hover_tool,'save','box_zoom,box_select,crosshair,reset'],
            toolbar_location="below")
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            if title:
                standardfig.title.text = title
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(Paired12)

            standardfig.line(x='date', y='cases', source=src1, color='red',
            line_width=2, legend_label=name1, hover_line_width=3)
            standardfig.line(x='date', y='cases', source=src2, color='blue',
            line_width=2, legend_label=name2, hover_line_width=3)

            standardfig.legend.location = 'bottom_left'
            panel = Panel(child=standardfig, title=axis_type)
            panels.append(panel)
        code="""
            var c = cb_obj.value;
            var y = s0.data[c];
            s1.data['cases'] = y;
            s1.change.emit();
            ax=p1.yaxis[0]
        """
        callback1 = CustomJS(args=dict(s0=source, s1=src1), code=code)
        callback2 = CustomJS(args=dict(s0=source, s1=src2), code=code)
        select_countries1 = Select(title="red chart", value=shorten_loc[0], options=shorten_loc)
        select_countries1.js_on_change('value', callback1)
        select_countries2 = Select(title="blue chart", value=shorten_loc[1], options=shorten_loc)
        select_countries2.js_on_change('value', callback2)

        tabs = Tabs(tabs=panels)
        layout = row(column(row(select_countries1, select_countries2), row(tabs)))
        return layout

    def CrystalFig(self, crys, err_y):
        sline = []
        scolumn = []
        i = 1
        list_fits_fig = crys.GetListFits()
        for dct in list_fits_fig:
            for key, value in dct.items():
                location = key
                if math.nan not in value[0] and math.nan not in value[1]:
                    maxy = crys.GetFitsParameters()[location][1]
                    if math.isnan(maxy) == False:
                        maxy = int(maxy)
                    leg = 'From fit : tmax:' + \
                        str(crys.GetFitsParameters()[location][0])
                    leg += '   Tot deaths:' + str(maxy)
                    fig = figure(plot_width=300, plot_height=200,
                                 tools=['box_zoom,box_select,crosshair,reset'], title=leg, x_axis_type="datetime")

                    date = [datetime.strptime(i, '%m/%d/%y')
                            for i in self.p.getDates()]
                    if err_y:
                        fig.circle(
                            date, value[0], color=self.colors[i % 10], legend_label=location)
                        y_err_x = []
                        y_err_y = []
                        for px, py in zip(date, value[0]):
                            err = np.sqrt(np.abs(py))
                            y_err_x.append((px, px))
                            y_err_y.append((py - err, py + err))
                        fig.multi_line(y_err_x, y_err_y,
                                       color=self.colors[i % 10])
                    else:
                        fig.line(
                            date, value[0], line_color=self.colors[i % 10], legend_label=location)

                    fig.line(date[:crys.GetTotalDaysConsidered(
                    )], value[1][:crys.GetTotalDaysConsidered()], line_color='red', line_width=4)

                    fig.xaxis.formatter = DatetimeTickFormatter(
                        days=["%d %b %y"], months=["%d %b %y"], years=["%d %b %y"])
                    fig.xaxis.major_label_orientation = math.pi/4
                    fig.xaxis.ticker.desired_num_ticks = 10

                    # tot_type_country=self.p.get_stats(country=country,type='Cumul',which='deaths')[-1]

                    fig.legend.location = "bottom_left"
                    fig.legend.title_text_font_style = "bold"
                    fig.legend.title_text_font_size = "5px"

                    scolumn.append(fig)
                    if i % 2 == 0:
                        sline.append(scolumn)
                        scolumn = []
                    i += 1
        fig = gridplot(sline)
        return fig

    def get_pandas(self):
        ''' Retrieve the pandas when CoCoDisplay is called '''
        return self.pycoa_pandas

    def __delete__(self, instance):
        print("deleted in descriptor object")
        del self.value


    @staticmethod
    def save_map2png(map=None,pngfile='map.png'):
        '''
        Save map as png geckodriver and PIL packages are needed
        '''
        size = width_height_default[0],width_height_default[1]
        if pngfile:
            pngfile=pngfile
        img_data = map._to_png(5)
        img = Image.open(io.BytesIO(img_data))
        img.thumbnail(size, Image.ANTIALIAS)
        img.save(pngfile)
        print(pngfile, ' is now save ...')

    @staticmethod
    def save_pandas_as_png(df=None, pngfile='pandas.png'):
        source = ColumnDataSource(df)
        df_columns = [df.index.name]
        df_columns.extend(df.columns.values)
        columns_for_table=[]
        for column in df_columns:
            if column != None:
                columns_for_table.append(TableColumn(field=column, title=column))
                #width_height_default
        data_table = DataTable(source=source, columns=columns_for_table,
            height_policy="auto",width_policy="auto",index_position=None)
        export_png(data_table, filename = pngfile)

    def return_map(self,mypandas,which_data = None,width_height = None, date = 'last'):
        """Create a Folium map from a pandas input

        Keyword arguments
        -----------------
        babepandas : pandas consided
        which_data: variable from pandas data. If pandas is produced from pycoa get_stat method
        then 'diff' and 'cumul' can be also used
        width_height : as a list of width and height of the histo, default [500,400]
        date : - default 'last'
               Value at the last date (from database point of view) and for all the location defined in
               the pandas will be computed
               - date
               Value at date (from database point of view) and for all the location defined in the pandas
               will be computed
        """
        if 'where' in mypandas.columns:
            mypandas = mypandas.rename(columns={'where':'location'})

        if width_height:
            plot_width  = width_height[0]
            plot_height = width_height[1]
        else :
            plot_width  = width_height_default[0]
            plot_height = width_height_default[1]
        label , what ='',''
        if date == "last" :
            when = mypandas['date'].max()
            when = when.strftime('%m/%d/%y')
        else:
            when = date

        if type(which_data) is None.__class__:
            which_data = mypandas.columns[2]
            label = which_data
        else:
            which_data = which_data
            if which_data == 'diff' :
               what = 'day to day diffence'
            else:
               what = 'cumulative sum'
            label = mypandas.columns[2] + ' (' + what +  ' @ ' + when + ')'



        jhu_stuff = mypandas.loc[(mypandas.date == when)]

        a = self.info.add_field(field=['geometry'],input=jhu_stuff ,geofield='location')

        data=gpd.GeoDataFrame(self.info.add_field(input=a,geofield='location',\
                                  field=['country_name']),crs="EPSG:4326")
        data = data.loc[data.geometry != None]
        data['geoid'] = data.index.astype(str)

        data=data[['geoid','location',which_data,'geometry']]
        data[which_data] = round(data[which_data])
        data = data.set_index('geoid')

        centroid=unary_union(data.geometry).centroid
        min_col,max_col=CocoDisplay.min_max_range(0,max(data[which_data]))
        colormap = branca.colormap.linear.RdPu_09.scale(min_col,max_col)
        #colormap = (colormap.to_step(n=len(data[which_data]),method='log'))
        colormap.caption = 'Covid-19 cases : ' + label
        fig = Figure(width=plot_width, height=plot_height)
        mapa = folium.Map(location=[centroid.y, centroid.x], zoom_start=2)
        #tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png',
        #attr = "IGN")
        fig.add_child(mapa)
        folium.GeoJson(
            data,
            style_function=lambda x:
            {
                #'fillColor': '#ffffffff' if x['properties'][which_data] < max(data[which_data]/1000.) else
                'fillColor':colormap(x['properties'][which_data]),
                'fillOpacity': 0.8,
                'color' : None,
            },
            name="Cases",
            highlight_function=lambda x: {'weight':2, 'color':'green'},
            tooltip=folium.GeoJsonTooltip(fields=['location',which_data],
                                              aliases = ['country','totcases'],
                                              labels=False),


        ).add_to(mapa)
        colormap.add_to(mapa)
        #folium.LayerControl(autoZIndex=False, collapsed=False).add_to(mapa)
        return mapa
'''
        choro = folium.Choropleth(
        geo_data=data,
        name='Covid19cases',
        data=data,
        columns=['geoid', which_data],
        key_on='feature.id',
        fill_color='PuRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        #scale=(0,100),
        line_color='white',
        line_weight=0,
        highlight=False,
        smooth_factor=1.0).add_to(mapa)
        mapa.add_child(colormap)
        folium.GeoJson(data,
               name="Cases",
               style_function=lambda x: {'color':'transparent','fillColor':'transparent','weight':0},
               highlight_function=lambda x: {'weight':2, 'color':'green'},
               tooltip=folium.GeoJsonTooltip(fields=['location',which_data],
                                             aliases = ['country','totcases'],
                                             labels=False)
                      ).add_to(mapa)
'''


def resume_pandas(self,pd):
    pd['New cases (last 30 days)'] = pd['deaths'].apply(self.sparkline)

'''
    babypandas_diff=self.p.getStats(country=self.countries,type='Diff',which='deaths',output='pandas')
    babypandas_diff=babypandas_diff.set_index('date')
    babypandas_cumul=self.p.getStats(country=self.countries,type='Cumul',which='deaths',output='pandas')
    babypandas_cumul=babypandas_cumul.set_index('date')

    n=self.SetTotalDaysConsidered(self.p.getDates()[0],self.stop_date_fit)
    [self.returnFits(i) for i in self.countries]

    pop_pd=w.getData()[w.getData()['Country'].isin(self.countries)]
        pop=pop_pd.sort_values(by=['Country'])['Population']

    Pourcentage=[[100*(self.GetTodayProjNdeaths()[i]-\
                      (babypandas_cumul.loc[babypandas_cumul['country']==i]).loc[self.stop_date_fit]['cases'])\
                  /(babypandas_cumul.loc[babypandas_cumul['country']==i]).loc[self.stop_date_fit]['cases'],0]\
                 [self.GetTodayProjNdeaths()[i] == -1]\
                 for i in self.countries]

    print(Pourcentage)

    resume =  pd.DataFrame({
                  'Country':self.countries,'Population':pop,
                  'Totaldeaths':babypandas_cumul.loc[self.stop_date_fit]['cases'].to_list(),
                  'TotaldeathsProj':[self.GetTodayProjNdeaths()[i] for i in self.countries],
                  'Diff%': Pourcentage,
                  'Total Forecast': [crys.GetFitsParameters()[i][1] for i in self.countries],
                  'Estimated pick': [crys.GetFitsParameters()[i][0] for i in self.countries],
                  'Last deaths': babypandas_diff.loc[self.stop_date_fit]['cases'].to_list(),
                  'Caseslist':(babypandas_diff.sort_values('date').groupby('country').apply(lambda x: x['cases'].tail(30)).values[:]).tolist()
    })
    resume['New cases (last 30 days)'] = resume['Caseslist'].apply(self.sparkline)
    last_date=self.stop_date_fit
    title='Resume and forcast for COVID-19 pandemy @ ' + str(last_date)
    resume=resume.loc[:, resume.columns != 'Caseslist']
    resume=resume.set_index('Country')
    resume=resume.sort_values(by=['Country'])
'''
