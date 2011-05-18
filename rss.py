#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         rss.py
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


import os
import urllib2
from xml.dom import minidom

import stormdb as adb

import wx

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc.controls.windows as aw


class RSSFeed:

    def __init__(self, url):
        self.url = url

    def get_feed(self):
        
        linkdata = []
        
        try:
            
            file_request = urllib2.Request(self.url)
            file_opener = urllib2.build_opener()
            file_feed = file_opener.open(file_request).read()
            file_xml = minidom.parseString(file_feed)
    
            item_node = file_xml.getElementsByTagName("item")
    
            for item in item_node:
                title = item.childNodes[0].firstChild.data
                link = item.childNodes[1].firstChild.data
    
                linkdata.append((title, link))
            
        except:
            pass
        
        return linkdata


# ------------------------------------------------------------------------------


class RSSFeedTable(adb.DbMem):
    
    def __init__(self, feed):
        adb.DbMem.__init__(self, 'title,url')
        if isinstance(feed, (str, unicode,)):
            feed = RSSFeed(feed)
        self.feed = feed
    
    def Retrieve(self):
        self.Reset()
        self.ChangeDataFrom(self.feed.get_feed())
        return True
    
    def ChangeDataFrom(self, feed_links):
        for title, url in feed_links:
            self.CreateNewRow()
            self.title = title
            self.url = url


# ------------------------------------------------------------------------------


class RSSFeedGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, feed):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbfeed = dbfeed = RSSFeedTable(feed)
        
        def cn(col):
            return self.dbfeed._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        
        cols = ((128, (cn('title'), "Titolo", _STR, True )),)
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = dbfeed.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDoubleClick)
    
    def UpdateFeed(self):
        self.dbfeed.Retrieve()
        self.ResetView()
    
    def OnDoubleClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbfeed.RowsCount():
            self.dbfeed.MoveRow(row)
            os.startfile(self.dbfeed.url)
        event.Skip()


# ------------------------------------------------------------------------------


_evtFEEDCHANGED = wx.NewEventType()
EVT_FEEDCHANGED = wx.PyEventBinder(_evtFEEDCHANGED, 0)
class RssFeedChangedEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, _evtFEEDCHANGED)


# ------------------------------------------------------------------------------


import thread

class RSSFeedUpdateThread:
    
    def __init__(self, feedpage):
        self.feedpage = feedpage

    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def Run(self):
        links = self.feedpage.feed.get_feed()
        evt = RssFeedChangedEvent()
        evt.links = links
        wx.PostEvent(self.feedpage, evt)
        self.running = False


# ------------------------------------------------------------------------------


class RSSFeedPanel(aw.Panel):
    
    feed_title = None
    feed_url = None
    
    def __init__(self, *args, **kwargs):
        
        self.feed_title = kwargs.pop('feed_title')
        self.feed_url = kwargs.pop('feed_url')
        self.thread = None
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.feed = RSSFeed(self.feed_url)
        self.gridfeed = RSSFeedGrid(self, self.feed)
        
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self.gridfeed, 0, wx.GROW|wx.ALL, 0)
        self.SetSizer(sz)
        sz.SetSizeHints(self)
    
    def UpdateFeed(self):
        self.gridfeed.UpdateFeed()
    
    def StartThread(self):
        self.thread = RSSFeedUpdateThread(self)
        self.thread.Start()
        self.Bind(EVT_FEEDCHANGED, self.OnUpdateFeed)
    
    def OnUpdateFeed(self, event):
        self.gridfeed.dbfeed.ChangeDataFrom(event.links)
        self.gridfeed.ResetView()


# ------------------------------------------------------------------------------

        
def AddNotebookFeedPage(notebook, feed_title, feed_url, update_now=False):
    page = RSSFeedPanel(notebook, feed_title=feed_title, feed_url=feed_url)
    notebook.AddPage(page, feed_title)
    if update_now:
        page.UpdateFeed()
    else:
        page.StartThread()


# ------------------------------------------------------------------------------


class RSSNotebook(wx.Notebook):
    
    def AddFeedPage(self, feed_title, feed_url, update_now=False):
        return AddNotebookFeedPage(self, feed_title, feed_url, update_now)
    
    def UpdateFeed(self, page_number):
        self.GetPage(page_number).UpdateFeed()
    
    def UpdateAllFeeds(self):
        for page_number in range(self.GetPageCount()):
            self.UpdateFeed(page_number)


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    
    def main():
        
        url_test = "http://www.ilsole24ore.com/rss/norme-e-tributi/fisco.xml"
        
#        feed = RSSFeed(url_test)
#        for title, url in feed.get_feed():
#            print '%s (%s)' % (title, url)
#        
#        print "*"*40
#        
#        t = RSSFeedTable(url_test)
#        t.Retrieve()
#        for t in t:
#            print '%s (%s)' % (t.title, t.url)
    
        app = wx.PySimpleApp()
        f = aw.Frame(None, -1, 'RSS Feed test')
        n = RSSNotebook(f)
        n.AddFeedPage('Test', url_test)
        f.Show()
#        def TestUpdate():
#            wx.Sleep(3)
#            n.UpdateAllFeeds()
#        wx.CallAfter(TestUpdate)
        app.MainLoop()
    
    main()
