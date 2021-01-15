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
from coa.geo import GeoManager as gm

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
from bokeh.models.tickers import FixedTicker
from bokeh.palettes import Viridis256, Cividis256, Turbo256, Magma256
from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Paired12
from bokeh.palettes import Dark2_5 as palette
from bokeh.io import export_png
from bokeh import events
from bokeh.models.widgets import DateSlider, Slider
from bokeh.tile_providers import get_provider, Vendors

import shapely.geometry as sg

import branca.colormap
from branca.colormap import LinearColormap
from branca.element import Element, Figure

import folium
from folium.plugins import FloatImage

from PIL import Image, ImageDraw, ImageFont

import matplotlib.pyplot as plt
import datetime as dt
width_height_default = [500,380]

class CocoDisplay():
    def __init__(self,db=None):
        verb("Init of CocoDisplay() with db="+str(db))
        self.database_name = db
        self.colors = Paired12[:10]
        self.plot_width =  width_height_default[0]
        self.plot_height =  width_height_default[1]
        self.geom = []
        self.this_done = False
        self.all_available_display_keys=['where','which','what','when','title_temporal','plot_height','plot_width','title','bins','var_displayed',
        'option','input','input_field','visu','plot_last_date','tile','orientation']
        self.tiles_listing=['CARTODBPOSITRON','CARTODBPOSITRON_RETINA','STAMEN_TERRAIN','STAMEN_TERRAIN_RETINA',
        'STAMEN_TONER','STAMEN_TONER_BACKGROUND','STAMEN_TONER_LABELS','OSM','WIKIMEDIA','ESRI_IMAGERY']


    def get_geodata(self,database='jhu'):
        '''
         return a GeoDataFrame used in map display (see map_bokeh and map_folium)
         Argument : database name
         The output format is the following :
         geoid | location |  geometry (POLYGON or MULTIPOLYGON)
        '''
        geopan = pd.DataFrame()
        if self.database_name == 'spf' or self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            if self.database_name == 'jhu-usa':
                country = 'USA'
            else:
                country = 'FRA'
            info = coge.GeoCountry(country,dense_geometry=False)

            geopan = info.get_subregion_list()[['code_subregion','town_subregion','geometry']]
            geopan = geopan.rename(columns={'code_subregion':'location'})
        elif self.database_name == 'jhu' or self.database_name == 'owid':
            geom=coge.GeoManager('name')
            info = coge.GeoInfo()
            allcountries = coge.GeoRegion().get_countries_from_region('world')
            geopan['location'] = [geom.to_standard(c)[0] for c in allcountries]
            geopan = info.add_field(field=['geometry'],input=geopan ,geofield='location')
            geopan = geopan[geopan.location != 'Antarctica']
        else:
            raise CoaTypeError('What data base are you looking for ?')

        geopan = geopan.dropna().reset_index(drop=True)
        data = gpd.GeoDataFrame(geopan,crs="EPSG:4326")
        self.boundary = data['geometry'].total_bounds

        return data

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

        vendors = kwargs.get('tile', self.tiles_listing[0])
        provider = None
        if vendors in self.tiles_listing:
            provider = vendors
        else:
            raise CoaTypeError('Don\'t know which you want to load ...')

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

    def standardfig(self,dbname=None,copyrightposition='right',**kwargs):
         """
         Create a standard Bokeh figure, with pycoa.frlabel,used in all the bokeh charts
         """
         fig=figure(**kwargs, plot_width=self.plot_width,plot_height=self.plot_height,
         tools=['save','box_zoom,reset'],toolbar_location="right")
         if copyrightposition == 'right':
             xpos=0.6
         elif  copyrightposition == 'left':
            xpos=0.03
         else:
            CoaKeyError('copyrightposition argument not yet implemented ...')
         textcopyright='©pycoa.fr (data from: {})'.format(self.database_name)
         self.logo_db_citation = Label(x=xpos*self.plot_width-len(textcopyright), y=0.01*self.plot_height,
         x_units='screen', y_units='screen',text_font_size='1.5vh',background_fill_color='white', background_fill_alpha=.75,
          text=textcopyright)
         fig.add_layout(self.logo_db_citation)
         return fig

    @staticmethod
    def dict_shorten_loc(location):
        '''
        return a shorten name location
        if location add , then location is the string before ,
        else: return 10 caracters name with ...
        '''
        a={}
        if type(location) == str:
            location=[location]
        for i in location:
            if len(i)<10:
                a[i]=i
            else:
                if i.find(',') != -1:
                   a[i]=i.split(',')[0]
                else:
                   tmp=i.replace('(','').replace(')','')
                   tmp=tmp[0:4]+'...'+tmp[-3:]
                   a[i]=tmp
        return a

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
            location_ordered_byvalues=list(mypandas.loc[mypandas.date==dico['when_end']].sort_values(by=input_field,ascending=False)['location'])
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'
            loc = location_ordered_byvalues#mypandas['location'].unique()
            shorten_loc = list(CocoDisplay.dict_shorten_loc(loc).values())
            for i in input_field:
                dict_filter_data[i] =  \
                    dict(mypandas.loc[(mypandas['location'].isin(loc)) &
                                     (mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end']) ].groupby('location').__iter__())

                for j in range(len(loc)):
                    dict_filter_data[i][shorten_loc[j]] = dict_filter_data[i].pop(loc[j])
            list_max=[]
            for i in input_field:
                [list_max.append(max(value.loc[value.location.isin(loc)][i])) for key,value in dict_filter_data[i].items()]

            if len([x for x in list_max if not np.isnan(x)])>0:
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
            shorten_loc = list(CocoDisplay.dict_shorten_loc(loc).values())


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

    @staticmethod
    def changeto_nonan_date(df=None,when_end=None,field=None):
        boolval=True
        j=0
        while(boolval == True):
                boolval = df.loc[df.date == (when_end-dt.timedelta(days=j))][field].dropna().empty
                j+=1
        if j>1:
            info(str(when_end)+'all the value seems to be nan! I will find an other previous date.\n'+
                'Here the date I will take: '+str(when_end-dt.timedelta(days=j-1)))
        return  when_end-dt.timedelta(days=j-1)

    @staticmethod
    def get_utcdate(date):
        return (date-dt.date(1970, 1, 1)).total_seconds()*1000.

    @staticmethod
    def test_all_val_null(s):
            a = s.to_numpy()
            return ( a == 0).all()

    def decohistomap(func):
        def generic_hm(self,mypandas,input_field = None,cursor_date = None, **kwargs):
            mypandas,dico = self.standard_input(mypandas,input_field,**kwargs,plot_last_date=True)

            if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
               input_field = mypandas.columns[2]
            else:
                if type(input_field) is None.__class__:
                    input_field = dico['var_displayed']
                else:
                    input_field = dico['input_field'][0]
            if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
                name_location_displayed = 'town_subregion'
            else:
                name_location_displayed = 'location'

            my_date = mypandas.date.unique()
            my_location = mypandas.location.unique()
            dshort_loc=CocoDisplay.dict_shorten_loc(my_location)
            colors = itertools.cycle(self.colors)
            dico_colors = {i:next(colors) for i in my_location}
            mypandas['colors']=[dico_colors[i] for i in mypandas.location ]

            if self.database_name == 'jhu' or self.database_name == 'owid':
                if len(geopdwd_filter.location.unique())>30:
                    geopdwd_filter = geopdwd_filter.iloc[0:30].reset_index(drop=True)
                    geopdwd = geopdwd.loc[geopdwd.location.isin(geopdwd_filter.location.unique())]

            if func.__name__ == 'map_folium' or func.__name__ == 'bokeh_map':
                self.location_geometry = self.get_geodata(database=self.database_name,)
                self.all_location_indb = self.location_geometry.location.unique()
                geopdwd = self.location_geometry
                geopdwd = pd.merge(geopdwd,mypandas,on='location')
                if self.database_name == 'spf' or self.database_name == 'opencovid19':
                    domtom=["971","972","973","974","975","976","977","978","984","986","987","988","989"]
                    self.boundary = geopdwd.loc[~geopdwd.location.isin(domtom)]['geometry'].total_bounds
            else:
                geopdwd = mypandas
            geopdwd =  geopdwd.loc[geopdwd.date >= dt.date(2020,3,15)] # before makes pb in horizohisto
            geopdwd = geopdwd.sort_values(by=input_field,ascending=False)


            geopdwd=geopdwd.dropna(subset=[input_field])
            geopdwd=geopdwd.reset_index(drop=True)

            geopdwd = geopdwd.rename(columns={input_field:'cases'})
            orientation = kwargs.get('orientation', 'horizontal')
            date_slider = DateSlider(title="Date: ", start=geopdwd.date.min(), end=dico['when_end'],
            value=dico['when_end'], step=24*60*60*1000,orientation=orientation)
            geopdwd_filter = geopdwd.copy()
            wanted_date = date_slider.value_as_datetime.date()
            geopdwd_filter = geopdwd_filter.loc[geopdwd_filter.date == wanted_date]
            geopdwd_filter = geopdwd_filter.drop(columns=['date'])
            geopdwd_filter = geopdwd_filter.reset_index(drop=True)


            if func.__name__ == 'pycoa_horizonhisto':
                geopdwd_filter['bottom']=geopdwd_filter.index
                geopdwd_filter['left']=[0]*len(geopdwd_filter.index)
                bthick=0.95
                geopdwd_filter['top']=[len(geopdwd_filter.index)+bthick/2-i for i in geopdwd_filter.index.to_list()]
                geopdwd_filter['bottom']=[len(geopdwd_filter.index)-bthick/2-i for i in geopdwd_filter.index.to_list()]
            if cursor_date == None:
                date_slider = None

            #geopdwd['location_shorten']=[dshort_loc[i] for i in geopdwd.location.to_list() ]
            #geopdwd_filter['location_shorten']=[dshort_loc[i] for i in geopdwd_filter.location.to_list() ]
            return func(self,input_field,date_slider,name_location_displayed,dico,geopdwd,geopdwd_filter)
        return generic_hm

    @decohistomap
    def pycoa_histo(self,input_field,date_slider,name_location_displayed,dico,geopdwd,geopdwd_filter):
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
        mypandas = geopdwd_filter.rename(columns={'cases':input_field})

        dict_histo = defaultdict(list)
        if 'location' in mypandas.columns:
            tooltips='Value at around @middle_bin : @val'
            loc = mypandas['location'].unique()
            shorten_loc = list(CocoDisplay.dict_shorten_loc(loc).values())
            val_per_country = defaultdict(list)

            for w in loc:
                val=mypandas.loc[mypandas.location == w][input_field]
                histo,edges = np.histogram(val,density=False, bins=dico['bins'])
                val_per_country[w]=val.values
                dict_histo[w] = pd.DataFrame({'location':w,'val': histo,
                   'left': edges[:-1],
                   'right': edges[1:],
                   'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2)})

            for j in range(len(loc)):
                dict_histo[shorten_loc[j]] = dict_histo.pop(loc[j])

            tooltips = 'Contributors : @contributors'
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
              'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2),'contributors':contributors})
        hover_tool = HoverTool(tooltips=tooltips)
        panels = []
        bottom=0
        for axis_type in ["linear", "linlog", "loglog"]:
            x_axis_type,y_axis_type,axis_type_title=3*['linear']
            if axis_type == 'linlog':
                y_axis_type,axis_type_title = 'log','log'
            if axis_type == 'loglog':
                x_axis_type,y_axis_type = 'log','log'
                axis_type_title = 'loglog'
            standardfig = self.standardfig(x_axis_type=x_axis_type,y_axis_type=y_axis_type)
            standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            #standardfig.title.text = dico['titlebar']
            standardfig.add_tools(hover_tool)
            colors = itertools.cycle(self.colors)
            standardfig.x_range=Range1d(0, 1.05*max(edges))
            standardfig.y_range=Range1d(0, 1.05*max(frame_histo['val']))
            if x_axis_type=="log":
                left=0.8
                if min(frame_histo['left'])>0:
                    left=min(frame_histo['left'])
                standardfig.x_range=Range1d(left, 1.05*max(edges))
            if y_axis_type=="log":
                bottom=0.0001
                standardfig.y_range=Range1d(0.001, 1.05*max(frame_histo['val']))

            label = dico['titlebar']
            p=standardfig.quad(source=ColumnDataSource(frame_histo),top='val', bottom=bottom, left='left', right='right',
            fill_color=next(colors),legend_label=label)
            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig , title=axis_type_title)
            panels.append(panel)
            CocoDisplay.bokeh_legend(standardfig)

        tabs = Tabs(tabs=panels)
        return tabs

    @decohistomap
    def pycoa_horizonhisto(self,input_field,date_slider,name_location_displayed,dico,geopdwd,geopdwd_filter):
        ''' Horizontal histogram  '''
        if date_slider:
            title = input_field
            input_field = 'cases'
        else:
            geopdwd = geopdwd.rename(columns={'cases':input_field})
            geopdwd_filter = geopdwd_filter.rename(columns={'cases':input_field})

        dshort_loc=CocoDisplay.dict_shorten_loc(geopdwd.location.unique())
        geopdwd['location']=[dshort_loc[i] for i in geopdwd.location.to_list()]
        geopdwd_filter['location']=[dshort_loc[i] for i in geopdwd_filter.location.to_list()]

        my_date = geopdwd.date.unique()
        dico_utc={i:DateSlider(value=i).value for i in my_date}
        geopdwd['date_utc']=[dico_utc[i] for i in geopdwd.date]
        source = ColumnDataSource(data=geopdwd)

        mypandas_filter = geopdwd_filter
        mypandas_filter = mypandas_filter.sort_values(by=input_field,ascending=False)

        srcfiltered = ColumnDataSource(data=mypandas_filter)
        max_value = geopdwd[input_field].max()
        min_value = geopdwd[input_field].min()
        min_value_gt0 = geopdwd[geopdwd[input_field]>0][input_field].min()

        tooltips = [('Location','@location'),('Cases','@'+input_field)]
        hover_tool = HoverTool(tooltips=tooltips)
        panels = []
        for axis_type in ["linear", "log"]:
            label = dico['titlebar']
            title = input_field
            standardfig = self.standardfig(x_axis_type=axis_type,x_range = (0.01,1.05*max_value), title=title)

            if axis_type=="log":
                min_range_val=0.01
                if min_value>=0:
                    min_range_val=10**np.floor(np.log10(min_value_gt0))
                standardfig.x_range=Range1d(min_range_val, 1.05*max_value)
                mypandas_filter['left']=[0.001]*len(mypandas_filter.index)
                srcfiltered = ColumnDataSource(data=mypandas_filter)

            standardfig.quad(source=srcfiltered,
            top='top', bottom='bottom',left='left', right=input_field,color='colors')

            if False:
                for xi,yi,ti in zip(mypandas[input_field].to_list(), mypandas['top'].to_list(),customed):
                    customed_histobar = Label(x=xi, y=yi,text=ti)
                    standardfig.add_layout(customed_histobar)

            if date_slider :
                date_slider.orientation='vertical'
                date_slider.height=int(0.8*self.plot_height)
                callback = CustomJS(args=dict(source=source,
                                              source_filter=srcfiltered,
                                                  date_slider=date_slider,
                                                  ylabel=standardfig.yaxis[0]),
                        code="""
                        var date_slide = date_slider.value;
                        var dates = source.data['date_utc'];
                        var val = source.data['cases'];
                        var loc = source.data['location'];
                        var colors = source.data['colors'];
                        var newval = [];
                        var newloc = [];
                        var newcol = [];
                        var labeldic = {};

                        for (var i = 0; i <= dates.length; i++){
                        if (dates[i] == date_slide){
                            newval.push(parseFloat(val[i]));
                            newloc.push(loc[i]);
                            newcol.push(colors[i]);
                            }
                        }
                        var len = newval.length;
                        var indices = new Array(len);
                        for (var i = 0; i < len; ++i) indices[i] = i;
                        indices.sort(function (a, b) { return newval[a] > newval[b] ? -1 : newval[a] < newval[b] ? 1 : 0; });
                        var orderval = [];
                        var orderloc = [];
                        var ordercol = [];
                        for (var i = 0; i < len; ++i)
                        {
                            orderval.push(newval[indices[i]]);
                            orderloc.push(newloc[indices[i]]);
                            ordercol.push(newcol[indices[i]]);
                            labeldic[len-indices[i]] = newloc[indices[i]];
                        }
                        console.log('Begin');
                        console.log(labeldic);
                        console.log('END');

                        source_filter.data['cases'] = orderval;
                        source_filter.data['location'] = orderloc;
                        source_filter.data['colors'] = ordercol;
                        ylabel.major_label_overrides = labeldic
                        source_filter.change.emit();
                    """)
                date_slider.js_on_change('value', callback)
            loc=mypandas_filter['location'].to_list()
            self.logo_db_citation.x_offset -= len(max(loc, key=len))
            standardfig.add_tools(hover_tool)
            standardfig.yaxis.ticker.desired_num_ticks = len(loc)

            label_dict={len(mypandas_filter)-k:v for k,v in enumerate(loc)}
            standardfig.yaxis.major_label_overrides = label_dict
            standardfig.yaxis.minor_tick_line_color = None
            panel = Panel(child=standardfig,title=axis_type)
            panels.append(panel)
        tabs = Tabs(tabs=panels)
        if date_slider:
            tabs = row(tabs,date_slider)
        return tabs

    @staticmethod
    def get_polycoords(geopandasrow):
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

    @staticmethod
    def wgs84_to_web_mercator(tuple_xy):
        ''' Take a tuple (longitude,latitude) from a coordinate reference system crs=EPSG:4326 '''
        ''' and converts it to a  longitude/latitude tuple from to Web Mercator format '''
        k = 6378137
        x = tuple_xy[0] * (k * np.pi/180.0)
        if tuple_xy[1] == -90:
            lat = -89
        else:
            lat  = tuple_xy[1]
        y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
        return x,y

    @decohistomap
    def map_folium(self,input_field,date_slider,name_location_displayed,dico,geopdwd,geopdwd_filter):
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
        if date_slider:
            input_field = 'cases'
        else:
            geopdwd = geopdwd.rename(columns={'cases':input_field})
            geopdwd_filter = geopdwd_filter.rename(columns={'cases':input_field})
        zoom = 2
        if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            self.boundary = geopdwd_filter['geometry'].total_bounds
            zoom = 5

        minx, miny, maxx, maxy = self.boundary

        mapa = folium.Map(location=[ (maxy+miny)/2., (maxx+minx)/2.], zoom_start=zoom)
        fig = Figure(width=self.plot_width, height=self.plot_height)
        fig.add_child(mapa)
        min_col,max_col=CocoDisplay.min_max_range(np.nanmin(geopdwd[input_field]),np.nanmax(geopdwd[input_field]))
        color_mapper = LinearColorMapper(palette=Viridis256, low = min_col, high = max_col,nan_color = '#d9d9d9')
        colormap = branca.colormap.LinearColormap(color_mapper.palette).scale(min_col,max_col)
        colormap.caption = 'Cases : ' + dico['titlebar']
        colormap.add_to(mapa)
        map_id = colormap.get_name()

        my_js = """
        var div = document.getElementById('legend');
        var ticks = document.getElementsByClassName('tick')
        for(var i = 0; i < ticks.length; i++){
        var values = ticks[i].textContent.replace(',','')
        val = parseFloat(values).toExponential(1).toString().replace("+", "")
        if(parseFloat(ticks[i].textContent) == 0) val = 0.
        div.innerHTML = div.innerHTML.replace(ticks[i].textContent,val);
        }
        """
        e = Element(my_js)
        html = colormap.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e
        geopdwd_filter[input_field+'scientific_format']=(['{:.3g}'.format(i) for i in geopdwd_filter[input_field]])

        map_dict = geopdwd_filter.set_index('location')[input_field].to_dict()
        if np.nanmin(geopdwd_filter[input_field]) == np.nanmax(geopdwd_filter[input_field]):
            map_dict['FakeCountry']=0.
        color_scale = LinearColormap(color_mapper.palette, vmin = min(map_dict.values()), vmax = max(map_dict.values()))

        def get_color(feature):
            value = map_dict.get(feature['properties']['location'])
            if value is None:
                return '#8c8c8c' # MISSING -> gray
            else:
                return color_scale(value)
        folium.GeoJson(
            geopdwd_filter,
            style_function=lambda x:
            {
                'fillColor': get_color(x),
                'fillOpacity': 0.8,
                'color' : None
            },
            highlight_function=lambda x: {'weight':2, 'color':'green'},
            tooltip=folium.features.GeoJsonTooltip(fields=[name_location_displayed,input_field+'scientific_format'],
                aliases=[name_location_displayed+':',input_field+":"],
                style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                        opacity: 0.2;
                        """),
                #'<div style="background-color: royalblue 0.2; color: black; padding: 2px; border: 1px solid black; border-radius: 2px;">'+input_field+'</div>'])
        ).add_to(mapa)


        W, H = (300,200)
        im = Image.new("RGBA",(W,H))
        draw = ImageDraw.Draw(im)
        msg = "©pycoa.fr (data from: {})".format(self.database_name)
        w, h = draw.textsize(msg)
        fnt = ImageFont.truetype('/Library/Fonts/Arial.ttf', 12)
        draw.text((2,0), msg, font=fnt,fill=(0, 0, 0))
        im.crop((0, 0,2*w,2*h)).save("pycoatextlogo.png", "PNG")
        FloatImage("pycoatextlogo.png", bottom=-2, left=1).add_to(mapa)

        return mapa

    @decohistomap
    def bokeh_map(self,input_field,date_slider,name_location_displayed,dico,geopdwd,geopdwd_filter):
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
        if date_slider:
            input_field = 'cases'
        else:
            geopdwd = geopdwd.rename(columns={'cases':input_field})
            geopdwd_filter = geopdwd_filter.rename(columns={'cases':input_field})
        geopdwd =   geopdwd[['location','geometry',input_field]]
        geopdwd_filter =   geopdwd_filter[['location','geometry',input_field]]

        new_poly=[]
        geolistmodified=dict()
        for index, row in geopdwd_filter.iterrows():
            split_poly=[]
            new_poly=[]
            for pt in self.get_polycoords(row):
                if type(pt) == tuple:
                    new_poly.append(CocoDisplay.wgs84_to_web_mercator(pt))
                elif type(pt) == list:
                    shifted=[]
                    for p in pt:
                        shifted.append(CocoDisplay.wgs84_to_web_mercator(p))
                    new_poly.append(sg.Polygon(shifted))
                else:
                    raise CoaTypeError("Neither tuple or list don't know what to do with \
                        your geometry description")

            if type(new_poly[0])==tuple:
               geolistmodified[row['location']]=sg.Polygon(new_poly)
            else:
               geolistmodified[row['location']]=sg.MultiPolygon(new_poly)

        ng = pd.DataFrame(geolistmodified.items(), columns=['location', 'geometry'])
        geolistmodified=gpd.GeoDataFrame({'location':ng['location'],'geometry':gpd.GeoSeries(ng['geometry'])},crs="epsg:3857")
        geopdwd_filter = geopdwd_filter.drop(columns='geometry')
        geopdwd_filter = pd.merge(geopdwd_filter,geolistmodified,on='location')

        #if self.database_name == 'spf' or  self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
        #    geopdwd_filter = geopdwd_filter.rename(columns={'location':name_location_displayed})

        #    minx, miny, maxx, maxy = geopdwd_filter['geometry'].total_bounds
        #else:
        minx, miny, maxx, maxy = self.boundary
        (minx, miny) = CocoDisplay.wgs84_to_web_mercator((minx,miny))
        (maxx, maxy) = CocoDisplay.wgs84_to_web_mercator((maxx,maxy))

        tile_provider = get_provider(dico['tile'])
        standardfig = self.standardfig(x_range=(minx,maxx), y_range=(miny,maxy),
        x_axis_type="mercator", y_axis_type="mercator",title=input_field,copyrightposition='left')
        standardfig.add_tile(tile_provider)
        min_col,max_col=CocoDisplay.min_max_range(np.nanmin(geopdwd_filter[input_field]),np.nanmax(geopdwd_filter[input_field]))
        color_mapper = LinearColorMapper(palette=Viridis256, low = min_col, high = max_col, nan_color = '#d9d9d9')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4,
                            border_line_color=None,location = (0,0), orientation = 'horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True,precision=1,power_limit_low=int(max_col))

        standardfig.add_layout(color_bar, 'below')
        json_data = json.dumps(json.loads(geopdwd_filter.to_json()))
        geopdwd_filter = GeoJSONDataSource(geojson = json_data)

        if date_slider :
            allcases_countries, allcases_dates=pd.DataFrame(),pd.DataFrame()
            allcountries_cases = (geopdwd.groupby('location')['cases'].apply(list))

            geopdwd_tmp = geopdwd.drop_duplicates(subset=['geometry'])
            geopdwd_tmp = geopdwd_tmp.drop(columns='cases')
            geopdwd_tmp = pd.merge(geopdwd_tmp,allcountries_cases,on='location')
            json_data = json.dumps(json.loads(geopdwd_tmp.to_json()))
            geopdwd_tmp = GeoJSONDataSource(geojson = json_data)

            callback = CustomJS(args=dict(source=geopdwd_tmp,
                                          source_filter=geopdwd_filter,
                                          date_slider=date_slider),
                        code="""
                        var index_max = (date_slider.end-date_slider.start)/(24*3600*1000);
                        var index = (date_slider.value-date_slider.start)/(24*3600*1000);
                        console.log(index_max);
                        var val_date = [];
                        for (var i = 0; i < source.get_length(); i++)
                        {
                            val_date.push(source.data['cases'][i][index_max-index]);
                        }
                        source_filter.data['cases'] = val_date;
                        source_filter.change.emit();
                    """)
            date_slider.js_on_change('value', callback)

        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.patches('xs','ys', source = geopdwd_filter,fill_color = {'field':input_field, 'transform' : color_mapper},
                  line_color = 'black', line_width = 0.25, fill_alpha = 1)
        cases_custom = CustomJSHover(code="""
        var value;
        if(value>0)
            return value.toExponential(2).toString();

        """)

        standardfig.add_tools(HoverTool(
        tooltips=[(name_location_displayed,'@'+name_location_displayed),(input_field,'@{'+input_field+'}'+'{custom}'),],
        formatters={name_location_displayed:'printf','@{'+input_field+'}':cases_custom,},
        point_policy="follow_mouse"))#,PanTool())
        if date_slider:
            standardfig = column(date_slider,standardfig)

        return standardfig

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
