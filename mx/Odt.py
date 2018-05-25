#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         custcontab/comunicazione.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

import os
import sys    
import datetime
import time
import zipfile
#import locale    
import tempfile
from xml.dom import minidom  
import subprocess 


class odtDocument():
    model=None
    singleValue=None
    replicatedValue=None
    
    def __init__(self, model=None):
        self.model=model
        self.singleValue={}
        self.replicatedValue=[]

    def isTable2Repeat(self, nodeTable):
        return (nodeTable.toprettyxml('\t').find('REPEAT')>=0)
    
    def isRowStartRepeat(self, nodeRow):
        return (nodeRow.toprettyxml('\t').find('&lt;&lt;'+'START_REPEAT'+'&gt;&gt;')>=0)
        
    def isRowEndRepeat(self, nodeRow):
        return (nodeRow.toprettyxml('\t').find('&lt;&lt;'+'END_REPEAT'+'&gt;&gt;')>=0)

    def NormalizeValue(self, value):
        newValue="".join(x for x in value if x.isalnum()or x==' ' or x=='.' or x=='(' or x==')')
        newValue=newValue.replace(' ', '_')
        newValue=newValue.replace('.', '_')
        newValue=newValue.replace('_ ', '_')
        newValue=newValue.replace(' _', '_')
        return newValue

    def CreateDir(self, fullpath):
        dir, file =os.path.split(fullpath)
        drive, dir= os.path.splitdrive(dir)
        drive=drive+'\\'
        wrk=''
        for x in dir.split('\\'):
            wrk=os.path.join(wrk, x)
            wrkDir=os.path.join(drive, wrk)
            if not os.path.exists(wrkDir):
                os.makedirs(wrkDir)

    def MakeOdt(self, newFile):
        def z(x, l):
            return str(x).zfill(l)
        try:
            self.CreateDir(newFile)
            zipInput=zipfile.ZipFile(self.model, 'a')
            txt=zipInput.read('content.xml')
            txt=self.AdeguaXml(txt)
            txt=self.MergeSingleValue(txt)

            # Necessario per riunificare il comportamento che a seconda se si sia in ambiente di sviluppo o meno
            # risulta essere misteriosamente differente                
            txt=self.WorkAround(txt)
            
            zipOut = zipfile.ZipFile (newFile, 'w')
            for item in zipInput.infolist():
                buffer = zipInput.read(item.filename)
                if (item.filename != 'content.xml'):
                    zipOut.writestr(item, buffer)
                else:
                    zipOut.writestr(item, txt)
            zipOut.close()
            zipInput.close()
        except:
            newFile=''
        return newFile
        
    def ViewDoc(self, file2view):
        file2view = file2view.replace('/', '\\')
        self.ViewDoc1(file2view)

    def ViewDoc1(self, file2view):
        path, file = os.path.split(file2view)
        os.chdir(path)
        cmd = 'start %s' %  file
        subprocess.call(cmd, shell=True)        


        
    def WorkAround(self, txt):
        tmpFile=tempfile.NamedTemporaryFile().name
        text_file = open(tmpFile, "w")
        text_file.write(txt)
        text_file.close()
        
        text_file = open(tmpFile, "r")
        txt=text_file.read()
        text_file.close()
        os.remove(tmpFile)
        
        return txt
        
        
    
        
    def MergeSingleValue(self, txt):
        for k in self.singleValue.keys():
            valore = self.singleValue[k]
            if not hasattr(sys, 'frozen'):
                valore = str(valore)
            if '&' in valore:
                valore = valore.replace('&', '&amp;')    
                
            if '<<' in k:
                k=k.replace('<<', '&lt;&lt;')
                k=k.replace('>>', '&gt;&gt;')
            else:
                k = "&lt;&lt;%s&gt;&gt;" % k
            try:
                txt = txt.replace(k,valore)
            except:
                pass
        return txt

    def MergeRepeatedValue(self, txt):
        for v in self.replicatedValue:
            for k in v.keys():
                valore=v[k]
                k=k.replace('<<', '')
                k=k.replace('>>', '')
                k=k.upper()
                try:
                    txt=txt.replace('&lt;&lt;'+k+'&gt;&gt;',valore, 1)
                except:
                    pass
        return txt
        
    def AdeguaXml(self, txt):
        xmldoc=minidom.parseString(txt)        
        allTable=xmldoc.getElementsByTagName('table:table')
        for t in allTable:
            isRowStart=False
            isRowEnd=False
            nodeStartRepeat=None
            nodeEndRepeat=None
            nodeRepeated=[]
            if self.isTable2Repeat(t):
                for row in t.getElementsByTagName('table:table-row'):
                    isRowStart=self.isRowStartRepeat(row) or isRowStart
                    isRowEnd=self.isRowEndRepeat(row) or isRowEnd
                    if self.isRowStartRepeat(row):
                        nodeStartRepeat=row
                    if self.isRowEndRepeat(row):
                        nodeEndRepeat=row
                    if isRowStart and not isRowEnd:
                        if not self.isRowStartRepeat(row) and not self.isRowEndRepeat(row):
                            nodeRepeated.append(row)
                            
                            
                for i in range(1,len(self.replicatedValue)):
                    for newRow in nodeRepeated:
                        newNode= newRow.cloneNode(99)
                        t.insertBefore(newNode, nodeEndRepeat)
                t.removeChild(nodeStartRepeat)
                t.removeChild(nodeEndRepeat)
                    
        txt=xmldoc.toprettyxml('\t').encode('utf-8')
        return txt

    def InsertFieldIndex(self, txt, index, position):
        def z(x, l):
            return str(x).zfill(l)
        return txt[:position] + z(index,2) + txt[position:]

    def AdeguaRow(self, newNode, index, doc=None):
        startTag='&lt;&lt;'
        endTag='&gt;&gt;'
        txt=newNode.toprettyxml('\t')
        startFind=0
        for i in range(0, txt.count('&lt;&lt;')):
            startFind=txt.find(endTag, startFind)
            txt=self.InsertFieldIndex(txt, index, startFind)
            startFind=startFind+4
        return newNode


