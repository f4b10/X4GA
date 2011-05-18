#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/numctrl.py
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
import wx.lib.masked as masked
import wx.calendar
from datetime import date

import awc.controls.mixin as cmix
import awc.controls.windows as aw


class NumCtrl(masked.numctrl.NumCtrl, cmix.TextCtrlMixin):
    """
    Wrapper per wx.lib.masked.numctrl.NumCtrl
    SetValue(None) => SetValue(0)
    """
    def __init__ (
                self, parent, id=-1, value = 0,
                pos = wx.DefaultPosition, size = wx.DefaultSize,
                style = wx.TE_PROCESS_TAB, validator = wx.DefaultValidator,
                name = "masked.num",
                **kwargs ):
        
        kwargs["groupChar"] = "."
        kwargs["decimalChar"] = ","
        kwargs["invalidBackgroundColour"] = "red"
        
        self.hasfocus = False
        self.is_too_big = False
        
        cmix.TextCtrlMixin.__init__(self)
        masked.numctrl.NumCtrl.__init__(self, parent, id, value, pos, size,\
                                        style, validator, name, **kwargs)
        
        #toglo il tasto invio dagli handlers di tastiera, che porterebbe
        #alla navigazione in avanti invece che bottone default
        del self._keyhandlers[13]
        
        self.Bind(wx.EVT_SET_FOCUS,  self._OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self._OnFocusLost)
        if wx.Platform == '__WXMSW__':
            self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnPaint(self, event):
        if self.IsEnabled():
            wx.TextCtrl.OnPaint(self, event)
        else:
            self.PaintDisabled(self._curValue)
        event.Skip()
    
#    def Enable(self, e=True):
#        e = e and not self.readonly and self.IsEditable()
#        masked.numctrl.NumCtrl.Enable(self, e)
#        masked.numctrl.NumCtrl.Refresh(self)
    
#    def Disable(self):
#        self.Enable(False)
#    
#    def Enable(self, e=True, set_editable=True):
#        if e:
#            c = wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER)
#        else:
#            c = wx.NullColour
#        if set_editable:
#            self.SetEditable(e, set_enable=False)
#        self.SetBackgroundColour(c)
#    
#    def IsEnabled(self):
#        return not self.readonly
#    
    def Disable(self, *args, **kwargs):
        return cmix.TextCtrlMixin.Disable(self, *args, **kwargs)
    
    def Enable(self, *args, **kwargs):
        return cmix.TextCtrlMixin.Enable(self, *args, **kwargs)
    
    def IsEnabled(self, *args, **kwargs):
        return cmix.TextCtrlMixin.IsEnabled(self, *args, **kwargs)
    
    def SetEditable(self, e=True, set_enable=True):
        masked.numctrl.NumCtrl.SetEditable(self, e)
        if set_enable:
            self.Enable(e, set_editable=False)
    
    def SetValue( self, n ):
        if n is None:
            n = 0
        try:
            out = masked.numctrl.NumCtrl.SetValue(self, n)
            self.is_too_big = False
        except ValueError, e:
            aw.awu.MsgDialog(self.GetParent(), "Il valore è troppo grande per essere editato: sono permesse al massimo %d cifre intere.\nIl valore sarà azzerato.\n(%s)" % (self._integerWidth, self.GetName()), "Valore non editabile", style=wx.ICON_ERROR)
            masked.numctrl.NumCtrl.SetValue(self, 0)
            self.is_too_big = True
            out = False
        return out
    
    def IsTooBig(self):
        return self.is_too_big
    
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
            #adeguo il tasto '.' come ','
            if event.GetKeyCode() in (46, 395):
                event.GetKeyCode = lambda *x: 44
#                def FixDecimals():
#                    def FixDecimals():
#                        ss, se = self.GetSelection()
#                        dp = self._decimalpos+1
#                        if ss == dp and se == len(wx.TextCtrl.GetValue(self)):
#                            self.SetSelection(ss, ss)
#                    wx.CallAfter(FixDecimals)
#                wx.CallAfter(FixDecimals)
            #test x bug editazione decimali su gtk: se selezionati, i caratteri
            #numerici digitati non vengono considerati
            if wx.Platform == '__WXGTK__' and hasattr(self, '_decimalpos'):
                ss, se = self.GetSelection()
                dp = self._decimalpos+1
                if ss == dp and se == len(wx.TextCtrl.GetValue(self)):
                    self.SetSelection(ss, ss)
            return masked.numctrl.NumCtrl._OnChar(self, event)
    
    def OnTextChange( self, event ):
        if self.notifyChanges:
            masked.numctrl.NumCtrl.OnTextChange(self, event)
        event.Skip()
    
    def SetBackgroundColour(self, *args, **kwargs):
        masked.numctrl.NumCtrl.SetBackgroundColour(self, *args, **kwargs)
    
    def _applyFormatting(self, *args, **kwargs):
        masked.numctrl.NumCtrl._applyFormatting(self)
        self.AdjustBackgroundColor(self.FindFocus() == self and self.IsEditable())
        self._Refresh()

    def _OnFocusGained(self, event):
        #if self.TestEnableOnFocus(event.GetWindow()):
            #return
        wx.CallAfter(lambda: self.SetSelection(0, len(self._mask)))
        self.hasfocus = True
        self.AdjustBackgroundColor(self.IsEditable())
        aw.SetFocusedControl(self)
        event.Skip()
    
    def _OnFocusLost(self, event):
        self.hasfocus = False
        self.AdjustBackgroundColor(False)
        event.Skip()
    
    #def Enable(self, e=True):
        #cmix.ControlsMixin.Enable(self, e)
        #self.SetEditable(e)
    
    #def Disable(self):
        #self.Enable(False)
    
    #def IsEnabled(self):
        #return cmix.ControlsMixin.IsEnabled(self)
