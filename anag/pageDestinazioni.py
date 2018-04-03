#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag.pageDestinazioni
# Author:       Marcello
# Data:          22/mag/2015 - 09:26:53
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

import Env
import anag.pdcrelAddPage_wdr as wdr
bt = Env.Azienda.BaseTab

from awc.layout.anagnewpage import GenericPersonalLinkedPage_Panel
from awc.layout.anagnewpage import GenericPersonalLinkedPage_InternalGrid
import wx.grid as gl


#===============================================================================
# Sostituire a:
# <NomeTabella> il nome della tabella da gestire (Iniziale maiuscola)
# <NOMETABELLA> il nome della tabella da gestire (TUTTO MAIUSCOLO)
#===============================================================================



class DestinPanel(GenericPersonalLinkedPage_Panel):
    def __init__(self, *args, **kwargs):

        self.gridTableName=bt.TABNAME_DESTIN
        GenericPersonalLinkedPage_Panel.__init__(self, *args, **kwargs)
        wdr.DestinFunc(self)
        panelGrid=self.GetPanelGrid()
        self._grid=DestinGrid(panelGrid, -1, size=panelGrid.GetClientSizeTuple(), mainPanel=self.mainPanel, gridTableName=self.gridTableName, idGrid='pagedestinatari')
        self.BindControl()

class DestinGrid(GenericPersonalLinkedPage_InternalGrid):


    def __init__(self, *args, **kwargs):
        GenericPersonalLinkedPage_InternalGrid.__init__(self, *args, **kwargs)


    def SetColumn2Fit(self):
        self.SetFitColumn(1)

    def SetOrder(self):
        return ['descriz', 'codice']

    def SetExclusiveCheckField(self):
        return ['pref']

    def SetCanEditCheck(self):
        return ['pref']

    def SetColumnGrid(self):
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _NUM = gl.GRID_VALUE_NUMBER

        #=======================================================================
        # Definire le colonne che debbono essere visualizzate nel seguente formarto:
        # - larghezza colonna in pixel
        # - posizione del campo a cui la colonna si riferisce all' interno della tabella gestita
        #   per agevolare l'indicazione puo' essere utilizzata il metodo GetIndexField a cui
        #   passando il nome del campo restituisce la sua posizione
        # - titolo della colonna
        # - tipo del campo
        # - se editabile o meno (non è comunque gestito e la colonna risulterà comunque non editabile)
        #
        # Di seguito un esempio di definizione che dovrà essere modificato secondo le esigenze
        #=======================================================================
        cols = (( 50, (self.GetIndexField('codice'),  "Codice",       _STR, True )),
                (120, (self.GetIndexField('descriz'), "Intestazione", _STR, True )),
                ( 30, (self.GetIndexField('pref'),    "Pref",         _CHK, True )),
                (  1, (self.GetIndexField('id'),      "#id",          _STR, False)),
            )
        self.cols = cols
        self.colmap  = [c[1] for c in cols]
        self.colsize = [c[0] for c in cols]
        #===============================================================================
        #     Per ogni campo gestito è possibile indicare i seguenti metodi che verranno
        #      automaticamente richiamati:
        #     - DefaultValue_<nomeCampo> imposta il valore di default del campo
        #     -        esegue un contrrollo di validità del valore
        #                                assegnato al campo restituendo vero o falso in
        #                                base all'esito del controllo
        #     - Warning_<nomeCampo>      restituisce la stringa da visualizzare qualora
        #                                il campo a cui si riferisce non superi il
        #                                controllo di Check_<nomeCampo>
        #
        #     A titolo di esempio si potrebbe avere:
        #
        #     def DefaultValue_citta(self):
        #         return 'VENTIMIGLIA'
        #
        #     def Check_descriz(self, record):
        #         value=record[self.GetIndexField('descriz')]
        #         return value is not None and len(value.strip())>0
        #
        #     def Warning_descriz(self, record):
        #         return 'Nome assente'
        #
        #------------------------------------------------------------------------------
        #     In alternativa il metodo Check_<nomeCampo> potrebbe essere definito come
        #     segue evitando di dover indicare il nome dello specifico campo all'interno
        #     della definizione del metodo. L'esecuzione in questa forma risulta comunque
        #     più lenta
        #
        #     def Check_descriz(self, data):
        #         value=self.GetActualFieldValue(data)
        #         return value is not None and len(value.strip())>0
        #===============================================================================

    #===========================================================================
    # def DefaultValue_codice(self):
    #     try:
    #         c = self.db_curs
    #         c.execute("SELECT MAX(0+CODICE) FROM %s des WHERE des.id_pdc=%s"\
    #                   % (bt.TABNAME_DESTIN, self.mainPanel.db_recid))
    #         rs = c.fetchone()
    #         lastab = rs[0] or 0
    #         lasmem = max([int(x[self.GetIndexField('codice')] or '') for x in self.rsdata])
    #         newc = str(int(max(lastab, lasmem)+1))
    #     except:
    #         newc = '1'
    #     return newc
    #===========================================================================

    def Check_codice(self, record):
        value=record[self.GetIndexField('codice')]
        return value is not None and len(value.strip())>0
    def Warning_codice(self, record):
        return 'Codice assente'


    def DefaultValue_descriz(self):
        return self.mainPanel.FindWindowByName('descriz').GetValue()
    def Check_descriz(self, record):
        value=record[self.GetIndexField('descriz')]
        return value is not None and len(value.strip())>0
    def Warning_descriz(self, record):
        return 'Intestaz.assente'

    def DefaultValue_cap(self):
        return ''
    def Check_cap(self, record):
        value=record[self.GetIndexField('cap')]
        return value is not None and len(value.strip())>0
    def Warning_cap(self, record):
        return 'CAP assente'

    def DefaultValue_citta(self):
        return ''
    def Check_citta(self, record):
        value=record[self.GetIndexField('citta')]
        return value is not None and len(value.strip())>0
    def Warning_citta(self, record):
        return "Localita' assente"

    def DefaultValue_prov(self):
        return ''
    def Check_prov(self, record):
        value=record[self.GetIndexField('prov')]
        return value is not None and len(value.strip())>0
    def Warning_prov(self, record):
        return "Prov.assente"

    def DefaultValue_indirizzo(self):
        return ''
    def Check_indirizzo(self, record):
        value=record[self.GetIndexField('indirizzo')]
        return value is not None and len(value.strip())>0
    def Warning_indirizzo(self, record):
        return "Indirizzo.assente"

    def OnChanged(self, evt):
        #=======================================================================
        # Non viene mai utilizzata perchè di fatto la grid non è editabile nonostante
        # nella definizione dovrebbe esserlo
        #=======================================================================
        row = self.GetSelectedRows()[0]
        if 0<=row<len(self.rsdata):
            desid = self.rsdata[row][self.GetIndexField('id')]
            if desid is not None and not desid in self.rsdatamod:
                self.rsdatamod.append(desid)
        self.mainPanel.SetDataChanged()


