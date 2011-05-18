#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/prodint.py
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

import anag.prod as prod
import anag.prod_wdr as wdr
import magazz.prodmas as prodmas
import magazz.prodpro as prodpro

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb
import magazz.dbtables as dbm
import magazz.stat.dbtables as dbs

import awc.controls.windows as aw
import awc.controls.notebook as awnb

import report as rpt


FRAME_TITLE = "Interrogazione prodotti"


TAB_ANAG =   0
TAB_LIST =   1
TAB_MASTRO = 2
TAB_EVAS =   3
TAB_PROGR =  4


class _ProdInterrMixin(object):
    baseclass = None
    panmastro = None
    panevas = None
    panprogr = None
    panstat = None
    
    def __init__(self, baseclass=None):
        if baseclass is None:
            baseclass = prod.ProdPanel
        self.baseclass = baseclass
    
    def InitControls(self, *args, **kwargs):
        self.baseclass.InitControls(self, *args, **kwargs)
        
        nb = self.FindWindowById(wdr.ID_WORKZONE)
        
        if getattr(Env.Azienda.Login.userdata, 'can_magazzint', True):
            nb.AddPage(aw.Panel(nb), "Mastro movimenti")
            nb.AddPage(aw.Panel(nb), "Evasioni")
            nb.AddPage(aw.Panel(nb), "Giacenze e progressivi")
            nb.AddPage(aw.Panel(nb), "Statistiche")
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanging, nb)
    
    def UpdateDataControls(self, *args, **kwargs):
        self.baseclass.UpdateDataControls(self, *args, **kwargs)
        self.TestForUpdates()

    def TestForUpdates(self, ntab=None):
        
        nb = self.FindWindowById(wdr.ID_WORKZONE)
        if ntab is None:
            ntab = nb.GetSelection()
        stab = nb.GetPageText(ntab)
        
        if   "movim" in stab.lower():
            #Selezionato il tab mastro
            if self.panmastro is None:
                #non è ancora presente, lo creo al volo
                wx.BeginBusyCursor()
                self.Freeze()
                try:
                    parent = nb.GetPage(ntab)
                    self.panmastro = prodmas.ProdMastroPanel(parent, self)
                    self.panmastro.gridmov.UpdateMov(retrieve=False)
                    parent.AddSizedPanel(self.panmastro)
                    nb.ReSize()
                finally:
                    self.Thaw()
                    wx.EndBusyCursor()
            #lo aggiorno
            self.panmastro.GridUpdate(prod=self.db_recid)
            
        elif "evas" in stab.lower():
            #Selezionato il tab evasioni
            if self.panevas is None:
                #non è ancora presente, lo creo al volo
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panevas = prodmas.ProdMastroEvaPanel(parent, self)
                    parent.AddSizedPanel(self.panevas)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            #lo aggiorno
            self.panevas.GridUpdate(prod=self.db_recid)
            
        elif "progress" in stab.lower():
            #selezionato il tab progressivi
            if self.panprogr is None:
                #non è ancora presente, lo creo al volo
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panprogr = prodpro.ProdProgrPanel(parent, self)
                    parent.AddSizedPanel(self.panprogr)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            #lo aggiorno
            self.panprogr.GridUpdate(prod=self.db_recid)
            
        elif "statistic" in stab.lower():
            #selezionato il tab progressivi
            if self.panstat is None:
                #non è ancora presente, lo creo al volo
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panstat = ProdIntMagPanel(parent)#, self)
                    parent.AddSizedPanel(self.panstat)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            #lo aggiorno
            self.panstat.UpdateGrids(proid=self.db_recid)
        
        return nb

    def OnPageChanging(self, event):
        nb = event.GetEventObject()
        self.TestForUpdates(event.GetSelection())
        event.Skip()

    
# ------------------------------------------------------------------------------


class ProdInterrPanel(prod.ProdPanel, _ProdInterrMixin):
    """
    Pannello interrogazioni prodotto.
    Deriva dalla classe di gestione anagrafica, nella quale il NoteBook di
    lavoro viene implementato con le seguenti pagine:
        - magazz.prodmas.ProdMastroPanel
        - magazz.prodpro.ProdProgrPanel
    """
    
    def __init__(self, *args, **kwargs):
        prod.ProdPanel.__init__(self, *args, **kwargs)
        _ProdInterrMixin.__init__(self)
    
    def InitControls(self, *args, **kwargs):
        _ProdInterrMixin.InitControls(self, *args, **kwargs)
    
    def UpdateDataControls(self, *args, **kwargs):
        _ProdInterrMixin.UpdateDataControls(self, *args, **kwargs)
    
    def DisplayAnag(self):
        self._DisplayTab(TAB_ANAG)

    def DisplayListini(self):
        self._DisplayTab(TAB_LIST)

    def DisplayMastro(self):
        self._DisplayTab(TAB_MASTRO)

    def DisplayEvasioni(self):
        self._DisplayTab(TAB_EVAS)

    def DisplayProgressivi(self):
        self._DisplayTab(TAB_PROGR)

    def _DisplayTab(self, tab):
        try:
            self.FindWindowById(wdr.ID_WORKZONE).SetSelection(tab)
        except:
            pass


# ------------------------------------------------------------------------------


class ProdInterrFrame(prod.ga._AnagFrame):
    """
    Frame Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        prod.ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ProdInterrPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ProdInterrDialog(prod.ga._AnagDialog):
    """
    Dialog Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        prod.ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ProdInterrPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


from magazz.stat.fatpro import FatturatoProCliGrid

class ProdIntMagFatCliGrid(FatturatoProCliGrid):
    
    def GetColDef(self):
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _VAL = bt.GetValIntMaskInfo()
        
        mov = self.dbfat
        pro = mov.prod
        pdc = mov.doc.pdc
        
        return (\
            ( 60, (cn(pdc, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(pdc, 'descriz'),          "Cliente",   _STR, False)),
            ( 90, (cn(mov, 'total_statqtafat'), "Qta",       _QTA, False)),
            (110, (cn(mov, 'total_statvalfat'), "Fatturato", _VAL, False)),
            (  1, (cn(pdc, 'id'),               "#cli",      _STR, False)),
        )
    
    def _SetFitColumn(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class ProdIntMagPanel(aw.Panel):
    
    ordinverso = False
    ftalastpdc = None
    fatlastpdc = None
    
    def __init__(self, parent):
        aw.Panel.__init__(self, parent)
        wdr.ProdIntMagPanelFunc(self)
        self.dbfatcli = dbs.FatturatoProCli()
        
        def cn(x):
            return self.FindWindowByName(x)
        
        cn('_fatdatmin').SetValue(Env.DateTime.Date(
            Env.Azienda.Login.dataElab.year,1,1))
        cn('_fatdatmax').SetValue(Env.Azienda.Login.dataElab)
        
        self.gridfatcli = ProdIntMagFatCliGrid(cn('pangridfatcli'), 
                                                  self.dbfatcli)
        
        for name, func in (('_btnfatupd', self.OnUpdateFilters),
                           ('_btnfatprt', self.OnStampa)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged,
                  id=wdr.ID_STATZONE)
    
    def OnMagPrint(self, event):
        self.MagPrint()
        event.Skip()
    
    def MagPrint(self):
        ci = lambda x: self.FindWindowById(x)
        sel = ci(wdr.ID_WORKZONE).GetSelection()
        label = ci(wdr.ID_WORKZONE).GetPageText(sel).lower()
        if 'prodotti' in label:
            rpt.Report(self, self.dbfta, 'Scheda vendite cliente')
        elif 'documenti' in label:
            rpt.Report(self, self.dbdoc, 'Lista documenti magazzino')
        elif 'movimenti' in label:
            self.dbmov.pro = self.dbmov.prod
            rpt.Report(self, self.dbmov, 'Lista movimenti magazzino')
        elif 'fatturato' in label:
            self.FatturatoPrint()
    
    def FatturatoPrint(self):
        d = FatturatoPrintSel(self)
        ok = d.ShowModal() == wx.ID_OK
        d.Destroy()
        if ok:
            if d.report_type == 'cat':
                db = self.dbfatcat
                report = 'Fatturato cliente per categoria merce'
            elif d.report_type == 'pro':
                db = self.dbfatpro
                report = 'Fatturato cliente per prodotto'
            else:
                db = None
            if db:
                rpt.Report(self, db, report)
            
    def OnPageChanged(self, event):
        self.UpdateFilters(event.GetSelection())
        event.Skip()
    
    def TestSelDoc(self):
        ci = lambda x: self.FindWindowById(x)
        cn = lambda x: self.FindWindowByName(x)
        #page = ci(wdr.ID_WORKZONE).GetSelection()
        #enable = not 'prodotti fatturati' in \
               #ci(wdr.ID_WORKZONE).GetPageText(page).lower()
        #for name in 'id_magazz,id_tipdoc,nodocacq,nodocann'.split(','):
            #cn(name).Enable(enable)
        
    def GetOrdInverso(self):
        return self.ordinverso
    
    def SetOrdInverso(self, oi=True):
        self.ordinverso = oi
    
    def OnOrdInverso(self, event):
        self.SetOrdInverso(int(event.GetSelection()))
        event.Skip()
    
    def OnPageChanging(self, event):
        self.UpdateFilters(event.GetSelection())
        #self.TestSelDoc()
        event.Skip()
    
    def UpdateGrids(self, proid):
        self.proid = proid
        self.UpdateFilters()
    
    def OnStampa(self, event):
        self.StampaFatturato()
        event.Skip()
    
    def StampaFatturato(self):
        db = self.dbfatcli
        db._info.datmin, db._info.datmax =\
          map(lambda x: self.FindWindowByName(x).GetValue(), 
              '_fatdatmin _fatdatmax'.split())
        rpt.Report(self, db, "Fatturato Prodotti per Cliente")
    
    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        event.Skip()
    
    def UpdateFilters(self, sel=None):
        
        ci = lambda x: self.FindWindowById(x)
        cn = lambda x: self.FindWindowByName(x)
        
        if sel is None:
            sel = ci(wdr.ID_STATZONE).GetSelection()
        label = ci(wdr.ID_STATZONE).GetPageText(sel).lower()
        if  'fatturato' in label:
            self.UpdateFatturato()
            return
    
    def UpdateFatturato(self):
        self.UpdateFatturatoClienti()
    
    def GetFatturatoFilter(self):
        def cn(x):
            return self.FindWindowByName(x)
        fatcli = self.dbfatcli
        self.fatlastpro = self.proid
        filtmov = []
        for name, op in (('_fatdatmin', '>='),
                         ('_fatdatmax', '<=')):
            val = cn(name).GetValue()
            if val:
                filtmov.append(('doc.datreg%s%%s' % op, val))
        return filtmov
    
    def UpdateFatturatoClienti(self, filter=None):
        fatcli = self.dbfatcli
        fatcli.ClearBaseFilters()
        filtmov = self.GetFatturatoFilter()
        if filtmov:
            for f, v in filtmov:
                fatcli.AddBaseFilter(f, v)
        #if filter:
            #for f in filter:
                #fatcat.AddBaseFilter(f)
        tipord = self.FindWindowByName('_fatorder').GetSelection()
        fatcli.ClearOrders()
        if   tipord == 1: #minimo
            fatcli.AddOrder('(total_statvalfat)', adb.ORDER_ASCENDING)
        elif tipord == 2: #massimo
            fatcli.AddOrder('(total_statvalfat)', adb.ORDER_DESCENDING)
        fatcli.AddOrder('pdc.descriz')
        fatcli.Retrieve('prod.id=%s', self.proid)
        self.gridfatcli.ResetView()
