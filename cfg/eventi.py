#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/eventi.py
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

import awc.layout.gestanag as ga
import cfg.eventi_wdr as wdr

import awc.controls.windows as aw
import awc.util as util

from Env import Azienda
bt = Azienda.BaseTab

import cfg.dbtables as dbcfg


FRAME_TITLE_TIPEVENT = "Tipi evento"


class TipiEventoPanel(ga.AnagPanel):
    
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup(bt.tabelle[bt.TABSETUP_TABLE_TIPEVENT])
        self.db_report = "Tipi evento"
    
    def InitAnagCard(self, parent):
        p = wx.Panel(parent, -1)
        wdr.TipiEventoCardFunc(p, True)
        return p
    

# ------------------------------------------------------------------------------


class TipiEventoFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Tipi evento.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_TIPEVENT
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TipiEventoPanel(self, -1))


# ------------------------------------------------------------------------------


class TipiEventoDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Tipi evento.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_TIPEVENT
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TipiEventoPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLE_MANAGER = "Event manager"


class EventManagerGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbevt):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbevt = dbevt
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        evt = dbevt
        tip = evt.tipevent
        
        _STR = gl.GRID_VALUE_STRING
        _DTT = gl.GRID_VALUE_DATETIME+":time"
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        
        cols = (\
            (140, (cn(evt, "data_evento"),    "Data",   _DTT, True)),
            ( 30, (cn(tip, "codice"),         "Cod.",   _STR, True)),
            (120, (cn(tip, "descriz"),        "Evento", _STR, True)),
            ( 40, (cn(evt, "notified_email"), "Mail",   _CHK, True)),
            ( 40, (cn(evt, "notified_xmpp"),  "XMPP",   _CHK, True)),
            (  1, (cn(evt, "id"),             "#evt",   _STR, True)),
            (  1, (cn(tip, "id"),             "#tpe",   _STR, True)),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(evt.GetRecordset(), colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class EventManagerPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.EventManagerFunc(self)
        self.dbevt = dbcfg.EventiTable()
        self.dbevt.ShowDialog(self)
        cn = self.FindWindowByName
        self.gridevt = EventManagerGrid(cn('pangridevent'), self.dbevt)
        for name, func in (('butupdate', self.OnUpdateData),
                           ('sendemailnow', self.OnSendEmailNow),
                           ('sendxmppnow', self.OnSendXmppNow),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnGridCellSelected)
    
    def OnSendEmailNow(self, event):
        if self.dbevt.Notify(owner=self, byemail=True, byxmpp=False):
            self.dbevt.Save()
            self.gridevt.Refresh()
            self.UpdateDetail()
        event.Skip()
    
    def OnSendXmppNow(self, event):
        if self.dbevt.Notify(owner=self, byemail=False, byxmpp=True):
            self.dbevt.Save()
            self.gridevt.Refresh()
            self.UpdateDetail()
        event.Skip()
    
    def OnGridCellSelected(self, event):
        self.dbevt.MoveRow(event.GetRow())
        self.UpdateDetail()
        event.Skip()
    
    def UpdateDetail(self):
        cn = self.FindWindowByName
        evt = self.dbevt
        enable_mail = enable_xmpp = True
        for ctrl in self.FindWindowByName('pandetails').GetChildren():
            name = ctrl.GetName()
            v = None
            if name == 'tipevent_code':
                v = evt.tipevent.codice
            elif name == 'tipevent_desc':
                v = evt.tipevent.descriz
            elif name == 'notifemail_yn':
                v = "NO SI".split()[bool(evt.tipevent.notify_emailto)]
            elif name == 'notifemail_status':
                if evt.notified_email == 1:
                    v = 'inviata'
                    if evt.notifieddemail:
                        v += ' il %s' % evt.notifieddemail.Format()
                    enable_mail = False
                else:
                    v = 'non inviata'
            elif name == 'notifxmpp_yn':
                v = "NO SI".split()[bool(evt.tipevent.notify_xmppto)]
            elif name == 'notifxmpp_status':
                if evt.notified_xmpp == 1:
                    v = 'inviata'
                    if evt.notifieddxmpp:
                        v += ' il %s' % evt.notifieddxmpp.Format()
                    enable_xmpp = False
                else:
                    v = 'non inviata'
            elif name in evt.GetFieldNames():
                v = getattr(evt, name)
            if v is not None:
                ctrl.SetValue(v)
        if bt.OPTNOTIFICHE:
            cn('sendemailnow').Enable(enable_mail)
            cn('sendxmppnow').Enable(enable_xmpp)
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        
        evt = self.dbevt
        evt.ClearFilters()
        
        cn = self.FindWindowByName
        
        for name, op in (('data1', '>='),
                         ('data2', '<='),):
            v = cn(name).GetValue()
            if v:
                evt.AddFilter("eventi.data_evento%s%%s" % op, v)
        
        tip = cn('id_tipevent').GetValue()
        if tip:
            evt.AddFilter("eventi.id_tipevent=%s", tip)
        
        mailsel, mailsey, mailsen = map(lambda x: cn(x).GetValue(), 
                                        'notifemail notifemailyes notifemailno'.split())
        if mailsel:
            evt.AddFilter("tipevent.notify_emailto<>''")
            if mailsey:
                evt.AddFilter("eventi.notified_email=1")
            elif mailsen:
                evt.AddFilter("eventi.notified_email=0 OR eventi.notified_email IS NULL")
        
        xmppsel, xmppsey, xmppsen = map(lambda x: cn(x).GetValue(), 
                                        'notifxmpp  notifxmppyes  notifxmppno'.split())
        if xmppsel:
            evt.AddFilter("tipevent.notify_xmppto<>''")
            if xmppsey:
                evt.AddFilter("eventi.notified_xmpp=1")
            elif xmppsen:
                evt.AddFilter("eventi.notified_xmpp=0 OR eventi.notified_xmpp IS NULL")
        
        evt.Retrieve()
        
        self.gridevt.ChangeData(evt.GetRecordset())


# ------------------------------------------------------------------------------


class EventManagerFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_MANAGER
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(EventManagerPanel(self))
        self.CenterOnScreen()
