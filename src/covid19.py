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
import datetime as dt

from src.tools import (
    verb,
    kwargs_test,
    flat_list,
    return_nonan_dates_pandas,
)
import src.geo as coge

import src.dbparser as parser

import geopandas as gpd
from src.error import *
from scipy import stats as sps
import pickle
import os, time
import src.allvisu as allvisu
import src.geo as coge
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

   def permanentdisplay(self,input):
    '''
     when sumall option is used this method is usefull for the display
     it returns an input with new columns
    '''
    input['permanentdisplay'] = input.code
    if 'code' and 'clustername' not in input.columns:
       input['code'] = input['where']
       input['clustername'] = input['where']
       input['rolloverdisplay'] = input['where']
       input['permanentdisplay'] = input['where']
    else:
       if self.granularity == 'country' :
           #input['code'] = input['code'].apply(lambda x: str(x).replace('[', '').replace(']', '') if len(x)< 10 else x[0]+'...'+x[-1] )
           ##input['permanentdisplay'] = input.apply(lambda x: x.clustername if self.geo.get_GeoRegion().is_region(x.clustername) else str(x.code), axis = 1)
           input['permanentdisplay'] = input.code
       else:
           if self.granularity == 'subregion' :
               input = input.reset_index(drop=True)
               if isinstance(input['code'].iloc[0],list):
                   input['code'] = input['code'].apply(lambda x: str(x).replace("'", '')\
                                                if len(x)<5 else '['+str(x[0]).replace("'", '')+',...,'+str(x[-1]).replace("'", '')+']')

               trad={}
               cluster = input.clustername.unique()

               if isinstance(input['where'].iloc[0],list):
                  cluster = [i for i in cluster]
               for i in cluster:
                   if i == self.namecountry:
                       input['permanentdisplay'] = input.clustername #[self.dbld[self.VirusStat_name][2]]*len(input)
                   else:
                       if self.geo.is_region(i):
                           trad[i] = self.geo.is_region(i)
                       elif self.geo.is_subregion(i):
                           trad[i] = self.geo.is_subregion(i)#input.loc[input.clustername==i]['code'].iloc[0]
                       else:
                           trad[i] = i
                       trad={k:(v[:3]+'...'+v[-3:] if len(v)>8 else v) for k,v in trad.items()}
                       if ',' in input.code[0]:
                           input['permanentdisplay'] = input.clustername
                       else:
                           input['permanentdisplay'] = input.code#input.clustername.map(trad)
           elif self.granularity == 'region' :
               if all(i == self.namecountry for i in input.clustername.unique()):
                   input['permanentdisplay'] = [self.namecountry]*len(input)
               else:
                   input['permanentdisplay'] = input.code
           else :
               CoaError("Sorry but what's the granularity of you DB "+self.granularity)
    input['rolloverdisplay'] = input['where']
    if isinstance(input['permanentdisplay'][0],list):
        input['permanentdisplay'] = [str(i) for i in input['permanentdisplay']]
    return input


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
       #else:
       #   datab=VirusStat.readpekl(filepkl)
       #   print("HERE")
       #if visu:
       if vis:
           datab.setvisu(db_name,datab.getwheregeometrydescription())
           return datab, datab.getvisu()
       else:
           return datab, None

   def setvisu(self,db_name,wheregeometrydescription):
       ''' Set the Display '''
       self.codisp = allvisu.AllVisu(db_name, wheregeometrydescription)

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
         print("Data from "+db_name + " isn't allready stored")
         datab = VirusStat(db_name)
         with open(filepkl, 'wb') as f:
             pickle.dump(datab,f)
      else:
         with open(filepkl, 'rb') as f:
             #print("Info of "+ db_name + " stored ")
             print("last update: %s" % time.ctime(os.path.getmtime(filepkl)))
             datab = pickle.load(f)
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

   def get_stats(self,**kwargs):
        '''
        Return the pandas pandas_datase
         - index: only an incremental value
         - location: list of location used in the VirusStat selected (using geo standardization)
         - 'which' :  return the keyword values selected from the avalailable keywords keepted seems
            self.currentdata.get_available_keywords()

         - 'option' :default none
            * 'nonneg' In some cases negatives values can appeared due to a VirusStat updated, nonneg option
                will smooth the curve during all the period considered
            * 'nofillnan' if you do not want that NaN values are filled, which is the default behaviour
            * 'smooth7' moving average, window of 7 days
            * 'sumall' sum data over all locations

        keys are keyswords from the selected VirusStat
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

        - a clustername variable is computed

        '''
        option = None
        sumall = None
        wallname = None
        optionskipped=False
        othersinputfieldpandas=pd.DataFrame()

        if 'where' not in kwargs or kwargs['where'] is None.__class__ or kwargs['where'] == None:
            kwargs['where'] = list(self.get_fulldb()['where'].unique())

        option = kwargs.get('option', 'fillnan')
        fillnan = True # default
        sumall = False # default
        sumallandsmooth7 = False
        if 'input' not in kwargs:
            mypycoapd = self.currentdata.get_maingeopandas()
            if 'which' not in kwargs:
                kwargs['which'] = self.currentdata.get_available_keywords()[0]
            #if kwargs['which'] not in self.currentdata.get_available_keywords():
            #    raise CoaKeyError(kwargs['which']+' this value is not available in this db, please check !')
            mainpandas = return_nonan_dates_pandas(mypycoapd,kwargs['which'])
            #while for last date all values are nan previous date
        else:
            mypycoapd=kwargs['input']
            if str(type(mypycoapd['where'][0]))=="<class 'list'>":
                return mypycoapd
            kwargs['which']=kwargs['input_field']
            mainpandas = return_nonan_dates_pandas(mypycoapd,kwargs['input_field'])
            #if isinstance(kwargs['input_field'],list):
            #    for i in kwargs['input_field']:
            #        mainpandas[i] = mypycoapd[i]

        devorigclist = None
        origclistlist = None
        origlistlistloc = None

        if 'sumall' in option:
            if not isinstance(kwargs['where'], list):
                kwargs['where'] = [[kwargs['where']]]
            else:
                if not isinstance(kwargs['where'][0], list):
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
                a = self.geo.get_data()
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
            if origlistlistloc != None:
                dicooriglist={}

                for i in origlistlistloc:
                    if i[0].upper() in [self.currentmetadata['geoinfo']['iso3'].upper(),self.currentmetadata['geoinfo']['iso3'].upper()]:
                        dicooriglist[self.currentmetadata[self.db][0]] = explosion(flat_list(self.slocation),self.currentmetadata['geoinfo']['granularity'])
                    else:
                        dicooriglist[','.join(i)]=explosion(i,self.currentmetadata['geoinfo']['granularity'])
            else:
                if any([i.upper() in [self.currentmetadata['geoinfo']['iso3'].upper(),self.currentmetadata['geoinfo']['iso3'].upper()] for i in listloc]):
                    listloc=self.slocation
                listloc = explosion(listloc,self.currentmetadata['geoinfo']['granularity'])
                listloc = flat_list(listloc)
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
                code = tmp.code.unique()
                tmp['clustername'] = [k]*len(tmp)
                if pdcluster.empty:
                    pdcluster = tmp
                else:
                    pdcluster = pd.concat([pdcluster,tmp])
                j+=1
            pdfiltered = pdcluster[['where','date','code',kwargs['which'],'clustername']]
        else:
            pdfiltered = mainpandas.loc[mainpandas['where'].isin(location_exploded)]
            if 'input_field' in kwargs or isinstance(kwargs['which'],list):
                if 'which' in kwargs:
                    kwargs['input_field']=kwargs['which']
                if isinstance(kwargs['input_field'],list):
                    pdfilteredoriginal = pdfiltered.copy()
                    pdfiltered = pdfiltered[['where','date','code',kwargs['input_field'][0]]]
                    othersinputfieldpandas = pdfilteredoriginal[['where','date']+kwargs['input_field'][1:]]
                    kwargs['which'] = kwargs['input_field'][0]
                else:
                    pdfiltered = pdfiltered[['where','date','code', kwargs['input_field']]]
                    kwargs['which'] = kwargs['input_field']
            else:
                pdfiltered = pdfiltered[['where','date','code', kwargs['which']]]
            pdfiltered['clustername'] = pdfiltered['where'].copy()

        if not isinstance(option,list):
            option=[option]
        if 'fillnan' not in option and 'nofillnan' not in option:
            option.insert(0, 'fillnan')
        if 'nonneg' in option:
            option.remove('nonneg')
            option.insert(0, 'nonneg')
        if 'smooth7' in option and 'sumall' in option:
            sumallandsmooth7=True

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
                #pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['where','clustername'])[kwargs['which']].apply(lambda x: x.bfill())
                pdfiltered.loc[:,kwargs['which']] = pdfiltered.groupby(['where','clustername'],group_keys=False)[kwargs['which']].apply(lambda x: x.bfill())
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
            elif o != None and o != '':
                raise CoaKeyError('The option '+o+' is not recognized in get_stats. See listoptions() for list.')
        pdfiltered = pdfiltered.reset_index(drop=True)

        #sumallandsmooth7 if sumall set, return only integrate val
        tmppandas=pd.DataFrame()
        if sumall:
            if origlistlistloc != None:
               uniqcluster = pdfiltered.clustername.unique()
               if kwargs['which'].startswith('cur_idx_') or kwargs['which'].startswith('cur_tx_'):
                  tmp = pdfiltered.groupby(['clustername','date']).mean().reset_index()
               else:
                  tmp = pdfiltered.groupby(['clustername','date']).sum(numeric_only=True).reset_index()#.loc[pdfiltered.clustername.isin(uniqcluster)].\

               codescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['code'].unique()) for i in uniqcluster}
               namescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['where'].unique()) for i in uniqcluster}

               tmp['code'] = tmp['clustername'].map(codescluster)
               tmp['where'] = tmp['clustername'].map(namescluster)

               pdfiltered = tmp
               pdfiltered = pdfiltered.drop_duplicates(['date','clustername'])
            # computing daily, cumul and weekly
            else:
                if kwargs['which'].startswith('cur_idx_'):
                    tmp = pdfiltered.groupby(['date']).mean().reset_index()
                else:
                    tmp = pdfiltered.groupby(['date']).sum().reset_index()
                uniqloc = list(pdfiltered['where'].unique())
                uniqcodeloc = list(pdfiltered.code.unique())
                tmp.loc[:,'where'] = ['dummy']*len(tmp)
                tmp.loc[:,'code'] = ['dummy']*len(tmp)
                tmp.loc[:,'clustername'] = ['dummy']*len(tmp)
                for i in range(len(tmp)):
                    tmp.at[i,'where'] = uniqloc #sticky(uniqloc)
                    tmp.at[i,'code'] = uniqcodeloc #sticky(uniqcodeloc)
                    tmp.at[i,'clustername'] =  sticky(uniqloc)[0]
                pdfiltered = tmp
            if sumallandsmooth7:
                pdfiltered[kwargs['which']] = pdfiltered.groupby(['clustername'])[kwargs['which']].rolling(7,min_periods=7).mean().reset_index(level=0,drop=True)
                pdfiltered.loc[:,kwargs['which']] =\
                pdfiltered.groupby(['clustername'])[kwargs['which']].apply(lambda x: x.bfill())
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
        pdfiltered.cumul=pdfiltered.cumul.astype('int32')
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
        unifiedposition=['where', 'date', kwargs['which'], 'daily', 'cumul', 'weekly', 'code','clustername']

        if kwargs['which'] in ['standard','daily','weekly','cumul']:
            unifiedposition.remove(kwargs['which'])
        pdfiltered = pdfiltered[unifiedposition]

        if wallname != None and sumall == True:
               pdfiltered.loc[:,'clustername'] = wallname
        pdfiltered = pdfiltered.drop(columns='cumul')
        if not othersinputfieldpandas.empty:
            pdfiltered = pd.merge(pdfiltered, othersinputfieldpandas, on=['date','where'])

        pdfiltered = pdfiltered.loc[~(pdfiltered['where'].isna() | pdfiltered['code'].isna())]
        pdfiltered = self.permanentdisplay(pdfiltered)
        return pdfiltered


   def normbypop(self, pandy, val2norm,bypop):
    """
        Return a pandas with a normalisation column add by population
        * can normalize by '100', '1k', '100k' or '1M'
    """
    if pandy.empty:
        raise CoaKeyError('Seems to be an empty field')
    if isinstance(pandy['code'].iloc[0],list):
        pandy = pandy.explode('code')

    clust = list(pandy['clustername'].unique())
    if self.db_world == True:
        pop_field='population'
        pandy = self._gi.add_field(input=pandy,field=pop_field,geofield='code')
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
            self._gi.add_field(input=pandy, field=pop_field, input_key='code')
        elif self.granularity == 'subregion':
            pandy=self._gi.add_field(input=pandy, field=pop_field, input_key='code')
        else:
            raise CoaKeyError('This is not region nor subregion what is it ?!')

        #if pop_field not in self._gi.get_list_properties():
        #    raise CoaKeyError('The population information not available for this country. No normalization possible')



    df = pd.DataFrame()
    for i in clust:
        pandyi = pandy.loc[ pandy['clustername'] == i ].copy()
        pandyi.loc[:,pop_field] = pandyi.groupby('code')[pop_field].first().sum()
        if len(pandyi.groupby('code')['code'].first().tolist()) == 1:
            cody = pandyi.groupby('code')['code'].first().tolist()*len(pandyi)
        else:
            cody = [pandyi.groupby('code')['code'].first().tolist()]*len(pandyi)
        pandyi = pandyi.assign(code=cody)
        if df.empty:
            df = pandyi
        else:
            df = pd.concat([df,pandyi])

    df = df.drop_duplicates(['date','clustername'])
    pandy = df

    pandy=pandy.copy()
    pandy[pop_field]=pandy[pop_field].replace(0., np.nan)

    if bypop == 'pop':
        pandy.loc[:,val2norm+' per total population']=pandy[val2norm]/pandy[pop_field]*VirusStat.dictbypop()[bypop]
    else:
        pandy.loc[:,val2norm+' per '+bypop + ' population']=pandy[val2norm]/pandy[pop_field]*VirusStat.dictbypop()[bypop]
    return pandy

   def merger(self,**kwargs):
        '''
        Merge two or more pycoa.pandas from get_stats operation
        'src.andas': list (min 2D) of pandas from stats
        '''

        src.andas = kwargs.get('src.andas', None)

        if src.andas is None or not isinstance(src.andas, list) or len(src.andas)<=1:
            raise CoaKeyError('src.andas value must be at least a list of 2 elements ... ')

        def renamecol(pandy):
            torename=['daily','cumul','weekly']
            return pandy.rename(columns={i:self.currentdata.get_available_keywords()+'_'+i  for i in torename})
        base = src.andas[0].copy()
        src.andas = [ renamecol(p) for p in src.andas ]
        base = src.andas[0].copy()
        if not 'clustername' in base.columns:
            raise CoaKeyError('No "clustername" in your pandas columns ... don\'t know what to do ')

        j=1
        for p in src.andas[1:]:
            [ p.drop([i],axis=1, inplace=True) for i in ['where','where','code'] if i in p.columns ]
            #p.drop(['where','code'],axis=1, inplace=True)
            base = pd.merge(base,p,on=['date','clustername'],how="inner")#,suffixes=('', '_drop'))
            #base.drop([col for col in base.columns if 'drop' in col], axis=1, inplace=True)
        return base

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
