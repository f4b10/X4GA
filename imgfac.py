#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         imgfac.py
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
import images

from awc.layout.imgfac import SetIconsType, GetIconsType, _ImagesFactory
_SetIconsType = SetIconsType
def SetIconsType(*args):
    return _SetIconsType(*args)


class ToolbarImagesFactory(_ImagesFactory):
    
    prefix = 'TB'
    images_module = images
    
    def getEmiDocBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('EmiDoc'), size)
    
    def getIntArtBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('IntArt'), size)
    
    def getIncPagBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('IncPag'), size)
    
    def getIntCliBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('IntCli'), size)
    
    def getIntForBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('IntFor'), size)
    
    def getScadCFBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('ScadCF'), size)
    
    def getIntPdcBitMap(self, size=48):
        return self._get_resized_bitmap(self._get_bitmap('IntPdc'), size)
    
