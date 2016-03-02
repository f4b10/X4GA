#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/listctrl.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
# Copyright:    (C) 2016 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
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
import awc.controls.mixin as cmix
import os, tempfile, codecs, csv

CSVFORMAT_ASGRID = 0
CSVFORMAT_DELIMITER = ';'
CSVFORMAT_QUOTECHAR = '"'
CSVFORMAT_QUOTING = csv.QUOTE_MINIMAL
CSVFORMAT_EXCELZERO = False

class ListCtrl(wx.ListCtrl, cmix.ControlsMixin):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        cmix.ControlsMixin.__init__(self)
        self.Bind(wx.EVT_SET_FOCUS,  self.OnFocusGained)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)

    def OnFocusGained(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()

    def OnFocusLost(self, event):
        self.AdjustBackgroundColor(False)
        event.Skip()

    def IsEditable(self):
        return True

    def ExportCsv(self):
        csvrs = []
        lTitoli=[]
        row=[]
        nColumn=self.GetColumnCount()
        for i in range(0, nColumn):
            lTitoli.append(self.GetColumn(i).GetText())

        for i in range(0, self.GetItemCount()):
            row=[]
            for j in range(0, nColumn):
                row.append(self.GetItem(i, j).GetText())
            csvrs.append(row)


        if len(csvrs)>0:
            tmpfile = tempfile.NamedTemporaryFile(suffix='.csv')
            tmpname = tmpfile.name
            tmpfile.close()
            tmpfile = open(tmpname, 'wb')
            tmpfile.write(codecs.BOM_UTF8)
            wx.GetApp().AppendTempFile(tmpname)
            writer = csv.writer(tmpfile,
                                delimiter=CSVFORMAT_DELIMITER,
                                quotechar=CSVFORMAT_QUOTECHAR,
                                doublequote=True,
                                skipinitialspace=False,
                                lineterminator='\r\n',
                                quoting=int(CSVFORMAT_QUOTING))
            csvrs.insert(0, lTitoli)
            writer.writerows(csvrs)
            tmpfile.close()
            os.startfile(tmpname)




#===============================================================================
#
#             for r in self.dbdett:
#                 if not _unisci(r.id_gruppo, r.id_centro, r.id_sezione, r.id_sezione1, r.id_sezione2) in cl:
#                     row=[]
#                     w=''
#                     for field in ['centro', 'gruppo', 'sezione', 'sezione1', 'sezione2']:
#                         v=getattr(r,field)
#                         if v:
#                             w='%s%s/' % (w, v)
#                         else:
#                             break
#                     row.append(w[:-1])
#                     row.append(r.datreg)
#                     row.append(r.causale)
#                     row.append(r.datdoc)
#                     row.append(r.numdoc)
#                     row.append(r.fornitore)
#                     row.append(r.id_pdc)
#                     row.append(r.sottoconto)
#                     row.append(locale.format("%.2f", r.impdett, grouping=True))
#                     csvrs.append(row)
#
#
#
#
#
#         pass
#===============================================================================
