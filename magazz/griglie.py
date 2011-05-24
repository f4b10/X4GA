#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/griglie.py
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

import magazz.griglie_wdr as wdr

from awc.controls.linktable import EVT_LINKTABCHANGED

import stormdb as adb

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import awc.controls.linktable as lt
import awc.controls.datectrl as dc

from anag.prod import ProdDialog
from anag.pdctip import PdcTipDialog
from anag.clienti import ClientiDialog
from anag.fornit import FornitDialog

_evtPRODCHANGED = wx.NewEventType()
EVT_PRODCHANGED = wx.PyEventBinder(_evtPRODCHANGED, 1)
class ProdChangedEvent(wx.PyCommandEvent):
    pass


FRAME_TITLE = "Griglie prezzi"


class GridSintAnag(dbglib.DbGrid):
    
    def __init__(self, parent, dbsia):
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), style=0)
        self.dbsia = dbsia
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        sia = dbsia
        
        _STR = gl.GRID_VALUE_STRING
        
        cols = (\
            ( 50, (cn(sia, "pdc_codice"),  "Cod.",       _STR, True )),\
            (200, (cn(sia, "pdc_descriz"), "Anagrafica", _STR, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData((), colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(-1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class GridSintesi(dbglib.DbGrid):
    
    def __init__(self, parent, dbsin):
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), style=0)
        self.dbsin = dbsin
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        sin = dbsin
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            (80, (cn(sin, "data"),          "Data",       _DAT, True )),\
            (70, (cn(sin, "count_id_prod"), "Prodotti",   _NUM, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
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


# ------------------------------------------------------------------------------


class GridGriglia(dbglib.DbGrid):
    
    def __init__(self, parent, dbgri, clifor):
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), style=0)
        self.dbgri = dbgri
        self.clifor = clifor
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        gri = self.dbgri
        pro = gri.prod
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _VAL = bt.GetValIntMaskInfo()
        _PZC = bt.GetMagPzcMaskInfo()
        _PRC = bt.GetMagScoMaskInfo()
        wp = 100
        ws = 40
        
        cols = []
        edc = []
        def a(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                edc.append(n)
            return n
        def b(x):
            return a(x, True)
        
        self.COL_CODART =  a((100, (cn(pro, "codice"),  "Codice",   _STR, True)))
        self.COL_DESCRIZ = a((180, (cn(pro, "descriz"), "Prodotto", _STR, True)))
        self.COL_DATA =    b(( 80, (cn(gri, 'data'),    "Data",     _DAT, True)))
        
        if self.clifor == "C":
            cde = bt.MAGCDEGRIP
        elif self.clifor == "F":
            cde = bt.MAGCDEGRIF
        else:
            raise Exception, "Impossibile determinare se la griglia è per i clienti o per i fornitori"
        if cde:
            self.COL_EXTCOD = b(( 80, (cn(gri, "ext_codice"),  "Codice Ext.",      _STR, False)))
            self.COL_EXTDES = b((200, (cn(gri, "ext_descriz"), "Descrizione Ext.", _STR, False)))
        
        self.COL_PREUFF =  a(( wp, (cn(pro, "prezzo"),  "Listino uff.",   _VAL, False)))
        self.COL_PREGRI =  b(( wp, (cn(gri, "prezzo"),  "Prezzo griglia", _VAL, False)))
        self.COL_SCONTO1 = b(( ws, (cn(gri, "sconto1"), "Sc.%1",          _PRC, False)))
        self.COL_SCONTO2 = b(( ws, (cn(gri, "sconto2"), "Sc.%2",          _PRC, False)))
        self.COL_SCONTO3 = b(( ws, (cn(gri, "sconto3"), "Sc.%3",          _PRC, False)))
        
        if bt.MAGPZCONF and bt.MAGPZGRIP:
            self.COL_PZCONF = b(( 50, (cn(gri, "pzconf"), "Pz.Conf.",     _PZC, False)))
        
        self.COL_ID =      a((  1, (cn(gri, "id"),      "#gri",           _STR, True )))
        
        self.edcols = edc
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        #afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1, self.TestValues), )
        self.SetData((), colmap, canedit, canins)
        
        self._bgcol1 = bc.GetColour("antiquewhite")
        self._bgcol2 = bc.GetColour("moccasin")
        self.SetCellDynAttr(self.GetAttr)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallProd)
    
    def OnCallProd(self, event):
        try:
            self.dbgri.MoveRow(event.GetRow())
            wx.BeginBusyCursor()
            dlg = ProdDialog(self, onecodeonly=self.dbgri.prod.id)
            dlg.OneCardOnly(self.dbgri.prod.id)
            ret = dlg.ShowModal()
            wx.EndBusyCursor()
            dlg.Destroy()
            if ret>0:
                evt = ProdChangedEvent(_evtPRODCHANGED, self.GetId())
                evt.SetEventObject(self)
                evt.SetId(self.GetId())
                self.GetEventHandler().AddPendingEvent(evt)
        except:
            pass
        event.Skip()
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        
        readonly = not col in self.edcols
        attr.SetReadOnly(readonly)
        
        if row%2 == 0:
            bgcol = self._bgcol2
        else:
            bgcol = self._bgcol1
        
        attr.SetBackgroundColour(bgcol)
        
        return attr


# ------------------------------------------------------------------------------


class GrigliaPanel(aw.Panel):
    
    clifor = None
    desana = None
    
    def __init__(self, *args, **kwargs):
        
        if self.clifor is None:
            raise Exception, "Impossibile determinare il tipo anagrafico della griglia"
        
        aw.Panel.__init__(self, *args, **kwargs)
        if self.clifor == 'C':
            wdr.LinkTableClienteFornitore = wdr.alib.LinkTableCliente
        else:
            wdr.LinkTableClienteFornitore = wdr.alib.LinkTableFornit
        wdr.GrigliaFunc(self)
        
        ci = self.FindWindowById
        
        gri = adb.DbTable(bt.TABNAME_GRIGLIE, 'gri', writable=True)
        pdc = gri.AddJoin(bt.TABNAME_PDC,     'pdc', join=adb.JOIN_RIGHT)
        pro = gri.AddJoin(bt.TABNAME_PROD,    'prod', join=adb.JOIN_RIGHT)
        sts = pro.AddJoin(bt.TABNAME_STATART, 'status', join=adb.JOIN_LEFT)
        gri.AddOrder('prod.codice')
        gri.Get(-1)
        
        self.dbgri = gri
        
        sia = adb.DbTable(bt.TABNAME_GRIGLIE, 'gri', writable=False)
        pdc = sia.AddJoin(bt.TABNAME_PDC,     'pdc', join=adb.JOIN_RIGHT)
        pro = sia.AddJoin(bt.TABNAME_PROD,    'prod', join=adb.JOIN_RIGHT)
        tip = pro.AddJoin(bt.TABNAME_STATART, 'status', join=adb.JOIN_LEFT, fields=None)
        tip = pdc.AddJoin(bt.TABNAME_PDCTIP,  'tipo', fields=None)
        sia.Synthetize()
        sia.AddGroupOn('gri.id_pdc')
        sia.AddGroupOn('pdc.codice', alias='pdc_codice')
        sia.AddGroupOn('pdc.descriz', alias='pdc_descriz')
        sia.AddGroupOn('tipo.tipo', alias='pdc_tipana')
        sia.AddOrder('pdc.descriz')
        sia.Get(-1)
        
        self.dbsia = sia
        
        if bt.MAGDATGRIP:
            
            sin = adb.DbTable(bt.TABNAME_GRIGLIE, 'gri', writable=False)
            pdc = sin.AddJoin(bt.TABNAME_PDC,     'pdc', join=adb.JOIN_RIGHT)
            pro = sin.AddJoin(bt.TABNAME_PROD,    'prod', join=adb.JOIN_RIGHT)
            sin.Synthetize()
            sin.AddGroupOn('gri.data')
            sin.AddCountOf('gri.id_prod')
            sin.AddOrder('gri.data', adb.ORDER_DESCENDING)
            sin.Get(-1)
            
            self.dbsin = sin
            
            self.dataval = None
            
            self.gridsin = GridSintesi( ci(wdr.ID_PANGRIDSIN), self.dbsin)
        
        self.id_pdc = None
        self.grigliachanged = False
        self.sologriglia = False
        
        self.gridsia = GridSintAnag(ci(wdr.ID_PANGRIDSIA), self.dbsia)
        self.gridgri = GridGriglia( ci(wdr.ID_PANGRIDGRI), self.dbgri, self.clifor)
        
        self.gridsia.Bind(gl.EVT_GRID_SELECT_CELL, self.OnSelectPdc)
        self.gridgri.Bind(gl.EVT_GRID_CELL_CHANGE, self.OnGrigliaChanged)
        
        cn = lambda x: self.FindWindowByName(x)
        for name, evt in (('id_pdc',    lt.EVT_LINKTABCHANGED),
                          ('codice',    wx.EVT_TEXT),
                          ('descriz',   wx.EVT_TEXT),
                          ('id_status', lt.EVT_LINKTABCHANGED),
                          ('id_catart', lt.EVT_LINKTABCHANGED),
                          ('id_gruart', lt.EVT_LINKTABCHANGED),
                          ('id_tipart', lt.EVT_LINKTABCHANGED)):
            self.Bind(evt, self.OnUpdateSin, cn(name))
        
        self.Bind(wx.EVT_CHECKBOX, self.OnSoloGriglia, cn('sologriglia'))
        self.Bind(wx.EVT_BUTTON, self.OnSaveGriglia, ci(wdr.ID_SAVEGRIGLIA))
        self.Bind(EVT_PRODCHANGED, self.OnProdChanged)
        
        if bt.MAGDATGRIP:
            self.gridsin.Bind(gl.EVT_GRID_SELECT_CELL, self.OnUpdateData)
            self.Bind(dc.EVT_DATECHANGED, self.OnData, cn('data'))
        
        self.FindWindowByName('clifor_label').SetLabel(self.desana)
        self.UpdateSintAnag()
    
    def OnProdChanged(self, event):
        self.UpdateGriglia()
        event.Skip()
    
    def OnSoloGriglia(self, event):
        self.sologriglia = event.GetEventObject().GetValue()
        self.UpdateGriglia()
        event.Skip()
    
    def OnGrigliaChanged(self, event):
        self.SetGrigliaChanged(True)
        event.Skip()
    
    def SetGrigliaChanged(self, changed):
        self.grigliachanged = changed
        self.FindWindowById(wdr.ID_SAVEGRIGLIA).Enable(changed)
    
    def OnData(self, event):
        data = event.GetEventObject().GetValue()
        self.dataval = data
        self.UpdateGriglia()
        self.EnableGriglia()
        event.Skip()
    
    def EnableGriglia(self):
        e = self.id_pdc is not None
        if bt.MAGDATGRIP:
            e = e and self.dataval is not None
        self.gridgri.Enable(e)
    
    def OnUpdateSin(self, event):
        ctr = event.GetEventObject()
        if ctr.GetName() == 'id_pdc':
            self.id_pdc = ctr.GetValue()
        else:
            self.UpdateSintAnag()
        if bt.MAGDATGRIP:
            self.UpdateSintesi()
        #workaround: il cambio del contenuto grid sintesi non scatena l'evento
        #di selezione riga, con conseguente non aggiornamento della data e
        #quindi della griglia :(
        self.UpdateGriglia()
        if ctr.GetName() == 'id_pdc':
            self.EnableGriglia()
        event.Skip()
    
    def OnSelectPdc(self, event):
        sia = self.dbsia
        try:
            sia.MoveRow(event.GetRow())
        except:
            pass
        self.FindWindowByName('id_pdc').SetValue(sia.id_pdc)
        event.Skip()
    
    def OnUpdateData(self, event):
        sin = self.dbsin
        try:
            sin.MoveRow(event.GetRow())
        except:
            pass
        if bt.MAGDATGRIP:
            self.SetDataVal(sin.data)
        event.Skip()
    
    def SetDataVal(self, data):
        self.FindWindowByName('data').SetValue(data)
    
    def UpdateSintesi(self):
        self.ApplyFilters(self.dbsin, self.gridsin, riep=True)
    
    def UpdateSintAnag(self):
        self.ApplyFilters(self.dbsia, self.gridsia, riep=True, riepanag=True)
    
    def UpdateGriglia(self):
        self.ApplyFilters(self.dbgri, self.gridgri, riep=False)
        self.SetGrigliaChanged(False)
    
    def ApplyFilters(self, gri, grid, riep, riepanag=False):
        if not riep and self.id_pdc is None:
            return
        cn = lambda x: self.FindWindowByName(x)
        gri.ClearFilters()
        if riep:
            if riepanag:
                gri.AddFilter("tipo.tipo=%s", self.clifor)
            else:
                gri.AddFilter("gri.id_pdc=%s", self.id_pdc)
        else:
            try:
                expr = "gri.id_prod=prod.id AND (gri.id_pdc=%s" % self.id_pdc
                if bt.MAGDATGRIP:
                    #expr += " AND gri.data='%s'" % adb.DateTime.ISO.str(self.dataval)[:10]
                    expr += " AND gri.data='%s'" % self.dataval.FormatANSI()[:10]
                if self.sologriglia:
                    gri.AddFilter('gri.id_pdc=%s', self.id_pdc)
                    if bt.MAGDATGRIP:
                        gri.AddFilter('gri.data=%s', self.dataval)
                else:
                    expr += " OR gri.id_pdc IS NULL"
                expr += ")"
                gri.prod._info.relation.expression = expr
            except:
                return
        for name in ('codice',
                     'descriz'):
            val = cn(name).GetValue()
            if val:
                gri.AddFilter("prod.%s LIKE %%s" % name, val+'%')
        for name in ('id_status',
                     'id_catart',
                     'id_gruart',
                     'id_tipart'):
            val = cn(name).GetValue()
            if val:
                gri.AddFilter("prod.%s=%%s" % name, val)
        if cn('ssv').GetValue():
            gri.AddFilter("status.hidesearch IS NULL OR status.hidesearch<>1")
        if riepanag and bt.MAGDATGRIP:
            gri.AddFilter("gri.data IS NOT NULL")
        gri.Retrieve()
        grid.ChangeData(gri.GetRecordset())
    
    def OnSaveGriglia(self, event):
        if self.Validate():
            self.SaveGriglia()
            pdcid = self.id_pdc
            self.UpdateSintAnag()
            if self.dbsia.Locate(lambda x: x.id_pdc == pdcid):
                self.gridsia.SetGridCursor(self.dbsia.RowNumber(),0)
            if bt.MAGDATGRIP:
                self.UpdateSintesi()
                data = self.dataval
                if self.dbsin.Locate(lambda x: x.data == data):
                    self.gridsin.SetGridCursor(self.dbsin.RowNumber(),0)
        event.Skip()
    
    def TestValori(self, x):
        cp, cz = map(lambda x: self.dbgri._GetFieldIndex(x, inline=True),
                     ('prezzo', 'pzconf'))
        return (x[cp] or 0) or (x[cz] or 0)
    
    def Validate(self):
        out = True
        try:
            aw.awu.ListSearch(self.dbgri.GetRecordset(), self.TestValori)
        except:
            if aw.awu.MsgDialog(self, message=\
                                """Nessun è presente alcun prezzo: se si è """\
                                """in modifica, l'intera griglia verrà """\
                                """eliminata.\n\nConfermi?""",
                                style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_NO:
                out = False
        return out
    
    def SaveGriglia(self):
        gri = self.dbgri
        rs = gri.GetRecordset()
        n = len(rs)-1
        for row in range(n, -1, -1):
            gri.MoveRow(row)
            if self.TestValori(rs[row]):
                if gri.id_pdc is None:
                    gri.id_pdc = self.id_pdc
                if gri.id_prod is None:
                    gri.id_prod = gri.prod.id
                if gri.data is None and bt.MAGDATGRIP:
                    gri.data = self.dataval
                #faccio recepire alla dbtable che il record è da salvare poiché
                #è stato modificato qualcosa direttamente dal dbgrid, senza
                #passare x l'attribuzione di variabile con __setattr__
                if gri.id is not None and not gri.id in gri._info.modifiedRecords:
                    gri._info.modifiedRecords.append(gri.id)
            else:
                gri.Delete()
        out = gri.Save()
        if out:
            self.UpdateGriglia()
        else:
            aw.awu.MsgDialog(self, message=repr(gri.GetError()))
        return out


# ------------------------------------------------------------------------------


class GrigliaClientiPanel(GrigliaPanel):
    clifor = 'C'
    desana = 'Cliente'


# ------------------------------------------------------------------------------


class GrigliaFornitPanel(GrigliaPanel):
    clifor = 'F'
    desana = 'Fornitore'


# ------------------------------------------------------------------------------


class GrigliaClientiFrame(aw.Frame):
    """
    Frame gestione griglia prezzi clienti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GrigliaClientiPanel(self, -1))
        self.CenterOnScreen()
    

# ------------------------------------------------------------------------------


class GrigliaFornitFrame(aw.Frame):
    """
    Frame gestione griglia prezzi fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GrigliaFornitPanel(self, -1))
        self.CenterOnScreen()
