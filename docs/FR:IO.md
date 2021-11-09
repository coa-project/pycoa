# Les sorties

Si l'on souhaite travailler sur les données pour des traitements ultérieurs,
différentes types de sorties peuvent être demandées.
```python
cf.listoutput()
```

>['pandas', 'list', 'dict', 'array']

* Pandas dataframe
```python
A=cf.get(where=['usa'], what='daily', which='recovered',output='pandas')
type(A) : <class 'pandas.core.frame.DataFrame'>
A.head()
where 	date 	recovered 	daily 	weekly 	codelocation 	clustername 	cumul
0 	United States 	2020-01-22 	0 	0.0 	0.0 	USA 	United States 	0
1 	United States 	2020-01-23 	0 	0.0 	0.0 	USA 	United States 	0
2 	United States 	2020-01-24 	0 	0.0 	0.0 	USA 	United States 	0
3 	United States 	2020-01-25 	0 	0.0 	0.0 	USA 	United States 	0
4 	United States 	2020-01-26 	0 	0.0 	0.0 	USA 	United States 	0
...
```
* Liste
```python
A=cf.get(where=['usa'], what='daily', which='recovered',output='list')
```
* Dictionnaire
```python
A=cf.get(where=['usa'], what='daily', which='recovered',output='dict')
```
* Tableau
```python
A=cf.get(where=['usa'], what='daily', which='recovered',output='array')
```
Pour les list, dict & array les sorties n'ayant pas d'interet ne sont pas écrites 

# Les entrées
