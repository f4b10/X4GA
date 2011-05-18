#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/listini.py
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

import copy

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw
MsgBox = aw.awu.MsgDialog

import magazz.listini_wdr as wdr

from awc.controls.linktable import EVT_LINKTABCHANGED

import stormdb as adb
import magazz.dbtables as dbm

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import awc.controls.linktable as lt
import awc.controls.datectrl as dc

from anag.prod import ProdDialog

import csv

from magazz.chiusure.editgiac import ProdottoHelperEditor

import awc.controls.dbgrideditors as dbgred

import report as rpt


_evtPRODCHANGED = wx.NewEventType()
EVT_PRODCHANGED = wx.PyEventBinder(_evtPRODCHANGED, 1)
class ProdChangedEvent(wx.PyCommandEvent):
    pass

_evtLISTCHANGED = wx.NewEventType()
EVT_LISTCHANGED = wx.PyEventBinder(_evtLISTCHANGED, 1)
class ListChanged(wx.PyCommandEvent):
    pass


FRAME_TITLE = "Listini di vendita"


class SintesiGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbsin):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetSize(), style=0)
        self.dbsin = dbsin
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        sin = dbsin
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            (80, (cn(sin, "data"),          "Data",       _DAT, True )),\
            (70, (cn(sin, "count_id_prod"), "Prodotti",   _NUM, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData((), colmap, canedit, canins)
        
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


class VariaPercDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        p = aw.Panel(self)
        wdr.VariaPercFunc(p)
        c = self.FindWindowByName('tvlist')
        c.SetValue('R')
        if bt.MAGNUMLIS == 0:
            c.Disable()
        self.EnableList()
        self.AddSizedPanel(p)
        self.Fit()
        self.CenterOnScreen()
        self.Bind(wx.EVT_RADIOBOX, self.OnEnableList, id=wdr.ID_TVLIST)
        self.Bind(wx.EVT_BUTTON, self.OnApplica, id=wdr.ID_BTNOK)
    
    def OnEnableList(self, event):
        self.EnableList()
        event.Skip()
    
    def EnableList(self):
        def cn(x):
            return self.FindWindowByName(x)
        e = (cn('tvlist').GetValue() == 'V')
        for l in range(1,10):
            for name in ('pvprezzo%d,labelprezzo%d'%(l,l)).split(','):
                cn(name).Enable(e and l<=bt.MAGNUMLIS)

    def OnApplica(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class DescrizCellEditor(dbgred.TextCellEditor):
    
    qtacol = 0
    def SetQtaCol(self, qc):
        self.qtacol = qc
    
    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing:
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            table = grid.GetTable()
            try:
                r = aw.awu.ListSearch(table.data, lambda x: (x[grid.descrizcol] or '').startswith(val.lstrip()))
                def Muovi():
                    grid.MakeCellVisible(r, self.qtacol)
                    grid.SetGridCursor(r, self.qtacol)
                wx.CallAfter(Muovi)
            except IndexError:
                pass
        self.editing = False
        self.startValue = None
        return changed


# ------------------------------------------------------------------------------


class CodForCellEditor(dbgred.TextCellEditor):
    
    qtacol = 0
    def SetQtaCol(self, qc):
        self.qtacol = qc
    
    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing:
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            table = grid.GetTable()
            try:
                r = aw.awu.ListSearch(table.data, lambda x: x[grid.codforcol] == val)
                def Muovi():
                    grid.MakeCellVisible(r, self.qtacol)
                    grid.SetGridCursor(r, self.qtacol)
                wx.CallAfter(Muovi)
            except IndexError:
                pass
        self.editing = False
        self.startValue = None
        return changed


# ------------------------------------------------------------------------------


class AssegnaGruppoPrezziPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.AssegnaGruPrezFunc(self)


# ------------------------------------------------------------------------------


class AssegnaGruppoPrezziDialog(aw.Dialog):
    
    id_gruprez = None
    solosenza = True
    
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = AssegnaGruppoPrezziPanel(self)
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnAssegna, 
                  self.FindWindowByName('butassegna'))
    
    def SetNumProdotti(self, numprod):
        self.FindWindowByName('numprodotti').SetLabel(str(numprod))
    
    def OnAssegna(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        self.id_gruprez = cn('new_gruprez').GetValue()
        self.solosenza = cn('solosenzagp').GetValue()
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class ListiniGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dblis):
        
        class ListiniGridTable(dbglib.DbGridTable):
            
            def GetDataValue(tself, row, col, gridcols=False):
                
                out = None
                
                try:
                    r = self.dblis.GetRecordset()[row]
                    
                    try:
                        if   col == getattr(self, 'COL_P_VREP', None):
                            #ricarica effettiva (prezzo al pubblico rispetto al costo)
                            out = (r[self._colprelis]/r[self._colcoslis]*100)-100
                            
                        elif col == getattr(self, 'COL_P_VRE1', None):
                            #ricarica effettiva (listino 1 rispetto al costo)
                            out = (r[self._col_prelis1]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE2', None):
                            #ricarica effettiva (listino 2 rispetto al costo)
                            out = (r[self._col_prelis2]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE3', None):
                            #ricarica effettiva (listino 3 rispetto al costo)
                            out = (r[self._col_prelis3]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE4', None):
                            #ricarica effettiva (listino 4 rispetto al costo)
                            out = (r[self._col_prelis4]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE5', None):
                            #ricarica effettiva (listino 5 rispetto al costo)
                            out = (r[self._col_prelis5]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE6', None):
                            #ricarica effettiva (listino 6 rispetto al costo)
                            out = (r[self._col_prelis6]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE7', None):
                            #ricarica effettiva (listino 7 rispetto al costo)
                            out = (r[self._col_prelis7]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE8', None):
                            #ricarica effettiva (listino 8 rispetto al costo)
                            out = (r[self._col_prelis8]/r[self._colcoslis]*100)-100
                        elif col == getattr(self, 'COL_P_VRE9', None):
                            #ricarica effettiva (listino 9 rispetto al costo)
                            out = (r[self._col_prelis9]/r[self._colcoslis]*100)-100
                            
                        elif col == getattr(self, 'COL_P_VSEP', None):
                            #sconto effettivo (costo rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._colcoslis])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE1', None):
                            #sconto effettivo (listino 1 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis1])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE2', None):
                            #sconto effettivo (listino 2 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis2])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE3', None):
                            #sconto effettivo (listino 3 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis3])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE4', None):
                            #sconto effettivo (listino 4 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis4])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE5', None):
                            #sconto effettivo (listino 5 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis5])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE6', None):
                            #sconto effettivo (listino 6 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis6])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE7', None):
                            #sconto effettivo (listino 7 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis7])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE8', None):
                            #sconto effettivo (listino 8 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis8])/r[self._colprelis]*100
                        elif col == getattr(self, 'COL_P_VSE9', None):
                            #sconto effettivo (listino 9 rispetto al prezzo al pubblico)
                            out = (r[self._colprelis]-r[self._col_prelis9])/r[self._colprelis]*100
                            
                    except ZeroDivisionError:
                        out = 0
                except:
                    pass
                    
                if out is None:
                    out = dbglib.DbGridTable.GetDataValue(tself, row, col, gridcols)
                
                return out
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetSize(), 
                                              tableClass=ListiniGridTable)
        self.dblis = dblis
        self.dbpro = dbm.Prodotti()
        self.autoricalc = False
        self.autolistino = False
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        lis = self.dblis
        pro = lis.prod
        gpr = pro.gruprez
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRE = bt.GetMagPreMaskInfo()
        _PRC = bt.GetMagScoMaskInfo()
        wp = wdr.PREZZOWIDTH
        wr = 40 #larghezza wx delle colonne percentuale intera
        
        cols = []
        self.colnames = ['codice','descriz','p_costo','p_prezzo']
        self.edcols = []
        def c(col, ed=False):
            n = len(cols)
            cols.append(col)
            if col[1] is not None:
                self.colnames.append(col[1])
            if ed:
                self.edcols.append(n)
            return n
        def C(col):
            return c(col, ed=True)
        
        self.COL_CODICE =  C(( 80, None,       (cn(pro, "codice"),   "Codice",        _STR, True )))
        self.proidcol = cn(pro, "id")
        self.COL_DESCRIZ = C((240, None,       (cn(pro, "descriz"),  "Prodotto",      _STR, True )))
        self.descrizcol = cn(pro, "descriz")
        
        if bt.MAGFORLIS:
            self.COL_CODFOR = C(( 90, None,    (cn(pro, "codfor"),   "Cod.Fornit.",   _STR, True )))
            self.codforcol = cn(pro, "codfor")
        
        self.COL_grupre =  C(( 30, None,       (cn(gpr, "codice"),   "GP",            _STR, False)))
        self.COL_cpc =     c(( 10, None,       (cn(gpr, "calcpc"),   "CPC",           _STR, False)))
        
        self.COL_COSTO =   C(( wp, 'p_costo',  (cn(lis, "p_costo"),  "Costo acq.",    _PRE, False)))
        
        #ricariche sul prodotto - editazione
        self.COL_P_ERP1 = self.COL_P_ERP2 = self.COL_P_ERP3 = None
        if bt.MAGERPLIS >= 1:
            self.COL_P_ERP1 = C(( wr, None,    (cn(pro, "ricar1"),   "RP%1",    _PRC, False)))
        if bt.MAGERPLIS >= 2:
            self.COL_P_ERP2 = C(( wr, None,    (cn(pro, "ricar2"),   "RP%2",    _PRC, False)))
        if bt.MAGERPLIS >= 3:
            self.COL_P_ERP3 = C(( wr, None,    (cn(pro, "ricar3"),   "RP%3",    _PRC, False)))
        
        #ricariche sul gruppo prezzi - visualizzazione 
        self.COL_P_VRG1 = self.COL_P_VRG2 = self.COL_P_VRG3 = None
        if bt.MAGVRGLIS >= 1:
            self.COL_P_VRG1 = c(( wr, None,    (cn(gpr, "prccosric1"), "RG%1",    _PRC, False)))
        if bt.MAGVRGLIS >= 2:
            self.COL_P_VRG2 = c(( wr, None,    (cn(gpr, "prccosric2"), "RG%2",    _PRC, False)))
        if bt.MAGVRGLIS >= 3:
            self.COL_P_VRG3 = c(( wr, None,    (cn(gpr, "prccosric3"), "RG%3",    _PRC, False)))
        
        self.COL_PREZZO =  C(( wp, 'p_prezzo', (cn(lis, "p_prezzo"), "Prezzo pubbl.", _PRE, False)))
        
        #ricarica effettiva del prezzo pubblico sul costo - visualizzazione 
        self.COL_P_VREP = self.COL_P_VSEP = None
        if bt.MAGREPLIS >= 1:
            self.COL_P_VREP = c(( wr, None,    (-1, "RE%",    _PRC, False)))
        if bt.MAGSEPLIS >= 1:
            self.COL_P_VSEP = c(( wr, None,    (-1, "SE%",    _PRC, False)))
        
        #scontistiche sul prodotto - editazione
        self.COL_P_ESP1 = self.COL_P_ESP2 = self.COL_P_ESP3 = None
        if bt.MAGESPLIS >= 1:
            self.COL_P_ESP1 = C(( wr, None,    (cn(pro, "sconto1"),  "SP%1",    _PRC, False)))
        if bt.MAGESPLIS >= 2:
            self.COL_P_ESP2 = C(( wr, None,    (cn(pro, "sconto2"),  "SP%2",    _PRC, False)))
        if bt.MAGESPLIS >= 3:
            self.COL_P_ESP3 = C(( wr, None,    (cn(pro, "sconto3"),  "SP%3",    _PRC, False)))
        
        #scontistiche sul gruppo prezzi - visualizzazione 
        self.COL_P_VSG1 = self.COL_P_VSG2 = self.COL_P_VSG3 = None
        if bt.MAGVSGLIS >= 1:
            self.COL_P_VSG1 = c(( wr, None,    (cn(gpr, "prcpresco1"),  "SG%1",    _PRC, False)))
        if bt.MAGVSGLIS >= 2:
            self.COL_P_VSG2 = c(( wr, None,    (cn(gpr, "prcpresco2"),  "SG%2",    _PRC, False)))
        if bt.MAGVSGLIS >= 3:
            self.COL_P_VSG3 = c(( wr, None,    (cn(gpr, "prcpresco3"),  "SG%3",    _PRC, False)))
        
        for l in range(1,bt.MAGNUMLIS+1):
            
            n = 'prezzo%d'%l
            C((wp, n, (cn(lis, n), "Listino #%d"%l, _PRE, False)))
            
            #ricarica effettiva del listino - visualizzazione
            setattr(self, 'COL_P_VRE%d'%l, None) 
            if bt.MAGRELLIS >= 1:
                v = c(( wr, None,    (-1, "RE%", _PRC, False)))
                setattr(self, 'COL_P_VRE%d'%l, v)
            
            #sconto effettivo del listino - visualizzazione
            setattr(self, 'COL_P_VSE%d'%l, None) 
            if bt.MAGSELLIS >= 1:
                v = c(( wr, None,    (-1, "SE%", _PRC, False)))
                setattr(self, 'COL_P_VSE%d'%l, v)
        
        C((200, 'note', (cn(lis, "note"), "note", _STR, True )))
        
        if not bt.MAGDATLIS:
            c((wp, None, (cn(lis, "data"), "Data val.", _DAT, False)))
        
        c((  1,   None, (cn(lis, "id"),   "#lis", _STR, True )))
        
        self._colcospro = cn(pro, 'costo')
        self._colcoslis = cn(lis, 'p_costo')
        self._colprepro = cn(pro, 'prezzo')
        self._colprelis = cn(lis, 'p_prezzo')
        self._col_prelis1 = cn(lis, 'prezzo1')
        self._col_prelis2 = cn(lis, 'prezzo2')
        self._col_prelis3 = cn(lis, 'prezzo3')
        self._col_prelis4 = cn(lis, 'prezzo4')
        self._col_prelis5 = cn(lis, 'prezzo5')
        self._col_prelis6 = cn(lis, 'prezzo6')
        self._col_prelis7 = cn(lis, 'prezzo7')
        self._col_prelis8 = cn(lis, 'prezzo8')
        self._col_prelis9 = cn(lis, 'prezzo9')
        
        colmap  = [c[2] for c in cols]
        colsize = [c[0] for c in cols]
        self.listcols = {}
        for n, col in enumerate(cols):
            if col[1] is not None:
                self.listcols[n] = col[1]
        self.modrows = []
        self.delrows = []
        self.promod = {}
        
        canedit = True
        canins = False
        
        afteredit = ( (dbglib.CELLEDIT_BEFORE_UPDATE, -1,\
                       self.OnValueChanged), )
        
        editors = []
        prod_editor = ProdottoHelperEditor(bt.TABNAME_PROD,    #table
                                           cn(pro, 'id'),      #rs col id
                                           cn(pro, 'codice'),  #rs col cod
                                           cn(pro, 'descriz'), #rs col des
                                           ProdDialog)         #card class
        prod_editor.SetQtaCol(self.COL_PREZZO)
        editors.append((self.COL_CODICE, prod_editor))
        
        descriz_editor = DescrizCellEditor()
        descriz_editor.SetQtaCol(self.COL_PREZZO)
        editors.append((self.COL_DESCRIZ, descriz_editor))
        
        if bt.MAGFORLIS:
            codfor_editor = CodForCellEditor()
            codfor_editor.SetQtaCol(self.COL_PREZZO)
            editors.append((self.COL_CODFOR, codfor_editor))
        
        import anag.lib as alib
        from anag.gruprez import GruPrezDialog
        gped = alib.DataLinkGruPrezEditor(bt.TABNAME_GRUPREZ,     #table
                                           cn(pro, 'id_gruprez'), #rs col id
                                           cn(gpr, 'codice'),     #rs col cod
                                           cn(gpr, 'descriz'),    #rs col des
                                           GruPrezDialog)         #card class
        editors.append((self.COL_grupre, gped))
        
        self.SetData((), colmap, canedit, canins, afterEdit=afteredit,
                     editors=editors)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallProd)
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnMenu)
        
        self.lastrow = -1
        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnSelectCell)
    
    def OnSelectCell(self, event):
        if event.GetRow() != self.lastrow:
            self.Refresh()
            self.lastrow = event.GetRow()
        event.Skip()
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        readonly = not col in self.edcols
        rs = self.dblis.GetRecordset()
        if 0 <= row < len(rs):
            r = rs[row]
            sf = adb.DbTable.samefloat
            fg = bg = None
            if col in (self.COL_CODICE, self.COL_DESCRIZ) and row == self.GetGridCursorRow():
                bg = 'cyan'
            if col == self.COL_COSTO and not sf(r[self._colcospro] or 0, r[self._colcoslis] or 0) or\
               col == self.COL_PREZZO and not sf(r[self._colprepro] or 0, r[self._colprelis] or 0) or\
               col in self.listcols and row in self.modrows:
                bg = 'yellow'
            if 'E%' in self.GetColLabelValue(col):
                fg = 'darkgray'
            if fg:
                attr.SetTextColour(fg)
            if bg:
                attr.SetBackgroundColour(bg)
            
        attr.SetReadOnly(readonly)
        return attr
    
    def SetAutoRicalc(self, ar):
        self.autoricalc = ar
    
    def SetAutoListino(self, al):
        self.autolistino = al
    
    def OnMenu(self, event):
        row = event.GetRow()
        if 0 <= row < self.dblis.RowsCount():
            self.MenuPopup(event)
            event.Skip()
    
    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        self.SetGridCursor(row, col)
        #self.SelectRow(row)
        lis = self.dblis
        sep = (None,None,None)
        voci = []
        voci.append(("Apri scheda prodotto", self.OnCallProd, True))
        voci.append(sep)
        voci.append(("&Ricalcola il costo/prezzo", self.OnRicalcPC, True))
        voci.append(("Ricalcola i prezzi di &listino", self.OnRicalcList, True))
        voci.append(("Ricalcola il costo/prezzo &e i listini", self.OnRicalcAll, True))
        voci.append(sep)
        voci.append(("Applica &variazioni percentuali", self.OnVariaPerc, True))
        voci.append(sep)
        voci.append(("Seleziona &tutto", self.OnSelectAll, True))
        voci.append(sep)
        voci.append(("Assegna &gruppo prezzi", self.OnAssegnaGruPrez, True))
        menu = wx.Menu()
        for text, func, enab in voci:
            if text is None:
                menu.AppendSeparator()
            else:
                id = wx.NewId()
                menu.Append(id, text)
                menu.Enable(id, enab)
                self.Bind(wx.EVT_MENU, func, id=id)
        xo, yo = event.GetPosition()
        self.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        self.SetFocus()
        event.Skip()
    
    def OnAssegnaGruPrez(self, event):
        d = AssegnaGruppoPrezziDialog(self)
        d.SetNumProdotti(len(self.GetSelectedRows()))
        do = (d.ShowModal() == wx.ID_OK)
        id_gruprez = d.id_gruprez
        solosenza = d.solosenza
        d.Destroy()
        self.RemoveChild(d)
        if do and id_gruprez is None:
            msg =\
                """E' stato confermato l'assegnamento del gruppo prezzi, ma questo non è stato definito.\n"""\
                """Proseguendo, a tutti i prodotti selezionati verrà tolto il gruppo prezzi eventualmente presente.\n"""\
                """Confermi l'eliminazione dei gruppi prezzi dalle schede prodotto?"""
            stl = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
            if aw.awu.MsgDialog(self, msg, style=stl) != wx.ID_YES:
                do = False
        if do:
            lis = self.dblis
            pro = self.dbpro
            sr = self.GetSelectedRows()
            w = len(sr)>10
            if w:
                wd = aw.awu.WaitDialog(self, message="Applicazione gruppo prezzi in corso",
                                       maximum=len(sr))
            try:
                for n, row in enumerate(sr):
                    lis.MoveRow(row)
                    if pro.Get(lis.prod.id) and pro.OneRow():
                        if pro.id_gruprez is None or not solosenza:
                            pro.id_gruprez = lis.prod.id_gruprez = id_gruprez
                            if not pro.Save():
                                aw.awu.MsgDialog(self, repr(pro.GetError()))
                    if w:
                        wd.SetValue(n)
            finally:
                if w:
                    wd.Destroy()
            self.ResetView()
        event.Skip()
    
    def OnSelectAll(self, event):
        self.SelectBlock(0,0,self.dblis.RowsCount()-1,1)
        event.Skip()
    
    def OnVariaPerc(self, event):
        self.VariaPerc()
        event.Skip()
    
    def VariaPerc(self):
        dlg = VariaPercDialog(self, -1, 'Variazioni percentuali')
        if dlg.ShowModal() == wx.ID_OK:
            v = {}
            for c in aw.awu.GetAllChildrens(dlg):
                if hasattr(c, 'GetValue'):
                    v[c.GetName()] = c.GetValue()
            rows = self.GetSelectedRows()
            wait = aw.awu.WaitDialog(self, message="Ricalcolo in corso...",
                                     maximum=len(rows))
            lis = self.dblis
            DP = bt.MAGPRE_DECIMALS
            for r, row in enumerate(rows):
                lis.MoveRow(row)
                w = False
                if v['pvcosto']:
                    #variazione del costo di acquisto
                    lis.p_costo = round(lis.p_costo*(100+v['pvcosto'])/100, DP)
                    w = True
                if v['pvprezzo']:
                    #variazione del prezzo al pubblico
                    lis.p_prezzo = round(lis.p_prezzo*(100+v['pvprezzo'])/100, DP)
                    w = True
                if w:
                    if v['ricalcpc']:
                        self.RicalcolaPC(row)
                    self.promod[lis.prod.id] = [lis.p_costo, lis.p_prezzo]
                if v['tvlist'] == 'R':
                    self.RicalcolaListini(row)
                elif v['tvlist'] == 'V':
                    for l in range(1, bt.MAGNUMLIS+1):
                        x = v['pvprezzo%d'%l]
                        if x:
                            p = getattr(lis, 'prezzo%d'%l)
                            setattr(lis, 'prezzo%d'%l, round(p*(100+x)/100, DP))
                            if not row in self.modrows:
                                self.modrows.append(row)
                wait.SetValue(r)
            self.Refresh()
            wait.Destroy()
        dlg.Destroy()
    
    def OnRicalcPC(self, event):
        self.RicalcolaPC()
        event.Skip()
    
    def OnRicalcList(self, event):
        self.RicalcolaListini()
        event.Skip()
    
    def OnRicalcAll(self, event):
        self.RicalcolaTutto()
        event.Skip()
    
    def RicalcolaPC(self, row=None, exclude=None):
        lis = self.dblis
        pro = self.dbpro
        gpr = pro.gruprez
        if row is not None:
            rows = (row,)
            refresh = False
        else:
            rows = self.GetSelectedRows()
            refresh = True
        wait = None
        if len(rows)>1:
            wait = aw.awu.WaitDialog(self, 
                                     message="Ricalcolo costo/prezzo in corso...",
                                     maximum=len(rows))
        chg = False
        for n, row in enumerate(rows):
            if exclude == 'p_costo' and lis.prod.gruprez.calcpc == "C":
                do = True
            elif exclude == 'p_prezzo' and lis.prod.gruprez.calcpc == "P":
                do = True
            else:
                lis.MoveRow(row)
                pro.Reset()
                pro.CreateNewRow()
                pro.costo = lis.p_costo
                pro.prezzo = lis.p_prezzo
                for name in 'ricar sconto'.split():
                    for num in range(3):
                        field = '%s%d' % (name, num+1)
                        setattr(pro, field, getattr(lis.prod, field))
                pro.id_gruprez = lis.prod.id_gruprez
                tipo, val = pro.RicalcolaPC()
                do = False
                sf = adb.DbTable.samefloat
                if tipo == 'C':
                    if not sf(lis.p_costo, pro.costo):
                        lis.p_costo = pro.costo
                        do = True
                elif tipo == 'P':
                    if not sf(lis.p_prezzo, pro.prezzo):
                        lis.p_prezzo = pro.prezzo
                        do = True
            if do:
                if self.autolistino:
                    pro.RicalcolaListini(lis)
                self.promod[lis.prod.id] = [lis.p_costo, lis.p_prezzo]
                if not row in self.modrows:
                    self.modrows.append(row)
                chg = True
            if wait:
                wait.SetValue(n)
        if wait:
            wait.Destroy()
        if chg and refresh:
            self.Refresh()
            self.RaiseListChanged()
    
    def RaiseListChanged(self):
        evt = ListChanged(_evtLISTCHANGED, self.GetId())
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        self.GetEventHandler().AddPendingEvent(evt)
    
    def RicalcolaListini(self, row=None):
        lis = self.dblis
        pro = self.dbpro
        gpr = pro.gruprez
        if row is not None:
            rows = (row,)
            refresh = True
        else:
            rows = self.GetSelectedRows()
            refresh = True
        wait = None
        if len(rows)>1:
            wait = aw.awu.WaitDialog(self, 
                                     message="Ricalcolo listini in corso...",
                                     maximum=len(rows))
        chg = False
        for n, row in enumerate(rows):
            lis.MoveRow(row)
            pro.Reset()
            pro.CreateNewRow()
            pro.costo = lis.p_costo
            pro.prezzo = lis.p_prezzo
            pro.id_gruprez = lis.prod.id_gruprez
            prezzi = pro.RicalcolaListini(lis)
            w = False
            for n in range(1, bt.MAGNUMLIS+1):
                if n in prezzi:
                    p = prezzi[n]
                else:
                    p = 0
                if not adb.DbTable.samefloat(getattr(lis, 'prezzo%d'%n) or 0, p or 0):
                    setattr(lis, 'prezzo%d'%n, p)
                w = chg = True
            if w:
                if not row in self.modrows:
                    self.modrows.append(row)
            if wait:
                wait.SetValue(n)
        if wait:
            wait.Destroy()
        if chg:
            if refresh:
                self.Refresh()
            self.RaiseListChanged()
    
    def RicalcolaTutto(self):
        self.RicalcolaPC()
        self.RicalcolaListini()
    
    def ChangeData(self, *args, **kwargs):
        dbglib.DbGridColoriAlternati.ChangeData(self, *args, **kwargs)
        self.ClearSelection()
        del self.modrows[:]
        del self.delrows[:]
        self.promod.clear()
    
    def GetModifiedRows(self):
        return self.modrows
    
    def GetDeletedRows(self):
        return self.delrows
    
    def GetProMod(self):
        return self.promod
    
    def OnValueChanged(self, row, gridcol, col, value):
        lis = self.dblis
        lis.MoveRow(row)
        if gridcol in self.listcols:
            setattr(lis, self.listcols[gridcol], value)
            self.TestChanges(row, gridcol)
        elif gridcol in (self.COL_grupre, self.COL_P_ERP1, self.COL_P_ERP2, self.COL_P_ERP3, self.COL_P_ESP1, self.COL_P_ESP2, self.COL_P_ESP3):
            p = self.dbpro
            if p.Get(lis.prod.id) and p.OneRow():
                if gridcol == self.COL_grupre:
                    p.id_gruprez = lis.prod.id_gruprez = value
                elif gridcol == self.COL_P_ERP1:
                    p.ricar1 = value
                elif gridcol == self.COL_P_ERP2:
                    p.ricar2 = value
                elif gridcol == self.COL_P_ERP3:
                    p.ricar3 = value
                elif gridcol == self.COL_P_ESP1:
                    p.sconto1 = value
                elif gridcol == self.COL_P_ESP2:
                    p.sconto2 = value
                elif gridcol == self.COL_P_ESP3:
                    p.sconto3 = value
                p.Save()
                self.ForceResetView()
        return True
    
    def TestChanges(self, row, gridcol=None, namecol=None):
        assert gridcol is not None or namecol is not None
        if gridcol is None:
            gridcol = self.colnames.index(namecol)
        try:
            if self.listcols[gridcol] in 'p_costo,p_prezzo'.split(','):
                lis = self.dblis
                self.promod[lis.prod.id] = [lis.p_costo, lis.p_prezzo]
                if self.autoricalc:
                    self.RicalcolaPC(row, exclude=self.listcols[gridcol])
                if self.autolistino:
                    self.RicalcolaListini(row)
            else:
                lis = self.dblis
                lis.MoveRow(row)
                lis.data = Env.Azienda.Login.dataElab
            if not row in self.modrows:
                self.modrows.append(row)
        except KeyError:
            pass
    
    def OnCallProd(self, event):
        rows = self.GetSelectedRows()
        if len(rows) == 0:
            return
        row = rows[0]
        try:
            self.dblis.MoveRow(row)
            wx.BeginBusyCursor()
            dlg = ProdDialog(self, onecodeonly=self.dblis.prod.id)
            dlg.OneCardOnly(self.dblis.prod.id)
            dlg.CenterOnScreen()
            ret = dlg.ShowModal()
            wx.EndBusyCursor()
            dlg.Destroy()
            if ret>0:
                evt = ProdChangedEvent(_evtPRODCHANGED, self.GetId())
                evt.SetEventObject(self)
                evt.SetId(self.GetId())
                self.GetEventHandler().AddPendingEvent(evt)
        except:
            pass


# ------------------------------------------------------------------------------


class ColonneDaStampareDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        self.unique = False
        p = aw.Panel(self)
        wdr.ColonneDaStampareFunc(p)
        self.AddSizedPanel(p)
        def cn(x):
            return self.FindWindowByName(x)
        for l in range(1,10):
            name = 'prezzo%d' % l
            cn(name).Enable(l<=bt.MAGNUMLIS)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wdr.ID_OKPRINT)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
    
    def SetUnique(self, u):
        self.unique = u
    
    def OnCheckBox(self, event):
        if self.unique:
            o = event.GetEventObject()
            for c in self.GetAllChildren():
                if isinstance(c, wx.CheckBox) and c is not o:
                    c.SetValue(False)
        event.Skip()
    
    def OnOk(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class ListiniPanel(aw.Panel, aw.awu.LimitiFiltersMixin):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.ListiniFunc(self)
        
        aw.awu.LimitiFiltersMixin.__init__(self)
        
        def ci(x):
            return self.FindWindowById(x)
        def cn(x):
            return self.FindWindowByName(x)
        
        self.dblis = dbm.Listino()
        self.dbsin = dbm.ListinoSintesi()
        self.dbpro = dbm.Prodotti()
        
        lis = self.dblis
        
        ALS = self.AddLimitiFiltersSequence
        ALS(lis, 'prod',   'codice')
        ALS(lis, 'prod',   'descriz')
        ALS(lis, 'status', 'id_status')
        ALS(lis, 'catart', 'id_catart')
        ALS(lis, 'gruart', 'id_gruart')
        ALS(lis, 'tipart', 'id_tipart')
        ALS(lis, 'fornit', 'id_fornit')
        
        self.dataval = None
        self.listchanged = False
        self.sololist = False
        
        self.gridsin = SintesiGrid(ci(wdr.ID_PANGRIDSIN), self.dbsin)
        self.gridlis = ListiniGrid(ci(wdr.ID_PANGRIDLIS), self.dblis)
        
        if bt.MAGNUMLIS == 0 or not bt.MAGDATLIS:
            ci(wdr.ID_PANSINT).Hide()
            if bt.MAGNUMLIS == 0:
                for cid in (wdr.ID_RICALCALL, wdr.ID_RICALCLIST, wdr.ID_SOLOLIST):
                    ci(cid).Hide()
            self.Layout()
        
        ci(wdr.ID_NEWDATA).Hide()
        ci(wdr.ID_NEWDATALABEL).Hide()
        
        self.gridsin.Bind(gl.EVT_GRID_SELECT_CELL, self.OnUpdateData)
        self.gridlis.Bind(gl.EVT_GRID_CELL_CHANGE, self.OnListChanged)
        self.gridlis.Bind(EVT_LISTCHANGED, self.OnListChanged)
        
        cn = lambda x: self.FindWindowByName(x)
        self.Bind(dc.EVT_DATECHANGED, self.OnData, cn('data'))
        self.Bind(EVT_PRODCHANGED, self.OnProdChanged)
        
        for cid, func in ((wdr.ID_UPDATE,     self.OnUpdateSin),
                          (wdr.ID_RICALCALL,  self.OnRicalcAll),
                          (wdr.ID_RICALCPC,   self.OnRicalcPC),
                          (wdr.ID_RICALCLIST, self.OnRicalcList),
                          (wdr.ID_VARIAPERC,  self.OnVariaPerc),
                          (wdr.ID_RESET,      self.OnReset),
                          (wdr.ID_COPYLIS,    self.OnCopyList),
                          (wdr.ID_CANCLIST,   self.OnDeleteList),
                          (wdr.ID_PRINTLIS,   self.OnPrintList),
                          (wdr.ID_SAVELIST,   self.OnSaveList),
                          (wdr.ID_ACQLIST,    self.OnAcqCSV),):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        for cid, func in ((wdr.ID_SOLOLIST,    self.OnSoloList),
                          (wdr.ID_AUTORICALC,  self.OnAutoRicalc),
                          (wdr.ID_AUTOLISTINO, self.OnAutoList)):
            self.Bind(wx.EVT_CHECKBOX, func, id=cid)
        
        self.Bind(gl.EVT_GRID_CELL_CHANGE, self.OnGridChanged)
        
        self.SetName('listinipanel')
    
    def OnAcqCSV(self, event):
        self.AcqCSV()
        event.Skip()
    
    def AcqCSV(self):
        dlg = wx.FileDialog(self,\
                            message="Seleziona il file da acquisire",\
                            defaultDir = "C:/",\
                            defaultFile = "listino.csv",\
                            wildcard = "File listino (*.CSV)|*.CSV",\
                            style=wx.OPEN)
        filename = None
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()
        if filename is None:
            return
        try:
            h = open(filename)
        except IOError, e:
            aw.awu.MsgDialog(self, message="Problema in apertura file csv:\n%s"\
                             % repr(e.args))
            return
        cfg = Env.Azienda.config
        reader = csv.reader(h, 
                            delimiter=cfg.DataExport_csvdelimiter,
                            quotechar=cfg.DataExport_csvquotechar,
                            quoting=int(cfg.DataExport_csvquoting))
        csvtab = None
        rs = []
        for n,row in enumerate(reader):
            if n == 0:
                csvtab = dbm.AcqListino(','.join(row))
            else:
                rs.append(row)
        if csvtab is not None:
            try:
                csvtab.SetRecordset(rs)
            except AssertionError:
                aw.awu.MsgDialog(self, "Formato di file non confacente")
                return
            wait = aw.awu.WaitDialog(self, message="Estrazione listino in corso",
                                     maximum=csvtab.RowsCount()*2)
            do = False
            try:
                try:
                    csvtab.epura(lambda n: wait.SetValue(n))
                    do = True
                except Exception, e:
                    MsgBox(self, repr(e.args))
                if do:
                    wait.SetMessage('Aggiornamento valori in corso...')
                    lis = self.dblis
                    rslis = lis.GetRecordset()
                    cols = {}
                    for col in 'codice,codfor,barcode'.split(','):
                        cols[col] = lis.prod._GetFieldIndex(col, inline=True)
                    changed = False
                    #creazione dizionari chiavi x identificazione del prodotto
                    def cn(x):
                        return lis.prod._GetFieldIndex(x, inline=True)
                    colcod = cn('codice')
                    colcof = cn('codfor')
                    colbar = cn('barcode')
                    codes_int = {} #codice interno
                    codes_for = {} #codice fornitore
                    codes_bar = {} #codice a barre
                    for n,l in enumerate(rslis):
                        codes_int[l[colcod]] = n
                        if l[colcof]:
                            codes_for[l[colcof]] = n
                        if l[colbar]:
                            codes_int[l[colbar]] = n
                    
                    for a,acq in enumerate(csvtab):
                        cod = acq.codice
                        if cod in codes_int:
                            m = codes_int
                        elif cod in codes_for:
                            m = codes_for
                        elif cod in codes_bar:
                            m = codes_bar
                        else:
                            m = None
                        if m:
                            lis.MoveRow(m[cod])
                            for col in csvtab._info.cols:
                                if col != 'codice':
                                    if col in 'costo,prezzo'.split(','):
                                        colw = 'p_'+col
                                    else:
                                        colw = col
                                    setattr(lis, colw, getattr(acq, col))
                                    self.gridlis.TestChanges(lis.RowNumber(),
                                                             namecol=colw)
                                    changed = True
                        wait.SetValue(csvtab.RowsCount()+a)
                    if changed:
                        self.SetListChanged(True)
                        self.gridlis.Refresh()
            finally:
                wait.Destroy()
        return
    
    def OnDeleteList(self, event):
        self.DeleteList()
        event.Skip()
    
    def DeleteList(self):
        def ci(x):
            return self.FindWindowById(x)
        dat = ci(wdr.ID_DATA).GetValue()
        if dat is None:
            MsgBox(self, "Data vuota, cancellazione non possibile")
            return False
        if MsgBox(self, "Confermi la cancellazione dei prezzi validi al %s ?"\
                  % adb.DbTable.dita(dat), 
                  style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            wait = aw.awu.WaitDialog(self, 
                                     message="Eliminazione listini in corso...",
                                     maximum=self.dblis.RowsCount())
            try:
                rs = []
                lids = []
                for l, lis in enumerate(self.dblis):
                    if lis.id is not None:
                        rs.append(copy.deepcopy(lis.GetRecordset()[l]))
                        lids.append(lis.id)
                    wait.SetValue(l)
            finally:
                wait.Destroy()
            out = True
            lis = self.dblis
            lis.SetRecordset(rs)
            lis._info.deletedRecords += lids
            if not lis.Save():
                MsgBox(self, repr(lis.GetError()))
                out = False
            self.UpdateSintesi()
    
    def OnCopyList(self, event):
        def ci(x):
            return self.FindWindowById(x)
        if ci(wdr.ID_NEWDATA).IsShown():
            self.CopiaListino()
        else:
            ci(wdr.ID_NEWDATA).SetValue(None)
            ci(wdr.ID_NEWDATA).Show()
            ci(wdr.ID_NEWDATA).SetFocus()
            ci(wdr.ID_NEWDATALABEL).Show()
            ci(wdr.ID_DATA).Disable()
            ci(wdr.ID_UPDATE).Disable()
            ci(wdr.ID_SAVELIST).Disable()
            ci(wdr.ID_COPYLIS).SetLabel('&Genera')
            ci(wdr.ID_COPYLIS).SetToolTipString(\
                "Conferma la generazione dei nuovi prezzi")
        event.Skip()
    
    def CopiaListino(self):
        newdat = self.FindWindowById(wdr.ID_NEWDATA).GetValue()
        if newdat is None:
            MsgBox(self, message="Data errata", style=wx.ICON_ERROR)
            return False
        sin = self.dbsin
        if sin.Locate(lambda s: s.data == newdat):
            MsgBox(self, "La data esiste già")
            return False
        out = False
        if MsgBox(self, message=\
                  """Confermi la copia dei listini visualizzati nella nuova """
                  """data del %s ?""" % adb.DbTable.dita(newdat),
                  style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
            wait = aw.awu.WaitDialog(self, message="copia listini in corso...",
                                     maximum=self.dblis.RowsCount())
            try:
                rs = []
                for l, lis in enumerate(self.dblis):
                    if lis.id_prod is not None and not lis.IsEmpty():
                        lis.id = None
                        lis.data = newdat
                        rs.append(copy.deepcopy(lis.GetRecordset()[l]))
                    wait.SetValue(l)
            finally:
                wait.Destroy()
            out = True
            lis = self.dblis
            lis.SetRecordset(rs)
            if not lis.Save():
                MsgBox(self, repr(lis.GetError()))
                out = False
            self.UpdateSintesi()
            if sin.Locate(lambda s: s.data == newdat):
                self.gridsin.SelectRow(sin.RowNumber())
        return out
    
    def OnVariaPerc(self, event):
        self.gridlis.VariaPerc()
        event.Skip()
    
    def OnGridChanged(self, event):
        self.ListNav(False)
        event.Skip()
    
    def ListNav(self, e=True):
        def ci(x):
            return self.FindWindowById(x)
        ci(wdr.ID_DATA).Enable(e)
        ci(wdr.ID_PANGRIDSIN).Enable(e)
        ci(wdr.ID_NEWDATA).Hide()
        ci(wdr.ID_NEWDATALABEL).Hide()
        ci(wdr.ID_COPYLIS).SetLabel('&Copia')
        ci(wdr.ID_COPYLIS).SetToolTipString(\
            "Permette la copia dei prezzi visualizzati in una nuova data")
    
    def OnPrintList(self, event):
        self.PrintListino()
        event.Skip()
    
    def SetColumnsToPrint(self, rptdef, *args):
        out = None
        unique = '1 prezzo' in rptdef
        lis = self.dblis
        if bt.MAGNUMLIS == 0 or not bt.MAGDATLIS:
            lis._datlis = Env.Azienda.Login.dataElab
        else:
            lis._datlis = self.FindWindowById(wdr.ID_DATA).GetValue()
        lis._deslis = "Prezzi validi a partire dal:"
        dlg = ColonneDaStampareDialog(self, -1, 'Stampa listini')
        dlg.SetUnique(unique)
        do = False
        nc = 0
        if dlg.ShowModal() == wx.ID_OK:
            out = lis
            for name in ['p_costo','p_prezzo']+['prezzo%d'%l for l in range(1,10)]:
                tl = dbm.dba.TipoListino()
                x = dlg.FindWindowByName(name).GetValue()
                k = lis.Columns()[name]
                if name == 'p_costo':
                    t = 'Costo acquisto'
                elif name == 'p_prezzo':
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
                MsgBox(self, message=\
                       """Devi selezionare almeno una colonna, altrimenti """
                       """diventa una lista prodotti e non una stampa di """
                       """listino!!!""",
                       style=wx.ICON_WARNING)
                out = None
            elif unique and nc>1:
                MsgBox(self, message=\
                       """Devi selezionare solo una colonna.""",
                       style=wx.ICON_INFORMATION)
                out = None
        dlg.Destroy()
        return out
    
    def PrintListino(self):
        name = 'Listino prezzi'
        cn = self.FindWindowByName
        r = cn('raggruppam').GetValue()
        if r == "C":
            #raggruppamento per categoria
            name += ' per categoria'
        elif r == "G":
            #raggruppamento per categoria
            name += ' per categoria e gruppo'
        def setEjectPage(rptdef, dbt):
            pass
        if r in 'CG':
            msg = "Salto pagina ad ogni categoria?"
            stl = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
            if aw.awu.MsgDialog(self, msg, style=stl) == wx.ID_YES:
                def setEjectPage(rptdef, dbt):
                    groups = rptdef.lGroup
                    for g in groups:
                        if groups[g].name == 'catart':
                            groups[g].isStartNewPage = 'true'
        rpt.Report(self, self.dblis, name, dbfunc=self.SetColumnsToPrint,
                   startFunc=setEjectPage)
    
    def OnReset(self, event):
        self.ResetList()
        event.Skip()
    
    def TestDataSaved(self):
        g = self.gridlis
        do = True
        if g.GetModifiedRows() or g.GetProMod():
            do = False
            if MsgBox(self, 
                      message="Ci sono dati non salvati.Procedo comunque?",
                      style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                do = True
        return do
    
    def ResetList(self):
        def ci(x):
            return self.FindWindowById(x)
        ci(wdr.ID_NEWDATA).Hide()
        ci(wdr.ID_NEWDATALABEL).Hide()
        ci(wdr.ID_UPDATE).Enable()
        if self.TestDataSaved():
            self.UpdateListini()
            self.ListNav(True)
            c = self.FindWindowById(wdr.ID_DATA)
            c.Enable()
            c.SetFocus()
    
    def OnAutoRicalc(self, event):
        self.gridlis.SetAutoRicalc(event.GetSelection())
        event.Skip()
    
    def OnAutoList(self, event):
        self.gridlis.SetAutoListino(event.GetSelection())
        event.Skip()
    
    def OnRicalcAll(self, event):
        self.gridlis.RicalcolaTutto()
        event.Skip()
    
    def OnRicalcPC(self, event):
        self.gridlis.RicalcolaPC()
        event.Skip()
    
    def OnRicalcList(self, event):
        self.gridlis.RicalcolaListini()
        event.Skip()
    
    def OnProdChanged(self, event):
        self.UpdateListini()
        event.Skip()
    
    def OnSoloList(self, event):
        self.sololist = event.GetEventObject().GetValue()
        self.UpdateListini()
        event.Skip()
    
    def OnListChanged(self, event):
        self.SetListChanged(True)
        event.Skip()
    
    def SetListChanged(self, changed=True):
        self.listchanged = changed
        def cn(x):
            return self.FindWindowById(x)
        cn(wdr.ID_SAVELIST).Enable(changed)
    
    def OnData(self, event):
        data = event.GetEventObject().GetValue()
        if data is not None and data.year>2000:
            self.dataval = data
            self.UpdateListini()
            self.gridlis.Enable(data is not None)
            event.Skip()
    
    def OnUpdateSin(self, event):
        if not self.TestDataSaved():
            return
        if bt.MAGDATLIS:
            self.UpdateSintesi()
        #workaround: il cambio del contenuto grid sintesi non scatena l'evento
        #di selezione riga, con conseguente non aggiornamento della data e
        #quindi del listino :(
        self.UpdateListini()
        event.Skip()
    
    def OnUpdateData(self, event):
        if not self.TestDataSaved():
            return
        sin = self.dbsin
        try:
            sin.MoveRow(event.GetRow())
        except:
            pass
        self.SetDataVal(sin.data)
        event.Skip()
    
    def SetDataVal(self, data):
        self.FindWindowByName('data').SetValue(data)
    
    def UpdateSintesi(self):
        self.ApplyFilters(self.dbsin, self.gridsin, riep=True)
    
    def UpdateListini(self):
        cn = self.FindWindowByName
        ordinam = cn('ordinam').GetValue()
        raggruppam = cn('raggruppam').GetValue()
        lis = self.dblis
        lis.ClearOrders()
        if raggruppam == "C":
            lis.AddOrder('catart.codice')
        elif raggruppam == "G":
            lis.AddOrder('catart.codice')
            lis.AddOrder('gruart.codice')
        if ordinam == "C":
            lis.AddOrder('prod.codice')
        elif ordinam == "D":
            lis.AddOrder('prod.descriz')
        elif ordinam == "F":
            lis.AddOrder('prod.codfor')
            lis.AddOrder('prod.codice')
        lis.AddOrder('lis.data', adb.ORDER_DESCENDING)
        self.ApplyFilters(lis, self.gridlis, riep=False)
        self.SetListChanged(False)
        self.FindWindowById(wdr.ID_DATA).Enable()
        for cid in (wdr.ID_NEWDATALABEL, wdr.ID_NEWDATA):
            self.FindWindowById(cid).Hide()

    def ApplyFilters(self, lis, grid, riep):
        cn = lambda x: self.FindWindowByName(x)
        lis.ClearFilters()
        if not riep:
            r = lis.prod._info.relation
            r.joinType = adb.JOIN_RIGHT
            expr = "lis.id_prod=prod.id"
            if bt.MAGDATLIS and self.dataval:
                #dl = adb.DateTime.ISO.str(self.dataval)[:10]
                dl = self.dataval.FormatANSI()[:10]
                try:
                    addexpr = ' AND (lis.data="%s"' % dl
                    if self.sololist:
                        lis.AddFilter('lis.data="%s"' % dl)
                    else:
                        addexpr += " OR lis.data IS NULL"
                    addexpr += ")"
                    expr += addexpr
                except:
                    return
            elif not bt.MAGDATLIS and self.sololist:
                expr += " AND (%s) " % " OR ".join(["lis.prezzo%d<>0"%(n+1) for n in range(bt.MAGNUMLIS)])
                r.joinType = adb.JOIN_ALL
            r.expression = expr
        self.LimitiFiltersApply()
        ssv = cn('ssv').GetValue()
        if ssv:
            lis.AddFilter('status.hidesearch IS NULL OR status.hidesearch<>1')
        if cn('excl0cos').IsChecked():
            lis.AddFilter('prod.costo<>0')
        if cn('excl0pre').IsChecked():
            lis.AddFilter('prod.prezzo<>0')
        wx.BeginBusyCursor()
        lis.Retrieve()
        wx.EndBusyCursor()
        grid.ChangeData(lis.GetRecordset())
    
    def OnSaveList(self, event):
        if self.Validate():
            self.SaveListini()
            data = self.dataval
            self.UpdateSintesi()
            if self.dbsin.Locate(lambda x: x.data == data):
                self.gridsin.SetGridCursor(self.dbsin.RowNumber(),0)
        event.Skip()
    
    #def TestValori(self, x):
        #cp1 = self.dblis._GetFieldIndex('prezzo1', inline=True)
        #v = 0
        #for c in range(6):
            #v += (x[cp1+c] or 0)
        #return v
    
    def Validate(self):
        out = True
        #try:
            #aw.awu.ListSearch(self.dblis.GetRecordset(), self.TestValori)
        #except:
            #if aw.awu.MsgDialog(self, message=\
                                #"""Nessun è presente alcun prezzo: se si è """\
                                #"""in modifica, l'intero listino verrà """\
                                #"""eliminato.\n\nConfermi?""",
                                #style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_NO:
                #out = False
        return out
    
    def SaveListini(self):
        out = False
        lis = self.dblis
        rs = lis.GetRecordset()
        n = len(rs)-1
        #aggiornamento tabella listini
        wx.BeginBusyCursor()
        try:
            rs = []
            mr = self.gridlis.GetModifiedRows()
            di = copy.copy(self.dblis._info.deletedRecords)
            sf = adb.DbTable.samefloat
            data = self.FindWindowByName('data').GetValue()
            for row in mr:
                lis.MoveRow(row)
                if lis.IsEmpty():
                    if lis.id and not lis.id in di:
                        di.append(lis.id)
                else:
                    lis.id_prod = lis.prod.id
                    if bt.MAGDATLIS:
                        lis.data = data
                    rs.append(copy.deepcopy(lis.GetRecordset()[row]))
            lis.Reset()
            lis.WriteAll()
            lis._info.deletedRecords += di
            lis.SetRecordset(rs)
            out = lis.Save()
        finally:
            wx.EndBusyCursor()
        if out:
            #aggiornamento costo/prezzo su schede prodotto
            wx.BeginBusyCursor()
            try:
                pro = self.dbpro
                pm = self.gridlis.GetProMod()
                for pid in pm:
                    if pro.Get(pid) and pro.OneRow():
                        w = False
                        for n, col in enumerate('costo,prezzo'.split(',')):
                            pv = getattr(pro, col)
                            lv = pm[pid][n]
                            if not sf(pv, lv):
                                setattr(pro, col, lv)
                                w = True
                        if w:
                            pro.Save()
            finally:
                wx.EndBusyCursor()
        if out:
            self.UpdateListini()
        else:
            MsgBox(self, message=repr(lis.GetError()))
        return out
    

# ------------------------------------------------------------------------------


class ListiniFrame(aw.Frame):
    """
    Frame gestione listini di vendita.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ListiniPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ListiniDialog(aw.Dialog):
    """
    Dialog gestione listini di vendita.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ListiniPanel(self, -1))
        self.CenterOnScreen()
