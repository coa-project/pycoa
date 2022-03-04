# PyCoa - Release_notes

## dev
-  

## v2.20
- Includes population information for USA and France.
- Add yearly and spiral plots
- Includes now insee (FR) and europa db
- Remove tile 'positron' for maps
- Normalization by population available for full population
- Fixing various plot titles issues
- Can switch between dense and standard geometry for countries allowing it (ESP, FRA, USA)
- Adding usefull geo function for regions / subregions
- Fixing text boundaries and size for pies
- Add Insee, Risklayer, Greece and Cyprus db
- Add spiral plot
- Map label uniformization using  pycoa_pimpmap method (maplabel: text, spiral and spark)
- Add geopandas output in the front get method
- Figure bokeh can be retrieved in the front (this give the opportunity to have a pointer to the axis, colormap ...)

## v2.11
- Mv coabook to the current folder
- remove coadocker from git no more usefull
- Decorator uniformization in the front
- Use kwargs in the backend remove dico
- date_plot with several variable and several location
- add mode : mode=vline or hline
- Use @wraps in the decorator to get the real name and doctring of each method
- When which='cur_' change the default title
- add new spf value nbre_pass_corona
- mv jhu which to 'tot'_which to avoid to cumul al already cumul value
- when option = sumall + smooth7 do sumall and smooth and not the opposite
- use cumsum new_tests to produce total_test in owid since total_test was not available for France
- change tot_* to cur_ for sciensano db
- in the front get uses the parser decorator , it wasn't the case so far ...
- covid19india db change val to tot_val
- log to maplabel
- fix folium boundaries
- add geopandas output format in the front
- remove cumul replace by standard
- add GRC DB
- add CYP DB

## v2.10 -
- Map bug fixed for option='sumall'
- maplabel added for bokeh map   
- fix bug with smooth7 , in the case data non continious
- add opencovid19national datase, remove ephad data for opencovid19 (only available for national)
- add SPF variant and SI-DEP school (var: ti & tp)
- fix bug display: last date is lastest date with nonan in which columns
- add new class rapport to give a rapport on a given keywords
- fix color bug when 2 var. is displayed
- self.dates move after fill_missing_dates
- new national databases added : ESP, DEU, BEL, GBR, PRT
- jhu-usa code modification db (codelocation=location)
- could sumall for different sublist
- add Obepine french db
- add export and merger method
- change flat_list from covdi19 to staticmethod i.e remove self not needed
- keep owid : world field -> change to owid_* & population value
- various sumall and region sumall graphical issues
- add sumall with list of list, for instance [['EU'],['Africa']]
- if which is tot_ or total_ cumul = value
## v2.02 - march 2021 - Import decorators modifciation inside the display
- New standard output is pandas dataframe
- Bug solved for a SPF database which has changed
- Some bugs solved for Windows based machines
- Added pie chart representation (hist with typeofhist='pie' option)
- Simplication on bokeh geo
- Fixed bug on horizontal histo label
- Added date_slider in the front end for hist (except byvalue) and map
- Optimized style of code writing (pyCharm recommandations), and docstrings corrections

## v2.01 - march 2021 - Minor improvements
- New local database support : USA (Covidtracking), ITA (dpc), IND (covid19india)
- concerning IND: since we don't have a json file description of 'Telangana','Ladakh',
the covid19 for those states have been merged respectively to 'Andhra Pradesh' and
'Jammu and Kashmir'
- Bug solved for SPF (csv format change), and new data added (2nd vaccination information)
- Minor improvements and code structure modification
- Fix bug on date_slider (not fully tested with the front end)

## v2.0 - february 2021 - Major release
- Supporting more than one database : worldwide (OWID) and local, USA (JHU-USA) and FRANCE (SPF, OpenCovid19)
- Management of local countries with GeoCountry class
- Major improvement in graphical output, data processing, frontend
- Automatic cache system, and coacache data if available

## v1.0 - november 2020 - Major release
- First official release : support of the worldwide JHU database
