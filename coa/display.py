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

from bokeh.models import ColumnDataSource, TableColumn, DataTable, ColorBar, \
    HoverTool, BasicTicker, GeoJSONDataSource, LinearColorMapper, Label, \
    PrintfTickFormatter, BasicTickFormatter, CustomJS, CustomJSHover, Select, \
    Range1d, DatetimeTickFormatter, Legend, LegendItem, Text
from bokeh.models.widgets import Tabs, Panel
from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Category10, Category20, Viridis256

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

width_height_default = [500, 380]


class CocoDisplay:
    def __init__(self, db=None, geo = None):
        verb("Init of CocoDisplay() with db=" + str(db))
        self.database_name = db
        self.dbld = get_db_list_dict()
        self.lcolors = Category20[20]
        self.scolors = Category10[5]
        self.plot_width = width_height_default[0]
        self.plot_height = width_height_default[1]
        self.geom = []
        self.geopan = gpd.GeoDataFrame()
        self.location_geometry = None
        self.boundary_metropole = None

        self.all_available_display_keys = ['where', 'which', 'what', 'when', 'title_temporal', 'plot_height',
                                           'plot_width', 'title', 'bins', 'var_displayed','textcopyright',
                                           'option', 'input', 'input_field', 'visu', 'plot_last_date', 'tile',
                                           'orientation','mode','full_legend']
        self.tiles_listing = ['esri', 'openstreet', 'stamen', 'positron']
        try:
            if self.dbld[self.database_name][0] != 'WW' :
                self.geo=coge.GeoCountry(self.dbld[self.database_name][0])
                country = self.dbld[self.database_name][0]
                #self.boundary = geo['geometry'].total_bounds
                if self.dbld[self.database_name][1] == 'region':
                    self.location_geometry = geo.get_region_list()[['code_region', 'name_region', 'geometry']]
                    self.location_geometry = self.location_geometry.rename(columns={'name_region': 'location'})
                    if self.dbld[self.database_name][0] == 'PRT':
                         tmp=self.location_geometry.rename(columns={'name_region': 'location'})
                         tmp = tmp.loc[tmp.code_region=='PT.99']
                         self.boundary_metropole =tmp['geometry'].total_bounds
                    if self.dbld[self.database_name][0] == 'FRA':
                         tmp=self.location_geometry.rename(columns={'name_region': 'location'})
                         tmp = tmp.loc[tmp.code_region=='999']
                         self.boundary_metropole =tmp['geometry'].total_bounds

                elif self.dbld[self.database_name][1] == 'subregion':
                    list_dep_metro = None
                    self.location_geometry = geo.get_subregion_list()[['code_subregion', 'name_subregion', 'geometry']]
                    self.location_geometry = self.location_geometry.rename(columns={'name_subregion': 'location'})
                    if self.dbld[self.database_name][0] == 'FRA':
                         list_dep_metro =  geo.get_subregions_from_region(name='Métropole')
                    elif self.dbld[self.database_name][0] == 'ESP':
                         list_dep_metro =  geo.get_subregions_from_region(name='España peninsular')
                    if list_dep_metro:
                        self.boundary_metropole = self.location_geometry.loc[self.location_geometry.code_subregion.isin(list_dep_metro)]['geometry'].total_bounds
            else:
                   self.geo=coge.GeoManager('name')
                   geopan = gpd.GeoDataFrame()#crs="EPSG:4326")
                   info = coge.GeoInfo()
                   allcountries = geo.get_GeoRegion().get_countries_from_region('world')
                   geopan['location'] = [geo.to_standard(c)[0] for c in allcountries]
                   geopan = info.add_field(field=['geometry'],input=geopan ,geofield='location')
                   geopan = gpd.GeoDataFrame(geopan, geometry=geopan.geometry, crs="EPSG:4326")
                   geopan = geopan[geopan.location != 'Antarctica']
                   geopan = geopan.dropna().reset_index(drop=True)
                   self.location_geometry  = geopan
        except:
            raise CoaTypeError('What data base are you looking for ?')

    def standard_input(self, mypandas, input_field=None, **kwargs):
        """
        Parse a standard input, return :
            - pandas: with location keyword (eventually force a column named 'where' to 'location')
            - dico:
                * keys = [plot_width, plot_width, titlebar, when, title_temporal,bins, what, which, var_displayed]
        Note that method used only the needed variables, some of them are useless
        """
        input_dico = {}
        if 'where' in mypandas.columns:
            mypandas = mypandas.rename(columns={'where': 'location'})

        kwargs_test(kwargs, self.all_available_display_keys, 'Bad args used in the display function.')
        plot_width = kwargs.get('plot_width', self.plot_width)
        plot_height = kwargs.get('plot_height', self.plot_height)
        if plot_width != self.plot_width:
            self.plot_width = plot_width
        if plot_height != self.plot_height:
            self.plot_height = plot_height
        input_dico['plot_width'] = plot_width
        input_dico['plot_height'] = plot_height

        bins = kwargs.get('bins', 10)
        if bins != 10:
            bins = bins
        input_dico['bins'] = bins

        what = kwargs.get('what', '')  # cumul is the default
        input_dico['what'] = what

        if 'location' in mypandas:
            which = mypandas.columns[2]
        else:
            which = mypandas.columns[1]

        wallname = self.dbld[self.database_name][2]
        if self.dbld[self.database_name][0] == 'WW' :
            mypandas['codelocation'] = mypandas['codelocation'].apply(lambda x: str(x).replace('[', '').replace(']', '') if len(x)< 10 else x[0]+'...'+x[-1] )
            mypandas['permanentdisplay'] = mypandas.apply(lambda x: x.clustername if self.geo.get_GeoRegion().is_region(x.clustername) else str(x.codelocation), axis = 1)
        else:
            if self.dbld[self.database_name][1] == 'subregion' :
                if isinstance(mypandas['codelocation'][0],list):
                    mypandas['codelocation'] = mypandas['codelocation'].apply(lambda x: str(x).replace("'", '')\
                                                 if len(x)<5 else '['+str(x[0]).replace("'", '')+',...,'+str(x[-1]).replace("'", '')+']')

                trad={}
                cluster = mypandas.clustername.unique()
                if isinstance(mypandas.location[0],list):
                   cluster = [i for i in cluster]
                for i in cluster:
                    if i == self.dbld[self.database_name][2]:
                        mypandas['permanentdisplay'] = [self.dbld[self.database_name][2]]*len(mypandas)
                    else:
                        if self.geo.is_region(i):
                            trad[i] = self.geo.is_region(i)
                        elif self.geo.is_subregion(i):
                            trad[i] = self.geo.is_subregion(i)#mypandas.loc[mypandas.clustername==i]['codelocation'].iloc[0]
                        else:
                            trad[i] = i
                        trad={k:(v[:3]+'...'+v[-3:] if len(v)>8 else v) for k,v in trad.items()}
                        mypandas['permanentdisplay'] = mypandas.codelocation#mypandas.clustername.map(trad)
            elif self.dbld[self.database_name][1] == 'region' :
                if all(i == self.dbld[self.database_name][2] for i in mypandas.clustername.unique()):
                    mypandas['permanentdisplay'] = [self.dbld[self.database_name][2]]*len(mypandas)
                else:
                    mypandas['permanentdisplay'] = mypandas.codelocation
        mypandas['rolloverdisplay'] = mypandas['location']

        uniqloc = mypandas.clustername.unique()
        if len(uniqloc) < 5:
            colors = self.scolors
        else:
            colors = self.lcolors
        colors = itertools.cycle(colors)
        dico_colors = {i: next(colors) for i in uniqloc}
        mypandas = mypandas.copy()
        mypandas.loc[:,'colors'] = mypandas['clustername'].map(dico_colors)#(pd.merge(mypandas, country_col, on='location'))

        input_dico['which'] = which
        var_displayed = which
        title = kwargs.get('title', None)
        input_dico['title'] = title
        textcopyright = kwargs.get('textcopyright', 'default')
        input_dico['textcopyright'] = textcopyright
        when = kwargs.get('when', None)
        input_dico['when'] = when
        title_temporal = ''
        input_dico['when_beg'] = mypandas.date.min()

        if mypandas[which].isnull().all():
            raise CoaTypeError("Sorry all data are NaN for " + which)
        else:
            input_dico['when_end'] = mypandas.dropna(subset=[which]).date.max()
        if when:
            input_dico['when_beg'], input_dico['when_end'] = extract_dates(when)
            if input_dico['when_beg'] == dt.date(1, 1, 1):
                input_dico['when_beg'] = mypandas['date'].min()

            if input_dico['when_end'] == '':
                input_dico['when_end'] = mypandas['date'].max()

            if not isinstance(input_dico['when_beg'], dt.date):
                raise CoaNoData("With your current cuts, there are no data to plot.")

            if input_dico['when_end'] <= input_dico['when_beg']:
                print('Requested date below available one, take', input_dico['when_beg'])
                input_dico['when_end'] = input_dico['when_beg']

        when_end_change = CocoDisplay.changeto_nonull_date(mypandas, input_dico['when_end'], var_displayed)
        if when_end_change != input_dico['when_end']:
            input_dico['when_end'] = when_end_change
            mypandas = mypandas[mypandas.date <= input_dico['when_end']]

        if kwargs.get('plot_last_date', None) == True:
            title_temporal = ' (at ' + input_dico['when_end'].strftime('%d/%m/%Y') + ')'
        else:
            title_temporal = ' (' + 'between ' + input_dico['when_beg'].strftime('%d/%m/%Y') + ' and ' + input_dico['when_end'].strftime('%d/%m/%Y') + ')'

        if kwargs.get('option', '') != '':
            title_temporal = ', option ' + str(kwargs.get('option')) + title_temporal

        input_dico['title_temporal'] = title_temporal
        titlebar = which + title_temporal

        if input_field:
            if not isinstance(input_field, list):
                input_field = [input_field]
            else:
                input_field = input_field
            input_dico['input_field'] = input_field
            titlebar = str(input_field).replace('[', '').replace(']', '').replace('\'', '') + title_temporal
        else:
            if what:
                if what == 'daily':
                    titlebar = which + ', ' + 'day to day difference ' + title_temporal
                elif what == 'weekly':
                    titlebar = which + ', ' + 'week to week difference' + title_temporal
                elif what == 'cumul':
                    titlebar = which + ', ' + 'cumulative sum ' + title_temporal
                else:
                    raise CoaTypeError('what argument is not daily, daily, cumul nor weekly . See help.')
                var_displayed = what

        vendors = kwargs.get('tile', 'openstreet')
        if vendors in self.tiles_listing:
            input_dico['tile'] = vendors
        else:
            raise CoaTypeError('Don\'t know which you want to load ...')

        if title:
            titlebar = title
        input_dico['titlebar'] = titlebar
        input_dico['var_displayed'] = var_displayed
        input_dico['data_base'] = self.database_name

        return mypandas, input_dico

    def get_tiles(self):
        """ Return all the tiles available in Bokeh """
        return self.tiles_listing

    def standardfig(self, dbname = None, copyrightposition = 'left', textcopyright = 'default', **kwargs):
        """
         Create a standard Bokeh figure, with pycoa.fr label, used in all the bokeh charts
         """
        fig = figure(**kwargs, plot_width=self.plot_width, plot_height=self.plot_height,
                     tools=['save', 'box_zoom,reset'], toolbar_location="right")
        xpos = 0.
        if copyrightposition == 'right':
            xpos = 0.75
        elif copyrightposition == 'left':
            xpos = 0.08
        else:
            CoaKeyError('copyrightposition argument not yet implemented ...')

        if textcopyright == 'default':
                textcopyright = '©pycoa.fr (data from: {})'.format(self.database_name)
        else:
                textcopyright = '©pycoa.fr ' + textcopyright

        self.logo_db_citation = Label(x=xpos * self.plot_width - len(textcopyright), y=0.01 * self.plot_height,
                                          x_units='screen', y_units='screen',
                                          text_font_size='1.5vh', background_fill_color='white', background_fill_alpha=.75,
                                          text=textcopyright)
        fig.add_layout(self.logo_db_citation)
        return fig
    ###################### BEGIN Static Methods ##################
    @staticmethod
    def get_tile(tilename, which):
        tile = ''
        if tilename == 'openstreet':
            if which == 'pycoa_mapfolium':
                tile = r'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            else:
                tile = r'http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png'
        elif tilename == 'positron':
            tile = 'https://tiles.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
        elif tilename == 'esri':
            tile = r'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'
        elif tilename == 'stamen':
            tile = r'http://tile.stamen.com/toner/{z}/{x}/{y}.png'
        else:
            CoaKeyError('Don\'t know you tile ... take default one')
        return tile
    ######################
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
            raise CoaTypeError(' Not a valide data ... ')

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
            raise CoaTypeError(' Not a valide data ... ')
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
            for ea in geometry:
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
            lat = -89
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
    def add_columns_for_pie_chart(self,df,column_name):
        r = 0.9
        df = df.copy()
        column_sum = df[column_name].sum()
        df['percentage'] = (df[column_name]/column_sum)
        #(( df['percentage'] * 100 ).astype(np.double).round(2)).apply(lambda x: str(x)+'%')
        percentages = [0]  + df['percentage'].cumsum().tolist()
        df['angle'] = (df[column_name]/column_sum)*2 * np.pi
        df['starts'] = [p * 2 * np.pi for p in percentages[:-1]]
        df['ends'] = [p * 2 * np.pi for p in percentages[1:]]
        #df['middle'] = (df['starts'] + df['ends'])/2
        df['diff'] = (df['ends'] - df['starts'])
        df['middle'] = df['starts']+np.abs(df['ends']-df['starts'])/2.

        df['text_size'] = '10pt'
        df['text_angle'] = 0.
        df.loc[:, 'percentage'] = (( df['percentage'] * 100 ).astype(np.double).round(2)).apply(lambda x: str(x))
        df['textdisplayed']=df['permanentdisplay'].astype(str).str.pad(15, side = "left")
        df['textdisplayed2'] = df[column_name].astype(np.double).round(1).astype(str).str.pad(46, side = "left")
        df.loc[df['diff']<= np.pi/20,'textdisplayed']=''
        df.loc[df['diff']<= np.pi/20,'textdisplayed2']=''
        return df
    ###################### BEGIN Plots ##################
    def decoplot(func):
        """
        decorator for plot purpose
        """
        def generic_plot(self, mypandas, input_field=None, cursor_date=False, **kwargs):
            mypandas, dico = self.standard_input(mypandas, input_field, **kwargs)
            if input_field is None and dico['which'] is None:
                input_field = mypandas.columns[2]
            else:
                if type(input_field) is None.__class__:
                    input_field = [dico['var_displayed']]
                else:
                    input_field = dico['input_field']

            dict_filter_data = defaultdict(list)
            ax_type = ['linear', 'log']
            tooltips = 'Date: @date{%F} <br>  $name: @$name'
            #uniqloc = mypandas.clustername.unique()
            if 'location' in mypandas.columns:
                tooltips = 'Location: @codelocation <br> Date: @date{%F} <br>  $name: @$name'
                new = pd.DataFrame(columns = mypandas.columns)
                location_ordered_byvalues = list(
                    mypandas.loc[mypandas.date == dico['when_end']].sort_values(by=input_field, ascending=False)[
                        'clustername'].unique())
                mypandas = mypandas.loc[(mypandas['date'] >= dico['when_beg']) & (mypandas['date'] <= dico['when_end'])]
                mypandas = mypandas.copy()  # needed to avoid warning

                mypandas.loc[:,'clustername'] = pd.Categorical(mypandas.clustername,
                                                       categories=location_ordered_byvalues, ordered=True)

                mypandas = mypandas.sort_values(by=['clustername', 'date']).reset_index()

                if len(location_ordered_byvalues) > 12:
                    mypandas = mypandas.loc[mypandas.clustername.isin(location_ordered_byvalues[:12])]
                list_max = []
                for i in input_field:
                    list_max.append(max(mypandas.loc[mypandas.clustername.isin(location_ordered_byvalues)][i]))
                if len([x for x in list_max if not np.isnan(x)]) > 0:
                    amplitude = (np.nanmax(list_max) - np.nanmin(list_max))
                    if amplitude > 10 ** 4:
                        ax_type.reverse()
            hover_tool = HoverTool(tooltips=tooltips, formatters={'@date': 'datetime'})
            return func(self, mypandas, dico, input_field, hover_tool, ax_type, **kwargs)
        return generic_plot

    @decoplot
    def pycoa_plot(self, mypandas, dico, input_field, hover_tool, ax_type, **kwargs):
        panels = []
        cases_custom = CocoDisplay.rollerJS()
        for axis_type in ax_type:
            standardfig = self.standardfig(x_axis_label = input_field[0],
                                           y_axis_label = input_field[1], y_axis_type = axis_type, title = dico['titlebar'],
                                           textcopyright = dico['textcopyright'])

            standardfig.add_tools(HoverTool(
                tooltips=[('Location', '@rolloverdisplay'), ('date', '@date{%F}'),
                          (input_field[0], '@{casesx}' + '{custom}'),
                          (input_field[1], '@{casesy}' + '{custom}')],
                formatters={'location': 'printf', '@{casesx}': cases_custom, '@{casesy}': cases_custom,
                            '@date': 'datetime'},
                point_policy="snap_to_data"))  # ,PanTool())

            if len(input_field) != 2:
                raise CoaTypeError('Two variables are needed to be plotted ... ')

            for loc in mypandas.clustername.unique():
                pandaloc = mypandas.loc[mypandas.clustername == loc].sort_values(by='date', ascending='True')
                pandaloc.rename(columns={input_field[0]: 'casesx', input_field[1]: 'casesy'}, inplace=True)
                standardfig.line(x='casesx', y='casesy',
                                 source=ColumnDataSource(pandaloc), legend_label=pandaloc.clustername.iloc[0],
                                 color=pandaloc.colors.iloc[0], line_width=3, hover_line_width=4)

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig, title=axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "top_left"
            CocoDisplay.bokeh_legend(standardfig)
        tabs = Tabs(tabs=panels)
        return tabs

    @decoplot
    def pycoa_date_plot(self, mypandas, dico, input_field, hover_tool, ax_type, **kwargs):
        panels = []
        cases_custom = CocoDisplay.rollerJS()
        if isinstance(mypandas['rolloverdisplay'][0],list):
            mypandas['rolloverdisplay'] = mypandas['clustername']
        full_legend=kwargs.get('full_legend', True)
        mode = kwargs.get('mode', 'mouse')
        allmode=['mouse','vline','hline']
        if mode not in allmode:
            raise CoaKeyError("Bokeh hover tool displays error not in :",allmode)
        for axis_type in ax_type:
            standardfig = self.standardfig(y_axis_type = axis_type, x_axis_type = 'datetime', title = dico['titlebar'],
            textcopyright = dico['textcopyright'])
            i = 0
            r_list=[]
            maxou=-1000
            for val in input_field:
                line_style = ['solid', 'dashed', 'dotted', 'dotdash']
                for loc in list(mypandas.clustername.unique()):
                    mypandas_filter = mypandas.loc[mypandas.clustername == loc].reset_index(drop = True)
                    src = ColumnDataSource(mypandas_filter)
                    leg = mypandas_filter.permanentdisplay[0]
                    if len(input_field)>1:
                        leg += mypandas_filter.permanentdisplay[0] + ', ' + val
                        color = self.scolors[i]
                    else:
                        color = mypandas_filter.colors[i]
                    r = standardfig.line(x = 'date', y = val, source = src,
                                     color = color, line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = val, line_dash=line_style[i])
                    r_list.append(r)
                    maxou=max(maxou,np.nanmax(mypandas_filter[val].values))
                i += 1
            for r in r_list:
                label = r.name
                tooltips = [('Location', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name')]
                formatters = {'location': 'printf', '@date': 'datetime', '@name': 'printf'}
                hover=HoverTool(tooltips = tooltips, formatters = formatters,
                                            point_policy = "snap_to_data",mode=mode,renderers=[r])  # ,PanTool())
                standardfig.add_tools(hover)

            if axis_type == 'linear':
                if maxou  < 1e4 :
                    standardfig.yaxis.formatter = BasicTickFormatter(use_scientific=False)

            standardfig.legend.label_text_font_size = "12px"
            panel = Panel(child=standardfig, title = axis_type)
            panels.append(panel)
            standardfig.legend.background_fill_alpha = 0.6

            standardfig.legend.location = "top_left"
            standardfig.legend.click_policy="hide"

            standardfig.xaxis.formatter = DatetimeTickFormatter(
                days = ["%d/%m/%y"], months = ["%d/%m/%y"], years = ["%b %Y"])

            CocoDisplay.bokeh_legend(standardfig)
        tabs = Tabs(tabs = panels)
        return tabs

    @decoplot
    def pycoa_scrollingmenu(self, mypandas, dico, input_field, hover_tool, ax_type, **kwargs):
        uniqloc = mypandas.clustername.unique().to_list()
        if 'location' in mypandas.columns:
            if len(uniqloc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                   'There is no sens to use this method. See help.')

        mypandas = mypandas.loc[(mypandas['date'] >= dico['when_beg']) & (mypandas['date'] <= dico['when_end'])]
        mypandas[input_field[0]] = mypandas[input_field[0]].astype(float)

        mypandas = mypandas[['date', 'clustername', input_field[0]]]
        mypivot = pd.pivot_table(mypandas, index='date', columns='clustername', values=input_field[0])
        source = ColumnDataSource(mypivot)

        filter_data1 = mypivot[[uniqloc[0]]].rename(columns={uniqloc[0]: 'cases'})
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = mypivot[[uniqloc[1]]].rename(columns={uniqloc[1]: 'cases'})
        src2 = ColumnDataSource(filter_data2)

        cases_custom = CocoDisplay.rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@{cases}' + '{custom}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in ax_type:
            standardfig = self.standardfig(y_axis_type = axis_type,
                                           x_axis_type = 'datetime', title = dico['titlebar'])
            standardfig.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            if dico['title']:
                standardfig.title.text = dico['title']
            standardfig.add_tools(hover_tool)

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
        label = dico['titlebar']
        return tabs

    ###################### END Plots ##################
    ##################### BEGIN HISTOS/MAPS##################
    def decohistomap(func):
        """
        Decorator function used for histogram and map
        """
        def generic_hm(self, mypandas, input_field = None, cursor_date = False, maplabel = False, **kwargs):

            mypandas, dico = self.standard_input(mypandas, input_field, **kwargs, plot_last_date=True)
            #if func.__name__ == 'pycoa_mapfolium' or  func.__name__ == 'innerdecopycoageo' or :
            if isinstance(mypandas['location'].iloc[0],list):
                mypandas['rolloverdisplay'] = mypandas['clustername']
                mypandas = mypandas.explode('location')
            else:
                mypandas['rolloverdisplay'] = mypandas['location']
            if type(input_field) is None.__class__ and dico['which'] is None.__class__:
                input_field = mypandas.columns[2]
            else:
                if type(input_field) is None.__class__:
                    input_field = dico['var_displayed']
                else:
                    input_field = dico['input_field'][0]

            uniqloc = mypandas.clustername.unique()

            if func.__name__ != 'pycoa_mapfolium' and  func.__name__ != 'innerdecopycoageo':
                    mypandas = mypandas.drop_duplicates(["date", "codelocation","clustername"])

            geopdwd = mypandas

            geopdwd = geopdwd.sort_values(by = input_field, ascending=False)
            geopdwd = geopdwd.reset_index(drop = True)
            orientation = kwargs.get('orientation', 'horizontal')

            if dico['when_end'] <= geopdwd.date.min():
                started = geopdwd.date.min()
                ended = geopdwd.date.min() + dt.timedelta(days=1)
            else:
                started = geopdwd.date.min()
                ended = dico['when_end']
            date_slider = DateSlider(title = "Date: ", start = started, end = ended,
                                     value = ended, step=24 * 60 * 60 * 1000, orientation = orientation)
            geopdwd_filter = geopdwd.copy()

            wanted_date = date_slider.value_as_datetime.date()
            geopdwd_filter = geopdwd_filter.loc[geopdwd_filter.date == wanted_date]
            geopdwd_filter = geopdwd_filter.reset_index(drop = True)

            if func.__name__ == 'pycoa_mapfolium' or func.__name__ == 'innerdecomap' or func.__name__ == 'innerdecopycoageo':
                if isinstance(mypandas.location.to_list()[0],list):
                    geom = self.location_geometry
                    geodic={loc:geom.loc[geom.location==loc]['geometry'].values[0] for loc in geopdwd_filter.location.unique()}
                    geopdwd_filter['geometry'] = geopdwd_filter['location'].map(geodic)
                else:
                    geopdwd_filter = pd.merge(geopdwd_filter, self.location_geometry, on='location')
                geopdwd_filter = gpd.GeoDataFrame(geopdwd_filter, geometry=geopdwd_filter.geometry, crs="EPSG:4326")
                dico['tile'] = CocoDisplay.get_tile(dico['tile'], func.__name__)

            if func.__name__ == 'inner' or func.__name__ == 'pycoa_histo':
                pos = {}
                new = pd.DataFrame()#columns=geopdwd_filter.columns, dtype=lisgeopdwd_filter.dtypes)
                n = 0
                for i in uniqloc:
                    perloc = geopdwd_filter.loc[geopdwd_filter.clustername == i]
                    if all(perloc != 0):
                        pos = perloc.index[0]
                        if new.empty:
                            new = perloc
                        else:
                            new = new.append(perloc)
                        n += 1

                geopdwd_filter = new.reset_index(drop=True)
                my_date = geopdwd.date.unique()

                dico_utc = {i: DateSlider(value = i ).value for i in my_date}
                geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
                geopdwd_filter=geopdwd_filter.sort_values(by=[input_field], ascending=False)
            geopdwd_filter = geopdwd_filter.reset_index(drop=True)

            if cursor_date is False:
                date_slider = False
            return func(self, input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filter)
        return generic_hm

    def pycoa_heatmap(self, pycoa_pandas):
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

        pycoa_pandas = pycoa_pandas.set_index('location')
        pycoa_pandas = pycoa_pandas.apply(lambda x: (x - x.min()) / (x.max() - x.min()))

        pycoa_pandas.columns.name = 'data'
        pycoa_pandas = pycoa_pandas.stack().rename("value").reset_index()

        standardfig = self.standardfig(y_range = list(pycoa_pandas.location.unique()),
                                       x_range = list(pycoa_pandas.data.unique()))
        standardfig.xaxis.major_label_orientation = "vertical"

        invViridis256 = Viridis256[::-1]
        color_mapper = LinearColorMapper(palette = invViridis256, low = pycoa_pandas.value.min(),
                                         high = pycoa_pandas.value.max(), nan_color = '#ffffff')
        color_bar = ColorBar(color_mapper = color_mapper, label_standoff=4,
                             border_line_color = None, location=(0, 0), orientation = 'vertical', ticker = BasicTicker())
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
            tooltips=[('location', '@rolloverdisplay'), ('value', '@value')],
            point_policy="snap_to_data"))
        return standardfig

    @decohistomap
    def pycoa_histo(self, input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered):
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
        mypandas = geopdwd_filtered.rename(columns = {'cases': input_field})
        if 'location' in mypandas.columns:
            uniqloc = list(mypandas.clustername.unique())
            allval  = mypandas.loc[mypandas.clustername.isin(uniqloc)][['clustername', input_field,'permanentdisplay']]
            min_val = allval[input_field].min()
            max_val = allval[input_field].max()
            if len(uniqloc) == 1:
                dico['bins'] = 2
                min_val = 0.

            if dico['bins']:
                bins = dico['bins']
            else:
                bins = len(uniqloc)

            delta = (max_val - min_val ) / (bins-1)
            interval = [ min_val + (i-1)*delta for i in range(1,(bins+1)+1)]

            contributors = {  i : [] for i in range(bins)}
            for i in range(len(allval)):
                rank = bisect.bisect_left(interval, allval.iloc[i][input_field])
                contributors[rank].append(allval.iloc[i]['clustername'])

            colors = itertools.cycle(self.lcolors)
            lcolors = [next(colors) for i in range(bins)]
            contributors = dict(sorted(contributors.items()))
            frame_histo = pd.DataFrame({
                              'left': interval[:-1],
                              'right':interval[1:],
                              'middle_bin': [format((i+j)/2, ".1f") for i,j in zip(interval[:-1],interval[1:])],
                              'top': [len(i) for i in list(contributors.values())],
                              'contributors': [', '.join(i) for i in contributors.values() ],
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
            standardfig = self.standardfig(x_axis_type=x_axis_type, y_axis_type=y_axis_type, title=dico['titlebar'])
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

    def decohistopie(func):
        def inner(self, input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered):
            """
            Decorator for
            Horizontal histogram & Pie Chart
            """
            title_fig = input_field
            geopdwd['cases'] = geopdwd[input_field]
            geopdwd_filtered['cases'] = geopdwd_filtered[input_field]

            my_date = geopdwd.date.unique()
            dico_utc = {i: DateSlider(value=i).value for i in my_date}
            geopdwd['date_utc'] = [dico_utc[i] for i in geopdwd.date]
            geopdwd = geopdwd.drop_duplicates(["date", "codelocation","clustername"])#for sumall avoid duplicate
            geopdwd_filtered = geopdwd_filtered.sort_values(by='cases', ascending = False).reset_index()
            locunique = geopdwd_filtered.clustername.unique()#geopdwd_filtered.location.unique()

            geopdwd_filter = geopdwd_filtered.copy()
            nmaxdisplayed = 18

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
                bthick = 0.95
                geopdwd_filter['top'] = [len(geopdwd_filter.index) + bthick / 2 - i for i in
                                             geopdwd_filter.index.to_list()]
                geopdwd_filter['bottom'] = [len(geopdwd_filter.index) - bthick / 2 - i for i in
                                                geopdwd_filter.index.to_list()]
                geopdwd_filter['horihistotexty'] =  geopdwd_filter['bottom'] + bthick/2
                geopdwd_filter['horihistotextx'] = geopdwd_filter['right']
                geopdwd_filter['horihistotext'] = [ '{:.3g}'.format(float(i)) if float(i)>1.e4 else round(float(i),2) for i in geopdwd_filter['right'] ]

            if func.__name__ == 'pycoa_pie' :
                geopdwd_filter = self.add_columns_for_pie_chart(geopdwd_filter,input_field)
                geopdwd = self.add_columns_for_pie_chart(geopdwd,input_field)

            source = ColumnDataSource(data = geopdwd)
            mypandas_filter = geopdwd_filter
            srcfiltered = ColumnDataSource(data = mypandas_filter)
            max_value = mypandas_filter[input_field].max()
            min_value = mypandas_filter[input_field].min()
            min_value_gt0 = mypandas_filter[mypandas_filter[input_field] > 0][input_field].min()
            panels = []
            for axis_type in ["linear", "log"]:
                title = dico['titlebar']
                if title_fig != title.split()[0]:
                    title = title_fig + ' ' + title

                standardfig = self.standardfig(x_axis_type = axis_type, x_range = (1.05*min_value, 1.05 * max_value),
                                                   title = dico['titlebar'])
                standardfig.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
                standardfig.x_range = Range1d(0.01, 1.2 * max_value)
                if not mypandas_filter[mypandas_filter[input_field] < 0.].empty:
                    standardfig.x_range = Range1d(1.2 * min_value, 1.2 * max_value)

                if axis_type == "log":
                    if not mypandas_filter[mypandas_filter[input_field] < 0.].empty:
                        print('Some value are negative, can\'t display log scale in this context')
                    else:
                        if func.__name__ == 'pycoa_horizonhisto' :
                            standardfig.x_range = Range1d(0.01, 50 * max_value)
                            srcfiltered.data['left'] = [0.01] * len(srcfiltered.data['right'])

                if func.__name__ == 'pycoa_pie' :
                    if not mypandas_filter[mypandas_filter[input_field] < 0.].empty:
                        raise CoaKeyError('Some values are negative, can\'t display a Pie chart, try histo by location')
                    standardfig.plot_width = self.plot_height
                    standardfig.plot_height = self.plot_height
                if date_slider:
                    date_slider.width = int(0.8*self.plot_width)
                    callback = CustomJS(args = dict(source = source,
                                                  source_filter = srcfiltered,
                                                  date_slider = date_slider,
                                                  ylabel = standardfig.yaxis[0],
                                                  title = standardfig.title,
                                                  x_range = standardfig.x_range,
                                                  x_axis_type = axis_type),
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
                            console.log(newcodeloc);
                            var len = source_filter.data['clustername'].length;

                            var indices = new Array(len);
                            for (var i = 0; i < len; i++) indices[i] = i;

                            indices.sort(function (a, b) { return newval[a] > newval[b] ? -1 : newval[a] < newval[b] ? 1 : 0; });
                            var orderval = [];
                            var orderloc = [];
                            var ordercodeloc = [];
                            var ordername_subregion = [];
                            var ordercolors = [];
                            for (var i = 0; i < len; i++)
                            {
                                orderval.push(newval[indices[i]]);
                                orderloc.push(newloc[indices[i]]);
                                ordercodeloc.push(newcodeloc[indices[i]]);

                                if(typeof subregion !== 'undefined')
                                    ordername_subregion.push(newname_subregion[i]);
                                ordercolors.push(newcolors[indices[i]]);
                                labeldic[len-indices[i]] = orderloc[indices[i]];
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

                                top.push((orderval.length-i) + bthick/2);
                                bottom.push((orderval.length-i) - bthick/2);

                                if(orderval[i]<0)
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

                            ylabel.major_label_overrides = labeldic;

                            source_filter.data['top'] = top;
                            source_filter.data['bottom'] = bottom;
                            source_filter.data['left'] = left_quad;
                            source_filter.data['right'] = right_quad;

                            var mid =[];
                            var ht = [];
                            for(i=0; i<right_quad.length;i++){
                                mid.push(bottom[i]+(top[i] - bottom[i])/2);
                                ht.push(right_quad[i].toFixed(2).toString());
                            }

                            source_filter.data['horihistotextxy'] =  mid;
                            source_filter.data['horihistotextx'] =  right_quad
                            source_filter.data['horihistotext'] =  ht

                            var maxx = Math.max.apply(Math, right_quad);
                            var minx = Math.min.apply(Math, left_quad);

                            x_range.end =  1.2 * maxx;
                            x_range.start =  1.05 * minx;
                            if(x_axis_type==='log' && minx >= 0){
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
                        tooltips=[('Location', '@rolloverdisplay'), (input_field, '@{' + 'cases' + '}' + '{custom}'), ('%','@percentage'), ],
                        formatters={'location': 'printf', '@{' + 'cases' + '}': cases_custom, '%':'printf'},
                        point_policy="snap_to_data"))  # ,PanTool())
                else:
                    standardfig.add_tools(HoverTool(
                        tooltips=[('Location', '@rolloverdisplay'), (input_field, '@{' + 'cases' + '}' + '{custom}'), ],
                        formatters={'location': 'printf', '@{' + 'cases' + '}': cases_custom, },
                        point_policy="snap_to_data"))  # ,PanTool())
                panel = Panel(child = standardfig, title = axis_type)
                panels.append(panel)
            return func(self, srcfiltered, panels, date_slider)
        return inner

    @decohistomap
    @decohistopie
    def pycoa_horizonhisto(self, srcfiltered, panels, date_slider):
        n = len(panels)
        loc = srcfiltered.data['permanentdisplay']#srcfiltered.data['codelocation']
        chars = [' ','-']
        returnchars = [x for x in loc if x in chars]
        label_dict = {}
        label_dict = {(len(loc) - k) : v for k, v in enumerate(loc) }
        new_panels = []
        for i in range(n):
            fig = panels[i].child
            fig.yaxis.ticker = list(range(1, len(loc)+1))
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
        if date_slider:
                tabs = column(date_slider,tabs)
        return tabs

    @decohistomap
    @decohistopie
    def pycoa_pie(self, srcfiltered, panels, date_slider):
        standardfig = panels[0].child
        standardfig.x_range = Range1d(-1.1, 1.1)
        standardfig.y_range = Range1d(-1.1, 1.1)
        standardfig.axis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None

        standardfig.wedge(x=0, y=0, radius=1.05,line_color='#E8E8E8',
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        fill_color='colors', legend_label='clustername', source=srcfiltered)
        standardfig.legend.visible = False

        labels = LabelSet(x=0, y=0, text='textdisplayed',
        angle=cumsum('angle', include_zero=True), source=srcfiltered, render_mode='canvas',text_font_size="10pt")
        labels2 = LabelSet(x=0, y=0, text='textdisplayed2',
        angle=cumsum('angle', include_zero=True), source=srcfiltered, render_mode='canvas',text_font_size="8pt")

        standardfig.add_layout(labels)
        standardfig.add_layout(labels2)
        if date_slider:
            standardfig = column(date_slider,standardfig)
        return standardfig

    @decohistomap
    def pycoa_mapfolium(self, input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered):
        """Create a Folium map from a pandas input
        Folium limite so far:
            - scale format can not be changed (no way to use scientific notation)
            - map can not be saved as png only html format
                - save_map2png for this purpose (available only in command line, not in iconic form)
        Keyword arguments
        -----------------
        babepandas : pandas considered
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
        geopdwd['cases'] = geopdwd[input_field]
        geopdwd_filtered['cases'] = geopdwd_filtered[input_field]

        zoom = 1
        if self.dbld[self.database_name] != 'WW':
            self.boundary = geopdwd_filtered['geometry'].total_bounds
            name_location_displayed = 'name_subregion'
            zoom = 1
        uniqloc = list(geopdwd_filtered.codelocation.unique())
        geopdwd_filtered = geopdwd_filtered.drop(columns=['date', 'colors'])

        if self.dbld[self.database_name][0] in ['FRA','ESP','PRT']:# and all(len(l) == 2 for l in geopdwd_filtered.codelocation.unique()):
            minx, miny, maxx, maxy = self.boundary_metropole
            zoom = 1
        else:
            minx, miny, maxx, maxy = self.boundary
            zoom = 1

        msg = "(data from: {})".format(self.database_name)
        mapa = folium.Map(location=[(maxy + miny) / 2., (maxx + minx) / 2.], zoom_start=zoom,
                          tiles=dico['tile'], attr='<a href=\"http://pycoa.fr\"> ©pycoa.fr </a>' + msg)  #

        fig = Figure(width=self.plot_width, height=self.plot_height)
        fig.add_child(mapa)
        min_col, max_col = CocoDisplay.min_max_range(np.nanmin(geopdwd_filtered[input_field]),
                                                     np.nanmax(geopdwd_filtered[input_field]))

        invViridis256 = Viridis256[::-1]
        color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#d9d9d9')
        colormap = branca.colormap.LinearColormap(color_mapper.palette).scale(min_col, max_col)
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
        geopdwd_filtered[input_field + 'scientific_format'] = \
            (['{:.5g}'.format(i) for i in geopdwd_filtered[input_field]])
        # (['{:.3g}'.format(i) if i>100000 else i for i in geopdwd_filter[input_field]])

        map_dict = geopdwd_filtered.set_index('location')[input_field].to_dict()
        if np.nanmin(geopdwd_filtered[input_field]) == np.nanmax(geopdwd_filtered[input_field]):
            map_dict['FakeCountry'] = 0.
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

    def decopycoageo(func):
        def innerdecopycoageo(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered):
            geopdwd['cases'] = geopdwd[input_field]
            geopdwd_filtered['cases'] = geopdwd_filtered[input_field]
            geopdwd_filtered = gpd.GeoDataFrame(geopdwd_filtered, geometry=geopdwd_filtered.geometry, crs="EPSG:4326")
            geopdwd = geopdwd.sort_values(by=['clustername', 'date'], ascending = [True, False])

            geopdwd_filtered = geopdwd_filtered.sort_values(by=['clustername', 'date'], ascending = [True, False]).drop(columns=['date', 'colors'])
            new_poly = []
            geolistmodified = dict()
            if date_slider:
                date_slider.orientation = 'horizontal'

            for index, row in geopdwd_filtered.iterrows():
                split_poly = []
                new_poly = []
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
            geolistmodified = gpd.GeoDataFrame({'location': ng['location'], 'geometry': gpd.GeoSeries(ng['geometry'])},
                                               crs="epsg:3857")
            geopdwd_filtered = geopdwd_filtered.drop(columns='geometry')
            geopdwd_filtered = pd.merge(geolistmodified, geopdwd_filtered, on='location')
            return func(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered)
        return innerdecopycoageo

    @decohistomap
    @decopycoageo
    def pycoageo(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered):
        return geopdwd_filtered

    def decomap(func):
        def innerdecomap(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered):
            sourcemaplabel = ColumnDataSource(pd.DataFrame({'centroidx':[],'centroidy':[],'cases':[],'spark':[]}))
            uniqloc = list(geopdwd_filtered.clustername.unique())

            if maplabel or func.__name__ == 'pycoa_sparkmap':
                geopdwd_filtered['centroidx'] = geopdwd_filtered['geometry'].centroid.x
                geopdwd_filtered['centroidy'] = geopdwd_filtered['geometry'].centroid.y
                locsum = geopdwd_filtered.clustername.unique()
                for i in locsum:
                    cases = geopdwd_filtered.loc[geopdwd_filtered.clustername == i]['cases'].values[0]
                    centrosx = geopdwd_filtered.loc[geopdwd_filtered.clustername == i]['centroidx']#.mean()
                    centrosy = geopdwd_filtered.loc[geopdwd_filtered.clustername == i]['centroidy']#.mean()
                    geopdwd_filtered.loc[geopdwd_filtered.clustername == i,'centroidx'] = centrosx
                    geopdwd_filtered.loc[geopdwd_filtered.clustername == i,'centroidy'] = centrosy
                    geopdwd_filtered.loc[geopdwd_filtered.clustername == i,'spark'] = \
                                CocoDisplay.sparkline(geopdwd.loc[(geopdwd.clustername == i) &
                                (geopdwd.date >= dico['when_beg']) & (geopdwd.date <= dico['when_end'])].sort_values(by='date')[input_field])
                dfLabel=pd.DataFrame(geopdwd_filtered[['location','centroidx','centroidy','cases','spark','clustername']])
                dfLabel['cases'] = dfLabel['cases'].round(2)
                dfLabel = (dfLabel.groupby(['cases','clustername','spark']).mean())
                dfLabel = dfLabel.reset_index()
                sourcemaplabel = ColumnDataSource(dfLabel)

            if self.dbld[self.database_name][0] in ['FRA','ESP','PRT'] and all(len(l) == 2 for l in geopdwd_filtered.codelocation.unique()):
                minx, miny, maxx, maxy = self.boundary_metropole
                (minx, miny) = CocoDisplay.wgs84_to_web_mercator((minx, miny))
                (maxx, maxy) = CocoDisplay.wgs84_to_web_mercator((maxx, maxy))
            else:
                minx, miny, maxx, maxy =  geopdwd_filtered['geometry'].total_bounds #self.boundary

            if self.dbld[self.database_name][0] != 'WW':
                ratio = 0.05
                minx -= ratio*minx
                maxx += ratio*maxx
                miny -= ratio*miny
                maxy += ratio*maxy

            copyrightposition = 'left'
            if self.dbld[self.database_name][0] == 'ESP' :
                copyrightposition='right'

            if func.__name__ == 'pycoa_sparkmap':
                tit=dico['titlebar']
                dico['titlebar']=tit[:-12]+' [ '+dico['when_beg'].strftime('%d/%m/%Y')+ '-'+ tit[-12:-1]+'])'
            standardfig = self.standardfig(x_range=(minx, maxx), y_range=(miny, maxy),
                                           x_axis_type="mercator", y_axis_type="mercator", title=dico['titlebar'],
                                           copyrightposition = copyrightposition)

            wmt = WMTSTileSource(
                        url=dico['tile'])
            standardfig.add_tile(wmt)

            geopdwd_filtered = geopdwd_filtered[['cases','geometry','location','codelocation','rolloverdisplay']]
            if self.dbld[self.database_name][0] == 'BEL' :
                reorder = list(geopdwd_filtered.location.unique())
                geopdwd_filtered = geopdwd_filtered.set_index('location')
                geopdwd_filtered = geopdwd_filtered.reindex(index = reorder)
                geopdwd_filtered = geopdwd_filtered.reset_index()

            if self.dbld[self.database_name][0] == 'GBR' :
                geopdwd = geopdwd.loc[~geopdwd.cases.isnull()]
                geopdwd_filtered  = geopdwd_filtered.loc[~geopdwd_filtered.cases.isnull()]
            return func(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered,standardfig,sourcemaplabel)
        return innerdecomap

    @decohistomap
    @decopycoageo
    @decomap
    def pycoa_map(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered,standardfig,sourcemaplabel):
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

        if date_slider:
            allcases_location, allcases_dates = pd.DataFrame(), pd.DataFrame()
            allcases_location = geopdwd.groupby('location')['cases'].apply(list)
            geopdwd_tmp = geopdwd.drop_duplicates(subset = ['location']).drop(columns = 'cases')
            geopdwd_tmp = pd.merge(geopdwd_tmp, allcases_location, on = 'location')

            geopdwd_tmp = ColumnDataSource(geopdwd_tmp)

            callback = CustomJS(args =  dict(source = geopdwd_tmp, source_filter = geopdwd_filtered,
                                          date_slider = date_slider, title=standardfig.title,
                                          maplabel = sourcemaplabel),
                        code = """
                        var ind_date_max = (date_slider.end-date_slider.start)/(24*3600*1000);
                        var ind_date = (date_slider.value-date_slider.start)/(24*3600*1000);
                        var val_cases = [];
                        var val_loc = [];
                        var val_ind = [];
                        var new_cases = [];
                        var new_location = [];
                        var dict = {};
                        var iloop = source_filter.data['location'].length;

                        for (var i = 0; i < source.get_length(); i++)
                        {
                                new_cases.push(source.data['cases'][i][ind_date_max-ind_date]);
                                new_location.push(source.data['location'][i][ind_date_max-ind_date]);
                        }
                        if(source.get_length() == 1 && iloop>1)
                            for(var i = 0; i < iloop; i++)
                                for(var j = 0; j < new_cases.length; j++)
                                source_filter.data['cases'][i][j] = new_cases[j];

                        else
                            source_filter.data['cases'] = new_cases;

                        if (maplabel.get_length() !== 0){
                            maplabel.data['cases'] = source_filter.data['cases'];
                            }

                        var tmp = title.text;
                        tmp = tmp.slice(0, -11);
                        var dateconverted = new Date(date_slider.value);
                        var dd = String(dateconverted.getDate()).padStart(2, '0');
                        var mm = String(dateconverted.getMonth() + 1).padStart(2, '0'); //January is 0!
                        var yyyy = dateconverted.getFullYear();
                        var dmy = dd + '/' + mm + '/' + yyyy;
                        title.text = tmp + dmy+")";
                        if (maplabel.get_length() !== 0)
                            maplabel.change.emit();

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
        if maplabel :
            labels = LabelSet(
                x = 'centroidx',
                y = 'centroidy',
                text = 'cases',
                source = sourcemaplabel,text_font_size='10px',text_color='white',background_fill_color='grey',background_fill_alpha=0.05)
            standardfig.add_layout(labels)

        cases_custom = CocoDisplay.rollerJS()
        loctips = ('location', '@rolloverdisplay')
        standardfig.add_tools(HoverTool(
            tooltips = [loctips, (input_field, '@{' + 'cases' + '}' + '{custom}'), ],
            formatters = {'location': 'printf', '@{' + 'cases' + '}': cases_custom, },
            point_policy = "snap_to_data"))  # ,PanTool())
        if date_slider:
            standardfig = column(date_slider, standardfig)
        return standardfig

    def pycoa_map2(self,input_field, geopdwd_filtered):

        sourcemaplabel = ColumnDataSource(pd.DataFrame({'centroidx':[],'centroidy':[],'cases':[]}))
        uniqloc = list(geopdwd_filtered.name_subregion.unique())
        boundary = geopdwd_filtered.loc[geopdwd_filtered.name_subregion.isin(uniqloc)]['geometry'].total_bounds
        minx, miny, maxx, maxy = boundary

        standardfig = self.standardfig(x_range=(minx, maxx), y_range=(miny, maxy),
                                       x_axis_type="mercator", y_axis_type="mercator")

        min_col, max_col = CocoDisplay.min_max_range(np.nanmin(geopdwd_filtered[input_field]),
                                                         np.nanmax(geopdwd_filtered[input_field]))

        invViridis256 = Viridis256[::-1]
        color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#ffffff')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4,
                             border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))
        standardfig.add_layout(color_bar, 'below')

        geopdwd_filtered = geopdwd_filtered[['cases','geometry','location','codelocation','rolloverdisplay']]
        json_data = json.dumps(json.loads(geopdwd_filtered.to_json()))
        geopdwd_filtered = GeoJSONDataSource(geojson=json_data)
        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.patches('xs', 'ys', source = geopdwd_filtered,
                            fill_color = {'field': 'cases', 'transform': color_mapper},
                            line_color = 'black', line_width = 0.25, fill_alpha = 1)
        return standardfig
    ##################### END HISTOS/MAPS##################

    #### NOT YET IMPLEMENTED WITH THIS CURRENT VERSION ... TO DO ...
    #took from https://github.com/iiSeymour/sparkline-nb/blob/master/sparkline-nb.ipynb
    def sparkline(data, figsize=(0.5, 0.5), **kwags):
        """
        Returns a HTML image tag containing a base64 encoded sparkline style plot
        """
        data = list(data)
        fig, ax = plt.subplots(1, 1, figsize=figsize, **kwags)
        ax.patch.set_alpha(0.2)
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

    @decohistomap
    @decopycoageo
    @decomap
    def pycoa_sparkmap(self,input_field, date_slider, maplabel, dico, geopdwd, geopdwd_filtered,standardfig,sourcemaplabel):
        standardfig.xaxis.visible = False
        standardfig.yaxis.visible = False
        standardfig.xgrid.grid_line_color = None
        standardfig.ygrid.grid_line_color = None
        standardfig.image_url(url='spark', x='centroidx', y='centroidy',source=sourcemaplabel,anchor="center")
        return standardfig

    def spark_pandas(self, pandy, which_data):
        """
            Return pandas : location as index andwhich_data as sparkline (latest 30 values)
        """
        pd.DataFrame._repr_html_ = lambda self: self.to_html(escape=False)
        loc = pandy['location'].unique()
        resume = pd.DataFrame({
            'location': loc,
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
                    if not math.isnan(maxy):
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
                            date, value[0], color=self.scolors[i % 10], legend_label=location)
                        y_err_x = []
                        y_err_y = []
                        for px, py in zip(date, value[0]):
                            err = np.sqrt(np.abs(py))
                            y_err_x.append((px, px))
                            y_err_y.append((py - err, py + err))
                        fig.multi_line(y_err_x, y_err_y,
                                       color=self.scolors[i % 10])
                    else:
                        fig.line(
                            date, value[0], line_color=self.scolors[i % 10], legend_label=location)

                    fig.line(date[:crys.GetTotalDaysConsidered(
                    )], value[1][:crys.GetTotalDaysConsidered()], line_color='red', line_width=4)

                    fig.xaxis.formatter = DatetimeTickFormatter(
                        days=["%d %b %y"], months=["%d %b %y"], years=["%d %b %y"])
                    fig.xaxis.major_label_orientation = np.pi / 4
                    fig.xaxis.ticker.desired_num_ticks = 10
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
