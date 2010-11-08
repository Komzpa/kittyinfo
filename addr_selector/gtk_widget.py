#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    This file is part of kothic, the realtime map renderer.

#   kothic is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   kothic is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with kothic.  If not, see <http://www.gnu.org/licenses/>.
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os

import tree

try:
  import psyco
  psyco.full()
except ImportError:
  debug("Psyco import failed. Program may run slower. Ir you run it on i386 machine, please install Psyco to get best performance.")

CHILDREN = 1 ## magic constants
CENTER = 2
BBOX = 3
LINE = 4
PASSED = 5

class AddrSelector(gtk.VBox):
  __gsignals__ = dict(box_changed=(gobject.SIGNAL_RUN_FIRST,
  gobject.TYPE_NONE,
  ()))
  def __init__(self):
    #combo = gtk.Combo()
    gtk.VBox.__init__(self)

    
    self.Combos = []
    self.CombosLists = []
    self.CombosIDs = []
    self.CombosNum = 10
    self.bbox = (-1,-1,1,1)

    for i in range(0,self.CombosNum):
      self.CombosIDs.append([])
      self.CombosLists.append(gtk.ListStore(gobject.TYPE_STRING))
      self.Combos.append(gtk.ComboBox(self.CombosLists[i]))
      cell = gtk.CellRendererText()
      self.Combos[i].pack_start(cell, True)
      self.Combos[i].add_attribute(cell, 'text', 0)
      self.Combos[i].connect("changed", self.load_list, i)
      self.Combos[i].set_wrap_width(5)
      self.Combos[i].set_no_show_all(True)
      self.pack_start(self.Combos[i],False,False,0)

    for top in tree.tops:
      self.CombosLists[0].append([tree.tree["relation"][top].get("name", str(top))])
      self.CombosIDs[0].append(("relation", top))
    self.Combos[0].set_active(0)
    self.Combos[0].show()
    self.set_size_request(300, 300)

  def show_all(self):
    self.show()
  def load_list(self, widget, index):
    """
    Load list for combobox number "index"+1
    """
    for i in range(index+1,self.CombosNum):
      self.Combos[i].hide()
      self.CombosLists[i].clear()
      self.CombosIDs[i] = []
    act = self.Combos[index].get_active()
    if act > -1:
      t,r = self.CombosIDs[index][act]
      if BBOX in tree.tree[t][r]:
        self.bbox = tree.tree[t][r][BBOX]
      if t == "relation":
        lst = []
        for T, I, R in tree.tree[t][r][CHILDREN]:
          if I in tree.tree[T] and R not in ("street"):
            lst.append((tree.tree[T][I].get("index_name:ru", tree.tree[T][I].get("name",tree.tree[T][I].get("addr:housenumber",str(I)))),
            tree.tree[T][I].get("name",tree.tree[T][I].get("addr:housenumber",str(I))),
            T,
            I
            ))
        print lst
        lst.sort(None, lambda x: x[0])
        print lst
        for a,b,T,I in lst:
            self.CombosLists[index+1].append([tree.tree[T][I].get("name", tree.tree[T][I].get("addr:housenumber",str(I)))])
            self.CombosIDs[index+1].append((T,I))
        self.Combos[index+1].show()
    self.emit("box_changed")
if __name__ == "__main__":

  gtk.gdk.threads_init()
  kap = KothicApp()
  kap.main()
