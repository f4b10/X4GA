#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stagrip.py
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
awu = aw.awu

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb
import anag.dbtables as dba

import magazz.listini_wdr as wdr
from magazz.listini import ColonneDaStampareDialog

import report as rpt

import magazz.stalis as stalis


FRAME_CLIENTI_TITLE = "Griglia prezzi in vigore per il cliente"
FRAME_FORNIT_TITLE = "Griglia prezzi in vigore per il fornitore"


class GrigliaPrezziAttualiGrid(stalis.ListiniAttualiGrid):
    
    def __init__(self, parent, dblis, clifor):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, 
                                              size=parent.GetSize())
        
        self.dblis = lis = dblis
        self.clifor = clifor
        
        def cc(col):
            return lis._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        ws = 50
        wp = 90
        
        cols = []
        def a(x):
            cols.append(x)
        
        a((100, (cc("prod_codice"),  "Codice",      _STR, True)))
        a((300, (cc("prod_descriz"), "Prodotto",    _STR, True)))
        a(( wp, (cc("grip_prezzo"),  "Prezzo",      _PRZ, True)))
        
        if self.clifor == "C":
            cde = bt.MAGCDEGRIP
        elif self.clifor == "F":
            cde = bt.MAGCDEGRIF
        else:
            raise Exception, "Impossibile determinare se la griglia è per i clienti o per i fornitori"
        if cde:
            a(( 80, (cc("grip_ext_codice"),  "Codice Ext.",      _STR, False)))
            a((200, (cc("grip_ext_descriz"), "Descrizione Ext.", _STR, False)))
        
        if bt.MAGNUMSCO >= 1:
            a(( ws, (cc("grip_sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( ws, (cc("grip_sconto2"), "Sc.%2",       _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( ws, (cc("grip_sconto3"), "Sc.%3",       _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( ws, (cc("grip_sconto4"), "Sc.%4",       _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( ws, (cc("grip_sconto5"), "Sc.%5",       _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( ws, (cc("grip_sconto6"), "Sc.%6",       _SCO, True)))
        
        if bt.MAGDATGRIP:
            a(( 80, (cc("grip_data"),"Data val.",   _DAT, True)))
        
        a(( 50, (cc("pdc_codice"),   "Cod.",        _STR, True)))
        a((250, (cc("pdc_descriz"),  "Fornitore",   _STR, True)))
        a((120, (cc("prod_codfor"),  "Cod.Fornit.", _STR, True)))
        a((120, (cc("prod_barcode"), "Barcode",     _STR, True)))
        a((  1, (cc("prod_id"),      "#pro",        _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(lis.GetRecordset(), colmap, canedit, canins)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiProdottoGrid(GrigliaPrezziAttualiGrid):
    
    def __init__(self, parent, dblis):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, 
                                              size=parent.GetSize())
        
        self.dblis = lis = dblis
        
        def cc(col):
            return lis._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        ws = 50
        wp = 90
        
        cols = []
        def a(x):
            cols.append(x)
        a(( 80, (cc("grip_pdc_codice"),  "Cod.",        _STR, True)))
        a((300, (cc("grip_pdc_descriz"), "Anagrafica",  _STR, True)))
        a(( wp, (cc("grip_prezzo"),      "Prezzo",      _PRZ, True)))
        if bt.MAGNUMSCO >= 1:
            a(( ws, (cc("grip_sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( ws, (cc("grip_sconto2"), "Sc.%2",       _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( ws, (cc("grip_sconto3"), "Sc.%3",       _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( ws, (cc("grip_sconto4"), "Sc.%4",       _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( ws, (cc("grip_sconto5"), "Sc.%5",       _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( ws, (cc("grip_sconto6"), "Sc.%6",       _SCO, True)))
        
        if bt.MAGDATGRIP:
            a(( 80, (cc("grip_data"),    "Data val.",   _DAT, True)))
        
        a(( 50, (cc("pdc_codice"),       "Cod.",        _STR, True)))
        a((250, (cc("pdc_descriz"),      "Fornitore",   _STR, True)))
        a((120, (cc("prod_codfor"),      "Cod.Fornit.", _STR, True)))
        a((120, (cc("prod_barcode"),     "Barcode",     _STR, True)))
        a((  1, (cc("prod_id"),          "#pro",        _STR, True)))
                                       
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(lis.GetRecordset(), colmap, canedit, canins)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)


# ------------------------------------------------------------------------------


class ChiCosaGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbriep):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, 
                                              size=parent.GetSize())
        
        riep = dbriep
        
        def cc(col):
            return riep._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        ws = 50
        wp = 90
        
        cols = []
        def a(x):
            cols.append(x)
        a((100, (cc("codice"),        "Cod.",        _STR, True)))
        a((300, (cc("descriz"),       "Anagrafica",  _STR, True)))
        a(( wp, (cc("count_numprod"), "#Prodotti",   _NUM, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(riep.GetRecordset(), colmap, canedit, canins)
        
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


class ChiCosaPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        tipana = kwargs.pop('tipana')
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ChiCosaFunc(self)
        r = adb.DbTable(bt.TABNAME_PDC, 'pdc', fields=None)
        r.AddJoin(bt.TABNAME_PDCTIP,  'tipana', fields=None, idLeft='id_tipo', idRight='id')
        r.AddJoin(bt.TABNAME_GRIGLIE, 'grip', fields=None, idLeft='id', idRight='id_pdc')
        r.Synthetize()
        r.AddGroupOn('pdc.id')
        r.AddGroupOn('pdc.codice')
        r.AddGroupOn('pdc.descriz')
        r.AddCountOf('grip.id', 'numprod')
        r.AddFilter('tipana.tipo=%s', tipana)
        r.Retrieve()
        self.dbriep = r
        def cn(x):
            return self.FindWindowByName(x)
        self.gridriep = ChiCosaGrid(cn('pangridriep'), self.dbriep)


# ------------------------------------------------------------------------------


class ChiCosaDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        tipana = kwargs.pop('tipana')
        if not 'title' in kwargs:
            kwargs['title'] = "Riepilogo anagrafiche e numero di prodotti associati"
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = ChiCosaPanel(self, tipana=tipana)
        self.AddSizedPanel(self.panel)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSelez)
        self.CenterOnScreen()
    
    def OnSelez(self, event):
        row = event.GetRow()
        r = self.panel.dbriep
        if 0 <= row < r.RowsCount():
            r.MoveRow(row)
            self.EndModal(wx.ID_OK)
    
    def GetPdc(self):
        return self.panel.dbriep.id


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiPanel(stalis.ListiniAttualiPanel):
    
    def __init__(self, *args, **kwargs):
        self.tipana = kwargs.pop('tipana')
        if self.tipana == "C":
            self._desana = "Cliente"
            anag = bt.TABNAME_CLIENTI
        else:
            self._desana = "Fornitore"
            anag = bt.TABNAME_FORNIT
        self.dbana = adb.DbTable(anag, 'anag', fields='id,id_pdcgrp')
        stalis.ListiniAttualiPanel.__init__(self, *args, **kwargs)
        def cn(x):
            return self.FindWindowByName(x)
        self.Bind(wx.EVT_BUTTON, self.OnCercaChiCosa, cn('butchicosa'))
    
    def OnCercaChiCosa(self, event):
        d = ChiCosaDialog(self, tipana=self.tipana)
        do = (d.ShowModal() == wx.ID_OK)
        d.Destroy()
        if do:
            self.FindWindowByName('id_pdc').SetValue(d.GetPdc())
            self.UpdateData()
        event.Skip()
    
    def InitTable(self):
        self.dblis = dba.TabProdGrigliaPrezziAttualiPdcTable()
    
    def InitControls(self):
        wdr.SelDataPanel = wdr.GrigliaPrezziiAttualiSelDataPanel
        wdr.ListiniAttualiFunc(self)
        def cn(x):
            return self.FindWindowByName(x)
        self.gridlis = GrigliaPrezziAttualiGrid(cn('pangridlist'), self.dblis, self.tipana)
    
    def Validate(self):
        def cn(x):
            return self.FindWindowByName(x)
        for name, msg in (('dataval', "Impostare la data di validità"),
                          ('id_pdc', "Definire il sottoconto della griglia")):
            if not cn('dataval').GetValue():
                awu.MsgDialog(self, msg, style=wx.ICON_ERROR)
                return False
        return True
    
    def UpdateData(self):
        def cn(x):
            return self.FindWindowByName(x)
        d, p = map(lambda x: cn(x).GetValue(), 'dataval id_pdc'.split())
        dbana = self.dbana
        if dbana.Get(p) and dbana.OneRow():
            if dbana.id_pdcgrp is not None:
                p = dbana.id_pdcgrp
        lis = self.dblis
        lis.SetParam(d, p)
        class Filter:
            cmd = ""
            par = []
            def AddFilter(self, f, p):
                if self.cmd:
                    self.cmd += " AND "
                self.cmd += f
                self.par.append(p)
        li = Filter()
        for col in 'codice codfor barcode'.split():
            c1, c2 = map(lambda x: cn(x).GetValue(), (col+'1', col+'2'))
            if c1:
                li.AddFilter("prod.%s>=%%s" % col, c1)
            if c2:
                li.AddFilter("prod.%s<=%%s" % col, '%sZ'%c2)
        for tab in 'tipart catart gruart marart status'.split():
            c1, c2 = map(lambda x: cn(x).GetValueCod(), (tab+'1', tab+'2'))
            if c1:
                li.AddFilter("%s.codice>=%%s" % tab, c1)
            if c2:
                li.AddFilter("%s.codice<=%%s" % tab, c2)
        c1, c2 = map(lambda x: cn(x).GetValueDes(), 'fornit1 fornit2'.split())
        if c1:
            li.AddFilter("pdc.descriz>=%s", c1)
        if c2:
            li.AddFilter("pdc.descriz<=%s", c2)
        lis.Retrieve(li.cmd, li.par)
        self.gridlis.ChangeData(lis.GetRecordset())
        return True
    
    def PrintListino(self):
        self.dblis._datlis = self.FindWindowByName('dataval').GetValue()
        self.dblis._desana = self._desana
        rpt_name = "Griglia prezzi in vigore dell'anagrafica"
        if self.tipana == 'C':
            cde = bt.MAGCDEGRIP
        else:
            cde = bt.MAGCDEGRIF
        if cde:
            rpt_name += ' con codice e descrizione esterni'
        rpt.Report(self, self.dblis, rpt_name)


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiClientiFrame(aw.Frame):
    tipana = "C"
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_CLIENTI_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GrigliaPrezziAttualiPanel(self, tipana=self.tipana))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiFornitFrame(GrigliaPrezziAttualiClientiFrame):
    tipana = "F"
