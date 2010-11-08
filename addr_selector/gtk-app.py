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
from gtk_widget import AddrSelector

import tree

try:
  import psyco
  psyco.full()
except ImportError:
  debug("Psyco import failed. Program may run slower. Ir you run it on i386 machine, please install Psyco to get best performance.")



class KothicApp:
  def __init__(self):
    self.width, self.height = 800, 480
    print tree.tops
    

    self.window = gtk.Window()


    self.window.set_size_request(self.width, self.height)

    self.window.connect("destroy", gtk.main_quit)
    vbox = AddrSelector()
    vbox.connect("box_changed", self.printa)
    #vbox.__reinit__()
    self.window.add(vbox)
  def main(self):
    self.window.show_all()

    gtk.main()
    exit()
  def printa(self, widget):
    print widget.bbox

if __name__ == "__main__":

  gtk.gdk.threads_init()
  kap = KothicApp()
  kap.main()
