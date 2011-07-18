#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dbtables.py
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
import awc.controls.windows as aw
import awc.controls.dbgrid as dbgrid

import contab.dbtables as dbc

import cfg.spesometro_2011_wdr as wdr


FRAME_TITLE = "Massimali Spesometro"


class MassimaliSpesometroPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.MassimaliSpesometroFunc(self)
        cn = self.FindWindowByName
        self.dbmsm = dbc.Spesometro2011_Massimali()
        self.gridmsm = MassimaliSpesometroGrid(cn('pangridmass'), self.dbmsm)
        self.Bind(wx.EVT_BUTTON, self.OnSaveData, cn('butsave'))
    
    def OnSaveData(self, event):
        if not self.dbmsm.Save():
            aw.awu.MsgDialog(self, repr(self.dbmsm.GetError()), style=wx.ICON_ERROR)
            return
        event.Skip()


# ------------------------------------------------------------------------------


class MassimaliSpesometroGrid(dbgrid.ADB_Grid):
    
    def __init__(self, parent, dbmsm):
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbmsm, can_edit=True, can_insert=True)
        
        msm = dbmsm
        self.AddColumn(msm, 'keydiff',   'Anno', is_fittable=True)
        self.AddColumn(msm, 'progrimp1', 'Aziende', col_type=self.TypeFloat(9, 2), is_editable=True)
        self.AddColumn(msm, 'progrimp2', 'Privati', col_type=self.TypeFloat(9, 2), is_editable=True)
        self.CreateGrid()


# ------------------------------------------------------------------------------


class MassimaliSpesometroFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = MassimaliSpesometroPanel(self)
        self.AddSizedPanel(self.panel)
        cn = self.FindWindowByName
        self.Bind(wx.EVT_BUTTON, self.OnDataSaved, cn('butsave'))
    
    def OnDataSaved(self, event):
        self.Close()
