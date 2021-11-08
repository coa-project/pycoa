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
Deux dossiers
* coa: ensemble des modules Python
  * error.py : module de gestion des erreurs
  * front.py :  module du `front end`
  * tools.py : module
  * covid19.py : module de gestion des base de données covid et de geographie
  * display.py : module graphique basé sur la librairie `bokeh`. Module appelé aussi `backend`
  * ffront.py  :
  * geo.py : module de gestion de la géographie.
* coabook : ensemble des notebooks
L'ensemble des notebooks sont dans le dossier coabook

# Utilisation de `pycoa`

<!---
<center>
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Panneau_travaux.svg/1164px-Panneau_travaux.svg.png" height="150px" />

Attention. Au 15 mars 2021, cette page est encore en cours de mise à jour de la version `v1.0` à la version `v2.0`.

Les informations que vous trouverez ci-après pourraient ne pas correspondre à la version `v2.0` actuelle. Si vous êtes impatients d'utiliser la nouvelle version, vous devriez demander à [`support@pycoa.fr`](mailto:support@pycoa.fr).
<hr/>Markdown
</center>
--->

Il faudra bien sûr une [[Installation|FR:Install]] correcte du package. On vérifiera celle-ci [[en effectuant le test de l'installation|FR:Install#tester-la-bonne-installation]] avant de continuer, et d'utiliser une version >= `v2.10`.

Il existe deux niveaux d'utilisation de `PyCoA` :
* L'utilisation simplifiée qui utilise le _frontend_ `front.py`, proposant un nombre de méthode et d'options réduit, suffisant pour la plupart des usages.
* L'utilisation avancée, avec gestion manuelle des instances des objets de `PyCoA`.

Nous décrivons dans cette page uniquement l'utilisation simplifiée dans le cadre du _frontend_.
Pour une description avancée des fonctionnalités de `PyCoA` on se référera à la [[référence|FR:Ref]].

# Exemples pratiques sous forme de _notebooks_

La consultation et l'exécution des exemples sont certainement la manière la plus explicite de comprendre les fonctionnalités de `PyCoA`. Nous proposons dans un premier temps  :

Nom | Description courte | sur GitHub | sur Colab | sur NbViewer
--- | --- | --- | --- | ---
`demo_coa` | Démonstration basique de `PyCoA`  | <a href="https://github.com/coa-project/coabook/blob/master/demo_pycoa.ipynb" /><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" height="20" alt="GitHub logo" /></a> | <a href="https://colab.research.google.com/github/coa-project/coabook/blob/master/demo_pycoa.ipynb" ><img src="https://colab.research.google.com/img/colab_favicon_256px.png" height="20" alt="Google colab logo" /></a> | <a href="https://nbviewer.jupyter.org/github/coa-project/coabook/blob/master/demo_pycoa.ipynb"><img src="https://nbviewer.jupyter.org/static/img/nav_logo.svg" height="20" alt="NbViewer logo" /></a>
`using_pycoa_in_depth` | Démonstration de fonctionnalités plus complexes, toujours dans le cadre du _frontend_ | <a href="https://github.com/coa-project/coabook/blob/master/using_pycoa_in_depth.ipynb" /><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" height="20" alt="GitHub logo" /></a> | <a href="https://colab.research.google.com/github/coa-project/coabook/blob/master/using_pycoa_in_depth.ipynb" ><img src="https://colab.research.google.com/img/colab_favicon_256px.png" height="20" alt="Google colab logo" /></a> | <a href="https://nbviewer.jupyter.org/github/coa-project/coabook/blob/master/using_pycoa_in_depth.ipynb"><img src="https://nbviewer.jupyter.org/static/img/nav_logo.svg" height="20" alt="NbViewer logo" /></a>

D'autres notebooks sont disponibles sur notre [page `coabook`](https://github.com/coa-project/coabook/blob/master/README.md).

# Base de données et données géographiques
## Importation du _frontend_
L'importation du module <code>coaenv</code> permet de charger le <code>frontend</code> ainsi qu'un certain nombre de variables d'environnements nécessaires au bon fonctionnement du logiciel.
```python
import coaenv as cf
```
Par défaut, et pour des raisons historiques, la base base donnée mondiale _JHU_ est sélectionnée. L'utilisateur ne sera pas surpris de voir apparaître:
```python
1) JHU aka Johns Hopkins database selected ...
Few information concernant the selected database :  jhu
2) Available key-words, which ∈ ['deaths', 'confirmed', 'recovered']
3) Example of location :  Honduras, Russian Federation, Nicaragua, Sao Tome and Principe, Belarus  ...
4) Last date data  2021-11-05
```
1) La base de donnée sélectionnée (ici JHU)
2) Données épidémiologiques disponibles pour la base de données considérée (ici ['deaths', 'confirmed', 'recovered']). Ces données seront accessibles par la variable <code>which</code>. Une et une seule variable est autorisée.
3) Données géographiques disponibles; suivant la granularité de la base de données considérées des informations par pays, regions ou sub-regions seront disponibles. Comme la database JHU est mondiale les données géographiques disponibles sont par pays et/ou par groupe de pays (regroupé géographiquement ou politiquement)
4) Dernière mise à jour de la base de données selectionnée. Si des données sont non disponibles le logiciel infère avec la donnée disponible au jour précédent.

L'importation initialise des variables internes `PyCoA`.
Lorsque les données statiques (géographiques par exemple) ont déjà été consultées, elles sont stockées localement pour réduire les requetes sur le réseau et accélérer `pycoa`. Enfin, si le réseau est indisponible pour les données dynamiques, un avertissement apparaît, et une ancienne version sera utilisée.
Cela nécessite donc une connexion réseau. Suivant la taille de la base selectionnée quelques secondes ou plusieurs dizaines de secondes
seront nécessaires.

La liste des bases disponibles est accessible avec <code>listwhom(detailed=False)</code>
```

cf.listwhom()
```
> `
['jhu',
 'owid',
 'jhu-usa',
 'spf',
 'spfnational',
 'opencovid19',
 'opencovid19national',
 'dpc',
 'covidtracking',
 'covid19india',
 'rki',
 'escovid19data',
 'phe',
 'sciensano',
 'dgs',
 'obepine',
 'moh']`


 <code>
 cf.getinfo('cur_hosp')
 </code>
 Pour changer de base, on utilisera la méthode <code>setwhom('Nom de la Base')</code> avec le nom de la base en argument.
 Par exemple
 ```python
 cf.setwhom('spf')
 ```
 Pour charger la base de donnée de Santé Publique France ou spf.
 Une fois chargée la liste des données épidémilogiques disponibles est renvoyée.
 `
 ['tot_dc',
  'cur_hosp',
  'tot_rad',
  'cur_rea',
  'tot_vacc',
  'tot_vacc2',
  'cur_idx_tx_incid',
  'cur_idx_R',
  'cur_idx_taux_occupation_sae',
  'cur_taux_pos',
  'cur_idx_Prc_tests_PCR_TA_crible',
  'cur_idx_Prc_susp_501Y_V1',
  'cur_idx_Prc_susp_501Y_V2_3',
  'cur_idx_Prc_susp_IND',
  'cur_idx_Prc_susp_ABS',
  'cur_idx_ti',
  'cur_idx_tp',
  'cur_taux_crib',
  'cur_idx_tx_A1',
  'cur_idx_tx_B1',
  'cur_idx_tx_C1',
  'tot_incid_hosp',
  'tot_incid_rea',
  'tot_incid_rad',
  'tot_incid_dc',
  'tot_P',
  'tot_T',
  'nb_A0',
  'nb_A1',
  'nb_B0',
  'nb_B1',
  'nb_C0',
  'nb_C1']
 `
 A tout moment cette liste est disponible via la méthode <code>listwhich()</code>
 `
 cf.listwhich()
 `

# Base de données et données épidémilogiques

Si l'argument True est demandé <code>cf.listwhom(detailed=True)</code> ou plus simplement <code>cf.listwhom(True)</code>
renvoie les granularités géographiques des bases de données sont renvoyées:
`
jhu  associated to:  World
owid  associated to:  World
jhu-usa  associated to:  United States of America
spf  associated to:  France
spfnational  associated to:  France
opencovid19  associated to:  France
opencovid19national  associated to:  France
dpc  associated to:  Italy
covidtracking  associated to:  United States of America
covid19india  associated to:  India
rki  associated to:  Germany
escovid19data  associated to:  Spain
phe  associated to:  United Kingdom
sciensano  associated to:  Belgium
dgs  associated to:  Portugal
obepine  associated to:  France
moh  associated to:  Malaysia
`

# Graphiques
## Plot
* Pour faire un tracé, le lieu doit impérativement être spécifié avec l'option `where`, qui peut comporter un pays unique, une région du monde, ou plusieurs pays, ou plusieurs régions, ou un mélange de pays et de régions. Par défaut, l'ensemble des lieux disponibles est pris en compte pour `where`. Les données à tracer sont précisées par l'option `which` (par défaut, décès de la CoVid19, mot clef `deaths`), et le type de données par l'option `what` (par défaut `cumul`, i.e. en mode cumulatif). Ainsi :

```python
cf.plot(where=['France', 'Italy', 'United kingdom'], which='deaths', what='cumul')
```
effectue le tracé de la série temporel du nombre de décès dans 3 pays européens en mode cumulatif.

Dans cet exemple, les mots clefs choisis pour `which` et `what` étant ceux par défaut, on aurait pu tout aussi bien écrire :

```python
cf.plot(where=['France', 'Italy', 'United kingdom'])
```

<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/v1.0/pycoa_plot_example.png" alt="pycoa_plot_example.png" />

Le tracé s'effectue par l'intermédiaire de la librairie `bokeh` qui permet d'effectuer des zooms ou bien de sauvegarder la figure. Par ailleurs, en interactif, on pourra utiliser le curseur pour avoir des informations à tel ou tel instant pour telle ou telle courbe.

* Le choix pour les données tracées s'effectue donc au travers les mots clefs `which` et `what`. Pour avoir la liste des options possibles :
```python
cf.listwhich()
```
> `['deaths', 'confirmed', 'recovered']`
c'est-à-dire _décès_, _cas confirmés_, _cas guéris_.

```python
cf.listwhat()
```
> `['cumul', 'daily', 'weekly']`
Il s'agit successivement :
 - des _données cumulées_,
 - des données _différentielles_ journalières,
 - des données _différentielles_ hebdomadaires.

 On peut également ajouter un champ de date d'intérêt au travers l'option `when` qui comprend soit 1 soit 2 dates successives, au format jj/mm/aaaa.
  - lorsqu'une unique date est donnée, cela donne la borne de fin du lot de données.
  - lorsque deux dates sont données, séparées par `:` , cela définit la tranche temporelle pour les données.

Il est enfin possible d'ajouter des options. La liste de celles-ci est accessible avec la fonction

```python
cf.listoption()
```
> `['nonneg', 'nofillnan', 'smooth7', 'sumall']`
Par défaut aucun option n'est spécifiée.
Les options correspondent à :
- `nonneg`, qui s'applique aux données cumulées qui doivent être croissantes, et qui corrige les données non croissantes afin d'avoir un différentiel journalié positif ou nul
- `nofillnan`. Par défaut, les valeurs invalides (`NaN` des données sont remplis avec les données des jours précédents. Avec cette option, les données invalides ne sont pas remplies.
- `smooth7` effectue un moyennage glissant sur 7 jour centré
- `sumall` effectue la somme des valeurs pour tous les lieux précisés.

Il est possible de cumuler plusieurs options. Par exemple :
```python
cf.plot(where='European Union',option=['sumall','smooth7'])
```

À propos de la localisation choisie au travers le mot clef `where`, la liste des régions disponibles est accessible via la fonction
```python
cf.listregion()
```

Il est possible de faire des sommes partielles de données pour des régions entières en utilisant la notation à double crochets. Ainsi, par exemple pour un histogramme :
```python
cf.hist(where=[['asia','africa','europe']],option='sumall')
```
<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_v2.10_region_sumall.png" alt="pycoa_v2.10_region_sumall.png" />

* Pour réaliser une carte, les arguments sont les mêmes. Mais on fait appel à la fonction `map`. Le champ de données tracé correspond à celui du dernier jour de données disponible. Ainsi
```python
cf.map(where=['world'],what='daily',when='01/04/2020')
```
produit une carte du monde du nombre de décès quotidien (mot clef `which='deaths'` par défaut), type de donnée différentiel `'daily'` au 1er avril 2020. En mode interactif dans un _notebook_, il est possible de déplacer le curseur sur chaque pays pour avoir une information quantitative sur celui-ci. Il est aussi possible d'effecter des zooms.

<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_v2.10_map_example.png" alt="pycoa_map_example.png" />

* Production d'histogramme
Il s'agit du même type de traitement que pour les cartes (données à une date donnée, soit la dernière enregistrée, soit précisée par le champ `when=...'`). Au lieu d'une représentation géographique des données, celles-ci sont sous forme d'un histogramme pour le type de données choisies.

Deux types d'histogrammes sont possibles. Soit par localisation (par défaut)
```python
cf.setwhom('owid') # changing database
cf.hist(which='total_vaccinations') # default is for all countries
```
<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_hist_bycountry.png">

Soit par valeur :
```python
cf.hist(which='total_people_fully_vaccinated_per_hundred',typeofhist='byvalue',where='asia')
```
fournissant ainsi l'histogramme pour tous les pays d'Afrique Centrale du nombre de cas confirmés.

<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_v2.10_histval.png" alt="pycoa_v2.10_histval.png" />

Soit sous forme d'un camembert :
```python
cf.hist(which='cur_icu_patients',typeofhist='pie',where='european union')
```
qui donne la répartition des patients en soins intensifs dans les pays de l'Union Européenne.

<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_v2.10_pie.png" alt="pycoa_v2.10_pie.png" />


* Enfin, si l'on souhaite travailler sur les données pour des traitements ultérieurs, on pourra récupérer par exemple un `pandas` :
```python
cf.get(where=['usa'], what='daily', which='recovered',output='pandas')
```
pour les USA, en mode différentiel, pour les personnes guéries.

Pour la liste des formats de sorties :
```python
listoutput()
```
> `['list','dict','array','pandas']`

## À propos des bases disponibles
La liste disponible est fournie par :
```python
cf.listwhom()
```
et renvoie pour la version `v2.10` :
> `['jhu',
 'owid',
 'jhu-usa',
 'spf',
 'spfnational',
 'opencovid19',
 'opencovid19national',
 'dpc',
 'covidtracking',
 'covid19india',
 'rki',
 'escovid19data',
 'phe',
 'sciensano',
 'dgs',
 'obepine',
 'moh']`

 Certaines bases sont locales, d'autres mondiales. Pour chaque base sélectionnée à l'aide de `cf.setwhom( 'a_database_name' )`, la liste des champs `which` et les regions via `cf.listregion()` sont mises à jour.

 Les bases supportées correspondent à :
- `jhu` et `jhu-usa`, données mondiales et américaines du _Center for Systems Science and Engineering (CSSE) at Johns Hopkins University_ [https://github.com/CSSEGISandData/COVID-19/](ttps://github.com/CSSEGISandData/COVID-19/)
- `owid`, données Covid19 mondiales de _Our World in Data_, [https://github.com/owid/covid-19-data/](https://github.com/owid/covid-19-data/)
- `spf`, fusion de divers données de _Santé Publique France_, [https://www.data.gouv.fr/fr/search/?q=covid19](https://www.data.gouv.fr/fr/search/?q=covid19)
- `opencovid19`, données française du projet _OpenCovid19_, [https://www.github.com/opencovid19-fr](https://www.github.com/opencovid19-fr)
- `dpc`, base de données du _Dipartimento della Protezione Civile_ italien, [https://github.com/pcm-dpc/COVID-19/](https://github.com/pcm-dpc/COVID-19/)
- `covidtracking`, base de données américaine, projet `covidtracking` [https://covidtracking.com/data](https://covidtracking.com/data)
- `covid19india`, base de données indienne, [https://api.covid19india.org/](https://api.covid19india.org/)
- `rki`, base de données du Robert Koch Institute pour l'Allemagne [https://github.com/jgehrcke/covid-19-germany-gae](https://github.com/jgehrcke/covid-19-germany-gae)
- `escovid19data`, base de données espagnole, [https://github.com/montera34/escovid19data](https://github.com/montera34/escovid19data)
- `phe`, la base Public Health England pour le Royaume Uni [https://api.coronavirus.data.gov.uk](https://api.coronavirus.data.gov.uk)
- `sciensano` de l'institut national Belge [https://epistat.sciensano.be](https://epistat.sciensano.be)
- `dgs`, base du ministère portugais Direcção Geral de Saúde [https://github.com/dssg-pt/covid19pt-data](https://github.com/dssg-pt/covid19pt-data)
- `moh` base du ministère de la santé de Malaysie [https://github.com/MoH-Malaysia](https://github.com/MoH-Malaysia)

### _Frontend_ spécifique
Par défaut, la base `jhu` est appelée par le _frontend_. Si l'on souhaite utiliser une autre base, il faut appeler `cf.setwhom('autre_base')` comme nous l'avons vu.

Dans le cas particulier de la base `spf`, il est possible d'appeler directement un _frontend_ spécifique afin d'éviter de charger inutilement les données `jhu`. On utilisera alors :
```python
import coa.ffront as cf
```
où `ffront` se comprend comme étant le _french frontend_.

#### Utilisation avancée
Pour utiliser des fonctionnalités plus complexes de `PyCoA`, nous conseillons de se référer au _notebook_ [`using_pycoa_in_depth` sur GitHub](https://github.com/coa-project/coabook/blob/master/using_pycoa_in_depth.ipynb) ou bien à la [[référence du code|FR:Ref]].

#### Et ensuite…
* [[Référence|FR:Ref]]
* [[Autres analyses|FR:Analysis]]
* [[Évolutions prochaines|FR:Future]]
