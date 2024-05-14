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
    display  
   """
   def __init__(self,db, geo,visu):
        vis=['bokeh','mplt','ascii']
        if visu not in vis:
            raise CoaError("Locale setting problem. Please contact support@pycoa.fr")
        else:  
            self.codisp = allvis.CocoDisplay(db, geo,visu)
   

   def pycoa_date_plot(self,input, input_field,**kwargs):  
      return self.codisp.pycoa_date_plot(input, input_field,**kwargs)

   def pycoa_spiral_plot(self, input, input_field,**kwargs):
       return self.codisp.pycoa_spiral_plot(**kwargs)

   def pycoa_scrollingmenu(self,input, input_field,**kwargs):
       return self.codisp.pycoa_scrollingmenu(input, input_field,**kwargs)
   
   def pycoa_yearly_plot(self,input, input_field,**kwargs):
       return self.codisp.pycoa_yearly_plot(**kwargs)
   
   def pycoa_histo(self, input, input_field,**kwargs):
       return self.codisp.pycoa_histo(input, input_field,**kwargs)
   
   def pycoa_horizonhisto(self,input, input_field,**kwargs):
       return self.codisp.pycoa_horizonhisto(input, input_field,**kwargs)
   
   def pycoa_pie(self, input, input_field,**kwargs):
       return self.codisp.pycoa_pie(input, input_field,**kwargs)
   
   def pycoa_mapfolium(self,  input,input_field,**kwargs):
       return self.codisp.pycoa_mapfolium( input,input_field,**kwargs)
   
   def tiles_list(self):
       return self.codisp.tiles_list()

   def pycoa_map(self, input,input_field,**kwargs):
       return self.codisp.pycoa_map(input,input_field,**kwargs)
   
   def pycoa_resume_data(self, input,input_field,**kwargs):
       return self.codisp.pycoa_resume_data(input,input_field,**kwargs)
   
   def pycoa_geodata(self, input,input_field,**kwargs):
       return self.codisp.pycoa_geodata(input,input_field,**kwargs)

