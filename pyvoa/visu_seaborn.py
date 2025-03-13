# -*- coding: utf-8 -*-

"""
Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa_fr
License: See joint LICENSE file

Module : pyvoa.visu_seaborn

About :
-------

An interface module to easily plot pycoa_data with bokeh

"""
from pyvoa.tools import (
    extract_dates,
    verb,
    fill_missing_dates
)
from pyvoa.error import *
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

from pyvoa.jsondb_parser import MetaInfo

class visu_seaborn:
    ######SEABORN#########
    ######################
    def __init__(self,):
        pass

    def decoplotseaborn(func):
        """
        decorator for seaborn plot
        """
        @wraps(func)
        def inner_plot(self, **kwargs):
            import matplotlib.pyplot as plt
            import seaborn as sns
            fig, ax = plt.subplots(1, 1,figsize=(12, 8))
            input = kwargs.get('input')
            which = kwargs.get('which')
            title = f"Graphique de {which}"
            if 'where' in kwargs:
                title += f" - {kwargs.get('where')}"
            kwargs['title'] = title
            # top_countries = (input.groupby('where')[which].sum()
            #              .nlargest(Max_Countries_Default).index.tolist())
            # filtered_input = input[input['where'].isin(top_countries)]

            loc = list(input['where'].unique())
            kwargs['plt'] = plt
            kwargs['sns'] = sns
            return func(self, **kwargs)
        return inner_plot

    def decohistseaborn(func):
        """
        decorator for seaborn histogram
        """
        @wraps(func)
        def inner_hist(self,**kwargs):
            input = kwargs.get('input')
            which = kwargs.get('which')
            if isinstance(which, list):
                which = which[0]

            input = (input.sort_values('date')
                  .drop_duplicates('where', keep='last')
                  .drop_duplicates(['where', which])
                  .sort_values(by=which, ascending=False)
                  .reset_index(drop=True))

            kwargs['input'] = input
            return func(self, **kwargs)
        return inner_hist

    #####SEABORN PLOT#########
    @decoplotseaborn
    def seaborn_date_plot(self, **kwargs):
        """
        Create a seaborn line plot with date on x-axis and which on y-axis.
        """
        input = kwargs['input']
        which = kwargs['which']
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        st=['-','--',':']
        for idx, i in enumerate(which):
            input['where+i']=input['where'].apply(lambda x: x+', '+i)
            sns.lineplot(data=input, x='date', y = i, hue='where+i',style='where+i')#linestyle=st[idx])
        plt.legend(title = "where", loc= "upper right",bbox_to_anchor=(1.04, 1))
        plt.title(title)
        plt.xlabel('Date')
        #plt.ylabel(', '.join(which))
        plt.xticks(rotation=45)
        return plt

    @decoplotseaborn
    def seaborn_versus_plot(self, **kwargs):
        input = kwargs['input']
        which = kwargs['which']
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(12, 8))

        sns.lineplot(data=input, x=which[0], y=which[1], hue='where')
        plt.legend(title = "where", loc= "upper right",bbox_to_anchor=(1.04, 1))
        plt.title(title)
        plt.xlabel(which[0])
        plt.ylabel(which[1])
        return plt

    @decoplotseaborn
    @decohistseaborn
    def seaborn_hist(self, **kwargs):
        """
        Create a seaborn vertical histogram with which on y-axis.
        """
        filtered_input = kwargs['filtered_input']
        which = kwargs['which']
        title = kwargs.get('title')

        # Créer le graphique
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.barplot(data=filtered_input, x='where', y=which, palette="viridis")
        plt.title(title)
        plt.xlabel('')  # Suppression de l'étiquette de l'axe x
        plt.ylabel(which)
        plt.xticks(rotation=70, ha='center')  # Rotation à 70 degrés et alignement central
        plt.show()

    @decohistseaborn
    def seaborn_hist_value(self, **kwargs):
        """
        Create a seaborn vertical histogram where the x-axis represents a numerical field.
        """
        input = kwargs['input']
        which = kwargs['which']
        title = kwargs.get('title')
        if isinstance(which, list):
            which = which[0]

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.histplot(data=filtered_input, x=which, bins=24, color='blue', kde=True)
        plt.title(title)
        plt.xlabel(which)
        plt.ylabel('Fréquence')
        plt.show()

    ######SEABORN HIST HORIZONTALE#########
    @decoplotseaborn
    @decohistseaborn
    def seaborn_hist_horizontal(self, **kwargs):
        """
        Create a seaborn horizontal histogram with which on x-axis.
        """
        input = kwargs['input']
        which = kwargs['which']
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        if isinstance(which, list):
            which = which[0]

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        sns.barplot(data=input, x=which, y='where', palette="viridis", errorbar=None)
        plt.title(title)
        plt.xlabel(which)
        plt.ylabel('')
        plt.xticks(rotation=45)
        return plt

    ######SEABORN BOXPLOT#########
    @decoplotseaborn
    def seaborn_pie(self, **kwargs):
        """
        Create a seaborn pairplot
        """
        input = kwargs['input']
        which = kwargs['which']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(14, 7))
        plt.pie(input[which], labels=input['where'], autopct='%1.1f%%')
        plt.xlabel(which)
        plt.ylabel('')
        plt.xticks(rotation=45)
        return plt

    ######SEABORN heatmap#########
    @decoplotseaborn
    def seaborn_heatmap(self, **kwargs):
        """
        Create a seaborn heatmap
        """
        CoaWarning("BEWARE !!! THIS visulasation need to be checked !!!")
        input = kwargs.get('input')
        which = kwargs.get('which')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')

        input['month'] = [m.month for m in input['date']]
        input['year'] = [m.year for m in input['date']]

        data_pivot = input.pivot_table(index='month', columns='year', values='daily')

        total = data_pivot.sum().sum()

        sns.heatmap(data_pivot, annot=True, fmt=".1f", linewidths=.5, cmap='plasma')
        plt.title(f'Heatmap of {which.replace("_", " ").capitalize()} by Month and Year')
        plt.xlabel('Year')
        plt.ylabel('Month')

        # Afficher le total en dehors du graphique
        plt.text(0, data_pivot.shape[0] + 1, f'Total: {total}', fontsize=12)
        return plt
