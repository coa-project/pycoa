# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file
Module : coa.dbparser
Aboutself.granu_country
-----
This is the PyCoA rapport module it gives all available information concerning a database key words
"""
import pandas as pd
from functools import reduce
from bs4 import BeautifulSoup
import os.path
from os import listdir
from os.path import isfile, join
import json
import datetime
import collections
import random
import numpy as np
from tqdm import tqdm
from coa.error import *
from coa.tools import (
    info,
    verb,
    kwargs_test,
    exists_from_url,
    get_local_from_url,
    week_to_date,
    fill_missing_dates,
    flat_list
)
import coa.geo as coge
import sys
import pycountry

class MetaInfo:
  def __init__(self):
        '''
        For a specific database (call namedb), returns information on the epidemiological variables.
        Those informations are used later on in covid19.py.
        It returns a dictionnary with:
            * key: epidemiological variable
            * values:
                - new variable name for pycoa purpose, if needed. By default is an empty string ''
                - desciption of the variable. By default is an empty string '' but it is highly recommended to describe the variable
                - url of the csv where the epidemiological variable is
                - url of the master i.e where some general description could be located. By default is an empty string ''
        '''
        self.dropdb = []
        self.pdjson = MetaInfo.getallmetadata()

  @staticmethod
  def parsejson(file):
    '''
        Parse the description of the database selected, in json data format.
        The json file description like this:

        "header": "Some Header",
        "geoinfo": {
                    "granularity": "country / region / subregion ",
                    "where": "World / Europe /country name / ..."
                    },
        "columns / rows ": [ -> columns / rows : you want to keep from your database
                {
                        "name":"XXX", -> name of the variable in Pycoa
                        "alias":"XXX", -> original name in the db selected
                        "description":"Some description of the variable",
                        "url": "https://XXX", -> location of the db
                        "urlmaster":"https://XXX" -> eventually a master url
                },
                ...
                ]
        }
    '''
    filename = os.path.basename(file)
    check_file = os.path.isfile(file)

    if check_file:
        sig, msg = 1, ''
        try:
            with open(file, 'r') as file:
                data = json.load(file)
                sig, msg = MetaInfo.checkmetadatastructure(data)
                if sig == 0:
                    data = 'Database json description incompatible: '+ msg
        except ValueError as e:
            sig = 0
            data = 'Invalid json file ' + filename +': %s' % e
    else:
        sig = 0
        data = 'This file :' + filename +  ' do not exist'
    return {sig:data}

  @staticmethod
  def getallmetadata():
      '''
      List all the valide json file in the json folder
      return a dictionnary with db name as a key and the parsing json file as dictionnary or
      the error if the file do not exist or not valide
      '''
      pathmetadb = '../json/'
      onlyfiles = [f for f in listdir(pathmetadb) if isfile(join(pathmetadb, f)) and f.endswith('.json')]
      jsongeoinfo = {}
      col = ['name','validejson','parsingjson']
      df = pd.DataFrame(columns = col)
      valide = ''
      for i in onlyfiles:
         name = i.replace('.json','')
         metadata = MetaInfo.parsejson(pathmetadb+i)
         try:
             meta = metadata[1]
             valide = "GOOD"
         except:
             meta = metadata[0]
             valide = "BAD"
         tmp=pd.DataFrame([[name,valide,meta]],columns=col)
         df = pd.concat([df,tmp],ignore_index=True)
      return df

  def getcurrentmetadata(self,namedb):
      '''
        Return current meta information from the json file i.e from "namedb".json
      '''
      line = self.pdjson.loc[self.pdjson.name == namedb]
      if line.validejson.values == 'GOOD':
          try:
              return line.parsingjson.values[0]
          except:
              raise CoaError('Database json description incompatible, please check')
      else:
        error =  " Database json parsing error:\n" + line.parsingjson.values[0]
        raise CoaError(error)

  def getcurrentmetadatawhich(self,dico):
      '''
        from the dictionnary parsed in the json retrieve the "which" values
        which are defined by name key word in the json fill
      '''
      which=[]
      for i in dico['datasets']:
        for j in i['columns']:
            if j['name']:
                which.append(j['name'])
      if 'date' in which:
            which.remove('date')
      if 'where' in which:
            which.remove('where')
      return which

  @staticmethod
  def checkmetadatastructure(metastructure):
      '''
      Some meta data information are mandatory in the JSON file
      check if all are present in the files
      Return 2D list : sig (1 Ok, 0 not good) & message
      '''

      def test(dico,lm):
          sig = 1
          msg = 'pycoa json meta structure is validated'
          for i in lm:
              try:
                 dico[i]
              except:
                 sig = 0
                 msg = 'Missing in your json file : '+i
          return [sig,msg]

      jsonkeys0 = ['geoinfo','datasets']
      sig, msg = test(metastructure,jsonkeys0)
      if sig == 1:
          geoinfokeys = ['where','isocode','granularity','locationmode']
          sig, msg = test(metastructure['geoinfo'],geoinfokeys)
          if sig == 1:
              datasetskeys = ['urldata','columns']
              for i in metastructure['datasets']:
                  sig, msg = test(i,datasetskeys)
                  if sig == 1:
                      columnskeys = ['name']
                      for i in metastructure['datasets']:
                          for j in i['columns']:
                              sig,msg = test(j,columnskeys)
      return [sig,msg]

class DataParser:
  def __init__(self, namedb):
        self.db = namedb
        self.granu_country = False
        self.metadata = MetaInfo().getcurrentmetadata(namedb)
        granularity = self.metadata['geoinfo']['granularity']
        try:
            if granularity == 'country': # world wide dba
                self.granu_country = True
                self.geo = coge.GeoManager('name')
                self.geo_all = 'world'
            else: # local db
                self.geo = coge.GeoCountry('FRA')
                if granularity == 'region':
                    self.geo_all = self.geo.get_region_list()
                    granularityinfo = ['name_region','code_region']
                elif granularity == 'subregion':
                    self.geo_all = self.geo.get_subregion_list()
                    granularityinfo = ['name_subregion','code_subregion']
                else:
                    CoaError('Granularity problem: neither country, region or subregion')
            # specific reading of data according to the db
            self.mainpandas = self.get_parsing()

        except:
            raise CoaDbError("An error occured while parsing data of "+self.db+". This may be due to a data format modification. "
                "You may contact support@pycoa.fr. Thanks.")
        #self.addGeoDescription(self.mainpandas)
            # some info
            #self.get_echoinfo()
            #print(self.geo_all)

  def get_echoinfo(self):
      info('Few information concernant the selected database : ', self.db)
      info('Available key-words, which ∈', sorted(self.get_available_keywords()))
      info('Example of where : ',  ', '.join(random.choices(self.get_locations(), k=min(5,len(self.get_locations() ))   )), ' ...')
      info('Last date data ', pd.to_datetime(max(self.get_dates())).strftime("%m/%d/%Y"))

  def get_parsing(self,):
      '''
        Parse the json file load in the init fonction (self.metadata)
        it returns a pandas with this structure
        |date|where|isocode| var-1 ... var-n
        var-i are the variable selected in the json file
        To assure a good standardization "where" et "isocode" use geo metho
      '''
      if 'header' in list(self.metadata.keys()):
          self.dbdescription = self.metadata['header']
      else:
          self.dbdescription = 'No descrition for DB = ' + self.db
      pandas_db = pd.DataFrame()
      locationmode = self.metadata['geoinfo']['locationmode']
      granularity = self.metadata['geoinfo']['granularity']
      place = self.metadata['geoinfo']['where']

      if 'replace' in list(self.metadata.keys()):
          replace_field = self.metadata['replace']

      self.url = []
      self.keyword_definition = {}
      self.keyword_url = {}
      for datasets in self.metadata['datasets']:
          url = datasets['urldata']
          pdata = pd.DataFrame(datasets['columns'])
          pdata['description'] = pdata['description'].fillna('No description')
          pdata.alias.fillna(pdata.name, inplace=True)
          if 'description' not in list(pdata.columns):
              pdata['description'] = 'No description'
          usecols = pdata.alias.to_list()
          selections = None
          if 'selections' in list(datasets.keys()):
              selections = datasets['selections']
              usecols += list(selections.keys())
          separator = ';'
          if 'separator' in list(datasets.keys()):
              separator = datasets['separator']
          drop = None
          if 'drop' in list(datasets.keys()):
              drop = datasets['drop']
          cast = None
          if 'cast' in list(datasets.keys()):
               cast = datasets['cast']
          decimal='.'
          if 'decimal' in list(datasets.keys()):
             decimal=datasets['decimal']
          rename_columns = None
          if 'alias' in list(pdata.columns) and 'name' in list(pdata.columns):
            rename_columns = pdata.set_index('alias')['name'].to_dict()

          kd = pdata.loc[~pdata.name.isin(['where','date'])].set_index('name')['description'].to_dict()
          for k,v in kd.items():
              self.keyword_definition[k]=v
              self.keyword_url[k]=url
          try:
              pandas_temp = pd.read_csv(get_local_from_url(url,10000), sep = separator, usecols = usecols,
                keep_default_na = False, na_values = '' , header=0, dtype = cast, decimal = decimal, low_memory = False)
          except:
              raise CoaError('Something went wrong during the parsing')
          if drop:
              for key,val in drop.items():
                  if key in pandas_temp.columns:
                      pandas_temp = pandas_temp[~pandas_temp[key].str.startswith(val)]
                      #pandas_temp = pandas_temp.loc[~pandas_temp[key].isin([val])]
          if selections:
              for key,val in selections.items():
                  if key in pandas_temp.columns:
                      pandas_temp = pandas_temp.loc[pandas_temp[key] == val]
                      pandas_temp = pandas_temp.drop(columns=key)
                  else:
                      raise CoaError("This is weird " + key + " selection went wrong ! ")
          if replace_field:
             pandas_temp = pandas_temp.replace(replace_field)

          pandas_temp = pandas_temp.rename(columns = rename_columns)
          if 'semaine' in usecols:
             pandas_temp['date'] = [ week_to_date(i) for i in pandas_temp['date']]
          if self.db == "govcy":
             pandas_temp['date'] = pd.to_datetime(pandas_temp['date'], errors='coerce', format="%d/%m/%Y").dt.date
             pandas_temp = pandas_temp.replace(':',np.nan)
          elif self.db == "olympics":
             pandas_temp['date'] = pd.to_datetime(pandas_temp['date'], format='%Y', errors='coerce').dt.date
          else:
             pandas_temp['date'] = pd.to_datetime(pandas_temp['date'], errors='coerce', infer_datetime_format=True).dt.date

          if granularity == 'country' and 'where' not in list(pdata.name):
              pandas_temp['where'] = place

          if pandas_db.empty:
              pandas_db = pandas_temp
          else:
              pandas_db = pandas_db.merge(pandas_temp, how = 'outer', on=['where','date'])
          self.url += [url]

      whereanddate =  ['date','where']
      notwhereanddate =  [ i  for i in list(pandas_db.columns) if i not in whereanddate ]
      self.available_keywords = notwhereanddate

      pandas_db[notwhereanddate] = pandas_db[notwhereanddate].fillna(method = 'bfill').fillna(method = 'ffill')
      pandas_db[notwhereanddate] = pandas_db[notwhereanddate].astype(float)
      pandas_db = pandas_db[whereanddate+notwhereanddate]
      pandas_db = pandas_db.groupby(whereanddate).sum(min_count=1).reset_index()
      pandas_db['date'] = pd.to_datetime(pandas_db['date'], errors='coerce', infer_datetime_format=True)
      pandas_db = fill_missing_dates(pandas_db)
      pandas_db = pandas_db.sort_values(['where','date'])

      self.available_keywords = list(pandas_db.columns)
      if 'date' in self.available_keywords:
          self.available_keywords.remove('date')
      if 'where' in self.available_keywords:
         self.available_keywords.remove('where')

      #return pandas_db
      locationdb = list(pandas_db['where'].unique())
      granularity = self.metadata['geoinfo']['granularity']
      namecodedico = {}
      if self.granu_country:
          if locationmode == "isocode":
            g = coge.GeoManager('name')
          else:
            g = coge.GeoManager('iso3')
          namecode  = g.to_standard(locationdb,output='dict',db = self.db)
          namecodedico = {k.upper():v.capitalize() for k,v in namecode.items()}
      else:
          if granularity == 'subregion':
              geopd = self.geo.get_subregion_list()
              geocodename = geopd.loc[geopd.code_subregion.isin(locationdb)]
              namecodedico = geocodename.set_index('name_subregion')['code_subregion'].to_dict()
              db='toto'
              if db == 'jhu-usa':
                  pass
              elif db == 'rki':
                  pass
              else:
                  pass
          elif granularity == 'region':
                  namecodedico = self.geo.get_data().set_index('name_region')['code_region'].to_dict()
          else:
              raise CoaTypeError('Not a region nors ubregion ... sorry but what is it ?')

      if locationmode == "isocode":
          pandas_db = pandas_db.rename(columns={"where": "isocode"})
          pandas_db['isocode'] = pandas_db['isocode'].str.upper()
          pandas_db['where'] = pandas_db['isocode'].map(namecodedico)
      elif locationmode == "name":
          pandas_db['where'] = pandas_db['where'].str.capitalize()
          pandas_db['isocode'] = pandas_db['where'].map(namecodedico)
      else:
          CoaError("what locationmode in your json file is supposed to be ?")

      self.slocation = list(pandas_db['where'].unique())
      self.dates = list(pandas_db['date'].unique())
      return pandas_db

  def get_db(self,):
     '''
        Return the current covid19 database selected. See get_available_database() for full list
     '''
     return self.db

  def get_geo(self,):
      return self.geo

  def get_world_boolean(self,):
    return self.granu_country

  def get_locations(self,):
      ''' Return available location countries / regions / subregions in the current database
          Using the geo method standardization
      '''
      return self.slocation

  def get_dates(self,):
      ''' Return all dates available in the current database as datetime format'''
      return self.dates

  def get_available_keywords(self):
      '''
           Return all the available keyswords for the database selected
      '''
      return self.available_keywords

  def get_url(self):
      '''
       Return all the url which have been parsed for the database selected
      '''
      return self.url

  def get_keyword_definition(self,which):
      '''
           Return available keywords (originally named original keywords) definition
      '''
      if which and which in self.get_available_keywords():
          return self.keyword_definition[which]
      else:
          raise CoaError("Missing which or which not in ",self.get_available_keywords())

  def get_keyword_url(self,which):
      if which and which in self.get_available_keywords():
          return self.keyword_url[which]
      else:
          raise CoaError("Missing which or which not in ",self.get_available_keywords())

  def get_dbdescription(self):
      '''
           Return available information concerning the db selected
      '''
      return self.dbdescription

  def get_mainpandas(self,):
      return self.mainpandas
