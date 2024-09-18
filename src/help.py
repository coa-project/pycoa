import argparse
from colorama import init, Fore, Style

__version__ = '3.0.1'
__author__ = 'Tristan Beau, Julien Browaeys, Olivier Dadoun'
__github__ = 'https://github.com/src.project/pycoa
__web__ = 'http://pycoa.fr/'

def display_full_help():
    print()
    # Message d'accueil
    print(Fore.RED + "Bienvenue dans l'aide de Pysrc. + Style.RESET_ALL)

    # Affichage de l'aide 
    print()
    # Section liste des commandes basiques
    print(Fore.BLUE + "Liste des commandes" + Style.RESET_ALL)

    print()
    # Liste des commandes et leurs descriptions
    list_commands = [
        ('listwhom', "Liste les bases de données disponibles"),
        ('listwhom(True)', "Liste les bases de données disponibles en format pandas (recommandé)"),
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
        ('listtile', "Liste les textures disponibles pour les cartes"),
        ('listvisu', "Liste les options de visualisation disponibles pour les cartes"),
        ('dir(pycoa.', "Affiche toutes les méthodes")
    ]

    for command, description in list_commands:        
        print(Fore.GREEN + command.ljust(30) + Style.RESET_ALL + description)

    print()
    # Section pour les commandes de graphiques
    print(Fore.BLUE + "Commandes de graphiques" + Style.RESET_ALL)

    print()
    # Liste des commandes et descriptions pour les commandes de graphiques
    graph_commands = [
        ('plot', "Représentation de la donnée sélectionnée en fonction du temps (série temporelle)"),
        ('map', "Représentation sous forme de carte"),
        ('hist', "Représentation sous forme d'histogrammes"),
        ('get', "Récupérer les données en vue d'un traitement ultérieur")
    ]

    # sous commande de plot et hist
    for command, description in graph_commands:
        print(Fore.GREEN + command.ljust(30) + Style.RESET_ALL + description)
        # typeofplot
        if command == 'plot':
            plot_options = [
                ("typeofplot='date'(défaut)", "Le plot est une évolution temporelle de la variable épidémiologique étudiée."),
                ("typeofplot='menulocation'", "Si l'on désire comparer uniquement 2 variations temporelles parmi la liste where."),
                ("typeofplot='yearly'", "Permet de comparer les différentes années entre elles mois par mois."),
                ("typeofplot='spiral'", "Représentation en spiral, complémentaire de la précédente.")
            ]
            for plot_command, plot_description in plot_options:
                print("  " + Fore.YELLOW + plot_command.ljust(30) + Style.RESET_ALL + plot_description)
        # typeofhist
        if command == 'hist':
            hist_options = [
                ("typeofhist='bycountry'(défaut)", "Histogramme par pays"),
                ("typeofhist='byvalue'", "Histogramme en fonction des valeurs"),
                ("typeofhist='pie'", "Diagramme circulaire")
            ]
            for hist_command, hist_description in hist_options:
                print("  " + Fore.YELLOW + hist_command.ljust(30) + Style.RESET_ALL + hist_description)

    print()
    # Section exemple
    print(Fore.BLUE + "Exemple de requêtes avec Pysrc. + Style.RESET_ALL)

    print()
    # Liste des commandes et descriptions pour les commandes de graphiques
    exemple_commands = [
        ('listwhich', "pycoa.listwhich()"),
        ('plot', "pycoa.plot(where=['France', 'Italy', 'United kingdom'])"),
        ('map', "pycoa.map(where='world',what='daily',when='01/04/2020')"),
        ('hist', "pycoa.hist(where='middle africa', which='tot_confirmed',what='cumul')"),
        ('get', "pycoa.get(where='usa', what='daily', which='tot_recovered',output='pandas')")
    ]

    for command, description in exemple_commands:
        print(Fore.GREEN + command.ljust(30) + Style.RESET_ALL + Style.BRIGHT + description + Style.RESET_ALL)

    print()

def main():
    # Initialiser colorama
    init()

    parser = argparse.ArgumentParser(description=Fore.RED+"Aide supplémentaire de Pysrc.+Style.RESET_ALL, add_help=False)

    parser.add_argument('-h', '--help', action='store_true', help="Affiche l'aide complète de Pysrc.)
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}',
                        help="Affiche la version de Pysrc.)
    parser.add_argument('-a', '--author', action='store_true',
                        help="Affiche les auteurs de Pysrc.)
    parser.add_argument('-g', '--github', action='store_true', 
                        help="Affiche le github de Pysrc.)
    parser.add_argument('-w', '--web', action='store_true',
                        help="Affiche le site web de Pysrc.)

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        display_full_help()
    elif args.github:
        print(__github__)
    elif args.web:
        print(__web__)
    elif args.author:
        print(__author__)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
