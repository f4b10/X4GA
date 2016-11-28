#!/bin/env python
# -*- coding: utf-8 -*-
"""
coccoawc/controls/treecolumn
"""
import os, tempfile
import sys
import subprocess
import wx
import  wx.gizmos   as  gizmos
import awc.controls.windows as aw
import Env
import stormdb as adb
import csv
import codecs

CSVFORMAT_ASGRID = 0
CSVFORMAT_DELIMITER = ';'
CSVFORMAT_QUOTECHAR = '"'
CSVFORMAT_QUOTING = csv.QUOTE_MINIMAL
CSVFORMAT_EXCELZERO = False



class TreeListCtrl(gizmos.TreeListCtrl):
    idItem = None

    def __init__(self, *args, **kwargs):
        gizmos.TreeListCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick)
        self.idItem=0


    def OnColRightClick(self, evt):
        x, y = list(evt.GetPosition())
        self._Grid_TreeListCtrl(x,y)
        evt.Skip()


    def _Grid_TreeListCtrl(self, x, y):
        voci = []
        menu = wx.Menu()
        voci.append(("Esporta file CSV", self.OnExportCSV, True))
        voci.append(("Esporta file HTML", self.OnExportHTML, True))
        for text, func, enab in voci:
            if text is None:
                menu.AppendSeparator()
                continue
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        self.PopupMenu(menu, (x, y-20))
        menu.Destroy()

    def OnExportCSV(self, event):
        self.ExportCSV()
        event.Skip()

    def ExportCSV(self):
        lista=self.tree2list()
        maxLevel=0
        for level, item, nChild in lista:
            maxLevel=max(maxLevel, level)
        dLivelli={}
        titoli=[]
        for i in range(maxLevel+1):
            dLivelli[i]=''
            titoli.append('Livello %s' % i)
        titoli.append('Valore')

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
        csvrs = []
        csvrs.append(titoli)

        for level, item, nChild in lista:
            row=[]
            for j in range(level, maxLevel+1):
                dLivelli[j]=''
            dLivelli[level]=self.GetItemText(item).strip()

            for j in range(maxLevel+1):
                row.append(dLivelli[j])
            for j in range(1,self.GetColumnCount()):
                try:
                    w=self.GetItemText(item,j).strip()
                    row.append(w)
                except:
                    break
            if nChild==0:
                csvrs.append(row)
        writer.writerows(csvrs)
        tmpfile.close()
        os.startfile(tmpname)

    def OnExportHTML(self, event):
        p=self.GetParent()
        p.ExportHtmlTree()
        event.Skip()

    def GetMaxLevel(self):
        l=self.tree2list()
        MaxLevel=0
        for r in l:
            MaxLevel=max(MaxLevel, r[0])
        return MaxLevel

    def GetLastPathUsed(self):
        s = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGSETUP, 'setup')
        for k, o, f in [
                        ['last_path_used',  'lastPath','descriz'],
                    ]:
            if s.Retrieve("setup.chiave='export_%s'" % k) and s.OneRow():
                setattr(self, o, getattr(s, f))
            else:
                setattr(self, o, '')

    def SaveLastPathUsed(self, outputFile):
        s = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGSETUP, 'setup')
        if s.Retrieve("setup.chiave='export_last_path_used'") and not s.OneRow():
            s.CreateNewRow()
        s.chiave='export_last_path_used'
        path, file = os.path.split(outputFile)
        s.descriz=path
        s.Save()

    def SetExportFile(self):
        self.GetLastPathUsed()
        outputFile=''
        exportPath=self.lastPath
        filename='Centri_costo.html'
        wildcard='*.html'
        dlg = wx.FileDialog(
            self, message="Esporta con nome", defaultDir=exportPath,
            defaultFile=filename, wildcard=wildcard, style=wx.SAVE
            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            outputFile=dlg.GetPath()
            if os.path.exists(outputFile):
                id=aw.awu.MsgDialog(self, u"Esiste già il file %s.\nSi desidera sovrascriverlo?" % outputFile, style=wx.ICON_QUESTION|wx.YES_NO)
                if id==wx.ID_NO:
                    outputFile=''
        return outputFile

    def ExportHtml(self, modelName=None, titolo='', titoliColonna=['COLONNA']):
        if os.path.exists(modelName):
            outputFile=self.SetExportFile()
            if len(outputFile)>0:
                html=[]
                input = open(modelName, "r")
                output= open(outputFile, 'w')
                for line in input :
                    line=line.replace('\n', '')
                    line=line.replace('<<title>>', titolo)
                    line=line.replace('<<azienda>>', Env.Azienda.descrizione)
                    line=line.replace('<<dataexport>>', Env.DateTime.today().strftime('%d-%m-%Y'))
                    line=line.replace('<<titolo>>', titolo)
                    if line.find('<<TitoliColonne>>')>=0:
                        wrk=''
                        for t in titoliColonna:
                            wrk='%s<th>%s</th>' % (wrk, t)
                        line=line.replace('<<TitoliColonne>>', wrk)

                    if line.find('<<expand_level>>')>=0:
                        maxLevel=self.GetMaxLevel()
                        wrk=''
                        for i in range(maxLevel+1):
                            if i==maxLevel:
                                wrk='%s<span id="%s" class="tbltree-level-item">[%s]</span>&nbsp;\\' % (wrk, i, i+1)
                            else:
                                wrk='%s<span id="%s" class="tbltree-level-item">[%s]</span>&nbsp;\\\n' % (wrk, i, i+1)
                        line=line.replace('<<expand_level>>', wrk)

                    if line.find('<<Struttura>>')>=0:
                        stru=self.scanBranch(stru=[])
                        for r in stru:
                            html.append(r)
                        line=''
                    html.append(line)
                for r in html:
                    output.write('%s\n' % r)
                input.close()
                output.close()

                self.SaveLastPathUsed(outputFile)
                id=aw.awu.MsgDialog(self, u"File di esportazione %s è stato generato.\nSi desidera visualizzarlo?" % outputFile, style=wx.ICON_QUESTION|wx.YES_NO)
                if id==wx.ID_YES:
                    cmd='START %s' %  outputFile
                    if hasattr(sys, 'frozen'):
                        os.system(cmd)
                    else:
                        # subprocess.Popen([pdfcmd, filename])
                        FNULL = open(os.devnull, 'w')
                        process =subprocess.Popen(cmd, stdout=FNULL, stderr=FNULL, shell=True)
                        process.wait()
        else:
            id=aw.awu.MsgDialog(self, u"Esportazione impossibile!\n Modello per esportazione assente (%s)" % modelName, style=wx.ICON_ERROR)

    def getLeefList(self):
        l=self.tree2list()
        leef=[]
        for e in l:
            if e[2]==0:
                leef.append(e)
        return leef

    def tree2list(self, item=None, nLevel=0, lista=None):
        l=nLevel
        if not lista:
            lista=[]
        if item is None:
            item=self.GetRootItem()
        key=item
        lChildren=self._GetChildren(item)
        lista.append([nLevel, key, len(lChildren)])
        if len(lChildren)>0:
            for son in lChildren:
                self.tree2list(son, nLevel=l+1, lista=lista)
        return lista

    def _GetChildren(self, item):
        lChildren=[]
        if self.ItemHasChildren(item):
            wrkItem, cookie = self.GetFirstChild(item)
            lChildren.append(wrkItem)
            while wrkItem.IsOk():
                try:
                    wrkItem, cookie = self.GetNextChild(item, cookie)
                    if wrkItem.IsOk():
                        lChildren.append(wrkItem)
                except:
                    break
        return lChildren


    def scanBranch(self, item=None, nLevel=0, idParent=0, stru=[]):
        self.idItem=self.idItem+1
        idItem=self.idItem
        if item is None:
            item=self.GetRootItem()
        l=nLevel
        if self.GetColumnCount()>1:
            if idParent==0:
                stru.append('<tr row-id="%s"><td>%s</td><td class="data" align="right"><font size="4">&euro;&nbsp;%s</font></td></tr>' % (idItem, self.GetItemText(item, 0), self.GetItemText(item, 1)))
            else:
                stru.append('<tr row-id="%s"     parent-id="%s">    <td>%s     </td><td class="data" align="right"><font size="4">&euro;&nbsp;%s</font></td></tr>' % (idItem, idParent, self.GetItemText(item, 0), self.GetItemText(item, 1)))
        else:
            if idParent==0:
                stru.append('<tr row-id="%s"><td>%s</td></tr>' % (idItem, self.GetItemText(item, 0)))
            else:
                stru.append('<tr row-id="%s"     parent-id="%s">    <td>%s     </td></tr>' % (idItem, idParent, self.GetItemText(item, 0)))
        lChildren=self._GetChildren(item)
        if len(lChildren)>0:
            for son in lChildren:
                stru=self.scanBranch(son, nLevel=l+1, idParent=idItem, stru=stru)
        return stru
