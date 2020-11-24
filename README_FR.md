<!-- [Pycoa Logo](fig/pycoa_logo.png) -->
| Left-aligned | Center-aligned | 
| :---:        |     :---:      |
| ![](https://github.com/coa-project/coa-project.github.io/blob/main/fig/plot_exemple.png)  | ![](https://github.com/coa-project/coa-project.github.io/blob/main/fig/map_exemple.png) |
|![](https://github.com/coa-project/coa-project.github.io/blob/main/fig/histo_exemple.png) | ![](https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_get_example.png)|

# PyCoA version 1.0

_Avril/Novembre 2020_

[<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/FR.png" height="14px" alt="FR flag"> Version française ](https://github.com/coa-project/pycoa/blob/main/README_FR.md) /
[<img src="https://github.com/tjbtjbtjb/pycoa/blob/main/docs/fig/UK.png" height="14px" alt="UK flag"> English  version ](https://github.com/coa-project/pycoa/blob/main/README.md)


`PyCoA` (Python Covid Analysis) est un ensemble de code Python™ qui fournit :
- un accès simple aux bases de données sur la Covid-19 ;
- des outils pour représenter et analyser les données du Covid-19, comme des séries temporelles ou des cartes.

Elle est pensée pour être accessibles à des non-spécialistes : des lycéen·nes qui apprennent Python™, des étudiant·es, des journalistes scientifiques, voire même des chercheurs et chercheuses qui ne sont pas famillier·es avec l'extraction de données. Des analyses simples peuvent être directement effectuées, et des analyses plus poussées peuvent être produites par les personnes habituées à programmer en Pythpn™. Comme exemple, après avoir [installé PyCoA](https://github.com/tjbtjbtjb/pycoa/wiki/Install), les quelques lignes suivantes permettent de créer les figures en entête de cette courte documentation.

```python
import pycoa.pycoa as pc
cf.plot(where=['France', 'Italy', 'United kingdom'], which='deaths', what='cumul')
cf.map(where=['world'],what='daily',when='01/04/2020')
cf.hist(where='middle africa', which='confirmed',what='cumul')
cf.get(where=['usa'], what='daily', which='recovered',output='pandas')
```

PyCoA fonctionne :
- sur une installation locale de Python™ comme [`Spyder`](https://www.spyder-ide.org/),
- sur des plateforme `Jupyter` en ligne, comme [`Google Colab`](https://colab.research.google.com/),
- ou même avec un `docker`, comme [`mybinder`](https://mybinder.org/).


### Auteurs

* Tristan Beau - [Université de Paris](http://u-paris.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)
* Julien Browaeys - [Université de Paris](http://u-paris.fr) - [MSC laboratory](http://www.msc.univ-paris-diderot.fr/)
* Olivier Dadoun - [CNRS](http://cnrs.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)

