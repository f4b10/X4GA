#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/cfgprogr.py
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

import wx

import MySQLdb

from Env import Azienda
bt = Azienda.BaseTab

from awc.util import MsgDialog, MsgDialogDbError, ListSearch


TYPE_NUM =    1
TYPE_DATE =   2
TYPE_TOTAL1 = 4
TYPE_TOTAL2 = 8


class CfgProgr(object):
    """
    Lettura e caricamento progressivi configurati in C{_progrKeys}.
    Vedere L{CfgProgr._Progr_AddKeys()}
    """
    def __init__(self, db_curs):
        """
        Costruttore.  Passare l'oggetto cursore di database che verrà
        utilizzato per accedere alla tabella degli automatismi.
        """
        object.__init__(self)
        self.db_curs = db_curs
        self._progrKeys = []

    def ReadProgr(self):
        """
        Caricamento progressivi specificati in C{self.:_progrKeys}
        Per ogni elemento presente in C{self.:_progrKeys}, vengono
        create una o più variabili di istanza, in base a quanto richiesto
        nel tipo::
            self._Progr_AddKeys(("test",None,None))
            self.ReadProgr() => _progr_test_num  se tipo comprende TYPE_NUM
                              e _progr_test_date se tipo comprende TYPE_DATE
                              e _progr_test_tot1 se tipo comprende TYPE_TOTAL1
                              e _progr_test_tot2 se tipo comprende TYPE_TOTAL2
        
        Ad ognuna di queste variabili viene assegnato il corrispondente
        valore presente nella tabella progressivi, o None nel caso non sia
        presente in tale tabella.
        """
        totprogr = 0
        try:
            for key,id,diff,ptype in self._progrKeys:
                par = []
                if id is None:
                    filt = "key_id IS NULL"
                else:
                    filt = "key_id=%s"
                    par.append(id)
                filt += " and "
                if diff is None:
                    filt += "keydiff IS NULL"
                else:
                    filt += "keydiff=%s"
                    par.append(diff)
                cmd =\
"""SELECT descriz, progrnum, progrdate, progrimp1, progrimp2 """\
"""FROM %s WHERE %s and codice=%%s;""" % (bt.TABNAME_CFGPROGR, filt)
                par.append(key)
                key = "_progr_"+key
                self.db_curs.execute(cmd, par)
                rs = self.db_curs.fetchone()
                if rs:
                    values = [rs[col] for col in range(1,5)]
                else:
                    values = [None for col in range(2,6)]
                if ptype & TYPE_NUM:
                    self.__setattr__("%s_num" % key, values[0] or 0)
                if ptype & TYPE_DATE:
                    self.__setattr__("%s_date" % key, values[1])
                if ptype & TYPE_TOTAL1:
                    self.__setattr__("%s_tot1" % key, values[2] or 0)
                if ptype & TYPE_TOTAL2:
                    self.__setattr__("%s_tot2" % key, values[3] or 0)
                totprogr += 1
        except MySQLdb.Error, e:
            MsgDialogDbError(None, e)
        return totprogr

    def _Clear_AllKeys(self):
        """
        Rimozione di tutte le chiavi e le variabili di istanza create.
        progressivi.
        """
        for key,id,diff,ptype in self._progrKeys:
            try:
                if ptype & TYPE_NUM:
                    self.__delattr__("%s_num" % key)
                if ptype & TYPE_DATE:
                    self.__delattr__("%s_date" % key)
                if ptype & TYPE_TOTAL1:
                    self.__delattr__("%s_tot1" % key)
                if ptype & TYPE_TOTAL2:
                    self.__delattr__("%s_tot2" % key)
            except:
                pass
        self._progrKeys = ()

    def _Progr_AddKeys(self, keys):
        """
        Aggiunta chiavi per lettura progressivi
        C{keys} contiene l'elenco dei progressivi da caricare, con la
        seguente struttura::
            - key
            - id
            - insieme dei dati da caricare; uno o più fra i tipi:
                - TYPE_NUM
                - TYPE_DATE
                - TYPE_TOTAL1
                - TYPE_TOTAL2
        Nel caso occorrano più dati da caricare (ad esempio numero e data),
        tali tipi possono essere combinati tramite or::
            TYPE_NUM | TYPE_DATE
            
        Vedere L{CfgProgr.ReadProgr} per i dettagli del caricamento dei
        progressivi.
        """
        for key,id,diff,ptype in keys:
            try:
                n = ListSearch(self._progrKeys, lambda x: x[0] == key)
                self._progrKeys[n] = (key, id, diff, ptype)
            except IndexError:
                self._progrKeys.append((key, id, diff, ptype))
        self.ReadProgr()

    def _Progr_AddKeysContab(self, year):
        """
        C{CfgProgr._Progr_AddKeysContab(self, year)}
        Progessivi di tipo contabile::
            - ccg_giobol_ec   numero e data dell'ultima stampa di giornale esercizio in corso
            - ccg_mastri      data ultima stampa mastrini
            - ccg_aggcon      data ultimo aggiornamento contabile
            - ccg_apertura    data ultimo movimento di apertura
            - ccg_chiusura    data ultimo movimento di chiusura
            - ccg_apechi_flag flag movimenti generati
        Tutti i progressivi sono riferiti ad un determinato esercizio.
        
        @param year: anno esercizio
        @type year: int
        """ 
        self._Progr_AddKeys(\
            (( "ccg_giobol",      None,    0, TYPE_DATE|TYPE_NUM ),\
             ( "ccg_mastri",      None, year, TYPE_DATE ),\
             ( "ccg_aggcon",      None,    0, TYPE_DATE ),\
             ( "ccg_apertura",    None,    0, TYPE_DATE ),\
             ( "ccg_chiusura",    None,    0, TYPE_DATE ),\
             ( "ccg_apechi_flag", None,    0, TYPE_NUM  )) )

    def _Progr_AddKeysContabTipo_I(self, year, id_regiva):
        """
        Progressivi di tipo IVA::
            - iva_stareg  numero e data ultima stampa fiscale del registro
            - iva_datins  numero e data ultima registrazione del registro
            
        Tutti i progressivi sono riferiti ad un determinato esercizio e
        registro IVA.
        
        @param year: anno esercizio
        @type year: int
        @param id_regiva: id registro IVA
        #type id_regiva: int
        """
#        self._Progr_AddKeys(\
# (( "iva_stareg", id_regiva, year, TYPE_NUM | TYPE_DATE ),\
#  ( "iva_ultins", id_regiva, year, TYPE_NUM | TYPE_DATE )) )
        pass

    def _Progr_AddKeysMagazz(self):
        """
        C{CfgProgr._Progr_AddKeysContab(self, year)}
        Progessivi di tipo contabile::
            - mag_chiusura    data dell'ultima chiusura
            - mag_archiv      data ultima archiviazione movimenti
        """ 
        self._Progr_AddKeys(\
            (( "mag_chiusura",    None, None, TYPE_DATE ),\
             ( "mag_archiv",      None, None, TYPE_DATE )) )


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    app = wx.PySimpleApp()
    app.MainLoop()
    Azienda.DB.testdb()
    
    test = CfgProgr(Azienda.DB.connection.cursor())
    test._Progr_AddKeys((("test",None,None,TYPE_NUM|TYPE_DATE),))
    test._Progr_AddKeysContab("2004")
    test._Progr_AddKeysContabTipo_I("2004", 58) #reg.iva acquisti
    test._Progr_AddKeysMagazz()
    print "%d progressivi caricati: " % test.ReadProgr()
    for key, val in test.__dict__.iteritems():
        if key.startswith("_progr_"):
            print key, val
