#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/__init__.py
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

CELLEDIT_BEFORE_UPDATE = 1
CELLEDIT_AFTER_UPDATE =  2

#import wx.lib.newevent
#(DateChangedEvent, EVT_DATECHANGED)   = wx.lib.newevent.NewEvent()

evt_DATECHANGED = wx.NewEventType()
EVT_DATECHANGED = wx.PyEventBinder(evt_DATECHANGED, 1)

evt_DATEFOCUSLOST = wx.NewEventType()
EVT_DATEFOCUSLOST = wx.PyEventBinder(evt_DATEFOCUSLOST, 1)

SEARCH_COLORS1 = 'black darkseagreen1'.split()
SEARCH_COLORS2 = 'black darkseagreen2'.split()
