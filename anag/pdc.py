#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         anag/pdc.py
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
import anag.dbtables as dba
from anag.pdcrel_wdr import *

import awc.controls.windows as aw
from awc.controls.linktable import EVT_LINKTABCHANGED
from awc.util import MsgDialog

from anag.pdcrel import _PdcRangeCode

from Env import Azienda
bt = Azienda.BaseTab

import stormdb as adb
import report as rpt

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc.wxinit as wxinit


FRAME_TITLE = "Piano dei Conti"


class PdcSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        cols = []
        def a(x):
            cols.append(x)
        a(    ( 35, (cn('bilmas_codice'),    "Cod.",          _STR, True)))
        a(    (120, (cn('bilmas_descriz'),   "Mastro",        _STR, True)))
        a(    ( 35, (cn('bilcon_codice'),    "Cod.",          _STR, True)))
        a(    (120, (cn('bilcon_descriz'),   "Conto",         _STR, True)))
        a(    ( 50, (cn('pdc_codice'),       "Cod.",          _STR, True)))
        a(    ( 30, (cn('tipana_codice'),    "Tipo",          _STR, True)))
        a(    (300, (cn('pdc_descriz'),      "Descrizione",   _STR, True)))
        if bt.CONBILRCEE:
            a(( 30, (cn('bilcee_sezione'),   'Sez.',          _STR, True)))
            a(( 30, (cn('bilcee_voce'),      'Voce',          _STR, True)))
            a(( 30, (cn('bilcee_capitolo'),  'Cap.',          _STR, True)))
            a(( 30, (cn('bilcee_dettaglio'), 'Dett',          _STR, True)))
            a(( 30, (cn('bilcee_subdett'),   'Sub.',          _STR, True)))
            a((400, (cn('bilcee_descriz'),   'Riclassif.CEE', _STR, True)))
        a(    (  1, (cn('pdc_id'),           "#pdc",          _STR, True)))
        a(    (  1, (cn('bilmas_id'),        "#mas",          _STR, True)))
        a(    (  1, (cn('bilcon_id'),        "#con",          _STR, True)))
        a(    (  1, (cn('tipana_id'),        "#tip",          _STR, True)))
        if bt.CONBILRCEE:
            a((  1, (cn('pdc_id'),           "#cee",          _STR, True)))
        return cols
    
    def SetColumn2Fit(self):
        self.SetFitColumn(6)


# ------------------------------------------------------------------------------


class PdcPanel(ga.AnagPanel, _PdcRangeCode):
    """
    Gestione della tabella Piano dei Conti.
    """
    
    def __init__(self, *args, **kwargs):
        
        ga.AnagPanel.__init__(self, *args, **kwargs)
        _PdcRangeCode.__init__(self)
        
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_PDC ] )
        self.SetDbOrderColumns((
            ("Bilancio e codice", 
             ('IF(bilmas.tipo="P",0,IF(bilmas.tipo="E",1,IF(bilmas.tipo="O",2,3)))', 
              'bilmas.codice', 
              'bilcon.codice', 
              'IF(tipana.tipo IN ("C","F"), pdc.descriz, pdc.codice)')),
            ("Bilancio e descrizione", 
             ('IF(bilmas.tipo="P",0,IF(bilmas.tipo="E",1,IF(bilmas.tipo="O",2,3)))', 
              'bilmas.descriz', 
              'bilcon.descriz', 
              'pdc.descriz')),
            ("Bilancio CEE e codice",
             ('bilcee.codice', 'pdc.codice',)),
            ("Bilancio CEE e descrizione",
             ('bilcee.codice', 'pdc.descriz',)),
            ("Codice",
             ('pdc.codice',)),
            ("Tipo e Descrizione",
             ('tipana.codice', 'pdc.descriz',)),
        ))
        
        self._sqlrelcol = ", bilmas.tipo, tipana.tipo"
        self._sqlrelcol += ", bilmas.id, bilmas.codice, bilmas.descriz"
        self._sqlrelcol += ", bilcon.id, bilcon.codice, bilcon.descriz"
        self._sqlrelcol += ", tipana.id, tipana.codice, tipana.descriz"
        self._sqlrelcol += ", bilcee.id, bilcee.codice, bilcee.descriz, bilcee.sezione, bilcee.voce, bilcee.capitolo, bilcee.dettaglio, bilcee.subdett"
        
        self._sqlrelfrm =\
            " LEFT JOIN %s AS bilmas ON pdc.id_bilmas=bilmas.id"\
            " LEFT JOIN %s AS bilcon ON pdc.id_bilcon=bilcon.id"\
            " LEFT JOIN %s AS tipana ON pdc.id_tipo=tipana.id"\
            " LEFT JOIN %s AS status ON pdc.id_statpdc=status.id"\
            " LEFT JOIN %s AS bilcee ON pdc.id_bilcee=bilcee.id"\
            % ( bt.TABNAME_BILMAS,
                bt.TABNAME_BILCON,
                bt.TABNAME_PDCTIP,
                bt.TABNAME_STATPDC,
                'x4.bilcee')
        self.db_tabprefix = "pdc."
        
        self._valfilters['biltip'] = ['bilmas.tipo',   'T',  None]
        self._valfilters['bilmas'] = ['bilmas.codice', None, None]
        self._valfilters['bilcon'] = ['bilcon.codice', None, None]
        self._valfilters['tipo'] =   ['tipana.codice', None, None]
        self._valfilters['bilcee'] = ['bilcee.codice', None, None]
        self._valfilters['nobilcee'] = [None, False, None]
        self._nulfilters['nobilcee'] = [True, False]
        self._nulfilters['biltip'] = ['T']
        self._filternocee = False
        self._filtercf = False
        #inizio escludendo cli/for
        self.db_filtersexpr = "NOT tipana.tipo IN ('C', 'F')"
        self.db_filterspars = []
        self._hasfilters = True
        
        self.db_report = "Piano dei Conti"
        
        self.HelpBuilder_SetDir('anag.pdcrel')
    
    def InitAnagCard(self, parent):
        p = aw.Panel( parent, -1)
        PdcCardFunc( p, True )
        return p

    def InitAnagToolbar(self, parent):        
        out = ga.AnagToolbar(parent, -1, hide_ssv=False)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnSSV)
        return out
    
    def OnSSV(self, event):
        self.UpdateSearch()
        event.Skip()
    
    def GetSearchResultsGrid(self, parent):
        grid = PdcSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                    self.db_tabname, self.GetSqlColumns())
        return grid
    
    def InitControls(self, *args, **kwargs):
        out = ga.AnagPanel.InitControls(self, *args, **kwargs)
        self.Bind(EVT_LINKTABCHANGED, self.OnMastroChanged, id=ID_CTRBILMAS)
        self.Bind(EVT_LINKTABCHANGED, self.OnTipanaChanged, id=ID_CTRPDCTIP)

    def GetSqlFilterSearch(self):
        cn = self.FindWindowByName
        cmd, par = ga.AnagPanel.GetSqlFilterSearch(self)
        #filtro per inclusione/esclusione elementi con status nascosto
        if cn('_ssv').GetValue():
            flt = "status.hidesearch IS NULL or status.hidesearch<>1"
            if cmd:
                cmd = "(%s) AND " % cmd
            cmd += "(%s)" % flt
        return cmd, par
    
    def GetSpecializedSearchPanel(self, parent):
        p = wx.Panel(parent, -1)
        PdcSpecSearchFunc(p)
        p.FindWindowById(ID_FILT_PEO).SetDataLink('biltip', 'TPEO')
        p.FindWindowById(ID_NOBILCEE).SetDataLink(values=[True, False])
        def OnDataLinkChanged(event):
            ctr = event.GetEventObject()
            name = ctr.GetName()
            if name.startswith('bilmas'):
                masid = ctr.GetValue()
                con = parent.FindWindowByName('bilcon'+name[-1])
                if masid is None:
                    con.SetFilter('1')
                else:
                    con.SetFilter('id_bilmas=%d' % masid)
            event.Skip()
        p.Bind(EVT_LINKTABCHANGED, OnDataLinkChanged)
        return p
    
    def InitSearchFilters(self, fltwin):
        ga.AnagPanel.InitSearchFilters(self, fltwin)
        cn = fltwin.FindWindowByName
        cn('clifor').SetValue(self._filtercf)
        cn('nobilcee').SetValue(self._filternocee)
        
    def ApplySearchFilters(self, fltwin):
        flt, par = ga.AnagPanel.ApplySearchFilters(self, fltwin)
        cn = fltwin.FindWindowByName
        #filtro per inclusione/esclusione clienti e fornitori
        clifor = cn('clifor').GetValue()
        if not clifor:
            if flt: flt += " AND "
            flt += "NOT tipana.tipo IN ('C', 'F')"
        self._filtercf = clifor
        #filtro per classificazione cee mancante
        nobilcee = cn('nobilcee').GetValue()
        if nobilcee:
            if flt: flt += " AND "
            flt += "bilcee.id IS NULL"
        self._filternocee = nobilcee
        self.db_filtersexpr, self.db_filterspars = flt, par
        return flt, par
    
    def OnMastroChanged( self, event ):
        ci = lambda x: self.FindWindowById(x)
        mas, con = map(ci, (ID_CTRBILMAS, ID_CTRBILCON))
        idmas = mas.GetValue()
        if idmas is None:
            con.Disable()
        else:
            con.SetFilter( "id_bilmas=%d" % idmas )
            con.Enable()
        if not con.Validate():
            con.ResetValue()
        return self
    
    def GetDbPrint(self):
        return dba.PdcStruttura()
    
    def UpdateDataControls(self, *args, **kwargs):
        #tolgo il filtro dal conto di bilancio
        #poiché il filtro presente è stato impostato *prima* di aggiornare i
        #controlli con i valori di questo record, quindi se il mastro del
        #record attuale differisce da quello del record precedente, il filtro
        #impostato sul conto è *errato*
        self.FindWindowByName('id_bilcon').SetFilter(None)
        ga.AnagPanel.UpdateDataControls(self, *args, **kwargs)


# ------------------------------------------------------------------------------


class PdcFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Piano dei Conti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(PdcPanel(self, -1))


# ------------------------------------------------------------------------------


class PdcDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Piano dei Conti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(PdcPanel(self, -1))


# ------------------------------------------------------------------------------


class PdcCeeSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 30, (cn('bilcee_sezione'),   'Sez.',          _STR, True)),
                ( 30, (cn('bilcee_voce'),      'Voce',          _STR, True)),
                ( 30, (cn('bilcee_capitolo'),  'Cap.',          _STR, True)),
                ( 30, (cn('bilcee_dettaglio'), 'Dett',          _STR, True)),
                ( 30, (cn('bilcee_subdett'),   'Sub.',          _STR, True)),
                (240, (cn('bilcee_descriz'),   'Riclassif.CEE', _STR, True)),
                ( 50, (cn('pdc_codice'),       "Cod.",          _STR, True)),
                ( 30, (cn('tipana_codice'),    "Tipo",          _STR, True)),
                (300, (cn('pdc_descriz'),      "Descrizione",   _STR, True)),
                ( 35, (cn('bilmas_codice'),    "Cod.",          _STR, True)),
                (120, (cn('bilmas_descriz'),   "Mastro",        _STR, True)),
                ( 35, (cn('bilcon_codice'),    "Cod.",          _STR, True)),
                (120, (cn('bilcon_descriz'),   "Conto",         _STR, True)),
                (  1, (cn('pdc_id'),           "#pdc",          _STR, True)),
                (  1, (cn('bilmas_id'),        "#mas",          _STR, True)),
                (  1, (cn('bilcon_id'),        "#con",          _STR, True)),
                (  1, (cn('tipana_id'),        "#tip",          _STR, True)),
                (  1, (cn('pdc_id'),           "#cee",          _STR, True)),
            )                           
    
    def SetColumn2Fit(self):
        self.SetFitColumn(6)


# ------------------------------------------------------------------------------


class PdcCeePanel(PdcPanel):
    
    def __init__(self, *args, **kwargs):
        PdcPanel.__init__(self, *args, **kwargs)
        self.db_searchordnum = 2
        self.db_report = "Piano dei Conti CEE"
        self.HelpBuilder_SetDir('anag.pdccee.pdc')
    
    def GetSearchResultsGrid(self, parent):
        grid = PdcCeeSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid


# ------------------------------------------------------------------------------


class PdcCeeFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Piano dei Conti CEE.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(PdcCeePanel(self, -1))


# ------------------------------------------------------------------------------


class PdcCeeDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Piano dei Conti CEE.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(PdcCeePanel(self, -1))
