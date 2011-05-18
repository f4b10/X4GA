#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/button.py
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
from wx.lib.buttons import * 
import wx.lib.colourdb 
import awc.controls.mixin as cmix


class _WinFlatMixin(cmix.ControlsMixin):
    """ 
    Emulates a win32 flat button 
    Default-state:border=0 
    hover:border=1 
    down:do not change colour 
    """ 
    def __init__(self):
        cmix.ControlsMixin.__init__(self)
        self.useFocusInd = False
        self.bezelWidth = 0
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_SET_FOCUS,  self.OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)
    
    def OnMouseEnter(self,event):         
        self.bezelWidth = 1
        self.Refresh()
    
    def OnMouseLeave(self,event): 
        self.bezelWidth = 0
        self.Refresh()
    
    #def OnPaint(self, event): 
        #""" 
        #copy&paste from GenButton with 1 minor change(colour on down) 
        #""" 
        #(width, height) = self.GetClientSizeTuple()
        #x1 = y1 = 0
        #x2 = width-1
        #y2 = height-1
        
        #dc = wx.BufferedPaintDC(self)
        #brush = None
        
        #if True: #was:if self.up
            #colBg = self.GetBackgroundColour()
            #brush = wx.Brush(colBg, wx.SOLID)
            #if self.style & wx.BORDER_NONE:
                #myAttr = self.GetDefaultAttributes()
                #parAttr = self.GetParent().GetDefaultAttributes()
                #myDef = colBg == myAttr.colBg
                #parDef = self.GetParent().GetBackgroundColour() == parAttr.colBg
                #if myDef and parDef:
                    #if wx.Platform == "__WXMAC__":
                        #brush.MacSetTheme(1) # 1 == kThemeBrushDialogBackgroundActive
                    #elif wx.Platform == "__WXMSW__":
                        #if self.DoEraseBackground(dc):
                            #brush = None
                #elif myDef and not parDef:
                    #colBg = self.GetParent().GetBackgroundColour()
                    #brush = wx.Brush(colBg, wx.SOLID)
        #else:
            #brush = wx.Brush(self.faceDnClr, wx.SOLID)
        #if brush is not None:
            #dc.SetBackground(brush)
            #dc.Clear()
        
        #self.DrawBezel(dc, x1, y1, x2, y2)
        #if True:#self.bmpLabel:
            #self.DrawLabel(dc, width, height)
        #if self.hasFocus and self.useFocusInd:
            #self.DrawFocusIndicator(dc, width, height)
    
    def OnFocusGained(self, event):
        self.AdjustBackgroundColor(self.IsEditable() and self.IsEnabled())
        event.Skip()
    
    def OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()
    
    def IsEditable(self):
        return True


# ------------------------------------------------------------------------------


class FlatButton(_WinFlatMixin,GenButton):
    def __init__(self, *arg, **kwargs):
        GenButton.__init__(self, *arg, **kwargs)
        _WinFlatMixin.__init__(self)
        #self.bmpLabel = None
        #if 'size' in kwargs:
            #self.SetSize(kwargs['size'])
 

# ------------------------------------------------------------------------------


class FlatBitmapButton(_WinFlatMixin,GenBitmapButton):
    def __init__(self, *arg, **kwargs):
        GenBitmapButton.__init__(self, *arg, **kwargs)
        _WinFlatMixin.__init__(self)
        if 'size' in kwargs:
            self.SetSize(kwargs['size'])
 
 
# ------------------------------------------------------------------------------


class FlatBitmapTextButton(_WinFlatMixin,GenBitmapTextButton):
    def __init__(self, *arg, **kwargs):
        GenBitmapTextButton.__init__(self, *arg, **kwargs)
        _WinFlatMixin.__init__(self)


# ------------------------------------------------------------------------------


class Button(wx.Button, cmix.HelpedControl):
    
    def __init__(self, *arg, **kwargs):
        wx.Button.__init__(self, *arg, **kwargs)
        cmix.HelpedControl.__init__(self)


# ------------------------------------------------------------------------------


class BitmapButton(wx.BitmapButton, cmix.HelpedControl):
    
    def __init__(self, *arg, **kwargs):
        wx.Button.__init__(self, *arg, **kwargs)
        cmix.HelpedControl.__init__(self)


# ------------------------------------------------------------------------------


if wx.Platform == '__WXGTK__':
    TippedButton = Button
    
else:
    class TippedButton(Button):
        """
        A normal wxButton on wich tooltips appears even if it is disabled ;)
        This is done by making a transparent panel as its parent, and setting
        tooltip on both the panel and the button.
        """
        def __init__(self, parent, *args, **kwargs):
            p = wx.Panel(parent, -1, style=wx.NO_BORDER)
            Button.__init__(self, p, *args, **kwargs)
            self._moving = False
            self._SetPosition()
            self._SetSize()
            self.Bind(wx.EVT_MOVE, self.OnMove)
            self.Bind(wx.EVT_SIZE, self.OnSize)
        
        def OnMove(self, event):
            if not self._moving:
                self._moving = True
                self._SetPosition()
                self._moving = False
                event.Skip()
        
        def OnSize(self, event):
            self._SetSize()
            event.Skip()
        
        def _SetPosition(self):
            self.GetParent().SetPosition(self.GetPosition())
            self.SetPosition((0,0))
        
        def _SetSize(self):
            self.GetParent().SetSize(self.GetSize())
        
        def SetToolTipString(self, tip):
            Button.SetToolTipString(self, tip)
            self.GetParent().SetToolTipString(tip)


FlatButton = Button
FlatBitmapButton = wx.BitmapButton
FlatBitmapTextButton = wx.BitmapButton
