# GeoManager


GeoManager class definition. No inheritance from any other class.   
It should raise only CoaError and derived exceptions in case of errors (see pycoa.error) 

## Methods


### __init__


__init__ member function, with default definition of the used standard. To get the current default standard, see get_list_standard()[0]. 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
standard |  | 





### get_list_standard


return the list of supported standard name of countries. First one is default for the class 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_list_output


return supported list of output type. First one is default for the class 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_list_db


return supported list of database name for translation of country names to standard. 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_standard


return current standard use within the GeoManager class  

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### set_standard


set the working standard type within the GeoManager class. The standard should meet the get_list_standard() requirement 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
standard |  | 





### to_standard


Given a list of string of locations (countries), returns a normalised list according to the used standard (defined via the setStandard() or __init__ function. Current default is iso2.   
Arguments ----------------- first arg        --  w, list of string of locations (or single string) to convert to standard one   
output           -- 'list' (default), 'dict' or 'pandas' db               -- database name to help conversion. Default : None, meaning best effort to convert. Known database : jhu, wordometer interpret_region -- Boolean, default=False. If yes, the output should be only 'list'. 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
w |  | 





### first_db_translation


This function helps to translate from country name to standard for specific databases. It's the first step before final translation.   
One can easily add some database support adding some new rules for specific databases 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
w |  | 
db |  | 




