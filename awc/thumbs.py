#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/thumbs.py
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

import os
import wx
import PIL
from PIL import Image
import cStringIO

def opj(x,y):
    return os.path.join(x,y).replace('\\','/')


THUMB_SIZE = 100
THUMB_SPACE = 10
THUMB_LABEL_HEIGHT = 20

IMAGE_EXTENSIONS = 'bmp hpg jpg jpeg tif png gif'.split()


class ResizingImagePanel(wx.Panel):

    """
    A panel which displays an image whose location is given at runtime.
    Resizing events fit that image as appropriate to the size of the panel
    by rescaling it via L{wx.Image.Rescale}.
    """

    def __init__(self, *args, **kwargs):
        """All parameters are passed to the panel initialization function."""
        wx.Panel.__init__(self, *args, **kwargs)
        self._create_sizers()
        self._initialize_panels()

    def _create_sizers(self):
        """Creates persistent sizers for the panel."""
        self.sizer = wx.GridSizer()
        self.SetSizer(self.sizer)

    def _initialize_panels(self):
        """
        Initializes persistent child widgets of the panel and adds them to
        sizers as appropriate. Binds L{wx.EVT_SIZE} to the image rescaling
        method.
        """
        self.static_bitmap = wx.StaticBitmap(self)
        self.sizer.Add(self.static_bitmap, 0, wx.ALIGN_CENTER)
        self.image_loc = None
        self.Bind(wx.EVT_SIZE, self._rescale_image)

    def display_image(self, image_loc):
        """
        Initializes panel so that it begins to display the image at the given
        location.

        @param image_loc: The location passed to the L{wx.Image} initialization
            function.
        """
        self.image_loc = image_loc
        if not self._rescale_image():
            self.undisplay_image()

    def _rescale_image(self, event=None):
        """
        Updates the displayed L{StaticBitmap} to display a proportionately
        sized image, as given by the internal image location. Is to be called
        on resize events to display the most appropriately sized bitmap for the
        panel as display area changes.

        @param event: An unused parameter that may be passed in when binding
            this function to occur on events, such as L{wx.EVT_SIZE}.
        """
        scaled = False
        client_size = self.GetClientSizeTuple()
        if self.image_loc:
            image = wx.Image(self.image_loc)
            image_size = image.GetSize()
            proportions = (float(client_size[i]) / image_size[i]
                           for i in range(len(image_size)))
            proportion = min(proportions) # Use the smallest proportion.
            # Can't use wx.Image.Shrink because it doesn't provide enough pixel
            # granularity -- the shrinking has serious discontinuities.
            new_size = (pixels * proportion for pixels in image_size)
            image.Rescale(*new_size)
            bitmap = wx.BitmapFromImage(image)
            image.Destroy()
            scaled = True
        else:
            bitmap = wx.EmptyBitmap(*client_size)
        self.static_bitmap.SetBitmap(bitmap)
        self.Layout()
        self.Refresh()
        return scaled
    
    def get_image_size(self):
        dimx = dimy = 0
        if self.image_loc:
            image = wx.Image(self.image_loc)
            dimx, dimy = image.GetSize()
        return dimx, dimy
    
    def undisplay_image(self):
        """
        Dissociates an image location from a L{ResizingImagePanel}. Removes the
        currently displayed image from the panel.
        """
        self.image_loc = None
        self._rescale_image()


# ------------------------------------------------------------------------------


class ThumbsPanel(wx.Panel):
    
    thumb_size = THUMB_SIZE
    
    def __init__(self, parent, *args, **kwargs):
        
        if 'thumb_size' in kwargs:
            thumb_size = kwargs.pop('thumb_size')
            if thumb_size is not None:
                self.thumb_size = thumb_size
        
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.images = {}
        self.selected_icon = None
        
        hs = wx.FlexGridSizer(1, 0, 0, 0)
        hs.AddGrowableCol(1)
        hs.AddGrowableRow(0)
        
        ts = self.thumb_size
        
        thumbslist = wx.ScrolledWindow(self, size=(ts+2*THUMB_SPACE+20,100), 
                                       style=wx.SUNKEN_BORDER)
        hs.Add(thumbslist, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.thumbslist = thumbslist
        
        preview = ResizingImagePanel(self, -1, wx.DefaultPosition, 
                                     [400,400], wx.SUNKEN_BORDER)
        hs.Add(preview, 0, 
               wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP|wx.BOTTOM, 5)
        preview.static_bitmap.SetName('preview_bitmap')
        preview.static_bitmap.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        preview.static_bitmap.Bind(wx.EVT_LEFT_UP, self.OnImageOpen)
        self.preview = preview
        
        self.SetSizer(hs)
        hs.SetSizeHints(self)
        
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
    
    def OnMouseLeftUp(self, event):
        if self.selected_icon:
            self.ImagePreview(self.selected_icon)
        event.Skip()
    
    def OnImageOpen(self, event):
        if self.selected_icon:
            filename = self.images[self.selected_icon]
            os.startfile(filename.replace('/','\\'))
        event.Skip()
    
    def PopulateFromPath(self, path, func=None):
        files = [opj(path, f) for f in os.listdir(path)]
        return self._PopulateFromFiles(files, func)
    
    def PopulateFromFilesList(self, files, func=None):
        return self._PopulateFromFiles(files, func)
    
    def _PopulateFromFiles(self, files, func):
        
        self.selected_icon = None
        files = [f for f in files 
                 if '.' in f and f.split('.')[-1].lower() in IMAGE_EXTENSIONS]
        row = 0
        ts = self.thumb_size
        client_size = [ts, ts]
        
        for imageFile in files:
            if not os.path.exists(imageFile):
                continue
            image = wx.Image(imageFile)
            image_size = image.GetSize()
            proportions = (float(client_size[i]) / image_size[i]
                           for i in range(len(image_size)))
            proportion = min(proportions) # Use the smallest proportion.
            # Can't use wx.Image.Shrink because it doesn't provide enough pixel
            # granularity -- the shrinking has serious discontinuities.
            new_size = (pixels * proportion for pixels in image_size)
            image.Rescale(*new_size)
            bmp = wx.BitmapFromImage(image)
            image.Destroy()
            pos = [0,0]
            pos[0] = THUMB_SPACE
            pos[1] = THUMB_SPACE+(ts+THUMB_SPACE+THUMB_LABEL_HEIGHT)*row
            size = [ts, ts]
            b = wx.StaticBitmap(self.thumbslist, -1, bmp, pos, size,
                                style=wx.RAISED_BORDER)
            b.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            self.images[b] = imageFile
            b.Bind(wx.EVT_LEFT_UP, self.OnBitmapClicked)
            if self.selected_icon is None:
                self.selected_icon = b
            pos[1] += ts
            size = [ts, THUMB_LABEL_HEIGHT]
            title = imageFile.replace('\\','/').split('/')[-1]
            t = wx.StaticText(self.thumbslist, -1, title, pos, size,
                              style=wx.RAISED_BORDER)
            row += 1
            if callable(func):
                func(row)
        
        self.thumbslist.SetScrollbars(0, ts+THUMB_SPACE+THUMB_LABEL_HEIGHT, 
                                      0, row)
        
        if self.selected_icon:
            self.ImagePreview(self.selected_icon)
    
    def OnBitmapClicked(self, event):
        bmp = event.GetEventObject()
        if bmp in self.images:
            self.selected_icon = bmp
            self.ImagePreview(bmp)
        event.Skip()
    
    def ImagePreview(self, bmp_icon):
        filename = self.images[bmp_icon]
        self.preview.display_image(filename)


# ------------------------------------------------------------------------------


class _mixin(object):
    
    def __init__(self, thumb_size=None):
        
        self.thumbs_panel = ThumbsPanel(self, thumb_size=thumb_size)
        sizer = wx.FlexGridSizer(0, 1, 0, 0)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        sizer.Add(self.thumbs_panel, 0, 
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
    
    def PopulateFromPath(self, *args, **kwargs):
        return self.thumbs_panel.PopulateFromPath(*args, **kwargs)
    
    def PopulateFromFilesList(self, *args, **kwargs):
        return self.thumbs_panel.PopulateFromFilesList(*args, **kwargs)
    
# ------------------------------------------------------------------------------


class ThumbsFrame(wx.Frame, _mixin):
    
    def __init__(self, *args, **kwargs):
        if 'thumb_size' in kwargs:
            thumb_size = kwargs.pop('thumb_size')
        else:
            thumb_size = THUMB_SIZE
        kwargs['title'] = 'Immagini'
        kwargs['size'] = (600,400)
        wx.Frame.__init__(self, *args, **kwargs)
        _mixin.__init__(self, thumb_size)


# ------------------------------------------------------------------------------


class ThumbsDialog(wx.Dialog, _mixin):
    
    def __init__(self, *args, **kwargs):
        if 'thumb_size' in kwargs:
            thumb_size = kwargs.pop('thumb_size')
        else:
            thumb_size = THUMB_SIZE
        kwargs['title'] = 'Immagini'
        kwargs['size'] = (600,400)
        wx.Dialog.__init__(self, *args, **kwargs)
        _mixin.__init__(self, thumb_size)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    
    class ThumbsApp(wx.PySimpleApp):
        def OnInit(self):
            f = ThumbsFrame(None)
            f.PopulateFromPath('D:\\p900 stuff\\240706')
            f.SetSize((600,400))
            f.Show()
            return True

    app = ThumbsApp()
    app.MainLoop()
