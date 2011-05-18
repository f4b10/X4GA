#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/cfgmagazz.py
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

import stormdb as adb

from awc.util import MsgDialog, MsgDialogDbError

from Env import Azienda
bt = Azienda.BaseTab


#costanti per accesso a matrice documenti da acquisire in cfg. doc.
#CfgDocMov.AcquisDocs()
ACQDOC_ID =      0
ACQDOC_COPY =    1
ACQDOC_CODICE =  2
ACQDOC_DESCRIZ = 3

class CfgDocMov(adb.DbTable):
    """
    Configurazione documento magazzino.
    """
    def __init__(self, *args, **kwargs):
        """
        Costruttore.
        C{CfgDocumento.__init__(self)}
        """
        self._dockeys = ("id",        #Id causale
                         "codice",    #Codice causale
                         "descriz",   #Descrizione causale
                         "valuta",    #Flag valuta
                         "id_pdctip", #ID Tipo sottoconto
                         "descanag",  #Descrizione tipo sottoconto
                         "datdoc",    #Flag tipo data documento
                         "numdoc",    #Flag tipo numero documento
                         "docfam",    #Famiglia documenti
                         "ctrnum",    #Flag controllo numero documento
                         "aggnum",    #Flag aggiornamento numero documento
                         "id_acqdoc1",#ID Documento da acquisire #1
                         "id_acqdoc2",#ID Documento da acquisire #2
                         "id_acqdoc3",#ID Documento da acquisire #3
                         "id_acqdoc4",#ID Documento da acquisire #4
                         "tipacq1",   #Flag tipo acquisizione documento #1
                         "tipacq2",   #Flag tipo acquisizione documento #2
                         "tipacq3",   #Flag tipo acquisizione documento #3
                         "tipacq4",   #Flag tipo acquisizione documento #4
                         "annacq1",   #Flag annullamento documento acquisito #1
                         "annacq2",   #Flag annullamento documento acquisito #2
                         "annacq3",   #Flag annullamento documento acquisito #3
                         "annacq4",   #Flag annullamento documento acquisito #4
                         "askmagazz", #Flag richiesta magazzino
                         "askmodpag", #Flag richiesta mod.pagamento
                         "askdestin", #Flag richiesta destinatario
                         "askrifdesc",#Flag richiesta descrizione riferimento
                         "askrifdata",#Flag richiesta data riferimento
                         "askrifnum", #Flag richiesta numero riferimento
                         "askagente", #Flag richiesta agente
                         "askzona",   #Flag richiesta zona
                         "asklist",   #Flag richiesta listino
                         "colcg",     #Flag collegamento contabile
                         "id_caucg",  #ID Causale contabile
                         "askprotiva",#Flag richiesta protocollo IVA
                         "scorpiva",  #Flag scorporo IVA
                         "totali",    #Flag visualizzazione totali
                         "totzero",   #Flag permesso totale documento nullo
                         "totneg",    #Flag permesso totale documento negativo
                         "tiposta",   #Tipo stampa
                         "staobb",    #Flag stampa obbligatoria
                         "stanoc",    #Flag stampa non contabile
                         "listxmov",  #Flag richiesta listino x ogni riga di mov
                         "asktracau", #Flag causale trasp.
                         "asktracur", #Flag trasp. a cura
                         "asktravet", #Flag vettore
                         "asktraasp", #Flag aspetto beni
                         "asktrapor", #Flag porto
                         "asktracon", #Flag tipo contrass.
                         "asktrakgc", #Flag peso/colli
                         "custde")    #Nome personalizzazione dataentry
        
        self._forcebooldoc = ("ctrnum",\
                              "aggnum",\
                              "pienum",\
                              "askmagazz",\
                              "askmodpag",\
                              "askdestin",\
                              "askrifdesc",\
                              "askrifdata",\
                              "askrifnum",\
                              "askagente",\
                              "askzona",\
                              "asklist",\
                              "totzero",\
                              "totneg",\
                              "staobb",\
                              "stanoc",\
                              "asktracau",\
                              "asktracur",\
                              "asktravet",\
                              "asktraasp",\
                              "asktrapor",\
                              "asktracon",\
                              "asktrakgc")
        
        self._movkeys = ("id",        #Id movimento
                         "codice",    #Codice movimento
                         "descriz",   #Descrizione movimento
                         "aggcosto",  #Flag aggiornamento costo
                         "aggprezzo", #Flag aggiornamento prezzo
                         "aggini",    #Flag +/- aggiornamento giac.iniziale
                         "aggcar",    #Flag +/- aggiornamento carichi
                         "aggcarv",   #Flag +/- aggiornamento valore carichi
                         "aggsca",    #Flag +/- aggiornamento scarichi
                         "aggscav",   #Flag +/- aggiornamento valore scarichi
                         "aggordcli", #Flag +/- aggiornamento ord.cliente
                         "aggordfor", #Flag +/- aggiornamento ord.fornitore
                         "aggfornit", #Flag aggiornamento fornitore
                         "askvalori", #Flag richiesta quantità
                         "mancosto",  #Management costo riga
                         "id_pdc",    #ID Sottoconto per collegam. contabile
                         "stadesc",   #Descrizione in stampa
                         "tipvaluni", #Tipo di valore unitario da proporre
                         "tipsconti", #Tipo di sconti da proporre
                         "noprint",   #Flag esclusione righe da stampa doc.
                         "f_acqpdt")  #Flag acquisizione letture da pdt
        
        adb.DbTable.__init__(self, bt.TABNAME_CFGMAGDOC, "tipdoc")
        
        dbmov = self.AddMultiJoin(\
            bt.TABNAME_CFGMAGMOV, "tipmov")
        dbmov.AddOrder("tipmov.codice")
        
        dbpdc = dbmov.AddJoin(\
            bt.TABNAME_PDC,       "pdc",\
            join=adb.JOIN_LEFT)
        
        dbmas = dbpdc.AddJoin(\
            bt.TABNAME_BILMAS,    "bilmas",\
            join=adb.JOIN_LEFT)
        
        cfgcg = self.AddJoin(\
            bt.TABNAME_CFGCONTAB, "caucon", idLeft="id_caucg",\
            join=adb.JOIN_LEFT)
        
        cfgri = cfgcg.AddJoin(\
            bt.TABNAME_REGIVA,    "regiva",\
            join=adb.JOIN_LEFT)
        
        cfgcg.AddMultiJoin(\
            bt.TABNAME_CFGMAGRIV, "magriv",  idLeft="id", idRight="id_caus")
        
        def _NoWrite(*args):
            pass
        self._SaveRecords = _NoWrite
        
        self.Get(-1)

    def _UpdateTableVars(self, *args, **kwargs):
        adb.DbTable._UpdateTableVars(self, *args, **kwargs)
        if not self.custde:
            self.custde = 'standard'
        for field in self._forcebooldoc:
            self.__setattr__(field, bool(self.__getattribute__(field)))

    def CfgDocumentoIsValid(self):
        return self.cfgdoc.RowsCount() == 1

    def FindMov(self, movid):
        out = False
        if self.RowsCount() == 1:
            if self.mov.Locate(lambda mov: mov.id == movid):
                out = True
        return out
    
    def AcquisDocs(self, soloevas=False, solocheck=False):
        if soloevas:
            modi = 'E'
        else:
            modi = 'CEA'
        docs = []
        dbd = adb.DbTable(bt.TABNAME_CFGMAGDOC, "tipdoc")
        for adn in range(1,5):
            docid = getattr(self, "id_acqdoc%d" % adn)
            modo = getattr(self, "tipacq%d" % adn, '')
            ann = getattr(self, "annacq%d" % adn, 0)
            chk = getattr(self, "checkacq%d" % adn, 0)
            if docid is not None and modo in modi:
                dbd.Get(docid)
                if chk or not solocheck:
                    docs.append((docid, modo, bool(ann), dbd.codice, dbd.descriz))
        del dbd
        return docs
    
    def HasAcquisDocs(self):
        return (self.id_acqdoc1 is not None and self.tipacq1 is not None) or\
               (self.id_acqdoc2 is not None and self.tipacq2 is not None) or\
               (self.id_acqdoc3 is not None and self.tipacq3 is not None) or\
               (self.id_acqdoc4 is not None and self.tipacq4 is not None)
    
    def GetAcqPDTMov(self):
        out = None
        if self.tipmov.Locate(lambda x: x.f_acqpdt == 1):
            out = self.tipmov.id
        return out
    
    def IsPrintable(self):
        p = False
        if self.toolprint:
            p = True
        return p
    
    def HasMovAcconto(self):
        for tipmov in self.tipmov:
            if tipmov.is_acconto == 1:
                return True
        return False
    
    def HasMovStornoAcconto(self):
        for tipmov in self.tipmov:
            if tipmov.is_accstor == 1:
                return True
        return False
