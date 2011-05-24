#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         plugins.py
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
import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc.controls.windows as aw

import Env

import X_wdr as wdr

class PluginInfo(object):
    name =\
    title =\
    version =\
    author =\
    info = '-'
    def __init__(self, name):
        object.__init__(self)
        self.name = name


# ------------------------------------------------------------------------------


class PluginsGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        def FormattaDescrizione(x):
            x = x.replace('.\n', '.<cr>')
            x = x.replace('\n', '')
            x = x.replace('<cr>', '\n')
            return x
        
        rsp = []
        if True:#Env.MODVERSION_NAME:
            try:
                import custapp
                if hasattr(custapp, 'name'):
                    i = PluginInfo(custapp.name)
                    try: 
                        i.title = custapp.title
                    except AttributeError:
                        i.title = '???'
                    try: 
                        i.version = custapp.custver.v.MODVERSION_STRING
                    except AttributeError:
                        i.version = '???'
                    try: 
                        i.author = custapp.author
                    except AttributeError:
                        i.author = '???'
                    try: 
                        i.info = FormattaDescrizione(custapp.description)
                    except AttributeError:
                        i.description = '???'
                    rsp.append((i.name, i.title, i))
            except ImportError:
                pass
        
        plugins = Env.plugins
        names = plugins.keys()
        names.sort()
        for name in names:
            p = plugins[name]
            i = PluginInfo(name)
            try: 
                i.title = p.title
            except AttributeError: pass
            try: 
                i.version = p.version
            except AttributeError: pass
            try: 
                i.author = p.author
            except AttributeError: pass
            try: 
                i.info = FormattaDescrizione(p.description)
            except AttributeError: pass
            rsp.append((name, i.title, i))
        self.rsp = rsp
        
        _STR = gl.GRID_VALUE_STRING
        
        cols = (\
            (100, (0, "Nome",        _STR, True)),\
            (100, (1, "Descrizione", _STR, True)),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(rsp, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class PluginsPanel(wx.Panel):
    """
    Panel Informazioni sui plugin installati.
    """
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.PluginsFunc(self)
        self.grid = PluginsGrid(self.FindWindowById(wdr.ID_PANGRIDPLUGINS))
        self.UpdateData()
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnSelect)
    
    def OnSelect(self, event):
        self.UpdateData(event.GetRow())
        event.Skip()
    
    def UpdateData(self, row=0):
        info = self.grid.rsp[row][2]
        def ci(x):
            return self.FindWindowById(x)
        assert isinstance(info, PluginInfo)
        for cid, label in ((wdr.ID_PLUGINNAME, info.name),
                           (wdr.ID_PLUGINDESC, info.title),
                           (wdr.ID_PLUGINVERS, info.version),
                           (wdr.ID_PLUGINAUTH, info.author)):
            ci(cid).SetLabel(label)
        ci(wdr.ID_PLUGININFO).SetValue(info.info)


# ------------------------------------------------------------------------------


class PluginsDialog(aw.Dialog):
    """
    Dialog Informazioni sui plugin installati.
    """
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        p = PluginsPanel(self)
        self.AddSizedPanel(p)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_PLUGINEND)
    
    def OnClose(self, event):
        self.EndModal(wx.ID_OK)
