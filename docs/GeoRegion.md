# GeoRegion


GeoRegion class definition. Does not inheritate from any other class.   
It should raise only CoaError and derived exceptions in case of errors (see pycoa.error) 

## Methods


### __init__


__init__ member function.  

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_source




#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_region_list




#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_countries_from_region


it returns a list of countries for the given region name. The standard used is iso3. To convert to another standard, use the GeoManager class. 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
region |  | 





### get_pandas




#### Parameters
name | description | default
--- | --- | ---
self |  | 




