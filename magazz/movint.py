#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/movint.py
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


FRAME_TITLE = "Movimenti magazzino"


class GridMov(maglib.GridMov):
    
    def __init__(self, parent, dlg):
        
        maglib.GridMov.__init__(self, dlg)
        self.dbmov = dbm.ElencoMovim()
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
        a(( 35, (cn(mag, "codice"),    "Mag.",         _STR, True)))
        a(( 80, (cn(doc, "datreg"),    "Data reg.",    _DAT, True)))
        a(( 35, (cn(tpd, "codice"),    "Cod.",         _STR, True)))
        a((110, (cn(tpd, "descriz"),   "Documento",    _STR, True)))
        a(( 50, (cn(doc, "numdoc"),    "Num.",         _STR, True)))
        a(( 80, (cn(doc, "datdoc"),    "Data doc.",    _DAT, True)))
        a(( 50, (cn(pdc, "codice"),    "Cod.",         _STR, True)))
        a((260, (cn(pdc, "descriz"),   "Sottoconto",   _STR, True)))
        a(( 35, (cn(tpm, "codice"),    "Cod.",         _STR, True)))
        a((110, (cn(tpm, "descriz"),   "Movimento",    _STR, True)))
        a(( 90, (cn(pro, "codice"),    "Codice",       _STR, True)))
        a((205, (cn(mov, "descriz"),   "Descrizione",  _STR, True)))
        a(( 80, (cn(mov, "qta"),       "Qtà",          _QTA, True)))
        #a(( 80, (cn(mov, "prezzo"),    "Prezzo",       _PRE, True)))
        a(( 80, (cn(mov, "prezzoimp"),  "Prezzo",       _PRE, True)))
        #a(( 80, (cn(iva, "perciva"),    "Iva",       _PRE, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 45, (cn(mov, "sconto1"),   "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 45, (cn(mov, "sconto2"),   "Sc.%2",    _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 45, (cn(mov, "sconto3"),   "Sc.%3",    _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 45, (cn(mov, "sconto4"),   "Sc.%4",    _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 45, (cn(mov, "sconto5"),   "Sc.%5",    _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 45, (cn(mov, "sconto6"),   "Sc.%6",    _SCO, True)))
        #a(( 90, (cn(mov, "importo"),   "Importo",      _IMP, True)))
        a(( 90, (cn(mov, "imponibile"),"Imponibile",   _IMP, True)))
        a((120, (cn(mov, "note"),      "Note",         _STR, True)))
        a(( 35, (cn(iva, "codice"),    "Cod.",         _STR, True)))
        a(( 90, (cn(iva, "descriz"),   "Aliquota IVA", _STR, True)))
        a(( 35, (cn(age, "codice"),    "Cod.",         _STR, True)))
        a(( 90, (cn(age, "descriz"),   "Agente",       _STR, True)))
        a(( 30, (cn(doc, "f_printed"), "St.",          _CHK, True)))
        a(( 30, (cn(doc, "f_emailed"), "Em.",          _CHK, True)))
        a(( 30, (cn(mov, "f_ann"),     "Man",          _CHK, True)))
        a(( 30, (cn(doc, "f_ann"),     "Ann",          _CHK, True)))
        a(( 30, (cn(doc, "f_acq"),     "Acq",          _CHK, True)))
        a((  1, (cn(mov, "id"),        "#mov",         _STR, True)))
        a((  1, (cn(doc, "id"),        "#doc",         _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = self.dbmov.GetRecordset()
        
        grid = dbglib.DbGridColoriAlternati(parent, -1, size=size, style=0,\
                                            tableClass=maglib.GridTable,
                                            idGrid='inter_mov')
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
        
        self.PostInit()


# ------------------------------------------------------------------------------


class MovIntPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        wdr.MovMagFunc(self)
        
        pp = self.FindWindowById(wdr.ID_PANGRIDMOV)
        self.gridmov = GridMov(pp, self)
        
        for cid, func in ((wdr.ID_MASBUTUPD, self.gridmov.GridMovOnUpdateFilters),
                          (wdr.ID_MASBUTPRT, self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        o = self.FindWindowById(wdr.ID_MASID_TIPDOC)
        o.Bind(EVT_LINKTABCHANGED, self.OnTipDocChanged)
    
    def OnPrint(self, event):
        rpt.Report(self, self.gridmov.dbmov, "Lista movimenti magazzino")
        event.Skip()
    
    def OnTipDocChanged(self, event):
        td = event.GetEventObject()
        docid = td.GetValue()
        def cn(x):
            return self.FindWindowByName(x)
        cn('masid_tipmov').SetTipoDoc(td.GetValue())
        cn('masid_tipmov').SetValue(None)
        cn('masid_pdc').SetPdcTipCods(td.dbdoc.tipana.codice)
        e = (td.dbdoc.askagente == 'X')
        c = cn('masid_agente')
        c.Enable(e)
        if not e:
            c.SetValue(None)


# ------------------------------------------------------------------------------


class MovIntFrame(aw.Frame):
    """
    Frame Interrogazione documenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(MovIntPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class MovIntDialog(aw.Dialog):
    """
    Dialog Interrogazione movimenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(MovIntPanel(self, -1))
        self.CenterOnScreen()
