#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/pdfprint.py
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

import os, sys

import wx


def PdfPrint(filename, printer, copies=1, cbex=None, usedde=False, cmdprint=False, pdfcmd=None):
    """ print a pdf """
    
    out = False
    if usedde:
        
        ## create a DDE connection and open acrobat if possible
        res = _checkAcrobatOpen(1, cbex)
    
        if not res:
            return
        
        ddeServer = res[0]
        ddeConv = res[1]
        
        try:
            for n in range(copies):
                if n>0:
                    wx.Sleep(1)
                ddeConv.Exec('[FilePrintTo("%s", "%s")]' % (filename, printer))
            out = True
        except:
            pass
        
        ddeServer.Destroy()
    
    if cmdprint and bool(pdfcmd):
        import subprocess
        try:
            subprocess.Popen([pdfcmd, '/t', filename, printer])
            out = True
        except:
            pass
    
    if cbex:
        cbex()
    
    return out

#------------------------------------------------------------------------------

def PdfView(filename, cbex=None, usedde=False, pdfcmd=None):
    
    out = False
    dorun = not usedde
    
    if usedde:
        res = _checkAcrobatOpen(1, cbex)
        if res:
            ddeServer = res[0]
            ddeConv = res[1]
            try:
                ddeConv.Exec('[DocOpen("%s")]' % filename)
                out = True
            except:
                pass
            ddeServer.Destroy()
            if cbex:
                cbex()
        else:
            dorun = True
        
    elif pdfcmd:
        import subprocess
        try:
            subprocess.Popen([pdfcmd, filename])
            dorun = False
        except:
            pass
    
    if dorun:
        try:
            os.startfile(filename)
            out = True
        except WindowsError, e:
            import awc.util as awu
            if e.errno == 1155:
                msg = "Sembra che i file PDF su questo computer\nnon vengano riconosciuti.\n\nAssicurarsi di avere installato un adeguato browser,\nadesempio Adobe Reader o similari."
            else:
                msg = repr(e.args)
            awu.MsgDialog(None, msg, style=wx.ICON_ERROR)
        except Exception, e:
            pass
    
    return out

#------------------------------------------------------------------------------

def _launchAcrobat():
    try:
        """ try to find the acrobat executable and launch it """
        import win32api, win32con
        r = win32api.RegOpenKeyEx(win32con.HKEY_CLASSES_ROOT, 
                                  'AcroExch.Document\\Shell\\Open\\Command')
        v = win32api.RegEnumValue(r, 0)
        r.Close()
        cmd = v[1].split('"')[1]
        try:
            os.spawnl(os.P_DETACH, cmd, 'acrobat')
            #wx.Sleep(3)
            return 1
        except:
            pass
    except Exception, e:
        pass
    return 0

#------------------------------------------------------------------------------

def _checkAcrobatOpen(launch=0, cbex=None):
    """ try to create a DDE conversation, if it fails, launch acrobat and try again """
    try:
        (s, c) = _connectAcrobat()
        return (s, c)
    except:
        if launch:
            if not _launchAcrobat():
                return 0
            if cbex:
                cbex()
        for i in xrange(5):
            try:
                (s, c) = _connectAcrobat()
                return (s, c)
            except Exception, e:
                wx.Sleep(1)

#------------------------------------------------------------------------------

def _connectAcrobat():
    """ Create a DDE server and conversation with acroview """
    s = None
    try:
        import win32ui
        import dde
        s = dde.CreateServer()
        s.Create('')
        c = dde.CreateConversation(s)
        c.ConnectTo('acroview', 'control')
        return (s, c)
    except:
        if s:
            s.Destroy()
        raise Exception, 'DDE link failed'
