#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dbftd.py
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

import magazz.dbtables as dbm
adb = dbm.adb #alias stormdb
dba = dbm.dba #anag.dbtables

import Env
bt = Env.Azienda.BaseTab



class DocAll(dbm.DocAll):
    
    def __init__(self, *args, **kwargs):
        dbm.DocAll.__init__(self, *args, **kwargs)
        pdc = self['pdc']
        anacli = pdc.AddJoin(bt.TABNAME_CLIENTI, 'anacli', idLeft='id', idRight='id', join=adb.JOIN_LEFT)
        anafor = pdc.AddJoin(bt.TABNAME_FORNIT,  'anafor', idLeft='id', idRight='id', join=adb.JOIN_LEFT)
        pdc.anag = anacli
        self.Reset()


# ------------------------------------------------------------------------------


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
        
        self.AddOrder("%s.id_doc" % alias)
        self.AddOrder("%s.numriga" % alias)
        
        self.Get(-1)


# ------------------------------------------------------------------------------


class FtDif(adb.DbTable):
    """
    Fatturazione differita
    """
    
    def __init__(self):
        
        adb.DbTable.__init__(self,
            bt.TABNAME_CFGFTDIF,  'ftdcfg', writable=False)
        
        dgs = self.AddJoin(
            bt.TABNAME_CFGMAGDOC, 'tipdoc', idLeft='id_docgen')
        dgc = dgs.AddJoin(
            bt.TABNAME_CFGCONTAB, 'caucon', idLeft='id_caucg',
            join=adb.JOIN_LEFT)
        
        mgs = dgs.AddMultiJoin(
            bt.TABNAME_CFGMAGMOV, 'tipmov')
        
        ddr = self.AddMultiJoin(
            bt.TABNAME_CFGFTDDR,  'ddr', idRight='id_ftd')
        ddr.AddFilter("ddr.f_attivo=1")
        
        drs = ddr.AddJoin(
            bt.TABNAME_CFGMAGDOC, 'tipdoc', idLeft='id_docrag')
        
        mrs = drs.AddMultiJoin(
            bt.TABNAME_CFGMAGMOV, 'tipmov')
        
        docgen = DocAll(alias='docgen', writable=True)
        movgen = MovAll(alias='movgen', writable=True)
        docgen._lastdat = None
        docgen._lastnum = None
        docgen._firstdat = None
        docgen._firstnum = None
        docgen._year = Env.Azienda.Esercizio.dataElab.year
        docgen._sepall = None
        docgen._sepmp = None
        docgen._sepdest = None
        #aggiungo colonna dummy su movimenti generati per distinzione visuale
        #in grid dettaglio documento generato
        movgen.AddField('movgen.id', 'docset')
        movgen.Get(-1)
        self.docgen = docgen
        self.movgen = movgen
        
        docrag = DocAll(alias='docrag', writable=True)
        docrag.tot.AddTotalOf("IF(tipmov.askvalori IN ('T', 'V') AND (tot.importo IS NULL OR tot.importo=0), 1, 0)", "prezzizero")
        
        movrag = MovAll(alias='movrag', writable=False)
        #aggiungo colonna dummy su documenti estratti per gestione flag di
        #raggruppamento, default=True su tutti i documenti estratti
        docrag.AddField('docrag.id>0', 'raggruppa')
        docrag.Get(-1)
        docrag._datmin = None
        docrag._datmax = None
        docrag._nummin = None
        docrag._nummax = None
        docrag._esclacq = None
        docrag._esclann = None
        docrag._solosta = None
        docrag._solomag = None
        docrag._solopdc = None
        docrag._soloage = None
        docrag._solozona = None
        docrag._solocateg = None
        docrag._solomp = None
        docrag._tipidoc = None
        docrag._cautras = None
        docrag._movmap = None
        docrag._movdes = None
        docrag.ClearOrders()
#        docrag.AddOrder('pdc.descriz')
#        docrag.AddOrder('modpag.descriz')
#        docrag.AddOrder('dest.descriz')
#        docrag.AddOrder('docrag.datreg')
#        docrag.AddOrder('docrag.datdoc')
#        docrag.AddOrder('docrag.numdoc')
        
        self.docrag = docrag
        self.movrag = movrag
        self.docwrite = dbm.DocMag()
        self.docacq = {}
        
        self.Get(-1)

    def SetRaggr(self, fdid):
        
        if not self.Get(fdid):
            raise Exception, self.GetError()
        
        #controllo congruenza movimenti
        #per ogni documento da raggruppare viene testata la congruenza
        #del codice e del tipo di valori richiesti per ogni suo movimento
        #rispetto al documento da generare
        
        self.docrag._movmap = {}
        self.docrag._movdes = {}
        movsgen = self.tipdoc.tipmov
        for ddr in self.ddr:
            movsrag = ddr.tipdoc.tipmov
            for mov in movsrag:
                err = None
                if not movsgen.Locate(lambda mg: mg.codice == mov.codice):
                    err = "Mancata corrispondenza del codice movimento"
                else:
                    if mov.askvalori != movsgen.askvalori:
                        err = "Tipologia di informazioni non congruente"
                if err:
                    err += ": %s (%s) del documento %s (%s)"\
                        % (mov.codice, mov.descriz,
                           ddr.tipdoc.codice, ddr.tipdoc.descriz)
                    raise Exception, err
                self.docrag._movmap[ddr.tipdoc.tipmov.id] = movsgen.id
                if ddr.tipdoc.tipmov.Locate(lambda x: x.tipologia == "D")\
                   and not ddr.tipdoc.id in self.docrag._movdes:
                    self.docrag._movdes[ddr.tipdoc.id] = ddr.tipdoc.tipmov.id
        self.ReadLast()
        tipana = adb.DbTable(bt.TABNAME_PDCTIP, 'tipana')
        tipana.Get(self.tipdoc.id_pdctip)
        if tipana.tipo == "C":
            self.docrag.pdc.anag = self.docrag.pdc.anacli
        else:
            self.docrag.pdc.anag = self.docrag.pdc.anafor
    
    def SetYear(self, year):
        self.docgen._year = year
        self.ReadLast()
    
    def ReadLast(self):
        if self.tipdoc.colcg == 'X' and self.tipdoc.numdoc == '3' and self.tipdoc.id_caucg is not None:
            reg = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg', writable=False)
            reg.Synthetize()
            reg.AddFilter('reg.id_regiva=%s', self.tipdoc.caucon.id_regiva)
            reg.AddFilter('YEAR(reg.datreg)=%s', self.docgen._year)
            reg.AddMaximumOf("reg.numiva")
            reg.AddMaximumOf("reg.datdoc")
            if reg.Retrieve():
                self.docgen._lastdat = reg.max_datdoc
                self.docgen._lastnum = reg.max_numiva
        else:
            doc = adb.DbTable(bt.TABNAME_MOVMAG_H, 'doc', writable=False)
            doc.AddJoin(bt.TABNAME_CFGMAGDOC, 'tipdoc')
            if self.tipdoc.docfam:
                doc.AddFilter("tipdoc.docfam=%s", self.tipdoc.docfam)
            else:
                doc.AddFilter("doc.id_tipdoc=%s", self.id_docgen)
            doc.AddFilter("YEAR(doc.datdoc)=%s", self.docgen._year)
            doc.Synthetize()
            doc.AddMaximumOf("numdoc")
            doc.AddMaximumOf("datdoc")
            if doc.Retrieve():
                self.docgen._lastdat = doc.max_datdoc
                self.docgen._lastnum = doc.max_numdoc
    
    def Estrai(self):
        
        dr = self.docrag
        dg = self.docgen
        
        dr.ClearOrders()
        dr.AddOrder('pdc.descriz')
        if dg._sepmp:
            dr.AddOrder('modpag.descriz')
        if dg._sepdest:
            dr.AddOrder('dest.descriz')
        dr.AddOrder('docrag.datreg')
        dr.AddOrder('docrag.datdoc')
        dr.AddOrder('docrag.numdoc')
                
        dr.ClearFilters()
        dr.AddFilter('docrag.id_tipdoc IN (%s)'\
                     % ','.join([str(x) for x in dr._tipidoc]))
        ct = [str(x) for x in dr._cautras if x is not None]
        ctf1 = ''
        if ct:
            ctf1 = 'docrag.id_tracau IN (%s)' % ','.join(ct)
        ctf2 = ''
        if None in dr._cautras:
            ctf2 = 'docrag.id_tracau IS NULL'
        if ctf1 or ctf2:
            ctf = ctf2
            if ctf1:
                if ctf:
                    ctf += ' OR '
                ctf += ctf1
        dr.AddFilter(ctf)
        
        #selezioni sui documenti
        for field, op, name, default in (
            ('datdoc',    '>=', '_datmin',    None),
            ('datdoc',    '<=', '_datmax',    None),
            ('numdoc',    '>=', '_nummin',    None),
            ('numdoc',    '<=', '_nummax',    None),
            ('id_magazz', '=',  '_solomag',   None),
            ('id_pdc',    '=',  '_solopdc',   None),
            ('id_agente', '=',  '_soloage',   None),
            ('id_zona',   '=',  '_solozona',  None),
            ('f_printed', '=',  '_solosta',  self.docrag._solosta),
            ):                     
            value = self.docrag.__getattr__(name) or default
            if value:
                dr.AddFilter('docrag.%s%s%%s' % (field, op), value)
        
        #selezioni sui clienti (o fornitori: improbabile, ma possibile)
        #determino l'alias della tabella anagrafica clienti o fornitori
        anag = dr.pdc.anag.GetTableAlias()
        for field, op, name, default in (
            ('id_categ',  '=', '_solocateg', None),
            ('id_modpag', '=', '_solomp',    None),
            ):                     
            value = self.docrag.__getattr__(name) or default
            if value:
                dr.AddFilter('%s.%s%s%%s' % (anag, field, op), value)
        
        for field, value in (('f_acq', self.docrag._esclacq),
                             ('f_ann', self.docrag._esclann)):
            if value:
                dr.AddFilter('docrag.%s<>1' % field)
        
        if not dr.Retrieve():
            raise Exception, repr(dr.GetError())
    
    def Raggruppa(self, cbf=None):
        
        dr = self.docrag
        mr = self.movrag
        dg = self.docgen
        mg = self.movgen
        
        pdcanags = { "A": dba.Casse(),
                     "B": dba.Banche(),
                     "D": dba.Effetti(),
                     "C": dba.Clienti(),
                     "F": dba.Fornit() }
        for pdc in pdcanags:
            pdcanags[pdc].Get(-1)
        
        err = None
        if dr.RowsCount() == 0:
            err = "Nessun documento estratto"
        elif dg._firstdat is None:
            err = "Data di generazione documento indefinita"
        elif dg._firstnum is None:
            err = "Numero di generazione documento indefinito"
        if err:
            raise Exception, err
        
        sepall = dg._sepall# or self.f_sepall == 1)
        sepmp = dg._sepmp# or self.f_sepmp == 1)
        sepdest = dg._sepdest# or self.f_sepdest == 1)
        
        dat = dg._firstdat
        num = dg._firstnum-1
        niv = None
        if self.tipdoc.colcg and self.tipdoc.caucon.id_regiva:
            if self.tipdoc.numdoc == '3':
                niv = num
            else:
                cg = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg', writable=False)
                cg.AddFilter('YEAR(reg.datreg)=%s', dg._year)
                cg.AddFilter('reg.id_regiva=%s', self.tipdoc.caucon.id_regiva)
                cg.Synthetize()
                cg.AddMaximumOf('reg.numiva')
                if cg.Retrieve():
                    niv = cg.max_numiva#-1
                else:
                    raise Exception,\
                          "Errore in determinazione numero protocollo iva: %s"\
                          % repr(cg.GetError())
                del cg
        
        cfg = self.tipdoc
        
        headfields = {'datreg':    dat,
                      'datdoc':    dat,
                      'numdoc':    num,
                      'id_tipdoc': self.id_docgen,
                      'totpeso':   0,
                      'totcolli':  0,
                      'id_tracau': None,
                      'id_tracur': None,
                      'id_traasp': None,
                      'id_trapor': None,
                      'id_tracon': None,
                      'id_travet': 0,
                      'f_acq':     0,
                      'f_ann':     0,
                      'f_printed': 0,
                      'f_emailed': 0,
                      'impcontr':  0,
                      'notevet':   0 }
        
        bodyfields = {'id_doc': None, 
                      'f_ann':  0}
        
        lastmag = None
        lastpdc = None
        lastmp = None
        lastdest = None
        lastrig = None
        docset = 1
        
        dg.Reset()
        mg.Reset()
        dr.MoveFirst()
        
        bancf = adb.DbTable(bt.TABNAME_BANCF, 'bancf', writable=False)
        
        #ciclo su documenti estratti
        self.docacq = {}
        for n, d in enumerate(dr):
            
            if not d.raggruppa:
                continue
            
            #caricamento dettaglio documento estratto
            if not mr.Retrieve('movrag.id_doc=%s', d.id):
                raise Exception,\
                      "Errore in caricamento dettaglio documento: %s"\
                      % repr(mr.GetError())
            
            if mr.IsEmpty():
                continue
            
            if self.f_chgmag and self.id_chgmag:
                idmag = self.id_chgmag
            else:
                idmag = d.id_magazz
            
            #test necessità di nuovo documento
            if idmag != lastmag or d.id_pdc != lastpdc or sepall or\
               (sepmp and d.id_modpag != lastmp) or \
               (sepdest and d.id_dest != lastdest):
                
                #creazione testata
                
                num += 1
                if niv is not None:
                    niv += 1
                
                headfields['numdoc'] = num
                headfields['numiva'] = niv
                headfields['datrif'] = dr.datdoc
                headfields['numrif'] = dr.numdoc
                headfields['desrif'] = dr.tipdoc.descriz
                
                dg.CreateNewRow()
                
                #copia campi da documento origine
                for field in dr.GetFieldNames():
                    if field != 'id' and not field in headfields:
                        dg.__setattr__(field, dr.__getattr__(field))
                
                #cambio magazzino se necessario, da configurazione ftdif
                if self.f_chgmag and self.id_chgmag:
                    dg.id_magazz = self.id_chgmag
                
                if self.f_setgen:
                    dg.f_genrag = 1
                
                #id testate generate = -numero documento generato
                self.docacq[-num] = d.id
                dg.id = -num
                
                #campi propri del documento generato
                for field, value in headfields.iteritems():
                    dg.__setattr__(field, value)
                
                #campi necessari da setup documento generato
                #se mancanti, vengono presi dalla scheda anagrafica
                pdc = None
                tipo = dg.pdc.pdctip.tipo
                if tipo in pdcanags:
                    pdc = pdcanags[tipo]
                if pdc is not None:
                    pdc.Get(dr.id_pdc)
                for field, needed in (('id_modpag', cfg.askmodpag == 'X' or False),
                                      ('id_agente', cfg.askagente == 'X' or False),
                                      ('id_zona',   cfg.askzona   == 'X' or False),
                                      ):
                    if needed and not dg.__getattr__(field):
                        if pdc is not None:
                            if field in pdc.anag.GetFieldNames():
                                if pdc.id == d.id_pdc or pdc.Get(dg.id_pdc):
                                    dg.__setattr__(field, 
                                                   pdc.anag.__getattr__(field))
                
                #banca e spese di incasso
                banid = speid = None
                if sepmp:
                    #fatturazione separata x mod.pag, prendo da ddt
                    banid = dr.id_bancf
                    speid = dr.id_speinc
                else:
                    if pdc:
                        #prendo da scheda anagrafica
                        if bancf.Retrieve('bancf.id_pdc=%s', pdc.id):
                            if bancf.RowsCount() == 1:
                                banid = bancf.id
                            elif bancf.Locate(lambda x: bool(x.pref)):
                                banid = bancf.id
                            speid = pdc.anag.id_speinc
                if banid:
                    dg.id_bancf = banid
                    dg.id_speinc = speid
                
                #note per stampa
                nd = getattr(pdc.anag, 'notedoc', None)
                if nd:
                    setattr(dg, 'notedoc', nd)
                
                dg.tot.total_imponib = 0
                
                self.HeadCreated(dg)
                
                docset = 0
                lastrig = 0
                
                lastmag =  dg.id_magazz
                lastpdc =  dr.id_pdc
                lastmp =   dr.id_modpag
                lastdest = dr.id_dest
                
                if cbf is not None:
                    cbf(n)
            
            if not num in self.docacq:
                self.docacq[num] = []
            self.docacq[num].append(d.id)
            
            docset += 1
            bodyfields['docset'] = docset
            
            #nota: l'id di ogni movimento viene attribuito dal db in fase di
            #scittura (conferma); per manenere il legame tra documento generato
            #e relative righe di dettaglio, nell'id del movimento viene messo
            #temporaneamente il numero di documento invertito di segno
            
            #nota: il campo id_moveva, sulla riga di riferimento al documento
            #raggruppato, contiene l'id del documento originale con il segno -
            
            #creazione riga descrittiva rif.to doc. raggruppato
            if d.id_tipdoc in dr._movdes and not self.f_nodesrif:
                lastrig = self.GeneraDesRif(num, lastrig, d, bodyfields)
            
            #copia dettaglio documento raggruppato
            for m in mr:
                mg.CreateNewRow()
                lastrig += 1
                for field in mr.GetFieldNames():
                    if field != 'id' and not field in bodyfields:
                        mg.__setattr__(field, mr.__getattr__(field))
                
                bodyfields['id_tipmov'] = dr._movmap[m.id_tipmov]
                bodyfields['id_moveva'] = mr.id
                bodyfields['numriga'] = lastrig
                
                for field, value in bodyfields.iteritems():
                    mg.__setattr__(field, value)
                
                #id testate generate = -numero documento generato
                mg.id_doc = -num
                
                if not m.tipmov.tipologia in 'EO':
                    impriga = m.importo or 0
                    if m.tipmov.tipologia == 'I':
                        impriga *= -1
                    dg.tot.total_imponib += impriga
            
            self.BodyCopied(dg, dr)
        self.AllBodyCopied(dg, dr)
    
    def HeadCreated(self, *args, **kwargs):
        pass
    
    def AllBodyCopied(self, *args, **kwargs):
        pass

    def BodyCopied(self, *args, **kwargs):
        pass
    
    def GeneraDesRif(self, num, lastrig, doc, bodyfields):
        dr = self.docrag
        mg = self.movgen
        mg.CreateNewRow()
        lastrig += 1
        bodyfields['id_doc'] =    -num #attribuito in fase di conferma
        bodyfields['id_tipmov'] = dr._movmap[dr._movdes[doc.id_tipdoc]]
        #bodyfields['id_moveva'] = -d.id
        bodyfields['numriga'] = lastrig
        
        for field, value in bodyfields.iteritems():
            mg.__setattr__(field, value)
        mg.__setattr__('descriz', "Rif.to %s n. %s del %s"\
                  % (doc.tipdoc.descriz, doc.numdoc, Env.StrDate(doc.datdoc)))
        
        return lastrig
    
    def Genera(self, func=None):
        
        new = self.docwrite
        tdocgenid = self.docgen.tipdoc.id
        doc = self.docgen
        mov = self.movgen
        headfields = doc.GetFieldNames()
        bodyfields = mov.GetFieldNames()
        
        for doc in doc:
            num = doc.id
            if mov.Locate(lambda m: m.id_doc == num):
                
                new.Reset()
                new.cfgdoc.Get(tdocgenid)
                new.CreateNewRow()
                for field in headfields:
                    setattr(new, field, getattr(doc, field))
                new.id = None
                new.id_docacq = doc.id
                
                while mov.id_doc == num:
                    new.mov.CreateNewRow()
                    for field in bodyfields:
                        setattr(new.mov, field, getattr(mov, field))
                    new.mov.id_doc = None
                    new.mov.id_moveva = mov.id
                    if not mov.MoveNext():
                        break
                
                if self.f_setacq == 1:
                    new._info.acqdocacq = self.docacq[-doc.id]
                
                if self.f_setann == 1:
                    new._info.acqdocann = self.docacq[-doc.id]
                
                if new.config.colcg and new.config.caucon:
                    if new.config.caucon.pcf == '1':
                        new.MakeTotals()
                        new.CalcolaScadenze()
                    new.regcon._info.id_effbap = new.id_bancf
                    try:
                        new.CollegaCont()
                    except Exception, e:
                        raise Exception, repr(e.args)
                
                if new.Save():
                    self.DocGenerato(new)
                else:
                    raise Exception, new.GetError()
                
                if func is not None:
                    func(new)
    
    def DocGenerato(self, *args, **kwargs):
        pass


# ------------------------------------------------------------------------------


class FtDifHistory(adb.DbTable):
    """
    Elaborazioni avvenute (storia doc.raggr.->doc.generati)
    """
    
    def __init__(self, **kwargs):
        
        adb.DbTable.__init__(self, bt.TABNAME_MOVMAG_H, 'docrag', **kwargs)
        self.AddJoin(bt.TABNAME_CFGMAGDOC, 'cfgrag', idLeft='id_tipdoc')
        dg = self.AddJoin(bt.TABNAME_MOVMAG_H, 'docgen', idLeft='id_docacq')
        dg.AddJoin(bt.TABNAME_CFGMAGDOC, 'cfggen', idLeft='id_tipdoc')
        self.SetOrderRag()
        self.Get(-1)
    
    def SetOrderRag(self):
        self.ClearOrders()
        self.AddOrder('docrag.datdoc')
        self.AddOrder('docrag.numdoc')
    
    def SetOrderGen(self):
        self.ClearOrders()
        self.AddOrder('docgen.datdoc')
        self.AddOrder('docgen.numdoc')
