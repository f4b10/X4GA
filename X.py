#!/usr/bin/python2
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         X.py
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

import glob

import stormdb as adb
adb.db.setlog(False)

import xpaths
config_base_path = xpaths.GetConfigPath()

if hasattr(sys, 'frozen'):
    
    try:
        os.chdir(os.path.split(sys.argv[0])[0])
    except:
        pass
    
    sp = []
    
    for file in glob.glob(os.path.join(config_base_path, 'cust/*.zip')):
        sp.append(file.replace('/', '\\'))
    
    for file in glob.glob(os.path.join(config_base_path, 'plugin/*.zip')):
        sp.append(file.replace('/', '\\'))
    
    for file in glob.glob(os.path.join(config_base_path, 'addon/*.zip')):
        sp.append(file.replace('/', '\\'))
    
    for n in range(len(sp)-1, -1, -1):
        sys.path.insert(0, sp[n])
    

stdmod = 10
modmod = 0

#import mx.DateTime
#d = mx.DateTime.now()
#if d.month == 12:
#    if 11 <= d.day <= 25:
#        import images
#        for prefix in 'Splash X4'.split():
#            for name in 'Bitmap,Data,Image'.split(','):
#                setattr(images, 'get%sLogo%s' % (prefix, name), 
#                        getattr(images, 'get%sLogoNatale%s' % (prefix, name)))
#    elif d.day > 25:
#        import images
#        for prefix in 'Splash X4'.split():
#            for name in 'Bitmap,Data,Image'.split(','):
#                setattr(images, 'get%sLogo%s' % (prefix, name), 
#                        getattr(images, 'get%sLogoBrindisi%s' % (prefix, name)))
#elif d.month == 1 and d.day <= 6:
#    import images
#    for prefix in 'Splash X4'.split():
#        for name in 'Bitmap,Data,Image'.split(','):
#            setattr(images, 'get%sLogo%s' % (prefix, name), 
#                    getattr(images, 'get%sLogoBefana%s' % (prefix, name)))

import wx
import awc.wxinit

import xsplash

import impex

dummy_app = wx.PySimpleApp()
dummy_app.splash = xsplash.XSplashScreen(stdmod)
dummy_app.splash.SetJob("Inizializzazione in corso...")
dummy_app.splash.Show()

try:
    #aggancio personalizzazione
    import custapp
except ImportError, e:
    if not 'custapp' in repr(e.args):
        import awc.util as awu
        awu.MsgDialog(None, "Errore di importazione modulo in caricamento personalizzazione:\n%s" % repr(e.args))
except Exception, e:
    import awc.util as awu
    awu.MsgDialog(None, "Errore in caricamento personalizzazione:\n%s" % repr(e.args))

import xapp

dummy_app.Destroy()

import Env

#app = xapp.XApp(redirect=bool(not getattr(sys, 'frozen', True)))
app = xapp.XApp(redirect=bool(not getattr(sys, 'frozen', True)) or Env.Azienda.params['redirect-output'])
app.splash = dummy_app.splash

#import awc.controls.linktable as lt
#lt.LinkTable._codewidth = 50

adb.dbtable.DbInfo.GetEnv = classmethod(lambda *x: Env)

Env.SetConfigBasePath()

if not Env.InitSettings():
    if app.splash:
        app.splash.Destroy()
    import wx
    import awc.util as awu
    awu.MsgDialog(None, 
                  """X4 necessita di una licenza d'uso per funzionare """
                  """correttamente.\nImpossibile proseguire in mancanza """
                  """delle informazioni richieste.""",
                  style=wx.ICON_WARNING)
    import os
    os.sys.exit()

#aggancio plugins
if hasattr(sys, 'frozen'):
    plugins = Env.plugins
    #carico plugins
    files = glob.glob(Env.opj(Env.plugin_base_path, '*.zip'))
    files.sort()
    for file in files:
        file = file.replace('\\','/')
        n = file.rindex('/')
        name = file[n+1:-4]
        n2i = name
        if not n2i.endswith('_plugin'):
            n2i += '_plugin'
        try:
            #aggancio plugin
            m = __import__(n2i)
            if hasattr(m, 'TabStru'):
                m.TabStru(Env.Azienda.BaseTab)
        except ImportError, e:
            print 'import fallito di %s: %s' % (name, repr(e.args))
            m = None
        if m is not None:
            if name.endswith('_plugin'):
                name = name[:-7]
            plugins[name] = m


import xframe as xfr


def Main():
    
    try:
        import custrun
    except ImportError:
        pass
    
    import erman
    def _exceptionhook(type, err, traceback):
        erman.ErrorWarning(err, traceback)
    sys.excepthook = _exceptionhook
    
    app.StartApp()
    app.MainLoop()
    
    prg = Env.Azienda.params['onexit-execute']
    if prg:
        db = Env.adb.db.__database__
        if db:
            try:
                prg = prg.replace('[sql_username]', db.username)
                prg = prg.replace('[sql_password]', db.password)
            except:
                pass
        parts = prg.split()
        prg = parts[0]
        try:
            if len(parts) == 1:
                os.execl(prg)
            else:
                os.execl(prg, *parts)
        except:
            pass


if __name__ == '__main__':
    
    Main()
    
    os._exit(0)
