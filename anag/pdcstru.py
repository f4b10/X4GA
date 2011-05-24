#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/pdcstru.py
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

import awc.controls.windows as aw
import anag.dbtables as dba
import anag.pdcrel_wdr as wdr

import stormdb as adb

import report as rpt


class PdcStrutturaPanel(aw.Panel):
    pdcstru = dba.PdcStruttura
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.PdcStruFunc(self)
        
        self.dbstru = self.pdcstru()
        self.tree = None
        self.populate()
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CHECKBOX, self.OnPopulate, id=wdr.ID_INCLCF)
        self.Bind(wx.EVT_BUTTON, self.OnPrint, id=wdr.ID_PRINT)
    
    def OnPopulate(self, event):
        self.populate()
        event.Skip()
    
    def populate(self):
        
        wx.BeginBusyCursor()
        
        db = self.dbstru
        db.ClearFilters()
        if not self.FindWindowById(wdr.ID_INCLCF).GetValue():
            db.AddFilter("NOT tipana.tipo IN ('C', 'F')")
        db.Retrieve()
        
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        
        if self.tree is None:
            pr = self.FindWindowById(wdr.ID_PANELSTRU)
            tree = gizmos.TreeListCtrl(pr, -1, style =
                                       wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT)
            tree.SetImageList(il)
            self.il = il
            tree.AddColumn("Codice")
            tree.AddColumn("Descrizione")
            tree.SetMainColumn(0) # the one with the tree in it...
            tree.SetColumnWidth(0, 175)
        else:
            tree = self.tree
        tree.DeleteAllItems()
        
        #tree.GetMainWindow().Bind(wx.EVT_LEFT_DCLICK, self.OnDblClick)
        
        root = tree.AddRoot("Sezione")
        tree.SetItemText(root, "", 1)
        tree.SetItemImage(root, fldridx, which = wx.TreeItemIcon_Normal)
        tree.SetItemImage(root, fldropenidx, which = wx.TreeItemIcon_Expanded)
        
        lasttip = lastmas = lastcon = None
        treetip = treemas = treecon = None
        
        for sc in db:
            
            if sc.bilmas.tipo != lasttip:
                treetip = tree.AppendItem(root, sc.bilmas.tipo)
                tree.SetItemText(treetip, sc.bilmas.GetSezione(), 1)
                tree.SetItemImage(treetip, fldridx, which = wx.TreeItemIcon_Normal)
                tree.SetItemImage(treetip, fldropenidx, which = wx.TreeItemIcon_Expanded)
                lasttip = sc.bilmas.tipo
            
            if sc.bilmas.id != lastmas:
                treemas = tree.AppendItem(treetip, sc.bilmas.codice)
                tree.SetItemText(treemas, sc.bilmas.descriz, 1)
                tree.SetItemImage(treemas, fldridx, which = wx.TreeItemIcon_Normal)
                tree.SetItemImage(treemas, fldropenidx, which = wx.TreeItemIcon_Expanded)
                lastmas = sc.bilmas.id
            
            if sc.bilcon.id != lastcon:
                treecon = tree.AppendItem(treemas, sc.bilcon.codice)
                tree.SetItemText(treecon, sc.bilcon.descriz, 1)
                tree.SetItemImage(treecon, fldridx, which = wx.TreeItemIcon_Normal)
                tree.SetItemImage(treecon, fldropenidx, which = wx.TreeItemIcon_Expanded)
                lastcon = sc.bilcon.id
            
            child = tree.AppendItem(treecon, sc.codice)
            tree.SetItemText(child, sc.descriz, 1)
            tree.SetItemImage(child, fldridx, which = wx.TreeItemIcon_Normal)
            tree.SetItemImage(child, fldropenidx, which = wx.TreeItemIcon_Expanded)
            last = child
        
        tree.Expand(root)
        
        self.dbstru = db
        self.tree = tree
        
        wx.EndBusyCursor()
        
        self._SetSize()

    def OnSize(self, evt):
        self._SetSize()
        evt.Skip()
        
    def _SetSize(self):
        self.tree.SetSize(self.tree.GetParent().GetClientSize())
        w = self.tree.GetSize()[0]
        w -= self.tree.GetColumnWidth(0)
        w -= 10
        if w>0: self.tree.SetColumnWidth(1, w)
    
    def OnPrint(self, event):
        rpt.Report(self, self.dbstru, "Piano dei Conti")
        event.Skip()


# ------------------------------------------------------------------------------


class PdcStrutturaFrame(aw.Frame):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Struttura P.d.C."
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(PdcStrutturaPanel(self, -1))


# ------------------------------------------------------------------------------


class PdcStrutturaRiclPanel(PdcStrutturaPanel):
    pdcstru = dba.PdcStrutturaRicl


# ------------------------------------------------------------------------------


class PdcStrutturaRiclFrame(aw.Frame):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Struttura P.d.C. Riclassificato"
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(PdcStrutturaRiclPanel(self, -1))
