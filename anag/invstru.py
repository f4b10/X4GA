#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         anag/invstru.py
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
import anag.prod_wdr as wdr

import stormdb as adb

import report as rpt


class InvStrutturaPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.InvStruFunc(self)
        
        self.dbstru = dba.InvStruttura()
        self.tree = None
        self.populate()
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_BUTTON, self.OnPrint, id=wdr.ID_PRINT)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnTest, self.tree)
    
    def OnTest(self, event):
        event.Skip()
    
    def OnPopulate(self, event):
        self.populate()
        event.Skip()
    
    def populate(self):
        
        wx.BeginBusyCursor()
        
        db = self.dbstru
        db.ClearFilters()
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
        
        root = tree.AddRoot("Inventario")
        tree.SetItemText(root, "", 1)
        tree.SetItemImage(root, fldridx, which = wx.TreeItemIcon_Normal)
        tree.SetItemImage(root, fldropenidx, which = wx.TreeItemIcon_Expanded)
        
        lastcat = lastgru = None
        treecat = treegru = None
        
        for pr in db:
            
            if pr.catart.id != lastcat or treecat is None:
                if pr.catart.codice is None:
                    catcod = '-'
                    catdes = 'non definito'
                else:
                    catcod = pr.catart.codice
                    catdes = pr.catart.descriz
                treecat = tree.AppendItem(root, catcod)
                tree.SetItemText(treecat, catdes, 1)
                tree.SetItemImage(treecat, fldridx, which = wx.TreeItemIcon_Normal)
                tree.SetItemImage(treecat, fldropenidx, which = wx.TreeItemIcon_Expanded)
                lastcat = pr.catart.id
                treegru = None
            
            if pr.gruart.id != lastgru or treegru is None:
                if pr.gruart.codice is None:
                    grucod = '-'
                    grudes = 'non definito'
                else:
                    grucod = pr.gruart.codice
                    grudes = pr.gruart.descriz
                treegru = tree.AppendItem(treecat, grucod)
                tree.SetItemText(treegru, grudes, 1)
                tree.SetItemImage(treegru, fldridx, which = wx.TreeItemIcon_Normal)
                tree.SetItemImage(treegru, fldropenidx, which = wx.TreeItemIcon_Expanded)
                lastgru = pr.gruart.id
            
            child = tree.AppendItem(treegru, pr.codice)
            tree.SetItemText(child, pr.descriz, 1)
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
        rpt.Report(self, self.dbstru, "Prodotti")
        event.Skip()


# ------------------------------------------------------------------------------


class InvStrutturaFrame(aw.Frame):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Struttura Inventario"
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(InvStrutturaPanel(self, -1))
