# GeoInfo


GeoInfo class definition. No inheritance from any other class.   
It should raise only CoaError and derived exceptions in case of errors (see pycoa.error) 

## Methods


### __init__


__init__ member function.  

#### Parameters
name | description | default
--- | --- | ---
self |  | 
gm |  | 0





### get_list_field


return the list of supported additionnal fields available  

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_source


return the source of the information provided for a given field. 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
field |  | None





### add_field


this is the main function of the GeoInfo class. It adds to the input pandas dataframe some fields according to the geofield field of input. The return value is the pandas dataframe.   
Arguments : field    -- should be given as a string of list of strings and should be valid fields (see get_list_field() ) Mandatory. input    -- provide the input pandas dataframe. Mandatory. geofield -- provide the field name in the pandas where the location is stored. Default : 'location' overload -- Allow to overload a field. Boolean value. Default : False 

#### Parameters
name | description | default
--- | --- | ---
self |  | 




