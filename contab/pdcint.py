#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/pdcint.py
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

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc.layout.gestanag as ga
import anag.pdcrel_wdr as rel_wdr
import contab.pdcint_wdr as wdr

import contab
import contab.dataentry as ctb
import contab.dbtables as dbc
from cfg.dbtables import ProgrEsercizio

import magazz.dbtables as dbm
import magazz.pdcint as magint

import anag.casse
import anag.banche
import anag.effetti
import anag.clienti
import anag.fornit
import anag.pdc

import awc
import awc.controls.windows as aw
import awc.controls.notebook as awnb

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import stormdb as adb

import report as rpt

import locale
import os, tempfile

from contab.pcf import PcfDialog


FRAME_TITLE_CAS = "Interroga Cassa"
FRAME_TITLE_BAN = "Interroga Banche"
FRAME_TITLE_CLI = "Interroga Clienti"
FRAME_TITLE_FOR = "Interroga Fornitori"
FRAME_TITLE_EFF = "Interroga Effetti"
FRAME_TITLE_PDC = "Interroga Sottoconti"


class _PdcInterrFrameMixin(object):
    def DisplayTab(self, tabname):
        nb = self.FindWindowById(rel_wdr.ID_WORKZONE)
        for pn in range(nb.GetPageCount()):
            if tabname.lower() in nb.GetPageText(pn).lower():
                nb.SetSelection(pn)
                break


# ------------------------------------------------------------------------------


class GridMastro(dbglib.DbGridColoriAlternati):
    
    def __init__(self, *args, **kwargs):
        
        parent = args[0]
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size)
        
        self.dbmas = dbc.PdcMastro()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        pdc = self.dbmas
        mov = pdc.GetMastro()
        reg = mov.reg
        cau = reg.caus
        riv = reg.regiva
        pcp = mov.pdccp
        
        self.colsegno = cn(mov, 'segno')
        self.colcaues = cn(mov.reg.caus, 'esercizio')
        self.coltpreg = cn(mov.reg, 'tipreg')
        self.coltprig = cn(mov, 'tipriga')
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _FLV = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (cn(reg, "datreg"),    "Data reg.", _DAT, True )),
            ( 40, (cn(cau, "codice"),    "Cod.",      _STR, True )),
            (120, (cn(cau, "descriz"),   "Causale",   _STR, True )),
            ( 50, (cn(reg, "numdoc"),    "N.doc.",    _STR, True )),
            ( 80, (cn(reg, "datdoc"),    "Data doc.", _DAT, True )),
            ( 50, (cn(reg, "numiva"),    "Prot.",     _NUM, True )),
            ( 35, (cn(riv, "codice"),    "C.",        _STR, True )),
            (100, (cn(riv, "descriz"),   "Reg. IVA",  _STR, True )),
            (110, (cn(mov, "dare"),      "Dare",      _FLV, True )),
            (110, (cn(mov, "avere"),     "Avere",     _FLV, True )),
            ( 50, (cn(pcp, "codice"),    "Cod.",      _STR, True )),
            (220, (cn(pcp, "descriz"),   "C/Partita", _STR, True )),
            ( 35, (cn(reg, "esercizio"), "Es.",       _STR, True )),
            (240, (cn(mov, "note"),      "Note",      _STR, True )),
            (  1, (cn(reg, "id"),        "#reg",      _STR, True )),
            (  1, (cn(mov, "id"),        "#mov",      _STR, True )),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = mov.GetRecordset()
        
        self.SetData( rs, colmap, canedit, canins)
        
        self._fgcold, self._fgcola = contab.GetColorsDA()
        self._fgcoli = Env.Azienda.Colours.GetColour('grey40')
        
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(9, (2, 7))
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        rsmov = self.dbmas.GetMastro().GetRecordset()
        if row<len(rsmov):
            if (rsmov[row][self.coltprig] or ' ') in 'IO':
                fgcol = self._fgcoli
            else:
                if rsmov[row][self.colsegno] == 'D':
                    fgcol = self._fgcold
                else:
                    fgcol = self._fgcola
            attr.SetTextColour(fgcol)
            try:
                f = attr.GetFont()
                if rsmov[row][self.colcaues] == '1':
                    f.SetStyle(wx.FONTSTYLE_ITALIC)
                else:
                    f.SetStyle(wx.FONTSTYLE_NORMAL)
                attr.SetFont(f)
            except:
                pass
        return attr
    
    def OnDblClick(self, event):
        pdc = self.dbmas
        mov = pdc.GetMastro()
        row = event.GetRow()
        mov.MoveRow(row)
        try:
            cls = contab.RegConDialogClass(mov.id_reg)
            if cls:
                wx.BeginBusyCursor()
                dlg = cls(aw.awu.GetParentFrame(self))
                dlg.SetOneRegOnly(mov.id_reg)
                wx.EndBusyCursor()
                if dlg.ShowModal() in (ctb.REG_MODIFIED, ctb.REG_DELETED):
                    evt = contab.RegChangedEvent(contab._evtREGCHANGED, 
                                                 self.GetId())
                    evt.SetEventObject(self)
                    evt.SetId(self.GetId())
                    #self.GetEventHandler().ProcessEvent(evt)
                    self.GetEventHandler().AddPendingEvent(evt)
                dlg.Destroy()
                event.Skip()
        except:
            pass
    
    def UpdateGrid(self):
        self.ChangeData(self.dbmas.GetMastro().GetRecordset())


# ------------------------------------------------------------------------------


class _PdcInterrMixin(object):
    panel = None
    panmastro = None
    pref = None
    
    def __init__(self, baseclass):
        object.__init__(self)
        self.baseclass = baseclass
        self.preftab = 0
    
    def SetPref(self, pref):
        self.preftab = pref
    
    def InitControls(self, *args, **kwargs):
        self.baseclass.InitControls(self, *args, **kwargs)
        
        ci = lambda x: self.FindWindowById(x)
        nb = ci(rel_wdr.ID_WORKZONE)
        
        if getattr(Env.Azienda.Login.userdata, 'can_contabint', True):
            p = aw.Panel(nb)
            nb.AddPage(p, "Mastro")
            self.preftab = nb.GetPageCount()
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanging, nb)
    
    def UpdateDataControls(self, *args, **kwargs):
        self.baseclass.UpdateDataControls(self, *args, **kwargs)
        self.TestForUpdates()
    
    def OnPageChanging(self, event):
        nb = event.GetEventObject()
        self.TestForUpdates(event.GetSelection())
        event.Skip()
    
    def TestForUpdates(self, ntab=None, mastroaddfilter=None):
        nb = self.FindWindowById(rel_wdr.ID_WORKZONE)
        if ntab is None:
            ntab = nb.GetSelection()
            self.preftab = ntab
        if   "Mastro" in nb.GetPageText(ntab):
            if self.panmastro is None:
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panmastro = PdcMastroPanel(parent)
                    parent.AddSizedPanel(self.panmastro)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            self.panmastro.UpdateGrid(pdcid=self.db_recid, addfilter=mastroaddfilter)

    def DisplayScheda(self):
        if self.db_recno == ga.NEW_RECORD or self.preftab is None:
            ga.AnagPanel.DisplayScheda(self)
        else:
            self._DisplayPage(self.preftab)
            self.SetFirstFocus()


# ------------------------------------------------------------------------------


VIEW_SALDI = 0
VIEW_PROGR = 1

VIEW_MODE = VIEW_SALDI

class PdcMastroPanel(aw.Panel):
    
    def __init__(self, parent):
        aw.Panel.__init__(self, parent)
        wdr.PdcMastroFunc(self)
        
        ci = lambda x: self.FindWindowById(x)
        
        ci(wdr.ID_MASSEGNO).SetSelection(0)
        
        pp = ci(wdr.ID_MASPANGRID)
        self.gridmas = GridMastro(pp)
        self.viewmode = VIEW_MODE
        self.pdcid = None
        self.UpdateButtonView()
        
        pe = ProgrEsercizio()
        ec = pe.GetEsercizioInCorso()
        ds = pe.GetEsercizioDates(ec)[0]
        self.FindWindowById(wdr.ID_MAS_DATINI).SetValue(ds)
        self.gridmas.dbmas.SetDateStart(ds)
        
        for cid, col in ((wdr.ID_PANCOLMASD, self.gridmas._fgcold),
                         (wdr.ID_PANCOLMASA, self.gridmas._fgcola),
                         (wdr.ID_PANCOLMASI, self.gridmas._fgcoli),):
            ci(cid).SetBackgroundColour(col)
        
        for evt, func, cid in (
            (wx.EVT_BUTTON, self.OnUpdateFilters, wdr.ID_MASBTNUPD),
            (wx.EVT_BUTTON, self.OnChangeTotals,  wdr.ID_MASBTNPRO),
            (wx.EVT_BUTTON, self.OnStampa,        wdr.ID_MASBTNPRT),
            (wx.EVT_BUTTON, self.OnResetImporti,  wdr.ID_MASRESET)):
            self.Bind(evt, func, id=cid)
        
        self.Bind(contab.EVT_REGCHANGED, self.OnUpdateFilters)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        self.Bind(wx.EVT_CHOICE, self.OnEsercizioChanged, cn('masesercizio'))
        
        self.HelpBuilder_SetDir('anag.pdcrel')
        self.SetName('MastroPage')
    
    def OnResetImporti(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        for name in 'maslimimp1 maslimimp2'.split():
            cn(name).SetValue(0)
        cn('massegno').SetSelection(0)
        event.Skip()
    
    def OnEsercizioChanged(self, event):
        cn = self.FindWindowByName
        pe = ProgrEsercizio()
        ds = pe.GetEsercizioDates(cn('masesercizio').GetValue() or pe.GetEsercizioInCorso())[0]
        cn('masdatini').SetValue(ds)
        self.UpdateFilters()
        self.UpdateGrid(self.pdcid)
        event.Skip()
    
    def OnStampa(self, event):
        self.StampaMastrino()
        event.Skip()
    
    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        self.UpdateGrid(self.pdcid)
        event.Skip()
    
    def OnChangeTotals(self, event):
        self.viewmode = 1-self.viewmode
        self.UpdateButtonView()
        self.UpdateTotals()
        event.Skip()
    
    def UpdateButtonView(self):
        if self.viewmode == VIEW_SALDI:
            label = "Progressivi"
        else:
            label = "Saldi"
        self.FindWindowById(wdr.ID_MASBTNPRO).SetLabel(label)
    
    def UpdateFilters(self, addfilter=None):
        
        cn = lambda x: self.FindWindowByName(x)
        
        pdc = self.gridmas.dbmas
        pdc.SetRigheIva(cn('masincrigiva').GetValue())
        if addfilter:
            pdc.GetMastro().AddBaseFilter(addfilter)
        pdc.ClearMovFilters()
        
        e, ds, de = map(lambda x: cn(x).GetValue(), 'masesercizio masdatini masdatmov'.split())
        pdc.SetDateStart(ds, esercizio=e)
        pdc.SetDateEnd(de)
        pdc.SetEsercizio(e)
        
        for tab, field, name, op in (\
            ("reg",    "id_caus",   "masid_caus",   "=" ),\
            ("reg",    "id_regiva", "masid_regiva", "=" ),\
            ("mov",    "id_pdccp",  "masid_pdccp",  "=" )):
            val = cn(name).GetValue()
            if val is not None:
                pdc.AddMovFilter("%s.%s%s%%s" % (tab, field, op), val)
        
        tipreg_filt = []
        if cn('mastipregacq').IsChecked():
            tipreg_filt.append('regiva.tipo="A"')
        if cn('mastipregven').IsChecked():
            tipreg_filt.append('regiva.tipo="V"')
        if cn('mastipregcor').IsChecked():
            tipreg_filt.append('regiva.tipo="C"')
        if cn('mastipregniv').IsChecked():
            tipreg_filt.append('reg.id_regiva IS NULL')
        if tipreg_filt:
            tipreg_filt = ' OR '.join(tipreg_filt)
            pdc.AddMovFilter(tipreg_filt)
        
        for n, op in ((1, '>='),
                      (2, '<=')):
            v = cn('maslimimp%d'%n).GetValue()
            if v:
                pdc.AddMovFilter("mov.importo%s%%s" % op, v)
        s = cn('massegno').GetSelection()
        if s>0:
            pdc.AddMovFilter(r"mov.segno=%s", "DA"[s-1])
    
    def UpdateGrid(self, pdcid=None, addfilter=None):
        if True:#pdcid is not None:
            self.UpdateFilters(addfilter=addfilter)
            self.pdcid = pdcid
            db = self.gridmas.dbmas
            if not db.Get(pdcid):
                awc.util.MsgDialog("Problema in lettura dati:\n\n%s"\
                                   % db.GetError())
        self.gridmas.UpdateGrid()
        self.UpdateTotals()

    def UpdateTotals(self):
        scv = lambda x, y: self.FindWindowByName(x).SetValue(y)
        pdc = self.gridmas.dbmas
        totinid, totinia = pdc.GetProgrIni()
        totmovd, totmova = pdc.GetProgrMov()
        totfind, totfina = pdc.GetProgrTot()
        scv("masdatsal", pdc.GetLastRegDate())
        for tipo, dare, avere in (('ini', totinid, totinia),\
                                  ('mov', totmovd, totmova),\
                                  ('sal', totfind, totfina)):
            named = "mastot%sd" % tipo
            namea = "mastot%sa" % tipo
            if self.viewmode == VIEW_PROGR:
                scv(named, dare)
                scv(namea, avere)
            else:
                if dare >= avere:
                    scv(named, dare-avere); scv(namea, 0)
                else:
                    scv(named, 0); scv(namea, avere-dare)

    def StampaMastrino(self):
        db = self.gridmas.dbmas
        rpt.Report(self, db, "Mastro sottoconto", testrec=db.mov)


# ------------------------------------------------------------------------------


class ScadenzarioColorsGridMixin(object):
    
    def __init__(self, dbpcf):
        
        object.__init__(self)
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        self.colsca, self.colimp, self.colpar, self.colins =\
            [cn(dbpcf, x) for x in ('datscad',
                                    'imptot',
                                    'imppar',
                                    'insoluto')]
        
        self._bcpag, self._bcasc, self._bcsca,\
        self._bcina, self._bcinp, self._bctot =\
            [bc.GetColour(c) for c in ('forestgreen', #pagato
                                       'blue2',       #a scadere
                                       'orange4',     #scaduto
                                       'orangered',   #insoluto attivo
                                       'magenta2',    #insoluto pagato
                                       'blue4')]      #totali di colonna
    
    def ScadenzarioColorsGetAttr(self, rspcf, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        fgcol = bc.NORMAL_FOREGROUND
        if self.IsOnTotalRow(row):
            fgcol = self._bctot
        elif row<len(rspcf):
            rspcf = rspcf[row]
            pag = (abs(rspcf[self.colimp]-rspcf[self.colpar])<0.0001)
            ins = rspcf[self.colins]
            sca = rspcf[self.colsca]<Env.Azienda.Login.dataElab
            if pag:
                if ins:
                    fgcol = self._bcinp
                else:
                    fgcol = self._bcpag
            else:
                if ins:
                    fgcol = self._bcina
                else:
                    if sca:
                        fgcol = self._bcsca
                    else:
                        fgcol = self._bcasc
        attr.SetTextColour(fgcol)
        attr.SetReadOnly(True)
        return attr


# ------------------------------------------------------------------------------


class GridScadenzario(dbglib.DbGridColoriAlternati,
                      ScadenzarioColorsGridMixin):
    
    def __init__(self, parent, dbscad):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbscad = dbscad
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        pdc = self.dbscad
        pcf = pdc.GetPartite()
        cau = pcf.caus
        mpa = pcf.modpag
        
        ScadenzarioColorsGridMixin.__init__(self, pcf)
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL
        _FLV = bt.GetValIntMaskInfo()
        _RIB = _CHK+":1,0"
        
        cols = (\
            ( 80, (cn(pcf, "datscad"), "Scadenza",      _DAT, True )),
            ( -1, (cn(pcf, "riba"),    "R.B.",          _RIB, True )),
            ( 35, (cn(mpa, "codice"),  "Cod.",          _STR, True )),
            ( 90, (cn(mpa, "descriz"), "Mod.Pagamento", _STR, True )),
            ( 35, (cn(cau, "codice"),  "Cod.",          _STR, True )),
            ( 90, (cn(cau, "descriz"), "Causale",       _STR, True )),
            ( 80, (cn(pcf, "datdoc"),  "Data doc.",     _DAT, True )),
            ( 50, (cn(pcf, "numdoc"),  "Num.",          _STR, True )),
            (110, (cn(pcf, "saldo"),   "Saldo",         _FLV, True )),
            (240, (cn(pcf, "note"),    "Note",          _STR, True )),
            (110, (cn(pcf, "imptot"),  "Importo",       _FLV, False)),
            (110, (cn(pcf, "imppar"),  "Pareggiamento", _FLV, False)),
            (  1, (cn(pcf, "id"),      "#pcf",          _STR, False)),
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        nci = pcf._GetFieldIndex('imptot')
        ncp = pcf._GetFieldIndex('imppar')
        
        canedit = False
        canins = False
        
        rs = pcf.GetRecordset()
        
        self.SetData( rs, colmap, canedit, canins)
        
        self.AddTotalsRow(3,'Totali:',(cn(pcf, "saldo"),
                                       cn(pcf, "imptot"),
                                       cn(pcf, "imppar")))
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
#        self.SetFitColumn(-4) #note
        self.SetAnchorColumns(8, (3, 5))
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        rspcf = self.dbscad.GetPartite().GetRecordset()
        return self.ScadenzarioColorsGetAttr(rspcf, row, col, rscol, attr)
    
    def UpdateGrid(self):
        self.ChangeData(self.dbscad.GetPartite().GetRecordset())
    
    def OnDblClick(self, event):
        row = event.GetRow()
        if self.IsOnTotalRow(row):
            return
        pdc = self.dbscad
        pcf = pdc.GetPartite()
        pcf.MoveRow(row)
        wx.BeginBusyCursor()
        dlg = PcfDialog(self)
        dlg.SetPcf(pcf.id)
        wx.EndBusyCursor()
        if dlg.ShowModal() != 0:
            evt = contab.PcfChangedEvent(contab._evtPCFCHANGED, self.GetId())
            evt.SetEventObject(self)
            evt.SetId(self.GetId())
            self.GetEventHandler().AddPendingEvent(evt)
        dlg.Destroy()
        event.Skip()


# ------------------------------------------------------------------------------


class ScadenzarioColorsPanelMixin(object):
    
    def __init__(self, gridpcf):
        
        object.__init__(self)
        
        def ci(cid):
            return self.FindWindowById(cid)
        
        for cid, col in ((wdr.ID_PANCOLSCAPAG, gridpcf._bcpag),
                         (wdr.ID_PANCOLSCAASC, gridpcf._bcasc),
                         (wdr.ID_PANCOLSCASCA, gridpcf._bcsca),
                         (wdr.ID_PANCOLSCAINA, gridpcf._bcina),
                         (wdr.ID_PANCOLSCAINP, gridpcf._bcinp)):
            ci(cid).SetBackgroundColour(col)
        


# ------------------------------------------------------------------------------


_evtEMAILPREVIEW = wx.NewEventType()
EVT_EMAILPREVIEW = wx.PyEventBinder(_evtEMAILPREVIEW, 0)
class EmailPreviewEvent(wx.PyCommandEvent):
    email_id = None
    def SetEmailId(self, email_id):
        self.email_id = email_id
    def GetEmailId(self):
        return self.email_id


# ------------------------------------------------------------------------------


class CliForEmailsGrid(dbglib.DbGridColoriAlternati):
    
    emaid = None
    
    def __init__(self, parent, dbema):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbema = dbema
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        ema = self.dbema
        doc = ema.doc
        tpd = doc.tipdoc
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _DTM = gl.GRID_VALUE_DATETIME+":with:time"
        _CHK = gl.GRID_VALUE_BOOL
        
        cols = (\
            (140, (cn(ema, "datsend"), "Spedizione", _DTM, True )),
            ( 40, (cn(tpd, "codice"),  "Cod.",       _STR, True )),
            (100, (cn(tpd, "descriz"), "Documento",  _STR, True )),
            ( 50, (cn(doc, "numdoc"),  "Num.",       _NUM, True )),
            ( 80, (cn(doc, "datdoc"),  "Data",       _DAT, True )),
            (600, (cn(ema, "oggetto"), "Oggetto",    _STR, True )),
            (  1, (cn(ema, "id"),      "#ema",       _STR, False)),
            (  1, (cn(doc, "id"),      "#doc",       _STR, False)),
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(ema.GetRecordset(), colmap)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(5)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelected)
    
    def OnCellSelected(self, event):
        row = event.GetRow()
        ema = self.dbema
        if 0 <= row < ema.RowsCount():
            ema.MoveRow(row)
            if self.emaid != ema.id:
                evt = EmailPreviewEvent(_evtEMAILPREVIEW)
                evt.SetEmailId(ema.id)
                evt.SetEventObject(self)
                evt.SetId(self.GetId())
                self.GetEventHandler().AddPendingEvent(evt)
        event.Skip()


# ------------------------------------------------------------------------------


class CliForEmailsPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.DocsEmailFunc(self)
        self.pdcid = None
        cn = self.FindWindowByName
        self.dbema = dbc.SendedEmail()
        self.gridemail = CliForEmailsGrid(cn('pangridemail'), self.dbema)
        self.Bind(EVT_EMAILPREVIEW, self.OnPreview)
        self.Bind(wx.EVT_BUTTON, self.OnOpenPdf, cn('butemailopenpdf'))
    
    def OnOpenPdf(self, event):
        ema = self.dbema
        row = self.gridemail.GetSelectedRows()[0]
        if 0 <= row < ema.RowsCount():
            self.OpenPdf(ema.id)
            event.Skip()
    
    def OpenPdf(self, email_id):
        ema = adb.DbTable(bt.TABNAME_DOCSEMAIL, 'emails')
        if not ema.Get(email_id) or not ema.OneRow():
            return
        tmpfile = tempfile.NamedTemporaryFile(suffix='.pdf')
        tmpname = tmpfile.name
        tmpfile.close()
        wx.GetApp().AppendTempFile(tmpname)
        tmpfile = open(tmpname, 'wb')
        tmpfile.write(ema.documento)
        tmpfile.close()
        os.startfile(tmpname)
    
    def OnPreview(self, event):
        self.PreviewMessage(event.GetEmailId())
        event.Skip()
    
    def PreviewMessage(self, email_id):
        ema = adb.DbTable(bt.TABNAME_DOCSEMAIL, 'emails')
        ema.Get(email_id)
        cn = self.FindWindowByName
        cn('butemailopenpdf').Enable(ema.id is not None)
        for name, col in (('emailfrom', 'mittente'),
                          ('emailto',   'destinat'),
                          ('emaildate', 'datsend'),
                          ('emailbody', 'testo'),):
            v = getattr(ema, col)
            if hasattr(v, 'year'):
                v = ema.dita(v)
            c = cn(name)
            if hasattr(c, 'SetValue'):
                c.SetValue(v or '')
            else:
                c.SetLabel(v or '')
    
    def UpdateGrid(self, pdcid=None):
        if True:#pdcid is not None:
            self.pdcid = pdcid
            db = self.dbema
            if not db.Retrieve('emails.id_pdc=%s', pdcid):
                awc.util.MsgDialog(self,\
                                   "Problema in lettura dati:\n\n%s"\
                                   % repr(db.GetError()))
        g = self.gridemail
        g.ChangeData(db.GetRecordset())
        g.SetGridCursor(0, 0)
        g.MakeCellVisible(0, 0)
        self.PreviewMessage(db.id)
        


# ------------------------------------------------------------------------------


class _PdcCliForInterrMixin(_PdcInterrMixin):
    panscad = None
    panmag = None
    panemail = None
    
    #totali x test quadratura totale partite/saldo contabile
    _pcfquadcont_pcf = 0 #totale partite
    _pcfquadcont_mas = 0 #saldo contabile
    
    def InitControls(self, *args, **kwargs):
        
        _PdcInterrMixin.InitControls(self, *args, **kwargs)
        
        nb = self.FindWindowById(rel_wdr.ID_WORKZONE)
        
        if getattr(Env.Azienda.Login.userdata, 'can_contabsca', True):
            p = aw.Panel(nb)
            nb.AddPage(p, "Scadenzario")
        
        if getattr(Env.Azienda.Login.userdata, 'can_magazzint', True):
            p = aw.Panel(nb)
            nb.AddPage(p, "Magazzino")
        
        if bt.MAGDEMSENDFLAG:
            p = aw.Panel(nb)
            nb.AddPage(p, "Email")
    
    def TestForUpdates(self, ntab=None):
        
        _PdcInterrMixin.TestForUpdates(self, ntab)
        nb = self.FindWindowById(rel_wdr.ID_WORKZONE)
        if ntab is None:
            ntab = nb.GetSelection()
            
        if   "Scadenzario" in nb.GetPageText(ntab):
            if self.panscad is None:
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panscad = PdcScadenzarioPanel(parent, self)
                    parent.AddSizedPanel(self.panscad)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            self.panscad.UpdateGrid(pdcid=self.db_recid)
            self.panscad.TestQuadCont()
            
        elif "Magazzino" in nb.GetPageText(ntab):
            if self.panmag is None:
                wx.BeginBusyCursor()
                try:
                    iscli = isinstance(self, ClientiInterrPanel)
                    parent = nb.GetPage(ntab)
                    self.panmag = magint.PdcIntMagPanel(parent, self, iscli=iscli)
                    self.panmag.UpdateFilters()
                    parent.AddSizedPanel(self.panmag)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            self.panmag.UpdateGrids(pdcid=self.db_recid)
        
        elif "Email" in nb.GetPageText(ntab):
            if self.panemail is None:
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panemail = CliForEmailsPanel(parent)
                    parent.AddSizedPanel(self.panemail)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            self.panemail.UpdateGrid(pdcid=self.db_recid)
            
        
        return nb


# ------------------------------------------------------------------------------


class PdcScadenzarioPanel(aw.Panel,
                          ScadenzarioColorsPanelMixin):
    
    def __init__(self, parent, cfm):
        aw.Panel.__init__(self, parent)
        self.cliformixin = cfm
        pt = wx.Panel(self, wdr.ID_PCFTOTALI)
        wdr.PcfTotaliFunc(pt)
        wdr.PdcScadenzarioFunc(self)
        
        self.dbscad = dbc.PdcScadenzario(\
            today=Env.Azienda.Login.dataElab,\
            giorni_rb=30)
        if cfm.pdctipo == "C":
            tabanag = bt.TABNAME_CLIENTI
        else:
            tabanag = bt.TABNAME_FORNIT
        self.dbscad.AddJoin(tabanag, 'anag', idLeft='id', idRight='id')
        
        ci = lambda x: self.FindWindowById(x)
        
        pp = ci(wdr.ID_PCFPANGRID)
        self.gridpcf = GridScadenzario(pp, self.dbscad)
        self.pdcid = None
        
        ScadenzarioColorsPanelMixin.__init__(self, self.gridpcf)
        
        for cid, evt, func in (
            (wdr.ID_PCFBUTUPD,    wx.EVT_BUTTON,   self.OnUpdateFilters),
            (wdr.ID_PCFONLYINSO,  wx.EVT_CHECKBOX, self.OnUpdateFilters),
            (wdr.ID_PCFONLYOPEN,  wx.EVT_CHECKBOX, self.OnUpdateFilters),
            (wdr.ID_PCFSQUADVEDI, wx.EVT_BUTTON,   self.OnVediSquadCont),
            (wdr.ID_PCFBTNPRT,    wx.EVT_BUTTON,   self.OnStampa)):
            self.Bind(evt, func, id=cid)
        self.Bind(contab.EVT_PCFCHANGED, self.OnPcfChanged)
        
        self.HelpBuilder_SetDir('anag.pdcrel_CliFor')
        self.SetName('CliForScadPage')

    def OnStampa(self, event):
        self.StampaScadenzario()
        event.Skip()
    
    def StampaScadenzario(self):
        db = self.gridpcf.dbscad
        rpt.Report(self, db, "Scadenzario clienti-fornitori", testrec=db.mastro)
    
    def OnPcfChanged(self, event):
        self.UpdateGrid(pdcid=self.pdcid)
        self.TestQuadCont()
        event.Skip()
    
    def OnUpdateFilters(self, event):
        self.UpdateGrid(self.pdcid)
        event.Skip()
    
    def UpdateFilters(self):
        
        pdc = self.dbscad
        
        pdc.ClearPcfFilters()
        
        for name, field, op in (\
            ('pcfdatdoc1', 'datdoc',    '>='),
            ('pcfdatdoc2', 'datdoc',    '<='),
            ('pcfdatsca1', 'datscad',   '>='),
            ('pcfdatsca2', 'datscad',   '<='),
            ('pcfcau',     'id_caus',   '=' ),
            ('pcfmodpag',  'id_modpag', '=' ),):
            val = self.FindWindowByName(name).GetValue()
            if val:
                pdc.AddPcfFilter('sintesi.%s%s%%s' % (field, op), val)
        for name, filt in (('pcfonlyopen', 'imptot<>imppar'),
                           ('pcfonlyinso', 'insoluto=1'),):
            if self.FindWindowByName(name).IsChecked():
                pdc.AddPcfFilter(filt)
    
    def UpdateGrid(self, pdcid=None):
        if True:#pdcid is not None:
            self.UpdateFilters()
            self.pdcid = pdcid
            db = self.dbscad
            if not db.Get(pdcid):
                awc.util.MsgDialog(self,\
                                   "Problema in lettura dati:\n\n%s"\
                                   % repr(db.GetError()))
        self.gridpcf.UpdateGrid()
        self.UpdateTotals()

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
    
    def TestQuadCont(self):
        if not self.pdcid: return
        cfm = self.cliformixin
        cfm._pcfquadcont_pcf = cfm._pcfquadcont_mas = 0
        pcf = adb.DbTable(bt.TABNAME_PCF, 'pcf', writable=False)
        pcf.AddFilter("pcf.id_pdc=%d" % self.pdcid)
        pcf.AddGroupOn("pcf.id_pdc")
        pcf.AddTotalOf("pcf.imptot-pcf.imppar", "saldo")
        if pcf.Retrieve():
            cfm._pcfquadcont_pcf = pcf.total_saldo or 0
            pdc = dbc.PdcMastro()
            if pdc.Get(self.pdcid):
                mas = pdc.GetMastro()
                mas.AddFilter("mov.id_pdcpa=%d" % self.pdcid)
                mas.AddGroupOn("mov.id_pdcpa")
                mas.AddTotalOf("IF(mov.segno='D',mov.importo,-mov.importo)", "saldo")
                if mas.Retrieve():
                    total_saldo = mas.total_saldo or 0
                    if pdc.tipana.tipo == "F":
                        total_saldo *= -1
                    cfm._pcfquadcont_mas = total_saldo
        squad = not adb.DbTable.samefloat(cfm._pcfquadcont_pcf, cfm._pcfquadcont_mas)
        ctrsquad = self.FindWindowByName('pcfsquadcont')
        ctrsquad.Show(squad)
        if squad:
            ctrsquad.SetSize((180,23)) #workaround, dopo show rimane width=0 boh
    
    def OnVediSquadCont(self, event):
        dlg = aw.Dialog(self, -1, "Squadratura")
        wdr.PcfShowSquadContFunc(dlg)
        cn = lambda x: dlg.FindWindowByName(x)
        v = {}
        cfm = self.cliformixin
        if cfm.tabanag == bt.TABNAME_FORNIT:
            clifor = "F"
        else:
            clifor = "A"
        v['pcfquad_mas'] = cfm._pcfquadcont_mas
        if v['pcfquad_mas']>=0:
            if clifor == "C":
                segno = "D"
            else:
                segno = "A"
        else:
            if clifor == "C":
                segno = "A"
            else:
                segno = "D"
        v['pcfquad_pcf'] = cfm._pcfquadcont_pcf
        dif = v['pcfquad_pcf']-v['pcfquad_mas']
        v['pcfquad_dif'] = dif
        for name, val in (('pcfquad_mas', abs(v['pcfquad_mas'])),
                          ('pcfquad_pcf',     v['pcfquad_pcf'] ),
                          ('pcfquad_dif',     dif              ),):
            cn(name).SetLabel(locale.format('%.2f', val, True))
        cn('pcfquad_masda').SetLabel(segno)
        dlg.ShowModal()
        dlg.Destroy()
        event.Skip()


# ------------------------------------------------------------------------------


class CasseInterrPanel(anag.casse.CassePanel, _PdcInterrMixin):
    
    def __init__(self, *args, **kwargs):
        anag.casse.CassePanel.__init__(self, *args, **kwargs)
        _PdcInterrMixin.__init__(self, anag.casse.CassePanel)
    
    def InitControls(self, *args, **kwargs):
        _PdcInterrMixin.InitControls(self, *args, **kwargs)

    def UpdateDataControls(self, *args, **kwargs):
        return _PdcInterrMixin.UpdateDataControls(self, *args, **kwargs)


# ------------------------------------------------------------------------------


class CasseInterrFrame(ga._AnagFrame, _PdcInterrFrameMixin):
    """
    Frame Interrogazione Casse.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_CAS
        ga._AnagFrame.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(CasseInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class CasseInterrDialog(ga._AnagDialog, _PdcInterrFrameMixin):
    """
    Dialog Interrogazione Casse.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_CAS
        ga._AnagDialog.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(CasseInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class BancheInterrPanel(anag.banche.BanchePanel, _PdcInterrMixin):
    
    def __init__(self, *args, **kwargs):
        anag.banche.BanchePanel.__init__(self, *args, **kwargs)
        _PdcInterrMixin.__init__(self, anag.banche.BanchePanel)
    
    def InitControls(self, *args, **kwargs):
        _PdcInterrMixin.InitControls(self, *args, **kwargs)

    def UpdateDataControls(self, *args, **kwargs):
        return _PdcInterrMixin.UpdateDataControls(self, *args, **kwargs)


# ------------------------------------------------------------------------------


class BancheInterrFrame(ga._AnagFrame, _PdcInterrFrameMixin):
    """
    Frame Interrogazione Banche.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BAN
        ga._AnagFrame.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(BancheInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class BancheInterrDialog(ga._AnagDialog, _PdcInterrFrameMixin):
    """
    Dialog Interrogazione Banche.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BAN
        ga._AnagDialog.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(BancheInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class EffettiPresentatiRiepDataGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbriep):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        riep = dbriep
        
        def cn(col):
            return riep._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            ( 80, (cn("effdate"),       "Data", _DAT, True )),
            ( 40, (cn("count_effetti"), "Num.", _NUM, True )),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(riep.GetRecordset(), colmap)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_CLICK, self.OnRigaSel)
    
    def OnRigaSel(self, event):
        event.Skip()


# ------------------------------------------------------------------------------


class EffettiPresentatiGrid(dbglib.DbGridColoriAlternati,
                            ScadenzarioColorsGridMixin):
    
    datpres = None
    def SetDatPres(self, dp):
        self.datpres = dp
    
    def __init__(self, parent, dbpcf):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        self.dbpcf = dbpcf
        pcf = dbpcf
        pdc = pcf.pdc
        cau = pcf.caus
        mpa = pcf.modpag
        
        ScadenzarioColorsGridMixin.__init__(self, self.dbpcf)
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (cn(pcf, "datscad"),  "Scadenza",       _DAT, True)),
            ( 60, (cn(pdc, "codice"),   "Cod.",           _STR, True)),
            (180, (cn(pdc, "descriz"),  "Cliente",        _STR, True)),
            ( 90, (cn(pcf, "impeff"),   "Importo",        _IMP, True)),
            ( 30, (cn(cau, "codice"),   "Cod.",           _STR, True)),
            (120, (cn(cau, "descriz"),  "Causale",        _STR, True)),
            ( 50, (cn(pcf, "numdoc"),   "Num.",           _STR, True)),
            ( 80, (cn(pcf, "datdoc"),   "Data",           _DAT, True)),
            ( 90, (cn(pcf, "imptot"),   "ImportoPartita", _IMP, True)),
            ( 90, (cn(pcf, "imptot"),   "Pareggiamento",  _IMP, True)),
            ( 90, (cn(pcf, "saldo"),    "Saldo",          _IMP, True)),
            (  1, (cn(pcf, "id"),       "#pcf",           _STR, True)),
            (  1, (cn(cau, "id"),       "#cau",           _STR, True)),
            (  1, (cn(pdc, "id"),       "#pdc",           _STR, True)),
            (  1, (cn(mpa, "id"),       "#mpa",           _STR, True)),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(pcf.GetRecordset(), colmap)
        
        self.AddTotalsRow(2, 'Totali:', (cn(pcf, "impeff"),
                                         cn(pcf, "imptot"),
                                         cn(pcf, "imppar"),
                                         cn(pcf, "saldo"),))
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(3, 2)
#        self.SetFitColumn(2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnApriPcf)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        rspcf = self.dbpcf.GetRecordset()
        return self.ScadenzarioColorsGetAttr(rspcf, row, col, rscol, attr)
    
    def OnApriPcf(self, event):
        row = event.GetRow()
        pcf = self.dbpcf
        if 0 <= row < pcf.RowsCount():
            pcf.MoveRow(row)
            d = PcfDialog(self)
            d.SetPcf(pcf.id)
            d.CenterOnScreen()
            d.ShowModal()
            d.Destroy()
            self.RemoveChild(d)
        event.Skip()


# ------------------------------------------------------------------------------


class EffettiPresentatiPanel(wx.Panel,
                             ScadenzarioColorsPanelMixin):
    
    pdcid = None
    pdccod = None
    pdcdes = None
    def SetPdcId(self, pdcid, cod, des):
        self.pdcid = pdcid
        self.pdccod = cod
        self.pdcdes = des
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.EffettiPresentatiFunc(self)
        self.dbriep = dbc.PcfEffettiPresentatiRiepData()
        self.dbpcf = dbc.PcfEffettiPresentati()
        import anag.dbtables as dba
        def cn(x):
            return self.FindWindowByName(x)
        self.gridriep = EffettiPresentatiRiepDataGrid(cn('pandate'), self.dbriep)
        self.gridpcf = EffettiPresentatiGrid(cn('panpcf'), self.dbpcf)
        ScadenzarioColorsPanelMixin.__init__(self, self.gridpcf)
        self.gridriep.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnUpdatePcf)
        self.Bind(wx.EVT_BUTTON, self.OnPrint, cn('btn_pcfprt'))
    
    def OnPrint(self, event):
        db = self.dbpcf
        db._info.contoef = '%s %s' % (self.pdccod, self.pdcdes)
        db._info.datpres = self.gridpcf.datpres
        rpt.Report(self, self.dbpcf, "Lista effetti presentati")
        event.Skip()
    
    def UpdateFilters(self):
        r = self.dbriep
        r.ClearFilters()
        r.AddFilter('pcf.id_effpdc=%s', self.pdcid)
        r.Retrieve()
    
    def OnUpdatePcf(self, event):
        riep = self.dbriep
        row = event.GetRow()
        pcf = self.dbpcf
        if 0 <= row < riep.RowsCount():
            riep.MoveRow(row)
            pcf.ClearFilters()
            pcf.AddFilter('pcf.id_effpdc=%s', self.pdcid)
            pcf.AddFilter('pcf.effdate=%s', riep.effdate)
            pcf.Retrieve()
        else:
            pcf.Reset()
        self.gridpcf.ChangeData(pcf.GetRecordset())
        self.gridpcf.SetDatPres(riep.effdate)
        event.Skip()
    
    def UpdateGrid(self):
        self.gridriep.ChangeData(self.dbriep.GetRecordset())


# ------------------------------------------------------------------------------


class EffettiInterrPanel(anag.effetti.EffettiPanel, _PdcInterrMixin):
    
    panpres = None
    
    def __init__(self, *args, **kwargs):
        anag.effetti.EffettiPanel.__init__(self, *args, **kwargs)
        _PdcInterrMixin.__init__(self, anag.effetti.EffettiPanel)
    
    def InitControls(self, *args, **kwargs):
        _PdcInterrMixin.InitControls(self, *args, **kwargs)
        nb = self.FindWindowById(rel_wdr.ID_WORKZONE)
        p = aw.Panel(nb)
        nb.AddPage(p, "Presentazioni")

    def TestForUpdates(self, ntab=None):
        
        _PdcInterrMixin.TestForUpdates(self, ntab)
        nb = self.FindWindowById(rel_wdr.ID_WORKZONE)
        if ntab is None:
            ntab = nb.GetSelection()
            
        if "Presentazioni" in nb.GetPageText(ntab):
            if self.panpres is None:
                wx.BeginBusyCursor()
                try:
                    parent = nb.GetPage(ntab)
                    self.panpres = EffettiPresentatiPanel(parent)
                    parent.AddSizedPanel(self.panpres)
                    nb.ReSize()
                finally:
                    wx.EndBusyCursor()
            def cn(x):
                return self.FindWindowByName(x)
            self.panpres.SetPdcId(self.db_recid, 
                                  cn('codice').GetValue(),
                                  cn('descriz').GetValue())
            self.panpres.UpdateFilters()
            self.panpres.UpdateGrid()
        
        return nb
    
    def UpdateDataControls(self, *args, **kwargs):
        return _PdcInterrMixin.UpdateDataControls(self, *args, **kwargs)


# ------------------------------------------------------------------------------


class EffettiInterrFrame(ga._AnagFrame, _PdcInterrFrameMixin):
    """
    Frame Interrogazione Effetti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_EFF
        ga._AnagFrame.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(EffettiInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class EffettiInterrDialog(ga._AnagDialog, _PdcInterrFrameMixin):
    """
    Dialog Interrogazione Effetti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_EFF
        ga._AnagDialog.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(EffettiInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class ClientiInterrPanel(anag.clienti.ClientiPanel, _PdcCliForInterrMixin):
    
    def __init__(self, *args, **kwargs):
        anag.clienti.ClientiPanel.__init__(self, *args, **kwargs)
        _PdcCliForInterrMixin.__init__(self, anag.clienti.ClientiPanel)
    
    def InitControls(self, *args, **kwargs):
        _PdcCliForInterrMixin.InitControls(self, *args, **kwargs)

    def UpdateDataControls(self, *args, **kwargs):
        return _PdcCliForInterrMixin.UpdateDataControls(self, *args, **kwargs)


# ------------------------------------------------------------------------------


class ClientiInterrFrame(ga._AnagFrame, _PdcInterrFrameMixin):
    """
    Frame Interrogazione Clienti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_CLI
        ga._AnagFrame.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(ClientiInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class ClientiInterrDialog(ga._AnagDialog, _PdcInterrFrameMixin):
    """
    Dialog Interrogazione Clienti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_CLI
        ga._AnagDialog.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(ClientiInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class FornitInterrPanel(anag.fornit.FornitPanel, _PdcCliForInterrMixin):
    
    def __init__(self, *args, **kwargs):
        anag.fornit.FornitPanel.__init__(self, *args, **kwargs)
        _PdcCliForInterrMixin.__init__(self, anag.fornit.FornitPanel)
    
    def InitControls(self, *args, **kwargs):
        _PdcCliForInterrMixin.InitControls(self, *args, **kwargs)

    def UpdateDataControls(self, *args, **kwargs):
        return _PdcCliForInterrMixin.UpdateDataControls(self, *args, **kwargs)


# ------------------------------------------------------------------------------


class FornitInterrFrame(ga._AnagFrame, _PdcInterrFrameMixin):
    """
    Frame Interrogazione Fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_FOR
        ga._AnagFrame.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(FornitInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class FornitInterrDialog(ga._AnagDialog, _PdcInterrFrameMixin):
    """
    Dialog Interrogazione Fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_FOR
        ga._AnagDialog.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(FornitInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class PdcInterrPanel(anag.pdc.PdcPanel, _PdcInterrMixin):
    
    def __init__(self, *args, **kwargs):
        anag.pdc.PdcPanel.__init__(self, *args, **kwargs)
        _PdcInterrMixin.__init__(self, anag.pdc.PdcPanel)
    
    def InitControls(self, *args, **kwargs):
        _PdcInterrMixin.InitControls(self, *args, **kwargs)

    def UpdateDataControls(self, *args, **kwargs):
        return _PdcInterrMixin.UpdateDataControls(self, *args, **kwargs)
    

# ------------------------------------------------------------------------------


class PdcInterrFrame(ga._AnagFrame, _PdcInterrFrameMixin):
    """
    Frame Interrogazione Piano dei conti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_PDC
        ga._AnagFrame.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(PdcInterrPanel(self, -1))
        TestInitialFrameSize(self)


# ------------------------------------------------------------------------------


class PdcInterrDialog(ga._AnagDialog, _PdcInterrFrameMixin):
    """
    Dialog Interrogazione Piano dei conti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_PDC
        ga._AnagDialog.__init__(self, *args, **kwargs)
        _PdcInterrFrameMixin.__init__(self)
        self.LoadAnagPanel(PdcInterrPanel(self, -1))
        TestInitialFrameSize(self)
