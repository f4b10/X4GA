#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         xsplash.py
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
import images


class XSplashScreen(wx.SplashScreen):
    
    def GetImage(self):
        return images.getSplashLogoBitmap()
    
    def __init__(self, moduli=None):
        
        self.pbar = None
        self.pcount = None
        
        wx.SplashScreen.__init__(self, self.GetImage(),
                                 wx.SPLASH_CENTRE_ON_SCREEN, 0, None,
                                 style=wx.SIMPLE_BORDER
                                 |wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP)
        
        self.SetBackgroundColour("white")
        sw, sh = self.GetSize()
        mw = sw
        mh = 35
        mx = 0
        my = sh-mh
        msgPan = wx.Panel(self.GetSplashWindow(), -1, 
                          pos=(mx, my), size=(mw, mh))
        msgPan.SetBackgroundColour("white")
        
        bw = sw-20
        bh = 10
        bd = (sw-bw)/2
        
        y = 6
        if moduli is not None:
            self.pbar = wx.Gauge(msgPan, -1, moduli, 
                                 pos=(bd, y), size=(bw, bh))
            self.pbar.SetForegroundColour('gray')
            self.pbar.SetBackgroundColour('white')
            self.pbar.SetValue(1)
            wx.SafeYield(onlyIfNeeded=True)
            self.pcount = 0
            y += bh
        
        self.job = wx.StaticText(msgPan, -1, pos=(bd, y), size=(bw, 20),\
                                 style = wx.ST_NO_AUTORESIZE)
        
        wx.Yield()
    
    def SetJob(self, job):
        self.job.SetLabel(job)
        wx.SafeYield(onlyIfNeeded=True)
    
    def UpdateProgress(self):
        self.pcount += 1
        self.pbar.SetValue(self.pcount)
