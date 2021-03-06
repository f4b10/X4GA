# -*- coding: UTF-8 -*-

#-----------------------------------------------------------------------------
# Python source generated by wxDesigner from file: stat.wdr
# Do not modify this file, all changes will be lost!
#-----------------------------------------------------------------------------

# Include wxPython modules
import wx
import wx.grid
import wx.animate

# Custom source
from wx import Panel as wxPanel
from wx.lib import masked

from awc.controls.linktable import LinkTable
from awc.controls.datectrl import DateCtrl
from awc.controls.textctrl import TextCtrl
from awc.controls.checkbox import CheckBox
from awc.controls.notebook import Notebook
from awc.controls.numctrl import NumCtrl

from anag.prod import ProdDialog
from anag.catart import CatArtDialog
from anag.gruart import GruArtDialog
from anag.marart import MarArtDialog
from anag.tipart import TipArtDialog
from anag.aliqiva import AliqIvaDialog
from anag.fornit import FornitDialog
from anag.mag import MagazzDialog
from anag.agenti import AgentiDialog
from anag.zone import ZoneDialog
from anag.clienti import ClientiDialog

from anag.lib import LinkTableProd

from Env import Azienda
bt = Azienda.BaseTab



# Window functions

ID_TEXT = 14000
ID_PDC1 = 14001
ID_PDC2 = 14002
ID_AGE1 = 14003
ID_AGE2 = 14004
ID_ZONA1 = 14005
ID_ZONA2 = 14006
ID_DATA1 = 14007
ID_DATA2 = 14008
ID_ORDER = 14009
ID_TIPART1 = 14010
ID_TIPART2 = 14011
ID_CATART1 = 14012
ID_CATART2 = 14013
ID_GRUART1 = 14014
ID_GRUART2 = 14015
ID_MARART1 = 14016
ID_MARART2 = 14017
ID_FORNIT1 = 14018
ID_FORNIT2 = 14019
ID_UPDATE = 14020
ID_PRINT = 14021
ID_PANGRIDSINT = 14022

def PdcFtProdFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item2 = wx.FlexGridSizer( 1, 0, 0, 0 )
    
    item3 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item5 = wx.StaticBox( parent, -1, "Anagrafiche" )
    item4 = wx.StaticBoxSizer( item5, wx.VERTICAL )
    
    item6 = wx.FlexGridSizer( 0, 3, 0, 0 )
    
    item7 = wx.StaticText( parent, ID_TEXT, "", wx.DefaultPosition, wx.DefaultSize, 0 )
    item6.Add( item7, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item8 = wx.StaticText( parent, ID_TEXT, "Da:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item6.Add( item8, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item9 = wx.StaticText( parent, ID_TEXT, "A:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item6.Add( item9, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5 )

    item10 = wx.StaticText( parent, ID_TEXT, "Cliente:", wx.DefaultPosition, [50,-1], wx.ALIGN_RIGHT )
    item6.Add( item10, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item11 = LinkTable(parent, ID_PDC1); item11.SetDataLink(bt.TABNAME_PDC, "pdc1", ClientiDialog)
    item6.Add( item11, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item12 = LinkTable(parent, ID_PDC2); item12.SetDataLink(bt.TABNAME_PDC, "pdc2", ClientiDialog)
    item6.Add( item12, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item13 = wx.StaticText( parent, ID_TEXT, "Agente:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
    item6.Add( item13, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item14 = LinkTable(parent, ID_AGE1); item14.SetDataLink(bt.TABNAME_AGENTI, "age1", AgentiDialog)
    item6.Add( item14, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item15 = LinkTable(parent, ID_AGE2); item15.SetDataLink(bt.TABNAME_AGENTI, "age2", AgentiDialog)
    item6.Add( item15, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item16 = wx.StaticText( parent, ID_TEXT, "Zona:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item6.Add( item16, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item17 = LinkTable(parent, ID_ZONA1); item17.SetDataLink(bt.TABNAME_ZONE, "zona1", ZoneDialog)
    item6.Add( item17, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item18 = LinkTable(parent, ID_ZONA2); item18.SetDataLink(bt.TABNAME_ZONE, "zona2", ZoneDialog)
    item6.Add( item18, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item6.AddGrowableCol( 1 )

    item6.AddGrowableCol( 2 )

    item4.Add( item6, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item3.Add( item4, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item19 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item21 = wx.StaticBox( parent, -1, "Periodo" )
    item20 = wx.StaticBoxSizer( item21, wx.VERTICAL )
    
    item22 = wx.FlexGridSizer( 0, 3, 0, 0 )
    
    item23 = wx.StaticText( parent, ID_TEXT, "", wx.DefaultPosition, wx.DefaultSize, 0 )
    item22.Add( item23, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item24 = wx.StaticText( parent, ID_TEXT, "Da:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item22.Add( item24, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item25 = wx.StaticText( parent, ID_TEXT, "A:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item22.Add( item25, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5 )

    item26 = wx.StaticText( parent, ID_TEXT, "Data:", wx.DefaultPosition, [50,-1], wx.ALIGN_RIGHT )
    item22.Add( item26, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item27 = DateCtrl( parent, ID_DATA1, "", wx.DefaultPosition, [80,-1], 0 )
    item27.SetName( "data1" )
    item22.Add( item27, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item28 = DateCtrl( parent, ID_DATA2, "", wx.DefaultPosition, [80,-1], 0 )
    item28.SetName( "data2" )
    item22.Add( item28, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item22.AddGrowableCol( 1 )

    item22.AddGrowableCol( 2 )

    item20.Add( item22, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item19.Add( item20, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item29 = wx.RadioBox( parent, ID_ORDER, "Ordina per:", wx.DefaultPosition, wx.DefaultSize, 
        ["Prodotto","Data di vendita"] , 1, wx.RA_SPECIFY_COLS )
    item29.SetName( "order" )
    item19.Add( item29, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item19.AddGrowableCol( 1 )

    item3.Add( item19, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item3.AddGrowableCol( 0 )

    item3.AddGrowableRow( 1 )

    item2.Add( item3, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item31 = wx.StaticBox( parent, -1, "Prodotti" )
    item30 = wx.StaticBoxSizer( item31, wx.VERTICAL )
    
    item32 = wx.FlexGridSizer( 0, 3, 0, 0 )
    
    item33 = wx.StaticText( parent, ID_TEXT, "", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item33, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item34 = wx.StaticText( parent, ID_TEXT, "Da:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item34, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item35 = wx.StaticText( parent, ID_TEXT, "A:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item35, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5 )

    item36 = wx.StaticText( parent, ID_TEXT, "Tipo:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item36, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item37 = LinkTable(parent, ID_TIPART1); item37.SetDataLink(bt.TABNAME_TIPART, "tipart1", TipArtDialog)
    item32.Add( item37, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item38 = LinkTable(parent, ID_TIPART2); item38.SetDataLink(bt.TABNAME_TIPART, "tipart2", TipArtDialog)
    item32.Add( item38, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item39 = wx.StaticText( parent, ID_TEXT, "Categoria:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item39, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item40 = LinkTable(parent, ID_CATART1); item40.SetDataLink(bt.TABNAME_CATART, "catart1", CatArtDialog)
    item32.Add( item40, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item41 = LinkTable(parent, ID_CATART2); item41.SetDataLink(bt.TABNAME_CATART, "catart2", CatArtDialog)
    item32.Add( item41, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item42 = wx.StaticText( parent, ID_TEXT, "Gruppo:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item42, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item43 = LinkTable(parent, ID_GRUART1); item43.SetDataLink(bt.TABNAME_GRUART, "gruart1", GruArtDialog)
    item32.Add( item43, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item44 = LinkTable(parent, ID_GRUART2); item44.SetDataLink(bt.TABNAME_GRUART, "gruart2", GruArtDialog)
    item32.Add( item44, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item45 = wx.StaticText( parent, ID_TEXT, "Marca:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item45, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5 )

    item46 = LinkTable(parent, ID_MARART1); item46.SetDataLink(bt.TABNAME_MARART, "marart1", MarArtDialog)
    item32.Add( item46, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item47 = LinkTable(parent, ID_MARART2); item47.SetDataLink(bt.TABNAME_MARART, "marart2", MarArtDialog)
    item32.Add( item47, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item48 = wx.StaticText( parent, ID_TEXT, "Fornitore:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item32.Add( item48, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5 )

    item49 = LinkTable(parent, ID_FORNIT1); item49.SetDataLink(bt.TABNAME_PDC, "fornit1", FornitDialog)
    item32.Add( item49, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5 )

    item50 = LinkTable(parent, ID_FORNIT2); item50.SetDataLink(bt.TABNAME_PDC, "fornit2", FornitDialog)
    item32.Add( item50, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5 )

    item32.AddGrowableCol( 1 )

    item32.AddGrowableCol( 2 )

    item30.Add( item32, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item2.Add( item30, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP|wx.BOTTOM, 5 )

    item2.AddGrowableCol( 0 )

    item2.AddGrowableCol( 1 )

    item2.AddGrowableRow( 0 )

    item1.Add( item2, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item51 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item52 = wx.Button( parent, ID_UPDATE, "Aggiorna", wx.DefaultPosition, wx.DefaultSize, 0 )
    item52.SetDefault()
    item51.Add( item52, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP|wx.BOTTOM, 5 )

    item53 = wx.Button( parent, ID_PRINT, "&Lista", wx.DefaultPosition, wx.DefaultSize, 0 )
    item51.Add( item53, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM, 5 )

    item1.Add( item51, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 5 )

    item1.AddGrowableCol( 0 )

    item1.AddGrowableRow( 0 )

    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item54 = wx.Panel( parent, ID_PANGRIDSINT, wx.DefaultPosition, [800,400], wx.SUNKEN_BORDER )
    item0.Add( item54, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item0.AddGrowableCol( 0 )

    item0.AddGrowableRow( 1 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

ID_BUTUPD = 14023
ID_PANGRIDVEN = 14024
ID_TOTRICAVO = 14025
ID_TOTCOSTO = 14026
ID_TOTUTILE = 14027
ID_PRCMAR = 14028
ID_PRCRIC = 14029
ID_BUTPRT = 14030

def ReddVendFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = wx.FlexGridSizer( 1, 0, 0, 0 )
    
    item3 = wx.StaticBox( parent, -1, "Selezioni" )
    item2 = wx.StaticBoxSizer( item3, wx.HORIZONTAL )
    
    item4 = wx.StaticText( parent, ID_TEXT, "Vendite dal:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item2.Add( item4, 0, wx.ALIGN_CENTER|wx.LEFT|wx.TOP|wx.BOTTOM, 5 )

    item5 = DateCtrl( parent, ID_DATA1, "", wx.DefaultPosition, [80,-1], 0 )
    item5.SetName( "data1" )
    item2.Add( item5, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item6 = wx.StaticText( parent, ID_TEXT, "al:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item2.Add( item6, 0, wx.ALIGN_CENTER|wx.LEFT|wx.TOP|wx.BOTTOM, 5 )

    item7 = DateCtrl( parent, ID_DATA2, "", wx.DefaultPosition, [80,-1], 0 )
    item7.SetName( "data2" )
    item2.Add( item7, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item1.Add( item2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item8 = wx.Button( parent, ID_BUTUPD, "Aggiorna", wx.DefaultPosition, wx.DefaultSize, 0 )
    item8.SetDefault()
    item8.SetName( "butupd" )
    item1.Add( item8, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

    item1.AddGrowableCol( 1 )

    item0.Add( item1, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

    item9 = wx.StaticText( parent, ID_TEXT, "Elenco delle vendite:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item9.SetForegroundColour( wx.BLUE )
    item0.Add( item9, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.TOP, 5 )

    item10 = wx.Panel( parent, ID_PANGRIDVEN, wx.DefaultPosition, [700,400], wx.SUNKEN_BORDER )
    item10.SetName( "pangridven" )
    item0.Add( item10, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item11 = wx.FlexGridSizer( 0, 2, 0, 0 )
    
    item12 = wx.FlexGridSizer( 0, 5, 0, 0 )
    
    item13 = wx.StaticText( parent, ID_TEXT, "Tot.Ricavo:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.Add( item13, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.TOP, 5 )

    item14 = wx.StaticText( parent, ID_TEXT, "Tot.Costo:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.Add( item14, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.TOP, 5 )

    item15 = wx.StaticText( parent, ID_TEXT, "Tot.Utile:", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.Add( item15, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.TOP, 5 )

    item16 = wx.StaticText( parent, ID_TEXT, "%Margine", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.Add( item16, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.TOP, 5 )

    item17 = wx.StaticText( parent, ID_TEXT, "%Ricarica", wx.DefaultPosition, wx.DefaultSize, 0 )
    item12.Add( item17, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.TOP, 5 )

    item18 = NumCtrl(parent, ID_TOTRICAVO, name='totricavo', integerWidth=8, fractionWidth=2); item18.Disable()
    item12.Add( item18, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item19 = NumCtrl(parent, ID_TOTCOSTO, name='totcosto', integerWidth=8, fractionWidth=2); item19.Disable()
    item12.Add( item19, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item20 = NumCtrl(parent, ID_TOTUTILE, name='totutile', integerWidth=8, fractionWidth=2); item20.Disable()
    item12.Add( item20, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item21 = NumCtrl(parent, ID_PRCMAR, name='prcmar', integerWidth=4, fractionWidth=2); item21.Disable()
    item12.Add( item21, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item22 = NumCtrl(parent, ID_PRCRIC, name='prcric', integerWidth=4, fractionWidth=2); item22.Disable()
    item12.Add( item22, 0, wx.ALIGN_CENTER|wx.LEFT|wx.BOTTOM, 5 )

    item11.Add( item12, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item23 = wx.Button( parent, ID_BUTPRT, "Lista", wx.DefaultPosition, wx.DefaultSize, 0 )
    item23.SetName( "butprt" )
    item11.Add( item23, 0, wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5 )

    item11.AddGrowableCol( 1 )

    item0.Add( item11, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5 )

    item0.AddGrowableCol( 0 )

    item0.AddGrowableRow( 2 )

    if set_sizer == True:
        parent.SetSizer( item0 )
        if call_fit == True:
            item0.SetSizeHints( parent )
    
    return item0

# Menubar functions

# Toolbar functions

# Bitmap functions


# End of generated file
