#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/docint.py
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
import awc.controls.windows as aw
from awc.controls.linktable import EVT_LINKTABCHANGED

import magazz.docint_wdr as wdr

import magazz
import magazz.dbtables as dbm

import report as rpt

import Env
bt = Env.Azienda.BaseTab


FRAME_TITLE = "Interrogazione documenti magazzino"


class _DocIntGridMixin(object):

    def __init__(self):
        assert isinstance(self, dbglib.DbGrid)
        object.__init__(self)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc)

    def OnCallDoc(self, event):
        assert isinstance(self, dbglib.DbGrid)
        row = event.GetRow()
        dbdoc = self.dbdoc
        if 0 <= row < dbdoc.RowsCount():
            dbdoc.MoveRow(row)
            if magazz.CheckPermUte(dbdoc.id_tipdoc, 'leggi'):
                wx.BeginBusyCursor()
                try:
                    Dialog = magazz.GetDataentryDialogClass()
                    dlg = Dialog(aw.awu.GetParentFrame(self))
                    dlg.SetOneDocOnly(dbdoc.id)
                    dlg.CenterOnScreen()
                finally:
                    wx.EndBusyCursor()
                r = dlg.ShowModal()
                if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                    self.UpdateGrid()
                    if r == magazz.DOC_MODIFIED:
                        wx.CallAfter(lambda: self.SelectRow(row))
                dlg.Destroy()
        event.Skip()


# ------------------------------------------------------------------------------


class DocIntGrid(dbglib.DbGridColoriAlternati, _DocIntGridMixin):

    def __init__(self, parent, dlg, dbdoc, canedit=False, idGrid=None):

        dbglib.DbGridColoriAlternati.__init__(self, parent,
                                              size=parent.GetSize(),
                                              idGrid=idGrid)
        _DocIntGridMixin.__init__(self)
        self.dbdoc = dbdoc
        self.dlg = dlg

        self.totdef = ("totimponib",
                       "totimposta",
                       "totimporto",
                       "totmerce",
                       "totservi",
                       "totspese",
                       "tottrasp",
                       "totscrip",
                       "totscmce",
                       "totomagg")

        size = parent.GetClientSizeTuple()

        #cols=self.SetColumnsGrid()
        cols=self.GetDbColumns()
        
        self._cols=cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        #canedit = False
        canins = False

        rs = self.dbdoc.GetRecordset()

        self.SetData( rs, colmap, canedit, canins)
        self.GetTable().dbdoc = self.dbdoc

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.SetAnchorColumns(10, 6)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


    def GetDbColumns(self):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        doc = self.dbdoc
        spe = doc.speinc
        mag = doc.magazz
        tpd = doc.tipdoc
        pdc = doc.pdc
        mpa = doc.modpag
        age = doc.agente

        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()

        cols = (\
            ( 40, (cn(mag,"codice"),     "Mag.",          _STR, True)),
            ( 80, (cn(doc,"datreg"),     "Data reg.",     _DAT, True)),
            (120, (cn(tpd,"descriz"),    "Documento",     _STR, True)),
            ( 50, (cn(doc,"numdoc"),     "Num.",          _STR, True)),
            ( 80, (cn(doc,"datdoc"),     "Data doc.",     _DAT, True)),
            ( 50, (cn(pdc,"codice"),     "Cod.",          _STR, True)),
            (290, (cn(pdc,"descriz"),    "Sottoconto",    _STR, True)),
            ( 35, (cn(mpa,"codice"),     "Mp",            _STR, True)),
            (120, (cn(mpa,"descriz"),    "Mod.Pagamento", _STR, True)),
            ( 35, (cn(spe,"codice"),     "Spese",         _STR, True)),
            (110, (cn(doc,"totimporto"), "Tot.Documento", _IMP, True)),
            (110, (cn(doc,"totimponib"), "Imponibile",    _IMP, True)),
            (110, (cn(doc,"totimposta"), "Imposta",       _IMP, True)),
            (120, (cn(doc,"desrif"),     "Riferimento",   _STR, True)),
            ( 80, (cn(doc,"datrif"),     "Data rif.",     _DAT, True)),
            ( 50, (cn(doc,"numrif"),     "N.Rif.",        _STR, True)),
            ( 35, (cn(age,"codice"),     "Cod.",          _STR, True)),
            (120, (cn(age,"descriz"),    "Agente",        _STR, True)),
            ( 30, (cn(doc,"f_printed"),  "St.",           _CHK, True)),
            ( 30, (cn(doc,"f_emailed"),  "Em.",           _CHK, True)),
            ( 30, (cn(doc,"f_ann"),      "Ann",           _CHK, True)),
            ( 30, (cn(doc,"f_acq"),      "Acq",           _CHK, True)),
            (  1, (cn(doc,"id"),         "#doc",          _STR, True)),
            (  1, (cn(doc,"id_reg"),     "#reg",          _STR, True)),
        )

        return cols

    def UpdateGrid(self):

        doc = self.dbdoc

        wx.BeginBusyCursor()

        try:

            wait = aw.awu.WaitDialog(self.dlg, dataread=True)
            doc.Retrieve()
            wait.Destroy()

            self.ChangeData(doc.GetRecordset())
            self.AutoSizeColumns()

            def ProgrUpdate(doc, row):
                pass
    #            wait.SetValue(row)

            totals = doc.GetTotalOf([(doc, tot) for tot in self.totdef],
                                    ProgrUpdate)

            cn = lambda x: self.dlg.FindWindowByName(x)

            cn("totnumdoc").SetValue(self.dbdoc.RowsCount())
            for n, name in enumerate(self.totdef):
                try:
                    cn(name).SetValue(totals[n])
                except AttributeError:
                    pass

        finally:
            wx.EndBusyCursor()

    def GridDocOnUpdateFilters(self, event):

        doc = self.dbdoc
        doc.ClearFilters()

        cn = self.dlg.FindWindowByName

        for tab, name in (("doc", "id_magazz"),\
                          ("doc", "id_pdc"),\
                          ("doc", "id_dest"),\
                          ("doc", "id_agente"),\
                          ("doc", "id_zona")):
            ctr = cn(name)
            val = ctr.GetValue()
            if val is not None:
                doc.AddFilter("%s.%s=%%s" % (tab, name), val)

        doc.ClearOrders()
        doc.AddOrder('doc.datreg')
        doc.AddOrder('tipdoc.codice')
        doc.AddOrder('doc.datdoc')
        doc.AddOrder('doc.numdoc')

        td = cn('id_tipdoc').GetValue()
        if td:
            try:
                df = cn('docfam').IsChecked()
            except:
                df = False
            if df:
                doc.AddFilter('tipdoc.docfam=%s', df)
                doc.ClearOrders()
                doc.AddOrder('doc.datreg')
                doc.AddOrder('tipdoc.docfam')
                doc.AddOrder('doc.datdoc')
                doc.AddOrder('doc.numdoc')
            else:
                doc.AddFilter('doc.id_tipdoc=%s', td)

        for name in ("num", "dat"):
            for tipo in ("doc", "reg", "rif"):
                for estr in '12':
                    if estr == '1': oper = ">="
                    else:           oper = "<="
                    field = "mas%s%s%s" % (name, tipo, estr)
                    ctr = self.dlg.FindWindowByName(field)
                    val = ctr.GetValue()
                    if val:
                        field = "doc.%s%s" % (name, tipo)
                        doc.AddFilter("%s%s%%s" % (field, oper), val)

       #filtro descrizione riferimento
        d = cn('masdesrif')
        if d:
            val = d.GetValue()
            if val:
                val = '%%%s%%' % val.replace('..', r'%')
                if bt.OPTSPASEARCH:
                    val = val.replace(' ', r'%')
                doc.AddFilter('doc.desrif LIKE %s', val)

        for name in 'ann acq'.split():
            val = cn('nodoc%s' % name).IsChecked()
            if val:
                doc.AddFilter("(doc.f_%s IS NULL OR doc.f_%s<>1)" % (name, name))

        self.UpdateGrid()

    def GridDocOnResetFilters(self):
        self.dbdoc.ClearFilters()
        self.UpdateGrid()

    def GridDocOnPrint(self, event):
        self.Print()
        event.Skip()

    def Print(self):
        rpt.Report(self, self.dbdoc, "Lista documenti magazzino",
                   filtersPanel=aw.awu.GetParentFrame(self).FindWindowByName('panelsel'))


# ------------------------------------------------------------------------------


class DocIntPanel(aw.Panel):

    def __init__(self, *args, **kwargs):

        aw.Panel.__init__(self, *args, **kwargs)
        #=======================================================================
        # self.dbdoc = dbm.ElencoDocum()
        # self.dbtpd = dbm.adb.DbTable(bt.TABNAME_CFGMAGDOC, 'tipdoc')
        #=======================================================================
        self.SetData()
        self.LoadWdr()
        #wdr.DocMagFunc(self)
        cn = self.FindWindowByName
        pp = self.FindWindowById(wdr.ID_PANGRIDDOC)
        self.griddoc = DocIntGrid(pp, self, self.dbdoc, idGrid='intdocmag')
        self.Bind(EVT_LINKTABCHANGED, self.OnDocChanged, cn('id_tipdoc'))
        for cid, func in ((wdr.ID_MASBUTUPD, self.griddoc.GridDocOnUpdateFilters),
                          (wdr.ID_MASBUTPRT, self.griddoc.GridDocOnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)

    def LoadWdr(self):
        wdr.DocMagFunc(self)
        

    def SetData(self):
        self.dbdoc = dbm.ElencoDocum()
        self.dbtpd = dbm.adb.DbTable(bt.TABNAME_CFGMAGDOC, 'tipdoc')

    def OnDocChanged(self, event):
        cn = self.FindWindowByName
        td = cn('id_tipdoc')
        c = None
        ta = td.dbdoc.tipana.codice
        if ta:
            c = ta
        cn('id_pdc').SetPdcTipCods(c)
        self.EnableFields()
        event.Skip()

    def EnableFields(self):
        cn = self.FindWindowByName
        td = cn('id_tipdoc').dbdoc
        for col in 'agente zona'.split():
            c = cn('id_%s' % col)
            if td.id:
                f = getattr(td, 'ask%s' % col)
                if not f:
                    c.SetValue(None)
                c.Enable(f == "X")
            else:
                c.Enable()
        tpd = self.dbtpd
        tpd.Get(cn('id_tipdoc').GetValue())
        cn('docfam').Enable(bool(tpd.docfam))


    def GetPanelDataSource(self):
        return self.dbdoc

# ------------------------------------------------------------------------------


class DocIntFrame(aw.Frame):
    """
    Frame Interrogazione documenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(DocIntPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class DocIntDialog(aw.Dialog):
    """
    Dialog Interrogazione documenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(DocIntPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    import Env
    Env.InitSettings()
    db = dbm.adb.DB()
    db.Connect()
    win = DocIntDialog()
    win.Show()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
