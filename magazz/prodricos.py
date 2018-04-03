#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/prodricos.py
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

import magazz.dbtables as dbm

import magazz.invent_wdr as wdr

Env = dbm.Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours


FRAME_TITLE = "Aggiornamento costo prodotti su movimenti"


class ProdRiCosGridRiepilogo(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbsin):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              idGrid='aggiorna_costi')
        
        self.dbsin = dbsin
        
        def cn(col):
            return dbsin._GetFieldIndex(col, inline=True)
        
        sin = self.dbsin
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        
        cols = (\
            ( 80, (cn("codice"),        "Codice",      _STR, True)),
            (240, (cn("descriz"),       "Descrizione", _STR, True)),
            ( 90, (cn("count_movzero"), "#Mov.Zero",   _NUM, True)),
            (  1, (cn("id"),            "#pro",        _STR, True)),)
                                                   
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData((), colmap, False, False)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class ProdRiCosPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        wdr.ProdRiCosFunc(self)
        cn = self.FindWindowByName
        
        self.dbsin = dbm.SintesiMovimentiSenzaCostoMemTable()
        self.gridriep = ProdRiCosGridRiepilogo(cn('pangridriep'), self.dbsin)
        for name, func in (('butver', self.OnVerifica),
                           ('butupd', self.OnAggiorna),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnVerifica(self, event):
        self.Verifica()
        event.Skip()
    
    def Verifica(self):
        sin = self.dbsin
        wx.BeginBusyCursor()
        try:
            self.dbsin.Retrieve(ssv=self.FindWindowByName('ssv').IsChecked())
        finally:
            wx.EndBusyCursor()
        self.gridriep.ChangeData(sin.GetRecordset())
        self.FindWindowByName('butupd').Enable(not sin.IsEmpty())
    
    def OnAggiorna(self, event):
        if self.AggiornaCosti():
            event.Skip()
    
    def AggiornaCosti(self):
        if aw.awu.MsgDialog(self, "Confermi l'aggiornamenti dei costi sui movimenti ?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
            return False
        wait = aw.awu.WaitDialog(self, message="Aggiornamento costo su movimenti in corso...")
        wx.BeginBusyCursor()
        try:
            o = self.dbsin.AggiornaCostoMovimenti(ssv=self.FindWindowByName('ssv').IsChecked())
        finally:
            wait.Destroy()
            wx.EndBusyCursor()
        if o:
            aw.awu.MsgDialog(self, "Elaborazione terminata", style=wx.ICON_INFORMATION)
        return o


# ------------------------------------------------------------------------------


class ProdRiCosFrame(aw.Frame):
    """
    Frame Aggiornamento costo prodotti su movimenti
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProdRiCosPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BUTUPD)
    
    def OnClose(self, event):
        self.Close()


# ------------------------------------------------------------------------------


class ProdRiCosDialog(aw.Dialog):
    """
    Dialog Aggiornamento costo prodotti su movimenti
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProdRiCosPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BUTUPD)
    
    def OnClose(self, event):
        self.EndModal(wx.ID_OK)
