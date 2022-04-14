# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - april 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file
Module : report
About
-----
This is the PyCoA rapport module it gives all available information concerning a database key words
"""

def dbstructured(namedb):
    '''
    Return from slected covid19 db:
        - name db & structure type : 'date_as_columns','date_as_rows'
        - variable keeped and the rename
        - url information
        bdstructure=['date_as_columns','date_as_rows']
    '''
    if namedb == 'jhu'
        dbformat={'name':'date_as_columns'}
        mainurl = 'https://github.com/CSSEGISandData/COVID-19'
        varkeeped = ['deaths','confirmed']
        varrenamed = ['tot_' for i in varkeeped]
        vardef = [
        'counts include confirmed and probable (where reported)',
        "counts include confirmed and probable (where reported)",
        ]
        varurl =[
              'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv',\
              'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv',\
              ]
