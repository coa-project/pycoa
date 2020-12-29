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
from functools import reduce

class DataBase(object):
   '''
   DataBase class
   Parse a Covid-19 database and filled the pandas python objet : mainpandas
   It takes a string argument, which can be: 'jhu','spf','owid' and 'opencovid19'
   '''
   def __init__(self,db_name):
        '''
         Fill the pandas_datase
        '''
        verb("Init of covid19.DataBase()")
        self.database_name = ['jhu','owid','jhu-usa','spf','opencovid19']
        self.available_options = ['nonneg','fillnan0','fillnanf','smooth7']
        self.available_keys_words = []
        self.dates = []
        self.database_columns_not_computed = {}
        self.db =  db_name
        self.geo_all = ''
        self.set_display(self.db)

        if self.db not in self.database_name:
            raise CoaDbError('Unknown ' + self.db + '. Available database so far in PyCoa are : ' + str(self.database_name) ,file=sys.stderr)
        else:
            if self.db == 'jhu':
                info('JHU aka Johns Hopkins database selected ...')
                self.geo = coge.GeoManager('name')
                self.geo_all='world'
                self.return_jhu_pandas()
            if self.db == 'jhu-usa':
                info('USA, JHU aka Johns Hopkins database selected ...')
                self.geo = coge.GeoCountry('USA',True)
                self.geo_all = self.geo.get_subregion_list()['code_subregion'].to_list()
                self.return_jhu_pandas()
            elif self.db == 'spf':
                self.geo = coge.GeoCountry('FRA',True)
                self.geo_all = self.geo.get_subregion_list()['code_subregion'].to_list()
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
                spf1=self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7",
                              rename_columns=rename,constraints=constraints,cast=cast)
                # https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
                # incid_hosp	string 	Nombre quotidien de personnes nouvellement hospitalisées
                # incid_rea	integer	Nombre quotidien de nouvelles admissions en réanimation
                # incid_dc	integer	Nombre quotidien de personnes nouvellement décédées
                # incid_rad	integer	Nombre quotidien de nouveaux retours à domicile
                spf2=self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c",
                              rename_columns=rename,cast=cast)
                # https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-resultats-des-tests-virologiques-covid-19/
                # T       Number of tests performed
                # P       Number of positive tests
                constraints={'cl_age90':0}
                spf3=self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/406c6a23-e283-4300-9484-54e78c8ae675",
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
                #columns_skipped=['region','libelle_reg','libelle_dep','tx_incid_couleur','R_couleur',\
                #'taux_occupation_sae_couleur','tx_pos_couleur','nb_orange','nb_rouge']
                columns_keeped=['dc','hosp', 'rea', 'rad', 'incid_hosp', 'incid_rea', 'incid_dc',
                    'incid_rad', 'P', 'T', 'tx_incid', 'R', 'taux_occupation_sae', 'tx_pos'] # with 'dc' first
                spf4=self.csv2pandas("https://www.data.gouv.fr/fr/datasets/r/4acad602-d8b1-4516-bc71-7d5574d5f33e",
                            rename_columns=rename, separator=',', encoding = "ISO-8859-1",cast=cast)
                #result = pd.concat([spf1, spf2,spf3,spf4], axis=1, sort=False)
                result = reduce(lambda x, y: pd.merge(x, y, on = ['location','date']), [spf1, spf2,spf3,spf4])
                self.return_structured_pandas(result,columns_keeped=columns_keeped)
            elif self.db == 'opencovid19':
                info('OPENCOVID19 selected ...')
                self.geo = coge.GeoCountry('FRA',True)
                self.geo_all = self.geo.get_subregion_list()['code_subregion'].to_list()
                rename={'maille_code':'location'}
                cast={'source_url':str,'source_archive':str,'source_type':str}
                drop_field  = {'granularite':['pays','monde','region']}
                #columns_skipped = ['granularite','maille_nom','source_nom','source_url','source_archive','source_type']
                columns_keeped = ['deces','cas_confirmes', 'cas_ehpad', 'cas_confirmes_ehpad', 'cas_possibles_ehpad',
                     'deces_ehpad', 'reanimation', 'hospitalises', 'nouvelles_hospitalisations', 'nouvelles_reanimations', 'gueris', 'depistes']
                opencovid19 = self.csv2pandas('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv',
                            drop_field=drop_field,rename_columns=rename,separator=',',cast=cast)
                opencovid19['location'] = opencovid19['location'].apply(lambda x: x.replace('COM-','').replace('DEP-',''))
                self.return_structured_pandas(opencovid19,columns_keeped=columns_keeped)
            elif self.db == 'owid':
                info('OWID aka \"Our World in Data\" database selected ...')
                self.geo = coge.GeoManager('name')
                self.geo_all='world'
                columns_keeped=['total_deaths','total_cases','reproduction_rate','icu_patients','hosp_patients','total_tests','positive_rate','total_vaccinations']
                drop_field = {'location':['International','World']}
                owid = self.csv2pandas("https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
                separator=',',drop_field=drop_field)
                self.return_structured_pandas(owid,columns_keeped=columns_keeped)
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
        Return the current covid19 database selected, so far:
        'jhu','spf','owid' or 'opencovid19'
        '''
        return self.db

   def get_available_database(self):
        '''
        Return all the available Covid19 database :
        ['jhu', 'spf', 'owid', 'opencovid19']
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
        - 'opencovid19' :['cas_confirmes', 'cas_ehpad', 'cas_confirmes_ehpad', 'cas_possibles_ehpad', 'deces', 'deces_ehpad',
        'reanimation', 'hospitalises','nouvelles_hospitalisations', 'nouvelles_reanimations', 'gueris', 'depistes']
        No translation have been done for french keywords data
        For more information please have a look to https://github.com/opencovid19-fr
        '''
        return self.available_keys_words

   def get_database_url(self):
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
        self.database_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"+\
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
            url = self.database_url + fileName
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
        if self.db == 'jhu':
            d_loc_s = self.geo.to_standard(list(uniqloc),output='list',db=self.get_db(),interpret_region=True)
            self.slocation = d_loc_s
            newloc = d_loc_s
            toremove=['']
        else:
            loc_sub = list(self.geo.get_subregion_list()['name_subregion'])
            loc_code = list(self.geo.get_data().loc[self.geo.get_data().name_subregion.isin(loc_sub)]['code_subregion'])
            self.slocation = loc_code
            oldloc = loc_sub
            newloc = loc_code
            toremove = [x for x in uniqloc if x not in loc_sub]

        result = reduce(lambda x, y: pd.merge(x, y, on = ['location','date']), pandas_list)
        result = result.loc[~result.location.isin(toremove)]
        result = result.replace(oldloc,newloc)
        result['date'] = pd.to_datetime(result['date'],errors='coerce').dt.date
        self.dates  = result['date']
        result=result.sort_values(['location','date'])
        self.mainpandas = result

   def csv2pandas(self,url,**kwargs):
        '''
        Parse and convert the database cvs file to a pandas structure
        '''
        self.database_url=url
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
        pandas_db = pandas.read_csv(get_local_from_url(self.database_url,7200),sep=separator,dtype=dico_cast, encoding = encoding ) # cached for 2 hours
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
        pandas_db['date'] = pandas.to_datetime(pandas_db['date'],errors='coerce').dt.date
        self.dates  = pandas_db['date']
        pandas_db = pandas_db.sort_values(['location','date'])
        return pandas_db

   def return_structured_pandas(self,mypandas,**kwargs):
        '''
        Return the mainpandas core of the PyCoA structure
        '''
        kwargs_test(kwargs,['columns_skipped','columns_keeped'],
            'Bad args used in the return_structured_pandas function.')
        columns_skipped = kwargs.get('columns_skipped', None)
        columns_keeped  = kwargs.get('columns_keeped', None)

        absolutlyneeded = ['date','location']

        if columns_skipped:
            columns_keeped = [x for x in mypandas.columns.values.tolist() if x not in columns_skipped + absolutlyneeded]

        mypandas = mypandas[absolutlyneeded + columns_keeped]
        self.available_keys_words = columns_keeped #+ absolutlyneeded

        uniqloc = mypandas['location'].unique()
        oldloc = uniqloc
        if self.db == 'owid':
            d_loc_s=self.geo.to_standard(list(uniqloc),output='list',db=self.get_db(),interpret_region=True)
            self.slocation=d_loc_s
            newloc = d_loc_s
            toremove=['']
        else:
            loc_sub=list(self.geo.get_subregion_list()['name_subregion'])
            toremove=[x for x in uniqloc if x not in loc_sub]
            loc_code=list(self.geo.get_data().loc[self.geo.get_data().name_subregion.isin(loc_sub)]['code_subregion'])
            self.slocation=loc_code
            oldloc = loc_sub
            newloc = loc_code
        mypandas = mypandas.replace(oldloc,newloc)
        self.mainpandas = mypandas

   def get_mainpandas(self):
       '''
            Return the csv file to the mainpandas structure
            index | location              | date      | keywords1       |  keywords2    | ...| keywordsn
            -----------------------------------------------------------------------------------------
            0     |        location1      |    1      |  l1-val1-1      |  l1-val2-1    | ...|  l1-valn-1
            1     |        location1      |    2      |  l1-val1-2      |  l1-val2-2    | ...|  l1-valn-2
            2     |        location1      |    3      |  l1-val1-3      |  l1-val2-3    | ...|  l1-valn-3
                             ...
            p     |       locationp       |    1      |   lp-val1-1     |  lp-val2-1    | ...| lp-valn-1
            ...
        '''
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
         - date : from min date to max date used by the database selected
         - 'which' :  return the keyword values selected from the avalailable keywords keepted seems
            self.get_available_keys_words()
         - daily  : 'which' daily difference
         - weekly : 'which' weekly difference

         - 'option' :default none
            * 'nonneg' In some cases negatives values can appeared due to a database updated, nonneg option
                will smooth the curve during all the period considered
            * fillnan0 fill nan by 0
            * fillnanf fill nan by lastested available value
            * smooth7 moving average, window of 7 days

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
        kwargs_test(kwargs,['location','which','option',],
            'Bad args used in the get_stats() function.')

        if kwargs['location']==None:
            kwargs['location']=self.geo_all

        if not isinstance(kwargs['location'], list):
            clist = ([kwargs['location']]).copy()
        else:
            clist = (kwargs['location']).copy()
        if not all(isinstance(c, str) for c in clist):
            raise CoaWhereError("Location via the where keyword should be given as strings. ")

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

        pdfiltered = self.get_mainpandas().loc[self.get_mainpandas().location.isin(clist)]
        pdfiltered = pdfiltered[['location','date',kwargs['which']]]

        option = kwargs.get('option', '')
        fillnan0 = False
        if not isinstance(option,list):
            option=[option]
        for o in option:
            if o == 'nonneg':
                for loca in clist:
                    # modify values in order that diff values is never negative
                    pdloc=pdfiltered.loc[ pdfiltered.location == loca ][kwargs['which']]
                    y0=pdloc.values[0] # integrated offset at t=0
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
            elif o == 'fillnan0':
                # fill nan with zeros
                pdfiltered = pdfiltered.fillna(0)
                fillnan0 = True
            elif o == 'fillnanf':
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['location'])[kwargs['which']].fillna(method='ffill')
            elif o == 'smooth7':
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['location'])[kwargs['which']].rolling(7,min_periods=7,center=True).mean().reset_index(level=0,drop=True)
            elif o != None and o != '':
                raise CoaKeyError('The option '+o+' is not recognized in get_stats. See get_available_options() for list.')

        pdfiltered['daily'] = pdfiltered.groupby(['location'])[kwargs['which']].diff()
        pdfiltered['cumul'] = pdfiltered.groupby(['location'])[kwargs['which']].cumsum()
        pdfiltered['weekly'] = pdfiltered.groupby(['location'])[kwargs['which']].diff(7)

        if fillnan0:
            pdfiltered = pdfiltered.fillna(0)

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
