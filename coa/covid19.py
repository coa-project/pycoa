# -*- coding: utf-8 -*-
"""
Project : PyCoA
Date :    april 2020 - march 2021
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
import coa.dbinfo as report
import coa.display as codisplay
from coa.error import *
from scipy import stats as sps
import random
from functools import reduce
import collections
from bs4 import BeautifulSoup
import json
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
        self.available_keys_words = []
        self.dates = []
        self.database_columns_not_computed = {}
        self.db = db_name
        self.geo_all = ''
        self.database_url = []
        self.db_world=None
        self.databaseinfo = report
        if self.db not in self.database_name:
            raise CoaDbError('Unknown ' + self.db + '. Available database so far in PyCoa are : ' + str(self.database_name), file=sys.stderr)
        else:
            try:
                if get_db_list_dict()[self.db][1] == 'nation': # world wide db
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
                elif self.db == 'govcy': #CYP
                    info('Cyprus, govcy database selected ...')
                    rename_dict = {'daily deaths': 'tot_deaths'}
                    gov = self.csv2pandas('https://www.data.gov.cy/sites/default/files/CY%20Covid19%20Open%20Data%20-%20Extended%20-%20new_247.csv'
                    ,separator=',')
                    columns_keeped = ['tot_deaths']
                    gov['tot_deaths']=gov.groupby(['location'])['daily deaths'].cumsum()
                    self.return_structured_pandas(gov, columns_keeped=columns_keeped)
                elif self.db == 'dpc': #ITA
                    info('ITA, Dipartimento della Protezione Civile database selected ...')
                    rename_dict = {'data': 'date', 'denominazione_regione': 'location', 'totale_casi': 'tot_cases','deceduti':'tot_deaths'}
                    dpc1 = self.csv2pandas('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv',\
                    rename_columns = rename_dict, separator=',')
                    #dpc1 = self.csv2pandas("https://github.com/pcm-dpc/COVID-19/raw/master/dati-province/dpc-covid19-ita-province.csv",\
                    columns_keeped = ['tot_deaths','tot_cases']
                    self.return_structured_pandas(dpc1, columns_keeped=columns_keeped)
                elif self.db == 'rki': # DEU
                    info('DEU, Robert Koch Institut data selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'dgs': # PRT
                    info('PRT, Direcção Geral de Saúde - Ministério da Saúde Português data selected ...')
                    rename_dict = {'data': 'date','concelho':'location','confirmados_1':'tot_cases'}
                    url='https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data_concelhos_new.csv'
                    prt_data=self.csv2pandas(url,separator=',',rename_columns = rename_dict)
                    columns_keeped = ['tot_cases']
                    self.return_structured_pandas(prt_data, columns_keeped=columns_keeped)
                elif self.db == 'obepine' : # FRA
                    info('FRA, réseau Obepine, surveillance Sars-Cov-2 dans les eaux usées')
                    url='https://www.data.gouv.fr/fr/datasets/r/69b8af15-c8c5-465a-bdb6-1ac73430e590'
                    #url='https://www.data.gouv.fr/fr/datasets/r/89196725-56cf-4a83-bab0-170ad1e8ef85'
                    rename_dict={'Code_Region':'location','Date':'date','Indicateur\"':'idx_obepine'}
                    cast = {'Code_Region': 'string'}
                    obepine_data=self.csv2pandas(url,cast=cast,separator=';',rename_columns=rename_dict)
                    obepine_data['idx_obepine']=obepine_data['idx_obepine'].astype(float)
                    self.return_structured_pandas(obepine_data,columns_keeped=['idx_obepine'])
                elif self.db == 'escovid19data': # ESP
                    info('ESP, EsCovid19Data ...')
                    rename_dict = {'ine_code': 'location',\
                        'deceased':'tot_deaths',\
                        'cases_accumulated_PCR':'tot_cases',\
                        'hospitalized':'cur_hosp',\
                        'hospitalized_accumulated':'tot_hosp',\
                        'intensive_care':'cur_icu',\
                        'recovered':'tot_recovered',\
                        'cases_per_cienmil':'tot_cases_per100k',\
                        'intensive_care_per_1000000':'cur_icu_per1M',\
                        'deceassed_per_100000':'tot_deaths_per100k',\
                        'hospitalized_per_100000':'cur_hosp_per100k',\
                        'ia14':'incidence',\
                        'poblacion':'population',\
                    }
                    #url='https://github.com/montera34/escovid19data/raw/master/data/output/covid19-provincias-spain_consolidated.csv'
                    url='https://raw.githubusercontent.com/montera34/escovid19data/master/data/output/covid19-provincias-spain_consolidated.csv'
                    col_names = pd.read_csv(get_local_from_url(url), nrows=0).columns
                    cast={i:'string' for i in col_names[17:]}
                    esp_data=self.csv2pandas(url,\
                        separator=',',rename_columns = rename_dict,cast = cast)
                    #print('Available columns : ')
                    #display(esp_data.columns)
                    esp_data['location']=esp_data.location.astype(str).str.zfill(2)
                    columns_keeped = list(rename_dict.values())
                    columns_keeped.remove('location')

                    for w in list(columns_keeped):
                            esp_data[w]=pd.to_numeric(esp_data[w], errors = 'coerce')

                    self.return_structured_pandas(esp_data,columns_keeped=columns_keeped)

                elif self.db == 'sciensano': #Belgian institute for health,
                    info('BEL, Sciensano Belgian institute for health data  ...')
                    rename_dict = { 'DATE' : 'date',\
                    'PROVINCE':'location',\
                    'TOTAL_IN':'cur_hosp',
                    'TOTAL_IN_ICU':'cur_icu',
                    'TOTAL_IN_RESP':'cur_resp',
                    'TOTAL_IN_ECMO':'cur_ecmo'}
                    url='https://epistat.sciensano.be/Data/COVID19BE_HOSP.csv'
                    beldata=self.csv2pandas(url,separator=',',rename_columns=rename_dict)
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
                    beldata["location"].replace(cvsloc2jsonloc, inplace=True)
                    beldata['date'] = pandas.to_datetime(beldata['date'],errors='coerce').dt.date
                    self.return_structured_pandas(beldata,columns_keeped=columns_keeped)
                elif self.db == 'phe': # GBR from owid
                    info('GBR, Public Health England data ...')
                    rename_dict = { 'areaCode':'location',\
                        'cumDeaths28DaysByDeathDate':'tot_deaths',\
                        'cumCasesBySpecimenDate':'tot_cases',\
                        'cumLFDTestsBySpecimenDate':'tot_tests',\
                        'cumPeopleVaccinatedFirstDoseByVaccinationDate':'tot_vacc1',\
                        'cumPeopleVaccinatedSecondDoseByVaccinationDate':'tot_vacc2',\
                        #'cumPeopleVaccinatedThirdInjectionByVaccinationDate':'tot_vacc3',\
                        #'covidOccupiedMVBeds':'cur_icu',\
                        #'cumPeopleVaccinatedFirstDoseByVaccinationDate':'tot_dose1',\
                        #'cumPeopleVaccinatedSecondDoseByVaccinationDate':'tot_dose2',\
                        #'hospitalCases':'cur_hosp',\
                        }
                    url = 'https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla'
                    for w in rename_dict.keys():
                        if w not in ['areaCode']:
                            url=url+'&metric='+w
                    url = url+'&format=csv'
                    gbr_data = self.csv2pandas(url,separator=',',rename_columns=rename_dict)
                    constraints = {'Lineage': 'B.1.617.2'}
                    url = 'https://covid-surveillance-data.cog.sanger.ac.uk/download/lineages_by_ltla_and_week.tsv'
                    gbrvar = self.csv2pandas(url,separator='\t',constraints=constraints,rename_columns = {'WeekEndDate': 'date','LTLA':'location'})
                    varname =  'B.1.617.2'
                    gbr_data = pd.merge(gbr_data,gbrvar,how="outer",on=['location','date'])
                    gbr_data = gbr_data.rename(columns={'Count':'cur_'+varname})
                    columns_keeped = list(rename_dict.values())
                    columns_keeped.append('cur_'+varname)
                    columns_keeped.remove('location')
                    self.return_structured_pandas(gbr_data,columns_keeped=columns_keeped)
                elif self.db == 'moh': # MYS
                    info('Malaysia moh covid19-public database selected ...')
                    rename_dict = {'state': 'location'}
                    moh1 = self.csv2pandas("https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/cases_state.csv",rename_columns=rename_dict,separator=',')
                    moh1['tot_cases']=moh1.groupby(['location'])['cases_new'].cumsum()

                    moh2 = self.csv2pandas("https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/hospital.csv",rename_columns=rename_dict,separator=',')
                    moh3 = self.csv2pandas("https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/icu.csv",rename_columns=rename_dict,separator=',')
                    moh4 = self.csv2pandas("https://raw.githubusercontent.com/CITF-Malaysia/citf-public/main/vaccination/vax_state.csv",rename_columns=rename_dict,separator=',')

                    list_moh = [moh1,moh2,moh3,moh4]
                    result = reduce(lambda left, right: left.merge(right, how = 'outer', on=['location','date']), list_moh)
                    columns_keeped = ['tot_cases','hosp_covid','daily_partial','daily_full','icu_covid','beds_icu_covid']
                    self.return_structured_pandas(result, columns_keeped = columns_keeped)
                elif self.db == 'minciencia': # CHL
                    info('Chile Ministerio de Ciencia, Tecnología, Conocimiento, e Innovación database selected ...')
                    cast = {'Codigo comuna': 'string'}
                    rename_dict = {'Codigo comuna':'location','Poblacion':'population','Fecha':'date','Casos confirmados':'cases'}
                    ciencia = self.csv2pandas("https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto1/Covid-19_std.csv",cast=cast,rename_columns=rename_dict,separator=',')
                    columns_keeped = ['cases']
                    self.return_structured_pandas(ciencia, columns_keeped = columns_keeped)
                elif self.db == 'covid19india': # IND
                    info('COVID19India database selected ...')

                    columns_keeped = ['Deceased', 'Confirmed', 'Recovered', 'Tested',]
                    rename_dict = {i:'tot_'+i for i in columns_keeped}
                    columns_keeped = list(rename_dict.values())
                    rename_dict.update({'Date': 'date', 'State': 'location'})
                    drop_field  = {'State': ['India', 'State Unassigned']}
                    indi = self.csv2pandas("https://api.covid19india.org/csv/latest/states.csv",drop_field=drop_field,rename_columns=rename_dict,separator=',')
                     # Removing 'Other' data, not identified
                    indi['location'] = indi['location'].apply(lambda x: x.replace('Andaman and Nicobar Islands','Andaman and Nicobar'))
                    locationvariant = self.geo.get_subregion_list()['variation_name_subregion'].to_list()
                    locationgeo = self.geo.get_subregion_list()['name_subregion'].to_list()
                    def fusion(pan, new, old):
                        tmp = (pan.loc[pan.location.isin([new, old])].groupby('date').sum())
                        tmp['location'] = old
                        tmp = tmp.reset_index()
                        cols = tmp.columns.tolist()
                        cols = cols[0:1] + cols[-1:] + cols[1:-1]
                        tmp = tmp[cols]
                        pan = pan.loc[~pan.location.isin([new, old])]
                        pan = pan.append(tmp)
                        return pan

                    indi=fusion(indi, 'Telangana', 'Andhra Pradesh')
                    indi=fusion(indi,'Ladakh', 'Jammu and Kashmir')
                    # change name according to json one
                    oldnew = {}
                    for i in indi.location.unique():
                        for k,l in zip(locationgeo,locationvariant):
                            if l.find(i) == 0:
                                oldnew[i] = k
                    indi['location'] = indi['location'].map(oldnew)
                    self.return_structured_pandas(indi,columns_keeped = columns_keeped)
                elif self.db == 'covidtracking':
                    info('USA, CovidTracking.com database selected... ...')
                    rename_dict = {'state': 'location',
                            'death': 'tot_death',
                            'hospitalizedCumulative': 'tot_hosp',
                            'hospitalizedCurrently': 'cur_hosp',
                            'inIcuCumulative': 'tot_icu',
                            'inIcuCurrently': 'cur_icu',
                            'negative': 'tot_neg_test',
                            'positive': 'tot_pos_test',
                            'onVentilatorCumulative': 'tot_onVentilator',
                            'onVentilatorCurrently': 'cur_onVentilator',
                            'totalTestResults':'tot_test',
                            }
                    ctusa = self.csv2pandas("https://covidtracking.com/data/download/all-states-history.csv",
                        rename_columns = rename_dict, separator = ',')
                    columns_keeped = list(rename_dict.values())
                    columns_keeped.remove('location') # is already expected
                    self.return_structured_pandas(ctusa, columns_keeped = columns_keeped)
                elif self.db == 'spf' or self.db == 'spfnational':
                    if self.db == 'spfnational':
                        rename_dict = {
                        'patients_reanimation':'cur_reanimation',
                        'patients_hospitalises':'cur_hospitalises'
                        }
                        columns_keeped = ['total_deces_hopital','cur_reanimation','cur_hospitalises',
                        'total_cas_confirmes','total_patients_gueris',
                        'total_deces_ehpad','total_cas_confirmes_ehpad','total_cas_possibles_ehpad']

                        spfnat = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/d3a98a30-893f-47f7-96c5-2f4bcaaa0d71",
                        rename_columns = rename_dict, separator = ',')
                        colcast=[i for i in columns_keeped]

                        spfnat[colcast]=pd.to_numeric(spfnat[colcast].stack(),errors = 'coerce').unstack()
                        self.return_structured_pandas(spfnat, columns_keeped=columns_keeped) # with 'tot_dc' first
                    else:
                        info('SPF aka Sante Publique France database selected (France departement granularity) ...')
                        info('... Nine different databases from SPF will be parsed ...')
                        # https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
                        # Parse and convert spf data structure to JHU one for historical raison
                        # hosp Number of people currently hospitalized
                        # rea  Number of people currently in resuscitation or critical care
                        # rad      Total amount of patient that returned home
                        # dc       Total amout of deaths at the hospital
                        # 'sexe' == 0 male + female
                        cast = {'dep': 'string'}
                        rename = {'jour': 'date', 'dep': 'location'}
                        cast.update({'HospConv':'string','SSR_USLD':'string','autres':'string'})
                        constraints = {'sexe': 0}
                        spf1 = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7",
                                      rename_columns = rename, constraints = constraints, cast = cast)
                        # https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
                        # All data are incidence. → integrated later in the code
                        # incid_hosp	string 	Nombre quotidien de personnes nouvellement hospitalisées
                        # incid_rea	integer	Nombre quotidien de nouvelles admissions en réanimation
                        # incid_dc	integer	Nombre quotidien de personnes nouvellement décédées
                        # incid_rad	integer	Nombre quotidien de nouveaux retours à domicile
                        spf2 = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c",
                                      rename_columns = rename, cast = cast)
                        # https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-resultats-des-tests-virologiques-covid-19/
                        # T       Number of tests performed daily → integrated later
                        # P       Number of positive tests daily → integrated later
                        constraints = {'cl_age90': 0}
                        spf3 = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/406c6a23-e283-4300-9484-54e78c8ae675",
                                      rename_columns = rename, constraints = constraints, cast = cast)
                        # https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-personnes-vaccinees-contre-la-covid-19-1
                        # Les données issues du système d’information Vaccin Covid permettent de dénombrer en temps quasi réel
                        # (J-1), le nombre de personnes ayant reçu une injection de vaccin anti-covid en tenant compte du nombre
                        # de doses reçues, de l’âge, du sexe ainsi que du niveau géographique (national, régional et
                        # départemental).
                        constraints = {'vaccin': 0} # 0 means all vaccines
                        # previously : https://www.data.gouv.fr/fr/datasets/r/4f39ec91-80d7-4602-befb-4b522804c0af
                        spf5 = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/535f8686-d75d-43d9-94b3-da8cdf850634",
                            rename_columns = rename, constraints = constraints, separator = ';', encoding = "ISO-8859-1", cast = cast)
                        #print(spf5)
                        # https://www.data.gouv.fr/fr/datasets/indicateurs-de-suivi-de-lepidemie-de-covid-19/#_
                        # tension hospitaliere
                        #'date', 'location', 'region', 'libelle_reg', 'libelle_dep', 'tx_incid',
                        # 'R', 'taux_occupation_sae', 'tx_pos', 'tx_incid_couleur', 'R_couleur',
                        # 'taux_occupation_sae_couleur', 'tx_pos_couleur', 'nb_orange',
                        # 'nb_rouge']
                        # Vert : taux d’occupation compris entre 0 et 40% ;
                        # Orange : taux d’occupation compris entre 40 et 60% ;
                        # Rouge : taux d'occupation supérieur à 60%.
                        # R0
                        # vert : R0 entre 0 et 1 ;
                        # Orange : R0 entre 1 et 1,5 ;
                        # Rouge : R0 supérieur à 1,5.
                        cast = {'departement': 'string'}
                        rename = {'extract_date': 'date', 'departement': 'location'}
                        #columns_skipped=['region','libelle_reg','libelle_dep','tx_incid_couleur','R_couleur',\
                        #'taux_occupation_sae_couleur','tx_pos_couleur','nb_orange','nb_rouge']
                        spf4 = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/4acad602-d8b1-4516-bc71-7d5574d5f33e",
                                    rename_columns = rename, separator=',', encoding = "ISO-8859-1", cast=cast)

                        #https://www.data.gouv.fr/fr/datasets/donnees-de-laboratoires-pour-le-depistage-indicateurs-sur-les-variants/
                        #Prc_tests_PCR_TA_crible = % de tests PCR criblés parmi les PCR positives
                        #Prc_susp_501Y_V1 = % de tests avec suspicion de variant 20I/501Y.V1 (UK)
                        #Prc_susp_501Y_V2_3 = % de tests avec suspicion de variant 20H/501Y.V2 (ZA) ou 20J/501Y.V3 (BR)
                        #Prc_susp_IND = % de tests avec une détection de variant mais non identifiable
                        #Prc_susp_ABS = % de tests avec une absence de détection de variant
                        #Royaume-Uni (UK): code Nexstrain= 20I/501Y.V1
                        #Afrique du Sud (ZA) : code Nexstrain= 20H/501Y.V2
                        #Brésil (BR) : code Nexstrain= 20J/501Y.V3

                        cast = {'dep': 'string'}
                        rename = {'dep': 'location'}
                        constraints = {'cl_age90': 0}
                        spf6 =  self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/16f4fd03-797f-4616-bca9-78ff212d06e8",
                                     constraints = constraints,rename_columns = rename, separator=';', cast=cast)

                        constraints = {'age_18ans': 0}
                        spf7 =  self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/c0f59f00-3ab2-4f31-8a05-d317b43e9055",
                                    constraints = constraints, rename_columns = rename, separator=';', cast=cast)
                        #Mutation d'intérêt :
                        #A = E484K
                        #B = E484Q
                        #C = L452R
                        spf8 = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/4d3e5a8b-9649-4c41-86ec-5420eb6b530c",
                        rename_columns = rename, separator=';',cast=cast)
                        #spf8keeped = list(spf8.columns)[2:]
                        rename = {'date_de_passage':'date','dep':'location'}
                        spf9 = self.csv2pandas("https://www.data.gouv.fr/en/datasets/r/eceb9fb4-3ebc-4da3-828d-f5939712600a",
                        rename_columns = rename, separator=';',cast=cast)

                        list_spf=[spf1, spf2, spf3, spf4, spf5, spf6, spf7,spf8,spf9]

                        #for i in list_spf:
                        #    i['date'] = pd.to_datetime(i['date']).apply(lambda x: x if not pd.isnull(x) else '')
                        #    print(i.loc[i.date==d1])
                        #dfs = [df.set_index(['date', 'location']) for df in list_spf]
                        result = reduce(lambda left, right: left.merge(right, how = 'outer', on=['location','date']), list_spf)
                        result = result.loc[~result['location'].isin(['00'])]
                        result = result.sort_values(by=['location','date'])
                        result.loc[result['location'].isin(['975','977','978','986','987']),'location']='980'
                        result = result.drop_duplicates(subset=['location', 'date'], keep='last')

                        for w in ['incid_hosp', 'incid_rea', 'incid_rad', 'incid_dc', 'P', 'T', 'n_cum_dose1', 'n_cum_dose2','n_cum_dose3','n_cum_dose4','n_cum_rappel']:
                            result[w]=pd.to_numeric(result[w], errors = 'coerce')
                            if w.startswith('incid_'):
                                ww = w[6:]
                                result[ww] = result.groupby('location')[ww].fillna(method = 'bfill')
                                result['incid_'+ww] = result.groupby('location')['incid_'+ww].fillna(method = 'bfill')
                                #result['offset_'+w] = result.loc[result.date==min_date][ww]-result.loc[result.date==min_date]['incid_'+ww]
                                #result['offset_'+w] = result.groupby('location')['offset_'+w].fillna(method='ffill')
                            else:
                                pass
                                #result['offset_'+w] = 0
                            if w not in ['n_cum','incid_hosp', 'incid_rea', 'incid_rad', 'incid_dc']:
                                result['tot_'+w]=result.groupby(['location'])[w].cumsum()#+result['offset_'+w]

                        def dontneeeded():
                            for col in result.columns:
                                if col.startswith('Prc'):
                                    result[col] /= 100.
                            for col in result.columns:
                                if col.startswith('ti'):
                                    result[col] /= 7. #par
                            for col in result.columns:
                                if col.startswith('tp'):
                                    result[col] /= 7. #par

                        rename_dict={
                            'dc': 'tot_dc',
                            'hosp': 'cur_hosp',
                            'rad': 'tot_rad',
                            'rea': 'cur_rea',
                            'n_cum_dose1': 'tot_vacc1',
                            'n_cum_dose2': 'tot_vacc2',
                            'n_cum_dose3': 'tot_vacc3',
                            'n_cum_dose4': 'tot_vacc4',
                            'n_cum_rappel':'tot_rappel_vacc',
                            'tx_incid': 'cur_idx_tx_incid',
                            'R': 'cur_idx_R',
                            'taux_occupation_sae': 'cur_idx_taux_occupation_sae',
                            'tx_pos': 'cur_taux_pos',
                            'Prc_tests_PCR_TA_crible':'cur_idx_Prc_tests_PCR_TA_crible',
                            'Prc_susp_501Y_V1':'cur_idx_Prc_susp_501Y_V1',
                            'Prc_susp_501Y_V2_3':'cur_idx_Prc_susp_501Y_V2_3',
                            'Prc_susp_IND':'cur_idx_Prc_susp_IND',
                            'Prc_susp_ABS':'cur_idx_Prc_susp_ABS',
                            'ti':'cur_idx_ti',
                            'tp':'cur_idx_tp',
                            'tx_crib' : 'cur_taux_crib',
                            'tx_A1':'cur_idx_tx_A1',
                            'tx_B1':'cur_idx_tx_B1',
                            'tx_C1':'cur_idx_tx_C1',
                            'nbre_pass_corona':'cur_nbre_pass_corona',
                            }
                        spf8keeped = ['nb_A0','nb_A1', 'nb_B0', 'nb_B1', 'nb_C0', 'nb_C1']
                        rename_dict.update({i:'cur_'+i for i in spf8keeped})
                        result = result.rename(columns=rename_dict)
                        #coltocast=list(rename_dict.values())[:5]
                        #result[coltocast] = result[coltocast].astype('Int64')
                        rename_dict2={i:i.replace('incid_','tot_incid_') for i in ['incid_hosp', 'incid_rea', 'incid_rad', 'incid_dc']}
                        result = result.rename(columns=rename_dict2)
                        columns_keeped  = list(rename_dict.values()) + list(rename_dict2.values()) + ['tot_P', 'tot_T']
                        self.return_structured_pandas(result,columns_keeped=columns_keeped) # with 'tot_dc' first
                elif self.db == 'opencovid19' or  self.db == 'opencovid19national':
                    rename={'maille_code':'location'}
                    cast={'source_url':str,'source_archive':str,'source_type':str,'nouvelles_hospitalisations':str,'nouvelles_reanimations':str}
                    if self.db == 'opencovid19':
                        info('OPENCOVID19 (country granularity) selected ...')
                        drop_field  = {'granularite':['pays','monde','region']}
                        dict_columns_keeped = {
                            'deces':'tot_deces',
                            'cas_confirmes':'tot_cas_confirmes',
                            'reanimation':'cur_reanimation',
                            'hospitalises':'cur_hospitalises',
                            'gueris':'tot_gueris'
                            }
                    else:
                        info('OPENCOVID19 (national granularity) selected ...')
                        drop_field  = {'granularite':['monde','region','departement']}
                        dict_columns_keeped = {
                        'deces':'tot_deces',
                        'cas_confirmes':'tot_cas_confirmes',
                        'cas_ehpad':'tot_cas_ehpad',
                        'cas_confirmes_ehpad':'tot_cas_confirmes_ehpad',
                        'cas_possibles_ehpad':'tot_cas_possibles_ehpad',
                        'deces_ehpad':'tot_deces_ehpad',
                        'reanimation':'cur_reanimation',
                        'hospitalises':'cur_hospitalises',
                        'gueris':'tot_gueris'
                        }
                    opencovid19 = self.csv2pandas('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv',
                                drop_field=drop_field,rename_columns=rename,separator=',',cast=cast)

                    opencovid19['location'] = opencovid19['location'].apply(lambda x: x.replace('COM-','').replace('DEP-','').replace('FRA','France'))
                    # integrating needed fields
                    if self.db == 'opencovid19national':
                        opencovid19 = opencovid19.loc[~opencovid19.granularite.isin(['collectivite-outremer'])]

                    column_to_integrate=['nouvelles_hospitalisations', 'nouvelles_reanimations']
                    opencovid19[column_to_integrate]=pd.to_numeric(opencovid19[column_to_integrate].stack(),errors = 'coerce').unstack()

                    for w in ['nouvelles_hospitalisations', 'nouvelles_reanimations']:
                        opencovid19['tot_'+w]=opencovid19.groupby(['location'])[w].cumsum()
                    #columns_skipped = ['granularite','maille_nom','source_nom','source_url','source_archive','source_type']
                    self.return_structured_pandas(opencovid19.rename(columns=dict_columns_keeped),columns_keeped=list(dict_columns_keeped.values())+['tot_'+c for c in column_to_integrate])
                elif self.db == 'owid':
                    variant = True
                    info('OWID aka \"Our World in Data\" database selected ...')
                    drop_field = {'location':['International']}#, 'World']}
                    owid = self.csv2pandas("https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
                    separator=',',drop_field=drop_field)
                    # renaming some columns
                    col_to_rename1=['reproduction_rate','icu_patients','hosp_patients','weekly_hosp_admissions','positive_rate']
                    renamed_cols1=['cur_'+c if c != 'positive_rate' else 'cur_idx_'+c for c in col_to_rename1]
                    col_to_rename2=['people_vaccinated','people_fully_vaccinated','people_fully_vaccinated_per_hundred',\
                    'people_vaccinated_per_hundred','population','gdp_per_capita']
                    renamed_cols2=['total_'+i for i in col_to_rename2]
                    col_to_rename = col_to_rename1+col_to_rename2
                    renamed_cols = renamed_cols1 +renamed_cols2
                    columns_keeped=['iso_code','total_deaths','total_cases','total_vaccinations','total_tests']
                    columns_keeped+=['total_cases_per_million','total_deaths_per_million','total_vaccinations_per_hundred','total_boosters']
                    #owid['total_tests_with_new_tests'] = owid.groupby(['location'])['new_tests'].cumsum()
                    uniq=list(owid.location.unique())
                    mask = (owid.loc[owid.location.isin(uniq)]['total_tests'].isnull() &\
                                                owid.loc[owid.location.isin(uniq)]['new_tests'].isnull())
                    #sometimes is new_tests sometimes total_tests
                    owid_test         = owid[~mask]
                    owid_new_test     = owid_test[owid_test['total_tests'].isnull()]
                    owid_total_test   = owid_test[~owid_test['total_tests'].isnull()]
                    owid_new_test     = owid_new_test.drop(columns='total_tests')

                    owid_new_test.loc[:,'total_tests'] = owid_new_test.groupby(['location'])['new_tests'].cumsum()
                    owid = pd.concat([owid[mask],owid_new_test,owid_total_test])
                    self.return_structured_pandas(owid.rename(columns=dict(zip(col_to_rename,renamed_cols))),columns_keeped=columns_keeped+renamed_cols)
                elif self.db == 'risklayer':
                    info('EUR, Who Europe from RiskLayer ...')
                    rename_dict = {'UID': 'location',
                        'CumulativePositive': 'tot_positive',
                        'IncidenceCumulative': 'tot_incidence',
                        'DateRpt':'date'}
                    deur = self.csv2pandas("https://docs.google.com/spreadsheets/d/e/2PACX-1vQ-JLawOH35vPyOk39w0tjn64YQLlahiD2AaNfjd82pgQ37Jr1K8KMHOqJbxoi4k2FZVYBGbZ-nsxhi/pub?output=csv",
                        rename_columns = rename_dict, separator = ',')
                    columns_keeped = list(rename_dict.values())
                    columns_keeped.remove('location') # is already expected
                    columns_keeped.remove('date') # is already expected
                    self.return_structured_pandas(deur, columns_keeped = columns_keeped)
                elif self.db == 'insee':
                    info('FRA, INSEE global deaths statistics...')
                    url = "https://www.data.gouv.fr/fr/datasets/fichier-des-personnes-decedees/"
                    with open(get_local_from_url(url,86400*7)) as fp: # update each week
                        soup = BeautifulSoup(fp,features="lxml")
                    ld_json=soup.find('script', {'type':'application/ld+json'}).contents
                    data=json.loads(ld_json[0])
                    deces_url={}
                    for d in data['distribution']:
                        deces_url.update({d['name']:d['url']})
                    dc={}
                    for i in ['2021','2020','2019','2018','2017']:# ['2000','2001','2002','2003','2004','2005','2020-t1','2020-t2','2020-t3','2019','2018']:
                        with open(get_local_from_url(deces_url['deces-'+i+'.txt'],86400*30)) as f:
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
                            data.append([first_name,last_name,sex,birthdate,birthlocationcode,birthlocationname,deathdate,deathlocationcode,deathlocationshortcode,deathid,deathdatebis,1])
                        p=pd.DataFrame(data)
                        p.columns=['first_name','last_name','sex','birth_date','birth_location_code','birth_location_name','death_date','death_location_code','location','death_id','death_date_bis','i']
                        p["age"]=[k.days/365 for k in p["death_date"]-p["birth_date"]]
                        p["age_class"]=[math.floor(k/20) for k in p["age"]]

                        p=p[['location','death_date']].reset_index(drop=True)
                        p['death_date']=pd.to_datetime(p['death_date']).dt.date
                        p['location']=p['location'].astype(str)
                        insee_pd=insee_pd.append(p)
                        #pdict.update({i:p})
                    insee_pd['daily_number_of_deaths'] = insee_pd.groupby(['death_date','location'])['death_date'].transform('count')
                    #p=pd.DataFrame()

                    #p=p[p.death_date>=fromisoformat('2019-01-01')]
                    #for k in pdict.keys():
                    #    p=p.append(pdict[k].groupby(['death_date','location']).sum())
                    #p['daily_number_of_deaths']=p.i
                    #p=p.reset_index()
                    #p['date']=p.death_date
                    #p=p[p.death_date>=datetime.date.fromisoformat('2019-01-01')]
                    since_date='2018-01-01'
                    insee_pd = insee_pd[insee_pd.death_date>=datetime.date.fromisoformat(since_date)]
                    insee_pd =  insee_pd.rename(columns={'death_date':'date'})
                    insee_pd.sort_values(by=['date', 'location'],inplace=True)
                    insee_pd['deaths_since_'+since_date]=insee_pd.groupby(['location'])['daily_number_of_deaths'].cumsum()
                    #display(insee_pd)
                    self.return_structured_pandas(insee_pd,columns_keeped=['deaths_since_'+since_date])
            except:
                raise CoaDbError("An error occured while parsing data of "+self.get_db()+". This may be due to a data format modification. "
                    "You may contact support@pycoa.fr. Thanks.")
            # some info
            info('Few information concernant the selected database : ', self.get_db())
            info('Available key-words, which ∈',self.get_available_keys_words())
            info('Example of location : ',  ', '.join(random.choices(self.get_locations(), k=min(5,len(self.get_locations() ))   )), ' ...')
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

   def get_available_options(self):
        '''
        Return available options for the get_stats method
        '''
        o=self.available_options
        return o

   def get_available_keys_words(self):
        '''
        Return all the available keyswords for the database selected
        Key-words are for:
        - jhu : ['deaths','confirmed','recovered']
                            * the data are cumulative i.e for a date it represents the total cases
            For more information please have a look to https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data
        - 'owid' : ['total_deaths','total_cases','reproduction_rate','icu_patients','hosp_patients','total_tests',
                    'positive_rate','total_vaccinations']
        For more information please have a look to https://github.com/owid/covid-19-data/tree/master/public/data/
        - 'spf' : ['hosp', 'rea', 'rad', 'dc', 'incid_hosp', 'incid_rea', 'incid_dc',
                    'incid_rad', 'P', 'T', 'tx_incid', 'R', 'taux_occupation_sae', 'tx_pos']
            No translation have been done for french keywords data
        For more information please have a look to  https://www.data.gouv.fr/fr/organizations/sante-publique-france/
        - 'opencovid19' :['cas_confirmes', 'deces',
        'reanimation', 'hospitalises','nouvelles_hospitalisations', 'nouvelles_reanimations', 'gueris', 'depistes']
        - 'opencovid19national' :['cas_confirmes', 'cas_ehpad', 'cas_confirmes_ehpad', 'cas_possibles_ehpad', 'deces', 'deces_ehpad',
        'reanimation', 'hospitalises','nouvelles_hospitalisations', 'nouvelles_reanimations', 'gueris', 'depistes']

        No translation have been done for french keywords data
        For more information please have a look to https://github.com/opencovid19-fr
        '''
        return self.available_keys_words

   def get_keyword_definition(self,keys):
       '''
            Return definition on the selected keword
       '''
       value = self.databaseinfo.generic_info(self.get_db(),keys)[0]
       return value

   def get_keyword_url(self,keys):
       '''
        Return url where the keyword have been parsed
       '''
       value = self.databaseinfo.generic_info(self.get_db(),keys)[1]
       master  = self.databaseinfo.generic_info(self.get_db(),keys)[2]
       return value, master


   def return_jhu_pandas(self):
        ''' For center for Systems Science and Engineering (CSSE) at Johns Hopkins University
            COVID-19 Data Repository by the see homepage: https://github.com/CSSEGISandData/COVID-19
            return a structure : pandas location - date - keywords
            for jhu location are countries (location uses geo standard)
            for jhu-usa location are Province_State (location uses geo standard)
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

        self.available_keys_words = []
        if self.db == 'rki':
                self.available_keys_words = ['tot_deaths','tot_cases']
        pandas_list = []
        for ext in jhu_files_ext:
            fileName = base_name + ext + extension
            url = base_url + fileName
            self.database_url.append(url)
            pandas_jhu_db = pandas.read_csv(get_local_from_url(url,7200), sep = ',') # cached for 2 hours
            if self.db == 'jhu':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Country/Region':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['Province/State','Lat','Long'])
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location"],var_name="date",value_name=ext)
                pandas_jhu_db = pandas_jhu_db.loc[~pandas_jhu_db.location.isin(['Diamond Princess'])]
            elif self.db == 'jhu-usa':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Province_State':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['UID','iso2','iso3','code3','FIPS',
                                    'Admin2','Country_Region','Lat','Long_','Combined_Key'])
                if 'Population' in pandas_jhu_db.columns:
                    pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location",'Population'],var_name="date",value_name=ext)
                else:
                    pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location"],var_name="date",value_name=ext)
                removethose=['American Samoa','Diamond Princess','Grand Princess','Guam',
                'Northern Mariana Islands','Puerto Rico','Virgin Islands']
                pandas_jhu_db = pandas_jhu_db.loc[~pandas_jhu_db.location.isin(removethose)]
            elif self.db == 'rki':
                pandas_jhu_db = pandas_jhu_db.drop(columns=['sum_'+ext])
                pandas_jhu_db = pandas_jhu_db.set_index('time_iso8601').T.reset_index().rename(columns={'index':'location'})
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location"],var_name="date",value_name=ext)
                pandas_jhu_db['location'] = pandas_jhu_db.location.astype(str)
                pandas_jhu_db = pandas_jhu_db.rename(columns={'deaths':'tot_deaths','cases':'tot_cases'})
            elif self.db == 'imed':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'county_normalized':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['Γεωγραφικό Διαμέρισμα','Περιφέρεια','county','pop_11'])
                ext='tot_'+ext
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location"],var_name="date",value_name=ext)
                self.available_keys_words += [ext]
            else:
                raise CoaTypeError('jhu nor jhu-usa database selected ... ')

            pandas_jhu_db=pandas_jhu_db.groupby(['location','date']).sum().reset_index()
            pandas_list.append(pandas_jhu_db)

        if 'jhu' in self.db:
            pandas_list = [pan.rename(columns={i:'tot_'+i for i in jhu_files_ext}) for pan in pandas_list]
            self.available_keys_words = ['tot_'+i for i in jhu_files_ext]
        uniqloc = list(pandas_list[0]['location'].unique())
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


        result = reduce(lambda x, y: pd.merge(x, y, on = ['location','date']), pandas_list)

        if location_is_code:
            result['codelocation'] = result['location']
            result['location'] = result['location'].map(codename)
        else:
            if self.db == 'jhu':
                result['location'] = result['location'].map(d_loc_s)
            result['codelocation'] = result['location'].map(codename)
        result = result.loc[result.location.isin(self.slocation)]

        tmp = pd.DataFrame()
        if 'Kosovo' in uniqloc:
            #Kosovo is Serbia ! with geo.to_standard
            tmp=(result.loc[result.location.isin(['Serbia'])]).groupby('date').sum().reset_index()
            tmp['location'] = 'Serbia'
            tmp['codelocation'] = 'SRB'
            kw = [i for i in self.available_keys_words]
            colpos=['location', 'date'] + kw + ['codelocation']
            tmp = tmp[colpos]
            result = result.loc[~result.location.isin(['Serbia'])]
            result = result.append(tmp)

        result['date'] = pd.to_datetime(result['date'],errors='coerce').dt.date
        result = result.sort_values(by=['location','date'])
        result = result.reset_index(drop=True)
        self.mainpandas = fill_missing_dates(result)
        self.dates  = self.mainpandas['date']

   def csv2pandas(self,url,**kwargs):
        '''
        Parse and convert the database cvs file to a pandas structure
        '''
        self.database_url.append(url)
        kwargs_test(kwargs,['cast','separator','encoding','constraints','rename_columns','drop_field','quotechar'],
            'Bad args used in the csv2pandas() function.')

        cast = kwargs.get('cast', None)
        dico_cast = {}
        if cast:
            for key,val in cast.items():
                dico_cast[key] = val
        separator = kwargs.get('separator', ';')
        if separator:
            separator = separator
        encoding = kwargs.get('encoding', None)
        if encoding:
            encoding = encoding
        quoting=0
        if self.db == 'obepine':
              quoting=3
        pandas_db = pandas.read_csv(get_local_from_url(url,7200),sep=separator,dtype=dico_cast, encoding = encoding,
            keep_default_na=False,na_values='',header=0,quoting=quoting) # cached for 2 hours

        #pandas_db = pandas.read_csv(self.database_url,sep=separator,dtype=dico_cast, encoding = encoding )
        constraints = kwargs.get('constraints', None)
        rename_columns = kwargs.get('rename_columns', None)
        drop_field = kwargs.get('drop_field', None)
        if self.db == 'obepine':
            pandas_db = pandas_db.rename(columns=rename_columns)
            pandas_db = pandas_db.applymap(lambda x: x.replace('"', ''))
        if constraints:
            for key,val in constraints.items():
                pandas_db = pandas_db.loc[pandas_db[key] == val]
                pandas_db = pandas_db.drop(columns=key)
        if drop_field:
            for key,val in drop_field.items():
                for i in val:
                    pandas_db =  pandas_db[pandas_db[key] != i ]
        if rename_columns:
            for key,val in rename_columns.items():
                pandas_db = pandas_db.rename(columns={key:val})
        if 'semaine' in  pandas_db.columns:
            pandas_db['semaine'] = [ week_to_date(i) for i in pandas_db['semaine']]
            #pandas_db = pandas_db.drop_duplicates(subset=['semaine'])
            pandas_db = pandas_db.rename(columns={'semaine':'date'})
        pandas_db['date'] = pandas.to_datetime(pandas_db['date'],errors='coerce').dt.date
        #self.dates  = pandas_db['date']
        if self.database_type[self.db][1] == 'nation' and  self.database_type[self.db][0] in ['FRA','CYP']:
            pandas_db['location'] = self.database_type[self.db][2]
        pandas_db = pandas_db.sort_values(['location','date'])
        return pandas_db

   def return_structured_pandas(self,mypandas,**kwargs):
        '''
        Return the mainpandas core of the PyCoA structure
        '''
        kwargs_test(kwargs,['columns_skipped','columns_keeped'],
            'Bad args used in the return_structured_pandas function.')
        columns_skipped = kwargs.get('columns_skipped', None)
        absolutlyneeded = ['date','location']
        defaultkeept = list(set(mypandas.columns.to_list()) - set(absolutlyneeded))
        columns_keeped  = kwargs.get('columns_keeped', defaultkeept)
        if columns_skipped:
            columns_keeped = [x for x in mypandas.columns.values.tolist() if x not in columns_skipped + absolutlyneeded]
        mypandas = mypandas[absolutlyneeded + columns_keeped]

        self.available_keys_words = columns_keeped #+ absolutlyneeded
        not_un_nation_dict={'Kosovo':'Serbia'}
        for subpart_country, main_country in not_un_nation_dict.items() :
            tmp=(mypandas.loc[mypandas.location.isin([subpart_country,main_country])].groupby('date').sum())
            tmp['location']=main_country
            mypandas = mypandas.loc[~mypandas.location.isin([subpart_country,main_country])]
            tmp = tmp.reset_index()
            cols = tmp.columns.tolist()
            cols = cols[0:1] + cols[-1:] + cols[1:-1]
            tmp = tmp[cols]
            mypandas = mypandas.append(tmp)
        if 'iso_code' in mypandas.columns:
            mypandas['iso_code'] = mypandas['iso_code'].dropna().astype(str)
            mypandasori=mypandas.copy()
            strangeiso3tokick = [i for i in mypandasori['iso_code'].dropna().unique() if not len(i)==3 ]
            mypandasori = mypandas.loc[~mypandas.iso_code.isin(strangeiso3tokick)]
            self.available_keys_words.remove('iso_code')
            mypandasori = mypandasori.drop(columns=['location'])
            mypandasori = mypandasori.rename(columns={'iso_code':'location'})
            if self.db == 'owid':
                onlyowid = mypandas.loc[mypandas.iso_code.isin(strangeiso3tokick)]
                onlyowid = onlyowid.copy()
                onlyowid.loc[:,'location'] = onlyowid['location'].apply(lambda x : 'owid_'+x)
            mypandas = mypandasori

        if self.db == 'dpc':
            gd = self.geo.get_data()[['name_region','code_region']]
            A=['P.A. Bolzano','P.A. Trento']
            tmp=mypandas.loc[mypandas.location.isin(A)].groupby('date').sum()
            tmp['location']='Trentino-Alto Adige'
            mypandas = mypandas.loc[~mypandas.location.isin(A)]
            tmp = tmp.reset_index()
            mypandas = mypandas.append(tmp)
            uniqloc = list(mypandas['location'].unique())
            sub2reg = dict(gd.values)
            #collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_region.isin(uniqloc)]['code_region'])))
            mypandas['codelocation'] = mypandas['location'].map(sub2reg)
        if self.db == 'dgs':
            gd = self.geo.get_data()[['name_region','name_region']]
            mypandas = mypandas.reset_index(drop=True)
            mypandas['location'] = mypandas['location'].apply(lambda x: x.title().replace('Do', 'do').replace('Da','da').replace('De','de'))
            uniqloc = list(mypandas['location'].unique())
            sub2reg = dict(gd.values)
            #sub2reg = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_subregion.isin(uniqloc)]['name_region'])))
            mypandas['location'] = mypandas['location'].map(sub2reg)
            mypandas = mypandas.loc[~mypandas.location.isnull()]

         # filling subregions.
            gd = self.geo.get_data()[['code_region','name_region']]
            uniqloc = list(mypandas['location'].unique())
            name2code = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_region.isin(uniqloc)]['code_region'])))
            mypandas = mypandas.loc[~mypandas.location.isnull()]

        codename = None
        location_is_code = False
        uniqloc = list(mypandas['location'].unique()) # if possible location from csv are codelocation

        if self.db_world:
            uniqloc = [s for s in uniqloc if 'OWID_' not in s]
            db=self.get_db()
            if self.db == 'govcy':
                db=None
            codename = collections.OrderedDict(zip(uniqloc,self.geo.to_standard(uniqloc,output='list',db=db,interpret_region=True)))
            self.slocation = list(codename.values())
            location_is_code = True
        else:
            if self.database_type[self.db][1] == 'region' :
                if self.db == 'covid19india':
                    mypandas = mypandas.loc[~mypandas.location.isnull()]
                    uniqloc = list(mypandas['location'].unique())
                temp = self.geo.get_region_list()[['name_region','code_region']]
                #codename = collections.OrderedDict(zip(uniqloc,list(temp.loc[temp.name_region.isin(uniqloc)]['code_region'])))
                codename=dict(temp.values)
                self.slocation = uniqloc
                if self.db == 'obepine':
                    codename = {v:k for k,v in codename.items()}
                    location_is_code = True

            elif self.database_type[self.db][1] == 'subregion':
                temp = self.geo_all[['code_subregion','name_subregion']]
                codename=dict(temp.loc[temp.code_subregion.isin(uniqloc)].values)
                if self.db in ['phe','covidtracking','spf','escovid19data','opencovid19','minciencia','moh','risklayer','insee']:
                    #codename={i:list(temp.loc[temp.code_subregion.isin([i])]['name_subregion'])[0] for i in uniqloc if not temp.loc[temp.code_subregion.isin([i])]['name_subregion'].empty }
                    #codename = collections.OrderedDict(zip(uniqloc,list(temp.loc[temp.code_subregion.isin(uniqloc)]['name_subregion'])))
                    self.slocation = list(codename.values())
                    location_is_code = True
                else:
                    #codename=dict(temp.loc[temp.code_subregion.isin(uniqloc)][['code_subregion','name_subregion']].values)
                    #codename={i:list(temp.loc[temp.code_subregion.isin([i])]['code_subregion'])[0] for i in uniqloc if not temp.loc[temp.code_subregion.isin([i])]['code_subregion'].empty }
                    #codename = collections.OrderedDict(zip(uniqloc,list(temp.loc[temp.name_subregion.isin(uniqloc)]['code_subregion'])))
                    #print(codename)
                    self.slocation = uniqloc
            else:
                CoaDbError('Granularity problem , neither region nor sub_region ...')

        if self.db == 'dgs':
            mypandas = mypandas.reset_index(drop=True)

        if self.db != 'spfnational':
            mypandas = mypandas.groupby(['location','date']).sum(min_count=1).reset_index() # summing in case of multiple dates (e.g. in opencovid19 data). But keep nan if any

        if self.db == 'govcy':
            location_is_code=False

        mypandas = fill_missing_dates(mypandas)

        if location_is_code:
            if self.db != 'dgs':
                mypandas['codelocation'] =  mypandas['location'].astype(str)
            mypandas['location'] = mypandas['location'].map(codename)
            if self.db == 'obepine':
                mypandas = mypandas.dropna(subset=['location'])
                self.slocation = list(mypandas.codelocation.unique())
            mypandas = mypandas.loc[~mypandas.location.isnull()]
        else:
            mypandas['codelocation'] =  mypandas['location'].map(codename).astype(str)
        if self.db == 'owid':
            onlyowid['codelocation'] = onlyowid['location']
            mypandas = mypandas.append(onlyowid)
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
            * selected_col: column to keep according to get_available_keys_words (None : all get_available_keys_words)
                            N.B. location column is added
        '''
       kwargs_test(kwargs,['location', 'date', 'selected_col'],
                    'Bad args used in the get_stats() function.')

       location = kwargs.get('location', None)
       selected_col = kwargs.get('selected_col', None)
       watch_date = kwargs.get('date', None)
       if location:
            if not isinstance(location, list):
                clist = ([location]).copy()
            else:
                clist = (location).copy()
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
            filtered_pandas = filtered_pandas.loc[filtered_pandas.location.isin(clist)]
            if watch_date:
                check_valid_date(watch_date)
                mydate = pd.to_datetime(watch_date).date()
            else :
                mydate = filtered_pandas.date.max()
            filtered_pandas = filtered_pandas.loc[filtered_pandas.date==mydate].reset_index(drop=True)
            if selected_col:
                l = selected_col
            else:
                l=list(self.get_available_keys_words())
            l.insert(0, 'location')
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

   def get_stats(self, **kwargs):
        '''
        Return the pandas pandas_datase
         - index: only an incremental value
         - location: list of location used in the database selected (using geo standardization)
         - 'which' :  return the keyword values selected from the avalailable keywords keepted seems
            self.get_available_keys_words()

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
        kwargs_test(kwargs,['location','which','option'],
            'Bad args used in the get_stats() function.')
        wallname = None
        if not 'location' in kwargs or kwargs['location'] is None.__class__ or kwargs['location'] == None:
            if get_db_list_dict()[self.db][0] == 'WW':
                kwargs['location'] = 'world'
            else:
                kwargs['location'] = self.slocation #self.geo_all['code_subregion'].to_list()
            wallname = get_db_list_dict()[self.db][2]
        else:
            kwargs['location'] = kwargs['location']

        option = kwargs.get('option', 'fillnan')
        fillnan = True # default
        sumall = False # default
        sumallandsmooth7 = False
        if kwargs['which'] not in self.get_available_keys_words():
            raise CoaKeyError(kwargs['which']+' is not a available for ' + self.db + ' database name. '
            'See get_available_keys_words() for the full list.')

        #while for last date all values are nan previous date
        mainpandas = self.return_nonan_dates_pandas(self.get_mainpandas(),kwargs['which'])
        devorigclist = None
        origclistlist = None
        origlistlistloc = None
        if option and 'sumall' in option:
            if not isinstance(kwargs['location'], list):
                kwargs['location'] = [[kwargs['location']]]
            else:
                if isinstance(kwargs['location'][0], list):
                    kwargs['location'] = kwargs['location']
                else:
                    kwargs['location'] = [kwargs['location']]
        if not isinstance(kwargs['location'], list):
            listloc = ([kwargs['location']]).copy()
            if not all(isinstance(c, str) for c in listloc):
                raise CoaWhereError("Location via the where keyword should be given as strings. ")
            origclist = listloc
        else:
            listloc = (kwargs['location']).copy()
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
                dicooriglist={','.join(i):explosion(i,self.database_type[self.db][1]) for i in origlistlistloc}
                #origlistlistloc = DataBase.flat_list(list(dicooriglist.values()))
                #location_exploded = origlistlistloc
            else:
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
                tmp = tmp.loc[tmp.location.isin(v)]
                code = tmp.codelocation.unique()
                tmp['clustername'] = [k]*len(tmp)
                if pdcluster.empty:
                    pdcluster = tmp
                else:
                    pdcluster = pdcluster.append(tmp)
                j+=1
            pdfiltered = pdcluster[['location','date','codelocation',kwargs['which'],'clustername']]
        else:
            pdfiltered = mainpandas.loc[mainpandas.location.isin(location_exploded)]
            pdfiltered = pdfiltered[['location','date','codelocation',kwargs['which']]]
            pdfiltered['clustername'] = pdfiltered['location'].copy()
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
                    location = list(sub.location.unique())
                    for loca in location:
                        pdloc = sub.loc[sub.location == loca][kwargs['which']]
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
                        reconstructed=reconstructed.append(sub)
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
                pdfiltered.groupby(['location','clustername'])[kwargs['which']].apply(lambda x: x.bfill())
                #if kwargs['which'].startswith('total_') or kwargs['which'].startswith('tot_'):
                #    pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].apply(lambda x: x.ffill())
                if pdfiltered.loc[pdfiltered.date == pdfiltered.date.max()][kwargs['which']].isnull().values.any():
                    print(kwargs['which'], "has been selected. Some missing data has been interpolated from previous data.")
                    print("This warning appear right now due to some missing values at the latest date ", pdfiltered.date.max(),".")
                    print("Use the option='nofillnan' if you want to only display the original data")
                    pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['location','clustername'])[kwargs['which']].apply(lambda x: x.ffill())
                    pdfiltered = pdfiltered[pdfiltered[kwargs['which']].notna()]
            elif o == 'smooth7':
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['location'])[kwargs['which']].rolling(7,min_periods=7).mean().reset_index(level=0,drop=True)
                inx7=pdfiltered.groupby('location').head(7).index
                pdfiltered.loc[inx7, kwargs['which']] = pdfiltered[kwargs['which']].fillna(method="bfill")
                fillnan=True
            elif o == 'sumall':
                sumall = True
            elif o == 'sumallandsmooth7':
                sumall = True
                sumallandsmooth7 = True
            elif o != None and o != '' and o != 'sumallandsmooth7':
                raise CoaKeyError('The option '+o+' is not recognized in get_stats. See get_available_options() for list.')
        pdfiltered = pdfiltered.reset_index(drop=True)

        # if sumall set, return only integrate val
        tmppandas=pd.DataFrame()
        if sumall:
            if origlistlistloc != None:
               uniqcluster = pdfiltered.clustername.unique()
               if kwargs['which'].startswith('cur_idx_'):
                  tmp = pdfiltered.groupby(['clustername','date']).mean().reset_index()
               else:
                  tmp = pdfiltered.groupby(['clustername','date']).sum().reset_index()#.loc[pdfiltered.clustername.isin(uniqcluster)].\

               codescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['codelocation'].unique()) for i in uniqcluster}
               namescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['location'].unique()) for i in uniqcluster}
               tmp['codelocation'] = tmp['clustername'].map(codescluster)
               tmp['location'] = tmp['clustername'].map(namescluster)

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
                uniqloc = list(pdfiltered.location.unique())
                uniqcodeloc = list(pdfiltered.codelocation.unique())
                tmp.loc[:,'location'] = ['dummy']*len(tmp)
                tmp.loc[:,'codelocation'] = ['dummy']*len(tmp)
                tmp.loc[:,'clustername'] = ['dummy']*len(tmp)
                for i in range(len(tmp)):
                    tmp.at[i,'location'] = uniqloc #sticky(uniqloc)
                    tmp.at[i,'codelocation'] = uniqcodeloc #sticky(uniqcodeloc)
                    tmp.at[i,'clustername'] =  sticky(uniqloc)[0]
                pdfiltered = tmp
        else:
            if self.db_world :
                pdfiltered['clustername'] = pdfiltered['location'].apply(lambda x: self.geo.to_standard(x)[0] if not x.startswith("owid_") else x)
            else:
                pdfiltered['clustername'] = pdfiltered['location']

        if 'cur_' in kwargs['which'] or 'total_' in kwargs['which'] or 'tot_' in kwargs['which']:
            pdfiltered['cumul'] = pdfiltered[kwargs['which']]
        else:
            pdfiltered['cumul'] = pdfiltered_nofillnan.groupby('clustername')[kwargs['which']].cumsum()
            if fillnan:
                pdfiltered.loc[:,'cumul'] =\
                pdfiltered.groupby('clustername')['cumul'].apply(lambda x: x.ffill())

        pdfiltered['daily'] = pdfiltered.groupby('clustername')['cumul'].diff()
        inx = pdfiltered.groupby('clustername').head(1).index
        pdfiltered['weekly'] = pdfiltered.groupby('clustername')['cumul'].diff(7)
        inx7=pdfiltered.groupby('clustername').head(7).index
        #First value of diff is always NaN
        pdfiltered.loc[inx, 'daily'] = pdfiltered['daily'].fillna(method="bfill")
        pdfiltered.loc[inx7, 'weekly'] = pdfiltered['weekly'].fillna(method="bfill")

        unifiedposition=['location', 'date', kwargs['which'], 'daily', 'cumul', 'weekly', 'codelocation','clustername']
        pdfiltered = pdfiltered[unifiedposition]

        if wallname != None and sumall == True:
               pdfiltered.loc[:,'clustername'] = wallname

        pdfiltered = pdfiltered.drop(columns='cumul')
        verb("Here the information I\'ve got on ", kwargs['which']," : ", self.get_keyword_definition(kwargs['which']))
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
            [ p.drop([i],axis=1, inplace=True) for i in ['location','where','codelocation'] if i in p.columns ]
            #p.drop(['location','codelocation'],axis=1, inplace=True)
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
      #m['clustername']=m.m('location')['clustername'].fillna(method='bfill')
      #m['codelocation']=m.groupby('location')['codelocation'].fillna(method='bfill')
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
