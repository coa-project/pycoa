* Enfin, si l'on souhaite travailler sur les données pour des traitements ultérieurs, on pourra récupérer par exemple un `pandas` :
```python
cf.get(where=['usa'], what='daily', which='recovered',output='pandas')
```
pour les USA, en mode différentiel, pour les personnes guéries.


