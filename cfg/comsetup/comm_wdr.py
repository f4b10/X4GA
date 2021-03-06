# -*- coding: UTF-8 -*-

#-----------------------------------------------------------------------------
# Python source generated by wxDesigner from file: comm.wdr
# Do not modify this file, all changes will be lost!
#-----------------------------------------------------------------------------

# Include wxPython modules
import wx
import wx.grid
import wx.animate

# Custom source
import wx
from awc.util import GetParentFrame

from awc.controls.textctrl import TextCtrl, TextCtrl_LC
from awc.controls.numctrl import NumCtrl
from awc.controls.linktable import LinkTable
from awc.controls.checkbox import CheckBox
from awc.controls.radiobox import RadioBox
from awc.controls.entries import MailEntryCtrl

import Env
bt = Env.Azienda.BaseTab


class EmailAuthCheckBox(CheckBox):

    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=[1,0])
        self.Bind(wx.EVT_CHECKBOX, self.OnAuthChanged)

    def OnAuthChanged(self, event):
        self.EnableUserPW()
        event.Skip()

    def EnableUserPW(self):
        e = self.IsChecked()
        f = GetParentFrame(self)
        def cn(name):
            return f.FindWindowByName(name)
        sf = False
        for name in 'authuser authpswd authtls'.split():
            c = cn(name)
            c.Enable(e)
            if e and sf:
                wx.CallAfter(lambda: c.SetFocus())
                sf = False

class UnoZeroCheckBox(CheckBox):

    def __init__(self, *args, **kwargs):
        CheckBox.__init__(self, *args, **kwargs)
        self.SetDataLink(values=[1,0])



# Window functions

ID_TEXT = 16000
ID_SMTPADDR = 16001
ID_SENDER = 16002
ID_SMTPPORT = 16003
ID_AUTHREQ = 16004
ID_AUTHTLS = 16005
ID_AUTHUSER = 16006
ID_AUTHPSWD = 16007
ID_BTNTEST = 16008
ID_BTNOK = 16009

def EmailConfigFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item2 = wx.StaticBox( parent, -1, u"Parametri collegamento server posta elettronica" )
    item1 = wx.StaticBoxSizer( item2, wx.VERTICAL )
    
    item3 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item4 = wx.StaticText( parent, ID_TEXT, u"Server SMTP:", wx.DefaultPosition, [100,-1], wx.ALIGN_RIGHT )
    item3.Add( item4, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item5 = TextCtrl_LC( parent, ID_SMTPADDR, "", wx.DefaultPosition, [300,-1], 0 )
    item5.SetName( "smtpaddr" )
    item3.Add( item5, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item6 = wx.StaticText( parent, ID_TEXT, u"Indirizzo mittente:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item3.Add( item6, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item7 = TextCtrl_LC( parent, ID_SENDER, "", wx.DefaultPosition, [200,-1], 0 )
    item7.SetName( "sender" )
    item3.Add( item7, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item8 = wx.StaticText( parent, ID_TEXT, u"Porta (25):", wx.DefaultPosition, wx.DefaultSize, 0 )
    item3.Add( item8, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item9 = wx.FlexGridSizer( 1, 0, 0, 0 )
    
    item10 = NumCtrl(parent, ID_SMTPPORT, integerWidth=4, allowNegative=False, groupDigits=False); item10.SetName("smtpport")
    item9.Add( item10, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item11 = EmailAuthCheckBox( parent, ID_AUTHREQ, u"Effettua il login", wx.DefaultPosition, wx.DefaultSize, 0 )
    item11.SetName( "authreq" )
    item9.Add( item11, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item12 = UnoZeroCheckBox( parent, ID_AUTHTLS, u"Usa TLS (porta=587)", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.SetName( "authtls" )
    item9.Add( item12, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item3.Add( item9, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item3.AddGrowableCol( 1 )

    item1.Add( item3, 0, wx.GROW, 5 )

    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item14 = wx.StaticBox( parent, -1, u"Parametri per l'autenticazione, se necessari" )
    item13 = wx.StaticBoxSizer( item14, wx.VERTICAL )
    
    item15 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item16 = wx.StaticText( parent, ID_TEXT, u"Utente:", wx.DefaultPosition, [100,-1], wx.ALIGN_RIGHT )
    item15.Add( item16, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item17 = TextCtrl_LC( parent, ID_AUTHUSER, "", wx.DefaultPosition, [300,-1], 0 )
    item17.SetName( "authuser" )
    item15.Add( item17, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item18 = wx.StaticText( parent, ID_TEXT, u"Password:", wx.DefaultPosition, [100,-1], wx.ALIGN_RIGHT )
    item15.Add( item18, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item19 = TextCtrl_LC( parent, ID_AUTHPSWD, "", wx.DefaultPosition, [300,-1], wx.TE_PASSWORD )
    item19.SetName( "authpswd" )
    item15.Add( item19, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item15.AddGrowableCol( 1 )

    item13.Add( item15, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item0.Add( item13, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item20 = wx.BoxSizer( wx.HORIZONTAL )
    
    item21 = wx.Button( parent, ID_BTNTEST, u"Test", wx.DefaultPosition, wx.DefaultSize, 0 )
    item21.SetName( "btntest" )
    item20.Add( item21, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item22 = wx.Button( parent, ID_BTNOK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
    item22.SetName( "btnok" )
    item20.Add( item22, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item0.Add( item20, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

    item0.AddGrowableCol( 0 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

ID_XMPPADDR = 16010
ID_XMPPPORT = 16011
ID_ONLINEONLY = 16012

def XmppConfigFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item2 = wx.StaticBox( parent, -1, u"Parametri collegamento server messaggistica" )
    item1 = wx.StaticBoxSizer( item2, wx.VERTICAL )
    
    item3 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item4 = wx.StaticText( parent, ID_TEXT, u"Server XMPP:", wx.DefaultPosition, [100,-1], wx.ALIGN_RIGHT )
    item3.Add( item4, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item5 = TextCtrl_LC( parent, ID_XMPPADDR, "", wx.DefaultPosition, [300,-1], 0 )
    item5.SetName( "xmppaddr" )
    item3.Add( item5, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item6 = wx.StaticText( parent, ID_TEXT, u"Porta (5222):", wx.DefaultPosition, wx.DefaultSize, 0 )
    item3.Add( item6, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item7 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item8 = NumCtrl(parent, ID_XMPPPORT, integerWidth=4, allowNegative=False, groupDigits=False); item8.SetName("xmppport")
    item7.Add( item8, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item9 = UnoZeroCheckBox( parent, ID_ONLINEONLY, u"Invia solo se il destinatario risulta online", wx.DefaultPosition, wx.DefaultSize, 0 )
    item9.SetName( "onlineonly" )
    item7.Add( item9, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item3.Add( item7, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item10 = wx.StaticText( parent, ID_TEXT, u"JID mittente:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item3.Add( item10, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item11 = TextCtrl_LC( parent, ID_AUTHUSER, "", wx.DefaultPosition, [200,-1], 0 )
    item11.SetName( "authuser" )
    item3.Add( item11, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item12 = wx.StaticText( parent, ID_TEXT, u"Password:", wx.DefaultPosition, [100,-1], wx.ALIGN_RIGHT )
    item3.Add( item12, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item13 = TextCtrl_LC( parent, ID_AUTHPSWD, "", wx.DefaultPosition, [300,-1], wx.TE_PASSWORD )
    item13.SetName( "authpswd" )
    item3.Add( item13, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item3.AddGrowableCol( 1 )

    item1.Add( item3, 0, wx.GROW, 5 )

    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item14 = wx.BoxSizer( wx.HORIZONTAL )
    
    item15 = wx.Button( parent, ID_BTNTEST, u"Test", wx.DefaultPosition, wx.DefaultSize, 0 )
    item15.SetName( "btntest" )
    item14.Add( item15, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item16 = wx.Button( parent, ID_BTNOK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
    item16.SetName( "btnok" )
    item14.Add( item16, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item0.Add( item14, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

    item0.AddGrowableCol( 0 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

# Menubar functions

# Toolbar functions

# Bitmap functions


# End of generated file
