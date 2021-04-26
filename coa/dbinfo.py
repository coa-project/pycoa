# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - april 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file
Module : report
About
-----
This is the PyCoA rapport module it gives all available information concerning a database key words
"""

def keyswords_info(namedb, keys):
        '''
        Return information on the available keyswords for the database selected
        '''
        mydico = {}
        if namedb == 'spf':
            spfdic = {
            'tot_dc':'tot_dc:FILLIT',
            'cur_hosp':'cur_hosp:FILLIT',
            'tot_rad':'tot_rad:FILLIT',
            'cur_rea':'cur_rea:FILLIT',
            'cur_idx_tx_incid':'cur_idx_tx_incid:FILLIT',
            'cur_idx_R':'cur_idx_R:FILLIT',
            'cur_idx_taux_occupation_sae':'cur_idx_taux_occupation_sae:FILLIT',
            'cur_idx_tx_pos':'cur_idx_tx_pos:FILLIT',
            'tot_vacc':'tot_vacc: (nom initial n_cum_dose1)',
            'tot_vacc2':'tot_vacc2: (nom initial n_cum_dose2)',
            'tot_incid_hosp':'tot_incid_hosp: Nombre total de personnes hospitalisées',
            'tot_incid_rea':'tot_incid_rea: Nombre total d\'admissions en réanimation',
            'tot_incid_rad':'tot_incid_rad: Nombre total de  retours à domicile',
            'tot_incid_dc':'tot_incid_dc: 	Nombre total de personnes  décédées',
            'tot_P':'tot_P: Nombre total de tests positifs',
            'tot_T':'tot_T: Nombre total de tests réalisés',
            'cur_idx_Prc_tests_PCR_TA_crible' : 'Prc_tests_PCR_TA_crible: % de tests PCR criblés parmi les PCR positives.',
            'cur_idx_Prc_susp_501Y_V1' : 'Prc_susp_501Y_V1: % de tests avec suspicion de variant 20I/501Y.V1 (UK).\n Royaume-Uni (UK): code Nexstrain= 20I/501Y.V1.',
            'cur_idx_Prc_susp_501Y_V2_3' : 'Prc_susp_501Y_V2_3: % de tests avec suspicion de variant 20H/501Y.V2 (ZA) ou 20J/501Y.V3 (BR).Afrique du Sud (ZA) : code Nexstrain= 20H/501Y.V2. Brésil (BR) : code Nexstrain= 20J/501Y.V3',
            'cur_idx_Prc_susp_IND' : 'Prc_susp_IND: % de tests avec une détection de variant mais non identifiable',
            'cur_idx_Prc_susp_ABS' : 'Prc_susp_ABS: % de tests avec une absence de détection de variant'
            }
            mydico = spfdic
        elif namedb == 'opencovid19':
            op19 = {
            'tot_deces':'tot_deces: total cumulé du nombre de décès au niveau national',
            'tot_cas_confirmes':'tot_cas_confirmes: total cumulé du nombre de cas confirmes au niveau national',
            'cur_reanimation':'cur_reanimation:  nombre de personnes en réanimation',
            'cur_hospitalises':'cur_hospitalises: nombre de personnes en hospitalisation',
            'tot_gueris':'tot_gueris: total cumulé du nombre de gueris au niveau national',
            'tot_nouvelles_hospitalisations':'tot_nouvelles_hospitalisations: total cumulé du nombre d\'hospitalisation au niveau national',
            'tot_nouvelles_reanimations':'tot_nouvelles_reanimations: tot_nouvelles_reanimations: total cumulé du nombre réanimations au niveau national',
            'tot_depistes':'tot_depistes: total cumulé du nombre de personnes dépistées (testées par PCR) au niveau national'
            }
            mydico = op19
        elif namedb == 'opencovid19national':
            op19nat = {
             'tot_deces':'tot_deces: total cumulé du nombre de décès',
             'tot_cas_confirmes':'tot_cas_confirmes: total cumulé du nombre de cas confirmés',
             'tot_cas_ehpad':'tot_cas_ehpad: total cumulé du nombre de cas en EHPAD',
             'tot_cas_confirmes_ehpad':'total cumulé du nombre de cas positifs en EHPAD',
             'tot_cas_possibles_ehpad':'tot_cas_possibles_ehpad:FILLIT',
             'tot_deces_ehpad':'total cumulé du nombre de décès en EHPAD',
             'cur_reanimation':'cur_hospitalises: nombre de personnes en reanimation',
             'cur_hospitalises':'cur_hospitalises: nombre de personnes en hospitalisation',
             'tot_gueris':'total cumulé du nombre de gueris',
             'tot_nouvelles_hospitalisations':'tot_nouvelles_hospitalisations: total cumulé du nombre d\'hospitalisation',
             'tot_nouvelles_reanimations':'tot_nouvelles_reanimations: tot_nouvelles_reanimations: total cumulé du nombre réanimations',
             'tot_depistes':'tot_depistes: total cumulé du nombre de personnes dépistées (testées par PCR)'
              }
            mydico = op19nat
        elif namedb == 'owid':
            owid={
            'total_deaths':'total_deaths:FILLIT',
            'total_cases':'total_cases:FILLIT',
            'total_tests':'total_tests: FILLIT',
            'total_vaccinations':'total_vaccinations:FILLIT',
            'total_cases_per_million':'total_cases_per_million:FILLIT',
            'total_deaths_per_million':'total_deaths_per_million:FILLIT',
            'total_vaccinations_per_hundred':'total_vaccinations_per_hundred: COVID19 vaccine doses administered per 100 people',
            'cur_reproduction_rate':'cur_reproduction_rate:FILLIT',
            'cur_icu_patients':'cur_icu_patients: (ICU: intensive care unit)',
            'cur_hosp_patients':'cur_hosp_patients:FILLIT',
            'cur_idx_positive_rate':'cur_idx_positive_rate:FILLIT'
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
            'Deceased':'Deceased:FILLIT',
            'Confirmed':'Confirmed:FILLIT',
            'Recovered':'Recovered:FILLIT',
            'Tested':'Tested:FILLIT'
            }
            mydico = india
        elif namedb == 'dpc':
            ita = {
            'tot_casi':'tot_casi::FILLIT'
            }
            mydico = ita
        else:
            raise CoaKeyError('Error in the database selected, please check !')
        if keys not in mydico:
            raise CoaKeyError(keys + ': this keyword doesn\'t exist for this database !')
        else:
            return mydico[keys]

