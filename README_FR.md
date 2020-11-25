#  PyCoA version v1.0 <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/logo-anime.gif" width="140px" align=bottom > 

_Avril/Novembre 2020_

[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/UK.png" height="14px" alt="UK flag"> English  version ](https://github.com/coa-project/pycoa)
/
[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/FR.png" height="14px" alt="FR flag"> Version française ](https://github.com/coa-project/pycoa/blob/main/README_FR.md)

`PyCoA` (Python Covid Analysis) est un ensemble de code Python™ qui fournit :
- un accès simple aux bases de données sur la Covid-19 ;
- des outils pour représenter et analyser les données du Covid-19, comme des séries temporelles ou des cartes.

<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_plot_example.png" height="200px" align=top> <img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_map_example.png" height="200px" align=bottom> 

<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_hist_example.png" height="200px" align=top> <img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/pycoa_get_example.png" height="200px" align=top>

Cette analyse est pensée pour être accessible à des non-spécialistes : des lycéen·nes qui apprennent Python™, des étudiant·es, des journalistes scientifiques, voire même des chercheurs et chercheuses qui ne sont pas famillier·es avec l'extraction de données. Des analyses simples peuvent être directement effectuées, et des analyses plus poussées peuvent être produites par les personnes habituées à programmer en Pythpn™. Comme exemple, après avoir <a href="https://github.com/coa-project/pycoa/wiki/FR:Install" >installé PyCoA</a>, les quelques lignes suivantes permettent de créer les figures en entête de cette courte documentation.

```python
import coa.front as cf
cf.plot(where=['France', 'Italy', 'United kingdom'], which='deaths', what='cumul')
cf.map(where=['world'],what='daily',when='01/04/2020')
cf.hist(where='middle africa', which='confirmed',what='cumul')
cf.get(where=['usa'], what='daily', which='recovered',output='pandas')
```

PyCoA fonctionne actuellement au sein de _notebooks_ `Jupyter`, que l'installation soit locale ou bien sur des plateformes en ligne comme <a href="https://colab.research.google.com/" >Google Colab</a>.

Un code de démonstration simple est accesible comme sous forme d'un <a href="https://github.com/coa-project/coabook/blob/master/demo_pycoa.ipynb" >notebook sur GitHub</a> ou bien directement en tant que <a href="https://colab.research.google.com/github/coa-project/coabook/blob/master/demo_pycoa.ipynb">Google Colab notebook</a>.

La documentation complète se trouve sur <a href="https://github.com/coa-project/pycoa/wiki/FR:Home" >le Wiki</a>.

### Auteurs

* Tristan Beau - [Université de Paris](http://u-paris.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)
* Julien Browaeys - [Université de Paris](http://u-paris.fr) - [MSC laboratory](http://www.msc.univ-paris-diderot.fr/)
* Olivier Dadoun - [CNRS](http://cnrs.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)

### Contact
* [`support@pycoa.fr`](mailto:support@pycoa.fr)
* This page : [`pycoa.fr`](http://pycoa.fr)
* Sur twitter : [`@pycoa_fr`](https://twitter.com/pycoa_fr)
