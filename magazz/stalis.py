#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stalis.py
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
awu = aw.awu

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb
import anag.dbtables as dba

import magazz.listini_wdr as wdr
from magazz.listini import ColonneDaStampareDialog

import report as rpt


FRAME_TITLE = "Listini in vigore"


class ListiniAttualiGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dblis, incl_costo=False, incl_pzconf=False):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, 
                                              size=parent.GetSize())
        
        self.dblis = lis = dblis
        
        def cc(col):
            return lis._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRZ = bt.GetMagPreMaskInfo()
        _PZC = bt.GetMagPzcMaskInfo()
        wp = 90
        wq = 60
        
        cols = []
        def a(x):
            cols.append(x)
        a(( 30, (cc("catart"),      "Cat.",        _STR, True )))
        a(( 45, (cc("gruart"),      "Gruppo",        _STR, True )))
        a(( 80, (cc("prod_codice"),      "Codice",        _STR, True )))
        a((300, (cc("prod_descriz"),     "Prodotto",      _STR, True )))
        
        if incl_pzconf:
            a(( wq, (cc("prod_pzconf"),  "Pz.Conf.",      _PZC, True )))
        
        if incl_costo:
            a(( wp, (cc("prod_costo"),   "Costo",         _PRZ, True )))
        
        a(( wp, (cc("prod_prezzo"),      "Prezzo",        _PRZ, True )))
        
        if bt.MAGDATLIS:
            a(( 80, (cc("listino_data"), "Data val.",     _DAT, True )))


        dbList = adb.DbTable(bt.TABNAME_TIPLIST, 'tiplis', writable=False)
        dbList.Retrieve()
        titListini={}
        for r in dbList:
            titListini[r.tipoprezzo]=r.descriz


        
        for l in range(1,bt.MAGNUMLIS+1):
            n = 'listino_prezzo%d'%l
            try:
                a((wp, (cc(n),               "%s"%(titListini['%s'%l]), _PRZ, False)))
            except:
                a((wp, (cc(n),               "Listino #%d"%l, _PRZ, False)))
        
        a(( 50, (cc("pdc_codice"),       "Cod.",          _STR, True )))
        a((250, (cc("pdc_descriz"),      "Fornitore",     _STR, True )))
        a((120, (cc("prod_codfor"),      "Cod.Fornit.",   _STR, True )))
        a((120, (cc("prod_barcode"),     "Barcode",       _STR, True )))
        a((  1, (cc("prod_id"),          "#pro",          _STR, True )))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(lis.GetRecordset(), colmap, canedit, canins)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def OnDblClick(self, event):
        lis = self.dblis
        row = event.GetRow()
        if not 0 <= row < lis.RowsCount():
            return
        lis.MoveRow(row)
        try:
            wx.BeginBusyCursor()
            from anag.prod import ProdDialog
            dlg = ProdDialog(self, onecodeonly=lis.prod_id)
            dlg.OneCardOnly(lis.prod_id)
            wx.EndBusyCursor()
            dlg.ShowModal()
            dlg.Destroy()
            event.Skip()
        except:
            pass


# ------------------------------------------------------------------------------


class ListiniAttualiPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.InitTable()
        self.InitControls()
        def cn(x):
            return self.FindWindowByName(x)
        cn('dataval').SetValue(Env.Azienda.Login.dataElab)
        for name, func in (('butupdate', self.OnUpdate),
                           ('butprint', self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        self.SetName('ListiniAttuali')
    
    def InitTable(self):
        self.dblis = dba.TabProdListiniAttualiTable()
    
    def InitControls(self):
        wdr.SelDataPanel = wdr.ListiniAttualiSelDataPanel
        wdr.ListiniAttualiFunc(self)
        self.gridlis = None
        self.InitGrid()
    
    def InitGrid(self):
        cn = self.FindWindowByName
        if self.gridlis:
#            self.gridlis.Destroy()
            wx.CallAfter(self.gridlis.Destroy)
        self.gridlis = ListiniAttualiGrid(cn('pangridlist'), self.dblis, 
                                          incl_costo=cn('incl_costo').IsChecked(), 
                                          incl_pzconf=cn('incl_pzconf').IsChecked())
    
    def OnUpdate(self, event):
        if self.Validate():
            self.UpdateData()
            event.Skip()
    
    def Validate(self):
        def cn(x):
            return self.FindWindowByName(x)
        if bt.MAGDATLIS and not cn('dataval').GetValue():
            awu.MsgDialog(self, "Impostare la data di validità", style=wx.ICON_ERROR)
            return False
        return True
    
    def UpdateData(self):
        cn = self.FindWindowByName
        d = cn('dataval').GetValue()
        lis = self.dblis
        lis.SetDataVal(d)
        class Filter:
            cmd = ""
            par = []
            def AddFilter(self, f, p):
                if self.cmd:
                    self.cmd += " AND "
                self.cmd += f
                self.par.append(p)
        li = Filter()
        for col in 'codice codfor barcode'.split():
            c1, c2 = map(lambda x: cn(x).GetValue(), (col+'1', col+'2'))
            if c1:
                li.AddFilter("prod.%s>=%%s" % col, c1)
            if c2:
                li.AddFilter("prod.%s<=%%s" % col, '%sZ'%c2)
        for tab in 'tipart catart gruart marart status'.split():
            c1, c2 = map(lambda x: cn(x).GetValueCod(), (tab+'1', tab+'2'))
            if c1:
                li.AddFilter("%s.codice>=%%s" % tab, c1)
            if c2:
                li.AddFilter("%s.codice<=%%s" % tab, c2)
        c1, c2 = map(lambda x: cn(x).GetValueDes(), 'fornit1 fornit2'.split())
        if c1:
            li.AddFilter("pdc.descriz>=%s", c1)
        if c2:
            li.AddFilter("pdc.descriz<=%s", c2)
            
            
        if self.FindWindowByName('includiHide').GetValue()==0:
            li.AddFilter("(not status.hidesearch=%s or status.hidesearch is null)", 1)
            
            
        lis.Retrieve(li.cmd, li.par)
        self.InitGrid()
        self.gridlis.ChangeData(lis.GetRecordset())
        return True
    
    def SetColumnsToPrint(self, rptdef, *args):
        out = None
        def cn(x):
            return self.FindWindowByName(x)
        unique = '1 prezzo' in rptdef
        lis = self.dblis
        if bt.MAGNUMLIS == 0:
            lis._datlis = Env.Azienda.Login.dataElab
        else:
            lis._datlis = cn('dataval').GetValue()
        lis._deslis = "Listino in vigore al:"
        dlg = ColonneDaStampareDialog(self, -1, 'Stampa listini')
        def dn(x):
            return dlg.FindWindowByName(x)
        dn('p_costo').SetName('prod_costo')
        dn('p_prezzo').SetName('prod_prezzo')
        for n in range(1,10,1):
            dn('prezzo%d'%n).SetName('listino_prezzo%d'%n)
        dlg.SetUnique(unique)
        do = False
        nc = 0
        if dlg.ShowModal() == wx.ID_OK:
            out = lis
            for name in ['prod_costo', 'prod_prezzo']+['listino_prezzo%d'%l for l in range(1,10)]:
                tl = dba.TipoListino()
                x = dlg.FindWindowByName(name).GetValue()
                k = lis._cols[name]
                if name == 'prod_costo':
                    t = 'Costo acquisto'
                elif name == 'prod_prezzo':
                    t = 'Prezzo pubbl.'
                else:
                    l = name[-1]
                    if tl.Retrieve('tipoprezzo=%s', l):
                        t = tl.descriz or 'Prezzo %s' % l
                k['title'] = t
                lis.PrintCol(name, x)
                if x:
                    do = True
                    nc += 1
            if not do:
                msg =\
                """Devi selezionare almeno una colonna, altrimenti """\
                """diventa una lista prodotti e non una stampa di """\
                """listino!!!"""
                aw.awu.MsgDialog(self, message=msg, style=wx.ICON_WARNING)
                out = None
            elif unique and nc>1:
                msg = """Devi selezionare solo una colonna."""
                aw.awu.MsgDialog(self, message=msg, style=wx.ICON_INFORMATION)
                out = None
        dlg.Destroy()
        return out
    
    def OnPrint(self, event):
        self.PrintListino()
        event.Skip()
    
    def PrintListino(self):
        rpt.Report(self, self.dblis, 'Listino prezzi', 
                   dbfunc=self.SetColumnsToPrint)


# ------------------------------------------------------------------------------


class ListiniAttualiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ListiniAttualiPanel(self))
        self.CenterOnScreen()
