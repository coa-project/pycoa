# -*- coding: utf-8 -*-
"""
Project : PyCoA
Date :    april 2020 - june 2024
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
import numpy as np
import pandas as pd
import datetime as dt

from coa.tools import (
    verb,
    kwargs_test,
    flat_list,
    return_nonan_dates_pandas,
)
import coa.geo as coge
import coa.dbparser as dbparser
from coa.dbparser import _db_list_dict
import geopandas as gpd
from coa.error import *
from scipy import stats as sps
import pickle
import os, time
import coa.allvisu as allvisu
import coa.geo as coge
class DataBase(object):
   """
   DataBase class
   Parse a Covid-19 database and filled the pandas python objet : mainpandas
   It takes a string argument, which can be: 'jhu','spf', 'spfnational','owid', 'opencovid19' and 'opencovid19national'
   """
   def __init__(self, db_name):
        """
            Main pycoa class:
            - call the get_parser
            - call the geo
            - call the display
        """
        verb("Init of covid19.DataBase()")
        self.database_type = dbparser._db_list_dict
        self.db = db_name
        self.dbfullinfo = dbparser.DBInfo(db_name)
        self.slocation = self.dbfullinfo.get_locations()
        #self.geo = self.dbfullinfo.get_geo()
        self.db_world = self.dbfullinfo.get_world_boolean()
        self.codisp  = None
        self.iso3country = _db_list_dict[db_name][0]
        self.granularity = _db_list_dict[db_name][1]
        self.namecountry = _db_list_dict[db_name][2]
        self._gi = coge.GeoInfo()

        try:
            if self.granularity != 'nation':
                self.geo = coge.GeoCountry(self.iso3country)
                if self.granularity == 'region':
                    where_kindgeo = self.geo.get_region_list()[['code_region', 'name_region', 'geometry']]
                    where_kindgeo = where_kindgeo.rename(columns={'name_region': 'where'})
                    if self.iso3country == 'PRT':
                         tmp = where_kindgeo.rename(columns={'name_region': 'where'})
                         tmp = tmp.loc[tmp.code_region=='PT.99']
                         self.boundary_metropole =tmp['geometry'].total_bounds
                    if self.iso3country == 'FRA':
                         tmp = where_kindgeo.rename(columns={'name_region': 'where'})
                         tmp = tmp.loc[tmp.code_region=='999']
                         self.boundary_metropole =tmp['geometry'].total_bounds
                elif self.granularity == 'subregion':
                    list_dep_metro = None
                    where_kindgeo = self.geo.get_subregion_list()[['code_subregion', 'name_subregion', 'geometry']]
                    where_kindgeo = where_kindgeo.rename(columns={'name_subregion': 'where'})
            else:
                   self.geo = coge.GeoManager('name')
                   geopan = gpd.GeoDataFrame()#crs="EPSG:4326")
                   info = coge.GeoInfo()
                   allcountries = self.geo.get_GeoRegion().get_countries_from_region('world')
                   geopan['where'] = [self.geo.to_standard(c)[0] for c in allcountries]
                   geopan = info.add_field(field=['geometry'],input=geopan ,geofield='where')
                   geopan = gpd.GeoDataFrame(geopan, geometry=geopan.geometry, crs="EPSG:4326")
                   geopan = geopan[geopan['where'] != 'Antarctica']
                   where_kindgeo = geopan.dropna().reset_index(drop=True)
        except:
            raise CoaTypeError('What data base are you looking for ?')
        self.where_geodescription = where_kindgeo
        #self.set_display(db_name,where_kindgeo,vis)

   def getwheregeometrydescription(self):
        return self.where_geodescription

   def permanentdisplay(self,input):
    '''
     when sumall option is used this method is usefull for the display
     it returns an input with new columns
    '''
    input['permanentdisplay'] = input.codelocation
    if 'codelocation' and 'clustername' not in input.columns:
       input['codelocation'] = input['where']
       input['clustername'] = input['where']
       input['rolloverdisplay'] = input['where']
       input['permanentdisplay'] = input['where']
    else:
       if self.granularity == 'nation' :
           #input['codelocation'] = input['codelocation'].apply(lambda x: str(x).replace('[', '').replace(']', '') if len(x)< 10 else x[0]+'...'+x[-1] )
           ##input['permanentdisplay'] = input.apply(lambda x: x.clustername if self.geo.get_GeoRegion().is_region(x.clustername) else str(x.codelocation), axis = 1)
           input['permanentdisplay'] = input.codelocation
       else:
           if self.granularity == 'subregion' :
               input = input.reset_index(drop=True)

               if isinstance(input['codelocation'].iloc[0],list):
                   input['codelocation'] = input['codelocation'].apply(lambda x: str(x).replace("'", '')\
                                                if len(x)<5 else '['+str(x[0]).replace("'", '')+',...,'+str(x[-1]).replace("'", '')+']')

               trad={}
               cluster = input.clustername.unique()

               if isinstance(input['where'].iloc[0],list):
                  cluster = [i for i in cluster]
               for i in cluster:
                   if i == self.namecountry:
                       input['permanentdisplay'] = input.clustername #[self.dbld[self.database_name][2]]*len(input)
                   else:
                       if self.geo.is_region(i):
                           trad[i] = self.geo.is_region(i)
                       elif self.geo.is_subregion(i):
                           trad[i] = self.geo.is_subregion(i)#input.loc[input.clustername==i]['codelocation'].iloc[0]
                       else:
                           trad[i] = i
                       trad={k:(v[:3]+'...'+v[-3:] if len(v)>8 else v) for k,v in trad.items()}
                       if ',' in input.codelocation[0]:
                           input['permanentdisplay'] = input.clustername
                       else:
                           input['permanentdisplay'] = input.codelocation#input.clustername.map(trad)
           elif self.granularity == 'region' :
               if all(i == self.namecountry for i in input.clustername.unique()):
                   input['permanentdisplay'] = [self.namecountry]*len(input)
               else:
                   input['permanentdisplay'] = input.codelocation
           else :
               CoaError("Sorry but what's the granularity of you DB "+self.granularity)
    input['rolloverdisplay'] = input['where']
    return input


   @staticmethod
   def factory(**kwargs):
       '''
        Return an instance to DataBase and to Display methods
        This is recommended to avoid mismatch in labeled figures
       '''
       db_name = kwargs.get('db_name')
       reload = kwargs.get('reload', True)

       path = ".cache/"
       if not os.path.exists(path):
           os.makedirs(path)
       filepkl = path + db_name + '.pkl'

       if reload:
           datab = DataBase(db_name)
           with open(filepkl, 'wb') as f:
               pickle.dump(datab,f)
       #else:
       #   datab=DataBase.readpekl(filepkl)
       #   print("HERE")
       #if visu:
       visu=True
       datab.set_display(db_name,datab.getwheregeometrydescription())
       if visu:
           return datab, datab.get_display()
       else:
            return datab, None

   def set_display(self,db,wheregeometrydescription):
       ''' Set the Display '''
       self.codisp = allvisu.AllVisu(db, wheregeometrydescription)

   def get_display(self):
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
         datab = DataBase(db_name)
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
       return self.dbfullinfo

   def get_fulldb(self):
      return self.dbfullinfo.get_mainpandas()

   def get_available_database(self):
        '''
        Return all the available Covid19 database
        '''
        return self.database_name

   def get_stats(self,**kwargs):
        '''
        Return the pandas pandas_datase
         - index: only an incremental value
         - location: list of location used in the database selected (using geo standardization)
         - 'which' :  return the keyword values selected from the avalailable keywords keepted seems
            self.dbfullinfo.get_available_keywords()

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

        - a clustername variable is computed

        '''
        option = None
        sumall = None
        wallname = None
        optionskipped=False
        othersinputfieldpandas=pd.DataFrame()
        if 'where' not in kwargs or kwargs['where'] is None.__class__ or kwargs['where'] == None:
            #if self.dbfullinfo.get_dblistdico(self.db)[0] == 'WW':
            #    kwargs['where'] = self.dbfullinfo.get_dblistdico(self.db)[2]
            #else:
            #    kwargs['where'] = self.slocation
            kwargs['where'] = self.dbfullinfo.get_dblistdico(self.db)[2]
            wallname = self.dbfullinfo.get_dblistdico(self.db)[2]
        else:
            kwargs['where'] = kwargs['where']

        wallname = None
        option = kwargs.get('option', 'fillnan')
        fillnan = True # default
        sumall = False # default
        sumallandsmooth7 = False
        if 'input' not in kwargs:
            mypycoapd = self.dbfullinfo.get_mainpandas()
            if 'which' not in kwargs:
                kwargs['which'] = mypycoapd.columns[2]
            #if kwargs['which'] not in self.dbfullinfo.get_available_keywords():
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
                            if dbparser._db_list_dict[self.db][0] in ['USA, FRA, ESP, PRT']:
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
                    if i[0].upper() in [self.database_type[self.db][0].upper(),self.database_type[self.db][2].upper()]:
                        dicooriglist[self.database_type[self.db][0]]=explosion(flat_list(self.slocation),self.database_type[self.db][1])
                    else:
                        dicooriglist[','.join(i)]=explosion(i,self.database_type[self.db][1])
            else:
                if any([i.upper() in [self.dbfullinfo.get_dblistdico(self.db)[0].upper(),self.dbfullinfo.get_dblistdico(self.db)[2].upper()] for i in listloc]):
                    listloc=self.slocation
                listloc = explosion(listloc,self.dbfullinfo.get_dblistdico(self.db)[1])
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

               codescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['codelocation'].unique()) for i in uniqcluster}
               namescluster = {i:list(pdfiltered.loc[pdfiltered.clustername==i]['where'].unique()) for i in uniqcluster}

               tmp['codelocation'] = tmp['clustername'].map(codescluster)
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
                uniqcodeloc = list(pdfiltered.codelocation.unique())
                tmp.loc[:,'where'] = ['dummy']*len(tmp)
                tmp.loc[:,'codelocation'] = ['dummy']*len(tmp)
                tmp.loc[:,'clustername'] = ['dummy']*len(tmp)
                for i in range(len(tmp)):
                    tmp.at[i,'where'] = uniqloc #sticky(uniqloc)
                    tmp.at[i,'codelocation'] = uniqcodeloc #sticky(uniqcodeloc)
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
        pdfiltered = pdfiltered.loc[~(pdfiltered['where'].isna() | pdfiltered['codelocation'].isna())]
        pdfiltered = self.permanentdisplay(pdfiltered)
        return pdfiltered


   def normbypop(self, pandy, val2norm,bypop):
    """
        Return a pandas with a normalisation column add by population
        * can normalize by '100', '1k', '100k' or '1M'
    """
    if pandy.empty:
        raise CoaKeyError('Seems to be an empty field')
    if isinstance(pandy['codelocation'].iloc[0],list):
        pandy = pandy.explode('codelocation')

    if self.db_world == True:
        pop_field='population'
        pandy = self._gi.add_field(input=pandy,field=pop_field,geofield='codelocation')
    else:
        if not isinstance(self._gi,coge.GeoCountry):
            self._gi=None
        else:
            if self._gi.get_country() != self.geo.get_country():
                self._gi=None

        if self._gi == None :
            self._gi = self.geo
        pop_field='population_subregion'
        if pop_field not in self._gi.get_list_properties():
            raise CoaKeyError('The population information not available for this country. No normalization possible')

        pandy=self._gi.add_field(input=pandy,field=pop_field,input_key='codelocation')

    clust = pandy['clustername'].unique()
    df = pd.DataFrame()
    for i in clust:
        pandyi = pandy.loc[ pandy['clustername'] == i ].copy()
        pandyi.loc[:,pop_field] = pandyi.groupby('codelocation')[pop_field].first().sum()
        if len(pandyi.groupby('codelocation')['codelocation'].first().tolist()) == 1:
            cody = pandyi.groupby('codelocation')['codelocation'].first().tolist()*len(pandyi)
        else:
            cody = [pandyi.groupby('codelocation')['codelocation'].first().tolist()]*len(pandyi)
        pandyi = pandyi.assign(codelocation=cody)
        if df.empty:
            df = pandyi
        else:
            df = pd.concat([df,pandyi])

    df = df.drop_duplicates(['date','clustername'])
    pandy = df

    pandy=pandy.copy()
    pandy[pop_field]=pandy[pop_field].replace(0., np.nan)
    av = allvisu.AllVisu()
    _dict_bypop =  av._dict_bypop
    if bypop == 'pop':
        pandy.loc[:,val2norm+' per total population']=pandy[val2norm]/pandy[pop_field]*_dict_bypop[bypop]
    else:
        pandy.loc[:,val2norm+' per '+bypop + ' population']=pandy[val2norm]/pandy[pop_field]*_dict_bypop[bypop]
    return pandy

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
