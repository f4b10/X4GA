#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/attachments.py
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


import sys, os, subprocess
def opj(x,y):
    return os.path.join(x,y).replace('\\', '/')

import wx
import wx.lib.colourdb as colourdb
import stormdb as adb

import awc.controls.attachbutton_wdr as wdr
import awc.util as awu
import awc.controls.dbgrid as dbg

#import twain
twain = None

from mx import DateTime

import locale
try:
    locale.setlocale(locale.LC_ALL, 'it')
except locale.Error:
    locale.setlocale(locale.LC_ALL)

import shutil

import awc.controls.images as images

import awc.thumbs as thumbs
import base64

_colorsok = False

attach_dir = './attach_files'
FILES_PER_DIR = 1024


ATTACH_TYPE_FILE =  1
ATTACH_TYPE_TWAIN = 2
ATTACH_TYPE_URL =   3
ATTACH_TYPE_VOICE = 4
ATTACH_TYPE_NOTE =  5


PAGE_NOTES = 0
PAGE_FILE = 1
PAGE_TWAIN = -1
PAGE_URL = 2
PAGE_VOICE = -1


ATTACH_SIZEMAX = 1024*1024*16 #in bytes => 16 MB

if sys.platform.startswith('linux'):
    TEMP_DIR = '/tmp'
else:
    TEMP_DIR = os.getenv('temp')

TWAIN_TEMPFILE = opj(TEMP_DIR, "x4scan.bmp")

VOICE_MAXLEN =   60 #seconds
VOICE_TEMPFILE = opj(TEMP_DIR, "x4voice.mp3")
TEXT_TEMPFILE =  opj(TEMP_DIR, "x4text.txt")


__image_ext__ = ('bmp', 'jpg', 'jpeg', 'tif', 'tiff', 'gif')
__sound_ext__ = ('mp3', 'wav')

#__voicerec__ = True
#try:
#    import time, sys
#    import pymedia.audio.sound as sound
#    import pymedia.audio.acodec as acodec
#except ImportError:
#    __voicerec__ = False
#
#__voiceplay__ = True
#try:
#    import pymedia.audio.sound as sound
#    import pymedia.audio.acodec as acodec
#    import pymedia.muxer as muxer
#    if len(sound.getODevices()) == 0:
#        __voiceplay__ = False
#except:
#    __voiceplay__ = False


_evtATTACHSMODIFIED = wx.NewEventType()
EVT_ATTACHSMODIFIED = wx.PyEventBinder(_evtATTACHSMODIFIED, 1)
class AttachsModifiedEvent(wx.PyCommandEvent):
    pass


class _AttachTableMixin(adb.DbTable):
    
    def GetLastFolderNumber(self):
        last = 1
        if not os.path.exists(attach_dir):
            os.mkdir(attach_dir)
        dirs = [f for f in os.listdir(attach_dir) if os.path.isdir(f)]
        if dirs:
            dirs.sort()
            last = dirs[-1]
            last = last.replace('\\', '/')
            last = int(last.split('/')[-1])
        return last
    
    def GetNewFilePathAndName(self):
        path_number = self.GetLastFolderNumber()
        while True:
            path = self.GetFolderName(path_number)
            if not os.path.exists(path):
                os.mkdir(path)
            if len(os.listdir(path)) < FILES_PER_DIR:
                break
            path_number += 1
        now = DateTime.now()
        def f(x,n=2):
            return str(int(x)).zfill(n)
        file_name = '%s-%s-%s %s-%s-%s' % (f(now.year,4),
                                           f(now.month),
                                           f(now.day),
                                           f(now.hour),
                                           f(now.minute),
                                           f(now.second))
        return path_number, file_name
    
    def IsImage(self):
        if self.attach_type == ATTACH_TYPE_TWAIN:
            out = True
        elif self.attach_type == ATTACH_TYPE_FILE:
            out = (self.file or '').split('.')[-1].lower() in thumbs.IMAGE_EXTENSIONS
        else:
            out = False
        return out
    
    def IsNote(self):
        return self.attach_type == ATTACH_TYPE_NOTE
    
    def IsURL(self):
        return self.attach_type == ATTACH_TYPE_URL
    
    def IsVoice(self):
        return self.attach_type == ATTACH_TYPE_VOICE
    
    def IsTwain(self):
        return self.attach_type == ATTACH_TYPE_TWAIN
    
    def IsDocument(self):
        return self.attach_type == ATTACH_TYPE_FILE
    
    def GetFolderName(self, n=None):
        if n is None:
            n = self.folderno
        return opj(attach_dir, str(n).zfill(3))
    
    def GetFileName(self):
        return opj(self.GetFolderName(), self.file)
        
    def GetDefaultImageName(self):
        for a in self:
            if a.IsImage() and a.autotext:
                return self.GetFileName()
    
    def GetBase64EncodedImage(self, image=None):
        out = ''
        if not self.IsEmpty():
            if image is None:
                fn = self.GetFileName()
                if fn:
                    if os.path.exists(fn):
                        try:
                            f = open(self.GetFileName(), 'rb')
                            image = f.read()
                            f.close()
                        except Exception:
                            pass
            if image is not None:
                out = base64.b64encode(image)
        return out
    
    def GetBase64EncodedResizedImage(self, dimx, dimy, scale_test_func=None, force_jpeg=False):
        out = None
        if not self.IsEmpty():
            fn = self.GetFileName()
            if fn:
                if os.path.exists(fn):
                    try:
                        client_size = (dimx, dimy)
                        image = wx.Image(fn)
                        if callable(scale_test_func):
                            do = scale_test_func(image)
#                            if not do:
#                                out = self.GetBase64EncodedImage()
                        else:
                            do = True
                        if do:
                            image_size = image.GetSize()
                            proportions = (float(client_size[i]) / image_size[i]
                                           for i in range(len(image_size)))
                            proportion = min(proportions) # Use the smallest proportion.
                            # Can't use wx.Image.Shrink because it doesn't provide enough pixel
                            # granularity -- the shrinking has serious discontinuities.
                            new_size = (pixels * proportion for pixels in image_size)
                            image.Rescale(*new_size)
                        if do or force_jpeg:
                            import tempfile
                            tmpfile = tempfile.NamedTemporaryFile(suffix='.temp')
                            tmpname = tmpfile.name
                            tmpfile.close()
                            app = wx.GetApp()
                            if hasattr(app, 'AppendTempFile'):
                                wx.GetApp().AppendTempFile(tmpname)
                            image.SaveFile(tmpname, wx.BITMAP_TYPE_JPEG)
                            f = open(tmpname, 'rb')
                            buf = f.read()
                            f.close()
                            out = self.GetBase64EncodedImage(buf)
                    except Exception, e:
                        pass
        return out


# ------------------------------------------------------------------------------


class AttachTableMemo(_AttachTableMixin):
    
    def __init__(self, tabname, *args):
        _AttachTableMixin.__init__(self, tabname, 'allegati', writable=True,
                                   defaults={'attach_type': 1, 'hidden': 0})
        self.AddField('NULL', 'filecontent')
        self.AddFilter("FALSE")


# ------------------------------------------------------------------------------


class AttachTableList(_AttachTableMixin):
    
    def __init__(self, tabname, *args):
        mix = _AttachTableMixin
        mix.__init__(self, tabname, 'allegati', writable=False,\
                     fields="id,attscope,attkey,description,attach_type,"\
                     +"folderno,file,url,voiceatt_id,autotext,hidden")
        self.AddOrder("attach_type")
        self.AddOrder("datins")
        self.AddOrder("description")


# ------------------------------------------------------------------------------


class AttachmentButton(wx.Button):
    """
    Classe per la gestione degli allegati.
    
    Da qui è possibile inserire, modificare, eliminare e richiamare allegati di
    vario tipo.
    
    Gli allegati sono memorizzati sulla tabella 'allegati' e sono
    contestualizzati mediante i seguenti identificativi:
        - attscope    (char,10) Tipicamente il nome tabella a cui si riferiscono
        - attkey      (integer) Tipicamente l'id del record a cui si riferiscono
    
    A corredo di ogni allegato troviamo:
        - description (varchar,255) Descrizione dell'allegato
        - name        (varchar,255) Nome del documento o indirizzo url
        - content     (blob)        Contenuto dell'allegato
        - attach_type (integer)     Tipologia di allegato:
          1 = Documento
          2 = Immagine
          3 = URL
          4 = Nota vocale
          5 = Nota 
    
    Ad esempio, per allegare un documento alla scheda anagrafica di un cliente,
    pesupposto che il nome della tabella clienti sia 'clienti', avremo:
        attscope    = clienti (nome della tabella clienti)
        attkey      = 1234    (id del cliente nella tabella clienti)
        description = Condizioni contrattuali
        attach_type = 1 (documento)
        content     = <binary> - contenuto del file di Word.
    """

    def __init__(self, *args, **kwargs):
        
        wx.Button.__init__(self, *args, **kwargs)
        
        self._tabname = "allegati"
        self._attscope = None
        self._attkey = None
        self._canadd = True
        self._canedit = True
        self._autotext = None
        
        self._autotext_prefix = None
        self._autotext_suffix = None
        
        self._twain_sm = None
        self._twain_sd = None
        
        self._voice_playnow = True
        
        self.image_files = []
        
        self._spypanel = None
        self._autoscan = None
        
        #_attlist contiene le informazioni degli allegati senza il campo blob
        #che appesantisce la ricerca; è *sempre* allineato con il contenuto
        #della tabella allegati, anche dopo averne inserito di nuovi, la cui
        #scrittura sulla tabella è differita rispetto al loro inserimento nel
        #bottone - questo ne consente l'inserimento anche quando l'elemento a 
        #cui si riferiscono non ha ancora un proprio id.
        #ATTENZIONE
        #per la memorizzazione di nuovi allegati è necessario richiamare
        #l'apposito metodo Save - vedi specifiche
        self._attlist = AttachTableList(self._tabname)
        
        #_attmemo contiene *tutte* le informazioni dei soli allegati che si 
        #stanno inserendo - vedi considerazioni precedenti
        #ATTENZIONE
        #per la memorizzazione di nuovi allegati è necessario richiamare
        #l'apposito metodo Save - vedi specifiche
        self._attmemo = AttachTableMemo(self._tabname)
        
        self.Bind(wx.EVT_BUTTON, self._OnCallAttachMenu)
    
    def SetSpyPanel(self, panel):
        assert isinstance(panel, AttachmentSpyPanel)
        self._spypanel = panel
    
    def SetAutoScan(self, autoscan=True):
        self._autoscan = autoscan
    
    def GetDefaultImageName(self):
        return self._attlist.GetDefaultImageName()
    
    def SetAutoText(self, at):
        self._autotext = at
    
    def SetScope(self, scope):
        """
        Imposta lo 'scope' degli allegati, ovvero l'ambito nel quale la chiave
        a cui si riferiscono ha significato; tipicamente è il nome della 
        tabella sulla quale risiede il record a cui si riferiscono gli allegati.
        """
        self._attscope = scope
    
    def SetAutotextPS(self, prefix=None, suffix=None):
        self._autotext_prefix = prefix
        self._autotext_suffix = suffix
    
    def SetKey(self, key, save=False, delete=False):
        """
        Imposta la chiave numerica di relazione degli allegati; tipicamente è
        l'id del record della tabella indicata nello 'scope' (vedi SetScope)
        a cui si riferiscono gli allegati.
        """
        self._attkey = key
        if save:
            self.SaveAttachments()
        self._attmemo.Retrieve()
        if delete:
            self.DeleteAttachments()
        self.UpdateElements()
        self.UpdateButtonStatus()
    
    def SetPermissions(self, caninsert=True, canedit=True):
        """
        Imposta i diritti di inserimento e modifica degli allegati:
        SetPermissions(self, caninsert=True, canedit=True)
        """
        self._canadd = caninsert
        self._canedit = canedit
    
    def UpdateElements(self):
        """
        Aggiorna l'elenco degli allegati per la costruzione del menu alla
        pressione del bottone.
        """
        db = self._attlist
        db.ClearFilters()
        db.AddFilter("allegati.attscope=%s", self._attscope)
        db.AddFilter("allegati.attkey=%s", self._attkey)
        #db.AddFilter("allegati.datdel IS NULL")
        db.AddFilter("hidden<>1")        
        if db.Retrieve():
            sp = self._spypanel
            if sp is not None:
                sp.SetEmpty()
            at = self._autotext
            txt = ''
            for att in db:
                if sp is not None and att.IsImage() and att.autotext:
                    sp.SetFull()
                elif att.IsNote() and att.autotext and self._autotext:
                    file = att.GetFileName()
                    try:
                        h = open(file, 'r')
                        c = h.read()
                        h.close()
                        if txt:
                            txt += ' - '
                        txt += c
                    except:
                        pass
            if at is not None:
                text, sep = '', ' :: '
                if self._autotext_prefix:
                    text += self._autotext_prefix
                    if txt:
                        text += sep
                text += txt
                if self._autotext_suffix:
                    if txt:
                        text += sep
                    text += self._autotext_suffix
                at.SetText(text)
            n = db.RowsCount()
        else:
            n = 0
        font = self.GetFont()
        if n > 0:
            if n == 1:
                txt = "1 allegato"
            else:
                txt = "%d allegati" % n
            font.SetWeight(wx.FONTWEIGHT_BOLD)
        else:
            txt = "No allegati"
            font.SetWeight(wx.FONTWEIGHT_NORMAL)
        #self.Enable(n>0)
        self.SetFont(font)
        self.SetLabel(txt)
    
    def GetAutoNotes(self, db):
        txt = ''
        for att in db:
            if att.IsNote() and att.autotext:
                file = att.GetFileName()
                try:
                    h = open(file, 'r')
                    c = h.read()
                    h.close()
                    if txt:
                        txt += ' - '
                    txt += c
                except:
                    pass
        return txt
    
    def StoreNewAttach(self, att):
        out = True
        if att.filecontent:
            n, f = att.GetNewFilePathAndName()
            att.folderno = n
            path = att.GetFolderName()
            if not os.path.isdir(path):
                try:
                    os.mkdir(path)
                except:
                    out = False
            if att.file is None:
                ext = '.'
            else:
                ext = att.file
            filename = opj(path, '%s%s' % (f, ext))
            att.file = filename.split('/')[-1]
            att.size = len(att.filecontent)
            try:
                h = open(filename, 'wb')
                h.write(att.filecontent)
                h.close()
            except Exception, e:
                awu.MsgDialog(self, repr(e.args))
                out = False
        return out
    
    def LaunchAttachment(self, attid, saveonly=False):
        """
        Lancia l'allegato.
        """
        am = AttachTableList(self._tabname)
        if am.Get(attid) and am.OneRow():
            if   am.IsURL():
                if am.url:
                    try:
                        url = am.url
                        if not url.startswith('http://') and not url.startswith('https://'):
                            url = 'http://%s' % url
                        os.startfile(url)
                    except:
                        pass
                return
            file = am.GetFileName()
            if not saveonly:
                if am.IsVoice():
                    if am.hidden:
                        t = "Commento audio"
                    else:
                        t = am.description
                    self.CallVoicePlayer(file, start=self._voice_playnow,\
                                         title=t)
                else:
                    if not os.path.exists(file):
                        awu.MsgDialog(self, "File non trovato",
                                      style=wx.ICON_ERROR)
                        return
                    try:
                        os.startfile(file.replace('/','\\'))
                        if am.voiceatt_id is not None:
                            self._voice_playnow = False
                            self.LaunchAttachment(am.voiceatt_id)
                            self._voice_playnow = True
                        
                    except Exception, e:
                        if awu.MsgDialog(self,\
                                         """Impossibile aprire il file %s.\n"""\
                                         """Vuoi salvarlo?""" % file,\
                                         "Apertura allegato fallita",\
                                         style=wx.ICON_ERROR|\
                                         wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                            saveonly = True
                        
                    except Exception, e:
                        awu.MsgDialog(self, repr(e.args))
            if saveonly:
                self.SaveAttachFileAs(file)
    
    def SaveAttachFileAs(self, tmp):
        out = False
        if '.' in tmp:
            ext = tmp[tmp.rindex(".")+1:]
            extinfo = "Tutti i files %s (*.%s)|*.%s" % (ext, ext, ext)
        else:
            ext = "*"
            extinfo = "Tutti i files (*.*)|*.*"
        file = tmp.replace("\\","/")
        if "/" in file:
            file = file[file.rindex("/")+1:]
        dlg = wx.FileDialog(None,\
                            message="Seleziona il file da salvare",\
                            defaultFile=file,\
                            wildcard=extinfo,\
                            style=wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                shutil.copyfile(tmp, dlg.GetPath())
                out = True
            except Exception, e:
                awu.MsgDialog(self,\
                              """Impossibile scrivere su questo file\n"""\
                              """Errore: %s""" % repr(e.args))
        dlg.Destroy()
        return out

    def UpdateButtonStatus(self):
        global _colorsok
        if not _colorsok:
            colourdb.updateColourDB()
            _colorsok = True
        if self._attmemo.RowsCount() > 0:
            bg = wx.TheColourDatabase.Find("LIGHT CORAL")
        else:
            bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE)
        self.SetBackgroundColour(bg)
    
    def ManageAttachments(self):
        dlg = AttachmentsGridDialog(self, -1, "Manutenzione allegati",\
                                    style=wx.DEFAULT_FRAME_STYLE\
                                    |wx.RESIZE_BORDER)
        if dlg.ShowModal() == 1:
            self.UpdateElements()
        dlg.Destroy()
    
    def MakeNewAttach(self, toscan=False):
        
        am = self._attmemo
        attno = am.RowsCount()
        am.CreateNewRow()
        am.autotext = 0
        dlg = AttachmentDetailsDialog(self, -1, "Inserimento nuovo allegato")
        dlg._twain_sm = self._twain_sm
        dlg._twain_sd = self._twain_sd
        force_autotext = 0
#        if toscan:
#            def cn(x):
#                return dlg.FindWindowByName(x)
#            cn('description').SetValue("Scansione Documento")
#            dlg.notebook.SetSelection(2)
#            force_autotext = 1
        
        am.attach_type = dlg.ShowModal()
        
        if am.attach_type >= ATTACH_TYPE_FILE:
            
            am.attscope =    self._attscope
            am.attkey =      self._attkey
            am.description = dlg.GetFieldValue('description')
            am.datins =      DateTime.now()
            
            if am.IsTwain():
                am.file = dlg._file
            
            file = None
            if am.IsDocument():
                file = dlg.GetFieldValue('file')
            elif am.IsTwain():
                file = dlg._file
            if file is not None:
                file = file.replace('\\','/')
                if "/" in file:
                    file = file.split('/')[-1]
                if not '.' in file:
                    file += '.'
                file = file.split('.')[-1]
                am.file = '.%s'%file
            
            if am.IsImage() or am.IsNote():
                am.autotext = int(dlg._autotext or force_autotext)
            
            if am.IsURL():
                am.url = dlg.GetFieldValue('url')
                
            elif am.IsNote():
                am.file = '.txt'
            
            if dlg._stream:
                if am.IsDocument():
                    if am.IsImage():
                        am.attach_type = ATTACH_TYPE_TWAIN
                am.filecontent = dlg._stream
            
            self.UpdateButtonStatus()
            event = AttachsModifiedEvent(_evtATTACHSMODIFIED, self.GetId())
            event.SetEventObject(self)
            event.m_id = self.GetId()
            event.SetId(event.m_id)
            self.GetParent().AddPendingEvent(event)
        
        dlg.Destroy()
    
    def SaveAttachments(self):
        out = True
        am = self._attmemo
        if am.RowsCount() > 0:
            if self._attkey is None:
                if am.RowsCount() == 1:
                    desc = "l'allegato inserito"
                else:
                    desc = "i %d allegati inseriti" % am.RowsCount()
                awu.MsgDialog(self,\
                              """Non è possibile memorizzare %s in quanto """\
                              """manca l'identificativo a cui riferirli""",\
                              style=wx.ICON_ERROR)
                out = False
            else:
                for a in am:
                    a.attkey = self._attkey
                    self.StoreNewAttach(am)
                out = am.Save()
                if not out:
                    awu.MsgDialog(self,\
                                  """Problema durante il salvataggio """\
                                  """degli allegati inseriti\nErrore: %s"""\
                                  % repr(am.GetError()))
                self.UpdateElements()
                am.Retrieve()
        self.UpdateButtonStatus()
        return out
    
    def DeleteAttachments(self):
        out = True
        al = self._attlist
        if al.RowsCount() > 0:
            rows = [(a.id, a.folderno, a.file) for a in al if a.id is not None]
            db = al._info.db
            filerr = []
            for di, dn, df in rows:
                db.Execute("DELETE FROM %s WHERE id=%d" % (self._tabname, di))
                path = al.GetFolderName(dn)
                file = opj(path, df)
                try:
                    os.remove(file)
                except Exception, e:
                    filerr.append(file[:100])
            if filerr:
                awu.MsgDialog(self, 
                              """I seguenti files non sono stati """\
                              """cancellati del file.\n%s"""\
                              % repr(e.args))
        return out
    
    def ChangesPending(self):
        return self._attmemo.RowsCount() > 0
    
    def CallVoicePlayer(self, fn, start=True, title="Riproduzione nota vocale"):
        parent = self
        if not self._voice_playnow:
            parent = None
        s = wx.DEFAULT_DIALOG_STYLE
        if not start: s |= wx.STAY_ON_TOP
        dlg = wdr.VoicePlayerDialog(parent, -1, title, size=(300,60),\
                                    style=s)
        #dlg.FindWindowByName('voice_record').Enable(False)
        dlg.CenterOnScreen()
        player = VoicePlayer(dlg)
        player.SetFileName(fn)
        dlg.Show()
        wx.SafeYield(onlyIfNeeded=True)
        if start:
            player.VoicePlay(fn)
        else:
            try:
                h = open(fn, 'rb')
                s = h.read()
                h.close()
                player._stream = s
            except:
                player._stream = None
            player.UpdateVoice()
    
    # callbacks gestione eventi ------------------------------------------------
    
    def _OnLaunchAttachment(self, event):
        n = event.GetId()
        self._attlist.MoveRow(n)
        self.LaunchAttachment(self._attlist.id)
    
    def _OnCallAttachMenu(self, event):
        
        def AddSubMenu(mainmenu, submenu, att_type, att_num):
            if   att_type == ATTACH_TYPE_FILE:
                desc = "Documenti (%d)" % att_num
            elif att_type == ATTACH_TYPE_TWAIN:
                desc = "Immagini (%d)" % att_num
            elif att_type == ATTACH_TYPE_URL:
                desc = "Pagine Web (%d)" % att_num
            elif att_type == ATTACH_TYPE_VOICE:
                desc = "Note vocali (%d)" % att_num
            elif att_type == ATTACH_TYPE_NOTE:
                desc = "Note (%d)" % att_num
            else:
                desc = "tipo %d sconosciuto" % att_type
            mainmenu.AppendMenu(-1, desc, submenu)
        
        mnuId = 0
        last_type = -1
        tot_type = 0
        submenu = None
        menu = wx.Menu()
        del self.image_files[:]
        autoimg = False
        
        for mnuId, att in enumerate(self._attlist):
            if att.attach_type != last_type:
                if submenu is not None:
                    AddSubMenu(menu, submenu, last_type, tot_type)
                submenu = wx.Menu()
                last_type = att.attach_type
                tot_type = 0
            desc = att.description
            if att.url:
                if desc != att.url:
                    desc += " (%s)" % att.url
            elif att.file and att.attach_type == ATTACH_TYPE_FILE:#and att.file != "image.bmp":
                desc += " (%s)" % att.file
            if att.voiceatt_id is not None:
                desc += " - con commento audio"
            submenu.Append(mnuId, desc)
            self.Bind(wx.EVT_MENU, self._OnLaunchAttachment, id=mnuId)
            tot_type += 1
            if att.attach_type == ATTACH_TYPE_TWAIN:
                self.image_files.append(att.GetFileName())
                if att.autotext:
                    autoimg = True
        
        if submenu is not None:
            AddSubMenu(menu, submenu, last_type, tot_type)
        
        if len(self.image_files)>0:
            if menu.GetMenuItemCount() > 0:
                menu.AppendSeparator()
            mnuId = wx.NewId()
            menu.Append(mnuId, "Anteprima immagini")
            self.Bind(wx.EVT_MENU, self._OnPreviewImages, id=mnuId)
        
        if self._attmemo.RowsCount() > 0:
            if menu.GetMenuItemCount() > 0:
                menu.AppendSeparator()
            mnuId = wx.NewId()
            if self._attkey is None:
                if self._attmemo.RowsCount() == 1:
                    desc = "un allegato"
                else:
                    desc = "%d allegati" % self._attmemo.RowsCount()
                menu.Append(mnuId, "(%s ancora da memorizzare)" % desc)
                def _DoNothing(*args, **kwargs): pass
                self.Bind(wx.EVT_MENU, _DoNothing, id=mnuId)
            else:
                if self._attmemo.RowsCount() == 1:
                    desc = "un allegato inserito"
                else:
                    desc = "%d allegati inseriti" % self._attmemo.RowsCount()
                menu.Append(mnuId, "%s - memorizza ora" % desc)
                self.Bind(wx.EVT_MENU, self._OnSaveAttachments, id=mnuId)
        
        if self._canedit and menu.GetMenuItemCount() > 0:
            menu.AppendSeparator()
            mnuId = wx.NewId()
            menu.Append(mnuId, "Manutenzione")
            self.Bind(wx.EVT_MENU, self._OnManageAttachs, id=mnuId)
        
        if self._canadd:
            if menu.GetMenuItemCount() > 0:
                menu.AppendSeparator()
            mnuId = wx.NewId()
            menu.Append(mnuId, "Aggiungi nuovo allegato")
            self.Bind(wx.EVT_MENU, self._OnCallNewAttach, id=mnuId)
            if (self._spypanel or self._autoscan) and not autoimg:
                mnuId = wx.NewId()
                menu.Append(mnuId, "Aggiungi scansione documento")
                self.Bind(wx.EVT_MENU, self._OnCallDocumentScan, id=mnuId)
        
        xo, yo = self.GetPosition()
        self.PopupMenu(menu, (0,0))
        menu.Destroy()
        event.Skip()
    
    def _OnCallDocumentScan(self, event):
        self.MakeNewAttach(toscan=True)
        event.Skip()
    
    def _OnPreviewImages(self, event):
        wait = awu.WaitDialog(self, message="Creazione anteprime in corso...",
                              maximum=len(self.image_files), 
                              style=wx.ICON_INFORMATION)
        dlg = thumbs.ThumbsDialog(self, thumb_size=160, 
                                  style=wx.DEFAULT_FRAME_STYLE)
        try:
            dlg.PopulateFromFilesList(self.image_files, 
                                      func=lambda n: wait.SetValue(n))
        finally:
            wait.Destroy()
        dlg.SetSize((800, 600))
        dlg.CenterOnScreen()
        dlg.ShowModal()
        dlg.Destroy()
    
    def _OnCallNewAttach(self, event):
        if self._canadd:
            self.MakeNewAttach()
    
    def _OnSaveAttachments(self, event):
        self.SaveAttachments()
    
    def _OnManageAttachs(self, event):
        if self._canedit:
            self.ManageAttachments()
    

# ------------------------------------------------------------------------------


def s2h(sec):
    h = int(sec/3600)
    sec -= h*3600
    m = int(sec/60)
    sec -= m*60
    s = int(sec)
    if   h: out = '%s:%s:%s' % (h, str(m).zfill(2), str(s).zfill(2))
    elif m: out =    '%s:%s' % (                 m, str(s).zfill(2))
    else:   out =       '%s' % s
    return out


# ------------------------------------------------------------------------------


class VoicePlayer:
    
    filename = None
    
    def __init__(self, parent):
        if parent is None: parent = self
        self.parent = parent
        self._voice_pos = 0
        self._voice_rec = False
        self._voice_play = False
        self._voice_canrec = False
        self._stream = None
        cn = lambda name: self.parent.FindWindowByName(name)
        for evt, func, control in (\
            (wx.EVT_BUTTON,   self._OnVoiceRecord, cn('voice_record')),\
            (wx.EVT_BUTTON,   self._OnVoicePlay,   cn('voice_play')),\
            (wx.EVT_BUTTON,   self._OnVoiceStop,   cn('voice_stop'))):
            self.parent.Bind(evt, func, control)
        self.parent.Bind(wx.EVT_BUTTON, self._OnVoiceStop)
        self.UpdateVoice()
    
    def SetFileName(self, fn):
        self.filename = fn
    
    def Unlock(self):
        self._voice_canrec = True
        self.UpdateVoice()
    
    def UpdateVoice(self, secs=0, progress=0):
        cn = lambda name: self.parent.FindWindowByName(name)
        cn('voice_position').SetLabel(s2h(secs))
        cn('voice_play').Enable(self._stream is not None\
                                and len(self._stream)>0\
                                and not self._voice_play\
                                and not self._voice_rec)
        cn('voice_record').Enable(self._voice_canrec\
                                  and not self._voice_rec\
                                  and not self._voice_play)
        cn('voice_stop').Enable(self._voice_play or self._voice_rec)
        cn('voice_progress').SetValue(progress)
    
    def VoiceRecord(self):
        secs = VOICE_MAXLEN
        cn = lambda name: self.parent.FindWindowByName(name)
        cn('voice_progress').SetRange(secs*1000)
        cparams= { 'id':          acodec.getCodecID('mp3'),
                   'bitrate':     128000,
                   'sample_rate':  44100,
                   'channels':         2 } 
        #card = periferica di registrazione
        #TODO: setup periferica registrazione in modo da poterla scegliere se
        #ce ne sono presenti + di una.  Per ora viene considerata la prima
        #periferica con + di un canale: sul PC di sviluppo, in presenza di
        #periferica di registrazione legata al modem (con un solo canale),
        #sound.Input(...) si pianta
        card = -1
        snds = sound.getIDevices()
        for n, dev in enumerate(snds):
            if dev['channels']>1:
                card = n
                break
        if card<0:
            awu.MsgDialog(None, message="Nessuna periferica di registrazione audio")
            return
        fn = VOICE_TEMPFILE
        f = open(fn, 'wb' )
        ac = acodec.Encoder( cparams )
        snd = sound.Input(44100, 2, sound.AFMT_S16_LE, card)
        snd.start()
        pp = 0
        self._voice_play = False
        self._voice_rec = True
        while self._voice_rec:
            pos = snd.getPosition()
            if pos > secs:
                break
            s = snd.getData()
            if s and len(s):
                for fr in ac.encode(s): f.write(fr)
            else:
                time.sleep(.003)
            self.UpdateVoice(pos, pos*1000)
            wx.SafeYield(onlyIfNeeded=True)
        snd.stop()
        self._voice_rec = False
        f.close()
        f = open(fn, 'rb')
        self._stream = f.read()
        f.close()
        self.VoicePlay(fn)
    
    def VoicePlay(self, name):
        cn = lambda name: self.parent.FindWindowByName(name)
        dm = muxer.Demuxer(str.split(name, '.')[-1].lower())
        f = open( name, 'rb' )
        self._stream = f.read()
        f.seek(0,0)
        cn('voice_progress').SetRange(len(self._stream))
        snd = resampler = dec = None
        self._voice_rec = False
        self._voice_play = True
        ##card = 0
        #card = periferica di riproduzione
        #TODO: setup periferica riproduzione in modo da poterla scegliere se
        #ce ne sono presenti + di una.  Per ora viene considerata la prima
        #periferica con + di un canale: sul PC di sviluppo, in presenza di
        #periferica di riproduzione legata al modem (con un solo canale) va
        #in tutto in crash
        card = -1
        snds = sound.getODevices()
        for n, dev in enumerate(snds):
            if dev['channels']>1:
                card = n
                break
        if card<0:
            self._voice_play = False
        rate = 1
        s = f.read(32000)
        #t = 0
        #EMULATE = 0
        pp = 0#len(s)
        pos = 0
        while len(s) and self._voice_play:
            frames = dm.parse(s)
            if frames:
                for fr in frames:
                    if dec == None:
                        #print dm.getInfo(), dm.streams
                        dec= acodec.Decoder( dm.streams[ fr[ 0 ] ] )
                    r = dec.decode(fr[1])
                    if r and r.data:
                        if snd == None:
                            #print 'Opening sound with %d channels -> %s' % ( r.channels, snds[ card ][ 'name' ] )
                            snd = sound.Output(int(r.sample_rate*rate), r.channels, sound.AFMT_S16_LE, card)
                            if rate <> 1:
                                resampler = sound.Resampler((r.sample_rate,r.channels), (int(r.sample_rate/rate),r.channels))
                                #print 'Sound resampling %d->%d' % ( r.sample_rate, r.sample_rate/rate )
                        data = r.data
                        if resampler:
                            data = resampler.resample(data)
                        #if EMULATE:
                            #d = len(data)/float(r.sample_rate*r.channels*2)
                            #time.sleep(d)
                            ##if int(t+d)!= int(t):
                                ##print 'playing: %d sec\r' % ( t+d ),
                            #t += d
                        #else:
                            #snd.play( data )
                        snd.play(data)
                        pos = snd.getPosition()
            
            pp += len(s)
            self.UpdateVoice(pos, pp)
            wx.SafeYield(onlyIfNeeded=True)
            
            s = f.read(512)
        
        try:
            while snd.isPlaying():
                time.sleep(.05)
        except:
            pass
        
        self._voice_play = False
        
        c = cn('attach_voice')
        if c:
            c.Enable(self._stream is not None and len(self._stream) > 0)
        
        self.UpdateVoice()
        cn('voice_play').Enable()
        wx.SafeYield(onlyIfNeeded=True)
    
    # callbacks gestione eventi ------------------------------------------------
    
    def _OnVoiceRecord(self, event):
        self.VoiceRecord()
        event.Skip()
    
    def _OnVoicePlay(self, event):
        if self.filename:
            fn = self.filename
        else:
            fn = VOICE_TEMPFILE
        self.VoicePlay(fn)
        event.Skip()
    
    def _OnVoiceStop(self, event):
        self._voice_play = False
        self._voice_rec = False
        event.Skip()


# ------------------------------------------------------------------------------


class AttachmentDetailsDialog(wx.Dialog, VoicePlayer):
    """
    Dialog per l'inserimento/modifica di un allegato.
    Al momento è previsto solo l'inserimento; per la cancellazione vedi la
    classe per la manutenzione AttachmentsGridDialog.
    """
    def __init__(self, *args, **kwargs):
        """
        Costruttore dialog standard.
        """
        
        wx.Dialog.__init__(self, *args, **kwargs)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        self._attachtype = 1
        self._stream = None
        self._file = None
        self._twain_sm = None
        self._twain_sd = None
        self._autotext = False
        
        wdr.AttachButtonDetailsFunc(self)
        self.TestPage()
        
        il = wx.ImageList(16, 16)
        i = []
        i.append(il.Add(images.getText16Bitmap()))
        i.append(il.Add(images.getImage16Bitmap()))
#        i.append(il.Add(images.getScanner16Bitmap()))
        i.append(il.Add(images.getWeb16Bitmap()))
#        i.append(il.Add(images.getAudio16Bitmap()))
        nb = self.FindWindowById(wdr.ID_ATTACH_SPECS)
        nb.AssignImageList(il)
        for n, i in enumerate(i):
            nb.SetPageImage(n, i)
        self.notebook = nb
        
        for evt, func, control in (\
            (wx.EVT_BUTTON,   self._OnAttachNote,  cn('attach_note')),\
            (wx.EVT_BUTTON,   self._OnAttachFile,  cn('attach_file')),\
            (wx.EVT_BUTTON,   self._OnSearchFile,  cn('search_file')),\
            (wx.EVT_TEXT,     self._OnFileChanged, cn('file')),\
#            (wx.EVT_BUTTON,   self._OnAttachUrl,   cn('attach_url')),\
#            (wx.EVT_BUTTON,   self._OnChangeTwain, cn('change_twain')),\
#            (wx.EVT_BUTTON,   self._OnAttachTwain, cn('attach_twain')),\
#            (wx.EVT_BUTTON,   self._OnAttachVoice, cn('attach_voice')),\
            ):
            self.Bind(evt, func, control)
        
        self.Bind(wx.EVT_TEXT,     self.OnTestNote, cn('note'))
        self.Bind(wx.EVT_CHECKBOX, self.OnTestNote, cn('autotext'))
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._OnPageChanged)
        self.Bind(wx.EVT_CLOSE,  self._OnQuit)
        
#        VoicePlayer.__init__(self, self)
        self._voice_canrec = True
    
    def OnTestNote(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        self._stream = cn('note').GetValue()
        self._autotext = cn('autotext').GetValue()
        self.TestNote()
        event.Skip()
    
    def TestNote(self):
        def cn(x):
            return self.FindWindowByName(x)
        l = len(cn('note').GetValue())
        cn('attach_note').Enable(l>0)
    
    def ProcessData(self, attach_type):
        """
        Esegue la verifica dei dati inseriti; se ok, esce dal dialog modale
        ritornando lo status corrispondente al tipo di allegato inserito.
        Se Twain, provvede a lanciare l'interfaccia di acquisizione e l'uscita
        dal dialog modale avviene alla fine del callback specifico di reazione
        agli eventi dell'interfaccia twain _OnTwainEvent.
        """
        ok = False
        if self.CheckData(attach_type):
            
            if attach_type == ATTACH_TYPE_FILE:
                
                fn = self.GetFieldValue('file')
                try:
                    f = open(fn, 'rb')
                    self._stream = f.read()
                    f.close()
                except IOError, e:
                    awu.MsgDialog(\
                        self,\
                        "Problema in apertura file:\nErrore n.%d - %s"\
                        % (e.args[0], e.args[1]))
                    self.EndModal(0)
                
#                if len(self._stream) > ATTACH_SIZEMAX:
#                    awu.MsgDialog(\
#                        self,\
#                        """L'immagine acquisita pesa %s bytes,\n"""\
#                        """il limite attuale è di %s."""\
#                        % (locale.format("%d", len(self._stream), True),\
#                           locale.format("%d", ATTACH_SIZEMAX, True)),\
#                        style=wx.ICON_WARNING)
#                else:
#                    ok = True
                ok = True
                
            elif attach_type == ATTACH_TYPE_TWAIN:
                self.TwainAcquire()
                
            elif attach_type in (ATTACH_TYPE_VOICE,
                                 ATTACH_TYPE_NOTE):
                if attach_type == ATTACH_TYPE_VOICE:
                    self._voice_rec = False
                    self._voice_play = False
                ok = self._stream is not None and len(self._stream)>0
                
            else:
                ok = True
        
        if ok:
            self.EndModal(attach_type)

    def CheckData(self, attach_type):
        """
        Verifica dati inseriti.
        La descrizione è sempre richiesta e, coerentemente con il tipo di
        allegato selezionato, viene testata l'esistenza di:
            - ATTACH_TYPE_FILE: il nome del file da acquisire
            - ATTACH_TYPE_
        """
        
        err = False
        
        if attach_type in (ATTACH_TYPE_VOICE,
                           ATTACH_TYPE_NOTE):
            err = self._stream is None or len(self._stream) == 0
        
        if not err:
            
            names = ['description']
            if   attach_type == ATTACH_TYPE_FILE:
                names.append('file')
                default = self.GetFieldValue('file')
                if default:
                    default = default.replace('\\', '/')
                    if '/' in default:
                        default = default.split('/')[-1]
                
            elif attach_type == ATTACH_TYPE_URL:
                names.append('url')
                default = (self.GetFieldValue('url') or '')[:50]
                
            elif attach_type == ATTACH_TYPE_VOICE:
                default = 'Commento audio'
                
            elif attach_type == ATTACH_TYPE_NOTE:
                names.append('note')
                default = (self.GetFieldValue('note') or '')[:50]
                
            else:
                default = None
            
            if not self.GetFieldValue('description') and default:
                self.FindWindowByName('description').SetValue(default)
            
            for name in names:
                if not self.GetFieldValue(name):
                    err = True
                    break
        
        if err:
            awu.MsgDialog(self, "Dati non validi", style=wx.ICON_ERROR)
        
        return not err
    
    def GetFieldValue(self, name):
        """
        Ritorna il contenuto di un controllo mediante il suo nome.
        """
        out = None
        ctr = self.FindWindowByName(name)
        if ctr is not None:
            out = ctr.GetValue()
        return out
    
    def ShowModal(self, *args, **kwags):
        """
        Focus su descrizione allegato.
        """
        self.FindWindowByName('description').SetFocus()
        return wx.Dialog.ShowModal(self, *args, **kwags)
    
    def EndModal(self, *args, **kwags):
        """
        Chiude il dialog modale con il codice di ritorno passato, memorizzando
        nel bottone parent AttachmentButton le eventuali 2 istanze delle
        classi di gestione twain, onde evitare la riselezione della periferica
        al successivo inserimento di allegato da sorgente twain.
        """
        b = self.GetParent()
        b._twain_sm = self._twain_sm
        b._twain_sd = self._twain_sd
        return wx.Dialog.EndModal(self, *args, **kwags)
    
    # metodi specifici di gestione periferiche twain ---------------------------
    
    def UpdateTwain(self):
        """
        Apre il pannello di selezione della sorgente twain e ne aggiorna la
        descrizione nel dialog.
        """
        cn = lambda x: self.FindWindowByName(x)
        if self.TwainOpen():
            cn('twain_source').SetValue(self._twain_sd.GetSourceName())
            cn("attach_twain").Enable()
        else:
            cn('twain_source').SetValue("non trovata")
            cn("attach_twain").Enable(False)
    
    def TwainOpen(self):
        """
        Apre il pannello di selezione della sorgente twain
        """
        out = False
        if not self._twain_sm:
            self._twain_sm = twain.SourceManager(self.GetParent().GetHandle())
        if self._twain_sm:
            self._twain_sm.SetCallback(self._OnTwainEvent)
        if not self._twain_sm:
            return
        if self._twain_sd:
            out = True
        else:
            self._twain_sd = self._twain_sm.OpenSource()
            if self._twain_sd:
                out = True
        return out
    
    def TwainAcquire(self):
        """
        Acquisisce l'immagine dalla periferica twain.
        """
        if not self._twain_sd:
            self.TwainOpen()
        if self._twain_sd:
            self._twain_sd.RequestAcquire()
    
    def TwainTransfer(self, event):
        """
        Attiva il trasferimento dell'immagine dalla periferica twain.
        """
        (handle, more_to_come) = self._twain_sd.XferImageNatively()
        bmpfile = TWAIN_TEMPFILE
        twain.DIBToBMFile(handle, bmpfile)
        #bmp = wx.Image(bmpfile, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        #img = wx.StaticBitmap(self, -1, bmp, wx.Point(1,1),
                              #wx.Size(bmp.GetWidth(), bmp.GetHeight()))
        try:
            f = open(bmpfile, 'rb')
            self._stream = f.read()
            self._file = TWAIN_TEMPFILE
            f.close()
        except IOError, e:
            awu.MsgDialog(\
                self,\
                "Problema in apertura file:\nErrore n.%d - %s"\
                % (e.args[0], e.args[1]))
            self.EndModal(0)
        twain.GlobalHandleFree(handle)
    
    # callbacks gestione eventi ------------------------------------------------
    
    def _OnPageChanged(self, event):
        self.TestPage()
        event.Skip()
    
    def TestPage(self):
        def cn(x):
            return self.FindWindowByName(x)
        page = self.FindWindowById(wdr.ID_ATTACH_SPECS).GetSelection()
        if page == PAGE_NOTES:
            sel = ATTACH_TYPE_NOTE-1
        else:
            sel = page
        #cn('attach_type').SetSelection(sel)
        if   page == PAGE_TWAIN: #pagina twain
            self.UpdateTwain()
        elif page == PAGE_VOICE: #nota vocale
            self.UpdateVoice()
            if self._stream is None or len(self._stream) == 0:
                cn('attach_voice').Enable(False)

    def _OnAttachUrl(self, event):
        self.ProcessData(ATTACH_TYPE_URL)
    
    def _OnAttachNote(self, event):
        self.ProcessData(ATTACH_TYPE_NOTE)
    
    def _OnAttachVoice(self, event):
        self.ProcessData(ATTACH_TYPE_VOICE)
    
    def _OnFileChanged(self, event):
        cn = lambda x: self.FindWindowByName(x)
        file = cn('file').GetValue()
        if '.' in file:
            ext = file[file.rindex('.')+1:].lower()
            if   ext in __image_ext__:
                sel = 1
            elif ext in __sound_ext__:
                sel = 3
            else:
                sel = 0
            #cn('attach_type').SetSelection(sel)
        event.Skip()
    
    def _OnAttachFile(self, event):
        self.ProcessData(ATTACH_TYPE_FILE)
    
    def _OnSearchFile(self, event):
        dlg = wx.FileDialog(\
            None,\
            message = "Selezione file da allegare",
            defaultFile = "*.*",
            wildcard = "Tutti i files (*.*)|*.*" )
        if dlg.ShowModal() == wx.ID_OK:
            self.FindWindowByName('file').SetValue(dlg.GetPath())
        dlg.Destroy()
    
    def _OnChangeTwain(self, event):
        if self._twain_sd:
            self._twain_sd.destroy()
            self._twain_sd = None
        if self._twain_sm:
            self._twain_sm.destroy()
            self._twain_sm = None
        self.UpdateTwain()
    
    def _OnAttachTwain(self, event):
        self.ProcessData(ATTACH_TYPE_TWAIN)
    
    def _OnTwainEvent(self, event):
        try:
            if event == twain.MSG_XFERREADY:
                self.TwainTransfer(event)
                #Dlg.SetSourceInfo(self.SD, self)
                #Dlg.ShowModal()
                #try:
                    ## When the transfer dialog closes, it automatically
                    ## raises its parent, which may obscure the bit map
                    ## display box. I simply attempt to raise that box.
                    #Dlg.frm.Raise()
                #except:
                    #pass
                #self.Log("self.SS.HideUI()")
                self._twain_sd.HideUI()
                
                if len(self._stream) > ATTACH_SIZEMAX:
                    awu.MsgDialog(\
                        self,\
                        """L'immagine acquisita pesa %s bytes,\n"""\
                        """il limite attuale è di %s."""\
                        % (locale.format("%d", len(self._stream), True),\
                           locale.format("%d", ATTACH_SIZEMAX, True)),\
                        style=wx.ICON_WARNING)
                else:
                    self.EndModal(ATTACH_TYPE_TWAIN)
                
            elif event == twain.MSG_CLOSEDSREQ:
                # Have to close the DS (note: not hide it)
                self._twain_sd.destroy()
                self._twain_sd = None
                #self._twain_sm.destroy()
                #self._twain_sm = None
            
        except Exception, e:
            pass
    
    def _OnQuit(self, event):
        self.EndModal(0)


# ------------------------------------------------------------------------------


RS_ID =        0
RS_DATINS =    1
RS_TYPE =      2
RS_DESC =      3
RS_FOLDERNO =  4
RS_FILE =      5
RS_URL =       6
RS_SIZE =      7
RS_SCOPE =     8
RS_KEY =       9
RS_VATT_ID =  10
RS_AUTOTEXT = 11


class AttachmentsGrid(dbg.DbGridColoriAlternati):
    """
    Manutenzione allegati.
    Viene presentata una griglia con l'elenco degliallegati presenti e la 
    possibilità di eseguirli ed eliminarli.
    """
    
    def __init__(self, father, parent, attscope, attkey, **kwargs):
        """
        Costruttore griglia.
        Vengono passati:
            - father   = istanza del bottone AttachmentButton
            - parent   = pannello container della griglia
            - attscope = prelevato dal father
            - attkey   = prelevato dal father
        """
        self._attscope = attscope
        self._attkey = attkey
        self.attbutton = father
        self.filedel = []
        
        db = AttachTableMemo(father._tabname)
        self.db = db
        
        _NUM = dbg.gridlib.GRID_VALUE_NUMBER
        _STR = dbg.gridlib.GRID_VALUE_STRING
        _DAT = dbg.gridlib.GRID_VALUE_DATETIME
        _BYT = dbg.gridlib.GRID_VALUE_FLOAT+":10,0"
        _CHK = dbg.gridlib.GRID_VALUE_BOOL+":1,0"
        
        def cn(col):
            return self.db._GetFieldIndex(col, inline=True)
        cm = {}
        for name in 'id datins attach_type description autotext file url size voiceatt_id'.split():
            cm[name] = cn(name)
        
        cols = (( 80, (-1, "Data ins.",   _DAT, True )),\
                ( 50, (-2, "Ora",         _STR, True )),\
                ( 80, (-3, "Tipologia",   _STR, True )),\
                (250, (-4, "Descrizione", _STR, True )),\
                ( 30, (-5, "AT",          _CHK, True )),\
                (160, (-6, "File/URL",    _STR, True )),\
                ( 90, (-7, "Peso Bytes",  _BYT, True )),\
                ( 60, (-8, "id#",         _NUM, True )),\
                )
        
        class _GridTable(dbg.DbGridTable):
            """
            Ritorna il contenuto di ogni cella della griglia per il suo disegno.
            """
            def GetValue(self, row, gridcol):
                
                r = self.grid.db.GetRecordset()[row]
                col = self.rsColumns[gridcol]
                
                def GV(col):
                    return r[cm[col]]
                
                if   col == -1: #data inserimento
                    out = GV('datins')
                    if out:
                        out = out.Format().split()[0]
                    
                elif col == -2: #ora inserimento
                    out = GV('datins')
                    if out:
                        out = out.Format().split()[1]
                    
                elif col == -3: #tipologia
                    t = GV('attach_type')
                    if   t == ATTACH_TYPE_FILE:
                        out = "Documento"
                    elif t == ATTACH_TYPE_TWAIN:
                        out = "Immagine"
                    elif t == ATTACH_TYPE_URL:
                        out = "Pagina Web"
                    elif t == ATTACH_TYPE_VOICE:
                        out = "Nota vocale"
                    elif t == ATTACH_TYPE_NOTE:
                        out = "Nota"
                    else:
                        out = "Tipo sconosciuto (%s)" % t
                    
                elif col == -4: #descrizione
                    out = GV('description')
                    if GV('attach_type') in (ATTACH_TYPE_FILE, 
                                             ATTACH_TYPE_TWAIN)\
                       and GV('voiceatt_id') is not None:
                        out += " (con commento vocale, id=%d)"\
                            % GV('voiceatt_id')
                    
                elif col == -5: #autotext
                    if GV('autotext'):
                        out = 1
                    else:
                        out = 0
                    
                elif col == -6: #file/url
                    out = GV('file')
                    if not out:
                        out = GV('url')
                        if '/' in (out or ''):
                            out = out[:out.index('/')-1]
                    
                elif col == -7: #peso blob
                    if GV('size'):
                        out = locale.format("%d", GV('size'), True)
                    else:
                        out = "-"
                    out = out.rjust(10)
                    
                elif col == -8: #id
                    out = GV('id')
                    
                else:
                    out = "???"
                
                return out
        
        size = parent.GetClientSizeTuple()
        
        dbg.DbGridColoriAlternati.__init__(self, parent, -1, size=size, 
                                           tableClass=_GridTable)
        
        parent.SetBackgroundColour("gray")
        
        wait = awu.WaitDialog(father, message="Caricamento allegati in corso")
        
        #db = adb.DbTable(\
            #father._tabname, "allegati", writable=True,\
            #fields="id,datins,attach_type,description,folderno,file,url,size,"\
            #+"attscope,attkey,voiceatt_id,autotext")
        
        db.AddOrder("datins")
        db.AddOrder("description")
        db.ClearFilters()
        db.AddFilter("allegati.attscope=%s", attscope)
        db.AddFilter("allegati.attkey=%s", attkey)
        #db.AddFilter("allegati.datdel IS NULL")
        db.Retrieve()
        
        wait.Close()
        wait.Destroy()
        
        cn = lambda col: db._GetFieldIndex(col, inline=True)
        
        coldins = cn("datins")
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(db.GetRecordset(), colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(3)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        def MenuPopup(row, event):
            """
            Apertura menu con tasto dx del mouse su una riga della griglia.
            Il menu presenta sempre due scelte, la prima lancia l'allegato e
            la seconda lo elimina.
            """
            if row < self.db.RowsCount():
                self.db.MoveRow(row)
                
                def _Launch(*args):
                    father.LaunchAttachment(self.db.id)
                
                def _SaveAs(*args):
                    father.LaunchAttachment(self.db.id, saveonly=True)
                
                def _DeleteRow(*args):
                    #self.filedel.append((self.db.folderno, self.db.file))
                    if self.db.file and self.db.folderno:
                        self.filedel.append(self.db.GetFileName())
                    self.db.Delete()
                    self.ResetView()
                    self.GetParent().GetParent().UpdateStatus()
                
                def _AddVoice(*args):
                    
                    dlg = wx.FileDialog(\
                        self,\
                        message = "Seleziona sottofondo audio",
                        defaultFile = "*.mp3",
                        wildcard = "Tutti i files .mp3 (*.mp3)|*.mp3" )
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        fn = dlg.GetPath()
                        do = False
                        if '.' in fn:
                            do = fn[fn.rindex('.')+1:] in __sound_ext__
                        if do:
                            f = open(fn, 'rb')
                            _voiceatt = f.read()
                            f.close()
                            
                            db = self.db
                            v = AttachTableMemo(db.GetTableName())
                            v.AddField('NULL', 'filecontent')
                            
                            do = False
                            if db.voiceatt_id is not None:
                                if v.Get(db.voiceatt_id) and v.RowsCount() == 1:
                                    do = True
                            if not do:
                                do = v.CreateNewRow()
                                if do:
                                    v.attscope = self._attscope
                                    v.attkey = self._attkey
                                    v.attach_type = ATTACH_TYPE_VOICE
                            
                            if do:
                                v.description =\
                                  "Commento audio"
                                v.file = '.%s'%fn.split('.')[-1]
                                v.datins = DateTime.now()
                                v.filecontent = _voiceatt
                                self.attbutton.StoreNewAttach(v)
                                if v.Save():
                                    db.voiceatt_id = v.id
                                    db.Save()
                                    self.ResetView()
                    
                    dlg.Destroy()
                
                def _RecordVoice(*args):
                    dlg = wdr.VoicePlayerDialog(self, -1,\
                                                "Registra commento audio",\
                                                style=wx.DEFAULT_FRAME_STYLE\
                                                |wx.STAY_ON_TOP,\
                                                display_connect=True)
                    db = self.db
                    v = adb.DbTable(db.GetTableName(), "allegati",\
                                    writable=True,\
                                    defaults={'attach_type': 4,\
                                              'hidden':      1})
                    newrow = True
                    
                    dlg.CenterOnScreen()
                    player = VoicePlayer(dlg)
                    
                    if db.voiceatt_id is not None:
                        if v.Get(db.voiceatt_id) and v.RowsCount() == 1:
                            try:
                                f = open(VOICE_TEMPFILE, 'wb')
                                f.write(v.filecontent)
                                f.close()
                                player._stream = v.filecontent
                                newrow = False
                            except:
                                pass
                    
                    player.Unlock()
                    
                    if dlg.ShowModal() == 1:
                        do = True
                        if newrow:
                            do = v.CreateNewRow()
                            if do:
                                v.attscope = self._attscope
                                v.attkey = self._attkey
                        if do:
                            v.description =\
                              "Commento audio di sottofondo immagine"
                            v.file = "Commento.mp3"
                            v.datins = DateTime.now()
                            v.filecontent = player._stream
                            if v.Save():
                                db.voiceatt_id = v.id
                    dlg.Destroy()
                
                def _ToggleAutoText(*args):
                    db = self.db
                    if db.autotext:
                        db.autotext = 0
                    else:
                        db.autotext = 1
                    self.ForceRefresh()
                
                self.SelectRow(row)
                menu = wx.Menu()
                at = self.db.attach_type
                if   at == ATTACH_TYPE_FILE:
                    desc1 = "Apri documento"
                    desc2 = "Salva documento"
                elif at == ATTACH_TYPE_TWAIN:
                    desc1 = "Visualizza immagine"
                    desc2 = "Salva immagine"
                elif at == ATTACH_TYPE_URL:
                    desc1 = "Visita pagina"
                    desc2 = None
                elif at == ATTACH_TYPE_URL:
                    desc1 = "Riproduci"
                    desc2 = "Salva file audio"
                else:
                    desc1 = desc2 = desc3 = None
                if desc1 is not None:
                    launchId = wx.NewId()
                    menu.Append(launchId, desc1)
                    self.Bind(wx.EVT_MENU, _Launch, id=launchId)
                if desc2 is not None:
                    saveasId = wx.NewId()
                    menu.Append(saveasId, desc2)
                    self.Bind(wx.EVT_MENU, _SaveAs, id=saveasId)
                if at in (ATTACH_TYPE_FILE,
                          ATTACH_TYPE_TWAIN,
                          ATTACH_TYPE_NOTE):
                    if self.db.voiceatt_id:
                        desc1 = "Sostituisci"
                        desc2 = "Riregistra"
                    else:
                        desc1 = "Aggiungi"
                        desc2 = "Registra"
                    addVoiceId = wx.NewId()
                    menu.Append(addVoiceId, "%s file audio..." % desc1)
                    self.Bind(wx.EVT_MENU, _AddVoice, id=addVoiceId)
                    recVoiceId = wx.NewId()
                    menu.Append(recVoiceId, "%s commento audio..." % desc2)
                    self.Bind(wx.EVT_MENU, _RecordVoice, id=recVoiceId)
                if at == ATTACH_TYPE_NOTE or self.db.IsImage():
                    if self.db.autotext:
                        text = 'Disabilita'
                    else:
                        text = 'Abilita'
                    text += ' AutoText'
                    toganoteid = wx.NewId()
                    menu.Append(toganoteid, text)
                    self.Bind(wx.EVT_MENU, _ToggleAutoText, id=toganoteid)
                deleteId = wx.NewId()
                menu.Append(deleteId, "Elimina")
                self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
                xo, yo = event.GetPosition()
                self.PopupMenu(menu, (xo, yo))
                menu.Destroy()
            event.Skip()
        
        # callbacks gestione eventi griglia ------------------------------------
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if row >= 0:
                MenuPopup(row, event)
        
        self.Bind(dbg.gridlib.EVT_GRID_CELL_RIGHT_CLICK,  _OnRightClick)


# ------------------------------------------------------------------------------


class AttachmentsGridDialog(wx.Dialog):
    """
    Gestione allegati mediante griglia.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Costruttore dialog standard.
        """
        wx.Dialog.__init__(self, *args, **kwargs)
        wdr.AttachGridFunc(self)
        
        father = self.GetParent()
        parent = self.FindWindowByName('grid_container')
        self._grid = AttachmentsGrid(father, parent, father._attscope,\
                                     father._attkey)
        self.UpdateStatus()
        
        cn = lambda x: self.FindWindowByName(x)
        
        self.Bind(wx.EVT_BUTTON, self._OnSave, cn('save_modif'))
        
        self.CenterOnScreen()
    
    def UpdateStatus(self):
        rs = self._grid.db.GetRecordset()
        n, s = 0, 0
        for row in range(len(rs)):
            if rs[row][RS_TYPE] in (1,2):
                n += 1
                s += (rs[row][RS_SIZE] or 0)
        label = self.FindWindowByName('counters')
        label.SetLabel("%d documenti/immagini, per un peso totale di %s bytes"\
                       % (n, locale.format("%d", s, True)))
    
    # callbacks gestione eventi dialog -----------------------------------------
    
    def _OnSave(self, event):
        if self._grid.db.Save():
            for file in self._grid.filedel:
                try:
                    os.remove(file)
                except Exception, e:
                    awu.MsgDialog(self, 
                                  """Errore durante la cancellazione """\
                                  """del file.\n%s""" % repr(e.args))
            self.EndModal(1)


# ------------------------------------------------------------------------------

from wx.lib.ticker import Ticker

#class DummyTicker(wx.Panel):
#    def Start(self, *args, **kwargs):
#        pass
#    def Stop(self, *args, **kwargs):
#        pass
#    def IsRunning(self, *args, **kwargs):
#        return True
#    def SetText(self, *args, **kwargs):
#        pass
#Ticker = DummyTicker
    

class AutoNotes(Ticker):
    
#    def __init__(self, *args, **kwargs):
#        Ticker.__init__(self, *args, **kwargs)
##        bg = self.GetParent().GetBackgroundColour()
##        bg = wx.NullColor
##        self.SetBackgroundColour(bg)
#        self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
#        self.SetBackgroundColour(wx.NullColor)
    
    def SetText(self, t):
        if t:
            fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
            bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
            t = t.replace('\n', ' - ')
        else:
            fg = bg = wx.NullColor
        self.SetForegroundColour(fg)
        self.SetBackgroundColour(bg)
        Ticker.SetText(self, t)


# ------------------------------------------------------------------------------


class AttachmentSpyPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.AttachSpyFunc(self)
        self.bitmap = self.FindWindowByName('spy_bitmap')
    
    def SetFull(self):
        self._change_bitmap(images.getText20Bitmap())
    
    def SetEmpty(self):
        self._change_bitmap(wx.NullBitmap)
    
    def _change_bitmap(self, bmp):
        self.bitmap.SetBitmap(bmp)
        self.Layout()
        self.Refresh()
