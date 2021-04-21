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
            'tot_dc':'tot_dc',
            'cur_hosp':'cur_hosp',
            'tot_rad':'tot_rad',
            'cur_rea':'cur_rea', 
            'cur_idx_tx_incid':'cur_idx_tx_incid',
            'cur_idx_R':'cur_idx_R',
            'cur_idx_taux_occupation_sae':'cur_idx_taux_occupation_sae',
            'cur_idx_tx_pos':'cur_idx_tx_pos', 
            'tot_vacc':'tot_vacc: (nom initial n_cum_dose1)',
            'tot_vacc2':'tot_vacc2: (nom initial n_cum_dose2)',
            'tot_incid_hosp':'tot_incid_hosp', 
            'tot_incid_rea':'tot_incid_rea', 
            'tot_incid_rad':'tot_incid_rad', 
            'tot_incid_dc':'tot_incid_dc', 
            'tot_P':'tot_P', 
            'tot_T':'tot_T',
            'Prc_tests_PCR_TA_crible' : 'Prc_tests_PCR_TA_crible: % de tests PCR criblés parmi les PCR positives',
            'Prc_susp_501Y_V1' : 'Prc_susp_501Y_V1: % de tests avec suspicion de variant 20I/501Y.V1 (UK)',
            'Prc_susp_501Y_V2_3' : 'Prc_susp_501Y_V2_3: % de tests avec suspicion de variant 20H/501Y.V2 (ZA) ou 20J/501Y.V3 (BR)',
            'Prc_susp_IND' : 'Prc_susp_IND: % de tests avec une détection de variant mais non identifiable',
            'Prc_susp_ABS' : 'Prc_susp_ABS: % de tests avec une absence de détection de variant'
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
            'total_vaccinations_per_hundred':'total_vaccinations_per_hundred: COVID19 vaccine doses administered per 100 people',
            'cur_reproduction_rate':'FILLIT',
            'cur_icu_patients':'cur_icu_patients: (ICU: intensive care unit)',
            'cur_hosp_patients':'FILLIT',
            'cur_idx_positive_rate':'FILLIT'
             }
            mydico = owid
        elif namedb == 'jhu':
            jhu = {
            'deaths':'deaths: counts include confirmed and probable (where reported).',
            'confirmed':'confirmed: counts include confirmed and probable (where reported).',
            'recovered':'recovered: cases are estimates based on local media reports, and state and local reporting when available, and therefore may be substantially lower than the true number. US state-level recovered cases are from COVID Tracking Project (https://covidtracking.com/)'
             }
            mydico = jhu
        elif namedb == 'jhu-usa':
            jhuusa = {
            'deaths':'deaths: counts include confirmed and probable (where reported).',
            'confirmed':'confirmed: counts include confirmed and probable (where reported).'
            }
            mydico = jhuusa
        elif namedb == 'covid19india':
            india = {
            'Deceased':'Deceased',
            'Confirmed':'Confirmed',
            'Recovered':'Recovered',
            'Tested':'Tested'
            }
            mydico = india
        elif namedb == 'dpc':
            ita = {
            'tot_casi':'tot_casi'
            }
            mydico = ita
        else:
            raise CoaKeyError('Error in the database selected, please check !')
        if keys not in mydico:
            raise CoaKeyError(keys + ': this keyword doesn\'t exist for this database !')
        else:
            return mydico[keys]

