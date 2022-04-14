---
date: '2021-12-09T15:56:56.735Z'
docname: coa.front
images: {}
path: /coa-front
title: coa.front module
---

# coa.front module

Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - march 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : coa.front

## About :

This is the PyCoA front end functions. It provides easy access and
use of the whole PyCoA framework in a simplified way.
The use can change the database, the type of data, the output format
with keywords (see help of functions below).

## Basic usage

\*\* plotting covid deaths (default value) vs. time \*\*

    import coa.front as cf

    cf.plot(where=’France’)  # where keyword is mandatory

\*\* getting recovered data for some countries \*\*

> cf.get(where=[‘Spain’,’Italy’],which=’recovered’)

\*\* listing available database and which data can be used \*\*

    cf.listwhom()
    cf.setwhom(‘jhu’) # return available keywords (aka ‘which’ data)
    cf.listwhich()   # idem
    cf.listwhat()    # return available time series type (weekly,

    > # daily…)

    cf.plot(option=’sumall’) # return the cumulative plot for all countries

        # for default which keyword. See cf.listwhich() and
        # and other cf.list\*\*() function (see below)

## Summary

Functions:

| `chartsinput_deco`

 | Main decorator it mainly deals with arg testings

 |
| `get`

                | Return covid19 data in specified format output (default, by list) for specified locations ('where' keyword).

                                                                                                  |
| `getinfo`

            | Return keyword_definition for the db selected

                                                                                                                                                                 |
| `getversion`

         | Return the current running version of pycoa.

                                                                                                                                                                  |
| `getwhom`

            | Return the current base which is used

                                                                                                                                                                         |
| `hist`

               | Create histogram according to arguments.

                                                                                                                                                                      |
| `listbypop`

          | Get the list of available population normalization

                                                                                                                                                            |
| `listoption`

         | Return the list of currently avalailable option apply to data.

                                                                                                                                                |
| `listoutput`

         | Return the list of currently available output types for the get() function.

                                                                                                                                   |
| `listtile`

           | Return the list of currently avalailable tile option for map() Default is the first one.

                                                                                                                      |
| `listvisu`

           | Return the list of currently available visualization for the map() function.

                                                                                                                                  |
| `listwhat`

           | Return the list of currently avalailable type of series available.

                                                                                                                                            |
| `listwhere`

          | Get the list of available regions/subregions managed by the current database

                                                                                                                                  |
| `listwhich`

          | Get which are the available fields for the current base.

                                                                                                                                                      |
| `listwhom`

           | Return the list of currently avalailable databases for covid19 data in PyCoA.

                                                                                                                                 |
| `map`

                | Create a map according to arguments and options. See help(map). - 2 types of visu are avalailable so far : bokeh or folium (see listvisu()) by default visu='bokeh' - In the default case (i.e visu='bokeh') available option are :     - dateslider=True: a date slider is called and displayed on the right part of the map     - maplabel = text, value are displayed directly on the map                = spark, sparkline are displayed directly on the map                = tickmap%, colormap tick are in %.

 |
| `merger`

             | Merge two or more pycoa pandas from get_stats operation 'coapandas': list (min 2D) of pandas from stats 'whichcol': list variable associate to the coapandas list to be retrieve

                                                                                                                                                                                                                                                                                                                                    |
| `plot`

               | Create a date plot according to arguments.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `saveoutput`

         | Export pycoas pandas as an output file selected by output argument 'pandas': pandas to save 'saveformat': excel (default) or csv 'savename': None (default pycoaout+ '.xlsx/.csv')

                                                                                                                                                                                                                                                                                                                                  |
| `setwhom`

            | Set the covid19 database used, given as a string.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
## Reference


### chartsinput_deco(f)
Main decorator it mainly deals with arg testings


### get(\*\*kwargs)
Return covid19 data in specified format output (default, by list)
for specified locations (‘where’ keyword).
The used database is set by the setbase() function but can be
changed on the fly (‘whom’ keyword)
Keyword arguments
—————–

where  –   a single string of location, or list of (mandatory,

    no default value)

which  –   what sort of data to deliver ( ‘death’,’confirmed’,

    ‘recovered’ for ‘jhu’ default database). See listwhich() function
    for full list according to the used database.

what   –   which data are computed, either in cumulative mode

    (‘cumul’, default value), or ‘daily’ (diff with previous day
    and ‘weekly’ (diff with previous week). See
    listwhich() for fullist of available
    Full list of what keyword with the listwhat() function.

whom   –   Database specification (overload the setbase()

    function). See listwhom() for supported list

when   –   dates are given under the format dd/mm/yyyy. In the when

    option, one can give one date which will be the end of
    the data slice. Or one can give two dates separated with
    “:”, which will define the time cut for the output data
    btw those two dates.

output –   output format returned ( pandas (default), array (numpy.array),

    dict or list). See listoutput() function.

option –   pre-computing option.

    
    * nonneg means that negative daily balance is pushed back

    to previousdays in order to have a cumulative function which is
    monotonous increasing.
    \* nofillnan means that nan value won’t be filled.
    \* smooth7 will perform a 7 day window average of data
    \* sumall will return integrated over locations given via the
    where keyword. If using double bracket notation, the sumall
    option is applied for each bracketed member of the where arg.

    By default : no option.
    See listoption().

bypop –    normalize by population (if available for the selected database).

    
    * by default, ‘no’ normalization


    * can normalize by ‘100’, ‘1k’, ‘100k’ or ‘1M’


### getinfo(which)
Return keyword_definition for the db selected


### getversion()
Return the current running version of pycoa.


### getwhom()
Return the current base which is used


### hist(\*\*kwargs)
Create histogram according to arguments.
See help(hist).
Keyword arguments
—————–

where (mandatory if no input), what, which, whom, when : (see help(get))

input       –  input data to plot within the pycoa framework (e.g.

    after some analysis or filtering). Default is None which
    means that we use the basic raw data through the get
    function.
    When the ‘input’ keyword is set, where, what, which,
    whom when keywords are ignored.
    input should be given as valid pycoa pandas dataframe.

input_field –  is the name of the field of the input pandas to plot.

    Default is ‘deaths/cumul’, the default output field of
    the get() function.

width_height

    If specified should be a list of width and height.
    For instance width_height=[400,500]

typeofhist  –  ‘bylocation’ (default), ‘byvalue’ or pie

bins        –  number of bins used, only available for ‘byvalue’ type of

    histograms.
    If none provided, a default value will be used.


### listbypop()
Get the list of available population normalization


### listoption()
Return the list of currently avalailable option apply to data.
Default is no option.


### listoutput()
Return the list of currently available output types for the
get() function. The first one is the default output given if
not specified.


### listtile()
Return the list of currently avalailable tile option for map()
Default is the first one.


### listvisu()
Return the list of currently available visualization for the
map() function. The first one is the default output given if
not specified.


### listwhat()
Return the list of currently avalailable type of series available.
The first one is the default one.


### listwhere(clustered=False)
Get the list of available regions/subregions managed by the current database


### listwhich()
Get which are the available fields for the current base.
Output is a list of string.
By default, the listwhich()[0] is the default which field in other
functions.


### listwhom(detailed=False)
Return the list of currently avalailable databases for covid19
data in PyCoA.
The first one is the default one.

If detailed=True, gives information location of each given database.


### map(\*\*kwargs)
Create a map according to arguments and options.
See help(map).
- 2 types of visu are avalailable so far : bokeh or folium (see listvisu())
by default visu=’bokeh’
- In the default case (i.e visu=’bokeh’) available option are :

> 
> * dateslider=True: a date slider is called and displayed on the right part of the map


> * maplabel = text, value are displayed directly on the map

>     = spark, sparkline are displayed directly on the map
>     = tickmap%, colormap tick are in %


### merger(\*\*kwargs)
Merge two or more pycoa pandas from get_stats operation
‘coapandas’: list (min 2D) of pandas from stats
‘whichcol’: list variable associate to the coapandas list to be retrieve


### plot(\*\*kwargs)
Create a date plot according to arguments. See help(plot).
Keyword arguments
—————–

where (mandatory), what, which, whom, when : (see help(get))

input       –  input data to plot within the pycoa framework (e.g.

    after some analysis or filtering). Default is None which
    means that we use the basic raw data through the get
    function.
    When the ‘input’ keyword is set, where, what, which,
    whom when keywords are ignored.
    input should be given as valid pycoa pandas dataframe.

input_field –  is the name of the field of the input pandas to plot.

    Default is ‘deaths/cumul’, the default output field of
    the get() function.

width_height

    If specified should be a list of width and height. For instance width_height=[400,500]

title       –  to force the title of the plot

typeofplot  – ‘date’ (default), ‘menulocation’ or ‘versus’

    ‘date’:date plot
    ‘menulocation’: date plot with two scroll menu locations.

    > Usefull to study the behaviour of a variable for two different countries.

    ‘versus’: plot variable against an other one.

        For this type of plot one should used ‘input’ and ‘input_field’ (not fully tested).
        Moreover dim(input_field) must be 2.


### saveoutput(\*\*kwargs)
Export pycoas pandas as an output file selected by output argument
‘pandas’: pandas to save
‘saveformat’: excel (default) or csv
‘savename’: None (default pycoaout+ ‘.xlsx/.csv’)


### setwhom(base)
Set the covid19 database used, given as a string.
Please see pycoa.listbase() for the available current list.

By default, the listbase()[0] is the default base used in other
functions.
