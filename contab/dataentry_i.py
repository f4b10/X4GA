#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry_i.py
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

import copy

import wx
import wx.grid as gl

import MySQLdb

from mx import DateTime

import Env
from Env import Azienda
bt = Azienda.BaseTab

import contab.scad          as scad
import contab.dataentry     as ctb
import contab.dataentry_wdr as wdr
import contab.iva           as ivalib

import awc.controls.windows   as aw
import awc.controls.linktable as lt
import awc.controls.dbgrid    as dbglib
import awc.util as awu

import awc
from awc.util import MsgDialog, MsgDialogDbError, GetNamedChildrens,\
                     DictNamedChildrens, GetAllChildrens

from awc.tables.util import GetRecordInfo

import cfg.cfgautomat as auto
import cfg.cfgprogr as progr

import anag
import anag.util as autil
from anag.pdc import PdcDialog
from anag.pdctip import PdcTipDialog

import stormdb as adb

from contab.util import SetWarningPag


(GridSelectedEvent, EVT_GRIDSELECTED) = wx.lib.newevent.NewEvent()

#costanti per recordset scadenze
RSSCA_DATA =    0
RSSCA_IMPORTO = 1
RSSCA_NOTE =    2
RSSCA_PCF_ID =  3
RSSCA_ISRIBA =  4

NDEC = 2


class GeneraPartiteMixin(scad.Scadenze):
    
    def __init__(self, *args, **kwargs):
        scad.Scadenze.__init__(self, *args, **kwargs)
        self.reg_modpag_id = None

    def InitPdcControls(self):
        pdcpa_ctrls = [x for x in GetAllChildrens(self)
                       if x.GetName().startswith('_pdcpa_')]
#        for x in pdcpa_ctrls:
#            try:
#                x.SetEditable(False)
#            except:
#                x.Disable()
        self.pdcpa_ctrls = pdcpa_ctrls
    
    def OnNumDocChanged(self, event):
        ndoc = self.controls['numdoc'].GetValue()
        self.reg_numdoc = ndoc
        self.UpdateButtons()
        event.Skip()
    
    def UpdateScadButtons(self, enable=True):
        if self.controls["button_end"].IsEnabled():
            tip = ''
            cnv = lambda x: self.FindWindowByName(x).GetValue()
            if self.status == ctb.STATUS_EDITING:
                if not tip and self._cfg_pcf == '1' and self.totdoc>0 and self.mp_id_pdcpi is None:
                    timp = 0
                    for s in self.regrss:
                        timp += (s[RSSCA_IMPORTO] or 0)
                        if not s[RSSCA_DATA] or not s[RSSCA_IMPORTO]:
                            tip = "Dati mancanti sulle scadenze"
                            break
                    if not adb.DbTable.samefloat(timp, self.totdoc):
                        tip = "Totale scadenze non congruente con il documento"
                if tip:
                    enable = False
            else:
                enable = False
            if not enable:
                self.controls["button_end"].Enable(enable)
            if tip:
                self.controls["button_end"].SetToolTipString(tip)
    
    def ScadReset(self):
        #reset recordset scadenze
        del self.regrss[:]
        del self.regrss_old[:]
        for ctrl in self.pdcpa_ctrls:
            name = ctrl.GetName()[7:]
            ctrl.SetValue(None)
    
    def InitPanelScad( self ):
        """
        Inizializzazione del pannello delle scadenze.
        In questa classe il metodo non ha effetto, in quanto il data entry
        del dettaglio Dare/Avere dipende dal tipo di registrazione.
        
        @see: sottoclassi di ContabDialog::
            ContabPanelTipo_I  - reg.iva
            ContabPanelTipo_E  - reg. sola iva
            ContabPanelTipo_C  - reg. composta
            ContabPanelTipo_S  - reg. semplice
            ContabPanelTipo_SC - reg. semplice in saldaconto
        """
        self.pansca = wx.Panel(self, wdr.ID_PANEL_SCAD)
        wdr.ScadFunc(self.pansca, True)
        self._GridEdit_Sca__Init__()
        self.Bind(lt.EVT_LINKTABCHANGED, self.OnModPagChanged,\
                  id = wdr.ID_MODPAG)
        self.Bind(wx.EVT_BUTTON, self.OnAnagDisplay, id=wdr.ID_ANAGDIALOG)
        self.Bind(wx.EVT_BUTTON, self.OnAnagChange, id=wdr.ID_ANAGCHANGE)
        self.Bind(wx.EVT_BUTTON, self.OnScadNew, id=wdr.ID_SCADNEW)
        self.Bind(wx.EVT_BUTTON, self.OnScadDel, id=wdr.ID_SCADDEL)
        self.Bind(wx.EVT_BUTTON, self.OnScadSud, id=wdr.ID_SCADSUD)
    
    def OnModPagChanged(self, event):
        newmp = self.controls["modpag"].GetValue()
        if self.reg_modpag_id != newmp:
            self.reg_modpag_id = newmp
            self.ScadCalc()
            self.UpdatePanelScad()
            self.UpdatePanelBody()
            self.UpdateButtons()
        event.Skip()
    
    def UpdateModPag(self, totimposta=0):
        """
        Aggiorna la modalità di pagamento in base al sottoconto della riga 1
        """
        if self._cfg_pcf != '1':
            return
        self.reg_modpag_id = self.InfoCliFor("id_modpag")
        self.controls["modpag"].SetValue(self.reg_modpag_id)
        self.ScadCalc(totimposta)
        self.UpdatePanelScad()
        self.UpdatePanelBody()
    
    def GetSelRowPaClass(self):
        return SelRowPa
    
    def OnAnagDisplay(self, event):
        tipo = GetRecordInfo(self.db_curs, bt.TABNAME_PDC, self.id_pdcpa, ('id_tipo',))[0]
        dc = autil.GetPdcDialogClass(tipo)
        if dc:
            dlg = dc(self, onecodeonly=self.id_pdcpa)
            dlg.OneCardOnly(self.id_pdcpa)
            dlg.CenterOnScreen()
            recid = dlg.ShowModal()
            dlg.Destroy()
            if recid>0:
                self.UpdatePanelCliFor()
                cvn = lambda x: self.FindWindowByName('_pdcpa_%s' % x).GetValue()
                for row in range(len(self.regrsb)):
                    if self.regrsb[row][ctb.RSDET_PDCPA_ID] == self.id_pdcpa:
                        self.regrsb[row][ctb.RSDET_PDCPA_cod] = cvn('codice')
                        self.regrsb[row][ctb.RSDET_PDCPA_des] = cvn('descriz')
                self._grid_dav.Refresh()
        event.Skip()

    def OnAnagChange(self, event):
        dlgPa = self.GetSelRowPaClass()(self, -1)
        dlgPa.id = self.id_pdcpa
        dlgPa.doc = self.totdoc
        dlgPa.controls['pdcpa'].SetValue(self.id_pdcpa)
        dlgPa.controls['totdoc'].SetValue(self.totdoc)
        dlgPa.controls['pdcpref'].Enable(False)
        if dlgPa.ShowModal() > 0:
            self.id_pdcpa = dlgPa.id
            self.totdoc = dlgPa.doc
            impd = self.totdoc; impa = None
            if self._cfg_pasegno == "A": impd, impa = impa, impd
            if (impd or 0) < 0:
                impa = -impd
                impd = None
            elif (impa or 0) < 0:
                impd = -impa
                impa = None
#            if self._cfg_pasegno == "A": impd, impa = impa, impd
            self.UpdateModPag()
            self.UpdatePanelCliFor()
            if len(self.regrsb) == 0:
                #crea riga partita
                self.regrsb.append([1,         #RSDET_NUMRIGA
                                    "C",       #RSDET_TIPRIGA
                                    dlgPa.id,  #RSDET_PDCPA_ID
                                    dlgPa.cod, #RSDET_PDCPA_cod
                                    dlgPa.des, #RSDET_PDCPA_des
                                    impd,      #RSDET_IMPDARE
                                    impa,      #RSDET_IMPAVERE
                                    None,      #RSDET_ALIQ_ID
                                    None,      #RSDET_ALIQ_cod
                                    None,      #RSDET_ALIQ_des
                                    None,      #RSDET_ALIQ_TOT
                                    None,      #RSDET_NOTE
                                    0])        #RSDET_RIGAPI
            else:
                #modifica cli/for su riga già esistente
                cvn = lambda x: dlgPa.FindWindowByName('_pdcpa_%s' % x).GetValue()
                r = self.regrsb[0]
                r[ctb.RSDET_PDCPA_ID] = self.id_pdcpa
                r[ctb.RSDET_PDCPA_cod] = cvn('codice')
                r[ctb.RSDET_PDCPA_des] = cvn('descriz')
            #adeguamento tot.doc.
            r = self.regrsb[0]
            r[ctb.RSDET_IMPDARE] = impd
            r[ctb.RSDET_IMPAVERE] = impa
            self._grid_dav.Refresh()
            self.UpdateTotDav()
        dlgPa.Destroy()
        event.Skip()

    def OnScadNew(self, event):
        """
        Aggiunge nuova scadenza
        """
        s = self.regrss
        s.append([None, #data scadenza
                  0,    #importo
                  '',   #note
                  None, #id partita
                  0])   #flag riba
        self.UpdatePanelScad()
        self.UpdateButtons()
        event.Skip()
    
    def OnScadDel(self, event):
        """
        Elimina scadenza selezionata
        """
        rows = self._grid_sca.GetSelectedRows()
        if len(rows) >= 1:
            row = rows[-1]
            del self.regrss[row]
            self.UpdatePanelScad()
            self.UpdateButtons()
        event.Skip()
    
    def OnScadSud(self, event):
        """
        Suddivide equamente gli importi delle scadenze
        """
        s = self.regrss
        if len(s) == 0:
            MsgDialog(self, message="Non ci sono scadenze su cui suddividere")
            return
        nd = Azienda.BaseTab.VALINT_DECIMALS
        rata = round(self.totdoc/len(s), nd)
        totrate = 0
        for n in range(len(s)-1):
            s[n][RSSCA_IMPORTO] = rata
            totrate += rata
        s[len(s)-1][RSSCA_IMPORTO] = round(self.totdoc-totrate, nd)
        self.UpdatePanelScad()
        self.UpdateButtons()
        event.Skip()
    
    def EnableScadControls(self, enable = True):
        enable = enable and self.status == ctb.STATUS_EDITING
        aw.awu.EnableControls(self.FindWindowById(wdr.ID_PANSCADSCAD),
                              enable and self._cfg_pcf == '1')
        for cid in (wdr.ID_ANAGDIALOG, wdr.ID_ANAGCHANGE):
            self.FindWindowById(cid).Enable(enable)
    
    def UpdatePanelScad(self):
        """
        Aggiorna i controlli mod.pag. e partite in base al corrente recordset
        relativo alle scadenze C{self.regrss}
        """
        if self._grid_sca is not None:
            self._grid_sca.ResetView()
            self._grid_sca.AutoSizeColumns()
            self.UpdateTotSca()

    def UpdateTotSca(self):
        totimp = sum( [x[RSSCA_IMPORTO] for x in self.regrss] )
        self.controls["totscad"].SetValue(totimp)
    
    def ScadCalc(self, totimposta=0):
        if self._cfg_pcf != '1':
            return
        del self.regrss[:]
        datdoc = self.controls["datdoc"].GetValue()
        if datdoc is None:
            datdoc = self.controls["datreg"].GetValue()
        scad = self.CalcolaScadenze(datdoc, self.reg_modpag_id,\
                                    self.totdoc, totimposta)
        note = [ x[RSSCA_NOTE] for x in self.regrss ]
        for data, imp, riba, cass in scad:
            self.regrss.append( [data, imp, None, None, riba] )
        if len(note) == len(self.regrss):
            for s in range(len(note)):
                self.regrss[s][RSSCA_NOTE] = note[s]
    
    def TestPagImm(self):
        if self.mp_id_pdcpi is not None:
            #pagamento immediato, genero righe di giroconto cli-for/cassa
            n = len(self.regrsb)-1
            if n>=0:
                note = "PAG. IMMEDIATO"
                r0 = self.regrsb[0]
                pdcpa_id =  r0[ctb.RSDET_PDCPA_ID]
                pdcpa_cod = r0[ctb.RSDET_PDCPA_cod]
                pdcpa_des = r0[ctb.RSDET_PDCPA_des]
                totd = r0[ctb.RSDET_IMPDARE]
                tota = r0[ctb.RSDET_IMPAVERE]
                r = self.regrsb[n][ctb.RSDET_NUMRIGA]+1
                if totd:
                    impd1 = 0
                    impa1 = totd
                    impd2 = totd
                    impa2 = 0
                else:
                    impd1 = tota
                    impa1 = 0
                    impd2 = 0
                    impa2 = tota
                #riga cli/for
                self.regrsb.append([r,         #RSDET_NUMRIGA
                                    "A",       #RSDET_TIPRIGA
                                    pdcpa_id,  #RSDET_PDCPA_ID
                                    pdcpa_cod, #RSDET_PDCPA_cod
                                    pdcpa_des, #RSDET_PDCPA_des
                                    impd1,     #RSDET_IMPDARE
                                    impa1,     #RSDET_IMPAVERE
                                    None,      #RSDET_ALIQ_ID
                                    None,      #RSDET_ALIQ_cod
                                    None,      #RSDET_ALIQ_des
                                    None,      #RSDET_ALIQ_TOT
                                    note,      #RSDET_NOTE
                                    1,         #RSDET_RIGAPI
                                    1])        #RSDET_SOLOCONT
                #riga cassa/banca
                pdcpa_id = self.mp_id_pdcpi
                pdcpa_cod = self.mp_pdcpi_cod
                pdcpa_des = self.mp_pdcpi_des
                r += 1
                self.regrsb.append([r,         #RSDET_NUMRIGA
                                    "A",       #RSDET_TIPRIGA
                                    pdcpa_id,  #RSDET_PDCPA_ID
                                    pdcpa_cod, #RSDET_PDCPA_cod
                                    pdcpa_des, #RSDET_PDCPA_des
                                    impd2,     #RSDET_IMPDARE
                                    impa2,     #RSDET_IMPAVERE
                                    None,      #RSDET_ALIQ_ID
                                    None,      #RSDET_ALIQ_cod
                                    None,      #RSDET_ALIQ_des
                                    None,      #RSDET_ALIQ_TOT
                                    note,      #RSDET_NOTE
                                    1,         #RSDET_RIGAPI
                                    1])        #RSDET_SOLOCONT

    def ScadStorno(self):
        """
        Storno partite.
        """
        out = False
        #storno importi scadenze da partite associate
        cmd1 =\
"""UPDATE %s SET imptot=imptot-%%s, imppar=imppar-%%s """\
"""WHERE id=%%s""" % bt.TABNAME_PCF
        par1 = []
        #elimino i riferimenti alle partite dopo averle stornate
        cmd2 =\
"""DELETE FROM %s WHERE id_reg=%%s""" % bt.TABNAME_CONTAB_S
        par2 = (self.reg_id,)
        for scad in self.regrss_old:
            pcf = scad[RSSCA_PCF_ID]
            imp = scad[RSSCA_IMPORTO]
            imptot = imppar = 0
            if self._cfg_pcfimp == '1':
                if   self._cfg_pcfsgn == '+':
                    imptot = imp
                elif self._cfg_pcfsgn == '-':
                    imptot = -imp
            elif self._cfg_pcfimp == '2':
                if   self._cfg_pcfsgn == '+':
                    imppar = imp
                elif self._cfg_pcfsgn == '-':
                    imppar = -imp
            par1.append((imptot, imppar, scad[RSSCA_PCF_ID]))
            
        try:
            x = self.db_curs.executemany(cmd1, par1)
            z = self.db_curs.execute(cmd2, par2)
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            out = True
        
        return True
    
    def ScadWrite(self):
        out = True
        try:
            nsca = 0
            last_datscad = None
            last_pcf_id = None
            for n, scad in enumerate(self.regrss):
                #aggiornamento partite
                pcf = scad[RSSCA_PCF_ID]
                imp = scad[RSSCA_IMPORTO]
                imptot = imppar = 0
                if self._cfg_pcfimp == '1':
                    if   self._cfg_pcfsgn == '+':
                        imptot = imp
                    elif self._cfg_pcfsgn == '-':
                        imptot = -imp
                elif self._cfg_pcfimp == '2':
                    if   self._cfg_pcfsgn == '+':
                        imppar = imp
                    elif self._cfg_pcfsgn == '-':
                        imppar = -imp
                note = scad[RSSCA_NOTE]
                if pcf is None and last_pcf_id is not None and scad[RSSCA_DATA] == last_datscad:
                    pcf = scad[RSSCA_PCF_ID] = last_pcf_id
                if pcf is None:
                    #creazione nuova partita
                    cmd =\
"""INSERT INTO %s ("""\
"""id_pdc, id_caus, id_modpag, riba, datdoc, """\
"""numdoc, datscad, imptot, imppar, note) """\
"""VALUES (%s)""" % (bt.TABNAME_PCF, ("%s, " * 10)[:-2] )
                    par = [ self.id_pdcpa,\
                            self.reg_cau_id,\
                            self.reg_modpag_id,\
                            scad[RSSCA_ISRIBA],\
                            self.reg_datdoc,\
                            self.reg_numdoc,\
                            scad[RSSCA_DATA],\
                            imptot,\
                            imppar,\
                            note]
                else:
                    #modifica partita esistente
                    cmd =\
"""UPDATE %s SET id_pdc=%%s, id_caus=%%s, id_modpag=%%s, riba=%%s, datdoc=%%s, """\
"""numdoc=%%s, datscad=%%s, imptot=imptot+%%s, imppar=imppar+%%s """\
"""WHERE id=%%s""" % bt.TABNAME_PCF
                    par = [ self.id_pdcpa,\
                            self.reg_cau_id,\
                            self.reg_modpag_id,\
                            scad[RSSCA_ISRIBA],\
                            self.reg_datdoc,\
                            self.reg_numdoc,\
                            scad[RSSCA_DATA],\
                            imptot,\
                            imppar,\
                            pcf ]
                
                self.db_curs.execute(cmd, par)
                if pcf is None:
                    self.db_curs.execute("SELECT LAST_INSERT_ID();")
                    rs = self.db_curs.fetchone()
                    pcf = int(rs[0])
                    self.regrss[nsca][RSSCA_PCF_ID] = pcf
                
                last_datscad = scad[RSSCA_DATA]
                last_pcf_id = pcf
                
                nsca += 1
            
            #scrittura riferimenti
            cmd =\
"""INSERT INTO %s (id_reg, id_pcf, datscad, importo, note) """\
"""VALUES (%s)""" % (bt.TABNAME_CONTAB_S, (r"%s, " * 5)[:-2] )
            par = [ [self.reg_id,\
                     scad[RSSCA_PCF_ID],\
                     scad[RSSCA_DATA],\
                     scad[RSSCA_IMPORTO],\
                     scad[RSSCA_NOTE] ] for scad in self.regrss ]
            self.db_curs.executemany(cmd, par)
            
            #elimino le partite che dopo lo storno sono andate a zero
            cmd =\
"""DELETE FROM %s WHERE id=%%s and imptot=0 and imppar=0""" % bt.TABNAME_PCF
            par = []
            for scad in self.regrss_old+self.regrss:
                pcf = scad[RSSCA_PCF_ID]
                par.append((pcf,))
            self.db_curs.executemany(cmd, par)
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            out = False
        
        return out

    def ScadRead(self, idreg):
        """
        Lettura delle scadenze della registrazione C{self.regrss}.
        """
        out = True
        cmd =\
"""SELECT sca.datscad, sca.importo, sca.note, pcf.id, pcf.riba """\
"""  FROM %s AS sca """\
"""  LEFT JOIN %s AS pcf ON sca.id_pcf=pcf.id """\
""" WHERE id_reg=%%s ORDER BY sca.datscad;"""\
            % (bt.TABNAME_CONTAB_S, bt.TABNAME_PCF)
        try:
            self.db_curs.execute(cmd, idreg)
            rss = self.db_curs.fetchall()
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            out = False
        else:
            del self.regrss[:]
            for scad in rss:
                self.regrss.append(list(scad))
            self.regrss_old = copy.deepcopy(self.regrss)
        return out

    def _GridEdit_Sca__Init__(self):
        
        if hasattr(self, '_grid_sca'):
            if self._grid_sca:
#                self._grid_sca.Destroy()
                wx.CallAfter(self._grid_sca.Destroy)
        
        parent = self.FindWindowById(wdr.ID_PANGRID_SCA)
#        parent.SetSize((0,0))
        size = parent.GetClientSizeTuple()
        grid = dbglib.DbGrid(parent, -1, size=size, style=0)
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE, 1, 
                       self._GridEdit_Sca_TestValues), )
        
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _STR = gl.GRID_VALUE_STRING
        
        grid.SetData( self.regrss, (\
            ( RSSCA_DATA,    "Scadenza", _DAT, False),
            ( RSSCA_IMPORTO, "Importo",  _IMP, False),
            ( RSSCA_ISRIBA,  "Ri.Ba.",   _CHK, False),
            ( RSSCA_NOTE,    "Note",     _STR, False),),
            afterEdit=afteredit,\
            canEdit=True, canIns=False)
        
        grid.SetFitColumn(-1)
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self._grid_sca = grid
    
    def _GridEdit_Sca_TestValues(self, row, gridcol, col, value):
        self.UpdateTotSca()
        self.UpdateButtons()
        return True
    
    def UpdatePanelCliFor(self):
        def cn(x):
            return self.FindWindowByName(x)
        cmd = """
        SELECT pdc.codice, pdc.descriz
          FROM %s pdc
         WHERE pdc.id=%%s""" % bt.TABNAME_PDC
        try:
            self.db_curs.execute(cmd, self.id_pdcpa)
            rs = self.db_curs.fetchone()
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            for n, c in enumerate(('codice', 'descriz',)):
                cn('_pdcpa_%s' % c).SetValue(rs[n])
            cmd = """
            SELECT pdctip.tipo 
              FROM %s pdc JOIN %s pdctip ON pdc.id_tipo=pdctip.id
             WHERE pdc.id=%%s""" % (bt.TABNAME_PDC, bt.TABNAME_PDCTIP)
            try:
                self.db_curs.execute(cmd, self.id_pdcpa)
                rs = self.db_curs.fetchone()
            except:
                pass
            else:
                tipo = rs[0]
                if    tipo == "C": tab = bt.TABNAME_CLIENTI
                elif  tipo == "F": tab = bt.TABNAME_FORNIT
                else:              tab = None
                if tab:
                    campi = 'indirizzo cap citta prov codfisc id_stato piva id_aliqiva'.split()
                    cmd = """
                    SELECT %s """ % ','.join(['anag.%s' % c for c in campi])
                    cmd += """
                    FROM %s anag
                    WHERE anag.id=%%s""" % tab
                    try:
                        self.db_curs.execute(cmd, self.id_pdcpa)
                        rs = self.db_curs.fetchone()
                    except MySQLdb.Error, e:
                        MsgDialogDbError(self, e)
                    else:
                        for n, c in enumerate(campi):
                            try:
                                cn('_pdcpa_%s' % c).SetValue(rs[n])
                            except:
                                pass
                        cn('_pdcpa_nazione').SetValue(cn('_pdcpa_id_stato').GetValueCod())
                        if hasattr(self, 'SetAliqIvaDefault'):
                            if campi[n] == 'id_aliqiva':
                                dbiva = adb.DbTable(bt.TABNAME_ALIQIVA, 'aliq')
                                if dbiva.Get(rs[n]) and dbiva.OneRow():
                                    self.SetAliqIvaDefault(dbiva)
                SetWarningPag(self.FindWindowByName('butattach'), self.id_pdcpa)
    
    def InfoCliFor(self, col):
        """
        Recupera informazioni dalla tabella del cliente o fornitore
        """
        out = None
        cmd =\
"""SELECT cli.%s, frn.%s """\
"""FROM %s AS pdc """\
"""LEFT JOIN %s AS cli ON cli.id=pdc.id """\
"""LEFT JOIN %s AS frn ON frn.id=pdc.id """\
"""WHERE pdc.id=%%s;""" % ( col, 
                            col, 
                            bt.TABNAME_PDC,
                            bt.TABNAME_CLIENTI,
                            bt.TABNAME_FORNIT )
        
        try:
            self.db_curs.execute(cmd, self.id_pdcpa)
            rs = self.db_curs.fetchone()
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            if rs[0] is None:
                out = rs[1]
            else:
                out = rs[0]
        return out


# ------------------------------------------------------------------------------


class ContabPanelTipo_I(ctb.ContabPanel,\
                        ivalib.IVA,\
                        GeneraPartiteMixin):
    """
    Data entry di contabilità: registrazioni con iva.
    La classe non è direttamente istanziabile in quanto il data entry
    varia a seconda se l'azienda è in contabilitò ordinaria o semplificata.
    Il data entry è realizzato dalle sottoclassi::
        ContabPanelTipo_I_O x contab.ordinaria
        ContabPanelTipo_I_S x contab.semplificata
        ContabPanelTipo_E   x registrazioni di sola iva.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Costruttore standard.
        """
        #pdc iva normale
        self._auto_pdciva_id = None
        self._auto_pdciva_cod = None
        self._auto_pdciva_des = None
        #pdc iva indeduc.
        self._auto_pdcind_id = None
        self._auto_pdcind_cod = None
        self._auto_pdcind_des = None
        #pdc iva cee
        self._auto_pdccee_id = None
        self._auto_pdccee_cod = None
        self._auto_pdccee_des = None
        #pdc iva sosp.
        self._auto_pdcsos_id = None
        self._auto_pdcsos_cod = None
        self._auto_pdcsos_des = None
        
        self.totimpon = 0
        self.totimpst = 0
        self.totivato = 0
        self.totinded = 0
        
        self.aliqdef_id = None  #aliquota predefinita del fornitore
        self.aliqdef_cod = None
        self.aliqdef_des = None
        
        self.totdoc = 0
        self.regrss = []       #recordset scadenze
        self.regrss_old = []   #recordset scadenze originale x storno modif.
        self._grid_sca = None
        
        ctb.ContabPanel.__init__(self, *args, **kwargs)
        
        self._Auto_AddKeysContabTipo_I()
        self.ReadAutomat()
        
        ivalib.IVA.__init__(self, self.db_curs)
        GeneraPartiteMixin.__init__(self, self.db_curs)
        
        self._progr_iva_ultins_num = 0
        
        self.dbrei = adb.DbTable(bt.TABNAME_REGIVA, 'rei')
        self.dbsrc = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg')
        self.dbsrc.AddJoin(bt.TABNAME_CFGCONTAB, 'caus', idLeft='id_caus', idRight='id')
        body = self.dbsrc.AddJoin(bt.TABNAME_CONTAB_B, 'body', idLeft='id', idRight='id_reg')
        body.AddJoin(bt.TABNAME_PDC, 'pdcpa', idLeft='id_pdcpa', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        
        self.Bind(lt.EVT_LINKTABCHANGED, self.OnRegIvaChanged, id=wdr.ID_REGIVA)
    
    def OnRegIvaChanged(self, event):
        if self.reg_id is None:
            if self.status == ctb.STATUS_EDITING:
                self.DefNumIva()
        else:
            cri = self.FindWindowById(wdr.ID_REGIVA)
            self.reg_regiva_id = cri.GetValue()
            self.reg_regiva_cod = cri.GetValueCod()
            self.reg_regiva_des = cri.GetValueDes()
        self.SetRegIvaParam()
        self.UpdateButtons()
        event.Skip()
    
    def DefNumIva(self):
        cri = self.FindWindowById(wdr.ID_REGIVA)
        self.reg_regiva_id = cri.GetValue()
        self.reg_regiva_cod = cri.GetValueCod()
        self.reg_regiva_des = cri.GetValueDes()
        dr = self.FindWindowByName('datreg').GetValue()
        if dr:
            year = dr.year
        else:
            year = None
        self._Progr_AddKeysContabTipo_I(year, self.reg_regiva_id)
        self.ReadProgr()
        self.DefaultValues()
        self.controls["numiva"].SetValue(self.reg_numiva)
        self.controls["numdoc"].SetValue(self.reg_numdoc)
    
    def InitCausale(self):
        """
        Inizializza il tipo di causale (C{"I"})
        """
        self.cautipo = "I"
        self.caufilt = "tipo='%s'" % self.cautipo
        return ctb.ContabPanel.InitCausale(self)
    
    def InitPanelBody(self):
        ctb.ContabPanel.InitPanelBody(self)
        self.InitPdcControls()
    
    def Validate(self):
        
        out = ctb.ContabPanel.Validate(self)
        
        if out:
            #test registro iva
            if self.reg_regiva_id is None:
                msg = "Manca l'attribuzione ad un registro IVA"
            else:
                rei = self.dbrei
                rei.Get(self.reg_regiva_id)
                msg = None
                if rei.lastprtdat is not None and self.reg_datreg<rei.lastprtdat:
                    msg = "La data di registrazione è antecedente l'ultima stampa definitiva del registro Iva"
                elif (rei.lastprtnum or 0)>0 and rei.lastprtdat.year == self.reg_datreg.year and self.reg_numiva<rei.lastprtnum:
                    msg = "Il numero di protocollo Iva è inferiore all'ultimo protocollo stampato in definitivo sul registro."
            if msg:
                awu.MsgDialog(self, msg, style=wx.ICON_ERROR)
                out = False
        
        if out:
            self.reg_numiva = self.controls["numiva"].GetValue()
            self.reg_modpag_id = self.controls["modpag"].GetValue()
        
        return out

    def RegSearchClass( self ):
        """
        Indica la classe da utilizzare per il dialog di ricerca delle
        registrazioni.
        """
        return Reg_I_SearchDialog
    
    def RegSearch( self ):
        out = False
        if self.cauid is not None:
            srccls = self.RegSearchClass()
            if srccls is not None:
                dlg = srccls(self)
                dlg.db_curs = self.db_curs
                dlg.SetCausale(self.cauid, self.caudes)
                dlg.SetRegIva(self.controls['id_regiva'].GetValue())
                dlg.UpdateSearch()
                idreg = dlg.ShowModal()
                dlg.Destroy()
                if idreg >= 0:
                    if self.RegRead(idreg):
                        if self.canedit and not self.reg_st_giobol and not self.reg_st_regiva:
                            self.SetRegStatus(ctb.STATUS_EDITING)
                        else:
                            self.SetRegStatus(ctb.STATUS_DISPLAY)
        return out
    
    def RegNew(self):
        if self.canins:
            dlgPa = self.GetSelRowPaClass()(self, -1)
            if self._cfg_id_pdcrow1:
                dlgPa.id = self._cfg_id_pdcrow1
                dlgPa.controls['pdcpa'].SetValue(self._cfg_id_pdcrow1)
            if dlgPa.ShowModal() > 0:
                cn = lambda x: self.FindWindowByName(x)
                regiva_id = cn('id_regiva').GetValue()
                regiva_cod = cn('id_regiva').GetValueCod()
                regiva_des = cn('id_regiva').GetValueDes()
                ctb.ContabPanel.RegNew(self)
                self.reg_regiva_id = regiva_id
                self.reg_regiva_cod = regiva_cod
                self.reg_regiva_des = regiva_des
                self.id_pdcpa = dlgPa.id
                self.totdoc = dlgPa.doc
                impd = self.totdoc; impa = None
                if self._cfg_pasegno == "A": impd, impa = impa, impd
                if (impd or 0) < 0:
                    impa = -impd
                    impd = None
                elif (impa or 0) < 0:
                    impd = -impa
                    impa = None
                self.UpdateModPag()
                self.UpdatePanelCliFor()
                if self._cfg_tipo != "E":
                    #crea riga partita
                    self.regrsb.append([1,         #RSDET_NUMRIGA
                                        "C",       #RSDET_TIPRIGA
                                        dlgPa.id,  #RSDET_PDCPA_ID
                                        dlgPa.cod, #RSDET_PDCPA_cod
                                        dlgPa.des, #RSDET_PDCPA_des
                                        impd,      #RSDET_IMPDARE
                                        impa,      #RSDET_IMPAVERE
                                        None,      #RSDET_ALIQ_ID
                                        None,      #RSDET_ALIQ_cod
                                        None,      #RSDET_ALIQ_des
                                        None,      #RSDET_ALIQ_TOT
                                        None,      #RSDET_NOTE
                                        0,         #RSDET_RIGAPI
                                        0])        #RSDET_SOLOCONT
                    nrig = 2
                    for cprow in dlgPa.rspref:
                        #crea righe c/partita da sottoconti preferiti
                        if cprow[0]:
                            self.AddDefaultRow([nrig,             #RSDET_NUMRIGA
                                                "C",              #RSDET_TIPRIGA
                                                cprow[1],         #RSDET_PDCPA_ID
                                                cprow[2],         #RSDET_PDCPA_cod
                                                cprow[3],         #RSDET_PDCPA_des
                                                None,             #RSDET_IMPDARE
                                                None,             #RSDET_IMPAVERE
                                                self.aliqdef_id,  #RSDET_ALIQ_ID
                                                self.aliqdef_cod, #RSDET_ALIQ_cod
                                                self.aliqdef_des, #RSDET_ALIQ_des
                                                None,             #RSDET_ALIQ_TOT
                                                None,             #RSDET_NOTE
                                                0,                #RSDET_RIGAPI
                                                0])               #RSDET_SOLOCONT
                            self._cfg_pdcpref_da[cprow[1]] = cprow[4] #segno
                            nrig += 1
                self.ReadProgr()
                self.DefaultValues()
                self.reg_nocalciva = 0
                if self._cfg_tipo == "E":
                    self.reg_nocalciva = 1
                
                import anag.dbtables as dba
                for cls in (dba.Clienti, dba.Fornit):
                    t = cls()
                    if t.Get(self.id_pdcpa) and t.OneRow():
                        if t.anag.aliqiva.id is not None:
                            self.SetAliqIvaDefault(t.anag.aliqiva)
                            if len(self.regrsb)>1:
                                self.InitPdcIndeduc(1)
                
                self.SetRegStatus(ctb.STATUS_EDITING)
                
            else:
                
                self.SetRegStatus(ctb.STATUS_SELCAUS)
            
            dlgPa.Destroy()
    
    def AddDefaultRow(self, row):
        self.regrsb.append(row)
    
    def SetAliqIvaDefault(self, *args, **kwargs):
        pass
    
    def InitPdcIndeduc(self, *args, **kwargs):
        pass
    
    def GetSottocontiIva(self, tipaliq):
        
        #id1,cod1,des1 x sottoconto iva
        #id2,cod2,des2 x sottoconto indeducibile
        
        tipo = tipaliq
        
        if not tipo:
            #aliquota normale
            id1 =  self._auto_pdciva_id
            cod1 = self._auto_pdciva_cod
            des1 = self._auto_pdciva_des
            id2 =  self._auto_pdcind_id
            cod2 = self._auto_pdcind_cod
            des2 = self._auto_pdcind_des
            
        elif tipo == "C":
            #aliquota cee
            id1 =  self._auto_pdccee_id
            cod1 = self._auto_pdccee_cod
            des1 = self._auto_pdccee_des
            id2 =  None
            cod2 = None
            des2 = None
            
        elif tipo == "S":
            #aliquota sospensione
            id1 =  self._auto_pdcsos_id
            cod1 = self._auto_pdcsos_cod
            des1 = self._auto_pdcsos_des
            id2 =  None
            cod2 = None
            des2 = None
        
        return id1, cod1, des1, id2, cod2, des2
    
    def RegReset(self):
        ctb.ContabPanel.RegReset(self)
        self.reg_numiva = None
        self.reg_modpag_id = None
        self.ScadReset()
        self.aliqdef_id = None
        self.aliqdef_cod = None
        self.aliqdef_des = None
        self.reg_nocalciva = None

    def DefaultValues(self):
        ctb.ContabPanel.DefaultValues(self)
        regiva = self.reg_regiva_id
#        numiva = self._progr_iva_ultins_num+1
#        if self._cfg_numiva == '1':
#            self.reg_numiva = numiva
        datreg = self.controls['datreg'].GetValue()
        if datreg:
            reg = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg', writable=False, fields=None)
            reg.Synthetize()
            reg.AddMaximumOf('numiva')
            reg.AddFilter('id_regiva=%s', regiva)
            reg.AddFilter('YEAR(datreg)=%s', datreg.year)
            if reg.Retrieve() and reg.OneRow():
#                numiva = max(numiva, (reg.max_numiva or 0)+1)
                numiva = (reg.max_numiva or 0)+1
                if self._cfg_numiva == '1':
                    self.reg_numiva = numiva
                if self._cfg_numdoc == '1':
                    self.reg_numdoc = "%s" % numiva
        self.ScadCalc()
    
    def OnCauChanged( self, event ):
        """
        Callback per causale selezionata.
        Oltre al normale comportamento del callback di C{ContabPanel},
        vengono aggiornati gli automatismi iva.
        """
        cauchanged = ctb.ContabPanel.OnCauChanged(self, event)
        if cauchanged:
            cmd ="""
            SELECT id_regiva
              FROM %s AS rim
              JOIN %s AS riv ON rim.id_regiva=riv.id
             WHERE rim.id_caus=%%s
          ORDER BY riv.codice""" % (bt.TABNAME_CFGMAGRIV,
                                    bt.TABNAME_REGIVA)
            c = self.db_curs
            c.execute(cmd, self.cauid)
            rs = c.fetchall()
            rim = []
            if self._cfg_regiva_id is not None:
                rim.append(str(self._cfg_regiva_id))
            rim += [str(x[0]) for x in rs]
            filter = "id IN (%s)" % ', '.join(rim)
            cri = self.FindWindowById(wdr.ID_REGIVA)
            cri.SetFilter(filter)
            cri.SetValue(self._cfg_regiva_id)
        
        return cauchanged
    
    def SetRegIvaParam(self):
        if self._cfg_regiva_tipo is None:
            return
        if self._cfg_regiva_tipo in "AVC":
            if   self._cfg_regiva_tipo == "A":
                self._auto_pdciva_id = self._auto_ivaacq
                self._auto_pdcind_id = self._auto_ivaind
                self._auto_pdccee_id = self._auto_ivaacqcee
                self._auto_pdcsos_id = self._auto_ivaacqsos
                
            elif self._cfg_regiva_tipo == "V":
                self._auto_pdciva_id = self._auto_ivaven
                self._auto_pdcind_id = self._auto_ivaind
                self._auto_pdccee_id = self._auto_ivaacqcee
                self._auto_pdcsos_id = self._auto_ivavensos
                
            elif self._cfg_regiva_tipo == "C":
                self._auto_pdciva_id = self._auto_ivacor
                self._auto_pdcind_id = None
                self._auto_pdccee_id = None
                self._auto_pdcsos_id = None
            
            self._auto_pdciva_cod, self._auto_pdciva_des =\
                GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                              self._auto_pdciva_id, ("codice","descriz"))
            
            self._auto_pdcind_cod, self._auto_pdcind_des =\
                GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                              self._auto_pdcind_id, ("codice","descriz"))
            
            self._auto_pdccee_cod, self._auto_pdccee_des =\
                GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                              self._auto_pdccee_id, ("codice","descriz"))
            
            self._auto_pdcsos_cod, self._auto_pdcsos_des =\
                GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                              self._auto_pdcsos_id, ("codice","descriz"))
            
            #if self._cfg_regiva_id is not None:
                #self._Progr_AddKeysContabTipo_I(ctb.YEAR,\
                                                #self._cfg_regiva_id)
    
    def OnDatRegChanged(self, event):
        if self.reg_id is None:
            if self.status == ctb.STATUS_EDITING:
                newdd = self.controls["datreg"].GetValue(adapt_year=False)
                if self.reg_datreg != newdd:
                    self.reg_datreg = newdd
                    if newdd:
                        self.DefNumIva()
                if self._cfg_datdoc == '1':
                    self.controls['datdoc'].SetValue(newdd)
                    self.RicalcolaScadenzeDaDataDocumento(forcericalc=True)
                self.UpdateButtons()
        event.Skip()
    
    def OnDatDocChanged(self, event):
        self.RicalcolaScadenzeDaDataDocumento()
        event.Skip()
    
    def RicalcolaScadenzeDaDataDocumento(self, forcericalc=False):
        newdd = self.controls["datdoc"].GetValue()
        if self.reg_datdoc != newdd or forcericalc:
            self.reg_datdoc = newdd
            self.ScadCalc()
            self.UpdatePanelScad()
            self.UpdatePanelBody()
        self.UpdateButtons()
    
    def OnNumIvaChanged(self, event):
        niva = self.controls['numiva'].GetValue()
        self.reg_numiva = niva
        if self.reg_id is None:
            if self._cfg_numdoc == '1':
                self.controls['numdoc'].SetValue(str(niva))
        event.Skip()
    
    def UpdateAllControls(self):
        ctb.ContabPanel.UpdateAllControls(self)
        self.controls["modpag"].SetValue(self.reg_modpag_id)
        self.UpdatePanelScad()

    def UpdateButtons(self, enable=True):
        ctb.ContabPanel.UpdateButtons(self, enable)
        if enable and self.status == ctb.STATUS_EDITING:
            c = self.controls["button_end"]
            if c.IsEnabled():
                if self.reg_regiva_id is None:
                    c.Enable(False)
                    c.SetToolTipString("Manca il registro IVA")
        self.UpdateScadButtons(enable)
    
    def IsIvaOK(self):
        return True
    
    def InitPanelHead(self):
        ctb.ContabPanel.InitPanelHead(self)
        for cid, func in ((wdr.ID_TXT_DATREG, self.OnDatRegChanged),
                          (wdr.ID_TXT_DATDOC, self.OnDatDocChanged)):
            self.Bind(wdr.EVT_DATECHANGED, func, id=cid)
        for cid, func in ((wdr.ID_TXT_NUMIVA, self.OnNumIvaChanged),
                          (wdr.ID_TXT_NUMDOC, self.OnNumDocChanged),):
            self.Bind(wx.EVT_TEXT, func, id=cid)
        self.InitPanelScad()

    def UpdatePanelHead(self):
        ctb.ContabPanel.UpdatePanelHead(self)
        regiva = self.controls["id_regiva"]
        numiva = self.controls["numiva"]
        if self.status != ctb.STATUS_SELCAUS:
            regiva.SetValueSilent(self.reg_regiva_id)
            numiva.SetValue(self.reg_numiva)

    def EnableAllControls(self, enable = True):
        ctb.ContabPanel.EnableAllControls(self, enable)
        self.EnableScadControls(enable)

    def RegSave(self):
        """
        Scrittura registrazione su db.  Oltre alla scrittura della
        registrazione, provvede a scrviere le scadenze e ad aggiornare
        le partite clienti/fornitori.
        """
        out = ctb.ContabPanel.RegSave(self)
        if out and self._cfg_pcf == '1':
            out = self.ScadStorno()
            if out:
                out = self.ScadWrite()
        return out
    
    def RegDelete(self):
        out = self.ScadStorno()
        if out:
            out = ctb.ContabPanel.RegDelete(self)
        return out
    
    def RegRead(self, idreg):
        out = ctb.ContabPanel.RegRead(self, idreg)
        self.SetRegIvaParam()
        #elimino righe giroc. cli/for-cassa x pag.immediato
        #vengono reinserite in fase di memorizzazione se occorre
        for r in range(len(self.regrsb)-1,0,-1):
            if self.regrsb[r][ctb.RSDET_RIGAPI] and self.regrsb[r][ctb.RSDET_TIPRIGA] not in "IO":
                self.regrsb.pop(r)
        try:
            n = awc.util.ListSearch(self.regrsb,\
                                    lambda x: x[ctb.RSDET_NUMRIGA] == 1)
        except:
            self.totdoc = 0
        if out:
            out = self.ScadRead(idreg)
            self.SetupModPag(self.reg_modpag_id)
        if out:
            self.UpdatePanelCliFor()
        return out

    def CheckNumIva(self, canForce=False, numiva=None, datreg=None):
        """
        Controllo di congruenza tra numero iva e data registrazione::
            Esito positivo se:
            - numero iva non presente       se immissione
            - numero iva >= precedente + 1  se esistente
            - numero iva <= successivo - 1  se esistente
            - data >= data precedente       se esistente
            - data <= data successiva       se esistente
            
            Esito positivo ma con messaggio di warning per numeri mancanti:
            - numero iva != precedente + 1  o primo numero dell'anno
            - numero iva != successivo - 1  se esistente
        """
        out = True
        if not self._cfg_numiva:
            self.reg_numiva = None
            return out
        ri = adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
        if not self.reg_numiva:
            if ri.Get(self.reg_regiva_id) and ri.OneRow():
                if ri.noprot:
                    if aw.awu.MsgDialog(self, "La registrazione dovrà essere protocollata successivamente, confermi?", style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                        self.reg_numiva = None
                        return out
        if numiva is None: numiva = self.reg_numiva
        if datreg is None: datreg = self.reg_datreg
        par = [datreg.year, self.reg_regiva_id, numiva]
        err = ""
        forcereq = False
        try:
            #test esistenza numero protocollo
            filt = ""
            if not self.newreg:
                filt = """reg.id!=%d and """ % self.reg_id
            filt += r"""year(reg.datreg)=%s and reg.id_regiva=%s """\
                     """and reg.numiva=%s """\
                     """and (det.numriga=1 or det.numriga IS NULL)"""
            cmd =\
"""SELECT reg.id, reg.datreg, cau.descriz, reg.numdoc, reg.datdoc, """\
"""pdc.descriz FROM contab_h  AS reg """\
"""JOIN %s AS cau ON cau.id=reg.id_caus """\
"""LEFT JOIN %s AS det ON reg.id=det.id_reg """\
"""LEFT JOIN %s AS pdc ON pdc.id=det.id_pdcpa """\
"""WHERE %s"""
            self.db_curs.execute(cmd % (bt.TABNAME_CFGCONTAB,\
                                        bt.TABNAME_CONTAB_B,\
                                        bt.TABNAME_PDC,\
                                        filt), par)
            rs = self.db_curs.fetchone()
            if rs:
                err =\
"""Il protocollo n.%s è già stato attribuito alla registrazione """\
"""#%d del %s:\n\n%s""" % ( self.reg_numiva,\
                            int(rs[0]),\
                            rs[1].Format().split()[0],\
                            rs[2])
                if rs[3]:
                    err +=  " n.%s" % rs[3]
                if rs[4]:
                    err += " del %s" % rs[4].Format().split()[0]
                if rs[5]:
                    err += ", di %s" % rs[5]
                #test possibilità di forzare il protocollo doppio, nel caso
                #in cui il numero documento sia diverso dalla reg. del
                #protocollo esistente.
                ndoc = self.controls['numdoc'].GetValue()
                if ndoc:
                    filt += ' AND reg.numdoc="%s"' % ndoc.replace('"','')
                    self.db_curs.execute(cmd % (bt.TABNAME_CFGCONTAB,\
                                                bt.TABNAME_CONTAB_B,\
                                                bt.TABNAME_PDC,\
                                                filt), par)
                    rs = self.db_curs.fetchone()
                    if not rs:
                        forcereq = True
            else:
                #determinazione numero/data prot. precedente e successivo
                #per controllo buchi numerazione e continuità delle date
                dprec = nprec = dnext = nnext = None
                n = 0
                filt = ""
                for cmdtype in (("MAX","<"), ("MIN",">")):
                    if not self.newreg:
                        filt = """reg.id!=%d""" % self.reg_id
                    if filt:
                        filt += """ and """
                    filt += """year(reg.datreg)=%s and """\
                            """reg.id_regiva=%s and reg.numiva"""\
                            % (datreg.year,\
                               self.reg_regiva_id)
                    cmd = """SELECT %s(reg.numiva) """\
                        """FROM %s AS reg """\
                        """WHERE %s%s%s""" % (cmdtype[0], 
                                              bt.TABNAME_CONTAB_H, 
                                              filt, 
                                              cmdtype[1], 
                                              numiva)
                    cmd = """SELECT datreg, numiva """\
                        """FROM %s AS reg """\
                        """WHERE %s=(%s)""" % (bt.TABNAME_CONTAB_H, 
                                               filt,
                                               cmd)
                    self.db_curs.execute(cmd)
                    rs = self.db_curs.fetchone()
                    if rs:
                        if n == 0:
                            dprec, nprec = rs
                            if not nprec:
                                nprec = 0
                            #print "prec: ", nprec, dprec
                        else:
                            dnext, nnext = rs
                            #print "next: ", nnext, dnext
                    n += 1
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            if not err:
                nprec = nprec or 0
                diff = numiva - nprec
                if diff > 1:
                    if nprec:
                        err =\
"""Il protocollo precedente risulta essere il numero %d: """ % nprec
                    else:
                        err =\
"""Non risultano protocolli precedenti, questo dovrebbe essere il primo: """
                    if diff == 2:
                        err +=\
"""manca il protocollo n.%d""" % (numiva-1)
                    else:
                        err +=\
"""mancano i protocolli dal n.%d al n.%d""" % (nprec+1, numiva-1)
                    forcereq = canForce
                
                if dprec and datreg < dprec:
                    if err:
                        err += """   Inoltre, la """
                    else:
                        err = """La """
                    err +=\
"""data di registrazione non può essere inferiore al %s, data di """\
"""registrazione del precedente protocollo n.%d""" % ( dprec.Format()[:10],\
                                                       nprec )
                
                if dnext and datreg > dnext:
                    if err:
                        err += """   Inoltre, la """
                    else:
                        err = """La """
                    err +=\
"""data di registrazione non può essere superiore al %s, data di """\
"""registrazione del successivo protocollo n.%d""" % ( dnext.Format()[:10],\
                                                       nnext )
                
            if err:
                out = False
                if forcereq:
                    err += "\n\nVuoi forzare la numerazione ?"
                    if MsgDialog( self, err,\
                                  "Numero protocollo IVA incongruente",\
                                  style = wx.ICON_WARNING\
                                |wx.YES_NO|wx.NO_DEFAULT ) == wx.ID_YES:
                        out = True
                else:
                    MsgDialog(self, err, style=wx.ICON_ERROR)
        
        return out
    
    def CheckDocumento(self):
        """
        Controllo che non ci sia già una registrazione dello stesso tipo,
        facente capo allo stesso cliente/fornitore e con lo stesso numero di 
        documento nell'anno della data documento.
        Se lo trovo, segnalo e chiedo conferma.
        """
        src = self.dbsrc
        src.ClearFilters()
        src.AddFilter('reg.id_regiva=%s', self.reg_regiva_id)
        if self.reg_cau_tipo == "E":
            nr = 2
        else:
            nr = 1
        src.AddFilter('body.numriga=%s', nr)
        src.AddFilter('body.id_pdcpa=%s', self.id_pdcpa)
        src.AddFilter('reg.numdoc=%s', self.reg_numdoc)
        if self.reg_datdoc:
            src.AddFilter('YEAR(reg.datdoc)=%s', self.reg_datdoc.year)
        if self.reg_id is not None:
            src.AddFilter('reg.id<>%s', self.reg_id)
        src.Retrieve()
        if src.IsEmpty():
            return True
        msg = \
            """Esiste già una registrazione su questo registro IVA,\n"""\
            """facente capo alla stessa anagrafica e con lo stesso\n"""\
            """numero di documento:\n\n"""
        msg += """%s %s n.%s del %s,\nregistrato il %s,\n%s %s\n\n"""\
            % (src.caus.codice, src.caus.descriz, src.numdoc, src.dita(src.datdoc), src.dita(src.datreg), src.body.pdcpa.codice, src.body.pdcpa.descriz)
        msg += """Confermi comunque la scrittura di questa registrazione?"""
        stl = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
        return awu.MsgDialog(self, msg, style=stl) == wx.ID_YES
    
    def UpdateModPag(self, totimposta=0):
        GeneraPartiteMixin.UpdateModPag(self, totimposta=self.totimpst)
    
    def UpdateRegIva(self):
        out = True
        #filt = r"codice=%s and keydiff=%s and key_id=%s"
        #lastnum = None
        #cmd =\
#"""SELECT progrnum FROM %s WHERE %s""" % (bt.TABNAME_CFGPROGR, filt)
        #par = ( "IVA_ULTINS",\
                #"%s" % self.reg_datreg.year,\
                #self.reg_regiva_id )
        #try:
            #self.db_curs.execute(cmd, par)
            #rs = self.db_curs.fetchone()
            #if rs:
                #lastnum = rs[0]
                #if self.reg_numiva > lastnum:
                    #cmd =\
#"""UPDATE %s SET progrnum=%%s, progrdate=%%s """\
#"""WHERE %s""" % (bt.TABNAME_CFGPROGR, filt)
                    #self.db_curs.execute(cmd, ( self.reg_numiva,\
                                                #self.reg_datreg ) + par)
            #else:
                #MsgDialog(self,"Progressivi di numerazione del registro iva non trovati")
        #except MySQLdb.Error, e:
            #MsgDialogDbError(self, e)
            #out = True
        
        return out

    def RegWriteHead(self):
        written = False
        if self.CheckNumIva(canForce = True):
            if self.CheckDocumento():
                written = ctb.ContabPanel.RegWriteHead(self)
                if written:
                    self.UpdateRegIva()
        return written
    
    def RegWriteBody(self, *args):
        self.TestPagImm()
        return ctb.ContabPanel.RegWriteBody(self, *args)
    

# ------------------------------------------------------------------------------


class SelRowPa(wx.Dialog):
    """
    Dialog per la selezione del sottoconto di partita, nonché degli
    eventuali sottoconti di contropartita preferiti, definiti nella causale
    e/o nel sottoconto di partita stesso.
    """
    def __init__(self, parent, id=-1, title="Ricerca sottoconto",\
                 pos=wx.DefaultPosition, size=(400,300),\
                 style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        
        wx.Dialog.__init__(self, parent, id, title, pos, size)
        
        self.id_cau = parent.cauid
        self.id = None
        self.cod = None
        self.des = None
        self.doc = 0
        
        self.db_curs = parent.db_curs
        self.rspref = []
        self._grid_pref = None
        
        self.FillContent()
        wx.CallAfter(self.SetFirstFocus)
        
        self.controls = DictNamedChildrens(self)
        self.controls["labeltipo"].SetLabel(parent._cfg_pdctippa_des)
        
        pdcpa = self.controls["pdcpa"]
        #pdcpa.SetFilterLinks((("Tipo sottoconto",\
                                #bt.TABNAME_PDCTIP,\
                                #"id_tipo",\
                                #PdcTipDialog,\
                                #None,\
                                #parent._cfg_pdctippa_id),))
        pdcpa.SetFilterValue(parent._cfg_pdctippa_id)
        
        #imposto la classe del dialog x ins/mod mediante funzione che
        #la cerca in base al tipo anagrafico selezionato
        
        def GetPdcPaTipo():
            return autil.GetPdcDialogClass(pdcpa.GetFilterValue())
        pdcpa.SetDynCard(GetPdcPaTipo)
        
        if 'totdoc' in self.controls:
            self.controls["totdoc"].SetValue(0)
        
        lt = ctb.linktab
        self.Bind(lt.EVT_LINKTABCHANGED,\
                  self.OnPdcPaChanged, self.controls["pdcpa"])
        
        self.Bind( wx.EVT_CLOSE, self.OnClose )
        self.Bind( wx.EVT_BUTTON, self.OnOk, id = wdr.ID_BTNOK )
        
        self.InitGridPref()
        self.UpdateGridPref()
    
    def FillContent(self):
        wdr.SelRowPaFunc(self)
    
    def SetFirstFocus(self):
        self.FindWindowByName('pdcpa').SetFocus()
    
    def InitGridPref(self):
        
        parent = self.FindWindowById(wdr.ID_PANGRID_PDCPREF)
        size = parent.GetClientSizeTuple()
        
        colmap = ((0, "Sel.",       gl.GRID_VALUE_BOOL+":1,0", False),
                  (2, "Cod.",       gl.GRID_VALUE_STRING,      False),
                  (3, "Sottoconto", gl.GRID_VALUE_STRING,      False))
        
        grid = dbglib.DbGridColoriAlternati(parent, -1, size=size, style=0)
        grid.SetData(self.rspref, colmap, canEdit=False)
        grid.SetDefaultColSize(1,70)
        grid.SetFitColumn(-1)
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self._grid_pref = grid
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_CLICK, self.OnGridClicked, grid)
        grid.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
    
    def OnKeyUp(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            row = self._grid_pref.GetSelectedRows()[0]
            self.InvertiFlag(row)
        event.Skip()
    
    def OnGridClicked(self, event):
        row = event.GetRow()
        if event.GetCol() == 0 and 0 <= row < len(self.rspref):
            self.InvertiFlag(row)
        event.Skip()
    
    def InvertiFlag(self, row):
        r = self.rspref[row]
        r[0] = 1-r[0]
        self._grid_pref.ResetView()
    
    def OnClose(self, event):
        self.EndModal(0)

    def OnOk(self, event):
        if self.Validate():
            if self.doc<0:
                #totale documento negativo, inverto i segni delle contropartite preferite presenti
                for cprow in self.rspref:
                    if type(cprow[4]) in (str, unicode) and cprow[4] in "DA":
                        cprow[4] = "DA"["AD".index(cprow[4])]
            self.EndModal(1)

    def Validate(self):
        out = True
        if 'totdoc' in self.controls:
            self.doc = self.controls["totdoc"].GetValue()
            if not self.doc:
                if MsgDialog(self,\
                        """Sei sicuro che il totale documento sia nullo ?""",\
                        "Richiesta di conferma",\
                        style = wx.ICON_QUESTION|\
                                wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                    out = False
        if out and self.id is None:
            MsgDialog(self,\
                      """Devi selezionare il sottoconto del documento""",\
                      style = wx.ICON_EXCLAMATION)
            out = False
        return out

    def OnPdcPaChanged(self, event):
        ctr = event.GetEventObject()
        self.id = ctr.GetValue()
        self.cod = ctr.GetValueCod()
        self.des = ctr.GetValueDes()
        self.UpdateGridPref()

    def SetCausale(self, idcau):
        self.id_cau = idcau
        self.UpdateGridPref()


    def UpdateGridPref(self):
        if self._grid_pref is not None:
            del self.rspref[:]
            for n in range(2):
                if n == 0: amb, key = 1, self.id_cau
                else:      amb, key = 2, self.id
                if key:
                    cmd = """
                    SELECT 0, pref.id_pdc, pdc.codice, pdc.descriz, pref.segno 
                    FROM %s AS pref 
                    JOIN %s AS pdc ON pref.id_pdc=pdc.id 
                    WHERE pref.ambito=%%s and pref.key_id=%%s
                    ORDER BY pdcord""" % (bt.TABNAME_CFGPDCP, bt.TABNAME_PDC)
                    try:
                        self.db_curs.execute(cmd, (amb, key))
                        rs = self.db_curs.fetchall()
                    except MySQLdb.Error, e:
                        MsgDialogDbError(self, e)
                    else:
                        for rec in rs:
                            self.rspref.append(list(rec))
            
            self._grid_pref.ResetView()
            self._grid_pref.AutoSizeColumns()


# ------------------------------------------------------------------------------


class Reg_I_SearchGrid(ctb.RegSearchGrid):
    
    def DefColumns(self):
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        return (( 80, ( 1, "Data reg.",  _DAT, False)),
                ( 30, ( 2, "Reg.",       _STR, False)),
                ( 60, ( 3, "Prot.",      _STR, False)),
                (200, ( 4, "Sottoconto", _STR, False)),
                ( 80, ( 5, "N.Doc.",     _STR, True )),
                ( 80, ( 6, "Data doc.",  _DAT, True )),
                (110, ( 7, "Dare",       _IMP, True )),
                (110, ( 8, "Avere",      _IMP, True )),
                (  1, ( 0, "#reg",       _STR, False)))
    
    def GetColumn2Fit(self):
        return 3


# ------------------------------------------------------------------------------


class Reg_I_SearchPanel(ctb.RegSearchPanel):
    
    wdrFiller = wdr.RegSearchFuncTipo_I
    GridClass = Reg_I_SearchGrid
    id_regiva = None
    
    def SetRegIva(self, ri):
        self.id_regiva = ri
    
    def UpdateSearch(self):
        dmin = self.datmin.GetValue()
        ctb.DATSEARCH1 = dmin
        dmax = self.datmax.GetValue()
        ctb.DATSEARCH2 = dmax
        filter = "reg.id_caus=%d" % self.cauid
        par = []
        if dmin:
            filter += " AND reg.datreg>=%s"
            par.append(dmin)
        if dmax:
            filter += " AND reg.datreg<=%s"
            par.append(dmax)
        try:
            wx.BeginBusyCursor()
            try:
                cmd = \
"""   SELECT reg.id, reg.datreg, riv.codice, reg.numiva, """\
"""          pdc.descriz, reg.numdoc, reg.datdoc, """\
"""IF(row.segno="D", row.importo, 0), IF(row.segno="A", row.importo, 0) """\
"""     FROM ((%s AS reg JOIN %s AS cau ON reg.id_caus=cau.id) """\
"""LEFT JOIN contab_b AS row ON row.id_reg=reg.id) """\
"""LEFT JOIN pdc AS pdc ON row.id_pdcpa=pdc.id """\
"""     JOIN regiva AS riv ON reg.id_regiva=riv.id """\
"""    WHERE (row.numriga=1 OR row.numriga IS NULL) and %s """\
""" ORDER BY reg.datreg, reg.numiva"""\
 % (bt.TABNAME_CONTAB_H, bt.TABNAME_CFGCONTAB, filter)
                db_curs = Env.adb.db.__database__._dbCon.cursor()
                db_curs.execute(cmd, par)
                rs = db_curs.fetchall()
                db_curs.close()
                self.gridsrc.ChangeData(rs)
                
            except MySQLdb.Error, e:
                MsgDialogDbError(self, e)
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


class Reg_I_SearchDialog(ctb.RegSearchDialog):
    """
    Ricerca registrazioni.
    Dialog per la ricerca di registrazioni della causale selezionata.
    """
    
    panelClass = Reg_I_SearchPanel
    
    def SetRegIva(self, *args, **kwargs):
        self.panel.SetRegIva(*args, **kwargs)
