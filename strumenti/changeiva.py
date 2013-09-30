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
import strumenti.changeiva_wdr as wdr

import anag.dbtables as dba
adb = dba.adb


import Env
bt = Env.Azienda.BaseTab

from awc.controls import EVT_DATECHANGED

import awc.controls.linktable as linktab

FRAME_TITLE = "Cambia codice Iva a prodotti"




class ChangeIvaPanel(aw.Panel):
    
    oldIva=None
    newIva=None
    btnChange=None
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.ChangeIvaFunc(self)
        cn = self.FindWindowById
        
        self.oldIva=cn(wdr.ID_OLDIVA)
        self.newIva=cn(wdr.ID_NEWIVA)
        self.btnChange=cn(wdr.ID_BTNCHANGE)
        self.btnCancel=cn(wdr.ID_BTNABORT)
        
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnOldIvaChanged, self.oldIva)
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnNewIvaChanged, self.newIva)
        self.Bind(wx.EVT_BUTTON, self.OnChangeIva, self.btnChange)
        self.Bind(wx.EVT_BUTTON, self.OnAbort, self.btnCancel)
    
    def OnOldIvaChanged(self, event):
        o = event.GetEventObject()
        if self.Validate(o.GetValue(), self.newIva.GetValue()):
            self.btnChange.Enable(True)
        event.Skip()
    
    def OnNewIvaChanged(self, event):
        o = event.GetEventObject()
        if self.Validate(self.oldIva.GetValue(), o.GetValue()):
            self.btnChange.Enable(True)
        event.Skip()
    
    def Validate(self, oldValue, newValue):
        return not oldValue is None and not newValue is None and not oldValue==newValue
            
    def OnChangeIva(self, event):
        msg="ATTENZIONE!\n"
        msg=msg+"L'operazione non è annullabile. Prima di procedere si consiglia di effettuare un backup degli archivi.\n"
        msg=msg+"Si desidera procedere?"
        if aw.awu.MsgDialog(self, msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            self.ChangeIva(self.oldIva.GetValue(), self.newIva.GetValue())

    def OnAbort(self, event):
        event.Skip()
        
    def CreateNewSpeInc(self, oldIva, newIva, r):
        oldId=r[0]
        oldCodice=r[1]
        oldDescriz=r[2]
        oldImporto=r[3]
        oldId_aliqiva=r[4]
        db = adb.db.__database__
        cmd="select perciva FROM %s where id=%s" % (bt.TABNAME_ALIQIVA, newIva)
        db.Retrieve(cmd)
        newAliqIva=int(db.rs[0][0])
        newCodice='%s.%s' % (oldCodice, newAliqIva)
        newDescriz='%s.%s' % (oldDescriz, newAliqIva)
        cmd="INSERT INTO %s (codice, descriz, importo, id_aliqiva) VALUES ('%s', '%s', %s, %s)" % (bt.TABNAME_SPEINC, newCodice, newDescriz, oldImporto, newIva)
        db.Retrieve(cmd)
        cmd="select id FROM %s where codice='%s'" % (bt.TABNAME_SPEINC, newCodice)        
        db.Retrieve(cmd)
        return db.rs[0][0]
        
    def ChangeIva(self, oldIva, newIva):
        db = adb.db.__database__
        db1 = adb.db.__database__
        cmd="select COUNT(*) FROM %s where id_aliqiva=%s" % (bt.TABNAME_SPEINC, oldIva)
        db.Retrieve(cmd)
        speinc=db.rs
        nCliSpeChg=0
        if speinc[0][0]>0:
            db.Retrieve('select * FROM %s where id_aliqiva=%s' % (bt.TABNAME_SPEINC, oldIva))
            speinc=db.rs
            for x in speinc:
                oldIdSpe=x[0]
                newIdSpe=self.CreateNewSpeInc(oldIva, newIva, x )
                cmd="select COUNT(*) FROM %s where id_speinc=%s" % (bt.TABNAME_CLIENTI, oldIdSpe)
                db1.Retrieve(cmd)                
                nCliSpeChg=nCliSpeChg+db1.rs[0][0]
                cmd = "UPDATE %s SET id_speinc=%s WHERE id_speinc=%s" % (bt.TABNAME_CLIENTI, newIdSpe, oldIdSpe)
                db1.Execute(cmd)
        cmd="select COUNT(*) FROM %s where id_aliqiva=%s" % (bt.TABNAME_PROD, oldIva)
        db.Retrieve(cmd)
        prod=db.rs
        nProdChg=prod[0][0]
        cmd="select COUNT(*) FROM %s where id_aliqiva=%s" % (bt.TABNAME_CLIENTI, oldIva)
        db.Retrieve(cmd)
        cli=db.rs
        nCliChg=cli[0][0]
        cmd = "UPDATE %s SET id_aliqiva=%s WHERE id_aliqiva=%s" % (bt.TABNAME_PROD, newIva, oldIva)
        db.Execute(cmd)
        cmd = "UPDATE %s SET id_aliqiva=%s WHERE id_aliqiva=%s" % (bt.TABNAME_CLIENTI, newIva, oldIva)
        db.Execute(cmd)
        msg="L'elaborazione ha modificato:\n"
        msg=msg+"%s Articoli\n" % nProdChg
        msg=msg+"%s Anagrafiche Clienti con Aliquota Preimpostata\n" % nCliChg
        msg=msg+"%s Anagrafiche Clienti soggette a spese di incasso\n" % nCliSpeChg
        aw.awu.MsgDialog(self, msg)
        

class ChangeIvaFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ChangeIvaPanel(self))
        self.Bind(wx.EVT_BUTTON, self.OnAbort, id=wdr.ID_BTNABORT)
    
        
    def OnAbort(self, event):
        self.Close()
        event.Skip()




    def Abort(self):
        self.Close()
# ------------------------------------------------------------------------------
