#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/prodripro.py
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

import magazz.dbtables as dbm

import magazz.invent_wdr as wdr

Env = dbm.Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours


FRAME_TITLE = "Ricalcolo progressivi prodotti"


class ProdRiProPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.year = Env.Azienda.Esercizio.year
        
        self.dbmag = dbm.dba.TabMagazz()
        self.dbinv = dbm.InventarioDaMovim(flatmag=True)
        
        self.dbpro = dbm.ProdProgrDaScheda()
        
        wdr.ProdRiProFunc(self)
        self.FindWindowByName('datinv').SetValue(Env.Azienda.Esercizio.dataElab)
        
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, id=wdr.ID_BUTUPD)
    
    def OnUpdate(self, event):
        if self.Validate():
            if self.UpdateInv():
                event.Skip()
    
    def Validate(self):
        data = self.FindWindowByName('datinv').GetValue()
        if data is None or data>Env.Azienda.Esercizio.dataElab:
            aw.awu.MsgDialog(self, message="Data errata", style=wx.ICON_WARNING)
            return False
        return True
    
    def UpdateInv(self):
        
        magid = self.FindWindowByName("id_magazz").GetValue()
        
        cmd = "DELETE FROM %s" % bt.TABNAME_PRODPRO
        if magid:
            cmd += " WHERE id_magazz=%d" % magid
        
        wait = aw.awu.WaitDialog(self,
                                 message="Azzeramento progressivi in corso")
        db = self.dbpro._info.db
        db.Execute(cmd)
        wait.Destroy()
        
        wait = aw.awu.WaitDialog(self,
                                 title="Ricalcolo inventario",\
                                 maximum=0)
        
        try:
            
            dbmag = self.dbmag
            dbmag.ClearFilters()
            if magid:
                dbmag.Get(magid)
            else:
                dbmag.Retrieve()
            
            for mag in dbmag:
                
                i = self.dbinv
                for x in (i, i.mov):
                    x.ClearFilters()
                
                i.mov.AddFilter("doc.id_magazz=%s", mag.id)
                data = self.FindWindowByName("datinv").GetValue()
                if data is not None:
                    i.mov.AddFilter("doc.datreg<=%s", data)
                
                wait.SetMessage('Inventario magazzino: %s - %s' % (mag.codice, mag.descriz))
                wait.SetRange(0)
                i.Retrieve()
                wait.SetMessage('Progressivi magazzino: %s - %s' % (mag.codice, mag.descriz))
                wait.SetRange(self.dbinv.RowsCount())
                
                inv = self.dbinv
                pro = self.dbpro
                
                for i in inv:
                    pro.CreateNewRow()
                    pro.id_prod = i.id
                    pro.id_magazz = mag.id
                    pro.ini =    inv.total_ini or 0
                    pro.car =    inv.total_car or 0
                    pro.sca =    inv.total_sca or 0
                    pro.iniv =   inv.total_iniv or 0
                    pro.carv =   inv.total_carv or 0
                    pro.scav =   inv.total_scav or 0
                    pro.cvccar = inv.total_cvccar or 0
                    pro.cvcsca = inv.total_cvcsca or 0
                    pro.cvfcar = inv.total_cvfcar or 0
                    pro.cvfsca = inv.total_cvfsca or 0
                    wait.SetValue(i.RowNumber())
        
        finally:
            wait.Destroy()
        
        if pro.Save():
            aw.awu.MsgDialog(self, message="Ricalcolo effettuato",
                             style=wx.ICON_INFORMATION)
            return True
        else:
            aw.awu.MsgDialog(self, message="Problema in aggiornamento progressivi:\n%s" % repr(pro.GetError()),
                             style=wx.ICON_ERROR)
            return False


# ------------------------------------------------------------------------------


class ProdRiProFrame(aw.Frame):
    """
    Frame Inventario magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProdRiProPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BUTUPD)
    
    def OnClose(self, event):
        self.Close()


# ------------------------------------------------------------------------------


class ProdRiProDialog(aw.Dialog):
    """
    Dialog Inventario magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProdRiProPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BUTUPD)
    
    def OnClose(self, event):
        self.EndModal(wx.ID_OK)
