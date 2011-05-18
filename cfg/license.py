#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/license.py
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
import wx.grid as gl
import awc.controls.dbgrid as dbglib

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

import awc.controls.windows as aw
import awc.controls.radiobox as awradio

import cfg.license_wdr as wdr
import X_wdr
from cfg.wksetup import ConfigPanel, ConfigDialog

import stormdb as adb

import os
import ConfigParser

import md5

import version
import licenses


class _LicenseMixin(object):
    ragsoc = ''
    piva = ''
    prefix = ''
    errmsg = "Prefisso non conforme"
    
    def __init__(self, rs, piva):
        object.__init__(self)
        self.SetParam(rs, piva)
    
    def SetParam(self, rs, piva):
        self.ragsoc = rs
        self.piva = piva
    
    def Complete(self, s, *args, **kwargs):
        return s+self._Chypher(s, *args, **kwargs)
    
    def _Chypher(self, s, v=''):
        m = md5.new()
        m.update(s) #codice da hasciare
        m.update(v) #eventuale stringa da aggiungere x l'hasc (tipicamente una ragione sociale)
        h = m.hexdigest().upper()
        o = ''
        for n in range(0,len(h),3):
            o += str(ord(h[n]))[-1]
        return o
    
    def _PivaCypher(self):
        if not self.piva:
            raise Exception, "Definire la partita iva"
        h = ''
        for n in (0,1):
            for p in range(n,12,2):
                try:
                    h += self.piva[p]
                except IndexError:
                    pass
        return h
    
    def Calcola(self, prefix):
        prefix = '%s-%s-' % (prefix, self._PivaCypher())
        self.TestFormato(prefix)
        self.prefix = prefix
        return self.Complete(prefix, self.ragsoc)
    
    def IsOk(self, lic):
        ok = False
        try:
            ok = (lic == self.Calcola(lic[:8]))
        except:
            ok = version.OSS()
        if ok:
            try:
                if version.OSS():
                    owner = licenses.getOssOwner()
                    text = licenses.getOssLicense()
                else:
                    owner = licenses.getLicenseOwner()
                    lictipo = lic[5]
                    if lictipo == "C":
                        text = licenses.getTextContent('license_cl')
                    else:
                        text = "CODICE NON RICONOSCIUTO"
            except Exception, e:
                owner = ''
                text = repr(e.args)
            Env.LICENSE_OWNER = owner
            Env.LICENSE_TEXT = text
        return ok
    
    def TestFormato(self, prefix, specvalid):
        if not self.ragsoc:
            raise Exception, "Definire la ragione sociale"
        if not self.piva:
            raise Exception, "Definire la partita iva"
        if ''.join([prefix[p] for p in (4,8,20)]) != '---' or not specvalid:
            raise Exception, self.errmsg


# ------------------------------------------------------------------------------


class License(_LicenseMixin):
    """
    GGGG-XCC-LLLLLLLLLLLL-YYYYYYYY
    """
    def TestFormato(self, prefix):
        def z(x, l):
            return str(x).zfill(l)
        try:
            _LicenseMixin.TestFormato(self, prefix,
                                      prefix[:4] == z(int(prefix[:4]), 4) and\
                                      prefix[5] in 'CO' and\
                                      prefix[6:8] == z(int(prefix[6:8]), 2))
        except:
            raise Exception, self.errmsg
    
    def GetLicenseType(self):
        return self.prefix[5]
        

# ------------------------------------------------------------------------------


class ActivationCode(_LicenseMixin):
    """
    X4TT-VVV-LLLLLLLLLLLL-YYYYYYYY
    """
    def TestFormato(self, prefix):
        _LicenseMixin.TestFormato(self, prefix,
                                  prefix[5:8] == str(prefix[5:8]).zfill(3))
    

# ------------------------------------------------------------------------------


class LicensePanel(ConfigPanel):
    """
    Impostazione licenza.
    """
    license = None
    
    def __init__(self, *args, **kwargs):
        ConfigPanel.__init__(self, *args, **kwargs)
        wdr.LicenseSetup(self)
        cn = self.FindWindowByName
        if version.OSS():
            di = "Intestatario della registrazione:"
            dl = "Codice registrazione:"
        else:
            di = "Intestatario della licenza d'uso:"
            dl = "Codice licenza:"
        cn('desint').SetLabel(di)
        cn('deslic').SetLabel(dl)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def Validate(self):
        out = True
        rs, piv, lic = map(lambda x: self.FindWindowByName(x).GetValue(),
                           ('License_head', 'License_piva', 'License_pswd'))
        if version.OSS():
            dl = "registrazione"
        else:
            dl = "licenza d'uso"
        msg = None
        if not rs:
            msg = "Indicare la ragione sociale dell'intestatario della %s" % dl
        elif not piv:
            msg = "Indicare partita iva dell'intestatario della %s" % dl
        elif not lic:
            msg = "Indicare il codice della %s" % dl
        else:
            if not License(rs, piv).IsOk(lic):
                msg = "Codice di %s errato" % dl
        if msg:
            aw.awu.MsgDialog(self, message=msg, style=wx.ICON_ERROR)
            out = False
        return out


# ------------------------------------------------------------------------------


class LicenseDialog(ConfigDialog):
    """
    Dialog impostazione licenza
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Licenza d'uso"
        ConfigDialog.__init__(self, *args, **kwargs)
        self.panel = LicensePanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def OnSave(self, event):
        aw.awu.MsgDialog(self, "Le informazioni sulla licenza sono state aggiornate",
                         style=wx.ICON_INFORMATION)
        ConfigDialog.OnSave(self, event)


# ------------------------------------------------------------------------------


class LicenseInfoPanel(wx.Panel):
    """
    Informazioni licenza.
    """
    license = None
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.LicenseInfoFunc(self)
        cn = self.FindWindowByName
        cfg = Env.Azienda.license
        if version.OSS():
            di = "Intestatario della registrazione:"
            dl = "Codice registrazione:"
        else:
            di = "Intestatario della licenza d'uso:"
            dl = "Codice licenza:"
        cn('desint').SetLabel(di)
        cn('deslic').SetLabel(dl)
        try:
            rs = cfg.get('License', 'head')
            pi = cfg.get('License', 'pswd')
        except:
            rs = pi = ''
        if not rs and version.OSS():
            rs = '*** prodotto non registrato ***'
        cn('License_head').SetLabel(rs)
        cn('License_pswd').SetLabel(pi)
        lictxt = cn('lic_text')
        l = Env.LICENSE_OWNER
        if l:
            l += '\n'
        l += Env.LICENSE_TEXT
        lictxt.SetValue(l)
        lictxt.SetEditable(False)
        self.Fit()
        self.Layout()


# ------------------------------------------------------------------------------


class LicenseInfoDialog(aw.Dialog):
    """
    Dialog informazioni licenza
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Informazioni sulla licenza"
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(LicenseInfoPanel(self))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.FindWindowById(wdr.ID_OK))
    
    def OnClose(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class ActivationCodesGrid(dbglib.DbGrid):
    
    def __init__(self, parent, codes):
        
        dbglib.DbGrid.__init__(self, parent, -1, 
                               size=parent.GetClientSizeTuple())
        self.codes = codes
        
        cols = (\
            ( 40, (0, "Mod.",   gl.GRID_VALUE_STRING, True)),
            (300, (1, "Codice", gl.GRID_VALUE_STRING, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = True
        
        linktables = None
        afteredit = ((dbglib.CELLEDIT_BEFORE_UPDATE, 1, self.TestCode),
                     (dbglib.CELLEDIT_AFTER_UPDATE, 1, self.CodeEntered),
                 )
        
        self.SetData(self.codes, colmap, canedit, canins, 
                     linktables, afteredit, self.AddNewRow)
        
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def TestCode(self, row, gridcol, col, value):
        out = False
        if not value:
            return False
        out = ActivationCode(Env.Azienda.descrizione, 
                             Env.Azienda.license.License_piva).IsOk(value)
        if not out:
            aw.awu.MsgDialog(self, "Codice di attivazione errato")
        return out
    
    def CodeEntered(self, row, gridcol, col, value):
        self.codes[row][0] = value[:4]
        self.ForceRefresh()
        return True
    
    def AddNewRow(self):
        self.codes.append(['', ''])
        return True
    
    def GetAttr(self, row, col, rscol, attr):
        attr.SetReadOnly(col == 0)
        attr.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.BOLD))
        return attr


# ------------------------------------------------------------------------------


class ActivationCodesPanel(ConfigPanel):
    """
    Impostazione codici di attivazione.
    """
    codes = None
    
    def __init__(self, *args, **kwargs):
        self.codes = []
        ConfigPanel.__init__(self, *args, **kwargs)
        wdr.ActivationCodesFunc(self)
        p = self.FindWindowById(wdr.ID_PANGRIDCODES)
        self.grid = ActivationCodesGrid(p, self.codes)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def GetValue(self, sec, opt):
        if sec == 'License':
            out = ConfigPanel.GetValue(self, sec, opt)
        else:
            out = [x[1] for x in self.codes if x[0] == sec][0]
        return out
    
    def Read(self):
        ConfigPanel.Read(self)
        del self.codes[:]
        cfg = self.config
        for sec in cfg.sections():
            if sec != 'License':
                code = cfg.get(sec, 'pswd')
                self.codes.append([code[:4], code])
        self.grid.ResetView()
        self.grid.SetGridCursor(len(self.codes)-1,1)
    
    def Save(self):
        cfg = self.config
        lic = cfg._sections['License']
        cfg._sections.clear()
        cfg._sections['License'] = lic
        for key, code in self.codes:
            cfg.add_section(key)
            cfg.set(key, 'pswd', code)
        ConfigPanel.Save(self)


# ------------------------------------------------------------------------------


class ActivationCodesDialog(ConfigDialog):
    """
    Dialog impostazione codici di attivazione
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Codici di attivazione"
        ConfigDialog.__init__(self, *args, **kwargs)
        self.panel = ActivationCodesPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def OnSave(self, event):
        aw.awu.MsgDialog(self, "Le informazioni sulla licenza sono state aggiornate",
                         style=wx.ICON_INFORMATION)
        ConfigDialog.OnSave(self, event)
