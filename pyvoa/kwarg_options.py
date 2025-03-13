# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa_fr
License: See joint LICENSE file

Module : pyvoa.allvisu

About :
-------

An interface module to easily plot pycoa_data with bokeh

"""
from pyvoa.tools import kwargs_keystesting
from pyvoa.error import *
import math
import pandas as pd
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

import bisect
from functools import wraps

__all__ = ['InputOption']

class InputOption():
    """
        Option visualisation !
    """
    def __init__(self):
        self.d_batchinput_args  = {
                'where':[''],\
                        'option':['nonneg','smooth7','sumall',
                                  'bypop=0','bypop=100', 'bypop=1k', 'bypop=100k','bypop=1M'],\
                                          'which':[''],\
                                          'what':['current','daily','weekly'],\
                                          'when':[''],\
                                          'input':[pd.DataFrame()],\
                                          'output':['pandas','geopandas','list','dict','array']
                                          }
        self.listchartkargskeys = list(self.d_batchinput_args.keys())
        self.listchartkargsvalues = list(self.d_batchinput_args.values())

        self.d_graphicsinput_args = {
                'title':'',\
                        'copyright': 'pyvoa',\
                        'mode':['mouse','vline','hline'],\
                        'typeofhist':['bylocation','byvalue','pie'],\
                        'typeofplot':['date','menulocation','versus','spiral','yearly'],\
                        'bins':10,\
                        'vis':['matplotlib','bokeh','folium','seaborn'],\
                        'tile' : ['openstreet','esri','stamen','positron'],\
                        'orientation':['horizontal','vertical'],\
                        'dateslider':[False,True],\
                        'mapoption':['text','textinteger','spark','label%','log','unsorted','dense'],\
                        'guideline':[False,True],\
                        'ax_type':['linear', 'log']
                        }
        self.listviskargskeys = list(self.d_graphicsinput_args.keys())
        self.dicokfront = {}


    def test_add_graphics_libraries(self,libraries):
        '''
            Tests the presence of the specified graphical libraries
        '''
        results = {}
        for lib in libraries:
            try:
                importlib.import_module(lib)
                results[lib] = True
            except ImportError:
                results[lib] = False
        return results
    def setkwargsfront(self,kw):
        kwargs_keystesting(kw, list(self.d_graphicsinput_args.keys())+list(self.d_graphicsinput_args.keys()), 'Error with this resquest (not available in setoptvis)')
        self.dicokfront = kw

    def getkwargsfront(self):
        return self.dicokfront
