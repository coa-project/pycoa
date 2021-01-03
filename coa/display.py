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
from datascroller import scroll
from bokeh.models import ColumnDataSource, TableColumn, DataTable,ColorBar, \
    HoverTool,BasicTicker, GeoJSONDataSource, LinearColorMapper, Label, \
    PrintfTickFormatter, BasicTickFormatter, CustomJS, CustomJSHover, Select, \
    Range1d, DatetimeTickFormatter, Legend, LegendItem,PanTool
from bokeh.models.widgets import Tabs, Panel
from bokeh.palettes import Viridis256, Cividis256, Turbo256, Magma256
from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Paired12
from bokeh.palettes import Dark2_5 as palette
from bokeh.io import export_png
from bokeh import events
import shapely.geometry as sg
from bokeh.tile_providers import get_provider, Vendors

import branca.colormap
from branca.element import Element, Figure

import folium
from folium.plugins import FloatImage

from shapely.ops import unary_union

from PIL import Image, ImageDraw, ImageFont

import matplotlib.pyplot as plt
import datetime as dt
width_height_default = [680,330] #337 magical value to avoid scroll menu in bokeh map

class CocoDisplay():
    def __init__(self,db=None):
        verb("Init of CocoDisplay() with db="+str(db))
        self.database_name = db
        self.colors = Paired12[:10]
        self.plot_width =  width_height_default[0]
        self.plot_height =  width_height_default[1]
        self.all_available_display_keys=['where','which','what','when','title_temporal','plot_height','plot_width','title','bins','var_displayed',
        'option','input','input_field','visu','plot_last_date','tile']
        self.tiles_listing=['CARTODBPOSITRON','CARTODBPOSITRON_RETINA','STAMEN_TERRAIN','STAMEN_TERRAIN_RETINA',
        'STAMEN_TONER','STAMEN_TONER_BACKGROUND','STAMEN_TONER_LABELS','OSM','WIKIMEDIA','ESRI_IMAGERY']
        if self.database_name == 'jhu' or self.database_name == 'owid':
            g=coge.GeoManager()
            g.set_standard('name')
            self.pandas_world = pd.DataFrame({'location':g.to_standard(['world'],interpret_region=True),
                                    'which':np.nan,'cumul':np.nan,'daily':np.nan,'weekly':np.nan})
            self.infoword = coge.GeoInfo()

        if self.database_name == 'spf' or self.database_name == 'opencovid19':
            c=coge.GeoCountry('FRA',True)
            self.pandas_country = pd.DataFrame({'location':c.get_data()['code_subregion'],
                                                   'which':np.nan,'cumul':np.nan,'daily':np.nan,'weekly':np.nan})
            self.infocountry = c
        if self.database_name == 'jhu-usa':
            c=coge.GeoCountry('USA',True)
            self.pandas_country = pd.DataFrame({'location':c.get_data()['code_subregion'],
                                                   'which':np.nan,'cumul':np.nan,'daily':np.nan,'weekly':np.nan})
            self.infocountry = c

    def standard_input(self,mypandas,input_field=None,**kwargs):
        '''
        Parse a standard input, return :
            - pandas: with location keyword (eventually force a column named 'where' to 'location')
            - dico:
                * keys = [plot_width, plot_width, titlebar, when, title_temporal,bins, what, which, var_displayed]
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

        bins = kwargs.get('bins',50)
        if bins != 50:
            bins = bins
        input_dico['bins'] = bins

        what = kwargs.get('what', None)
        input_dico['what']=what

        if 'location' in mypandas:
            which =  mypandas.columns[2]
        else:
            which =  mypandas.columns[1]

        input_dico['which']=which
        var_displayed=which

        title = kwargs.get('title', None)
        input_dico['title']=title
        when = kwargs.get('when', None)
        input_dico['when'] = when
        title_temporal=''
        input_dico['when_beg'] = mypandas.date.min()
        input_dico['when_end'] = mypandas.date.max()

        if when:
            input_dico['when_beg'],input_dico['when_end']=extract_dates(when)
            if input_dico['when_beg'] == dt.date(1,1,1):
                input_dico['when_beg'] = mypandas['date'].min()

            if input_dico['when_end'] == '':
                input_dico['when_end'] = mypandas.date.max()

        if kwargs.get('plot_last_date',None) == True:
            title_temporal =  ' (at ' + input_dico['when_end'].strftime('%d/%m/%Y') + ')'
        else:
            title_temporal =  ' (' + 'between ' + input_dico['when_beg'].strftime('%d/%m/%Y') +' and ' + input_dico['when_end'].strftime('%d/%m/%Y') + ')'


        if kwargs.get('option', '') != '':
            title_temporal = ', option '+str(kwargs.get('option'))+title_temporal

        input_dico['title_temporal'] = title_temporal
        titlebar = which + title_temporal

        if input_field:
            if not isinstance(input_field, list):
                input_field=[input_field]
            else:
                input_field=input_field
            input_dico['input_field'] = input_field
        else:
            if what:
                if what == 'daily':
                    titlebar = which + ', ' + 'day to day difference ' +  title_temporal
                elif what == 'weekly':
                    titlebar = which + ', ' + 'week to week difference' + title_temporal
                elif what == 'cumul':
                    titlebar = which + ', ' + 'cumulative sum ' +  title_temporal
                else:
                    raise CoaTypeError('what argument is not daily, daily, cumul nor weekly . See help.')
                    #else:
                    #    titlebar = which + ' (' + what +  ' @ ' + when.strftime('%d/%m/%Y') + ')'
                var_displayed = what

        when_end_change=CocoDisplay.changeto_nonan_date(mypandas, input_dico['when_end'],var_displayed)
        if when_end_change != input_dico['when_end']:
             input_dico['when_end'] = when_end_change

        vendors = kwargs.get('tile', 'CARTODBPOSITRON')
        provider = None
        if vendors in self.tiles_listing:
            provider = vendors
        else:
            raise CoaTypeError('Don\'t which you want to load ...')

        input_dico['tile']=provider

        if title:
            titlebar = title
        input_dico['titlebar']=titlebar
        input_dico['var_displayed']=var_displayed
        input_dico['data_base'] = self.database_name

        return mypandas, input_dico

    def get_tiles(self):
        ''' Return all the tiles available in Bokeh '''
        return self.tiles_listing

    def standardfig(self,dbname=None,**kwargs):
         """
         Create a standard Bokeh figure, with pycoa.frlabel,used in all the bokeh charts
         """
         fig=figure(**kwargs,plot_width=self.plot_width,plot_height=self.plot_height,
         tools=['save','box_zoom,reset'],toolbar_location="right")
         logo_db_citation = Label(x=0.005*self.plot_width, y=0.01*self.plot_height, x_units='screen',
          y_units='screen',text_font_size='1.5vh',background_fill_color='white', background_fill_alpha=.75,
          text='©pycoa.fr (data from: {})'.format(self.database_name))
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
          * If pandas is produced from pycoa get_stat method 'daily','weekly' or 'cumul' variable are available
        - title: title for the figure , no title by default
        - width_height : width and height of the figure,  default [400,300]

        Note
        -----------------
        HoverTool is available it returns location, date and value
        """
        mypandas,dico = self.standard_input(mypandas,input_field,**kwargs)
        dict_filter_data = defaultdict(list)
        ax_type = ["linear", "log"]

        tooltips='Date: @date{%F} <br>  $name: @$name'

        if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
           input_field = mypandas.columns[2]
        else:
            if type(input_field) is None.__class__:
                input_field = [dico['var_displayed']]
            else:
                input_field = dico['input_field']

        if 'location' in mypandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = mypandas['location'].unique()
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]
            for i in input_field:
                dict_filter_data[i] =  \
                    dict(mypandas.loc[(mypandas['location'].isin(loc)) &
                                     (mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end']) ].groupby('location').__iter__())

                for j in range(len(loc)):
                    dict_filter_data[i][shorten_loc[j]] = dict_filter_data[i].pop(loc[j])
            list_max=[]
            for i in input_field:
                [list_max.append(max(value.loc[value.location.isin(loc)][i])) for key,value in dict_filter_data[i].items()]
            amplitude=(np.nanmax(list_max) - np.nanmin(list_max))
            if amplitude > 10**4:
                ax_type.reverse()
        else:
            for i in input_field:
                dict_filter_data[i] = {i:mypandas.loc[(mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end'])]}

        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})


        panels = []
        for axis_type in ax_type :
            standardfig =  self.standardfig(y_axis_type=axis_type, x_axis_type='datetime',title= dico['titlebar'])
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(self.colors)
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

            standardfig.legend.location = "top_left"

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
        then 'daily','weekly' and 'cumul' can be also used
        title: title for the figure , no title by default
        width_height : as a list of width and height of the histo, default [500,400]
        bins : number of bins of the hitogram default 50
        when : - default None
                dates are given under the format dd/mm/yyyy. In the when
                option, one can give one date which will be the end of
                the data slice. Or one can give two dates separated with
                ":", which will define the time cut for the output data
                btw those two dates.

        Note
        -----------------
        HoverTool is available it returns position of the middle of the bin and the value.
        """
        mypandas,dico = self.standard_input(mypandas,input_field,**kwargs,plot_last_date=True)
        dict_histo = defaultdict(list)
        if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
           input_field = mypandas.columns[2]
        else:
            if type(input_field) is None.__class__:
                input_field = dico['var_displayed']
            else:
                input_field = dico['input_field']

        dico['when_end'] = when_end
        if 'location' in mypandas.columns:
            tooltips='Value at around @middle_bin : @val'
            loc = mypandas['location'].unique()
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]

            for w in loc:
                histo,edges = np.histogram((mypandas.loc[(mypandas['location'] == w) &
                                                        (mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end'])]
                                                        [input_field].dropna()),density=False, bins=dico['bins'])

                dict_histo[w] = pd.DataFrame({'location':w,'val': histo,
                   'left': edges[:-1],
                   'right': edges[1:],
                   'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2)})
            for j in range(len(loc)):
                dict_histo[shorten_loc[j]] = dict_histo.pop(loc[j])

            tooltips = 'Contributors : @contributors'

            val_per_country = defaultdict(list)
            for w in loc:
               mypandas = mypandas.loc[(mypandas.date == dico['when_end'])]
               val = mypandas.loc[mypandas['location'] == w][input_field].values
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
            colors = itertools.cycle(self.colors)

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
        the 'daily' or 'cumul' are available
        A list of names_data can be given
        title: title for the figure , no title by default
        width_height : width and height of the figure,  default [400,300]

        Note
        -----------------
        HoverTool is available it returns location, date and value
        """
        mypandas,dico = self.standard_input(mypandas,input_field,**kwargs)

        if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
           input_field = mypandas.columns[2]
        else:
            if type(input_field) is None.__class__:
                input_field = dico['var_displayed']
            else:
                input_field = dico['input_field']

        tooltips='Date: @date{%F} <br>  $name: @$name'
        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})


        if 'location' in mypandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = list(mypandas['location'].unique())
            loc = sorted(loc)
            if len(loc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                    'There is no sens to use this method. See help.')
            shorten_loc = [ i if len(i)<15 else i.replace('-',' ').split()[0]+'...'+i.replace('-',' ').split()[-1] for i in loc]

        mypandas = mypandas.loc[(mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end'])]
        data  = pd.pivot_table(mypandas,index='date',columns='location',values=input_field)

        [data.rename(columns={i:j},inplace=True) for i,j in zip(loc,shorten_loc)]
        data=data.reset_index()
        source = ColumnDataSource(data)
        filter_data1 = data[['date', shorten_loc[0]]].rename(columns={shorten_loc[0]: 'cases'})
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = data[['date', shorten_loc[1]]].rename(columns={shorten_loc[1]: 'cases'})
        src2 = ColumnDataSource(filter_data2)
        hover_tool = HoverTool(tooltips=[
                        ("Cases", '@cases'),
                        ('date', '@date{%F}')],
                        formatters={'@date': 'datetime'})
        panels = []
        for axis_type in ["linear", "log"]:
            standardfig = self.standardfig(y_axis_type=axis_type,
            x_axis_type='datetime',title= dico['titlebar'])
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            if dico['title']:
                standardfig.title.text = dico['title']
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(self.colors)

            def add_line(src,options, init,  color):
                s = Select(options=options, value=init)
                r = standardfig.line(x='date', y='cases', source=src,line_width=3, line_color=color)
                li = LegendItem(label=init, renderers=[r])
                s.js_on_change('value', CustomJS(args=dict(s0=source, s1=src,li=li),
                                     code = """
                                            var c = cb_obj.value;
                                            var y = s0.data[c];
                                            s1.data['cases'] = y;
                                            li.label = {value: cb_obj.value};
                                            s1.change.emit();
                                     """))
                return s,li

            s1, li1 = add_line(src1,shorten_loc, shorten_loc[0], 'navy')
            s2, li2= add_line(src2,shorten_loc, shorten_loc[1], 'firebrick')
            standardfig.add_layout(Legend(items=[li1, li2]))
            standardfig.legend.location = 'top_left'
            layout = row(column(row(s1, s2), row(standardfig)))
            panel = Panel(child=layout, title=axis_type)
            panels.append(panel)

        tabs = Tabs(tabs=panels)
        label = dico['titlebar']
        return tabs

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
    def changeto_nonan_date(df=None,when_end=None,field=None):
        boolval=True
        j=0
        while(boolval == True):
                boolval = df.loc[df.date == (when_end-dt.timedelta(days=j))][field].dropna().empty
                j+=1
        if j>1:
            print(when_end, 'all the value seems to be nan! I will find an other previous date')
            print("Here the date I will take:", when_end-dt.timedelta(days=j-1))
        return  when_end-dt.timedelta(days=j-1)

    def get_polycoords(self,geopandasrow):
        """ Take a row of a geopandas as an input (i.e : for index, row in geopdwd.iterrows():...)
        and returns a tuple (if the geometry is a Polygon) or a list (if the geometry is a multipolygon)
        of an exterior.coords """
        geometry = geopandasrow['geometry']
        if geometry.type=='Polygon':
            return list( geometry.exterior.coords)
        if geometry.type=='MultiPolygon':
            all = []
            for ea in geometry:
                all.append(list( ea.exterior.coords))
            return all

    def wgs84_to_web_mercator(self,tuple_xy):
        ''' Take a tuple (longitude,latitude) from a coordinate reference system crs=EPSG:4326 '''
        ''' and converts it to a  longitude/latitude tuple from to Web Mercator format '''
        k = 6378137
        x = tuple_xy[0] * (k * np.pi/180.0)
        y = np.log(np.tan((90 + tuple_xy[1]) * np.pi/360.0)) * k
        return x,y


    def bokeh_map(self,mypandas,input_field = None,**kwargs):
        """Create a Bokeh map from a pandas input
        Keyword arguments
        -----------------
        babepandas : pandas considered
        Input parameters:
          - what (default:None) at precise date: by default get_which() set in get_stats()
           could be 'daily' or cumul or 'weekly'
          - when   --   dates are given under the format dd/mm/yyyy. In the when
                          option, one can give one date which will be the end of
                          the data slice. Or one can give two dates separated with
                          ":", which will define the time cut for the output data
                          btw those two dates.
                         Only the when_end date is taking into account [:dd/mm/yyyy]
          - plot_width, plot_height (default [500,400]): bokeh variable for map size
        Known issue: can not avoid to display value when there are Nan values
        """
        mypandas,dico = self.standard_input(mypandas,input_field,**kwargs,plot_last_date=True)

        if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
           input_field = mypandas.columns[2]
        else:
            if type(input_field) is None.__class__:
                input_field = dico['var_displayed']
            else:
                input_field = dico['input_field'][0]

        if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            panda2map = self.pandas_country
            name_displayed = 'name_subregion'
        else:
            panda2map = self.pandas_world
            name_displayed = 'location'


        my_location = mypandas.location.unique()
        mypandas_filtered = mypandas.loc[mypandas.date == dico['when_end']]

        mypandas_filtered = mypandas_filtered.drop(columns=['date'])
        geopdwd = self.get_geodata(mypandas_filtered)
        new_poly=[]
        geolistmodified=dict()
        for index, row in geopdwd.iterrows():
            split_poly=[]
            new_poly=[]
            for pt in self.get_polycoords(row):
                if type(pt) == tuple:
                    new_poly.append(self.wgs84_to_web_mercator(pt))
                elif type(pt) == list:
                    shifted=[]
                    for p in pt:
                        shifted.append(self.wgs84_to_web_mercator(p))
                    new_poly.append(sg.Polygon(shifted))
                else:
                    CoaTypeError("Neither tuple or list don't know what to do with \
                        your geometry description")

            if type(new_poly[0])==tuple:
               geolistmodified[row['location']]=sg.Polygon(new_poly)
            else:
               geolistmodified[row['location']]=sg.MultiPolygon(new_poly)

        ng = pd.DataFrame(geolistmodified.items(), columns=['location', 'geometry'])
        geolistmodified=gpd.GeoDataFrame({'location':ng['location'],'geometry':gpd.GeoSeries(ng['geometry'])},crs="epsg:3857")

        geopdwd = geopdwd.reset_index()
        geopdwd = pd.merge(geopdwd,mypandas_filtered,on='location')
        geopdwd = geopdwd.drop(columns='geometry')
        geopdwd = pd.merge(geopdwd,geolistmodified,on='location')
        geopdwd = geopdwd.set_index("geoid")
        json_data = json.dumps(json.loads(geopdwd.to_json()))
        geosource = GeoJSONDataSource(geojson = json_data)

        tile_provider = get_provider(dico['tile'])
        minx, miny, maxx, maxy = (geopdwd.loc[geopdwd.location.isin(my_location)]).total_bounds
        standardfig = self.standardfig(x_range=(minx,maxx), y_range=(miny,maxy),
        x_axis_type="mercator", y_axis_type="mercator",title=dico['titlebar'])

        standardfig.add_tile(tile_provider)
        min_col,max_col=CocoDisplay.min_max_range(0,np.nanmax(geopdwd[input_field]))

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
        tooltips=[(name_displayed,'@'+name_displayed),(input_field,'@{'+input_field+'}'+'{custom}'),],
        formatters={name_displayed:'printf','@{'+input_field+'}':cases_custom,},
        point_policy="follow_mouse"),PanTool())

        return standardfig

    def map_folium(self,mypandas,input_field=None,**kwargs):
        """Create a Folium map from a pandas input
        Folium limite so far:
            - scale format can not be changed (no way to use scientific notation)
            - map can not be saved as png only html format
                - save_map2png for this purpose (available only in command line, not in iconic form)
        Keyword arguments
        -----------------
        babepandas : pandas consided
        which_data: variable from pandas data. If pandas is produced from pycoa get_stat method
        then 'daily', 'weekly' and 'cumul' can be also used
        width_height : as a list of width and height of the histo, default [500,400]
        when   --   dates are given under the format dd/mm/yyyy. In the when
                        option, one can give one date which will be the end of
                        the data slice. Or one can give two dates separated with
                        ":", which will define the time cut for the output data
                        btw those two dates.
                    only the when_end date is taking into account [:dd/mm/yyyy]
        Known issue: format for scale can not be changed. When data value are important
        overlaped display appear
        """
        mypandas,dico = self.standard_input(mypandas,input_field,**kwargs,plot_last_date=True)

        if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
           input_field = mypandas.columns[2]
        else:
            if type(input_field) is None.__class__:
                input_field = dico['var_displayed']
            else:
                input_field = dico['input_field'][0]

        mypandas_filtered = mypandas.loc[mypandas.date == dico['when_end']]
        mypandas_filtered = mypandas_filtered.drop(columns=['date'])
        if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            panda2map = self.pandas_country
            panda2map = panda2map.loc[(panda2map.location != '2A') & (panda2map.location != '2B')]
            panda2map = panda2map.copy()
            name_displayed = 'town_subregion'
            my_location = mypandas.location.unique()
            zoom = 4
        else:
            panda2map = self.pandas_world
            name_displayed = 'location'
            zoom = 2

        geopdwd = self.get_geodata(mypandas_filtered)
        geopdwd = geopdwd.reset_index()
        geopdwd = pd.merge(geopdwd,mypandas_filtered,on='location')
        geopdwd = geopdwd.set_index("geoid")

        my_location = panda2map.location.to_list()
        minx, miny, maxx, maxy = (geopdwd.loc[geopdwd.location.isin(my_location)]).total_bounds

        mapa = folium.Map(location=[ (maxy+miny)/2., (maxx+minx)/2.], zoom_start=zoom)
        fig = Figure(width=self.plot_width, height=self.plot_height)
        fig.add_child(mapa)

        min_col,max_col=CocoDisplay.min_max_range(0,max(geopdwd[input_field]))
        colormap = branca.colormap.linear.RdPu_09.scale(min_col,max_col)
        colormap.caption = 'Cases : ' + dico['titlebar']
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
