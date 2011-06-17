#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/textctrl.py
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
import awc.controls.windows as aw


class TextCtrl(wx.TextCtrl, cmix.TextCtrlMixin):
    changing = False
    lowercaseok = False
    
    def __init__(self, parent, id=-1, value='', pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0, validator=wx.DefaultValidator,
                 name=wx.TextCtrlNameStr):
        wx.TextCtrl.__init__(self, parent, id=id, value=value, pos=pos, 
                             size=size, style=style, validator=validator, 
                             name=name)
        self.mypaint = True
        if style is not None:
            if style & wx.TE_PASSWORD:
                self.mypaint = False
        cmix.TextCtrlMixin.__init__(self)
        self.Bind(wx.EVT_SET_FOCUS,  self._OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self._OnFocusLost)
        self.Bind(wx.EVT_KEY_DOWN, self._OnKeyDown)
        self.Bind(wx.EVT_CHAR, self._OnChar)
        self.Bind(wx.EVT_TEXT, self._OnText)
        if wx.Platform == '__WXMSW__':
            self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnPaint(self, event):
        if self.IsEnabled() or not self.mypaint: 
            wx.TextCtrl.OnPaint(self, event)
        else:
            self.PaintDisabled(self.GetValue())
        event.Skip()
    
    def ForceUpperCase(self, fuc=True):
        self.lowercaseok = not fuc
    
#    def Enable(self, e=True):
#        e = e and not self.readonly and self.IsEditable()
#        wx.TextCtrl.Enable(self, e)
#        wx.TextCtrl.Refresh(self)
    
    def Disable(self, *args, **kwargs):
        return cmix.TextCtrlMixin.Disable(self, *args, **kwargs)
    
    def Enable(self, *args, **kwargs):
        return cmix.TextCtrlMixin.Enable(self, *args, **kwargs)
    
    def IsEnabled(self, *args, **kwargs):
        return cmix.TextCtrlMixin.IsEnabled(self, *args, **kwargs)
    
    def SetEditable(self, e=True, set_enable=True):
        wx.TextCtrl.SetEditable(self, e)
        if set_enable:
            self.Enable(e, set_editable=False)
    
    def SetValue(self, value):
        if value is None:
            value = ""
        if not self.lowercaseok and hasattr(value, 'upper'):
            value = value.upper()
        wx.TextCtrl.SetValue(self, value)
    
    
    def _OnKeyDown(self, event):
        event.Skip()
    
    def _OnChar(self, event):
        if not self.IsEnabled() and not self.IsEditable() and\
                event.GetKeyCode() == wx.WXK_TAB and \
                not event.ControlDown() and wx.Platform == '__WXGTK__':
            #il tab su gtk a volte non esce dal controllo se disabilitato
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                self.Navigate(wx.NavigationKeyEvent.IsForward)
        else:
            event.Skip()
    
    def _OnText(self, event):
        changed = False
        if not self.changing and not self.lowercaseok:
            self.changing = True
            ip = self.GetInsertionPoint()
            oldval = self.GetValue()
            self.SetValue(oldval.upper())
            self.SetInsertionPoint(ip)
            changed = oldval != self.GetValue()
            def StopChanging():
                self.changing = False
            wx.CallAfter(StopChanging)
        event.Skip()
        return changed
    
    def _OnFocusGained(self, event):
        self.AdjustBackgroundColor(self.IsEditable())
        v = self.GetValue()
        if v is not None:
            self.SetSelection(0,len(v))
        aw.SetFocusedControl(self)
        self.Refresh()
        event.Skip()
    
    def _OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()


# ------------------------------------------------------------------------------


class TextCtrl_LC(TextCtrl):
    lowercaseok = True


# ------------------------------------------------------------------------------


class FixedLenghtTextCtrl(TextCtrl):
    
    _fixlen = 10
    
    def SetFixLen(self, l):
        self._fixlen = l
        self.SetMaxLength(self._fixlen)

# ------------------------------------------------------------------------------


class ZeroFilledTextCtrl(FixedLenghtTextCtrl):
    
    def _OnFocusLost(self, event):
        assert self._fixlen is not None
        TextCtrl._OnFocusLost(self, event)
        v = self.GetValue()
        if v:
            v2 = str(v).zfill(self._fixlen)
            if v2 != v:
                self.SetValue(v2)


# ------------------------------------------------------------------------------


class NotEditableTextCtrl(TextCtrl):
    
    def __init__(self, *args, **kwargs):
        TextCtrl.__init__(self, *args, **kwargs)
        self.SetEditable(False)
