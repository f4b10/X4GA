#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/fornit.py
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

import awc.layout.gestanag as ga
import anag.pdcrel_wdr as wdr

from anag import pdcrel

from Env import Azienda
from awc.controls.linktable import EVT_LINKTABCHANGED
bt = Azienda.BaseTab

import awc.controls.windows as aw
import stormdb as adb
import report as rpt


FRAME_TITLE = "Fornitori"


class FornitPanel(pdcrel._CliForPanel):
    """
    Gestione della tabella Fornitori.
    """
    def __init__(self, *args, **kwargs):
        
        self.pdctipo = "F"
        self.tabanag = Azienda.BaseTab.TABNAME_FORNIT
        pdcrel._CliForPanel.__init__(self, *args, **kwargs)
        
        self.anag_db_columns = [ c for c in Azienda.BaseTab.tabelle\
                                 [bt.TABSETUP_TABLE_FORNIT]\
                                 [bt.TABSETUP_TABLESTRUCTURE] ]
        
        self._sqlrelfrm +=\
            " LEFT JOIN %s AS zona     ON anag.id_zona=zona.id"\
            " LEFT JOIN %s AS stato    ON anag.id_stato=stato.id"\
            " LEFT JOIN %s AS categ    ON anag.id_categ=categ.id"\
            " LEFT JOIN %s AS status   ON anag.id_status=status.id"\
            " LEFT JOIN %s AS modpag   ON anag.id_modpag=modpag.id"\
            " LEFT JOIN %s AS speinc   ON anag.id_speinc=speinc.id"\
            " LEFT JOIN %s AS travet   ON anag.id_travet=travet.id"\
            " LEFT JOIN %s AS aliqiva  ON anag.id_aliqiva=aliqiva.id"\
            " LEFT JOIN %s AS bancapag ON anag.id_bancapag=bancapag.id"\
            % (bt.TABNAME_ZONE,
               'x4.stati',
               bt.TABNAME_CATFOR,
               bt.TABNAME_STATFOR,
               bt.TABNAME_MODPAG,
               bt.TABNAME_SPEINC,
               bt.TABNAME_TRAVET,
               bt.TABNAME_ALIQIVA,
               bt.TABNAME_PDC,
           )
        
        self._sqlrelcol += ', status.hidesearch'
        
        self._valfilters['zona'] =     ['zona.codice',      None, None]
        self._valfilters['stato'] =    ['stato.codice',     None, None]
        self._valfilters['categ'] =    ['categ.codice',     None, None]
        self._valfilters['status'] =   ['status.codice',    None, None]
        self._valfilters['modpag'] =   ['modpag.codice',    None, None]
        self._valfilters['speinc'] =   ['speinc.codice',    None, None]
        self._valfilters['travet'] =   ['travet.codice',    None, None]
        self._valfilters['aliqiva'] =  ['aliqiva.codice',   None, None]
        self._valfilters['bancapag'] = ['bancapag.descriz', None, None]
        self._valfilters['citta'] =    ['anag.citta',       None, None]
        self._valfilters['prov'] =     ['anag.prov',        None, None]
        self._valfilters['note'] =     ['anag.note',        None, None]
        self._cntfilters.append('citta')
        self._cntfilters.append('note')
        self._hasfilters = True
        
        self._Auto_AddKeys( { "pdctip_fornit": True,
                              "bilmas_fornit": True,
                              "bilcon_fornit": True,
                              "bilcee_fornit": bt.CONBILRCEE == 1,
                               } )
        self.ReadAutomat()
        self._auto_pdctip = getattr(self, "_auto_pdctip_fornit", None)
        self._auto_bilmas = getattr(self, "_auto_bilmas_fornit", None)
        self._auto_bilcon = getattr(self, "_auto_bilcon_fornit", None)
        self._auto_bilcee = getattr(self, "_auto_bilcee_fornit", None)
        
        self.db_report = "Lista Fornitori"
    
    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.LinkTableClienteFornitore = wdr.LinkTableFornit
        wdr.FornitCardFunc( p, True )
        def cn(x):
            return self.FindWindowByName(x)
        self._pdcpref = cn('pdcpref')
        cn('allegcf').SetDataLink('allegcf', {True:  1, False: 0})
        cn('piva').SetStateControl(cn('nazione'))
        self.InitGrigliaPrezzi()
        self.Bind(EVT_LINKTABCHANGED, self.OnPdcGrpChanged, cn('id_pdcgrp'))
        self.Bind(EVT_LINKTABCHANGED, self.OnStatoChanged, cn('id_stato'))
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
        return alib.LinkTableFornit

    def GetSpecializedSearchPanel(self, parent):
        p = wx.Panel(parent, -1)
        wdr.FornitSpecSearchFunc(p)
        return p
    
    def SetInsertMode(self, *args, **kwargs):
        pdcrel._CliForPanel.SetInsertMode(self, *args, **kwargs)
        if not self.valuesearch:
            self.FindWindowById(wdr.ID_ALLEGCF).SetValue(1)
    
    def UpdateButtonsState(self):
        pdcrel._CliForPanel.UpdateButtonsState(self)
        self._pdcpref.UpdateMoveButtonsState()

    def UpdateDataControls( self, recno ):
        pdcrel._CliForPanel.UpdateDataControls( self, recno )
        if not self.valuesearch:
            self._pdcpref.UpdateDataControls(self.db_recid)

    def TransferDataFromWindow( self ):
        out = pdcrel._CliForPanel.TransferDataFromWindow(self)
        if out:
            out = self._pdcpref.TransferDataFromWindow(self.db_recid)
        return out
    
    def GetOrdStampaDialog(self):
        return OrdStampaDialog(self, -1, 'Lista fornitori')
    
    def GetOrdStampaRaggr(self, db, rag):
        r = {#nessun raggruppamento
             "N": (None,
                   lambda: '1',
                   None),
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


# ------------------------------------------------------------------------------


class OrdStampaPanel(aw.Panel):
    """
    Seleziona ordinamento e raggruppamento da effettuare in lista anagrafiche.
    """
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.OrdStampaForFunc(self)
        self.FindWindowById(wdr.ID_RAGGR).SetDataLink('raggr', 'NZCSPc')


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


class FornitFrame(pdcrel.ga._AnagFrame):
    """
    Frame Gestione tabella Fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(FornitPanel(self, -1))


# ------------------------------------------------------------------------------


class FornitDialog(pdcrel.ga._AnagDialog):
    """
    Dialog Gestione tabella Fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(FornitPanel(self, -1))
