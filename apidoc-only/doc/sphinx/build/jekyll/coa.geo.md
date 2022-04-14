---
date: '2021-12-09T15:56:56.735Z'
docname: coa.geo
images: {}
path: /coa-geo
title: coa.geo module
---

# coa.geo module

Project : PyCoA
Date :    april 2020 - march 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.geo

## About :

Geo classes within the PyCoA framework.

GeoManager class provides translations between naming normalisations
of countries. It’s based on the pycountry module.

GeoInfo class allow to add new fields to a pandas DataFrame about
statistical information for countries.

GeoRegion class helps returning list of countries in a specified region

GeoCountry manages information for a single country.

## Summary

Classes:

| `GeoCountry`

 | GeoCountry class definition.

 |
| `GeoInfo`

            | GeoInfo class definition.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `GeoManager`

         | GeoManager class definition.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `GeoRegion`

          | GeoRegion class definition.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
Class diagram:



![image](uml_images/classes_coa.geo.png)

## Reference


### class GeoCountry(country=None, \*\*kwargs)
Bases: `object`

GeoCountry class definition.
This class provides functions for specific countries and their states / departments / regions,
and their geo properties (geometry, population if available, etc.)

The list of supported countries is given by get_list_countries() function.


#### add_field(\*\*kwargs)
Return a the data pandas.Dataframe with an additionnal column with property prop.

Arguments :
input        : pandas.Dataframe object. Mandatory.
field        : field of properties to add. Should be within the get_list_prop() list. Mandatory.
input_key    : input geo key of the input pandas dataframe. Default  ‘where’
geofield     : internal geo field to make the merge. Default ‘code_subregion’
region_merging : Boolean value. Default False, except if the geofield contains ‘_region’.

> If True, the merge between input dans GeoCountry data is done within the
> region version of the data, not the subregion data which is the default
> behavious.

overload   : Allow to overload a field. Boolean value. Default : False


#### get_country()
Return the current country used.


#### get_data(region_version=False)
Return the whole geopandas data.
If region_version = True (not default), the pandas output is region based focalized.


#### get_list_countries()
This function returns back the list of supported countries


#### get_list_properties()
Return the list of available properties for the current country


#### get_region_list()
Return the list of available regions with code, name and geometry


#### get_source()
Return informations about URL sources


#### get_subregion_list()
Return the list of available subregions with code, name and geometry


#### get_subregions_from_list_of_region_names(l, output='code')
Return the list of subregions according to list of region names given.
The output argument (‘code’ as default) is given to the get_subregions_from_region function.


#### get_subregions_from_region(\*\*kwargs)
Return the list of subregions within a specified region.
Should give either the code or the name of the region as strings in kwarg : code=# or name=#
Output default is ‘code’ of subregions. Can be changer with output=’name’.


#### is_init()
Test if the country is initialized. Return True if it is. False if not.


#### is_region(r)
Return False if r is a not a known region, return the correctly capitalized name if ok


#### is_subregion(r)
Return False if r is a not a known region, return the correctly capitalized name if ok


#### test_is_init()
Test if the country is initialized. If not, raise a CoaDbError.


### class GeoInfo(gm=0)
Bases: `object`

GeoInfo class definition. No inheritance from any other class.

It should raise only CoaError and derived exceptions in case
of errors (see pycoa.error)


#### add_field(\*\*kwargs)
this is the main function of the GeoInfo class. It adds to
the input pandas dataframe some fields according to
the geofield field of input.
The return value is the pandas dataframe.

Arguments :
field    – should be given as a string of list of strings and

> should be valid fields (see get_list_field() )
> Mandatory.

input    – provide the input pandas dataframe. Mandatory.
geofield – provide the field name in the pandas where the

> location is stored. Default : ‘location’

overload – Allow to overload a field. Boolean value.

    Default : False


#### get_GeoManager()
return the local instance of used GeoManager()


#### get_list_field()
return the list of supported additionnal fields available


#### get_source(field=None)
return the source of the information provided for a given
field.


### class GeoManager(standard='iso2')
Bases: `object`

GeoManager class definition. No inheritance from any other class.

It should raise only CoaError and derived exceptions in case
of errors (see pycoa.error)


#### first_db_translation(w, db)
This function helps to translate from country name to
standard for specific databases. It’s the first step
before final translation.

One can easily add some database support adding some new rules
for specific databases


#### get_GeoRegion()
return the GeoRegion local instance


#### get_list_db()
return supported list of database name for translation of
country names to standard.


#### get_list_output()
return supported list of output type. First one is default
for the class


#### get_list_standard()
return the list of supported standard name of countries.
First one is default for the class


#### get_region_list()
return the list of region via the GeoRegion instance


#### get_standard()
return current standard use within the GeoManager class


#### set_standard(standard)
set the working standard type within the GeoManager class.
The standard should meet the get_list_standard() requirement


#### to_standard(w, \*\*kwargs)
Given a list of string of locations (countries), returns a
normalised list according to the used standard (defined
via the setStandard() or __init__ function. Current default is iso2.

first arg        –  w, list of string of locations (or single string)

    to convert to standard one

output           – ‘list’ (default), ‘dict’ or ‘pandas’
db               – database name to help conversion.

> Default : None, meaning best effort to convert.
> Known database : jhu, wordometer…
> See get_list_db() for full list of known db for
> standardization

interpret_region – Boolean, default=False. If yes, the output should

    be only ‘list’.


### class GeoRegion()
Bases: `object`

GeoRegion class definition. Does not inheritate from any other
class.

It should raise only CoaError and derived exceptions in case
of errors (see pycoa.error)


#### get_countries_from_region(region)
it returns a list of countries for the given region name.
The standard used is iso3. To convert to another standard,
use the GeoManager class.


#### get_pandas()

#### get_region_list()

#### get_source()

#### is_region(region)
it returns either False or the correctly named region name
