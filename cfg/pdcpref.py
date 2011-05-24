#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/pdcpref.py
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

from cfg.dbtables import PdcPrefTable

import awc
import awc.util as awu

import awc.controls.linktable as ltlib
import awc.controls.dbgrid as dbglib

import cfg.pdcpref_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab


class PdcPrefGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbpcp):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1,
                                              size=parent.GetClientSizeTuple())
        
        self.dbpcp = dbpcp
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        pcp = self.dbpcp
        pdc = pcp.pdc
        
        cols = self.DefColumns()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = canins = True
        
        import anag.lib as lib
        links = []
        ltpdc = lib.LinkTabPdcAttr(bt.TABNAME_PDC,     #table
                                   0,                  #grid col per codice
                                   cn(pcp, 'id_pdc'),  #rs col id
                                   cn(pdc, 'codice'),  #rs col cod
                                   cn(pdc, 'descriz'), #rs col des
                                   refresh = True)
        links.append(ltpdc)
        
        afteredit = ( (dbglib.CELLEDIT_BEFORE_UPDATE, -1, self.TestEditedValues), )
        
        #afteredit = dbglib.AfterEditAttr()
        #afteredit.SetAfterMemoCallback(0, 
                       #lambda *x: self.parent.SetDataChanged() )
        
        self.SetData(dbpcp.GetRecordset(), colmap, canedit, canins,
                      links, afteredit, self.OnNewRow)
        
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
        raise Exception, "Classe non istanziabile"
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        raise Exception, "Classe non istanziabile"
    
    def OnNewRow(self):
        pcp = self.dbpcp
        pcp.CreateNewRow()
    
    def TestEditedValues(self, row, gridcol, col, value):
        if gridcol == 2:
            if not (value is None or value in 'DA'):
                awu.MsgDialog(self, 'Segno contabile errato')
                return False
            pcp = self.dbpcp
            pcp.MoveRow(row)
            pcp.segno = value
        self.ResetView()
        return True


# ------------------------------------------------------------------------------


class PdcPrefCauGrid(PdcPrefGrid):
    
    def DefColumns(self):
        
        _STR = gl.GRID_VALUE_STRING
        
        pcp = self.dbpcp
        pdc = pcp.pdc
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        return (( 50, (cn(pdc, "codice"),  "Cod.",        _STR, True)),
                (300, (cn(pdc, "descriz"), "Sottocontro", _STR, True)),
                ( 35, (cn(pcp, "segno"),   "D/A",         _STR, True)),
                (  1, (cn(pcp, "id"),      "#pcp",        _STR, True)),
                (  1, (cn(pdc, "id"),      "#pdc",        _STR, True)),
            )
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly(not col in (0, 2))
        return attr


# ------------------------------------------------------------------------------


class PdcPrefPanel(wx.Panel):
    
    _ambito = None
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, *args, **kwargs)
        wdr.PdcPrefPanelFunc(self)
        
        self.dbpcp = PdcPrefTable()
        
        self.CreateGrid()
        
        def cn(x):
            return self.FindWindowByName(x)
        
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellChanged)
        
        for name, func in (('butmoveup',   self.OnMoveUp),
                           ('butmovedown', self.OnMoveDown),
                           ('butdelete',   self.OnDelPref)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def CreateGrid(self):
        raise Exception, "Classe non istanziabile"
    
    def OnCellChanged(self, event):
        self.UpdateMoveButtonsState(event.GetRow())
        event.Skip()
    
    def SetAmbito(self, a):
        self._ambito = a
    
    def OnMoveUp(self, event):
        self._MoveRow(-1)
    
    def OnMoveDown(self, event):
        self._MoveRow(1)
    
    def _MoveRow(self, direction):
        grid = self._grid_pref
        pcp = self.dbpcp
        rowold = grid.GetSelectedRows()[0]
        rownew = rowold+direction
        if rownew >= 0 and rownew <= pcp.RowsCount():
            rs = pcp.GetRecordset()
            rs[rowold], rs[rownew] = rs[rownew], rs[rowold]
            grid.SetGridCursor(rownew, 0)
            grid.Refresh()
            self.UpdateMoveButtonsState(rownew)
            self.SetDataChanged()
    
    def OnDelPref(self, event):
        grid = self._grid_pref
        pcp = self.dbpcp
        row = grid.GetSelectedRows()[0]
        if 0 <= row < pcp.RowsCount():
            pcp.MoveRow(row)
            if pcp.id is not None:
                if not pcp.id in pcp._info.deletedRecords:
                    pcp._info.deletedRecords.append(pcp.id)
            pcp._info.recordCount -= 1
            grid.DeleteRows(row)
            self.SetDataChanged()

    def UpdateMoveButtonsState(self, rowcur=None):
        grid = self._grid_pref
        pcp = self.dbpcp
        if rowcur is None:
            rowcur = self._grid_pref.GetSelectedRows()[0]
        rowmax = pcp.RowsCount()
        def cn(x):
            return self.FindWindowByName(x)
        btnup, btndn, btndel = map(cn, 'butmoveup butmovedown butdelete'.split())
        enable = not pcp.IsEmpty()
        btnup.Enable(enable and rowmax > rowcur > 0)
        btndn.Enable(enable and rowcur < rowmax-1)
        btndel.Enable(enable and rowmax > rowcur >= 0)
    
    def SetDataChanged(self):
        parent = self.GetParent()
        while parent is not None:
            if hasattr(parent, 'SetDataChanged'):
                parent.SetDataChanged()
                break
            parent = parent.GetParent()

    def UpdateDataControls(self, db_recid):
        if db_recid is None: return
        self.db_recid = db_recid
        pref = self.dbpcp
        pref.ClearFilters()
        pref.AddFilter('pcp.ambito=%s', self._ambito)
        pref.AddFilter('pcp.key_id=%s', db_recid)
        pref.Retrieve()
        self._grid_pref.ChangeData(pref.GetRecordset())
        self.UpdateMoveButtonsState(0)
    
    def TransferDataFromWindow(self, db_recid):
        pcp = self.dbpcp
        for n, pcp in enumerate(pcp):
            pcp.ambito = self._ambito
            pcp.key_id = db_recid
            pcp.pdcord = n
        return pcp.Save()


# ------------------------------------------------------------------------------


class PdcPrefCauPanel(PdcPrefPanel):
    
    _ambito = 1
    
    def CreateGrid(self):
        def cn(x):
            return self.FindWindowByName(x)
        self._grid_pref = PdcPrefCauGrid(cn('pangridpref'), self.dbpcp)


# ------------------------------------------------------------------------------


class PdcPrefFornitGrid(PdcPrefGrid):
    
    def DefColumns(self):
        
        _STR = gl.GRID_VALUE_STRING
        
        pcp = self.dbpcp
        pdc = pcp.pdc
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        return (( 50, (cn(pdc, "codice"),  "Cod.",        _STR, True)),
                (300, (cn(pdc, "descriz"), "Sottocontro", _STR, True)),
                (  1, (cn(pcp, "id"),      "#pcp",        _STR, True)),
                (  1, (cn(pdc, "id"),      "#pdc",        _STR, True)),
            )
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly(col != 0)
        return attr


# ------------------------------------------------------------------------------


class PdcPrefFornitPanel(PdcPrefPanel):
    
    _ambito = 2
    
    def CreateGrid(self):
        def cn(x):
            return self.FindWindowByName(x)
        self._grid_pref = PdcPrefFornitGrid(cn('pangridpref'), self.dbpcp)
