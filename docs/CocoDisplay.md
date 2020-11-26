# CocoDisplay




## Methods


### __init__




#### Parameters
name | description | default
--- | --- | ---
self |  | 
db |  | None





### standardfig




#### Parameters
name | description | default
--- | --- | ---
self |  | 
title |  | None
axis_type |  | "linear"
x_axis_type |  | "datetime"





### pycoa_date_plot


Create a Bokeh date chart from pandas input (x axis is a date format)   
Keyword arguments ----------------- - babepandas : pandas where the data is considered - input_names_data : variable from pandas data. * variable or list of variables available in babepandas (i.e available in the babepandas columns name  ) * If pandas is produced from pycoa get_stat method 'diff' or 'cumul' variable are available - title: title for the figure , no title by default - width_height : width and height of the figure,  default [400,300]   
Note ----------------- HoverTool is available it returns location, date and value 

#### Parameters
name | description | default
--- | --- | ---
babepandas |  | 
input_names_data |  | None
title |  | None
width_height |  | None





### min_max_range


Return a cleverly rounded min and max giving raw min and raw max of data. Usefull for hist range and colormap 

#### Parameters
name | description | default
--- | --- | ---
a_min |  | 
a_max |  | 





### pycoa_histo


Create a Bokeh histogram from a pandas input   
Keyword arguments ----------------- babepandas : pandas consided input_names_data : variable from pandas data. If pandas is produced from pycoa get_stat method then 'diff' and 'cumul' can be also used title: title for the figure , no title by default width_height : as a list of width and height of the histo, default [500,400] bins : number of bins of the hitogram default 50 date : - default 'last' Value at the last date (from database point of view) and for all the location defined in the pandas will be computed - date Value at date (from database point of view) and for all the location defined in the pandas will be computed - 'all' Value for all the date and for all the location will be computed Note ----------------- HoverTool is available it returns position of the middle of the bin and the value. In the case where date='all' i.e all the date for all the location then location name is provided 

#### Parameters
name | description | default
--- | --- | ---
babepandas |  | 
input_names_data |  | None
bins |  | None
title |  | None
width_height |  | None
date |  | "last"





### scrolling_menu


Create a Bokeh plot with a date axis from pandas input   
Keyword arguments ----------------- babepandas : pandas where the data is considered input_names_data : variable from pandas data . If pandas is produced from cocoas get_stat method the 'diff' or 'cumul' are available A list of names_data can be given title: title for the figure , no title by default width_height : width and height of the figure,  default [400,300]   
Note ----------------- HoverTool is available it returns location, date and value 

#### Parameters
name | description | default
--- | --- | ---
babepandas |  | 
input_names_data |  | None
title |  | None
width_height |  | None





### CrystalFig




#### Parameters
name | description | default
--- | --- | ---
self |  | 
crys |  | 
err_y |  | 





### get_pandas


Retrieve the pandas when CoCoDisplay is called 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### __delete__




#### Parameters
name | description | default
--- | --- | ---
self |  | 
instance |  | 





### save_map2png


Save map as png geckodriver and PIL packages are needed 

#### Parameters
name | description | default
--- | --- | ---
map |  | None
pngfile |  | "map.png"





### save_pandas_as_png




#### Parameters
name | description | default
--- | --- | ---
df |  | None
pngfile |  | "pandas.png"





### return_map


Create a Folium map from a pandas input   
Keyword arguments ----------------- babepandas : pandas consided which_data: variable from pandas data. If pandas is produced from pycoa get_stat method then 'diff' and 'cumul' can be also used width_height : as a list of width and height of the histo, default [500,400] date : - default 'last' Value at the last date (from database point of view) and for all the location defined in the pandas will be computed - date Value at date (from database point of view) and for all the location defined in the pandas will be computed 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
mypandas |  | 
which_data |  | None
width_height |  | None
date |  | "last"





### sparkline


Returns a HTML image tag containing a base64 encoded sparkline style plot 

#### Parameters
name | description | default
--- | --- | ---
data |  | 
figsize |  | 





### spark_pandas


Return pandas : location as index andwhich_data as sparkline (latest 30 values) 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
pandy |  | 
which_data |  | 




