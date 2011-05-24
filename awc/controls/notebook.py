#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/notebook.py
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
import awc.controls.focus as afocus
import awc.controls.mixin as mixin


class Notebook(wx.Notebook, mixin.ContainersMixin):
    curpage = 0
    newpage = -1
    
    def __init__(self, *args, **kwargs):
        wx.Notebook.__init__(self, *args, **kwargs)
        mixin.ContainersMixin.__init__(self)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged, self)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
    
    def OnPageChanged(self, event):
        if event.GetOldSelection() > -1:
            afocus.SetFirstFocus(self.GetPage(event.GetSelection()))
        event.Skip()
    
    def OnClick(self,evt):
        page = self.HitTest(evt.GetPosition())[0]  # only works with MSW
        if page > -1:  # else clicked on blank area, or platform is GTK
            self.newpage = page
        evt.Skip()
    
    def AddPage(self, page, *args, **kwargs):
        out = wx.Notebook.AddPage(self, page, *args, **kwargs)
        self._RecalcSize(page)
        return out
    
    def InsertPage(self, index, page, *args, **kwargs):
        out = wx.Notebook.InsertPage(self, index, page, *args, **kwargs)
        self._RecalcSize(page)
        return out
    
    def _RecalcSize(self, page):
        page.Fit()
        pw, ph = page.GetSize()
        cw, ch = self.GetClientSize()
        #aggiungo dei punti poiché SetClientSize fa esattamente come SetSize :(
        ns1 = (max(pw+8, cw), max(ph+24, ch))
        #inoltre cambio size 2 volte se no la pagina aggiunta potrebbe essere
        #disegnata con dimensioni errate (hey sizers do you do your job or not)
        ns2 = (ns1[0]+1, ns1[1]+1)
        if self.GetSize() < ns2:
            self.SetSize(ns2)
            self.SetSize(ns1)
            self.SetMinSize(self.GetSize())
