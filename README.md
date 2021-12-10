#  PyCoA release v2 <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/logo-anime.gif" width="140px" align=bottom >

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![Made withJupyter](https://img.shields.io/badge/Made%20with-Jupyter-orange?style=for-the-badge&logo=Jupyter)](https://jupyter.org/try)
![GitHub last commit](https://img.shields.io/github/last-commit/pycoa/coa/dev?style=for-the-badge)
![GitHub](https://img.shields.io/github/license/pycoa/coa?style=for-the-badge)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/coa-project/pycoa/dev)
_April 2020/October 2021_

[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/UK.png" height="14px" alt="UK flag"> English  version ](https://github.com/coa-project/pycoa)
/
[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/FR.png" height="14px" alt="FR flag"> Version française ](https://github.com/coa-project/pycoa/blob/main/README_FR.md)

<!--center>
<iframe id="mobilehide" height="460" width="580" src="fig/pycoa_v2.10_mapFranceVariant.html" frameborder="0"></iframe>
</center-->

`PyCoA` (Python Covid Analysis) is a Python™ code framework which provides:
- a simple access to the main databases of <a href="https://www.who.int/fr/emergencies/diseases/novel-coronavirus-2019/question-and-answers-hub">Covid19</a>;
- tools to display and analyse data related to Covid19, such as time series or maps.

This environment is designed to be accessible to non-specialists: high-school students who are learning Python™, university students, data journalists, even scientists who are not particularly familiar with extracting data from online databases. Simple analyses can be readily performed, and deeper ones may be programmed by people with a reasonable Python™ proficiency.

The `PyCoA` tool provides access to several databases and reformats its data. `PyCoA` transparently joins the data with geo-localization databases (management of country or region names, creation of maps). This geolocation information can also be used for other applications outside the Covid19 problematics.

The `PyCoA` tool is designed to be used in a [jupyter](https://jupyter.org/) environment, installed locally or on a remote server (like [Google colaboratory](https://colab.research.google.com/) or [Binder](https://mybinder.org/)). This simplifies [installation](https://github.com/coa-project/pycoa/wiki/Install) and ensures, thanks to the [`Bokeh`](https://bokeh.org/) library, powerful graphical outputs with very few lines of code for the user, as the following examples attest.

```python
import coa.front as cf
cf.plot(where=['France', 'Italy', 'United kingdom'], which='deaths', what='cumul')
cf.map(where='world',what='daily',when='01/04/2020')
cf.hist(where='middle africa', which='confirmed',what='cumul')
cf.get(where='usa', what='daily', which='recovered',output='pandas')
```
<img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/pycoa_plot_example.png" height="240" align=top />
<img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/pycoa_map_example.png" height="240" align=top />
<br/>
<img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/pycoa_hist_example.png" height="240" align=top />
<img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/pycoa_get_example.png" height="240" align=top />

## About us

Physicists on particle physics experiments at [CERN](https://home.cern/) or studying complex matter, used to managing _big data_, we wished to share our skills in statistics and data management to the largest number of people interested in the analysis of data related to the Covid19 pandemic. We believe that data mining and statistics should help everyone to better understand one of the most important phenomena in recent history.

This is the reason why we have initiated the `PyCoA` project, which stands for _Python™ Covid19 Analysis_. This tool that can be used online, with a simple interface and clear modelling schemes. It is available online through [Google Colaboratory](https://colab.research.google.com/) or [Binder](https://mybinder.org/), a Python™ notebook infrastructure, with no installation effort. Collaborative work can be therefore performed, with access to a huge computational infrastructure (like GPUs for _deep learning_ analyses of Covid19 data).

## Origins

The `PyCoA` project, initially named `CoCoA`, was born from the participation in April 2020 to the hackathon organized by [UltraHack.org](https://ultrahack.org/covid-19datahack).
Selected in final phase, the project is free and open source. It has continued to evolve since then and underwent a major update during the [Hackathon Covid19](https://hackathon-covid.fr) organized by the [Direction interministérielle de la transformation publique](https://www.modernisation.gouv.fr/) in April 2021.

Its code is public as well as the `notebooks` and are used as references or examples of use during animations or workshops (during the [Salon Culture et Jeux Mathématiques 2021](https://salon-math.fr/) or during the [Fête de la Science 2021](https://www.fetedelascience.fr/)).

## PyCoA: generic software for numerical analysis in Python.
The project was originally developed for epidemiological studies related to Covid19. However, it can be used for other types of studies.   
Any analyses involving time series data associated with numerical and geographical variables can use `PyCoA`. Studies will be greatly simplified with clear and precise graphical representations.    


## License

The `PyCoA` project is under [MIT license](https://github.com/coa-project/pycoa/blob/main/LICENSE).

## Authors

* Tristan Beau - [Université de Paris](http://u-paris.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)
* Julien Browaeys - [Université de Paris](http://u-paris.fr) - [MSC laboratory](http://www.msc.univ-paris-diderot.fr/)
* Olivier Dadoun - [CNRS](http://cnrs.fr)/[in2p3](https://www.in2p3.cnrs.fr/) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)

## Institutions
<div class="row">
    <img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/logoCNRS.jpg" alt="CNRS" style="height:45px; padding: 5px;" />
    <img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/Universite_Paris_logo_horizontal.jpg" alt="UParis" style="height:45px; padding: 5px;" />
    <img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/logo_sorbonne_U.png" alt="SorbonneU" style="height:45px;" />
    <img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/logo_LPNHE_web_bleu_2011.gif" alt="LPNHE" style="height:45px; padding: 5px;" />
    <img src="http://www.msc.univ-paris-diderot.fr/plugins/kitcnrs/images/logo_msc.jpg" alt="MSC" style="height:45px; padding: 5px;" />
</div>

***
[ⓒpycoa.fr <img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/world-wide-web.png' height='25px' />](http://www.pycoa.fr) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/email.png' height='25px' align='bottom' />](mailto:support@pycoa.fr) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/twitter.png' height='25px' alt='Twitter'  />](https://twitter.com/pycoa_fr) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/github.png' height='25px' alt='GitHub' />](https://github.com/coa-project/pycoa) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/information.png' height='25px' alt='User manual' />](https://github.com/coa-project/pycoa/wiki) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/manual.png' height='25px' alt='Core documentation' />](https://www.pycoa.fr/docs) &nbsp;&nbsp;
[<img src='https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/mybinder.png' height='20px' alt='MyBinder launch' />](https://mybinder.org/v2/gh/coa-project/pycoa/dev)
