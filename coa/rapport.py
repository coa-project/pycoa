# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - april 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file

Module : rapport

About
-----
This is the PyCoA rapport module it gives all available information concerning a database key words
"""
from coa.error import CoaKeyError, CoaTypeError, CoaConnectionError, CoaNotManagedError

def keyswords_info(namedb,keys):
        '''
        Return information on the available keyswords for the database selected
        '''
        mydico = {}
        if namedb == 'spf':
            spfdic = {
            'Prc_tests_PCR_TA_crible' : '% de tests PCR criblés parmi les PCR positives',
            'Prc_susp_501Y_V1' : '% de tests avec suspicion de variant 20I/501Y.V1 (UK)',
            'Prc_susp_501Y_V2_3' : ' % de tests avec suspicion de variant 20H/501Y.V2 (ZA) ou 20J/501Y.V3 (BR)',
            'Prc_susp_IND' : '% de tests avec une détection de variant mais non identifiable',
            'Prc_susp_ABS' : '% de tests avec une absence de détection de variant'
            }
            mydico = spfdic
        elif namedb == 'opencovid19':
            op19 = {
            'tot_deces':'FILLIT',
            'tot_cas_confirmes':'FILLIT',
            'cur_reanimation':'FILLIT',
            'cur_hospitalises':'FILLIT',
            'tot_gueris':'FILLIT',
            'tot_nouvelles_hospitalisations':'FILLIT',
            'tot_nouvelles_reanimations':'FILLIT',
            'tot_depistes':'FILLIT'
            }
            mydico = op19
        elif namedb == 'opencovid19national':
            op19nat = {
             'tot_deces':'FILLIT',
             'tot_cas_confirmes':'FILLIT',
             'tot_cas_ehpad':'FILLIT',
             'tot_cas_confirmes_ehpad':'FILLIT',
             'tot_cas_possibles_ehpad':'FILLIT',
             'tot_deces_ehpad':'FILLIT',
             'cur_reanimation':'FILLIT',
             'cur_hospitalises':'FILLIT',
             'tot_gueris':'FILLIT',
             'tot_nouvelles_hospitalisations':'FILLIT',
             'tot_nouvelles_reanimations':'FILLIT',
             'tot_depistes':'FILLIT'
              }
            mydico = op19nat
        elif namedb == 'owid':
            owid={
            'total_deaths':'FILLIT',
            'total_cases':'FILLIT',
            'total_tests':'FILLIT',
            'total_vaccinations':'FILLIT',
            'total_cases_per_million':'FILLIT',
            'total_deaths_per_million':'FILLIT',
            'total_vaccinations_per_hundred':'FILLIT',
            'cur_reproduction_rate':'FILLIT',
            'cur_icu_patients':'FILLIT',
            'cur_hosp_patients':'FILLIT',
            'cur_idx_positive_rate':'FILLIT'
             }
            mydico = owid
        elif namedb == 'jhu':
            jhu={
            'deaths':'FILLIT',
            'confirmed':'FILLIT',
            'recovered':'FILLIT'
             }
            mydico = jhu
        else:
            raise CoaKeyError('Error in the database selected, please check !')
        if keys not in mydico:
            raise CoaKeyError(keys + ': this keyword doesn\'t exist for this database !')
        else:
            return mydico[keys]

