#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/windows.py
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
def opj(x, y):
    return os.path.join(x, y).replace('\\', '/')

import re

import wx
from wx.lib.gestures import MouseGestures

import awc.util as awu
from awc.controls.mixin import ContainersMixin


TITLE_APPEND = None
def SetTitleAppend(s):
    global TITLE_APPEND
    o = TITLE_APPEND
    TITLE_APPEND = s
    return o


# ------------------------------------------------------------------------------


STD_ICON = None
def SetStandardIcon(icon):
    global STD_ICON
    STD_ICON = icon


# ------------------------------------------------------------------------------


def SetDefaultButton(frame, button):
    if sys.platform.startswith('linux'):
        if button is None:
            name = '_dummy_button_'
            b = frame.FindWindowByName(name)
            if b is None:
                b = wx.Button(frame, wx.NewId())
                b.SetName(name)
                b.Hide()
            b.SetDefault()
        else:
            button.SetDefault()
    else:
        for oldbutton in awu.GetNamedChildrens(frame, Test=lambda x: isinstance(x, wx.Button)):
            oldbutton.SetBackgroundColour(None)
        frame.SetDefaultItem(button)
        if button is not None:
            button.SetBackgroundColour('light blue')


# ------------------------------------------------------------------------------


_Button_SetDefault_Original = wx.Button.SetDefault
def _SetDefault(button):
    parent = button.GetParent()
    parent._default_item = button
    while not isinstance(parent, (wx.Frame, wx.Dialog)):
        parent = parent.GetParent()
    if sys.platform == 'win32':
        SetDefaultButton(parent, button)
    else:
        _Button_SetDefault_Original(button)
wx.Button.SetDefault = _SetDefault


# ------------------------------------------------------------------------------


def SetFocusedControl(control):
    parent = control
    defbut = None
    while not isinstance(parent, (wx.Frame, wx.Dialog)):
        parent = parent.GetParent()
        if hasattr(parent, '_default_item'):
            d = parent._default_item
            if d:
                defbut = d
                break
    SetDefaultButton(awu.GetParentFrame(control), defbut)
    

# ------------------------------------------------------------------------------


class mixin(ContainersMixin):
    """
    Mixin x Frame e Dialog.
    """
    helpbuilder_root = None
    def HelpBuilder_SetRoot(self, r):
        self.helpbuilder_root = r
    def HelpBuilder_GetRoot(self):
        return self.helpbuilder_root
    
    helpbuilder_helpdir = None
    def HelpBuilder_SetDir(self, hd):
        self.helpbuilder_helpdir = hd
    def HelpBuilder_GetDir(self):
        return self.helpbuilder_helpdir
    
    helpbuilder_forcemain = False
    def HelpBuilder_SetForceMain(self, force=True):
        self.helpbuilder_forcemain = force
    def HelpBuilder_GetForceMain(self):
        return self.helpbuilder_forcemain
    
    mindimx = None
    mindimy = None
    helpbuilder_object = None
    helpbuilder_hilite = False
    
    def __init__(self, title=None):
        ContainersMixin.__init__(self)
        if title:
            self.SetTitle(title)
        if STD_ICON:
            self.SetIcon(STD_ICON)
    
    def HelpBuilder_Enable(self):
        self.helpbuilder_hilite = True
        self.HelpBuilder_Check()
    
    def HelpBuilder_Disable(self):
        self.helpbuilder_hilite = False
        self.HelpBuilder_Check()
    
    def HelpBuilder_Switch(self):
        self.helpbuilder_hilite = not self.helpbuilder_hilite
        self.HelpBuilder_Check()
    
    def HelpBuilder_Check(self):
        if self.helpbuilder_hilite:
            t = 240
        else:
            t = 255
        self.SetTransparent(t)
        import awc.controls.dbgrid as dbglib
        for c in awu.GetAllChildrens(self):
            c.Bind(wx.EVT_ENTER_WINDOW, self.OnHelpBuilderMouseEnter)
            c.Bind(wx.EVT_LEAVE_WINDOW, self.OnHelpBuilderMouseLeave)
    
    def HelpBuilder_HiLiteObject(self, o):
        self.helpbuilder_object = o 
        o.Refresh()
        o.Update()
        w, h = o.GetSize()
        pdc = wx.ClientDC(o)
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        rect = wx.Rect(0,0, w, h)
        if self.HelpBuilder_IsObjectValidName(o):
            if os.path.exists(self.HelpBuilder_GetFileName(o)):
                r, g, b = (0, 128, 0)
            else:
                r, g, b = (0, 0, 255)
        else:
            r, g, b = (205, 92, 92)
        penclr = wx.Colour(r, g, b, wx.ALPHA_OPAQUE)
        brushclr = wx.Colour(r, g, b, 128)   # half transparent
        dc.SetPen(wx.Pen(penclr))
        dc.SetBrush(wx.Brush(brushclr))
        rect.SetPosition((0,0))
        dc.DrawRoundedRectangleRect(rect, 4)
        #print "%s__%s" % (self.__class__, o.GetName())
    
    def HelpBuilder_IsObjectValidName(self, obj):
        return obj.GetName().lower() not in 'panel,sizedpanel,statictext,staticbitmap,grid window'.split(',')
        
    def OnHelpBuilderMouseEnter(self, event):
        if self.helpbuilder_hilite:
            #attivo gestures
            def ActivateGesture(obj):
                if hasattr(self, 'mgest'):
                    while self.mgest.gestures:
                        g = self.mgest.gestures[-1]
                        self.mgest.RemoveGesture(g)
                    del self.mgest
                self.mgest = MouseGestures(obj, Auto=True,
                                           MouseButton=wx.MOUSE_BTN_MIDDLE)
                self.mgest.SetGesturesVisible(True)
                self.mgest.AddGesture('LR', self.HelpBuilder_RunEditor, obj, True)
                self.mgest.AddGesture('RL', self.HelpBuilder_RunEditor, obj)
            obj = event.GetEventObject()
            wx.CallAfter(self.HelpBuilder_HiLiteObject, obj)
            wx.CallAfter(ActivateGesture, obj)
            obj._oldtip = obj.GetToolTip()
            name = obj.GetName()
            import awc.controls.linktable as linktable
            try:
                if isinstance(obj.GetParent().GetParent(), linktable.LinkTable):
                    name = obj.GetParent().GetParent().GetName()
            except:
                pass
            t = 'name=%s, file=%s' % (name, self.HelpBuilder_GetFileName(obj))
            obj.SetToolTipString(t)
        event.Skip()
    
    def OnHelpBuilderMouseLeave(self, event):
        if self.helpbuilder_hilite:
            o = event.GetEventObject()
            if hasattr(o, '_oldtip'):
                o.SetToolTip(o._oldtip)
                del o._oldtip
            o.Refresh()
            o.Update()
        event.Skip()
    
    def HelpBuilder_RunEditor(self, obj, edit=False):
        if not self.HelpBuilder_IsObjectValidName(obj):
            awu.MsgDialog(self, "Il nome dell'elemento non è valido, in quanto generico (%s)" % obj.GetName())
            return
        self.HelpBuilder_LoadObjectHelp(obj, init=True)
        filename = self.HelpBuilder_GetFileName(obj)
        afn = os.path.abspath(filename)
        if edit:
            os.spawnl(os.P_NOWAIT, 'C:\\KompoZer 0.7.10\\kompozer.exe', '"%s"'%afn, '"%s"'%afn)
        else:
            HelpBuilder_ShowHelp(afn)
    
    def HelpBuilder_LoadObjectHelp(self, obj, init=False, links2exclude=None):
        html = None
        filename = self.HelpBuilder_GetFileName(obj, createdirs=init)
        if os.path.exists(filename):
            h = open(filename)
            html = h.read()
            h.close()
        elif init:
            html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<style media="all" type="text/css">@import "style.css";</style>
<meta content="text/html; charset=UTF-8"
http-equiv="content-type" />
<title>Manuale X4</title>
</head>
<body>
<br />
</body>
</html>"""
            h = open(filename, 'w')
            h.write(html)
            h.close()
        return html
    
    def HelpBuilder_GetFileName(self, obj=None, createdirs=False):
        
        from awc.layout.helpsys import GetHelpRoot
        
        rootdir = ''
        name = None
        
        def MakeDir(spath):
            rootdir = ''
            for path in ('%s.%s' % (GetHelpRoot(), spath)).split('.'):
                rootdir = opj(rootdir, path)
                if createdirs and not os.path.exists(rootdir):
                    os.mkdir(rootdir)
            return rootdir
        
        if obj is not None:
            p = obj
            while True:
                try:
                    rd = p.HelpBuilder_GetDir()
                    if rd:
                        rootdir = MakeDir(rd)
                        try:
                            if obj.HelpBuilder_GetForceMain(): 
                                name = 'main'
                        except:
                            pass
                        break
                except AttributeError:
                    pass
                p = p.GetParent()
                if p is None or isinstance(p, (wx.Frame, wx.Dialog)):
                    break
        
        if not rootdir:
            try:
                p = '%s_%s' % (self.__module__, self.__class__.__name__)
                for x in 'Dialog Frame'.split():
                    p = p.replace(x, '') 
                rootdir = MakeDir(p)
            except Exception, e:
                import awc.util as awu
                awu.MsgDialog(self, repr(e.args))
                return None
        
        if name is None:
            if obj is not None and obj is not self.HelpBuilder_GetRoot():
                name = obj.GetName()
                try:
                    import awc.controls.linktable as linktable
                    cp = obj.GetParent().GetParent()
                    if isinstance(cp, linktable.LinkTable):
                        name = cp.GetName()
                except:
                    pass
        
        if name is None:
            name = 'main'
        
        if '#' in name:
            name = name[:name.index('#')]
        
        return '%s.html' % opj(rootdir, name)
            
    def HelpBuilder_GetFilePath(self, *args, **kwargs):
        fn = self.HelpBuilder_GetFileName(*args, **kwargs)
        return os.path.split(fn)[0]
        
    def HelpBuilder_FindObjectHelp(self, obj):
        o = obj
        while True:
            fn = self.HelpBuilder_GetFileName(o)
            if os.path.exists(fn):
                return fn
            o = o.GetParent()
            if o is None or isinstance(o, (wx.Frame, wx.Dialog)):
                break
        return None
    
    def HelpBuilder_ShowObjectHelp(self, obj):
        fn = self.HelpBuilder_FindObjectHelp(obj)
        if fn is not None:
            HelpBuilder_ShowHelp(fn, parent=awu.GetParentFrame(obj))
    
    def AddSizedPanel(self, panel, name='sizedpanel'):
        """
        Aggiunge (al Dialog o Frame) il Panel passato, creando automaticamente
        un Sizer di tipo griglia impostato con un'unica colonna che provvede
        a rempostare automaticamente la grandezza del Panel (e di tutti i
        controlli ivi contenuti) a seconda del dimensionamento del Dialog/Frame.
        """
        sizer = wx.FlexGridSizer(0, 1, 0, 0)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        sizer.Add(panel, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        if panel.GetName() == 'panel':
            panel.SetName(name)
        self.HelpBuilder_SetRoot(panel)
        return sizer
    
    def __StandardTitle__(self, title):
        """
        Aggiunge sempre la descrizione dell'azienda in coda al titolo del
        Dialog/Frame.
        """
        if title is not None:
            if TITLE_APPEND is not None:
                title += " - %s" % TITLE_APPEND
        return title
    
    def SetMinHeight(self, my):
        self.mindimy = my
    
    def SetMinWidth(self, mw):
        self.mindimx = mw
    
    def CheckDimensions(self):
        sx, sy = self.GetSize()
        resize = False
        if self.mindimx is not None and sx < self.mindimx:
            sx = self.mindimx
            resize = True
        if self.mindimy is not None and sy < self.mindimy:
            sy = self.mindimy
            resize = True
        #if resize:
            #self.SetSize((sx, sy))
            #self.CenterOnScreen()
        mx, my = wx.GetDisplaySize()
        #if ((sx>=800 and sy>=550) or sy>=600) and (mx<=1024 or my<=768):
        if False:#float(sx)/float(mx)>.99 or float(sy)/float(my)>.99:
            if self.GetTitle():
                self.Maximize()
        if not self.IsMaximized():
            w, h = self.GetSize()
            x, y = self.GetPosition()
            c = False
            if w<mx:
                if w+x>mx:
                    x = mx-w
                    c = True
            if h<my:
                if y+h>my:
                    y = my-h
                    c = True
            if c:
                self.SetPosition((x, y))
    
    def GetAllChildren(self):
        return awu.GetAllChildrens(self)
    
    def _Layout(self):
        #la funzione layout su gtk non ridisegna sempre correttamente quanto dovuto
        #specialmente in caso di controlli che possono essere nascosti/visualizzati
        #al momento
        #questo workaround si basa sul cambiodi grandezza del container, casistica
        #che causa il corretto ridisegnamento
        s = self.GetSize()
        self.SetSize((s[0]+1, s[1]+1))
        wx.CallAfter(lambda: self.SetSize(s))


# ------------------------------------------------------------------------------


def HelpBuilder_ShowHelp(name, parent=None, addprefix=False):
    from awc.layout.helpsys import GetHelpRoot
    hr = GetHelpRoot()
    if addprefix and not name.startswith(hr):
        name = os.path.join(hr, name)
    if not name.lower().endswith('.html'):
        name += '.html'
    if os.path.exists(name):
        #os.startfile(os.path.abspath(name))
        from awc.layout.helpsys import HelpHtmlFrame
        title = '%s - Manuale Utente' % wx.GetApp().GetAppName()
        h = HelpHtmlFrame(parent, -1, title, filename=name)
        h.Show()


# ------------------------------------------------------------------------------


class Frame(wx.Frame, mixin):
    """
    Frame.
    """
    def __init__(self, parent=None, id=-1, title='',\
                 pos=wx.DefaultPosition, size=wx.DefaultSize,\
                 style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE|wx.TAB_TRAVERSAL,\
                 **kwargs):
        
        wx.Frame.__init__(self, parent, id, title, pos, size, style, **kwargs)
        
        if not title and 'title' in kwargs:
            title = kwargs.pop('title')
        mixin.__init__(self, title)
        wx.DEFAULT_FRAME_STYLE
        self.CheckDimensions()
    
    def SetTitle(self, title):
        wx.Frame.SetTitle(self, self.__StandardTitle__(title))
    
    def SetSize(self, *args, **kwargs):
        wx.Frame.SetSize(self, *args, **kwargs)
        self.CheckDimensions()
    
    def Show(self, *args, **kwargs):
        self.CheckDimensions()
        return wx.Frame.Show(self, *args, **kwargs)

# ------------------------------------------------------------------------------


class Dialog(wx.Dialog, mixin):
    """
    Dialog.
    """
    
    def __init__(self, parent=None, id=-1, title='',\
                 pos=wx.DefaultPosition, size=wx.DefaultSize,\
                 style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE,\
                 **kwargs):
        
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, **kwargs)
        
        if not title and 'title' in kwargs:
            title = kwargs.pop('title')
        mixin.__init__(self, title)
        
        self.SetReturnCode(-1)
        
        self.CheckDimensions()
        
        self.Bind(wx.EVT_CLOSE, self._OnQuit)
    
    def SetTitle(self, title):
        wx.Dialog.SetTitle(self, self.__StandardTitle__(title))
    
    def SetSize(self, *args, **kwargs):
        wx.Dialog.SetSize(self, *args, **kwargs)
        self.CheckDimensions()
    
    def Show(self, *args, **kwargs):
        self.CheckDimensions()
        return wx.Dialog.Show(self, *args, **kwargs)
    
    def ShowModal(self, *args, **kwargs):
        self.CheckDimensions()
        return wx.Dialog.ShowModal(self, *args, **kwargs)
    
    def _OnQuit(self, event):
        if self.IsModal():
            self.EndModal(-1)
        else:
            self.Destroy()
    

# ------------------------------------------------------------------------------


class AcceleratorKey(object):
    
    key = None         #tasto scorciatoia (lettera)
    control_id = None  #id del controllo (bottone) di cui il tasto è scorciatoia
    use_alt = False    #uso del tasto con il modificatore "Alt"
    use_ctrl = False   #uso del tasto con il modificatore "Ctrl"
    use_shift = False  #uso del tasto con il modificatore "Shift"
    label = None       #etichetta da rimpiazzare sul controllo (bottone) di cui il tasto è scorciatoia
    description = None #descrizione funzionalità, per tooltip e menu acceleratori attivi
    
    def __init__(self, key, control, label=None, description=None, use_alt=True, use_ctrl=False, use_shift=False):
        if hasattr(control, 'GetId'):
            control_id = control.GetId()
        else:
            control_id = control
        self.key = key
        self.control_id = control_id
        self.use_alt = use_alt
        self.use_ctrl = use_ctrl
        self.use_shift = use_shift
        self.description = description
        self.label = label

    
# ------------------------------------------------------------------------------


class Panel(wx.Panel, mixin):
    """
    Pannello.
    """
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name="panel"):                 
        style |= wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        self._default_item = None
        self._accelerators = {}
        self._accel_bindings = []
    
    def SetAcceleratorKey(self, *args, **kwargs):
        a = AcceleratorKey(*args, **kwargs)
        self._accelerators[a.key] = a
        self.BuildAcceleratorTable()
    
    def DelAcceleratorKey(self, key):
        if key in self._accelerators:
            del self._accelerators[key]
        self.BuildAcceleratorTable()
    
    def BuildAcceleratorTable(self):
        
        t = []
        for key in self._accelerators:
            
            a = self._accelerators[key]
            
            modifier = wx.ACCEL_NORMAL
            if a.use_alt:
                modifier |= wx.ACCEL_ALT
            if a.use_ctrl:
                modifier |= wx.ACCEL_CTRL
            if a.use_shift:
                modifier |= wx.ACCEL_SHIFT
            
            if type(a.key) is str:
                keyord = ord(a.key)
            else:
                keyord = key
            
            ctrl_id = a.control_id
            ctrl = self.FindWindowById(ctrl_id)
#            if ctrl is None:
#                raise Exception, "Control not found assigning accelerator key"
            t.append((modifier, keyord, ctrl_id))
            
            if a.label:
                l = a.label
                if a.use_alt:
                    if not key.lower() in l.lower():
                        l = '%s (%s)' % (l.replace('&', ''), key)
                    if key.lower() in l.lower():
                        n = l.lower().index(key.lower())
                        l = l[:n]+'&'+l[n:]
            else:
                l = ctrl.GetLabel()
            ctrl.SetLabel(l)
            
            if a.description:
                ks = ''
                if a.use_shift:
                    ks += 'Shift-'
                if a.use_alt:
                    ks += 'Alt-'
                if a.use_ctrl:
                    ks += 'Ctrl-'
                ks += a.key
                tt = '%s (%s)' % (a.description, ks)
                ctrl.SetToolTip(wx.ToolTip(tt))
            
            if not ctrl_id in self._accel_bindings:
                self.Bind(wx.EVT_BUTTON, self.OnAcceleratorKeyPressed, id=ctrl_id)
                self._accel_bindings.append(ctrl_id)
        
        self.SetAcceleratorTable(wx.AcceleratorTable(t))
    
    def OnAcceleratorKeyPressed(self, event):
        b = event.GetEventObject()
        if b is None:
            return
        b.SetForegroundColour('yellow')
        b.SetBackgroundColour('blue')
        wx.YieldIfNeeded()
        def RestoreColors():
            try:
                if awu.GetParentFrame(b).IsShown():
                    try:
                        b.SetForegroundColour(None)
                        b.SetBackgroundColour(None)
                        wx.YieldIfNeeded()
                    except:
                        pass
            except:
                pass
        wx.CallLater(44, RestoreColors)
        event.Skip()
    
    def SetDefaultItem(self, c):
        parent = self
        while not isinstance(self, wx.Panel):
            parent = parent.GetParent()
        parent._default_item = c
        f = awu.GetParentFrame(self)
        SetDefaultButton(f, c)
        #workaround su WXP non ridisegna il bottone con il bordo del bottone 
        #di default, fino a che esso non riceve il focus
        f = self.FindFocus()
        s = None
        if isinstance(f, wx.TextCtrl): 
            s = f.GetSelection()
        if s: 
            f.SetSelection(*s)
    
    def RefreshDefaultItem(self):
        f = awu.GetParentFrame(self)
        f.SetDefaultItem(f.GetDefaultItem())
    
    def Enable(self, *args, **kwargs):
        wx.Panel.Enable(self, *args, **kwargs)
        self.RefreshInsideDefaultItems()
    
    def Disable(self, *args, **kwargs):
        wx.Panel.Disable(self, *args, **kwargs)
        self.RefreshInsideDefaultItems()
    
    def RefreshInsideDefaultItems(self):
        for c in awu.GetAllChildrens(self):
            if hasattr(c, 'RefreshDefaultItem'):
                c.RefreshDefaultItem()
    
    def ValidateControls(self, controls):
        """
        Esamina la lista dei controlli passati.
        Per ognuno vailda il metodo Validate(); in caso di esito negativo,
        setta il colore di sfondo come COLOR_ERROR
        Ritorna True se tutti i controlli danno esito positivo.
        """
        
        valid = True
        
        for ctr in controls:
            if isinstance(ctr, wx.Window):
                v = ctr.Validate()
                if v:
                    ctr.SetBackgroundColour(wx.NullColour)
                else:
                    try:
                        ctr.SetBackgroundColour('red')
                    except:
                        pass
                    valid = False
        
        if not valid:
            awu.MsgDialog(self,\
                          """Sono presenti valori non validi.  Correggere le parti evidenziate """\
                          """per continuare.  I dati non sono stati salvati.""" )
        
        return valid
