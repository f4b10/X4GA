# -*- coding: UTF-8 -*-

#-----------------------------------------------------------------------------
# Python source generated by wxDesigner from file: pdcrange.wdr
# Do not modify this file, all changes will be lost!
#-----------------------------------------------------------------------------

# Include wxPython modules
import wx
import wx.grid
import wx.animate

# Window functions

ID_PANGRID = 16000
ID_BTNOK = 16001

def PdcRangeFunc( parent, call_fit = True, set_sizer = True ):
    item0 = wx.FlexGridSizer( 0, 1, 0, 0 )
    
    item1 = wx.Panel( parent, ID_PANGRID, wx.DefaultPosition, [400,160], 0 )
    item0.Add( item1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

    item2 = wx.BoxSizer( wx.HORIZONTAL )
    
    item3 = wx.Button( parent, ID_BTNOK, "Conferma", wx.DefaultPosition, wx.DefaultSize, 0 )
    item2.Add( item3, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

    item0.Add( item2, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

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
