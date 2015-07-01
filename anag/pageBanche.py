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

import wx
import awc.controls.windows as aw

from awc.layout.anagnewpage import GenericPersonalLinkedPage_Panel
from awc.layout.anagnewpage import GenericPersonalLinkedPage_InternalGrid
import wx.grid as gl




#===============================================================================
# Sostituire a:
# <NomeTabella> il nome della tabella da gestire (Iniziale maiuscola)
# <NOMETABELLA> il nome della tabella da gestire (TUTTO MAIUSCOLO)
#===============================================================================


class DatiBancariMixin(object):

    def OnCalcolaBBAN(self, event):
        self.CalcolaXBAN1('bban')
        event.Skip()

    def OnCalcolaIBAN(self, event):
        self.CalcolaXBAN1('iban')
        event.Skip()

    def CalcolaXBAN1(self, tipo):

        if not tipo in 'bban iban'.split():
            raise Exception, 'Tipo di calcolo errato: %s' % tipo

        cols = []
        keys = []

        lcc = 12
        if tipo == 'iban':
            keys.append(['paese',   'Paese',    2])
            keys.append(['ciniban', 'CIN IBAN', 2])
            lcc = 12

        keys.append(['cinbban', 'CIN BBAN', 1])
        keys.append(['abi',     'ABI',      5])
        keys.append(['cab',     'CAB',      5])
        keys.append(['numcc',   'C/C',    lcc])

        cols = [key for key, des, lun in keys]

        def cn(col):
            return self.FindWindowByName('bancf_%s'%col)

        if cn(tipo).GetValue():
            if aw.awu.MsgDialog(self, "Il codice %s è già compilato, vuoi ricalcolarlo ?" % str(tipo).upper(), style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return

        xban = ''
        for key, des, lun in keys:
            val = cn(key).GetValue() or ''
            if not val:
                aw.awu.MsgDialog(self, "Manca %s" % des)
                def setfocus():
                    cn(key).SetFocus()
                wx.CallAfter(setfocus)
                return
            if key == 'numcc':
                if tipo == 'bban' or xban.startswith('IT'):
                    v = ''
                    for x in str(val):
                        if str.isdigit(x):
                            v += x
                    val = str(v).zfill(lun)
                else:
                    val = str(val).strip()
            else:
                if len(val) != lun:
                    aw.awu.MsgDialog(self, "Valore errato per %s" % des)
                    return
            xban += val

        cn(tipo).SetValue(xban)




class BanchePanel(GenericPersonalLinkedPage_Panel, DatiBancariMixin):

    _OnCalcolaBBAN = DatiBancariMixin.OnCalcolaBBAN
    _OnCalcolaIBAN = DatiBancariMixin.OnCalcolaIBAN

    def __init__(self, *args, **kwargs):

        self.gridTableName=bt.TABNAME_BANCF
        GenericPersonalLinkedPage_Panel.__init__(self, *args, **kwargs)
        self.SetLayoutFromWdr()
        panelGrid=self.GetPanelGrid()
        self._grid=self.GetPanelGridClass()(panelGrid, -1, size=panelGrid.GetClientSizeTuple(), mainPanel=self.mainPanel, gridTableName=self.gridTableName)
        self.BindControl()

    def BindAddButton(self):
        cn=self.FindWindowByName
        cn('ban_butcalc_bban').Bind(wx.EVT_BUTTON, self._OnCalcolaBBAN)
        cn('ban_butcalc_iban').Bind(wx.EVT_BUTTON, self._OnCalcolaIBAN)

    def SetLayoutFromWdr(self):
        wdr.BancheFunc(self)

    def GetPanelGridClass(self):
        return BancheGrid


class BancheGrid(GenericPersonalLinkedPage_InternalGrid):

    def __init__(self, *args, **kwargs):
        GenericPersonalLinkedPage_InternalGrid.__init__(self, *args, **kwargs)


    def SetColumn2Fit(self):
        self.SetFitColumn(1)

    def SetOrder(self):
        return ['descriz', 'codice']

    def SetExclusiveCheckField(self):
        return ['pref']

    def SetUniqueField(self):
        #TODO: Introdurre la possibilità di specificare il(i campi che debbono necessariamente assumenre un valore univoco
        return []


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


    def Check_codice(self, record):
        value=record[self.GetIndexField('codice')]
        return value is not None and len(value.strip())>0
    def Warning_codice(self, record):
        return 'Codice assente'


    def DefaultValue_descriz(self):
        return ''
    def Check_descriz(self, record):
        value=record[self.GetIndexField('descriz')]
        return value is not None and len(value.strip())>0
    def Warning_descriz(self, record):
        return 'Intestaz.assente'

    def DefaultValue_abi(self):
        return ''
    def Check_abi(self, record):
        value=record[self.GetIndexField('abi')]
        return value is not None and len(value.strip())>0
    def Warning_abi(self, record):
        return 'ABI assente'

    def DefaultValue_cab(self):
        return ''
    def Check_cab(self, record):
        value=record[self.GetIndexField('cab')]
        return value is not None and len(value.strip())>0
    def Warning_cab(self, record):
        return 'CAB assente'

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


