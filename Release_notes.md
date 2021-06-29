# PyCoa - Release_notes

## dev - 
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

