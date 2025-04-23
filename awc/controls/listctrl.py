#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/listctrl.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
# Copyright:    (C) 2016 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
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
import awc.controls.mixin as cmix
import os, tempfile, codecs, csv

CSVFORMAT_ASGRID = 0
CSVFORMAT_DELIMITER = ';'
CSVFORMAT_QUOTECHAR = '"'
CSVFORMAT_QUOTING = csv.QUOTE_MINIMAL
CSVFORMAT_EXCELZERO = False

from wx.lib.mixins.listctrl import CheckListCtrlMixin


class ListCtrl(wx.ListCtrl, cmix.ControlsMixin):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        cmix.ControlsMixin.__init__(self)
        
        self.Bind(wx.EVT_SET_FOCUS,  self.OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)

    def OnFocusGained(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()

    def OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()

    def IsEditable(self):
        return True

    def ExportCsv(self):
        csvrs = []
        lTitoli=[]
        row=[]
        nColumn=self.GetColumnCount()
        for i in range(0, nColumn):
            lTitoli.append(self.GetColumn(i).GetText())

        for i in range(0, self.GetItemCount()):
            row=[]
            for j in range(0, nColumn):
                row.append(self.GetItem(i, j).GetText())
            csvrs.append(row)


        if len(csvrs)>0:
            tmpfile = tempfile.NamedTemporaryFile(suffix='.csv')
            tmpname = tmpfile.name
            tmpfile.close()
            tmpfile = open(tmpname, 'wb')
            tmpfile.write(codecs.BOM_UTF8)
            wx.GetApp().AppendTempFile(tmpname)
            writer = csv.writer(tmpfile,
                                delimiter=CSVFORMAT_DELIMITER,
                                quotechar=CSVFORMAT_QUOTECHAR,
                                doublequote=True,
                                skipinitialspace=False,
                                lineterminator='\r\n',
                                quoting=int(CSVFORMAT_QUOTING))
            csvrs.insert(0, lTitoli)
            writer.writerows(csvrs)
            tmpfile.close()
            os.startfile(tmpname)

class CheckListCtrl(ListCtrl, CheckListCtrlMixin):
    listCheck = []
    
    def __init__(self, *args, **kwargs):
        ListCtrl.__init__(self, *args, **kwargs)
        CheckListCtrlMixin.__init__(self)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)


    def OnItemSelected(self, evt):
        print 'SELEZIONO ', evt
        evt.Skip()
        
    def OnItemDeselected(self, evt):
        print 'DESELEZIONO', evt
        evt.Skip()

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.m_itemIndex)

    def DeleteAllItems(self):
        self.listCheck = []
        ListCtrl.DeleteAllItems(self)       
        

    # this is called by the base class when an item is checked/unchecked
    def OnCheckItem(self, index, flag):
        data = self.GetItemData(index)
        if flag:
            self.listCheck.append(index)
            what = "checked"
        else:
            self.listCheck.remove(index)
            what = "unchecked"
        print data, index, what, self.listCheck
      

