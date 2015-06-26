#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/ctrcassa.py
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

import awc
import contab.dbtables as dbc
import contab.pdcint_wdr as wdr

from contab.pdcint import GridMastro as GridMas

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import report as rpt


FRAME_TITLE = "Controllo saldi cassa/banca"


class GridPdc(dbglib.DbGrid):
    
    def __init__(self, dbctr, *args, **kwargs):
        
        parent = args[0]
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size)
        
        self.dbctr = dbctr
        pdc = self.dbctr
        tpa = pdc.tipana
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        
        cols = (( 35, (cn(tpa, 'codice'),  "Tipo",       _STR, True)),
                ( 50, (cn(pdc, 'codice'),  "Cod.",       _STR, True)),
                (140, (cn(pdc, 'descriz'), "Sottoconto", _STR, True)),)
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        self._cols=cols
        canedit = False
        canins = False
        
        self.SetData(self.dbctr.GetRecordset(), colmap, canedit, canins)
        
        #def GridAttr(row, col, rscol, attr):
            #if row<len(self.rsscad):
                #if self.rsscad[row][RSGLOB_SALDO]<0:
                    #fgcol = stdcolor.GetColour("red")
                    #bgcol = stdcolor.GetColour("azure3")
                #else:
                    #fgcol = stdcolor.NORMAL_FOREGROUND
                    #bgcol = stdcolor.GetColour("bisque")
                #attr.SetTextColour(fgcol)
                #attr.SetBackgroundColour(bgcol)
            #return attr
        #self.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def UpdateGrid(self):
        self.ChangeData(self.dbctr.GetRecordset())


# ------------------------------------------------------------------------------


class GridSal(dbglib.DbGrid):
    
    def __init__(self, dbsal, *args, **kwargs):
        
        parent = args[0]
        size = parent.GetClientSizeTuple()
        
        self.dbsal = dbsal
        sal = self.dbsal
        reg = sal.reg
        cau = reg.caus
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        ncdat = cn(sal, 'giorno')
        nctod = cn(sal, 'total_dare')
        nctoa = cn(sal, 'total_avere')
        nctsd = cn(sal, 'total_saldo_dare')
        nctsa = cn(sal, 'total_saldo_avere')
        nctpd = cn(sal, 'total_progr_dare')
        nctpa = cn(sal, 'total_progr_avere')
        nctxd = cn(sal, 'total_saldoprogr_dare')
        nctxa = cn(sal, 'total_saldoprogr_avere')
        
        cols = (\
            ( 90, (ncdat, "Data reg.",     _STR, True)),
            (110, (nctsd, "Saldo Dare",    _IMP, True)),
            (110, (nctsa, "Saldo Avere",   _IMP, True)),
            (110, (nctxd, "Saldo P.Dare",  _IMP, True)),
            (110, (nctxa, "Saldo P.Avere", _IMP, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        class Registrazioni(dbglib.DbGridTable):
            def GetValue(self, row, col):
                if col == 0 and row<len(self.data):
                    d = self.data[row][self.rsColumns[col]]
                    if d is None:
                        if row == 0:
                            out = 'Riporto'
                        else:
                            out = ''
                    elif type(d) is Env.DateTime.Date:
                        #mysql 5.1 => mi arriva Date OK
                        out = dbc.adb.DbTable.dita(d)
                    elif type(d) in (str, unicode):
                        #mysql 5.0 => mi arriva stringa ?!?
                        out = '%s/%s/%s' % (d[8:10], d[5:7], d[:4])
                    else:
                        out = '???'
                else:
                    out = dbglib.DbGridTable.GetValue(self, row, col)
                return out
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size,
                               tableClass=Registrazioni)
        
        self.SetData([], colmap, canedit, canins)
        
        def GridAttr(row, col, rscol, attr):
            if col in (0,4) and row<self.dbsal.RowsCount():
                if row != self.dbsal.RowNumber():
                    self.dbsal.MoveRow(row)
                if self.dbsal.total_progr_avere>self.dbsal.total_progr_dare:
                    fgcol = stdcolor.GetColour("red")
                else:
                    fgcol = stdcolor.NORMAL_FOREGROUND
                attr.SetTextColour(fgcol)
            return attr
        self.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def UpdateGrid(self):
        wx.BeginBusyCursor()
        self.dbsal.CalcProgr()
        wx.EndBusyCursor()
        self.ChangeData(self.dbsal.GetRecordset())


# ------------------------------------------------------------------------------


class CtrCassaPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.dbctr = dbc.PdcSaldiGiornalieri()
        
        wdr.CtrCassaFunc(self)
        
        cbn = lambda x: self.FindWindowByName(x)
        cbi = lambda x: self.FindWindowById(x)
        
        cbi(wdr.ID_CSCMAINZONE).SetSashPosition(260)
        cbi(wdr.ID_CSCDETZONE).SetSashPosition(360)
        cbi(wdr.ID_CSCDETZONE).SetSashGravity(0.6)
        
        self.gridpdc = GridPdc(self.dbctr,     cbi(wdr.ID_CSCGRIDPDC))
        self.gridsal = GridSal(self.dbctr.mov, cbi(wdr.ID_CSCGRIDSAL))
        self.gridmas = GridMas(cbi(wdr.ID_CSCGRIDREG))
        
        def OnGridPdcSelected(event):
            row = event.GetRow()
            if row<self.dbctr.RowsCount():
                wx.BeginBusyCursor()
                self.dbctr.MoveRow(row)
                wx.EndBusyCursor()
                self.gridsal.UpdateGrid()
            event.Skip()
        self.gridpdc.Bind(gl.EVT_GRID_SELECT_CELL, OnGridPdcSelected)
        
        def OnGridSalSelected(event):
            row = event.GetRow()
            if row<self.dbctr.mov.RowsCount():
                db = self.gridmas.dbmas
                mov = self.dbctr.mov
                mov.MoveRow(row)
                if mov.giorno is None:
                    d1 = None
                    d2 = self.FindWindowByName('cscdatini').GetValue()
                    if d2: d2 -= 1
                else:
                    d1 = d2 = mov.reg.datreg
                db.ClearMovFilters()
                db.SetDateStart(d1)
                db.SetDateEnd(d2)
                wx.BeginBusyCursor()
                db.Get(self.dbctr.id)
                wx.EndBusyCursor()
                self.gridmas.UpdateGrid()
            event.Skip()
        self.gridsal.Bind(gl.EVT_GRID_SELECT_CELL, OnGridSalSelected)
        
        for cid, func in ((wdr.ID_BUTUPD,   self.OnUpdateFilters),
                          (wdr.ID_BUTPRINT, self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
    
    def OnPrint(self, event):
        self.dbctr.mov.MoveFirst()
        rpt.Report(self, self.dbctr, 'Controllo saldi giornalieri', 
                   noMove=True, exitOnGroup=True)
        wx.BeginBusyCursor()
        self.dbctr.mov.CalcProgr()
        wx.EndBusyCursor()
        event.Skip()
    
    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        self.UpdateGridPdc()
        self.gridpdc.SelectRow(0)
        event.Skip()
        
    def UpdateFilters(self):
        
        pdc = self.dbctr
        pdc.ClearFilters()
        pdc.AddFilter("tipana.tipo IN ('A','B')")
        
        mov = pdc.mov
        reg = mov.reg
        #mov.ClearFilters()
        #for name, tab, field, op in (\
            #('cscdatini', reg, 'datreg', '>='),\
            #('cscdatfin', reg, 'datreg', '<='),\
            #):
            #val = self.FindWindowByName(name).GetValue()
            #if val:
                #mov.AddFilter('%s.%s%s%%s'\
                              #% (tab.GetTableAlias(), field, op), val)
        cn = lambda x: self.FindWindowByName(x)
        grp = mov._info.group.groups[0]
        data1, data2 = [cn(x).GetValue() for x in ('cscdatini', 'cscdatfin')]
        if data1:
            g = "IF(reg.datreg<'%s',NULL,reg.datreg)" \
              % data1.Format("%Y-%m-%d")
        else:
            g = "IF(FALSE,NULL,reg.datreg)"
        mov.ChangeGroupExpression('giorno', g)
        mov.ClearFilters()
        if data2:
            mov.AddFilter(r"reg.datreg<=%s", data2)
        pdc._info.data1, pdc._info.data2 = data1, data2
        wx.BeginBusyCursor()
        pdc.Retrieve()
        wx.EndBusyCursor()
    

    
    def UpdateGridPdc(self):
        db = self.dbctr
        self.dbGridPdc = db 
        wx.BeginBusyCursor()
        do = db.Retrieve()
        wx.EndBusyCursor()
        if not do:
            awc.util.MsgDialog(self,\
                               "Problema in lettura dati:\n\n%s"\
                               % repr(db.GetError()))
        self.gridpdc.UpdateGrid()
        #self.UpdateTotals()


# ------------------------------------------------------------------------------


class CtrCassaFrame(aw.Frame):
    """
    Frame Controllo saldo cassa/banca.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(CtrCassaPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class CtrCassaDialog(aw.Dialog):
    """
    Dialog Controllo saldo cassa/banca.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(CtrCassaPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    import Env
    Env.InitSettings()
    db = dbc.adb.DB()
    db.Connect()
    win = CtrCassaDialog()
    win.Show()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
