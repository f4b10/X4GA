#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/awcontrols.py
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
import awc.controls.choice as awch

import stormdb as adb

import Env
bt = Env.Azienda.BaseTab


class TipoListinoChoice(awch.Choice):
    
    def __init__(self, *args, **kwargs):
        self.allow_none = kwargs.pop('allow_none', False)
        awch.Choice.__init__(self, *args, **kwargs)
        l = adb.DbTable(bt.TABNAME_TIPLIST, 'tiplist')
        l.AddOrder('tiplist.codice')
        l.Retrieve()
        for l in l:
            self.Append(('%s - %s' % (l.codice, l.descriz)))
        if self.allow_none:
            self.Append('')
        self.dbtlis = l
    
    def SetValue(self, value):
        l = self.dbtlis
        if value is None:
            if self.allow_none:
                self.SetSelection(self.GetCount()-1)
        elif l.Locate(lambda x: x.id == value):
            self.SetSelection(l.RowNumber())
    
    def GetValue(self):
        l = self.dbtlis
        try:
            l.MoveRow(self.GetSelection())
        except:
            return None
        return l.id

if __name__ == '__main__':
    
    db = adb.DB()
    if not db.Connect(host='localhost', user='x4user', passwd='x4user', db='x4_niris'):
        print db.dbError.description
        import sys
        sys.exit()
    
    a = wx.PySimpleApp()
    
    f = wx.Frame(None, -1, 'test')
    p = wx.Panel(f)
    test = TipoListinoChoice(p, allow_none=True)
    
    def OnSelected(event):
        o = event.GetEventObject()
        v = o.GetValue()
        if v == 3:
            o.SetValue(None)
    
    f.Bind(wx.EVT_CHOICE, OnSelected, test)
    
    f.Show()
    
    test.SetValue(3)
    
    a.MainLoop()
