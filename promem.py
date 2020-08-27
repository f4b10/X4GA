#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         promem.py
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
import wx.gizmos as gizmos
import stormdb as adb
import Env
bt = Env.Azienda.BaseTab

import awc.controls.windows as aw
import promem_wdr as wdr


evt_REMINDERCLOSED = wx.NewEventType()
EVT_REMINDERCLOSED = wx.PyEventBinder(evt_REMINDERCLOSED, 1)
class ReminderClosedEvent(wx.PyCommandEvent):
    pass

evt_PROMEMDELETED = wx.NewEventType()
EVT_PROMEMDELETED = wx.PyEventBinder(evt_PROMEMDELETED, 1)
class PromemDeletedEvent(wx.PyCommandEvent):
    pass


class TimerCheck(wx.Timer):
    tipo = 'check'

class TimerAvviso(wx.Timer):
    tipo = 'avviso'


class PromemPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.tree = None
        self.user = None
        self.timer = None
        self.reminder = None
        self.pmdisp = []
        self.soloatt = True
        self.pm = adb.DbTable(bt.TABNAME_PROMEM,  "promem", writable=True)
        pmu = self.pm.AddJoin(bt.TABNAME_PROMEMU, "pmu", 
                              idLeft="id", idRight="id_promem", join=adb.JOIN_LEFT)
        self.pm.AddFilter("promem.globale=1 OR pmu.utente=%s", Env.Azienda.Login.usercode)
        self.pm.AddGroupOn("promem.id")
        self.pm.AddOrder("promem.datasca")
        #refresh utenti
        self.pmu = adb.DbTable(bt.TABNAME_PROMEMU, 'pmu', writable=True)
        self.pmu.AddFilter("utente=%s", Env.Azienda.Login.usercode)
        self.pmu.AddFilter("id_promem=-1")
        wdr.PromemRiepFunc(self)
        cn = lambda x: self.FindWindowByName(x)
        cn('_soloatt').Bind(wx.EVT_CHECKBOX, self.OnSoloAtt)
        cn('_nuovopm').Bind(wx.EVT_BUTTON, self.OnNuovoPM)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
    
    def OnSoloAtt(self, event):
        self.soloatt = event.GetEventObject().GetValue()
        self.populate()
        event.Skip()
    
    def OnNuovoPM(self, event):
        dlg = PromemDataDialog(self, -1)
        dlg.SetPromemNew()
        if dlg.ShowModal() == 1:
            self.populate()
        dlg.Destroy()
        event.Skip()
    
    def setUser(self, user):
        self.user = user
    
    def populate(self, refresh=False):
        
        do = True
        if refresh:
            do = self.pmu.Retrieve() and self.pmu.refresh == 1
        
        if not do:
            return
        
        if self.tree: self.tree.Destroy()
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        
        pr = self.FindWindowByName('_panelriep')
        self.tree = gizmos.TreeListCtrl(pr, -1, style =
                                        wx.TR_DEFAULT_STYLE
                                        |wx.TR_FULL_ROW_HIGHLIGHT
                                    )
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.tree.GetMainWindow().Bind(wx.EVT_LEFT_DCLICK, self.OnDblClick)
        
        self.tree.SetImageList(il)
        self.il = il
        
        self.tree.AddColumn("Scadenza")
        self.tree.AddColumn("Oggetto")
        self.tree.SetMainColumn(0) # the one with the tree in it...
        self.tree.SetColumnWidth(0, 175)
        
        self.root = self.tree.AddRoot("Promemoria")
        self.tree.SetItemText(self.root, "", 1)
        self.tree.SetItemImage(self.root, fldridx, which = wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, fldropenidx, which = wx.TreeItemIcon_Expanded)
        
        pm = self.pm
        pm.StoreFilters()
        if self.soloatt:
            pm.AddFilter("promem.status<>1")
        pm.Retrieve()
        pm.ResumeFilters()
        
        for pm in pm:
            
            txt = Env.StrDate(pm.datasca)
            if not txt: txt = '-'
            child = self.tree.AppendItem(self.root, txt)
            self.tree.SetItemText(child, pm.oggetto, 1)
            self.tree.SetItemImage(child, fldridx, which = wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(child, fldropenidx, which = wx.TreeItemIcon_Expanded)
            last = child
            
            txt = "-"
            item = self.tree.AppendItem(last,  txt)
            self.tree.SetItemText(item, pm.descriz, 1)
            self.tree.SetPyData(item, pm.id)
            self.tree.SetItemImage(item, fileidx, which = wx.TreeItemIcon_Normal)
            #self.tree.SetItemImage(item, smileidx, which = wx.TreeItemIcon_Selected)
        
        if self.pmu.Retrieve():
            if self.pmu.refresh:
                self.pmu.refresh = 0
                self.pmu.Save()
        
        self._SetSize()
        self.tree.Expand(self.root)
    
    def autoUpdate(self, seconds=0):
        if seconds:
            if self.timer is None:
                self.timer = TimerCheck(self)
            else:
                self.timer.Stop()
            self.timer.Start(seconds*1000)
    
    def OnTimer(self, event):
        timer = event.GetEventObject()
        if timer.tipo == 'check':
            self.check()
        elif timer.tipo == 'avviso':
            self.testReminder()
        event.Skip()
    
    def check(self):
        self.populate(refresh=True)
    
    def testReminder(self):
        for pm in self.pm:
            now = adb.DateTime.now()
            if pm.avvisa and pm.datarem and pm.status == 0:
                if pm.datarem <= now and not pm.id in self.pmdisp:
                    self.pmdisp.append(pm.id)
                    f = PromemAlertFrame(self)
                    f.SetPromemId(pm.id)
                    f.Show()
                    def OnReminderClose(event):
                        try:
                            n = self.pmdisp.index(event.GetId())
                            self.pmdisp.pop(n)
                            self.populate()
                        except IndexError:
                            pass
                    self.Bind(EVT_REMINDERCLOSED, OnReminderClose)
    
    def startReminder(self, seconds=0):
        if seconds:
            if self.reminder is None:
                self.reminder = TimerAvviso(self)
            else:
                self.reminder.Stop()
            self.reminder.Start(seconds*1000)
    
    def OnSize(self, evt):
        self._SetSize()
        evt.Skip()
    
    def OnDblClick(self, event):
        pos = event.GetPosition()
        item, flags, col = self.tree.HitTest(pos)
        if item:
            pmid = self.tree.GetPyData(item)
            if pmid is not None:
                dlg = PromemDataDialog(self, -1)
                dlg.SetPromemId(pmid)
                if dlg.ShowModal() == 1:
                    self.populate()
                dlg.Destroy()
        try:
            pass
            #event.Skip()
        except:
            pass
    
    def _SetSize(self):
        self.tree.SetSize(self.GetSize())
        w = self.tree.GetSize()[0]
        w -= self.tree.GetColumnWidth(0)
        w -= 10
        if w>0: self.tree.SetColumnWidth(1, w)


# ------------------------------------------------------------------------------


class PromemDataPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.pm = adb.DbTable(bt.TABNAME_PROMEM,  "promem", writable=True)
        self.pm.AddMultiJoin( bt.TABNAME_PROMEMU, "users",
                              idLeft="id", idRight="id_promem", writable=True)
        dbu = adb.DB(globalConnection=False, openMode=adb.OPENMODE_READONLY)
        dbu.Connect(host=Env.Azienda.DB.servername,
                    user=Env.Azienda.DB.username,
                    passwd=Env.Azienda.DB.password,
                    db='x4')
        self.utenti = adb.DbTable("utenti", fields="id,codice,descriz",
                                  writable=False, db=dbu)
        self.utenti.AddOrder("descriz")
        self.ucod = []
        wdr.PromemPanelFunc(self)
        cn = lambda x: self.FindWindowByName(x)
        for name, flags in (('globale', {True: 1, False: 0}),
                            ('avvisa',  {True: 1, False: 0}),
                            ('status',  {True: 1, False: 0}),
                            ):
            cn(name).SetDataLink(name, flags)
        cn('_save').Bind(wx.EVT_BUTTON, self.OnSave)
        cn('_delete').Bind(wx.EVT_BUTTON, self.OnDelete)
        cn('globale').Bind(wx.EVT_CHECKBOX, self.OnGlobale)
        cn('avvisa').Bind(wx.EVT_CHECKBOX, self.OnAvviso)
        self._evtAvviso = False
    
    def SetPromemId(self, pmid):
        self.pm.Get(pmid)
        self.FillControls()
    
    def SetPromemNew(self):
        pm = self.pm
        pm.Get(-1)
        pm.CreateNewRow()
        pm.datains = adb.DateTime.now()
        pm.uteins = Env.Azienda.Login.usercode
        pm.users.CreateNewRow()
        pm.users.utente = pm.uteins
        self.FillControls()

    def FillControls(self):
        cn = lambda x: self.FindWindowByName(x)
        for name in self.pm._GetFieldNames():
            ctr = cn(name)
            if ctr:
                val = self.pm.__getattr__(name)
                if val:
                    ctr.SetValue(val)
        if self.pm.uteins:
            if self.utenti.Retrieve("codice=%s", self.pm.uteins):
                cn("_descuteins").SetValue(self.utenti.descriz)
        self.utenti.Retrieve()
        u = cn('utenti')
        u.Clear()
        del self.ucod[:]
        for n, ute in enumerate(self.utenti):
            u.Append(ute.descriz)
            if self.pm.users.Locate(lambda x: x.utente == ute.codice):
                u.Check(n)
            self.ucod.append(ute.codice)
        self.CheckUtenti()
        self.CheckAvviso()
        cn('_delete').Enable(self.pm.id is not None)
    
    def CheckUtenti(self):
        cn = lambda x: self.FindWindowByName(x)
        glob = cn('globale').GetValue() == 1
        if glob:
            for n in range(len(self.ucod)):
                cn('utenti').Check(n, False)
        cn('utenti').Enable(not glob)
    
    def OnGlobale(self, event):
        self.CheckUtenti()
        event.Skip()
    
    def CheckAvviso(self):
        cn = lambda x: self.FindWindowByName(x)
        enab = (cn('avvisa').GetValue() == 1)
        if enab and self._evtAvviso:
            cn('datarem').SetValue(cn('datasca').GetValue())
        cn('datarem').Enable(enab)
        self._evtAvviso = True
    
    def OnAvviso(self, event):
        self.CheckAvviso()
        event.Skip()
    
    def OnSave(self, event):
        if self.CtrFields():
            cn = lambda x: self.FindWindowByName(x)
            pm = self.pm
            if pm.RowsCount() == 0:
                pm.CreateNewRow()
                pm.uteins = Env.Azienda.Login.usercode
            for name in pm._GetFieldNames():
                ctr = cn(name)
                if ctr:
                    val = ctr.GetValue()
                    if val is not None:
                        pm.__setattr__(name, val)
            for usr in pm.users:
                usr.Delete()
            for n in cn('utenti').GetSelections():
                pm.users.CreateNewRow()
                pm.users.utente = self.ucod[n]
            pm.Save()
            
            #aggiorno refresh utenti coinvolti
            pmu = adb.DbTable(bt.TABNAME_PROMEMU, 'pmu', writable=True)
            pmu.AddFilter("id_promem=-1")
            if pmu.Retrieve():
                for n, u in enumerate(self.ucod):
                    if not pmu.Locate(lambda x: x.utente == u):
                        pmu.CreateNewRow()
                        pmu.id_promem = -1
                        pmu.utente = u
                    if u != Env.Azienda.Login.usercode and\
                       (cn('globale').GetValue() == 1 or cn('utenti').IsChecked(n)):
                        pmu.refresh = 1
                pmu.Save()
            
            self.GetParent().EndModal(1)
            event.Skip()
    
    def OnDelete(self, event):
        pmid = self.pm.id
        if pmid is None: return
        n = aw.awu.MsgDialog(self, "Elimino il promemoria?",
                             style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if n == wx.ID_YES:
            self.pm.Delete()
            self.pm.Save()
            de = PromemDeletedEvent(evt_PROMEMDELETED, self.GetId())
            de.SetEventObject(self)
            de.SetId(pmid)
            self.GetEventHandler().AddPendingEvent(de)
            self.GetParent().EndModal(1)
    
    def CtrFields(self):
        cn = lambda x: self.FindWindowByName(x)
        err = None
        mand = (('oggetto', "Specificare l'oggetto"),)
        for name, msg in mand:
            if not cn(name).GetValue():
                err = msg
                break
        if not err:
            if not cn('globale').GetValue():
                if len(cn('utenti').GetSelections()) == 0:
                    err = "Specificare gli utenti interessati"
        if err:
            aw.awu.MsgDialog(self, message=err)
        return not err


# ------------------------------------------------------------------------------


class PromemDataDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        self.pmpanel = PromemDataPanel(self, -1)
        self.AddSizedPanel(self.pmpanel)

    def SetPromemId(self, *args, **kwarsg):
        self.pmpanel.SetPromemId(*args, **kwarsg)
        self.SetTitle("Visualizza promemoria")
    
    def SetPromemNew(self, *args, **kwargs):
        self.pmpanel.SetPromemNew(*args, **kwargs)
        self.SetTitle("Nuovo promemoria")


# ------------------------------------------------------------------------------


class PromemAlertPanel(wx.Panel):
    wdr_filler = wdr.PromemAlertFunc
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.pm = adb.DbTable(bt.TABNAME_PROMEM, "promem", writable=True)
        self.wdr_filler(self)
        cn = lambda x: self.FindWindowByName(x)
        cn('_rimanda').Bind(wx.EVT_BUTTON, self.OnRimanda)
        cn('_finito').Bind(wx.EVT_BUTTON, self.OnFinito)
        cn('_tempo').Bind(wx.EVT_CHOICE, self.OnTempo)
        cn('_modifica').Bind(wx.EVT_BUTTON, self.OnModifica)
        cn('_tempo').SetSelection(0)
        self.Bind(EVT_PROMEMDELETED, self.OnPromemDeleted)
    
    def OnPromemDeleted(self, event):
        self.Close()
        event.Skip()
    
    def SetPromemId(self, pmid):
        pm = self.pm
        pm.Get(pmid)
        cn = lambda x: self.FindWindowByName(x)
        for name in 'oggetto,descriz'.split(','):
            cn(name).SetLabel(self.pm.__getattr__(name))
        color = wx.BLACK
        if pm.datasca:
            now = adb.DateTime.now()
            if pm.datasca < now:
                scad = 'scaduto da '
                diff = now-pm.datasca
                color = wx.RED
            else:
                scad = 'scade tra '
                diff = pm.datasca-now
            d = diff.days
            h = diff.seconds/3600
            m = diff.seconds/60
            if d == 0 and h == 0 and m == 0:
                scad = "scade ora"
            else:
                sc = []
                if  d == 1: sc.append('1 giorno')
                elif d > 0: sc.append('%d giorni' % d)
                if  h == 1: sc.append('1 ora')
                elif h > 0: sc.append('%d ore' % h)
                if  m == 1: sc.append('1 minuto')
                elif m > 0: sc.append('%d minuti' % m)
                scad += ' '+', '.join(sc)
        else:
            scad = "nessuna scadenza"
        scad = "(%s)" % scad
        cn('_scadenza').SetLabel(scad)
        cn('_scadenza').SetForegroundColour(color)
        self.SetNewDate()
    
    def SetNewDate(self):
        cn = lambda x: self.FindWindowByName(x)
        n = cn('_tempo').GetSelection()
        d, h, m = ((0,  0,  1),    #1 minuto
                   (0,  0,  5),    #5 minuti
                   (0,  0, 10),    #10 minuti
                   (0,  0, 15),    #15 minuti
                   (0,  0, 30),    #30 minuti
                   (0,  1,  0),    #1 ora
                   (0,  2,  0),    #2 ore
                   (0,  3,  0),    #3 ore
                   (0,  4,  0),    #4 ore
                   (0,  6,  0),    #6 ore
                   (0, 12,  0),    #12 ore
                   (1,  0,  0),    #1 giorno
                   (2,  0,  0))[n] #2 giorni
        newdat = adb.DateTime.now()+adb.DateTime.DateTimeDelta(d, 0, 0, 0, m, h)
        cn('datarem').SetValue(newdat)
        self.pm.datarem = newdat
    
    def OnTempo(self, event):
        self.SetNewDate()
        event.Skip()
    
    def OnModifica(self, event):
        f = PromemDataDialog(self)
        f.SetPromemId(self.pm.id)
        pop = (f.ShowModal() == 1)
        f.Destroy()
        if pop:
            tlw = wx.GetApp().GetTopWindow()
            if hasattr(tlw, 'promem'):
                tlw.promem.populate()
        self.Close()
        self.GetParent().Close()
    
    def OnRimanda(self, event):
        self.pm.Save()
        self.GetParent().Close()
    
    def OnFinito(self, event):
        self.pm.status = 1
        self.pm.Save()
        self.GetParent().Close()
    

# ------------------------------------------------------------------------------


class PromemAlertFrame(aw.Frame):
    def __init__(self, parent):
        aw.Frame.__init__(self, parent, -1, "Promemoria", pos=wx.DefaultPosition,
                          style=wx.CAPTION|wx.STAY_ON_TOP
                          |wx.THICK_FRAME|wx.SYSTEM_MENU
                          |wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.ap = PromemAlertPanel(self, -1)
        self.AddSizedPanel(self.ap)
        #icon = wx.EmptyIcon()
        #icon.CopyFromBitmap(images.getIconChildBitmap())
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def SetPromemId(self, *args, **kwargs):
        return self.ap.SetPromemId(*args, **kwargs)
    
    def OnClose(self, event):
        ce = ReminderClosedEvent(evt_REMINDERCLOSED, self.GetId())
        ce.SetEventObject(self)
        ce.SetId(self.ap.pm.id)
        self.GetEventHandler().AddPendingEvent(ce)
        event.Skip()
