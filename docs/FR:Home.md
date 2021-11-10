TEST
Bienvenue au wiki de `PyCoA` en version française <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/FR.png" height="16px" alt="drapeau FR" />. Il existe aussi la [[version en anglais|Home:v1]] <img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/UK.png" height="16px" alt="UK flag" />.

<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/logo-anime.gif" height=150px /> 

[ⓒ pycoa.fr](http://pycoa.fr) - `PyCoA` version v1.0 - _Avril/Novembre 2020_

`PyCoA` (Python Covid Analysis) est un ensemble de code Python™ qui fournit :
- un accès simple aux bases de données sur la <a href="https://www.who.int/fr/emergencies/diseases/novel-coronavirus-2019/question-and-answers-hub">Covid19</a>. ;
- des outils pour représenter et analyser les données du Covid-19, comme des séries temporelles ou des cartes.

Cet environnement est pensé pour être accessible à des non-spécialistes : des lycéen·nes qui apprennent Python™, des étudiant·es, des journalistes scientifiques, voire même des chercheurs et chercheuses qui ne sont pas famillier·es avec l'extraction de données. Des analyses simples peuvent être directement effectuées, et des analyses plus poussées peuvent être produites par les personnes habituées à programmer en Python™. 

L'outil `PyCoA` assure l'accès à plusieurs bases de données et fourni un format standardisé pour les données. Il assure par ailleurs une jointure transparente avec des bases concernant géo-localisation (gestion des noms de pays ou de régions, possibilité de jointures sur des bases avec des description différentes, création de cartes). Ces informations de géolocalisation peuvent par ailleurs être utilisées pour d'autres application en dehors des aspects Covid19.

L'outil `PyCoA` est pensé pour être utilisé dans un environnement [jupyter](https://jupyter.org/), installé localement ou bien sur un serveur distant (comme le propose par exemple [google colaboratory](https://colab.research.google.com/)). Cela en simplifie l'[[installation|FR:Install:v1]] et assure des sorties graphiques performantes avec très peu de lignes de code pour l'utilisateur comme en attestent les quelques lignes de code suivantes et les sorties associées.

```python
import coa.front as cf
cf.plot(where=['France', 'Italy', 'United kingdom'], which='deaths', what='cumul')
cf.map(where=['world'],what='daily',when='01/04/2020')
cf.hist(where='middle africa', which='confirmed',what='cumul')
cf.get(where=['usa'], what='daily', which='recovered',output='pandas')
```
<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_plot_example.png" height="240" align=top /> 
<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_map_example.png" height="240" align=top /> 
<br/>
<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_hist_example.png" height="240" align=top /> 
<img src="https://github.com/coa-project/coa-project.github.io/blob/main/fig/pycoa_get_example.png" height="240" align=top />

## À propos

Physiciens sur des expériences en physique des particules au CERN ou en physique de la matière complexe, habitués à la gestion de _big data_, nous avons souhaité partager nos compétences en statistiques et gestion de données au plus grand nombre pour ce qui concerne l'analyse de données liées à la pandémie de la Covid19 au travers le monde. 
L'exploration de données et les statistiques devraient pouvoir aider toutes et tous à mieux comprendre un des phénomènes les plus importants de l'histoire récente.

Pour cela nous proposons le projet `PyCoA`, pour _Python™ Covid19 Analysis_, un outil de statistique qui peut s'utiliser en ligne, avec une interface simple et des schémas de modélisation clairs. La version proposée en ligne peut notamment s'utiliser au travers [Google Colaboratory](https://colab.research.google.com/), une infrastructure de notebooks Python™, et ce, sans aucun effort d'installation. 
Cela permet en outre un travail collaboratif par le partage de _notebooks_ sur le nuage de `google colab`, ce dernier permettant en outre l'utilisation d'une infrastructure de calcul énorme (incluant aussi des GPU pour de futures analyses de _deep learning_ des données Covid19). 

## Origines

Le projet `PyCoA`, initialement désigné `CoCoA`, a vu le jour initialement à partir de la participation en avril 2020 à l'hackathon organisé par UltraHack.org : [https://ultrahack.org/covid-19datahack](https://ultrahack.org/covid-19datahack) . Retenu en phase final mais non sorti vainqueur, le projet se veut _free_ et _opensource_ . Il continue d'évoluer depuis, son code est public ainsi que les `notebooks` qui servent de référence et d'exemples d'utilisation.

## Licence

Le projet `PyCoA` est sous [licence MIT](https://github.com/coa-project/pycoa/blob/main/LICENSE).

## Auteurs

* Tristan Beau - [Université de Paris](http://u-paris.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)
* Julien Browaeys - [Université de Paris](http://u-paris.fr) - [MSC laboratory](http://www.msc.univ-paris-diderot.fr/)
* Olivier Dadoun - [CNRS](http://cnrs.fr) - [LPNHE laboratory](http://lpnhe.in2p3.fr/)

## Contact 
* Page web de présentation : [`pycoa.fr`](http://pycoa.fr)
* Mail de contact : [`support@pycoa.fr`](mailto:support@pycoa.fr)
* Soumission d'erreurs : [issue sur site GitHub](https://github.com/coa-project/pycoa/issues)

## Et maintenant…
FR:Arborescence.md FR:Home.md         FR:IO.md           FR:Plot.md
FR:Histo.md        FR:Home:v1.md      FR:Notebooks.md    fig

* [[Arborescence|FR:Arborescence]]
* [[Notebooks|FR:Notebooks]]
* [[IO|FR:IO]]
* [[Plot|FR:Plot_et_al]]
* [[Histo|FR:Histo_et_al]]
