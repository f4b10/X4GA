#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/__init__.py
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
import os, sys
import glob
import cStringIO

from report.output import print_Report as PrintRpt

import stormdb as adb

import awc.util as awu

import report_wdr as wdr

# Static imports from PIL for py2exe
from PIL import GifImagePlugin
from PIL import JpegImagePlugin


TYPE_PDF = 0


pathrpt = '.'  #path definizione report jrxml
def SetPathRpt(x):
    global pathrpt
    pathrpt = awu.ExpandPath(x)

pathpdf = '.'  #path generazione pdf
def SetPathPdf(x):
    global pathpdf
    pathpdf = awu.ExpandPath(x)

pathimg = ''   #path ricerca immagini
def SetPathImg(x):
    global pathimg
    pathimg = awu.ExpandPath(x)

pathsub = ''   #path alternativa di ricerca del jrxml
def SetPathSub(x):
    global pathsub
    pathsub = awu.ExpandPath(x)


pathalt = []   #lista path alternative di ricerca del jrxml
def ClearPathAlt():
    global pathalt
    del pathalt[:]
def AppendPathAlt(x):
    global pathalt
    pathalt.append(awu.ExpandPath(x))


usedpath = ''  #path usata, dipende dalla selezione del report


printername = '' #nome stampante per stampa diretta
def SetPrinterName(name):
    global printername
    printername = name
def GetPrinterName():
    return printername

labelername = '' #nome stampante etichettatrice
def SetLabelerName(name):
    global labelername
    labelername = name
def GetLabelerName():
    return labelername

updatelastprinter = True
def SetUpdateLastPrinter(u):
    global updatelastprinter
    updatelastprinter = u

actiondefault = 'view'
def SetActionDefault(a):
    assert a in 'view print'.split()
    global actiondefault
    actiondefault = a
def GetActionDefault():
    return actiondefault

dde = True
def SetDDE(d):
    assert type(d) is bool
    global dde
    dde = d
def GetDDE():
    return dde

pdfcmd = None
def SetPdfCommand(c):
    global pdfcmd
    pdfcmd = c


class MultiReportStandardDialog(wx.Dialog):
    
    reportname = None
    printername = None
    bitmap = None
    _action = None
    _copies = None
    _can_preview = None
    _can_print = None
    
    def __init__(self, *args, **kwargs):
        self._can_preview = kwargs.pop('can_preview', True)
        self._can_print = kwargs.pop('can_print', True)
        wx.Dialog.__init__(self, *args, **kwargs)
        self.FillControls()
        self.CenterOnScreen()
        def cn(x):
            return self.FindWindowByName(x)
        if (actiondefault == 'view' or not dde) and self._can_preview:
            cn('btnpreview').SetDefault()
            self._action = 'VIEW'
        elif (actiondefault == 'print' and dde) and self._can_print:
            cn('btnprint').SetDefault()
            self._action = 'PRINT'
        if not dde:
            for name in 'btnprint printername numcopie'.split():
                cn(name).Disable()
        self.Bind(wx.EVT_LISTBOX, self.OnHiLite, id=wdr.ID_REPORTS)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnLaunch, id=wdr.ID_REPORTS)
        self.Bind(wx.EVT_COMBOBOX, self.OnPrinterChanged, cn('printername'))
        for name, func in (('btnpreview', self.OnPreview),
                           ('btnprint', self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def SetEmailOnlyButton(self, totemail):
        cn = self.FindWindowByName
        cn('btnpreview').SetLabel('Spedisci %d email' % totemail)
        cn('btnprint').Hide()
        self.Layout()
    
    def OnLaunch(self, event):
        self._SetOutput(self._action)
    
    def OnPrinterChanged(self, event):
        self.FindWindowByName('btnprint').Enable()
        event.Skip()
    
    def FillControls(self):
        wdr.MultiReportBottomPanel = wdr.MultiReportStandardBottomPanel
        wdr.MultiReportFunc(self)
    
    def ShowModal(self, *args, **kwargs):
        def cn(x):
            return self.FindWindowByName(x)
        if not self._can_preview:
            cn('btnpreview').Disable()
        p = cn('printername')
        if not p.GetValue() or not self._can_print:
            cn('btnprint').Disable()
        c = cn('numcopie')
        if c.GetValue() == 0:
            c.SetValue(1)
        self.FindWindowByName('reports').SetFocus()
        return wx.Dialog.ShowModal(self, *args, **kwargs)
    
    def OnHiLite(self, event):
        self.HiLite()
        event.Skip()
    
    def HiLite(self):
        ci = lambda x: self.FindWindowById(x)
        reports = ci(wdr.ID_REPORTS)
        n = reports.GetSelection()
        if n>=0:
            if self.bitmap:
                self.bitmap.Destroy()
            img = ci(wdr.ID_PANELPREVIEW)
            bmp = reports.GetClientData(n)[1]
            self.bitmap = wx.StaticBitmap(img, -1, bmp, size=img.GetClientSize())
            note = ci(wdr.ID_NOTE)
            text = reports.GetClientData(n)[2]
            try:
                note.SetValue(text)
            except:
                text = text.decode('iso-8859-1')
                try:
                    note.SetValue(text)
                except:
                    note.SetValue('')
    
    def OnPrint(self, event):
        self._SetOutput('PRINT')
        event.Skip()
    
    def OnPreview(self, event):
        self._SetOutput('VIEW')
        event.Skip()
    
    def _SetOutput(self, tipo):
        self._action = tipo
        if not dde:
            self.EndModal(wx.ID_OK)
        reports, printers, copies = map(lambda x: self.FindWindowByName(x), 
                                'reports printername numcopie'.split())
        n = reports.GetSelection()
        if n>=0:
            d = reports.GetClientData(n)
            self.reportname = d[0]
            self.printername = printers.GetValue()
            if d[3] is not None:
                prt = d[3]
                msg = "Il report selezionato è impostato per essere stampato su '%s'\nUso tale stampante?" % prt
                if awu.MsgDialog(self, msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                    self.printername = prt
                    SetUpdateLastPrinter(False)
            self._copies = copies.GetValue()
            self.EndModal(wx.ID_OK)
    
    def SetReport(self, path, name, multi_default=None):
        ci = lambda x: self.FindWindowById(x)
        ci(wdr.ID_REPORTNAME).SetLabel(name)
        reports = ci(wdr.ID_REPORTS)
        sel = None
        searchReportDef = path
        if os.path.isdir(path):
            searchReportDef += "/*"
        searchReportDef += ".jrxml"
        for n, r in enumerate(glob.glob(searchReportDef)):
            r = r.replace('\\', '/')
            name = r[r.rfind('/')+1:-6]
            if name == multi_default or (sel is None and multi_default is None):
                sel = n
            if '_' in name:
                #i report che contengono il carattere '_' nel nome sono interni
                #quindi vengono esclusi dalla visualizzazione
                continue
            fname = r[:-6]+'.png'
            if os.path.exists(fname):
                data = open(fname, "rb").read()
                stream = cStringIO.StringIO(data)
                bmp = wx.BitmapFromImage(wx.ImageFromStream(stream))
            else:
                bmp = wx.NullBitmap
            fname = r[:-6]+'.txt'
            if os.path.exists(fname):
                note = open(fname).read()
            else:
                note = ''
            fname = r[:-6]+'.prt'
            if os.path.exists(fname):
                prt = open(fname).read()
            else:
                prt = None
            reports.Append(epura(name), (r, bmp, note, prt))
        
        
        if reports.GetCount()>0:
            reports.SetSelection(sel or 0)
            self.HiLite()
    
    def GetReportName(self):
        return self.reportname
    
    def SetPrinter(self, printer):
        p = self.FindWindowByName('printername')
        q = p.GetQueues()
        if printer in q:
            self.printername = printer
            p.SetSelection(q.index(printer))
    
    def GetPrinterName(self):
        return self.printername
    
    def SetCopies(self, c=1):
        self._copies = c
        self.FindWindowByName('numcopie').SetValue(c)
    
    def GetCopies(self):
        return self._copies
    
    def GetAction(self):
        return self._action
    
    def GetLabelOffset(self):
        return [self.FindWindowById(x).GetValue() for x in (wdr.ID_ROW0, 
                                                            wdr.ID_COL0)]


# ------------------------------------------------------------------------------


class Report:
    """
    Generatore reportistica
    """
    
    ChoiceDialog = MultiReportStandardDialog
    
    usedReport = None
    usedDialog = None
    
    def __init__(self, parent, dbt, rptdef, rptout=None, output="VIEW", 
                 desc=None, tipo=TYPE_PDF, noMove=False, exitOnGroup=False,
                 rowFunc=None, testrec=None, dbfunc=None, rowFilter=None,
                 messages=True, printer=None, copies=None, 
                 changepathname=None, changefilename=None, forcechoice=False, 
                 emailbutton=0, multi_default=None, 
                 otherquestions_filler=None, otherquestions_reactor=None,
                 multicopia_init=None, multicopia_reactor=None,
                 can_preview=True, can_print=True,
                 **oa):
        
        self.messages = messages
        self.parameters = {}
        
        if not self.TestData(parent, dbt, testrec):
            return
        
        #ricerca del report
        for pathsrc in self.GetPaths():
            test = "%s/%s" % (pathsrc, rptdef)
            if os.path.isdir(test) or os.path.isfile(test+'.jrxml'):
                if os.path.isfile(test+'.jrxml') and output == "STORE" and not forcechoice:
                    rptdef = test+'.jrxml'
                    copies = 1
                    break
                if not printer:
                    printer = printername
                    SetUpdateLastPrinter(True)
                rptdef, printer, def_output, copies = self.GetMultiReport(parent, test, rptdef, printer, copies, emailbutton, multi_default=multi_default, otherquestions_filler=otherquestions_filler, can_preview=can_preview, can_print=can_print)
                if callable(otherquestions_reactor):
                    otherquestions_reactor(self.usedDialog)
                if output != "STORE":
                    output = def_output
                if rptdef is None:
                    return
        if rptdef is not None:
            global usedpath
            usedpath = pathsrc
        
        if not os.path.exists(rptdef):
            err = "Manca la definizione del report %s" % rptdef
            if self.messages:
                awu.MsgDialog(parent, message=err)
            else:
                raise Exception, err
            return
        
        if dbfunc is not None:
            dbt = dbfunc(rptdef.replace('.jrxml',''), self)
        
        if dbt is None:
            return
        
        if not self.TestData(parent, dbt, testrec, datareq=True):
            return
        
        if rptout is None:
            if changefilename:
                rptout = changefilename
            else:
                rptout = rptdef.replace('\\','/')[:-6]
                if '/' in rptout:
                    rptout = rptout[rptout.rfind('/')+1:]
            pp = pathpdf
            if changepathname:
                if changepathname.startswith('+'):
                    pp = os.path.join(pathpdf, changepathname[1:])
                else:
                    pp = changepathname
            rptout = "%s/%s." % (pp, rptout)
        
        if desc is None:
            desc = "documento"
        
        if tipo == TYPE_PDF:
            if rptout[-4:].lower() != '.pdf':
                if rptout[-1] != '.':
                    rptout += "."
                rptout += "pdf"
            
            basePath, _ = os.path.split(rptout)
            try:
                if not os.path.isdir(basePath):
                    os.makedirs(basePath)
            except:
                awu.MsgDialog(None, 'Impossibile creare la cartella %s' % basePath, style=wx.ICON_ERROR|wx.YES_NO|wx.YES_DEFAULT)
                pass
                
            p = self.parameters
            p['rptdef'] = rptdef
            p['rptout'] = rptout
            p['output'] = output
            p['dbTable'] = dbt
            p['parentWindow'] = parent
            p['waitMessage'] = "Generazione %s in corso" % desc
            p['pageCount'] = None
            p['noMove'] = noMove
            p['exitOnGroup'] = exitOnGroup
            p['rowFunc'] = rowFunc
            p['rowFilter'] = rowFilter
            p['messages'] = messages
            p['dde'] = dde
            p['printer'] = printer
            p['labeler'] = labelername
            p['copies'] = copies
            p['multicopia_init'] = multicopia_init
            p['multicopia_reactor'] = multicopia_reactor
            p['otherargs'] = oa
            self.usedReport = self.StartReport()
            
            if updatelastprinter:
                SetPrinterName(printer)
    
    def StartReport(self, rptout=None):
        p = self.parameters
        rptdef = p['rptdef']
        if rptout is None:
            #nessun nome specificato, uso quello impostato da Report.__init__
            rptout = p['rptout']
        else:
            #nome specificato, uso tale nome accodato al percorso pdf attualmente
            #impostato, da Report.__init__
            bp = os.path.split(self.GetFileName())[0]
            rptout = os.path.join(bp, rptout)
        if rptout[-4:].lower() != '.pdf':
            if rptout[-1] != '.':
                rptout += "."
            rptout += "pdf"
        output = p['output']
        dbt = p['dbTable']
        parentWindow = p['parentWindow']
        waitMessage = p['waitMessage']
        pageCount = p['pageCount']
        noMove = p['noMove']
        exitOnGroup = p['exitOnGroup']
        rowFunc = p['rowFunc']
        rowFilter = p['rowFilter']
        messages = p['messages']
        dde = p['dde']
        printer = p['printer']
        labeler = p['labeler']
        copies = p['copies']
        multicopia_init = p['multicopia_init']
        multicopia_reactor = p['multicopia_reactor']
        oa = p['otherargs']
        return PrintRpt(rptdef, rptout, output, dbTable=dbt,
                        parentWindow=parentWindow,
                        waitMessage=waitMessage,
                        pageCount=None,
                        noMove=noMove,
                        exitOnGroup=exitOnGroup,
                        rowFunc=rowFunc,
                        rowFilter=rowFilter, 
                        messages=messages, 
                        usedde=dde,
                        printer=printer,
                        labeler=labeler,
                        copies=copies,
                        pdfcmd=pdfcmd,
                        multicopia_init=multicopia_init,
                        multicopia_reactor=multicopia_reactor,
                        **oa)
        
    def GetMultiReport(self, parent, path, name, printer, copies, emailbutton, multi_default=None, otherquestions_filler=None, can_preview=True, can_print=True):
        rptdef = None
        action = None
        dlg = self.ChoiceDialog(parent, -1, "Selezione report", can_preview=can_preview, can_print=can_print)
        p = dlg.FindWindowByName('otherquestionspanel')
        if otherquestions_filler:
            otherquestions_filler(p)
        else:
            p.Hide()
        if emailbutton:
            dlg.SetEmailOnlyButton(emailbutton)
        dlg.SetReport(path, name, multi_default)
        dlg.SetPrinter(printer)
        dlg.SetCopies(copies)
        do = dlg.ShowModal() == wx.ID_OK
        if do:
            rptdef = dlg.GetReportName()
            printer = dlg.GetPrinterName()
            action = dlg.GetAction()
            copies = dlg.GetCopies()
        dlg.Destroy()
        self.ReportSelected(dlg)
        return rptdef, printer, action, copies
    
    def ReportSelected(self, dlg):
        self.usedDialog = dlg
    
    def GetFileName(self):
        out = None
        if self.usedReport:
            out = self.usedReport.nameOutputFile
        return out
    
    def GetPaths(cls):
        paths = []
        if len(pathsub)>0:
            paths.append(pathsub)
        for p in pathalt:
            paths.append(p)
        paths.append(pathrpt)
        return paths
    GetPaths = classmethod(GetPaths)
    
    def GetUsedReport(self):
        return self.usedReport
    
    def GetUsedDialog(self):
        return self.usedDialog
    
    def TestData(self, parent, dbt, testrec, datareq=False):
        ok = True
        if testrec is None:
            testrec = dbt
        if testrec is None:
            ok = not datareq
        else:
            if testrec.RowsCount() == 0:
                if self.messages:
                    err = message="Nessun dato da stampare"
                    awu.MsgDialog(parent, message=err)
                    ok = False
                else:
                    raise Exception, err
        return ok
        
    def SetRange(self, range):
        pass
    
    def SetValue(self, val):
        self.progr.Update(val)


# ------------------------------------------------------------------------------


class MultiReportLabelsDialog(MultiReportStandardDialog):
    
    def FillControls(self):
        wdr.MultiReportBottomPanel = wdr.MultiReportLabelsBottomPanel
        wdr.MultiReportFunc(self)
        def ci(x):
            return self.FindWindowById(x)
        ci(wdr.ID_ROW0).SetValue(1)
        ci(wdr.ID_COL0).SetValue(1)


# ------------------------------------------------------------------------------


class ReportLabels(Report):
    
    ChoiceDialog = MultiReportLabelsDialog
    row0 = 1
    col0 = 1
    
    def GetLabelOffsetRow(self):
        return self.row0
    
    def GetLabelOffsetCol(self):
        return self.col0
    
    def ReportSelected(self, dlg):
        Report.ReportSelected(self, dlg)
        for name in 'row0 col0'.split():
            setattr(self, name, dlg.FindWindowByName(name).GetValue())


# ------------------------------------------------------------------------------


def epura(name, isfile=False):
    if isfile and '/' in name:
        n = name.rindex('/')+1
        path, name = name[:n], name[n:]
    else:
        path, name = '', name
    if name.startswith('-') and '-' in name[1:]:
        name = name[name[1:].index('-', )+2:].lstrip()
    return path+name


# ------------------------------------------------------------------------------


if __name__ == "__main__":
   
    class TryReport(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            dialog = wx.Dialog( None, -1, "SuperApp", [0,0], [100,76] )
            return True
        
    app = TryReport(True)
    
    db = adb.DB()
    db.Connect()
    
    pdc = adb.DbTable("pdc", writable=False)
    mas = pdc.AddJoin("bilmas")
    con = pdc.AddJoin("bilcon")
    tip = pdc.AddJoin("pdctip", "tipana", idLeft="id_tipo")
    pdc.AddOrder("IF(bilmas.tipo='P',1,IF(bilmas.tipo='E',2,3))")
    pdc.AddOrder("bilmas.descriz")
    pdc.AddOrder("bilcon.descriz")
    pdc.AddOrder("pdc.descriz")
    pdc.AddFilter("tipana.tipo NOT IN ('C','F')")
    if pdc.Retrieve():
        Report(pdc, "test")
    else:
        print pdc.GetError()
        app.MainLoop()

