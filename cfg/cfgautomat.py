#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/cfgautomat.py
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


class AutomatException(Exception):
    pass


# ------------------------------------------------------------------------------


class CfgAutomat(object):
    """
    Lettura e caricamento automatismi.  BaseClass per automatismi specifici
    derivati.
    La variabile di classe C{_autoKeys} è un dizionario; vedere il metodo
    L{CfgAutomat.ReadAutomat}
    """
    def __init__(self, db_curs):
        """
        Costruttore.  Passare il cursore di database che verrà
        utilizzato per accedere alla tabella degli automatismi.
        """
        object.__init__(self)
        self.db_curs = db_curs
        self._autoKeys = {}

    def ReadAutomat(self):
        """
        Lettura automatismi definiti in C{self._autoKeys}.
        C{self._autoKeys} è un dizionario, contenente come chiave il codice
        dell'automatismo e come valore il flag (C{True/False}) che indica
        se l'automatismo è obbligatorio o meno.
        Se tutte le chiavi obbligatorie presenti nel dizionario sono
        presenti nella tabella degli automatismi, esse verranno caricate
        insieme alle chiavi facoltative nel dizionario locale della classe,
        originando anche, per ogni automatismo (obbligatorio o meno),
        una variabile di istanza, denominata C{_auto_xxx}, dove C{xxx} è
        il nome della chiave.::
            
            self._Auto_AddKeys({"test": False}) => self._auto_test
            
        Il contenuto di tale variabile è prelevato dalla tabella degli
        automatismi::
        
            self._Auto_AddKeys({"test": True}) => self._auto_test
        solo se esiste nella tabella automatismi la voce "test"
        """
        
        totautomat = 0
        
        cmd =\
"""SELECT codice, descriz, aut_id """\
"""FROM %s ORDER BY codice ASC;""" % bt.TABNAME_CFGAUTOM
        
        try:
            self.db_curs.execute(cmd)
            rs = self.db_curs.fetchall()
            
        except MySQLdb.Error, e:
            MsgDialogDbError(None, e)
            
        else:
            
            missedKeys = []
            
            for loadKey, needed in self._autoKeys.iteritems():
                missing = False
                if needed:
                    try:
                        n = ListSearch(rs,\
                                   lambda x: x[0].strip().lower() == loadKey)
                    except IndexError, e:
                        missing = True
                    else:
                        if not rs[n][2]:
                            missing = True
                    if missing:
                        missedKeys.append(loadKey)
            
            if len(missedKeys)>0:
                raise AutomatException, \
                      """Impossibile proseguire per la mancanza dei """\
                      """seguenti automatismi:\n\n%s""" % ", ".join(missedKeys)
            
            for au_key, au_desc, au_id in rs:
                au_key = au_key.strip().lower()
                if self._autoKeys.has_key(au_key):
                    self.__setattr__("_auto_%s" % au_key,  au_id)
                    del self._autoKeys[au_key]
                    totautomat += 1
        
        return totautomat

    def _Auto_AddKeys(self, params):
        for key,obbl in params.iteritems():
            self._autoKeys[key] = obbl
        return self.ReadAutomat()

    def _Auto_AddKeysPdcTip(self):
        """
        Tipi anagrafici x cassa, banca, clienti, fornitori.
        """
        for key, need in (('bilmas', True),
                          ('bilcon', True),
                          ('bilcee', bt.CONBILRCEE == 1),):
            for tab in ( bt.TABNAME_CASSE,
                         bt.TABNAME_BANCHE,
                         bt.TABNAME_CLIENTI,
                         bt.TABNAME_FORNIT,
                         bt.TABNAME_EFFETTI):
                self._autoKeys["%s_%s" % (key, tab)] = need
        return self.ReadAutomat()

    def _Auto_AddKeysContab(self):
        """
        Automatismi di tipo contabile.
        """
        pass

    def _Auto_AddKeysContabTipo_I(self, read=True):
        """
        Automatismi di tipo contabile per registrazioni di tipo IVA.
        Automatismi obbligatori::
            - ivaacq - id pdc sottoconto iva acquisti
            - ivaven - id pdc sottoconto iva vendite
            
        Automatismi facoltativi, caricati solo se presenti::
            - ivaind    - id pdc sottoconto iva indeducibile
            - ivacor    - id pdc sottoconto iva corrispettivi
            - ivaacqcee - id pdc sottoconto iva acquisti cee
            - ivaacqsos - id pdc sottoconto iva acquisti in sospensione
            - omaggi    - id pdc sottoconto omaggi
        """
        self._autoKeys["ivaacq"] = True
        self._autoKeys["ivaven"] = True
        self._autoKeys["ivaind"] = False
        self._autoKeys["ivacor"] = False
        self._autoKeys["ivaacqcee"] = False
        self._autoKeys["ivaacqsos"] = False
        self._autoKeys["ivavensos"] = False
        self._autoKeys["omaggi"] = False
        if read:
            self.ReadAutomat()

    def _Auto_AddKeysContabTipo_SC(self, read=True):
        """
        Automatismi di tipo contabile per registrazioni in saldaconto.
        Automatismi obbligatori::
            - abbatt - id pdc abbuoni attivi
            - abbpas - id pdc abbuoni passivi
            - speinc - id pdc spese incasso
        """
        self._autoKeys["abbatt"] = True
        self._autoKeys["abbpas"] = True
        self._autoKeys["speinc"] = False
        if read:
            self.ReadAutomat()

    def _Auto_AddKeysMagazz(self, read=True):
        """
        Automatismi di magazzino.
        Automatismi facoltativi::
            - magomaggi - id pdc sottoconto omaggi
            - magivascm - id aliquota iva per sconto merce
            - magivacee - id aliquota iva per vendite cee
            - magivaest - id aliquota iva per vendite estero
            - magivadef - id aliquota iva di default
        """
        self._autoKeys["magomaggi"] = False
        self._autoKeys["magivascm"] = False
        self._autoKeys["magivacee"] = False
        self._autoKeys["magivaest"] = False
        self._autoKeys["magivadef"] = False
        self._autoKeys["pdctip_costi"] = False
        self._autoKeys["pdctip_ricavi"] = False
        self._Auto_AddKeysContabTipo_I(read=False)
        if read:
            self.ReadAutomat()


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    app = wx.PySimpleApp()
    app.MainLoop()
    Azienda.DB.testdb()
    
    test = CfgAutomat(Azienda.DB.connection.cursor())
    print "%d automatismi caricati: " % test._Auto_AddKeysMagazz()
    for key, val in test.__dict__.iteritems():
        if key.startswith("_auto_"):
            print key, val
