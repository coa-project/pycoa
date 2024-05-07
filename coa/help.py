import argparse
from colorama import init, Fore, Style

__version__ = '2.22.1'
__author__ = 'Tristan Beau, Julien Browaeys, Olivier Dadoun'

def main():
    #init() 

    parser = argparse.ArgumentParser(description=Fore.RED+"Aide de Pycoa"+Style.RESET_ALL)
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}',
                        help="Affiche la version de Pycoa")
    parser.add_argument('-a', '--author', action='version', version=f'%(prog)s {__author__}',
                        help="Affiche les auteurs de Pycoa")

    # Ajoutez une sous-commande pour afficher les descriptions des fonctions
    subparsers = parser.add_subparsers(title='Liste des commandes :', dest='commande', description='')

    # Liste des commandes et leurs descriptions
    list_commands = [
        ('listwhom', "Liste les bases de données disponibles"),
        ('setwhom("DBname")', "Pour définir la base de données à utiliser"),
        ('getwhom', "Connaitre la base de données utilisée"),
        ('listwhich', "Liste les variables épidémiologiques disponibles dans la BD choisie"),
        ('listwhere', "Liste les départements disponibles"),
        ('listwhere(True)', "Liste les régions disponibles"),
        ('listwhat', "Données cumulées ou différentielles : cumul, daily, weekly"),
        ('listoption', "Liste les options disponibles"),
        ('listoutput', "Liste les formats de sortie disponibles : pandas, geopandas, list, dict, array"),
        ('listbypop', "Liste les options pour normaliser les courbes par le nombre d'habitants"),
        ('listplot', "Liste les types de graphiques disponibles"),
        ('dir(pycoa)', "Affiche toutes les méthodes")
    ]

    # Ajouter les sous-commandes avec les descriptions
    for command, description in list_commands:
        subparser = subparsers.add_parser(Fore.GREEN + command + Style.RESET_ALL, help=description)


    # Ajouter une nouvelle section pour les commandes de graphiques
    subparsers.add_parser(Fore.BLUE + "Commandes de graphiques" + Style.RESET_ALL, help="", description="")

    # Liste des commandes et descriptions pour les commandes de graphiques
    graph_commands = [
        ('plot', "Représentation de la donnée sélectionnée en fonction du temps (série temporelle)"),
        ('map', "Représentation sous forme de carte"),
        ('hist', "Représentation sous forme d'histogrammes, avec pour option : typeofhist='bycountry' (par défaut), typeofhist='byvalue', typeofhist='pie'"),
        ('get', "Récupérer les données en vue d'un traitement ultérieur")
    ]

    # Ajouter les sous-commandes avec les descriptions pour les commandes de graphiques
    for command, description in graph_commands:
        subparser = subparsers.add_parser(Fore.GREEN + command + Style.RESET_ALL, help=description)

    args = parser.parse_args()

if __name__ == '__main__':
    main()
