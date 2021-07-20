#!/bin/env python
# -*- coding: utf-8 -*-
"""
coccoawc/controls/treecolumn
"""
import os, tempfile
import sys
import subprocess
import wx
import  wx.gizmos   as  gizmos
import awc.controls.windows as aw
import Env
import stormdb as adb
import csv
import codecs

CSVFORMAT_ASGRID = 0
CSVFORMAT_DELIMITER = ';'
CSVFORMAT_QUOTECHAR = '"'
CSVFORMAT_QUOTING = csv.QUOTE_MINIMAL
CSVFORMAT_EXCELZERO = False



class TreeListCtrl(gizmos.TreeListCtrl):
    idItem = None

    def __init__(self, *args, **kwargs):
        gizmos.TreeListCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick)
        self.idItem=0


    def OnColRightClick(self, evt):
        x, y = list(evt.GetPosition())
        self._Grid_TreeListCtrl(x,y)
        evt.Skip()


    def _Grid_TreeListCtrl(self, x, y):
        voci = []
        menu = wx.Menu()
        voci.append(("Esporta file CSV", self.OnExportCSV, True))
        voci.append(("Esporta file HTML", self.OnExportHTML, True))
        for text, func, enab in voci:
            if text is None:
                menu.AppendSeparator()
                continue
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        self.PopupMenu(menu, (x, y-20))
        menu.Destroy()

    def OnExportCSV(self, event):
        self.ExportCSV()
        event.Skip()

    def ExportCSV(self):
        lista=self.tree2list()
        maxLevel=0
        for level, item, nChild in lista:
            maxLevel=max(maxLevel, level)
        dLivelli={}
        titoli=[]
        for i in range(maxLevel+1):
            dLivelli[i]=''
            titoli.append('Livello %s' % i)
        titoli.append('Valore')

        tmpfile = tempfile.NamedTemporaryFile(suffix='.csv')
        tmpname = tmpfile.name
        tmpfile.close()
        tmpfile = open(tmpname, 'wb')
        tmpfile.write(codecs.BOM_UTF8)
        wx.GetApp().AppendTempFile(tmpname)
        writer = csv.writer(tmpfile,
                            delimiter=CSVFORMAT_DELIMITER,
                            quotechar=CSVFORMAT_QUOTECHAR,
                            doublequote=True,
                            skipinitialspace=False,
                            lineterminator='\r\n',
                            quoting=int(CSVFORMAT_QUOTING))
        csvrs = []
        csvrs.append(titoli)

        for level, item, nChild in lista:
            row=[]
            for j in range(level, maxLevel+1):
                dLivelli[j]=''
            dLivelli[level]=self.GetItemText(item).strip()

            for j in range(maxLevel+1):
                row.append(dLivelli[j])
            for j in range(1,self.GetColumnCount()):
                try:
                    w=self.GetItemText(item,j).strip()
                    row.append(w)
                except:
                    break
            if nChild==0:
                csvrs.append(row)
        writer.writerows(csvrs)
        tmpfile.close()
        os.startfile(tmpname)

    def OnExportHTML(self, event):
        lFound=False
        p=self.GetParent()
        while not lFound:
            try:
                p.ExportHtmlTree()
                lFound=True
            except:
                p=p.GetParent()
                if p==None:
                    lFound=True
        event.Skip()

    def GetMaxLevel(self):
        l=self.tree2list()
        MaxLevel=0
        for r in l:
            MaxLevel=max(MaxLevel, r[0])
        return MaxLevel

    def GetLastPathUsed(self):
        s = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGSETUP, 'setup')
        for k, o, f in [
                        ['last_path_used',  'lastPath','descriz'],
                    ]:
            if s.Retrieve("setup.chiave='export_%s'" % k) and s.OneRow():
                setattr(self, o, getattr(s, f))
            else:
                setattr(self, o, '')

    def SaveLastPathUsed(self, outputFile):
        s = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGSETUP, 'setup')
        if s.Retrieve("setup.chiave='export_last_path_used'") and not s.OneRow():
            s.CreateNewRow()
        s.chiave='export_last_path_used'
        path, file = os.path.split(outputFile)
        s.descriz=path
        s.Save()

    def SetOutputFileName(self, fileName=None):
        if not fileName:
            fileName="\export.html"
        return fileName

    def SetExportFile(self, outputFileName):
        self.GetLastPathUsed()
        outputFile=''
        exportPath=self.lastPath
        filename=self.SetOutputFileName(outputFileName)
        wildcard='*.html'
        dlg = wx.FileDialog(
            self, message="Esporta con nome", defaultDir=exportPath,
            defaultFile=filename, wildcard=wildcard, style=wx.SAVE
            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            outputFile=dlg.GetPath()
            if os.path.exists(outputFile):
                id=aw.awu.MsgDialog(self, u"Esiste già il file %s.\nSi desidera sovrascriverlo?" % outputFile, style=wx.ICON_QUESTION|wx.YES_NO)
                if id==wx.ID_NO:
                    outputFile=''
        return outputFile

    def ExportHtml(self, modelName=None, titolo='', titoliColonna=None, outputFileName=None):
        if os.path.exists(modelName) or True:
            outputFile=self.SetExportFile(outputFileName)
            if len(outputFile)>0:
                html=[]
                try:
                    input = open(modelName, "r")
                    lines = input.readlines()
                except:
                    input = self.GetModel()
                    lines = input.readlines()


                output= open(outputFile, 'w')

                #for line in input :
                for nRow in range(len(lines)):
                    line=lines[nRow]
                    line=line.replace('\n', '')
                    line=line.replace('<<title>>', titolo)
                    line=line.replace('<<azienda>>', Env.Azienda.descrizione)
                    line=line.replace('<<dataexport>>', Env.DateTime.today().strftime('%d-%m-%Y'))
                    line=line.replace('<<titolo>>', titolo)
                    if line.find('<<TitoliColonne>>')>=0:
                        wrk=''
                        for nc in range(0, self.GetColumnCount()):
                            wrk='%s<th>%s</th>' % (wrk, self.GetColumnText(nc))
                        #=======================================================
                        # for t in titoliColonna:
                        #     wrk='%s<th>%s</th>' % (wrk, t)
                        #=======================================================
                        line=line.replace('<<TitoliColonne>>', wrk)

                    if line.find('<<expand_level>>')>=0:
                        maxLevel=self.GetMaxLevel()
                        wrk=''
                        for i in range(maxLevel+1):
                            if i==maxLevel:
                                wrk='%s<span id="%s" class="tbltree-level-item">[%s]</span>&nbsp;\\' % (wrk, i, i+1)
                            else:
                                wrk='%s<span id="%s" class="tbltree-level-item">[%s]</span>&nbsp;\\\n' % (wrk, i, i+1)
                        line=line.replace('<<expand_level>>', wrk)

                    if line.find('<<Struttura>>')>=0:
                        stru=self.scanBranch(stru=[])
                        for r in stru:
                            html.append(r)
                        line=''
                    html.append(line)

                for r in html:
                    try:
                        r=r.replace(u'\u20ac', '&euro;')
                        r=r.encode('ascii', 'ignore')
                        output.write('%s\n' % r)
                    except:
                        pass
                output.close()
                input.close()

                self.SaveLastPathUsed(outputFile)
                id=aw.awu.MsgDialog(self, u"File di esportazione %s è stato generato.\nSi desidera visualizzarlo?" % outputFile, style=wx.ICON_QUESTION|wx.YES_NO)
                if id==wx.ID_YES:
                    cmd='START %s' %  outputFile
                    if hasattr(sys, 'frozen'):
                        os.system(cmd)
                    else:
                        # subprocess.Popen([pdfcmd, filename])
                        FNULL = open(os.devnull, 'w')
                        process =subprocess.Popen(cmd, stdout=FNULL, stderr=FNULL, shell=True)
                        process.wait()
        else:
            id=aw.awu.MsgDialog(self, u"Esportazione impossibile!\n Modello per esportazione assente (%s)" % modelName, style=wx.ICON_ERROR)

    def getLeefList(self):
        l=self.tree2list()
        leef=[]
        for e in l:
            if e[2]==0:
                leef.append(e)
        return leef

    def tree2list(self, item=None, nLevel=0, lista=None):
        l=nLevel
        if not lista:
            lista=[]
        if item is None:
            item=self.GetRootItem()
        key=item
        lChildren=self._GetChildren(item)
        lista.append([nLevel, key, len(lChildren)])
        if len(lChildren)>0:
            for son in lChildren:
                self.tree2list(son, nLevel=l+1, lista=lista)
        return lista

    def _GetChildren(self, item):
        lChildren=[]
        try:
            if self.ItemHasChildren(item):
                wrkItem, cookie = self.GetFirstChild(item)
                lChildren.append(wrkItem)
                while wrkItem.IsOk():
                    try:
                        wrkItem, cookie = self.GetNextChild(item, cookie)
                        if wrkItem.IsOk():
                            lChildren.append(wrkItem)
                    except:
                        break
        except:
            pass
        return lChildren


    def scanBranch(self, item=None, nLevel=0, idParent=0, stru=[]):
        self.idItem=self.idItem+1
        idItem=self.idItem
        if item is None:
            item=self.GetRootItem()
        l=nLevel
        #--------------------------
        if idParent==0:
            m1= '<tr row-id="%s">' % idItem
            m2=''
            for nc in range(0, self.GetColumnCount()):
                align='left'
                if self.GetColumnAlignment(nc)==wx.ALIGN_LEFT:
                    align='left'
                elif self.GetColumnAlignment(nc)==wx.ALIGN_RIGHT:
                    align='right'
                elif self.GetColumnAlignment(nc)==wx.ALIGN_CENTER:
                    align='center'
                try:
                    msg=self.GetItemText(item, nc)
                    if u'®' in msg:
                        msg=msg.replace(u'®', '&#174;')
                    m2='%s  <td class="data" align="%s">%s</td>' % (m2, align, msg)
                except:
                    m2='%s  <td class="data" align="%s">%s</td>' % (m2, align, '')

            m3='</tr>'
            stru.append('%s%s%s' % (m1, m2, m3))
        else:
            m1= '<tr row-id="%s"     parent-id="%s">'  % (idItem, idParent)
            m2= ''
            for nc in range(0, self.GetColumnCount()):
                align='left'
                if self.GetColumnAlignment(nc)==wx.ALIGN_LEFT:
                    align='left'
                elif self.GetColumnAlignment(nc)==wx.ALIGN_RIGHT:
                    align='right'
                elif self.GetColumnAlignment(nc)==wx.ALIGN_CENTER:
                    align='center'
                try:
                    msg=self.GetItemText(item, nc).replace(u'®', '&#174;')
                    #===========================================================
                    # if u'®' in msg:
                    #     msg=msg.replace(u'®', '&#174;')
                    #===========================================================
                    m2='%s  <td class="data" align="%s">%s</td>' % (m2, align, msg)
                except:
                    m2='%s  <td class="data">%s</td>' % (m2, '')
            m3='</tr>'
            stru.append('%s%s%s' % (m1, m2, m3))
        lChildren=self._GetChildren(item)
        if len(lChildren)>0:
            for son in lChildren:
                stru=self.scanBranch(son, nLevel=l+1, idParent=idItem, stru=stru)
        return stru

    def GetModel(self):
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        model="""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="chrome=1">
    <title><<title>></title>
    <style type="text/css">
        .tbltree-indent {width:16px; height: 16px; display: inline-block; position: relative;}

        .tbltree-expander {width:16px; height: 16px; display: inline-block; position: relative; cursor: pointer;}

        .tbltree-expander-expanded{background-image:  url("data:image/png;base64,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"); }
        .tbltree-expander-collapsed{background-image: url("data:image/png;base64,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"); }


        .tbltree-level-pickers {float: left;}
        .tbltree-level-pickers .tbltree-level-item {cursor: pointer;}
        .tbltree-count-wrap {
            font-style: italic;
            font-size: 10px;
            float: right;
        }
    </style>

    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.1/jquery-ui.min.js"></script>
    <!--     <script type="text/javascript" src="../js/jquery.cookie.js"></script> -->
    <script type="text/javascript" language="javascript">
        /*!
         * jQuery Cookie Plugin v1.3.1
         * https://github.com/carhartl/jquery-cookie
         *
         * Copyright 2013 Klaus Hartl
         * Released under the MIT license
         */
        (function (factory) {
            if (typeof define === 'function' && define.amd) {
                // AMD. Register as anonymous module.
                define(['jquery'], factory);
            } else {
                // Browser globals.
                factory(jQuery);
            }
        }(function ($) {

            var pluses = /\+/g;

            function decode(s) {
                if (config.raw) {
                    return s;
                }
                return decodeURIComponent(s.replace(pluses, ' '));
            }

            function decodeAndParse(s) {
                if (s.indexOf('"') === 0) {
                    // This is a quoted cookie as according to RFC2068, unescape...
                    s = s.slice(1, -1).replace(/\\\\"/g, '"').replace(/\\\\\\\\/g, '\\\\');
                }

                s = decode(s);

                try {
                    return config.json ? JSON.parse(s) : s;
                } catch(e) {}
            }

            var config = $.cookie = function (key, value, options) {

                // Write
                if (value !== undefined) {
                    options = $.extend({}, config.defaults, options);

                    if (typeof options.expires === 'number') {
                        var days = options.expires, t = options.expires = new Date();
                        t.setDate(t.getDate() + days);
                    }

                    value = config.json ? JSON.stringify(value) : String(value);

                    return (document.cookie = [
                        config.raw ? key : encodeURIComponent(key),
                        '=',
                        config.raw ? value : encodeURIComponent(value),
                        options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
                        options.path    ? '; path=' + options.path : '',
                        options.domain  ? '; domain=' + options.domain : '',
                        options.secure  ? '; secure' : ''
                    ].join(''));
                }

                // Read
                var cookies = document.cookie.split('; ');
                var result = key ? undefined : {};
                for (var i = 0, l = cookies.length; i < l; i++) {
                    var parts = cookies[i].split('=');
                    var name = decode(parts.shift());
                    var cookie = parts.join('=');

                    if (key && key === name) {
                        result = decodeAndParse(cookie);
                        break;
                    }

                    if (!key) {
                        result[name] = decodeAndParse(cookie);
                    }
                }

                return result;
            };

            config.defaults = {};

            $.removeCookie = function (key, options) {
                if ($.cookie(key) !== undefined) {
                    // Must not alter options, thus extending a fresh object...
                    $.cookie(key, '', $.extend({}, options, { expires: -1 }));
                    return true;
                }
                return false;
            };

        }));

    </script>
    <!--     <script type="text/javascript" src="../js/jquery.tbltree.js"></script> -->

    <script type="text/javascript" language="javascript">
        /*
         * jQuery tbletree Plugin 1.0.0
          *
         * Copyright 2014, Gagik Sukiasyan
         * Licensed under the MIT licenses.
         */
        (function($) {
             $.widget( "ui.tbltree", {
              // default options
              options: {

                rowAttr: 'row-id',
                parentAttr: 'parent-id',
                treeColumn: 0,

                saveState: false,
                saveStateName: 'tbltree-state',
                saveStateMethod: 'cookie',
                initState: 'collapsed',
                levelPicker: '',

                expanderTemplate: '<span class="tbltree-expander"></span>',
                levelPickerTemplate: '<div class="tbltree-level-pickers">\
                                        <<expand_level>>
                                      </div>',
                indentTemplate: '<span class="tbltree-indent"></span>',
                expanderExpandedClass: 'tbltree-expander-expanded',
                expanderCollapsedClass: 'tbltree-expander-collapsed',


                count: {
                    enabled: false,
                    format: '<div class="tbltree-count-wrap">(<span class="tbltree-count"></span>)</div>',
                    method: function(row) {
                        // count every row
                        return 1;
                    },
                    click: null
                },

                // callbacks
                change: null,
                expand: null,
                collapse: null,
                showlevel: null
              },

                 // the constructor
                _create: function() {
                    var $this = this;
                    this.element
                      .addClass( "jquery-tbltree" )

                    if (this.options.levelPicker !== "" && $(this.options.levelPicker).length > 0) {
                        this.pickers = $(this.options.levelPickerTemplate);
                        this.pickers.find('.tbltree-level-item').click(function(){
                            $this.showLevel($(this).attr('id'))
                        })
                        $(this.options.levelPicker).append(this.pickers);
                    }
                },
                _init: function() {
                    var $this = this;
                    this.getRootNodes().each(function(){
                        $this._initTree($(this));
                    })
                },

                getID: function(row) {
                    return row.attr(this.options.rowAttr);
                },
                getParentID: function(row) {
                    return row.attr(this.options.parentAttr);
                },
                isExpanded: function(cell) {
                    return cell.hasClass('tbltree-expanded');
                },
                isCollapsed: function(cell) {
                    return cell.hasClass('tbltree-collapsed');
                },
                getRootNodes: function () {
                    var nodes = this.element.find('tr['+this.options.rowAttr+']').not('tr['+this.options.parentAttr+']')
                    return nodes
                },
                getRow: function(id) {
                    return this.element.find('tr['+this.options.rowAttr+'="'+id+'"]');
                },

                saveState: function(row) {
                    var $this = this;
                    if ($this.options.saveState && $this.options.saveStateMethod === 'cookie') {

                        var stateArrayString = $.cookie(this.options.saveStateName) || '';
                        var stateArray = (stateArrayString === '' ? [] : stateArrayString.split(','));
                        var nodeId = $this.getID(row);

                        if ($this.isExpanded(row)) {
                            if ($.inArray(nodeId, stateArray) === -1) {
                                stateArray.push(nodeId);
                            }
                        } else if ($this.isCollapsed(row)) {
                            if ($.inArray(nodeId, stateArray) !== -1) {
                                stateArray.splice($.inArray(nodeId, stateArray), 1);
                            }
                        }
                        $.cookie(this.options.saveStateName, stateArray.join(','));
                    }
                    return $this;
                },
                getState: function(row) {
                    var $this = this;

                    if ($this.options.saveState && $this.options.saveStateMethod === 'cookie') {
                        var stateArrayString = $.cookie(this.options.saveStateName) || '';
                        var stateArray = (stateArrayString === '' ? [] : stateArrayString.split(','));
                        if ($.inArray($this.getID(row), stateArray) !== -1) {
                            return "expanded";
                        } else {
                            return "collapsed";
                        }

                    }
                    return $this.options.initState;
                },

                toggle: function (row) {
                    if (typeof(row) != "object") {
                        row = this.getRow(row);
                    }
                    if (this.isCollapsed(row)) {
                        this.expand(row, 1);

                    } else {
                        this.collapse(row, 1);
                    }
                },

                collapse: function(id, user) {
                        var $this = this;

                        if (typeof(id) === "object") {
                            row_id = this.getID(id);
                            row = id;
                        } else {
                            row_id = id;
                            row = this.getRow(row_id);
                        }


                        var row_id = this.getID(row);
                        if (user) {
                            this.render(row, 'collapsed');
                            this.saveState(row);
                            this._trigger("collapse", null, row);
                            this._trigger("change", null, {type: 'collapsed', 'row': row});
                        }

                        this._getChildren(row_id).each(function(){
                            $(this).hide();
                            $this.collapse($(this), 0);
                        })
                },
                expand: function(id, user) {
                        var $this = this;

                        if (typeof(id) === "object") {
                            row_id = this.getID(id);
                            row = id;
                        } else {
                            row_id = id;
                            row = this.getRow(row_id);
                        }

                        var row_id = this.getID(row);
                        if (user) {
                            this.render(row, 'expanded')
                            this.saveState(row);
                            this._trigger("expand", null, row);
                            this._trigger("change", null, {type: 'expanded', 'row': row});
                        }

                        this._getChildren(row_id).each(function(){
                            if ( ! $this.isCollapsed($(this))) {
                                $this.expand($(this), 0);
                            }
                            $(this).show();
                        })
                },

                expandLevel: function(level) {
                    var $this = this;
                    $this.element.find('tr[level]').filter(function() {
                        return  $(this).attr("level") <= level;
                    })
                    .each(function(){
                        $this.expand($(this), 1);
                    })
                },

                collapseLevel: function(level) {
                    var $this = this;
                    $this.element.find('tr[level='+level+']').each(function(){
                            $this.collapse($(this), 1);
                    })

                },

                showLevel: function(level) {
                    var $this = this;
                    if (level > 0) {
                        $this.expandLevel(level - 1);
                    }
                    $this.collapseLevel(level);
                    this._trigger("showlevel", null, level);
                },

                render: function(row, state) {
                    var $this = this;
                    if (state == 'collapsed') {
                        row.attr('tree-state', 'hidden')
                        row.removeClass('tbltree-expanded');
                        row.addClass('tbltree-collapsed');
                    } else {
                        row.attr('tree-state', 'shown')
                        row.removeClass('tbltree-collapsed');
                        row.addClass('tbltree-expanded');
                    }
                    this._renderExpander(row);
                },

                _getChildren: function (id) {
                    if (typeof(id) === "object") {
                        id = this.getID(id);
                    }
                    return this.element.find('tr['+this.options.parentAttr+'="'+id+'"]');
                },

                getTreeCell: function (row) {
                    return $(row.find('td').get(this.options.treeColumn));
                },

                isLeaf: function(row) {
                    if (row.attr('is-leaf') == "true") {
                        return true;
                    }
                    return false;
                },

                _initExpander: function(root) {
                    var $this = this;

                   var cell = this.getTreeCell(root);

                    var tpl = $(this.options.expanderTemplate);
                    var expander = root.find('.tbltree-expander');
                    if (expander) {
                        expander.remove();
                    }
                    tpl.prependTo(cell)

                    tpl.click(function() {
                        $this.toggle(root)
                    });

                },
                _renderExpander: function(cell) {
                    if (cell.attr('is-leaf') == "true") {
                        return;
                    }
                    var expander = cell.find('.tbltree-expander');
                    if (expander.length) {
                        if (!this.isCollapsed(cell)) {
                            expander.removeClass(this.options.expanderCollapsedClass);
                            expander.addClass(this.options.expanderExpandedClass);
                        } else {
                            expander.removeClass(this.options.expanderExpandedClass);
                            expander.addClass(this.options.expanderCollapsedClass);
                        }
                    } else {
                        this._initExpander(cell);
                        this._renderExpander(cell);
                    }
                },

                _initIndent: function(cell, level) {
                    cell.find('.tbltree-indent').remove();
                    var $indent = $(this.options.indentTemplate);
                    $indent.css('width', (level * 16));
                    $indent.insertBefore(cell.find('.tbltree-expander'));
                },

                _initTree: function(row, parent, level) {
                    var $this = this;
                    level = (level == undefined) ? 0: level;

                    var children = this._getChildren(row);

                    $this._initExpander(row);
                    $this._initIndent(row, level)
                    row.attr('level', level);
                    row.attr('is-leaf', (children.length == 0));

                    $this.render(row, this.getState(row));

                    if (parent !== undefined && parent.attr('tree-state') == 'hidden') {
                        row.hide();
                        row.attr('tree-state', 'hidden');
                    } else {
                        row.show();
                    }
                    if (children.length != 0) {
                        var count = $this._getCount(row);
                        $.each(children, function(i, tree){
                            $this._initTree($(tree), row, level+1);
                            count += $this._getCount($(tree));
                        })

                        $this._setCount(row, count);
                    }
                },

                _getCount: function(row) {
                    if (!this.options.count.enabled) {
                        return 0;
                    }

                    var count = row.attr('count');
                    if (count != undefined) {
                        return parseInt(count);
                    }
                    count = 0;
                    if (typeof(this.options.count.method) === "function") {
                        count += parseInt(this.options.count.method(row));
                    }
                    return count;
                },

                _setCount: function(row, count) {
                    if (!this.options.count.enabled) {
                        return 0;
                    }

                    var $this = this;
                    if (typeof(this.options.count.format) === "function") {
                        this.options.count.format(row, count);
                    } else {
                        var elem = $(this.options.count.format);
                        elem.find('.tbltree-count').text(count)
                        elem.appendTo(this.getTreeCell(row))

                        if (typeof(this.options.count.click) === "function") {
                            elem.css('cursor', 'pointer').click(function(e) {
                                $this.options.count.click(e, row, count)
                            } )
                        }
                    }
                    row.attr('count', count);
                },

              // events bound via _on are removed automatically
              // revert other modifications here
              _destroy: function() {
                this.element
                  .removeClass( "jquery-tbltree" )
                  .enableSelection()

                this.pickers.remove();
              },

              // _setOptions is called with a hash of all options that are changing
              // always refresh when changing options
              _setOptions: function() {
                // _super and _superApply handle keeping the right this-context
                this._superApply( arguments );
              },

              // _setOption is called for each individual option that is changing
              _setOption: function( key, value ) {
                // prevent invalid color values
                this._super( key, value );
              }
            });

        })(jQuery);
    </script>


    <!--     <link rel="stylesheet" href="./stylesheets/styles.css"> -->

    <style type="text/css">
        @import url(https://fonts.googleapis.com/css?family=Arvo:400,700,400italic);

        /* MeyerWeb Reset */

        html, body, div, span, applet, object, iframe,
        h1, h2, h3, h4, h5, h6, p, blockquote, pre,
        a, abbr, acronym, address, big, cite, code,
        del, dfn, em, img, ins, kbd, q, s, samp,
        small, strike, strong, sub, sup, tt, var,
        b, u, i, center,
        dl, dt, dd, ol, ul, li,
        fieldset, form, label, legend,
        table, caption, tbody, tfoot, thead, tr, th, td,
        article, aside, canvas, details, embed,
        figure, figcaption, footer, header, hgroup,
        menu, nav, output, ruby, section, summary,
        time, mark, audio, video {
          margin: 0;
          padding: 0;
          border: 0;
          font: inherit;
          vertical-align: baseline;
        }


        /* Base text styles */

        body {
          padding:10px 50px 0 0;
          font-family:"Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 14px;
            color: #232323;
            background-color: #FBFAF7;
            margin: 0;
            line-height: 1.8em;
            -webkit-font-smoothing: antialiased;

        }

        h1, h2, h3, h4, h5, h6 {
          color:#232323;
          margin:36px 0 10px;
        }

        ul, ol, table, dl {
          margin:0 0 22px;
        }

        h1, h2, h3 {
            font-family: Arvo, Monaco, serif;
          line-height:1.3;
            font-weight: normal;
        }

        h1,h2, h3 {
            display: block;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }

        h1 {
            font-size: 30px;
        }

        h2 {
            font-size: 24px;
        }

        h3 {
            font-size: 18px;
        }

        h4, h5, h6 {
            font-family: Arvo, Monaco, serif;
            font-weight: 700;
        }

        a {
          color:#C30000;
          font-weight:200;
          text-decoration:none;
        }

        a:hover {
            text-decoration: underline;
        }

        a small {
            font-size: 12px;
        }

        em {
            font-style: italic;
        }

        strong {
          font-weight:700;
        }

        ul {
          list-style: inside;
          padding-left: 25px;
        }

        ol {
          list-style: decimal inside;
          padding-left: 20px;
        }

        blockquote {
          margin: 0;
          padding: 0 0 0 20px;
          font-style: italic;
        }

        dl, dt, dd, dl p {
            font-color: #444;
        }

        dl dt {
          font-weight: bold;
        }

        dl dd {
          padding-left: 20px;
          font-style: italic;
        }

        dl p {
          padding-left: 20px;
          font-style: italic;
        }

        hr {
          border:0;
          background:#ccc;
          height:1px;
          margin:0 0 24px;
        }

        /* Images */

        img {
          position: relative;
          margin: 0 auto;
          max-width: 650px;
          padding: 5px;
          margin: 10px 0 32px 0;
          border: 1px solid #ccc;
        }

        p img {
          display: inline;
          margin: 0;
          padding: 0;
          vertical-align: middle;
          text-align: center;
          border: none;
        }

        /* Code blocks */

        code, pre {
            font-family: Monaco, "Bitstream Vera Sans Mono", "Lucida Console", Terminal, monospace;
          color:#000;
          font-size:14px;
        }

        pre {
            padding: 4px 12px;
          background: #FDFEFB;
          border-radius:4px;
          border:1px solid #D7D8C8;
          overflow: auto;
          overflow-y: hidden;
            margin-bottom: 32px;
        }


        /* Tables */

        table {
          width:100%;
        }

        table {
          border: 1px solid #ccc;
          margin-bottom: 32px;
          text-align: left;
         }

        th {
          font-family: 'Arvo', Helvetica, Arial, sans-serif;
            font-size: 18px;
            font-weight: normal;
          padding: 10px;
          background: #232323;
          color: #FDFEFB;
         }

        td {
          padding: 10px;
            background: #ccc;
         }


        /* Wrapper */
        .wrapper {
          width:960px;
        }


        /* Header */

        header {
            background-color: #171717;
            color: #FDFDFB;
          width:170px;
          float:left;
          position:fixed;
            border: 1px solid #000;
            -webkit-border-top-right-radius: 4px;
            -webkit-border-bottom-right-radius: 4px;
            -moz-border-radius-topright: 4px;
            -moz-border-radius-bottomright: 4px;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            padding: 34px 25px 22px 50px;
            margin: 30px 25px 0 0;
            -webkit-font-smoothing: antialiased;
        }

        p.header {
            font-size: 16px;
        }

        h1.header {
            font-family: Arvo, sans-serif;
            font-size: 30px;
            font-weight: 300;
            line-height: 1.3em;
            border-bottom: none;
            margin-top: 0;
        }


        h1.header, a.header, a.name, header a{
            color: #fff;
        }

        a.header {
            text-decoration: underline;
        }

        a.name {
            white-space: nowrap;
        }

        header ul {
          list-style:none;
          padding:0;
        }

        header li {
            list-style-type: none;
          width:132px;
          height:15px;
            margin-bottom: 12px;
            line-height: 1em;
            padding: 6px 6px 6px 7px;

            background: #AF0011;
            background: -moz-linear-gradient(top, #AF0011 0%, #820011 100%);
          background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,#f8f8f8), color-stop(100%,#dddddd));
          background: -webkit-linear-gradient(top, #AF0011 0%,#820011 100%);
          background: -o-linear-gradient(top, #AF0011 0%,#820011 100%);
          background: -ms-linear-gradient(top, #AF0011 0%,#820011 100%);
          background: linear-gradient(top, #AF0011 0%,#820011 100%);

            border-radius:4px;
          border:1px solid #0D0D0D;

            -webkit-box-shadow: inset 0px 1px 1px 0 rgba(233,2,38, 1);
            box-shadow: inset 0px 1px 1px 0 rgba(233,2,38, 1);

        }

        header li:hover {
            background: #C3001D;
            background: -moz-linear-gradient(top, #C3001D 0%, #950119 100%);
          background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,#f8f8f8), color-stop(100%,#dddddd));
          background: -webkit-linear-gradient(top, #C3001D 0%,#950119 100%);
          background: -o-linear-gradient(top, #C3001D 0%,#950119 100%);
          background: -ms-linear-gradient(top, #C3001D 0%,#950119 100%);
          background: linear-gradient(top, #C3001D 0%,#950119 100%);
        }

        a.buttons {
            -webkit-font-smoothing: antialiased;
            background: url(../images/arrow-down.png) no-repeat;
            font-weight: normal;
            text-shadow: rgba(0, 0, 0, 0.4) 0 -1px 0;
            padding: 2px 2px 2px 22px;
            height: 30px;
        }

        a.github {
            background: url(../images/octocat-small.png) no-repeat 1px;
        }

        a.buttons:hover {
            color: #fff;
            text-decoration: none;
        }


        /* Section - for main page content */

        section {
          width:650px;
          float:right;
          padding-bottom:50px;
        }


        /* Footer */

        footer {
          width:170px;
          float:left;
          position:fixed;
          bottom:10px;
            padding-left: 50px;
        }

        @media print, screen and (max-width: 960px) {

          div.wrapper {
            width:auto;
            margin:0;
          }

          header, section, footer {
            float:none;
            position:static;
            width:auto;
          }

            footer {
                border-top: 1px solid #ccc;
                margin:0 84px 0 50px;
                padding:0;
            }

          header {
            padding-right:320px;
          }

          section {
            padding:20px 84px 20px 50px;
            margin:0 0 20px;
          }

          header a small {
            display:inline;
          }

          header ul {
            position:absolute;
            right:130px;
            top:84px;
          }
        }

        @media print, screen and (max-width: 720px) {
          body {
            word-wrap:break-word;
          }

          header {
            padding:10px 20px 0;
                margin-right: 0;
          }

            section {
            padding:10px 0 10px 20px;
            margin:0 0 30px;
          }

            footer {
                margin: 0 0 0 30px;
            }

          header ul, header p.view {
            position:static;
          }
        }

        @media print, screen and (max-width: 480px) {

          header ul li.download {
            display:none;
          }

            footer {
                margin: 0 0 0 20px;
            }

            footer a{
                display:block;
            }

        }

        @media print {
          body {
            padding:0.4in;
            font-size:12pt;
            color:#444;
          }
        }
    </style>


    <!--     <link rel="stylesheet" href="./stylesheets/pygment_trac.css"> SE NE PUO' FARE A MENO -->

    <!--    <script src="./javascripts/scale.fix.js"></script>  SE NE PUO' FARE A MENO -->
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <!--[if lt IE 9]>
    <script src="//html5shiv.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->


      <script>
      $(function() {


        // initialize with default options
        $( "#table1" ).tbltree({
            saveState: true,
            levelPicker: '#my-widget1'
        });

      });
      </script>

  </head>
  <body>
    <div>
        <p align=right ><font size="3"><<azienda>></font></p>
        <p align=right ><font size="3"><<dataexport>></font></p>
        <P align=center><font size="5"><<titolo>> </font></P>
    </div>
<div id="my-widget1"></div>
<table id="table1" class="controller" border="1" align="left" style="width:100%">
  <thead>
    <!--
    <tr>
        <th>Centro di Costo</th>
        <th>Valore</th>
    </tr>
    -->
    <tr>
        <<TitoliColonne>>
    </tr>

    </thead>
       <tbody>
            <<Struttura>>
        </tbody>
    </table>

      </section>

    </div>
    <!--[if !IE]><script>fixScale(document);</script><![endif]-->

  </body>
</html>
"""
        html = StringIO(model)
        return html




