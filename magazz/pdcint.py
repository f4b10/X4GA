#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/pdcint.py
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

import wx.lib.newevent

import awc.controls.windows as aw
import awc.controls.notebook as nb

import magazz.dbtables as dbm
import magazz.stat.dbtables as dbs
Env = dbm.Env
bt = Env.Azienda.BaseTab

import magazz
import magazz.docint as docint
import magazz.docint_wdr as wdr

import report as rpt


_evtDOCUMENT_CHANGED = wx.NewEventType()
EVT_DOCUMENT_CHANGED = wx.PyEventBinder(_evtDOCUMENT_CHANGED, 1)
class DocumentChangedEvent(wx.PyCommandEvent):
    def __init__(self, parent_id):
        wx.PyCommandEvent.__init__(self, _evtDOCUMENT_CHANGED, parent_id)


class PdcIntMagDocGrid(dbglib.DbGridColoriAlternati, docint._DocIntGridMixin):
    
    def __init__(self, parent, dbdoc, **kwargs):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(), idGrid='interdoc')
        docint._DocIntGridMixin.__init__(self)
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        self.dbdoc = dbdoc
        doc = self.dbdoc
        tpd = doc.tipdoc
        pdc = doc.pdc
        dst = doc.dest
        mag = doc.magazz
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 35, (cn(mag, "codice"),     "Mag.",          _STR, True )),
            ( 80, (cn(doc, "datreg"),     "Data reg.",     _DAT, True )),
            (110, (cn(tpd, "descriz"),    "Causale",       _STR, True )),
            ( 80, (cn(doc, "datdoc"),     "Data doc.",     _DAT, True )),
            ( 60, (cn(doc, "numdoc"),     "Num.",          _NUM, True )),
            (180, (cn(dst, 'descriz'),    "Destinazione",  _STR, True )),
            (100, (cn(doc, 'totimponib'), "Imponibile",    _IMP, True )),
            (100, (cn(doc, 'totimporto'), "Tot.Documento", _IMP, True )),
            ( 30, (cn(doc, 'f_acq'),      "Acq",           _CHK, True )),
            ( 30, (cn(doc, 'f_ann'),      "Ann",           _CHK, True )),
            (  1, (cn(doc, "id"),         "#doc",          _STR, True )),
        )
        self._cols=cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(doc.GetRecordset(), colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(7, (2,5))
        self.SetFitColumn(5)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        #self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc)
    
    #def OnCallDoc(self, event):
        #row = event.GetRow()
        #dbdoc = self.dbdoc
        #if 0 <= row < dbdoc.RowsCount():
            #dbdoc.MoveRow(row)
            #wait = aw.awu.WaitDialog(self, 
                                     #message="Caricamento documento in corso")
            #try:
                #Dialog = magazz.GetDataentryDialogClass()
                #dlg = Dialog(self)
                #dlg.SetOneDocOnly(dbdoc.id)
                #dlg.CenterOnScreen()
            #finally:
                #wait.Destroy()
            #r = dlg.ShowModal()
            #if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                #self.UpdateGrid()
                #if r == magazz.DOC_MODIFIED:
                    #wx.CallAfter(lambda: self.SelectRow(row))
            #dlg.Destroy()
        #event.Skip()
    
    def UpdateGrid(self):
        evt = DocumentChangedEvent(self.GetId())
        self.GetEventHandler().AddPendingEvent(evt)


# ------------------------------------------------------------------------------


class PdcIntMagMovGrid(dbglib.DbGridColoriABlocchi):
    
    def __init__(self, parent, dbmov, **kwargs):
        
        dbglib.DbGridColoriABlocchi.__init__(self, parent, -1, 
                                             size=parent.GetClientSizeTuple(),
                                             idGrid='intermov')
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        self.SetColonnaDelta(cn(dbmov, 'id_doc'))
        
        self.dbmov = dbmov
        mov = self.dbmov
        tpm = mov.tipmov
        pro = mov.prod
        doc = mov.doc
        tpd = doc.tipdoc
        pdc = doc.pdc
        mag = doc.magazz
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = []
        a = cols.append
        a(( 35, (cn(mag, "codice"),  "Mag.",         _STR, True)))
        a(( 80, (cn(doc, "datreg"),  "Data reg.",    _DAT, True)))
        a(( 35, (cn(tpd, "codice"),  "Doc.",         _STR, True)))
        a(( 80, (cn(doc, "datdoc"),  "Data doc.",    _DAT, True)))
        a(( 60, (cn(doc, "numdoc"),  "Num.",         _NUM, True)))
        a(( 35, (cn(tpm, "codice"),  "Mov.",         _STR, True)))
        a((100, (cn(pro, "codice"),  "Cod.",         _STR, True)))
        a((190, (cn(mov, "descriz"), "Descrizione.", _STR, True)))
        a(( 80, (cn(mov, "qta"),     "Quantità",     _QTA, True)))
        #a(( 90, (cn(mov, "prezzo"),  "Prezzo",       _PRZ, True)))
        a(( 80, (cn(mov, "prezzoimp"),  "Prezzo",    _PRZ, True)))
        
        if bt.MAGNUMSCO >= 1:
            a(( 60, (cn(mov, "sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 60, (cn(mov, "sconto2"), "Sc.%2",    _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 60, (cn(mov, "sconto3"), "Sc.%3",    _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 60, (cn(mov, "sconto4"), "Sc.%4",    _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 60, (cn(mov, "sconto5"), "Sc.%5",    _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 60, (cn(mov, "sconto6"), "Sc.%6",    _SCO, True)))
        a(( 90, (cn(mov, "imponibile"),"Imponibile", _IMP, True)))
        #a((110, (cn(mov, "importo"), "Importo",      _IMP, True)))
        a((200, (cn(mov, "note"),    "Note",         _STR, True)))
        a((120, (cn(tpd, "descriz"), "Documento",    _STR, True)))
        a((120, (cn(tpm, "descriz"), "Movimento",    _STR, True)))
        a((  1, (cn(mov, "id"),      "#mov",         _STR, True)))
        a((  1, (cn(doc, "id"),      "#doc",         _STR, True)))
        a((  1, (cn(pro, "id"),      "#pro",         _STR, True)))
        
        self._cols=cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(mov.GetRecordset(), colmap, canedit, canins)
        
        #self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(8, 7)
        self.SetFitColumn(6)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc)
    
    def OnCallDoc(self, event):
        row = event.GetRow()
        dbmov = self.dbmov
        if 0 <= row < dbmov.RowsCount():
            dbmov.MoveRow(row)
            wx.BeginBusyCursor()
            try:
                Dialog = magazz.GetDataentryDialogClass()
                dlg = Dialog(aw.awu.GetParentFrame(self))
                dlg.SetOneDocOnly(dbmov.doc.id)
                dlg.CenterOnScreen()
            finally:
                wx.EndBusyCursor()
            r = dlg.ShowModal()
            if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                self.UpdateGrid()
                if r == magazz.DOC_MODIFIED:
                    wx.CallAfter(lambda: self.SelectRow(row))
            dlg.Destroy()
        event.Skip()
    
    def UpdateGrid(self):
        evt = DocumentChangedEvent(self.GetId())
        self.GetEventHandler().AddPendingEvent(evt)


# ------------------------------------------------------------------------------


class PdcIntMagFtProdGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbfat, **kwargs):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              idGrid='ftprod')
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        self.dbfat = dbfat
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (cn(dbfat, "prod_codice"),  "Codice",       _STR, True)),
            (220, (cn(dbfat, "prod_descriz"), "Prodotto",     _STR, True)),
            ( 60, (cn(dbfat, "totqta"),       "Tot.Qta",      _QTA, True)),
            ( 80, (cn(dbfat, "lastdat"),      "Ultima vend.", _DAT, True)),
            ( 60, (cn(dbfat, 'lastqta'),      "Quantità",     _QTA, True)),
            ( 70, (cn(dbfat, 'lastprz'),      "Prezzo",       _PRZ, True)),
            ( 40, (cn(dbfat, 'lastsco'),      "Sc.%",         _SCO, True)),
            ( 70, (cn(dbfat, 'lastscmq'),     "Sc.Mce",       _QTA, True)),
        )
        self._cols=cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(dbfat.GetRecordset(), colmap, canedit, canins)
        
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


class PdcIntMagFatCatArtGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbfat):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              idGrid='magfatcatart')
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        self.dbfat = dbfat
        mov = dbfat
        cat = mov.prod.catart
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 35, (cn(cat, 'codice'),           "Cod.",      _STR, True)),
            (120, (cn(cat, 'descriz'),          "Categoria", _STR, True)),
            ( 60, (cn(mov, "total_statqtafat"), "Qta",       _QTA, True)),
            ( 90, (cn(mov, "total_statvalfat"), "Importo",   _IMP, True)),
        )
        self._cols=cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(mov.GetRecordset(), colmap, canedit, canins)
        
        self.AddTotalsRow(1, 'Totale:', (cn(mov, "total_statvalfat"),))
        
        self.SetNotSpecifCols((0,1))
        
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


class PdcIntMagFatProGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbfat):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              idGrid='intmagfatprod')
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        self.dbfat = dbfat
        mov = dbfat
        pro = mov.prod
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (cn(pro, 'codice'),           "Cod.",      _STR, True)),
            (140, (cn(pro, 'descriz'),          "Prodotto",  _STR, True)),
            ( 60, (cn(mov, "total_statqtafat"), "Qta",       _QTA, True)),
            ( 90, (cn(mov, "total_statvalfat"), "Importo",   _IMP, True)),
            (  1, (cn(pro, "id"),               "#pro",      _STR, True)),
        )
        self._cols=cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(mov.GetRecordset(), colmap, canedit, canins)
        
        self.SetNotSpecifCols((0,1))
        
        self.AddTotalsRow(1, 'Totali:', (cn(mov, "total_statqtafat"),
                                         cn(mov, "total_statvalfat"),))
        
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


class FatturatoPrintSel(aw.Dialog):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Selezione stampa'
        aw.Dialog.__init__(self, *args, **kwargs)
        self.report_type = None
        p = aw.Panel(self)
        wdr.FatturatoPrintSelFunc(p)
        self.AddSizedPanel(p)
        self.CenterOnScreen()
        def cn(x):
            return p.FindWindowByName(x)
        p.Bind(wx.EVT_BUTTON, self.OnPrintCat, cn('btnfatcat'))
        p.Bind(wx.EVT_BUTTON, self.OnPrintPro, cn('btnfatpro'))
    
    def OnPrintCat(self, event):
        self.report_type = 'cat'
        self.EndModal(wx.ID_OK)
    
    def OnPrintPro(self, event):
        self.report_type = 'pro'
        self.EndModal(wx.ID_OK)
    

class PdcIntMagPanel(aw.Panel):
    
    ordinverso = False
    ftalastpdc = None
    fatlastpdc = None
    
    def __init__(self, parent, cfm, iscli=False):
        
        aw.Panel.__init__(self, parent)
        self.Freeze()
        
        try:
            self.cliformixin = cfm
            #pt = wx.Panel(self, wdr.ID_PCFTOTALI)
            #wdr.PcfTotaliFunc(pt)
            wdr.AnagIntMagFunc(self)
            
            self.dbdoc = dbm.DocAll()#; self.dbdoc.ShowDialog(self)
            self.dbmov = dbm.MovAll()#; self.dbmov.ShowDialog(self)
            
            ci = lambda x: self.FindWindowById(x)
            
            if Env.Azienda.GetAutom('magordinv'):
                ci(wdr.ID_ORDINVERSO).SetValue(1)
                self.SetOrdInverso(1)
            
            self.griddoc = PdcIntMagDocGrid(ci(wdr.ID_PANDOC), self.dbdoc)
            self.gridmov = PdcIntMagMovGrid(ci(wdr.ID_PANMOV), self.dbmov)
            
            self.dbfta = None
            self.pdcid = None
            
            if iscli:
                wz = ci(wdr.ID_WORKZONE)
                #riepilogo prodotti fatturati
                p = wx.Panel(wz, -1)
                wdr.AnagIntMagFtProdFunc(p, False)
                wz.AddPage(p, "Prodotti venduti")
                self.dbfta = dbs.SintesiProVenCli()
                self.gridfta = PdcIntMagFtProdGrid(ci(wdr.ID_FTA_PANGRID), self.dbfta)
                ci(wdr.ID_FTAORDER).SetSelection(Env.Azienda.GetAutom('magordfta', 0))
                #statistica fatturato
                def cn(x):
                    return self.FindWindowByName(x)
                p = wx.Panel(wz, -1)
                wdr.AnagIntMagFatturatoFunc(p, False)
                wz.AddPage(p, "Fatturato")
                self.dbfatcat = dbs.FatturatoCliCatArt()
                self.gridfatcat = PdcIntMagFatCatArtGrid(cn('_pangridfatcat'),
                                                         self.dbfatcat)
                self.gridfatcat.SetToolTipString("""Doppio click su una categoria\n"""
                                                 """per visualizzare solo i prodotti\n"""
                                                 """che le appartengono.""")
                self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnIntMagFatCatDClick,
                          self.gridfatcat)
                self.dbfatpro = dbs.FatturatoCliPro()
                self.gridfatpro = PdcIntMagFatProGrid(cn('_pangridfatpro'),
                                                      self.dbfatpro)
            
            tabmax = ci(wdr.ID_WORKZONE).GetPageCount()-1
            
            tabdef = Env.Azienda.GetAutom('magintcli', 0)
            ci(wdr.ID_WORKZONE).SetSelection(min(tabdef, tabmax))
            self.TestSelDoc()
            
        finally:
            self.Thaw()
        
        for cid, evt, func in (
            (wdr.ID_MAGUPDATE, wx.EVT_BUTTON, self.OnUpdateFilters),
            (wdr.ID_MAGPRINT, wx.EVT_BUTTON, self.OnMagPrint),
            (wdr.ID_ORDINVERSO, wx.EVT_CHECKBOX, self.OnOrdInverso),
            (wdr.ID_WORKZONE, wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanging),
            ):
            self.Bind(evt, func, id=cid)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        self.Bind(EVT_DOCUMENT_CHANGED, self.OnUpdateFilters)
    
    def OnMagPrint(self, event):
        self.MagPrint()
        event.Skip()
    
    def MagPrint(self):
        ci = lambda x: self.FindWindowById(x)
        sel = ci(wdr.ID_WORKZONE).GetSelection()
        label = ci(wdr.ID_WORKZONE).GetPageText(sel).lower()
        if 'prodotti' in label:
            rpt.Report(self, self.dbfta, 'Scheda vendite cliente')
        elif 'documenti' in label:
            rpt.Report(self, self.dbdoc, 'Lista documenti magazzino')
        elif 'movimenti' in label:
            self.dbmov.pro = self.dbmov.prod
            rpt.Report(self, self.dbmov, 'Lista movimenti magazzino')
        elif 'fatturato' in label:
            self.FatturatoPrint()
    
    def FatturatoPrint(self):
        d = FatturatoPrintSel(self)
        ok = d.ShowModal() == wx.ID_OK
        d.Destroy()
        if ok:
            if d.report_type == 'cat':
                db = self.dbfatcat
                report = 'Fatturato cliente per categoria merce'
            elif d.report_type == 'pro':
                db = self.dbfatpro
                report = 'Fatturato cliente per prodotto'
            else:
                db = None
            if db:
                rpt.Report(self, db, report)
            
    def OnPageChanged(self, event):
        self.TestSelDoc()
        event.Skip()
    
    def TestSelDoc(self):
        ci = lambda x: self.FindWindowById(x)
        cn = lambda x: self.FindWindowByName(x)
        page = ci(wdr.ID_WORKZONE).GetSelection()
        enable = not 'prodotti fatturati' in \
               ci(wdr.ID_WORKZONE).GetPageText(page).lower()
        for name in 'id_magazz,id_tipdoc,nodocacq,nodocann'.split(','):
            cn(name).Enable(enable)
        
    def GetOrdInverso(self):
        return self.ordinverso
    
    def SetOrdInverso(self, oi=True):
        self.ordinverso = oi
    
    def OnOrdInverso(self, event):
        self.SetOrdInverso(int(event.GetSelection()))
        event.Skip()
    
    def OnPageChanging(self, event):
        self.UpdateFilters(event.GetSelection())
        self.TestSelDoc()
        event.Skip()
    
    def UpdateGrids(self, pdcid):
        self.pdcid = pdcid
        self.UpdateFilters()
    
    def OnStampa(self, event):
        #self.StampaScadenzario()
        event.Skip()
    
    #def StampaScadenzario(self):
        #db = self.gridpcf.dbscad
        #rpt.Report(self, db, "Scadenzario clienti-fornitori", testrec=db.mastro)
    
    def OnUpdateFilters(self, event):
        self.ftalastpdc = None
        self.fatlastpdc = None
        self.UpdateFilters()
        event.Skip()
    
    def UpdateFilters(self, sel=None):
        
        ci = lambda x: self.FindWindowById(x)
        cn = lambda x: self.FindWindowByName(x)
        
        if sel is None:
            sel = ci(wdr.ID_WORKZONE).GetSelection()
        label = ci(wdr.ID_WORKZONE).GetPageText(sel).lower()
        if 'prodotti' in label:
            self.UpdateFtProd()
            return
        elif 'fatturato' in label:
            self.UpdateFatturato()
            return
        if 'documenti' in label:
            tab, grid = self.dbdoc, self.griddoc
        else:
            tab, grid = self.dbmov, self.gridmov
        
        tab.ClearFilters()
        tab.AddFilter(r'doc.id_pdc=%s', self.pdcid)
        
        for name, field, op in (\
            ('id_magazz',  'doc.id_magazz', '='),\
            ('id_tipdoc',  'doc.id_tipdoc', '='),\
            ('masdatreg1', 'doc.datreg',    '>='),\
            ('masdatreg2', 'doc.datreg',    '<='),\
            ('masdatdoc1', 'doc.datdoc',    '>='),\
            ('masdatdoc2', 'doc.datdoc',    '<='),\
            ('masdatrif1', 'doc.datrif',    '>='),\
            ('masdatrif2', 'doc.datrif',    '<='),\
            ('masnumreg1', 'doc.numreg',    '>='),\
            ('masnumreg2', 'doc.numreg',    '<='),\
            ('masnumdoc1', 'doc.numdoc',    '>='),\
            ('masnumdoc2', 'doc.numdoc',    '<='),\
            ('masnumrif1', 'doc.numrif',    '>='),\
            ('masnumrif2', 'doc.numrif',    '<=')):
            val = cn(name).GetValue()
            if val:
                tab.AddFilter('%s %s %%s' % (field, op), val)
        
        for name, field in (\
            ('nodocacq', 'doc.f_acq'),\
            ('nodocann', 'doc.f_ann')):
            val = cn(name).GetValue()
            if val:
                tab.AddFilter('%s IS NULL OR %s <> 1' % (field, field))
        
        if tab.GetTableAlias() == 'mov':
            for name, field, op in (\
                ('id_prod',   'mov.id_prod',    '='),\
                ('id_tipart', 'prod.id_tipart', '='),\
                ('id_catart', 'prod.id_catart', '='),\
                ('id_marart', 'prod.id_marart', '='),\
                ('descriz',   'mov.descriz',    'LIKE')):
                val = cn(name).GetValue()
                if val:
                    if op == 'LIKE':
                        val = '%%%s%%' % val
                    tab.AddFilter('%s %s %%s' % (field, op), val)
        
        if self.ordinverso:
            order = dbm.adb.ORDER_DESCENDING
        else:
            order = dbm.adb.ORDER_ASCENDING
        tab.ClearOrders()
        if tab.GetTableAlias() == 'doc':
            tab.AddOrder("YEAR(doc.datdoc)", order)
            tab.AddOrder("doc.datdoc", order)
            tab.AddOrder("tipdoc.codice", order)
            tab.AddOrder("doc.numdoc", order)
        else:
            tab.AddOrder("doc.datdoc", order)
            tab.AddOrder("tipdoc.codice", order)
            tab.AddOrder("doc.numdoc", order)
            tab.AddOrder("mov.numriga")
        
        if not tab.Retrieve():
            aw.awu.MsgDialog(self, message=repr(tab.GetError()), 
                             style=wx.ICON_ERROR)
            return
        
        if tab.GetTableAlias() in 'doc,mov'.split(','):
            totals = grid.GetTotalsRows()
            if cn('id_tipdoc').GetValue():
                if not totals:
                    cn = lambda db, col: db._GetFieldIndex(col, inline=True)
                    if tab.GetTableAlias() == 'doc':
                        grid.AddTotalsRow(1, 'Totali:', (cn(tab, 'totimponib'),
                                                         cn(tab, 'totimporto')))
                    else:
                        grid.AddTotalsRow(5, 'Totali:', (cn(tab, 'qta'),
                                                         cn(tab, 'importo')))
            else:
                if totals:
                    del totals[:]
        grid.ChangeData(tab.GetRecordset())         
    
    def UpdateFtProd(self):
        cn = lambda x: self.FindWindowByName(x)
        if self.dbfta is None:
            return
        if self.ftalastpdc == self.pdcid:
            return
        self.ftalastpdc = self.pdcid
        filtanag = "pdc.id=%d" % self.pdcid
        filtprod = []
        for name in 'tipart,catart,marart'.split(','):
            val = cn('fta_id_%s' % name).GetValue()
            if val:
                filtprod.append('%s.id=%d' % (name, val))
        filtmov = []
        for name, op in (('masdatdoc1', '>='),
                         ('masdatdoc2', '<=')):
            val = cn(name).GetValue()
            if val:
                filtmov.append('doc.datdoc%s\'%s\'' % (op, val.Format('%Y%m%d')))
        order = "PD"[cn('ftaorder').GetSelection()]
        wx.BeginBusyCursor()
        try:
            self.dbfta.Retrieve(filtanag, 
                                ' AND '.join(filtprod), 
                                ' AND '.join(filtmov), order)
        finally:
            wx.EndBusyCursor()
        self.gridfta.ChangeData(self.dbfta.GetRecordset())
    
    def UpdateFatturato(self):
        if self.dbfatcat is None or self.dbfatpro is None:
            return
        if self.fatlastpdc == self.pdcid:
            return
        wx.BeginBusyCursor()
        try:
            self.UpdateFatturatoCatArt()
            self.UpdateFatturatoProd()
        finally:
            wx.EndBusyCursor()
    
    def GetFatturatoFilter(self):
        def cn(x):
            return self.FindWindowByName(x)
        fatcat, fatpro = self.dbfatcat, self.dbfatpro
        self.fatlastpdc = self.pdcid
        filtmov = []
        for name, op in (('masdatdoc1', '>='),
                         ('masdatdoc2', '<=')):
            val = cn(name).GetValue()
            if val:
                filtmov.append('doc.datdoc%s\'%s\'' % (op, val.Format('%Y%m%d')))
        return filtmov
    
    def UpdateFatturatoCatArt(self, filter=None):
        fatcat = self.dbfatcat
        fatcat.ClearBaseFilters()
        filtmov = self.GetFatturatoFilter()
        if filtmov:
            for f in filtmov:
                fatcat.AddBaseFilter(f)
        if filter:
            for f in filter:
                fatcat.AddBaseFilter(f)
        fatcat.Retrieve('pdc.id=%s', self.pdcid)
        self.gridfatcat.ResetView()
    
    def UpdateFatturatoProd(self, filter=None):
        fatpro = self.dbfatpro
        fatpro.ClearBaseFilters()
        filtmov = self.GetFatturatoFilter()
        if filtmov:
            for f in filtmov:
                fatpro.AddBaseFilter(f)
        if filter:
            for f in filter:
                fatpro.AddBaseFilter(f)
        fatpro.Retrieve('pdc.id=%s', self.pdcid)
        self.gridfatpro.ResetView()
    
    def OnIntMagFatCatDClick(self, event):
        row = event.GetRow()
        mov = self.dbfatcat
        filter = None
        if row < mov.RowsCount():
            mov.MoveRow(row)
            catid = mov.prod.id_catart
            if catid is not None:
                filter = ("prod.id_catart=%d" % catid,)
        self.UpdateFatturatoProd(filter)
        event.Skip()
