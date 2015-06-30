#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         custanag/page/contatori.py
# Author:       Marcello Montaldo
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------
import wx.lib
import awc.controls.linktable
from awc.controls.linktable import EVT_LINKTABCHANGED
from awc.controls.datectrl import EVT_DATECHANGED

import MySQLdb
import Env
import awc.controls.windows as aw
from awc.util import MsgDialog, MsgDialogDbError
import wx.grid as gl
import awc.controls.dbgrid as dbglib

stdcolor = Env.Azienda.Colours
bt = Env.Azienda.BaseTab
from awc.tables.util import CheckRefIntegrity

class GenericPersonalLinkedPage_InternalGrid(dbglib.DbGridColoriAlternati):
    _grid_contatori = None
    rsdata          = None
    rsdatamod       = None
    rsdatanew       = None
    rsdatadel       = None
    colmap          = None
    colsize         = None
    mainPanel       = None
    gridTableName   = None
    fields          = None
    dFields         = None
    updating        = None

    def __init__(self, *args, **kwargs):

        self.rsdata     = []
        self.rsdatamod  = []
        self.rsdatanew  = []
        self.rsdatadel  = []

        self.mainPanel = kwargs.pop('mainPanel', None)
        self.gridTableName = kwargs.pop('gridTableName', None)
        dbglib.DbGridColoriAlternati.__init__(self, *args, **kwargs)

        self.SetGridField()
        self.SetConnection()
        self.SetColumnGrid()

        self.SetData(self.rsdata, self.colmap, canEdit=True)
        self.SetCellDynAttr(self.GetAttr)
        self.SetColumn2Fit()
        self.SetColumnSize()
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent = self.mainPanel.FindWindowByName('%s_panelgrid' % self.gridTableName)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnSelected)
        self.LoadData()



    #TODO: Introdurre la possibilità di specificare il/i campi che debbono
    #necessariamente assumenre un valore univoco

    #TODO: Introdurre la possibilità di specificare il/i campi da gestire in
    #      sola lettura per i quali non è consentita la modifica in editazione

    def GetDbColumns(self):
        return self._cols



    def SetDisabledField(self):
        return []


    def SetColumn2Fit(self):
        self.SetFitColumn(0)

    def SetOrder(self):
        return []

    def SetExclusiveCheckField(self):
        return []

    def SetCanEditCheck(self):
        return []

    def SetColumnSize(self):
        for i, s in enumerate(self.colsize):
            self.SetColumnDefaultSize(i, s)

    def SetConnection(self):
        self.db_conn = Env.Azienda.DB.connection
        self.db_curs = None
        try:
            self.db_curs = self.db_conn.cursor()

        except MySQLdb.Error, e:
            MsgDialog(self,
                      message="Problema durante l'accesso al database.\n\n%s: %s"
                      % (e.args[0], e.args[1]),
                      caption = "X4 :: Errore di accesso",
                      style=wx.YES_CANCEL|wx.ICON_EXCLAMATION)

    def OnCreate(self, evt):
        self.updating = True
        self.AddNewRow()
        self.ResetView()
        self.SetGridCursor(len(self.rsdata)-1,1)
        self.mainPanel.SetDataChanged(True)

    def UpdateDataRecord(self):
        self.WriteData();
        self.LoadData()
        self.mainPanel.SetDataChanged(False)

    def EnableFields(self, enable=True):
        def cn(name):
            return self.mainPanel.FindWindowByName('%s_%s'% (self.gridTableName, name))
        for col, name in enumerate(self.fields):
            c = cn(name)
            if name in self.SetDisabledField():
                c.Enable(False)
            else:
                if c:
                    c.Enable(enable)

    def ResetFields(self):
        def cn(name):
            return self.mainPanel.FindWindowByName('%s_%s'% (self.gridTableName, name))
        for col, name in enumerate(self.fields):
            c = cn(name)
            if c:
                try:
                    c.SetValue(None)
                except:
                    pass

    def TestWarning(self, row):
        def cn(name):
            return self.mainPanel.FindWindowByName('%s_%s'% (self.gridTableName, name))
        ctr=cn('warning')
        if ctr:
            label = ""
            for name in self.dFields.keys():
                if hasattr(self, 'Check_%s' % name):
                    if not getattr(self, 'Check_%s' % name)(self.rsdata[row]):
                        if hasattr(self, 'Warning_%s' % name):
                            label='%s %s' % (label, getattr(self, 'Warning_%s' % name)(self.rsdata[row]))
                        else:
                            label='%s %s non valido' % (label, name)
            ctr.SetLabel(label )

    def OnPrint(self, evt):
        print 'OnPrint'
        evt.Skip()

    def BeforeWriteData(self):
        pass

    def WriteData(self):
        self.BeforeWriteData()
        return self.WriteRelated(self.gridTableName, self.fields, self.rsdata,\
                                 self.rsdatanew, self.rsdatamod, self.rsdatadel)

    def WriteRelated(self, table, fields, rs, rsins, rsmod, rsdel):
        written = False
        setCol = ""
        for field in fields[1:]:
            setCol += "%s=%%s, " % field
        setCol += r"id_pdc=%s"
        cmdDel = "DELETE FROM %s WHERE %s.id=%%s"\
               % (table, table)
        cmdIns = "INSERT INTO %s SET %s"\
               % (table, setCol)
        cmdUpd = "UPDATE %s SET %s WHERE %s.id=%%s"\
               % (table, setCol, table)
        parDel = []
        parIns = []
        parUpd = []
        for rec in rs:
            recid = rec[0]
            if recid in rsdel:
                parDel.append(recid)
            else:
                par = rec[1:]
                par.append(self.mainPanel.db_recid)
                if recid is None:
                    parIns.append(par)
                else:
                    par.append(recid)
                    parUpd.append(par)
        for recid in rsdel:
            if not recid in parDel:
                parDel.append(recid)
        try:
            if parDel:
                self.db_curs.executemany(cmdDel, parDel)
            if parIns:
                self.db_curs.executemany(cmdIns, parIns)
            if parUpd:
                self.db_curs.executemany(cmdUpd, parUpd)
            written = True
        except MySQLdb.Error, e:
            aw.awu.MsgDialog(self, repr(e.args))
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args))
            pass
        return written

    def LoadData(self):
        if self.mainPanel.db_recid is None:
            rsdata = ()
        else:
            cmd =\
"""SELECT """
            for field in self.fields:
                cmd += "d.%s, " % field
            cmd = cmd[:-2]+" FROM %s AS d WHERE d.id_pdc=%%s """ % self.gridTableName
            order=''
            for f in self.SetOrder():
                order = '%sd.%s, ' % (order, f)
            order=order[:-2]
            if len(order)>0:
                cmd = '%s ORDER BY %s' % (cmd, order)
            try:
                self.db_curs.execute(cmd, self.mainPanel.db_recid)
                rsdata = self.db_curs.fetchall()
                void = False
            except MySQLdb.Error, e:
                MsgDialogDbError(self, e)
            except Exception, e:
                pass
        del self.rsdata[:]

        for n in range(len(rsdata)):
            self.rsdata.append(list(rsdata[n]))
        self.ResetView()
        del self.rsdatadel[:]
        del self.rsdatamod[:]
        del self.rsdatanew[:]
        if len(self.rsdata)>0:
            self.UpdateCard()
            #===================================================================
        else:
            self.ResetFields()
            self.EnableFields(False)
        self.Refresh()
        self.ResetColLabels()

    def UpdateFields(self, row):
        if not 0 <= row < len(self.rsdata):
            return
        def cn(name):
            return self.mainPanel.FindWindowByName('%s_%s'% (self.gridTableName, name))
        r = self.rsdata[row]
        for col, name in enumerate(self.fields):
            c = cn(name)
            if c:
                needNotifyChange=self.SetNotify(c, False)
                try:
                    c.SetValue(r[col])
                except:
                    c.SetValue('')
                needNotifyChange=self.SetNotify(c, needNotifyChange)

    def SetNotify(self, ctrl, value):
        status=False
        try:
            status=ctrl.NotifyChanges(value)
        except:
            pass
        return status

    def UpdateCard(self):
        self.MakeCellVisible(0,0)
        self.SetGridCursor(0,0)
        self.SelectRow(0)
        self.updating = True
        self.UpdateFields(0)
        self.updating = False


    def ChangeData(self, newdata):
        self.rsdata=newdata
        self.UpdateCard()


    def OnGridChanged(self, event):
        row = self.GetSelectedRows()[0]
        if self.updating or not 0 <= row < len(self.rsdata):
            return
        obj = event.GetEventObject()
        name = obj.GetName()
        lProceed=name.startswith('%s_' % self.gridTableName)
        if lProceed:
            fieldName = name[(len(self.gridTableName)+1):]
        else:
            if len(obj.GetParent().GetChildren())>0:
                ancestor=obj.GetParent().GetName()
                lProceed=ancestor.startswith('%s_' % self.gridTableName)
                fieldName = ancestor[(len(self.gridTableName)+1):]
        if lProceed:
            if fieldName in self.fields:
                col = self.fields.index(fieldName)
                self.rsdata[row][col] = obj.GetValue()
                self.Refresh()
                self.TestWarning(row)
                self.mainPanel.SetDataChanged()

    def OnSelected(self, evt):
        def cn(name):
            return self.mainPanel.FindWindowByName('%s_%s'% (self.gridTableName, name))
        row = evt.GetRow()
        col = evt.GetCol()
        enable = 0<=row<len(self.rsdata)
        if enable:
            try:
                self.rsdata.MoveRow(row)
            except:
                pass
            type=self.colmap[col][2]
            if 'bool' in type and self.fields[self.colmap[col][0]] in self.SetCanEditCheck():
                r=self.rsdata[row]
                v = r[self.colmap[col][0]] = 1-(r[self.colmap[col][0]] or 0)
                if v:
                    fieldName=self.fields[self.colmap[col][0]]
                    if fieldName in self.SetExclusiveCheckField():
                        for nr in range(len(self.rsdata)):
                            if nr != row:
                                self.rsdata[nr][self.colmap[col][0]] = 0
                self.ResetView()
                self.mainPanel.SetDataChanged()
        else:
            self.ResetFields()
        self.EnableFields(enable)
        try:
            ctr = cn('butdel')
            ctr.Enable(enable)
            self.updating = True
            self.UpdateFields(row)
            self.updating = False
            self.TestWarning(row)
        except:
            pass
        evt.Skip()

    def IsOk(self, row):
        valok = True
        if 0<=row<len(self.rsdata):
            data = self.rsdata[row]
            for n in self.fields:
                if hasattr(self, 'Check_%s' % n):
                    valok = valok and getattr(self, 'Check_%s' % n)(data)
                if not valok:
                    break
        return valok

    def GetPrimaryKey(self):
        i=0
        idx=aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == self.gridTableName)
        t=bt.tabelle[idx]
        for tipo, nome in t[3]:
            if tipo=='PRIMARY KEY':
                break
        for i, f in enumerate(self.fields):
            if f==nome:
                break
        return i

    def GetDescrizioneEntita(self):
        i=0
        idx=aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == self.gridTableName)
        t=bt.tabelle[idx]
        return t[5][1][0]

    def GetVincoliIntegrita(self):
        i=0
        idx=aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == self.gridTableName)
        t=bt.tabelle[idx]
        return t[4]

    def OnDelete(self, evt):
        sr = self.GetSelectedRows()
        if sr:
            row = sr[-1]
            if 0 <= row < len(self.rsdata):
                idxPrimaryKey=self.GetPrimaryKey()
                des=self.GetDescrizioneEntita()
                desid = self.rsdata[row][idxPrimaryKey]
                do = True
                if desid is not None:
                    vincoli=self.GetVincoliIntegrita()
                    do = CheckRefIntegrity(self, self.db_curs, vincoli, desid)
                    if do:
                        if aw.awu.MsgDialog(self, "Confermi la cancellazione di questo %s?" % des, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                            do = False
                    if do:
                        self.rsdatadel.append(desid)
                if do:
                    self.DeleteRows(row)
                    self.ResetView()
                    self.mainPanel.SetDataChanged()
                    if len(self.rsdata) == 0:
                        self.ResetFields()
                        self.EnableFields(False)
                    else:
                        row = len(self.rsdata)-1
                        self.MakeCellVisible(row,0)
                        self.SetGridCursor(row,0)
                        self.SelectRow(row)
                        self.UpdateFields(row)
                self.Refresh()

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly(True)
        if 0<=row<len(self.rsdata):
            if not self.IsOk(row):
                #colorazione riga se dati errati
                attr.SetTextColour(stdcolor.VALERR_FOREGROUND)
                attr.SetBackgroundColour(stdcolor.VALERR_BACKGROUND)
        return attr

    def SetGridField(self):
        lOk=False
        self.fields=[]
        self.dFields={}
        idx=aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == self.gridTableName)
        t=bt.tabelle[idx]
        i=0
        for n, t, len, dec, des, k in t[2]:
            if not n=='id_pdc':
                self.fields.append(n)
                self.dFields[n]=i
                i=i+1
            else:
                lOk=True
        if not lOk:
            aw.awu.MsgDialog(self, 'Attenzione!\nLa tabella %s deve necessariamente contenere il campo id_pdc.'  %  self.gridTableName, caption="ERRORE PROGRAMMAZIONE", style=wx.ICON_ERROR)

    def AddNewRow(self):
        newc=''
        newData=[]
        for name in self.fields:
            newData.append(self.DefaultValue(name))
        self.rsdata.append(newData)

    def DefaultValue(self, name):
        if hasattr(self, 'DefaultValue_%s' % name):
            value=getattr(self, 'DefaultValue_%s' % name)()
        else:
            value=None
        return value

    def GetThisFunctionName(self, pos=-2):
        import traceback
        stack = traceback.extract_stack()
        filename, codeline, funcName, text = stack[pos]
        return funcName

    def GetActualFieldValue(self, data):
        funcName=self.GetThisFunctionName(pos=-3)
        field=funcName.replace('Check_', '')
        value=data[self.dFields[field]]
        return value

    def GetIndexField(self, fieldName):
        return self.dFields[fieldName]

    def DefaultValue_codice(self):
        try:
            c = self.db_curs
            c.execute("SELECT MAX(0+CODICE) FROM %s des WHERE des.id_pdc=%s"\
                      % (bt.TABNAME_BANCF, self.mainPanel.db_recid))
            rs = c.fetchone()
            lastab = rs[0] or 0
        except:
            lastab = 0
        try:
            lasmem = max([int(x[self.GetIndexField('codice')] or '') for x in self.rsdata])
        except:
            lasmem=0
        newc = str(int(max(lastab, lasmem)+1))
        return newc

    def Data2Dict(self, index):
        dict={}
        for n in self.fields:
            dict[n]=self.rsdata[index][self.GetIndexField(n)]
        return dict



def GetNamedChildrens(container, names=None, Test=None):
    """
    Esamina tutta la discendenza di figli di C{container} e ritorna una
    lista dei controlli.  Se C{names} è definito vengono esaminati solo
    i controlli i cui nomi siano compresi in tale lista.

    @param container: contenitore da esaminare
    @type container: L{wx.Window}
    @param names: lista nomi da testare
    @type names: lista di stringhe

    @return: lista di controlli
    @rtype: list
    """
    if Test is None:
        Test = lambda c: True
    childrens = container.GetChildren()
    namedlist = [ child for child in childrens\
                  if len(child.GetName())>0\
                  and (not names or child.GetName() == names)\
                  and Test(child)]
    for child in childrens:
        namedlist += GetNamedChildrens(child, names, Test)
    return namedlist




from contab.pdcint import ClientiInterrPanel


class GenericPersonalPage_Panel(wx.Panel):
    wdrFunc=None

    def __init__(self, *args, **kwargs):
        self.mainPanel= kwargs.pop('mainPanel', None)
        self.wdrFunc= kwargs.pop('wdrFunc', None)
        wx.Panel.__init__(self, *args, **kwargs)

    def InitDataControls(self):
        from awc.util import GetNamedChildrens
        controls = GetNamedChildrens( self,\
                                      [ col[0] \
                                        for col in self.mainPanel.anag_db_columns ])
        new_db_datalink =[ ( ctr.GetName(), ctr ) for ctr in controls ]
        new_db_datacols= [ col for col,ctr in new_db_datalink ]

        for col, ctr in new_db_datalink:
            for i in ['CodiceFiscaleEntryCtrl' ,
                      'FileEntryCtrl' ,
                      'FolderEntryCtrl' ,
                      'FullPathFileEntryCtrl' ,
                      'HttpEntryCtrl' ,
                      'MailEntryCtrl' ,
                      'PartitaIvaEntryCtrl' ,
                      'PhoneEntryCtrl']:
                if isinstance(ctr, getattr(awc.controls.entries, i )):
                    self.mainPanel.BindChangedEvent(ctr.GetChildren()[0])
            if isinstance(ctr, wx.TextCtrl):
                self.mainPanel.BindChangedEvent(ctr)
            elif isinstance(ctr, awc.controls.datectrl.DateCtrl):
                self.mainPanel.BindChangedEvent(ctr)
            elif isinstance(ctr, wx.CheckBox):
                self.mainPanel.BindChangedEvent(ctr)
            elif isinstance(ctr, awc.controls.linktable.LinkTable):
                self.mainPanel.BindChangedEvent(ctr)



        for o in new_db_datalink:
            self.mainPanel.anag_db_datalink.append(o)

        for o in new_db_datacols:
            self.mainPanel.anag_db_datacols.append(o)




class GenericPersonalLinkedPage_Panel(ClientiInterrPanel):

    #===========================================================================
    # rsdata         = None
    # rsdatamod      = None
    # rsdatanew      = None
    # rsdatadel      = None
    # mainPanel      = None
    #===========================================================================
    gridTableName  = None
    _grid          = None

    db_datalink    = None
    db_datacols    = None


    def __init__(self, *args, **kwargs):

        self.db_recid = kwargs.pop('idPdc', None)
        self.mainPanel= kwargs.pop('mainPanel', None)

        ClientiInterrPanel.__init__(self, *args, **kwargs)

        #=======================================================================
        # self.rsdata      = []
        # self.rsdatamod   = []
        # self.rsdatanew   = []
        # self.rsdatadel   = []
        #=======================================================================
        self._grid  = None

    def UpdateDataRecord( self):
        self._grid.UpdateDataRecord()

    def UpdateDataControls( self ):
        self._grid.LoadData()

    def BindChangedEvent(self, c):
        fullName=c.GetName()
        if fullName.startswith('%s_' % self.gridTableName):
            name=fullName.replace('%s_' % self.gridTableName, '')
            idx=aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == self.gridTableName)
            t=bt.tabelle[idx][2]
            n = aw.awu.ListSearch(t, lambda x: x[bt.TABSETUP_COLUMNNAME] == name)
            if hasattr(c, 'SetMaxLength'):
                c.SetMaxLength(t[n][bt.TABSETUP_COLUMNLENGTH])
        for i in ['CodiceFiscaleEntryCtrl' ,
                  'FileEntryCtrl' ,
                  'FolderEntryCtrl' ,
                  'FullPathFileEntryCtrl' ,
                  'HttpEntryCtrl' ,
                  'MailEntryCtrl' ,
                  'PartitaIvaEntryCtrl' ,
                  'PhoneEntryCtrl']:
            if isinstance(c, getattr(awc.controls.entries, i )):
                c.GetChildren()[0].Bind(wx.EVT_TEXT, self._grid.OnGridChanged)
        if isinstance(c, wx.TextCtrl):
            self.Bind(wx.EVT_TEXT, self._grid.OnGridChanged, c)
        elif isinstance(c, awc.controls.datectrl.DateCtrl):
            self.Bind(EVT_DATECHANGED, self._grid.OnGridChanged, c)
        elif isinstance(c, wx.CheckBox):
            self.Bind(wx.EVT_CHECKBOX, self._grid.OnGridChanged, c)
        elif isinstance(c, awc.controls.linktable.LinkTable):
            self.Bind(EVT_LINKTABCHANGED, self._grid.OnGridChanged, c)

    def GetDataStructure(self):
        controls=[]
        for n in self._grid.fields:
            c=GetNamedChildrens(self, '%s_%s' % (self.gridTableName, n))
            if c:
                controls.append(c[0])
        self.db_datalink += [ ( ctr.GetName(), ctr ) for ctr in controls ]
        self.db_datacols = [ col for col,ctr in self.db_datalink ]

    def GetPanelGrid(self):
        cn = self.FindWindowByName
        panelGrid = cn('%s_panelgrid' % self.gridTableName )
        if not panelGrid:
            aw.awu.MsgDialog(self, 'Attenzione!\nIl panel contenente la griglia relativa a %s deve obbligatoriamente avere none %s_panelgrid.' % ( self.gridTableName, self.gridTableName), caption="ERRORE PROGRAMMAZIONE", style=wx.ICON_ERROR)
        return panelGrid

    def BindStdButton(self):
        cn = self.FindWindowByName
        for name, func in (('%s_butnew' % self.gridTableName, self._grid.OnCreate),
                           ('%s_butdel' % self.gridTableName, self._grid.OnDelete),
                           ('%s_butlst' % self.gridTableName, self._grid.OnPrint),):
            obj=cn(name)
            try:
                obj.Bind(wx.EVT_BUTTON, func)
            except:
                aw.awu.MsgDialog(self, "Attenzione!\nNon e' stato definito il controllo %s." % name, caption="ERRORE PROGRAMMAZIONE", style=wx.ICON_ERROR)
        self.BindAddButton()

    def BindAddButton(self):
        pass

    def BindInputControl(self):
        self.GetDataStructure()
        for col, ctr in self.db_datalink:
            if isinstance(ctr, wx.Window):
                self.BindChangedEvent(ctr)

    def BindControl(self):
        self.BindInputControl()
        self.BindStdButton()

    def DeleteDataRecord( self, recid ):
        try:
            cmdDel = """DELETE FROM %s WHERE id_pdc=%%s""" % self.gridTableName
            self.db_curs.execute(cmdDel, recid)
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        except Exception, e:
            MsgDialogDbError(self, e)








