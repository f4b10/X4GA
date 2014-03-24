#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/dbgrid.py
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
from wx.grid import GRID_VALUE_NUMBER, GRID_VALUE_FLOAT, GRID_VALUE_DATETIME,\
    GRID_VALUE_STRING, GRID_VALUE_CHOICE, GRID_VALUE_CHOICEINT

"""
Presentazione e/o editazione valori in formato griglia.
"""

import csv
CSVFORMAT_ASGRID = 0
CSVFORMAT_DELIMITER = ','
CSVFORMAT_QUOTECHAR = '"'
CSVFORMAT_QUOTING = csv.QUOTE_MINIMAL
CSVFORMAT_EXCELZERO = False

YEAR4 = True

import os, tempfile
import subprocess

import locale

import wx
import wx.grid as gridlib

import awc.controls.dbgrideditors as awg
#import awc.controls.linktable as lt
from awc.controls import CELLEDIT_AFTER_UPDATE, CELLEDIT_BEFORE_UPDATE

import awc.controls.mixin as cmix
import awc.controls.windows as aw

CELLCOLOR_FOREGROUND = "black"
CELLCOLOR_BACKGROUND = "white"

#costanti di larghezza colonna per nascondere/visualizzare le colonne #id
MINCOLEXPAND = 10 #limite minimo per essere considerata colonna da espandere
STDCOLEXPAND = 60 #larghezza colonna da espandere quando necessario


#TABTRAVERSAL = True  => Il tasto Tab naviga sui controlli prima/dopo la griglia
#TABTRAVERSAL = False => Il tasto Tab naviga sulle celle della griglia
TABTRAVERSAL = True

from mx.DateTime import Date, DateTime, FORMAT_DATE, FORMAT_DATE_SH, FORMAT_DATETIME, FORMAT_DATETIME_SH
import mx.DateTime as dt

import awc.wxinit as wxinit


class DbGrid(gridlib.Grid, cmix.HelpedControl):
    """
    Presentazione e/o editazione valori in formato griglia.
    """
    def __init__(self, *args, **kwargs):
        
        self.tableClass = DbGridTable
        kwtest = "tableClass"
        if kwtest in kwargs:
            if kwargs[kwtest] is not None:
                self.tableClass = kwargs[kwtest]
            kwargs.pop(kwtest)
        
        kwargs['style'] = wx.WANTS_CHARS|wx.TE_PROCESS_ENTER
        
        gridlib.Grid.__init__(self, *args, **kwargs)
        cmix.HelpedControl.__init__(self)
        
        self.SetColMinimalAcceptableWidth(0)
        self.EnableDragRowSize(False)
        
        self._edrow = None
        self._edcol = None
        self._csize = {}
        self._fitColumn = None
        self._anchor_column = None #colonna da ancorare al lato destro della griglia
        self._anchor_resize = None #colonna da ridimensionare per ancorare la colonna precedente
        self._colmap = {}
        self._colmap_check = True
        self._colfunc = None
        self._coldefault = 0
        self._colmaxchars = {}
        self._maximizable = True
        self._maximized = False
        
        self.positioning = False
        self.ratiofactor = 1
        
        self._newrow = None
        self._newcol = None
        
        self._defaultValueCB = None
        
        self._gridcolor_on, self._gridcolor_off = \
            map(lambda col: wx.TheColourDatabase.Find(col), 
                'deepskyblue,gray'.split(','))
        
        _GC = wx.SystemSettings.GetColour
        self._textcolor_sel_on =  _GC(wx.SYS_COLOUR_CAPTIONTEXT)
        self._gridcolor_sel_on =  _GC(wx.SYS_COLOUR_ACTIVECAPTION)
        self._textcolor_sel_off = _GC(wx.SYS_COLOUR_INACTIVECAPTIONTEXT)
        self._gridcolor_sel_off = _GC(wx.SYS_COLOUR_INACTIVECAPTION)
        
        self.DEFAULT_FONT = f = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.FONT_SIZE  = f.GetPointSize()
        
        self.rowheight = wxinit.GetGridRowHeight()
        
        self.SetScrollLineX(1)
        
        self.DrawLines()
        
        self.Bind(gridlib.EVT_GRID_EDITOR_SHOWN, self.OnShowCellEditor)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        
        #workaround: EVT_SET_FOCUS e EVT_KILL_FOCUS non vengono richiamati sul
        #grid, ma sull'ultimo dei suoi figli (grid_window) wxPython 2.6.2.1
        for c in ([self]+list(self.GetChildren())):
            c.Bind(wx.EVT_SET_FOCUS, self.OnFocusGain)
            c.Bind(wx.EVT_KILL_FOCUS, self.OnFocusKill)
        self.Bind(gridlib.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelect)
        self.Bind(wx.EVT_KEY_DOWN, self.OnChar)
        
        self._args = args
        self._kwargs = kwargs
        self._lastdim = [None, None, False]
        self.Bind(wx.EVT_SIZE, self.OnGridResized)
    
    def SetFocus(self):
        self.SetFocusTo()
    
    def SetFocusTo(self):
        list(self.GetChildren())[3].SetFocus()
    
    def SetNotSpecifCols(self, nsc):
        self.GetTable().SetNotSpecifCols(nsc)
    
    def OnChar(self, event):
        do = False
        if event.GetKeyCode() == wx.WXK_TAB:
            if TABTRAVERSAL:
                do = True
                if not do:
                    do = self.GetSelectionMode() == self.wxGridSelectRows
                if not do:
                    do = not self.IsEditable()
            else:
                do = event.ControlDown()
            if do:
                d = wx.NavigationKeyEvent.IsForward
                if event.ShiftDown():
                    d = wx.NavigationKeyEvent.IsBackward
                self.Navigate(d)
        if not do:
            #if event.GetKeyCode() == wx.WXK_RETURN and event.ControlDown():
            if event.GetKeyCode() == wx.WXK_RETURN and event.ShiftDown():
                self.SetGridCursorNewRowCol()
            else:
                event.Skip()
    
    def SetGridCursorNewRowCol(self):
        if not self.canIns:
            return
        data = self.GetTable().data
        if len(data)>0:
            row, col = len(data), self._coldefault
            self.SetGridCursor(row, col)
            self.MakeCellVisible(row, col)
    
    def SetColDefault(self, cd):
        self._coldefault = cd
    
    def OnCellSelect(self, event):
        if self.FindFocus() in self.GetChildren():
            self.DrawLines(True)
        event.Skip()
    
    def OnFocusGain(self, event):
        self.FocusGained()
        event.Skip()
        
    def FocusGained(self):
        self.DrawLines(True)
        self.Refresh()
    
    def OnFocusKill(self, event):
        self.FocusKilled()
        event.Skip()
    
    def FocusKilled(self):
        self.DrawLines()
        self.Refresh()
    
    def DrawLines(self, focused=False):
        if focused:
            tx = self._textcolor_sel_on
            cb = self._gridcolor_sel_on
            cl = self._gridcolor_on
        else:
            tx = 'white'#self._textcolor_sel_off #pare che senza focus la riga di selezione abbia sempre background grigio
            cb = self._gridcolor_sel_off
            cl = self._gridcolor_off
        self.SetSelectionForeground(tx)
        self.SetSelectionBackground(cb)
        self.SetGridLineColour(cl)
    
    def Reset(self):
        self.ChangeData(())
    
    def OnLabelRightClick(self, event):
        x, y = list(event.GetPosition())
        self._Grid_MenuPopup(x,y)
        event.Skip()
    
    def _Grid_MenuPopup(self, x, y):
        hascte = hasctc = False
        for col in range(self.GetNumberCols()):
            if self.GetColSize(col)<MINCOLEXPAND:
                hascte = True
                hasctc = False
                break
            if self.GetColLabelValue(col).startswith('#'):
                hasctc = True
        voci = []
        menu = wx.Menu()
        for flag, text, func in (
            (hascte, "Mostra colonne nascoste", self.OnExpandHiddenColumns),
            (hasctc, "Nascondi colonne #id",    self.OnHideIdColumns)):
            if flag:
                voci.append((text, func, True))
        data = self.GetTable().data
        if data:
            voci.append(("Esporta file CSV (%d righe)" % len(data), self.OnExportCSV, True))
        for text, func, enab in voci:
            if text is None:
                menu.AppendSeparator()
                continue
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        self.PopupMenu(menu, (x, y-20))
        menu.Destroy()
    
    def OnExportCSV(self, event):
        self.GetTable().ExportCSV()
        event.Skip()
    
    def OnExpandHiddenColumns(self, event):
        self.ExpandHiddenColumns()
        event.Skip()
    
    def ExpandHiddenColumns(self):
        for col in range(self.GetNumberCols()):
            if self.GetColSize(col)<MINCOLEXPAND:
                self.SetColSize(col, STDCOLEXPAND)
        self.ResetView()
    
    def OnHideIdColumns(self, event):
        self.HideIdColumns()
        event.Skip()
    
    def HideIdColumns(self):
        for col in range(self.GetNumberCols()):
            text = self.GetColLabelValue(col)
            if text.startswith('#'):
                self.SetColSize(col, 1)
        self.ResetView()
    
    def SetRatioFactor(self, n):
        self.ratiofactor = n
        self.SetRowScrollRatio()
    
    def Enable(self, e=True):
        pass
        #if self.CanEnableCellControl():
            #self.EnableCellEditControl(e)
    
    def Disable(self):
        self.Enable(False)
    
    def SetBackgroundColour(self, color):
        gridlib.Grid.SetBackgroundColour(self, color)
        self.SetDefaultCellBackgroundColour(color)
    
    def SetColumnsMap(self, cm):
        self._colmap = cm
    
    def SetColumnsFunc(self, cf):
        self._colfunc = cf
    
    def TestNewColumn(self, row, col):
        newrow = newcol = None
        if self._colfunc is not None:
            newrow, newcol = self._colfunc(self, row, col)
        elif col in self._colmap:
            newcol = self._colmap[col]
        if newrow is None:
            newrow = row
        if newcol is None:
            if col<(self.GetNumberCols()-1):
                newcol = col+1
        if newrow is not None and newcol is not None:
            self.SetGridCursor(newrow, newcol)
    
    def SetGridCursor(self, row, col):
        if not self.positioning:
            self.positioning = True
            gridlib.Grid.SetGridCursor(self, row, col)
            self.positioning = False
    
    def SetDefaultValueCB(self, d):
        self._defaultValueCB = d
    
    def GetDefaultValueCB(self):
        return self._defaultValueCB
    
    def SetFitColumn(self, colno):
        self._fitColumn = colno
#        if colno is not None:
#            #for evt in (wx.EVT_SIZE, wx.EVT_MAXIMIZE):
#            evt = wx.EVT_SIZE
#            if True:
#                #self.GetParent().Bind(evt, self.OnGridResized)
#                self.Bind(evt, self.OnGridResized)
    
    def SetAnchorColumns(self, a_column, a_resize):
        if not isinstance(a_resize, (list, tuple)):
            a_resize = [a_resize]
        self._anchor_column = a_column
        self._anchor_resize = a_resize
    
    def OnGridResized(self, event):
#        if self._fitColumn is not None:
#            self.FitColumn()
        f = aw.awu.GetParentFrame(self)
        if f.IsShown():
            dim = aw.awu.GetParentFrame(self).GetSize()
            ld = self._lastdim
            fit = True
            if ld[0] is None or dim[0] != ld[0] or ld[2] != f.IsMaximized():
                self.AutoSizeColumns()
                fit = False
            self._lastdim[0] = dim[0]
            self._lastdim[1] = dim[1]
            self._lastdim[2] = f.IsMaximized()
            if fit:
                self.FitColumn()
        event.Skip()
    
    def FitColumn(self):
        if self._fitColumn is None:
            return
        numcols = self.GetNumberCols()
        if self._fitColumn<0:
            c2fit = numcols+self._fitColumn
        else:
            c2fit = self._fitColumn
        wtot = sum([self.GetColSize(n) for n in range(numcols) if n != c2fit])
        wtot += self.GetRowLabelSize()
        #wcl = self.GetClientSize()[0]
        wcl = self.GetVirtualSize()[0]
        if wtot < wcl:
            csize = wcl-wtot
        else:
            csize = 30
        if c2fit in self._csize:
            csize = max(csize, self._csize[c2fit])
        self.SetColSize(c2fit, csize)
    
    def AnchorColumn(self):
        if self._anchor_column is None:
            return False
        if aw.awu.GetParentFrame(self).IsMaximized():
            #frame massimizzato: invece di ancorare la colonna,
            #resetto le larghezze delle colonne da resizare in ancoramento
            #ai rispettivi valori impostati come larghezza iniziale
            for col in self._anchor_resize:
                self.SetColSize(col, self._csize[col])
            return False
        a_col = self._anchor_column
        a_siz = self._anchor_resize
        wtot = self.GetRowLabelSize() or 0
        for col in range(a_col+1):
            if not col in a_siz:
                wtot += self.GetColSize(col)
        wmax = self.GetVirtualSize()[0]
        if wtot<wmax:
            wdif = wmax-wtot
            waum = 0
            sizes = []
            for col in a_siz:
                w =  self._csize[col]
                sizes.append(w)
                waum += w
            wcol = 0
            while waum<wdif:
                sizes[wcol] += 1
                waum += 1
                wcol += 1
                if wcol>=len(sizes):
                    wcol = 0
            for c, col in enumerate(a_siz):
                self.SetColSize(col, sizes[c])
            return True
        return False
    
    def AddTotalsRow(self, *args, **kwargs):
        """
        Aggiunge una riga di totali.
        lblcol #col. label
        lbl    label
        cols   lista colonne da totalizzare
        cbfilt callback filtro di applicazione dei totalizzatori x ogni riga
        """
        table = self.GetTable()
        if table:
            return table.AddTotalsRow(*args, **kwargs)
    
    def GetTotalsRows(self):
        table = self.GetTable()
        if table:
            return table.GetTotalsRows()
    
    def SetGetExternal(self, rscol, getExternal):
        table = self.GetTable()
        if table:
            table.SetGetExternal(rscol, getExternal)

    def ResetColumnsDefaultSize(self, col, size):
        self._csize = {}
    
    def SetColumnDefaultSize(self, col, size):
        if size>0:
            self._csize[col] = size
    
    def AutoSizeColumns(self, *args, **kwargs):
        
        if self._csize:
            for col in self._csize:
                if self._csize[col]>-1:
                    self.SetColSize(col, self._csize[col])
        else:
            gridlib.Grid.AutoSizeColumns(self, *args, **kwargs)
        
        tab = self.GetTable()
        
        try:
            dummy = wx.TextCtrl(self, -1)
            dummy.Hide()
        except:
            dummy = None
        
        for col, size in self._csize.iteritems():
            
            spec = tab.dataTypes[col].split(':')
            col_type = spec[0]
            col_char = None
            
            if col_type in (gridlib.GRID_VALUE_NUMBER,
                            gridlib.GRID_VALUE_LONG,):
                try:
                    _len = int(spec[1].split(",")[0])
                except:
                    _len = 10
                
            elif col_type == gridlib.GRID_VALUE_FLOAT:
                _len = int(spec[1].split(",")[0])
                try:
                    _dec = int(spec[1].split(",")[1])
                except:
                    _dec = 2
                test = 10**_len-1
                if _dec:
                    test += 1/(10**_dec)
                _len = len(locale.format("%%.%df" % _dec, test, True, monetary=True))
                
            elif col_type == gridlib.GRID_VALUE_DATETIME:
                try:
                    #classe mx.DateTime
                    if len(spec) == 1:
                        if YEAR4:
                            m = FORMAT_DATE
                        else:
                            m = FORMAT_DATE_SH
                        _len = len(dt.today().Format(m))
                    else:
                        if YEAR4:
                            m = FORMAT_DATETIME
                        else:
                            m = FORMAT_DATETIME_SH
                        _len = len(dt.today().Format(m))
                except Exception:
                    _len = 10
                
            else:
                _len = None
            
            if _len and dummy is not None:
                dummy.SetFont(self.colFont[col])
                sizing_text = 'M' * _len
                if wx.Platform != "__WXMSW__":   # give it a little extra space
                    sizing_text += 'M'
                if wx.Platform == "__WXMAC__":   # give it even a little more...
                    sizing_text += 'M'
                w, h = dummy.GetTextExtent(sizing_text)
                size = w
                size += 8
                if wx.Platform == '__WXMSW__':
                    size += 4
                self._csize[col] = size
            
            self.SetColMinimalWidth(col, 15)
            self.SetColSize(col, size)
        
        if dummy is not None:
            dummy.Destroy()
        
        fit = True
        if self._anchor_column is not None:
            fit = not self.AnchorColumn()
        
        if fit and self._fitColumn is not None:
            self.FitColumn()

    def _MultiParam(self, param, classAttr):
        #unico elemento passato come singolo attributo
        if hasattr(param, '_GetParams'):
            param = [param._GetParams(),]
        
        #unico elemento passato come lista di argomenti
        if type(param) in (list, tuple):
            if type(param[0]) is int:
                param = [param,]
        
        #+ elementi passati come lista di attributi
        if type(param) in (list, tuple):
            for n in range(len(param)):
                if hasattr(param[n], '_GetParams'):
                    param[n] = param[n]._GetParams()
        
        return param
    
    def SetData(self, rs, colmap, canEdit = False, canIns = False,\
                linktables = None, afterEdit = None, newRowFunc = None,\
                editors = None):
        
        if self._colmap_check:
            assert not filter(lambda x: x[0] is None, colmap)
        
        canIns = canIns and (newRowFunc is not None)
        
        linktables = self._MultiParam(linktables, LinkTabAttr)
        afterEdit = self._MultiParam(afterEdit, AfterEditAttr)
        
        if type(editors) in (list, tuple):
            if not type(editors[0]) in (list, tuple):
                editors = (editors,)
        
        #table = DbGridTable(self, rs, colmap, canIns, afterEdit, newRowFunc)
        table = self.tableClass(\
            self, rs, colmap, canIns, afterEdit, newRowFunc)
        
        self.canEdit = canEdit
        self.canIns = canIns
        
        self.SetTable(table, True)
        self.SetRowLabelSize(0)
        self.SetColLabelSize(20)
        self.SetMargins(0,0)
        
        self.EnableEditing(canEdit)
        if not canEdit:
            self.SetSelectionMode(self.SelectRows)
            def OnCellSelected(event, *args):
                self.SelectRow(event.GetRow())
                event.Skip()
            self.Bind(gridlib.EVT_GRID_SELECT_CELL, OnCellSelected)
            if table.GetNumberRows()>0:
                self.SelectRow(0)
        
        assert isinstance(rs, (list, tuple)),\
            "Il recordset deve essere una lista o una tupla"
        
        #attributi delle colonne
        self.colAttr = []
        
        #font delle colonne
        self.colFont = []
        
        for col in range(len(table.dataTypes)):
            
            spec = table.dataTypes[col].split(':')
            _type = spec[0]
            attr = gridlib.GridCellAttr()
            attr_editor = None
            attr_render = None
            attr_align = wx.LEFT
            attr_font = None
            
            #determinazione editor
            if editors is not None:
                for ed_col,ed_class in editors:
                    if ed_col == col:
                        #editor personalizzato
                        attr_editor = ed_class
            
            if attr_editor is None:
                if _type == gridlib.GRID_VALUE_NUMBER:
                    try:
                        _len = int(spec[1].split(",")[0])
                    except:
                        _len = 10
                    _dec = 0
                    #std editor numero intero
                    attr_editor = awg.NumericCellEditor(_len, _dec)
                    
                elif _type == gridlib.GRID_VALUE_FLOAT:
                    _len = int(spec[1].split(",")[0])
                    _dec = int(spec[1].split(",")[1])
                    #std editor numero con decimail
                    #attr_editor = gridlib.GridCellFloatEditor(_len, _dec)
                    attr_editor = awg.NumericCellEditor(_len, _dec)
                    
                elif _type == gridlib.GRID_VALUE_DATETIME:
                    #std editor data
                    if len(spec) == 1:
                        attr_editor = awg.DateCellEditor()
                        attr_align = wx.LEFT
                    else:
                        attr_editor = awg.DateTimeCellEditor()
                    
                elif _type in (gridlib.GRID_VALUE_BOOL, 
                               gridlib.GRID_VALUE_CHOICE):
                    if _type == gridlib.GRID_VALUE_BOOL:
                        e = awg.CheckBoxCellEditor
                    else:
                        e = awg.FlatCheckBoxCellEditor
                    #std editor checkbox
                    try:
                        values = spec[1].split(",")
                        attr_editor = e(eval(values[0]), eval(values[1]))
                        attr_render = awg.CheckBoxCellRenderer()
                        if e is awg.FlatCheckBoxCellEditor:
                            self.Bind(wx.EVT_CHAR, attr_editor.OnKeyPressed)
                    except:
                        raise AttributeError,\
                              """per le colonne checkbox indicare i """\
                              """valori per checked/notchecked"""
                    
                elif _type == gridlib.GRID_VALUE_STRING:
                    #std editor data
                    if len(spec) > 1 and spec[1] == 'lowercase':
                        attr_editor = awg.TextLowerCaseCellEditor()
                    else:
                        attr_editor = awg.TextCellEditor()
            
            if _type == 'image':
                #esempio: image:bitmap,48x48 (width x height)
                attr_editor = None
                w, h = map(int, spec[1].split(',')[1].split('x'))
                attr_render = awg.ImageCellRenderer(w, h)
        
            #if attr_editor is None and linktables is not None:
            if linktables is not None:
                for lt_col, lt_rsidcol, lt_rscodcol, lt_rsdescol,\
                    lt_table, lt_filter, lt_cardclass, lt_fl, lt_events,\
                    lt_editor, lt_oncreate in linktables:
                    if lt_col == col:
                        attr_editor = lt_editor( lt_table,
                                                 lt_rsidcol,
                                                 lt_rscodcol,
                                                 lt_rsdescol,
                                                 lt_cardclass,
                                                 lt_filter,
                                                 lt_fl,
                                                 lt_events,
                                                 lt_oncreate)
            
            if attr_editor is None:
                attr_editor = awg.TextCellEditor()
            
            #determinazione font ed allineamento
            if _type.split(":")[0] in (gridlib.GRID_VALUE_NUMBER,\
                                       gridlib.GRID_VALUE_FLOAT,\
                                       gridlib.GRID_VALUE_DATETIME):
                attr_font = wx.Font(self.FONT_SIZE, wx.MODERN, wx.NORMAL, wx.NORMAL)
                
                if True:#_type.split(":")[0] not in (gridlib.GRID_VALUE_DATETIME,\
                    #gridlib.GRID_VALUE_BOOL):
                    attr_align = wx.ALIGN_RIGHT
            
            else:
                attr_font = self.DEFAULT_FONT
                
#            elif _type.split(":")[0] == gridlib.GRID_VALUE_DATETIME:
#                attr_font = wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL)
#            
            if attr_editor is not None:
                attr.SetEditor(attr_editor)
            
            if attr_render is not None:
                attr.SetRenderer(attr_render)
            else:
                attr.SetRenderer(gridlib.GridCellStringRenderer())
            
            attr.SetFont(attr_font)
            self.colFont.append(attr_font)
            attr.SetAlignment(attr_align, wx.ALIGN_CENTRE_VERTICAL)
            #self.SetColLabelAlignment(attr_align, wx.ALIGN_CENTER_VERTICAL)
            
            self.colAttr.append(attr)
            del attr
        
        self.SetRowScrollRatio()
        self.AdjustRowsHeight()
#        if self._fitColumn:
#            self.FitColumn()
        wx.CallAfter(self.AutoSizeColumns)
    
    def SetSelectionMode(self, mode):
        gridlib.Grid.SetSelectionMode(self, mode)
        if mode == self.SelectRows:
            self.HideHiliteBox()
    
    def HideHiliteBox(self):
        self.SetCellHighlightPenWidth(0)
        self.SetCellHighlightROPenWidth(0)
    
    def SetCellDynAttr(self, dynattr_cb):
        table = self.GetTable()
        if table:
            table.SetCellDynAttr(dynattr_cb)
    
    def SetColMaxChar(self, col, max):
        self._colmaxchars[col] = max

    def OnShowCellEditor(self, event):
        self._edrow = row = event.GetRow()
        self._edcol = col = event.GetCol()
        e = self.GetCellEditor(row, col)
        if isinstance(e, awg.TextCellEditor):
            t = self.GetTable()
            c = t.rsColumns[col]
            if c in self._colmaxchars:
                e.SetMaxLength(self._colmaxchars[c])
        event.Skip()

    def DeleteRows(self, rowFrom, rowTo=None):
        table = self.GetTable()
        if table:
            return table.DeleteRows(rowFrom, rowTo)

    def ChangeData(self, newdata):
        table = self.GetTable()
        if table:
            table.ChangeData(newdata, autosize_columns=False)
            self.AnchorColumn()
            self.SetRowScrollRatio()
            self.SetGridCursor(0,0)
        self._edrow = self._edcol = None
        self.AdjustRowsHeight()
    
    def SetRowHeight(self, rh):
        self.rowheight = rh
        self.AdjustRowsHeight()
        self.SetRowScrollRatio()
    
    def AdjustRowsHeight(self):
        if self.rowheight is None:
            return
#        for n in range(self.GetNumberRows()):
#            self.SetRowSize(n, self.rowheight)
        self.SetDefaultRowSize(self.rowheight)
    
    def SetEditableColumns(self, edcol):
        """
        Imposta le colonne che è possibile modificare
        
        @param edcol: lista colonne da editare
        @type edcol: list/tuple
        """
        if edcol:
            for col in range(len(self.colAttr)):
                if not col in edcol:
                    self.colAttr[col].SetReadOnly()

    def ForceResetView(self, force = True):
        table = self.GetTable()
        assert isinstance(table, DbGridTable), "Table not istantiated"
        if table:
            table.ForceResetView(force)

    def ResetView(self):
        #numcols = self.GetNumberCols()
        #cs = [self.GetColSize(x) for x in range(numcols)]
        table = self.GetTable()
        if table:
            table.ResetView(autosize_columns=False)
        self.SetRowScrollRatio()
        if not self.AnchorColumn() and self._fitColumn:
            self.FitColumn()
    
    def SetRowScrollRatio(self):
        #rx, ry = self.GetScrollPixelsPerUnit()
        h = self.rowheight or self.GetDefaultRowSize()
        #pxx = 
        #self.SetScrollbars(rx, h, len(self.GetColumn), noUnitsY)
        self.SetScrollLineY(h*self.ratiofactor)

    def SetRowDynLabel(self, rowdynlabel):
        table = self.GetTable()
        if table:
            table.SetRowDynLabel(rowdynlabel)

    def GetSelectedRows(self):
        rows = []
        grc =  self.GetGridCursorRow()
        set1 = self.GetSelectionBlockTopLeft()
        set2 = self.GetSelectionBlockBottomRight()
        rows.append(grc)
        if len(set1):
            assert len(set1)==len(set2)
            for i in range(len(set1)):
                for row in range(set1[i][0], set2[i][0]+1):
                    if row not in rows:
                        rows.append(row)
        #else:
            #rows.append(grc)
        return rows
    
    def IsOnTotalRow(self, *args, **kwargs):
        out = False
        table = self.GetTable()
        if table:
            out = table.IsOnTotalRow(*args, **kwargs)
        return out
    
    def CurrentTotalRow(self, *args, **kwargs):
        out = -1
        table = self.GetTable()
        if table:
            out = table.CurrentTotalRow(*args, **kwargs)
        return out
    

# ------------------------------------------------------------------------------


class LinkTabAttr(object):
    """
    Classe per specifiche di colonna con editor LinkTable.
    """
    editorclass = awg.DataLinkCellEditor
    
    _col = None
    _rsidcol = None
    _rscodcol = None
    _rsdescol = None
    _table = None
    _cardclass = None
    _filter = None
    _oncreate = None
    
    def __init__(self, table, col, rsidcol, rscodcol, rsdescol=None,\
                 cardclass=None, filter=None, refresh=False, oncreate=None):
        """
        Costruttore attributi per editor colonne di tipo LinkTable.
        @param col: num.colonna nella griglia da associare a questo editor
        @type col: int
        @param rsidcol: num.colonna nel recordset contenente l'id
        dell'elemento da relazionare
        @type rsidcol: int
        @param rscodcol: num.colonna nel recordset contenente il codice
        relativo all'elemento relazionato (-1 se non esiste la col. codice)
        @param rsdescol: num.colonna nel recordset contenente la descrizione
        relativo all'elemento relazionato (-1 se non esiste la col. descr.)
        @param table: nome tabella relazionata sulla colonna
        @type table: str
        @param cardclass: classe per la manutenzione/inserimento
        dell'elemento relazionato
        @param filter: espressione sql del filtro da applicare
        @type filter: str
        @param refresh: flag per ridisegnare la griglia in uscita
        @type refresh: bool
        """
        object.__init__(self)
        if rsdescol is None and rscodcol is not None:
            rsdescol = rscodcol+1
        self._col = col
        self._rsidcol = rsidcol
        self._rscodcol = rscodcol
        self._rsdescol = rsdescol
        if table:
            self._table = table
        if cardclass:
            self._cardclass = cardclass
        self._filter = filter
        self._filterlinks = []
        self.eventBindings = []
        if oncreate:
            self._oncreate = oncreate

    def AddBinding(self, eventbind):
        self.eventBindings.append(eventbind)
    
    def SetFilter(self, filter):
        """
        Imposta il filtro che deve 
        """
        self._filter = filter
        self._filterlinks = []

    def AddFilter(self, label, table, column,\
                  cardClass=None, filter=None, startValue=None):
        """
        LinkTabAttr::AddFilter(label, table, column,
        cardClass=None, filter=None, startValue=None)
        
        Aggiunge un filtro basato su LinkTable.
        
        @param label: descrizione del filtro. Sarà perceduto da 
                      "Filtra in base a:"
        @type table: str
        @param table: nome tabella relazionata sulla colonna
        @type table: str
        @param columns: nome colonna sulla tabella relazionata che deve
                        essere filtrata in base al LinkTable di filtro
        @param cardclass: classe per la manutenzione/inserimento
        @param filter: espressione sql del filtro da applicare
        @type filter: str
        @param startvalue: valore iniziale da attribuire al LinkTable; può
essere sia l'id dell'elemento da impostare, sia il suo codice
        """
        self._filterlinks.append( [ label,
                                    table, 
                                    column, 
                                    cardClass, 
                                    filter, 
                                    startValue ] )

    def _GetParams(self):
        """
        Ritorna le informazioni inserite tramite init ed eventuali
        Addfilter sotto forma di lista, come voluto da DbGrid
        """
        return [ self._col,\
                 self._rsidcol,\
                 self._rscodcol,\
                 self._rsdescol,\
                 self._table,\
                 self._filter,\
                 self._cardclass,\
                 self._filterlinks,\
                 self.eventBindings,\
                 self.editorclass,
                 self._oncreate]


# ------------------------------------------------------------------------------


class AfterEditAttr(object):
    """
    Classe per specifiche after edit.
    """
    def __init__(self):
        object.__init__(self)
        self.stru = ()

    def SetBeforeMemoCallback(self, column, callable):
        self.stru = (CELLEDIT_BEFORE_UPDATE, column, callable)

    def SetAfterMemoCallback(self, column, callable):
        self.stru = (CELLEDIT_AFTER_UPDATE, column, callable)

    def _GetParams(self):
        """
        Ritorna le informazioni inserite tramite init sotto forma di lista,
        come voluto da DbGrid
        """
        return self.stru


# ------------------------------------------------------------------------------


class DbGridTable(gridlib.PyGridTableBase):
    def __init__(self, grid, rs, colmap, canins, afterEditCB, newRowCB,\
                 getExternal = None):
        """
        Imposta il recordset che deve riempire la griglia.
        Si basa essenzialmente su un recordset generalmente ottenuto come
        risultato di una query SQL ed ua struttura di mapping tra colonne 
        del recordset e colonne della griglia; è possibile specificare anche
        la struttura descrittiva del recordset, generalmente ottenuta dal
        membro C{description} dell'oggetto C{cursore} del database.
        
        C{rs} è il recordset (nrec-tuple di ncol-tuple)
        C{colmap} è la struttura di mapping tra recordset e colonne da
        gestire nella griglia; ogni elemento della tupla è una tupla
        che contiene il numero della colonna del recordset e la relativa
        intestazione.
        Per le colonne di tipo non stringa, è possibile specificarne
        il tipo come terzo elemento della tupla; per i tipi numerici è
        possibile specificare il numero di cifre intere e per i tipi
        'float' è necessario indicare il numero delle cifre decimali.
        
        @param rs: recordset con i valori che riepiono la griglia
        @type rs: tuple
        @param colmap: struttura di mapping
        @type colmap: ncol-tuple di 2/3/4-tuple 
        C{numero, intestazione [, tipo [, lunghezza [, decimali] ] ]}
        """
        gridlib.PyGridTableBase.__init__(self)
        
        self.grid = grid
        self.data = rs
        self.canInsert = canins
        self.afterEditCB = afterEditCB
        self.newRowCB = newRowCB
        self.getExternal = getExternal
        
        self.colLabels = []
        self.rsColumns = []
        self.dataTypes = []
        self.noneIsBlank = []
        self.totals = []
        
        ncol = 0
        for num,des,tip,nib in colmap:
            self.colLabels.append(des)
            self.rsColumns.append(num)
            self.dataTypes.append(tip)
            self.noneIsBlank.append(nib)
            ncol += 1
            
        self._dynattr_cb = None
        self._rowDynLabel = None
        
        self._numrows = self.GetNumberRows()
        self._numcols = self.GetNumberCols()
        
        self.forceResetView = False
        
        self._saynscols = []
    
    def SetNotSpecifCols(self, nsc):
        self._saynscols = nsc

    def AddTotalsRow(self, lblcol, lbl, cols, cbfilt=None):
        """
        Aggiunge una riga di totali.
        lblcol #col. label
        lbl    label
        cols   lista colonne da totalizzare
        cbfilt callback filtro di applicazione dei totalizzatori x ogni riga
        """
        if cbfilt is None:
            cbfilt = lambda *args: True
        if type(cols) != list:
            cols = list(cols)
        self.totals.append((lblcol, lbl, cols, [0]*len(cols), cbfilt))
    
    def GetTotalsRows(self):
        return self.totals

    def UpdateTotals(self):
        for tr in self.totals:
            for t in range(len(tr[3])):
                tr[3][t] = 0
        for row, rsrow in enumerate(self.data):
            for tr in self.totals:
                if tr[4](self.data, row):
                    for tot, col in enumerate(tr[2]):
                        if col<0:
                            tr[3][tot] += self.GetDataValue(row, col, 
                                                            gridcols=True) or 0
                        else:
                            tr[3][tot] += rsrow[col] or 0

    def SetGetExternal(self, rscol, getExternal):
        self.getExternal = (rscol, getExternal)

    def GetNumberRows(self):
        if self.data is None:
            if self.canInsert:
                out = 1
            else:
                out = 0
        else:
            out = len(self.data)
            if self.canInsert:
                out += 1
            else:
                out += len(self.totals)
        return out

    def GetNumberCols(self):
        return len(self.rsColumns)

    def GetColLabelValue(self, col):
        return self.colLabels[col]

    def IsEmptyCell(self, row, col):
        try:
            return (self.data[row][ self.rsColumns[col] ] is None)
        except:
            return True

    def SetCellDynAttr(self, dynattr_cb):
        self._dynattr_cb = dynattr_cb

    def GetAttr(self, row, col, kind = None):
        try:
            attr = self.GetView().colAttr[col]
        except:
            attr = None
        else:
            if self._dynattr_cb is not None:
                rscol = self.rsColumns[col]
                attr = self._dynattr_cb(row, col, rscol, attr)
            if attr is not None:
                attr.IncRef()
        return attr

    def SetRowDynLabel(self, rowdynlabel):
        self._rowDynLabel = rowdynlabel

    def GetRowLabelValue(self, row):
        if self._rowDynLabel:
            out = self._rowDynLabel(row)
        else:
            out = "%d" % row
        return out

    def TestAfterEdit(self, mode, row, col, value):
        """
        Richiamo callback per editazione cella avvenuta.
        Se C{mode} = 1, viene valutato il callback prima dell'aggiornamento
        della cella ed essa viene aggiornata solo se il ritorno dal
        callback non è C{False}.
        Se C{mode} = 2, viene valutato il callback dopo l'aggiornamento
        della cella.
        """
        valok = True
        if self.afterEditCB is not None:
            for ae_mode, ae_col, ae_callback in self.afterEditCB:
                if mode == ae_mode and (ae_col == col or ae_col < 0):
                    rscol = self.rsColumns[col]
                    cbo = ae_callback(row, col, rscol, value)
                    if type(cbo) == bool:
                        valok = cbo
        
        #in qualche afteredit potrebbe essere stato richiesto di resettare
        #la griglia dopo la sua esecuzione
        if self.forceResetView:
            self.ResetView()
        
        return valok
    
    #def __setattr__(self, x, y):
        #if x == "forceResetView" and y is True:
            #pass
        #DbGrid.__setattr__(self, x, y)
    
    def SetValue(self, row, col, value):
        #setta il valore della cella
        setval = True
        rscol = self.rsColumns[col]
        if not self.TestAfterEdit(CELLEDIT_BEFORE_UPDATE, row, col, value):
            setval = False
        #in qualche afteredit eseguito prima dell'aggiornamento della tabella
        #potrebbe essere stato richiesto di ridisegnare la griglia
        if self.forceResetView:
            self.ResetView()
        if setval:
            if self.canInsert and row == len(self.data):
                #testo la necessità di chiamare il callback per l'aggiunta
                #di una riga alla tabella
                if self.newRowCB is None:
                    setval = False
                else:
                    self.newRowCB()
                    msg = gridlib.GridTableMessage(self,\
                        gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                    self.GetView().ProcessTableMessage(msg)
                    self._numrows += 1
        if setval:
            if rscol>=0: self.data[row][rscol] = value
            self.TestAfterEdit(CELLEDIT_AFTER_UPDATE, row, col, value)

    #def CanGetValueAs(self, row, col, typeName):
        #return typeName in self.dataTypes[col]

    def GetDataValue(self, row, col, gridcols=False):
        value = None
        rows = self.GetNumberRows()
        if gridcols:
            rscol = col
        else:
            rscol = self.rsColumns[col]
        try:
            if row == rows-1 and self.canInsert:
                value = None
            else:
                if self.totals and self.IsOnTotalRow(row):
                    tr = self.totals[-(rows-row)]
                    if col == tr[0]:
                        value = tr[1]
                    elif rscol in tr[2]:
                        value = tr[3][tr[2].index(rscol)]
                    else:
                        value = None
                else:
                    if self.getExternal and rscol == self.getExternal[0]:
                        #prendo valore non dal recordset ma dalla funzione
                        #definita in getExternal - utile in caso di visualizz.
                        #particolari +o- complesse di valori non presenti nel
                        #recordset associato al grid
                        value = (self.getExternal[1])(row, col, rscol)
                    else:
                        #prendo valore da recordset - standard
                        if rscol>=0:
                            value = self.data[row][rscol]
                        else:
                            value=None
        except IndexError:
            pass
        return value
    
    def GetValue(self, row, col):
        
        out = None
        value = self.GetDataValue(row, col)
        
        spec = self.dataTypes[col].split(':')
        _type = spec[0]
        
        if _type == gridlib.GRID_VALUE_STRING:
            if value is None:# and self.noneIsBlank[col]:
                value = ''
            if len(spec) > 1:
                if spec[1] == 'lowercase':
                    out = value
                else:
                    try:
                        out = value.rjust(int(spec[1]))
                    except:
                        pass
            else:
                out = value
            
        elif _type == gridlib.GRID_VALUE_NUMBER:
            try:
                _len = int(spec[1].split(",")[0])
            except:
                _len = 10
            if not value and self.noneIsBlank[col]:
                out = "".rjust(_len)
            else:
                if value is None:
                    value = 0
                try:
                    out = locale.format("%d", value, True)
                except:
                    pass
            
        elif _type == gridlib.GRID_VALUE_FLOAT:
            _len = int(spec[1].split(",")[0])
            try:
                _dec = int(spec[1].split(",")[1])
            except:
                _dec = 2
            w = _len+_dec+1
            #if value is None and self.noneIsBlank[col]:
            if not value and self.noneIsBlank[col]:
                out = "".rjust(w)
            else:
                if value is None:
                    value = 0
                try:
                    out = locale.format("%%.%df" % _dec, value, 1, monetary=True).rjust(w)
                except:
                    pass
            
        elif _type == gridlib.GRID_VALUE_DATETIME:
            if value is None:
                out = ""
            else:
                try:
                    #classe mx.DateTime
                    if len(spec) == 1:
                        if YEAR4:
                            m = FORMAT_DATE
                        else:
                            m = FORMAT_DATE_SH
                    else:
                        if YEAR4:
                            m = FORMAT_DATETIME
                        else:
                            m = FORMAT_DATETIME_SH
                    out = value.Format(m)
                except Exception, e:
                    out = repr(value)
            
        elif _type in (gridlib.GRID_VALUE_BOOL, gridlib.GRID_VALUE_CHOICE):
            try:
                if len(spec)>1:
                    val_yes, _ = eval(spec[1])
                else:
                    val_yes, _ = 1, 0
                out = int(value == val_yes)
            except:
                pass
        
        if not out:
            if col in self._saynscols and 0<=row<len(self.data):
                out = self.GetUnspecifiedVal(out)
            elif out is None:
                out = "???"
        
        return out
    
    def GetUnspecifiedVal(self, val):
        if not val:
            val = '-n/s-'
        return val
    
    def IsOnTotalRow(self, row):
        return row >= self.GetNumberRows()-len(self.totals)
    
    def CurrentTotalRow(self, row):
        if self.IsOnTotalRow(row):
            out = row-(self.GetNumberRows()-len(self.totals))
        else:
            out = -1
        return out
    
    def DeleteRows(self, rowFrom, rowTo = None):
        if type(rowFrom) in (list, tuple):
            rows = list(rowFrom)
            rows = rows[:]
            rows.sort()
            deleteCount = 0
            for i in rows:
                self.data.pop(i-deleteCount)
                deleteCount += 1
        else:
            if rowTo is None:
                rowTo = rowFrom+1
            del self.data[rowFrom:rowTo]
        wx.CallAfter(self.ResetView)

    def ChangeData(self, newdata, autosize_columns=True):
        self.data = newdata
        self.ResetView(autosize_columns)

    def ForceResetView(self, force = True):
        self.forceResetView = force

    def ResetView(self, autosize_columns=True):
        """
        E' cambiato il numero di righe e/o colonne: l'intera griglia
        viene aggiornata a video.
        """
        grid = self.GetView()
        
        grid.BeginBatch()
        
        for current, new, delmsg, addmsg in\
          [ (self._numrows, self.GetNumberRows(),
             gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED,\
             gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED),\
            
            (self._numcols, self.GetNumberCols(),\
             gridlib.GRIDTABLE_NOTIFY_COLS_DELETED,\
             gridlib.GRIDTABLE_NOTIFY_COLS_APPENDED) ]:
            
            if new < current:
                msg = gridlib.GridTableMessage(self,\
                                               delmsg, new, current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = gridlib.GridTableMessage(self, addmsg, new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)
        
        grid.EndBatch()
        
        self._numrows = self.GetNumberRows()
        self._numcols = self.GetNumberCols()
        # update the column rendering plugins
        #self._updateColAttrs(grid)
        
        # update the scrollbars and the displayed part of the grid
        grid.AdjustScrollbars()
        grid.ForceRefresh()
        
        if autosize_columns:
            self.grid.AutoSizeColumns()
        
        if self.forceResetView:
            self.forceResetView = False
        
        self.UpdateTotals()

    def UpdateValues(self, grid):
        msg = gridlib.GridTableMessage(self,\
                gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)
    
    def col2rs(self, col):
        if col<len(self.rsColumns):
            col = self.rsColumns[col]
        else:
            col = None
        return col
    
    def rs2col(self, col):
        if col in self.rsColumns:
            col = self.rsColumns.index(col)
        else:
            col = None
        return col
    
    def ExportCSV(self):
        """
        Esporta il contenuto della griglia in un file csv
        """
        import awc.util as awu #sta qui x rif.circolare
        msgbox = lambda msg: awu.MsgDialog(self.grid,
                                           message=msg,
                                           style=wx.ICON_ERROR)
        
        wx.BeginBusyCursor()
        
        try:
            
            try:
                
                import codecs
                tmpfile = tempfile.NamedTemporaryFile(suffix='.csv')
                tmpname = tmpfile.name
                tmpfile.close()
                tmpfile = open(tmpname, 'wb')
                tmpfile.write(codecs.BOM_UTF8)
                wx.GetApp().AppendTempFile(tmpname)
                
                #writer = csv.writer(tmpfile)
                writer = csv.writer(tmpfile,
                                    delimiter=CSVFORMAT_DELIMITER,
                                    quotechar=CSVFORMAT_QUOTECHAR,
                                    doublequote=True,
                                    skipinitialspace=False,
                                    lineterminator='\r\n',
                                    quoting=int(CSVFORMAT_QUOTING))
                csvrs = []
                #intestazioni di colonna
                csvrs.append([self.grid.GetColLabelValue(col).encode('utf-8') 
                              for col in range(self.grid.GetNumberCols())])
                
                #generazione recordset csv
                if CSVFORMAT_ASGRID:
                    #formato come valori presentati in griglia, nessuna conversione
                    def f(x):
                        try:
                            return x.encode('utf-8')
                        except:
                            return x
                    for row in range(len(self.data)):
                        csvrs.append([f(self.GetValue(row, col)) 
                                      for col in range(self.grid.GetNumberCols())])
                    
                else:
                    #formato dipendente dalla configurazione specificata in
                    #CSVFORMAT_XXX, conversione valori celle indipendentemente
                    #dal formato espresso nella griglia
                    def strdate(x):
                        if x is None: return ''
                        return x.Format().split(' ')[0]
                    def strdatetime(x):
                        if x is None: return ''
                        return x.Format()
                    def strnum(x):
                        if x is None: return ''
                        return locale.format('%.6f', x)
                    def strbool(x):
                        if x is None: return ''
                        return [' ', 'X'][int(bool(x))]
                    def strunicode(x):
                        if x is None: return ''
                        x = unicode(x).encode('utf-8')
                        if CSVFORMAT_EXCELZERO and (x or ' ')[0].isdigit():
                            x = '="%s"' % x
                        return x
                    colmap = {gridlib.GRID_VALUE_DATETIME:         strdate,
                              gridlib.GRID_VALUE_DATETIME+":time": strdatetime,
                              gridlib.GRID_VALUE_FLOAT:            strnum,
                              gridlib.GRID_VALUE_NUMBER:           strnum,
                              gridlib.GRID_VALUE_LONG:             strnum,
                              gridlib.GRID_VALUE_BOOL:             strbool,
                              gridlib.GRID_VALUE_CHOICE:           strbool,
                              gridlib.GRID_VALUE_STRING:           strunicode,
                              gridlib.GRID_VALUE_TEXT:             strunicode,
                          }                               
                    types = []
                    for col in range(self.grid.GetNumberCols()):
                        spec = self.dataTypes[col].split(':')
                        typ = spec[0]
                        if typ == 'datetime' and len(spec)>1:
                            typ += ":time"
                        types.append(typ)
                    
                    #d = writer.dialect
                    #d.delimiter = CSVFORMAT_DELIMITER
                    #d.quotechar = CSVFORMAT_QUOTECHAR
                    #d.quoting = int(CSVFORMAT_QUOTING)
                    
                    for row in range(len(self.data)):
                        rs = []
                        for col in range(self.grid.GetNumberCols()):
                            try:
                                val = self.GetDataValue(row, col)
                            except:
                                val = self.GetValue(row, col)
                            rs.append(colmap[types[col]](val))
                        csvrs.append(rs)
                
                writer.writerows(csvrs)
                tmpfile.close()
                
                os.startfile(tmpname)
               
            except IOError, e:
                msgbox('Generazione fallita del file csv (%s)\n%s'\
                       % (tmpname, repr(e.args)), style=wx.ICON_ERROR)
                
            except Exception, e:
                if e.args[0] == 1155:
                    msg =\
                        """Il file CSV è stato generato, ma il sistema non """\
                        """conosce l'applicazione da utilizzare per aprirlo.\n\n"""
                    msg += tmpname
                else:
                    msg =\
                        """Problema durante l'apertura del file CSV:\n%s"""\
                        % repr(e.args)
                msgbox(msg)
            
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


class DbGridColored(DbGrid):
    
    _fgbgcol = 'black', 'ivory2'

    def __init__(self, *args, **kwargs):
        DbGrid.__init__(self, *args, **kwargs)
        self.DrawLines()
    
    def SetColors(self, fg, bg):
        self._fgbgcol = [fg, bg]
        self.UpdateColors()
    
    def UpdateColors(self):
        fg, bg = self._fgbgcol
        self.SetForegroundColour(fg)
        self.SetBackgroundColour(bg)
    
    def GetAttr(self, row, col, rscol, attr=gridlib.GridCellAttr):
        fg, bg = self._fgbgcol
        attr.SetTextColour(fg)
        attr.SetBackgroundColour(bg)
        return attr


# ------------------------------------------------------------------------------


import awc.controls
SEARCH_COLORS1 = awc.controls.SEARCH_COLORS1
SEARCH_COLORS2 = awc.controls.SEARCH_COLORS2

class DbGrid2Colori(DbGridColored):
    _colors = None
    
    def __init__(self, *args, **kwargs):
        DbGridColored.__init__(self, *args, **kwargs)
        self._colors = [['black', 'ivory2'],['black', 'ivory3']]
##        self._SetSysColors(0, wx.SYS_COLOUR_WINDOWTEXT, wx.SYS_COLOUR_WINDOW)
##        self._SetSysColors(1, wx.SYS_COLOUR_WINDOWTEXT, wx.SYS_COLOUR_WINDOWFRAME)
#        if wx.Platform == '__WXMSW__':
#            c = wx.SYS_COLOUR_MENU
#        else:
#            c = wx.SYS_COLOUR_WINDOW
#        self._SetSysColors(0, wx.SYS_COLOUR_WINDOWTEXT, c)
#        fg1, bg1 = self._colors[0]
#        fg2 = fg1
#        r = bg1.red
#        g = bg1.green
#        b = bg1.blue
#        d = 32
#        r -= d; r %= 256
#        g -= d; g %= 256
#        b -= d; b %= 256
#        bg2 = wx.Colour(r, g, b)
#        self._colors[1][0] = fg2
#        self._colors[1][1] = bg2
        self.DrawLines()
    
    def SetData(self, *args, **kwargs):
        DbGrid.SetData(self, *args, **kwargs)
        self.SetCellDynAttr(self.GetAttr)
    
    def SetColors1(self, fg, bg):
        self._SetColors(0, fg, bg)
    
    def SetColors2(self, fg, bg):
        self._SetColors(1, fg, bg)
    
    def _SetColors(self, num, fg, bg):
        self._colors[num] = map(wx.TheColourDatabase.Find, (fg, bg))
        if num == 0:
            self.SetColors(fg, bg)
    
    def SetSearchColors(self):
        self.SetColors1(*SEARCH_COLORS1)
        self.SetColors2(*SEARCH_COLORS2)
    
    def _SetSysColors(self, num, fg, bg):
        self._colors[num] = map(wx.SystemSettings.GetColour, (fg, bg))
        if num == 0:
            self.SetColors(*self._colors[num])
    

# ------------------------------------------------------------------------------


class DbGridColoriAlternati(DbGrid2Colori):
    
    cond_color = None
    def AddConditionalColor(self, testcol, value, fg, bg):
        if not testcol in self.cond_color:
            self.cond_color[testcol] = []
        self.cond_color[testcol].append([value, fg, bg])
    
    def __init__(self, *args, **kwargs):
        DbGrid2Colori.__init__(self, *args, **kwargs)
        self._getattr_keys = {}
        self._getattr_index = 0
        self._getattr_column = None
        self.SetRatioFactor(2)
        self.cond_color = {}
        
    def SetColorsByColumn(self, column):
        self._getattr_column = column
    
    def ChangeData(self, *args, **kwargs):
        DbGrid2Colori.ChangeData(self, *args, **kwargs)
        self._getattr_keys.clear()
        self._getattr_index = 0
    
    def GetAttr(self, row, col, rscol, attr=gridlib.GridCellAttr):
        
        rs = self.GetTable().data
        
        if self._getattr_column is None:
            n = row % 2
            
        else:
            try:
                key = rs[row][self._getattr_column]
            except:
                key = None
            if not key in self._getattr_keys:
                self._getattr_index = 1-self._getattr_index
                self._getattr_keys[key] = self._getattr_index
            
            n = self._getattr_keys[key]
        
        fg, bg = self._colors[n]
        
        attr.SetTextColour(fg)
        attr.SetBackgroundColour(bg)
        
        if self.cond_color and 0 <= row < len(rs):
            for testcol in self.cond_color:
                value = rs[row][testcol]
                for testvalue, fg, bg in self.cond_color[testcol]:
                    if value == testvalue:
                        attr.SetTextColour(fg)
                        attr.SetBackgroundColour(bg)
        
        attr.SetReadOnly()
        
        font = attr.GetFont()
        if self.IsOnTotalRow(row):
            style = wx.ITALIC
        else:
            style = wx.NORMAL
        font.SetStyle(style)
        attr.SetFont(font)
        
        return attr


# ------------------------------------------------------------------------------


class DbGridColoriABlocchi(DbGrid2Colori):
    testcol = None
    deltakeys = None
    
    def __init__(self, *args, **kwargs):
        DbGrid2Colori.__init__(self, *args, **kwargs)
        self.deltakeys = []
    
    def SetData(self, newdata, *args, **kwargs):
        DbGrid2Colori.SetData(self, newdata, *args, **kwargs)
        self.Analizza(newdata)
    
    def ChangeData(self, newdata):
        DbGrid2Colori.ChangeData(self, newdata)
        self.Analizza(newdata)
    
    def Analizza(self, data):
        del self.deltakeys[:]
        def UpdateKeys(row):
            key = row[self.testcol]
            if not key in self.deltakeys:
                self.deltakeys.append(key)
        map(UpdateKeys, data)
    
    def SetColonnaDelta(self, col):
        self.testcol = col
    
    def GetAttr(self, row, col, rscol, attr=gridlib.GridCellAttr):
        delta = 0
        rs = self.GetTable().data
        if 0 < row < len(rs):
            key = rs[row][self.testcol]
            if key in self.deltakeys:
                delta = self.deltakeys.index(key)%2
        fg, bg = self._colors[delta]
        attr.SetTextColour(fg)
        attr.SetBackgroundColour(bg)
        attr.SetReadOnly()
        return attr


# ------------------------------------------------------------------------------


def MustDerive(method_name):
    raise Exception, "Must derive %s" % method_name


# ------------------------------------------------------------------------------


class ADB_Grid(DbGridColoriAlternati):
    
    _TYPE_DATE = GRID_VALUE_DATETIME
    @classmethod
    def TypeDate(cls):
        return cls._TYPE_DATE
    
    _TYPE_DATETIME = GRID_VALUE_DATETIME+":datetime"
    @classmethod
    def TypeDateTime(cls):
        return cls._TYPE_DATETIME
    
    _TYPE_FLOAT = GRID_VALUE_FLOAT
    @classmethod
    def TypeFloat(cls, integers=10, decimals=2):
        return '%s:%d,%d' % (cls._TYPE_FLOAT, integers, decimals)
    
    _TYPE_NUMBER = GRID_VALUE_NUMBER
    @classmethod
    def TypeInteger(cls, len=10):
        return '%s:%d' % (cls._TYPE_NUMBER, len)
    
    _TYPE_STRING = GRID_VALUE_STRING
    @classmethod
    def TypeString(cls):
        return cls._TYPE_STRING
    
    _TYPE_STRING_LOWERCASE = GRID_VALUE_STRING+":lowercase"
    @classmethod
    def TypeStringLowerCase(cls):
        return cls._TYPE_STRING_LOWERCASE
    
    _TYPE_CHECK = GRID_VALUE_CHOICE
    @classmethod
    def TypeCheck(cls, value_check=1, value_uncheck=0):
        return '%s:%s,%s' % (cls._TYPE_CHECK, value_check, value_uncheck)
    
    def __init__(self, parent, id=None, db_table=None, can_edit=False, can_insert=False, on_menu_select=None, **kwargs):
        
        if id is None:
            id = wx.NewId()
        
        kwargs['size'] = parent.GetClientSizeTuple()
        DbGridColoriAlternati.__init__(self, parent, id, **kwargs)
        
        self.db_table = db_table
        self.is_editable = can_edit
        self.is_insertable = can_insert
        
        self._colmap_check = False
        
        self._cols = []
        self._edcols = []
        self._added_cols = []
        self.db_columns = {}
        
        self._context_menu = []
        self._context_menu_on_select = on_menu_select #None, 'row', 'cell'
        assert on_menu_select in (None, 'row', 'cell')
        
        self._last_selected_row = -1    #last row for row selection
        self.Bind(gridlib.EVT_GRID_CMD_SELECT_CELL, self._OnRowSelected)
        
        self._last_selected_rc_row = -1 #last row for cell selection
        self._last_selected_rc_col = -1 #last col for cell selection
        self.Bind(gridlib.EVT_GRID_CMD_SELECT_CELL, self._OnCellSelected)
        
        self.Bind(gridlib.EVT_GRID_CMD_CELL_LEFT_CLICK, self._OnCellClicked)
        self.Bind(gridlib.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.OnCellDoubleClicked)
        
        self.Bind(gridlib.EVT_GRID_CMD_CELL_RIGHT_CLICK, self.OnContextMenu)
        self.Bind(gridlib.EVT_GRID_CMD_CELL_RIGHT_CLICK, self.OnCellRightClicked)
        self.Bind(gridlib.EVT_GRID_CMD_CELL_RIGHT_DCLICK, self.OnCellRightDoubleClicked)
        
        self.Bind(wx.EVT_CHAR, self._OnChar)
    
    def AddColumn(self, 
                  db_table=None,         #dbtable
                  col_name=None,         #column name
                  label=None,            #column label
                  col_type=None,         #column type (use TypeString(), TypeDate() etc. class methods)
                  blank_if_none=True,    #True/False to see blank instead of None in cells
                  col_width=None,        #pixles size of column (for numbers/dates it is not required)
                  is_editable=None,      #True/False for editing permission
                  is_fittable=None,      #True/False for column fitting (set only one column)
                  anchor=None,           #number of the column to anchor
                  resize_by_anchor=None, #number of the column to resize when anchoring
                  linktable_info=None,   #linktable specifications dictionary (see in the code below):
                  get_cell_func=None):   #callable returning cell display value, if not in recordset
        
        assert self.db_table is not None
        assert col_name is not None
        
        if db_table is None:
            db_table = self.db_table
        
        if col_type is None:
            col_type = GRID_VALUE_STRING
        
        if label is None:
            label = col_name
        
        if is_editable is None:
            is_editable = False
        
        stru = {'col_size':         col_width or 10,
                'is_fittable':      is_fittable,
                'is_editable':      is_editable,
                'blank_if_none':    blank_if_none,
                'db_table':         db_table,
                'col_name':         col_name,
                'col_type':         col_type,
                'label':            label,
                'anchor':           anchor,
                'resize_by_anchor': resize_by_anchor,
                'linktable_info':   linktable_info,
                'get_cell_func':    get_cell_func,}
        
        self._cols.append(stru)
        
        return len(self._cols)-1
    
    def CreateGrid(self):
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        colsize = []
        colmap = []
        col2fit = None
        anchor_col = None
        resize_col = None
        linktables = []
        
        for n, col in enumerate(self._cols):
            
            db_table = col['db_table']
            col_name = col['col_name']
            col_index = cn(db_table, col_name)
            
            assert col_index >= 0 or col['get_cell_func'] is not None, 'Unable to map column %s' % col_name
            
            col_type = col['col_type']
            col_size = col['col_size']
            blank_if_none = col['blank_if_none']
            label = col['label']
            
            if col['is_fittable']:
                if col2fit is not None:
                    raise Exception, "Only one column can be marked as fittable"
                col2fit = n
            
            if col['anchor']:
                if anchor_col is not None:
                    raise Exception, "Only one column can be marked to be the anchor"
                anchor_col = n
            
            if col['resize_by_anchor']:
                if resize_col is not None:
                    raise Exception, "Only one column can be marked to be resized by anchor"
                resize_col = n
            
            if col['is_editable']:
                self._edcols.append(n)
            
            if col['get_cell_func']:
                self._added_cols.append(n)
            
            linktable_info = col['linktable_info']
            
            if linktable_info:
                
                linktable_class =             linktable_info.get('class')
                linktable_attrib_column_id =  linktable_info.get('col_id')
                linktable_attrib_column_cod = linktable_info.get('col_cod', None)
                linktable_attrib_column_des = linktable_info.get('col_des', None)
                linktable_attrib_filter =     linktable_info.get('filter', None)
                linktable_attrib_refresh =    linktable_info.get('refresh', None)
                linktable_attrib_oncreate =   linktable_info.get('oncreate', None)
                
                class LinkTableCellEditor(awg.DataLinkCellEditor):
                    baseclass = linktable_class
                
                class LinkTableCellAttr(LinkTabAttr):
                    editorclass = LinkTableCellEditor
                
                linktable = LinkTableCellAttr(None,                        #table name must be declared in linktable class
                                              n,                           #column number of controlled id 
                                              linktable_attrib_column_id,  #recordset id column
                                              linktable_attrib_column_cod, #recordset code column
                                              linktable_attrib_column_des, #recordset description column
                                              None,                        #card class must be declared in linktable class
                                              linktable_attrib_filter,     #sql base filter
                                              linktable_attrib_refresh,    #refresh flag
                                              linktable_attrib_oncreate)   #on create callback
                linktables.append(linktable)
            
            colsize.append(col_size)
            colmap.append([col_index, label, col_type, blank_if_none])
            self.db_columns['%s.%s' % (db_table.GetTableAlias(), col_name)] = n
        
        canedit = self.is_editable
        canins = self.is_insertable
        
        self._fitColumn = col2fit
        self._anchor_column = anchor_col
        self._anchor_resize = resize_col
        
        self._last_selected_row = self._last_selected_col = -1
        
        afteredit = ((CELLEDIT_BEFORE_UPDATE, -1, self._CellEditBeforeUpdate),
                     (CELLEDIT_AFTER_UPDATE, -1, self._CellEditAfterUpdate),)
        editors = None
        
        db_table = self.db_table
        
        self.tableClass = self.GetGridTableClass()
        
        self.SetData(db_table.GetRecordset(), colmap, canedit, canins,
                     linktables or None, afteredit or None, self.CreateNewRow, editors) 
        
        if not db_table.IsEmpty():
            try:
                self.MakeCellVisible(0, 0)
                self.SetGridCursor(0, 0)
            except:
                pass
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        self.AutoSizeColumns()
        
        sizer = wx.FlexGridSizer(1,0,0,0)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        sizer.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent = self.GetParent()
        parent.SetSizer(sizer)
        sizer.SetSizeHints(parent)
    
    def GetGridTableClass(self):
        
        grid = self
        
        class GridTable(DbGridTable):
            def GetValue(self, row, col):
                stru = grid._cols[col]
                if stru['get_cell_func']:
                    return stru['get_cell_func'](row, col)
                return DbGridTable.GetValue(self, row, col)
        
        return GridTable
    
    def _OnCellSelected(self, event):
        
        row, col = event.GetRow(), event.GetCol()
        
        if row != self._last_selected_rc_row or col != self._last_selected_rc_col:
            _lastrow = self._last_selected_rc_row
            _lastcol = self._last_selected_rc_col
            event.GetLastRow = lambda: _lastrow
            event.GetLastCol = lambda: _lastcol
            self.OnCellSelected(event)
            self._last_selected_rc_row = row
            self._last_selected_rc_col = col
        else:
            event.Skip()
    
    def _OnRowSelected(self, event):
        
        row, col = event.GetRow(), event.GetCol()
        
        if row != self._last_selected_row:
            _lastrow = self._last_selected_rc_row
            event.GetLastRow = lambda: _lastrow
            self.OnRowSelected(event)
            self._last_selected_row = row
        else:
            event.Skip()
    
    def _CellEditBeforeUpdate(self, row, gridcol, col, value):
        return self.CellEditBeforeUpdate(row, gridcol, col, value)
    
    def _CellEditAfterUpdate(self, row, gridcol, col, value):
        c = self._cols[gridcol]
        db_table = self.db_table
        db_table.MoveRow(row)
        if c['linktable_info'] is None:
            col_name = c['col_name']
            col_value = value
        else:
            col_name = db_table.GetFieldName(0)
            col_value = getattr(db_table, col_name)
        setattr(db_table, col_name, col_value)
        return self.CellEditAfterUpdate(row, gridcol, col, value)
    
    def OnContextMenu(self, event):
        self.ShowContextMenu(event.GetPosition(), event.GetRow(), event.GetCol())
    
    def ResetContextMenu(self):
        del self._context_menu[:]
    
    def AppendContextMenuVoice(self, label, function, is_enabled=True):
        self._context_menu.append({'label': label,
                                   'function': function,
                                   'is_enabled': is_enabled,})
    
    def SetContextMenuVoices(self, menu_voices):
        self.ResetContextMenu()
        for menu_voice in menu_voices:
            self.AppendContextMenuVoice(menu_voice.get('label'),
                                        menu_voice.get('function'),
                                        menu_voice.get('is_enabled', True))
    
    def ShowContextMenu(self, position, row, col):
        if not self._context_menu:
            return
        menu = wx.Menu()
        for voice in self._context_menu:
            voice_id = voice.get('id', None) or wx.NewId()
            voice_label = voice.get('label')
            voice_func = voice.get('function')
            voice_enabled = voice.get('is_enabled', True)
            if voice_label == '-':
                menu.AppendSeparator()
            else:
                menu.Append(voice_id, voice_label)
                menu.Enable(voice_id, voice_enabled)
            self.Bind(wx.EVT_MENU, voice_func, id=voice_id)
        self.SetGridCursor(row, col)
        if self._context_menu_on_select == 'row':
            self.SelectRow(row)
        self.PopupMenu(menu, position)
        menu.Destroy()
    
    def GetAttr(self, row, col, rscol, attr):
        attr = DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        ro = True
        if self.is_editable and col in self._edcols:
            ro = False
        attr.SetReadOnly(ro)
        return attr
    
    def _OnCellClicked(self, event):
        if self.is_editable:
            row, col = event.GetRow(), event.GetCol()
            self._SwapCheckValue(row, col)
        event_Skip = event.Skip
        event.Skip = lambda: None
        self.OnCellClicked(event)
        event_Skip()
    
    def _OnChar(self, event):
        if self.is_editable:
            row, col = row, col = self.GetGridCursorRow(), self.GetGridCursorCol()
            self._SwapCheckValue(row, col)
        event.Skip()
    
    def _SwapCheckValue(self, row, col):
        checked = False
        stru = self._cols[col]
        cname = stru['col_name']
        ctype = stru['col_type']
        if ctype.startswith(self._TYPE_CHECK):
            _, values = ctype.split(':')
            v1, v0 = map(eval, values.split(','))
            db_table = stru['db_table'] or self.db_table
            if 0 <= row < db_table.RowsCount():
                self.db_table.MoveRow(row)
                cur_value = getattr(db_table, cname)
                if cur_value == v1:
                    value = v0
                else:
                    value = v1
                    checked = True
                setattr(db_table, cname, value)
                wx.CallAfter(lambda: self.ResetView())
        return checked
    
    
    #-----------------------------------------------------------------
    
    
    def OnCellClicked(self, event):
        event.Skip()
    
    def OnCellDoubleClicked(self, event):
        event.Skip()
    
    def OnCellRightClicked(self, event):
        event.Skip()
    
    def OnCellRightDoubleClicked(self, event):
        event.Skip()
    
    def OnCellSelected(self, event):
        event.Skip()
    
    def OnRowSelected(self, event):
        event.Skip()
    
    def CreateNewRow(self, *args):
        self.db_table.CreateNewRow()
        return True
    
    def DeleteRow(self, row):
        t = self.db_table
        if 0 <= row < t.RowsCount():
            t.MoveRow(row)
            if t.id is not None:
                if not t.id in t._info.deletedRecords:
                    t._info.deletedRecords.append(t.id)
            self.DeleteRows(row)
            t._info.recordCount = len(t._info.rs)
            if t._info.recordNumber >= t._info.recordCount:
                t._info.recordNumber = t._info.recordCount
    
    def CellEditBeforeUpdate(self, row, gridcol, col, value):
        return True
    
    def CellEditAfterUpdate(self, row, gridcol, col, value):
        return True


if __name__ == '__main__':
    
    import sys
    import stormdb as adb
    import anag.lib as alib
    
    import Env
    
    db = adb.DB()
    if not db.Connect(host='localhost', user='user_name', passwd='password', db='db_name'):
        print db.dbError.description
        sys.exit()
    
    class TestApp(wx.PySimpleApp):
        def OnInit(self, *args, **kwargs):
            Env.Azienda.Colours.SetDefaults()
            f = TestFrame()
            f.Show()
            self.dbcon = db._dbCon
            return True
    
    class TestFrame(wx.Frame):
        
        def __init__(self):
            wx.Frame.__init__(self, None, -1, title='ADB_Grid test')
            p = wx.Panel(self, -1)
            self.grid = TestGrid(p)
            self.Bind(wx.EVT_SIZE, self.OnSize)
            wx.CallAfter(lambda: self.grid.SetFocus())
        
        def OnSize(self, event):
            self.grid.SetSize(self.GetClientSize())
            event.Skip()
    
    class TestGrid(ADB_Grid):
        
        def __init__(self, parent):
            
            test = adb.DbTable('pdc')
            anag = test.AddJoin('clienti', 'anag', idLeft='id')
            stato = anag.AddJoin('x4.stati', 'stato')
            aliqiva = anag.AddJoin('aliqiva', join=adb.JOIN_LEFT)
            clifat = anag.AddJoin('pdc', 'clifat', join=adb.JOIN_LEFT)
            test.AddField('NULL', 'prova_data')
            test.Retrieve()
            for test in test:
                test.prova_data = Env.DateTime.now()
            
            self.dbpdc = test
            print '%d rows' % test.RowsCount()
            
            def cn(db, col):
                return db._GetFieldIndex(col, inline=True)
            
            linktable_stato = {'class':   alib.LinkTableStati,
                               'col_id':  cn(stato, 'id'),
                               'col_cod': cn(stato, 'codice'),
                               'col_des': cn(stato, 'descriz')}
            
            linktable_aliqiva = {'class':   alib.LinkTableAliqIva,
                                 'col_id':  cn(aliqiva, 'id'),
                                 'col_cod': cn(aliqiva, 'codice'),
                                 'col_des': cn(aliqiva, 'descriz')}
            
            linktable_clifat = {'class':   alib.LinkTableCliente,
                                'col_id':  cn(clifat, 'id'),
                                'col_cod': cn(clifat, 'codice'),
                                'col_des': cn(clifat, 'descriz')}
            
            ADB_Grid.__init__(self, parent, db_table=test, can_edit=True, can_insert=True, 
                              on_menu_select=None)
            
            self.AddColumn(test,    'codice',         'Codice', col_width=60)
            self.AddColumn(test,    'descriz',        'Cliente', col_width=300, is_editable=True)
            self.AddColumn(anag,    'indirizzo',      'Indirizzo', col_width=200, is_fittable=True)
            self.AddColumn(anag,    'cap',            'CAP', col_width=50)
            self.AddColumn(anag,    'citta',          'Città', col_width=200)
            self.AddColumn(anag,    'prov',           'Prov.', col_width=40)
            self.AddColumn(anag,    'is_blacklisted', 'BL', col_width=40, col_type=self.TypeCheck())
            
            self.AddColumn(stato,   'codice',         'Cod.', col_width=40, is_editable=True, linktable_info=linktable_stato)
            self.AddColumn(stato,   'descriz',        'Stato', col_width=200, is_editable=True)
            
            self.AddColumn(aliqiva, 'codice',         'Cod.', col_width=40, is_editable=True, linktable_info=linktable_aliqiva)
            self.AddColumn(aliqiva, 'descriz',        'Aliquota', col_width=200, is_editable=True)
            
            self.AddColumn(clifat,  'codice',         'Cod.', col_width=40, is_editable=True, linktable_info=linktable_clifat)
            self.AddColumn(clifat,  'descriz',        'ClienteFatt.', col_width=200, is_editable=True)
            
            self.AddColumn(test,    'prova_data',     'TestData', col_type=self.TypeDateTime(), is_editable=True)
            
            def TestCella(row, col):
                return '%s-%s' % (row, col)
            self.AddColumn(col_name='TestCella', label='prova funzione', get_cell_func=TestCella)
            
            self.CreateGrid()
            
            def TestPippo(event):
                print 'pippo'
            self.AppendContextMenuVoice('pippo', TestPippo)
            def TestPluto(event):
                print 'pluto'
            self.AppendContextMenuVoice('pluto', TestPluto)
            self.AppendContextMenuVoice('-', None)
            self.AppendContextMenuVoice('pluto', TestPluto, False)
        
        def CreateNewRow(self, *args, **kwargs):
            ADB_Grid.CreateNewRow(self, *args, **kwargs)
            return True
        
        def CellEditBeforeUpdate(self, row, gridcol, col, value):
            print 'CellBeforeAfterUpdate: row=%d, col=%d, value=%s' % (row, gridcol, value)
            return "OK" in value
        
        def CellEditAfterUpdate(self, row, gridcol, col, value):
            print 'CellEditAfterUpdate: row=%d, col=%d, value=%s' % (row, gridcol, value)
        
        def OnCellSelected(self, event):
            print 'OnCellSelected: row=%d, col=%d' % (event.GetRow(), event.GetCol())
            event.Skip()
        
        def OnRowSelected(self, event):
            print 'OnRowSelected: row=%d' % event.GetRow()
            event.Skip()
        
        def OnCellClicked(self, event):
            print 'OnCellClicked: row=%d, col=%d' % (event.GetRow(), event.GetCol())
            self.db_table.MoveRow(event.GetRow())
            print 'is_blacklisted=%s' % self.db_table.anag.is_blacklisted
            event.Skip()
        
        def OnCellDoubleClicked(self, event):
            print 'OnCellDoubleClicked: row=%d, col=%d' % (event.GetRow(), event.GetCol())
            event.Skip()
        
        def OnCellRightClicked(self, event):
            print 'OnCellRightClicked: row=%d, col=%d' % (event.GetRow(), event.GetCol())
            event.Skip()
        
        def OnCellRightDoubleClicked(self, event):
            print 'OnCellRightDoubleClicked: row=%d, col=%d' % (event.GetRow(), event.GetCol())
            event.Skip()
        
        def CreateContextMenu(self):
            pass
    
    a = TestApp()
    a.MainLoop()
