#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/destsrc.py
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
import wx.grid as gl

import awc.util as awu
import anag.pdcrel_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab
bc = Azienda.Colours

import awc.controls.windows as aw
import awc.controls.dbgrid as dbglib

import stormdb as adb
import anag.dbtables as dba

import anag.clienti as clienti

import report as rpt


FRAME_TITLE = "Ricerca destinatari"


class DestinazSearchGrid(dbglib.DbGridColoriAlternati):
    """
    Grid ricerca destinatari.
    """
    def __init__(self, parent, dbdes):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetSize())
        
        self.dbdes = dbdes
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        
        des = dbdes
        pdc = des.pdc
        
        coldef = (
            ( 50, (cn(des, 'codice'),  "Cod.D",         _STR, False)),
            (250, (cn(des, 'descriz'), "Destinatario", _STR, False)),
            ( 50, (cn(pdc, 'codice'),  "Cod.C",         _STR, False)),
            (250, (cn(pdc, 'descriz'), "Cliente",      _STR, False)),
        )
        
        self._cols=coldef
        
        sizes =  [c[0] for c in coldef]
        colmap = [c[1] for c in coldef]
        
        canedit = False
        canins = False
        
        self.SetData(des.GetRecordset(), colmap, canedit, canins)
        
        for c,s in enumerate(sizes):
            self.SetColumnDefaultSize(c,s)
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallCli)
    
    def OnCallCli(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbdes.RowsCount():
            self.dbdes.MoveRow(row)
            pdcid = self.dbdes.id_pdc
            dlg = clienti.ClientiDialog(self, onecodeonly=pdcid)
            dlg.OneCardOnly(pdcid)
            dlg.CenterOnScreen()
            dlg.ShowModal()
            dlg.Destroy()
        event.Skip()

    
# ------------------------------------------------------------------------------


class DestinazSearchPanel(aw.Panel):
    """
    Panel ricerca destinatari.
    """
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.dbdes = dba.TabDestinaz()
        wdr.DestinazSearchFunc(self, True)
        def cn(x): return self.FindWindowByName(x)
        self.grides = DestinazSearchGrid(cn('gridsearch'), self.dbdes)
        self.UpdateDest()
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, cn('btnupdate'))
    
    def OnUpdate(self, event):
        self.UpdateDest()
        event.Skip()
    
    def UpdateDest(self):
        des = self.dbdes
        def cn(x): return self.FindWindowByName(x)
        d = cn('desdes').GetValue()
        des.ClearFilters()
        if d:
            des.AddFilter('dest.descriz LIKE %s', '%%%s%%' % d)
        des.Retrieve()
        self.grides.ResetView()

    def GetPanelDataSource(self):
        return self.dbdes
# ------------------------------------------------------------------------------


class DestinazSearchFrame(aw.Frame):
    """
    Frame ricerca destinatari.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(DestinazSearchPanel(self))
