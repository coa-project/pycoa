# Python Documentation

## Classes

**[GeoManager](GeoManager.md)**: GeoManager class definition. No inheritance from any other class.   
It should raise only CoaError and derived exceptions in case of errors (see pycoa.error) 

**[GeoInfo](GeoInfo.md)**: GeoInfo class definition. No inheritance from any other class.   
It should raise only CoaError and derived exceptions in case of errors (see pycoa.error) 

**[GeoRegion](GeoRegion.md)**: GeoRegion class definition. Does not inheritate from any other class.   
It should raise only CoaError and derived exceptions in case of errors (see pycoa.error) 

**[CocoDisplay](CocoDisplay.md)**: 

**[CoaError](CoaError.md)**: Base class for exceptions in PyCoa. 

**[CoaKeyError](CoaKeyError.md)**: Exception raised for errors in used key option.   
Attributes: message -- explanation of the error 

**[CoaWhereError](CoaWhereError.md)**: Exception raised for location errors.   
Attributes: message -- explanation of the error 

**[CoaTypeError](CoaTypeError.md)**: Exception raised for type mismatch errors.   
Attributes: message -- explanation of the error 

**[CoaLookupError](CoaLookupError.md)**: Exception raised for type lookup errors.   
Attributes: message -- explanation of the error 

**[CoaNotManagedError](CoaNotManagedError.md)**: Exception raised when the error is unknown and not managed.   
Attributes: message -- explanation of the error 

**[CoaDbError](CoaDbError.md)**: Exception raised for database errors.   
Attributes: message -- explanation of the error 

**[CoaConnectionError](CoaConnectionError.md)**: Exception raised for connection errors.   
Attributes: message -- explanation of the error 

**[DataBase](DataBase.md)**: DataBase class Parse a Covid-19 database and filled the pandas python objet : pandas_datase It takes a string argument, which can be: 'jhu','spf','owid' and 'opencovid19' The pandas_datase structure is based, for historical reason, on the JHU structure: ['location', 'date', key-words , 'cumul', 'diff'] 


## Functions

### info


Print to stdout with similar args as the builtin print function, if _verbose_mode > 0 




### verb


Print to stdout with similar args as the builtin print function, if _verbose_mode > 1 




### kwargs_test


Test that the list of kwargs is compatible with expected args. If not it raises a CoaKeyError with error_string. 
#### Parameters
name | description | default
--- | --- | ---
given_args |  | 
expected_args |  | 
error_string |  | 





### check_valid_date


Check if a string is compatible with a valid date under the format day/month/year with 2 digits for day, 2 digits for month and 4 digits for year. 
#### Parameters
name | description | default
--- | --- | ---
date |  | 





### extract_dates


Expecting None or 1 or 2 dates separated by :. The format is a string. If 2 dates are given, they must be ordered. When 1 date is given, assume that's the latest which is given. When None date is give, the oldest date is 01/01/0001, the newest is now.   
It returns 2 datetime object. If nothing given, the oldest date is 01/01/0001, 
#### Parameters
name | description | default
--- | --- | ---
when |  | 





### listoutput


Return the list of currently available output types for the get() function. The first one is the default output given if not specified. 




### listwhom


Return the list of currently avalailable databases for covid19 data in PyCoA. The first one is the default one. 




### listwhat


Return the list of currently avalailable type of series available. The first one is the default one. 




### setwhom


Set the covid19 database used, given as a string. Please see pycoa.listbase() for the available current list.   
By default, the listbase()[0] is the default base used in other functions. 
#### Parameters
name | description | default
--- | --- | ---
base |  | 





### listwhich


Get which are the available fields for the current or specified base. Output is a list of string. By default, the listwhich()[0] is the default which field in other functions. 
#### Parameters
name | description | default
--- | --- | ---
dbname |  | None





### get


Return covid19 data in specified format output (default, by list) for specified locations ('where' keyword). The used database is set by the setbase() function but can be changed on the fly ('whom' keyword) Keyword arguments -----------------   
where  --   a single string of location, or list of (mandatory, no default value) which  --   what sort of data to deliver ( 'death','confirmed', 'recovered' …). See listwhat() function for full list according to the used database. what   --   which data are computed, either in cumulative mode ('cumul', default value), 'daily' or 'diff' and 'weekly' (rolling daily over 1 week) . See listwhich() for fullist of available Full list of which keyword with the listwhich() function. whom   --   Database specification (overload the setbase() function). See listwhom() for supported list function). See listwhom() for supported list when   --   dates are given under the format dd/mm/yyyy. In the when option, one can give one date which will be the end of the data slice. Or one can give two dates separated with ":", which will define the time cut for the output data btw those two dates.   
output --   output format returned ( list (default), array (numpy.array), dict or pandas)   
option --   pre-computing option. Currently, only the nonneg option is available, meaning that negative daily balance is pushed back to previous days in order to have a cumulative function which is monotonous increasing. is available. By default : no option. 




### decoplot



#### Parameters
name | description | default
--- | --- | ---
func |  | 





### plot



#### Parameters
name | description | default
--- | --- | ---
t |  | 
which |  | 
title |  | 
width_height |  | 





### scrollmenu_plot



#### Parameters
name | description | default
--- | --- | ---
t |  | 
which |  | 
title |  | 
width_height |  | 





### hist


Create histogram according to arguments (same as the get function) and options.   
Keyword arguments -----------------   
where (mandatory if no input), what, which, whom, when : (see help(get))   
  
bins        --  number of bins used. If none provided, a default value will be used.   
input       --  input data to plot within the pycoa framework (e.g. after some analysis or filtering). Default is None which means that we use the basic raw data through the get function. When the 'input' keyword is set, where, what, which, whom when keywords are ignored. input should be given as valid pycoa pandas dataframe.   
input_field --  is the name of the field of the input pandas to plot. Default is 'deaths/cumul', the default output field of the get() function.   
width_height : width and height of the picture . If specified should be a list of width and height. For instance width_height=[400,500] 




### map


Create a map according to arguments and options. See help(hist). 

