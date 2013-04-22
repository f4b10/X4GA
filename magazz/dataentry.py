#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dataentry.py
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

import lib

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib

import stormdb as adb

import awc.controls.windows as aw
from awc.controls.linktable import LinkTable
from awc.controls import EVT_DATECHANGED
from awc.controls.linktable import EVT_LINKTABCHANGED
import awc.controls.mixin as cmix

import Env
from awc.controls.datectrl import DateCtrl
Esercizio = Env.Azienda.Esercizio
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import report as rpt


import magazz
import magazz.dbtables as dbm
from magazz import\
     STATUS_SELCAUS, STATUS_GETKEY, STATUS_DISPLAY, STATUS_EDITING,\
     EDITING_HEAD, EDITING_BODY, EDITING_FOOT,\
     FOOT_TOT, FOOT_ACC

from magazz.dataentry_b import GridBody, SelezionaMovimentoAccontoDialog

import magazz.dataentry_acq as dma

import magazz.dataentry_wdr as wdr

if False:
    #sembra che questo non serva, ma serve (a py2exe per includere il gateway nell'exe)
    import magazz.dataentry_gw as gateway

import contab
from contab.util import SetWarningPag

import anag
import anag.prod as prod
import anag.util as autil

import awc.controls.linktable as linktab

import awc.util
from awc.util import MsgDialog, MsgDialogDbError

import cfg.cfgcontab   as cfgcon
import cfg.cfgautomat  as auto
import cfg.cfgprogr    as progr

import contab
import contab.scadedit as scadedit
import contab.pdcint as pdcint

from awc.controls.attachbutton import AttachTableList

today = Env.Azienda.Esercizio.dataElab
datregsrc1 = today-today.day+1
datregsrc2 = today
datdocsrc1 = datdocsrc2 = None
magsearch = None
pdcsearch = None
acqsearch = True
annsearch = True
ricsearch = True

def DbgMsg(x):
    #print x
    pass


class PdcProdHistoryGrid(dbglib.DbGrid):
    
    def __init__(self, parent):
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), style=0)
        
        self.dbmas = dbm.ProdMastro()
        mov = self.dbmas.mov
        doc = mov.doc
        tpd = doc.tipdoc
        tpm = mov.tipmov
        mag = doc.mag
        
        self._cache_history = {}
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        
        cols = []
        a = cols.append
        a(( 35, (cn(mag, "codice"),  "Mag.",      _STR, True)))
        a((100, (cn(tpd, "descriz"), "Documento", _STR, True)))
        a(( 40, (cn(doc, "numdoc"),  "Num.",      _STR, True)))
        a(( 80, (cn(doc, "datdoc"),  "Data doc.", _DAT, True)))
        a(( 35, (cn(tpm, "codice"),  "Mov.",      _STR, True)))
        a(( 35, (cn(mov, "um"),      "UM",        _STR, True)))
        a(( 80, (cn(mov, "qta"),     "Qtà",       _QTA, True)))
        a(( 80, (cn(mov, "prezzo"),  "Prezzo",    _PRE, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 60, (cn(mov, "sconto1"), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _SCO, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 60, (cn(mov, "sconto2"), "Sc.%2", _SCO, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 60, (cn(mov, "sconto3"), "Sc.%3", _SCO, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 60, (cn(mov, "sconto4"), "Sc.%4", _SCO, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 60, (cn(mov, "sconto5"), "Sc.%5", _SCO, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 60, (cn(mov, "sconto6"), "Sc.%6", _SCO, True)))
        a((100, (cn(mov, "importo"), "Importo",   _IMP, True)))
        a((140, (cn(mov, "note"),    "Note.",     _STR, True)))
        a(( 30, (cn(doc, "f_ann"),   "Dan",       _CHK, True)))
        a(( 30, (cn(mov, "f_ann"),   "Man",       _CHK, True)))
        a(( 30, (cn(doc, "f_acq"),   "Acq",       _CHK, True)))
        a((  1, (cn(doc, "id"),      "#doc",      _STR, True)))
        a((  1, (cn(mov, "id"),      "#mov",      _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        self.SetData((), colmap, canedit, canins)
        
        self._bgcol1, self._bgcol2 = [bc.GetColour(c) for c in ("lavender",
                                                                "aliceblue")]
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
        
        #self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallProd)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        readonly = col < 3 or col > 8
        attr.SetReadOnly(readonly)
        
        if row%2 == 0:
            bgcol = self._bgcol2
        else:
            bgcol = self._bgcol1
        
        #attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        
        return attr
    
    def UpdateGrid(self, idpdc, idprod):
        if idprod is None:
            rs = ()
        else:
            key = '%s_%s' % (idpdc, idprod)
            if not key in self._cache_history:
                mas = self.dbmas
                mov = mas.mov
                mov.ClearFilters()
                mov.AddFilter('doc.id_pdc=%s', idpdc)
                mov.AddFilter('mov.id_prod=%s', idprod)
                mov.ClearOrders()
                mov.AddOrder('doc.datreg', adb.ORDER_DESCENDING)
                mov.AddOrder('doc.numdoc', adb.ORDER_DESCENDING)
                mov.SetLimits(100)
                mas.Get(idprod)
                rs = mov.GetRecordset()
                self._cache_history[key] = rs
            rs = self._cache_history[key]
        self.ChangeData(rs)
    
    def ClearHistoryCache(self):
        self._cache_history.clear()


# ------------------------------------------------------------------------------


class DisplayFidoPanel(aw.Panel):
    
    check = None
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.DisplayFidoClienteFunc(self)
        for name, func in (('btnprintfido', self.OnPrintFido),
                           ('btnprintritp', self.OnPrintRitardi)):
            self.Bind(wx.EVT_BUTTON, func, self.FindWindowByName(name))
    
    def OnPrintFido(self, event):
        rpt.Report(self, self.check, 'Situazione fido cliente')
        event.Skip()
    
    def OnPrintRitardi(self, event):
        s = self.check.dbscad
        s.Get(self.check.id)
        if s.mastro.IsEmpty():
            aw.awu.MsgDialog(self, "Nessun dato da stampare")
            return
        rpt.Report(self, s, 'Analisi ritardi pagamenti clienti')
        event.Skip()
    
    def UpdateValues(self, check):
        assert isinstance(check, dbm.CtrFidoCliente)
        def cn(x):
            return self.FindWindowByName(x)
        self.check = check
        for name in 'doc esa ddf esp sco pap ggs'.split():
            v1 = getattr(check, '_%s'%name)
            cn(name).SetValue(v1)
            try:
                v2 = getattr(check, '_fido%s'%name)
                cn('fido%s'%name).SetValue(v2)
                if v2 and v1>v2:
                    cn('status_%s'%name).SetLabel("-esubero-")
            except:
                pass


# ------------------------------------------------------------------------------


class DisplayFidoDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Situazione fido cliente'
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = DisplayFidoPanel(self)
        self.AddSizedPanel(self.panel)
    
    def UpdateValues(self, check):
        self.panel.UpdateValues(check)


# ------------------------------------------------------------------------------


class MagazzPanel(aw.Panel,\
                  cfgcon.CfgCausale,\
                  auto.CfgAutomat,\
                  progr.CfgProgr,\
                  GridBody,\
                  scadedit.GridScad):
    """
    Panel Documenti magazzino.
    """
    onedoconly_id = None
    _testload = True
    gridbodyclass = GridBody
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        global today
        today = Env.Azienda.Esercizio.dataElab
        
        self.caudisp = [ ("codice",  "Cod."),\
                         ("descriz", "Causale") ]
        self.cauid = None
        self.canins = True
        self.canedit = True
        self.candelete = True
        self.editing = False
        self.modified = False
        self._scadok = True
        self._headok = False
        self._docs2elab = []
        self._acqpdtmov = None
        self._docsearch = None
        self._regsearch = None
        self.interrpdc = None
        self.interrpdc_lastid = None
        self.loadingdoc = False
        self.oldlist = None
        
        self._delta_xy = 1
        
        self.setenablecontrols = True
        self.rowsok = True
        
        self.dbdoc = dbm.DocMag()
        self.ctrfido = dbm.CtrFidoCliente()
        
        self.dbpdc = adb.DbTable(bt.TABNAME_PDC)
        self.dbpdc.AddJoin(bt.TABNAME_PDCTIP, "tipana", idLeft="id_tipo")
        self.dbpag = adb.DbTable(bt.TABNAME_MODPAG, "modpag")
        self.dbanag = None
        
        self.dbattanag = AttachTableList(bt.TABNAME_ALLEGATI)
        
        self.dbevas = dbm.ElencoMovimEva()
        self.dbevas.AddLimit(1)
        
        db_curs = adb.db.__database__.GetConnection().cursor()
        
        cfgcon.CfgCausale.__init__(self, db_curs)
        auto.CfgAutomat.__init__(self, db_curs)
        progr.CfgProgr.__init__(self, db_curs)
        
        self.gridbodyclass.__init__(self)
        
        scadedit.GridScad.__init__(self, self.dbdoc.regcon)
        
        self._Auto_AddKeysMagazz()
        self._Progr_AddKeysMagazz()
        
        self.status = None
        self.caufilt = None
        
        wdr.DialogFunc(self, True)
        self.InitPanelTot()
        
        cn = self.FindWindowByName
        ci = self.FindWindowById
        
        cn('scadwarning').SetLabel('')
        cn('butfido').Disable()
        
        self.boxanag = None
        self.boxdest = None
        ctrls = aw.awu.GetAllChildrens(self)
        for c in ctrls:
            if isinstance(c, wx.StaticBox):
                if c.GetLabel() in 'boxanag,boxdest'.split(','):
                    setattr(self, c.GetLabel(), c)
        self.boxanag.SetLabel('Anagrafica')
        self.boxdest.SetLabel('Destinazione diversa')
        
        self.GridBody_Init(ci(wdr.ID_PANGRIDBODY))
        self.gridlist = prod.ListAttGrid(ci(wdr.ID_PANGRIDLIST))
        self.gridmovi = PdcProdHistoryGrid(ci(wdr.ID_PANGRIDMOVIM))
        
        self.controls = awc.util.DictNamedChildrens(self)
        
        def ResetPdc(*x):
            """
            Quando viene confermato il dialog modale della scheda anagrafica,
            provvede a resettare il campo id_pdc sul dbdoc onde far riaggiornare
            tutti i dati della testata dopo il loro eventuale cambiamento.
            Questo avviene solo se il documento è in fase di inserimento,
            altrimenti id_pdc non viene resettato in quanto i dati della testata
            devono rimanere gli stessi anche se modificati su scheda anagrafica.
            """
            if self.dbdoc.id is None:
                self.dbdoc.id_pdc = None
        self.controls['id_pdc'].SetPreSetVal(ResetPdc)
        
        btnat = self.controls["butattach"]
        btnat.SetScope("movmag_h")
        btnat.SetAutoText(self.controls["autonotes_doc"])
        btnat.SetSpyPanel(cn('attachspy'))
        
        self._docsearch = dbm.DocMag()
        self._regsearch = dbm.dbc.DbRegCon()
        self._regsearch.AddGroupOn('reg.id_regiva')
        self._regsearch.AddMaximumOf('reg.numiva', 'numiva')
        
        self.InitCausale()
        self.SetRegStatus(STATUS_SELCAUS)
        
        #per grandezza minima della griglia, che altrimenti è settata come altezza completa 
        #ed abilitando la zona dati del prodotto la griglia rimane troppo alta, 
        #nascondendo i bottoni sottostanti x nuova riga, elimina riga ecc.
        self.SetProdZoneSize(force_visible=True)
        
        self.SetFieldsMaxLength()
        
        for n in range(9):
            if n+1>bt.MAGNUMSCO:
                for prefix in 'labsco sconto'.split():
                    c = cn('%s%d' % (prefix, n+1))
                    if c:
                        c.Hide()
        
        # bind eventi dei bottoni
        for name, func in (("butnew",     self.OnDocNew),
                           ("butsrc",     self.OnDocSearch),
                           ("butsave",    self.OnDocEnd),
                           ("butquit",    self.OnDocQuit),
                           ("butdel",     self.OnDocDelete),
                           ("butmodif",   self.OnButModify),
                           ("butacquis",  self.OnButAcquis),
                           ("butdoc",     self.OnButDoc),
                           ("butprint",   self.OnButPrint),
                           ("butprodsch", self.GridBodyOnSchedaProd),
                           ("butprodmas", self.GridBodyOnMastroMov),
                           ("butfido",    self.OnDisplayFidoCliente),
                           ("butvediacc", self.OnDisplayAccontiCliente),):
            self.Bind(wx.EVT_BUTTON, func, self.controls[name])
        
        # bind eventi di cambiamento dati del documento
        for name, evt in (('numdoc', wx.EVT_TEXT),
                          ('numiva', wx.EVT_TEXT),
                          ('datdoc',  EVT_DATECHANGED),
                          ('datreg',  EVT_DATECHANGED),):
            self.Bind(evt, self.OnDocIdChanged, self.controls[name])
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnDocIdChanged,\
                  id=wdr.ID_MAGAZZ)
        
        ci(wdr.ID_PDC).GetCtrlScheda().Bind(wx.EVT_RIGHT_DOWN, self.OnInterrPdc)
        
        ci(wdr.ID_PDC).SetInitFocus(linktab.INITFOCUS_DESCRIZ)
        
        ci(wdr.ID_FANN).SetDataLink('f_ann', {True: 1, False: 0})
        ci(wdr.ID_FACQ).SetDataLink('f_acq', {True: 1, False: 0})
        
        # bind evento cambiamento sottoconto x agg.dati anagrafici
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnAnagChanged,\
                  id=wdr.ID_PDC)
        #self.Bind(linktab.EVT_LINKTABCHANGED, self.OnDestChanged,\
                  #id=wdr.ID_DEST)
        
        # bind eventi di cambiamento dati di testata
        for name in 'f_ann f_acq'.split():
            self.Bind(wx.EVT_CHECKBOX, self.OnHeadChanged, cn(name))
        
        for name in 'pdc modpag bancf speinc aliqiva agente zona tiplist valuta dest'.split():
            self.Bind(EVT_LINKTABCHANGED, self.OnHeadChanged, cn("id_%s" % name))
        
        for name in 'desrif numrif noteint notedoc sconto1 sconto2 sconto3 sconto4 sconto5 sconto6'.split():
            self.Bind(wx.EVT_TEXT, self.OnHeadChanged, cn(name))
        
        for name in 'datrif'.split():
            self.Bind(EVT_DATECHANGED, self.OnHeadChanged, cn(name))
        
        # bind eventi di cambiamento dati accompagnatori
        for name in 'cau cur vet asp por con'.split():
            self.Bind(EVT_LINKTABCHANGED, self.OnFootChanged, cn("id_tra%s" % name))
        
        for name in 'impcontr totpeso totcolli notevet'.split():
            self.Bind(wx.EVT_TEXT, self.OnFootChanged, cn(name))
        
        self.Bind(EVT_DATECHANGED, self.OnFootChanged, cn("initrasp"))
        self.Bind(wx.EVT_BUTTON, self.OnFootChanged, cn("initraspnow"))
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnWorkZoneChanged, cn('workzone'))
        
        for cid, func in ((wdr.ID_BTNBODYNEW,  self.GridBodyOnCreate),
                          (wdr.ID_BTNBODYDEL,  self.GridBodyOnDelete),
                          (wdr.ID_BTNBODYPDT,  self.GridBodyOnAcqPDT),
                          (wdr.ID_BTNBODYETIC, self.GridBodyOnLabels)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        for type in 'des vet'.split():
            
            c = cn('enable_nocode%s' % type)
            self.Bind(wx.EVT_CHECKBOX, self.OnFootChanged, c)
            
            c = cn('nocode%s_id_stato' % type)
            if c:
                self.Bind(EVT_LINKTABCHANGED, self.OnFootChanged, c)
            
            for name in 'descriz indirizzo cap citta prov codfisc piva'.split():
                c = cn('nocode%s_%s' % (type, name))
                if c:
                    self.Bind(wx.EVT_TEXT, self.OnFootChanged, c)
        
        cn('nocodevet_piva').SetStateControl(cn('nocodevet_nazione'))
        
        if bt.MAGEXTRAVET:
            for name in 'targa autista dichiar'.split():
                c = cn('nocodevet_%s' % name)
                self.Bind(wx.EVT_TEXT, self.OnFootChanged, c)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnVariaDestin, cn('enable_nocodedes'))
        self.Bind(wx.EVT_CHECKBOX, self.OnVariaVettore, cn('enable_nocodevet'))
        self.Bind(wx.EVT_TEXT, self.OnVariaColli, cn('numcolli'))
        
        self.Bind(wx.EVT_SIZE, self.OnResize)
        
#        self.SetSize((1024,768))
        
        self.Layout_()
        wx.CallAfter(self.Layout_)
        
        self.SetAcceleratorKey('I', wdr.ID_BTN_NEW,    'Inserisci',       'Inserisce un nuovo documento')
        self.SetAcceleratorKey('C', wdr.ID_BTN_SEARCH, 'Cerca',           'Cerca un documento esistente')
        self.SetAcceleratorKey('M', wdr.ID_BTN_MODIF,  'Modifica',        'Modifica il documento visualizzato')
        self.SetAcceleratorKey('V', wdr.ID_BTN_ACQUIS, 'Evasione',        'Avvia l\'evasione di un altro documento')
        self.SetAcceleratorKey('S', wdr.ID_BTN_SAVE,   'Salva e Chiudi',  'Salva il presente documento')
        self.SetAcceleratorKey('P', wdr.ID_BTN_PRINT,  'Stampa e Chiudi', 'Stampa il presente documento')
        self.SetAcceleratorKey('X', wdr.ID_BTN_DELETE, 'Elimina',         'Elimina il presente documento')
        self.SetAcceleratorKey('Q', wdr.ID_BTN_QUIT,   'Abbandona',       'Abbandona il documento senza salvare')
    
    def Layout_(self):
        s = self.GetSize()
        self.SetSize((s[0]+self._delta_xy, s[1]))
        self._delta_xy = 0-self._delta_xy
    
    def OnVariaDestin(self, event):
        def Enable(f):
            self.EnableHeadControls()
            self.EnableDatiAcc()
            self.UpdateHeadDest()
            if f:
                self.FindWindowByName('nocodedes_descriz').SetFocus()
        wx.CallAfter(Enable, event.GetEventObject().IsChecked())
        event.Skip()
    
    def OnVariaVettore(self, event):
        wx.CallAfter(self.EnableDatiAcc)
        if event.GetEventObject().IsChecked():
            f = self.FindWindowByName('nocodevet_descriz')
        else:
            f = self.FindWindowByName('id_travet')
        wx.CallAfter(lambda: f.SetFocus())
        event.Skip()
    
    def OnVariaColli(self, event):
        cn = self.FindWindowByName
        cn('butrptcolli').Enable((cn('totcolli').GetValue() or 0) > 0)
        event.Skip()
    
    def SetFieldsMaxLength(self):
        for f in bt.tabelle[bt.TABSETUP_TABLE_MOVMAG_H][bt.TABSETUP_TABLESTRUCTURE]:
            if f[bt.TABSETUP_COLUMNTYPE] in 'CHAR,VARCHAR':
                c = self.FindWindowByName(f[bt.TABSETUP_COLUMNNAME])
                if c:
                    c.SetMaxLength(f[bt.TABSETUP_COLUMNLENGTH])
    
    def TestQuit(self):
        out = True
        if self.status == STATUS_EDITING and self.dbdoc.HasModifies():
            x = aw.awu.MsgDialog(self, message=\
                                 """Confermi l'abbandono delle informazioni """
                                 """sin qui inserite?""",
                                 style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
            out = (x == wx.ID_YES)
        return out
    
    def OnInterrPdc(self, event):
        self.InterrPdc(show=True)
        event.Skip()

    def InterrPdc(self, show=False):
        pdcid = self.controls['id_pdc'].GetValue()
        if pdcid == self.interrpdc_lastid and not show or pdcid is None:
            return
        make = False
        dlgcls = self.GetInterrPdcFrameClass()
        if self.interrpdc is None:
            make = True
        else:
            try:
                x = self.interrpdc.GetSize()
            except wx.PyDeadObjectError:
                make = True
        try:
            wx.BeginBusyCursor()
            if make:
                f = aw.awu.GetParentFrame(self)
                self.interrpdc = dlgcls(f, complete=False, onecodeonly=pdcid)
                self.interrpdc.SetTitle("Interroga anagrafica")
                self.interrpdc.FindWindowByName('_titlecard').SetLabel('Scheda')
                self.interrpdc.panel.firstfocus = None
                self.interrpdc.DisplayTab('magazzino')
            self.interrpdc.panel.onecodeonly = pdcid
            self.interrpdc.UpdateSearch()
            if make or show:
                self.interrpdc.Show()
                self.interrpdc.SetFocus()
        finally:
            wx.EndBusyCursor()
        self.interrpdc_lastid = pdcid
    
    #def InitPanelTot(self):
        #pass
    
    def OnWorkZoneChanged(self, event):
        ci = self.FindWindowById
        wz = self.FindWindowByName('workzone')
        ntab = wz.GetSelection()
        if ntab == 2:
            #piede - totali
            self.UpdatePanelFoot()
            self.EnableFootControls()
        elif ntab == 3:
            #piede - dati accompagnatori
            self.UpdatePanelDAcc()
            self.EnableFootControls()
        self.TestWorkZoneFirstFocus()
        event.Skip()
    
    def TestWorkZoneFirstFocus(self):
        ci = self.FindWindowById
        wz = self.FindWindowByName('workzone')
        if self.status == STATUS_DISPLAY:
            wz.SetFocus()
        else:
            ntab = wz.GetSelection()
            if ntab == 0:
                #testata
                if self.status == STATUS_EDITING:
                    ci(wdr.ID_PDC).SetFocus()
                elif self.status == STATUS_SELCAUS:
                    ci(wdr.ID_CAUSALE).SetFocus()
                    self.SetDefaultItem(self.controls['butnew'])
            elif ntab == 1:
                #corpo
                ci(wdr.ID_PANGRIDBODY).SetFocus()
            elif ntab == 3:
                #piede - dati accompagnatori
                for c in aw.awu.GetAllChildrens(wz.GetPage(ntab)):
                    if hasattr(c, 'SetFocus') and c.IsEnabled() and not isinstance(c, wx.StaticText):
                        c.SetFocus()
                        break
    
    def UpdatePanelDAcc(self):
        doc = self.dbdoc
        ctr = lambda f: self.FindWindowByName(f)
        for f in ("id_tracau", "id_tracur", "id_travet", "id_traasp",\
                  "id_trapor", "id_tracon", "impcontr", "initrasp",\
                  "totpeso", "totcolli", "notevet"):
            if f == "impcontr" and self.status == STATUS_EDITING:
                ctr(f).SetValueSilent(doc.totimporto)
            else:
                ctr(f).SetValueSilent(doc.__getattr__(f))
        for name in 'totpeso totcolli'.split():
            ctr(name).SetValue(getattr(doc, name))
        for name in doc.GetFieldNames():
            if ('nocodedes' in name or 'nocodevet' in name):
                try:
                    ctr(name).SetValue(getattr(doc, name))
                except:
                    pass
    
    def IsDocValid(self, docload=True, frame=None):
        valid = False
        if frame is None:
            frame = self
        def cn(x):
            return frame.FindWindowByName(x)
        numdoc = cn('numdoc').GetValue()
        numiva = cn('numiva').GetValue()
        datreg = cn('datreg').GetValue()
        datdoc = cn('datdoc').GetValue()
        #valuta = cn('id_valuta').GetValue()
        magazz = cn('id_magazz').GetValue()
        doc = self.dbdoc
        reg = doc.regcon
        cfg = doc.cfgdoc
        err = ""
        if   numdoc<0 or (numdoc == 0 and not doc.cfgdoc.pienum):
            err = "Il numero documento è errato"
        elif (numiva<0 or numiva == 0 and not doc.cfgdoc.pienum) and cfg.caucon.id_regiva is not None:
            err = "Il numero di protocollo iva è errato"
        elif datreg is None:
            err = "La data di registrazione è errata"
        elif datdoc is None:
            err = "La data del documento è errata"
        else:
            filter, fparms = self.GetDocLoadFilter(frame)
            dbdoc = adb.DbTable(bt.TABNAME_MOVMAG_H, "doc")
            dbdoc.AddJoin(bt.TABNAME_CFGMAGDOC, "tipdoc")
            dbdoc.AddJoin(bt.TABNAME_PDC, "pdc", join=adb.JOIN_LEFT)
            if dbdoc.Retrieve(filter, *fparms):
                exist = False
                if dbdoc.RowsCount() > 0:
                    exist = True
                    if dbdoc.id_tipdoc == self.dbdoc.id_tipdoc:
                        if docload and dbdoc.tipdoc.ctrnum == 'X':
                            valid = self.DocLoad(dbdoc.id)
                            if valid:
                                self.UpdateDocIdControls()
                                self.GridScadCheckImporti()
                        else:
                            valid = True
                if exist and not valid:
                    err =\
"""Numero già attribuito ad altro documento:\n%s del %s - %s %s"""\
                        % (dbdoc.tipdoc.descriz,
                           dbdoc.dita(dbdoc.datdoc),
                           dbdoc.pdc.codice,
                           dbdoc.pdc.descriz)
            else:
                err = dbdoc._info.dbError.description
            del dbdoc
            self.SetAnagFilters()
        if not err:
            magid = cn('id_magazz').GetValue()
            dreg = cn('datreg').GetValue()
            numdocmin, datregmin, numdocmax, datregmax = self.GetLimits(magid, dreg)
        if err:
            MsgDialog(self, err)
        else:
            valid = True
            self.UpdateHeadAnag()
            self.UpdateHeadDest()
        return valid
    
    def GetDocLoadFilter(self, frame=None):
        if frame is None:
            frame = self
        def cnv(x):
            return frame.FindWindowByName(x).GetValue()
        doc = self.dbdoc
        cfg = doc.cfgdoc
        filter = "doc.id_magazz=%s"
        fparms = [cnv('id_magazz')]
        filter += " AND YEAR(doc.datreg)=%s"
        fparms.append(cnv('datreg').year)
        if cfg.docfam:
            filter += " AND tipdoc.docfam=%s" 
            fparms.append(cfg.docfam)
        else:
            filter += " AND doc.id_tipdoc=%s"
            fparms.append(self.cauid)
        filter += " AND doc.numdoc=%s"
        fparms.append(cnv('numdoc'))
        if doc.id:
            filter += " AND doc.id<>%s"
            fparms.append(doc.id)
        return filter, fparms
    
    def DocLoad(self, docid):
        out = False
        doc = self.dbdoc
        if doc.Get(docid):
            out = doc.RowsCount() == 1
            idreg = doc.id_reg
            self.controls['butattach'].SetKey(doc.id)
        else:
            idreg = None
        #self.gridscad.ChangeData(doc.regcon.scad.GetRecordset())
        self.GridScadSetReg(doc.regcon)
        if self.onedoconly_id:
            self.controls['causale'].SetValue(doc.id_tipdoc)
        self.UpdateDocIdControls()
        self.UpdatePanelHead()
        self.UpdateDatiScad()
        self.UpdateDatiAcconto()
        self.UpdateDatiEvas()
        self.UpdateAnagAutoNotes()
        self.IsHeadValid()
        self.MakeTotals(False)
        if self.interrpdc:
            self.InterrPdc()
        return out
    
    def DocRedraw(self):
        doc = self.dbdoc
        self.controls['butattach'].SetKey(doc.id)
        self.GridScadSetReg(doc.regcon)
        if self.onedoconly_id:
            self.controls['causale'].SetValue(doc.id_tipdoc)
        self.UpdatePanelDocId()
        self.UpdatePanelHead()
        self.UpdateDatiScad()
        self.UpdateDatiAcconto()
        self.UpdateDatiEvas()
        self.UpdateAnagAutoNotes()
        self.IsHeadValid()
        self.MakeTotals(False)
        if self.interrpdc:
            self.InterrPdc()
    
    def TestPcf(self):
        out = True
        doc = self.dbdoc
        if doc.regcon.config.pcf != '1':
            return out
        #controllo partite
        p = []
        rb = False
        for scad in doc.regcon.scad:
            if doc.regcon.config.pcfimp == '1':
                iop = scad.pcf.imptot
                iot = scad.pcf.imppar
            elif doc.regcon.config.pcfimp == '2':
                iop = scad.pcf.imppar
                iot = scad.pcf.imptot
            else:
                iop = iot = None
            sf = scad.samefloat
            if iop is not None and (not sf(scad.importo, iop) or not sf(iot, 0)):
                if scad.pcf.riba == 1:
                    s = 'R.B.'
                    rb = True
                else:
                    s = 'Partita'
                s += ' in scadenza al %s,' % scad.dita(scad.pcf.datscad)
                s += 'saldo=%s' % scad.sepn((scad.pcf.imptot or 0)-
                                            (scad.pcf.imppar or 0),
                                            bt.VALINT_DECIMALS)
                p.append(s)
        if p:
            msg =\
                """Attenzione\n\nLe partite derivanti da questo """\
                """documento risultano richiamate da altre registrazioni."""\
                """\nProseguendo, tali partite verranno disallineate tra """\
                """le registrazioni coinvolte"""
            if rb:
                msg +=\
                    """.\n\nInoltre, sono presenti anche ricevute bancarie """\
                    """già emesse: salvare nuovamente questo documento """\
                    """comporterà la loro riemissione"""
            msg += ":\n\n%s\n\n" % '\n'.join(p)
            msg +=\
                """Se si prosegue, sarà opportuno verificare la """\
                """situazione dello scadenzario di questa anagrafica"""
            if rb:
                msg +=\
                    """, nonché lo stato di emissione delle sue r.b."""
            msg += "\n\nConfermi la riapertura del documento?"
            style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
            if MsgDialog(self, msg, style=style) != wx.ID_YES:
                out = False
        return out

    def GetLimits(self, magid, dreg):
        dbdoc = adb.DbTable(bt.TABNAME_MOVMAG_H, "doc")
        dbdoc.AddJoin(bt.TABNAME_CFGMAGDOC, "tipdoc")
        if self.dbdoc.config.docfam:
            dbdoc.AddFilter("tipdoc.docfam=%s", self.dbdoc.config.docfam)
        else:
            dbdoc.AddFilter("doc.id_tipdoc=%s", self.cauid)
        if not self.dbdoc.config.nonumxmag:
            dbdoc.AddFilter("doc.id_magazz=%s", magid)
        if dreg is None:
            dreg = Env.Azienda.Login.dataElab
        dbdoc.AddFilter("YEAR(doc.datdoc)=%s", dreg.year)
        dbdoc.Synthetize()
        dbdoc.AddMinimumOf("numdoc")
        dbdoc.AddMinimumOf("datreg")
        dbdoc.AddMaximumOf("numdoc")
        dbdoc.AddMaximumOf("datreg")
        if not dbdoc.Retrieve():
            aw.awu.MsgDialog(self, message=repr(dbdoc.GetError()))
        values = dbdoc.min_numdoc, dbdoc.min_datreg,\
               dbdoc.max_numdoc, dbdoc.max_datreg
        return values
    
    def OnButDoc(self, event):
        if self.status == STATUS_GETKEY:
            if self.ValidateDates():
                if hasattr(self, 'isediting'):
                    del self.isediting
                    self.SetRegStatus(STATUS_EDITING)
                else:
                    if self.IsDocValid(docload=True):
                        if self.status == STATUS_GETKEY and self.TestNumDoc():
                            if self.TestPcf():
                                doc = self.dbdoc
                                c = self.controls["id_pdc"]
                                if doc.cfgdoc.pdcdamag:
#                                    doc.id_pdc = doc.magazz.id_pdc
                                    def InitAnag(*args):
                                        c.SetValue(doc.magazz.id_pdc)
                                    wx.CallAfter(InitAnag)
                                self.SetRegStatus(STATUS_EDITING)
                                c.SetFocus()
        else:
            self.isediting = True
            self.SetRegStatus(STATUS_GETKEY)
        event.Skip()
    
    def ValidateDates(self):
        out = True
        cn = self.FindWindowByName
        dl = Env.Azienda.Login.dataElab
        dr = cn('datreg').GetValue()
        if self.dbdoc.cfgdoc.datdoc == '3':
            dd = dr
        else:
            dd = cn('datdoc').GetValue()
        err = None
        if not err and (not dr or not dd):
            err = 'Definire la data di registrazione e la data del documento'
        if not err and dr<dd:
            err = 'La data di registrazione non può essere antecedente la data documento'
        if not err and dr.year > dl.year:
            err = "L'anno della data di registrazione è successivo alla data di login"
        if not err:
            doc = self.dbdoc
            cfg = doc.cfgdoc
            riv = doc.GetRegIva()
            dbriv = adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
            dbriv.Get(riv)
            if cfg.colcg == 'X':
                p = doc._info.progr
                p.ClearFilters()
                p.AddFilter('progr.codice=%s', 'ccg_aggcon')
                p.AddFilter('progr.keydiff=%s', 0)
                ducc = None #data ultima chiusura contabile
                if p.Retrieve() and p.OneRow():
                    ducc = p.progrdate
                if ducc is None:
                    err =\
                        """Manca la data dell'ultimo aggiornamento contabile.\n"""\
                        """Per proseguire, completare il setup dei progressivi """\
                        """contabili."""
                elif dr<=ducc:
                    err =\
                        """La data di registrazione è antecedente l'ultima\n"""\
                        """chiusura contabile."""
                if not err and riv is not None:
                    #controllo sequenza protocollo
                    ni = cn('numiva').GetValue()
                    if ni and dr:
                        db = adb.db.__database__
                        year = dr.year
                        cmd = """
                        SELECT COUNT(reg.id)
                          FROM contab_h reg
                         WHERE reg.id_regiva=%(riv)s AND YEAR(reg.datreg)=%(year)s AND reg.datreg>"%(dr)s" AND reg.numiva<%(ni)s
                         """ % locals()
                        if db.Retrieve(cmd):
                            if (db.rs[0][0] or 0) > 0:
                                err =\
                                """Sono presenti registrazioni successive con protocollo inferiore."""
                        else:
                            err = 'Errore in controllo protocollo iva\n\n%s' % db.dbError.description
                if not err and riv is not None:
                    #controllo progressivi liquidazione
                    p.ClearFilters()
                    p.AddFilter('progr.codice=%s', 'iva_debcred')
                    p.AddFilter('progr.keydiff=%s', Env.Azienda.Login.dataElab.year)
                    duli = None #data ultima liquidazione iva
                    if p.Retrieve() and p.OneRow():
                        duli = p.progrdate
                    if duli is None:
                        pass
#                        err =\
#                            """Manca la data dell'ultima liquidazione iva.\n"""\
#                            """Per proseguire, completare il setup dei progressivi """\
#                            """di liquidazione."""
                    elif dr<=duli:
                        err =\
                            """La data di registrazione è antecedente l'ultima\n"""\
                            """liquidazione iva."""
                    if not err:
                        usri = dbriv.lastprtdat #data ultima stampa reg.iva
                        if usri is not None and dr<=usri:
                            err =\
                            """La data di registrazione è antecedente l'ultima\n"""\
                            """stampa del registro iva."""
        if not err and dr.year < Env.Azienda.Login.dataElab.year-1:
            if MsgDialog(self, "L'anno della data di registrazione è troppo indietro rispetto alla data di login.\n\nConfermi l'operazione?", style=wx.ICON_WARNING|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                out = False
        if not err and dd.year < Env.Azienda.Login.dataElab.year-1:
            if MsgDialog(self, "L'anno della data documento è troppo indietro rispetto alla data di login.\n\nConfermi l'operazione?", style=wx.ICON_WARNING|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                out = False
        if not err and dd > Env.Azienda.Login.dataElab:
            if MsgDialog(self, "La data del documento è successiva alla data di login.\n\nConfermi l'operazione?", style=wx.ICON_WARNING|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                out = False
        if err:
            aw.awu.MsgDialog(self, err, style=wx.ICON_ERROR)
            out = False
        else:
            self.dbdoc.datreg = dr
            self.dbdoc.datdoc = dd
        return out
    
    def OnButPrint(self, event):
        if self.PrintDoc():
            if self.status == STATUS_EDITING:
                if self.onedoconly_id:
                    event.Skip()
                else:
                    self.SetRegStatus(STATUS_SELCAUS)
    
    def OnButModify(self, event):
        if self.status == STATUS_DISPLAY and self.canedit:
            if self.TestCanModify():
                if self.TestPcf():
                    self.SetRegStatus(STATUS_EDITING)
                    self.UpdateBodyButtons()
        event.Skip()
    
    def TestCanModify(self):
        """
        Verifica la possibilità di mofidicare il documento.
        Casi in cui la modifica non è possibile:
            Se il documento è contabilizzato:
                registrazione già stampata sul giornale
                registrazione già stampata sul registro iva
                data registrazione precedente l'ultima stampa definitiva del giornale
                data registrazione precedente l'ultima stampa definitiva del registro iva
        """
        out = True
        doc = self.dbdoc
        reg = doc.regcon
        err = None
        if reg.id:
            if reg.st_giobol == 1:
                err = 'è già stata stampata in definitivo sul giornale'
            elif reg.st_regiva == 1:
                err = 'è già stata stampata in definitivo sul registro iva'
            if not err:
                p = adb.DbTable(bt.TABNAME_CFGPROGR, 'progr')
                if p.Retrieve('progr.codice="ccg_giobol"') and doc.datreg<p.progrdate:
                    err = "è antecedente l'ultima stampa definitiva del giornale"
            if not err:
                if doc.datreg<reg.regiva.lastprtdat:
                    err = "è antecedente l'ultima stampa definitiva del registro iva"
            if err:
                err = 'La registrazione contabile derivante da questo documento\n%s' % err
        if err:
            aw.awu.MsgDialog(self, message=err, caption="Impossibile modificare",
                             style=wx.ICON_ERROR)
            out = False
        return out
    
    def OnButAcquis(self, event):
        self.AcqDoc()
        self.gridbody.ResetView()
        event.Skip()
    
    def OnAnagChanged(self, event):
        DbgMsg('OnAnagChanged, control=%s' %event.GetEventObject().GetName())
        self.UpdateHeadAnag(initAll=True)
        doc = self.dbdoc
        cn = self.FindWindowByName
        try:
            if getattr(self.dbanag.status, 'nomov_%s' % doc.cfgdoc.clasdoc) == 1:
                aw.awu.MsgDialog(self, "%s - %s\nAnagrafica non utilizzabile in questo documento" % (doc.pdc.codice, doc.pdc.descriz), 
                                 caption="Restrizioni sullo status (%s - %s)" % (self.dbanag.status.codice, self.dbanag.status.descriz), 
                                 style=wx.ICON_WARNING)
                cn('id_pdc').SetValue(None)
        except:
            pass
        def UpdateHead():
            for name in\
                """id_pdc id_dest id_modpag id_bancf id_speinc id_agente """\
                """id_zona id_valuta id_tiplist id_aliqiva desrif numrif """\
                """datrif noteint notedoc sconto1 sconto2 sconto3 sconto4 sconto5 sconto6""".split():
                if name != 'notedoc' or doc.cfgdoc.aanotedoc != 1:
                    setattr(doc, name, cn(name).GetValue())
            if bt.MAGNUMLIS > 0:
                if doc.mov.RowsCount()>0 and doc.id_tiplist is not None\
                   and self.oldlist is not None and doc.id_tiplist != self.oldlist:
                    msg =\
                        """L'anagrafica selezionata ha un listino diverso """\
                        """da quello attualmente in uso: applico il nuovo """\
                        """listino alle righe già presenti?"""
                    self.CheckVariaListino(msg)
            if doc.id_tiplist is not None:
                self.oldlist = doc.id_tiplist
            doc.MakeTotals()
            self.SetEnableHeadControls(True)
            self.EnableFootControls()
        wx.CallAfter(UpdateHead)
        if self.interrpdc:
            self.InterrPdc()
        if self._testload:
            if not doc.config.ctrnum and doc.id is None and doc.datdoc:
                ds = self._docsearch
                if ds.Retrieve(r'doc.id_tipdoc=%s AND doc.id_pdc=%s AND YEAR(doc.datdoc)=%s AND doc.numdoc=%s',
                               doc.id_tipdoc, doc.id_pdc, doc.datdoc.year, doc.numdoc):
                    if ds.OneRow():
                        if MsgDialog(self, 'Attenzione!\n\nQuesto documento è già presente!\nVuoi richiamarlo?',
                                     style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                            self.DocLoad(ds.id)
                            self.UpdateDocIdControls()
                            MsgDialog(self, 'Il documento è stato richiamato, non lo stai inserendo',
                                      style=wx.ICON_INFORMATION)
                del ds
        wx.CallAfter(self.TestModPagStatusAnag)
        event.Skip()
    
    def TestModPagStatusAnag(self):
        try:
            doc = self.dbdoc
            if (doc.modpag.tipo or ' ') in 'RI' and self.dbanag.status.noeffetti == 1:
                aw.awu.MsgDialog(self, "%s - %s\nMod.Pagamento con effetti non utilizzabile su questa anagrafica" % (doc.pdc.codice, doc.pdc.descriz), 
                                 "Restrizioni sullo status (%s - %s)" % (self.dbanag.status.codice, self.dbanag.status.descriz), 
                                 style=wx.ICON_WARNING)
                self.controls['id_modpag'].SetValue(None)
                return False
        except:
            pass
        return True
    
    def SetEnableHeadControls(self, s):
        self.setenablecontrols = s
    
    def PrintDoc(self, doc=None):
        
        if not self.Validate():
            return False
        
        if doc is None:
            doc = self.dbdoc
            
        cfg = doc.cfgdoc
        tool = cfg.toolprint
        if not tool:
            aw.awu.MsgDialog(self, message="Manca definizione stampa documento")
            return False
        
        sendem = False
        copies = cfg.copies
        
        if self.status == STATUS_EDITING:
            sei = doc.SendMail_Prepare()
            if sei.sendto and sei.request:
                sendem = True
                msg = sei.request
                if sei.errors:
                    s = wx.ICON_ERROR
                else:
                    s = wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT
                    msg += "Confermi l'invio?"
                if aw.awu.MsgDialog(self, msg, "Documento via email", style=s) == wx.ID_YES:
                    anag = doc.GetAnag()
                    if hasattr(anag, 'noexmail'):
                        if copies>1 and anag.noexemail != 1:
                            copies -= 1
                else:
                    sendem = False
        
        if self.status == STATUS_EDITING:
            self.dbdoc.f_printed = 1
            if not self.DocSave(doc):
                return False
            self.UpdateDocIdControls()
            self.UpdateButtons()
            
        doc._info.anag = doc.GetAnag()
        
        def MoveFirst(rpt, dbt):
            dbt.mov.MoveFirst()
        
        def PrintOtherQuestionsFiller(p):
            wdr.PrintOtherQuestionsFunc(p)
            pcn = p.FindWindowByName
            si = pcn('staint')
            si.SetValue(cfg.staintest == 'X')
            if cfg.askstaint != 'X':
                si.Hide()
            sp = pcn('stapre')
            sp.SetValue(getattr(doc._info.anag, 'ddtstapre', 0) == 1)
            if getattr(doc._info.anag, 'ddtfixpre', 0):
                sp.Disable()
            if cfg.askstapre != 'X':
                sp.Hide()
        
        def PrintOtherQuestionsReactor(dlg):
            pcn = dlg.FindWindowByName
            doc._info.report_askstaint_reply = (pcn('staint').IsChecked())
            doc._info.report_askstapre_reply = (pcn('stapre').IsChecked())
        
        def PrintMultiCopiaInit(multicopia):
            for mc in multicopia:
                if 'vettore' in mc[0].lower():
                    if getattr(doc, 'enable_nocodevet', False) or doc.id_travet:
                        mc[1] = 1
        
        pathname = doc.GetPrintPathName()
        filename = doc.GetPrintFileName()
        r = rpt.Report(self, doc, tool, noMove=True, startFunc=MoveFirst,
                       printer=cfg.printer, copies=copies, 
                       changepathname=pathname, changefilename=filename,
                       otherquestions_filler=PrintOtherQuestionsFiller,
                       otherquestions_reactor=PrintOtherQuestionsReactor,
                       multicopia_init=PrintMultiCopiaInit)
        
        out = False
        ur = r.GetUsedReport()
        if ur is not None and ur.completed:
            out = True
        
        if out and sendem:
            progr = aw.awu.WaitDialog(self, message="Invio email a: %s" % sei.sendto)
            try:
                try:
                    doc.SendMail(sei, r.GetFileName())
                    doc.f_emailed = 1
                    doc.Save()
                except Exception, e:
                    aw.awu.MsgDialog(self, "Problema nell'invio dell'email:\n%s" % repr(e.args),
                                     style=wx.ICON_ERROR)
            finally:
                progr.Destroy()
        
        return out
    
    def UpdateHeadAnag(self, initAll=False):
        DbgMsg('UpdateHeadAnag')
        idpdc = self.controls["id_pdc"].GetValue()
        doc = self.dbdoc
        doc.id_pdc = idpdc
        anag = doc.GetAnag()
        self.dbanag = anag
        copyCols = """indirizzo cap citta prov nazione piva codfisc"""
        if initAll:
            copyCols += """ id_modpag id_speinc id_aliqiva id_agente id_zona id_tiplist """\
                     """sconto1 sconto2 sconto3 sconto4 sconto5 sconto6"""
            if bt.CONATTRITACC and doc.cfgdoc.sogritacc:
                ra = 0
                if hasattr(anag, 'sogritacc'):
                    ra = anag.sogritacc or 0
                doc.sogritacc = ra
                sra = self.FindWindowByName('sogritacc')
                sra.SetValue(ra)
                sra.TestPercentuali(doc)
        copyCols = copyCols.split()
        hcol = {}
        hcol["descriz"] = doc.pdc.descriz
        for field in copyCols:
            if anag is None:
                value = None
            else:
                if field == 'id_modpag' and doc.cfgdoc.id_modpag is not None:
                    value = doc.cfgdoc.id_modpag
                    self.controls[field].SetValue(value)
                    continue
                else:
                    value = anag.GetValue(field)
            hcol[field] = value
            if self.controls.has_key(field):
                c = self.controls[field]
                if hasattr(c, 'SetValueSilent'):
                    SetVal = c.SetValueSilent
                else:
                    SetVal = c.SetValue
                SetVal(value)
        nc = nd = ''
        if anag is not None:
            if 'note' in anag.GetFieldNames():
                nc = anag.note or ''
            if 'notedoc' in anag.GetFieldNames() and doc.cfgdoc.aanotedoc != 1:
                nd = anag.notedoc or ''
        self.controls['notecli'].SetValue(nc)
        self.controls['notecli2'].SetValue(nc)
        self.SetAnagFilters()
        if initAll:
            destid = None
            try:
                #impostazione destinatario preferito
                if anag.dest.Locate(lambda x: x.pref == 1):
                    destid = anag.dest.id
            except:
                pass
            self.controls['id_dest'].SetValue(destid)
            if doc.id is None:
                self.controls["notedoc"].SetValue(nd)
            if not doc.cfgdoc.askmpnoeff:
                banid = None
                try:
                    #impostazione banca preferita
                    banid = anag.banche.id
                except:
                    pass
                self.controls["id_bancf"].SetValue(banid)
        if hcol['nazione'] and hcol['nazione'] != 'IT': 
            hcol['piva'] = hcol['nazione']+hcol['piva']
        ind = ''
        x = hcol["indirizzo"]
        if x:
            ind += ('%s' % x)
        x = hcol["cap"]
        if x:
            ind += (' - %s' % x)
        x = hcol["citta"]
        if x:
            ind += (' %s' % x)
        x = hcol["prov"]
        if x:
            ind += (' (%s)' % x)
        for name, field in (\
            ("anagrs", (hcol["descriz"] or "").replace('&', '&&')),\
            ("anagaddr", ind),\
            ("anagcodfisc", hcol["codfisc"] or ""),\
            ("anagpiva", hcol["piva"] or "")):
            self.controls[name].SetLabel(field)
        self.Layout()

    def UpdateHeadDest(self, initAll=True, update_nocodedes=True):
        
        cn = self.FindWindowByName
        
        doc = self.dbdoc
        dest = self.dbdoc.dest
        
        if dest.contatto:
            contact = "Contatto: %s" % dest.contatto
        else:
            contact = ""
            
        if getattr(doc, 'enable_nocodedes', False):
            ddes = doc.nocodedes_descriz
            dind = doc.nocodedes_indirizzo
            dcap = doc.nocodedes_cap
            dcit = doc.nocodedes_citta
            dprv = doc.nocodedes_prov
        else:
            ddes = dest.descriz
            dind = dest.indirizzo
            dcap = dest.cap
            dcit = dest.citta
            dprv = dest.prov
            if update_nocodedes:
                cn("nocodedes_descriz").SetValue(ddes or '')
                cn("nocodedes_indirizzo").SetValue(dind or '')
                cn("nocodedes_cap").SetValue(dcap or '')
                cn("nocodedes_citta").SetValue(dcit or '')
                cn("nocodedes_prov").SetValue(dprv or '')
        
        d = ''
        if dind:
            if d:
                d += ' - '
            d += dind
        if dcap:
            if d:
                d += ' - '
            d += dcap
        if dcit:
            if d:
                d += ' - '
            d += dcit
        if dprv:
            d += (' (%s)' % dprv)
        for name, field in (("destrs",      ddes or ""),\
                            ("destaddr",    d),\
                            ("destcontact", contact)):
            cn(name).SetLabel(field)
    
    def SetAnagFilters(self):
        doc = self.dbdoc
        #if doc.id_pdc is None:
            #print "filtro su nessuno conto"
        #else:
            #print "filtro su conto %d" % doc.id_pdc
        for ctr in (self.controls["id_dest"],\
                    self.controls["id_bancf"]):
            if doc.id_pdc is None:
                ctr.SetFilter("id_pdc<0")
            else:
                ctr.SetFilter("id_pdc=%d" % doc.id_pdc)
    
    def OnDocIdChanged(self, event):
        name = event.GetEventObject().GetName()
        value = event.GetEventObject().GetValue()
        self.TestDocIdChanges(name, value)
        event.Skip()
    
    def TestDocIdChanges(self, name, value):
        doc = self.dbdoc
        if name == "id_magazz":
            doc.id_magazz = value
            self.EnableDocIdControls()
        elif name == "id_valuta":
            doc.id_valuta = value
        if name in self.dbdoc._info.fieldNames:
            setattr(doc, name, value)
            if self.status == STATUS_GETKEY:
                if   name == "datreg" and doc.cfgdoc.datdoc in '13':
                    doc.datdoc = value
                    self.controls["datdoc"].SetValue(value)
                if name in ("id_magazz", "datreg") and not doc.cfgdoc.pienum:
                    if doc.id is None:
                        self.DefNumDoc()
                        self.controls["numdoc"].SetValue(doc.numdoc)
                        self.controls["numiva"].SetValue(doc.numiva)
                if name == "numdoc" and doc.cfgdoc.numdoc == '3':
                    doc.numiva = value
                    self.controls["numiva"].SetValue(doc.numiva)
    
    def OnHeadChanged(self, event):
        
        if self.status == STATUS_SELCAUS:
            self.UpdateButtons()
            return
        
        name = event.GetEventObject().GetName()
        value = event.GetEventObject().GetValue()
        doc = self.dbdoc
        
        if name == 'id_pdc' and doc.id_pdc == value:
            return
        
        if name == 'id_tiplist' and doc.id_tiplist == value:
            return
        
        if name in doc.GetFieldNames():
            doc.__setattr__(name, value)
            if name == "id_dest":
                self.UpdateHeadDest()
        
        #if not self.loadingdoc:# and doc.modpag.tipo != 'R':
            #doc.totspese = None
        scad = (doc.totdare != doc._info.oldtot or\
                doc.id_modpag != doc._info.oldpag)
        if name in 'id_modpag,id_speinc'.split(','):
            #if name == 'id_modpag' and doc.modpag.tipo != 'R':
                #for name in 'id_bancf,id_speinc'.split(','):
                    #self.controls[name].SetValue(None)
            if name == 'id_modpag':
                if not self.TestModPagStatusAnag():
                    return
                if not doc.modpag.askbanca:
                    self.controls['id_bancf'].SetValue(None)
                if not doc.modpag.askspese:
                    s = self.controls['id_speinc'].GetValue()
                    self.controls['id_speinc'].SetValue(None)
                    doc.totspese = None
                    if s is not None:
                        s = self.controls['id_speinc'].GetValue()
                        aw.awu.MsgDialog(self, 
                                         """Il cambio di madalità di pagamento """
                                         """comporta l'azzeramento della """
                                         """banca d'appoggio e delle spese """
                                         """di incasso.""",
                                         style=wx.ICON_INFORMATION)
            self.MakeTotals()
            if self.setenablecontrols:
                self.EnableHeadControls()
                self.EnableBodyControls()
                self.EnableFootControls()
        else:
            self.IsHeadValid()
        
        if name == "id_bancf":
            if value is not None and (doc.config.askbanca != 'X' or not doc.modpag.askbanca):
                value = None
                doc.id_bancf = None
                self.FindWindowByName('id_bancf').SetValue(None)
            doc.regcon._info.id_effbap = value
        
        if name == "id_pdc":
            self.UpdateDatiScad()
            self.UpdateDatiAcconto()
            self.UpdateDatiEvas()
            self.UpdateAnagAutoNotes()
        
        if name == 'id_tiplist':
            self.CheckVariaListino("""Applico il listino selezionato alle """
                                   """righe già presenti?""")
            if value is not None:
                self.oldlist = value
        
        if self.setenablecontrols:
            self.EnableHeadControls()
            self.EnableBodyControls()
            self.EnableFootControls()
        
        self.UpdateButtons()
        
        event.Skip()
    
    def CheckVariaListino(self, msg):
        doc = self.dbdoc
        lis = self.FindWindowByName('id_tiplist').GetValue()
        if lis is not None and doc.mov.RowsCount()>0:
            r = aw.awu.MsgDialog(self, msg, 
                                 style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
            if r == wx.ID_YES:
                try:
                    doc.ApplicaListino()
                except dbm.ListinoMancanteException, e:
                    aw.awu.MsgDialog(self, e.args[0], caption="Problema in cambio prezzi")
    
    def UpdateAnagAutoNotes(self):
        def cn(x):
            return self.FindWindowByName(x)
        txt = ''
        pdcid = self.dbdoc.id_pdc
        if pdcid is not None:
            db = self.dbattanag
            db.Reset()
            db.Retrieve('attscope="pdc" and attkey=%s' % pdcid)
            txt = cn('butattach').GetAutoNotes(db)
        cn('autonotes_cli').SetText(txt)
    
    def UpdateDatiScad(self):
        def cn(x):
            return self.FindWindowByName(x)
        doc = self.dbdoc
        s = doc._info.scadenzario
        warn = ''
        pdcid = doc.id_pdc
        if pdcid:
            SetWarningPag(self.FindWindowByName('butattach'), pdcid)
            if s.Get(pdcid) and s.OneRow():
                if s.sintesi.total_saldo_ins:
                    warn = "ATTENZIONE! Insoluti aperti per un totale di %s"\
                         % Env.locale.format('%%.%sf' % bt.VALINT_DECIMALS,
                                         s.sintesi.total_saldo_ins)
        else:
            s.Reset()
        cn('warninganag').SetLabel(warn)
        for name, val in (('pcfscaduto',  s.sintesi.total_saldo_scaduto),
                          ('pcfascadere', s.sintesi.total_saldo_ascadere),
                          ('pcfinsoluti', s.sintesi.total_saldo_ins),
                          ('pcfsaldo',    s.sintesi.total_saldo)):
            cn(name).SetValue(val or 0)
        anag = doc.GetAnag()
#        if 'note' in anag.GetFieldNames():
#            if anag.note:
#                tts.Parla("Nota: "+anag.note)
        self.EnableButFido()
    
    def UpdateDatiAcconto(self):
        if bt.MAGGESACC != 1:
            return
        doc = self.dbdoc
        a = doc._info.acconti
        a.GetForPdc(doc.id_pdc)
        cn = self.FindWindowByName
        cn('accontodisp').SetValue((a.acconto_disponib or 0))
    
    def EnableButFido(self, doc=None):
        if doc is None:
            doc = self.dbdoc
        def cn(x):
            return self.FindWindowByName(x)
        cn('butfido').Enable(bt.GESFIDICLI == '1' and doc.cfgdoc.checkfido == 1)
    
    def UpdateDatiEvas(self):
        doc = self.dbdoc
        cfg = doc.cfgdoc
        if not cfg.AcquisDocs(solocheck=True):
            return
        e = self.dbevas
        pdcid = doc.id_pdc
        if pdcid is None:
            e.Reset()
        else:
            e.ClearFilters()
            e.Retrieve("doc.id_pdc=%s AND (doc.f_acq IS NULL OR doc.f_acq<>1) AND (doc.f_ann IS NULL OR doc.f_ann<>1) AND (mov.f_ann IS NULL OR mov.f_ann<>1)", pdcid)
        c = self.FindWindowByName('warningevas')
        if e.IsEmpty():
            c.SetLabel('')
        else:
            c.SetLabel('Ci sono documenti da evadere')
    
    def OnFootChanged(self, event):
        cn = self.FindWindowByName
        name = event.GetEventObject().GetName()
        doc = self.dbdoc
        if name in doc.GetFieldNames():
            value = event.GetEventObject().GetValue()
            setattr(doc, name, value)
            if name in 'id_tracur id_travet':
                if name == 'id_travet':
                    fields = 'descriz indirizzo cap citta prov id_stato codfisc piva'
                    if bt.MAGEXTRAVET:
                        fields += ' dichiar targa autista'
                    for field in fields.split():
                        v = getattr(doc.travet, field)
                        c = cn('nocodevet_%s' % field)
                        if c is not None:
                            c.SetValue(v)
                        setattr(doc, 'nocodevet_%s' % field, v)
                self.EnableDatiAcc()
            elif "nocodedes" in name and not name.startswith("enable"):
                self.UpdateHeadDest(update_nocodedes=False)
            elif name == 'nocodevet_id_stato':
                cn('nocodevet_nazione').SetValue(cn('nocodevet_id_stato').GetVatPrefix())
            elif name == 'initrasp':
                cn('butinitraspnow').Enable(not bool(value))
                
        elif name == 'butinitraspnow':
            now = Env.DateTime.now()
            doc.initrasp = now
            c = cn('initrasp')
            c.SetValue(now)
            c.SetFocus()
        
        elif name == 'butrptcolli':
            self.PrintSegnaColli()
        
        event.Skip()
    
    def PrintSegnaColli(self):
        cn = self.FindWindowByName
        totcolli = (cn('totcolli').GetValue() or 0)
        if totcolli > 0:
            dbsc = self.dbdoc.GetSegnaColli(totcolli)
            rpt.ReportLabels(self, dbsc, 'Etichette Segnacollo')
    
    def OnDocNew( self, event ):
        if self.status == STATUS_SELCAUS:
            if self.TestConfig():
                self.DocNew()
        event.Skip()
    
    def OnDocSearch( self, event ):
        if self.status == STATUS_SELCAUS:
            if self.TestConfig():
                self.DocSearch()
        elif self.status == STATUS_DISPLAY:
            self.SetRegStatus(STATUS_SELCAUS)
        event.Skip()
    
    def TestConfig(self):
        out = True
        cfg = self.dbdoc.cfgdoc
        if not cfg.askmagazz and cfg.id_magazz is None:
            aw.awu.MsgDialog(self, message=\
                             """Problema di configurazione del magazzino, """\
                             """controllare il setup della causale""",\
                             style=wx.ICON_ERROR)
            out = False
        return out
    
    def OnDisplayFidoCliente(self, event):
        self.CheckFidoCliente(messages=False)
        dlg = DisplayFidoDialog(self)
        dlg.UpdateValues(self.ctrfido)
        dlg.ShowModal()
        dlg.Destroy()
        event.Skip()
    
    def OnDisplayAccontiCliente(self, event):
        pdcid = self.dbdoc.id_pdc
        if pdcid is not None:
            dlg = SelezionaMovimentoAccontoDialog(self)
            if not self.FindWindowByName('accontodisp').GetValue():
                dlg.FindWindowByName('anchechiusi').SetValue(True)
            dlg.SetPdcId(pdcid)
            dlg.ShowModal()
            dlg.Destroy()
            event.Skip()
        
    def OnDocEnd( self, event ):
        if self.DocSave():
            if self.onedoconly_id:
                event.Skip()
            else:
                self.SetRegStatus(STATUS_SELCAUS)
    
    def CheckFidoCliente(self, messages=True):
        doc = self.dbdoc
        out = True
        if bt.GESFIDICLI == '1' and doc.cfgdoc.checkfido:
            cf = self.ctrfido
            if doc.cfgdoc.caucon.id:
                #documento contabilizzante, estremi da escludere nella ricerca partite
                e = {'cau_id':  doc.cfgdoc.caucon.id,
                     'cau_cod': doc.cfgdoc.caucon.codice,
                     'cau_des': doc.cfgdoc.caucon.descriz}
            else:
                #documento non contab. (ddt), estremi da escludere nella ricerca
                e = {'cau_id':  doc.cfgdoc.id,
                     'cau_cod': doc.cfgdoc.codice,
                     'cau_des': doc.cfgdoc.descriz}
            e['datdoc'] = doc.datdoc
            e['numdoc'] = doc.numdoc
            td = doc.totimporto
            kwa = {}
            if doc.id:
                kwa['doc_id_ex'] = doc.id
            f = cf.CheckFido(doc.id_pdc, e, td, **kwa)
            if f != 'OK' and messages:
                r = MsgDialog(self, 
                              """Sforamento del fido concesso al cliente\n"""
                              """%s\n\nProseguo lo stesso?""" % f, 
                              style=wx.ICON_WARNING|wx.YES_NO|wx.NO_DEFAULT)
                if r != wx.ID_YES:
                    out = False
            elif f != 'OK' and not messages:
                out = False
        return out
    
    def DocSave(self, doc=None):
        if doc is None:
            doc = self.dbdoc
        if doc.config.caucon.id:
            try:
                _ = doc.GetPdcIva()
            except Exception, e:
                aw.awu.MsgDialog(self, e.args[0], style=wx.ICON_ERROR)
                return False
        if doc.id_aliqiva is not None:
            for mov in doc.mov:
                if mov.id_aliqiva is not None and mov.id_aliqiva != doc.id_aliqiva:
                    msg =\
                    """Attenzione!\n"""\
                    """Sono presenti righe con aliquota IVA diversa da quella impostata nella testata.\n"""\
                    """Confermi le informazioni inserite?"""
                    if aw.awu.MsgDialog(self, msg, style=wx.ICON_INFORMATION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                        return False
                    break
        wz = self.FindWindowByName('workzone')
        if wz.GetPageText(wz.GetSelection()).lower() != 'piede':
            self.UpdatePanelFoot()
        if not self.Validate():
            return False
        if not self.rowsok:
            return False
        if len(doc._info.righep0)>0:
            if MsgDialog(self, "Sono presenti righe senza prezzo.\nConfermi l'operazione?", 
                         style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return False
        if (doc.totimporto == 0 or doc.mov.RowsCount() == 0)\
           and not doc.cfgdoc.totzero:
            err = "nullo"
        elif doc.totimporto < 0 and not doc.cfgdoc.totneg:
            err = "negativo"
        else:
            err = ""
        if err:
            MsgDialog(self, """Non è possibile confermare il documento: non può avere il totale %s""" % err)
            return False
        if doc.regcon.config.tipo == "I":
            if (bt.TIPO_CONTAB == "O" and len(doc._info.totiva) == 0) or (bt.TIPO_CONTAB == "S" and len(doc._info.totpdc) == 0):
                MsgDialog(self, """Nessun totale IVA presente, impossibile confermare il documento.""")
                return False
        
        if (doc.totimporto == 0 or doc.mov.RowsCount() == 0) and doc.cfgdoc.totzero:
            err = "nullo"
        elif doc.totimporto < 0 and doc.cfgdoc.totneg:
            err = "negativo"
        if err:
            if MsgDialog(self, "Il totale documento è %s.\nConfermi l'operazione?" % err, 
                         style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return False
        
        if bt.CONATTRITACC and doc.cfgdoc.sogritacc and doc.sogritacc:
            if not doc.samefloat(doc.impritacc, doc.totimponib):
                msg =\
                    """La ritenuta d'acconto viene calcolata su un importo """\
                    """differente dall'imponibile del documento.\nConfermi?"""
                style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
                if MsgDialog(self, msg, style=style) != wx.ID_YES:
                    return False
        
        #controllo fidi
        if not self.CheckFidoCliente():
            return False
        
        #determinazione nuovo numero documento
        if doc.id is None:# and not doc.numdoc:
            if not doc.numdoc:
                self.DefNumDoc()
            if not doc.numiva:
                self.DefNumIva()
        
        save = True
        
        if doc.cfgdoc.pienum and doc.id is None:
            #dialog conferma numero
            dlg = NumDocDialog(self, doc.cfgdoc.datdoc, doc.cfgdoc.numdoc, doc.cfgdoc.askprotiva)
            dk = {}
            for name, val in (('numdoc', doc.numdoc),
                              ('numiva', doc.numiva),
                              ('datreg', doc.datreg),
                              ('datdoc', doc.datdoc),
                              ('id_tipdoc', doc.id_tipdoc),
                              ('id_magazz', doc.id_magazz),
                              ('id_regiva', doc.GetRegIva()),):
                dk[name] = dlg.FindWindowByName(name)
                dk[name].SetValue(val)
            if dlg.ShowModal() == wx.ID_OK:
                if self.IsDocValid(docload=False, frame=dlg):
                    for name in dk:
                        if not name.startswith('id_'):
                            setattr(doc, name, dk[name].GetValue())
                else:
                    save = False
            else:
                save = False
            dlg.Destroy()
        
        chk_do, chk_des = doc.CheckNum()
        if not chk_do:
            aw.awu.MsgDialog(self, chk_des, style=wx.ICON_WARNING|wx.OK)
            save = False
        
        if not save:
            aw.awu.MsgDialog(self, 'Il documento non è stato salvato', style=wx.ICON_WARNING|wx.OK)
            return False
        
        dispnum = False
        if doc.cfgdoc.colcg and doc.cfgdoc.caucon:
            try:
                doc.CollegaCont()
            except Exception, e:
                MsgDialog(self,\
                          """Problema in contabilizzazione:\n%s\n\nCONTROLLARE MASTRO E SCADENZARIO."""\
                          % repr(e.args))
                if doc.regcon.id:
                    doc.regcon.Erase()
        
        saved = doc.Save()
        if saved:
            self.controls['butattach'].SetKey(doc.id, save=True)
            if dispnum:
                msg = "Il documento è stato salvato con il numero %d" % doc.numdoc
                MsgDialog(self, msg)
        else:
            err =\
                """Durante il salvataggio del documento, si è """\
                """verificato un problema sul database:\n\n%s"""\
                % repr(doc.GetError())
            MsgDialog(self, err)
        
        return saved

    def OnDocQuit( self, event ):
        if self.TestQuit():
            if self.onedoconly_id:
                event.Skip()
            else:
                self.SetRegStatus(STATUS_SELCAUS)

    def OnDocDelete(self, event):
        action = MsgDialog(self,\
"""Sei sicuro di voler cancellare il documento?  Confermando, non sarà """\
"""più recuperabile in alcun modo.  """\
"""Confermi l'operazione di eliminazione ?""",\
                  style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if action == wx.ID_YES:
            if self.RegDelete():
                if self.onedoconly_id:
                    event.Skip()
                else:
                    self.SetRegStatus(STATUS_SELCAUS)

    def OnResize(self, event):
        if self.IsShown():
            wx.CallAfter(self.SetProdZoneSize)
        event.Skip()
    
    def SetOneDocOnly(self, iddoc):
        self.onedoconly_id = iddoc
        if self.DocLoad(iddoc):
            for name in 'butnew butsrc'.split():
                self.FindWindowByName(name).Hide()
            p = self.GetParent()
            s = p.GetSize()
            p.SetSize((s[0]+1, s[0]+1))
            p.SetSize(s)
            self.SetRegStatus(STATUS_DISPLAY)

    def UpdateAllControls(self):
        if   self.status == STATUS_SELCAUS: lbl = "Seleziona causale"
        elif self.status == STATUS_DISPLAY: lbl = "Visualizzazione"
        elif self.status in (STATUS_GETKEY, STATUS_EDITING):
            if self.dbdoc.id is None: lbl = "Inserimento"
            else:                     lbl = "Modifica"
        if 'statusdes' in self.controls:
            self.controls["statusdes"].SetLabel(lbl)
        self.UpdateDocIdControls()
        self.UpdatePanelDocId()
        self.UpdatePanelHead()
        self.UpdatePanelBody()
        self.UpdatePanelFoot()

    def DocSearchClass( self ):
        return DocSearch
    
    def InitCausale( self ):
        """
        Inizializza il controllo della selezione causale.
        
        @return: Vero o falso a seconda che sia riuscito a caricare
        le causali.
        @rtype: bool
        """
        out = True
        ctrcau = self.controls["causale"]
        cfg = self.dbdoc.cfgdoc
        flt = "TRUE"
        #escludo eventuali documenti di trasf.mag. generati in autom.
        if cfg.Retrieve("id_tdoctra IS NOT NULL"):
            if cfg.RowsCount()>0:
                flt = "id NOT IN (%s)" % ','.join([str(c.id_tdoctra) for c in cfg])
        #testo diritti utenti su causali magazzino
        from cfg.dbtables import PermessiUtenti
        p = PermessiUtenti(ambito='caumagazz')
        p.Retrieve('perm.id_utente=%s AND perm.scrivi=1',
                   Env.Azienda.Login.userid)
        if not p.IsEmpty():
            if flt:
                flt += " AND "
            flt = "id IN (%s)" % ','.join([str(p.id_rel) for p in p])
        ctrcau.SetFilter(flt)
        self.Bind(EVT_LINKTABCHANGED, self.OnCauChanged, ctrcau)
        return out
    
    def OnCauChanged(self, event):
        """
        Callback per causale selezionata
        Vengono aggiornati i dati relativi alla causale: ::
            id
            codice
            descrizione
            configurazione
        """
        self.SetCausale()
        wx.CallAfter(self.SetProdZoneSize)
        event.Skip()
    
    def SetCausale(self):
        ci = self.FindWindowById
        cn = self.FindWindowByName
        doc = self.dbdoc
        cfg = doc.cfgdoc
        ctrcau = ci(wdr.ID_CAUSALE)
        self.cauid = ctrcau.GetValue()
        self.caudes = ctrcau.GetValueDes()
        cfg.Get(self.cauid)
        self.GridBody_Init(ci(wdr.ID_PANGRIDBODY))
        if self.cauid:
            self.SetDefaultItem(self.FindWindowByName('butnew'))
            wx.CallAfter(ctrcau.SetFocus)
        for c in (self.boxanag, ci(wdr.ID_LABELANAGHEAD)):
            c.SetLabel(cfg.descanag or 'Anagrafica')
        if cfg.id_tdoctra is None:
            filt = "id_tipo=%s" % cfg.id_pdctip
        else:
            mags = adb.DbTable(bt.TABNAME_MAGAZZ, 'mag', writable=False)
            mags.Retrieve()
            filt = "id IN (%s)" % ','.join([str(x.id_pdc)
                                            for x in mags 
                                            if x.id_pdc is not None])
        mp = self.controls['id_modpag']
        if cfg.askmpnoeff:
            filt = "tipo<>'R'"
        else:
            filt = '1'
        mp.SetFilter(filt)
        ci(wdr.ID_PDC).SetFilterValue(cfg.id_pdctip)
        ci(wdr.ID_PDC).SetFilter(filt)
        self.GridBodySetTipMovFilter()
        p = self.FindWindowByName('workzone').GetPageWithText('accomp', exact=False)
        if p:
            p.Enable(cfg.askdatiacc == "X")
        self.Freeze()
        try:
            for name in 'dati tot'.split():
                c = self.FindWindowByName('panritacc%s'%name)
                c.Show(bool(bt.CONATTRITACC and cfg.sogritacc))
            cn('panmargine').Show(bool(cfg.vismargine == 1))
            a = (bt.MAGGESACC == 1)
            if a:
                a = cfg.HasMovAcconto() or cfg.HasMovStornoAcconto()
            cn('panacconti').Show(a)
            self.Layout_()
        finally:
            self.Thaw()
        self.UpdateButtons()
        docs = cfg.AcquisDocs(solocheck=True)
        if docs:
            e = self.dbevas
            e.ClearBaseFilters()
            if len(docs) == 1:
                e.AddBaseFilter("doc.id_tipdoc=%s" % docs[0][0])
            else:
                did = ','.join(map(str, [d[0] for d in docs]))
                e.AddBaseFilter("doc.id_tipdoc IN (%s)" % did)
            e.AddBaseFilter("doc.f_acq IS NULL OR doc.f_acq<>1")
            e.AddBaseFilter("doc.f_ann IS NULL OR doc.f_ann<>1")
            e.AddBaseFilter("mov.f_ann IS NULL OR mov.f_ann<>1")
            e.ClearHavings()
            e.AddHaving('(total_evas_qta IS NULL OR total_evas_qta<mov.qta)')
    
    def SetProdZoneSize(self, force_visible=False):
        def cid(x): 
            return self.FindWindowById(x)
        cfg = self.dbdoc.cfgdoc
        prodzone = bool(cfg.viscosto or cfg.visgiac or cfg.vislistini or cfg.visultmov)
        if prodzone or force_visible:
            h = 195
        else:
            h = 0
        bz = cid(wdr.ID_BODYZONE)
        bz.SetSashPosition(bz.GetSize()[1]-h)
        if cfg.ultmovbef:
            cid(wdr.ID_BODYSTATZONE).SetSelection(1)
    
    def SetRegStatus( self, status = None):
        """
        Imposta lo status della registrazione::
            STATUS_SELCAUS - Selezione causale
            STATUS_DISPLAY - Visualizza registrazione
            STATUS_MODIFY  - Editing registrazione
        """
        oldstatus = self.status
        self.status = status
        self.SetDefaultItem(None)
        if status == STATUS_SELCAUS:
            self.DocReset()
            self.controls['butattach'].SetKey(None)
            if 'causale' in self.controls:
                self.controls['causale'].SetFocus()
            for name in 'warning,warninganag,warningevas,warningdest'.split(','):
                self.controls[name].SetLabel('')
            for name in 'pcfscaduto,pcfascadere,pcfinsoluti,pcfsaldo'.split(','):
                self.controls[name].SetValue(0)
            self.controls['autonotes_cli'].SetText('')
        if 'butdoc' in self.controls:
            bdoc = self.controls["butdoc"]
            if status in (STATUS_SELCAUS, STATUS_GETKEY):
                self.GridScadCheckImporti()
                bdoc.SetLabel("Conferma")
                if status == STATUS_GETKEY:
                    self.SetDefaultItem(bdoc)
            else:
                bdoc.SetLabel("Cambia")
        self.SetEnableHeadControls(False)
        self.UpdateAllControls()
        self.GridBodyReset()
        self.EnableAllControls()
        if status == STATUS_SELCAUS:
            nb = self.FindWindowByName('workzone')
            if nb:
                nb.SetSelection(0)
        #elif status == STATUS_GETKEY:
            #self.SetDefaultItem(self.FindWindowByName('butdoc'))
        c = self.controls['butattach']
        if status == STATUS_EDITING:
            c.SetPermissions(True, True)
            self.GridBodySetTipMovFilter()
            self.dbdoc.f_printed = 0
            self.dbdoc.f_emailed = 0
        else:
            c.SetPermissions(False, False)
        wx.CallAfter(lambda *x: self.SetEnableHeadControls(True))
        c = self.FindWindowByName('butprint')
        l = d = 'Stampa'
        if status == STATUS_EDITING:
            l += ' e chiudi'
            d += ' e chiude'
        d += ' il presente documento'
        self.SetAcceleratorKey('P', wdr.ID_BTN_PRINT, l, d)
#        if status == STATUS_SELCAUS:
#            def SetFocus():
#                self.controls['causale'].SetFocus()
#                self.SetDefaultItem(self.controls['butnew'])
#            wx.CallAfter(SetFocus)
#        elif status == STATUS_DISPLAY:
#            def SetFocus():
#                self.FindWindowByName('workzone').SetFocus()
#            wx.CallAfter(SetFocus)
#        elif status == STATUS_EDITING:
#            def SetFocus():
#                self.controls['id_pdc'].SetFocus()
#            wx.CallAfter(SetFocus)
        wx.CallAfter(self.TestWorkZoneFirstFocus)
        return oldstatus
    
    def SetDataChanged(self, changed=True):
        pass
    
    def SetEditingType( self, etype=EDITING_HEAD):
        """
        Imposta il tipo di editing attivo::
            EDITING_HEAD - Seleziona pagina testata
            EDITING_BODY - Seleziona pagina dettaglio righe
            EDITING_FOOT - Seleziona pagina piede (tot./dati acc.)
        """
        nb = self.FindWindowByName('workzone')
        nb.SetPage(etype)
        self.UpdateAllControls()
        self.EnableAllControls()
    
    def EnableAllControls(self, enable = True):
        self.UpdateButtons(enable)
        self.controls["causale"].Enable(enable and\
                                        self.status == STATUS_SELCAUS)
        self.EnableDocIdControls(enable)
        self.EnableHeadControls(enable)
        self.EnableBodyControls(enable)
        self.EnableFootControls(enable)

    def UpdateButtons(self, enable = True):
        status = self.status
        doc = self.dbdoc
        self.controls["butnew"].Enable(enable and\
                                       self.canedit and\
                                       self.canins and\
                                       self.cauid is not None and\
                                       status == STATUS_SELCAUS)
        
        self.controls["butsrc"].Enable(enable and\
                                       status == STATUS_SELCAUS and\
                                       self.cauid is not None)
        
        self.controls["butsave"].Enable(enable and\
                                        status == STATUS_EDITING and\
                                        self._headok and\
                                        self._scadok)
        
        self.controls["butprint"].Enable(enable and\
                                         status in (STATUS_DISPLAY,
                                                    STATUS_EDITING) and\
                                         self._headok and\
                                         self._scadok and\
                                         doc.cfgdoc.IsPrintable())
        
        self.controls["butmodif"].Enable(enable and\
                                         status == STATUS_DISPLAY)
        
        self.controls["butacquis"].Enable(enable and\
                                          status == STATUS_EDITING and\
                                          doc.id_pdc is not None and\
                                          doc.cfgdoc.HasAcquisDocs())
        
        self.controls["butquit"].Enable(enable and\
                                        status in (STATUS_GETKEY,\
                                                   STATUS_DISPLAY,\
                                                   STATUS_EDITING))
        
        self.controls["butdel"].Enable(enable and\
                                       self.candelete and\
                                       status == STATUS_EDITING and\
                                       self.dbdoc.id is not None)
        
        self.controls["butattach"].Enable(enable and status in (STATUS_DISPLAY,
                                                                STATUS_EDITING))
        
        if 'butdoc' in self.controls:
            self.controls["butdoc"].Enable(enable and\
                                           status in (STATUS_GETKEY,\
                                                      STATUS_EDITING))

    def RegSave(self):
        """
        Scrittura registrazione su db.
        """
        pass
    
    def Validate(self):
        for c in aw.awu.GetAllChildrens(self, lambda x: hasattr(x, 'IsTooBig')):
            if c.IsTooBig():
#                aw.awu.MsgDialog(self, "Valore numerico troppo elevato\n(%s)" % c.GetName(), style=wx.ICON_ERROR)
                return False
        return True
    
    def DocReset(self):
        self.dbdoc.Reset()
        self.dbdoc.cfgdoc.Get(self.cauid)
        self.dbdoc.CreateNewRow()
        self.GridBodyReset()
        self.GridScadReset()
        self.GridScadSetReg(self.dbdoc.regcon)
        self.gridmovi.ClearHistoryCache()
        self.canedit = True
        self.rowsok = True
        self.oldlist = None
        #self.candelete = False
        #azzeramento descrizioni main
        self.controls["anagrs"].SetLabel(self.dbpdc.descriz or "")
        for prefix in ("anag", "dest"):
            for name in ("addr1", "addr2", "piva"):
                name = prefix+name
                if name in self.controls:
                    self.controls[name].SetLabel("")
        for field in ("valuta", "magazz", "pdc", "dest", "modpag", "speinc",\
                      "aliqiva", "agente", "zona", "tiplist"):
            field = "id_%s" % field
            if field in self.controls:
                self.controls[field].SetValueSilent(None)

    def DocNew(self):
        cn = self.FindWindowByName
        if self.canins:
            self.DocReset()
            self.DefaultValues()
            self.UpdateDocIdControls()
            self.SetRegStatus(STATUS_GETKEY)
            self.TestDocIdChanges('datreg', cn('datreg').GetValue())
            for name in 'id_magazz datreg datdoc numdoc'.split():
                c = self.controls[name]
                if c.IsEnabled():
                    c.SetFocus()
                    break
            if bt.MAGNOCODEDES and bt.MAGNOCDEFDES:
                self.dbdoc.enable_nocodedes = 1
            if bt.MAGNOCODEVET and bt.MAGNOCDEFVET:
                self.dbdoc.enable_nocodevet = 1
    
    def DefaultValues(self):
        doc = self.dbdoc
        doc.id_tipdoc = self.cauid
        doc.datreg = today
        doc.f_ann = 0
        doc.f_acq = 0
        doc.f_genrag = 0
        doc.f_printed = 0
        doc.f_emailed = 0
        for name in ('id_tracau',
                     'id_tracur',
                     'id_travet',
                     'id_traasp',
                     'id_trapor',
                     'id_tracon'):
            setattr(doc, name, getattr(doc.config, name))
        magid = doc.cfgdoc.id_magazz
        if magid is None:
            magid = magazz.GetDefaultMagazz()
        doc.id_magazz = magid
    
    def DefNumDoc(self, doc=None):
        if doc is None:
            doc = self.dbdoc
        self.DefNumIva(doc=doc)
        cfg = doc.cfgdoc
        if cfg.numdoc == '3':
            doc.numdoc = doc.numiva
        self.ReadProgr()
        if cfg.numdoc == '1':#in '13':
            magid = self.FindWindowByName('id_magazz').GetValue()
            dreg = self.FindWindowByName('datreg').GetValue()
            numdocmin, datregmin, numdocmax, datregmax = self.GetLimits(magid, dreg)
            numdocmax = numdocmax or 0
            if True:#numdocmax>=doc.numdoc:
                doc.numdoc = numdocmax+1
            if cfg.numdoc == '3':
                doc.numiva = doc.numdoc
    
    def DefNumIva(self, doc=None):
        if doc is None:
            doc = self.dbdoc
        cfg = doc.cfgdoc
        tipreg = cfg.caucon.tipo
        if tipreg is None or not tipreg in 'IE':
            return
        if cfg.caucon.regivadyn == 1:
            if cfg.caucon.magriv.Locate(lambda rim: rim.id_magazz == self.FindWindowByName('id_magazz').GetValue()):
                cfg.caucon.id_regiva = cfg.caucon.magriv.id_regiva
                #print 'reg.iva cambiato in %s' % cfg.caucon.magriv.id_regiva
        regiva = cfg.caucon.regiva
        if regiva.id and doc.datreg is not None:
            #year = doc.datdoc.year
            #self._Progr_AddKeysContabTipo_I(year, regiva.id)
            #self.ReadProgr()
            #doc.numiva = self._progr_iva_ultins_num+1
            reg = self._regsearch
            reg.ClearFilters()
            reg.AddFilter('reg.id_regiva=%s', regiva.id)
            reg.AddFilter('YEAR(reg.datreg)=%s', doc.datreg.year)
            reg.Retrieve()
            doc.numiva = (reg.max_numiva or 0)+1
    
    def TestNumDoc(self):
        out = True
        doc = self.dbdoc
        c = self.FindWindowByName('id_magazz')
        if c.GetValue() is None:
            aw.awu.MsgDialog(self, message="Indicare il magazzino")
            c.SetFocus()
            out = False
        return out
    
    def UpdateDocIdControls(self):
        doc = self.dbdoc
        for f, v in (("doc_id",    doc.id),\
                     ("id_magazz", doc.id_magazz),\
                     ("id_valuta", None),\
                     ("datreg",    doc.datreg),\
                     ("datdoc",    doc.datdoc),\
                     ("numdoc",    doc.numdoc),\
                     ("numiva",    doc.numiva)):
            if f in self.controls:
                self.controls[f].SetValue(v)
    
    def RegDelete(self):
        out = True
        doc = self.dbdoc
        if doc.id_reg is not None:
            reg = doc.regcon
            reg.Erase()
            if out:
                doc.id_reg = None
            else:
                awc.util.MsgDialog(self, message=\
                    "Errore nella cancellazione della registrazione contabile:"+\
                    "\n %s" % repr(reg.GetError()))
        if out:
            docid = doc.id
            out = doc.Erase()
            if out:
                self.controls['butattach'].SetKey(docid, delete=True)
            else:
                awc.util.MsgDialog(self, message=\
                    "Errore nella cancellazione del documento:"+\
                    "\n %s" % repr(doc.GetError()))
        return out
    
    def UpdatePanelHead(self):
        names = """id_pdc id_dest id_modpag id_agente id_zona id_valuta id_tiplist id_aliqiva """\
                """datrif numrif desrif noteint notedoc f_ann f_acq """\
                """sconto1 sconto2 sconto3 sconto4 sconto5 sconto6""".split()
        if not self.dbdoc.cfgdoc.askmpnoeff:
            names.append("id_bancf")
            names.append("id_speinc")
        for name in names:
            if name != 'notedoc' or self.dbdoc.cfgdoc.aanotedoc != 1:
                self.controls[name].SetValueSilent(\
                    self.dbdoc.__getattr__(name))
        self.FindWindowById(wdr.ID_STATUSACQ).UpdateText(self.dbdoc)
        self.UpdateHeadAnag()
        self.UpdateHeadDest()
    
    def UpdatePanelDocId(self):
        """
        Aggiorna i controlli della testata.
        """
        doc_id = self.controls["doc_id"]
        magazz = self.controls["id_magazz"]
        valuta = self.controls["id_valuta"]
        datreg = self.controls["datreg"]
        datdoc = self.controls["datdoc"]
        numdoc = self.controls["numdoc"]
        numiva = self.controls["numiva"]
        
        if self.status == STATUS_SELCAUS:
            doc_id.SetValueSilent(None)
            magazz.SetValueSilent(None)
            valuta.SetValueSilent(None)
            datreg.SetValueSilent(None)
            datdoc.SetValueSilent(None)
            numdoc.SetValueSilent(0)
            numiva.SetValueSilent(0)
        else:
            doc = self.dbdoc
            doc_id.SetValueSilent(doc.id)
            magazz.SetValueSilent(doc.id_magazz)
            valuta.SetValueSilent(None)
            datreg.SetValueSilent(doc.datreg)
            datdoc.SetValueSilent(doc.datdoc)
            numdoc.SetValueSilent(doc.numdoc)
            numiva.SetValueSilent(doc.numiva)

    def EnableHeadControls(self, enable = True):
        en = enable and self.status == STATUS_EDITING
        cfg = self.dbdoc.cfgdoc
        mpa = self.dbdoc.modpag
        c = self.controls
        c["f_ann"].Enable(en)
        c["f_acq"].Enable(en)
        c["id_pdc"].Enable(en)
        c["id_modpag"].Enable(en and cfg.askmodpag)
        c["id_speinc"].Enable(en and cfg.askmodpag and bool(mpa.askspese) and bool(cfg.askbanca))
        #c["id_speinc"].Enable(en and cfg.askmodpag)
        c["id_bancf"].Enable(en and cfg.askmodpag and bool(mpa.askbanca) and bool(cfg.askbanca))
        #c["id_bancf"].Enable(en and cfg.askmodpag and bool(cfg.askbanca))
        c["sconto1"].Enable(en)
        c["sconto2"].Enable(en)
        c["sconto3"].Enable(en)
        c["sconto4"].Enable(en)
        c["sconto5"].Enable(en)
        c["sconto6"].Enable(en)
        c["id_agente"].Enable(en and cfg.askagente)
        c["id_zona"].Enable(en and cfg.askzona)
        c["id_tiplist"].Enable(en and cfg.asklist)
        c["id_dest"].Enable(en and cfg.askdestin and not bool(getattr(self.dbdoc, 'enable_nocodedes', False)))
        c["id_aliqiva"].Enable(en)
        c["desrif"].Enable(en and cfg.askrifdesc)
        c["datrif"].Enable(en and cfg.askrifdata)
        c["numrif"].Enable(en and cfg.askrifnum)
        c["noteint"].Enable(en)
        c["notecli"].Enable(False)
        c["notecli2"].Enable(False)
        h = self.FindWindowByName('workzone').GetPageWithText('testa', exact=False)
        for n in range(6):
            l = n+1
            s = h.FindWindowByName('sconto%d'%l)
            s.Enable(en and (not (cfg.numsconti) or l<=cfg.numsconti))
    
    def EnableFootControls(self, enable=True):
        enable = enable and self.status == STATUS_EDITING
        enable = enable and self.IsHeadValid()
        scadenab = enable
        if scadenab and self.dbdoc.cfgdoc.caucon.pcf != '1':
            scadenab = False
        self.GridScadSetCanEdit(scadenab)
        self.FindWindowByName('notedoc').Enable(enable)
        self.EnableDatiAcc()
        self.EnableRitAccControls(enable)
    
    def EnableRitAccControls(self, enable=True):
        def cn(x):
            return self.FindWindowByName(x)
        enable = enable and bool(bt.CONATTRITACC and self.dbdoc.cfgdoc.sogritacc)
        for name in 'dati tot'.split():
            cn('panritacc%s'%name).Enable(enable)
        enable = enable and cn('sogritacc').GetValue()
        for name in 'per com imp'.split():
            cn('%sritacc'%name).Enable(enable)
        cn('butritacc').Enable(enable)
    
    def EnableDatiAcc(self):
        doc = self.dbdoc
        cfgdoc = doc.config
        ctrls = self.controls
        for name in ('tracau',
                     'tracur',
                     'travet',
                     'traasp',
                     'trapor'):
            enab = cfgdoc.askdatiacc == 'X' and getattr(cfgdoc, 'ask'+name) == 'X'
            if name == 'travet':
                enab = enab and bool(doc.tracur.askvet) and not self.FindWindowByName('enable_nocodevet').IsChecked()
            ctrls['id_'+name].Enable(self.status == STATUS_EDITING and enab)
        enab = cfgdoc.askdatiacc == 'X' and cfgdoc.asktracon == 'X' and doc.modpag.contrass == 1
        for name in 'id_tracon impcontr'.split():
            ctrls[name].Enable(self.status == STATUS_EDITING and enab)
        enab = cfgdoc.askdatiacc == 'X'
        for name in 'notevet totpeso totcolli initrasp'.split():
            ctrls[name].Enable(self.status == STATUS_EDITING and enab)
        cn = self.FindWindowByName
        cn('butinitraspnow').Enable(self.status == STATUS_EDITING and not bool(cn('initrasp').GetValue()))
        cn('butrptcolli').Show(cfgdoc.rptcolli == 1)
        #abilitazione campi destinatario non codificato
        e = (bt.MAGNOCODEDES and self.status == STATUS_EDITING and enab and cfgdoc.askdatiacc == 'X' and cfgdoc.askdestin == 'X' and doc.id_dest is None)
        self.FindWindowByName('enable_nocodedes').Enable(e)
        e = e and cn('enable_nocodedes').IsChecked()
        for ctrl in aw.awu.GetAllChildrens(self, lambda x: x.GetName().startswith('nocodedes')):
            ctrl.Enable(e)
        #abilitazione campi vettore non codificato
        e = (bt.MAGNOCODEVET and self.status == STATUS_EDITING and enab and cfgdoc.askdatiacc == 'X' and cfgdoc.asktravet == 'X' and doc.id_travet is None)
        self.FindWindowByName('enable_nocodevet').Enable(e)
        e = e and cn('enable_nocodevet').IsChecked()
        for ctrl in aw.awu.GetAllChildrens(self, lambda x: x.GetName().startswith('nocodevet')):
            ctrl.Enable(e)
    
    def EnableDocIdControls(self, enable = True):
        """
        Abilita o meno i controlli della testata in base alla
        configurazione della causale.
        """
        enable = enable and self.status == STATUS_GETKEY
        
        cfg = self.dbdoc.cfgdoc
        self.controls["id_magazz"].Enable(enable and cfg.askmagazz)
        enable = enable and self.controls["id_magazz"].GetValue() is not None
        self.controls["datreg"].Enable(enable)
        self.controls["doc_id"].Enable(False)
        self.controls["datdoc"].Enable(enable and cfg.datdoc != '3')
        self.controls["numdoc"].Enable(enable)
        self.controls["numiva"].Enable(enable\
                                       and cfg.askprotiva is not None\
                                       and len(cfg.askprotiva)>0\
                                       and cfg.askprotiva in "012")
        self.controls["id_valuta"].Enable(enable and False)
    
    def EnableBodyControls(self, enable = True):
        enable = enable and self.status == STATUS_EDITING and self.IsHeadValid()
        nb = self.FindWindowByName('workzone')
        def test(c):
            out = True
            name = c.GetName()
            if name is not None:
                out = not c.GetName().startswith('butprod')
            return out
        p = nb.GetPageWithText('Corpo')
        self.EnableControls(enable, p, test)
        self.gridbody.Refresh()
        self.UpdateBodyButtons()
        show = enable and self.status == STATUS_EDITING
        showpdt = show
        if show:
            showpdt = self.dbdoc.cfgdoc.GetAcqPDTMov() is not None
        self.controls["btnacqpdt"].Show(showpdt)
        showbcd = self.dbdoc.cfgdoc.printetic == 1
        b = self.controls["btnetic"]
        #b.Enable(self.dbdoc.mov.RowsCount()>0)
        b.Show(showbcd)
        b.GetParent().Layout()
    
    def EnableControls(self, enable, parent, func=None):
        if func is None:
            func = lambda *x: True
        #DbgMsg('enable=%s on controls of %s' % (enable, parent.GetName()))
        ctrls = aw.awu.GetAllChildrens(parent)
        for c in ctrls:
            if isinstance(c, (wx.TextCtrl, wx.Button, dbglib.DbGrid)):
                if func(c):
                    c.Enable(enable)
    
    def IsHeadValid(self):
        
        warn = self.FindWindowById(wdr.ID_WARNING)
        warn.SetLabel('')
        
        #if self.status != STATUS_EDITING:
            #return True
        
        def CtrMissing(self, ctrname):
            return self.controls[ctrname].GetValue() is None
        
        valid = True
        err = []
        doc = self.dbdoc
        cfg = doc.cfgdoc
        pdc = doc.pdc
        if CtrMissing(self, "id_pdc"):
            valid = False
        else:
            if cfg.askmodpag and CtrMissing(self, "id_modpag"):
                err.append("la mod.pagamento")
            if cfg.askmodpag and CtrMissing(self, "id_bancf") and\
               doc.modpag.askbanca and cfg.askbanca:# and pdc.tipana.tipo == 'C':
                err.append("la banca d'appoggio")
            if cfg.askagente and CtrMissing(self, "id_agente"):
                err.append("l'agente")
            if cfg.askzona   and CtrMissing(self, "id_zona"):
                err.append("la zona")
            if cfg.asklist   and CtrMissing(self, "id_tiplist"):
                err.append("il listino")
        if err:
            warn.SetLabel('Indicare '+', '.join(err))
            valid = False
        else:
            if cfg.id_tdoctra is not None:
                if doc.id_pdc == doc.magazz.magpdc.id:
                    warn.SetLabel('Il magazzino non può essere lo stesso di partenza')
                    valid = False
        self._headok = valid
        return valid

    def GetPdcDialogClass(self, *args):
        tipo = self.dbdoc.cfgdoc.id_pdctip
        return autil.GetPdcDialogClass(tipo)

    def GetInterrPdcFrameClass(self, *args):
        tipo = self.dbdoc.cfgdoc.id_pdctip
        return contab.GetInterrPdcFrameClass(tipo)

    def MakeTotals(self, *args, **kwargs):
        self.dbdoc.MakeTotals(*args, **kwargs)
        self.dbdoc.regcon._info.id_effbap =\
            self.FindWindowByName("id_bancf").GetValue()
        self.CheckScad()

    def CheckScad(self):
        doc = self.dbdoc
        if doc.cfgdoc.caucon.pcf != '1':
            return True
        self._scadok = doc.modpag.id_pdcpi \
            or doc.samefloat(doc.totdare,\
                             self.dbreg.scad.GetTotalOf('importo'))
        if self._scadok:
            ud = []
            for s in doc.regcon.scad:
#                if not s.datscad or s.datscad<doc.datdoc or s.datscad in ud:
                if not s.datscad or s.datscad in ud:
                    self._scadok = False
                    break
                ud.append(s.datscad)
        self.UpdateButtons()
        return self._scadok

    def DocSearch( self ):
        out = False
        if self.cauid is not None:
            srccls = self.DocSearchClass()
            if srccls is not None:
                dlg = srccls(self, self.cauid, self.caudes, 
                             self.dbdoc.cfgdoc.numdoc)
                dlg.db_curs = self.db_curs
                #if self.dbdoc.cfgdoc.ctrnum:
                    #dlg.SetOrderDocOut()
                #else:
                    #dlg.SetOrderDocIn()
                idreg = dlg.ShowModal()
                dlg.Destroy()
                if idreg >= 0:
                    self.loadingdoc = True
                    #previene l'azzeramento delle spese in fase di aggiornamento
                    #dei dati di testata
                    if self.DocLoad(idreg):
                        self.SetRegStatus(STATUS_DISPLAY)
                    def reset():
                        self.loadingdoc = False
                    wx.CallAfter(reset)
                    out = True
        return out

    def AcqDoc(self):
        doc = self.dbdoc
        ana = self.dbanag
        docs = doc.cfgdoc.AcquisDocs()
        dlgsel = dma.SelDocDialog(self, doc.id_pdc, doc.id_dest, docs)
        dlgsel.CenterOnScreen()
        acqdocid = dlgsel.ShowModal()
        dlgsel.Destroy()
        if acqdocid < 0: return
        modoacq = dlgsel.modoacq
        annacq = dlgsel.annacq
        dlgacq = dma.AcqDocDialog(self, acqdocid, modoacq, annacq)
        dlgacq.CenterOnScreen()
        if dlgacq.ShowModal() == 1:
            daq = dlgacq.dbacq.doc
            if doc.mov.IsEmpty():
                daq = dbm.DocMag()
                daq.Get(acqdocid)
                headfields = []
                for field, desc in (('id_modpag',  'Mod.Pagamento'),
                                    ('id_bancf',   'Banca'),
                                    ('id_speinc',  'Spese incasso'),
                                    ('id_aliqiva', 'Aliquota IVA'),
                                    ('id_agente',  'Agente'),
                                    ('id_zona',    'Zona'),
                                    ('id_tiplist', 'Listino'),
                                    ('sconto1',    'Sconto 1'),
                                    ('sconto2',    'Sconto 2'),
                                    ('sconto3',    'Sconto 3'),
                                    ('sconto4',    'Sconto 4'),
                                    ('sconto5',    'Sconto 5'),
                                    ('sconto6',    'Sconto 6'),):
                    v_doc = x_doc = getattr(daq, field)
                    if field == 'id_bancf':
                        v_ana = x_ana = None
                        for b in ana.banche:
                            if b.pref:
                                v_ana = b.id
                                x_ana = '%s %s' % (b.codice, b.descriz)
                                break
                    else:
                        v_ana = x_ana = getattr(ana, field, None)
                    if v_doc != v_ana and (bool(v_doc) or bool(v_ana)):
                        if field.startswith('id_'):
                            x_doc = x_ana = '<nulla>'
                            if hasattr(daq, field[3:]):
                                t = getattr(daq, field[3:])
                                if t.id:
                                    x_doc = '%s %s' % (t.codice, t.descriz)
                            if hasattr(ana, field[3:]):
                                t = getattr(ana, field[3:])
                                if t.id:
                                    x_ana = '%s %s' % (t.codice, t.descriz)
                        headfields.append([field,
                                           desc,
                                           {'doc': {'value': v_doc, 'display': x_doc},
                                            'ana': {'value': v_ana, 'display': x_ana},}])
                if headfields:
                    tit = "Copia dati di testata"
                    msg = "Ci sono alcune differenze tra le informazioni di testata e quelle dell'anagrafica:\n"
                    for v_col, v_des, v_dict in headfields:
                        v_doc = v_dict['doc']
                        v_ana = v_dict['ana']
                        msg += ('%s: su documento = %s, su anagrafica = %s\n' % (v_des, v_doc['display'], v_ana['display']))
                    msg += "\nVuoi considerare i valori specifici del documento aquisito?"
                    if aw.awu.MsgDialog(self, msg, tit, style=wx.ICON_QUESTION|wx.YES_NO|wx.CANCEL|wx.YES_DEFAULT) == wx.ID_YES:
                        for v_col, v_des, v_dict in headfields:
                            v_doc = v_dict['doc']
                            v_ana = v_dict['ana']
                            c = self.FindWindowByName(v_col)
                            c.SetValue(v_doc['value'])
            if doc.cfgdoc.tipmov.Locate(lambda x: x.askvalori == "D"):
                movdesid = doc.cfgdoc.tipmov.id
            else:
                movdesid = None
            mov = self.dbdoc.mov
            mov.MoveLast()
            riga = (mov.numriga or 0)+1
            if movdesid is not None:
                mov.CreateNewRow()
                mov.id_tipmov = movdesid
                acq = dlgacq.dbacq
                mov.descriz = """Rif.to %s n. %s del %s"""\
                   % (acq.doc.tipdoc.descriz, acq.doc.numdoc,\
                      lib.dtoc(acq.doc.datdoc))
                mov.numriga = riga
                riga += 1
            for acq in dlgacq.dbacq:
                if acq.acquis:
                    if doc.cfgdoc.tipmov.Locate(lambda x:\
                                                x.codice == acq.tipmov.codice):
                        mov.CreateNewRow()
                        for field in mov.GetFieldNames():
                            if field == 'id':
                                pass
                            else:
                                mov.__setattr__(field, acq.__getattr__(field))
                        mov.numriga = riga
                        mov.id_tipmov = doc.cfgdoc.tipmov.id
                        mov.id_moveva = acq.id
                        mov.qta =     acq.qtaacq
                        mov.importo = acq.impacq
                        mov.sconto1 = acq.sconto1
                        mov.sconto2 = acq.sconto2
                        mov.sconto3 = acq.sconto3
                        mov.sconto4 = acq.sconto4
                        mov.sconto5 = acq.sconto5
                        mov.sconto6 = acq.sconto6
                        mov.f_ann = 0
                        riga += 1
                if acq.annacq:
                    #segno x l'annullamento, in fase di scrittura, del movimento
                    #acquisito e contrassegnato x l'annullamento
                    if not acq.doc.id in doc._info.acqmovann:
                        doc._info.acqmovann[acq.doc.id] = []
                    doc._info.acqmovann[acq.doc.id].append(acq.id)
            if annacq and not acqdocid in doc._info.acqdocann:
                #segno x l'annullamento, in fase di scrittura, del documento
                #acquisito nel caso il tipo di acquisizione lo preveda
                #ed al documento evaso non rimane altro da evadere
                a = True
                for mov in acq:
                    if mov.annacq != 1:
                        if mov.tipmov.askvalori in 'QT':
                            if (mov.qtaacq or 0) < max(0, mov.qta-(mov.total_qtaeva or 0)):
                                a = False
                                break
                if a:
                    doc._info.acqdocann.append(acqdocid)
            if modoacq == "A" and not acqdocid in doc._info.acqdocacq:
                #segno x contrassegnare, in fase di scrittura, il documento
                #acquisito come 'acquisito'
                doc._info.acqdocacq.append(acqdocid)
            if self.lastmovid is None:
                doc.mov.MoveLast()
                self.lastmovid = doc.mov.id_tipmov
        dlgacq.Destroy()
        self.MakeTotals()


# ------------------------------------------------------------------------------


class GridSearchDoc(dbglib.DbGridColoriAlternati):
    """
    Griglia ricerca documenti
    """
    def __init__(self, parent, **kwargs):
        """
        Passare il parent della griglia (tipicamente wx.Panel)
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=parent.GetClientSizeTuple())
        
        self.dbdocs = self.MakeDbDocs()
        
        cols = self.MakeColumns()
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData([], colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.clrer = 'gold indianred'.split()
        self.colnum = self.dbdocs._GetFieldIndex('numdoc')
        self.SetCellDynAttr(self.GetAttr)
        self.SetSearchColors()
        
#        self.SetFitColumn(-1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def MakeDbDocs(self):
#        dbdocs = dbm.DocMag()
        dbdocs = dbm.ElencoDocum()
        dbdocs.config = dbdocs.tipdoc
        if bt.MAGNOCODEDES:
            destfield = 'IF(doc.enable_nocodedes=1 AND doc.nocodedes_descriz IS NOT NULL AND doc.nocodedes_descriz<>"", CONCAT(doc.nocodedes_descriz, " ", doc.nocodedes_indirizzo, " ", doc.nocodedes_cap, " ", doc.nocodedes_citta, " ", doc.nocodedes_prov), "")'
        else:
            destfield = 'dest.descriz'
        dbdocs.AddField(destfield, '_destdesc')
        dbdocs.Reset()
        dbdocs._info.displayonly = True
        dbdocs.ShowDialog(self)
        dbdocs.ClearOrders()
        dbdocs.AddOrder('datreg')
        dbdocs.AddOrder('datdoc')
        dbdocs.AddOrder('numdoc')
        return dbdocs
    
    def MakeColumns(self):
        
        doc = self.dbdocs
        mag = doc.magazz
        pdc = doc.pdc
        des = doc.dest
        self.colors = True
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()
        
        descanag = doc.config.descanag or "Anagrafica"
        
        cols = []
        a = cols.append
        a([ 30, (cn(mag, 'codice'),     "Mag.",          _STR, True)])
        a([ 80, (cn(doc, 'datreg'),     "Data reg.",     _DAT, True)])
        a([ 50, (cn(doc, 'numdoc'),     "N.Doc.",        _NUM, True)])
        a([ 80, (cn(doc, 'datdoc'),     "Data doc.",     _DAT, True)])
        a([ 60, (cn(doc, 'numrif'),     "N.Rif.",        _STR, True)])
        a([ 50, (cn(pdc, 'codice'),     "Cod.",          _STR, True)])
        a([300, (cn(pdc, 'descriz'),     descanag,       _STR, True)])
        a([100, (cn(doc, 'totimporto'), "Tot.Documento", _IMP, True)])
        a([ 35, (cn(doc, 'f_printed'),  "St.",           _CHK, True)])
        a([ 35, (cn(doc, 'f_emailed'),  "Em.",           _CHK, True)])
        a([ 35, (cn(doc, 'f_ann'),      "Ann",           _CHK, True)])
        a([ 35, (cn(doc, 'f_acq'),      "Acq",           _CHK, True)])
        a([ 50, (cn(des, 'codice'),     "Cod.",          _STR, True)])
        a([300, (cn(doc, '_destdesc'),  "Destinazione",  _STR, True)])
        a([  1, (cn(doc, 'id'),         "doc#",          _STR, True)])
        a([  1, (cn(doc, 'id_reg'),     "reg#",          _STR, True)])
        
        self.SetAnchorColumns(7, 6)
        
        return cols
    
    def EnableColors(self, ec):
        self.colors = ec
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        ok = True
        if self.colors and 0 < row < self.dbdocs.RowsCount():
            rs = self.dbdocs.GetRecordset()
            cnum = self.colnum
            if rs[row][cnum] < rs[row-1][cnum]:
                fgcol, bgcol = self.clrer
                attr.SetTextColour(fgcol)
                attr.SetBackgroundColour(bgcol)
            attr.SetReadOnly(True)
        return attr
    
    def UpdateGrid(self, td, dr1, dr2, dd1, dd2, mag, pdc, acq, ann):
        """
        Aggiorna i dati della griglia di ricerca.
        Passare:
        id tipo doc. (obbligatorio)
        valore data reg. minima
        valore data reg. massima
        valore data doc. minima
        valore data doc. massima
        id magazzino
        id anagrafica
        """
        docs = self.dbdocs
        docs.ClearFilters()
        docs.AddFilter("doc.id_tipdoc=%s", td)
        if mag: docs.AddFilter("doc.id_magazz=%s", mag)
        if pdc: docs.AddFilter("doc.id_pdc=%s", pdc)
        if dr1: docs.AddFilter("doc.datreg>=%s", dr1)
        if dr2: docs.AddFilter("doc.datreg<=%s", dr2)
        if dd1: docs.AddFilter("doc.datdoc>=%s", dd1)
        if dd2: docs.AddFilter("doc.datdoc<=%s", dd2)
        if not acq: docs.AddFilter("doc.f_acq IS NULL OR doc.f_acq<>1")
        if not ann: docs.AddFilter("doc.f_ann IS NULL OR doc.f_ann<>1")
        docs.Retrieve()
        self.ChangeData(docs.GetRecordset())


# ------------------------------------------------------------------------------


class DocSearch(wx.Dialog):
    """
    Ricerca registrazioni.
    Dialog per la ricerca di registrazioni della causale selezionata.
    """
    db_curs = None
    _idreg = None
    _ctrlist = None
    
    def __init__(self, parent, tdocid, tdocdes, tipnum):
        wx.Dialog.__init__(self, parent,\
                           title="Ricerca documenti di tipo: %s" % tdocdes,\
                           style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.tdocid = tdocid
        self.tdocdes = tdocdes
        
        wdr.DocSearchFunc(self)
        pangrid = self.FindWindowById(wdr.ID_SRCDOCPANGRID)
        self.gridsrc = GridSearchDoc(pangrid)
        self.gridsrc.EnableColors((tipnum or '') in '23')
        
        for name, val in (('srcdatreg1', datregsrc1),
                          ('srcdatreg2', datregsrc2),
                          ('srcdatdoc1', datdocsrc1),
                          ('srcdatdoc2', datdocsrc2),
                          ('id_magazz',  pdcsearch),
                          ('id_pdc',     magsearch),
                          ('acqsearch',  acqsearch),
                          ('annsearch',  annsearch),
                          ('ricordasel', ricsearch),):
            c = self.FindWindowByName(name)
            c.SetValue(val)
            
        self.CenterOnScreen()
        
        self.UpdateSearch()
        
        self.gridsrc.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDocSelected)
        self.gridsrc.Bind(wx.EVT_KEY_DOWN, self.OnGridKeyDown)
        self.Bind(wx.EVT_BUTTON, self.OnUpdateSearch, id=wdr.ID_SRCBUTSRC)
        self.Bind(wx.EVT_BUTTON, self.OnDocSelected, id=wdr.ID_SRCBUTSEL)
        
        for c in aw.awu.GetAllChildrens(self):
            if isinstance(c, (wx.TextCtrl, DateCtrl, LinkTable)):
                c.Bind(wx.EVT_SET_FOCUS, self.OnFocusGainedBySearchControls)
        self.gridsrc.Bind(wx.EVT_SET_FOCUS, self.OnFocusGainedByGrid)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def OnFocusGainedBySearchControls(self, event):
        self.FindWindowById(wdr.ID_SRCBUTSRC).SetDefault()
        event.Skip()
    
    def OnFocusGainedByGrid(self, event):
        self.FindWindowById(wdr.ID_SRCBUTSEL).SetDefault()
        event.Skip()
    
    def OnGridKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.DocSelected()
        event.Skip()
    
    def OnUpdateSearch(self, event):
        self.UpdateSearch()
        event.Skip()
    
    def UpdateSearch(self):
        dr1, dr2, dd1, dd2, magid, pdcid, acq, ann =\
            map(lambda x: self.FindWindowByName(x).GetValue(),
                'srcdatreg1 srcdatreg2 srcdatdoc1 srcdatdoc2 id_magazz id_pdc acqsearch annsearch'.split())
        
        self.gridsrc.UpdateGrid(self.tdocid, dr1, dr2, dd1, dd2, magid, pdcid, acq, ann)
        if self.gridsrc.dbdocs.IsEmpty():
            f = self.FindWindowById(wdr.ID_SRCDATREG1)
        else:
            f = self.gridsrc
        def SetFocus():
            f.SetFocus()
        wx.CallAfter(SetFocus)

    def OnDocSelected(self, event):
        self.DocSelected()
    
    def DocSelected(self):
        docid = -1
        try:
            sr = self.gridsrc.GetSelectedRows()[-1]
            self.gridsrc.dbdocs.MoveRow(sr)
            docid = self.gridsrc.dbdocs.id
        except:
            pass
        
        global ricsearch; ricsearch = self.FindWindowByName('ricordasel').IsChecked()
        if ricsearch:
            dr1, dr2, dd1, dd2, magid, pdcid, acq, ann =\
                map(lambda x: self.FindWindowByName(x).GetValue(),
                    'srcdatreg1 srcdatreg2 srcdatdoc1 srcdatdoc2 id_magazz id_pdc acqsearch annsearch'.split())
            global datregsrc1; datregsrc1 = dr1
            global datregsrc2; datregsrc2 = dr2
            global datdocsrc1; datdocsrc1 = dd1
            global datdocsrc2; datdocsrc2 = dd2
            global pdcsearch;  pdcsearch = pdcid
            global magsearch;  magsearch = magid
            global acqsearch;  acqsearch = acq
            global annsearch;  annsearch = ann
        
        self.EndModal(docid)
    
    def ShowModal(self):
        wx.CallAfter(lambda: self.FindWindowById(wdr.ID_SRCDATREG1).SetFocus())
        return wx.Dialog.ShowModal(self)
    
    def OnClose(self, event):
        self.EndModal(-1)


# ------------------------------------------------------------------------------


class NumDocDialog(aw.Dialog):
    
    def __init__(self, parent, tipdat, tipnum, tipniv, **kwargs):
        kwargs['title'] = 'Attribuzione numero documento'
        kwargs['style'] = wx.DEFAULT_DIALOG_STYLE
        aw.Dialog.__init__(self, parent, **kwargs)
        self.tipdat = tipdat
        self.tipnum = tipnum
        self.tipniv = tipniv
        self.panel = aw.Panel(self)
        wdr.NumDocFunc(self.panel)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        def ci(x):
            return self.FindWindowByName(x)
        ci('datdoc').Enable(tipdat != '3')
        ci('numiva').Enable(tipniv is not None and\
                            len(tipniv)>0 and\
                            tipniv in '012')
        for name, evt in (('numdoc', wx.EVT_TEXT),
                          ('numiva', wx.EVT_TEXT),
                          ('datdoc', EVT_DATECHANGED),
                          ('datreg', EVT_DATECHANGED),):
            self.Bind(evt, self.OnDataChanged, ci(name))
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnDataChanged,\
                  id=wdr.ID_MAGAZZ)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNSAVE)
    
    def OnDataChanged(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        name = event.GetEventObject().GetName()
        value = event.GetEventObject().GetValue()
        p = self.GetParent()
        doc = p.dbdoc
        setattr(doc, name, value)
        if   name == "datreg" and self.tipdat == '3':
            cn('datdoc').SetValue(value)
        elif name == "numdoc" and self.tipnum == '3':
            cn('numiva').SetValue(value)
        if name == 'datreg' and value is not None:
            def cnp(x):
                return self.GetParent().FindWindowByName(x)
            cnp('datreg').SetValue(cn('datreg').GetValue())
            cnp('id_magazz').SetValue(cn('id_magazz').GetValue())
            p.DefNumDoc()
            cn('numdoc').SetValue(doc.numdoc)
            cn('numiva').SetValue(doc.numiva)
        event.Skip()
    
    def OnSave(self, event):
        fields = list('datdoc,numdoc,datreg'.split(','))
        if self.tipniv and self.tipniv in '012':
            fields.append('numiva')
        err = False
        for field in fields:
            val = self.FindWindowByName(field).GetValue()
            if not val:
                aw.awu.MsgDialog(self, message='Definire tutti i valori')
                err = True
        if not err:
            p = self.GetParent()
            for name in 'id_magazz datreg datdoc numdoc numiva'.split():
                p.FindWindowByName(name).SetValue(self.FindWindowByName(name).GetValue())
            err = not p.ValidateDates()
        if not err:
            self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class _FrameDialogMixin(object):
    
    def SetOneDocOnly(self, *args, **kwargs):
        return self.panel.SetOneDocOnly(*args, **kwargs)
    
    def FixTimerProblem(self):
        #fix Timer su wx.2.8.11: se non lo stoppo, l'applicaizone va in crash :-(
        #TODO: verificare quando è stato risolto il problema nella libreria wx
        for name in 'autonotes_doc autonotes_cli'.split():
            c = self.FindWindowByName(name)
            if c:
                c.Stop()
    
    def CanClose(self):
        #richiamata da XFrame in fase di chiusura applicazione
        if self.panel.TestQuit():
            self.FixTimerProblem()
            return True
        return False
