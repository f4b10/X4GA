#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/mixin.py
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
import awc.util as awu

class HelpedControl(object):
    
    def __init__(self):
        object.__init__(self)
        try:
            self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown_TestHelp)
        except Exception, e:
            pass
    
    def OnKeyDown_TestHelp(self, event):
        if event.GetKeyCode() == wx.WXK_F1:
            f = awu.GetParentFrame(self)
            if event.ControlDown():
                #CtrlF1 Attiva/Disattiva identificazione Window
                if hasattr(f, 'HelpBuilder_Switch'):
                    try:
                        f.HelpBuilder_Switch()
                    except:
                        pass
            else:#if event.AltDown():
                a = wx.GetApp()
                if hasattr(f, 'HelpBuilder_ShowObjectHelp'):
                    f.HelpBuilder_ShowObjectHelp(self)
                elif not hasattr(a, 'HelpBuilder_ShowObjectHelp'):
                    awu.MsgDialog(self, "L'Applicazione non supporta il sistema di Help.")
                else:
                    a.HelpBuilder_ShowObjectHelp(self)
        event.Skip()
    
        
class ControlsMixin(HelpedControl):
    enabled = True
    refresh = True
    
    def __init__(self, *args, **kwargs):
        HelpedControl.__init__(self)
        self.notifyChanges = True
        self.readonly = False
        cf = lambda x: wx.TheColourDatabase.Find(x)
        self._colors = {'focusedBackground':  cf('lemonchiffon1'), 
                        'normalBackground':   wx.NullColour,
                        'disabledBackground': wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE),#cf('lightgrey'),
                        'disabledForeground': cf('black'),
                        'invalidBackground':  cf('orange'),
                        'normalForeground':   cf('black'),
                        'invalidForeground':  cf('black')}
        self.colors = self._colors.copy()
    
    def SetDynColor(self, key, color=None):
        assert key in self.colors
        if color is None:
            color = self._colors[key]
        self.colors[key] = color
    
    def NotifyChanges(self, new):
        current = self.notifyChanges
        self.notifyChanges = new
        return current
    
    def SetValueSilent(self, value):
        nc = self.NotifyChanges(False)
        self.SetValue(value)
        self.NotifyChanges(nc)
    
    def SetReadOnly(self, ro=True):
        self.readonly = ro
        if wx.Platform == '__WXGTK__' and hasattr(self, 'SetEditable'):
            self.SetEditable(not ro)
        else:
            self.Enable(not ro)
    
    def AdjustBackgroundColor(self, focused=False, obj=None, func=None, 
                              error=False, refresh_func=None):
        """
        Setta il colore di sfondo in base al tipo passato:
        False x colore editazione disabilitata
        True  x colore editazione abilitata
        """
        if obj is None:
            obj = self
        if error:
            color = self.colors['invalidBackground']
            self.SetBackgroundColour(color)
        elif self.IsEnabled():
            if focused:
                color = self.colors['focusedBackground']
            else:
                color = self.colors['normalBackground']
        else:
            color = self.colors['disabledBackground']
        obj.SetBackgroundColour(color)
        if func is not None:
            func(color)
        if self.refresh:
            self.refresh = False
            if refresh_func is None:
                obj.Refresh()
            else:
                refresh_func()
            def Reset():
                self.refresh = True
            wx.CallAfter(Reset)
    
    def Disable(self):
        self.Enable(False)
    
    def Enable(self, e=True, set_editable=True):
        if set_editable:
            self.SetEditable(e, set_enable=False)
        self.AdjustBackgroundColor()
    
    def IsEnabled(self):
        return not self.readonly and self.IsEditable()


# ------------------------------------------------------------------------------


class TextCtrlMixin(ControlsMixin):
    
    def PaintDisabled(self, text, obj=None):
        
        if wx.Platform == '__WXGTK__':
            return
        
        if obj is None:
            obj = self
        
        dc = wx.PaintDC(obj)
        dc.SetFont(self.GetFont())
        dc.Clear()
        textwidth, textheight = dc.GetTextExtent(text)
        dcwidth, dcheight = self.GetClientSizeTuple()
        y = (dcheight - textheight) / 2
        x = 2#dcwidth - textwidth - 2
        
        c = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        b = wx.Brush(c, wx.SOLID)
        dc.SetBrush(b)
        dc.SetPen(wx.Pen(c, 0, wx.TRANSPARENT))
        dc.DrawRectangle(0,0, dcwidth, dcheight)
        c = self.colors['disabledForeground']
        dc.SetPen(wx.Pen(c, 0, wx.SOLID))
        dc.SetClippingRegion(0, 0, dcwidth, dcheight)
        dc.DrawText(text, x, y)
    
    #def RePaint(self):
        #self.Refresh()#UpdateWindowUI(wx.UPDATE_UI_PROCESS_ALL|wx.UPDATE_UI_RECURSE)
    
    #def Enable(self, e=True):
        #wx.TextCtrl.Enable(self, e)
        #wx.CallAfter(self.RePaint)
    
    #def Disable(self, e=True):
        #wx.TextCtrl.Disable()
        #wx.CallAfter(self.RePaint)
    

# ------------------------------------------------------------------------------


class ContainersMixin(object):
    def ReSize(self):
        #problema sui containers (panel, notebook, ecc):
        #quando aggiungo dei pannelli successivamente alla creazione del 
        #container, il sizer non lavora correttamente: l'elemento aggiunto non
        #viene ridimensionato nel modo opportuno - cambiando la dimensione del
        #container invece l'elemento viene ridimensionato come si deve.
        #Quindi faccio finta di ridimensionare il container in modo che avvenga
        #il dimensionamento iniziale dell'elemento aggiunto.
        s = self.GetSize()
        self.SetSize((s[0],s[1]-1))
        self.SetSize(s)
