#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/progrcon.py
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

import cfg.caucontab_wdr as wdr

import awc
import awc.util as awu

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import awc.controls.windows as aw

import stormdb as adb
import cfg.dbtables as dbc


FRAME_TITLE = "Progressivi contabili"


class ProgrStampaMastriGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbstm, **kwargs):
        
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size)
        
        self.dbstm = dbstm
        
        def cn(col):
            return dbstm._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            ( 35, (cn("keydiff"),   "Es.",       _STR, True)),
            ( 80, (cn("progrdate"), "St.Mastri", _DAT, True)),
            (  1, (cn("id"),        "#stm",      _STR, True)),
        )                            
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1,\
                       self.EditedValues), )
        
        self.SetData(dbstm.GetRecordset(), colmap, canedit, canins, 
                     afterEdit=afteredit)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr.SetReadOnly(col != 1)
        return attr
    
    def EditedValues(self, row, gridcol, col, value):
        p = self.dbstm
        p.MoveRow(row)
        if p.id is not None and not p.id in p._info.modifiedRecords:
            p._info.modifiedRecords.append(p.id)
        return True


# ------------------------------------------------------------------------------


class ProgrContabPanel(aw.Panel):
    """
    Gestione Progressivi contabili.
    """
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.ProgressiviFunc(self, True)
        
        self.dbprg = dbc.Progressivi()
        self.dbstm = dbc.ProgrStampaMastri()
        
        cn = self.FindWindowByName
        
        if not bt.CONSOVGES:
            cn('sovrapp').Hide()
        
        self.gridstm = ProgrStampaMastriGrid(cn('pangridstm'), self.dbstm)
        
        e = Env.Azienda.Esercizio
        
        self.keys = (#esercizio in corso e sovrapposizione attivata
                     ('ccg_esercizio',
                      {'progrnum':  'curreserc',     #esercizio in corso
                       'progrimp1': 'sovrapp',       #flag sovrapposizione attivata
                       'progrimp2': 'apechi_flag'}), #flag movimenti chiusura/apertura generati
                     
                     #progressivi giornale data/numero ultima reg. stampata
                     ('ccg_giobol',
                      {'progrdate': 'gioboldat',
                       'progrnum':  'giobolrig',
                       'progrimp1': 'giobolann',
                       'progrimp2': 'giobolpag',
                       'progrdesc': 'giobolint'}),
                     
                     #progressivi giornale dare/avere esercizio in corso
                     ('ccg_giobol_ec',
                      {'progrimp1': 'giobolecd',
                       'progrimp2': 'gioboleca'}),
                     
                     #progressivi giornale dare/avere esercizio precedente
                     ('ccg_giobol_ep',
                      {'progrimp1': 'giobolepd',
                       'progrimp2': 'giobolepa'}),
                     
                     #data ultimo aggiornamento contabile
                     ('ccg_aggcon',
                      {'progrdate': 'aggcon'}),
                     
                     #data movimenti apertura
                    ('ccg_apertura',
                      {'progrdate': 'apertura'}),
                     
                     #data movimenti chiusura
                     ('ccg_chiusura',
                      {'progrdate': 'chiusura'}),
                 )
        
        self.LoadData()
        
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_SAVE)
    
    def OnSave(self, event):
        if self.Validate():
            if self.SaveData():
                event.Skip()
    
    def Validate(self):
        return True
    
    def SaveData(self):
        def cn(x):
            return self.FindWindowByName(x)
        out = True
        dbc = self.dbprg
        keys = self.keys
        for key, p in keys:
            for name in p.keys():
                v = cn(p[name]).GetValue()
                if not dbc.SaveKey(key, dif='0', fields=(name,), values=(v,)):
                    awu.MsgDialog(self, message=repr(dbc.GetError()))
                    out = False
                    break
        self.dbstm.Save()
        import lib
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        return out
    
    def LoadData(self):
        def cn(x):
            return self.FindWindowByName(x)
        dbc = self.dbprg
        keys = self.keys
        for key, p in keys:
            for name in p.keys():
                v = dbc.ReadKey(key, dif='0', fields=name)
                if v:
                    cn(p[name]).SetValue(v[0])
        self.dbstm.CreaEserciziMancanti()
        self.gridstm.ChangeData(self.dbstm.GetRecordset())


# ------------------------------------------------------------------------------


class ProgrContabFrame(aw.Frame):
    """
    Frame Gestione Progressivi contabili.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProgrContabPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_SAVE)
    
    def OnSave(self, event):
        self.Close()
        event.Skip()


# ------------------------------------------------------------------------------


class ProgrContabDialog(aw.Dialog):
    """
    Dialog Gestione tabella Causali contabili.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProgrContabPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_SAVE)
    
    def OnSave(self, event):
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Close()
