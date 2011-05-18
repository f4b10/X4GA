#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/barcodes.py
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

import magazz.barcodes_wdr as wdr
import magazz.dbtables as dbm

import awc.util as util
from anag.prod import ProdDialog

from Env import Azienda
bt = Azienda.BaseTab

import report as rpt


FRAME_TITLE = "Stampa etichette prodotti"


class EtichetteProdottiGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbpro):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbpro = pro = dbpro
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        self.colqta = cn(pro,'qtaetic')
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        
        cols = (\
            ( 80, (cn(pro, "codice"),   "Cod.",         _STR, True)),
            (200, (cn(pro, "descriz"),  "Descrizione",  _STR, True)),
            (200, (cn(pro, "descetic"), "Su etichetta", _STR, True)),
            (100, (cn(pro, "barcode"),  "BarCode",      _STR, True)),
            ( 40, (cn(pro, "qtaetic"),  "Qtà",          _NUM, True)),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = True
        
        editors = []
        from anag.lib import DataLinkProdCellEditor
        prod_editor = DataLinkProdCellEditor(bt.TABNAME_PROD,   #table
                                             cn(pro,'id'),      #rs col id
                                             cn(pro,'codice'),  #rs col cod
                                             cn(pro,'descriz'), #rs col des
                                             ProdDialog)      #card class
        editors.append((0, prod_editor))
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1,\
                       self.OnCellEdited), )
        
        self.SetData(dbpro.GetRecordset(), colmap, canedit, canins,
                     afterEdit=afteredit, editors=editors, 
                     newRowFunc=self.CreateNewRow)
        
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
        
        def MoveColumnAfterEdit(grid, row, col):
            pro = self.dbpro
            if 0 <= row < pro.RowsCount():
                col = 4
            return row, col
        self.SetColumnsFunc(MoveColumnAfterEdit)
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def OnCellEdited(self, row, col, rscol, value):
        resetview = False
        pro = self.dbpro
        pro.MoveRow(row)
        if col == 0:
            pro.id = value #aggiorna i dati del prodotto
            if not pro.qtaetic:
                pro.qtaetic = 1
        self.Refresh()
        return True
    
    def CreateNewRow(self):
        self.dbpro.CreateNewRow()
        return True
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        rs = self.dbpro.GetRecordset()
        ro = (col != 0 and (rscol != self.colqta or row>=len(rs)))
        attr.SetReadOnly(ro)
        if 0 <= row < len(rs):
            bc = Azienda.Colours
            if rs[row][self.colqta] <= 0:
                c = 'gray'
            else:
                c = bc.NORMAL_FOREGROUND
            attr.SetTextColour(c)
        return attr
    
    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        self.SetGridCursor(row, col)
        voci = []
        voci.append(("Azzera quantità", self.OnResetRows, True))
        voci.append(("Setta quantità=1", self.OnSetOneRows, True))
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
    
    def OnRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbpro.RowsCount():
            self.MenuPopup(event)
            event.Skip()
    
    def OnResetRows(self, event):
        self.SetQtaOnSelectedRows(0)
        event.Skip()
    
    def OnSetOneRows(self, event):
        self.SetQtaOnSelectedRows(1)
        event.Skip()
    
    def SetQtaOnSelectedRows(self, n):
        for row in self.GetSelectedRows():
            p = self.dbpro
            p.MoveRow(row)
            p.qtaetic = n
        self.Refresh()
    
    def OnDblClick(self, event):
        row = event.GetRow()
        pro = self.dbpro
        if row >= pro.RowsCount():
            return
        pro.MoveRow(row)
        dlg = ProdDialog(self, onecodeonly=pro.id)
        dlg.OneCardOnly(pro.id)
        dlg.ShowModal()
        dlg.Destroy()
        self.Refresh()


# ------------------------------------------------------------------------------


class EtichetteProdottiPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.EtichetteProdottiPanelFunc(self)
        self.dbpro = dbm.ProdEticList()
        def ci(x):
            return self.FindWindowById(x)
        self.grid = EtichetteProdottiGrid(ci(wdr.ID_PANGRIDBC), self.dbpro)
        for cid, func in ((wdr.ID_PRINT, self.OnPrintEtic),
                          (wdr.ID_RESET, self.OnResetProd)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        self.SetName('LabelSpot')
    
    def SetProdEticList(self, dbpro):
        self.dbpro = self.grid.dbpro = dbpro
        self.grid.ChangeData(self.dbpro.GetRecordset())
    
    def OnResetProd(self, event):
        do = aw.awu.MsgDialog(self, message="Svuoto l'elenco dei prodotti?",
                              style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if do == wx.ID_YES:
            self.dbpro.Reset()
            self.grid.ChangeData(self.dbpro.GetRecordset())
            self.grid.SetFocus()
        event.Skip()
    
    def OnPrintEtic(self, event):
        self.PrintEtichette()
        event.Skip()
    
    def PrintEtichette(self):
        def GetPrintTable(rptdef, _rpt):
            rows = cols = 1
            if '(' in rptdef:
                x = rptdef[rptdef.rindex('(')+1:]
                if x.endswith(')'):
                    x = x[:-1]
                if 'x' in x:
                    rows, cols = map(int,x.split('x'))
            row0 = _rpt.GetLabelOffsetRow()
            col0 = _rpt.GetLabelOffsetCol()
            return self.dbpro.GetPrintTable(rptdef, rows, cols, row0, col0)
        rpt.ReportLabels(self, None, 'Etichette prodotti', dbfunc=GetPrintTable)


# ------------------------------------------------------------------------------


class _EtichetteProdottiMixin(object):
    def __init__(self, kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
    def SetProdEticList(self, dbpro):
        self.panel.SetProdEticList(dbpro)


# ------------------------------------------------------------------------------


class EtichetteProdottiFrame(aw.Frame, _EtichetteProdottiMixin):
    def __init__(self, *args, **kwargs):
        _EtichetteProdottiMixin.__init__(self, kwargs)
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = EtichetteProdottiPanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class EtichetteProdottiDialog(aw.Dialog, _EtichetteProdottiMixin):
    def __init__(self, *args, **kwargs):
        _EtichetteProdottiMixin.__init__(self, kwargs)
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = EtichetteProdottiPanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
    

# ------------------------------------------------------------------------------


class SelQtaPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.SelQtaFunc(self)
        self.FindWindowById(wdr.ID_NUMETIC).SetValue(1)
        self.Bind(wx.EVT_BUTTON, self.OnStampa, id=wdr.ID_PRINTETIC)
        self.Bind(wx.EVT_RADIOBOX, self.OnChanged, id=wdr.ID_QTAETIC)
    
    def OnChanged(self, event):
        if event.GetSelection() == 2:
            self.FindWindowById(wdr.ID_NUMETIC).SetFocus()
        event.Skip()
    
    def GetQta(self, giac):
        def ci(x):
            return self.FindWindowById(x)
        q = ci(wdr.ID_QTAETIC).GetSelection()
        if q == 0:   #un'etichetta
            out = 1
        elif q == 1: #da giacenza
            out = giac
        elif q == 2: #numero di etichette digitato
            out = int(ci(wdr.ID_NUMETIC).GetValue())
        return out
    
    def GetSoloInterni(self):
        return self.FindWindowById(wdr.ID_SOLOINT).GetValue()
    
    def OnStampa(self, event):
        def ci(x):
            return self.FindWindowById(x)
        if ci(wdr.ID_QTAETIC).GetSelection() == 2 and ci(wdr.ID_NUMETIC).GetValue() <= 0:
            aw.awu.MsgDialog(self, 'Dati errati')
            return
        event.Skip()


# ------------------------------------------------------------------------------


class SelQtaDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = 'Quante etichette stampare?'
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = SelQtaPanel(self)
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnPrint, id=wdr.ID_PRINTETIC)
    
    def GetQta(self, *args):
        return self.panel.GetQta(*args)
    
    def GetSoloInterni(self):
        return self.panel.GetSoloInterni()
    
    def OnPrint(self, event):
        self.EndModal(wx.ID_OK)
