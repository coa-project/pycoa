# DataBase


DataBase class Parse a Covid-19 database and filled the pandas python objet : pandas_datase It takes a string argument, which can be: 'jhu','spf','owid' and 'opencovid19' The pandas_datase structure is based, for historical reason, on the JHU structure: ['location', 'date', key-words , 'cumul', 'diff'] 

## Methods


### __init__


Fill the pandas_datase 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
db_name |  | 





### get_db


Return the Covid19 database selected, so far: 'jhu','spf','owid' or 'opencovid19' 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_available_database


Return all the available Covid19 database : ['jhu', 'spf', 'owid', 'opencovid19'] 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_available_keys_words


Return all the available keyswords for the database selected Key-words are for: - jhu : ['deaths','confirmed','recovered'] * the data are cumulative i.e for a date it represents the total cases For more information please have a look to https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data - 'owid' : ['total_cases', 'new_cases', 'total_deaths', 'new_deaths', 'total_cases_per_million', 'new_cases_per_million', 'total_deaths_per_million', 'new_deaths_per_million', 'total_tests', 'new_tests', 'total_tests_per_thousand', 'new_tests_per_thousand', 'new_tests_smoothed', 'new_tests_smoothed_per_thousand', 'stringency_index'] For more information please have a look to https://github.com/owid/covid-19-data/tree/master/public/data/ - 'spf' : ['hosp', 'rea', 'rad', 'dc', 'incid_hosp', 'incid_rea', 'incid_dc', 'incid_rad', 'P', 'T', 'tx_incid', 'R', 'taux_occupation_sae', 'tx_pos'] No translation have been done for french keywords data For more information please have a look to  https://www.data.gouv.fr/fr/organizations/sante-publique-france/ - 'opencovid19' :['cas_confirmes', 'cas_ehpad', 'cas_confirmes_ehpad', 'cas_possibles_ehpad', 'deces', 'deces_ehpad', 'reanimation', 'hospitalises','nouvelles_hospitalisations', 'nouvelles_reanimations', 'gueris', 'depistes'] No translation have been done for french keywords data For more information please have a look to https://github.com/opencovid19-fr 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_database_url


Return all the url used to fill pandas_datase 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_rawdata


Return pandas_datase as a python dictionnaries: keys are keyswords and values are: | date-1    | date-2   | date-3     | ...   | date-i location     |           |          |            |       | location-1   |           |          |            |       | location-2   |           |          |            |       | location-3   |           |          |            |       | ... location-j   |           |          |            |       | 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### parse_convert_jhu


For center for Systems Science and Engineering (CSSE) at Johns Hopkins University COVID-19 Data Repository by the see homepage: https://github.com/CSSEGISandData/COVID-19 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### csv_to_pandas_index_location_date


Parse and convert CSV file to a pandas with location+date as an index 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
url |  | 





### pandas_index_location_date_to_jhu_format


Return a pandas in PyCoA Structure 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
mypandas |  | 





### fill_pycoa_field


Fill PyCoA variables with database data 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### flat_list


Flatten list function used in covid19 methods 

#### Parameters
name | description | default
--- | --- | ---
self |  | 
matrix |  | 





### get_current_days


Return a python dictionnary key = 'keywords values = [value_i @ date_i] 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_cumul_days


Return a python dictionnary cumulative key = 'keywords values = [cumululative value of current days return by get_current_days() from (date_0 to date_i)] 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_diff_days


Return a python dictionnary differential key = 'keywords values = [difference value between i+1 and ith days current days return by get_current_days()] 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_dates


Return all dates available in the current database 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_locations


Return available location countries / regions in the current database 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### get_stats


Return the pandas pandas_datase 'which' :   keywords 'location': list of location used in the database selected 'output': 'pandas' by default, 'array' return a Python array if output used: 'type': 'cumul' or 'diff' return cumulative of diffferential  of keywords value for all the  location selected 'option': default none can be 'nonneg'. In some cases negatives values can appeared due to a database updated, nonneg option will smooth the curve during all the period considered keys are keyswords from the selected database location        | date      | keywords     |  cumul        | diff ----------------------------------------------------------------------- location1       |    1      |  val1-1      |  cuml1-1      |  diff1-1 location1       |    2      |  val1-2      |  cumul1-2     |  diff1-2 location1       |    3      |  val1-3      |  cumul1-3     |  diff1-3 ... location1       | last-date |  val1-last   |  cumul1-last  |   diff1-last ... location-i      |    1      |  vali-1      |  cumli-1      |  diffi-1 location-i      |    2      |  vali-1      |  cumli-2      |  diffi-2 location-i      |    3      |  vali-1      |  cumli-3      |  diffi-3 ... 

#### Parameters
name | description | default
--- | --- | ---
self |  | 





### smooth_cases




#### Parameters
name | description | default
--- | --- | ---
self |  | 
cases |  | 





### get_posteriors




#### Parameters
name | description | default
--- | --- | ---
self |  | 
sr |  | 
window |  | 7
min_periods |  | 1




