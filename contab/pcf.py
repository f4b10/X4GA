#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/pcf.py
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

import sys

import wx
import wx.grid as gl

import MySQLdb

import Env
Esercizio = Env.Azienda.Esercizio
bt = Env.Azienda.BaseTab

import awc.controls.linktable as linktab

import awc
import awc.controls.windows as aw
from awc.util import MsgDialog, MsgDialogDbError, DictNamedChildrens
from awc.tables.util import CheckRefIntegrity

import awc.controls.dbgrid as dbglib

import contab.pcf_wdr as wdr

import stormdb as adb


#costanti per accesso a recordset partita
RSPCF_PDC_ID =    0
RSPCF_DATSCA =    1
RSPCF_DATDOC =    2
RSPCF_NUMDOC =    3
RSPCF_CAUS_ID =   4
RSPCF_CAUS_COD =  5
RSPCF_CAUS_DES =  6
RSPCF_MPAG_ID =   7
RSPCF_MPAG_COD =  8
RSPCF_MPAG_DES =  9
RSPCF_ISRIBA =   10
RSPCF_ISCASS =   11
RSPCF_ISINSOL =  12
RSPCF_IMPTOT =   13
RSPCF_IMPPAR =   14
RSPCF_IMPEFF =   15
RSPCF_NOTE =     16
RSPCF_EFFEME =   17
RSPCF_EFFCON =   18
RSPCF_EFFBAN =   19
RSPCF_EFFPDC =   20
RSPCF_EFFBAP =   21
RSPCF_EFFDAT =   22


#costanti per accesso a recordset riferimenti partita
RSSCA_DATREG =  0
RSSCA_REG_ID =  1
RSSCA_CAU_ID =  2
RSSCA_CAU_COD = 3
RSSCA_CAU_DES = 4
RSSCA_NUMDOC =  5
RSSCA_DATDOC =  6
RSSCA_IMPTOT =  7
RSSCA_IMPPAR =  8
RSSCA_NOTE =    9


YEAR = Env.Azienda.Esercizio.year
datelab = Env.Azienda.Esercizio.dataElab

FRAME_TITLE_PCF = "Scheda partita"


"""
Scheda partita cli/for con mastro riferimenti (storia partita)
"""

class GridPcfRif(dbglib.DbGrid):
    """
    Griglia riferimenti partita
    """
    def __init__(self, rsrif, parent, idGrid=None):
        
        dbglib.DbGrid.__init__(self, parent, -1, 
                               size=parent.GetClientSizeTuple(), 
                               style=wx.SUNKEN_BORDER,
                               idGrid=idGrid)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _FLV = bt.GetValIntMaskInfo()
        
        cols = (
            ( 80, (RSSCA_DATREG,  "Data reg.", _DAT, False)),
            ( 30, (RSSCA_CAU_COD, "Cod.",      _STR, False)),
            ( 90, (RSSCA_CAU_DES, "Causale",   _STR, False)),
            ( 50, (RSSCA_NUMDOC,  "Num.Doc.",  _STR, False)),
            ( 80, (RSSCA_DATDOC,  "Data Doc.", _DAT, False)),
            (110, (RSSCA_IMPTOT,  "Importi",   _FLV, False)),
            (110, (RSSCA_IMPPAR,  "Pareggiam.",_FLV, False)),
            (140, (RSSCA_NOTE,    "Note",      _STR, True )),
            ( 50, (RSSCA_REG_ID,  "#reg",      _STR, False)),
        )                                       
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        self.SetData(rsrif, colmap)
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        self.SetFitColumn(-2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class PcfPanel(aw.Panel):
    """
    Pannello  scheda partita cli/for con mastro riferimenti
    (grid storia partita).
    """
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.db_conn = Env.Azienda.DB.connection
        
        self.rsrif = [] #recordset riferimenti scadenze registrazioni
        self._gridrif = None
        self.datscad = None
        
        wdr.PcfPanelFunc(self)
        
        self._gridrif = GridPcfRif(self.rsrif, 
                                   self.FindWindowById(wdr.ID_PANELHIST),
                                   idGrid='storia_partita')
        
        self.controls = DictNamedChildrens(self)
        c = self.controls
        for name in ('riba', 'contrass', 'insoluto', 'f_effemes', 'f_effcont'):
            c[name].SetDataLink(name, {True: 1, False: 0})
            if name == 'riba': c[name].Bind(wx.EVT_CHECKBOX, self.OnRiba)
        
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=wdr.ID_BTNDEL)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
        
        for name in ('imptot', 'imppar'):
            c[name].Bind(wx.EVT_TEXT, self.OnImporti)
        
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnPdc, id=wdr.ID_PDC)
        self.Bind(wx.EVT_CHECKBOX, self.OnEffEmesso, id=wdr.ID_EFFEMESS)
    
    def OnEffEmesso(self, event):
        self.EnableEffControls()
        event.Skip()
    
    def EnableEffControls(self):
        cn = lambda x: self.FindWindowByName(x)
        isriba, efemes = map(lambda x: cn(x).GetValue(), ('riba', 'f_effemes'))
        cn('impeff').Enable(isriba)
        for name, e in (('id_effbap', isriba),
                        ('effdate',   isriba and efemes),
                        ('id_effban', isriba and efemes),
                        ('id_effpdc', isriba and efemes)):
            cn(name).Enable(e)
    
    def OnPdc(self, event):
        bancf = self.FindWindowById(wdr.ID_BANAPP)
        pdcid = event.GetEventObject().GetValue()
        if pdcid is None:
            bancf.SetFilter('0')
        else:
            bancf.SetFilter('id_pdc=%d' % pdcid)
        event.Skip()
    
    def OnRiba(self, event):
        self.EnableEffControls()
        event.Skip()

    def OnDelete(self, event):
        if self.DeletePcf():
            event.Skip()
    
    def OnSave(self, event):
        if self.Validate():
            if self.WritePcf():
                event.Skip()
    
    def Validate(self):
        out = True
        for cid, msg in ((wdr.ID_PDC, 'il sottoconto'),
                         (wdr.ID_CAUSALE, 'la causale'),
                         (wdr.ID_DATDOC, 'la data del documento'),
                         (wdr.ID_NUMDOC, 'il numero del documento'),
                         (wdr.ID_DATSCAD, 'la data di scadenza')):
            if not self.FindWindowById(cid).GetValue():
                aw.awu.MsgDialog(self, message='Manca %s' % msg)
                out = False
        return out
    
    def OnImporti(self, event):
        cn = lambda x: self.FindWindowByName(x)
        cn('saldo').SetValue(( cn('imptot').GetValue() or 0)
                             -(cn('imppar').GetValue() or 0))
        event.Skip()
    
    def UpdatePcf(self):
        pcf_id = self.GetParent().pcf_id
        out = False
        try:
            curs = self.db_conn.cursor()
            #estrazione recordset partita
            cmd =\
"""SELECT pcf.id_pdc, pcf.datscad, pcf.datdoc, pcf.numdoc, pcf.id_caus, """\
"""cau.codice, cau.descriz, pcf.id_modpag, mpa.codice, mpa.descriz, """\
"""pcf.riba, pcf.contrass, pcf.insoluto, """\
"""pcf.imptot, pcf.imppar, pcf.impeff, pcf.note, """\
"""pcf.f_effemes, pcf.f_effcont, pcf.id_effban, pcf.id_effpdc, pcf.id_effbap, pcf.effdate """\
"""FROM %s AS pcf """\
"""LEFT JOIN %s AS cau ON pcf.id_caus=cau.id """\
"""LEFT JOIN %s AS mpa ON pcf.id_modpag=mpa.id """\
"""WHERE pcf.id=%%s """\
"""ORDER BY pcf.datscad""" % ( bt.TABNAME_PCF, bt.TABNAME_CFGCONTAB,\
                               bt.TABNAME_MODPAG )
            par = (pcf_id,)
            curs.execute(cmd, par)
            rsp = curs.fetchone()
            c = self.controls
            if rsp:
                c['id_pcf'].SetValue(pcf_id)
                for name, col in (('id_pdc',    RSPCF_PDC_ID),
                                  ('datscad',   RSPCF_DATSCA),
                                  ('datdoc',    RSPCF_DATDOC),
                                  ('numdoc',    RSPCF_NUMDOC),
                                  ('id_caus',   RSPCF_CAUS_ID),
                                  ('id_modpag', RSPCF_MPAG_ID),
                                  ('riba',      RSPCF_ISRIBA),
                                  ('contrass',  RSPCF_ISCASS),
                                  ('insoluto',  RSPCF_ISINSOL),
                                  ('imptot',    RSPCF_IMPTOT),
                                  ('imppar',    RSPCF_IMPPAR),
                                  ('impeff',    RSPCF_IMPEFF),
                                  ('note',      RSPCF_NOTE),
                                  ('f_effemes', RSPCF_EFFEME),
                                  ('f_effcont', RSPCF_EFFCON),
                                  ('id_effban', RSPCF_EFFBAN),
                                  ('id_effpdc', RSPCF_EFFPDC),
                                  ('id_effbap', RSPCF_EFFBAP),
                                  ('effdate',   RSPCF_EFFDAT),
                                  ):
                    c[name].SetValue(rsp[col])
                    s = (rsp[RSPCF_IMPTOT] or 0) - (rsp[RSPCF_IMPPAR] or 0)
                c['saldo'].SetValue(s)
            self.datscad = rsp[RSPCF_DATSCA]
            pdc = c['id_pdc']
            pdc.Enable(pdc.GetValue() is None)
            
            #estrazione recordset riferimenti
            cmd =\
"""SELECT reg.datreg, reg.id, reg.id_caus, cau.codice, cau.descriz, """\
"""reg.numdoc, reg.datdoc, """\
"""if(cau.pcfimp=1, sca.importo*if(cau.pcfsgn='-', -1, 1), NULL), """\
"""if(cau.pcfimp=2, sca.importo*if(cau.pcfsgn='-', -1, 1), NULL), """\
"""sca.note """\
"""FROM %s AS pcf """\
"""JOIN %s AS sca ON sca.id_pcf=pcf.id """\
"""JOIN %s AS reg ON sca.id_reg=reg.id """\
"""JOIN %s AS cau ON reg.id_caus=cau.id """\
"""WHERE pcf.id=%%s """\
"""ORDER BY reg.datreg""" % ( bt.TABNAME_PCF, bt.TABNAME_CONTAB_S,\
                              bt.TABNAME_CONTAB_H, bt.TABNAME_CFGCONTAB )
            par = (pcf_id,)
            curs.execute(cmd, par)
            self.rsrif = curs.fetchall()
            self._gridrif.ChangeData(self.rsrif)
            self._gridrif.AutoSizeColumns()
            curs.close()
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            pdc = self.controls["id_pdc"]
            tipo = None
            if pdc.GetValue():
                dbpdc = adb.DbTable(bt.TABNAME_PDC, 'pdc')
                dbpdc.AddJoin(bt.TABNAME_PDCTIP, 'tipo')
                if dbpdc.Get(pdc.GetValue()) and dbpdc.RowsCount() == 1:
                    tipo = dbpdc.tipo.id
            else:
                dbtip = adb.DbTable(bt.TABNAME_PDCTIP, 'tipo')
                dbtip.AddOrder('tipo.codice')
                if dbtip.Retrieve("tipo.tipo='C'") and dbtip.RowsCount()>0:
                    tipo = dbtip.id
            pdc.SetFilterValue(tipo)
            self.EnableEffControls()
            out = True
        
        return out
    
    def WritePcf(self):
        pcf_id = self.GetParent().pcf_id
        out = False
        cols = ('id_pdc', 
                'datscad', 
                'datdoc', 
                'numdoc', 
                'id_caus', 
                'id_modpag', 
                'riba', 
                'contrass', 
                'insoluto', 
                'imptot',
                'imppar', 
                'impeff', 
                'note',
                'f_effemes',
                'f_effcont',
                'id_effban',
                'id_effpdc',
                'id_effbap',
                'effdate')
        cn = lambda n: self.FindWindowByName(n)
        values = [cn(x).GetValue() for x in cols]
        try:
            curs = self.db_conn.cursor()
            if pcf_id is None:
                #inserimento nuova partita
                cmd = """
INSERT INTO %s (%s) VALUES (%s)"""\
                    % (bt.TABNAME_PCF, 
                       ', '.join(cols),
                       (", %s"*len(values))[2:])
                curs.execute(cmd, values)
            else:
                #aggiornamento recordset partita
                repl = ['%s=%%s' % x for x in cols]
                cmd = """
UPDATE %s SET %s WHERE id=%s"""\
                    % (bt.TABNAME_PCF,
                       ', '.join(repl),
                       pcf_id)
                curs.execute(cmd, values)
            curs.close()
            
            if self.datscad:
                scadold = self.datscad
                scadnew = cn('datscad').GetValue()
                dbs = adb.DbTable(bt.TABNAME_CONTAB_S, 'sca', writable=True)
                dbs.Retrieve("sca.id_pcf=%s AND datscad=%s", pcf_id, scadold)
                for dbs in dbs:
                    dbs.datscad = scadnew
                if not dbs.Save():
                    aw.awu.MsgDialog(self, message=
                                     """Problema in scrittura scadenze:\n%s"""
                                     % repr(dbs.GetError()))
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            out = True
        
        return out
    
    def DeletePcf(self):
        pcf_id = self.GetParent().pcf_id
        if pcf_id is None: return False
        curs = adb.db.__database__._dbCon.cursor()
        constr = bt.TABSETUP_CONSTR_PCF
        do = CheckRefIntegrity(self, curs, constr, pcf_id)
        curs.close()
        if not do:
            return False
        if aw.awu.AskForDeletion(self, "Sicuro di voler cancellare la partita?"):
            try:
                curs = self.db_conn.cursor()
                cmd = """DELETE FROM %s WHERE id=%s""" % (bt.TABNAME_PCF, 
                                                          pcf_id)
                curs.execute(cmd)
                return True
            except MySQLdb.Error, e:
                MsgDialogDbError(self, e)
        return False
    

# ------------------------------------------------------------------------------


class PcfDialog(aw.Dialog):
    """
    Dialog scheda partita cli/for con mastro riferimenti
    (grid storia partita).
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_PCF
        aw.Dialog.__init__(self, *args, **kwargs)
        self.pcf_id = None
        self.pcfpanel = PcfPanel(self, -1)
        self.AddSizedPanel(self.pcfpanel)
        
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=wdr.ID_BTNDEL)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)

    def SetPcf(self, pcf_id):
        self.pcf_id = pcf_id
        self.pcfpanel.UpdatePcf()
    
    def OnSave(self, event):
        self.EndModal(1)
    
    def OnDelete(self, event):
        self.EndModal(2)
