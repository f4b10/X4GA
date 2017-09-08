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

import anag.lib as alib

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


class ScontiCategoriaGrid(dbglib.ADB_Grid):

    def __init__(self, parent, dbscc):

        dbglib.ADB_Grid.__init__(self, parent, db_table=dbscc, can_edit=True, can_insert=True, on_menu_select='row')

        self.dbscc = dbscc
        self.id_pdc = None

        scc = dbscc
        cat = dbscc.catart
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        self.AddColumn(cat, 'codice',  'Cod.', col_width=40, is_editable=True,
                       linktable_info={'class':   alib.LinkTableCatArt,
                                       'col_id':  cn(scc, 'id_catart'),
                                       'col_cod': cn(cat, 'codice'),
                                       'col_des': cn(cat, 'descriz')})
        self.AddColumn(cat, 'descriz', 'Categoria', col_width=140, is_fittable=True)
        for n in range(1, bt.MAGNUMSCO+1, 1):
            self.AddColumn(scc, 'sconto%d'%n, 'Sc.%%%d'%n, col_type=self.TypeFloat(2, 2), is_editable=True)
        self.AddColumn(scc, 'id', '#scc', col_width=1)
        self.AddColumn(scc, 'id', '#cat', col_width=1)

        self.CreateGrid()

        self.AppendContextMenuVoice('Scheda categoria', self.OnSchedaCatArt)
        self.AppendContextMenuVoice('Elimina sconto', self.OnDeleteRow)

    def SetPdc(self, idpdc):
        self.id_pdc = idpdc

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

    def OnDeleteRow(self, event):
        row = self.GetSelectedRows()[0]
        self.DeleteRow(row)
        event.Skip()

    def CreateNewRow(self):
        dbglib.ADB_Grid.CreateNewRow(self)
        self.db_table.id_pdc = self.id_pdc


# ------------------------------------------------------------------------------


class VarListGrid(dbglib.ADB_Grid):

    def __init__(self, parent, dbvli):

        dbglib.ADB_Grid.__init__(self, parent, db_table=dbvli, can_edit=True, can_insert=True, on_menu_select='row')

        self.dbvli = dbvli
        self.id_cliente = None

        vli = dbvli
        fornit = dbvli.fornit
        marart = dbvli.marart
        catart = dbvli.catart
        gruart = dbvli.gruart
        tiplist = dbvli.tiplist

        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)

        fit = True

        if bt.MAGVLIFOR:
            self.AddColumn(fornit, 'codice',  'Cod.', col_width=50, is_editable=True,
                           linktable_info={'class':   alib.LinkTableFornit,
                                           'col_id':  cn(vli, 'id_fornit'),
                                           'col_cod': cn(fornit, 'codice'),
                                           'col_des': cn(fornit, 'descriz')})
            self.AddColumn(fornit, 'descriz', 'Fornitore', col_width=150, is_fittable=fit)
            fit = False

        if bt.MAGVLIMAR:
            self.AddColumn(marart, 'codice',  'Cod.', col_width=50, is_editable=True,
                           linktable_info={'class':   alib.LinkTableMarArt,
                                           'col_id':  cn(vli, 'id_marart'),
                                           'col_cod': cn(marart, 'codice'),
                                           'col_des': cn(marart, 'descriz')})
            self.AddColumn(marart, 'descriz', 'Marca', col_width=150, is_fittable=fit)
            fit = False

        if bt.MAGVLICAT:
            self.AddColumn(catart, 'codice',  'Cod.', col_width=50, is_editable=True,
                           linktable_info={'class':   alib.LinkTableCatArt,
                                           'col_id':  cn(vli, 'id_catart'),
                                           'col_cod': cn(catart, 'codice'),
                                           'col_des': cn(catart, 'descriz')})
            self.AddColumn(catart, 'descriz', 'Categoria', col_width=150, is_fittable=fit)
            fit = False

        if bt.MAGVLIGRU:
            self.AddColumn(gruart, 'codice',  'Cod.', col_width=50, is_editable=True,
                           linktable_info={'class':   alib.LinkTableGruArt,
                                           'col_id':  cn(vli, 'id_gruart'),
                                           'col_cod': cn(gruart, 'codice'),
                                           'col_des': cn(gruart, 'descriz')})
            self.AddColumn(gruart, 'descriz', 'Gruppo', col_width=150, is_fittable=fit)
            fit = False

        self.AddColumn(tiplist, 'codice',  'Cod.', col_width=50, is_editable=True,
                       linktable_info={'class':   alib.LinkTableTipList,
                                       'col_id':  cn(vli, 'id_tiplist'),
                                       'col_cod': cn(tiplist, 'codice'),
                                       'col_des': cn(tiplist, 'descriz')})
        self.AddColumn(tiplist, 'descriz', 'Tipo listino', col_width=150)

        self.AddColumn(vli, 'id',        '#vli', col_width=1)
        if bt.MAGVLIFOR:
            self.AddColumn(vli, 'id_fornit', '#for', col_width=1)
            self.AppendContextMenuVoice('Scheda fornitore', self.OnSchedaFornit)
        if bt.MAGVLIMAR:
            self.AddColumn(vli, 'id_marart', '#mar', col_width=1)
            self.AppendContextMenuVoice('Scheda marca', self.OnSchedaMarArt)
        if bt.MAGVLICAT:
            self.AddColumn(vli, 'id_catart', '#cat', col_width=1)
            self.AppendContextMenuVoice('Scheda categoria', self.OnSchedaCatArt)
        if bt.MAGVLIGRU:
            self.AddColumn(vli, 'id_gruart', '#gru', col_width=1)
            self.AppendContextMenuVoice('Scheda gruppo', self.OnSchedaGruArt)

        self.CreateGrid()

        self.AppendContextMenuVoice('Elimina listino variabile', self.OnDeleteRow)

    def SetPdc(self, idpdc):
        self.id_pdc = idpdc

    def OnSchedaFornit(self, event):
        row = self.GetSelectedRows()[0]
        vli = self.dbvli
        if 0 <= row < vli.RowsCount():
            vli.MoveRow(row)
            from anag.fornit import FornitDialog
            d = FornitDialog(self, onecodeonly=vli.id_fornit)
            d.OneCardOnly(vli.id_fornit)
            d.ShowModal()
            d.Destroy()
        event.Skip()

    def OnSchedaMarArt(self, event):
        row = self.GetSelectedRows()[0]
        vli = self.dbvli
        if 0 <= row < vli.RowsCount():
            vli.MoveRow(row)
            from anag.marart import MarArtDialog
            d = MarArtDialog(self, onecodeonly=vli.id_marart)
            d.OneCardOnly(vli.id_marart)
            d.ShowModal()
            d.Destroy()
        event.Skip()

    def OnSchedaCatArt(self, event):
        row = self.GetSelectedRows()[0]
        vli = self.dbvli
        if 0 <= row < vli.RowsCount():
            vli.MoveRow(row)
            from anag.catart import CatArtDialog
            d = CatArtDialog(self, onecodeonly=vli.id_catart)
            d.OneCardOnly(vli.id_catart)
            d.ShowModal()
            d.Destroy()
        event.Skip()

    def OnSchedaGruArt(self, event):
        row = self.GetSelectedRows()[0]
        vli = self.dbvli
        if 0 <= row < vli.RowsCount():
            vli.MoveRow(row)
            from anag.gruart import GruArtDialog
            d = GruArtDialog(self, onecodeonly=vli.id_gruart)
            d.OneCardOnly(vli.id_gruart)
            d.ShowModal()
            d.Destroy()
        event.Skip()

    def OnDeleteRow(self, event):
        row = self.GetSelectedRows()[0]
        self.DeleteRow(row)
        event.Skip()

    def CreateNewRow(self):
        dbglib.ADB_Grid.CreateNewRow(self)
        self.db_table.id_cliente = self.id_pdc


# ------------------------------------------------------------------------------


class ClientiPanel(pdcrel._CliForPanel):
    """
    Gestione della tabella clienti.
    """
    def __init__(self, *args, **kwargs):
        #=======================================================================
        # tipana=None
        # try:
        #     tipana=kwargs.pop('tipana')
        # except:
        #     tipana=''
        # if tipana==None:
        #     self.pdctipo = "C"
        # else:
        #     self.pdctipo = tipana
        #=======================================================================

        self.pdctipo='C'

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

        self._sqlrelcol += ', status.hidesearch'

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

        return p

    def OnStatoChanged(self, event):
        cn = self.FindWindowByName
        if not cn('nazione').GetValue() or len(cn('nazione').GetValue().strip())==0:
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

        cn = self.FindWindowByName
        nb = cn('commzone')
        for n in range(nb.GetPageCount()):
            if nb.GetPageText(n) == 'Sconti e fido':
                p = nb.GetPage(n)
                if bt.GESFIDICLI == '1':
                    c = p.FindWindowByName('_butfido')
                    if c:
                        self.Bind(wx.EVT_BUTTON, self.OnVediFido, c)
                else:
                    c = p.FindWindowByName('panfidi')
                    if c:
                        c.Hide()
                    nb.SetPageText(n, 'Sconti')

        for n in range(9):
            if n+1>bt.MAGNUMSCO:
                for prefix in 'labsco sconto'.split():
                    c = cn('%s%d' % (prefix, n+1))
                    if c:
                        c.Hide()

        if bt.MAGSCOCAT:
            p = wx.Panel(nb)
            self.InitScontiCC(p)
            nb.AddPage(p, 'Sconti per categoria')
            self.LoadScontiCC()

        if bt.MAGROWLIS and (bt.MAGVLIFOR or bt.MAGVLIMAR or bt.MAGVLICAT or bt.MAGVLIGRU):
            p = wx.Panel(nb)
            self.InitVarList(p)
            nb.AddPage(p, 'Listini variabili')
            self.LoadVarList()

    def GetSpecializedSearchPanel(self, parent):
        p = aw.Panel(parent, -1)
        wdr.ClientiSpecSearchFunc(p)
        return p

    def UpdateDataRecord( self ):
        written = pdcrel._CliForPanel.UpdateDataRecord(self)
        if written:
            if bt.MAGSCOCAT:
                self.WriteScontiCC(); self.LoadScontiCC()
            if bt.MAGROWLIS:
                self.WriteVarList(); self.LoadVarList()
        return written

    def UpdateDataControls( self, recno ):
        pdcrel._CliForPanel.UpdateDataControls( self, recno )
        if self.loadrelated:
            if bt.MAGSCOCAT:
                self.LoadScontiCC()
                self._grid_scc.SetGridCursor(0,1)
            if bt.MAGROWLIS and (bt.MAGVLIFOR or bt.MAGVLIMAR or bt.MAGVLICAT or bt.MAGVLIGRU):
                self.LoadVarList()
                self._grid_vli.SetGridCursor(0,1)

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

    def InitScontiCC(self, parent):
        self.dbscc = dba.TabScontiCC()
        self._grid_scc = ScontiCategoriaGrid(parent, self.dbscc)

    def LoadScontiCC(self):
        scc = self.dbscc
        if self.db_recid is None:
            scc.Reset()
        else:
            scc.Retrieve('scc.id_pdc=%s', self.db_recid)
            self._grid_scc.SetPdc(self.db_recid)
        self._grid_scc.ResetView()

    def WriteScontiCC(self):
        scc = self.dbscc
        for s in scc:
            if s.id_pdc is None:
                s.id_pdc = self.db_recid
        if not scc.Save():
            aw.awu.MsgDialog(self, message=repr(scc.GetError()))

    def InitVarList(self, parent):
        self.dbvli = dba.TabVarList()
        self._grid_vli = VarListGrid(parent, self.dbvli)

    def LoadVarList(self):
        if bt.MAGROWLIS and (bt.MAGVLIFOR or bt.MAGVLIMAR or bt.MAGVLICAT or bt.MAGVLIGRU):
            vli = self.dbvli
            if self.db_recid is None:
                vli.Reset()
            else:
                vli.Retrieve('vli.id_cliente=%s', self.db_recid)
                self._grid_vli.SetPdc(self.db_recid)
            self._grid_vli.ResetView()

    def WriteVarList(self):
        if bt.MAGROWLIS and (bt.MAGVLIFOR or bt.MAGVLIMAR or bt.MAGVLICAT or bt.MAGVLIGRU):
            vli = self.dbvli
            for v in vli:
                if v.id_cliente is None:
                    v.id_cliente = self.db_recid
            if not vli.Save():
                aw.awu.MsgDialog(self, message=repr(vli.GetError()))


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
