#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/quadpcfcont.py
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

import awc
import awc.controls.windows as aw

import contab.dbtables as dbc
import contab.pdcint_wdr as wdr

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import contab
import anag.util as autil
import stormdb as adb

import report as rpt
import copy


FRAME_TITLE = "Quadratura scadenzari-mastri"

#todo: implementare join su subdbtable
#vedi: contab.dbtables.PdcQuadPcfCont

class PdcQuadPcfContGrid(dbglib.DbGrid):
    
    def __init__(self, parent, dbdif):
        
        dbglib.DbGrid.__init__(self, parent, -1, 
                               size=parent.GetClientSizeTuple())
        
        self.dbdif = dbdif
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 50, (cn(dbdif, 'pdc_codice'),  "Cod.",          _STR, True)),\
            (220, (cn(dbdif, 'pdc_descriz'), "Anagrafica",    _STR, True)),\
            (110, (cn(dbdif, 'saldocont'),   "Saldo Mastro",  _IMP, True)),\
            (110, (cn(dbdif, 'saldopcf'),    "Saldo Partite", _IMP, True)),\
            (  1, (cn(dbdif, 'pdc_id'),      "#pdc",          _STR, True)),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = dbdif.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
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


class PdcQuadPcfContPanel(aw.Panel):
    interrpdc = None
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.dbdif = dbc.PdcQuadPcfCont()
        
        wdr.PdcQuadPcfContFunc(self)
        
        ci = lambda x: self.FindWindowById(x)
        ci(wdr.ID_CTRQUADCF).SetDataLink('clifor', ('CF'))
        ci(wdr.ID_CTRQUADCF).SetValue('C')
        
        self.gridif = PdcQuadPcfContGrid(ci(wdr.ID_CTRPANDIFF), self.dbdif)
        
        self.tipicf = {'C': [],
                       'F': []}
        tipana = adb.DbTable(bt.TABNAME_PDCTIP, 'tipana', writable=False)
        for tipo in 'CF':
            if tipana.Retrieve('tipana.tipo=%s', tipo):
                self.tipicf[tipo] = [t.id for t in tipana]
            else:
                raise Exception, repr(tipana.GetError())
            if len(self.tipicf['C']) == 0:
                raise Exception, "Tipi anagrafici mancanti per tipo %s" % tipo
        del tipana
        self.SetCliForFilters()
        
        for cid, func in ((wdr.ID_BTNUPD, self.OnUpdateFilters),
                          (wdr.ID_BTNPRT, self.OnStampa)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        self.Bind(wx.EVT_RADIOBOX, self.OnCliFor, id=wdr.ID_CTRQUADCF)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnShowDiff, self.gridif)
    
    def OnCliFor(self, event):
        self.SetCliForFilters()
        event.Skip()
    
    def SetCliForFilters(self):
        ci = lambda x: self.FindWindowById(x)
        clifor = ci(wdr.ID_CTRQUADCF).GetValue()
        tipi = self.tipicf[clifor]
        for cid in (wdr.ID_CTRQUADANA1,
                    wdr.ID_CTRQUADANA2):
            ci(cid).SetValue(None)
            ci(cid).SetFilter("id_tipo IN (%s)" % ','.join([str(t) for t in tipi]))
    
    def OnStampa(self, event):
        self.Stampa()
        event.Skip()
    
    def Stampa(self, singolo=False, sintesi=False):
        if self.FindWindowById(wdr.ID_CTRQUADCF).GetValue() == "C":
            cf, sg = "Clienti", "D"
        else:
            cf, sg = "Fornitori", "A"
        i = self.dbdif._info
        i._clifor, i._segno = cf, sg
        rpt.Report(self, self.dbdif, "Quadratura Mastri-Partite")

    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        event.Skip()
    
    def UpdateFilters(self):
        
        dif = self.dbdif
        dif.ClearFilters()
        
        ci = lambda x: self.FindWindowById(x)
        clifor = ci(wdr.ID_CTRQUADCF).GetValue()
        filter = r"tipana.tipo=%s"
        par = [clifor]
        for cid, op in ((wdr.ID_CTRQUADANA1, '>='),
                        (wdr.ID_CTRQUADANA2, '<=')):
            val = ci(cid).GetValueDes()
            if val:
                filter += " AND pdc.descriz %s %%s" % op
                par.append(val)
        
        wait = aw.awu.WaitDialog(self)
        ok = dif.Retrieve(filter, par)
        wait.Destroy()
        if ok:
            rs = dif.GetRecordset()
        else:
            aw.awu.MsgDialog(self, message=repr(dif.GetError()))
            rs = ()
        self.gridif.ChangeData(rs)
    
    def OnShowDiff(self, event):
        tipo = self.FindWindowById(wdr.ID_CTRQUADCF).GetValue()
        self.dbdif.MoveRow(event.GetRow())
        pdcid = self.dbdif.pdc_id
        if tipo == 'C':
            from contab.pdcint import ClientiInterrFrame as dlgcls
        else:
            from contab.pdcint import FornitInterrFrame as dlgcls
        make = False
        if self.interrpdc is None:
            make = True
        else:
            try:
                x = self.interrpdc.GetSize()
            except wx.PyDeadObjectError:
                make = True
            else:
                if not isinstance(self.interrpdc, dlgcls):
                    self.interrpdc.Destroy()
                    make = True
        try:
            wx.BeginBusyCursor()
            if make:
                self.interrpdc = dlgcls(self, complete=False, onecodeonly=pdcid)
                self.interrpdc.SetTitle("Interroga anagrafica")
                self.interrpdc.FindWindowByName('_titlecard').SetLabel('Scheda')
                self.interrpdc.panel.firstfocus = None
                self.interrpdc.DisplayTab('scadenzario')
            self.interrpdc.panel.onecodeonly = pdcid
            self.interrpdc.UpdateSearch()
            if make:
                self.interrpdc.Show()
                self.interrpdc.SetFocus()
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


class PdcQuadPcfContFrame(aw.Frame):
    """
    Frame differenze martri-scadenzari
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(PdcQuadPcfContPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class PdcQuadPcfContDialog(aw.Dialog):
    """
    Dialog differenze martri-scadenzari
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(PdcQuadPcfContPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    import Env
    Env.InitSettings()
    db = dbc.adb.DB()
    db.Connect()
    win = PdcQuadPcfContFrame()
    win.ShowModal()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
