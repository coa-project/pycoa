    # -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - february 2021
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
import collections
import itertools
import json
import io
import os
from tempfile import gettempdir
from getpass import getuser
from io import BytesIO
import base64
from datascroller import scroll

from bokeh.models import ColumnDataSource, TableColumn, DataTable,ColorBar, \
    HoverTool,BasicTicker, GeoJSONDataSource, LinearColorMapper, Label, \
    PrintfTickFormatter, BasicTickFormatter, CustomJS, CustomJSHover, Select, \
    Range1d, DatetimeTickFormatter, Legend, LegendItem,PanTool
from bokeh.models.widgets import Tabs, Panel
from bokeh.models.tickers import FixedTicker
from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Set1,Set2,Set3,Spectral,Paired,Category10,Category20,Viridis256
from bokeh.palettes import Dark2_5 as palette
from bokeh.io import export_png
from bokeh import events
from bokeh.models.widgets import DateSlider, Slider
from bokeh.tile_providers import get_provider, Vendors
from bokeh.models import WMTSTileSource
from bokeh.transform import transform

import shapely.geometry as sg

import branca.colormap
from branca.colormap import LinearColormap
from branca.element import Element, Figure
import random
import folium
from folium.plugins import FloatImage
from PIL import Image, ImageDraw, ImageFont

import matplotlib.pyplot as plt
import datetime as dt
from ast import literal_eval

width_height_default = [500,380]

class CocoDisplay():
    def __init__(self,db=None):
        verb("Init of CocoDisplay() with db="+str(db))
        self.database_name = db

        a=map(list, zip(Paired[10], Set2[8],Set3[12]))
        chain = itertools.chain(*a)
        #self.colors=[Viridis256[i] for i in random.sample(range(256),30)]
        self.lcolors = Category20[20]
        self.scolors = Category10[5]

        self.plot_width =  width_height_default[0]
        self.plot_height =  width_height_default[1]
        self.geom = []
        self.geopan = gpd.GeoDataFrame()
        self.location_geometry = None

        self.all_available_display_keys=['where','which','what','when','title_temporal','plot_height','plot_width','title','bins','var_displayed',
        'option','input','input_field','visu','plot_last_date','tile','orientation']
        self.tiles_listing=['esri','openstreet','stamen','positron']
        self.location_geometry = self.get_geodata()

    def get_geodata(self):
        '''
         Return a GeoDataFrame used in map display (see map_bokeh and map_folium)
         The output format is the following :
         geoid | location |  geometry (POLYGON or MULTIPOLYGON)
        '''
        geopan = gpd.GeoDataFrame()
        if self.database_name in ['spf','opencovid19','jhu-usa','dpc','covidtracking','covid19-india']:
            if self.database_name == 'jhu-usa' or self.database_name == 'covidtracking':
                country = 'USA'
            elif self.database_name == 'dpc':
                country = 'ITA'
            elif self.database_name == 'covid19-india':
                country = 'IND'
            else:
                country = 'FRA'
            info = coge.GeoCountry(country,dense_geometry=False)
            geopan = info.get_subregion_list()[['code_subregion','name_subregion','geometry']]
            geopan = geopan.rename(columns={'code_subregion':'location'})
        elif self.database_name == 'jhu' or self.database_name == 'owid':
            info = coge.GeoInfo()

            geom=info.get_GeoManager()
            lstd=geom.get_standard()
            geom.set_standard('name')

            allcountries = geom.get_GeoRegion().get_countries_from_region('world')
            geopan['location'] = [geom.to_standard(c)[0] for c in allcountries]

            geom.set_standard(lstd)
            # restore standard

            geopan = info.add_field(field=['geometry'],input=geopan ,geofield='location')
            geopan = geopan[geopan.location != 'Antarctica']
        else:
            raise CoaTypeError('What data base are you looking for ?')
        geopan = geopan.dropna().reset_index(drop=True)
        self.data = gpd.GeoDataFrame(geopan,crs="EPSG:4326")
        self.geopan = geopan
        self.boundary = self.data['geometry'].total_bounds
        self.location_geometry = self.data
        return self.data

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

        bins = kwargs.get('bins',10)
        if bins != 10:
            bins = bins
        input_dico['bins'] = bins

        what = kwargs.get('what', '') # cumul is the default
        input_dico['what']=what
        input_dico['locsumall']=None
        if 'location' in mypandas:
            mypandas['rolloverdisplay']=mypandas['codelocation']
            if mypandas['location'].apply(lambda x : True if type(x) == list else False).any():
                #len(x) == 3 or len(x) == 2 : we suppose that codelocation is iso3 -len=3- or int for french code region
                # For other nationnal db need to check !
                maskcountries=mypandas['codelocation'].apply(lambda x : True if type(x) == int or len(x) == 3 else False)
                mypandascountry=mypandas[maskcountries]
                mypandassumall=mypandas[~maskcountries]
                if not mypandassumall.empty:
                    copypandas= mypandassumall.copy()
                    new=mypandassumall.iloc[:1]
                    for i in mypandassumall.codelocation.unique():
                        sub = mypandassumall.loc[mypandassumall.codelocation==i]
                        copypandas = sub.copy()
                        if type(sub['location'].iloc[0])==list:
                            list_list_loc = [j for j in sub['location'].iloc[0]]
                        else:
                            list_list_loc = sub['location'].iloc[0]
                        sub = sub.drop(columns=['location'])
                        if type(list_list_loc)==str:
                            list_list_loc=[list_list_loc]
                        sub.insert(0, 'location', list_list_loc[0])
                        for i in list_list_loc[1:]:
                            copypandas['location']=i
                            sub = sub.append(copypandas)
                        if not mypandascountry.empty:
                            mypandascountry=mypandascountry.append(sub)
                        else:
                            mypandascountry=sub
                mypandas =  mypandascountry
            if self.database_name in ['spf','opencovid19','jhu-usa','dpc','covidtracking','covid19-india']:
                pd_name_displayed = self.geopan[['location','name_subregion']]
                maskcountries = mypandas['codelocation'].apply(lambda x : True if len(x) == 2 or len(x) == 3 or len(x) == 5 else False)
                mypandassumall = mypandas[~maskcountries]
                mypandascountry = mypandas[maskcountries]
                if not mypandascountry.empty:
                    mypandascountry = pd.merge(mypandascountry,pd_name_displayed,on='location',how='inner')
                    mypandascountry = mypandascountry.drop(columns='rolloverdisplay')
                    mypandascountry['rolloverdisplay'] = mypandascountry['name_subregion']
                    if not mypandassumall.empty:
                        mypandascountry=mypandascountry.append(mypandassumall)
                    mypandas = mypandascountry
            else:
                maskcountries = mypandas['codelocation'].apply(lambda x : True if len(x) == 3 else False)
                mypandassumall = mypandas[~maskcountries]
                mypandascountry = mypandas[maskcountries]
                if not mypandascountry.empty:
                    mypandascountry = mypandascountry.drop(columns='rolloverdisplay')
                    mypandascountry['rolloverdisplay'] = mypandascountry['location']
                    if not mypandassumall.empty:
                        mypandascountry=mypandascountry.append(mypandassumall)
                    mypandas = mypandascountry

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

            if not isinstance(input_dico['when_beg'],dt.date):
                raise CoaNoData("With your current cuts, there are no data to plot.")

            if input_dico['when_end'] <= input_dico['when_beg']:
                print('Requested date below available one, take',input_dico['when_beg'])
                input_dico['when_end'] = input_dico['when_beg']

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
            titlebar = str(input_field).replace('[','').replace(']','').replace('\'','') + title_temporal
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

        vendors = kwargs.get('tile', 'openstreet')
        if vendors in self.tiles_listing:
            input_dico['tile'] = vendors
        else:
            raise CoaTypeError('Don\'t know which you want to load ...')

        if title:
            titlebar = title
        input_dico['titlebar']=titlebar
        input_dico['var_displayed']=var_displayed
        input_dico['data_base'] = self.database_name
        return mypandas, input_dico

    def get_tiles(self):
        ''' Return all the tiles available in Bokeh '''
        return self.tiles_listing

    def standardfig(self,dbname=None,copyrightposition='left',**kwargs):
         """
         Create a standard Bokeh figure, with pycoa.frlabel,used in all the bokeh charts
         """
         fig=figure(**kwargs, plot_width=self.plot_width,plot_height=self.plot_height,
         tools=['save','box_zoom,reset'],toolbar_location="right")
         if copyrightposition == 'right':
             xpos=0.5
         elif  copyrightposition == 'left':
            xpos=0.08
         else:
            CoaKeyError('copyrightposition argument not yet implemented ...')

         textcopyright='©pycoa.fr (data from: {})'.format(self.database_name)
         self.logo_db_citation = Label(x=xpos*self.plot_width-len(textcopyright), y=0.01*self.plot_height,
         x_units='screen', y_units='screen',
         text_font_size='1.5vh',background_fill_color='white', background_fill_alpha=.75,
          text=textcopyright)
         fig.add_layout(self.logo_db_citation)
         return fig
###################### BEGIN Static Methods ##################
    @staticmethod
    def return_standard_location(db,name):
        if db in ['spf','opencovid19','jhu-usa','dpc','covidtracking','covid19-india'] :
            if db == 'jhu-usa' or db == 'covidtracking' :
                country = 'USA'
            elif db == 'dpc':
                country = 'ITA'
            elif db == 'covid19-india':
                country = 'IND'
            else:
                country = 'FRA'
            info = coge.GeoCountry(country,dense_geometry=False)
            if name == 'FRA' or name == 'USA' or name == 'ITA'  or name == 'IND':
                location = info.get_subregion_list()['code_subregion'].to_list()
            else:
                #location = info.get_subregions_from_list_of_region_names(name)
                location = info.get_subregions_from_region(name=name)
        elif db == 'jhu' or db == 'owid':
            geo=coge.GeoManager('name')
            geo.set_standard('name')
            location=(geo.to_standard(name,output='list',interpret_region=True))
        return location

    @staticmethod
    def get_tile(tilename,which):
        if tilename == 'openstreet':
            if which == 'map_folium':
                tile=r'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            else:
                tile=r'http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png'
        elif tilename== 'positron':
            tile = 'https://tiles.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
        elif tilename == 'esri':
            tile=r'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'
        elif tilename == 'stamen':
            tile=r'http://tile.stamen.com/toner/{z}/{x}/{y}.png'
        else:
            CoaKeyError('Don\'t know you tile ... take default one')
            tile=tile
        return tile

    @staticmethod
    def dict_shorten_loc(toshort):
        '''
            return a shorten name location
        '''
        s=[]
        if type(toshort) == np.ndarray:
            toshort=list(toshort)
            toshort = [toshort]
            s=''
        elif type(toshort) == str:
            toshort = [toshort]
            s=''
        if type(toshort) != list:
            print('That is weird ...',toshort, 'not str nor list')

        for val in toshort:
            if type(val)==list:
                val=val[0]
            if val.find(',') == -1:
                A=val
            else:
                txt=val.split(',')
                if len(txt[0])<4 and len(txt[-1])<4:
                     A=[txt[0]+'...'+txt[-1]]
                else:
                    A=txt[0][:5]+'...'+txt[-1][-5:]
            if type(s)==list:
                s.append(A)
            else:
                s=A
        return s

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
            verb(str(when_end)+': all the value seems to be nan! I will find an other previous date.\n'+
                'Here the date I will take: '+str(when_end-dt.timedelta(days=j-1)))
        return  when_end-dt.timedelta(days=j-1)

    @staticmethod
    def get_utcdate(date):
        return (date-dt.date(1970, 1, 1)).total_seconds()*1000.

    @staticmethod
    def test_all_val_null(s):
            a = s.to_numpy()
            return ( a == 0).all()

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

    @staticmethod
    def rollerJS():
        return CustomJSHover(code="""
                var value;
                 //   if(Math.abs(value)>100000 || Math.abs(value)<0.001)
                 //       return value.toExponential(2);
                 //   else
                 //       return value.toFixed(2);

                  var s=value.toPrecision(5);
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
                  return s;
                """)
###################### END Static Methods ##################

###################### BEGIN Plots ##################
    def decoplot(func):
        ''' decorator for plot purpose'''
        def generic_plot(self,mypandas,input_field = None,cursor_date = None, **kwargs):
            mypandas,dico = self.standard_input(mypandas,input_field,**kwargs)
            if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
               input_field = mypandas.columns[2]
            else:
                if type(input_field) is None.__class__:
                    input_field = [dico['var_displayed']]
                else:
                    input_field = [dico['input_field']][0]

            dict_filter_data = defaultdict(list)
            ax_type = ['linear','log']
            tooltips='Date: @date{%F} <br>  $name: @$name'

            my_location = mypandas.location.unique()
            if len(my_location) < 5:
                colors =  self.scolors
            else:
                colors =  self.lcolors
            colors = itertools.cycle(colors)
            dico_colors = {i:next(colors) for i in my_location}
            country_col = pd.DataFrame(dico_colors.items(),columns=['location', 'colors'])
            mypandas=(pd.merge(mypandas, country_col, on='location'))

            if 'location' in mypandas.columns:
                tooltips='Location: @codelocation <br> Date: @date{%F} <br>  $name: @$name'
                uniqcodeloc = mypandas.codelocation.unique()

                new=pd.DataFrame(columns=mypandas.columns)
                n=0
                for i in uniqcodeloc:
                    pos = (mypandas.loc[mypandas.codelocation==i].index)

                    if type(i)== int or len(i) == 3:
                        new =  new.append(mypandas.iloc[pos])
                    else:
                        coun=mypandas.loc[mypandas.codelocation==i]['location'].unique()
                        new = new.append(mypandas.loc[(mypandas.codelocation==i) & (mypandas.location==coun[0])])

                mypandas = new
                location_ordered_byvalues=list(mypandas.loc[mypandas.date==dico['when_end']].sort_values(by=input_field,ascending=False)['codelocation'].unique())
                mypandas = mypandas.loc[(mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end'])]
                mypandas = mypandas.copy() #needed to avoid warning
                mypandas.codelocation = pd.Categorical(mypandas.codelocation,
                        categories=location_ordered_byvalues,ordered=True)
                mypandas=mypandas.sort_values(by=['codelocation','date'])
                if len(location_ordered_byvalues)>12:
                    mypandas = mypandas.loc[mypandas.codelocation.isin(location_ordered_byvalues[:12])]

                list_max=[]
                for i in input_field:
                    list_max.append(max(mypandas.loc[mypandas.codelocation.isin(location_ordered_byvalues)][i]))

                if len([x for x in list_max if not np.isnan(x)])>0:
                    amplitude=(np.nanmax(list_max) - np.nanmin(list_max))
                    if amplitude > 10**4:
                        ax_type.reverse()

            hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})
            return func(self,mypandas, dico, input_field, hover_tool,ax_type, **kwargs)
        return generic_plot
    @decoplot
    def pycoa_plot(self,mypandas,dico,input_field, hover_tool, ax_type,**kwargs):
        panels = []
        hover_tool = None
        cases_custom = CocoDisplay.rollerJS()
        for axis_type in ax_type :
            standardfig =  self.standardfig(x_axis_label=input_field[0],
            y_axis_label=input_field[1], y_axis_type=axis_type ,title= dico['titlebar'])

            standardfig.add_tools(HoverTool(
            tooltips=[('Location','@rolloverdisplay'),('date', '@date{%F}'),(input_field[0],'@{casesx}'+'{custom}'),
            (input_field[1],'@{casesy}'+'{custom}')],
            formatters={'location':'printf','@{casesx}':cases_custom,'@{casesy}':cases_custom ,'@date': 'datetime'},
            point_policy="follow_mouse"))#,PanTool())

            if len(input_field)!=2:
                raise CoaTypeError('Two variables are needed to be plotted ... ')

            for loc in mypandas.location.unique():
                pandaloc=mypandas.loc[mypandas.location==loc].sort_values(by='date',ascending='True')
                pandaloc.rename(columns={input_field[0]:'casesx',input_field[1]:'casesy'},inplace=True)
                standardfig.line(x='casesx', y='casesy',
                source=ColumnDataSource(pandaloc), legend_label=pandaloc.codelocation.iloc[0],color=pandaloc.colors.iloc[0], line_width=3,hover_line_width=4)

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig , title=axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "top_left"
            CocoDisplay.bokeh_legend(standardfig)
        tabs = Tabs(tabs=panels)
        return tabs
    @decoplot
    def pycoa_date_plot(self,mypandas,dico,input_field, hover_tool, ax_type,**kwargs):
        panels = []

        cases_custom = CocoDisplay.rollerJS()
        for axis_type in ax_type :
            standardfig =  self.standardfig(y_axis_type=axis_type, x_axis_type='datetime',title= dico['titlebar'])
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")

            formatters={'location':'printf','@date': 'datetime'}
            tooltips=[('Location','@rolloverdisplay'),('date', '@date{%F}')]

            for val in input_field:
                for loc in mypandas.codelocation.unique():
                    if len(input_field) >1:
                        leg=loc+' '+val
                    else:
                        leg=loc

                    mypandas_filter = mypandas.loc[mypandas.codelocation == loc].reset_index(drop=True)
                    standardfig.line(x='date', y=val, source=ColumnDataSource(mypandas_filter),
                    color=mypandas_filter.colors.iloc[0],line_width=3, legend_label=CocoDisplay.dict_shorten_loc(mypandas_filter.codelocation[0]),
                    hover_line_width=4)
                tooltips.append((val,'@{'+val+'}'+'{custom}'))
                formatters['@{'+val+'}']=cases_custom

            standardfig.add_tools(HoverTool(tooltips=tooltips,formatters=formatters,
                    point_policy="follow_mouse"))#,PanTool())

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
    @decoplot
    def scrolling_menu(self,mypandas,dico,input_field, hover_tool, ax_type,**kwargs):
        if dico['locsumall'] is not None:
            raise CoaKeyError('For coherence \'locsumall\' can not be called with scrolling_menu ...')
        tooltips='Date: @date{%F} <br>  $name: @$name'
        hover_tool = HoverTool(tooltips=tooltips,formatters={'@date': 'datetime'})

        uniqloc =  mypandas.codelocation.unique().to_list()
        if 'location' in mypandas.columns:
            tooltips='Location: @location <br> Date: @date{%F} <br>  $name: @$name'

            if len(uniqloc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                    'There is no sens to use this method. See help.')
            #shorten_loc = list(CocoDisplay.dict_shorten_loc(loc).values())

        mypandas = mypandas.loc[(mypandas['date']>=dico['when_beg']) & (mypandas['date']<=dico['when_end'])]


        mypandas[input_field[0]] = mypandas[input_field[0]].astype(float)
        mypandas = mypandas[['date','codelocation',input_field[0]]]
        mypivot  = pd.pivot_table(mypandas,index='date',columns='codelocation',values=input_field[0])
        source = ColumnDataSource(mypivot)

        filter_data1 = mypivot[[uniqloc[0]]].rename(columns={uniqloc[0]: 'cases'})
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = mypivot[[uniqloc[1]]].rename(columns={uniqloc[1]: 'cases'})
        src2 = ColumnDataSource(filter_data2)

        cases_custom = CocoDisplay.rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases','@{cases}'+'{custom}'),('date', '@date{%F}')],
            formatters={'Cases':'printf','@{cases}':cases_custom,'@date': 'datetime'},
            point_policy="follow_mouse")#,PanTool())


        panels = []
        for axis_type in ax_type:
            standardfig = self.standardfig(y_axis_type=axis_type,
            x_axis_type='datetime',title= dico['titlebar'])
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            if dico['title']:
                standardfig.title.text = dico['title']
            standardfig.add_tools(hover_tool)

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

            s1, li1 = add_line(src1,uniqloc, uniqloc[0], self.scolors[0])
            s2, li2 = add_line(src2,uniqloc, uniqloc[1],  self.scolors[1])
            standardfig.add_layout(Legend(items=[li1, li2]))
            standardfig.legend.location = 'top_left'
            layout = row(column(row(s1, s2), row(standardfig)))
            panel = Panel(child=layout, title=axis_type)
            panels.append(panel)

        tabs = Tabs(tabs=panels)
        label = dico['titlebar']
        return tabs
###################### END Plots ##################
##################### BEGIN HISTOS/MAPS##################
    def decohistomap(func):
        ''' Decorator function used for histogram and map '''
        def generic_hm(self,mypandas,input_field = None,cursor_date = None, **kwargs):
            mypandas,dico = self.standard_input(mypandas,input_field,**kwargs,plot_last_date=True)
            if type(input_field) is None.__class__ and dico['which'] is None.__class__ :
               input_field = mypandas.columns[2]
            else:
                if type(input_field) is None.__class__:
                    input_field = dico['var_displayed']
                else:
                    input_field = dico['input_field'][0]

            my_date = mypandas.date.unique()
            my_location = mypandas.location.unique()
            dshort_loc=CocoDisplay.dict_shorten_loc(mypandas.codelocation.unique())
            if len(my_location)<5:
                colors = self.scolors
            else:
                colors = self.lcolors

            colors = itertools.cycle(colors)
            dico_colors = {i:next(colors) for i in my_location}
            country_col = pd.DataFrame(dico_colors.items(),columns=['location', 'colors'])
            mypandas=(pd.merge(mypandas, country_col, on='location'))

            geopdwd = mypandas
            #geopdwd =  geopdwd.loc[geopdwd.date >= dt.date(2020,3,15)] # before makes pb in horizohisto
            geopdwd = geopdwd.sort_values(by=input_field,ascending=False)

            geopdwd=geopdwd.dropna(subset=[input_field])
            geopdwd=geopdwd.reset_index(drop=True)

            geopdwd = geopdwd.rename(columns={input_field:'cases'})
            orientation = kwargs.get('orientation', 'horizontal')

            if dico['when_end'] <= geopdwd.date.min():
                started=geopdwd.date.min()
                ended=geopdwd.date.min() + dt.timedelta(days=1)
            else:
                started=geopdwd.date.min()
                ended=dico['when_end']
            date_slider = DateSlider(title="Date: ", start=started, end=ended,
            value=ended, step=24*60*60*1000,orientation=orientation)
            geopdwd_filter = geopdwd.copy()
            wanted_date = date_slider.value_as_datetime.date()
            geopdwd_filter = geopdwd_filter.loc[geopdwd_filter.date == wanted_date]
            #geopdwd_filter = geopdwd_filter.drop(columns=['date'])
            geopdwd_filter = geopdwd_filter.reset_index(drop=True)
            uniqcodeloc = geopdwd_filter.codelocation.unique()
            if func.__name__ == 'map_folium' or func.__name__ == 'bokeh_map':
                self.all_location_indb = self.location_geometry.location.unique()
                geopdwd_filter = pd.merge(geopdwd_filter,self.location_geometry,on='location')
                dico['tile'] = CocoDisplay.get_tile(dico['tile'],func.__name__)


            if func.__name__ == 'pycoa_horizonhisto' or func.__name__ == 'pycoa_histo':
                pos={}
                new=pd.DataFrame(columns=geopdwd_filter.columns)
                n=0
                for i in uniqcodeloc:
                    pos = (geopdwd_filter.loc[geopdwd_filter.codelocation==i].index[0])
                    new =  new.append(geopdwd_filter.iloc[pos])
                    if type(i) == str and len(i) != 3:
                        new.iloc[n, 0] = i
                    n+=1
                geopdwd_filter = new.reset_index(drop=True)

                if len(geopdwd_filter.codelocation.unique())>30:
                        new_loc = geopdwd_filter.codelocation.unique()[:30]
                        geopdwd_filter = geopdwd_filter.loc[geopdwd_filter.codelocation.isin(new_loc)]
                        geopdwd = geopdwd.loc[geopdwd.codelocation.isin(new_loc)]
                        geopdwd = geopdwd[:-1]
                        geopdwd_filter = geopdwd_filter[:-1]

                geopdwd_filter['bottom']=geopdwd_filter.index
                geopdwd_filter['left']=geopdwd_filter['cases']
                geopdwd_filter['right']=geopdwd_filter['cases']
                geopdwd_filter['left'] = geopdwd_filter['left'].apply(lambda x : 0 if x > 0 else x)
                geopdwd_filter['right'] = geopdwd_filter['right'].apply(lambda x : 0 if x < 0 else x)
                bthick=0.95
                geopdwd_filter['top']=[len(geopdwd_filter.index)+bthick/2-i for i in geopdwd_filter.index.to_list()]
                geopdwd_filter['bottom']=[len(geopdwd_filter.index)-bthick/2-i for i in geopdwd_filter.index.to_list()]

            if cursor_date == None:
                date_slider = None

            return func(self,input_field,date_slider,dico,geopdwd,geopdwd_filter)
        return generic_hm

    def pycoa_heatmap(self,pycoa_pandas):
        """Create a Bokeh heat map from a pandas input
        location in the column is mandatory in the pandas structure
        Keyword arguments
        -----------------
        pycoa_pandas : pandas considered
        y_axis : location
        x_axis : column name
        The values are normalized to maximun observed in the current columns
        """
        if 'location' not in pycoa_pandas.columns:
            raise CoaKeyError('location column name is not present, this is mandatory')

        def norm(col):
            return (col-col.min())/(col.max()-col.min())

        pycoa_pandas = pycoa_pandas.set_index('location')
        #pycoa_pandas = pycoa_pandas.apply(lambda x: (x-x.min())/(x.max()-x.min()))
        pycoa_pandas = pycoa_pandas.apply(lambda x: (x-x.min())/(x.max()-x.min()))
        #apply(lambda x: (x-x.min()/(x.max()-x.min())))
        #normalized_dict = { pycoa_pandas.apply(lambda x: x(x-x.min())/(x.max()-x.min()))}
        #print(pycoa_pandas['tot_dc'].apply(norm))
        pycoa_pandas.columns.name = 'data'
        pycoa_pandas = pycoa_pandas.stack().rename("value").reset_index()

        standardfig = self.standardfig(y_range=list(pycoa_pandas.location.unique()),
                                        x_range=list(pycoa_pandas.data.unique()),title= dico['titlebar'])
        standardfig.xaxis.major_label_orientation = "vertical"
        color_mapper = LinearColorMapper(palette=Viridis256, low=pycoa_pandas.value.min(), high=pycoa_pandas.value.max(), nan_color = '#ffffff')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4,\
                            border_line_color=None,location = (0,0), orientation = 'vertical', ticker=BasicTicker())
        standardfig.add_layout(color_bar, 'right')
        standardfig.rect(
        y="location",
        x="data",
        width=1,
        height=1,
        source=ColumnDataSource(pycoa_pandas),
        line_color=None,
        fill_color=transform('value', color_mapper))

        standardfig.add_tools(HoverTool(
        tooltips=[('location','@rolloverdisplay'),('value','@value')],
        #formatters={'location':'printf','@{'+input_field+'}':cases_custom,},
        point_policy="follow_mouse"))
        return standardfig

    @decohistomap
    def pycoa_histo(self,input_field,date_slider,dico,geopdwd,geopdwd_filter):
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
            uniqloc = list(mypandas.codelocation.unique())
            shorten_loc = CocoDisplay.dict_shorten_loc(uniqloc)
            val_per_country = defaultdict(list)
            if len(uniqloc) == 1:
                dico['bins'] = 2
            for w in uniqloc:
                val=mypandas.loc[mypandas.codelocation == w][input_field]
                histo,edges = np.histogram(val,density=False, bins=dico['bins'])
                val_per_country[w]=val.values[0]
                dict_histo[w] = pd.DataFrame({'location':w,'val': histo,
                   'left': edges[:-1],
                   'right': edges[1:],
                   'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2)})

            for j in range(len(uniqloc)):
                dict_histo[shorten_loc[j]] = dict_histo.pop(uniqloc[j])

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
                   name_dis=mypandas.loc[mypandas.codelocation.isin(res)]['rolloverdisplay'].values
                   contributors.append(name_dis)

            colors = itertools.cycle(self.scolors)
            lcolors = [next(colors) for i in range(bins)]

            frame_histo = pd.DataFrame({'val': histo,'left': edges[:-1],'right': edges[1:],
              'middle_bin':np.floor(edges[:-1]+(edges[1:]-edges[:-1])/2),'contributors':contributors,
              'colors':lcolors})
        hover_tool = HoverTool(tooltips=tooltips)
        panels = []
        bottom=0
        x_axis_type,y_axis_type,axis_type_title=3*['linear']
        for axis_type in ["linear", "linlog", "loglin", "loglog"]:
            if axis_type == 'linlog':
                y_axis_type,axis_type_title = 'log','logy'
            if axis_type == 'loglin':
                x_axis_type,y_axis_type,axis_type_title = 'log','linear','logx'
            if axis_type == 'loglog':
                x_axis_type,y_axis_type = 'log','log'
                axis_type_title = 'loglog'
            standardfig = self.standardfig(x_axis_type=x_axis_type,y_axis_type=y_axis_type,title= dico['titlebar'])
            standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            #standardfig.title.text = dico['titlebar']
            standardfig.add_tools(hover_tool)
            standardfig.x_range=Range1d(0, 1.05*max(edges))
            standardfig.y_range=Range1d(0, 1.05*max(frame_histo['val']))
            if x_axis_type=="log":
                left=0.8
                if frame_histo['left'][0]>0:
                    left=frame_histo['left'][0]
                standardfig.x_range=Range1d(left, 1.05*max(edges))
            if y_axis_type=="log":
                bottom=0.0001
                standardfig.y_range=Range1d(0.001, 1.05*max(frame_histo['val']))

            label = dico['titlebar']

            p=standardfig.quad(source=ColumnDataSource(frame_histo),top='val', bottom=bottom, left='left', right='right',
            fill_color='colors',legend_label=label)
            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig , title=axis_type_title)
            panels.append(panel)
            CocoDisplay.bokeh_legend(standardfig)

        tabs = Tabs(tabs=panels)
        return tabs

    @decohistomap
    def pycoa_horizonhisto(self,input_field,date_slider,dico,geopdwd,geopdwd_filter):
        ''' Horizontal histogram  '''
        title_fig = input_field
        if date_slider:
            input_field = 'cases'
        else:
            geopdwd = geopdwd.rename(columns={'cases':input_field})
            geopdwd_filter = geopdwd_filter.rename(columns={'cases':input_field})

        my_date = geopdwd.date.unique()
        dico_utc={i:DateSlider(value=i).value for i in my_date}
        geopdwd['date_utc']=[dico_utc[i] for i in geopdwd.date]
        source = ColumnDataSource(data=geopdwd)

        mypandas_filter = geopdwd_filter
        mypandas_filter = mypandas_filter.sort_values(by=input_field,ascending=False)
        srcfiltered = ColumnDataSource(data=mypandas_filter)
        max_value = mypandas_filter[input_field].max()
        min_value = mypandas_filter[input_field].min()
        min_value_gt0 = mypandas_filter[mypandas_filter[input_field]>0][input_field].min()

        panels = []

        for axis_type in ["linear", "log"]:
            title = dico['titlebar']
            if title_fig != title.split()[0]:
                title =  title_fig + ' ' + title
            if mypandas_filter[mypandas_filter[input_field]<0.].empty:
                standardfig = self.standardfig(x_axis_type=axis_type,x_range = (0.01,1.05*max_value), title=dico['titlebar'])
                standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
                if axis_type=="log":
                    min_range_val=0.01
                    if min_value>=0:
                        min_range_val=10**np.floor(np.log10(min_value_gt0))
                    standardfig.x_range=Range1d(min_range_val, 1.05*max_value)
                    standardfig.y_range=Range1d(min(mypandas_filter['bottom']), max(mypandas_filter['top']))
                    mypandas_filter['left']=[0.001]*len(mypandas_filter.index)
                    srcfiltered = ColumnDataSource(data=mypandas_filter)
            else:
                max_value = max(np.abs(mypandas_filter['left']).max(),mypandas_filter['right'].max())
                standardfig = self.standardfig(x_axis_type=axis_type,x_range = (-max_value,max_value), title= dico['titlebar'])

            standardfig.quad(source=srcfiltered,
                top='top', bottom='bottom',left='left', right='right',color='colors',line_color='black',
                line_width=1,hover_line_width=2)

            if date_slider and mypandas_filter[mypandas_filter[input_field]<0].empty:
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
                        var shortloc = source.data['codelocation'];
                        var colors = source.data['colors'];
                        var newval = [];
                        var newloc = [];
                        var newcol = [];
                        var newshortenloc = [];
                        var labeldic = {};

                        for (var i = 0; i <= dates.length; i++){
                        if (dates[i] == date_slide){
                            newval.push(parseFloat(val[i]));
                            newloc.push(loc[i]);
                            newshortenloc.push(shortloc[i]);
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
                            labeldic[len-indices[i]] = newshortenloc[indices[i]];
                        }
                        console.log('Begin');
                        console.log(labeldic);
                        console.log('END');

                        source_filter.data['cases'] = orderval;
                        source_filter.data['right'] = orderval;
                        source_filter.data['location'] = orderloc;
                        source_filter.data['colors'] = ordercol;
                        ylabel.major_label_overrides = labeldic;
                        source_filter.change.emit();
                    """)
                date_slider.js_on_change('value', callback)

            #if dico['locsumall'] is None:
            #    if self.database_name == 'spf' or self.database_name == 'opencovid19' or self.database_name == 'jhu-usa':
            #        mypandas_filter = mypandas_filter.drop(columns=['shortenlocation'])
            #        mypandas_filter['shortenlocation'] = mypandas_filter['location']
            #    else:
            #        mypandas_filter = mypandas_filter.drop(columns=['shortenlocation'])
            #        mypandas_filter['shortenlocation'] = mypandas_filter['codelocation']
            #loc=mypandas_filter['shortenlocation'].to_list()
            loc=mypandas_filter['codelocation'].to_list()

            loc=CocoDisplay.dict_shorten_loc(loc)
            cases_custom = CocoDisplay.rollerJS()
            standardfig.add_tools(HoverTool(
            tooltips=[('Location','@rolloverdisplay'),(input_field,'@{'+input_field+'}'+'{custom}'),],
            formatters={'location':'printf','@{'+input_field+'}':cases_custom,},
            point_policy="follow_mouse"))#,PanTool())

            label_dict={len(mypandas_filter)-k:v for k,v in enumerate(loc)}
            if dico['locsumall'] is not None:
                iamthelegend=dico['locsumall']['codelocation'][0]
                if len(iamthelegend)>20:
                    del label_dict
                    label_dict={}
                    label_dict[1]=iamthelegend.split()[0] + '...' + iamthelegend.split()[-1]

            standardfig.yaxis.major_label_overrides = label_dict
            standardfig.yaxis.ticker = list(range(1,len(loc)+1))
            panel = Panel(child=standardfig,title=axis_type)
            panels.append(panel)

        tabs = Tabs(tabs=panels)
        if date_slider:
            if mypandas_filter[mypandas_filter[input_field]<0].empty:
                tabs = row(tabs,date_slider)
            else:
                print('Cursor date not implemented for negative value, sorry about that ...')
        return tabs

    @decohistomap
    def map_folium(self,input_field,date_slider ,dico,geopdwd,geopdwd_filter):
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
        geopdwd_filter = gpd.GeoDataFrame(geopdwd_filter , geometry = geopdwd_filter.geometry,crs="EPSG:4326")
        if date_slider:
            input_field = 'cases'
        else:
            geopdwd = geopdwd.rename(columns={'cases':input_field})
            geopdwd_filter = geopdwd_filter.rename(columns={'cases':input_field})
        zoom = 2
        if self.database_name in ['spf','opencovid19','jhu-usa','dpc','covidtracking','covid19-india']:
            self.boundary = geopdwd_filter['geometry'].total_bounds
            name_location_displayed = 'name_subregion'
            zoom = 2
        uniqloc = list(geopdwd_filter.codelocation.unique())
        geopdwd_filter = geopdwd_filter.drop(columns=['date','colors'])

        minx, miny, maxx, maxy = self.boundary

        msg = "(data from: {})".format(self.database_name)
        mapa = folium.Map(location=[ (maxy+miny)/2., (maxx+minx)/2.], zoom_start=zoom,
            tiles=dico['tile'],attr='<a href=\"http://pycoa.fr\"> ©pycoa.fr </a>'+msg)#

        fig = Figure(width=self.plot_width, height=self.plot_height)
        fig.add_child(mapa)
        min_col,max_col=CocoDisplay.min_max_range(np.nanmin(geopdwd_filter[input_field]),np.nanmax(geopdwd_filter[input_field]))

        color_mapper = LinearColorMapper(palette=Viridis256, low = min_col, high = max_col,nan_color = '#d9d9d9')
        colormap = branca.colormap.LinearColormap(color_mapper.palette).scale(min_col,max_col)
        colormap.caption = 'Cases : ' + dico['titlebar']
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
        geopdwd_filter[input_field+'scientific_format']=\
        (['{:.5g}'.format(i) for i in geopdwd_filter[input_field]])
        #(['{:.3g}'.format(i) if i>100000 else i for i in geopdwd_filter[input_field]])


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

        if len(uniqloc)>1:
                displayed='rolloverdisplay'
        else:
               displayed='codelocation'

        folium.GeoJson(
            geopdwd_filter,
            style_function=lambda x:
            {
                'fillColor': get_color(x),
                'fillOpacity': 0.8,
                'color' : None
            },
            highlight_function=lambda x: {'weight':2, 'color':'green'},
            tooltip=folium.features.GeoJsonTooltip(fields=[displayed,input_field+'scientific_format'],
                aliases=['location'+':',input_field+":"],
                style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                        opacity: 0.2;
                        """),
                #'<div style="barialckground-color: royalblue 0.2; color: black; padding: 2px; border: 1px solid black; border-radius: 2px;">'+input_field+'</div>'])
            ).add_to(mapa)

        return mapa

    @decohistomap
    def bokeh_map(self,input_field,date_slider,dico,geopdwd,geopdwd_filter):
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
        uniqloc= list(geopdwd_filter.codelocation.unique())
        #geopdwd = geopdwd[['location','codelocation','geometry','date',input_field]]
        #geopdwd_filter =   geopdwd_filter[['location','codelocation','geometry',input_field]]

        geopdwd = geopdwd.sort_values(by=['location','date'],ascending=False)
        geopdwd = geopdwd.drop(columns=['date'])
        geopdwd_filter = geopdwd_filter.drop(columns=['date','colors'])

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
        geopdwd_filter = pd.merge(geolistmodified,geopdwd_filter,on='location')

        minx, miny, maxx, maxy = self.boundary
        (minx, miny) = CocoDisplay.wgs84_to_web_mercator((minx,miny))
        (maxx, maxy) = CocoDisplay.wgs84_to_web_mercator((maxx,maxy))

        wmt=WMTSTileSource(
        url=dico['tile']
        )
        standardfig = self.standardfig(x_range=(minx,maxx), y_range=(miny,maxy),
        x_axis_type="mercator", y_axis_type="mercator",title=dico['titlebar'],copyrightposition='left')
        standardfig.add_tile(wmt)
        min_col,max_col=CocoDisplay.min_max_range(np.nanmin(geopdwd_filter[input_field]),np.nanmax(geopdwd_filter[input_field]))
        color_mapper = LinearColorMapper(palette=Viridis256, low = min_col, high = max_col, nan_color = '#ffffff')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4,
                            border_line_color=None,location = (0,0), orientation = 'horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True,precision=1,power_limit_low=int(max_col))
        standardfig.add_layout(color_bar, 'below')
        json_data = json.dumps(json.loads(geopdwd_filter.to_json()))
        geopdwd_filter = GeoJSONDataSource(geojson = json_data)
        if date_slider :
            allcases_location, allcases_dates=pd.DataFrame(),pd.DataFrame()
            allcases_location = (geopdwd.groupby('location')['cases'].apply(list))
            geopdwd_tmp = geopdwd.drop_duplicates(subset=['codelocation'])
            geopdwd_tmp = geopdwd_tmp.drop(columns='cases')
            geopdwd_tmp = pd.merge(geopdwd_tmp,allcases_location,on='location')
            geopdwd_tmp = pd.merge(geolistmodified,geopdwd_tmp,on='location')
            json_data = json.dumps(json.loads(geopdwd_tmp.to_json()))
            geopdwd_tmp = GeoJSONDataSource(geojson = json_data)
            callback = CustomJS(args=dict(source=geopdwd_tmp,
                                          source_filter=geopdwd_filter,
                                          date_slider=date_slider),
                        code="""
                        var ind_date_max = (date_slider.end-date_slider.start)/(24*3600*1000);
                        var ind_date = (date_slider.value-date_slider.start)/(24*3600*1000);
                        var val_cases = [];
                        var val_loc = [];
                        var val_ind = [];
                        var dict = {};

                        console.log('BEGIN');
                        for (var i = 0; i < source.get_length(); i++)
                        {
                            dict[source.data['location'][i]]=source.data['cases'][i][ind_date_max-ind_date];
                        }
                        var val_cases = [];
                        for(var i = 0; i < source_filter.get_length();i++)
                        {
                            for(var key in dict) {
                                if(source_filter.data['location'][i] == key)
                                {
                                val_cases.push(dict[key]);
                                break;
                                }
                            }
                        }
                        source_filter.data['cases']=val_cases;
                        console.log(val_cases)
                        source_filter.change.emit();
                    """)
            date_slider.js_on_change('value', callback)
        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.patches('xs','ys', source = geopdwd_filter,fill_color = {'field':input_field, 'transform' : color_mapper},
                  line_color = 'black', line_width = 0.25, fill_alpha = 1)
        cases_custom = CocoDisplay.rollerJS()
        if len(uniqloc)>1:
            loctips=('location','@rolloverdisplay')
        else:
           loctips=('location','@codelocation')

        standardfig.add_tools(HoverTool(
        tooltips=[loctips,(input_field,'@{'+input_field+'}'+'{custom}'),],
        formatters={'location':'printf','@{'+input_field+'}':cases_custom,},
        point_policy="follow_mouse"))#,PanTool())
        if date_slider:
            standardfig = column(date_slider,standardfig)

        return standardfig
##################### END HISTOS/MAPS##################

#### NOT YET IMPLEMENTED WITH THIS CURRENT VERSION ... TO DO ...
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
