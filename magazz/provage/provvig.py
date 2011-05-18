#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/provage/provvig.py
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

import magazz.provage.dbtables as dbp

import magazz.provage.provvig_wdr as wdr

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLE = "Provvigioni Agenti"


class ProvvigAgentiDetGrid(dbglib.DbGridColoriAlternati):
    rpt_name = 'Provvigioni Agenti - Dettaglio Movimenti'
    
    def __init__(self, parent, dbprov):
        
        self.dbprov = dbprov
        
        coldef = self.GetColDef()
        sizes =  [c[0] for c in coldef]
        colmap = [c[1] for c in coldef]
        
        dbglib.DbGridColoriAlternati.__init__(self, 
                                              parent, 
                                              size=parent.GetClientSizeTuple())
        
        self.SetData(dbprov.GetRecordset(), colmap)
        
        self.SetTotali()
        
        for c,s in enumerate(sizes):
            self.SetColumnDefaultSize(c,s)
        self._SetFitColumn()
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetColDef(self):
        
        def cn(col):
            return self.dbprov._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _VAL = bt.GetValIntMaskInfo()
        
        return (\
            ( 40, (cn('age_codice'),     "Cod.",         _STR, False)),
            (120, (cn('age_descriz'),    "Agente",       _STR, False)),
            ( 40, (cn('tipdoc_codice'),  "Cod.",         _STR, False)),
            (110, (cn('tipdoc_descriz'), "Documento",    _STR, False)),
            ( 50, (cn('doc_numdoc'),     "Num.",         _STR, False)),
            ( 80, (cn('doc_datdoc'),     "Data",         _DAT, False)),
            ( 40, (cn('pdc_codice'),     "Cod.",         _STR, False)),
            (200, (cn('pdc_descriz'),    "Cliente",      _STR, False)),
            (100, (cn('prod_codice'),    "Cod.",         _STR, False)),
            (200, (cn('mov_descriz'),    "Descrizione",  _STR, False)),
            ( 90, (cn('mov_qta'),        "Qta",          _QTA, False)),
            ( 90, (cn('mov_prezzo'),     "Prezzo",       _PRE, False)),
            ( 50, (cn('mov_sconto1'),    "Sc.%1",        _SCO, False)),
            ( 50, (cn('mov_sconto2'),    "Sc.%2",        _SCO, False)),
            ( 50, (cn('mov_sconto3'),    "Sc.%3",        _SCO, False)),
            (110, (cn('total_vendita'),  "Vendita",      _VAL, False)),
            ( 40, (cn('aliqiva_codice'), "Aliq.",        _STR, False)),
            ( 50, (cn('avg_perpro'),     "Prov.%.",      _SCO, False)),
            (110, (cn('total_provvig'),  "Provvig.",     _VAL, False)),
            ( 40, (cn('dest_codice'),    "Cod.",         _STR, False)),
            (200, (cn('dest_descriz'),   "Destinatario", _STR, False)),
            (  1, (cn('mov_id'),         "#mov",         _STR, False)),
            (  1, (cn('mov_id_doc'),     "#doc",         _STR, False)),
            (  1, (cn('pdc_id'),         "#pdc",         _STR, False)),
            (  1, (cn('prod_id'),        "#pro",         _STR, False)),
        )
    
    def _SetFitColumn(self):
        self.SetFitColumn(7)
    
    def SetTotali(self):
        def cn(col):
            return self.dbprov._GetFieldIndex(col)
        self.AddTotalsRow(1, 'Totali', (cn('total_vendita'),
                                        cn('total_provvig'),))
    
    def AskForPageEject(self):
        return aw.awu.MsgDialog(self, "Vuoi un solo agente per ogni pagina?",
                                style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)


# ------------------------------------------------------------------------------


class ProvvigAgentiTotGrid(ProvvigAgentiDetGrid):
    rpt_name = 'Provvigioni Agenti - Totali Documento'
    
    def GetColDef(self):
        
        def cn(col):
            return self.dbprov._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _VAL = bt.GetValIntMaskInfo()
        _SCO = bt.GetPerGenMaskInfo()
        
        return (\
            ( 40, (cn('age_codice'),     "Cod.",         _STR, False)),
            (120, (cn('age_descriz'),    "Agente",       _STR, False)),
            ( 40, (cn('tipdoc_codice'),  "Cod.",         _STR, False)),
            (110, (cn('tipdoc_descriz'), "Documento",    _STR, False)),
            ( 50, (cn('doc_numdoc'),     "Num.",         _STR, False)),
            ( 80, (cn('doc_datdoc'),     "Data",         _DAT, False)),
            ( 40, (cn('pdc_codice'),     "Cod.",         _STR, False)),
            (200, (cn('pdc_descriz'),    "Cliente",      _STR, False)),
            ( 40, (cn('dest_codice'),    "Cod.",         _STR, False)),
            (200, (cn('dest_descriz'),   "Destinatario", _STR, False)),
            (110, (cn('total_vendita'),  "Vendita",      _VAL, False)),
            ( 50, (cn('avg_perpro'),     "Prov.%.",      _SCO, False)),
            (110, (cn('total_provvig'),  "Provvig.",     _VAL, False)),
            (  1, (cn('doc_id'),         "#doc",         _STR, False)),
            (  1, (cn('pdc_id'),         "#pdc",         _STR, False)),
        )
    
    def AskForPageEject(self):
        return aw.awu.MsgDialog(self, "Vuoi un solo agente per ogni pagina?",
                                style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)


# ------------------------------------------------------------------------------


class ProvvigAgentiPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ProvvigAgentiFunc(self)
        cn = self.FindWindowByName
        self.gridmov = None
        self.InitGrid()
        for name, func in (('butupdate', self.OnUpdateData),
                           ('butprint', self.OnPrintData),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def InitGrid(self):
        if self.gridmov is not None:
#            self.gridmov.Destroy()
            wx.CallAfter(self.gridmov.Destroy)
        cn = self.FindWindowByName
        if cn('dettrighe').IsChecked():
            self.dbprov = dbp.ProvvigAgentiDetTable()
            self.gridmov = ProvvigAgentiDetGrid(cn('pangridmov'), self.dbprov)
        else:
            self.dbprov = dbp.ProvvigAgentiTotTable()
            self.gridmov = ProvvigAgentiTotGrid(cn('pangridmov'), self.dbprov)
        
    def OnUpdateData(self, event):
        self.InitGrid()
        self.UpdateData()
        event.Skip()
    
    def OnPrintData(self, event):
        self.PrintData()
    
    def UpdateData(self):
        dbprov = self.dbprov
        dbprov.ClearFilters()
        cn = self.FindWindowByName
        v = cn('agente1').GetValueCod()
        if v:
            dbprov.AddFilter('age.codice>=%s', v)
        v = cn('agente2').GetValueCod()
        if v:
            dbprov.AddFilter('age.codice<=%s', v)
        v = cn('datdoc1').GetValue()
        if v:
            dbprov.AddFilter('doc.datdoc>=%s', v)
        v = cn('datdoc2').GetValue()
        if v:
            dbprov.AddFilter('doc.datdoc<=%s', v)
        if cn('solosaldati').IsChecked():
            dbprov.AddHaving('total_saldo IS NULL OR total_saldo=0')
        wx.BeginBusyCursor()
        try:
            dbprov.Retrieve()
        finally:
            wx.EndBusyCursor()
        self.gridmov.ChangeData(dbprov.GetRecordset())
    
    def PrintData(self):
#        db = self.dbprov
#        cn = self.FindWindowByName
#        for name in 'datdoc1 datdoc2 solosaldati'.split():
#            db.SetPrintValue(name, cn(name).GetValue())
#        cpp = self.gridmov.AskForPageEject() == wx.ID_YES
#        def setCPP(rptdef, dbt):
#            groups = rptdef.lGroup
#            for g in groups:
#                if groups[g].name == 'agente':
#                    if cpp:
#                        snp = 'true'
#                    else:
#                        snp = 'false'
#                    groups[g].isStartNewPage = snp
#        rpt.Report(self, db, self.gridmov.rpt_name, startFunc=setCPP)
        db = self.dbprov
        cn = self.FindWindowByName
        for name in 'datdoc1 datdoc2 solosaldati'.split():
            db.SetPrintValue(name, cn(name).GetValue())
        def setCPP(rptdef, dbt):
            groups = rptdef.lGroup
            for g in groups:
                if groups[g].name == 'agente':
                    if cn('agepag').IsChecked():
                        snp = 'true'
                    else:
                        snp = 'false'
                    groups[g].isStartNewPage = snp
        rpt.Report(self, db, self.gridmov.rpt_name, startFunc=setCPP)


# ------------------------------------------------------------------------------


class ProvvigAgentiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = ProvvigAgentiPanel(self)
        self.AddSizedPanel(self.panel)
