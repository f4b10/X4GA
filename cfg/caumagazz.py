#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/caumagazz.py
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

import MySQLdb

import awc.layout.gestanag as ga
from awc.layout.gestanag_wdr import ID_BTN_RECSAVE
import cfg.caumagazz_wdr as wdr

import awc
from awc.util import GetAllChildrens, MsgDialog, MsgDialogDbError

import awc.controls.windows as aw
import awc.controls.linktable as ltlib

import awc.controls.dbgrid as dbglib
from anag.pdc import PdcDialog
from anag.pdctip import PdcTipDialog

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import stormdb as adb

from cfg.dbtables import PermessiUtenti

from awc.tables.util import CheckRefIntegrity


FRAME_TITLE = "Causali magazzino"


movfields = []; fldap = movfields.append
movdefaults = []; defap = movdefaults.append
fldap('id');           defap(None); RSMOV_ID        =     0
fldap('codice');       defap(None); RSMOV_CODICE    =     1
fldap('descriz');      defap(None); RSMOV_DESCRIZ   =     2
fldap('id_tipdoc');    defap(None); RSMOV_TIPDOC    =     3
fldap('askvalori');    defap('T');  RSMOV_ASKVALORI =     4
fldap('tipvaluni');    defap(' ');  RSMOV_TIPVALUNI =     5
fldap('tipsconti');    defap(' ');  RSMOV_TIPSCONTI =     6
fldap('aggprezzo');    defap(' ');  RSMOV_AGGPREZZO =     7
fldap('aggcosto');     defap(' ');  RSMOV_AGGCOSTO  =     8
fldap('agggrip');      defap(' ');  RSMOV_AGGGRIP   =     9
fldap('aggfornit');    defap(' ');  RSMOV_AGGFORNIT =    10
fldap('ricprezzo');    defap(' ');  RSMOV_RICPREZZO =    11
fldap('riccosto');     defap(' ');  RSMOV_RICCOSTO  =    12
fldap('riccostosr');   defap(' ');  RSMOV_RICCOSTOSR=    13
fldap('riclist');      defap(' ');  RSMOV_RICLIST   =    14
fldap('newlist');      defap(' ');  RSMOV_NEWLIST   =    15
fldap('aggini');       defap(0);    RSMOV_AGGINI    =    16
fldap('agginiv');      defap(0);    RSMOV_AGGINIV   =    17
fldap('aggcar');       defap(0);    RSMOV_AGGCAR    =    18
fldap('aggcarv');      defap(0);    RSMOV_AGGCARV   =    19
fldap('aggsca');       defap(0);    RSMOV_AGGSCA    =    20
fldap('aggscav');      defap(0);    RSMOV_AGGSCAV   =    21
fldap('aggordcli');    defap(0);    RSMOV_AGGORDCLI =    22
fldap('aggordfor');    defap(0);    RSMOV_AGGORDFOR =    23
fldap('statftcli');    defap(0);    RSMOV_STATFTCLI =    24
fldap('statftfor');    defap(0);    RSMOV_STATFTFOR =    25

fldap('agggiacon');      defap(0);  RSMOV_AGGGIACON =    26
fldap('agggiafis');      defap(0);  RSMOV_AGGGIAFIS =    27
fldap('id_pdc');       defap(None); RSMOV_ID_PDC    =    28
fldap('tipologia');    defap('M');  RSMOV_TIPOLOGIA =    29
fldap('aggcvccar');    defap(None); RSMOV_AGGCVCCAR =    30
fldap('aggcvcsca');    defap(None); RSMOV_AGGCVCSCA =    31
fldap('aggcvfcar');    defap(None); RSMOV_AGGCVFCAR =    32
fldap('aggcvfsca');    defap(None); RSMOV_AGGCVFSCA =    33
fldap('f_acqpdt');     defap(None); RSMOV_ACQPDT    =    34
fldap('proobb');       defap(None); RSMOV_PROOBB    =    35
fldap('tqtaxpeso');    defap(None); RSMOV_TQTAXPESO =    36
fldap('tqtaxcolli');   defap(None); RSMOV_TQTAXCOLLI =   37
fldap('lendescriz');   defap(60);   RSMOV_LENDESCRIZ =   38
fldap('mancosto');     defap("N");  RSMOV_MANCOSTO =     39
fldap('noprovvig');    defap(0);    RSMOV_NOPROVVIG =    40
fldap('statcscli');    defap(0);    RSMOV_STATCSCLI =    41
fldap('prtdestot');    defap("");   RSMOV_PRTDESTOT =    42
fldap('is_acconto');   defap(0);    RSMOV_ISACCONTO =    43
fldap('is_accstor');   defap(0);    RSMOV_ISACCSTOR =    44
fldap('acc_sepiva');   defap(0);    RSMOV_ACCSEPIVA =    45
fldap('canprezzo0');   defap(0);    RSMOV_CANPREZZO0 =   46
fldap('modimpricalc'); defap(0);    RSMOV_MODIMPRICALC = 47
fldap('nomastroprod'); defap(0);    RSMOV_NOPRODMASTRO = 48
fldap('is_default');   defap(0);    RSMOV_ISDEFAULT =    49



PERM_UTE_ID = 0
PERM_UTECOD = 1
PERM_UTEDES = 2
PERM_LEGGI =  3
PERM_SCRIVI = 4
PERM_GIORNI = 5


class PermUteGrid(dbglib.DbGridColoriAlternati):

    def __init__(self, parent, rsper):

        _STR = gl.GRID_VALUE_STRING
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _INT = gl.GRID_VALUE_NUMBER



        coldef = ((120, (PERM_UTEDES, "Utente", _STR, True)),
                  ( 50, (PERM_LEGGI,  "Legge",  _CHK, False)),
                  ( 50, (PERM_SCRIVI, "Scrive", _CHK, False)),
                  ( 30, (PERM_GIORNI, "Giorni", _INT, True)),
        )
        sizes =  [c[0] for c in coldef]
        colmap = [c[1] for c in coldef]

        canedit = True
        canins = False

        afteredit = None

        dbglib.DbGridColoriAlternati.__init__(self,
                                              parent,
                                              size=parent.GetClientSizeTuple())

        self.rsper = rsper
        self.SetData(self.rsper, colmap, canedit, canins,\
                     None, afteredit,\
                     lambda *x: self.AddNewRow)

        self.SetEditableColumns((0,1,2,3,))

        for c,s in enumerate(sizes):
            self.SetColumnDefaultSize(c,s)
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        self.Bind(gl.EVT_GRID_CELL_LEFT_CLICK, self.OnCellClick)
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRClick)

    def OnCellClick(self, event):
        row = event.GetRow()
        if 0 <= row < len(self.rsper):
            col = event.GetCol()
            if col in (1,2):   #colonne permesso leggi/scrivi
                if col == 1:
                    i = PERM_LEGGI
                else:
                    i = PERM_SCRIVI
                self.rsper[row][i] = 1-(self.rsper[row][i] or 0)
            elif col == 3:
                self.rsper[row][PERM_GIORNI]=1 + (self.rsper[row][PERM_GIORNI] or 0)
            self.SetDataChanged()
            self.Refresh()
        event.Skip()

    def OnCellRClick(self, event):
        row = event.GetRow()
        if 0 <= row < len(self.rsper):
            col = event.GetCol()
            if  col == 3:
                self.rsper[row][PERM_GIORNI]= max(0, (self.rsper[row][PERM_GIORNI] or 0) - 1)
            self.SetDataChanged()
            self.Refresh()
        event.Skip()


    def SetDataChanged(self):
        p=self
        try:
            for i in  range(100):
                p=p.GetParent()
                if 'BindChangedEvent' in dir(p):
                    p.SetDataChanged(True)
                    break
        except:
            pass




# ------------------------------------------------------------------------------


class DefMovGrid(dbglib.DbGridColoriAlternati):

    def __init__(self, parent, dbmov):
        coldef = (\
            ( 40, (RSMOV_CODICE,  "Cod.",      gl.GRID_VALUE_STRING, False)),
            (140, (RSMOV_DESCRIZ, "Movimento", gl.GRID_VALUE_STRING, False)),
            ( 30, (RSMOV_ISDEFAULT, "Pref.",   gl.GRID_VALUE_CHOICE+":1,0", False)),
            (  1, (RSMOV_ID,      "#mov",      gl.GRID_VALUE_NUMBER, False)),
        )

        sizes =  [c[0] for c in coldef]
        colmap = [c[1] for c in coldef]

        canedit = True
        canins = False

        afteredit = None

        dbglib.DbGridColoriAlternati.__init__(self,
                                              parent,
                                              size=parent.GetClientSizeTuple())

        self.dbmov = dbmov
        self.SetData(dbmov.GetRecordset(), colmap, canedit, canins,\
                     None, afteredit,\
                     lambda *x: self.AddNewRow)

        self.SetColMaxChar(RSMOV_CODICE, 10)
        self.SetColMaxChar(RSMOV_DESCRIZ, 20)

        self.SetCellDynAttr(self.GetAttr)
        for c,s in enumerate(sizes):
            self.SetColumnDefaultSize(c,s)
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelected)

    def OnCellSelected(self, event):
        self.SelectRow(event.GetRow())
        event.Skip()

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):

        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)

        #blocco editazione su cella ID
        readonly = (rscol == RSMOV_ID)
        attr.SetReadOnly(readonly)

        #impostazione colori
        if 0 <= row < self.dbmov.RowsCount():
            bgcol = None
            if not self.IsRowOk(row):
                bgcol = stdcolor.VALERR_BACKGROUND
            elif self.dbmov.GetRecordset()[row][RSMOV_ID] is None:
                bgcol = stdcolor.ADDED_BACKGROUND
            #attr.SetTextColour(fgcol)
            if bgcol:
                attr.SetBackgroundColour(bgcol)

        return attr

    def IsRowOk(self, row):
        mov = self.dbmov.GetRecordset()[row]
        valok = True
        for c in (RSMOV_CODICE, RSMOV_DESCRIZ):
            valok = valok and mov[c] is not None and len(mov[c].strip())>0
            if not valok:
                break
        return valok

    def AddNewRow(self):
        dbmov = self.dbmov
        dbmov.CreateNewRow()
        rs = []
        for n, col in enumerate(movfields):
            val = movdefaults[n]
            if val is not None:
                setattr(dbmov, col, val)
        return True


# ------------------------------------------------------------------------------


class CauMagazzPanel(ga.AnagPanel):
    """
    Gestione tabella Causali contabilità.
    """
    def __init__(self, *args, **kwargs):

        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_CFGMAGDOC ] )

        self.dbmov = adb.DbTable(bt.TABNAME_CFGMAGMOV, 'tipmov', fields=movfields)
        self.dbmov.AddOrder('tipmov.codice')
        self.dbmov.Reset()
        self._grid_mov = None
        self.loadmovs = True

    def InitControls(self, *args, **kwargs):
        ga.AnagPanel.InitControls(self, *args, **kwargs)
        cols = bt.tabelle[bt.TABSETUP_TABLE_CFGMAGMOV][bt.TABSETUP_TABLESTRUCTURE]
        cn = self.FindWindowByName
        controls = aw.awu.GetNamedChildrens(cn('docbook').GetPage(2), [col[0] for col in cols])
        lnk = [ ( ctr.GetName(), ctr ) for ctr in controls ]
        self.SetControlsMaxLength(cols, lnk)

    def InitAnagCard(self, parent):
        cn = self.FindWindowByName
        ci = self.FindWindowById
        p = wx.Panel( parent, -1)
        wdr.CauMagazzCardFunc( p, True )
        self.IdPdcTipo = self.FindWindowByName('id_pdctip')
        self.DefaultIdPdc = self.FindWindowByName('default_id_pdc')
        self.IdPdcTipo .Bind(ga.linktable.EVT_LINKTABCHANGED, self.OnChangeTipo)
        self._grid_mov = DefMovGrid(self.FindWindowById(wdr.ID_PANGRIDMOV), self.dbmov)
        self._grid_mov.Bind(gl.EVT_GRID_SELECT_CELL, self.OnGridMovCellSelected)
        self._grid_mov.Bind(gl.EVT_GRID_CELL_CHANGE, self.OnGridMovCellChanged)
        for name, val in ( ("numdoc",     "013A"),\
                           ("datdoc",     " 0123"),\
                           ("askprotiva", " 012"),\
                           ("scorpiva",   " 1"),\
                           ("askvalori",  "QTVD"),\
                           ("tipvaluni",  " 12L"),\
                           ("tipsconti",  " 12GX"),\
                           ("aggcosto",   (' ','1','2')),\
                           ("aggprezzo",  (' ','1','2')),\
                           ("agggrip",    (' ','A','N')),\
                           ("aggini",     (0,1)),\
                           ("agginiv",    (0,1,-1)),\
                           ("aggcar",     (0,1,-1)),\
                           ("aggcarv",    (0,1,-1)),\
                           ("aggsca",     (0,1,-1)),\
                           ("aggscav",    (0,1,-1)),\
                           ("aggordcli",  (0,1,-1)),\
                           ("aggordfor",  (0,1,-1)),\
                           ("statftcli",  (0,1,-1)),\
                           ("statcscli",  (0,1,-1)),\
                           ("statftfor",  (0,1,-1)),\
                           ("agggiacon",  (0,1,-1)),\
                           ("agggiafis",  (0,1,-1)),\
                           ("aggcvccar",  (0,1,-1)),\
                           ("aggcvcsca",  (0,1,-1)),\
                           ("aggcvfcar",  (0,1,-1)),\
                           ("aggcvfsca",  (0,1,-1)),\
                           ("provvig",    (0,1,-1)),\
                           ("mancosto",   ("N", "V", "M")),\
                           ("tipologia",  "DMVSTIEOP"),\
                           ("clasdoc",    (None, "ordfor", "carfor", "resfor", "ordcli", "vencli", "rescli")),
                           ("modimpricalc", (" ", "Q", "P") ), ):
            ctr = cn(name)
            ctr.SetDataLink(name, val)
            self.Bind(wx.EVT_RADIOBOX, self.OnChanged, ctr)

        for name, val in ( ("valuta",     { True: 'X', False: ' '} ),
                           ("ctrnum",     { True: 'X', False: ' '} ),
                           ("aggnum",     { True: 'X', False: ' '} ),
                           ("pienum",     { True: 'X', False: ' '} ),
                           ("askrifdesc", { True: 'X', False: ' '} ),
                           ("askrifdata", { True: 'X', False: ' '} ),
                           ("askrifnum",  { True: 'X', False: ' '} ),
                           ("askmagazz",  { True: 'X', False: ' '} ),
                           ("askmodpag",  { True: 'X', False: ' '} ),
                           ("askmpnoeff", { True: 'X', False: ' '} ),
                           ("askdestin",  { True: 'X', False: ' '} ),
                           ("askagente",  { True: 'X', False: ' '} ),
                           ("askzona",    { True: 'X', False: ' '} ),
                           ("asklist",    { True: 'X', False: ' '} ),
                           ("rowlist",    { True: 'X', False: ' '} ),
                           ("askbanca",   { True: 'X', False: ' '} ),
                           ("asktracau",  { True: 'X', False: ' '} ),
                           ("asktracur",  { True: 'X', False: ' '} ),
                           ("asktravet",  { True: 'X', False: ' '} ),
                           ("asktraasp",  { True: 'X', False: ' '} ),
                           ("asktrapor",  { True: 'X', False: ' '} ),
                           ("asktracon",  { True: 'X', False: ' '} ),
                           ("asktrakgc",  { True: 'X', False: ' '} ),
                           ("totali",     { True: 'X', False: ' '} ),
                           ("totzero",    { True: 'X', False: ' '} ),
                           ("totneg",     { True: 'X', False: ' '} ),
                           ("colcg",      { True: 'X', False: ' '} ),
                           ("staobb",     { True: 'X', False: ' '} ),
                           ("noprompt",   { True: 'X', False: ' '} ),
                           ("stanoc",     { True: 'X', False: ' '} ),
                           ("staintest",  { True: 'X', False: ' '} ),
                           ("stalogo",    { True: 'X', False: ' '} ),
                           ("askdatiacc", { True: 'X', False: ' '} ),
                           ("aggfornit",  { True: 'X', False: ' '} ),
                           ("riccosto",   { True: 'X', False: ' '} ),
                           ("ricprezzo",  { True: 'X', False: ' '} ),
                           ("riclist",    { True: 'X', False: ' '} ),
                           ("newlist",    { True: 'X', False: ' '} ),
                           ("riccostosr", { True: 'X', False: ' '} ),
                           ("askstapre",  { True: 'X', False: ' '} ),
                           ("askstaint",  { True: 'X', False: ' '} ),
                           ("viscosto",   { True: 1,   False: 0  } ),
                           ("visgiac",    { True: 1,   False: 0  } ),
                           ("vislistini", { True: 1,   False: 0  } ),
                           ("visultmov",  { True: 1,   False: 0  } ),
                           ("ultmovbef",  { True: 1,   False: 0  } ),
                           ("annacq1",    { True: 1,   False: 0  } ),
                           ("annacq2",    { True: 1,   False: 0  } ),
                           ("annacq3",    { True: 1,   False: 0  } ),
                           ("annacq4",    { True: 1,   False: 0  } ),
                           ("f_acqpdt",   { True: 1,   False: 0  } ),
                           ("proobb",     { True: 1,   False: 0  } ),
                           ("noprovvig",  { True: 1,   False: 0  } ),
                           ("printetic",  { True: 1,   False: 0  } ),
                           ("pdcdamag",   { True: 1,   False: 0  } ),
                           ("tqtaxpeso",  { True: 1,   False: 0  } ),
                           ("tqtaxcolli", { True: 1,   False: 0  } ),
                           ("checkfido",  { True: 1,   False: 0  } ),
                           ("checkacq1",  { True: 1,   False: 0  } ),
                           ("checkacq2",  { True: 1,   False: 0  } ),
                           ("checkacq3",  { True: 1,   False: 0  } ),
                           ("checkacq4",  { True: 1,   False: 0  } ),
                           ("autoqtaonbc",{ True: 1,   False: 0  } ),
                           ("vismargine", { True: 1,   False: 0  } ),
                           ("is_acconto", { True: 1,   False: 0  } ),
                           ("is_accstor", { True: 1,   False: 0  } ),
                           ("acc_sepiva", { True: 1,   False: 0  } ),
                           ("canprezzo0", { True: 1,   False: 0  } ),
                           ("nomastroprod",{True: 1,   False: 0  } ),
                           ("nonumxmag",  { True: 1,   False: 0  } ),
                           ("noivaprof",  { True: 1,   False: 0  } ),
                           ("rptcolli",   { True: 1,   False: 0  } ),
                           ("aanotedoc",  { True: 1,   False: 0  } ),
                           ("is_default", { True: 1,   False: 0  } ),
                           ):
            ctr = cn(name)
            ctr.SetDataLink(name, val)
            self.Bind(wx.EVT_CHECKBOX, self.OnChanged, ctr)

        self.FindWindowByName('catdoc').Bind(wx.EVT_CHECKLISTBOX, self.OnChanged)
        self.FindWindowByName('catdoc').SetDataChanged=self.SetDataChanged


#        cn('lendescriz').Bind(wx.EVT_KILL_FOCUS, self.OnChanged)
        for name in 'lendescriz prtdestot'.split():
            cn(name).Bind(wx.EVT_KILL_FOCUS, self.OnChanged)
        self.Bind(ga.linktable.EVT_LINKTABCHANGED, self.OnChanged, ci(wdr.ID_CTRPDC))

        self.Bind(wx.EVT_BUTTON, self.OnNewMov,  id = wdr.ID_BUTNEWMOV)
        self.Bind(wx.EVT_BUTTON, self.OnDelMov,  id = wdr.ID_BUTDELMOV)

        self.EnableDatiAcc()

        DB = Env.Azienda.DB
        db = Env.adb.DB(globalConnection=False)

        self.permute = []
        if db.Connect(host=DB.servername,
                      user=DB.username,
                      passwd=DB.password,
                      db='x4'):
            u = Env.adb.DbTable('utenti', 'ute', db=db, writable=False)
            u.AddOrder('ute.descriz')
            if u.Retrieve():
                for u in u:
                    self.permute.append([u.id,        #PERM_UTE_ID
                                         u.codice,    #PERM_UTECOD
                                         u.descriz,   #PERM_UTEDES
                                         0,           #PERM_LEGGI
                                         0,           #PERM_SCRIVI
                                         0,])         #PERM_GIORNI
            else:
                awc.util.MsgDialog(self, repr(u.GetError()))
            db.Close()
        else:
            awc.util.MsgDialog(self, repr(db.dbError.description))

        self.gridperm = PermUteGrid(cn('pangridperm'), self.permute)
        self.dbperm = PermessiUtenti(ambito='caumagazz')

        return p

    def UpdateControls(self, row):
        dbmov = self.dbmov
        if 0 <= row < dbmov.RowsCount():
            dbmov.MoveRow(row)
            for col, field in enumerate(movfields[3:]):
                ctr = self.FindWindowByName(field)
                if ctr:
                    ctr.SetValue(getattr(dbmov, field))

    def OnChangeTipo(self, evt):
        oPdcTipo = self.FindWindowByName('id_pdctip')
        self.DefaultIdPdc.Enable(not self.IdPdcTipo.GetValue()==None)
        if not self.IdPdcTipo.GetValue()==None:
            self.DefaultIdPdc.SetFilterValue(self.IdPdcTipo.GetValue(),0)

    def OnGridMovCellChanged(self, event):
        row = event.GetRow()
        self.UpdateFromControls(row)
        self._grid_mov.ResetView()
        event.Skip()

    def OnGridMovCellSelected(self, event, *args):
        self.UpdateControls(event.GetRow())
        event.Skip()

    def DeleteDataRecord(self):
        try:
            self.db_curs.execute( "DELETE FROM %s WHERE id_tipdoc=%d;"
                                  % ( bt.TABNAME_CFGMAGMOV,
                                      self.db_recid ) )
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            return False
        return ga.AnagPanel.DeleteDataRecord(self)

    def OnChanged(self, event):
        self.SetDataChanged()
        sr = self._grid_mov.GetSelectedRows()
        if sr:
            row = sr[-1]
            self.UpdateFromControls(row)
        if event.GetEventObject().GetName() == 'askdatiacc':
            self.EnableDatiAcc()
        elif event.GetEventObject().GetName() == 'is_default':
            o=event.GetEventObject()
            if o.IsChecked():
                for i,r in enumerate(self.dbmov):
                    if sr and i==row:
                        r.is_default=1
                    else:
                        r.is_default=0
            self._grid_mov.Refresh()
            pass
        event.Skip()

    def UpdateFromControls(self, row):
        dbmov = self.dbmov
        if 0 <= row < dbmov.RowsCount():
            dbmov.MoveRow(row)
            for col, field in enumerate(movfields[3:]):
                ctr = self.FindWindowByName(field)
                if ctr:
                    setattr(dbmov, field, ctr.GetValue())

    def EnableDatiAcc(self):
        e = self.FindWindowByName('askdatiacc').GetValue() == 'X'
        map(lambda x: x.Enable(e), [x for x in GetAllChildrens(self)
                                    if x.GetName().startswith('asktra')
                                    or x.GetName().startswith('id_tra')])

    def UpdateButtonsState( self ):
        ga.AnagPanel.UpdateButtonsState(self)
        if self.onecodeonly == None:
            valid = True
            for row in range(self.dbmov.RowsCount()):
                valid = self._grid_mov.IsRowOk(row)
                if not valid:
                    break
            if not valid:
                ctr = self.FindWindowById(ID_BTN_RECSAVE)
                if ctr:
                    ctr.Enable(False)

    def OnNewMov(self, event):
        self._grid_mov.AddNewRow()
        self._grid_mov.ResetView()
        self._grid_mov.SetGridCursor(self.dbmov.RowsCount()-1,1)
        event.Skip()

    def OnDelMov(self, event):
        dbmov = self.dbmov
        for row in self._grid_mov.GetSelectedRows():
            if 0 <= row < dbmov.RowsCount():
                dbmov.MoveRow(row)
                movid = dbmov.id
                if movid is None:
                    do = True
                else:
                    movconstr = bt.TABSETUP_CONSTR_CFGMAGMOV
                    do = CheckRefIntegrity(self, self.db_curs, movconstr, movid)
                if do:
                    if movid is not None:
                        if not movid in dbmov._info.deletedRecords:
                            #riga già esistente, marco per cancellazione da db
                            dbmov._info.deletedRecords.append(movid)
                    self._grid_mov.DeleteRows(row)
                    dbmov._info.recordCount -= 1
                    if dbmov._info.recordNumber >= dbmov._info.recordCount:
                        dbmov._info.recordNumber -= 1
                        dbmov._UpdateTableVars()
                    #after deletion, record cursor is on the following one
                    #so for iterations we decrement iteration index and count
                    dbmov._info.iterIndex -= 1
                    dbmov._info.iterCount -= 1
                    self.SetDataChanged()
                    event.Skip()

    def UpdateDataRecord( self ):
        cn = lambda x: self.FindWindowByName(x)
        for i in range(4):
            val = ''
            if   cn('_copydoc%d' % (i+1)).GetValue(): val = 'C'
            elif cn('_evadoc%d' % (i+1)).GetValue():  val = 'E'
            elif cn('_acqdoc%d' % (i+1)).GetValue():  val = 'A'
            cn('tipacq%d' % (i+1)).SetValue(val)
        self.loadmovs = False
        written = ga.AnagPanel.UpdateDataRecord(self)
        self.loadmovs = True
        if written:
            for mov in self.dbmov:
                if mov.id_tipdoc != self.db_recid:
                    mov.id_tipdoc = self.db_recid
            if not self.dbmov.Save():
                MsgDialog(self, repr(self.dbmov.GetError()), style=wx.ICON_ERROR)
            self.LoadMovs()
#        if written:
#            setCol = ""
#            for field in movfields:
#                setCol += "%s=%%s, " % field
#            setCol += r"id_tipdoc=%s"
#            cmdIns = "INSERT INTO %s SET %s" % (bt.TABNAME_CFGMAGMOV, setCol)
#            parIns = []
#            for mov in self.rsmov:
#                par = mov
#                par.append(self.db_recid)
#                parIns.append(par)
#            try:
#                if self.db_recid is not None:
#                    cmdDel = "DELETE FROM %s WHERE id_tipdoc=%%s"\
#                           % bt.TABNAME_CFGMAGMOV
#                    self.db_curs.execute(cmdDel, self.db_recid)
#                self.db_curs.executemany(cmdIns, parIns)
#                written = True
#            except MySQLdb.Error, e:
#                MsgDialogDbError(self, e)
#            except Exception, e:
#                pass
#            self.LoadMovs()
        return written

    def TransferDataFromWindow(self):
        out = ga.AnagPanel.TransferDataFromWindow(self)
        if out:
            p = self.dbperm
            p.SetIdRel(self.db_recid)
            if self.db_recid:
                db = p._info.db
                db.Execute("DELETE FROM %s WHERE ambito=%%s AND id_rel=%%s"\
                           % bt.TABNAME_CFGPERM, (p.GetAmbito(), self.db_recid))
            p.Reset()
            pu = self.permute

            for n, (puid, pucod, pudes, pleg, pscr, pgg) in enumerate(pu):
                if pleg or pscr or pgg:
                    p.CreateNewRow()
                    p.id_utente = puid
                    p.leggi  = pleg
                    p.scrivi = pscr
                    p.gg     = pgg
            if not p.IsEmpty():
                if not p.Save():
                    awc.util.MsgDialog(self, repr(p.GetError()))
            self.FindWindowByName('catdoc').Save(self.db_recid)
        return out

    def UpdateDataControls( self, recno ):
        ga.AnagPanel.UpdateDataControls( self, recno )
        cn = lambda x: self.FindWindowByName(x)
        for i in range(4):
            val = cn('tipacq%d' % (i+1)).GetValue()
            cn('_copydoc%d' % (i+1)).SetValue(val == 'C')
            cn('_evadoc%d' % (i+1)).SetValue(val == 'E')
            cn('_acqdoc%d' % (i+1)).SetValue(val == 'A')
        if self.loadmovs:
            self.LoadMovs()
            sr = self._grid_mov.GetSelectedRows()
            if sr:
                self.UpdateControls(sr[-1])
        p = self.dbperm
        if self.db_recid:
            p.Retrieve('perm.id_rel=%s', self.db_recid)
        else:
            p.Reset()
        pu = self.permute
        for n, (puid, pucod, pudes, pleg, pscr, pgg) in enumerate(pu):
            if p.Locate(lambda x: x.id_utente == puid):
                l = p.leggi
                s = p.scrivi
                g = p.gg
            else:
                l = s = g = 0
            pu[n][PERM_LEGGI] = l
            pu[n][PERM_SCRIVI] = s
            pu[n][PERM_GIORNI] = g
        self.gridperm.ResetView()
        self.FindWindowByName('catdoc').SetCatartAttive(self.FindWindowByName('id').GetValue())



    def CopyFrom_DoCopy(self, idcopy):
        ga.AnagPanel.CopyFrom_DoCopy(self, idcopy)
        self.LoadMovs(idcopy)
        for mov in self.dbmov:
            mov.id = None

    def LoadMovs(self, recid=None):
        if recid is None:
            recid = self.db_recid
        self.dbmov.Retrieve('tipmov.id_tipdoc=%s', recid)
        self._grid_mov.ChangeData(self.dbmov.GetRecordset())


# ---------------------------------------------------------------------------


class CauMagazzFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Causali magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(CauMagazzPanel(self, -1))


# ------------------------------------------------------------------------------


class CauMagazzDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Causali magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(CauMagazzPanel(self, -1))
