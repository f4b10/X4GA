#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/wxinit.py
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
import os
import subprocess


FONT_SIZE = 8
FONT_FAMILY = wx.SWISS
FONT_WEIGHT = wx.NORMAL
FONT_FLAGS = wx.NORMAL

GRID_ROW_HEIGHT = 24


def GetCodiceStandardWidth():
    isapp = (wx.GetApp() is not None)
    if not isapp:
        dummy_app = wx.PySimpleApp()
    f = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    if not isapp:
        dummy_app.Destroy()
#    w = int(f.GetPixelSize()[0]*2)
    w = int(f.GetPointSize()*4)
    if wx.Platform == '__WXGTK__':
        w += 8
    return w


# ------------------------------------------------------------------------------


def GetGridRowHeight():
    f = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    return int(f.GetPointSize()*2+2)


def TestInitialFrameSize(frame):
    if False:#wx.Platform == '__WXGTK__':
        size = frame.GetSize()
        frame.SetSize((1024, size[1]))


# ------------------------------------------------------------------------------


if wx.Platform == '__WXGTK__':
    
    def startfile(*args):
        subprocess.Popen(['xdg-open']+list(args))
    os.startfile = startfile
    
    
    def ApplyStandardFont(obj):
        f = wx.Font(FONT_SIZE, FONT_FAMILY, FONT_WEIGHT, FONT_FLAGS)
#        try:
#            obj.SetFont(f)
#        except Exception, e:
#            pass
    
#    #workaround classe Choice su GTK: pare che se, alla crezione,
#    #il numero di voci è inferiore a 2, il cambio Font fallisce
#    #miseramente.
#    GTK_Choice_Init_Original = wx.Choice.__init__
#    def GTK_Choice_Init(self, parent, id, pos=wx.DefaultPosition, size=wx.DefaultSize,
#                        choices=None, *args, **kwargs):
#        true_choices = choices
#        if len(choices or [])<2:
#            choices = ['dummy1', 'dummy2']
#        GTK_Choice_Init_Original(self, parent, id, pos, size, choices, *args, **kwargs)
#        if choices != true_choices:
#            self.Clear()
#            for choice in true_choices:
#                self.Append(choice)
#    wx.Choice.__init__ = GTK_Choice_Init
    
    GTK_Panel_Init_Original = wx.Panel.__init__
    def GTK_Panel_Init(self, *args, **kwargs):
        GTK_Panel_Init_Original(self, *args, **kwargs)
        ApplyStandardFont(self)
    wx.Panel.__init__ = GTK_Panel_Init
    
    #hacking classi per attribuzione font di default
    classes = []
    for name in dir(wx):
        o = getattr(wx, name)
        if hasattr(o, 'SetFont'):
            classes.append(o)
    for cls in classes:
        std_init = getattr(cls, '__init__')
        def GetInitFunc():
            init = std_init
            def InitFactory(self, *args, **kwargs):
                init(self, *args, **kwargs)
                ApplyStandardFont(self)
            return InitFactory
        setattr(cls, '__init__', GetInitFunc())


    #la ridefinizione di Bind serve, su gtk, a sopperire alla impossibilità
    #di associare un acceleratore di tastiera ad un bottone
    _Button_Bind_Original_ = wx.Button.Bind
    def _Button_Bind(self, _EVT_TYPE, _func, *args, **kwargs):
        _Button_Bind_Original_(self, _EVT_TYPE, _func, *args, **kwargs)
        self._button_accelerator_func = _func
    wx.Button.Bind = _Button_Bind
