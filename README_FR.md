#  PyCoA version v2 <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/logo-anime.gif" width="140px" align=bottom >

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![Made withJupyter](https://img.shields.io/badge/Made%20with-Jupyter-orange?style=for-the-badge&logo=Jupyter)](https://jupyter.org/try)
![GitHub last commit](https://img.shields.io/github/last-commit/pycoa/coa/dev?style=for-the-badge)
![GitHub](https://img.shields.io/github/license/pycoa/coa?style=for-the-badge)

_Avril 2020 / Mars 2022_

[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/UK.png" height="14px" alt="UK flag"> English  version ](https://github.com/coa-project/pycoa)
/
[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/FR.png" height="14px" alt="FR flag"> Version française ](https://github.com/coa-project/pycoa/blob/main/README_FR.md)

<center>
<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/mapFranceVariant.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/mapFranceVariant.png"></a>
</center>

`PyCoA` (Python Covid Analysis) est un ensemble de code Python™ qui fournit :
- un accès simple aux bases de données sur la Covid-19 ;
- des outils pour représenter et analyser les données du Covid-19, comme des séries temporelles, des histogrammes ou des cartes.

|Série temporelle (cumulative) | Séries temporelles (G20) |
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_plot_sumall.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_plot_sumall.png"></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_plot_g20.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_plot_g20.png"></a>|

|Carte (OCDE) | Histogramme (Monde) |
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_plot_oecd.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_plot_oecd.png"></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_hist_bycountry.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_hist_bycountry.png"></a>|

|PIE (UE) | Histogram by value (Asie) |
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_pie.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_pie.png"></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_histval.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_histval.png"></a>|

Cette analyse est pensée pour être accessible à des non-spécialistes : des lycéen·nes qui apprennent Python™, des étudiant·es, des journalistes scientifiques, voire même des chercheurs et chercheuses qui ne sont pas famillier·es avec l'extraction de données. Des analyses simples peuvent être directement effectuées, et des analyses plus poussées peuvent être produites par les personnes habituées à programmer en Python™. Comme exemple, après avoir <a href="https://github.com/coa-project/pycoa/wiki/FR:Install" target=_blank>installé PyCoA</a>, les quelques lignes suivantes permettent de créer les figures en entête de cette courte documentation.

```python
import coa.front as cf
# default database is JHU
cf.plot(option='sumall') # default is 'deaths', for all countries
cf.plot(where='g20') # managing region
cf.map(where='oecd',what='daily',when='01/02/2021',which='confirmed')

cf.setwhom('owid') # changing database
cf.hist(which='total_vaccinations') # default is for all countries
cf.hist(which='cur_icu_patients',typeofhist='pie',where='european union')
cf.hist(which='total_people_fully_vaccinated_per_hundred',typeofhist='byvalue',where='asia')
```
Depuis la version `v2.0`, PyCoA accède également à des données locales :
- [JHU-USA](https://coronavirus.jhu.edu/) ou [CovidTracking](https://covidtracking.com) pour les États-Unis,
- [SPF](https://www.santepubliquefrance.fr/dossiers/coronavirus-covid-19), [OpenCovid19](https://github.com/opencovid19-fr) ou [Obepine](https://www.reseau-obepine.fr/donnees-ouvertes/) pour la France,
- [DPC](https://github.com/pcm-dpc/COVID-19) pour l'Italie,
- [Covid19India](https://api.covid19india.org) pour l'Inde,
- [RKI](https://github.com/jgehrcke/covid-19-germany-gae) pour l'Allemagne,
- [Escovid19Data](https://github.com/montera34/escovid19data) pour l'Espagne,
- [PHE](https://api.coronavirus.data.gov.uk) pour le Royaume Uni,
- [Sciensano](https://epistat.sciensano.be) pour la Belgique,
- [DGS](https://github.com/dssg-pt/covid19pt-data) pour le Portugal,
- [MOH](https://github.com/MoH-Malaysia) pour la Malaysie.
- [RiskLayer](https://www.risklayer-explorer.com) pour un découpage Européen par région ou [Europa](https://github.com/ec-jrc/COVID-19/)_
- [IMED](https://github.com/iMEdD-Lab/open-data/tree/master/COVID-19) pour la Grèce,
- [GOVCY](https://www.data.gov.cy/) for Chypre,
- [INSEE](https://www.insee.fr) pour la France (tous décès, pas uniquement liés au COVID)

Nous pouvons allons obtenir des graphes comme ci-après. D'autres bases ont également été ajouté, pour l'Italie ou l'Inde par exemple.

|Données SPF | Données JHU-USA |
|------------|-------------|
|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_spf.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_spf.png" width=504></a>|<a href="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_v2.10_jhu-usafolium.html" target="_blank"><img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_v2.0_jhu-usafolium.jpg" width=504></a>|
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

***
[ⓒpycoa.fr <img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/world-wide-web.png' height='25px' />](http://www.pycoa.fr) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/email.png' height='25px' align='bottom' />](mailto:support@pycoa.fr) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/twitter.png' height='25px' alt='Twitter'  />](https://twitter.com/pycoa_fr) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/github.png' height='25px' alt='GitHub' />](https://github.com/coa-project/pycoa) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/information.png' height='25px' alt='User manual' />](https://github.com/coa-project/pycoa/wiki) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/manual.png' height='25px' alt='Core documentation' />](https://www.pycoa.fr/docs) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/mybinder.png' height='20px' alt='MyBinder launch' />](https://mybinder.org/v2/gh/coa-project/pycoa/dev)
