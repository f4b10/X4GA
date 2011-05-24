#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/scadenzario.py
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

import awc
import awc.controls.windows as aw

import contab.dbtables as dbc
import anag.dbtables as dba

import contab.pdcint_wdr as wdr

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import stormdb as adb

import report as rpt
import copy


FRAME_TITLE = "Scadenzario clienti/fornitori"
FRAME_TITLE_GRUPPO = "Scadenzario clienti/fornitori di gruppo"


class GridScadTot(dbglib.DbGridColoriAlternati):
    
    grouptitle = None
    
    def __init__(self, parent, dbscad, cfmix, *args, **kwargs):
        
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size)
        
        self.mode = kwargs.pop('agente_mode', None)
        
        self.dbscad = dbscad
        dbscad.Get(-1)
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        pdc = self.dbscad
        age = pdc.anagcli.agente
        sin = pdc.sintesi
        pcf = pdc.GetPartite()
        cau = pcf.caus
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        if cfmix:
            cf = 'cf_'
        else:
            cf = ''
        ts1 = "total_%ssaldo" % cf
        ts2 = "total_%ssaldo_scaduto" % cf
        ts3 = "total_%ssaldo_ascadere" % cf
        in1 = "total_%sinsoluti_passati" % cf
        in2 = "total_%sinsoluti_attivi" % cf
        
        col0rsc, col0tit, col1rsc, col1tit = self.DefGroupCols()
        
        cols = (\
            ( 44, (col0rsc,      col0tit,           _STR, True )),\
            (150, (col1rsc,      col1tit,           _STR, True )),\
            (110, (cn(sin, ts1), "Saldo",           _IMP, True )),\
            (110, (cn(sin, ts2), "Scaduto",         _IMP, True )),\
            (110, (cn(sin, ts3), "A scadere",       _IMP, True )),\
            (110, (cn(sin, in2), "Insoluti attivi", _IMP, True )),\
            (110, (cn(sin, in1), "Insoluti pagati", _IMP, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = pdc.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        self.AddTotalsRow(1, 'Totali:', (cn(sin, ts1),
                                         cn(sin, ts2),
                                         cn(sin, ts3),
                                         cn(sin, in2),
                                         cn(sin, in1)))
        
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
    
    def DefGroupCols(self):
        col0rsc, col0tit = self.GetColumnSpec('codice')
        col1rsc, col1tit = self.GetColumnSpec('descriz')
        return col0rsc, col0tit, col1rsc, col1tit
    
    def GetColumnSpec(self, *args):
        raise Exception, 'Classe non istanziabile'


# ------------------------------------------------------------------------------


class GridScadTotAgeZna(GridScadTot):
    
    mode = 'anag'
    def SetMode(self, mode):
        self.mode = mode
    
    def GetColumnSpec(self, col):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        if col == 'codice':
            title = 'Cod.'
        else:
            title = 'Descrizione'
        if self.mode == 'anag':
            return (cn(self.dbscad.anagcli.agente, col), title)
        return (cn(self.dbscad, 'age%s'%col[:3]), title)
    
    def DefGroupCols(self):
        col0rsc, col0tit = self.GetColumnSpec('codice')
        col1rsc, col1tit = self.GetColumnSpec('descriz')
        return col0rsc, col0tit, col1rsc, col1tit
    
    def SetGridMode(self, gm):
        assert gm in 'agente zona'.split()
        rsc = self.GetTable().rsColumns
        cl = self.GetTable().colLabels
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        if gm == 'agente':
            cl[1] = 'Agente'
            tab = self.dbscad.anagcli.agente
            if self.mode == 'anag':
                rsc[0] = cn(tab, 'codice')
                rsc[1] = cn(tab, 'descriz')
            else:
                rsc[0] = cn(self.dbscad, 'agecod')
                rsc[1] = cn(self.dbscad, 'agedes')
        else:
            cl[1] = 'Zona'
            tab = self.dbscad.anagcli.zonacli
            rsc[0] = cn(tab, 'codice')
            rsc[1] = cn(tab, 'descriz')


# ------------------------------------------------------------------------------


class GridScadTotAnag(GridScadTot):
    grouptitle = 'Sottoconto'
    
    def GetColumnSpec(self, col):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        if col == 'codice':
            title = 'Cod.'
        else:
            title = self.grouptitle
        return (cn(self.dbscad, col), title)
    

# ------------------------------------------------------------------------------


from contab.pdcint import GridScadenzario as GridScadDet

class ScadenzarioPanel(aw.Panel):
    
    WdrFunc = wdr.ScadenzarioFunc
    cfmix = False

    ageupdate = False
    znaupdate = False
    detanag = False
    
    agente_mode = 'anag'
    def SetAgenteMode(self, mode):
        self.agente_mode = mode
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        self.WdrFunc(self)
        
        self.OpenTables()
        
        cbn = lambda x: self.FindWindowByName(x)
        cbi = lambda x: self.FindWindowById(x)
        
        for name, val, init in (('pcftipocf', "CFG", "C"),\
                                ('pcforder',  "CD", "D")):
            c = cbn(name)
            if c:
                c.SetDataLink(name, val)
                c.SetValue(init)
        
        self.CreateGrids()
        
        for cid, func in ((wdr.ID_PCFCLIAGE,   self.OnSetAgenteUpdate),
                          (wdr.ID_PCFRAGGR,    self.OnSetAgenteZonaRaggr),
                          (wdr.ID_PCFRAGGRAGE, self.OnSetAgenteRaggr),
                          (wdr.ID_PCFRAGGRZNA, self.OnSetZonaRaggr),
                          (wdr.ID_PCFDETCLI,   self.OnSetDetAnag)):
            self.Bind(wx.EVT_CHECKBOX, func, id=cid)
        
        self.Bind(wx.EVT_RADIOBOX, self.OnCliFor, id=wdr.ID_PCFTIPCF)
        
        for cid, func in ((wdr.ID_PCFBUTUPD,     self.OnUpdateFilters),
                          (wdr.ID_PCFBTNPRT,     self.OnStampaDet),
                          (wdr.ID_PCFBTNPRTALL,  self.OnStampaTutto),
                          (wdr.ID_PCFBTNPRTRIEP, self.OnStampaRiep)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        self.UpdateFilters(warn=False)
        self.TestCliFor()
    
    def OpenTables(self, agedoc=False):
        
        self.dbtipa = dba.TipiAnagrafici()
        
        self.dbscad = dbc.PdcScadenzario(\
            today=Env.Azienda.Login.dataElab,\
            giorni_rb=30)
        
        for tab, alias in ((bt.TABNAME_CLIENTI, 'anagcli'),
                           (bt.TABNAME_FORNIT,  'anagfor')):
            anag = self.dbscad.AddJoin(tab, alias, join=adb.JOIN_LEFT,
                                       idLeft='id', idRight='id')
            #l'alias della zona deve essere diverso tra clienti e fornitori,
            #altrimenti si hanno due alias uguali a livello sql
            #per semplificare l'accesso alle informazioni della zona
            #indistintamente per clienti e fornitori, viene creato un riferimento
            #dal nome costante (=zona, che fantasia eh) sia sul nodo clienti
            #(dbscad.anagcli.zona) che su quello fornitori (dbscad.anagfor.zona)
            #stesso discorso per la categoria cliente/fornitore
            if tab == bt.TABNAME_CLIENTI:
                anag.AddJoin(bt.TABNAME_AGENTI, 'agente', join=adb.JOIN_LEFT)
                anag.zona =\
                    anag.AddJoin(bt.TABNAME_ZONE,   'zonacli', 
                                 idLeft='id_zona', join=adb.JOIN_LEFT)
                anag.catana =\
                    anag.AddJoin(bt.TABNAME_CATCLI, 'catcli', 
                                 idLeft='id_categ', join=adb.JOIN_LEFT)
            else:
                anag.zona =\
                    anag.AddJoin(bt.TABNAME_ZONE,   'zonafor', 
                                 idLeft='id_zona', join=adb.JOIN_LEFT)
                anag.catana =\
                    anag.AddJoin(bt.TABNAME_CATFOR, 'catfor', 
                                 idLeft='id_categ', join=adb.JOIN_LEFT)
        
        if agedoc:
            self.dbscad.AddField("""(
              SELECT age.id
                FROM contab_s sca
                JOIN contab_h reg ON reg.id=sca.id_reg
           LEFT JOIN movmag_h doc ON doc.id_reg=reg.id
           LEFT JOIN agenti   age ON age.id=doc.id_agente
               WHERE sca.id_pcf=sintesi.id AND reg.id_regiva IS NOT NULL
               LIMIT 1)""", 'ageid')
            
            self.dbscad.AddField("""(
              SELECT age.codice
                FROM contab_s sca
                JOIN contab_h reg ON reg.id=sca.id_reg
           LEFT JOIN movmag_h doc ON doc.id_reg=reg.id
           LEFT JOIN agenti   age ON age.id=doc.id_agente
               WHERE sca.id_pcf=sintesi.id AND reg.id_regiva IS NOT NULL
               LIMIT 1)""", 'agecod')
            
            self.dbscad.AddField("""(
              SELECT age.descriz
                FROM contab_s sca
                JOIN contab_h reg ON reg.id=sca.id_reg
           LEFT JOIN movmag_h doc ON doc.id_reg=reg.id
           LEFT JOIN agenti   age ON age.id=doc.id_agente
               WHERE sca.id_pcf=sintesi.id AND reg.id_regiva IS NOT NULL
               LIMIT 1)""", 'agedes')
        
        self.dbscad._info.cpp = False
        self.dbscad.Reset()
        
        mode = 'anag'
        if agedoc:
            mode = 'doc'
        self.SetAgenteMode(mode)
    
    def CreateGrids(self):
        
        ci = self.FindWindowById
        
        if getattr(self, 'gridtot1', None):
#            self.gridtot1.Destroy()
            wx.CallAfter(self.gridtot1.Destroy)
        self.gridtot1 = GridScadTotAgeZna(ci(wdr.ID_PCFGRIDTOT1), self.dbscad, self.cfmix, agente_mode=self.agente_mode)
        self.gridtot1.Bind(gl.EVT_GRID_SELECT_CELL, self.OnAgeZnaSelected)
        
        if getattr(self, 'gridtot2', None):
#            self.gridtot2.Destroy()
            wx.CallAfter(self.gridtot2.Destroy)
        self.gridtot2 = GridScadTotAnag(ci(wdr.ID_PCFGRIDTOT2), self.dbscad, self.cfmix)
        
        if getattr(self, 'griddet', None):
#            self.griddet.Destroy()
            wx.CallAfter(self.griddet.Destroy)
        self.griddet = GridScadDet(ci(wdr.ID_PCFGRIDDET), self.dbscad)
        
        self.TestSplitterTot()
        self.TestSplitterAnag()
        
        for cid, col in ((wdr.ID_PANCOLSCAPAG, self.griddet._bcpag),
                         (wdr.ID_PANCOLSCAASC, self.griddet._bcasc),
                         (wdr.ID_PANCOLSCASCA, self.griddet._bcsca),
                         (wdr.ID_PANCOLSCAINA, self.griddet._bcina),
                         (wdr.ID_PANCOLSCAINP, self.griddet._bcinp)):
            ci(cid).SetBackgroundColour(col)
        
        self.gridtot2.Bind(gl.EVT_GRID_SELECT_CELL, self.OnPdcSelected)
        
    def OnCliFor(self, event):
        self.TestCliFor()
        event.Skip()
    
    def TestCliFor(self):
        def ci(x):
            return self.FindWindowById(x)
        c = ci(wdr.ID_PCFTIPCF)
        if c is not None:
            cf = "CF"[c.GetSelection()]
            tipana = self.dbtipa
            for cid in (wdr.ID_PCFPDC1, wdr.ID_PCFPDC2):
                pdc = ci(cid)
                pdc.SetFilter('id_tipo IN (%s)' % ','.join(
                    map(str, tipana.GetTipi(cf))))
                if pdc.IsIdErr():
                    pdc.SetValue(None)
    
    def OnSize(self, event):
        wx.CallAfter(self.TestSplitterAnag)
        event.Skip()
    
    def OnSetAgenteUpdate(self, event):
        self.ageupdate = bool(event.GetSelection())
        #self.UpdateGridAnag()
        event.Skip()
    
    def OnSetDetAnag(self, event):
        self.detanag = bool(event.GetSelection())
        self.TestSplitterAnag()
        event.Skip()
    
    def OnSetAgenteZonaRaggr(self, event):
        for cid in (wdr.ID_PCFRAGGRAGE, wdr.ID_PCFRAGGRZNA, wdr.ID_PCFCLIAGE):
            self.FindWindowById(cid).Enable(event.GetSelection())
        event.Skip()
    
    def OnSetAgenteRaggr(self, event):
        if event.GetSelection():
            self.FindWindowById(wdr.ID_PCFRAGGRZNA).SetValue(False)
        event.Skip()
    
    def OnSetZonaRaggr(self, event):
        if event.GetSelection():
            self.FindWindowById(wdr.ID_PCFRAGGRAGE).SetValue(False)
        event.Skip()
    
    def OnAgeZnaSelected(self, event):
        if not self.ageupdate and not self.znaupdate:
            return
        self.UpdateGridAnag(event.GetRow())
        event.Skip()
    
    def OnPdcSelected(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbscad.RowsCount():
            self.dbscad.MoveRow(row)
        self.griddet.UpdateGrid()
        event.Skip()
    
    def OnStampaRiep(self, event):
        self.StampaScadenzario(sintesi=True)
        event.Skip()
    
    def OnStampaDet(self, event):
        self.StampaScadenzario(singolo=True)
        event.Skip()
    
    def OnStampaTutto(self, event):
        cpp = aw.awu.MsgDialog(self, "Vuoi una sola anagrafica per ogni pagina?",
                               style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        self.dbscad._info.cpp = (cpp == wx.ID_YES)
        self.StampaScadenzario(singolo=False)
        event.Skip()
    
    def StampaScadenzario(self, singolo=False, sintesi=False):
        db = self.dbscad
        row = self.gridtot2.GetSelectedRows()[0]
        if row<db.RowsCount():
            db.MoveRow(row)
        nome = "Scadenzario clienti-fornitori"
        cn = lambda x: self.FindWindowByName(x)
        cf = cn('pcftipocf').GetValue()
        db._info.gruppo = ''
        db._info.clifor = ['Clienti', 'Fornitori']['CF'.index(cf)]
        if sintesi:
            nome = "Sintesi "+nome
            testrec = db
        else:
            testrec=db.mastro
        if cn('pcfraggrage').GetValue():
            nome += ' per agente'
        elif cn('pcfraggrzna').GetValue():
            nome += ' per zona'
        def setCPP(rptdef, dbt):
            groups = rptdef.lGroup
            for g in groups:
                if groups[g].name == 'sottoconto':
                    if self.dbscad._info.cpp:
                        snp = 'true'
                    else:
                        snp = 'false'
                    groups[g].isStartNewPage = snp
        rpt.Report(self, db, nome, testrec=testrec, 
                   noMove=singolo, exitOnGroup=singolo, startFunc=setCPP,
                   filtersPanel=self.FindWindowByName('filterspanel'))

    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        event.Skip()
        
    def UpdateFilters(self, warn=True):
        
        cn = self.FindWindowByName
        
        try:
            agedoc = cn('agentefrom').GetValue() == "D"
        except:
            agedoc = False
        
        self.OpenTables(agedoc)
        self.CreateGrids()
        
        pdc = self.dbscad
        pcf = pdc.sintesi
        cau = pcf.caus
        mpa = pcf.modpag
        age = pdc.anagcli.agente
        zna = pdc.anagcli.zona
        cat = pdc.anagcli.catana
        
        pdc.ClearFilters()
        
        if not self.UpdateFilters_SetPdcFilters(pdc, warn=warn):
            return
        
        try:
            mdip = cn('pcfmaxdatincpag').GetValue()
        except:
            mdip = None
        pdc.ClearPcfFilters(mdip)
        
        for tab, name, field, pcfrel in ((pdc, 'pcfpdc',    'descriz', 0),
                                         (cau, 'pcfcau',    'codice',  1),
                                         (mpa, 'pcfmodpag', 'codice',  1),
                                         (pcf, 'pcfdatdoc', 'datdoc',  1),
                                         (pcf, 'pcfdatsca', 'datscad', 1),
                                         (age, 'pcfage',    'codice',  0),
                                         (zna, 'pcfzona',   'codice',  0),
                                         (cat, 'pcfcatana', 'codice',  0),
                                         ):
            tabname = tab.GetTableAlias()
            c1, c2 = map(cn, (name+'1', name+'2'))
            if c1 is not None and c2 is not None:
                if field == 'codice':
                    def f(x): return x.GetValueCod()
                elif field == 'descriz':
                    def f(x): return x.GetValueDes()
                else:
                    def f(x): return x.GetValue()
                v1, v2 = [f(cn(x)) for x in (name+'1', name+'2')]
                if v1 or v2:
                    if pcfrel:
                        f = pdc.AddPcfFilter
                    else:
                        f = pdc.AddFilter
                    stdf = True
                    if name == 'pcfage' and agedoc:
                        c = """(   SELECT age.codice
                                     FROM contab_s sca
                                     JOIN contab_h reg ON reg.id=sca.id_reg
                                LEFT JOIN movmag_h doc ON doc.id_reg=reg.id
                                LEFT JOIN agenti   age ON age.id=doc.id_agente
                                    WHERE sca.id_pcf=sintesi.id AND reg.id_regiva IS NOT NULL
                                    LIMIT 1)"""
                        if v1 == v2:
                            f('%s=%%s' % c, v1)
                        else:
                            if v1:
                                f('%s>=%%s' % c, v1)
                            if v2:
                                f('%s<=%%s' % c, v2)
                        stdf = False
                    if stdf:
                        if v1 == v2:
                            f('%s.%s=%%s' % (tabname, field), v1)
                        else:
                            if v1:
                                f('%s.%s>=%%s' % (tabname, field), v1)
                            if v2:
                                f('%s.%s<=%%s' % (tabname, field), v2)
        
        #test banca pagamento
        c = cn('pcfbancapag')
        if c is not None:
            if pcfrel:
                f = pdc.AddPcfFilter
            else:
                f = pdc.AddFilter
            bp = c.GetValue()
            nb = cn('pcfnobancapag').GetValue()
            anag = pdc.anag.GetTableAlias()
            if nb:
                f('%s.id_bancapag IS NULL' % anag)
            elif bp:
                f('%s.id_bancapag=%s' % (anag, bp))
        
        if cn('pcfnozero').IsChecked():
            pdc.AddPcfFilter('sintesi.imptot<>sintesi.imppar')
        if cn('pcfsolins').IsChecked():
            pdc.AddPcfFilter('sintesi.insoluto=1')
        
        ra = None
        c = cn('pcfraggrage')
        if c:
            ra = c.GetValue()
            if ra:
                if cn('agentefrom').GetValue() == "A":
                    m = 'anag'
                else:
                    m = 'doc'
                self.SetAgenteMode(m)
        if ra:
            self.gridtot1.SetGridMode('agente')
        
        c = cn('pcfraggrzna')
        if c:
            rz = c.GetValue()
            if rz:
                self.gridtot1.SetGridMode('zona')
        else:
            rz = None
        pdc.ClearOrders()
        if cn('pcforder').GetValue() == "C":
            if ra:
                if self.agente_mode == 'anag':
                    pdc.AddOrder('agente.codice')
                else:
                    pdc.AddOrder('(agecod)')
            elif rz:
                pdc.AddOrder('zonacli.codice')
            pdc.AddOrder('tipana.tipo')
            pdc.AddOrder('codice')
        else:
            if ra:
                if self.agente_mode == 'anag':
                    pdc.AddOrder('agente.descriz')
                else:
                    pdc.AddOrder('(agedes)')
            elif rz:
                pdc.AddOrder('zonacli.descriz')
            pdc.AddOrder('tipana.tipo')
            pdc.AddOrder('descriz')
        
        pdc.mastro.ClearOrders()
        pdc.mastro.AddOrder('datscad')
        
        pdc.sintesi.ClearHavings()
        if cn('pcfnozero').IsChecked():
            pdc.sintesi.AddHaving("SUM(sintesi.imptot-sintesi.imppar)<>0")
        if cn('pcfsolins').IsChecked():
            pdc.sintesi.AddHaving("COUNT(sintesi.insoluto)>0")
        if agedoc:
            #il filtro sugli agenti, se presi dal documento, vanno messi nella clausola HAVING
            #in quanto reperiti tramite colonne aggiuntive con loro specifica clausola SELECT
            v1 = cn('pcfage1').GetValueCod()
            v2 = cn('pcfage2').GetValueCod()
            if v1 or v2:
                if v1 == v2:
                    h = 'agecod="%s"' % v1
                else:
                    h = []
                    if v1:
                        h.append('agecod>="%s"' % v1)
                    if v2:
                        h.append('agecod<="%s"' % v2)
                    h = ' AND '.join(h)
                pdc.sintesi.AddHaving(h)
        
        ci = lambda x: self.FindWindowById(x)
        if ra or rz:
            self.UpdateGridAgenti(ra, rz)
            try:
                self.gridtot1.SelectRow(0)
            except:
                pass
        
        if not self.ageupdate and not self.znaupdate:
            self.UpdateGridAnag()
        
        self.TestSplitterTot()
    
    def UpdateFilters_SetPdcFilters(self, pdc, warn=True):
        tipana = self.FindWindowByName('pcftipocf').GetValue()
        pdc.AddFilter(r"tipana.tipo=%s", tipana)
        pdc.anag = [pdc.anagcli,pdc.anagfor]["CF".index(tipana)]
        return True
    
    def TestSplitterTot(self):
        ci = lambda x: self.FindWindowById(x)
        ca = ci(wdr.ID_PCFRAGGRAGE)
        cz = ci(wdr.ID_PCFRAGGRZNA)
        if ca and cz and (ca.GetValue() or cz.GetValue()):
            pos = 120
            grv = .5
        else:
            pos = 1
            grv = 0
        split = ci(wdr.ID_PCFTOTZONE)
        split.SetSashPosition(pos)
        split.SetSashGravity(grv)
    
    def TestSplitterAnag(self):
        ci = lambda x: self.FindWindowById(x)
        split = ci(wdr.ID_PCFGRIDZONE)
        if self.detanag:
            pos = 330
            grv = .5
        else:
            pos = split.GetParent().GetClientSize()[0]-1
            grv = 0
        split.SetSashPosition(pos)
        split.SetSashGravity(grv)
    
    def UpdateGridAgenti(self, ra, rz):
        if ra:
            if self.agente_mode == 'anag':
                col = 'agente.id'
            else:
                col = 'agecod'
        elif rz:
            col = 'zonacli.id'
        dbscad = self.dbscad
        dbscad._info.group.groups[0][0] = col
        dbscad._info.group.groups[1][0] = '0.0'
        wx.BeginBusyCursor()
        try:
            if not dbscad.Retrieve():
                awc.util.MsgDialog(self,\
                                   "Problema in lettura dati:\n\n%s"\
                                   % repr(dbscad.GetError()))
        finally:
            wx.EndBusyCursor()
        self.gridtot1.ChangeData(copy.deepcopy(dbscad.GetRecordset()))

    def UpdateGridAnag(self, row=None):
        dbscad = self.dbscad
        gridana = self.gridtot2
        parms = []
        if self.ageupdate:
            gridage = self.gridtot1
            rsa = gridage.GetTable().data
            if row is None:
                row = gridage.GetSelectedRows()[0]
            if row >= len(rsa):
                return
            cn = lambda db, col: db._GetFieldIndex(col, inline=True)
            if self.agente_mode == 'anag':
                col = cn(dbscad.anagcli.agente, 'id')
                ageid = rsa[row][col]
                if ageid is not None:
                    parms.append(r'agente.id=%s')
                    parms.append(ageid)
            else:
                col = cn(dbscad, 'ageid')
                ageid = rsa[row][col]
                f = dbscad.sintesi._info.group.filters
                for n, h in enumerate(f):
                    if 'ageid=' in h[0]:
                        del f[n]
                        break
                if ageid is not None:
                    dbscad.sintesi.AddHaving(r'ageid=%s', ageid)
        elif self.znaupdate:
            gridzna = self.gridtot1
            rsz = gridzna.GetTable().data
            if row is None:
                row = gridzna.GetSelectedRows()[0]
            if row >= len(rsz):
                return
            cn = lambda db, col: db._GetFieldIndex(col, inline=True)
            col = cn(dbscad.anagcli.zona, 'id')
            znaid = rsz[row][col]
            if znaid is not None:
                parms.append(r'zonacli.id=%s')
                parms.append(znaid)
        g = dbscad._info.group.groups[0][0]
        dbscad._info.group.groups[0][0] = '0.0'
        dbscad._info.group.groups[1][0] = '0.0'
        err = False
        wx.BeginBusyCursor()
        try:
            if not dbscad.Retrieve(*parms):
                awc.util.MsgDialog(self,\
                                   "Problema in lettura dati:\n\n%s"\
                                   % repr(dbscad.GetError()))
                err = True
            if not err:
                self.UpdateTotals()
                dbscad._info.group.groups[0][0] = g
                dbscad._info.group.groups[1][0] = 'pdc.id'
                if not dbscad.Retrieve(*parms):
                    awc.util.MsgDialog(self,\
                                       "Problema in lettura dati:\n\n%s"\
                                       % repr(dbscad.GetError()))
                    err = True
            if not err:
                gridana.ChangeData(dbscad.GetRecordset())
        finally:
            wx.EndBusyCursor()
    
    def UpdateTotals(self):
        pdc = self.dbscad
        sintesi = pdc.sintesi
        for name, total in (\
            ('cas1', sintesi.total_cont_scaduto),\
            ('cas2', sintesi.total_cont_ascadere),\
            ('cas3', sintesi.total_cont_ins_scaduto),\
            ('bon1', sintesi.total_bonif_scaduto),\
            ('bon2', sintesi.total_bonif_ascadere),\
            ('bon3', sintesi.total_bonif_ins_scaduto),\
            ('rib1', sintesi.total_riba_scaduto),\
            ('rib2', sintesi.total_riba_ascadere),\
            ('rib3', sintesi.total_riba_ins_scaduto),\
            ('tot1', \
             (sintesi.total_cont_scaduto  or 0)+\
             (sintesi.total_bonif_scaduto or 0)+\
             (sintesi.total_riba_scaduto  or 0)),\
            ('tot2', \
             (sintesi.total_cont_ascadere  or 0)+\
             (sintesi.total_bonif_ascadere or 0)+\
             (sintesi.total_riba_ascadere  or 0)),\
            ('tot3', \
             (sintesi.total_cont_ins_scaduto  or 0)+\
             (sintesi.total_bonif_ins_scaduto or 0)+\
             (sintesi.total_riba_ins_scaduto  or 0)),\
            ):
            self.FindWindowByName("pcf%s" % name).SetValue(total)


# ------------------------------------------------------------------------------


class ScadenzarioFrame(aw.Frame):
    """
    Frame Scadenzario clienti/fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ScadenzarioPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ScadenzarioGruppoPanel(ScadenzarioPanel):

    WdrFunc = wdr.ScadenzarioGruppoFunc
    cfmix = True

    def StampaScadenzario(self, singolo=False, sintesi=False):
        def cn(x):
            return self.FindWindowByName(x)
        db = self.dbscad
        row = self.gridtot2.GetSelectedRows()[0]
        if row<db.RowsCount():
            db.MoveRow(row)
        nome = "Scadenzario clienti-fornitori di gruppo"
        cn = lambda x: self.FindWindowByName(x)
        gr = cn('scadgrp').GetValue()
        db._info.gruppo = cn('scadgrp').GetValueDes()
        db._info.clifor = ''
        if sintesi:
            nome = "Sintesi "+nome
            testrec = db
        else:
            testrec=db.mastro
        if gr is None and cn('pcfraggrage').GetValue():
            nome += ' per agente'
        rpt.Report(self, db, nome, testrec=testrec, 
                   noMove=singolo, exitOnGroup=singolo)
    
    def UpdateFilters_SetPdcFilters(self, pdc, warn=True):
        grp = self.FindWindowByName('scadgrp').GetValue()
        if grp is None:
            if warn:
                aw.awu.MsgDialog(self, "Selezionare un gruppo")
            return False
        pdc.AddFilter(r"""
        (anagcli.id_scadgrp=%s) OR (anagfor.id_scadgrp=%s)""", grp, grp)
        return True


# ------------------------------------------------------------------------------


class ScadenzarioGruppoFrame(aw.Frame):
    """
    Frame Scadenzario clienti/fornitori di gruppo.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_GRUPPO
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ScadenzarioGruppoPanel(self, -1))
        self.CenterOnScreen()
