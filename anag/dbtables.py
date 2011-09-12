#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/dbtables.py
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
Definizione classi per tabelle anagrafiche.
"""

import stormdb as adb

import Env
bt = Env.Azienda.BaseTab

import copy


class TabMastri(adb.DbTable):
    def __init__(self, *args, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_BILMAS, 'bilmas', **kwargs)
        self.AddOrder('IF(bilmas.tipo="P",1,IF(bilmas.tipo="E",2,IF(bilmas.tipo="O",3,4)))')
        self.AddOrder('bilmas.codice')
    
    def GetSezione(self):
        out = ''
        tipo = self.tipo
        if tipo in "PEO":
            out = ['STATO PATRIMONIALE', 
                   'CONTO ECONOMICO', 
                   'CONTI D\'ORDINE']["PEO".index(tipo)]
        return out


# ------------------------------------------------------------------------------


class TabConti(adb.DbTable):
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_BILCON, 'bilcon', **kwargs)
        self.AddJoin(bt.TABNAME_BILMAS, 'bilmas', dbTabClass=TabMastri)
        self.AddOrder('bilcon.codice')


# ------------------------------------------------------------------------------


class TabMastriRicl(TabMastri):
    def __init__(self, name=None, alias=None, **kwargs):
        if name is None:
            name = bt.TABNAME_BRIMAS
        if alias is None:
            alias = 'brimas'
        adb.DbTable.__init__(self, name, alias, **kwargs)
        self.AddOrder('IF(%s.tipo="P",1,IF(%s.tipo="E",2,IF(%s.tipo="O",3,4)))'\
                  % (alias, alias, alias))
        self.AddOrder('%s.codice' % alias)


# ------------------------------------------------------------------------------


class TabContiRicl(adb.DbTable):
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_BRICON, 'bricon', **kwargs)
        self.AddJoin(bt.TABNAME_BRIMAS, 'brimas', idLeft='id_bilmas', 
                     idRight='id', dbTabClass=TabMastriRicl)
        self.AddOrder('bilcon.codice')


# ------------------------------------------------------------------------------


class Pdc(adb.DbTable):
    """
    DbTable anagrafica pdc.
    Struttura:
    pdc: piano dei conti
       +--> bilmas (bilmas): mastro di bilancio
       +--> bilcon (bilcon): conto di bilancio
       +--> tipana (pdctip): tipo anagrafico
    """
    def __init__(self, *args, **kwargs):
        
        parms = {"writable":        True,\
                 "mandatoryFields": "codice,descriz,id_tipo"}
        
        for key, val in parms.iteritems():
            if not kwargs.has_key(key):
                kwargs[key] = val
        
        adb.DbTable.__init__(\
            self, bt.TABNAME_PDC,  "pdc", **kwargs)
        
        bilmas = self.AddJoin(\
            bt.TABNAME_BILMAS, "bilmas",  idLeft="id_bilmas",
        dbTabClass=TabMastri)
        
        bilcon = self.AddJoin(\
            bt.TABNAME_BILCON, "bilcon",  idLeft="id_bilcon",\
            join=adb.JOIN_LEFT)
        
        tipana = self.AddJoin(\
            bt.TABNAME_PDCTIP, "tipana",  idLeft="id_tipo",\
            join=adb.JOIN_LEFT)
        
        self._info.autom = adb.DbTable(bt.TABNAME_CFGAUTOM, "autom",\
                                       writable=False)
        #self.Get(-1)

    def __setattr__(self, field, value, **kwargs):
        adb.DbTable.__setattr__(self, field, value, **kwargs)
        try:
            do = field == "id_tipo" and self.tipana.tipo in "ABDCF"
        except:
            do = False
        if do:
            autom = self._info.autom
            if   self.tipana.tipo == "A": key = "cassa"
            elif self.tipana.tipo == "B": key = "banche"
            elif self.tipana.tipo == "D": key = "effetti"
            elif self.tipana.tipo == "C": key = "clienti"
            elif self.tipana.tipo == "F": key = "fornit"
            else: key = None
            if key is not None and self.id_bilmas is None:
                autom.ClearFilters()
                autom.AddFilter("autom.codice='bilmas_%s'" % key)
                if autom.Retrieve() and autom.RowsCount() == 1:
                    self.id_bilmas = autom.aut_id
                autom.Reset()
            if key is not None and self.id_bilcon is None:
                autom.ClearFilters()
                autom.AddFilter("autom.codice='bilcon_%s'" % key)
                if autom.Retrieve() and autom.RowsCount() == 1:
                    self.id_bilcon = autom.aut_id
                autom.Reset()


# ------------------------------------------------------------------------------


class PdcRicl(Pdc):
    """
    DbTable anagrafica pdc con mastri e conti riclassificati.
    Struttura:
    pdc: piano dei conti
       +--> bilmas (brimas): mastro ricl. di bilancio
       +--> bilcon (bricon): conto ricl. di bilancio
       +--> tipana (pdctip): tipo anagrafico
    """
    def __init__(self, *args, **kwargs):
        
        parms = {"writable":        True,\
                 "mandatoryFields": "codice,descriz,id_tipo"}
        
        for key, val in parms.iteritems():
            if not kwargs.has_key(key):
                kwargs[key] = val
        
        adb.DbTable.__init__(\
            self, bt.TABNAME_PDC,  "pdc", **kwargs)
        
        bilmas = self.AddJoin(\
            bt.TABNAME_BRIMAS, "bilmas",  idLeft="id_brimas",
        dbTabClass=TabMastriRicl)
        
        bilcon = self.AddJoin(\
            bt.TABNAME_BRICON, "bilcon",  idLeft="id_bricon",\
            join=adb.JOIN_LEFT)
        
        tipana = self.AddJoin(\
            bt.TABNAME_PDCTIP, "tipana",  idLeft="id_tipo",\
            join=adb.JOIN_LEFT)
        
        self._info.autom = adb.DbTable(bt.TABNAME_CFGAUTOM, "autom",\
                                       writable=False)


# ------------------------------------------------------------------------------


class Casse(Pdc):
    """
    Gestione tabella Casse
    """
    def __init__(self, *args, **kwargs):
        
        Pdc.__init__(self, *args, **kwargs)
        
        self.AddJoin(\
            bt.TABNAME_CASSE, "anag", idLeft='id', idRight='id')


# ------------------------------------------------------------------------------


class Banche(Pdc):
    """
    Gestione tabella Banche
    """
    def __init__(self, *args, **kwargs):
        
        Pdc.__init__(self, *args, **kwargs)
        
        self.AddJoin(\
            bt.TABNAME_BANCHE, "anag", idLeft='id', idRight='id')


# ------------------------------------------------------------------------------


class Effetti(Pdc):
    """
    Gestione tabella Effetti
    """
    def __init__(self, *args, **kwargs):
        
        Pdc.__init__(self, *args, **kwargs)
        
        eff = self.AddJoin(\
            bt.TABNAME_EFFETTI, "anag", idLeft='id', idRight='id')
        
        eff.AddJoin(\
            bt.TABNAME_PDC,     "banca", idLeft='id_banca', idRight='id',
            join=adb.JOIN_LEFT)


# ------------------------------------------------------------------------------


class Clienti(Pdc):
    """
    Gestione tabella Clienti
    """
    def __init__(self, *args, **kwargs):
        
        Pdc.__init__(self, *args, **kwargs)
        
        cli = self.AddJoin(\
            bt.TABNAME_CLIENTI, "anag",    idLeft='id', idRight='id')
        
        cli.AddJoin(\
            bt.TABNAME_MODPAG,  "modpag",  idLeft="id_modpag",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_SPEINC,  "spese",   idLeft="id_speinc",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_AGENTI,  "agente",  idLeft="id_agente",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_ZONE,    "zona",    idLeft="id_zona",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_TIPLIST, "tiplist", idLeft="id_tiplist",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_CATCLI,  "catana",  idLeft="id_categ",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_STATCLI, "status",  idLeft="id_status",\
            join=adb.JOIN_LEFT)
        
        cli.AddJoin(\
            bt.TABNAME_ALIQIVA, "aliqiva", idLeft="id_aliqiva",\
            join=adb.JOIN_LEFT)
        
        m = cli.AddMultiJoin(\
            bt.TABNAME_BANCF,   "banche",  idRight="id_pdc",\
            join=adb.JOIN_LEFT)
        m.AddOrder("banche.pref", adb.ORDER_DESCENDING)
        
        m = cli.AddMultiJoin(\
            bt.TABNAME_DESTIN, "dest",   idRight="id_pdc",\
            join=adb.JOIN_LEFT)
        m.AddOrder("dest.pref", adb.ORDER_DESCENDING)


# ------------------------------------------------------------------------------


class Fornit(Pdc):
    """
    Gestione tabella Fornitori
    """
    def __init__(self, *args, **kwargs):
        
        Pdc.__init__(self, *args, **kwargs)
        
        fornit = self.AddJoin(\
            bt.TABNAME_FORNIT, "anag",     idLeft='id', idRight='id')
        
        fornit.AddJoin(\
            bt.TABNAME_MODPAG,  "modpag",  idLeft="id_modpag",\
            join=adb.JOIN_LEFT)
        
        fornit.AddJoin(\
            bt.TABNAME_ZONE,    "zona",    idLeft="id_zona",\
            join=adb.JOIN_LEFT)
        
        fornit.AddJoin(\
            bt.TABNAME_CATFOR,  "catana",  idLeft="id_categ",\
            join=adb.JOIN_LEFT)
        
        fornit.AddJoin(\
            bt.TABNAME_STATFOR, "status",  idLeft="id_status",\
            join=adb.JOIN_LEFT)
        
        fornit.AddJoin(\
            bt.TABNAME_ALIQIVA, "aliqiva", idLeft="id_aliqiva",\
            join=adb.JOIN_LEFT)


# ------------------------------------------------------------------------------


class PdcTip(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PDCTIP, 'tipana', writable=False)
        self.AddOrder('tipana.codice')


# ------------------------------------------------------------------------------


def GetPdcClass(id_tipo):
    """
    Ritorna il dbtable di gestione anagrafica congruente con il tipo di 
    sottoconto passato.
    La DbTable è da istanziare.
    """
    cls = None
    tipibase = "ABDCF"
    tipo = adb.DbTable("pdctip", "tipo", writable=False)
    if tipo.Get(id_tipo) and tipo.RowsCount() == 1:
        if tipo.tipo in tipibase:
            cls = (Casse,\
                    Banche,\
                    Effetti,\
                    Clienti,\
                    Fornit)[tipibase.index(tipo.tipo)]
        else:
            cls = Pdc
    del tipo
    return cls


# ------------------------------------------------------------------------------


def GetPdcTipForCodice(tipo):
    out = None
    t = adb.DbTable(bt.TABNAME_PDCTIP, 'tipana')
    if t.Retrieve('tipana.tipo=%s', 'F'):
        out = t.id
    return out


# ------------------------------------------------------------------------------


class PdcStruttura(Pdc):
    
    def __init__(self, *args, **kwargs):
        
        Pdc.__init__(self, *args, **kwargs)
        
        from cfg.dbtables import BilancioCeeTable
        bilcee = self.AddJoin('x4.bilcee', 'bilcee', join=adb.JOIN_LEFT,
                              dbTabClass=BilancioCeeTable)
        
        status = self.AddJoin(\
            bt.TABNAME_STATPDC, "status", idLeft="id_statpdc",\
            join=adb.JOIN_LEFT)
        
        self.Reset()
        
        self.ClearOrders()
        self.AddOrder('IF(bilmas.tipo="P",1,IF(bilmas.tipo="E",2,IF(bilmas.tipo="O",3,4)))')
        self.AddOrder('bilmas.tipo')
        self.AddOrder('bilmas.codice')
        self.AddOrder('bilcon.codice')
        self.AddOrder('pdc.descriz')


# ------------------------------------------------------------------------------


class PdcStrutturaRicl(PdcRicl):
    def __init__(self, *args, **kwargs):
        PdcRicl.__init__(self, *args, **kwargs)
        self.ClearOrders()
        self.AddOrder('IF(bilmas.tipo="P",1,IF(bilmas.tipo="E",2,IF(bilmas.tipo="O",3,4)))')
        self.AddOrder('bilmas.tipo')
        self.AddOrder('bilmas.codice')
        self.AddOrder('bilcon.codice')
        self.AddOrder('pdc.descriz')


# ------------------------------------------------------------------------------


class TipoListino(adb.DbTable):
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_TIPLIST, 'tiplist', **kwargs)
        self.AddJoin(bt.TABNAME_MACRO, 'macro', join=adb.JOIN_LEFT)
        self.AddOrder('tiplist.codice')
        self.Get(-1)


# ------------------------------------------------------------------------------


class TabProdotti(adb.DbTable):
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_PROD, 'prod', **kwargs)
        self.AddJoin(bt.TABNAME_TIPART,  "tipart",  join=adb.JOIN_LEFT)
        self.AddJoin(bt.TABNAME_CATART,  "catart",  join=adb.JOIN_LEFT)
        self.AddJoin(bt.TABNAME_GRUART,  "gruart",  join=adb.JOIN_LEFT)
        self.AddJoin(bt.TABNAME_MARART,  "marart",  join=adb.JOIN_LEFT)
        self.AddJoin(bt.TABNAME_STATART, "status",  join=adb.JOIN_LEFT, idLeft='id_status')
        self.AddJoin(bt.TABNAME_ALIQIVA, "aliqiva", join=adb.JOIN_LEFT)
        self.AddJoin(bt.TABNAME_PDC,     "pdc",     join=adb.JOIN_LEFT, idLeft="id_fornit")


# ------------------------------------------------------------------------------


class TabProdListiniAttualiTable(adb.DbMem):
    
    class NullProd(object):
        db = None
        def __init__(self, db):
            self.db = db
        def __getattr__(self, name):
            if name in 'codice descriz descextra'.split():
                name = 'prod_%s' % name
            return adb.DbMem.__getattr__(self.db, name)
    
    datamax = None
    
    def __init__(self, **kwargs):
        adb.DbMem.__init__(self, 'prod_id,prod_codice,prod_descriz,prod_descextra,prod_pzconf,prod_codfor,prod_barcode,pdc_id,pdc_codice,pdc_descriz,prod_costo,prod_prezzo,listino_data,listino_prezzo1,listino_prezzo2,listino_prezzo3,listino_prezzo4,listino_prezzo5,listino_prezzo6,listino_prezzo7,listino_prezzo8,listino_prezzo9')
        self.prod = self.NullProd(self)
        self._keys = ['prod_costo', 'prod_prezzo']
        self._keys += ['listino_prezzo%d'%l for l in range(1,10)]
        self._cols = {}
        for col in self._keys:
            self._cols[col] = copy.copy({'value': None,
                                         'title': None,
                                         'print': False})
    
    def Retrieve(self, filter_cmd=None, filter_par=[]):
        if bt.MAGDATLIS:
            cmd = """
            SELECT prod.id        'prod_id', 
                   prod.codice    'prod_codice', 
                   prod.descriz   'prod_descriz', 
                   prod.descextra 'prod_descextra',
                   prod.pzconf    'prod_pzconf', 
                   prod.codfor    'prod_codfor', 
                   prod.barcode   'prod_barcode', 
                   pdc.id         'pdc_id',
                   pdc.codice     'pdc_codice',
                   pdc.descriz    'pdc_descriz',
                   prod.costo     'prod_costo', 
                   prod.prezzo    'prod_prezzo', 
                   lis.data       'listino_data', 
                   lis.prezzo1    'listino_prezzo1', 
                   lis.prezzo2    'listino_prezzo2', 
                   lis.prezzo3    'listino_prezzo3', 
                   lis.prezzo4    'listino_prezzo4', 
                   lis.prezzo5    'listino_prezzo5', 
                   lis.prezzo6    'listino_prezzo6', 
                   lis.prezzo7    'listino_prezzo7', 
                   lis.prezzo8    'listino_prezzo8', 
                   lis.prezzo9    'listino_prezzo9'
                
              FROM prod
              
              LEFT JOIN tipart         ON tipart.id=prod.id_tipart
              LEFT JOIN catart         ON catart.id=prod.id_catart
              LEFT JOIN gruart         ON gruart.id=prod.id_gruart
              LEFT JOIN marart         ON marart.id=prod.id_marart
              LEFT JOIN statart status ON status.id=prod.id_status
              LEFT JOIN pdc            ON pdc.id=prod.id_fornit
              LEFT JOIN (
              
                   SELECT id_prod   'id_prod', 
                          MAX(data) 'max_data'
                     FROM listini l
                    WHERE l.data<=%s
                 GROUP BY l.id_prod) riep 
                 
                                       ON riep.id_prod=prod.id
                  JOIN listini lis     ON lis.id_prod=prod.id AND lis.data=riep.max_data
            """
            par = [self.datamax]
        else:
            cmd = """
            SELECT prod.id        'prod_id', 
                   prod.codice    'prod_codice', 
                   prod.descriz   'prod_descriz', 
                   prod.descextra 'prod_descextra', 
                   prod.pzconf    'prod_pzconf', 
                   prod.codfor    'prod_codfor', 
                   prod.barcode   'prod_barcode', 
                   pdc.id         'pdc_id',
                   pdc.codice     'pdc_codice',
                   pdc.descriz    'pdc_descriz',
                   prod.costo     'prod_costo', 
                   prod.prezzo    'prod_prezzo', 
                   lis.data       'listino_data', 
                   lis.prezzo1    'listino_prezzo1', 
                   lis.prezzo2    'listino_prezzo2', 
                   lis.prezzo3    'listino_prezzo3', 
                   lis.prezzo4    'listino_prezzo4', 
                   lis.prezzo5    'listino_prezzo5', 
                   lis.prezzo6    'listino_prezzo6', 
                   lis.prezzo7    'listino_prezzo7', 
                   lis.prezzo8    'listino_prezzo8', 
                   lis.prezzo9    'listino_prezzo9'
                
              FROM prod
              
              LEFT JOIN tipart         ON tipart.id=prod.id_tipart
              LEFT JOIN catart         ON catart.id=prod.id_catart
              LEFT JOIN gruart         ON gruart.id=prod.id_gruart
              LEFT JOIN marart         ON marart.id=prod.id_marart
              LEFT JOIN statart status ON status.id=prod.id_status
              LEFT JOIN pdc            ON pdc.id=prod.id_fornit
                   JOIN listini lis    ON lis.id_prod=prod.id
            """
            par = []
        if filter_cmd:
            cmd += """
            WHERE %s
            """ % filter_cmd
        par += filter_par
        db = adb.db.__database__
        db.Retrieve(cmd, par)
        self.SetRecordset(db.rs)
    
    def SetDataVal(self, d):
        self.datamax = d
    
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


class TabProdGrigliaPrezziAttualiPdcTable(adb.DbMem):
    
    datamax = None
    idpdc = None
    
    def __init__(self, **kwargs):
        adb.DbMem.__init__(self, ['prod_id',
                                  'prod_codice',
                                  'prod_descriz',
                                  'prod_descextra',
                                  'prod_codfor',
                                  'prod_barcode',
                                  'pdc_id',
                                  'pdc_codice',
                                  'pdc_descriz',
                                  'prod_costo',
                                  'prod_prezzo',
                                  'prod_pzconf',
                                  'grip_pdc_id',
                                  'grip_pdc_codice',
                                  'grip_pdc_descriz',
                                  'grip_data',
                                  'grip_prezzo',
                                  'grip_sconto1',
                                  'grip_sconto2',
                                  'grip_sconto3',
                                  'grip_sconto4',
                                  'grip_sconto5',
                                  'grip_sconto6',
                                  'grip_ext_codice',
                                  'grip_ext_descriz',
                                  'grip_pzconf'])
    
    def Retrieve(self, filter_cmd=None, filter_par=[]):
        if bt.MAGDATGRIP:
            cmd = """
            SELECT prod.id          'prod_id', 
                   prod.codice      'prod_codice', 
                   prod.descriz     'prod_descriz', 
                   prod.descextra   'prod_descextra', 
                   prod.codfor      'prod_codfor', 
                   prod.barcode     'prod_barcode', 
                   pdc.id           'pdc_id',
                   pdc.codice       'pdc_codice',
                   pdc.descriz      'pdc_descriz',
                   prod.costo       'prod_costo', 
                   prod.prezzo      'prod_prezzo', 
                   prod.pzconf      'prod_pzconf', 
                   pdcgrip.id       'grip_pdc_id', 
                   pdcgrip.codice   'grip_pdc_codice', 
                   pdcgrip.descriz  'grip_pdc_descriz', 
                   grip.data        'grip_data', 
                   grip.prezzo      'grip_prezzo', 
                   grip.sconto1     'grip_sconto1', 
                   grip.sconto2     'grip_sconto2', 
                   grip.sconto3     'grip_sconto3', 
                   grip.sconto4     'grip_sconto4', 
                   grip.sconto5     'grip_sconto5', 
                   grip.sconto6     'grip_sconto6', 
                   grip.ext_codice  'grip_ext_codice',
                   grip.ext_descriz 'grip_ext_descriz',
                   grip.pzconf      'grip_pzconf'
                                 
              FROM prod
              
              LEFT JOIN tipart         ON tipart.id=prod.id_tipart
              LEFT JOIN catart         ON catart.id=prod.id_catart
              LEFT JOIN gruart         ON gruart.id=prod.id_gruart
              LEFT JOIN marart         ON marart.id=prod.id_marart
              LEFT JOIN statart status ON status.id=prod.id_status
              LEFT JOIN pdc            ON pdc.id=prod.id_fornit
              LEFT JOIN (
              
                   SELECT id_prod   'id_prod', 
                          MAX(data) 'max_data'
                     FROM griglie g
                    WHERE g.id_pdc=%s AND g.data<=%s
                 GROUP BY g.id_prod) riep 
                 
                                       ON riep.id_prod=prod.id
                  JOIN griglie grip    ON grip.id_prod=prod.id AND grip.id_pdc=%s AND grip.data=riep.max_data
                  JOIN pdc pdcgrip     ON pdcgrip.id=grip.id_pdc
            """
            par = [self.idpdc, self.datamax, self.idpdc]
        else:
            cmd = """
            SELECT prod.id          'prod_id', 
                   prod.codice      'prod_codice', 
                   prod.descriz     'prod_descriz', 
                   prod.descextra   'prod_descextra', 
                   prod.codfor      'prod_codfor', 
                   prod.barcode     'prod_barcode', 
                   pdc.id           'pdc_id',
                   pdc.codice       'pdc_codice',
                   pdc.descriz      'pdc_descriz',
                   prod.costo       'prod_costo', 
                   prod.prezzo      'prod_prezzo', 
                   prod.pzconf      'prod_pzconf', 
                   pdcgrip.id       'grip_pdc_id', 
                   pdcgrip.codice   'grip_pdc_codice', 
                   pdcgrip.descriz  'grip_pdc_descriz', 
                   grip.data        'grip_data', 
                   grip.prezzo      'grip_prezzo', 
                   grip.sconto1     'grip_sconto1', 
                   grip.sconto2     'grip_sconto2', 
                   grip.sconto3     'grip_sconto3', 
                   grip.sconto4     'grip_sconto4', 
                   grip.sconto5     'grip_sconto5', 
                   grip.sconto6     'grip_sconto6', 
                   grip.ext_codice  'grip_ext_codice',
                   grip.ext_descriz 'grip_ext_descriz',
                   grip.pzconf      'grip_pzconf'
                                 
              FROM prod
              
              LEFT JOIN tipart         ON tipart.id=prod.id_tipart
              LEFT JOIN catart         ON catart.id=prod.id_catart
              LEFT JOIN gruart         ON gruart.id=prod.id_gruart
              LEFT JOIN marart         ON marart.id=prod.id_marart
              LEFT JOIN statart status ON status.id=prod.id_status
              LEFT JOIN pdc            ON pdc.id=prod.id_fornit
                   JOIN griglie grip   ON grip.id_prod=prod.id AND grip.id_pdc=%s
                   JOIN pdc pdcgrip    ON pdcgrip.id=grip.id_pdc
            """
            par = [self.idpdc]
        if filter_cmd:
            cmd += """
            WHERE %s
            """ % filter_cmd
        cmd += """
        ORDER BY prod.codice, pdcgrip.descriz, grip.data DESC
        """
        par += filter_par
        db = adb.db.__database__
        db.Retrieve(cmd, par)
        self.SetRecordset(db.rs)
    
    def SetParam(self, data, pdc):
        self.datamax = data
        self.idpdc = pdc


# ------------------------------------------------------------------------------


class TabProdGrigliaPrezziAttualiProdTable(adb.DbMem):
    
    datamax = None
    idprod = None
    tipana = None
    
    def __init__(self, **kwargs):
        adb.DbMem.__init__(self,\
                           """prod_id prod_codice prod_descriz prod_descextra prod_codfor prod_barcode """\
                           """pdc_id pdc_codice pdc_descriz prod_costo prod_prezzo prod_pzconf """\
                           """grip_pdc_id grip_pdc_codice grip_pdc_descriz grip_data grip_prezzo """\
                           """grip_sconto1 grip_sconto2 grip_sconto3 grip_sconto4 grip_sconto5 grip_sconto6 grip_pzconf""".split())
    
    def Retrieve(self, filter_cmd=None, filter_par=[]):
        cmd = """
        SELECT prod.id          'prod_id', 
               prod.codice      'prod_codice', 
               prod.descriz     'prod_descriz', 
               prod.descextra   'prod_descextra', 
               prod.codfor      'prod_codfor', 
               prod.barcode     'prod_barcode', 
               pdc.id           'pdc_id',
               pdc.codice       'pdc_codice',
               pdc.descriz      'pdc_descriz',
               prod.costo       'prod_costo', 
               prod.prezzo      'prod_prezzo', 
               prod.pzconf      'prod_pzconf', 
               pdcgrip.id       'grip_pdc_id', 
               pdcgrip.codice   'grip_pdc_codice', 
               pdcgrip.descriz  'grip_pdc_descriz', 
               grip.data        'grip_data', 
               grip.prezzo      'grip_prezzo', 
               grip.sconto1     'grip_sconto1', 
               grip.sconto2     'grip_sconto2', 
               grip.sconto3     'grip_sconto3',
               grip.sconto4     'grip_sconto4', 
               grip.sconto5     'grip_sconto5', 
               grip.sconto6     'grip_sconto6', 
               grip.pzconf      'grip_pzconf'
                             
          FROM prod
          
          LEFT JOIN tipart         ON tipart.id=prod.id_tipart
          LEFT JOIN catart         ON catart.id=prod.id_catart
          LEFT JOIN gruart         ON gruart.id=prod.id_gruart
          LEFT JOIN marart         ON marart.id=prod.id_marart
          LEFT JOIN statart status ON status.id=prod.id_status
          LEFT JOIN pdc            ON pdc.id=prod.id_fornit
          LEFT JOIN (
          
               SELECT id_prod   'id_prod', 
                      id_pdc    'id_pdc', 
                      MAX(data) 'max_data'
                 FROM griglie g
                WHERE g.id_prod=%s AND g.data<=%s
             GROUP BY g.id_prod, g.id_pdc) riep 
             
                                   ON riep.id_prod=prod.id
              JOIN griglie grip    ON grip.id_prod=prod.id AND grip.id_pdc=riep.id_pdc AND grip.data=riep.max_data
              JOIN pdc pdcgrip     ON pdcgrip.id=grip.id_pdc
              JOIN pdctip tipana   ON pdcgrip.id_tipo=tipana.id
        """
        if self.tipana:
            if filter_cmd:
                filter_cmd += " AND "
            else:
                filter_cmd = ""
            filter_cmd += "tipana.tipo='%s'" % self.tipana
        if filter_cmd:
            cmd += """
            WHERE %s
            """ % filter_cmd
        cmd += """
        ORDER BY prod.codice, pdcgrip.descriz, grip.data DESC
        """
        par = [self.idprod, self.datamax]+filter_par
        db = adb.db.__database__
        db.Retrieve(cmd, par)
        self.SetRecordset(db.rs)
    
    def SetParam(self, data, pro, tipana=None):
        self.datamax = data
        self.idprod = pro
        self.tipana = tipana


# ------------------------------------------------------------------------------


class TabAliqIva(adb.DbTable):
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_ALIQIVA, 'aliqiva', **kwargs)


# ------------------------------------------------------------------------------


class TabAgenti(adb.DbTable):
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_AGENTI, 'age', **kwargs)
        self.AddOrder('age.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class InvStruttura(TabProdotti):
    def __init__(self, **kwargs):
        TabProdotti.__init__(self, fields='id,codice,descriz', **kwargs)
        self.AddOrder('catart.codice')
        self.AddOrder('gruart.codice')
        self.AddOrder('prod.codice')


# ------------------------------------------------------------------------------


class TipiAnagrafici(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PDCTIP, 'tipana',
                             writable=False)
        self.Reset()
    
    def GetTipi(self, tipo):
        assert type(tipo) in (str, unicode)
        assert len(tipo) == 1
        out = None
        if self.Retrieve('tipana.tipo=%s', tipo):
            out = [t.id for t in self]
        return tuple(out)


# ------------------------------------------------------------------------------


class TabZone(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_ZONE, 'zona',
                             writable=False)
        self.Reset()


# ------------------------------------------------------------------------------


class TabScontiCC(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_SCONTICC, 'scc')
        pdc = self.AddJoin(bt.TABNAME_PDC)
        cli = pdc.AddJoin(bt.TABNAME_CLIENTI, 'cliente', idLeft='id')
        cat = self.AddJoin(bt.TABNAME_CATART, 'catart')
        self.AddOrder('pdc.codice')
        self.AddOrder('catart.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TabTipArt(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_TIPART, 'tipart')
        self.AddOrder('tipart.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TabCatArt(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CATART, 'catart')
        self.AddOrder('catart.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TabGruArt(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_GRUART, 'gruart')
        self.AddJoin(bt.TABNAME_CATART, 'catart')
        self.AddOrder('gruart.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TabMarArt(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_MARART, 'marart')
        self.AddOrder('marart.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TabMagazz(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_MAGAZZ, 'magazz')
        pdc = self.AddJoin(bt.TABNAME_PDC, 'pdc', join=adb.JOIN_LEFT)
        self.AddOrder('magazz.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TabDestinaz(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_DESTIN, 'dest')
        pdc = self.AddJoin(bt.TABNAME_PDC, 'pdc', join=adb.JOIN_LEFT)
        self.Reset()


# ------------------------------------------------------------------------------


class TipiDocumento(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGMAGDOC, 'tipdoc')
        self.AddOrder('tipdoc.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class TipiMovimento(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGMAGMOV, 'tipmov')
        self.AddOrder('tipmov.codice')
        self.Reset()


# ------------------------------------------------------------------------------


class ProdPromo(adb.DbTable):
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_PROMO, 'promo')
        self.AddJoin(bt.TABNAME_PROD, 'prod')
        self.Reset()
        self.AddOrder('prod.codice')
        self.AddOrder('promo.datmin', adb.ORDER_DESCENDING)


# ------------------------------------------------------------------------------


class GriglieCollegatePdc_(adb.DbTable):
    
    anag_table = None
    pdc_master = None
    
    def __init__(self):
        if self.anag_table is None:
            raise 'Classe non istanziabile'
        adb.DbTable.__init__(self, bt.TABNAME_PDC, 'pdc', fields='id,codice,descriz')
        anag = self.AddJoin(self.anag_table, 'anag', idLeft='id', idRight='id', fields=None)
        anag.AddField('IF(anag.grpstop IS NULL, 1, 0)', 'vediprod_all')
        anag.AddField('IF(anag.grpstop="G", 1, 0)',     'vediprod_gra')
        anag.AddField('IF(anag.grpstop="F", 1, 0)',     'vediprod_grf')
        self.AddOrder('pdc.descriz')
        self.Reset()
    
    def SetPdcMaster(self, pm):
        self.pdc_master = pm
        return self.Retrieve('anag.id_pdcgrp=%s', pm)


# ------------------------------------------------------------------------------


class GriglieCollegateClienti(GriglieCollegatePdc_):
    anag_table = bt.TABNAME_CLIENTI


# ------------------------------------------------------------------------------


class GriglieCollegateFornit(GriglieCollegatePdc_):
    anag_table = bt.TABNAME_FORNIT
