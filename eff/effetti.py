#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         eff/effetti.py
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
import os
import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw
import awc.util as awu

import Env
import eff.dbtables as dbe

from eff import effetti_wdr as wdr

import contab
from contab.pcf import PcfDialog

import report as rpt

import copy
import mx.DateTime as dt

import awc.controls.linktable as lt


FRAME_TITLE = "Effetti"


adb = dbe.adb
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

selcol = None
emecol = None
inscol = None
bapcod = None
bapid =  None
bapcod = None
bapdes = None
bapabi = None
bapcab = None
saldato = None
colscad = None
colimp = None

gbapcod = None


LIST_ESTRAZ = 0
SAVE_SELECT = 1
LIST_SELECT = 2
STAMPA_DIST = 3
GENERA_FILE = 4
CONTABILIZZ = 5


class InfoSsd():

    dbeff           = None
    tipiDistinta    = None

    PhyMsgTpCd      = None  # Tipo Servizio
    MsgId           = None  # Identificativo univoco messaggio
    CreDtTm         = None  # Data e Ora di Creazione
    InitgPty_Nm     = None  # Nome Azienda Creditrice
    InitgPty_Id     = None  # Identificativo Azienda Creditrice (Cod. CUC)

    NbOfTxs         = None  # Numero totale disposizioni
    CtrlSum         = None  # Totale complessivo delle disposizioni presenti nella dustinta
    banem           = None  # Anagrafica banca emittente

    #--------------------------------------------------------------------------
    PmtInfId        = None  # Identificativo Univoco della Sottodistinta
    SeqTp           = None  # Tipo  sequenza di incasso (valori ammessi:
                            # - FRST (prima di una serie di disposizioni)
                            # - RCUR  (l'autorizzazione viene utilizzata per una serie di incassi a scadenze regolari)
                            # - FNAL  (ultima di una serie di disposizioni)
                            # - OOFF (singola non ripetuta).
    ReqdColltnDt    = None  # Data Scadenza
    Cdtr_Nm         = None  # Nome Azienda Creditrice
    CdtrAcct_IBAN   = None  # IBAN Banca Creditrice
    CdtrSchmedId_Nm = None  # Nome Azienda Creditrice
    CdtrSchmedId_Id = None  # Numero univoco creditore


    InstrId         = None  # Numero Progressivo effetto nell'ambito della sottodistinta
    EndToEndId      = None  # Identificativo univoco dell'effetto all'interno della distinta
    InstdAmt        = None  # Importo effetto
    MndtId          = None  # Identificativo Univoco del mandato ??????
    DtOfSgntr       = None  # Data Autorizzazione Rid
    Dbtr_Nm         = None  # Ragione Sociale Cliente
    DbtrAcct_IBAN   = None  # IBAN Cliente
    RmtInf_Ustrd    = None  # Causale Descrittiva effetto
    def __init__(self, idbanem=None, dbeff=None):
        self.dbeff = dbeff
        self.GetDistinte()
        self.GetNbOfTxs()
        self.GetCtrlSum()
        self.GetBanem(idbanem)


        self.PhyMsgTpCd='INC-SDDC-01'
        self.MsgId='%s-%s' % ('DistintaXml', dt.now().strftime('%d%m%y-%H.%m'))
        self.CreDtTm = '%s' % dt.now().isoformat()
        self.InitgPty_Nm = Env.Azienda.descrizione
        self.InitgPty_Id = self.banem.anag.cuc


    def GetDistinte(self):
        self.tipiDistinta={}
        for idx, eff in enumerate(self.dbeff):
            if eff.f_effsele == 1:
                if eff.bap.rcur==1:
                    tipoDistinta='RCUR'
                else:
                    tipoDistinta='FRST'
                key=tipoDistinta+eff.datscad.strftime('%d-%m-%Y')
                if self.tipiDistinta.has_key(key):
                    self.tipiDistinta[key].append({'idx':idx, 'id':eff.id, 'importo':eff.impeff})
                else:
                    self.tipiDistinta[key]=[{'idx':idx, 'id':eff.id, 'importo':eff.impeff}]

    def GetNbOfTxs(self):
        self.NbOfTxs=0
        for k in self.tipiDistinta:
            self.NbOfTxs =self.NbOfTxs + len(self.tipiDistinta[k])

    def GetCtrlSum(self):
        self.CtrlSum=0
        for k in self.tipiDistinta:
            for e in self.tipiDistinta[k]:
                self.CtrlSum = self.CtrlSum + e['importo']

    def GetBanem(self, idbanem):
        self.banem = adb.DbTable(bt.TABNAME_PDC, "pdc", writable=False)
        self.banem.AddJoin(bt.TABNAME_BANCHE, "anag", idLeft="id", idRight="id")
        self.banem.Get(idbanem)

    def SetNewSottodistinta(self, key, nDistinta):
        self.PmtInfId='%s GR%s' % (self.MsgId, nDistinta)
        self.SeqTp   = key[:4]
        self.ReqdColltnDt = '%s-%s-%s' % (key[10:14], key[7:9], key[4:6])
        self.CdtrAcct_IBAN = self.banem.anag.iban

        self.Cdtr_Nm = Env.Azienda.descrizione

        self.CdtrAgt_MmbId = self.banem.anag.abi

        self.CdtrSchmedId_Nm = Env.Azienda.descrizione
        self.CdtrSchmedId_Id = self.banem.anag.creid


    def SetNewEffetto(self, key, nEffetto):

        idxEffetto=self.tipiDistinta[key][nEffetto]['idx']
        self.dbeff.MoveRow(idxEffetto)
        d=self.tipiDistinta[key][nEffetto]

        self.InstrId = str(nEffetto+1)
        self.EndToEndId = '%s.%s' % (self.PmtInfId, nEffetto+1)
        self.InstdAmt =('% 8.2f' % d['importo']).strip()

        self.Dbtr_Nm=self.dbeff.pdc.descriz[:35]
        try:
            self.MndtId= '%s-%s' % (self.dbeff.pdc.codice, self.dbeff.bap.dtini_rid.strftime('%Y-%m-%d'))
        except:
            self.MndtId   = None
        try:
            self.DtOfSgntr= self.dbeff.bap.dtini_rid.strftime('%Y-%m-%d')
        except:
            self.DtOfSgntr= None
        self.DbtrAcct_IBAN = self.dbeff.bap.iban
        self.RmtInf_Ustrd='SALDO NS. %s N.%s DEL %s' % (self.dbeff.caus.descriz, self.dbeff.numdoc, self.dbeff.datdoc.strftime('%d-%m-%y'))


class EffGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia effetti
    """
    def __init__(self, parent, dbeff):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable effetti (eff.dbtables.Eff)
        """

        dbglib.DbGridColoriAlternati.__init__(self, parent, -1,
                                              size=parent.GetClientSizeTuple())

        self.dbeff = dbeff

        eff = self.dbeff
        cau = eff.caus
        pdc = eff.pdc
        pba = eff.pdcban
        ban = pba.ban
        bap = eff.bap

        cn = lambda db, col: db._GetFieldIndex(col, inline=True)

        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()

        #colcodart = pro._GetFieldIndex("codice", inline=True)

        cols = (\
            ( 80, (cn(eff, 'datscad'), "Scadenza",        _DAT, True )),\
            ( 50, (cn(pdc, 'codice'),  "Cod.",            _STR, True )),\
            (250, (cn(pdc, 'descriz'), "Cliente",         _STR, True )),\
            (110, (cn(eff, 'impeff'),  "Importo Effetto", _IMP, True )),\
            (110, (cn(eff, 'saldo'),   "Saldo partita",   _IMP, True )),\
            (100, (cn(cau, 'descriz'), "Causale",         _STR, True )),\
            ( 80, (cn(eff, 'datdoc'),  "Data",            _DAT, True )),\
            ( 60, (cn(eff, 'numdoc'),  "Num.",            _STR, True )),\
            ( 50, (cn(bap, 'codice'),  "Cod.",            _STR, True )),\
            (220, (cn(bap, 'descriz'), "Banca Appoggio",  _STR, True )),\
            ( 60, (cn(bap, 'abi'),     "ABI",             _STR, True )),\
            ( 60, (cn(bap, 'cab'),     "CAB",             _STR, True )),\
            ( 80, (cn(eff, 'effdate'), "Emissione",       _DAT, True )),\
            ( 50, (cn(pba, 'codice'),  "Cod.",            _STR, True )),\
            (220, (cn(pba, 'descriz'), "Banca Emittente", _STR, True )),\
            ( 60, (cn(ban, 'abi'),     "ABI",             _STR, True )),\
            ( 60, (cn(ban, 'cab'),     "CAB",             _STR, True )),\
            (  1, (cn(eff, 'id'),      "#eff",            _STR, True )),\
            )

        global gbapcod; gbapcod = 8

        self._cols = cols

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False

        links = []
        ltbap = dbglib.LinkTabAttr(bt.TABNAME_BANCF, #table
                                   gbapcod,          #grid col
                                   bapid,            #rs col id
                                   bapcod,           #rs col cod
                                   bapdes,           #rs col des
                                   None)             #card class
        links.append(ltbap)

        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE, gbapcod,\
                       self._RefreshBap), )
        self.SetData( self.dbeff._info.rs, colmap, canedit, canins,\
                      links, afteredit)
        self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.colors = { 'datierr': [stdcolor.NORMAL_FOREGROUND,
                                    stdcolor.GetColour('salmon')],
                        'inspag':  [stdcolor.NORMAL_FOREGROUND,
                                    stdcolor.GetColour('plum')],
                        'insatt':  [stdcolor.GetColour('yellow'),
                                    stdcolor.GetColour('red')],
                        'selez':   [stdcolor.EFFSEL_FOREGROUND,
                                    stdcolor.EFFSEL_BACKGROUND],
                        'saldato': [stdcolor.GetColour('black'),
                                    stdcolor.GetColour('yellow')],
                        'normal':  [stdcolor.NORMAL_FOREGROUND,
                                    stdcolor.NORMAL_BACKGROUND] }

        self.SetAnchorColumns(3, 2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        self.Bind(gl.EVT_GRID_CMD_EDITOR_SHOWN, self.OnEditorShown)

    def _RefreshBap(self, row, gridcol, col, value):
        #richiamato da testafteredit, provvede ad aggiornare i dati
        #relativi alla banca d'appoggio: DataLinkCellAttr aggiorna solo
        #l'id della banca nella matrice del recordset
        eff = self.dbeff
        eff.MoveRow(row)
        eff.id_effbap = value
        return True

    def OnEditorShown(self, event):
        if event.GetCol() == gbapcod:
            row = event.GetRow()
            editor = self.GetCellEditor(row, gbapcod)
            do = True
            if editor._tc:
                if editor._tc.IsShown():
                    do = False
            if do:
                eff = self.dbeff
                eff.MoveRow(row)
                editor.lt_filter = "id_pdc=%s" % eff.id_pdc
                lt = editor._tc
                if lt:
                    lt.SetFilter(editor.lt_filter)
        event.Skip()

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        readonly = not rscol in (colscad, bapcod)
        if 0 <= row < self.dbeff.RowsCount():
            roweff = self.dbeff.GetRecordset()[row]
            colors = self.colors
            if not self.DatiOK(row):
                fgcol, bgcol =  colors['datierr']
            elif col<3 and roweff[inscol]:
                if roweff[saldato]:
                    fgcol, bgcol = colors['inspag']
                else:
                    fgcol, bgcol = colors['insatt']
            elif roweff[selcol]:
                fgcol, bgcol = colors['selez']
            elif roweff[saldato]:
                fgcol, bgcol = colors['saldato']
            else:
                fgcol, bgcol = colors['normal']
            attr.SetTextColour(fgcol)
            attr.SetBackgroundColour(bgcol)
        attr.SetReadOnly(readonly)
        return attr

    def DatiOK(self, effrow):
        rse = self.dbeff.GetRecordset()[effrow]
        return (rse[bapid]  or False) and\
               (rse[bapabi] or False) and\
               (rse[bapcab] or False) and\
               (rse[colimp] > 0)


# ------------------------------------------------------------------------------


class EmiEffettiPanel(wx.Panel):
    """
    Pannello gestione Effetti.
    """

    errorMsg   = None
    faseMsg    = None
    effettoMsg = None


    def __init__(self, *args, **kwargs):

        wx.Panel.__init__(self, *args, **kwargs)

        self.dbeff = dbe.Eff()
        self.effsel = []

        global selcol, emecol, inscol, bapid, bapcod, bapdes, bapabi, bapcab
        global saldato, colscad, colimp
        eff = self.dbeff
        gfi = lambda t, f: t._GetFieldIndex(f, inline=True)
        selcol  = gfi(eff, "f_effsele")
        emecol  = gfi(eff, "f_effemes")
        inscol  = gfi(eff, "insoluto")
        saldato = gfi(eff, "saldato")
        colscad = gfi(eff, "datscad")
        colimp =  gfi(eff, "impeff")
        bapid  =  gfi(eff.bap, "id")
        bapcod  = gfi(eff.bap, "codice")
        bapdes  = gfi(eff.bap, "descriz")
        bapabi  = gfi(eff.bap, "abi")
        bapcab  = gfi(eff.bap, "cab")

        wdr.EffettiFunc(self)
        cn = lambda x: self.FindWindowById(x)

        #determino tipi sottoconti per filtro su controlli
        #per pdc clienti,banca,conto effetti
        tipana = adb.DbTable(bt.TABNAME_PDCTIP, "tipana", writable=False)
        tipana.AddOrder("tipana.codice")
        tipi = {}
        for tipo in "CBD":
            tipi[tipo] = [None, []]
            tipana.ClearFilters()
            tipana.AddFilter("tipana.tipo='%s'" % tipo)
            if tipana.Retrieve():
                tipi[tipo][0] = tipana.id
                for t in tipana:
                    tipi[tipo][1].append(t.id)
        del tipana

        #filtro su causale contabile origine riba
        cc = cn(wdr.ID_CAUS)
        cc.SetFilter("pcf=1 AND pcfscon!=1 AND id_pdctippa IN (%s)"\
                     % ",".join(map(str, tipi["C"][1])))

        ##filtro su mod.pag.
        #mp = cn(wdr.ID_MODPAG)
        #mp.SetFilter("tipo='R'")

        #filtro su sottoconti cliente, banca, conto effetti
        for ctrid, tipo in ((wdr.ID_PDC,      "C"),\
                            (wdr.ID_BANCA,    "B"),\
                            (wdr.ID_CONTOEFF, "D")):
            ctr = cn(ctrid)
            #===================================================================
            # ctr.SetFilterLinks(("Tipo di sottoconto",
            #                    bt.TABNAME_PDCTIP,
            #                    "id_tipo",
            #                    None,#PdcTipDialog,
            #                    "tipo='%s'" % tipo,
            #                    tipi[tipo][0]))
            #===================================================================
            ctr.SetFilterValue(tipi[tipo][0])
            ctr.SetFilterFilter("tipo='%s'" % tipo)

        cn(wdr.ID_TIPEFF).SetDataLink(values='RIS')

        cn(wdr.ID_DATDIST).SetValue(Env.Azienda.Esercizio.dataElab)

        self.grideff = EffGrid(cn(wdr.ID_PANGRID), self.dbeff)
        for cid, colorkey in ((wdr.ID_COLORSELEZ,  'selez'),
                              (wdr.ID_COLOREMESSO, 'saldato'),
                              (wdr.ID_COLORERROR,  'datierr'),
                              (wdr.ID_COLORINSATT, 'insatt'),
                              (wdr.ID_COLORINSPAG, 'inspag')):
            cn(cid).SetBackgroundColour(self.grideff.colors[colorkey][1])

        self.AdeguaFiltriByTipEff()

        self.Bind(wx.EVT_RADIOBOX, self.OnTipEffChanged, cn(wdr.ID_TIPEFF))

        for cid, func in ((wdr.ID_BUTSRC,      self.OnUpdate),
                          (wdr.ID_BUTSELEFF,   self.OnSelectYes),
                          (wdr.ID_BUTDESELEFF, self.OnSelectNo),
                          (wdr.ID_BUTSELALL,   self.OnSelectAllYes),
                          (wdr.ID_BUTDESELALL, self.OnSelectAllNo),
                          (wdr.ID_BUTLISTALL,  self.OnListaEstraz),
                          (wdr.ID_BUTLISTSEL,  self.OnListaSelez),
                          (wdr.ID_BUTDIST,     self.OnStampaDist),
                          (wdr.ID_BUTFILE,     self.OnGeneraFile),
                          (wdr.ID_BUTCONT,     self.OnContabilizza),
                          (wdr.ID_BUTSAVESEL,  self.OnSaveSel),
                          ):
            self.Bind(wx.EVT_BUTTON, func, id=cid)

        for cid, func in ((wdr.ID_BANCA,    self.OnBancaChanged),
                          (wdr.ID_CONTOEFF, self.OnContoEffChanged)):
            self.Bind(lt.EVT_LINKTABCHANGED, func, id=cid)

        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
        self.Bind(contab.EVT_PCFCHANGED, self.OnUpdate)


    def GetPanelDataSource(self):
        return self.dbeff

    def OnTipEffChanged(self, event):
        self.AdeguaFiltriByTipEff()
        event.Skip()

    def AdeguaFiltriByTipEff(self):
        def ci(x):
            return self.FindWindowById(x)
        #filtro su mod.pag.
        te = ci(wdr.ID_TIPEFF)
        if te.GetValue() == 'I':
            tipo = 'I'
        elif te.GetValue() == 'S':
            tipo = 'S'
        else:
            tipo = 'R'
        mp = ci(wdr.ID_MODPAG)
        mp.SetFilter("tipo='%s'" % tipo)

        #filtro su conto effetti
        banca, pdcef = map(ci, (wdr.ID_BANCA, wdr.ID_CONTOEFF))
        banid = banca.GetValue()
        te = self.FindWindowById(wdr.ID_TIPEFF).GetValue()
        fte = "(eff.tipo IS NULL OR eff.tipo='%s')" % te
        if banid is None:
            pdcef.SetFilter(fte)
        else:
            e = adb.DbTable(bt.TABNAME_EFFETTI, 'effetti', writable=False)
            if e.Retrieve("id_banca IS NULL OR id_banca=%d" % banid):
                if e.RowsCount()>0:
                    def ResetValues(*args):
                        ci(wdr.ID_FILEPATH).SetValue(None)
                        ci(wdr.ID_CAUCONT).SetValue(None)
                    pdcef.SetFilter('%s AND pdc.id IN (%s)' \
                                    % (fte, ','.join([str(e.id) for e in e])),
                                    resetOnError=True, onError=ResetValues)
            del e

    def OnBancaChanged(self, event):
        self.AdeguaFiltriByTipEff()
        event.Skip()

    def OnContoEffChanged(self, event):
        pdcef, caus, path = map(self.FindWindowById, (wdr.ID_CONTOEFF,
                                                      wdr.ID_CAUCONT,
                                                      wdr.ID_FILEPATH))
        effid = pdcef.GetValue()
        if effid is not None:
            e = adb.DbTable(bt.TABNAME_EFFETTI, 'effetti', writable=False)
            if e.Get(effid):
                caus.SetValue(e.id_caus)
                path.SetValue(e.filepath)
            del e
        event.Skip()

    def OnDblClick(self, event):
        row = event.GetRow()
        if self.grideff.IsOnTotalRow(row):
            return
        pcf = self.dbeff
        pcf.MoveRow(row)
        wx.BeginBusyCursor()
        dlg = PcfDialog(self)
        dlg.SetPcf(pcf.id)
        wx.EndBusyCursor()
        changed = (dlg.ShowModal() == 1)
        dlg.Destroy()
        if changed:
            evt = contab.PcfChangedEvent(contab._evtPCFCHANGED, self.GetId())
            evt.SetEventObject(self)
            evt.SetId(self.GetId())
            self.GetEventHandler().AddPendingEvent(evt)
        event.Skip()

    def OnUpdate(self, event):
        self.UpdateEff()
        event.Skip()

    def UpdateEff(self, msg=True):
        cn = lambda x: self.FindWindowById(x)
        eff = self.dbeff
        eff.ClearFilters()
        te = cn(wdr.ID_TIPEFF).GetValue()
        if te == 'I':
            #rid, filtro su tipologia della mod.pag.
            eff.AddFilter("modpag.tipo='I'")
        else:
            #riba, filtro su flag della partita
            eff.AddFilter("pcf.riba=1")
        for ctrid, filt in ((wdr.ID_CAUS,    r"pcf.id_caus=%s"),\
                            (wdr.ID_MODPAG,  r"pcf.id_modpag=%s"),\
                            (wdr.ID_PDC,     r"pcf.id_pdc=%s"),\
                            (wdr.ID_DATSCA1, r"pcf.datscad>=%s"),\
                            (wdr.ID_DATSCA2, r"pcf.datscad<=%s"),\
                            (wdr.ID_DATDOC1, r"pcf.datdoc>=%s"),\
                            (wdr.ID_DATDOC2, r"pcf.datdoc<=%s"),\
                            (wdr.ID_NUMDOC1, r"pcf.numdoc>=%s"),\
                            (wdr.ID_NUMDOC2, r"pcf.numdoc<=%s")):
            ctr = cn(ctrid)
            val = ctr.GetValue()
            if val:
                eff.AddFilter(filt, val)
        if not cn(wdr.ID_INCLEMES).GetValue():
            eff.AddFilter("pcf.f_effemes IS NULL OR pcf.f_effemes=0")
            eff.AddFilter("pcf.imptot<>pcf.imppar")
        if not cn(wdr.ID_INCLCONT).GetValue():
            eff.AddFilter("pcf.f_effcont IS NULL OR pcf.f_effcont=0")
        if not cn(wdr.ID_INCLINSOL).GetValue():
            eff.AddFilter("pcf.insoluto IS NULL OR pcf.insoluto=0")
        if not cn(wdr.ID_INCLCHIUS).GetValue():
            eff.AddFilter("pcf.imptot<>pcf.imppar")
        if eff.Retrieve():
            self.grideff.ResetView()
            if eff.RowsCount() == 0 and msg:
                awu.MsgDialog(self, "Nessun effetto trovato")
        else:
            awu.MsgDialog(self, repr(eff.GetError()))
        del self.effsel[:]
        rse = eff.GetRecordset()
        self.effsel += [row for row in range(eff.RowsCount())\
                        if rse[row][selcol]]
        cn(wdr.ID_NUMEFF).SetValue(eff.RowsCount())
        col = eff._GetFieldIndex('impeff', inline=True)
        cn(wdr.ID_TOTEFF).SetValue(sum([e[col] for e in eff.GetRecordset()]))
        self.UpdateTot()

    def OnSelectYes(self, event):
        sr = self.grideff.GetSelectedRows()
        self.SelectEff(sr, True)
        event.Skip()

    def OnSelectNo(self, event):
        sr = self.grideff.GetSelectedRows()
        self.SelectEff(sr, False)
        event.Skip()

    def OnSelectAllYes(self, event):
        sr = range(self.dbeff.RowsCount())
        self.SelectEff(sr, True)
        event.Skip()

    def OnSelectAllNo(self, event):
        sr = range(self.dbeff.RowsCount())
        self.SelectEff(sr, False)
        event.Skip()

    def SelectEff(self, rows, dosel):
        eff = self.dbeff
        for row in rows:
            sel = dosel and self.grideff.DatiOK(row)
            eff.MoveRow(row)
            if sel: eff.f_effsele = 1
            else:   eff.f_effsele = 0
            if sel:
                if not row in self.effsel:
                    self.effsel.append(row)
            else:
                if row in self.effsel:
                    n = self.effsel.index(row)
                    self.effsel.pop(n)
        self.UpdateTot()
        self.grideff.Refresh()

    def UpdateTot(self):
        eff = self.dbeff
        cn = lambda x: self.FindWindowById(x)
        colimp = eff._GetFieldIndex("impeff", inline=True)
        cn(wdr.ID_NUMSEL).SetValue(len(self.effsel))
        tot = 0
        rse = eff.GetRecordset()
        for row in self.effsel:
            tot += rse[row][colimp]
        cn(wdr.ID_TOTSEL).SetValue(tot)

    def OnSaveSel(self, event):
        self.SaveSel()
        event.Skip()

    def SaveSel(self):
        """
        Salva le selezioni
        """
        out = self.dbeff.Save()
        if not out:
            awu.MsgDialog(self, repr(self.dbeff.GetError()))
        return out

    def OnListaEstraz(self, event):
        self.ListaEstraz()
        event.Skip()

    def ListaEstraz(self):
        """
        Lista effetti estratti
        """
        eff = self.dbeff
        if eff.RowsCount() == 0:
            awu.MsgDialog(self, "Nessun effetto trovato")
            return
        te = self.FindWindowById(wdr.ID_TIPEFF).GetValue()
        if te == 'R':
            tipo = 'Ri.Ba.'
        elif te == 'I':
            tipo = 'RID'
        else:
            tipo = 'Effetti'
        eff._info.titleprint = 'Lista %s presenti' % tipo
        rpt.Report(self, eff, 'Effetti')

    def OnListaSelez(self, event):
        self.ListaSelez()
        event.Skip()

    def ListaSelez(self):
        """
        Lista effetti selezionati
        """
        eff = self.dbeff
        if eff.GetCountOf(lambda rse: rse[selcol] or False) == 0:
            awu.MsgDialog(self, "Nessun effetto selezionato")
            return
        te = self.FindWindowById(wdr.ID_TIPEFF).GetValue()
        if te == 'R':
            tipo = 'Ri.Ba.'
        elif te == 'I':
            tipo = 'RID'
        else:
            tipo = 'Effetti'
        eff._info.titleprint = 'Lista %s selezionati' % tipo
        rpt.Report(self, eff, 'Effetti',
                   rowFilter=lambda e: e.f_effsele == 1)

    def OnStampaDist(self, event):
        self.StampaDist()
        event.Skip()

    def StampaDist(self):
        eff = self.dbeff
        if not eff.Locate(lambda x: x.f_effsele == 1):
            awu.MsgDialog(self, "Nessun effetto selezionato")
            return
        datdist, banca = self.GetValori(wdr.ID_DATDIST, wdr.ID_BANCA)
        if datdist is not None and banca is not None:
            ci = lambda x: self.FindWindowById(x)
            te = ci(wdr.ID_TIPEFF).GetValue()
            if te == 'R':
                tipo = 'RIBA'
            else:
                tipo = 'RID'
            name = "Distinta emissione %s" % tipo
            eff._info.datdist = ci(wdr.ID_DATDIST).GetValue()
            eff._info.pdcbanem.Get(ci(wdr.ID_BANCA).GetValue())
            rpt.Report(self, eff, name, rowFilter=lambda e: e.f_effsele == 1)
            self.SaveEff()

    def OnGeneraFile(self, event):
        self.GeneraFile()
        event.Skip()

    def GeneraFile(self):
        """
        Generazione file
        """
        if self.dbeff.GetCountOf(lambda rse: rse[selcol] or False) == 0:
            awu.MsgDialog(self, "Nessun effetto selezionato")
            return
        datdist, idbanem, idpdcef, filepath = self.GetValori(wdr.ID_DATDIST,
                                                             wdr.ID_BANCA,
                                                             wdr.ID_CONTOEFF,
                                                             wdr.ID_FILEPATH)
        if datdist is None or idbanem is None or filepath is None:
            return
        te = self.FindWindowById(wdr.ID_TIPEFF).GetValue()
        if te == 'I':
            self.GeneraFileRibaRid(datdist, idbanem, idpdcef, filepath )
        elif te== 'R':
            self.GeneraFileRibaRid(datdist, idbanem, idpdcef, filepath )
        elif te== 'S':
            self.GeneraFileRibaRid(datdist, idbanem, idpdcef, filepath )

    def Output(self, row):
        lSuccess=True
        info=self.infoSsd
        try:
            self.output.write('%s\n' % eval(row))
        except:
            lSuccess=False
            self.errorMsg=row
        return lSuccess

    def WriteMainHeader(self):
        lOk=True
        for r in self.tr['H']:
            lOk=self.Output(r)
            if not lOk:
                break
        return lOk

    def WriteMainFooter(self):
        for r in self.tr['F']:
            lOk=self.Output(r)
            if not lOk:
                break
        return lOk

    def WriteDistintaHeader(self, k, nDistinta):
        """
        k         key del dizionario self.infoSsd.tipiDistinta contenente l'elenco degli effetti
                  facenti capo ad una stessa sottodistinta
        nDistinta numero progressivo della sottodistinta
        """
        # k key del dizionario che contiene l'indicazione degli effetti compresi nellas sottodistinta
        lOk=True
        self.infoSsd.SetNewSottodistinta(k, nDistinta+1)
        for r in self.tr['H1']:
            lOk=self.Output(r)
            if not lOk:
                break
        return lOk

    def WriteDistintaBody(self, k, idbanem, idpdcef, datdist):
        """
        k         key del dizionario self.infoSsd.tipiDistinta contenente l'elenco degli effetti
                  facenti capo ad una stessa sottodistinta
        idbanem   id dela banca emittente
        idpdceff  id sottoconto effetti da utilizzare
        datdist   data emissione effetti
        """
        lOk=True
        for nEffetto, effetto in enumerate(self.infoSsd.tipiDistinta[k]):
            ### ciclo su tutti gli effetti delle stessa sottodistinta
            idxEffetto=effetto['idx']
            self.dbeff.MoveRow(idxEffetto)
            self.numeff = self.numeff + 1
            self.infoSsd.SetNewEffetto(k, nEffetto)
            for r in self.tr['B1']:
                ### scrivo il corpo del singolo effetto
                lOk=self.Output(r)
                if not lOk:
                    rs=self.dbeff.pdc.descriz
                    nd=self.dbeff.numdoc
                    dd=self.dbeff.datdoc.strftime('%d%m%y')
                    eu=('% 8.2f' % self.dbeff.impeff).strip()
                    self.effettoMsg='\n\nEffetto n.%s\na %s\ndoc. n.%s del %s\nEuro %s' % (nEffetto+1, rs, nd, dd, eu)
                    break
            if lOk:
                self.dbeff.effnum = self.numeff
                self.dbeff.id_effban = idbanem
                self.dbeff.id_effpdc = idpdcef
                self.dbeff.effdate   = datdist
                self.dbeff.f_effemes = 1
                #self.dbeff.bap.rcur  = 1
            else:
                break
        return lOk

    def WriteDistintaFooter(self, k):
        """
        k         key del dizionario self.infoSsd.tipiDistinta contenente l'elenco degli effetti
                  facenti capo ad una stessa sottodistinta
        """
        for r in self.tr['F1']:
            lOk=self.Output(r)
            if not lOk:
                break
        return lOk


    def GetFilename(self, filepath, preFix, msg, wd):
        def fmt(x,l=2):
            return str(x).zfill(l)

        filename = preFix
        now = Env.DateTime.now()
        filename = '%s %s-%s-%s %s-%s' % (filename,
                                          fmt(now.year, 4),
                                          fmt(now.month),
                                          fmt(now.day),
                                          fmt(now.hour),
                                          fmt(now.minute))
        dlg = wx.FileDialog(\
            None,\
            message = msg,\
            defaultDir = filepath,\
            defaultFile = filename,\
            wildcard = wd,\
            style=wx.SAVE)
        filename = None
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()
        return filename
    
    
    def GeneraFileRibaRid(self, datdist, idbanem, idpdcef, filepath):
        """
        Generazione file x RI.BA. o RID Arricchito
        """
        te = self.FindWindowById(wdr.ID_TIPEFF).GetValue()
        if te == 'I':
            tipo = 'I'
            _prefix = "RID"
            _msg="selezione file rid da generare"
            _wd ="File esportazione effetti (*.TXT)|*.TXT"
            
        elif te == 'R':
            tipo = 'R'
            _prefix = "RIBA"
            _msg="selezione file riba da generare"
            _wd="File esportazione effetti (*.TXT)|*.TXT"
        elif te == 'S':
            tipo = 'S'
            _prefix = "SDD"
            _msg="selezione file sdd da generare"
            _wd="File esportazione effetti (*.XML)|*.XML"
        try:
            tr = dbe.GetEffConfig(tipo, idbanem)
            self.tr = tr
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args))
            return
        banem = adb.DbTable(bt.TABNAME_PDC, "pdc", writable=False)
        banem.AddJoin(bt.TABNAME_BANCHE, "anag", idLeft="id", idRight="id")
        if not banem.Get(idbanem):
            awu.MsgDialog(self, "Banca emittente non trovata")
            return
        effauto = adb.DbTable(bt.TABNAME_CFGPROGR, "progr")
        effauto.AddFilter("progr.codice='EFF_LASTEFF'")
        effauto.AddFilter("progr.keydiff=%s", datdist.year)
        numeff = 0
        if effauto.Retrieve():
            numeff = effauto.progrnum or 0
        self.numeff = numeff
        #selezione file da generare
        filename = self.GetFilename(filepath, _prefix, _msg, _wd)
        if filename is None:
            return
        #generazione file
        def rbdate(d):
            if d:
                out = "%s%s%s" % (str(d.day).zfill(2),\
                                  str(d.month).zfill(2),\
                                  str(d.year)[-2:])
            else:
                out = '000000'
            return out
#        s = lambda x,n: (x or "").ljust(n)
        def s(x, n):
            return ((x or '').encode('ascii', 'ignore')+' '*n)[:n]
        z = lambda x,n: str(x or 0).zfill(n)
        def pivacf(piva,cf):
            if not piva:
                out = cf or ""
            else:
                out = piva or ""
            return out.ljust(16)
        def addrcli(eff):
            cli = eff.pdc.anag
            if not cli.spdind:
                out = s(cli.indirizzo,30)+s(cli.cap,5)+s(cli.citta,20)
            else:
                out = s(cli.spdind,30)+s(cli.spdcap,5)+s(cli.spdcit,20)
            return out
        def addrcli2(eff):
            cli = eff.pdc.anag
            if not cli.spdind:
                out = s(cli.indirizzo,30)+s(cli.cap,5)+s(cli.citta,22)+' '+s(cli.prov or '', 2)
            else:
                out = s(cli.spdind,30)+s(cli.spdcap,5)+s(cli.spdcit,22)+' '+s(cli.spdpro or '', 2)
            return out
        def rifdoc(eff):
            return eff.rifdoc()

        eff = self.dbeff
        keydisk = '0'*8 + dt.now().Format().split()[1].replace(':','.')
        keydisk = keydisk[-8:]
        eff._info.keydisk = keydisk
        try:
            ErrMsg = lambda zona, riga, err:\
                   awu.MsgDialog(self,\
                                 """Errore nella configurazione del """\
                                 """file effetti (%s/%d):\n%s"""\
                                 % (zona, riga, repr(err.args)))
            f = file(filename, 'w')
            fok = True
            numriga = 0
            efftotnum = 0
            efftotimp = 0
            if tipo in ['R', 'I']:
                # generazione file per RIBA e RID
                for n,m in enumerate(tr["H"]):
                    try:
                        r = eval(m)
                    except Exception, err:
                        ErrMsg("H", n, err)
                        fok = False
                        break
                    f.write("%s\n" % r)
                if fok:
                    for eff in self.dbeff:
                        if eff.f_effsele == 1:
                            #scrittura corpo
                            efftotnum += 1
                            efftotimp += eff.impeff
                            numeff += 1
                            numriga += 1
                            for n,m in enumerate(tr["B"]):
                                try:
                                    r = eval(m)
                                except Exception, err:
                                    ErrMsg("B", n, err)
                                    fok = False
                                    break
                                f.write("%s\n" % r)
                            if not fok: break
                            eff.effnum = numeff
                            eff.id_effban = idbanem
                            eff.id_effpdc = idpdcef
                            eff.effdate = datdist
                            eff.f_effemes = 1
                if fok:
                    #scrittura piede
                    for n,m in enumerate(tr["F"]):
                        try:
                            r = eval(m)
                        except Exception, err:
                            ErrMsg("F", n, err)
                            fok = False
                            break
                        f.write("%s\n" % r)
            elif tipo=='S':
                # generazione file per SDD
                self.infoSsd=InfoSsd(idbanem, self.dbeff)
                self.faseMsg="Composizione Testata Distinta"
                self.output = f
                fok=True
                if self.WriteMainHeader():
                    fok=True
                    for i, k in enumerate(self.infoSsd.tipiDistinta.keys()):
                        fok=False
                        self.faseMsg="Composizione Testata SottoDistinta %s" % (i+1)
                        if self.WriteDistintaHeader(k, i):
                            self.faseMsg="Composizione Corpo di SottoDistinta %s" % (i+1)
                            if self.WriteDistintaBody(k, idbanem, idpdcef, datdist):
                                self.faseMsg="Composizione Piede di SottoDistinta %s" % (i+1)
                                if self.WriteDistintaFooter(k):
                                    fok=True
                        if not fok:
                            break
                    if fok:
                        self.faseMsg="Composizione Piede Distinta"
                        fok=self.WriteMainFooter()
                else:
                    fok=False                
                
                if not fok:
                    if not self.errorMsg==None:
                        msg="Errore in valutazione della direttiva\n%s\nDurante la fase %s" % (self.errorMsg, self.faseMsg)
                        if not self.effettoMsg==None:
                            msg = '%s\n%s' % (msg, self.effettoMsg)
                    else:
                        msg="Errore in generazione flusso durante la fase\n%s" % self.faseMsg
                    awu.MsgDialog(self, msg, style = wx.ICON_WARNING)
            if fok:
                if self.SaveEff():
                    if effauto.RowsCount() == 0:
                        effauto.CreateNewRow()
                        effauto.codice = "eff_lasteff"
                        effauto.descriz = "Ultimo effetto emesso"
                        effauto.keydiff = datdist.year
                    effauto.progrnum = numeff
                    effauto.progrdate = datdist
                    effauto.Save()
                awu.MsgDialog(self, "File effetti generato correttamente",\
                              style = wx.ICON_INFORMATION)
            else:
                awu.MsgDialog(self, "File effetti non generato",\
                              style = wx.ICON_WARNING)
            f.close()
        except IOError, err:
            awu.MsgDialog(self, "Problema durante la generazione del file:\n%s"\
                          % repr(err.args))

    def OnContabilizza(self, event):
        nsel = self.dbeff.GetCountOf(lambda rse: rse[selcol] or False)
        if nsel>0:
            self.Contabilizza()
        else:
            awu.MsgDialog(self, "Nessun effetto selezionato")
        event.Skip()

    def Contabilizza(self):
        datdist, idbanem, idcontoeff, idcaucont =\
               self.GetValori(wdr.ID_DATDIST, wdr.ID_BANCA,\
                              wdr.ID_CONTOEFF, wdr.ID_CAUCONT)
        if datdist is None or\
           idbanem is None or\
           idcontoeff is None or\
           idcaucont is None:
            return

        if awu.MsgDialog(self, message="Confermi la contabilizzazione degli effetti selezionati?",
                         style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
            return

        noem = False
        s0 = False
        for eff in self.dbeff:
            if eff.f_effsele == 1:
                if eff.f_effemes != 1:
                    noem = True
                if eff.saldo<=0:
                    s0 = True

        if noem:
            msg =\
                """ATTENZIONE\n\nGli effetti selezionati non sono stati emessi, confermi comunque la loro contabilizzazione?\n"""\
                """Procedendo, essi verranno contabilizzati ma non sarà possibile produrre il file da trasmettere alla banca,\n"""\
                """se non con una successiva operazione di estrazione e filtro.\n\n"""\
                """Confermi la contabilizzazione senza emissione?"""
            if awu.MsgDialog(self, message=msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return

        if s0:
            msg =\
                """ATTENZIONE\n\nCi sono partite con saldo a zero o negativo, la loro contabilizzazione porterà\n"""\
                """ad un saldo negativo pari all'importo del relativo effetto.\n\n"""\
                """Si consiglia di contabilizzare solo effetti relativi a partite con saldo utile all'emissione,\n"""\
                """ovvero togliendo dalle selezioni il flag relativo alle partite saldate e rieffettuando l'estrazione.\n"""\
                """Confermi la contabilizzazione in queste condizioni?"""
            if awu.MsgDialog(self, message=msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return

        wait = awu.WaitDialog(self,\
                              message="Contabilizzazione effetti in corso",\
                              maximum=self.dbeff.RowsCount())

        #oggetto usato per aggiornare su dbeff le colonne imptot/imppar
        #dopo la scittura della registrazione
        pcf = adb.DbTable(bt.TABNAME_PCF, "pcf")



        te = self.FindWindowById(wdr.ID_TIPEFF).GetValue()

        #contabilizzazione
        cok = True
        reg = dbe.dbc.DbRegCon()
        for eff in self.dbeff:
            if eff.f_effsele == 1:
                #testata
                reg.Reset()
                reg.CreateNewRow()
                reg.esercizio = datdist.year
                reg.id_caus = idcaucont
                reg.tipreg = reg.config.tipo
                reg.datreg = datdist
                #dettaglio: riga1=cliente, riga2=conto effetti
                body = reg.body
                for riga, cpa, ccp, segno in\
                    ((1, eff.id_pdc, idcontoeff, reg.config.pasegno),\
                     (2, idcontoeff, eff.id_pdc, reg.GetSegnoCP()  )):
                    body.CreateNewRow()
                    body.numriga =  riga
                    body.tipriga =  reg.tipreg
                    body.importo =  eff.impeff
                    body.segno =    segno
                    body.id_pdcpa = cpa
                    body.id_pdccp = ccp
                #scadenze: quella della riba
                scad = reg.scad
                scad.CreateNewRow()
                scad.datscad = eff.datscad
                scad.importo = eff.impeff
                scad.abbuono = 0
                scad.spesa =   0
                scad.id_pcf =  eff.id
                if reg.Save():
                    if pcf.Get(eff.id):
                        #la registrazione contabile aggiorna la partita che
                        #sto lavorando come effetto; adeguo importo e pareggiam.
                        #dell'effetto così come risulta dopo tale aggiornamento
                        eff.imptot = pcf.imptot
                        eff.imppar = pcf.imppar
                else:
                    awu.MsgDialog(\
                        self,\
                        "Problema durante la contabilizzazione dell'effetto:\n"\
                        % repr(reg.GetError()))
                    cok = False
                    break
                eff.f_effsele = 0
                eff.f_effcont = 1
                eff.id_effreg = reg.id
                if te == 'S':
                    bancf = adb.DbTable(bt.TABNAME_BANCF, "bancf")
                    bancf.Get(self.dbeff.bap.id)
                    bancf.rcur=1
                    bancf.Save()
            if not wait.SetValue(eff.RowNumber()):
                break

        wait.Destroy()

        if cok:
            self.SaveEff()
            awu.MsgDialog(self, message="Contabilizzazione terminata.")
            self.UpdateEff(msg=False)

    def SaveEff(self):
        out = self.dbeff.Save()
        if not out:
            awu.MsgDialog(\
                self,\
                "Problema durante la memorizzazione degli effetti:\n%s"\
                % repr(self.dbeff.GetError()))
        return out

    def GetValori(self, *campi):
        ctrls = {wdr.ID_DATDIST:  "Data distinta",\
                 wdr.ID_BANCA:    "Banca emittente",\
                 wdr.ID_CONTOEFF: "Conto effetti",\
                 wdr.ID_CAUCONT:  "Causale contabile",\
                 wdr.ID_FILEPATH: "Percorso generazione file"}
        out = []
        cn = lambda x: self.FindWindowById(x)
        for c in campi:
            v = cn(c).GetValue()
            if not v and c in ctrls:
                awu.MsgDialog(self, "Occorre indicare: %s" % ctrls[c])
            out.append(v)
        return out


# ------------------------------------------------------------------------------


class EmiEffettiFrame(aw.Frame):
    """
    Frame Gestione Effetti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(EmiEffettiPanel(self, -1))


# ------------------------------------------------------------------------------


class EmiEffettiDialog(aw.Dialog):
    """
    Dialog Gestione tabella Effetti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(EmiEffettiPanel(self, -1))


# ------------------------------------------------------------------------------


if __name__ == "__main__":

    class _testApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            Env.Azienda.DB.testdb()
            db = adb.DB()
            db.Connect()
            return True

    app = _testApp(True)
    app.MainLoop()
    Env.InitSettings()
    test = EmiEffettiDialog()
    test.ShowModal()
