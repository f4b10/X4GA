#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/focus.py
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

from awc.controls.textctrl  import TextCtrl
from awc.controls.numctrl   import NumCtrl
from awc.controls.datectrl  import DateCtrl
from awc.controls.checkbox  import CheckBox
from awc.controls.radiobox  import RadioBox
from awc.controls.choice    import Choice
from awc.controls.linktable import LinkTable
from awc.controls.dbgrid    import DbGrid

import awc.util as awu

def SetFirstFocus(parent):
    if parent.IsShown():
        if awu.GetParentFrame(parent).IsShown():
            for ctrl in awu.GetAllChildrens(parent):
                if isinstance(ctrl, (TextCtrl, NumCtrl, DateCtrl, CheckBox, RadioBox, Choice, LinkTable, DbGrid)):
                    if hasattr(ctrl, 'this'):
                        def SetFocus():
                            try:
                                ctrl.SetFocus()
                            except:
                                pass
                        wx.CallAfter(SetFocus)
                    break
