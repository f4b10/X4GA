#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/layout/gestanag.py
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
from wx.lib import masked

import MySQLdb

import awc
import awc.util
import awc.controls.linktable as linktable
import awc.controls.radiobox  as radiobox
import awc.controls.checkbox  as checkbox
import awc.controls.textctrl  as textctrl
import awc.controls.numctrl   as numctrl
import awc.controls.datectrl  as datectrl
import awc.controls.entries   as entries

import awc.layout.images as awlimg
import awc.controls.images as awcimg

from gestanag_wdr import *

from Env import Azienda, GetUserMaxSqlCount
bt = Azienda.BaseTab

from awc.util import GetNamedChildrens
from awc.util import MsgDialog
from awc.util import MsgDialogDbError
from awc.util import AskForDeletion

from awc.tables.util import CheckRefIntegrity

import os
import sys
import string
import time

import stormdb as adb
import report as rpt

from awc.controls.attachbutton import EVT_ATTACHSMODIFIED

import awc.controls.windows as aw

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import sync.manager as manager

#variabile globale che imposta la presentazione automatica o meno
#dei risultati della ricerca anagrafica una volta presentata la finestra
#di gestione

SEARCH_ON_SHOW = False
def SearchOnShow(sos=True):
    global SEARCH_ON_SHOW
    SEARCH_ON_SHOW = sos


#per le tabelle semplici (codice, descrizione e poco altro) si rischia di
#avere uno spazio troppo ristretto (verticalmente) per la zona destinata
#algrid dei risultati della ricerca.
MINIMUM_FRAME_HEIGHT = 444


(AcceptDataChanged, EVT_ACCEPTDATACHANGED) = wx.lib.newevent.NewEvent()


NEW_RECORD = -1

ID_BITMAP_ORDERUP = 8
ID_BITMAP_ORDERDOWN = 9


PAGE_ELENCO = 0
PAGE_SCHEDA = 1

class SearchResultsGrid(dbglib.DbGridColoriAlternati):

    tableClass = None

    def __init__(self, parent, id, table, fields, **kwargs):


        idGrid=None
        if 'idGrid' in kwargs:
            idGrid=kwargs.pop('idGrid')            
            
        dbglib.DbGridColoriAlternati.__init__(self, parent, id,
                                              size=parent.GetClientSizeTuple(),
                                              tableClass=self.tableClass,
                                              style=0,
                                              idGrid=idGrid)
        self.tabalias = table

        cols = fields.split(',')
        for n, col in enumerate(cols):
            if ' AS ' in col.upper():
                cols[n] = col[:col.upper().index(' AS ')]
            elif ' ~AS ' in col.upper():
                cols[n] = col[col.upper().index(' ~AS ')+5:]
            cols[n] = cols[n].strip()
        fields = ','.join(cols)
        fields = fields.replace('.', '_')
        fields = fields.replace(' ', '')
        self.db = adb.DbMem(fields=fields)

        if 'status_hidesearch' in self.db.GetFieldNames():
            col = self.db._GetFieldIndex('status_hidesearch')
            self.AddConditionalColor(col, 1, fg='yellow', bg='burlywood')

        cols = self.GetDbColumns()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]

        canedit = False
        canins = False

        self.SetData((), colmap, canedit, canins)

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.SetColumn2Fit()
        
        
        
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        #self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)

    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 60, (cn(tab+'_codice'),  "Codice",      _STR, True )),
                (200, (cn(tab+'_descriz'), "Descrizione", _STR, True )),
                (  1, (cn(tab+'_id'),      "#rec",        _STR, True )),
            )

    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class FiltersDialog(aw.Dialog, awc.util.LimitiFiltersMixin):

    def __init__(self, *args, **kwargs):
        mainpanel = kwargs.pop('mainpanel')
        aw.Dialog.__init__(self, *args, **kwargs)
        panel = mainpanel.GetSpecializedSearchPanel(self)
        bs = wx.BoxSizer( wx.HORIZONTAL )
        br = wx.Button(panel, -1, "Reset", wx.DefaultPosition, wx.DefaultSize)
        br.SetName( "_btnreset" )
        bs.Add(br, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        bu = wx.Button(panel, -1, "Torna", wx.DefaultPosition, wx.DefaultSize)
        bu.SetName( "_btnundo" )
        bs.Add(bu, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        bf = wx.Button(panel, -1, "Applica", wx.DefaultPosition, wx.DefaultSize)
        bf.SetDefault()
        bf.SetName( "_btnfilter" )
        bs.Add(bf, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        panel.GetSizer().Add(bs, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.AddSizedPanel(panel)
        cdb = lambda x: wx.TheColourDatabase.Find(x)
        self.SetBackgroundColour(cdb('honeydew'))
        tit = self.FindWindowByName('searchresultstitle')
        if tit:
            tit.SetForegroundColour(cdb('black'))
            tit.SetBackgroundColour(cdb('seagreen3'))
        self.Layout()
        size = mainpanel.GetSize()
        pos = list(self.GetPosition())
        pos[1] += 40
        self.SetPosition(pos)
        self.SetSize((size[0], self.GetSize()[1]+40))
        awc.util.LimitiFiltersMixin.__init__(self)
        for ctr, func in ((br, self.OnLimitiFiltersReset),
                          (bu, self.OnUndo),
                          (bf, self.OnFilter)):
            self.Bind(wx.EVT_BUTTON, func, ctr)

    def OnUndo(self, event):
        self.EndModal(wx.ID_ABORT)

    def OnFilter(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class OrderDialog(wx.Dialog):

    def __init__(self, *args, **kwargs):
        orders, actual = map(kwargs.pop, ('orders', 'actual'))
        wx.Dialog.__init__(self, *args, **kwargs)
        p = aw.Panel(self, -1)
        rb = wx.RadioBox(p, ID_SEARCHNUM, "Ordina per:",
                         wx.DefaultPosition, wx.DefaultSize,
                         orders, 1, wx.RA_SPECIFY_COLS)
        SeachOrderFunc(p)
        self.FindWindowById(ID_SEARCHNUM).SetSelection(actual)
        self.Fit()
        self.Bind(wx.EVT_COMMAND_RIGHT_DCLICK, self.OnSelected, id=ID_SEARCHNUM)
        self.Bind(wx.EVT_BUTTON, self.OnSelected, id=ID_BTNORDER)

    def OnSelected(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class CopyFromPanel(aw.Panel):

    def __init__(self, *args, **kwargs):
        linktable_class_cb = kwargs.pop('linktable_class_cb')
        linktable_tab_name = kwargs.pop('linktable_tab_name')
        linktable_dlgclass = kwargs.pop('linktable_dlgclass')
        linktable_last_ins = kwargs.pop('linktable_last_ins')
        aw.Panel.__init__(self, *args, **kwargs)
        lt_class = linktable_class_cb()
        lt1 = lt_class(self, ID_LINKTAB1)
        lt2 = lt_class(self, ID_LINKTAB2)
        for n, lt in enumerate((lt1, lt2)):
            lt.SetDataLink(linktable_tab_name, "id_sel%d"%(n+1), linktable_dlgclass)
        if linktable_last_ins is not None:
            lt1.SetValue(linktable_last_ins)
        CopyFromFunc(self)
        self.TestLinkTables()
        self.Bind(wx.EVT_RADIOBOX, self.OnTestLinkTables, id=ID_COPYFROM)
        self.Bind(wx.EVT_BUTTON, self.OnDoCopy, id=ID_BUTCOPY)

    def OnTestLinkTables(self, event):
        self.TestLinkTables()

    def TestLinkTables(self):
        cn = self.FindWindowByName
        cf = cn('copyfrom').GetValue()
        e = cf == 'S'
        c = cn('id_sel2')
        c.Enable(e)
        if e:
            c.SetFocus()

    def Validate(self):
        out = True
        return out

    def OnDoCopy(self, event):
        if self.Validate():
            event.Skip()


# ------------------------------------------------------------------------------


class CopyFromDialog(aw.Dialog):

    def __init__(self, *args, **kwargs):
        linktable_class_cb = kwargs.pop('linktable_class_cb')
        linktable_tab_name = kwargs.pop('linktable_tab_name')
        linktable_dlgclass = kwargs.pop('linktable_dlgclass')
        linktable_last_ins = kwargs.pop('linktable_last_ins')
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = CopyFromPanel(self,
                                   linktable_class_cb=linktable_class_cb,
                                   linktable_tab_name=linktable_tab_name,
                                   linktable_dlgclass=linktable_dlgclass,
                                   linktable_last_ins=linktable_last_ins)
        for c in aw.awu.GetAllChildrens(self.panel):
            if hasattr(c, 'Bind'):
                c.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_BUTTON, self.OnDoCopy, id=ID_BUTCOPY)
        self.Fit()

    def OnChar(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_NO)
        event.Skip()

    def GetIdCopy(self):
        cn = self.FindWindowByName
        if cn('copyfrom').GetValue() == 'U':
            name = 'id_sel1'
        else:
            name = 'id_sel2'
        return cn(name).GetValue()

    def OnDoCopy(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class AnagPanel(aw.Panel):
    """
    Panel per la gestione di tabelle di tipo anagrafico.
    Da subclassare.
    """
    needSync = None
    autoCode = None
    dDefaultValue={}

    def __init__(self, parent, id=None, pos = wx.DefaultPosition,\
                 size = wx.DefaultSize):

        if id is None:
            id = wx.NewId()

        try:

            wx.BeginBusyCursor()

            aw.Panel.__init__(self, parent, id, pos, size)

            self.db_conn = Azienda.DB.connection
            self.db_curs = None

            self.db_schema = ""
            self.db_tabname = ""
            self.db_tabdesc = ""
            self.db_tabconstr = ()

            self.db_columns = []
            self.db_datalink = []
            self.db_datacols = []
            self.db_rs = []
            self.db_recno = None
            self.db_recno_old = 0
            self.db_recid = None
            self.db_tabprefix = ""
            self.db_last_inserted_id = None

            self.db_ordercolumns = None
            self.db_searchordnum = 0
            self.db_orderdirection = 0

            self.db_searchfilter = None

            self.db_filtersexpr = None
            self.db_filterspars = None

            self.db_filter = None
            self.db_parms = []
            self.db_report = None

            self._oricod = None
            self._orides = None

            self._sqlrelcol = ""
            self._sqlrelfrm = ""
            self._sqlrelwhr = ""

            #variabili per gestione pannello filtri ricerca
            #per il funzionamento vedi classi anag.pdc, anag.clienti
            self._valfilters = {}    #colonna db, val1, val2
            self._nulfilters = {}    #valori da non considerare in filtro
            self._cntfilters = []    #elenco campi di ricerca x contenuto
            self._hasfilters = False

            self.datachanged = False
            self.acceptDataChanged = True

            self.firstfocus = 'codice'

            self.autoCode = False
            self.complete = True
            self.onecodeonly = None
            self.valuesearch = False
            self.valuesearchvalues = []

            self._panelsplit = None
            self._paneltb = None
            self._panelcard = None
            self._gridsrc = None
            self._btnattach = None

        finally:
            wx.EndBusyCursor()

        try:
            self.db_curs = self.db_conn.cursor()

        except MySQLdb.Error, e:
            MsgDialog(self,
                      message="Problema durante l'accesso al database.\n\n%s: %s"
                      % (e.args[0], e.args[1]),
                      caption = "X4 :: Errore di accesso",
                      style=wx.YES_CANCEL|wx.ICON_EXCLAMATION)

        self.Bind(EVT_ACCEPTDATACHANGED, self.OnAcceptDataChanged)

        self.SyncManager=manager.SyncManager()
        if bt.SYNCFLAG==1:
            if self.SyncManager.IsMaster():
                self.SyncManager.RemoveOldUpdate()


    def SetAutoCode(self, autocode=False):
        if autocode:
            self.firstfocus = 'descriz'
        self.autoCode = autocode

    def BeforeDeleteRecord(self):
        pass

    def AfterDeleteRecord(self):
        if self.SyncManager.NeedStore2Sync(self.db_tabname):
            self.SyncManager.StoreUpdate(op='DELETE', \
                                      dbTable=self.db_tabname, \
                                      recId=self.db_recid)

    def BeforeInsertRecord(self):
        if self.SyncManager.NeedStore2Sync(self.db_tabname):
            self.recNew=[]
            for col,ctr in self.db_datalink:
                self.recNew.append(ctr.GetValue())

    def AfterInsertRecord(self, recid):
        if self.SyncManager.NeedStore2Sync(self.db_tabname):
            for i, (col,ctr) in enumerate(self.db_datalink):
                if col=='id':
                    self.recNew[i]=recid
                    break
            self.SyncManager.StoreUpdate(op='INSERT', \
                                      dbTable=self.db_tabname, \
                                      recNew=self.recNew, \
                                      dataLink=self.db_datalink)

    def BeforeUpdateRecord(self):
        if self.SyncManager.NeedStore2Sync(self.db_tabname):
            self.recOld=self.db_rs[self.db_recno]
            #print 'tabella %s UPDATE (before)' % self.db_tabname

    def AfterUpdateRecord(self, dbvalues):
        if self.SyncManager.NeedStore2Sync(self.db_tabname):
            #print 'tabella %s UPDATE (after)' % self.db_tabname
            self.recNew=dbvalues
            for i, (col,ctr) in enumerate(self.db_datalink):
                if not ctr.GetValue()==self.recOld[i]:
                    self.SyncManager.StoreUpdate(op='UPDATE', \
                                              dbTable=self.db_tabname, \
                                              recNew=self.recNew, \
                                              dataLink=self.db_datalink)
                    break


    def IsGestioneClientiFornitori(self):
        lReturn = False
        try:
            import contab.pdcint
            if isinstance(self, contab.pdcint.ClientiInterrPanel):
                lReturn = True
        except:
            pass
        return lReturn




    def OnAcceptDataChanged(self, event):
        if "acceptchanges" in dir(event):
            flag = event.acceptchanges
        else:
            flag = True
        self.acceptDataChanged = flag
        if True:#hasattr(event, 'resetchanges'):
            self.SetDataChanged(False)
        event.Skip()

    def SetOneCodeOnly(self, code):
        self.onecodeonly = code
        self.complete = False

    def SetValueSearch(self, vs=True):
        self.valuesearch = vs

    def InitControls(self):

        father = awc.util.GetParentFrame(self)

        #l'intero panel è controllato da un flexgrid sizer verticale
        sizer = wx.FlexGridSizer( 0, 1, 0, 0 )
        sizer.AddGrowableCol( 0 )
        sizer.AddGrowableRow( 1 )

        #a seconda del tipo di azione, cambia il componente di testa
        if self.complete:
            #gestione completa: toolbar
            panel = self.InitAnagToolbar(self)
            panel.win = self
            self._paneltb = panel
            sizer.Add(panel, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5)
        else:
            #una scheda sola: barra descrittiva
            cardtitle = self.db_tabdesc
            if self.valuesearch:
                cardtitle += " - Cerca valori"
            elif self.onecodeonly is None:
                cardtitle += " - Nuovo"
            tp = AnagPanel.TitlePanel(self, cardtitle)
            sizer.Add(tp, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|\
                      wx.LEFT|wx.RIGHT|wx.TOP, 0 )
            if self.valuesearch:
                c = self.FindWindowById(ID_BITMAPCARD)
                bmp = awcimg.getFilter16Bitmap()
                c.SetBitmap(bmp)

        #choicebook contenente la lista e la scheda
        cb = wx.Choicebook(self, -1)
        cb.SetName('elescheda')
        #pannello risultati ricerca
        panel = self.GetSearchResultsPanel(cb)
        cb.AddPage(panel, 'Elenco')
        #pannello anagrafico vero e proprio
        panel = self.InitCardPanel(cb)
        cb.AddPage(panel, 'Scheda')
        #panel.Fit()
        sizer.Add(cb, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 0)

        def OnElencoScheda(event):
            if self.db_recno == NEW_RECORD:
                return
            if event.GetSelection() == 1 and self._gridsrc:
                if not 'schedachanging' in dir(self):
                    self.schedachanging = False
                if not self.schedachanging:
                    self.schedachanging = True
                    self.UpdateDataControls(self._gridsrc.GetSelectedRows()[0])
                    del self.schedachanging
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, OnElencoScheda, cb)
        def OnElencoSchedaOk(event):
            self.UpdateButtonsState()
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, OnElencoSchedaOk, cb)

        if not self.complete:
            #setto pagina scheda
            cb.SetSelection(1)
            #una sola scheda: mancano i bottoni di azione sul recordset,
            #aggiungo il bottone per confermare i dati
            if self.valuesearch:
                bl = 'Cerca'
                func = self.OnValueSearch
                sa = False
            else:
                bl = 'Salva'
                func = self.OnRecordSave
                sa = True
            #sizer verticale bottoni in basso
            bsz = wx.FlexGridSizer(1,0,0,0)
            bsz.AddGrowableCol(0)
            #sizer bottoni azzera/ricorda selezioni x cerca valori
            blsz = wx.FlexGridSizer(1,0,0,0)
            blsz.AddGrowableCol(0)
            ID_BUTAZZ = wx.NewId()
            bazz = wx.Button(self, ID_BUTAZZ, "&Elimina selezioni",
                             wx.DefaultPosition, wx.DefaultSize, 0)
            bazz.SetName('resetvaluesearch')
            bazz.Show(self.valuesearch)
            blsz.Add(bazz, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            ID_BUTRIC = wx.NewId()
            bric = wx.ToggleButton(self, ID_BUTRIC, "&Ricorda selezioni",
                                   wx.DefaultPosition, wx.DefaultSize, 0)
            bric.SetName('fixvaluesearch')
            bric.Show(self.valuesearch)
            blsz.Add(bric, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
            bsz.Add(blsz, 0, wx.ALIGN_CENTER, 5)
            ID_BUTSOS = wx.NewId()
            btnsos = wx.Button(self, ID_BUTSOS, bl)
            bsz.Add(btnsos, 0, wx.ALIGN_CENTER|wx.RIGHT|wx.TOP|wx.BOTTOM, 5)
            self.SetDefaultItem(btnsos)
            if sa:
                self.SetAcceleratorKey('S', ID_BUTSOS, None, 'Salva le informazioni digitate')
            sizer.Add(bsz, 0, \
                      wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnValueSearchReset, bazz)
            self.Bind(wx.EVT_BUTTON, func, btnsos)

        #bindings toolbar (o tasto di conferma)
        for cid, func in ((ID_BTN_RECFIRST,    self.OnRecordFirst),
                          (ID_BTN_RECPREVIOUS, self.OnRecordPrevious),
                          (ID_BTN_RECNEXT,     self.OnRecordNext),
                          (ID_BTN_RECLAST,     self.OnRecordLast),
                          (ID_BTN_RECSAVE,     self.OnRecordSave),
                          (ID_BTN_RECUNDO,     self.OnRecordUndo),
                          (ID_BTN_RECNEW,      self.OnRecordNew),
                          (ID_BTN_COPYFROM,    self.OnCopyFrom),
                          (ID_BTN_RECDELETE,   self.OnRecordDelete),
                          (ID_SEARCHBTN,       self.OnUpdateSearch),
                          (ID_SEARCHORD,       self.OnSearchOrder),
                          (ID_BTNFILTERS,      self.OnCallFilters),
                          (ID_BTNVALSRC,       self.OnCallValueSearch),
                          (ID_BTNPRINT,        self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)

        if self.complete:

            self.FindWindowById(ID_BTN_RECNEW).Bind(wx.EVT_RIGHT_UP, self.OnCopyToDuplicate)

            self.SetAcceleratorKey('V', ID_SSV,             'SSV',   'Abilita o disabilita la visualizzazione degli elementi con status nascosto')
            self.SetAcceleratorKey('C', ID_SEARCHBTN,       'Cerca', 'Cerca quanto digitato')
            self.SetAcceleratorKey('O', ID_SEARCHORD,       None,    'Cambia l\'ordinamento dell\'elenco risultati')
            self.SetAcceleratorKey('F', ID_BTNFILTERS,      None,    'Imposta la maschera di filtro')
            self.SetAcceleratorKey('E', ID_BTNVALSRC,       None,    'Imposta la maschera del cerca valori')
            self.SetAcceleratorKey('I', ID_BTN_RECNEW,      None,    'Inserisce un nuovo elemento')
            self.SetAcceleratorKey('Y', ID_BTN_COPYFROM,    None,    'Consente di copiare le informazioni da un altro elemento a scelta')
            self.SetAcceleratorKey('S', ID_BTN_RECSAVE,     None,    'Salva l\'elemento corrente')
            self.SetAcceleratorKey('X', ID_BTN_RECDELETE,   None,    'Elimina l\'elemento corrente')
            self.SetAcceleratorKey('Q', ID_BTN_RECUNDO,     None,    'Abbandona le modifiche effettuate')
            self.SetAcceleratorKey('1', ID_BTN_RECFIRST,    None,    'Sposta sul primo elemento della lista')
            self.SetAcceleratorKey('2', ID_BTN_RECPREVIOUS, None,    'Sposta sull\'elemento precedente')
            self.SetAcceleratorKey('3', ID_BTN_RECNEXT,     None,    'Sposta sull\'elemento successivo')
            self.SetAcceleratorKey('4', ID_BTN_RECLAST,     None,    'Sposta sull\'ultimo elemento')

        if not self._hasfilters:
            c = self.FindWindowById(ID_BTNFILTERS)
            if c is not None:
                c.Show(False)
                self._paneltb.Layout()

        #bottone allegati
        self._btnattach = self.FindWindowByName('_btnattach')
        if self._btnattach is not None:
            if self.valuesearch:
                self._btnattach.Hide()
            else:
                self._btnattach.SetScope(self.db_tabname)
                self.Bind(EVT_ATTACHSMODIFIED, self.OnAttachsModified)
            c = self.FindWindowByName('_attach_autotext')
            if c:
                self._btnattach.SetAutoText(c)

        if self.SyncManager.NeedSync():
            self.SyncManager.UpdateTables()

        self.SetSizer(sizer)

        self.InitDataControls()
        self.SetControlsMaxLength(self.db_columns, self.db_datalink)

        if self.complete:
            wx.CallAfter(lambda: self.FindWindowByName('_searchval').SetFocus())

        """
        il richiamo del metodo InitControls_PersonalPage() non deve essere richiamato da qui nel caso si stiano
        gestendo clienti o fornitori. Altrimenti lo spostamenti sulla grid non aggiornerebbe conseguientemente
        gli oggetti presenti nella card.
        """
        if not self.IsGestioneClientiFornitori():
            self.InitControls_PersonalPage()

        if self.db_report == None:
            try:
                self.FindWindowById(ID_BTNPRINT).Hide()
            except:
                pass


    def InitControls_PersonalPage(self):
        pass

    def UpdateDataRecord_PersonalPage(self):
        pass

    def OnAttachsModified(self, event):
        self.SetDataChanged()
        self.UpdateButtonsState()
        event.Skip()

    def GetSpecializedSearchPanel(self, parent):
        return None

    def GetMultiEticReportName(self):
        if getattr(self, 'db_report', None):
            return '%s - Etichette' % self.db_report
        return None

    def GetSearchResultsPanel(self, parent):
        panel = aw.Panel(parent, style=wx.RAISED_BORDER)
        SearchResultsFunc(panel)
        self.InitSearchGrid()
        show = False
        be = panel.FindWindowByName('butetic')
        if be:
            if getattr(self, 'db_report', None):
                test = '%s - Etichette' % self.db_report
                import report
                tipo, nome = report.get_report(test)
                if tipo:
                    show = True
            be.Show(show)
            if show:
                self.Bind(wx.EVT_BUTTON, self.OnPrintListEtic, be)
        return panel

    def OnPrintListEtic(self, event):
        rptname = self.GetMultiEticReportName()
        if rptname:
            db = self.GetDbPrint()
            db.ShowDialog(self)
            if self.db_filter:
                db.AddFilter(self.db_filter, *self.db_parms)
            if self.db_orderdirection == 1:
                ot = adb.ORDER_DESCENDING
            else:
                ot = adb.ORDER_ASCENDING
            n = self.GetOrderNumber()
            db.ClearOrders()
            db._info.ragexpr = '1'
            db._info.ragprint = None
            for of in self.db_ordercolumns[n][1]:
                db.AddOrder(of, ot)
            if db.Retrieve():
                def GetMultiEticTable(rptdef, _rpt):
                    rows = cols = 1
                    if '(' in rptdef:
                        x = rptdef[rptdef.rindex('(')+1:]
                        if x.endswith(')'):
                            x = x[:-1]
                        if 'x' in x:
                            rows, cols = map(int,x.split('x'))
                    row0 = _rpt.GetLabelOffsetRow()
                    col0 = _rpt.GetLabelOffsetCol()
                    me = adb.dbtable.MultiEticList(db)
                    wait = aw.awu.WaitDialog(self, message="Costruzione etichette in corso.")
                    try:
                        t = me.GetPrintTable(rptdef, rows, cols, row0, col0)
                    finally:
                        wait.Destroy()
                    return t
                rpt.ReportLabels(self, db, rptname, dbfunc=GetMultiEticTable)
            else:
                MsgDialog(self, repr(db.GetError()))
        event.Skip()

    def GetSearchResultsGrid(self, parent):
        grid = SearchResultsGrid(parent, ID_SEARCHGRID,
                                 self.db_tabname, self.GetSqlColumns(), idGrid='eletab_%s' % self.db_tabname)
        return grid

    def InitSearchGrid(self):
        if not self.db_datalink:
            return
        panel = self.FindWindowById(ID_SEARCHPANGRID)
        self._gridsrc = self.GetSearchResultsGrid(panel)
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self._gridsrc, 0, wx.GROW|wx.ALL, 0)
        panel.SetSizer(sz)
        sz.SetSizeHints(panel)
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnSearchMove, id=ID_SEARCHGRID)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSearchSel, id=ID_SEARCHGRID)
        self._gridsrc.Bind(wx.EVT_KEY_DOWN, self.OnSearchTestCR)

    def OnSearchMove(self, event):
        if self.complete:
            self.FindWindowById(ID_NUMRECFIRST).SetLabel(str(event.GetRow()+1))
        event.Skip()

    def OnSearchTestCR(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.UpdateDataControls(self._gridsrc.GetSelectedRows()[0])
            self.DisplayScheda()
        else:
            event.Skip()

    def OnSearchSel(self, event):
        self.UpdateDataControls(event.GetRow())
        self.DisplayScheda()
        self.SetFirstFocus()
        event.Skip()

    def InitCardPanel(self, parent):
        panel = aw.Panel(parent, -1)
        sizer = wx.FlexGridSizer( 0, 1, 0, 0 )
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        self._panelcard = self.InitAnagCard(panel)
        sizer.Add( self._panelcard, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )
        panel.SetSizer(sizer)
        return panel

    def SetControlsMaxLength(self, fields, controls):
        types = 'CHAR VARCHAR'.split()
        for cname, ctype, clen, cdec, cdes, cadd in fields:
            if ctype in types and clen is not None:
                try:
                    n = aw.awu.ListSearch(controls, lambda x: x[0] == cname)
                except IndexError:
                    continue
                try:
                    controls[n][1].SetMaxLength(clen)
                except AttributeError:
                    pass

    def InitAnagToolbar(self, parent):
        return AnagToolbar(parent, -1)

    def InitAnagCard(self, parent):
        return AnagCard( parent, -1 )

    def InitDataControls( self, update=True ):
        """
        Inizializza la lista dei controlli legati ai dati
        Aggiunge workaround per problemi di visualizzazione in caso di resize
        del frame
        """
        controls = GetNamedChildrens( self, [ col[0] \
                                              for col in self.db_columns ])
        self.db_datalink += [ ( ctr.GetName(), ctr ) for ctr in controls ]
        self.db_datacols = [ col for col,ctr in self.db_datalink ]

        for col, ctr in self.db_datalink:
            if isinstance(ctr, wx.Window):
                self.BindChangedEvent(ctr)
            if col in 'codice descriz'.split():
                ctr.Bind(wx.EVT_LEFT_DCLICK, self.OnCodDesDoubleClick)

        cb = self.FindWindowByName('elescheda')
        p = cb.GetPage(0)
        p.SetName('main#searchresults')
        #p.HelpBuilder_SetDir('ui.anaglayout.searchresults')
        p = cb.GetPage(1)
        l = list(p.GetChildren())
        if len(l) == 1 and isinstance(l[0], wx.Panel):
            p = l[0]
        p.SetName('main#schedapanel')

        self.InitSearchGrid()

        if update and SEARCH_ON_SHOW:
            self.UpdateSearch()

    def OnCodDesDoubleClick(self, event):
        obj = event.GetEventObject()
        if not obj.IsEditable():
            if aw.awu.MsgDialog(self, "Il codice e la descrizione sono al momento non editabili.\nVuoi modificarli ?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                for name in 'codice descriz'.split():
                    self.FindWindowByName(name).SetEditable(True)
        event.Skip()

    def BindChangedEvent(self, ctr):
        cc = ctr.__class__
        if   issubclass(cc, (wx.TextCtrl,\
                             numctrl.NumCtrl,\
                             datectrl.DateCtrl)):

            #self.Bind(wx.EVT_TEXT, self.OnDataChanged, ctr)
            ctr.Bind(wx.EVT_TEXT, self.OnDataChanged)

        elif issubclass(cc, entries._EntryCtrlMixin):
            #self.Bind(wx.EVT_TEXT, self.OnDataChanged, ctr.address)
            ctr.address.Bind(wx.EVT_TEXT, self.OnDataChanged)

        elif issubclass(cc, linktable.LinkTable):
            #self.Bind(linktable.EVT_LINKTABCHANGED, self.OnDataChanged, ctr)
            ctr.Bind(linktable.EVT_LINKTABCHANGED, self.OnDataChanged)

        elif issubclass(cc, wx.RadioBox):
            #self.Bind(wx.EVT_RADIOBOX, self.OnDataChanged, ctr)
            ctr.Bind(wx.EVT_RADIOBOX, self.OnDataChanged)

        elif issubclass(cc, wx.CheckBox):
            #self.Bind(wx.EVT_CHECKBOX, self.OnDataChanged, ctr)
            ctr.Bind(wx.EVT_CHECKBOX, self.OnDataChanged)

        elif issubclass(cc, wx.CheckListBox):
            #self.Bind(wx.EVT_CHECKBOX, self.OnDataChanged, ctr)
            ctr.Bind(wx.EVT_CHECKLISTBOX, self.OnDataChanged)

        elif issubclass(cc, wx.ComboBox):
            #self.Bind(wx.EVT_CHECKLISTBOX, self.OnDataChanged, ctr)
            ctr.Bind(wx.EVT_COMBOBOX, self.OnDataChanged)

        elif issubclass(cc, (datectrl.DateCtrl, datectrl.DateTimeCtrl)):
            #self.Bind(datectrl.EVT_DATECHANGED, self.OnDataChanged, ctr)
            ctr.Bind(datectrl.EVT_DATECHANGED, self.OnDataChanged)

    def OnSearch(self, event):
        self.UpdateSearch()
        event.Skip()

    def OnPrint(self, event):
        self.PrintLista()
        event.Skip()

    def OnDataChanged(self, event):
        if self.acceptDataChanged and not self.datachanged and not self.valuesearch:
            self.SetDataChanged(True, event.GetEventObject())
        event.Skip()

    def OnUpdateSearch(self, event):
        self.UpdateSearch()
        event.Skip()

    def OnSearchOrder(self, event):
        so = self.FindWindowById(ID_SEARCHORD)
        pos = so.GetPosition()
        size = so.GetSize()
        pos = (pos[0], pos[1]+size[1])
        p = so.GetParent()
        pos = p.ClientToScreen(pos)
        dlg = OrderDialog(p, -1, pos=pos, style=wx.SIMPLE_BORDER,
                          orders=[o[0] for o in self.db_ordercolumns],
                          actual=self.db_searchordnum)
        dlg.ShowModal()
        order = self.FindWindowById(ID_SEARCHNUM).GetSelection()
        senso = int(self.FindWindowById(ID_ORDERDOWN).GetValue())
        dlg.Destroy()
        if order != self.db_searchordnum or senso != self.db_orderdirection:
            self.db_searchordnum = order
            self.db_orderdirection = senso
            self.UpdateSearch()
        event.Skip()

    def OnCallValueSearch(self, event):
        print 'OnCallValueSearch'
        if self.valuesearch:
            self.valuesearchvalues = self.GetValueSearchValues()
            self.UpdateSearch()
            self.valuesearch = False
            self.UpdateButtonsState()
            self.SetValueSearchFields()
            if self.valuesearchvalues:
                bmp = awcimg.getFilterAt16Bitmap()
            else:
                bmp = awcimg.getFilter16Bitmap()
            self.SetDefaultItem(None)
        else:
            self.valuesearch = True
            self._panelcard.Enable()
            self.SetInsertMode()
            f = True
            for tab, col, val in self.valuesearchvalues:
                ctr = self.FindWindowByName(col)
                if ctr:
                    ctr.SetValue(val)
                    if f:
                        wx.CallAfter(lambda: ctr.SetFocus())
                        f = False
            bmp = awcimg.getFilter16Bitmap()
            self.SetDefaultItem(self.FindWindowById(ID_BTNVALSRC))
        self.FindWindowById(ID_BTNVALSRC).SetBitmapLabel(bmp)
        event.Skip()

    def OnCallFilters(self, event):

        if not self._hasfilters:
            return

        b = self.FindWindowById(ID_BTNFILTERS)

        p = b.GetParent()
        pos = p.ClientToScreen((0,0))
        dlg = FiltersDialog(self, -1, pos=pos, style=wx.SIMPLE_BORDER,
                          mainpanel=self)
        self.InitSearchFilters(dlg)
        if dlg.ShowModal() == wx.ID_OK:
            self.ApplySearchFilters(dlg)
            self.UpdateSearch()
        dlg.Destroy()
        event.Skip()

    def UpdateSpecFiltersButton(self):
        if self.db_filtersexpr:
            bmp = images.getSearchAt16Bitmap()
        else:
            bmp = images.getSearch16Bitmap()
        self.FindWindowById(ID_BTNFILTERS).SetBitmapLabel(bmp)

    def InitSearchFilters(self, fltwin):
        """
        Inizializza i controlli nel pannello dei filtri di ricerca.
        I valori sono recuperati dal dizionario ::_valfilters, che è
        aggiornato in fase di conferma del pannello dei filtri 'fltwin'
        """
        for ctrl in aw.awu.GetAllChildrens(fltwin):
            name = ctrl.GetName()
            vc = 1
            if name[-1] in '12':
                vc += int(name[-1])-1
                name = name[:-1]
            if name in self._valfilters:
                val = self._valfilters[name][vc]
                if val is not None:
                    ctrl.SetValue(val)

    def ApplySearchFilters(self, fltwin):
        """
        Applica i filtri impostati nel pannello dei filtri di ricerca.
        """
        flt = ''
        par = []
        cn = lambda x: fltwin.FindWindowByName(x)
        for name in self._valfilters:
            defs = self._valfilters[name]
            #cerco limiti da/a per il nome della variabile di filtro
            ctr1, ctr2 = cn(name+'1'), cn(name+'2')
            if ctr1 is None or ctr2 is None:
                #se non li trovo, non considero da/a ma unica variabile
                ctr1 = ctr2 = cn(name)
            name1, name2 = ctr1.GetName(), ctr2.GetName()
            val1, val2 = ctr1.GetValue(), ctr2.GetValue()
            defs[1], defs[2] = val1, val2
            if hasattr(ctr1, 'filter_by_descriz'):
                val1, val2 = ctr1.GetValueDes(), ctr2.GetValueDes()
            elif hasattr(ctr1, 'GetValueCod'):
                val1, val2 = ctr1.GetValueCod(), ctr2.GetValueCod()
            if val1 == val2 and val1:
                if name in self._nulfilters and val1 in self._nulfilters[name]:
                    continue
                if flt: flt += " AND "
                if name in self._cntfilters:
                    #ricerca x contenuto di stringa
                    flt += "%s LIKE %%s" % defs[0]
                    val1 = '%%%s%%' % val1
                else:
                    #ricerca x valore esatto
                    flt += "%s=%%s" % defs[0]
                par.append(val1)
            else:
                if val1:
                    if not (name in self._nulfilters
                            and val1 in self._nulfilters[name]):
                        if flt: flt += " AND "
                        flt += "%s>=%%s" % defs[0]
                        par.append(val1)
                if val2:
                    if not (name in self._nulfilters
                            and val1 in self._nulfilters[name]):
                        if flt: flt += " AND "
                        flt += "%s<=%%s" % defs[0]
                        par.append(val2)
        self.db_filtersexpr, self.db_filterspars = flt, par
        return flt, par

    def OnRecordFirst(self, event):
        if self.MoveRecordFirst():
            event.Skip()

    def OnRecordPrevious(self, event):
        if self.MoveRecordPrevious():
            event.Skip()

    def OnRecordNext( self, event ):
        if self.MoveRecordNext():
            event.Skip()

    def OnRecordLast( self, event ):
        if self.MoveRecordLast():
            event.Skip()

    def MoveRecordFirst(self):
        if not self.TestForChanges():
            return False
        ok = len(self.db_rs)>0
        if ok:
            self.UpdateDataControls(0)
        return ok

    def MoveRecordPrevious(self):
        if not self.TestForChanges():
            return False
        ok = 0 < self.db_recno < len(self.db_rs)
        if ok:
            self.UpdateDataControls(self.db_recno-1)
        return ok

    def MoveRecordNext(self):
        if not self.TestForChanges():
            return False
        ok = 0 <= self.db_recno < len(self.db_rs)-1
        if ok:
            self.UpdateDataControls(self.db_recno+1)
        return ok

    def MoveRecordLast(self):
        if not self.TestForChanges():
            return False
        ok = len(self.db_rs)>0 and self.db_recno < len(self.db_rs)-1
        if ok:
            self.UpdateDataControls(len(self.db_rs)-1)
        return ok

    def OnRecordSave( self, event ):
        if self.UpdateDataRecord():
            if not self.complete:
                f = awc.util.GetParentFrame(self)
                if issubclass(f.__class__, wx.Dialog) and f.IsModal():
                    f.EndModal(self.db_recid)
        event.Skip()

    def OnValueSearch(self, event):
        if not self.complete:
            f = awc.util.GetParentFrame(self)
            if issubclass(f.__class__, wx.Dialog) and f.IsModal():
                f.EndModal(wx.ID_OK)
        event.Skip()

    def OnValueSearchReset(self, event):
        if not self.complete:
            f = awc.util.GetParentFrame(self)
            if issubclass(f.__class__, wx.Dialog) and f.IsModal():
                f.EndModal(wx.ID_RESET)
        event.Skip()

    def OnRecordUndo( self, event ):
        self.LoadFieldsValues()
        event.Skip()

    def LoadFieldsValues(self):
        self.valuesearch = False
        self.SetValueSearchFields()
        self.db_recno = self.db_recno_old
        self.UpdateDataControls(self.db_recno)
        self.SetDataChanged(False)

    def OnRecordNew( self, event ):
        self.SetInsertMode()
        self._panelcard.Enable()
        event.Skip()

    def OnCopyFrom(self, event):
        so = self.FindWindowById(ID_BTN_COPYFROM)
        pos = so.GetPosition()
        size = so.GetSize()
        pos = (pos[0], pos[1]+size[1])
        p = so.GetParent()
        pos = p.ClientToScreen(pos)
        dlg = CopyFromDialog(p, -1, pos=pos, style=wx.SIMPLE_BORDER,
                             linktable_class_cb=self.GetLinkTableClass,
                             linktable_tab_name=self.db_tabname,
                             linktable_dlgclass=None,
                             linktable_last_ins=self.CopyFrom_GetLastInserted())
        idcopy = None
        wx.CallAfter(lambda: dlg.FindWindowByName('copyfrom').SetFocus())
        if dlg.ShowModal() == wx.ID_OK:
            idcopy = dlg.GetIdCopy()
        dlg.Destroy()
        if idcopy is not None:
            self.CopyFrom_DoCopy(idcopy)
        event.Skip()

    def CopyFrom_GetLastInserted(self):
        lastid = self.db_last_inserted_id
        if lastid is None:
            db = adb.db.__database__
            if db.Retrieve('SELECT MAX(id) FROM %s' % self.db_tabname):
                if len(db.rs) == 1:
                    lastid = db.rs[0][0]
        return lastid

    def CopyFrom_DoCopy(self, idcopy):
        db = adb.DbTable(self.db_tabname, 'tab')
        if db.Get(idcopy) and db.OneRow():
            for name in db.GetFieldNames():
                if name != 'id':
                    try:
                        n = aw.awu.ListSearch(self.db_datalink, lambda x: x[0] == name)
                        v = getattr(db, name)
                        if v is not None:
                            self.db_datalink[n][1].SetValue(v)
                    except IndexError:
                        pass
            self.TestRecordValuesAfterCopy(idcopy)
            self.SetFirstFocus()
            return True
        return False

    def OnCopyToDuplicate(self, event):
        if self.db_recid is not None:
            self.CopyTo_Duplicate()
            if self.db_recid is None:
                aw.awu.MsgDialog(self, "Stai lavorando su un record duplicato, effettua le modifiche", style=wx.ICON_INFORMATION)
        event.Skip()

    def CopyTo_Duplicate(self):

        out = False

        if self.db_recid is not None:

            idcopy = self.db_recid
            self.SetInsertMode()
            self._panelcard.Enable()

            out = self.CopyFrom_DoCopy(idcopy)

        return out

    def TestRecordValuesAfterCopy(self, idcopyfrom):
        pass

    def GetLinkTableClass(self):
        return linktable.LinkTable

    def OnRecordDelete( self, event ):
        if self.CanUpdate():
            out = False
            if self.db_recno >= 0:
                if self.TestForDeletion() and AskForDeletion(self):
                    out = self.DeleteDataRecord()
                    if out:
                        try:
                            self._btnattach.SetKey(self.db_recid, delete=True)
                        except:
                            pass
                    self.UpdateSearch()
                    event.Skip()
        else:
            self.ViewMessageRifiuto()
            out=False
        return out

    def SetInsertMode(self):
        self.UpdateDataControls(NEW_RECORD)
        self.UpdateButtonsState()
        self.SetValueSearchFields()
        if not self.valuesearch:
            self.SetDefaultsFromFilters()
        self.InsertingRecord()
        self.SetFirstFocus()
        return True

    def InsertingRecord(self):
        pass

    def SetValueSearchFields(self, dl=None):
        if self.valuesearch:
            bg = wx.TheColourDatabase.Find('darkseagreen3')
        else:
            bg = None
        if dl is None:
            dl = self.db_datalink
        for col, ctr in dl:
            try:
                ctr.SetDynColor('focusedBackground', bg)
            except AttributeError:
                pass
            if isinstance(ctr, wx.RadioBox):
                ctr.Enable(not self.valuesearch)
            #else:
                #if self.valuesearch:
                    #ctr.Enable()
        if self.complete:
            for cid in (ID_SEARCHVAL, ID_SEARCHBTN, ID_SEARCHORD):
                self.FindWindowById(cid).Enable(not self.valuesearch)

    def GetValueSearchValues(self):
        vsf = []
        if self.valuesearch:
            for n, (col, ctr) in enumerate(self.db_datalink):
                if isinstance(ctr, (wx.RadioBox, wx.CheckBox, wx.ComboBox)):
                    continue
                if type(ctr) in (str, unicode):
                    value = getattr(self, ctr)
                else:
                    value = ctr.GetValue()
                if value:
                    vsf.append((self.db_tabname, col, value))
        return vsf

    def SetDefaultsFromFilters(self):
        """
        Inizializza i controlli relativi ai filtri di ricerca.
        I valori dei filtri sono impostati in __init__ ed aggiornati in fase
        di conferma del frame di impostazione filtri ricerca.
        Se il controllo relativo è sdoppiato x permettere i limiti da/a,
        viene considerato il controllo del limite 'da'
        """
        cn = lambda x: self.FindWindowByName(x)
        for name in self._valfilters:
            col, v1, v2 = self._valfilters[name]
            val = v1 or v2
            ctr = cn(name)
            if ctr is None:
                ctr = cn('id_'+name)
            if ctr:
                ctr.SetValue(val)

        if self.db_recno == NEW_RECORD:
            if len(self.dDefaultValue.keys())>0:
                for k in self.dDefaultValue.keys():
                    self.FindWindowByName(k).SetValue(self.dDefaultValue[k])

    def TestForChanges(self):
        """
        Verifica che non ci siano editazioni attive sul record gestito.
        """
        do = True
        if self.datachanged:
            msg =\
            """Le informazioni digitate non sono state salvate.\n"""\
            """Salvo tali informazioni prima di procedere?"""
            do = False
            r = aw.awu.MsgDialog(self, msg, caption="Conferma modifiche", style=wx.ICON_QUESTION|wx.YES_NO|wx.CANCEL|wx.YES_DEFAULT)
            if r == wx.ID_YES:
                do = self.UpdateDataRecord()
            elif r == wx.ID_NO:
                do = True
        return do

    def TestForDeletion( self ):
        """
        Metodo per la verifica della cancellabilità di un elemento.
        """
        return CheckRefIntegrity( self,
                                  self.db_curs,
                                  self.db_tabconstr,
                                  self.db_recid )




    def DeleteDataRecord( self ):
        out = False
        try:
            self.BeforeDeleteRecord()
            self.db_curs.execute( "DELETE FROM %s%s WHERE id=%d;"
                                  % ( self.db_schema,
                                      self.db_tabname,
                                      self.db_recid ) )
            self.AfterDeleteRecord()
            self.db_rs = self.db_rs[:self.db_recno] +\
                         self.db_rs[self.db_recno+1:]
            if self.db_recno > len(self.db_rs)-1:
                self.db_recno = len(self.db_rs)-1
            if self.db_rs:
                if "id" in self.db_datacols:
                    pkcol = self.db_datacols.index("id")
                else:
                    raise Exception,\
                          """Manca il controllo relativo all'id del record"""
                self.db_recid = int(self.db_rs[self.db_recno][pkcol])
            else:
                self.db_recid = None
            out = True

        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)

        return out

    def BeforeUpdateDataRecord(self):
        pass


    def ViewMessageRifiuto(self):
        MsgDialog(self,\
    """Non si detengono i diritti per poter modificare la scheda.\n"""\
    """Le modifiche apportate non saranno pertanto memorizzate.""",
    style = wx.ICON_STOP )
        

    def CanUpdate(self):
        canUpdate=True
        try:
            if self.db_tabname=="prod":
                if not (Azienda.Login.userdata.can_updprod==1):
                    canUpdate=False
            else:
                try:
                    if self.tabanag=="clienti":
                        if not (Azienda.Login.userdata.can_updcli==1):
                            canUpdate=False
                except:
                    canUpdate=True
        except:
            canUpdate=True
        return canUpdate        

    def UpdateDataRecord( self ):
        """
        Memorizzazione dati del record: il metodo effettua la validazione di tutti
        i controlli del dialog.  I controlli che hanno dato esito negativo alla
        validazione vengono messi con colore di background rosso.
        Se tutti i controlli hanno dato esito positivo alla validazione, viene
        richiamato il metodo L{self.TransferDataFromWindow}
        """

            
        if self.CanUpdate():
            self.BeforeUpdateDataRecord()
            written = False
            newcod, newdes = map(lambda x: self.FindWindowByName(x).GetValue(),
                                 ('codice', 'descriz'))
            if self.db_recno != NEW_RECORD and self._oricod is not None and self._orides is not None:
                if newcod != self._oricod or newdes != self._orides:
                    msg = "Attenzione\n\nSto per variare i seguenti dati dell'elemento esistente:\n"
                    msg += "Prima della modifica:\ncodice=%s, descrizione=%s\n" % (self._oricod, self._orides)
                    msg += "Dopo la modifica:\ncodice=%s, descrizione=%s\n\n" % (newcod, newdes)
                    msg += "Confermi la variazione ?"
                    style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
                    if MsgDialog(self, message=msg, style=style) != wx.ID_YES:
                        return False
            COLOR_NORMAL = wx.NullColour
            COLOR_ERROR = wx.RED
            valid = True
            for col,ctr in self.db_datalink:
                if isinstance(ctr, wx.Window):
                    if ctr.Validate():
                        ctr.SetBackgroundColour(COLOR_NORMAL)
                    else:
                        ctr.SetBackgroundColour(COLOR_ERROR)
                        ctr.Refresh()
                        valid = False
            if valid:
                if self.TransferDataFromWindow():
                    #TODO AGGIUNTA PER MEMORIZZARE DATI NELLE TABELLE LINKATE
                    self.UpdateDataRecord_PersonalPage()
                    self.UpdateDataControls( self.db_recno )
                    self._oricod, self._orides = newcod, newdes
                    written = True
            else:
                MsgDialog(self,\
    """Sono presenti valori non validi.  Correggere le parti evidenziate per """\
    """continuare.  I dati non sono stati salvati.""" )
    
        else:
            self.ViewMessageRifiuto()
            self.LoadFieldsValues()
            written = True
        return written

    def TransferDataFromWindow( self ):
        out = False

        if self.db_recno is None: self.db_recno = NEW_RECORD

        dbvalues = list()
        colid = -1
        for n, (col, ctr) in enumerate(self.db_datalink):
            if type(ctr) in (str, unicode):
                value = getattr(self, ctr)
            else:
                value = ctr.GetValue()
            dbvalues.append(value)
            if col == 'id':
                colid = n

        try:
            #aggiornamento database
            if self.db_recno == NEW_RECORD:
                self.BeforeInsertRecord()
                cmd = "INSERT INTO %s%s (" % (self.db_schema, self.db_tabname)
                cmd += ", ".join( [ col for col,ctr in self.db_datalink ] )
                cmd += ") VALUES ("
                cmd += (r"%s, " * len(self.db_datalink))[:-2] + ");"

                self.db_curs.execute( cmd, dbvalues )
                self.db_curs.execute( "SELECT LAST_INSERT_ID();" )
                recid = int(self.db_curs.fetchone()[0])
                self.AfterInsertRecord(recid)

                #aggiunta record in coda al recordset
                rec = list()
                for col,ctr in self.db_datalink:
                    if col.lower() == "id":
                        value = recid
                    else:
                        if isinstance(ctr, wx.Window):
                            value = ctr.GetValue()
                        else:
                            value = getattr(self, ctr)
                    rec.append( value )
                self.db_rs.append( rec )
                self.db_recno = len( self.db_rs ) - 1
                self.db_recid = recid
                dbvalues[colid] = recid
                self.FindWindowByName("id").SetValue( repr( self.db_recid ) )
                self.db_last_inserted_id = recid

            else:
                self.BeforeUpdateRecord()
                cmd = "UPDATE %s%s SET " % (self.db_schema, self.db_tabname)
                cmd += ", ".join(
                       [ "%s=%%s" % col for col,ctr in self.db_datalink ] )
                cmd += " WHERE ID = %s;" % self.db_recid
                self.db_curs.execute( cmd, dbvalues )
                self.AfterUpdateRecord(dbvalues)

            #aggiornamento recordset
            ncol = 0
            for col,ctr in self.db_datalink:
                self.db_rs[self.db_recno][ncol] = dbvalues[ncol]
                ncol += 1

            if self._btnattach and self._btnattach.ChangesPending():
                self._btnattach.SetKey(self.db_recid, save=True)

            self.SetDataChanged(False)
            out = True

        except MySQLdb.Error, e:

            errcode = e.args[0]
            errdesc = e.args[1]

            if errcode == 1062:
                #chiave duplicata
                if "key 2" in errdesc.lower():
                    msg = "Il codice immesso"
                elif "key 3" in errdesc.lower():
                    msg = "La descrizione immessa"
                else:
                    msg = "La chiave"
                msg += """ esiste già.  Modificare tale informazione per """\
                       """poter memorizzare."""
                MsgDialog(self, msg)
            else:
                MsgDialogDbError(self, e)

        except Exception, e:
            MsgDialogDbError(self, e)

        return out

    def DisplayElenco(self):
        self._DisplayPage(PAGE_ELENCO)

    def DisplayScheda(self):
        self._DisplayPage(PAGE_SCHEDA)
        self.SetFirstFocus()

    def SetFirstFocus(self):
        if self.firstfocus:
            #forzo focus su id se no non aggiorna il colore del controllo
            ctr = self.FindWindowByName('id')
            if ctr:
                ctr.SetFocus()
            ctr = self.FindWindowByName(self.firstfocus)
            if ctr:
                ctr.SetFocus()

    def _DisplayPage(self, n):
        es = self.FindWindowByName('elescheda')
        if es.GetSelection() != n:
            es.SetSelection(n)

    def IsPageElenco(self):
        return self._GetCurrentPage() == PAGE_ELENCO

    def IsPageScheda(self):
        return self._GetCurrentPage() == PAGE_SCHEDA

    def _GetCurrentPage(self):
        return self.FindWindowByName('elescheda').GetSelection()

    def UpdateDataControls( self, recno=None, activatechanges=True ):
        """
        Aggiorna i controlli a video con i valori del record indicato.
        In caso di inserimento, il numero del record è C{NEW_RECORD}

        @param recno: numero del record da associare ai controlli
        @type recno: int
        """
        if recno is None:
            recno = self.db_recno
        if recno is None:
            return
        if recno >= len(self.db_rs):
            return

        self.db_recno_old = self.db_recno
        self.db_recno = recno

        self.acceptDataChanged = False

        if recno == NEW_RECORD:
            for col, ctr in self.db_datalink:
                if isinstance(ctr, wx.Window):
                    self.ResetControl(ctr)
                else:
                    setattr(self, ctr, None)
                if col in 'codice descriz'.split():
                    ctr.SetEditable(True)
            self.db_recid = None
            if self.valuesearch:
                status = "CERCA VALORI"
                srecno = 'CV'
            else:
                status = "INSERIMENTO"
                srecno = 'NEW'
            wx.CallAfter(self.DisplayScheda)

        else:
            self.db_recno_old = self.db_recno
            rec = self.db_rs[recno]
            n = 0
            for col, ctr in self.db_datalink:
                if isinstance(ctr, wx.Window):
                    if rec[n] == None:
                        self.ResetControl(ctr)
                    else:
                        try:
                            ctr.SetValue( rec[n] )
                        except:
                            #print ctr
                            pass
                    if col in 'codice descriz'.split():
                        ctr.SetEditable(False)
                    if ctr.GetName() == 'codice':
                        self._oricod = ctr.GetValue()
                    elif ctr.GetName() == 'descriz':
                        self._orides = ctr.GetValue()
                else:
                    setattr(self, ctr, rec[n])
                if col.lower() == "id":
                    self.db_recid = int(rec[n])
                n += 1
            status = "VISUALIZZAZIONE"
            srecno = str(self.db_recno+1)

        def SetColor(dl):
            col, ctr = dl
            if isinstance(ctr, wx.Window):
                try:
                    ctr.AdjustBackgroundColor()
                except:
                    ctr.SetBackgroundColour(wx.NullColour)
        map(SetColor, self.db_datalink)

#        self.SetDataChanged(False)
        self.UpdateButtonsState()

        if recno == NEW_RECORD:
            ctr = self.FindWindowByName('workzone')
            if ctr:
                if ctr.GetPageCount()>0:
                    ctr.SetSelection(0)

        if activatechanges:
            #self.acceptDataChanged = True
            def EnableChanges():
                event = AcceptDataChanged()
                event.resetchanges = True
                wx.PostEvent(self, event)
            wx.CallAfter(EnableChanges)

        if self.complete:
            ci = lambda x: self.FindWindowById(x)
            ci(ID_NUMRECFIRST).SetLabel(srecno)
            ci(ID_NUMRECLAST).SetLabel(str(len(self.db_rs)))
            ci(ID_RECORDSTATUS).SetLabel(status[:3])

        if self._gridsrc and recno != NEW_RECORD:
            self._gridsrc.SelectRow(recno)
            col = self._gridsrc.GetGridCursorCol()
            #self._gridsrc.MakeCellVisible(recno, col)
        if self._btnattach is not None:
            self._btnattach.SetKey(self.db_recid)

        if not self.IsGestioneClientiFornitori():
            self.UpdateDataControls_PersonalPage()

    def UpdateDataControls_PersonalPage(self):
        pass

    def ResetControl( self, ctr ):
        try:
            c = ctr.__class__
            if   issubclass(c, masked.NumCtrl):
                ctr.SetValue(0)

            elif issubclass(c, (wx.TextCtrl,
                                entries._EntryCtrlMixin,)):
                ctr.SetValue("")

            elif issubclass(c, (linktable.LinkTable,
                                checkbox.CheckBox,
                                checkbox.CheckListBox,
                                radiobox.RadioBox,
                                datectrl.DateCtrl,
                                datectrl.DateTimeCtrl,
                                entries.PrintersComboBox)):
                ctr.SetValue(None)
        except:
            pass
        
        
        

    def SetDataChanged(self, dmod=True, changedobject=None):
        if (self.db_recno is not None and self.acceptDataChanged) or not dmod:
            self.datachanged = dmod
            if self.acceptDataChanged:
                if self.db_recno != NEW_RECORD:
                    if dmod and self.complete:
                        self.FindWindowById(ID_RECORDSTATUS).SetLabel("MODIFICA"[:3])
                self.UpdateButtonsState()

    def UpdateButtonsState( self ):
        if self.complete:
            e = not self.valuesearch
            nn = (self.db_recno != NEW_RECORD)
            if not nn:
                if self.autoCode:
                    if self.FindWindowByName("codice").GetValue()=='':
                        obj = self.FindWindowByName("codice")
                        #print 'componi codice di lunghezza %s per la tabella %s' % (obj.GetMaxLength(), self.db_tabname)
                        newCode = self.GetNewCode(lenght=obj.GetMaxLength())           
                        self.FindWindowByName("codice").SetValue(newCode)
            
            for cid, enab in (
                (ID_BTN_RECNEW,      e and nn),
                (ID_BTN_COPYFROM,    e and self.db_recno == -1),
                (ID_BTN_RECFIRST,    e and self.db_recno > 0),
                (ID_BTN_RECPREVIOUS, e and self.db_recno > 0),
                (ID_BTN_RECNEXT,     e and nn and self.db_recno < len(self.db_rs)-1),
                (ID_BTN_RECLAST,     e and nn and self.db_recno < len(self.db_rs)-1),
                (ID_BTN_RECSAVE,     e and (self.datachanged or nn) and self.FindWindowByName('elescheda').GetSelection() == 1),
                (ID_BTN_RECUNDO,     True),
                (ID_BTN_RECDELETE,   e and nn and self.IsPageScheda()),
                (ID_BTNFILTERS,      e),
                (ID_BTNVALSRC,       True),
                ):
                ctr = self.FindWindowById(cid)
                if ctr:
                    ctr.Enable(enab)
                    if cid == ID_BTNVALSRC:
                        if self.valuesearch:
                            tt = 'Cerca i valori digitati'
                        else:
                            tt = 'Imposta i valori da ricercare'
                        for key in self._accelerators:
                            if self._accelerators[key].control_id == ID_BTNVALSRC:
                                self._accelerators[key].description = tt
                                self.BuildAcceleratorTable()
                                break

    def GetMaxCodice(self):
        sql = "select max(codice) FROM %s%s WHERE codice REGEXP '^[0-9]+$';" % ( self.db_schema, self.db_tabname )
        self.db_curs.execute( sql)
        rs = self.db_curs.fetchone()
        if rs[0]==None:
            ret = 0
        else:
            ret = int(rs[0])
        return ret
        
    def GetNewCode(self, lenght=10):
        newCode = ''
        try:
            newValue = self.GetMaxCodice()
            sLen = '%03d' % lenght
            mask = '%%%sd' % sLen            
            newCode = mask%(newValue+1)
            if len(newCode)>lenght:
                newValue = self.GetFreeCode()
                newCode = mask%(newValue) 
        except:
            pass           
        
        return newCode[-lenght:]     

    def GetFreeCode(self):
        sql = """SELECT codice, CAST(codice AS DECIMAL) + 1 available_codice 
  FROM %s%s t
 WHERE NOT EXISTS
(
  SELECT *
    FROM %s%s
   WHERE CAST(codice AS DECIMAL) = CAST(t.codice AS DECIMAL) + 1

)
 ORDER BY codice
LIMIT 1"""   % (self.db_schema, self.db_tabname,self.db_schema, self.db_tabname)  
        self.db_curs.execute( sql)
        rs = self.db_curs.fetchone()
        try:
            if rs[0]==None:
                ret = 0
            else:
                ret = int(rs[1])
        except:
            ret = 0
        return ret

    def SetSearchFilter(self, sf):
        self.db_searchfilter = sf

    def GetSqlFilterSearch(self):
        #filtro di base, non visuale e impostato dalla sottoclasse
        filter = self.db_searchfilter or ''
        par = []
        val = self.FindWindowById(ID_SEARCHVAL).GetValue()
        #filtro in base al valore digitato
        if val:
            #valore digitato nel box di ricerca
            val = val.replace('..', '%')
            if bt.OPTSPASEARCH:
                val = val.replace(' ', '%')
            tab = self.db_tabname
            #test su codice (inizia con)
            flt = "%s.codice LIKE %%s" % tab
            par.append(val)
            #test su descrizione (inizia con)
            flt += " OR %s.descriz LIKE %%s" % tab
            if not val.endswith(r'%'):
                val = val.rstrip()+r'%'
            par.append(val)
            if filter:
                filter = "(%s) AND " % filter
            filter += "(%s)" % flt
        return filter, par

    def GetSqlFilterSpecific(self):
        #filtro specifico della sottoclasse, richiamato dall'utente tramite
        #pannello filtri
        return self.db_filtersexpr, self.db_filterspars

    def GetSqlFilter(self):
        fltexp = ''
        fltpar = []
        for exp, par in (self.GetSqlFilterSearch(),
                         self.GetSqlFilterSpecific()):
            if exp:
                if fltexp:
                    fltexp += " AND "
                fltexp += ("(%s)" % exp)
                fltpar += par
        return fltexp, fltpar

    def GetSqlColumns(self):
        fields = ''
        for col,ctr in self.db_datalink:
            fields += '%s.%s, ' % (self.db_tabname, col)
        fields = fields[:-2]
        fields += self._sqlrelcol
        return fields

    def GetSqlSearch(self):
        cmd = "SELECT %s FROM %s%s%s"\
              % (self.GetSqlColumns(), self.db_schema, self.db_tabname, self._sqlrelfrm)
        par = []
        return cmd, par

    def SetOrderNumber(self, n):
        self.db_searchordnum = n

    def GetOrderNumber(self):
        return self.db_searchordnum

    def GetSqlValueSearch(self):
        flt = ''
        par = []
        vs = []
        tab = self.db_tabname
        for tab, col, val in self.valuesearchvalues:
            op = '='
            if type(val) in (str, unicode):
                val = val.replace(r'%', '')
                val = val.replace('..', r'%')
                if bt.OPTSPASEARCH:
                    val = val.replace(' ', r'%')
                endby = val.startswith("*")
                if endby:
                    val = "%%%s" % val[1:]
                if val.endswith("*"):
                    val = val[:-1]
                if not endby:
                    val += "%"
                if '%' in val:
                    op = ' LIKE '
            flt = linktable.AndApp(flt, "%s.%s%s%%s" % (tab, col, op))
            par.append(val)
        return flt, par

    def TestSqlCount(self):

        valid = True
        if not self.complete or not GetUserMaxSqlCount():
            return valid

        def ci(x):
            return self.FindWindowById(x)

        cmd = "SELECT COUNT(*) FROM %s%s%s"\
              % (self.db_schema, self.db_tabname, self._sqlrelfrm)
        par = []

        filterexpr, filterpar = self.GetSqlFilter()
        fvs, pvs = self.GetSqlValueSearch()
        if fvs:
            if filterexpr:
                filterexpr = "(%s) AND (%s)" % (filterexpr, fvs)
            else:
                filterexpr = fvs
            filterpar += pvs
        if filterexpr:
            cmd += " WHERE %s" % filterexpr
            if filterpar: par += filterpar
        if self._sqlrelwhr:
            cmd += self._sqlrelwhr
        _group = self.GetSqlGroup()
        if _group:
            cmd += " GROUP BY %s" % _group

        wx.BeginBusyCursor()

        try:

            cmd, par = self.AlterSqlSearch(cmd, par)

            db = adb.db.__database__
            if db.Retrieve(cmd, par):
                rows = db.rs[0][0]
                if rows>GetUserMaxSqlCount():
                    if aw.awu.GetParentFrame(self).IsShown():
                        msg = """Sono stati trovati %d risultati.\n"""\
                        """Proseguendo con questi criteri, la ricerca """\
                        """potrebbe durare più tempo del solito.\n\n"""\
                        """Confermi la ricerca ?""" % rows
                        if aw.awu.MsgDialog(self, msg, style=wx.ICON_WARNING|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                            valid = False
                    else:
                        valid = False

        finally:
            wx.EndBusyCursor()

        return valid

    def UpdateSearch(self):

        def ci(x):
            return self.FindWindowById(x)

        cmd, par = self.GetSqlSearch()

        if self.complete:

            if not self.TestSqlCount():
                return False

            filterexpr, filterpar = self.GetSqlFilter()

            fvs, pvs = self.GetSqlValueSearch()
            if fvs:
                if filterexpr:
                    filterexpr = "(%s) AND (%s)" % (filterexpr, fvs)
                else:
                    filterexpr = fvs
                filterpar += pvs

        else:

            if self.onecodeonly is None:
                #inserimento nuovo record da dialog modale
                self.SetInsertMode()
                self._panelcard.Enable()
                return True

            else:
                #unico record da gestire:
                filterexpr = "%s.id=%%s" % self.db_tabname
                filterpar = (self.onecodeonly,)

        if filterexpr:
            cmd += " WHERE %s" % filterexpr
            if filterpar: par += filterpar
            self.db_filter = filterexpr
            self.db_parms = par
        else:
            self.db_filter = self.db_parms = None

        if self._sqlrelwhr:
            cmd += self._sqlrelwhr

        _group = self.GetSqlGroup()
        if _group:
            cmd += " GROUP BY %s" % _group

        _order = self.GetSqlOrder()
        if ord:
            cmd += " ORDER BY "+_order

        wx.BeginBusyCursor()

        try:

            cmd, par = self.AlterSqlSearch(cmd, par)

            db = adb.db.__database__
            if db.Retrieve(cmd, par, asList=True):
                self.db_rs = []+db.rs

            else:
                MsgDialog(self,
                          message="Problema durante l'accesso ai dati:\n%s"\
                          % repr(db.dbError.description),
                          style=wx.ICON_EXCLAMATION)

            self.UpdateSearchGrid()

        finally:
            wx.EndBusyCursor()

        self.MoveRecordFirst()

        if self.complete:
            ci(ID_NUMRECLAST).SetLabel(str(len(self.db_rs)))

        self.acceptDataChanged = False

        if self.db_rs:
            self._panelcard.Enable()
        else:
            for col, ctr in self.db_datalink:
                if isinstance(ctr, wx.Window):
                    self.ResetControl(ctr)
                else:
                    setattr(self, ctr, None )
            self._panelcard.Disable()
            if self.complete:
                for cid, label in ((ID_RECORDSTATUS, ''),
                                   (ID_NUMRECFIRST,  '0'),
                                   (ID_NUMRECLAST,   '0')):
                    ci(cid).SetLabel(label)
            self.UpdateButtonsState()

        self.SetDataChanged(False)

        if self.complete:
            self.UpdateSpecFiltersButton()
            if len(self.db_rs) == 1:
                self.UpdateDataControls(0)
                self.DisplayScheda()
            else:
                self.DisplayElenco()
                if len(self.db_rs) == 0:
                    ci(ID_SEARCHVAL).SetFocus()
                else:
                    self.SetDefaultItem(None)
                    self._gridsrc.SetFocus()

        return len( self.db_rs ) > 0

    def AlterSqlSearch(self, cmd, par):
        return cmd, par

    def GetSqlGroup(self):
        return ""

    def GetSqlOrder(self, addAlias=True):
        _order = ''
        if self.db_ordercolumns:
            n = self.GetOrderNumber()
            if n < len(self.db_ordercolumns):
                for order in self.db_ordercolumns[n][1]:
                    if not '.' in order and addAlias:
                        order = '%s.%s' % (self.db_tabname, order)
                    if _order:
                        _order += ', '
                    _order += order
                    _order += ' '+("ASC","DESC")[self.db_orderdirection]
        return _order

    def UpdateSearchGrid(self):
        self._gridsrc.ChangeData(self.db_rs)

    def SetDbConnection( self, db_conn ):
        """
        Imposta la connessione al database.
        L'oggetto è automaticamente impostato in base al valore di
        L{Azienda.DB.connection}, questa funzione non è solitamente necessaria.

        @param db_conn: connessione al database
        @type db_conn: mysql db connection
        """
        self.db_conn = db_conn

    def SetDbSetup( self, db_setup ):
        """
        Imposta la tabella da gestire.
        Per la struttura di C{db_setup} si veda la documentazione di L{Azienda.BaseTab}

        @param db_setup: struttura tabella da gestire
        @type db_setup: tupla
        """
        tab = db_setup[bt.TABSETUP_TABLENAME]
        des = db_setup[bt.TABSETUP_TABLEDESCRIPTION]
        col = db_setup[bt.TABSETUP_TABLESTRUCTURE]
        con = db_setup[bt.TABSETUP_TABLECONSTRAINTS]
        self.SetDbTableName(tab, des)
        self.SetDbColumns(col)
        self.SetDbConstraints(con)
        self.SetDbOrderColumns((("Codice",      ('%s.codice' % tab,)),
                                ("Descrizione", ('%s.descriz' % tab,)),))

    def SetDbTableName( self, db_tabname, db_tabdesc = None ):
        """
        Imposta il nome della tabella da gestire.

        @param db_tabname: nome della tabella da gestire
        @type db_tabname: String
        @param db_tabdesc: descrizione della tabella  I{(Default: Tabella C{db_tabname})}
        @type db_tabdesc: String

        B{N.B.:} Normalmente si utilizza la funzione L{SetDbSetup} in quanto consente di
        specificare contestualmente nome, descrizione e struttura della tabella da
        gestire; l'utilizzo di questa funzione deve essere invece accompagnato perlomeno
        da L{SetDbColumns}.
        """
        if db_tabdesc is None:
            db_tabdesc = "Tabella %s" % db_tabname.title()
        self.db_tabname = db_tabname
        self.db_tabdesc = db_tabdesc

    def SetDbColumns( self, db_columns):
        """
        Imposta la struttura delle colonne da gestire.

        @param db_columns: struttura colonne
        @type: tupla di tuple:
            - nome della colonna
            - larghezza
            - decimali
            - descrizione contenuto
            - attributi db
        @see: Esempio struttura clienti: L{Azienda.BaseTab.clienti}
        """
        self.db_columns = db_columns

    def SetDbConstraints( self, db_constraints ):
        """
        Imposta le condizioni per il controllo dell'integrità referenziale
        della tabella, nel caso in cui tale controllo non sia effettuato dal
        db server.

        @param db_constraints: elenco tabelle relazionate
        @type: tupla di tuple:
            - nome tabella relazionata
            - numero indice da utilizzare per il controllo
            - elenco colonne chiave
        """
        self.db_tabconstr = db_constraints

    def SetDbOrderColumns( self, db_ordercolumns ):
        """
        Imposta le colonne in base alle quali ordinare il recordset ottenuto
        in fase di ricerca.

        @param db_ordercolumns: 2 str-tuple: descrizione;elenco,dei,campi
        @type db_ordercolumns: tupla di stringhe
        """
        self.db_ordercolumns = db_ordercolumns

    def SetDbOrderDirection( self, db_orderdirection ):
        """
        Imposta il modo di ordinare il recordset ottenuto in fase di ricerca,
        a seconda che si voglia ordinare dal basso all'altro o viceversa.

        @param db_orderdirection: direzione: 0=ascendente, 1=discendente
        @type db_orderdirection: int
        """
        self.db_orderdirection = db_orderdirection

    def GetDbConnection( self ):
        """
        Ritorna la connessione al database

        @return: connessione al database
        @rtype: mysql db connection
        """
        return self.db_conn

    def GetDbTableName( self ):
        """
        Ritorna il nome della tabella da gestire.

        @return: nome tabella da gestire
        @rtype: String
        """
        return self.db_tabname

    def GetDbRecordSet( self ):
        """
        Ritorna il recordset attivo al momento.
        """
        return self.db_rs

    def GetDbOrderColumns( self ):
        """
        Ritorna l'elenco delle colonne in base alle quali ordinare il recordset
        ottenuto in fase di ricerca.

        @return: elenco nomi colonna per l'ordinamento
        @rtype: tupla di stringhe
        """
        return self.db_ordercolumns

    def GetDbDatalink( self ):
        """
        Ritorna l'elenco dei controlli legati ai dati.
        E' una tupla di tuple, ogniuna delle quali contiene:
            - nome del controllo (deve corrispondere al nome della colonna)
            - puntatore al controllo
        """
        return self.db_datalink

    def GetDbColumnsNames( self ):
        """
        Ritorna l'elenco delle colonne agganciate ai controlli.
        """
        return self.db_datacols

    class TitlePanel(aw.Panel):
        def __init__( self, parent, title = "Tabella" ):
            aw.Panel.__init__( self, parent, pos = (0,0), size = (80,80) )
            self.SetBackgroundColour("white")
            TitlePanelFunc(self)
            self.SetName('titlepanel')
            self.FindWindowById(ID_TITLECARD).SetLabel(title)

    def GetDbPrint(self):
        return adb.DbTable(self.db_tabname, writable=False)

    def PrintLista(self):
        if self.db_report is None: return
        os = self.GetOrdStampaDialog()
        if os is None:
            do = True
            rag = None
        else:
            do = os.ShowModal() == wx.ID_OK
            rag = os.GetRaggr()
        if do:
            db = self.GetDbPrint()
            db.ShowDialog(self)
            if self.db_filter:
                db.AddFilter(self.db_filter, *self.db_parms)
            if self.db_orderdirection == 1:
                ot = adb.ORDER_DESCENDING
            else:
                ot = adb.ORDER_ASCENDING
            n = self.GetOrderNumber()
            db.ClearOrders()
            if rag:
                ragord, ragexpr, ragprint = self.GetOrdStampaRaggr(db, rag)
                db.AddOrder(ragord, ot)
            else:
                ragexpr = '1'
                ragprint = None
            db._info.ragexpr = ragexpr
            db._info.ragprint = ragprint
            for of in self.db_ordercolumns[n][1]:
                db.AddOrder(of, ot)
            if db.Retrieve():
                rpt.Report(self, db, self.db_report)
            else:
                MsgDialog(self, repr(db.GetError()))
        if os:
            os.Destroy()

    def GetOrdStampaDialog(self):
        return None

    def __getitem__(self, name):
        out = None
        #try:
        if self.db_recno != NEW_RECORD:
            ncol = self.db_datacols.index(name)
            if ncol >= 0:
                out = self.db_rs[ self.db_recno ][ncol]
        #except:
            #pass
        return out


# ------------------------------------------------------------------------------


class AnagToolbar(aw.Panel):
    def __init__(self, parent, id,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TAB_TRAVERSAL, hide_ssv=True):
        aw.Panel.__init__(self, parent, id, pos, size, style)
        AnagToolbarFunc( self, True )
        self.SetName('anagtoolbar')
        self.HelpBuilder_SetDir('ui.anagtoolbar')
        self.HelpBuilder_SetForceMain()
        if hide_ssv:
            self.FindWindowByName('_ssv').Hide()


# ------------------------------------------------------------------------------


class AnagCard(aw.Panel):
    def __init__(self, parent, id,
        pos = wx.DefaultPosition, size = wx.DefaultSize,
        style = wx.TAB_TRAVERSAL ):
        aw.Panel.__init__(self, parent, id, pos, size, style)
        AnagCardFunc( self, True )


# ------------------------------------------------------------------------------


class _AnagMixin(object):

    def OneCardOnly( self, onecodeonly, desProd=None, codProd=None ):
        if len(self.panel.db_rs) == 0:
            self.SetTitle( "Inserimento scheda" )
            if type(self.onecodeonly) in (str, unicode):
                ctr = self.FindWindowByName("codice")
                self.panel.db_recno = NEW_RECORD
                if ctr != None:
                    ctr.SetValue( onecodeonly )
                self.panel.InsertingRecord()
            if not desProd==None:
                ctr = self.FindWindowByName("codice")
                ctr.SetValue(codProd)
                ctr = self.FindWindowByName("descriz")
                ctr.SetValue(desProd)
            bmp = awcimg.getCardEmpty16Bitmap()
        else:
            self.SetTitle( "Scheda anagrafica" )
            self.panel.UpdateDataControls(0)
            bmp = awcimg.getCardFull16Bitmap()
        c = self.FindWindowById(ID_BITMAPCARD)
        if c:
            c.SetBitmap(bmp)
            c.Refresh()

    def OnClose(self, event):
        if not self.panel.TestForChanges():
            event.Veto(True)
            return False
        self.FixTimerProblem()
        event.Skip()
        return True

    def SelectZone(self, page_name, notebook_name='workzone'):
        out = False
        cn = self.FindWindowByName
        wz = cn(notebook_name)
        if wz:
            for pn in range(wz.GetPageCount()):
                t = wz.GetPageText(pn)
                if page_name.lower() in t.lower():
                    wz.SetSelection(pn)
                    out = True
                    break
        return out

    def FixTimerProblem(self):
        #fix Timer su wx.2.8.11: se non lo stoppo, l'applicaizone va in crash :-(
        #TODO: verificare quando è stato risolto il problema nella libreria wx
        c = self.FindWindowByName('_attach_autotext')
        if c:
            c.Stop()

    def CanClose(self):
        #richiamata da XFrame in fase di chiusura applicazione
        if self.panel.TestForChanges():
            self.FixTimerProblem()
            return True
        return False


# ------------------------------------------------------------------------------


class _AnagDialog(aw.Dialog, _AnagMixin):

    def __init__(self, *args, **kwargs):

        self.complete = True
        self.onecodeonly = None
        if 'onecodeonly' in kwargs:
            self.onecodeonly = kwargs.pop('onecodeonly')
            self.complete = False
        if 'valuesearch' in kwargs:
            self.valuesearch = kwargs.pop('valuesearch')

        aw.Dialog.__init__(self, *args, **kwargs)
        _AnagMixin.__init__(self)

        self.SetMinHeight(MINIMUM_FRAME_HEIGHT)
        self.panel = None

    def LoadAnagPanel(self, panel, forceComplete=False):
        try:
            if not self.complete:
                panel.SetOneCodeOnly(self.onecodeonly)
            panel.SetValueSearch(self.valuesearch)
            panel.complete = forceComplete
        except:
            pass
        self.panel = panel
        self.panel.InitControls()
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def GetValueSearchValues(self):
        return self.panel.GetValueSearchValues()

    def EndModal(self, value):
        self.FixTimerProblem()
        aw.Dialog.EndModal(self, value)


# ------------------------------------------------------------------------------


class _AnagFrame(aw.Frame, _AnagMixin):
    complete = True
    onecodeonly = None

    def __init__(self, *args, **kwargs):

        if 'complete' in kwargs:
            self.complete = kwargs.pop('complete')
        else:
            self.complete = True
        if 'onecodeonly' in kwargs:
            self.onecodeonly = kwargs.pop('onecodeonly')

        aw.Frame.__init__(self, *args, **kwargs)
        _AnagMixin.__init__(self)

        self.SetMinHeight(MINIMUM_FRAME_HEIGHT)
        self.panel = None

    def LoadAnagPanel(self, panel):
        self.panel = panel
        self.panel.complete = self.complete
        self.panel.InitControls()
        self.AddSizedPanel(self.panel)
        if self.onecodeonly:
            self.OneCardOnly(self.onecodeonly)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def SetSearchFilter(self, *args):
        self.panel.SetSearchFilter(*args)

    def UpdateSearch(self):
        self.panel.UpdateSearch()

    def Show(self):
        aw.Frame.Show(self)
        def SetFocus():
            ctr = self.FindWindowById(ID_SEARCHVAL)
            if ctr:
                ctr.SetFocus()
        wx.CallAfter(SetFocus)
