# PyCoa - Release_notes

## v2.01 - march 2021 - Minor improvements
- New local database support : USA (Covidtracking), ITA (dpc), IND (covid19india)
- concerning IND: since we don't have a json file description of 'Telangana','Ladakh',
the covid19 for those states have been merged respectively to 'Andhra Pradesh' and
'Jammu and Kashmir'
- Bug solved for SPF (csv format change), and new data added (2nd vaccination information)
- Minor improvements and code structure modification
- fix bug on date_slider (not fully tested with the front end)

## v2.0 - february 2021 - Major release 
- Supporting more than one database : worldwide (OWID) and local, USA (JHU-USA) and FRANCE (SPF, OpenCovid19)
- Management of local countries with GeoCountry class
- Major improvement in graphical output, data processing, frontend
- Automatic cache system, and coacache data if available

## v1.0 - november 2020 - Major release
- First official release : support of the worldwide JHU database
