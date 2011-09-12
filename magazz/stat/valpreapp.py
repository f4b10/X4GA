#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/valpreapp.py
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

import copy

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw
MsgBox = aw.awu.MsgDialog

import magazz.listini_wdr as wdr

from awc.controls.linktable import EVT_LINKTABCHANGED

import stormdb as adb
import magazz.stat.dbtables as dbms

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import awc.controls.linktable as lt
import awc.controls.datectrl as dc

from anag.prod import ProdDialog

import csv

from magazz.chiusure.editgiac import ProdottoHelperEditor

import awc.controls.dbgrideditors as dbgred

import report as rpt


PREZZI_FRAME_TITLE = "Valutazione prezzi di vendita applicati"


class MovimentiPrezziGrid(dbglib.DbGridColoriAlternati):
    """
    DbGrid Movimenti che determinano le valutazioni del prezzo.
    """
    
    def __init__(self, parent, dbmov):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetSize(), style=0)
        self.dbmov = dbmov
        
        cols = self.DefColumns()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = canins = False
        
        self.SetData((), colmap, canedit, canins)
        
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
    
    def DefColumns(self):
        
        mov = self.dbmov
        tpm = mov.tipmov
        doc = mov.doc
        tpd = doc.tipdoc
        pdc = doc.pdc
        age = doc.agente
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRZ = bt.GetMagPreMaskInfo()
        _QTA = bt.GetMagQtaMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        wp = wdr.PREZZOWIDTH
        wi = wp+20
        
        cols = []
        self.edcols = []
        def c(col, ed=False):
            n = len(cols)
            cols.append(col)
            if ed:
                self.edcols.append(n)
            return n
        def C(col):
            return c(col, ed=True)
        
        self.COL_DATDOC = c(( 80, (cn(doc, "datdoc"),  "Data doc.",  _DAT, True )))
        self.COL_TPDCOD = c(( 35, (cn(tpd, "codice"),  "Cod.",       _STR, True )))
        self.COL_TPDDES = c((120, (cn(tpd, "descriz"), "Documento",  _STR, True )))
        self.COL_TPMCOD = c(( 35, (cn(tpm, "codice"),  "Mov.",       _STR, True )))
        self.COL_NUMDOC = c(( 50, (cn(doc, "numdoc"),  "Num.",       _STR, True )))
        self.COL_PDCCOD = c(( 50, (cn(pdc, "codice"),  "Cod.",       _STR, True )))
        self.COL_PDCDES = c((230, (cn(pdc, "descriz"), "Cliente",    _STR, True )))
        self.COL_PREZUN = c(( wp, (cn(mov, "prezzo"),  "Prezzo Un.", _PRZ, True )))
        self.COL_PREZSC = c(( wp, (cn(mov, "presco"),  "Prezzo Sc.", _PRZ, True )))
        self.COL_TOTQTA = c(( wp, (cn(mov, "qta"),     "Qta",        _QTA, True )))
        if bt.MAGNUMSCO >= 1:
            self.COL_SCONT1 = c(( 50, (cn(mov, "sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True )))
        if bt.MAGNUMSCO >= 2:
            self.COL_SCONT2 = c(( 50, (cn(mov, "sconto2"), "Sc.%2",  _SCO, True )))
        if bt.MAGNUMSCO >= 3:
            self.COL_SCONT3 = c(( 50, (cn(mov, "sconto3"), "Sc.%3",  _SCO, True )))
        if bt.MAGNUMSCO >= 4:
            self.COL_SCONT4 = c(( 50, (cn(mov, "sconto4"), "Sc.%4",  _SCO, True )))
        if bt.MAGNUMSCO >= 5:
            self.COL_SCONT5 = c(( 50, (cn(mov, "sconto5"), "Sc.%5",  _SCO, True )))
        if bt.MAGNUMSCO >= 6:
            self.COL_SCONT6 = c(( 50, (cn(mov, "sconto6"), "Sc.%6",  _SCO, True )))
        self.COL_IMPORT = c(( wi, (cn(mov, "importo"), "Importo",    _IMP, True )))
        self.COL_PDCCOD = c(( 50, (cn(age, "codice"),  "Cod.",       _STR, True )))
        self.COL_PDCDES = c((140, (cn(age, "descriz"), "Agente",     _STR, True )))
        c((  1, (cn(tpd, "id"),   "#tpd", _STR, True )))
        c((  1, (cn(tpm, "id"),   "#tpm", _STR, True )))
        c((  1, (cn(pdc, "id"),   "#pdc", _STR, True )))
        
        return cols


# ------------------------------------------------------------------------------


class MovimentiPrezziPanel(aw.Panel):
    """
    Panel Movimenti che determinano le valutazioni del prezzo.
    """
    
    statftcol = 'statftcli'
    GridClass = MovimentiPrezziGrid
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.MovimentiPrezziFunc(self)
        cn = self.FindWindowByName
        self.dbmov = dbms.MovimentiPrezzi(bt.TABNAME_MOVMAG_B, 'mov')
        self.gridmov = self.GridClass(cn('pangridmov'), self.dbmov)
    
    def SetParam(self, id_prod, filters):
        wx.BeginBusyCursor()
        try:
            mov = self.dbmov
            mov._info.filters = filters
            mov.AddFilter('mov.id_prod=%s', id_prod)
            mov.AddFilter('tipmov.%s=1' % self.statftcol)
            mov.Retrieve()
            self.gridmov.ChangeData(mov.GetRecordset())
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


PREZZI_FRAME_TITLE_DETT = 'Prezzi applicati'

class MovimentiPrezziFrame(aw.Frame):
    """
    Frame Movimenti che determinano le valutazioni del prezzo.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = PREZZI_FRAME_TITLE_DETT
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = MovimentiPrezziPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
    
    def SetParam(self, *args, **kwargs):
        return self.panel.SetParam(*args, **kwargs)


# ------------------------------------------------------------------------------


class MovimentiPrezziDialog(aw.Dialog):
    """
    Dialog Movimenti che determinano le valutazioni del prezzo.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = PREZZI_FRAME_TITLE_DETT
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = MovimentiPrezziPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
    
    def SetParam(self, *args, **kwargs):
        return self.panel.SetParam(*args, **kwargs)


# ------------------------------------------------------------------------------


class ValutaPrezziGrid(dbglib.DbGridColoriAlternati):
    """
    DbGrid Valutazione prezzi di vendita applicati.
    """
    
    def __init__(self, parent, dbvpv):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetSize(), style=0)
        self.dbvpv = dbvpv
        
        cols = self.DefColumns()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = canins = False
        
        self.SetData((), colmap, canedit, canins)
        
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
    
    def DefColumns(self):
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        vpv = self.dbvpv
        pro = vpv.prod
        
        _STR = gl.GRID_VALUE_STRING
        _PRZ = bt.GetMagPreMaskInfo()
        wp = wdr.PREZZOWIDTH
        
        cols = []
        self.edcols = []
        def c(col, ed=False):
            n = len(cols)
            cols.append(col)
            if ed:
                self.edcols.append(n)
            return n
        def C(col):
            return c(col, ed=True)
        
        self.COL_CODICE =  C(( 80, (cn(vpv, "prod_codice"),        "Codice",        _STR, True )))
        self.COL_DESCRIZ = C((170, (cn(vpv, "prod_descriz"),       "Prodotto",      _STR, True )))
        
        if bt.MAGFORLIS:
            self.COL_CODFOR = c(( 90, (cn(vpv, "prod_codfor"),     "Cod.Fornit.",   _STR, True )))
        
        self.COL_PREPUB =  C(( wp, (cn(vpv, "prod_prezzo"),        "Prezzo pubbl.", _PRZ, False)))
        
        #minimo, massimo, media su prezzo unitario
        self.COL_PREAPPUN_MIN =  C(( wp, (cn(vpv, "min_prezzoun"), "Min.Un.",       _PRZ, False)))
        self.COL_PREAPPUN_MAX =  C(( wp, (cn(vpv, "max_prezzoun"), "Max.Un.",       _PRZ, False)))
        self.COL_PREAPPUN_AVG =  C(( wp, (cn(vpv, "avg_prezzoun"), "Media.Un.",     _PRZ, False)))
        
        #minimo, massimo, media su prezzo scontato
        self.COL_PREAPPSC_MIN =  C(( wp, (cn(vpv, "min_prezzosc"), "Min.Sc.",       _PRZ, False)))
        self.COL_PREAPPSC_MAX =  C(( wp, (cn(vpv, "max_prezzosc"), "Max.Sc.",       _PRZ, False)))
        self.COL_PREAPPSC_AVG =  C(( wp, (cn(vpv, "avg_prezzosc"), "Media.Sc.",     _PRZ, False)))
        
        c((  1, (cn(vpv, "prod_id"),   "#pro", _STR, True )))
        
        return cols


# ------------------------------------------------------------------------------


class ValutaPrezziPanel(aw.Panel, aw.awu.LimitiFiltersMixin):
    """
    Panel Valutazione prezzi di vendita applicati.
    """
    
    ValutaCostiPrezziTable = dbms.ValutaPrezziVendita
    WdrFiller = wdr.ValutaPrezziApplicatiFunc
    GridClass = ValutaPrezziGrid
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        self.WdrFiller(self)
        
        aw.awu.LimitiFiltersMixin.__init__(self)
        cn = self.FindWindowByName
        
        self.dbvpv = self.ValutaCostiPrezziTable()
        self.gridvpv = self.GridClass(cn('pangridvpv'), self.dbvpv)
        
        self.DefALS()
        
        for name, func in (('update', self.OnUpdateData),
                           ('print',  self.OnPrintData),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnVediPrezzi, self.gridvpv)
    
    def DefALS(self):
        ALS = self.AddLimitiFiltersSequence
        vpv = self.dbvpv
        pro = vpv.prod
        doc = vpv.doc
        ALS(pro, 'prod',    'codice')
        ALS(pro, 'prod',    'descriz')
        ALS(pro, 'status',  'id_status')
        ALS(pro, 'catart',  'id_catart')
        ALS(pro, 'gruart',  'id_gruart')
        ALS(pro, 'tipart',  'id_tipart')
        ALS(pro, 'fornit',  'id_fornit')
        ALS(doc, 'doc',     'datreg')
        ALS(doc, 'pdc',     'id_anag')
        ALS(doc, 'agente',  'id_agente')
    
    def OnVediPrezzi(self, event):
        row = event.GetRow()
        vpv = self.dbvpv
        vpv.MoveRow(row)
        self.VediPrezzi(vpv.prod_id)
        event.Skip()
    
    def VediPrezzi(self, id_prod):
        vpv = self.dbvpv
        filters = []
        for tab in (vpv.doc, vpv.doc.pdc, vpv.doc.agente):
            if tab._info.filters:
                filters += ([]+tab._info.filters)
        dlg = MovimentiPrezziDialog(self)
        dlg.SetParam(id_prod, filters)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnPrintData(self, event):
        self.PrintData()
        event.Skip()
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def PrintData(self):
        rpt.Report(self, self.dbvpv, 'Valutazione Prezzi Vendita')
    
    def UpdateData(self):
        cn = self.FindWindowByName
        ordinam = cn('ordinam').GetValue()
        vpv = self.dbvpv
        vpv.ClearOrders()
        if ordinam == "C":
            vpv.AddOrder('prod.codice')
        elif ordinam == "D":
            vpv.AddOrder('prod.descriz')
        elif ordinam == "F":
            vpv.AddOrder('prod.codfor')
            vpv.AddOrder('prod.codice')
        vpv.ClearFilters()
        for _ in vpv._info.iChildrens:
            _.ClearFilters()
        self.LimitiFiltersApply()
        ssv = cn('ssv').GetValue()
        if ssv:
            vpv.AddFilter('status.hidesearch IS NULL OR status.hidesearch<>1')
        wx.BeginBusyCursor()
        try:
            vpv.Retrieve()
            self.gridvpv.ChangeData(vpv.GetRecordset())
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


class ValutaPrezziFrame(aw.Frame):
    """
    Frame Valutazione prezzi di vendita applicati.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = PREZZI_FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ValutaPrezziPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ValutaPrezziDialog(aw.Dialog):
    """
    Dialog Valutazione prezzi di vendita applicati.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = PREZZI_FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ValutaPrezziPanel(self, -1))
        self.CenterOnScreen()
