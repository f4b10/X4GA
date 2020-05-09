#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         strumenti/changeiva.py
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

import wx
import os

import awc.controls.windows as aw
import awc.controls.dbgrid as dbgrid

import strumenti
import strumenti.ripara_wdr as wdr

import anag.dbtables as dba
adb = dba.adb


import Env
bt = Env.Azienda.BaseTab

from awc.controls import EVT_DATECHANGED

import awc.controls.linktable as linktab

FRAME_TITLE = "Riparazione Tabelle"




class RiparaPanel(aw.Panel):
    
    oldIva=None
    newIva=None
    btnChange=None
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.RiparaFunc(self)
        ci = self.FindWindowById
        cn = self.FindWindowByName
        
        self.dbCurs = self.GetDbCurs()
        
        self.btnChange=ci(wdr.ID_BTNCHANGE)
        self.btnCancel=ci(wdr.ID_BTNABORT)
        self.Titolo   =cn('labelTitolo')
        self.Stato    =cn('stato')
        self.Bind(wx.EVT_BUTTON, self.OnRipara, self.btnChange)
        self.Bind(wx.EVT_BUTTON, self.OnAbort, self.btnCancel)
        self.Titolo.SetLabel('Riparazione tabelle del database %s' % Env.Azienda.DB.schema)
            
    def GetDbCurs(self):
        return Env.Azienda.DB.connection.cursor()              
            
    def OnRipara(self, event):
        
        from cfg.tabsetup import WarningDialog
        dlg = WarningDialog(self)
        do = (dlg.ShowModal() == wx.ID_OK)
        dlg.Destroy()
        
        if do:
            self.Ripara()
            
    def Ripara(self):
        
        
        self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))        
        
        
        msg=''
        cmd = 'SHOW TABLES'
        cmd = "show full tables where Table_Type = 'BASE TABLE'"
        
        
        self.dbCurs.execute(cmd)
        res = self.dbCurs.fetchall()
        lTable = [w for (w,_) in res]
        lTable.sort()
        
        nOk    = 0
        nError = 0
        for i, n in enumerate(lTable):
            try:
                indexes = [j for j,x in enumerate(Env.Azienda.BaseTab.tabelle) if x[0] == n][0]
                des = Env.Azienda.BaseTab.tabelle[indexes][1]
            except:
                des = 'tabella temporanea'
            des = '%s%s' % (des, ' '*60)
            des = des[0:40]
            n = '%s%s' % (n, ' '*60)
            n = n[0:20]
            
            if i==0:
                msg = '%03d - %s %s' % (i+1, n, des)
            else:
                msg = '%s\n%03d - %s %s' % (msg, i+1, n,  des)
            self.Stato.SetValue(msg)
            self.Stato.SetInsertionPointEnd()
            
            cmd = 'REPAIR TABLE %s' % n
            self.dbCurs.execute(cmd)
            ret = self.dbCurs.fetchall()
            esito = ret[0][3]
            
            
            
            
            #===================================================================
            # if i==0:
            #     msg = '%03d - %s %s %s' % (i+1, n, des, esito)
            # else:
            #     msg = '%s\n%03d - %s %s %s' % (msg, i+1, n,  des, esito)
            #===================================================================
            if esito=='OK':
                nOk = nOk + 1
            else:
                nError = nError + 1
                
            msg = '%s %s' % (msg, esito)
            self.Stato.SetValue(msg)
            self.Stato.SetInsertionPointEnd()
            
            
            wx.YieldIfNeeded()

        msg = '%s\n%s' % (msg, '='*70)
        self.Stato.SetValue(msg)
        self.Stato.SetInsertionPointEnd()
        
        msg1=""
        msg1=msg1+"%03d Tabelle riparate.   \n" % nOk
        msg1=msg1+"%03d Tabelle non riparate." % nError
        
        msg = '%s\n%s\n%s' % (msg, msg1, '='*70)
        self.Stato.SetValue(msg)
        self.Stato.SetInsertionPointEnd()
        aw.awu.MsgDialog(self, msg1, style=wx.ICON_INFORMATION)
        #self.Parent.Close()
        self.SetCursor(wx.STANDARD_CURSOR)       

    def OnAbort(self, event):
        event.Skip()
        

class RiparaFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(RiparaPanel(self))
        self.Bind(wx.EVT_BUTTON, self.OnAbort, id=wdr.ID_BTNABORT)
    
        
    def OnAbort(self, event):
        self.Close()
        event.Skip()




    def Abort(self):
        self.Close()
# ------------------------------------------------------------------------------
