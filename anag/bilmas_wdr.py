# -*- coding: UTF-8 -*-

#-----------------------------------------------------------------------------
# Python source generated by wxDesigner from file: bilmas.wdr
# Do not modify this file, all changes will be lost!
#-----------------------------------------------------------------------------

# Include wxPython modules
import wx
import wx.grid
import wx.animate

# Custom source
from anag.basetab import AnagCardPanel

from awc.controls.linktable import LinkTable
from awc.controls.radiobox import RadioBox

from awc.controls.attachbutton import AttachmentButton

from Env import Azienda
bt = Azienda.BaseTab



# Window functions

ID_ANAGMAIN = 16000
ID_RADIOBIL = 16001

def BilMasCardFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = AnagCardPanel(parent)
    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item2 = RadioBox( parent, ID_RADIOBIL, "Tipologia:", wx.DefaultPosition, [350,-1], 
        ["Stato Patrimoniale","Conto Economico","Conti d'Ordine"] , 1, wx.RA_SPECIFY_ROWS )
    item2.SetName( "tipo" )
    item0.Add( item2, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item0.Add( [ 20, 120 ] , 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item0.AddGrowableCol( 0 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

ID_LBL_SEARCHRESULTS = 16002
ID_FILT_PEO = 16003

def BilMasSpecSearchFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = wx.StaticText( parent, ID_LBL_SEARCHRESULTS, "Mostra solo i mastri relativi a:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTRE )
    item1.SetBackgroundColour( wx.LIGHT_GREY )
    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, 5 )

    item2 = RadioBox( parent, ID_FILT_PEO, "Bilancio", wx.DefaultPosition, wx.DefaultSize, 
        ["Tutti i mastri","Stato Patrimoniale","Conto Economico","Conti d'Ordine"] , 1, wx.RA_SPECIFY_ROWS )
    item2.SetName( "tipo" )
    item0.Add( item2, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item0.AddGrowableCol( 0 )

    item0.AddGrowableRow( 5 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

# Menubar functions

# Toolbar functions

# Bitmap functions


# End of generated file
