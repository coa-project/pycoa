# -*- coding: utf-8 -*-
"""
Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : src.covid19

About :
-------

Main class definitions for covid19 dataset access. Currently, we are only using the JHU CSSE data.
The parser class gives a simplier access through an already filled dict of data

"""

import pandas
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import datetime as dt

from src.tools import (
    kwargs_valuestesting,
    extract_dates,
    debug,
    verb,
    flat_list,
    getnonnegfunc,
    return_nonan_dates_pandas,
)
import src.geo as coge

import src.dbparser as parser

import geopandas as gpd
from src.error import *
import pickle
import os, time
import re
import src.geo as coge
from src.output import InputOption
class VirusStat(object):
   """
   VirusStat class
   """
   def __init__(self, db_name):
        """
            Main pycoa.class:
            - call the get_parser
            - call the geo
            - call the display
        """
        verb("Init of covid19.VirusStat()")
        self.db = db_name
        self.currentmetadata = parser.MetaInfo().getcurrentmetadata(db_name)
        self.currentdata = parser.DataParser(db_name)

        self.slocation = self.currentdata.get_locations()
        #self.geo = self.currentdata.get_geo()
        self.db_world = self.currentdata.get_world_boolean()
        self.codisp  = None
        self.code = self.currentmetadata['geoinfo']['iso3']
        self.granularity = self.currentmetadata['geoinfo']['granularity']
        self.namecountry = self.currentmetadata['geoinfo']['iso3']
        self._gi = coge.GeoInfo()

        try:
            if self.granularity == 'country':
                   self.geo = coge.GeoManager('name')
                   geopan = gpd.GeoDataFrame()#crs="EPSG:4326")
                   info = coge.GeoInfo()
                   allcountries = self.geo.get_GeoRegion().get_countries_from_region('world')
                   geopan['where'] = [self.geo.to_standard(c)[0] for c in allcountries]
                   geopan = info.add_field(field=['geometry'],input=geopan ,geofield='where')
                   geopan = gpd.GeoDataFrame(geopan, geometry=geopan.geometry, crs="EPSG:4326")
                   geopan = geopan[geopan['where'] != 'Antarctica']
                   where_kindgeo = geopan.dropna().reset_index(drop=True)
            else:
                   self.geo = coge.GeoCountry(self.code)
                   if self.granularity == 'region':
                        where_kindgeo = self.geo.get_region_list()[['code_region', 'name_region', 'geometry']]
                        where_kindgeo = where_kindgeo.rename(columns={'name_region': 'where'})
                        if self.code == 'PRT':
                             tmp = where_kindgeo.rename(columns={'name_region': 'where'})
                             tmp = tmp.loc[tmp.code_region=='PT.99']
                             self.boundary_metropole =tmp['geometry'].total_bounds
                        if self.code == 'FRA':
                             tmp = where_kindgeo.rename(columns={'name_region': 'where'})
                             tmp = tmp.loc[tmp.code_region=='999']
                             self.boundary_metropole =tmp['geometry'].total_bounds
                   elif self.granularity == 'subregion':
                        list_dep_metro = None
                        where_kindgeo = self.geo.get_subregion_list()[['code_subregion', 'name_subregion', 'geometry']]
                        where_kindgeo = where_kindgeo.rename(columns={'name_subregion': 'where'})
                   else:
                       raise CoaTypeError('What is the granularity of your  database ?')
        except:
            raise CoaTypeError('What data base are you looking for ?')
        self.where_geodescription = where_kindgeo

   @staticmethod
   def dictbypop():
       ''' return dictionnary bypop '''
       bypop = {'no':0,'100':100,'1k':1e3,'100k':1e5,'1M':1e6,'pop':1.}
       return bypop

   def getwheregeometrydescription(self):
        return self.where_geodescription

   def gettypeofgeometry(self):
        return self.geo

   def get_available_keywords(self):
       '''
        return available from the dbparser
       '''
       return self.currentdata.get_available_keywords()

   @staticmethod
   def factory(**kwargs):
       '''
        Return an instance to VirusStat and to Display methods
        This is recommended to avoid mismatch in labeled figures
       '''
       db_name = kwargs.get('db_name')
       reload = kwargs.get('reload', True)
       vis = kwargs.get('vis',None)

       path = ".cache/"
       if not os.path.exists(path):
           os.makedirs(path)
       filepkl = path + db_name + '.pkl'

       if reload:
           datab = VirusStat(db_name)
           with open(filepkl, 'wb') as f:
               pickle.dump(datab,f)

       if vis:
           datab.setvisu(db_name,datab.getwheregeometrydescription())
           return datab, datab.getvisu()
       else:
           return datab, None

   def setvisu(self,db_name,wheregeometrydescription):
       ''' Set the Display '''
       import src.output as output
       self.codisp = output.AllVisu(db_name, wheregeometrydescription)

   def getvisu(self):
       ''' Return the instance of Display initialized by factory'''
       return self.codisp

   @staticmethod
   def readpekl(filepkl):
      if not os.path.isfile(filepkl):
         path = ".cache/"
         if not os.path.exists(path):
              os.makedirs(path)
         db_name=filepkl.replace(path,'').replace('.pkl','')
         CoaWarning("Data from "+db_name + " isn't allready stored")
         datab = VirusStat(db_name)
         with open(filepkl, 'wb') as f:
             pickle.dump(datab,f)
      else:
         with open(filepkl, 'rb') as f:
             #print("Info of "+ db_name + " stored ")
             CoaInfo("last update: %s" % time.ctime(os.path.getmtime(filepkl)))
             #datab = pickle.load(f)
             datab = pd.read_pickle(f)
             datab.get_parserdb().get_echoinfo()
      return datab

   def setgeo(self,geo):
       self.geo = geo

   def getgeo(self):
       return self.geo

   def get_parserdb(self):
       return self.currentdata

   def get_fulldb(self):
      return self.currentdata.get_maingeopandas()

   def get_available_VirusStat(self):
        '''
        Return all the available Covid19 VirusStat
        '''
        return self.VirusStat_name

   def subregions_deployed(self,listloc,typeloc='subregion'):
        exploded = []
        a = self.geo.get_data()
        for i in listloc:
            if typeloc == 'subregion':
                if self.geo.is_region(i):
                    i = [self.geo.is_region(i)]
                    tmp = self.geo.get_subregions_from_list_of_region_names(i,output='name')
                elif self.geo.is_subregion(i):
                   tmp = i
                else:
                    raise CoaTypeError(i + ': not subregion nor region ... what is it ?')
            elif typeloc == 'region':
                tmp = self.geo.get_region_list()
                if i.isdigit():
                    tmp = list(tmp.loc[tmp.code_region==i]['name_region'])
                elif self.geo.is_region(i):
                    tmp = self.geo.get_regions_from_macroregion(name=i,output='name')
                    if self.currentmetadata['geoinfo']['iso3'] in ['USA, FRA, ESP, PRT']:
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
        return flat_list(exploded)

   def whereclustered(self,**kwargs):
        '''
        Handles the name and geometric behavior of the object
        Return a pandas after whereclustered
            - sum of the name location
            - sum all value or return mean value (depends on the variable considered)
            - sum all the geometry
        upper str comparision to be insensitive case
        '''
        input = kwargs['input']
        which = kwargs['which']
        where = kwargs['where']
        #where = [i.title() for i in where]
        option = kwargs['option']
        newpd = pd.DataFrame()

        if not isinstance(where[0],list):
            where = [where]
        if 'sumall' in option:
            for w in where:
                temp = pd.DataFrame()
                if not isinstance(w,list):
                    w=[w]

                if self.db_world:
                    self.geo.set_standard('name')
                    w_s = self.geo.to_standard(w,output='list',interpret_region=True)
                else:
                    w_s = self.subregions_deployed(w,self.granularity)
                temp = input.loc[input['where'].str.upper().isin([x.upper() for x in w_s])].reset_index(drop=True)

                temp = gpd.GeoDataFrame(temp, geometry=temp.geometry, crs="EPSG:4326").reset_index(drop=True)
                wpd = pd.DataFrame()

                for wi in which:
                    wherejoined  = ',' .join(flat_list(w))
                    code = temp.loc[temp.date==temp.date.max()]['code']
                    codejoined  = ',' .join(code)
                    geometryjoined = temp.loc[temp.date==temp.date.max()]["geometry"].unary_union

                    temp = temp.groupby(['date'])[which].sum().reset_index()
                    temp['where'] =  len(temp)*[wherejoined]
                    temp['code'] =  len(temp)*[codejoined]
                    temp['geometry'] = len(temp)*[geometryjoined]

                    if wpd.empty:
                        wpd = temp
                    else:
                        wpd = pd.concat([wpd,temp])

                wpd=wpd.loc[~wpd['where'].isin(w)]
                if newpd.empty:
                    newpd = temp
                else:
                    newpd = pd.concat([newpd,temp])
        else:
            where = flat_list(where)
            if self.db_world:
                where = self.geo.to_standard(where,output='list',interpret_region=True)
            else:
                where = self.subregions_deployed(where,self.granularity)
            newpd = input.loc[input['where'].str.upper().isin([x.upper() for x in where])]
        newpd = gpd.GeoDataFrame(newpd, geometry=newpd.geometry, crs='EPSG:4326').reset_index(drop=True)
        return newpd

   def get_stats(self,**kwargs):
       '''
            Return a fill kwargs after input arguments applied
            options:
             - test all arguments an their values
             - nonneg redistribute value in order to remove negative value

       '''
       defaultargs = InputOption().d_batchinput_args
       option = kwargs['option']
       kwargs_valuestesting(option,defaultargs['option'],'option error ... ')
       what = kwargs['what']
       kwargs_valuestesting(what,defaultargs['what'],'what error ...')
       output = kwargs['output']
       kwargs_valuestesting(output,defaultargs['output'],'output error ...')
       which = kwargs.get('which',[self.currentdata.get_available_keywords()[0]])
       if which == ['']:
           which = [self.currentdata.get_available_keywords()[0]]
           kwargs['which'] = which
       kwargs_valuestesting(which,self.currentdata.get_available_keywords(),'which error ...')
       when = kwargs.get('when')

       input = kwargs['input']

       if input.empty:
           input = self.currentdata.get_maingeopandas()
           kwargs['input'] = input

       anticolumns = [x for x in self.currentdata.get_available_keywords() if x not in which]

       input = input.loc[:,~input.columns.isin(anticolumns)]
       where = kwargs.get('where')

       kwargs['input'] = input

       input['date'] = pd.to_datetime(input['date'], errors='coerce')
       when_beg_data, when_end_data = input.date.min(), input.date.max()
       when_beg_data, when_end_data = when_beg_data.date(), when_end_data.date()
       #print("HERE 3")
       if when:
           when_beg, when_end = extract_dates(when)
           print("HERE",when_beg,type(when_beg),type(input.date[0].date()))
           if when_beg < when_beg_data:
                when_beg = when_beg_data
                CoaWarning("No available data before "+str(when_beg_data) + ' - ' + str(when_beg) + ' is considered')
           if when_end > when_end_data:
                when_end = when_end_data
                CoaWarning("No available data after "+str(when_end_data) + ' - ' + str(when_end) + ' is considered')
           input = input[(input.date >= pd.to_datetime(when_beg)) & (input.date <= pd.to_datetime(when_end))]
           kwargs['input'] = input
           when_beg_data,when_end_data = when_beg, when_end

       kwargs['when'] = [str(when_beg_data)+':'+str(when_end_data)]

       input = self.whereclustered(**kwargs)
       flatwhere = flat_list(where)

       for w in which:
           for o in option:
               wconcatpd = pd.DataFrame()
               temppd = input
               if o == 'fillnan':
                    temppd.loc[:,w] = temppd.groupby('where')[w].bfill()
                    temppd.loc[:,w] = temppd.groupby('where')[w].ffill()
               elif o == 'nofillnan':
                    fillnan = False
               elif o == 'nonneg':
                   if w.startswith('cur_'):
                       raise CoaWarning('The option nonneg cannot be used with instantaneous data, such as : ' + w)
                   concatpd = pd.DataFrame()
                   for loca in flatwhere:
                       pdwhere = temppd.loc[temppd['where'] == loca]
                       nonneg = getnonnegfunc(pdwhere,w)
                       if concatpd.empty:
                           concatpd = nonneg
                       else:
                           concatpd = pd.concat([concatpd,nonneg])
                   temppd = concatpd
               elif o == 'smooth7':
                    temppd.loc[:,w] = temppd.groupby(['where'])[w].rolling(7,min_periods=7).mean().reset_index(level=0,drop=True)
                    inx7 = temppd.groupby('where').head(7).index
                    temppd.loc[inx7, which] = temppd[w].bfill()
               elif o == 'sumall':
                    if w.startswith('cur_idx_') or w.startswith('cur_tx_'):
                        temppd = temppd.groupby(['where','code','date','geometry']).mean().reset_index()
                    else:
                        temppd = temppd.groupby(['where','code','date','geometry']).sum(numeric_only=True).reset_index()
               elif o.startswith('bypop='):
                     input = self.normbypop(input, which ,o)
                     kwargs['input'] = input
                     temppd = self.whereclustered(**kwargs)

               if wconcatpd.empty:
                    wconcatpd = temppd
               else:
                    wconcatpd = pd.concat([wconcatpd,temppd])

       input = wconcatpd
       input.loc[:,'daily'] = input.groupby('where')[w].diff()
       input.loc[:,'weekly'] = input.groupby('where')[w].diff(7)
       input.loc[:,'daily'] = input['daily'].bfill()
       input.loc[:,'weekly'] = input['weekly'].bfill()

       input = input.reset_index(drop=True)
       kwargs['input'] = input
       return kwargs

   def normbypop(self, pandy, val2norm ,bypop):
    """
        Return a pandas with a normalisation column add by population
        * can normalize by '100', '1k', '100k' or '1M' and the new which
    """
    if pandy.empty:
        raise CoaError('normbypop problem, your pandas seems to be empty ....')
    value = re.sub(r'^.*?bypop=', '', bypop)
    clust = list(pandy['where'].unique())
    pop_field='population'
    uniquepandy = pandy.groupby('where').first().reset_index()
    if self.db_world == True:
        uniquepandy = self._gi.add_field(input = uniquepandy,field = 'population')
    else:
        if not isinstance(self._gi,coge.GeoCountry):
            self._gi = None
        else:
            if self._gi.get_country() != self.geo.get_country():
                self._gi=None

        if self._gi == None :
            self._gi = self.geo

        pop_field='population_subregion'
        if self.granularity == 'region':
            regsubreg={i:self.geo.get_subregions_from_region(name=i) for i in clust}
            uniquepandy = self._gi.add_field(input=uniquepandy, field=pop_field, input_key='code')
        elif self.granularity == 'subregion':
            uniquepandy = self._gi.add_field(input=uniquepandy, field=pop_field, input_key='code')
        else:
            raise CoaKeyError('This is not region nor subregion what is it ?!')
    uniquepandy = uniquepandy[['where',pop_field]]
    pandy = pd.merge(pandy,uniquepandy,on='where',how='outer')

    for i in val2norm:
        pandy.loc[:,i+' '+bypop]=pandy[i]/pandy[pop_field]*VirusStat.dictbypop()[value]
    return pandy

   def saveoutput(self,**kwargs):
       '''
       saveoutput pycoa. pandas as an  output file selected by output argument
       'pandas': pycoa.pandas
       'saveformat': excel or csv (default excel)
       'savename': pycoa.ut (default)
       '''
       possibleformat=['excel','csv']
       saveformat = 'excel'
       savename = 'pycoa.ut'
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
        from scipy import stats as sps
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
