#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/prodmas.py
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

import anag.prod_wdr as wdr

import magazz.maglib as maglib
dbm = maglib.dbm
bt = dbm.Env.Azienda.BaseTab
stdcolor = dbm.Env.Azienda.Colours

import report as rpt


class GridMov(maglib.GridMov):
    
    def __init__(self, parent, dlg):
        
        maglib.GridMov.__init__(self, dlg)
        self.dbmas = dbm.ProdMastro()
        self.dbmov = self.dbmas.mov
        #self.dbmov.ShowDialog(parent)
        
        size = parent.GetClientSizeTuple()
        
        
        cols= self.SetColumnGrid()        
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rsmas = self.dbmov.GetRecordset()
        
        grid = dbglib.DbGrid(parent, -1, size=size, tableClass=maglib.GridTable, idGrid='movprod')
        grid.SetData( rsmas, colmap, canedit, canins)
        grid.GetTable().dbmov = self.dbmov
        
        grid=self.SetTotalGrid(grid)
        
        grid.SetCellDynAttr(self.GetAttr)
        
        ci = lambda x: parent.GetGrandParent().FindWindowById(x)
        
        ci(wdr.ID_MASBUTUPD).Bind(wx.EVT_BUTTON, self.GridMovOnUpdateFilters)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.gridmov = grid


    def SetColumnGrid(self):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        mov = self.dbmov
        doc = mov.doc
        mag = doc.mag
        tpd = doc.tipdoc
        tpm = mov.tipmov
        pdc = doc.pdc
        iva = mov.iva
        age = doc.agente
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        ncqtaeva = cn(mov, 'total_evas_qta')
        ncqtares = cn(mov, 'total_resid_qta')

        cols = []
        a = cols.append
        a(( 35, (cn(mag, "codice"),  "Mag.",         _STR, True)))
        a(( 80, (cn(doc, "datreg"),  "Data reg.",    _DAT, True)))
        a(( 35, (cn(tpd, "codice"),  "Cod.",         _STR, True)))
        a((180, (cn(tpd, "descriz"), "Documento",    _STR, True)))
        a(( 35, (cn(tpm, "codice"),  "Mov.",         _STR, True)))
        a((110, (cn(mov, "qta"),     "Qtà",          _QTA, True)))
        a((100, (cn(mov, "prezzo"),  "Prezzo",       _PRE, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 45, (cn(mov, "sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 45, (cn(mov, "sconto2"), "Sc.%2",    _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 45, (cn(mov, "sconto3"), "Sc.%3",    _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 45, (cn(mov, "sconto4"), "Sc.%4",    _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 45, (cn(mov, "sconto5"), "Sc.%5",    _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 45, (cn(mov, "sconto6"), "Sc.%6",    _SCO, True)))
        #=======================================================================
        # a((110, (cn(mov, "importo"), "Importo",      _IMP, True)))
        #=======================================================================
        #TODO:SCORPORO X BARBARA
        a((110, (cn(mov, "imponibile"), "Imponibile",   _IMP, True)))
        a(( 35, (cn(iva, "codice"),  "Cod.",         _STR, True)))
        a(( 90, (cn(iva, "descriz"), "Aliquota IVA", _STR, True)))
        a(( 50, (cn(doc, "numdoc"),  "Num.",         _STR, True)))
        a(( 80, (cn(doc, "datdoc"),  "Data doc.",    _DAT, True)))
        a(( 50, (cn(doc, "numrif"),  "Num.",         _STR, True)))
        a(( 80, (cn(doc, "datrif"),  "Data rif.",    _DAT, True)))
        a(( 90, (cn(doc, "desrif"),  "Riferimento",  _STR, True)))
        a(( 50, (cn(pdc, "codice"),  "Cod.",         _STR, True)))
        a((260, (cn(pdc, "descriz"), "Sottoconto",   _STR, True)))
        a((110, (cn(tpm, "descriz"), "Movimento",    _STR, True)))
        a((120, (cn(mov, "note"),    "Note",         _STR, True)))
        a(( 35, (cn(age, "codice"),  "Cod.",         _STR, True)))
        a(( 90, (cn(age, "descriz"), "Agente",       _STR, True)))
        a(( 30, (cn(mov, "f_ann"),   "Man",          _CHK, True)))
        a(( 30, (cn(doc, "f_ann"),   "Ann",          _CHK, True)))
        a(( 30, (cn(doc, "f_acq"),   "Acq",          _CHK, True)))
        #=======================================================================
        # Introdotte a fini di debug
        #=======================================================================
        # a(( 30, (cn(tpm, "id"),      "Ini",          _STR, True)))
        # a(( 30, (cn(tpm, "tv_isini"),"Ini",          _CHK, True)))
        # a(( 30, (cn(tpm, "aggini"),  "g.i.",          _CHK, True)))
        #=======================================================================
        a((  1, (cn(mov, "id"),      "#mov",         _STR, True)))
        a((  1, (cn(doc, "id"),      "#doc",         _STR, True)))
        return cols
        

    def SetTotalGrid(self, grid):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        tpm = self.dbmov.tipmov
        self._ncaggcar = cn(tpm, 'aggcar')
        self._ncaggsca = cn(tpm, 'aggsca')
        self._ncaggorc = cn(tpm, 'aggordcli')
        self._ncaggorf = cn(tpm, 'aggordfor')
        self._ncaggini = cn(tpm, 'aggini')        
        
        self._bgcolrow = stdcolor.NORMAL_BACKGROUND
        self._bgcoltot = stdcolor.GetColour('aliceblue')
                
        for label, func in (\
            ('Giac.Iniziale:',       lambda rsm, row: rsm[row][self._ncaggini]),                                    
            ('Tot. Carichi:',        lambda rsm, row: rsm[row][self._ncaggcar]),
            ('Tot. Scarichi:',       lambda rsm, row: rsm[row][self._ncaggsca]),
            ('Tot. Ord. Clienti:',   lambda rsm, row: rsm[row][self._ncaggorc]),
            ('Tot. Ord. Fornitori:', lambda rsm, row: rsm[row][self._ncaggorf])):
            #===================================================================
            # grid.AddTotalsRow(3, label, (cn(self.dbmov, "qta"),                 # mantenuto per storia non serve
            #                              cn(self.dbmov, "finale"),
            #                              cn(self.dbmov, "importo"),
            #                              cn(self.dbmov, "imponibile"),), func)
            #===================================================================
            grid.AddTotalsRow(3, label, (cn(self.dbmov, "qta"),
                                         cn(self.dbmov, "importo"),
                                         cn(self.dbmov, "imponibile"),), func)
            
        pass
        return grid


    def GetAttr(self, row, col, rscol, attr):
        if self.gridmov.IsOnTotalRow(row):
            bgcol = self._bgcoltot
        else:
            bgcol = self._bgcolrow
        attr.SetBackgroundColour(bgcol)
        attr.SetReadOnly()
        return attr
    

# ------------------------------------------------------------------------------


class ProdMastroPanel(wx.Panel):
    
    def __init__(self, parent, dlg):
        wx.Panel.__init__(self, parent)
        wdr.ProdMastroFunc(self)
        def ci(x):
            return self.FindWindowById(x)
        pp = ci(wdr.ID_MASPANMASTRO)
        self.gridmov = GridMov(pp, dlg)
        ci(wdr.ID_MASID_TIPMOV).Enable(False)
        if dbm.Env.Azienda.GetAutom('magordinv'):
            self.FindWindowByName('ordinv').SetValue(1)
        from awc.controls.linktable import EVT_LINKTABCHANGED
        self.Bind(EVT_LINKTABCHANGED, self.OnTipDocChanged, 
                  ci(wdr.ID_MASID_TIPDOC))
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc, self.gridmov.gridmov)
        self.Bind(wx.EVT_BUTTON, self.OnPrintData, ci(wdr.ID_MASBUTPRT))
    
    def OnCallDoc(self, event):
        row = event.GetRow()
        dbmov = self.gridmov.dbmas.mov
        if 0 <= row < dbmov.RowsCount():
            dbmov.MoveRow(row)
            import awc.util as awu
            wait = awu.WaitDialog(self, message="Caricamento documento in corso")
            try:
                import magazz
                Dialog = magazz.GetDataentryDialogClass()
                dlg = Dialog(self)
                dlg.SetOneDocOnly(dbmov.doc.id)
                dlg.CenterOnScreen()
                dbdoc = dlg.panel.dbdoc
                c = dbdoc.mov._GetFieldIndex('id_prod')
                p = dbmov.id_prod
                def TrovaRiga(r):
                    return r[c] == p
                n = dbdoc.mov.LocateRS(TrovaRiga)
                if n:
                    dlg.panel.gridbody.MakeCellVisible(n, 1)
                    dlg.panel.gridbody.SetGridCursor(n, 1)
                    dlg.panel.FindWindowByName('workzone').SetSelection(1)
            finally:
                wait.Destroy()
            r = dlg.ShowModal()
            if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                self.GridUpdate(prod=p)
                if r == magazz.DOC_MODIFIED:
                    wx.CallAfter(lambda: self.gridmov.gridmov.SelectRow(row))
            dlg.Destroy()
        event.Skip()
    
    def OnTipDocChanged(self, event):
        def ci(x):
            return self.FindWindowById(x)
        tdoc = ci(wdr.ID_MASID_TIPDOC).GetValue()
        if tdoc is None:
            flt = None
        else:
            flt = "id_tipdoc=%d" % tdoc
        tm = ci(wdr.ID_MASID_TIPMOV)
        tm.SetFilter(flt)
        tm.Enable(flt is not None)
        event.Skip()
    
    def GridUpdate(self, prod=None):
        wx.BeginBusyCursor()
        if prod is not None:
            self.gridmov.dbmas.Get(prod)
        self.gridmov.GridMovUpdate()
        wx.EndBusyCursor()
    
    def OnPrintData(self, event):
        self.PrintData()
        event.Skip()
    
    def PrintData(self):
        db = self.gridmov.dbmas.mov
        db._info.dbprod = self.gridmov.dbmas
        rpt.Report(self, db, "Lista movimenti prodotto")


# ------------------------------------------------------------------------------


class GridMovEva(maglib.GridMovEva):
    
    def __init__(self, parent, dlg):
        
        maglib.GridMovEva.__init__(self, dlg)
        self.dbmas = dbm.ProdMastroEva()
        self.dbmov = self.dbmas.mov
        #self.dbmov.ShowDialog(parent)
        
        size = parent.GetClientSizeTuple()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        mov = self.dbmov
        doc = mov.doc
        mag = doc.mag
        tpd = doc.tipdoc
        tpm = mov.tipmov
        pdc = doc.pdc
        iva = mov.iva
        age = doc.agente
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        ncqtaeva = cn(mov, 'total_evas_qta')
        ncqtares = cn(mov, 'total_resid_qta')
        
        cols = []
        a = cols.append
        a(( 35, (cn(mag, "codice"),  "Mag.",         _STR, True)))
        a(( 80, (cn(doc, "datreg"),  "Data reg.",    _DAT, True)))
        a(( 35, (cn(tpd, "codice"),  "Doc.",         _STR, True)))
        a((110, (cn(tpd, "descriz"), "Documento",    _STR, True)))
        a(( 35, (cn(tpm, "codice"),  "Mov.",         _STR, True)))
        a(( 50, (cn(doc, "numdoc"),  "Num.",         _STR, True)))
        a(( 80, (cn(doc, "datdoc"),  "Data doc.",    _DAT, True)))
        a(( 80, (cn(mov, "qta"),     "Qtà",          _QTA, True)))
        a(( 80, (-1,                 "Evaso",        _QTA, True)))
        a(( 80, (-2,                 "Residuo",      _QTA, True)))
        #=======================================================================
        # a(( 80, (cn(mov, "prezzo"),  "Prezzo",       _PRE, True)))
        # a(( 85, (cn(mov, "importo"), "Importo",      _IMP, True)))
        #=======================================================================
        #TODO:SCORPORO X BARBARA
        a(( 80, (cn(mov, "prezzoimp"),  "Prezzo",       _PRE, True)))
        a(( 85, (cn(mov, "imponibile"), "Imponibile",      _IMP, True)))
        a(( 50, (cn(pdc, "codice"),  "Cod.",         _STR, True)))
        a((260, (cn(pdc, "descriz"), "Sottoconto",   _STR, True)))
        a((110, (cn(tpm, "descriz"), "Movimento",    _STR, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 45, (cn(mov, "sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 45, (cn(mov, "sconto2"), "Sc.%2",    _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 45, (cn(mov, "sconto3"), "Sc.%3",    _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 45, (cn(mov, "sconto4"), "Sc.%4",    _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 45, (cn(mov, "sconto5"), "Sc.%5",    _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 45, (cn(mov, "sconto6"), "Sc.%6",    _SCO, True)))
        a((120, (cn(mov, "note"),    "Note",         _STR, True)))
        a(( 35, (cn(age, "codice"),  "Cod.",         _STR, True)))
        a(( 90, (cn(age, "descriz"), "Agente",       _STR, True)))
        a(( 35, (cn(iva, "codice"),  "Cod.",         _STR, True)))
        a(( 90, (cn(iva, "descriz"), "Aliquota IVA", _STR, True)))
        a(( 30, (cn(mov, "f_ann"),   "Man",          _CHK, True)))
        a(( 30, (cn(doc, "f_ann"),   "Ann",          _CHK, True)))
        a(( 30, (cn(doc, "f_acq"),   "Acq",          _CHK, True)))
        a((  1, (cn(mov, "id"),      "#mov",         _STR, True)))
        a((  1, (cn(doc, "id"),      "#doc",         _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rsmas = self.dbmov.GetRecordset()
        
        grid = dbglib.DbGrid(parent, -1, size=size, tableClass=maglib.GridTable, idGrid='evasioni')
        grid.SetData( rsmas, colmap, canedit, canins)
        grid.GetTable().dbmov = self.dbmov
        
        self._ncaggcar = cn(tpm, 'aggcar')
        self._ncaggsca = cn(tpm, 'aggsca')
        self._ncaggorc = cn(tpm, 'aggordcli')
        self._ncaggorf = cn(tpm, 'aggordfor')
        self._bgcolrow = stdcolor.NORMAL_BACKGROUND
        self._bgcoltot = stdcolor.GetColour('aliceblue')
        
        #for label, func in (\
            #('Tot. Carichi:',        lambda rsm, row: rsm[row][self._ncaggcar]),
            #('Tot. Scarichi:',       lambda rsm, row: rsm[row][self._ncaggsca]),
            #('Tot. Ord. Clienti:',   lambda rsm, row: rsm[row][self._ncaggorc]),
            #('Tot. Ord. Fornitori:', lambda rsm, row: rsm[row][self._ncaggorf])):
            #grid.AddTotalsRow(1, label, (cn(mov, "qta"),
                                         #cn(mov, "importo"),
                                         #-1,
                                         #-2), func)
        grid.SetCellDynAttr(self.GetAttr)
        
        ci = lambda x: parent.GetGrandParent().FindWindowById(x)
        
        ci(wdr.ID_EVABUTUPD).Bind(wx.EVT_BUTTON, self.GridMovOnUpdateFilters)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.gridmov = grid

    def GetAttr(self, row, col, rscol, attr):
        if self.gridmov.IsOnTotalRow(row):
            bgcol = self._bgcoltot
        else:
            bgcol = self._bgcolrow
        attr.SetBackgroundColour(bgcol)
        attr.SetReadOnly()
        return attr
    

# ------------------------------------------------------------------------------


class ProdMastroEvaPanel(wx.Panel):
    
    def __init__(self, parent, dlg):
        wx.Panel.__init__(self, parent)
        wdr.ProdMastroEvaFunc(self)
        pp = self.FindWindowById(wdr.ID_MASPANMASTROEVA)
        self.gridmov = GridMovEva(pp, dlg)
        self.Bind(wx.EVT_BUTTON, self.OnPrintData, self.FindWindowById(wdr.ID_EVABUTPRT))
    
    def GridUpdate(self, prod=None):
        wx.BeginBusyCursor()
        if prod is not None:
            self.gridmov.dbmas.Get(prod)
        self.gridmov.GridMovUpdate()
        wx.EndBusyCursor()
    
    def OnPrintData(self, event):
        self.PrintData()
        event.Skip()
    
    def PrintData(self):
        db = self.gridmov.dbmas.mov
        db._info.dbprod = self.gridmov.dbmas
        rpt.Report(self, db, 'Stato evasione prodotto')
