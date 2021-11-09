# Arborescence  du dossier  `pycoa`
```
pycoa
| __init__.py
| LICENSE          
| README_FR.md    
| README.md
| setup.py
| Release_notes.md
| environment.yml  
└─── coa              
|   │   error.py
|   │   front.py    
|   │   tools.py
|   |   covid19.py
|   |   display.py  
|   |   ffront.py  
|   |   geo.py
|
└─── coabook
    |   coaenv.py
    |   FdS2021.ipynb
    ...
    |   v1.0
```
On peut voir pluiseurs fichiers:
* __init__.py: fichier initialisation
* LICENSE: descrition de la licence          
* README_FR.md: le README en français    
* README.md: le README en anglais
* setup.py: le setup d'installation de en local
```python
python3 setup.py install
```
* Release_notes.md: tentative de description des différentes mise à jour
* environment.yml: fichier de descrition de module necessaire au fonctionnement de `Pycoa` dans `Binder`

Et deux dossiers
* coa: ensemble des modules Python
  * error.py : module de gestion des erreurs
  * front.py : module du `front end`
  * tools.py : module outils permet de gerer entre autre le niveau de verbosité 
```python
import coa.tools as ct
ct._verbose_mode=1
```
  * covid19.py : module de gestion des base de données covid et de geographie
  * display.py : module graphique basé sur la librairie `bokeh`. Module appelé aussi `backend`
  * ffront.py  :
  * geo.py : module de gestion de la géographie.
* coabook : ensemble des notebooks
L'ensemble des notebooks sont dans le dossier coabook
