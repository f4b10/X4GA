#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/mastri.py
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

import cfg.dbtables as dbx
from cfg.cfgcontab import CfgContab

import contab.dbtables as dbc
import contab.pdcint_wdr as wdr
from contab.pdcint import GridMastro as MastriSottocontoRegGrid
from cfg.cfgcontab import CfgContab

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import stormdb as adb

import report as rpt


FRAME_TITLE = "Mastri sottoconto"


class MastriSottocontoPdcGrid(dbglib.DbGrid2Colori):
    
    def __init__(self, parent, dbpdc):
        
        dbglib.DbGrid2Colori.__init__(self, parent, -1, 
                                      size=parent.GetClientSizeTuple(),
                                      idGrid='mastriconti')
        
        pdc = self.dbpdc = dbpdc
        mas = pdc.bilmas
        con = pdc.bilcon
        pdc.Get(-1)
        
        _STR = gl.GRID_VALUE_STRING
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        cols = (\
            ( 40, (cn(mas, 'codice'),  "Mas.",       _STR, True )),\
            ( 40, (cn(con, 'codice'),  "Con.",       _STR, True )),\
            ( 50, (cn(pdc, 'codice'),  "Cod.",       _STR, True )),\
            (100, (cn(pdc, 'descriz'), "Sottoconto", _STR, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(dbpdc.GetRecordset(), colmap, canedit, canins)
        
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


# ------------------------------------------------------------------------------


class MastriSottocontoPanel(aw.Panel):
    """
    Panel Mastri sottoconto
    """
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.MastriSottocontoFunc(self)
        def cn(x):
            return self.FindWindowByName(x)
        
        self.tiposta = cn('tiposta')
        self.noEsercizio = cn('noEsercizio')
        
        
        self.dbpdc = dbc.MastriSottoconto()
        self.dbpdc.ShowDialog(self)
        self.dbpsm = dbx.ProgrStampaMastri()
        self.dbcfg = CfgContab()
        self.SetDates()
        self.gridreg = MastriSottocontoRegGrid(cn('pangridreg'))
        self.gridreg.dbmas = self.dbpdc
        self.gridpdc = MastriSottocontoPdcGrid(cn('pangridpdc'), self.dbpdc)
        for name, func in (('btnupdate', self.OnUpdate),
                           ('btnprint',  self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        self.lastpdcrow = None
        cn('mastrizone').SetSashPosition(350)
        self.Bind(wx.EVT_CHOICE, self.OnEsercizioChanged, cn('esercizio'))
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnUpdateReg, self.gridpdc)
        
        self.tiposta.Bind(wx.EVT_RADIOBOX, self.OnTipoSta)
        
    def OnTipoSta(self, evt):
        titolo = self.FindWindowByName('tipotit')
        if self.tiposta.GetValue()=='R':
            self.noEsercizio.SetValue(False)
            titolo.SetLabel('Ristampa')
        elif self.tiposta.GetValue()=='D':
            self.noEsercizio.SetValue(False)
            titolo.SetLabel('Stampa definitiva')
        else:
            titolo.SetLabel('Stampa provvisoria')
        self.noEsercizio.Enable(self.tiposta.GetValue()=='P')
        evt.Skip()
        
    
    def OnEsercizioChanged(self, event):
        self.SetDates()
        event.Skip()
    
    def SetDates(self):
        def cn(x):
            return self.FindWindowByName(x)
        e = cn('esercizio').GetValue()
        de1, de2 = self.dbcfg.GetEsercizioDates(e)
        if e:
            d1 = self.dbpsm.GetDataMastri(e)
            if d1:
                d1 += Env.DateTime.DateTimeDelta(1)
        if not d1:
            d1 = de1
        d2 = de2
        if d1:
            cn('datreg1').SetValue(d1)
        if d2:
            cn('datreg2').SetValue(d2)
    
    def OnUpdateReg(self, event):
        self.UpdateGridReg(row = event.GetRow())
        event.Skip()
    
    def UpdateGridReg(self, row=None):
        if row is None:
            row = self.gridpdc.GetSelectedRows()[0]
        if row < self.dbpdc.RowsCount():
            if row != self.lastpdcrow:
                dbpdc = self.dbpdc
                if row < dbpdc.RowsCount():
                    dbpdc.MoveRow(row)
                    rs = dbpdc.mov.GetRecordset()
                else:
                    rs = ()
                self.gridreg.ChangeData(rs)
                self.lastpdcrow = row
    
    def OnUpdate(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        pdc = self.dbpdc
        def cn(x):
            return self.FindWindowByName(x)
        e, d1, d2, to = map(lambda x: cn(x).GetValue(), 'esercizio datreg1 datreg2 tipord'.split())
        
        
        if self.noEsercizio.GetValue():
            e=None
        
        err = None
        if d1 is None:
            err = "Manca la data iniziale"
        if not err and d2 is None:
            err = "Manca la data finale"
        if err:
            aw.awu.MsgDialog(self, message=err, style=wx.ICON_ERROR)
            return
        pdc.ClearOrders()
        if to == 'C':
            #ordinamento per codice
            pdc.AddOrder('pdc.codice')
        elif to == 'D':
            #ordinamento per descrizione
            pdc.AddOrder('pdc.descriz')
        elif to == 'B':
            #ordinamento per classif. bilancio e descrizione
            pdc.AddOrder('bilmas.codice')
            pdc.AddOrder('bilcon.codice')
            pdc.AddOrder('pdc.descriz')
        pdc.ClearFilters()
        pdc.ClearMovFilters()
        pdc.SetMovBaseFilter()
        for name, tab in (('mastro', 'bilmas'),
                          ('conto',  'bilcon'),
                          ('pdc',    'pdc'),
                          ('tipana', 'tipana'),
                          ):
            for num, op in (('1', '>='),
                            ('2', '<='),
                            ):
                val = cn(name+num).GetValueCod()
                if val:
                    pdc.AddFilter('%s.codice%s%%s' % (tab, op), val)
        d1, d2 = map(lambda x: cn(x).GetValue(), ('datreg1', 'datreg2'))
        if d1:
            pdc.SetDateStart(d1, esercizio=e)
        if d2:
            pdc.SetDateEnd(d2)
        pdc.SetEsercizio(e)
        if pdc.Retrieve():
            self.gridpdc.ChangeData(pdc.GetRecordset())
            self.lastpdcrow = None
            self.UpdateGridReg()
        else:
            aw.awu.MsgDialog(self, message=repr(pdc.GetError()),
                             style=wx.ICON_ERROR)
    
    def OnPrint(self, event):
        self.StampaMastrino()
        event.Skip()
    
    def StampaMastrino(self):
        db = self.dbpdc
        cpp = aw.awu.MsgDialog(self, "Vuoi un solo sottoconto per ogni pagina?",
                               style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        db._info.cpp = (cpp == wx.ID_YES)
        db._info.intestapag = self.FindWindowByName('intestapag').GetValue() == 1
        def setCPP(rptdef, dbt):
            groups = rptdef.lGroup
            for g in groups:
                if groups[g].name == 'sottoconto':
                    if db._info.cpp:
                        snp = 'true'
                    else:
                        snp = 'false'
                    groups[g].isStartNewPage = snp
        rpt.Report(self, db, "Mastro sottoconto", testrec=db.mov, startFunc=setCPP)


# ------------------------------------------------------------------------------


class MastriSottocontoFrame(aw.Frame):
    """
    Frame Mastri sottoconto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(MastriSottocontoPanel(self, -1))
        self.CenterOnScreen()
