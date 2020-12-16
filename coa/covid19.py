# -*- coding: utf-8 -*-
"""
Project : PyCoA
Date :    april-november 2020
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
from coa.tools import info,verb,kwargs_test,get_local_from_url
import coa.geo as coge
import coa.display as codisplay
from coa.error import *
from scipy import stats as sps
import random

class DataBase():
   '''
   DataBase class
   Parse a Covid-19 database and filled the pandas python objet : pandas_datase
   It takes a string argument, which can be: 'jhu','spf','owid' and 'opencovid19'
   The pandas_datase structure is based, for historical reason, on the JHU structure:
   ['location', 'date', key-words , 'cumul', 'diff']
   '''
   def __init__(self,db_name):
        '''
         Fill the pandas_datase
        '''
        verb("Init of covid19.DataBase()")
        self.database_name=['jhu','owid','jhu-usa','spf','opencovid19']
        self.pandas_datase = {}
        self.available_keys_words=[]
        self.dates = []
        self.dicos_countries = {}
        self.dict_current_days = {}
        self.dict_cumul_days = {}
        self.dict_diff_days = {}
        self.location_more_info={}
        self.database_columns_not_computed={}
        self.db =  db_name
        if self.db == 'jhu' or  self.db == 'owid':
            self.geo = coge.GeoManager('name')
        if self.db =='spf' or self.db == 'opencovid19':
            self.geo = coge.GeoCountry('FRA',True)
        if self.db =='jhu-usa':
            self.geo = coge.GeoCountry('USA',True)
        if self.db not in self.database_name:
            raise CoaDbError('Unknown ' + self.db + '. Available database so far in PyCoa are : ' + str(self.database_name) ,file=sys.stderr)
        else:
            if self.db == 'jhu':
                info('JHU aka Johns Hopkins database selected ...')
                self.pandas_datase = self.parse_convert_jhu()
            if self.db == 'jhu-usa':
                info('USA, JHU aka Johns Hopkins database selected ...')
                self.pandas_datase = self.parse_convert_jhu()
            elif self.db == 'spf':
                info('SPF aka Sante Publique France database selected ...')
                info('... tree differents db from SPF will be parsed ...')
                # https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
                # Parse and convert spf data structure to JHU one for historical raison
                # hosp Number of people currently hospitalized
                # rea  Number of people currently in resuscitation or critical care
                # rad      Total amount of patient that returned home
                # dc       Total amout of deaths at the hospital
                # 'sexe' == 0 male + female
                cast={'dep':'string'}
                rename={'jour':'date','dep':'location'}
                constraints={'sexe':0}
                spf1=self.csv_to_pandas_index_location_date("https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7",
                              rename_columns=rename,constraints=constraints,cast=cast)
                # https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
                # incid_hosp	string 	Nombre quotidien de personnes nouvellement hospitalisées
                # incid_rea	integer	Nombre quotidien de nouvelles admissions en réanimation
                # incid_dc	integer	Nombre quotidien de personnes nouvellement décédées
                # incid_rad	integer	Nombre quotidien de nouveaux retours à domicile
                spf2=self.csv_to_pandas_index_location_date("https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c",
                              rename_columns=rename,cast=cast)
                # https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-resultats-des-tests-virologiques-covid-19/
                # T       Number of tests performed
                # P       Number of positive tests
                constraints={'cl_age90':0}
                spf3=self.csv_to_pandas_index_location_date("https://www.data.gouv.fr/fr/datasets/r/406c6a23-e283-4300-9484-54e78c8ae675",
                              rename_columns=rename,constraints=constraints,cast=cast)

                #https://www.data.gouv.fr/fr/datasets/indicateurs-de-suivi-de-lepidemie-de-covid-19/#_
                # tension hospitaliere
                # Vert : taux d’occupation compris entre 0 et 40% ;
                # Orange : taux d’occupation compris entre 40 et 60% ;
                # Rouge : taux d'occupation supérieur à 60%.
                # R0
                # vert : R0 entre 0 et 1 ;
                # Orange : R0 entre 1 et 1,5 ;
                # Rouge : R0 supérieur à 1,5.
                cast={'departement':'string'}
                rename={'extract_date':'date','departement':'location'}
                columns_skipped=['region','libelle_reg','libelle_dep','tx_incid_couleur','R_couleur',\
                'taux_occupation_sae_couleur','tx_pos_couleur','nb_orange','nb_rouge']
                spf4=self.csv_to_pandas_index_location_date("https://www.data.gouv.fr/fr/datasets/r/4acad602-d8b1-4516-bc71-7d5574d5f33e",
                            rename_columns=rename, separator=',', encoding = "ISO-8859-1",cast=cast)
                result = pd.concat([spf1, spf2,spf3,spf4], axis=1, sort=False)
                self.pandas_datase = self.pandas_index_location_date_to_jhu_format(result,columns_skipped=columns_skipped)
            elif self.db == 'opencovid19':
                info('OPENCOVID19 selected ...')
                rename={'maille_code':'location'}
                cast={'source_url':str,'source_archive':str,'source_type':str}
                drop_field  = {'granularite':['pays','monde','region']}
                columns_skipped = ['granularite','maille_nom','source_nom','source_url','source_archive','source_type']
                opencovid19 = self.csv_to_pandas_index_location_date('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv',
                            drop_field=drop_field,rename_columns=rename,separator=',',cast=cast)
                opencovid19 = opencovid19.reset_index()
                opencovid19['location'] = opencovid19['location'].apply(lambda x: x.replace('COM-','').replace('DEP-',''))
                opencovid19 = opencovid19.set_index('location','date')
                self.pandas_datase = self.pandas_index_location_date_to_jhu_format(opencovid19,columns_skipped=columns_skipped)
            elif self.db == 'owid':
                info('OWID aka \"Our World in Data\" database selected ...')
                columns_keeped = ['total_cases', 'new_cases', 'total_deaths','new_deaths', 'total_cases_per_million',
                'new_cases_per_million', 'total_deaths_per_million','new_deaths_per_million', 'total_tests', 'new_tests',
                'total_tests_per_thousand', 'new_tests_per_thousand', 'new_tests_smoothed', 'new_tests_smoothed_per_thousand','stringency_index']
                drop_field = {'location':['International','World']}
                owid = self.csv_to_pandas_index_location_date("https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
                separator=',',drop_field=drop_field)
                self.pandas_datase = self.pandas_index_location_date_to_jhu_format(owid,columns_keeped=columns_keeped)
            self.fill_pycoa_field()
            info('Few information concernant the selected database : ', self.get_db())
            info('Available which key-words for: ',self.get_available_keys_words())
            info('Example of location : ',  ', '.join(random.choices(self.get_locations(), k=5)), ' ...')
            info('Last date data ', self.get_dates()[-1])

   def get_db(self):
        '''
        Return the Covid19 database selected, so far:
        'jhu','spf','owid' or 'opencovid19'
        '''
        return self.db

   def get_available_database(self):
        '''
        Return all the available Covid19 database :
        ['jhu', 'spf', 'owid', 'opencovid19']
        '''
        return self.database_name

   def get_available_keys_words(self):
        '''
        Return all the available keyswords for the database selected
        Key-words are for:
        - jhu : ['deaths','confirmed','recovered']
            * the data are cumulative i.e for a date it represents the total cases
            For more information please have a look to https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data
        - 'owid' : ['total_cases', 'new_cases', 'total_deaths', 'new_deaths',
                    'total_cases_per_million', 'new_cases_per_million', 'total_deaths_per_million',
                     'new_deaths_per_million', 'total_tests', 'new_tests', 'total_tests_per_thousand',
                     'new_tests_per_thousand', 'new_tests_smoothed', 'new_tests_smoothed_per_thousand',
                      'stringency_index']
        For more information please have a look to https://github.com/owid/covid-19-data/tree/master/public/data/
        - 'spf' : ['hosp', 'rea', 'rad', 'dc', 'incid_hosp', 'incid_rea', 'incid_dc',
                    'incid_rad', 'P', 'T', 'tx_incid', 'R', 'taux_occupation_sae', 'tx_pos']
            No translation have been done for french keywords data
        For more information please have a look to  https://www.data.gouv.fr/fr/organizations/sante-publique-france/
        - 'opencovid19' :['cas_confirmes', 'cas_ehpad', 'cas_confirmes_ehpad', 'cas_possibles_ehpad', 'deces', 'deces_ehpad',
        'reanimation', 'hospitalises','nouvelles_hospitalisations', 'nouvelles_reanimations', 'gueris', 'depistes']
        No translation have been done for french keywords data
        For more information please have a look to https://github.com/opencovid19-fr
        '''
        return self.available_keys_words

   def get_database_url(self):
        '''
        Return all the url used to fill pandas_datase
        '''
        return self.database_url

   def get_rawdata(self):
        '''
        Return pandas_datase as a python dictionnaries:
        keys are keyswords and values are:
                        | date-1    | date-2   | date-3     | ...   | date-i
           location     |           |          |            |       |
           location-1   |           |          |            |       |
           location-2   |           |          |            |       |
           location-3   |           |          |            |       |
            ...
           location-j   |           |          |            |       |
        '''
        return self.pandas_datase

   def parse_convert_jhu(self):
        ''' For center for Systems Science and Engineering (CSSE) at Johns Hopkins University
            COVID-19 Data Repository by the see homepage: https://github.com/CSSEGISandData/COVID-19 '''

        self.database_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"+\
                                "csse_covid_19_data/csse_covid_19_time_series/"
        jhu_files_ext = ['deaths', 'confirmed', 'recovered']
        pandas_jhu = {}
        if self.db == 'jhu':
            extansion =  "_global.csv"
        else:
            extansion = "_US.csv"
            jhu_files_ext = ['confirmed','deaths']
        self.available_keys_words = jhu_files_ext
        for ext in jhu_files_ext:
            fileName = "time_series_covid19_" + ext + extansion
            url = self.database_url + fileName
            pandas_jhu_db = pandas.read_csv(get_local_from_url(url,7200), sep = ',') # cached for 2 hours
            if self.db == 'jhu':
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Country/Region':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['Province/State','Lat','Long'])
            else:
                pandas_jhu_db = pandas_jhu_db.rename(columns={'Country_Region':'location'})
                pandas_jhu_db = pandas_jhu_db.drop(columns=['UID','iso2','iso3','code3','FIPS',
                                    'Admin2','Province_State','Lat','Long_','Combined_Key'])
            pandas_jhu_db = pandas_jhu_db.sort_values(by=['location'])
            pandas_jhu_db = pandas_jhu_db.set_index('location')
            self.dates    = pandas.to_datetime(pandas_jhu_db.columns,errors='coerce')
            pandas_jhu[ext] = pandas_jhu_db
        return pandas_jhu

   def csv_to_pandas_index_location_date(self,url,**kwargs):
        '''
        Parse and convert CSV file to a pandas with location+date as an index
        '''
        self.database_url=url

        kwargs_test(kwargs,['cast','separator','encoding','constraints','rename_columns','drop_field'],
            'Bad args used in the csv_to_pandas_index_location_date() function.')

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
        pandas_db = pandas.read_csv(get_local_from_url(self.database_url,7200),sep=separator,dtype=dico_cast, encoding = encoding ) # cached for 2 hours
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
        pandas_db['date'] = pandas.to_datetime(pandas_db['date'],errors='coerce')
        #pandas_db['date'] = pandas_db['date'].dt.strftime("%m/%d/%y")
        pandas_db = pandas_db.sort_values(['location','date'])
        pandas_db = pandas_db.groupby(['location','date']).first()

        return pandas_db

   def pandas_index_location_date_to_jhu_format(self,mypandas,**kwargs):
        '''
        Return a pandas in PyCoA Structure
        '''
        kwargs_test(kwargs,['columns_skipped','columns_keeped'],
            'Bad args used in the pandas_index_location_date_to_jhu_format() function.')

        columns_skipped = kwargs.get('columns_skipped', None)
        columns_keeped  = kwargs.get('columns_keeped', None)
        database_columns_not_computed = ['date','location']
        available_keys_words_pub = [i for i in mypandas.columns.values.tolist() if i not in database_columns_not_computed]
        if columns_skipped:
            for col in columns_skipped:
                database_columns_not_computed.append(col)
            available_keys_words_pub = [i for i in mypandas.columns.values.tolist() if i not in database_columns_not_computed]
        if columns_keeped:
           available_keys_words_pub = columns_keeped
        self.available_keys_words = available_keys_words_pub
        mypandas.reset_index(inplace=True)
        pandas_dico = {}
        for w in available_keys_words_pub:
            pandas_temp   = mypandas[['location','date',w]]
            pandas_temp.reset_index(inplace=True)
            pandas_temp   = pandas_temp.pivot_table(index='location',values=w,columns='date',dropna=False)
            #pandas_temp   = pandas_temp.rename(columns=lambda x: x.strftime('%m/%d/%y'))
            pandas_dico[w] = pandas_temp
            self.dates    = pandas.to_datetime(pandas_dico[w].columns,errors='coerce')
        return pandas_dico

   def fill_pycoa_field(self):
        ''' Fill PyCoA variables with database data '''
        df = self.get_rawdata()
        #self.dicos_countries = defaultdict(list)

        one_time_enough = False
        for keys_words in self.available_keys_words:
                self.dicos_countries[keys_words] = defaultdict(list)
                self.dict_current_days[keys_words] = defaultdict(list)
                self.dict_cumul_days[keys_words] = defaultdict(list)
                self.dict_diff_days[keys_words] = defaultdict(list)

                if self.db != 'jhu' and self.db != 'jhu-usa': # needed since not same nb of rows for deaths,recovered and confirmed
                    if one_time_enough == False:
                        d_loc  = df[keys_words].to_dict('split')['index']
                        if self.db == 'owid' and one_time_enough == False:
                            d_loc=self.geo.to_standard(list(d_loc),output='list',db=self.get_db(),interpret_region=True)

                        one_time_enough = True
                else :
                    d_loc  = df[keys_words].to_dict('split')['index']
                    if self.db == 'jhu' and one_time_enough == False:
                        d_loc=self.geo.to_standard(list(d_loc),output='list',db=self.get_db(),interpret_region=True)
                    if self.db == 'jhu-usa' and one_time_enough == False:
                        d_loc=self.geo.get_subregion_list()['code_subregion']

                d_data = df[keys_words].to_dict('split')['data']
                {self.dicos_countries[keys_words][loc].append(data) for loc,data in zip(d_loc,d_data)}

                self.dict_current_days[keys_words] = {loc:list(np.sum(data, 0)) for loc,data in \
                self.dicos_countries[keys_words].items()}

                self.dict_cumul_days[keys_words] = {loc: np.nancumsum(data) for loc,data in \
                self.dict_current_days[keys_words].items()}

                self.dict_diff_days[keys_words] = {loc: np.insert(np.diff(data),0,0) for loc,data in \
                self.dict_current_days[keys_words].items()}

   def flat_list(self, matrix):
        ''' Flatten list function used in covid19 methods'''

        flatten_matrix = []
        for sublist in matrix:
            for val in sublist:
                flatten_matrix.append(val)
        return flatten_matrix

   def get_current_days(self):
        '''Return a python dictionnary
        key = 'keywords
        values = [value_i @ date_i]
        '''
        return self.dict_current_days

   def get_cumul_days(self):
        '''Return a python dictionnary cumulative
        key = 'keywords
        values = [cumululative value of current days return by get_current_days() from (date_0 to date_i)]
        '''
        return self.dict_cumul_days

   def get_diff_days(self):
        '''Return a python dictionnary differential
        key = 'keywords
        values = [difference value between i+1 and ith days current days return by get_current_days()]
        '''
        return self.dict_diff_days

   def get_dates(self):
        ''' Return all dates available in the current database'''
        return self.dates

   def get_locations(self):
        ''' Return available location countries / regions in the current database '''
        return np.array(tuple(self.get_diff_days()[self.available_keys_words[0]].keys()))

   def get_stats(self, **kwargs):
        '''
        Return the pandas pandas_datase
        'which' :   keywords
        'location': list of location used in the database selected
        'output': 'pandas' by default, 'array' return a Python array
        if output used:
            'type': 'cumul' or 'diff' return cumulative of diffferential  of keywords value for all the  location
            selected
        'option': default none can be 'nonneg'.
                In some cases negatives values can appeared due to a database updated, nonneg option
                will smooth the curve during all the period considered
        keys are keyswords from the selected database
                location        | date      | keywords     |  cumul        | diff
                -----------------------------------------------------------------------
                location1       |    1      |  val1-1      |  cuml1-1      |  diff1-1
                location1       |    2      |  val1-2      |  cumul1-2     |  diff1-2
                location1       |    3      |  val1-3      |  cumul1-3     |  diff1-3
                    ...
                location1       | last-date |  val1-last   |  cumul1-last  |   diff1-last
                    ...
                location-i      |    1      |  vali-1      |  cumli-1      |  diffi-1
                location-i      |    2      |  vali-1      |  cumli-2      |  diffi-2
                location-i      |    3      |  vali-1      |  cumli-3      |  diffi-3
                    ...

        '''
        kwargs_test(kwargs,['location','output','type','which','option',],
            'Bad args used in the get_stats() function.')

        if not isinstance(kwargs['location'], list):
            clist = ([kwargs['location']]).copy()
        else:
            clist = (kwargs['location']).copy()
        if not all(isinstance(c, str) for c in clist):
            raise CoaWhereError("Location via the where keyword should be given as strings. ")

        output = kwargs.get('output','pandas')
        process_data = kwargs.get('type', None)

        if kwargs['which'] not in self.get_available_keys_words() :
            raise CoaKeyError(kwargs['which']+' is not a available for' + self.db + 'database name. '
            'See get_available_keys_words() for the full list.')

        if self.db == 'jhu' or self.db == 'owid' or self.db == 'jhu-usa':
            if self.db == 'jhu-usa':
                clist=self.geo.get_subregion_list()['code_subregion']
            else:
                self.geo.set_standard('name')
                clist=self.geo.to_standard(clist,output='list',interpret_region=True)
            clist=list(set(clist)) # to suppress duplicate countrie
            diff_locations = list(set(clist) - set(self.get_locations()))
            clist = [i for i in clist if i not in diff_locations]

        currentout = np.array(tuple(dict(
            (c, (self.get_current_days()[kwargs['which']][c])) for c in clist).values()))
        cumulout = np.array(tuple(dict(
            (c, (self.get_cumul_days()[kwargs['which']][c])) for c in clist).values()))
        diffout = np.array(tuple(dict(
            (c, self.get_diff_days()[kwargs['which']][c]) for c in clist).values()))

        option = kwargs.get('option', None)
        if option == 'nonneg':
            diffout = np.array(diffout, dtype=float)
            currentout = np.array(currentout, dtype=float)
            for c in range(diffout.shape[0]):
                yy = np.array(diffout[c, :], dtype=float)
                where_nan = np.isnan(yy)
                yy[where_nan] = 0.
                for kk in np.where(yy < 0)[0]:
                    k = int(kk)
                    val_to_repart = -yy[k]
                    if k < np.size(yy)-1:
                        yy[k] = (yy[k+1]+yy[k-1])/2
                    else:
                        yy[k] = yy[k-1]
                    val_to_repart = val_to_repart + yy[k]
                    s = np.sum(yy[0:k])
                    yy[0:k] = yy[0:k]*(1-float(val_to_repart)/s)
                diffout[c, :] = yy
                currentout[c, :] = np.cumsum(yy)
                cumulout[c, :] = np.cumsum(np.cumsum(yy))
        elif option != None:
            raise CoaKeyError('The option '+option+' is not recognized in get_stat. Error.')

        datos=self.get_dates()
        i = 0
        temp=[]

        for coun in clist:
            if len(coun)==0:
                continue

            if len(currentout[i]):
                val1,val2,val3 = currentout[i], cumulout[i], diffout[i]

            else:
                val1 = val2 = val3 = [np.nan]*len(datos)
            data = {
                'location':[coun]*len(datos),
                'date': datos,
                kwargs['which']:val1,
                'cumul':val2,
                'diff': val3
                }
            temp.append(pd.DataFrame(data))
            i+=1

        pandy = pd.concat(temp)
        pandy['weekly'] = pandy.groupby('location')[kwargs['which']].rolling(7).mean().reset_index(level=0, drop=True)

        if output == "array":
            if process_data == 'cumul':
                out = cumulout
            elif process_data == 'diff':
	            out = diffout
            else:
                out =  currentout
            if out.shape[0] == 1:
                return out[0]
            else:
                return out.T

        #if len(clist) == 1 :
        #    temp[0] = temp[0].drop(columns=['location'])

        if temp==[]:
            raise CoaWhereError('No valid country available')
        pandy.db_citation = self.get_db()
        return pandy

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

   def get_display(self):
       co = None
       co = codisplay.CocoDisplay(self.db)
       return co

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
