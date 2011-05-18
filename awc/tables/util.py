#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/tables/util.py
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
import sys

import MySQLdb

from Env import Azienda
import awc.tables.util_wdr as wdr

from awc.util import MsgDialog, MsgDialogDbError

base = Azienda.BaseTab

def CheckRefIntegrity(parent, db_curs, db_constr, rec_id):
    out = False
    try:
        ref = []
        for r_table, r_field, r_type in db_constr:
            if not r_type in (base.TABCONSTRAINT_TYPE_RESTRICT,
                              base.TABCONSTRAINT_TYPE_NOACTION,):
                continue
            cmd = "SELECT COUNT(1) FROM %s WHERE %s=%d;" % (r_table, r_field, rec_id)
            db_curs.execute(cmd)
            rs = db_curs.fetchone()
            if rs[0] > 0:
                try:
                    r_tabname = [ tb[base.TABSETUP_TABLEDESCRIPTION]\
                                for tb in Azienda.BaseTab.tabelle\
                                if tb[base.TABSETUP_TABLENAME] == r_table ][0]
                except:
                    r_tabname = r_table
                ref.append((r_table, r_tabname, r_field, rs[0]))
                
        if len(ref) == 0:
            out = True
        else:
            dlg = RefIntegrityDialog( parent, -1, "X4 :: Cancellazione impossibile" )
            dlg.ref = ref
            dlg.recid = rec_id
            dlg.db_curs = db_curs
            # creazione intestazioni
            lista = dlg.FindWindowById(wdr.ID_LISTREF)
            ncol = 0
            for listcol in 'Tabella Occorrenze'.split():
                info = wx.ListItem()
                info.m_mask = wx.LIST_MASK_TEXT
                info.m_text = listcol
                lista.InsertColumnInfo(ncol, info)
                ncol += 1
            #riepimento con riferimenti trovati
            wocc = 80
            w = lista.GetSizeTuple()[0]
            for tab, des, idf, tot in ref:
                index = lista.InsertStringItem( sys.maxint, "" )
                lista.SetStringItem( index, 0, des )
                lista.SetColumnWidth( 0, w-wocc )
                lista.SetStringItem( index, 1, "%d" % tot )
                lista.SetColumnWidth( 1, wocc )
            lista.SetItemState( 0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED )
            
            dlg.ShowModal()
            dlg.Destroy()
            
            out = False
            
    except MySQLdb.Error, e:
        MsgDialogDbError(None, e)
                
    return out


class RefIntegrityDialog(wx.Dialog):
    """
    Dialogo per la visualizzazione degli elementi in conflitto con la cancellazione
    per legami di integrità referenziale.
    """
    
    ref = ()
    recid = -1
    def __init__(self, parent, id, title,
                 pos = wx.DefaultPosition, size = wx.DefaultSize ):
        wx.Dialog.__init__(self, parent, id, title, pos, size)
        wdr.RefIntegrityFunc( self, True )
        wx.EVT_LIST_ITEM_SELECTED( self, wdr.ID_LISTREF, self.OnRefSelection )
        wx.EVT_BUTTON( self, wdr.ID_BTNCLOSE, self.OnCloseWindow )

    def OnRefSelection( self, event ):
        dett = self.FindWindowById(wdr.ID_LISTDET)
        n = self.FindWindowById(wdr.ID_LISTREF).GetSelectedItemCount()
        if n >= 1 and n <= len(self.ref):
            tab, _, idf, _ = self.ref[n-1]
            idr = self.recid
            try:
                cmd = "SELECT descriz FROM %s WHERE %s=%d ORDER BY descriz" % ( tab, idf, idr )
                self.db_curs.execute(cmd)
            except MySQLdb.Error:
                cmd = "SELECT * FROM %s WHERE %s=%d" % ( tab, idf, idr )
                self.db_curs.execute(cmd)
            rs = self.db_curs.fetchall()
            dett.Clear()
            for rec in rs:
                dett.Append(str(rec[0]))
    
    def OnCloseWindow( self, event ):
        self.EndModal(False)

def GetRecordInfo(curs, tab, id, columns):
    """
    Effettua la ricerca sulla tabella e con l'id indicati, e restituisce
    una lista contenente i valori delle colonne indicate.
    """
    info = [None for _ in range(len(columns))]
    if id is not None:
        cmd = "SELECT %s FROM %s WHERE id=%%s;"\
              % (",".join(columns), tab)
        try:
            nrec = curs.execute(cmd, id)
            if nrec == 0:
                MsgDialog(None,\
                          """Nessuna informazione trovata cercando """
                          """l'id %s sulla tabella '%s'"""\
                          % (id, tab), style = wx.ICON_EXCLAMATION )
            elif nrec == 1:
                rs = curs.fetchone()
                info = rs
        except MySQLdb.Error, e:
            MsgDialogDbError(None, e)
    return info
