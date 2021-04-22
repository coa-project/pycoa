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
from coa.tools import info, verb, kwargs_test, get_local_from_url, fill_missing_dates, check_valid_date, rollingweek_to_middledate, get_db_list_dict
import coa.rapport as rap

import coa.geo as coge
import coa.display as codisplay
from coa.error import *
from scipy import stats as sps
import random
from functools import reduce

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
        self.available_options = ['nonneg', 'nofillnan', 'smooth7', 'sumall']
        self.available_keys_words = []
        self.dates = []
        self.database_columns_not_computed = {}
        self.db = db_name
        self.geo_all = ''
        self.set_display(self.db)
        self.database_url = []
        self.db_world=None
        if self.db not in self.database_name:
            raise CoaDbError('Unknown ' + self.db + '. Available database so far in PyCoa are : ' + str(self.database_name), file=sys.stderr)
        else:
            try:

                if get_db_list_dict()[self.db] == 'WW': # world wide db
                    self.db_world = True
                    self.geo = coge.GeoManager('name')
                    self.geo_all = 'world'
                else: # local db
                    self.db_world = False
                    self.geo = coge.GeoCountry(get_db_list_dict()[self.db])
                    self.geo_all = self.geo.get_subregion_list()['code_subregion'].to_list()

                # specific reading of data according to the db
                if self.db == 'jhu':
                    info('JHU aka Johns Hopkins database selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'jhu-usa':
                    info('USA, JHU aka Johns Hopkins database selected ...')
                    self.return_jhu_pandas()
                elif self.db == 'dpc':
                    info('ITA, Dipartimento della Protezione Civile database selected ...')
                    rename_dict = {'data': 'date', 'sigla_provincia': 'location', 'totale_casi': 'tot_casi'}
                    dpc1 = self.csv2pandas("https://github.com/pcm-dpc/COVID-19/raw/master/dati-province/dpc-covid19-ita-province.csv",\
                        rename_columns = rename_dict, separator=',')
                    columns_keeped = ['tot_casi']
                    self.return_structured_pandas(dpc1, columns_keeped=columns_keeped)
                elif self.db == 'covid19india':
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
                        info('... Six differents db from SPF will be parsed ...')
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
                        # variables n_dose_1, n_dose_2
                        constraints = {'vaccin': 0} # all vaccines
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
                        #
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
                        list_spf=[spf1, spf2, spf3, spf4, spf5, spf6]

                        for i in list_spf:
                            i['date'] = pd.to_datetime(i['date']).apply(lambda x: x if not pd.isnull(x) else '')

                        min_date=min([s.date.min() for s in list_spf])
                        max_date=max([s.date.max() for s in list_spf])
                        spf1, spf2, spf3, spf4, spf5, spf6 = spf1.set_index(['date', 'location']),\
                                                    spf2.set_index(['date', 'location']),\
                                                    spf3.set_index(['date', 'location']),\
                                                    spf4.set_index(['date', 'location']),\
                                                    spf5.set_index(['date', 'location']),\
                                                    spf6.set_index(['date', 'location'])

                        list_spf = [spf1, spf2, spf3, spf4, spf5, spf6]
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
                        for w in ['incid_hosp', 'incid_rea', 'incid_rad', 'incid_dc', 'P', 'T']:#, 'n_dose1', 'n_dose2']:
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
                        rename_dict={
                            'dc': 'tot_dc',
                            'hosp': 'cur_hosp',
                            'rad': 'tot_rad',
                            'rea': 'cur_rea',
                            'tx_incid': 'cur_idx_tx_incid',
                            'R': 'cur_idx_R',
                            'taux_occupation_sae': 'cur_idx_taux_occupation_sae',
                            'tx_pos': 'cur_idx_tx_pos',
                            'n_cum_dose1': 'tot_vacc',
                            'n_cum_dose2': 'tot_vacc2',

                            }
                        result = result.rename(columns=rename_dict)
                        columns_keeped  = list(rename_dict.values())+['tot_incid_hosp', 'tot_incid_rea', 'tot_incid_rad', 'tot_incid_dc', 'tot_P', 'tot_T']
                        columns_keeped += ['Prc_tests_PCR_TA_crible', 'Prc_susp_501Y_V1', 'Prc_susp_501Y_V2_3', 'Prc_susp_IND', 'Prc_susp_ABS']

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
       return  datab,datab.get_display()

   def set_display(self,db):
       ''' Set the CocoDisplay '''
       self.codisp = codisplay.CocoDisplay(db)

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

   def get_info_keys_words(self,keys):
       return rap.keyswords_info(self.get_db(),keys)


   def get_source(self):
        '''
        Return the current url used to fill the mainpandas
        (csv file)
        '''
        return self.database_url

   def return_jhu_pandas(self):
        ''' For center for Systems Science and Engineering (CSSE) at Johns Hopkins University
            COVID-19 Data Repository by the see homepage: https://github.com/CSSEGISandData/COVID-19
            return a structure : pandas location - date - keywords
            for jhu location are countries (location uses geo standard)
            for jhu-usa location are Province_State (location uses geo standard)
            '''
        base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"+\
                                "csse_covid_19_data/csse_covid_19_time_series/"
        jhu_files_ext = ['deaths', 'confirmed', 'recovered']
        pandas_jhu = {}
        if self.db == 'jhu':
            extansion =  "_global.csv"
        else:
            extansion = "_US.csv"
            jhu_files_ext = ['deaths','confirmed']
        self.available_keys_words = jhu_files_ext

        pandas_list = []
        for ext in jhu_files_ext:
            fileName = "time_series_covid19_" + ext + extansion
            url = base_url + fileName
            self.database_url.append(url)
            pandas_jhu_db = pandas.read_csv(get_local_from_url(url,7200), sep = ',') # cached for 2 hours
            if self.db == 'jhu':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Country/Region':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['Province/State','Lat','Long'])
                pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location"],var_name="date",value_name=ext)
            elif self.db == 'jhu-usa':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Province_State':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['UID','iso2','iso3','code3','FIPS',
                                    'Admin2','Country_Region','Lat','Long_','Combined_Key'])
                if 'Population' in pandas_jhu_db.columns:
                    pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location",'Population'],var_name="date",value_name=ext)
                else:
                    pandas_jhu_db = pandas_jhu_db.melt(id_vars=["location"],var_name="date",value_name=ext)
            else:
                raise CoaTypeError('jhu nor jhu-usa database selected ... ')
            pandas_jhu_db=pandas_jhu_db.groupby(['location','date']).sum().reset_index()
            pandas_list.append(pandas_jhu_db)

        uniqloc = pandas_list[0]['location'].unique()
        oldloc = uniqloc
        codedico={}
        if self.db_world:
            d_loc_s = self.geo.to_standard(list(uniqloc),output='list',db=self.get_db(),interpret_region=True)
            self.slocation = d_loc_s
            newloc = d_loc_s
            toremove = ['']
            g=coge.GeoManager('iso3')
            codedico={i:str(g.to_standard(i,db=self.get_db(),interpret_region=True)[0]) for i in newloc}
        else:
            loc_sub_name  = list(self.geo.get_subregion_list()['name_subregion'])
            loc_sub_code = list(self.geo.get_subregion_list()['code_subregion'])
            #loc_code = list(self.geo.get_data().loc[self.geo.get_data().name_subregion.isin(loc_sub)]['code_subregion'])
            self.slocation = loc_sub_code
            oldloc = loc_sub_name
            newloc = loc_sub_code
            toremove = [x for x in uniqloc if x not in loc_sub_name]
            codedico={i:j for i,j in zip(uniqloc,newloc)}
        result = reduce(lambda x, y: pd.merge(x, y, on = ['location','date']), pandas_list)
        result = result.loc[~result.location.isin(toremove)]
        tmp = pd.DataFrame()
        if 'Kosovo' in oldloc:
            tmp=(result.loc[result.location.isin(['Kosovo','Serbia'])].groupby('date').sum())
            tmp['location']='Serbia'
            result = result.loc[~result.location.isin(['Kosovo','Serbia'])]
            tmp = tmp.reset_index()
            cols = tmp.columns.tolist()
            cols = cols[0:1] + cols[-1:] + cols[1:-1]
            tmp = tmp[cols]
            result = result.append(tmp)

        result = result.replace(oldloc,newloc)
        if self.db == 'jhu-usa':
            result['codelocation'] = result['location']
        else:
            result['codelocation'] = result['location'].map(codedico)

        result['date'] = pd.to_datetime(result['date'],errors='coerce').dt.date
        self.dates  = result['date']
        result=result.sort_values(['location','date'])
        #self.mainpandas = result
        self.mainpandas = fill_missing_dates(result)

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
            pandas_db['semaine'] = [ rollingweek_to_middledate(i) for i in pandas_db['semaine'] ]
            pandas_db = pandas_db.rename(columns={'semaine':'date'})

        pandas_db['date'] = pandas.to_datetime(pandas_db['date'],errors='coerce').dt.date
        self.dates  = pandas_db['date']

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

        if 'iso_code' in self.available_keys_words:
            strangeiso3tokick=[i for i in mypandas['iso_code'].unique() if not len(i)==3]
            mypandas = mypandas.loc[~mypandas.iso_code.isin(strangeiso3tokick)]
            self.available_keys_words.remove('iso_code')
        uniqloc = list(mypandas['location'].unique())
        oldloc = uniqloc
        codedico={}
        if self.db_world:
            d_loc_s=self.geo.to_standard(uniqloc,output='list',db=self.get_db(),interpret_region=True)
            self.slocation=d_loc_s
            newloc = d_loc_s
            toremove=['']
            g=coge.GeoManager('iso3')
            codedico={i:str(g.to_standard(i,db=self.get_db(),interpret_region=True)[0]) for i in newloc}
        else:
            loc_sub_name  = list(self.geo.get_subregion_list()['name_subregion'])
            loc_sub_code = list(self.geo.get_subregion_list()['code_subregion'])
            #loc_code = list(self.geo.get_data().loc[self.geo.get_data().name_subregion.isin(loc_sub)]['code_subregion'])
            self.slocation = loc_sub_code
            oldloc = loc_sub_name
            newloc = loc_sub_code
            toremove = [x for x in uniqloc if x not in loc_sub_name]
            codedico={i:j for i,j in zip(loc_sub_code,newloc)}
        tmp = pd.DataFrame()

        not_un_nation_dict={'Kosovo':'Serbia','Northern Cyprus':'Cyprus'}
        for subpart_country, main_country in not_un_nation_dict.items() :
            if subpart_country in oldloc:
                tmp=(mypandas.loc[mypandas.location.isin([subpart_country,main_country])].groupby('date').sum())
                tmp['location']=main_country
                mypandas = mypandas.loc[~mypandas.location.isin([subpart_country,main_country])]
                tmp = tmp.reset_index()
                cols = tmp.columns.tolist()
                cols = cols[0:1] + cols[-1:] + cols[1:-1]
                tmp = tmp[cols]
                mypandas = mypandas.append(tmp)

        if len(oldloc) != len(newloc):
            raise CoaKeyError('Seems to be an iso3 problem behaviour ...')
        mypandas = mypandas.replace(oldloc,newloc)
        mypandas = mypandas.groupby(['location','date']).sum(min_count=1).reset_index() # summing in case of multiple dates (e.g. in opencovid19 data). But keep nan if any
        mypandas['codelocation'] = mypandas['location'].map(codedico)
        #self.mainpandas = mypandas

        self.mainpandas = fill_missing_dates(mypandas)

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
                if clist == ['FRA'] or clist == ['USA'] or clist == ['ITA']:
                    clist=self.geo_all

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
            for val in sublist:
                flatten_matrix.append(val)
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

        if not 'location' in kwargs or kwargs['location'] is None.__class__ or kwargs['location']==None:
            kwargs['location']=self.geo_all
        else:
            kwargs['location']=kwargs['location']

        if not isinstance(kwargs['location'], list):
            clist = ([kwargs['location']]).copy()
        else:
            clist = (kwargs['location']).copy()
        if not all(isinstance(c, str) for c in clist):
            raise CoaWhereError("Location via the where keyword should be given as strings. ")

        if kwargs['which'] not in self.get_available_keys_words() :
            raise CoaKeyError(kwargs['which']+' is not a available for ' + self.db + ' database name. '
            'See get_available_keys_words() for the full list.')

        if self.db_world:
            self.geo.set_standard('name')
            clist=self.geo.to_standard(clist,output='list',interpret_region=True)
        else:
            clist=clist+self.geo.get_subregions_from_list_of_region_names(clist)
            if clist == ['FRA'] or clist == ['USA']:
                clist=self.geo_all

        clist=list(set(clist)) # to suppress duplicate countries
        diff_locations = list(set(clist) - set(self.get_locations()))
        clist = [i for i in clist if i not in diff_locations]
        if len(clist) == 0:
            raise CoaWhereError('No correct subregion found according to the where option given.')

        pdfiltered = self.get_mainpandas().loc[self.get_mainpandas().location.isin(clist)]
        #if 'Serbia' in clist:
        #    ptot=self.get_mainpandas().loc[self.get_mainpandas().location=='Serbia'].\
        #        groupby(['date','location'])[self.get_available_keys_words()].sum().reset_index()
        #    for col in ptot.columns:
        #        if col.startswith('cur_idx_'):
        #            ptot[col]=ptot[col]/2
        #    clist.remove('Serbia')
        #    pdfiltered = self.get_mainpandas().loc[self.get_mainpandas().location.isin(clist)].reset_index()
        #    pdfiltered = pd.concat([pdfiltered,ptot])
        pdfiltered = pdfiltered[['location','date','codelocation',kwargs['which']]]

        # insert dates at the end for each country if necessary
        maxdate=pdfiltered['date'].max()
        for loca in pdfiltered.location.unique(): # not clist because it may happen that some location does not exist in actual pandas
            lmaxdate=pdfiltered.loc[ pdfiltered.location == loca ]['date'].max()
            if lmaxdate != maxdate:
                pdfiltered = pdfiltered.append(pd.DataFrame({'location':loca,
                    'date':pd.date_range(start=lmaxdate,end=maxdate,closed='right').date,
                    kwargs['which']:np.nan}) )
        pdfiltered.reset_index(level=0,drop=True,inplace=True)

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
                for loca in clist:
                    # modify values in order that diff values is never negative
                    pdloc=pdfiltered.loc[ pdfiltered.location == loca ][kwargs['which']]
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
            elif o == 'smooth7':
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['location'])[kwargs['which']].fillna(method='ffill')
                pdfiltered = pdfiltered.fillna(0)
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['location'])[kwargs['which']].rolling(7,min_periods=7,center=True).mean().reset_index(level=0,drop=True)
                #pdfiltered[kwargs['which']] = pdfiltered[kwargs['which']].fillna(0) # causes bug with fillnan procedure below
                pdfiltered = pdfiltered.groupby('location').apply(lambda x : x[3:-3]).reset_index(drop=True) # remove out of bound dates.
                fillnan = False
            elif o == 'sumall':
                sumall = True
            elif o != None and o != '':
                raise CoaKeyError('The option '+o+' is not recognized in get_stats. See get_available_options() for list.')

        if fillnan: # which is the default. Use nofillnan option instead.
            # fill with previous value
            pdfiltered[kwargs['which']] = pdfiltered.groupby(['location'])[kwargs['which']].fillna(method='ffill')
            # fill remaining nan with zeros
            pdfiltered = pdfiltered.fillna(0)

        # if sumall set, return only integrate val
        if sumall:
            loc = pdfiltered['location'].unique()
            ntot=len(loc)
            ptot=pdfiltered.groupby(['location']).fillna(method='ffill').groupby(['date']).sum().reset_index()   # summing for all locations

            # mean for some columns, about index and not sum of values.
            for col in ptot.columns:
                if col.startswith('cur_idx_'):
                    ptot[col]=ptot[col]/ntot
            # adding the location name
            #all_loc_string=str(kwargs['location'])
                #if len(kwargs['location'])>2:
                    #all_loc_string="["+str(kwargs['location'][0])+"..."+str(kwargs['location'][-1])+"]"
            ptot['location']=[list(loc)]*len(ptot)
            if type(kwargs['location']) == str:
                kwargs['location']= [kwargs['location']]
            ptot['codelocation']=[str(kwargs['location'])]*len(ptot)
            pdfiltered=ptot
            pdfiltered['daily'] = pdfiltered[kwargs['which']].diff()
            pdfiltered['cumul'] = pdfiltered[kwargs['which']].cumsum()
            pdfiltered['weekly'] = pdfiltered[kwargs['which']].diff(7)
        # computing daily, cumul and weekly
        else:
            if type(kwargs['location']) == str:
                kwargs['location']= [kwargs['location']]
            pdfiltered['daily'] = pdfiltered.groupby(['location'])[kwargs['which']].diff()
            pdfiltered['cumul'] = pdfiltered.groupby(['location'])[kwargs['which']].cumsum()
            pdfiltered['weekly'] = pdfiltered.groupby(['location'])[kwargs['which']].diff(7)
        if fillnan:
            pdfiltered = pdfiltered.fillna(0) # for diff if needed

        unifiedposition=['location', 'date', kwargs['which'], 'daily', 'cumul', 'weekly', 'codelocation']
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
