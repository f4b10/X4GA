#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry.py
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
import awc.controls.dbgrid as dbglib

import MySQLdb

import awc.controls.windows as aw
from awc.controls.dbgrid import DbGrid
from awc.controls.datectrl import DateCtrl
from awc.controls.linktable import LinkTable

import Env
Esercizio = Env.Azienda.Esercizio
bt = Env.Azienda.BaseTab

import contab.dataentry_wdr as wdr

import awc.controls.linktable as linktab

import awc.util
from awc.util import MsgDialog, MsgDialogDbError

import cfg.cfgcontab as cfg
import cfg.cfgautomat as auto
import cfg.cfgprogr as progr
from cfg.dbtables import ProgrEsercizio

from cfg.dbtables import ProgrStampaGiornale, ProgrStampaMastri


#costanti per l'uscita dal dialog se modale
REG_UNMODIFIED = 0
REG_MODIFIED =   1
REG_DELETED =    2


#costanti per lo status del frame
STATUS_SELCAUS = 0
STATUS_DISPLAY = 1
STATUS_EDITING = 2


#costanti per recordset righe dettaglio (corpo)
RSDET_NUMRIGA =   0
RSDET_TIPRIGA =   1
RSDET_PDCPA_ID =  2
RSDET_PDCPA_cod = 3
RSDET_PDCPA_des = 4
RSDET_IMPDARE =   5
RSDET_IMPAVERE =  6
RSDET_ALIQ_ID =   7
RSDET_ALIQ_cod =  8
RSDET_ALIQ_des =  9
RSDET_ALIQ_TOT = 10
RSDET_NOTE =     11
RSDET_RIGAPI =   12
RSDET_last_col =\
RSDET_SOLOCONT = 13


class ContabPanel(aw.Panel,\
                  cfg.CfgCausale,\
                  auto.CfgAutomat,\
                  progr.CfgProgr ):
    """
    Data entry di contabilità.
    """
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.caudisp = [ ("codice",  "Cod."),\
                         ("descriz", "Causale") ]
        self.caurs = []
        self.cauid = None
        self.caudes = None
        self.cauconfig = None
        self.oneregonly_id = None
        self.canins = True
        self.canedit = True
        self.candelete = True
        self.editing = False
        self.totdare = 0
        self.totavere = 0
        self.id_pdcpa = None
        self.modified = False
        self.newreg = False
        
        self.reg_id = None
        self.reg_esercizio = None
        self.reg_cau_id = None
        self.reg_cau_tipo = None
        self.reg_datreg = None
        self.reg_datdoc = None
        self.reg_numdoc = None
        self.reg_regiva_id = None
        self.reg_numiva = None
        self.reg_modpag_id = None
        self.reg_regiva_cod = None
        self.reg_regiva_des = None
        self.reg_st_regiva = None
        self.reg_st_giobol = None
        self.reg_nocalciva = None
        
        self._grid_dav = None  #grid dare-avere
        
        self.dbprog = ProgrStampaGiornale()
        self.dbprom = ProgrStampaMastri()
        
        self.db_conn = Env.Azienda.DB.connection
        try:
            self.db_curs = self.db_conn.cursor()
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            
        else:
            #auto.CfgAutomatContab.__init__(self, self.db_curs)
            self._auto_cod_tippdc_pdciva = "I" #DA AUTOMATIZZARE!!!
            self._auto_cod_tippdc_pdcric = "R" #DA AUTOMATIZZARE!!!
            self._auto_cod_tippdc_pdcspe = "S" #DA AUTOMATIZZARE!!!
            
            cfg.CfgCausale.__init__(self, self.db_curs)
            auto.CfgAutomat.__init__(self, self.db_curs)
            progr.CfgProgr.__init__(self, self.db_curs)
            
            self._Auto_AddKeysContab()
            self._Progr_AddKeysContab(Env.Azienda.Esercizio.year)
            
            #self.cfgctb = cfg.CfgContab()
            self.dbese = ProgrEsercizio()
            
            self.regrsb = []       # recordset dettaglio
            
            self.status = None
            
            self.cautipo = None
            self.caufilt = None
            
            self.pancaus = None
            self.panhead = None
            self.panbody = None
            
            self.InitPanelCaus()
            self.InitPanelHead()
            self.InitPanelBody()
            
            wdr.DialogFunc( self, True )
            
            self.controls = awc.util.DictNamedChildrens(self)
            
            c = self.controls["butattach"]
            c.SetScope("contab_h")
            c.SetAutoText(self.controls['autonotes'])
            c.SetSpyPanel(self.FindWindowByName('attachspy'))
            
            butnew = self.controls["button_new"]
            butsrc = self.controls["button_search"]
            butend = self.controls["button_end"]
            butmod = self.controls["button_modify"]
            butquit = self.controls["button_quit"]
            butdel = self.controls["button_delete"]
            
            self.InitCausale()
            
            self.__postInit()
            
            self.Bind(wx.EVT_BUTTON, self.OnRegNew,    butnew)
            self.Bind(wx.EVT_BUTTON, self.OnRegSearch, butsrc)
            self.Bind(wx.EVT_BUTTON, self.OnRegEnd,    butend)
            self.Bind(wx.EVT_BUTTON, self.OnRegModify, butmod)
            self.Bind(wx.EVT_BUTTON, self.OnRegQuit,   butquit)
            self.Bind(wx.EVT_BUTTON, self.OnRegDelete, butdel)
            
            self.Bind(wx.EVT_SIZE,   self.OnResize)
    
    def GetSegnoInvertito(self, segno):
        if segno == "D":
            return "A"
        elif segno == "A":
            return "D"
        return None
    
    def __postInit(self):
        
        self.SetAcceleratorKey('I', wdr.ID_BTN_NEW,    'Inserisci',           'Inserisce una nuova registrazione')
        self.SetAcceleratorKey('C', wdr.ID_BTN_SEARCH, 'Cerca',               'Cerca registrazioni con la stessa causale')
        self.SetAcceleratorKey('S', wdr.ID_BTN_END,    'Salva e Chiudi',      'Salva e chiude la presente registrazione')
        self.SetAcceleratorKey('M', wdr.ID_BTN_MODIFY, 'Modifica',            'Modifica la presente registrazione')
        self.SetAcceleratorKey('X', wdr.ID_BTN_DELETE, 'Elimina',             'Elimina la presente registrazione')
        self.SetAcceleratorKey('Q', wdr.ID_BTN_QUIT,   'Abbandona modifiche', 'Abbandona la registrazione senza salvare')
        
        self.UpdatePanelHead()
        self.UpdatePanelBody()
        
        self.SetRegStatus(STATUS_SELCAUS)

    def OnParity(self, event):
        #sq = round(self.totdare-self.totavere, bt.VALINT_DECIMALS)
        row = self._grid_dav.GetGridCursorRow()
        if len(self.regrsb) == 0 or row>=len(self.regrsb):
            return
        td, ta = self.GetTotaliDA()
        sq = round(td-ta, 6)
        if len(self.regrsb) <= 1 or self.regrsb[row][RSDET_TIPRIGA] == 'A'\
           or self.regrsb[row][RSDET_IMPDARE] or self.regrsb[row][RSDET_IMPAVERE]:
            aw.awu.MsgDialog(self, 
                             """E' possibile pareggiare solo una riga sprovvista di importo.""",
                             style=wx.ICON_INFORMATION)
            return
        if sq>0:
            self.regrsb[row][RSDET_IMPAVERE] = sq
            self.regrsb[row][RSDET_IMPDARE] = None
        else:
            self.regrsb[row][RSDET_IMPAVERE] = None
            self.regrsb[row][RSDET_IMPDARE] = -sq
        self._grid_dav.ResetView()
        self.UpdateTotDav()
        event.Skip()
    
    def OnRegNew( self, event ):
        if self.status == STATUS_SELCAUS:
            self.RegNew()
    
    def OnRegSearch( self, event ):
        if self.status == STATUS_SELCAUS:
            self.RegSearch()
        elif self.status == STATUS_DISPLAY:
            self.SetRegStatus(STATUS_SELCAUS)

    def OnRegEnd( self, event ):
        if round(self.totdare,6) == round(self.totavere,6):
            if self.RegSave():
                if self.oneregonly_id:
                    try:
                        if self.GetParent().IsModal():
                            self.GetParent().EndModal(REG_MODIFIED)
                    except:
                        self.Destroy()
                else:
                    self.SetRegStatus(STATUS_SELCAUS)
        else:
            MsgDialog(self,\
"""Non è possibile confermare la registrazione in quanto risulta """\
"""squadrata.  Eliminare la squadratura e riprovare.""")
    
    def OnRegModify(self, event):
        self.SetRegStatus(STATUS_EDITING)
        event.Skip()
    
    def OnRegQuit( self, event ):
        quit = True
        if self.editing:
            action = MsgDialog(self,\
"""La registrazione risulta essere modificata.  confermandone """\
"""l'abbandono, andranno persi i dati fin qui inseriti.  """\
"""Confermi l'abbandono ?""",\
                        style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
            quit = (action == wx.YES)
        if quit:
            if self.oneregonly_id:
                try:
                    if self.GetParent().IsModal():
                        self.GetParent().EndModal(REG_UNMODIFIED)
                except:
                    self.Destroy()
            else:
                self.SetRegStatus(STATUS_SELCAUS)

    def OnRegDelete(self, event):
        action = MsgDialog(self,\
"""Sei sicuro di voler cancellare la registrazione ?  Confermando, la """\
"""registrazione non sarà più recuperabile in alcun modo.  """\
"""Confermi l'operazione di eliminazione ?""",\
                  style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if action == wx.ID_YES:
            if self.RegDelete():
                self.SetRegStatus(STATUS_SELCAUS)
                event.Skip()

    def OnResize(self, event):
        self.UpdatePanelBody()
        event.Skip()

    def RegSearch( self ):
        out = False
        if self.cauid is not None:
            srccls = self.RegSearchClass()
            if srccls is not None:
                dlg = srccls(self)
                dlg.db_curs = self.db_curs
                dlg.SetCausale(self.cauid, self.caudes)
                dlg.UpdateSearch()
                idreg = dlg.ShowModal()
                dlg.Destroy()
                if idreg >= 0:
                    if self.RegRead(idreg):
                        if self.canedit:
                            self.SetRegStatus(STATUS_EDITING)
                        else:
                            self.SetRegStatus(STATUS_DISPLAY)
        return out
    
    def SetOneRegOnly(self, idreg):
        self.oneregonly_id = idreg
        if self.RegRead(idreg):
            for name in 'button_new button_search'.split():
                self.FindWindowByName(name).Hide()
            p = self.GetParent()
            s = p.GetSize()
            p.SetSize((s[0]+1, s[0]+1))
            p.SetSize(s)
            self.UpdateCausale()
            self.SetRegStatus(STATUS_DISPLAY)
            self.UpdateButtons()

    def UpdateAllControls(self):
        if   self.status == STATUS_SELCAUS: lbl = "Seleziona causale"
        elif self.status == STATUS_DISPLAY: lbl = "Visualizzazione"
        elif self.status == STATUS_EDITING:
            if self.reg_id is None: lbl = "Inserimento"
            else:                   lbl = "Modifica"
        self.controls["statusdes"].SetLabel(lbl)
        self.UpdatePanelHead()
        self.UpdatePanelBody()
    
    def UpdateCausale(self):
        #aggiorna combo causale in base a self.cauid
        caus = self.controls['causale']
        #n = caus.GetCount()
        #for x in range(n):
            #cauid, caucod = caus.GetClientData(x)
            #if cauid == self.cauid:
                #caus.SetSelection(x)
                #break
        caus.SetValue(self.cauid)

    def RegSearchClass( self ):
        return RegSearchDialog
    
    def InitCausale( self ):
        """
        Inizializza il combobox della selezione causale.
        
        @return: Vero o falso a seconda che sia riuscito a caricare
        le causali.
        @rtype: bool
        """
        out = False
        ctrcau = self.controls["causale"]
        if self.caufilt:
            f = self.caufilt
            if not self.dbese.GetSovrapposizione():
                if f:
                    f = "(%s) AND " % f
                f += "esercizio<>'1'"
            ctrcau.SetFilter(f)
        self.Bind(linktab.EVT_LINKTABCHANGED, self.OnCauChanged, ctrcau)
        #try:
            #cmd =\
#"""SELECT id, codice, descriz """\
#"""FROM %s AS cau """\
#"""WHERE %s ;""" % ( bt.TABNAME_CFGCONTAB, 
                     #self.caufilt )
            #self.db_curs.execute( cmd )
            #self.caurs = self.db_curs.fetchall()
        #except MySQLdb.Error, e:
            #MsgDialogDbError(self, e)
        #else:
            #ctrcau.Clear()
            #for rec in self.caurs:
                #ctrcau.Append( rec[2], ( int(rec[0]), rec[1] ) )
            #out = True
        return out
    
    def OnCauChanged( self, event ):
        """
        Callback per causale selezionata
        Vengono aggiornati i dati relativi alla causale: ::
            id
            codice
            descrizione
            configurazione
        """
        cauchanged = False
        ctrcau = event.GetEventObject()
        oldcau = self.cauid
        cauid = ctrcau.GetValue()
        self.cauid = cauid
        if cauid is None:
            self.caudes = None
            self.UpdateButtons()
        else:
            self.caudes = ctrcau.GetValueDes()
            self.CfgCausale_Read(self.cauid)
            self.EnableAllControls()
            self.SetDefaultItem(self.controls['button_new'])
            cauchanged = (self.cauid != oldcau)
        return cauchanged
    
    def InitPanelCaus( self ):
        """
        Inizializza il pannello della selezione causale.
        """
        self.pancaus = aw.Panel(self, wdr.ID_PANEL_CAUS)
        self.pancaus.SetName('panelcausale')
        self.pancaus.HelpBuilder_SetDir('contab.dataentry.Causale')
        wdr.CauRegFunc(self.pancaus, True)

    def InitPanelHead( self ):
        """
        Inizializzazione del pannello di testata.
        In questa classe il metodo non ha effetto, in quanto il data entry
        del dettaglio Dare/Avere dipende dal tipo di registrazione.
        
        @see: sottoclassi di ContabPanel::
            ContabPanelTipo_I  - reg.iva
            ContabPanelTipo_E  - reg. sola iva
            ContabPanelTipo_C  - reg. composta
            ContabPanelTipo_S  - reg. semplice
            ContabPanelTipo_SC - reg. semplice in saldaconto
        """
        self.panhead = aw.Panel(self, wdr.ID_PANEL_HEAD)
        self.panhead.SetName('panelhead')
        self.panhead.HelpBuilder_SetDir('contab.dataentry.Testata')
        wdr.HeadFunc(self.panhead, True)
        h = bt.tabelle[bt.TABSETUP_TABLE_CONTAB_H][bt.TABSETUP_TABLESTRUCTURE]
        n = aw.awu.ListSearch(h, lambda x: x[0] == 'numdoc')
        self.FindWindowByName('numdoc').SetMaxLength(h[n][2])
        return self
    
    def InitPanelBody( self ):
        """
        Inizializzazione del pannello del corpo.
        In questa classe il metodo non ha effetto, in quanto il data entry
        del dettaglio Dare/Avere dipende dal tipo di registrazione.
        """
        self.panbody = wx.Panel(self, wdr.ID_PANEL_BODY)
        return self
    
    def SetRegStatus( self, status = None):
        """
        Imposta lo status della registrazione::
            STATUS_SELCAUS - Selezione causale
            STATUS_DISPLAY - Visualizza registrazione
            STATUS_MODIFY  - Editing registrazione
        """
        oldstatus = self.status
        self.status = status
        btnatt = self.controls['butattach']
        if status == STATUS_SELCAUS:
            self.RegReset()
            btnatt.SetKey(None)
            def SetFocus():
                self.controls['causale'].SetFocus()
            wx.CallAfter(SetFocus)
        elif status == STATUS_EDITING:
            def SetFocus():
                self.controls['datreg'].SetFocus()
            wx.CallAfter(SetFocus)
        self.UpdateAllControls()
        self.EnableAllControls()
        if status == STATUS_EDITING:
            btnatt.SetPermissions(True, True)
        else:
            btnatt.SetPermissions(False, False)
        return oldstatus
    
    def EnableAllControls(self, enable = True):
        self.UpdateButtons(enable)
        self.controls["causale"].Enable(enable and\
                                        self.status == STATUS_SELCAUS)
        self.EnableHeadControls(enable)
        self.EnableBodyControls(enable)

    def UpdateButtons(self, enable = True):
        status = self.status
        self.controls["button_new"].Enable(enable and\
                                           self.canedit and\
                                           self.canins and\
                                           self.cauid is not None and\
                                           status == STATUS_SELCAUS)
        
        self.controls["button_search"].Enable(enable and\
                                              self.cauid is not None and\
                                              status == STATUS_SELCAUS)
        
        c = self.controls["button_end"]
        ena = True
        if enable and status == STATUS_EDITING:
            if self.dbese.samefloat(self.totdare, self.totavere):
                if self._cfg_datdoc and not self.controls["datdoc"].GetValue():
                    tip = "Definire la data del documento"
                    ena = False
                elif self._cfg_numdoc and not self.controls["numdoc"].GetValue():
                    tip = "Definire il numero del documento"
                    ena = False
                else:
                    tip = "Conferma la registrazione"
            else:
                tip = "Squadratura Dare/Avere"
                ena = False
        else:
            tip = ""
            ena = False
        c.Enable(ena)
        c.SetToolTipString(tip)
        
        self.controls["button_modify"].Enable(enable and\
                                              self.canedit and\
                                              not(self.reg_st_regiva) and\
                                              not(self.reg_st_giobol) and\
                                              status == STATUS_DISPLAY)
        
        self.controls["button_quit"].Enable(enable and\
                                            status in (STATUS_DISPLAY,
                                                       STATUS_EDITING))
        
        self.controls["button_delete"].Enable(enable and\
                                              self.candelete and\
                                              status == STATUS_EDITING and\
                                              not self.newreg)
        
        self.controls["butattach"].Enable(enable and status in (STATUS_DISPLAY,
                                                                STATUS_EDITING))

    def RegRead(self, idreg):
        self.newreg = False
        out = self.RegReadHead(idreg)
        if out:
            self.CfgCausale_Read(self.cauid) #cauid settato in RegRead
            self.RegReadBody(idreg)
            if len(self.regrsb)>0:
                self.id_pdcpa = self.regrsb[0][RSDET_PDCPA_ID]
        self.controls['butattach'].SetKey(idreg)
        return out
    
    def RegReadHead(self, idreg):
        """
        Caricamento dati testata registrazione.
        """
        out = False
        rsh = []
        try:
            cmd =\
                """SELECT reg.id, reg.esercizio, reg.id_caus, reg.tipreg, """\
                """reg.datreg, reg.datdoc, reg.numdoc, """\
                """reg.id_regiva, reg.numiva, """\
                """reg.st_regiva, reg.st_giobol, """\
                """reg.id_modpag, reg.nocalciva, """\
                """riv.codice, riv.descriz """\
                """FROM %s AS reg """\
                """LEFT JOIN %s AS riv ON reg.id_regiva=riv.id """\
                """WHERE reg.id=%%s;""" % ( bt.TABNAME_CONTAB_H,\
                                            bt.TABNAME_REGIVA )
            self.db_curs.execute(cmd, idreg)
            rsh = self.db_curs.fetchone()
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            if rsh:
                self.reg_id,\
                self.reg_esercizio,\
                self.reg_cau_id,\
                self.reg_cau_tipo,\
                self.reg_datreg,\
                self.reg_datdoc,\
                self.reg_numdoc,\
                self.reg_regiva_id,\
                self.reg_numiva,\
                self.reg_st_regiva,\
                self.reg_st_giobol,\
                self.reg_modpag_id,\
                self.reg_nocalciva,\
                self.reg_regiva_cod,\
                self.reg_regiva_des = rsh
                self.reg_id = int(self.reg_id)
                self.cauid = self.reg_cau_id
                self._cfg_regiva_id = self.reg_regiva_id
                self._cfg_regiva_cod = self.reg_regiva_cod
                self._cfg_regiva_des = self.reg_regiva_des
                out = True
            else:
                MsgDialog(self, "La registrazione #%d non è stata trovata."\
                          % idreg)
        return out

    def RegSave(self):
        """
        Scrittura registrazione su db.
        """
        out = False
        if self.Validate():
            newreg = (self.reg_id is None)
            headw = self.RegWriteHead()
            if headw:
                bodyw = self.RegWriteBody()
                if bodyw:
                    if self._cfg_id_tipevent and self._cfg_event_msg:
                        self.GeneraEvento(newreg)
                    self.controls['butattach'].SetKey(self.reg_id, save=True)
                    out = True
                else:
                    self.RegDelete()
        return out
    
    def GeneraEvento(self, newreg):
        from contab.dbtables import DbRegCon
        r = DbRegCon()
        if r.Get(self.reg_id) and r.OneRow():
            r.GeneraEvento(self, newreg)
    
    def Validate(self):
        
        COLOR_ERROR = Env.Azienda.Colours.VALERR_BACKGROUND
        gvalid = True
        msg = None
        stl = wx.ICON_ERROR
        
        dr = self.controls['datreg'].GetValue()
        if not dr:
            #test data registrazione
            msg = "La data di registrazione è obbligatoria"
            gvalid = False
        
        if gvalid:
            #test data chiusura
            if self._progr_ccg_aggcon_date:
                if dr<=self._progr_ccg_aggcon_date:
                    msg = "La data di registrazione è antecendente l'ultima chiusura contabile"
                    gvalid = False
        
        if gvalid:
            #test esercizio
            ec = self.dbese.GetEsercizioInCorso()
            ie, fe = self.dbese.GetEsercizioDates()
            if dr<ie:
                msg = "La data di registrazione è antecedente l'esercizio in corso"
                gvalid = False
            else:
                e = ec#self.dbese.GetEsercizioDaData(dr)
                if self._cfg_esercizio == '1':
                    e -= 1
                    if not ie <= dr <= fe:
                        msg = "Le rettifiche all'esercizio precedente devono essere comprese nell'esercizio in corso"
                        gvalid = False
                if gvalid:
                    if dr.year>Env.Azienda.Login.dataElab.year:
                        m = "L'anno della data di registrazione eccede l'anno della data di lavoro.\nConfermi?"
                        if aw.awu.MsgDialog(self, m, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                            gvalid = False
                if gvalid:
                    e = self.dbese.GetEsercizioDaData(dr)
                    if self._cfg_esercizio == '1':
                        e -= 1
                    self.reg_esercizio = e
        
        if gvalid:
            #test data registrazione in confronto al giornale
            dg = self.dbprog.GetDataGiornale()
            dm = self.dbprom.GetDataMastri(self.reg_esercizio)
            msg = None
            if dg is not None and self.reg_datreg<dg:
                msg = "La data di registrazione è antecedente l'ultima stampa definitiva del giornale"
            elif dm is not None and self.reg_datreg<dm:
                msg = "La data di registrazione è antecedente l'ultima stampa definitiva dei mastri"
            if msg:
                gvalid = False
        
        if gvalid:
            #test data documento in confronto alla data registrazione
            if self._cfg_datdoc in ('0', '1'):
                msg = None
                dd = self.controls["datdoc"].GetValue()
                if dd is None:
                    msg = "La data documento è obbligatoria"
                elif dd > dr:
                    msg = "La data documento non può essere successiva a quella di registrazione"
                elif dd.year<dr.year:
                    msg = "La data documento si riferisce ad un altro anno rispetto alla data di registrazione.\nConfermi la sua esattezza?"
                    stl = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
                if msg:
                    gvalid = False
        
        if gvalid:
            #test validità recordset dare/avere
            td = ta = 0
            rs = self.regrsb
            msg = None
            for n in range(len(rs)):
                r = rs[n]
                if r[RSDET_IMPDARE] is None and r[RSDET_IMPAVERE] is None and n>0 and r[RSDET_TIPRIGA] != "O":
                    if rs[0][RSDET_IMPDARE] or rs[0][RSDET_IMPAVERE]:
                        msg = "Nessun importo specificato"
                elif r[RSDET_IMPDARE] is not None and r[RSDET_IMPDARE]<0:
                    msg = "Importo negativo in Dare"
                elif r[RSDET_IMPAVERE] is not None and r[RSDET_IMPAVERE]<0:
                    msg = "Importo negativo in Avere"
                elif float(r[RSDET_IMPDARE] or 0) and float(r[RSDET_IMPAVERE] or 0):
                    msg = "Importi errati"
                elif r[RSDET_PDCPA_ID] is None:
                    msg = "Sottoconto non specificato"
                if msg:
                    break
                td += r[RSDET_IMPDARE] or 0
                ta += r[RSDET_IMPAVERE] or 0
            if msg:
                msg += " alla riga %d" % (n+1)
            else:
                if abs(td-ta)>0.00000001:
                    msg = "Squadratura tra Dare e Avere"
            if msg:
                gvalid = False
        
        if gvalid and rs:
            #test validità segno contabile su riga partita
            if (self._cfg_pasegno or ' ') in 'DA':
                s = self._cfg_pasegno
                if s == "D" and rs[0][RSDET_IMPAVERE] or s == "A" and rs[0][RSDET_IMPDARE]:
                    msg =\
                        """La causale è impostata con segno %s sulla riga della partita,\n"""\
                        """mentre l'importo di %s è stato inserito dalla parte opposta.\n"""\
                        % (["DARE","AVERE"]["DA".index(s)], 
                           self.dbese.sepnvi(rs[0][RSDET_IMPDARE] or rs[0][RSDET_IMPAVERE]))
                    if self._cfg_camsegr1:
                        msg += """Confermi l'esattezza della registrazione?"""
                        stl = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
                        if MsgDialog(self, msg, style=stl) != wx.ID_YES:
                            gvalid = False
                            msg = "Verificare il segno contabile delle righe presenti"
                            stl = wx.ICON_ERROR
                    else:
                        msg += """Impossibile memorizzare la registrazione"""
                        gvalid = False
                        stl = wx.ICON_ERROR
        
        if gvalid:
            #test validità sui singoli controlli
            for name, ctr in self.controls.iteritems():
                if isinstance(ctr, wx.Window):
                    valid = ctr.Validate()
                    if not valid:
                        ctr.SetBackgroundColour( COLOR_ERROR )
                        msg =\
                            """Sono presenti valori non validi.  Correggere le parti """\
                            """evidenziate per continuare.\n"""\
                            """La registrazione non è stata salvata."""
                        gvalid = False
        
        if not gvalid and msg is not None:
            if MsgDialog(self, msg, style=stl) == wx.ID_YES:
                gvalid = True
        
        if gvalid:
            self.reg_datreg = self.controls["datreg"].GetValue()
            self.reg_datdoc = self.controls["datdoc"].GetValue()
            self.reg_numdoc = self.controls["numdoc"].GetValue()
        
        return gvalid
    
    def RegWriteHead(self):
        """
        Scrive la testata e i record di dettaglio della registrazione.
        """
        out = False
        par = [ self.reg_esercizio,\
                self.reg_cau_id,\
                self.reg_cau_tipo,\
                self.reg_datreg,\
                self.reg_datdoc,\
                self.reg_numdoc,\
                self.reg_regiva_id,\
                self.reg_numiva,\
                self.reg_modpag_id,\
                self.reg_nocalciva]
        headwritten = False
        bodywritten = False
        if self.newreg:
            #inserimento testata nuova registrazione
            cmd =\
"""INSERT INTO %s (esercizio, id_caus, tipreg, datreg, datdoc, numdoc, """\
"""id_regiva, numiva, id_modpag, nocalciva) """\
"""VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)"""\
% bt.TABNAME_CONTAB_H
            
        else:
            #modifica testata registrazione esistente
            cmd =\
"""UPDATE %s SET esercizio=%%s, id_caus=%%s, tipreg=%%s, datreg=%%s, """\
"""datdoc=%%s, numdoc=%%s, id_regiva=%%s, numiva=%%s, id_modpag=%%s, """\
"""nocalciva=%%s """\
"""WHERE id=%%s"""\
% bt.TABNAME_CONTAB_H
            par.append(self.reg_id)
        
        try:
            self.db_curs.execute(cmd, par)
            if self.newreg:
                self.db_curs.execute( "SELECT LAST_INSERT_ID();" )
                self.SetNewRegId( self.db_curs.fetchone()[0] )
            out = True
            
        except MySQLdb.Error, e:
            print e.args[0], e.args[1]
        
        return out

    def SetNewRegId(self, newid):
        self.reg_id = newid
        self.newreg = False

    def RegWriteBody(self, addRows=None):
        """
        Scrittura dettaglio registrazione su db.
        """
        out = False
        rows = []
        rsb = self.regrsb
        #rmax = 0
        #for n in range(len(rsb)):
            #rmax = max(rmax, rsb[n][RSDET_NUMRIGA])
        rmax = 0
        for n in range(len(rsb)):
            if rsb[n][RSDET_IMPDARE] > 0:
                imp = rsb[n][RSDET_IMPDARE]
                segno = "D"
            else:
                imp = rsb[n][RSDET_IMPAVERE]
                segno = "A"
            regid = self.reg_id
            numriga =  rsb[n][RSDET_NUMRIGA]
            tipriga =  rsb[n][RSDET_TIPRIGA]
            pdcpaid =  rsb[n][RSDET_PDCPA_ID]
            pdccpid =  rsb[n][RSDET_PDCPA_ID]
            note =     rsb[n][RSDET_NOTE]
            ivaman =   rsb[n][RSDET_RIGAPI]
            davscorp = rsb[n][RSDET_ALIQ_TOT]
            solocont = rsb[n][RSDET_SOLOCONT]
            #riga c/partita
            pdccpid = None
            if n == 0:
                #c/p della prima riga
                for r in rsb[1:]:
                    if r[RSDET_TIPRIGA] != "A":
                        pdccpid = r[RSDET_PDCPA_ID]
                        break
                aliqivaid = None
            else:
                #c/p delle righe oltre la prima
                if pdcpaid == rsb[0][RSDET_PDCPA_ID]:
                    #pdc=pdc prima riga (pag.imm?)
                    if n<(len(self.regrsb)-1):
                        #c/p = pdc della riga successiva
                        pdccpid = rsb[n+1][RSDET_PDCPA_ID]
                else:
                    #pdc della prima riga
                    pdccpid = rsb[0][RSDET_PDCPA_ID]
                aliqivaid = rsb[n][RSDET_ALIQ_ID]
            if pdccpid is None: 
                pdccpid = self.id_pdcpa
            rows.append((regid,     #id_reg
                         numriga,   #numriga
                         tipriga,   #tipriga
                         None,      #imponib
                         None,      #imposta
                         imp,       #importo
                         None,      #indeduc
                         ivaman,    #ivaman
                         segno,     #segno
                         aliqivaid, #id_aliqiva
                         davscorp,  #davscorp
                         solocont,  #solocont
                         pdcpaid,   #id_pdcpa
                         pdccpid,   #id_pdccp
                         None,      #id_pdciva
                         None,      #id_pdcind
                         note))     #note
            #rmax += 1
            rmax = max(rmax, rsb[n][RSDET_NUMRIGA])
        
        if addRows is not None:
            #se dalle sottoclassi arriva la chiamata con righe aggiuntive da
            #memorizzare, esse vengono aggiunte in coda alle righe contabili
            #presenti
            for n in range(len(addRows)):
                rmax += 1
                addRows[n][0] = self.reg_id
                addRows[n][1] = rmax
                rows.append(addRows[n])
        
        try:
            cmd =\
"""DELETE FROM %s WHERE id_reg=%%s""" % bt.TABNAME_CONTAB_B
            self.db_curs.execute(cmd, self.reg_id)
            cmd =\
"""INSERT INTO %s ("""\
"""id_reg, numriga, tipriga, imponib, imposta, importo, indeduc, ivaman, segno, """\
"""id_aliqiva, davscorp, solocont, id_pdcpa, id_pdccp, id_pdciva, id_pdcind, note) """\
"""VALUES (%s)""" % ( bt.TABNAME_CONTAB_B,\
                      (r"%s, " * 17)[:-2] )
            self.db_curs.executemany(cmd, rows)
            out = True
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        return out
    
    def RegReadBody(self, idreg):
        out = True
        rsb = []
        try:
            cmd = """
   SELECT row.numriga, 
          row.tipriga, 
          row.id_pdcpa, 
          pdc.codice, 
          pdc.descriz, 
          if(row.segno="D", row.importo, NULL), 
          if(row.segno="A", row.importo, NULL), 
          row.id_aliqiva,
          iva.codice,
          iva.descriz,
          row.solocont,
          row.note, 
          row.ivaman, 
          row.davscorp 
     FROM %s AS row 
     JOIN %s AS pdc ON row.id_pdcpa=pdc.id 
LEFT JOIN %s AS iva ON row.id_aliqiva=iva.id
 WHERE row.id_reg=%%s""" % (bt.TABNAME_CONTAB_B,
                            bt.TABNAME_PDC,
                            bt.TABNAME_ALIQIVA)
            self.db_curs.execute(cmd, idreg)
            rsb = self.db_curs.fetchall()
            if not rsb:
                MsgDialog(self,\
"""Attenzione!  La registrazione non contiene alcuna riga!""")
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            out = False
        else:
            del self.regrsb[:]
            for b in rsb:
                self.regrsb.append(list(b))
        self.totdare, self.totavere = self.GetTotaliDA()
        return out
    
    def RegReset(self):
        #reset valori testata
        self.reg_id = None
        self.reg_esercizio = None
        self.reg_cau_id = None
        self.reg_cau_tipo = None
        self.reg_datreg = None
        self.reg_datdoc = None
        self.reg_numdoc = None
        self.reg_regiva_id = None
        self.reg_numiva = None
        self.reg_st_regiva = None
        self.reg_st_giobol = None
        self.reg_modpag_id = None
        self.reg_regiva_cod = None
        self.reg_regiva_des = None
        #reset variabili registrazione
        self.id_pdcpa = None
        self.totdare = 0
        self.totavere = 0
        #reset recordet dettaglio
        del self.regrsb[:]

    def RegNew(self):
        if self.canins:
            self.newreg = True
            self.RegReset()
            self.DefaultValues()
            #self.UpdatePanelHead()
            self.SetRegStatus(STATUS_EDITING)
            self.controls["datreg"].SetFocus()

    def DefaultValues(self):
        
        if self.reg_datreg is None:
            self.reg_datreg = Esercizio.dataElab
        
        self.ReadProgr()
        
        self.reg_esercizio = Esercizio.year #automatizzare
        self.reg_cau_id = self.cauid
        self.reg_cau_tipo = self.cautipo
        
        if self._cfg_datdoc == '1':
            self.reg_datdoc = self.reg_datreg

    def RegDelete(self):
        out = False
        try:
            cmd =\
"""DELETE FROM %s WHERE id=%%s""" % bt.TABNAME_CONTAB_H
            self.db_curs.execute(cmd, self.reg_id)
            cmd =\
"""DELETE FROM %s WHERE id_reg=%%s""" % bt.TABNAME_CONTAB_B
            self.db_curs.execute(cmd, self.reg_id)
            self.controls['butattach'].SetKey(self.reg_id, delete=True)
            out = True
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        return out
    
    def UpdatePanelHead(self):
        """
        Aggiorna i controlli della testata.
        """
        reg_id = self.controls["reg_id"]
        datreg = self.controls["datreg"]
        datdoc = self.controls["datdoc"]
        numdoc = self.controls["numdoc"]
        
        if self.status == STATUS_SELCAUS:
            reg_id.SetValue(None)
            datreg.SetValue(None)
            datdoc.SetValue(None)
            numdoc.SetValue("")
        else:
            reg_id.SetValue(self.reg_id)
            datreg.SetValue(self.reg_datreg)
            datdoc.SetValue(self.reg_datdoc)
            numdoc.SetValue(self.reg_numdoc)

    def UpdatePanelBody(self):
        """
        Aggiorna i controlli del dettaglio in base al corrente recordset
        relativo al corpo registrazione C{self.regrsb}
        A seconda del tipo di registrazione (e quindi della sottoclasse)
        oltre a C{self.regrsb} potrebbero essercene altri.
        In questa classe il metodo non ha effetto.
        """
        self.UpdatePanelDav()
    
    def UpdatePanelDav(self, sizeDavCols=True):
        if self._grid_dav is not None:
            self._grid_dav.ResetView()
            if sizeDavCols:
                self._grid_dav.AutoSizeColumns()
        self.UpdateTotDav()
    
    def GetTotaliDA(self):
        totd = tota = 0
        if self.regrsb:
            d = a = 0
            for n, rig in enumerate(self.regrsb):
                d = rig[RSDET_IMPDARE]
                if d: totd += d
                a = rig[RSDET_IMPAVERE]
                if a: tota += a
        return totd, tota
    
    def UpdateTotDav(self):
        
        totd, tota = self.GetTotaliDA()
        
        self.controls["totdare"].SetValue(totd)
        self.controls["totavere"].SetValue(tota)
        q = self.controls["totquadr"]
        q.SetValue(abs(totd-tota))
        if abs(totd-tota)<0.000001:
            l = 'Quadratura:'
            c = wx.NullColor
            if totd:
                s = 'OK'
            else:
                s = ''
        else:
            l = 'SQUADRA:'
            c = 'red'
            if totd>tota:
                s = 'DARE'
            else:
                s = 'AVERE'
        q = self.controls['totquadrsgn']
        q.SetValue(s)
        q = self.FindWindowByName('totquadrlbl')
        q.SetLabel(l)
        q.GetParent().Layout()
        q.SetForegroundColour(c)
        self.totdare, self.totavere = totd, tota
        self.UpdateButtons()

    def EnableHeadControls(self, enable = True):
        """
        Abilita o meno i controlli della testata in base alla
        configurazione della causale.
        """
        enable = enable and self.status == STATUS_EDITING
        
        self.controls["datreg"].Enable(enable)
        
        self.controls["reg_id"].Enable(False)
        
        self.controls["datdoc"].Enable(enable and\
                                       self._cfg_datdoc in ('0', '1'))
        
        self.controls["numdoc"].Enable(enable and\
                                       self._cfg_numdoc in ('0', '1'))
        
        #self.controls["rivdes"].Enable(enable and\
            #self._cfg_regiva_id is not None)
        
        #self.controls["numiva"].Enable(enable and\
            #self._cfg_regiva_id is not None)
        
        #il reg.iva può essere variabile come da cfg.causale
        self.controls["id_regiva"].Enable(enable and self._cfg_tipo in 'IE' and\
                                          (self._cfg_regiva_dyn == 1 or self.reg_regiva_id is None))
        
        self.controls["numiva"].Enable(enable and\
                                       self._cfg_tipo in 'IE' and\
                                       bool(self._cfg_numiva))

    def EnableBodyControls(self, enable = True):
        enable = enable and self.status == STATUS_EDITING
        aw.awu.EnableControls(self.panbody, enable)


# ------------------------------------------------------------------------------


class _ContabMixin(object):
    
    dataentrypanel = None #viene inizializzato nelle classi derivate
    def __init__(self):
        object.__init__(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    def SetOneRegOnly(self, *args, **kwargs):
        #proxy x il pannello del dataentry
        self.dataentrypanel.SetOneRegOnly(*args, **kwargs)
    def OnClose(self, event):
        self.FixTimerProblem()
        event.Skip()
    
    def FixTimerProblem(self):
        #fix Timer su wx.2.8.11: se non lo stoppo, l'applicaizone va in crash :-(
        #TODO: verificare quando è stato risolto il problema nella libreria wx
        c = self.FindWindowByName('autonotes')
        if c:
            c.Stop()
    
    def CanClose(self):
        #richiamata da XFrame in fase di chiusura applicazione
        self.FixTimerProblem()
        return True


# ------------------------------------------------------------------------------


class ContabFrame(aw.Frame, _ContabMixin):
    
    def __init__(self, *args, **kwargs):
        aw.Frame.__init__(self, *args, **kwargs)
        _ContabMixin.__init__(self)


# ------------------------------------------------------------------------------


class ContabDialog(aw.Dialog, _ContabMixin):
    
    def __init__(self, *args, **kwargs):
        aw.Dialog.__init__(self, *args, **kwargs)
        _ContabMixin.__init__(self)
        self.Bind(wx.EVT_BUTTON, self.OnTestDelete)
    
    def EndModal(self, value):
        self.FixTimerProblem()
        aw.Dialog.EndModal(self, value)
    
    def OnTestDelete(self, event):
        if event.GetEventObject().GetName() == 'button_delete':
            if self.dataentrypanel.oneregonly_id:
                if self.IsModal():
                    self.EndModal(REG_DELETED)
                else:
                    self.Close()


# ------------------------------------------------------------------------------


class RegSearchGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent):
        dbglib.DbGridColoriAlternati.__init__(self, parent,
                                              size=parent.GetClientSizeTuple())
        cols = self.DefColumns()
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        self.SetData((), colmap)
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        self.SetFitColumn(self.GetColumn2Fit())
        self.AutoSizeColumns()
        
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def DefColumns(self):
        raise Exception, "Classe non istanziabile"
    
    def GetColumn2Fit(self):
        raise Exception, "Classe non istanziabile"


# ------------------------------------------------------------------------------


DATSEARCH1 = None
DATSEARCH2 = None

class RegSearchPanel(aw.Panel):
    
    wdrFiller = None
    GridClass = RegSearchGrid
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        self.wdrFiller(self)
        cn = self.FindWindowByName
        self.gridsrc = self.GridClass(cn('pangridsearch'))
        
        self.cauid = None
        self.caudes = None
        
        self.datmin = cn('srcdatmin')
        self.datmax = cn('srcdatmax')
        
        d2 = DATSEARCH2
        if not d2:
            d2 = Env.Azienda.Login.dataElab
        d1 = DATSEARCH1
        if not d1:
            d1 = Env.DateTime.Date(d2.year, d2.month, 1)
        
        self.datmin.SetValue(d1)
        self.datmax.SetValue(d2)
        
        for c in aw.awu.GetAllChildrens(self):
            if isinstance(c, (wx.TextCtrl, DateCtrl, LinkTable)):
                c.Bind(wx.EVT_SET_FOCUS, self.OnFocusGainedBySearchControls)
        self.gridsrc.Bind(wx.EVT_SET_FOCUS, self.OnFocusGainedByGrid)
        
        self.Bind(wx.EVT_BUTTON, self.OnSearch, cn('btnsearch'))
        
        wx.CallAfter(lambda: self.datmin.SetFocus())
    
    def OnFocusGainedBySearchControls(self, event):
        self.FindWindowByName('btnsearch').SetDefault()
        event.Skip()
    
    def OnFocusGainedByGrid(self, event):
        self.FindWindowByName('btnselect').SetDefault()
        event.Skip()
    
    def SetCausale( self, id, des):
        self.cauid = id
        self.caudes = des
    
    def OnSearch( self, event ):
        self.UpdateSearch()
        if self.gridsrc.GetTable().data:
            f = self.gridsrc
        else:
            f = self.FindWindowByName('srcdatmin')
        def SetFocus():
            f.SetFocus()
        wx.CallAfter(SetFocus)
        event.Skip()
    
    def UpdateSearch(self):
        dmin = self.datmin.GetValue()
        global DATSEARCH1
        DATSEARCH1 = dmin
        dmax = self.datmax.GetValue()
        global DATSEARCH2
        DATSEARCH2 = dmax
        filter = "id_caus=%d" % self.cauid
        par = []
        if dmin:
            filter += " and DATREG>=%s"
            par.append(dmin)
        if dmax:
            filter += " and DATREG<=%s"
            par.append(dmax)
        try:
            wx.BeginBusyCursor()
            try:
                cmd = \
"""SELECT reg.id, reg.datreg, pdc.descriz, reg.numdoc, reg.datdoc, """\
"""IF(row.segno="D", row.importo, 0), IF(row.segno="A", row.importo, 0) """\
"""FROM ((%s AS reg INNER JOIN %s AS cau ON reg.id_caus=cau.id) """\
"""JOIN contab_b AS row ON row.id_reg=reg.id) """\
"""JOIN pdc AS pdc ON row.id_pdcpa=pdc.id """\
"""WHERE row.numriga=1 and %s """\
"""ORDER BY reg.datreg, year(reg.datdoc), reg.numdoc;"""\
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




class RegSearchDialog(aw.Dialog):
    """
    Ricerca registrazioni.
    Dialog per la ricerca di registrazioni della causale selezionata.
    """
    
    panelClass = RegSearchPanel
    
    def __init__(self, parent, id = -1, title = "Ricerca registrazione",
                 pos=wx.DefaultPosition, size=wx.DefaultSize):
        
        aw.Dialog.__init__(self, parent, id, title, pos, size,
                           style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
        self.panel = self.panelClass(self)
        cn= self.FindWindowByName
        self.AddSizedPanel(self.panel)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnGridRowSelected, self.panel.gridsrc)
        self.Bind(wx.EVT_BUTTON, self.OnSelected, cn('btnselect'))
    
        self.panel.gridsrc.Bind(wx.EVT_KEY_DOWN, self.OnGridKeyDown)
        
        self.CenterOnScreen()
    
    def OnGridKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            row = self.panel.gridsrc.GetSelectedRows()[0]
            regid = self.panel.gridsrc.GetTable().data[row][0]
            self.EndModal(regid)
        event.Skip()
    
    def OnSelected(self, event):
        row = self.panel.gridsrc.GetSelectedRows()[0]
        regid = self.panel.gridsrc.GetTable().data[row][0]
        self.EndModal(regid)
    
    def OnGridRowSelected(self, event):
        regid = self.panel.gridsrc.GetTable().data[event.GetRow()][0]
        self.EndModal(regid)
        
    def SetCausale( self, id, des):
        self.panel.SetCausale(id, des)
        self.SetTitle("Ricerca registrazioni di tipo: %s" % self.panel.caudes)
    
    def UpdateSearch(self, *args, **kwargs):
        return self.panel.UpdateSearch(*args, **kwargs)
    
    def OnClose( self, event ):
        self.EndModal(-1)
        self.Destroy()
