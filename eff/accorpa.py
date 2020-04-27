#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         eff/accorpa.py
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
import awc.util as awu

import Env
import contab.dbtables as dbc

from contab import pcf_wdr as wdr

import report as rpt

import copy
import mx.DateTime as dt


FRAME_TITLE = "Accorpamento Effetti"


RSACC_PCF_ID =   0
RSACC_PDC_ID =   1
RSACC_ACCORPA =  2
RSACC_RACCOGLI = 3
RSACC_DATSCAD =  4
RSACC_MPA_ID =   5
RSACC_MPA_COD =  6
RSACC_MPA_DES =  7
RSACC_IMPTOT =   8
RSACC_IMPPAR =   9
RSACC_SALDO =   10
RSACC_CAU_ID =  11
RSACC_CAU_COD = 12
RSACC_CAU_DES = 13
RSACC_NUMDOC =  14
RSACC_DATDOC =  15
RSACC_COLORS =  16


adb = dbc.adb
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours


class PcfGrid(dbglib.DbGrid):
    """
    Griglia partite del cliente/fornitore
    """
    
    def __init__(self, parent, idGrid=None):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable effetti (eff.dbtables.Eff)
        """
        
        class Table(dbglib.DbGridTable):
            totacc = ()
            totrac = ()
            def GetDataValue(self, row, col):
                rs = self.data
                if col == 0: #colonna 'accorpa'
                    value = int(rs[row][RSACC_PCF_ID] in self.totacc)
                elif col == 1: #colonna 'accogli'
                    value = int(rs[row][RSACC_PCF_ID] in self.totrac)
                else:
                    value = dbglib.DbGridTable.GetDataValue(self, row, col)
                return value
        
        dbglib.DbGrid.__init__(self, parent, -1, tableClass=Table, 
                               size=parent.GetClientSizeTuple(), style=0,
                               idGrid=idGrid)
        self.data = []
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 60, (RSACC_ACCORPA,  "Accorpa",       _CHK, True)),
            ( 60, (RSACC_RACCOGLI, "Raccogli",      _CHK, True)),
            ( 80, (RSACC_DATSCAD,  "Scadenza",      _DAT, True)),
            (100, (RSACC_MPA_DES,  "Mod.Pagamento", _STR, True)),
            (110, (RSACC_SALDO,    "Saldo",         _IMP, True)),
            (100, (RSACC_CAU_DES,  "Documento",     _STR, True)),
            ( 60, (RSACC_NUMDOC,   "Numero",        _STR, True)),
            ( 80, (RSACC_DATDOC,   "Data",          _DAT, True)),
            ( 50, (RSACC_PCF_ID,   "pcf#",          _STR, True)),
        )
        
        #definizione colori alternati coerentemente con la data di scadenza
        #per eveidenziare i gruppi di partite del cliente che scadono nella
        #stessa data
        self.colors = ((bc.GetColour('black'), bc.GetColour('khaki')),
                       (bc.GetColour('black'), bc.GetColour('turquoise')))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False
        
        self.SetData(self.data, colmap, canEdit=True)
        self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        self.SetCellDynAttr(self.GetAttr)
        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnCellSelected)
        #grid.Bind(gl.EVT_GRID_CELL_CHANGE, self.GridBodyOnChanged)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(3)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        #self.DefTotal(3)
    
    #===========================================================================
    # def DefTotal(self, col=1):
    #     self.AddTotalsRow(col, 'Totali',[RSACC_SALDO,])
    #===========================================================================
    
    def OnCellSelected(self, event):
        event.Skip()
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        rs = self.data
        if row<len(rs):
            fgcol, bgcol = self.colors[rs[row][RSACC_COLORS]]
            attr.SetTextColour(fgcol)
            attr.SetBackgroundColour(bgcol)
            attr.SetReadOnly(True)
        return attr
    
    def ChangeData(self, rs):
        self.data = rs
        dbglib.DbGrid.ChangeData(self, rs)


# ------------------------------------------------------------------------------


class AccorpaPanel(wx.Panel):
    """
    Pannello gestione Effetti.
    """
    
    def __init__(self, *args, **kwargs):
        
        pdc = adb.DbTable(bt.TABNAME_PDC, 'pdc', writable=False)
        pdc.AddJoin(bt.TABNAME_PDCTIP, 'tipana', idLeft='id_tipo', idRight='id')
        pcf = pdc.AddJoin(bt.TABNAME_PCF, 'pcf', idLeft='id', idRight='id_pdc')
        pcf.AddJoin(bt.TABNAME_MODPAG, 'modpag')
        pdc.AddGroupOn('pdc.id')
        pdc.AddTotalOf('pcf.imptot-pcf.imppar', 'saldo')
        pdc.AddCountOf('pcf.id', 'partite')
        pdc.AddHaving('count_partite>1')
        pdc.AddOrder('pdc.descriz')
        pdc.Get(-1)
        
        pcf = dbc.Pcf()
        pcf.ClearOrders()
        #ordino x cliente x puntamento immediato alle sue partite
        pcf.AddOrder('pcf.id_pdc')
        #ordino x data scadenza x evidenziare i gruppi di partite da accorpare
        pcf.AddOrder('pcf.datscad')
        #ordino x data/num documento x determinare la partita raccogliente :)
        pcf.AddOrder('pcf.datdoc')
        pcf.AddOrder('pcf.numdoc')
        pcf.Get(-1)
        
        self.dbpdc = pdc
        self.dbpcf = pcf
        
        self.totacc = []
        self.totrac = {}
        self.wrirac = {}
        
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.AccorpaFunc(self)
        
        ci = lambda x: self.FindWindowById(x)
        self.gridpcf = PcfGrid(ci(wdr.ID_PANGRIDPCF), idGrid='accorpa')
        t = self.gridpcf.GetTable()
        t.totacc = self.totacc
        t.totrac = self.totrac
        
        ci(wdr.ID_CLIFOR).SetDataLink('clifor', 'CF')
        ci(wdr.ID_RIBA).SetDataLink('riba', 'SNA')
        
        self.Bind(wx.EVT_BUTTON,       self.OnUpdate,       id=wdr.ID_UPDATE)
        self.Bind(wx.EVT_BUTTON,       self.OnAccorpaDo,    id=wdr.ID_ACCORPA)
        self.Bind(wx.EVT_BUTTON,       self.OnAccorpaWrite, id=wdr.ID_WRITE)
        self.Bind(wx.EVT_LISTBOX,      self.OnPdcSelected,  id=wdr.ID_CLIENTI)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnPdcChecked,   id=wdr.ID_CLIENTI)
    
    def OnUpdate(self, event):
        self.UpdateData()
        event.Skip()

    def UpdateData(self):
        
        ci = lambda x: self.FindWindowById(x)
        
        pdc, pcf = self.dbpdc, self.dbpcf
        tabs = (pdc, pcf)
        
        map(lambda tab: tab.ClearBaseFilters(), tabs)
        
        #escludi partite saldate
        nos0 = ci(wdr.ID_NOPCFSALD).GetValue()
        if nos0:
            for tab in tabs:
                tab.AddBaseFilter("pcf.imptot<>pcf.imppar")
        
        #clienti/fornitori
        cf = ci(wdr.ID_CLIFOR).GetValue()
        pdc.AddBaseFilter("tipana.tipo='%s'" % cf)
        
        #riba?
        riba = ci(wdr.ID_RIBA).GetValue()
        if riba != "T":
            if riba == "S":
                op = '='
            else:
                op = '<>'
            pdc.AddBaseFilter("modpag.tipo%s'R'" % op)
            pcf.AddBaseFilter("modpag.tipo%s'R' OR pcf.riba=1" % op)
        
        #periodo
        d1, d2 = map(lambda x: ci(x).GetValue(), (wdr.ID_DATA1,
                                                  wdr.ID_DATA2))
        for dt, op in ((d1, '>='),
                       (d2, '<=')):
            for tab in tabs:
                if dt:
                    tab.AddBaseFilter("pcf.datscad%s%%s" % op, dt)
        
        #mostra solo le partite che hanno la stessa scadenza
        spm = ci(wdr.ID_SCADMULTI).GetValue()
        if spm:
            for tab in tabs:
                tab.AddBaseFilter("""
                (SELECT COUNT(*) 
                   FROM pcf AS test 
                  WHERE test.id_pdc=pdc.id AND test.datscad=pcf.datscad)>1""")
        
        wait = awu.WaitDialog(self)
        try:
            if not pdc.Retrieve():
                awu.MsgDialog(self, message=repr(pdc.GetError()))
                return
            if pdc.RowsCount() == 0:
                wait.Destroy()
                awu.MsgDialog(self, message="Nessuna partita trovata")
                return
            col = pdc._GetFieldIndex('id')
            rs = pdc.GetRecordset()
            pdcids = [rs[n][col] for n in range(pdc.RowsCount())]
            if not pcf.Retrieve("pcf.id_pdc IN (%s)" % ','.join(map(str, pdcids))):
                wait.Destroy()
                awu.MsgDialog(self, message=repr(pcf.GetError()))
                return
        finally:
            wait.Destroy()
        
        lc = ci(wdr.ID_CLIENTI)
        lc.Clear()
        
        for pdc in pdc:
            lc.Append(pdc.descriz)
        
        self.gridpcf.ChangeData(())
        
        if pdc.RowsCount() == 0:
            self.gridpcf.ChangeData(())
            awu.MsgDialog(self, message="Nessuna scadenza da accorpare")
        else:
            lc.SetSelection(0)
        
        self.totrac.clear()
        self.wrirac.clear()
        del self.totacc[:]
        
        self.UpdatePcf()
        
        self.TestButton()
    
    def TestButton(self):
        self.FindWindowById(wdr.ID_WRITE).Enable(bool(self.wrirac))
    
    def OnPdcChecked(self, event):
        sel = event.GetSelection()
        lc = self.FindWindowById(wdr.ID_CLIENTI)
        def SetSelection():
            lc.SetSelection(sel)
            self.UpdatePcf(updateacc=True)
        wx.CallAfter(SetSelection)
        event.Skip()
    
    def OnPdcSelected(self, event):
        self.UpdatePcf()
        event.Skip()
    
    def UpdatePcf(self, updateacc=False):
        
        lc = self.FindWindowById(wdr.ID_CLIENTI)
        row = lc.GetSelection()
        pdc = self.dbpdc
        rs = []
        if row>=0 and pdc.MoveRow(row):
            
            pcf = self.dbpcf
            col = pcf._GetFieldIndex('id_pdc')
            if pcf.LocateRow(lambda rsrow: rsrow[RSACC_PDC_ID] == pdc.id):
                colors = 0
                lastscad = pcf.datscad
                while pcf.id_pdc == pdc.id:
                    if pcf.datscad != lastscad:
                        colors = 1-colors
                        lastscad = pcf.datscad
                    rs.append([pcf.id,             #RSACC_PCF_ID
                               pcf.pdc.id,         #RSACC_PDC_ID
                               0,                  #RSACC_ACCORPA
                               0,                  #RSACC_RACCOGLI
                               pcf.datscad,        #RSACC_DATSCAD
                               pcf.modpag.id,      #RSACC_MPA_ID
                               pcf.modpag.codice,  #RSACC_MPA_COD
                               pcf.modpag.descriz, #RSACC_MPA_DES
                               pcf.imptot,         #RSACC_IMPTOT
                               pcf.imppar,         #RSACC_IMPPAR
                               pcf.saldo,          #RSACC_SALDO
                               pcf.caus.id,        #RSACC_CAU_ID
                               pcf.caus.codice,    #RSACC_CAU_COD
                               pcf.caus.descriz,   #RSACC_CAU_DES
                               pcf.numdoc,         #RSACC_NUMDOC
                               pcf.datdoc,         #RSACC_DATDOC
                               colors])            #RSACC_COLORS
                    if not pcf.MoveNext():
                        break
                
                if updateacc:
                    chk = lc.IsChecked(pdc.RowNumber())
                    if chk:
                        lastcol = rs[0][RSACC_COLORS]
                        rsa = []
                        for r in rs:
                            if r[RSACC_COLORS] != lastcol:
                                self.UpdateAccorpamenti(rsa)
                                lastcol = r[RSACC_COLORS]
                                del rsa[:]
                            rsa.append(r)
                        if rsa:
                            self.UpdateAccorpamenti(rsa)
                    else:
                        ta, tr, wr = self.totacc, self.totrac, self.wrirac
                        for r in rs:
                            if r[RSACC_PCF_ID] in ta:
                                ta.pop(ta.index(r[RSACC_PCF_ID]))
                            if r[RSACC_PCF_ID] in tr:
                                del tr[r[RSACC_PCF_ID]]
                            if r[RSACC_PCF_ID] in wr:
                                del wr[r[RSACC_PCF_ID]]
                    self.TestButton()
        
        grid = self.gridpcf
        grid.ChangeData(rs)
    
    def UpdateAccorpamenti(self, rsa):
        #preimpostazione flag x accorpamento
        acc = []
        rac = None
        for r in rsa:
            if r[RSACC_SALDO]>0:
                rac = r[RSACC_PCF_ID]
        if rac is not None:
            for r in rsa:
                if r[RSACC_PCF_ID] != rac:
                    for lst in (acc, self.totacc):
                        if not r[RSACC_PCF_ID] in lst:
                            lst.append(r[RSACC_PCF_ID])
            self.totrac[rac] = acc
            self.wrirac[rac] = acc
    
    def OnAccorpaDo(self, event):
        self.AccorpaDo()
        #else:
            #self.AccorpaWrite()
        event.Skip()
    
    def AccorpaDo(self):
        
        pdc, pcf = self.dbpdc, self.dbpcf
        
        rsold = pcf.GetRecordset()
        colpcfid = pcf._GetFieldIndex('id')
        rsnew = []
        pdcids = []
        for rac, accs in self.totrac.iteritems():
            timp = tpar = 0
            for acc in accs:
                pcf.LocateRow(lambda r: r[colpcfid] == acc)
                timp += pcf.imptot
                tpar += pcf.imppar
                pcf.DeleteRow()
            pcf.LocateRow(lambda r: r[colpcfid] == rac)
            pcf.imptot += timp
            pcf.imppar += tpar
            pcf.saldo = pcf.imptot-pcf.imppar
        self.totrac.clear()
        del self.totacc[:]
        
        self.UpdatePcf()
        self.TestButton()
    
    def OnAccorpaWrite(self, event):
        if awu.MsgDialog(self, message="Confermi gli accorpamenti effettuati?",
                         style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            self.AccorpaWrite()
            event.Skip()
    
    def AccorpaWrite(self):
        accs = []
        accmap = {}
        for wr, wa in self.wrirac.iteritems():
            for acc in wa:
                accmap[acc] = wr
                accs.append(acc)
        scad = adb.DbTable(bt.TABNAME_CONTAB_S, 'scad', writable=True)
        if scad.Retrieve("id_pcf IN (%s)" % ','.join(map(str, accs))):
            for scad in scad:
                scad.id_pcf = accmap[scad.id_pcf]
        if not scad.Save():
            awu.MsgDialog(self, message="Problema in aggiornamento riferimenti\n%s" % repr(scad.GetError()))
            return
        if not self.dbpcf.Save():
            awu.MsgDialog(self, message="Problema in aggiornamento partite\n%s" % repr(scad.GetError()))
            return
        awu.MsgDialog(self, message="Scrittura accorpamenti terminata con successo.")


# ------------------------------------------------------------------------------


class AccorpaFrame(aw.Frame):
    """
    Frame Gestione Accorpamenti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AccorpaPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_WRITE)
    
    def OnClose(self, event):
        self.Close()


# ------------------------------------------------------------------------------


class AccorpaDialog(aw.Dialog):
    """
    Dialog Gestione Accorpamenti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AccorpaPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_WRITE)
    
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_ABORT)


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    
    class _testApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            Env.Azienda.DB.testdb()
            db = adb.DB()
            db.Connect()
            return True
    
    app = _testApp(True)
    app.MainLoop()
    Env.InitSettings()
    test = AccorpaDialog()
    test.ShowModal()
