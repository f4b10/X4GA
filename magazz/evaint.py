#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/evaint.py
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

import magazz.movint_wdr as wdr

import magazz.dbtables as dbm
bt = dbm.Env.Azienda.BaseTab

import magazz.maglib as maglib

from awc.controls.linktable import EVT_LINKTABCHANGED

import report as rpt


FRAME_TITLE = "Stato evasione movimenti"


class GridMov(maglib.GridMovEva):
    
    def __init__(self, parent, dlg):
        
        maglib.GridMovEva.__init__(self, dlg)
        self.dbmov = dbm.ElencoMovimEva()
        self.dbmov.ShowDialog(parent)
        
        size = parent.GetClientSizeTuple()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        mov = self.dbmov
        pro = mov.pro
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
        
        cols = []
        a = cols.append
        a(( 35, (cn(mag, "codice"),  "Mag.",         _STR, True)))
        a(( 80, (cn(doc, "datreg"),  "Data reg.",    _DAT, True)))
        a(( 35, (cn(tpd, "codice"),  "Doc.",         _STR, True)))
        a(( 35, (cn(tpm, "codice"),  "Mov.",         _STR, True)))
        a(( 80, (cn(pro, "codice"),  "Codice",       _STR, True)))
        a((190, (cn(mov, "descriz"), "Descrizione",  _STR, True)))
        a(( 80, (cn(mov, "qta"),     "Qtà",          _QTA, True)))
        a(( 80, (-1,                 "Evaso",        _QTA, True)))
        a(( 80, (-2,                 "Residuo",      _QTA, True)))
        a(( 80, (cn(mov, "prezzo"),  "Prezzo",       _PRE, True)))
        a(( 85, (cn(mov, "importo"), "Importo",      _IMP, True)))
        a(( 50, (cn(doc, "numdoc"),  "Num.",         _STR, True)))
        a(( 80, (cn(doc, "datdoc"),  "Data doc.",    _DAT, True)))
        a(( 50, (cn(pdc, "codice"),  "Cod.",         _STR, True)))
        a((260, (cn(pdc, "descriz"), "Sottoconto",   _STR, True)))
        a((110, (cn(tpd, "descriz"), "Documento",    _STR, True)))
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
        
        rs = self.dbmov.GetRecordset()
        
        grid = dbglib.DbGridColoriAlternati(parent, -1, size=size, style=0,\
                                            tableClass=maglib.GridTable)
        grid.SetData( rs, colmap, canedit, canins)
        grid.GetTable().dbmov = self.dbmov
        
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
        
        def MenuPopup(self, event, row):
            def _VediEvaDoc(*args):
                self.OnVediEvaDoc(event)
            def _VediEvaMov(*args):
                self.OnVediEvaMov(event)
            self.gridmov.SelectRow(row)
            menu = wx.Menu()
            vedievadocId = wx.NewId()
            menu.Append(vedievadocId, "Vedi evasioni di tutto il documento")
            self.gridmov.Bind(wx.EVT_MENU, _VediEvaDoc, id=vedievadocId)
            vedievamovId = wx.NewId()
            menu.Append(vedievamovId, "Vedi evasioni di questo movimento")
            self.gridmov.Bind(wx.EVT_MENU, _VediEvaMov, id=vedievamovId)
            xo, yo = event.GetPosition()
            self.gridmov.PopupMenu(menu, (xo, yo))
            menu.Destroy()
            event.Skip()
        
        def _OnLabelRightClick(event, self=self):
            row = event.GetRow()
            if 0 <= row < self.dbmov.RowsCount():
                self.dbmov.MoveRow(row)
                self.gridmov.SelectRow(row)
                MenuPopup(self, event, row)
        
        grid.Bind(gl.EVT_GRID_LABEL_RIGHT_CLICK, _OnLabelRightClick)
        grid.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, _OnLabelRightClick)
    
    def OnVediEvaDoc(self, event):
        self.VediEvasioni(alldoc=True)
        event.Skip()
    
    def OnVediEvaMov(self, event):
        self.VediEvasioni(alldoc=False)
        event.Skip()
    
    def VediEvasioni(self, alldoc):
        docid = self.dbmov.doc.id
        movid = None
        if not alldoc:
            movid = self.dbmov.id
        dlg = VediEvasioniDialog(self.gridmov, docid=docid, movid=movid)
        dlg.ShowModal()
        dlg.Destroy()


# ------------------------------------------------------------------------------


class VediEvasioniGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbmov):
        
        size = parent.GetClientSizeTuple()
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1,
                                              size=parent.GetSize())
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        self.dbmov = dbmov
        mov = self.dbmov
        eva = mov.eva
        doc = eva.evadoc
        tpd = doc.evatpd
        tpm = eva.evatpm
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = []
        a = cols.append
        a(( 80, (cn(doc, "datreg"),  "Data reg.",    _DAT, True)))
        a(( 35, (cn(tpd, "codice"),  "Cod.",         _STR, True)))
        a((110, (cn(tpd, "descriz"), "Documento",    _STR, True)))
        a(( 50, (cn(doc, "numdoc"),  "Num.",         _STR, True)))
        a(( 80, (cn(doc, "datdoc"),  "Data doc.",    _DAT, True)))
        a(( 40, (cn(mov, "numriga"), "Riga",         _QTA, True)))
        a(( 35, (cn(tpm, "codice"),  "Cod.",         _STR, True)))
        a((110, (cn(tpm, "descriz"), "Movimento",    _STR, True)))
        a(( 80, (cn(mov, "qta"),     "Qtà",          _QTA, True)))
        a(( 80, (cn(eva, "qta"),     "Evaso",        _QTA, True)))
        a(( 80, (cn(mov, "prezzo"),  "Prezzo",       _PRE, True)))
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
        a(( 85, (cn(mov, "importo"), "Importo",      _IMP, True)))
        a((120, (cn(mov, "note"),    "Note",         _STR, True)))
        a(( 30, (cn(mov, "f_ann"),   "Man",          _CHK, True)))
        a(( 30, (cn(doc, "f_ann"),   "Ann",          _CHK, True)))
        a(( 30, (cn(doc, "f_acq"),   "Acq",          _CHK, True)))
        a((  1, (cn(mov, "id"),      "#mov",         _STR, True)))
        a((  1, (cn(doc, "id"),      "#doc",         _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = self.dbmov.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol(0)
        sz.AddGrowableRow(0)
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class VediEvasioniPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        wdr.VediEvasioniFunc(self)
        
        for c in aw.awu.GetAllChildrens(self):
            if hasattr(c, 'SetReadOnly'):
                c.SetReadOnly()
        
        self.dbmov = dbm.DettaglioEvasioni()
        
        pp = self.FindWindowById(wdr.ID_PANGRIDMOVEVA)
        self.gridmov = VediEvasioniGrid(pp, self.dbmov)
    
    def UpdateValues(self, docid, movid=None):
        mov = self.dbmov
        mov.ClearFilters()
        mov.AddFilter('doc.id=%s', docid)
        if movid:
            mov.AddFilter('mov.id=%s', movid)
        if mov.Retrieve():
            if mov.IsEmpty():
                aw.awu.MsgDialog(self, message="Nessun documento di evasione trovato")
            else:
                for c in aw.awu.GetAllChildrens(self):
                    name = c.GetName()
                    if name in mov.doc.GetFieldNames():
                        c.SetValue(getattr(mov.doc, name))
                self.gridmov.ChangeData(mov.GetRecordset())
        else:
            aw.awu.MsgDialog(self, message=repr(mov.GetError()))


# ------------------------------------------------------------------------------


class VediEvasioniDialog(aw.Dialog):
    """
    Dialog visione movimenti di evasione.
    """
    def __init__(self, *args, **kwargs):
        docid = kwargs.pop('docid')
        movid = kwargs.pop('movid')
        kwargs['title'] = 'Dettaglio evasione'
        aw.Dialog.__init__(self, *args, **kwargs)
        p = VediEvasioniPanel(self, -1)
        p.UpdateValues(docid, movid)
        self.AddSizedPanel(p)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class EvaIntPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        wdr.EvaMagFunc(self)
        
        pp = self.FindWindowById(wdr.ID_PANGRIDMOV)
        self.gridmov = GridMov(pp, self)
        
        for cid, func in ((wdr.ID_MASBUTUPD, self.gridmov.GridMovOnUpdateFilters),
                          (wdr.ID_MASBUTPRT, self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        def ci(x):
            return self.FindWindowById(x)
        
        o = ci(wdr.ID_MASID_TIPDOC)
        o.Bind(EVT_LINKTABCHANGED, self.OnTipDocChanged)
    
    def OnEvaMov(self, event):
        self.TestEvaControls()
        event.Skip()
    
    def OnPrint(self, event):
        rpt.Report(self, self.gridmov.dbmov, "Stato evasione movimenti")
        event.Skip()
    
    def OnTipDocChanged(self, event):
        docid = event.GetSelection()
        cfg = dbm.adb.DbTable(dbm.bt.TABNAME_CFGMAGDOC)
        cfg.Get(docid)
        tipid = cfg.id_pdctip
        for cid, id, fld in ((wdr.ID_MASID_TIPMOV, docid, "id_tipdoc"),
                             (wdr.ID_MASID_PDC,    tipid, "id_tipo")):
            o = self.FindWindowById(cid)
            if id is None:
                o.SetFilter(None)
            else:
                o.SetFilter("%s=%d" % (fld, id))


# ------------------------------------------------------------------------------


class EvaIntFrame(aw.Frame):
    """
    Frame Interrogazione documenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(EvaIntPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class EvaIntDialog(aw.Dialog):
    """
    Dialog Interrogazione movimenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(EvaIntPanel(self, -1))
        self.CenterOnScreen()
