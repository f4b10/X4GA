#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         Env.py
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

from version import MODVERSION_NAME, __version__, __modversion__
import version

import locale

from mx import DateTime

import wx
import wx.lib.colourdb
import wx.grid as gl

from awc.util import ListSearch, MsgDialog
msgbox = lambda *args: MsgDialog(None, *args)

import awc.controls.dbgrid as dbgrid
import awc.controls.numctrl as numctrl

import MySQLdb


import ConfigParser
import os.path

import stormdb as adb

import crypt, base64

import sys, getopt

_USER_MAX_SQL_COUNT = None
def GetUserMaxSqlCount():
    return _USER_MAX_SQL_COUNT
def SetUserMaxSqlCount(n):
    global _USER_MAX_SQL_COUNT
    _USER_MAX_SQL_COUNT = n


logfile = 'c:/x4.log'
if os.path.exists(logfile):
    os.remove(logfile)

def log(x):
    f=open(logfile, 'a')
    f.write(x+'\n')
    f.close()
    

def opj(x,y):
    return os.path.join(x,y).replace('\\', '/')


config_base_path = '.'
plugin_base_path = './plugin'
custom_base_path = './cust'

import xpaths
def SetConfigBasePath(appdesc=None, pathprefix=''):
    global config_base_path
    config_base_path = xpaths.GetConfigPath(appdesc)
    global custom_base_path
    custom_base_path = xpaths.GetCustomPath(appdesc, pathprefix+config_base_path)
    global plugin_base_path
    plugin_base_path = xpaths.GetPluginPath(appdesc, pathprefix+config_base_path)
    global logfile
    logfile = opj(config_base_path, 'log.txt')


from __builtin__ import round as round_bi
def _round(n,d):
    return round_bi(n+0.0000001,d)

import __builtin__
__builtin__.round = _round


class PluginLoadingException(Exception):
    pass

plugins = {}
def LoadPlugin(plugin_name):
    plugin_name = plugin_name.replace('_plugin', '')
    plugin_func = plugin_name
    if not plugin_func.endswith('_plugin'):
        plugin_func += '_plugin'
    m = __import__(plugin_func, {}, {}, False)
    if True:#not hasattr(sys, 'frozen'):
        global plugins
        plugins[plugin_name] = m
    return True


LICENSE_OWNER = ""
LICENSE_TEXT = ""


dbservers = []

class Setup(ConfigParser.RawConfigParser):
    types = None
    def __init__(self, fileName, defs):
        fileName = fileName.replace('\\', '/')
        ConfigParser.RawConfigParser.__init__(self)
        self.types = {}
        self.defs = defs
        if not '/' in fileName and not '\\' in fileName and not ":" in fileName:
            fileName = opj(config_base_path, fileName)
            path = config_base_path
        else:
            n = fileName.rindex('/')
            path = fileName[:n]
        if not os.path.isdir(path):
            os.mkdir(path)
        self.fileName = fileName
        if os.path.exists(fileName):
            self.read()
        self.InitDefs(defs)
    
    def InitDefs(self, defs):
        for sec, opts in defs:
            for opt, val in opts:
                if not sec in self.types:
                    self.types[sec] = {}
                self.types[sec][opt] = type(val)
                if not self.has_section(sec):
                    self.add_section(sec)
                if self.has_option(sec, opt):
                    val = self.get(sec, opt)
                self.set(sec, opt, val)
    
    def set(self, sec, opt, val):
        if sec in self.types:
            t = self.types[sec]
            if opt in t:
                if type(t[opt]) is not type(val):
                    cast = t[opt]
                    if val == 'None':
                        val = None
                    try:
                        val = cast(val)
                    except TypeError:
                        pass
        ConfigParser.RawConfigParser.set(self, sec, opt, val)
        setattr(self, '%s_%s' % (sec, opt), val)
    
    def get(self, sec, opt, setvar=False):
        val = ConfigParser.RawConfigParser.get(self, sec, opt)
        if sec in self.types:
            t = self.types[sec]
            if opt in t:
                if type(t[opt]) is not type(val):
                    cast = t[opt]
                    try:
                        if cast is tuple:
                            val = eval(val)
                        else:
                            val = cast(val)
                    except TypeError:
                        pass
            if setvar:
                setattr(self, '%s_%s' % (sec, opt), val)
        return val
    
    def read(self):
        fp = open(self.fileName, 'r')
        out = self.readfp(fp)
        fp.close()
        return out
    
    def write(self):
        pswds = []
        for sec in self.sections():
            for opt in self.options(sec):
                if opt == 'pswd':
                    pswds.append((sec, opt, self.get(sec, opt)))
                    self.set(sec, opt, '****')
        fp = open(self.fileName, 'w')
        out = ConfigParser.RawConfigParser.write(self, fp)
        fp.close()
        for sec, opt, pswd in pswds:
            enc = crypt.encrypt_data(pswd)
            try:
                f = open(self.getPswdFile(sec), 'wb')
                f.write(enc)
                f.close()
            except IOError:
                pass
            self.set(sec, opt, pswd)
        return out
    
    def readfp(self, fp):
        out = ConfigParser.RawConfigParser.readfp(self, fp)
        for sec in self.sections():
            for opt in self.options(sec):
                if opt == 'pswd':
                    name = self.getPswdFile(sec)
                    if os.path.exists(name):
                        try:
                            f = open(name, 'rb')
                            enc = f.read()
                            f.close()
                            pswd = crypt.decrypt_data(enc)
                            self.set(sec, opt, pswd)
                        except IOError:
                            pass
        return out
    
    def getPswdFile(self, sec):
        """
        Determina il nome del file contenente la password relativa alla sezione 'sec' e voce 'opt'
        """
        path = self.fileName[:self.fileName.rindex('/')+1]
        return ('%s.pswd' % (path+sec.lower()))


# ------------------------------------------------------------------------------


class GeneralSetup(Setup):
    
    @classmethod
    def GetConfigFileName(cls):
        if sys.platform.startswith('linux'):
            return 'x4ga.conf' #linux
        return 'x4ga.ini' #windows
        
    @classmethod
    def GetConfigPath(cls):
        return opj(config_base_path, cls.GetConfigFileName())
    
    def __init__(self, fileName=None, config_stru=None):
        
        defs = [('Database',                            #configurazione database
                 (('type', 'mysql'),                    #tipo motore
                  ('user', ''),                         #nome utente X4
                  ('sqlspy', '0'))),                    #flag visualizzazione comandi sql
                 
                ('MySQL',                               #configurazione mysql
                 (('desc', 'Server locale'),            #descrizione server
                  ('host', 'localhost'),                #url server
                  ('port', 3306),                       #porta tcp/ip
                  ('user', ''),                         #nome utente mysql
                  ('pswd', ''))),                       #password utente mysql
                 
                ('Report',                              #configurazione report
                 (('temp',    './report/temp'),         #cartella temporanea
                  ('defin',   './report/jrxml'),        #cartella jrxml
                  ('dpers',   ''),                      #cartella report personalizzati
                  ('output',  './report/pdf'),          #cartella output files pdf
                  ('images',  './report/immagini'),     #cartella immagini dei report
                  ('dde',     '1'),                     #flag attivazione DDE x Adobe Reader
                  ('cmdprint','0'),                     #flag stampa diretta da command line
                  ('action',  'view'),                  #azione di default: view/print
                  ('pdfcmd',  ''),                      #comando apertura pdf a fine stampa
                  ('prtdef',  ''),                      #nome stampante di default
                  ('labeler', ''),)),                   #nome stampante etichettatrice
                 
                ('Site',                                #configurazione installazione
                 (('name',   'sede'),                   #nome sito
                  ('folder', ''),                       #cartella comune
                  ('attdir', ''),                       #cartella files allegati
                  ('remote', '0'),                      #flag workstation remota
                  ('inetao', '0'),)),                   #flag internet always on
                 
                ('X4news',                              #visualizzazione modifiche all'avvio
                 (('lastversionshown', ''),             #ultima versione mostrata
                  ('lastmodversionshown', ''),          #ultima mod mostrata
                  ('shownews', 0),)),                   #flag visualizza modifiche
                 
                ('Updates',                             #configurazione aggiornamenti
                 (('url',       'http://www.x4ga.com'), #url aggiornamenti
                  ('user',      ''),                    #nome utente
                  ('pswd',      ''),                    #password
                  ('folder',    ''),                    #cartella download
                  ('autocheck', '2'),)),                #flag autocheck alla partenza: 0=No, 1=Si, 2=Configura
                 
                ('DataExport',                          #configurazione esportazione griglie
                 (('csvasgrid',    '1'),                #flag genera come mostrato
                  ('csvdelimiter', ','),                #separatore campi
                  ('csvquotechar', '"'),                #delimitatore campi
                  ('csvquoting',   '2'),                #tipo presenza delimitatori
                  ('csvexcelzero', '0'),)),             #numeri come formula, workaround x excel
                 
                ('Controls',                            #configurazione controlli
                 (('iconstype', 'Vista'),               #tipo di icone delle toolbar
                  ('gridtabtraversal', '1'),)),         #flag navigazione con tasto "Alt"
             ]
        
        if config_stru:
            defs += config_stru
        
        if fileName is None:
            fileName = self.GetConfigPath()
        
        Setup.__init__(self, fileName, defs)
        
        self.loadHosts()
    
    def set(self, sec, opt, val):
        
        if sec == 'Updates':
            if opt == 'url' and val == 'http://astrasrl.dyndns.org':
                val = 'http://www.x4ga.com'
        
        Setup.set(self, sec, opt, val)
        
        if sec == 'Report':
            
            import report
            
            if opt == 'defin':
                report.SetPathRpt(val)
                if Azienda.codice:
                    report.SetPathSub('azienda_%s' % Azienda.codice)
                else:
                    report.SetPathSub('')
                
            elif opt == 'dpers':
                if val:
                    report.SetPathSub(val)
                
            elif opt == 'action':
                if val in 'view print'.split():
                    report.SetActionDefault(val)
                
            elif opt == 'pdfcmd':
                if val:
                    report.SetPdfCommand(val or None)
                
            elif opt == 'dde':
                report.SetDDE(val == '1')
                
            elif opt == 'cmdprint':
                report.SetDirectPrint(val == '1')
                
            elif opt == 'prtdef':
                report.SetPrinterName((val or '').replace('/', '\\'))
                
            elif opt == 'labeler':
                report.SetLabelerName((val or '').replace('/', '\\'))
                
            elif opt == 'output':
                if val.startswith('./') and sys.platform.startswith('linux'):
                    val = os.path.expanduser('~/%s/%s' % (version.appcode, val[2:]))
                report.SetPathPdf(val)
                
            elif opt == 'images':
                report.SetPathImg(val)
                Azienda.imagePath = val
            
        elif sec == 'DataExport':
            
            if opt == 'csvdelimiter':
                dbgrid.CSVFORMAT_DELIMITER = val
                
            elif opt == 'csvquotechar':
                dbgrid.CSVFORMAT_QUOTECHAR = val
                
            elif opt == 'csvquoting':
                dbgrid.CSVFORMAT_QUOTING = val
                
            elif opt == 'csvexcelzero':
                dbgrid.CSVFORMAT_EXCELZERO = bool(int(val or 0))
            
        elif sec == 'Site':
            
            if opt == 'remote':
                import awc.layout.gestanag as ga
                ga.SEARCH_ON_SHOW = self.get(sec, opt) != '1'
                
            elif opt == 'inetao':
                from awc.controls.entries import PartitaIvaEntryCtrl
                PartitaIvaEntryCtrl.SetAskForLink(self.get(sec, opt) != '1')
            
        elif sec == 'Database':
            
            if opt == 'sqlspy':
                adb.db.setlog(val == '1')
            
        elif sec == 'Controls':
            
            if opt == 'gridtabtraversal':
                dbgrid.TABTRAVERSAL = (val == '1')
    
    def read(self):
        out = Setup.read(self)
        self.setReportSub()
        self.setPaths()
        self.setIconsType()
        return out
    
    def write(self):
        out = Setup.write(self)
        if out:
            self.setPaths()
    
    def setPaths(self):
        sitepath = self.get('Site', 'folder')
        if len(sitepath) == 0:
            sitepath = config_base_path
        updatespath = self.get('Updates', 'folder')
        if len(updatespath) == 0:
            updatespath = opj(sitepath, 'updates')
        try:
            attachpath = self.get('Site', 'attdir')
        except:
            attachpath = ''
        if len(attachpath) == 0:
            attachpath = opj(sitepath, 'attach_files')
        import awc.controls.attachbutton as ab
        ab.attach_dir = attachpath
        if not os.path.isdir(sitepath):
            wx.MessageBox('Impossibile accedere alla cartella di configurazione:\n%s' % sitepath)
        self.set('Site', 'folder', sitepath)
        self.set('Updates', 'folder', updatespath)
    
    def setReportSub(self):
        pathrpt = self.get('Report', 'defin')
        pathimg = self.get('Report', 'images')
        try:
            pathsub = self.get('Report', 'dpers')
        except:
            pass
        if not pathsub:
            pathsub = opj(self.get('Site', 'folder'), 'report')
        if Azienda.codice:
            sub = 'azienda_%s' % Azienda.codice
        else:
            sub = ''
        import report
        del report.pathalt[:]
        for n,p in enumerate(plugins):
            if pathsub:
                report.AppendPathAlt(opj(opj(pathsub or pathrpt, sub), 
                                         'X4-plugin.%s' % p))
            report.AppendPathAlt(opj(pathsub or pathrpt, 
                                     'X4-plugin.%s' % p))
        pathsub = opj(pathsub or pathrpt, sub)
        report.SetPathRpt(pathrpt)
        report.SetPathSub(pathsub)
        report.SetPathImg(pathimg)
    
    def setIconsType(self):
        import imgfac
        try:
            imgfac.SetIconsType(self.get('Controls', 'iconstype'))
        except:
            pass
    
    def loadHosts(self):
        #impostazione multiserver
        global dbservers
        del dbservers[:]
        for i in range(10):
            sec = 'MySQL'
            if i>0:
                sec += '%d' % i
            s = []
            for opt in 'host,desc,port'.split(','):
                try:
                    s.append(self.get(sec, opt))
                except:
                    pass
            if s:
                dbservers.append(s)


# ------------------------------------------------------------------------------


class LicenseSetup(Setup):
    
    def __init__(self, fileName):
        defs = (('License',
                 (('head', ''),
                  ('piva', ''),
                  ('pswd', ''))),
             )
        Setup.__init__(self, fileName, defs)


# ------------------------------------------------------------------------------


def InitSettings(ask_missing_config=True):
    out = True
    try:
        locale.setlocale( locale.LC_ALL, "it" )
    except locale.Error:
        locale.setlocale( locale.LC_ALL)
    config = GeneralSetup()
    Azienda.config = config
    if not os.path.exists(config.fileName):
        if sys.platform == 'win32':
            test_path, test_name = os.path.split(config.fileName)
            test_file = os.path.join(test_path, 'config.ini')
            if os.path.exists(test_file):
                os.rename(test_file, config.fileName)
                config = GeneralSetup()
                Azienda.config = config
    if not os.path.exists(config.fileName):
        if not ask_missing_config:
            return False
        Azienda.firstTime=True
        import cfg.wksetup as wks
        d = wks.WorkstationSetupDialog()
        d.setConfig(config)
        if not d.ShowModal() == wx.ID_OK:
            out = False
        d.Destroy()
        if out:
            import prgup as pup
            d = pup.ProgramUpdateSetupDialog()
            d.setConfig(config)
            if not d.ShowModal() == wx.ID_OK:
                out = False
            d.Destroy()
        config.loadHosts()
    if out:
        out = InitLicense(config)
    if out:
        Azienda.firstTime=False        
        Azienda.reportPath = config.get('Report', 'defin')
        Azienda.tempPath = config.get('Report', 'temp')
        Azienda.pdfPath = config.get('Report', 'output')
        Azienda.imagePath = config.get('Report', 'images')
        host, user, psw = config.get('MySQL', 'host'), config.get('MySQL', 'user'), config.get('MySQL', 'pswd')
        Azienda.DB.servername = adb.DEFAULT_HOSTNAME = host
        Azienda.DB.username =   adb.DEFAULT_USERNAME = user
        Azienda.DB.password =   adb.DEFAULT_PASSWORD = psw
    Azienda.Colours.SetDefaults()
    return out
    

# ------------------------------------------------------------------------------


def InitLicense(config):
    path = opj(config.Site_folder, 'license')
    if not os.path.isdir(path) and not version.OSS():
        wx.MessageBox('Impossibile accedere alle informazioni della licenza d\'uso:\n%s' % path)
        try:
            os.mkdir(path)
        except OSError, e:
            wx.MessageBox('Impossibile creare le informazioni della licenza d\'uso:\n%s' % repr(e.args))
            return False
    licenseFile = opj(path, 'config.ini')
    cfglic = LicenseSetup(licenseFile)
    Azienda.license = cfglic
    import cfg.license as license
    out = False
    while not out:
        try:
            out = license.License(cfglic.License_head, 
                                  cfglic.License_piva).IsOk(cfglic.License_pswd)
        except Exception, e:
            out = version.OSS()
        if not out:
            d = license.LicenseDialog()
            d.setConfig(cfglic)
            if d.ShowModal() != wx.ID_OK:
                break
            d.Destroy()
    return out


# ------------------------------------------------------------------------------


def StrImp(num, dec=None, sepm=True, zeroblank=False):
    """
    Converte un numero in una a stringa con separatori migliaia
    Il numero di decimali per default è C{Azienda.BaseTab.VALINT_DECIMALS}
    """
    if dec is None:
        dec = Azienda.BaseTab.VALINT_DECIMALS
    if (num is None or num == 0) and zeroblank:
        out = ""
    else:
        out = locale.format("%%.%df" % dec, num, sepm)
    return out


# ------------------------------------------------------------------------------


def StrDate(date):
    """
    Converte un DateTime in una stringa nel formato di sistema (solo data)
    """
    if date is None:
        out = ''
    else:
        out = date.Format().split()[0]
    return out


# ------------------------------------------------------------------------------


def StrDateTime(date):
    """
    Converte un DateTime in una stringa nel formato italiano (data e ora)
    """
    return date.Format().split()


# ------------------------------------------------------------------------------


class Azienda(object):
    """
    Insieme di classi per la configurazione dell'azienda e la sua 
    accessibilità sul database.
    """
    firstTime = False
    config = None
    license = None
    codice = ""
    descrizione = ""
    indirizzo = ""
    cap = ""
    citta = ""
    prov = ""
    codfisc = ""
    stato = ""
    piva = ""
    numtel = ""
    numfax = ""
    email = ""
    titprivacy = ""
    infatti = ""
    reportPath = ""
    tempPath = ""
    pdfPath = ""
    imagePath = ""
    defaults = {}

    args = sys.argv[1:]
    params = {'password-length': 6,
              'onexit-execute': '',
              'redirect-output': 0,
              'show-syspath': 0,
              'custom-menu': '',}
    try:
        optlist, args = getopt.getopt(args, '', ['%s=' % key for key in params])
        for opt, val in optlist:
            key = opt.replace('--','').replace('=','')
            tipo = type(params[key])
            params[key] = tipo(val)
    except getopt.GetoptError, e:
        pass#MsgDialog(None, message="Parametri errati %s" % repr(e.args))
    
    class Login(object):
        """
        Dati relativi all'utente e l'ingresso in azienda
        """
        username = None
        usercode = None
        userid = None
        userdata = None
        dataElab = DateTime.today()
        
        @classmethod
        def GetUserData(cls, col):
            return getattr(cls.userdata, col)
    
    class Esercizio(object):
        """
        Dati relativi all'esercizio.
        Da automatizzare.
        """
        year = "2006"
        start = DateTime.Date(2006, 1, 1)
        end = DateTime.Date(2006, 12, 31)
        dataElab = DateTime.today()
    
    # --------------------------------------------------------------------------

    class Colours(object):
        """
        Database colori standard dell'applicazione.
        Colori definiti::
            NORMAL_BACKGROUND - colore standard background controlli
            NOCALC_BACKGROUND - colore di background per elementi il cui 
                                calcolo automatico è disabilitato
            
            Accesso:
                Azienda.Colours.chiave_colore
        """
        NORMAL_BACKGROUND   = None
        NORMAL_FOREGROUND   = None
        NOCALC_BACKGROUND   = None
        VALMISS_FOREGROUND  = None
        VALMISS_BACKGROUND  = None
        VALERR_FOREGROUND   = None
        VALERR_BACKGROUND   = None
        SCONTI_FOREGROUND   = None
        SCONTI_BACKGROUND   = None
        READONLY_FOREGROUND = None
        READONLY_BACKGROUND = None
        ADDED_FOREGROUND    = None
        ADDED_BACKGROUND    = None
        DELETED_FOREGROUND  = None
        DELETED_BACKGROUND  = None
        EFFSEL_FOREGROUND   = None
        EFFSEL_BACKGROUND   = None
        
        
        @classmethod
        def SetDefaults(cls):
            wx.lib.colourdb.updateColourDB()
            cdb = wx.TheColourDatabase
            cls.NORMAL_BACKGROUND =\
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW)
            cls.NORMAL_FOREGROUND =\
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT)
            cls.NOCALC_BACKGROUND = cdb.Find("ANTIQUE WHITE")
            cls.VALERR_FOREGROUND = cls.NORMAL_FOREGROUND
            cls.VALMISS_BACKGROUND = cdb.Find("MISTYROSE3")
            cls.VALERR_FOREGROUND = cdb.Find("YELLOW")
            cls.VALERR_BACKGROUND = cdb.Find("RED")
            cls.SCONTI_FOREGROUND = cdb.Find("RED")
            cls.ADDED_FOREGROUND = cdb.Find("BLACK")
            cls.ADDED_BACKGROUND = cdb.Find("LAVENDER")
            cls.READONLY_FOREGROUND = cdb.Find("BLACK")
            cls.READONLY_BACKGROUND = cdb.Find("MOCCASIN")
            cls.DELETED_FOREGROUND = cdb.Find("BLACK")
            cls.DELETED_BACKGROUND = cdb.Find("YELLOW")
            cls.EFFSEL_FOREGROUND = cdb.Find("BLACK")
            cls.EFFSEL_BACKGROUND = cdb.Find("MOCCASIN")
        
        
        @classmethod
        def GetColour(cls, colorname):
            """
            Ritorna il wx.Colour corrispondente alla stringa passata,
            cercando nel database dei colori wx.TheColourDatabase
            """
            try:
                out = wx.TheColourDatabase.Find(colorname)
            except:
                out = None
            return out

    # --------------------------------------------------------------------------

    class DB:
        """
        Fornisce i parametri per la connessione al database server.
        
            - Valori definiti dalla configurazione della workstation:
                - servername
                - serverport
                
            - Valori definiti dall'utente in fase di selezione azienda:
                - username
                - password
        """
        servername = ""
        serverport = ""
        username   = ""
        password   = ""
        pswAdmin   = ""
        schema     = ""
        
        connection = None
        
        def testdb(*args):
            #Azienda.DB.connection = MySQLdb.connect( host = "localhost",\
            #user = "jfc",\
            #passwd = "jfc",\
            #db = "astra" )
            servername = "localhost"
            username =   "root"
            password =   "root"
            schema =     "astra"
            
            Azienda.DB.servername = servername
            Azienda.DB.username =   username
            Azienda.DB.password =   password
            Azienda.DB.schema =     schema
            
            Azienda.DB.connection = MySQLdb.connect(\
                host =   Azienda.DB.servername,\
                user =   Azienda.DB.username,\
                passwd = Azienda.DB.password,\
                db =     Azienda.DB.schema)
            
            adb.DEFAULT_DATABASE = servername
            adb.DEFAULT_USERNAME = username
            adb.DEFAULT_PASSWORD = password
            adb.DEFAULT_DATABASE = schema
            
            db = adb.DB()
            db.Connect()
            
            Azienda.Login.username = username
            
        testdb = staticmethod(testdb)
    
    # --------------------------------------------------------------------------
    
    def GetAutom(codauto, default=None):
        out = default
        dba = adb.DbTable(Azienda.BaseTab.TABNAME_CFGAUTOM, 'auto', 
                          writable=False)
        if dba.Retrieve('codice=%s', codauto) and dba.OneRow():
            out = dba.aut_id
        return out
    GetAutom = staticmethod(GetAutom)
    
    # --------------------------------------------------------------------------

    class BaseTab(object):
        """
        Definizione struttura tabelle.
        ==============================
        Struttura tabelle
        -----------------
        C{BaseTab.tabelle} contiene i dati necessari alla gestione di tutte le
        tabelle del package; è una tupla di tuple, in cui ogni elemento si
        riferisce ad una singola tabella:
            
            - Nome  I{String}
            - Descrizione tabella  I{String}
            - Struttura  I{tuple}
            - Indici I{tuple}
            - Constraints I{tuple}
            - Specifiche vocali I{dict}
            
        Il terzo elemento è la tupla contenente la struttura della tabella,
        in cui ogni elemento è una tupla costituita da:
            
            - Nome della colonna   I{String}
            - Larghezza  I{int}
            - Decimali  I{int}
            - Descrizione del contenuto  I{String}
            - Attributi aggiuntivi database column  I{String}
        
        
        Accesso alla struttura di una tabella
        -------------------------------------
        E' possibile accedere alla tupla delle tabelle indirizzando l'elemento
        tabella desiderato tramite la relativa costante di posizione nella tupla,
        per ogni tabella definita come C{TABSETUP_TABLE_TABXX}, dove C{TABXX} è il
        nome maiuscolo della tabella.
        
        Esempio:
        C{strutturaclienti = Azienda.BaseTab.tabelle[ TABSETUP_TABLE_CLIENTI ]}
        
        In tale struttura è possibile accedere agli elementi tramite le costanti:::
            TABSETUP_TABLENAME = 0
            TABSETUP_TABLEDESCRIPTION = 1
            TABSETUP_TABLESTRUCTURE = 2
            TABSETUP_TABLEINDEXES = 3
            TABSETUP_TABLECONSTRAINTS = 4
            
        Nella struttura in C{TABSETUP_TABLESTRU} è possibile accedere agli elementi
        tramite le costanti:::
            TABSETUP_COLUMNNAME = 0
            TABSETUP_COLUMNTYPE = 1
            TABSETUP_COLUMNLENGTH = 2
            TABSETUP_COLUMNDECIMALS = 3
            TABSETUP_COLUMNDESCRIPTION = 4
            TABSETUP_COLUMNATTRIBUTES = 5
        
        
        Tabelle standard
        ----------------
        
        Le tabelle standard sono:::
            Tabella           Nome std   Descrizione                           Costante di posizione
            -----------------------------------------------------------------------------------------
            TABNAME_BILMAS    bilmas     Mastri di bilancio                    TABSETUP_TABLE_BILMAS
            TABNAME_BILCON    bilcon     Conti di bilancio                     TABSETUP_TABLE_BILCON
            TABNAME_PDCTIP    pdctip     Tipi anagrafici nel piano dei conti   TABSETUP_TABLE_PDCTIP
            TABNAME_ALIQIVA   aliqiva    Aliquote iva                          TABSETUP_TABLE_ALIQIVA
            TABNAME_AGENTI    agenti     Agenti                                TABSETUP_TABLE_AGENTI
            TABNAME_ZONE      zone       Zone geografiche                      TABSETUP_TABLE_ZONE
            TABNAME_VALUTE    valuet     Valute                                TABSETUP_TABLE_VALUTE
            TABNAME_MODPAG    modpag     Modalità di pagamento                 TABSETUP_TABLE_MODPAG
            TABNAME_TRAVETT   travet     Vettori x trasporto merce             TABSETUP_TABLE_TRAVET
            TABNAME_SPEINC    speinc     Spese di incasso                      TABSETUP_TABLE_SPEINC
            TABNAME_REGIVA    regiva     Registri IVA                          TABSETUP_TABLE_REGIVA
            TABNAME_CFGCONTAB cfgcontab  Configurazione causali contabili      TABSETUP_TABLE_CFGCONTAB
            TABNAME_PDC       pdc        Piano di Conti                        TABSETUP_TABLE_PDC
            TABNAME_CLIENTI   clienti    Clienti                               TABSETUP_TABLE_CLIENTI
            TABNAME_DESTIN    destin     Destinazioni dei clienti              TABSETUP_TABLE_DESTIN
            TABNAME_BANCF     bancf      Banche dei clienti/fornitori          TABSETUP_TABLE_BANCF
            TABNAME_FORNIT    fornit     Fornitori                             TABSETUP_TABLE_FORNIT
            TABNAME_CASSE     casse      Casse                                 TABSETUP_TABLE_CASSE
            TABNAME_BANCHE    banche     Banche                                TABSETUP_TABLE_BANCHE
            TABNAME_CFGPROGR  cfgprogr   Progressivi                           TABSETUP_TABLE_CFGPROGR
            TABNAME_CFGAUTOM  cfgautom   Automatismi                           TABSETUP_TABLE_CFGAUTOM
            TABNAME_CFGPDCP   cfgpdcpref Sottoconti preferiti                  TABSETUP_TABLE_CFGPDCP
            TABNAME_CONTAB_H  contab_h   Registrazioni contabili               TABSETUP_TABLE_CONTAB_H
            TABNAME_CONTAB_B  contab_b   Dettaglio registrazioni contabili     TABSETUP_TABLE_CONTAB_B
            TABNAME_CONTAB_S  contab_s   Scadenze registrazioni contabili      TABSETUP_TABLE_CONTAB_S
            TABNAME_TIPART    tipart     Tipi articolo                         TABSETUP_TABLE_TIPART
            TABNAME_CATART    catart     Categorie merce                       TABSETUP_TABLE_CATART
            TABNAME_GRUART    gruart     Gruppi merce                          TABSETUP_TABLE_GRUART
            TABNAME_PROD      prod       Prodotti                              TABSETUP_TABLE_PROD
            TABNAME_CODARTCF  codartcf   Codici articolo clienti/fornitori     TABSETUP_TABLE_CODARTCF
            TABNAME_LISTINI   listini    Listini di vendita                    TABSETUP_TABLE_LISTINI
            TABNAME_GRIGLIE   griglie    Griglie prezzi cilenti                TABSETUP_TABLE_GRIGLIE
            TABNAME_MAGAZZ    magazz     Magazzini                             TABSETUP_TABLE_MAGAZZ
            TABNAME_CFGMAGDOC cfgmagdoc  Documenti magazzino                   TABSETUP_TABLE_CFGMAGDOC
            TABNAME_CFGMAGMOV cfgmagmov  Movimenti magazzino                   TABSETUP_TABLE_CFGMAGMOV
            TABNAME_MOVMAG_H  movmag_h   Documenti magazzino                   TABSETUP_TABLE_MOVMAG_H
            TABNAME_MOVMAG_B  movmag_b   Movimenti magazzino                   TABSETUP_TABLE_MOVMAG_B
        
        """
        
        OPTDIGSEARCH = True  #flag ricerca immediata in digitazione codice/descrizione
        OPTTABSEARCH = True  #flag attivazione ricerche anche con il tasto Tab
        OPTRETSEARCH = True  #flag attivazione ricerche anche con il tasto Return
        OPTSPASEARCH = False #flag ricerca per contenuto anche con spazio, come punto punto
        OPTNOTIFICHE = False #flag attivazione notifiche eventi
        OPTBACKUPDIR = None  #cartella predefinita per i backup
        OPTLNKCRDPDC = None  #inizializzazione focus su codice/descrizione in LinkTablePdc da scheda
        OPTLNKGRDPDC = None  #inizializzazione focus su codice/descrizione in LinkTablePdc da griglia
        OPTLNKCRDCLI = None  #inizializzazione focus su codice/descrizione in LinkTableCliente da scheda
        OPTLNKGRDCLI = None  #inizializzazione focus su codice/descrizione in LinkTableCliente da griglia
        OPTLNKCRDFOR = None  #inizializzazione focus su codice/descrizione in LinkTableFornit da scheda
        OPTLNKGRDFOR = None  #inizializzazione focus su codice/descrizione in LinkTableFornit da griglia
        
        OPT_GC_PRINT = True  #flag abilitazione stampe su google cloud print
        OPT_GCP_USER = None  #nome utente google
        OPT_GCP_PSWD = None  #password utente google
        
        TIPO_CONTAB = None   #tipo di contabilità
        
        CONSOVGES = None     #chiusure con sovrapposizione o no
        CONBILRICL = False   #flag gestione bilanci riclassificati
        CONBILRCEE = False   #flag gestione bilencio riclassificato cee
        CONATTRITACC = False #flag gestione ritenute d'acconto
        CONPERRITACC = None  #percentuale di calcolo della ritenuta d'acconto
        CONCOMRITACC = None  #percentuale di competenza del totale imponibile per r.a.
        
        VALINT_DECIMALS = 2  #numero decimali su valuta interna
        VALUTE_DECIMALS = 6  #numero decimali su valuta estera
        
        VALINT_INTEGERS = 12 #numero cifre intere su valuta interna
        VALUTE_INTEGERS = 16 #numero cifre intere su valuta estera
        MAGPRE_INTEGERS = 12 #numero cifre intere prezzi
        MAGQTA_INTEGERS = 10 #numero cifre intere prezzi
        
        MAGPRE_DECIMALS = 2  #numero decimali prezzi
        MAGQTA_DECIMALS = 0  #numero decimali quantità
        MAGEAN_PREFIX = '22' #prefisso per generazione codici ean
        MAGSCOCAT = 0        #flag gestione sconti per categoria
        MAGSCORPCOS = None   #flag scorporo iva da costo
        MAGSCORPPRE = None   #flag scorporo iva da prezzi
        GESFIDICLI = False   #flag gestione fidi clienti
        MAGIMGPROD = False   #flag gestione immagine prodotto su scheda
        MAGDIGSEARCH = True  #flag ricerca prodotti in digitazione
        MAGRETSEARCH = False #flag ricerca prodotti anche con invio
        MAGEXCSEARCH = False #flag ricerca esclusiva sul codice prodotto
        MAGATTGRIP = False   #flag attivazione griglie prezzi clienti
        MAGATTGRIF = False   #flag attivazione griglie prezzi fornitori
        MAGCDEGRIP = False   #flag attivazione codice/descrizione esterni su griglie prezzi clienti
        MAGCDEGRIF = False   #flag attivazione codice/descrizione esterni su griglie prezzi fornitori
        MAGDATGRIP = False   #flag griglie per data
        MAGAGGGRIP = False   #flag aggiornamento griglie prezzi da documento
        MAGALWGRIP = False   #flag proposizione aggiornamento in nuove righe doc
        MAGPZCONF = False    #flag gestione confezioni
        MAGPZGRIP = False    #flag gestione confezioni su griglie prezzi
        MAGPPROMO = False    #flag gestione condizioni promozionali di vendita
        MAGVISGIA = False    #flag visualizzazione giacenza prodotti in ricerca e gestione
        MAGVISPRE = False    #flag visualizzazione prezzo prodotti in ricerca e gestione
        MAGVISCOS = False    #flag visualizzazione costo prodotti in ricerca e gestione
        MAGVISCPF = False    #flag visualizzazione codice prodotto del fornitore prodotti in ricerca e gestione
        MAGVISBCD = False    #flag visualizzazione barcode prodotti in ricerca e gestione
        MAGGESACC = False    #flag gestione acconti
        MAGPROVATT = False   #flag gestione calcolo provvigioni
        MAGPROVCLI = False   #flag gestione provvigione su scheda cliente
        MAGPROVPRO = False   #flag gestione provvigione su scheda prodotto
        MAGPROVMOV = " "     #flag ereditarietà provvigione su riga movimento
        MAGPROVSEQ = "P"     #tipo ereditarietà provvigione su riga moviment C=Cliente, P=Prodotto
        MAGDEMSENDFLAG = 0   #flag gestione email documenti
        MAGDEMSENDDESC = ""  #descrizione mittente email documenti
        MAGDEMSENDADDR = ""  #indirizzo posta elettroniva mittente email documenti
        MAGDEMDALLBODY = ""  #corpo del messaggio generico email documenti
        MAGNOCODEDES = False #flag attivazione destinatari non codificati
        MAGNOCODEVET = False #flag attivazione vettori non codificati
        MAGNOCDEFDES = False #flag attivazione di default destinatari non codificati su ogni nuovo doc.
        MAGNOCDEFVET = False #flag attivazione di default vettori non codificati su ogni nuovo doc.
        MAGEXTRAVET = False  #flag attivazione campi extra sui vettori
        
        #variabili per la gestione dei listini
        MAGNUMSCO = 3        #numero di sconti gestiti
        MAGNUMRIC = 3        #numero di ricariche gestite
        MAGNUMLIS = 0        #numero di listini vendita
        MAGRICLIS = 0        #numero di ricariche su listini vendita
        MAGSCOLIS = 0        #numero di scontistiche su listini vendita
        MAGROWLIS = 0        #flag attivazione listino su righe dettaglio documento
        MAGVLIFOR = 0        #flag listino variabile per fornitore
        MAGVLIMAR = 0        #flag listino variabile per marca
        MAGVLICAT = 0        #flag listino variabile per categoria
        MAGVLIGRU = 0        #flag listino variabile per gruppo
        MAGDATLIS = False    #flag listini per data
        MAGFORLIS = False    #flag codice fornitore su manutenzione listini
        MAGBCOLIS = False    #flag barcode su manutenzione listini
        MAGERPLIS = 0        #numero di ricariche del prodotto da visualizzare e mantenere
        MAGESPLIS = 0        #numero di scontistiche del prodotto da visualizzare e mantenere
        MAGVRGLIS = 0        #numero di ricariche del gruppo prezzi da visualizzare
        MAGVSGLIS = 0        #numero di scontistiche del gruppo prezzi da visualizzare
        MAGREPLIS = False    #flag visualizzazione ricarica effettiva del prezzo pubblico v/ costo ultimo
        MAGSEPLIS = False    #flag visualizzazione sconto effettivo del costo ultimo v/ prezzo pubblico
        MAGRELLIS = False    #flag visualizzazione ricarica effettiva di ogni singolo listino v/ costo ultimo
        MAGSELLIS = False    #flag visualizzazione sconto effettivo di ogni singolo listino v/ prezzo pubblico
        
        TABSETUP_COLUMNNAME =        0
        TABSETUP_COLUMNTYPE =        1
        TABSETUP_COLUMNLENGTH =      2
        TABSETUP_COLUMNDECIMALS =    3
        TABSETUP_COLUMNDESCRIPTION = 4
        TABSETUP_COLUMNATTRIBUTES =  5
        
        TABSETUP_TABLENAME =         0
        TABSETUP_TABLEDESCRIPTION =  1
        TABSETUP_TABLESTRUCTURE =    2
        TABSETUP_TABLEINDEXES =      3
        TABSETUP_TABLECONSTRAINTS =  4
        
        TABCONSTRAINT_TABLE = 0
        TABCONSTRAINT_FIELD = 1
        TABCONSTRAINT_TYPE =  2
        
        TABCONSTRAINT_TYPE_RESTRICT =   0
        TABCONSTRAINT_TYPE_NOACTION =   1
        TABCONSTRAINT_TYPE_CASCADE =    2
        TABCONSTRAINT_TYPE_SETNULL =    3
        TABCONSTRAINT_TYPE_SETDEFAULT = 4
        
        class NumProgressivo(object):
            def __init__(self):
                object.__init__(self)
                self.progr = -1
            def next(self):
                self.progr += 1
                return self.progr
        
        numtab = NumProgressivo()
        
        TABNAME_BILMAS = "bilmas"
        TABDESC_BILMAS = "Mastri di bilancio"
        TABSETUP_TABLE_BILMAS = numtab.next()
        TABSETUP_CONSTR_BILMAS = []
        TABVOICE_BILMAS = {1: ['mastro', ['il', 'un', 'del', 'dal']],
                           2: ['mastri', ['i', 'dei', 'dai']]}
        
        TABNAME_BILCON = "bilcon"
        TABDESC_BILCON = "Conti di bilancio"
        TABSETUP_TABLE_BILCON = numtab.next()
        TABSETUP_CONSTR_BILCON = []
        TABVOICE_BILCON = {1: ['conto', ['il', 'un', 'del', 'dal']],
                           2: ['conti', ['i', 'dei', 'dai']]}
        
        TABNAME_PDCTIP = "pdctip"
        TABDESC_PDCTIP = "Tipi sottoconto"
        TABSETUP_TABLE_PDCTIP = numtab.next()
        TABSETUP_CONSTR_PDCTIP = []
        TABVOICE_PDCTIP = {1: ['tipo', ['il', 'un', 'del', 'dal']],
                           2: ['tipi', ['i', 'dei', 'dai']]}
        
        TABNAME_ALIQIVA = "aliqiva"
        TABDESC_ALIQIVA = "Aliquote IVA"
        TABSETUP_TABLE_ALIQIVA = numtab.next()
        TABSETUP_CONSTR_ALIQIVA = []
        TABVOICE_ALIQIVA = {1: ['aliquota IVA', ['l\'', 'un\'', 'dell\'', 'dall\'']],
                            2: ['aliquote IVA', ['le', 'delle', 'dalle']]}
        
        TABNAME_AGENTI = "agenti"
        TABDESC_AGENTI = "Agenti"
        TABSETUP_TABLE_AGENTI = numtab.next()
        TABSETUP_CONSTR_AGENTI = []
        TABVOICE_AGENTI = {1: ['agente', ['l\'', 'un', 'dell\'', 'dall\'']],
                           2: ['agenti', ['gli', 'degli', 'dagli']]}
        
        TABNAME_ZONE = "zone"
        TABDESC_ZONE = "Zone"
        TABSETUP_TABLE_ZONE = numtab.next()
        TABSETUP_CONSTR_ZONE = []
        TABVOICE_ZONE = {1: ['zona', ['la', 'una', 'della', 'dalla']],
                         2: ['zone', ['le', 'dele', 'dalle']]}
        
        TABNAME_VALUTE = "valute"
        TABDESC_VALUTE = "Valute"
        TABSETUP_TABLE_VALUTE = numtab.next()
        TABSETUP_CONSTR_VALUTE = []
        TABVOICE_VALUTE = {1: ['valuta', ['la', 'una', 'della', 'dalla']],
                           2: ['valute', ['le', 'delle', 'dalle']]}
        
        TABNAME_MODPAG = "modpag"
        TABDESC_MODPAG = "Modalità di pagamento"
        TABSETUP_TABLE_MODPAG = numtab.next()
        TABSETUP_CONSTR_MODPAG = []
        TABVOICE_MODPAG = {1: ['mod.pagamento', ['la', 'una', 'della', 'dalla']],
                           2: ['mod.pagamento', ['le', 'delle', 'dalle']]}
        
        TABNAME_TRAVET = "travet"
        TABDESC_TRAVET = "Vettori"
        TABSETUP_TABLE_TRAVET = numtab.next()
        TABSETUP_CONSTR_TRAVET = []
        TABVOICE_TRAVET = {1: ['vettore', ['il', 'un', 'del', 'dal']],
                           2: ['vettori', ['i', 'dei', 'dai']]}
        
        TABNAME_SPEINC = "speinc"
        TABDESC_SPEINC = "Spese di incasso"
        TABSETUP_TABLE_SPEINC = numtab.next()
        TABSETUP_CONSTR_SPEINC = []
        TABVOICE_SPEINC = {1: ['spesa di incasso', ['la', 'una', 'della', 'dalla']],
                           2: ['spese di incasso', ['le', 'delle', 'dalle']]}
        
        TABNAME_REGIVA = "regiva"
        TABDESC_REGIVA = "Registri IVA"
        TABSETUP_TABLE_REGIVA = numtab.next()
        TABSETUP_CONSTR_REGIVA = []
        TABVOICE_REGIVA = {1: ['registro IVA', ['il', 'un', 'del', 'dal']],
                           2: ['registri IVA', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGCONTAB = "cfgcontab"
        TABDESC_CFGCONTAB = "Causali contabili"
        TABSETUP_TABLE_CFGCONTAB = numtab.next()
        TABSETUP_CONSTR_CFGCONTAB = []
        TABVOICE_CFGCONTAB = {1: ['causale', ['la', 'una', 'della', 'dalla']],
                              2: ['causali', ['le', 'delle', 'dalle']]}
        
        TABNAME_CATCLI = "catcli"
        TABDESC_CATCLI = "Categorie clienti"
        TABSETUP_TABLE_CATCLI = numtab.next()
        TABSETUP_CONSTR_CATCLI = []
        TABVOICE_CATCLI = {1: ['categoria cliente', ['la', 'una', 'della', 'dalla']],
                           2: ['categorie cliente', ['le', 'delle', 'dalle']]}
        
        TABNAME_CATFOR = "catfor"
        TABDESC_CATFOR = "Categorie fornitori"
        TABSETUP_TABLE_CATFOR = numtab.next()
        TABSETUP_CONSTR_CATFOR = []
        TABVOICE_CATFOR = {1: ['categoria fornitore', ['la', 'una', 'della', 'dalla']],
                           2: ['categorie fornitore', ['le', 'delle', 'dalle']]}
        
        TABNAME_STATCLI = "statcli"
        TABDESC_STATCLI = "Status clienti"
        TABSETUP_TABLE_STATCLI = numtab.next()
        TABSETUP_CONSTR_STATCLI = []
        TABVOICE_STATCLI = {1: ['status cliente', ['lo', 'uno', 'dello', 'dallo']],
                            2: ['status cliente', ['gli', 'degli', 'dagli']]}
        
        TABNAME_STATFOR = "statfor"
        TABDESC_STATFOR = "Status fornitori"
        TABSETUP_TABLE_STATFOR = numtab.next()
        TABSETUP_CONSTR_STATFOR = []
        TABVOICE_STATFOR = {1: ['status fornitore', ['lo', 'uno', 'dello', 'dallo']],
                            2: ['status fornitore', ['gli', 'degli', 'dagli']]}
        
        TABNAME_PDC = "pdc"
        TABDESC_PDC = "Piano dei conti"
        TABSETUP_TABLE_PDC = numtab.next()
        TABSETUP_CONSTR_PDC = []
        TABVOICE_PDC = {1: ['sottoconto', ['il', 'un', 'del', 'dal']],
                        2: ['sottoconti', ['i', 'dei', 'dai']]}
        
        TABNAME_CLIENTI = "clienti"
        TABDESC_CLIENTI = "Clienti"
        TABSETUP_TABLE_CLIENTI = numtab.next()
        TABSETUP_CONSTR_CLIENTI = []
        TABVOICE_CLIENTI = {1: ['cliente', ['il', 'un', 'del', 'dal']],
                            2: ['clienti', ['i', 'dei', 'dai']]}
        
        TABNAME_DESTIN = "destin"
        TABDESC_DESTIN = "Destinatari"
        TABSETUP_TABLE_DESTIN = numtab.next()
        TABSETUP_CONSTR_DESTIN = []
        TABVOICE_DESTIN = {1: ['destinatario', ['il', 'un', 'del', 'dal']],
                           2: ['destinatari', ['i', 'dei', 'dai']]}
        
        TABNAME_BANCF = "bancf"
        TABDESC_BANCF = "Banche di clienti/fornitori"
        TABSETUP_TABLE_BANCF = numtab.next()
        TABSETUP_CONSTR_BANCF = []
        TABVOICE_BANCF = {1: ['banca',  ['la', 'una', 'della', 'dalla']],
                          2: ['banche', ['le', 'delle', 'dalle']]}
        
        TABNAME_FORNIT = "fornit"
        TABDESC_FORNIT = "Fornitori"
        TABSETUP_TABLE_FORNIT = numtab.next()
        TABSETUP_CONSTR_FORNIT = []
        TABVOICE_FORNIT = {1: ['fornitore', ['il', 'un', 'del', 'dal']],
                           2: ['fornitori', ['i', 'dei', 'dai']]}
        
        TABNAME_CASSE = "casse"
        TABDESC_CASSE = "Casse"
        TABSETUP_TABLE_CASSE = numtab.next()
        TABSETUP_CONSTR_CASSE = []
        TABVOICE_CASSE = {1: ['cassa', ['la', 'una', 'della', 'dalla']],
                          2: ['casse', ['le', 'delle', 'dalle']]}
        
        TABNAME_BANCHE = "banche"
        TABDESC_BANCHE = "Banche"
        TABSETUP_TABLE_BANCHE = numtab.next()
        TABSETUP_CONSTR_BANCHE = []
        TABVOICE_BANCHE = {1: ['banca',  ['la', 'una', 'della', 'dalla']],
                           2: ['banche', ['le', 'delle', 'dalle']]}
        
        TABNAME_CONTAB_H = "contab_h"
        TABDESC_CONTAB_H = "Registrazioni contabili"
        TABSETUP_TABLE_CONTAB_H = numtab.next()
        TABSETUP_CONSTR_CONTAB_H = []
        TABVOICE_CONTAB_H = {1: ['registrazione contabile', ['la', 'una', 'della', 'dalla']],
                             2: ['registrazioni contabili', ['le', 'delle', 'dalle']]}
        
        TABNAME_CONTAB_B = "contab_b"
        TABDESC_CONTAB_B = "Dettaglio registrazioni contabili"
        TABSETUP_TABLE_CONTAB_B = numtab.next()
        TABSETUP_CONSTR_CONTAB_B = []
        TABVOICE_CONTAB_B = {1: ['dettaglio della reg.contabile', ['il', 'un', 'del', 'dal']],
                             2: ['dettagli delle reg.contabili',  ['l', 'dei', 'dai']]}
        
        TABNAME_PCF = "pcf"
        TABDESC_PCF = "Partite clienti/fornitori"
        TABSETUP_TABLE_PCF = numtab.next()
        TABSETUP_CONSTR_PCF = []
        TABVOICE_PCF = {1: ['partita cliente/fornitore', ['la', 'una', 'della', 'dalla']],
                        2: ['partite clienti/fornitori', ['le', 'delle', 'dalle']]}
        
        TABNAME_CONTAB_S = "contab_s"
        TABDESC_CONTAB_S = "Scadenze registrazioni contabili"
        TABSETUP_TABLE_CONTAB_S = numtab.next()
        TABSETUP_CONSTR_CONTAB_S = []
        TABVOICE_CONTAB_S = {1: ['scadenza della reg.contabile', ['la', 'una', 'della', 'dalla']],
                             2: ['scadenze delle reg.contabili', ['le', 'delle', 'dalle']]}
        
        TABNAME_CFGPROGR = "cfgprogr"
        TABDESC_CFGPROGR = "Progressivi"
        TABSETUP_TABLE_CFGPROGR = numtab.next()
        TABSETUP_CONSTR_PROGR = []
        TABVOICE_CFGPROGR = {1: ['progressivo', ['il', 'un', 'del', 'dal']],
                             2: ['progressivi', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGAUTOM = "cfgautom"
        TABDESC_CFGAUTOM = "Automatismi"
        TABSETUP_TABLE_CFGAUTOM = numtab.next()
        TABSETUP_CONSTR_AUTOM = []
        TABVOICE_CFGAUTOM = {1: ['automatismo', ['l\'', 'un', 'dell\'', 'dall\'']],
                             2: ['automatismi', ['gli', 'degli', 'dagli']]}
        
        TABNAME_CFGPDCP = "cfgpdcpref"
        TABDESC_CFGPDCP = "Sottoconti preferiti"
        TABSETUP_TABLE_CFGPDCP = numtab.next()
        TABSETUP_CONSTR_CFGPDCP = []
        TABVOICE_CFGPDCP = {1: ['sottoconto preferito', ['il', 'uno', 'del', 'dal']],
                            2: ['sottoconti preferiti', ['i', 'dei', 'dai']]}
        
        TABNAME_TIPART = "tipart"
        TABDESC_TIPART = "Tipi articolo"
        TABSETUP_TABLE_TIPART = numtab.next()
        TABSETUP_CONSTR_TIPART = []
        TABVOICE_TIPART = {1: ['tipo articolo', ['il', 'un', 'del', 'dal']],
                           2: ['tipi articolo', ['i', 'dei', 'dai']]}
        
        TABNAME_CATART = "catart"
        TABDESC_CATART = "Categorie merce"
        TABSETUP_TABLE_CATART = numtab.next()
        TABSETUP_CONSTR_CATART = []
        TABVOICE_CATART = {1: ['categoria merce', ['la', 'una', 'della', 'dalla']],
                           2: ['categorie merce', ['le', 'delle', 'dalle']]}
        
        TABNAME_GRUART = "gruart"
        TABDESC_GRUART = "Gruppi merce"
        TABSETUP_TABLE_GRUART = numtab.next()
        TABSETUP_CONSTR_GRUART = []
        TABVOICE_GRUART = {1: ['gruppo merce', ['il', 'un', 'del', 'dal']],
                           2: ['gruppi merce', ['i', 'dei', 'dai']]}
        
        TABNAME_STATART = "statart"
        TABDESC_STATART = "Status prodotti"
        TABSETUP_TABLE_STATART = numtab.next()
        TABSETUP_CONSTR_STATART = []
        TABVOICE_STATART = {1: ['status articolo', ['lo', 'uno', 'dello', 'dallo']],
                            2: ['status articoli', ['gli', 'degli', 'dagli']]}
        
        TABNAME_PROD = "prod"
        TABDESC_PROD = "Prodotti"
        TABSETUP_TABLE_PROD = numtab.next()
        TABSETUP_CONSTR_PROD = []
        TABVOICE_PROD = {1: ['prodotto', ['il', 'un', 'del', 'dal']],
                         2: ['prodotti', ['i', 'dei', 'dai']]}
        
        TABNAME_CODARTCF = "artfor"
        TABDESC_CODARTCF = "Codici prodotto dei fornitori"
        TABSETUP_TABLE_CODARTCF = numtab.next()
        TABSETUP_CONSTR_CODARTCF = []
        TABVOICE_CODARTCF = {1: ['codice prodotto alternativo', ['il', 'un', 'del', 'dal']],
                             2: ['codici prodotto alternativi', ['i', 'dei', 'dai']]}
        
        TABNAME_LISTINI = "listini"
        TABDESC_LISTINI = "Listini"
        TABSETUP_TABLE_LISTINI = numtab.next()
        TABSETUP_CONSTR_LISTINI = []
        TABVOICE_LISTINI = {1: ['condizione di listino', ['la', 'una', 'della', 'dalla']],
                            2: ['condizioni di listino', ['le', 'delle', 'dalle']]}
        
        TABNAME_GRIGLIE = "griglie"
        TABDESC_GRIGLIE = "Griglie"
        TABSETUP_TABLE_GRIGLIE = numtab.next()
        TABSETUP_CONSTR_GRIGLIE = []
        TABVOICE_GRIGLIE = {1: ['condizione di griglia', ['la', 'una', 'della', 'dalla']],
                            2: ['condizioni di griglia', ['le', 'delle', 'dalle']]}
        
        TABNAME_MAGAZZ = "magazz"
        TABDESC_MAGAZZ = "Magazzini"
        TABSETUP_TABLE_MAGAZZ = numtab.next()
        TABSETUP_CONSTR_MAGAZZ = []
        TABVOICE_MAGAZZ = {1: ['magazzino', ['il', 'un', 'del', 'dal']],
                           2: ['magazzini', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGMAGDOC = "cfgmagdoc"
        TABDESC_CFGMAGDOC = "Documenti di magazzino"
        TABSETUP_TABLE_CFGMAGDOC = numtab.next()
        TABSETUP_CONSTR_CFGMAGDOC = []
        TABVOICE_CFGMAGDOC = {1: ['tipo di documento', ['il', 'un', 'del', 'dal']],
                              2: ['tipi di documento', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGMAGMOV = "cfgmagmov"
        TABDESC_CFGMAGMOV = "Movimenti di magazzino"
        TABSETUP_TABLE_CFGMAGMOV = numtab.next()
        TABSETUP_CONSTR_CFGMAGMOV = []
        TABVOICE_CFGMAGMOV = {1: ['tipo di movimento', ['il', 'un', 'del', 'dal']],
                              2: ['tipi di movimento', ['i', 'dei', 'dai']]}
        
        TABNAME_MOVMAG_H = "movmag_h"
        TABDESC_MOVMAG_H = "Documenti di magazzino"
        TABSETUP_TABLE_MOVMAG_H = numtab.next()
        TABSETUP_CONSTR_MOVMAG_H = []
        TABVOICE_MOVMAG_H = {1: ['testata del documento', ['la', 'una', 'della', 'dalla']],
                             2: ['testate dei documenti', ['le', 'delle', 'dalle']]}
        
        TABNAME_MOVMAG_B = "movmag_b"
        TABDESC_MOVMAG_B = "Movimenti di magazzino"
        TABSETUP_TABLE_MOVMAG_B = numtab.next()
        TABSETUP_CONSTR_MOVMAG_B = []
        TABVOICE_MOVMAG_B = {1: ['riga di dettaglio del documento',  ['la', 'una', 'della', 'dalla']],
                             2: ['righe di dettaglio dei documenti', ['le', 'delle', 'dalle']]}
        
        TABNAME_MACRO = "macro"
        TABDESC_MACRO = "Macro per personalizzazioni"
        TABSETUP_TABLE_MACRO = numtab.next()
        TABSETUP_CONSTR_MACRO = []
        TABVOICE_MACRO = {1: ['macro', ['la', 'una', 'della', 'dalla']],
                          2: ['macro', ['le', 'delle', 'dalle']]}
        
        TABNAME_TIPLIST = "tiplist"
        TABDESC_TIPLIST = "Tipi listino"
        TABSETUP_TABLE_TIPLIST = numtab.next()
        TABSETUP_CONSTR_TIPLIST = []
        TABVOICE_TIPLIST = {1: ['tipo di listino', ['il', 'un', 'del', 'dal']],
                            2: ['tipi di listino', ['i', 'dei', 'dai']]}
        
        TABNAME_TRACAU = "tracau"
        TABDESC_TRACAU = "Causali trasporto"
        TABSETUP_TABLE_TRACAU = numtab.next()
        TABSETUP_CONSTR_TRACAU = []
        TABVOICE_TRACAU = {1: ['causale di trasporto', ['la', 'una', 'della', 'dalla']],
                           2: ['causali di trasporto', ['le', 'delle', 'dalle']]}
        
        TABNAME_TRACUR = "tracur"
        TABDESC_TRACUR = "Trasporto a cura"
        TABSETUP_TABLE_TRACUR = numtab.next()
        TABSETUP_CONSTR_TRACUR = []
        TABVOICE_TRACUR = {1: ['trasporto a cura', ['il', 'un', 'del', 'dal']],
                           2: ['trasporti a cura', ['i', 'dei', 'dai']]}
        
        TABNAME_TRAASP = "traasp"
        TABDESC_TRAASP = "Aspetto beni trasporto"
        TABSETUP_TABLE_TRAASP = numtab.next()
        TABSETUP_CONSTR_TRAASP = []
        TABVOICE_TRAASP = {1: ['aspetto del trasporto', ['ll\'', 'un', 'dell\'', 'dall\'']],
                           2: ['aspetti del trasporto', ['gli', 'degli', 'dagli']]}
        
        TABNAME_TRAPOR = "trapor"
        TABDESC_TRAPOR = "Porto"
        TABSETUP_TABLE_TRAPOR = numtab.next()
        TABSETUP_CONSTR_TRAPOR = []
        TABVOICE_TRAPOR = {1: ['tipo di porto', ['il', 'un', 'del', 'dal']],
                           2: ['tipi di porto', ['i', 'dei', 'dai']]}
        
        TABNAME_TRACON = "tracon"
        TABDESC_TRACON = "Tipo di incasso contrassegno per vettore"
        TABSETUP_TABLE_TRACON = numtab.next()
        TABSETUP_CONSTR_TRACON = []
        TABVOICE_TRACON = {1: ['tipo di contrassegno', ['il', 'un', 'del', 'dal']],
                           2: ['tipi di contrassegno', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGEFF = "cfgeff"
        TABDESC_CFGEFF = "Configurazione tracciato effetti x emissione a banca"
        TABSETUP_TABLE_CFGEFF = numtab.next()
        TABSETUP_CONSTR_CFGEFF = []
        TABVOICE_CFGEFF = {1: ['riga di configurazione effetti',  ['la', 'una', 'della', 'dalla']],
                           2: ['righe di configurazione effetti', ['le', 'delle', 'dalle']]}
        
        TABNAME_ALLEGATI = "allegati"
        TABDESC_ALLEGATI = "Allegati esterni a tabelle X4"
        TABSETUP_TABLE_ALLEGATI = numtab.next()
        TABSETUP_CONSTR_ALLEGATI = []
        TABVOICE_ALLEGATI = {1: ['allegato', ['l\'', 'un', 'dell\'', 'dall\'']],
                             2: ['allegati', ['gli', 'degli', 'dagli']]}
        
        TABNAME_LIQIVA = "liqiva"
        TABDESC_LIQIVA = "Liquidazioni IVA"
        TABSETUP_TABLE_LIQIVA = numtab.next()
        TABSETUP_CONSTR_LIQIVA = []
        TABVOICE_LIQIVA = {1: ['liquidazione IVA', ['la', 'una', 'della', 'dalla']],
                           2: ['liquidazioni IVA', ['le', 'delle', 'dalle']]}
        
        TABNAME_CFGSETUP = "cfgsetup"
        TABDESC_CFGSETUP = "Setup"
        TABSETUP_TABLE_SETUP = numtab.next()
        TABSETUP_CONSTR_CFGSETUP = []
        TABVOICE_CFGSETUP = {1: ['riga di configurazione del setup',  ['la', 'una', 'della', 'dalla']],
                             2: ['righe di configurazione del setup', ['le', 'delle', 'dalle']]}
        
        TABNAME_CFGFTDIF = "cfgftdif"
        TABDESC_CFGFTDIF = "Setup fatturazione differita"
        TABSETUP_TABLE_CFGFTDIF = numtab.next()
        TABSETUP_CONSTR_CFGFTDIF = []
        TABVOICE_CFGFTDIF = {1: ['tipo di elaborazione differita', ['il', 'un', 'del', 'dal']],
                             2: ['tipo di elaborazione differita', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGFTDDR = "cfgftddr"
        TABDESC_CFGFTDDR = "Setup fatturazione differita - documenti da raggruppare"
        TABSETUP_TABLE_CFGFTDDR = numtab.next()
        TABSETUP_CONSTR_CFGFTDDR = []
        TABVOICE_CFGFTDDR = {1: ['documento da includere nell\'elaborazione differita', ['il', 'un', 'del', 'dal']],
                             2: ['documento da includere nell\'elaborazione differita', ['i', 'dei', 'dai']]}
        
        TABNAME_CFGPERM = "cfgperm"
        TABDESC_CFGPERM = "Permessi utenti"
        TABSETUP_TABLE_CFGPERM = numtab.next()
        TABSETUP_CONSTR_CFGPERM = []
        TABVOICE_CFGPERM = {1: ['permesso utente', ['il', 'un', 'del', 'dal']],
                            2: ['permessi utente', ['i', 'dei', 'dai']]}
        
        TABNAME_EFFETTI = "effetti"
        TABDESC_EFFETTI = "Effetti"
        TABSETUP_TABLE_EFFETTI = numtab.next()
        TABSETUP_CONSTR_EFFETTI = []
        TABVOICE_EFFETTI = {1: ['effetto', ['l\'', 'un', 'dell\'', 'dall\'']],
                            2: ['effetti', ['gli', 'degli', 'dagli']]}
        
        TABNAME_SCADGRP = "scadgrp"
        TABDESC_SCADGRP = "Gruppi scadenzario"
        TABSETUP_TABLE_SCADGRP = numtab.next()
        TABSETUP_CONSTR_SCADGRP = []
        TABVOICE_SCADGRP = {1: ['gruppo scadenzario', ['il', 'un', 'del', 'dal']],
                            2: ['gruppi scadenzario', ['i', 'dei', 'dai']]}
        
        TABNAME_PROMEM = "promem"
        TABDESC_PROMEM = "Promemoria"
        TABSETUP_TABLE_PROMEM = numtab.next()
        TABSETUP_CONSTR_PROMEM = []
        TABVOICE_PROMEM = {1: ['promemoria', ['il', 'un', 'del', 'dal']],
                           2: ['promemoria', ['i', 'dei', 'dai']]}
        
        TABNAME_PROMEMU = "promemu"
        TABDESC_PROMEMU = "Utenti dei promemoria"
        TABSETUP_TABLE_PROMEMU = numtab.next()
        TABSETUP_CONSTR_PROMEMU = []
        TABVOICE_PROMEMU = {1: ['utente del promemoria', ['il', 'un', 'del', 'dal']],
                            2: ['utenti del promemoria', ['gli', 'degli', 'dagli']]}
        
        TABNAME_CFGMAGRIV = "cfgmagriv"
        TABDESC_CFGMAGRIV = "Reg.IVA x magazzino/causale"
        TABSETUP_TABLE_CFGMAGRIV = numtab.next()
        TABSETUP_CONSTR_CFGMAGRIV = []
        TABVOICE_CFGMAGRIV = {1: ['associazione magazzino/registro IVA', ['l\'', 'un\'', 'dell\'', 'dall\'']],
                              2: ['associazioni magazzino/registro IVA', ['le', 'delle', 'dalle']]}
        
        TABNAME_MARART = "marart"
        TABDESC_MARART = "Marche prodotti"
        TABSETUP_TABLE_MARART = numtab.next()
        TABSETUP_CONSTR_MARART = []
        TABVOICE_MARART = {1: ['marca del prodotto',  ['la', 'una', 'della', 'dalla']],
                           2: ['marche dei prodotti', ['le', 'delle', 'dalle']]}
        
        TABNAME_PDCRANGE =  "pdcrange"
        TABDESC_PDCRANGE = "Ranges sottoconti"
        TABSETUP_TABLE_PDCRANGE = numtab.next()
        TABSETUP_CONSTR_PDCRANGE = []
        TABVOICE_PDCRANGE = {1: ['range dei sottoconti', ['il', 'un', 'del', 'dal']],
                             2: ['range dei sottoconti', ['i', 'dei', 'dai']]}
        
        TABNAME_BRIMAS = "brimas"
        TABDESC_BRIMAS = "Mastri bilancio riclassificato"
        TABSETUP_TABLE_BRIMAS = numtab.next()
        TABSETUP_CONSTR_BRIMAS = []
        TABVOICE_BRIMAS = {1: ['mastro riclassificato', ['il', 'un', 'del', 'dal']],
                           2: ['mastri riclassificati', ['i', 'dei', 'dai']]}
        
        TABNAME_BRICON = "bricon"
        TABDESC_BRICON = "Conti bilancio riclassificato"
        TABSETUP_TABLE_BRICON = numtab.next()
        TABSETUP_CONSTR_BRICON = []
        TABVOICE_BRICON = {1: ['conto riclassificato', ['il', 'un', 'del', 'dal']],
                           2: ['conti riclassificati', ['i', 'dei', 'dai']]}
        
        TABNAME_PRODPRO = "prodpro"
        TABDESC_PRODPRO = "Progressivi prodotti"
        TABSETUP_TABLE_PRODPRO = numtab.next()
        TABSETUP_CONSTR_PRODPRO = []
        TABVOICE_PRODPRO = {1: ['riga di progressivi del prodotto',  ['la', 'una', 'della', 'dalla']],
                            2: ['righe di progressivi dei prodotti', ['le', 'delle', 'dalle']]}
        
        TABNAME_GRUPREZ = "gruprez"
        TABDESC_GRUPREZ = "Gruppi prezzi"
        TABSETUP_TABLE_GRUPREZ = numtab.next()
        TABSETUP_CONSTR_GRUPREZ = []
        TABVOICE_GRUPREZ = {1: ['gruppo prezzi', ['il', 'un', 'del', 'dal']],
                            2: ['gruppi prezzo', ['i', 'dei', 'dai']]}
        
        TABNAME_SCONTICC = "sconticc"
        TABDESC_SCONTICC = "Sconti categoria/cliente"
        TABSETUP_TABLE_SCONTICC = numtab.next()
        TABSETUP_CONSTR_SCONTICC = []
        TABVOICE_SCONTICC = {1: ['scontistica', ['la', 'una', 'della', 'dalla']],
                             2: ['scontistiche', ['le', 'delle', 'dalle']]}
        
        TABNAME_PDT_H = "pdt_h"
        TABDESC_PDT_H = "Testate letture pdt"
        TABSETUP_TABLE_PDT_H = numtab.next()
        TABSETUP_CONSTR_PDT_H = []
        TABVOICE_PDT_H = {1: ['testata delle letture PDT', ['la', 'una', 'della', 'dalla']],
                          2: ['testate delle letture PDT', ['le', 'delle', 'dalle']]}
        
        TABNAME_PDT_B = "pdt_b"
        TABDESC_PDT_B = "Dettaglio letture pdt"
        TABSETUP_TABLE_PDT_B = numtab.next()
        TABSETUP_CONSTR_PDT_B = []
        TABVOICE_PDT_B = {1: ['riga di dettaglio delle letture PDT',  ['la', 'una', 'della', 'dalla']],
                          2: ['righe di dettaglio delle letture PDT', ['le', 'delle', 'dalle']]}
        
        TABNAME_PROCOS = "procos"
        TABDESC_PROCOS = "Costi consolidati sui prodotti"
        TABSETUP_TABLE_PROCOS = numtab.next()
        TABSETUP_CONSTR_PROCOS = []
        TABVOICE_PROCOS = {1: ['costo consolidato del prodotto', ['il', 'un', 'del', 'dal']],
                           2: ['costi consolidati dei prodotti', ['i', 'dei', 'dai']]}
        
        TABNAME_PROGIA = "progia"
        TABDESC_PROGIA = "Giacenze prodotti rilevate"
        TABSETUP_TABLE_PROGIA = numtab.next()
        TABSETUP_CONSTR_PROGIA = []
        TABVOICE_PROGIA = {1: ['giacenza consolidata del prodotto', ['la', 'una', 'della', 'dalla']],
                           2: ['giacenze consolidate dei prodotti', ['le', 'delle', 'dalle']]}
        
        TABNAME_PROMO = "promo"
        TABDESC_PROMO = "Condizioni promozionali prodotti"
        TABSETUP_TABLE_PROMO = numtab.next()
        TABSETUP_CONSTR_PROMO = []
        TABVOICE_PROMO = {1: ['condizione promo del prodotto', ['la', 'una', 'della', 'dalla']],
                          2: ['condizioni promo dei prodotti', ['le', 'delle', 'dalle']]}
        
        TABNAME_STATPDC = "statpdc"
        TABDESC_STATPDC = "Status sottoconti P.d.C."
        TABSETUP_TABLE_STATPDC = numtab.next()
        TABSETUP_CONSTR_STATPDC = []
        TABVOICE_STATPDC = {1: ['status del P.d.C.', ['lo', 'uno', 'dello', 'dallo']],
                            2: ['status del P.d.C.', ['gli', 'degli', 'dagli']]}
        
        TABNAME_TIPEVENT = "tipevent"
        TABDESC_TIPEVENT = "Tipi evento"
        TABSETUP_TABLE_TIPEVENT = numtab.next()
        TABSETUP_CONSTR_TIPEVENT = []
        TABVOICE_TIPEVENT = {1: ['tipo di evento', ['il', 'un', 'del', 'dal']],
                             2: ['tipi di evento', ['i', 'dei', 'dai']]}
        
        TABNAME_EVENTI = "eventi"
        TABDESC_EVENTI = "Eventi"
        TABSETUP_TABLE_EVENTI = numtab.next()
        TABSETUP_CONSTR_EVENTI = []
        TABVOICE_EVENTI = {1: ['evento', ['l\'', 'un', 'dell\'', 'dall\'']],
                           2: ['eventi', ['gli', 'degli', 'dagli']]}
        
        TABNAME_DOCSEMAIL = "docsemail"
        TABDESC_DOCSEMAIL = "Documenti per email"
        TABSETUP_TABLE_DOCSEMAIL = numtab.next()
        TABSETUP_CONSTR_DOCSEMAIL = []
        TABVOICE_DOCSEMAIL = {1: ['email', ['l\'', 'una', 'dell\'', 'dall\'']],
                              2: ['email', ['le', 'delle', 'dalle']]}
        
        TABNAME_VARLIST = "varlist"
        TABDESC_VARLIST = "Listini variabili"
        TABSETUP_TABLE_VARLIST = numtab.next()
        TABSETUP_CONSTR_VARLIST = []
        TABVOICE_VARLIST = {1: ['listino variabile', ['il', 'un', 'del', 'dal']],
                            2: ['listini variabili', ['i', 'dai', 'dai']]}
        
        tabelle = None
        
        idw = 6    #larghezza colonne ID (integer)
        ntw = 1024 #larghezza colonne di tipo note
        dsw = 1024 #larghezza colonna descrizione in dettaglio doc.mag
        
        std_indexes = ( ("PRIMARY KEY", "id"),
                        ("UNIQUE KEY",  "codice"),
                        ("UNIQUE KEY",  "descriz"), )
        
        
        @classmethod
        def getStdIdWidth(cls):
            return cls.idw
        
        
        @classmethod
        def getStdNoteWidth(cls):
            return cls.ntw
        
        
        @classmethod
        def getStdDesMovWidth(cls):
            return cls.dsw
        
        
        @classmethod
        def defstru(cls, initall=True):
            
            DVI = cls.VALINT_DECIMALS #decimali valuta di conto
            DVE = cls.VALUTE_DECIMALS #decimali max valute estere
            DQM = cls.MAGQTA_DECIMALS #decimali qta mag.
            DPM = cls.MAGPRE_DECIMALS #decimali prezzo mag.
            
            IVI = cls.VALINT_INTEGERS #cifre intere valuta di conto
            IVE = cls.VALUTE_INTEGERS #cifre intere valute estere
            IQM = cls.MAGQTA_INTEGERS #cifre intere qta mag.
            IPM = cls.MAGPRE_INTEGERS #cifre intere prezzo mag.
            
            adb.dbtable.SetNumDecImp(DVI)
            adb.dbtable.SetNumDecPrz(DPM)
            adb.dbtable.SetNumDecQta(DQM)
            
            idw = cls.idw
            ntw = cls.ntw
            
            #azzeramento costrizioni tabelle
            for nome in dir(cls):
                if nome.startswith('TABSETUP_CONSTR_'):
                    del getattr(cls, nome)[:]
            
            cls.bilmas =\
              [ [ "id",         "INT",    idw,    0, "ID Mastro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "tipo",       "CHAR",     1, None, "Tipologia P/E/O", None ] ]
            cls.bilmas_indexes = cls.std_indexes
            
            
            cls.bilcon =\
              [ [ "id",         "INT",    idw, None, "ID Conto", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "id_bilmas",  "INT",    idw, None, "ID Mastro", None ] ]
            
            cls.set_constraints(cls.TABNAME_BILCON,
                                ((cls.TABSETUP_CONSTR_BILMAS, 'id_bilmas', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.bilcon_indexes = [ ["PRIMARY KEY", "id"],
                                    ["UNIQUE KEY",  "id_bilmas,codice"],
                                    ["UNIQUE KEY",  "id_bilmas,descriz"], ]
            
            
            cls.pdctip =\
              [ [ "id",         "INT",    idw, None, "ID Tipo sottoconto", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "tipo",       "CHAR",     1, None, "Tipo", None ],
                [ "id_bilmas",  "INT",    idw, None, "ID Mastro default", None ],
                [ "id_bilcon",  "INT",    idw, None, "ID Conto default", None ],
                [ "id_bilcee",  "INT",    idw, None, "ID bilancio CEE", None ],
                [ "id_pdcrange","INT",    idw, None, "ID range sottoconti", None ] ]
            
            cls.set_constraints(cls.TABNAME_PDCTIP,
                                ((cls.TABSETUP_CONSTR_BILMAS, 'id_bilmas', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_BILCON, 'id_bilcon', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.pdctip_indexes = cls.std_indexes
            
            
            cls.aliqiva =\
              [ [ "id",         "INT",    idw, None, "ID Aliquota", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "tipo",       "CHAR",     1, None, "Tipo aliquota", None ],
                [ "modo",       "CHAR",     1, None, "Modo applicazione iva (imponibile, non imponibile, esente, fuori campo)", None ],
                [ "perciva",    "DECIMAL",  5,    2, "Perc.IVA", None ],
                [ "percind",    "DECIMAL",  5,    2, "Perc.Indeducibilità", None ],
                [ "pralcc1",    "TINYINT",  1, None, "Flag allegati clienti col.1", None ],
                [ "pralcc2",    "TINYINT",  1, None, "Flag allegati clienti col.2", None ],
                [ "pralcc3",    "TINYINT",  1, None, "Flag allegati clienti col.3", None ],
                [ "pralcc4",    "TINYINT",  1, None, "Flag allegati clienti col.4", None ],
                [ "pralfc1",    "TINYINT",  1, None, "Flag allegati fornitori col.1", None ],
                [ "pralfc2",    "TINYINT",  1, None, "Flag allegati fornitori col.2", None ],
                [ "pralfc3",    "TINYINT",  1, None, "Flag allegati fornitori col.3", None ],
                [ "pralfc4",    "TINYINT",  1, None, "Flag allegati fornitori col.4", None ],
                [ "sm11_no",    "TINYINT",  1, None, "Flag esclusione da spesometro 2011", None ], ]
            
            cls.aliqiva_indexes = cls.std_indexes
            
            
            cls.agenti =\
              [ [ "id",         "INT",    idw, None, "ID Agente", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "indirizzo",  "VARCHAR", 60, None, "Indirizzo", None ],
                [ "cap",        "CHAR",     5, None, "CAP", None ],
                [ "citta",      "VARCHAR", 60, None, "Città", None ],
                [ "prov",       "CHAR",     2, None, "Provincia", None ],
                [ "piva",       "CHAR",    20, None, "Partita IVA", None ],
                [ "numtel",     "VARCHAR", 60, None, "Num. telefono", None ],
                [ "numtel2",    "VARCHAR", 60, None, "Num. telefono agg.", None ],
                [ "numcel",     "VARCHAR", 60, None, "Num. cellulare", None ],
                [ "numfax",     "VARCHAR", 60, None, "Num FAX", None ],
                [ "siteurl",    "VARCHAR",120, None, "Url sito internet", None ],
                [ "email",      "VARCHAR", 80, None, "Indirizzo email", None ],
                [ "banca",      "VARCHAR", 80, None, "Banca", None ],
                [ "abi",        "CHAR",     5, None, "ABI", None ],
                [ "cab",        "CHAR",     5, None, "CAB", None ],
                [ "numcc",      "VARCHAR", 12, None, "Num. C/C", None ],
                [ "iban",       "VARCHAR", 27, None, "Coord. IBAN", None ],
                [ "id_zona",    "INT",    idw, None, "ID zona", None ],
                [ "noprovvig",  "TINYINT",  1, None, "Flag esclusione da provvigioni", None ], ]
            
            #cls.set_constraints(cls.TABNAME_AGENTI,
                                #((cls.TABSETUP_CONSTR_ZONE, 'id_zona', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.agenti_indexes = cls.std_indexes
            
            
            cls.zone =\
              [ [ "id",         "INT",    idw, None, "ID Zona", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ] ]
            
            cls.zone_indexes = cls.std_indexes
            
            
            cls.valute =\
              [ [ "id",         "INT",    idw, None, "ID Valuta", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "cambio",     "DECIMAL",IVE,    6, "Cambio EURO", None ]  ]
            
            cls.valute_indexes = cls.std_indexes
            
            
            cls.modpag =\
              [ [ "id",         "INT",    idw, None, "ID Mod.pagamento", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],\
                [ "tipo",       "CHAR",     1, None, "Tipologia", None ],\
                [ "congar",     "TINYINT",  1, None, "Flag con o senza garanzia", None ],\
                [ "contrass",   "TINYINT",  1, None, "Flag contrassegno", None ],\
                [ "askbanca",   "TINYINT",  1, None, "Flag richiesta banca", None ],\
                [ "askspese",   "TINYINT",  1, None, "Flag richiesta spese", None ],\
                [ "modocalc",   "CHAR",     1, None, "Modalità di calcolo Sintetico/Dettagliato", None ],\
                [ "tipoper",    "CHAR",     1, None, "Tipo periodi", None ],\
                [ "finemese0",  "TINYINT",  1, None, "Flag fine mese su inizio calcolo", None ],\
                [ "finemese",   "TINYINT",  1, None, "Flag calcolo fine mese", None ],\
                [ "numscad",    "INT",      2, None, "Numero di scadenze", None ],\
                [ "mesi1",      "INT",      2, None, "Num. di mesi alla prima scadenza", None ],\
                [ "mesitra",    "INT",      2, None, "Num. di mesi tra una scadenza e l'altra", None ],\
                [ "sc1noeff",   "TINYINT",  1, None, "Esclusione effetto su scadenza 1", None ],\
                [ "sc1iva",     "TINYINT",  1, None, "Importo della scadenza 1 pari al totale IVA", None ],\
                [ "sc1perc",    "DECIMAL",  3,    0, "Percentuale di calcolo per scadenza 1", None ],\
                [ "id_pdcpi",   "INT",    idw, None, "ID cassa/banca se pag.immediato", None ] ]
            for n in range(1,37):
                col = 'gg' + ("00%d" % n)[-2:]
                cls.modpag.append([ col, "INT", 4, None,\
                                    "Giorni alla scadenza #%d" % n, None ])
            cls.modpag.append([ "ggextra", "INT", 2, None, "Giorni extra da aggiungere ad ogni scadenza", None ])
            for n in range(1,13):
                col = 'gem' + ("00%d" % n)[-2:]
                cls.modpag.append([ col, "INT", 4, None, "Giorni extra per il mese #%d" % n, None ])
            
            cls.set_constraints(cls.TABNAME_MODPAG,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdcpi', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.modpag_indexes = cls.std_indexes
            
            
            cls.travet =\
              [ [ "id",         "INT",     idw, None, "ID Vettore", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",     10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 255, None, "Descrizione", None ], 
                [ "indirizzo",  "VARCHAR",  60, None, "Indirizzo", None ],
                [ "cap",        "CHAR",      8, None, "CAP", None ],
                [ "citta",      "VARCHAR",  60, None, "Città", None ],
                [ "prov",       "CHAR",      2, None, "Provincia", None ],
                [ "codfisc",    "CHAR",     16, None, "Cod. fiscale", None ],
                [ "nazione",    "CHAR",      4, None, "Nazione", None ],
                [ "piva",       "CHAR",     20, None, "Partita IVA", None ],
                [ "numtel",     "VARCHAR",  60, None, "Nmu. telefono", None ],
                [ "numtel2",    "VARCHAR",  60, None, "Num. telefono aggiuntivo", None ],
                [ "numfax",     "VARCHAR",  60, None, "Num. FAX", None ],
                [ "numfax2",    "VARCHAR",  60, None, "Num. FAX aggiuntivo", None ],
                [ "email",      "VARCHAR", 120, None, "Email", None ], 
                [ "siteurl",    "VARCHAR", 120, None, "Url sito internet", None ], 
                [ "id_stato",   "INT",     idw, None, "ID Stato", None ], ]
            
            if cls.MAGEXTRAVET:
                a = cls.travet.append
                a(["targa",   "VARCHAR",    16, None, "Targa", None ])
                a(["autista", "VARCHAR",    64, None, "Autista", None ])
                a(["dichiar", "VARCHAR",   ntw, None, "Dichiarazione", None ])
            
            cls.set_constraints(cls.TABNAME_TRAVET,
                                ((cls.TABSETUP_CONSTR_MOVMAG_H, 'id_travet', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.travet_indexes = cls.std_indexes
            
            
            cls.speinc =\
              [ [ "id",         "INT",    idw, None, "ID Spesa", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "importo",    "DECIMAL",  9,  DVI, "Importo spesa", None ],
                [ "id_aliqiva", "INT",    idw, None, "ID aliquota IVA", None ] ]
            
            cls.set_constraints(cls.TABNAME_SPEINC,
                                ((cls.TABSETUP_CONSTR_ALIQIVA, 'id_aliqiva', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.speinc_indexes = cls.std_indexes
            
            
            cls.regiva = \
              [ [ "id",         "INT",    idw, None, "ID Registro IVA", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "tipo",       "CHAR",     1, None, "Tipologia registro", None ],
                [ "intestaz",   "VARCHAR",160, None, "Intestazione registro", None ],
                [ "intanno",    "INT",      4, None, "Anno intestazione", None ],
                [ "intpag",     "INT",      6, None, "Num. pagina in intestazione", None ], 
                [ "lastprtnum", "INT",      6, None, "Num. protocollo ultima stampa definitiva", None ], 
                [ "lastprtdat", "DATE",  None, None, "Data registrazione ultima stampa definitiva", None ], 
                [ "noprot",     "TINYINT",  1, None, "Flag inibizione numero protocollo", None ], 
                [ "rieponly",   "TINYINT",  1, None, "Flag registro riepilogativo", None ], 
                [ "stacosric",  "TINYINT",  1, None, "Flag stampa costi/ricavi in semplificata", None ], 
                [ "numdocsez",  "CHAR",     4, None, "Sezione per stampa sezione su numero documento", None ], 
                [ "numdocann",  "TINYINT",  1, None, "Flag per stampa anno su numero documento", None ], 
            ]
            
            cls.regiva_indexes = cls.std_indexes
            
            
            cls.cfgcontab =\
              [ [ "id",          "INT",     idw, None, "ID Causale", "AUTO_INCREMENT" ],
                [ "codice",      "CHAR",     10, None, "Codice", None ],
                [ "descriz",     "VARCHAR",  60, None, "Descrizione", None ],
                [ "tipo",        "CHAR",      1, None, "Tipologia", None ],
                [ "esercizio",   "CHAR",      1, None, "Esercizio", None ],
                [ "id_regiva",   "INT",     idw, None, "ID registro IVA", None ],
                [ "regivadyn",   "TINYINT",   1, None, "Registro IVA variabile con il magazzino", None ],
                [ "datdoc",      "CHAR",      1, None, "Tipo di gestione Data Documento", None ],
                [ "numdoc",      "CHAR",      1, None, "Tipo di gestione Numero Documento", None ],
                [ "numiva",      "CHAR",      1, None, "Tipo di gestione Numero protocollo IVA", None ],
                [ "modpag",      "CHAR",      1, None, "Tipo di gestione Mod. Pagamento", None ],
                [ "pcf",         "CHAR",      1, None, "Gestione scadenzario", None ],
                [ "pcfscon",     "CHAR",      1, None, "Gestione scadenzario: saldaconto", None ],
                [ "pcfimp",      "CHAR",      1, None, "Gestione scadenzario: importo/pareggiamento", None ],
                [ "pcfsgn",      "CHAR",      1, None, "Gestione scadenzario: segno", None ],
                [ "pcfabb",      "CHAR",      1, None, "Gestione scadenzario: abbuono", None ],
                [ "pcfspe",      "CHAR",      1, None, "Gestione scadenzario: spese", None ],
                [ "pcfins",      "CHAR",      1, None, "Gestione scadenzario: insoluto", None ],
                [ "pades",       "VARCHAR",  60, None, "Partita: descrizione", None ],
                [ "id_pdctippa", "INT",     idw, None, "Partita: ID tipo PDC", None ],
                [ "pasegno",     "CHAR",      1, None, "Partita: Segno contabile", None ],
                [ "cpdes",       "VARCHAR",  60, None, "C/Partita: descrizione", None ],
                [ "id_pdctipcp", "INT",     idw, None, "C/Partita: ID tipo PDC", None ],
                [ "pralcf",      "TINYINT",   1, None, "Flag allegati clienti/fornitori", None ],
                [ "id_pdcrow1",  "INT",     idw, None, "Partita: ID PDC fisso", None ],
                [ "camsegr1",    "TINYINT",   1, None, "Flag permesso cambio segno su riga 1", None ], 
                [ "quaivanob",   "TINYINT",   1, None, "Flag quadratura iva/dare-avere non bloccante", None ], 
                [ "davscorp",    "TINYINT",   1, None, "Flag colonna importo da scorporare su dare/avere", None ], 
                [ "id_tipevent", "INT",     idw, None, "ID Tipo evento", None ], 
                [ "event_msg",   "VARCHAR",1024, None, "Messaggio evento", None ], 
                [ "rptname",     "VARCHAR",  64, None, "Nome report da proporre a fine registrazione", None ], 
            ]
            
            cls.set_constraints(cls.TABNAME_CFGCONTAB,
                                ((cls.TABSETUP_CONSTR_REGIVA,   'id_regiva',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDCTIP,   'id_pdctippa', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDCTIP,   'id_pdctipcp', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,      'id_pdcrow1',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TIPEVENT, 'id_tipevent', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgcontab_indexes = cls.std_indexes
            
            
            cls.catcli =\
              [ [ "id",         "INT",    idw, None, "ID Categoria", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ], ]
            
            cls.catcli_indexes = cls.std_indexes
            
            
            cls.catfor =\
              [ [ "id",         "INT",    idw, None, "ID Categoria", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ], ]
            
            cls.catfor_indexes = cls.std_indexes
            
            
            cls.statcli =\
              [ [ "id",           "INT",    idw, None, "ID Sottoconto", "AUTO_INCREMENT" ],
                [ "codice",       "CHAR",    10, None, "Codice", None ],
                [ "descriz",      "VARCHAR", 60, None, "Descrizione", None ], 
                [ "hidesearch",   "TINYINT",  1, None, "Flag per nascondere nelle ricerche", None ],
                [ "nomov_ordcli", "TINYINT",  1, None, "Flag per impedire l'inserimento negli ordini da cliente", None ],
                [ "nomov_vencli", "TINYINT",  1, None, "Flag per impedire l'inserimento nelle vendite a cliente", None ],
                [ "nomov_rescli", "TINYINT",  1, None, "Flag per impedire l'inserimento nei resi da cliente", None ],
                [ "noeffetti",    "TINYINT",  1, None, "Flag per impedire l'uso di mod.pagemento con effetti", None ],
            ]
            
            cls.statcli_indexes = cls.std_indexes
            
            
            cls.statfor =\
              [ [ "id",           "INT",    idw, None, "ID Sottoconto", "AUTO_INCREMENT" ],
                [ "codice",       "CHAR",    10, None, "Codice", None ],
                [ "descriz",      "VARCHAR", 60, None, "Descrizione", None ], 
                [ "hidesearch",   "TINYINT",  1, None, "Flag per nascondere nelle ricerche", None ],
                [ "nomov_ordfor", "TINYINT",  1, None, "Flag per impedire l'inserimento negli ordini a fornitore", None ],
                [ "nomov_carfor", "TINYINT",  1, None, "Flag per impedire l'inserimento nei carichi da fornitore", None ],
                [ "nomov_resfor", "TINYINT",  1, None, "Flag per impedire l'inserimento nei resi a fornitore", None ],
            ]
            
            cls.statfor_indexes = cls.std_indexes
            
            
            cls.pdc =\
              [ [ "id",         "INT",    idw, None, "ID Sottoconto", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "f_sermer",   "CHAR",     1, None, "Flag servizi/merce per spesometro", None ],
                [ "id_tipo",    "INT",    idw, None, "ID tipo anagrafico", None ],
                [ "id_bilmas",  "INT",    idw, None, "ID mastro bilancio", "NOT NULL DEFAULT -1" ],
                [ "id_bilcon",  "INT",    idw, None, "ID conto bilancio", "NOT NULL DEFAULT -1" ],
                [ "id_brimas",  "INT",    idw, None, "ID mastro bilancio ricl.", None ],
                [ "id_bricon",  "INT",    idw, None, "ID conto bilancio ricl.", None ],
                [ "id_bilcee",  "INT",    idw, None, "ID bilancio CEE", None ], 
                [ "id_statpdc", "INT",    idw, None, "ID status p.d.c.", None ], 
            ]
            
            cls.set_constraints(cls.TABNAME_PDC,
                                ((cls.TABSETUP_CONSTR_BILMAS,  'id_bilmas',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_BILCON,  'id_bilcon',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_BRIMAS,  'id_brimas',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_BRICON,  'id_bricon',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_STATPDC, 'id_statpdc', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.pdc_indexes = [ ["PRIMARY KEY", "id"],
                                 ["UNIQUE KEY", "codice"],
                                 ["KEY",        "id_tipo,descriz"] ]
            
            
            cls.clienti =\
              [ [ "id",             "INT",    idw, None, "ID Cliente", None ],
                [ "indirizzo",      "VARCHAR", 60, None, "Indirizzo", None ],
                [ "cap",            "CHAR",     8, None, "CAP", None ],
                [ "citta",          "VARCHAR", 60, None, "Città", None ],
                [ "prov",           "CHAR",     2, None, "Provincia", None ],
                [ "codfisc",        "CHAR",    16, None, "Cod. fiscale", None ],
                [ "nazione",        "CHAR",     4, None, "Nazione", None ],
                [ "piva",           "CHAR",    20, None, "Partita IVA", None ],
                [ "numtel",         "VARCHAR", 60, None, "Nmu. telefono", None ],
                [ "numtel2",        "VARCHAR", 60, None, "Num. telefono aggiuntivo", None ],
                [ "numfax",         "VARCHAR", 60, None, "Num. FAX", None ],
                [ "numfax2",        "VARCHAR", 60, None, "Num. FAX aggiuntivo", None ],
                [ "email",          "VARCHAR",120, None, "Email", None ],
                [ "docsemail",      "VARCHAR",120, None, "Email spedizione fatture e documenti", None ],
                [ "noexemail",      "VARCHAR",120, None, "Flag stampa comunque carta anche se ha email documenti", None ],
                [ "siteurl",        "VARCHAR",120, None, "Url sito internet", None ],
                [ "ctt1nome",       "VARCHAR",255, None, "Contatto1: nome", None ],
                [ "ctt1email",      "VARCHAR",255, None, "Contatto1: email", None ],
                [ "ctt1numtel",     "VARCHAR", 60, None, "Contatto1: num.telefono", None ],
                [ "ctt2nome",       "VARCHAR",255, None, "Contatto2: nome", None ],
                [ "ctt2email",      "VARCHAR",255, None, "Contatto2: email", None ],
                [ "ctt2numtel",     "VARCHAR", 60, None, "Contatto2: num.telefono", None ],
                [ "ctt3nome",       "VARCHAR",255, None, "Contatto3: nome", None ],
                [ "ctt3email",      "VARCHAR",255, None, "Contatto3: email", None ],
                [ "ctt3numtel",     "VARCHAR", 60, None, "Contatto3: num.telefono", None ],
                [ "spddes",         "VARCHAR", 60, None, "Descriz. x spedizione documenti", None ],
                [ "spdind",         "VARCHAR", 60, None, "Indirizzo x spedizione documenti", None ],
                [ "spdcap",         "CHAR",     5, None, "CAP x spedizione documenti", None ],
                [ "spdcit",         "VARCHAR", 60, None, "Città x spedizione documenti", None ],
                [ "spdpro",         "CHAR",     2, None, "Provincia x spedizione doc.", None ],
                [ "sconto1",        "DECIMAL",  5,    2, "Sconto perc.1", None ],
                [ "sconto2",        "DECIMAL",  5,    2, "Sconto perc.2", None ],
                [ "sconto3",        "DECIMAL",  5,    2, "Sconto perc.3", None ],
                [ "sconto4",        "DECIMAL",  5,    2, "Sconto perc.4", None ],
                [ "sconto5",        "DECIMAL",  5,    2, "Sconto perc.5", None ],
                [ "sconto6",        "DECIMAL",  5,    2, "Sconto perc.6", None ],
                [ "chiusura",       "VARCHAR", 60, None, "Giorno di chiusura", None ],
                [ "note",           "VARCHAR",ntw, None, "Annotazioni", None ],
                [ "notedoc",        "VARCHAR",ntw, None, "Note da stampre sui documenti", None ],
                [ "notepag",        "VARCHAR",ntw, None, "Note per i pagamenti", None ],
                [ "fdr0doc",        "TINYINT",  3, None, "Num.scoperti fido non riba", None ],
                [ "fdr0imp",        "DECIMAL",IVI,  DVI, "Imp.scoperti fido non riba", None ],
                [ "fdr1doc",        "TINYINT",  3, None, "Num.scoperti fido riba", None ],
                [ "fdr1imp",        "DECIMAL",IVI,  DVI, "Imp.scoperti fido riba", None  ],
                [ "id_stato",       "INT",    idw, None, "ID Stato", None ],
                [ "id_pdc",         "INT",    idw, None, "ID Sottoconto associato", None ],
                [ "id_zona",        "INT",    idw, None, "ID Zona appartenenza", None ],
                [ "id_agente",      "INT",    idw, None, "ID Agente", None ],
                [ "id_valuta",      "INT",    idw, None, "ID Valuta", None ],
                [ "id_aliqiva",     "INT",    idw, None, "ID Aliquota IVA", None ],
                [ "id_modpag",      "INT",    idw, None, "ID Mod.pagamento", None ],
                [ "id_speinc",      "INT",    idw, None, "ID Spese incasso", None ],
                [ "id_tiplist",     "INT",    idw, None, "ID Tipo listino", None ],
                [ "id_travet",      "INT",    idw, None, "ID Vettore", None ],
                [ "id_categ",       "INT",    idw, None, "ID Categoria", None ],
                [ "id_status",      "INT",    idw, None, "ID Status", None ],
                [ "id_clifat",      "INT",    idw, None, "ID Cliente fatturazione", None ],
                [ "id_scadgrp",     "INT",    idw, None, "ID Gruppo scadenzario", None ],
                [ "id_bancapag",    "INT",    idw, None, "ID Banca predefinita per incassi", None ],
                [ "id_pdcgrp",      "INT",    idw, None, "ID Cliente griglia prezzi", None ],
                [ "grpstop",        "CHAR",     1, None, "Flag stop inserimento prodotti non in griglia", None ],
                [ "allegcf",        "TINYINT",  1, None, "Flag allegati", None ],
                [ "fido_maxpcf",    "INT",      4, None, "Fido: max partite aperte", None ],
                [ "fido_maxggs",    "INT",      4, None, "Fido: max giorni scoperto più vecchio", None ],
                [ "fido_maximp",    "DECIMAL", 10, DVI,  "Fido: max importo scoperto", None ],
                [ "fido_maxesp",    "DECIMAL", 10, DVI,  "Fido: max esposizione", None ],
                [ "sogritacc",      "TINYINT",  1, None, "Flag soggetto a ritnuta d'acconto", None ],
                [ "perpro",         "DECIMAL",  5, 2,    "Percentuale provvigione", None ],
                [ "ddtstapre",      "TINYINT",  1, None, "Flag stampa prezzi su ddt", None ],
                [ "ddtfixpre",      "TINYINT",  1, None, "Flag blocco scelta stampa prezzi su ddt", None ],
                [ "is_blacklisted", "TINYINT",  1, None, "Flag anagrafica in blacklist paradisi fiscali", None ],
                [ "aziper",         "CHAR",     1, None, "Tipo cliente", None ],
                [ "sm11_cognome",   "VARCHAR", 60, None, "Soggetto estero: cognome", None ],
                [ "sm11_nome",      "VARCHAR", 60, None, "Soggetto estero: nome", None ],
                [ "sm11_nascdat",   "DATE",  None, None, "Soggetto estero: data di nascita", None ],
                [ "sm11_nascprv",   "CHAR",     2, None, "Soggetto estero: provincia di nascita (EE=Estero)", None ],
                [ "sm11_nasccom",   "VARCHAR", 60, None, "Soggetto estero: comune di nascita (o stato se estero)", None ],
                [ "sm11_sedeind",   "VARCHAR", 60, None, "Soggetto estero: persona giuridica - sede legale, indirizzo", None ],
                [ "sm11_sedecit",   "VARCHAR", 60, None, "Soggetto estero: persona giuridica - sede legale, città", None ],
                [ "sm11_sedestt",   "INT",    idw, None, "Soggetto estero: id stato estero sede legale", None ],
                [ "sm11_associa",   "TINYINT",  1, None, "Soggetto estero: flag associa sempre tutte le registrazioni", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_CLIENTI,
                                ((cls.TABSETUP_CONSTR_PDC,     'id_pdc',      cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ZONE,    'id_zona',     cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_AGENTI,  'id_agente',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_VALUTE,  'id_valuta',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ALIQIVA, 'id_aliqiva',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MODPAG,  'id_modpag',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_SPEINC,  'id_speinc',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TIPLIST, 'id_tiplist',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAVET,  'id_travet',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CATCLI,  'id_categ',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_STATCLI, 'id_status',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CLIENTI, 'id_clifat',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_SCADGRP, 'id_scadgrp',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,     'id_bancapag', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.clienti_indexes = [ ["PRIMARY KEY", "id"], ]
            
            
            cls.destin =\
              [ [ "id",         "INT",    idw, None, "ID Destinatario", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "indirizzo",  "VARCHAR", 60, None, "Indirizzo", None ],
                [ "cap",        "CHAR",     5, None, "CAP", None ],
                [ "citta",      "VARCHAR", 60, None, "Città", None ],
                [ "prov",       "CHAR",     2, None, "Provincia", None ],
                [ "numtel",     "VARCHAR", 60, None, "Num. telefono", None ],
                [ "numtel2",    "VARCHAR", 60, None, "Num. telefono agg.", None ],
                [ "numcel",     "VARCHAR", 60, None, "Num. cellulare", None ],
                [ "numfax",     "VARCHAR", 60, None, "Num FAX", None ],
                [ "email",      "VARCHAR", 80, None, "Indirizzo email", None ],
                [ "contatto",   "VARCHAR", 60, None, "Contatto", None ],
                [ "pref",       "TINYINT",  1, None, "Flag destinazione preferita", None ],
                [ "id_pdc",     "INT",    idw, None, "ID Anagrafica di app.", None ] ]
            
            cls.set_constraints(cls.TABNAME_DESTIN,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.destin_indexes = [ ["PRIMARY KEY", "id"],
                                    ["UNIQUE KEY", "id_pdc,codice"],
                                    ["KEY",        "id_pdc,descriz"], ]
            
            
            cls.bancf =\
              [ [ "id",         "INT",    idw, None, "ID Banca del cliente", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "paese",      "CHAR",     2, None, "Paese", None ],
                [ "ciniban",    "CHAR",     2, None, "CIN IBAN", None ],
                [ "cinbban",    "CHAR",     1, None, "CIN BBAN", None ],
                [ "abi",        "CHAR",     5, None, "ABI", None ],
                [ "cab",        "CHAR",     5, None, "CAB", None ],
                [ "numcc",      "VARCHAR", 19, None, "Num. C/C", None ],
                [ "bban",       "VARCHAR", 23, None, "Coord. BBAN", None ],
                [ "iban",       "VARCHAR", 34, None, "Coord. IBAN", None ],
                [ "bic",        "VARCHAR", 11, None, "Codice BIC", None ],
                [ "pref",       "TINYINT",  1, None, "Flag banca preferita", None ],
                [ "id_pdc",     "INT",    idw, None, "ID Anagrafica di app.", None ] ]
            
            cls.set_constraints(cls.TABNAME_BANCF,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.bancf_indexes = [ ["PRIMARY KEY", "id"],
                                   ["UNIQUE KEY",  "id_pdc,descriz"], ]
            
            
            cls.fornit =\
              [ [ "id",             "INT",    idw, None, "ID Fornitore", None ],
                [ "indirizzo",      "VARCHAR", 60, None, "Indirizzo", None ],
                [ "cap",            "CHAR",     8, None, "CAP", None ],
                [ "citta",          "VARCHAR", 60, None, "Città", None ],
                [ "prov",           "CHAR",     2, None, "Provincia", None ],
                [ "codfisc",        "CHAR",    16, None, "Cod. fiscale", None ],
                [ "nazione",        "CHAR",     4, None, "Nazione", None ],
                [ "piva",           "CHAR",    20, None, "Partita IVA", None ],
                [ "numtel",         "VARCHAR", 60, None, "Nmu. telefono", None ],
                [ "numtel2",        "VARCHAR", 60, None, "Num. telefono aggiuntivo", None ],
                [ "numfax",         "VARCHAR", 60, None, "Num. FAX", None ],
                [ "numfax2",        "VARCHAR", 60, None, "Num. FAX aggiuntivo", None ],
                [ "email",          "VARCHAR",120, None, "Indirizzo email", None ],
                [ "siteurl",        "VARCHAR",120, None, "Url sito internet", None ],
                [ "ctt1nome",       "VARCHAR",255, None, "Contatto1: nome", None ],
                [ "ctt1email",      "VARCHAR",255, None, "Contatto1: email", None ],
                [ "ctt1numtel",     "VARCHAR", 60, None, "Contatto1: num.telefono", None ],
                [ "ctt2nome",       "VARCHAR",255, None, "Contatto2: nome", None ],
                [ "ctt2email",      "VARCHAR",255, None, "Contatto2: email", None ],
                [ "ctt2numtel",     "VARCHAR", 60, None, "Contatto2: num.telefono", None ],
                [ "ctt3nome",       "VARCHAR",255, None, "Contatto3: nome", None ],
                [ "ctt3email",      "VARCHAR",255, None, "Contatto3: email", None ],
                [ "ctt3numtel",     "VARCHAR", 60, None, "Contatto3: num.telefono", None ],
                [ "spddes",         "VARCHAR", 60, None, "Descriz. x spedizione documenti", None ],
                [ "spdind",         "VARCHAR", 60, None, "Indirizzo x spedizione documenti", None ],
                [ "spdcap",         "CHAR",     5, None, "CAP x spedizione documenti", None ],
                [ "spdcit",         "VARCHAR", 60, None, "Città x spedizione documenti", None ],
                [ "spdpro",         "CHAR",     2, None, "Provincia x spedizione doc.", None ],
                [ "sconto1",        "DECIMAL",  5,    2, "Sconto perc.1", None ],
                [ "sconto2",        "DECIMAL",  5,    2, "Sconto perc.2", None ],
                [ "sconto3",        "DECIMAL",  5,    2, "Sconto perc.3", None ],
                [ "sconto4",        "DECIMAL",  5,    2, "Sconto perc.4", None ],
                [ "sconto5",        "DECIMAL",  5,    2, "Sconto perc.5", None ],
                [ "sconto6",        "DECIMAL",  5,    2, "Sconto perc.6", None ],
                [ "note",           "VARCHAR",ntw, None, "Annotazioni", None ],
                [ "notepag",        "VARCHAR",ntw, None, "Note per i pagamenti", None ],
                [ "id_stato",       "INT",    idw, None, "ID Stato", None ],
                [ "id_pdc",         "INT",    idw, None, "ID P.d.C. associato", None ],
                [ "id_valuta",      "INT",    idw, None, "ID Valuta", None ],
                [ "id_aliqiva",     "INT",    idw, None, "ID Aliquota IVA", None ],
                [ "id_modpag",      "INT",    idw, None, "ID Mod.pagamento", None ],
                [ "id_speinc",      "INT",    idw, None, "ID Spese incasso", None ],
                [ "id_travet",      "INT",    idw, None, "ID Vettore", None ],
                [ "id_categ",       "INT",    idw, None, "ID Categoria", None ],
                [ "id_zona",        "INT",    idw, None, "ID Zona appartenenza", None ],
                [ "id_status",      "INT",    idw, None, "ID Status", None ],
                [ "id_scadgrp",     "INT",    idw, None, "ID Gruppo scadenzario", None ],
                [ "id_bancapag",    "INT",    idw, None, "ID Banca predefinita per pagamenti", None ],
                [ "id_pdcgrp",      "INT",    idw, None, "ID Fornitore griglia prezzi", None ],
                [ "grpstop",        "CHAR",     1, None, "Flag stop inserimento prodotti non in griglia", None ],
                [ "allegcf",        "TINYINT",  1, None, "Flag allegati", None ],
                [ "is_blacklisted", "TINYINT",  1, None, "Flag anagrafica in blacklist paradisi fiscali", None ],
                [ "aziper",         "CHAR",     1, None, "Tipo cliente", None ], 
                [ "sm11_cognome",   "VARCHAR", 60, None, "Soggetto estero: cognome", None ],
                [ "sm11_nome",      "VARCHAR", 60, None, "Soggetto estero: nome", None ],
                [ "sm11_nascdat",   "DATE",  None, None, "Soggetto estero: data di nascita", None ],
                [ "sm11_nascprv",   "CHAR",     2, None, "Soggetto estero: provincia di nascita (EE=Estero)", None ],
                [ "sm11_nasccom",   "VARCHAR", 60, None, "Soggetto estero: comune di nascita (o stato se estero)", None ],
                [ "sm11_sedeind",   "VARCHAR", 60, None, "Soggetto estero: persona giuridica - sede legale, indirizzo", None ],
                [ "sm11_sedecit",   "VARCHAR", 60, None, "Soggetto estero: persona giuridica - sede legale, città", None ],
                [ "sm11_sedestt",   "INT",    idw, None, "Soggetto estero: id stato estero sede legale", None ],
                [ "sm11_associa",   "TINYINT",  1, None, "Soggetto estero: flag associa sempre tutte le registrazioni", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_FORNIT,
                                ((cls.TABSETUP_CONSTR_PDC,     'id_pdc',      cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_VALUTE,  'id_valuta',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ALIQIVA, 'id_aliqiva',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MODPAG,  'id_modpag',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_SPEINC,  'id_speinc',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAVET,  'id_travet',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CATFOR,  'id_categ',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_STATFOR, 'id_status',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ZONE,    'id_zona',     cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_SCADGRP, 'id_scadgrp',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,     'id_bancapag', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.fornit_indexes = [ ["PRIMARY KEY", "id"], ]
            
            
            cls.casse =\
              [ [ "id",         "INT",    idw, None, "ID Cassa", None ], ]
            
            cls.casse_indexes = [ ["PRIMARY KEY", "id"], ]
            
            
            cls.banche =\
              [ [ "id",         "INT",    idw, None, "ID Banca", None ],
                [ "abi",        "CHAR",     5, None, "ABI", None ],
                [ "cab",        "CHAR",     5, None, "CAB", None ],
                [ "numcc",      "VARCHAR", 12, None, "Num. C/C", None ],
                [ "cin",        "CHAR",     1, None, "Cod. CIN", None ],
                [ "iban",       "VARCHAR", 27, None, "Coord. IBAN", None ],
                [ "sia",        "CHAR",     5, None, "Cod. SIA", None ],
                [ "setif",      "CHAR",     5, None, "Cod. SETIF", None ],
                [ "desriba1",   "VARCHAR", 24, None, "Descriz. x disco riba r.1", None ],
                [ "desriba2",   "VARCHAR", 24, None, "Descriz. x disco riba r.2", None ],
                [ "desriba3",   "VARCHAR", 24, None, "Descriz. x disco riba r.3", None ],
                [ "desriba4",   "VARCHAR", 24, None, "Descriz. x disco riba r.4", None ],
                [ "firmariba",  "VARCHAR", 20, None, "Firma x disco riba", None ],
                [ "provfin",    "VARCHAR", 15, None, "Prov. Finanza", None],
                [ "aubanum",    "VARCHAR", 10, None, "Num. autorizz. banca", None],
                [ "aubadat",    "DATE",  None, None, "Data autorizz. banca", None] ]
            
            cls.banche_indexes = [ ["PRIMARY KEY", "id"], ]
            
            
            cls.contab_h =\
              [ [ "id",         "INT",    idw, None, "ID Registrazione", "AUTO_INCREMENT" ],
                [ "esercizio",  "INT",      4, None, "Flag esercizio", "UNSIGNED NOT NULL" ],
                [ "id_caus",    "INT",    idw, None, "ID causale", None ],
                [ "tipreg",     "CHAR",     1, None, "Tipo di registrazione", None ],
                [ "datreg",     "DATE",  None, None, "Data registrazione", None ],
                [ "datdoc",     "DATE",  None, None, "Data documento", None ],
                [ "numdoc",     "VARCHAR", 20, None, "Numero documento", None ],
                [ "numiva",     "INT",     10, None, "Numero protocollo IVA", None ],
                [ "numreg",     "INT",     10, None, "numero reg. mirage", None ],
                [ "st_regiva",  "TINYINT",  1, None, "Flag stampa registro IVA", "DEFAULT 0" ],
                [ "st_giobol",  "TINYINT",  1, None, "Flag stampa giornale bollato", "DEFAULT 0" ],
                [ "id_valuta",  "INT",    idw, None, "ID Valuta", None ],
                [ "id_regiva",  "INT",    idw, None, "ID Registro IVA associato", None ],
                [ "id_modpag",  "INT",    idw, None, "ID Modalità di pagamento", None ],
                [ "nocalciva",  "TINYINT",  1, None, "Flag inibizione calcolo dav/iva", None ],
                [ "sm_link",    "INT",      6, None, "Chiave di raggruppamento registrazioni per spesometro", None ],
                [ "sm_regrif",  "TINYINT",  1, None, "Flag spesometro registrazione di riferimento per aggregazioni", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_CONTAB_H,
                                ((cls.TABSETUP_CONSTR_CFGCONTAB, 'id_caus',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_VALUTE,    'id_valuta', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_REGIVA,    'id_regiva', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MODPAG,    'id_modpag', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.contab_h_indexes = [ ["PRIMARY KEY", "id"],
                                      ["KEY",        "id_regiva,numiva,numdoc"],
                                      ["KEY",        "datreg,id_regiva,numiva"], ]
            
            
            cls.contab_b =\
              [ [ "id",         "INT",     idw, None, "ID Riga", "AUTO_INCREMENT" ],
                [ "id_reg",     "INT",     idw, None, "ID registrazione", None ],
                [ "numriga",    "INT",       4, None, "Numero di riga", None ],
                [ "tipriga",    "CHAR",      1, None, "Tipo di riga", None ],
                [ "nrigiobol",  "INT",       6, None, "Numero riga stampa giornale", None ],
                [ "importo",    "DECIMAL", IVI,  DVI, "Importo riga", None ],
                [ "imponib",    "DECIMAL", IVI,  DVI, "Imponib [x d.e. ord.]", None ],
                [ "imposta",    "DECIMAL", IVI,  DVI, "Imposta [x d.e. sempl.]", None ],
                [ "indeduc",    "DECIMAL", IVI,  DVI, "Imposta indeducibile", None ],
                [ "davscorp",   "DECIMAL", IVI,  DVI, "Importo da scorporare su sezione dare-avere", None ],
                [ "id_aliqiva", "INT",     idw, None, "ID Aliquota IVA", None ],
                [ "segno",      "CHAR",      1, None, "Segno contabile", None ],
                [ "id_pdcpa",   "INT",     idw, None, "ID Sottoconto partita", "NOT NULL" ],
                [ "id_pdccp",   "INT",     idw, None, "ID Sottoconto c/partita", None ],
                [ "id_pdciva",  "INT",     idw, None, "ID Sottoconto IVA", None ],
                [ "id_pdcind",  "INT",     idw, None, "ID Sottoconto IVA indeducibile", None ],
                [ "note",       "VARCHAR", ntw, None, "Descrizione movimento", None ],
                #[ "importo_ve", "DECIMAL", IVE,  DVE, "Importo in valuta", None ],
                #[ "imponib_ve", "DECIMAL", IVE,  DVE, "Imponibile in valuta", None ],
                #[ "imposta_ve", "DECIMAL", IVE,  DVE, "Imposta in valuta", None ],
                #[ "indeduc_ve", "DECIMAL", IVE,  DVE, "Imposta indeducibile in valuta", None ],
                [ "ivaman",     "TINYINT",   1, None, "Calcolo IVA inibito", None ],
                [ "solocont",   "TINYINT",   1, None, "Flag riga solo contabile", None ], 
                [ "f_sermer",   "CHAR",      1, None, "Flag servizi/merce per spesometro", None ], ]
            
            cls.set_constraints(cls.TABNAME_CONTAB_B,
                                ((cls.TABSETUP_CONSTR_CONTAB_H, 'id_reg',     cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_ALIQIVA,  'id_aliqiva', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,      'id_pdcpa',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,      'id_pdccp',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,      'id_pdciva',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,      'id_pdcind',  cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.contab_b_indexes = [ ["PRIMARY KEY", "id"],
                                     ["KEY",         "id_reg,numriga"],
                                     ["KEY",         "id_pdcpa,id_reg"] ]
            
            
            cls.pcf =\
              [ [ "id",         "INT",     idw, None, "ID Partita", "AUTO_INCREMENT" ],
                [ "id_pdc",     "INT",     idw, None, "ID sottoconto pdc", "NOT NULL" ],
                [ "id_caus",    "INT",     idw, None, "ID causale di origine", None ],
                [ "id_modpag",  "INT",     idw, None, "ID della modalità di pagamento", None ],
                [ "riba",       "TINYINT",   1, None, "Flag riba", None ],
                [ "contrass",   "TINYINT",   1, None, "Flag contrassegno", None ],
                [ "insoluto",   "TINYINT",   1, None, "Flag insoluto", None ],
                [ "datdoc",     "DATE",   None, None, "Data documento", None ],
                [ "numdoc",     "CHAR",     20, None, "Numero documento", None ],
                [ "datscad",    "DATE",   None, None, "Data scadenza", "NOT NULL" ],
                [ "imptot",     "DECIMAL", IVI,  DVI, "Importo fattura della scadenza", None ],
                [ "imppar",     "DECIMAL", IVI,  DVI, "Importo n.c./pag. della scadenza", None ],
                [ "impeff",     "DECIMAL", IVI,  DVI, "Importo effetto", None ],
                [ "note",       "VARCHAR", ntw, None, "Annotazioni scadenza", None ],
                [ "imptot_ve",  "DECIMAL", IVE,  DVE, "Importo fattura della scadenza in valuta estera", None ],
                [ "imppar_ve",  "DECIMAL", IVE,  DVE, "Importo n.c./pag. della scadenza in valuta estera", None ],
                [ "f_effsele",  "TINYINT",   1, None, "Flag effetto selezionato", None ],
                [ "f_effemes",  "TINYINT",   1, None, "Flag effetto emesso", None ],
                [ "f_effcont",  "TINYINT",   1, None, "Flag effetto contabilizzato", None ],
                [ "id_effban",  "INT",     idw, None, "ID banca emittente effetto emesso", None ],
                [ "id_effbap",  "INT",     idw, None, "ID banca appoggio effetto emesso", None ],
                [ "id_effreg",  "INT",     idw, None, "ID reg.contabile effetto", None ],
                [ "id_effpdc",  "INT",     idw, None, "ID sottoconto effetto", None ],
                [ "effdate",    "DATE",   None, None, "Data emissione effetto", None ] ]
            
            cls.set_constraints(cls.TABNAME_PCF,
                                ((cls.TABSETUP_CONSTR_PDC,       'id_pdc',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGCONTAB, 'id_caus',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MODPAG,    'id_modpag', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,       'id_effban', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_BANCF,     'id_effbap', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,       'id_effpdc', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.pcf_indexes = [ ["PRIMARY KEY", "id"],
                                ["KEY",         "id_pdc,datscad"],
                                ["KEY",         "datscad"], ]
            
            
            cls.contab_s =\
              [ [ "id",         "INT",     idw, None, "ID Scadenza", "AUTO_INCREMENT" ],
                [ "id_reg",     "INT",     idw, None, "ID registrazione", "NOT NULL" ],
                [ "datscad",    "DATE",   None, None, "Data scadenza", "NOT NULL" ],
                [ "importo",    "DECIMAL", IVI,  DVI, "Importo della scadenza", "NOT NULL" ],
                [ "importo_ve", "DECIMAL", IVE,  DVE, "Importo della scadenza in valuta estera", None ],
                [ "abbuono",    "DECIMAL", IVI,  DVI, "Importo abbuono per operazioni in saldaconto", None ],
                [ "spesa",      "DECIMAL", IVI,  DVI, "Importo spesa per operazioni in saldaconto", None ],
                [ "f_riba",     "TINYINT",   1, None, "Flag Riba", None ],
                [ "id_pcf",     "INT",     idw, None, "ID della partita collegata", None ],
                [ "note",       "VARCHAR", ntw, None, "Note scadenza", None ],
                [ "tipabb",     "CHAR",      1, None, "Tipo di abbuono", None ] ]
            
            cls.set_constraints(cls.TABNAME_CONTAB_S,
                                ((cls.TABSETUP_CONSTR_PCF, 'id_pcf', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.contab_s_indexes = [ ["PRIMARY KEY", "id"],
                                     ["KEY",         "id_reg,datscad"], ]
            
            
            cls.cfgprogr =\
              [ [ "id",         "INT",    idw, None, "ID Progressivo", "AUTO_INCREMENT" ],
                [ "codice",     "VARCHAR", 20, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "keydiff",    "VARCHAR", 20, None, "Chiave: discriminante", None ],
                [ "key_id",     "INT",    idw, None, "Chiave: ID", None ],
                [ "progrnum",   "INT",    idw, None, "Progressivo: numero", None ],
                [ "progrdate",  "DATE",  None, None, "Progressivo: data", None ],
                [ "progrimp1",  "DECIMAL", 12,  DVI, "Progressivo: importo 1", None ],
                [ "progrimp2",  "DECIMAL", 12,  DVI, "Progressivo: importo 2", None ],
                [ "progrdesc",  "VARCHAR",255, None, "Progressivo: stringa", None ], ]
            
            cls.cfgprogr_indexes = [ ["PRIMARY KEY", "id"],
                                      ["UNIQUE KEY",  "codice,keydiff,key_id"], ]
            
            
            cls.cfgautom =\
              [ [ "id",         "INT",    idw, None, "ID Automatismo", "AUTO_INCREMENT" ],
                [ "codice",     "VARCHAR", 20, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "aut_id",     "INT",    idw, None, "Chiave: ID", None ] ]
            
            cls.cfgautom_indexes = [ ["PRIMARY KEY", "id"],
                                      ["UNIQUE KEY",  "codice"], ]
            
            
            cls.cfgpdcp =\
              [ [ "id",         "INT",    idw, None, "ID Sottoconto preferenziale", "AUTO_INCREMENT" ],
                [ "ambito",     "TINYINT",  1, None, "Ambito preferenza", None ],
                [ "key_id",     "INT",    idw, None, "Id chiave nell'ambito", None ],
                [ "pdcord",     "INT",      3, None, "Ordinamento pdc nell'ambito/chiave", None ],
                [ "id_pdc",     "INT",    idw, None, "Id pdc preferito", None ],
                [ "segno",      "CHAR",     1, None, "Segno D/A", None ], ]
            
            cls.set_constraints(cls.TABNAME_CFGPDCP,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgpdcp_indexes = [ ["PRIMARY KEY", "id"],
                                     ["KEY",         "ambito,key_id"], ]
            
            
            cls.tipart =\
              [ [ "id",         "INT",    idw, None, "ID Tipo articolo", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ] ]
            
            cls.tipart_indexes = cls.std_indexes
            
            
            cls.catart =\
              [ [ "id",         "INT",    idw, None, "ID Categoria merce", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "id_pdcacq",  "INT",    idw, None, "ID Pdc collegamento contabile su acquisti", None ],
                [ "id_pdcven",  "INT",    idw, None, "ID Pdc collegamento contabile su vendite", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_CATART,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdcacq', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC, 'id_pdcven', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.catart_indexes = cls.std_indexes
            
            
            cls.gruart =\
              [ [ "id",         "INT",    idw, None, "ID Gruppo merce", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "id_catart",  "INT",    idw, None, "ID della categoria di appartenenza", None ] ]
            
            cls.set_constraints(cls.TABNAME_GRUART,
                                ((cls.TABSETUP_CONSTR_CATART, 'id_catart', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.gruart_indexes = [ ["PRIMARY KEY", "id"],
                                   ["UNIQUE KEY",  "id_catart,codice"],
                                   ["UNIQUE KEY",  "id_catart,descriz"], ]
            
            
            cls.statart =\
              [ [ "id",           "INT",    idw, None, "ID Status", "AUTO_INCREMENT" ],
                [ "codice",       "CHAR",    10, None, "Codice", None ],
                [ "descriz",      "VARCHAR", 60, None, "Descrizione", None ],
                [ "hidesearch",   "TINYINT",  1, None, "Flag per nascondere nelle ricerche", None ],
                [ "nomov_ordfor", "TINYINT",  1, None, "Flag per impedire l'inserimento negli ordini a fornitore", None ],
                [ "nomov_carfor", "TINYINT",  1, None, "Flag per impedire l'inserimento nei carichi da fornitore", None ],
                [ "nomov_ordcli", "TINYINT",  1, None, "Flag per impedire l'inserimento negli ordini da cliente", None ],
                [ "nomov_vencli", "TINYINT",  1, None, "Flag per impedire l'inserimento nelle vendite a cliente", None ],
            ]
            
            cls.statart_indexes = cls.std_indexes
            
            
            cls.prod =\
              [ [ "id",         "INT",    idw, None, "ID Prodotto", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    16, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ],
                [ "um",         "CHAR",     5, None, "Unità di misura", "NOT NULL" ],
                [ "costo",      "DECIMAL",IPM,  DPM, "Ultimo costo di acquisto", None ],
                [ "prezzo",     "DECIMAL",IPM,  DPM, "Prezzo di listino ufficiale", None ],
                [ "sconto1",    "DECIMAL",  5,    2, "Sconto #1", None ],
                [ "sconto2",    "DECIMAL",  5,    2, "Sconto #2", None ],
                [ "sconto3",    "DECIMAL",  5,    2, "Sconto #3", None ],
                [ "sconto4",    "DECIMAL",  5,    2, "Sconto #4", None ],
                [ "sconto5",    "DECIMAL",  5,    2, "Sconto #5", None ],
                [ "sconto6",    "DECIMAL",  5,    2, "Sconto #6", None ],
                [ "ricar1",     "DECIMAL",  5,    2, "Ricarica #1", None ],
                [ "ricar2",     "DECIMAL",  5,    2, "Ricarica #2", None ],
                [ "ricar3",     "DECIMAL",  5,    2, "Ricarica #3", None ],
                [ "ricar4",     "DECIMAL",  5,    2, "Ricarica #4", None ],
                [ "ricar5",     "DECIMAL",  5,    2, "Ricarica #5", None ],
                [ "ricar6",     "DECIMAL",  5,    2, "Ricarica #6", None ],
                [ "note",       "VARCHAR",ntw, None, "Annotazioni", None ],
                [ "barcode",    "VARCHAR", 20, None, "Barcode", None ],
                [ "codfor",     "VARCHAR", 20, None, "Codice prodotto del fornitore", None ],
                [ "pzconf",     "DECIMAL",  6,  DQM, "Pezzi x confezione", None ],
                [ "kgconf",     "DECIMAL",  8,    3, "Peso confezione", None ],
                [ "dimx",       "DECIMAL",  6,    2, "Dimensione cm.X imballo", None ],
                [ "dimy",       "DECIMAL",  6,    2, "Dimensione cm.Y imballo", None ],
                [ "dimz",       "DECIMAL",  6,    2, "Dimensione cm.Z imballo", None ],
                [ "volume",     "DECIMAL",  8,    5, "Volume m3", None ],
                [ "stetic",     "TINYINT",  1, None, "Flag stampa etichetta", None ],
                [ "descetic",   "VARCHAR", 60, None, "Descrizione x etichetta", None ],
                [ "descextra",  "VARCHAR", 60, None, "Descrizione extra x stampe listini", None ],
                [ "perpro",     "DECIMAL",  5,    2, "Percentuale di provvigione", None ],
                [ "scomin",     "DECIMAL",IQM,  DQM, "Scorta minima", None ],
                [ "scomax",     "DECIMAL",IQM,  DQM, "Scorta massima", None ],
                [ "scaffale",   "VARCHAR", 20, None, "Posizione negli scaffali", None ],
                [ "id_aliqiva", "INT",    idw, None, "ID aliquota IVA", None ],
                [ "id_tipart",  "INT",    idw, None, "ID tipo articolo", None ],
                [ "id_catart",  "INT",    idw, None, "ID categoria merce", None ],
                [ "id_gruart",  "INT",    idw, None, "ID gruppo merce", None ],
                [ "id_fornit",  "INT",    idw, None, "ID fornitore", None ],
                [ "id_status",  "INT",    idw, None, "ID status", None ],
                [ "id_marart",  "INT",    idw, None, "ID marca", None ],
                [ "id_gruprez", "INT",    idw, None, "ID gruppo prezzi", None ],
                [ "id_pdcacq",  "INT",    idw, None, "ID Pdc collegamento contabile su acquisti", None ],
                [ "id_pdcven",  "INT",    idw, None, "ID Pdc collegamento contabile su vendite", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_PROD,
                                ((cls.TABSETUP_CONSTR_ALIQIVA, 'id_aliqiva', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TIPART,  'id_tipart',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CATART,  'id_catart',  cls.TABCONSTRAINT_TYPE_SETNULL),
                                 (cls.TABSETUP_CONSTR_GRUART,  'id_gruart',  cls.TABCONSTRAINT_TYPE_SETNULL),
                                 (cls.TABSETUP_CONSTR_PDC,     'id_fornit',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_STATART, 'id_status',  cls.TABCONSTRAINT_TYPE_SETNULL),
                                 (cls.TABSETUP_CONSTR_MARART,  'id_marart',  cls.TABCONSTRAINT_TYPE_SETNULL),
                                 (cls.TABSETUP_CONSTR_GRUPREZ, 'id_gruprez', cls.TABCONSTRAINT_TYPE_SETNULL),
                                 (cls.TABSETUP_CONSTR_PDC,     'id_pdcacq',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,     'id_pdcven',  cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.prod_indexes = [ ["PRIMARY KEY", "id"],
                                 ["UNIQUE KEY",  "codice"],
                                 ["KEY",         "id_tipart,descriz"], ]
            
            
            cls.codartcf =\
              [ [ "id",         "INT",    idw, None, "ID Codice fornitore", "AUTO_INCREMENT" ],
                [ "id_prod",    "INT",    idw, None, "ID Prodotto", "NOT NULL" ],
                [ "id_pdc",     "INT",    idw, None, "ID Cliente/Fornitore", None ],
                [ "datins",     "DATE",  None, None, "Data inserimento", None ],
                [ "codice",     "CHAR",    20, None, "Codice articolo del fornitore", None ],
                [ "barcode",    "CHAR",    20, None, "Barcode articolo del fornitore", None ],
                [ "predef",     "TINYINT",  1, None, "Codice attuale del fornitore", None ] ]
            
            cls.set_constraints(cls.TABNAME_CODARTCF,
                                ((cls.TABSETUP_CONSTR_PROD, 'id_prod', cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_PDC,  'id_pdc',  cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.codartcf_indexes = [ ["PRIMARY KEY", "id"],
                                     ["KEY",  "id_prod,id_pdc"],
                                     ["KEY",  "id_pdc,id_prod"], ]
            
            
            cls.listini =\
              [ [ "id",         "INT",     idw, None, "ID Listino", "AUTO_INCREMENT" ],
                [ "id_prod",    "INT",     idw, None, "ID Prodotto", "NOT NULL" ],
                [ "id_valuta",  "INT",     idw, None, "ID Valuta", None ],
                [ "data",       "DATE",   None, None, "Data di validità", None ],
                [ "prezzo1",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #1", None ],
                [ "prezzo2",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #2", None ],
                [ "prezzo3",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #3", None ],
                [ "prezzo4",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #4", None ],
                [ "prezzo5",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #5", None ],
                [ "prezzo6",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #6", None ],
                [ "prezzo7",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #7", None ],
                [ "prezzo8",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #8", None ],
                [ "prezzo9",    "DECIMAL", IPM,  DPM, "Prezzo di vendita #9", None ],
                [ "scolis1",    "DECIMAL",  5,    2, "Sconto #1", None ],
                [ "scolis2",    "DECIMAL",  5,    2, "Sconto #2", None ],
                [ "scolis3",    "DECIMAL",  5,    2, "Sconto #3", None ],
                [ "scolis4",    "DECIMAL",  5,    2, "Sconto #4", None ],
                [ "scolis5",    "DECIMAL",  5,    2, "Sconto #5", None ],
                [ "scolis6",    "DECIMAL",  5,    2, "Sconto #6", None ],
                [ "scolis7",    "DECIMAL",  5,    2, "Sconto #7", None ],
                [ "scolis8",    "DECIMAL",  5,    2, "Sconto #8", None ],
                [ "scolis9",    "DECIMAL",  5,    2, "Sconto #9", None ],
                [ "riclis1",    "DECIMAL",  5,    2, "Ricarica #1", None ],
                [ "riclis2",    "DECIMAL",  5,    2, "Ricarica #2", None ],
                [ "riclis3",    "DECIMAL",  5,    2, "Ricarica #3", None ],
                [ "riclis4",    "DECIMAL",  5,    2, "Ricarica #4", None ],
                [ "riclis5",    "DECIMAL",  5,    2, "Ricarica #5", None ],
                [ "riclis6",    "DECIMAL",  5,    2, "Ricarica #6", None ],
                [ "riclis7",    "DECIMAL",  5,    2, "Ricarica #7", None ],
                [ "riclis8",    "DECIMAL",  5,    2, "Ricarica #8", None ],
                [ "riclis9",    "DECIMAL",  5,    2, "Ricarica #9", None ],
                [ "note",       "VARCHAR", ntw, None, "Note", None ], ]
            
            cls.set_constraints(cls.TABNAME_LISTINI,
                                ((cls.TABSETUP_CONSTR_PROD,   'id_prod',   cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_VALUTE, 'id_valuta', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.listini_indexes = [ ["PRIMARY KEY", "id"],
                                     ["UNIQUE KEY",  "id_prod,data"], ]
            
            
            cls.griglie =\
              [ [ "id",          "INT",    idw, None, "ID Griglia", "AUTO_INCREMENT" ],
                [ "id_prod",     "INT",    idw, None, "ID Prodotto", "NOT NULL" ],
                [ "id_pdc",      "INT",    idw, None, "ID Cliente/Fornitore", "NOT NULL" ],
                [ "data",        "DATE",  None, None, "Data di validità", None ],
                [ "prezzo",      "DECIMAL", 12,  DPM, "Prezzo di griglia", None ],
                [ "sconto1",     "DECIMAL",  5,    2, "Sconto #1", None ],
                [ "sconto2",     "DECIMAL",  5,    2, "Sconto #2", None ],
                [ "sconto3",     "DECIMAL",  5,    2, "Sconto #3", None ],
                [ "sconto4",     "DECIMAL",  5,    2, "Sconto #4", None ],
                [ "sconto5",     "DECIMAL",  5,    2, "Sconto #5", None ],
                [ "sconto6",     "DECIMAL",  5,    2, "Sconto #6", None ],
                [ "prebloc",     "TINYINT",  1, None, "Flag blocco prezzo", None ],
                [ "pzconf",      "DECIMAL",  6,  DQM, "Pezzi per confezione specifici dell'anagrafica", None ],
                [ "ext_codice",  "VARCHAR", 20, None, "Codice prodotto del cliente/fornitore", None ],
                [ "ext_descriz", "VARCHAR", 60, None, "Descrizione prodotto del cliente/fornitore", None ],
                 ]
            
            cls.set_constraints(cls.TABNAME_GRIGLIE,
                                ((cls.TABSETUP_CONSTR_PROD, 'id_prod', cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_PDC,  'id_pdc',  cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.griglie_indexes = [ ["PRIMARY KEY", "id"],
                                     ["UNIQUE KEY",  "id_prod,id_pdc,data"], ]
            
            
            cls.magazz =\
              [ [ "id",         "INT",    idw, None, "ID Magazzino", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "id_pdc",     "INT",    idw, None, "ID sottoconto associato", None ] ]
            
            cls.set_constraints(cls.TABNAME_MAGAZZ,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.magazz_indexes = cls.std_indexes
            
            
            cls.cfgmagdoc =\
              [ [ "id",         "INT",    idw, None, "ID Documento", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ],
                [ "valuta",     "CHAR",     1, None, "Flag documento in valuta", None ],
                [ "id_pdctip",  "INT",    idw, None, "ID Tipo sottoconto", None ],
                [ "descanag",   "VARCHAR", 30, None, "Descrizione tipo sottoconto", None ],
                [ "datdoc",     "CHAR",     1, None, "Flag tipo data documento", None ],
                [ "numdoc",     "CHAR",     1, None, "Flag tipo numero documento", None ],
                [ "numest",     "CHAR",     1, None, "Flag tipo numerazione esterna", None ],
                [ "docfam",     "CHAR",    10, None, "Famiglia documenti", None ],
                [ "ctrnum",     "CHAR",     1, None, "Flag controllo numero documento", None ],
                [ "aggnum",     "CHAR",     1, None, "Flag aggiornamento numero documento", None ],
                [ "pienum",     "CHAR",     1, None, "Flag numrazione a piede documento", None ],
                [ "id_acqdoc1", "INT",    idw, None, "ID Documento da acquisire #1", None ],
                [ "id_acqdoc2", "INT",    idw, None, "ID Documento da acquisire #2", None ],
                [ "id_acqdoc3", "INT",    idw, None, "ID Documento da acquisire #3", None ],
                [ "id_acqdoc4", "INT",    idw, None, "ID Documento da acquisire #4", None ],
                [ "tipacq1",    "CHAR",     1, None, "Flag tipo acquisizione documento #1", None ],
                [ "tipacq2",    "CHAR",     1, None, "Flag tipo acquisizione documento #2", None ],
                [ "tipacq3",    "CHAR",     1, None, "Flag tipo acquisizione documento #3", None ],
                [ "tipacq4",    "CHAR",     1, None, "Flag tipo acquisizione documento #4", None ],
                [ "annacq1",    "TINYINT",  1, None, "Flag annullamento documento acquisito #1", None ],
                [ "annacq2",    "TINYINT",  1, None, "Flag annullamento documento acquisito #2", None ],
                [ "annacq3",    "TINYINT",  1, None, "Flag annullamento documento acquisito #3", None ],
                [ "annacq4",    "TINYINT",  1, None, "Flag annullamento documento acquisito #4", None ],
                [ "checkacq1",  "TINYINT",  1, None, "Flag check documenti da acquisire #1", None ],
                [ "checkacq2",  "TINYINT",  1, None, "Flag check documenti da acquisire #2", None ],
                [ "checkacq3",  "TINYINT",  1, None, "Flag check documenti da acquisire #3", None ],
                [ "checkacq4",  "TINYINT",  1, None, "Flag check documenti da acquisire #4", None ],
                [ "askmagazz",  "CHAR",     1, None, "Flag richiesta magazzino", None ],
                [ "id_magazz",  "INT",    idw, None, "ID magazzino fisso", None ],
                [ "askmodpag",  "CHAR",     1, None, "Flag richiesta mod.pagamento", None ],
                [ "id_modpag",  "INT",    idw, None, "ID Mod.Pagamento", None ],
                [ "askmpnoeff", "CHAR",     1, None, "Flag inibizione mod.pagamento di tipo effetto", None ],
                [ "askdestin",  "CHAR",     1, None, "Flag richiesta destinatario", None ],
                [ "askrifdesc", "CHAR",     1, None, "Flag richiesta descrizione riferimento", None ],
                [ "askrifdata", "CHAR",     1, None, "Flag richiesta data riferimento", None ],
                [ "askrifnum",  "CHAR",     1, None, "Flag richiesta numero riferimento", None ],
                [ "askagente",  "CHAR",     1, None, "Flag richiesta agente", None ],
                [ "askzona",    "CHAR",     1, None, "Flag richiesta zona", None ],
                [ "asklist",    "CHAR",     1, None, "Flag richiesta listino", None ],
                [ "rowlist",    "CHAR",     1, None, "Flag richiesta listino su riga", None ],
                [ "askbanca",   "CHAR",     1, None, "Flag richiesta banca", None ],
                [ "askdatiacc", "CHAR",     1, None, "Flag richiesta dati trasporto", None ],
                [ "asktracau",  "CHAR",     1, None, "Flag richiesta dati trasporto: causale", None ],
                [ "id_tracau",  "INT",    idw, None, "ID causale trasporto", None ],
                [ "asktracur",  "CHAR",     1, None, "Flag richiesta dati trasporto: a cura", None ],
                [ "id_tracur",  "INT",    idw, None, "ID trasporto a cura", None ],
                [ "asktravet",  "CHAR",     1, None, "Flag richiesta dati trasporto: vettore", None ],
                [ "id_travet",  "INT",    idw, None, "ID trasporto vettore", None ],
                [ "asktraasp",  "CHAR",     1, None, "Flag richiesta dati trasporto: aspetto", None ],
                [ "id_traasp",  "INT",    idw, None, "ID traporto aspetto beni", None ],
                [ "asktrapor",  "CHAR",     1, None, "Flag richiesta dati trasporto: porto", None ],
                [ "id_trapor",  "INT",    idw, None, "ID trasporto tipo di porto", None ],
                [ "asktracon",  "CHAR",     1, None, "Flag richiesta dati trasporto: contrassegno", None ],
                [ "id_tracon",  "INT",    idw, None, "ID trasporto tipo contrassegno", None ],
                [ "asktrakgc",  "CHAR",     1, None, "Flag richiesta dati trasporto: peso e colli", None ],
                [ "colcg",      "CHAR",     1, None, "Flag collegamento contabile", None ],
                [ "id_caucg",   "INT",    idw, None, "ID Causale contabile", None ],
                [ "id_tdoctra", "INT",    idw, None, "ID Tipo documento da generare per trasferimento", None ],
                [ "askprotiva", "CHAR",     1, None, "Flag richiesta protocollo IVA", None ],
                [ "scorpiva",   "CHAR",     1, None, "Flag scorporo IVA", None ],
                [ "totali",     "CHAR",     1, None, "Flag visualizzazione totali", None ],
                [ "totzero",    "CHAR",     1, None, "Flag permesso totale documento nullo", None ],
                [ "totneg",     "CHAR",     1, None, "Flag permesso totale documento negativo", None ],
                [ "tiposta",    "CHAR",     2, None, "Tipo stampa", None ],
                [ "staobb",     "CHAR",     1, None, "Flag stampa obbligatoria", None ],
                [ "stanoc",     "CHAR",     1, None, "Flag stampa non contabile", None ],
                [ "provvig",    "TINYINT",  1, None, "Flag calcolo provvigioni agenti", None ],
                [ "toolprint",  "VARCHAR", 20, None, "Nome tool stampa documento", None ],
                [ "toolbarra",  "CHAR",     1, None, "Numerazione /X per tool stampa documento", None ],
                [ "staintest",  "CHAR",     1, None, "Flag stampa intestazione azienda", None ],
                [ "stalogo",    "CHAR",     1, None, "Flag stampa logo azienda", None ],
                [ "viscosto",   "TINYINT",  1, None, "Flag visualizzazione costo prodotto", None ],
                [ "visgiac",    "TINYINT",  1, None, "Flag visualizzazione giacenza prodotto", None ],
                [ "vislistini", "TINYINT",  1, None, "Flag visualizzazione prezzi listino prodotto", None ],
                [ "visultmov",  "TINYINT",  1, None, "Flag visualizzazione ultimi movimenti prod/cli-for", None ],
                [ "vismargine", "TINYINT",  1, None, "Flag visualizzazione margine vendita", None ],
                [ "ultmovbef",  "TINYINT",  1, None, "Flag priorità ultimi movimenti prod/cli-for", "NOT NULL DEFAULT 0" ],
                [ "printetic",  "TINYINT",  1, None, "Flag stampa etichette", "NOT NULL DEFAULT 0" ],
                [ "pdcdamag",   "TINYINT",  1, None, "Flag sottoconto da magazzino", None ],
                [ "checkfido",  "TINYINT",  1, None, "Flag controllo fido cliente", None ],
                [ "sogritacc",  "TINYINT",  1, None, "Flag gestione ritenuta d'acconto", None ],
                [ "id_pdc_ra",  "INT",    idw, None, "ID sottoconto per ritenuta d'acconto", None ],
                [ "autoqtaonbc","TINYINT",  1, None, "Flag auto quantita' su lettura barcode", None ],
                [ "printer",    "CHAR",    60, None, "Nome stampante da usare, se prefissata", None ],
                [ "copies",     "INT",      3, None, "Numero copie x stampe dirette", None ],
                [ "custde",     "VARCHAR", 44, None, "Sigla personalizzazione immissione", None ],
                [ "docemail",   "TINYINT",  1, None, "Flag documento da inviare per email", None ],
                [ "txtemail",   "VARCHAR", ntw, None, "Flag documento da inviare per email", None ],
                [ "clasdoc",    "CHAR",     6, None, "Classificazione documento: ordfor, carfor, ordcli, vencli", None ],
                [ "askstapre",  "CHAR",     1, None, "Flag richiesta stampa prezzi in stampa documento", None ],
                [ "askstaint",  "CHAR",     1, None, "Flag richiesta stampa intestazioni in stampa", None ],
                [ "numsconti",  "TINYINT",  1, None, "Numero di sconti da gestire se diverso da setup azienda", None ],
                [ "nonumxmag",  "TINYINT",  1, None, "Flag numerazione non dipendente da magazzino", None ],
                [ "noivaprof",  "TINYINT",  1, None, "Flag accorpamento iva su c/partita se causale non iva in reg. contabile", None ],
                [ "rptcolli",   "TINYINT",  1, None, "Flag stampa segnacolli", None ],
                [ "aanotedoc",  "TINYINT",  1, None, "Flag inibizione note documento da anagrafica", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_CFGMAGDOC,
                                ((cls.TABSETUP_CONSTR_PDCTIP,    'id_pdctip',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_acqdoc1', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_acqdoc2', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_acqdoc3', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_acqdoc4', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRACAU,    'id_tracau',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRACUR,    'id_tracur',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAVET,    'id_travet',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAASP,    'id_traasp',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAPOR,    'id_trapor',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRACON,    'id_tracon',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGCONTAB, 'id_caucg',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_tdoctra', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,       'id_pdc_ra',  cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgmagdoc_indexes = cls.std_indexes
            
            
            cls.cfgmagmov =\
              [ [ "id",           "INT",    idw, None, "ID Documento", "AUTO_INCREMENT" ],
                [ "codice",       "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",      "VARCHAR", 60, None, "Descrizione", "NOT NULL" ],
                [ "id_tipdoc",    "INT",    idw, None, "ID Documento di appartenenza", None ],
                [ "aggcosto",     "CHAR",     1, None, "Flag aggiornamento costo", None ],
                [ "aggprezzo",    "CHAR",     1, None, "Flag aggiornamento prezzo", None ],
                [ "agggrip",      "CHAR",     1, None, "Flag aggiornamento prezzo griglia clienti/fornitori", None ],
                [ "riccosto",     "CHAR",     1, None, "Flag ricalcolo costo da gruppo prezzi", None ],
                [ "riccostosr",   "CHAR",     1, None, "Flag uso sconti riga per ricalcolo costo", None ],
                [ "ricprezzo",    "CHAR",     1, None, "Flag ricalcolo prezzo al pubblico da gruppo prezzi", None ],
                [ "riclist",      "CHAR",     1, None, "Flag ricalcolo listini vendita da gruppo prezzi", None ],
                [ "newlist",      "CHAR",     1, None, "Flag creazione listini vendita da gruppo prezzi", None ],
                [ "aggini",       "TINYINT",  1, None, "Flag +/- aggiornamento giacenza iniziale", None ],
                [ "agginiv",      "TINYINT",  1, None, "Flag +/- aggiornamento valore giacenza iniziale", None ],
                [ "aggcar",       "TINYINT",  1, None, "Flag +/- aggiornamento carichi", None ],
                [ "aggcarv",      "TINYINT",  1, None, "Flag +/- aggiornamento valore carichi", None ],
                [ "aggsca",       "TINYINT",  1, None, "Flag +/- aggiornamento scarichi", None ],
                [ "aggscav",      "TINYINT",  1, None, "Flag +/- aggiornamento valore scarichi", None ],
                [ "aggordcli",    "TINYINT",  1, None, "Flag +/- aggiornamento ordini cliente", None ],
                [ "aggordfor",    "TINYINT",  1, None, "Flag +/- aggiornamento ordini fornitore", None ],
                [ "aggfornit",    "CHAR",     1, None, "Flag aggiornamento fornitore", None ],
                [ "aggcvccar",    "TINYINT",  1, None, "Flag +/- aggiornamento carichi c/vendita clienti", None ],
                [ "aggcvcsca",    "TINYINT",  1, None, "Flag +/- aggiornamento scarichi c/vendita clienti", None ],
                [ "aggcvfcar",    "TINYINT",  1, None, "Flag +/- aggiornamento carichi c/vendita fornitori", None ],
                [ "aggcvfsca",    "TINYINT",  1, None, "Flag +/- aggiornamento scarichi c/vendita fornitori", None ],
                [ "statftcli",    "TINYINT",  1, None, "Flag +/- statistica fatturato clienti (vendita)", None ],
                [ "statcscli",    "TINYINT",  1, None, "Flag +/- statistica fatturato clienti (costo)", None ],
                [ "statftfor",    "TINYINT",  1, None, "Flag +/- statistica fatturato fornitori", None ],
                [ "mancosto",     "CHAR",     1, None, "Management costo riga (N/V/M = nulla,visualizza,modifica)", None ],
                [ "askvalori",    "CHAR",     1, None, "Flag richiesta quantità", None ],
                [ "id_pdc",       "INT",    idw, None, "ID Sottoconto per collegamento contabile", None ],
                [ "stadesc",      "VARCHAR", 30, None, "Descrizione in stampa", None ],
                [ "tipvaluni",    "CHAR",     1, None, "Tipo di valore unitario da proporre", None ],
                [ "tipsconti",    "CHAR",     1, None, "Tipo di sconti da proporre", None ],
                [ "noprint",      "CHAR",     1, None, "Flag esclusione righe da stampa documento", None ],
                [ "tipologia",    "CHAR",     1, None, "Tipologia movimento", None ],
                [ "f_acqpdt",     "TINYINT",  1, None, "Flag acquisizione righe da letture pdt", None ],
                [ "proobb",       "TINYINT",  1, None, "Flag provvigione obbligatoria se prodotto non codificato", None ],
                [ "noprovvig",    "TINYINT",  1, None, "Flag esclusione da calcolo provvigioni", None ],
                [ "tqtaxpeso",    "TINYINT",  1, None, "Flag totalizzazione qta righe per tot. peso", None ],
                [ "tqtaxcolli",   "TINYINT",  1, None, "Flag totalizzazione qta righe per tot. colli", None ],
                [ "lendescriz",   "INT",      4, None, "Numero caratteri editabili in campo descrizione", None ],
                [ "prtdestot",    "CHAR",    15, None, "Descrizione riga totale pdc/iva (solo x semplif.)", None ],
                [ "is_acconto",   "TINYINT",  1, None, "Flag acconto: incremento (fattura acconto)", None ],
                [ "is_accstor",   "TINYINT",  1, None, "Flag acconto: decremento (storno acconto)", None ],
                [ "acc_sepiva",   "TINYINT",  1, None, "Flag acconto: storno separato su totali iva", None ],
                [ "canprezzo0",   "TINYINT",  1, None, "Flag permesso prezzo nullo", None ],
                [ "modimpricalc", "CHAR",     1, None, "Flag tipo ricalcolo se modifica importo", None ],
                [ "nomastroprod", "TINYINT",  1, None, "Flag esclusione movimenti in mastro prodotto", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_CFGMAGMOV,
                                ((cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_tipdoc', cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_PDC,       'id_pdc',    cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgmagmov_indexes = [ ["PRIMARY KEY", "id"],
                                      ["UNIQUE KEY",  "id_tipdoc,codice"], ]
            
            
            cls.movmag_h =\
              [ [ "id",                   "INT",       idw, None, "ID Documento", "AUTO_INCREMENT" ],
                [ "datreg",               "DATE",     None, None, "Data registrazione", "NOT NULL" ],
                [ "datdoc",               "DATE",     None, None, "Data documento", "NOT NULL" ],
                [ "numdoc",               "INT",        10, None, "Numero documento", "NOT NULL" ],
                [ "numiva",               "INT",        10, None, "Numero protocollo IVA", None ],
                [ "datrif",               "DATE",     None, None, "Data riferimento", None ],
                [ "numrif",               "CHAR",       10, None, "Numero riferimento", None ],
                [ "desrif",               "VARCHAR",    60, None, "Descrizione riferimento", None ],
                [ "notedoc",              "VARCHAR",   ntw, None, "Note piede documento", None ],
                [ "notevet",              "VARCHAR",   ntw, None, "Note per il vettore", None ],
                [ "noteint",              "VARCHAR",   ntw, None, "Note interne", None ],
                [ "sconto1",              "DECIMAL",     4,    2, "Sconto perc.1", None ],
                [ "sconto2",              "DECIMAL",     4,    2, "Sconto perc.2", None ],
                [ "sconto3",              "DECIMAL",     4,    2, "Sconto perc.3", None ],
                [ "sconto4",              "DECIMAL",     4,    2, "Sconto perc.4", None ],
                [ "sconto5",              "DECIMAL",     4,    2, "Sconto perc.5", None ],
                [ "sconto6",              "DECIMAL",     4,    2, "Sconto perc.6", None ],
                [ "totimponib",           "DECIMAL",   IVI,  DVI, "Totale imponibile", None ],
                [ "totimposta",           "DECIMAL",   IVI,  DVI, "Totale imposta", None ],
                [ "totimporto",           "DECIMAL",   IVI,  DVI, "Totale documento", None ],
                [ "sogritacc",            "TINYINT",     1, None, "Flag documento soggetto a ritenuta d'acconto", None ],
                [ "perritacc",            "DECIMAL",     4,    2, "Percentuale di ritenuta d'acconto", None ],
                [ "comritacc",            "DECIMAL",     5,    2, "Percentuale dell'importo su cui applicare la ritenuta d'acconto", None ],
                [ "impritacc",            "DECIMAL",   IVI,  DVI, "Importo su cui applicare la ritenuta d'acconto", None ],
                [ "totritacc",            "DECIMAL",   IVI,  DVI, "Importo della ritenuta d'acconto", None ],
                [ "totdare",              "DECIMAL",   IVI,  DVI, "Totale dare", None ],
                [ "totmerce",             "DECIMAL",   IVI,  DVI, "Totale imponibile merce", None ],
                [ "totservi",             "DECIMAL",   IVI,  DVI, "Totale imponibile servizi", None ],
                [ "tottrasp",             "DECIMAL",   IVI,  DVI, "Totale imponibile trasporti", None ],
                [ "totspese",             "DECIMAL",   IVI,  DVI, "Totale imponibile spese incasso", None ],
                [ "totscrip",             "DECIMAL",   IVI,  DVI, "Totale imponibile sconti ripartiti", None ],
                [ "totscmce",             "DECIMAL",   IVI,  DVI, "Totale imponibile sconti in merce", None ],
                [ "totomagg",             "DECIMAL",   IVI,  DVI, "Totale imponibile merce in omaggio", None ],
                [ "totpeso",              "DECIMAL",     6,    3, "Trasporto: Totale peso", None ],
                [ "totcolli",             "INT",         6, None, "Trasporto: Totale colli", None ],
                [ "impcontr",             "DECIMAL",   IVI,  DVI, "Importo del contrassegno", None ],
                [ "id_tipdoc",            "INT",       idw, None, "ID Tipo documento", None ],
                [ "id_valuta",            "INT",       idw, None, "ID Valuta", None ],
                [ "id_magazz",            "INT",       idw, None, "ID Magazzino", None ],
                [ "id_pdc",               "INT",       idw, None, "ID Sottoconto pdc del documento", None ],
                [ "id_modpag",            "INT",       idw, None, "ID Mod.pagamento", None ],
                [ "id_bancf",             "INT",       idw, None, "ID Banca del cliente/fornitore", None ],
                [ "id_speinc",            "INT",       idw, None, "ID Tipo spese di incasso", None ],
                [ "id_dest",              "INT",       idw, None, "ID Destinatario", None ],
                [ "id_agente",            "INT",       idw, None, "ID Agente", None ],
                [ "id_zona",              "INT",       idw, None, "ID Zona", None ],
                [ "id_tiplist",           "INT",       idw, None, "ID Tipo listino", None ],
                [ "id_tracau",            "INT",       idw, None, "ID Trasporto: Causale", None ],
                [ "id_tracur",            "INT",       idw, None, "ID Trasporto: A cura", None ],
                [ "id_travet",            "INT",       idw, None, "ID Trasporto: Vettore", None ],
                [ "id_traasp",            "INT",       idw, None, "ID Trasporto: Aspetto", None ],
                [ "id_trapor",            "INT",       idw, None, "ID Trasporto: Porto", None ],
                [ "id_tracon",            "INT",       idw, None, "ID Trasporto: Tipo incasso contrass.", None ],
                [ "id_aliqiva",           "INT",       idw, None, "ID Aliquota IVA particolare", None ],
                [ "id_reg",               "INT",       idw, None, "ID Registrazione contabile", None ],
                [ "id_doctra",            "INT",       idw, None, "ID documento generato per trasferimento", None ],
                [ "id_docaccfor",         "INT",       idw, None, "ID documento per il quale questo documento è un acconto", None ],
                [ "f_ann",                "TINYINT",     1, None, "Flag documento annullato", "NOT NULL DEFAULT 0" ],
                [ "f_acq",                "TINYINT",     1, None, "Flag documento acquisito", "NOT NULL DEFAULT 0" ],
                [ "f_genrag",             "TINYINT",     1, None, "Flag documento generato da raggruppamento", "NOT NULL DEFAULT 0" ],
                [ "id_docacq",            "INT",       idw, None, "ID documento acquisito da raggruppamento", None ],
                [ "f_printed",            "TINYINT",     1, None, "Flag documento stampato", None ],
                [ "f_emailed",            "TINYINT",     1, None, "Flag documento spedito x email", None ],
                [ "initrasp",             "DATETIME", None, None, "Data e ora inizio trasporto", None ], ]
            
            if cls.MAGNOCODEDES:
                cls.movmag_h += [\
                [ "enable_nocodedes",     "TINYINT",  None, None, "Destinatario non codificato: flag attivazione", None ],
                [ "nocodedes_descriz",    "VARCHAR",    60, None, "Destinatario non codificato: Descrizione", None ],
                [ "nocodedes_indirizzo",  "VARCHAR",    60, None, "Destinatario non codificato: Indirizzo", None ],
                [ "nocodedes_cap",        "CHAR",        5, None, "Destinatario non codificato: CAP", None ],
                [ "nocodedes_citta",      "VARCHAR",    60, None, "Destinatario non codificato: Città", None ],
                [ "nocodedes_prov",       "CHAR",        2, None, "Destinatario non codificato: Provincia", None ],
                [ "nocodedes_id_stato",   "INT",       idw, None, "Destinatario non codificato: ID stato", None ], ]
            
            if cls.MAGNOCODEVET:
                cls.movmag_h += [\
                [ "enable_nocodevet",     "TINYINT",  None, None, "Vettore non codificato: flag attivazione", None ],
                [ "nocodevet_descriz",    "VARCHAR",    60, None, "Vettore non codificato: Descrizione", None ],
                [ "nocodevet_indirizzo",  "VARCHAR",    60, None, "Vettore non codificato: Indirizzo", None ],
                [ "nocodevet_cap",        "CHAR",        5, None, "Vettore non codificato: CAP", None ],
                [ "nocodevet_citta",      "VARCHAR",    60, None, "Vettore non codificato: Città", None ],
                [ "nocodevet_prov",       "CHAR",        2, None, "Vettore non codificato: Provincia", None ],
                [ "nocodevet_id_stato",   "INT",       idw, None, "Vettore non codificato: ID stato", None ], 
                [ "nocodevet_codfisc",    "CHAR",       16, None, "Vettore non codificato: Cod. fiscale", None ],
                [ "nocodevet_nazione",    "CHAR",        4, None, "Vettore non codificato: Nazione", None ],
                [ "nocodevet_piva",       "CHAR",       20, None, "Vettore non codificato: Partita IVA", None ], ]
                if cls.MAGEXTRAVET:
                    cls.movmag_h += [\
                    ["nocodevet_targa",   "VARCHAR",    16, None, "Vettore non codificato: targa", None ],
                    ["nocodevet_autista", "VARCHAR",    64, None, "Vettore non codificato: autista", None ],
                    ["nocodevet_dichiar", "VARCHAR",   ntw, None, "Vettore non codificato: dichiarazione", None ], ]
            
            cls.set_constraints(cls.TABNAME_MOVMAG_H,
                                ((cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_tipdoc',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_VALUTE,    'id_valuta',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MAGAZZ,    'id_magazz',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,       'id_pdc',     cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MODPAG,    'id_modpag',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_BANCF,     'id_bancf',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_SPEINC,    'id_speinc',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_DESTIN,    'id_dest',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_AGENTI,    'id_agente',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ZONE,      'id_zona',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TIPLIST,   'id_tiplist', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRACAU,    'id_tracau',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRACUR,    'id_tracur',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAVET,    'id_travet',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAASP,    'id_traasp',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRAPOR,    'id_trapor',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_TRACON,    'id_tracon',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ALIQIVA,   'id_aliqiva', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.movmag_h_indexes = [ ["PRIMARY KEY", "id"],
                                      ["UNIQUE KEY",  "id_magazz,datdoc,id_pdc,id_tipdoc,numdoc"], 
                                      ["KEY",         "id_pdc,datdoc,id_tipdoc,numdoc"], ]
            
            
            cls.movmag_b =\
              [ [ "id",         "INT",     idw, None, "ID Movimento", "AUTO_INCREMENT" ],
                [ "id_doc",     "INT",     idw, None, "ID Documento appartenenza", "NOT NULL" ],
                [ "id_tipmov",  "INT",     idw, None, "ID Tipo mocumento", "NOT NULL" ],
                [ "numriga",    "INT",      10, None, "Numero della riga", None ],
                [ "id_prod",    "INT",     idw, None, "ID Prodotto", None ],
                [ "descriz",    "VARCHAR", ntw, None, "Descrizione libera", None ],
                [ "um",         "CHAR",      5, None, "Unità di misura", None ],
                [ "nmconf",     "INT",       6, None, "Numero di confezioni", None ],
                [ "pzconf",     "DECIMAL",   6,  DQM, "Pezzi per confezione", None ],
                [ "qta",        "DECIMAL", IQM,  DQM, "Quantità", None ],
                [ "prezzo",     "DECIMAL", IPM,  DPM, "Valore unitario", None ],
                [ "sconto1",    "DECIMAL",   5,    2, "Sconto riga #1", None ],
                [ "sconto2",    "DECIMAL",   5,    2, "Sconto riga #2", None ],
                [ "sconto3",    "DECIMAL",   5,    2, "Sconto riga #3", None ],
                [ "sconto4",    "DECIMAL",   5,    2, "Sconto riga #4", None ],
                [ "sconto5",    "DECIMAL",   5,    2, "Sconto riga #5", None ],
                [ "sconto6",    "DECIMAL",   5,    2, "Sconto riga #6", None ],
                [ "importo",    "DECIMAL", IVI,  DVI, "Valore globale della riga", None ],
                [ "costou",     "DECIMAL", IPM,  DPM, "Costo unitario della riga", None ],
                [ "costot",     "DECIMAL", IVI,  DVI, "Costo totale della riga", None ],
                [ "id_aliqiva", "INT",     idw, None, "ID Aliquota IVA", None ],
                [ "id_moveva",  "INT",     idw, None, "ID Movimento evaso", None ],
                [ "id_movacc",  "INT",     idw, None, "ID Movimento acconto", None ],
                [ "f_ann",      "TINYINT",   1, None, "Flag riga annullata", None ],\
                [ "f_acq",      "TINYINT",   1, None, "Flag riga acquisita", None ],\
                [ "perpro",     "DECIMAL",   5,    2, "Provvigione% particolare del movimento", None ],
                [ "note",       "VARCHAR", ntw, None, "Note", None],
                [ "id_pdccg",   "INT",     idw, None, "ID Pdc collegamento contabile specifico", None],
                [ "agggrip",    "TINYINT",   1, None, "Flag aggiornamento griglia prezzi", None ],
                [ "id_tiplist", "INT",     idw, None, "ID Tipo listino", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_MOVMAG_B,
                                ((cls.TABSETUP_CONSTR_MOVMAG_H,  'id_doc',     cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_CFGMAGMOV, 'id_tipmov',  cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PROD,      'id_prod',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_ALIQIVA,   'id_aliqiva', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PROD,      'id_prod',    cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_PDC,       'id_pdccg',   cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.movmag_b_indexes = [ ["PRIMARY KEY", "id"],
                                      ["KEY",         "id_doc,numriga"],
                                      ["KEY",         "id_prod,id_doc,numriga"],
                                      ["KEY",         "id_moveva"], 
                                      ["KEY",         "id_movacc"], ]
            
            
            cls.macro =\
              [ [ "id",         "INT",      idw, None, "ID Macro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",      10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR",   60, None, "Descrizione", "NOT NULL" ],
                [ "macro",      "VARCHAR", 2048, None, "Espressione macro", None] ]
            
            cls.tiplist_indexes = cls.std_indexes
            
            
            cls.tiplist =\
              [ [ "id",         "INT",      idw, None, "ID Macro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",      10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR",   60, None, "Descrizione", "NOT NULL" ],
                [ "tipoprezzo", "CHAR",       1, None, "Tipo prezzo", None ],
                [ "id_macro",   "VARCHAR", 2048, None, "ID Macro prezzo personalizzato", None] ]
            
            cls.macro_indexes = cls.std_indexes
            
            
            cls.tracau =\
              [ [ "id",         "INT",    idw, None, "ID Causale", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ],
                [ "esclftd",    "TINYINT",  1, None, "Flag esclusione raggruppamento ddt", "UNSIGNED NOT NULL DEFAULT '0'" ] ]
            
            cls.tracau_indexes = cls.std_indexes
            
            
            cls.tracur =\
              [ [ "id",         "INT",    idw, None, "ID Trasporto a cura", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ],\
                [ "askvet",     "TINYINT",  1, None, "Flag gestione vettore", "NOT NULL DEFAULT 0" ] ]
            
            cls.tracur_indexes = cls.std_indexes
            
            
            cls.traasp =\
              [ [ "id",         "INT",    idw, None, "ID Macro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ] ]
            
            cls.traasp_indexes = cls.std_indexes
            
            
            cls.trapor =\
              [ [ "id",         "INT",    idw, None, "ID Macro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ] ]
            
            cls.trapor_indexes = cls.std_indexes
            
            
            cls.tracon =\
              [ [ "id",         "INT",    idw, None, "ID Macro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", "NOT NULL" ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", "NOT NULL" ] ]
            
            cls.tracon_indexes = cls.std_indexes
            
            
            cls.cfgeff =\
              [ [ "id",         "INT",    idw, None, "ID", "AUTO_INCREMENT" ],
                [ "id_banca",   "INT",    idw, None, "ID Banca", None ],
                [ "tipo",       "CHAR",     1, None, "Tipo configurazione", None ],
                [ "zona",       "CHAR",     1, None, "Zona H/B/F", None ],
                [ "riga",       "INT",      2, None, "Num. riga", None ],
                [ "macro",      "TEXT",  None, None, "Macro riga", None ] ]
            
            cls.set_constraints(cls.TABNAME_CFGEFF,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_banca', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgeff_indexes = [ ["PRIMARY KEY", "id"],
                                    ["UNIQUE KEY",  "id_banca,tipo,zona,riga"], ] 
            
            
            cls.allegati =\
              [ [ "id",         "INT",      idw, None, "ID", "AUTO_INCREMENT" ],
                [ "attscope",   "VARBINARY", 45, None, "Scope validità di attkey", None ],
                [ "attkey",     "INT",      idw, None, "Id record riferimento allegati", None ],
                [ "description","VARBINARY",255, None, "Descrizione allegato", None ],
                [ "folderno",   "INT",        6, None, "Numero cartella contenente il file", None ],
                [ "file",       "VARBINARY",255, None, "Nome file x documento/immagine", None ],
                [ "size",       "INT",       10, None, "Dimensione dell'allegato in bytes", None ],
                [ "url",        "VARBINARY",255, None, "Indirizzo x pagina web", None ],
                [ "datins",     "DATETIME",None, None, "Data inserimento", None ],
                [ "attach_type","TINYINT",    3, None, "Tipo di allegato", None ],
                [ "hidden",     "TINYINT",    1, None, "Flag nascosto", None ],
                [ "autotext",   "TINYINT",    1, None, "Flag popup automatico note", None ],
                [ "voiceatt_id","INT",      idw, None, "ID allegato vocale", None ],
            ]
            
            cls.allegati_indexes = [ ["PRIMARY KEY", "id"],
                                      ["KEY",         "attscope,attkey,attach_type,datins"],
                                      ["KEY",         "attscope,attkey,datins"], ]
            
            
            cls.liqiva =\
              [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                [ "anno",       "INT",       4, None, "Anno liquidazione", None ],
                [ "periodo",    "INT",       2, None, "Periodo riferimento mese/trim.", None ],
                [ "datmin",     "DATE",    None,None, "Data partenza periodo", None ],
                [ "datmax",     "DATE",    None,None, "Data fine periodo", None ],
                [ "datliq",     "DATE",    None,None, "Data di liquidazione", None ],
                [ 'vennor1',    "DECIMAL",  IVI, DVI, "IVA vendite debito", None ],
                [ 'vennor2',    "DECIMAL",  IVI, DVI, "IVA vendite credito", None ],
                [ 'vencor1',    "DECIMAL",  IVI, DVI, "IVA corrispettivi debito", None ],
                [ 'vencor2',    "DECIMAL",  IVI, DVI, "IVA corrispettivi credito", None ],
                [ 'venven1',    "DECIMAL",  IVI, DVI, "IVA ventilazione debito", None ],
                [ 'venven2',    "DECIMAL",  IVI, DVI, "IVA ventilazione credito", None ],
                [ 'acqnor1',    "DECIMAL",  IVI, DVI, "IVA acquisti debito", None ],
                [ 'acqnor2',    "DECIMAL",  IVI, DVI, "IVA acquisti credito", None ],
                [ 'acqcee1',    "DECIMAL",  IVI, DVI, "IVA acquisti cee debito", None ],
                [ 'acqcee2',    "DECIMAL",  IVI, DVI, "IVA acquisti cee credito", None ],
                [ 'tivper1',    "DECIMAL",  IVI, DVI, "IVA totale periodo debito", None ],
                [ 'tivper2',    "DECIMAL",  IVI, DVI, "IVA totale periodo credito", None ],
                [ 'vensos1',    "DECIMAL",  IVI, DVI, "IVA vendite sosp. debito", None ],
                [ 'vensos2',    "DECIMAL",  IVI, DVI, "IVA vendite sosp. credito", None ],
                [ 'ivaind1',    "DECIMAL",  IVI, DVI, "IVA indeducibile debito", None ],
                [ 'ivaind2',    "DECIMAL",  IVI, DVI, "IVA indeducibile credito", None ],
                [ 'docper1',    "DECIMAL",  IVI, DVI, "IVA periodo debito", None ],
                [ 'docper2',    "DECIMAL",  IVI, DVI, "IVA periodo credito", None ],
                [ 'ivaesi1',    "DECIMAL",  IVI, DVI, "IVA debito", None ],
                [ 'ivadet2',    "DECIMAL",  IVI, DVI, "IVA credito", None ],
                [ 'ivadcp1',    "DECIMAL",  IVI, DVI, "IVA periodo debito", None ],
                [ 'ivadcp2',    "DECIMAL",  IVI, DVI, "IVA periodo credito", None ],
                [ 'varpre1',    "DECIMAL",  IVI, DVI, "Variaz. periodi prec. debito", None ],
                [ 'varpre2',    "DECIMAL",  IVI, DVI, "Variaz. periodi prec. credito", None ],
                [ 'invpre1',    "DECIMAL",  IVI, DVI, "IVA non vers.periodi prec. debito", None ],
                [ 'invpre2',    "DECIMAL",  IVI, DVI, "IVA non vers.periodi prec. credito", None ],
                [ 'docpre1',    "DECIMAL",  IVI, DVI, "IVA periodo prec. debito", None ],
                [ 'docpre2',    "DECIMAL",  IVI, DVI, "IVA periodo prec. credito", None ],
                [ 'cricom2',    "DECIMAL",  IVI, DVI, "IVA compens. in detraz.", None ],
                [ 'ivadov1',    "DECIMAL",  IVI, DVI, "IVA periodo dovuta", None ],
                [ 'ivadov2',    "DECIMAL",  IVI, DVI, "IVA periodo credito", None ],
                [ 'crsdet2',    "DECIMAL",  IVI, DVI, "Crediti speciali d'imposta detratti", None ],
                [ 'percint',    "DECIMAL",  IVI, DVI, "Perc.interessi IVA trimestrale", None ],
                [ 'inttri1',    "DECIMAL",  IVI, DVI, "Interessi IVA trimestrale", None ],
                [ 'acciva2',    "DECIMAL",  IVI, DVI, "Acconto versato", None ],
                [ 'vertra1',    "DECIMAL",  IVI, DVI, "Importo vers./trasf.", None ],
                [ 'docfin1',    "DECIMAL",  IVI, DVI, "Debito risultante periodo", None ],
                [ 'docfin2',    "DECIMAL",  IVI, DVI, "Credito risultante periodo", None ],
                [ 'ciciniz',    "DECIMAL",  IVI, DVI, "Cred.Compens. inizio periodo", None ],
                [ 'ciculiq',    "DECIMAL",  IVI, DVI, "Cred.Compens. utilizzato in liq.", None ],
                [ 'cicuf24',    "DECIMAL",  IVI, DVI, "Cred.Compens. utilizzato su F24", None ],
                [ 'cicfine',    "DECIMAL",  IVI, DVI, "Cred.Compens. disponib. a fine liq.", None ]]
            
            cls.liqiva_indexes = [ ["PRIMARY KEY", "id"],
                                    ["UNIQUE KEY", "anno,periodo"], ]
            
            
            cls.cfgsetup =\
              [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                [ "chiave",     "CHAR",     60, None, "Chiave", None ],
                [ "flag",       "CHAR",      1, None, "Flag carattere", None ],
                [ "codice",     "CHAR",     10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", ntw, None, "Descrizione", None ],
                [ 'data',       "DATE",   None, None, "Data", None ],
                [ 'importo',    "DECIMAL", IVI, DVI, "Importo", None ] ]
            
            cls.cfgsetup_indexes = [ ["PRIMARY KEY", "id"],
                                      ["UNIQUE KEY",  "chiave"], ]
            
            
            cls.cfgperm =\
              [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                [ "id_utente",  "INT",     idw, None, "ID utente", None ],
                [ "ambito",     "CHAR",     60, None, "Chiave permesso (ambito)", None ],
                [ "id_rel",     "INT",     idw, None, "ID utente", None ],
                [ "attivo",     "TINYINT",   1, None, "Flag attivo", None ],
                [ "leggi",      "TINYINT",   1, None, "Flag lettura", None ],
                [ "scrivi",     "TINYINT",   1, None, "Flag scrittura", None ],
                [ "permesso",   "CHAR",      1, None, "Tipo di permesso", None ], ]
            
            cls.cfgperm_indexes = [ ["PRIMARY KEY", "id"],
                                    ["UNIQUE KEY",  "ambito,id_rel,id_utente"], ]
            
            
            cls.cfgftdif =\
              [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                [ 'codice',     "CHAR",     10, None, "Descrizione", None ],
                [ 'descriz',    "VARCHAR",  60, None, "Descrizione", None ],
                [ "id_docgen",  "INT",     idw, None, "ID documento da generare", None ],
                [ "f_sepall",   "TINYINT",   1, None, "Separa ad ogni doc.raggr.", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_sepmp",    "TINYINT",   1, None, "Separa ad ogni diversa mod.pag.", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_sepdest",  "TINYINT",   1, None, "Separa ad ogni diversa destinazione", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_solosta",  "TINYINT",   1, None, "Considera solo documenti stampati", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_setacq",   "TINYINT",   1, None, "Setta flag acquisito su doc.generato", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_setann",   "TINYINT",   1, None, "Setta flag annullato su doc.generato", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_setgen",   "TINYINT",   1, None, "Setta flag documento generato da raggruppamento su doc.generato", "UNSIGNED NOT NULL DEFAULT '1'" ],
                [ "f_nodesrif", "TINYINT",   1, None, "Non genera riga di riferimento al documento raggruppato", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "f_chgmag",   "TINYINT",   1, None, "Flag cambio magazzino su documenti generati", "UNSIGNED NOT NULL DEFAULT '0'" ],
                [ "id_chgmag",  "TINYINT", idw, None, "Id magazzino da sostituire su documenti generati", None ], ]
            
            cls.set_constraints(cls.TABNAME_CFGFTDIF,
                                ((cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_docgen', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MAGAZZ,    'id_chgmag', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgftdif_indexes = cls.std_indexes
            
            
            cls.cfgftddr =\
              [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                [ 'id_ftd',     "INT",     idw, None, "ID Fatturazione differita", None ],
                [ "id_docrag",  "INT",     idw, None, "ID Tipo documento da raggruppare", None ],
                [ "f_attivo",   "TINYINT",   1, None, "Flag attivo", None ] ]
            
            cls.set_constraints(cls.TABNAME_CFGFTDDR,
                                ((cls.TABSETUP_CONSTR_CFGFTDIF,  'id_ftd',    cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_CFGMAGDOC, 'id_docrag', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.cfgftddr_indexes = [ ["PRIMARY KEY", "id"],
                                      ["UNIQUE KEY",  "id_ftd,id_docrag"], ]
            
            
            cls.effetti =\
              [ [ "id",         "INT",     idw, None, "ID Tipo effetto", "AUTO_INCREMENT" ],
                [ "tipo",       "CHAR",      1, None, "Tipo effetto", None ],
                [ "id_banca",   "INT",     idw, None, "ID banca associata", None ],
                [ "id_caus",    "INT",     idw, None, "ID causale contabilizzazione", None ],
                [ "filepath",   "VARCHAR", 250, None, "Percorso generazione file banca", None ], ]
            
            cls.set_constraints(cls.TABNAME_EFFETTI,
                                ((cls.TABSETUP_CONSTR_PDC,       'id_banca', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_CFGCONTAB, 'id_caus',  cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.effetti_indexes = [ ["PRIMARY KEY", "id"], ]
            
            
            cls.scadgrp =\
              [ [ "id",         "INT",    idw, None, "ID Gruppo", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice gruppo", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione gruppo", None ] ]
            
            cls.scadgrp_indexes = cls.std_indexes
            
            
            cls.promem =\
              [ [ "id",         "INT",       idw, None, "ID promemoria", "AUTO_INCREMENT" ],
                [ "datains",    "DATETIME", None, None, "Data inserimento", None ],
                [ "uteins",     "CHAR",        2, None, "Cod. utente inserimento", None ],
                [ "datasca",    "DATETIME", None, None, "Data/ora scadenza", None ],
                [ "datarem",    "DATETIME", None, None, "Data/ora avviso", None ],
                [ "globale",    "TINYINT",     1, None, "Globale x tutti gli utenti", None ],
                [ "oggetto",    "VARCHAR",   255, None, "Oggetto", None ],
                [ "descriz",    "VARCHAR",  1024, None, "Testo promemoria", None ],
                [ "status",     "TINYINT",     1, None, "Status lavoro", None ],
                [ "avvisa",     "TINYINT",     1, None, "Flag avviso scadenza", None ],
            ]
            
            cls.promem_indexes = [ ["PRIMARY KEY", "id"],
                                    ["KEY",         "datasca"], ]
            
            
            cls.promemu =\
              [ [ "id",         "INT",       idw, None, "ID utente promemoria", "AUTO_INCREMENT" ],
                [ "id_promem",  "INT",       idw, None, "ID promemoria", None ],
                [ "utente",     "CHAR",        2, None, "Codice utente", None ],
                [ "refresh",    "TINYINT",     1, None, "Flag refresh ui", None ],
            ]
            
            cls.set_constraints(cls.TABNAME_PROMEMU,
                                ((cls.TABSETUP_CONSTR_PROMEM, 'id_promem', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.promemu_indexes = [ ["PRIMARY KEY", "id"],
                                     ["UNIQUE KEY",  "id_promem,utente"], ]
            
            
            cls.cfgmagriv =\
              [ [ "id",         "INT",       idw, None, "ID", "AUTO_INCREMENT" ],
                [ "id_caus",    "INT",       idw, None, "ID causale iva", "NOT NULL" ],
                [ "id_magazz",  "INT",       idw, None, "ID magazzino", "NOT NULL" ],
                [ "id_regiva",  "INT",       idw, None, "ID registro iva", "NOT NULL" ],
            ]
            
            cls.set_constraints(cls.TABNAME_CFGMAGRIV,
                                ((cls.TABSETUP_CONSTR_CFGCONTAB, 'id_caus',   cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_MAGAZZ,    'id_magazz', cls.TABCONSTRAINT_TYPE_NOACTION),
                                 (cls.TABSETUP_CONSTR_REGIVA,    'id_regiva', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.cfgmagriv_indexes = [ ["PRIMARY KEY", "id"],
                                       ["UNIQUE KEY",  "id_caus,id_magazz,id_regiva"], ]
            
            
            cls.marart =\
              [ [ "id",         "INT",    idw, None, "ID Marca prodotto", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ] ]
            
            cls.marart_indexes = cls.std_indexes
            
            
            cls.pdcrange =\
              [ [ "id",         "INT",    idw, None, "ID Range", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "rangemin",   "INT",      6, None, "Range minimo", None ],
                [ "rangemax",   "INT",      6, None, "Range massimo", None ] ]
            
            cls.pdcrange_indexes = cls.std_indexes
            
            
            cls.brimas =\
              [ [ "id",         "INT",    idw,    0, "ID Mastro", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "tipo",       "CHAR",     1, None, "Tipologia P/E/O", None ] ]
            cls.brimas_indexes = cls.std_indexes
            
            
            cls.bricon =\
              [ [ "id",         "INT",    idw, None, "ID Conto", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "id_bilmas",  "INT",    idw, None, "ID Mastro", None ] ]
            
            cls.set_constraints(cls.TABNAME_BRICON,
                                ((cls.TABSETUP_CONSTR_BRIMAS, 'id_bilmas', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.bricon_indexes = [ ["PRIMARY KEY", "id"],
                                    ["UNIQUE KEY",  "id_bilmas,codice"],
                                    ["UNIQUE KEY",  "id_bilmas,descriz"], ]
            
            
            cls.prodpro =\
              [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                [ "id_prod",    "INT",     idw, None, "ID Prodotto", "NOT NULL" ],
                [ "id_magazz",  "INT",     idw, None, "ID Magazzino", "NOT NULL" ],
                [ "ini",        "DECIMAL", IQM, DQM,  "Giacenza iniziale", "default '0'"],\
                [ "car",        "DECIMAL", IQM, DQM,  "Carichi", "default '0'"],\
                [ "sca",        "DECIMAL", IQM, DQM,  "Scarichi", "default '0'"],\
                [ "iniv",       "DECIMAL", IVI, DVI,  "Valore iniziale", "default '0'"],\
                [ "carv",       "DECIMAL", IVI, DVI,  "Valore carichi", "default '0'"],\
                [ "scav",       "DECIMAL", IVI, DVI,  "Valore scarichi", "default '0'"],\
                [ "cvccar",     "DECIMAL", IQM, DQM,  "Carichi C/V clienti", "default '0'"],\
                [ "cvcsca",     "DECIMAL", IQM, DQM,  "Scarichi C/V clienti", "default '0'"],\
                [ "cvfcar",     "DECIMAL", IQM, DQM,  "Carichi C/V fornitori", "default '0'"],\
                [ "cvfsca",     "DECIMAL", IQM, DQM,  "Scarichi C/V fornitori", "default '0'"],\
            ]
            
            cls.set_constraints(cls.TABNAME_PRODPRO,
                                ((cls.TABSETUP_CONSTR_PROD,   'id_prod',   cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_MAGAZZ, 'id_magazz', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.prodpro_indexes = [["PRIMARY KEY", "id"],
                                   ["UNIQUE KEY",  "id_prod,id_magazz"],]
            
            
            cls.gruprez =\
              [ [ "id",         "INT",    idw, None, "ID", "AUTO_INCREMENT" ],
                [ "codice",     "CHAR",    10, None, "Codice", None ],
                [ "descriz",    "VARCHAR", 60, None, "Descrizione", None ],
                [ "calcpc",     "CHAR",     1, None, "Tipo calcolo del costo/prezzo", "NOT NULL" ],
                [ "calclis",    "CHAR",     1, None, "Tipo calcolo dei listini", "NOT NULL" ],
                [ "prccosric1", "DECIMAL",  6, 2,    "Calcolo prezzo al pubblico: ricarica 1", None],\
                [ "prccosric2", "DECIMAL",  6, 2,    "Calcolo prezzo al pubblico: ricarica 2", None],\
                [ "prccosric3", "DECIMAL",  6, 2,    "Calcolo prezzo al pubblico: ricarica 3", None],\
                [ "prccosric4", "DECIMAL",  6, 2,    "Calcolo prezzo al pubblico: ricarica 4", None],\
                [ "prccosric5", "DECIMAL",  6, 2,    "Calcolo prezzo al pubblico: ricarica 5", None],\
                [ "prccosric6", "DECIMAL",  6, 2,    "Calcolo prezzo al pubblico: ricarica 6", None],\
                [ "prcpresco1", "DECIMAL",  6, 2,    "Calcolo costo di acquisto: sconto 1", None],\
                [ "prcpresco2", "DECIMAL",  6, 2,    "Calcolo costo di acquisto: sconto 2", None],\
                [ "prcpresco3", "DECIMAL",  6, 2,    "Calcolo costo di acquisto: sconto 3", None],\
                [ "prcpresco4", "DECIMAL",  6, 2,    "Calcolo costo di acquisto: sconto 4", None],\
                [ "prcpresco5", "DECIMAL",  6, 2,    "Calcolo costo di acquisto: sconto 5", None],\
                [ "prcpresco6", "DECIMAL",  6, 2,    "Calcolo costo di acquisto: sconto 6", None],\
                [ "prclisric1", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 1", None],\
                [ "prclisric2", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 2", None],\
                [ "prclisric3", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 3", None],\
                [ "prclisric4", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 4", None],\
                [ "prclisric5", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 5", None],\
                [ "prclisric6", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 6", None],\
                [ "prclisric7", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 7", None],\
                [ "prclisric8", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 8", None],\
                [ "prclisric9", "DECIMAL",  6, 2,    "Prezzo da costo di acquisto: ricarica prezzo 9", None],\
                [ "prclissco1", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 1", None],\
                [ "prclissco2", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 2", None],\
                [ "prclissco3", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 3", None],\
                [ "prclissco4", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 4", None],\
                [ "prclissco5", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 5", None],\
                [ "prclissco6", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 6", None],\
                [ "prclissco7", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 7", None],\
                [ "prclissco8", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 8", None],\
                [ "prclissco9", "DECIMAL",  6, 2,    "Prezzo da prezzo al pubblico: sconto prezzo 9", None],\
                [ "prclisvar1", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 1", None],\
                [ "prclisvar2", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 2", None],\
                [ "prclisvar3", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 3", None],\
                [ "prclisvar4", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 4", None],\
                [ "prclisvar5", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 5", None],\
                [ "prclisvar6", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 6", None],\
                [ "prclisvar7", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 7", None],\
                [ "prclisvar8", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 8", None],\
                [ "prclisvar9", "DECIMAL",  6, 2,    "Prezzo da calcolo variabile: variazione percentuale 9", None],\
                [ "prclisbas1", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 1", None],\
                [ "prclisbas2", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 2", None],\
                [ "prclisbas3", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 3", None],\
                [ "prclisbas4", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 4", None],\
                [ "prclisbas5", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 5", None],\
                [ "prclisbas6", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 6", None],\
                [ "prclisbas7", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 7", None],\
                [ "prclisbas8", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 8", None],\
                [ "prclisbas9", "CHAR",     1, None, "Prezzo da calcolo variabile: base calcolo 9", None],\
                [ "nosconti",   "TINYINT",  1, None, "Flag inibizione scontistiche, tranne promo", None],\
                [ "id_lisdagp", "INT",    idw, None, "ID Gruppo prezzi da usare per il calcolo dei listini", None], ]                                                                                    
            
            cls.set_constraints(cls.TABNAME_GRUPREZ,
                                ((cls.TABSETUP_CONSTR_GRUPREZ, 'id_lisdagp', cls.TABCONSTRAINT_TYPE_NOACTION),))
            
            cls.gruprez_indexes = cls.std_indexes
            
            
            cls.sconticc =\
               [ [ "id",         "INT",    idw, None, "ID", "AUTO_INCREMENT" ],
                 [ "id_pdc",     "INT",    idw, None, "ID cliente", None ],
                 [ "id_catart",  "INT",    idw, None, "ID categoria", None ],
                 [ "sconto1",    "DECIMAL",  4,    2, "Sconto perc.1", None ],
                 [ "sconto2",    "DECIMAL",  4,    2, "Sconto perc.2", None ],
                 [ "sconto3",    "DECIMAL",  4,    2, "Sconto perc.3", None ], 
                 [ "sconto4",    "DECIMAL",  4,    2, "Sconto perc.4", None ], 
                 [ "sconto5",    "DECIMAL",  4,    2, "Sconto perc.5", None ], 
                 [ "sconto6",    "DECIMAL",  4,    2, "Sconto perc.6", None ], ]
            
            cls.set_constraints(cls.TABNAME_SCONTICC,
                                ((cls.TABSETUP_CONSTR_PDC,    'id_pdc',    cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_CATART, 'id_catart', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.sconticc_indexes = [ ["PRIMARY KEY", "id"],
                                     ["UNIQUE KEY",  "id_pdc,id_catart"] ]
            
            
            cls.pdt_h =\
               [ [ "id",            "INT",       idw, None, "ID", "AUTO_INCREMENT" ],
                 [ "uid",           "CHAR",       32, None, "Identificativo sessione di lavoro", None ],
                 [ "descriz",       "VARCHAR",    64, None, "Descrizione riferimento cliente", None ],
                 [ "pdtnum",        "INT",         3, None, "Numero terminalino pdt", None ],
                 [ "datins",        "DATETIME", None, None, "Data ora inserimento letture", None ],
                 [ "datemis",       "DATETIME", None, None, "Data ora emissione documento", None ],
                 [ "id_utente",     "INT",       idw, None, "ID utente", None ],
                 [ "id_pdc",        "INT",       idw, None, "ID cliente", None ],
                 [ "id_tiplist",    "INT",       idw, None, "ID tipo listino", None ],
                 [ "id_aliqiva",    "INT",       idw, None, "ID aliquota predefinita", None ],
                 [ "id_destin",     "INT",       idw, None, "ID destinatario", None ],
                 [ "id_modpag",     "INT",       idw, None, "ID mod.pagamento", None ],
                 [ "id_bancf",      "INT",       idw, None, "ID banca cliente", None ],
                 [ "id_speinc",     "INT",       idw, None, "ID spese incasso", None ],
                 [ "id_tracau",     "INT",       idw, None, "ID causale trasporto", None ],
                 [ "id_tracur",     "INT",       idw, None, "ID trasporto cura", None ],
                 [ "id_travet",     "INT",       idw, None, "ID vettore", None ],
                 [ "id_traasp",     "INT",       idw, None, "ID aspetto beni", None ],
                 [ "id_trapor",     "INT",       idw, None, "ID porto", None ],
                 [ "id_tracon",     "INT",       idw, None, "ID tipo contrassegno", None ],
                 [ "id_docdone",    "INT",       idw, None, "ID documento emesso", None ],
                 [ "do_print",      "TINYINT",     1, None, "Flag documento da stampare", None ],
                 [ "is_printed",    "TINYINT",     1, None, "Flag documento stampato", None ],
                 [ "print_warning", "TINYINT",     1, None, "Warning stampa documento", None ],
                 [ "totpeso",       "DECIMAL",     9,    3, "Tot.peso", None ],
                 [ "totcolli",      "INT",         6, None, "Num.colli", None ],
                 [ "initrasp",      "DATETIME", None, None, "Data ora inizio trasporto", None ],
                 [ "notedoc",       "VARCHAR",   ntw, None, "Note in stampa documento", None ],
                 [ "noteint",       "VARCHAR",   ntw, None, "Note interne documento", None ],
                 [ "notevet",       "VARCHAR",   ntw, None, "Note vettore", None ],
                 [ "acconto",       "DECIMAL",   IVI,  DVI, "Ammontare dell'acconto", None ],
                 [ "accstor",       "DECIMAL",   IVI,  DVI, "Ammontare dello storno acconto", None ],
                 [ "ready",         "TINYINT",     1, None, "Flag sessione letture conclusa", None ],
                 [ "ddtstapre",     "TINYINT",     1, None, "Flag stampa prezzi su ddt", None ],
                 [ "numdoc",        "INT",        10, None, "Numero documento da generare", None ],
                 [ "datdoc",        "DATE",     None, None, "Data documento da generare", None ],
             ]
            
            if cls.MAGNOCODEDES:
                cls.pdt_h += [\
                [ "nocodedes_descriz",    "VARCHAR",    60, None, "Destinatario non codificato: Descrizione", None ],
                [ "nocodedes_indirizzo",  "VARCHAR",    60, None, "Destinatario non codificato: Indirizzo", None ],
                [ "nocodedes_cap",        "CHAR",        5, None, "Destinatario non codificato: CAP", None ],
                [ "nocodedes_citta",      "VARCHAR",    60, None, "Destinatario non codificato: Città", None ],
                [ "nocodedes_prov",       "CHAR",        2, None, "Destinatario non codificato: Provincia", None ],
                [ "nocodedes_id_stato",   "INT",       idw, None, "Destinatario non codificato: ID stato", None ], ]
            
            cls.set_constraints(cls.TABNAME_PDT_H,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.pdt_h_indexes = [ ["PRIMARY KEY", "id"],
                                  ["KEY",  "uid"] ]
            
            
            cls.pdt_b =\
               [ [ "id",         "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                 [ "id_h",       "INT",     idw, None, "ID sessione", None ],
                 [ "numriga",    "INT",       4, None, "Num.riga", None ],
                 [ "id_prod",    "INT",     idw, None, "ID prodotto", None ],
                 [ "descriz",    "VARCHAR",  60, None, "Descrizione", None ],
                 [ "barcode",    "CHAR",     32, None, "Barcode letto dal pdt", None ],
                 [ "id_tiplist", "INT",     idw, None, "ID tipo listino", None ],
                 [ "id_aliqiva", "INT",     idw, None, "ID aliquota iva", None ],
                 [ "um",         "CHAR",      5, None, "Unità di misura", None ],
                 [ "qta",        "DECIMAL", IQM,  DQM, "Quantita'", None ],
                 [ "prezzo",     "DECIMAL", IPM,  DPM, "Prezzo", None ],
                 [ "sconto1",    "DECIMAL",   5,    2, "Sconto 1", None ],
                 [ "sconto2",    "DECIMAL",   5,    2, "Sconto 2", None ],
                 [ "sconto3",    "DECIMAL",   5,    2, "Sconto 3", None ],
                 [ "importo",    "DECIMAL",  10,  DVI, "Importo riga", None ],
                 [ "note",       "VARCHAR", ntw, None, "Note della riga", None ],
             ]
            
            cls.set_constraints(cls.TABNAME_PDT_B,
                                ((cls.TABSETUP_CONSTR_PDT_H, 'id_h',    cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_PROD,  'id_prod', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.pdt_b_indexes = [ ["PRIMARY KEY", "id"], ]
            
            
            cls.procos =\
               [ [ "id",      "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                 [ "id_prod", "INT",     idw, None, "ID Prodotto", None ],
                 [ "anno",    "INT",       4, None, "Anno di riferimento", None ],
                 [ "costou",  "DECIMAL", IPM,  DPM, "Costo ultimo", None ],
                 [ "costom",  "DECIMAL", IPM,  DPM, "Costo medio", None ],
                 [ "prezzop", "DECIMAL", IPM,  DPM, "Prezzo al pubblico", None ],
                 [ "prezzo1", "DECIMAL", IPM,  DPM, "Prezzo listino 1", None ],
                 [ "prezzo2", "DECIMAL", IPM,  DPM, "Prezzo listino 2", None ],
                 [ "prezzo3", "DECIMAL", IPM,  DPM, "Prezzo listino 3", None ],
                 [ "prezzo4", "DECIMAL", IPM,  DPM, "Prezzo listino 4", None ],
                 [ "prezzo5", "DECIMAL", IPM,  DPM, "Prezzo listino 5", None ],
                 [ "prezzo6", "DECIMAL", IPM,  DPM, "Prezzo listino 6", None ],
                 [ "prezzo7", "DECIMAL", IPM,  DPM, "Prezzo listino 7", None ],
                 [ "prezzo8", "DECIMAL", IPM,  DPM, "Prezzo listino 8", None ],
                 [ "prezzo9", "DECIMAL", IPM,  DPM, "Prezzo listino 9", None ], ]
            
            cls.set_constraints(cls.TABNAME_PROCOS,
                                ((cls.TABSETUP_CONSTR_PROD, 'id_prod', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.procos_index = [ ["PRIMARY KEY", "id"], 
                                 ["KEY", "id_prod,anno"], ]
            
            
            cls.progia =\
               [ [ "id",        "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                 [ "id_prod",   "INT",     idw, None, "ID Prodotto", None ],
                 [ "id_magazz", "INT",     idw, None, "ID Magazzino", None ],
                 [ "anno",      "INT",       4, None, "Anno di riferimento", None ],
                 [ "datgia",    "DATE",   None, None, "Data determinazione giacenze contabili", None ],
                 [ "giacon",    "DECIMAL", IQM,  DQM, "Giacenza contabile", None ],
                 [ "giafis",    "DECIMAL", IQM,  DQM, "Giacenza rilevata", None ], 
                 [ "movgen",    "TINYINT",   1, None, "Flag movimento generato", None ], 
             ]
            
            cls.set_constraints(cls.TABNAME_PROGIA,
                                ((cls.TABSETUP_CONSTR_PROD,   'id_prod',   cls.TABCONSTRAINT_TYPE_CASCADE),
                                 (cls.TABSETUP_CONSTR_MAGAZZ, 'id_magazz', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.progia_index = [ ["PRIMARY KEY", "id"],
                                 ["UNIQUE KEY",  "id_prod,id_magazz,anno"], ]
            
            
            cls.promo =\
               [ [ "id",        "INT",     idw, None, "ID", "AUTO_INCREMENT" ],
                 [ "id_prod",   "INT",     idw, None, "ID Prodotto", None ],
                 [ "datmin",    "DATE",   None, None, "Data partenza promozione", None ],
                 [ "datmax",    "DATE",   None, None, "Data fine promozione", None ],
                 [ "prezzo",    "DECIMAL", IPM,  DPM, "Prezzo", None ],
                 [ "sconto1",   "DECIMAL",   5,    2, "Sconto #1", None ],
                 [ "sconto2",   "DECIMAL",   5,    2, "Sconto #2", None ],
                 [ "sconto3",   "DECIMAL",   5,    2, "Sconto #3", None ],
                 [ "sconto4",   "DECIMAL",   5,    2, "Sconto #4", None ],
                 [ "sconto5",   "DECIMAL",   5,    2, "Sconto #5", None ],
                 [ "sconto6",   "DECIMAL",   5,    2, "Sconto #6", None ],
                 [ "note",      "VARCHAR", ntw, None, "Annotazioni", None ], ]
            
            cls.set_constraints(cls.TABNAME_PROMO,
                                ((cls.TABSETUP_CONSTR_PROD, 'id_prod', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.promo_index = [ ["PRIMARY KEY", "id"],
                                ["KEY",         "id_prod,datmin"], ]
            
            
            cls.statpdc =\
              [ [ "id",           "INT",    idw, None, "ID Status", "AUTO_INCREMENT" ],
                [ "codice",       "CHAR",    10, None, "Codice", None ],
                [ "descriz",      "VARCHAR", 60, None, "Descrizione", None ],
                [ "hidesearch",   "TINYINT",  1, None, "Flag per nascondere nelle ricerche", None ],
            ]
            
            cls.statpdc_indexes = cls.std_indexes
            
            
            cls.tipevent =\
               [ [ "id",             "INT",     idw, None, "ID Tipo evento", "AUTO_INCREMENT" ],
                 [ "codice",         "CHAR",     10, None, "Codice", None ],
                 [ "descriz",        "VARCHAR",  60, None, "Descrizione", None ],
                 [ "notify_emailto", "VARCHAR", 255, None, "Destinatario notifica email", None ],
                 [ "notify_xmppto",  "VARCHAR", 255, None, "Destinatario notifica xmpp", None ],
             ]
            
            cls.tipevent_indexes = cls.std_indexes
            
            
            cls.eventi =\
               [ [ "id",             "INT",       idw, None, "ID Evento", "AUTO_INCREMENT" ],
                 [ "data_evento",    "DATETIME", None, None, "Data e ora evento", None ],
                 [ "wksname",        "VARCHAR",   128, None, "Nome pc client", None ],
                 [ "wksaddr",        "VARCHAR",   128, None, "Indirizzo pc client", None ],
                 [ "usercode",       "VARCHAR",    16, None, "Codice utente", None ],
                 [ "username",       "VARCHAR",    16, None, "Nome utente", None ],
                 [ "id_tipevent",    "INT",       idw, None, "ID Tipo evento", None ],
                 [ "dettaglio",      "VARCHAR",  1024, None, "Dettaglio evento", None ],
                 [ "tablename",      "CHAR",       16, None, "Nome tabella elemento collegato", None ],
                 [ "tableid",        "INT",       idw, None, "ID Elemento collegato", None ],
                 [ "notified_email", "TINYINT",     1, None, "Flag evento notificato per posta elettronica", None ],
                 [ "notifieddemail", "DATETIME", None, None, "Data invio notifica per posta elettronica", None ],
                 [ "notified_xmpp",  "TINYINT",     1, None, "Flag evento notificato per messaggistica immediata", None ],
                 [ "notifieddxmpp",  "DATETIME", None, None, "Data invio notifica per messaggistica immediata", None ],
             ]
            
            cls.set_constraints(cls.TABNAME_EVENTI,
                                ((cls.TABSETUP_CONSTR_TIPEVENT, 'id_tipevent', cls.TABCONSTRAINT_TYPE_SETNULL),))
            
            cls.eventi_indexes = [ ["PRIMARY KEY", "id"],
                                   ["KEY",         "data_evento"], ]
            
            
            cls.docsemail =\
               [ [ "id",             "INT",       idw, None, "ID Email", "AUTO_INCREMENT" ],
                 [ "datcoda",        "DATETIME", None, None, "Data-ora inserimento nella coda", None ],
                 [ "datsend",        "DATETIME", None, None, "Data-ora invio", None ],
                 [ "id_pdc",         "INT",       idw, None, "ID anagrafica cliente/fornitore", None ],
                 [ "id_doc",         "INT",       idw, None, "ID documento", None ],
                 [ "tipologia",      "VARCHAR",   120, None, "Tipologia messaggio", None ],
                 [ "mittente",       "VARCHAR",   120, None, "Descrizione mittente", None ],
                 [ "destinat",       "VARCHAR",   120, None, "Descrizione destinatario", None ],
                 [ "oggetto",        "VARCHAR",   ntw, None, "Oggetto della mail", None ],
                 [ "testo",          "VARCHAR",   ntw, None, "Testo della mail", None ],
                 [ "documento",      "LONGBLOB", None, None, "Stream del documento allegato", None ],
             ]
            
            cls.set_constraints(cls.TABNAME_DOCSEMAIL,
                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.docsemail_indexes = [ ["PRIMARY KEY", "id"],
                                      ["KEY",         "datcoda"], ]
            
            
            cls.varlist =\
               [ [ "id",             "INT",       idw, None, "ID Email", "AUTO_INCREMENT" ],
                 [ "id_cliente",     "INT",       idw, None, "ID cliente", None ],
                 [ "id_fornit",      "INT",       idw, None, "ID fornitore", None ],
                 [ "id_marart",      "INT",       idw, None, "ID marca prodotto", None ],
                 [ "id_catart",      "INT",       idw, None, "ID categoria merce", None ],
                 [ "id_gruart",      "INT",       idw, None, "ID gruppo merce", None ],
                 [ "id_tiplist",     "INT",       idw, None, "ID tipo listino", None ],
             ]
            
#            cls.set_constraints(cls.TABNAME_VARLIST,
#                                ((cls.TABSETUP_CONSTR_PDC, 'id_pdc', cls.TABCONSTRAINT_TYPE_CASCADE),))
            
            cls.varlist_indexes = [ ["PRIMARY KEY", "id"],
                                    ["KEY",         "id_cliente"], ]
            
            
            cls.tabelle = [ 
                (cls.TABNAME_BILMAS,    cls.TABDESC_BILMAS,    cls.bilmas,    cls.bilmas_indexes,    cls.TABSETUP_CONSTR_BILMAS,    cls.TABVOICE_BILMAS    ),
                (cls.TABNAME_BILCON,    cls.TABDESC_BILCON,    cls.bilcon,    cls.bilcon_indexes,    cls.TABSETUP_CONSTR_BILCON,    cls.TABVOICE_BILCON    ),
                (cls.TABNAME_PDCTIP,    cls.TABDESC_PDCTIP,    cls.pdctip,    cls.pdctip_indexes,    cls.TABSETUP_CONSTR_PDCTIP,    cls.TABVOICE_PDCTIP    ),
                (cls.TABNAME_ALIQIVA,   cls.TABDESC_ALIQIVA,   cls.aliqiva,   cls.aliqiva_indexes,   cls.TABSETUP_CONSTR_ALIQIVA,   cls.TABVOICE_ALIQIVA   ),
                (cls.TABNAME_AGENTI,    cls.TABDESC_AGENTI,    cls.agenti,    cls.agenti_indexes,    cls.TABSETUP_CONSTR_AGENTI,    cls.TABVOICE_AGENTI    ),
                (cls.TABNAME_ZONE,      cls.TABDESC_ZONE,      cls.zone,      cls.zone_indexes,      cls.TABSETUP_CONSTR_ZONE,      cls.TABVOICE_ZONE      ),
                (cls.TABNAME_VALUTE,    cls.TABDESC_VALUTE,    cls.valute,    cls.valute_indexes,    cls.TABSETUP_CONSTR_VALUTE,    cls.TABVOICE_VALUTE    ),
                (cls.TABNAME_MODPAG,    cls.TABDESC_MODPAG,    cls.modpag,    cls.modpag_indexes,    cls.TABSETUP_CONSTR_MODPAG,    cls.TABVOICE_MODPAG    ),
                (cls.TABNAME_TRAVET,    cls.TABDESC_TRAVET,    cls.travet,    cls.travet_indexes,    cls.TABSETUP_CONSTR_TRAVET,    cls.TABVOICE_TRAVET    ),
                (cls.TABNAME_SPEINC,    cls.TABDESC_SPEINC,    cls.speinc,    cls.speinc_indexes,    cls.TABSETUP_CONSTR_SPEINC,    cls.TABVOICE_SPEINC    ),
                (cls.TABNAME_REGIVA,    cls.TABDESC_REGIVA,    cls.regiva,    cls.regiva_indexes,    cls.TABSETUP_CONSTR_REGIVA,    cls.TABVOICE_REGIVA    ),
                (cls.TABNAME_CFGCONTAB, cls.TABDESC_CFGCONTAB, cls.cfgcontab, cls.cfgcontab_indexes, cls.TABSETUP_CONSTR_CFGCONTAB, cls.TABVOICE_CFGCONTAB ),
                (cls.TABNAME_CATCLI,    cls.TABDESC_CATCLI,    cls.catcli,    cls.catcli_indexes,    cls.TABSETUP_CONSTR_CATCLI,    cls.TABVOICE_CATCLI    ),
                (cls.TABNAME_CATFOR,    cls.TABDESC_CATFOR,    cls.catfor,    cls.catfor_indexes,    cls.TABSETUP_CONSTR_CATFOR,    cls.TABVOICE_CATFOR    ),
                (cls.TABNAME_STATCLI,   cls.TABDESC_STATCLI,   cls.statcli,   cls.statcli_indexes,   cls.TABSETUP_CONSTR_STATCLI,   cls.TABVOICE_STATCLI   ),
                (cls.TABNAME_STATFOR,   cls.TABDESC_STATFOR,   cls.statfor,   cls.statfor_indexes,   cls.TABSETUP_CONSTR_STATFOR,   cls.TABVOICE_STATFOR   ),
                (cls.TABNAME_PDC,       cls.TABDESC_PDC,       cls.pdc,       cls.pdc_indexes,       cls.TABSETUP_CONSTR_PDC,       cls.TABVOICE_PDC       ),
                (cls.TABNAME_CLIENTI,   cls.TABDESC_CLIENTI,   cls.clienti,   cls.clienti_indexes,   cls.TABSETUP_CONSTR_CLIENTI,   cls.TABVOICE_CLIENTI   ),
                (cls.TABNAME_DESTIN,    cls.TABDESC_DESTIN,    cls.destin,    cls.destin_indexes,    cls.TABSETUP_CONSTR_DESTIN,    cls.TABVOICE_DESTIN    ),
                (cls.TABNAME_BANCF,     cls.TABDESC_BANCF,     cls.bancf,     cls.bancf_indexes,     cls.TABSETUP_CONSTR_BANCF,     cls.TABVOICE_BANCF     ),
                (cls.TABNAME_FORNIT,    cls.TABDESC_FORNIT,    cls.fornit,    cls.fornit_indexes,    cls.TABSETUP_CONSTR_FORNIT,    cls.TABVOICE_FORNIT    ),
                (cls.TABNAME_CASSE,     cls.TABDESC_CASSE,     cls.casse,     cls.casse_indexes,     cls.TABSETUP_CONSTR_CASSE,     cls.TABVOICE_CASSE     ),
                (cls.TABNAME_BANCHE,    cls.TABDESC_BANCHE,    cls.banche,    cls.banche_indexes,    cls.TABSETUP_CONSTR_BANCHE,    cls.TABVOICE_BANCHE    ),
                (cls.TABNAME_CONTAB_H,  cls.TABDESC_CONTAB_H,  cls.contab_h,  cls.contab_h_indexes,  cls.TABSETUP_CONSTR_CONTAB_H,  cls.TABVOICE_CONTAB_H  ),
                (cls.TABNAME_CONTAB_B,  cls.TABDESC_CONTAB_B,  cls.contab_b,  cls.contab_b_indexes,  cls.TABSETUP_CONSTR_CONTAB_B,  cls.TABVOICE_CONTAB_B  ),
                (cls.TABNAME_PCF,       cls.TABDESC_PCF,       cls.pcf,       cls.pcf_indexes,       cls.TABSETUP_CONSTR_PCF,       cls.TABVOICE_PCF       ),
                (cls.TABNAME_CONTAB_S,  cls.TABDESC_CONTAB_S,  cls.contab_s,  cls.contab_s_indexes,  cls.TABSETUP_CONSTR_CONTAB_S,  cls.TABVOICE_CONTAB_S  ),
                (cls.TABNAME_CFGPROGR,  cls.TABDESC_CFGPROGR,  cls.cfgprogr,  cls.cfgprogr_indexes,  cls.TABSETUP_CONSTR_PROGR,     cls.TABVOICE_CFGPROGR  ),
                (cls.TABNAME_CFGAUTOM,  cls.TABDESC_CFGAUTOM,  cls.cfgautom,  cls.cfgautom_indexes,  cls.TABSETUP_CONSTR_AUTOM,     cls.TABVOICE_CFGAUTOM  ),
                (cls.TABNAME_CFGPDCP,   cls.TABDESC_CFGPDCP,   cls.cfgpdcp,   cls.cfgpdcp_indexes,   cls.TABSETUP_CONSTR_CFGPDCP,   cls.TABVOICE_CFGPDCP   ),
                (cls.TABNAME_TIPART,    cls.TABDESC_TIPART,    cls.tipart,    cls.tipart_indexes,    cls.TABSETUP_CONSTR_TIPART,    cls.TABVOICE_TIPART    ),
                (cls.TABNAME_CATART,    cls.TABDESC_CATART,    cls.catart,    cls.catart_indexes,    cls.TABSETUP_CONSTR_CATART,    cls.TABVOICE_CATART    ),
                (cls.TABNAME_GRUART,    cls.TABDESC_GRUART,    cls.gruart,    cls.gruart_indexes,    cls.TABSETUP_CONSTR_GRUART,    cls.TABVOICE_GRUART    ),
                (cls.TABNAME_STATART,   cls.TABDESC_STATART,   cls.statart,   cls.statart_indexes,   cls.TABSETUP_CONSTR_STATART,   cls.TABVOICE_STATART   ),
                (cls.TABNAME_PROD,      cls.TABDESC_PROD,      cls.prod,      cls.prod_indexes,      cls.TABSETUP_CONSTR_PROD,      cls.TABVOICE_PROD      ),
                (cls.TABNAME_CODARTCF,  cls.TABDESC_CODARTCF,  cls.codartcf,  cls.codartcf_indexes,  cls.TABSETUP_CONSTR_CODARTCF,  cls.TABVOICE_CODARTCF  ),
                (cls.TABNAME_LISTINI,   cls.TABDESC_LISTINI,   cls.listini,   cls.listini_indexes,   cls.TABSETUP_CONSTR_LISTINI,   cls.TABVOICE_LISTINI   ),
                (cls.TABNAME_GRIGLIE,   cls.TABDESC_GRIGLIE,   cls.griglie,   cls.griglie_indexes,   cls.TABSETUP_CONSTR_GRIGLIE,   cls.TABVOICE_GRIGLIE   ),
                (cls.TABNAME_MAGAZZ,    cls.TABDESC_MAGAZZ,    cls.magazz,    cls.magazz_indexes,    cls.TABSETUP_CONSTR_MAGAZZ,    cls.TABVOICE_MAGAZZ    ),
                (cls.TABNAME_CFGMAGDOC, cls.TABDESC_CFGMAGDOC, cls.cfgmagdoc, cls.cfgmagdoc_indexes, cls.TABSETUP_CONSTR_CFGMAGDOC, cls.TABVOICE_CFGMAGDOC ),
                (cls.TABNAME_CFGMAGMOV, cls.TABDESC_CFGMAGMOV, cls.cfgmagmov, cls.cfgmagmov_indexes, cls.TABSETUP_CONSTR_CFGMAGMOV, cls.TABVOICE_CFGMAGMOV ),
                (cls.TABNAME_MOVMAG_H,  cls.TABDESC_MOVMAG_H,  cls.movmag_h,  cls.movmag_h_indexes,  cls.TABSETUP_CONSTR_MOVMAG_H,  cls.TABVOICE_MOVMAG_H  ),
                (cls.TABNAME_MOVMAG_B,  cls.TABDESC_MOVMAG_B,  cls.movmag_b,  cls.movmag_b_indexes,  cls.TABSETUP_CONSTR_MOVMAG_B,  cls.TABVOICE_MOVMAG_B  ),
                (cls.TABNAME_MACRO,     cls.TABDESC_MACRO,     cls.macro,     cls.macro_indexes,     cls.TABSETUP_CONSTR_MACRO,     cls.TABVOICE_MACRO     ),
                (cls.TABNAME_TIPLIST,   cls.TABDESC_TIPLIST,   cls.tiplist,   cls.tiplist_indexes,   cls.TABSETUP_CONSTR_TIPLIST,   cls.TABVOICE_TIPLIST   ),
                (cls.TABNAME_TRACAU,    cls.TABDESC_TRACAU,    cls.tracau,    cls.tracau_indexes,    cls.TABSETUP_CONSTR_TRACAU,    cls.TABVOICE_TRACAU    ),
                (cls.TABNAME_TRACUR,    cls.TABDESC_TRACUR,    cls.tracur,    cls.tracur_indexes,    cls.TABSETUP_CONSTR_TRACUR,    cls.TABVOICE_TRACUR    ),
                (cls.TABNAME_TRAASP,    cls.TABDESC_TRAASP,    cls.traasp,    cls.traasp_indexes,    cls.TABSETUP_CONSTR_TRAASP,    cls.TABVOICE_TRAASP    ),
                (cls.TABNAME_TRAPOR,    cls.TABDESC_TRAPOR,    cls.trapor,    cls.trapor_indexes,    cls.TABSETUP_CONSTR_TRAPOR,    cls.TABVOICE_TRAPOR    ),
                (cls.TABNAME_TRACON,    cls.TABDESC_TRACON,    cls.tracon,    cls.tracon_indexes,    cls.TABSETUP_CONSTR_TRACON,    cls.TABVOICE_TRACON    ),
                (cls.TABNAME_CFGEFF,    cls.TABDESC_CFGEFF,    cls.cfgeff,    cls.cfgeff_indexes,    cls.TABSETUP_CONSTR_CFGEFF,    cls.TABVOICE_CFGEFF    ),
                (cls.TABNAME_ALLEGATI,  cls.TABDESC_ALLEGATI,  cls.allegati,  cls.allegati_indexes,  cls.TABSETUP_CONSTR_ALLEGATI,  cls.TABVOICE_ALLEGATI  ),
                (cls.TABNAME_LIQIVA,    cls.TABDESC_LIQIVA,    cls.liqiva,    cls.liqiva_indexes,    cls.TABSETUP_CONSTR_LIQIVA,    cls.TABVOICE_LIQIVA    ),
                (cls.TABNAME_CFGSETUP,  cls.TABDESC_CFGSETUP,  cls.cfgsetup,  cls.cfgsetup_indexes,  cls.TABSETUP_CONSTR_CFGSETUP,  cls.TABVOICE_CFGSETUP  ),
                (cls.TABNAME_CFGFTDIF,  cls.TABDESC_CFGFTDIF,  cls.cfgftdif,  cls.cfgftdif_indexes,  cls.TABSETUP_CONSTR_CFGFTDIF,  cls.TABVOICE_CFGFTDIF  ),
                (cls.TABNAME_CFGFTDDR,  cls.TABDESC_CFGFTDDR,  cls.cfgftddr,  cls.cfgftddr_indexes,  cls.TABSETUP_CONSTR_CFGFTDDR,  cls.TABVOICE_CFGFTDDR  ),
                (cls.TABNAME_CFGPERM,   cls.TABDESC_CFGPERM,   cls.cfgperm,   cls.cfgperm_indexes,   cls.TABSETUP_CONSTR_CFGPERM,   cls.TABVOICE_CFGPERM   ),
                (cls.TABNAME_EFFETTI,   cls.TABDESC_EFFETTI,   cls.effetti,   cls.effetti_indexes,   cls.TABSETUP_CONSTR_EFFETTI,   cls.TABVOICE_EFFETTI   ),
                (cls.TABNAME_SCADGRP,   cls.TABDESC_SCADGRP,   cls.scadgrp,   cls.scadgrp_indexes,   cls.TABSETUP_CONSTR_SCADGRP,   cls.TABVOICE_SCADGRP   ),
                (cls.TABNAME_PROMEM,    cls.TABDESC_PROMEM,    cls.promem,    cls.promem_indexes,    cls.TABSETUP_CONSTR_PROMEM,    cls.TABVOICE_PROMEM    ),
                (cls.TABNAME_PROMEMU,   cls.TABDESC_PROMEMU,   cls.promemu,   cls.promemu_indexes,   cls.TABSETUP_CONSTR_PROMEMU,   cls.TABVOICE_PROMEMU   ),
                (cls.TABNAME_CFGMAGRIV, cls.TABDESC_CFGMAGRIV, cls.cfgmagriv, cls.cfgmagriv_indexes, cls.TABSETUP_CONSTR_CFGMAGRIV, cls.TABVOICE_CFGMAGRIV ),
                (cls.TABNAME_MARART,    cls.TABDESC_MARART,    cls.marart,    cls.marart_indexes,    cls.TABSETUP_CONSTR_MARART,    cls.TABVOICE_MARART    ),
                (cls.TABNAME_PDCRANGE,  cls.TABDESC_PDCRANGE,  cls.pdcrange,  cls.pdcrange_indexes,  cls.TABSETUP_CONSTR_PDCRANGE,  cls.TABVOICE_PDCRANGE  ),
                (cls.TABNAME_BRIMAS,    cls.TABDESC_BRIMAS,    cls.brimas,    cls.brimas_indexes,    cls.TABSETUP_CONSTR_BRIMAS,    cls.TABVOICE_BRIMAS    ),
                (cls.TABNAME_BRICON,    cls.TABDESC_BRICON,    cls.bricon,    cls.bricon_indexes,    cls.TABSETUP_CONSTR_BRICON,    cls.TABVOICE_BRICON    ),
                (cls.TABNAME_PRODPRO,   cls.TABDESC_PRODPRO,   cls.prodpro,   cls.prodpro_indexes,   cls.TABSETUP_CONSTR_PRODPRO,   cls.TABVOICE_PRODPRO   ),
                (cls.TABNAME_GRUPREZ,   cls.TABDESC_GRUPREZ,   cls.gruprez,   cls.gruprez_indexes,   cls.TABSETUP_CONSTR_GRUPREZ,   cls.TABVOICE_GRUPREZ   ),
                (cls.TABNAME_SCONTICC,  cls.TABDESC_SCONTICC,  cls.sconticc,  cls.sconticc_indexes,  cls.TABSETUP_CONSTR_SCONTICC,  cls.TABVOICE_SCONTICC  ),
                (cls.TABNAME_PDT_H,     cls.TABDESC_PDT_H,     cls.pdt_h,     cls.pdt_h_indexes,     cls.TABSETUP_CONSTR_PDT_H,     cls.TABVOICE_PDT_H     ),
                (cls.TABNAME_PDT_B,     cls.TABDESC_PDT_B,     cls.pdt_b,     cls.pdt_b_indexes,     cls.TABSETUP_CONSTR_PDT_B,     cls.TABVOICE_PDT_B     ),
                (cls.TABNAME_PROCOS,    cls.TABDESC_PROCOS,    cls.procos,    cls.procos_index,      cls.TABSETUP_CONSTR_PROCOS,    cls.TABVOICE_PROCOS    ),
                (cls.TABNAME_PROGIA,    cls.TABDESC_PROGIA,    cls.progia,    cls.progia_index,      cls.TABSETUP_CONSTR_PROGIA,    cls.TABVOICE_PROGIA    ),
                (cls.TABNAME_PROMO,     cls.TABDESC_PROMO,     cls.promo,     cls.promo_index,       cls.TABSETUP_CONSTR_PROMO,     cls.TABVOICE_PROMO     ),
                (cls.TABNAME_STATPDC,   cls.TABDESC_STATPDC,   cls.statpdc,   cls.statpdc_indexes,   cls.TABSETUP_CONSTR_STATPDC,   cls.TABVOICE_STATPDC   ),
                (cls.TABNAME_TIPEVENT,  cls.TABDESC_TIPEVENT,  cls.tipevent,  cls.tipevent_indexes,  cls.TABSETUP_CONSTR_TIPEVENT,  cls.TABVOICE_TIPEVENT  ),
                (cls.TABNAME_EVENTI,    cls.TABDESC_EVENTI,    cls.eventi,    cls.eventi_indexes,    cls.TABSETUP_CONSTR_EVENTI,    cls.TABVOICE_EVENTI    ),
                (cls.TABNAME_DOCSEMAIL, cls.TABDESC_DOCSEMAIL, cls.docsemail, cls.docsemail_indexes, cls.TABSETUP_CONSTR_DOCSEMAIL, cls.TABVOICE_DOCSEMAIL ),
                (cls.TABNAME_VARLIST,   cls.TABDESC_VARLIST,   cls.varlist,   cls.varlist_indexes,   cls.TABSETUP_CONSTR_VARLIST,   cls.TABVOICE_VARLIST   ),
            ]
            
            #alterazioni strutture tabelle da applicazione personalizzata
            cls.modstru(initall)
        
        
        @classmethod
        def set_constraints(cls, tablename, relations):
            for r_constr, r_field, r_type in relations:
                r_constr.append([tablename, r_field, r_type])
        
        
        @classmethod
        def modstru(cls, initall):
            import report
            if hasattr(report, 'pathalt'):
                #alterazioni strutture tabelle da plugin presenti
                del report.pathalt[:]
            #modifiche strutturali dei plugins
            for p in plugins:
                m = plugins[p]
                if hasattr(m, 'TabStru'):
                    m.TabStru(cls)
                report.pathalt.append(p)
            #modifiche strutturali della personalizzazione
            try:
                import custapp
                if hasattr(custapp, 'TabStru'):
                    custapp.TabStru(cls)
            except ImportError, e:
                pass
        
        
        @classmethod
        def getcolwidth(cls, table, column):
            out = None
            tables = cls.tabelle
            tabdef = filter(lambda x: x[0] == table, tables)
            if tabdef:
                stru = tabdef[0][2]
                coldef = filter(lambda x: x[0] == column, stru)
                if coldef:
                    out = coldef[0][2]
            return out
        
        
        __min_compat_ver__ = version.__min_compat_ver__
        __min_compat_mod__ = version.__min_compat_mod__
        
        
        @classmethod
        def GetBaseTab(cls):
            return cls.BaseTab
            
        @classmethod
        def ReadAziendaSetup(cls):
            
            cfg = adb.DbTable(cls.TABNAME_CFGSETUP, 'cfg', writable=False)
            
            keys = cls.GetSetupKeys()
            for p in plugins:
                m = plugins[p]
                if hasattr(m, 'GetSetupKeys'):
                    keys += m.GetSetupKeys(cls)
            try:
                import custapp
                if hasattr(custapp, 'GetSetupKeys'):
                    keys += custapp.GetSetupKeys(cls)
            except ImportError, e:
                pass
            
            import awc.controls.entries as entries
            
            for name, key, col, conv, err in keys:
                if cfg.Retrieve("cfg.chiave=%s", key):
                    if cfg.OneRow():
                        v = conv(getattr(cfg, col))
                        setattr(cls, name, v)
                        if name == 'OPTDIGSEARCH':
                            import awc.controls.linktable as lt
                            lt.LinkTable.SetDigitSearchOnDescriz(v)
                        elif name == 'OPTTABSEARCH':
                            import awc.controls.linktable as lt
                            lt.LinkTable.SetTabSearchOnCode(True)
                            lt.LinkTable.SetTabSearchOnDescriz(v)
                        elif name == 'OPTRETSEARCH':
                            import awc.controls.linktable as lt
                            lt.LinkTable.SetRetSearchOnCode(True)
                            lt.LinkTable.SetRetSearchOnDescriz(v)
                        elif name == 'OPTSPASEARCH':
                            import awc.controls.linktable as lt
                            lt.LinkTable.SetSpaceSearch(v)
                        elif name == 'OPT_GC_PRINT':
                            entries.EnableGoogleCloudPrint(v)
                        elif name == 'OPT_GCP_USER':
                            entries.SetGoogleCloudPrintUsername(v)
                        elif name == 'OPT_GCP_PSWD':
                            p = v
                            try:
                                dec = base64.b64decode(v)
                                p = crypt.decrypt_data(dec)
                            except:
                                pass
                            entries.SetGoogleCloudPrintPassword(p)
                            cls.OPT_GCP_PSWD = p
                        elif name.endswith('_PASSWORD'):
                            p = v
                            try:
                                dec = base64.b64decode(v)
                                p = crypt.decrypt_data(dec)
                            except:
                                pass
                            setattr(cls, name, p)
                        if cls != Azienda.BaseTab_base:
                            #se è stata sovrascritta la classe BaseTab, scrivo 
                            #gli stessi settaggi anche nella sua forma base,
                            #che è già stata importata in svariati moduli
                            setattr(Azienda.BaseTab_base, name, v)
                    else:
                        if err is not None:
                            raise Azienda.BaseTab.AziendaSetupException, \
                                  """Configurazione azienda errata: manca """\
                                  """la definizione %s.\nVerificare il setup """\
                                  """dei dati aziendali.""" % err
            cls.defstru()
            cls.SetMailParams()
            cls.SetXmppParams()
            cls.SetNotifyClass()
            return True
        
        
        @classmethod
        def GetSetupKeys(cls):
            
            tc = 'del tipo di contabilità'
            d = 'del numero di decimali su'
            f = 'flag'
            i = 'importo'
            s = 'descriz'
            
            def _str(x):
                return str(x)
            def _int(x):
                return int(x or '0')
            def _flt(x):
                return float(x or 0)
            
            return [\
                ('TIPO_CONTAB',     'tipo_contab',        f, _str, tc),
                ('CONSOVGES',       'consovges',          f, _int, None),
                ('CONBILRICL',      'conbilricl',         f, _int, None),
                ('CONBILRCEE',      'conbilrcee',         f, _int, None),
                ('CONATTRITACC',    'conattritacc',       f, _int, None),
                ('CONPERRITACC',    'conperritacc',       i, _flt, None),
                ('CONCOMRITACC',    'concomritacc',       i, _flt, None),
                ('MAGPRE_DECIMALS', 'magdec_prez',        i, _int, '%si prezzi' % d),
                ('MAGQTA_DECIMALS', 'magdec_qta',         i, _int, '%slle quantità' % d),
                ('MAGEAN_PREFIX',   'mageanprefix',       s, _str, 'del prefisso EAN'),
                ('VALINT_DECIMALS', 'contab_decimp',      i, _int, '%slla valuta di conto' % d),
                ('MAGSCOCAT',       'magscocat',          f, _int, 'del flag di attivazione degli sconti per categoria'),
                ('MAGSCORPCOS',     'magscorpcos',        f, _str, 'del flag di scorporo iva dal costo di acquisto'),
                ('MAGSCORPPRE',     'magscorppre',        f, _str, 'del flag di scorporo iva dal prezzo di vendita'),
                ('GESFIDICLI',      'gesfidicli',         f, _str, 'del flag di attivazione fidi clienti'),
                ('MAGIMGPROD',      'magimgprod',         f, _str, 'del flag di attivazione immagine prodotto'),
                ('MAGDIGSEARCH',    'magdigsearch',       f, _int, 'del flag di ricerca immediata prodotti in digitazione codice'),
                ('MAGRETSEARCH',    'magretsearch',       f, _int, None),
                ('MAGEXCSEARCH',    'magexcsearch',       f, _int, None),
                ('OPTDIGSEARCH',    'optdigsearch',       f, _int, None),
                ('OPTTABSEARCH',    'opttabsearch',       f, _int, None),
                ('OPTRETSEARCH',    'optretsearch',       f, _int, None),
                ('OPTSPASEARCH',    'optspasearch',       f, _int, None),
                ('OPTLNKCRDPDC',    'optlnkcrdpdc',       f, _int, None),
                ('OPTLNKGRDPDC',    'optlnkgrdpdc',       f, _int, None),
                ('OPTLNKCRDCLI',    'optlnkcrdcli',       f, _int, None),
                ('OPTLNKGRDCLI',    'optlnkgrdcli',       f, _int, None),
                ('OPTLNKCRDFOR',    'optlnkcrdfor',       f, _int, None),
                ('OPTLNKGRDFOR',    'optlnkgrdfor',       f, _int, None),
                ('OPTNOTIFICHE',    'optnotifiche',       f, _int, None),
                ('OPTBACKUPDIR',    'optbackupdir',       s, _str, None),
                ('OPT_GC_PRINT',    'opt_gc_print',       f, _int, None),
                ('OPT_GCP_USER',    'opt_gcp_user',       s, _str, None),
                ('OPT_GCP_PSWD',    'opt_gcp_pswd',       s, _str, None),
                ('MAGATTGRIP',      'magattgrip',         f, _int, None),
                ('MAGATTGRIF',      'magattgrif',         f, _int, None),
                ('MAGCDEGRIP',      'magcdegrip',         f, _int, None),
                ('MAGCDEGRIF',      'magcdegrif',         f, _int, None),
                ('MAGDATGRIP',      'magdatgrip',         f, _int, 'del flag di gestione delle griglie prezzo per data'),
                ('MAGAGGGRIP',      'magagggrip',         f, _int, None),
                ('MAGALWGRIP',      'magalwgrip',         f, _int, None),
                ('MAGPZCONF',       'magpzconf',          f, _int, None),
                ('MAGPZGRIP',       'magpzgrip',          f, _int, None),
                ('MAGPPROMO',       'magppromo',          f, _int, None),
                ('MAGVISGIA',       'magvisgia',          f, _int, None),
                ('MAGVISPRE',       'magvispre',          f, _int, None),
                ('MAGVISCOS',       'magviscos',          f, _int, None),
                ('MAGVISCPF',       'magviscpf',          f, _int, None),
                ('MAGVISBCD',       'magvisbcd',          f, _int, None),
                ('MAGGESACC',       'maggesacc',          f, _int, None),
                ('MAGPROVATT',      'magprovatt',         f, _int, None),
                ('MAGPROVCLI',      'magprovcli',         f, _int, None),
                ('MAGPROVPRO',      'magprovpro',         f, _int, None),
                ('MAGPROVMOV',      'magprovmov',         f, _str, None),
                ('MAGPROVSEQ',      'magprovseq',         s, _str, None),
                ('MAGDEMSENDFLAG',  'docsemail_sendflag', f, _int, None),
                ('MAGDEMSENDDESC',  'docsemail_senddesc', s, _str, None),
                ('MAGDEMSENDADDR',  'docsemail_sendaddr', s, _str, None),
                ('MAGDEMDALLBODY',  'docsemail_dallbody', s, _str, None),
                ('MAGNOCODEDES',    'magnocodedes',       f, _int, None),
                ('MAGNOCODEVET',    'magnocodevet',       f, _int, None),
                ('MAGNOCDEFDES',    'magnocdefdes',       f, _int, None),
                ('MAGNOCDEFVET',    'magnocdefvet',       f, _int, None),
                ('MAGEXTRAVET',     'magextravet',        f, _int, None),
                ('MAGNUMSCO',       'magnumsco',          i, _int, None),
                ('MAGNUMRIC',       'magnumric',          i, _int, None),
                ('MAGNUMLIS',       'magnumlis',          i, _int, 'del numero di listini'),
                ('MAGRICLIS',       'magriclis',          i, _int, None),
                ('MAGSCOLIS',       'magscolis',          i, _int, None),
                ('MAGROWLIS',       'magrowlis',          f, _int, None),
                ('MAGVLIFOR',       'magvlifor',          f, _int, None),
                ('MAGVLIMAR',       'magvlimar',          f, _int, None),
                ('MAGVLICAT',       'magvlicat',          f, _int, None),
                ('MAGVLIGRU',       'magvligru',          f, _int, None),
                ('MAGDATLIS',       'magdatlis',          f, _int, 'del flag di gestione dei listini per data'),
                ('MAGFORLIS',       'magforlis',          f, _int, None),
                ('MAGBCOLIS',       'magbcolis',          f, _int, None),
                ('MAGERPLIS',       'magerplis',          i, _int, None),
                ('MAGESPLIS',       'magesplis',          i, _int, None),
                ('MAGVRGLIS',       'magvrglis',          i, _int, None),
                ('MAGVSGLIS',       'magvsglis',          i, _int, None),
                ('MAGREPLIS',       'magreplis',          f, _flt, None),
                ('MAGSEPLIS',       'magseplis',          f, _flt, None),
                ('MAGRELLIS',       'magrellis',          f, _flt, None),
                ('MAGSELLIS',       'magsellis',          f, _flt, None),
            ]
        
        
        @classmethod
        def SetMailParams(cls):
            from cfg.dbtables import EmailConfigTable
            try:
                e = EmailConfigTable()
                import comm.comsmtp as smtp
                smtp.SetSMTP_Addr(e.smtpaddr)
                smtp.SetSMTP_Port(e.smtpport)
                smtp.SetAUTH_User(e.authuser)
                smtp.SetAUTH_Pswd(e.GetAuthPassword())
                smtp.SetAUTH_TLS(e.authtls)
                smtp.SetSender(e.sender)
            except:
                pass
        
        
        @classmethod
        def SetXmppParams(cls):
            from cfg.dbtables import XmppConfigTable
            try:
                s = XmppConfigTable()
                import comm.comxmpp as xmpp
                xmpp.SetXMPP_Addr(s.xmppaddr)
                xmpp.SetXMPP_Port(s.xmppport)
                xmpp.SetAUTH_User(s.authuser)
                xmpp.SetAUTH_Pswd(s.GetAuthPassword())
                xmpp.SetOnlineOnly(s.onlineonly)
            except:
                pass
        
        
        @classmethod
        def SetNotifyClass(cls):
            class MessageBoxNotify:
                parent = None
                notifyWin = None
                def __init__(self, parent):
                    self.parent = parent
                def start(self, msg):
                    import awc.util as awu
                    self.notifyWin = awu.WaitDialog(self.parent, message=msg)
                def stop(self):
                    if self.notifyWin:
                        self.notifyWin.Destroy()
                    self.notifyWin = None
            import cfg.dbtables
            cfg.dbtables.EventiStdCallbacks = MessageBoxNotify
        
        
        @classmethod
        def TableName4TipAna(cls, tipo):
            if   tipo == "A": out = cls.TABNAME_CASSE
            elif tipo == "B": out = cls.TABNAME_BANCHE
            elif tipo == "C": out = cls.TABNAME_CLIENTI
            elif tipo == "F": out = cls.TABNAME_FORNIT
            else:             out = None
            return out
        
        
        @classmethod
        def GetValIntIntegersDisplay(cls):
            return 9
        
        @classmethod
        def GetValIntMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetValIntIntegersDisplay()
            if numdec is None:
                numdec = cls.VALINT_DECIMALS
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetValIntNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetValIntIntegersDisplay()
            if numdec is None:
                numdec = cls.VALINT_DECIMALS
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, groupDigits=True, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
        
        @classmethod
        def GetMagQtaIntegersDisplay(cls):
            return 9
        
        @classmethod
        def GetMagQtaMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetMagQtaIntegersDisplay()
            if numdec is None:
                numdec = cls.MAGQTA_DECIMALS
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetMagQtaNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetMagQtaIntegersDisplay()
            if numdec is None:
                numdec = cls.MAGQTA_DECIMALS
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, groupDigits=True, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
        
         
        @classmethod
        def GetMagPzcIntegersDisplay(cls):
            return 6
        
        @classmethod
        def GetMagPzcDecimalsDisplay(cls):
            return cls.MAGQTA_DECIMALS
        
        @classmethod
        def GetMagPzcMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetMagPzcIntegersDisplay()
            if numdec is None:
                numdec = cls.GetMagPzcDecimalsDisplay()
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetMagPzcNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetMagPzcIntegersDisplay()
            if numdec is None:
                numdec = cls.GetMagPzcDecimalsDisplay()
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, groupDigits=True, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
        
         
        @classmethod
        def GetMagPreIntegersDisplay(cls):
            return 6
        
        @classmethod
        def GetMagPreMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetMagPreIntegersDisplay()
            if numdec is None:
                numdec = cls.MAGPRE_DECIMALS
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetMagPreNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetMagPreIntegersDisplay()
            if numdec is None:
                numdec = cls.MAGPRE_DECIMALS
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, groupDigits=True, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
         
        @classmethod
        def GetMagScoIntegersDisplay(cls):
            return 2
        
        @classmethod
        def GetMagScoDecimalsDisplay(cls):
            return 2
        
        @classmethod
        def GetMagScoMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetMagScoIntegersDisplay()
            if numdec is None:
                numdec = cls.GetMagScoDecimalsDisplay()
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetMagScoNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetMagScoIntegersDisplay()
            if numdec is None:
                numdec = cls.GetMagScoDecimalsDisplay()
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, 
                                   groupDigits=True, allowNegative=True, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
         
        @classmethod
        def GetMagRicIntegersDisplay(cls):
            return 3
        
        @classmethod
        def GetMagRicDecimalsDisplay(cls):
            return 2
        
        @classmethod
        def GetMagRicMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetMagRicIntegersDisplay()
            if numdec is None:
                numdec = cls.GetMagRicDecimalsDisplay()
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetMagRicNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetMagRicIntegersDisplay()
            if numdec is None:
                numdec = cls.GetMagRicDecimalsDisplay()
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, 
                                   groupDigits=True, allowNegative=False, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
         
        @classmethod
        def GetPerGenIntegersDisplay(cls):
            return 2
        
        @classmethod
        def GetPerGenDecimalsDisplay(cls):
            return 2
        
        @classmethod
        def GetPerGenMaskInfo(cls, numint=None, numdec=None):
            if numint is None:
                numint = cls.GetPerGenIntegersDisplay()
            if numdec is None:
                numdec = cls.GetPerGenDecimalsDisplay()
            return gl.GRID_VALUE_FLOAT+":%d,%d" % (numint, numdec)
        
        @classmethod
        def GetPerGenNumCtrl(cls, parent, id, name, editable=True, numint=None, numdec=None, **kwa):
            if numint is None:
                numint = cls.GetPerGenIntegersDisplay()
            if numdec is None:
                numdec = cls.GetPerGenDecimalsDisplay()
            ctrl = numctrl.NumCtrl(parent, id or -1, 
                                   integerWidth=numint, fractionWidth=numdec, 
                                   groupDigits=True, allowNegative=True, **kwa)
            ctrl.SetName(name)
            ctrl.SetEditable(editable)
            return ctrl
        
        
        class AziendaSetupException(Exception):
            pass
    
    BaseTab_base = BaseTab


# ------------------------------------------------------------------------------


stati_cee = [["AUSTRIA",         "AT"],
             ["BELGIO",          "BE"],
             ["BULGARIA",        "BG"],
             ["CIPRO",           "CY"],
             ["DANIMARCA",       "DK"],
             ["ESTONIA",         "EE"], 
             ["FINLANDIA",       "FI"], 
             ["FRANCIA",         "FR"], 
             ["GERMANIA",        "DE"],
             ["GRAN BRETAGNA",   "GB"], 
             ["GRECIA",          "EL"],
             ["IRLANDA",         "IE"],
             ["ITALIA",          "IT"],
             ["LETTONIA",        "LV"],
             ["LITUANIA",        "LT"],
             ["LUSSEMBURGO",     "LU"],
             ["MALTA",           "MT"],
             ["OLANDA",          "NL"],
             ["POLONIA",         "PL"],
             ["PORTOGALLO",      "PT"], 
             ["REPUBBLICA CECA", "CZ"],
             ["ROMANIA",         "RO"],
             ["SLOVACCHIA",      "SK"],
             ["SLOVENIA",        "SI"],
             ["SPAGNA",          "ES"],
             ["SVEZIA",          "SE"],
             ["UNGHERIA",        "HU"],]


Azienda.BaseTab.defstru(initall=False)


if __name__ == '__main__':
    
    def ExportCSV(tab, tmpname, headings=None):
        import csv
        tmpfile = open(tmpname, 'wb')
        writer = csv.writer(tmpfile,
                            delimiter=';',
                            quotechar='"',
                            doublequote=True,
                            skipinitialspace=False,
                            lineterminator='\r\n',
                            quoting=csv.QUOTE_NONNUMERIC)
        csvrs = []
        if headings:
            csvrs.append([h for h in headings])
        csvrs += tab.GetRecordset()
        writer.writerows(csvrs)
        tmpfile.close()
        getattr(os, 'startfile')(tmpname)
    
    app = wx.PySimpleApp()
    
    bt = Azienda.BaseTab
    
    doc = adb.DbMem('c1,c2,c3,c4,c5')
    cnr = doc.CreateNewRow
    
    import awc.util as awu
    w = awu.WaitDialog(None, message="Documentazione strutture in corso...",
                       maximum=len(bt.tabelle))
    
    n = 0
    for nome, desc, stru, indi, cost, voic in bt.tabelle:
        print str(nome).ljust(12), desc
        cnr()
        doc.c1 = 'Nome:'
        doc.c2 = nome
        cnr()
        doc.c1 = 'Descrizione:'
        doc.c2 = desc
        cnr()
        cnr()
        doc.c1 = 'Struttura:'
        cnr()
        doc.c1 = 'Nome'
        doc.c2 = 'Tipo'
        doc.c3 = 'Lungh.'
        doc.c4 = 'Dec.'
        doc.c5 = 'Descrizione'
        for cnome, ctipo, clung, cdeci, cdesc, caddi in stru:
            cnr()
            doc.c1 = cnome
            doc.c2 = ctipo
            doc.c3 = clung
            doc.c4 = cdeci
            doc.c5 = cdesc
        cnr()
        cnr()
        cnr()
        n += 1
        w.SetValue(n)
    
    w.Destroy()
    
    ExportCSV(doc, 'stru.csv')#, 'c1 c2 c3 c4'.split())
