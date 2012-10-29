#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         xpaths.py
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

import sys, os
import wx

from version import appcode, appdesc

def GetConfigPath(_appdesc=None, _appcode=None):
    _appcode = _appcode or appcode
    _appdesc = _appdesc or appdesc
    config_base_path = os.getenv("X4_CONFIG_PATH")
    if not config_base_path:
        if sys.platform.startswith('linux'):
            config_base_path = os.path.expanduser('~/.%s' % _appcode)
        elif sys.platform.startswith('win32'):
            import wx
            a = wx.GetApp()
            isapp = a is not None
            if not isapp:
                a = wx.PySimpleApp()
                a.SetAppName(_appdesc)
            else:
                if a.GetAppName() != _appdesc:
                    a.SetAppName(_appdesc)
            sp = wx.StandardPaths.Get()
            config_base_path = wx.StandardPaths.GetConfigDir(sp)
            if not isapp:
                a.Destroy()
        else:
            raise Exception, "Piattaforma sconosciuta"
    if not os.path.isdir(config_base_path):
        os.mkdir(config_base_path)
    return config_base_path

def GetPluginPath(appdesc=None, path=None):
    if path is None:
        path = GetConfigPath(appdesc)
    return os.path.join(path, 'plugin').replace('\\', '/')

def GetAddonPath(appdesc=None, path=None):
    if path is None:
        path = GetConfigPath(appdesc)
    return os.path.join(path, 'addon').replace('\\', '/')

def GetCustomPath(appdesc=None, path=None):
    if path is None:
        path = GetConfigPath(appdesc)
    return os.path.join(path, 'cust').replace('\\', '/')
