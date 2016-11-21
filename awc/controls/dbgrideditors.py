#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/dbgrideditors.py
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

import string

import wx
import wx.grid as gridlib

import awc.controls.windows as aw

import awc.controls.datectrl
import awc.controls.linktable
import awc.controls.numctrl
import awc.controls.textctrl
import awc.controls.checkbox

import awc.controls.linktable

from awc.controls import CELLEDIT_AFTER_UPDATE, CELLEDIT_BEFORE_UPDATE

_evtEDITORSHOWN = wx.NewEventType()
EVT_EDITORSHOWN = wx.PyEventBinder(_evtEDITORSHOWN, 0)

class EditorShownEvent(wx.PyCommandEvent):

    def __init__(self, row, col):
        wx.PyCommandEvent.__init__(self, _evtEDITORSHOWN)
        self._row = row
        self._col = col

    def GetRow(self):
        return self._row

    def GetCol(self):
        return self._col


class CellEditorsMixin(object):

    editing = False

    def EndEdit(self, grid, row, col, changed=False, moveCursor=True):
        self.editing = False
        if moveCursor:#changed:
            def SetPos():
                grid.TestNewColumn(row, col)
                grid.SetFocus()
            wx.CallAfter(SetPos)

    def TestNewRow(self, grid, row, value):
        out = True
        insreq = False
        data = grid.GetTable().data
        if data is None:
            insreq = True
        elif row == len(data):
            insreq = True
        if insreq:
            if value:
                table = grid.GetTable()
                out = table.newRowCB()
                if type(out) is not bool:
                    out = True
                #grid.ResetView()
            else:
                out = False
        return out

    def GetDefaultValue(self, grid, row, col, editor):
        startValue = None
        dvfunc = grid.GetDefaultValueCB()
        if dvfunc:
            startValue = dvfunc(row, col, editor)
        return startValue

    def IsAcceptedKey(self, evt):
        """
        Return True to allow the given key to start editing: the base class
        version only checks that the event has no modifiers.  F2 is special
        and will always start the editor.
        """
        out = False
        if not (evt.ControlDown() or evt.AltDown())\
           and evt.GetKeyCode() != wx.WXK_SHIFT:
            key = evt.GetKeyCode()
            out = (key>=48 and key<=57) or\
                (key>=wx.WXK_NUMPAD0 and key<=wx.WXK_NUMPAD9)
        return out

    def TrigEditorShownEvent(self, row, col):
        evt = EditorShownEvent(row, col)
        evt.SetEventObject(self._tc)
        self._tc.GetEventHandler().AddPendingEvent(evt)


# ------------------------------------------------------------------------------


class DateCellEditor(gridlib.PyGridCellEditor, CellEditorsMixin):
    """
    CellEditor di tipo LinkTable, per ottenere l'help dei record di una
    determinata tabella all'interno di una cella di DbGrid.
    """
    def __init__(self):
        gridlib.PyGridCellEditor.__init__(self)
        CellEditorsMixin.__init__(self)

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = awc.controls.datectrl.DateCtrl(parent, id, "",\
                                                  pos = (-100, -100))
        self.SetControl(self._tc)

        win = parent
        while win:
            win = win.GetParent()
            if win != None:
                if isinstance( win, ( wx.Frame, wx.Dialog ) ):
                    break
        if win:
            self._tc.Bind(awc.controls.datectrl.EVT_DATEFOCUSLOST,
                     self.OnFocusLost)
            for ctr in (self._tc.maskedCtrl, self._tc.buttonCalendar):
                ctr.Bind(wx.EVT_CHAR, self.OnTestEscape)
            self.grid = parent.GetParent()

#        if evtHandler:
#            self._tc.PushEventHandler(evtHandler)

    def OnFocusLost(self, event):
        if self.grid._edrow is None:
            return
        if True:#self._tc.GetValue() is not None:
            #self.grid.SetGridCursor(self.grid._edrow, self.grid._edcol)
            self.EndEdit(self.grid._edrow, self.grid._edcol, self.grid)
            self.Show(0)
            wx.CallAfter(self.grid.SetFocusTo)
        event.Skip()

    def OnTestEscape(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            CellEditorsMixin.EndEdit(self, self.grid, self.grid._edrow, self.grid._edcol, False)
            self.startValue = None
        event.Skip()

    def SetInitialCursor(self):
        self._tc.maskedCtrl._SetInsertionPoint(0)

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr=None):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        self._tc.Enable()
        #self.base_Show(show, attr)
        gridlib.PyGridCellEditor.Show(self, show, attr)
        if show:
            self.editing = True

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        pass

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        table = grid.GetTable()
        rscol = table.rsColumns[col]
        try:
            self.startValue = table.data[row][rscol]
        except:
            self.startValue = self.GetDefaultValue(grid, row, col, self)
        self._tc.SetValue(self.startValue)
        self._tc.SetFocus()
        self.TrigEditorShownEvent(row, col)
        wx.CallAfter(self.SetInitialCursor)

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing or not hasattr(self, 'startValue'):
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            table = grid.GetTable()
            # callback x valid. cella prima dell'aggiornamento del recordset
            if table.TestAfterEdit(CELLEDIT_BEFORE_UPDATE, row, col, val):
                # callback x creazione nuova riga
                if self.TestNewRow(grid, row, val):
                    # aggiornamento recordset
                    rscol = table.rsColumns[col]
                    if rscol>=0:
                        table.data[row][rscol] = val
                    table.ForceResetView()
                    changed = True
                    # callback successivo all'aggiornamento del recordset
                    table.TestAfterEdit(CELLEDIT_AFTER_UPDATE, row, col, val)
        CellEditorsMixin.EndEdit(self, grid, row, col, changed)
        self.startValue = None
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        self._tc.SetValue(self.startValue)

    def IsAcceptedKey(self, evt):
        """
        Return True to allow the given key to start editing: the base class
        version only checks that the event has no modifiers.  F2 is special
        and will always start the editor.
        """
        key = evt.GetKeyCode()
        ch = None
        if key in\
           [ wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3,
             wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7,
             wx.WXK_NUMPAD8, wx.WXK_NUMPAD9 ]:
            ch = ch = chr(ord('0') + key - wx.WXK_NUMPAD0)
        ch = chr(key)
        return ch.isdigit()

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        key = evt.GetKeyCode()
        ch = None
        if key in\
           [ wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3,
             wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7,
             wx.WXK_NUMPAD8, wx.WXK_NUMPAD9 ]:
            ch = ch = chr(ord('0') + key - wx.WXK_NUMPAD0)
        ch = chr(key)
        if ch.isdigit():
            self._tc.maskedCtrl.SetValue(ch)
            wx.CallAfter(lambda: self._tc.maskedCtrl._SetInsertionPoint(1))

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        pass

    def Destroy(self):
        """final cleanup"""
        #self.base_Destroy()
        gridlib.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        return DateCellEditor()


# ------------------------------------------------------------------------------


class DateTimeCellEditor(DateCellEditor):

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = awc.controls.datectrl.DateTimeCtrl(parent, id, "",\
                                                      pos = (-100, -100))
        self.SetControl(self._tc)

        win = parent
        while win:
            win = win.GetParent()
            if win != None:
                if isinstance( win, ( wx.Frame, wx.Dialog ) ):
                    break
        if win:
            self._tc.Bind(awc.controls.datectrl.EVT_DATEFOCUSLOST,
                     self.OnFocusLost)
            for ctr in (self._tc.maskedCtrl, self._tc.buttonCalendar):
                ctr.Bind(wx.EVT_CHAR, self.OnTestEscape)
            self.grid = parent.GetParent()


# ------------------------------------------------------------------------------


class DataLinkCellEditor(gridlib.PyGridCellEditor, CellEditorsMixin):
    """
    CellEditor di tipo LinkTable, per ottenere l'help dei record di una
    determinata tabella all'interno di una cella di DbGrid.
    """
    baseclass = None
    def __init__(self, tabname, rscolid, rscolcod, rscoldes=None,\
                 cardclass = None, filter = None, filterlinks = None,\
                 eventBindings=None, oncreate=None):

        if eventBindings is None:
            eventBindings = []

        if rscoldes is None and rscolcod is not None:
            rscoldes = rscolcod+1

        if self.baseclass is None:
            self.baseclass = awc.controls.linktable.LinkTable

        self.lt_tabname = tabname
        self.lt_rscolid = rscolid
        self.lt_rscolcod = rscolcod
        self.lt_rscoldes = rscoldes
        self.lt_cardclass = cardclass
        self.lt_filter = filter
        self.lt_filterlinks = filterlinks
        self.lt_eventBindings = eventBindings
        self.lt_oncreate = oncreate
        self._tc = None

        gridlib.PyGridCellEditor.__init__(self)
        CellEditorsMixin.__init__(self)

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = self.baseclass(parent, id=id, pos = (-100,-100),
                                  fromgrid=True)

        if self.lt_tabname:
            self._tc.SetDataLink(self.lt_tabname,\
                                 cardclass = self.lt_cardclass,\
                                 filter = self.lt_filter,\
                                 filterlinks = self.lt_filterlinks)
        for container, callable in self.lt_eventBindings:
            container.Bind(awc.controls.linktable.EVT_LINKTABCHANGED,\
                           callable, self._tc)
        #self._tc.KillSizers()
        self.SetControl(self._tc)

        win = parent
        while win:
            win = win.GetParent()
            if win != None:
                if isinstance( win, ( wx.Frame, wx.Dialog ) ):
                    break
        if win:
            win.Bind(awc.controls.linktable.EVT_LINKTABCHANGED,\
                     self.OnValueChanged, self._tc)
            win.Bind(awc.controls.linktable.EVT_LINKTABFOCUSLOST,\
                     self.OnFocusLost, self._tc)
            for ctr in (self._tc._ctrcod, self._tc._ctrdes):
                ctr.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
            self.grid = parent.GetParent()

        if evtHandler:
            self._tc.SetExactCode(True)
            #self._tc._ctrcod.PushEventHandler(evtHandler)
            #self._tc._ctrdes.PushEventHandler(evtHandler)

        if self.lt_oncreate:
            self.lt_oncreate(self._tc, self, parent)

    def OnKeyDown(self, event):
        if event.GetKeyCode() == 27:
            self._tc._PostEventFocusLost()
            def RestorePos():
                self.Reset()
                self.grid.SetGridCursor(self.grid._edrow, self.grid._edcol)
            wx.CallAfter(RestorePos)
        event.Skip()

    def OnFocusLost(self, event):
        if not event.GetEventObject().HasFocus():
            self.Show(0)
            event.Skip()

    def OnValueChanged(self, event):
        if self.grid._edrow is None:
            return
        if self._tc.GetValue() is not None:
            #self.grid.SetGridCursor(self.grid._edrow, self.grid._edcol)
            self.EndEdit(self.grid._edrow, self.grid._edcol, self.grid)
            self.Show(0)
        event.Skip()

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        grid = self.GetControl().GetParent().GetParent()
#        col = grid._edcol
        width = 0
        if self.lt_rscolcod is None:
            wcod = 0
            colcod = None
        else:
            colcod = grid._edcol
            wcod = grid.GetColSize(colcod)
        if self.lt_rscoldes is None:
            coldes = None
            wdes = 0
        else:
            coldes = grid._edcol
            if colcod is not None:
                coldes += 1
            wdes = max(grid.GetColSize(coldes), 80)
#        width = wcod+wdes+2
        width = wcod+wdes
        if wcod and wdes:
            width += 2
        height = rect.height
        #self._tc.SetDimensions(rect.x, rect.y, width+2, height+2,
                               #wx.SIZE_ALLOW_MINUS_ONE)
        self._tc.NORECALCS = True
        self._tc.SetDimensions(rect.x, rect.y, wcod, wdes, height+2,\
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr=None):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        if not show and self._tc._helpInProgress: return
        if not show and hasattr(self._tc, '_retain_focus'):
            show = True
        self._tc.Enable()
        #self.base_Show(show, attr)
        gridlib.PyGridCellEditor.Show(self, show, attr)
        if show:
            self.editing = True
        else:
            self.grid.GetGridWindow().SetFocus()

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        pass

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        for c in self._tc.GetChildren()[0].GetChildren():
            c.Enable()
        self.startValue = None
        try:
            self.startValue = grid.GetTable().data[row][self.lt_rscolid]
        except:
            self.startValue = self.GetDefaultValue(grid, row, col, self)
        self._tc.notifyChanges = False
        self._tc.SetValue(self.startValue, stopevents=False)
        self._tc.notifyChanges = True
        if hasattr(self._tc, 'EditorShownCB'):
            self._tc.EditorShownCB()
        self.TrigEditorShownEvent(row, col)
        self._tc.SetFocus()

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing or not hasattr(self, 'startValue'):
            return
        if self._tc._helpInProgress:
            self.Show(0)
        changed = False
        rel_id = self._tc.GetValue()
        relcod = self._tc.GetValueCod()
        reldes = self._tc.GetValueDes()
        if rel_id != self.startValue:
            # callback x valid. cella prima dell'aggiornamento del recordset
            table = grid.GetTable()
            if table.TestAfterEdit(CELLEDIT_BEFORE_UPDATE, row, col, rel_id):
                # callback x creazione nuova riga
                if self.TestNewRow(grid, row, rel_id):
                    # aggiornamento recordset
                    if self.lt_rscolid>=0:
                        data = table.data
                        data[row][self.lt_rscolid] = rel_id
                        if self.lt_rscolcod>0:
                            data[row][self.lt_rscolcod] = relcod
                        if self.lt_rscoldes>0:
                            data[row][self.lt_rscoldes] = reldes
                    table.ForceResetView()
                    changed = True
                    # callback successivo all'aggiornamento del recordset
                    table.TestAfterEdit(CELLEDIT_AFTER_UPDATE, row, col, rel_id)
        CellEditorsMixin.EndEdit(self, grid, row, col, changed)
        self.startValue = None
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        self._tc.SetValue(self.startValue)
        #workaround: esc non esce dalla digitazione della cella
        self.Show(0)

    #def IsAcceptedKey(self, evt):
        #"""
        #Return True to allow the given key to start editing: the base class
        #version only checks that the event has no modifiers.  F2 is special
        #and will always start the editor.
        #"""
        #return (not (evt.ControlDown() or evt.AltDown()) and
                #evt.GetKeyCode() != wx.WXK_SHIFT)

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        key = evt.GetKeyCode()
        ch = None
        if key in\
           [ wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3,
             wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7,
             wx.WXK_NUMPAD8, wx.WXK_NUMPAD9 ]:
            ch = chr(ord('0') + key - wx.WXK_NUMPAD0)
        else:
            ch = unichr(key)

        if ch:
            if self._tc.initfocus == awc.controls.linktable.INITFOCUS_CODICE:
                c = self._tc._ctrcod
            else:
                c = self._tc._ctrdes
            def startedit():
                c.SetValue('')
                c.SetValue(ch)
                wx.CallAfter(lambda: c.SetInsertionPointEnd())
            wx.CallAfter(startedit)
        #else:
        evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        pass

    def Destroy(self):
        """final cleanup"""
        #self.base_Destroy()
        gridlib.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        return DataLinkCellEditor(self.lt_tabname,\
                                  self.lt_rscolid,\
                                  self.lt_rscolcod,\
                                  self.lt_rscoldes,\
                                  self.lt_cardclass,\
                                  self.lt_filter,\
                                  self.lt_filterlinks)


# ------------------------------------------------------------------------------


class NumericCellEditor(gridlib.PyGridCellEditor, CellEditorsMixin):
    """
    CellEditor di tipo numerico, per formattazione cifre intere e con la
    virgola.
    """
    def __init__(self, nint, ndec = 0):
        gridlib.PyGridCellEditor.__init__(self)
        CellEditorsMixin.__init__(self)
        self._nint = nint
        self._ndec = ndec

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = awc.controls.numctrl.NumCtrl(parent, id,\
                                                pos = (-100, -100),\
                                                integerWidth = self._nint,\
                                                fractionWidth = self._ndec)

        self.SetControl(self._tc)
        self.grid = parent.GetParent()
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def SetInitialCursor(self):
        mask = wx.TextCtrl.GetValue(self._tc)
        if "," in mask: pos = mask.index(",")
        else:           pos = len(mask)
        self._tc._SetInsertionPoint(pos)

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        self._tc.Enable()
        #self.base_Show(show, attr)
        gridlib.PyGridCellEditor.Show(self, show, attr)
        if show:
            self.editing = True
        else:
            self.grid.GetGridWindow().SetFocus()

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        pass

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        table = grid.GetTable()
        rscol = table.rsColumns[col]
        self.startValue = None
        try:
            self.startValue = table.data[row][rscol]
        except:
            self.startValue = self.GetDefaultValue(grid, row, col, self)
        self._tc.SetValue(self.startValue)
        self._tc.SetFocus()
        self.TrigEditorShownEvent(row, col)
        wx.CallAfter(self.SetInitialCursor)

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing or not hasattr(self, 'startValue'):
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            table = grid.GetTable()
            #----data = table.data
            # callback x valid. cella prima dell'aggiornamento del recordset
            if table.TestAfterEdit(CELLEDIT_BEFORE_UPDATE, row, col, val):
                # callback x creazione nuova riga
                if self.TestNewRow(grid, row, val):
                    # aggiornamento recordset
                    rscol = table.rsColumns[col]
                    if rscol>=0:
                        data = table.data
                        #data[row][rscol] = val
                        data[row][rscol] = self._tc.GetValue() #potrebbe essere stato variato dai callback
                    table.ForceResetView()
                    changed = True
                    # callback successivo all'aggiornamento del recordset
                    table.TestAfterEdit(CELLEDIT_AFTER_UPDATE, row, col, val)
        CellEditorsMixin.EndEdit(self, grid, row, col, changed)
        self.startValue = None
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        key = evt.GetKeyCode()
        ch = None
        if key>=48 and key<=57:
            #tasti numerici tastiera
            ch = chr(key)
        elif key>=wx.WXK_NUMPAD0 and key<=wx.WXK_NUMPAD9:
            #tasti numerici tastierino
            ch = chr(ord('0') + key - wx.WXK_NUMPAD0)
        if ch:
            self._tc.SetValue(ch)
            wx.CallAfter(self.SetInitialCursor)
        else:
            evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        pass

    def Destroy(self):
        """final cleanup"""
        #self.base_Destroy()
        gridlib.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        return DataLinkCellEditor(self.lt_tabname,\
                                  self.lt_rscolid,\
                                  self.lt_rscolcod,\
                                  self.lt_rscoldes,\
                                  self.lt_cardclass,\
                                  self.lt_filter)


# ------------------------------------------------------------------------------


class TextCellEditor(gridlib.PyGridCellEditor, CellEditorsMixin):
    """
    CellEditor di tipo stringa.
    """
    _lowercase = False

    def __init__(self):
        gridlib.PyGridCellEditor.__init__(self)
        CellEditorsMixin.__init__(self)
        self._maxlen = None

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = awc.controls.textctrl.TextCtrl(parent, id,\
                                                  pos = (-100, -100))
        if self._maxlen is not None:
            self._tc.SetMaxLength(self._maxlen)
        self._tc.ForceUpperCase(not self._lowercase)
        self.SetControl(self._tc)
        self.grid = parent.GetParent()
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def SetInitialCursor(self):
        mask = wx.TextCtrl.GetValue(self._tc)
        if "," in mask: pos = mask.index(",")
        else:           pos = len(mask)
        self._tc.SetInsertionPoint(len(wx.TextCtrl.GetValue(self._tc)))

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        self._tc.Enable()
        if self._maxlen is not None:
            self._tc.SetMaxLength(self._maxlen)
        #self.base_Show(show, attr)
        gridlib.PyGridCellEditor.Show(self, show, attr)
        if show:
            self.editing = True
        else:
            self.grid.GetGridWindow().SetFocus()

    def SetMaxLength(self, max):
        self._maxlen = max

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        pass

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        table = grid.GetTable()
        rscol = table.rsColumns[col]
        self.startValue = None
        try:
            self.startValue = table.data[row][rscol]
        except:
            self.startValue = self.GetDefaultValue(grid, row, col, self)
        self._tc.SetValue(self.startValue)
        self._tc.SetFocus()
        self.TrigEditorShownEvent(row, col)
        wx.CallAfter(self.SetInitialCursor)

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing or not hasattr(self, 'startValue'):
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            table = grid.GetTable()
            data = table.data
            # callback x valid. cella prima dell'aggiornamento del recordset
            if table.TestAfterEdit(CELLEDIT_BEFORE_UPDATE, row, col, val):
                # callback x creazione nuova riga
                if self.TestNewRow(grid, row, val):
                    # aggiornamento recordset
                    rscol = table.rsColumns[col]
                    if rscol>=0:
                        try:
                            data[row][rscol] = val
                        except:
                            msg='Intercettato errore\nControllare quanto digitato.'
                            aw.awu.MsgDialog(None, msg, style=wx.ICON_ERROR)
                            pass
                    table.ForceResetView()
                    changed = True
                    # callback successivo all'aggiornamento del recordset
                    table.TestAfterEdit(CELLEDIT_AFTER_UPDATE, row, col, val)
        CellEditorsMixin.EndEdit(self, grid, row, col, changed)
        self.startValue = None
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    #def IsAcceptedKey(self, evt):
        #"""
        #Return True to allow the given key to start editing: the base class
        #version only checks that the event has no modifiers.  F2 is special
        #and will always start the editor.
        #"""
        #return (not (evt.ControlDown() or evt.AltDown()) and
                #evt.GetKeyCode() != wx.WXK_SHIFT)

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        key = evt.GetKeyCode()
        #ch = None
        #if key>=48 and key<=57:
            ##tasti numerici tastiera
            #ch = chr(key)
        #elif key in\
           #[ wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3,
             #wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7,
             #wx.WXK_NUMPAD8, wx.WXK_NUMPAD9 ]:
            ##tasti numerici tastierino
            #ch = chr(ord('0') + key - wx.WXK_NUMPAD0)
        ch = unichr(key)
        if ch:
            self._tc.SetValue(ch)
            wx.CallAfter(self.SetInitialCursor)
        else:
            evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        pass

    def Destroy(self):
        """final cleanup"""
        #self.base_Destroy()
        gridlib.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        #return DataLinkCellEditor(self.lt_tabname,\
                                  #self.lt_rscolid,\
                                  #self.lt_rscolcod,\
                                  #self.lt_rscoldes,\
                                  #self.lt_cardclass,\
                                  #self.lt_filter)
        pass


class TextLowerCaseCellEditor(TextCellEditor):
    """
    CellEditor di tipo stringa, caratteri minuscoli ammessi
    """
    _lowercase = True


# ------------------------------------------------------------------------------


class CheckBoxCellEditor(gridlib.PyGridCellEditor, CellEditorsMixin):
    """
    CellEditor di tipo checkbox.
    """
    def __init__(self, valCheck = 1, valNotCheck = 0):
        gridlib.PyGridCellEditor.__init__(self)
        CellEditorsMixin.__init__(self)
        self.valueCheck = valCheck
        self.valueNotCheck = valNotCheck

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = awc.controls.checkbox.CheckBox(\
            parent, id, pos = (-100, -100))
        self._tc.SetDataLink("", {True:  self.valueCheck,\
                                  False: self.valueNotCheck})
        self.SetControl(self._tc)
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    #def SetInitialCursor(self):
        #mask = wx.TextCtrl.GetValue(self._tc)
        #if "," in mask: pos = mask.index(",")
        #else:           pos = len(mask)
        #self._tc._SetInsertionPoint(pos)

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        #self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               #wx.SIZE_ALLOW_MINUS_ONE)
        self._tc.SetDimensions(rect.x, rect.y, 20, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        self._tc.Enable()
        #self.base_Show(show, attr)
        gridlib.PyGridCellEditor.Show(self, show, attr)
        if show:
            self.editing = True

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        pass

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        table = grid.GetTable()
        rscol = table.rsColumns[col]
        self.startValue = None
        try:
            self.startValue = table.data[row][rscol]
        except:
            self.startValue = self.GetDefaultValue(grid, row, col, self)
        self._tc.SetValue(self.startValue)
        self._tc.SetFocus()
        self.TrigEditorShownEvent(row, col)
        #wx.CallAfter(self.SetInitialCursor)

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing or not hasattr(self, 'startValue'):
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            # callback x valid. cella prima dell'aggiornamento del recordset
            table = grid.GetTable()
            if table.TestAfterEdit(CELLEDIT_BEFORE_UPDATE, row, col, val):
                # callback x creazione nuova riga
                if self.TestNewRow(grid, row, val):
                    # aggiornamento recordset
                    rscol = table.rsColumns[col]
                    if rscol>=0:
                        table.data[row][rscol] = val
                    changed = True
                    # callback successivo all'aggiornamento del recordset
                    table.TestAfterEdit(CELLEDIT_AFTER_UPDATE, row, col, val)
        CellEditorsMixin.EndEdit(self, grid, row, col, changed)
        self.startValue = None
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        self._tc.SetValue(self.startValue)
        #self._tc.SetInsertionPointEnd()

    #def IsAcceptedKey(self, evt):
        #"""
        #Return True to allow the given key to start editing: the base class
        #version only checks that the event has no modifiers.  F2 is special
        #and will always start the editor.
        #"""
        #return (not (evt.ControlDown() or evt.AltDown()) and
                #evt.GetKeyCode() == wx.WXK_SPACE)

    #def StartingKey(self, evt):
        #"""
        #If the editor is enabled by pressing keys on the grid, this will be
        #called to let the editor do something about that first key if desired.
        #"""
        #key = evt.GetKeyCode()
        #ch = None
        #if key == wx.WXK_SPACE:
            #self._tc.SetValue(not self._tc.GetValue())
        #else:
            #evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        pass

    def Destroy(self):
        """final cleanup"""
        #self.base_Destroy()
        gridlib.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        CheckBoxCellEditor(self.valueCheck, self.valueNotCheck)


# ------------------------------------------------------------------------------


class FlatCheckBoxCellEditor(CheckBoxCellEditor):

    #def IsAcceptedKey(self, evt):
        #"""
        #Return True to allow the given key to start editing: the base class
        #version only checks that the event has no modifiers.  F2 is special
        #and will always start the editor.
        #"""
        #return False

    #def StartingKey(self, evt):
        #"""
        #If the editor is enabled by pressing keys on the grid, this will be
        #called to let the editor do something about that first key if desired.
        #"""
        #if evt.GetKeyCode() == wx.WXK_SPACE:
            ##self._tc.SetValue(ch)
            #wx.CallAfter(self.SetInitialCursor)
        #else:
            #evt.Skip()

    def Create(self, *args, **kwargs):
        pass

    def SetSize(self, *args, **kwargs):
        pass

    def Show(self, *args, **kwargs):
        pass

    def BeginEdit(self, *args, **kwargs):
        pass

    def EndEdit(self, *args, **kwargs):
        pass

    def OnKeyPressed(self, event):
        # space deve invertire lo stato del checkbox, però
        # da qui non si può intercettare il tasto premuto
        # avviene quindi il binding EVT_KEY a livello di chiamante (Grid.SetData)
        # qui devo capire se il tasto è stato premuto in corrispondenza di una
        # colonna che ha questa classe come editor, se si allora inverto lo
        # stato del checkbox di questa classe
        if event.GetKeyCode() == wx.WXK_SPACE:
            w = event.GetEventObject()
            if w:
                w = w.GetParent()
                if w:
                    if hasattr(w, 'GetGridCursorCol'):
                        row = w.GetGridCursorRow()
                        col = w.GetGridCursorCol()
                        e = w.GetCellEditor(row, col)
                        if e is self:
                            #ok, sono io :D
                            a = w.colAttr[col]
                            if a:
                                if not a.IsReadOnly():
                                    t = w.GetTable()
                                    if col in t.rsColumns:
                                        rscol = t.rsColumns[col]
                                        rs = t.data
                                        v = rs[row][rscol]
                                        if type(v) is int:
                                            v = 1-v
                                        elif type(v) is bool:
                                            v = not v
                                        rs[row][rscol] = v
                                        w.Refresh()
        event.Skip()


# ------------------------------------------------------------------------------


import images

class CheckBoxCellRenderer(gridlib.PyGridCellRenderer):

    def __init__(self):
        gridlib.PyGridCellRenderer.__init__(self)
        self.bmp_yes = images.getCheckYesBitmap()
        self.bmp_no = images.getCheckNoBitmap()

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        #dc.SetBackgroundMode(wx.SOLID)
        #bgcol = wx.WHITE
        #celattr = grid.GetTable().GetAttr(row, col)
        #if celattr is not None:
            #bgcol = celattr.GetBackgroundColour()
        #dc.SetBrush(wx.Brush(bgcol, wx.SOLID))
        #dc.SetPen(wx.TRANSPARENT_PEN)
        #dc.DrawRectangleRect(rect)

        ##dc.SetFont(attr.GetFont())

        dim = 16
        h = rect[3]
        x = rect[0]+6
        y = rect[1]+(h-dim)/2
        checkRect = (x, y, dim, dim)
        dc.SetBackgroundMode(wx.SOLID)

        bgcol = wx.WHITE
        celattr = attr#grid.GetTable().GetAttr(row, col)
        if celattr is not None:
            bgcol = celattr.GetBackgroundColour()
        dc.SetBrush(wx.Brush(bgcol, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect)

        value = grid.GetTable().GetValue(row, col)
        if value:
            bmp = self.bmp_yes
        else:
            bmp = self.bmp_no
        dc.DrawBitmap(bmp, x, y)

    def GetBestSize(self, grid, attr, dc, row, col):
        #text = grid.GetCellValue(row, col)
        #dc.SetFont(attr.GetFont())
        #w, h = dc.GetTextExtent(text)
        #return wx.Size(w, h)
        return wx.Size(20, 20)

    def Clone(self):
        return CheckBoxCellRenderer()


# ------------------------------------------------------------------------------


class ImageCellRenderer(gridlib.PyGridCellRenderer):

    def __init__(self, width, height):
        gridlib.PyGridCellRenderer.__init__(self)
        self.width = width
        self.height = height

    def SetBitmap(self, bmp):
        self.bitmap = bmp

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        try:
            bmp = grid.GetCellBitmap(row, col)
        except:
            bmp = None
        if bmp:
            x = rect[0]
            y = rect[1]
            dc.DrawBitmap(bmp, x, y)
        else:
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetBrush(wx.Brush('white', wx.SOLID))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangleRect(rect)

    def GetBestSize(self, grid, attr, dc, row, col):
        #text = grid.GetCellValue(row, col)
        #dc.SetFont(attr.GetFont())
        #w, h = dc.GetTextExtent(text)
        #return wx.Size(w, h)
        return wx.Size(self.width, self.height)

    def Clone(self):
        return ImageCellRenderer(self.width, self.height)
