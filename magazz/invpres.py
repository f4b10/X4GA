#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/invpres.py
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

import report as rpt
import magazz.barcodes as bcode

Env = dbm.Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

"""
Inventario presunto
Inventario con giacenza da movimenti, ordini fornitori, ordini clienti. 
"""


FRAME_TITLE = "Inventario presunto"


class InventarioPresuntoGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbinp):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbinp = dbinp
        pro = dbinp
        
        def cc(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        
        qw = 110 # qta col width
        
        cols = [( 90, (cc(pro, 'codice'),         "Codice",          _STR, True)),
                (300, (cc(pro, 'descriz'),        "Prodotto",        _STR, True)),
                ( qw, (cc(pro, 'total_giac'),     "Giacenza",        _QTA, True)),
                ( qw, (cc(pro, 'total_backfor'),  "BackOrd.Fornit.", _QTA, True)),
                ( qw, (cc(pro, 'total_backcli'),  "BackOrd.Clienti", _QTA, True)),
                ( qw, (cc(pro, 'total_giacpres'), "Giac.Presunta",   _QTA, True)),
                ]
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(dbinp.GetRecordset(), colmap, canedit, canins)
        
        self.AddTotalsRow(1,'Totali:',(cc(pro, "total_giac"),
                                       cc(pro, "total_backfor"),
                                       cc(pro, "total_backcli"),
                                       cc(pro, "total_giacpres"),))
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


class BackordersGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbbko):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbbko = dbbko
        mov = dbbko
        tpm = mov.tipmov
        doc = mov.doc
        tpd = doc.tipdoc
        pdc = doc.pdc
        
        def cc(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _QTA = bt.GetMagQtaMaskInfo()
        
        qw = 110 # qta col width
        iw = 110 # val col width
        
        cols = [( 50, (cc(tpd, 'codice'),         "Cod.",       _STR, True)),
                (120, (cc(tpd, 'descriz'),        "Documento",  _STR, True)),
                ( 50, (cc(doc, 'numdoc'),         "Num.",       _STR, True)),
                ( 80, (cc(doc, 'datdoc'),         "Data doc.",  _DAT, True)),
                ( 30, (cc(tpm, 'codice'),         "M.",         _STR, True)),
                ( 50, (cc(pdc, 'codice'),         "Codice",     _STR, True)),
                (240, (cc(pdc, 'descriz'),        "Anagrafica", _STR, True)),
                ( 90, (cc(mov, 'qta'),            "Qtà",        _QTA, True)),
                ( 90, (cc(mov, 'total_evas_qta'), "Evaso",      _QTA, True)),
                ( qw, (cc(mov, 'total_residuo'),  "Backorder",  _QTA, True)),]
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.AddTotalsRow(1,'Totali:',(cc(mov, "qta"),
                                       cc(mov, "total_evas_qta"),
                                       cc(mov, "total_residuo"),))
        
        self.SetData(dbbko.GetRecordset(), colmap, canedit, canins)
        
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


class InventarioPresuntoPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.InventarioPresuntoFunc(self)
        cn = self.FindWindowByName
        self.dbinp = dbm.InventarioPresunto()
        self.dbinp.ShowDialog(self)
        self.winbackord = None
        self.gridinp = InventarioPresuntoGrid(cn('pangridinv'), self.dbinp)
        self.UpdateBackorders()
        for name, func in (('butupdate', self.OnUpdateData),
                           ('butprint', self.OnPrintData),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        self.Bind(wx.EVT_RADIOBOX, self.OnTipoBackordersChanged, cn('tipobackord'))
        self.gridinp.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelect)
    
    def OnTipoBackordersChanged(self, event):
        tb = event.GetEventObject().GetValue()
        if tb == "N":
            if self.winbackord:
                self.winbackord.Hide()
        else:
            if not self.winbackord:
                self.winbackord = InventarioPresuntoBackordersFrame(self.GetParent())
            self.winbackord.SetCliFor(tb)
            self.UpdateBackorders()
            self.winbackord.Show()
        event.Skip()
    
    def OnCellSelect(self, event):
        self.UpdateBackorders(event.GetRow())
        event.Skip()
    
    def UpdateBackorders(self, row=None):
        if not self.winbackord:
            return
        if row is None:
            row = self.gridinp.GetSelectedRows()[-1]
        if 0 <= row < self.dbinp.RowsCount():
            self.dbinp.MoveRow(row)
            self.winbackord.SetProdotto(self.dbinp.id)
    
    def OnUpdateData(self, event):
        self.UpdateData()
        self.UpdateBackorders()
        event.Skip()
    
    def OnPrintData(self, event):
        pass
    
    def UpdateData(self):
        i = self.dbinp
        i.ClearFilters()
        cn = self.FindWindowByName
        #filtri sul codice
        v1 = cn('codice1').GetValue()
        v2 = cn('codice2').GetValue()
        if v1 or v2:
            if v1: i.AddFilter(r"prod.codice>=%s", v1)
            if v2: i.AddFilter(r"prod.codice<=%s", v2.rstrip()+'Z')
        #filtri sulle classificazioni
        for name in 'tipart,catart,gruart,pdcforn'.split(','):
            c1 = cn(name+'1')
            c2 = cn(name+'2')
            if hasattr(c1, 'GetValueCod'):
                v1 = cn(name+'1').GetValueCod()
                v2 = cn(name+'2').GetValueCod()
            else:
                v1 = cn(name+'1').GetValue()
                v2 = cn(name+'2').GetValue()
            if v1 or v2:
                if v1 == v2:
                    i.AddFilter("%s.codice=%%s" % name, v1)
                else:
                    if v1:
                        i.AddFilter("%s.codice>=%%s" % name, v1)
                    if v2:
                        i.AddFilter("%s.codice<=%%s" % name, v2.rstrip()+'Z')
        def Progr0(db):
            db.__waitProgress = aw.awu.WaitDialog(self, maximum=db.RowsCount())
        def Progr1(db, n):
            db.__waitProgress.SetValue(n)
        def Progr2(db):
            db.__waitProgress.Destroy()
        i.Retrieve(func0=Progr0, func1=Progr1, func2=Progr2, 
                   checkgiac=cn('checkgiac').GetValue(),
                   checkofor=cn('checkofor').GetValue(),
                   checkocli=cn('checkocli').GetValue(),
                   checkgpin=cn('checkgpin').GetValue(),)
        self.gridinp.ChangeData(i.GetRecordset())


# ------------------------------------------------------------------------------


class InventarioPresuntoFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = InventarioPresuntoPanel(self)
        self.AddSizedPanel(self.panel, 'invprespanel')


# ------------------------------------------------------------------------------


class InventarioPresuntoBackordersElencoEvasioniGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbmov):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbmov = dbmov
        mov = dbmov
        tpm = mov.tipmov
        doc = mov.doc
        pdc = doc.pdc
        tpd = doc.tipdoc
        
        def cc(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _VAL = bt.GetValIntMaskInfo()
        
        qw = 110 # qta col width
        iw = 110 # val col width
        
        cols = []
        a = cols.append
        a(( 50, (cc(tpd, 'codice'),  "Cod.",      _STR, True)))
        a((140, (cc(tpd, 'descriz'), "Documento", _STR, True)))
        a(( 50, (cc(doc, 'numdoc'),  "Num.",      _STR, True)))
        a(( 80, (cc(doc, 'datdoc'),  "Data doc.", _DAT, True)))
        a(( 30, (cc(tpm, 'codice'),  "M.",        _STR, True)))
        a(( 90, (cc(mov, 'qta'),     "Qtà",       _QTA, True)))
        a(( 90, (cc(mov, 'prezzo'),  "Prezzo",    _VAL, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 50, (cc(mov, 'sconto1'), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 50, (cc(mov, 'sconto2'), "Sc.%2", _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 50, (cc(mov, 'sconto3'), "Sc.%3", _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 50, (cc(mov, 'sconto4'), "Sc.%4", _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 50, (cc(mov, 'sconto5'), "Sc.%5", _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 50, (cc(mov, 'sconto6'), "Sc.%6", _SCO, True)))
        a((110, (cc(mov, 'importo'), "Importo",   _VAL, True)))
        a((200, (cc(mov, 'note'),    "Note",      _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(dbmov.GetRecordset(), colmap, canedit, canins)
        
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


class InventarioPresuntoBackordersPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.InventarioPresuntoBackordersFunc(self)
        self.dbbko = None
        self.dbeva = dbm.Movim(bt.TABNAME_MOVMAG_B, 'mov')
        self.dbeva.Reset()
        self.gridbko = None
        self.clifor = None
        self.prodid = None
    
    def SetCliFor(self, clifor):
        self.clifor = clifor
        l = 'Dettaglio evasioni del %s' % 'cliente fornitore'.split()['CF'.index(clifor)]
        cn = self.FindWindowByName
        cn('desanag').SetLabel(l)
        self.dbbko = dbm.MovimentiConEvasione()
        tpm = dbm.adb.DbTable(bt.TABNAME_CFGMAGMOV, 'tipmov')
        tipana = 'cli for'.split()['CF'.index(clifor)]
        tpm.Retrieve('tipmov.aggord%s IN (1,-1)' % tipana)
        if tpm.IsEmpty():
            f = 'FALSE'
        elif tpm.OneRow():
            f = 'tipmov.id=%d' % tpm.id
        else:
            f = 'tipmov.id IN (%s)' % ','.join(map(str, [tpm.id for tpm in tpm]))
        self.dbbko.AddBaseFilter(f)
        if self.gridbko is None:
            self.gridbko = BackordersGrid(cn('panbackord'), self.dbbko)
            self.grideva = InventarioPresuntoBackordersElencoEvasioniGrid(cn('panbackeva'), self.dbeva)
            self.gridbko.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelected)
    
    def OnCellSelected(self, event):
        self.UpdateEvasioni(event.GetRow())
        event.Skip()
    
    def UpdateEvasioni(self, row=None):
        bko = self.dbbko
        eva = self.dbeva
        if row is None:
            row = bko.GetSelectedRows()[-1]
        if 0 <= row < self.dbbko.RowsCount():
            bko.MoveRow(row)
            eva.Retrieve('mov.id_moveva=%s', bko.id)
            self.grideva.ChangeData(eva.GetRecordset())
    
    def SetProdotto(self, prodid):
        self.prodid = prodid
        self.FindWindowByName('id_prod').SetValue(prodid)
        self.dbbko.Retrieve('mov.id_prod=%s', prodid)
        self.gridbko.ChangeData(self.dbbko.GetRecordset())
    
    def UpdateData(self):
        pass


# ------------------------------------------------------------------------------


class InventarioPresuntoBackordersFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Elenco backorders'
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = InventarioPresuntoBackordersPanel(self)
        self.AddSizedPanel(self.panel, 'inventariopresunto_backorders')
        self.CenterOnScreen()
    
    def SetCliFor(self, *args, **kwargs):
        return self.panel.SetCliFor(*args, **kwargs)
    
    def SetProdotto(self, *args, **kwargs):
        return self.panel.SetProdotto(*args, **kwargs)
