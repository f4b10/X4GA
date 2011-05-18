#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/layout/imgfac.py
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

"""
Images Factory
"""

import wx

ICONS_TYPE = 'Vista' #icone di default
def SetIconsType(it):
    global ICONS_TYPE
    if it in 'Spheric Vista Pastel'.split():
        ICONS_TYPE = it
def GetIconsType():
    return ICONS_TYPE


class _ImagesFactory(object):
    
    prefix = None
    images_module = None
    
    def _get_bitmap(self, name):
        name = 'get%s_%s_%sBitmap' % (self.prefix, GetIconsType(), name)
        if hasattr(self.images_module, name):
            bmp = getattr(self.images_module, name)()
        else:
            bmp = wx.NullBitmap
        return bmp
    
    def _get_resized_bitmap(self, bmp, size):
        img = bmp.ConvertToImage()
        img.Rescale(size, size)#, wx.IMAGE_QUALITY_HIGH)
        return wx.BitmapFromImage(img)


# ------------------------------------------------------------------------------


import awc.layout.images as images

class WebBrowserImagesFactory(_ImagesFactory):
    
    prefix = 'Web'
    images_module = images
    
    def getWebPreviousBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('Previous'), size)
    
    def getWebNextBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('Next'), size)
    
    def getWebHomeBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('Home'), size)
    
    def getWebWorldBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('World'), size)
