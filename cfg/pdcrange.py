#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/pdcrange.py
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

import cfg.pdcrange_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab
bc = Azienda.Colours

import stormdb as adb

FRAME_TITLE = "Range sottoconti"


class PdcRangeGrid(dbglib.DbGrid):
    
    def __init__(self, parent, dbr):
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), style=0)
        self.dbr = dbr
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _VAL = gl.GRID_VALUE_FLOAT+":5,0"
        
        cols = (\
            ( 50, (cn(dbr, "codice"),    "Cod.",   _STR, True )),\
            ( 80, (cn(dbr, "descriz"),   "Range",  _STR, True )),\
            ( 60, (cn(dbr, "rangemin"),  "Min.",   _VAL, False)),\
            ( 60, (cn(dbr, "rangemax"),  "Max.",   _VAL, False)),\
            ( 50, (cn(dbr, "id"),        "range#", _STR, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = True
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1,\
                       self.EditedValues), )
        
        self.SetData(dbr.GetRecordset(), colmap, canedit, canins,
                     newRowFunc=self.AddNewRow, afterEdit=afteredit)
        
        self._bgcol1, self._bgcol2 = [bc.GetColour(c) for c in ("lavender",
                                                                "aliceblue")]
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
        
        #self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallProd)
    
    def AddNewRow(self):
        dbr = self.dbr
        dbr.MoveNewRow()
        dbr.AppendNewRow()
    
    def EditedValues(self, row, gridcol, col, value):
        self.dbr.MoveRow(row)
        if self.dbr.id is not None:
            if not row in self.dbr._info.modifiedRecords:
                self.dbr._info.modifiedRecords.append(self.dbr.id)
        return
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        readonly = col > 3
        attr.SetReadOnly(readonly)
        
        if row%2 == 0:
            bgcol = self._bgcol2
        else:
            bgcol = self._bgcol1
        
        #attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        
        return attr


# ------------------------------------------------------------------------------


    
class PdcRangePanel(aw.Panel):
    """
    Gestione tabella Range sottoconti.
    """
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.PdcRangeFunc(self)
        self.dbr = adb.DbTable(bt.TABNAME_PDCRANGE, 'pr', writable=True)
        self.dbr.AddOrder('rangemin')
        self.dbr.Retrieve()
        cid = lambda x: self.FindWindowById(x)
        self.grid = PdcRangeGrid(cid(wdr.ID_PANGRID), self.dbr)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def OnSave(self, event):
        if not self.dbr.Save():
            aw.awu.MsgDialog(self, message=repr(self.dbr.GetError()))
        else:
            self.dbr.Retrieve()
            self.grid.ResetView()


# ------------------------------------------------------------------------------


class PcdRangeFrame(aw.Frame):
    """
    Frame Gestione tabella Range sottoconti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(PdcRangePanel(self, -1))


# ---------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = PdcRangeDialog()
    win.Show()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    import stormdb as adb
    db = adb.DB()
    db.Connect()
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
