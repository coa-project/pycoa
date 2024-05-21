# -*- coding: utf-8 -*-
"""
Project : PyCoA
Date :    april 2020 - mai 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.display

About :
-------


"""

import coa.allvisu as allvis
from coa.error import *

class Display(object):
   """
    The display select the method requested by the visualization set by the user in the front
    It give a pointer to allvisu.py
   """
   def __init__(self,db, geo,chart=None):
       '''
        Init
       '''
       self.db = db
       self.geo = geo
       self.codisp = allvis.AllVisu(self.db, self.geo,chart)
       self.visu = 'bokeh'
   
   def setvisu(self,visu):
       '''
        Visualization seter
       '''
       vis=['bokeh','mplt','folium', 'seaborn']
       if visu not in vis:
            raise CoaError("Visualisation "+ visu + " not implemented setting problem. Please contact support@pycoa.fr")
       else: 
            self.visu = visu

   def getallvisu(self,):
       return self.codisp

   def getvisu(self,):
       '''
        Visualization geter
       '''
       return self.visu
   
   def pycoa_date_plot(self,**kwargs):  
       if self.visu == 'bokeh':
            return self.codisp.pycoa_date_plot(**kwargs)
       elif self.visu == 'mplt':
          return self.codisp.pycoa_mpltdate_plot(**kwargs)
       elif self.visu == 'seaborn':
            return self.codisp.pycoa_date_plot_seaborn(**kwargs)
       else:
            print('Not implemented !!')

   def pycoa_yearly_plot(self,**kwargs):
       if self.visu == 'bokeh':
            return self.codisp.pycoa_yearly_plot(**kwargs)
       elif self.visu == 'mplt':
            return self.codisp.pycoa_mpltyearly_plot(**kwargs)
       else:
            print('Not implemented !!')
   
   def pycoa_histo(self,**kwargs):
        if self.visu == 'bokeh':
            return self.codisp.pycoa_histo(**kwargs)
        elif self.visu == 'mplt': 
            return self.codisp.pycoa_mplthisto(**kwargs)
        elif self.visu == 'seaborn':
            return self.codisp.pycoa_hist_seaborn_verti(**kwargs)
        else:
            print('Not implemented !!')

   
   def pycoa_horizonhisto(self,**kwargs):
        if self.visu == 'bokeh':
            return self.codisp.pycoa_horizonhisto(**kwargs)
        elif self.visu == 'seaborn':
            return self.codisp.pycoa_hist_seaborn_hori( **kwargs)
        elif self.visu == 'mplt':
            return self.codisp.pycoa_mplthorizontalhisto(**kwargs)
        else:
            print('Not implemented !!')

   def pycoa_pie(self,**kwargs):
       if self.visu == 'bokeh':
            return self.codisp.pycoa_pie(**kwargs)
       elif self.visu == 'seaborn':
            return self.codisp.pycoa_pairplot_seaborn(**kwargs)
       elif self.visu == 'mplt':
            return self.codisp.pycoa_mpltpie(**kwargs)
       else:
            print('Not implemented !!') 
   
   def pycoa_map(self,**kwargs):
       '''
         Map of an input_field 
       '''
       print("HERE",type(self.visu),self.getvisu())
       if self.visu == 'bokeh':
            mappy = self.codisp.pycoa_map(**kwargs)
       elif self.visu == 'seaborn':
            mappy = self.codisp.pycoa_heatmap_seaborn(**kwargs)
       elif self.visu == 'mplt':
            mappy = self.codisp.pycoa_mpltmap(**kwargs)
       elif self.visu == 'folium':
            mappy = self.codisp.pycoa_mapfolium(**kwargs)
       else:
            print('Not implemented !!')
       return mappy 
    

   def pycoa_mapfolium(self,**kwargs):
       return self.codisp.pycoa_mapfolium(**kwargs)
   
   def pycoa_spiral_plot(self,**kwargs):
       return self.codisp.pycoa_spiral_plot(**kwargs)

   def pycoa_scrollingmenu(self,**kwargs):
       return self.codisp.pycoa_scrollingmenu(**kwargs)


