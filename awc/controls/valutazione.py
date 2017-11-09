#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/valutazione.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
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

import string
import wx

import images



import awc.controls.windows as aw

class Star(wx.BitmapButton):
    selected = None
    def __init__(self, *args, **kwargs):

        self.StarSelected = images.getStarSiBitmap()
        self.StarDeselected = images.getStarNoBitmap()
        self.StarMidSelected = images.getStarNiBitmap()

        wx.BitmapButton.__init__(self, *args, **kwargs)
        self.selected = False

    def Select(self):
        self.selected = True
        self.SetBitmapLabel(self.StarSelected)
        self.Refresh()

    def Deselect(self):
        self.selected = False
        self.SetBitmapLabel(self.StarDeselected)
        self.Refresh()

    def MidSelect(self):
        self.selected = True
        self.SetBitmapLabel(self.StarMidSelected)
        self.Refresh()



class StarPanel(aw.Panel):
    value = None

    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        w, h = self.Size
        self.star1    = Star(self, wx.ID_ANY, size=(h, h))
        self.star2    = Star(self, wx.ID_ANY, size=(h, h))
        self.star3    = Star(self, wx.ID_ANY, size=(h, h))
        self.star4    = Star(self, wx.ID_ANY, size=(h, h))
        self.star5    = Star(self, wx.ID_ANY, size=(h, h))
        self.SetValue(0)
        self.Better_Bind(wx.EVT_BUTTON, self.star1, self.OnStar, 1)
        self.Better_Bind(wx.EVT_BUTTON, self.star2, self.OnStar, 2)
        self.Better_Bind(wx.EVT_BUTTON, self.star3, self.OnStar, 3)
        self.Better_Bind(wx.EVT_BUTTON, self.star4, self.OnStar, 4)
        self.Better_Bind(wx.EVT_BUTTON, self.star5, self.OnStar, 5)

        topSizer        = wx.BoxSizer(wx.VERTICAL)
        inputOneSizer   = wx.BoxSizer(wx.HORIZONTAL)
        inputOneSizer.Add(self.star1, 0, wx.CENTER, 0)
        inputOneSizer.Add(self.star2, 0, wx.CENTER, 0)
        inputOneSizer.Add(self.star3, 0, wx.CENTER, 0)
        inputOneSizer.Add(self.star4, 0, wx.CENTER, 0)
        inputOneSizer.Add(self.star5, 0, wx.CENTER, 0)

        topSizer.Add(inputOneSizer, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(topSizer)
        topSizer.Fit(self)

    def Better_Bind(self, type, instance, handler, *args, **kwargs):
        self.Bind(type, lambda event: handler(event, *args, **kwargs), instance)

    def OnStar(self, evt, n):
        self.SetStar(n)
        evt.Skip()

    def SetValue(self, value):
        oldValue = self.value
        self.value = value
        for i in range(1,6):
            obj = getattr(self, 'star%s' % i)
            if i<=value:
                obj.Select()
            else:
                obj.Deselect()
        if not self.value==int(self.value):
            obj = getattr(self, 'star%s' % (int(self.value+1)))
            obj.MidSelect()
        self.Refresh()

    def SetStar(self, n):
        objStar = getattr(self, 'star%s' % n)
        if objStar.selected:
            if n==self.value:
                self.SetValue(n-1)
            else:
                self.SetValue(n)
        else:
            self.SetValue(n)

    def GetValue(self):
        return self.value
