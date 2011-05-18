#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/listbox.py
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


class ListBox(wx.ListBox, cmix.ControlsMixin):
    def __init__(self, *args, **kwargs):
        wx.ListBox.__init__(self, *args, **kwargs)
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
