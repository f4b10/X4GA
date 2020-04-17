#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/pdcrel.py
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

from awc.controls.linktable import EVT_LINKTABCHANGED
from awc.controls.datectrl import EVT_DATECHANGED

import wx
from wx.lib import masked

import MySQLdb

import awc
MsgDialog = awc.util.MsgDialog

import awc.controls.linktable as lt
import awc.layout.gestanag as ga
import awc.controls.windows as aw

import anag.pdcrel_wdr as wdr
import anag

from awc.util import GetNamedChildrens
from awc.util import MsgDialog, MsgDialogDbError

from awc.tables.util import CheckRefIntegrity

import cfg.cfgautomat as auto

import stormdb as adb
import report as rpt

import dbtables as dba


import wx.lib.newevent
(FilterChangedEvent,  EVT_FilterChanged)  =  wx.lib.newevent.NewEvent()

import os

import Env
stdcolor = Env.Azienda.Colours
bt = Env.Azienda.BaseTab

import wx.grid as gl
import awc.controls.dbgrid as dbglib


CONTACT_TYPE_EMAIL = 0
CONTACT_TYPE_CALL =  1

ID_BTN_CARDPDC = wx.NewId()


class _PdcRangeCode(object):
    """
    Mixin x classi che gestiscono sottoconti.  Offre il metodo per determinare
    il codice automatico del sottoconto in fase di inserimento.
    """
    def __init__(self):
        """
        dbpdcmax dbtable pdc sintetizzata x il codice max.
        dbpdctip dbtable tipi anagrafici con allegati i rispettivi range cod.
        """
        self.dbpdcmax = adb.DbTable(bt.TABNAME_PDC, 'pdc', writable=False,
                                    fields='codice')
        self.dbpdcmax.AddLimit(1)
        self.dbpdcmax.AddOrder('pdc.codice', adb.ORDER_DESCENDING)

        self.dbpdctip = adb.DbTable(bt.TABNAME_PDCTIP, 'tipana', writable=False)
        self.dbpdctip.AddJoin(bt.TABNAME_PDCRANGE, 'pdcrange')

    def NewRangeCode(self, idtipo):
        """
        Determina il nuovo codice automatico in base al tipo anagrafico passato
        ed al relativo range di codici.
        """
        newcod = ''
        pdc, tpa = self.dbpdcmax, self.dbpdctip
        if tpa.Retrieve('tipana.id=%s', idtipo) and tpa.RowsCount():
            pdc.ClearFilters()
            pdc.AddFilter('pdc.codice>=%s AND pdc.codice<=%s',
                          tpa.pdcrange.rangemin,
                          tpa.pdcrange.rangemax)
            if pdc.Retrieve():
                if pdc.OneRow() and pdc.codice is not None:
                    lastnum = int(pdc.codice or '')
                else:
                    lastnum = tpa.pdcrange.rangemin
                newcod = str(lastnum+1)
        return newcod

    def OnTipanaChanged(self, event):
        if self.db_recid is None and not self.valuesearch:
            tipo = event.GetEventObject().GetValue()
            ctr = self.FindWindowByName('codice')
            if tipo is not None and ctr is not None:
                ctr.SetValue(self.NewRangeCode(tipo))
        event.Skip()


# ------------------------------------------------------------------------------


class _PdcRelPanel(ga.AnagPanel,\
                   auto.CfgAutomat,\
                   _PdcRangeCode):
    """
    Classe specializzata nel mantenere relazionate le tabelle anagrafiche
    di clienti, fornitori, banche con i relativi sottoconti nella tabella
    del piano dei conti di contabilità.
    """

    _ctrcod = None
    _ctrdes = None
    tabanag = None
    pdctipo = None

    def __init__(self, *args, **kwargs):

        assert type(self.tabanag) in (str, unicode),\
               """Il nome della tabella anagrafica non è definito"""

        assert type(self.pdctipo) in (str, unicode),\
               """Il tipo di anagrafica non è definito"""

        ga.AnagPanel.__init__(self, *args, **kwargs)

        self.firstfocus ='descriz'

        self.SetDbSetup(bt.tabelle[bt.TABSETUP_TABLE_PDC])
        self._sqlrelcol = ", tipana.tipo, tipana.codice"
        self._sqlrelfrm =\
            " LEFT JOIN %s AS tipana ON %s.id_tipo=tipana.id"\
            % ( bt.TABNAME_PDCTIP, bt.TABNAME_PDC )
        self._sqlrelfrm +=\
            " LEFT JOIN %s AS anag ON %s.id=anag.id"\
            % ( self.tabanag, bt.TABNAME_PDC )
        self.db_searchfilter = "tipana.tipo='%s'" % self.pdctipo
        self.db_tabprefix = "%s." % bt.TABNAME_PDC
        self.SetDbOrderColumns((
            ("Codice",      ('pdc.codice',)),
            ("Descrizione", ('tipana.codice', 'pdc.descriz',)),
        ))
        self.SetOrderNumber(1)

        self.anag_db_columns = None

        auto.CfgAutomat.__init__(self, self.db_curs)
        self._auto_pdctip = None
        self._auto_bilmas = None
        self._auto_bilcon = None
        self._auto_bilcee = None

        _PdcRangeCode.__init__(self)

        self.HelpBuilder_SetDir('anag.pdcrel_%s' % str(self.tabanag).capitalize())

    def InitControls(self, *args, **kwargs):
        ga.AnagPanel.InitControls(self, *args, **kwargs)
        if self._btnattach is not None:
            self._btnattach.SetScope(self.db_tabname)#self.tabanag)
        self.Bind(lt.EVT_LINKTABCHANGED, self.OnTipanaChanged, id=wdr.ID_CTRPDCTIP)

    def SetControlsMaxLength(self, fields, controls):
        ga.AnagPanel.SetControlsMaxLength(self, fields, controls)
        ga.AnagPanel.SetControlsMaxLength(self, self.anag_db_columns, self.anag_db_datalink)

    def InitDataControls( self ):
        """
        Inizializza i controlli relativi alle colonne standard C{codice} e
        C{descriz} (codice e descrizione della tabella gestita).
        """
        out = ga.AnagPanel.InitDataControls( self, update=False )

        controls = GetNamedChildrens( self._panelcard,\
                                      [ col[0] \
                                        for col in self.anag_db_columns ])
        self.anag_db_datalink = [ ( ctr.GetName(), ctr )\
                                  for ctr in controls ]
        self.anag_db_datacols = [ col for col,ctr in self.anag_db_datalink ]

        for col, ctr in self.anag_db_datalink:
            if isinstance(ctr, wx.Window):
                self.BindChangedEvent(ctr)

        for col,ctr in self.db_datalink:
            if col == "id_tipo":
                ctr.SetFilter("tipo='%s'" % self.pdctipo)
        self._ctrcod = self.FindWindowByName("codice")
        err = not self._ctrcod
        if err: msg = "codice"
        else:
            self._ctrdes = self.FindWindowByName("descriz")
            err = not self._ctrdes
            if err: msg = "descrizione"
        if err:
            MsgDialog(self,\
"""Non sarà possibile inserire nuovi elementi poiché manca la """\
"""definizione del controllo di tipo '%s'.""" % msg )

        #se c'è un solo record, il controllo della descrizione è inspiegabilmente
        #scrollato a destra troncando a video la parte iniziale; settando il focus
        #tale comportamento errato non ha luogo
        #viva le gui :(
        c = self.FindWindowByName('descriz')
        if c:
            c.SetFocus()

        if ga.SEARCH_ON_SHOW or not self.complete:
            self.UpdateSearch()

        return out

    def UpdateDataControls( self, recno ):
        ga.AnagPanel.UpdateDataControls( self, recno, activatechanges=False )
        if self.db_recid is None and not self.valuesearch:
            #inserimento record, imposto classificazioni di default
            #per mastro conto e tipo, sulla base di quanto definito nella
            #sottoclasse (casse, banche, clienti, fornitori)
            for auto, col in (("pdctip", "tipo"),
                              ("bilmas", "bilmas"),
                              ("bilcon", "bilcon"),
                              ("bilcee", "bilcee"),):
                ctr = self.FindWindowByName("id_%s" % col)
                if ctr is not None:
                    ctr.SetValue(self.__getattribute__("_auto_%s" % auto))
        _sel = ""
        for col,ctr in self.anag_db_datalink:
            _sel += "%s.%s, " % (self.tabanag, col)
        _sel = _sel[:-2]
        cmd =\
"""SELECT %s FROM %s """\
"""WHERE id""" % (_sel, self.tabanag)
        par = []
        if self.db_recid is None:
            cmd += """ IS NULL"""
        else:
            cmd += r"=%s"
            par.append(self.db_recid)
        void = True
        try:
            if self.db_curs.execute(cmd, par):
                rsanag = self.db_curs.fetchone()
                void = False
        except Exception, e:
            MsgDialog(self, "Problema di definizione tabella:\nErrore=%s"\
                      % repr(e.args))
            pass
        for n, (col, ctr) in enumerate(self.anag_db_datalink):
            if isinstance(ctr, wx.Window) and col != 'id':
                if void:
                    self.ResetControl(ctr)
                else:
                    if rsanag[n] is None:
                        self.ResetControl(ctr)
                    else:
                        ctr.SetValue( rsanag[n] )
        event = ga.AcceptDataChanged()
        event.acceptchanges = True
        wx.PostEvent(self, event)

    def CopyFrom_GetLastInserted(self):
        lastid = self.db_last_inserted_id
        if lastid is None:
            db = adb.db.__database__
            if db.Retrieve('SELECT MAX(id) FROM %s' % self.tabanag):
                if len(db.rs) == 1:
                    lastid = db.rs[0][0]
        return lastid

    def CopyFrom_DoCopy(self, idcopy):
        for tabname, datalink in ((self.db_tabname, self.db_datalink),
                                  (self.tabanag,    self.anag_db_datalink),):
            db = adb.DbTable(tabname, 'tab')
            if db.Get(idcopy) and db.OneRow():
                for name in db.GetFieldNames():
                    if name != 'id':
                        try:
                            n = aw.awu.ListSearch(datalink, lambda x: x[0] == name)
                            v = getattr(db, name)
                            if v is not None:
                                datalink[n][1].SetValue(v)
                        except IndexError:
                            pass
        self.SetFirstFocus()

    def SetValueSearchFields(self):
        ga.AnagPanel.SetValueSearchFields(self)
        ga.AnagPanel.SetValueSearchFields(self, self.anag_db_datalink)

    def GetValueSearchValues(self):
        vsf = ga.AnagPanel.GetValueSearchValues(self)
        for n, (col, ctr) in enumerate(self.anag_db_datalink):
            if isinstance(ctr, (wx.RadioBox, wx.CheckBox, wx.ComboBox)):
                continue
            if type(ctr) in (str, unicode):
                value = getattr(self, ctr)
            else:
                value = ctr.GetValue()
            if value:
                vsf.append((self.tabanag, col, value))
        return vsf

    def GetSqlValueSearch(self):
        flt, par = ga.AnagPanel.GetSqlValueSearch(self)
        if self.complete:
            for alias in 'clienti,fornit'.split(','):
                alias += '.'
                if alias in flt:
                    flt = flt.replace(alias, 'anag.')
        return flt, par

    def TransferDataFromWindow( self ):
        """
        Scrittura dati.  Vengono prima salvati i dati del pdc se con
        successo vengono salvati i dati anagrafici.
        """
        new = self.db_recid is None
        if not new:
            #in modifica di cli/for nato come pdc non relazionato ad anagrafiche
            try:
                self.db_curs.execute("SELECT COUNT(id) FROM %s WHERE id=%%s" \
                                     % self.tabanag, self.db_recid)
                n = self.db_curs.fetchone()[0]
                new = (n == 0)
            except MySQLdb.Error, e:
                pass
        written = ga.AnagPanel.TransferDataFromWindow(self)
        if written:

            if new:
                cmd = "INSERT INTO %s (" % self.tabanag
                cmd += ", ".join( [ col for col,ctr in self.anag_db_datalink ] )
                cmd += ") VALUES ("
                cmd += (r"%s, " * len(self.anag_db_datalink))[:-2] + ");"
            else:
                cmd = "UPDATE %s SET " % self.tabanag
                cmd += ", ".join(
                       [ "%s=%%s" % col for col,ctr in self.anag_db_datalink ] )
                cmd += " WHERE ID=%s;" % self.db_recid

            par = []
            for col, ctr in self.anag_db_datalink:
                if col == 'id':
                    par.append(self.db_recid)
                else:
                    par.append(ctr.GetValue())

            try:
                self.db_curs.execute(cmd, par)
                if self.SyncManager.NeedStore2Sync(self.tabanag):
                    if new:
                        op='INSERT'
                    else:
                        op='UPDATE'
                    self.SyncManager.StoreUpdate(op=op, \
                                              dbTable=self.tabanag, \
                                              recNew=par, \
                                              dataLink=self.anag_db_datalink)
            except MySQLdb.Error, e:
                MsgDialog(self, message=repr(e.args))
                written = False

        return written

    #def TestForDeletion( self ):
        #"""
        #Metodo per la verifica della cancellabilità di un elemento.

        #@todo: controlli per integrità referenziale sulle movimentazioni.
        #"""
        #out = False
        #if ga.AnagPanel.TestForDeletion(self):
            #out = True
        #return out

    def DeleteDataRecord( self ):
        """
        Cancellazione record.  Viene prima cancellato il record dei dati
        anagrafici e se con successo viene richiamato DeleteDataRecord di
        AnagPanel.
        """
        out = False
        delete = False
        if self.db_recid is None:
            delete = True
        else:
            cmd =\
"""DELETE FROM %s WHERE id=%s""" % (self.tabanag, self.db_recid)
            try:
                self.db_curs.execute(cmd)
                delete = True
            except:
                pass
        if delete:
            if self.SyncManager.NeedStore2Sync(self.tabanag):
                self.SyncManager.StoreUpdate(op='DELETE', \
                                          dbTable=self.tabanag, \
                                          recId=self.db_recid)
            out = ga.AnagPanel.DeleteDataRecord(self)
        return out

    def GetDbPrint(self):
        if self.tabanag == bt.TABNAME_CLIENTI:
            db = dba.Clienti()
        elif self.tabanag == bt.TABNAME_FORNIT:
            db = dba.Fornit()
        elif self.tabanag == bt.TABNAME_CASSE:
            db = dba.Casse()
        elif self.tabanag == bt.TABNAME_BANCHE:
            db = dba.Banche()
        elif self.tabanag == bt.TABNAME_EFFETTI:
            db = dba.Effetti()
        else:
            db = dba.Pdc()
        return db


# ------------------------------------------------------------------------------


class GrigliaPrezziGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia prezzi.
    """

    idpdc = None

    def __init__(self, parent, dbgri):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable grigila prezzi
        """

        dbglib.DbGridColoriAlternati.__init__(self, parent, -1,
                                              size=parent.GetClientSizeTuple(),
                                              style=0,
                                              idGrid='grigliaprezzi')
        self.dbgri = dbgri

        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL
        _PRE = bt.GetMagPreMaskInfo()
        _PRC = bt.GetMagScoMaskInfo()
        _PZC = bt.GetMagPzcMaskInfo()

        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        gri = dbgri
        pro = gri.prod

        cols = []
        self.edcols = []

        def a(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                self.edcols.append(n)
            return n
        def b(x):
            return a(x, True)

        self.COL_codice =  b((100, (cn(pro, 'codice'),  "Codice",         _STR, True)))
        self.COL_descriz = a((230, (cn(pro, 'descriz'), "Prodotto",       _STR, True)))
        self.COL_DATA =    b(( 90, (cn(gri, 'data'),    "Data",           _DAT, True)))

        if bt.MAGPZGRIP:
            self.COL_PZCONF = b((70,(cn(gri,'pzconf'),  "Pz.Conf.",       _PZC, True)))

        self.COL_PREZZO =  b((110, (cn(gri, 'prezzo'),  "Prezzo griglia", _PRE, True)))

        if bt.MAGNUMSCO >= 1:
            self.COL_SCONTO1 = b(( 50, (cn(gri, 'sconto1'), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _PRC, True)))
        if bt.MAGNUMSCO >= 2:
            self.COL_SCONTO2 = b(( 50, (cn(gri, 'sconto2'), "Sc.%2",      _PRC, True)))
        if bt.MAGNUMSCO >= 3:
            self.COL_SCONTO3 = b(( 50, (cn(gri, 'sconto3'), "Sc.%3",      _PRC, True)))
        if bt.MAGNUMSCO >= 4:
            self.COL_SCONTO4 = b(( 50, (cn(gri, 'sconto4'), "Sc.%4",      _PRC, True)))
        if bt.MAGNUMSCO >= 5:
            self.COL_SCONTO5 = b(( 50, (cn(gri, 'sconto5'), "Sc.%5",      _PRC, True)))
        if bt.MAGNUMSCO >= 6:
            self.COL_SCONTO6 = b(( 50, (cn(gri, 'sconto6'), "Sc.%6",      _PRC, True)))
        self.COL_ID_GRIP = a((  1, (cn(gri, 'id'),      "#gri",           _STR, True)))
        self.COL_ID_PROD = a((  1, (cn(pro, 'id'),      "#pro",           _STR, True)))

        self.cols = cols

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        canedit = canins = True

        links = []
        import anag.lib as alib
        from anag.prod import ProdDialog
        ltpro = alib.LinkTabProdAttr(bt.TABNAME_PROD, #table
                                     self.COL_codice,     #grid col
                                     cn(gri, 'id_prod'),  #rs col id
                                     cn(pro, 'codice'),   #rs col cod
                                     cn(pro, 'descriz'),  #rs col des
                                     ProdDialog,          #card class
                                     refresh=True)        #refresh flag
        links.append(ltpro)

        afteredit = ((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.EditedValues),)

        self.SetData([], colmap, canedit, canins, links, afteredit, self.CreateNewRow)

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

        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)

    def EditedValues(self, row, gridcol, col, value):
        dbgrip = self.dbgri
        if 0 <= row < dbgrip.RowsCount():
            dbgrip.MoveRow(row)
            dbgrip.data = dbgrip.data #forza la scrittura della riga
        return True

    def OnRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbgri.RowsCount():
            self.MenuPopup(event)
            event.Skip()

    def OnDblClick(self, event):
        gri = self.dbgri
        sr = self.GetSelectedRows()
        row = sr[0]
        if 0 <= row < gri.RowsCount():
            gri.MoveRow(row)
            self.ApriSchedaProd()
        event.Skip()

    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        if not 0 <= row < self.dbgri.RowsCount():
            return
        self.dbgri.MoveRow(row)
        self.SetGridCursor(row, col)
        self.SelectRow(row)
        gri = self.dbgri
        prodok = gri.id_prod is not None
        voci = []
        voci.append(("Apri la scheda prodotto", self.OnSchedaProd, prodok))
        voci.append(("Elimina il prodotto dalla griglia", self.OnDeleteRow, True))
        menu = wx.Menu()
        for text, func, enab in voci:
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        xo, yo = event.GetPosition()
        self.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()

    def OnSchedaProd(self, event):
        self.ApriSchedaProd()
        event.Skip()

    def ApriSchedaProd(self):
        proid = self.dbgri.id_prod
        f = None
        try:
            from anag.prod import ProdDialog
            wx.BeginBusyCursor()
            f = ProdDialog(self, onecodeonly=proid)
            f.OneCardOnly(proid)
            f.CenterOnScreen()
        finally:
            wx.EndBusyCursor()
        f.ShowModal()
        if f is not None:
            f.Destroy()

    def OnDeleteRow(self, event):
        sr = self.GetSelectedRows()
        if sr:
            row = sr[-1]
            gri = self.dbgri
            if 0 <= row < gri.RowsCount():
                gri.MoveRow(row)
                if gri.id is not None:
                    if not gri.id in gri._info.deletedRecords:
                        #riga già esistente, marco per cancellazione da db
                        gri._info.deletedRecords.append(gri.id)
                #elimino riga da dbgrid
                self.DeleteRows(row)
                gri._info.recordCount -= 1
                if gri._info.recordNumber >= gri._info.recordCount:
                    gri._info.recordNumber -= 1
                    gri._UpdateTableVars()
                #after deletion, record cursor is on the following one
                #so for iterations we decrement iteration index and count
                gri._info.iterIndex -= 1
                gri._info.iterCount -= 1
                self.Refresh()
        event.Skip()

    def SetPdcId(self, idpdc):
        self.idpdc = idpdc

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly(not col in self.edcols)
        return attr

    def GridListTestValues(self, row, gridcol, col, value):
        out = True
        return out

    def CreateNewRow(self):
        g = self.dbgri
        g.CreateNewRow()
        g.id_pdc = self.idpdc
        if bt.MAGDATGRIP:
            g.data = Env.Azienda.Login.dataElab
        return True


# ------------------------------------------------------------------------------


class GriglieCollegateGrid(dbglib.DbGridColoriAlternati):
    """
    Correlazione anagrafiche per la griglia prezzi.
    """

    idpdc = None

    def __init__(self, parent, dbpcp):
        """
        Parametri:
        parent griglia  (wx.Panel)
        """

        dbglib.DbGridColoriAlternati.__init__(self, parent, -1,
                                              size=parent.GetClientSizeTuple(),
                                              style=0)
        _STR = gl.GRID_VALUE_STRING
        _CHK = gl.GRID_VALUE_BOOL+":1,0"

        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)

        cols = []
        self.edcols = []

        def e(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                self.edcols.append(n)
            return n
        def E(x):
            return e(x, True)

        self.dbpcp = pcp = dbpcp
        pdc = pcp
        ana = pdc.anag

        self.COL_CODICE =  e(( 50, (cn(pdc, 'codice'),       "Codice",     _STR, True)))
        self.COL_DESCRIZ = e((200, (cn(pdc, 'descriz'),      "Anagrafica", _STR, True)))
        self.COL_vediall = e(( 50, (cn(ana, 'vediprod_all'), "Tutti",      _CHK, True)))
        self.COL_vedigri = e(( 50, (cn(ana, 'vediprod_gra'), "S.G.",       _CHK, True)))
        self.COL_vedigrf = e(( 50, (cn(ana, 'vediprod_grf'), "G.F.",       _CHK, True)))

        self.cols = cols
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        canedit = canins = False

        self.SetData((), colmap, canedit, canins)

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

    def SetPdcId(self, idpdc):
        self.idpdc = idpdc
        self.dbpcp.SetPdcMaster(idpdc)
        self.ChangeData(self.dbpcp.GetRecordset())


# ------------------------------------------------------------------------------


class GriglieCollegatePanel(aw.Panel):

    def __init__(self, *args, **kwargs):
        GriglieTableClass = kwargs.pop('GriglieTableClass')
        pdc_master = kwargs.pop('pdc_master')
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.GriglieCollegateFunc(self)
        cn = self.FindWindowByName
        self.dbpcp = GriglieTableClass()
        self.gridpcp = GriglieCollegateGrid(cn('pangridlink'), self.dbpcp)
        cn('pdc_master').SetValue(pdc_master)
        self.gridpcp.SetPdcId(pdc_master)


# ------------------------------------------------------------------------------


class GriglieCollegateDialog(aw.Dialog):

    def __init__(self, *args, **kwargs):
        GriglieTableClass = kwargs.pop('GriglieTableClass')
        pdc_master = kwargs.pop('pdc_master')
        kwargs['title'] = 'Griglie Collegate'
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = GriglieCollegatePanel(self, GriglieTableClass=GriglieTableClass,
                                           pdc_master=pdc_master)

        self.AddSizedPanel(self.panel)


# ------------------------------------------------------------------------------


#costanti per recordset banche del cliente/fornitore
RSBAN_ID      =  0
RSBAN_CODICE  =  1
RSBAN_DESCRIZ =  2
RSBAN_PAESE   =  3
RSBAN_CINIBAN =  4
RSBAN_CINBBAN =  5
RSBAN_ABI     =  6
RSBAN_CAB     =  7
RSBAN_NUMCC   =  8
RSBAN_BBAN    =  9
RSBAN_IBAN    = 10
RSBAN_BIC     = 11
RSBAN_PREF    = 12

#campi della tabella banche del cliente
banfields = 'id codice descriz paese ciniban cinbban abi cab numcc bban iban bic pref'.split()

#===============================================================================
#
# #costanti per recordset destinatari del cliente/fornitore
# RSDES_ID       =  0
# RSDES_CODICE   =  1
# RSDES_DESCRIZ  =  2
# RSDES_INDIR    =  3
# RSDES_CAP      =  4
# RSDES_CITTA    =  5
# RSDES_PROV     =  6
# RSDES_NUMTEL   =  7
# RSDES_NUMTEL2  =  8
# RSDES_NUMCEL   =  9
# RSDES_NUMFAX   = 10
# RSDES_EMAIL    = 11
# RSDES_CONTATTO = 12
# RSDES_PREF     = 13
#
#
# #campi della tabella destinatari del cliente
# desfields = 'id codice descriz indirizzo cap citta prov numtel numtel2 numcel numfax email contatto pref'.split()
#===============================================================================

class GrigliaPrezziAttualiPanel(wx.Panel):

    def __init__(self, *args, **kwargs):

        id_pdc = kwargs.pop('id_pdc')
        tipana = kwargs.pop('tipana')
        if tipana == "C":
            self._desana = "Cliente"
        else:
            self._desana = "Fornitore"
        self.tipana = tipana

        wx.Panel.__init__(self, *args, **kwargs)

        import magazz.listini_wdr as liswdr
        liswdr.VediPrezziInVigoreFunc(self)

        import magazz.stagrip as stagrip
        self.dbgrip = stagrip.dba.TabProdGrigliaPrezziAttualiPdcTable()
        self.dbgrip.SetParam(Env.Azienda.Login.dataElab, id_pdc)
        self.dbgrip.Retrieve()

        def cn(x):
            return self.FindWindowByName(x)

        self.gridlis = stagrip.GrigliaPrezziAttualiGrid(cn('pangridlist'),
                                                        self.dbgrip,
                                                        self.tipana)

        self.Bind(wx.EVT_BUTTON, self.OnPrint, cn('butprint'))

    def OnPrint(self, event):
        self.dbgrip._datlis = Env.Azienda.Login.dataElab
        self.dbgrip._desana = self._desana
        rpt_name = "Griglia prezzi in vigore dell'anagrafica"
        if self.tipana == 'C':
            cde = bt.MAGCDEGRIP
        else:
            cde = bt.MAGCDEGRIF
        if cde:
            rpt_name += ' con codice e descrizione esterni'
        rpt.Report(self, self.dbgrip, rpt_name)
        event.Skip()


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        id_pdc = kwargs.pop('id_pdc')
        tipana = kwargs.pop('tipana')
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GrigliaPrezziAttualiPanel(self, id_pdc=id_pdc, tipana=tipana))


# ------------------------------------------------------------------------------


class DatiBancariMixin(object):

    def OnCalcolaBBAN(self, event):
        self.CalcolaXBAN('bban')
        event.Skip()

    def OnCalcolaIBAN(self, event):
        self.CalcolaXBAN('iban')
        event.Skip()

    def CalcolaXBAN(self, tipo):

        if not tipo in 'bban iban'.split():
            raise Exception, 'Tipo di calcolo errato: %s' % tipo

        cols = []
        keys = []

        lcc = 12
        if tipo == 'iban':
            keys.append(['paese',   'Paese',    2])
            keys.append(['ciniban', 'CIN IBAN', 2])
            lcc = 12

        keys.append(['cinbban', 'CIN BBAN', 1])
        keys.append(['abi',     'ABI',      5])
        keys.append(['cab',     'CAB',      5])
        keys.append(['numcc',   'C/C',    lcc])

        cols = [key for key, des, lun in keys]

        def cn(col):
            return self.FindWindowByName('ban_%s'%col)

        if cn(tipo).GetValue():
            if aw.awu.MsgDialog(self, "Il codice %s è già compilato, vuoi ricalcolarlo ?" % str(tipo).upper(), style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return

        xban = ''
        for key, des, lun in keys:
            val = cn(key).GetValue() or ''
            if not val:
                aw.awu.MsgDialog(self, "Manca %s" % des)
                def setfocus():
                    cn(key).SetFocus()
                wx.CallAfter(setfocus)
                return
            if key == 'numcc':
                if tipo == 'bban' or xban.startswith('IT'):
                    v = ''
                    for x in str(val):
                        if str.isdigit(x):
                            v += x
                    val = str(v).zfill(lun)
                else:
                    val = str(val).strip()
            else:
                if len(val) != lun:
                    aw.awu.MsgDialog(self, "Valore errato per %s" % des)
                    return
            xban += val

        cn(tipo).SetValue(xban)


# ------------------------------------------------------------------------------


class _CliForPanel(_PdcRelPanel, DatiBancariMixin):

    #_GridBan_OnCalcolaBBAN = DatiBancariMixin.OnCalcolaBBAN
    #_GridBan_OnCalcolaIBAN = DatiBancariMixin.OnCalcolaIBAN

    def __init__(self, *args, **kwargs):

        _PdcRelPanel.__init__(self, *args, **kwargs)
        DatiBancariMixin.__init__(self)

        self._sqlrelcol += ", anag.indirizzo, anag.cap, anag.citta, anag.prov"
        self._sqlrelcol += ", anag.piva, anag.codfisc"
        self._sqlrelcol += ", anag.numtel, anag.numfax, anag.email, tipana.tipo"
        
        try:
            from fatturapa_ver import VERSION_STRING
            if VERSION_STRING >= '1.1.17':
                if self.pdctipo == 'C':
                    self._sqlrelcol += ", anag.ftel_pec, anag.ftel_codsdi"
        except:
            pass
        self.rsban = []
        self.rsbanmod = []
        self.rsbannew = []
        self.rsbandel = []
        self._grid_ban = None

        self.rsdes = []
        self.rsdesmod = []
        self.rsdesnew = []
        self.rsdesdel = []
        self._grid_des = None

        self.dbgrip = None
        self.gridgrip = None

        self.loadrelated = None

    def InitControls(self, *args, **kwargs):
        self.loadrelated = False
        _PdcRelPanel.InitControls(self, *args, **kwargs)
        self.loadrelated = True

        cn = self.FindWindowByName
        nb = cn('workzone')
        for i in range(0,nb.GetPageCount()):
            if nb.GetPageText(i)=='Impostazioni Commerciali':
                break

        i=i+1
        import pageBanche
        self.banchePanel=pageBanche.BanchePanel(nb,  mainPanel=self )
        nb.InsertPage(i, self.banchePanel, 'Banche')

        i=i+1
        import pageDestinazioni
        self.destinPanel=pageDestinazioni.DestinPanel(nb,  mainPanel=self )
        nb.InsertPage(i, self.destinPanel, 'Destinazioni')

        self.InitControls_PersonalPage()

    def InitAnagToolbar(self, parent):
        out = ga.AnagToolbar(parent, -1, hide_ssv=False)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnSSV)
        return out

    def OnSSV(self, event):
        self.UpdateSearch()
        event.Skip()

    def InitGrigliaPrezzi(self):
        def cn(x):
            return self.FindWindowByName(x)
        if (self.pdctipo == "C" and bt.MAGATTGRIP) or (self.pdctipo == "F" and bt.MAGATTGRIF):
            gri = adb.DbTable(bt.TABNAME_GRIGLIE, 'gri')
            pdc = gri.AddJoin(bt.TABNAME_PROD,    'prod')
            gri.AddOrder('prod.codice')
            gri.AddOrder('gri.data', adb.ORDER_DESCENDING)
            gri.Get(-1)
            self.dbgrip = gri
            self.gridgrip = GrigliaPrezziGrid(cn('pangrip'), self.dbgrip)
            for name, func in (('butvediprevig', self.OnVediGrigliaInVigore),
                               ('butvedipdcgrp', self.OnVediGriglieCollegate),):
                self.Bind(wx.EVT_BUTTON, func, cn(name))
        else:
            wz = cn('workzone')
            for n in range(wz.GetPageCount()):
                if wz.GetPageText(n).lower() == 'griglia prezzi':
                    wz.RemovePage(n)
                    break

    def OnVediGriglieCollegate(self, event):
        cn = self.FindWindowByName
        pdc_master = cn('id_pdcgrp').GetValue()
        if pdc_master is None:
            pdc_master = self.db_recid
        if pdc_master:
            if self.pdctipo == 'C':
                GriglieTableClass = dba.GriglieCollegateClienti
            elif self.pdctipo == 'F':
                GriglieTableClass = dba.GriglieCollegateFornit
            else:
                raise Exception, "Impossibile determinare la tipologia di sottoconto per vedere le anagrafiche collegate alla griglia"
            dlg = GriglieCollegateDialog(self, GriglieTableClass=GriglieTableClass, pdc_master=pdc_master)
            dlg.ShowModal()
            dlg.Destroy()
        event.Skip()

    def OnVediGrigliaInVigore(self, event):
        cn = self.FindWindowByName
        pdc_master = cn('id_pdcgrp').GetValue()
        if pdc_master is None:
            pdc_master = self.db_recid
        title = "Griglia prezzi in vigore per %s" % cn('descriz').GetValue()
        d = GrigliaPrezziAttualiDialog(self, title=title, id_pdc=pdc_master, tipana=self.pdctipo)
        d.CenterOnScreen()
        d.ShowModal()
        d.Destroy()
        event.Skip()

    def UpdateDataControls( self, recno ):
        _PdcRelPanel.UpdateDataControls( self, recno )
        if self.loadrelated:
            for panel in [self.banchePanel, self.destinPanel]:
                try:
                    panel.UpdateDataControls()
                except:
                    pass
            self.UpdateDataControls_PersonalPage()
            if self.gridgrip is not None:
                self.LoadGriglia()
                self.gridgrip.SetGridCursor(0,0)

    def UpdateDataControls_PersonalPage(self):
        # Metodo da implementare nella classe derivata per gestire l'aggiornamento visuale dei controlli
        pass


    def UpdateDataRecord( self ):

        cn = self.FindWindowByName

        id, cf, pi, grupi = map(lambda x: cn(x).GetValue(), 'id codfisc piva grupiva'.split())

        do = True
        
        canProceed = True
        for ctr in range(3):
            err = ''
            if ctr == 0:
                #controllo presenza
                if (not cf or not pi) and grupi==1:
                    err = "Se indicato gruppo IVA e' necessario specificare sia Codice Fiscale che Partita Iva"
                    canProceed = False
                elif not cf and not pi:
                    err = 'Mancano sia il Codice Fiscale che la Partita IVA'
                elif not cf:
                    err = 'Manca il Codice Fiscale'
                elif not pi:
                    err = 'Manca la Partita IVA'
            elif ctr == 1:
                #controllo di forma
                if pi:
                    ctrpi = cn('piva').GetControllo()
                    if not ctrpi.Controlla():
                        err = ctrpi.GetStatus()
                if cf:
                    ctrcf = cn('codfisc').GetControllo()
                    if not ctrcf.Controlla():
                        err = ctrcf.GetStatus()
            elif ctr == 2:
                #controllo univocità
                db = adb.DbTable(self.tabanag, 'anag', writable=False)
                db.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id', idRight='id')
                db.Reset()
                for col, val, des in (('piva',    pi, 'La Partita IVA'),
                                      ('codfisc', cf, 'Il Codice Fiscale')):
                    db.ClearFilters()
                    if val:
                        db.AddFilter('anag.%s=%%s' % col, cn(col).GetValue())
                        if id:
                            db.AddFilter('anag.id<>%s', id)
                        db.Retrieve()
                        if not db.IsEmpty():
                            if err:
                                err += '\n'
                            err = "%s e' gia' presente su:\n" % des
                            err += '\n'.join(['%s %s' % (db.pdc.codice,
                                                         db.pdc.descriz)])
            if err and canProceed:
                err += '\n\nProcedo ugualmente?'
                x = MsgDialog(self, message=err,
                              style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
                do = x == wx.ID_YES
                if not do:
                    break
            elif err and not canProceed:
                x = MsgDialog(self, message=err)
                break
        if do:

            if cn('id_stato').GetValue() is None:
                cn('id_stato').SetValueHome()
                cn('nazione').SetValue("IT")

            self.loadrelated = False
            written = _PdcRelPanel.UpdateDataRecord(self)
            self.loadrelated = True

            if written:
                self.WriteGriglia(); self.LoadGriglia()

                for panel in [self.banchePanel, self.destinPanel]:
                    try:
                        panel.UpdateDataRecord()
                    except:
                        pass
                self.UpdateDataRecord_PersonalPage()
        else:
            written = False

        return written

    def UpdateDataRecord_PersonalPage(self):
        # Metodo da implementare nella classe derivata per gestire l'aggiornamento
        pass

    def WriteGriglia(self):
        if (self.pdctipo == "C" and bt.MAGATTGRIP) or (self.pdctipo == "F" and bt.MAGATTGRIF):
            gri = self.dbgrip
            if gri:
                if not gri.Save():
                    MsgDialog(self, 'Problema in scrittura griglia:\n%s'\
                              % repr(gri.GetError()))

    def WriteRelated(self, table, fields, rs, rsins, rsmod, rsdel):
        written = False
        setCol = ""
        for field in fields[1:]:
            setCol += "%s=%%s, " % field
        setCol += r"id_pdc=%s"
        cmdDel = "DELETE FROM %s WHERE %s.id=%%s"\
               % (table, table)
        cmdIns = "INSERT INTO %s SET %s"\
               % (table, setCol)
        cmdUpd = "UPDATE %s SET %s WHERE %s.id=%%s"\
               % (table, setCol, table)
        parDel = []
        parIns = []
        parUpd = []
        for rec in rs:
            recid = rec[0]
            if recid in rsdel:
                parDel.append(recid)
            else:
                par = rec[1:]
                par.append(self.db_recid)
                if recid is None:
                    parIns.append(par)
                else:
                    par.append(recid)
                    parUpd.append(par)
        for recid in rsdel:
            if not recid in parDel:
                parDel.append(recid)
        try:
            if parDel:
                self.db_curs.executemany(cmdDel, parDel)
            if parIns:
                self.db_curs.executemany(cmdIns, parIns)
            if parUpd:
                self.db_curs.executemany(cmdUpd, parUpd)
            written = True
        except MySQLdb.Error, e:
            aw.awu.MsgDialog(self, repr(e.args))
            #MsgDialogDbError(self, e)
        except Exception, e:
            pass
        return written


    def DeleteDataRecord( self ):
        recid = self.db_recid
        deleted = _PdcRelPanel.DeleteDataRecord(self)
        if deleted:
            for panel in [self.banchePanel, self.destinPanel]:
                try:
                    panel.DeleteDataRecord(recid)
                except:
                    pass
        self.DeleteDataRecord_PersonalPage(recid)

        return deleted

    def DeleteDataRecord_PersonalPage( self, recid ):
        # Metodo da implementare nella classe derivata per gestire la cancellazione
        pass

    def LoadGriglia(self):
        if self.gridgrip is not None:
            gri = self.dbgrip
            id_pdcgrp = self.FindWindowByName('id_pdcgrp').GetValue() or self.db_recid
            gri.Retrieve('gri.id_pdc=%s', id_pdcgrp)
            self.gridgrip.ChangeData(gri.GetRecordset())
            self.gridgrip.SetPdcId(id_pdcgrp)


    def BanDesPrint(self, fields, rs, rptname):
        cols = []
        for col in 'codice descriz indirizzo cap citta prov codfisc nazione piva'.split():
            cols.append(col)
        anag = adb.DbMem(','.join(cols))
        anag.CreateNewRow()
        for col in cols:
            setattr(anag, col, self.FindWindowByName(col).GetValue() or '')
        db = adb.DbMem(','.join(fields))
        db.SetRecordset(rs)
        db.anag = anag
        rpt.Report(self, db, rptname)

    def GetSqlFilterSearch(self):
        cn = self.FindWindowByName
        cmd, par = _PdcRelPanel.GetSqlFilterSearch(self)
        #filtro per inclusione/esclusione elementi con status nascosto
        if cn('_ssv').GetValue():
            flt = "status.hidesearch IS NULL or status.hidesearch<>1"
            if cmd:
                cmd = "(%s) AND " % cmd
            cmd += "(%s)" % flt
        val = self.FindWindowById(ga.ID_SEARCHVAL).GetValue()
        if len(val) == 11 and val.isdigit():
            cmd = lt.OrApp(cmd, "anag.piva=%s")
            par.append(val)
        elif len(val) == 16:
            cmd = lt.OrApp(cmd, "anag.codfisc=%s")
            par.append(val)
        return cmd, par

    def GetSearchResultsGrid(self, parent):
        if self.pdctipo=='C':
            idGrid = 'elecli'
        elif self.pdctipo=='F':
            idGrid = 'elefor'
        else:
            idGrid = 'elepdc'
        return CliForSearchResultsGrid(parent, ga.ID_SEARCHGRID,
                                       self.db_tabname, self.GetSqlColumns(), idGrid=idGrid)


# ------------------------------------------------------------------------------


class CliForSearchResultsGrid(ga.SearchResultsGrid):

    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        try:
            tipo=self.Parent.Parent.Parent.Parent.pdctipo
        except:
            tipo=''
        fields= (
            ( 50, (cn('pdc_codice'),     "Cod.",            _STR, True )),
            ( 30, (cn('tipana_codice'),  "T.",              _STR, True )),
            (325, (cn('pdc_descriz'),    "Ragione sociale", _STR, True )),
            (180, (cn('anag_indirizzo'), "Indirizzo",       _STR, True )),
            ( 50, (cn('anag_cap'),       "CAP",             _STR, True )),
            (140, (cn('anag_citta'),     "Città",           _STR, True )),
            ( 30, (cn('anag_prov'),      "Pr.",             _STR, True )),
            ( 80, (cn('anag_piva'),      "P.IVA",           _STR, True )),
            (110, (cn('anag_codfisc'),   "Cod.Fiscale",     _STR, True )),
            (150, (cn('anag_numtel'),    "Telefono",        _STR, True )),
            (150, (cn('anag_numfax'),    "FAX",             _STR, True )),
            (200, (cn('anag_email'),     "e-mail",          _STR, True )),
        )
        l = list(fields)
        if tipo=='C':
            try:
                from fatturapa_ver import VERSION_STRING
                if VERSION_STRING >= '1.1.17':
                    l.append( [200, (cn('anag_ftel_pec'),     "pec x fatt.Elettroniche",          _STR, True )])
                    l.append( [ 80, (cn('anag_ftel_codsdi'),  "Cod.SDI",      _STR, True )])
            except:
                pass
        l.append([  1, (cn('pdc_id'),         "#pdc",            _STR, True )])
        fields = tuple(l)
        return fields
     
    def SetColumn2Fit(self):
        self.SetFitColumn(2)
