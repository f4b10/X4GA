#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         contab/alleg.py
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
from mx import DateTime

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import awc
import awc.controls.windows as aw
from awc.util import MsgDialog, MsgDialogDbError, DictNamedChildrens
import awc.controls.dbgrid as dbglib

import contab.dbtables as dbc
adb = dbc.adb
dba = dbc.dba

import contab.alleg_wdr as wdr

import report as rpt


FRAME_TITLE_ALLEG = "Allegati Clienti/Fornitori"


"""
Allegati Clienti/Fornitori
"""

class AllegatiGrid(dbglib.DbGrid):
    """
    Griglia allegati
    """
    def __init__(self, parent):
        
        dbglib.DbGrid.__init__(self, parent, -1, 
                               size=parent.GetClientSizeTuple())
        
        _STR = gl.GRID_VALUE_STRING
        _FLV = bt.GetValIntMaskInfo()
        
        db = dbc.AllegatiCliFor('C')
        cn = lambda col: db._GetFieldIndex(col, inline=True)
        
        cols = (( 40, (cn("codice"),       "Cod.",           _STR, True )),\
                (150, (cn("descriz"),      "Rag.Sociale",    _STR, True )),\
                (110, (cn("total_pralc1"), "Imponibile",     _FLV, True )),\
                (110, (cn("total_pralc2"), "Imposta",        _FLV, True )),\
                (110, (cn("total_pralc3"), "Non Imponibile", _FLV, True )),\
                (110, (cn("total_pralc4"), "Esente",         _FLV, True )),\
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData((), colmap, canedit, canins)
        
        self._bgcol1, self._bgcol2 = [bc.GetColour(c) for c in ("lavender",
                                                                "aliceblue")]
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AddTotalsRow(1, 'Totali:', (cn("total_pralc1"),
                                         cn("total_pralc2"),
                                         cn("total_pralc3"),
                                         cn("total_pralc4")))
        self.testcol = cn("total_pralc1")
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr.SetReadOnly(True)
        rs = self.GetTable().data
        bgcol = bc.GetColour('white')
        if row<len(rs):
            if self.IsOnTotalRow(row):
                bgcol = bc.GetColour('green')
            else:
                bgcol = self._bgcol2
                for val in rs[row][self.testcol:self.testcol+4]:
                    if val<0:
                        bgcol = self._bgcol1
                        break
        attr.SetBackgroundColour(bgcol)
        return attr


# ------------------------------------------------------------------------------


class DettaglioRigheIvaGrid(dbglib.DbGrid):
    """
    Griglia righe iva di un cliente/fornitore
    """
    def __init__(self, parent, pdcid, data1, data2):
        
        dbglib.DbGrid.__init__(self, parent, -1, 
                               size=parent.GetClientSizeTuple())
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _FLV = bt.GetValIntMaskInfo()
        
        pdc = dba.Pdc()
        if pdc.Get(pdcid) and pdc.RowsCount() == 1:
            clifor = pdc.tipana.tipo
        else:
            clifor = 'C'
        rig = dbc.AllegatiRigheIva(clifor)
        rig.AddFilter('reg.datreg>=%s AND reg.datreg<=%s', data1, data2)
        rig.AddFilter('movcf.id_pdcpa=%s', pdcid)
        rig.Retrieve()
        reg = rig.reg
        cau = reg.caus
        riv = reg.regiva
        mov = rig.moviva
        alq = mov.aliqiva
        
        cn = lambda tab, col: tab._GetFieldIndex(col, inline=True)
        
        cols = ((100, (cn(reg, 'datreg'),  "Data Reg.",      _DAT, True )),\
                ( 30, (cn(cau, 'codice'),  "Cod.",           _STR, True )),\
                (150, (cn(cau, 'descriz'), "Causale",        _STR, True )),\
                ( 50, (cn(reg, 'numdoc'),  "Num.Doc.",       _STR, True )),\
                (100, (cn(reg, 'datdoc'),  "Data Doc.",      _DAT, True )),\
                (110, (cn(rig, 'pralc1'),  "Imponibile",     _FLV, True )),\
                (110, (cn(rig, 'pralc2'),  "Imposta",        _FLV, True )),\
                (110, (cn(rig, 'pralc3'),  "Non Imponibile", _FLV, True )),\
                (110, (cn(rig, 'pralc4'),  "Esente",         _FLV, True )),\
                ( 30, (cn(riv, 'codice'),  "Cod.",           _STR, True )),\
                (150, (cn(riv, 'descriz'), "Registro",       _STR, True )),\
                ( 30, (cn(alq, 'codice'),  "Cod.",           _STR, True )),\
                (150, (cn(alq, 'descriz'), "Aliquota",       _STR, True )),\
                (110, (cn(mov, 'imponib'), "Imponibile",     _FLV, True )),\
                (110, (cn(mov, 'imposta'), "Imposta",        _FLV, True )),\
                ( 40, (cn(rig, 'id'),      "#mov",           _STR, True )),\
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(rig.GetRecordset(), colmap, canedit, canins)
        
        self._bgcol1, self._bgcol2 = [bc.GetColour(c) for c in ("lavender",
                                                                "aliceblue")]
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AddTotalsRow(4, 'Totali:', (cn(rig, "pralc1"),
                                         cn(rig, "pralc2"),
                                         cn(rig, "pralc3"),
                                         cn(rig, "pralc4"),
                                         cn(rig, "importo"),
                                         cn(rig, "imposta")))
        self.testcol = cn(rig, "pralc1")
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr.SetReadOnly(True)
        rs = self.GetTable().data
        bgcol = bc.GetColour('white')
        if row<len(rs):
            fgcol = bc.NORMAL_FOREGROUND
            if self.IsOnTotalRow(row):
                bgcol = bc.GetColour('green')
            else:
                bgcol = self._bgcol2
                for val in rs[row][self.testcol:self.testcol+4]:
                    if val<0:
                        bgcol = self._bgcol1
                        break
            if 5 <= col <= 8:
                fgcol = bc.GetColour('blue')
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        return attr


# ------------------------------------------------------------------------------


class DettaglioRigheIvaDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Dettaglio righe IVA'
        aw.Dialog.__init__(self, *args, **kwargs)
        p = aw.Panel(self, -1)
        wdr.DettaglioRigheIvaFunc(p)
        self.AddSizedPanel(p)
        self.CenterOnScreen()
    
    def SetParams(self, pdcid, data1, data2):
        p = self.FindWindowById(wdr.ID_PANELGRID)
        self.gridrighe = DettaglioRigheIvaGrid(p, pdcid, data1, data2)


# ------------------------------------------------------------------------------


class AllegatiPanel(aw.Panel):
    """
    Pannello allegati clienti/fornitori
    """
    dball = None
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.AllegatiPanelFunc(self)
        self.gridall = AllegatiGrid(self.FindWindowById(wdr.ID_PANELGRID))
        
        datelab = Env.Azienda.Esercizio.dataElab
        d1 = DateTime.Date(datelab.year,1,1)
        d2 = DateTime.Date(datelab.year,12,31)
        for cid, val in ((wdr.ID_DATA1, d1),
                         (wdr.ID_DATA2, d2)):
            self.FindWindowById(cid).SetValue(val)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDClick, self.gridall)
        for cid, func in ((wdr.ID_UPDATE, self.OnUpdate),
                          (wdr.ID_PRINT,  self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
    
    def OnDClick(self, event):
        row = event.GetRow()
        dlg = DettaglioRigheIvaDialog(self, -1)
        self.dball.MoveRow(row)
        dlg.SetParams(self.dball.id, 
                      self.FindWindowById(wdr.ID_DATA1).GetValue(),
                      self.FindWindowById(wdr.ID_DATA2).GetValue())
        dlg.ShowModal()
        dlg.Destroy()
        event.Skip()
    
    def OnUpdate(self, event):
        if not self.Validate():
            aw.awu.MsgDialog(self, message="Date non valide")
            return
        self.UpdateGrid()
        event.Skip()
    
    def UpdateGrid(self):
        ci = lambda x: self.FindWindowById(x)
        db = dbc.AllegatiCliFor('CF'[ci(wdr.ID_CLIFOR).GetSelection()])
        db.SetDate(ci(wdr.ID_DATA1).GetValue(),
                   ci(wdr.ID_DATA2).GetValue())
        if ci(wdr.ID_SOLOALL).GetValue():
            db.AddFilter('anag.allegcf=1')
        wx.BeginBusyCursor()
        do = db.Retrieve()
        wx.EndBusyCursor()
        ci(wdr.ID_PRINT).Enable(db.RowsCount()>0)
        self.dball = db
        if do:
            self.gridall.ChangeData(db.GetRecordset())
        else:
            aw.awu.MsgDialog(self, message=repr(db.GetError()))
    
    def Validate(self):
        return not None in [self.FindWindowById(x).GetValue() 
                            for x in (wdr.ID_DATA1, wdr.ID_DATA2)]
    
    def OnPrint(self, event):
        name = 'Allegati '
        if self.dball._info.clifor == 'c':
            name += 'Clienti'
        else:
            name += 'Fornitori'
        rpt.Report(self, self.dball, name)
        event.Skip()


# ------------------------------------------------------------------------------


class AllegatiFrame(aw.Frame):
    """
    Dialog allegati clienti/fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_ALLEG
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AllegatiPanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = AllegatiFrame(None, -1)
    win.Show()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
