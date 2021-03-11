#  PyCoA version v2 <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/logo-anime.gif" width="140px" align=bottom > 

_Avril 2020 / Mars 2021_

[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/UK.png" height="14px" alt="UK flag"> English  version ](https://github.com/coa-project/pycoa)
/
[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/FR.png" height="14px" alt="FR flag"> Version française ](https://github.com/coa-project/pycoa/blob/main/README_FR.md)

<center>
<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_mapworld.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_mapworld.png"></a>
</center>

`PyCoA` (Python Covid Analysis) est un ensemble de code Python™ qui fournit :
- un accès simple aux bases de données sur la Covid-19 ;
- des outils pour représenter et analyser les données du Covid-19, comme des séries temporelles, des histogrammes ou des cartes.

|Série temporelle (cumulative) | Séries temporelles (G20) |
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_plot_sumall.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_plot_sumall.png"></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_plot_g20.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_plot_g20.png"></a>|

|Carte (OCDE) | Histogramme | 
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_map_oecd.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_map_oecd.png"></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_hist_bycountry.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_hist_bycountry.png"></a>|

Cette analyse est pensée pour être accessible à des non-spécialistes : des lycéen·nes qui apprennent Python™, des étudiant·es, des journalistes scientifiques, voire même des chercheurs et chercheuses qui ne sont pas famillier·es avec l'extraction de données. Des analyses simples peuvent être directement effectuées, et des analyses plus poussées peuvent être produites par les personnes habituées à programmer en Python™. Comme exemple, après avoir <a href="https://github.com/coa-project/pycoa/wiki/FR:Install" target=_blank>installé PyCoA</a>, les quelques lignes suivantes permettent de créer les figures en entête de cette courte documentation.

```python
import coa.front as cf
# default database is JHU
cf.plot(option='sumall') # default is 'deaths', for all countries
cf.plot(where='g20') # managing region
cf.map(where='oecd',what='daily',when='01/02/2021',which='confirmed')

cf.setwhom('owid') # changing database
cf.hist(which='total_vaccinations') # default is for all countries
```
Depuis la version `v2.0`, PyCoA accède également à des données locales comme [SPF](https://www.santepubliquefrance.fr/dossiers/coronavirus-covid-19) ou [OpenCovid19](https://github.com/opencovid19-fr) pour la France, [JHU-USA](https://coronavirus.jhu.edu/) pour les États-Unis. Nous pouvons allons obtenir des graphes comme ci-après. D'autres bases ont également été ajouté, pour l'Italie ou l'Inde par exemple.

|Données SPF | Données JHU-USA |
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_spf.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_spf.png" width=504></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_jhu-usafolium.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.0_jhu-usafolium.jpg" width=504></a>|

```python
cf.setwhom('spf') # Santé Publique France database
cf.map(which='tot_vacc',tile='esri') # Vaccinations, map view optional tile 

cf.setwhom('jhu-usa') # JHU USA database
cf.map(visu='folium') # deaths, map view with folium visualization output
```

PyCoA fonctionne actuellement au sein de _notebooks_ `Jupyter`, que l'installation soit locale ou bien sur des plateformes en ligne comme <a href="https://colab.research.google.com/" target=_blank>Google Colab</a>.

Un code de démonstration simple est accesible comme sous forme d'un notebook sur <a href="https://github.com/coa-project/coabook/blob/master/demo_pycoa.ipynb" target=_blank ><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" height="20" alt="GitHub logo" /> GitHub</a>, sur <a href="https://colab.research.google.com/github/coa-project/coabook/blob/master/demo_pycoa.ipynb" target=_blank ><img src="https://colab.research.google.com/img/colab_favicon_256px.png" height="20" alt="Google colab logo" /> Google Colab</a>, ou sur <a href="https://nbviewer.jupyter.org/github/coa-project/coabook/blob/master/demo_pycoa.ipynb" target=_blank ><img src="https://nbviewer.jupyter.org/static/img/nav_logo.svg" height="20" alt="NbViewer logo" /> Jupyter NbViewer</a>. D'autres _notebooks_ sont fournis via notre <a href="https://github.com/coa-project/coabook/blob/master/README.md" target=_blank >page coabook</a>.

La documentation complète se trouve sur <a href="https://github.com/coa-project/pycoa/wiki/FR:Home" target=_blank>le Wiki</a>.

### Auteurs

* Tristan Beau - [Université de Paris](http://u-paris.fr) - [laboratoire LPNHE](http://lpnhe.in2p3.fr/)
* Julien Browaeys - [Université de Paris](http://u-paris.fr) - [laboratoire MSC](http://www.msc.univ-paris-diderot.fr/)
* Olivier Dadoun - [CNRS](http://cnrs.fr) - Sorbonne Université](https://www.sorbonne-universite.fr/) - [laboratoire LPNHE](http://lpnhe.in2p3.fr/)

### Contact
* [`support@pycoa.fr`](mailto:support@pycoa.fr)
* La page web : [`pycoa.fr`](http://www.pycoa.fr/index_FR)
* Sur twitter : [`@pycoa_fr`](https://twitter.com/pycoa_fr)
