#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         erman.py
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
import sys, os, time, traceback, types
import awc.controls.windows as aw
import Env
import erman_wdr as wdr
import httplib, mimetypes


def ErrorWarning(e, tb_info=None):
    dlg = X4ErrorDialog(wx.GetActiveWindow(), 
                        err=X4Error(e, sys.exc_info(), tb_info))
    dlg.ShowModal()
    dlg.Destroy()
    

# ------------------------------------------------------------------------------


class X4Error:
    """Wraps and stores information about the current exception"""
    def __init__(self, error, exc_info, tb_info=None):
        import copy
        
        excType, excValue = exc_info[:2]
        self.error = error
        
        if tb_info is None:
            # traceback list entries: (filename, line number, function name, text)
            tb_info = exc_info[2]
        self.traceback = traceback.extract_tb(tb_info)
        
        # --Based on traceback.py::format_exception_only()--
        if type(excType) == types.ClassType:
            self.exception_type = excType.__name__
        else:
            self.exception_type = excType
        
        # If it's a syntax error, extra information needs
        # to be added to the traceback
        if excType is SyntaxError:
            try:
                msg, (filename, lineno, self.offset, line) = excValue
            except:
                pass
            else:
                if not filename:
                    filename = "<string>"
                line = line.strip()
                self.traceback.append( (filename, lineno, "", line) )
                excValue = msg
        try:
            self.exception_details = str(excValue)
        except:
            self.exception_details = "<unprintable %s object>" & type(excValue).__name__
        del exc_info
        self.genfile()
    
    def genfile(self):
        az = Env.Azienda
        path = os.path.join(az.config.Site_folder, 'errors').replace('\\','/')
        if not os.path.exists(path):
            os.mkdir(path)
        if az.license is not None:
            key = az.license.License_pswd
        else:
            key = Env.MODVERSION_NAME
            if not key:
                key = "GENERIC"
        import glob
        files = glob.glob(os.path.join(path, '%s_*.x4err' % key))
        if files:
            files.sort()
            f = files[-1]
            parts = f.split('_')
            n = int(parts[-1][:6])+1
        else:
            n = 1
        self.filename = os.path.join(path, '%s_%s.x4err' \
                                     % (key, str(n).zfill(6))).replace('\\','/')
        m = [0,0,0,0]
        for tb in self.traceback:
            for n in range(4):
                m[n] = max(m[n], len(str(tb[n])))
        h = open(self.filename, 'w')
        def w(x):
            h.write('%s\n' % x)
        d = Env.DateTime.now()
        w('Eccezione: %s - %s' % tuple(d.Format().split()))
        x = ' Versione: %s' % Env.__version__
        import version as v
        if v.MODVERSION_NAME:
            x += ' mod '+v.MODVERSION_NAME+' v. '+v.MODVERSION_STRING
        else:
            x += ' head'
        w(x)
        w('  Azienda: %s - %s' % (az.codice, az.descrizione))
        w('Operatore: %s - %s' % (az.Login.usercode, az.Login.username))
        w('')
        w('Traceback:')
        for tb in self.traceback:
            w('%s | %s | %s | %s' % tuple([str(x).ljust(m[n]) 
                                           for n, x in enumerate(tb)]))
        w(repr(self.error))
        w(str(self.error))
        h.close()
    
    def __str__(self):
        ret = "Type %s \n \
        Traceback: %s \n \
        Details  : %s" % (str(self.exception_type), 
                          str(self.traceback), 
                          self.exception_details)
        return ret


# ------------------------------------------------------------------------------


class X4ErrorPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        err = kwargs.pop('err')
        wx.Panel.__init__(self, *args, **kwargs)#, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        wdr.ErrorPanelFunc(self)
        #Clr = wx.TheColourDatabase.Find
        #self.SetBackgroundColour(Clr('tan'))
        #for c in aw.awu.GetAllChildrens(self):
            #if isinstance(c, wx.Button):
                #c.SetForegroundColour(Clr('yellow'))
                #c.SetBackgroundColour(Clr('red'))
        def ci(x): return self.FindWindowById(x)
        ci(wdr.ID_ERROR).SetValue('%s\n%s'%(repr(err.error),
                                            str(err.error)))
        ci(wdr.ID_ERROR).SetEditable(False)
        self.list = ci(wdr.ID_DETAILS)
        self.list.InsertColumn(0, "Filename")
        self.list.InsertColumn(1, "Line", wx.LIST_FORMAT_RIGHT)
        self.list.InsertColumn(2, "Function")
        self.list.InsertColumn(3, "Code")
        for col, size in enumerate((110,40,100,300)):
            self.list.SetColumnWidth(col, size)
        self.InsertTraceback(self.list, err.traceback)
        self.err = err
        self.Bind(wx.EVT_BUTTON, self.OnSend, id=wdr.ID_SEND)
    
    def InsertTraceback(self, list, traceback):
        #Add the traceback data
        for x in range(len(traceback)):
            file, line, func, code = traceback[x]
            list.InsertStringItem(x, os.path.basename(file)) # Filename
            list.SetStringItem(x, 1, str(line))              # Line
            list.SetStringItem(x, 2, str(func))              # Function
            list.SetStringItem(x, 3, str(code))              # Code
            self.list.SetItemData(x, -1)

    def OnSend(self, event):
        note = self.FindWindowById(wdr.ID_NOTEOP).GetValue()
        if not note:
            msg =\
            """ATTENZIONE!\n\n"""\
            """Non è stata scritta alcuna nota circa l'errore che si sta inviando.\n"""\
            """In molti casi, la sola segnalazione di errore sprovvista di note esplicative\n"""\
            """dell'operatore causa difficoltà di interpretazione e pone ostacoli alla sua\n"""\
            """risoluzione.\n\n"""\
            """Si consiglia di descrivere brevemente l'ambito in cui esso si è manifestato,\n"""\
            """ovvero dove è successo l'errore ed in seguito a cosa.\n\n"""\
            """Confermi l'invio senza annotazioni?"""
            if aw.awu.MsgDialog(self, msg, "Richiesta di conferma dell'invio segnalazione", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return
        self.SendTraceback()
        event.Skip()
    
    def SendTraceback(self):
        import urllib2, base64
        server = Env.Azienda.config.Updates_url
        if not server.endswith('/'):
            server += '/'
        url = server+'traceback/fileupload.php'
        note = self.FindWindowById(wdr.ID_NOTEOP).GetValue()
        if note:
            fd = open(self.err.filename, 'ab')
            fd.write("\nNote operatore:\n%s" % note)
            fd.close()
        fd = open(self.err.filename, 'rb')
        data = {'traceback_file' : fd,}
        cfg = Env.Azienda.config
        string = '%s:%s' % (cfg.Updates_user, cfg.Updates_pswd)
        stringb64 = base64.encodestring(string)[:-1]
        wait = aw.awu.WaitDialog(self, message="Connessione in corso...",
                                 maximum=2)
        req = urllib2.Request(url, data, {"Authorization": "Basic %s" % stringb64})
        wait.SetValue(1)
        err = None
        try:
            wait.SetMessage("Trasmissione dettagli problema in corso...")
            u = urllib2.urlopen(req)
            wait.SetValue(2)
            wx.Sleep(1)
            r = u.read()
            if (r or '  ')[:2] != "OK":
                err = r
        except urllib2.HTTPError, errobj:
            err = "HTTPError %s" % errobj.code
        except:
            pass
        wait.Destroy()
        if err:
            aw.awu.MsgDialog(self, message="Trasmissione non riuscita:\n%s" % err)
        else:
            aw.awu.MsgDialog(self, message="Trasmissione effettuata con successo",
                             style=wx.ICON_INFORMATION)


# ------------------------------------------------------------------------------


class X4ErrorDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        err = kwargs.pop('err')
        if not 'style' in kwargs:
            kwargs['style'] = wx.BORDER_RAISED
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = X4ErrorPanel(self, err=err)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose)
    
    def OnClose(self, event):
        self.EndModal(wx.ID_ABORT)
