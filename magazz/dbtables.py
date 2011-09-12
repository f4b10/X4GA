#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dbtables.py
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
Definizione classi specializzate x gestione magazzino.
"""

import os

import stormdb as adb

import Env
bt = Env.Azienda.BaseTab

from awc.util import ListSearch, MsgDialog

from cfg.cfgmagazz import CfgDocMov
import magazz
import contab.dbtables as dbc
import contab.iva as iva
import anag.dbtables as dba

import mx
import copy

import awc.util as awu


try:
    from custmagazz.defpresco import DefPrezzoSconti
except:
    DefPrezzoSconti = None


class NumProtIvaEsiste(Exception):
    pass


# ------------------------------------------------------------------------------


class SendMailInfo(object):
    
    def __init__(self):
        object.__init__(self)
        self.clear()
    
    def clear(self):
        self.errors = False
        self.request = None
        self.sendfrom = None
        self.sendto = None
        self.message = None
        self.noexemail = False
        self.filename = None


# ------------------------------------------------------------------------------


class DocMag(adb.DbTable,\
             iva.IVA):
    """
    DbTable documenti magazzino.
    Struttura:
    doc: documento
       +--> tipdoc: setup documento
       |       +--> caucon: setup causale contabile associata
       |               +--> regiva: registro iva
       +--> pdc: sottoconto del documento
       +--> modpag: modalità di pagamento del documento
       +--> spese: tipo spese associate al documento
       |       +--> iva: aliquota iva sulle spese
       +--> agente: agente del documento
       +--> zona: zona del documento
       +--> tiplist: listino associato al documento
       +--> valuta: valuta del documento
       |
       +---->> mov: movimenti del documento
                  +--> tipmov: setup movimento
                  |       +--> pdc: sottocoto di collegamento contabile
                  +--> prod: prodotto del movimento
                  |       +---->> list: listini associati al prodotto
                  +--> iva: aliquota iva del movimento        
    """
    def __init__(self, writable=True, **kwargs):
        kwargs['writable'] = writable
        adb.DbTable.__init__(self,\
                             bt.TABNAME_MOVMAG_H,  "doc",\
                             **kwargs)
        
        dbcurs = adb.db.__database__.GetConnection().cursor()
        iva.IVA.__init__(self, dbcurs)
        
        dbtdoc = self.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "config",  idLeft="id_tipdoc")
        
        dbcauc = dbtdoc.AddJoin(\
            bt.TABNAME_CFGCONTAB, "caucon",  idLeft="id_caucg",\
            join=adb.JOIN_LEFT)
        
        dbcauc.AddJoin(\
            bt.TABNAME_REGIVA,    "regiva",\
            join=adb.JOIN_LEFT)
        
        dbcauc.AddMultiJoin(\
            bt.TABNAME_CFGMAGRIV, "magriv",  idLeft="id", idRight="id_caus")
        
        dbpdc = self.AddJoin(\
            bt.TABNAME_PDC,       "pdc",\
            join=adb.JOIN_LEFT)
        
        dbpdc.AddJoin(\
            bt.TABNAME_BILMAS,    "bilmas",\
            join=adb.JOIN_LEFT)
        
        dbpdc.AddJoin(\
            bt.TABNAME_BILCON,    "bilcon",\
            join=adb.JOIN_LEFT)
        
        dbpdc.AddJoin(\
            bt.TABNAME_PDCTIP,    "tipana",  idLeft="id_tipo",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_DESTIN,    "dest",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_BANCF,     "bancf",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_ALIQIVA,   "ivadoc", idLeft="id_aliqiva",\
            join=adb.JOIN_LEFT)
        
        dbspe = self.AddJoin(\
            bt.TABNAME_SPEINC,    "spese",   idLeft="id_speinc",\
            join=adb.JOIN_LEFT)
        self.speinc = dbspe #non togliere questo alias
        
        dbspe.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva",     idLeft="id_aliqiva",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_AGENTI,    "agente",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_ZONE,      "zona",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TIPLIST,   "tiplist",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_VALUTE,    "valuta",\
            join=adb.JOIN_LEFT)
        
        mag = self.AddJoin(\
            bt.TABNAME_MAGAZZ,    "magazz",\
            join=adb.JOIN_LEFT)
        
        mag.AddJoin(\
            bt.TABNAME_PDC,       "magpdc", idLeft='id_pdc', idRight='id',\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TRACAU,    "tracau",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TRACUR,    "tracur",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TRAASP,    "traasp",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TRAPOR,    "trapor",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TRACON,    "tracon",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            bt.TABNAME_TRAVET,    "travet",\
            join=adb.JOIN_LEFT)
        
        dbmov = self.AddMultiJoin(\
            bt.TABNAME_MOVMAG_B,  "mov",     idRight="id_doc",\
            fields=magazz.movfields, writable=writable)
        
        dbtmov = dbmov.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "config",  idLeft="id_tipmov",\
            join=adb.JOIN_LEFT)
        
        dbpdc = dbtmov.AddJoin(\
            bt.TABNAME_PDC,       "movpdc",\
            join=adb.JOIN_LEFT)
        
        dbpdc.AddJoin(\
            bt.TABNAME_BILMAS,    "bilmas",\
            join=adb.JOIN_LEFT)
        
        dbpdc.AddJoin(\
            bt.TABNAME_BILCON,    "bilcon",\
            join=adb.JOIN_LEFT)
        
        dbpdc.AddJoin(\
            bt.TABNAME_BILCON,    "tipana", idLeft="id_tipo",\
            join=adb.JOIN_LEFT)
        
        dbprod = dbmov.AddJoin(\
            bt.TABNAME_PROD,      "prod",\
            join=adb.JOIN_LEFT)
        
        dbaliq = dbmov.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva",     idLeft="id_aliqiva",\
            join=adb.JOIN_LEFT)
        
        dbcat = dbprod.AddJoin(\
            bt.TABNAME_CATART,    "catart",\
            join=adb.JOIN_LEFT)
        
        dbgpr = dbprod.AddJoin(\
            bt.TABNAME_GRUPREZ,   "gruprez",\
            join=adb.JOIN_LEFT)
        
        dbpdccg = dbmov.AddJoin(\
            bt.TABNAME_PDC,       "pdccg",   idLeft="id_pdccg",\
            join=adb.JOIN_LEFT)
        
        dbtlis = dbmov.AddJoin(\
            bt.TABNAME_TIPLIST,   "tiplist", idLeft="id_tiplist",\
            join=adb.JOIN_LEFT)
        
        self.cfgdoc = CfgDocMov()
        self.regcon = dbc.DbRegCon()
        self.updpro = Prodotti()
        self.updlis = adb.DbTable(bt.TABNAME_LISTINI, 'list')
        self.updlis.AddOrder('data')
        self.updlis.Reset()
        self.updgrp = adb.DbTable(bt.TABNAME_GRIGLIE, 'grip')
        self.updgrp.AddOrder('data')
        self.updgrp.Reset()
        
        self.totimponib = 0    #totale imponibile
        self.totimposta = 0    #totale imposta
        self.totimporto = 0    #totale importo documento
        self.perritacc =  0    #percentuale ritenuta d'acconto
        self.comritacc =  0    #percentuale dell'importo su cui calcolare
        self.impritacc =  0    #importo su cui calcolare la ritenuta
        self.totritacc =  0    #importo della ritenuta calcolata
        self.totdare =    0    #totale dare
        self.totmerce =   0    #totale merce
        self.totservi =   0    #totale servizi
        self.tottrasp =   0    #totale trasporto
        self.totspese =   0    #totale spese incasso
        self.totscrip =   0    #totale sconti da ripartire
        self.totscmce =   0    #totale sconti in merce
        self.totomagg =   0    #totale merci in omaggio
        
        i = self._info
        
        i.totiva = [] #totali iva
        i.totpdc = [] #totali per sottoconto di costo/ricavo
        i.totpdx = [] #totali per sottoconto di costo/ricavo, no display (omaggi)
        i.oldtot = 0
        i.oldpag = None
        i.oldana = (None, None)
        i.acqdocacq = [] #altri doc. da segnare come acquisiti
        i.acqdocann = [] #altri doc. da annullare
        i.acqmovann = {} #movimenti di altri doc. da annullare
        #la chiave del dizionario è l'id del documento contenente i movimenti
        #da annullare; il valore è la lista degli id movimento da annullare
        i.tradocdel = [] #documenti generati da eliminare
        i.deleting = False
        i.displayonly = False #evita la ritotalizzazione nel caricamento
        i.pdtreadann = [] #lista id letture pdt da annullare in fase di conf.doc
        i.righep0 = [] #lista dei numeri di riga con prezzo nullo, aggiornata in totalizzazione
        
        DQ = bt.MAGQTA_DECIMALS; q = 'mov.qta'
        DI = bt.VALINT_DECIMALS; v = 'mov.importo'
        
        i.prodpro = {}     #aggiornamento progressivi scheda prodotto
        i.ppkeys = {       #chiavi aggiornamento x storno
            'mag': None,   #magazzino da stornare
            'drg': None,   #data registrazione documento prima della memorizz.
            'ann': False,  #flag documento annullato prima della memorizz.
        }
        i.ppcol = {        #struttura aggiornamento:
            #          valore   valore   numero     espr. da
            #          storno   agg.     decimali   valutare
            'ini':    {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #giacenza iniziale
            'car':    {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #carichi
            'sca':    {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #scarichi
            'iniv':   {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': v}, #valore giacenza iniziale
            'carv':   {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': v}, #valore carichi
            'scav':   {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': v}, #valore scarichi
            'cvccar': {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #carichi c/v clienti
            'cvcsca': {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #scarichi c/v clienti
            'cvfcar': {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #carichi c/v fornitori
            'cvfsca': {'tr': 0, 'tw': 0, 'dec': DQ, 'exp': q}, #scarichi c/v fornitori
        }
        
        #progressivi generali
        i.progr = adb.DbTable(bt.TABNAME_CFGPROGR, "progr", writable=True)
        
        #automatismi
        i.autom = adb.DbTable(bt.TABNAME_CFGAUTOM, "autom", writable=False)
        
        #progressivi car/scar
        i.dbppr = adb.DbTable(bt.TABNAME_PRODPRO,  "ppr")
        
        #promozioni
        i.dbpromo = dba.ProdPromo()
        
        #listini
        i.dblist = adb.DbTable(bt.TABNAME_LISTINI, "list", writable=False)
        i.dblist.AddOrder("list.data", adb.ORDER_DESCENDING)
        
        #griglie prezzi
        i.dbgrip = adb.DbTable(bt.TABNAME_GRIGLIE, 'grip', writable=False)
        i.dbgrip.AddOrder("grip.data", adb.ORDER_DESCENDING)
        
        #sconti cliente/categoria
        i.dbscc = dba.TabScontiCC()
        
        #consultazione scadenzario anagrafica
        i.scadenzario = dbc.PdcSintesiPartite(today=Env.Azienda.Login.dataElab)
        
        #consultazione acconti anagrafica
        i.acconti = PdcTotaleAcconti()
        
        i.lastchiusura = None
        setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable=False)
        if setup.Retrieve('chiave="magdatchi"') and setup.OneRow():
            if setup.data is not None:
                i.lastchiusura = setup.data
        
        auto = i.autom
        
        pdco = None
        if auto.Retrieve("codice=%s", 'magomaggi') and auto.OneRow():
            pdco = auto.aut_id
        i.id_pdc_omaggi = pdco
        
        omar = False
        if auto.Retrieve("codice=%s", 'magomareg') and auto.OneRow():
            omar = (auto.aut_id == 1)
        i.magomareg = omar
        
        i.sendmail_info = SendMailInfo()
        
        i.regsearch = dbc.DbRegCon()
        i.regsearch.AddGroupOn('reg.id_regiva')
        i.regsearch.AddMaximumOf('reg.numiva', 'numiva')
        
        self.AddOrder('doc.datreg')
        self.AddOrder('config.descriz')
        self.AddOrder('doc.datdoc')
        self.AddOrder('doc.numdoc')
        
        self.Get(-1)
    
    def _GetNumDatLimits(self, magid, dreg):
        dbdoc = adb.DbTable(bt.TABNAME_MOVMAG_H, "doc")
        dbdoc.AddJoin(bt.TABNAME_CFGMAGDOC, "tipdoc")
        if self.config.docfam:
            dbdoc.AddFilter("tipdoc.docfam=%s", self.config.docfam)
        else:
            dbdoc.AddFilter("doc.id_tipdoc=%s", self.id_tipdoc)
        dbdoc.AddFilter("doc.id_magazz=%s", magid)
        if dreg is None:
            dreg = Env.Azienda.Login.dataElab
        dbdoc.AddFilter("YEAR(doc.datdoc)=%s", dreg.year)
        dbdoc.Synthetize()
        dbdoc.AddMinimumOf("numdoc")
        dbdoc.AddMinimumOf("datreg")
        dbdoc.AddMaximumOf("numdoc")
        dbdoc.AddMaximumOf("datreg")
        if not dbdoc.Retrieve():
            raise Exception, repr(dbdoc.GetError())
        return dbdoc.min_numdoc, dbdoc.min_datreg, dbdoc.max_numdoc, dbdoc.max_datreg
    
    def DefNumDoc(self, doc=None):
        if doc is None:
            doc = self
        self.DefNumIva(doc=doc)
        cfg = doc.cfgdoc
        if cfg.numdoc == '3':
            doc.numdoc = doc.numiva
        if cfg.numdoc == '1':
            magid = self.id_magazz
            dreg = self.datreg
            numdocmin, datregmin, numdocmax, datregmax = self._GetNumDatLimits(magid, dreg)
            numdocmax = numdocmax or 0
            doc.numdoc = numdocmax+1
            if cfg.numdoc == '3':
                doc.numiva = doc.numdoc
    
    def DefNumIva(self, doc=None):
        if doc is None:
            doc = self
        cfg = doc.cfgdoc
        if cfg.id is None:
            raise Exception, "Configurazione documento nulla"
        tipreg = cfg.caucon.tipo
        if tipreg is None or not tipreg in 'IE':
            return
        if cfg.caucon.regivadyn == 1:
            if cfg.caucon.magriv.Locate(lambda rim: rim.id_magazz == self.id_magazz):
                cfg.caucon.id_regiva = cfg.caucon.magriv.id_regiva
        regiva = cfg.caucon.regiva
        if regiva.id and doc.datreg is not None:
            reg = self._info.regsearch
            reg.ClearFilters()
            reg.AddFilter('reg.id_regiva=%s', regiva.id)
            reg.AddFilter('YEAR(reg.datreg)=%s', doc.datreg.year)
            reg.Retrieve()
            doc.numiva = (reg.max_numiva or 0)+1
    
    def TestNumDoc(self):
        out = True
        if self.id_magazz is None:
            raise Exception, "Indicare il magazzino"
            out = False
        return out
    
    def GetDatiScadenzario(self, info='total_saldo', escludidoc=True):
        out = None
        s = self._info.scadenzario
        s.ClearPcfFilters()
        s.Reset()
        if self.id_pdc:
            if escludidoc:
                f = "sintesi.numdoc<>%s AND sintesi.datdoc<>%s"
                s.AddPcfFilter(f, self.numdoc, self.datdoc)
            if s.Get(self.id_pdc):
                try:
                    out = getattr(s.sintesi, info)
                except:
                    pass
        return out
    
    def DefSconto(self, numsc, mov):
        """
        Determinazione dello sconto di riga.
        """
        scontocol = 'sconto%d' % numsc
        if mov.prod.gruprez.nosconti == 1:
            return getattr(mov, scontocol) or 0, ''
        sconto = getattr(mov, scontocol) or getattr(self, scontocol) or 0
        tipo = ''
        if not sconto and bt.MAGSCOCAT and mov.prod.id_catart is not None:
            #da cliente/categoria, se attivato
            scc = self._info.dbscc
            if scc.Retrieve('scc.id_pdc=%s and scc.id_catart=%s', 
                            self.id_pdc, mov.prod.id_catart):
                if scc.sconto1 or scc.sconto2 or scc.sconto3 or scc.sconto4 or scc.sconto5 or scc.sconto6:
                    sconto = getattr(scc, scontocol) or 0
                    tipo = 'C'
        if not sconto and mov.config.tipsconti == '1': #sconti da prodotto
            sconto = getattr(mov.prod, scontocol) or 0
            tipo = 'P'
        if not sconto and mov.config.tipsconti == '2': #sconti da anagrafica (testata)
            sconto = getattr(self, scontocol) or getattr(mov, scontocol) or 0
            tipo = 'H'
        return sconto, tipo
    
    def DefPrezzoSconti(self, prod=None, cfgmov=None, force_tiplist=None, sconti6=False):
        prezzo = 0
        sc1 = sc2 = sc3 = sc4 = sc5 = sc6 = None
        tipo = None
        if callable(DefPrezzoSconti):
            prezzo, sc1, sc2, sc3, sc4, sc5, sc6 = DefPrezzoSconti(self)
            if prezzo or sc1 or sc2 or sc3 or sc4 or sc5 or sc6:
                if sconti6:
                    return prezzo, 'X', sc1, sc2, sc3, sc4, sc5, sc6
                return prezzo, 'X', sc1, sc2, sc3
        if prod is None:
            prod = self.mov.prod
        if cfgmov is None:
            cfgmov = self.mov.config
        cfg = cfgmov
        if cfg.tipvaluni == '1':
            #scorporo iva su costo acquisto
            sia = (bt.MAGSCORPCOS == '1')
        else:
            #scorporo iva su prezzo vendita
            sia = (bt.MAGSCORPPRE == '1')
        #scorporo iva su documento
        sid = (self.config.scorpiva == '1')
        nosconti = (prod.gruprez.nosconti == 1)
        if cfg.tipvaluni in '2L' and bt.MAGPPROMO:
            prm = self._info.dbpromo
            prm.ClearFilters()
            prm.AddFilter("promo.id_prod=%s", prod.id)
            prm.AddFilter("promo.datmin<=%s", self.datreg)
            prm.AddFilter("promo.datmax>=%s", self.datreg)
            if prm.Retrieve() and prm.RowsCount()>0:
                prezzo = prm.prezzo or 0
                sc1 = prm.sconto1 or 0
                sc2 = prm.sconto2 or 0
                sc3 = prm.sconto3 or 0
                sc4 = prm.sconto4 or 0
                sc5 = prm.sconto5 or 0
                sc6 = prm.sconto6 or 0
                tipo = "P"
        if tipo is None:
            if cfg.tipvaluni in '12L':
                #determinazione prezzo griglia se esistente
                self._info.anag = anag = self.GetAnag()
                grip = self._info.dbgrip
                grip.ClearFilters()
                grip.AddFilter("id_pdc=%s", getattr(anag, 'id_pdcgrp', None) or self.id_pdc)
                grip.AddFilter("id_prod=%s", prod.id)
                if bt.MAGDATGRIP:
                    grip.AddFilter("data<=%s", self.datreg)
                if grip.Retrieve() and grip.RowsCount()>0:
                    prezzo = grip.prezzo or 0
                    sc1 = grip.sconto1 or 0
                    sc2 = grip.sconto2 or 0
                    sc3 = grip.sconto3 or 0
                    sc4 = grip.sconto4 or 0
                    sc5 = grip.sconto5 or 0
                    sc6 = grip.sconto6 or 0
                    if prezzo != 0:
                        tipo = 'G'
        if tipo is None:
            if   cfg.tipvaluni == '1':
                # proposizione costo
                prezzo = prod.costo or 0
                tipo = 'C'
                sia = (bt.MAGSCORPCOS == '1')
            elif cfg.tipvaluni == '2':
                # proposizione prezzo ufficiale
                prezzo = prod.prezzo or 0
                tipo = 'P'
            elif cfg.tipvaluni == "L":
                # proposizione prezzo di listino
                tiplist = adb.DbTable(bt.TABNAME_TIPLIST, 'tiplist')
                tiplist.Reset()
                if force_tiplist is None:
                    if self.mov.id_tiplist is not None:
                        tiplist.Get(self.mov.id_tiplist)
                    elif self.tiplist.id is not None:
                        tiplist.Get(self.tiplist.id)
                else:
                    tiplist.Get(force_tiplist)
                if tiplist.id is not None:
                    list = self._info.dblist
                    list.ClearFilters()
                    list.AddFilter("id_prod=%s", prod.id)
                    if bt.MAGDATLIS:
                        list.AddFilter("data<=%s", self.datreg)
                    if list.Retrieve() and list.RowsCount()>0:
                        prezzo = list.__getattr__("prezzo%s"\
                                                  % tiplist.tipoprezzo) or 0
                        tipo = 'L'
        
        if (tipo or '') in 'PL':
            if cfg.tipsconti == 'X':
                gp = prod.gruprez
                sc1 = gp.prcpresco1
                sc2 = gp.prcpresco2
                sc3 = gp.prcpresco3
                sc4 = gp.prcpresco4
                sc5 = gp.prcpresco5
                sc6 = gp.prcpresco6
        
        #adeguamento del costo/prezzo in funzione dei flag di scoporo dell'iva
        #relativamente all'azienda (scheda prodotto) e al tipo di documento
        if sia != sid:
            if sia: 
                #sul setup dell'azienda è indicato che il prezzo/costo è da 
                #scoporare (è comprensivo di iva), mentre sul documento l'iva
                #deve essere aggiunta: il valore proposto va quindi scorporato
                imponib, imposta, ivato, indeduc =\
                       self.CalcolaIVA(prod.id_aliqiva, ivato=prezzo, decimals=bt.MAGPRE_DECIMALS)
                prezzo = imponib
            else:
                #sul setup dell'azienda è indicato che il prezzo/costo non è da 
                #scoporare (e' al netto di iva), mentre sul documento l'iva
                #deve essere scorporata: il valore proposto va quindi aumentato
                #dell'iva
                imponib, imposta, ivato, indeduc =\
                       self.CalcolaIVA(prod.id_aliqiva, imponib=prezzo, decimals=bt.MAGPRE_DECIMALS)
                prezzo = ivato
        
        #costo/prezzo su anagrafica ivato e documento da scorporare, ma in 
        #testata è specificata un'aliquota di esenzione: il valore proposto
        #va scorporato dall'iva che non deve essere calcolata
        if sia and sid:
            if self.ivadoc.id and not self.ivadoc.perciva:
                imponib, imposta, ivato, indeduc =\
                       self.CalcolaIVA(prod.id_aliqiva, ivato=prezzo, decimals=bt.MAGPRE_DECIMALS)
                prezzo = imponib
        
        if sconti6:
            return (prezzo, tipo, sc1, sc2, sc3, sc4, sc5, sc6)
        
        return (prezzo, tipo, sc1, sc2, sc3)
    
    def DefPrezzoSconti6(self, *args, **kwargs):
        kwargs['sconti6'] = True
        return self.DefPrezzoSconti(*args, **kwargs)
    
    def GetDatoGriglia(self, col):
        grip = self._info.dbgrip
        grip.ClearFilters()
        grip.AddFilter("id_pdc=%s", getattr(self._info.anag, 'id_pdcgrp', None) or self.id_pdc)
        grip.AddFilter("id_prod=%s", self.mov.prod.id)
        if bt.MAGDATGRIP:
            grip.AddFilter("data<=%s", self.datreg)
        if grip.Retrieve() and grip.RowsCount()>0:
            return getattr(grip, col)
        return None
    
    def GetDestinat(self):
        out = ''
        try:
            if getattr(self, 'enable_nocodedes', False):
                ddes = self.nocodedes_descriz
                dind = self.nocodedes_indirizzo
                dcap = self.nocodedes_cap
                dcit = self.nocodedes_citta
                dprv = self.nocodedes_prov
            else:
                d = self.dest
                if d.id is None:
                    ddes = self.pdc.descriz.rstrip()
                    d = self._info.anag
                else:
                    ddes = d.descriz.rstrip()
                dind = d.indirizzo.rstrip()
                dcap = d.cap
                dcit = d.citta
                dprv = d.prov
            out = ddes or ''
            if out:
                out += ' - '
            if dind:
                out += (dind or '')
            if out:
                out += ' - '
            out += (dcap or '')+' '+(dcit or '').rstrip()
            if dprv:
                out += ' ('+(dprv or '')+')'
        except:
            pass
        return out
    
    def Reset(self, *args, **kwargs):
        adb.DbTable.Reset(self, *args, **kwargs)
        self.ResetVars()
    
    def ResetVars(self, *args, **kwargs):
        self.regcon = dbc.DbRegCon()
        self.regcon.CreateNewRow()
        self.totimponib = 0
        self.totimposta = 0
        self.totimporto = 0
        self._info.oldtot = 0
        self._info.oldpag = None
        del self._info.acqdocacq[:]
        del self._info.acqdocann[:]
        self._info.acqmovann.clear()
        del self._info.tradocdel[:]
        del self._info.pdtreadann[:]
        del self._info.righep0[:]
        self.ProdProReset()
        self._info.deleting = False
    
    def DeleteRow(self):
        tdid = self.id_doctra
        o = adb.DbTable.DeleteRow(self)
        self._info.deleting = True
        if o and tdid is not None:
            self._info.tradocdel.append(tdid)
        return o
    
    def _SaveRecords(self, records, deletions):
        deleting = self._info.deleting
        if self.id_doctra is not None:
            if not self.id_doctra in self._info.tradocdel:
                self._info.tradocdel.append(self.id_doctra)
        self.DelDocTra()
        if deleting:
            self.AggiornaCliFor(deldoc=True)
        out = adb.DbTable._SaveRecords(self, records, deletions)
        if out:
            if deleting:
                self.AggiornaProdotti(deldoc=True)
            else:
                if self._info.acqdocacq or self._info.acqdocann:
                    acqdoc = DocMag()
                    docs = []
                    for did in self._info.acqdocacq:
                        if not did in docs:
                            docs.append(did)
                    for did in self._info.acqdocann:
                        if not did in docs:
                            docs.append(did)
                    for did in docs:
                        if acqdoc.Get(did) and acqdoc.OneRow():
                            if acqdoc.id in self._info.acqdocacq:
                                #segno il documento come acquisito
                                acqdoc.f_acq = 1
                                acqdoc.id_docacq = self.id
                            if acqdoc.id in self._info.acqdocann:
                                #segno il documento come annullato
                                acqdoc.f_ann = 1
                            acqdoc.Save()
                if self._info.acqmovann:
                    acqdoc = DocMag()
                    docs = self._info.acqmovann.keys()
                    for did in self._info.acqmovann:
                        if acqdoc.Get(did) and acqdoc.OneRow():
                            for mid in self._info.acqmovann[acqdoc.id]:
                                if acqdoc.mov.Locate(lambda m: m.id == mid):
                                    acqdoc.mov.f_ann = 1
                            acqdoc.Save()
                if self._info.pdtreadann:
                    db = self._info.db
                    for pdtread in self._info.pdtreadann:
                        db.Execute("DELETE FROM %s WHERE id_h=%%s"\
                                   % bt.TABNAME_PDT_B, pdtread)
                        db.Execute("DELETE FROM %s WHERE id=%%s"\
                                   % bt.TABNAME_PDT_H, pdtread)
                if self.cfgdoc.aggnum and self.id_tipdoc is not None:
                    progr = self._info.progr
                    #aggiornamento ultimo numero di documento
                    progr.ClearFilters()
                    progr.AddFilter("progr.codice=%s",  "mag_lastdoc")
                    progr.AddFilter("progr.keydiff=%s", self.datdoc.year)
                    progr.AddFilter("progr.key_id=%s",  self.id_tipdoc)
                    if progr.Retrieve():
                        if progr.IsEmpty():
                            progr.CreateNewRow()
                            progr.codice = "mag_lastdoc"
                            progr.keydiff = self.datdoc.year
                            progr.key_id = self.id_tipdoc
                            progr.progrnum = 0
                        if self.numdoc > progr.progrnum:
                            progr.progrnum = self.numdoc
                            progr.Save()
                    del progr
                self.AggiornaProdotti()
                self.AggiornaCliFor()
                if self.cfgdoc.id_tdoctra is not None:
                    try:
                        self.GenDocTra()
                    except Exception, e:
                        self._info.db.dbError.description = repr(e.args)
                        out = False
        if out:
            del self._info.tradocdel[:]
            self._info.deleting = False
        return out
    
    def AggiornaProdotti(self, deldoc=False):
        wp = self._info.waitDialog
        if wp:
            wait = awu.WaitDialog(wp, message="Aggiornamento prodotti in corso",
                                  maximum=self.mov.RowsCount())
        else:
            wait = None
        pp = self._info.prodpro
        if not deldoc:
            pup = {}
            tm = self.mov.config
            for n, mov in enumerate(self.mov):
                if wait: wait.SetValue(n)
                proid = mov.id_prod
                if proid is None or self.f_ann == 1 or mov.f_ann == 1:
                    continue
                ppkey = '%d/%d' % (mov.id, mov.id_prod)
                if not ppkey in pp:
                    pp[ppkey] = copy.deepcopy(self._info.ppcol)
                pr = pp[ppkey]
                for col in pr.keys():
                    agg = getattr(tm, 'agg%s' % col) or 0
                    p = pr[col]
                    p['tw'] += round(((eval(p['exp']) or 0)*agg),p['dec'])
                cols = {}
                if (tm.aggcosto or ' ') in '12':
                    cols['costo'] = {'val':  None, 
                                      'type': tm.aggcosto,
                                      'sia': bt.MAGSCORPCOS == '1'}
                
                if (tm.aggprezzo or ' ') in '12':
                    cols['prezzo'] = {'val':  None, 
                                      'type': tm.aggprezzo,
                                      'sia': bt.MAGSCORPPRE == '1'}
                
                if tm.aggfornit == 'X':
                    cols['updfornit'] = {'val': True}
                
                if (bt.MAGATTGRIP or bt.MAGATTGRIF) and bt.MAGAGGGRIP:
                    if (tm.agggrip or ' ') in 'AN' and mov.agggrip:
                        cols['griprez'] = {'val':  [tm.agggrip, 
                                                    self.datreg, 
                                                    mov.prezzo or 0, 
                                                    mov.sconto1 or 0, 
                                                    mov.sconto2 or 0, 
                                                    mov.sconto3 or 0,
                                                    mov.sconto4 or 0,
                                                    mov.sconto5 or 0,
                                                    mov.sconto6 or 0,
                                                    mov.pzconf] }
                
                sid = (self.config.scorpiva == '1')
                for col in cols:
                    val = cols[col]['val']
                    if 'type' in cols[col]:
                        tipo = cols[col]['type']
                        if tipo == '1':
                            val = mov.prezzo or 0
                        elif tipo == '2':
                            DQ = bt.MAGPRE_DECIMALS
                            try: val = round((mov.importo or 0)/(mov.qta or 0), DQ)
                            except ZeroDivisionError: val = 0
                    if val is not None:
                        if 'sia' in cols[col]:
                            sia = cols[col]['sia']
                            if sid != sia:
                                if sia:
                                    #c/p con iva, doc no: aggiungo iva
                                    val = round(val*(100+mov.iva.perciva)/100,
                                                bt.MAGPRE_DECIMALS)
                                else:
                                    #c/p senza iva, doc si: scorporo iva
                                    val = round(val/(100+mov.iva.perciva)/100,
                                                bt.MAGPRE_DECIMALS)
                        if not proid in pup:
                            pup[proid] = []
                        pup[proid].append({col: val,
                                           '|1|riccosto':   tm.riccosto == 'X',
                                           '|2|ricprezzo':  tm.ricprezzo == 'X',
                                           '|3|riccostosr': (tm.riccostosr == 'X', 
                                                             mov.sconto1, 
                                                             mov.sconto2, 
                                                             mov.sconto3, 
                                                             mov.sconto4, 
                                                             mov.sconto5, 
                                                             mov.sconto6),
                                           '|4|riclist':    tm.riclist == 'X',
                                           '|?|newlist':    tm.newlist == 'X',
                                           '|?|datlist':    self.datreg})
                self.UpdateMovExternalWrite()
        oldmag = self._info.ppkeys['mag']
        olddrg = self._info.ppkeys['drg']
        for ppkey in pp:
            self.ProdProWrite(ppkey, oldmag, olddrg, 'tr', '-')
            if not deldoc:
                newmag = self.id_magazz
                newdrg = self.datreg
                self.ProdProWrite(ppkey, newmag, newdrg, 'tw', '+')
        if not deldoc:
            self.UpdateProdotti(pup)
        if wait:
            wait.Destroy()
    
    def UpdateMovExternalRead(self):
        pass
    
    def UpdateMovExternalWrite(self):
        pass
    
    def AggiornaCliFor(self, deldoc=False):
        self.CliForProWrite('+-'[int(deldoc)])
    
    def CliForProRead(self):
        pass
    
    def CliForProWrite(self, segno='+'):
        pass
    
    def ProdProWrite(self, ppkey, magid, dreg, tcol, segno):
        _, proid = map(int, ppkey.split('/'))
        do = True
        if self._info.lastchiusura is not None:
            do = dreg > self._info.lastchiusura
        if not do:
            return
        pp = self._info.prodpro
        pr = pp[ppkey]
        cmdins = []
        cmdupd = []
        for col in pr.keys():
            p = pr[col]
            if p[tcol]:
                v = p[tcol]
                if segno == '-':
                    try:
                        v *= -1
                    except:
                        v = 0
                cmdins.append((col, v))
                cmdupd.append(("%s=%s%s%%s" % (col, col, segno), p[tcol]))
        if cmdins or cmdupd:
            tab = self._info.dbppr._info.tableName
            db = adb.db.__database__
            assert isinstance(db, adb.DB)
            db.Retrieve('SELECT 1 FROM prodpro WHERE id_prod=%s AND id_magazz=%s',
                        (proid, magid))
            new = (len(db.rs) == 0)
            cmd = ''
            par = []
            if new:
                #if segno == '-':
                    #return True
                ph = ''
                for c in cmdins:
                    if cmd: cmd += ', '
                    cmd += c[0]
                    par.append(c[1])
                    if ph: ph += ', '
                    ph += r'%s'
                cmd += ', id_prod, id_magazz'
                ph += r', %s, %s'
                cmd = "INSERT INTO %s (%s) VALUES (%s)" % (bt.TABNAME_PRODPRO, 
                                                           cmd, ph)
            else:
                for c in cmdupd:
                    if cmd: cmd += ', '
                    cmd += c[0]
                    par += list(c[1:])
                cmd = "UPDATE %s SET " % tab + cmd
                cmd += r" WHERE id_prod=%s AND id_magazz=%s"
            par.append(proid)
            par.append(magid)
            if not db.Execute(cmd, par):
                raise Exception, db.dbError.description
        return True
    
    def UpdateProdotti(self, gpup):
        pro = self.updpro
        gpr = pro.gruprez
        lis = self.updlis
        grp = self.updgrp
        DQ = bt.MAGQTA_DECIMALS
        DP = bt.MAGPRE_DECIMALS
        err = None
        for proid in gpup:
            if pro.Get(proid) and pro.OneRow():
                for pup in gpup[proid]:
                    wpro = False
                    cols = pup.keys()
                    cols.sort()
                    for col in cols:
                        val = pup[col]
                        if col.startswith('|'):
                            if 'riccosto' in col and val:
                                if gpr.calcpc == 'C':
                                    #ricalcola costo
                                    rc = pup['|3|riccostosr']
                                    if rc[0] and (rc[1] or\
                                                  rc[2] or\
                                                  rc[3] or\
                                                  rc[4] or\
                                                  rc[5] or\
                                                  rc[6]):
                                        pro.RicalcolaCosto(rc[1] or 0,
                                                           rc[2] or 0,
                                                           rc[3] or 0,
                                                           rc[4] or 0,
                                                           rc[5] or 0,
                                                           rc[6] or 0)
                                    else:
                                        pro.RicalcolaCosto()
                            if 'ricprezzo' in col and val:
                                if gpr.calcpc == 'P':
                                    #ricalcola prezzo
                                    pro.RicalcolaPrezzo()
                            if 'riclist' in col and val:
                                #aggiorna listini
                                lis.ClearFilters()
                                lis.AddFilter('id_prod=%s', proid)
                                data = pup['|?|datlist']
                                if bt.MAGDATLIS:
                                    if pup['|?|newlist']:
                                        lis.AddFilter('data=%s', data)
                                    else:
                                        lis.AddFilter('data<=%s', data)
                                lis.Retrieve()
                                if lis.RowsCount() == 0:
                                    lis.CreateNewRow()
                                    lis.id_prod = pro.id
                                    if True:#bt.MAGDATLIS:
                                        lis.data = data
                                wl = False
                                for n in range(1,bt.MAGNUMLIS+1):
                                    if gpr.calclis == 'C':
                                        #listini da costo di acquisto e ricariche
                                        r = getattr(gpr, 'prclisric%d' % n)
                                        p = round(pro.costo*(100+r)/100, DP)
                                    elif gpr.calclis == 'P':
                                        #listini da prezzo al pubblico e sconti
                                        s = getattr(gpr, 'prclissco%d' % n)
                                        p = round(pro.prezzo*(100-s)/100, DP)
                                    else:
                                        p = None
                                    if p is not None:
                                        setattr(lis, 'prezzo%d' % n, p)
                                        wl = True
                                if wl:
                                    if not lis.Save():
                                        err = repr(lis.GetError())
                                        break
                            
                        elif col == 'updfornit':
                            if val and self.id_pdc:
                                pro.id_fornit = self.id_pdc
                                wpro = True
                            
                        elif col == 'griprez':
                            tip, dat, prz, sc1, sc2, sc3, sc4, sc5, sc6, pzc = val
                            if val and self.id_pdc:
                                #aggiorna griglia prezzi
                                grp.ClearFilters()
                                grp.AddFilter('id_prod=%s', proid)
                                grp.AddFilter('id_pdc=%s', self.id_pdc)
                                data = pup['|?|datlist']
                                if tip == 'A':
                                    grp.AddFilter('data<=%s', dat)
                                else:
                                    grp.AddFilter('data=%s', dat)
                                grp.AddLimit(1)
                                grp.Retrieve()
                                if grp.RowsCount() == 0:
                                    #creo griglia, per la data vedo se ci sono griglie di altri prodotti ed eventualmente prendo quella
                                    grp.ClearFilters()
                                    grp.AddFilter('id_pdc=%s', self.id_pdc)
                                    grp.Retrieve()
                                    if grp.RowsCount() == 0:
                                        dg = dat
                                    else:
                                        dg = grp.data
                                    grp.CreateNewRow()
                                    grp.id_prod = pro.id
                                    grp.id_pdc = self.id_pdc
                                    grp.data = dg
                                grp.prezzo = prz
                                grp.sconto1 = sc1
                                grp.sconto2 = sc2
                                grp.sconto3 = sc3
                                grp.sconto4 = sc4
                                grp.sconto5 = sc5
                                grp.sconto6 = sc6
                                if bt.MAGPZGRIP:
                                    grp.pzconf = pzc
                                if not grp.Save():
                                    err = repr(grp.GetError())
                                    break
                            
                        else:
                            setattr(pro, col, val)
                            wpro = True
                    
                    if err:
                        break
                    
                if err:
                    break
            
            if wpro:
                if not pro.Save():
                    err = repr(pro.GetError())
                    break
        
        return True
    
    def GenDocTra(self):
        """
        Genera il documento di trasferimento.  Il documento generato sarà una
        copia identica al documento di partenza, eccetto che per il sottoconto
        ed il magazzino: il documento di partenza deve essere configurato per
        operare su sottoconti di tipo magazzino; la scelta del sottoconto 
        determina anche il magazzino del documento da generare, come da
        configurazione della tabella magazzini.
        La corrispondenza tra i tipi movimento è fatta mediante codice, quindi
        occorre configurare entrambi i tipi documento utilizzando gli stessi
        codici per i movimenti.
        """
        cfg1 = self.cfgdoc
        cfg2 = adb.DbTable(bt.TABNAME_CFGMAGDOC, 'tipdoc')
        cfg2.AddMultiJoin(bt.TABNAME_CFGMAGMOV, 'tipmov')
        if not cfg2.Retrieve('tipdoc.id=%s', cfg1.id_tdoctra):
            raise Exception, repr(cfg2.GetError())
        tpms = {}
        movok = True
        for m in cfg1.tipmov:
            if not cfg2.tipmov.Locate(lambda x: x.codice == m.codice):
                movok = False
                raise Exception, 'Tipi movimento incongruenti'
            tpms[m.id] = cfg2.tipmov.id
        docgen = DocMag()
        if self.id_doctra is not None:
            self.DelDocTra()
        dbm = adb.DbTable(bt.TABNAME_MAGAZZ, 'mag')
        dbm.Retrieve('id_pdc=%s', self.id_pdc)
        docgen.Get(-1)
        docgen.CreateNewRow()
        for f in self.GetFieldNames():
            if f != 'id':
                if f == 'id_tipdoc':
                    v = cfg1.id_tdoctra
                elif f == 'id_magazz':
                    v = dbm.id
                elif f == 'id_pdc':
                    v = self.magazz.id_pdc
                elif f == 'id_doctra':
                    v = None
                else:
                    v = getattr(self, f)
                setattr(docgen, f, v)
        m2 = docgen.mov
        for m1 in self.mov:
            m2.CreateNewRow()
            for f in m2.GetFieldNames():
                if not f in ('id', 'id_doc'):
                    v = getattr(m1, f)
                    if f == 'id_tipmov':
                        v = tpms[v]
                    elif f == 'id_moveva':
                        v = None
                    elif f == 'id_movacq':
                        v = getattr(m1, f)
                    setattr(m2, f, v)
        if not docgen.Save():
            raise Exception, repr(docgen.GetError())
        remove = self.id in self._info.modifiedRecords
        self.id_doctra = docgen.id
        if remove:
            self._info.modifiedRecords.remove(self.id)
        cmd = "UPDATE %s SET id_doctra=%s WHERE id=%s" \
            % (bt.TABNAME_MOVMAG_H, self.id_doctra, self.id)
        self._info.db.Execute(cmd)
    
    def DelDocTra(self):
        """
        Cancella il documento di trasferimento correntemente associato.
        """
        dgids = ','.join([str(x) for x in self._info.tradocdel])
        if dgids:
            for cmd in ("DELETE FROM %s WHERE id_doc IN (%s)" \
                        % (bt.TABNAME_MOVMAG_B, dgids),
                        "DELETE FROM %s WHERE id IN (%s)" \
                        % (bt.TABNAME_MOVMAG_H, dgids)):
                self._info.db.Execute(cmd)
        self.id_doctra = None
    
    def DocLoad(self, cod, num, year=None):
        out = False
        if year is None:
            year = Env.Azienda.Esercizio.year
        tipdoc = adb.DbTable(bt.TABNAME_CFGMAGDOC, "tipdoc",\
                             writable=False)
        tipdoc.AddFilter("tipdoc.codice=%s", cod)
        if tipdoc.Retrieve():
            self.StoreFilters()
            self.ClearFilters()
            self.AddFilter("doc.id_tipdoc=%s", tipdoc.id)
            self.AddFilter("YEAR(doc.datdoc)=%s", year)
            self.AddFilter("doc.numdoc=%s", num)
            if self.Retrieve():
                out = self.RowsCount() == 1
            self.ResumeFilters()
        self.ProdProReset()
        if out:
            self.ProdProRead()
            self.CliForProRead()
            self.regcon.Get(self.id_reg)
        return out
    
    def CheckNum(self):
        out_flag = True
        out_desc = ''
        tn = self.config.numdoc or ' '
        if tn in '01' and self.config.ctrnum == 'X':
            d = adb.DbTable(bt.TABNAME_MOVMAG_H, 'doc')
            d.AddJoin(bt.TABNAME_CFGMAGDOC, 'tipdoc', idLeft='id_tipdoc')
            d.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id_pdc')
            d.AddFilter('YEAR(doc.datreg)=%s', self.datreg.year)
            d.AddFilter('doc.id_magazz=%s', self.id_magazz)
            p = []
            if self.config.docfam:
                f = 'tipdoc.docfam=%s'
                p = self.config.docfam
            else:
                f = 'doc.id_tipdoc=%s'
                p = self.id_tipdoc
            d.AddFilter(f, p)
            d.AddFilter('doc.numdoc=%s', self.numdoc)
            if self.id:
                d.AddFilter('doc.id<>%s', self.id)
            if d.Retrieve() and not d.IsEmpty():
                out_flag = False
                out_desc = 'Numero esistente sul documento:\n'\
                    +'%s n. %s del %s, anagr. %s - %s'\
                    % (d.tipdoc.descriz, d.numdoc, d.dita(d.datdoc), d.pdc.codice, d.pdc.descriz)
        elif tn == '3' or (self.config.askprotiva or ' ') in '123':
            if self.regcon.id is None:
                ri = self.GetRegIva()
            else:
                ri = self.regcon.id_regiva
            yr = self.datreg.year
            ni = self.numiva
            r = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg')
            _ = r.AddJoin(bt.TABNAME_CFGCONTAB, 'caus', idLeft='id_caus')
            m = r.AddJoin(bt.TABNAME_CONTAB_B, 'mov', join=adb.JOIN_LEFT, relexpr='mov.id_reg=reg.id AND mov.numriga=1')
            _ = m.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id_pdcpa', join=adb.JOIN_LEFT)
            if ri is not None:
                r.AddFilter('reg.id_regiva=%s', ri)
                r.AddFilter('YEAR(reg.datreg)=%s', yr)
                r.AddFilter('reg.numiva=%s', ni)
                if self.regcon.id is not None:
                    r.AddFilter('reg.id<>%s', self.regcon.id)
                if r.Retrieve() and not r.IsEmpty():
                    out_flag = False
                    out_desc = 'Protocollo IVA già impegnato:\n'\
                        +'%s n. %s del %s, prot. %s, anagr. %s - %s'\
                        % (r.caus.descriz, r.numdoc, r.dita(r.datdoc), r.numiva, r.mov.pdc.codice, r.mov.pdc.descriz)
        return (out_flag, out_desc)
    
    def Get(self, *args, **kwargs):
        self.ResetVars()
        out = adb.DbTable.Get(self, *args, **kwargs)
        self.cfgdoc.Get(self.id_tipdoc)
        self.ProdProRead()
        self.CliForProRead()
        if self.cfgdoc.colcg:
            self.regcon.Get(self.id_reg)
        return out
    
    def _UpdateTableVars(self, *args, **kwargs):
        out = adb.DbTable._UpdateTableVars(self, *args, **kwargs)
        #if self.cfgdoc.id != self.id_tipdoc:
            #self.cfgdoc.Get(self.id_tipdoc)
        self._info.oldtot = self.totdare
        self._info.oldpag = self.id_modpag
        if not self._info.displayonly:
            self.MakeTotals(scad=False)
        return out
    
    def ProdProReset(self):
        self._info.prodpro.clear()
        self._info.ppkeys['mag'] = None
        self._info.ppkeys['drg'] = None
        self._info.ppkeys['ann'] = False
    
    def ProdProRead(self):
        self.ProdProReset()
        do = True
        if self.datreg is not None and self._info.lastchiusura is not None:
            do = self.datreg > self._info.lastchiusura
        if not do:
            return
        self._info.ppkeys['mag'] = self.id_magazz
        self._info.ppkeys['drg'] = self.datreg
        if self.datreg is None:
            year = None
        else:
            year = self.datreg.year
        self._info.ppkeys['ann'] = (self.f_ann == 1)
        if (self.f_ann == 1):
            return
        pp = self._info.prodpro
        for mov in self.mov:
            if mov.id_prod and mov.f_ann != 1:
                ppkey = '%d/%d' % (mov.id, mov.id_prod)
                if not ppkey in pp:
                    pp[ppkey] = copy.deepcopy(self._info.ppcol)
                pr = pp[ppkey]
                for col in pr.keys():
                    agg = getattr(self.mov.config, 'agg%s' % col)
                    p = pr[col]
                    try:
                        p['tr'] += round(((eval(p['exp']) or 0)*agg),p['dec'])
                    except:
                        pass
            self.UpdateMovExternalRead()
    
    def _TotalizzaRiga(self, mov):
        return True
    
    def ApplicaListino(self):
        lisnul = []
        for mov in self.mov:
            if mov.id_prod:
                prz, tipo, _, _, _, _, _, _ = self.DefPrezzoSconti()
                if tipo == "L" and mov.id_tiplist is None:
                    if prz:
                        mov.prezzo = prz
                        ND = bt.VALINT_DECIMALS
                        mov.importo = round(mov.qta*mov.prezzo\
                                            *(100-mov.sconto1)/100\
                                            *(100-mov.sconto2)/100\
                                            *(100-mov.sconto3)/100\
                                            *(100-mov.sconto4)/100\
                                            *(100-mov.sconto5)/100\
                                            *(100-mov.sconto6)/100, ND)
                    else:
                        if not mov.prod.codice in lisnul:
                            lisnul.append(mov.prod.codice)
        self.MakeTotals()
        if lisnul:
            msg = \
                """Non è stato possibile applicare il nuovo listino """
            if len(lisnul) == 1:
                msg += """al codice prodotto: """
            else:
                msg += """ai seguenti codici prodotto:\n"""
            msg += '\n'.join(lisnul)
            msg += """\npoiché mancante"""
            raise ListinoMancanteException, msg
    
    #def __setattr__(self, field, content, setChanged=True):
        #adb.DbTable.__setattr__(self, field, content, setChanged=True)
        #if field == 'totspese' and not content and self.id is not None:
            #pass
    
    def MakeTotals(self, scad=True, pesocolli=False):
        m = magazz
        if bt.TIPO_CONTAB == "O":
            def TotIvaSearch(self, aliqid, aliqcod, aliqdes, aliqprc, aliqind, aliqtip, isomagg):
                try:
                    i = ListSearch(self._info.totiva,\
                                   lambda x: x[m.RSIVA_ID] == aliqid and x[m.RSIVA_ISOMAGG] == isomagg)
                except IndexError:
                    if isomagg:
                        aliqdes = "OMAGGI"
                    self._info.totiva.append(\
                        [aliqid,   #RSIVA_ID
                         aliqcod,  #RSIVA_codiva
                         aliqdes,  #RSIVA_desiva
                         0,        #RSIVA_IMPONIB
                         0,        #RSIVA_IMPOSTA
                         0,        #RSIVA_IMPORTO
                         0,        #RSIVA_IMPOSCR
                         isomagg,  #RSIVA_ISOMAGG
                         aliqprc,  #RSIVA_perciva
                         aliqind,  #RSIVA_percind
                         aliqtip]) #RSIVA_tipoalq
                    i = len(self._info.totiva)-1
                return i
            def _TotPdcSearch(self, totpdc, pdcid, pdccod, pdcdes, tipriga, *dummy):
                try:
                    i = ListSearch(totpdc, lambda x: x[m.RSPDC_ID] == pdcid)
                except IndexError:
                    totpdc.append([pdcid,    #RSPDC_ID
                                   pdccod,   #RSPDC_codpdc
                                   pdcdes,   #RSPDC_despdc
                                   0,        #RSPDC_IMPONIB
                                   0,        #RSPDC_IMPORTO
                                   False,    #RSPDC_ISSPESA
                                   False,    #RSPDC_ISOMAGG
                                   tipriga]) #RSPDC_TIPRIGA
                    i = len(totpdc)-1
                return i
        else:
            
            def _TotPdcSearch(self, totpdc, pdcid, pdccod, pdcdes, tipriga, ivaid, ivacod, ivades, isomagg, destot):
                try:
                    i = ListSearch(totpdc, lambda x: x[m.RSPDC_ID] == pdcid and x[m.RSPDC_ALIQ_ID] == ivaid and x[m.RSPDC_ISOMAGG] == isomagg)
                except IndexError:
#                    if isomagg:
#                        ivades = "OMAGGI"
                    totpdc.append([pdcid,             #RSPDC_ID
                                   pdccod,            #RSPDC_codpdc
                                   pdcdes,            #RSPDC_despdc
                                   0,                 #RSPDC_IMPONIB
                                   0,                 #RSPDC_IMPORTO
                                   False,             #RSPDC_ISSPESA
                                   isomagg,           #RSPDC_ISOMAGG
                                   tipriga,           #RSPDC_TIPRIGA
                                   ivaid,             #RSPDC_ALIQ_ID
                                   ivacod,            #RSPDC_aliqcod
                                   ivades,            #RSPDC_aliqdes
                                   0,                 #RSPDC_IMPOSTA
                                   0,                 #RSPDC_INDEDUC
                                   0,                 #RSPDC_IMPOSCR
                                   destot or pdcdes]) #RSPDC_DESTOT
                    i = len(totpdc)-1
                return i
            
        def TotPdcSearch(self, pdcid, pdccod, pdcdes, *args):
            return _TotPdcSearch(self, self._info.totpdc, pdcid, pdccod, pdcdes, *args)
        def TotPdxSearch(self, pdcid, pdccod, pdcdes, *args):
            return _TotPdcSearch(self, self._info.totpdx, pdcid, pdccod, pdcdes, *args)
        
        totspese = None
        
        def RoundImp(i):
            return round(i, bt.VALINT_DECIMALS)
        
        # azzero totali doc., x iva e x pdc
        totiva = self._info.totiva
        totpdc = self._info.totpdc
        totpdx = self._info.totpdx
        self.totimponib = 0
        self.totimposta = 0
        self.totimporto = 0
        self.totdare = 0
        self.totmerce = 0
        self.totservi = 0
        self.tottrasp = 0
        self.totspese = 0
        self.totscrip = 0
        self.totscmce = 0
        self.totscpra = 0
        self.totomagg = 0
        self.totaumpr = 0
        self._totvend = 0
        self._totcost = 0
        if pesocolli:
            self.totpeso = 0
            self.totcolli = 0
        del totiva[:]
        del totpdc[:]
        del totpdx[:]
        del self._info.righep0[:]
        
        totscrip = 0
        totimpon = 0
        totimpox = 0 #tot.imponib esclusi omaggi, x ripartizione sconti "I"
        totivato = 0
        totivatx = 0 #tot.ivato esclusi omaggi, x ripartizione sconti "I"
        pdcnorip = []
        calspese = True
        _curmov = self.mov.RowNumber()
        sid = (self.config.scorpiva == '1')
        if sid:
            coltot = m.RSIVA_IMPORTO
        else:
            coltot = m.RSIVA_IMPONIB
        
        # aumento totali di ogni riga in funzione della maggiorazione documento
        # determinata come somma degli importi delle righe di tipo P
        testaumpr = self.cfgdoc.tipmov.Locate(lambda tm: tm.tipologia == "P")
        if testaumpr:
            #totalizzo righe di incremento prezzi
            tmid = self.cfgdoc.tipmov.id
            def mcc(x):
                return self.mov._GetFieldIndex(x, inline=True)
            tmcol = mcc('id_tipmov')
            imcol = mcc('importo')
            qtcol = mcc('qta')
            prcol = mcc('qta')
            s1col = mcc('sconto1')
            s2col = mcc('sconto2')
            s3col = mcc('sconto3')
            s4col = mcc('sconto4')
            s5col = mcc('sconto5')
            s6col = mcc('sconto6')
            avcol = self.mov.config._GetFieldIndex('askvalori', inline=True)
            rs = self.mov.GetRecordset()
            totau = 0
            for n in range(self.mov.RowsCount()):
                if rs[n][tmcol] == tmid:
                    totau += rs[n][imcol]
            self.totaumpr = totau
            #ciclo su movimenti per ricalcolare importo standard
            totau = 0
            totim = 0
            lastm = None
            for mov in self.mov:
                if mov.config.tipologia != "M" or mov.config.askvalori != "T":
                    continue
                if mov.importo is not None:
                    if mov.qta is not None and mov.prezzo is not None:
                        mov.importo = RoundImp(mov.qta*mov.prezzo\
                                               *(100-mov.sconto1)/100\
                                               *(100-mov.sconto2)/100\
                                               *(100-mov.sconto3)/100\
                                               *(100-mov.sconto4)/100\
                                               *(100-mov.sconto5)/100\
                                               *(100-mov.sconto6)/100)
                        totim += mov.importo
            if self.totaumpr>0:
                totau = 0
                totim = RoundImp(totim)
                lastm = None
                for mov in self.mov:
                    if mov.config.tipologia != "M" or mov.config.askvalori != "T":
                        continue
                    if mov.importo is not None:
                        try:
                            au = RoundImp(self.totaumpr*(mov.importo or 0)/totim)
                            mov.importo = RoundImp(mov.importo+au)
                            lastm = mov.RowNumber()
                        except ZeroDivisionError:
                            au = 0
                    totau += au
                if totau != self.totaumpr and lastm is not None:
                    self.mov.MoveRow(lastm)
                    self.mov.importo = RoundImp(self.mov.importo+self.totaumpr-totau)
        
        for mov in self.mov:
            if not self._TotalizzaRiga(mov):
                continue
            # determinazione imponibili x aliquota 
            # e ammontare sconti da ripartire
            imp = mov.importo or 0
            if mov.id is None or not mov.IsDeleted():
                if not (mov.config.askvalori or ' ') in 'DQ':
                    tipo = mov.config.tipologia
                    if tipo == "I":
                        totscrip += imp
                        #totimpon -= mov.importo
                    elif tipo not in "EDP":
                        if mov.qta and mov.prezzo:
                            self.totscpra += RoundImp(mov.qta*mov.prezzo)-imp
                        mi = mov.iva
                        if bt.TIPO_CONTAB == "O":
                            #ordinaria
                            i = TotIvaSearch(self, mi.id, mi.codice, mi.descriz,\
                                             mi.perciva, mi.percind, mi.tipo,\
                                             tipo == "O")
                            totiva[i][coltot] += imp
                            if sid:
                                totivato += imp
                                if tipo != "O":
                                    totivatx += imp
                            else:
                                totimpon += imp
                                if tipo != "O":
                                    totimpox += imp
                            if not tipo in "SO":
                                totiva[i][m.RSIVA_IMPOSCR] += imp
                            if tipo == "S":
                                calspese = False
                            #determinazione sottconto di costo/ricavo
                            if tipo != "E":#not in "EO":
                                if tipo == "O":
                                    tp = totpdx
                                else:
                                    tp = totpdc
                                if mov.id_pdccg:
                                    pdccg_id = mov.id_pdccg
                                    pdccg_cod = mov.pdccg.codice
                                    pdccg_des = mov.pdccg.descriz
                                else:
                                    pdccg_id = mov.config.movpdc.id
                                    pdccg_cod = mov.config.movpdc.codice
                                    pdccg_des = mov.config.movpdc.descriz
                                i = _TotPdcSearch(self, tp, pdccg_id, pdccg_cod, pdccg_des, tipo)
                                if sid:
                                    tp[i][m.RSPDC_IMPORTO] += imp
                                    imp, _, _, _ = self.CalcolaIVA(mov.id_aliqiva, ivato=imp)
                                tp[i][m.RSPDC_IMPONIB] += imp
                                if tipo in "S":#"OS":
                                    pdcnorip.append(i)
                                    tp[i][m.RSPDC_ISSPESA] = (tipo == "S")
                                    tp[i][m.RSPDC_ISOMAGG] = (tipo == "O")
                        else:
                            
                            #semplif.
#                            i = TotIvaSearch(self, mi.id, mi.codice, mi.descriz,\
#                                             mi.perciva, mi.percind, mi.tipo,\
#                                             tipo == "O")
#                            totiva[i][coltot] += imp
                            if sid:
                                totivato += imp
                                if tipo != "O":
                                    totivatx += imp
                            else:
                                totimpon += imp
                                if tipo != "O":
                                    totimpox += imp
#                            if not tipo in "SO":
#                                totiva[i][m.RSIVA_IMPOSCR] += imp
                            if tipo == "S":
                                calspese = False
                            #determinazione sottconto di costo/ricavo
                            if tipo != "E":#not in "EO":
                                if False:#tipo == "O":
                                    tp = totpdx
                                else:
                                    tp = totpdc
                                if mov.id_pdccg:
                                    pdccg_id = mov.id_pdccg
                                    pdccg_cod = mov.pdccg.codice
                                    pdccg_des = mov.pdccg.descriz
                                else:
                                    pdccg_id = mov.config.movpdc.id
                                    pdccg_cod = mov.config.movpdc.codice
                                    pdccg_des = mov.config.movpdc.descriz
                                i = _TotPdcSearch(self, tp, pdccg_id, pdccg_cod, pdccg_des, tipo, mi.id, mi.codice, mi.descriz, tipo == "O", mov.config.prtdestot)
                                if sid:
                                    tp[i][m.RSPDC_IMPORTO] += imp
                                    imp, _, _, _ = self.CalcolaIVA(mov.id_aliqiva, ivato=imp)
                                tp[i][m.RSPDC_IMPONIB] += imp
                                if tipo in "OS":
                                    pdcnorip.append(i)
                                    tp[i][m.RSPDC_ISSPESA] = (tipo == "S")
                                    tp[i][m.RSPDC_ISOMAGG] = (tipo == "O")
                                else:
                                    tp[i][m.RSPDC_IMPOSCR] = imp
                    
                    if mov.config.statftcli in (1, -1):
                        self._totvend += (imp or 0)*mov.config.statftcli
                    if mov.config.statcscli in (1, -1):
                        self._totcost += (mov.costot or 0)*mov.config.statcscli
                    
                    if mov.config.askvalori == 'T' and (mov.prezzo == 0 or mov.prezzo is None):
                        self._info.righep0.append(mov.numriga)
                
                if pesocolli:
                    self.AddTotalPesoColli(mov)
            
            tipo = mov.config.tipologia
            if   tipo == "M":
                self.totmerce += imp
#                self.totscpra += (mov.qta*mov.prezzo)-imp
            elif tipo == "V":
                self.totservi += imp
            elif tipo == "T":
                self.tottrasp += imp
            elif tipo == "I":
                self.totscrip += imp
            elif tipo == "E":
                self.totscmce += imp
            elif tipo == "O":
                self.totomagg += imp
            elif tipo == "S":
                totspese = (totspese or 0) + imp
        
        if 0 <= _curmov < self.mov.RowsCount():
            self.mov.MoveRow(_curmov)
        
        self._totmargineval =  self._totvend-self._totcost
        try:
            self._totmargineperc = (self._totvend-self._totcost)/self._totvend*100
        except:
            self._totmargineperc = 0
        
        #numero riga tot.x pdc conto spese se in caso di doc. scorporo il calc.
        #dell'imponibile della spesa non sia corretto rispetto al tot. imponib.
        #del documento
        pdcspe = None
        
        # calcolo spese se non presenti nel dettaglio
        if calspese and self.id_speinc is not None:
            if self.cfgdoc.tipmov.Locate(lambda mov: mov.tipologia == "S"):
                dbspese = self.spese
                if dbspese.importo and dbspese.id_aliqiva:
                    if totspese is None:
                        totspese = self.spese.importo*(self.modpag.numscad or 0)
                        if sid:
                            totspese = RoundImp(totspese*(100+dbspese.iva.perciva)/100)
                    si = self.spese.iva
                    if bt.TIPO_CONTAB == "O":
                        #ordinaria
                        i = TotIvaSearch(self,\
                                         si.id, si.codice, si.descriz,\
                                         si.perciva, si.percind, si.tipo,\
                                         False)
                        if sid:
                            totiva[i][m.RSIVA_IMPORTO] += totspese
                            totivatx += totspese
                        else:
                            totiva[i][m.RSIVA_IMPONIB] += totspese
                            totimpox += totspese
                        i = TotPdcSearch(self,\
                                         self.cfgdoc.tipmov.pdc.id,\
                                         self.cfgdoc.tipmov.pdc.codice,\
                                         self.cfgdoc.tipmov.pdc.descriz,\
                                         "S")
                        if sid:
                            s, _, _, _ = self.CalcolaIVA(dbspese.id_aliqiva, ivato=totspese)
                            totspese = s
                            pdcspe = i
                        else:
                            s = totspese
                        totpdc[i][m.RSPDC_IMPONIB] += s
                        totpdc[i][m.RSPDC_ISSPESA] = True
                        pdcnorip.append(i)
                    else:
                        
                        #semplif.
                        i = TotPdcSearch(self,\
                                         self.cfgdoc.tipmov.pdc.id,\
                                         self.cfgdoc.tipmov.pdc.codice,\
                                         self.cfgdoc.tipmov.pdc.descriz,\
                                         "S",
                                         si.id,
                                         si.codice,
                                         si.descriz,
                                         False,
                                         self.cfgdoc.tipmov.prtdestot)
                        if sid:
                            totivatx += totspese
                            totpdc[i][m.RSPDC_IMPORTO] += totspese
                            s, _, _, _ = self.CalcolaIVA(dbspese.id_aliqiva, ivato=totspese)
                            totspese = s
                            pdcspe = i
                        else:
                            totimpox += totspese
#                            s, _, _, _ = self.CalcolaIVA(dbspese.id_aliqiva, imponib=totspese)
                            totpdc[i][m.RSPDC_IMPONIB] += totspese
                        totpdc[i][m.RSPDC_ISSPESA] = True
                        pdcnorip.append(i)
        self.totspese = totspese
        
#        if sid and pdcspe:
#            timpdc = 0
#            for t in totpdc:
#                timpdc += t[m.RSPDC_IMPONIB]
#            if not adb.DbTable.samefloat(timpdc, self.totimponib):
#                totpdc[pdcspe][m.RSPDC_IMPONIB] += (self.totimponib-timpdc)
        
        if bt.TIPO_CONTAB == "O":
            #ordinaria
            # ripartizione sconti su totali x aliquota
            if totscrip and totiva:
                totsc = 0
                for i in totiva:
                    if not i[m.RSIVA_ISOMAGG]:
                        if sid:
#                            sc = totscrip*i[m.RSIVA_IMPOSCR]/totivatx
                            sc = RoundImp(totscrip*i[m.RSIVA_IMPORTO]/totivatx)
                            i[m.RSIVA_IMPORTO] -= sc
                        else:
#                            sc = totscrip*i[m.RSIVA_IMPOSCR]/totimpox
                            sc = RoundImp(totscrip*i[m.RSIVA_IMPONIB]/totimpox)
                            i[m.RSIVA_IMPONIB] -= sc
                        totsc += sc
                if totsc and totsc != totscrip:
                    last = len(totiva)-1
                    if sid:
                        i[m.RSIVA_IMPORTO] += totscrip-totsc
                    else:
                        i[m.RSIVA_IMPONIB] += totscrip-totsc
            
            # calcolo imposta x aliquota
            for i in totiva:
                ivaid = i[m.RSIVA_ID]
                if sid:
                    importo = i[m.RSIVA_IMPORTO]
                    imponib, imposta, importo, indeduc =\
                           self.CalcolaIVA(ivaid, ivato=importo)
                else:
                    imponib = i[m.RSIVA_IMPONIB]
                    imponib, imposta, importo, indeduc =\
                           self.CalcolaIVA(ivaid, imponib=imponib)
                #if i[m.RSIVA_desiva] == "OMAGGI":
                    #importo -= imponib
                    #imponib = 0
                i[m.RSIVA_IMPONIB] = imponib
                i[m.RSIVA_IMPOSTA] = imposta+indeduc
                if i[m.RSIVA_ISOMAGG]:
                    i[m.RSIVA_IMPORTO] = imposta
                else:
                    i[m.RSIVA_IMPORTO] = importo
                self.totimposta += imposta+indeduc
                if i[m.RSIVA_ISOMAGG]:
                    self.totimporto += imposta
                else:
                    self.totimponib += imponib
                    self.totimporto += importo
            
            self.totdare = self.totimporto - (self.totritacc or 0)
        
        # ripartizione sconti su totali x pdc
        if totscrip and totpdc:
            if sid:
                #documento a scoporo - per abbattere proporzionalmente
                #l'imponibile di ogni sottoconto di costo/ricavo, totalizzo
                #l'imponibile della matrice dei totali per aliquota, e spalmo
                #sui totali imponibili di ogni riga di sottoconto sulla base di
                #tale totale
                
                if bt.TIPO_CONTAB == "O":
                    ttp = sum([i[m.RSIVA_IMPONIB] for n,i in enumerate(totpdc) if not n in pdcnorip])
                    tti = sum([i[m.RSIVA_IMPONIB] for n,i in enumerate(totiva) if not i[m.RSIVA_ISOMAGG]])-(totspese or 0)
                    self.totscrip = ttp-tti
                    ttx = 0
                    last = None
                    for n,i in enumerate(totpdc):
                        if n not in pdcnorip:
                            i[m.RSPDC_IMPONIB] = round(i[m.RSPDC_IMPONIB]/ttp*tti, bt.VALINT_DECIMALS)
                            ttx += i[m.RSPDC_IMPONIB]
                            last = i
                    if ttx != tti and last is not None:
                        if ttx > tti:
                            last[m.RSPDC_IMPONIB] -= (ttx-tti)
                        elif ttx < tti:
                            last[m.RSPDC_IMPONIB] += (tti-ttx)
                else:
                    ttx = sum([i[m.RSPDC_IMPORTO] for n,i in enumerate(totpdc) if not n in pdcnorip])
                    totsc = 0
                    last = None
                    for n,i in enumerate(totpdc):
                        if n not in pdcnorip:
                            sc = round(totscrip*i[m.RSPDC_IMPORTO]/ttx,
                                       bt.VALINT_DECIMALS)
                            i[m.RSPDC_IMPORTO] -= sc
                            totsc += sc
                            last = i
                    if totsc != totscrip and last is not None:
                        last[m.RSPDC_IMPORTO] += totscrip-totsc
            else:
                #documento a calcolo - l'abbattimento sugli imponibili dei
                #sottoconti viene fatto proporzionalmente in base all'ammontare
                #degli sconti ripartiti, visto che sono di per se stessi valori
                #imponibili
                ttx = sum([i[m.RSPDC_IMPONIB] for n,i in enumerate(totpdc) if not n in pdcnorip])
                totsc = 0
                last = None
                for n,i in enumerate(totpdc):
                    if n not in pdcnorip:
                        sc = round(totscrip*i[m.RSPDC_IMPONIB]/ttx,
                                   bt.VALINT_DECIMALS)
                        i[m.RSPDC_IMPONIB] -= sc
                        totsc += sc
                        last = i
                if totsc != totscrip and last is not None:
                    last[m.RSPDC_IMPONIB] += totscrip-totsc
        
        if bt.TIPO_CONTAB == "O":
            #ordinaria
            #controllo congruenza totali imponibile tra totali iva e x pdc
            #in caso di documento con scorporo
            if sid:
#                timp = 0
#                for t in totiva:
#                    if not t[m.RSIVA_ISOMAGG]:
#                        timp += t[m.RSIVA_IMPONIB]
                timp = sum([t[m.RSIVA_IMPONIB] for t in totiva if not t[m.RSIVA_ISOMAGG]])
                tx = 0
                _m = 0
                for n, t in enumerate(totpdc):
                    i = t[m.RSPDC_IMPONIB]
                    tx += i
                    if i>_m:
                        _m = i
                        _n = n
                if not self.samefloat(tx, timp):
                    d = (timp-tx)
                    #adeguo imponibile su tot.pdc del 
                    #sottoconto con imponib. + alto
                    totpdc[_n][m.RSPDC_IMPONIB] += d
                    tr = totpdc[_n][m.RSPDC_TIPRIGA]
                    _k = None
                    if   tr == 'M': #adeguo su tot.merce
                        _k = 'totmerce'
                    elif tr == 'V': #adeguo su tot.servizi
                        _k = 'totservi'
                    elif tr == 'T': #adeguo su tot.trasporti
                        _k = 'tottrasp'
                    elif tr == 'S': #adeguo su tot.spese
                        _k = 'totspese'
                    if _k:
                        setattr(self, _k, getattr(self, _k)+d)
            
        else:
            
            #semplif.
            #calcolo imposta e indeduc. per ogni riga della matrice totali pdc
            for t in totpdc:
                if sid:
                    imp, mps, mpr, ind = self.CalcolaIVA(t[m.RSPDC_ALIQ_ID], ivato=t[m.RSPDC_IMPORTO])
                else:
                    imp, mps, mpr, ind = self.CalcolaIVA(t[m.RSPDC_ALIQ_ID], imponib=t[m.RSPDC_IMPONIB])
                t[m.RSPDC_IMPONIB] = imp
                t[m.RSPDC_IMPOSTA] = mps
                t[m.RSPDC_INDEDUC] = ind
                t[m.RSPDC_IMPORTO] = mpr
                self.totimposta += mps
                if t[m.RSPDC_ISOMAGG]:
                    self.totimporto += mps
                else:
                    self.totimponib += imp
                    self.totimporto += mpr
                
            self.totdare = self.totimporto - (self.totritacc or 0)
            
        #ridefinizione dei subtotali
        _t = {}
        for name in 'merce servi trasp spese'.split():
            if not name in _t:
                _t[name] = 0
        for tp in totpdc:
            if tp[m.RSPDC_TIPRIGA] == "M":
                _t['merce'] += tp[m.RSPDC_IMPONIB]
            elif tp[m.RSPDC_TIPRIGA] == "V":
                _t['servi'] += tp[m.RSPDC_IMPONIB]
            elif tp[m.RSPDC_TIPRIGA] == "T":
                _t['trasp'] += tp[m.RSPDC_IMPONIB]
            elif tp[m.RSPDC_TIPRIGA] == "S":
                _t['spese'] += tp[m.RSPDC_IMPONIB]
        for name in _t:
            setattr(self, 'tot%s' % name, _t[name])
        
        if scad and self.config.caucon.pcf == '1':
            self.CalcolaScadenze()
    
    def AddTotalPesoColli(self, mov):
        if mov.config.tqtaxpeso:
            pc = mov.prod.kgconf or 0
            if pc:
                if mov.nmconf:
                    p = pc*mov.nmconf
                    if mov.pzconf and mov.prod.pzconf and mov.pzconf != mov.prod.pzconf:
                        p *= float(mov.pzconf)/float(mov.prod.pzconf)
                elif mov.prod.pzconf:
                    p = pc*mov.prod.pzconf
                else:
                    p = pc*mov.qta
                self.totpeso += round(p, 3)
        if mov.config.tqtaxcolli:
            self.totcolli += (mov.nmconf or mov.qta or 0)
    
    def CalcolaScadenze(self):
        if self.config.caucon.pcf == '1':
            self.regcon.CalcolaScadenze(self.datdoc, self.id_modpag,\
                                        self.totdare, self.totimposta)
        self._info.oldtot = self.totdare
        self._info.oldpag = self.id_modpag
    
    def GetRegIva(self):
        if self.config.caucon.regivadyn == 1:
            self.config.caucon.magriv.Locate(lambda x: x.id_magazz == self.id_magazz)
            id_regiva = self.config.caucon.magriv.id_regiva
        else:
            id_regiva = self.config.caucon.id_regiva
        return id_regiva
    
    def MakeRegCon(self):
        """
        Scrittura registrazione contabile
        """
        
        out = True
        reg = self.regcon
        
        if reg.RowsCount() == 0:
            reg.CreateNewRow()
        
        #testata registrazione
        reg.esercizio = self.datdoc.year
        reg.id_caus =   self.config.id_caucg
        reg.tipreg =    reg.config.tipo
        reg.datreg =    self.datreg
        reg.datdoc =    self.datdoc
        reg.numdoc =    self.numdoc
        reg.numiva =    self.numiva
        reg.id_regiva = self.GetRegIva()
        reg.id_valuta = self.id_valuta
        reg.id_modpag = self.id_modpag
        
        segnopa = reg.config.pasegno
        if segnopa == "D":
            segnocp = "A"
        else:
            segnocp = "D"
        
        body = reg.body
        for b in body:
            b.DeleteRow()
        
        numriga = 1
        
#        if reg.config.tipo in 'IE':
#            pdcivaid = self.GetPdcIva(reg)
#        else:
#            pdcivaid = None
        
        pdcivaid = self.GetPdcIva(reg)
        
        if reg.config.tipo in 'IC':
            #riga 1 - sottoconto relativo al documento
            numriga = 1
            body.CreateNewRow()
            body.numriga =     numriga
            body.tipriga =     "C"
            #body.importo =     self.totimporto
            body.importo =     abs(self.totdare)
            body.imposta =     abs(self.totimposta)
            body.indeduc =     0
            if self.totdare >= 0:
                body.segno =   segnopa
            else:
                body.segno =   segnocp
            body.id_pdcpa =    self.id_pdc
            numriga += 1
        
        if reg.config.tipo in 'IC':
            #riga contabile "A" - iva
            if self.totimposta:
                body.CreateNewRow()
                body.numriga =     numriga
                body.tipriga =     "A"
                body.importo =     abs(self.totimposta)
                if self.totimposta >= 0:
                    body.segno =   segnocp
                else:
                    body.segno =   segnopa
                body.id_pdcpa =    pdcivaid
                body.id_pdccp =    self.id_pdc
                numriga += 1
            
        pdccpid = None
        notomagg = "OMAGGI"
        
        if bt.TIPO_CONTAB == "O":
            
            if reg.config.tipo in 'IC':
                #ordinaria
                #righe contabili "C"
                for tpdc in self._info.totpdc:
                    body.CreateNewRow()
                    body.numriga =     numriga
                    body.tipriga =     "C"
                    if True:#reg.config.tipo == 'I':
                        body.importo = abs(tpdc[magazz.RSPDC_IMPONIB])
                    else:
                        body.importo = abs(tpdc[magazz.RSPDC_IMPORTO])
                    if tpdc[magazz.RSPDC_IMPONIB] >= 0:
                        body.segno =   segnocp
                    else:
                        body.segno =   segnopa
                    body.id_pdcpa =    tpdc[magazz.RSPDC_ID]
                    body.id_pdccp =    self.id_pdc
                    if body.id_pdcpa is None:
                        out = False
                    if pdccpid is None:
                        pdccpid = body.id_pdcpa
                    numriga += 1
        else:
            
            #semplif.
            #righe contabili "I"
            for tpdc in self._info.totpdc:
                body.CreateNewRow()
                body.numriga =     numriga
                if tpdc[magazz.RSPDC_ISOMAGG] and not self._info.magomareg:
                    body.tipriga = "O"
                else:
                    body.tipriga = reg.config.tipo#"I"
                body.importo =     abs(tpdc[magazz.RSPDC_IMPONIB])
                body.imponib =         tpdc[magazz.RSPDC_IMPONIB]
                body.imposta =         tpdc[magazz.RSPDC_IMPOSTA]
                body.indeduc =         tpdc[magazz.RSPDC_INDEDUC]
                body.id_aliqiva =      tpdc[magazz.RSPDC_ALIQ_ID]
                if tpdc[magazz.RSPDC_IMPONIB] >= 0:
                    body.segno =   segnocp
                else:
                    body.segno =   segnopa
                body.id_pdcpa =    tpdc[magazz.RSPDC_ID]
                body.id_pdccp =    self.id_pdc
                body.id_pdciva =   pdcivaid
                if body.id_pdcpa is None:
                    out = False
                if pdccpid is None:
                    pdccpid = body.id_pdcpa
                numriga += 1
            
        if reg.config.tipo in 'IC':
            #riga ritenuta d'acconto
            if bt.CONATTRITACC and self.cfgdoc.sogritacc and self.sogritacc:
                body.CreateNewRow()
                body.numriga =     numriga
                body.tipriga =     "C"
                body.importo =     abs(self.totritacc)
                body.segno =       segnocp
                body.id_pdcpa =    tpdc[magazz.RSPDC_ID]
                body.id_pdccp =    self.id_pdc
                body.segno =       segnopa
                body.id_pdcpa =    self.cfgdoc.id_pdc_ra
                body.solocont =    1
                numriga += 1
            
        #altre righe contabili "C": omaggi e storno
        if self._info.magomareg:
            if bt.TIPO_CONTAB == "O":
                #ordinaria
                impomagg = 0
                pdccpid = None
                pdco = self._info.id_pdc_omaggi
                for tpdc in self._info.totpdx:
                    body.CreateNewRow()
                    body.numriga =     numriga
                    body.tipriga =     "C"
                    body.importo =     abs(tpdc[magazz.RSPDC_IMPONIB])
                    body.segno =       segnocp
                    body.id_pdcpa =    tpdc[magazz.RSPDC_ID]
                    body.id_pdccp =    self.id_pdc
                    if body.id_pdcpa is None:
                        out = False
                    body.note = notomagg
                    body.solocont = 1
                    impomagg += tpdc[magazz.RSPDC_IMPONIB]
                    if pdco is None:
                        pdco = tpdc[magazz.RSPDC_ID]
                    numriga += 1
            else:
                #semplif.
                impomagg = 0
                pdco = self._info.id_pdc_omaggi
                for tpdc in self._info.totpdc:
                    if tpdc[magazz.RSPDC_ISOMAGG]:
                        impomagg += tpdc[magazz.RSPDC_IMPONIB]
                        if pdco is None:
                            pdco = tpdc[magazz.RSPDC_ID]
                    numriga += 1
            if impomagg:
                body.CreateNewRow()
                body.numriga =     numriga
                body.tipriga =     "C"
                body.importo =     abs(impomagg)
                body.segno =       segnopa
                body.id_pdcpa =    pdco
                body.id_pdccp =    self.id_pdc
                body.note =        notomagg
                body.solocont =    1
                if body.id_pdcpa is None:
                    out = False
                pdccpid = body.id_pdcpa
                numriga += 1
    
        #aggiorno c/p su riga prima riga
        body.MoveFirst()
        body.id_pdccp = pdccpid
        
        if bt.TIPO_CONTAB == "O":
            
            if reg.config.tipo in 'IE':
                #ordinaria
                #righe iva "I"
                for tiva in self._info.totiva:
                    body.CreateNewRow()
                    body.numriga = numriga
                    if tiva[magazz.RSIVA_ISOMAGG]:
                        body.note = notomagg
                        body.tipriga = "O"
                    else:
                        body.tipriga = "I"
                    body.imponib =    tiva[magazz.RSIVA_IMPONIB]
                    body.imposta =    tiva[magazz.RSIVA_IMPOSTA]
                    body.indeduc =    0
                    body.importo =    tiva[magazz.RSIVA_IMPORTO]
                    body.segno =      segnocp
                    body.id_aliqiva = tiva[magazz.RSIVA_ID]
                    body.id_pdcpa =   self.id_pdc
                    body.id_pdccp =   pdcivaid
                    body.id_pdciva =  pdcivaid
                    numriga += 1
        
        return out

    def CollegaCont(self):
        regcon = self.regcon
        scad = regcon.scad
        rssca = copy.deepcopy(scad.GetRecordset())
        if regcon.id is not None:
            regcon.Erase()
        self.MakeTotals()
        if self.MakeRegCon():
            #scad._info.rs = rssca
            def InitScadenze(scad):
                del scad._info.rs[:]
                scad._info.rs += list(rssca)
                scad._info.recordCount = len(rssca)
                scad._info.recordNumber = len(rssca)-1
                scad._info.writable = True
                for scad in scad:
                    scad.id = None
                    scad.id_reg = regcon.id
            InitScadenze(regcon.scad)
            coll = regcon.Save()
            self.id_reg = regcon.id
            #self.f_printed = 1
            if not coll:
                #if not self.Save():
                    #raise Exception, \
                          #"Problema in collegamento contabile:\n%s"\
                          #% repr(regcon.GetError())
            #else:
                if regcon.IsDuplicated() and \
                   regcon.GetDuplicatedKeyNumber() == 2:
                    err, msg = NumProtIvaEsiste, 'Protocollo IVA esistente'
                else:
                    err, msg = Exception, repr(regcon.GetError())
                regcon.Erase()
                self.MakeRegCon()
                InitScadenze(regcon.scad)
                raise err, msg
            return True
        else:
            raise Exception,\
                  """Sono presenti righe che non puntano ad alcun sottoconto """\
                  """per la contabilizzazione del documento."""
    
    def GetPdcIva(self, reg=None, id_regiva=None):
        pdcid = cod = None
        if reg is None:
            if id_regiva is None:
                id_regiva = self.GetRegIva()
#            if id_regiva is None:
#                raise Exception, "Registro IVA non definito"
            regiva = adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
            regiva.Get(id_regiva)
#            if regiva.IsEmpty():
#                raise Exception, "Registro IVA non trovato"
        else:
            regiva = reg.regiva
        regivatip = regiva.tipo
        for mov in self.mov:
            if mov.id_aliqiva is not None:
                if mov.iva.tipo == 'C':
                    if regivatip != "A":
                        raise Exception, "Impossibile usare l'aliquota %s, riservata agli acquisti intracomunitari, se il registro non e' di tipo Acquisti" % mov.iva.codice
                    cod = "ivaacqcee"
                    break
                elif mov.iva.tipo == 'S':
                    if regivatip != "V":
                        raise Exception, "Impossibile usare l'aliquota %s, riservata alle vendite in sospensione di imposta, se il registro non e' di tipo Vendite" % mov.iva.codice
                    cod = "ivavensos"
                    break
        if cod is None:
            if (regivatip or ' ') in "AVC":
                if   regivatip == "A":
                    cod = "ivaacq"
                elif regivatip == "V":
                    cod = "ivaven"
                elif regivatip == "C":
                    cod = "ivacor"
            else:
                cod = "ivapro"
        autom = self._info.autom
        autom.ClearFilters()
        autom.AddFilter("codice=%s", cod)
        autom.Retrieve()
        pdcid = autom.aut_id
        if pdcid is None and regivatip is None:
            #non trovato automatismo per iva proforma, prendo iva vendite
            cod = 'ivaven'
            autom.ClearFilters()
            autom.AddFilter("codice=%s", cod)
            autom.Retrieve()
            pdcid = autom.aut_id
        return pdcid
    
    def GetAnag(self):
        out = None
        tipo = self.pdc.tipana.tipo
        if tipo is None:
            dbtip = adb.DbTable(bt.TABNAME_PDCTIP, "tipana")
            if dbtip.Get(self.cfgdoc.id_pdctip):
                tipo = dbtip.tipo
            del dbtip
        tabanag = bt.TableName4TipAna(tipo)
        if tabanag is None:
            out = self.pdc
        else:
            anag = adb.DbTable(tabanag, "anag")
            if tabanag in (bt.TABNAME_CLIENTI,
                           bt.TABNAME_FORNIT):
                anag.AddJoin(\
                    bt.TABNAME_MODPAG,  "modpag", idLeft="id_modpag",\
                    join=adb.JOIN_LEFT)
                anag.AddJoin(\
                    'x4.stati',         "stato",  idLeft="id_stato",\
                    join=adb.JOIN_LEFT)
                anag.AddJoin(\
                    bt.TABNAME_SPEINC,  "spese",  idLeft="id_speinc",\
                    join=adb.JOIN_LEFT)
                anag.AddJoin(\
                    bt.TABNAME_ZONE,    "zona",   idLeft="id_zona",\
                    join=adb.JOIN_LEFT)
                b = anag.AddMultiJoin(\
                    bt.TABNAME_BANCF,   "banche", idRight="id_pdc",\
                    join=adb.JOIN_LEFT)
                anag.bancf = b #fix non togliere alias
                b.AddOrder("banche.pref", adb.ORDER_DESCENDING)
                if self.pdc.id is None:
                    b.AddFilter("banche.id_pdc<0")
                if tabanag == bt.TABNAME_CLIENTI:
                    anag.AddJoin(\
                        bt.TABNAME_AGENTI, "agente",   idLeft="id_agente",\
                        join=adb.JOIN_LEFT)
                    anag.AddJoin(\
                        bt.TABNAME_TIPLIST, "tiplist", idLeft="id_tiplist",\
                        join=adb.JOIN_LEFT)
                    anag.AddJoin(\
                        bt.TABNAME_STATCLI, "status",  idLeft="id_status",\
                        join=adb.JOIN_LEFT)
                else:
                    anag.AddJoin(\
                        bt.TABNAME_STATFOR, "status",  idLeft="id_status",\
                        join=adb.JOIN_LEFT)
                d = anag.AddMultiJoin(\
                    bt.TABNAME_DESTIN, "dest",   idRight="id_pdc",\
                    join=adb.JOIN_LEFT)
                d.AddOrder("dest.pref", adb.ORDER_DESCENDING)
                if self.pdc.id is None:
                    d.AddFilter("dest.id_pdc<0")
            anag.Get(self.pdc.id)
            out = anag
        return out
    
    def GetAnagPrint(self, field):
        """
        Ritorna l'informazione specificata in C{field} dell'anagrafica da 
        stampare come dati di spedizione della merce o del documento, a seconda 
        della richiesta o meno dei dati di accompagnamento.
        """
        if not 'anag' in dir(self._info):
            return None
        anag = self._info.anag
        dest = self.dest
        assert isinstance(anag, adb.DbTable)
        assert isinstance(dest, adb.DbTable)
        try:
            if self.config.askdatiacc == 'X':
                #dati accompagnatori richiesti
                if getattr(self, 'enable_nocodedes', False):
                    #considero il estemporaneo
                    return getattr(self, 'nocodedes_%s' % field) or ''
                elif dest.id is not None:
                    #considero il destinatario
                    return getattr(dest, field) or ''
                else:
                    if field in ('codice', 'descriz'):
                        #considero dati del sottoconto
                        return getattr(self.pdc, field)
                    else:
                        #considero dati dell'anagrafica
                        return getattr(anag, field)
            else:
                #no dati accompagnatori
                if anag.spdind:
                    #considero indirizzo di spedizione documenti
                    return {'descriz':   anag.spddes or self.pdc.descriz,
                            'indirizzo': anag.spdind,
                            'cap':       anag.spdcap,
                            'citta':     anag.spdcit,
                            'prov':      anag.spdpro}[field] or ''
                else:
                    if field in ('codice', 'descriz'):
                        #considero dati del sottoconto
                        return getattr(self.pdc, field)
                    else:
                        #considero dati dell'anagrafica
                        return getattr(anag, field)
        except:
            return None
    
    def GetPrintFileName_Normalize(self, x):
        c = True
        x = x.lower().encode('ascii', 'xmlcharrefreplace')
        y = ''
        for n in range(len(x)):
            if x[n] == '.':
                c = True
            if c and x[n].isalpha():
                y += x[n].upper()
                c = False
            elif x[n].isalnum() or x[n].isspace():
                y += x[n]
        return y
    
    def GetPrintPathName(self):
        return '+Documenti %s/%s' % (self.datdoc.year, self.config.toolprint)
    
    def GetPrintFileName(self):
        N = self.GetPrintFileName_Normalize
        td = N(self.config.descriz)
        dd = N(self.pdc.descriz)
        filename = "%s n. %s - %s (%s)" % (td, self.numdoc, dd.upper(), self.pdc.codice)
        return filename
        
    def SendMail_Prepare(self):
        sei = self._info.sendmail_info
        sei.clear()
        if bt.MAGDEMSENDFLAG and self.config.docemail == 1:
            anag = self.GetAnag()
            if hasattr(anag, 'docsemail'):
                if anag.docsemail:
                    if anag.GetTableName() == bt.TABNAME_CLIENTI:
                        desana = 'cliente'
                    elif anag.GetTableName() == bt.TABNAME_FORNIT:
                        desana = 'fornitore'
                    else:
                        desana = 'soggetto'
                    sendem = True
                    msg = """Dalla scheda dell'anagrafica risulta che il %s desidera\n"""\
                    """una copia del documento per posta elettronica, all'indirizzo:\n\n<%s>\n\n""" % (desana, anag.docsemail)
                    if bt.MAGDEMSENDDESC and bt.MAGDEMSENDADDR:
                        sender = '%s <%s>' % (bt.MAGDEMSENDDESC, bt.MAGDEMSENDADDR)
                    else:
                        sender = None
                    if not sender:
                        msg += """Tuttavia, manca l'indicazione del mittente.\n"""
                    body = self.config.txtemail
                    if not body:
                        body = bt.MAGDEMDALLBODY
                    if not body:
                        msg += """Tuttavia, manca il corpo del testo da inserire nel messaggio.\n"""
                    if not sender or not body:
                        msg += """Configurare opportunamente il sistema di invio documenti via email,\n"""\
                        """nonché l'eventuale testo specifico per questo tipo di documento,\n"""\
                        """nel relativo setup della causale.\n\n"""\
                        """Il documento non sarà inviato: correggere le configurazioni e riprovare."""
                        sendem = False
                    sei.request = msg
                    sei.sendfrom = sender
                    sei.sendto = "%s <%s>" % (self.pdc.descriz, anag.docsemail)
                    sei.message = body
                    if sendem:
                        msg += """Confermi la spedizione del documento via email?"""
                        sei.noexemail = bool(anag.noexemail)
                    else:
                        sei.errors = True
        return sei
    
    def SendMail(self, sei, filename):
        if not bt.MAGDEMSENDFLAG:
            return
        sub = "Recapito elettronico documento: %s del %s" % (os.path.split(filename)[1], self.dita(self.datdoc))
        from comm.comsmtp import SendDocumentMail
        sm = SendDocumentMail()
        sm.send(SendFrom=sei.sendfrom,
                SendTo=sei.sendto,
                Subject=sub,
                Message=sei.message,
                Attachments=[filename,])
        self.f_emailed = 1
        cmd = "UPDATE %s SET f_emailed=1 WHERE id=%s" % (bt.TABNAME_MOVMAG_H, self.id)
        self._info.db.Execute(cmd)
        sm.storicizza('Documento', self.id_pdc, self.id)
    
    def GetTraVetInlineDescription(self):
        if getattr(self, 'enable_nocodevet', False):
            if self.nocodevet_descriz:
                out = self.nocodevet_descriz
                ind = self.nocodevet_indirizzo
                cap = self.nocodevet_cap
                cit = self.nocodevet_citta
                prv = self.nocodevet_prov
                if ind: out += (' %s' % ind)
                if cap: out += (' %s' % cap)
                if cit: out += (' %s' % cit)
                if prv: out += (' (%s)' % prv)
                return out
        else:
            travet = self.travet
            if travet.id:
                ind, cap, cit, prv = map(lambda x: getattr(travet, x), 'indirizzo cap citta prov'.split())
                out = travet.descriz
                if ind: out += (' %s' % ind)
                if cap: out += (' %s' % cap)
                if cit: out += (' %s' % cit)
                if prv: out += (' (%s)' % prv)
                return out
        return None


# ------------------------------------------------------------------------------


class DocMag_Differiti(DocMag):
    
    def GetPrintFileName(self):
        def cap(x):
            c = True
            n = 0
            x = x.lower()
            for n in range(len(x)):
                if x[n] == '.':
                    c = True
                if c and x[n].isalpha():
                    x = '%s%s%s' % (x[:n], x[n].upper(), x[n+1:])
                    c = False
            return x
        self.MoveFirst()
        td = cap(self.config.descriz)
        filename = "%s (%s) da n. %s" % (td, self.datdoc.year, self.numdoc)
        self.MoveLast()
        filename += " a n. %s" % self.numdoc
        self.MoveFirst()
        return filename


# ------------------------------------------------------------------------------


class ListinoMancanteException(Exception):
    pass


# ------------------------------------------------------------------------------


class CtrFidoCliente(adb.DbTable):
    
    _doc = None
    _esa = None
    _ddf = None
    _esp = None
    _sco = None
    _pap = None
    _ggs = None
    
    _fidoesp = None
    _fidosco = None
    _fidopap = None
    _fidoggs = None
    
    _cau_id = None
    _cau_cod = None
    _cau_des = None
    _doc_num = None
    _doc_dat = None
    
    _ritardi = {}
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CLIENTI, 'cliente',
                             writable=False)
        self.AddJoin(bt.TABNAME_PDC, 'pdc', idLeft='id', idRight='id')
        #sintesi sulle partite
        self.dbpcf = adb.DbTable(bt.TABNAME_PCF, 'pcf', writable=False)
        self.dbpcf.Synthetize()
        ts = Env.Azienda.Login.dataElab.Format('%Y-%m-%d')
        self.dbpcf.AddTotalOf("IF(pcf.datscad<'%s',pcf.imptot-pcf.imppar,0)"%ts,
                              """scoperto""")
        self.dbpcf.AddTotalOf("pcf.imptot-pcf.imppar", 
                              """esposiz""")
        self.dbpcf.AddTotalOf("IF(pcf.imptot-pcf.imppar>0,1.0,0)",
                              """numpcf_open""")
        self.dbpcf.AddMinimumOf("IF(pcf.imptot-pcf.imppar>0,pcf.datscad,NULL)",
                                """farpcf_date""")
        self.dbpcf.Reset()
        #per elenco partite
        self.dbscad = dbc.PdcScadenzario()
        self.dbscad.mastro.AddFilter('mastro.imptot=mastro.imppar')
        def GetRitardoPag():
            out = 0
            p = self.dbscad.GetPartite()
            if p.id in self._ritardi:
                out = self._ritardi[p.id]
            return out
        self.dbscad.GetRitardoPag = GetRitardoPag
        #per determinazione ritardi di pagamento
        self.dbpag = p = adb.DbTable(bt.TABNAME_CONTAB_S, 'scad', 
                                     fields='id_reg,id_pcf')
        p.AddJoin(bt.TABNAME_CONTAB_H, 'reg', fields=None)
        p.AddJoin(bt.TABNAME_PCF, 'pcf', fields='datscad')
        p.AddFilter('reg.tipreg="S"')
        p.AddGroupOn('pcf.id')
        p.AddMaximumOf('reg.datreg')
        #per totalizzazione ddt da fatturare
        self._dbddf = adb.DbTable(bt.TABNAME_MOVMAG_H, 'ddf', writable=False)
        self._dbddf.Synthetize()
        self._dbddf.AddTotalOf('ddf.totimporto')
        #elenco tipi documento ddt da fatturare
        self._ddr = []
        cfg = adb.DbTable(bt.TABNAME_CFGMAGDOC, 'cfg', writable=False)
        ddf = adb.DbTable(bt.TABNAME_CFGFTDDR, 'ddf', writable=False)
        ddf.Retrieve()
        for d in ddf:
            if d.f_attivo:
                cfg.Retrieve('cfg.id=%s', d.id_docrag)
                if cfg.checkfido:
                    self._ddr.append(d.id_docrag)
    
    def Reset(self):
        adb.DbTable.Reset()
        self._fidoesp =\
        self._fidosco =\
        self._fidopap =\
        self._fidoggs =\
        self._doc =\
        self._esa =\
        self._ddf =\
        self._esp =\
        self._sco =\
        self._pap =\
        self._ggs = None
    
    def CheckFido(self, idcli, exclude=None, impadd=0, doc_id_ex=None):
        self.Get(idcli)
        self._fidosco = self.fido_maximp
        self._fidoesp = self.fido_maxesp
        self._fidopap = self.fido_maxpcf
        self._fidoggs = self.fido_maxggs
        p = self.dbpcf
        if p.min_farpcf_date is None:
            self._ggs = 0
        p.ClearFilters()
        p.AddFilter('pcf.id_pdc=%s', idcli)
        if exclude:
            p.AddFilter('NOT (pcf.id_caus=%s AND pcf.datdoc=%s AND pcf.numdoc=%s)',
                        exclude['cau_id'],
                        exclude['datdoc'],
                        exclude['numdoc'])
            self._cau_id = exclude['cau_id']
            self._cau_cod = exclude['cau_cod']
            self._cau_des = exclude['cau_des']
            self._doc_dat = exclude['datdoc']
            self._doc_num = exclude['numdoc']
        p.Retrieve()
        self._doc = impadd
        self._sco = p.total_scoperto or 0
        self._esa = p.total_esposiz or 0
        self._ddf = 0
        if self._ddr:
            ddf = self._dbddf
            ddf.ClearFilters()
            ddf.AddFilter('ddf.id_pdc=%s', self.id)
            ddf.AddFilter('ddf.id_tipdoc IN (%s)' % ','.join(map(str, self._ddr)))
            ddf.AddFilter('ddf.f_ann IS NULL OR ddf.f_ann<>1')
            ddf.AddFilter('ddf.f_acq IS NULL OR ddf.f_acq<>1')
            if doc_id_ex:
                ddf.AddFilter('ddf.id<>%s', doc_id_ex)
            ddf.Retrieve()
            self._ddf = ddf.total_totimporto or 0
        self._esp = self._esa+self._ddf
        self._pap = p.total_numpcf_open or 0
        if p.min_farpcf_date is None:
            self._ggs = 0
        else:
            dy,dm,dd = map(int, p.min_farpcf_date.split('-'))
            dd = Env.Azienda.Login.dataElab-Env.DateTime.Date(dy,dm,dd)
            self._ggs = dd.days
        if exclude:
            self._pap += 1
        if impadd:
            self._esp += impadd
        out = 'OK'
        evf = 'eccedente il valore del fido'
        if self.fido_maximp and self._sco>self.fido_maximp:
            out = 'Totale partite scadute %s' % evf
        elif self.fido_maxesp and self._esp>self.fido_maxesp:
            out = 'Totale saldo partite aperte %s' % evf
        elif self.fido_maxpcf and self._pap>self.fido_maxpcf:
            out = 'Numero partite aperte %s' % evf
        elif self.fido_maxggs and self._ggs>self.fido_maxggs:
            out = 'La partita aperta scaduta più vecchia è %s' % evf
        self._ritardi.clear()
        self.dbpag.Retrieve('pcf.id_pdc=%s', idcli)
        for p in self.dbpag:
            if p.max_datreg and p.pcf.datscad:
                d = p.max_datreg-p.pcf.datscad
                gr = int(d.days)
                if gr>0:
                    self._ritardi[p.pcf.id] = gr
        return out


# ------------------------------------------------------------------------------


class Movim(adb.DbTable):
    """
    DbTable movimenti, provvede i metodi per valutarne lo stato di
    evasione.  Visto che Movim è utilizzato sia per il dettaglio dei 
    movimenti del prodotto che per il dettaglio dei movimenti che 
    hanno evaso il singolo movimento del prodotto, è gestita 
    l'intera catena di evasione dei documenti:
    prod         => prodotto
    prod.mov     => movimento/i 'x' del prodotto
    prod.mov.eva => movimento/i 'y' che hanno evaso il movimento 'x'
    Esempio:
    prod             (pippo)
    prod.mov         (ordine)
    prod.mov.eva     (ddt)
    prod.mov.eva.eva (fattura)
    """
    def __init__(self, *args, **kwargs):
        
        adb.DbTable.__init__(self, *args, **kwargs)
        
        pro = self.AddJoin(\
            bt.TABNAME_PROD,      "pro", join=adb.JOIN_LEFT)
        
        iva = self.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva", join=adb.JOIN_LEFT)
        
        doc = self.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "doc")
        
        mag = doc.AddJoin(\
            bt.TABNAME_MAGAZZ,    "mag")
        
        pdc = doc.AddJoin(\
            bt.TABNAME_PDC,       "pdc")
        
        agente = doc.AddJoin(\
            bt.TABNAME_AGENTI,    "agente", join=adb.JOIN_LEFT)
        
        tipdoc = doc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        tipmov = self.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov")
        
        modpag = doc.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag", join=adb.JOIN_LEFT)
        
        speinc = doc.AddJoin(\
            bt.TABNAME_SPEINC,    "spese", join=adb.JOIN_LEFT)
        
        bancf = doc.AddJoin(\
            bt.TABNAME_BANCF,     "bancf", join=adb.JOIN_LEFT)
    
    def TotEvasQta(self):
        """
        Restituisce il totale della quantità evasa.
        """
        try:
            q = self.eva._GetFieldIndex("qta")
            out = sum( [x[q] for x in self.eva.GetRecordset()] )
        except:
            out = 0
        return out
    
    def TotEvasImporto(self):
        """
        Restituisce il totale dell'importo evaso.
        """
        try:
            i = self.eva._GetFieldIndex("importo")
            out = sum( [x[i] for x in self.eva.GetRecordset()] )
        except:
            out = 0
        return out
    
    def TotEvasImpNoSc(self):
        """
        Restituisce il totale dell'importo evaso, senza sconti: qta*prezzo.
        """
        try:
            q = self.eva._GetFieldIndex("qta")
            p = self.eva._GetFieldIndex("prezzo")
            out = sum([ x[q] * x[p] for x in self.eva.GetRecordset()] )
        except:
            out = 0
        return out
    
    def EvasoTutto(self):
        """
        Restituisce C{True} se la sommatoria delle quantità dei
        movimenti di evasione è pari alla quantità di origine.
        """
        return self.TotEvasQta() == self.qta
    
    def EvasoParz(self):
        """
        Restituisce C{True} se c'è almeno un movimento di evasione.
        """
        return self.TotEvasQta() > 0
    
    def InEssere(self):
        """
        Restituisce C{True} se il movimento ed il relativo documento
        non sono annullato e il movimento non è ancora interamente
        evaso.
        """
        return not (self.f_ann == 1 or self.doc.f_ann == 1 or\
                    self.doc.f_acq == 1 or self.EvasoTutto())


# ------------------------------------------------------------------------------


class ElencoMovim(Movim):
    
    def __init__(self, **kwargs):
        
        if not 'writable' in kwargs:
            kwargs['writable'] = False
        Movim.__init__(self, bt.TABNAME_MOVMAG_B, "mov", **kwargs)
        
        self.AddField("mov.importo*(tipmov.tipologia='M')", "impmerce")
        self.AddField("mov.importo*(tipmov.tipologia='S')", "impspese")
        self.AddField("mov.importo*(tipmov.tipologia='V')", "impservi")
        self.AddField("mov.importo*(tipmov.tipologia='T')", "imptrasp")
        self.AddField("mov.importo*(tipmov.tipologia='I')", "impscrip")
        self.AddField("mov.importo*(tipmov.tipologia='E')", "impscmce")
        self.AddField("mov.importo*(tipmov.tipologia='O')", "impomagg")
        
        self.AddOrder("doc.datreg")
        self.AddOrder("tipdoc.codice")
        self.AddOrder("doc.numdoc")
        self.AddOrder("mov.numriga")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class ElencoMovimEva(Movim):
    def __init__(self):
        Movim.__init__(self, bt.TABNAME_MOVMAG_B, "mov", writable=False)
        #evasioni
        eva = self.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "eva",  idLeft="id", idRight="id_moveva",\
            join=adb.JOIN_LEFT, fields=None)
        
        #eva.Synthetize()
        self.AddGroupOn("mov.id")
        self.AddTotalOf("eva.qta",            "evas_qta")
        self.AddTotalOf("eva.importo",        "evas_importo")
        self.AddTotalOf("eva.qta*eva.prezzo", "evas_implord")
        self.AddCountOf("eva.id",             "evas_movim")
        
        self.AddOrder("doc.datreg")
        self.AddOrder("doc.id_tipdoc")
        self.AddOrder("doc.numdoc")
        self.AddOrder("mov.numriga")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class ElencoDocum(adb.DbTable):
    
    def __init__(self):
        
        adb.DbTable.__init__(\
            self,\
            bt.TABNAME_MOVMAG_H, "doc", writable=False)
        
        tipdoc = self.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        mag = self.AddJoin(\
            bt.TABNAME_MAGAZZ,    "magazz")
        
        pdc = self.AddJoin(\
            bt.TABNAME_PDC,       "pdc")
        
        tipana = pdc.AddJoin(\
            bt.TABNAME_PDCTIP,    "tipana", idLeft='id_tipo')
        
        modpag = self.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag", join=adb.JOIN_LEFT)
        
        speinc = self.AddJoin(\
            bt.TABNAME_SPEINC,    "speinc", join=adb.JOIN_LEFT)
        
        agente = self.AddJoin(\
            bt.TABNAME_AGENTI,    "agente", join=adb.JOIN_LEFT)
        
        dest = self.AddJoin(\
            bt.TABNAME_DESTIN,    "dest", join=adb.JOIN_LEFT)
        
        self.AddOrder('doc.datreg')
        self.AddOrder('tipdoc.codice')
        self.AddOrder('doc.datdoc')
        self.AddOrder('doc.numdoc')
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class TraVetDocs(ElencoDocum):
    
    def __init__(self):
        ElencoDocum.__init__(self)
        self.AddJoin(bt.TABNAME_TRAVET, 'travet')
        self['pdc'].AddJoin(bt.TABNAME_CLIENTI, 'anacli', idLeft='id', join=adb.JOIN_LEFT)
        self['pdc'].AddJoin(bt.TABNAME_FORNIT, 'anafor', idLeft='id', join=adb.JOIN_LEFT)
        self.Reset()
    
    def GetAnagTable(self):
        pdc = self.pdc
        if pdc.tipana.tipo == "C":
            return pdc.anacli 
        return pdc.anafor
    
    def GetDestAnagTable(self):
        if self.id_dest:
            return self.dest
        return self.GetAnagTable()
        
    def GetSpedIndirizzo(self):
        return getattr(self.GetDestAnagTable(), 'indirizzo', None)
    
    def GetSpedCAP(self):
        return getattr(self.GetDestAnagTable(), 'cap', None)
    
    def GetSpedCitta(self):
        return getattr(self.GetDestAnagTable(), 'citta', None)
    
    def GetSpedProv(self):
        return getattr(self.GetDestAnagTable(), 'prov', None)
    
    def GetTraVetInlineDescription(self):
        travet = self.travet
        if travet.id:
            ind, cap, cit, prv = map(lambda x: getattr(travet, x), 'indirizzo cap citta prov'.split())
            out = travet.descriz
            if ind: out += (' %s' % ind)
            if cap: out += (' %s' % cap)
            if cit: out += (' %s' % cit)
            if prv: out += (' (%s)' % prv)
            return out
        return None


# ------------------------------------------------------------------------------


class ProdMastro(adb.DbTable):
    """
    DbTable movimenti del prodotto.
    Struttura:
    prod: prodotto
       +==>> mov: movimenti
       |       +--> doc: documento di appartenenza
       |       |      +--> tipdoc: setup documento
       |       |      +--> magazz: magazzino di competenza
       |       |      +--> pdc: sottoconto relativo al documento
       |       +--> tipmov: setup movimento
       +--> cat: categoria merce
       +--> gru: gruppo merce
       +==> list: listini del prodotto
    """
    def __init__(self):
        
        adb.DbTable.__init__(self,\
                             bt.TABNAME_PROD,  "prod",\
                             writable=False)
        
        #movimenti
        mov = self.AddMultiJoin(
            bt.TABNAME_MOVMAG_B,  "mov",\
            join=adb.JOIN_LEFT,\
            dbTabClass=Movim)
        
        mov.AddOrder("doc.datreg")
        mov.AddOrder("doc.datdoc")
        mov.AddOrder("doc.numdoc")
        mov.AddOrder("doc.id")
        
        self.Get(-1)
    

# ------------------------------------------------------------------------------


class ProdMastroEva(ProdMastro):
    """
    DbTable movimenti del prodotto.
    Struttura:
    prod: prodotto
       +==>> mov: movimenti
       |       +--> doc: documento di appartenenza
       |       |      +--> tipdoc: setup documento
       |       |      +--> magazz: magazzino di competenza
       |       |      +--> pdc: sottoconto relativo al documento
       |       +--> tipmov: setup movimento
       +--> cat: categoria merce
       +--> gru: gruppo merce
       +==> list: listini del prodotto
    """
    def __init__(self, *args, **kwargs):
        
        ProdMastro.__init__(self, *args, **kwargs)
        
        #movimenti
        mov = self['mov']
        
        #evasioni
        eva = mov.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "eva",  idLeft="id", idRight="id_moveva",\
            join=adb.JOIN_LEFT, fields=None)
        
        mov.AddGroupOn("mov.id")
        mov.AddTotalOf("eva.qta",            "evas_qta")
        mov.AddTotalOf("eva.importo",        "evas_importo")
        mov.AddTotalOf("eva.qta*eva.prezzo", "evas_implord")
        mov.AddCountOf("eva.id",             "evas_movim")
        
        mov.AddOrder("doc.datreg")
        mov.AddOrder("doc.datdoc")
        mov.AddOrder("doc.numdoc")
        mov.AddOrder("doc.id")
        
        self.Get(-1)
    

# ------------------------------------------------------------------------------


VALINV_COSTOULTIMO = 0
VALINV_COSTOMEDIO =  1
#da implementare
VALINV_LIFO =        2
VALINV_FIFO =        3
VALINV_PREZZOUFF =   4
VALINV_PREZZOLIST =  5

VALINV_DEFAULT =     VALINV_COSTOULTIMO


class _InventarioMixin(adb.DbTable):
    
    _imponib = True
    
    def __init__(self, **kwargs):
        
        if not 'writable' in kwargs:
            kwargs['writable'] = False
        adb.DbTable.__init__(self, bt.TABNAME_PROD, 'prod', **kwargs)
        
        tip = self.AddJoin(bt.TABNAME_TIPART,  'tipart',  join=adb.JOIN_LEFT)
        cat = self.AddJoin(bt.TABNAME_CATART,  'catart',  join=adb.JOIN_LEFT)
        gru = self.AddJoin(bt.TABNAME_GRUART,  'gruart',  join=adb.JOIN_LEFT)
        mar = self.AddJoin(bt.TABNAME_MARART,  'marart',  join=adb.JOIN_LEFT)
        iva = self.AddJoin(bt.TABNAME_ALIQIVA, 'aliqiva', join=adb.JOIN_LEFT)
        pdc = self.AddJoin(bt.TABNAME_PDC,     'pdcforn', join=adb.JOIN_LEFT,
                           idLeft='id_fornit', idRight='id')
        frn = pdc.AddJoin(bt.TABNAME_FORNIT,   'fornit',  join=adb.JOIN_LEFT,
                          idLeft='id', idRight='id')
        
        self.total_giac =  0
        
        self._info.g_datalastchi = None
        self._info.g_data = None
        self._info.max_data = None
        self._info.g_magazz = None
        
        self._info.calciva = False
        self._info.valivati = False
        
        self._info.dblis = adb.DbTable(bt.TABNAME_LISTINI, 'lis', 
                                       writable=False)
        self._info.dblis.AddOrder("lis.data", adb.ORDER_DESCENDING)
        
        self._info.dbtli = adb.DbTable(bt.TABNAME_TIPLIST, 'tiplist',
                                       writable=False)
        
        setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable=False)
        if setup.Retrieve('chiave="magdatchi"') and setup.OneRow():
            if setup.data is not None:
                self._info.g_datalastchi = setup.data
    
    def ClearFilters(self):
        raise NotImplementedError
    
    def SetDataStart(self, data):
        self._info.g_datalastchi = data
        self._SetFilters()
    
    def SetDataInv(self, data):
        self._info.g_data = data
        self._SetFilters()
    
    def SetMagazz(self, id_magazz):
        self._info.g_magazz = id_magazz
        self._SetFilters()
    
    def Valore(self, tipo=VALINV_DEFAULT, id_lis=None, numlis=None):
        out = None
        if   tipo == VALINV_COSTOULTIMO:
            out = self.costo
            scorp = bt.MAGSCORPCOS
            
        elif tipo == VALINV_COSTOMEDIO:
            try:
                out =\
                    (self.total_iniv + self.total_carv)/\
                    (self.total_ini  + self.total_car )
                scorp = bt.MAGSCORPCOS
            except ZeroDivisionError:
                out = 0
                scorp = None
            
        elif tipo == VALINV_PREZZOUFF:
            out = self.prezzo
            scorp = bt.MAGSCORPPRE
            
        elif tipo == VALINV_PREZZOLIST:
            out = None
            lis = self._info.dblis
            lis.ClearFilters()
            lis.AddFilter("lis.id_prod=%s", self.id)
            if self._info.g_data:
                lis.AddFilter("lis.data<=%s", self._info.g_data)
            lis.AddLimit(1)
            lis.Retrieve()
            if numlis is None:
                tli = self._info.dbtli
                tli.Retrieve('tiplist.id=%s', id_lis)
                numlis = int(tli.tipoprezzo)
            out = getattr(lis, 'prezzo%d' % numlis)
            scorp = bt.MAGSCORPPRE
            
        else:
            raise """Tipo di valorizzazione da implementare"""
        
        if out:
            perciva = round((self.aliqiva.perciva or 0)/100, 2)
            if not scorp and self._info.calciva:
                #il valore è imponibile, e si vuole ivato: aggiungo iva
                out = round(out*(1+perciva), 2)
            elif scorp and not self._info.calciva:
                #il valore è ivato, e si vuole imponibile: scorporo iva
                out = round(out/(1+perciva), 2)
        
        self._info.valivati = scorp or self._info.calciva
        
        return out or 0
    
    def SetCalcIva(self, calciva):
        self._info.calciva = calciva

    def Valorizza(self, tipo=VALINV_DEFAULT, id_lis=None, numlis=None):
        return self.total_giac * self.Valore(tipo, id_lis, numlis)
    

# ------------------------------------------------------------------------------


class MovimTable(adb.DbTable):
    pass
    #total_giac = 0
    #def _UpdateTableVars(self, *args, **kwargs):
        #out = adb.DbTable._UpdateTableVars(self, *args, **kwargs)
        #self.total_giac =\
            #(self.total_ini or 0) +\
            #(self.total_car or 0) -\
            #(self.total_sca or 0)
        #return out


# ------------------------------------------------------------------------------


class InventarioDaMovim(_InventarioMixin):
    """
    DbTable totalizzazione movimenti prodotto per carico/scarico.
    Struttura:
    prod: prodotto
       +==>> mov: movimenti
       |       +--> doc: documento di appartenenza
       |       |      +--> tipdoc: setup documento
       |       |      +--> magazz: magazzino di competenza
       |       |      +--> pdc: sottoconto relativo al documento
       |       +--> tipmov: setup movimento
       +--> cat: categoria merce
       +--> gru: gruppo merce
       +==> list: listini del prodotto
    """
    
    MovimClass = MovimTable
    
    def __init__(self, ultraTot=None, flatmag=False, **kwargs):
        
        _InventarioMixin.__init__(self, **kwargs)
        
        self._info.flatmag = flatmag
        
        self._info.totdef = [("ini",    "mov.qta*tipmov.aggini"),
                             ("car",    "mov.qta*tipmov.aggcar"),
                             ("sca",    "mov.qta*tipmov.aggsca"),
                             ("giac",   "(mov.qta*tipmov.aggini)+(mov.qta*tipmov.aggcar)-(mov.qta*tipmov.aggsca)"),
                             ("iniv",   "mov.importo*tipmov.agginiv"),
                             ("carv",   "mov.importo*tipmov.aggcarv"),
                             ("scav",   "mov.importo*tipmov.aggscav"),
                             ("cvccar", "mov.qta*tipmov.aggcvccar"),
                             ("cvcsca", "mov.qta*tipmov.aggcvcsca"),
                             ("cvctot", "(mov.qta*tipmov.aggcvccar)-(mov.qta*tipmov.aggcvcsca)"),
                             ("cvfcar", "mov.qta*tipmov.aggcvfcar"),
                             ("cvfsca", "mov.qta*tipmov.aggcvfsca"),
                             ("cvftot", "(mov.qta*tipmov.aggcvfcar)-(mov.qta*tipmov.aggcvfsca)"),
                         ]
        if ultraTot:
            self._info.totdef += ultraTot
        
        if True:#flatmag:
            mov = self.AddJoin(bt.TABNAME_MOVMAG_B, 'mov', idLeft='id', idRight='id_prod', join=adb.JOIN_LEFT, fields=None)
            mov.AddBaseFilter('mov.f_ann IS NULL OR mov.f_ann<>1')
            self.mov = mov
        else:
            mov = self.AddMultiJoin(bt.TABNAME_MOVMAG_B,  "mov", fields=None,
                                    dbTabClass=self.MovimClass)
        
        doc = mov.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "doc", idLeft='id_doc', idRight='id', join=adb.JOIN_LEFT, fields='id_magazz')
        
        if self._info.g_datalastchi:
            mov.AddBaseFilter("doc.datreg>%s", self._info.g_datalastchi)
        
        mov.AddBaseFilter('doc.f_ann IS NULL OR doc.f_ann<>1')
        
        mag = doc.AddJoin(\
            bt.TABNAME_MAGAZZ,    "mag", join=adb.JOIN_LEFT, fields='id,codice,descriz')
        
        pdc = doc.AddJoin(\
            bt.TABNAME_PDC,       "pdc", join=adb.JOIN_LEFT, fields=None)
        
        tipdoc = doc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc", join=adb.JOIN_LEFT, idLeft='id_tipdoc', idRight='id', fields='id,codice,descriz')
        
        tipmov = mov.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov", join=adb.JOIN_LEFT, idLeft='id_tipmov', idRight='id', fields='id,codice,descriz')
        
        self.dbmov = mov
        
        self._MakeGroups()
        
        for name, expr in self._info.totdef:
            self.AddTotalOf(expr, name)
            self.__setattr__("total_%s" % name, 0)
        
        self.AddOrder("prod.codice")
        
        self.Reset()
    
    def ClearFilters(self):
        adb.DbTable.ClearFilters(self)
        self.dbmov.ClearFilters()
    
    def AddMovTables(self, *args):
        pass
    
    def _MakeGroups(self):
        """
        Imposta la rottura e l'ordinamento per magazzino
        """
        self.AddGroupOn('prod.id', 'prod_id')
    
    def _SetFilters(self):
        #if self._info.flatmag:
            #tab = self
        #else:
            #tab = self.mov
        tab = self.dbmov
        tab.ClearFilters()
        m = self._info.g_magazz
        if type(m) in (int, long, float):
            tab.AddFilter("doc.id_magazz=%s", m)
        elif type(m) in (list, tuple):
            tab.AddFilter("doc.id_magazz IN ('%s')" % ','.join(map(str, m)))
        if self._info.g_datalastchi is not None:
            tab.AddFilter("doc.datreg>%s", self._info.g_datalastchi)
        if self._info.g_data is not None:
            tab.AddFilter("doc.datreg<=%s", self._info.g_data)
    
    def _UpdateTableVars(self, *args, **kwargs):
        
        out = adb.DbTable._UpdateTableVars(self, *args, **kwargs)
        
        for name, expr in self._info.totdef:
            name = "total_%s" % name
            #if self._info.flatmag:
                #val = getattr(self, name) or 0
            #else:
                #val = 0
            #setattr(self, name, val)
            setattr(self, name, getattr(self, name) or 0)
        
        ##if not self._info.flatmag:
            
            ##for m in self.mov:
                ##for name, expr in self._info.totdef:
                    ##name = "total_%s" % name
                    ##value = self.__getattr__(name)
                    ##setattr(self, name, value +\
                            ##(getattr(self.mov, name) or 0))
        
        ##self.UpdateGiacenza()
    
    def UpdateGiacenza(self):
        pass
        #self.total_giac = self.total_ini + self.total_car - self.total_sca


# ------------------------------------------------------------------------------


class InventarioPresunto(adb.DbTable):
    
    def __init__(self):
        
        adb.DbTable.__init__(self, bt.TABNAME_PROD, 'prod', fields='id,codice,descriz,costo,prezzo', writable=True)
        
        kwa = {'join':   adb.JOIN_LEFT,
               'fields': None}
        tip = self.AddJoin(bt.TABNAME_TIPART,  'tipart',  **kwa)
        cat = self.AddJoin(bt.TABNAME_CATART,  'catart',  **kwa)
        gru = self.AddJoin(bt.TABNAME_GRUART,  'gruart',  **kwa)
        mar = self.AddJoin(bt.TABNAME_MARART,  'marart',  **kwa)
        iva = self.AddJoin(bt.TABNAME_ALIQIVA, 'aliqiva', **kwa)
        pdc = self.AddJoin(bt.TABNAME_PDC,     'pdcforn', join=adb.JOIN_LEFT, fields=None, idLeft='id_fornit', idRight='id')
        frn = pdc.AddJoin(bt.TABNAME_FORNIT,   'fornit',  join=adb.JOIN_LEFT, fields=None, idLeft='id', idRight='id')
        
        mov = self.AddJoin(bt.TABNAME_MOVMAG_B, 'mov',    join=adb.JOIN_LEFT, fields=None, idLeft='id', idRight='id_prod')
        doc = mov.AddJoin(bt.TABNAME_MOVMAG_H,  'doc',    join=adb.JOIN_LEFT, fields=None, idLeft='id_doc', idRight='id')
        tpd = doc.AddJoin(bt.TABNAME_CFGMAGDOC, 'tipdoc', join=adb.JOIN_LEFT, fields=None, idLeft='id_tipdoc', idRight='id')
        mag = doc.AddJoin(bt.TABNAME_MAGAZZ,    'magazz', join=adb.JOIN_LEFT, fields=None, idLeft='id_magazz', idRight='id')
        tpm = mov.AddJoin(bt.TABNAME_CFGMAGMOV, 'tipmov', join=adb.JOIN_LEFT, fields=None, idLeft='id_tipmov', idRight='id')
        
#        movoc = self.AddJoin(bt.TABNAME_MOVMAG_B,  'movoc', join=adb.JOIN_LEFT, idLeft='id', idRight='id_prod', fields=None)
#        movec = movoc.AddJoin(bt.TABNAME_MOVMAG_B, 'movec', join=adb.JOIN_LEFT, idLeft='id', idRight='id_moveva', fields=None)
        
        self._info.g_datalastchi = None
        setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable=False)
        if setup.Retrieve('chiave="magdatchi"') and setup.OneRow():
            if setup.data is not None:
                self._info.g_datalastchi = setup.data
        
        self.AddBaseFilter('doc.f_ann IS NULL OR doc.f_ann<>1')
        self.AddBaseFilter('mov.f_ann IS NULL OR mov.f_ann<>1')
        if self._info.g_datalastchi:
            self.AddBaseFilter('doc.datreg>%s', self._info.g_datalastchi)
        
        self.AddGroupOn('prod.id')
        
        self._info.totdef = [("ini",      "mov.qta*tipmov.aggini"),
                             ("car",      "mov.qta*tipmov.aggcar"),
                             ("sca",      "mov.qta*tipmov.aggsca"),
                             ("giac",     "(mov.qta*tipmov.aggini)+(mov.qta*tipmov.aggcar)-(mov.qta*tipmov.aggsca)"),
                             ("backfor",  "0.0"),
                             ("backcli",  "0.0"),
                             ("giacpres", "0.0"),]
        
        for name, expr in self._info.totdef:
            self.AddTotalOf(expr, name)
            self.__setattr__("total_%s" % name, 0)
        
        self.AddOrder('prod.codice')
        
        self.Reset()
    
    def Retrieve(self, *args, **kwargs):
        func0 = kwargs.pop('func0', None)
        func1 = kwargs.pop('func1', None)
        func2 = kwargs.pop('func2', None)
        checkgiac = kwargs.pop('checkgiac', False)
        checkofor = kwargs.pop('checkofor', False)
        checkocli = kwargs.pop('checkocli', False)
        checkgpin = kwargs.pop('checkgpin', False)
        out = adb.DbTable.Retrieve(self, *args, **kwargs)
        if out:
            rs = []
            if callable(func0):
                func0(self)
            dbordfor = TotaliEvasioneFornit()
            dbordcli = TotaliEvasioneClienti()
            for n, prod in enumerate(self):
                prod.total_giac = prod.total_giac or 0
                #conto i backorder fornitori
                dbordfor.Retrieve("movord.id_prod=%s", prod.id)
                tb = 0
                for _ in dbordfor:
                    tb += (dbordfor.avg_qtaord or 0) - (dbordfor.total_qtaeva or 0)
                prod.total_backfor = tb
                #conto i backorder clienti
                dbordcli.Retrieve("movord.id_prod=%s", prod.id)
                tb = 0
                for _ in dbordcli:
                    tb += (dbordcli.avg_qtaord or 0) - (dbordcli.total_qtaeva or 0)
                prod.total_backcli = tb
                #giac. presunta
                prod.total_giacpres = prod.total_giac + prod.total_backfor - prod.total_backcli
                #filtro
                if (self.total_giac>0 or not checkgiac) and (self.total_backfor>0 or not checkofor) and (self.total_backcli>0 or not checkocli) and (self.total_giacpres<0 or not checkgpin):
                    rs.append(self.GetRecordset()[n])
                if callable(func1):
                    func1(self, n)
            if callable(func2):
                func2(self)
            self.SetRecordset(rs)
        return out


# ------------------------------------------------------------------------------


class MovimentiConEvasione(Movim):
    
    def __init__(self):
        Movim.__init__(self, bt.TABNAME_MOVMAG_B, "mov", writable=True)
        #evasioni
        eva = self.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "eva",  idLeft="id", idRight="id_moveva",\
            join=adb.JOIN_LEFT, fields=None)
        
        #eva.Synthetize()
        self.AddGroupOn("mov.id")
        self.AddTotalOf("eva.qta", "evas_qta")
        self.AddTotalOf("0.0", "residuo")
        
        self.AddOrder("doc.datreg", adb.ORDER_DESCENDING)
        self.AddOrder("doc.id_tipdoc")
        self.AddOrder("doc.numdoc")
        self.AddOrder("mov.numriga")
        
        self.Reset()
    
    def Retrieve(self, *args, **kwargs):
        out = Movim.Retrieve(self, *args, **kwargs)
        if out:
            for _ in self:
                if (self.f_ann is None or self.f_ann<>1) and (self.doc.f_ann is None or self.doc.f_ann<>1):
                    tr = (self.qta)-(self.total_evas_qta or 0)
                else:
                    tr = 0
                self.total_residuo = tr
        return out


# ------------------------------------------------------------------------------


class TotaliEvasioneClienti(adb.DbTable):
    
    tipana = "cli"
    
    def __init__(self):
        
        movord = adb.DbTable.__init__(self, bt.TABNAME_MOVMAG_B, 'movord', fields=None)
        tipmov = self.AddJoin(bt.TABNAME_CFGMAGMOV,  'tipmov', fields=None, idLeft='id_tipmov', idRight='id')
        docord = self.AddJoin(bt.TABNAME_MOVMAG_H,   'docord', fields=None, idLeft='id_doc',    idRight='id')
        tipdoc = docord.AddJoin(bt.TABNAME_CFGMAGDOC,'tipdoc', fields=None, idLeft='id_tipdoc', idRight='id')
        magord = docord.AddJoin(bt.TABNAME_MAGAZZ,   'magord', fields=None, idLeft='id_magazz', idRight='id')
        moveva = self.AddJoin(bt.TABNAME_MOVMAG_B,   'moveva', fields=None, idLeft='id',        idRight='id_moveva', join=adb.JOIN_LEFT)
        doceva = moveva.AddJoin(bt.TABNAME_MOVMAG_H, 'doceva', fields=None, idLeft='id_doc',    idRight='id',        join=adb.JOIN_LEFT)
        mageva = doceva.AddJoin(bt.TABNAME_MAGAZZ,   'mageva', fields=None, idLeft='id_magazz', idRight='id',        join=adb.JOIN_LEFT)
        
        AG = self.AddGroupOn
        AG('movord.id')
        AG('tipdoc.codice')
        AG('tipdoc.descriz')
        AG('docord.numdoc')
        AG('docord.datdoc')
        
        self.AddAverageOf('movord.qta', 'qtaord')
        self.AddTotalOf('moveva.qta', 'qtaeva')
        
        tpm = adb.DbTable(bt.TABNAME_CFGMAGMOV, 'tipmov')
        tpm.Retrieve('tipmov.aggord%s IN (1,-1)' % self.tipana)
        if tpm.IsEmpty():
            f = 'FALSE'
        elif tpm.OneRow():
            f = 'tipmov.id=%d' % tpm.id
        else:
            f = 'tipmov.id IN (%s)' % ','.join(map(str, [tpm.id for tpm in tpm]))
        self.AddBaseFilter(f)
        self.AddBaseFilter('docord.f_ann IS NULL OR docord.f_ann<>1')
        self.AddBaseFilter('movord.f_ann IS NULL OR movord.f_ann<>1')
        
        self.Reset()


# ------------------------------------------------------------------------------


class TotaliEvasioneFornit(TotaliEvasioneClienti):
    tipana = "for"


# ------------------------------------------------------------------------------


class InventarioDaScheda(_InventarioMixin):
    
    def __init__(self, flatmag=False):
        
        _InventarioMixin.__init__(self)
        
        self._info.flatmag = flatmag
        
        if flatmag:
            pp = self.AddJoin(bt.TABNAME_PRODPRO, 'pp', 
                              idLeft='id', idRight='id_prod',
                              join=adb.JOIN_LEFT)
            tab = self
        else:
            pp = self.AddMultiJoin(bt.TABNAME_PRODPRO, 'pp', 
                                   idLeft='id', idRight='id_prod',
                                   join=adb.JOIN_LEFT)
            tab = pp
        
        mag = pp.AddJoin(bt.TABNAME_MAGAZZ, 'mag', 
                         idLeft='id_magazz', idRight='id', join=adb.JOIN_LEFT)
        
        self._info.totdef = [("ini",    "pp.ini"),
                             ("car",    "pp.car"),
                             ("sca",    "pp.sca"),
                             ("giac",   "pp.ini+pp.car-pp.sca"),
                             ("iniv",   "pp.iniv"),
                             ("carv",   "pp.carv"),
                             ("scav",   "pp.scav"),
                             ("cvccar", "pp.cvccar"),
                             ("cvcsca", "pp.cvcsca"),
                             ("cvctot", "pp.cvccar-pp.cvcsca"),
                             ("cvfcar", "pp.cvfcar"),
                             ("cvfsca", "pp.cvfsca"),
                             ("cvftot", "pp.cvfcar-pp.cvfsca"),]
        
        self._MakeGroups()
        
        for name, expr in self._info.totdef:
            tab.AddTotalOf(expr, name)
            setattr(tab, "total_%s" % name, 0)
        
        self.AddOrder("prod.codice")
        
        self.Reset()
    
    def ClearFilters(self):
        adb.DbTable.ClearFilters(self)
    
    def _SetFilters(self):
        if self._info.flatmag:
            pp = self
        else:
            pp = self['pp']
        pp.ClearFilters()
        m = self._info.g_magazz
        if type(m) in (int, long):
            pp.AddFilter("(pp.id_magazz=%s OR pp.id IS NULL)", m)
        elif type(m) in (list, tuple):
            pp.AddFilter("pp.id_magazz IN ('%s') OR pp.id IS NULL" % ','.join(map(str, m)))
    
    def _MakeGroups(self):
        """
        Imposta la rottura e l'ordinamento per magazzino
        """
        if self._info.flatmag:
            pp = self
            grp = 'prod.id'
        else:
            pp = self['pp']
            grp = 'mag.id'
        pp.ClearGroups()
        pp.AddGroupOn(grp)
    
    def _UpdateTableVars(self, *args, **kwargs):
        out = adb.DbTable._UpdateTableVars(self, *args, **kwargs)
        
        for name, expr in self._info.totdef:
            name = "total_%s" % name
            if self._info.flatmag:
                val = getattr(self, name) or 0
            else:
                val = 0
            setattr(self, name, val)
        
        if not self._info.flatmag:
            for m in self.pp:
                for name, expr in self._info.totdef:
                    name = "total_%s" % name
                    value = self.__getattr__(name)
                    setattr(self, name, value +\
                            (getattr(self.pp, name) or 0))
        
        self.total_giac = self.total_ini + self.total_car - self.total_sca


# ------------------------------------------------------------------------------


class InventarioPrint(adb.DbMem):
    def __init__(self):
        adb.DbMem.__init__(self,'codice,tipo,descriz,desctipo,codcat,descat,forncod,forndes,ini,iniv,car,carv,sca,scav,gia,val,giav')
    

# ------------------------------------------------------------------------------


class SottoscortaPrint(adb.DbMem):
    def __init__(self):
        adb.DbMem.__init__(self,'codice,tipo,descriz,desctipo,gia,sco,fab')
    

# ------------------------------------------------------------------------------


class ProdProgrDaScheda(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PRODPRO, 'pp')
        self.AddJoin(bt.TABNAME_MAGAZZ, 'magazz')
        self.Reset()


# ------------------------------------------------------------------------------


class ProdProgrDaMovim(InventarioDaMovim):
    def __init__(self):
        totdef = [("ordcli",  "mov.qta*tipmov.aggordcli"),
                  ("ordfor",  "mov.qta*tipmov.aggordfor"),
                  ("ordcliv", "mov.importo*tipmov.aggordcli"),
                  ("ordforv", "mov.importo*tipmov.aggordfor")]
        InventarioDaMovim.__init__(self, ultraTot=totdef)
        mov = self.dbmov
        #mov.AddField("mov.qta*tipmov.aggordcli",     'total_ordcli')
        #mov.AddField("mov.qta*tipmov.aggordfor",     'total_ordfor')
        #mov.AddField("mov.importo*tipmov.aggordcli", 'total_ordcliv')
        #mov.AddField("mov.importo*tipmov.aggordfor", 'total_ordforv')
        self.Reset()


# ------------------------------------------------------------------------------


class ProdProgrDaMovimByMag(ProdProgrDaMovim):
    def _MakeGroups(self):
        """
        Imposta la rottura e l'ordinamento per magazzino
        """
        self.ClearGroups()
        self.AddGroupOn("prod.id")
        self.AddGroupOn("mag.codice")
        self.AddGroupOn("mag.descriz")
        self.mov.ClearOrders()
        self.mov.AddOrder("mag.codice")


# ------------------------------------------------------------------------------


class ProdProgrDaMovimByMov(ProdProgrDaMovim):
    def _MakeGroups(self):
        """
        Imposta la rottura e l'ordinamento per movimento
        """
        self.ClearGroups()
        self.AddGroupOn("prod.id")
        self.AddGroupOn("tipdoc.codice")
        self.AddGroupOn("tipdoc.descriz")
        self.AddGroupOn("tipmov.codice")
        self.AddGroupOn("tipmov.descriz")
        self.mov.ClearOrders()     
        self.mov.AddOrder("tipdoc.codice")
        self.mov.AddOrder("tipmov.codice")


# ------------------------------------------------------------------------------


class ProdProgrEvas(adb.DbTable):
    def __init__(self):
        #vengono considerati i movimenti di evasione, collegati a quelli
        #originali
        adb.DbTable.__init__(self,\
            bt.TABNAME_MOVMAG_B,  "mov", writable=False, fields=None)
        
        doc = self.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "doc", idLeft='id_doc')
        
        tpd = doc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        tpm = self.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov", idLeft='id_tipmov')
        
        mag = doc.AddJoin(\
            bt.TABNAME_MAGAZZ,    "magazz")
        
        pro = self.AddJoin(\
            bt.TABNAME_PROD,      "prod", join=adb.JOIN_LEFT)
        
        iva = self.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva", join=adb.JOIN_LEFT)
        
        #collegamento ai movimenti di origine
        movbase = self.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "movbase", idLeft="id_moveva", idRight="id",\
            fields=None)
        tmvbase = movbase.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tmvbase", idLeft="id_tipmov", idRight="id",\
            join=adb.JOIN_LEFT)
        docbase = movbase.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "docbase", idLeft='id_doc')
        tpdbase = doc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tpdbase", idLeft='id_tipdoc')
        
        self.AddGroupOn("mov.id_prod")
        self.AddTotalOf("mov.qta*tmvbase.aggini",        "evasini")
        self.AddTotalOf("mov.qta*tmvbase.aggcar",        "evascar")
        self.AddTotalOf("mov.qta*tmvbase.aggsca",        "evassca")
        self.AddTotalOf("mov.importo*tmvbase.agginiv",   "evasiniv")
        self.AddTotalOf("mov.importo*tmvbase.aggcarv",   "evascarv")
        self.AddTotalOf("mov.importo*tmvbase.aggscav",   "evasscav")
        self.AddTotalOf("mov.qta*tmvbase.aggordcli",     "evasordcli")
        self.AddTotalOf("mov.qta*tmvbase.aggordfor",     "evasordfor")
        self.AddTotalOf("mov.importo*tmvbase.aggordcli", "evasordcliv")
        self.AddTotalOf("mov.importo*tmvbase.aggordfor", "evasordforv")
        #c/v
        self.AddTotalOf("mov.qta*tmvbase.aggcvccar",     "evascvccar")
        self.AddTotalOf("mov.qta*tmvbase.aggcvcsca",     "evascvcsca")
        self.AddTotalOf("mov.qta*tmvbase.aggcvfcar",     "evascvfcar")
        self.AddTotalOf("mov.qta*tmvbase.aggcvfsca",     "evascvfsca")
        
        #self.AddBaseFilter("movbase.f_ann IS NULL AND movbase.f_ann<>1")
        #self.AddBaseFilter("docbase.f_ann IS NULL AND docbase.f_ann<>1")
        self.AddBaseFilter("mov.f_ann=0")
        self.AddBaseFilter("doc.f_ann=0")
        
        self.Get(-1)
   
    
# ------------------------------------------------------------------------------


class RiepDocAcquis(adb.SubDbTable):
    """
    Individua i documenti con la sintesi della loro evasione.
    mov.*
      +-> doc.*
      !     +-> pdc.*
      !     +-> dest.*
      +-> eva.-
      !     +-> tmveva.*
      +->> totacq: total_qtaorig totale qta documento
                   total_qtaevas totale qta evase sul documento
                   total_valorig totale importi documento
                   total_valevas totale importi evasi sul documento
    Esempio:
    x = RiepDocAcquis()
    x.mov.doc       documento
    x.mov.doc.pdc   pdc
    x.mov.doc.dest  destinatario
    x.total_qtaorig totale qta documento
    x.total_qtaevas totale qta evase sul documento
    x.total_valorig totale importi documento
    x.total_valevas totale importi evasi sul documento
    x.mov.doc.AddFilter("doc.id_pdc=%s", ...)  per filtrare il pdc
    x.mov.doc.AddFilter("doc.id_dest=%s", ...) per filtrare il destinatario ecc.
    
    Per limitare i documenti in base al loro stato di evasione:
    x.AddHaving("qtaevas IS NULL") solo documenti che non sono stati mai evasi,
                                   neanche parzialmente
    x.AddHaving("qtaevas>0")       solo documenti che sono stati parzialmente o 
                                   totalmente evasi
    x.AddHaving("qtaevas=qtaorig") solo documenti completamente evasi
    """
    def __init__(self):
        
        mov = adb.DbTable(\
            bt.TABNAME_MOVMAG_B,  "mov", writable=False,
            fields='id,id_doc,qta,prezzo,sconto1,sconto2,sconto3,sconto4,sconto5,sconto6')
        mov.AddFilter("mov.f_ann IS NULL or mov.f_ann<>1")
        
        doc = mov.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "doc", idLeft="id_doc", idRight="id", 
            fields='id_tipdoc,id_pdc,id_dest,datdoc,numdoc,datreg')
        mov.AddFilter("(doc.f_ann IS NULL or doc.f_ann<>1) AND (doc.f_acq IS NULL or doc.f_acq<>1)")
        
        pdc = doc.AddJoin(\
            bt.TABNAME_PDC,       "pdc", fields='id,codice,descriz')
        
        des = doc.AddJoin(\
            bt.TABNAME_DESTIN,    "dest", idLeft='id_dest', idRight='id',
            join=adb.JOIN_LEFT, fields='id,codice,descriz')
        
        eva = mov.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "eva", idLeft="id", idRight="id_moveva",\
            fields=None, join=adb.JOIN_LEFT)
        #eva.AddFilter("eva.f_ann IS NULL OR eva.f_ann<>1")
        
        evatmv = eva.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tmveva", idLeft="id_tipmov", idRight="id",\
            join=adb.JOIN_LEFT, fields=None)
        
        mov.AddGroupOn("mov.id", 'mov_id_group')
        mov.AddTotalOf("""eva.qta""",                "qtaeva")
        mov.AddTotalOf("""eva.qta*eva.prezzo"""\
                       """*(100-eva.sconto1)/100"""\
                       """*(100-eva.sconto2)/100"""\
                       """*(100-eva.sconto3)/100"""\
                       """*(100-eva.sconto4)/100"""\
                       """*(100-eva.sconto5)/100"""\
                       """*(100-eva.sconto6)/100""", "valeva")
        mov.AddOrder("doc.numdoc")
        mov.Reset()
        
        adb.SubDbTable.__init__(self, mov, "totacq")#, debug=True)
        
        self.AddGroupOn("totacq.mov_id_doc")
        self.AddTotalOf("""totacq.mov_qta""",                "qtaorig")
        self.AddTotalOf("""totacq.mov_total_qtaeva""",       "qtaevas")
        self.AddTotalOf("""totacq.mov_qta*totacq.mov_prezzo"""\
                        """*(100-totacq.mov_sconto1)/100"""\
                        """*(100-totacq.mov_sconto2)/100"""\
                        """*(100-totacq.mov_sconto3)/100"""\
                        """*(100-totacq.mov_sconto4)/100"""\
                        """*(100-totacq.mov_sconto5)/100"""\
                        """*(100-totacq.mov_sconto6)/100""", "valorig")
        self.AddTotalOf("""totacq.mov_total_valeva""",       "valevas")
        #self.SetDebug()

    def SetAcqStatus(self, aperti=True, parz=True, chiusi=True):
        self.ClearHavings()
        hav = ""
        if aperti:
            if hav: hav += " OR "
            hav += "(total_qtaevas IS NULL OR total_qtaevas=0)"
        if parz:
            if hav: hav += " OR "
            hav += "(total_qtaevas<total_qtaorig)"
        if chiusi:
            if hav: hav += " OR "
            hav += "(total_qtaevas>=total_qtaorig)"
        if hav:
            self.AddHaving(hav)

# ------------------------------------------------------------------------------


class RiepMovAcquis(adb.DbTable):
    """
    Elenco movimenti con dati di sintesi dell'evasione
    
    mov
      +-> tipmov
      +-> prod
      +-> iva
      +-> doc
      !     +-> tipdoc
      !     +-> magazz
      !     +-> pdc
      !     +-> dest
      !     +-> agente
      !
      +:: total_qtaeva
    
    mov contiene, oltre a *tutti* i campi di movmag_b, anche:
    - total_qtaeva, sommatoria delle quantità che hanno evaso il movimento
    """
    
    def __init__(self, writable=False):
        
        adb.DbTable.__init__(self,\
            bt.TABNAME_MOVMAG_B,  "mov", writable=writable)
        
        doc = self.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "doc")
        
        tpd = doc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        mag = doc.AddJoin(\
            bt.TABNAME_MAGAZZ,    "magazz")
        
        pdc = doc.AddJoin(\
            bt.TABNAME_PDC,       "pdc")
        
        dest = doc.AddJoin(\
            bt.TABNAME_DESTIN,    "dest", join=adb.JOIN_LEFT)
        
        agente = doc.AddJoin(\
            bt.TABNAME_AGENTI,    "agente", join=adb.JOIN_LEFT)

        tpm = self.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov")
        
        pro = self.AddJoin(\
            bt.TABNAME_PROD,      "prod", join=adb.JOIN_LEFT)
        
        iva = self.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva", join=adb.JOIN_LEFT)
        
        #totalizzazione movimenti evasione
        eva = self.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "eva",    idLeft="id", idRight="id_moveva",\
            fields=None, join=adb.JOIN_LEFT)
        #eva.AddFilter("eva.f_ann IS NULL OR eva.f_ann<>1")
        evatmv = eva.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tmveva", idLeft="id_tipmov", idRight="id",\
            join=adb.JOIN_LEFT)
        
        self.AddField("0.0", "qtaacq") # colonna qta da acquisire x dataentry
        self.AddField("0.0", "impacq") # colonna importo da acquisire x dataentry
        self.AddField("0.0", "annacq") # colonna flag x annullamento residuo
        self.AddField("0.0", "acquis") # colonna flag x acquisizione riga
        self.AddField("0.0", "closed") # colonna flag riga chiusa (x qta/val/des)
        
#        self.AddFilter("mov.f_ann<>1")
#        
#        self.AddOrder("mov.id_doc")
#        self.AddOrder("mov.numriga")
#        
        self.AddGroupOn("mov.id")
#        self.AddTotalOf("mov.qta", "qtamov")
        self.AddTotalOf("eva.qta", "qtaeva")
        self.AddCountOf("eva.id",  "numovi")
#        
        self.Get(-1)

    def CalcQtaAcq(self):
        m = self
        if m.qta:
            m.qtaacq = m.qta-(m.total_qtaeva or 0)
        else:
            m.qtaacq = None
        m.CalcImpAcq()

    def CalcImpAcq(self):
        m = self
        if m.qtaacq and m.prezzo:
            m.impacq = round(m.qtaacq*m.prezzo\
                             *(100-(m.sconto1 or 0))/100\
                             *(100-(m.sconto2 or 0))/100\
                             *(100-(m.sconto3 or 0))/100\
                             *(100-(m.sconto4 or 0))/100\
                             *(100-(m.sconto5 or 0))/100\
                             *(100-(m.sconto6 or 0))/100, bt.VALINT_DECIMALS)
        else:
            m.impacq = None


# ------------------------------------------------------------------------------


class DocAll(adb.DbTable):
    
    def __init__(self, table=bt.TABNAME_MOVMAG_H, alias='doc', **kwargs):
        
        adb.DbTable.__init__(self, table, alias, **kwargs)
        
        tipdoc = self.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        mag = self.AddJoin(\
            bt.TABNAME_MAGAZZ,    "magazz")
        
        pdc = self.AddJoin(\
            bt.TABNAME_PDC,       "pdc")
        pdctip = pdc.AddJoin(\
            bt.TABNAME_PDCTIP,    "pdctip", idLeft='id_tipo')
        
        dest = self.AddJoin(\
            bt.TABNAME_DESTIN,    "dest",   join=adb.JOIN_LEFT)
        
        modpag = self.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag", join=adb.JOIN_LEFT)
        
        speinc = self.AddJoin(\
            bt.TABNAME_SPEINC,    "speinc", join=adb.JOIN_LEFT)
        
        agente = self.AddJoin(\
            bt.TABNAME_AGENTI,    "agente", join=adb.JOIN_LEFT)
        
        zona = self.AddJoin(\
            bt.TABNAME_ZONE,      "zona",   join=adb.JOIN_LEFT)
        
        bancf = self.AddJoin(\
            bt.TABNAME_BANCF,     "bancf",  join=adb.JOIN_LEFT)
        
        tiplist = self.AddJoin(\
            bt.TABNAME_TIPLIST,   "list",   join=adb.JOIN_LEFT)
        
        tracau = self.AddJoin(\
            bt.TABNAME_TRACAU,    "tracau", join=adb.JOIN_LEFT)
        
        tracur = self.AddJoin(\
            bt.TABNAME_TRACUR,    "tracur", join=adb.JOIN_LEFT)
        
        traasp = self.AddJoin(\
            bt.TABNAME_TRAASP,    "traasp", join=adb.JOIN_LEFT)
        
        trapor = self.AddJoin(\
            bt.TABNAME_TRAPOR,    "trapor", join=adb.JOIN_LEFT)
        
        tracon = self.AddJoin(\
            bt.TABNAME_TRACON,    "tracon", join=adb.JOIN_LEFT)
        
        travet = self.AddJoin(\
            bt.TABNAME_TRAVET,    "travet", join=adb.JOIN_LEFT)
        
        #totalizzazione movimenti
        tot = self.AddJoin(\
            bt.TABNAME_MOVMAG_B,  "tot",    idLeft="id", idRight="id_doc",\
            fields=None)
        
        tipmov = tot.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov", idLeft="id_tipmov", idRight="id")
        
        self.AddOrder("YEAR(%s.datdoc)" % alias)
        self.AddOrder("%s.id_tipdoc" % alias)
        self.AddOrder("%s.numdoc" % alias)
        
        self.AddGroupOn("%s.id" % alias)
        tot.Synthetize()
        tot.AddTotalOf(\
            """IF(tipmov.tipologia IN ('M','S','V','T'), tot.importo, """\
            """IF(tipmov.tipologia='I', -tot.importo, 0))""",\
            "imponib")
        tot.AddTotalOf("IF(tipmov.tipologia='M', tot.importo, 0)", "merce")
        tot.AddTotalOf("IF(tipmov.tipologia='S', tot.importo, 0)", "spese")
        tot.AddTotalOf("IF(tipmov.tipologia='V', tot.importo, 0)", "servi")
        tot.AddTotalOf("IF(tipmov.tipologia='T', tot.importo, 0)", "trasp")
        tot.AddTotalOf("IF(tipmov.tipologia='I', tot.importo, 0)", "scrip")
        tot.AddTotalOf("IF(tipmov.tipologia='E', tot.importo, 0)", "scmce")
        tot.AddTotalOf("IF(tipmov.tipologia='O', tot.importo, 0)", "omagg")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


#class MovAll(adb.DbTable):
    
    #def __init__(self, table=bt.TABNAME_MOVMAG_B, alias='mov', **kwargs):
        
        #adb.DbTable.__init__(self, table, alias, **kwargs)
        
        #tipmov = self.AddJoin(\
            #bt.TABNAME_CFGMAGMOV, "tipmov")
        
        #prod = self.AddJoin(\
            #bt.TABNAME_PROD,      "prod",    join=adb.JOIN_LEFT)
        #prod.AddJoin(\
            #bt.TABNAME_TIPART,    "tipart",  join=adb.JOIN_LEFT)
        #prod.AddJoin(\
            #bt.TABNAME_CATART,    "catart",  join=adb.JOIN_LEFT)
        #prod.AddJoin(\
            #bt.TABNAME_GRUART,    "gruart",  join=adb.JOIN_LEFT)
        
        #iva = self.AddJoin(\
            #bt.TABNAME_ALIQIVA,   "iva",     join=adb.JOIN_LEFT)
        
        #self.AddOrder("%s.id_doc" % alias)
        #self.AddOrder("%s.numriga" % alias)
        
        #self.Get(-1)


class MovAll(adb.DbTable):
    
    def __init__(self, table=bt.TABNAME_MOVMAG_B, alias='mov', **kwargs):
        
        adb.DbTable.__init__(self, table, alias, **kwargs)
        
        tipmov = self.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov")
        
        prod = self.AddJoin(\
            bt.TABNAME_PROD,      "prod",    join=adb.JOIN_LEFT)
        prod.AddJoin(\
            bt.TABNAME_TIPART,    "tipart",  join=adb.JOIN_LEFT)
        prod.AddJoin(\
            bt.TABNAME_CATART,    "catart",  join=adb.JOIN_LEFT)
        prod.AddJoin(\
            bt.TABNAME_GRUART,    "gruart",  join=adb.JOIN_LEFT)
        
        iva = self.AddJoin(\
            bt.TABNAME_ALIQIVA,   "iva",     join=adb.JOIN_LEFT)
        
        doc = self.AddJoin(\
            bt.TABNAME_MOVMAG_H,   "doc")
        
        tipdoc = doc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        mag = doc.AddJoin(\
            bt.TABNAME_MAGAZZ,    "magazz")
        
        pdc = doc.AddJoin(\
            bt.TABNAME_PDC,       "pdc")
        pdctip = pdc.AddJoin(\
            bt.TABNAME_PDCTIP,    "pdctip", idLeft='id_tipo')
        
        dest = doc.AddJoin(\
            bt.TABNAME_DESTIN,    "dest",   join=adb.JOIN_LEFT)
        
        modpag = doc.AddJoin(\
            bt.TABNAME_MODPAG,    "modpag", join=adb.JOIN_LEFT)
        
        speinc = doc.AddJoin(\
            bt.TABNAME_SPEINC,    "speinc", join=adb.JOIN_LEFT)
        
        agente = doc.AddJoin(\
            bt.TABNAME_AGENTI,    "agente", join=adb.JOIN_LEFT)
        
        zona = doc.AddJoin(\
            bt.TABNAME_ZONE,      "zona",   join=adb.JOIN_LEFT)
        
        tiplist = doc.AddJoin(\
            bt.TABNAME_TIPLIST,   "list",   join=adb.JOIN_LEFT)
        
        tracau = doc.AddJoin(\
            bt.TABNAME_TRACAU,    "tracau", join=adb.JOIN_LEFT)
        
        tracur = doc.AddJoin(\
            bt.TABNAME_TRACUR,    "tracur", join=adb.JOIN_LEFT)
        
        traasp = doc.AddJoin(\
            bt.TABNAME_TRAASP,    "traasp", join=adb.JOIN_LEFT)
        
        trapor = doc.AddJoin(\
            bt.TABNAME_TRAPOR,    "trapor", join=adb.JOIN_LEFT)
        
        tracon = doc.AddJoin(\
            bt.TABNAME_TRACON,    "tracon", join=adb.JOIN_LEFT)
        
        travet = doc.AddJoin(\
            bt.TABNAME_TRAVET,    "travet", join=adb.JOIN_LEFT)
        
        self.AddOrder("doc.datdoc")
        self.AddOrder("tipdoc.codice")
        self.AddOrder("doc.numdoc")
        self.AddOrder("tipmov.codice")
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class DettaglioEvasioni(Movim):
    
    def __init__(self, **kwargs):
        
        kwargs['writable'] = True #per giocare con le causali
        Movim.__init__(self, bt.TABNAME_MOVMAG_B, 'mov', **kwargs)
        
        evamov = self.AddJoin(  bt.TABNAME_MOVMAG_B, 'eva',
                             idLeft='id', idRight='id_moveva')
        
        evadoc = evamov.AddJoin(\
            bt.TABNAME_MOVMAG_H,  "evadoc", idLeft='id_doc', idRight='id')
        
        evatpd = evadoc.AddJoin(\
            bt.TABNAME_CFGMAGDOC, "evatpd", idLeft='id_tipdoc', idRight='id')
        
        evatpm = evamov.AddJoin(\
            bt.TABNAME_CFGMAGMOV, "evatpm", idLeft='id_tipmov', idRight='id')
        
        self.Reset()


# ------------------------------------------------------------------------------


class Prodotti(adb.DbTable):
    
    def __init__(self, table=None, alias=None, **kwargs):
        if table is None:
            table = bt.TABNAME_PROD
            alias = 'prod'
        kwargs['writable'] = True
        adb.DbTable.__init__(self, table, alias, **kwargs)
        tipart = self.AddJoin(bt.TABNAME_TIPART,  'tipart', join=adb.JOIN_LEFT)
        catart = self.AddJoin(bt.TABNAME_CATART,  'catart', join=adb.JOIN_LEFT)
        gruart = self.AddJoin(bt.TABNAME_GRUART,  'gruart', join=adb.JOIN_LEFT)
        fornit = self.AddJoin(bt.TABNAME_PDC,     'fornit', join=adb.JOIN_LEFT)
        status = self.AddJoin(bt.TABNAME_STATART, 'status', join=adb.JOIN_LEFT)
        gruprez = self.AddJoin(bt.TABNAME_GRUPREZ, 'gruprez', join=adb.JOIN_LEFT)
        gplbase = gruprez.AddJoin(bt.TABNAME_GRUPREZ, 'gplbase', join=adb.JOIN_LEFT, idLeft='id_lisdagp', idRight='id')
        self.AddOrder('prod.codice')
        self.Reset()
    
    def RicalcolaCosto(self, s1=None, s2=None, s3=None, s4=None, s5=None, s6=None):
        out = False
        gpr = self.gruprez
        if s1 is None:
            if self.sconto1 or self.sconto2 or self.sconto3 or self.sconto4 or self.sconto5 or self.sconto6:
                s1 = self.sconto1 or 0
                s2 = self.sconto2 or 0
                s3 = self.sconto3 or 0
                s4 = self.sconto4 or 0
                s5 = self.sconto5 or 0
                s6 = self.sconto6 or 0
            else:
                s1 = gpr.prcpresco1 or 0
                s2 = gpr.prcpresco2 or 0
                s3 = gpr.prcpresco3 or 0
                s4 = gpr.prcpresco4 or 0
                s5 = gpr.prcpresco5 or 0
                s6 = gpr.prcpresco6 or 0
        if gpr.calcpc == 'C' or (s1 or s2 or s3 or s4 or s5 or s6):
            #aggiorna costo
            if s1 or s2 or s3 or s4 or s5 or s6:
                c = round((self.prezzo or 0)\
                          *(100-s1)/100\
                          *(100-s2)/100\
                          *(100-s3)/100\
                          *(100-s4)/100\
                          *(100-s5)/100\
                          *(100-s6)/100, bt.MAGPRE_DECIMALS)
                if c:
                    self.costo = c
                    out = True
        return out
    
    def RicalcolaPrezzo(self, r1=None, r2=None, r3=None, r4=None, r5=None, r6=None):
        out = False
        gpr = self.gruprez
        if r1 is None:
            if self.ricar1 or self.ricar2 or self.ricar3 or self.ricar4 or self.ricar5 or self.ricar6:
                r1 = self.ricar1 or 0
                r2 = self.ricar2 or 0
                r3 = self.ricar3 or 0
                r4 = self.ricar4 or 0
                r5 = self.ricar5 or 0
                r6 = self.ricar6 or 0
            else:
                r1 = gpr.prccosric1 or 0
                r2 = gpr.prccosric2 or 0
                r3 = gpr.prccosric3 or 0
                r4 = gpr.prccosric4 or 0
                r5 = gpr.prccosric5 or 0
                r6 = gpr.prccosric6 or 0
        if gpr.calcpc == 'P' or (r1 or r2 or r3 or r4 or r5 or r6):
            #aggiorna prezzo
            if r1 or r2 or r3:
                p = round(self.costo\
                          *(100+r1)/100\
                          *(100+r2)/100\
                          *(100+r3)/100\
                          *(100+r4)/100\
                          *(100+r5)/100\
                          *(100+r6)/100, bt.MAGPRE_DECIMALS)
                if p:
                    self.prezzo = p
                    out = True
        return out
    
    def RicalcolaPC(self):
        gpr = self.gruprez
        if gpr.calcpc == 'C' or (self.sconto1 or self.sconto2 or self.sconto3 or self.sconto4 or self.sconto5 or self.sconto6):
            out = 'C', self.RicalcolaCosto()
        elif gpr.calcpc == 'P' or (self.ricar1 or self.ricar2 or self.ricar3 or self.ricar4 or self.ricar5 or self.ricar6):
            out = 'P', self.RicalcolaPrezzo()
        else:
            out = None, None
        return out
    
    def RicalcolaListini(self, lis):
        prezzi = {}
        gpr = self.gruprez
        if gpr.gplbase.id is not None:
            gpr = gpr.gplbase
        for n in range(1,bt.MAGNUMLIS+1):
            p = None
            if gpr.calclis == 'C':
                #listini da costo di acquisto e ricariche
                r = getattr(gpr, 'prclisric%d' % n)
                p = round(self.costo*(100+(r or 0))/100, bt.MAGPRE_DECIMALS)
            elif gpr.calclis == 'P':
                #listini da prezzo al pubblico e sconti
                s = getattr(gpr, 'prclissco%d' % n)
                p = round(self.prezzo*(100-(s or 0))/100, bt.MAGPRE_DECIMALS)
            elif gpr.calclis == 'V':
                #listini a calcolo variabile
                v = getattr(gpr, 'prclisvar%d' % n)
                b = getattr(gpr, 'prclisbas%d' % n)
                if b == 'C':
                    if hasattr(lis, 'p_costo'):
                        x = lis.p_costo
                    else:
                        x = self.costo
                elif b == 'P':
                    x = self.prezzo
                elif b in ''.join(map(lambda x: str(x+1), range(bt.MAGNUMLIS))):
                    x = getattr(lis, 'prezzo%s'%b)
                else:
                    x = None
                if x is not None:
                    p = round(x*(100+v)/100, bt.MAGPRE_DECIMALS)
            p = p or 0
            if p:
                setattr(lis, 'prezzo%d'%n, p)
            else:
                p = getattr(lis, 'prezzo%d'%n)
            if not bt.MAGDATLIS:
                lis.data = Env.Azienda.Login.dataElab
            prezzi[n] = p
        return prezzi


# ------------------------------------------------------------------------------


class Listino(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_LISTINI, 'lis', writable=True)
        pro = self.AddJoin(bt.TABNAME_PROD,   'prod', join=adb.JOIN_RIGHT)
        gpr = pro.AddJoin(bt.TABNAME_GRUPREZ, 'gruprez', join=adb.JOIN_LEFT)
        sts = pro.AddJoin(bt.TABNAME_STATART, 'status', join=adb.JOIN_LEFT, fields='id,codice,descriz', idLeft='id_status', idRight='id')
        tip = pro.AddJoin(bt.TABNAME_TIPART,  'tipart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        cat = pro.AddJoin(bt.TABNAME_CATART,  'catart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        gru = pro.AddJoin(bt.TABNAME_GRUART,  'gruart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        mar = pro.AddJoin(bt.TABNAME_MARART,  'marart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        frn = pro.AddJoin(bt.TABNAME_PDC,     'fornit', join=adb.JOIN_LEFT, fields='id,codice,descriz', idLeft='id_fornit', idRight='id')
        self.AddField('prod.costo',  'p_costo')
        self.AddField('prod.prezzo', 'p_prezzo')
        self.AddOrder('prod.codice')
        self.AddOrder('lis.data', adb.ORDER_DESCENDING)
        self.Reset()
        self._keys = ['p_costo','p_prezzo']
        self._keys += ['prezzo%d'%l for l in range(1,10)]
        self._cols = {}
        for col in self._keys:
            self._cols[col] = copy.copy({'value': None,
                                         'title': None,
                                         'print': False})
    
    def IsEmpty(self):
        out = True
        for n in range(1, bt.MAGNUMLIS+1):
            if getattr(self, 'prezzo%d'%n):
                out = False
                break
        return out
    
    def Columns(self):
        return self._cols
    
    def PrintCol(self, col, do=None):
        if do is not None:
            self._cols[col]['print'] = do
        return self._cols[col]['print']
    
    def GetCols(self):
        c = []
        for name in self._keys:
            if self.PrintCol(name):
                self._cols[name]['value'] = getattr(self, name)
                c.append(self._cols[name])
        return c
    
    def GetPrintColTitle(self, n):
        o = ''
        c = self.GetCols()
        if n<len(c):
            o = c[n]['title']
        return o
    
    def GetPrintColValue(self, n):
        o = 0
        c = self.GetCols()
        if n<len(c):
            o = c[n]['value']
        return o
    

# ------------------------------------------------------------------------------


class ListinoSintesi(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_LISTINI, 'lis', writable=False)
        pro = self.AddJoin(bt.TABNAME_PROD, 'prod', join=adb.JOIN_RIGHT)
        gpr = pro.AddJoin(bt.TABNAME_GRUPREZ, 'gruprez', join=adb.JOIN_LEFT)
        sts = pro.AddJoin(bt.TABNAME_STATART, 'status', join=adb.JOIN_LEFT, fields='id,codice,descriz', idLeft='id_status', idRight='id')
        tip = pro.AddJoin(bt.TABNAME_TIPART,  'tipart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        cat = pro.AddJoin(bt.TABNAME_CATART,  'catart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        gru = pro.AddJoin(bt.TABNAME_GRUART,  'gruart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        mar = pro.AddJoin(bt.TABNAME_MARART,  'marart', join=adb.JOIN_LEFT, fields='id,codice,descriz')
        frn = pro.AddJoin(bt.TABNAME_PDC,     'fornit', join=adb.JOIN_LEFT, fields='id,codice,descriz', idLeft='id_fornit', idRight='id')
        self.Synthetize()
        self.AddGroupOn('lis.data')
        self.AddCountOf('lis.id_prod')
        self.AddOrder('lis.data', adb.ORDER_DESCENDING)
        self.Get(-1)


# ------------------------------------------------------------------------------


class ListiniAttuali(adb.DbMem, iva.IVA):
    """
    Listini in vigore alla data
    prod
    +--> list (listini)
    """
    def __init__(self):
        adb.DbMem.__init__(self, fields=\
                           'tiplisid,tipliscod,listino,imponib,ivato,scprep,riccos,scol1,')
        iva.IVA.__init__(self, adb.db.__database__._dbCon.cursor())
        self.SetRecordset([])
        self._info.dbtli = adb.DbTable(bt.TABNAME_TIPLIST, 'tiplis',
                                       writable=False)
        self._info.dblis = adb.DbTable(bt.TABNAME_LISTINI, 'list', 
                                       writable=False)
        self._info.dblis.AddOrder("data", adb.ORDER_DESCENDING)
        self._info.dbpro = adb.DbTable(bt.TABNAME_PROD, 'prod', 
                                       writable=False)
        self._info.dbtli.AddOrder("codice")
        self._info.dbtli.Retrieve("tipoprezzo IN ('1','2','3','4','5','6','7','8','9')")
    
    def Determina(self, idprod, data=None):
        lis = self._info.dblis
        pro = self._info.dbpro
        lis.ClearFilters()
        lis.AddFilter('list.id_prod=%s', idprod)
        if data is not None:
            lis.AddFilter('list.data<=%s', data)
        lis.Retrieve()
        pro.Retrieve('id=%s', idprod)
        tli = self._info.dbtli
        rs = []
        for n in range(1, bt.MAGNUMLIS+1, 1):
            if tli.Locate(lambda x: x.tipoprezzo == str(n)):
                cl = tli.codice
                dl = tli.descriz
                il = tli.id
            else:
                cl = str(n)
                dl = "LISTINO %d" % n
                il = None
            pre = getattr(lis, 'prezzo%d' % n)
            pre, iva, pri, ind = self.CalcolaIVA(pro.id_aliqiva, pre, decimals=bt.MAGPRE_DECIMALS)
            prp = pro.prezzo or 0
            cos = pro.costo or 0
            spp = 0 #sconto su prezzo al pubblico
            rca = 0 #ricarica su costo d'acquisto
            sl1 = 0 #sconto su listino 1
            gsc = 0 #guadagno su costo d'acquisto
            if pre:
                pl1 = lis.prezzo1 or 0
                try: spp = (prp-pre)/prp*100
                except ZeroDivisionError: pass
                try: rca = (pre/cos-1)*100
                except ZeroDivisionError: pass
                try: sl1 = (pl1-pre)/pl1*100
                except ZeroDivisionError: pass
                try: gsc = (pre-cos)/pre*100
                except ZeroDivisionError: pass
            rs.append((il, cl, dl, pre, pri, spp, rca, sl1, gsc))
        self.SetRecordset(rs)


# ------------------------------------------------------------------------------


class AcqListino(adb.DbMem):
    
    def __init__(self, fields=None, **kwargs):
        """
        I nomi delle colonne vengono convertiti in sole lettere minuscole.
        """
        adb.DbMem.__init__(self, fields.lower(), **kwargs)
    
    def epura(self, func=None):
        """
        Dal file cvs le colonne importate hanno due caratteristiche:
        1) la prima colonna *deve* essere il codice, ma le restanti colonne
           non sono determinabili a priori (il costo, il prezzo ed i vari 
           listini possono essere presenti o meno)
        2) il formato delle colonne costo/prezzo/listini può essere stato
           impostato nel foglio di calcolo come valori decimali, o come stringhe
           dotate di separatori delle migliaia, del simbolo dell'euro ecc.
        Questo metodo ripassa l'intero recordset e, per ogni riga:
        1) determina quali colonne, oltre alla colonna codice, sono presenti;
        2) toglie la formattazione testuale dalle colonne costo/prezzo/listini
           rendendo l'informazione di tipo numerico con decimali.
        """
        #determinazione delle colonne che servono
        i = self._info
        i.cols = {}
        cols = 'codice,costo,prezzo'.split(',')
        cols = list(cols)+['prezzo%d'%(n+1) for n in range(10)]
        for col in cols:
            pos = self._GetFieldIndex(col) 
            if pos >= 0:
                i.cols[col] = pos
        if not 'codice' in self.GetFieldNames():
            raise Exception, "Non trovo colonna codice"
        for n, r in enumerate(i.rs):
            for col in i.cols:
                try:
                    v = r[i.cols[col]]
                    if col == 'codice':
                        if type(v) not in (str, unicode):
                            r[i.cols[col]] = str(v)
                    if col.startswith('costo') or col.startswith('prezzo'):
                        #trovato costo, prezzo o listino
                        #verifico formato ed eventualmente converto in numerico
                        if v is None:
                            v = 0
                        if type(v) in (str, unicode):
                            if ',' in v:
                                v = v.replace(',', '.')
                            sv = v
                            v = ''
                            for n in range(len(sv)):
                                if str.isdigit(sv[n]) or sv[n] == '.':
                                    v += sv[n]
                            if str.count(v, '.')>0:
                                p = len(v)-str.rindex(v, '.')-1
                                div = 10**p
                            else:
                                div = 1
                            v = str.replace(v, '.', '')
                            if v:
                                v = float(v.replace('.',''))/div
                            else:
                                v = 0
                        r[i.cols[col]] = v
                except IndexError:
                    pass
            if func:
                func(n)


# ------------------------------------------------------------------------------


class ProdEticList(adb.DbMem):
    
    def __init__(self, colonne=1):
        p = adb.DbTable(bt.TABNAME_PROD, 'prod')
        p.AddField('0.0', 'qtaetic')
        p.Reset()
        adb.DbMem.__init__(self, ','.join(p.GetAllColumnsNames()), 'id')
        self._info.dbpro = p
        self._info.colonne = colonne
    
    def __setattr__(self, name, val, **kw):
        adb.DbMem.__setattr__(self, name, val, **kw)
        if name == 'id' and hasattr(self._info, 'dbpro'):
            p = self._info.dbpro
            if p.Get(val):
                rs = self.GetRecordset()
                for col in p.GetAllColumnsNames():
                    if not col in ('id', 'qtaetic'):
                        setattr(self, col, getattr(p, col))
    
    def GetPrintTable(self, rptdef, rows, cols, row0, col0):
        rsp = copy.deepcopy(self.GetRecordset())
        self._info.colonne = cols
        wait = awu.WaitDialog(self._info.waitDialog, maximum=self.RowsCount())
        pt = None
        try:
            if row0>1 or col0>1:
                rs = [None]*len(rsp[0])
                rs = [rs]*(cols*(row0-1)+col0-1)
                self.SetRecordset(rs+rsp)
            pt = adb.SplittedTable(self, 'qtaetic', self._info.colonne, 
                                   lambda n: wait.SetValue(n), qtadefault=1)
        finally:
            wait.Destroy()
        self.SetRecordset(rsp)
        return pt


# ------------------------------------------------------------------------------


class PdtScan(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PDT_H, 'pdt_h')
        self.AddOrder('pdt_h.datins')
        b = self.AddMultiJoin(bt.TABNAME_PDT_B, 'pdt_b', 
                              idLeft='id', idRight='id_h')
        p = b.AddJoin(bt.TABNAME_PROD, 'prod')
        i = p.AddJoin(bt.TABNAME_ALIQIVA, 'aliqiva', join=adb.JOIN_LEFT)
        self.Reset()
        self.AddBaseFilter('pdt_h.ready=1 OR pdt_h.ready IS NULL')


# ------------------------------------------------------------------------------


class SintesiMovimentiSenzaCostoMemTable(adb.DbMem):
    
    def __init__(self):
        adb.DbMem.__init__(self, 'id,codice,descriz,count_movzero')
        self.Reset()
    
    def Retrieve(self, ssv=False):
        filt = ""
        if ssv:
            filt = " AND (statart.hidesearch IS NULL OR statart.hidesearch=0)"
        cmd = """
        SELECT prod.id, prod.codice, prod.descriz, COUNT(mov.id) count_movzero
        FROM movmag_b mov
        JOIN prod ON prod.id=mov.id_prod
        LEFT JOIN statart ON statart.id=prod.id_status
        WHERE mov.costou IS NULL OR mov.costou=0 %(filt)s
        GROUP BY prod.id, prod.codice, prod.descriz
        HAVING count_movzero>0
        ORDER BY prod.codice
        """ % locals()
        db = adb.db.__database__
        if db.Retrieve(cmd):
            self.SetRecordset(db.rs)
            return True
        return False
    
    def AggiornaCostoMovimenti(self, ssv=False):
        filt = ""
        if ssv:
            filt = " AND (SELECT IF(statart.hidesearch IS NULL, 0, statart.hidesearch) FROM statart WHERE statart.id=(SELECT id_status FROM prod WHERE prod.id=movmag_b.id_prod))=0"
        cmd = """
        UPDATE movmag_b SET 
        costou=(SELECT costo FROM prod WHERE prod.id=movmag_b.id_prod), 
        costot=movmag_b.qta*movmag_b.costou
        WHERE movmag_b.id_prod IS NOT NULL AND (movmag_b.costou IS NULL OR movmag_b.costou=0) %(filt)s
        """ % locals()
        db = adb.db.__database__
        return db.Execute(cmd)


# ------------------------------------------------------------------------------


class PdcSituazioneAcconti(adb.DbMem):
    
    def __init__(self):
        
        adb.DbMem.__init__(self, 'pdc_id,pdc_codice,pdc_descriz,accomov_id,accotpd_id,accotpd_codice,accotpd_descriz,accotpm_id,accotpm_codice,accotpm_descriz,accodoc_id,accodoc_numdoc,accodoc_datdoc,accomov_descriz,accomov_importo,accoiva_id,accoiva_codice,accoiva_descriz,total_storno,acconto_disponib')
        self.Reset()
        
        self._pdcid = None  #id cliente, None = tutti i clienti
        self._macid = None  #id movimento acconto, None = tutti gli acconti
        self._dexid = None  #id documento da escludere nella determinazione degli storni, None = considera tutti gli storni che trova
        self._tutti = False #true estrae tutti gli acconti, false solo quelli in essere
        self._group = ""
    
    def GetInnerSel(self):
        if self._dexid is None:
            dexfilter = ""
        else:
            dexfilter = " AND stormov.id_doc<>%s" % self._dexid
        return """
           accodoc.id_pdc  as accopdc_id,
           accopdc.codice  as accopdc_codice,
           accopdc.descriz as accopdc_descriz,
           accomov.id      as accomov_id,
           accotpd.id      as accotpd_id,
           accotpd.codice  as accotpd_codice,
           accotpd.descriz as accotpd_descriz,
           accotpm.id      as accotpm_id,
           accotpm.codice  as accotpm_codice,
           accotpm.descriz as accotpm_descriz,
           accodoc.id      as accodoc_id,
           accodoc.numdoc  as accodoc_numdoc,
           accodoc.datdoc  as accodoc_datdoc,
           accomov.descriz as accomov_descriz,
           accomov.importo as accomov_importo,
           accoiva.id      as accoiva_id,
           accoiva.codice  as accoiva_codice,
           accoiva.descriz as accoiva_descriz, (
    
               SELECT SUM(ABS(stormov.importo))
                 FROM movmag_b stormov
                WHERE stormov.id_movacc=accomov.id %(dexfilter)s
            
            ) AS total_storno""" % locals()
    
    def Retrieve(self):
        
        if self._pdcid is None:
            pdcfilter = "1"
        else:
            pdcfilter = "accodoc.id_pdc=%s" % self._pdcid
        if self._macid:
            pdcfilter += " AND accomov.id=%s" % self._macid
        group = self._group
        innsersel = self.GetInnerSel()
        if self._tutti:
            having = ""
        else:
            having = "HAVING acconto_disponib IS NOT NULL AND acconto_disponib>0"
        
        cmd = """
SELECT acconti.*, 
       acconti.accomov_importo-IF(total_storno IS NULL, 0, total_storno) as acconto_disponib
        
  FROM (

    SELECT %(innsersel)s
    
    FROM movmag_b AS accomov
    
    INNER JOIN cfgmagmov AS accotpm ON accomov.id_tipmov = accotpm.id
    INNER JOIN aliqiva   AS accoiva ON accomov.id_aliqiva = accoiva.id
    INNER JOIN movmag_h  AS accodoc ON accomov.id_doc = accodoc.id
    INNER JOIN cfgmagdoc AS accotpd ON accodoc.id_tipdoc = accotpd.id
    INNER JOIN pdc       AS accopdc ON accopdc.id = accodoc.id_pdc
    
    WHERE (%(pdcfilter)s) and (accotpm.is_acconto=1)
    
    %(group)s
    
    ORDER BY accopdc.descriz, accodoc.datdoc) as acconti

%(having)s
        """ % locals()
        
        db = adb.db.__database__
        db.Retrieve(cmd)
        self.SetRecordset(db.rs)
    
    def VediTutti(self):
        self._tutti = True
    
    def VediSoloAperti(self):
        self._tutti = False
    
    def GetForPdc(self, pdcid, macid=None, dexid=None):
        self._pdcid = pdcid
        self._macid = macid
        self._dexid = dexid
        return self.Retrieve()


# ------------------------------------------------------------------------------


class PdcTotaleAcconti(PdcSituazioneAcconti):
    
    def __init__(self):
        
        adb.DbMem.__init__(self, 'pdc_id,pdc_codice,pdc_descriz,accomov_importo,total_storno,acconto_disponib')
        self.Reset()
        
        self._pdcid = None  #id cliente, None = tutti i clienti
        self._macid = None  #id movimento acconto, None = tutti gli acconti
        self._dexid = None  #id documento da escludere nella determinazione degli storni, None = considera tutti gli storni che trova
        self._tutti = False #true estrae tutti gli acconti, false solo quelli in essere
        self._group = "GROUP BY accodoc.id_pdc"
    
    def GetInnerSel(self):
        if self._dexid is None:
            dexfilter = ""
        else:
            dexfilter = " AND stormov.id_doc<>%s" % self._dexid
        return """
           accodoc.id_pdc       as accopdc_id,
           accopdc.codice       as accopdc_codice,
           accopdc.descriz      as accopdc_descriz,
           SUM(accomov.importo) as accomov_importo, SUM((
    
               SELECT SUM(ABS(stormov.importo))
                 FROM movmag_b stormov
                WHERE stormov.id_movacc=accomov.id %(dexfilter)s
            
            )) AS total_storno""" % locals()


# ------------------------------------------------------------------------------


class PdcSituazioneStorniAcconto(ElencoMovim):
    
    def __init__(self):
        ElencoMovim.__init__(self, writable=True)
        self.AddField('0.0', 'acconto_disponib')
        self.Reset()


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    db = adb.DB()
    db.Connect()
    x = ProdEticList()
    for pid, qta in ((64300, 5),
                     (64302, 6),
                     (64304, 4)):
        x.CreateNewRow()
        x.id = pid
        x.qtaetic = qta
    for pr in x.GetPrintTable(3):
        print '(%s, %s) (%s, %s) (%s, %s)' % (pr.codice_0, pr.descriz_0,
                                              pr.codice_1, pr.descriz_1,
                                              pr.codice_2, pr.descriz_2)
