#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dataentry_b.py
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

import stormdb as adb
import magazz as m
import magazz.dataentry_wdr as wdr

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import wx
import wx.grid as gl
import awc.controls.windows as aw
import awc.controls.dbgrid as dbglib
import awc.controls.dbgrideditors as dbgred

from awc.controls.linktable import EVT_LINKTABCHANGED

import magazz.dbtables as dbm
import magazz.barcodes as bcode

from reportlab.pdfbase.pdfmetrics import stringWidth

import copy


import time

_DEBUG=False

def ElapsedTime(msg='', reset = False):
    if _DEBUG:
        global start_time
        if reset:
            start_time = time.time()
        else:
            try:
                print '%s %s' % (msg, time.time() - start_time)
            except:
                print 'errore'
            start_time = time.time()
    return True



def DbgMsg(x):
    if _DEBUG:
        print '[standard dataentry_b] ->%s' % x
    pass


class AcqPDTRiepGrid(dbglib.DbGridColoriAlternati):

    _lastrow = None

    def __init__(self, parent, db, *args, **kwargs):

        kwargs['size'] = parent.GetClientSizeTuple()
        dbglib.DbGridColoriAlternati.__init__(self, parent, *args, **kwargs)

        self.dbpdt = db

        _STR = gl.GRID_VALUE_STRING
        _NUM = gl.GRID_VALUE_NUMBER
        _DAT = gl.GRID_VALUE_DATETIME

        def cn(db, col):
            return db._GetFieldIndex(col)

        cols = (( 140, (cn(db, 'descriz'), "Riferimento", _STR, True )),\
                (  80, (cn(db, 'datins'),  "Data",        _DAT, True )),\
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        self.SetData(db.GetRecordset(), colmap, canEdit=False, canIns=False)

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnRowSel)

    def OnRowSel(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbpdt.RowsCount():
            if row != self._lastrow:
                self.dbpdt.MoveRow(row)
                self._lastrow = row
        event.Skip()


# ------------------------------------------------------------------------------


class AcqPDTRigheGrid(dbglib.DbGridColoriAlternati):

    def __init__(self, parent, dblet, *args, **kwargs):

        kwargs['size'] = parent.GetClientSizeTuple()
        dbglib.DbGridColoriAlternati.__init__(self, parent, *args, **kwargs)

        colcod = dblet.prod._GetFieldIndex('codice', inline=True)
        coldes = dblet.prod._GetFieldIndex('descriz', inline=True)
        colqta = dblet._GetFieldIndex('qta')

        _STR = gl.GRID_VALUE_STRING
        _NUM = gl.GRID_VALUE_NUMBER

        cols = (( 80, (colcod, "Cod.",     _STR, True  )),\
                (200, (coldes, "Articolo", _STR, True  )),\
                ( 90, (colqta, "Qta",      _NUM, True  )),\
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        self.SetData((), colmap, canEdit=False, canIns=False)

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


# ------------------------------------------------------------------------------


class AcqPDTDialog(aw.Dialog):

    dbpdt = None

    def __init__(self, *args, **kwargs):
        self.dbpdt = kwargs.pop('dbpdt')
        aw.Dialog.__init__(self, *args, **kwargs)
        wdr.AcqPDTFunc(self)
        self.CenterOnScreen()
        cid = lambda x: self.FindWindowById(x)
        self.gridriep = AcqPDTRiepGrid(cid(wdr.ID_ACQPDTRIEP), self.dbpdt)
        self.gridlett = AcqPDTRigheGrid(cid(wdr.ID_ACQPDTGRID), self.dbpdt.pdt_b)
        self.gridriep.Bind(gl.EVT_GRID_SELECT_CELL, self.OnUpdateLett)
        self.gridriep.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnAcq)
        for cid, func in ((wdr.ID_BTNACQPDT, self.OnAcq),
                          (wdr.ID_BTNDELPDT, self.OnDel),):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        self.UpdateLett()

    def OnUpdateLett(self, event):
        self.UpdateLett(event.GetRow())
        event.Skip()

    def UpdateLett(self, row=0):
        db = self.dbpdt
        if 0 <= row < db.RowsCount():
            db.MoveRow(row)
            rs = db.pdt_b.GetRecordset()
        else:
            rs = ()
        self.gridlett.ChangeData(rs)

    def OnAcq(self, event):
        if aw.awu.MsgDialog(self, 'Confermi l\'acquisizione delle letture ?',
                            style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            self.EndModal(wx.ID_YES)
        event.Skip()

    def OnDel(self, event):
        row = self.gridriep.GetSelectedRows()[0]
        p = self.dbpdt
        if 0 <= row < p.RowsCount():
            if aw.awu.MsgDialog(self, 'Confermi l\'eliminazione di queste letture ?',
                                style=wx.ICON_WARNING|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                p.MoveRow(row)
                p.Delete()
                p.Save()
                self.EndModal(wx.ID_NO)
        event.Skip()


# ------------------------------------------------------------------------------


class LongDescrizPanel(wx.Panel):

    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.LongDescrizBodyFunc(self)


# ------------------------------------------------------------------------------


class LongDescrizDialog(aw.Dialog):

    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(LongDescrizPanel(self))
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, self.FindWindowByName('butoklongdes'))

    def SetLongDescriz(self, x, maxlen, editable):
        cn = self.FindWindowByName
        c = cn('longdescriz')
        c.SetMaxLength(maxlen)
        c.SetValue(x)
        if not editable:
            #c.SetReadOnly(True)
            cn('butoklongdes').Disable()

    def GetLongDescriz(self):
        return self.FindWindowByName('longdescriz').GetValue()

    def OnConfirm(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class SelezionaMovimentoAccontoGrid(dbglib.DbGridColoriAlternati):

    def __init__(self, parent, dbacc):

        dbglib.DbGridColoriAlternati.__init__(self, parent,
                                              size=parent.GetClientSizeTuple())

        self.dbacc = dbacc

        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _IMP = bt.GetValIntMaskInfo()

        def cn(col):
            return dbacc._GetFieldIndex(col, inline=True)

        cols = (( 40, (cn('accotpd_codice'),   "Cod.",        _STR, True )),
                (150, (cn('accotpd_descriz'),  "Causale",     _STR, True )),
                ( 50, (cn('accodoc_numdoc'),   "Num.",        _NUM, True )),
                ( 80, (cn('accodoc_datdoc'),   "Data",        _DAT, True )),
                (110, (cn('accomov_importo'),  "Acconto",     _IMP, True )),
                ( 40, (cn('accoiva_codice'),   "IVA",         _STR, True )),
                (110, (cn('acconto_disponib'), "Disponibile", _IMP, False)),
                (300, (cn('accomov_descriz'),  "Descrizione", _STR, True )),)

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        self.SetData((), colmap, canEdit=False, canIns=False)

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


# ------------------------------------------------------------------------------


class SelezionaMovimentoAccontoStorniGrid(dbglib.DbGridColoriAlternati):

    def __init__(self, parent, dbmov):

        dbglib.DbGridColoriAlternati.__init__(self, parent,
                                              size=parent.GetClientSizeTuple())

        self.dbmov = dbmov
        mov = dbmov
        tpm = mov.tipmov
        iva = mov.iva
        doc = mov.doc
        tpd = doc.tipdoc

        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _IMP = bt.GetValIntMaskInfo()

        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)

        cols = (( 40, (cn(tpd, 'codice'),           "Cod.",        _STR, True )),
                (150, (cn(tpd, 'descriz'),          "Causale",     _STR, True )),
                ( 50, (cn(doc, 'numdoc'),           "Num.",        _NUM, True )),
                ( 80, (cn(doc, 'datdoc'),           "Data",        _DAT, True )),
                (110, (cn(mov, 'importo'),          "Storno",      _IMP, True )),
                ( 40, (cn(iva, 'codice'),           "IVA",         _STR, True )),
                (110, (cn(mov, 'acconto_disponib'), "Disponibile", _IMP, False)),
                (300, (cn(mov, 'descriz'),          "Descrizione", _STR, True )),)

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        self.SetData((), colmap, canEdit=False, canIns=False)

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


# ------------------------------------------------------------------------------


class SelezionaMovimentoAccontoPanel(wx.Panel):

    def __init__(self, *args, **kwargs):

        wx.Panel.__init__(self, *args, **kwargs)
        self.SetName('accontipanel')
        self.pdcid = None
        self.lastmovaccid = None
        wdr.SelezionaMovimentoAccontoFunc(self)
        cn = self.FindWindowByName

        self.dbacc = dbm.PdcSituazioneAcconti()
        self.dbacc.VediSoloAperti()
        self.gridacc = SelezionaMovimentoAccontoGrid(cn('pangridacc'), self.dbacc)

        self.dbsto = dbm.PdcSituazioneStorniAcconto()
        self.gridsto = SelezionaMovimentoAccontoStorniGrid(cn('pangridsto'), self.dbsto)

        self.Bind(wx.EVT_CHECKBOX, self.OnChiusi, cn('anchechiusi'))
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelected, self.gridacc)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSelectRow, self.gridacc)

    def OnCellSelected(self, event):
        row = event.GetRow()
        acc = self.dbacc
        if 0 <= row < acc.RowsCount():
            acc.MoveRow(row)
            self.UpdateAnag()
            if acc.accomov_id != self.lastmovaccid:
                acc.MoveRow(row)
                self.UpdateStorni(acc.accomov_id, acc.accomov_importo)
                event.Skip()

    def UpdateAnag(self):
        self.FindWindowByName('rsanag').SetLabel(self.dbacc.pdc_descriz)

    def OnChiusi(self, event):
        self.UpdateData()
        event.Skip()

    def OnSelectRow(self, event):
        self.dbacc.MoveRow(event.GetRow())
        if (self.dbacc.acconto_disponib or 0) > 0:
            event.Skip()

    def SetPdcId(self, pdcid):
        self.pdcid = pdcid
        self.UpdateData()

    def UpdateData(self):
        dbacc = self.dbacc
        if self.FindWindowByName('anchechiusi').IsChecked():
            dbacc.VediTutti()
        else:
            dbacc.VediSoloAperti()
        dbacc.GetForPdc(self.pdcid)
        self.gridacc.ChangeData(dbacc.GetRecordset())
        if not dbacc.IsEmpty():
            self.gridacc.SelectRow(0)
            self.UpdateStorni(dbacc.accomov_id, dbacc.accomov_importo)
        else:
            self.UpdateStorni(None, 0)

    def UpdateStorni(self, accomov_id, accdisp):
        mov = self.dbsto
        if accomov_id is None:
            mov.Reset()
        else:
            mov.Retrieve("mov.id_movacc=%s", accomov_id)
            for mov in mov:
                accdisp -= abs(mov.importo)
                mov.acconto_disponib = accdisp
        self.lastmovaccid = accomov_id
        self.gridsto.ChangeData(mov.GetRecordset())


# ------------------------------------------------------------------------------


class SelezionaMovimentoAccontoDialog(aw.Dialog):

    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = 'Situazione acconti cliente'
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = SelezionaMovimentoAccontoPanel(self)
        self.AddSizedPanel(self.panel)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSelectRow)

    def OnSelectRow(self, event):
        self.EndModal(wx.ID_OK)

    def SetPdcId(self, *args, **kwargs):
        return self.panel.SetPdcId(*args, **kwargs)


# ------------------------------------------------------------------------------


class GridBody(object):
    """
    Gestione griglia dataentry dettaglio magazzino
    """
    pangridbody = None
    def __init__(self):
        object.__init__(self)


        self.gridbody = None
        self.gridlist = None
        self.gridmovi = None
        self.lastmovid = None
        self.lastprod = None
        self.pdc_cg_tip = None

        mov = self.dbdoc.mov
        m.RSMOV_codmov = mov.config._GetFieldIndex("codice", inline=True)
        m.RSMOV_desmov = mov.config._GetFieldIndex("descriz", inline=True)
        m.RSMOV_codart = mov.prod._GetFieldIndex("codice", inline=True)
        m.RSMOV_desart = mov.prod._GetFieldIndex("descriz", inline=True)
        m.RSMOV_codiva = mov.iva._GetFieldIndex("codice", inline=True)
        m.RSMOV_desiva = mov.iva._GetFieldIndex("descriz", inline=True)
        m.RSMOV_codlis = mov.tiplist._GetFieldIndex("codice", inline=True)
        m.RSMOV_deslis = mov.tiplist._GetFieldIndex("descriz", inline=True)
        m.RSMOV_PDCCG_cod = mov.pdccg._GetFieldIndex("codice", inline=True)
        m.RSMOV_PDCCG_des = mov.pdccg._GetFieldIndex("descriz", inline=True)

        self.GetEsenti()
        



        class UsableProdTable(adb.DbTable):
            def __init__(self):
                adb.DbTable.__init__(self, bt.TABNAME_PROD, 'prod', writable=True)
                self.AddJoin(bt.TABNAME_STATART, 'status', idLeft='id_status', join=adb.JOIN_LEFT)
            def IsUsableWithClasDoc(self, clasdoc_key):
                out = True
                try:
                    out = getattr(self.status, 'nomov_%s' % clasdoc_key) != 1
                except:
                    pass
                return out

        self.dbprod = UsableProdTable()
        self.dbaliq = adb.DbTable(bt.TABNAME_ALIQIVA, "iva",  writable=True)
        self.dbinv = dbm.InventarioDaMovim()

        self._cache_giacenze = {}

    def GetEsenti(self):
        self.esenti=[]
        if (bt.MAGIVAPREVA or 0)=='1':
            iva = dbm.AliqIva()
            self.esenti = iva.GetEsenti()
            #print self.esenti


    def SetPdcCgTip(self, pdc_cg_tip):
        self.pdc_cg_tip = pdc_cg_tip

    def GridBodyDefColumns(self):

        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        _PZC = bt.GetMagQtaMaskInfo(numint=6)

        viscosto = vismargine = False
        for tm in self.dbdoc.cfgdoc.tipmov:
            if (tm.mancosto or ' ') in 'VM':
                viscosto = True
                vismargine = (self.dbdoc.cfgdoc.scorpiva != '1')
                break


        cols = []
        def a(x):
            cols.append(x)
            return len(cols)-1

        for attr in dir(self):
            if attr.startswith('COL_'):
                delattr(self, attr)

        self.COL_codmov =  a(( 35, [m.RSMOV_codmov,    "Mov.",           _STR, True]))
        self.COL_codart =  a(( 80, [m.RSMOV_codart,    "Codice",         _STR, True]))
        self.COL_DESCRIZ = a((300, [m.RSMOV_DESCRIZ,   "Descrizione",    _STR, True]))
        self.COL_UM =      a(( 40, [m.RSMOV_UM,        "U.M.",           _STR, True]))

        if bt.MAGPZCONF:
            self.COL_NMCONF = a((1, [m.RSMOV_NMCONF, "Confez.",          _PZC, True]))
            self.COL_PZCONF = a((1, [m.RSMOV_PZCONF, "Pz.Conf.",         _PZC, True]))

        self.COL_QTA =     a((1, [m.RSMOV_QTA,       "Quantità",         _QTA, True]))

        if bt.MAGROWLIS and self.dbdoc.cfgdoc.rowlist == 'X':
            self.COL_codlist = a((40, [m.RSMOV_codlis, "List.",         _STR, True]))

        self.COL_PREZZO =  a((1, [m.RSMOV_PREZZO,    "Prezzo",           _PRE, True]))

        if (bt.MAGATTGRIP or bt.MAGATTGRIF) and bt.MAGAGGGRIP:
            self.COL_AGGGRIP = a(( -1, [m.RSMOV_AGGGRIP, "AGP",          _CHK, True]))

        numsco = bt.MAGNUMSCO
        c = self.dbdoc.cfgdoc.numsconti or 0
        if 0 < c < numsco:
            numsco = c

        if numsco >= 1:
            self.COL_SC1 = a((  1, [m.RSMOV_SC1,       "Sc.%"+'1'*int(numsco>1), _SCO, True]))
        if numsco >= 2:
            self.COL_SC2 = a((  1, [m.RSMOV_SC2,       "Sc.%2",          _SCO, True]))
        if numsco >= 3:
            self.COL_SC3 = a((  1, [m.RSMOV_SC3,       "Sc.%3",          _SCO, True]))
        if numsco >= 4:
            self.COL_SC4 = a((  1, [m.RSMOV_SC4,       "Sc.%4",          _SCO, True]))
        if numsco >= 5:
            self.COL_SC5 = a((  1, [m.RSMOV_SC5,       "Sc.%5",          _SCO, True]))
        if numsco >= 6:
            self.COL_SC6 = a((  1, [m.RSMOV_SC6,       "Sc.%6",          _SCO, True]))

        self.COL_IMPORTO = a((  1, [m.RSMOV_IMPORTO,   "Importo",        _IMP, True]))
        self.COL_codiva =  a(( 35, [m.RSMOV_codiva,    "Iva",            _STR, True]))
        self.COL_NOTE =    a((200, [m.RSMOV_NOTE,      "Note",           _STR, True]))
        self.COL_PERPRO =  a(( 60,[-m.RSMOV_PERPRO,    "Provv.%",        _SCO, True]))
        self.COL_desmov =  a((140, [m.RSMOV_desmov,    "Mov.",           _STR, True]))
        self.COL_pdccod =  a(( 50, [m.RSMOV_PDCCG_cod, "Cod.",           _STR, True]))
        self.COL_pdcdes =  a((200, [m.RSMOV_PDCCG_des, "Coll.Contabile", _STR, True]))

        if viscosto:
            self.COL_COSTOU =      a((1, [m.RSMOV_COSTOU, "Costo U.",    _PRE, True]))
            self.COL_COSTOTOT =    a((1, [m.RSMOV_COSTOT, "Costo Tot.",  _IMP, True]))
        if vismargine:
            self.COL_VENDITATOT =  a((1, [-1,             "T.Vendita",   _IMP, True]))
            self.COL_MARGINEVAL =  a((1, [-1,             "Margine",     _IMP, True]))
            self.COL_MARGINEPERC = a((1, [-1,             "Marg.%",      _SCO, True]))

        self.COL_ID =      a((  1, [m.RSMOV_ID,        "#mov",           _STR, True]))
        self.COL_ID_PROD = a((  1, [m.RSMOV_ID_PROD,   "#pro",           _STR, True]))
        self.COL_ID_ALIQ = a((  1, [m.RSMOV_ID_IVA,    "#iva",           _STR, True]))

        return cols

    def GridBody_InsertNewColumn(self, columns, index_aftercol, cstru):
        columns.insert(index_aftercol+1, cstru)
        #sposto a destra di una colonne tutte quelle già esistenti, a partire da quella inserita
        #(il cui nome non esiste ancora sotto forma di COL_xxx: viene settato al ritorno di questa funzione)
        column_names = []
        for attr_name in dir(self):
            if attr_name.startswith('COL_'):
                if getattr(self, attr_name) > index_aftercol:
                    column_names.append(attr_name)
        for column_name in column_names:
            setattr(self, column_name, getattr(self, column_name)+1)
        return index_aftercol+1

    def GridBody_Init(self, parent):
        self.default_tipmov=None
        for r in self.dbdoc.cfgdoc.tipmov:
            if r.is_default:
                self.default_tipmov=r.id
                break
        if self.gridbody:
            wx.CallAfter(self.gridbody.Destroy)

        #costruzione griglia dettaglio documento
        size = parent.GetClientSizeTuple()

        cols = self.GridBodyDefColumns()

        mov = self.dbdoc.mov
        cn = lambda tab, col: tab._GetFieldIndex(col, inline=True)
        self.avcol = cn(mov.config, "askvalori")
        self.tpcol = cn(mov.config, "tipologia")
        self.pocol = cn(mov.config, "proobb")
        self.agcol = cn(mov.config, "agggrip")
        self.mccol = cn(mov.config, "mancosto")
        self.p0col = cn(mov.config, "canprezzo0")
        self.cacol = cn(mov, "id_prod")
        self.prcol = cn(mov, "perpro")

        self.importo_col = cn(mov, 'importo')
        self.costot_col = cn(mov, 'costot')
        self.statftcli_col = cn(mov.config, 'statftcli')
        self.statcscli_col = cn(mov.config, 'statcscli')

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = True

        links = self.GridBodyDefLinks()
        editors = self.GridBodyDefEditors()
        afteredit = self.GridBodyDefAfterEdit()

        grid = dbglib.DbGrid(parent, -1, size=size, tableClass=self.GridBodyGetTable(), idGrid='magbody')

        #imposto lungh. max. su campi char
        stru = bt.tabelle[bt.TABSETUP_TABLE_MOVMAG_B][bt.TABSETUP_TABLESTRUCTURE]
        for c_name, c_type, c_len, c_dec, c_desc, c_constr in stru:
            if "CHAR" in c_type:
                c = self.dbdoc.mov._GetFieldIndex(c_name, inline=True)
                if c >= 0:
                    grid.SetColMaxChar(c, c_len)

        #grid.SetColMaxChar(m.RSMOV_DESCRIZ, bt.getcolwidth(bt.TABNAME_MOVMAG_B, 'descriz'))
        #grid.SetColMaxChar(m.RSMOV_NOTE, bt.getStdNoteWidth())
        grid.SetData( self.dbdoc.mov._info.rs, colmap, canedit, canins,\
                      links, afteredit, self.GridBodyAddNewRow,
                      editors=editors)


        grid.SetRowDynLabel(self.GridBodyGetRowLabel)
        grid.SetCellDynAttr(self.GridBodyGetAttr)

        self._rowcol = None

        grid.SetColumnsFunc(self.GridBodyMoveColumnAfterEdit)

        grid.SetColDefault(self.COL_codart)
        grid.Bind(gl.EVT_GRID_SELECT_CELL, self.GridBodyOnSelected)

        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        grid.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.GridBodyOnRightClick)
        grid.Bind(dbgred.EVT_EDITORSHOWN, self.GridBodyOnEditorShown)
        grid.Bind(gl.EVT_GRID_CELL_LEFT_CLICK, self.GridBodyOnClick)
        grid.Bind(wx.EVT_KEY_UP, self.GridBodyOnKeyPress)

        self.gridbody = grid


    def CreateNewRow(self):
        mov = self.dbmov
        mov.CreateNewRow()
        self.ForceResetView()
        return True


    def GridBodyDefLinks(self):

        import anag.lib as alib

        links = []
        ltmov = dbglib.LinkTabAttr(bt.TABNAME_CFGMAGMOV, #table
                                   self.COL_codmov,      #grid col
                                   m.RSMOV_ID_TMOV,      #rs col id
                                   m.RSMOV_codmov,       #rs col cod
                                   -1,                   #rs col des
                                   None)                 #card class
        ltmov.AddBinding((self, self.GridBodyOnTipMovChanged))
        links.append(ltmov)

        from anag.aliqiva import AliqIvaDialog

        ltiva = dbglib.LinkTabAttr(bt.TABNAME_ALIQIVA, #table
                                   self.COL_codiva,    #grid col
                                   m.RSMOV_ID_IVA,     #rs col id
                                   m.RSMOV_codiva,     #rs col cod
                                   -1,                 #rs col des
                                   AliqIvaDialog,      #card class
                                   refresh=True)       #refresh flag
        links.append(ltiva)

        from anag.pdc import PdcDialog

        def SetPdcTip(tc, ed, x):
            f = tc.SetFocus
            def SetFocusLinkTablePdc(*x):
                tipid, filt = tc.magpanel.GetFiltriCP()
                tc.SetFilterValue(tipid)
                tc.SetFilterFilter(filt)
                wx.Window.SetFocus(tc)
            tc.SetFocus = SetFocusLinkTablePdc
            tc.magpanel = self
        ltpdc = alib.LinkTabPdcAttr(bt.TABNAME_PDC,     #table
                                    self.COL_pdccod,    #grid col
                                    m.RSMOV_PDCCG_ID,   #rs col id
                                    m.RSMOV_PDCCG_cod,  #rs col cod
                                    m.RSMOV_PDCCG_des,  #rs col des
                                    PdcDialog,          #card class
                                    refresh=True,       #refresh flag
                                    oncreate=SetPdcTip) #on create call
        links.append(ltpdc)

        if bt.MAGROWLIS and self.dbdoc.cfgdoc.rowlist == 'X':

            from anag.tiplist import TipListDialog

            ltlis = dbglib.LinkTabAttr(bt.TABNAME_TIPLIST, #table
                                       self.COL_codlist,   #grid col
                                       m.RSMOV_TIPLIST,    #rs col id
                                       m.RSMOV_codlis,     #rs col cod
                                       -1,                 #rs col des
                                       TipListDialog,      #card class
                                       refresh=True)       #refresh flag
            links.append(ltlis)


        if self.pangridbody == None:
            self.pangridbody = self.FindWindowById(wdr.ID_PANGRIDBODY)
            self.pangridbody.Bind(wx.EVT_KEY_DOWN, self.OnTestGridChar)


        return links

    def OnTestGridChar(self, event):
        key = event.GetKeyCode()
        if key==wx.WXK_F5 and self.dbdoc.cfgdoc.multilinee==1 and self.FindWindowByName('butmultilinea').IsEnabled():
            self.ShowMultiLineDialog()
        event.Skip()

    def ShowMultiLineDialog(self):
        dlg=MultiLineDialog(self, cfgdoc=self.dbdoc.cfgdoc)
        x= (475.0/259.0) * int(self.dbdoc.cfgdoc.dessize) + 5442.0/259.0
        x = x * (7.0 / float(self.dbdoc.cfgdoc.fontsize))
        x = x+15
        dlg.SetSize((x,300))
        dlg.SetMinSize(dlg.GetSize())
        dlg.CenterOnScreen()
        dlg.ShowModal()
        ret=dlg.ReturnValue
        if ret['esito']:
            idTipMov=ret['idTipMov']
            lRow=ret['testo']

            mov = self.dbdoc.mov
            for row in lRow:
                self.GridBodyAddNewRow()
                mov.MoveLast()
                mov.id_tipmov = idTipMov
                mov.descriz = row.encode().decode()
            self.gridbody.ResetView()
            self.MakeTotals()
        dlg.Destroy()
        

    def GridBodyDefEditors(self):

        import anag.lib as alib
        from anag.prod import ProdDialog

        editors = []
        prod_editor = alib.DataLinkProdCellEditor(bt.TABNAME_PROD, #table
                                                  m.RSMOV_ID_PROD, #rs col id
                                                  m.RSMOV_codart,  #rs col cod
                                                  -1,              #rs col des
                                                  ProdDialog)      #card class
        editors.append((self.COL_codart, prod_editor))

        return editors

    def GridBodyMoveColumnAfterEdit(self, grid, row, col):
        mov = self.dbdoc.mov
        if 0 <= row < mov.RowsCount():
            if self._rowcol:
                row, col = self._rowcol
                self._rowcol = None
            else:
                avcol = mov.config._GetFieldIndex("askvalori", inline=True)
                askv = mov._info.rs[row][avcol] or ''
                col = grid.GetTable().col2rs(col)
                if col == m.RSMOV_codmov:
                    if askv in 'QT':
                        col = m.RSMOV_codart
                    else:
                        col = m.RSMOV_DESCRIZ
                elif col in (m.RSMOV_codart, m.RSMOV_DESCRIZ):
                    if askv in 'QT':
                        if bt.MAGPZCONF:
                            col = m.RSMOV_NMCONF
                        else:
                            if mov.um:
                                col = m.RSMOV_QTA
                            else:
                                col = m.RSMOV_UM
                    elif askv == 'T':
                        col = m.RSMOV_IMPORTO
                else:
                    row = col = None
                if col is not None:
                    col = grid.GetTable().rs2col(col)
        return row, col

    def GridBodyDefAfterEdit(self):
        return ((dbglib.CELLEDIT_BEFORE_UPDATE, -1, self.GridBodyEditingValues),
                (dbglib.CELLEDIT_AFTER_UPDATE, -1, self.GridBodyEditedValues),)

    def GridBodyGetTable(self):

        class GridBodyTable(dbglib.DbGridTable):

            def GetDataValue(grid, row, col, gridcols=False):
                out = None
                if row<len(grid.data):
                    if col in (getattr(self, "COL_VENDITATOT", None),
                               getattr(self, "COL_MARGINEVAL", None),
                               getattr(self, "COL_MARGINEPERC", None),):
                        doc = self.dbdoc
                        mov = doc.mov
                        try:
                            r = mov.GetRecordset()[row]
                            vendita = (r[self.importo_col] or 0)*(r[self.statftcli_col] or 0)
                            if col == getattr(self, "COL_VENDITATOT", None) and vendita:
                                out = vendita
                            else:
                                totcost = (r[self.costot_col] or 0)*(r[self.statcscli_col] or 0)
                                if col == getattr(self, "COL_MARGINEVAL", None):# and totcost:
                                    out = vendita-totcost
                                elif col == getattr(self, "COL_MARGINEPERC", None):# and totcost:
                                    out = (vendita-totcost)/vendita*100
                        except:
                            pass
                if out is None:
                    out = dbglib.DbGridTable.GetDataValue(grid, row, col, gridcols)
                return out

            def GetValue(self, row, col):
                out = None
                if row<len(self.data):
                    if self.rsColumns[col] == -m.RSMOV_PERPRO:
                        perpro = self.data[row][m.RSMOV_PERPRO]
                        if perpro is None:
                            out = '-auto-'
                        else:
                            out = '%.2f' % perpro
                if out is None:
                    out = dbglib.DbGridTable.GetValue(self, row, col)
                return out

        return GridBodyTable

    def GetFiltriCP(self):
        da = self.dbdoc.cfgdoc.descanag
        if 'clie' in da.lower():
            tipid = self._auto_pdctip_ricavi
        else:
            tipid = self._auto_pdctip_costi
        return tipid, '1'

    def GridBodyOnClick(self, event):
        if self.status == m.STATUS_EDITING and hasattr(self, 'COL_AGGGRIP'):
            mov = self.dbdoc.mov
            row, col = event.GetRow(), event.GetCol()
            if col == self.COL_AGGGRIP:
                if 0 <= row < mov.RowsCount():
                    mov.MoveRow(row)
                    if (mov.config.agggrip or ' ') in 'AN':
                        mov.agggrip = 1-(mov.agggrip or 0)
                        self.gridbody.ResetView()
        event.Skip()

    def GridBodyOnKeyPress(self, event):
        pass

    def GridBodyOnEditorShown(self, event):
        row, col = event.GetRow(), event.GetCol()
        t = self.gridbody.GetTable()
        #if t.rsColumns[col] == m.RSMOV_PDCCG_cod:
            #pass
        if t.rsColumns[col] == m.RSMOV_DESCRIZ:
            pass
        event.Skip()

    def GridBodyOnLabels(self, event):
        self.GridBodyPrintEtichette()
        event.Skip()

    def GridBodyPrintEtichette(self):
        dlg = bcode.SelQtaDialog(self)
        do = dlg.ShowModal() == wx.ID_OK
        dlg.Destroy()
        if not do:
            return
        wait = aw.awu.WaitDialog(self.GetParent(),
                                 message='Preparazione etichette in corso...')
        try:
            db = dbm.ProdEticList()
            db.ShowDialog(self.GetParent())
            for n, mov in enumerate(self.dbdoc.mov):
                if mov.id_prod is not None:
                    do = True
                    if dlg.GetSoloInterni():
                        do = False
                        bc = mov.prod.barcode
                        if bc is not None:
                            if bc.startswith(bt.MAGEAN_PREFIX):
                                do = True
                    if do:
                        db.CreateNewRow()
                        db.id = mov.id_prod
                        db.qtaetic = dlg.GetQta(mov.qta)
                wait.SetValue(n)
        finally:
            wait.Destroy()
        if db.RowsCount() == 0:
            aw.awu.MsgDialog(self, message="Nessuna etichetta da stampare.")
            return
        SelDialog = bcode.EtichetteProdottiDialog
        dlg = SelDialog(self, title='Etichette prodotti da documento')
        dlg.SetProdEticList(db)
        dlg.ShowModal()
        dlg.Destroy()

    def GridBodyOnLongDescriz(self, event):
        mov = self.dbdoc.mov
        d = LongDescrizDialog(self)
        d.SetLongDescriz(mov.descriz, mov.config.lendescriz or 60, self.status == m.STATUS_EDITING)
        if d.ShowModal() == wx.ID_OK:
            self.dbdoc.mov.descriz = d.GetLongDescriz()
            self.gridbody.Refresh()
        event.Skip()

    def GridBodyOnSchedaProd(self, event):
        self.ApriSchedaProdotto(mas=False)
        event.Skip()

    def GridBodyOnMastroMov(self, event):
        self.ApriSchedaProdotto(mas=True)
        event.Skip()

    def ApriSchedaProdotto(self, mas):
        mov = self.dbdoc.mov
        assert isinstance(mov, adb.DbTable)
        row = self.gridbody.GetSelectedRows()[0]
        if not 0 <= row < mov.RowsCount():
            return
        mov.MoveRow(row)
        proid = mov.id_prod
        if proid is None:
            aw.awu.MsgDialog(self, message='La riga non si riferisce ad un prodotto codificato')
            return
        wx.BeginBusyCursor()
        from magazz.prodint import ProdInterrDialog
        f = ProdInterrDialog(self, onecodeonly=proid)
        f.OneCardOnly(proid)
        f.CenterOnScreen()
        wx.EndBusyCursor()
        if mas:
            #f.panel.DisplayMastro()
            f.SelectZone('mastro')
            f.SelectZone('movimenti', notebook_name='mastrozone')
        f.ShowModal()
        f.Destroy()
        self.dbprod.Reset()
        self.lastprod = None
        self.UpdateProdZone(proid)

    def GridBodyMakeMenuPopup(self):
        edit = self.status == m.STATUS_EDITING
        mov = self.dbdoc.mov
        prodok = mov.id_prod is not None
        longok = (mov.config.lendescriz or 60) > 60
        voci = []
        voci.append(["Edita descrizione estesa",          self.GridBodyOnLongDescriz, longok])
        voci.append(["Apri la scheda del prodotto",       self.GridBodyOnSchedaProd, prodok])
        voci.append(["Visualizza il mastro del prodotto", self.GridBodyOnMastroMov,  prodok])
        if edit:
            desc = "Elimina riga"
            voci.append([desc, self.GridBodyOnDelete, True])
            voci.append(["Imposta provvigione a zero", self.GridBodyOnAzzPro, True])
            if prodok and mov.perpro is not None:
                voci.append(["Annulla provvigione manuale", self.GridBodyOnAnnPro, True])
            if bt.MAGGESACC == 1 and mov.config.is_accstor:
                voci.append(['-', None, None])
                if mov.id_movacc is None:
                    voci.append(['Aggancia Acconto', self.GridBodyOnLinkToAcconto, True])
                else:
                    voci.append(['Sgancia da Acconto', self.GridBodyOnUnlinkFromAcconto, True])
        return voci

    def GridBodyMenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        self.gridbody.SetGridCursor(row, col)
        self.gridbody.SelectRow(row)
        menu = wx.Menu()
        for text, func, enab in self.GridBodyMakeMenuPopup():
            id = wx.NewId()
            if text == '-':
                menu.AppendSeparator()
            else:
                menu.Append(id, text)
                menu.Enable(id, enab)
                self.Bind(wx.EVT_MENU, func, id=id)
        xo, yo = event.GetPosition()
        self.gridbody.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()

    def GridBodyOnRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbdoc.mov.RowsCount():
            self.GridBodyMenuPopup(event)
            event.Skip()

    def GridBodyOnLinkToAcconto(self, event):
        doc = self.dbdoc
        mov = doc.mov
        a = dbm.PdcSituazioneAcconti()
        a.GetForPdc(doc.id_pdc)
        dlg = SelezionaMovimentoAccontoDialog(self)
        dlg.SetPdcId(doc.id_pdc)
        do = dlg.ShowModal() == wx.ID_OK
        dlg.Destroy()
        if do:
            dbacc = dlg.panel.dbacc
            mov.descriz = "STORNO ACCONTO FT. N. %s DEL %s" % (dbacc.accodoc_numdoc,
                                                               doc.dita(dbacc.accodoc_datdoc))
            mov.importo = min(dbacc.acconto_disponib, doc.totimponib)
            if doc.cfgdoc.caucon.pasegno != "A":
                mov.importo = -mov.importo
            mov.id_aliqiva = dbacc.accoiva_id
            mov.id_movacc = dbacc.accomov_id
            self.MakeTotals()
            self.gridbody.ForceRefresh()

    def GridBodyOnUnlinkFromAcconto(self, event):
        self.dbdoc.mov.id_movacc = None
        self.gridbody.ForceRefresh()
        event.Skip()

    def GridBodyOnAnnPro(self, event):
        self.dbdoc.mov.perpro = None
        self.gridbody.ForceRefresh()
        event.Skip()

    def GridBodyOnAzzPro(self, event):
        self.dbdoc.mov.perpro = 0
        self.gridbody.ForceRefresh()
        event.Skip()

    def GridBodyOnAcqPDT(self, event):
        self.GridBodyAcqPDT()
        event.Skip()

    def GridBodyAcqPDT(self):
        doc = self.dbdoc
        pra = doc._info.pdtreadann
        if pra:
            flt = "pdt_h.id NOT IN (%s)" % ','.join(map(str, pra))
        else:
            flt = '1'
        dbpdt = dbm.PdtScan()
        if not dbpdt.Retrieve(flt):
            aw.awu.MsgDialog(self, repr(dbpdt.GetError()))
            return
        if dbpdt.RowsCount() == 0:
            aw.awu.MsgDialog(self, 'Nessuna lettura da acquisire')
            return
        dlg = AcqPDTDialog(self, -1, 'Acquisizione letture PDT', dbpdt=dbpdt)
        if dlg.ShowModal() == wx.ID_YES:
            mov = doc.mov
            tmid = self.dbdoc.cfgdoc.GetAcqPDTMov()
            for row in dbpdt.pdt_b:
                self.GridBodyAddNewRow()
                mov.MoveLast()
                mov.id_tipmov = tmid
                mov.id_prod = row.prod.id
                mov.descriz = row.prod.descriz
                #mov.id_aliqiva = row.prod.id_aliqiva
                self.GridBodyDefAliqIva()
                mov.um = row.prod.um
                mov.qta = row.qta
                p, s1, s2, s3, s4, s5, s6 = self.GridBodyDefPrezzoSconti6()
                mov.prezzo = p
                mov.sconto1 = s1 or 0
                mov.sconto2 = s2 or 0
                mov.sconto3 = s3 or 0
                mov.sconto4 = s4 or 0
                mov.sconto5 = s5 or 0
                mov.sconto6 = s6 or 0
                mov.sconto1 = self.GridBodyDefSconto(1, mov)
                mov.sconto2 = self.GridBodyDefSconto(2, mov)
                mov.sconto3 = self.GridBodyDefSconto(3, mov)
                mov.sconto4 = self.GridBodyDefSconto(4, mov)
                mov.sconto5 = self.GridBodyDefSconto(5, mov)
                mov.sconto6 = self.GridBodyDefSconto(6, mov)
                mov.importo = round(mov.prezzo*mov.qta\
                                    *(100-mov.sconto1)/100\
                                    *(100-mov.sconto2)/100\
                                    *(100-mov.sconto3)/100\
                                    *(100-mov.sconto4)/100\
                                    *(100-mov.sconto5)/100\
                                    *(100-mov.sconto6)/100, bt.VALINT_DECIMALS)
            #dbpdt.Delete()
            #dbpdt.Save()
            doc._info.pdtreadann.append(dbpdt.id)
            for i, r in enumerate(doc.mov):
                if r.id_prod==None:
                    r.Delete()
                else:
                    print i, r.id_tipmov, r.id_prod, r.descriz
            self.gridbody.ResetView()
            self.MakeTotals()
        dlg.Destroy()


    def GridBodyReset(self):
        #self.gridbody.ResetView()
        mov = self.dbdoc.mov
        self.gridbody.ChangeData(mov.GetRecordset())
        if mov.RowsCount() == 0:
            self.lastmovid = None
        else:
            mov.MoveLast()
            self.lastmovid = mov.config.id
        self.lastprod = None
        self._cache_giacenze.clear()

    def GridBodyOnTipMovChanged(self, event):
        idtipmov = event.GetEventObject().GetValue()
        if idtipmov is not None:
            self.lastmovid = idtipmov
        event.Skip()

    def GridBodyGetRowLabel(self, row):
        desc = ""
        mov = self.dbdoc.mov
        if 0 <= row < mov.RowsCount():
            mov.MoveRow(row)
            desc = mov.config.descriz
        return desc

    def GridBodyMissVal(self, row, rscol, testcol, tipo):
        out = False
        if rscol == testcol:
            value = self.dbdoc.mov._info.rs[row][rscol]
            if rscol == m.RSMOV_QTA:
                out = (tipo in "QT" and not value)
            elif rscol in (m.RSMOV_PREZZO,\
                 m.RSMOV_SC1, m.RSMOV_SC2, m.RSMOV_SC3):
                out = (tipo == "T" and not value)
            elif rscol == m.RSMOV_IMPORTO:
                out = (tipo in "TV" and not value)
            elif rscol == m.RSMOV_codiva:
                out = (tipo != "D" and not value)
            elif rscol == m.RSMOV_DESCRIZ:
                out = not value
        return out

    def GridBodyGetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        #blocco editazione su cella ID
        readonly = self.status != m.STATUS_EDITING or\
                 (rscol in (m.RSMOV_ID, m.RSMOV_ID_PROD, m.RSMOV_ID_IVA, m.RSMOV_desmov, m.RSMOV_PDCCG_des, m.RSMOV_AGGGRIP)) or\
                 (rscol != m.RSMOV_codmov and self.lastmovid is None)
        fgcol = stdcolor.NORMAL_FOREGROUND
        bgcol = stdcolor.NORMAL_BACKGROUND
        mov = self.dbdoc.mov
        if 0 <= row < mov.RowsCount():
            # vista la frequenza con la quale viene richiamato questo metodo
            # è meglio non ricorrere al posizionamnto sul recordset movimenti
            # con conseguente aggiornamento delle variabili e sottotabelle;
            # determino quindi nel recordset principale moviomenti la posiz.
            # della colonna relativa ad 'askvalori' della sottotabella
            # di configurazione del tipo movimento
            # (self.dbdoc.mov.config.askvalori)
            askv = mov._info.rs[row][self.avcol] or ""
            tipo = mov._info.rs[row][self.tpcol] or ""
            if not readonly and rscol == m.RSMOV_QTA:
                readonly = askv not in "QT"
            if not readonly and rscol in (m.RSMOV_PREZZO, m.RSMOV_SC1,\
                                          m.RSMOV_SC2, m.RSMOV_SC3):
                readonly = askv != "T"
            if not readonly and rscol == m.RSMOV_IMPORTO:
                readonly = askv not in "TV"
            if not readonly and rscol == m.RSMOV_COSTOU:
                readonly = (mov._info.rs[row][self.mccol] or " ") != "M"
            if not readonly and rscol == m.RSMOV_codiva:
                readonly = (askv == "D" or tipo in "IP")
            #impostazione colori
            #sfondo
            rec = mov.GetRecordset()[row]
            val = rec[rscol]
            err = False
            if rscol == m.RSMOV_QTA:
                err = (askv in "QT" and not val)
            elif rscol == m.RSMOV_PREZZO:
                err = (askv == "T" and not val)
            elif rscol == m.RSMOV_AGGGRIP:
                if (mov._info.rs[row][self.agcol] or ' ') in 'AN':
                    readonly = False
            elif rscol == m.RSMOV_IMPORTO:
                err = (askv in "TV" and not val)
            elif rscol == m.RSMOV_codiva:
                err = (askv != "D" and tipo != 'I' and not val)
            elif rscol == m.RSMOV_DESCRIZ and askv != "D":
                err = not val
            elif rscol == -m.RSMOV_PERPRO:
                prob = mov._info.rs[row][self.pocol] or 0
                prod = mov._info.rs[row][self.cacol]
                prov = mov._info.rs[row][self.prcol]
                if prob == 1 and prod is None and prov is None:
                    err = True
            if col in (getattr(self, 'COL_COSTOU', None),
                       getattr(self, 'COL_COSTOTOT', None),
                       getattr(self, 'COL_VENDITATOT', None),
                       getattr(self, 'COL_MARGINEVAL', None),
                       getattr(self, 'COL_MARGINEPERC', None),):
                bgcol = stdcolor.READONLY_BACKGROUND
                if not col in (getattr(self, 'COL_COSTOU', None), getattr(self, 'COL_COSTOTOT', None)) or not askv in "QT":
                    readonly = True
            else:
                if err:
                    bgcol = stdcolor.VALMISS_BACKGROUND
                elif rec[m.RSMOV_ID] is None:
                    bgcol = stdcolor.ADDED_BACKGROUND
            #primopiano
            if rscol == m.RSMOV_IMPORTO and tipo in "IEO":
                fgcol = stdcolor.SCONTI_FOREGROUND
        attr.SetReadOnly(readonly)
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)

        return attr

    def GridBodyVerifyTipMov(self, row, gridcol, col, value):
        mov = self.dbdoc.mov
        if 0 <= row < mov.RowsCount():
            mov.MoveRow(row)
            mov._info.askvprec = mov.config.askvalori
        return True

    def GridBodyEditingValues(self, row, gridcol, col, value):
        if col == m.RSMOV_codmov and value is None:
            aw.awu.MsgDialog(self, 'Definire il tipo movimento', style=wx.ICON_ERROR)
            return False
        elif col == m.RSMOV_codart:
            ElapsedTime('', reset = True)
            prod = self.dbprod
            prod.Get(value)
            ElapsedTime('prod.Get(value)')
            if not prod.IsUsableWithClasDoc(self.dbdoc.cfgdoc.clasdoc):
                aw.awu.MsgDialog(self, "%s - %s\nIl prodotto non è utilizzabile in questo documento" % (prod.codice, prod.descriz),
                                 "Restrizioni sullo status (%s - %s)" % (prod.status.codice, prod.status.descriz),
                                 style=wx.ICON_WARNING)
                return False
            doc = self.dbdoc
            ElapsedTime('', reset = True)
            anag = doc._info.anag = doc.GetAnag()
            ElapsedTime('doc.GetAnag()')

            #===================================================================
            # grip = self.dbdoc._info.dbgrip
            # if not doc.cfgdoc.visultmov==1:
            #     grip.Reset()
            # else:
            #     grip.ClearFilters()
            #     grip.AddFilter("id_pdc=%s", getattr(anag, 'id_pdcgrp', None) or self.dbdoc.id_pdc)
            #     grip.AddFilter("id_prod=%s", value)
            #     if bt.MAGDATGRIP:
            #         grip.AddFilter("data<=%s", self.dbdoc.datreg)
            #     grip.Retrieve()
            #     ElapsedTime('grip.Retrieve()')
            #     if grip.IsEmpty():
            #         sp = getattr(anag, 'grpstop', None)
            #         msg = "Il prodotto non è presente nella griglia dell'anagrafica"
            #         if sp == 'G':
            #             msg += ".\nImpossibile procedere"
            #             aw.awu.MsgDialog(self, msg, style=wx.ICON_ERROR)
            #             return False
            #         elif sp == 'F':
            #             msg += ",tuttavia è possibile forzare il suo utilizzo.\n\nDesideri utilizzare questo prodotto?"
            #             return aw.awu.MsgDialog(self, msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES
            #     ElapsedTime('self.grip.Retrieve()')
            #===================================================================
        elif col == m.RSMOV_IMPORTO:
            doc = self.dbdoc
            mov = doc.mov
            if bt.MAGGESACC == 1 and mov.id_movacc is not None:
                a = dbm.PdcSituazioneAcconti()
                a.GetForPdc(doc.id_pdc, mov.id_movacc, doc.id)
                if abs(value)>a.acconto_disponib:
                    aw.awu.MsgDialog(self, "L'acconto disponibile è di %s" % a.sepnvi(a.acconto_disponib), style=wx.ICON_ERROR)
                    return False
        return True

    def GridBodyEditedValues(self, row, gridcol, col, value):

        resetview = False
        doc = self.dbdoc
        mov = doc.mov
        mov.MoveRow(row)

        def DefImporto():
            i = round((mov.qta or 0)*(mov.prezzo or 0)\
                      *(100-(mov.sconto1 or 0))/100\
                      *(100-(mov.sconto2 or 0))/100\
                      *(100-(mov.sconto3 or 0))/100\
                      *(100-(mov.sconto4 or 0))/100\
                      *(100-(mov.sconto5 or 0))/100\
                      *(100-(mov.sconto6 or 0))/100, bt.VALINT_DECIMALS)
            if len(str(abs(int(i)))) > bt.VALINT_INTEGERS:
                msg =\
                """Il valore dell'importo è troppo elevato,\n"""\
                """sono permesse al massimo %d cifre intere.\n"""\
                """L'importo sarà azzerato.""" % bt.VALINT_INTEGERS
                aw.awu.MsgDialog(self, msg, "Valore errato", style=wx.ICON_ERROR)
                i = 0
            mov.importo = i
            if mov.costou and mov.qta:
                mov.costot = round(mov.qta*mov.costou, bt.VALINT_DECIMALS)

        if   col == m.RSMOV_codmov:
            mov.id_tipmov = value
            if "askvprec" in dir(mov._info):
                askvalori = mov.config.askvalori
                if askvalori != mov._info.askvprec:
                    if askvalori in "DQVT":
                        mov.prezzo  = 0
                        mov.sconto1 = mov.sconto2 = mov.sconto3 = mov.sconto4 = mov.sconto5 = mov.sconto6 = 0
                        if askvalori == "T":
                            mov.importo = 0
                        elif askvalori == "D":
                            mov.qta = 0
            if mov.config.tipologia == "I":
                mov.id_prod = None
            self.GridBodyDefAliqIva()

        elif col == m.RSMOV_DESCRIZ:
            mov.descriz = (value or '').replace('<CR>', '\n')
            resetview = True
            if mov.id_aliqiva is None:
                self.GridBodyDefAliqIva()
            #if mov.id_prod is None and mov.perpro is None:
                #mov.perpro = 0

        elif col == m.RSMOV_codiva:
            mov.id_aliqiva = value

        elif col == m.RSMOV_codart:
            if self.dbprod.Get(value):
                mov.id_prod = value
                doc.DefVarList()
                mov.descriz    = self.dbprod.descriz
                mov.um         = self.dbprod.um
                #########################################################
                # per ALGOR
                if 'ALGOR' in Env.Azienda.descrizione:
                    prezzo1 = prezzo2 = prezzo3 = 0
                    list = self.dbdoc._info.dblist
                    list.ClearFilters()
                    list.AddFilter("id_prod=%s", self.dbdoc.mov.id_prod)
                    if bt.MAGDATLIS:
                        list.AddFilter("data<=%s", self.dbdoc.datreg)
                    if list.Retrieve() and list.RowsCount()>0:
                        prezzo1 = list.__getattr__("prezzo1") or 0                    
                        prezzo2 = list.__getattr__("prezzo2") or 0                    
                        prezzo3 = list.__getattr__("prezzo3") or 0                    
                    mov.prezzo1 = prezzo1
                    mov.prezzo2 = prezzo2
                    mov.prezzo3 = prezzo3
                
                if mov.config.askvalori == 'T':
                    p, s1, s2, s3, s4, s5, s6 = self.GridBodyDefPrezzoSconti6()
                    mov.prezzo = p
                    mov.sconto1 = s1 or 0
                    mov.sconto2 = s2 or 0
                    mov.sconto3 = s3 or 0
                    mov.sconto4 = s4 or 0
                    mov.sconto5 = s5 or 0
                    mov.sconto6 = s6 or 0
                    mov.sconto1 = self.GridBodyDefSconto(1, mov)
                    mov.sconto2 = self.GridBodyDefSconto(2, mov)
                    mov.sconto3 = self.GridBodyDefSconto(3, mov)
                    mov.sconto4 = self.GridBodyDefSconto(4, mov)
                    mov.sconto5 = self.GridBodyDefSconto(5, mov)
                    mov.sconto6 = self.GridBodyDefSconto(6, mov)
                    if 'ALGOR' in Env.Azienda.descrizione:
                        if mov.config.tipologia=='O':
                            mov.sconto1 = mov.sconto2 = mov.sconto3 = mov.sconto4 = mov.sconto5 = mov.sconto6 = 0
                    
                    if bt.MAGPZCONF:
                        mov.pzconf = mov.prod.pzconf
                        if bt.MAGPZGRIP:
                            #determinazione pezzi per confezione da griglia
                            grip = self.dbdoc._info.dbgrip
                            grip.ClearFilters()
                            grip.AddFilter("id_pdc=%s", doc.id_pdc)
                            grip.AddFilter("id_prod=%s", mov.id_prod)
                            grip.AddFilter("data<=%s", doc.datreg)
                            if grip.Retrieve() and grip.RowsCount()>0:
                                if grip.pzconf:
                                    mov.pzconf = grip.pzconf
                    mov.costou = self.dbprod.costo
                    if bt.MAGPROVMOV == "E":
                        prio = []
                        for _prio in (bt.MAGPROVSEQ or ""):
                            try:
                                if _prio == "P":
                                    #prodotto
                                    prio.append(self.dbprod.perpro or None)
                                if _prio == "C":
                                    #prodotto
                                    prio.append(getattr(self.dbanag, 'perpro', None) or None)
                            except:
                                pass
                        for n in range(len(prio)):
                            mov.perpro = prio[n]
                            if mov.perpro:
                                break
                    else:
                        if self.dbprod.perpro:
                            mov.perpro = self.dbprod.perpro
                    DefImporto()
                elif mov.config.askvalori == 'V':
                    mov.importo, _, _, _, _, _, _ = self.GridBodyDefPrezzoSconti6()
                self.GridBodyDefAliqIva()
                #ElapsedTime('', reset = True)
                self.UpdateProdZone(value)
                #ElapsedTime('self.UpdateProdZone(value)')
                if self.dbdoc.config.autoqtaonbc == 1:
                    c = self.gridbody.GetCellEditor(row,gridcol)._tc
                    if c.barcode_readed:
                        self.AssegnaQta(mov, row, gridcol)
                        #=======================================================
                        # mov.qta = 1
                        # ElapsedTime('', reset = True)
                        # DefImporto()
                        # ElapsedTime('DefImporto()')
                        # self._rowcol = (row+1, gridcol)
                        #=======================================================
            if self.dbdoc.config.colcg == 'X':
                if mov.prod.id_pdcven:
                    mov.id_pdccg = mov.prod.id_pdcven
                elif mov.prod.catart.id_pdcven:
                    mov.id_pdccg = mov.prod.catart.id_pdcven

        elif col == m.RSMOV_PZCONF:
            mov.pzconf = value
            mov.qta = round(mov.pzconf*mov.nmconf, bt.MAGQTA_DECIMALS)
            DefImporto()

        elif col == m.RSMOV_NMCONF:
            mov.nmconf = value
            mov.qta = round(mov.pzconf*mov.nmconf, bt.MAGQTA_DECIMALS)
            DefImporto()
            resetview = True

        elif col in (m.RSMOV_QTA, m.RSMOV_PREZZO,\
                     m.RSMOV_SC1, m.RSMOV_SC2, m.RSMOV_SC3, m.RSMOV_SC4, m.RSMOV_SC5, m.RSMOV_SC6):
            DefImporto()
            resetview = True

        elif hasattr(self, 'COL_codlist') and col == m.RSMOV_codlis:
            mov.id_tiplist = value
            if value is not None:
                mov.prezzo, _, _, _, _, _, _, _ = doc.DefPrezzoSconti6(force_tiplist=value)
                DefImporto()

        elif col == m.RSMOV_IMPORTO:
            if value:
                if mov.config.modimpricalc == "P":
                    #da configurazione movimento, devo ricalcolare il prezzo
                    if mov.qta:
                        mov.prezzo = value/(mov.qta\
                                            *(100-(mov.sconto1 or 0))/100\
                                            *(100-(mov.sconto2 or 0))/100\
                                            *(100-(mov.sconto3 or 0))/100\
                                            *(100-(mov.sconto4 or 0))/100\
                                            *(100-(mov.sconto5 or 0))/100\
                                            *(100-(mov.sconto6 or 0))/100)
                elif mov.config.modimpricalc == "Q":
                    #da configurazione movimento, devo ricalcolare la quantità
                    if mov.prezzo:
                        mov.qta = value/(mov.prezzo\
                                         *(100-(mov.sconto1 or 0))/100\
                                         *(100-(mov.sconto2 or 0))/100\
                                         *(100-(mov.sconto3 or 0))/100\
                                         *(100-(mov.sconto4 or 0))/100\
                                         *(100-(mov.sconto5 or 0))/100\
                                         *(100-(mov.sconto6 or 0))/100)
                else:
                    #da configurazione movimento, devo ricalcolare lo sconto
                    if mov.qta and mov.prezzo:
                        s = round(100-value*100/(mov.qta*mov.prezzo), 2)
                        if s >= 1000:
                            err =\
                            """Il valore dello sconto è troppo grande (%.2f) e sarà azzerato.\n"""
                        elif s <= -1000:
                            err =\
                            """Il valore dello sconto è troppo piccolo (%.2f) e sarà azzerato.\n"""
                        else:
                            err = None
                        if err:
                            err +=\
                            """Controllare l'esattezza dell'importo digitato,eventualmente\n"""\
                            """correggere il prezzo o la quantità"""
                            s = 0
                        mov.sconto1 = s
                        mov.sconto2 = mov.sconto3 = mov.sconto4 = mov.sconto5 = mov.sconto6 = 0
                resetview = True
            mov.importo = value

        elif col == m.RSMOV_COSTOU:
            mov.costou = value
            if value and mov.qta:
                mov.costot = round(mov.qta*value, bt.VALINT_DECIMALS)
                resetview = True

        elif col == m.RSMOV_COSTOT:
            mov.costot = value
            if value and mov.qta:
                mov.costou = round(mov.costot/mov.qta, bt.MAGPRE_DECIMALS)
                resetview = True

        elif col == -m.RSMOV_PERPRO:
            mov.perpro = value
            resetview = True

        elif col == m.RSMOV_PDCCG_cod:
            mov.id_pdccg = value
            resetview = True

        else:
            if col < len(self.dbdoc.mov.GetFieldNames()):
                setattr(self.dbdoc.mov, self.dbdoc.mov.GetFieldNames()[col], value)

        #--------------------------------------------- Ricalcola ricarica
        ElapsedTime('', reset = True)
        wx.CallAfter(self.UpdateProdZonePRic)
        #self.UpdateProdZonePRic()
        ElapsedTime('self.UpdateProdZonePRic()')
        #--------------------------------------------- Ricalcola ricarica

        ElapsedTime('', reset = True)
        #self.MakeTotals(pesocolli=True)
        wx.CallAfter(self.MakeTotalPesoColli)
        ElapsedTime('self.MakeTotals(pesocolli=True)')

        if mov.config.tipologia == "P":
            resetview = True

        if resetview:
            self.gridbody.ResetView()

        return True

    def AssegnaQta(self, mov, row, gridcol):
        def DefImporto():
            i = round((mov.qta or 0)*(mov.prezzo or 0)\
                      *(100-(mov.sconto1 or 0))/100\
                      *(100-(mov.sconto2 or 0))/100\
                      *(100-(mov.sconto3 or 0))/100\
                      *(100-(mov.sconto4 or 0))/100\
                      *(100-(mov.sconto5 or 0))/100\
                      *(100-(mov.sconto6 or 0))/100, bt.VALINT_DECIMALS)
            if len(str(abs(int(i)))) > bt.VALINT_INTEGERS:
                msg =\
                """Il valore dell'importo è troppo elevato,\n"""\
                """sono permesse al massimo %d cifre intere.\n"""\
                """L'importo sarà azzerato.""" % bt.VALINT_INTEGERS
                aw.awu.MsgDialog(self, msg, "Valore errato", style=wx.ICON_ERROR)
                i = 0
            mov.importo = i
            if mov.costou and mov.qta:
                mov.costot = round(mov.qta*mov.costou, bt.VALINT_DECIMALS)
        
        print 'AssegnaQta id=%s numRow=%s' % (mov.id_prod, row)
        mov.qta = 1
        ElapsedTime('', reset = True)
        DefImporto()
        ElapsedTime('DefImporto()')
        self._rowcol = (row+1, gridcol)        
        
        
        

    def MakeTotalPesoColli(self):
        self.MakeTotals(pesocolli=True)

    def GridBodyDefSconto(self, numsc, mov):
        sconto, tipo = self.dbdoc.DefSconto(numsc, mov)
        return sconto

    def GridBodyDefPrezzoSconti(self, sconti6=False):

        if sconti6:
            prezzo, tipo, sc1, sc2, sc3, sc4, sc5, sc6 = self.dbdoc.DefPrezzoSconti6()
            return prezzo, sc1, sc2, sc3, sc4, sc5, sc6

        prezzo, tipo, sc1, sc2, sc3 = self.dbdoc.DefPrezzoSconti()
        return prezzo, sc1, sc2, sc3

    def GridBodyDefPrezzoSconti6(self):
        return self.GridBodyDefPrezzoSconti(sconti6=True)

    def GridBodyDefAliqIva(self):
        doc = self.dbdoc
        mov = doc.mov
        tiprig = mov.config.tipologia
        if tiprig == "I":
            #righe sconto ripartito - no aliquota
            idaliq = None
        elif tiprig == "E":
            #righe sconto merce - aliquota da automatismi magazzino
            idaliq = self._auto_magivascm
        elif tiprig == "D":
            idaliq = None
        else:
            if doc.id_aliqiva is not None:
                idaliq = doc.id_aliqiva
            else:
                try:
                    idaliq = self.dbanag.id_aliqiva
                except:
                    idaliq = None
            if bt.MAGIVAPREVA or False:
                print (bt.MAGIVAPREVA or False), mov.prod.codice, mov.prod.descriz, mov.prod.id_aliqiva
                if idaliq in self.esenti and mov.prod.id_aliqiva in self.esenti:
                    idaliq = mov.prod.id_aliqiva
                
        if idaliq is None and not (tiprig or ' ') in "DI":
            idaliq = mov.prod.id_aliqiva
            if idaliq is None and hasattr(self, '_auto_magivadef'):
                idaliq = self._auto_magivadef
            if self.dbanag.splitpay==1:
                self.dbaliq.Get(idaliq)
                if self.dbaliq.id_split:
                    idaliq = self.dbaliq.id_split
        mov.id_aliqiva = idaliq

    def GridBodyIsRowOK(self):
        valok = True
        mov = self.dbdoc.mov
        if mov.config.id is None:
            valok = False
        elif mov.config.askvalori is None:
            valok = False
        if mov.config.askvalori != "D" and (mov.descriz is None or len(mov.descriz.strip())) == 0:
            valok = False
        elif mov.config.askvalori in "QT" and (mov.qta == 0 or mov.qta is None):
            valok = False
        elif mov.config.askvalori == "T" and (mov.prezzo == 0 or mov.prezzo is None) and mov.config.canprezzo0 != 1:
            valok = False
        elif mov.config.askvalori in "TV" and (mov.importo == 0 or mov.importo is None) and mov.config.canprezzo0 != 1:
            valok = False
        elif mov.config.askvalori in "TQV" and mov.id_aliqiva is None\
           and not mov.config.tipologia in "IP":
            valok = False
        elif mov.config.proobb and mov.id_prod is None and mov.perpro is None:
            valok = False
        return valok

    def GridBodyAddNewRow(self, before_row=None):
        if self.status != m.STATUS_EDITING:
            #workaround: quando ho inserito una fattura e cerco di inserire un
            #ddt, appenda confermo il numero doc. da inserire, viene richiamato
            #EndEdit della colonna tipmov (non ho idea del perché e da chi)
            return False
        doc = self.dbdoc
        mov = doc.mov
        mov.MoveNewRow()
        mov.AppendNewRow()
        mov.numriga = mov.RowsCount()
        map(mov._ResetTableVar, 'descriz um note qta prezzo sconto1 sconto2 sconto3 sconto4 sconto5 sconto6 importo'.split())
        mov.perpro = None
        mov.agggrip = int((bt.MAGATTGRIP or bt.MAGATTGRIF) and bt.MAGAGGGRIP and bt.MAGALWGRIP)
        if self.lastmovid is not None:
            mov.id_tipmov = self.lastmovid

        if before_row is not None:
            rsb = mov.GetRecordset()
            r = rsb.pop()
            rsb.insert(before_row, r)
            for n, mov in enumerate(mov):
                mov.numriga = n+1
        if bt.MAGROWLIS:
            doc.DefVarList()
        self.UpdateBodyButtons()
        return True

    def GridBodyOnSelected(self, event):
        row, col = event.GetRow(), event.GetCol()
        self.UpdateBodyButtons(row)
        doc = self.dbdoc
        if row < doc.mov.RowsCount():
            doc.mov.MoveRow(row)
            proid = doc.mov.id_prod
            dsw = doc.mov.config.lendescriz or 60
            self.gridbody.SetColMaxChar(m.RSMOV_DESCRIZ, dsw)
        else:
            proid = None
        self.UpdateProdZone(proid)
        event.Skip()

    def GridBodySetTipMovFilter(self):
        editor = self.gridbody.GetCellEditor(0, self.COL_codmov)
        assert isinstance(editor, dbgred.DataLinkCellEditor),\
               "L'editor della colonna tipo movimento non è DataLinkCellEditor"
        do = True
        if editor._tc:
            if editor._tc.IsShown():
                do = False
        if do:
            lt = editor._tc
            editor.lt_filter = "id_tipdoc=%s" % self.cauid
            if lt:
                lt.SetFilter(editor.lt_filter)

    def UpdateProdZonePRic(self):
        def cn(x): return self.FindWindowByName(x)
#        def ci(x): return self.FindWindowById(x)
        cfg = self.dbdoc.cfgdoc
        if cfg.visgiac or cfg.viscosto:
            bprc = 0
            cstu = self.dbprod.costo or 0
            qt   = self.dbdoc.mov.qta or 0
            pv   = self.dbdoc.mov.prezzo or 0
            im   = self.dbdoc.mov.importo or 0
            sc   = self.dbdoc.cfgdoc.scorpiva
            iv   = self.dbdoc.mov.iva.perciva
            if im>0 and qt>0:
                try:
                    pv = round(im/qt, 2)
                except ZeroDivisionError:
                    pv = 0
            if pv>0 and cstu>0:
                try:
                    if sc == 1 or sc=='1':
                        try:
                            cstu = cstu + (cstu * iv /100)
                        except:
                            pass
                    bprc = round((pv/cstu)*100, 2) - 100
                except ZeroDivisionError:
                    bprc = 0
            cn('bodypric').SetValue(bprc)
#            ci('ID_BODYPRIC').SetValue(bprc)


    def UpdateProdZone(self, idpro):
        if idpro == self.lastprod:
            return
        def cn(x): return self.FindWindowByName(x)
        def ci(x): return self.FindWindowById(x)
        cfg = self.dbdoc.cfgdoc
        if cfg.visgiac or cfg.viscosto:
            magid = cn('id_magazz').GetValue()
#            giac = cstu = cstm = 0
            giac = cstu = cstm = bprc = 0
            #aggiorno giacenza
            if not idpro in self._cache_giacenze:
                inv = self.dbinv
                inv.SetMagazz(magid)
                inv.Get(idpro)
                giac = inv.total_giac
                cstu = inv.costo or 0
                if cstu==0 and idpro:
                    # Calcolo Costo Ultimo
                    dbProd = self.dbprod
                    dbProd.Get(idpro)
                    cstu = dbProd.costo or 0
                vc = (inv.total_iniv or 0) + (inv.total_carv or 0)
                cv = (inv.total_ini or 0) + (inv.total_car or 0)
                try:
                    cstm = round(vc/cv, bt.MAGPRE_DECIMALS)
                except ZeroDivisionError:
                    cstm = 0
                self._cache_giacenze[idpro] = (giac, cstu, cstm)
            giac, cstu, cstm = self._cache_giacenze[idpro]
            
            #aggiorno dati prodotto
            pro = self.dbprod
            if pro.id != idpro:
                ElapsedTime('', reset=True)
                pro.Get(idpro)
                ElapsedTime('UpdateProdZone - pro.Get(idpro)')
                
                
                
                
                


            ElapsedTime('', reset=True)
            for c in aw.awu.GetAllChildrens(ci(wdr.ID_BODYSTATZONE)):
                name = c.GetName()
                if name is not None:
                    if name.startswith('datiprod_'):
                        name = name[9:]
                        if name in pro.GetFieldNames():
                            #print name
                            c.SetValue(getattr(pro, name))
            ElapsedTime('Assegna valori')
            for name, val, cond in (('bodygiac', giac, cfg.visgiac),
                                    ('bodycost', cstu, cfg.viscosto),
                                    ('bodycstm', cstm, cfg.viscosto)):
                if cond:
                    cn(name).SetValue(val)
#            #--------------------------------------------- Ricalcola ricarica
            self.UpdateProdZonePRic()
#            #--------------------------------------------- Ricalcola ricarica
        if cfg.vislistini:
            #aggiorno listini del prodotto
            self.gridlist.Update(idpro)
        if cfg.visultmov:
            #aggiorno storico movimenti pdc/prod
            ElapsedTime('', reset=True)
            idpdc = self.dbdoc.id_pdc
            wx.CallAfter(self.gridmovi.UpdateGrid, idpdc, idpro)
            #self.gridmovi.UpdateGrid(idpdc, idpro)
            ElapsedTime('self.gridmovi.UpdateGrid(idpdc, idpro)')
        self.lastprod = idpro

    def UpdateBodyButtons(self, row=None):
        disable = True
        if row is None:
            sr = self.gridbody.GetSelectedRows()
            if sr:
                row = sr[-1]
        if row is not None:
            mov = self.dbdoc.mov
            if 0 <= row < mov.RowsCount():
                mov.MoveRow(row)
                enable = self.status == m.STATUS_EDITING
                self.controls["butnewrow"].Enable(enable)
                self.controls["butdelrow"].Enable(enable)
                disable = False
        if disable:
            self.controls["butnewrow"].Enable(False)
            self.controls["butdelrow"].Enable(False)


    def SetFirstTipMov(self):
        if self.default_tipmov or False:
            if self.dbdoc.mov.RowsCount()==0:
                try:
                    self.GridBodyAddNewRow(before_row=0)
                    #self.dbdoc.mov.id = self.default_tipmov
                    idxCodMov=self.dbdoc.mov.config._GetFieldIndex("codice", inline=True)
                    self.GridBodyEditingValues(0, 1, idxCodMov, self.default_tipmov)
                    self.GridBodyEditedValues(0, 1, idxCodMov, self.default_tipmov)
                    self.gridbody.ChangeData(self.gridbody.GetTable().data)
                    self.lastmovid = self.default_tipmov
                    self.gridbody.SetGridCursor(0, 1)
                except:
                    pass


    def GridBodyOnAdd(self, event):
        try:
            br = self.gridbody.GetGridCursorRow()
            col = self.gridbody.GetGridCursorCol()
            br = self.dbdoc.mov.RowsCount()
            if br==0:
                if self.default_tipmov:
                    self.GridBodyAddNewRow(before_row=br)
                    #self.dbdoc.mov.id = self.default_tipmov
                    idxCodMov=self.dbdoc.mov.config._GetFieldIndex("codice", inline=True)
                    self.GridBodyEditingValues(br, 1, idxCodMov, self.default_tipmov)
                    self.GridBodyEditedValues(br, 1, idxCodMov, self.default_tipmov)
                    self.gridbody.ChangeData(self.gridbody.GetTable().data)
                    self.lastmovid = self.default_tipmov

            self.gridbody.ResetView()
            self.gridbody.SetGridCursor(br, 1)#self.dbdoc.mov.RowsCount()-1,0)
            self.GridBodyIsRowOK()
            self.gridbody.SetFocus()
            self.FocusGained()

        except:
            pass

    def GridBodyOnCreate(self, event):
        br = self.gridbody.GetGridCursorRow()
        col = self.gridbody.GetGridCursorCol()
        if br >= self.dbdoc.mov.RowsCount():
            br = self.dbdoc.mov.RowsCount()-1
        self.GridBodyAddNewRow(before_row=br)
        self.gridbody.ResetView()
        self.gridbody.SetGridCursor(br, col)#self.dbdoc.mov.RowsCount()-1,0)
        self.gridbody.SetFocus()

    def GridBodyOnDelete(self, event):
        sr = self.gridbody.GetSelectedRows()
        if sr:
            row = sr[-1]
            mov = self.dbdoc.mov
            if 0 <= row < mov.RowsCount():
                mov.MoveRow(row)
                if mov.id is not None:
                    if not mov.id in mov._info.deletedRecords:
                        #riga già esistente, marco per cancellazione da db
                        mov._info.deletedRecords.append(mov.id)
                #elimino riga da dbgrid
                self.gridbody.DeleteRows(row)
                mov._info.recordCount -= 1
                if mov._info.recordNumber >= mov._info.recordCount:
                    mov._info.recordNumber -= 1
                    mov._UpdateTableVars()
                #after deletion, record cursor is on the following one
                #so for iterations we decrement iteration index and count
                mov._info.iterIndex -= 1
                mov._info.iterCount -= 1
                self.gridbody.Refresh()
                self.SetDataChanged()
                self.MakeTotals()
                self.UpdateBodyButtons()
        event.Skip()


    def GridBodyOnMulti(self, event):
        if self.dbdoc.cfgdoc.multilinee==1:
            self.ShowMultiLineDialog()        
        event.Skip()


    def UpdatePanelBody(self):
        #if self.gridbody is not None:
            #self.gridbody.ResetView()
            #self.gridbody.AutoSizeColumns()
        ##self.UpdateTotDav()
        pass




class MultiLineDialog(aw.Dialog):
    ReturnValue = None

    def __init__(self, *args, **kwargs):

        cfgdoc = self.dbpdt = kwargs.pop('cfgdoc')
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Multilinea"
        aw.Dialog.__init__(self, *args, **kwargs)

        self.panel = MultiLinePanel(self, cfgdoc=cfgdoc)
        self.AddSizedPanel(self.panel)
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.CenterOnScreen()


        cn = self.FindWindowByName
        self.btnAbort     = cn('btnAbort')
        self.btnAbort.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_CLOSE, self.OnQuit, id=self.Id)

        self.InitReturnValue()



    def InitReturnValue(self):
        self.ReturnValue = {}
        self.ReturnValue['esito']= False
        self.ReturnValue['testo']= []
        self.ReturnValue['idTipMov'] = 0



    def OnQuit(self, event):
        event.Skip()

    def OnClose(self, event):
        self.InitReturnValue()
        self.Close()
        event.Skip()

class MultiLinePanel(aw.Panel):
    elab=None
    cfgdoc = None
    def __init__(self, *args, **kwargs):
        self.cfgdoc = self.dbpdt = kwargs.pop('cfgdoc')
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.MultiLineFunc(self)
        cn = self.FindWindowByName
        self.selectedTesto= cn('selectedTesto')
        self.testo        = cn('testo')

        self.dbTesti= dbm.Testi()
        self.LoadTesti()
        msg = u''
        self.testo.SetValue(msg)
        self.btnConfirm   = cn('btnConfirm')
        self.btnConfirm.Bind(wx.EVT_BUTTON, self.OnConfirm)
        self.selectedTesto.Bind(wx.EVT_COMBOBOX, self.OnSelectTesto)
        
    def LoadTesti(self):
        self.selectedTesto.Clear()
        self.dbTesti.Retrieve()
        for r in self.dbTesti:
            self.selectedTesto.Append(r.descriz)

    def OnSelectTesto(self, evt):
        item = self.selectedTesto.GetValue()
        self.dbTesti.Retrieve('descriz="%s"' % item)
        if self.dbTesti.OneRow():
            self.testo.SetValue(self.dbTesti.testo)
        evt.Skip()

    def OnConfirm(self, evt):
        #=======================================================================
        # outTxt = self.TestoInRighe()
        # for i, r in enumerate(outTxt):
        #     print i,r
        # 
        # print '-'*60
        #=======================================================================
        txt = self.testo.GetValue()
        fontName=self.cfgdoc.font     
        fontSize=self.cfgdoc.fontsize 
        fieldLen=self.cfgdoc.dessize
        ml = MultiLineDescriz(txt, fontName, fontSize, fieldLen)
        outTxt=ml.GetLines()
        for i, r in enumerate(outTxt):
            print i,r
        
        self.Parent.ReturnValue['esito']= True
        self.Parent.ReturnValue['testo']= outTxt
        idMov = self.GetIdTipMov()
        if not idMov==0:
            self.Parent.ReturnValue['idTipMov'] = idMov
            self.Parent.Close()
        else:
            aw.awu.MsgDialog(self, 'Impossibile procedere\nDefinire il tipo movimento descrittivo per il documento %s' % self.cfgdoc.descriz , style=wx.ICON_ERROR)
        evt.Skip()

    def GetIdTipMov(self):
        idFound=0
        for r in self.cfgdoc.tipmov:
            if r.tipologia=='D':
                idFound=r.id
                break
        return idFound

    def Validate(self, fontName, fontSize, fieldLen):
        lSuccess=True
        if len(fontName)==0:
            lSuccess=False
        elif fontSize <= 0:
            lSuccess=False
        elif fieldLen <= 0:
            lSuccess=False
        return lSuccess

    #===========================================================================
    # def TestoInRighe(self):
    #     outTxt=[]
    #     def GetLineLen(fontName, fontSize, fieldLen):
    #         testString='i'*fieldLen
    #         lContinue = True
    #         while (lContinue):
    #             if int(stringWidth(testString,fontName,fontSize)+0.99) > fieldLen:
    #                 testString = testString[:-1]
    #             else:
    #                 lContinue=False
    #         return len(testString)
    #     
    #     def SplitParagraph(p, fontName, fontSize, fieldLen):
    #         lRow=[]
    #         lWord = p.split(' ')
    #         newRow=''
    #         for j, word in enumerate(lWord):
    #             oldRow = newRow
    #             if len(newRow)==0: 
    #                 newRow = word
    #             else:
    #                 newRow = '%s %s' % (newRow, word)
    #             if int(stringWidth(newRow,fontName,fontSize)+0.99) > fieldLen:
    #                 lRow.append(oldRow)
    #                 newRow=word
    #         lRow.append(newRow)
    #         return lRow
    #     
    #     txt = self.testo.GetValue()
    #     fontName=self.cfgdoc.font     
    #     fontSize=self.cfgdoc.fontsize 
    #     fieldLen=self.cfgdoc.dessize
    #     
    #     if self.Validate(fontName, fontSize, fieldLen):
    #         lineLen=GetLineLen(fontName, fontSize, fieldLen)
    #         txt = txt.replace(chr(9), '   ')
    #         lParagraph = txt.split('\n')
    #         for i, p in enumerate(lParagraph):
    #             for r in SplitParagraph(p, fontName, fontSize, fieldLen):
    #                 outTxt.append(r)
    #         return outTxt
    #===========================================================================
        
class MultiLineDescriz():
    txt      = None
    fontName = None
    fontSize = None
    fieldLen = None
    
    def __init__(self, txt, fontName, fontSize, fieldLen):
        self.txt      = txt     
        self.fontName = fontName
        self.fontSize = fontSize
        self.fieldLen = fieldLen

    def Validate(self):
        lSuccess=True
        if len(self.fontName)==0:
            lSuccess=False
        elif self.fontSize <= 0:
            lSuccess=False
        elif self.fieldLen <= 0:
            lSuccess=False
        return lSuccess

    def GetLineLen(self):
        testString='i'*self.fieldLen
        lContinue = True
        while (lContinue):
            if int(stringWidth(testString,self.fontName,self.fontSize)+0.99) > self.fieldLen:
                testString = testString[:-1]
            else:
                lContinue=False
        return len(testString)
    

    def SplitParagraph(self, p):
        lRow=[]
        lWord = p.split(' ')
        newRow=''
        for j, word in enumerate(lWord):
            oldRow = newRow
            if len(newRow)==0: 
                newRow = word
            else:
                newRow = '%s %s' % (newRow, word)
            if int(stringWidth(newRow, self.fontName, self.fontSize)+0.99) > self.fieldLen:
                lRow.append(oldRow)
                newRow=word
        lRow.append(newRow)
        return lRow
    
    def GetLines(self):
        outTxt=[]
        txt = self.txt
        if self.Validate():
            txt = txt.replace(chr(9), '   ')
            lParagraph = txt.split('\n')
            for i, p in enumerate(lParagraph):
                for r in self.SplitParagraph(p):
                    outTxt.append(r)
        return outTxt
