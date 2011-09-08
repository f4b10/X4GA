#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/choice.py
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
import awc.controls.mixin as cmix


class Choice(wx.Choice, cmix.ControlsMixin):
    
    def __init__(self, *args, **kwargs):
        wx.Choice.__init__(self, *args, **kwargs)
        cmix.ControlsMixin.__init__(self)
        self.Bind(wx.EVT_SET_FOCUS,  self.OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)
    
    def OnFocusGained(self, event):
        self.AdjustBackgroundColor(self.IsEditable())
        event.Skip()
    
    def OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()
    
    def IsEditable(self):
        return True
    
    def GetValue(self):
        return self.GetClientData(self.GetSelection())


# ------------------------------------------------------------------------------


class ChoiceData(Choice):
    
    index_if_not_found = 0 #elemento da settare con SetValue se valore=None
    
    def __init__(self, *args, **kwargs):
        Choice.__init__(self, *args, **kwargs)
        self._values = []
    
    def SetDataLink(self, name=None, values=None):
        if name is not None:
            self.SetName(name)
        if type(values) == tuple:
            values = list(values)
        self._values = values

    def SetValue(self, value):
        if value is None:
            value = self._values[self.index_if_not_found]
        if value == '' and ' ' in self._values:
            value = ' '
        if value in self._values:
            n = self._values.index(value)
            if n <= self.GetCount()-1:
                wx.Choice.SetSelection(self, n)

    def GetValue(self):
        out = None
        n = self.GetSelection()
        if n <= len(self._values)-1:
            out = self._values[n]
        return out
