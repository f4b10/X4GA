#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/checkbox.py
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
import awc.controls.mixin as cmix


class CheckBox(wx.CheckBox,\
               cmix.ControlsMixin):
    def __init__(self, *args, **kwargs):

        wx.CheckBox.__init__(self, *args, **kwargs)
        cmix.ControlsMixin.__init__(self)

        self._values = {True: True, False: False}

        self.Bind(wx.EVT_SET_FOCUS,  self._OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self._OnFocusLost)

    def SetDataLink(self, name=None, values=None):
        if name is not None:
            self.SetName(name)
        if type(values) in (list, tuple):
            values = {True:  values[0],
                      False: values[1]}
        self._values = values

    def SetValue(self, value):
        val = False
        if type(value) == bool:
            #passato vero/falso riferito al controllo, cerco corrispondente
            #valore nel datalink
            if self._values.has_key(value):
                self.__value = self._values[value]
                val = value
        else:
            #passato il valore del datalink, adeguo lo stato vero/falso
            #del controllo
            self.__value = value
            if self._values.has_key(True):
                if value == self._values[True]:
                    val = True
        wx.CheckBox.SetValue(self, val)

    def GetValue(self):
        out = None
        if self._values.has_key(True) and self._values.has_key(False):
            out = self._values[ wx.CheckBox.GetValue(self) ]
        return out

    #def SetBackgroundColour(self, color):
        #pass

    def _OnFocusGained(self, event):
        self.AdjustBackgroundColor(self.IsEnabled())
        event.Skip()

    def _OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()

    #def Enable(self, e=True):
        #wx.CheckBox.Enable(self, e)
        #cmix.ControlsMixin.Enable(self, e)

    #def Disable(self):
        #self.Enable(False)

    #def IsEnabled(self):
        #return cmix.ControlsMixin.IsEnabled(self)


# ------------------------------------------------------------------------------


class RCheckBox(CheckBox):
    def __init__(self, parent, id, label,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        style = style|wx.ALIGN_RIGHT
        CheckBox.__init__(self, parent, id, label, pos, size, style)


# ------------------------------------------------------------------------------


class CheckListBox(wx.CheckListBox):
    PyData=None
    _context_menu = None

    def __init__(self, *args, **kwargs):

        wx.CheckListBox.__init__(self, *args, **kwargs)
        self.PyData={}
        self._context_menu = []        
        self.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)
        

    def OnContextMenu(self, evt):
        self.ShowContextMenu(evt.GetPosition())
        evt.Skip()

    def ResetContextMenu(self):
        del self._context_menu[:]

    def AppendContextMenuVoice(self, label, function, is_enabled=True):
        self._context_menu.append({'label': label,
                                   'function': function,
                                   'is_enabled': is_enabled,})



    def ShowContextMenu(self, position):
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
        self.PopupMenu(menu, position)
        menu.Destroy()

        

    def GetSelections(self):
        sel = []
        for n in range(self.GetCount()):
            if self.IsChecked(n):
                sel.append(n)
        return tuple(sel)

    def SetPyData(self, itemIndex, value):
        self.PyData[itemIndex]=value

    def GetPyData(self, itemIndex):
        value=None
        if itemIndex in self.PyData.keys():
            value=self.PyData[itemIndex]
        return value

    def GetValue(self):
        check=''
        lChecked=self.GetSelections()
        for e in lChecked:
            check='%s%s|' % (check, self.GetPyData(e))
        return check[:-1]

    def SetValue(self, v=''):
        lChecked=v.split('|')
        for e in range(self.GetCount()):
            if self.GetPyData(e) in lChecked:
                self.Check(e, check=True)

# ------------------------------------------------------------------------------

class CheckListBox4Sync(CheckListBox):
    externalCheck=None

    def __init__(self, *args, **kwargs):

        CheckListBox.__init__(self, *args, **kwargs)
        self.externalCheck=[]

    def GetValue(self):
        check=''
        lChecked=self.GetSelections()
        for e in lChecked:
            check='%s%s|' % (check, self.GetPyData(e))
        for e in self.externalCheck:
            check='%s%s|' % (check, e)
        return check[:-1]

    def SetValue(self, v=''):
        lChecked=v.split('|')
        for n in lChecked:
            if not self.IsPresent(n):
                self.AddNotPresent(n)
        for e in range(self.GetCount()):
            if self.GetPyData(e) in lChecked:
                self.Check(e, check=True)

    def IsPresent(self, tableName):
        isPresent=False
        for e in range(self.GetCount()):
            if self.GetPyData(e) == tableName:
                isPresent=True
                break
        return isPresent

    def AddNotPresent(self, tableName):
        self.externalCheck.append(tableName)


class CheckListFromText(CheckListBox):
    externalCheck=None
    def __init__(self, *args, **kwargs):
        CheckListBox.__init__(self, *args, **kwargs)
        self.externalCheck=[]

    def GetValue(self):
        check='|'
        lChecked=self.GetSelections()
        for e in lChecked:
            check='%s%s|' % (check, self.GetPyData(e))
        return check

    def SetValue(self, v=''):
        lChecked=v.split('|')
        for n in lChecked:
            if not self.IsPresent(n):
                self.AddNotPresent(n)
        for e in range(self.GetCount()):
            self.Check(e, self.GetPyData(e) in lChecked)

    def IsPresent(self, tag):
        isPresent=False
        for e in range(self.GetCount()):
            if self.GetPyData(e) == tag:
                isPresent=True
                break
        return isPresent

    def AddNotPresent(self, tag):
        self.externalCheck.append(tag)



# ------------------------------------------------------------------------------


class UnoZeroCheckBox(CheckBox):

    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=[1,0])


# ------------------------------------------------------------------------------


class UnoZeroStringCheckBox(CheckBox):

    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=['1','0'])
