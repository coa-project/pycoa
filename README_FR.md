#  PyCoA version v2 <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/logo-anime.gif" width="140px" align=bottom >

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![Made withJupyter](https://img.shields.io/badge/Made%20with-Jupyter-orange?style=for-the-badge&logo=Jupyter)](https://jupyter.org/try)
![GitHub last commit](https://img.shields.io/github/last-commit/pycoa/coa/dev?style=for-the-badge)
![GitHub](https://img.shields.io/github/license/pycoa/coa?style=for-the-badge)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/coa-project/pycoa/dev)
_Avril 2020 / Octobre 2021_

[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/UK.png" height="14px" alt="UK flag"> English  version ](https://github.com/coa-project/pycoa)
/
[<img src="https://github.com/coa-project/coa-project.github.io/raw/main/fig/FR.png" height="14px" alt="FR flag"> Version française ](https://github.com/coa-project/pycoa/blob/main/README_FR.md)

<!--center>
<iframe id="mobilehide" height="460" width="580" src="fig/mapFranceVariant.html" frameborder="0"></iframe>
</center-->

`PyCoA` (Python Covid Analysis) est un ensemble de code Python™ qui fournit :
- un accès simple aux bases de données sur la <a href="https://www.who.int/fr/emergencies/diseases/novel-coronavirus-2019/question-and-answers-hub">Covid19</a> ;
- des outils pour représenter et analyser les données de la Covid19, comme des séries temporelles ou des cartes.

Cet environnement est pensé pour être accessible à des non-spécialistes : des lycéen·nes qui apprennent Python™, des étudiant·es, des journalistes scientifiques, voire même des chercheurs et chercheuses qui ne sont pas famillier·es avec l'extraction de données. Des analyses simples peuvent être directement effectuées, et des analyses plus poussées peuvent être produites par les personnes habituées à programmer en Python™.

L'outil `PyCoA` assure l'accès à plusieurs bases de données et fourni un format standardisé pour les données. Il assure par ailleurs une jointure transparente avec des bases concernant géo-localisation (gestion des noms de pays ou de régions, possibilité de jointures sur des bases avec des description différentes, création de cartes). Ces informations de géolocalisation peuvent par ailleurs être utilisées pour d'autres application en dehors des aspects Covid19.

L'outil `PyCoA` est pensé pour être utilisé dans un environnement [jupyter](https://jupyter.org/), installé localement ou bien sur un serveur distant (comme le propose par exemple [google colaboratory](https://colab.research.google.com/) ou [binder](https://mybinder.org/)). Cela en simplifie l'[installation](https://github.com/coa-project/pycoa/wiki/Installation) et assure grâce à la librairie [`Bokeh`](https://bokeh.org/) des sorties graphiques performantes avec très peu de lignes de code pour l'utilisateur comme en attestent les quelques lignes de code suivantes et les sorties associées.

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
<img src="https://raw.githubusercontent.com/wiki/coa-project/pycoa/figs/pycoa_get_example.png" height="240" width="300" align=top />

## À propos

Physiciens sur des expériences en physique des particules au [CERN](https://home.cern/) ou en physique de la matière complexe, habitués à la gestion de _big data_, nous avons souhaité partager nos compétences en statistiques et gestion de données au plus grand nombre pour ce qui concerne l'analyse de données liées à la pandémie de la Covid19 au travers le monde.
L'exploration de données et les statistiques devraient pouvoir aider toutes et tous à mieux comprendre un des phénomènes les plus importants de l'histoire récente.

Pour cela nous proposons le projet `PyCoA`, pour _Python™ Covid19 Analysis_, un outil de statistique qui peut s'utiliser en ligne, avec une interface simple et des schémas de modélisation clairs. La version proposée en ligne peut notamment s'utiliser au travers [Google Colaboratory](https://colab.research.google.com/) ou de [Binder](https://mybinder.org/), une infrastructure de notebooks Python™, et ce, sans aucun effort d'installation.
Cela permet en outre un travail collaboratif par le partage de _notebooks_ sur le nuage de `google colab`, ce dernier permettant de plus l'utilisation d'une infrastructure de calcul énorme (incluant aussi des GPU pour de futures analyses de _deep learning_ des données Covid19).

## Origines

Le projet `PyCoA`, initialement désigné `CoCoA`, a vu le jour initialement à partir de la participation en avril 2020 à l'hackathon organisé par [UltraHack.org](https://ultrahack.org/covid-19datahack).
Retenu en phase final mais non sorti vainqueur, le projet se veut libre et gratuit à code source ouvert. Il a continué d'évoluer depuis et a subi une mise à jour majeure lors du [Hackathon Covid19](https://hackathon-covid.fr) animé par la [Direction interministérielle de la transformation publique](https://www.modernisation.gouv.fr/) en avril 2021.

Son code est public ainsi que les `notebooks` et servent de références ou d'exemples d'utilisation lors d'animations ou d'ateliers (lors du [Salon Culture et Jeux Mathématiques 2021](https://salon-math.fr/) ou lors de la [Fête de la Science 2021](https://www.fetedelascience.fr/)).

## `PyCoA`: logiciel générique d'analyses numériques en `Python`
Le projet a été développé à l'origine pour des études épidémiologiques liées à la Covid19. Il pourra cependant être utilisé pour d'autres types d'études.   
Ainsi, des analyses comportant des données avec des séries temporelles associées à des variables numériques et géographiques, pourront utiliser `PyCoA`. Leurs études seront grandement simplifiées et ceux avec des représentations graphiques claires et précises .    


## Licence

Le projet `PyCoA` est sous [licence MIT](https://github.com/coa-project/pycoa/blob/main/LICENSE).

## Auteurs

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
