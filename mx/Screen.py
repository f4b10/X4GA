#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         mx/Screen.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
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
import sys
import wx
def TakeScreenShot(panel):
    """ Takes a screenshot of the screen at give pos & size (rect). """
    x,y = panel.GetScreenPosition()
    x=x-5
    y=y-15
    rect = panel.GetRect()
    # see http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3575899
    # created by Andrea Gavana

    # adjust widths for Linux (figured out by John Torres 
    # http://article.gmane.org/gmane.comp.python.wxpython/67327)
    if sys.platform == 'linux2':
        client_x, client_y = self.ClientToScreen((0, 0))
        border_width = client_x - rect.x
        title_bar_height = client_y - rect.y
        rect.width += (border_width * 2)
        rect.height += title_bar_height + border_width

    #Create a DC for the whole screen area
    dcScreen = wx.ScreenDC()

    #Create a Bitmap that will hold the screenshot image later on
    #Note that the Bitmap must have a size big enough to hold the screenshot
    #-1 means using the current default colour depth
    bmp = wx.EmptyBitmap(rect.width, rect.height)

    #Create a memory DC that will be used for actually taking the screenshot
    memDC = wx.MemoryDC()

    #Tell the memory DC to use our Bitmap
    #all drawing action on the memory DC will go to the Bitmap now
    memDC.SelectObject(bmp)

    #Blit (in this case copy) the actual screen on the memory DC
    #and thus the Bitmap
    memDC.Blit( 0, #Copy to this X coordinate
                0, #Copy to this Y coordinate
                rect.width, #Copy this width
                rect.height, #Copy this height
                dcScreen, #From where do we copy?
                rect.x+x, #What's the X offset in the original DC?
                rect.y+y  #What's the Y offset in the original DC?
                )

    #Select the Bitmap out of the memory DC by selecting a new
    #uninitialized Bitmap
    memDC.SelectObject(wx.NullBitmap)

    img = bmp.ConvertToImage()
    return img   
