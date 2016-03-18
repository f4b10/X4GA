#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/basetab.py
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
import anag.basetab_wdr as wdr
from awc.controls.notebook import Notebook
from awc.controls.checkbox import CheckBox, RCheckBox
from awc.controls.radiobox import RadioBox
from awc.thumbs import ResizingImagePanel


class AnagCardPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.AnagCardFunc(self)


# ------------------------------------------------------------------------------


class PdcRelAnagCardPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.PdcRelAnagCardFunc(self)


# ------------------------------------------------------------------------------


class WorkZoneNotebook(Notebook):

    def __init__(self, *args, **kwargs):
        Notebook.__init__(self, *args, **kwargs)
        self.SetName('workzone')


# ------------------------------------------------------------------------------


class UnoZeroCheckBox(CheckBox):
    
    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values={True: 1, False: 0})


# ------------------------------------------------------------------------------


class RUnoZeroCheckBox(RCheckBox):
    
    def __init__(self, *args, **kwargs):
        RCheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values={True: 1, False: 0})


# ------------------------------------------------------------------------------


class UnoZeroStringCheckBox(CheckBox):
    
    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values={True: '1', False: '0'})


# ------------------------------------------------------------------------------


class SiNoCheckBox(CheckBox):
    
    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values={True: "S", False: "N"})


# ------------------------------------------------------------------------------


class UnoZeroStringRadioBox(RadioBox):
    
    def __init__(self, *args, **kwargs):
        RadioBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=['1', '0'])


# ------------------------------------------------------------------------------


class SiNoRadioBox(RadioBox):
    
    def __init__(self, *args, **kwargs):
        RadioBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=["S", "N"])


# ------------------------------------------------------------------------------


class WebCatUpdateTypeRadioBox(RadioBox):

    def __init__(self, *args, **kwargs):
        RadioBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=["C","S","N"])


# ------------------------------------------------------------------------------


_evtIMAGECHANGED = wx.NewEventType()
EVT_IMAGECHANGED = wx.PyEventBinder(_evtIMAGECHANGED, 1)
class ImageChangedEvent(wx.PyCommandEvent):
    def __init__(self, *args, **kwargs):
        wx.PyCommandEvent.__init__(self, *args, **kwargs)
        self._filename = None
    def SetFileName(self, filename):
        self._filename = filename
    def GetFileName(self):    
        return self._filename


# ------------------------------------------------------------------------------


class FileDropTarget(wx.FileDropTarget):
    
    filename = None
    
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
    
    def OnDropFiles(self, x, y, filenames):
        fn = filenames[0]
        self.parent.display_image(fn)
        if len(filenames)==1:
            self.set_image_filename(fn)
        else:
            self.set_image_filename(filenames)
        self.parent.set_changed()
    
    def set_image_filename(self, fn):
        self.filename = fn
        evt = ImageChangedEvent(_evtIMAGECHANGED)
        evt.SetEventObject(self.parent)
        evt.SetId(self.parent.GetId())
        evt.SetFileName(fn)
        
        self.parent.GetEventHandler().AddPendingEvent(evt)
    
    def get_image_filename(self):
        return self.filename


# ------------------------------------------------------------------------------


class ImagePanel(ResizingImagePanel):
    
    changed = False
    
    def _create_sizers(self):
        pass
    
    def _initialize_panels(self):
        """
        Initializes persistent child widgets of the panel and adds them to
        sizers as appropriate. Binds L{wx.EVT_SIZE} to the image rescaling
        method.
        """
        self.static_bitmap = wx.StaticBitmap(self)
        self.image_loc = None
    
    def set_changed(self, c=True):
        self.changed = c
    
    def is_changed(self):
        return self.changed


# ------------------------------------------------------------------------------


class PhotoContainerPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        dnd = kwargs.pop('dnd', True)
        wx.Panel.__init__(self, *args, **kwargs)
        self.imagepanel = ImagePanel(self, size=self.GetClientSize())
        if dnd:
            self.droptarget = FileDropTarget(self.imagepanel)
            self.SetDropTarget(self.droptarget)
    
    def set_changed(self, *args, **kwargs):
        return self.imagepanel.set_changed(*args, **kwargs)
    
    def is_changed(self, *args, **kwargs):
        return self.imagepanel.is_changed(*args, **kwargs)
    
    def get_image_filename(self):
        return self.droptarget.get_image_filename()
    
    def display_image(self, fn):
        self.imagepanel.display_image(fn)
    
    def get_image_size(self):
        return self.imagepanel.get_image_size()
    
    def undisplay_image(self):
        self.imagepanel.undisplay_image()
