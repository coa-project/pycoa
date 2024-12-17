# -*- coding: utf-8 -*-
""" Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.geo

About :
-------

Geo classes within the PyCoA framework.

GeoManager class provides translations between naming normalisations
of countries. It's based on the pycountry module.

GeoInfo class allow to add new fields to a pandas DataFrame about
statistical information for countries.

GeoRegion class helps returning list of countries in a specified region

GeoCountry manages information for a single country.
"""

import inspect  # for debug purpose

import warnings

import pycountry as pc
import pycountry_convert as pcc
import pandas as pd
import geopandas as gpd
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so
import bs4
import numpy as np
import io

from src.tools import verb,kwargs_test,get_local_from_url,dotdict,tostdstring
from src.error import *

# ---------------------------------------------------------------------
# --- GeoManager class ------------------------------------------------
# ---------------------------------------------------------------------

class GeoManager():
    """GeoManager class definition. No inheritance from any other class.

    It should raise only CoaError and derived exceptions in case
    of errors (see pycoa.error)
    """

    _list_standard=['iso2',   # Iso2 standard, default
            'iso3',           # Iso3 standard
            'name',           # Standard name ( != Official, caution )
            'num']            # Numeric standard

    _list_db=[None,'jhu','worldometers','owid','opencovid19national','spfnational','mpoxgh','olympics'] # first is default
    _list_output=['list','dict','pandas'] # first is default

    _standard = None # currently used normalisation standard

    def __init__(self,standard=_list_standard[0]):
        """ __init__ member function, with default definition of
        the used standard. To get the current default standard,
        see get_list_standard()[0].
        """
        verb("Init of GeoManager() from "+str(inspect.stack()[1]))
        self.set_standard(standard)
        self._gr=GeoRegion()

    def get_GeoRegion(self):
        """ return the GeoRegion local instance
        """
        return self._gr

    def get_region_list(self):
        """ return the list of region via the GeoRegion instance
        """
        return self._gr.get_region_list()

    def get_list_standard(self):
        """ return the list of supported standard name of countries.
        First one is default for the class
        """
        return self._list_standard

    def get_list_output(self):
        """ return supported list of output type. First one is default
        for the class
        """
        return self._list_output

    def get_list_db(self):
        """ return supported list of database name for translation of
        country names to standard.
        """
        return self._list_db

    def get_standard(self):
        """ return current standard use within the GeoManager class
        """
        return self._standard

    def set_standard(self,standard):
        """
        set the working standard type within the GeoManager class.
        The standard should meet the get_list_standard() requirement
        """
        if not isinstance(standard,str):
            raise CoaTypeError('GeoManager error, the standard argument'
                ' must be a string')
        if standard not in self.get_list_standard():
            raise CoaKeyError('GeoManager.set_standard error, "'+\
                                    standard+' not managed. Please see '\
                                    'get_list_standard() function')
        self._standard=standard
        return self.get_standard()

    def to_standard(self, w, **kwargs):
        """Given a list of string of locations (countries), returns a
        normalised list according to the used standard (defined
        via the setStandard() or __init__ function. Current default is iso2.

        Arguments
        -----------------
        first arg        --  w, list of string of locations (or single string)
                             to convert to standard one

        output           -- 'list' (default), 'dict' or 'pandas'
        db               -- database name to help conversion.
                            Default : None, meaning best effort to convert.
                            Known database : jhu, wordometer...
                            See get_list_db() for full list of known db for
                            standardization
        interpret_region -- Boolean, default=False. If yes, the output should
                            be only 'list'.
        """

        kwargs_test(kwargs,['output','db','interpret_region'],'Bad args used in the to_standard() function.')

        output=kwargs.get('output',self.get_list_output()[0])
        if output not in self.get_list_output():
            raise CoaKeyError('Incorrect output type. See get_list_output()'
                ' or help.')

        db=kwargs.get('db',self.get_list_db()[0])
        if db not in self.get_list_db():
            raise CoaDbError('Unknown database "'+db+'" for translation to '
                'standardized location names. See get_list_db() or help.')

        interpret_region=kwargs.get('interpret_region',False)
        if not isinstance(interpret_region,bool):
            raise CoaTypeError('The interpret_region argument is a boolean, '
                'not a '+str(type(interpret_region)))

        if interpret_region==True and output!='list':
            raise CoaKeyError('The interpret_region True argument is incompatible '
                'with non list output option.')

        if isinstance(w,str):
            w=[w]
        elif not isinstance(w,list):
            raise CoaTypeError('Waiting for str, list of str or pandas'
                'as input of get_standard function member of GeoManager')

        w=[v.title() for v in w] # capitalize first letter of each name

        w0=w.copy()

        if db:
            w=self.first_db_translation(w,db)
        n=[] # will contain standardized name of countries (if possible)

        #for c in w:
        while len(w)>0:
            c=w.pop(0)
            if type(c)==int:
                c=str(c)
            elif type(c)!=str:
                raise CoaTypeError('Locations should be given as '
                    'strings or integers only')
            if (c in self._gr.get_region_list()) and interpret_region == True:
                w=self._gr.get_countries_from_region(c)+w
            else:
                if len(c)==0:
                    n1='' #None
                else:
                    try:
                        n0=pc.countries.lookup(c)
                    except LookupError:
                        try:
                            if c.startswith('Owid_'):
                                nf=['owid_*']
                                n1='OWID_*'
                            else:
                                nf=pc.countries.search_fuzzy(c)
                            if len(nf)>1:
                                warnings.warn('Caution. More than one country match the key "'+\
                                c+'" : '+str([ (k.name+', ') for k in nf])+\
                                ', using first one.\n')
                            n0=nf[0]
                        except LookupError:
                            raise CoaLookupError('No country match the key "'+c+'". Error.')
                        except Exception as e1:
                            raise CoaNotManagedError('Not managed error '+type(e1))
                    except Exception as e2:
                        raise CoaNotManagedError('Not managed error'+type(e1))

                    if n0 != 'owid_*':
                        if self._standard=='iso2':
                            n1=n0.alpha_2
                        elif self._standard=='iso3':
                            n1=n0.alpha_3
                        elif self._standard=='name':
                            n1=n0.name
                        elif self._standard=='num':
                            n1=n0.numeric
                        else:
                            raise CoaKeyError('Current standard is '+self._standard+\
                                ' which is not managed. Error.')

                n.append(n1)

        if output=='list':
            return n
        elif output=='dict':
            return dict(zip(w0, n))
        elif output=='pandas':
            return pd.DataFrame([{'inputname':w0,self._standard:n}])
        else:
            return None # should not be here

    def first_db_translation(self,w,db):
        """ This function helps to translate from country name to
        standard for specific databases. It's the first step
        before final translation.

        One can easily add some database support adding some new rules
        for specific databases
        """
        translation_dict={}
        # Caution : keys need to be in title mode, i.e. first letter capitalized
        if db=='jhu':
            translation_dict.update({\
                "Congo (Brazzaville)":"Republic of the Congo",\
                "Congo (Kinshasa)":"COD",\
                "Korea, South":"KOR",\
                "Taiwan*":"Taiwan",\
                "Laos":"LAO",\
                "West Bank And Gaza":"PSE",\
                "Burma":"Myanmar",\
                "Iran":"IRN",\
                "Diamond Princess":"",\
                "Ms Zaandam":"",\
                "Summer Olympics 2020":"",\
                "Micronesia":"FSM",\
                "Winter Olympics 2022":"",\
                "Antarctica":"",\
                "Korea, North":"PRK",\
                    })  # last two are names of boats
        elif db=='worldometers':
            translation_dict.update({\
                "Dr Congo":"COD",\
                "Congo":"COG",\
                "Iran":"IRN",\
                "South Korea":"KOR",\
                "North Korea":"PRK",\
                "Czech Republic (Czechia)":"CZE",\
                "Laos":"LAO",\
                "Sao Tome & Principe":"STP",\
                "Channel Islands":"JEY",\
                "St. Vincent & Grenadines":"VCT",\
                "U.S. Virgin Islands":"VIR",\
                "Saint Kitts & Nevis":"KNA",\
                "Faeroe Islands":"FRO",\
                "Caribbean Netherlands":"BES",\
                "Wallis & Futuna":"WLF",\
                "Saint Pierre & Miquelon":"SPM",\
                "Sint Maarten":"SXM",\
                "Turkey":"TUR",\
                } )
        elif db=='owid':
            translation_dict.update({\
                    "Bonaire Sint Eustatius And Saba":"BES",\
                    "Cape Verde":"CPV",\
                    "Democratic Republic Of Congo":"COD",\
                    "Faeroe Islands":"FRO",\
                    "Laos":"LAO",\
                    "South Korea":"KOR",\
                    "Swaziland":"SWZ",\
                    "United States Virgin Islands":"VIR",\
                    "Iran":"IRN",\
                    "Micronesia (Country)":"FSM",\
                    "Micronesia (country)":"FSM",\
                    "Northern Cyprus":"CYP",\
                    "Curacao":"CUW",\
                    "Faeroe Islands":"FRO",\
                    "Vatican":"VAT"
                })
        elif db=='olympics':
            translation_dict.update({\
                'RHO':'ZWE',\
                'ANZ':'AUS',\
                'BOH':'CZE',\
                'Tch':'CZE',\
                'Yug':'SRB',\
                'Urs':'RUS',\
                'Lib':'LBN',\
                'Uar':'EGY',\
                'Eun':'RUS',\
                })
        return [translation_dict.get(k,k) for k in w]

# ---------------------------------------------------------------------
# --- GeoInfo class ---------------------------------------------------
# ---------------------------------------------------------------------

class GeoInfo():
    """GeoInfo class definition. No inheritance from any other class.

    It should raise only CoaError and derived exceptions in case
    of errors (see pycoa.error)
    """

    _list_field={\
        'continent_code':'pycountry_convert (https://pypi.org/project/pycountry-convert/)',\
        'continent_name':'pycountry_convert (https://pypi.org/project/pycountry-convert/)' ,\
        'country_name':'pycountry_convert (https://pypi.org/project/pycountry-convert/)' ,\
        'population':'https://www.worldometers.info/world-population/population-by-country/',\
        'area':'https://www.worldometers.info/world-population/population-by-country/',\
        'fertility':'https://www.worldometers.info/world-population/population-by-country/',\
        'median_age':'https://www.worldometers.info/world-population/population-by-country/',\
        'urban_rate':'https://www.worldometers.info/world-population/population-by-country/',\
        #'geometry':'https://github.com/johan/world.geo.json/',\
        'geometry':'http://thematicmapping.org/downloads/world_borders.php and https://github.com/johan/world.geo.json/',\
        'region_code_list':'https://en.wikipedia.org/w/index.php?title=List_of_countries_by_United_Nations_geoscheme&oldid=1008989486',\
        #https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme',\
        'region_name_list':'https://en.wikipedia.org/w/index.php?title=List_of_countries_by_United_Nations_geoscheme&oldid=1008989486',\
        #https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme',\
        'capital':'https://en.wikipedia.org/w/index.php?title=List_of_countries_by_United_Nations_geoscheme&oldid=1008989486',\
        #https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme',\
        'flag':'https://github.com/linssen/country-flag-icons/blob/master/countries.json',\
        }

    _data_geometry = pd.DataFrame()
    _data_population = pd.DataFrame()
    _data_flag = pd.DataFrame()

    def __init__(self,gm=0):
        """ __init__ member function.
        """
        verb("Init of GeoInfo() from "+str(inspect.stack()[1]))
        if gm != 0:
            self._gm=gm
        else:
            self._gm=GeoManager()

        self._grp=self._gm._gr.get_pandas()

    def get_GeoManager(self):
        """ return the local instance of used GeoManager()
        """
        return self._gm

    def get_list_field(self):
        """ return the list of supported additionnal fields available
        """
        return sorted(list(self._list_field.keys()))

    def get_source(self,field=None):
        """ return the source of the information provided for a given
        field.
        """
        if field==None:
            return self._list_field
        elif field not in self.get_list_field():
            raise CoaKeyError('The field "'+str(field)+'" is not '
                'a supported field of GeoInfo(). Please see help or '
                'the get_list_field() output.')
        return field+' : '+self._list_field[field]


    def add_field(self,**kwargs):
        """ this is the main function of the GeoInfo class. It adds to
        the input pandas dataframe some fields according to
        the geofield field of input.
        The return value is the pandas dataframe.

        Arguments :
        field    -- should be given as a string of list of strings and
                    should be valid fields (see get_list_field() )
                    Mandatory.
        input    -- provide the input pandas dataframe. Mandatory.
        geofield -- provide the field name in the pandas where the
                    location is stored. Default : 'where'
        overload -- Allow to overload a field. Boolean value.
                    Default : False
        """

        # --- kwargs analysis ---

        kwargs_test(kwargs,['field','input','geofield','overload'],
            'Bad args used in the add_field() function.')

        p=kwargs.get('input',None) # the panda
        if not isinstance(p,pd.DataFrame):
            raise CoaTypeError('You should provide a valid input pandas'
                ' DataFrame as input. See help.')
        p=p.copy()

        overload=kwargs.get('overload',False)
        if not isinstance(overload,bool):
            raise CoaTypeError('The overload option should be a boolean.')

        fl=kwargs.get('field',None) # field list
        if fl == None:
            raise CoaKeyError('No field given. See help.')
        if not isinstance(fl,list):
            fl=[fl]
        if not all(f in self.get_list_field() for f in fl):
            raise CoaKeyError('All fields are not valid or supported '
                'ones. Please see help of get_list_field()')

        if not overload and not all(f not in p.columns.tolist() for f in fl):
            raise CoaKeyError('Some fields already exist in you panda '
                'dataframe columns. You may set overload to True.')

        geofield=kwargs.get('geofield','where')

        if not isinstance(geofield,str):
            raise CoaTypeError('The geofield should be given as a '
                'string.')
        if geofield not in p.columns.tolist():
            raise CoaKeyError('The geofield "'+geofield+'" given is '
                'not a valid column name of the input pandas dataframe.')

        self._gm.set_standard('iso2')
        countries_iso2=self._gm.to_standard(p[geofield].tolist())
        self._gm.set_standard('iso3')
        countries_iso3=self._gm.to_standard(p[geofield].tolist())

        p['iso2_tmp']=countries_iso2
        p['iso3_tmp']=countries_iso3

        # --- loop over all needed fields ---
        for f in fl:
            if f in p.columns.tolist():
                p=p.drop(f,axis=1)
            # ----------------------------------------------------------
            if f == 'continent_code':
                p[f] = [pcc.country_alpha2_to_continent_code(k) for k in countries_iso2]
            # ----------------------------------------------------------
            elif f == 'continent_name':
                p[f] = [pcc.convert_continent_code_to_continent_name( \
                    pcc.country_alpha2_to_continent_code(k) ) for k in countries_iso2 ]
            # ----------------------------------------------------------
            elif f == 'country_name':
                p[f] = [pcc.country_alpha2_to_country_name(k) for k in countries_iso2]
            # ----------------------------------------------------------
            elif f in ['population','area','fertility','median_age','urban_rate']:
                if self._data_population.empty:

                    field_descr=( (0,'','idx'),
                        (1,'Country','country'),
                        (2,'Population','population'),
                        (6,'Land Area','area'),
                        (8,'Fert','fertility'),
                        (9,'Med','median_age'),
                        (10,'Urban','urban_rate'),
                        ) # containts tuples with position in table, name of column, new name of field

                    # get data with cache ok for about 1 month
                    self._data_population = pd.read_html(get_local_from_url('https://www.worldometers.info/world-population/population-by-country/',30e5) ) [0].iloc[:,[x[0] for x in field_descr]]

                    # test that field order hasn't changed in the db
                    if not all (col.startswith(field_descr[i][1]) for i,col in enumerate(self._data_population.columns) ):
                        raise CoaDbError('The worldometers database changed its field names. '
                            'The GeoInfo should be updated. Please contact developers.')

                    # change field name
                    self._data_population.columns = [x[2] for x in field_descr]

                    # standardization of country name
                    self._data_population['iso3_tmp2']=\
                        self._gm.to_standard(self._data_population['country'].tolist(),\
                        db='worldometers')

                p=p.merge(self._data_population[["iso3_tmp2",f]],how='left',\
                        left_on='iso3_tmp',right_on='iso3_tmp2',\
                        suffixes=('','_tmp')).drop(['iso3_tmp2'],axis=1)
            # ----------------------------------------------------------
            elif f in ['region_code_list','region_name_list']:

                if f == 'region_code_list':
                    ff = 'region'
                elif f == 'region_name_list':
                    ff = 'region_name'

                p[f]=p.merge(self._grp[['iso3',ff]],how='left',\
                    left_on='iso3_tmp',right_on='iso3',\
                    suffixes=('','_tmp')) \
                    .groupby('iso3_tmp')[ff].apply(list).to_list()
            # ----------------------------------------------------------
            elif f in ['capital']:
                p[f]=p.merge(self._grp[['iso3',f]].drop_duplicates(), \
                    how='left',left_on='iso3_tmp',right_on='iso3',\
                    suffixes=('','_tmp'))[f]

            # ----------------------------------------------------------
            elif f == 'geometry':
                if self._data_geometry.empty:
                    #geojsondatafile = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'
                    #self._data_geometry = gpd.read_file(get_local_from_url(geojsondatafile,0,'.json'))[["id","geometry"]]
                    #world_geometry_url_zipfile='http://thematicmapping.org/downloads/TM_WORLD_BORDERS_SIMPL-0.3.zip' # too much simplified version ?
                    world_geometry_url_zipfile='https://github.com/coa-project/coadata/raw/main/coastore/TM_WORLD_BORDERS_SIMPL-0.3.zip' # too much simplified version ?
                    # world_geometry_url_zipfile='http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip' # too precize version ?
                    self._data_geometry = gpd.read_file('zip://'+get_local_from_url(world_geometry_url_zipfile,0,'.zip'))[['ISO3','geometry']]
                    self._data_geometry.columns=["id_tmp","geometry"]

                    # About some countries not properly managed by this database (south and north soudan)
                    self._data_geometry=pd.concat([self._data_geometry,pd.DataFrame({'id_tmp':'SSD','geometry':None},index=[0])],ignore_index=True)
                    #self._data_geometry=self._data_geometry.append({'id_tmp':'SSD','geometry':None},ignore_index=True) # adding the SSD row
                    #self._data_geometry=pd.concat([self._data_geometry,pd.DataFrame({'id_tmp':'SSD','geometry':None})])
                    for newc in ['SSD','SDN']:
                        newgeo=gpd.read_file(get_local_from_url('https://github.com/johan/world.geo.json/raw/master/countries/'+newc+'.geo.json'))
                        poly=newgeo[newgeo.id==newc].geometry.values[0]
                        self._data_geometry.loc[self._data_geometry.id_tmp==newc,'geometry']=gpd.GeoSeries(poly).values

                    # About countries that we artificially put on the east of the map
                    for newc in ['RUS','FJI','NZL','WSM']:
                        poly=self._data_geometry[self._data_geometry.id_tmp==newc].geometry.values[0]
                        poly=so.unary_union(sg.MultiPolygon([sg.Polygon([(x,y) if x>=0 else (x+360,y) for x,y in p.exterior.coords]) for p in poly.geoms]))
                        self._data_geometry.loc[self._data_geometry.id_tmp==newc,'geometry']=gpd.GeoSeries(poly).values

                    # About countries that we artificially put on the west of the map
                    for newc in ['USA']:
                        poly=self._data_geometry[self._data_geometry.id_tmp==newc].geometry.values[0]
                        poly=so.unary_union(sg.MultiPolygon([sg.Polygon([(x-360,y) if x>=0 else (x,y) for x,y in p.exterior.coords]) for p in poly.geoms]))
                        self._data_geometry.loc[self._data_geometry.id_tmp==newc,'geometry']=gpd.GeoSeries(poly).values

                p=p.merge(self._data_geometry,how='left',\
                    left_on='iso3_tmp',right_on='id_tmp',\
                    suffixes=('','_tmp')).drop(['id_tmp'],axis=1)

            # -----------------------------------------------------------
            elif f == 'flag':
                if self._data_flag.empty:
                    self._data_flag = pd.read_json(get_local_from_url('https://github.com/linssen/country-flag-icons/raw/master/countries.json',0))
                    self._data_flag['flag_url']='http:'+self._data_flag['file_url']

                p=p.merge(self._data_flag[['alpha3','flag_url']],how='left',\
                    left_on='iso3_tmp',right_on='alpha3').drop(['alpha3'],axis=1)

        return p.drop(['iso2_tmp','iso3_tmp'],axis=1,errors='ignore')

# ---------------------------------------------------------------------
# --- GeoRegion class -------------------------------------------------
# ---------------------------------------------------------------------

class GeoRegion():
    """GeoRegion class definition. Does not inheritate from any other
    class.

    It should raise only CoaError and derived exceptions in case
    of errors (see pycoa.error)
    """

    _source_dict={"UN_M49":"https://en.wikipedia.org/w/index.php?title=UN_M49&oldid=986603718", # pointing the previous correct ref . https://en.wikipedia.org/wiki/UN_M49",\
        "GeoScheme":"https://en.wikipedia.org/w/index.php?title=List_of_countries_by_United_Nations_geoscheme&oldid=1008989486", #pointing the previous correct ref. https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme",
        "European Union":"https://europa.eu/european-union/about-eu/countries/member-countries_en",
        "G7":"https://en.wikipedia.org/wiki/Group_of_Seven",
        "G8":"https://en.wikipedia.org/wiki/Group_of_Eight",
        "G20":"https://en.wikipedia.org/wiki/G20",
        "G77":"https://www.g77.org/doc/members.html",
        "OECD":"https://en.wikipedia.org/wiki/OECD",
        "BRICS":"https://en.wikipedia.org/wiki/BRICS",
        "CELAC":"https://en.wikipedia.org/wiki/Community_of_Latin_American_and_Caribbean_States",
        "CEDEAO":"https://fr.wikipedia.org/wiki/Communaut%C3%A9_%C3%A9conomique_des_%C3%89tats_de_l%27Afrique_de_l%27Ouest",
        "SADC":"https://en.wikipedia.org/wiki/Southern_African_Development_Community",
        "AMU":"https://en.wikipedia.org/wiki/Arab_Maghreb_Union",
        "CEEAC":"https://fr.wikipedia.org/wiki/Communaut%C3%A9_%C3%A9conomique_des_%C3%89tats_de_l%27Afrique_centrale",
        "EAC":"https://en.wikipedia.org/wiki/East_African_Community",
        "CENSAD":"https://en.wikipedia.org/wiki/Community_of_Sahel%E2%80%93Saharan_States",
        "COMESA":"https://www.worlddata.info/trade-agreements/comesa.php",
        "Commonwealth":"https://en.wikipedia.org/wiki/Member_states_of_the_Commonwealth_of_Nations",
        }

    _region_dict={}
    _p_gs = pd.DataFrame()

    def __init__(self,):
        """ __init__ member function.
        """
        #if 'XK' in self._country_list:
        #    del self._country_list['XK'] # creates bugs in pycountry and is currently a contested country as country


        # --- get the UN M49 information and organize the data in the _region_dict

        verb("Init of GeoRegion() from "+str(inspect.stack()[1]))

        p_m49=pd.read_html(get_local_from_url(self._source_dict["UN_M49"],0))[1]

        p_m49.columns=['code','region_name']
        p_m49['region_name']=[r.split('(')[0].rstrip().title() for r in p_m49.region_name]  # suppress information in parenthesis in region name
        p_m49.set_index('code')

        self._region_dict.update(p_m49.to_dict('split')['data'])
        self._region_dict.update({  "UE":"European Union",
                                    "G7":"G7",
                                    "G8":"G8",
                                    "G20":"G20",
                                    "OECD":"Oecd",
                                    "BRICS":"Brics",
                                    "CELAC":"Celac",
                                    "CEDEAO":"Cedeao",
                                    "AMU":"Amu",
                                    "CEEAC":"Ceeac",
                                    "EAC":"Eac",
                                    "SADC":"Sadc",
                                    "CENSAD":"Censad",
                                    "COMESA":"Comesa",
                                    "G77":"G77",
                                    "CW":"Commonwealth"
                                    })  # add UE for other analysis

        # --- filling cw information
        p_cw=pd.read_html(get_local_from_url('https://en.wikipedia.org/w/index.php?title=Member_states_of_the_Commonwealth_of_Nations&oldid=1090420488'))
        self._cw=[w.split('[')[0] for w in p_cw[0]['Country'].to_list()]   # removing wikipedia notes

        # --- filling celac information
        p_celac=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/Community_of_Latin_American_and_Caribbean_States'),\
                    match='Country')
        self._celac = [p_celac[0].Country.to_list()]

        # --- filling cedeao information
        p_cedeao=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/Economic_Community_of_West_African_States'))
        self._cedeao=["Cabo Verde" if x=="Cape Verde" else "CIV" if x=="Ivory Coast" else x for x in pd.concat([p_cedeao[1][0:-1],p_cedeao[2][0:-1]]).Country.to_list()]

        # --- filling sadc information
        p_sadc=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/Southern_African_Development_Community'))
        self._sadc=["COD" if x == "Democratic Republic of the Congo" else x for x in [w.split('[')[0] for w in p_sadc[2][p_sadc[2].columns[0]].to_list()]]

        # --- filling amu information
        p_amu=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/Arab_Maghreb_Union'))
        self._amu=p_amu[2].Country.to_list()[0:-1]

        # --- filling ceeac information
        p_ceeac=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/Economic_Community_of_Central_African_States'))
        self._ceeac=["COD" if w == "Democratic Republic of the Congo" else w for w in [x.split('[')[0] for x in p_ceeac[3].Country.to_list()]]

        # --- filling eac information
        p_eac=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/East_African_Community'))
        self._eac=["COD" if x == "DR Congo" else x for x in p_eac[1].Country.to_list()[0:-1]]

        # --- filling censad information
        p_censad=pd.read_html(get_local_from_url('https://en.wikipedia.org/wiki/Community_of_Sahel%E2%80%93Saharan_States'))
        self._censad=["Cabo Verde" if x == "Cape Verde" else "CIV" if x == "Ivory Coast" else x.split('[')[0] for x in p_censad[3][p_censad[3].columns[0]].to_list()[0:-1]]

        # --- filing comesa information
        p_comesa=pd.read_html(get_local_from_url('https://www.worlddata.info/trade-agreements/comesa.php'))
        self._comesa=["COD" if x == "Congo (Dem. Republic)" else x for x in p_comesa[0].Country.to_list()]

        # --- get the UnitedNation GeoScheme and organize the data
        p_gs=pd.read_html(get_local_from_url(self._source_dict["GeoScheme"],0))[0]
        p_gs.columns=['country','capital','iso2','iso3','num','m49']
        p_gs=pd.concat([p_gs,pd.DataFrame({'country':'Taiwan','iso2':'TW','iso3':'TWN','num':'158','m49':'030 < 0142 < 001'},index=[0])],ignore_index=True)
        #p_gs=p_gs.append({'country':'Taiwan','iso2':'TW','iso3':'TWN','num':'158','m49':'030 < 0142 < 001'},ignore_index=True)

        idx=[]
        reg=[]
        cap=[]

        for index, row in p_gs.iterrows():
            if row.iso3 != '–' : # meaning a non standard iso in wikipedia UN GeoScheme
                for r in row.m49.replace(" ","").split('<'):
                    idx.append(row.iso3)
                    reg.append(int(r))
                    cap.append(row.capital)
        self._p_gs=pd.DataFrame({'iso3':idx,'capital':cap,'region':reg})
        self._p_gs=self._p_gs.merge(p_m49,how='left',left_on='region',\
                            right_on='code').drop(["code"],axis=1)

    def get_source(self):
        return self._source_dict

    def get_region_list(self):
        return list(self._region_dict.values())

    def is_region(self,region):
        """ it returns either False or the correctly named region name
        """
        if type(region) != str:
            raise CoaKeyError("The given region is not a str type.")

        region=region.title()  # if not properly capitalized

        if region not in self.get_region_list():
            return False
        else :
            return region

    def get_countries_from_region(self,region):
        """ it returns a list of countries for the given region name.
        The standard used is iso3. To convert to another standard,
        use the GeoManager class.
        """
        r = self.is_region(region)
        if not r:
            raise CoaKeyError('The given region "'+str(region)+'" is unknown.')
        region=r

        clist=[]

        if region=='European Union':
            clist=['AUT','BEL','BGR','CYP','CZE','DEU','DNK','EST',\
                        'ESP','FIN','FRA','GRC','HRV','HUN','IRL','ITA',\
                        'LTU','LUX','LVA','MLT','NLD','POL','PRT','ROU',\
                        'SWE','SVN','SVK']
        elif region=='G7':
            clist=['DEU','CAN','USA','FRA','ITA','JPN','GBR']
        elif region=='G8':
            clist=['DEU','CAN','USA','FRA','ITA','JPN','GBR','RUS']
        elif region=='G20':
            clist=['ZAF','SAU','ARG','AUS','BRA','CAN','CHN','KOR','USA',\
                'IND','IDN','JPN','MEX','GBR','DEU','FRA','ITA','TUR',\
                'MEX','RUS']
        elif region=='Oecd': # OCDE in french
            clist=['DEU','AUS','AUT','BEL','CAN','CHL','COL','KOR','DNK',\
                'ESP','EST','USA','FIN','FRA','GRC','HUN','IRL','ISL','ISR',\
                'ITA','JPN','LVA','LTU','LUX','MEX','NOR','NZL','NLD','POL',\
                'PRT','SVK','SVN','SWE','CHE','GBR','CZE','TUR']
        elif region=='G77':
            clist=['AFG','DZA','AGO','ATG','ARG','AZE','BHS','BHR','BGD','BRB','BLZ',
                'BEN','BTN','BOL','BWA','BRA','BRN','BFA','BDI','CPV','KHM','CMR',
                'CAF','TCD','CHL','CHN','COL','COM','COG','CRI','CIV','CUB','PRK',
                'COD','DJI','DMA','DOM','ECU','EGY','SLV','GNQ','ERI','SWZ','ETH',
                'FJI','GAB','GMB','GHA','GRD','GTM','GIN','GNB','GUY','HTI','HND',
                'IND','IDN','IRN','IRQ','JAM','JOR','KEN','KIR','KWT','LAO','LBN',
                'LSO','LBR','LBY','MDG','MWI','MYS','MDV','MLI','MHL','MRT','MUS',
                'FSM','MNG','MAR','MOZ','MMR','NAM','NRU','NPL','NIC','NER','NGA',
                'OMN','PAK','PAN','PNG','PRY','PER','PHL','QAT','RWA','KNA','LCA',
                'VCT','WSM','STP','SAU','SEN','SYC','SLE','SGP','SLB','SOM','ZAF',
                'SSD','LKA','PSE','SDN','SUR','SYR','TJK','THA','TLS','TGO','TON',
                'TTO','TUN','TKM','UGA','ARE','TZA','URY','VUT','VEN','VNM','YEM',
                'ZMB','ZWE']

        elif region=='Commonwealth':
            clist=self._cw
        elif region=='Celac':
            clist=self._celac
        elif region=='Cedeao':
            clist=self._cedeao
        elif region=='Sadc':
            clist=self._sadc
        elif region=='Amu':
            clist=self._amu
        elif region=='Ceeac':
            clist=self._ceeac
        elif region=='Eac':
            clist=self._eac
        elif region=='Censad':
            clist=self._censad
        elif region=='Comesa':
            clist=self._comesa
        elif region=='Brics':
            clist=['BRA','RUS','IND','CHN','ZAF']
        else:
            clist=self._p_gs[self._p_gs['region_name']==region]['iso3'].to_list()

        return sorted(clist)

    def get_pandas(self):
        return self._p_gs


# ---------------------------------------------------------------------
# --- GeoCountryclass -------------------------------------------------
# ---------------------------------------------------------------------

class GeoCountry():
    """GeoCountry class definition.
    This class provides functions for specific countries and their states / departments / regions,
    and their geo properties (geometry, population if available, etc.)

    The list of supported countries is given by get_list_countries() function. """

    # Assuming zip file here
    _country_info_dict = {'FRA':'https://data.opendatasoft.com/explore/dataset/georef-france-departement@public/download/?format=geojson&timezone=Europe/Berlin&lang=fr',\
                    #previously https://github.com/coa-project/coadata/raw/main/coastore/public.opendatasoft.com_912711563.zip',\
                    #'USA':'https://alicia.data.socrata.com/api/geospatial/jhnu-yfrj?method=export&format=Original',\
                    'USA':'https://github.com/coa-project/coadata/raw/main/coacache/alicia.data.socrata.com_3337537769.zip',\
                    'ITA':'https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson',\
                    'IND':'https://raw.githubusercontent.com/deldersveld/topojson/master/countries/india/india-states.json',\
                    'DEU':'https://github.com/jgehrcke/covid-19-germany-gae/raw/master/geodata/DE-counties.geojson',\
                    #'ESP':'https://public.opendatasoft.com/explore/dataset/provincias-espanolas/download/?format=shp&timezone=Europe/Berlin&lang=en',\
                    'ESP':'https://github.com/coa-project/coadata/raw/main/coacache/public.opendatasoft.com_598837822.zip',\
                    # missing some counties 'GBR':'https://opendata.arcgis.com/datasets/69dc11c7386943b4ad8893c45648b1e1_0.zip?geometry=%7B%22xmin%22%3A-44.36%2C%22ymin%22%3A51.099%2C%22xmax%22%3A39.487%2C%22ymax%22%3A59.78%2C%22type%22%3A%22extent%22%2C%22spatialReference%22%3A%7B%22wkid%22%3A4326%7D%7D&outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D',\
                    'GBR':'https://github.com/coa-project/coadata/raw/main/coastore/opendata.arcgis.com_3256063640',\
                    # previously (but broken) : https://opendata.arcgis.com/datasets/3a4fa2ce68f642e399b4de07643eeed3_0.geojson',\
                    'BEL':'https://github.com/coa-project/coadata/raw/main/coacache/public.opendatasoft.com_537867990.zip',\
# previously (but not all regions now) 'https://public.opendatasoft.com/explore/dataset/arrondissements-belges-2019/download/?format=shp&timezone=Europe/Berlin&lang=en',\
                    'PRT':'https://github.com/coa-project/coadata/raw/main/coastore/concelhos.zip',\
                    # (simplification of 'https://github.com/coa-project/coadata/raw/main'https://dados.gov.pt/en/datasets/r/59368d37-cbdb-426a-9472-5a04cf30fbe4',\
                    'MYS':'https://stacks.stanford.edu/file/druid:zd362bc5680/data.zip',\
                    'CHL':'http://geonode.meteochile.gob.cl/geoserver/wfs?format_options=charset%3AUTF-8&typename=geonode%3Adivision_comunal_geo_ide_1&outputFormat=SHAPE-ZIP&version=1.0.0&service=WFS&request=GetFeature',\
                    'EUR':'https://github.com/coa-project/coadata/raw/main/coastore/WHO_EUROsmall2.json',\
                    'GRC':'https://geodata.gov.gr/dataset/6deb6a12-1a54-41b4-b53b-6b36068b8348/resource/3e571f7f-42a4-4b49-8db0-311695d72fa3/download/nomoiokxe.zip',\
                    'JPN':'https://raw.githubusercontent.com/piuccio/open-data-jp-prefectures-geojson/master/output/prefectures.geojson',\
                    }

    _source_dict = {'FRA':{'Basics':_country_info_dict['FRA'],\
                    'Subregion Flags':'http://sticker-departement.com/',\
                    'Region Flags':'https://fr.wikipedia.org/w/index.php?title=R%C3%A9gion_fran%C3%A7aise&oldid=177269957',\
                    'Population':'https://github.com/coa-project/coadata/raw/main/coastore/www.insee.fr_3658796960',\
                    # previously (but sometimes broken : 'https://www.insee.fr/fr/statistiques/4989753?sommaire=4989761'
                    },\
                    'USA':{'Basics':_country_info_dict['USA'],\
                    'Subregion informations':'https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States'},\
                    'ITA':{'Basics':_country_info_dict['ITA']},\
                    'IND':{'Basics':_country_info_dict['IND']},\
                    'DEU':{'Basics':_country_info_dict['DEU']},\
                    'ESP':{'Basics':_country_info_dict['ESP']},\
                    'GBR':{'Basics':_country_info_dict['GBR'],'Regions':'http://geoportal1-ons.opendata.arcgis.com/datasets/0c3a9643cc7c4015bb80751aad1d2594_0.csv'},\
                    'BEL':{'Basics':_country_info_dict['BEL']},\
                    'PRT':{'Basics':_country_info_dict['PRT']},\
                    #,'District':'https://raw.githubusercontent.com/JoaoFOliveira/portuguese-municipalities/master/municipalities.json'},\
                    'MYS':{'Basics':_country_info_dict['MYS']},\
                    'CHL':{'Basics':_country_info_dict['CHL']},\
                    'EUR':{'Basics':_country_info_dict['EUR']},\
                    'GRC':{'Basics':_country_info_dict['GRC']},\
                    'JPN':{'Basics':_country_info_dict['JPN']},\
                    }

    def __init__(self,country=None):

        """ __init__ member function.
        Must give as arg the country to deal with, as a valid ISO3 string.
        """

        self._country=country
        if country == None:
            return None

        if not country in self.get_list_countries():
            raise CoaKeyError("Country "+str(country)+" not supported. Please see get_list_countries() and help. ")

        self._country_data_region=None
        self._country_data_subregion=None
        self._municipality_region=None
        self._is_dense_geometry=False
        self._is_exploded_geometry=False
        self._is_main_geometry=False

        url=self._country_info_dict[country]
        # country by country, adapt the read file informations

        # --- 'FRA' case ---------------------------------------------------------------------------------------
        if self._country=='FRA':
            #self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip'))
            self._country_data = gpd.read_file(get_local_from_url(url,0))

            # adding a flag for subregion (departements)
            self._country_data['flag_subregion']=self._source_dict['FRA']['Subregion Flags']+'img/dept/sticker_plaque_immat_'+\
                self._country_data['dep_code']+'_'+\
                [n.lower() for n in self._country_data['dep_name']]+'_moto.png' # picture of a sticker for motobikes, not so bad...

            # Reading information to get region flags and correct names of regions
            f_reg_flag=open(get_local_from_url(self._source_dict['FRA']['Region Flags'],0), 'r', encoding="utf8")

            content_reg_flag = f_reg_flag.read()
            f_reg_flag.close()
            soup_reg_flag = bs4.BeautifulSoup(content_reg_flag,'lxml')
            for img in soup_reg_flag.find_all('img'):  # need to convert <img tags to src content for pandas_read
                src=img.get('src')
                if src[0] == '/':
                    src='http:'+src
                img.replace_with(src)

            tabs_reg_flag=pd.read_html(io.StringIO(str(soup_reg_flag))) # pandas read the modified html
            metropole=tabs_reg_flag[5][["Logo","Dénomination","Code INSEE[5]"]]  # getting 5th table, and only usefull columns
            ultramarin=tabs_reg_flag[6][["Logo","Dénomination","Code INSEE[5]"]] # getting 6th table
            p_reg_flag=pd.concat([metropole,ultramarin]).rename(columns={"Code INSEE[5]":"code_region",\
                                                                        "Logo":"flag_region",\
                                                                        "Dénomination":"name_region"})

            p_reg_flag=p_reg_flag[pd.notnull(p_reg_flag["code_region"])]  # select only valid rows
            p_reg_flag["name_region"]=[ n.split('[')[0] for n in p_reg_flag["name_region"] ] # remove footnote [k] index from wikipedia
            p_reg_flag["code_region"]=[ str(int(c)).zfill(2) for c in p_reg_flag["code_region"] ] # convert to str for merge the code, adding 1 leading 0 if needed

            self._country_data=self._country_data.merge(p_reg_flag,how='left',\
                    left_on='reg_code',right_on='code_region') # merging with flag and correct names
            # standardize name for region, subregion
            self._country_data.rename(columns={\
                'dep_code':'code_subregion',\
                'dep_name':'name_subregion',\
                #'nom_chf':'town_subregion',\
                },inplace=True)

            # adding population information (departements)
            pop_fra = pd.read_html(get_local_from_url(self._source_dict['FRA']['Population']))[0]
            pop_fra['population_subregion']=pop_fra['Population municipale'].str.replace(r"[ \xa0]","",regex=True).astype(int)
            # En l'absence de Mayotte dans ce document, car le recensement n'a pas eu lieu en phase, ajout à la main
            # En référence à la page pour Mayotte : https://www.insee.fr/fr/statistiques/3291775?sommaire=2120838
            mayotte_df=pd.DataFrame([{'Code département':'976','population_subregion':256518}])
            pop_fra=pd.concat([pop_fra,mayotte_df])
            #pop_fra=pop_fra.append(mayotte_df)
            # Pour les collectivités d'Outremer : https://www.insee.fr/fr/statistiques/4989739?sommaire=4989761
            com_df=pd.DataFrame([{'Code département':'980','population_subregion':(5985+10124+34065+281674+12067)}])
            pop_fra=pd.concat([pop_fra,com_df]).reset_index()
            #pop_fra=pop_fra.append(com_df).reset_index()
            geo_com=self._country_data[self._country_data.code_subregion.isin(['975','977','978','986','987'])][['geometry']]
            geo_com['smthing']=0
            geo_com=geo_com.dissolve(by='smthing')['geometry']
            self._country_data=pd.concat([self._country_data,\
            pd.DataFrame([{'code_subregion':'980','name_subregion':'Collectivités d\'outre-mer','code_region':'09','name_region':'Collectivités d\'outre-mer','geometry':geo_com.values[0]}])],ignore_index=True)
            #self._country_data=self._country_data.append(
            #    pd.DataFrame([{'code_subregion':'980','name_subregion':'Collectivités d\'outre-mer','code_region':'09','name_region':'Collectivités d\'outre-mer','geometry':geo_com.values[0]}])).reset_index()
            # Merging
            #self._country_data=self._country_data.append(
            #    pd.DataFrame([{'code_subregion':'980','name_subregion':'Collectivités d\'outre-mer','code_region':'09','name_region':'Collectivités d\'outre-mer','geometry':geo_com.values[0]}])).reset_index()
            # Merging
            self._country_data=self._country_data.merge(pop_fra,left_on='code_subregion',right_on='Code département')
            self._country_data=self._country_data[['geometry','code_subregion','name_subregion','flag_subregion','code_region','name_region','population_subregion']]
            #if needed, define translation for dense geometry
            self._list_translation={'971':(63,23),   # Guadeloupe
                     '972':(63,23), # Martinique
                     '973':(50,35), # Guyane
                     '974':(-51,60), # Réunion
                     '976':(-38,51.5)}  # Mayotte

        # --- 'USA' case ---------------------------------------------------------------------------------------
        elif self._country == 'USA':
            self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip')) # under the hypothesis this is a zip file
            self._country_data.rename(columns={\
                'STATE_NAME':'name_subregion',\
                'STATE_ABBR':'code_subregion',\
                'SUB_REGION':'code_region'},\
                inplace=True)
            self._country_data['name_region'] = self._country_data['code_region']
            self._country_data.drop(['DRAWSEQ','STATE_FIPS'],axis=1,inplace=True)

            # Adding informations from wikipedia
            f_us=open(get_local_from_url(self._source_dict['USA']['Subregion informations'],0), 'r')
            content_us = f_us.read()
            f_us.close()
            soup_us = bs4.BeautifulSoup(content_us,'lxml')
            for img in soup_us.find_all('img'):  # need to convert <img tags to src content for pandas_read
                src=img.get('src')
                if src[0] == '/':
                    src='http:'+src
                img.replace_with(src)

            h_us=pd.read_html(str(soup_us)) # pandas read the modified html
            h_us=h_us[1][h_us[1].columns[[0,1,2,5,7]]]
            h_us.columns=['flag_subregion','code_subregion','town_subregion','population_subregion','area_subregion']
            h_us['flag_subregion'] = [ h.split('\xa0')[0] for h in h_us['flag_subregion'] ]
            self._country_data=self._country_data.merge(h_us,how='left',on='code_subregion')

            # if needed, define some variable for dense / main geometry
            self._list_translation={"AK":(40,-40),"HI":(60,0)}
            self._list_scale={"AK":0.4,"HI":1}
            self._list_center={"AK":(-120,25),"HI":(-130,25)}

        # --- 'ITA' case ---------------------------------------------------------------------------------------
        elif self._country == 'ITA':
            self._country_data = gpd.read_file(get_local_from_url(url,0)) # this is a geojson file
            self._country_data.rename(columns={\
                'prov_name':'name_subregion',\
                'prov_acr':'code_subregion',\
                'reg_name':'name_region',\
                'reg_istat_code':'code_region',\
                },
                inplace=True)
            self._country_data['name_region'] = self._country_data['name_region'].replace({
            'Valle d\'Aosta/Vallée d\'Aoste':'Valle d\'Aosta',
            'Trentino-Alto Adige/Südtirol':'Trentino-Alto Adige', 'Friuli-Venezia Giulia':'Friuli Venezia Giulia'})
            self._country_data.drop(['prov_istat_code_num','reg_istat_code_num','prov_istat_code'],axis=1,inplace=True)

        # --- 'IND' case ---------------------------------------------------------------------------------------
        elif self._country == 'IND':
            self._country_data = gpd.read_file(get_local_from_url(url,0)) # this is a geojson file
            self._country_data.rename(columns={\
                'NAME_1':'name_subregion',\
                'VARNAME_1':'variationname',\
                'HASC_1':'code_subregion',\
                },
                inplace=True)
            self._country_data['name_subregion']= self._country_data['name_subregion'].replace('Orissa','Odisha')
            variationname=self._country_data['variationname'].to_list()
            name_subregion=self._country_data['name_subregion'].to_list()
            alllocationvariation=[ i+'|'+j if j != '' else i for i,j in zip(name_subregion,variationname)]
            self._country_data['variation_name_subregion'] = self._country_data['name_subregion'].\
                    replace(name_subregion,alllocationvariation)
            self._country_data['name_region'] = self._country_data['name_subregion']
            self._country_data['code_region'] = self._country_data['code_subregion']
            self._country_data.drop(['ISO','NAME_0','ID_1','TYPE_1','ENGTYPE_1','id'],axis=1,inplace=True)

        # --- 'DEU' case ---------------------------------------------------------------------------------------
        elif self._country == 'DEU':
            self._country_data = gpd.read_file(get_local_from_url(url,0)) # this is a geojson file
            self._country_data.rename(columns={\
                'GEN':'name_subregion',\
                'AGS':'code_subregion',\
                },
                inplace=True)
            # See https://www.ioer-monitor.de/en/methodology/glossary/o/official-municipality-key-ags/ for decoding information of region code
            self._country_data['code_region'] = (self._country_data.code_subregion.astype(int)//1000).astype(str).str.zfill(2)
            h_deu=pd.read_html(get_local_from_url('https://de.zxc.wiki/wiki/Amtlicher_Gemeindeschl%C3%BCssel',0))[3]
            h_deu['id']=h_deu['#'].str.slice(stop=2)
            h_deu['name_region']=h_deu['country']
            self._country_data=self._country_data.merge(h_deu,how='left',left_on='code_region',right_on='id')
            self._country_data['code_subregion']=self._country_data.code_subregion.astype(int).astype(str)
            self._country_data=self._country_data[['name_subregion','code_subregion','name_region','code_region','geometry']]
            disso = self._country_data[['name_subregion','geometry']].dissolve(by='name_subregion', aggfunc='sum').reset_index()
            # aggregate geometry with the same subregion name # some code subregion is lost somehow
            self._country_data = self._country_data.drop_duplicates(subset = ['name_subregion'])
            self._country_data = pd.merge(self._country_data.drop(columns=['geometry']),disso, on='name_subregion')

        # --- 'ESP' case ---------------------------------------------------------------------------------------
        elif self._country == 'ESP':
            self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip'),encoding='utf-8') # this is shapefile file
            self._country_data.rename(columns={\
                'ccaa':'name_region',\
                'cod_ccaa':'code_region',\
                'provincia':'name_subregion',\
                'codigo':'code_subregion'},inplace=True)
            self._country_data.drop(['texto'],axis=1,inplace=True)

        # --- 'GBR' case ---------------------------------------------------------------------------------------
        elif self._country == 'GBR':
            self._country_data = gpd.read_file(get_local_from_url(url,0))
            reg_england=pd.read_csv(get_local_from_url(self._source_dict['GBR']['Regions'],0))
            reg_adding_dict={
                'E07000245':('E12000006','East of England'), # West Suffolk in East of England
                'E07000244':('E12000006','East of England'), # East Suffolk in East of England
                'E06000059':('E12000009','South West'), # Dorset in South West
                'E06000058':('E12000009','South West'), # Bournemouth, Christchurch and Poole in South West
                'E07000246':('E12000009','South West'), # Somerset West and Taunton in South West
            }
            for k,v in reg_adding_dict.items():
                reg_england=pd.concat([reg_england,pd.DataFrame.from_records([{'LAD18CD':k,'RGN18CD':v[0],'RGN18NM':v[1]}])],ignore_index=True)

            self._country_data=self._country_data.merge(reg_england,how='left',left_on='lad19cd',right_on='LAD18CD')
            self._country_data.rename(columns={\
                'lad19nm':'name_subregion',\
                'lad19cd':'code_subregion',\
                'RGN18CD':'code_region',\
                'RGN18NM':'name_region',\
                },inplace=True)
            self._country_data.loc[self._country_data.code_region.isnull(),'code_region'] = \
                self._country_data[self._country_data.code_region.isnull()].code_subregion.str.slice(stop=1)
            dict_region={\
                'E':'England',\
                'W':'Wales',\
                'S':'Scotland',\
                'N':'Northern Ireland'\
                }
            self._country_data.loc[self._country_data.code_region.isin(list(dict_region.keys())),'name_region'] = \
                [dict_region[x] for x in self._country_data.code_region if x in list(dict_region.keys())]
            self._country_data=self._country_data[['name_subregion','code_subregion','geometry','code_region','name_region']]
            # modifying projection
            self._country_data['geometry']=self._country_data.geometry.to_crs('epsg:4326')
        # --- 'BEL' case --------------------------------------------------------------------------------------------
        elif self._country == 'BEL':
            self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip'),encoding='utf-8') # this is shapefile file
            self._country_data = self._country_data.where(pd.notnull(self._country_data), None) # to solve the issue https://github.com/geopandas/geopandas/issues/2783
            self._country_data.rename(columns={\
                'nom_arrondi':'name_subregion',\
                'niscode':'code_subregion',\
                'prov_code':'code_region'},inplace=True)
            p=[]

            for index,row in self._country_data.iterrows():
                if row.prov_name_n is not None:
                    p0=row.prov_name_n
                elif row.prov_name_f is not None:
                    p0=row.prov_name_f
                else:
                    p0=row.region
                p0=str(p0).title().replace(' ','').replace('(Le)','').replace('(La)','').replace('-','')
                if p0=='RégionDeBruxellesCapitale':
                    p0='Brussels'
                if p0=='Henegouwen':
                    p0='Hainaut'
                p.append(p0)
            self._country_data['name_region']=p
            self._country_data.loc[self._country_data.code_region.isnull(),'code_region']='00000'
            self._country_data=self._country_data[['name_subregion','code_subregion','name_region','code_region','geometry']]
            self._country_data['geometry']=self._country_data.geometry.to_crs('epsg:4326')
        # --- 'PRT' case --------------------------------------------------------------------------------------------
        elif self._country == 'PRT':
            self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip'),encoding='utf-8')
            #self._district=pd.read_json(self._source_dict['PRT']['District'])[['name','district']].dropna()

            self._country_data.rename(columns={\
                'NAME_2':'name_subregion',\
                'NAME_1':'name_region',\
                'HASC_2':'code_subregion'},inplace=True)
            self._country_data['code_region']=self._country_data.code_subregion.str.slice(stop=5)
            self._country_data=self._country_data[['name_subregion','code_subregion','name_region','code_region','geometry']]
        # --- 'MYS' case --------------------------------------------------------------------------------------------
        elif self._country == 'MYS':
            self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip')).dissolve(by='nam').reset_index()
            self._country_data['name_subregion']=[n.title() for n in self._country_data.nam]
            self._country_data['code_subregion']=self._country_data.name_subregion
            self._country_data['code_region']='MYS'
            self._country_data['name_region']='Malaysia'
            self._country_data['code_subregion']=self._country_data.code_subregion
            # to help the join procedure with current covid data, some translation
            dict_subregion={\
                'Wilayah Persekutuan Labuan':'W.P. Labuan',\
                'Wilayah Persekutuan':'W.P. Kuala Lumpur',\
                }
            self._country_data.loc[self._country_data.code_subregion.isin(list(dict_subregion.keys())),'code_subregion'] = \
                [dict_subregion[x] for x in self._country_data.code_subregion if x in list(dict_subregion.keys())]
            self._country_data=self._country_data[['name_subregion','code_subregion','name_region','code_region','geometry']]
        # --- 'CHL' case --------------------------------------------------------------------------------------------
        elif self._country == 'CHL':
            self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip'),encoding='utf-8')
            self._country_data.rename(columns={\
                'NOM_REG':'name_region',\
                'NOM_COM':'name_subregion'},inplace=True)
            self._country_data['code_subregion']=[str(c).zfill(5) for c in self._country_data.COD_COMUNA]
            self._country_data['code_region']=self._country_data.code_subregion.str.slice(stop=2)
            self._country_data=self._country_data[['name_subregion','code_subregion','name_region','code_region','geometry']]

        # --- 'EUR' case, which is a pseudo country for Europe ---------------------------------------------------------
        elif self._country == 'EUR':
            self._country_data=gpd.read_file(get_local_from_url(url,0))
            self._country_data.rename(columns={\
                'UID':'code_subregion',\
                'RegionName':'name_subregion',\
                'ADM0_ISO3':'code_region',\
                'ADM0_NAME':'name_region',\
                'Population':'population_subregion'},inplace=True)
            self._country_data=self._country_data[['name_subregion','code_subregion','population_subregion','name_region','code_region','geometry']]
            self._country_data.loc[self._country_data.geometry.is_empty,'geometry']=None
            # self._country_data=self._country_data[self._country_data.geometry!=None] to remove subregion without geometry

        # --- 'GRC' case ------------------------------------------------------------------------------------------------
        elif self._country == 'GRC':
            self._country_data=gpd.read_file('zip://'+get_local_from_url(url,0,'.zip')+'!nomoi_okxe',encoding='ISO-8859-7')
            self._country_data.rename(columns={\
                'POP':'population_subregion'},inplace=True)
            self._country_data['name_subregion']=self._country_data.NAME_GR.astype(str).str.slice(start=3)
            self._country_data['code_subregion']=self._country_data.PARENT.astype(str).str.slice(stop=2)
            self._country_data['name_region']=self._country_data['name_subregion']
            self._country_data['code_region']=self._country_data['code_subregion'] # no region info
            self._country_data=self._country_data[['name_subregion','code_subregion','population_subregion','name_region','code_region','geometry']]
            self._country_data=self._country_data.to_crs(epsg=4326)
            # Merge region to fit with the CSV epidemiological data
            ath=['ΔΥΤΙΚΗΣ ΑΤΤΙΚΗΣ', 'ΑΝΑΤΟΛΙΚΗΣ ΑΤΤΙΚΗΣ', 'ΠΕΙΡΑΙΩΣ ΚΑΙ ΝΗΣΩΝ','ΑΘΗΝΩΝ']
            self._country_data.loc[(self._country_data.name_subregion=='ΑΘΗΝΩΝ'),['geometry','population_subregion']]=\
                    self._country_data.loc[self._country_data.name_subregion.isin(ath)].dissolve(aggfunc='sum').values
            self._country_data = self._country_data.loc[~self._country_data.name_subregion.isin(ath[:-1])]
            changename={'Ο ΟΡΟΣ':'ΑΓΙΟ ΟΡΟΣ','ΑΘΗΝΩΝ':'ΑΤΤΙΚΗΣ'}
            self._country_data['name_subregion'].replace(changename, inplace=True)
            self._country_data['name_region'].replace(changename, inplace=True)

        #--- 'JPN' case ----------------------------------------------------------------------------------------
        elif self._country == 'JPN':
            self._country_data = gpd.read_file('https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson')
            np_name_subregion_jpn = np.array(['Hokkaido', 'Aomori', 'Iwate', 'Miyagi', 'Akita',\
                                              'Yamagata', 'Fukushima', 'Ibaraki', 'Tochigi',\
                                              'Gunma', 'Saitama','Chiba', 'Tokyo', 'Kanagawa',\
                                              'Niigata', 'Toyama', 'Ishikawa', 'Fukui','Yamanashi',\
                                              'Nagano', 'Gifu', 'Shizuoka', 'Aichi', 'Mie', 'Shiga',\
                                              'Kyoto', 'Osaka', 'Hyogo', 'Nara', 'Wakayama', 'Tottori',\
                                              'Shimane','Okayama', 'Hiroshima', 'Yamaguchi', 'Tokushima',\
                                              'Kagawa', 'Ehime','Kochi', 'Fukuoka', 'Saga', 'Nagasaki',\
                                              'Kumamoto', 'Oita', 'Miyazaki','Kagoshima', 'Okinawa'])
            np_town_subregion_jpn = np.array(['Sapporo','Aomori','Morioka','Sendai','Akita',\
                                              'Yamagata','Fukushima','Mito','Utsunomiya','Maebashi',\
                                              'Saitama','Chiba','Shinjuku','Yokohama','Niigata','Toyama',\
                                              'Kanazawa','Fukui','Kofu','Nagano','Gifu','Shizuoka',\
                                              'Nagoya','Tsu','Otsu','Kyoto','Osaka','Kobe','Nara','Wakayama','Tottori',\
                                              'Matsue','Okayama','Hiroshima','Yamaguchi','Tokushima','Takamatsu',\
                                              'Matsuyama','Kochi','Fukuoka','Saga','Nagasaki','Kumamoto','Oita',\
                                              'Miyazaki','Kagoshima','Naha'])
            np_name_region_jpn = np.array(['Hokkaido']+ 6*['Tohoku'] + 7*['Kanto'] + 9*['Chubu'] + 5*['Chugoku'] + 4*['Shikoku'] + 7*['Kansai'] + 8*['Kyushu'])
            np_code_region_jpn = np.array(['Hokkaido']+ 6*['Tohoku'] + 7*['Kanto'] + 9*['Chubu'] + 5*['Chugoku'] + 4*['Shikoku'] + 7*['Kansai'] + 8*['Kyushu'])
            np_code_subregion_jpn =np.arange(1,48)
            np_population_subregion_jpn = np.array([5224614,1237984,1210534,2301996,959502, 1068027,
                                        1833152,2867009,1933146,1939110,7344765,6284480,14047594,
                                        9237337,2201272,1034814,1132852,766863,809974,2048011, 1978742,3633202,7542415,1770254,1413610,2578087,
                                        8837685, 5465002, 1324473, 922584, 553407, 671126, 1888432, 2799702, 1342059,719559, 950244, 1344841, 691527, 5135214,
                                        811442, 1312317, 1738301, 1123852, 1069576, 1588256, 1467480])
            np_area_subregion_jpn =np.array([83457.00,9644.55,15278.89,7285.77, 11636.28, 9323.46, 13782.76,  6095.72,
                                 6408.28,6362.33, 3798.08, 5156.61, 2188.67, 2415.86, 12583.83, 4247.61,4185.67, 4189.88,
                                 4465.37,  13562.23, 10621.17, 7780.50,  5165.12, 5777.31, 4017.36, 4613.21, 1899.28, 8396.16, 3691.09, 4726.29, 3507.28, 6707.96, 7113.23, 8479.70
                                 ,6114.09, 4146.74, 1876.55, 5678.33, 7105.16, 4978.51, 2439.65, 4105.47, 7404.79, 6339.74, 7735.99, 9188.82, 2276.49])
            np_flag_subregion_jpn = np.array(
                            ['https://upload.wikimedia.org/wikipedia/commons/2/22/Flag_of_Hokkaido_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/3/30/Flag_of_Aomori_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/a/a9/Flag_of_Iwate_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/c/c7/Flag_of_Miyagi_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/8/84/Flag_of_Akita_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/a/a1/Flag_of_Yamagata_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/4/4b/Flag_of_Fukushima_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/a/a8/Flag_of_Ibaraki_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/d/d5/Flag_of_Tochigi_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/b/ba/Flag_of_Gunma_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/c/cd/Flag_of_Saitama_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/0/0a/Flag_of_Chiba_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/1/15/Flag_of_Tokyo_Metropolis.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/a/a7/Flag_of_Kanagawa_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/c/cb/Flag_of_Niigata_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/1/1d/Flag_of_Toyama_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/6/6a/Flag_of_Ishikawa_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/5/56/Flag_of_Fukui_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/0/00/Flag_of_Yamanashi_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/f/f0/Flag_of_Nagano_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/3/3e/Flag_of_Gifu_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/9/92/Flag_of_Shizuoka_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/0/02/Flag_of_Aichi_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/8/8c/Flag_of_Mie_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/9/99/Flag_of_Shiga_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/0/06/Flag_of_Kyoto_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/5/5a/Flag_of_Osaka_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/7/74/Flag_of_Hyogo_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/0/00/Flag_of_Nara_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/6/6e/Flag_of_Wakayama_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/1/1c/Flag_of_Tottori_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/e/e8/Flag_of_Shimane_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/3/33/Flag_of_Okayama_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/e/ed/Flag_of_Hiroshima_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/b/b9/Flag_of_Yamaguchi_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/a/ac/Flag_of_Tokushima_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/2/29/Flag_of_Kagawa_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/2/2d/Flag_of_Ehime_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/5/50/Flag_of_Kochi_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/7/71/Flag_of_Fukuoka_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/1/18/Flag_of_Saga_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/6/65/Flag_of_Nagasaki_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/f/f7/Flag_of_Kumamoto_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/c/c8/Flag_of_Oita_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/0/0b/Flag_of_Miyazaki_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/c/c5/Flag_of_Kagoshima_Prefecture.svg',
                             'https://upload.wikimedia.org/wikipedia/commons/2/2f/Flag_of_Okinawa_Prefecture.svg'], dtype = object)
            dic_japan = {'name_subregion' : np_name_subregion_jpn,'code_region' : np_name_region_jpn, 'name_region': np_name_region_jpn,\
                         'code_subregion' : np_code_subregion_jpn, 'flag_subregion' : np_flag_subregion_jpn, 'town_subregion' : np_town_subregion_jpn,\
                         'population_subregion' : np_population_subregion_jpn, 'area_subregion' : np_area_subregion_jpn }
            df_japan = pd.DataFrame(data = dic_japan)
            df_japan.index = np.arange(1,48)
            self._country_data = self._country_data.rename(columns = {"id" : "code_subregion"})  #
            df_final_japan = pd.merge(df_japan,self._country_data, on = ['code_subregion'])
            df_final_japan.drop(columns = ['nam', 'nam_ja'], inplace = True)
            self._country_data = gpd.GeoDataFrame(df_final_japan)
            #code_subregion as to be str to be able to be merged ...
            self._country_data['code_subregion']=self._country_data['code_subregion'].astype(str)

    # def get_region_from_municipality(self,lname):
    #     """  Return region list from a municipality list
    #     """
    #     if not isinstance(lname, list):
    #         lname=[lname]
    #     return self._municipality_region.loc[self._municipality_region.name.isin(lname)]['district'].to_list()

    def set_dense_geometry(self):
        """  If used, we're using for the current country a dense geometry forsubregions
        and regions.
        It's not possible to go back.
        """

        if self.is_dense_geometry():
            return

        if self.is_main_geometry():
            raise CoaError("You already set the main geometry. Cannot set the dense geometry now.")

        if self.is_exploded_geometry():
            raise CoaError("You already set the exploded geometry. Cannot set the dense geometry now.")

        if self.get_country() == 'FRA':
            #.drop(['id_geofla','code_reg','nom_reg','x_chf_lieu','y_chf_lieu','x_centroid','y_centroid','Code département','Nom du département','Population municipale'],axis=1,inplace=True) # removing some column without interest
            # moving artificially (if needed) outre-mer area to be near to metropole for map representations

            tmp = []
            for index, poi in self._country_data.iterrows():
                x=0
                y=0
                w=self._country_data.loc[index,"code_subregion"]
                if w in self._list_translation.keys():
                    x=self._list_translation[w][0]
                    y=self._list_translation[w][1]
                g = sa.translate(self._country_data.loc[index, 'geometry'], xoff=x, yoff=y)
                tmp.append(g)
            self._country_data['geometry']=tmp

            # Remove COM with dense geometry true, too many islands to manage
            self._country_data=self._country_data[self._country_data.code_subregion!='980']

        elif self.get_country() == 'USA':
            tmp = []
            for index, poi in self._country_data.iterrows():
                x=0
                y=0
                w=self._country_data.loc[index,"code_subregion"]
                if w in self._list_translation.keys():
                    x=self._list_translation[w][0]
                    y=self._list_translation[w][1]
                    g=sa.scale(sa.translate(self._country_data.loc[index, 'geometry'],xoff=x,yoff=y),\
                                            xfact=self._list_scale[w],yfact=self._list_scale[w],origin=self._list_center[w])
                else:
                    g=self._country_data.loc[index, 'geometry']

                tmp.append(g)
            self._country_data['geometry']=tmp
        else:
            raise CoaError("The current country does not have dense geometry support.")

        self._country_data_region = None
        self._country_data_subregion = None
        self._is_dense_geometry = True
        self._is_main_geometry = False

    def set_exploded_geometry(self):
        """  If used, we're using for the current country a dense geometry forsubregions
        and regions.
        Moreover we're exploding internal dense geometry for some countries (currently IdF
        for France, only).

        It's not possible to go back.
        """

        if self.is_main_geometry():
            raise CoaError("You already set the main geometry. Cannot set the exploded geometry now.")

        if self.is_dense_geometry():
            raise CoaError("You already set the dense geometry. Cannot set the exploded geometry now.")

        if self.is_exploded_geometry():
            return

        self.set_dense_geometry()

        if self.get_country() == 'FRA':
            # Add Ile de France zoom
            idf_translation=(-6.5,-5)
            idf_scale=3
            idf_center=(-1.5,43)
            tmp = []
            for index, poi in self._country_data.iterrows():
                g=self._country_data.loc[index, 'geometry']
                if self._country_data.loc[index,'code_subregion'] in ['75','91','92','93','94','95','77','78']:
                    g2=sa.scale(sa.translate(g,xoff=idf_translation[0],yoff=idf_translation[1]),\
                                            xfact=idf_scale,yfact=idf_scale,origin=idf_center)
                    g=g2 # so.unary_union([g,g2]) # uncomment if you want a copy
                tmp.append(g)
            self._country_data['geometry']=tmp

        self._is_dense_geometry = False
        self._is_main_geometry = False
        self._is_exploded_geometry = True

    def set_main_geometry(self):
        """  If used, we're using only for the current country the main
        geometry for subregions and regions.
        It's not possible to go back.
        """
        if self.is_main_geometry():
            return

        if self.is_dense_geometry() or self.is_exploded_geometry():
            raise CoaError("You already set the dense or exploded geometry. Cannot set the main geometry now.")

        if self.get_country()=='FRA':
            self._country_data = self._country_data[~self._country_data['code_subregion'].isin(self._list_translation.keys())]
            # Remove COM with main geometry true, too many islands to manage
            self._country_data=self._country_data[self._country_data.code_subregion!='980']
        elif self.get_country()=='USA':
            self._country_data = self._country_data[~self._country_data['code_subregion'].isin(self._list_translation.keys())]
        else:
            raise CoaError("The current country does not have dense geometry support.")

        self._country_data_region = None
        self._country_data_subregion = None
        self._is_main_geometry = True

    def is_dense_geometry(self):
        """Return the self._is_dense_geometry variable
        """
        return self._is_dense_geometry

    def is_exploded_geometry(self):
        """Return the self._is_exploded_geometry variable
        """
        return self._is_exploded_geometry

    def is_main_geometry(self):
        """Return the self._is_main_geometry variable
        """
        return self._is_main_geometry

    def get_source(self):
        """ Return informations about URL sources
        """
        if self.get_country() != None:
            return self._source_dict[self.get_country()]
        else:
            return self._source_dict

    def get_country(self):
        """ Return the current country used.
        """
        return self._country

    def get_list_countries(self):
        """ This function returns back the list of supported countries
        """
        return sorted(list(self._country_info_dict.keys()))

    def is_init(self):
        """Test if the country is initialized. Return True if it is. False if not.
        """
        if self.get_country() != None:
            return True
        else:
            return False

    def test_is_init(self):
        """Test if the country is initialized. If not, raise a CoaDbError.
        """
        if self.is_init():
            return True
        else:
            raise CoaDbError("The country is not set. Use a constructor with non empty country string.")

    def get_region_list(self):
        """ Return the list of available regions with code, name and geometry
        """
        cols=[c for c in self.get_list_properties() if '_region' in c]
        cols.append('geometry')
        return self.get_data(True)[cols]

    def is_region(self,r):
        """ Return False if r is a not a known region, return the correctly capitalized name if ok
        """
        r=tostdstring(r)
        for i in self.get_region_list().name_region.to_list():
            if tostdstring(i) == r:
                return i
        return False

    def get_subregion_list(self):
        """ Return the list of available subregions with code, name and geometry
        """
        cols=[c for c in self.get_list_properties() if '_subregion' in c ]
        cols.append('geometry')
        return self.get_data()[cols]

    def is_subregion(self,r):
        """ Return False if r is a not a known region, return the correctly capitalized name if ok
        """
        r2=tostdstring(r)
        for i in self.get_subregion_list().name_subregion.to_list():
            if tostdstring(i) == r2:
                return i
        a=self.get_subregion_list()[self.get_subregion_list().code_subregion==r].name_subregion.values
        if a.size == 1:
            return a[0]
        return False

    def get_subregions_from_region(self,**kwargs):
        """ Return the list of subregions within a specified region.
        Should give either the code or the name of the region as strings in kwarg : code=# or name=#
        Output default is 'code' of subregions. Can be changed with output='name'.
        """
        kwargs_test(kwargs,['name','code','output'],'Should give either name or code of region. Output can be changed with the output option.')
        code=kwargs.get("code",None)
        name=kwargs.get("name",None)
        out=kwargs.get("output",'code')
        if not (code == None) ^ (name == None):
            raise CoaKeyError("Should give either code or name of region, not both.")
        if not out in ['code','name']:
            raise CoaKeyError("Should set output either as 'code' or 'name' for subregions.")

        if name != None:
            if not isinstance(name,str):
                raise CoaTypeError("Name should be given as string.")
            name = name.title()
            if not name in self.get_region_list()['name_region'].str.title().to_list():
                raise CoaWhereError ("The region "+name+" does not exist for country "+self.get_country()+". See get_region_list().")
            cut=(self.get_data(True)['name_region'].str.title()==name)

        if code != None:
            if not isinstance(code,str):
                raise CoaTypeError("Name should be given as string.")
            if not code in self.get_region_list()['code_region'].to_list():
                raise CoaWhereError("The region "+code+" does not exist for country "+self.get_country()+". See get_region_list().")
            cut=(self.get_data(True)['code_region']==code)

        return self.get_data(True)[cut][out+'_subregion'].iloc[0]#to_list()

    def get_subregions_from_list_of_region_names(self,l,output='code'):
        """ Return the list of subregions according to list of region names given.
        The output argument ('code' as default) is given to the get_subregions_from_region function.
        """
        if not isinstance(l,list):
            raise CoaTypeError("Should provide list as argument")
        s=[]
        for r in l:
            s=s+self.get_subregions_from_region(name=r,output=output)
        return s

    def get_regions_from_subregion(self,code,output='code'):
        """ Return the list of regions where the subregion, given by a code, is.
        Output default is 'code' of subregions. Can be changer with output='name'.
        """

        if not output in ['code','name']:
            raise CoaKeyError('The output option should be "code" or "name" only')

        if not code in self.get_subregion_list()['code_subregion'].to_list():
            raise CoaWhereError("The subregion "+code+" does not exist for country "+self.get_country()+". See get_subregion_list().")

        l=[]
        for k,v in self.get_data(True).iterrows():
            if code in v.code_subregion:
                if output == 'code':
                    l.append(v.code_region)
                else: # due to first test, that's for sure name
                    l.append(v.name_region)
        return list(dict.fromkeys(l))

    def get_regions_from_list_of_subregion_codes(self,l,output='code'):
        """ Return the list of regions according to list of subregion names given.
        The output argument ('code' as default) is given to the get_regions_from_subregion function.
        """
        if not isinstance(l,list):
            raise CoaTypeError("Should provide list as argument")
        s=[]
        for sr in l:
            s=s+self.get_regions_from_subregion(sr,output=output)
        return list(dict.fromkeys(s))

    def get_regions_from_macroregion(self,**kwargs):
        """ Return the list of regions included in another macroregion
        Can provide input as code= or name=
        Can provide output as 'name' or 'code' (default).
        """
        kwargs_test(kwargs,['name','code','output'],'Should give either name or code of region. Output can be changed with the output option.')
        code=kwargs.get("code",None)
        name=kwargs.get("name",None)
        out=kwargs.get("output",'code')

        if not (code == None) ^ (name == None):
            raise CoaKeyError("Should give either code or name of region, not both.")
        if not out in ['code','name']:
            raise CoaKeyError("Should set output either as 'code' or 'name' for subregions.")

        dict_input={k:v for k,v in kwargs.items() if k in ['code','name']}
        r_out=self.get_regions_from_list_of_subregion_codes(self.get_subregions_from_region(**dict_input),output=out)

        # remove the input
        rl=self.get_region_list()
        if code != None:
            if out=='code':
                input=rl[rl.code_region==code].name_region.item()
            else:
                input=code
        else:
            if out=='name':
                input=name
            else:
                input=rl[rl.name_region==code].code_region.item()

        if input in r_out:
            r_out.remove(input)

        # Append the input in the right position, the macro region should be at the end
        if len(r_out) == 1: # the input is not a macro region but just a region
            r_out.insert(0,input)
        else: # the input is a real macro region
            r_out.append(input)

        return r_out

    def get_list_properties(self):
        """Return the list of available properties for the current country
        """
        if self.test_is_init():
            return sorted(self._country_data.columns.to_list())

    def get_data(self,region_version=False):
        """Return the whole geopandas data.
        If region_version = True (not default), the pandas output is region based focalized.
        """
        if self.test_is_init():
            if region_version:
                if not isinstance(self._country_data_region,pd.DataFrame): # i.e. is None
                    col_reg=[c for c in self._country_data.columns.tolist() if '_region' in c]
                    col=col_reg.copy()
                    col.append('geometry') # to merge the geometry of subregions
                    for p in self.get_list_properties():
                        if ('_subregion' in p) and pd.api.types.is_numeric_dtype(self._country_data[p]):
                            col.append(p)
                    if not 'code_subregion' in col:
                        col.append('code_subregion') # to get the list of subregion in region
                    if not 'name_subregion' in col:
                        col.append('name_subregion') # to get the list of subregion name in region

                    pr=self._country_data[col].copy()

                    # Country specific management
                    if self.get_country()=='FRA': # manage pseudo 'FRA' regions 'Métropole' and 'Outre-mer'
                        metropole_cut=pr.code_region.astype(int)>=10
                        pr_metropole=pr[metropole_cut].copy()
                        pr_metropole['code_region']='999'
                        pr_metropole['name_region']='Métropole'
                        pr_metropole['flag_region']=''
                        pr_outremer=pr[~metropole_cut].copy()
                        pr_outremer['code_region']='000'
                        pr_outremer['name_region']='Outre-mer'
                        pr_outremer['flag_region']=''

                        pr=pd.concat([pr,pr_metropole],ignore_index=True)
                        pr=pd.concat([pr,pr_outremer],ignore_index=True)
                        #pr=pr.append(pr_metropole,ignore_index=True).append(pr_outremer,ignore_index=True)

                    elif self.get_country()=='ESP' : # manage pseudo 'ESP' regions within and outside continent
                        islands_cut=pr.code_region.isin(['05'])
                        pr_metropole=pr[~islands_cut].copy()
                        pr_metropole['code_region']='99'
                        pr_metropole['name_region']='España peninsular'
                        pr_metropole['flag_region']=''

                        pr_outremer=pr[islands_cut].copy()
                        pr_outremer['code_region']='00'
                        pr_outremer['name_region']='Islas españolas'
                        pr_outremer['flag_region']=''

                        pr=pd.concat([pr,pr_metropole,pr_outremer],ignore_index=True)

                    elif self.get_country()=='PRT' : # manage pseudo 'PRT' regions within and outside continent
                        islands_cut=pr.code_region.isin(['PT.AC','PT.MA'])
                        pr_metropole=pr[~islands_cut].copy()
                        pr_metropole['code_region']='PT.99'
                        pr_metropole['name_region']='Portugal continental'
                        pr_metropole['flag_region']=''

                        pr_outremer=pr[islands_cut].copy()
                        pr_outremer['code_region']='PT.00'
                        pr_outremer['name_region']='Ilhas portuguesas'
                        pr_outremer['flag_region']=''

                        pr=pd.concat([pr,pr_metropole],ignore_index=True)
                        pr=pd.concat([pr,pr_outremer],ignore_index=True)
                        #pr=pr.append(pr_metropole,ignore_index=True).append(pr_outremer,ignore_index=True)

                    elif self.get_country()=='USA':
                        usa_col=pr.columns.tolist()
                        #usa_col.remove('_subregion') # Remove numeric column, if not, the dissolve does not work properly
                        #usa_col.remove('area_subregion') # idem
                        pr=pr[usa_col]

                    elif self.get_country()=='EUR':
                        pr.loc[pr.geometry.isnull(),'geometry']=sg.Point()  # For correct geometry merge
                        pr['geometry'] = pr['geometry'].buffer(0.001) # needed with geopandas 0.10.2' for EUR data only (apparently)

                    pr['code_subregion']=pr.code_subregion.apply(lambda x: [x])
                    pr['name_subregion']=pr.name_subregion.apply(lambda x: [x])

                    self._country_data_region=pr.dissolve(by=col_reg,aggfunc=(lambda x: x.sum())).sort_values(by='code_region').reset_index()
                    for x in ['population','area']:
                        if x+'_subregion' in self._country_data_region.columns:
                            self._country_data_region.rename(columns={x+'_subregion':x+'_region'},inplace=True)

                return self._country_data_region
            else:
                if not isinstance(self._country_data_subregion,pd.DataFrame): #i.e. is None
                    self._country_data_subregion=self._country_data.sort_values(by='code_subregion')
                return self._country_data_subregion

    def add_field(self,**kwargs):
        """Return a the data pandas.Dataframe with an additionnal column with property prop.

        Arguments :
        input        : pandas.Dataframe object. Mandatory.
        field        : field of properties to add. Should be within the get_list_prop() list. Mandatory.
        input_key    : input geo key of the input pandas dataframe. Default  'where'
        geofield     : internal geo field to make the merge. Default 'code_subregion'
        region_merging : Boolean value. Default False, except if the geofield contains '_region'.
                       If True, the merge between input dans GeoCountry data is done within the
                       region version of the data, not the subregion data which is the default
                       behavious.
        overload   : Allow to overload a field. Boolean value. Default : False
        """

        # Test of args
        kwargs_test(kwargs,['input','field','input_key','geofield','geotype','overload'],
            'Bad args used in the add_field() function.')

        # Testing input
        data=kwargs.get('input',None) # the panda
        if not isinstance(data,pd.DataFrame):
            raise CoaTypeError('You should provide a valid input pandas'
                ' DataFrame as input. See help.')
        data=data.copy()

        # Testing input_key
        input_key=kwargs.get('input_key','where')
        if not isinstance(input_key,str):
            raise CoaTypeError('The input_key should be given as a string.')
        if input_key not in data.columns.tolist():
            raise CoaKeyError('The input_key "'+input_key+'" given is '
                'not a valid column name of the input pandas dataframe.')

        # Testing geofield
        geofield=kwargs.get('geofield','code_subregion')
        if not isinstance(geofield,str):
            raise CoaTypeError('The geofield should be given as a string.')
        if geofield not in self._country_data.columns.tolist():
            raise CoaKeyError('The geofield "'+geofield+'" given is '
                'not a valid column name of the available data. '
                'See get_list_properties() for valid fields.')

        region_merging=kwargs.get('region_merging',None)
        if region_merging == None:
            if '_region' in geofield:
                region_merging=True
            else:
                region_merging=False

        if not isinstance(region_merging,bool):
            raise CoaKeyError('The region_mergin key should be boolean. See help.')

        # Testing fields
        prop=kwargs.get('field',None) # field list
        if prop == None:
            raise CoaKeyError('No field given. See help.')
        if not isinstance(prop,list):
            prop=[prop] # make the prop input a list if needed

        if not all(isinstance(p, str) for p in prop):
            raise CoaTypeError("Each property should be a string whereas "+str(prop)+" is not a list of string.")

        if not all(p in self.get_list_properties() for p in prop):
            raise CoaKeyError("The property "+prop+" is not available for country "+self.get_country()+".")

        # Testing overload
        overload=kwargs.get('overload',False)
        if not isinstance(overload,bool):
            raise CoaTypeError('The overload option should be a boolean.')

        if not overload and not all(p not in data.columns.tolist() for p in prop):
            raise CoaKeyError('Some fields already exist in you panda '
                'dataframe columns. You may set overload to True.')

        # Is the oject properly initialized ?
        self.test_is_init()

        # Now let's go for merging
        prop.append('code_subregion')
        return data.merge(self.get_data(region_merging)[prop],how='left',left_on=input_key,\
                            right_on=geofield)

