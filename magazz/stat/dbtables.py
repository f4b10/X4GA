#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/dbtables.py
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

import anag.dbtables as dba
adb = dba.adb

import magazz.dbtables as dbm

import Env
bt = Env.Azienda.BaseTab


class SintesiProVenCli(adb.DbMem):

    def __init__(self):
        adb.DbMem.__init__(self,
                       'pdc_id,pdc_codice,pdc_descriz,prod_id,prod_codice,prod_descriz,totqta,lastdat,lastqta,lastprz,lastsco,lastscmq,lastscmp')
        self.pdc = dba.Clienti()
        self.pdc.Get(-1)
        self.anag = self.pdc.anag

    def Retrieve(self, filtanag=None, filtprod=None, filtmov=None, order="P"):
        filtanag = filtanag or '1'
        filtprod = filtprod or '1'
        filtmov = filtmov or '1'
        filtmov = "%(filtmov)s AND (doc.f_ann IS NULL OR doc.f_ann<>1 AND doc.f_acq IS NULL OR doc.f_acq<>1) AND (mov.f_ann IS NULL OR mov.f_ann<>1)" % locals()
        if order == "P":
            order = "prod.codice"
        elif order == "D":
            order = "pdcprod.maxdat DESC, prod.codice"
        else:
            raise Exception, "Ordinamento errato"
        tmov = adb.DbTable(bt.TABNAME_CFGMAGMOV, 'tipmov', writable=False)
        tmov.Retrieve('tipmov.statftcli IN (1,-1)')
        if tmov.IsEmpty():
            return False
        movids = ','.join([str(tm.id) for tm in tmov])
        scmids = ','.join([str(tm.id) for tm in tmov if tm.tipologia == 'E'])
        filtmov_ven = "("
        filtmov_scm = "("
        if scmids:
            filtmov_ven += "NOT mov.id_tipmov IN (%s) AND " % scmids
            filtmov_scm += "mov.id_tipmov IN (%s) OR " % scmids
        filtmov_ven += "mov.sconto1<99)"
        filtmov_scm += "mov.sconto1>=99)"
        cmd = """
SELECT pdc.id         'pdc_id',
       pdc.codice     'pdc_codice',
       pdc.descriz    'pdc_descriz',
       prod.id        'prod_id',
       prod.codice    'prod_codice',
       prod.descriz   'prod_descriz',
       pdcprod.totqta 'totqta',
       pdcprod.maxdat 'lastdat', (

          SELECT mov.qta
            FROM movmag_h doc
            JOIN movmag_b mov ON mov.id_doc=doc.id
           WHERE mov.id_tipmov IN (%(movids)s) AND doc.id_pdc=pdc.id AND doc.datdoc=lastdat AND mov.id_prod=prod.id AND %(filtmov)s AND %(filtmov_ven)s
        ORDER BY doc.datdoc DESC
           LIMIT 1
) 'lastqta', (
          SELECT mov.prezzo
            FROM movmag_h doc
            JOIN movmag_b mov ON mov.id_doc=doc.id
           WHERE mov.id_tipmov IN (%(movids)s) AND doc.id_pdc=pdc.id AND doc.datdoc=lastdat AND mov.id_prod=prod.id AND %(filtmov)s AND %(filtmov_ven)s
        ORDER BY doc.datdoc DESC
           LIMIT 1
) 'lastprz', (
          SELECT 100*(1-mov.importo/(mov.prezzo*mov.qta))
            FROM movmag_h doc
            JOIN movmag_b mov ON mov.id_doc=doc.id
           WHERE mov.id_tipmov IN (%(movids)s) AND doc.id_pdc=pdc.id AND doc.datdoc=lastdat AND mov.id_prod=prod.id AND %(filtmov)s AND %(filtmov_ven)s
        ORDER BY doc.datdoc DESC
           LIMIT 1
) 'lastsco', (
          SELECT mov.qta
            FROM movmag_h doc
            JOIN movmag_b mov ON mov.id_doc=doc.id
           WHERE mov.id_tipmov IN (%(movids)s) AND doc.id_pdc=pdc.id AND doc.datdoc=lastdat AND mov.id_prod=prod.id AND %(filtmov)s AND %(filtmov_scm)s
        ORDER BY doc.datdoc DESC
           LIMIT 1
) 'lastscmq', (
          SELECT mov.prezzo
            FROM movmag_h doc
            JOIN movmag_b mov ON mov.id_doc=doc.id
           WHERE mov.id_tipmov IN (%(movids)s) AND doc.id_pdc=pdc.id AND doc.datdoc=lastdat AND mov.id_prod=prod.id AND %(filtmov)s AND %(filtmov_scm)s
        ORDER BY doc.datdoc DESC
           LIMIT 1
) 'lastscmp'

  FROM (

   SELECT doc.id_pdc 'pdc_id', mov.id_prod 'prod_id',
          SUM(mov.qta) 'totqta', MAX(doc.datdoc) 'maxdat'

     FROM movmag_b mov

    INNER JOIN movmag_h doc ON mov.id_doc=doc.id
    INNER JOIN prod ON mov.id_prod=prod.id
     LEFT JOIN tipart ON prod.id_tipart=tipart.id
     LEFT JOIN catart ON prod.id_catart=catart.id
     LEFT JOIN gruart ON prod.id_gruart=gruart.id
     LEFT JOIN marart ON prod.id_marart=marart.id
     LEFT JOIN pdc fornit ON prod.id_fornit=fornit.id

    WHERE mov.id_tipmov IN (%(movids)s) AND (%(filtmov)s) AND (%(filtprod)s)

    GROUP BY doc.id_pdc, mov.id_prod

) AS pdcprod

INNER JOIN pdc ON pdcprod.pdc_id=pdc.id
INNER JOIN prod ON pdcprod.prod_id=prod.id
 LEFT JOIN tipart ON prod.id_tipart=tipart.id
 LEFT JOIN catart ON prod.id_catart=catart.id
 LEFT JOIN gruart ON prod.id_gruart=gruart.id
 LEFT JOIN marart ON prod.id_marart=marart.id
 LEFT JOIN pdc fornit ON prod.id_fornit=fornit.id
INNER JOIN clienti cli ON pdc.id=cli.id
 LEFT JOIN agenti age ON cli.id_agente=age.id
 LEFT JOIN zone zona ON cli.id_zona=zona.id

WHERE %(filtanag)s AND %(filtprod)s

ORDER BY pdc.descriz, %(order)s
        """ % locals()
        db = adb.db.__database__
        if db.Retrieve(cmd, asList=False):
            self.SetRecordset(db.rs)
            return True
        return False

    def _UpdateTableVars(self):
        adb.DbMem._UpdateTableVars(self)
        idcli = self.pdc.id
        if idcli != self.pdc_id:
            self.pdc.Get(self.pdc_id)


# ------------------------------------------------------------------------------


class _FatturatoVendite(adb.DbTable):

    _pdctab = bt.TABNAME_CLIENTI
    _pdcalias = None
    _statcol = 'statftcli'

    def __init__(self, *args, **kwargs):

        adb.DbTable.__init__(self, bt.TABNAME_MOVMAG_B, 'mov', fields='id_tipmov')

        tpm = self.AddJoin(bt.TABNAME_CFGMAGMOV,  'tipmov')

        doc = self.AddJoin(bt.TABNAME_MOVMAG_H,   'doc', idLeft='id_doc',
                           idRight='id', fields='id_tipdoc,id_pdc,id_agente')
        tpd = doc.AddJoin(bt.TABNAME_CFGMAGDOC,    'tipdoc')

        pdc = doc.AddJoin(bt.TABNAME_PDC,         'pdc')
        ana = pdc.AddJoin(self._pdctab,           'anag',   join=adb.JOIN_LEFT,
                          idLeft='id', idRight='id')
        cta = ana.AddJoin(bt.TABNAME_CATCLI,      'catana', join=adb.JOIN_LEFT,
                          idLeft='id_categ', idRight='id')

        age = doc.AddJoin(bt.TABNAME_AGENTI,      'agente', join=adb.JOIN_LEFT)

        pro = self.AddJoin(bt.TABNAME_PROD,       'prod',   join=adb.JOIN_LEFT)
        tip = pro.AddJoin(bt.TABNAME_TIPART,      'tipart', join=adb.JOIN_LEFT)
        cat = pro.AddJoin(bt.TABNAME_CATART,      'catart', join=adb.JOIN_LEFT)
        gru = pro.AddJoin(bt.TABNAME_GRUART,      'gruart', join=adb.JOIN_LEFT)
        gru = pro.AddJoin(bt.TABNAME_MARART,      'marart', join=adb.JOIN_LEFT)
        stt = pro.AddJoin(bt.TABNAME_STATART,     'statart',join=adb.JOIN_LEFT,
                          idLeft='id_status', idRight='id')

        self.AddGroups()

        self.AddTotalOf('mov.qta*tipmov.%s' % self._statcol, 'statqtafat')
        self.AddTotalOf('mov.importo*tipmov.%s' % self._statcol, 'statvalfat')
        self.AddTotalOf('(mov.qta*mov.prezzo)*tipmov.%s' % self._statcol, 'statlrdfat')

        self.ClearBaseFilters()

        self.Reset()

    def ClearBaseFilters(self):
        adb.DbTable.ClearBaseFilters(self)
        self.AddBaseFilter('tipmov.%s IN (1,-1)' % self._statcol)
        self.AddBaseFilter('(doc.f_ann IS NULL OR doc.f_ann<>1) AND (doc.f_acq IS NULL OR doc.f_acq<>1) AND (mov.f_ann IS NULL OR mov.f_ann<>1)')


# ------------------------------------------------------------------------------


class FatturatoClienti(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('pdc.id')


# ------------------------------------------------------------------------------


class FatturatoCliPro(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('pdc.id')
        self.AddGroupOn('prod.id')


# ------------------------------------------------------------------------------


class FatturatoCliCatArt(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('pdc.id')
        self.AddGroupOn('catart.id')


# ------------------------------------------------------------------------------


class FatturatoCatArt(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('catart.id')


# ------------------------------------------------------------------------------


class FatturatoAgenti(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('agente.id')


# ------------------------------------------------------------------------------


class FatturatoProdotti(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('prod.id')


# ------------------------------------------------------------------------------


class FatturatoProCli(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('prod.id')
        self.AddGroupOn('pdc.id')


# ------------------------------------------------------------------------------


class FatturatoProCatCli(_FatturatoVendite):

    def AddGroups(self):
        self.AddGroupOn('prod.id')
        self.AddGroupOn('catana.id')


# ------------------------------------------------------------------------------


class ValutaPrezziVendita(adb.DbTable):

    statftcol = 'statftcli'

    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_MOVMAG_B, 'mov', fields=None)
        pro = self.AddJoin(bt.TABNAME_PROD,      'prod',   fields=None)
        tpm = self.AddJoin(bt.TABNAME_CFGMAGMOV, 'tipmov', fields=None, idLeft='id_tipmov')
        doc = self.AddJoin(bt.TABNAME_MOVMAG_H,  'doc',    fields=None, idLeft='id_doc')
        cli = doc.AddJoin(bt.TABNAME_PDC,        'pdc',    fields=None, idLeft='id_pdc')
        tpd = doc.AddJoin(bt.TABNAME_CFGMAGDOC,  'tipdoc', fields=None, idLeft='id_tipdoc')
        age = doc.AddJoin(bt.TABNAME_AGENTI,     'agente', fields=None, join=adb.JOIN_LEFT, idLeft='id_agente')
        sts = pro.AddJoin(bt.TABNAME_STATART,    'status', fields=None, join=adb.JOIN_LEFT, idLeft='id_status', idRight='id')
        cat = pro.AddJoin(bt.TABNAME_CATART,     'catart', fields=None, join=adb.JOIN_LEFT)
        gru = pro.AddJoin(bt.TABNAME_GRUART,     'gruart', fields=None, join=adb.JOIN_LEFT)
        tip = pro.AddJoin(bt.TABNAME_TIPART,     'tipart', fields=None, join=adb.JOIN_LEFT)
        frn = pro.AddJoin(bt.TABNAME_PDC,        'fornit', fields=None, join=adb.JOIN_LEFT, idLeft='id_fornit', idRight='id')
        self.AddGroupOn('prod.id',         'prod_id')
        self.AddGroupOn('prod.codice',     'prod_codice')
        if bt.MAGFORLIS:
            self.AddGroupOn('prod.codfor', 'prod_codfor')
        self.AddGroupOn('prod.descriz',    'prod_descriz')
        self.AddGroupOn('prod.costo',      'prod_costo')
        self.AddGroupOn('prod.prezzo',     'prod_prezzo')
        self.AddMinimumOf('mov.prezzo',    'prezzoun')
        self.AddMaximumOf('mov.prezzo',    'prezzoun')
        self.AddAverageOf('mov.prezzo',    'prezzoun')
        self.AddMinimumOf('mov.importo/IF(mov.qta IS NULL or mov.qta=0,1,mov.qta)', 'prezzosc')
        self.AddMaximumOf('mov.importo/IF(mov.qta IS NULL or mov.qta=0,1,mov.qta)', 'prezzosc')
        self.AddAverageOf('mov.importo/IF(mov.qta IS NULL or mov.qta=0,1,mov.qta)', 'prezzosc')
        self.AddBaseFilter('tipmov.%s=1 AND mov.prezzo IS NOT NULL AND mov.prezzo<>0' % self.statftcol)
        self.Reset()


# ------------------------------------------------------------------------------


class ValutaCostiAcquisto(ValutaPrezziVendita):
    statftcol = 'statftfor'


# ------------------------------------------------------------------------------


class MovimentiPrezzi(dbm.Movim):

    def __init__(self, *args, **kwargs):
        dbm.Movim.__init__(self, *args, **kwargs)
        self.AddField('mov.importo/IF(mov.qta IS NULL or mov.qta=0,1,mov.qta)', 'presco')
        self.Reset()


# ------------------------------------------------------------------------------


class ReddVend(adb.DbTable):

    def __init__(self):
        adb.DbTable.__init__(self, 'stat_reddvend', 'rv', primaryKey='doc_id')
        self.Reset()




class _FatturatoAcquisti(adb.DbTable):

    _pdctab = bt.TABNAME_FORNIT
    _pdcalias = None
    _statcol = 'statftfor'

    def __init__(self, *args, **kwargs):

        adb.DbTable.__init__(self, bt.TABNAME_MOVMAG_B, 'mov', fields='id_tipmov')

        tpm = self.AddJoin(bt.TABNAME_CFGMAGMOV,  'tipmov')

        doc = self.AddJoin(bt.TABNAME_MOVMAG_H,   'doc', idLeft='id_doc',
                           idRight='id', fields='id_tipdoc,id_pdc,id_agente')
        tpd = doc.AddJoin(bt.TABNAME_CFGMAGDOC,    'tipdoc')

        pdc = doc.AddJoin(bt.TABNAME_PDC,         'pdc')
        ana = pdc.AddJoin(self._pdctab,           'anag',   join=adb.JOIN_LEFT,
                          idLeft='id', idRight='id')
        cta = ana.AddJoin(bt.TABNAME_CATCLI,      'catana', join=adb.JOIN_LEFT,
                          idLeft='id_categ', idRight='id')

        age = doc.AddJoin(bt.TABNAME_AGENTI,      'agente', join=adb.JOIN_LEFT)

        pro = self.AddJoin(bt.TABNAME_PROD,       'prod',   join=adb.JOIN_LEFT)
        tip = pro.AddJoin(bt.TABNAME_TIPART,      'tipart', join=adb.JOIN_LEFT)
        cat = pro.AddJoin(bt.TABNAME_CATART,      'catart', join=adb.JOIN_LEFT)
        gru = pro.AddJoin(bt.TABNAME_GRUART,      'gruart', join=adb.JOIN_LEFT)
        gru = pro.AddJoin(bt.TABNAME_MARART,      'marart', join=adb.JOIN_LEFT)
        stt = pro.AddJoin(bt.TABNAME_STATART,     'statart',join=adb.JOIN_LEFT,
                          idLeft='id_status', idRight='id')

        self.AddGroups()

        self.AddTotalOf('mov.qta*tipmov.%s' % self._statcol, 'statqtafat')
        self.AddTotalOf('mov.importo*tipmov.%s' % self._statcol, 'statvalfat')
        self.AddTotalOf('(mov.qta*mov.prezzo)*tipmov.%s' % self._statcol, 'statlrdfat')

        self.ClearBaseFilters()

        self.Reset()

    def ClearBaseFilters(self):
        adb.DbTable.ClearBaseFilters(self)
        self.AddBaseFilter('tipmov.%s IN (1,-1)' % self._statcol)
        self.AddBaseFilter('(doc.f_ann IS NULL OR doc.f_ann<>1) AND (doc.f_acq IS NULL OR doc.f_acq<>1) AND (mov.f_ann IS NULL OR mov.f_ann<>1)')

class FatturatoFornitori(_FatturatoAcquisti):

    def AddGroups(self):
        self.AddGroupOn('pdc.id')



class FatturatoForCatArt(_FatturatoAcquisti):

    def AddGroups(self):
        self.AddGroupOn('pdc.id')
        self.AddGroupOn('catart.id')

