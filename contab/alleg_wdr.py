# -*- coding: UTF-8 -*-

#-----------------------------------------------------------------------------
# Python source generated by wxDesigner from file: alleg.wdr
# Do not modify this file, all changes will be lost!
#-----------------------------------------------------------------------------

# Include wxPython modules
import wx
import wx.grid
import wx.animate

# Custom source
from wx import Panel as wxPanel

from awc.controls.linktable import LinkTable
from awc.controls.textctrl import TextCtrl
from awc.controls.datectrl import DateCtrl
from awc.controls.numctrl import NumCtrl
from awc.controls.checkbox import CheckBox

from Env import Azienda
bt = Azienda.BaseTab



# Window functions

ID_CLIFOR = 10000
ID_TEXT = 10001
ID_DATA1 = 10002
ID_DATA2 = 10003
ID_SOLOALL = 10004
ID_UPDATE = 10005
ID_PANELGRID = 10006
ID_PRINT = 10007

def AllegatiPanelFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = wx.FlexGridSizer( 1, 0, 0, 0 )
    
    item2 = wx.RadioBox( parent, ID_CLIFOR, "Tipo", wx.DefaultPosition, wx.DefaultSize, 
        ["Clienti","Fornitori"] , 1, wx.RA_SPECIFY_ROWS )
    item1.Add( item2, 0, wx.GROW|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

    item4 = wx.StaticBox( parent, -1, "Periodo" )
    item3 = wx.StaticBoxSizer( item4, wx.VERTICAL )
    
    item5 = wx.FlexGridSizer( 1, 0, 0, 0 )
    
    item6 = wx.StaticText( parent, ID_TEXT, "Registrazioni dal:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item5.Add( item6, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item7 = DateCtrl( parent, ID_DATA1, "", wx.DefaultPosition, [80,-1], 0 )
    item7.SetName( "datdoc" )
    item5.Add( item7, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item8 = wx.StaticText( parent, ID_TEXT, "al:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item5.Add( item8, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item9 = DateCtrl( parent, ID_DATA2, "", wx.DefaultPosition, [80,-1], 0 )
    item9.SetName( "datdoc" )
    item5.Add( item9, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item10 = wx.CheckBox( parent, ID_SOLOALL, "Solo anagrafiche in allegato", wx.DefaultPosition, wx.DefaultSize, 0 )
    item10.SetValue( True )
    item5.Add( item10, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item11 = wx.Button( parent, ID_UPDATE, "Aggiorna", wx.DefaultPosition, wx.DefaultSize, 0 )
    item11.SetDefault()
    item5.Add( item11, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item5.AddGrowableCol( 5 )

    item3.Add( item5, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item1.Add( item3, 0, wx.GROW|wx.ALIGN_CENTER_HORIZONTAL|wx.RIGHT|wx.TOP|wx.BOTTOM, 5 )

    item1.AddGrowableCol( 1 )

    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item12 = wx.StaticText( parent, ID_TEXT, "Elenco anagrafiche e importi", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.SetBackgroundColour( wx.LIGHT_GREY )
    item0.Add( item12, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.TOP, 5 )

    item13 = wx.Panel( parent, ID_PANELGRID, wx.DefaultPosition, [750,300], wx.SUNKEN_BORDER )
    item0.Add( item13, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item14 = wx.BoxSizer( wx.HORIZONTAL )
    
    item15 = wx.Button( parent, ID_PRINT, "Stampa", wx.DefaultPosition, wx.DefaultSize, 0 )
    item15.Enable(False)
    item14.Add( item15, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item0.Add( item14, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

    item0.AddGrowableCol( 0 )

    item0.AddGrowableRow( 2 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0


def DettaglioRigheIvaFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = wx.Panel( parent, ID_PANELGRID, wx.DefaultPosition, [900,400], wx.SUNKEN_BORDER )
    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item0.AddGrowableCol( 0 )

    item0.AddGrowableRow( 0 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

# Menubar functions

# Toolbar functions

# Bitmap functions


# End of generated file
