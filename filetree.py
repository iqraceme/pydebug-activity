#!/usr/bin/env python
# Copyright (C) 2008, One Laptop Per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
from gettext import gettext as _

#major packages
from gi.repository import Gtk
from gi.repository import GdkPixbuf

# Initialize logging.
from pydebug_logging import _logger


class FileTree:

    column_names = [_('Name'), _('Size'), _('Last Changed')]
    
    def __init__(self,parent, widget=None, wTree=None):
        self.parent = parent
        self.treeview = widget
        self.wTree = wTree
        self.init_model()
        self.init_columns()
        self.connect_object()
        self.path = None
        
    def connect_object(self,  wTree=None): #caller should over-ride this
        """if wTree:
            self.wTree=wTree
        if self.wTree:"""
        mdict = {
            'file_system_row_selected_cb': self.file_system_row_selected_cb,
            'file_system_row_activated_cb': self.file_system_row_activated_cb,
            'file_system_toggle_cursor_row_cb': self.file_system_toggle_cursor_row_cb,
        }

        self.wTree.signal_autoconnect(mdict)

    def init_model(self):
        self.ft_model = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str, str, str)
        if not self.treeview:
            self.treeview = Gtk.TreeView()

        self.treeview.set_model(self.ft_model)
        self.treeview.show()

        #the following line was probably disabled for compatibility with earlier sugar
        #search for TOOLTIP to find problem areas
        self.treeview.set_tooltip_column(4)

        self.show_hidden = False

    def init_columns(self):
        col = Gtk.TreeViewColumn()
        col.set_title(self.column_names[0])

        render_pixbuf = Gtk.CellRendererPixbuf()
        col.pack_start(render_pixbuf, expand=False)
        col.add_attribute(render_pixbuf, 'pixbuf', 0)

        render_text = Gtk.CellRendererText()
        col.pack_start(render_text, expand=True)
        col.add_attribute(render_text, 'text', 1)
        self.treeview.append_column(col)

        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(self.column_names[1], cell)
        col.add_attribute(cell, 'text', 2)
        self.treeview.append_column(col)
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(self.column_names[2], cell)
        col.add_attribute(cell, 'text', 3)
        self.treeview.append_column(col)
        self.treeview.show()

    def get_filenames_list(self, dname=None, show_hidden=False):
        if not dname:
            self.dirname = os.path.expanduser('~')
        else:
            self.dirname = os.path.abspath(dname)

        if not os.path.isdir(self.dirname):
            return None

        files = [f for f in os.listdir(self.dirname) if f[0] <> '.' or  show_hidden]
        files.sort()
        #if not show_hidden: files = ['..'] + files
        return files

    def new_directory(self,fullpath=None,piter=None):
        dirlist = self.get_filenames_list(fullpath)
        if not dirlist: return
        for file in dirlist:
            if file.endswith('.pyc'): continue
            if file.endswith('.pyo'): continue
            if file.endswith('~'): continue
            if file.endswith('playpen'): continue
            fullname = os.path.join(self.dirname,file)
            if not os.path.isdir(fullname) and not os.path.isfile(fullname): continue
            if len(file)>16:
                short_file = file[:10] + '...' + file[-5:]
            else:
                short_file = file

            self.ft_model.append(piter, [self.file_pixbuf(fullname), short_file,
                                         self.file_size(fullname), self.file_last_changed(fullname),
                                         fullname,])

        if piter:
            tvpath = self.ft_model.get_path(piter)
            if tvpath:
                self.treeview.expand_row(tvpath,False)

    def set_file_sys_root(self, root, append = False):
        #self.file_sys_root = root
        self.dirname = root
        if not append:
            self.ft_model.clear()

        if not root: return
        self.new_directory(root)
        #self.current_citer = self.ft_model.append(None,[None,os.path.basename(self.file_sys_root),
                                                              #None,None,self.file_sys_root,])

    def file_system_row_activated_cb(self,widget,iter=None,path=None):
        selection=widget.get_selection()
        (model,iter)=selection.get_selected()
        childiter = model.iter_children(iter)
        if childiter != None: #there are children
            childpath = model.get_path(childiter)
            if self.treeview.row_expanded(childpath):
                self.treeview.collapse_row(model.get_path(iter))

            else:
                self.treeview.expand_row(model.get_path(iter),False)
            return

        fullpath = model.get(iter, 4)
        self.new_directory(fullpath[0], iter)

    def file_system_toggle_cursor_row_cb(self,widget,iter=None,path=None):
        selection = widget.get_selection()
        (model, iter) = selection.get_selected()
        childiter = model.iter_children(iter)

        if childiter != None: #there are children
            childpath = model.get_path(childiter)
            if self.treeview.row_expanded(childpath):
                self.treeview.collapse_row(model.get_path(iter))
            else:
                self.treeview.expand_row(model.get_path(iter), False)

            return

    def file_system_row_selected_cb(self, widget):
        selection = widget.get_selection()
        (model,iter) = selection.get_selected()
        fullpath = model.get(iter, 4)
        if fullpath[0].endswith('.activity'):
            #change 12/26/10 -- do nothing
            return  # Why it have code next to a 'return'?
            self.parent.child_path = fullpath[0]
            self.parent.read_activity_info()
        
    def position_to(self,fullpath):
        self.iter = None
        self.ft_model.foreach(self.fn_compare,fullpath)
        if self.iter != None:
            self.path = self.ft_model.get_path(self.iter)
            self.treeview.scroll_to_cell(self.path, use_align=True, row_align=0.2)

        else:
            _logger.debug('position to not found:%s' % fullpath)
            
    def position_recent(self,path = None):
        if not path:
            self.path = path

        if self.path:
            self.treeview.scroll_to_cell(self.path, use_align=True, row_align=0.2)

    def fn_compare(self, model, path, iter, fullpath):
        if model.get(iter, 4)[0] == fullpath:
            self.iter = iter
            return True

        return False

    def file_pixbuf(self, filename):
        if os.path.isdir(filename):
            return self.get_icon_pixbuf('STOCK_DIRECTORY')

        else:
            return self.get_icon_pixbuf('STOCK_FILE')

    def get_icon_pixbuf(self, stock):
        return self.treeview.render_icon(stock_id=getattr(Gtk, stock),
                                size=Gtk.IconSize.MENU,
                                detail=None)

    def file_size(self, filename):
        filestat = os.stat(filename)
        return filestat.st_size

    def file_last_changed(self, filename):
        filestat = os.stat(filename)
        rtn = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(filestat.st_mtime))
        return rtn

    def get_treeview(self):
        return self.treeview


def main():
    Gtk.main()

