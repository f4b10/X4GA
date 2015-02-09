#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/automat.py
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

import cfg.automat_wdr as wdr

import awc.controls.windows as aw
import awc.controls.linktable as lt

import awc.util as awu

import Env
bt = Env.Azienda.BaseTab

cn = lambda self, name: self.FindWindowByName(name)


FRAME_TITLECON = "Automatismi contabili"


class _automatmixin(object):
    """
    Gestione automatismi.
    self.auto = dizionario automatismi:
        la chiave è il codice dell'automatismo
        il valore è una lista contenente:
            - puntatore del controllo
            - descrizione dell'automatismo
    """
    
    def __init__(self):
        """
        Costruttore.
        """
        object.__init__(self)
        self.table = bt.TABNAME_CFGAUTOM
        self.db_conn = Env.Azienda.DB.connection
        self.db_curs = self.db_conn.cursor()
        self.auto = {}

    def LoadValues(self):
        """
        Aggiorna i controlli in base al contenuto della tabella.
        """
        try:
            for key, (ctr, des) in self.auto.iteritems():
                ctr.SetValue(self.LoadAutomat(key))
        except MySQLdb.Error, e:
            awu.MsgDialogDbError(self, e)
    
    def LoadAutomat(self, codice):
        """
        Carica gli automatismi dalla tabella.
        """
        out = None
        cmd =\
"""SELECT aut_id """\
"""FROM %s """\
"""WHERE codice=%%s""" % self.table
        self.db_curs.execute(cmd, codice)
        rs = self.db_curs.fetchone()
        if rs:
            out = rs[0]
        return out

    def SaveAutomat(self):
        """
        Scrive gli automatismi sulla tabella.
        """
        dberr = None
        for key, (ctr, des) in self.auto.iteritems():
            id = ctr.GetValue()
            cmd = """INSERT INTO %s (codice, descriz, aut_id) """\
                  """VALUES (%%s, %%s, %%s);""" % self.table
            try:
                self.db_curs.execute(cmd, (key,des, id) )
            except MySQLdb.Error, e:
                if e.args[0] == 1062:
                    cmd = """UPDATE %s SET descriz=%%s, aut_id=%%s """\
                          """WHERE codice=%%s;""" % self.table
                    try:
                        self.db_curs.execute(cmd, (des,id,key) )
                    except MySQLdb.Error, e:
                        dberr = e.args
                else:
                    dberr = e.args
            if dberr:
                awu.MsgDialog(self, repr(dberr))
                break
        return (dberr is None)
    
    def UpdateDataRecord(self):
        out = False
        ctrls = [cn(self, key) for key in self.auto.keys()]
        if self.ValidateControls(ctrls):
            if self.ValidateData():
                out = self.SaveAutomat()
        return out


# ------------------------------------------------------------------------------


class AutomatContabPanel(aw.Panel, _automatmixin):
    """
    Impostazione degli automatismi contabili.
    """
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        _automatmixin.__init__(self)
        
        wdr.AutomatContabFunc(self, True)
        
        for c in aw.awu.GetAllChildrens(self):
            if hasattr(c, 'SetLabel'):
                if c.GetLabel() == 'Iva in sospensione:':
                    c.SetLabel('Iva in split playment:')
        
        for aut, des in (("pdctip", "Tipo sottoconto"),
                         ("bilmas", "Mastro di bilancio"),
                         ("bilcon", "Conto di bilancio"),
                         ("bilcee", "Classificazione CEE"),):
            for tipo in 'casse banche clienti fornit effetti'.split():
                key = "%s_%s" % (aut, tipo)
                self.auto[key] =\
                    [None, "%s default per tabella %s" % (des, tipo)]
        
        for tipo in 'costi ricavi'.split():
            key = "pdctip_%s" % tipo
            self.auto[key] =\
                [None, "Tipo sottoconto default per %s" % tipo]
        
        for aut, des in (\
            ('abbatt',    'Sottoconto abbuoni attivi'),\
            ('abbpas',    'Sottoconto abbuoni passivi'),\
            ('speinc',    'Sottoconto spese incasso'),\
            ('uticam',    'Sottoconto utile su differenza cambio'),\
            ('percam',    'Sottoconto perdita su differenza cambio'),\
            ('regchicau', 'Causale bilancio chiusura'),\
            ('regchibil', 'Sottoconto bilancio chiusura'),\
            ('regchiupe', 'Sottoconto utile/perdita esercizio chiusura'),\
            ('regchiprp', 'Sottoconto profitti/poerdite chiusura'),\
            ('regapecau', 'Causale bilancio apertura'),\
            ('regapebil', 'Sottoconto bilancio apertura'),\
            ('regapeupe', 'Sottoconto profitti/perdite apertura'),\
            ('ivaacq',    'Sottoconto IVA su acquisti'),\
            ('ivaind',    'Sottoconto IVA indeducibile su acquisti'),\
            ('ivaacqcee', 'Sottoconto IVA su acquisti cee'),\
            ('ivaven',    'Sottoconto IVA su vendite'),\
            ('ivacor',    'Sottoconto IVA su vendite da corrispettivi'),\
            ('ivapro',    'Sottoconto IVA per vendite con fattura proforma'),\
            ('ivaacqsos', 'Sottoconto IVA per acquisti in sospensione di IVA'),\
            ('ivavensos', 'Sottoconto IVA per vendite in sospensione di IVA'),):
            self.auto[aut] = [None, des]
        
        for key in self.auto:
            ctr = cn(self, key)
            self.auto[key][0] = ctr
            if ctr.GetName().startswith('bilmas'):
                self.Bind(lt.EVT_LINKTABCHANGED, self.OnMastroChanged, ctr)
        
        self.LoadValues()
        
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BTNOK)
    
    def OnMastroChanged( self, event ):
        ctrmas = event.GetEventObject()
        ctrcon = None
        for tipo in ('casse', 'banche', 'clienti', 'fornit', 'effetti'):
            if ctrmas.GetName() == 'bilmas_%s' % tipo:
                ctrcon = cn(self, 'bilcon_%s' % tipo)
        if ctrcon is not None:
            mas = ctrmas.GetValue()
            if mas is None:
                ctrcon.ResetValue()
                ctrcon.Disable()
            else:
                ctrcon.SetFilter( "id_bilmas=%d" % ctrmas.GetValue() )
                ctrcon.Enable()

    def OnConfirm( self, event ):
        if self.UpdateDataRecord():
            event.Skip()
    
    def ValidateData(self):
        return True


# ------------------------------------------------------------------------------


class AutomatContabFrame(aw.Frame):
    """
    Frame Gestione tabella Automatismi contabili.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECON
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AutomatContabPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BTNOK)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BTNQUIT)

    def OnClose(self, event):
        self.Close()


# ------------------------------------------------------------------------------


class AutomatContabDialog(aw.Dialog):
    """
    Dialog Gestione tabella Automatismi contabili.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECON
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AutomatContabPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BTNOK)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=wdr.ID_BTNQUIT)

    def OnConfirm(self, event):
        if self.IsModal():
            self.EndModal(1)
        else:
            self.Close()

    def OnQuit(self, event):
        if self.IsModal():
            self.EndModal(0)
        else:
            self.Close()



# ------------------------------------------------------------------------------


FRAME_TITLEMAG = "Automatismi di magazzino"


class AutomatMagazzPanel(aw.Panel, _automatmixin):
    """
    Impostazione degli Automatismi di magazzino.
    """
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        _automatmixin.__init__(self)
        
        wdr.AutomatMagazzFunc(self, True)
        
        for aut, des in (('magomaggi', 'Sottoconto Omaggi'),\
                         ('magomareg', 'Omaggi in registrazione'),\
                         ('magivascm', 'Aliquota Iva per sconto merce'),\
                         ('magivacee', 'Aliquota Iva per documenti CEE'),\
                         ('magivaest', 'Aliquota Iva per documenti estero'),\
                         ('magivadef', 'Aliquota Iva di default'),\
                         ('magordinv', 'Ordine inverso su interrogazioni sottoconto'),\
                         ('magordfta', 'Ordinamento in interr.prodotti fatturati'),\
                         ('magintcli', 'Visualizzazione di default su scheda cliente'),\
                         ('maginidoc', 'Documento giacenza iniziale'),\
                         ('maginimov', 'Movimento giacenza iniziale'),\
                         ('magfiltip', 'Filtro ricerca articoli per tipo'),
                         ('magfilcat', 'Filtro ricerca articoli per categoria'),
                         ('magfilfor', 'Filtro ricerca articoli per fornitore'),
                         ('magfilmar', 'Filtro ricerca articoli per marca'),
                         ):
            self.auto[aut] = [None, des]
        
        for key in self.auto:
            self.auto[key][0] = cn(self, key)
        
        tf = {True: 1, False: 0}
        
        cn(self, 'magordinv').SetDataLink('magordinv', tf)
        for name, values in (('magordfta', (0,1)),
                             ('magintcli', (0,1,2))):
            cn(self, name).SetDataLink(name, values)
        
        for name in 'tip,cat,for,mar'.split(','):
            name = 'magfil%s' % name
            cn(self, name).SetDataLink(name, tf)
        cn(self, 'magomareg').SetDataLink(name, tf)
        
        self.LoadValues()
        self.Bind(lt.EVT_LINKTABCHANGED, self.OnTipDocChanged, cn(self, 'maginidoc'))
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BTNOK)
    
    def OnTipDocChanged(self, event):
        v = event.GetEventObject().GetValue()
        if v is None:
            flt = "FALSE"
        else:
            flt = "id_tipdoc=%d" % v
        self.FindWindowByName('maginimov').SetFilter(flt)
        event.Skip()
    
    def OnConfirm( self, event ):
        if self.UpdateDataRecord():
            event.Skip()
    
    def ValidateData(self):
        return True


# ------------------------------------------------------------------------------


class AutomatMagazzFrame(aw.Frame):
    """
    Frame Gestione tabella Automatismi di magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEMAG
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AutomatMagazzPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BTNOK)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_BTNQUIT)

    def OnClose(self, event):
        self.Close()


# ------------------------------------------------------------------------------


class AutomatMagazzDialog(aw.Dialog):
    """
    Dialog Gestione tabella Automatismi di magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEMAG
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(AutomatMagazzPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BTNOK)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=wdr.ID_BTNQUIT)

    def OnConfirm(self, event):
        if self.IsModal():
            self.EndModal(1)
        else:
            self.Close()

    def OnQuit(self, event):
        if self.IsModal():
            self.EndModal(0)
        else:
            self.Close()


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    Env.Azienda.Colours.SetDefaults()
    win = AutomatContabDialog()
    win.Show()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    import stormdb as adb
    db = adb.DB()
    db.Connect()
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
