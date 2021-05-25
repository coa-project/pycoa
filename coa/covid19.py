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
        self.geoinfo = report
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
                elif self.db == 'dpc': #ITA
                    info('ITA, Dipartimento della Protezione Civile database selected ...')
                    rename_dict = {'data': 'date', 'denominazione_regione': 'location', 'totale_casi': 'tot_cases','deceduti':'tot_deaths'}
                    dpc1 = self.csv2pandas('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv',\
                    rename_columns = rename_dict, separator=',')
                    #dpc1 = self.csv2pandas("https://github.com/pcm-dpc/COVID-19/raw/master/dati-province/dpc-covid19-ita-province.csv",\
                    columns_keeped = ['tot_cases','tot_deaths']
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
                    url='https://www.data.gouv.fr/es/datasets/r/ba71be57-5932-4298-81ea-aff3a12a440c'
                    rename_dict={'Code_Region':'location','Date':'date','Indicateur':'idx_obepine'}
                    obepine_data=self.csv2pandas(url,separator=';',rename_columns=rename_dict)
                    obepine_data['location']=obepine_data.location.astype(str)
                    self.return_structured_pandas(obepine_data,columns_keeped=['idx_obepine'])
                elif self.db == 'escovid19data': # ESP
                    info('ESP, EsCovid19Data ...')
                    rename_dict = {'ine_code': 'location',\
                        'deceased':'tot_deaths',\
                        'cases_accumulated':'tot_cases',\
                        'activos':'cur_cases',\
                        'hospitalized':'cur_hosp',\
                        'hospitalized_accumulated':'tot_hosp',\
                        'intensive_care':'cur_icu',\
                        'recovered':'tot_recovered',\
                        'cases_per_cienmil':'cur_cases_per100k',\
                        'intensive_care_per_1000000':'cur_icu_per1M',\
                        'deceassed_per_100000':'tot_deaths_per100k',\
                        'hospitalized_per_100000':'cur_hosp_per100k',\
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
                    'TOTAL_IN':'tot_hosp',
                    'TOTAL_IN_ICU':'tot_icu',
                    'TOTAL_IN_RESP':'tot_resp',
                    'TOTAL_IN_ECMO':'tot_ecmo'}
                    url='https://epistat.sciensano.be/Data/COVID19BE_HOSP.csv'
                    beldata=self.csv2pandas(url,separator=',',rename_columns=rename_dict)
                    columns_keeped = ['tot_hosp','tot_icu','tot_resp','tot_ecmo']
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
                elif self.db == 'phe': # GBR from https://coronavirus.data.gov.uk/details/download
                    info('GBR, Public Health England data ...')
                    rename_dict = { 'areaCode':'location',\
                        'cumDeathsByDeathDate':'tot_deaths',\
                        'cumCasesBySpecimenDate':'tot_cases',\
                        #'covidOccupiedMVBeds':'cur_icu',\
                        #'cumPeopleVaccinatedFirstDoseByVaccinationDate':'tot_dose1',\
                        #'cumPeopleVaccinatedSecondDoseByVaccinationDate':'tot_dose2',\
                        #'hospitalCases':'cur_hosp',\
                        }
                    url='https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla'
                    for w in rename_dict.keys():
                        if w not in ['areaCode']:
                            url=url+'&metric='+w
                    url=url+'&format=csv'

                    gbr_data=self.csv2pandas(url,separator=',',rename_columns=rename_dict)
                    columns_keeped = list(rename_dict.values())
                    columns_keeped.remove('location')
                    self.return_structured_pandas(gbr_data,columns_keeped=columns_keeped)

                elif self.db == 'covid19india': # IND
                    info('COVID19India database selected ...')
                    rename_dict = {'Date': 'date', 'State': 'location'}
                    drop_field  = {'State': ['India', 'State Unassigned']}
                    indi = self.csv2pandas("https://api.covid19india.org/csv/latest/states.csv",drop_field=drop_field,rename_columns=rename_dict,separator=',')
                    columns_keeped = ['Deceased', 'Confirmed', 'Recovered', 'Tested'] # Removing 'Other' data, not identified
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
                            'totalTestResults':' tot_test',
                            }
                    ctusa = self.csv2pandas("https://covidtracking.com/data/download/all-states-history.csv",
                        rename_columns = rename_dict, separator = ',')
                    columns_keeped = list(rename_dict.values())
                    columns_keeped.remove('location') # is already expected
                    self.return_structured_pandas(ctusa, columns_keeped = columns_keeped)
                elif self.db == 'spf' or self.db == 'spfnational':
                    if self.db == 'spfnational':
                        info('SPF aka Sante Publique France database selected (France granularity) ...')
                        spf = self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/d3a98a30-893f-47f7-96c5-2f4bcaaa0d71", separator = ',')
                        spf['total_deces_ehpad']=pd.to_numeric(spf['total_deces_ehpad'], errors = 'coerce')
                        self.return_structured_pandas(spf) # with 'tot_dc' first
                    else:
                        info('SPF aka Sante Publique France database selected (France departement granularity) ...')
                        info('... Seven different databases from SPF will be parsed ...')
                        # https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
                        # Parse and convert spf data structure to JHU one for historical raison
                        # hosp Number of people currently hospitalized
                        # rea  Number of people currently in resuscitation or critical care
                        # rad      Total amount of patient that returned home
                        # dc       Total amout of deaths at the hospital
                        # 'sexe' == 0 male + female
                        cast = {'dep': 'string'}
                        rename = {'jour': 'date', 'dep': 'location'}
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
                                    constraints = constraints, rename_columns = rename, separator=';', cast=cast)
                        #result = pd.concat([spf1, spf2,spf3,spf4,spf5], axis=1, sort=False)
                        constraints = {'age_18ans': 0}
                        spf7 =  self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/c0f59f00-3ab2-4f31-8a05-d317b43e9055",
                                    constraints = constraints, rename_columns = rename, separator=';', cast=cast)

                        list_spf=[spf1, spf2, spf3, spf4, spf5, spf6, spf7]

                        for i in list_spf:
                            i['date'] = pd.to_datetime(i['date']).apply(lambda x: x if not pd.isnull(x) else '')

                        min_date=min([s.date.min() for s in list_spf])
                        max_date=max([s.date.max() for s in list_spf])
                        spf1, spf2, spf3, spf4, spf5, spf6, spf7 = spf1.set_index(['date', 'location']),\
                                                    spf2.set_index(['date', 'location']),\
                                                    spf3.set_index(['date', 'location']),\
                                                    spf4.set_index(['date', 'location']),\
                                                    spf5.set_index(['date', 'location']),\
                                                    spf6.set_index(['date', 'location']),\
                                                    spf7.set_index(['date', 'location'])

                        list_spf = [spf1, spf2, spf3, spf4, spf5, spf6,spf7]

                        result = reduce(lambda left, right: pd.merge(left, right, on = ['date','location'],
                                                    how = 'outer'), list_spf)
                        result = result.reset_index()

                        #print(merged)
                        #result = reduce(lambda x, y: x.merge(x, y, on = ['location','date']), [spf1, spf2,spf3,spf4,spf5])
                        #print(result)
                        # ['location', 'date', 'hosp', 'rea', 'rad', 'dc', 'incid_hosp',
                           # 'incid_rea', 'incid_dc', 'incid_rad', 'P', 'T', 'pop', 'region',
                           # 'libelle_reg', 'libelle_dep', 'tx_incid', 'R', 'taux_occupation_sae',
                           # 'tx_pos', 'tx_incid_couleur', 'R_couleur',
                           # 'taux_occupation_sae_couleur', 'tx_pos_couleur', 'nb_orange',
                           # 'nb_rouge']
                        #min_date=result['date'].min()
                        for w in ['incid_hosp', 'incid_rea', 'incid_rad', 'incid_dc', 'P', 'T', 'n_dose1', 'n_dose2']:
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
                            result['tot_'+w]=result.groupby(['location'])[w].cumsum()#+result['offset_'+w]
                        #
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
                            'tx_incid': 'cur_idx_tx_incid',
                            'R': 'cur_idx_R',
                            'taux_occupation_sae': 'cur_idx_taux_occupation_sae',
                            'tx_pos': 'cur_idx_tx_pos',
                            'tot_n_dose1': 'tot_vacc',
                            'tot_n_dose2': 'tot_vacc2',
                            'Prc_tests_PCR_TA_crible':'cur_idx_Prc_tests_PCR_TA_crible',
                            'Prc_susp_501Y_V1':'cur_idx_Prc_susp_501Y_V1',
                            'Prc_susp_501Y_V2_3':'cur_idx_Prc_susp_501Y_V2_3',
                            'Prc_susp_IND':'cur_idx_Prc_susp_IND',
                            'Prc_susp_ABS':'cur_idx_Prc_susp_ABS',
                            'ti':'cur_idx_ti',
                            'tp':'cur_idx_tp',
                            }

                        result = result.rename(columns=rename_dict)
                        columns_keeped  = list(rename_dict.values())+['tot_incid_hosp', 'tot_incid_rea', 'tot_incid_rad', 'tot_incid_dc', 'tot_P', 'tot_T']
                        self.return_structured_pandas(result,columns_keeped=columns_keeped) # with 'tot_dc' first
                elif self.db == 'opencovid19' or  self.db == 'opencovid19national':
                    rename={'maille_code':'location'}
                    cast={'source_url':str,'source_archive':str,'source_type':str}
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

                    column_to_integrate=['nouvelles_hospitalisations', 'nouvelles_reanimations', 'depistes']
                    for w in ['nouvelles_hospitalisations', 'nouvelles_reanimations', 'depistes']:
                        opencovid19['tot_'+w]=opencovid19.groupby(['location'])[w].cumsum()
                    #columns_skipped = ['granularite','maille_nom','source_nom','source_url','source_archive','source_type']

                    self.return_structured_pandas(opencovid19.rename(columns=dict_columns_keeped),columns_keeped=list(dict_columns_keeped.values())+['tot_'+c for c in column_to_integrate])
                elif self.db == 'owid':
                    info('OWID aka \"Our World in Data\" database selected ...')
                    drop_field = {'location':['International','World']}
                    owid = self.csv2pandas("https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
                    separator=',',drop_field=drop_field)
                    # renaming some columns
                    col_to_rename=['reproduction_rate','icu_patients','hosp_patients','positive_rate']
                    renamed_cols=['cur_'+c if c != 'positive_rate' else 'cur_idx_'+c for c in col_to_rename]
                    columns_keeped=['iso_code','total_deaths','total_cases','total_tests','total_vaccinations']
                    columns_keeped+=['total_cases_per_million','total_deaths_per_million','total_vaccinations_per_hundred']
                    self.return_structured_pandas(owid.rename(columns=dict(zip(col_to_rename,renamed_cols))),columns_keeped=columns_keeped+renamed_cols)
            except:
                raise CoaDbError("An error occured while parsing data of "+self.get_db()+". This may be due to a data format modification. "
                    "You may contact support@pycoa.fr. Thanks.")
            # some info
            info('Few information concernant the selected database : ', self.get_db())
            info('Available which key-words for: ',self.get_available_keys_words())
            info('Example of location : ',  ', '.join(random.choices(self.get_locations(), k=5)), ' ...')
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
        return self.available_options

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
       value = self.geoinfo.generic_info(self.get_db(),keys)[0]
       return value

   def get_keyword_url(self,keys):
       '''
        Return url where the keyword have been parsed
       '''
       value = self.geoinfo.generic_info(self.get_db(),keys)[1]
       master  = self.geoinfo.generic_info(self.get_db(),keys)[2]
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
            jhu_files_ext = ['deaths', 'confirmed', 'recovered']
        elif self.db == 'jhu-usa': # 'USA'
            extension = "_US.csv"
            jhu_files_ext = ['deaths','confirmed']
        elif self.db == 'rki': # 'DEU'
            base_url = 'https://github.com/jgehrcke/covid-19-germany-gae/raw/master/'
            jhu_files_ext = ['deaths','cases']
            extension = '-rki-by-ags.csv'
            base_name = ''
        else:
            raise CoaDbError('Unknown JHU like db '+str(self.db))

        self.available_keys_words = jhu_files_ext
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
            else:
                raise CoaTypeError('jhu nor jhu-usa database selected ... ')

            pandas_jhu_db=pandas_jhu_db.groupby(['location','date']).sum().reset_index()
            pandas_list.append(pandas_jhu_db)

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
        kwargs_test(kwargs,['cast','separator','encoding','constraints','rename_columns','drop_field'],
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
        pandas_db = pandas.read_csv(get_local_from_url(url,7200),sep=separator,dtype=dico_cast, encoding = encoding,
            keep_default_na=False,na_values='') # cached for 2 hours
        #pandas_db = pandas.read_csv(self.database_url,sep=separator,dtype=dico_cast, encoding = encoding )
        constraints = kwargs.get('constraints', None)
        rename_columns = kwargs.get('rename_columns', None)
        drop_field = kwargs.get('drop_field', None)

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
            pandas_db['semaine'] = [ week_to_date(i) for i in pandas_db['semaine'] ]
            pandas_db = pandas_db.rename(columns={'semaine':'date'})
        pandas_db['date'] = pandas.to_datetime(pandas_db['date'],errors='coerce').dt.date
        #self.dates  = pandas_db['date']
        if self.db == 'spfnational':
            pandas_db['location'] = ['France']*len(pandas_db)
        pandas_db = pandas_db.sort_values(['location','date'])
        if self.db == 'owid':
            pandas_db = pandas_db.loc[~pandas_db.iso_code.isnull()]
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
        not_un_nation_dict={'Kosovo':'Serbia','Northern Cyprus':'Cyprus'}
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
            strangeiso3tokick=[i for i in mypandas['iso_code'].dropna().unique() if not len(i)==3 ]
            mypandas = mypandas.loc[~mypandas.iso_code.isin(strangeiso3tokick)]
            self.available_keys_words.remove('iso_code')
            mypandas = mypandas.drop(columns=['location'])
            mypandas = mypandas.rename(columns={'iso_code':'location'})
        if self.db == 'dpc':
            gd = self.geo.get_data()[['code_region','name_subregion']]
            A=['P.A. Bolzano','P.A. Trento']
            tmp=mypandas.loc[mypandas.location.isin(A)].groupby('date').sum()
            tmp['location']='Trentino-Alto Adige'
            mypandas = mypandas.loc[~mypandas.location.isin(A)]
            tmp = tmp.reset_index()
            mypandas = mypandas.append(tmp)
            uniqloc = list(mypandas['location'].unique())
            sub2reg = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_subregion.isin(uniqloc)]['code_region'])))
            mypandas['codelocation'] = mypandas['location'].map(sub2reg)
        if self.db == 'dgs':
            gd = self.geo.get_data()[['name_subregion','name_region']]
            mypandas = mypandas.reset_index(drop=True)
            mypandas['location'] = mypandas['location'].apply(lambda x: x.title().replace('Do', 'do').replace('Da','da').replace('De','de'))
            uniqloc = list(mypandas['location'].unique())
            sub2reg = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.name_subregion.isin(uniqloc)]['name_region'])))
            mypandas['location'] = mypandas['location'].map(sub2reg)
            mypandas = mypandas.loc[~mypandas.location.isnull()]
        if self.db == 'obepine': # filling subregions.
            gd = self.geo.get_data()[['code_subregion','name_region']]
            #preg=self.geo.get_data(True)[['code_subregion','code_region']]
            uniqloc = list(mypandas['location'].unique())
            sub2reg = collections.OrderedDict(zip(uniqloc,list(gd.loc[gd.code_subregion.isin(uniqloc)]['name_region'])))
            #mypandas=mypandas.merge(preg,how='left',left_on='location',right_on='code_region')
            #mypandas = mypandas.explode('code_subregion')
            #mypandas['location'] = mypandas['code_subregion']
            mypandas['location'] = mypandas['location'].map(sub2reg)
            mypandas = mypandas.loc[~mypandas.location.isnull()]

        codename = None
        location_is_code = False
        uniqloc = list(mypandas['location'].unique())
        if self.db_world:
            codename = collections.OrderedDict(zip(uniqloc,self.geo.to_standard(uniqloc,output='list',db=self.get_db(),interpret_region=True)))
            self.slocation = list(codename.values())
            location_is_code = True
        else:
            if self.database_type[self.db][1] == 'region':
                if self.db == 'covid19india':
                    mypandas = mypandas.loc[~mypandas.location.isnull()]
                    uniqloc = list(mypandas['location'].unique())
                temp = self.geo.get_region_list()[['code_region','name_region']]
                codename = collections.OrderedDict(zip(uniqloc,list(temp.loc[temp.name_region.isin(uniqloc)]['code_region'])))
                self.slocation = uniqloc

            elif self.database_type[self.db][1] == 'subregion':
                temp = self.geo_all[['code_subregion','name_subregion']]
                if self.db in ['phe','covidtracking','spf','escovid19data','obepine']:
                    codename = collections.OrderedDict(zip(uniqloc,list(temp.loc[temp.code_subregion.isin(uniqloc)]['name_subregion'])))
                    self.slocation = list(codename.values())
                    location_is_code = True
                else:
                    codename = collections.OrderedDict(zip(uniqloc,list(temp.loc[temp.name_subregion.isin(uniqloc)]['code_subregion'])))
                    self.slocation = uniqloc
            else:
                CoaDbError('Granularity problem , neither region nor sub_region ...')
            #self.slocation = loc_sub_code
            #oldloc = loc_sub_name
            #newloc = loc_sub_code
            #toremove = [x for x in uniqloc if x not in loc_sub_name]
            #codedico={i:j for i,j in zip(loc_sub_code,newloc)}
        #tmp = pd.DataFrame()

        if self.db == 'dgs':
            mypandas = mypandas.reset_index(drop=True)
            #mypandas['location'] = mypandas['location'].apply(lambda x: x.title().replace('Do', 'do').replace('Da','da').replace('De','de'))
            #uniqloc = list(mypandas.location.unique())
            #a=self.geo.get_data()
            #subreg=a.loc[a.name_subregion.isin(uniqloc)][['name_subregion','name_region']].rename(columns={'name_subregion':'location'})
            #mypandas['region'] = mypandas['location'].map(dict(zip(subreg.location, subreg.name_region)))
            #mypandas = mypandas.drop(columns=['location'])
            #mypandas = mypandas.rename(columns={'region':'location'})
        #if len(oldloc) != len(newloc):
        #    raise CoaKeyError('Seems to be an iso3 problem behaviour ...')
        #mypandas = mypandas.replace(oldloc,newloc)

        mypandas = mypandas.groupby(['location','date']).sum(min_count=1).reset_index() # summing in case of multiple dates (e.g. in opencovid19 data). But keep nan if any
        mypandas = fill_missing_dates(mypandas)

        if location_is_code:
            if self.db != 'dgs':
                mypandas['codelocation'] =  mypandas['location'].astype(str)
            mypandas['location'] = mypandas['location'].map(codename)
            mypandas = mypandas.loc[~mypandas.location.isnull()]
        else:
            mypandas['codelocation'] =  mypandas['location'].map(codename).astype(str)
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
                clist=self.geo.to_standard(clist,output='list', interpret_region=True)
            else:
                clist=clist+self.geo.get_subregions_from_list_of_region_names(clist)
                if clist == ['FRA'] or clist == ['USA'] or clist == ['ITA'] :
                    clist=self.geo_all['code_subregion'].to_list()
            clist=list(set(clist)) # to suppress duplicate countries
            diff_locations = list(set(clist) - set(self.get_locations()))
            clist = [i for i in clist if i not in diff_locations]
            filtered_pandas = self.mainpandas.copy()
            if len(clist) == 0:
                raise CoaWhereError('No correct subregion found according to the where option given.')
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

   def flat_list(self, matrix):
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

        if not 'location' in kwargs or kwargs['location'] is None.__class__ or kwargs['location'] == None:
            if get_db_list_dict()[self.db][0] == 'WW':
                kwargs['location'] = 'world'
            else:
                kwargs['location'] = self.slocation #self.geo_all['code_subregion'].to_list()
        else:
            kwargs['location'] = kwargs['location']


        if kwargs['which'] not in self.get_available_keys_words() :
            raise CoaKeyError(kwargs['which']+' is not a available for ' + self.db + ' database name. '
            'See get_available_keys_words() for the full list.')

        devorigclist = None
        origclistlist = None
        origlistlistloc = None
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
                    raise CoaWhereError("In the case of national DB, all locations must have the same types i.e\
                    list or string but both is not accepted, could be confusing")

        if self.db_world:
            self.geo.set_standard('name')
            if origlistlistloc != None:
                fulllist = [ i if isinstance(i, list) else [i] for i in origclist ]
                location_exploded = [ self.geo.to_standard(i,output='list',interpret_region=True) for i in fulllist ]
            else:
                location_exploded = self.geo.to_standard(listloc,output='list',interpret_region=True)
        else:
            def codetoname(listloc):
                convertname = []
                a=self.geo.get_data()
                for i in listloc:
                    if not isinstance(i,list):
                        i=[i]
                    if i[0].isdigit() or i[0] in ['2A','2B']:
                        convertname.append(list(a.loc[a.code_subregion.isin(i)]['name_subregion']))
                    else:
                        convertname.append(i)
                return convertname
            name_regions = []
            if origlistlistloc != None:
                name_regions  = origlistlistloc
                origlistlistloc = codetoname(origlistlistloc)
                location_exploded = [ self.geo.get_subregions_from_list_of_region_names(i,output='name') \
                            if len(self.geo.get_subregions_from_list_of_region_names(i,output='name'))>0 else i \
                            for i in origlistlistloc ]

                if origlistlistloc == [['Métropole']]:
                    all_region = self.geo.get_region_list()
                    all_codes = all_region.code_region.astype(int)
                    origclistlist = [[i] for i in all_region[(all_codes>10) & (all_codes<100)].name_region.to_list()]
                    dicolocation_exploded = { i[0]:self.geo.get_subregions_from_list_of_region_names(i,output='name') for i in origclistlist }
                    location_exploded = list(dicolocation_exploded.values())
                    name_regions = list(dicolocation_exploded.keys())

            else:
                listloc = codetoname(listloc)
                listloc = self.flat_list(listloc)
                location_exploded = [ self.geo.get_subregions_from_list_of_region_names([i],output='name')\
                            if len(self.geo.get_subregions_from_list_of_region_names([i],output='name'))>0 else i \
                            for i in listloc]
                if self.db == 'dpc' or self.db == 'sciensano':
                    location_exploded = listloc
                location_exploded = self.flat_list(location_exploded)


        def sticky(lname):
            if len(lname)>0:
                tmp=''
                for i in lname:
                    tmp+=i+'-'
                lname=tmp[:-1]
            return [lname]

        pdcluster = pd.DataFrame()
        j=0
        if origlistlistloc != None:
            for i in location_exploded:
                tmp = self.get_mainpandas().loc[self.get_mainpandas().location.isin(i)]
                if origlistlistloc == [['Métropole']]:
                    tmp['clustername'] = [name_regions[j]]*len(tmp)
                else:
                    tmp['clustername'] = sticky(origlistlistloc[j])*len(tmp)

                if pdcluster.empty:
                    pdcluster = tmp
                else:
                    pdcluster = pdcluster.append(tmp)
                j+=1
            pdfiltered = pdcluster[['location','date','codelocation',kwargs['which'],'clustername']]
        else:
            pdfiltered = self.get_mainpandas().loc[self.get_mainpandas().location.isin(location_exploded)]
            pdfiltered = pdfiltered[['location','date','codelocation',kwargs['which']]]
            pdfiltered['clustername'] = pdfiltered['location'].copy()
        # deal with options now
        option = kwargs.get('option', '')
        fillnan = True # default
        sumall = False # default
        if not isinstance(option,list):
            option=[option]
        for o in option:
            if o == 'nonneg':
                if kwargs['which'].startswith('cur_'):
                    raise CoaKeyError('The option nonneg cannot be used with instantaneous data, such as cur_ which variables.')
                for loca in location_exploded:
                    # modify values in order that diff values is never negative
                    pdloc=pdfiltered.loc[ pdfiltered.clustername == loca ][kwargs['which']]
                    y0=pdloc.values[0] # integrated offset at t=0
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
                    pdfiltered.loc[ind,kwargs['which']]=np.cumsum(yy)+y0 # do not forget the offset
            elif o == 'nofillnan':
                fillnan=False
            elif o == 'fillnan':
                fillnan=True
            elif o == 'smooth7':
                #pdfiltered[kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].fillna(method='ffill')
                #pdfiltered = pdfiltered.fillna(0)
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].rolling(7,min_periods=7,center=True).mean().reset_index(level=0,drop=True)
                #pdfiltered[kwargs['which']] = pdfiltered[kwargs['which']].fillna(0) # causes bug with fillnan procedure below
                pdfiltered = pdfiltered.groupby('clustername').apply(lambda x : x[3:-3]).reset_index(drop=True) # remove out of bound dates.
                fillnan = False
            elif o == 'sumall':
                sumall = True
                if kwargs['which'].startswith('cur_idx_Prc'):
                    print('Warning this data is from rolling value, ended date may be not correct ...')
            elif o != None and o != '':
                raise CoaKeyError('The option '+o+' is not recognized in get_stats. See get_available_options() for list.')
        pdfiltered = pdfiltered.reset_index(drop=True)
        if fillnan: # which is the default. Use nofillnan option instead.
            # fill with previous value
            pdfiltered = pdfiltered.copy()
            #if self.db_world:
            #pdfiltered[kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].fillna(method='bfill')
            pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].\
            apply(lambda x: x.ffill().bfill())
            # fill remaining nan with zeros
            #pdfiltered = pdfiltered.fillna(0)

        # if sumall set, return only integrate val
        tmppandas=pd.DataFrame()
        if sumall:
            if origlistlistloc != None:
               uniqcluster = pdfiltered.clustername.unique()

               tmp = pdfiltered.loc[pdfiltered.clustername.isin(uniqcluster)].\
                        groupby(['clustername','date']).sum().reset_index()

               #dicocode = {i:list(pdfiltered.loc[pdfiltered.clustername.isin(i)]['codelocation']) for i in uniqcluster}
               codescluster={i:list(pdfiltered.loc[pdfiltered.clustername==i]['codelocation'].unique()) for i in uniqcluster}
               namescluster={i:list(pdfiltered.loc[pdfiltered.clustername==i]['location'].unique()) for i in uniqcluster}
               tmp['codelocation'] = tmp['clustername'].map(codescluster)
               tmp['location'] = tmp['clustername'].map(namescluster)

               if kwargs['which'].startswith('cur_idx_'):
                    tmp[kwargs['which']] = tmp.loc[tmp.clustername.isin(uniqcluster)].\
                    apply(lambda x: x[kwargs['which']]/len(x.clustername),axis=1)
               pdfiltered = tmp

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
            pdfiltered['clustername'] = pdfiltered['location']

        pdfiltered['daily'] = pdfiltered[kwargs['which']].diff()
        inx = pdfiltered.groupby('clustername').head(1).index
        #First value of diff is always NaN
        pdfiltered.loc[inx, 'daily'] = pdfiltered[kwargs['which']].iloc[inx]
        pdfiltered['cumul'] = pdfiltered[kwargs['which']].cumsum()
        pdfiltered['weekly'] = pdfiltered[kwargs['which']].diff(7)
        inx7=pdfiltered.groupby('clustername').head(7).index
        pdfiltered.loc[inx7, 'weekly'] = pdfiltered[kwargs['which']].iloc[inx7]

        #if fillnan:
        #    pdfiltered = pdfiltered.fillna(0) # for diff if needed

        unifiedposition=['location', 'date', kwargs['which'], 'daily', 'cumul', 'weekly', 'codelocation','clustername']
        pdfiltered = pdfiltered[unifiedposition]

        return pdfiltered

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
