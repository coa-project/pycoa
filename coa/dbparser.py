# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - november 2023
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file
Module : report
Aboutself.db_world
-----
This is the PyCoA rapport module it gives all available information concerning a database key words
"""
import pandas as pd
from functools import reduce
from bs4 import BeautifulSoup
import json
import datetime
import collections
import random

from coa.error import *
from coa.tools import (
    info,
    verb,
    kwargs_test,
    get_local_from_url,
    week_to_date,
    fill_missing_dates,
    flat_list
)
import coa.geo as coge
import sys
import pycountry
# Known db

_db_list_dict = {
    'owid': ['WW','nation','World'],
    'dgs':['PRT','region','Portugal'],
    'dpc': ['ITA','region','Italy'],
    'europa':['WW','nation','Europe'],
    'escovid19data':['ESP','subregion','Spain'],
    'govcy':['CYP','nation','Cyprus'],
    'imed':['GRC','region','Greece'],
    'insee':['FRA','subregion','France'],
    'jhu': ['WW','nation','World'],
    'jhu-usa': ['USA','subregion','United States of America'],
    'jpnmhlw' :['JPN','subregion','Japan'],
    'moh':['MYS','subregion','Malaysia'],
    'mpoxgh':['WW','nation','World'],
    'phe':['GBR','subregion','United Kingdom'],
    'risklayer':['EUR','subregion','Europe'],
    'rki':['DEU','subregion','Germany'],
    'sciensano':['BEL','region','Belgium'],
    'spf': ['FRA','subregion','France'],
    'spfnational': ['WW','nation','France'],
    'olympics': ['WW','nation','World'],
    }
class DBInfo:
  def __init__(self, namedb):
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
        self.separator = {}
        self.db = namedb
        self.db_world = False
        alldb  = list(_db_list_dict.keys())
        if self.db not in alldb:
            raise CoaDbError('Unknown ' + namedb + '. Available database so far in PyCoa are : ' + str(alldb), file=sys.stderr)
        else:
            try:
                if self.get_dblistdico(namedb)[1] == 'nation': # world wide dba
                    self.db_world = True
                    self.geo = coge.GeoManager('name')
                    self.geo_all = 'world'
                else: # local db
                    self.db_world = False
                    self.geo = coge.GeoCountry(self.get_dblistdico(namedb)[0])
                    if self.get_dblistdico(namedb)[1] == 'region':
                        self.geo_all = self.geo.get_region_list()
                    elif self.get_dblistdico(namedb)[1] == 'subregion':
                        self.geo_all = self.geo.get_subregion_list()
                    else:
                        CoaError('Granularity problem, neither region or subregion')
                # specific reading of data according to the db
                self.get_parsing(namedb)
            except:
                raise CoaDbError("An error occured while parsing data of "+self.get_db()+". This may be due to a data format modification. "
                    "You may contact support@pycoa.fr. Thanks.")
            # some info
            self.get_echoinfo()

  def get_echoinfo(self):
      info('Few information concernant the selected database : ', self.get_db())
      info('Available key-words, which ∈', sorted(self.get_available_keywords()))
      info('Example of where : ',  ', '.join(random.choices(self.get_locations(), k=min(5,len(self.get_locations() ))   )), ' ...')
      info('Last date data ', self.get_dates().max())

  def get_parsing(self,namedb):
      '''
        Parse the DB selected
        When available total deaths should be the first epidemiological variable
      '''
      if namedb in _db_list_dict.keys():
          if namedb == 'owid':
              info('OWID aka \"Our World in Data\" database selected ...')
              owid={
              'total_deaths':['total_deaths','Total deaths attributed to COVID-19'],
              'total_cases':['total_cases','Total confirmed cases of COVID-19'],
              'total_tests':['total_tests','Total tests for COVID-19'],
              'total_tests_per_thousand':['total_tests_per_thousand','Total tests for COVID-19 per thousand'],
              'total_vaccinations':['total_vaccinations','Total number of COVID-19 vaccination doses administered'],
              'total_population':['population','total population of a given country'],
              'total_people_fully_vaccinated_per_hundred':['people_fully_vaccinated_per_hundred','Total number of people who received all doses prescribed by the vaccination protocol per 100 people in the total population'],
              'total_boosters':['total_boosters','Total number of COVID-19 vaccination booster doses administered (doses administered beyond the number prescribed by the vaccination protocol)'],
              'total_people_vaccinated':['people_vaccinated','Total number of people who received at least one vaccine dose'],
              'total_people_fully_vaccinated':['people_fully_vaccinated','total_people_fully_vaccinated (original name people_fully_vaccinated): Total number of people who received all doses prescribed by the vaccination protocol'],
              'total_people_vaccinated_per_hundred':['people_vaccinated_per_hundred','total_people_vaccinated_per_hundred (original name people_vaccinated_per_hundred): total_people_vaccinated_per_hundred:Total number of people who received all doses prescribed by the vaccination protocol per 100 people in the total population'],
              'total_cases_per_million':['total_cases_per_million','Total confirmed cases of COVID-19 per 1,000,000 people'],
              'total_deaths_per_million':['total_deaths_per_million','Total deaths attributed to COVID-19 per 1,000,000 people'],
              'total_vaccinations_per_hundred':['total_vaccinations_per_hundred','COVID19 vaccine doses administered per 100 people'],
              'cur_reproduction_rate':['reproduction_rate','cur_reproduction_rate (original name reproduction_rate): Real-time estimate of the effective reproduction rate (R) of COVID-19. See https://github.com/crondonm/TrackingR/tree/main/Estimates-Database'],
              'cur_icu_patients':['icu_patients','cur_icu_patients (orignal name icu_patients): Number of COVID-19 patients in intensive care units (ICUs) on a given day'],
              'cur_hosp_patients':['hosp_patients','cur_hosp_patients (original name hosp_patients): Number of COVID-19 patients in hospital on a given day'],
              'cur_weekly_hosp_admissions':['weekly_hosp_admissions','cur_weekly_hosp_admissions (original name weekly_hosp_admissions): Number of COVID-19 patients in hospital on a given week'],
              'cur_idx_positive_rate':['positive_rate','cur_idx_positive_rate (original name positive_rate): The share of COVID-19 tests that are positive, given as a rolling 7-day average (this is the inverse of tests_per_case)'],
              'total_gdp_per_capita':['gdp_per_capita','Gross domestic product at purchasing power parity (constant 2011 international dollars), most recent year available'],
              'cur_excess_mortality':['excess_mortality','original name excess_mortality. Percentage difference between the reported number of weekly or monthly deaths in 2020–2021 and the projected number of deaths for the same period based on previous years'],
              'cur_excess_mortality_cumulative_per_million':['excess_mortality_cumulative_per_million','cur_excess_mortality_cumulative_per_million:original name excess_mortality_cumulative_per_million.Cumulative difference between the reported number of deaths since 1 January 2020 and the projected number of deaths for the same period based on previous years, per million people. '],
              }
              url='https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
              self.separator = {url:','}
              masterurl='https://github.com/owid'
              for k,v in owid.items():
                  owid[k].append(url)
                  owid[k].append(masterurl)
              mydico = owid
              self.pandasdb = pd.DataFrame(owid,index=['Original name','Description','URL','Homepage'])
              lurl=list(dict.fromkeys(self.get_url()))
              url=lurl[0]
              rename = {'location':'where'}
              rename.update(self.original_to_available_keywords_dico())
              separator=self.get_url_separator(url)
              keep = ['date','where','iso_code'] + self.get_url_original_keywords()[url]
              owid = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
              self.dbparsed = owid
          elif namedb == 'dgs':
             info('PRT, Direcção Geral de Saúde - Ministério da Saúde Português data selected ...')
             dgs = {
                 'tot_cases':['confirmados_1','FILLIT']
                 }
             url='https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data_concelhos_new.csv'
             self.separator = {url:','}
             urlmaster = 'https://github.com/dssg-pt/covid19pt-data'
             for k,v in dgs.items():
                   dgs[k].append(url)
                   dgs[k].append(urlmaster)
             self.pandasdb = pd.DataFrame(dgs,index=['Original name','Description','URL','Homepage'])
             rename = {'data': 'date','concelho':'where'}
             rename.update(self.original_to_available_keywords_dico())
             lurl=list(dict.fromkeys(self.get_url()))
             url=lurl[0]
             keep = ['date','where'] + self.get_url_original_keywords()[url]
             separator=self.get_url_separator(url)
             self.dbparsed = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
             self.dbparsed['tot_cases'] = self.dbparsed.groupby(['where'])['tot_cases'].cumsum()
          elif namedb == 'dpc':
              info('ITA, Dipartimento della Protezione Civile database selected ...')
              ita = {
              'tot_deaths':['deceduti','FILLIT'],\
              'tot_cases':['totale_casi','FILLIT']
              }
              url='https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv'
              self.separator = {url:','}
              masterurl='https://github.com/pcm-dpc/COVID-19'
              for k,v in ita.items():
                  ita[k].append(url)
                  ita[k].append(masterurl)
              self.pandasdb = pd.DataFrame(ita,index=['Original name','Description','URL','Homepage'])
              rename = {'data': 'date', 'denominazione_regione': 'where'}
              rename.update(self.original_to_available_keywords_dico())
              lurl=list(dict.fromkeys(self.get_url()))
              url=lurl[0]
              separator=self.get_url_separator(url)
              keep = ['date','where'] + self.get_url_original_keywords()[url]
              self.dbparsed = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator ,keep_field = keep)
          elif namedb == 'europa':
              info('EUR, Rationale for the JRC COVID-19 website - data monitoring and national measures ...')
              euro = {
                  'tot_deaths':['CumulativeDeceased','FILLIT'],
                  'tot_positive':['CumulativePositive','FILLIT'],
                  'cur_hosp':['Hospitalized','FILLIT'],
                  'cur_icu':['IntensiveCare','FILLIT'],
                  }
              url='https://raw.githubusercontent.com/ec-jrc/COVID-19/master/data-by-region/jrc-covid-19-all-days-by-regions.csv'
              self.separator={url:','}
              urlmaster='https://github.com/ec-jrc/COVID-19/tree/master/data-by-region'
              for k,v in euro.items():
                  euro[k].append(url)
                  euro[k].append(urlmaster)
              self.pandasdb = pd.DataFrame(euro,index=['Original name','Description','URL','Homepage'])
              lurl=list(dict.fromkeys(self.get_url()))
              url=lurl[0]
              rename = {'CountryName':'where','iso3':'iso_code','Date':'date'}
              rename.update(self.original_to_available_keywords_dico())
              separator=self.get_url_separator(url)
              keep = ['date','where','iso_code'] + self.get_url_original_keywords()[url]
              drop_field={'where':['Ciudad Autónoma de Melilla','Gorenjske','Goriške','Greenland','Itä-Savo','Jugovzhodne','Koroške','Länsi-Pohja',\
                      'Mainland','NOT SPECIFIED','Obalno-kraške','Osrednjeslovenske','Podravske','Pomurske','Posavske','Primorsko-notranjske',\
                      'Repatriierte','Savinjske','West North','Zasavske']}
              drop_field['iso_code']=['WWW']
              self.dbparsed = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator, drop_field=drop_field, keep_field = keep)
          elif namedb == 'escovid19data':
            info('ESP, EsCovid19Data ...')
            esco = {
            'tot_deaths':['deceased','Cumulative deaths  (original name deceased)'],\
            'tot_cases':['cases_accumulated_PCR','Number of new COVID-19 cases detected with PCR (original name cases_accumulated_PCR)'],\
            'cur_hosp':['hospitalized','Hospitalized (original name hospitalized)'],\
            'tot_hosp':['hospitalized_accumulated','Cumulative Hospitalized (original name hospitalized_accumulated)'],\
            'cur_hosp_per100k':['tot_cases_per100k','Intensive care per 100,000 inhabitants (original name hospitalized_per_100000'],\
            'cur_icu':['intensive_care','UCI, intensive care patient, (original name intensive_care)'],\
            'tot_recovered':['recovered','Recovered (original name recovered)'],\
            'tot_cases_per100k':['cases_per_cienmil','Cumulative cases per 100,000 inhabitants (original name cases_per_cienmil)'],\
            'cur_icu_per1M' :['intensive_care_per_1000000','Intensive care per 1000,000 inhabitants (original name intensive_care_per_1000000)'],\
            'tot_deaths_per100k':['deceassed_per_100000','Cumulative deaths per 100,000 inhabitants (original name deceassed_per_100000)'],\
            'cur_hosp_per100k':['hospitalized_per_100000','Hosp per 100,000 inhabitants, (original name hospitalized_per_100000)'],\
            'incidence':['ia14','Cases in 14 days by 100,000 inhabitants (original name ia14'],\
            'population':['poblacion','Inhabitants of the province (orignal name poblacion)'],\
            }
            url='https://raw.githubusercontent.com/montera34/escovid19data/master/data/output/covid19-provincias-spain_consolidated.csv'
            urlmaster='https://github.com/montera34/escovid19data'
            self.separator = {url:','}
            for k,v in esco.items():
                esco[k].append(url)
                esco[k].append(urlmaster)
            self.pandasdb = pd.DataFrame(esco,index=['Original name','Description','URL','Homepage'])
            lurl=list(dict.fromkeys(self.get_url()))
            url=lurl[0]
            rename = {'ine_code': 'where'}
            rename.update(self.original_to_available_keywords_dico())
            separator=self.get_url_separator(url)
            keep = ['date','where'] + self.get_url_original_keywords()[url]
            esp_data = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
            esp_data['where']=esp_data['where'].astype(str).str.zfill(2)
            for w in list(esp_data.columns):
                if w not in ['date','where']:
                    esp_data[w]=pd.to_numeric(esp_data[w], errors = 'coerce')
            self.dbparsed = esp_data
          elif namedb == 'govcy':
            info('Cyprus, govcy database selected ...')
            mi = {
            'tot_deaths':['total deaths','total deaths attributed to Covid-19 disease (total deaths)'],\
            'tot_cases':['total cases','total number of confirmed cases (total cases)'],\
            'cur_hosp':['Hospitalised Cases','number of patients with covid-19 hospitalized cases (Hospitalised Cases)'],\
            'cur_icu':['Cases In ICUs','number of patients with covid-19 admitted to ICUs (Cases In ICUs)'],\
            'cur_incub':['Incubated Cases','number of patients with covid-19 admitted to ICUs (Incubated Cases)'],\
            'tot_pcr':['total PCR tests','extract from PCR_daily tests performedtotal number of PCR tests performed (PCR_daily tests performed)'],\
            'tot_rat':['total RA tests','total number of rapid antigen (RAT) tests performed (total RA tests)'],\
            'tot_test':['total tests','total numbers of PCR and RA tests performed (total tests)'],\
            }
            url='https://www.data.gov.cy/sites/default/files/CY%20Covid19%20Open%20Data%20-%20Extended%20-%20new_247.csv'
            self.separator = {url:','}
            masterurl='https://www.data.gov.cy/node/4617?language=en'
            for k,v in mi.items():
                mi[k].append(url)
                mi[k].append(masterurl)
            mydico = mi
            self.pandasdb = pd.DataFrame(mi,index=['Original name','Description','URL','Homepage'])
            rename=self.original_to_available_keywords_dico()
            lurl=list(dict.fromkeys(self.get_url()))
            url=lurl[0]
            separator=self.get_url_separator(url)
            keep = ['date'] + self.get_url_original_keywords()[url]
            self.dbparsed = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
          elif namedb == 'imed':
                  info('Greece, imed database selected ...')
                  imed = {
                  'tot_deaths':['deaths','FILLIT'],
                  'tot_cases':['cases','FILLIT']
                  }
                  urlb = 'https://raw.githubusercontent.com/iMEdD-Lab/open-data/master/COVID-19/greece_'
                  masterurl='https://github.com/iMEdD-Lab/open-data/tree/master/COVID-19'
                  for k,v in imed.items():
                       url=urlb+v[0]+'_v2.csv'
                       self.separator[url]=','
                       imed[k].append(url)
                       imed[k].append(masterurl)
                  self.pandasdb = pd.DataFrame(imed,index=['Original name','Description','URL','Homepage'])
                  rename={'county_normalized':'where'}
                  rename.update(self.original_to_available_keywords_dico())
                  drop_columns=['Γεωγραφικό Διαμέρισμα','Περιφέρεια','county','pop_11']
                  self.column_where_csv_parser(namedb, rename_columns = rename,drop_columns=drop_columns)
          elif namedb == 'insee':
                   info('FRA, INSEE global deaths statistics...')
                   url = "https://www.data.gouv.fr/fr/datasets/fichier-des-personnes-decedees/"
                   insee = {
                   'tot_deaths_since_2018-01-01':['daily_number_of_deaths','tot deaths number_of_deaths integrated since 2018-01-01 '],\
                   }
                   for k,v in insee.items():
                       insee[k].append(url)
                       insee[k].append('')
                   self.pandasdb = pd.DataFrame(insee,index=['Original name','Description','URL','Homepage'])
                   since_year=2018 # Define the first year for stats
                   with open(get_local_from_url(url,86400*7)) as fp: # update each week
                       soup = BeautifulSoup(fp,features="lxml")
                   ld_json=soup.find('script', {'type':'application/ld+json'}).contents
                   data=json.loads(ld_json[0])
                   deces_url={}
                   for d in data['distribution']:
                       deces_url.update({d['name']:d['url']})
                   dc={}
                   current_year=datetime.date.today().year
                   current_month=datetime.date.today().month

                   # manage year between since_year-1 and current_year(excluded)
                   for y in range(since_year-1,current_year):
                       i=str(y) #  in string
                       filename='deces-'+i+'.txt'
                       if filename not in list(deces_url.keys()):
                           continue
                       with open(get_local_from_url(deces_url[filename],86400*30)) as f:
                           dc.update({i:f.readlines()})

                   # manage months for the current_year
                   for m in range(current_month):
                       i=str(m+1).zfill(2) #  in string with leading 0
                       filename='deces-'+str(current_year)+'-m'+i+'.txt'
                       if filename not in list(deces_url.keys()):
                           continue
                       with open(get_local_from_url(deces_url[filename],86400)) as f:
                           dc.update({i:f.readlines()})

                   def string_to_date(s):
                       date=None
                       y=int(s[0:4])
                       m=int(s[4:6])
                       d=int(s[6:8])
                       if m==0:
                           m=1
                       if d==0:
                           d=1
                       if y==0:
                           raise ValueError
                       try:
                           date=datetime.date(y,m,d)
                       except:
                           if m==2 and d==29:
                               d=28
                               date=datetime.date(y,m,d)
                               raise ValueError
                       return date
                   pdict={}
                   insee_pd=pd.DataFrame()
                   for i in list(dc.keys()):
                       data=[]

                       for l in dc[i]:
                           [last_name,first_name]=(l[0:80].split("/")[0]).split("*")
                           sex=int(l[80])
                           birthlocationcode=l[89:94]
                           birthlocationname=l[94:124].rstrip()
                           try:
                               birthdate=string_to_date(l[81:89])
                               deathdate=string_to_date(l[154:].strip()[0:8]) # sometimes, heading space
                               lbis=list(l[154:].strip()[0:8])
                               lbis[0:4]=list('2003')
                               lbis=''.join(lbis)
                               deathdatebis=string_to_date(lbis)
                           except ValueError:
                               if lbis!='20030229':
                                   verb('Problem in a date parsing insee data for : ',l,lbis)
                           deathlocationcode=l[162:167]
                           deathlocationshortcode=l[162:164]
                           deathid=l[167:176]
                           data.append([deathlocationshortcode,deathdate])
                       p=pd.DataFrame(data)
                       p.columns=['where','death_date']
                       insee_pd=pd.concat([insee_pd,p])
                   insee_pd = insee_pd[['where','death_date']].reset_index(drop=True)
                   insee_pd = insee_pd.rename(columns={'death_date':'date'})
                   insee_pd['date']=pd.to_datetime(insee_pd['date']).dt.date
                   insee_pd['where']=insee_pd['where'].astype(str)
                   insee_pd = insee_pd.groupby(['date','where']).size().reset_index(name='daily_number_of_deaths')

                   since_date=str(since_year)+'-01-01'
                   insee_pd = insee_pd[insee_pd.date>=datetime.date.fromisoformat(since_date)].reset_index(drop=True)
                   insee_pd['tot_deaths_since_'+since_date]=insee_pd.groupby('where')['daily_number_of_deaths'].cumsum()
                   insee_pd=insee_pd.drop(columns='daily_number_of_deaths')
                   self.dbparsed = insee_pd
          elif namedb == 'jhu':
               info('JHU aka Johns Hopkins database selected ...')
               jhu = {
               'tot_deaths':['deaths','counts include confirmed and probable (where reported).'],\
               'tot_confirmed':['confirmed','counts include confirmed and probable (where reported).'],\
               'tot_recovered':['recovered','cases are estimates based on local media reports, and state and local reporting'+
                                 'when available, and therefore may be substantially lower than the true number.US state-level recovered cases'+
                                 'are from COVID Tracking Project (https://covidtracking.com/)']\
                }
               base_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'+\
                          'csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_'
               masterurl = 'https://github.com/CSSEGISandData/COVID-19'
               for k,v in jhu.items():
                    url=base_url+v[0]+"_global.csv"
                    self.separator[url]=','
                    jhu[k].append(url)
                    jhu[k].append(masterurl)
               self.pandasdb = pd.DataFrame(jhu,index=['Original name','Description','URL','Homepage'])
               rename={'Country/Region':'where'}
               drop_columns=['Province/State','Lat','Long']
               drop_field={'where':['Diamond Princess']}
               rename.update(self.original_to_available_keywords_dico())
               self.column_where_csv_parser(namedb,rename_columns=rename,drop_columns=drop_columns,drop_field=drop_field)
          elif namedb == 'jhu-usa':
               info('JHU USA aka Johns Hopkins USA database selected ...')
               base_url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'+\
               'csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_'
               jhuusa = {
               'tot_deaths':['deaths','counts include confirmed and probable (where reported).'],\
               'tot_confirmed':['confirmed','counts include confirmed and probable (where reported).'],\
               }
               masterurl="https://github.com/CSSEGISandData/COVID-19"
               for k,v in jhuusa.items():
                    url=base_url+v[0]+"_US.csv"
                    self.separator[url]=','
                    jhuusa[k].append(url)
                    jhuusa[k].append(masterurl)
               self.pandasdb = pd.DataFrame(jhuusa,index=['Original name','Description','URL','Homepage'])
               rename={'Province_State':'where'}
               rename.update(self.original_to_available_keywords_dico())
               drop_columns=['UID','iso2','iso3','code3','FIPS','Admin2','Country_Region','Lat','Long_','Combined_Key']
               drop_field={'where':['American Samoa','Diamond Princess','Grand Princess','Guam',\
                                    'Northern Mariana Islands','Puerto Rico','Virgin Islands']}
               self.column_where_csv_parser(namedb, rename_columns = rename,drop_columns=drop_columns,drop_field=drop_field)
          elif namedb == 'jpnmhlw':
             info('JPN, Ministry of wealth, labor and welfare')
             jpn = {
                 'tot_deaths':['deaths_cumulative_daily','FILLIT'],\
                 'cur_cases':['newly_confirmed_cases_daily','FILLIT'],\
                 'cur_cases_per_100_thousand':['newly_confirmed_cases_per_100_thousand_population_daily','FILLIT'],\
                 'tot_cases':['confirmed_cases_cumulative_daily','FILLIT'],\
                 'cur_severe_cases':['severe_cases_daily','FILLIT'],\
                 'cur_deaths':['number_of_deaths_daily','FILLIT'] ,\
                 }
             urlb = 'https://covid19.mhlw.go.jp/public/opendata/'
             urlmaster='https://covid19.mhlw.go.jp/en/'

             for k,v in jpn.items():
                 url=urlb+v[0]+".csv"
                 self.separator[url]=','
                 jpn[k].append(url)
                 jpn[k].append(urlmaster)
             self.pandasdb = pd.DataFrame(jpn,index=['Original name','Description','URL','Homepage'])

             def df_import_and_reshape_jpn(original,available):
                 url = self.pandasdb[available]['URL']
                 df_var = pd.read_csv(url)
                 df_var = df_var.drop(['ALL'], axis=1)
                 df_var = pd.melt(frame = df_var,id_vars = "Date")
                 rename = {'variable' : 'where', 'Date' : 'date', 'value' : available}
                 df_var = df_var.rename(columns = rename)
                 keep = ['date','where'] + self.get_url_original_keywords()[url]
                 return df_var

             def df_merge_jpn(dict_var):
                 df_var = pd.DataFrame()
                 for k,v in dict_var.items():
                     if df_var.empty :
                       df_var = df_import_and_reshape_jpn(k,v)
                     else :
                       df_var = pd.merge(df_var,df_import_and_reshape_jpn(k,v), on = ['date','where'])
                 return df_var
             rename=self.original_to_available_keywords_dico()
             df_japan = df_merge_jpn(rename) # use a function to obtain the df
             df_japan['date'] = pd.to_datetime(df_japan['date'])
             self.dbparsed = df_japan
          elif namedb == 'moh':
            info('Malaysia moh covid19-public database selected ...')
            url0='https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/cases_state.csv'
            url1='https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/hospital.csv'
            url2='https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/icu.csv'
            url3='https://raw.githubusercontent.com/CITF-Malaysia/citf-public/main/vaccination/vax_state.csv'
            url4='https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/deaths_state.csv'
            self.separator={url0:',',url1:',',url2:',',url3:',',url4:','}
            moh = {
            'tot_deaths':['deaths_new','from original data deaths_new',url4],\
            'tot_cases':['cases_new','from original data cases_new',url0],\
            'hosp_covid':['hosp_covid','FILLIT',url1],\
            'icu_covid':['icu_covid','FILLIT',url2],\
            'beds_icu_covid':['beds_icu_covid','beds_icu_covid',url2],\
            'daily_partial':['daily_partial','FILLIT',url3],\
            'daily_full':['daily_full','FILLIT',url3],\
            }
            for k,v in moh.items():
                moh[k].append("https://github.com/MoH-Malaysia/covid19-public")
            self.pandasdb = pd.DataFrame(moh,index=['Original name','Description','URL','Homepage'])
            lurl=list(dict.fromkeys(self.get_url()))
            url=lurl[0]
            list_moh=[]
            cast = {'where': 'string'}
            constraints = {'sexe': 0,'cl_age90': 0}
            rename = {'state':'where'}
            rename.update(self.original_to_available_keywords_dico())
            for url in lurl:
                keep = ['date','where'] + self.get_url_original_keywords()[url]
                separator=self.get_url_separator(url)
                list_moh.append(self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator, constraints = constraints, cast = cast, keep_field = keep))
            result=pd.DataFrame()
            for i in list_moh:
                if result.empty:
                    result=i
                else:
                    result=result.merge(i, how = 'outer', on=['where','date'])
            result = reduce(lambda left, right: left.merge(right, how = 'outer', on=['where','date']), list_moh)
            result['tot_cases']=result.groupby(['where'])['tot_cases'].cumsum()
            result['tot_deaths']=result.groupby(['where'])['tot_deaths'].cumsum()
            self.dbparsed=result
          elif namedb == 'mpoxgh':
            info('MonkeyPoxGlobalHealth selected...')
            url='https://raw.githubusercontent.com/owid/monkeypox/main/owid-monkeypox-data.csv'
            self.separator = {url:','}
            urlmaster='https://github.com/owid/monkeypox'
            mpoxgh = {
                'total_deaths': ['total death cases','FILLIT',url,urlmaster],\
                'total_cases': ['total confirmed cases','FILLIT',url,urlmaster],\
                }
            self.pandasdb = pd.DataFrame(mpoxgh,index=['Original name','Description','URL','Homepage'])
            lurl=list(dict.fromkeys(self.get_url()))
            url=lurl[0]
            keep = ['date','where'] + self.get_url_original_keywords()[url]
            rename = {'Date_confirmation':'date','iso_code':'where'}
            rename.update(self.original_to_available_keywords_dico())
            separator=self.get_url_separator(url)
            self.dbparsed = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator, keep_field = keep)
          elif namedb == 'phe':
            info('GBR, Public Health England data ...')
            phe = {
            'tot_deaths':['cumDeaths28DaysByDeathDate','Total number of deaths '],\
            'tot_cases':['cumCasesBySpecimenDate','Total number of cases'],
            'tot_tests':['cumLFDTestsBySpecimenDate','Total number of tests'],
            'tot_vacc1':['cumPeopleVaccinatedFirstDoseByVaccinationDate','FILLIT'],
            'tot_vacc2':['cumPeopleVaccinatedSecondDoseByVaccinationDate','FILLIT']
            }
            urlb='https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla&metric='
            urlmaster='https://coronavirus.data.gov.uk/details/download'
            self.separator={}
            for k,v in phe.items():
                url=urlb+phe[k][0] +'&format=csv'
                self.separator[url]=','
                phe[k].append(url)
                phe[k].append(urlmaster)
            burl= 'https://covid-surveillance-data.cog.sanger.ac.uk/download/lineages_by_ltla_and_week.tsv'
            phe['lineageB.1.617.2']=['Count','FILLIT',burl,urlmaster]
            self.separator[burl]='\t'
            self.pandasdb = pd.DataFrame(phe,index=['Original name','Description','URL','Homepage'])
            lurl=list(dict.fromkeys(self.get_url()))
            list_phe=[]
            rename = {'areaCode':'where','WeekEndDate': 'date','LTLA':'where'}
            rename.update(self.original_to_available_keywords_dico())
            constraints = {}
            for idx,url in enumerate(lurl):
                keep = ['date','where'] + self.get_url_original_keywords()[url]
                separator=self.get_url_separator(url)
                if idx==3:
                    constraints = {'Lineage': 'B.1.617.2'}
                list_phe.append(self.row_where_csv_parser(url=url,rename_columns = rename, constraints=constraints, separator = separator,keep_field = keep))
            result=pd.DataFrame()
            for i in list_phe:
                if result.empty:
                    result=i
                else:
                    result = result.merge(i, how = 'outer', on=['where','date'])
            del list_phe
            self.dbparsed = result
          elif namedb == 'risklayer':
              info('EUR, Who Europe from RiskLayer ...')
              risk = {
                  'tot_positive': ['CumulativePositive','FILLIT'],\
                  'tot_incidence': ['IncidenceCumulative','FILLIT'],\
                  }
              url='https://docs.google.com/spreadsheets/d/e/2PACX-1vQ-JLawOH35vPyOk39w0tjn64YQLlahiD2AaNfjd82pgQ37Jr1K8KMHOqJbxoi4k2FZVYBGbZ-nsxhi/pub?output=csv'
              self.separator={url:','}
              masterurl='https://www.risklayer-explorer.com/event/100/detail'
              for k,v in risk.items():
                  risk[k].append(url)
                  risk[k].append(masterurl)
              self.pandasdb = pd.DataFrame(risk,index=['Original name','Description','URL','Homepage'])
              lurl=list(dict.fromkeys(self.get_url()))
              url=lurl[0]
              rename = {'UID': 'where','DateRpt':'date'}
              keep = ['date','where'] + self.get_url_original_keywords()[url]
              rename.update(self.original_to_available_keywords_dico())
              separator=self.get_url_separator(url)
              self.dbparsed = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
          elif namedb == 'rki':
              info('DEU, Robert Koch Institut data selected ...')
              rki = {
              'tot_deaths':['tot_deaths','FILLIT'],
              'tot_cases':['tot_cases','FILLIT']
              }
              url='https://github.com/jgehrcke/covid-19-germany-gae/raw/master/deaths-rki-by-ags.csv'
              masterurl='https://github.com/jgehrcke/covid-19-germany-gae'
              self.separator = {url:','}
              for k,v in rki.items():
                  rki[k].append(url)
                  rki[k].append(masterurl)
              self.pandasdb = pd.DataFrame(rki,index=['Original name','Description','URL','Homepage'])
              drop_field={'where':['sum_'+self.get_url_original_keywords()[url][0]]}
              rename={'index':'where'}
              self.column_where_csv_parser(namedb, rename_columns = rename,drop_field=drop_field)
          elif namedb == 'spf':
              info('SPF aka Sante Publique France database selected (France departement granularity) ...')
              info('... 5 SPF databases will be parsed ...')
              urlmaster0='https://www.data.gouv.fr/fr/datasets/donnees-de-laboratoires-pour-le-depistage-a-compter-du-18-05-2022-si-dep/'
              urlmaster1='https://www.data.gouv.fr/fr/datasets/donnees-de-laboratoires-pour-le-depistage-a-compter-du-18-05-2022-si-dep/'
              urlmaster2='https://www.data.gouv.fr/fr/datasets/indicateurs-de-suivi-de-lepidemie-de-covid-19/'
              urlmaster3='https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-personnes-vaccinees-contre-la-covid-19-1'
              urlmaster4='https://www.data.gouv.fr/fr/datasets/donnees-de-laboratoires-pour-le-depistage-indicateurs-sur-les-mutations/'
              urlmaster5='https://www.data.gouv.fr/en/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/'
              url0='https://www.data.gouv.fr/fr/datasets/r/ca490480-09a3-470f-8556-76d6fd291325'
              url1='https://www.data.gouv.fr/fr/datasets/r/5c4e1452-3850-4b59-b11c-3dd51d7fb8b5'
              url2='https://www.data.gouv.fr/fr/datasets/r/4acad602-d8b1-4516-bc71-7d5574d5f33e'
              url3='https://www.data.gouv.fr/fr/datasets/r/83cbbdb9-23cb-455e-8231-69fc25d58111'
              url4='https://www.data.gouv.fr/fr/datasets/r/bc318bc7-fb90-4e76-a6cb-5cdc0a4e5432'
              url5='https://www.data.gouv.fr/en/datasets/r/eceb9fb4-3ebc-4da3-828d-f5939712600a'
              self.separator={url0:';',url1:',',url2:',',url3:';',url4:';',url5:';',}
              spfdic = {
              'tot_dchosp':['dchosp','FILLIT',url1,urlmaster1],\
              'tot_P':['P','Nombre total de tests positifs',url0,urlmaster0],\
              'tot_T':['T','Nombre total de tests réalisés',url0,urlmaster0],\
              'cur_hosp':['hosp','FILLIT',url1,urlmaster1],\
              'tot_rad':['rad','FILLIT',url1,urlmaster1],\
              'cur_rea':['rea','FILLIT',url1,urlmaster1],\
              'cur_idx_tx_incid':['tx_incid','Taux d\'incidence (activité épidémique : Le taux d\'incidence correspond au nombre de personnes testées\
              positives (RT-PCR et test antigénique) pour la première fois depuis plus de 60 jours rapporté à la taille de la population. \
              Il est exprimé pour 100 000 habitants)',url1,urlmaster1],\
              'incid_hosp':['incid_hosp','Nombre total de personnes hospitalisées',url1,urlmaster1],\
              'incid_rea':['incid_rea','Nombre total d\'admissions en réanimation',url1,urlmaster1],\
              'incid_rad':['incid_rad','Nombre total de  retours à domicile',url1,urlmaster1],\
              'incid_dchosp':['incid_dchosp','Nombre total de personnes  décédées',url1,urlmaster1],\
              'cur_idx_R':['R','FILLIT',url2,urlmaster2],\
              'cur_idx_tx_occupation_sae':['taux_occupation_sae','FILLIT',url2,urlmaster2],\
              'cur_tx_pos':['tx_pos','Taux de positivité des tests virologiques (Le taux de positivité correspond au nombre de personnes testées positives\
               (RT-PCR et test antigénique) pour la première fois depuis plus de 60 jours rapporté au nombre total de personnes testées positives ou \
               négatives sur une période donnée ; et qui n‘ont jamais été testées positive dans les 60 jours précédents.)',url2,urlmaster3],
              'tot_vacc1':['n_cum_dose1','FILLIT',url3,urlmaster3],\
              'tot_vacc_complet':['n_cum_complet','FILLIT',url3,urlmaster3],\
              'tot_vacc_rappel':['n_cum_rappel','FILLIT',url3,urlmaster3],\
              'tot_vacc2_rappel':['n_cum_2_rappel','FILLIT',url3,urlmaster3],\
              'cur_nb_A0' :['nb_A0','Nombre des tests positifs pour lesquels la recherche de mutation A est négatif (A = E484K)',url4,urlmaster4],\
              'cur_nb_A1':['nb_A1','Nombre des tests positifs pour lesquels la recherche de mutation A est positif (A = E484K)',url4,urlmaster4],\
              'cur_tx_A1' :['tx_A1','Taux de présence mutation A (A = E484K)',url4,urlmaster4],\
              'cur_nb_C0' :['nb_C0','Nombre des tests positifs pour lesquels la recherche de mutation C est négatif (C = L452R)',url4,urlmaster4],\
              'cur_nb_C1' :['nb_C1','Nombre des tests positifs pour lesquels la recherche de mutation C est positif (C = L452R)',url4,urlmaster4],\
              'cur_tx_C1' :['tx_C1','Taux de présence mutation C (C = L452R)',url4,urlmaster4],\
              'cur_nbre_pass_corona':['nbre_pass_corona','Nombre de passages aux urgences pour suspicion de COVID-19 (nbre_pass_corona)',url5,urlmaster5],
              }
              self.pandasdb = pd.DataFrame(spfdic,index=['Original name','Description','URL','Homepage'])
              list_spf=[]
              cast = {'where': 'string'}
              constraints = {'sexe': 0,'cl_age90': 0}
              rename = {'jour': 'date', 'dep': 'where','extract_date': 'date', 'departement': 'where','date_de_passage':'date'}
              rename.update(self.original_to_available_keywords_dico())
              lurl=list(dict.fromkeys(self.get_url()))
              for idx,url in enumerate(lurl):
                  keep = ['date','where'] + self.get_url_original_keywords()[url]
                  separator = self.get_url_separator(url)
                  sp = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator, constraints = constraints, cast = cast, keep_field = keep)
                  list_spf.append(sp)
              result=pd.DataFrame()
              for i in list_spf:
                  if result.empty:
                      result=i
                  else:
                      result=result.merge(i, how = 'outer', on=['where','date'])
              del list_spf
              result[['tot_T','tot_P']] = result[['tot_T','tot_P']].stack().str.replace(',','.').unstack()
              result = result.loc[~result['where'].isin(['00'])]
              result = result.sort_values(by=['where','date'])
              result.loc[result['where'].isin(['975','977','978','986','987']),'where']='980'
              result = result.drop_duplicates(subset=['where', 'date'], keep='last')
              for w in list(result.columns):
                  if w not in ['where', 'date']:
                      result[w]=pd.to_numeric(result[w], errors = 'coerce')
                      if w.startswith('incid_'):
                          result[w] = result.groupby('where')[w].fillna(method = 'bfill')
                      if w in ['tot_P','tot_T']:
                          result[w]=result.groupby(['where'])[w].cumsum()
              self.dbparsed = result
          elif namedb == 'spfnational':
              info('SPFNational, aka Sante Publique France, database selected (France with no granularity) ...')
              spfn = {
              'tot_dc_hosp':['dchosp','Cumul des décès (cumul des décès constatés à l\'hôpital et en EMS)'],\
              'cur_reanimation':['incid_rea','Nombre de nouveaux patients admis en réanimation au cours des dernières 24h.'],\
              'cur_hospitalises':['incid_hosp','Nombre de nouveaux patients hospitalisés au cours des dernières 24h.'],\
              'cur_cas':['conf_j1','Nombre de nouveaux cas confirmés (J-1 date de résultats)'],\
              'tot_dc_esms':['esms_dc','Décès en ESMS'],\
              'tot_dc':['dc_tot','FILL IT'],\
              'cur_tx_pos':['tx_pos','Taux de positivité des tests virologiques'],\
              }
              url = 'https://www.data.gouv.fr/fr/datasets/r/f335f9ea-86e3-4ffa-9684-93c009d5e617'
              self.separator = {url:','}
              urlmaster = 'https://www.data.gouv.fr/fr/datasets/synthese-des-indicateurs-de-suivi-de-lepidemie-covid-19/'
              for k,v in spfn.items():
                    spfn[k].append(url)
                    spfn[k].append(urlmaster)
              self.pandasdb = pd.DataFrame(spfn,index=['Original name','Description','URL','Homepage'])
              lurl=list(dict.fromkeys(self.get_url()))
              url=lurl[0]
              rename=self.original_to_available_keywords_dico()
              separator=self.get_url_separator(url)
              keep = ['date'] + self.get_url_original_keywords()[url]
              spfnat = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
              colcast=[i for i in self.get_available_keywords()]
              spfnat[colcast]=pd.to_numeric(spfnat[colcast].stack(),errors = 'coerce').unstack()
              self.dbparsed = spfnat
          elif namedb == 'sciensano':
              info('BEL, Sciensano Belgian institute for health data  ...')
              sci = {
              'tot_hosp':['TOTAL_IN','Total number of lab-confirmed hospitalized COVID-19 patients at the moment of reporting, including ICU (prevalence) (original name TOTAL_IN)'],\
              'tot_icu':['TOTAL_IN_ICU','Total number of lab-confirmed hospitalized COVID-19 patients in ICU at the moment of reporting (prevalence) (original name TOTAL_IN_ICU)'],\
              'cur_reporting':['NR_REPORTING','Number of hospitals reporting'],\
              'cur_confirmed':['NEW_IN','Number of new lab-confirmed COVID-19 patients in the last 24h (incidence),\
                                not referred from another hospital. This number excludes the patients that were admitted\
                                to the hospital for other reasons but tested positive for COVID-19 in a screening context.']
              }
              url='https://epistat.sciensano.be/Data/COVID19BE_HOSP.csv'
              self.separator = {url:','}
              masterurl='https://epistat.wiv-isp.be/covid/'
              for k,v in sci.items():
                  sci[k].append(url)
                  sci[k].append(masterurl)
              self.pandasdb = pd.DataFrame(sci,index=['Original name','Description','URL','Homepage'])
              lurl=list(dict.fromkeys(self.get_url()))
              url=lurl[0]
              rename = {'DATE' : 'date', 'PROVINCE':'where'}
              rename.update(self.original_to_available_keywords_dico())
              separator=self.get_url_separator(url)
              keep = ['date','where'] + self.get_url_original_keywords()[url]
              beldata = self.row_where_csv_parser(url=url,rename_columns = rename, separator = separator,keep_field = keep)
              colcast=[i for i in self.get_available_keywords()]
              beldata[colcast]=pd.to_numeric(beldata[colcast].stack(),errors = 'coerce').unstack()
              self.dbparsed = beldata
              '''
              [rename_dict.pop(i) for i in ['DATE','PROVINCE']]
              columns_keeped = list(rename_dict.values())
              cvsloc2jsonloc={
              'BrabantWallon':'Brabant wallon (le)',\
              'Brussels':'Région de Bruxelles-Capitale',\
              'Limburg':'Limbourg (le)',\
              'OostVlaanderen':'Flandre orientale (la)',\
              'Hainaut':'Hainaut (le)',\
              'VlaamsBrabant':'Brabant flamand (le)',\
              'WestVlaanderen':'Flandre occidentale (la)',\
              }
              beldata['where'].replace(cvsloc2jsonloc, inplace=True)
              beldata['date'] = pandas.to_datetime(beldata['date'],errors='coerce').dt.date
              self.return_structured_pandas(beldata,columns_keeped=columns_keeped)
              '''
          #TEST OLYMPICS AVEC FONCTION
          elif namedb == 'olympics':
                info('Olympics data selected test with fonction...')

                urls = [
                    'https://raw.githubusercontent.com/NoamXD8/olympics/main/athlete_events-1.csv',
                    'https://raw.githubusercontent.com/NoamXD8/olympics/main/athlete_events-2.csv',
                    'https://raw.githubusercontent.com/NoamXD8/olympics/main/athlete_events-3.csv'
                ]

                translation = pd.read_csv('https://raw.githubusercontent.com/NoamXD8/olympics/main/Liste_des_codes_pays_du_CIO_2.csv')
                translation.rename(columns={"Code\nCIO": "CIO", "ISO 3166-1\nalpha-3": "ISO3"}, inplace=True)
                dic_iso = {i: j for i, j in zip(translation["CIO"], translation["ISO3"]) if i != j}
                dic_iso.update({
                    'CRT': 'GRC', 'GDR': 'DEU', 'NFL': 'NLD', 'SCG': 'SRB', 'YMD': 'YEM', 'FRG': 'DEU', 'IOA': 'Athlètes olympiques internationaux'
                })

                addmedals = ['Gold', 'Silver', 'Bronze']
                def process_olympic_data(url, dic_iso):
                    olympics = {
                    #'Medal': ['Medal', 'Medal Type (Gold, Silver, Bronze)'],
                    'tot_Gold':['Gold','Or Medal (PYCOA computed, absent in the orignal)'],
                    'tot_Silver':['Silver','Silver Medal (PYCOA computed, absent in the orignal)'],
                    'tot_Bronze':['Bronze','Bronze Medal (PYCOA computed, absent in the orignal)']
                    }

                    self.separator = {url:','}
                    masterurl = "https://github.com/NoamXD8/olympics"

                    for k,v in olympics.items():
                        olympics[k].append(url)
                        olympics[k].append(masterurl)
                    mydico = olympics
                    self.pandasdb = pd.DataFrame(olympics,index=['Original name','Description','URL', 'Homepage'])
                    rename = {'Year': 'date', 'Team': 'where', 'NOC': 'iso_code'}
                    rename.update(self.original_to_available_keywords_dico())

                    separator = self.get_url_separator(url)
                    keep = ['date', 'where', 'iso_code'] + ['Medal']
                    cast = {'Age': 'string', 'Height': 'string', 'Weight': 'string', 'City': 'string', 'Team': 'string'}

                    olympics = self.row_where_csv_parser(url=url, rename_columns=rename, separator=separator, cast=cast)
                    olympics = olympics.replace({'iso_code': dic_iso})
                    olympics = olympics.loc[~olympics.iso_code.isin(['WIF', 'IOA', 'AHO'])]

                    df = olympics.copy()
                    df = df[df['Season'] == 'Summer']
                    #The 1906 Olympic Games, known as the 'Games of the Decade', are not recognised by the IOC
                    df = df[~df['date'].isin([datetime.date(1906, 1, 1)])]

                    df['count'] = df.groupby(['date', 'iso_code', 'Medal', 'Event']).Medal.transform('count')
                    df = df.drop_duplicates(subset=['iso_code', 'date', 'Event', 'Medal'])
                    df = df.loc[~df.Medal.isin(['NA'])]

                    df = df.pivot_table(index=['iso_code', 'date'], columns='Medal', values='count', aggfunc='size')
                    df = df.fillna(0)

                    df = df.sort_values(by=['date'])
                    df = df.groupby(['date','iso_code'])[addmedals].sum()

                    #df = df.groupby(level=1).cumsum().reset_index().rename_axis(None, axis=1)
                    df = df.reset_index(level=1).reset_index()
                    df['where'] = df['iso_code']
                    df = df[['date', 'where', 'iso_code'] + addmedals].reset_index(drop=True)
                    return df

                all_olympics_data = pd.DataFrame()
                for url in urls:
                    olympics_data = process_olympic_data(url, dic_iso)
                    all_olympics_data = pd.concat([all_olympics_data, olympics_data], ignore_index=True)

                all_olympics_data = all_olympics_data.groupby(['date','where','iso_code'])[addmedals].sum()
                all_olympics_data=all_olympics_data.reset_index()

                oldRUS=['URS','RUS','EUN']
                tmp = all_olympics_data.loc[all_olympics_data['iso_code'].isin(oldRUS)].\
                                        groupby('date').sum(numeric_only=True).reset_index()
                tmp['where'] = 'RUS'
                tmp['iso_code'] = 'RUS'
                all_olympics_data = all_olympics_data.loc[~all_olympics_data['where'].isin(oldRUS)]
                all_olympics_data = pd.concat([all_olympics_data,tmp])

                all_olympics_data[addmedals]=all_olympics_data.groupby(['where'])[addmedals].cumsum()
                df=all_olympics_data

                self.dbparsed = all_olympics_data.reset_index()

                self.dbparsed = self.dbparsed[['date','where', 'iso_code']+addmedals]
                dicnewmedals={i:'tot_'+i for i in addmedals}
                self.dbparsed = self.dbparsed.rename(columns=dicnewmedals)
                info('Data processing completed and merged.')

      else:
          raise CoaKeyError('Error in the database selected: '+db+'.Please check !')
      if namedb not in ['jhu','jhu-usa','imed','rki']:
            self.restructured_pandas(self.dbparsed)


  def get_dblistdico(self,key=None):
      '''
        Return info concerning the db selected, i.e key, return iso code, granularity,name
      '''
      if key is None:
         return  _db_list_dict
      return _db_list_dict[key]

  def get_db(self):
     '''
        Return the current covid19 database selected. See get_available_database() for full list
     '''
     return self.db

  def get_geo(self):
      return self.geo

  def get_world_boolean(self):
    return self.db_world

  def get_original_keywords(self):
      '''
               Return all the original keyswords for the database selected
               original keyswords have been renamed into available_keywords
      '''
      return self.pandasdb.loc['Original name']

  def get_locations(self):
      ''' Return available location countries / regions in the current database
          Using the geo method standardization
      '''
      return self.slocation

  def get_dates(self):
      ''' Return all dates available in the current database as datetime format'''
      return self.dates.values

  def get_available_keywords(self):
      '''
           Return all the available keyswords for the database selected
      '''
      return list(self.pandasdb.columns)

  def get_url(self):
      '''
       Return all the url which have been parsed for the database selected
      '''
      return self.pandasdb.loc['URL']

  def get_keyword_definition(self,which):
      '''
           Return available keywords (originally named original keywords) definition
      '''
      return self.pandasdb.loc['Description'][which]

  def get_keyword_url(self,which):
      return self.pandasdb.loc['URL'][which]

  def get_dbdescription(self):
      '''
           Return available information concerning the db selected
      '''
      return self.pandasdb

  def get_url_original_keywords(self):
      '''
           Return dico with keys=url and values=[original keywords]
      '''
      dico={}
      for i in self.get_available_keywords():
           if self.pandasdb[i]['URL'] not in dico:
               dico[self.pandasdb[i]['URL']]=[i]
           else:
               dico[self.pandasdb[i]['URL']].append(i)
      return dico

  def original_to_available_keywords_dico(self):
      '''
         Return dico with keys=original keywords and values=available keywords
         used to rename the variable
      '''
      return {self.pandasdb[i]['Original name']:i for i in self.get_available_keywords()}

  def get_url_separator(self,url):
      '''
           Return dico with keys=url and values=';' or ','
           default is ';'
      '''
      if not bool(self.separator):
          return ';'
      return self.separator[url]

  def column_where_csv_parser(self,db,**kwargs):
    ''' For center for Systems Science and Engineering (CSSE) at Johns Hopkins University
        COVID-19 Data Repository by the see homepage: https://github.com/CSSEGISandData/COVID-19
        return a structure : pandas where - date - keywords
        for jhu where are countries (where uses geo standard)
        for jhu-usa where are Province_State (where uses geo standard)
        '''
    # previous are default for actual jhu db
    rename_columns = kwargs.get('rename_columns', None)
    drop_columns = kwargs.get('drop_columns', None)
    drop_field = kwargs.get('drop_field', None)
    self.available_keywords = []
    pandas_list = []
    lurl=list(dict.fromkeys(self.get_url()))
    mypd = pd.DataFrame()
    pandas_list = []
    for url in lurl:
        self.available_keywords.append(self.get_url_original_keywords()[url])
        separator = self.get_url_separator(url)
        mypd = pd.read_csv(get_local_from_url(url,7200), sep = separator) # cached for 2 hours
        if rename_columns:
            if db == 'rki':
                mypd = mypd.set_index('time_iso8601').T.reset_index().rename(columns=rename_columns)
            else:
                mypd = mypd.rename(columns=rename_columns)
        if drop_columns:
            mypd = mypd.drop(columns=drop_columns)
        mypd = mypd.melt(id_vars=['where'],var_name="date",value_name=self.get_url_original_keywords()[url][0])
        if drop_field:
          for key,val in drop_field.items():
              mypd =  mypd[~mypd[key].isin(val)]
        mypd=mypd.groupby(['where','date']).sum().reset_index()
        pandas_list.append(mypd)
    self.available_keywords = flat_list(self.available_keywords)
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
      if self.get_dblistdico(db)[1] == 'subregion':
          pdcodename = self.geo.get_subregion_list()
          self.slocation = uniqloc
          codename = collections.OrderedDict(zip(self.slocation,list(pdcodename.loc[pdcodename.code_subregion.isin(self.slocation)]['name_subregion'])))
          if db == 'jhu-usa':
              d_loc_s = collections.OrderedDict(zip(uniqloc,list(pdcodename.loc[pdcodename.name_subregion.isin(uniqloc)]['code_subregion'])))
              self.slocation = list(d_loc_s.keys())
              codename = d_loc_s
          if db == 'rki':
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
      elif self.get_dblistdico(db)[1] == 'region':
          codename = self.geo.get_data().set_index('name_region')['code_region'].to_dict()
          self.slocation = list(codename.keys())
      else:
          raise CoaTypeError('Not a region nors ubregion ... sorry but what is it ?')

    result = reduce(lambda x, y: pd.merge(x, y, on = ['where','date']), pandas_list)

    if location_is_code:
      result['codelocation'] = result['where']
      result['where'] = result['where'].map(codename)
    else:
      if db == 'jhu':
          result['where'] = result['where'].map(d_loc_s)
      result['codelocation'] = result['where'].map(codename)
    result = result.loc[result['where'].isin(self.slocation)]
    tmp = pd.DataFrame()
    if 'Kosovo' in uniqloc:
      #Kosovo is Serbia ! with geo.to_standard
      tmp=(result.loc[result['where'].isin(['Serbia'])]).groupby('date').sum(numeric_only=True).reset_index()
      tmp['where'] = 'Serbia'
      tmp['codelocation'] = 'SRB'
      kw = [i for i in self.available_keywords]
      colpos=['where', 'date'] + kw + ['codelocation']
      tmp = tmp[colpos]
      result = result.loc[~result['where'].isin(['Serbia'])]
      result = pd.concat([result,tmp])

    result = result.copy()
    result.loc[:,'date'] = pd.to_datetime(result['date'],errors='coerce',utc=True).dt.date
    result = result.sort_values(by=['where','date'])
    result = result.reset_index(drop=True)
    if db == 'jhu-usa':
      col=result.columns.tolist()
      ncol=col[:2]+col[2:]
      result=result[ncol]
      self.available_keywords+=['Population']
    self.mainpandas = fill_missing_dates(result)
    self.dates  = self.mainpandas['date']

  def row_where_csv_parser(self,**kwargs):
     '''
        Parse and convert the database cvs file to a pandas structure
     '''
     kwargs_test(kwargs,['url','cast','separator','encoding','constraints','rename_columns','keep_field','drop_field','quotechar'],
         'Bad args used in the csv2pandas() function.')
     url = kwargs.get('url', None)
     cast = kwargs.get('cast', None)
     separator = kwargs.get('separator', None)
     constraints = kwargs.get('constraints', None)
     rename_columns = kwargs.get('rename_columns', None)
     drop_field = kwargs.get('drop_field', None)
     keep_field = kwargs.get('keep_field', None)
     self.available_keywords = self.get_url_original_keywords()[url]
     #self.database_url.append(url)
     encoding = kwargs.get('encoding', None)
     if encoding:
         encoding = encoding
     quoting=0
     pandas_db = pd.read_csv(get_local_from_url(url,10000), sep=separator, encoding = encoding,
          keep_default_na=False,na_values='',header=0,quoting=quoting, dtype=cast,low_memory=False) # cached for 2 hours

     if constraints:
         for key,val in constraints.items():
             if key in pandas_db.columns:
                 pandas_db = pandas_db.loc[pandas_db[key] == val]
                 pandas_db = pandas_db.drop(columns=key)
     if rename_columns:
             pandas_db = pandas_db.rename(columns=rename_columns)

     if drop_field:
         for key,val in drop_field.items():
             pandas_db =  pandas_db[~pandas_db[key].isin(val)]
     if 'semaine' in  pandas_db.columns:
         pandas_db['semaine'] = [ week_to_date(i) for i in pandas_db['semaine']]
         pandas_db = pandas_db.rename(columns={'semaine':'date'})
     if keep_field:
         pandas_db =  pandas_db[keep_field]
     if self.db == "govcy":
        pandas_db['date'] = pd.to_datetime(pandas_db['date'], errors='coerce', format="%d/%m/%Y").dt.date
     elif self.db == "olympics":
        pandas_db['date'] = pd.to_datetime(pandas_db['date'], format='%Y', errors='coerce').dt.date
     else:
        pandas_db['date'] = pd.to_datetime(pandas_db['date'], errors='coerce', infer_datetime_format=True).dt.date

     if self.get_dblistdico(self.db)[1] == 'nation' and self.get_dblistdico(self.db)[0] in ['FRA','CYP'] or \
         self.db=="spfnational":
         pandas_db['where'] = self.get_dblistdico(self.db)[2]
     pandas_db = pandas_db.sort_values(['where','date'])
     return pandas_db

  def restructured_pandas(self,mypandas,**kwargs):
      '''
      Return the mainpandas core of the PyCoA structure
      '''
      kwargs_test(kwargs,['columns_skipped'],
          'Bad args used in the restructured_pandas function.')
      columns_skipped = kwargs.get('columns_skipped', None)

      if self.db_world and self.db not in ['govcy','spfnational','mpoxgh']:
          if self.db == 'olympics':
                not_UN_nation_dict=['KSO','SRB']
                tmp=(mypandas.loc[mypandas['where'].isin(not_UN_nation_dict)].groupby('date').sum(numeric_only=True)).reset_index()
                tmp['where'] = 'Serbia'
                tmp['iso_code'] = 'SRB'
          else:
              not_UN_nation_dict=['Kosovo','Serbia']
              tmp=(mypandas.loc[mypandas['where'].isin(not_UN_nation_dict)].groupby('date').sum(numeric_only=True)).reset_index()
              tmp['where'] = 'Serbia'
              tmp['iso_code'] = 'SRB'
          cols = tmp.columns.tolist()
          cols = cols[0:1] + cols[-1:] + cols[1:-1]
          tmp = tmp[cols]
          mypandas = mypandas.loc[~mypandas['where'].isin(not_UN_nation_dict)]
          mypandas = pd.concat([mypandas,tmp])
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
          #uniqloc = [s for s in uniqloc if 'OWID_' not in s]
          uniqloc = [s for s in uniqloc if isinstance(s, str) and 'OWID_' not in s]
          #print("UNIQLOC",uniqloc)
          db=self.get_db()
          if self.db in ['govcy','europa']:
              db=None
          codename = collections.OrderedDict(zip(uniqloc,self.geo.to_standard(uniqloc,output='list',db=db,interpret_region=True)))
          location_is_code = True
          self.slocation = list(codename.values())
      else:
          if self.get_dblistdico(self.db)[1] == 'region' :
              temp = self.geo.get_region_list()[['name_region','code_region']]
              codename=dict(temp.values)
              self.slocation = uniqloc
          elif self.get_dblistdico(self.db)[1] == 'subregion':
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

      mypandas = mypandas.groupby(['where','date']).sum(min_count=1).reset_index() # summing in case of multiple dates (e.g. in opencovid19 data). But keep nan if any
      if self.db == 'govcy' or self.db == 'jpnmhlw':
          location_is_code=False

      #mypandas = fill_missing_dates(mypandas)
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

      if self.db != 'olympics':
          # since olympics is 4 years it takes times if we fill nan ...
          self.mainpandas = fill_missing_dates(mypandas)
      else:
          self.mainpandas=mypandas
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
