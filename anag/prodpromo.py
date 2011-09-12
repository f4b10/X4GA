#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/prodpromo.py
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

import MySQLdb
import stormdb as adb

import anag.prod_wdr as wdr

import awc.util as awu
import awc.controls.linktable as lt
import awc.controls.windows as aw

from anag.prod import ProdDialog

import Env
stdcolor = Env.Azienda.Colours

from Env import Azienda
bt = Azienda.BaseTab

import stormdb as adb
import report as rpt

import magazz.dbtables as dbm
dba = dbm.dba

import anag.lib as alib


FRAME_TITLE = "Condizioni promozionali"


class ProdPromoGrid(dbglib.DbGridColoriAlternati):
    """
    Condizioni promozionali di vendita sui prodotti.
    """
    
    def __init__(self, parent, dbprm):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable promo
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(), 
                                              style=0)
        self.dbprm = dbprm
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        
        def cc(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        prm = dbprm
        pro = prm.prod
        
        cols = []
        self.edcols = []
        
        def c(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                self.edcols.append(n)
            return n
        def C(x):
            return c(x, True)
        
        self.COL_procod =  C(( 80, (cc(pro, 'codice'),  "Codice",   _STR, True)))
        self.COL_prodes =  c((230, (cc(pro, 'descriz'), "Prodotto", _STR, True)))
        self.COL_DATMIN =  C(( 90, (cc(prm, 'datmin'),  "Dal",      _DAT, True)))
        self.COL_DATMAX =  C(( 90, (cc(prm, 'datmax'),  "Al",       _DAT, True)))
        self.COL_PREZZO =  C(( 80, (cc(prm, 'prezzo'),  "Prezzo",   _PRZ, True)))
        if bt.MAGNUMSCO >= 1:
            self.COL_SCONTO1 = C(( 50, (cc(prm, 'sconto1'), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            self.COL_SCONTO2 = C(( 50, (cc(prm, 'sconto2'), "Sc.%2",    _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            self.COL_SCONTO3 = C(( 50, (cc(prm, 'sconto3'), "Sc.%3",    _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            self.COL_SCONTO4 = C(( 50, (cc(prm, 'sconto4'), "Sc.%4",    _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            self.COL_SCONTO5 = C(( 50, (cc(prm, 'sconto5'), "Sc.%5",    _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            self.COL_SCONTO6 = C(( 50, (cc(prm, 'sconto6'), "Sc.%6",    _SCO, True)))
        self.COL_ID_PROM = c((  1, (cc(prm, 'id'),      "#prm",     _STR, True)))
        self.COL_ID_PROD = c((  1, (cc(pro, 'id'),      "#pdc",     _STR, True)))
                                  
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = canins = True
        
        links = None
        
        editors = []
        pe = alib.DataLinkProdCellEditor(bt.TABNAME_PROD,    #table
                                         cc(prm, 'id_prod'), #rs col id
                                         cc(pro, 'codice'),  #rs col cod
                                         cc(pro, 'descriz'), #rs col des
                                         ProdDialog)         #card class
        editors.append((self.COL_procod, pe))
        
        afteredit = ((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.EditedValues),)
        
        self.SetData(prm.GetRecordset(), colmap, canedit, canins, 
                     links, afteredit, self.CreateNewRow, editors)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly(not col in self.edcols)
        return attr

    def EditedValues(self, row, gridcol, col, value):
        prm = self.dbprm
        if 0 <= row < prm.RowsCount():
            prm.MoveRow(row)
            if gridcol == self.COL_procod:
                prm.id_prod = value
            elif col<len(prm.GetFieldNames()):
                setattr(prm, prm.GetFieldName(col), value)
        return True
    
    def OnRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbprm.RowsCount():
            self.MenuPopup(event)
            event.Skip()
    
    def OnDblClick(self, event):
        prm = self.dbprm
        sr = self.GetSelectedRows()
        row = sr[0]
        if 0 <= row < prm.RowsCount():
            prm.MoveRow(row)
            self.ApriSchedaProd()
        event.Skip()
    
    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        prm = self.dbprm
        if not 0 <= row < prm.RowsCount():
            return
        prm.MoveRow(row)
        self.SetGridCursor(row, col)
        if len(self.GetSelectedRows()) < 2:
            self.SelectRow(row)
        prook = prm.id_prod is not None
        voci = []
        if len(self.GetSelectedRows()) == 1:
            voci.append(("Apri la scheda del prodotto", self.OnSchedaProd, prook))
            voci.append(("Elimina la promozione", self.OnDeleteRow,  True))
        else:
            voci.append(("Elimina le promozioni selezionate", self.OnDeleteRow, True))
        menu = wx.Menu()
        for text, func, enab in voci:
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        xo, yo = event.GetPosition()
        self.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()
    
    def OnSchedaProd(self, event):
        self.ApriSchedaProd()
        event.Skip()
    
    def ApriSchedaProd(self):
        proid = self.dbprm.id_prod
        f = None
        try:
            wx.BeginBusyCursor()
            f = ProdDialog(self, onecodeonly=proid)
            f.OneCardOnly(proid)
            f.CenterOnScreen()
        finally:
            wx.EndBusyCursor()
        f.ShowModal()
        if f is not None:
            f.Destroy()
    
    def OnDeleteRow(self, event):
        sr = self.GetSelectedRows()
        if sr:
            prm = self.dbprm
            sr.sort()
            for n in range(len(sr)-1, -1, -1):
                row = sr[n]
                if 0 <= row < prm.RowsCount():
                    prm.MoveRow(row)
                    if prm.id is not None:
                        if not prm.id in prm._info.deletedRecords:
                            #riga già esistente, marco per cancellazione da db
                            prm._info.deletedRecords.append(prm.id)
                    #elimino riga da dbgrid
                    self.DeleteRows(row)
                    prm._info.recordCount -= 1
                    if prm._info.recordNumber >= prm._info.recordCount:
                        prm._info.recordNumber -= 1
                        prm._UpdateTableVars()
                    #after deletion, record cursor is on the following one
                    #so for iterations we decrement iteration index and count
                    prm._info.iterIndex -= 1
                    prm._info.iterCount -= 1
                    self.Refresh()
        event.Skip()
    
    def GridListTestValues(self, row, gridcol, col, value):
        out = True
        return out
    
    def CreateNewRow(self):
        g = self.dbprm
        g.CreateNewRow()
        return True


# ------------------------------------------------------------------------------


class ProdPromoPanel(wx.Panel):
    """
    Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ProdPromoFunc(self)
        def cn(col):
            return self.FindWindowByName(col)
        self.dbprm = dba.ProdPromo()
        self.dbprm.Retrieve()
        self.gridpromo = ProdPromoGrid(cn('pangridpromo'), self.dbprm)
        for name, func in (('butprint', self.OnPrint),
                           ('butsave',  self.OnSave)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnPrint(self, event):
        self.PrintData()
        event.Skip()
    
    def OnSave(self, event):
        if self.Validate():
            if self.SaveData():
                event.Skip()
    
    def PrintData(self):
        rpt.Report(self, self.dbprm, "Condizioni promozionali di vendita")
    
    def Validate(self):
        return True
    
    def SaveData(self):
        prm = self.dbprm
        if not prm.Save():
            awu.MsgDialog(self, repr(prm.GetError()))
            return False
        return True


# ------------------------------------------------------------------------------


class ProdPromoFrame(aw.Frame):
    """
    Frame Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProdPromoPanel(self, -1))
        self.CenterOnScreen()
