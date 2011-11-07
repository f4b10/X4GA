#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/iva.py
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

import MySQLdb

from Env import Azienda
bt = Azienda.BaseTab


MODO_CALCOLO =  1
MODO_SCORPORO = 2

COL_PDCI_ID =  0
COL_ALIQ_ID =  1
COL_PDCI_COD = 2
COL_PDCI_DES = 3
COL_ALIQ_COD = 4
COL_ALIQ_DES = 5
COL_ALIQ_PRC = 6
COL_ALIQ_IND = 7
COL_IMPONIB =  8
COL_IMPOSTA =  9
COL_INDEDUC = 10
COL_TOTALE =  11


class IVA(object):
    def __init__(self, db_curs=None):
        object.__init__(self)
        self.db_curs = db_curs

    def CalcolaIVA(self, id_aliq, 
                   imponib=None, imposta=None, ivato=None, indeduc=None, decimals=None):
        """
        Calcolo dei imponibile, imposta e ivato a partire dal dato a
        disposizione.
        L'id dell'aliquota è ovviamente indispensabile, mentre il calcolo
        effettuato dipende da quale dato si ha a disposizione; si può
        partire da::
            imponib - per determinare imposta e ivato
            imposta - per determinare imponibile e ivato
            ivato   - per determinare imponibile e imposta
        Vengono comunque sempre restituiti i tre importi in tale ordine e
        l'ammontare dell'eventuale iva indeducibile.
        """
        if id_aliq is None or\
           (imponib is None and imposta is None and ivato is None):
            return 0, 0, 0, 0
        cmd =\
"""SELECT codice, descriz, perciva, percind FROM %s WHERE id=%%s"""\
% bt.TABNAME_ALIQIVA
        
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        def R(n):
            return round(n, decimals)
        
        curs = self.db_curs
        if curs is None:
            import stormdb as adb
            con = getattr(adb.db.__database__, '_dbCon')
            curs = con.cursor()
        curs.execute(cmd, id_aliq)
        rs = curs.fetchone()
            
        cod, des, perciva, percind = rs
        perciva /= 100
        percind /= 100
        
        if imponib is not None:
            #calcolo imposta e ivato da imponibile
            imposta = self._Iva_CalcImposta(imponib, perciva, decimals)
            ivato = R(imponib+imposta)
            
        elif ivato is not None:
            #calcolo imponibile e imopsta da ivato
            imponib = self._Iva_ScorpImponib(ivato, perciva, decimals)
            imposta = R(ivato-imponib)
            
        elif imposta is not None:
            #calcolo imponibile e ivato da imposta
            imponib = self._Iva_CalcoliDaImposta(imposta, perciva, decimals)
            ivato = R(imponib+imposta)
        
        indeduc = R(imposta*percind)
        imposta = R(imposta-indeduc)
        
        if curs and self.db_curs is None:
            curs.close()
        
        return imponib, imposta, ivato, indeduc

    def _Iva_CalcImposta(self, imponib, perciva, decimals=None):
        """
        Restituisce l'imposta dall'imponibile e percentuale passati.
        """
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        return round(imponib*perciva, decimals)

    def _Iva_ScorpImponib(self, ivato, perciva, decimals=None):
        """
        Restituisce l'imponibile scorporando la percentuale dalla
        cifra passata.
        """
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        imposta = round(ivato-ivato/(1+perciva), decimals)
        return ivato-imposta
        
    
    def _Iva_CalcoliDaImposta(self, imposta, perciva, decimals=None):
        """
        Determina imponibile e tot.ivato a partire da imposta e percentuale
        passati.
        """
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        try:
            return round(imposta/perciva, decimals)
        except ZeroDivisionError:
            return 0
    
    def CalcolaIva_DaImponibile(self, id_aliq, x, ind=0, decimals=None):
        """
        Wrapper per il metodo CalcolaIva.
        Passare solo id_aliquota e imponibile (e indeducibile, facolt.).
        """
        return self.CalcolaIVA(id_aliq, imponib=x, indeduc=ind, decimals=decimals)
    
    def CalcolaIva_DaIvato(self, id_aliq, x, ind = 0, decimals=None):
        """
        Wrapper per il metodo CalcolaIva.
        Passare solo id_aliquota e tot.ivato (e indeducibile, facolt.).
        """
        return self.CalcolaIVA(id_aliq, ivato=x, indeduc=ind, decimals=decimals)
    
    def CalcolaIva_DaImposta(self, id_aliq, x, ind=0, decimals=None):
        """
        Wrapper per il metodo CalcolaIva.
        Passare solo id_aliquota e imposta (e indeducibile, facolt.).
        """
        return self.CalcolaIVA(id_aliq, imposta=x, indeduc=ind, decimals=decimals)


# ---------------------------------------------------------------------------


import stormdb as adb

class IVA_Table(adb.DbTable):
    
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_ALIQIVA, 'aliq', **kwargs)
        self.Reset()
    
    def CalcolaIVA(self, id_aliq, 
                   imponib=None, imposta=None, ivato=None, indeduc=None, decimals=None):
        """
        Calcolo dei imponibile, imposta e ivato a partire dal dato a
        disposizione.
        L'id dell'aliquota è ovviamente indispensabile, mentre il calcolo
        effettuato dipende da quale dato si ha a disposizione; si può
        partire da::
            imponib - per determinare imposta e ivato
            imposta - per determinare imponibile e ivato
            ivato   - per determinare imponibile e imposta
        Vengono comunque sempre restituiti i tre importi in tale ordine e
        l'ammontare dell'eventuale iva indeducibile.
        """
        if id_aliq is None or\
           (imponib is None and imposta is None and ivato is None):
            return 0, 0, 0, 0
        self.Get(id_aliq)
        
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        def R(n):
            return round(n, decimals)
        
        cod = self.codice
        des = self.descriz
        perciva = (self.perciva or 0)/100
        percind = (self.percind or 0)/100
        
        if imponib is not None:
            #calcolo imposta e ivato da imponibile
            imposta = self._Iva_CalcImposta(imponib, perciva, decimals)
            ivato = R(imponib+imposta)
            
        elif ivato is not None:
            #calcolo imponibile e imopsta da ivato
            imponib = self._Iva_ScorpImponib(ivato, perciva, decimals)
            imposta = R(ivato-imponib)
            
        elif imposta is not None:
            #calcolo imponibile e ivato da imposta
            imponib = self._Iva_CalcoliDaImposta(imposta, perciva, decimals)
            ivato = R(imponib+imposta)
        
        indeduc = R(imposta*percind)
        imposta = R(imposta-indeduc)
        
        return imponib, imposta, ivato, indeduc

    def _Iva_CalcImposta(self, imponib, perciva, decimals=None):
        """
        Restituisce l'imposta dall'imponibile e percentuale passati.
        """
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        return round(imponib*perciva, decimals)

    def _Iva_ScorpImponib(self, ivato, perciva, decimals=None):
        """
        Restituisce l'imponibile scorporando la percentuale dalla
        cifra passata.
        """
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        imposta = round(ivato-ivato/(1+perciva), decimals)
        return ivato-imposta
        
    
    def _Iva_CalcoliDaImposta(self, imposta, perciva, decimals=None):
        """
        Determina imponibile e tot.ivato a partire da imposta e percentuale
        passati.
        """
        if decimals is None:
            decimals = bt.VALINT_DECIMALS
        try:
            return round(imposta/perciva, decimals)
        except ZeroDivisionError:
            return 0
    
    def CalcolaIva_DaImponibile(self, id_aliq, x, ind=0, decimals=None):
        """
        Wrapper per il metodo CalcolaIva.
        Passare solo id_aliquota e imponibile (e indeducibile, facolt.).
        """
        return self.CalcolaIVA(id_aliq, imponib=x, indeduc=ind, decimals=decimals)
    
    def CalcolaIva_DaIvato(self, id_aliq, x, ind = 0, decimals=None):
        """
        Wrapper per il metodo CalcolaIva.
        Passare solo id_aliquota e tot.ivato (e indeducibile, facolt.).
        """
        return self.CalcolaIVA(id_aliq, ivato=x, indeduc=ind, decimals=decimals)
    
    def CalcolaIva_DaImposta(self, id_aliq, x, ind=0, decimals=None):
        """
        Wrapper per il metodo CalcolaIva.
        Passare solo id_aliquota e imposta (e indeducibile, facolt.).
        """
        return self.CalcolaIVA(id_aliq, imposta=x, indeduc=ind, decimals=decimals)


# ---------------------------------------------------------------------------


class ErroreIva(Exception):
    pass
