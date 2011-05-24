#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/clienti.py
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
from awc.wxinit import TestInitialFrameSize

import awc.controls.dbgrid as dbglib
import wx.grid as gl

import MySQLdb

import awc.layout.gestanag as ga
import anag.pdcrel_wdr as wdr

import awc.controls.windows as aw
from awc.util import MsgDialog, MsgDialogDbError

from anag import pdcrel

from anag.catart import CatArtDialog

import Env
from awc.controls.linktable import EVT_LINKTABCHANGED
stdcolor = Env.Azienda.Colours

from Env import Azienda
bt = Azienda.BaseTab

import stormdb as adb
import anag.dbtables as dba

import report as rpt


FRAME_TITLE = "Clienti"


class ScontiCategoriaGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbscc):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.id_pdc = None
        
        self.dbscc = dbscc
        
        cols = self.GetColumnsStructure()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        links = []
        
        scc = self.dbscc
        pdc = scc.pdc
        cli = pdc.cliente
        cat = scc.catart
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        ltcat = dbglib.LinkTabAttr(bt.TABNAME_CATART,    #table
                                   0,                    #grid col
                                   cn(scc, 'id_catart'), #rs col id
                                   cn(cat, 'codice'),    #rs col cod
                                   cn(cat, 'descriz'),   #rs col des
                                   CatArtDialog)         #card class
        links.append(ltcat)
        
        afteredit = ((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.EditedValues),)
        
        self.SetData(dbscc.GetRecordset(), colmap, canEdit=True, canIns=True, 
                     linktables=links, newRowFunc=self.AddNewRow,
                     afterEdit=afteredit)
        
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
    
    def GetColumnsStructure(self):
        
        scc = self.dbscc
        pdc = scc.pdc
        cli = pdc.cliente
        cat = scc.catart
        
        _STR = gl.GRID_VALUE_STRING
        _SCO = bt.GetMagScoMaskInfo()
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        return (( 40, (cn(cat, "codice"),    "Cod.",      _STR, True)),
                (120, (cn(cat, "descriz"),   "Categoria", _STR, True)),
                ( 50, (cn(scc, "sconto1"),   "Sc.%1",     _SCO, True)),
                ( 50, (cn(scc, "sconto2"),   "Sc.%2",     _SCO, True)),
                ( 50, (cn(scc, "sconto3"),   "Sc.%3",     _SCO, True)),
                (  1, (cn(scc, "id"),        "#scc",      _STR, True)),
                (  1, (cn(scc, "id_pdc"),    "#pdc",      _STR, True)),
                (  1, (cn(scc, "id_catart"), "#cat",      _STR, True)),)
    
    def SetPdc(self, idpdc):
        self.id_pdc = idpdc
    
    def OnRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbscc.RowsCount():
            self.MenuPopup(event)
            event.Skip()
    
    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        self.SetGridCursor(row, col)
        self.SelectRow(row)
        scc = self.dbscc
        voci = []
        voci.append(("Scheda categoria", self.OnSchedaCatArt, True))
        voci.append(("Elimina sconto", self.OnDeleteRow, True))
        menu = wx.Menu()
        for text, func, enab in voci:
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        xo, yo = event.GetPosition()
        self.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()
    
    def OnDeleteRow(self, event):
        row = self.GetSelectedRows()[0]
        scc = self.dbscc
        if 0<=row<scc.RowsCount():
            scc.MoveRow(row)
            if scc.id is not None:
                scc._info.deletedRecords.append(scc.id)
                scc._info.recordNumber -= 1
                scc._info.recordCount -= 1
            self.DeleteRows(row)
        event.Skip()
    
    def AddNewRow(self):
        self.dbscc.CreateNewRow()
    
    def EditedValues(self, row, gridcol, col, value):
        scc = self.dbscc
        scc.MoveRow(row)
        scc.id_pdc = self.id_pdc
        return True
    
    def GetAttr(self, row, col, rscol, attr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        if row == self.dbscc.RowsCount():
            ro = col != 0
        else:
            ro = col == 1
        attr.SetReadOnly(ro)
        return attr
    
    def OnSchedaCatArt(self, event):
        row = self.GetSelectedRows()[0]
        if 0<=row<self.dbscc.RowsCount():
            self.dbscc.MoveRow(row)
            catid = self.dbscc.id_catart
            d = CatArtDialog(self, onecodeonly=catid)
            d.OneCardOnly(catid)
            d.ShowModal()
            d.Destroy()
        event.Skip()
    
    def UpdateGrid(self):
        self.ChangeData(self.dbmas.GetMastro().GetRecordset())


# ------------------------------------------------------------------------------


class ClientiPanel(pdcrel._CliForPanel):
    """
    Gestione della tabella clienti.
    """
    def __init__(self, *args, **kwargs):
        
        self.pdctipo = "C"
        self.tabanag = Azienda.BaseTab.TABNAME_CLIENTI
        pdcrel._CliForPanel.__init__(self, *args, **kwargs)
        
        self.anag_db_columns = [ c for c in Azienda.BaseTab.tabelle\
                                 [bt.TABSETUP_TABLE_CLIENTI]\
                                 [bt.TABSETUP_TABLESTRUCTURE] ]
        
        self._sqlrelfrm +=\
            " LEFT JOIN %s AS agente   ON anag.id_agente=agente.id"\
            " LEFT JOIN %s AS zona     ON anag.id_zona=zona.id"\
            " LEFT JOIN %s AS stato    ON anag.id_stato=stato.id"\
            " LEFT JOIN %s AS categ    ON anag.id_categ=categ.id"\
            " LEFT JOIN %s AS status   ON anag.id_status=status.id"\
            " LEFT JOIN %s AS modpag   ON anag.id_modpag=modpag.id"\
            " LEFT JOIN %s AS speinc   ON anag.id_speinc=speinc.id"\
            " LEFT JOIN %s AS travet   ON anag.id_travet=travet.id"\
            " LEFT JOIN %s AS tiplist  ON anag.id_tiplist=tiplist.id"\
            " LEFT JOIN %s AS aliqiva  ON anag.id_aliqiva=aliqiva.id"\
            " LEFT JOIN %s AS bancapag ON anag.id_bancapag=bancapag.id"\
            % (bt.TABNAME_AGENTI,                       
               bt.TABNAME_ZONE,
               'x4.stati',
               bt.TABNAME_CATCLI,
               bt.TABNAME_STATCLI,
               bt.TABNAME_MODPAG,
               bt.TABNAME_SPEINC,
               bt.TABNAME_TRAVET,
               bt.TABNAME_TIPLIST,
               bt.TABNAME_ALIQIVA,
               bt.TABNAME_PDC,
           )
        
        self._valfilters['agente'] =   ['agente.codice',    None, None]
        self._valfilters['zona'] =     ['zona.codice',      None, None]
        self._valfilters['stato'] =    ['stato.codice',     None, None]
        self._valfilters['categ'] =    ['categ.codice',     None, None]
        self._valfilters['status'] =   ['status.codice',    None, None]
        self._valfilters['modpag'] =   ['modpag.codice',    None, None]
        self._valfilters['speinc'] =   ['speinc.codice',    None, None]
        self._valfilters['travet'] =   ['travet.codice',    None, None]
        self._valfilters['tiplist'] =  ['tiplist.codice',   None, None]
        self._valfilters['aliqiva'] =  ['aliqiva.codice',   None, None]
        self._valfilters['bancapag'] = ['bancapag.descriz', None, None]
        self._valfilters['citta'] =    ['anag.citta',       None, None]
        self._valfilters['prov'] =     ['anag.prov',        None, None]
        self._valfilters['note'] =     ['anag.note',        None, None]
        self._cntfilters.append('citta')               
        self._cntfilters.append('note')
        self._hasfilters = True
        
        self._Auto_AddKeys( { "pdctip_clienti": True,
                              "bilmas_clienti": True,
                              "bilcon_clienti": True,
                              "bilcee_clienti": bt.CONBILRCEE == 1, } )
        self.ReadAutomat()
        self._auto_pdctip = getattr(self, "_auto_pdctip_clienti", None)
        self._auto_bilmas = getattr(self, "_auto_bilmas_clienti", None)
        self._auto_bilcon = getattr(self, "_auto_bilcon_clienti", None)
        self._auto_bilcee = getattr(self, "_auto_bilcee_clienti", None)
        
        self.db_report = "Lista Clienti"

    def InitAnagCard(self, parent):
        wdr.LinkTableClienteFornitore = wdr.LinkTableCliente
        p = aw.Panel( parent, -1)
        wdr.ClientiCardFunc( p, True )
        def cn(x):
            return self.FindWindowByName(x)
        cn('allegcf').SetDataLink('allegcf', {True:  1, False: 0})
        cn('piva').SetStateControl(cn('nazione'))
        self.InitGrigliaPrezzi()
        self.Bind(EVT_LINKTABCHANGED, self.OnPdcGrpChanged, cn('id_pdcgrp'))
        self.Bind(EVT_LINKTABCHANGED, self.OnStatoChanged, cn('id_stato'))
        self.Bind(wx.EVT_BUTTON, self.OnVediFido, cn('_butfido'))
        return p
    
    def OnStatoChanged(self, event):
        cn = self.FindWindowByName
        cn('nazione').SetValue(cn('id_stato').GetVatPrefix())
        sbl = cn('id_stato').IsBlacklisted()
        cn('is_blacklisted').Enable(sbl)
        if not sbl:
            cn('is_blacklisted').SetValue(0)
        event.Skip()
    
    def OnPdcGrpChanged(self, event):
        self.LoadGriglia()
        event.Skip()
    
    def GetLinkTableClass(self):
        import anag.lib as alib
        return alib.LinkTableCliente

    def OnVediFido(self, event):
        from magazz.dbtables import CtrFidoCliente
        from magazz.dataentry import DisplayFidoDialog
        cf = CtrFidoCliente()
        cf.CheckFido(self.db_recid)
        dlg = DisplayFidoDialog(self)
        dlg.UpdateValues(cf)
        dlg.ShowModal()
        dlg.Destroy()
        event.Skip()
    
    def InitControls(self, *args, **kwargs):
        pdcrel._CliForPanel.InitControls(self, *args, **kwargs)
        if bt.MAGSCOCAT:
            self.InitScontiCC()
            self.LoadScontiCC()
        else:
            self.FindWindowById(wdr.ID_PANSCONTICC).Show(False)

    def GetSpecializedSearchPanel(self, parent):
        p = aw.Panel(parent, -1)
        wdr.ClientiSpecSearchFunc(p)
        return p

    def UpdateDataRecord( self ):
        written = pdcrel._CliForPanel.UpdateDataRecord(self)
        if written:
            if bt.MAGSCOCAT:
                self.WriteScontiCC(); self.LoadScontiCC()
        return written
    
    def WriteScontiCC(self):
        scc = self.dbscc
        for s in scc:
            if s.id_pdc is None:
                s.id_pdc = self.db_recid
        if not scc.Save():
            aw.awu.MsgDialog(self, message=repr(scc.GetError()))
    
    def UpdateDataControls( self, recno ):
        pdcrel._CliForPanel.UpdateDataControls( self, recno )
        if self.loadrelated and bt.MAGSCOCAT:
            self.LoadScontiCC()
            self._grid_scc.SetGridCursor(0,1)
    
    def SetInsertMode(self, *args, **kwargs):
        out = pdcrel._CliForPanel.SetInsertMode(self, *args, **kwargs)
        if out and not self.valuesearch:
            self.FindWindowById(wdr.ID_ALLEGCF).SetValue(1)
        return out
    
    def GetOrdStampaDialog(self):
        return OrdStampaDialog(self, -1, 'Lista clienti')
    
    def GetOrdStampaRaggr(self, db, rag):
        r = {#nessun raggruppamento
             "N": (None,
                   lambda: '1',
                   None),
             #agente
             "A": ('agente.codice', 
                   lambda: db.anag.id_agente,
                   lambda: 'Agente: %s %s' % (db.anag.agente.codice, 
                                              db.anag.agente.descriz)),
             #zona
             "Z": ('zona.codice',
                   lambda: db.anag.id_zona,
                   lambda: 'Zona: %s %s' % (db.anag.zona.codice, 
                                            db.anag.zona.descriz)),
             #categoria
             "C": ('catana.codice', 
                   lambda: db.anag.id_categ,
                   lambda: 'Categoria: %s %s' % (db.anag.catana.codice, 
                                                 db.anag.catana.descriz)),
             #status
             "S": ('status.codice', 
                   lambda: db.anag.id_status,
                   lambda: 'Status: %s %s' % (db.anag.status.codice, 
                                              db.anag.status.descriz)),
             #mod.pagamento
             "P": ('modpag.codice', 
                   lambda: db.anag.id_modpag,
                   lambda: 'Mod.Pagamento: %s %s' % (db.anag.modpag.codice, 
                                                     db.anag.modpag.descriz)),
             #città
             "c": ('anag.citta', 
                   lambda: db.anag.citta,
                   lambda: 'Città: %s' % db.anag.citta),
         }
        return r[rag]
    
    def InitScontiCC(self):
        self.dbscc = dba.TabScontiCC()
        p = self.FindWindowById(wdr.ID_PANGRIDSCOCC)
        self._grid_scc = ScontiCategoriaGrid(p, self.dbscc)
    
    def LoadScontiCC(self):
        scc = self.dbscc
        if self.db_recid is None:
            scc.Reset()
        else:
            scc.Retrieve('scc.id_pdc=%s', self.db_recid)
            self._grid_scc.SetPdc(self.db_recid)
        self._grid_scc.ResetView()#ChangeData(scc.GetRecordset())


# ------------------------------------------------------------------------------


class OrdStampaPanel(aw.Panel):
    """
    Seleziona ordinamento e raggruppamento da effettuare in lista anagrafiche.
    """
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.OrdStampaCliFunc(self)
        self.FindWindowById(wdr.ID_RAGGR).SetDataLink('raggr', 'NAZCSPc')


# ------------------------------------------------------------------------------


class OrdStampaDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(OrdStampaPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnSelect, id=wdr.ID_SELECT)
    
    def OnSelect(self, event):
        self.EndModal(wx.ID_OK)
        event.Skip()
    
    def GetRaggr(self):
        rag = self.FindWindowById(wdr.ID_RAGGR).GetValue()
        if rag == "N":
            rag = None
        return rag


# ------------------------------------------------------------------------------


class ClientiFrame(pdcrel.ga._AnagFrame):
    """
    Frame Gestione tabella Clienti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ClientiPanel(self, -1))
        TestInitialFrameSize(self)

# ------------------------------------------------------------------------------


class ClientiDialog(pdcrel.ga._AnagDialog):
    """
    Dialog Gestione tabella Clienti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ClientiPanel(self, -1))
        TestInitialFrameSize(self)
