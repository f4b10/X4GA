#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/quadreg.py
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
import awc.controls.dbgrid as dbglib

import awc.controls.windows as aw
import contab.quadreg_wdr as wdr

import contab.dbtables as dbc

import contab
from contab.dataentry import REG_MODIFIED, REG_DELETED

import Env
bt = Env.Azienda.BaseTab


FRAME_TITLE = "Controllo di quadratura registrazioni contabili"


class QuadRegGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbquad):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              idGrid='checkquadratura')
        
        self.dbquad = dbquad
        
        def cn(col):
            return self.dbquad._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            ( 80, (cn("reg_datreg"),  "Data reg.",    _DAT, True)),
            ( 40, (cn("cau_codice"),  "Cod.",         _STR, True)),
            (120, (cn("cau_descriz"), "Causale",      _STR, True)),
            ( 50, (cn("riv_codice"),  "Reg.Iva",      _STR, True)),
            ( 50, (cn("reg_numdoc"),  "Num.doc.",     _STR, True)),
            ( 80, (cn("reg_datdoc"),  "Data doc.",    _DAT, True)),
            (200, (cn("problema"),    "Problema su:", _STR, True)),
            (  1, (cn("reg_id"),      "#reg",         _STR, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = dbquad.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(-2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def OnDblClick(self, event):
        qua = self.dbquad
        row = event.GetRow()
        if row>=qua.RowsCount():
            return
        qua.MoveRow(row)
        try:
            cls = contab.RegConDialogClass(qua.reg_id)
            if cls:
                wx.BeginBusyCursor()
                dlg = cls(self)
                dlg.SetOneRegOnly(qua.reg_id)
                wx.EndBusyCursor()
                if dlg.ShowModal() in (REG_MODIFIED, REG_DELETED):
                    evt = contab.RegChangedEvent(contab._evtREGCHANGED, 
                                                 self.GetId())
                    evt.SetEventObject(self)
                    evt.SetId(self.GetId())
                    self.GetEventHandler().AddPendingEvent(evt)
                dlg.Destroy()
                event.Skip()
        except:
            pass


# ------------------------------------------------------------------------------


class QuadRegPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.dbquad = dbc.QuadReg()
        wdr.QuadRegFunc(self)
        cn = self.FindWindowByName
        d = Env.Azienda.Login.dataElab
        cn('datmin').SetValue(Env.DateTime.Date(d.year, 1, 1))
        cn('datmax').SetValue(d)
        self.gridquad = QuadRegGrid(cn('pangrid'), self.dbquad)
        self.Bind(contab.EVT_REGCHANGED, self.OnRegChanged)
        for name, func in (('butok', self.OnUpdateData),
                           ('butprint', self.OnPrintData)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnRegChanged(self, event):
        self.UpdateData()
        event.Skip()
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        cn = self.FindWindowByName
        d1, d2 = map(lambda x: cn(x).GetValue(), 'datmin datmax'.split())
        if not d1 or not d2:
            aw.awu.MsgDialog(self, "Definire le date limite del controllo")
            return
        wd = aw.awu.WaitDialog(self, maximum=self.dbquad.GetCicliCount())
        def Aggiorna(n, msg):
            wd.SetMessage(msg)
            wd.SetValue(n+1)
        quad = self.dbquad
        try:
            try:
                quad.Retrieve(d1, d2, Aggiorna)
            finally:
                wd.Destroy()
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args))
        self.gridquad.ChangeData(quad.GetRecordset())
        if quad.IsEmpty():
            aw.awu.MsgDialog(self, "Nessun problema riscontrato sulle registrazioni analizzate",
                             style=wx.ICON_INFORMATION)
    
    def OnPrintData(self, event):
        event.Skip()


# ------------------------------------------------------------------------------


class QuadRegFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(QuadRegPanel(self))
        self.CenterOnScreen()
