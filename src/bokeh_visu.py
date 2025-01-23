# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa_fr
License: See joint LICENSE file

Module : src.bokeh_visu

About :
-------


"""
from src.tools import (
    extract_dates,
    verb,
    fill_missing_dates
)
from src.error import *
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
import copy
import locale
import inspect
import importlib

import shapely.geometry as sg

import datetime as dt
import bisect
from functools import wraps

from src.dbparser import MetaInfo
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
Text,
)
from bokeh.models import (
    Toggle
)
from bokeh.models.layouts import TabPanel, Tabs
from bokeh.models import Panel
from bokeh.plotting import figure, show
from bokeh.io import output_notebook

output_notebook()
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

Width_Height_Default = [580, 400]
Max_Countries_Default = 24
import src.output
class bokeh_visu:
    def __init__(self,d_graphicsinput_args = None):
        self.pycoageopandas = False
        self.lcolors = Category20[20]
        self.scolors = Category10[5]
        #self.HoverTool= HoverTool
        #self.TabPanel = TabPanel
        #self.DatetimeTickFormatter = DatetimeTickFormatter
        #self.BasicTicker = BasicTicker
        #self.GeoJSONDataSource = GeoJSONDataSource
        #self.Tabs = Tabs
        #self.LinearColorMapper = LinearColorMapper
        #self.ColorBar = ColorBar
        #self.Viridis256 = Viridis256
        self.d_graphicsinput_args = d_graphicsinput_args
        self.graph_height=400
        self.graph_width=400

        #self.ColumnDataSource = ColumnDataSource
        if type(input)==gpd.geodataframe.GeoDataFrame:
            self.pycoageopandas = True

            '''
            kwargs['GeoJSONDataSource'] = GeoJSONDataSource,\
            kwargs['Viridis256'] = Viridis256,\
            kwargs['LinearColorMapper'] = LinearColorMapper,\
            kwargs['ColorBar'] = ColorBar,\
            kwargs['BasicTicker'] = BasicTicker,\
            kwargs['BasicTickFormatter'] = BasicTickFormatter,\
            kwargs['Label'] = Label,\
            kwargs['figure'] = figure,\
            kwargs['Title'] = Title,\
            kwargs['Category10'] = Category10,\
            kwargs['Category20'] = Category20,\
            kwargs['ColumnDataSource'] = ColumnDataSource,\
            kwargs['HoverTool'] = HoverTool,\
            kwargs['BasicTickFormatter'] = BasicTickFormatter,\
            kwargs['TabPanel'] = TabPanel,\
            kwargs['DatetimeTickFormatter'] = DatetimeTickFormatter,\
            kwargs['BasicTickFormatter'] = BasicTickFormatter,\
            kwargs['Tabs'] = Tabs,\
            kwargs['Range1d'] = Range1d,\
            kwargs['LabelSet'] = LabelSet,\
            '''

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

    @staticmethod
    def rollerJS():
        from bokeh.models import CustomJSHover
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

    def importbokeh(func):
        def wrapper(self,**kwargs):
            """
            ALL Librairies (and more) needs by bokeh
            """
            return func(self,**kwargs)
        return wrapper

    #@importbokeh
    def bokeh_figure(self, **kwargs):
        """
         Create a standard Bokeh figure, with pycoa_fr copyright, used in all the bokeh charts
        """
        '''
        copyright = kwargs.get('text')
        graph_width = kwargs.get('graph_width',Width_Height_Default[0])
        graph_height = kwargs.get('graph_height',Width_Height_Default[1])
        Label = kwargs.get('Label')
        figure = kwargs.get('figure')
        Title = kwargs.get('Title')
        min_width = kwargs.get('min_width')
        min_height = kwargs.get('min_height')


        citation = Label(x=0.65 * graph_width - len(copyright), y=0.01 *graph_height,
                                          x_units='screen', y_units='screen',
                                          text_font_size='1.5vh', background_fill_color='white',
                                          background_fill_alpha=.75,
                                          text = copyright)
        '''
        y_axis_type = kwargs.get('y_axis_type','linear')
        x_axis_type = kwargs.get('x_axis_type','linear')
        kwargs['width']  = kwargs.get('width', Width_Height_Default[0])
        kwargs['height'] = kwargs.get('height',Width_Height_Default[1])
        fig = figure(**kwargs)
            #y_axis_type = y_axis_type,x_axis_type = x_axis_type,\
            #min_width = graph_width, min_height = graph_height,
            #tools=['save', 'box_zoom,reset'],
            #toolbar_location="right", sizing_mode="stretch_width")
        #fig.add_layout(citation)
        #fig.add_layout(Title(text=self.uptitle, text_font_size="10pt"), 'above')
        return fig

    @staticmethod
    def bokeh_legend(bkfigure):
        from bokeh.models import CustomJS
        from bokeh import events
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

    def get_listfigures(self):
        return  self.listfigs

    def set_listfigures(self,fig):
            if not isinstance(fig,list):
                fig = [fig]
            self.listfigs = fig

    def bokeh_resume_data(self,**kwargs):
        loc=list(input['where'].unique())
        input['cases'] = input[which]
        resumetype = kwargs.get('resumetype','spiral')
        if resumetype == 'spiral':
            dspiral={i:AllVisu.spiral(input.loc[ (input['where']==i) &
                        (input.date >= self.when_beg) &
                        (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
            input['resume']=input['where'].map(dspiral)
        elif resumetype == 'spark':
            spark={i:AllVisu.sparkline(input.loc[ (input['where']==i) &
                        (input.date >= self.when_beg) &
                        (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
            input['resume']=input['where'].map(spark)
        else:
            raise CoaError('bokeh_resume_data can use spiral or spark ... here what ?')
        input = input.loc[input.date==input.date.max()].reset_index(drop=True)
        def path_to_image_html(path):
            return '<img src="'+ path + '" width="60" >'

        input=input.apply(lambda x: x.round(2) if x.name in [which,'daily','weekly'] else x)
        if isinstance(input['where'][0], list):
            col=[i for i in list(input.columns) if i not in ['where','where','code']]
            col.insert(0,'where')
            input = input[col]
            input=input.set_index('where')
        else:
           input = input.drop(columns='where')
           input=input.set_index('where')

        return input.to_html(escape=False,formatters=dict(resume=path_to_image_html))

    ''' PLOT VERSUS '''
    def bokeh_plot(self,**kwargs):
        '''
        -----------------
        Create a versus plot according to arguments.
        See help(bokeh_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element. It should be a list dim=2. Moreover the 2 variables must be present
        in the DataFrame considered.
        - plot_heigh = Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
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
        which = kwargs.get('which')
        copyright = kwargs.get('copyright')
        mode = kwargs.get('mode',list(self.d_graphicsinput_args['mode'])[0])

        panels = []
        cases_custom = bokeh_visu().rollerJS()
        if self.get_listfigures():
            self.set_listfigures([])
        listfigs=[]
        for axis_type in self.optionvisu.ax_type:
            bokeh_figure = self.bokeh_figure( x_axis_label = which[0], y_axis_label = which[1],
                                                y_axis_type = axis_type, text = "ffff")

            bokeh_figure.add_tools(HoverTool(
                tooltips=[('where', '@rolloverdisplay'), ('date', '@date{%F}'),
                          (which[0], '@{casesx}' + '{custom}'),
                          (which[1], '@{casesy}' + '{custom}')],
                formatters={'where': 'printf', '@{casesx}': cases_custom, '@{casesy}': cases_custom,
                            '@date': 'datetime'}, mode = mode,
                point_policy="snap_to_data"))  # ,PanTool())

            for loc in input['where'].unique():
                pandaloc = input.loc[input['where'] == loc].sort_values(by='date', ascending=True)
                pandaloc.rename(columns={which[0]: 'casesx', which[1]: 'casesy'}, inplace=True)
                bokeh_figure.line(x='casesx', y='casesy',
                                 source=ColumnDataSource(pandaloc), legend_label=pandaloc['where'].iloc[0],
                                 color=pandaloc.colors.iloc[0], line_width=3, hover_line_width=4)

            bokeh_figure.legend.label_text_font_size = "12px"
            panel = Panel(child=bokeh_figure, title=axis_type)
            panels.append(panel)
            bokeh_figure.legend.background_fill_alpha = 0.6

            bokeh_figure.legend.location = "top_left"
            listfigs.append(bokeh_figure)
            bokeh_visu().bokeh_legend(bokeh_figure)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' DATE PLOT '''
    #@importbokeh
    def bokeh_date_plot(self,**kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(bokeh_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
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
        input = input.drop(columns='geometry')
        which = kwargs.get('which')

        mode = kwargs.get('mode')
        guideline = kwargs.get('guideline')

        panels = []
        listfigs = []
        cases_custom = bokeh_visu().rollerJS()

        for axis_type in ['linear', 'log']:
            bokeh_figure = self.bokeh_figure( y_axis_type = axis_type, x_axis_type = 'datetime')
            lcolors = iter(self.lcolors)
            i = 0
            r_list=[]
            maxou=-1000
            lcolors = iter(self.lcolors)
            line_style = ['solid', 'dashed', 'dotted', 'dotdash','dashdot']
            maxou, minou=0, 0
            tooltips=[]
            for val in which:
                for loc in list(input['where'].unique()):
                    color = next(lcolors)
                    inputwhere = input.loc[input['where'] == loc].reset_index(drop = True)
                    src = ColumnDataSource(inputwhere)
                    leg = loc

                    r = bokeh_figure.line(x = 'date', y = val, source = src,
                                     color = color, line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = val, line_dash=line_style[i%4])
                    r_list.append(r)
                    maxou=max(maxou,np.nanmax(inputwhere[val]))
                    minou=max(minou,np.nanmin(inputwhere[val]))

                    if minou <0.01:
                        tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name')])
                    else:
                        tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')])
                    if isinstance(tooltips,tuple):
                        tooltips = tooltips[0]
                i += 1
            for i,r in enumerate(r_list):
                label = r.name
                tt = tooltips[i]
                formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
                hover=HoverTool(tooltips = tt, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
                bokeh_figure.add_tools(hover)

                if guideline:
                    cross= CrosshairTool()
                    bokeh_figure.add_tools(cross)

            if axis_type == 'linear':
                if maxou  < 1e4 :
                    bokeh_figure.yaxis.formatter = BasicTickFormatter(use_scientific=False)

            bokeh_figure.legend.label_text_font_size = "12px"
            panel = TabPanel(child=bokeh_figure, title = axis_type)
            panels.append(panel)
            bokeh_figure.legend.background_fill_alpha = 0.6

            bokeh_figure.legend.location  = "top_left"
            bokeh_figure.legend.click_policy="hide"
            bokeh_figure.legend.label_text_font_size = '8pt'
            if len(which) > 1 and len(which)*len(input['where'].unique())>16:
                CoaWarning('To much labels to be displayed ...')
                bokeh_figure.legend.visible=False
            bokeh_figure.xaxis.formatter = DatetimeTickFormatter(
                days = "%d/%m/%y", months = "%d/%m/%y", years = "%b %Y")
            bokeh_visu().bokeh_legend(bokeh_figure)
            listfigs.append(bokeh_figure)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' SPIRAL PLOT '''
    def bokeh_spiral_plot(self, **kwargs):
        panels = []
        listfigs = []
        input = kwargs.get('input')
        which = kwargs.get('which')

        if isinstance(input['rolloverdisplay'].iloc[0],list):
            input['rolloverdisplay'] = input['where']
        borne = 300

        bokeh_figure = self.bokeh_figure(x_range=[-borne, borne], y_range=[-borne, borne], match_aspect=True,**kwargs)

        if len(input['where'].unique()) > 1 :
            print('Can only display spiral for ONE location. I took the first one:', input['where'][0])
            input = input.loc[input['where'] == input['where'][0]].copy()
        input["dayofyear"]=input.date.dt.dayofyear
        input['year']=input.date.dt.year
        input['cases'] = input[which]

        K = 2*input[which].max()
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input["dayofyear_angle"] = input["dayofyear"]*2 * np.pi/365
        input["r_baseline"] = input.apply(lambda x : ((x["year"]-2020)*2 * np.pi + x["dayofyear_angle"])*K,axis=1)
        size_factor = 16
        input["r_cas_sup"] = input.apply(lambda x : x["r_baseline"] + 0.5*x[which]*size_factor,axis=1)
        input["r_cas_inf"] = input.apply(lambda x : x["r_baseline"] - 0.5*x[which]*size_factor,axis=1)

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
        bokeh_figure.patches(xcol,ycol,color='blue',fill_alpha = 0.5)

        src = ColumnDataSource(data=dict(
        x=x_base,
        y=y_base,
        date=input['date'],
        cases=input['cases']
        ))
        bokeh_figure.line( x = 'x', y = 'y', source = src, legend_label = input['where'][0],
                        line_width = 3, line_color = 'blue')
        circle = bokeh_figure.circle('x', 'y', size=2, source=src)

        cases_custom = bokeh_visu().rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               renderers=[circle],
                               point_policy="snap_to_data")
        bokeh_figure.add_tools(hover_tool)

        outer_radius=250
        [bokeh_figure.annular_wedge(
            x=0, y=0, inner_radius=0, outer_radius=outer_radius, start_angle=i*np.pi/6,\
            end_angle=(i+1)*np.pi/6,fill_color=None,line_color='black',line_dash='dotted')
        for i in range(12)]

        label = ['January','February','March','April','May','June','July','August','September','October','November','December']
        xr,yr = polar(np.linspace(0, 2 * np.pi, 13),outer_radius,1)
        bokeh_figure.text(xr[:-1], yr[:-1], label,text_font_size="9pt", text_align="center", text_baseline="middle")

        bokeh_figure.legend.background_fill_alpha = 0.6
        bokeh_figure.legend.location = "top_left"
        bokeh_figure.legend.click_policy="hide"
        return bokeh_figure

    ''' SCROLLINGMENU PLOT '''
    def bokeh_menu_plot(self, **kwargs):
        '''
        -----------------
        Create a date plot, with a scrolling menu location, according to arguments.
        See help(bokeh_menu_plot).
        Keyword arguments
        -----------------
        len(location) > 2
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
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
        which= kwargs.get('which')
        guideline = kwargs.get('guideline',self.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('guideline',self.d_graphicsinput_args['mode'][0])
        if isinstance(which,list):
            which=which[0]

        uniqloc = list(input['where'].unique())
        uniqloc.sort()
        if 'where' in input.columns:
            if len(uniqloc) < 2:
                raise CoaTypeError('What do you want me to do ? You have selected, only one country.'
                                   'There is no sens to use this method. See help.')
        input = input[['date', 'where', which]]
        input = input.sort_values(by='where', ascending = True).reset_index(drop=True)

        mypivot = pd.pivot_table(input, index='date', columns='where', values=which)
        column_order = uniqloc
        mypivot = mypivot.reindex(column_order, axis=1)
        source = ColumnDataSource(mypivot)

        filter_data1 = mypivot[[uniqloc[0]]].rename(columns={uniqloc[0]: 'cases'})
        src1 = ColumnDataSource(filter_data1)

        filter_data2 = mypivot[[uniqloc[1]]].rename(columns={uniqloc[1]: 'cases'})
        src2 = ColumnDataSource(filter_data2)

        cases_custom = bokeh_visu().rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               mode = mode, point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in self.optionvisu.ax_type:
            bokeh_figure = self.bokeh_figure( y_axis_type = axis_type, x_axis_type = 'datetime', **kwargs)

            bokeh_figure.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            bokeh_figure.xaxis.formatter = DatetimeTickFormatter(
                days = ["%d/%m/%y"], months = ["%d/%m/%y"], years = ["%b %Y"])

            bokeh_figure.add_tools(hover_tool)
            if guideline:
                cross= CrosshairTool()
                bokeh_figure.add_tools(cross)
            def add_line(src, options, init, color):
                s = Select(options = options, value = init)
                r = bokeh_figure.line(x = 'date', y = 'cases', source = src, line_width = 3, line_color = color)
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
            bokeh_figure.add_layout(Legend(items = [li1, li2]))
            bokeh_figure.legend.location = 'top_left'
            layout = row(column(row(s1, s2), row(bokeh_figure)))
            panel = Panel(child = layout, title = axis_type)
            panels.append(panel)

        tabs = Tabs(tabs = panels)
        label = bokeh_figure.title
        return tabs

    ''' YEARLY PLOT '''
    def bokeh_yearly_plot(self,**kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(bokeh_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pysrc.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
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
        which = kwargs['which']
        guideline = kwargs.get('guideline',self.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('mode',self.d_graphicsinput_args['mode'][0])

        if len(input['where'].unique()) > 1 :
            CoaWarning('Can only display yearly plot for ONE location. I took the first one:'+ input['where'][0])
        if isinstance(which[0],list):
            which = which[0][0]
            CoaWarning('Can only display yearly plot for ONE which value. I took the first one:'+ which)

        input = input.loc[input['where'] == input['where'][0]].copy()

        panels = []
        listfigs = []
        cases_custom = bokeh_visu().rollerJS()
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        allyears = list(input.allyears.unique())
        if isinstance(input['rolloverdisplay'].iloc[0],list):
            input['rolloverdisplay'] = input['where']
        #if len(which)>1:
        #    CoaError('Only one variable could be displayed')
        #else:
        #    which=which[0]
        for axis_type in self.optionvisu.ax_type:
            bokeh_figure = self.bokeh_figure( y_axis_type = axis_type,**kwargs)
            i = 0
            r_list=[]
            maxou=-1000
            input['cases']=input[which]
            line_style = ['solid', 'dashed', 'dotted', 'dotdash']
            colors = itertools.cycle(self.optionvisu.lcolors)
            for loc in list(input['where'].unique()):
                for year in allyears:
                    input = input.loc[(input['where'] == loc) & (input['date'].dt.year.eq(year))].reset_index(drop = True)
                    src = ColumnDataSource(input)
                    leg = str(year) + ' ' + loc
                    r = bokeh_figure.line(x = 'dayofyear', y = which, source = src,
                                     color = next(colors), line_width = 3,
                                     legend_label = leg,
                                     hover_line_width = 4, name = which)
                    maxou=max(maxou,np.nanmax(input[which].values))

            label = which
            tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), ('Cases', '@cases{0,0.0}')]
            formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
            hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = mode)  # ,PanTool())
            bokeh_figure.add_tools(hover)
            if guideline:
                cross= CrosshairTool()
                bokeh_figure.add_tools(cross)

            if axis_type == 'linear':
                if maxou  < 1e4 :
                    bokeh_figure.yaxis.formatter = BasicTickFormatter(use_scientific=False)

            bokeh_figure.legend.label_text_font_size = "12px"
            panel = Panel(child=bokeh_figure, title = axis_type)
            panels.append(panel)
            bokeh_figure.legend.background_fill_alpha = 0.6

            bokeh_figure.legend.location = "top_left"
            bokeh_figure.legend.click_policy="hide"

            minyear=input.date.min().year
            labelspd=input.loc[(input.allyears.eq(2023)) & (input.date.dt.day.eq(1))]
            bokeh_figure.xaxis.ticker = list(labelspd['dayofyear'].astype(int))
            replacelabelspd =  labelspd['date'].apply(lambda x: str(x.strftime("%b")))
            #label_dict = dict(zip(input.loc[input.allyears.eq(minyear)]['daymonth'],input.loc[input.allyears.eq(minyear)]['date'].apply(lambda x: str(x.day)+'/'+str(x.month))))
            bokeh_figure.xaxis.major_label_overrides = dict(zip(list(labelspd['dayofyear'].astype(int)),list(replacelabelspd)))

            bokeh_visu().bokeh_legend(bokeh_figure)
            listfigs.append(bokeh_figure)

        tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')]
        formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
        hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
        bokeh_figure.add_tools(hover)
        if guideline:
            cross= CrosshairTool()
            bokeh_figure.add_tools(cross)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' VERTICAL HISTO '''
    #@importbokeh
    def bokeh_histo(self, **kwargs):
        '''
            -----------------
            Create 1D histogramme by value according to arguments.
            See help(bokeh_histo).
            Keyword arguments
            -----------------
            - input : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
            - which = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - graph_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - when : default min and max according to the inpude DataFrame.
                     Dates are given under the format dd/mm/yyyy.
                     when format [dd/mm/yyyy : dd/mm/yyyy]
                     if [:dd/mm/yyyy] min date up to
                     if [dd/mm/yyyy:] up to max date
        '''
        which=kwargs.get('which')
        input = kwargs.get('input')
        input = input.rename(columns = {'cases': which})
        bins = kwargs.get('bins', self.d_graphicsinput_args['bins'])
        HoverTool = kwargs.get('HoverTool')
        PrintfTickFormatter = kwargs.get('PrintfTickFormatter')
        Range1d = kwargs.get('Range1d')
        ColumnDataSource = kwargs.get('ColumnDataSource')
        TabPanel = kwargs.get('TabPanel')
        Tabs = kwargs.get('Tabs')
        min_val = input[which].min()
        max_val =  input[which].max()

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
        for i in range(len(input)):
            rank = bisect.bisect_left(interval, input.iloc[i][which])
            if rank == bins+1:
                rank = bins
            contributors[rank].append(input.iloc[i]['where'])

        lcolors = iter(self.lcolors)

        contributors = dict(sorted(contributors.items()))
        frame_histo = pd.DataFrame({
                          'left': [0]+interval[:-1],
                          'right':interval,
                          'middle_bin': [format((i+j)/2, ".1f") for i,j in zip([0]+interval[:-1],interval)],
                          'top': [len(i) for i in list(contributors.values())],
                          'contributors': [', '.join(i) for i in contributors.values()],
                          'colors': [next(lcolors) for i in range(len(interval)) ]})
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
            bokeh_figure = self.bokeh_figure(x_axis_type=x_axis_type, y_axis_type=y_axis_type, **kwargs)

            #bokeh_figure.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            #bokeh_figure.xaxis[0].formatter = PrintfTickFormatter(format="%4.2e")
            bokeh_figure.add_tools(hover_tool)
            bokeh_figure.x_range = Range1d(1.05 * interval[0], 1.05 * interval[-1])
            bokeh_figure.y_range = Range1d(0, 1.05 * frame_histo['top'].max())
            if x_axis_type == "log":
                left = 0.8
                if frame_histo['left'][0] <= 0:
                    frame_histo.at[0, 'left'] = left
                else:
                    left  = frame_histo['left'][0]
                bokeh_figure.x_range = Range1d(left, 10 * interval[-1])

            if y_axis_type == "log":
                bottom = 0.0001
                bokeh_figure.y_range = Range1d(0.001, 10 * frame_histo['top'].max())

            bokeh_figure.quad(source=ColumnDataSource(frame_histo), top='top', bottom=bottom, left='left', \
                             right='right', fill_color='colors')
            panel = TabPanel(child=bokeh_figure, title=axis_type_title)
            panels.append(panel)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' VERTICAL HISTO '''
    #@importbokeh
    def bokeh_horizonhisto(self, **kwargs):
        '''
            -----------------
            Create 1D histogramme by location according to arguments.
            See help(bokeh_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
            - which = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - graph_width = Width_Height_Default[0]
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

        #ColumnDataSource = kwargs.get('ColumnDataSource')
        #TabPanel = kwargs.get('TabPanel')
        #Range1d = kwargs.get('Range1d')
        #NumeralTickFormatter = kwargs.get('NumeralTickFormatter')
        #LabelSet = kwargs.get('LabelSet')
        #Tabs = kwargs.get('Tabs')

        #dateslider=kwargs.get('dateslider')
        #toggl=kwargs.get('toggl')
        input = kwargs.get('input')
        input = input.drop(columns='geometry')
        which = kwargs.get('which')
        mode = kwargs.get('mode',self.d_graphicsinput_args['mode'])
        mapoption = kwargs.get('mapoption', self.d_graphicsinput_args['mapoption'])

        input['left'] = input[which]
        input['right'] = input[which]
        input['left'] = input['left'].apply(lambda x: 0 if x > 0 else x)
        input['right'] = input['right'].apply(lambda x: 0 if x < 0 else x)

        n = len(input.index)
        ymax = self.graph_height

        input['top'] = [ymax*(n-i)/n + 0.5*ymax/n   for i in range(n)]
        input['bottom'] = [ymax*(n-i)/n - 0.5*ymax/n for i in range(n)]
        input['horihistotexty'] = input['bottom'] + 0.5*ymax/n
        input['horihistotextx'] = input['right']

        if 'label%' in mapoption:
            input['right'] = input['right'].apply(lambda x: 100.*x)
            input['horihistotextx'] = input['right']
            input['horihistotext'] = [str(round(i))+'%' for i in input['right']]
        if 'textinteger' in mapoption:
            input['horihistotext'] = input['right'].astype(float).astype(int).astype(str)
        else:
            input['horihistotext'] = [ '{:.3g}'.format(float(i)) if float(i)>1.e4 or float(i)<0.01 else round(float(i),2) for i in input['right'] ]
            input['horihistotext'] = [str(i) for i in input['horihistotext']]

        lcolors = iter(self.lcolors)
        colors = next(lcolors)
        input['colors'] = [next(lcolors) for i in range(len(input))]
        srcfiltered = ColumnDataSource(data = input)
        new_panels = []
        for axis_type in self.d_graphicsinput_args['ax_type']:
            bokeh_figure = self.bokeh_figure( x_axis_type = axis_type)
            #fig = panels[i].child
            bokeh_figure.y_range = Range1d(min(srcfiltered.data['bottom']), max(srcfiltered.data['top']))
            #bokeh_figure.yaxis[0].formatter = NumeralTickFormatter(format="0.0")
            ytick_loc = [int(i) for i in srcfiltered.data['horihistotexty']]
            bokeh_figure.yaxis.ticker  = ytick_loc
            label_dict = dict(zip(ytick_loc,srcfiltered.data['where']))
            bokeh_figure.yaxis.major_label_overrides = label_dict


            bokeh_figure.quad(source = srcfiltered,
                top='top', bottom = 'bottom', left = 'left', right = 'right', color = 'colors', line_color = 'black',
                line_width = 1, hover_line_width = 2)

            labels = LabelSet(
                    x = 'horihistotextx',
                    y = 'horihistotexty',
                    x_offset=5,
                    y_offset=-4,
                    text = 'horihistotext',
                    source = srcfiltered,text_font_size='10px',text_color='black')

            cases_custom = bokeh_visu().rollerJS()
            hover_tool = HoverTool(tooltips=[('where', '@where'), (which, '@right{0,0.0}'), ],
                                   formatters = {'where': 'printf', '@{' + 'right' + '}': cases_custom, '%':'printf'},
                                   mode = mode, point_policy="snap_to_data")
            bokeh_figure.add_tools(hover_tool)
            bokeh_figure.add_layout(labels)

            panel = TabPanel(child = bokeh_figure, title = axis_type)
            new_panels.append(panel)
        tabs = Tabs(tabs = new_panels)
        dateslider = self.d_graphicsinput_args['dateslider']

        if dateslider:
                toggl = Toggle(label='► Play',active=False, button_type="success",height=30,width=10)
                #toggl.js_on_change('active',toggl_js)
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

        df['textdisplayed'] = df['where'].str.pad(36, side = "left")
        try:
            locale.setlocale(locale.LC_ALL, 'en_US')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            except:
                raise CoaError("Locale setting problem. Please contact support@pycoa_fr")

        df['textdisplayed2'] =  ['      '+str(round(100*i,1))+'%' for i in df['percentage']]
        df.loc[df['diff'] <= np.pi/20,'textdisplayed']=''
        df.loc[df['diff'] <= np.pi/20,'textdisplayed2']=''
        return df

    def bokeh_pie(self, **kwargs):
        '''
            -----------------
            Create a pie chart according to arguments.
            See help(bokeh_pie).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
            - which = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - graph_width = Width_Height_Default[0]
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
        bokeh_figure = panels[0].child
        bokeh_figure.graph_height=400
        bokeh_figure.graph_width=400
        bokeh_figure.x_range = Range1d(-1.1, 1.1)
        bokeh_figure.y_range = Range1d(-1.1, 1.1)
        bokeh_figure.axis.visible = False
        bokeh_figure.xgrid.grid_line_color = None
        bokeh_figure.ygrid.grid_line_color = None

        bokeh_figure.wedge(x=0, y=0, radius=1.,line_color='#E8E8E8',
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'), fill_color='colors',
        legend_label='where', source=srcfiltered)
        bokeh_figure.legend.visible = False

        labels = LabelSet(x=0, y=0,text='textdisplayed',angle=cumsum('angle', include_zero=True),
        text_font_size="10pt",source=srcfiltered,render_mode='canvas')

        labels2 = LabelSet(x=0, y=0, text='textdisplayed2',
        angle=cumsum('angle', include_zero=True),text_font_size="8pt",source=srcfiltered)

        bokeh_figure.add_layout(labels)
        bokeh_figure.add_layout(labels2)
        if dateslider:
            bokeh_figure = column(dateslider,bokeh_figure)
        return bokeh_figure

    def deco_bokeh_geo(func):
        @wraps(func)
        def innerdeco_bokeh_geo(self,**kwargs):
            input = kwargs.get('input')
            which = kwargs.get("which")
            input['cases'] = input[which]
            return func(self, **kwargs)
        return innerdeco_bokeh_geo

    @importbokeh
    @deco_bokeh_geo
    def bokeh_map(self,**kwargs):
        '''
            -----------------
            Create a map bokeh with arguments.
            See help(bokeh_histo).
            Keyword arguments
            -----------------
            - srcfiltered : A DataFrame with a Pysrc.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
            - which = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - graph_width = Width_Height_Default[0]
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
            - mapoption: False
        '''
        input=kwargs.get('input')
        sourcemapoption=kwargs.get('sourcemapoption')
        tile = kwargs.get('tile')
        tile = bokeh_visu.convert_tile(tile, 'bokeh')
        wmt = WMTSTileSource(url = tile)
        bokeh_figure = self.bokeh_figure(x_axis_type = 'mercator', y_axis_type = 'mercator', match_aspect = True)
        bokeh_figure.add_tile(wmt, retina=True)

        dateslider = kwargs.get('dateslider')
        mapoption = kwargs.get('mapoption')
        min_col, max_col, min_col_non0 = 3*[0.]
        try:
            if dateslider:
                min_col, max_col = bokeh_visu().min_max_range(np.nanmin(input['cases']),
                                                         np.nanmax(input['cases']))
                min_col_non0 = (np.nanmin(input.loc[input['cases']>0.]['cases']))
            else:
                min_col, max_col = bokeh_visu().min_max_range(np.nanmin(input['cases']),
                                                         np.nanmax(input['cases']))
                min_col_non0 = (np.nanmin(input.loc[input['cases']>0.]['cases']))
        except ValueError:
            pass
        #min_col, max_col = np.nanmin(inputed['cases']),np.nanmax(inputed['cases'])
        input = input.drop(columns='date')
        json_data = json.dumps(json.loads(input.to_json()))
        inputed = GeoJSONDataSource(geojson=json_data)

        invViridis256 = Viridis256[::-1]
        if mapoption and 'log' in mapoption:
            color_mapper = LogColorMapper(palette=invViridis256, low=min_col_non0, high=max_col, nan_color='#ffffff')
        else:
            color_mapper = LinearColorMapper(palette=invViridis256, low=min_col, high=max_col, nan_color='#ffffff')
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4, bar_line_cap='round',
                             border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))

        if mapoption and 'label%' in mapoption:
            color_bar.formatter = BasicTickFormatter(use_scientific=False)
            color_bar.formatter = NumeralTickFormatter(format="0.0%")

        self.bokeh_figure().add_layout(color_bar, 'below')
        #self.bokeh_figure().add_layout(Title(text=self.subtitle, text_font_size="8pt", text_font_style="italic"), 'below')
        if dateslider:
            allcases_location, allcases_dates = pd.DataFrame(), pd.DataFrame()
            allcases_location = input.groupby('where')['cases'].apply(list)
            input_tmp = input.drop_duplicates(subset = ['where']).drop(columns = 'cases')
            input_tmp = pd.merge(input_tmp, allcases_location, on = 'where')
            input_tmp  = input_tmp.drop_duplicates(subset = ['where'])
            input_tmp = ColumnDataSource(input_tmp.drop(columns=['geometry']))

            callback = CustomJS(args =  dict(source = input_tmp, source_filter = inputed,
                                          datesliderjs = dateslider, title=bokeh_figure.title,
                                          color_mapperjs = color_mapper, mapoptionjs = sourcemapoption),
                        code = """
                        var ind_date_max = (datesliderjs.end-datesliderjs.start)/(24*3600*1000);
                        var ind_date = (datesliderjs.value-datesliderjs.start)/(24*3600*1000);
                        var new_cases = [];
                        var dict = {};
                        var iloop = source_filter.data['where'].length;

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

                        if (mapoptionjs.get_length() !== 0){
                            mapoptionjs.data['cases'] = source_filter.data['cases'];
                            }
                        for (var i = 0; i < mapoptionjs.get_length(); i++)
                        {
                            mapoptionjs.data['cases'][i] = form(mapoptionjs.data['cases'][i]).toString();
                            mapoptionjs.data['rolloverdisplay'][i] = source_filter.data['rolloverdisplay'][i];
                        }

                        var tmp = title.text;
                        tmp = tmp.slice(0, -11);
                        var dateconverted = new Date(datesliderjs.value);
                        var dd = String(dateconverted.getDate()).padStart(2, '0');
                        var mm = String(dateconverted.getMonth() + 1).padStart(2, '0'); //January is 0!
                        var yyyy = dateconverted.getFullYear();
                        var dmy = dd + '/' + mm + '/' + yyyy;
                        title.text = tmp + dmy+")";

                        if (mapoptionjs.get_length() !== 0)
                            mapoptionjs.change.emit();

                        color_mapperjs.high=Math.max.apply(Math, new_cases);
                        color_mapperjs.low=Math.min.apply(Math, new_cases);
                        console.log(mapoptionjs.data['cases']);
                        source_filter.change.emit();
                    """)
            dateslider.js_on_change('value', callback)
            # Set up Play/Pause button/toggle JS
            date_list = pd.date_range(input.date.min(),input.date.max()-dt.timedelta(days=1),freq='d').to_list()
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

        bokeh_figure.xaxis.visible = False
        bokeh_figure.yaxis.visible = False
        bokeh_figure.xgrid.grid_line_color = None
        bokeh_figure.ygrid.grid_line_color = None
        bokeh_figure.patches('xs', 'ys', source = inputed,
                            fill_color = {'field': 'cases', 'transform': color_mapper},
                            line_color = 'black', line_width = 0.25, fill_alpha = 1)
        if mapoption:
            if 'text' in mapoption or 'textinteger' in mapoption:

                if 'textinteger' in mapoption:
                    sourcemapoption.data['cases'] = sourcemapoption.data['cases'].astype(float).astype(int).astype(str)
                sumgeo.loc[:,'centroidx'] = sumgeo['geometry'].centroid.x
                sumgeo.loc[:,'centroidy'] = sumgeo['geometry'].centroid.y
                labels = LabelSet(
                    x = 'centroidx',
                    y = 'centroidy',
                    text = 'cases',
                    source = sourcemapoption, text_font_size='10px',text_color='white',background_fill_color='grey',background_fill_alpha=0.5)
                bokeh_figure.add_layout(labels)

        #cases_custom = AllVisu.rollerJS()
        callback = CustomJS(code="""
        //document.getElementsByClassName('bk-tooltip')[0].style.backgroundColor="transparent";
        document.getElementsByClassName('bk-tooltip')[0].style.opacity="0.7";
        """ )
        tooltips = """
                    <b>location: @where<br>
                    cases: @cases{0,0.0} </b>
                    """

        bokeh_figure.add_tools(HoverTool(tooltips = tooltips,
        formatters = {'where': 'printf', 'cases': 'printf',},
        point_policy = "snap_to_data",callback=callback))  # ,PanTool())
        if dateslider:
            bokeh_figure = column(dateslider, bokeh_figure,toggl)
        return show(bokeh_figure)

    @staticmethod
    def bokeh_savefig(fig,name):
        from bokeh.io import export_png
        export_png(fig, filename = name)

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
