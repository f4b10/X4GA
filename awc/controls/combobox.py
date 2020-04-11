#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/combobox.py
# Author:       Marcello
# Data:          25 giu 2018 - 10:42:31
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------
# This file is part of X4GA
# 
# X4GA is free software: you can redistribute it and/or modify
# it under the terms of the Affero GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# X4GA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with X4GA.  If not, see <http://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------


import wx 
from wx.lib.buttons import * 
import wx.lib.colourdb 
import awc.controls.mixin as cmix

class ComboBoxWithPyData(wx.ComboBox):

    pyData=None

    def __init__(self, *args, **kwargs):

        wx.ComboBox.__init__(self, *args, **kwargs)
        self.pyData=[]
            
    def ClearAll(self):
        self.pyData=[]
        wx.ComboBox.Clear(self)
        
    def Append(self, text, pyData=None):
        wx.ComboBox.Append(self, text)
        self.pyData.append(pyData)
        
    def GetPyData(self, n):
        return self.pyData[n]
    
    def GetSelectedPyData(self):
        n=self.GetSelection()
        if not n<0:
            pyData = self.GetPyData(n)
        else:
            pyData = None 
        return pyData
    
    def SetString(self, n, text, pyData=None):
        wx.ComboBox.SetString(self, n, text)
        self.pyData[n]=pyData
        

