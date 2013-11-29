#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dbtables.py
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

"""
Definizione classi specializzate x gestione database.
"""

from cfg.dbtables import ProgrEsercizio

import anag.dbtables as dba
adb = dba.adb

import Env
bt = Env.Azienda.BaseTab

import magazz
import contab
import contab.scad as scad

import mx

import copy


class _ScadWorker(adb.DbTable):
    """
    Aggancia la scadenza ad una partita esistente
    """
    def LinkTo(self, idpcf):
        self.id_pcf = idpcf


# ------------------------------------------------------------------------------


class _ExtendedNumDoc_mixin_:
    
    def get_regiva(self):
        raise Exception, 'Classe non istanziabile'
    
    def get_numdoc_print(self):
        numdoc = '%s' % self.numdoc
        if self.datdoc:
            if self.datdoc.year >= 2013:
                regiva = self.get_regiva()
                if regiva.numdocsez:
                    numdoc += ('/%s' % regiva.numdocsez)
                if regiva.numdocann:
                    numdoc += ('/%s' % self.datdoc.year)
        return numdoc


class DbRegCon(adb.DbTable,
               _ExtendedNumDoc_mixin_):
    """
    DbTable registrazioni contabili.
    Struttura:
    reg: registrazione
       +--> config: setup causale
       +--> regiva: registro iva
       +--> valuta: valuta
       +--> modpag: modalità di pagamento del documento
       |
       |---->> body: dettaglio righe contabili
       |          +--> pdcpa: sottoconto partita
       |          +--> pdccp: sottoconto c/partita
       |          +--> pdciva: sottoconto iva
       |          +--> pdcind: sottoconto iva indeducibile
       |
       |---->> scad: scadenze associate alla registrazione
                  +--> pcf: partita associata alla scadenza
    """
    
    def get_regiva(self):
        return self.regiva
    
    def __init__(self, writable=True):
        
        adb.DbTable.__init__(self,\
            bt.TABNAME_CONTAB_H, "reg", writable=writable)
        
        self.dbmpa = scad.Scadenze_Table()
        
        dbconfig = self.AddJoin(\
            bt.TABNAME_CFGCONTAB,"config",    idLeft="id_caus",\
            join=adb.JOIN_LEFT)
        
        dbcfgiva = dbconfig.AddJoin(\
            bt.TABNAME_REGIVA,   "cfgiva",    idLeft="id_regiva",\
            join=adb.JOIN_LEFT)
        
        dbregiva = self.AddJoin(\
            bt.TABNAME_REGIVA,   "regiva",    idLeft="id_regiva",\
            join=adb.JOIN_LEFT)
        
        dbvaluta = self.AddJoin(\
            bt.TABNAME_VALUTE,   "valuta",    idLeft="id_valuta",\
            join=adb.JOIN_LEFT)
        
        dbmovpag = self.AddJoin(\
            bt.TABNAME_MODPAG,   "modpag",    idLeft="id_modpag",\
            join=adb.JOIN_LEFT)
        
        # multijoined table body (contab_b)
        dbbody = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_B, "body",      idRight="id_reg",\
            writable=writable)
        
        dbpdcpa = dbbody.AddJoin(\
            bt.TABNAME_PDC,      "pdcpa",     idLeft="id_pdcpa",\
            join=adb.JOIN_LEFT)
        
        dbpdccp = dbbody.AddJoin(\
            bt.TABNAME_PDC,      "pdccp",     idLeft="id_pdccp",\
            join=adb.JOIN_LEFT)
        
        dbpdcpiva = dbbody.AddJoin(\
            bt.TABNAME_PDC,      "pdciva",    idLeft="id_pdciva",\
            join=adb.JOIN_LEFT)
        
        dbpdcpind = dbbody.AddJoin(\
            bt.TABNAME_PDC,      "pdcind",    idLeft="id_pdcind",\
            join=adb.JOIN_LEFT)
        
        dbpdciva = dbbody.AddJoin(\
            bt.TABNAME_ALIQIVA,  "iva",       idLeft="id_aliqiva",\
            join=adb.JOIN_LEFT)
        
        # multijoined table scad (contab_s)
        dbscad = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_S, "scad",      idRight="id_reg",\
            writable=writable, fields=contab.scafields,\
            dbTabClass=_ScadWorker)
        dbscad.AddOrder("scad.datscad")
        
        dbpcf = dbscad.AddJoin(\
            bt.TABNAME_PCF,      "pcf",       idLeft="id_pcf",\
            join=adb.JOIN_LEFT)
        
        self._info.oldpdc = None
        self._info.oldsca = ()
        self._info.id_effbap = None
        self._info.progr = adb.DbTable(bt.TABNAME_CFGPROGR, "progr",\
                                       writable=True)
        
        self.Get(-1)
    
    def SetupModPag(self, *args, **kwargs):
        self.dbmpa.SetupModPag(*args, **kwargs)
        for c in dir(self.dbmpa):
            if c.startswith('mp_'):
                setattr(self, c, getattr(self.dbmpa, c))
    
    def DeleteRow(self, *args, **kwargs):
        #previene l'aggiornamento delle tabelle collegate in caso di 
        #cancellazione di una riga (=registrazione) onde evitare di perdersi 
        #la configurazione della causale per i successivi aggiornamenti 
        #sulle partite
        self._info.updateIChildrens = False
        out = adb.DbTable.DeleteRow(self, *args, **kwargs)
        self._info.updateIChildrens = True
        return out
    
    def Retrieve(self, *args, **kwargs):
        out = adb.DbTable.Retrieve(self, *args, **kwargs)
        if out:
            def Find(mov):
                return mov.tipriga == "A" and mov.ivaman == 1
            #elimino eventuali righe automatiche cli/for-cassa x giroc. pag.imm.
            while self.body.Locate(Find):
                self.body.DeleteRow()
            self.body.MoveFirst()
        if not (kwargs.has_key("refresh") and kwargs["refresh"]):
            self.UpdatePcfStorni()
        return out
    
    def UpdatePcfStorni(self):
        self._info.oldsca = copy.deepcopy(self.scad._info.rs)
    
    def _SaveRecords(self, records, deletions):
        out = True
        cfg = self.config
        newreg = (self.id is None)
        if cfg.pcf == '1':# and cfg.pcfscon != '1':
            #storno partite
            out = self.PcfStorno()
        if out and self.modpag.id_pdcpi is not None:
            if not self.id in deletions:
                #righe di giroc. cli/for-cassa x pag.imm.
                self.TestPagImm()
        if out:
            #scrittura registrazione
            self.SetSilent(True) #previene il ricaricamento degli mchildrens
            out = adb.DbTable._SaveRecords(self, records, deletions)
            self.SetSilent(False)
        if out:
#            if self.id_regiva:
#                #aggiornamento ultimo numero di protocollo iva
#                progr = self._info.progr
#                progr.ClearFilters()
#                progr.AddFilter("progr.codice=%s",  "iva_ultins")
#                progr.AddFilter("progr.keydiff=%s", self.esercizio)
#                progr.AddFilter("progr.key_id=%s",  self.id_regiva)
#                if progr.Retrieve():
#                    if progr.IsEmpty():
#                        progr.CreateNewRow()
#                        progr.codice = "iva_lastins"
#                        progr.keydiff = self.esercizio
#                        progr.key_id = self.id_regiva
#                        progr.progrnum = 0
#                    if self.numdoc > progr.progrnum:
#                        progr.progrnum = self.numiva
#                        progr.Save()
#                del progr
            if cfg.pcf == '1':
                if self.modpag.id_pdcpi is None:
                    #aggiorno partite
                    out = self.PcfWrite()
                else:
                    #pag.imm. non scrivo partite
                    out = True
                if out:
                    #rimemorizzo le scadenze della regitrazione
                    #se sono state create nuove parite
                    out = self.scad.SaveAll()
        if out and cfg.id_tipevent is not None:
            self.GeneraEvento(None, newreg)
        return out
    
    def GeneraEvento(self, parent, newreg):
        from cfg.dbtables import EventiTable
        e = EventiTable()
        e.CreateNewRow()
        e.data_evento = Env.DateTime.now()
        e.usercode = Env.Azienda.Login.usercode
        e.username = Env.Azienda.Login.username
        e.id_tipevent = self.config.id_tipevent
        e.dettaglio = e.ParseContent(self.config.event_msg, self)
        e.tablename = bt.TABNAME_CONTAB_H
        e.tableid = self.id
        err = False
        if not e.Save():
            err = True
        if not err:
            if newreg:
                plusmsg = ""
            else:
                plusmsg = " (MODIFICATO)"
            if e.Notify(owner=parent, plusmsg=plusmsg):
                if not e.Save():
                    err = True
        if err:
            raise Exception, repr(e.GetError())
        return True
    
    def TestPagImm(self):
        mov = self.body
        if mov.RowsCount()<2:
            return
        mov.MoveFirst()
        pdcpaid = mov.id_pdcpa
        pdccpid = None
        if mov.segno == "D":
            totd = mov.importo
            tota = 0
        elif mov.segno == "A":
            totd = 0
            tota = mov.importo
        while mov.MoveNext():
            if mov.tipriga != "A":
                pdccpid = mov.id_pdcpa
            if mov.id_pdccp is None:
                mov.id_pdccp = pdccpid
        nriga = (mov.numriga or 0)+1
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
        mov.CreateNewRow()
        mov.numriga = nriga
        mov.tipriga = "A"
        mov.id_pdcpa = pdcpaid
        mov.id_pdccp = self.modpag.id_pdcpi
        if impd1:
            mov.importo = impd1
            mov.segno = "D"
        elif impa1:
            mov.importo = impa1
            mov.segno = "A"
        mov.ivaman = 1
        #riga cassa/banca
        mov.CreateNewRow()
        mov.numriga = nriga+1
        mov.tipriga = "A"
        mov.id_pdcpa = self.modpag.id_pdcpi
        mov.id_pdccp = pdcpaid
        if impd2:
            mov.importo = impd2
            mov.segno = "D"
        elif impa2:
            mov.importo = impa2
            mov.segno = "A"
        mov.ivaman = 1
    
    def Reset(self, *args, **kwargs):
        self._info.oldpdc = None
        self._info.id_effbap = None
        return adb.DbTable.Reset(self, *args, **kwargs)
    
    def CalcolaScadenze(self, datdoc, idmp, timp, tiva):
        newscad = self.dbmpa.CalcolaScadenze(datdoc, idmp, timp, tiva)
        dbsca = self.scad
        for s in dbsca:
            s.DeleteRow()
        dbsca._info.recordCount = 0
        dbsca._info.recordNumber = -1
        for sca in newscad:
#            dbsca.MoveNewRow()
            dbsca.CreateNewRow()
            dbsca.datscad = sca[0]
            dbsca.importo = sca[1]
            dbsca.f_riba = sca[2]
#            dbsca.AppendNewRow()
#            row = dbsca.RowsCount()-1
#            dbsca._info.rs[row][contab.RSSCA_ISRIBA] = sca[2]
    
    def PcfStorno(self):
        """
        Storno partite.
        """
        out = True
        pcf_ind = self.scad._GetFieldIndex("id_pcf")
        imp_ind = self.scad._GetFieldIndex("importo")
        cfg = self.config
        pcf = adb.DbTable(bt.TABNAME_PCF, "pcf")
        #storno partite
        #for scad in self.scad._info.oldsca:
        NDEC = bt.VALINT_DECIMALS
        for scad in self._info.oldsca:
            pcfid = scad[pcf_ind]
            if pcfid is not None and pcf.Get(pcfid) and pcf.OneRow():
                pcf.imptot = pcf.imptot or 0
                pcf.imppar = pcf.imppar or 0
                if   cfg.pcfimp == '1':
                    if   cfg.pcfsgn == '+':
                        pcf.imptot = round(pcf.imptot - scad[imp_ind], NDEC)
                    elif cfg.pcfsgn == '-':
                        pcf.imptot = round(pcf.imptot + scad[imp_ind], NDEC)
                elif cfg.pcfimp == '2':
                    if   cfg.pcfsgn == '+': 
                        pcf.imppar = round(pcf.imppar - scad[imp_ind], NDEC)
                    elif cfg.pcfsgn == '-': 
                        pcf.imppar = round(pcf.imppar + scad[imp_ind], NDEC)
                pcf.Save()
        del pcf
        return out
    
    def PcfWrite(self):
        out = True
        idpdc = self.body.GetFieldFromRow("id_pdcpa", 0)
        pcf = adb.DbTable(bt.TABNAME_PCF, "pcf")
        if idpdc is not None:
            cfg = self.config
            #aggiornamento partite
            for scad in self.scad:
                if not scad.importo:
                    #l'importo della scadenza è nullo, non aggiorno partita
                    continue
                if scad.id_pcf is not None:
                    do = pcf.Get(scad.id_pcf) and pcf.RowsCount() == 1
                    if not do:
                        scad.id_pcf = None
                if scad.id_pcf is None:
                    do = pcf.CreateNewRow()
                    if do:
                        pcf.id_pdc =    idpdc
                        pcf.id_caus =   self.id_caus
                        pcf.id_modpag = self.id_modpag
                        pcf.datdoc =    self.datdoc
                        pcf.numdoc =    self.numdoc
                        pcf.datscad =   scad.datscad
                        pcf.imptot =    0
                        pcf.imppar =    0
                if not do:
                    break
                pcf.datscad = scad.datscad
                pcf.note =    scad.note
                if cfg.pcfins == '1':
                    pcf.insoluto = 1
                if   cfg.pcfimp == '1':
                    if   cfg.pcfsgn == '+': pcf.imptot += scad.importo
                    elif cfg.pcfsgn == '-': pcf.imptot -= scad.importo
                elif cfg.pcfimp == '2':
                    if   cfg.pcfsgn == '+': pcf.imppar += scad.importo
                    elif cfg.pcfsgn == '-': pcf.imppar -= scad.importo
                pcf.riba = scad.f_riba
                if True:#pcf.riba:
                    pcf.id_effbap = self._info.id_effbap
                if not pcf.Save():
                    break
                scad.id_pcf = pcf.id
        #elimino le partite che dopo lo storno sono andate a zero
        pcf_ind = self.scad._GetFieldIndex("id_pcf")
        #oldpcfids = [int(os[pcf_ind])\
                     #for os in self.scad._info.oldsca\
                     #if os[pcf_ind] is not None]
        oldpcfids = [int(os[pcf_ind])\
                     for os in self._info.oldsca\
                     if os[pcf_ind] is not None]
        if oldpcfids:
            if len(oldpcfids) == 1:
                pcf.AddFilter("pcf.id=%s" % oldpcfids[0])
            else:
                pcf.AddFilter("pcf.id IN %s" % repr(tuple(oldpcfids)))
            pcf.AddFilter("pcf.imptot=0")
            pcf.AddFilter("pcf.imppar=0")
            if pcf.Retrieve():
                for p in pcf:
                    p.DeleteRow()
                pcf.Save()
        del pcf
        #self.scad.UpdatePcfStorni()
        self.UpdatePcfStorni()
        return out

    def GetSegnoCP(self):
        s = self.config.pasegno
        if   s == "D": out = "A"
        elif s == "A": out = "D"
        else:          out = " "
        return out
    

# ------------------------------------------------------------------------------


class _PdcMovimMixin(adb.DbTable):
    """
    DbTable di partenza per saldi e mastro.
    Struttura:
    pdc
      +--> tipana (pdctip) tipo anagrafico
      +--> bilmas mastro di bilancio
      +--> bilcon conto di bilancio
    *Must override*
    """
    def __init__(self, **kwargs):
        
        for name, val in (('writable',   False),\
                          ('getFilters', True )):
            if not kwargs.has_key(name):
                kwargs[name] = val
        
        adb.DbTable.__init__(\
            self, bt.TABNAME_PDC, "pdc", **kwargs)
        
        self.mov = None
        
        tipana = self.AddJoin(\
            bt.TABNAME_PDCTIP, "tipana", idLeft="id_tipo")
        
        bilmas = self.AddJoin(\
            bt.TABNAME_BILMAS, "bilmas")
        
        bilcon = self.AddJoin(\
            bt.TABNAME_BILCON, "bilcon")

    def _AddMovTables(self):
        
        reg = self.mov.AddJoin(\
            bt.TABNAME_CONTAB_H,  "reg", idLeft="id_reg", idRight="id")
        
        cau = reg.AddJoin(\
            bt.TABNAME_CFGCONTAB, "caus")
        
        mpa = reg.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag",\
            join=adb.JOIN_LEFT)
        
        riv = reg.AddJoin(\
            bt.TABNAME_REGIVA,    "regiva",\
            join=adb.JOIN_LEFT)
        
        pcp = self.mov.AddJoin(\
            bt.TABNAME_PDC,       "pdccp", idLeft="id_pdccp", idRight="id",\
            join=adb.JOIN_LEFT)
    
    def ClearMovFilters(self):
        self.mov.ClearFilters()        
    
    def AddMovFilter(self, expr, val=None):
        self.mov.AddFilter(expr, val)

    
# ------------------------------------------------------------------------------


class PdcSaldi(_PdcMovimMixin):
    """
    DbTable specializzato nella determinazione del saldo contabile di ogni
    sottoconto.  Eventuali selezioni vanno impostate su 'self.saldi'
    Struttura da '_PdcMovimMixin'
      +--> saldi - rende disponibili i campi 'dare' e 'avere'
             +--> per le tabelle collegate vedi _PdcMovimMixin._AddMovTables
    """
    def __init__(self):
        
        _PdcMovimMixin.__init__(self)
        
        del self.mov
        
        mov = self.AddJoin(\
            bt.TABNAME_CONTAB_B, "mov", idLeft="id", idRight="id_pdcpa",\
            join=adb.JOIN_LEFT, fields=None)
        
        self._AddMovTables()
        
        self.AddOrder("tipana.tipo")
        self.AddGroupOn("pdc.id")
        mov.Synthetize()
        for segno, nome in (("D", "dare"),\
                            ("A", "avere")):
            mov.AddTotalOf(\
                "IF(mov.segno='%s', mov.importo, 0)" % segno, nome)
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class PdcMastro(_PdcMovimMixin):
    """
    DbTable specializzato nella determinazione del mastro contabile di ogni
    sottoconto.  Eventuali selezioni vanno impostate su 'self.mastro', che è
    il DbTable con i movimenti del mastro stesso.
    Struttura da '_PdcMovimMixin'
      +--> mastro - elenco movimenti del sottoconto
             +--> per le tabelle collegate vedi _PdcMovimMixin._AddMovTables
    """
    def __init__(self):
        
        _PdcMovimMixin.__init__(self)
        self._righeiva = False
        
        self._tipirighe = 'SCA'
        if bt.TIPO_CONTAB == "S":
            self._tipirighe += "I"
        
        del self.mov
        
        saldini = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_B, "saldini", idLeft="id", idRight="id_pdcpa",\
            join=adb.JOIN_LEFT, fields=None)
        _pdc = saldini.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id_pdcpa', fields=None)
        _mas = _pdc.AddJoin(bt.TABNAME_BILMAS, 'bilmas', idLeft='id_bilmas', fields=None)
        _reg = saldini.AddJoin(bt.TABNAME_CONTAB_H, 'reg', idLeft="id_reg", idRight="id", fields=None)
        _cau = _reg.AddJoin(bt.TABNAME_CFGCONTAB, 'caus', idLeft='id_caus', fields=None)
        saldini.AddGroupOn("saldini.id_pdcpa")
        saldini.AddTotalOf("IF(saldini.segno='D',saldini.importo,0)", "dare")
        saldini.AddTotalOf("IF(saldini.segno='A',saldini.importo,0)", "avere")
        saldini.AddBaseFilter("saldini.tipriga IN (%s)" % ','.join(["'%s'" % tr for tr in self._tipirighe]))
        
        regini = saldini.AddJoin(\
            bt.TABNAME_CONTAB_H, "regini", idLeft="id_reg", idRight="id",\
            join=adb.JOIN_LEFT)
        
        mov = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_B, "mov", idLeft="id", idRight="id_pdcpa",\
            join=adb.JOIN_ALL)
        self.mov = mov
        
        self._AddMovTables()
        
        for segno, nome in (("D", "dare"),\
                            ("A", "avere")):
            mov.AddField(\
                "IF(mov.segno='%s', mov.importo, 0)" % segno, nome)
        
        self._datmin = None
        self._datmax = None
        
        self.SetMovBaseFilter()
        self.mov.AddOrder("reg.datreg")
        self.mov.AddOrder("(reg.id_regiva IS NULL)")
        self.mov.AddOrder("regiva.codice")
        self.mov.AddOrder("reg.numiva")
        self.mov.AddOrder("reg.id")
        self.mov.AddOrder("mov.numriga")
        
        self.SetDateStart(mx.DateTime.Date(1970,6,20)) #todo
        
        self._info.intestapag = True #per stampa mastrino
        
        self.Get(-1)
    
    def SetRigheIva(self, ri):
        self._righeiva = ri
        self.SetMovBaseFilter()
    
    def SetMovBaseFilter(self):
        _tipirighe = self._tipirighe
        if self._righeiva:
            _tipirighe += "O"
        f = "mov.tipriga IN (%s)" % ','.join(["'%s'" % tr for tr in _tipirighe])
        if self._righeiva:
            f += ' OR reg.tipreg="E" AND mov.tipriga="I"'
        else:
            f += ' AND reg.tipreg != "E"'
        self.mov.ClearBaseFilters()
        self.mov.AddBaseFilter(f)
    
    def SetDateStart(self, data, esercizio=None):
        self.mov.ClearFilters()
        self.saldini.ClearFilters()
        if data:
            self.mov.AddFilter("reg.datreg>=%s", data)
            self.saldini.AddFilter("regini.datreg<%s", data)
            if esercizio is not None:
                pe = ProgrEsercizio()
                ec = pe.GetEsercizioInCorso()
                dses = pe.GetEsercizioDates(esercizio)[0]
                if esercizio <= ec:
                    dsec = dses
                elif esercizio > ec:
                    dsec = pe.GetEsercizioDates(ec)[0]
                if dsec:
                    self.saldini.AddFilter('(bilmas.tipo="P" AND regini.datreg>=%s) OR (bilmas.tipo<>"P" AND regini.datreg>=%s)', dsec, dses)
        else:
            self.saldini.AddFilter("0")
        self._datmin = data
    
    def SetDateEnd(self, data):
        if data:
            self.mov.AddFilter("reg.datreg<=%s", data)
        self._datmax = data
    
    def SetEsercizio(self, e=None):
        if e is not None:
            self.mov.AddFilter("reg.esercizio=%s", e)
            #self.saldini.AddFilter("regini.esercizio=%s", e) #todo: serve questo test?
    
    def GetMastro(self):
        return self.mov
    
    def GetProgrIni(self):
        return (self.saldini.total_dare or 0),\
               (self.saldini.total_avere or 0)
    
    def GetProgrMov(self):
        """
        Ritorna i totali dare/avere della movimentazione presente sul
        sottoconto.
        """
        return self.mov.GetTotalOf(('dare', 'avere'))

    def GetProgrTot(self):
        id, ia = self.GetProgrIni()
        md, ma = self.GetProgrMov()
        return (id+md), (ia+ma)

    def GetLastRegDate(self):
        """
        Ritorna la data dell'ultima registrazione presente nel mastro
        """
        m = self.mov
        m.MoveLast()
        return m.reg.datreg
    
    def GetSaldo(self, darav):
        """
        Ritorna il saldo come differenza tra dare e avere.
        """
        dare, avere = darav
        return dare-avere
    
    def calldebug(self):
        return 0


# ------------------------------------------------------------------------------


class MastriSottoconto(PdcMastro):
    
    def __init__(self, *args, **kwargs):
        PdcMastro.__init__(self, *args, **kwargs)
        tmov = self.AddJoin(bt.TABNAME_CONTAB_B, 'tmov', 
                            idLeft='id', idRight='id_pdcpa')
        treg = tmov.AddJoin(bt.TABNAME_CONTAB_H, 'treg',
                            idLeft='id_reg', idRight='id')
        self.AddGroupOn('pdc.id')
        self.AddCountOf('tmov.id')
        self.ClearOrders()
        self.AddOrder('pdc.codice')
    
    def ClearMovFilters(self):
        PdcMastro.ClearMovFilters(self)
        self.tmov.ClearFilters()        
    
    def AddMovFilter(self, expr, val=None):
        PdcMastro.AddMovFilter(self, expr, val)
        self.tmov.AddFilter(expr, val)
    
    def SetMovBaseFilter(self):
        PdcMastro.SetMovBaseFilter(self)
        try:
            getattr(self, 'tmov')
        except AttributeError:
            return
        _tipirighe = "SCA"
        if bt.TIPO_CONTAB == "S":
            _tipirighe += "I"
        if self._righeiva:
            _tipirighe += "O"
        self.tmov.ClearBaseFilters()
        self.tmov.AddBaseFilter("tmov.tipriga IN (%s)" % ','.join(["'%s'" % tr for tr in self._tipirighe]))
    
    def SetDateStart(self, data, esercizio=None):
        PdcMastro.SetDateStart(self, data, esercizio=esercizio)
        try:
            getattr(self, 'tmov')
        except AttributeError:
            return
        self.tmov.ClearFilters()
        if data:
            self.tmov.AddFilter("treg.datreg>=%s", data)
    
    def SetDateEnd(self, data):
        PdcMastro.SetDateEnd(self, data)
        try:
            getattr(self, 'tmov')
        except AttributeError:
            return
        if data:
            self.tmov.AddFilter("treg.datreg<=%s", data)
    
    def SetEsercizio(self, e=None):
        PdcMastro.SetEsercizio(self, e)
        if e is not None:
            try:
                getattr(self, 'tmov')
            except AttributeError:
                return
            self.tmov.AddFilter("treg.esercizio=%s", e)


# ------------------------------------------------------------------------------


class PdcContabView(adb.DbTable):
    """
    Interrogazioni contabili sul sottoconto.
    Provvede la gestione del saldo iniziale ad una certa data e l'insieme
    dei movimenti contabili da tale data ad altra data.
    """
    def __init__(self):
        
        adb.DbTable.__init__(self,\
                             bt.TABNAME_PDC, 'pdc',\
                             writable=False, fields="id,codice,descriz")
        
        self.dbsal = PdcSaldi()
        self.dbmas = PdcMastro()
        
        self.totinid = 0
        self.totinia = 0
        self.totmovd = 0
        self.totmova = 0
        self.totsald = 0
        self.totsala = 0
        
        self.datmin = None
        self.datmax = None
    
    def ClearMovFilters(self):
        for tab in (self.dbsal, self.dbmas):
            tab.ClearMovFilters()
        self.datmin = None
        self.datmax = None
    
    def AddMovFilter(self, expr, val=None):
        for tab in (self.dbsal, self.dbmas):
            tab.mov.AddFilter(expr, val)

    def Get(self, recid):
        
        out = adb.DbTable.Get(self, recid)
        
        if self.datmin is None:
            self.dbsal.mov.StoreFilters()
            self.dbsal.mov.AddFilter("YEAR(reg.datreg)<0")
        
        self.dbsal.Get(recid)
        self.dbmas.Get(recid)
        
        if self.datmin is None:
            self.dbsal.mov.ResumeFilters()
        
        self.totinid = self.dbsal.mov.total_dare  or 0
        self.totinia = self.dbsal.mov.total_avere or 0
        
        self.totmovd,\
        self.totmova = self.dbmas.GetProgrMov()
        
        self.totsald = self.totinid + self.totmovd
        self.totsala = self.totinia + self.totmova
        
        self.dbmas.mov.MoveLast()
        self.datmax = self.dbmas.mov.reg.datreg
        
        return out
    
    def GetSaldoIni(self):
        val = abs(self.totinid-self.totinia)
        if self.totinid >= self.totinia:
            sgn = "D"
        else:
            sgn = "A"
        return val, sgn, self.datmin
    
    def GetSaldoMov(self):
        val = abs(self.totmovd-self.totmova)
        if self.totmovd >= self.totmova:
            sgn = "D"
        else:
            sgn = "A"
        return val, sgn, self.datmax
    
    def GetSaldoFin(self):
        val = abs(self.totsald-self.totsala)
        if self.totsald >= self.totsala:
            sgn = "D"
        else:
            sgn = "A"
        return val, sgn, self.datmax


# ------------------------------------------------------------------------------


class PdcSintesiPartite(adb.DbTable):
    """
    Determina la situazione sintetica dei debiti/crediti relativi ad uno o
    più clienti/fornitori.
    Vengono totalizzate le partite a seconda del tipo di mod.pag. associata
    alla partita (contanti/bonifici/riba) e se le partite sono flaggate come
    insolute o meno:
    total_saldo
    total_bonif e total_ins_bonif
    total_cont  e total_ins_cont
    total_riba  e total_ins_riba
    
    Se la classe è istanziata passando un valore data alla kw 'today', tali
    variabili vengono ulteriormante suddivise:
    total_saldo_scaduto
    total_saldo_ascadere
    total_bonif_scaduto
    total_bonif_ascadere
    total_bonif_ins_scaduto
    total_cont_scaduto
    total_cont_ascadere
    total_cont_ins_scaduto
    total_riba_scaduto
    total_riba_ascadere
    total_riba_ins_scaduto
    
    Eventuali selezioni sulle partite vanno impostate tramite i metodi
    ClearPcfFilters e AddPcfFilter; i riferimenti a colonne della tabella
    partite devono essere fatti a 'sintesi': ad esempio: sintesi.datdoc>=...
    
    Struttura:
    pdc
      +--> tipana (pdctip) tipo anagrafico
      +--> bilmas mastro di bilancio
      +--> bilcon conto di bilancio
      +--> sintesi (pcf) x i totali
    """
    def __init__(self, **kwargs):
        
        for name, val in (('writable',   False),\
                          ('getFilters', True )):
            if not kwargs.has_key(name):
                kwargs[name] = val
        
        todaystr = None
        rbdatstr = None
        if kwargs.has_key('today'):
            today = kwargs['today']
            kwargs.pop('today')
            todaystr = today.Format('%Y-%m-%d')
            if kwargs.has_key('giorni_rb'):
                maxrbdate = today - kwargs['giorni_rb']
                kwargs.pop('giorni_rb')
                rbdatstr = maxrbdate.Format('%Y-%m-%d')
        
        adb.DbTable.__init__(\
            self,bt.TABNAME_PDC,'pdc', **kwargs)
        
        #anagcli = self.AddJoin(\
            #bt.TABNAME_CLIENTI, 'anagcli', idLeft='id', idRight='id', 
            #join=adb.JOIN_LEFT)
        
        #age = anagcli.AddJoin(\
            #bt.TABNAME_AGENTI,  'agente',
            #join=adb.JOIN_LEFT)
        
        #zona = anagcli.AddJoin(\
            #bt.TABNAME_ZONE,    'zona',
            #join=adb.JOIN_LEFT)
        
        #anagfor = self.AddJoin(\
            #bt.TABNAME_FORNIT,  'anagfor', idLeft='id', idRight='id', 
            #join=adb.JOIN_LEFT)
        
        tipana = self.AddJoin(\
            bt.TABNAME_PDCTIP, "tipana", idLeft="id_tipo")
        
        bilmas = self.AddJoin(\
            bt.TABNAME_BILMAS, "bilmas")
        
        bilcon = self.AddJoin(\
            bt.TABNAME_BILCON, "bilcon")
        
        sintesi = self.AddJoin(\
            bt.TABNAME_PCF, "sintesi", idLeft="id", idRight="id_pdc",\
            join=adb.JOIN_LEFT, fields=None)
        
        self._AddPcfJoins(sintesi)
        
        #gruppo finto: volendo raggruppare x agente, usare questo gruppo
        #è possibile ricorrere a ClearGroups per poi riscriverli, ma eventuali
        #dbgrid che sfruttino questa dbtables avrebbero problemi a puntare
        #correttamente le colonne; agendo su un gruppo (vero o finto che sia)
        #sempre presente, non si manifesta questo problema.
        #Per modificare l'espressione del gruppo, agire su 
        #self._info.group.groups[0][0] e mettere una costante (ad esempio '1')
        #nel caso non si voglia raggruppare
        self.AddGroupOn("1.0")
        self.AddGroupOn("pdc.id")
        self.AddOrder("tipana.tipo")
        sintesi.Synthetize()
        
        for tipname, cond, saldo in (\
            #alias    filtro                         totalizzatore
            ("saldo", "1",                           "sintesi.imptot-sintesi.imppar"),\
            ("cont",  "riba<>1 AND (modpag.tipo='C' OR modpag.id IS NULL)", 
                                                     "sintesi.imptot-sintesi.imppar"),\
            ("bonif", "riba<>1 AND modpag.tipo='B'", "sintesi.imptot-sintesi.imppar"),\
            ("riba",  "riba=1",                      "sintesi.imptot-sintesi.imppar")):
                     
            #for insname, ins in (("","(sintesi.insoluto IS NULL or sintesi.insoluto=0)"),\
            for insname, ins in (("",   "1"),\
                                 ("ins","sintesi.insoluto=1")):
                
                name = tipname
                if insname:
                    name += "_%s" % insname
                expr =\
                     """IF(%s AND %s, %s, 0)"""\
                     % (cond, ins, saldo)
                
                sintesi.AddTotalOf(expr, name)
                
                expr = "(%s)*IF(tipana.tipo='C',1,-1)" % expr
                sintesi.AddTotalOf(expr, 'cf_%s' % name)
                
                if todaystr is not None:
                    for opname, op in (("scaduto",  "<="),\
                                       ("ascadere", ">" )):
                        
                        name = tipname
                        if insname:
                            name += "_%s" % insname
                        name += "_%s" % opname
                        expr =\
                             """IF(sintesi.datscad%s'%s' """\
                             """   AND %s AND %s, %s, 0)"""\
                             % (op, todaystr, cond, ins, saldo)
                        
                        sintesi.AddTotalOf(expr, name)
                        
                        expr = "(%s)*IF(tipana.tipo='C',1,-1)" % expr
                        sintesi.AddTotalOf(expr, 'cf_%s' % name)
                        
                        if tipname == "riba" and opname == 'scaduto'\
                           and not insname and rbdatstr is not None:
                            
                            name = tipname
                            expr =\
                                 """IF(sintesi.datscad>='%s'"""\
                                 """   AND sintesi.datscad<='%s'"""\
                                 """   AND %s AND %s, %s, 0)"""\
                                 % (rbdatstr, todaystr, cond, ins, saldo)
                            
                            sintesi.AddTotalOf(expr, "riba_incerte")
                            
                            expr = "(%s)*IF(tipana.tipo='C',1,-1)" % expr
                            sintesi.AddTotalOf(expr, 'cf_%s' % name)
                    
                    for expr, name in (("""
                    IF(sintesi.insoluto=1 AND sintesi.imptot=sintesi.imppar,
                    sintesi.imptot,0)""", 'insoluti_passati'),
                                       ("""
                    IF(sintesi.insoluto=1 AND sintesi.imptot<>sintesi.imppar,
                    sintesi.imptot-sintesi.imppar,0)""", 'insoluti_attivi')):
                        sintesi.AddTotalOf(expr, name)
                        expr = "(%s)*IF(tipana.tipo='C',1,-1)" % expr
                        sintesi.AddTotalOf(expr, 'cf_%s' % name)
        
        self.Get(-1)
    
    def _AddPcfJoins(self, pcf):
        
        modpag = pcf.AddJoin(\
            bt.TABNAME_MODPAG,   "modpag", idLeft="id_modpag", idRight="id", join = adb.JOIN_LEFT)
        
        cau = pcf.AddJoin(\
            bt.TABNAME_CFGCONTAB,"caus",   idLeft="id_caus",   idRight="id", join = adb.JOIN_LEFT)
        
        #riv = cau.AddJoin(\
            #bt.TABNAME_REGIVA,   "regiva", idLeft="id_regiva", idRight="id", join = adb.JOIN_LEFT)
    
    def ClearPcfFilters(self):
        self.sintesi.ClearFilters()        
    
    def AddPcfFilter(self, expr, *values):
        self.sintesi.AddFilter(expr, *values)


# ------------------------------------------------------------------------------


class PdcScadenzario(PdcSintesiPartite):
    """
    Determina il mastro partite del sottoconto.
    
    N.B.
    Vedi _PartiteMixin per le funzionalità di filtro sulle partite.
    """
    def __init__(self, **kwargs):
        
        PdcSintesiPartite.__init__(self, **kwargs)
        
        mastro = self.AddMultiJoin(\
            bt.TABNAME_PCF, "mastro", idLeft="id", idRight="id_pdc",\
            join=adb.JOIN_ALL)
        mastro.AddOrder("mastro.datscad")
        mastro.AddOrder("mastro.datdoc")
        mastro.AddOrder("mastro.numdoc")
        mastro.AddField("mastro.imptot-mastro.imppar", "saldo")
        self._AddPcfJoins(mastro)
        
        if kwargs.has_key('today'):
            today = kwargs['today']
        else:
            today = Env.DateTime.now()
        todaystr = today.Format('%Y-%m-%d')
        mastro.AddField(\
            """IF(mastro.imptot=mastro.imppar, '',"""\
            """ IF(mastro.datscad='%s', 'Scade oggi',"""\
            """  IF(mastro.datscad<'%s', 'Scaduta', '')))"""\
            % ((todaystr,)*2),\
            "warning")
        mastro._info.today = today
        
        #mastro.AddField("(mastro.imptot)*IF(tipana.tipo='C',1,-1)", 'cf_imptot')
        #mastro.AddField("(mastro.imppar)*IF(tipana.tipo='C',1,-1)", 'cf_imppar')
        
        self.Get(-1)
    
    def ClearPcfFilters(self, maxincpag=None):
        PdcSintesiPartite.ClearPcfFilters(self)
        self.mastro.ClearFilters()
        if maxincpag is not None:
            cmd = """
            SELECT pdc.id, pdc.codice, pdc.descriz, MAX(IF((cau.pcf=1 AND cau.pcfimp=2 AND cau.pcfsgn="+"),reg.datreg,NULL)) as 'lastpag'
            FROM pdc
            JOIN pdctip tipana ON tipana.id=pdc.id_tipo
            LEFT JOIN contab_b mov ON mov.id_pdcpa=pdc.id
            LEFT JOIN contab_h reg ON reg.id=mov.id_reg
            LEFT JOIN cfgcontab cau ON cau.id=reg.id_caus
            WHERE tipana.tipo IN ("C", "F")
            GROUP BY pdc.codice, pdc.descriz
            HAVING lastpag IS NULL OR lastpag<"%s"
            """ % str(maxincpag)
            db = adb.db.__database__
            db.Retrieve(cmd)
            rs = db.rs
            anags = [str(r[0]) for r in rs]
            self.sintesi.AddFilter('pdc.id IN (%s)' % ','.join(anags))
    
    def AddPcfFilter(self, expr, val=None):
        PdcSintesiPartite.AddPcfFilter(self, expr, val)
        expr = expr.replace('sintesi', 'mastro')
        self.mastro.AddFilter(expr, val)
    
    def GetPartite(self):
        return self.mastro


# ------------------------------------------------------------------------------


BILORD_COD = 0
BILORD_DES = 1
BILORD_BIL = 2

class SaldiBilancio(adb.DbTable):
    
    def __init__(self, *args, **kwargs):
        
        #for par, val in (('writable', False),\
                         #('fields',   None )):
            #if not kwargs.has_key(par):
                #kwargs[par] = val
        
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_B, "saldi", fields=None)
        
        pdc = self.AddJoin(\
            bt.TABNAME_PDC,       "pdc",    idLeft="id_pdcpa", idRight="id")
        
        bilmas = pdc.AddJoin(self.GetMastroTabName(), "bilmas")
        
        bilcon = pdc.AddJoin(self.GetContoTabName(),  "bilcon")
        
        from cfg.dbtables import BilancioCeeTable
        bilcee = pdc.AddJoin(self.GetBilCeeName(), 'bilcee', join=adb.JOIN_LEFT,
                             dbTabClass=BilancioCeeTable)
        
        tipana = pdc.AddJoin(\
            bt.TABNAME_PDCTIP,    "tipana", idLeft="id_tipo",  idRight="id")
        
        reg = self.AddJoin(\
            bt.TABNAME_CONTAB_H,  "reg",    idLeft="id_reg",   idRight="id")
        
        cau = reg.AddJoin(\
            bt.TABNAME_CFGCONTAB, "cau",    idLeft="id_caus",  idRight="id")
        
        riv = cau.AddJoin(\
            bt.TABNAME_REGIVA,    "regiva",\
            join=adb.JOIN_LEFT)
        
        self.SetVar('ordin', None)
        
        self._SetGroups()
        self.AddTotalOf("IF(saldi.segno='D', saldi.importo, 0)", "dare")
        self.AddTotalOf("IF(saldi.segno='A', saldi.importo, 0)", "avere")
        
        _tipirighe = "SCA"
        if bt.TIPO_CONTAB == "S":
            _tipirighe += "I"
        self.AddBaseFilter("saldi.tipriga IN (%s) AND reg.tipreg<>'E'" % ','.join(["'%s'" % tr for tr in _tipirighe]))
        
        self._info.dbcee = BilancioCeeTable()
    
    def GetMastroTabName(self):
        return bt.TABNAME_BILMAS
    
    def GetContoTabName(self):
        return bt.TABNAME_BILCON
    
    def GetBilCeeName(self):
        return 'x4.bilcee'
    
    def _SetGroups(self):
        raise Exception, """Classe non direttamente istanziabile"""

    def SetOrdinamento(self, ordin=None):
        
        assert ordin in (BILORD_COD, BILORD_DES, BILORD_BIL),\
               """Tipo di ordinamento errato"""
        
        self.ClearOrders()
        
        if   ordin == BILORD_COD:
            self.AddOrder("pdc.codice")
            
        elif ordin == BILORD_DES:
            self.AddOrder("tipana.codice")
            self.AddOrder("pdc.descriz")
            
        elif ordin == BILORD_BIL:
            self.AddOrder("IF(bilmas.tipo='P',0,IF(bilmas.tipo='E',1,2))")
            self.AddOrder("bilmas.codice")
            self.AddOrder("bilcon.codice")
            self.AddOrder("pdc.descriz")
            self.AddOrder("pdc.codice")
        
        self.SetVar('ordin', ordin)


# ------------------------------------------------------------------------------


class Bilancio(SaldiBilancio):
    
    def _SetGroups(self):
        self.AddGroupOn("""IF(bilmas.tipo='P', 0,"""\
                        """IF(bilmas.tipo='E', 1,"""\
                        """IF(bilmas.tipo='O', 2, 3)))""",         'tipobil')
        self.AddGroupOn("""bilmas.codice""",                       'mastro')
        self.AddGroupOn("""bilcon.codice""",                       'conto')
        self.AddGroupOn("""CONCAT(IF(tipana.tipo IN ('C','F'),"""\
                        """pdc.descriz,pdc.codice), pdc.id)""",    'sottoconto')


# ------------------------------------------------------------------------------


class BilancioRicl(Bilancio):
    
    def GetMastroTabName(self):
        return bt.TABNAME_BRIMAS
    
    def GetContoTabName(self):
        return bt.TABNAME_BRICON
    

# ------------------------------------------------------------------------------


class BilancioCee(SaldiBilancio):
    
    def _SetGroups(self):
        self.AddGroupOn("""IF(bilcee.sezione IN ('1','2'), 1, """
                        """IF(bilcee.sezione IN ('4','5','6','7'), 3, """
                        """2))""", 'tipobil')
        self.AddGroupOn('bilcee.sezione',   'sezione')
        self.AddGroupOn('bilcee.voce',      'voce')
        self.AddGroupOn('bilcee.capitolo',  'capitolo')
        self.AddGroupOn('bilcee.dettaglio', 'dettaglio')
        self.AddGroupOn('bilcee.subdett',   'subdett')
        self.AddGroupOn('pdc.descriz',      'sottoconto')
    
    def SetOrdinamento(self, ordin=None):
        
        assert ordin in (BILORD_COD, BILORD_DES, BILORD_BIL),\
               """Tipo di ordinamento errato"""
        
        self.ClearOrders()
        self.AddOrder("bilcee.sezione")
        self.AddOrder("bilcee.voce")
        self.AddOrder("bilcee.capitolo")
        self.AddOrder("bilcee.dettaglio")
        self.AddOrder("bilcee.subdett")
        
        if   ordin == BILORD_COD:
            self.AddOrder("pdc.codice")
            
        elif ordin == BILORD_DES:
            self.AddOrder("tipana.codice")
            self.AddOrder("pdc.descriz")
            
        elif ordin == BILORD_BIL:
            self.AddOrder("pdc.descriz")
        
        self.SetVar('ordin', ordin)


# ------------------------------------------------------------------------------


class PcfMixin(adb.DbTable):
    """
    pcf
      +-> pdc
      +-> tipana (pdctip)
      +-> modpag (modpag)
      +-> caus   (cfgcontab)
             +-> regiva
    """
    
    def _AddPcfJoins(self, pcf=None):
        
        if pcf is None:
            pcf = self
        
        pdc = pcf.AddJoin(\
            bt.TABNAME_PDC,      "pdc",    idLeft="id_pdc",    idRight="id")
        
        tipana = pdc.AddJoin(\
            bt.TABNAME_PDCTIP,   "tipana", idLeft="id_tipo",   idRight="id")
        
        modpag = pcf.AddJoin(\
            bt.TABNAME_MODPAG,   "modpag", idLeft="id_modpag", idRight="id",\
            join=adb.JOIN_LEFT)
        
        cau = pcf.AddJoin(\
            bt.TABNAME_CFGCONTAB,"caus",   idLeft="id_caus",   idRight="id",\
            join=adb.JOIN_LEFT)
        
        #riv = cau.AddJoin(\
            #bt.TABNAME_REGIVA,   "regiva", idLeft="id_regiva", idRight="id",\
            #join=adb.JOIN_LEFT)
    


# ------------------------------------------------------------------------------


class PdcScadenzarioGlobale(PcfMixin):
    
    def __init__(self, *args, **kwargs):
        
        for name, val in (('writable',   False),\
                          ('getFilters', True ),\
                          ('fields',     None )):
            if not kwargs.has_key(name):
                kwargs[name] = val
        
        adb.DbTable.__init__(\
            self, bt.TABNAME_PCF, "sintesi", **kwargs)
        self.AddField("sintesi.imptot-sintesi.imppar", "saldo")
        
        self._AddPcfJoins(self)
        
        pcf = self.AddMultiJoin(\
            bt.TABNAME_PCF, "mastro", idLeft="datscad", idRight="datscad")
        pcf.AddField("mastro.imptot-mastro.imppar", "saldo")
        
        pcf.AddOrder("datdoc")
        pcf.AddOrder("numdoc")
        self._AddPcfJoins(pcf)
        
        self.AddOrder("sintesi.datscad")
        self.AddGroupOn("sintesi.datscad")
        
        self.AddFilter("sintesi.imptot<>sintesi.imppar")
        
        self.AddTotalOf("IF(tipana.tipo='C',1,-1)*sintesi.imptot",\
                        'imptot')
        self.AddTotalOf("IF(tipana.tipo='C',1,-1)*sintesi.imppar",\
                        'imppar')
        self.AddTotalOf("""IF(tipana.tipo='C',1,-1)*"""\
                        """IF(modpag.tipo='R',sintesi.imptot,"""\
                        """sintesi.imptot-sintesi.imppar)""",\
                        'saldo')
        
        self.Get(-1)
    
    def ClearPcfFilters(self):
        self.ClearFilters()
        self.mastro.ClearFilters()        
    
    def AddPcfFilter(self, expr, val=None):
        self.AddFilter(expr, val)
        expr = expr.replace('sintesi', 'mastro')
        self.mastro.AddFilter(expr, val)
    
    def GetPartite(self):
        return self.mastro


# ------------------------------------------------------------------------------


class Pcf(PcfMixin):
    """
    Partite clienti/fornitori.
    pcf
      +=>> rif (contab_s)
              +-> reg (contab_h)
                    +-> cau (cfgcontab)
    """
    def __init__(self, *args, **kwargs):
        
        adb.DbTable.__init__(\
            self, bt.TABNAME_PCF, "pcf", **kwargs)
        self.AddField("pcf.imptot-pcf.imppar", "saldo")
        
        self._AddPcfJoins()
        
        rif = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_S,  "rif", idLeft="id", idRight="id_pcf",\
            join=adb.JOIN_LEFT, writable=False)
        reg = rif.AddJoin(\
            bt.TABNAME_CONTAB_H,  "reg", idLeft="id_reg", idRight="id",\
            join=adb.JOIN_LEFT)
        cau = reg.AddJoin(\
            bt.TABNAME_CFGCONTAB, "cau", idLeft="id_caus", idRight="id",\
            join=adb.JOIN_LEFT)
        mpa = reg.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag", idLeft="id_modpag", idRight="id",\
            join=adb.JOIN_LEFT)
        rif.AddOrder('rif.datscad')
        
        self.AddOrder('pcf.datscad')
        self.AddOrder('pdc.descriz')
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class PcfEffettiPresentatiRiepData(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PCF, 'pcf', fields=None)
        self.AddGroupOn('pcf.effdate')
        self.AddCountOf('1.0', 'effetti')
        self.AddOrder('pcf.effdate', adb.ORDER_DESCENDING)
        self.Reset()


# ------------------------------------------------------------------------------


class PcfEffettiPresentati(PcfMixin):
    
    def __init__(self):
        PcfMixin.__init__(self, bt.TABNAME_PCF, 'pcf')
        self._AddPcfJoins()
        self.AddField('pcf.imptot-pcf.imppar', 'saldo')
        self.ClearOrders()
        self.AddOrder('pcf.datscad')
        self.AddOrder('pdc.descriz')
        self.Reset()


# ------------------------------------------------------------------------------


class PdcSaldiGiornalieri(_PdcMovimMixin):
    """
    DbTable specializzato nella determinazione del saldo contabile di ogni
    sottoconto, per ogni giorno in cui vengono rilevate registrazioni.
    """
    def __init__(self):
        
        _PdcMovimMixin.__init__(self)
        self._info.data1 = None
        self._info.data2 = None
        
        del self.mov
        
        class Movim(adb.DbTable):
            def CalcProgr(self, func=None):
                if func is None:
                    func = lambda row: None
                nctd = self._GetFieldIndex('total_dare')
                ncta = self._GetFieldIndex('total_avere')
                ncpd = self._GetFieldIndex('total_progr_dare')
                ncpa = self._GetFieldIndex('total_progr_avere')
                ncsd = self._GetFieldIndex('total_saldo_dare')
                ncsa = self._GetFieldIndex('total_saldo_avere')
                ncxd = self._GetFieldIndex('total_saldoprogr_dare')
                ncxa = self._GetFieldIndex('total_saldoprogr_avere')
                tpd = 0
                tpa = 0
                rs = self.GetRecordset()
                for row in range(self.RowsCount()):
                    tsd = rs[row][nctd] or 0
                    tsa = rs[row][ncta] or 0
                    if tsd>=tsa:
                        rs[row][ncsd] = tsd-tsa
                        rs[row][ncsa] = None
                    else:
                        rs[row][ncsd] = None
                        rs[row][ncsa] = tsa-tsd
                    tpd += tsd
                    tpa += tsa
                    rs[row][ncpd] = tpd
                    rs[row][ncpa] = tpa
                    if tpd>=tpa:
                        rs[row][ncxd] = tpd-tpa
                        rs[row][ncxa] = None
                    else:
                        rs[row][ncxd] = None
                        rs[row][ncxa] = tpa-tpd
                    func(row)
        
        mov = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_B, "mov", idLeft="id", idRight="id_pdcpa",\
            fields=None, writable=True, dbTabClass=Movim)
        mov.AddBaseFilter("mov.tipriga IN ('S','C','A')")
        self.mov = mov
        
        self._AddMovTables()
        
        self.AddOrder("tipana.tipo")
        self.AddOrder("pdc.codice")
        mov.AddGroupOn("reg.datreg", "giorno")
        mov.AddOrder("reg.datreg")
        for segno, nome in (("D", "dare"),\
                            ("A", "avere")):
            mov.AddTotalOf(\
                "IF(mov.segno='%s', mov.importo, 0)" % segno, nome)
        mov.AddTotalOf("0.0", "saldo_dare")
        mov.AddTotalOf("0.0", "saldo_avere")
        mov.AddTotalOf("0.0", "progr_dare")
        mov.AddTotalOf("0.0", "progr_avere")
        mov.AddTotalOf("0.0", "saldoprogr_dare")
        mov.AddTotalOf("0.0", "saldoprogr_avere")
        
        self.Get(-1)
    
    def GetPeriodo(self):
        data1, data2 = self._info.data1, self._info.data2
        out = ''
        if data1:
            out = 'Dal %s' % self.dita(data1)
        if data2:
            if out:
                out += ' '
            out += 'fino al %s' % self.dita(data2)
        return out or 'Tutto'


# ------------------------------------------------------------------------------


class RegIva(adb.DbTable,
             _ExtendedNumDoc_mixin_):
    """
    Registro IVA.
    reg:contab_h
      +--> cau:cfgcontab
      +--> rei:regiva
      +=>> mov:contab_b
      |      +-> iva:aliqiva
      +=>> bcf:contab_b (solo riga1, cli/for)
      !      +-> pdc:pdc
      !            +-> anag:clienti x reg.iva tipo Vendite/Corrisp
      !            +-> anag:fornit  x reg.iva tipo Acquisti
      Esporta:
      _riepaliq (RiepAliq) totali x aliquota
      _lastpdat DateTime   data ultima stampa
      _lastppro int        ultimo protocollo stampato
      pdc è anche disponibile come istanza della classe (=.bcf.pdc)
      _riepaliq (RiepIva) istanza riepilogo aliquote iva.
    Data la natura della classe, che per la totalizzazione delle aliquote
    si appoggia sulla classe RegIva della quale contiene una istanza, i limiti
    di periodo devono essere impostati mediante il metodo SetLimits, che si
    occupa di applicare i filtri dovuti anche sull'oggetto di totalizzazione.
    """
    
    tiprei = None
    tipana = None
    segnop = None
    segnom = None
    
    def get_regiva(self):
        return self.rei
    
    def __init__(self, rivid, *args, **kwargs):
        """
        rivid id registro iva
        """
        adb.DbTable.__init__(self,\
                             bt.TABNAME_CONTAB_H, "reg", *args, **kwargs)
        
        r = adb.DbTable(bt.TABNAME_REGIVA, "riv")
        if not r.Get(rivid) or r.RowsCount() != 1:
            raise Exception, "Registro IVA errato (id=%s)" % rivid
        
        self._rivid =  r.id
        self._rivcod = r.codice
        self._rivdes = r.descriz
        self._rivtipo = r.tipo
        self._lastdate = r.lastprtdat
        self._lastprot = r.lastprtnum
        self._intestaz = r.intestaz
        self._intanno = r.intanno
        self._intpag = r.intpag
#=======================================stampa controp.su registi================================
        self._stacosric=r.stacosric
#=======================================stampa controp.su registi================================
        
        if r.tipo in "VC":
            self._info.segnop = "D"
            self._info.segnom = "A"
            tabanag = bt.TABNAME_CLIENTI
        else:
            self._info.segnop = "A"
            self._info.segnom = "D"
            tabanag = bt.TABNAME_FORNIT
        del r
        
        p = adb.DbTable(bt.TABNAME_CFGPROGR, "pr")
        
        mov = self.AddMultiJoin(\
            bt.TABNAME_CONTAB_B,  "mov")
        
        s = self._info.segnom
#=======================================stampa controp.su registi================================
        if bt.TIPO_CONTAB=='O' and self._stacosric:
            mov.AddFilter("mov.tipriga IN ('I', 'E', 'O', 'C')")
            mov.AddField("mov.imponib*IF(mov.segno='%s',1,-1)*IF(mov.tipriga='C',0,1)" % s, "total_imponib")
            mov.AddField("mov.imposta*IF(mov.segno='%s',1,-1)*IF(mov.tipriga='C',0,1)" % s, "total_imposta")
            mov.AddField("mov.indeduc*IF(mov.segno='%s',1,-1)*IF(mov.tipriga='C',0,1)" % s, "total_indeduc")
        else:
            mov.AddFilter("mov.tipriga IN ('I', 'E', 'O')")
            mov.AddField("mov.imponib*IF(mov.segno='%s',1,-1)" % s, "total_imponib")
            mov.AddField("mov.imposta*IF(mov.segno='%s',1,-1)" % s, "total_imposta")
            mov.AddField("mov.indeduc*IF(mov.segno='%s',1,-1)" % s, "total_indeduc")
#=======================================stampa controp.su registi================================
        
        bodycf = self.AddJoin(\
            bt.TABNAME_CONTAB_B,  "bcf", idLeft="id", idRight="id_reg",\
            join=adb.JOIN_LEFT)
        bodycf.AddFilter("bcf.numriga=1")
        
        pdc = bodycf.AddJoin(\
            bt.TABNAME_PDC,       "pdc", idLeft="id_pdcpa",\
            join=adb.JOIN_LEFT)
        self.pdc = pdc
        
        anag = pdc.AddMultiJoin(tabanag, "anag", idLeft="id", idRight="id")
        
        tot = self.AddJoin(\
            bt.TABNAME_CONTAB_B,  "tot", idLeft="id", idRight="id_reg",\
            join=adb.JOIN_LEFT, fields=None)
        tot.AddFilter("tot.tipriga IN ('I', 'E', 'O')")
        
        s = self._info.segnom
        self.AddGroupOn("reg.id")
        self.AddTotalOf("tot.imponib*IF(tot.segno='%s',1,-1)" % s, "imponib")
        self.AddTotalOf("tot.imposta*IF(tot.segno='%s',1,-1)" % s, "imposta")
        self.AddTotalOf("tot.indeduc*IF(tot.segno='%s',1,-1)" % s, "indeduc")
        
#=======================================stampa controp.su registi================================
        if bt.TIPO_CONTAB=='O' and self._stacosric:
            iva = mov.AddJoin(\
                bt.TABNAME_ALIQIVA,   "iva", join=adb.JOIN_LEFT)
        else:
            iva = mov.AddJoin(\
                bt.TABNAME_ALIQIVA,   "iva")
#=======================================stampa controp.su registi================================
        
        pdp = mov.AddJoin(\
            bt.TABNAME_PDC,       "pdcpa", idLeft='id_pdcpa', join=adb.JOIN_LEFT)
        
        cau = self.AddJoin(\
            bt.TABNAME_CFGCONTAB, "cau", idLeft="id_caus")
        
        rei = self.AddJoin(\
            bt.TABNAME_REGIVA,    "rei", idLeft="id_regiva")
        
        self._riepaliq = None
        self._tipostampa = None
        self._year = Env.Azienda.Esercizio.year
        self._datmin = None
        self._datmax = None
        #self._lastdate = None
        #self._lastprot = None
        
        #self.AddOrder("reg.datreg")
        self.AddOrder("YEAR(reg.datreg)")
        self.AddOrder("reg.numiva")
        self.AddOrder("reg.datreg")
        
        self.Get(-1)
        
        self.dbprg = adb.DbTable(bt.TABNAME_CFGPROGR, "progr")
        
        #il registro iva indirizza di fatto anche la tipologia del tipo anagrafico:
        #Clienti per vendite e corrispettivi, Fornitori per acquisti
        #Ci possono essere tuttavia alcuni tipi di registrazione che esulano da tale accoppiamento;
        #Ad esempio, le autofatture cee che vanno sul registro vendite ma riguardano i fornitori.
        #In tali situazioni, il codice fiscale/partita iva non può essere prelevato dalla tabella
        #anagrafica linkata a pdc della registrazione, poiché il dato non è proprio presente.
        #In tali casi verranno recuperati mediante ricerca apposita sul seguente DbTable interno: 
        self.dbpdc = adb.DbTable(bt.TABNAME_PDC, "pdc",    fields="id,codice,descriz")
        self.dbpdc.AddJoin(bt.TABNAME_CLIENTI,   "anacli", fields="id,codfisc,nazione,piva", idLeft='id', join=adb.JOIN_LEFT)
        self.dbpdc.AddJoin(bt.TABNAME_FORNIT,    "anafor", fields="id,codfisc,nazione,piva", idLeft='id', join=adb.JOIN_LEFT)
        
        self.ReadLast()
    
    def SetTipoStampa(self, tiposta):
        """
        Imposta il tipo di stampa associata.  A seconda del tipo, vengono
        prese in considerazione diverse registrazioni iva:
        x tipo "P" o "D", registrazioni mai stampate
        x tipo "R" solo registrazioni già stampate
        
        """
        if not tiposta in "PDR":
            raise Exception, "Tipo stampa errato (%s)" % tiposta
        self._tipostampa = tiposta
    
    def SetYear(self, year):
        """
        Imposta l'anno per la determinazione dell'ultima data e protocollo
        stampato.  Per default la determinazione avviene in base all'anno
        della data di elaborazione.
        """
        self._year = year
        self.ReadLast()
    
    def ReadLast(self):
        """
        Determina data e ultimo protocollo stampato e li rende disponibili
        su:
        ._lastdate
        ._lastprot
        """
        r = adb.DbTable(bt.TABNAME_REGIVA, "riv")
        if r.Get(self._rivid) and r.RowsCount() == 1:
            self._lastdate = r.lastprtdat
            self._lastprot = r.lastprtnum
    
    def WriteLast(self):
        """
        Aggiorna data e ultimo protocollo stampato
        """
        out = False
        r = adb.DbTable(bt.TABNAME_REGIVA, "riv")
        if r.Get(self._rivid) and r.RowsCount() == 1:
            r.lastprtdat = self._lastdate
            r.lastprtnum = self._lastprot
            if r.Save():
                out = True
        return out
    
    def SetLimits(self, dreg1, dreg2, protini=None, radate=None, raprot=None):
        """
        Imposta il periodo:
        d1 = data partenza
        d2 = data fine
        Opzionalmente:
        protini num. protocollo iniziale
        radate  data partenza riepilogo aliquote
        raprot  prot.partenza riepilogo aliquote
        """
        self.ClearFilters()
        self.AddFilter("reg.id_regiva='%s'" % self._rivid)
        self.AddFilter(r"reg.datreg>=%s", dreg1)
        self.AddFilter(r"reg.datreg<=%s", dreg2)
        if protini:# is not None:
            self.AddFilter(r"reg.numiva>=%s", protini)
        
        if self._riepaliq is None:
            i = self._info
            self._riepaliq = RiepIva(self._rivid, i.segnop, i.segnom, 
                                     dreg1, dreg2)
        ra = self._riepaliq
        ra.ClearFilters()
        ra.AddFilter("reg.id_regiva='%s'" % self._rivid)
        if radate is None: radate = dreg1
        ra.AddFilter(r"reg.datreg>=%s", radate)
        ra.AddFilter(r"reg.datreg<=%s", dreg2)
        if raprot:# is not None:
            ra.AddFilter(r"reg.numiva>=%s", raprot)
        
        ts = self._tipostampa
        if ts:
            for x in (self, ra):
                if ts in "PD":  #stampa provvisoria, definitiva
                    x.AddFilter("reg.st_regiva<>1 OR reg.st_regiva IS NULL")
                elif ts == "R": #ristampa
                    x.AddFilter("reg.st_regiva=1")
        
        self._datmin = dreg1
        self._datmax = dreg2

    def Retrieve(self, *args, **kwargs):
        """
        Interno, si occupa di aggiornare l'oggetto ._riepaliq x la 
        totalizzazione delle aliquote iva.
        """
        out = adb.DbTable.Retrieve(self, *args, **kwargs)
        if out and self._riepaliq is not None: out = self._riepaliq.Retrieve()
        return out

    def GetTotIva(self):
        """
        Ritorna una tupla contenente le sommatorie di:
        imponibile
        imposta
        indeducibile
        """
        return self.GetTotalOf(("total_imponib",\
                                "total_imposta",\
                                "total_indeduc"))
    
    def GetPIVA(self):
        """
        Determina la p.iva o il cod.fiscale dell'anagrafica dell'operazione.
        """
        out = None
        if self.pdc.anag.id:
            #anagrafica cliente/fornitore direttamente correlata a tabella pdc
            anag = self.pdc.anag
        else:
            #anagrafica cliente/fornitore non trovata correlando da tabella pdc, la cerco
            pdc = self.dbpdc
            pdc.Get(self.pdc.id)
            if pdc.anacli.id:
                anag = pdc.anacli
            elif pdc.anafor.id:
                anag = pdc.anafor
            else:
                anag = None
        if anag:
            if anag.piva:
                out = anag.piva
                if anag.nazione and anag.nazione != "IT":
                    out = anag.nazione+out
            else:
                out = anag.codfisc
        return out
    
    def CtrSeq(self):
        rs = self.GetRecordset()
        datcol, nivcol = map(lambda col: self._GetFieldIndex(col, inline=True),
                             'datreg numiva'.split())
        ldat = lniv = None
        for r in rs:
            dat = r[datcol]
            niv = r[nivcol] or 0
            if ldat is not None:
                if dat<ldat:
                    return 'Protocollo fuori sequenza', niv, dat
                elif not self.rei.noprot and niv != (lniv+1) and getattr(dat, 'year', None) == getattr(ldat, 'year', None):
                    return 'Protocollo mancante', lniv+1, ldat
            ldat = dat
            lniv = niv
        return None, lniv, ldat
    
    def ElaboraDefin(self, func=None):
        ids = []
        for n, reg in enumerate(self):
            ids.append(self.id)
            if func:
                func(n, reg)
        db = self._info.db
        db.Execute("""
        UPDATE %s reg SET st_regiva=1
         WHERE reg.id IN (%s)""" % (bt.TABNAME_CONTAB_H,
                                    ', '.join(map(str,ids))))
        out = self.WriteLast()
        return out

    
# ------------------------------------------------------------------------------


class RiepIva(adb.DbTable):
    """
    Riepilogo aliquote x Registro IVA.
    """
    def __init__(self, rivid, segnop, segnom, datmin, datmax, **kwargs):
        """
        rivid id registro iva
        """
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_B,  "mov", **kwargs)
        
        self._info.rivid =  rivid
        self._info.segnop = segnop
        self._info.segnom = segnom
        self._info.datmin = datmin
        self._info.datmax = datmax
        
        class AliqIva(adb.DbTable):
            def IsNormale(self):
                return not self.tipo
            def IsCEE(self):
                return self.tipo == 'C'
            def IsSosp(self):
                return self.tipo == 'S'
        
        iva = self.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva", dbTabClass=AliqIva)
        
        reg = self.AddJoin(\
            bt.TABNAME_CONTAB_H,  "reg")
        
        cau = reg.AddJoin(\
            bt.TABNAME_CFGCONTAB, "cau", idLeft="id_caus")
        
        rei = reg.AddJoin(\
            bt.TABNAME_REGIVA,    "rei", idLeft="id_regiva")
        
        s = self._info.segnom
        self.AddGroupOn("mov.id_aliqiva")
        self.AddTotalOf("mov.imponib*IF(mov.segno='%s',1,-1)" % s, "imponib")
        self.AddTotalOf("mov.imposta*IF(mov.segno='%s',1,-1)" % s, "imposta")
        self.AddTotalOf("mov.indeduc*IF(mov.segno='%s',1,-1)" % s, "indeduc")
        self.AddCountOf("mov.id", "righe")
        self.AddFilter("mov.tipriga IN ('I', 'E', 'O')")
        self.AddOrder("iva.codice")
        
        self.Get(-1)

    def GetTotIva(self):
        """
        Ritorna una tupla contenente le sommatorie di:
        imponibile
        imposta
        indeducibile
        """
        return self.GetTotalOf(("total_imponib",\
                                "total_imposta",\
                                "total_indeduc"))


# ------------------------------------------------------------------------------


class RiepRegCon(adb.DbTable):
    """
    Riepilogo registrazioni contabili.
    """
    def __init__(self, **kwargs):
        
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_H, "reg", **kwargs)
        
        config = self.AddJoin(\
            bt.TABNAME_CFGCONTAB,"config",    idLeft="id_caus",\
            join=adb.JOIN_LEFT)
        
        regiva = self.AddJoin(\
            bt.TABNAME_REGIVA,   "regiva",    idLeft="id_regiva",\
            join=adb.JOIN_LEFT)
        
        body = self.AddJoin(\
            bt.TABNAME_CONTAB_B, "body",      idLeft="id", idRight="id_reg",\
            join=adb.JOIN_LEFT)
        #body.AddFilter("body.numriga=1")
        body.AddField("IF(body.segno='D',body.importo,0)", "dare")
        body.AddField("IF(body.segno='A',body.importo,0)", "avere")
        
        pdc = body.AddJoin(\
            bt.TABNAME_PDC,      "pdc",       idLeft="id_pdcpa", idRight="id",\
            join=adb.JOIN_LEFT)
        
        self.pdc = pdc
        
        self.AddOrder("reg.datreg")
        self.AddOrder("regiva.codice")
        self.AddOrder("reg.numiva")
        self.AddOrder("reg.datdoc")
        self.AddOrder("reg.numdoc")
        self.AddOrder("config.codice")
        
        self.AddGroupOn("reg.id")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class RiepMovCon(adb.DbTable):
    """
    Riepilogo registrazioni contabili, viste x dettaglio regstrazione.
    """
    def __init__(self, **kwargs):
        
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_B, "body", **kwargs)
        
        reg = self.AddJoin(\
            bt.TABNAME_CONTAB_H, "reg", join=adb.JOIN_LEFT)
        
        config = reg.AddJoin(\
            bt.TABNAME_CFGCONTAB,"config",    idLeft="id_caus",\
            join=adb.JOIN_LEFT)
        
        regiva = reg.AddJoin(\
            bt.TABNAME_REGIVA,   "regiva",    idLeft="id_regiva",\
            join=adb.JOIN_LEFT)
        
        pdc = self.AddJoin(\
            bt.TABNAME_PDC,      "pdc",       idLeft="id_pdcpa",  idRight="id",\
            join=adb.JOIN_LEFT)
        
        #pcp = self.AddJoin(\
            #bt.TABNAME_PDC,      "pdccp",     idLeft="id_pdccp",  idRight="id",\
            #join=adb.JOIN_LEFT)
        
        tpa = pdc.AddJoin(\
            bt.TABNAME_PDCTIP,   "pdctip",    idLeft="id_tipo",   idRight="id",\
            join=adb.JOIN_LEFT)
        
        bilmas = pdc.AddJoin(\
            bt.TABNAME_BILMAS,   "bilmas",    idLeft="id_bilmas", idRight="id",\
            join=adb.JOIN_LEFT, fields="id,codice,descriz,tipo")
        
        bilcon = pdc.AddJoin(\
            bt.TABNAME_BILCON,   "bilcon",    idLeft="id_bilcon", idRight="id",\
            join=adb.JOIN_LEFT, fields="id,codice,descriz")
        
        anac = pdc.AddJoin(\
            bt.TABNAME_CLIENTI,  "anacli",    idLeft="id",        idRight="id",\
            join=adb.JOIN_LEFT, fields="id,piva,codfisc")
        
        anaf = pdc.AddJoin(\
            bt.TABNAME_FORNIT,   "anafor",    idLeft="id",        idRight="id",\
            join=adb.JOIN_LEFT, fields="id,piva,codfisc")
        
        aliqiva = self.AddJoin(\
            bt.TABNAME_ALIQIVA, "aliqiva",    idLeft="id_aliqiva",idRight="id",\
            join=adb.JOIN_LEFT)
        
        self.AddField("IF(body.segno='D',body.importo,0)", "dare")
        self.AddField("IF(body.segno='A',body.importo,0)", "avere")
        
        self.AddOrder("reg.datreg")
        self.AddOrder("regiva.codice")
        self.AddOrder("reg.numiva")
        self.AddOrder("reg.datdoc")
        self.AddOrder("reg.numdoc")
        self.AddOrder("reg.id")
        self.AddOrder("body.numriga")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class GiornaleGenerale(RiepMovCon):
    
    def __init__(self, *args, **kwargs):
        
        RiepMovCon.__init__(self, *args, **kwargs)
        
        self.SetModoStampa('P')
        
        _tipirighe = "SCA"
        if bt.TIPO_CONTAB == "S":
            _tipirighe += "I"
        self.AddBaseFilter("body.tipriga IN (%s)" % ','.join(["'%s'" % tr for tr in _tipirighe]))
        
        self._info.colidreg = self._GetFieldIndex('id_reg')-1
    
    def SetModoStampa(self, ms):
        assert ms in 'PDR'
        self.ClearOrders()
        self.AddOrder("reg.datreg")
        if ms == 'R':
            self.AddOrder("body.nrigiobol")
        else:
            self.AddOrder("reg.id")
            self.AddOrder("body.numriga")
    
    def RecordUpdated(self, rsrow):
        """
        Richiamato in fase di aggiornamento dei movimenti, provvede a settare il flag
        st_giobol=1 sul record di testata della registrazione corrispondente.
        """
        e = db = self._info.db.Execute
        idreg = rsrow[self._info.colidreg]
        e("UPDATE %s SET st_giobol=1 WHERE id=%%s" % bt.TABNAME_CONTAB_H, (idreg,))
        #print 'id_reg=%d' % idreg
    
    def NumeraRighe(self, start, ec, ep, rinum=True, func=None):
        tecd = teca = 0
        tepd = tepa = 0
        nc_id, nc_nrg, nc_dare, nc_avere = map(lambda x: self._GetFieldIndex(x, inline=True),
                                               'id nrigiobol dare avere'.split())
        nc_ese = self.reg._GetFieldIndex('esercizio', inline=True)
        rs = self.GetRecordset()
        mr = self._info.modifiedRecords
        nr = start
        for n, r in enumerate(rs):
            if rinum:
                r[nc_nrg] = nr
                rid = r[nc_id]
                if not rid in mr:
                    mr.append(rid)
            try:
                if r[nc_ese] == ec:
                    tecd += r[nc_dare] or 0
                    teca += r[nc_avere] or 0
                elif r[nc_ese] == ep:
                    tepd += r[nc_dare] or 0
                    tepa += r[nc_avere] or 0
            except TypeError:
                pass
            nr += 1
            if func:
                func(n)
        return tecd, teca, tepd, tepa


# ------------------------------------------------------------------------------


class MovAliqIvaTable(RiepMovCon):
    
    def __init__(self, **kwargs):
        
        RiepMovCon.__init__(self, **kwargs)
        
        #importo, imposta, indeducibile con segno opportuno
        self.AddField('IF(regiva.tipo="A" AND config.pasegno="A" OR regiva.tipo IN ("V", "C") AND config.pasegno="D", body.imponib, IF(regiva.tipo="A" AND config.pasegno="D" OR regiva.tipo IN ("V", "C") AND config.pasegno="A", -body.imponib, 0))', 'valimponib')
        self.AddField('IF(regiva.tipo="A" AND config.pasegno="A" OR regiva.tipo IN ("V", "C") AND config.pasegno="D", body.imposta, IF(regiva.tipo="A" AND config.pasegno="D" OR regiva.tipo IN ("V", "C") AND config.pasegno="A", -body.imposta, 0))', 'valimposta')
        self.AddField('IF(regiva.tipo="A" AND config.pasegno="A" OR regiva.tipo IN ("V", "C") AND config.pasegno="D", body.indeduc, IF(regiva.tipo="A" AND config.pasegno="D" OR regiva.tipo IN ("V", "C") AND config.pasegno="A", -body.indeduc, 0))', 'valindeduc')
        
        self.Reset()


# ------------------------------------------------------------------------------


class RiepRegIva(adb.DbTable):
    """
    Riepilogo registrazioni iva.
    """
    def __init__(self, **kwargs):
        
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_H, "reg", **kwargs)
        
        config = self.AddJoin(\
            bt.TABNAME_CFGCONTAB,"config",    idLeft="id_caus",\
            join=adb.JOIN_LEFT)
        
        regiva = self.AddJoin(\
            bt.TABNAME_REGIVA,   "regiva",    idLeft="id_regiva",\
            join=adb.JOIN_LEFT)
        
        body = self.AddJoin(\
            bt.TABNAME_CONTAB_B, "body",      idLeft="id", idRight="id_reg",\
            join=adb.JOIN_LEFT)
        body.AddFilter("body.numriga=1 OR body.tipriga='E'")
        
        pdc = body.AddJoin(\
            bt.TABNAME_PDC,      "pdc",       idLeft="id_pdcpa", idRight="id",\
            join=adb.JOIN_LEFT)
        
        tot = self.AddJoin(\
            bt.TABNAME_CONTAB_B, "tot",       idLeft="id", idRight="id_reg",\
            join=adb.JOIN_LEFT, fields=None)
        tot.AddFilter("tot.tipriga IN ('I', 'E', 'O')")
        
        self.pdc = pdc
        
        sgnexpr = """
IF(regiva.tipo='A' AND tot.segno='D' 
OR regiva.tipo<>'A' AND tot.segno='A',1,-1)"""
        self.AddGroupOn("reg.id")
        self.AddTotalOf("tot.imponib*%s" % sgnexpr, "imponib")
        self.AddTotalOf("tot.imposta*%s" % sgnexpr, "imposta")
        self.AddTotalOf("tot.indeduc*%s" % sgnexpr, "indeduc")
        
        self.AddOrder("reg.datreg")
        self.AddOrder("regiva.codice")
        self.AddOrder("reg.numiva")
        self.AddOrder("reg.id")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


LIQIVA_ALIQ_ID =    0
LIQIVA_ALIQ_COD =   1
LIQIVA_ALIQ_DESC =  2
LIQIVA_ALIQ_PERC =  3
LIQIVA_ALIQ_INDED = 4
LIQIVA_ALIQ_TIPO =  5
LIQIVA_TOTIMPONIB = 6
LIQIVA_TOTIMPOSTA = 7
LIQIVA_TOTINDEDUC = 8

class ValoriErrati_Exception(Exception):
    pass

class LiqIva(adb.DbTable):
    """
    Elenco Registri IVA per liquidazione.
    regiva
    
    Esporta:
      regiva (RegIva) DbTable registro iva
      totaliq (list)  totali iva
    La classe estrae tutti i registri iva configurati, e per ognuno rende 
    disponibile la variabile C{regiva}, istanza della classe C{RegIva} 
    opportunamente popolata dai dati del registro iva relativo; prima di 
    popolare la DbTable, occorre obbligatoriamente specificare:
        - il tipo di elaborazione provvisoria/definitiva tramite C{SetTipoLiq(t)}
            dove t è "P" o "D"
        - il periodo da considerare tramite C{SetLimits(da_data, a_data)}
    Esempio:
        e = RegIvaElenco()
        e.SetTipoLiq("P")
        e.SetLimits(data1, data2)
        e.Retrieve()
        for r in e:
            ... => r contiene l'intero regitro iva come da classe C{RegIva}
    """
    
    def __init__(self, periodic=None, *args, **kwargs):
        """
        periodic è la periodicità di liquidazione "M" o "T" 
        Per default viene letto il flag dalla tabella cfgsetup in corrispondenza
        della chiave liqiva_periodic
        """
        adb.DbTable.__init__(self,\
                             bt.TABNAME_REGIVA, "regs", *args, **kwargs)
        
        #progressivi
        self._progr = adb.DbTable(
            bt.TABNAME_CFGPROGR, 'progr', writable=True)
        
        #liquidazioni effettuate
        self._liqeff = adb.DbTable(
            bt.TABNAME_LIQIVA,  'liqeff', writable=True)
        
        #riepilogo aliquote liquidazioni effettuate
        self._liqaliqeff = adb.DbTable(
            bt.TABNAME_LIQIVA,  'liqaliqeff', writable=True)
        
        self.regiva = None
        
        if periodic is None:
            s = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')
            if s.Retrieve('setup.chiave=%s', 'liqiva_periodic') and s.OneRow():
                periodic = s.flag
            else:
                class SetupMancante_Exception(Exception): pass
                raise SetupMancante_Exception
            del s
        
        if not (periodic or ' ') in "MT":
            class PeriodicError_Exception(Exception): pass
            raise PeriodicError_Exception
        
        self._year = Env.Azienda.Esercizio.year
        self._datmin = None      #data min. calcolo
        self._datmax = None      #data max. calcolo
        self._tipelab = "P"      #liquid. P/D provv./defin.
        self._tipoper = periodic #periodicita M/T mensile/trimestr.
        self._periodo = None     #num.periodo 1-12/1-4
        
        self._totxtip = {"A": [], #totali acquisti
                         "V": [], #totali vendite
                         "C": []} #totali corrispettivi
        
        self._totxreg = {}        #totali x registro
        
        self._totali = {}
        self.ResetTotali()
        
        self._cricom = {'cricomstart': 0, #credito iva compens. inizio anno
                        'cricomdisp':  0} #credito iva compens. disponib.
    
    def ResetTotali(self):
        #totalizzari per il calcolo
        for key in ('vennor1', 'vennor2', #vendite
                    'vencor1', 'vencor2', #corrispettivi
                    'venven1', 'venven2', #ventilazione
                    'acqnor1', 'acqnor2', #acquisti
                    'acqcee1', 'acqcee2', #acquisti cee
                    'tivper1', 'tivper2', #totale iva periodo
                    'vensos1', 'vensos2', #vendite sospensione
                    'ivaind1', 'ivaind2', #iva indeducibile
                    'docper1', 'docper2', #debito/credito periodo
                    
                    #totalizzatori per il prospetto
                    'ivaesi1', 'ivadet2', #iva esig. e che si detrae
                    'ivadcp1', 'ivadcp2', #debito/credito periodo
                               'crsdet2', #crediti speciali di imposta detratti
                    'varpre1', 'varpre2', #variaz. periodi preced.
                    'invpre1', 'invpre2', #iva non vers. periodi pre.
                    'docpre1', 'docpre2', #deb/cred. periodo prec.
                               'cricom2', #cred.comp. in detraz.
                    'ivadov1', 'ivadov2', #iva dovuta/cred. periodo
                    'percint',            #tasso int. x liq.trim.
                    'inttri1',            #interessi x liq.trim.
                               'acciva2', #acconto versato
                    'vertra1',            #importo da vers./trasf.
                    'docfin1', 'docfin2', #deb/cred. risult. periodo
                    
                    #credito iva compensabile - prospetto
                    'ciciniz',  #disponibile all'inizio della liquidaz.
                    'ciculiq',  #utilizzato nella liquidazione
                    'cicuf24',  #utilizzato con l'F24
                    'cicfine'): #disponibile alla fine della liquidaz.
            self._totali[key] = 0
        
        p = self._progr
        if p.Retrieve('progr.codice=%s', 'liqiva_percint') and p.OneRow():
            self._totali['percint'] = p.progrimp1 or 0
    
    def SetYear(self, year):
        """
        Imposta l'anno per la determinazione dell'ultima data e protocollo
        stampato.  Per default la determinazione avviene in base all'anno
        della data di elaborazione.
        """
        self._year = year
        self.UpdateLiqEff()
    
    def UpdateLiqEff(self):
        le = self._liqeff
        le.ClearFilters()
        le.AddFilter('liqeff.anno=%s', self._year)
        le.Retrieve()
        p = self._progr
        for key in ('cricomstart', 'cricomdisp'):
            p.ClearFilters()
            p.AddFilter("progr.codice=%s", 'iva_%s' % key)
            p.AddFilter("progr.keydiff=%s", str(self._year))
            self._totali[key] = 0
            if p.Retrieve():
                self._cricom[key] = p.progrimp1 or 0
    
    def SetTipoLiq(self, tipo):
        """
        Imposta il tipo di elaborazione:
            "P" provvisoria - solo registrazioni non stampate su registro
            "D" definitiva - solo registrazioni già stampate su registro
        """
        self._tipelab = tipo
    
    def SetPeriodo(self, periodo, dreg1, dreg2):
        """
        Imposta il periodo:
        periodo = 1-12/1-4 mese/trimestre
        dreg1 = data inizio calcolo
        dreg2 = data fine calcolo
        """
        self._periodo = periodo
        self._datmin = dreg1
        self._datmax = dreg2
        self.SetYear(dreg1.year)
    
    def _UpdateTableVars(self, *args, **kwargs):
        adb.DbTable._UpdateTableVars(self, *args, **kwargs)
        if self.id is None:
            self.regiva = None
        else:
            if self.regiva is None or self.regiva._rivid != self.id:
                r = RegIva(self.id)
                if self._tipelab == "D":
                    r.SetTipoStampa(self._tipelab)
                r.SetLimits(self._datmin, self._datmax)
                r.Retrieve()
                self.regiva = r

    def Totalizza(self, cbf=None):
        
        mt = self._totali
        
        for key in "AVC":
            del self._totxtip[key][:]
        
        self.ResetTotali()
        
        self._totxreg = {}
        for r in self:
            self._totxreg[r.id] = []
            tipo = r.regiva._rivtipo
            key = ('acqnor', 'vennor', 'vencor')["AVC".index(tipo)]
            for aliq in r.regiva._riepaliq:
                for t, tot in enumerate((self._totxreg[r.id],\
                                         self._totxtip[r.regiva._rivtipo])):
                    n = None
                    for x in range(len(tot)):
                        if tot[x][LIQIVA_ALIQ_ID] == aliq.iva.id:
                            n = x
                    if n is None:
                        tot.append([aliq.iva.id,      #LIQIVA_ALIQ_ID
                                    aliq.iva.codice,  #LIQIVA_ALIQ_COD
                                    aliq.iva.descriz, #LIQIVA_ALIQ_DESC
                                    aliq.iva.perciva, #LIQIVA_ALIQ_PERC
                                    aliq.iva.percind, #LIQIVA_ALIQ_INDED
                                    aliq.iva.tipo,    #LIQIVA_ALIQ_TIPO
                                    0,                #LIQIVA_TOTIMPONIB
                                    0,                #LIQIVA_TOTIMPOSTA
                                    0])               #LIQIVA_TOTINDEDUC
                        n = len(tot)-1
                    imponib = aliq.total_imponib or 0
                    imposta = aliq.total_imposta or 0
                    indeduc = aliq.total_indeduc or 0
                    tot[n][LIQIVA_TOTIMPONIB] += imponib
                    tot[n][LIQIVA_TOTIMPOSTA] += imposta
                    tot[n][LIQIVA_TOTINDEDUC] += indeduc
                    if t == 0:
                        if key.startswith('ven'):
                            col = '1'
                        else:
                            col = '2'
                        if not aliq.iva.tipo:
                            #iva normale
                            mt[key+col] += imposta
                        elif aliq.iva.tipo == "C":
                            #iva cee
                            mt['acqcee'+col] += imposta
                        elif aliq.iva.tipo == "S":
                            #iva sosp.
                            mt['vensos'+col] += imposta
            if cbf is not None:
                cbf(r)
        
        #lettura debito/credito periodo precedente
        p = self._progr
        p.ClearFilters()
        p.AddFilter('progr.codice=%s', 'iva_debcred')
        p.AddFilter('progr.keydiff=%s', self._year)
        p.AddFilter('progr.progrdate=%s', self._datmin-1)
        if p.Retrieve() and p.OneRow():
            if p.progrimp2>0 or p.progrimp2 is None:
                #riporto di un credito
                mt['docpre2'] = p.progrimp1 or 0
            elif p.progrimp2<0:
                #riporto di un debito
                mt['docpre1'] = p.progrimp1 or 0
        
        self.Calcola()
    
    def Calcola(self):
        self.CalcolaCalcolo()
        self.CalcolaProspetto()
    
    def CalcolaCalcolo(self):
        mt = self._totali
        #calcolo del debito/credito
        mt['tivper1'] = mt['tivper2'] = 0
        for key in ('vennor', 'vencor', 'venven', 'acqnor', 'acqcee'):
            for col in '12':
                mt['tivper'+col] += mt[key+col]
        sl = mt['tivper1']-mt['tivper2']
        if sl>=0:
            mt['docper1'], mt['docper2'] = sl, 0
        else:
            mt['docper1'], mt['docper2'] = 0, abs(sl)
        
    def CalcolaProspetto(self):
        mt = self._totali
        cc = self._cricom
        #test valori negativi
        for key in ('ivadcp1', 'ivadcp2',
                    'docpre1', 'docpre2', 'cricom2',
                    'percint', 'inttri1', 'acciva2', 'vertra1'):
            if mt[key] < 0:
                raise ValoriErrati_Exception,\
                      "Valore errato (%s)" % key
        if mt['inttri1'] and self._tipoper != "T":
            raise ValoriErrati_Exception,\
                  "Interessi non applicabili"
        if mt['cricom2']+mt['cicuf24'] > cc['cricomdisp']:
            raise ValoriErrati_Exception,\
                  "Credito Iva compensabile insufficiente"
        #prospetto di liquidazione
        #mt['ivaesi1'], mt['ivadet2'] = mt['docper1'], mt['docper2']
        mt['ivaesi1'], mt['ivadet2'] = mt['tivper1'], mt['tivper2']
        mt['ivadcp1'], mt['ivadcp2'] = mt['docper1'], mt['docper2']
        mt['ivadov1'], mt['ivadov2'] = 0, mt['cricom2']
        for key in ('ivadcp', 'varpre', 'invpre', 'docpre'):
            for col in '12':
                mt['ivadov'+col] += mt[key+col]
        if mt['ivadov1']>mt['ivadov2']:
            mt['ivadov1'] -= mt['ivadov2']
            mt['ivadov2'] = 0
        elif mt['ivadov1']<mt['ivadov2']:
            mt['ivadov2'] -= mt['ivadov1']
            mt['ivadov1'] = 0
        mt['docfin1'] = mt['ivadov1']+mt['inttri1']
        mt['docfin2'] = mt['ivadov2']+mt['acciva2']
        sl = mt['docfin1']-mt['docfin2']-mt['crsdet2']
        if sl >= 0:
            mt['docfin1'], mt['docfin2'] = sl, 0
        else:
            mt['docfin1'], mt['docfin2'] = 0, abs(sl)
        #calcolo del versamento
        if mt['docfin1'] >= 25.82:
            #il debito totale supera il limite del versamento minimo di 25,82 (ex 50.000 lire)
            mt['vertra1'] = mt['docfin1']
            mt['docfin1'] = mt['docfin2'] = 0
        else:
            #il debito totale non supera il limite del versamento minimo di 25,82 (ex 50.000 lire)
            #andrà riportato come debito del periodo precedente sulla liq.successiva
            mt['vertra1'] = 0
        #credito compensabile
        mt['ciciniz'] = cc['cricomdisp']
        mt['ciculiq'] = mt['cricom2']
        mt['cicfine'] = mt['ciciniz']-mt['ciculiq']-mt['cicuf24']
    
    def TestValori(self):
        out = True
        try:
            self.Calcola()
        except ValoriErrati_Exception:
            out = False
        return out
    
    def SaveLiq(self, regiva_id=None, regiva_anno=None, regiva_pag=None):
        le = self._liqeff
        if not self.TestValori():
            return False
        if regiva_id is not None and regiva_anno is not None and regiva_pag is not None:
            if regiva_pag>=0:
                ri = adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
                if ri.Get(regiva_id) and ri.OneRow():
                    ri.intanno = regiva_anno
                    ri.intpag = regiva_pag
                    ri.Save()
        def R(val):
            return round(val, Env.Azienda.BaseTab.VALINT_DECIMALS)
        le.Reset()
        le.CreateNewRow()
        le.anno =    self._year
        le.datmin =  self._datmin
        le.datmax =  self._datmax
        le.datliq =  Env.Azienda.Esercizio.dataElab
        le.periodo = self._periodo
        for key, val in self._totali.iteritems():
            if key in le._info.fieldNames:
                if type(val) is float:
                    val = R(val)
                setattr(le, key, val)
        out = le.Save()
        if out:
            p = self._progr
            p.ClearFilters()
            p.AddFilter("progr.codice=%s", 'iva_cricomdisp')
            p.AddFilter("progr.keydiff=%s", str(self._year))
            if p.Retrieve():
                if p.IsEmpty():
                    p.CreateNewRow()
                    p.keydiff = self._year
                    p.codice = 'iva_cricomdisp'
                p.progrimp1 = self._totali['cicfine']
                if not p.Save():
                    out = False
                    self.SetError(p.GetError())
            p.ClearFilters()
            p.AddFilter("progr.codice=%s", 'iva_debcred')
            p.AddFilter("progr.keydiff=%s", str(self._year))
            if p.Retrieve():
                if p.IsEmpty():
                    p.CreateNewRow()
                    p.keydiff = self._year
                    p.codice = 'iva_debcred'
                sal = self._totali['docfin2']-self._totali['docfin1']
                p.progrimp1 = R(abs(sal))
                if sal>=0:
                    p.progrimp2 = 1
                else:
                    p.progrimp2 = -1
                p.progrnum =  self._periodo
                #p.progrdate = Env.Azienda.Esercizio.dataElab
                p.progrdate = self._datmax
                if not p.Save():
                    out = False
                    self.SetError(p.GetError())
        self.UpdateLiqEff()
        return out


# ------------------------------------------------------------------------------


class RegIvaStatus(adb.DbTable):
    """
    Riepilogo registri iva presenti corredati da data e protocollo ultimo ins.
    e ultima stampa.
    """
    
    def __init__(self, year=2004, **kwargs):
        
        kwargs['writable'] = False
        
        adb.DbTable.__init__(\
            self,\
            bt.TABNAME_REGIVA,   "regiva", **kwargs)
        
        self.AddJoin(\
            bt.TABNAME_CFGPROGR, "ultins", join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_CFGPROGR, "stareg", join=adb.JOIN_LEFT)
        
        self.AddOrder('IF(regiva.tipo="A",1,IF(regiva.tipo="V",2,3))')
        self.AddOrder('regiva.codice')
        
        #le espressioni di relazione sono date nel seguente metodo
        self.SetYear(year)
        
        self.Get(-1)
    
    def SetYear(self, year):
        """
        Imposta i filtri sulle tabelle di progressivi per numero/data ultimo 
        inserimento e numero/data ultima stampa definitiav del registro.
        L'anno è necessario poiché tali progressivazioni sono distinte per anno.
        """
        for tab in ("ultins", "stareg"):
            self[tab].SetRelation("""regiva.id=%s.key_id AND """\
                                  """(%s.codice='iva_%s' AND %s.keydiff='%d')"""\
                                  % (tab, tab, tab, tab, year))


# ------------------------------------------------------------------------------


class AllegatiCliFor(_PdcMovimMixin):
    """
    Allegati clienti/fornitori.
    DbTable specializzato nella determinazione del mastro contabile di ogni
    sottoconto.  Eventuali selezioni vanno impostate su 'self.mastro', che è
    il DbTable con i movimenti del mastro stesso.
    Struttura da '_PdcMovimMixin'
    pdc
      +--> movcf (contab_b) solo righe con sottoconto cli/for
           +--> moviva - elenco righe iva del sottoconto
    """
    def __init__(self, clifor):
        
        assert clifor in 'CF'
        clifor = clifor.lower()
        
        _PdcMovimMixin.__init__(self)
        self._info.clifor = clifor
        self._info.totali = None
        
        del self.mov
        
        tabanag = [bt.TABNAME_CLIENTI, 
                   bt.TABNAME_FORNIT]['cf'.index(clifor)]
        self.AddJoin(tabanag, 'anag', idLeft='id', idRight='id',
                     join=adb.JOIN_LEFT)
        
        movcf = self.AddJoin(\
            bt.TABNAME_CONTAB_B, "movcf", idLeft="id", idRight="id_pdcpa",\
            join=adb.JOIN_ALL)
        
        moviva = movcf.AddJoin(\
            bt.TABNAME_CONTAB_B, "moviva", idLeft="id_reg", idRight="id_reg",\
            join=adb.JOIN_ALL)
        self.mov = moviva
        
        self._AddMovTables()
        
        iva = moviva.AddJoin(bt.TABNAME_ALIQIVA, "aliqiva")
        
        self.AddGroupOn('pdc.id')
        self.AddFilter("movcf.numriga=1 OR movcf.tipriga='E'")
        self.AddFilter("moviva.tipriga IN ('I', 'E', 'O')")
        self.AddOrder("pdc.descriz")
        for col in range(4):
            name = 'pral%sc%d' % (clifor, col+1)
            field = 'pralc%d' % (col+1)
            self.AddTotalOf("""
             IF(aliqiva.%s=1,moviva.IMPONIB*caus.pralcf,0)
            +IF(aliqiva.%s=2,moviva.IMPOSTA*caus.pralcf,0)
            """ % (2*(name,)), field)
        
        self.Get(-1)
    
    def SetDate(self, data1, data2):
        self.ClearFilters()
        self.AddFilter("tipana.tipo='%s'" % self._info.clifor)
        self.AddFilter("caus.pralcf IN (1,-1)")
        self.AddFilter("reg.datreg>=%s", data1)
        self.AddFilter("reg.datreg<=%s", data2)
        self._info.data1 = data1
        self._info.data2 = data2
    
    def Retrieve(self, *args, **kwargs):
        self._info.totali = [0,0,0,0]
        out = _PdcMovimMixin.Retrieve(self, *args, **kwargs)
        if out:
            self._info.totali = self.GetTotalOf([(self, 'total_pralc%d' % (x+1)) 
                                                 for x in range(4)])
        return out
    
    def GetPICF(self):
        out = None
        try:
            out = self.anag.codfisc
            if not out:
                out = self.anag.piva
        except AttributeError:
            pass
        return out


# ------------------------------------------------------------------------------


class AllegatiRigheIva(adb.DbTable):
    """
    Dettaglio righe iva di un cliente/fornitore
    """
    def __init__(self, clifor, **kwargs):
        
        assert clifor in 'CF'
        clifor = clifor.lower()
        
        kwargs['writable'] = False
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_B, 'movcf', **kwargs)
        
        reg = self.AddJoin(bt.TABNAME_CONTAB_H, 'reg')
        cau = reg.AddJoin(bt.TABNAME_CFGCONTAB, 'caus')
        regiva = reg.AddJoin(bt.TABNAME_REGIVA, 'regiva')
        moviva = self.AddJoin(bt.TABNAME_CONTAB_B, 'moviva',
                              idLeft='id_reg', idRight='id_reg')
        aliq = moviva.AddJoin(bt.TABNAME_ALIQIVA, 'aliqiva')
        
        pral = 'pral%sc%%d' % clifor
        
        for col in range(4):
            name = 'pral%sc%d' % (clifor, col+1)
            field = 'pralc%d' % (col+1)
            self.AddField("""
             IF(aliqiva.%s=1,moviva.IMPONIB*caus.pralcf,0)
            +IF(aliqiva.%s=2,moviva.IMPOSTA*caus.pralcf,0)
            """ % (2*(name,)), field)
        
        self.AddFilter('caus.pralcf IN (1,-1)')
        self.AddFilter('moviva.tipriga="I"')
        
        self.AddOrder('reg.datreg')
        self.AddOrder('regiva.codice')
        self.AddOrder('reg.numiva')
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class PdcQuadPcfCont(adb.DbMem):
    """
    Situazione di sintesi del sottoconto su progressivi dare/avere e totale
    scadenzario.
    Vengono estratti solo i sottoconti dei quali risulta differente il saldo
    contabile rispetto al saldo partite.
    La situazione ideale è avere il recordset vuoto dopo il Retrieve...
    """
    
    def __init__(self):
        adb.DbMem.__init__(self, fields='pdc_id,tipana_tipo,pdc_codice,pdc_descriz,saldocont,saldopcf')
    
    def Retrieve(self, filter=None, par=None):
        #todo: SubDbTable non è ancora in grado di gestire i join ad altre subselect
        #mi appoggio per ora ad una dbtable di memoria, che viene riempita qui
        #dal recordset ottenuto mediante valutazione dell'epressione sql manuale
        if filter is None:
            filter = ''
        else:
            filter = "WHERE %s" % filter
        if par is None: 
            par = []
        cmd = """
SELECT pdc.id, tipana.tipo, pdc.codice, pdc.descriz, ctb.saldocont, paa.saldopcf
FROM pdc
LEFT JOIN (

  #Totalizzazione mastro
  SELECT pdc.id 'pdc_id',
   SUM(IF(   (mastro.segno='D' AND tipana.tipo='C')   OR (mastro.segno='A' AND tipana.tipo='F'),  mastro.importo, 0)
      -IF(   (mastro.segno='D' AND tipana.tipo='C')   OR (mastro.segno='A' AND tipana.tipo='F'), 0,  mastro.importo)) AS saldocont
  FROM contab_b mastro
  JOIN pdc ON mastro.id_pdcpa=pdc.id
  JOIN pdctip AS tipana ON pdc.id_tipo = tipana.id
  WHERE (tipana.tipo IN ('C', 'F')) AND mastro.tipriga IN ('S','C','A')
  GROUP BY pdc.id
) ctb ON pdc.id=ctb.pdc_id 

LEFT JOIN (

  #Totalizzazione partite
  SELECT pdc.id 'pdc_id',
   SUM(pcf.imptot-pcf.imppar) as saldopcf
  FROM pcf
  JOIN pdc ON pcf.id_pdc=pdc.id
  GROUP BY pdc.id
) paa ON pdc.id=paa.pdc_id

JOIN pdctip tipana ON pdc.id_tipo=tipana.id
%s
HAVING (saldocont IS NULL AND saldopcf IS NOT NULL AND saldopcf<>0) OR (saldocont IS NOT NULL AND saldocont<>0 AND saldopcf IS NULL) OR saldocont<>saldopcf
ORDER BY tipana.tipo, pdc.descriz
        """ % filter
        db = adb.db.__database__
        dbcon = db._dbCon
        try:
            c = dbcon.cursor()
            c.execute(cmd, par)
            rs = c.fetchall()
            self.SetRecordset(rs)
            out = True
        except Exception, e:
            db.dbError.description = repr(e.args)
            self._info.db = db
            out = False
        return out


if __name__ == '__main__':
    db = adb.DB()
    db.Connect()
    q = PdcQuadPcfCont()
    if q.Retrieve():
        for x in q:
            print x.tipana_descriz, x.pdc_codice, x.pdc_descriz, x.saldocont, x.saldopcf
    else:
        print q.GetError()


# ------------------------------------------------------------------------------


class QuadReg(adb.DbMem):
    
    def __init__(self):
        
        adb.DbMem.__init__(self, 'reg_id,reg_datreg,cau_codice,cau_descriz,riv_codice,riv_descriz,riv_tipo,reg_datdoc,reg_numdoc,problema')
        
        righe_contab = '"S","C","A"'
        if bt.TIPO_CONTAB == "S":
            righe_contab += ',"I"'
        
        self.specs = []
        self.specs.append(('Quadratura Dare/Avere', """
        SELECT reg.id         as 'reg_id',
               reg.datreg     as 'reg_datreg',
               cau.codice     as 'cau_codice',
               cau.descriz    as 'cau_descriz',
               riv.codice     as 'riv_codice',
               riv.descriz    as 'riv_descriz',
               riv.tipo       as 'riv_tipo',
               reg.datdoc     as 'reg_datdoc',
               reg.numdoc     as 'reg_numdoc',
               "%%(problema)s" as 'problema'
            
        FROM contab_h reg
        
        LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
        LEFT JOIN regiva riv    ON reg.id_regiva=riv.id
        
        WHERE reg.datreg>='%%(datmin)s' AND reg.datreg<='%%(datmax)s'
          AND reg.tipreg in ('S','C','I') AND (SELECT SUM(mov.importo*IF(mov.segno='D',1,IF(mov.segno='A',-1,0)))
                                                 FROM contab_b mov
                                                WHERE mov.id_reg=reg.id AND mov.tipriga IN (%s))<>0
        ORDER BY reg.datreg""" % righe_contab))
        
        self.specs.append(("Congruenza dati scadenze", """
        SELECT reg.id         as 'reg_id',
               reg.datreg     as 'reg_datreg',
               cau.codice     as 'cau_codice',
               cau.descriz    as 'cau_descriz',
               riv.codice     as 'riv_codice',
               riv.descriz    as 'riv_descriz',
               riv.tipo       as 'riv_tipo',
               reg.datdoc     as 'reg_datdoc',
               reg.numdoc     as 'reg_numdoc',
               "%(problema)s" as 'problema',
               
        (SELECT mov.importo*IF(mov.segno=cau.pasegno,1,-1)
           FROM contab_b mov
          WHERE mov.id_reg=reg.id AND mov.numriga=1) as 'totreg',
        
        (SELECT SUM(sca.importo)
           FROM contab_s sca
          WHERE sca.id_reg=reg.id) as 'totsca'
        
        FROM contab_h reg
        LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
        LEFT JOIN regiva riv    ON reg.id_regiva=riv.id
        LEFT JOIN modpag mpa    ON reg.id_modpag=mpa.id
        
        WHERE reg.datreg>='%(datmin)s' AND reg.datreg<='%(datmax)s'
          AND reg.tipreg in ('S','C','I') 
          AND cau.pcf='1' AND cau.pcfscon<>'1' AND cau.pcfimp IN ('1','2')
          AND mpa.id_pdcpi IS NULL
        
        HAVING totreg<>0 AND (totsca IS NULL OR totreg<>totsca)
        
        ORDER BY reg.datreg"""))
        
        self.specs.append(("Congruenza partite", """
        SELECT reg.id         as 'reg_id',
               reg.datreg     as 'reg_datreg',
               cau.codice     as 'cau_codice',
               cau.descriz    as 'cau_descriz',
               riv.codice     as 'riv_codice',
               riv.descriz    as 'riv_descriz',
               riv.tipo       as 'riv_tipo',
               reg.datdoc     as 'reg_datdoc',
               reg.numdoc     as 'reg_numdoc',
               "%(problema)s" as 'problema'
        
        FROM contab_h reg
        LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
        LEFT JOIN regiva riv    ON reg.id_regiva=riv.id
        
        WHERE reg.datreg>='%(datmin)s' AND reg.datreg<='%(datmax)s'
          AND reg.tipreg in ('S','C','I') AND cau.pcf='1' AND cau.pcfscon<>'1' AND cau.pcfimp IN ('1','2')
          AND (SELECT COUNT(sca.id)
                 FROM contab_s sca
                 LEFT JOIN pcf ON sca.id_pcf=pcf.id
                WHERE sca.id_reg=reg.id AND pcf.id IS NULL)>0
        
        ORDER BY reg.datreg"""))
        
        if bt.TIPO_CONTAB == "O":
            self.specs.append(("Congruenza IVA-Dare/Avere", """
            SELECT reg.id         as 'reg_id',
                   reg.datreg     as 'reg_datreg',
                   cau.codice     as 'cau_codice',
                   cau.descriz    as 'cau_descriz',
                   riv.codice     as 'riv_codice',
                   riv.descriz    as 'riv_descriz',
                   riv.tipo       as 'riv_tipo',
                   reg.datdoc     as 'reg_datdoc',
                   reg.numdoc     as 'reg_numdoc',
                   "%(problema)s" as 'problema',
            
            (SELECT SUM(mov.importo*IF(mov.segno=cau.pasegno,-1,1))
               FROM contab_b mov
              WHERE mov.id_reg=reg.id 
                    AND mov.tipriga IN ('S','C','A') 
                    AND mov.numriga>1 
                    AND (mov.solocont IS NULL OR mov.solocont<>1) 
                    AND (mov.ivaman IS NULL OR mov.ivaman<>1)) as 'totdav',
            
            (SELECT SUM(mov.importo)
               FROM contab_b mov
              WHERE mov.id_reg=reg.id AND mov.tipriga IN ('I', 'E', 'O')) as 'totiva'
            
            FROM contab_h reg
            LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
            LEFT JOIN regiva riv    ON reg.id_regiva=riv.id
            
            WHERE reg.datreg>='%(datmin)s' AND reg.datreg<='%(datmax)s'
              AND reg.tipreg='I'
            
            HAVING totdav<>totiva
            
            ORDER BY reg.datreg"""))
        
        if bt.TIPO_CONTAB == "S":
            self.specs.append(("Congruenza IVA-Dare/Avere", """
            SELECT reg.id         as 'reg_id',
                   reg.datreg     as 'reg_datreg',
                   cau.codice     as 'cau_codice',
                   cau.descriz    as 'cau_descriz',
                   riv.codice     as 'riv_codice',
                   riv.descriz    as 'riv_descriz',
                   riv.tipo       as 'riv_tipo',
                   reg.datdoc     as 'reg_datdoc',
                   reg.numdoc     as 'reg_numdoc',
                   "%(problema)s" as 'problema',

            (SELECT SUM(IF(mov.tipriga="I",mov.imponib,IF(mov.tipriga="O",0,mov.importo))*IF(mov.segno=cau.pasegno,-1,1))
               FROM contab_b mov
              WHERE mov.id_reg=reg.id
                    AND mov.tipriga IN ('S','C','I','A')
                    AND mov.numriga>1
                    AND (mov.solocont IS NULL OR mov.solocont<>1)
                    AND (mov.ivaman IS NULL OR mov.ivaman<>1) OR mov.ivaman=1 AND mov.tipriga="I") as 'totdav',

            (SELECT SUM(IF(mov.tipriga="O",0,mov.imponib)+mov.imposta+mov.indeduc)
               FROM contab_b mov
              WHERE mov.id_reg=reg.id AND mov.tipriga IN ('I', 'E', 'O')) as 'totiva'

            FROM contab_h reg
            LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
            LEFT JOIN regiva riv    ON reg.id_regiva=riv.id

            WHERE reg.tipreg='I'

            HAVING totdav<>totiva

            ORDER BY reg.datreg"""))
        
        self.specs.append(("Congruenza sottoconti", """
        SELECT reg.id         as 'reg_id',
               reg.datreg     as 'reg_datreg',
               cau.codice     as 'cau_codice',
               cau.descriz    as 'cau_descriz',
               riv.codice     as 'riv_codice',
               riv.descriz    as 'riv_descriz',
               riv.tipo       as 'riv_tipo',
               reg.datdoc     as 'reg_datdoc',
               reg.numdoc     as 'reg_numdoc',
               "%%(problema)s" as 'problema'
        
        FROM contab_h reg
        LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
        LEFT JOIN regiva riv    ON reg.id_regiva=riv.id
        
        WHERE reg.datreg>='%%(datmin)s' AND reg.datreg<='%%(datmax)s'
          AND (SELECT COUNT(mov.id)
                 FROM contab_b mov
            LEFT JOIN pdc ON mov.id_pdcpa=pdc.id
                WHERE mov.id_reg=reg.id AND mov.tipriga IN (%s) AND pdc.id IS NULL)>0
        
        ORDER BY reg.datreg""" % righe_contab))
        
        self.specs.append(("Congruenza registri IVA", """
        SELECT reg.id         as 'reg_id',
               reg.datreg     as 'reg_datreg',
               cau.codice     as 'cau_codice',
               cau.descriz    as 'cau_descriz',
               riv.codice     as 'riv_codice',
               riv.descriz    as 'riv_descriz',
               riv.tipo       as 'riv_tipo',
               reg.datdoc     as 'reg_datdoc',
               reg.numdoc     as 'reg_numdoc',
               "%%(problema)s" as 'problema'
        
        FROM contab_h reg
        LEFT JOIN cfgcontab cau ON reg.id_caus=cau.id
        LEFT JOIN regiva riv    ON reg.id_regiva=riv.id
        
        WHERE reg.datreg>='%%(datmin)s' AND reg.datreg<='%%(datmax)s'
          AND (SELECT COUNT(mov.id)
                 FROM contab_b mov
            LEFT JOIN pdc ON mov.id_pdcpa=pdc.id
                WHERE mov.id_reg=reg.id AND mov.tipriga IN (%s) AND (cau.id_regiva IS NOT NULL AND reg.id_regiva IS NULL))>0
        
        ORDER BY reg.datreg""" % righe_contab))
    
    def GetCicliCount(self):
        return len(self.specs)
    
    def Retrieve(self, datmin=None, datmax=None, func=None):
        datmin = datmin.strftime('%Y-%m-%d')
        datmax = datmax.strftime('%Y-%m-%d')
        db = adb.db.__database__
        rs = []
        for n, (problema, spec) in enumerate(self.specs):
            if callable(func):
                func(n, problema)
            if not db.Retrieve(spec % locals()):
                raise Exception, db.dbError.description
            if db.rs:
                nc = len(self.GetFieldNames())
                if len(db.rs[0]) == nc:
                    rs += db.rs
                else:
                    rs += map(lambda x: x[:nc], db.rs)
        if rs:
            rs2 = [(x[1], x) for x in rs]
            rs2.sort()
            rs = [x[1] for x in rs2]
        self.SetRecordset(rs)
        return False


# ------------------------------------------------------------------------------


class CtrIvaSeqRis(adb.DbMem):
    
    def __init__(self):
        adb.DbMem.__init__(self, 'caucod,caudes,datreg,datdoc,numdoc,numiva,problema')
        self.Reset()


# ------------------------------------------------------------------------------


class CtrIvaSeqCheck(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_H, 'reg', fields='id,datreg,datdoc,numdoc,numiva')
        self.AddJoin(bt.TABNAME_CFGCONTAB, 'caus', idLeft='id_caus')
        self.AddJoin(bt.TABNAME_REGIVA, 'regiva', idLeft='id_regiva')
        self.AddOrder('reg.numiva')
        self.AddOrder('reg.datreg')
        self.Reset()
    
    def CtrSeq(self, id_regiva):
        
        self.ClearFilters()
        self.AddFilter('regiva.id=%s', id_regiva)
        self.AddFilter('YEAR(reg.datreg)=%s', Env.Azienda.Login.dataElab.year)
        self.Retrieve()
        ris = CtrIvaSeqRis()
        if self.IsEmpty():
            return ris
        
        def CreateNewRis(problema, copyreg=True):
            ris.CreateNewRow()
            if copyreg:
                ris.caucod = reg.caus.codice
                ris.caudes = reg.caus.descriz
                ris.datreg = reg.datreg
                ris.datdoc = reg.datdoc
                ris.numdoc = reg.numdoc
                ris.numiva = reg.numiva
            ris.problema = problema
        
        reg = self
        noprot = reg.regiva.noprot
        lastdat = None
        theoprot = 1
        reg.MoveFirst()
        #evidenzio protocolli nulli
        while (reg.numiva or 0) == 0:
            if noprot:
                msg = 'Registrazione ancora da protocollare'
            else:
                msg = 'Protocollo nullo'
            CreateNewRis(msg)
            if not reg.MoveNext():
                break
        
        #controllo buchi e sequenza temporale
        while True:
            niva = int(reg.numiva or 0)
            if niva != theoprot:
                if niva == theoprot+1:
                    msg = 'Manca protocollo %d' % theoprot
                else:
                    msg = 'Mancano protocolli da %d a %d' % (theoprot, niva-1)
                CreateNewRis(msg, copyreg=False)
            else:
                if lastdat is None:
                    lastdat = reg.datreg
                if reg.datreg<lastdat:
                    msg = 'Protocollo fuori sequenza (data prot.precedente: %s)' % reg.dita(lastdat)
                    CreateNewRis(msg)
            lastdat = reg.datreg
            theoprot += 1
            if not reg.MoveNext():
                break
        
        return ris


# ------------------------------------------------------------------------------



class VendAziPriv(adb.DbTable):
    
    def __init__(self, **kwargs):
        
        kwargs['fields'] = None
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_B, 'mov', **kwargs)
        
        mov = self
        reg = self.AddJoin(bt.TABNAME_CONTAB_H, 'reg',       fields=None, idLeft='id_reg')
        riv = reg.AddJoin(bt.TABNAME_REGIVA,    'regiva',    fields=None, idLeft='id_regiva')
        iva = mov.AddJoin(bt.TABNAME_ALIQIVA,   'aliq',      fields=None, idLeft='id_aliqiva')
        mdc = mov.AddJoin(bt.TABNAME_CONTAB_B,  'movpdc',    fields=None, relexpr='movpdc.id_reg=mov.id_reg AND movpdc.numriga=1')
        pdc = mdc.AddJoin(bt.TABNAME_PDC,       'pdc',       fields=None, idLeft='id_pdcpa')
        tpa = pdc.AddJoin(bt.TABNAME_PDCTIP,    'tipana',    fields=None, idLeft='id_tipo')
        cli = pdc.AddJoin(bt.TABNAME_CLIENTI,   'cliente',   fields=None, idLeft='id', idRight='id', join=adb.JOIN_LEFT)
        stc = cli.AddJoin('x4.stati',           'stato_cli', fields=None, idLeft='id_stato', idRight='id', join=adb.JOIN_LEFT)
        frn = pdc.AddJoin(bt.TABNAME_FORNIT,    'fornit',    fields=None, idLeft='id', idRight='id', join=adb.JOIN_LEFT)
        stf = frn.AddJoin('x4.stati',           'stato_for', fields=None, idLeft='id_stato', idRight='id', join=adb.JOIN_LEFT)
        
        AG = self.AddGroupOn
        AG('movpdc.id_pdcpa', 'pdc_id')
        AG('pdc.codice',      'pdc_codice')
        AG('pdc.descriz',     'pdc_descriz')
        AG('IF(tipana.tipo="C", stato_cli.codice, stato_for.codice)', 'anag_stato')
        AG('IF(tipana.tipo="C", cliente.piva,     fornit.piva)',      'anag_piva')
        AG('IF(tipana.tipo="C", cliente.codfisc,  fornit.codfisc)',   'anag_codfisc')
        
        impexpr = 'mov.imponib*IF(mov.segno="A",1,-1)'
        ivaexpr = '(mov.imposta+mov.indeduc)*IF(mov.segno="A",1,-1)'
        privafilt = 'IF(tipana.tipo="C", cliente.piva IS NULL OR cliente.piva="", fornit.piva IS NULL OR fornit.piva="")'
        pivitfilt = 'IF(tipana.tipo="C", stato_cli.codice="IT", stato_for.codice="IT")'
        pivcefilt = 'IF(tipana.tipo="C", stato_cli.is_cee=1 AND stato_cli.codice<>"IT", stato_for.is_cee=1 AND stato_for.codice<>"IT")'
        ivanull = '(aliq.perciva=0 OR aliq.perciva IS NULL)'
        pivestfilt = '(IF(tipana.tipo="C", stato_cli.codice != "IT", stato_for.codice != "IT") AND NOT %(pivcefilt)s)' % locals()
        
        #privati
        self.AddTotalOf('IF(NOT %(ivanull)s AND     %(privafilt)s, %(impexpr)s, 0)' % locals(),                       'imponib_priv')
        self.AddTotalOf('IF(NOT %(ivanull)s AND     %(privafilt)s, %(ivaexpr)s, 0)' % locals(),                       'imposta_priv')
        self.AddTotalOf('IF(    %(ivanull)s AND     %(privafilt)s, %(impexpr)s, 0)' % locals(),                       'noimpes_priv')
        
        #aziende italia
        self.AddTotalOf('IF(NOT %(ivanull)s AND NOT %(privafilt)s AND %(pivitfilt)s, %(impexpr)s, 0)' % locals(),     'imponib_aziita')
        self.AddTotalOf('IF(NOT %(ivanull)s AND NOT %(privafilt)s AND %(pivitfilt)s, %(ivaexpr)s, 0)' % locals(),     'imposta_aziita')
        self.AddTotalOf('IF(    %(ivanull)s AND NOT %(privafilt)s AND %(pivitfilt)s, %(impexpr)s, 0)' % locals(),     'noimpes_aziita')
        
        #aziende cee
        self.AddTotalOf('IF(NOT %(ivanull)s AND NOT %(privafilt)s AND     %(pivcefilt)s, %(impexpr)s, 0)' % locals(), 'imponib_azicee')
        self.AddTotalOf('IF(NOT %(ivanull)s AND NOT %(privafilt)s AND     %(pivcefilt)s, %(ivaexpr)s, 0)' % locals(), 'imposta_azicee')
        self.AddTotalOf('IF(    %(ivanull)s AND NOT %(privafilt)s AND     %(pivcefilt)s, %(impexpr)s, 0)' % locals(), 'noimpes_azicee')
        
        #soggetti fuori cee
        self.AddTotalOf('IF(NOT %(ivanull)s AND %(pivestfilt)s, %(impexpr)s, 0)' % locals(), 'imponib_estero')
        self.AddTotalOf('IF(NOT %(ivanull)s AND %(pivestfilt)s, %(ivaexpr)s, 0)' % locals(), 'imposta_estero')
        self.AddTotalOf('IF(    %(ivanull)s AND %(pivestfilt)s, %(impexpr)s, 0)' % locals(), 'noimpes_estero')
        
        self.AddBaseFilter('mov.tipriga IN ("I", "E", "O") AND regiva.tipo IN ("V", "C")')
        
        self.AddOrder('pdc.descriz')
        
        self._info.colpriv =\
        self._info.colaziita =\
        self._info.colazicee =\
        self._info.colestero = None
        
        self.Reset()
    
    def SetSpecs(self, priv=False, aziita=False, azicee=False, estero=False):
        self._info.colpriv =   priv
        self._info.colaziita = aziita
        self._info.colazicee = azicee
        self._info.colestero = estero
        
    def _Get_Specs(self):
        i = self._info
        return [['Privati',     i.colpriv,   self.total_imponib_priv,   self.total_imposta_priv,   self.total_noimpes_priv],
                ['Aziende ITA', i.colaziita, self.total_imponib_aziita, self.total_imposta_aziita, self.total_noimpes_aziita],
                ['Aziende CEE', i.colazicee, self.total_imponib_azicee, self.total_imposta_azicee, self.total_noimpes_azicee],
                ['Fuori CEE',   i.colestero, self.total_imponib_estero, self.total_imposta_estero, self.total_noimpes_estero],]
        
    def GetColumnTitle(self, n):
        t = []
        s = self._Get_Specs()
        for desc, do, _, _, _ in s:
            if do:
                t.append(desc)
        while len(t)<len(s):
            t.append('')
        return t[n]
    
    def GetColumnImponib(self, n):
        v = []
        s = self._Get_Specs()
        for _, do, totimp, _, _ in s:
            if do:
                v.append(totimp)
        while len(v)<4:
            v.append(0)
        return v[n]
    
    def GetColumnImposta(self, n):
        v = []
        s = self._Get_Specs()
        for _, do, _, totiva, _ in s:
            if do:
                v.append(totiva)
        while len(v)<4:
            v.append(0)
        return v[n]
    
    def GetColumnNoImpEs(self, n):
        v = []
        s = self._Get_Specs()
        for _, do, _, _, totnie in s:
            if do:
                v.append(totnie)
        while len(v)<4:
            v.append(0)
        return v[n]


# ------------------------------------------------------------------------------


class SendedEmail(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_DOCSEMAIL, 'emails', fields='id,id_pdc,id_doc,datsend,oggetto')
        doc = self.AddJoin(bt.TABNAME_MOVMAG_H, 'doc', idLeft='id_doc')
        tpd = doc.AddJoin(bt.TABNAME_CFGMAGDOC, 'tipdoc', idLeft='id_tipdoc')
        pdc = self.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id_pdc')
#        cli = pdc.AddJoin(bt.TABNAME_CLIENTI, 'anag', idLeft='id')
        self.AddOrder('emails.datsend', adb.ORDER_DESCENDING)
        self.Reset()


# ------------------------------------------------------------------------------


class FatturatoContabileClienti(adb.DbTable):
    
    clifor = "C"
    
    def __init__(self, **kwargs):
        
        kwargs['fields'] = None
        detail = kwargs.pop('detail', False)
        
        adb.DbTable.__init__(self, bt.TABNAME_CONTAB_B, 'mov', **kwargs)
        
        mov = self
        reg = mov.AddJoin(bt.TABNAME_CONTAB_H, 'reg',       fields=None, idLeft='id_reg')
        riv = reg.AddJoin(bt.TABNAME_REGIVA,   'regiva',    fields=None, idLeft='id_regiva')
        iva = mov.AddJoin(bt.TABNAME_ALIQIVA,  'aliq',      fields=None, idLeft='id_aliqiva')
        mdc = mov.AddJoin(bt.TABNAME_CONTAB_B, 'movpdc',    fields=None, relexpr='movpdc.id_reg=mov.id_reg AND movpdc.numriga=1')
        pdc = mdc.AddJoin(bt.TABNAME_PDC,      'pdc',       fields=None, idLeft='id_pdcpa')
        tpa = pdc.AddJoin(bt.TABNAME_PDCTIP,   'tipana',    fields=None, idLeft='id_tipo')
        cli = pdc.AddJoin(bt.TABNAME_CLIENTI,  'cliente',   fields=None, idLeft='id', idRight='id', join=adb.JOIN_LEFT)
        stc = cli.AddJoin('x4.stati',          'stato_cli', fields=None, idLeft='id_stato', idRight='id', join=adb.JOIN_LEFT)
        frn = pdc.AddJoin(bt.TABNAME_FORNIT,   'fornit',    fields=None, idLeft='id', idRight='id', join=adb.JOIN_LEFT)
        stf = frn.AddJoin('x4.stati',          'stato_for', fields=None, idLeft='id_stato', idRight='id', join=adb.JOIN_LEFT)
        
        if detail:
            AG = AT = self.AddField
            tp = 'total_'
        else:
            AG = self.AddGroupOn
            AT = self.AddTotalOf
            tp = ''
        
        AG('movpdc.id_pdcpa', 'pdc_id')
        AG('pdc.codice',      'pdc_codice')
        AG('pdc.descriz',     'pdc_descriz')
        AG('IF(tipana.tipo="C", stato_cli.codice,         stato_for.codice)',         'anag_stato')
        AG('IF(tipana.tipo="C", cliente.piva,             fornit.piva)',              'anag_piva')
        AG('IF(tipana.tipo="C", cliente.codfisc,          fornit.codfisc)',           'anag_codfisc')
        AG('IF(tipana.tipo="C", stato_cli.is_cee,         stato_for.is_cee)',         'anag_statocee')
        AG('IF(tipana.tipo="C", stato_cli.is_blacklisted, stato_for.is_blacklisted)', 'anag_statobl')
        AG('IF(tipana.tipo="C", cliente.is_blacklisted,   fornit.is_blacklisted)',    'anag_anagbl')
        
        if detail:
            reg.AddJoin(bt.TABNAME_CFGCONTAB, 'caus', fields=None, idLeft='id_caus', idRight='id', join=adb.JOIN_LEFT)
            AG('reg.id', 'reg_id')
            AG('reg.datreg', 'reg_datreg')
            AG('reg.datdoc', 'reg_datdoc')
            AG('reg.numdoc', 'reg_numdoc')
            AG('caus.codice', 'cau_codice')
            AG('caus.descriz', 'cau_descriz')
            AG('aliq.codice', 'aliq_codice')
            AG('aliq.descriz', 'aliq_descriz')
        
        if self.clifor == "C":
            segno = 'A'
            riflt = 'regiva.tipo IN ("V", "C")'
        else:
            segno = 'D'
            riflt = 'regiva.tipo="A"'
        
        AT('IF(aliq.modo="I", mov.imponib*IF(mov.segno="%(segno)s",1,-1), 0)' % locals(), '%simponibile'%tp)
        AT('IF(aliq.modo="N", mov.imponib*IF(mov.segno="%(segno)s",1,-1), 0)' % locals(), '%snonimponib'%tp)
        AT('IF(aliq.modo="E", mov.imponib*IF(mov.segno="%(segno)s",1,-1), 0)' % locals(), '%sesente_iva'%tp)
        AT('IF(aliq.modo="F", mov.imponib*IF(mov.segno="%(segno)s",1,-1), 0)' % locals(), '%sfuoricampo'%tp)
        AT('mov.imponib*IF(mov.segno="%(segno)s",1,-1)' % locals(),                       '%soperazioni'%tp)
        AT('(mov.imposta+mov.indeduc)*IF(mov.segno="%(segno)s",1,-1)' % locals(),         '%simpostaiva'%tp)
        
        self.AddBaseFilter(riflt)
        self.AddBaseFilter('mov.tipriga IN ("I", "E", "O")')
        
        self.AddOrder('pdc.descriz')
        self.AddOrder('reg.datreg')
        self.AddOrder('reg.id')
        self.AddOrder('mov.numriga')
        
        self.Reset()
    
    def GetTitlePrint(self):
        t = 'Fatturato '
        if self.clifor == "C":
            t += 'Vendite'
        else:
            t += 'Acquisti'
        return t


# ------------------------------------------------------------------------------


class FatturatoContabileFornitori(FatturatoContabileClienti):
    
    clifor = "F"


# ------------------------------------------------------------------------------


class Spesometro2011_AcquistiVendite(adb.DbMem):
    
    def __init__(self):
        
        f = 'Reg_Id Reg_Rif Reg_Link RegIva_Id RegIva_Cod RegIva_Descriz RegIva_Tipo'
        f += ' Anag_Id Anag_Cod Anag_Descriz Anag_AziPer Anag_CodFisc Anag_Nazione Anag_Citta Anag_Indirizzo Anag_StatUnico Anag_PIVA Anag_AllegCF'
        f += ' Anag_Cognome Anag_Nome Anag_NascDat Anag_NascPrv Anag_NascCom Anag_SedeInd Anag_SedeCit Anag_SedeStt Anag_Associa'
        f += ' Reg_Data Cau_Id Cau_Cod Cau_Descriz Reg_NumDoc Reg_DatDoc Reg_NumIva'
        f += ' Totale_DAV DAV_Merce DAV_Servizi DAV_Altro'
        f += ' IVA_AllImpo IVA_Imponib IVA_Imposta IVA_Totale IVA_NonImponib IVA_Esente IVA_FuoriCampo'
        f += ' selected'
        
        #quadro FA - dati x attività
        f += ' fa_att_cnt fa_att_tot fa_att_iva fa_att_ine fa_att_var fa_att_viv'
        #quadro FA - dati x passività
        f += ' fa_pas_cnt fa_pas_tot fa_pas_iva fa_pas_ine fa_pas_var fa_pas_viv'
        
        #quadro BL - dati x attività
        f += ' bl_att_cnt bl_att_tot bl_att_iva'
        #quadro BL - dati x passività
        f += ' bl_pas_cnt bl_pas_tot bl_pas_iva'
        
        #quadro SA - dati x attività
        f += ' sa_att_cnt sa_att_tot'
        
        adb.DbMem.__init__(self, f.replace(' ', ','))
        
        self.Reset()
        self._anno = None
        self._max_azi = None
        self._max_pri = None
    
    def GetData(self, param_list, solo_anag_all=True, solo_caus_all=True, 
                escludi_bl_anag=True, escludi_bl_stato=True):
        p = self.MakeFiltersDict(param_list)
        filters = []
        AF = filters.append
        AF('bodyanag.numriga=1')
        AF('aliq.sm11_no IS NULL OR aliq.sm11_no != 1')
        if p['acqvencor'] == "A":
            AF('regiva.tipo="A"')
            anacf = bt.TABNAME_FORNIT
        else:
            if p['acqvencor'] == "V":
                AF('regiva.tipo="V"')
            elif p['acqvencor'] == "C":
                AF('regiva.tipo="C"')
            anacf = bt.TABNAME_CLIENTI
        AF('reg.datreg>="%s"' % p['data1'])
        AF('reg.datreg<="%s"' % p['data2'])
        self._anno = p['data1'].year
        if solo_anag_all:
            AF('IF(tipana.tipo="C", anagcli.allegcf=1, anagfor.allegcf=1)')
        if solo_caus_all:
            AF('causale.pralcf IN (1, -1)')
        if escludi_bl_anag:
            AF('IF(tipana.tipo="C", anagcli.is_blacklisted IS NULL OR anagcli.is_blacklisted<>1, anagfor.is_blacklisted IS NULL OR anagfor.is_blacklisted<>1)')
        if escludi_bl_stato:
            AF('IF(tipana.tipo="C", statocli.is_blacklisted IS NULL OR statocli.is_blacklisted<>1, statofor.is_blacklisted IS NULL OR statofor.is_blacklisted<>1)')
        filters = ' AND '.join(['(%s)' % f for f in filters])
        if bt.TIPO_CONTAB == 'O':
            righecon = '"C", "S"'
        else:
            righecon = '"C", "S", "I"'
        cmd = """
SELECT reg.id              'Reg_Id', 
       reg.sm_regrif       'Reg_Rif',
       reg.sm_link         'Reg_Link',
       regiva.id           'RegIva_Id',
       regiva.codice       'RegIva_Cod',
       regiva.descriz      'RegIva_Descriz',
       regiva.tipo         'RegIva_Tipo',
       anag.id             'Anag_Id',
       anag.codice         'Anag_Cod',
       anag.descriz        'Anag_Descriz',
       IF(tipana.tipo="C", anagcli.aziper,       anagfor.aziper)       'Anag_AziPer',
       IF(tipana.tipo="C", anagcli.codfisc,      anagfor.codfisc)      'Anag_CodFisc',
       IF(tipana.tipo="C", 
          IF(anagcli.nazione IS NULL OR anagcli.nazione="",
             "IT", anagcli.nazione),
          IF(anagfor.nazione IS NULL OR anagfor.nazione="",
             "IT", anagfor.nazione))                                   'Anag_Nazione',
       IF(tipana.tipo="C", anagcli.citta,        anagfor.citta)        'Anag_Citta',
       IF(tipana.tipo="C", anagcli.indirizzo,    anagfor.indirizzo)    'Anag_Indirizzo',
       IF(tipana.tipo="C", statocli.codunico,    statofor.codunico)    'Anag_StatUnico',
       IF(tipana.tipo="C", anagcli.piva,         anagfor.piva)         'Anag_PIVA',
       IF(tipana.tipo="C", anagcli.allegcf,      anagfor.allegcf)      'Anag_AllegCF',
       IF(tipana.tipo="C", anagcli.sm11_cognome, anagfor.sm11_cognome) 'Anag_Cognome',
       IF(tipana.tipo="C", anagcli.sm11_nome,    anagfor.sm11_nome)    'Anag_Nome',
       IF(tipana.tipo="C", anagcli.sm11_nascdat, anagfor.sm11_nascdat) 'Anag_NascDat',
       IF(tipana.tipo="C", anagcli.sm11_nascprv, anagfor.sm11_nascprv) 'Anag_NascPrv',
       IF(tipana.tipo="C", anagcli.sm11_nasccom, anagfor.sm11_nasccom) 'Anag_NascCom',
       IF(tipana.tipo="C", anagcli.sm11_sedeind, anagfor.sm11_sedeind) 'Anag_SedeInd',
       IF(tipana.tipo="C", anagcli.sm11_sedecit, anagfor.sm11_sedecit) 'Anag_SedeCit',
       IF(tipana.tipo="C", anagcli.sm11_sedestt, anagfor.sm11_sedestt) 'Anag_SedeStt',
       IF(tipana.tipo="C", anagcli.sm11_associa, anagfor.sm11_associa) 'Anag_Associa',
       reg.datreg          'Reg_Data',
       causale.id          'Cau_Id',
       causale.codice      'Cau_Cod',
       causale.descriz     'Cau_Descriz',
       reg.numdoc          'Reg_NumDoc',
       reg.datdoc          'Reg_DatDoc',
       reg.numiva          'Reg_NumIva',
       
       SUM(bodycri.importo
           *IF(bodycri.tipriga IN (%(righecon)s), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)) 'Totale_DAV',
           
       SUM(bodycri.importo
           *IF(bodycri.tipriga IN (%(righecon)s), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(pdccer.f_sermer="M" OR bodycri.f_sermer="M", 1, 0))              'DAV_Merce',
           
       SUM(bodycri.importo
           *IF(bodycri.tipriga IN (%(righecon)s), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(pdccer.f_sermer="S" OR bodycri.f_sermer="S", 1, 0))              'DAV_Servizi',
           
       SUM(bodycri.importo
           *IF(bodycri.tipriga IN (%(righecon)s), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(    pdccer.f_sermer IN ("M", "S") 
               OR bodycri.f_sermer IN ("M", "S"), 0, 1))                        'DAV_Altro',
       
       SUM(bodycri.imponib
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)) 'IVA_AllImpo',
           
       SUM(bodycri.imponib
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(aliq.modo="I",1,0))                                              'IVA_Imponib',
       
       SUM(bodycri.imposta
           *IF(bodycri.tipriga IN ("I", "O"), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(aliq.modo="I",1,0))                                              'IVA_Imposta',
           
       SUM((bodycri.imponib+bodycri.imposta+bodycri.indeduc)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)) 'IVA_Totale',
           
       SUM(bodycri.imponib
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(aliq.modo="N",1,0))                                              'IVA_NonImponib',
           
       SUM(bodycri.imponib
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(aliq.modo="E",1,0))                                              'IVA_Esente',
           
       SUM(bodycri.imponib
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, -1)
           *IF(aliq.modo="F",1,0))                                              'IVA_FuoriCampo',
       
       0                                                                        'selected',
       
       SUM(1
           *IF((regiva.tipo="V" AND causale.pralcf= 1)
             OR(regiva.tipo="A" AND causale.pralcf=-1), 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0))                                      'fa_att_cnt',
       
       SUM(bodycri.imponib
           *causale.pralcf
           *IF(regiva.tipo="V", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(reg.tipreg="E",0,
               IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0)))  'fa_att_tot',
       
       SUM((bodycri.imposta+IF(bodycri.indeduc IS NULL, 0, bodycri.indeduc))
           *causale.pralcf
           *IF(regiva.tipo="V", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga IN ("I", "O"), 1, 0)
           *IF(reg.tipreg="E",1,
               IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0)))  'fa_att_iva',
       
       0                                                                        'fa_att_ine',
       
       SUM(bodycri.imponib
           *IF(causale.pralcf=-1, 1, 0)
           *IF(regiva.tipo="A", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 0, 1))  'fa_att_vim',
       
       SUM((bodycri.imposta+IF(bodycri.indeduc IS NULL, 0, bodycri.indeduc))
           *IF(causale.pralcf=-1, 1, 0)
           *IF(regiva.tipo="A", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 0, 1))  'fa_att_viv',
       
       SUM(1
           *IF((regiva.tipo="A" AND causale.pralcf= 1)
             OR(regiva.tipo="V" AND causale.pralcf=-1), 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0))                                      'fa_pas_cnt',
       
       SUM(bodycri.imponib
           *causale.pralcf
           *IF(regiva.tipo="A", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'fa_pas_tot',
       
       SUM((bodycri.imposta+IF(bodycri.indeduc IS NULL, 0, bodycri.indeduc))
           *causale.pralcf
           *IF(regiva.tipo="A", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga IN ("I", "O"), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'fa_pas_iva',
       
       0                                                                        'fa_pas_ine',
       
       SUM(bodycri.imponib
           *IF(causale.pralcf=-1, 1, 0)
           *IF(regiva.tipo="V", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 0, 1))  'fa_pas_vim',
       
       SUM((bodycri.imposta+IF(bodycri.indeduc IS NULL, 0, bodycri.indeduc))
           *IF(causale.pralcf=-1, 1, 0)
           *IF(regiva.tipo="V", 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 0, 1))  'fa_pas_viv',
           
       SUM(1
           *IF((regiva.tipo="V" AND causale.pralcf= 1)
             OR(regiva.tipo="A" AND causale.pralcf=-1), 1, 0)
           *IF((tipana.tipo="C" AND statocli.codice != "IT")
             OR(tipana.tipo="F" AND statofor.codice != "IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0))                                      'bl_att_cnt',
       
       SUM(bodycri.imponib
           *causale.pralcf
           *IF(regiva.tipo="V", 1, 0)
           *IF((tipana.tipo="C" AND statocli.codice != "IT")
             OR(tipana.tipo="F" AND statofor.codice != "IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'bl_att_tot',
       
       SUM((bodycri.imposta+IF(bodycri.indeduc IS NULL, 0, bodycri.indeduc))
           *causale.pralcf
           *IF(regiva.tipo="V", 1, 0)
           *IF((tipana.tipo="C" AND statocli.codice != "IT")
             OR(tipana.tipo="F" AND statofor.codice != "IT"), 1, 0)
           *IF(bodycri.tipriga IN ("I", "O"), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'bl_att_iva',
            
       SUM(1
           *IF((regiva.tipo="A" AND causale.pralcf= 1)
             OR(regiva.tipo="V" AND causale.pralcf=-1), 1, 0)
           *IF((tipana.tipo="C" AND statocli.codice != "IT")
             OR(tipana.tipo="F" AND statofor.codice != "IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0))                                      'bl_pas_cnt',
       
       SUM(bodycri.imponib
           *causale.pralcf
           *IF(regiva.tipo="A", 1, 0)
           *IF((tipana.tipo="C" AND statocli.codice != "IT")
             OR(tipana.tipo="F" AND statofor.codice != "IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'bl_pas_tot',
       
       SUM((bodycri.imposta+IF(bodycri.indeduc IS NULL, 0, bodycri.indeduc))
           *causale.pralcf
           *IF(regiva.tipo="A", 1, 0)
           *IF((tipana.tipo="C" AND statocli.codice != "IT")
             OR(tipana.tipo="F" AND statofor.codice != "IT"), 1, 0)
           *IF(bodycri.tipriga IN ("I", "O"), 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'bl_pas_iva',
           
       SUM(1
           *IF((regiva.tipo="C" AND causale.pralcf= 1), 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0))                                      'sa_att_cnt',
       
       SUM(bodycri.importo
           *causale.pralcf
           *IF((regiva.tipo="C" AND causale.pralcf= 1), 1, 0)
           *IF((tipana.tipo="C" AND statocli.id IS NULL or statocli.codice="IT")
             OR(tipana.tipo="F" AND statofor.id IS NULL or statofor.codice="IT"), 1, 0)
           *IF(bodycri.tipriga="I", 1, 0)
           *IF(CONCAT(regiva.tipo,bodycri.segno) IN ("VA", "CA", "AD"), 1, 0))  'sa_att_tot'

FROM contab_b bodyanag

INNER JOIN pdc       anag    ON anag.id=bodyanag.id_pdcpa
INNER JOIN pdctip    tipana  ON tipana.id=anag.id_tipo
 LEFT JOIN clienti   anagcli ON anagcli.id=anag.id
 LEFT JOIN fornit    anagfor ON anagfor.id=anag.id

 LEFT JOIN x4.stati  statocli ON statocli.id=anagcli.id_stato
 LEFT JOIN x4.stati  statofor ON statofor.id=anagcli.id_stato

INNER JOIN contab_h  reg     ON reg.id=bodyanag.id_reg
INNER JOIN           regiva  ON regiva.id=reg.id_regiva
INNER JOIN cfgcontab causale ON causale.id=reg.id_caus

INNER JOIN contab_b  bodycri ON bodycri.id_reg=bodyanag.id_reg AND (reg.tipreg="E" OR bodycri.numriga>1)
INNER JOIN pdc       pdccer  ON pdccer.id=bodycri.id_pdcpa

 LEFT JOIN aliqiva   aliq    ON aliq.id=bodycri.id_aliqiva

WHERE %(filters)s

GROUP BY anag.descriz, reg.datdoc, reg.numdoc, regiva.tipo, regiva.codice
ORDER BY anag.descriz, reg.datdoc, reg.numdoc, regiva.tipo, regiva.codice
        """ % locals()
#         print cmd
        db = adb.db.__database__
        if not db.Retrieve(cmd):
            raise Exception, repr(db.dbError.description)
        self.SetRecordset(db.rs)
        
        return True
    
    # info
    
    def Chiedi_QualiRigheSonoSelezionate(self):
        righe = []
        for det in self:
            if det.selected:
                righe.append(det.RowNumber())
        return righe
    
    def Chiedi_QualiChiaviCiSonoNelleRighe(self, righe_sel, even_none=False):
        keys = []
        for row in righe_sel:
            self.MoveRow(row)
            if (self.Reg_Link is not None or even_none) and not self.Reg_Link in keys:
                keys.append(self.Reg_Link)
        return keys
    
    def Chiedi_QuanteChiaviCiSonoNelleRighe(self, righe_sel):
        return len(self.Chiedi_QualiChiaviCiSonoNelleRighe(righe_sel))
    
    def Chiedi_CiSonoChiaviNelleRighe(self, righe_sel):
        return self.Chiedi_QuanteChiaviCiSonoNelleRighe(righe_sel) > 0
    
    def Chiedi_CiSonoPiuChiaviNelleRighe(self, righe_sel):
        return self.Chiedi_QuanteChiaviCiSonoNelleRighe(righe_sel) > 1
    
    def Chiedi_CeUnaSolaChiaveNelleRighe(self, righe_sel):
        return self.Chiedi_QuanteChiaviCiSonoNelleRighe(righe_sel) == 1
    
    def Chiedi_MancanoChiaviNelleRighe(self, righe_sel):
        return None in self.Chiedi_QualiChiaviCiSonoNelleRighe(righe_sel, even_none=True)
    
    def Chiedi_NuovaChiave(self):
        tab_name = bt.TABNAME_CONTAB_H
        cmd = """SELECT MAX(sm_link) FROM %(tab_name)s""" % locals()
        db = adb.db.__database__
        db.Retrieve(cmd)
        if len(db.rs) == 0:
            key = 1
        else:
            key = (db.rs[0][0] or 0) + 1
        return key
    
    def Chiedi_MassimaliAnno(self, anno):
        mass = Spesometro2011_Massimali()
        self._max_azi, self._max_pri = mass.Chiedi_PrendiMassimaliPerLAnno(anno)
        return self._max_azi, self._max_pri
    
    def Chiedi_NuovoRecordsetDaMassimali(self, anno, maxazi=None, maxpri=None):
        
        if maxazi is not None and maxpri is not None:
            self._max_azi = maxazi
            self._max_pri = maxpri
        else:
            mass = Spesometro2011_Massimali()
            maxazi, maxpri = mass.Chiedi_PrendiMassimaliPerLAnno(anno)
            self._max_azi, self._max_pri = maxazi, maxpri
        
        colkey = self._GetFieldIndex('Reg_Link')
        colapr = self._GetFieldIndex('Anag_AziPer')
        colimp = self._GetFieldIndex('IVA_AllImpo') #sommatoria di imponibile, non imp, esente, fuori campo
        coltot = self._GetFieldIndex('IVA_Totale')  #sommatoria di cui sopra più l'imposta
        fields = 'DAV_Merce DAV_Servizi DAV_Altro IVA_Imponib IVA_NonImponib IVA_Esente IVA_FuoriCampo'.split()
        columns = [self._GetFieldIndex(field)
                   for field in fields]
        
        first_row_of_links = None
        
        rs1 = self.GetRecordset()
        rs2 = []
        
        def TestImporti(row, first_row_of_links):
            try:
                link = rs1[row][colkey]
                azip = rs1[row][colapr]
                if link is None:
                    totimp = rs1[row][colimp]
                    tottot = rs1[row][coltot]
                else:
                    totimp = tottot = 0
                    if first_row_of_links is None:
                        first_row_of_links = row
                    row_test = first_row_of_links
                    while True:
                        totimp += (rs1[row_test][colimp] or 0)
                        tottot += (rs1[row_test][coltot] or 0)
                        if row_test == self.RowsCount()-1:
                            break
                        if row_test <= self.RowsCount()-2 and rs1[row_test+1][colkey] != link:
                            break
                        row_test += 1
                if azip == "A":
                    return totimp > maxazi and totimp != 0, first_row_of_links
                return tottot > maxpri and tottot != 0, first_row_of_links
            except Exception, e:
                pass
        
        lastkey = None
        for n, r in enumerate(rs1):
            key =  r[colkey]
            if key is None or key != lastkey:
                first_row_of_links = None
            add, first_row_of_links = TestImporti(n, first_row_of_links)
            if add:
                rs2.append(r)
            lastkey = key
        
        return rs2
    
    # modifica dati
    
    def Esegui_SelezionaRighePdc(self, id_pdc, seleziona=1):
        colid = self._GetFieldIndex('Anag_Id')
        row = self.LocateRS(lambda r: r[colid] == id_pdc)
        if row is not None:
            self.MoveRow(row)
            while self.Anag_Id == id_pdc:
                self.selected = seleziona
                self.MoveNext()
    
    def Esegui_DeselezionaRighePdc(self, id_pdc):
        self.Esegui_SelezionaRighePdc(id_pdc, seleziona=0)
    
    def Esegui_AbbinaRighe(self, righe_sel):
        keys = self.Chiedi_QualiChiaviCiSonoNelleRighe(righe_sel)
        if len(keys) == 0:
            key = self.Chiedi_NuovaChiave()
        else:
            key = keys[0]
        db = adb.db.__database__
        tab_name = bt.TABNAME_CONTAB_H
        for row in righe_sel:
            self.MoveRow(row)
            if self.Reg_Link != key:
                self.Reg_Link = sm_link = key
                reg_id = self.Reg_Id
                cmd = """UPDATE %(tab_name)s SET sm_link=%(sm_link)s WHERE id=%(reg_id)s""" % locals()
                db.Execute(cmd)
    
    def Esegui_ResettaChiaviNelleRighe(self, righe_sel):
        db = adb.db.__database__
        tab_name = bt.TABNAME_CONTAB_H
        for row in righe_sel:
            self.MoveRow(row)
            if self.Reg_Link is not None:
                sm_link = self.Reg_Link
                self.Reg_Link = None
                reg_id = self.Reg_Id
                cmd = """UPDATE %(tab_name)s SET sm_link=NULL, sm_regrif=NULL WHERE sm_link=%(sm_link)s""" % locals()
                db.Execute(cmd)
    
    def Esegui_SetMainReg(self):
        db = adb.db.__database__
        tab_name = bt.TABNAME_CONTAB_H
        sm_link = self.Reg_Link
        self.Reg_Link = None
        reg_id = self.Reg_Id
        cmd = """UPDATE %(tab_name)s SET sm_regrif=2 WHERE sm_link=%(sm_link)s""" % locals()
        db.Execute(cmd)
        cmd = """UPDATE %(tab_name)s SET sm_regrif=1 WHERE %(tab_name)s.id=%(reg_id)s""" % locals()
        db.Execute(cmd)
    
    def Esegui_GeneraFile(self, filename):
        
        def Z(num, len):
            return str(num).zfill(len)
        
        def F(val, len):
            val = (val or '').encode('ascii', 'replace').upper()
            return (val+' '*len)[:len]
        
        def D(dat):
            if dat is None:
                return '0'*8
            if type(dat) is str:
                #yyyy-mm-dd
                return dat[-2:]+dat[5:7]+dat[:4]
            return Z(dat.day, 2)+Z(dat.month, 2)+Z(dat.year, 4)
        
        def V(val):
            return abs(int(val))
        
        def get_pagamento(data):
#            if data.Anag_AziPer == "P":
#                #privati
#                if data.IVA_Totale < self._max_pri:
#                    #importo frazionato
#                    return '2'
#                else:
#                    #importo non frazionato
#                    return '1'
#            else:
#                #aziende
#                if data.IVA_AllImpo < self._max_azi:
#                    #importo frazionato
#                    return '2'
#                else:
#                    #importo non frazionato
#                    return '1'
            if data.Reg_Link is None:
                #importo non frazionato
                return '1'
            else:
                #importo frazionato
                return '2'
        
        def get_tipo_operazione(data):
            if data.RegIva_Tipo in 'VC':
                #Cessione e/o prestazione
                return '1'
            #Acquisto e/o prestazione ricevuta
            return '2'
        
        stati = adb.DbTable('x4.stati', 'stato')
        
        def get_stato_sede(data):
            if data.Anag_SedeStt is not None:
                stati.Get(data.Anag_SedeStt)
                return F(stati.codunico, 3)
            return F('', 3)
        
        obb_codfisc = Env.Azienda.codfisc
        obb_piva = Env.Azienda.piva
        obb_ragsoc = Env.Azienda.descrizione
        obb_comune = Env.Azienda.citta
        obb_prov = Env.Azienda.prov
        
        anno = self._anno
        invio_num = 1
        invio_tot = 1
        
        t_imponib = t_imposta = t_totale = numdoc = datdoc = None
        
        def record_testa_piede(tipo_rec):
            row =  tipo_rec             #Tipo Record (0=Testata, 9=Piede)
            row += 'ART21'              #Codice identificativo della fornitura
            row += '47'                 #Codice numerico della fornitura
            row += '0'                  #Tipologia di invio (invio ordinario)
            row += Z(0, 17)             #Protocollo telematico da sostituire o annullare
            row += Z(0, 6)              #Protocollo documento
            row += F(obb_codfisc, 16)   #Codice Fiscale
            row += Z(obb_piva, 11)      #Partita IVA
            row += F(obb_ragsoc, 60)    #Denominazione
            row += F(obb_comune, 40)    #Comune del domicilio fiscale
            row += F(obb_prov, 2)       #Provincia del domicilio fiscale
            row += F('', 24)            #Cognome
            row += F('', 20)            #Nome
            row += ' '                  #Sesso
            row += D(None)              #Data di nascita
            row += F('', 40)            #Comune o Stato estero di nascita
            row += F('', 2)             #Provincia di nascita
            row += Z(anno, 4)           #Anno di riferimento
            row += '0'                  #Comunicazioni dati di società incorporata (Comunicazione riferita esclusivamente al soggetto che comunica)
            row += Z(invio_num, 4)      #Progressivo invio
            row += Z(invio_tot, 4)      #Totale invii
            row += ' '*16               #Codice fiscale dell'intermediario che effettua la trasmissione
            row += Z(0, 5)              #Numero di iscrizione all'albo del C.A.F.
            row += '0'                  #Impegno a trasmettere in via telematica la comunicazione
            row += D(None)              #Data dell'impegno
            row += F('', 1498)          #Filler
            row += 'A'                  #Carattere di controllo
            return row
        
        def record_testa():
            return record_testa_piede('0')
        
        def record_piede():
            return record_testa_piede('9')
        
        def record_residente_azienda(data):
            row =  '2'                          #Tipo Record
            row += F(data.Anag_PIVA, 11)        #Partita IVA
            row += D(datdoc)                    #Data dell'operazione
            row += F(numdoc, 15)                #Numero della Fattura
            row += get_pagamento(data)          #Modalità di pagamento (Frazionato, non frazionato, corrispettivi periodici)
            row += Z(V(t_imponib), 9)           #Importo dovuto (Importo dell'operazione al netto dell'Imposta)
            row += Z(V(t_imposta), 9)           #Imposta
            row += get_tipo_operazione(data)    #Tipologia dell'operazione
            row += F('', 1742)                  #Filler
            row += 'A'                          #Carattere di controllo
            return row
        
        def record_residente_notavariazione(data):
            if data.RegIva_Tipo == "A":
                #note credito ricevuta: per me è un credito
                tipovar = "C"
            else:
                #note credito emessa: per me è un debito
                tipovar = "D"
            piva = data.Anag_PIVA
            codfisc = data.Anag_CodFisc
            if len(piva or '')>0:
                codfisc = ''
            row =  '4'                          #Tipo Record
            row += F(piva, 11)                  #Partita IVA
            row += F(codfisc, 16)               #Codice fiscale
            row += D(datdoc)                    #Data dell'operazione
            row += F(numdoc, 15)                #Numero della Nota di Variazione
            row += Z(V(t_imponib), 9)           #Imponibile della nota di Variazione
            row += Z(V(t_imposta), 9)           #Imposta sul Valore Aggiunto della Nota di Variazione
            row += '3112%s' % anno              #Data della Fattura da rettificare
            row += F('', 15)                    #Numero della Fattura da rettificare
            row += tipovar                      #Variazione dell'imponibile a credito o a debito
            row += tipovar                      #Variazione dell'imposta a credito o a debito
            row += F('', 1703)                  #Filler
            row += 'A'                          #Carattere di controllo
            return row
        
        def record_residente_privato(data):
            row =  '1'                          #Tipo Record
            row += F(data.Anag_CodFisc, 16)     #Codice Fiscale
            row += D(datdoc)                    #Data dell'operazione
            row += get_pagamento(data)          #Modalità di pagamento (Frazionato, non frazionato, corrispettivi periodici)
            row += Z(V(t_importo), 9)            #Importo dovuto
            row += F('', 1762)                  #Filler
            row += 'A'                          #Carattere di controllo
            return row
        
        def record_nonresidente(data):
            row =  '3'                          #Tipo Record
            row += F(data.Anag_Cognome, 24)     #Cognome
            row += F(data.Anag_Nome, 20)        #Nome
            row += D(data.Anag_NascDat)         #Data di nascita
            row += F(data.Anag_NascCom, 40)     #Comune o Stato estero di nascita
            row += F(data.Anag_NascPrv, 2)      #Provincia di nascita
            row += get_stato_sede(data)         #Stato estero del domicilio
            row += F(data.Anag_Descriz, 60)     #Denominazione, Ditta o ragione sociale
            row += F(data.Anag_SedeCit, 40)     #Città estera della sede legale
            row += get_stato_sede(data)         #Stato estero della sede legale
            row += F(data.Anag_SedeInd, 40)     #Indirizzo estero della sede legale
            row += D(datdoc)                    #Data dell'operazione
            row += F(numdoc, 15)                #Numero della Nota di variazione
            row += get_pagamento(data)          #Modalità di pagamento (Frazionato, non frazionato, corrispettivi periodici)
            row += Z(V(t_imponib), 9)           #Importo dovuto (Importo dell'operazione al netto dell'Imposta)
            row += Z(V(t_imposta), 9)           #Imposta
            row += get_tipo_operazione(data)    #Tipologia dell'operazione
            row += F('', 1513)                  #Filler
            row += 'A'                          #Carattere di controllo
            return row
        
        def record_nonresidente_notavariazione(data):
            if data.RegIva_Tipo == "A":
                #note credito ricevuta: per me è un credito
                tipovar = "C"
            else:
                #note credito emessa: per me è un debito
                tipovar = "D"
            row =  '5'                          #Tipo Record
            row += F(data.Anag_Cognome, 24)     #Cognome
            row += F(data.Anag_Nome, 20)        #Nome
            row += D(data.Anag_NascDat)         #Data di nascita
            row += F(data.Anag_NascCom, 40)     #Comune o Stato estero di nascita
            row += F(data.Anag_NascPrv, 2)      #Provincia di nascita
            row += get_stato_sede(data)         #Stato estero del domicilio
            row += F(data.Anag_Descriz, 60)     #Denominazione, Ditta o ragione sociale
            row += F(data.Anag_SedeCit, 40)     #Città estera della sede legale
            row += get_stato_sede(data)         #Stato estero della sede legale
            row += F(data.Anag_SedeInd, 40)     #Indirizzo estero della sede legale
            row += D(datdoc)                    #Data dell'operazione
            row += F(numdoc, 15)                #Numero della Nota di variazione
            row += Z(V(t_imponib), 9)           #Imponibile della nota di Variazione
            row += Z(V(t_imposta), 9)           #Imposta sul Valore Aggiunto della Nota di Variazione
            row += '3112%s' % anno              #Data della Fattura da rettificare
            row += F('', 15)                    #Numero della Fattura da rettificare
            row += tipovar                      #Variazione dell'imponibile a credito o a debito
            row += tipovar                      #Variazione dell'imposta a credito o a debito
            row += F('', 1490)                  #Filler
            row += 'A'                          #Carattere di controllo
            return row
        
        f = open(filename, 'w')
        
        def write_row(row):
            return f.write('%s\n' % row)
        
        #riga 0 - testata
        write_row(record_testa())
        
        last_link = None
        
        for data in self:
            
            if data.Reg_Link is not None and data.Reg_Link == last_link:
                continue
            
            numdoc = data.Reg_NumDoc
            datdoc = data.Reg_DatDoc
            t_imponib = data.IVA_AllImpo
            t_imposta = data.IVA_Imposta
            t_importo = data.IVA_Totale
            
            if data.Reg_Link is not None:
                move_to = data.RowNumber()
                sm_link = data.Reg_Link
                while True:
                    if not data.MoveNext() or data.Reg_Link != sm_link:
                        break
                    t_imponib += (data.IVA_AllImpo or 0)
                    t_imposta += (data.IVA_Imposta or 0)
                    t_importo += (data.IVA_Totale or 0)
                data.MoveRow(move_to)
            
            if (data.Anag_Nazione or "IT") == "IT":
                if t_imponib < 0:
                    row = record_residente_notavariazione(data)
                else:
                    if data.Anag_AziPer == "A":
                        row = record_residente_azienda(data)
                    else:
                        row = record_residente_privato(data)
            else:
                if t_imponib < 0:
                    row = record_nonresidente_notavariazione(data)
                else:
                    row = record_nonresidente(data)
            write_row(row)
            last_link = data.Reg_Link
        
        #riga 9 - piede
        write_row(record_piede())
        
        f.close()
        
        return True


# ------------------------------------------------------------------------------


class Spesometro2011_Massimali(adb.DbTable):
    
    _key = 'spesometro'
    _des = 'Massimali spesometro'
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr')
        self.AddBaseFilter('progr.codice=%s', self._key)
        self.AddOrder('progr.keydiff')
        self.Retrieve()
    
    def CreateNewRow(self):
        adb.DbTable.CreateNewRow(self)
        self.codice = self._key
        self.descriz = self._des
    
    def Chiedi_PrendiMassimaliPerLAnno(self, anno):
        self.Retrieve('progr.keydiff=%s', anno)
        if self.IsEmpty():
            raise Exception, "Massimali non definiti per l'anno %d" % anno
        return self.progrimp1, self.progrimp2


# ------------------------------------------------------------------------------


class CalcIntPcf(adb.DbTable):
    
    _percint = None
    def SetPercInt(self, p):
        self._percint = p
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PCF, 'pcf')
        _pdc = self.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id_pdc')
        _tpa = _pdc.AddJoin(bt.TABNAME_PDCTIP, 'tipana', idLeft='id_tipo')
        _cli = _pdc.AddJoin(bt.TABNAME_CLIENTI, 'anag', idLeft='id')
        _cau = self.AddJoin(bt.TABNAME_CFGCONTAB, 'caus', idLeft='id_caus')
        _mpa = self.AddJoin(bt.TABNAME_MODPAG, 'modpag', idLeft='id_modpag')
        today = Env.DateTime.today()
        self.AddField("pcf.imptot-pcf.imppar", "saldo")
        self.AddField("DATEDIFF(CAST(\"%s\" AS DATE), pcf.datscad)" % today.isoformat(), "ritardo")
        self.AddField("0.0", "interessi")
        self.AddBaseFilter("tipana.tipo=%s", "C")
        self.AddBaseFilter("pcf.datscad<\"%s\"" % today.isoformat())
        self.AddBaseFilter("pcf.imptot>pcf.imppar")
        self.AddOrder('pdc.descriz')
        self.AddOrder('pcf.datscad')
        self.Reset()
    
    def Retrieve(self, *args, **kwargs):
        today = Env.DateTime.today()
        out = adb.DbTable.Retrieve(self, *args, **kwargs)
        if out:
            for _self in self:
#                self.ritardo = (today-self.datscad).days
                if self._percint:
                    self.interessi = round(self.saldo*float(self.ritardo)/365*self._percint/100, 2)
        return out


class DbMemDynamic(adb.DbMem):
    
    _fields = []
    def add_field(self, field, value=None):
        self._fields.append(field)
        return value



import StringIO

class Quadro_00(adb.DbMem):
    
    tipo_record = None
    anno = None
    cf_contr = None
    tipo_com = None
    cod_attiv = None
    period = None
    form_com = None
    
    def __init__(self):
        fields = []; a = fields.append
        a('tipo_record')
        a('anno')
        a('cf_contr')
        a('tipo_com')
        a('cod_attiv')
        a('period')
        a('form_com')
        adb.DbMem.__init__(self, fields=fields)


class Quadro_FA(adb.DbMem):
    """
    Quadro FA
    Acquisti/Vendite con fattura con soggetti italiani
    """
    
    tipo_record = None
    anno = None
    cf_contr = None
    piva_clifor = None
    cf_clifor = None
    doc_riep = None
    opatt_numtot = None
    oppas_numtot = None
    opatt_importo = None
    opatt_imposta = None
    opatt_ivanesp = None
    opatt_notevar = None
    opatt_ivanvar = None
    oppas_importo = None
    oppas_imposta = None
    oppas_ivanesp = None
    oppas_notevar = None
    oppas_ivanvar = None
    
    def __init__(self):
        fields = []; a = fields.append
        a('tipo_record')
        a('anno')
        a('cf_contr')
        a('piva_clifor')
        a('cf_clifor')
        a('doc_riep')
        a('opatt_numtot')
        a('oppas_numtot')
        a('is_noleas')
        a('opatt_importo')
        a('opatt_imposta')
        a('opatt_ivanesp')
        a('opatt_notevar')
        a('opatt_ivanvar')
        a('oppas_importo')
        a('oppas_imposta')
        a('oppas_ivanesp')
        a('oppas_notevar')
        a('oppas_ivanvar')
        adb.DbMem.__init__(self, fields=fields)


class Quadro_BL(adb.DbMem):
    """
    Quadro BL
    Acquisti/Vendite con fattura con soggetti italiani
    """
    
    tipo_record = None
    anno = None
    cf_contr = None
    cognome = None
    nome = None
    data_nasc = None
    comstaest_nasc = None
    provest_nasc = None
    statest_dom = None
    ragsoc = None
    cittaest_sede = None
    statest_sede = None
    indirest_sede = None
    identif_iva = None
    cognome_rap = None
    nome_rap = None
    data_nasc_rap = None
    comstaest_nasc_rap = None
    provest_nasc_rap = None
    statest_dom_rap = None
    opatt_importo = None
    opatt_imposta = None
    oppas_importo = None
    oppas_imposta = None
    
    def __init__(self):
        fields = []; a = fields.append
        a('tipo_record')
        a('anno')
        a('cf_contr')
        a('cognome')
        a('nome')
        a('data_nasc')
        a('comstaest_nasc')
        a('provest_nasc')
        a('statest_dom')
        a('ragsoc')
        a('cittaest_sede')
        a('statest_sede')
        a('indirest_sede')
        a('identif_iva')
        a('cognome_rap')
        a('nome_rap')
        a('data_nasc_rap')
        a('comstaest_nasc_rap')
        a('provest_nasc_rap')
        a('statest_dom_rap')
        a('opatt_importo')
        a('opatt_imposta')
        a('oppas_importo')
        a('oppas_imposta')
        adb.DbMem.__init__(self, fields=fields)


class Quadro_SA(adb.DbMem):
    """
    Quadro SA
    Vendite senza fattura (corrispettivi) a soggetti italiani
    """
    
    tipo_record = None
    anno = None
    cf_contr = None
    cf_clifor = None
    opatt_numtot = None
    opatt_importo = None
    
    def __init__(self):
        fields = []; a = fields.append
        a('tipo_record')
        a('anno')
        a('cf_contr')
        a('cf_clifor')
        a('opatt_numtot')
        a('opatt_importo')
        adb.DbMem.__init__(self, fields=fields)


class Spesometro2013_AcquistiVendite(Spesometro2011_AcquistiVendite):
    
    def Chiedi_NuovoRecordsetDaMassimali(self, anno, maxazi=None, maxpri=None):
        
        if maxazi is not None and maxpri is not None:
            self._max_azi = maxazi
            self._max_pri = maxpri
        else:
            mass = Spesometro2011_Massimali()
            maxazi, maxpri = mass.Chiedi_PrendiMassimaliPerLAnno(anno)
            self._max_azi, self._max_pri = maxazi, maxpri
        
#         colkey = self._GetFieldIndex('Reg_Link')
        coltri = self._GetFieldIndex('RegIva_Tipo')
        colpdc = self._GetFieldIndex('Anag_Id')
        coldes = self._GetFieldIndex('Anag_Descriz')
        colapr = self._GetFieldIndex('Anag_AziPer')
        colriv = self._GetFieldIndex('RegIva_Cod')
        colniv = self._GetFieldIndex('Reg_NumIva')
        colndc = self._GetFieldIndex('Reg_NumDoc')
        colddc = self._GetFieldIndex('Reg_DatDoc')
        colimp = self._GetFieldIndex('IVA_Imponib')    #imponibile
        coliva = self._GetFieldIndex('IVA_Imposta')    #imposta
        colali = self._GetFieldIndex('IVA_AllImpo')    #sommatoria di imponibile, non imp, esente, fuori campo
        coltot = self._GetFieldIndex('IVA_Totale')     #sommatoria di cui sopra più l'imposta
        colnim = self._GetFieldIndex('IVA_NonImponib') #non imponibile
        colese = self._GetFieldIndex('IVA_Esente')     #non esente
        colfci = self._GetFieldIndex('IVA_FuoriCampo') #fuori campo
        colact = self._GetFieldIndex('fa_att_cnt')     #quadro FA op.attive - num. operazioni
        colatt = self._GetFieldIndex('fa_att_tot')     #quadro FA op.attive - totale imponibile, non imponibile, esente
        colaiv = self._GetFieldIndex('fa_att_iva')     #quadro FA op.attive - imposta
        colain = self._GetFieldIndex('fa_att_ine')     #quadro FA op.attive - iva non esposta
        colava = self._GetFieldIndex('fa_att_var')     #quadro FA op.attive - tot.note variazione
        colavi = self._GetFieldIndex('fa_att_viv')     #quadro FA op.attive - tot.imposta note variazione
        colpct = self._GetFieldIndex('fa_pas_cnt')     #quadro FA op.passive - num. operazioni
        colptt = self._GetFieldIndex('fa_pas_tot')     #quadro FA op.passive - totale imponibile, non imponibile, esente
        colpiv = self._GetFieldIndex('fa_pas_iva')     #quadro FA op.passive - imposta
        colpin = self._GetFieldIndex('fa_pas_ine')     #quadro FA op.passive - iva non esposta
        colpva = self._GetFieldIndex('fa_pas_var')     #quadro FA op.passive - tot.note variazione
        colpvi = self._GetFieldIndex('fa_pas_viv')     #quadro FA op.passive - tot.imposta note variazione
        colean = self._GetFieldIndex('bl_att_cnt')     #quadro BL op.attive - num. operazioni
        coleat = self._GetFieldIndex('bl_att_tot')     #quadro BL op.attive - totale imponibile, non imponibile, esente
        coleai = self._GetFieldIndex('bl_att_iva')     #quadro BL op.attive - imposta
        colepn = self._GetFieldIndex('bl_pas_cnt')     #quadro BL op.passive - num. operazioni
        colept = self._GetFieldIndex('bl_pas_tot')     #quadro BL op.passive - totale imponibile, non imponibile, esente
        colepi = self._GetFieldIndex('bl_pas_iva')     #quadro BL op.passive - imposta
        colsan = self._GetFieldIndex('sa_att_cnt')     #quadro SA op.attive - num. operazioni
        colsat = self._GetFieldIndex('sa_att_tot')     #quadro SA op.attive - totale imponibile, non imponibile, esente, imposta
        
        def get_key(regiva_tipo, anag_descriz):
#            return '%s-%s' % (regiva_tipo, anag_descriz)
            return anag_descriz
        
        rs1 = self.GetRecordset()
        rs2 = []
        
        _coltot = []
        _coltot.append(colimp)
        _coltot.append(coliva)
        _coltot.append(colali)
        _coltot.append(coltot)
        _coltot.append(colnim)
        _coltot.append(colese)
        _coltot.append(colfci)
        _coltot.append(colatt)
        _coltot.append(colaiv)
        _coltot.append(colain)
        _coltot.append(colava)
        _coltot.append(colavi)
        _coltot.append(colptt)
        _coltot.append(colpiv)
        _coltot.append(colpin)
        _coltot.append(colpva)
        _coltot.append(colpvi)
        _coltot.append(coleat)
        _coltot.append(coleai)
        _coltot.append(colept)
        _coltot.append(colepi)
        _coltot.append(colsat)
        
        lastkey = None
        for _n, r in enumerate(rs1):
            
            if r[colact] == 0 and r[colpct] == 0\
           and r[colean] == 0 and r[colepn] == 0\
           and r[colsat] == 0:
                continue
            
            #test massimali
            if (r[colapr] == "A" and abs(r[colimp]) < maxazi) or (r[colapr] == "P" and r[colsat] < maxpri):
                continue
            
            key = get_key(r[coltri], r[coldes])
            if key != lastkey:
                rs2.append([]+r)
                rs2[-1][coltri] = r[coltri]
                rs2[-1][colriv] = ''
                rs2[-1][colndc] = ''
                rs2[-1][colddc] = None
                rs2[-1][colniv] = 0
                lastkey = key
                
                for ct in _coltot:
                    rs2[-1][ct] = 0
                for ct in (colact, colpct, colean, colepn):
                    rs2[-1][ct] = 0
            
            for ct in _coltot:
                rs2[-1][ct] += (r[ct] or 0)
            for ct in (colact, colpct, colean, colepn):
                if r[ct] > 0:
                    rs2[-1][ct] += 1
                elif r[ct] < 0:
                    rs2[-1][ct] -= 1
        
        return rs2
    
    def genera_file(self, filename):
        
        def fmt_data(data):
            if data:
                return data.strftime('%d%m%Y')
            return ''
        
        def fmt_importo(importo):
            if not importo:
                return ''
            return ('%.2f' % importo).replace('.', ',')
        
        def fmt_string(msg):
            try:
                return (msg or '').encode('ascii', 'replace')
            except:
                return msg or ''
        
        quadri = []
        q_00 = Quadro_00(); quadri.append(q_00)
        q_fa = Quadro_FA(); quadri.append(q_fa)
        q_bl = Quadro_BL(); quadri.append(q_bl)
        q_sa = Quadro_SA(); quadri.append(q_sa)
        
        q_00.CreateNewRow()
        q_00.tipo_record = "B"
        q_00.anno = self._anno
        q_00.cf_contr = Env.Azienda.codfisc
        q_00.tipo_com = "O"
        q_00.cod_attiv = Env.Azienda.codateco
        
        setup = adb.DbTable('cfgsetup')
        setup.Retrieve('chiave=%s', 'liqiva_periodic')
        q_00.period = setup.flag
        
        q_00.form_com = "2"
        
        for _ in self:
            
            if self.fa_att_cnt != 0 or self.fa_pas_cnt != 0:
                
                #operazione con fattura (acquisto/vendita) soggetti italani
                
                q_fa.CreateNewRow()
                q_fa.tipo_record = "M"
                q_fa.anno = self._anno
                q_fa.cf_contr = Env.Azienda.codfisc
                if len(self.Anag_PIVA or '') > 0 and len(self.Anag_CodFisc or '') > 0:
                    if self.Anag_AziPer == "A":
                        q_fa.piva_clifor = self.Anag_PIVA
                    else:
                        q_fa.cf_clifor = self.Anag_CodFisc
                else:
                    if len(self.Anag_PIVA or '') > 0:
                        q_fa.piva_clifor = self.Anag_PIVA
                    elif len(self.Anag_CodFisc or '') > 0:
                        q_fa.cf_clifor = self.Anag_CodFisc
                    else:
                        q_fa.doc_riep = "S"
                q_fa.is_noleas = ''
                q_fa.opatt_numtot = str(self.fa_att_cnt)
                q_fa.oppas_numtot = str(self.fa_pas_cnt)
                q_fa.opatt_importo = fmt_importo(self.fa_att_tot)
                q_fa.opatt_imposta = fmt_importo(self.fa_att_iva)
                q_fa.opatt_ivanesp = fmt_importo(self.fa_att_ine)
                q_fa.opatt_notevar = fmt_importo(self.fa_att_var)
                q_fa.opatt_ivanvar = fmt_importo(self.fa_att_viv)
                q_fa.oppas_importo = fmt_importo(self.fa_pas_tot)
                q_fa.oppas_imposta = fmt_importo(self.fa_pas_iva)
                q_fa.oppas_ivanesp = fmt_importo(self.fa_pas_ine)
                q_fa.oppas_notevar = fmt_importo(self.fa_pas_var)
                q_fa.oppas_ivanvar = fmt_importo(self.fa_pas_viv)
            
            elif self.bl_att_cnt != 0 or self.bl_pas_cnt != 0:
                
                #operazione con fattura (acquisto/vendita) soggetti esteri
                
                q_bl.CreateNewRow()
                q_bl.tipo_record = "O"
                q_bl.anno = self._anno
                q_bl.cf_contr = Env.Azienda.codfisc
                
                if self.Anag_AziPer == "P":
                    q_bl.cognome = self.Anag_Cognome or ''
                    q_bl.nome = self.Anag_Nome or ''
                    if self.Anag_NascDat:
                        q_bl.data_nasc = fmt_data(self.Anag_NascDat)
                    q_bl.comstaest_nasc = fmt_string(self.Anag_NascCom or '')
                    q_bl.provest_nasc = fmt_string(self.Anag_NascPrv or '')
                    if q_bl.cognome:
                        q_bl.statest_dom = fmt_string(self.Anag_StatUnico)
                
                q_bl.ragsoc = fmt_string(self.Anag_Descriz)
                q_bl.cittaest_sede = fmt_string(self.Anag_Citta)
                q_bl.statest_sede = fmt_string(self.Anag_StatUnico)
                q_bl.indirest_sede = fmt_string(self.Anag_Indirizzo)
                q_bl.identif_iva = '%s%s' % (self.Anag_Nazione or '', self.Anag_PIVA)
                
                if self.Anag_AziPer == "A":
                    q_bl.cognome_rap = fmt_string(self.Anag_Cognome or '')
                    q_bl.nome_rap = fmt_string(self.Anag_Nome or '')
                    if self.Anag_NascDat:
                        q_bl.data_nasc_rap = fmt_data(self.Anag_NascDat)
                    q_bl.comstaest_nasc_rap = fmt_string(self.Anag_NascCom or '')
                    q_bl.provest_nasc_rap = fmt_string(self.Anag_NascPrv or '')
                    if q_bl.cognome_rap:
                        q_bl.statest_dom_rap = fmt_string(self.Anag_StatUnico)
                
                q_bl.opatt_importo = fmt_importo(self.bl_att_tot)
                q_bl.opatt_imposta = fmt_importo(self.bl_att_iva)
                q_bl.oppas_importo = fmt_importo(self.bl_pas_tot)
                q_bl.oppas_imposta = fmt_importo(self.bl_pas_iva)
        
            elif self.sa_att_cnt != 0:
                
                #operazione senza fattura (vendita con corrispettivo) a soggetti italani
                
                q_sa.CreateNewRow()
                q_sa.tipo_record = "N"
                q_sa.anno = self._anno
                q_sa.cf_contr = Env.Azienda.codfisc
                q_sa.cf_clifor = self.Anag_CodFisc
                
                q_sa.opatt_numtot = str(int(self.sa_att_cnt))
                q_sa.opatt_importo = fmt_importo(self.sa_att_tot)
        
        stream = ''
        for q in quadri:
            h = StringIO.StringIO()
            q.ExportCSV(h, delimiter=';', headings=False)
            stream += h.getvalue()
            h.close()
        
        h = open(filename, 'w')
        try:
            h.write(stream)
        finally:
            h.close()
