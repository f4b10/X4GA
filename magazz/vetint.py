#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/vetint.py
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

import anag.trasp_wdr as wdr
import anag.trasp as trasp

import magazz.dbtables as dbm

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLEVET = "Interrogazione Vettori"


class TraVetIntDocGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbdoc):
        
        self.dbdoc = doc = dbdoc
        
        class TraVetIntDocGridTable(dbglib.DbGridTable):
            
            def GetDataValue(tself, row, col, gridcols=False):
                
                out = None
                
                try:
                    
                    doc = self.dbdoc
                    
                    if col == self.COL_spedind:
                        if doc.RowNumber() != row:
                            doc.MoveRow(row)
                        out = doc.GetSpedIndirizzo()
                        
                    elif col == self.COL_spedcap: 
                        if doc.RowNumber() != row:
                            doc.MoveRow(row)
                        out = doc.GetSpedCAP()
                        
                    elif col == self.COL_spedcit: 
                        if doc.RowNumber() != row:
                            doc.MoveRow(row)
                        out = doc.GetSpedCitta()
                        
                    elif col == self.COL_spedprv: 
                        if doc.RowNumber() != row:
                            doc.MoveRow(row)
                        out = doc.GetSpedProv()
                    
                except:
                    pass
                    
                if out is None:
                    out = dbglib.DbGridTable.GetDataValue(tself, row, col, gridcols)
                
                return out
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              tableClass=TraVetIntDocGridTable)
        
        cols = self.DefColumns()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(doc.GetRecordset(), colmap, canEdit=False, canIns=False)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(6)
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
        
        doc = self.dbdoc
        mag = doc.magazz
        tpd = doc.tipdoc
        pdc = doc.pdc
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _COL = gl.GRID_VALUE_NUMBER+":5"
        _PES = gl.GRID_VALUE_FLOAT+":7,3"
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()
        
        cols = []
        self.edcols = []
        
        def v(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                self.edcols.append(n)
            return n
        def e(x):
            return v(x, True)
        
        self.COL_magcod =    v(( 35, (cn(mag, "codice"),     "Mag.",               _STR, True)))
        self.COL_tpdcod =    v(( 35, (cn(tpd, "codice"),     "Cod.",               _STR, True)))
        self.COL_tpddes =    v((100, (cn(tpd, "descriz"),    "Causale",            _STR, True)))
        self.COL_NUMDOC =    v(( 50, (cn(doc, "numdoc"),     "Num.",               _STR, True)))
        self.COL_DATDOC =    v(( 80, (cn(doc, "datdoc"),     "Data doc.",          _DAT, True)))
        self.COL_pdccod =    v(( 50, (cn(pdc, "codice"),     "Cod.",               _STR, True)))
        self.COL_pdcdes =    v((200, (cn(pdc, "descriz"),    "Anagrafica",         _STR, True)))
        self.COL_TOTCOLLI =  v(( 60, (cn(doc, "totcolli"),   "Colli",              _COL, True)))
        self.COL_TOTPESO =   v(( 80, (cn(doc, "totpeso"),    "Peso KG",            _PES, True)))
        self.COL_TOTDOC =    v((110, (cn(doc, "totimporto"), "Tot.Documento",      _IMP, True)))
        self.COL_spedind =   v((200, (0,                     "Indirizzo",          _STR, True)))
        self.COL_spedcap =   v(( 50, (0,                     "CAP",                _STR, True)))
        self.COL_spedcit =   v((200, (0,                     "Città",              _STR, True)))
        self.COL_spedprv =   v(( 40, (0,                     "Prov",               _STR, True)))
        self.COL_ID =        v((  1, (cn(doc, "id"),         "#doc",               _STR, True)))
        
        return cols

        
# ------------------------------------------------------------------------------


class TraVetIntDocPanel(wx.Panel):
    
    id_travet = None
    def SetTraVet(self, v):
        self.id_travet = v
        self.UpdateData()
    def GetTraVet(self):
        return self.id_travet
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.TraVetCardInterFunc(self)
        cn = self.FindWindowByName
        d2 = Env.Azienda.Login.dataElab
        d1 = Env.DateTime.Date(d2.year, d2.month, 1)
        cn('data1').SetValue(d1)
        cn('data2').SetValue(d2)
        self.dbdoc = dbm.TraVetDocs()
        self.gridoc = TraVetIntDocGrid(cn('pangridoc'), self.dbdoc)
        for name, func in (('butupdate', self.OnUpdateData),
                           ('butprint',  self.OnPrintLista),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        cn = self.FindWindowByName
        doc = self.dbdoc
        if self.id_travet:
            doc.ClearFilters()
            doc.AddFilter('doc.id_travet=%s', self.id_travet)
            td, d1, d2 = map(lambda x: cn(x).GetValue(), 'id_tipdoc data1 data2'.split())
            if td:
                doc.AddFilter('doc.id_tipdoc=%s', td)
            if d1:
                doc.AddFilter('doc.datdoc>=%s', d1)
            if d2:
                doc.AddFilter('doc.datdoc<=%s', d2)
            wx.BeginBusyCursor()
            try:
                doc.Retrieve()
            finally:
                wx.EndBusyCursor()
        else:
            doc.Reset()
        self.gridoc.ChangeData(doc.GetRecordset())
        cn('numdocs').SetValue(doc.RowsCount())
        tc, tp = doc.GetTotalOf('totcolli totpeso'.split())
        for name, val in (('totcolli', tc),
                          ('totpeso', tp),):
            cn(name).SetValue(val)
            doc.SetPrintValue(name, val)
    
    def OnPrintLista(self, event):
        self.PrintLista()
        event.Skip()
    
    def PrintLista(self):
        cn = self.FindWindowByName
        doc = self.dbdoc
        doc.SetPrintValue('codvet', doc.travet.codice)
        doc.SetPrintValue('desvet', doc.travet.descriz)
        rpt.Report(self, doc, 'Spedizioni del vettore')


# ------------------------------------------------------------------------------


class TraVetIntPanel(trasp.TraVetPanel):
    
    def InitAnagCard(self, parent):
        a = trasp.TraVetPanel.InitAnagCard(self, parent)
        nb = a.FindWindowByName('workzone')
        self.pandocs = TraVetIntDocPanel(nb)
        nb.AddPage(self.pandocs, 'Documenti')
        return a
    
    def UpdateDataControls(self, *args, **kwargs):
        out = trasp.TraVetPanel.UpdateDataControls(self, *args, **kwargs)
        self.pandocs.SetTraVet(self.db_recid)
        return out


# ------------------------------------------------------------------------------


class TraVetIntFrame(trasp.ga._AnagFrame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEVET
        trasp.ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraVetIntPanel(self, -1))
        self.CenterOnScreen()
