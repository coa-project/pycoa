# -*- coding: utf-8 -*-
"""
Project : PyCoA
Date :    april 2020 - march 2022
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.covid19

About :
-------

Main class definitions for covid19 dataset access. Currently, we are only using the JHU CSSE data.
The parser class gives a simplier access through an already filled dict of data

"""

import pandas
from collections import defaultdict
import numpy as np
import pandas as pd
import datetime as dt

import sys
from coa.tools import info, verb, kwargs_test, get_local_from_url, fill_missing_dates, check_valid_date, week_to_date, get_db_list_dict

import coa.geo as coge
import coa.dbinfo as dbinfo
import coa.display as codisplay
from coa.error import *
from scipy import stats as sps
import random
from functools import reduce
import collections
import re
import requests
import datetime
import math

class DataBase(object):
   """
   DataBase class
   Parse a Covid-19 database and filled the pandas python objet : mainpandas
   It takes a string argument, which can be: 'jhu','spf', 'spfnational','owid', 'opencovid19' and 'opencovid19national'
   """
   def __init__(self, db_name):
        """
         Fill the pandas_datase
        """
        verb("Init of covid19.DataBase()")
        self.database_name = list(get_db_list_dict().keys())
        self.database_type = get_db_list_dict()
        self.available_options = ['nonneg', 'nofillnan', 'smooth7', 'sumall']
        self.available_keywords = []
        self.dates = []
        self.database_columns_not_computed = {}
        self.db = db_name
        self.geo_all = ''
        self.database_url = []
        self.db_world=None
        self.dbfullinfo = dbinfo.DBInfo(db_name)
        if self.db not in self.database_name:
            raise CoaDbError('Unknown ' + self.db + '. Available database so far in PyCoa are : ' + str(self.database_name), file=sys.stderr)
        else:
            try:
                if get_db_list_dict()[self.db][1] == 'nation': # world wide dba
                    self.db_world = True
                    self.geo = coge.GeoManager('name')
                    self.geo_all = 'world'
                else: # local db
                    self.db_world = False
                    self.geo = coge.GeoCountry(get_db_list_dict()[self.db][0])
                    if get_db_list_dict()[self.db][1] == 'region':
                        self.geo_all = self.geo.get_region_list()
                    elif get_db_list_dict()[self.db][1] == 'subregion':
                        self.geo_all = self.geo.get_subregion_list()
                    else:
                        CoaError('Granularity problem, neither region or subregion')
                self.set_display(self.db,self.geo)

                # specific reading of data according to the db
                if self.db == 'jhu':
                    info('JHU aka Johns Hopkins database selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'jhu-usa': #USA
                    info('USA, JHU aka Johns Hopkins database selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'imed':
                    info('Greece, imed database selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'rki': # DEU
                    info('DEU, Robert Koch Institut data selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'govcy': #CYP
                    gov = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(gov)
                elif self.db == 'dpc': #ITA
                    dpc = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(dpc)
                elif self.db == 'dgs': # PRT
                    dgs = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(dgs)
                elif self.db == 'jpnmhlw' : # JPN
                    jpn = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(jpn)
                elif self.db == 'escovid19data': # ESP
                    esp = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(esp)
                elif self.db == 'sciensano': #Belgian institute for health,
                    bel = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(bel)
                elif self.db == 'phe': # GBR from owid
                    phe = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(phe)
                elif self.db == 'moh': # MYS
                    moh = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(moh)
                elif self.db == 'mpoxgh' :
                    mpoxgh = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(mpoxgh)
                elif self.db == 'spf' or self.db == 'spfnational':
                    spf = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(spf) # with 'tot_dc' first
                elif self.db == 'owid':
                    owid = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(owid)
                elif self.db == 'risklayer':
                    eur = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(eur)
                elif self.db == 'europa':
                    euro = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(euro)
                elif self.db == 'insee':
                    insee = self.dbfullinfo.get_pandas()
                    self.return_structured_pandas(insee)
            except:
                raise CoaDbError("An error occured while parsing data of "+self.get_db()+". This may be due to a data format modification. "
                    "You may contact support@pycoa.fr. Thanks.")
            # some info
            info('Few information concernant the selected database : ', self.get_db())
            info('Available key-words, which ∈', self.dbfullinfo.get_available_keywords())
            info('Example of where : ',  ', '.join(random.choices(self.get_locations(), k=min(5,len(self.get_locations() ))   )), ' ...')
            info('Last date data ', self.get_dates().max())

   @staticmethod
   def factory(db_name):
       '''
        Return an instance to DataBase and to CocoDisplay methods
        This is recommended to avoid mismatch in labeled figures
       '''
       datab = DataBase(db_name)
       return  datab, datab.get_display()

   def set_display(self,db,geo):
       ''' Set the CocoDisplay '''
       self.codisp = codisplay.CocoDisplay(db, geo)

   def get_display(self):
       ''' Return the instance of CocoDisplay initialized by factory'''
       return self.codisp

   def get_db(self):
        '''
        Return the current covid19 database selected. See get_available_database() for full list
        '''
        return self.db

   def get_available_database(self):
        '''
        Return all the available Covid19 database
        '''
        return self.database_name

   def return_jhu_pandas(self):
        ''' For center for Systems Science and Engineering (CSSE) at Johns Hopkins University
            COVID-19 Data Repository by the see homepage: https://github.com/CSSEGISandData/COVID-19
            return a structure : pandas where - date - keywords
            for jhu where are countries (where uses geo standard)
            for jhu-usa where are Province_State (where uses geo standard)
            '''
        base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"+\
                                "csse_covid_19_data/csse_covid_19_time_series/"
        base_name = "time_series_covid19_"
        # previous are default for actual jhu db

        pandas_jhu = {}

        if self.db == 'jhu': # worldwide
            extension =  "_global.csv"
            jhu_files_ext = ['deaths', 'confirmed']
        elif self.db == 'jhu-usa': # 'USA'
            extension = "_US.csv"
            jhu_files_ext = ['deaths','confirmed']
        elif self.db == 'rki': # 'DEU'
            base_url = 'https://github.com/jgehrcke/covid-19-germany-gae/raw/master/'
            jhu_files_ext = ['deaths','cases']
            extension = '-rki-by-ags.csv'
            base_name = ''
        elif self.db == 'imed': # 'GRC'
            base_url = 'https://raw.githubusercontent.com/iMEdD-Lab/open-data/master/COVID-19/greece_'
            jhu_files_ext = ['deaths','cases']
            extension = '_v2.csv'
            base_name = ''
        else:
            raise CoaDbError('Unknown JHU like db '+str(self.db))

        self.available_keywords = []
        if self.db == 'rki':
                self.available_keywords = ['tot_deaths','tot_cases']
        pandas_list = []
        for ext in jhu_files_ext:
            fileName = base_name + ext + extension
            url = base_url + fileName
            self.database_url.append(url)
            pandas_jhu_db = pandas.read_csv(get_local_from_url(url,7200), sep = ',') # cached for 2 hours
            if self.db == 'jhu':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Country/Region':'where'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['Province/State','Lat','Long'])
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=['where'],var_name="date",value_name=ext)
                pandas_jhu_db = pandas_jhu_db.loc[~pandas_jhu_db['where'].isin(['Diamond Princess'])]
            elif self.db == 'jhu-usa':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Province_State':'where'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['UID','iso2','iso3','code3','FIPS',
                                    'Admin2','Country_Region','Lat','Long_','Combined_Key'])
                if 'Population' in pandas_jhu_db.columns:
                    pandas_jhu_db = pandas_jhu_db.melt(id_vars=['where','Population'],var_name="date",value_name=ext)
                else:
                    pandas_jhu_db = pandas_jhu_db.melt(id_vars=['where'],var_name="date",value_name=ext)
                removethose=['American Samoa','Diamond Princess','Grand Princess','Guam',
                'Northern Mariana Islands','Puerto Rico','Virgin Islands']
                pandas_jhu_db = pandas_jhu_db.loc[~pandas_jhu_db['where'].isin(removethose)]
            elif self.db == 'rki':
                pandas_jhu_db = pandas_jhu_db.drop(columns=['sum_'+ext])
                pandas_jhu_db = pandas_jhu_db.set_index('time_iso8601').T.reset_index().rename(columns={'index':'where'})
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=['where'],var_name="date",value_name=ext)
                pandas_jhu_db['where'] = pandas_jhu_db['where'].astype(str)
                pandas_jhu_db = pandas_jhu_db.rename(columns={'deaths':'tot_deaths','cases':'tot_cases'})
            elif self.db == 'imed':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'county_normalized':'where'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['Γεωγραφικό Διαμέρισμα','Περιφέρεια','county','pop_11'])
                ext='tot_'+ext
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=['where'],var_name="date",value_name=ext)
                self.available_keywords += [ext]
            else:
                raise CoaTypeError('jhu nor jhu-usa database selected ... ')

            pandas_jhu_db=pandas_jhu_db.groupby(['where','date']).sum().reset_index()
            pandas_list.append(pandas_jhu_db)
        if 'jhu' in self.db:
            pandas_list = [pan.rename(columns={i:'tot_'+i for i in jhu_files_ext}) for pan in pandas_list]
            self.available_keywords = ['tot_'+i for i in jhu_files_ext]
        uniqloc = list(pandas_list[0]['where'].unique())
        oldloc = uniqloc
        codedico={}
        toremove = None
        newloc = None
        location_is_code = False
        if self.db_world:
            d_loc_s = collections.OrderedDict(zip(uniqloc,self.geo.to_standard(uniqloc,output='list',db=self.get_db(),interpret_region=True)))
            self.slocation = list(d_loc_s.values())
            g=coge.GeoManager('iso3')
            codename = collections.OrderedDict(zip(self.slocation,g.to_standard(self.slocation,output='list',db=self.get_db(),interpret_region=True)))
        else:
            if self.database_type[self.db][1] == 'subregion':
                pdcodename = self.geo.get_subregion_list()
                self.slocation = uniqloc
                codename = collections.OrderedDict(zip(self.slocation,list(pdcodename.loc[pdcodename.code_subregion.isin(self.slocation)]['name_subregion'])))
                if self.db == 'jhu-usa':
                    d_loc_s = collections.OrderedDict(zip(uniqloc,list(pdcodename.loc[pdcodename.name_subregion.isin(uniqloc)]['code_subregion'])))
                    self.slocation = list(d_loc_s.keys())
                    codename = d_loc_s
                if self.db == 'rki':
                    d_loc_s = collections.OrderedDict(zip(uniqloc,list(pdcodename.loc[pdcodename.code_subregion.isin(uniqloc)]['name_subregion'])))
                    self.slocation = list(d_loc_s.values())
                    codename = d_loc_s
                    location_is_code = True
                    def notuse():
                        count_values=collections.Counter(d_loc_s.values())
                        duplicates_location = list({k:v for k,v in count_values.items() if v>1}.keys())
                        def findkeywithvalue(dico,what):
                            a=[]
                            for k,v in dico.items():
                                if v == what:
                                    a.append(k)
                            return a
                        codedupli={i:findkeywithvalue(d_loc_s,i) for i in duplicates_location}
            elif self.database_type[self.db][1] == 'region':
                codename = self.geo.get_data().set_index('name_region')['code_region'].to_dict()
                self.slocation = list(codename.keys())


        result = reduce(lambda x, y: pd.merge(x, y, on = ['where','date']), pandas_list)

        if location_is_code:
            result['codelocation'] = result['where']
            result['where'] = result['where'].map(codename)
        else:
            if self.db == 'jhu':
                result['where'] = result['where'].map(d_loc_s)
            result['codelocation'] = result['where'].map(codename)
        result = result.loc[result['where'].isin(self.slocation)]

        tmp = pd.DataFrame()
        if 'Kosovo' in uniqloc:
            #Kosovo is Serbia ! with geo.to_standard
            tmp=(result.loc[result['where'].isin(['Serbia'])]).groupby('date').sum().reset_index()
            tmp['where'] = 'Serbia'
            tmp['codelocation'] = 'SRB'
            kw = [i for i in self.available_keywords]
            colpos=['where', 'date'] + kw + ['codelocation']
            tmp = tmp[colpos]
            result = result.loc[~result['where'].isin(['Serbia'])]
            result = pd.concat([result,tmp])

        result['date'] = pd.to_datetime(result['date'],errors='coerce').dt.date
        result = result.sort_values(by=['where','date'])
        result = result.reset_index(drop=True)
        if self.db == 'jhu-usa':
            col=result.columns.tolist()
            ncol=col[:2]+col[3:]+[col[2]]
            result=result[ncol]
            self.available_keywords+=['Population']
        self.mainpandas = fill_missing_dates(result)
        self.dates  = self.mainpandas['date']


   def return_structured_pandas(self,mypandas,**kwargs):
        '''
        Return the mainpandas core of the PyCoA structure
        '''
        kwargs_test(kwargs,['columns_skipped'],
            'Bad args used in the return_structured_pandas function.')
        columns_skipped = kwargs.get('columns_skipped', None)
        if self.db_world and self.db not in ['govcy','spfnational','mpoxgh']:
            not_UN_nation_dict=['Kosovo','Serbia']
            tmp=(mypandas.loc[mypandas['where'].isin(not_UN_nation_dict)].groupby('date').sum()).reset_index()
            tmp['where'] = 'Serbia'
            tmp['iso_code'] = 'SRB'
            cols = tmp.columns.tolist()
            cols = cols[0:1] + cols[-1:] + cols[1:-1]
            tmp = tmp[cols]
            mypandas = mypandas.loc[~mypandas['where'].isin(not_UN_nation_dict)]
            mypandas = pd.concat([tmp,mypandas])
        if 'iso_code' in mypandas.columns:
            mypandas['iso_code'] = mypandas['iso_code'].dropna().astype(str)
            mypandasori=mypandas.copy()
            strangeiso3tokick = [i for i in mypandasori['iso_code'].dropna().unique() if not len(i)==3 ]
            mypandasori = mypandas.loc[~mypandas.iso_code.isin(strangeiso3tokick)]
            mypandasori = mypandasori.drop(columns=['where'])
            mypandasori = mypandasori.rename(columns={'iso_code':'where'})
            if self.db == 'owid':
                onlyowid = mypandas.loc[mypandas.iso_code.isin(strangeiso3tokick)]
                onlyowid = onlyowid.copy()
                onlyowid.loc[:,'where'] = onlyowid['where'].apply(lambda x : 'owid_'+x)
            mypandas = mypandasori
        if self.db == 'dpc':
            gd = self.geo.get_data()[['name_region','code_region']]
            A=['P.A. Bolzano','P.A. Trento']
            tmp=mypandas.loc[mypandas['where'].isin(A)].groupby('date').sum()
            tmp['where']='Trentino-Alto Adige'
            mypandas = mypandas.loc[~mypandas['where'].isin(A)]
            tmp = tmp.reset_index()
            mypandas = pd.concat([mypandas,tmp])
            uniqloc = list(mypandas['where'].unique())
            sub2reg = dict(gd.values)
            #collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_region.isin(uniqloc)]['code_region'])))
            mypandas['codelocation'] = mypandas['where'].map(sub2reg)
        if self.db == 'dgs':
            gd = self.geo.get_data()[['name_region','name_region']]
            mypandas = mypandas.reset_index(drop=True)
            mypandas['where'] = mypandas['where'].apply(lambda x: x.title().replace('Do', 'do').replace('Da','da').replace('De','de'))
            uniqloc = list(mypandas['where'].unique())
            sub2reg = dict(gd.values)
            #sub2reg = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_subregion.isin(uniqloc)]['name_region'])))
            mypandas['where'] = mypandas['where'].map(sub2reg)
            mypandas = mypandas.loc[~mypandas['where'].isnull()]
         # filling subregions.
            gd = self.geo.get_data()[['code_region','name_region']]
            uniqloc = list(mypandas['where'].unique())
            name2code = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_region.isin(uniqloc)]['code_region'])))
            mypandas = mypandas.loc[~mypandas['where'].isnull()]
        codename = None
        location_is_code = False
        uniqloc = list(mypandas['where'].unique()) # if possible location from csv are codelocationv
        if self.db_world:
            uniqloc = [s for s in uniqloc if 'OWID_' not in s]
            db=self.get_db()
            if self.db in ['govcy','europa']:
                db=None
            codename = collections.OrderedDict(zip(uniqloc,self.geo.to_standard(uniqloc,output='list',db=db,interpret_region=True)))
            location_is_code = True
            self.slocation = list(codename.values())
        else:
            if self.database_type[self.db][1] == 'region' :
                temp = self.geo.get_region_list()[['name_region','code_region']]
                codename=dict(temp.values)
                self.slocation = uniqloc
            elif self.database_type[self.db][1] == 'subregion':
                temp = self.geo_all[['code_subregion','name_subregion']]
                codename=dict(temp.loc[temp.code_subregion.isin(uniqloc)].values)
                if self.db == 'jpnmhlw':
                    codename=dict(temp.loc[temp.name_subregion.isin(uniqloc)].values)
                if self.db in ['phe','covidtracking','spf','escovid19data','opencovid19','moh','risklayer','insee']:
                    self.slocation = list(codename.values())
                    location_is_code = True
                else:
                    self.slocation = uniqloc
            else:
                CoaDbError('Granularity problem , neither region nor sub_region ...')
        if self.db == 'dgs':
            mypandas = mypandas.reset_index(drop=True)
        if self.db != 'spfnational':
            mypandas = mypandas.groupby(['where','date']).sum(min_count=1).reset_index() # summing in case of multiple dates (e.g. in opencovid19 data). But keep nan if any
        if self.db == 'govcy' or self.db == 'jpnmhlw':
            location_is_code=False
        mypandas = fill_missing_dates(mypandas)
        if location_is_code:
            if self.db != 'dgs':
                mypandas['codelocation'] =  mypandas['where'].astype(str)
            mypandas['where'] = mypandas['where'].map(codename)
            mypandas = mypandas.loc[~mypandas['where'].isnull()]
        else:
            if self.db == 'jpnmhlw':
                reverse={j:i for i,j in codename.items()}
                mypandas['codelocation'] =  mypandas['where'].map(reverse).astype(str)
            else:
                mypandas['codelocation'] =  mypandas['where'].map(codename).astype(str)

        if self.db == 'owid':
            onlyowid['codelocation'] = onlyowid['where']
            mypandas = pd.concat([mypandas,onlyowid])
        self.mainpandas  = mypandas
        self.dates  = self.mainpandas['date']

   def get_mainpandas(self,**kwargs):
       '''
            * defaut :
                 - location = None
                 - date = None
                 - selected_col = None
                Return the csv file to the mainpandas structure
                index | location              | date      | keywords1       |  keywords2    | ...| keywordsn
                -----------------------------------------------------------------------------------------
                0     |        location1      |    1      |  l1-val1-1      |  l1-val2-1    | ...|  l1-valn-1
                1     |        location1      |    2      |  l1-val1-2      |  l1-val2-2    | ...|  l1-valn-2
                2     |        location1      |    3      |  l1-val1-3      |  l1-val2-3    | ...|  l1-valn-3
                                 ...
                p     |       locationp       |    1      |   lp-val1-1     |  lp-val2-1    | ...| lp-valn-1
                ...
            * location : list of location (None : all location)
            * date : latest date to retrieve (None : max date)
            * selected_col: column to keep according to get_available_keywords (None : all get_available_keywords)
                            N.B. location column is added
        '''
       kwargs_test(kwargs,['where', 'date', 'selected_col'],
                    'Bad args used in the get_stats() function.')

       where = kwargs.get('where', None)
       selected_col = kwargs.get('selected_col', None)
       watch_date = kwargs.get('date', None)
       if where:
            if not isinstance(where, list):
                clist = ([where]).copy()
            else:
                clist = (where).copy()
            if not all(isinstance(c, str) for c in clist):
                raise CoaWhereError("Location via the where keyword should be given as strings. ")
            if self.db_world:
                self.geo.set_standard('name')
                if self.db == 'owid':
                    owid_name = [c for c in clist if c.startswith('owid_')]
                    clist = [c for c in clist if not c.startswith('owid_')]
                clist=self.geo.to_standard(clist,output='list', interpret_region=True)
            else:
                clist=clist+self.geo.get_subregions_from_list_of_region_names(clist)
                if clist in ['FRA','USA','ITA'] :
                    clist=self.geo_all['code_subregion'].to_list()

            clist=list(set(clist)) # to suppress duplicate countries
            diff_locations = list(set(clist) - set(self.get_locations()))
            clist = [i for i in clist if i not in diff_locations]
            filtered_pandas = self.mainpandas.copy()
            if len(clist) == 0 and len(owid_name) == 0:
                raise CoaWhereError('Not a correct location found according to the where option given.')
            if self.db == 'owid':
                clist+=owid_name
            filtered_pandas = filtered_pandas.loc[filtered_pandas['where'].isin(clist)]
            if watch_date:
                check_valid_date(watch_date)
                mydate = pd.to_datetime(watch_date).date()
            else :
                mydate = filtered_pandas.date.max()
            filtered_pandas = filtered_pandas.loc[filtered_pandas.date==mydate].reset_index(drop=True)
            if selected_col:
                l = selected_col
            else:
                l=list(self.get_available_keywords())
            l.insert(0, 'where')
            filtered_pandas = filtered_pandas[l]
            return filtered_pandas
       self.mainpandas = self.mainpandas.reset_index(drop=True)
       return self.mainpandas

   @staticmethod
   def flat_list(matrix):
        ''' Flatten list function used in covid19 methods'''
        flatten_matrix = []
        for sublist in matrix:
            if isinstance(sublist,list):
                for val in sublist:
                    flatten_matrix.append(val)
            else:
                flatten_matrix.append(sublist)
        return flatten_matrix

   def get_dates(self):
        ''' Return all dates available in the current database as datetime format'''
        return self.dates.values

   def get_locations(self):
        ''' Return available location countries / regions in the current database
            Using the geo method standardization
        '''
        return self.slocation

   def return_nonan_dates_pandas(self, df = None, field = None):
         ''' Check if for last date all values are nan, if yes check previous date and loop until false'''
         watchdate = df.date.max()
         boolval = True
         j = 0
         while (boolval):
             boolval = df.loc[df.date == (watchdate - dt.timedelta(days=j))][field].dropna().empty
             j += 1
         df = df.loc[df.date <= watchdate - dt.timedelta(days=j - 1)]
         boolval = True
         j = 0
         watchdate = df.date.min()
         while (boolval):
             boolval = df.loc[df.date == (watchdate + dt.timedelta(days=j))][field].dropna().empty
             j += 1
         df = df.loc[df.date >= watchdate - dt.timedelta(days=j - 1)]
         return df


   def get_stats(self,**kwargs):
        '''
        Return the pandas pandas_datase
         - index: only an incremental value
         - location: list of location used in the database selected (using geo standardization)
         - 'which' :  return the keyword values selected from the avalailable keywords keepted seems
            self.get_available_keywords()

         - 'option' :default none
            * 'nonneg' In some cases negatives values can appeared due to a database updated, nonneg option
                will smooth the curve during all the period considered
            * 'nofillnan' if you do not want that NaN values are filled, which is the default behaviour
            * 'smooth7' moving average, window of 7 days
            * 'sumall' sum data over all locations

        keys are keyswords from the selected database
                location        | date      | keywords          |  daily            |  weekly
                -----------------------------------------------------------------------
                location1       |    1      |  val1-1           |  daily1-1          |  diff1-1
                location1       |    2      |  val1-2           |  daily1-2          |  diff1-2
                location1       |    3      |  val1-3           |  daily1-3          |  diff1-3
                    ...             ...                     ...
                location1       | last-date |  val1-lastdate    |  cumul1-lastdate   |   diff1-lastdate
                    ...
                location-i      |    1      |  vali-1           |  dailyi-1          |  diffi-1
                location-i      |    2      |  vali-1           |  daily1i-2         |  diffi-2
                location-i      |    3      |  vali-1           |  daily1i-3         |  diffi-3
                    ...

        '''
        option = None
        sumall = None
        wallname = None
        optionskipped=False
        othersinputfieldpandas=pd.DataFrame()
        kwargs_test(kwargs,['where','which','what','option','input','input_field','when','output',
        'typeofplot','typeofhist','tile','visu','mode','maplabel','bypop'],'Bad args used in the get_stats() function.')
        if not 'where' in kwargs or kwargs['where'] is None.__class__ or kwargs['where'] == None:
            if get_db_list_dict()[self.db][0] == 'WW':
                kwargs['where'] = get_db_list_dict()[self.db][2]
            else:
                kwargs['where'] = self.slocation #self.geo_all['code_subregion'].to_list()
            wallname = get_db_list_dict()[self.db][2]
        else:
            kwargs['where'] = kwargs['where']
        wallname = None
        option = kwargs.get('option', 'fillnan')
        fillnan = True # default
        sumall = False # default
        sumallandsmooth7 = False
        if 'input' not in kwargs:
            mypycoapd = self.get_mainpandas()
            if 'which' not in kwargs:
                kwargs['which'] = mypycoapd.columns[2]
            #if kwargs['which'] not in self.get_available_keywords():
            #    raise CoaKeyError(kwargs['which']+' is not a available for ' + self.db + ' database name. '
            #    'See get_available_keywords() for the full list.')
            mainpandas = self.return_nonan_dates_pandas(mypycoapd,kwargs['which'])
            #while for last date all values are nan previous date
        else:
            mypycoapd=kwargs['input']
            if str(type(mypycoapd['where'][0]))=="<class 'list'>":
                return mypycoapd
            kwargs['which']=kwargs['input_field']
            mainpandas = self.return_nonan_dates_pandas(mypycoapd,kwargs['input_field'])
            #if isinstance(kwargs['input_field'],list):
            #    for i in kwargs['input_field']:
            #        mainpandas[i] = mypycoapd[i]
        devorigclist = None
        origclistlist = None
        origlistlistloc = None
        if option and 'sumall' in option:
            if not isinstance(kwargs['where'], list):
                kwargs['where'] = [[kwargs['where']]]
            else:
                if isinstance(kwargs['where'][0], list):
                    kwargs['where'] = kwargs['where']
                else:
                    kwargs['where'] = [kwargs['where']]
        if not isinstance(kwargs['where'], list):
            listloc = ([kwargs['where']]).copy()
            if not all(isinstance(c, str) for c in listloc):
                raise CoaWhereError("Location via the where keyword should be given as strings. ")
            origclist = listloc
        else:
            listloc = (kwargs['where']).copy()
            origclist = listloc
            if any(isinstance(c, list) for c in listloc):
                if all(isinstance(c, list) for c in listloc):
                    origlistlistloc = listloc
                else:
                    raise CoaWhereError("In the case of sumall all locations must have the same types i.e\
                    list or string but both is not accepted, could be confusing")

        owid_name=''
        if self.db_world:
            self.geo.set_standard('name')
            if origlistlistloc != None:
                #fulllist = [ i if isinstance(i, list) else [i] for i in origclist ]
                fulllist = []
                for deploy in origlistlistloc:
                    d=[]
                    for i in deploy:
                        if not self.geo.get_GeoRegion().is_region(i):
                            d.append(self.geo.to_standard(i,output='list',interpret_region=True)[0])
                        else:
                            d.append(self.geo.get_GeoRegion().is_region(i))
                    fulllist.append(d)
                dicooriglist = { ','.join(i):self.geo.to_standard(i,output='list',interpret_region=True) for i in fulllist}
                location_exploded = list(dicooriglist.values())
            else:
                owid_name = [c for c in origclist if c.startswith('owid_')]
                clist = [c for c in origclist if not c.startswith('owid_')]
                location_exploded = self.geo.to_standard(listloc,output='list',interpret_region=True)

                if len(owid_name) !=0 :
                    location_exploded += owid_name
        else:
            def explosion(listloc,typeloc='subregion'):
                exploded = []
                a=self.geo.get_data()

                for i in listloc:
                    if typeloc == 'subregion':
                        if self.geo.is_region(i):
                            i = [self.geo.is_region(i)]
                            tmp = self.geo.get_subregions_from_list_of_region_names(i,output='name')
                        elif self.geo.is_subregion(i):
                           tmp = self.geo.is_subregion(i)
                        else:
                            raise CoaTypeError(i + ': not subregion nor region ... what is it ?')

                    elif typeloc == 'region':
                        tmp = self.geo.get_region_list()
                        if i.isdigit():
                            tmp = list(tmp.loc[tmp.code_region==i]['name_region'])
                        elif self.geo.is_region(i):
                            tmp = self.geo.get_regions_from_macroregion(name=i,output='name')
                            if get_db_list_dict()[self.db][0] in ['USA, FRA, ESP, PRT']:
                                tmp = tmp[:-1]
                        else:
                            if self.geo.is_subregion(i):
                                raise CoaTypeError(i+ ' is a subregion ... not compatible with a region DB granularity?')
                            else:
                                raise CoaTypeError(i + ': not subregion nor region ... what is it ?')
                    else:
                        raise CoaTypeError('Not subregion nor region requested, don\'t know what to do ?')
                    if exploded:
                        exploded.append(tmp)
                    else:
                        exploded=[tmp]
                return DataBase.flat_list(exploded)
            if origlistlistloc != None:
                dicooriglist={}
                for i in origlistlistloc:
                    if i[0].upper() in [self.database_type[self.db][0].upper(),self.database_type[self.db][2].upper()]:
                        dicooriglist[self.database_type[self.db][0]]=explosion(DataBase.flat_list(self.slocation))
                    else:
                        dicooriglist[','.join(i)]=explosion(i,self.database_type[self.db][1])

                        #print(list(map(lambda x: x.replace(i, ', '.join(DataBase.flat_list(self.slocation))), origlistlistloc)))
                #dicooriglist={','.join(i):explosion(i,self.database_type[self.db][1]) for i in origlistlistloc}
                #origlistlistloc = DataBase.flat_list(list(dicooriglist.values()))
                #location_exploded = origlistlistloc
            else:
                if any([i.upper() in [self.database_type[self.db][0].upper(),self.database_type[self.db][2].upper()] for i in listloc]):
                    listloc=self.slocation
                listloc = explosion(listloc,self.database_type[self.db][1])
                listloc = DataBase.flat_list(listloc)
                location_exploded = listloc
        def sticky(lname):
            if len(lname)>0:
                tmp=''
                for i in lname:
                    tmp += i+', '
                lname=tmp[:-2]
            return [lname]

        pdcluster = pd.DataFrame()
        j=0
        if origlistlistloc != None:
            for k,v in dicooriglist.items():
                tmp  = mainpandas.copy()
                if any(isinstance(c, list) for c in v):
                    v=v[0]
                tmp = tmp.loc[tmp['where'].isin(v)]
                code = tmp.codelocation.unique()
                tmp['clustername'] = [k]*len(tmp)
                if pdcluster.empty:
                    pdcluster = tmp
                else:
                    pdcluster = pd.concat([pdcluster,tmp])
                j+=1
            pdfiltered = pdcluster[['where','date','codelocation',kwargs['which'],'clustername']]
        else:
            pdfiltered = mainpandas.loc[mainpandas['where'].isin(location_exploded)]
            if 'input_field' in kwargs or isinstance(kwargs['which'],list):
                if 'which' in kwargs:
                    kwargs['input_field']=kwargs['which']
                if isinstance(kwargs['input_field'],list):
                    pdfilteredoriginal = pdfiltered.copy()
                    pdfiltered = pdfiltered[['where','date','codelocation',kwargs['input_field'][0]]]
                    othersinputfieldpandas = pdfilteredoriginal[['where','date']+kwargs['input_field'][1:]]
                    kwargs['which'] = kwargs['input_field'][0]
                else:
                    pdfiltered = pdfiltered[['where','date','codelocation', kwargs['input_field']]]
                    kwargs['which'] = kwargs['input_field']
            else:
                pdfiltered = pdfiltered[['where','date','codelocation', kwargs['which']]]
            pdfiltered['clustername'] = pdfiltered['where'].copy()
        if not isinstance(option,list):
            option=[option]
        if 'fillnan' not in option and 'nofillnan' not in option:
            option.insert(0, 'fillnan')
        if 'nonneg' in option:
            option.remove('nonneg')
            option.insert(0, 'nonneg')
        if 'smooth7' in  option and 'sumall' in  option:
            option.remove('sumall')
            option.remove('smooth7')
            option+=['sumallandsmooth7']
        for o in option:
            if o == 'nonneg':
                if kwargs['which'].startswith('cur_'):
                    raise CoaKeyError('The option nonneg cannot be used with instantaneous data, such as cur_ which variables.')
                cluster=list(pdfiltered.clustername.unique())
                separated = [ pdfiltered.loc[pdfiltered.clustername==i] for i in cluster]
                reconstructed = pd.DataFrame()
                for sub in separated:
                    where = list(sub['where'].unique())
                    for loca in where:
                        pdloc = sub.loc[sub['where'] == loca][kwargs['which']]
                        try:
                            y0=pdloc.values[0] # integrated offset at t=0
                        except:
                            y0=0
                        if np.isnan(y0):
                            y0=0
                        pa = pdloc.diff()
                        yy = pa.values
                        ind = list(pa.index)
                        where_nan = np.isnan(yy)
                        yy[where_nan] = 0.
                        indices=np.where(yy < 0)[0]
                        for kk in np.where(yy < 0)[0]:
                            k = int(kk)
                            val_to_repart = -yy[k]
                            if k < np.size(yy)-1:
                                yy[k] = (yy[k+1]+yy[k-1])/2
                            else:
                                yy[k] = yy[k-1]
                            val_to_repart = val_to_repart + yy[k]
                            s = np.nansum(yy[0:k])
                            if not any([i !=0 for i in yy[0:k]]) == True and s == 0:
                                yy[0:k] = 0.
                            elif s == 0:
                                yy[0:k] = np.nan*np.ones(k)
                            else:
                                yy[0:k] = yy[0:k]*(1-float(val_to_repart)/s)
                        sub=sub.copy()
                        sub.loc[ind,kwargs['which']]=np.cumsum(yy)+y0 # do not forget the offset
                    if reconstructed.empty:
                        reconstructed = sub
                    else:
                        reconstructed=pd.concat([reconstructed,sub])
                    pdfiltered = reconstructed
            elif o == 'nofillnan':
                pdfiltered_nofillnan = pdfiltered.copy().reset_index(drop=True)
                fillnan=False
            elif o == 'fillnan':
                fillnan=True
                # fill with previous value
                pdfiltered = pdfiltered.reset_index(drop=True)
                pdfiltered_nofillnan = pdfiltered.copy()

                pdfiltered.loc[:,kwargs['which']] =\
                pdfiltered.groupby(['where','clustername'])[kwargs['which']].apply(lambda x: x.bfill())
                #if kwargs['which'].startswith('total_') or kwargs['which'].startswith('tot_'):
                #    pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].apply(lambda x: x.ffill())
                if pdfiltered.loc[pdfiltered.date == pdfiltered.date.max()][kwargs['which']].isnull().values.any():
                    print(kwargs['which'], "has been selected. Some missing data has been interpolated from previous data.")
                    print("This warning appear right now due to some missing values at the latest date ", pdfiltered.date.max(),".")
                    print("Use the option='nofillnan' if you want to only display the original data")
                    pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['where','clustername'])[kwargs['which']].apply(lambda x: x.ffill())
                    pdfiltered = pdfiltered[pdfiltered[kwargs['which']].notna()]
            elif o == 'smooth7':
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['where'])[kwargs['which']].rolling(7,min_periods=7).mean().reset_index(level=0,drop=True)
                inx7=pdfiltered.groupby('where').head(7).index
                pdfiltered.loc[inx7, kwargs['which']] = pdfiltered[kwargs['which']].fillna(method="bfill")
                fillnan=True
            elif o == 'sumall':
                sumall = True
            elif o == 'sumallandsmooth7':
                sumall = True
                sumallandsmooth7 = True
            elif o != None and o != '' and o != 'sumallandsmooth7':
                raise CoaKeyError('The option '+o+' is not recognized in get_stats. See listoptions() for list.')
        pdfiltered = pdfiltered.reset_index(drop=True)

        # if sumall set, return only integrate val
        tmppandas=pd.DataFrame()
        if sumall:
            if origlistlistloc != None:
               uniqcluster = pdfiltered.clustername.unique()
               if kwargs['which'].startswith('cur_idx_') or kwargs['which'].startswith('cur_tx_'):
                  tmp = pdfiltered.groupby(['clustername','date']).mean().reset_index()
               else:
                  tmp = pdfiltered.groupby(['clustername','date']).sum().reset_index()#.loc[pdfiltered.clustername.isin(uniqcluster)].\

               codescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['codelocation'].unique()) for i in uniqcluster}
               namescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['where'].unique()) for i in uniqcluster}
               tmp['codelocation'] = tmp['clustername'].map(codescluster)
               tmp['where'] = tmp['clustername'].map(namescluster)

               pdfiltered = tmp
               pdfiltered = pdfiltered.drop_duplicates(['date','clustername'])
               if sumallandsmooth7:
                   pdfiltered[kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].rolling(7,min_periods=7).mean().reset_index(level=0,drop=True)
                   pdfiltered.loc[:,kwargs['which']] =\
                   pdfiltered.groupby(['clustername'])[kwargs['which']].apply(lambda x: x.bfill())
            # computing daily, cumul and weekly
            else:
                if kwargs['which'].startswith('cur_idx_'):
                    tmp = pdfiltered.groupby(['date']).mean().reset_index()
                else:
                    tmp = pdfiltered.groupby(['date']).sum().reset_index()
                uniqloc = list(pdfiltered['where'].unique())
                uniqcodeloc = list(pdfiltered.codelocation.unique())
                tmp.loc[:,'where'] = ['dummy']*len(tmp)
                tmp.loc[:,'codelocation'] = ['dummy']*len(tmp)
                tmp.loc[:,'clustername'] = ['dummy']*len(tmp)
                for i in range(len(tmp)):
                    tmp.at[i,'where'] = uniqloc #sticky(uniqloc)
                    tmp.at[i,'codelocation'] = uniqcodeloc #sticky(uniqcodeloc)
                    tmp.at[i,'clustername'] =  sticky(uniqloc)[0]
                pdfiltered = tmp
        else:
            if self.db_world :
                pdfiltered['clustername'] = pdfiltered['where'].apply(lambda x: self.geo.to_standard(x)[0] if not x.startswith("owid_") else x)
            else:
                pdfiltered['clustername'] = pdfiltered['where']
        if 'cur_' in kwargs['which'] or 'total_' in kwargs['which'] or 'tot_' in kwargs['which']:
            pdfiltered['cumul'] = pdfiltered[kwargs['which']]
        else:
            pdfiltered['cumul'] = pdfiltered_nofillnan.groupby('clustername')[kwargs['which']].cumsum()
            if fillnan:
                pdfiltered.loc[:,'cumul'] =\
                pdfiltered.groupby('clustername')['cumul'].apply(lambda x: x.ffill())
        pdfiltered['daily'] = pdfiltered.groupby('clustername')['cumul'].diff()
        pdfiltered['weekly'] = pdfiltered.groupby('clustername')['cumul'].diff(7)
        inx = pdfiltered.groupby('clustername').head(1).index
        inx7=pdfiltered.groupby('clustername').head(7).index
        #First value of diff is always NaN
        pdfiltered.loc[inx, 'daily'] = pdfiltered['daily'].fillna(method="bfill")
        pdfiltered.loc[inx7, 'weekly'] = pdfiltered['weekly'].fillna(method="bfill")
        if self.db == 'spf' and kwargs['which'] in ['tot_P','tot_T']:
            pdfiltered['daily'] = pdfiltered.groupby(['clustername'])[kwargs['which']].rolling(7,min_periods=7).mean()\
                                  .reset_index(level=0,drop=True).diff()
            inx=pdfiltered.groupby('clustername').head(7).index
            pdfiltered.loc[inx, 'daily'] = pdfiltered['daily'].fillna(method="bfill")
        unifiedposition=['where', 'date', kwargs['which'], 'daily', 'cumul', 'weekly', 'codelocation','clustername']
        if kwargs['which'] in ['standard','daily','weekly','cumul']:
            unifiedposition.remove(kwargs['which'])
        pdfiltered = pdfiltered[unifiedposition]
        if wallname != None and sumall == True:
               pdfiltered.loc[:,'clustername'] = wallname

        pdfiltered = pdfiltered.drop(columns='cumul')
        if not othersinputfieldpandas.empty:
            pdfiltered = pd.merge(pdfiltered, othersinputfieldpandas, on=['date','where'])
        if 'input_field' not in kwargs:
            verb("Here the information I\'ve got on ", kwargs['which']," : ",  self.dbfullinfo.get_keyword_definition(kwargs['which']))
        return pdfiltered

   def merger(self,**kwargs):
        '''
        Merge two or more pycoa pandas from get_stats operation
        'coapandas': list (min 2D) of pandas from stats
        '''

        coapandas = kwargs.get('coapandas', None)

        if coapandas is None or not isinstance(coapandas, list) or len(coapandas)<=1:
            raise CoaKeyError('coapandas value must be at least a list of 2 elements ... ')

        def renamecol(pandy):
            torename=['daily','cumul','weekly']
            return pandy.rename(columns={i:pandy.columns[2]+'_'+i  for i in torename})
        base = coapandas[0].copy()
        coapandas = [ renamecol(p) for p in coapandas ]
        base = coapandas[0].copy()
        if not 'clustername' in base.columns:
            raise CoaKeyError('No "clustername" in your pandas columns ... don\'t know what to do ')

        j=1
        for p in coapandas[1:]:
            [ p.drop([i],axis=1, inplace=True) for i in ['where','where','codelocation'] if i in p.columns ]
            #p.drop(['where','codelocation'],axis=1, inplace=True)
            base = pd.merge(base,p,on=['date','clustername'],how="inner")#,suffixes=('', '_drop'))
            #base.drop([col for col in base.columns if 'drop' in col], axis=1, inplace=True)
        return base

   def appender(self,**kwargs):
      '''
      Append two or more pycoa pandas from get_stats operation
      'coapandas': list (min 2D) of pandas from stats
      '''

      coapandas = kwargs.get('coapandas', None)
      if coapandas is None or not isinstance(coapandas, list) or len(coapandas)<=1:
          raise CoaKeyError('coapandas value must be at least a list of 2 elements ... ')

      coapandas = [ p.rename(columns={p.columns[2]:'cases'}) for p in coapandas ]
      m = pd.concat(coapandas).reset_index(drop=True)
      #m['clustername']=m.m('where')['clustername'].fillna(method='bfill')
      #m['codelocation']=m.groupby('where')['codelocation'].fillna(method='bfill')
      m=m.drop(columns=['codelocation','clustername'])
      return fill_missing_dates(m)

   def saveoutput(self,**kwargs):
       '''
       saveoutput pycoas pandas as an  output file selected by output argument
       'pandas': pycoa pandas
       'saveformat': excel or csv (default excel)
       'savename': pycoaout (default)
       '''
       possibleformat=['excel','csv']
       saveformat = 'excel'
       savename = 'pycoaout'
       pandyori = ''
       if 'saveformat' in kwargs:
            saveformat = kwargs['saveformat']
       if saveformat not in possibleformat:
           raise CoaKeyError('Output option '+saveformat+' is not recognized.')
       if 'savename' in kwargs and kwargs['savename'] != '':
          savename = kwargs['savename']

       if not 'pandas' in kwargs:
          raise CoaKeyError('Absolute needed variable : the pandas desired ')
       else:
          pandyori = kwargs['pandas']
       pandy = pandyori
       pandy['date'] = pd.to_datetime(pandy['date'])
       pandy['date']=pandy['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
       if saveformat == 'excel':
           pandy.to_excel(savename+'.xlsx',index=False, na_rep='NAN')
       elif saveformat == 'csv':
           pandy.to_csv(savename+'.csv', encoding='utf-8', index=False, float_format='%.4f',na_rep='NAN')

   ## https://www.kaggle.com/freealf/estimation-of-rt-from-cases
   def smooth_cases(self,cases):
        new_cases = cases

        smoothed = new_cases.rolling(7,
            win_type='gaussian',
            min_periods=1,
            center=True).mean(std=2).round()
            #center=False).mean(std=2).round()

        zeros = smoothed.index[smoothed.eq(0)]
        if len(zeros) == 0:
            idx_start = 0
        else:
            last_zero = zeros.max()
            idx_start = smoothed.index.get_loc(last_zero) + 1
        smoothed = smoothed.iloc[idx_start:]
        original = new_cases.loc[smoothed.index]

        return smoothed
   def get_posteriors(self,sr, window=7, min_periods=1):
        # We create an array for every possible value of Rt
        R_T_MAX = 12
        r_t_range = np.linspace(0, R_T_MAX, R_T_MAX*100+1)

        # Gamma is 1/serial interval
        # https://wwwnc.cdc.gov/eid/article/26/6/20-0357_article
        GAMMA = 1/7

        lam = sr[:-1].values * np.exp(GAMMA * (r_t_range[:, None] - 1))

        # Note: if you want to have a Uniform prior you can use the following line instead.
        # I chose the gamma distribution because of our prior knowledge of the likely value
        # of R_t.

        # prior0 = np.full(len(r_t_range), np.log(1/len(r_t_range)))
        prior0 = np.log(sps.gamma(a=3).pdf(r_t_range) + 1e-14)

        likelihoods = pd.DataFrame(
            # Short-hand way of concatenating the prior and likelihoods
            data = np.c_[prior0, sps.poisson.logpmf(sr[1:].values, lam)],
            index = r_t_range,
            columns = sr.index)

        # Perform a rolling sum of log likelihoods. This is the equivalent
        # of multiplying the original distributions. Exponentiate to move
        # out of log.
        posteriors = likelihoods.rolling(window,
                                     axis=1,
                                     min_periods=min_periods).sum()
        posteriors = np.exp(posteriors)

        # Normalize to 1.0
        posteriors = posteriors.div(posteriors.sum(axis=0), axis=1)

        return posteriors
