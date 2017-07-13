#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/__init__.py
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


#costanti per l'uscita dal dialog se modale
DOC_UNMODIFIED = 0
DOC_MODIFIED =   1
DOC_DELETED =    2


#costanti per lo status del frame
STATUS_SELCAUS = 0
STATUS_DISPLAY = 1
STATUS_GETKEY  = 2
STATUS_EDITING = 3

#costanti per il tipo di editing attivo
EDITING_HEAD = 0
EDITING_BODY = 1
EDITING_FOOT = 2
EDITING_FOOT = 3

#costanti per il tipo di piede da visualizzare
FOOT_TOT = 0
FOOT_ACC = 1


#costanti per recordset righe dettaglio (corpo) e campi della tabella movimenti
movfields = []
a = movfields.append
RSMOV_ID      =   0; a('id')
RSMOV_ID_DOC  =   1; a('id_doc')
RSMOV_ID_TMOV =   2; a('id_tipmov')
RSMOV_NUMRIGA =   3; a('numriga')
RSMOV_ID_PROD =   4; a('id_prod')
RSMOV_DESCRIZ =   5; a('descriz')
RSMOV_UM      =   6; a('um')
RSMOV_NMCONF  =   7; a('nmconf')
RSMOV_PZCONF  =   8; a('pzconf')
RSMOV_QTA     =   9; a('qta')
RSMOV_PREZZO  =  10; a('prezzo')
RSMOV_AGGGRIP =  11; a('agggrip')
RSMOV_SC1     =  12; a('sconto1')
RSMOV_SC2     =  13; a('sconto2')
RSMOV_SC3     =  14; a('sconto3')
RSMOV_SC4     =  15; a('sconto4')
RSMOV_SC5     =  16; a('sconto5')
RSMOV_SC6     =  17; a('sconto6')
RSMOV_IMPORTO =  18; a('importo')
RSMOV_ID_IVA  =  19; a('id_aliqiva')
RSMOV_NOTE    =  20; a('note')
RSMOV_ACQMOV  =  21; a('id_moveva')
RSMOV_ACCMOV  =  22; a('id_movacc')
RSMOV_PERPRO  =  23; a('perpro')
RSMOV_F_ANN   =  24; a('f_ann')
RSMOV_PDCCG_ID = 25; a('id_pdccg')
RSMOV_COSTOU =   26; a('costou')
RSMOV_COSTOT =   27; a('costot')
RSMOV_TIPLIST =  28; a('id_tiplist')
RSMOV_ID_DDTACQ= 29; a('id_ddtacq')
RSMOV_lastcol =\
RSMOV_ID_DOCSOURCE= 30; a('id_docsource')




# i seguenti valori sono determinati in fase di caricamento tabelle
RSMOV_codmov  = -1
RSMOV_codart  = -1
RSMOV_codiva  = -1
RSMOV_codlis  = -1
RSMOV_desmov  = -1
RSMOV_desart  = -1
RSMOV_desiva  = -1
RSMOV_deslis  = -1
RSMOV_PDCCG_cod = -1
RSMOV_PDCCG_des = -1


#costanti per recordset scadenze
RSSCA_ID      = 0
RSSCA_IDREG   = 1
RSSCA_DATSCAD = 2
RSSCA_IMPORTO = 3
RSSCA_ID_PCF  = 4
RSSCA_NOTE    = 5


#costanti per recordset totali iva
RSIVA_ID      =  0
RSIVA_codiva  =  1
RSIVA_desiva  =  2
RSIVA_IMPONIB =  3
RSIVA_IMPOSTA =  4
RSIVA_IMPORTO =  5
RSIVA_IMPOSCR =  6
RSIVA_ISOMAGG =  7
RSIVA_perciva =  8
RSIVA_percind =  9
RSIVA_tipoalq = 10


#costanti per recordset totali per sottoconto di costo/ricavo
RSPDC_ID      =  0
RSPDC_codpdc  =  1
RSPDC_despdc  =  2
RSPDC_IMPONIB =  3
RSPDC_IMPORTO =  4 #usato solo in caso di scorporo documento e presenza righe "I"
RSPDC_ISSPESA =  5
RSPDC_ISOMAGG =  6
RSPDC_TIPRIGA =  7 #usato per determinare, su doc. con scorporo, il subtotalizzatore (merce, servizi ecc) su cui adeguare l'importo in funzione dell'eventuale squadratura

#seguono costanti per dati iva, solo x contab.semplif.
RSPDC_ALIQ_ID =  8
RSPDC_aliqcod =  9
RSPDC_aliqdes = 10
RSPDC_IMPOSTA = 11
RSPDC_INDEDUC = 12
RSPDC_IMPOSCR = 13
RSPDC_DESTOT =  14



#campi della tabella documenti
bt = Env.Azienda.BaseTab
stru = bt.tabelle[bt.TABSETUP_TABLE_MOVMAG_H][2]
docfields = [ s[0] for s in stru ]

def GetDefaultMagazz():
    dbm = Env.adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGSETUP, 'cfg',
                          writable=False)
    if dbm.Retrieve('cfg.chiave=%s', 'magazz_default:site %s'
                    % Env.Azienda.config.Site_name) and dbm.RowsCount() == 1:
        out = dbm.importo
    else:
        out = None
    return out


# ------------------------------------------------------------------------------


def GetDataentryFrameClass():
    from magazz.dataentry_o import MagazzFrame_O as DocMagazzFrame
    return DocMagazzFrame


# ------------------------------------------------------------------------------


def GetDataentryDialogClass():
    from magazz.dataentry_o import MagazzDialog_O as DocMagazzDialog
    return DocMagazzDialog


# ------------------------------------------------------------------------------


def CheckPermUte(doc, perm, msg=True):
    assert perm in 'leggi scrivi'.split()
    from cfg.dbtables import PermessiUtenti
    p = PermessiUtenti()
    out = p._CheckRW('caumagazz', doc, perm)
    if not out and msg:
        from awc.util import MsgDialog
        if perm == 'leggi':
            msg = "vedere"
        else:
            msg = 'modificare'
        MsgDialog(None, "Non hai i diritti per %s questo documento" % msg)
    return out
