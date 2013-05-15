#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/provage/dbtables.py
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


import Env
bt = Env.Azienda.BaseTab

import stormdb as adb


class ProvvigAgentiDetTable(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_MOVMAG_B, 'mov', fields=None)
        tpm = self.AddJoin(bt.TABNAME_CFGMAGMOV, 'tipmov', idLeft='id_tipmov', fields=None)
        pro = self.AddJoin(bt.TABNAME_PROD,      'prod', idLeft='id_prod', fields=None, join=adb.JOIN_LEFT)
        iva = self.AddJoin(bt.TABNAME_ALIQIVA,   'aliqiva', idLeft='id_aliqiva', fields=None)
        doc = self.AddJoin(bt.TABNAME_MOVMAG_H,  'doc', idLeft='id_doc', fields=None)
        tpd = doc.AddJoin(bt.TABNAME_CFGMAGDOC,  'tipdoc', idLeft='id_tipdoc', fields=None)
        age = doc.AddJoin(bt.TABNAME_AGENTI,     'age', idLeft='id_agente', fields=None)
        pdc = doc.AddJoin(bt.TABNAME_PDC,        'pdc', idLeft='id_pdc', fields=None)
        dst = doc.AddJoin(bt.TABNAME_DESTIN,     'dest', idLeft='id_dest', fields=None, join=adb.JOIN_LEFT)
        sca = doc.AddJoin(bt.TABNAME_CONTAB_S,   'sca', idLeft='id_reg', idRight='id_reg', fields=None, join=adb.JOIN_LEFT)
        pcf = sca.AddJoin(bt.TABNAME_PCF,        'pcf', idLeft='id_pcf', fields=None, join=adb.JOIN_LEFT)
        
        self._AddGroups()
        
        self.AddTotalOf('mov.importo*(tipdoc.provvig)', 'vendita')
        self.AddAverageOf('IF(mov.perpro IS NULL, prod.perpro, mov.perpro)', 'perpro')
        self.AddTotalOf('mov.importo*IF(mov.perpro IS NULL, prod.perpro, mov.perpro)*(tipdoc.provvig)/100', 'provvig')
        self.AddTotalOf('pcf.imptot-pcf.imppar', 'saldo')
        
        self.AddBaseFilter('tipdoc.provvig IN (1, -1)')
        self.AddBaseFilter('tipmov.noprovvig IS NULL OR tipmov.noprovvig<>1')
        self.AddBaseFilter('age.noprovvig IS NULL OR age.noprovvig<>1')
        
        self._AddOrders()
        self.Reset()
    
    def _AddGroups(self):
        self.AddGroupOn('mov.id',          'mov_id')
        self.AddGroupOn('mov.id_doc',      'mov_id_doc')
        self.AddGroupOn('doc.datreg',      'doc_datreg')
        self.AddGroupOn('doc.datdoc',      'doc_datdoc')
        self.AddGroupOn('doc.numdoc',      'doc_numdoc')
        self.AddGroupOn('doc.id_agente',   'age_id')
        self.AddGroupOn('age.codice',      'age_codice')
        self.AddGroupOn('age.descriz',     'age_descriz')
        self.AddGroupOn('pdc.id',          'pdc_id')
        self.AddGroupOn('pdc.codice',      'pdc_codice')
        self.AddGroupOn('pdc.descriz',     'pdc_descriz')
        self.AddGroupOn('dest.codice',     'dest_codice')
        self.AddGroupOn('dest.descriz',    'dest_descriz')
        self.AddGroupOn('tipdoc.codice',   'tipdoc_codice')
        self.AddGroupOn('tipdoc.descriz',  'tipdoc_descriz')
        self.AddGroupOn('aliqiva.codice',  'aliqiva_codice')
        self.AddGroupOn('aliqiva.descriz', 'aliqiva_descriz')
        self.AddGroupOn('prod.id',         'prod_id')
        self.AddGroupOn('prod.codice',     'prod_codice')
        self.AddGroupOn('mov.numriga',     'mov_numriga')
        self.AddGroupOn('tipmov.codice',   'tipmov_codice')
        self.AddGroupOn('tipmov.descriz',  'tipmov_descriz')
        self.AddGroupOn('mov.descriz',     'mov_descriz')
        self.AddGroupOn('mov.qta',         'mov_qta')
        self.AddGroupOn('mov.prezzo',      'mov_prezzo')
        self.AddGroupOn('mov.sconto1',     'mov_sconto1')
        self.AddGroupOn('mov.sconto2',     'mov_sconto2')
        self.AddGroupOn('mov.sconto3',     'mov_sconto3')
        self.AddGroupOn('mov.sconto4',     'mov_sconto4')
        self.AddGroupOn('mov.sconto5',     'mov_sconto5')
        self.AddGroupOn('mov.sconto6',     'mov_sconto6')
    
    def _AddOrders(self):
        self.AddOrder('age.codice')
        self.AddOrder('doc.datdoc')
        self.AddOrder('tipdoc.codice')
        self.AddOrder('doc.numdoc')
        self.AddOrder('mov.numriga')


# ------------------------------------------------------------------------------


class ProvvigAgentiTotTable(ProvvigAgentiDetTable):
    
    def _AddGroups(self):
        self.AddGroupOn('doc.id',         'doc_id')
        self.AddGroupOn('doc.datreg',     'doc_datreg')
        self.AddGroupOn('doc.datdoc',     'doc_datdoc')
        self.AddGroupOn('doc.numdoc',     'doc_numdoc')
        self.AddGroupOn('doc.id_agente',  'age_id')
        self.AddGroupOn('age.codice',     'age_codice')
        self.AddGroupOn('age.descriz',    'age_descriz')
        self.AddGroupOn('pdc.id',         'pdc_id')
        self.AddGroupOn('pdc.codice',     'pdc_codice')
        self.AddGroupOn('pdc.descriz',    'pdc_descriz')
        self.AddGroupOn('dest.codice',    'dest_codice')
        self.AddGroupOn('dest.descriz',   'dest_descriz')
        self.AddGroupOn('tipdoc.codice',  'tipdoc_codice')
        self.AddGroupOn('tipdoc.descriz', 'tipdoc_descriz')
    
    def _AddOrders(self):
        self.AddOrder('age.codice')
        self.AddOrder('doc.datdoc')
        self.AddOrder('tipdoc.codice')
        self.AddOrder('doc.numdoc')
