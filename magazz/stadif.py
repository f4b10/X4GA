#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stadif.py
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


import magazz.dbftd as ftd
dbm = ftd.dbm
Env = dbm.Env
bt = dbm.bt
adb = dbm.adb
dt = dbm.mx.DateTime

import magazz.ftdif_wdr as wdr
import magazz.dataentry_wdr as dewdr

import report as rpt

stdcolor = dbm.Env.Azienda.Colours


FRAME_TITLE = "Stampa differita"


class DocsGrid(dbglib.DbGrid):
    """
    Griglia documenti estratti
    """
    def __init__(self, parent, dbdoc):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable documenti (derivati da magazz.dbtables.DocAll)
        """

        size = parent.GetClientSizeTuple()

        self.dbdoc = dbdoc
        doc = self.dbdoc
        mag = doc.magazz
        tpd = doc.config
        pdc = doc.pdc
        des = doc.dest

        cn = lambda db, col: db._GetFieldIndex(col, inline=True)

        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _FLT = bt.GetValIntMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":True,False"

        cols = (\
            ( 30, (cn(doc, 'dastampare'), "St.",           _CHK, True )),\
            ( 35, (cn(mag, 'codice'),     "Mag.",          _STR, True )),\
            ( 50, (cn(doc, 'numdoc'),     "Num.",          _NUM, True )),\
            ( 80, (cn(doc, 'datdoc'),     "Data Doc.",     _DAT, True )),\
            ( 80, (cn(doc, 'datreg'),     "Data reg.",     _DAT, True )),\
            ( 50, (cn(pdc, 'codice'),     "Cod.",          _STR, True )),\
            (190, (cn(pdc, 'descriz'),    "Anagrafica",    _STR, True )),\
            (100, (cn(doc, 'totimporto'), "Tot.Documento", _FLT, True )),\
            ( 40, (cn(des, 'codice'),     "Cod.",          _STR, True )),\
            (250, (cn(des, 'descriz'),    "Destinazione",  _STR, True )),\
            )

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False

        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)

        links = None

        afteredit = None
        self.SetData(self.dbdoc.GetRecordset(), colmap, canedit, canins,
                     links, afteredit)

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.SetAnchorColumns(7, 6)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        self.Bind(gl.EVT_GRID_CELL_LEFT_CLICK, self.OnDocSeleziona)

    def OnDocSeleziona(self, event):
        if event.GetCol() == 0:
            col = self.dbdoc._GetFieldIndex('dastampare', inline=True)
            row = event.GetRow()
            rs = self.dbdoc.GetRecordset()
            if row < len(rs):
                rs[row][col] = not rs[row][col]
                #self.ForceRefresh()
        event.Skip()


# ------------------------------------------------------------------------------


class StaDifPanel(aw.Panel):

    def __init__(self, *args, **kwargs):

        aw.Panel.__init__(self, *args, **kwargs)
        wdr.StaDifFunc(self)

        cn = self.FindWindowByName
        if not bt.MAGDEMSENDFLAG:
            cn('tipemail').Hide()
            cn('butemail').Hide()
            self.Fit()
            self.Layout()

        self.dbdocs = dbm.DocMag_Differiti()
        self.dbdocs._info.stampadiff = True
        self.dbdocs.ShowDialog(self)
        self.dbdocs.AddField('0.0', 'dastampare')
        self.dbdocs.Get(-1) #aggiorna i puntatori alle colonne dopo aggiunta col

        ci = lambda x: self.FindWindowById(x)
        self.gridocs = DocsGrid(ci(wdr.ID_PANGRID), self.dbdocs)

        ci(wdr.ID_YEAR).SetValue(Env.Azienda.Esercizio.dataElab.year)
        tpd = adb.DbTable(bt.TABNAME_CFGMAGDOC, 'tpd', writable=False)
        tpd.Retrieve('toolprint IS NOT NULL')
        ci(wdr.ID_TIPDOC).SetFilter('id IN (%s)' % ','.join([str(x.id)
                                                             for x in tpd]))

        for cid, func in ((wdr.ID_UPDATE, self.OnUpdate),
                          (wdr.ID_LISTA,  self.OnLista),
                          (wdr.ID_STAMPA, self.OnStampa),
                          (wdr.ID_EMAIL,  self.OnEmail),):
            self.Bind(wx.EVT_BUTTON, func, id=cid)

    def OnUpdate(self, event):
        self.Estrai()
        event.Skip()

    def OnLista(self, event):
        self.ListaDoc()
        event.Skip()

    def GetDocumenti(self):
        colid = self.dbdocs._GetFieldIndex('id')
        colds = self.dbdocs._GetFieldIndex('dastampare')
        docids = [str(drs[colid]) for drs in self.dbdocs._info.rs if drs[colds]]
        if not docids:
            aw.awu.MsgDialog(self, message="Nessun documento selezionato")
            return None
        if len(docids) == self.dbdocs.RowsCount():
            #tutti selezionati, lavoro su DocMag interno, della griglia
            docs = self.dbdocs
        else:
            #alcuni selezionai, lavoro su nuovo DocMag filtrato
            docs = dbm.DocMag()
            docs._info.stampadiff = True
            docs.AddFilter('doc.id IN (%s)' % ','.join(docids))
            if not docs.Retrieve():
                aw.awu.MsgDialog(self, message=repr(docs.GetError()))
                return None
        return docs

    def ListaDoc(self):
        self.Stampa("Liste di controllo Operazioni Differite",
                    "Lista documenti da stampare",
                    is_list=True)

    def Estrai(self):

        docs = self.dbdocs
        ci = self.FindWindowById
        cn = self.FindWindowByName

        td = ci(wdr.ID_TIPDOC).GetValue()
        if not docs.cfgdoc.Get(td):
            aw.awu.MsgDialog(self, repr(docs.GetError()))
            return
        if docs.cfgdoc.RowsCount() == 0:
            aw.awu.MsgDialog(self, "Impossibile determinare la configurazione del documento")
            return

        mg = cn('id_magazz').GetValue()
        te = cn('tipemail').GetValue()
        cn('butemail').Enable(te in 'CA')

        docs.ClearFilters()
        docs.AddFilter('doc.id_tipdoc=%s', td)
        if mg:
            docs.AddFilter('doc.id_magazz=%s', mg)
        docs.AddFilter('YEAR(doc.datreg)=%s', ci(wdr.ID_YEAR).GetValue())
        nd1, nd2 = [ci(x).GetValue() for x in (wdr.ID_NUMDOC1, wdr.ID_NUMDOC2)]
        if nd1: docs.AddFilter('doc.numdoc>=%s', nd1)
        if nd2: docs.AddFilter('doc.numdoc<=%s', nd2)

        # selezione per aliquota iva
        iv = cn('aliqiva').GetValue()
        if iv:
            fltIva=self.GetFilterByIva(td, iv, nd1, nd2, ci(wdr.ID_YEAR).GetValue())
            docs.AddFilter(fltIva)


        wx.BeginBusyCursor()
        wx.Yield()
        try:
            if docs.Retrieve():
                rs = docs._info.rs
                cpd = docs._GetFieldIndex('id_pdc')
                ces = docs._GetFieldIndex('f_emailed')
                col = docs._GetFieldIndex('dastampare')
                anag = docs.GetAnag()
                for row in range(docs.RowsCount()):
                    sel = True
                    if te in "CAS":
                        if anag.Get(rs[row][cpd]):
                            sel = bool(anag.docsemail)
                            if sel:
                                if te == "S":
                                    sel = not sel
                                elif te == "C":
                                    sel = not rs[row][ces] == 1
                            else:
                                if te == "S":
                                    sel = True
                    rs[row][col] = sel #seleziona tutti x default, o solo con/senza email
                self.gridocs.ChangeData(docs.GetRecordset())
            else:
                self.gridocs.ChangeData(())
                aw.awu.MsgDialog(self, message=repr(docs.GetError()))
        finally:
            wx.EndBusyCursor()

    def GetFilterByIva(self, idDoc,  iv, nd1, nd2, nAnno):
        lSelected=self.GetDocWithIva(idDoc,  iv, nd1, nd2, nAnno)
        flt=''
        if len(lSelected)>0:
            flt='doc.id in ('
            for id in lSelected:
                flt = '%s%s, ' % (flt, id)
            flt = '%s)' % flt
            flt = flt.replace(', )', ')')
        else:
            flt = 'False'
        return flt

    def GetDocWithIva(self, idDoc,  iv, nd1, nd2, nAnno):
        lSelected=[]
        ivaMov=ftd.MovXCodIva()
        ivaMov.ClearBaseFilters()
        ivaMov.AddFilter('doc.id_tipdoc=%s' % idDoc)
        ivaMov.AddFilter('mov.id_aliqiva=%s' % iv)
        ivaMov.AddFilter('year(doc.datdoc)=%s' % nAnno)
        if nd1:
            ivaMov.AddFilter('doc.numdoc>=%s' % nd1)
        if nd2:
            ivaMov.AddFilter('doc.numdoc<=%s' % nd2)
        ivaMov.Retrieve()
        for r in ivaMov:
            lSelected.append(r.id_doc)
        return lSelected


    def OnStampa(self, event):
        self.StampaDoc()
        event.Skip()

    def StampaDoc(self):
        self.Stampa(self.dbdocs.config.toolprint)

    def SetAnagAndRegCon(self, report, doc):
        if doc.cfgdoc.id != doc.id_tipdoc:
            doc.cfgdoc.Get(doc.id_tipdoc)
        do = True
        if doc._info.anag is not None:
            do = doc._info.anag.id != doc.id_pdc
        if do:
            doc._info.anag = doc.GetAnag()
        if doc.id_reg:
            doc.regcon.Get(doc.id_reg)

    def Stampa(self, rptname, rpttitle='', is_list=False):
        docs = self.GetDocumenti()
        if docs is None:
            return
        docs._info.anag = None
        dpflag = []

        cfg = dbm.CfgDocMov()
        cfg.Get(self.FindWindowById(wdr.ID_TIPDOC).GetValue())

        if is_list:
            PrintOtherQuestionsFiller = PrintOtherQuestionsReactor = None

        else:
            def PrintOtherQuestionsFiller(p):
                dewdr.PrintOtherQuestionsFunc(p)
                pcn = p.FindWindowByName
                if cfg.askstaint != 'X':
                    pcn('staint').Hide()
                if cfg.askstapre != 'X':
                    pcn('stapre').Hide()

            def PrintOtherQuestionsReactor(dlg):
                pcn = dlg.FindWindowByName
                docs._info.report_askstaint_reply = (pcn('staint').IsChecked())
                docs._info.report_askstapre_reply = (pcn('stapre').IsChecked())

        def SetAnagAndRegCon(report, doc):
            self.SetAnagAndRegCon(report, doc)
            if doc.f_printed != 1 and not doc.id in dpflag:
                dpflag.append(doc.id)

        docs._info.titleprint = rpttitle
        r = rpt.Report(self, self.SetDbTable2Print(docs), 
                       rptname, rowFunc=SetAnagAndRegCon,
                       changefilename=docs.GetPrintFileName(),
                       otherquestions_filler=PrintOtherQuestionsFiller,
                       otherquestions_reactor=PrintOtherQuestionsReactor,)
        if r.usedReport:
            if r.usedReport.printed:
                if dpflag:
                    cmd = "UPDATE %s SET f_printed=1 WHERE " % bt.TABNAME_MOVMAG_H
                    if len(dpflag) == 1:
                        cmd += "id=%d" % dpflag[0]
                    else:
                        cmd += "id IN (%s)" % ','.join(map(str, dpflag))
                    docs._info.db.Execute(cmd)

    def SetDbTable2Print(self, docs):
        return docs
    
    def OnEmail(self, event):
        self.SendMail(self.dbdocs.config.toolprint)
        event.Skip()

    def SendMail(self, rptname, rpttitle=''):
        r = None
        d2p = dbm.DocMag()
        d2p._info.anag = None
        wait = None
        totemails = 0
        c = self.dbdocs._GetFieldIndex('dastampare', inline=True)
        rs = self.dbdocs.GetRecordset()
        for n in range(self.dbdocs.RowsCount()):
            if rs[n][c]:
                totemails += 1
        try:
            try:
                for n, doc in enumerate(self.dbdocs):
                    if doc.dastampare:
                        d2p.Get(doc.id)
                        pathname = d2p.GetPrintPathName()
                        filename = d2p.GetPrintFileName()
                        if r is None:
                            #d2p._info.titleprint = rpttitle
                            r = rpt.Report(self, d2p, rptname, rowFunc=self.SetAnagAndRegCon, output="STORE",
                                           changepathname=pathname, changefilename=filename, forcechoice=True,
                                           emailbutton=totemails)
                            ur = r.GetUsedReport()
                            if ur is None:
                                break
                            sendfile = r.GetUsedReport().GetFileName()
                        else:
                            ur = r.StartReport(filename)
                        sei = d2p.SendMail_Prepare()
                        if sei.errors:
                            aw.awu.MsgDialog(self, sei.request, style=wx.ICON_ERROR)
                        else:
                            if wait is None:
                                wait = aw.awu.WaitDialog(self, message="Invio email in corso...",
                                                         maximum=self.dbdocs.RowsCount())
                                wx.Sleep(3)
                            wait.SetMessage("Invio a: %s" % sei.sendto)
                            wx.Sleep(3)
                            d2p.SendMail(sei, ur.GetFileName())
                    if wait is not None:
                        wait.SetValue(n)
            except Exception, e:
                aw.awu.MsgDialog(self, repr(e.args))
        finally:
            if wait is not None:
                wait.Destroy()


# ------------------------------------------------------------------------------


class StaDifFrame(aw.Frame):
    """
    Frame Stampa differita.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(StaDifPanel(self, -1))
        self.CenterOnScreen()

    def Show(self, show=True):
        aw.Frame.Show(self, show)
        if show:
            self.FindWindowById(wdr.ID_TIPDOC).SetFocus()
