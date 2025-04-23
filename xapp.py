#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         xapp.py
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
import os, sys, shutil, subprocess
import glob

import awc.controls.windows as aw
awu = aw.awu

import version as ver

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb

import X_wdr as wdr

import urllib2_file


class XApp(wx.App):
    
    appcode = 'appcode'
    @classmethod
    def SetAppCode(cls, appcode):
        cls.appcode = appcode
    @classmethod
    def GetAppCode(cls):
        return cls.appcode
    
    db = None
    dbcon = None
    tempfiles = []
    
    keyver = 'x4_version'
    setupname = 'x4setup'
    if ver.OSS():
        setupname += '_oss'
    
    def __init__(self, *args, **kwargs):
        
        self.moduli = 0
        try:
            self.moduli = kwargs.pop('moduli')
        except KeyError:
            pass
        
        wx.App.__init__(self, *args, **kwargs)
        
        self.SetAppCode(ver.appcode)
        self.SetAppName(ver.appdesc)
    
    def OnInit(self):
        #wx.InitAllImageHandlers()
        #self.splash = XSplashScreen(self.moduli)
        #self.SetJob("Inizializzazione in corso...")
        #self.splash.Show()
        return True
    
    def AppendTempFile(self, name):
        self.tempfiles.append(name)
    
    def OnExit(self):
        for name in self.tempfiles:
            try:
                os.remove(name)
            except:
                pass
    
    def StartApp(self):
        out = self.AppLoaded()
        if self.splash is not None:
            try:
                self.splash.Destroy()
            except wx.PyDeadObjectError:
                pass
        if out:
            self.AppStarted()
        return out
    
    def AppLoaded(self):
        self.SetJob("Inizializzazione terminata. Buon lavoro!", True)
        wx.Sleep(1)
        if self.splash is not None:
            self.splash.Hide()
        out = False
        self.TestUpdates()
        from selazienda import SelAziendaDialog
        aziDialog = SelAziendaDialog()
        if aziDialog.ShowModal() == 1:
            if self.db is None:
                self.db = adb.DB()
            else:
                self.db.Close()
            self.db.Connect(host =   Env.Azienda.DB.servername,
                            user =   Env.Azienda.DB.username,
                            passwd = Env.Azienda.DB.password,
                            db =     Env.Azienda.DB.schema)
            out = True
        aziDialog.Destroy()
        return out
    
    def AppStarted(self):
        if self.TestDBVers():
            import xframe as xfr
            frame = xfr.XFrame(None, -1, "X4GA")
            frame.Show(True)
            frame.Update()
            while not wx.SafeYield(onlyIfNeeded=True):
                wx.Sleep(.1)
            self.SetTopWindow(frame)
    
    def TestDBVers(self, force=False, reindex=False):
        
        vers_ok = True
        version_problems = []
        
        if force:
            checkv = checkm = checkp = True
        else:
            azidbver = '0.0.00'
            azidbmod = ''
            azidbapp = ''
            try:
                s = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable=False)
                if s.Retrieve("setup.chiave=%s", self.keyver) and s.OneRow():
                    azidbver = s.codice or azidbver
                    #print 'azidbver: %s' % azidbver
                    azidbmod = s.descriz[:6] or azidbmod
                    azidbapp = s.descriz[7:]
                self.setup = s
            except:
                pass
            checkv = bt.__min_compat_ver__ > azidbver
            
            #print 'bt.__min_compat_ver__:%s' % bt.__min_compat_ver__
            #print checkv
            
            if ver.VERSION_STRING < azidbver:
                version_problems.append(['X4 Gestione Aziendale', ver.VERSION_STRING, azidbver])
            checkm = False
            if len(ver.__min_compat_mod__)>0:
                checkm = ver.__min_compat_mod__ > azidbmod
                if ver.MODVERSION_STRING < azidbmod:
                    version_problems.append(['mod %s' % ver.MODVERSION_NAME, ver.MODVERSION_STRING, azidbmod])
            if not checkm:
                checkm = (azidbapp != ver.MODVERSION_NAME)
        
        checkp = False
        if not checkv and not checkm:
            for name in Env.plugins:
                p = Env.plugins[name]
                #checkp = True
                if hasattr(p, 'min_compat_ver'):
                    if s.Retrieve("setup.chiave=%s", '%s_plugin_version'%name):
                        if s.OneRow():
                            azidbver = s.codice
                            checkp = p.min_compat_ver > azidbver
                            if p.VERSION_STRING < azidbver:
                                version_problems.append(['Plugin %s' % name, p.VERSION_STRING, azidbver])
                        else:
                            checkp = True
                if checkp:
                    break
        #print checkv, checkm, checkp

        if checkv or checkm or checkp:
            compat = False
            if force:
                msg =\
                    """Per memorizzare le impostazioni occorre procedere al """\
                    """controllo di struttura delle tabelle dell'azienda."""
            elif checkv:
                try:
                    msg =\
                        """La versione delle tabelle di questa """\
                        """azienda (%s) non e' compatibile con la """\
                        """versione attuale del programma (%s).\n"""\
                        """Per proseguire occorre adeguare le """\
                        """strutture necessarie."""\
                        % (str(azidbver), ver.__version__,)
                except:
                    print azidbver, type(azidbver)
                    print ver.__version__, type(ver.__version__)
            elif checkm:
                msg =\
                    """La versione delle tabelle di questa """\
                    """azienda (%s) non e' compatibile con la """\
                    """mod attuale del programma (%s).\n"""\
                    """Per proseguire occorre adeguare le """\
                    """strutture necessarie."""\
                    % (azidbmod, ver.__modversion__,)
            elif checkp:
                msg =\
                    """La versione delle tabelle di questa azienda non e' """\
                    """compatibile con la versione di uno o più plugin.\n"""\
                    """Per proseguire occorre adeguare le strutture """\
                    """necessarie."""
            msg +=\
                """\n\nProseguo con l'analisi delle tabelle da adeguare?"""
                
            r = awu.MsgDialog(None, message=msg,
                              style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
            
            if r == wx.ID_YES:
                import cfg.tabsetup as tabsetup
                dlg = tabsetup.TabSetupDialog(reindex=reindex)
                vers_ok = dlg.ShowModal() != 0
                dlg.Destroy()
                
            else:
                if force:
                    msg =\
                        """Non e' possibile memorizzare queste impostazioni """\
                        """senza procedere al controllo di struttura """\
                        """delle tabelle dell'azienda"""
                else:
                    msg =\
                        """Le versioni sono incompatibili, non """\
                        """sara' possibile operare su questa """\
                        """azienda fino a quando la struttura del """\
                        """database non risultera' allineata alla """\
                        """corrente versione di programma %s"""\
                        % Env.__version__
                    if bt.__min_compat_mod__:
                        msg += ' mod %s' % bt.__min_compat_mod__
                awu.MsgDialog(None, message=msg, style=wx.ICON_ERROR)
                vers_ok = False
        
        self.version_problems = version_problems
        if version_problems:
            msg =\
            """Attenzione!!!\n\n"""\
            """C'e' qualcosa di non aggiornato nel software che usi:\n\n"""
            for name, verprg, verdb in version_problems:
                msg += "%s: v. software in uso=%s, database aggiornato a v.%s\n" % (name, verprg, verdb)
            msg +=\
            """\nSi consiglia di aggiornare il software quanto prima."""
            def VersionsWarning():
                aw.awu.MsgDialog(None, msg, style=wx.ICON_WARNING)
            wx.CallAfter(VersionsWarning)
        
        return vers_ok
    
    def TestUpdates(self):
        
        if not hasattr(sys, 'frozen') and False:
            return
        
        #path aggiornamenti scaricati su percorso comune
        path = Env.Azienda.config.Updates_folder
        if not path:
            return
        if not path.endswith('/'):
            path += '/'
        if not os.path.isdir(path):
            return
        
        #test setup head
        files = glob.glob(path+('%s*.exe' % self.setupname))
        if len(files) > 0:
            files.sort()
            name = files[-1].replace('\\', '/')
            parts = name[name.rindex('/')+1:-4].split('-')
            dlver = parts[1]
            #if len(parts) == 4:
                #dlver += ' - %s' % parts[3]
            over = ver.__version_exe__
            #if Env.MODVERSION_NAME:
                #over += ' - %s' % ver.__modversion_exe__
            if dlver > over or '-fu' in map(str, sys.argv) or '--forceupdate' in map(str, sys.argv):
                if aw.awu.MsgDialog(None, message=\
                                    """E' disponibile una versione aggiornata """\
                                    """del programma (%s)\nVuoi installarla ?"""\
                                    % dlver, style=wx.ICON_QUESTION|wx.YES_NO\
                                    |wx.YES_DEFAULT) == wx.ID_YES:
                    name = self.CopyFileInLocal(name)
                    print name
                    os.execl(name)
        
        self.InstallUpdatedZipFiles(path)
    
    def CopyFileInLocal(self, file):
        if os.path.exists(file):
            print file
            dir, f = os.path.split(file)
            newDir = "c:\X4GA_TMP"
            if not os.path.exists(newDir):
                os.mkdir(newDir)
            else:
                for filename in os.listdir(newDir):
                    file_path = os.path.join(newDir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception,e:
                        print 'Failed to delete %s. Reason: %s' % (file_path, e)                
                
            newFile = os.path.join(newDir, f)
            batchFile = self.CreateCopyBatch(file, newFile)
            FNULL = open(os.devnull, 'w')
            p =subprocess.Popen(batchFile , stdout=FNULL, stderr=FNULL, shell=True)
            p.wait()
            #shutil.copyfile(file, newFile)
        return newFile
    
    def CreateCopyBatch(self, oldFile, newFile):
        wrkDir, _ = os.path.split(newFile)
        fileBatch = os.path.join(wrkDir, 'x4_move.bat')
        fb = open(fileBatch, 'w')
        oldFile = oldFile.replace('/', '\\')
        cmd = 'copy "%s" "%s"' % (oldFile, newFile)
        fb.write('%s\n' % cmd)
        fb.close()
        return fileBatch   
    
    
    def InstallUpdatedZipFiles(self, path, request=True):
        
        if not hasattr(sys, 'frozen'):
            return False
        
        zips = []
        update = False
        
        #test personalizzazione
        f2e = None
        if Env.MODVERSION_NAME:
            files = glob.glob(path+'%s-*.zip' % Env.MODVERSION_NAME)
            if len(files) > 0:
                f2e = files[0]
                files.sort()
                name = files[-1].replace('\\', '/')
                parts = name[name.rindex('/')+1:-4].split('-')
                dlver = parts[1]
                over = ver.__modversion_exe__
                if dlver > over:
                    import custapp
                    zips.append((name, 'C', custapp.title, dlver))
        
        files = glob.glob(path+'*.zip')
        if len(files) > 0:
            files.sort()
            for f in files:
                if f != f2e:
                    try:
                        name = f.replace('\\', '/')
                        n = name.rindex('/')
                        m = name[n+1:]
                        n = m.index('-')
                        m = m[:n]
                        if m in Env.plugins:
                            m = Env.plugins[m]
                            parts = name[:-4].split('-')
                            dlver = parts[-1]
                            over = m.version
                            if dlver > over:
                                zips.append((name, 'P', m.title, dlver))
                    except:
                        pass
        
        if zips:
            if request:
                msg = "E' disponibile una versione aggiornata di:\n"
                for name, type, title, vers in zips:
                    msg += "%s (%s)\n" % (title, vers)
                msg += "Vuoi installare gli aggiornamenti presenti ?"
                style = wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT
                if aw.awu.MsgDialog(None, message=msg, style=style) == wx.ID_YES:
                    update = True
            else:
                update = True
        
        if not update:
            return False
        
        wait = awu.WaitDialog(None, message=\
                              'Aggiornamento componenti in corso...',
                              maximum=len(zips))
        try:
            for n, (zipfile, type, title, vers) in enumerate(zips):
                n = zipfile.rindex('/')
                name = zipfile[n+1:]
                name, name2 = name.split('-')
                dest = name+name2[-4:]
                if type == 'C':
                    path = Env.custom_base_path
                elif type == 'P':
                    path = Env.plugin_base_path
                if not os.path.isdir(path):
                    os.mkdir(path)
                try:
                    d = open(os.path.join(path,dest),'wb')
                    s = open(zipfile, 'rb')
                    d.write(s.read())
                    s.close()
                    d.close()
                except Exception, e:
                    aw.awu.MsgDialog(None, message=repr(e.args),
                                     style=wx.ICON_ERROR)
                wait.SetValue(n)
        finally:
            wait.Destroy()
        
        if request:
            def restart():
                awu.MsgDialog(None, "Il programma verrà riavviato per rendere effettive le modifiche",
                              style=wx.ICON_INFORMATION)
                os.execl(sys.argv[0])
            wx.CallAfter(restart)
    
    def SetJob(self, job, islast=False):
        try:
            self.splash.SetJob(job)
            if islast:
                b = self.splash.pbar
                b.SetValue(b.GetRange())
            wx.SafeYield(onlyIfNeeded=True)
        except:
            pass
    
    def HelpBuilder_ShowObjectHelp(self, obj=None):
        aw.HelpBuilder_ShowHelp('%s - %s' % (self.GetAppName(), 'Manuale utente'), addprefix=True)
