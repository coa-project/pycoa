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

from coa.tools import kwargs_test,check_valid_date,extract_dates,info,verb
import coa.geo as coge
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

from bokeh.models import ColumnDataSource, TableColumn, DataTable,ColorBar, \
    HoverTool,BasicTicker, GeoJSONDataSource, LinearColorMapper, Label, \
    PrintfTickFormatter, BasicTickFormatter, CustomJS, CustomJSHover, Select, \
    Range1d, DatetimeTickFormatter
from bokeh.models.widgets import Tabs, Panel
from bokeh.palettes import Viridis256, Cividis256, Turbo256, Magma256
from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Paired12
from bokeh.io import export_png
from bokeh import events

import branca.colormap
from branca.element import Element, Figure

import folium
from folium.plugins import FloatImage

from shapely.ops import unary_union

from PIL import Image, ImageDraw, ImageFont

import matplotlib.pyplot as plt
import datetime as dt
width_height_default = [600,337] #337 magical value to avoid scroll menu in bokeh map
class CocoDisplay():
    def __init__(self,db=None):
        verb("Init of CocoDisplay()")
        self.database_name = db
        self.colors = itertools.cycle(Paired12)
        self.plot_width =  width_height_default[0]
        self.plot_height =  width_height_default[1]

        self.all_available_display_keys=['where','which','what','date','when','plot_height','plot_width','title','bins','var_displayed',
        'option','input','input_field']

        if self.database_name == 'jhu' or self.database_name == 'owid':
            g=coge.GeoManager()
            g.set_standard('name')
            self.pandas_world = pd.DataFrame({'location':g.to_standard(['world'],interpret_region=True),
                                    'which':np.nan,'cumul':np.nan,'diff':np.nan,'weekly':np.nan})
            self.infoword = coge.GeoInfo()

        if self.database_name == 'spf' or self.database_name == 'opencovid19':
            c=coge.GeoCountry('FRA',True)
            self.pandas_country = pd.DataFrame({'location':c.get_data()['code_subregion'],
                                                   'which':np.nan,'cumul':np.nan,'diff':np.nan,'weekly':np.nan})
            self.infocountry = c
        if self.database_name == 'jhu-usa':
            c=coge.GeoCountry('USA',True)
            self.pandas_country = pd.DataFrame({'location':c.get_data()['code_subregion'],
                                                   'which':np.nan,'cumul':np.nan,'diff':np.nan,'weekly':np.nan})
            self.infocountry = c


    def standard_input(self,mypandas,**kwargs):
        '''
        Parse a standard input, return :
            - pandas: with location keyword (eventually force a column named 'where' to 'location')
            - dico:
                * keys = [plot_width, plot_width, titlebar, date, when, bins, what, which, var_displayed]
        Note that method used only the needed variables, some of them are useless
        '''
        input_dico={}
        if 'where' in mypandas.columns:
            mypandas = mypandas.rename(columns={'where':'location'})
        kwargs_test(kwargs,self.all_available_display_keys,'Bad args used in the display function.')
        plot_width = kwargs.get('plot_width', self.plot_width)
        plot_height = kwargs.get('plot_height', self.plot_height)
        if plot_width != self.plot_width:
            self.plot_width = plot_width
        if plot_height != self.plot_height:
            self.plot_height = plot_height
        input_dico['plot_width']=plot_width
        input_dico['plot_height']=plot_height

        date = kwargs.get('date', None)
        bins = kwargs.get('bins',50)
        if bins != 50:
            bins = bins
        input_dico['bins'] = bins

        what = kwargs.get('what', None)
        input_dico['what']=what

        which =  mypandas.columns[2]
        input_dico['which']=which
        var_displayed=which
        when = mypandas.date.max()
        title = kwargs.get('title', None)
        input_dico['title']=title
        if date:
            when = extract_dates(date)
        titlebar = which + ' (@' + when[1].strftime('%d/%m/%Y') +')'
        if what:
            if what not in ['daily','diff','cumul','weekly']:
                raise CoaTypeError('what argument is not diff nor cumul. See help.')
            else:
                if what == 'daily' or what == 'diff':
                    titlebar = which + ' (' + 'day to day difference ' +  ' @ ' + when.strftime('%d/%m/%Y') + ')'
                    what = 'diff'
                if what == 'weekly':
                    titlebar = which + ' (' + 'daily rolling over 1 week' +  ' @ ' + when.strftime('%d/%m/%Y') + ')'
                elif what == 'cumul':
                    titlebar = which + ' (' + 'cumulative sum ' +  ' @ ' + when.strftime('%d/%m/%Y') + ')'
                #else:
                #    titlebar = which + ' (' + what +  ' @ ' + when.strftime('%d/%m/%Y') + ')'
                var_displayed = what

        if title:
            titlebar = title
        input_dico['titlebar']=titlebar
        input_dico['var_displayed']=var_displayed
        input_dico['when']=when[1]
        input_dico['data_base'] = self.database_name
        return mypandas, input_dico

    def standardfig(self,dbname=None,**kwargs):
         """
         Create a standard Bokeh figure, with pycoa.frlabel,used in all the bokeh charts
         """
         fig=figure(**kwargs,plot_width=self.plot_width,plot_height=self.plot_height,
         tools=['save','box_zoom,reset'],toolbar_location="right")
         logo_db_citation = Label(x=0.005*self.plot_width, y=0.01*self.plot_height, x_units='screen', y_units='screen',
         text_font_size='1.5vh',text='©pycoa.fr (data from: {})'.format(self.database_name))
         fig.add_layout(logo_db_citation)
         return fig

    @staticmethod
    def bokeh_legend(bkfigure):
        toggle_legend_js = CustomJS(args=dict(leg=bkfigure.legend[0]), code="""
                            if (leg.visible) {
                            leg.visible = false
                            }
                            else {
                            leg.visible = true
                            }
                            """)
        bkfigure.js_on_event(events.DoubleTap, toggle_legend_js)


    def pycoa_date_plot(self,mypandas, input_field = None, **kwargs):
        """Create a Bokeh date chart from pandas input (x axis is a date format)

        Keyword arguments
        -----------------
        - babepandas : pandas where the data is considered
        - input_field : variable from pandas data.
          * variable or list of variables available in babepandas (i.e available in the babepandas columns name  )
          * If pandas is produced from pycoa get_stat method 'diff' or 'cumul' variable are available
        - title: title for the figure , no title by default
        - width_height : width and height of the figure,  default [400,300]

        Note
        -----------------
        HoverTool is available it returns location, date and value
        """
        mypandas,dico = self.standard_input(mypandas,**kwargs)

        dict_filter_data = defaultdict(list)
        tooltips='Date: @date{%F} <br>  $name: @$name'

        if type(input_field) is None.__class__:
           if dico['which']:
               input_field = dico['which']
           if dico['what']:
               input_field = dico['var_displayed']
           if type(dico['which']) and type(dico['what'])  is None.__class__:
               CoaTypeError('What do you want me to do ?. No variable to histogram . See help.')
        else:
                if not isinstance(input_field, list):
                    text_input = input_field
                else:
                    text_input = '-'
                    text_input= text_input.join(input_field)

        if not isinstance(input_field, list):
            input_field=[input_field]

        if 'location' in mypandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = mypandas['location'].unique()
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]
            for i in input_field:
                dict_filter_data[i] =  \
                    dict(mypandas.loc[(mypandas['location'].isin(loc)) & (mypandas['date']<=dico['when']) ].groupby('location').__iter__())
                for j in range(len(loc)):
                    dict_filter_data[i][shorten_loc[j]] = dict_filter_data[i].pop(loc[j])

        else:
            for i in input_field:
                dict_filter_data[i] = {i:mypandas}

        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})

        panels = []
        for axis_type in ["linear", "log"]:
            standardfig =  self.standardfig(y_axis_type=axis_type, x_axis_type='datetime',title= dico['titlebar'])
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")

            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(Paired12)
            for i in input_field:
                if len(input_field)>1:
                    p = [standardfig.line(x='date', y=i, source=ColumnDataSource(value),
                    color=next(colors), line_width=3, legend_label=key+' ('+i+')',
                    name=i,hover_line_width=4) for key,value in dict_filter_data[i].items()]
                else:
                    p = [standardfig.line(x='date', y=i, source=ColumnDataSource(value),
                    color=next(colors), line_width=3, legend_label=key,
                    name=i,hover_line_width=4) for key,value in dict_filter_data[i].items()]
            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig , title=axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "bottom_right"

            standardfig.xaxis.formatter = DatetimeTickFormatter(
                days=["%d/%m/%y"], months=["%d/%m/%y"], years=["%b %Y"])
            CocoDisplay.bokeh_legend(standardfig)
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

        if a_min==0:
            if a_max==0:
                p=0
            else:
                p=max_p
        else:
            if a_max==0:
                p=min_p
            else:
                p=max(min_p,max_p)

        if a_min!=0:
            min_r=math.floor(a_min/10**(p-1))*10**(p-1) # min range rounded
        else:
            min_r=0

        if a_max!=0:
            max_r=math.ceil(a_max/10**(p-1))*10**(p-1)
        else:
            max_r=0

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

    def pycoa_histo(self,mypandas,input_field = None,**kwargs):
        """Create a Bokeh histogram from a pandas input

        Keyword arguments
        -----------------
        babepandas : pandas consided
        input_field : variable from pandas data. If pandas is produced from pycoa get_stat method
        then 'diff' and 'cumul' can be also used
        title: title for the figure , no title by default
        width_height : as a list of width and height of the histo, default [500,400]
        bins : number of bins of the hitogram default 50
        date : - default None
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
        mypandas,dico = self.standard_input(mypandas,**kwargs)
        dict_histo = defaultdict(list)

        if type(input_field) is None.__class__:
           if dico['which']:
               input_field = dico['which']
           if dico['what']:
               input_field = dico['what']
           if type(dico['which']) and type(dico['what'])  is None.__class__:
               CoaTypeError('What do you want me to do ?. No variable to histogram . See help.')

        if 'location' in mypandas.columns:
            tooltips='Value at around @middle_bin : @val'
            loc = mypandas['location'].unique()
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]

            for w in loc:
                histo,edges = np.histogram((mypandas.loc[mypandas['location'] == w][input_field].dropna()),density=False, bins=dico['bins'])

                dict_histo[w] = pd.DataFrame({'location':w,'val': histo,
                   'left': edges[:-1],
                   'right': edges[1:],
                   'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2)})
            for j in range(len(loc)):
                dict_histo[shorten_loc[j]] = dict_histo.pop(loc[j])

            tooltips = 'Contributors : @contributors'

            val_per_country = defaultdict(list)
            for w in loc:
               retrieved_at = mypandas.loc[(mypandas['date'] == dico['when'])]
               if retrieved_at.empty:
                   raise CoaTypeError('Noting to retrieve at this date:', dico['when'])
               else:
                   val = mypandas.loc[(mypandas['location'] == w) & (mypandas['date'] == dico['when'])][input_field].values
                   #val_per_country.append(val)
               val_per_country[w]=val

            l_data=list(val_per_country.values())
            # good nb of bins
            l_n=len(l_data)
            if dico['bins']:
              bins = dico['bins']
            else:
              bins = math.ceil(2*l_n**(1./3))# Rice rule
              if bins<8:
                     bins=8

            histo,edges = np.histogram(l_data,density=False, bins=bins,range=CocoDisplay.min_max_range(np.min(l_data),np.max(l_data)))
            contributors=[]
            for i,j in zip(edges[:-1],edges[1:]):
                   res = [key for key, val in filter(lambda sub: int(sub[1]) >= i and int(sub[1]) <= j, val_per_country.items())]
                   contributors.append(res)
            frame_histo = pd.DataFrame({'val': histo,'left': edges[:-1],'right': edges[1:],
              'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2),
              'contributors':contributors})
        x_max=max(edges[1:])
        y_max=max(histo)
        hover_tool = HoverTool(tooltips=tooltips)
        panels = []
        bottom=0

        for axis_type in ["linear", "log"]:
            standardfig = self.standardfig(y_axis_type=axis_type)
            standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            #standardfig.title.text = dico['titlebar']
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(Paired12)

            if axis_type=="log":
                bottom=0.0001
            else:
                standardfig.y_range=Range1d(0, y_max)
            label = dico['titlebar']
            p=standardfig.quad(source=ColumnDataSource(frame_histo),top='val', bottom=bottom, left='left', right='right',
            fill_color=next(colors),legend_label=label)

            standardfig.x_range=Range1d(0, x_max)
            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig , title=axis_type)
            panels.append(panel)
            CocoDisplay.bokeh_legend(standardfig)

        tabs = Tabs(tabs=panels)
        return tabs

    def scrolling_menu(self,mypandas,input_field = None,**kwargs):
        """Create a Bokeh plot with a date axis from pandas input

        Keyword arguments
        -----------------
        babepandas : pandas where the data is considered
        input_field : variable from pandas data . If pandas is produced from cocoas get_stat method
        the 'diff' or 'cumul' are available
        A list of names_data can be given
        title: title for the figure , no title by default
        width_height : width and height of the figure,  default [400,300]

        Note
        -----------------
        HoverTool is available it returns location, date and value
        """
        mypandas,dico = self.standard_input(mypandas,**kwargs)

        tooltips='Date: @date{%F} <br>  $name: @$name'
        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})

        if type(input_field) is None.__class__:
           if dico['which']:
               input_field = dico['which']
           if dico['what']:
               input_field = dico['what']
           if type(dico['which']) and type(dico['what'])  is None.__class__:
               CoaTypeError('What do you want me to do ?. No variable to histogram . See help.')

        if 'location' in mypandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = list(mypandas['location'].unique())
            loc = sorted(loc)
            if len(loc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                    'There is no sens to use this method. See help.')
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]


        data  = pd.pivot_table(mypandas,index='date',columns='location',values=input_field)
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
                        formatters={'@date': 'datetime'})
        panels = []
        for axis_type in ["linear", "log"]:
            standardfig = self.standardfig(y_axis_type=axis_type,x_axis_type='datetime')
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            if dico['title']:
                standardfig.title.text = dico['title']
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(Paired12)
            standardfig.line(x='date', y='cases', source=src1, color='firebrick',alpha=0.7,
            line_width=2, legend_label=name1, hover_line_width=3)
            standardfig.line(x='date', y='cases', source=src2, color='navy',alpha=0.7,
            line_width=2, legend_label=name2, hover_line_width=3)
            standardfig.legend.location = 'bottom_right'
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
        label = dico['titlebar']
        return layout

    def crystal_fig(self, crys, err_y):
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

                    date = [extract_dates(i)
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

    def get_geodata(self,mypandas):
        '''
         return a GeoDataFrame used in map display (see map_bokeh and map_folium)
         Argument : mypandas, the pandas to be analysed. Only location or where columns
         name is mandatory.
         The output format is the following :
         geoid | location |  geometry (POLYGON or MULTIPOLYGON)
         Example :  get_geodata(d)
        '''

        if not isinstance(mypandas, pd.DataFrame):
                raise CoaTypeError('Waiting for pandas input.See help.')
        else:
            if not any(elem in mypandas.columns.tolist() for elem in ['location','where']):
                raise CoaTypeError('location nor where columns is presents in your pandas.'
                                'One of them is mandatory. See help.')
            if 'where' in mypandas.columns:
                mypandas = mypandas.rename(columns={'where':'location'})

        columns_keeped=''
        if not 'geometry' in mypandas.columns:
            if self.database_name == 'spf' or self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
                data = gpd.GeoDataFrame(self.infocountry.add_field(input=mypandas,input_key='location',
                field=['geometry','town_subregion','name_subregion']),crs="EPSG:4326")
                columns_keeped = ['geoid','location','geometry','town_subregion','name_subregion']
                meta_data = 'country'
            else:
                a = self.infoword.add_field(field=['geometry'],input=mypandas ,geofield='location')
                data=gpd.GeoDataFrame(self.infoword.add_field(input=a,geofield='location',field=['country_name']),
                crs="EPSG:4326")
                columns_keeped = ['geoid','location','geometry']
                meta_data = 'world'

        data = data.loc[data.geometry != None]
        data['geoid'] = data.index.astype(str)
        data=data[columns_keeped]
        data = data.set_index('geoid')
        data.meta_geoinfo = meta_data
        return data

    @staticmethod
    def changeto_nonan_date(df=None,when=None,field=None):
        value=np.nan
        if np.isnan(value):
            value=np.nan
            j=0
            while(np.isnan(value) == True):
                    value = np.nanmax(df.loc[df.date==when-dt.timedelta(days=j)][field])
                    j+=1
            if j>1:
                print(when, 'all the value seems to be nan! I will find an other previous date')
                print("Here the date I will take:", when-dt.timedelta(days=j-1))
            nonandata=when-dt.timedelta(days=j-1)
        else:
            nonandata = when
        return  nonandata

    def bokeh_map(self,mypandas,input_field = None,**kwargs):
        """Create a Bokeh map from a pandas input
        Keyword arguments
        -----------------
        babepandas : pandas considered
        Input parameters:
          - what (default:None) at precise date: by default get_which() set in get_stats()
           could be 'diff' or cumul
          - date (default:None): at which date data would be seen
          - plot_width, plot_height (default [500,400]): bokeh variable for map size
        Known issue: can not avoid to display value when there are Nan values
        """
        #esri = get_provider(WIKIMEDIA)

        mypandas,dico = self.standard_input(mypandas,**kwargs)

        if type(input_field) is None.__class__:
           input_field = dico['var_displayed']
        else:
            input_field = input_field

        flag = ''
        minx, miny, maxx, maxy=0,0,0,0
        if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            panda2map = self.pandas_country
            name_displayed = 'town_subregion'

        else:
            panda2map = self.pandas_world
            name_displayed = 'location'

        mypandas_filtered = mypandas.loc[(mypandas.date == dico['when'])]

        if CocoDisplay.changeto_nonan_date(mypandas, dico['when'],input_field) != dico['when']:
            dico['when'] = CocoDisplay.changeto_nonan_date(mypandas,dico['when'],input_field)
            mypandas_filtered = mypandas.loc[(mypandas.date == dico['when'])]
            dico['titlebar']+=' due to nan I shifted date to '+  dico['when'].strftime("%d/%m/%Y")

        mypandas_filtered = mypandas_filtered.drop(columns=['date'])
        my_countries = mypandas.location.to_list()

        panda2map = panda2map.rename(columns={'which':dico['which']})
        panda2map = panda2map[~panda2map.location.isin(my_countries)]
        panda2map = panda2map.append(mypandas_filtered)

        geopdwd = self.get_geodata(panda2map)
        geopdwd = geopdwd#.to_crs('EPSG:3857')#+proj=wintri')
        geopdwd = geopdwd.reset_index()

        geopdwd = pd.merge(geopdwd,panda2map,on='location')
        geopdwd = geopdwd.set_index("geoid")

        merged_json = json.loads(geopdwd.to_json())
        json_data = json.dumps(merged_json)
        geosource = GeoJSONDataSource(geojson = json_data)

        # geobounds = geopdwd.loc[geopdwd.location.isin(my_countries)]
        # minx, miny, maxx, maxy=unary_union(geobounds.geometry).bounds
        # high speed version …
        gbounds = (geopdwd.loc[geopdwd.location.isin(my_countries)]).bounds
        maxx,maxy = gbounds.max()[['maxx','maxy']]
        minx,miny = gbounds.min()[['minx','miny']]

        standardfig = self.standardfig(title=dico['titlebar'], x_range=Range1d(minx, maxx), y_range=Range1d(miny, maxy))
        standardfig.plot_height=dico['plot_height']+100
        standardfig.plot_width = dico['plot_width']-100

        min_col,max_col=CocoDisplay.min_max_range(0,np.nanmax(geopdwd[input_field]))

        #standardfig.add_tile(esri)
        #Viridis256.reverse()
        color_mapper = LinearColorMapper(palette=Viridis256, low = min_col, high = max_col, nan_color = '#d9d9d9')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4,
                            border_line_color=None,location = (0,0), orientation = 'horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True,precision=1,power_limit_low=int(max_col))
        standardfig.add_layout(color_bar, 'below')
        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.patches('xs','ys', source = geosource,fill_color = {'field':input_field, 'transform' : color_mapper},
                  line_color = 'black', line_width = 0.25, fill_alpha = 1)
        cases_custom = CustomJSHover(code="""
        var value;
        if(value>0)
            return value.toExponential(2).toString();

        """)
        standardfig.add_tools(HoverTool(
        tooltips=[(name_displayed,'@'+name_displayed),(input_field,'@'+input_field+'{custom}'),],
        formatters={name_displayed:'printf','@'+input_field:cases_custom,},
        point_policy="follow_mouse"
        ))

        return standardfig

    def map_folium(self,mypandas,input_field = None,**kwargs):
        """Create a Folium map from a pandas input
        Folium limite so far:
            - scale format can not be changed (no way to use scientific notation)
            - map can not be saved as png only html format
                - save_map2png for this purpose (available only in command line, not in iconic form)
        Keyword arguments
        -----------------
        babepandas : pandas consided
        which_data: variable from pandas data. If pandas is produced from pycoa get_stat method
        then 'diff' and 'cumul' can be also used
        width_height : as a list of width and height of the histo, default [500,400]
        date : - default 'None'
               Value at the last date (from database point of view) and for all the location defined in
               the pandas will be computed
               - date
               Value at date (from database point of view) and for all the location defined in the pandas
               will be computed
        Known issue: format for scale can not be changed. When data value are important
        overlaped display appear
        """
        mypandas,dico = self.standard_input(mypandas,**kwargs)

        if type(input_field) is None.__class__:
           input_field = dico['var_displayed']

        mypandas_filtered = mypandas.loc[(mypandas.date == dico['when'])]
        if CocoDisplay.changeto_nonan_date(mypandas, dico['when'],input_field) != dico['when']:
            dico['when'] = CocoDisplay.changeto_nonan_date(mypandas,dico['when'],input_field)
            mypandas_filtered = mypandas.loc[(mypandas.date == dico['when'])]
            dico['titlebar']+=' due to nan I shifted date to '+  dico['when'].strftime("%d/%m/%Y")

        mypandas_filtered = mypandas_filtered.drop(columns=['date'])

        flag = ''
        if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            panda2map = self.pandas_country
            name_displayed = 'town_subregion'
            zoom = 5
        else:
            panda2map = self.pandas_world
            name_displayed = 'location'
            zoom = 2

        geopdwd = self.get_geodata(mypandas_filtered)
        geopdwd = geopdwd.reset_index()
        geopdwd = pd.merge(geopdwd,mypandas_filtered,on='location')
        geopdwd = geopdwd.set_index("geoid")
        centroid=unary_union(geopdwd.geometry).centroid

        fig = Figure(width=self.plot_width, height=self.plot_height)
        mapa = folium.Map(location=[centroid.y, centroid.x], zoom_start=zoom)
        fig.add_child(mapa)

        min_col,max_col=CocoDisplay.min_max_range(0,max(geopdwd[input_field]))
        colormap = branca.colormap.linear.RdPu_09.scale(min_col,max_col)
        colormap.caption = 'Covid-19 cases : ' + dico['titlebar']
        colormap.add_to(mapa)
        map_id = colormap.get_name()

        my_js = """
        var div = document.getElementById('legend');
        var ticks = document.getElementsByClassName('tick')
        for(var i = 0; i < ticks.length; i++){
        var values = ticks[i].textContent.replace(',','')
        val = parseFloat(values).toExponential(2).toString()
        if(parseFloat(ticks[i].textContent) == 0) val = 0.
        div.innerHTML = div.innerHTML.replace(ticks[i].textContent,val);
        }
        """
        e = Element(my_js)
        html = colormap.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e

        W, H = (300,200)
        im = Image.new("RGBA",(W,H))
        draw = ImageDraw.Draw(im)
        msg = "©pycoa.fr (data from: {})".format(self.database_name)
        w, h = draw.textsize(msg)
        fnt = ImageFont.truetype('/Library/Fonts/Arial.ttf', 12)
        draw.text((2,0), msg, font=fnt,fill=(0, 0, 0))
        im.crop((0, 0,2*w,2*h)).save("pycoatextlogo.png", "PNG")
        FloatImage("pycoatextlogo.png", bottom=-2, left=1).add_to(mapa)
        geopdwd[input_field+'scientific_format']=(['{:.3g}'.format(i) for i in geopdwd[input_field]])
        folium.GeoJson(
            geopdwd,
            style_function=lambda x:
            {
                'fillColor':colormap(x['properties'][input_field]),
                'fillOpacity': 0.8,
                'color' : None,
            },
            highlight_function=lambda x: {'weight':2, 'color':'green'},
            tooltip=folium.features.GeoJsonTooltip(fields=[name_displayed,input_field+'scientific_format'],
                aliases=[name_displayed+':',input_field+":"],
                style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                        opacity: 0.2;
                        """),
                #'<div style="background-color: royalblue 0.2; color: black; padding: 2px; border: 1px solid black; border-radius: 2px;">'+input_field+'</div>'])
        ).add_to(mapa)

        return mapa
    @staticmethod
    def sparkline(data, figsize=(2, 0.25), **kwargs):
        """
        Returns a HTML image tag containing a base64 encoded sparkline style plot
        """
        data = list(data)
        *_, ax = plt.subplots(1, 1, figsize=figsize, **kwargs)

        ax.plot(data)
        ax.fill_between(range(len(data)), data, len(data)*[min(data)], alpha=0.1)
        ax.set_axis_off()
        img = BytesIO()
        plt.savefig(img)
        plt.close()
        return '<img src="data:image/png;base64, {}" />'.format(base64.b64encode(img.getvalue()).decode())

    def spark_pandas(self,pandy,which_data):
        '''
        Return pandas : location as index andwhich_data as sparkline (latest 30 values)
        '''
        pd.DataFrame._repr_html_ = lambda self: self.to_html(escape=False)
        loc = pandy['location'].unique()
        resume =  pd.DataFrame({
                'location':loc,
                'cases':
                [CocoDisplay.sparkline(pandy.groupby('location')[which_data].apply(list)[i][-30:])
                for i in loc]})
        return resume.set_index('location')
