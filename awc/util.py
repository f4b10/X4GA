#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/util.py
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


def mese(n):
    out = None
    if 1 <= n <= 12:
        out = ['gennaio',
               'febbraio',
               'marzo',
               'aprile',
               'maggio',
               'giugno',
               'luglio',
               'agosto',
               'settembre',
               'ottobre',
               'novembre',
               'dicembre'][n-1]
    return out


# ------------------------------------------------------------------------------


def iif(cond, val1, val2):
    """
    Espressione condizionale: se il primo argomento è vero, viene restituito 
    il secondo; altrimenti il terzo.
    
    @param cond: espressione logica in base alla quale scegliere il valore
    @type cond: bool
    @param val1: valore da ritornare in caso di C{cond == True}
    @param val2: valore da ritornare in caso di C{cond == False}
    """
    if cond:
        out = val1
    else:
        out = val2
    return out


# ------------------------------------------------------------------------------


def GetNamedChildrens(container, names=None, Test=None):
    """
    Esamina tutta la discendenza di figli di C{container} e ritorna una
    lista dei controlli.  Se C{names} è definito vengono esaminati solo
    i controlli i cui nomi siano compresi in tale lista.
    
    @param container: contenitore da esaminare
    @type container: L{wx.Window}
    @param names: lista nomi da testare
    @type names: lista di stringhe
    
    @return: lista di controlli
    @rtype: list
    """
    if Test is None:
        Test = lambda c: True
    childrens = container.GetChildren()
    namedlist = [ child for child in childrens\
                  if len(child.GetName())>0\
                  and (not names or child.GetName() in names)\
                  and Test(child)]
    for child in childrens:
        namedlist += GetNamedChildrens(child, names, Test)
    return namedlist


# ------------------------------------------------------------------------------


def GetAllChildrens(container, Test=None):
    """
    Esamina tutta la discendenza di figli di C{container} e ritorna una
    lista dei controlli.
    
    @param container: contenitore da esaminare
    @type container: L{wx.Window}
    
    @return: lista di controlli
    @rtype: list
    """
    if Test is None:
        Test = lambda c: True
    childrens = container.GetChildren()
    namedlist = [child for child in childrens if Test(child)]
    for child in childrens:
        namedlist += GetNamedChildrens(child, Test=Test)
    return namedlist


# ------------------------------------------------------------------------------


def EnableControls(parent, enable):
    def Enable(ctrl):
        from awc.controls.dbgrid import DbGrid
        from awc.controls.linktable import LinkTable
        if isinstance(ctrl, DbGrid):
            ctrl.EnableEditing(enable)
#        elif isinstance(ctrl, (wx.TextCtrl, wx.Button, LinkTable)):
        elif not isinstance(ctrl, (wx.Panel, wx.BookCtrlBase)):
            ctrl.Enable(enable)
    map(Enable, GetAllChildrens(parent))


# ------------------------------------------------------------------------------


def DictNamedChildrens( container, names = None ):
    """
    Esamina tutta la discendenza di figli di C{container} e ritorna un
    dizionario nel quale la chiave è il nome del controllo ed il valore
    è il controllo stesso.  Se C{names} è definito vengono esaminati solo
    i controlli i cui nomi siano compresi in tale lista.
    
    @param container: contenitore da esaminare
    @type container: L{wx.Window}
    @param names: lista nomi da testare
    @type names: lista di stringhe
    
    @return: dizionario di controlli
    @rtype: dict
    """
    d = {}
    ctrls = GetNamedChildrens(container, names)
    for ctrl in ctrls:
        d[ctrl.GetName().lower()] = ctrl
    return d


# ------------------------------------------------------------------------------


def MsgDialog( window, message = "Messaggio",
               caption = "X4",
               style = wx.ICON_WARNING ):
    """
    Visualizza un messaggio in un dialog modale e lo distrugge.
    Costanti per bottoni di scelta::
        wx.OK
        wx.CANCEL
        wx.YES_NO
        wx.YES_DEFAULT
        wx.NO_DEFAULT
        
    Costanti per tipo di icona:
        wx.ICON_EXCLAMATION
        wx.ICON_HAND
        wx.ICON_ERROR
        wx.ICON_QUESTION
        wx.ICON_INFORMATION
    
    @param window: Window da cui parte la richiesta del messaggio
    @type window: wx.Window
    @param caption: Titolo della finestra
    @type caption: String (Default = "X4 - Comunicazione")
    @param message: Messaggio da visualizzare
    @type message: String (Default = "Messaggio")
    @param style: Tipo di icona da visualizzare accanto al messaggio.
    @type style: int (Default = wx.ICON_WARNING)
    """
    dlg = wx.MessageDialog( parent = window,
                            caption = caption,
                            message = message,
                            style = style )
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret


# ------------------------------------------------------------------------------


def MsgDialogDbError( window, err, 
                      message = "",
                      caption = "X4 - Messaggio dal DataBase Server",
                      style = wx.ICON_WARNING ):
    """
    Visualizza un messaggio di segnalazione di problema sul db server.
    
    @param errcode: Codice di errore ritornato dal db server
    @type errcode: int
    @param errmsg: Messaggio di errore ritornato dal db server
    @type errmsg: String
    @param caption: Titolo della finestra
    @type caption: String (Default = "X4 - Messaggio dal DataBase Server")
    @param message: Messaggio da visualizzare
    @type message: String (Default: formattazione automatica cod/desc errore)
    @param style: Tipo di icona da visualizzare accanto al messaggio.
    @type style: int (Default = wx.ICON_WARNING)
    """
    if len(err.args) == 2:
        errcode = err.args[0]
        errmsg = err.args[1]
    else:
        errcode = 0
        errmsg = err.args[0]
    
    if message:
        message += "\n\n"
    message +=\
"""Durante l'elaborazione dei dati, si è verificato un problema; il """\
"""database server ha riscontrato l'errore #%d: %s""" % ( errcode, errmsg )
    
    return MsgDialog(window, message = message)


# ------------------------------------------------------------------------------


def AskForDeletion( parent,\
                    message = "Confermi la cancellazione dell'elemento?",\
                    caption = "X4 :: Richiesta di conferma",\
                    style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT ):
    x = MsgDialog( parent, message, caption, style )
    return ( x == wx.ID_YES )
    

# ------------------------------------------------------------------------------


def ListSearch( l, srcf):
    """
    Cerca un elemento in una lista in base ad una funzione di ricerca.
    Esempio:
        C{ListSearch( lista, lambda x: x[1]>0 and x[2]<100 )}
    """
    for i in range(len(l)):
        if srcf(l[i]):
            return i
    raise IndexError, "Il valore specificato da %s non è stato trovato"\
                      % srcf


# ------------------------------------------------------------------------------


def GetParentFrame(win):
    """
    Ricerca il frame/dialog di appartenenza del controllo passato.
    """
    while True:
        win = win.GetParent()
        if win != None and isinstance(win, (wx.Frame, wx.Dialog)):
            break
    return win


# ------------------------------------------------------------------------------


import awc.util_wdr as wdr

_evtWAITBREAK = wx.NewEventType()
EVT_WAITBREAK = wx.PyEventBinder(_evtWAITBREAK, 1)
class WaitBreakEvent(wx.PyCommandEvent):
    pass


class WaitDialog(wx.Dialog):
    """
    Visualizza un Dialog di elaborazione in corso.
    """
    def __init__(self, parent,
                 title="Attendere prego...",
                 message="Elaborazione dati in corso.",
                 style=0,#wx.STAY_ON_TOP,
                 dataread=False,
                 datawrite=False,
                 maximum=None,
                 canbreak=False,
                 progress2=False,
                 **kwargs):
        """
        title     = Titolo    (Attendere prego...)
        message   = Messaggio (Elaborazione dati in corso)
        style     = stile window (default: STAY_ON_TOP)
        dataread  = flag x messaggio automatico "Estrazione dati in corso"
        datawrite = flag x messaggio automatico "Aggiornamento dati in corso"
        maximum   = limite massimo x barra progresso
        canbreak  = flag x visualizzazione bottone "Interrompi"
        """
        
        wx.Dialog.__init__(self, parent, -1, style=style, **kwargs)
        wdr.WorkInProgressFunc(self)
        
        if not message:
            if   dataread:  message = "Estrazione dati in corso"
            elif datawrite: message = "Aggiornamento dati in corso"
        
        if not progress2:
            self.FindWindowByName('message2').Hide()
            self.FindWindowByName('progress2').Hide()
        
        self.SetTitle(title)
        self.SetMessage(message)
        
        p = self.FindWindowById(wdr.ID_PROGRESS)
        if maximum is None:
            p.Show(False)
        else:
            p.SetRange(maximum)
        self.progress = p
        self.progress2 = self.FindWindowById(wdr.ID_PROGRESS2)
        
        b = self.FindWindowById(wdr.ID_BTNBREAK)
        if canbreak:
            self.Bind(wx.EVT_BUTTON, self.OnButtonBreak, id=wdr.ID_BTNBREAK)
        else:
            b.Show(False)
        
        self.Fit()
        self.CenterOnScreen()
        self.Show()
        self._Update()
    
    def SetButtonBreakEnable(self, enable):
        self.FindWindowById(wdr.ID_BTNBREAK).Enable(enable)
    
    def OnButtonBreak(self, event):
        evt = WaitBreakEvent(_evtWAITBREAK, self.GetId())
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        self.GetEventHandler().ProcessEvent(evt)
        #self.GetEventHandler().AddPendingEvent(evt)
        event.Skip()
    
    def SetTitle(self, title):
        self.FindWindowById(wdr.ID_TITLE).SetLabel(title)
    
    def SetMessage(self, msg):
        p = self.FindWindowById(wdr.ID_PROGRESS)
        m = self.FindWindowById(wdr.ID_MESSAGE)
        w = p.GetSize()[0]
        m.SetLabel(msg or '')
        m.Wrap(w)
        self._Update()
    
    def SetRange(self, range):
        self.progress.SetRange(range)
        self._Update()
    
    def GetValue(self):
        return self.progress.GetValue()
    
    def SetValue(self, value):
        self.progress.SetValue(value)
        self._Update()
        return True
    
    def SetMessage2(self, msg):
        p = self.FindWindowById(wdr.ID_PROGRESS2)
        m = self.FindWindowById(wdr.ID_MESSAGE2)
        w = p.GetSize()[0]
        m.SetLabel(msg or '')
        m.Wrap(w)
        self._Update()
    
    def SetRange2(self, range):
        self.progress2.SetRange(range)
        self._Update()
    
    def GetValue2(self):
        return self.progress2.GetValue()
    
    def SetValue2(self, value):
        self.progress2.SetValue(value)
        self._Update()
        return True
    
    def _Update(self):
        if wx.Platform == '__WXMSW__':
            try:
                wx.SafeYield(onlyIfNeeded=True)
            except:
                pass
        else:
            wx.Yield()


# ------------------------------------------------------------------------------


class TimedPopupMessageFrame(wx.Frame):
    
    class TimedPopupMessagePanel(wx.Panel):
        def __init__(self, parent, message, text_color):
            wx.Panel.__init__(self, parent)
            s = wx.BoxSizer(wx.VERTICAL)
            m = wx.StaticText(self, -1, message)
            m.SetForegroundColour(text_color)
            s.Add(m, 0, wx.ALIGN_CENTER|wx.ALL, 5)
            self.SetSizer(s)
            s.SetSizeHints(self)
    
    def __init__(self, parent=None, message='Messaggio', seconds=1, text_color='blue'):
        wx.Frame.__init__(self, parent, style=wx.SIMPLE_BORDER|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP)
        self.panel = self.TimedPopupMessagePanel(self, message, text_color)
        self.Fit()
        self.CenterOnScreen()
        self.Show()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(seconds*1000, oneShot=True)

    def OnTimer(self, evt):
        if self.GetParent():
            self.GetParent().RemoveChild(self)
        self.Close()


# ------------------------------------------------------------------------------


def wp(x):
    return str(x).replace('/', '\\')


# ------------------------------------------------------------------------------


def up(x):
    return str(x).replace('\\', '/')


# ------------------------------------------------------------------------------


def sp(x):
    if sys.platform == 'win32':
        _p = wp
    else:
        _p = up
    return _p(x)


# ------------------------------------------------------------------------------


def ExpandPath(p):
    
    upp = sp(os.getenv("USERPROFILE"))
    if p.lower().startswith('%userprofile%'):
        p = p.replace('%userprofile%', '')
        if p and (p[0] or ' ') in '\\/':
            p = p[1:]
        p = os.path.join(upp, p)
    
    aup = sp(os.getenv("ALLUSERSPROFILE"))
    if p.lower().startswith('%allusersprofile%'):
        p = p.replace('%allusersprofile%', '')
        if p and (p[0] or ' ') in '\\/':
            p = p[1:]
        p = os.path.join(aup, p)
    
    return os.path.abspath(p)


# ------------------------------------------------------------------------------


def ReducePath(p):
    
    upp = sp(os.getenv("USERPROFILE"))
    if p.startswith(upp):
        p = p.replace(upp, '%userprofile%')
    
    aup = sp(os.getenv("ALLUSERSPROFILE"))
    if p.startswith(aup):
        p = p.replace(aup, '%allusersprofile%')
    
    return p


# ------------------------------------------------------------------------------


class LimitiFiltersMixin(object):
    
    limseq = None
    
    def __init__(self):
        assert isinstance(self, (wx.Panel, wx.Frame, wx.Dialog))
        self.limseq = []
        from awc.controls.linktable import EVT_LINKTABCHANGED
        self.Bind(EVT_LINKTABCHANGED, self.OnLimitiFiltersChanged)
    
    def OnLimitiFiltersChanged(self, event):
        event.Skip()
        if hasattr(self, 'adjustfilters'):
            return
        self.adjustfilters = True
        ctr = event.GetEventObject()
        name = ctr.GetName()
        if name.endswith('1'):
            ctr2 = self.FindWindowByName(name[:-1]+'2')
            if ctr2:
                val = ctr.GetValue()
                if val is None:
                    ctr2.SetFilter('1')
                else:
                    if hasattr(ctr2, 'filter_by_descriz'):
                        ctr2.SetFilter('%s.descriz>="%s"' % (ctr2.db_alias,
                                                             ctr.GetValueDes().replace('"', '')))
                    else:
                        ctr2.SetFilter('%s.codice>="%s"' % (ctr2.db_alias,
                                                            ctr.GetValueCod().replace('"', '')))
                if ctr2.GetValue() is None:
                    ctr2.SetValue(val)
                elif ctr2.iderror:
                    ctr2.SetValue(None)
        elif name.endswith('2'):
            ctr1 = self.FindWindowByName(name[:-1]+'1')
            if ctr1:
                val = ctr.GetValue()
        def delflag(obj):
            del obj.adjustfilters
        wx.CallAfter(delflag, self)
    
    def OnLimitiFiltersReset(self, event):

        for c in GetAllChildrens(self):
            if (c.GetName()[-1] or ' ') in '12':
                if hasattr(c, 'SetValue'):
                    c.SetValue(None)
    
    def AddLimitiFiltersSequence(self, table, alias, column):
        def cn(x):
            return self.FindWindowByName(x)
        self.limseq.append([table, alias, column, cn(column+'1'), cn(column+'2')])
    
    def LimitiFiltersApply(self, root=None):
        from awc.controls.linktable import LinkTable
        for table, alias, column, ctrl1, ctrl2 in self.limseq:
            if isinstance(ctrl1, LinkTable):
                if hasattr(ctrl1, 'filter_by_descriz'):
                    v1, v2 = ctrl1.GetValueDes(), ctrl2.GetValueDes()
                    field = 'descriz'
                else:
                    v1, v2 = ctrl1.GetValueCod(), ctrl2.GetValueCod()
                    field = 'codice'
            else:
                v1, v2 = ctrl1.GetValue(), ctrl2.GetValue()
                field = column
            if v1 or v2:
                if root is not None:
                    table = root
                if v1 == v2:
                    table.AddFilter("%s.%s=%%s" % (alias, field), v1)
                elif v1 and v2:
                    table.AddFilter("%s.%s>=%%s AND %s.%s<=%%s" % (alias, field, alias, field), v1, v2)
                elif v1:
                    table.AddFilter("%s.%s>=%%s" % (alias, field), v1)
                elif v2:
                    table.AddFilter("%s.%s<=%%s" % (alias, field), v2)
