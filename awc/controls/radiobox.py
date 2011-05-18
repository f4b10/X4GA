#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/radiobox.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
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
import wx.lib.newevent
import awc.controls.mixin as cmix


class RadioBox(wx.RadioBox,\
               cmix.ControlsMixin):
    
    def __init__(self, parent = None, id = -1, label = "",
                 pos = wx.DefaultPosition, size = wx.DefaultSize, 
                 choices = ('test'), dim = -1, style = wx.RA_SPECIFY_COLS ):
        
        wx.RadioBox.__init__(self, parent, id, label, pos, size, choices,
                             dim, style)
        cmix.ControlsMixin.__init__(self)
        
        self.Bind(wx.EVT_SET_FOCUS,  self._OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self._OnFocusLost)
        
        self._values = []
        self._valtype = str
    
    def SetDataLink(self, name=None, values=None):
        if name is not None:
            self.SetName(name)
        if type(values) == tuple:
            values = list(values)
        self._values = values

    def SetValue(self, value):
        if value is None:
            #if   self._valtype == str: value = ''
            #elif self._valtype == int: value = 0
            value = self._values[0]
        #if type(value) == int:
            #value = str(value)
            #self._valtype = int
        if value == '' and ' ' in self._values:
            value = ' '
        if value in self._values:
            n = self._values.index(value)
            if n <= self.GetCount()-1:
                wx.RadioBox.SetSelection(self, n)

    def GetValue(self):
        out = None
        n = self.GetSelection()
        if n <= len(self._values)-1:
            out = self._values[n]
        if self._valtype == int:
            out = int(out)
        return out

    def SetBackgroundColour(self, color):
        pass

    def _OnFocusGained(self, event):
        self.AdjustBackgroundColor(self.IsEnabled())
        event.Skip()
    
    def _OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()
    
    #def Enable(self, e=True):
        #wx.RadioBox.Enable(self, e)
        #cmix.ControlsMixin.Enable(self, e)
    
    #def Disable(self):
        #self.Enable(False)
    
    #def IsEnabled(self):
        #return cmix.ControlsMixin.IsEnabled(self)
    
    def AdjustBackgroundColor(self, *args, **kwargs):
        cmix.ControlsMixin.AdjustBackgroundColor(self, *args, **kwargs)
        self.Update()
