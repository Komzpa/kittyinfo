#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from lxml import etree
from bz2 import BZ2File
import twms.bbox

reload(sys)
sys.setdefaultencoding("utf-8")          # a hack to support UTF-8

try:
  import psyco
  psyco.full()
except ImportError:
  pass



def main ():

  print """
  Pass 1. Parsing address relations, IDs of interesting objects.
  """
  ID = 0
  osm_infile = BZ2File(sys.argv[1])
  addr = {}
  interesting = {}
  for t in ("node", "way", "relation"):
    addr[t] = {}
    interesting[t] = set()
  
  CHILDREN = 1 ## magic constants
  CENTER = 2
  BBOX = 3
  LINE = 4
  PASSED = 5
  tags = {}
  members = set()
  context = etree.iterparse(osm_infile)
  


  for action, elem in context:
    
    if elem.tag == "node":
      tags = {}
    elif elem.tag == "tag":
      items = dict(elem.items())
      tags[items["k"]] = items["v"]
    elif elem.tag == "way":
      tags = {}
    elif elem.tag == "relation":
      items = dict(elem.items())
      if "id" in items:
        ID = int(items["id"])
      if tags.get("type", None) == "address":
        if ID not in addr["relation"]:
          addr["relation"][ID] = {}
        addr["relation"][ID].update(tags)
        if CHILDREN not in addr["relation"][ID]:
          addr["relation"][ID][CHILDREN] = set() # set of (type, id, role)
        for t,i,r in members:
          if r == "is_in":
            if t == "relation":
              if i not in addr["relation"]:
                addr["relation"][i] = {}
              if CHILDREN not in addr["relation"][i]:
                addr["relation"][i][CHILDREN] = set() # set of (type, id, role)
              addr["relation"][i][CHILDREN].add(("relation", ID, tags.get("address:type", "house")))
          else:
            addr["relation"][ID][CHILDREN].add((t,i,r))
          interesting[t].add(i)
      tags = {}
      members = set()

    elif elem.tag == "member":
      items = dict(elem.items())
      members.add((items["type"],int(items["ref"]),items["role"]))
    elem.clear()
  #print interesting
  print """
  Pass 2. Getting interesting ways and nodes out of dump
  """
  ID = 0
  osm_infile = BZ2File(sys.argv[1])
  tags = {}
  members = set()
  curway = []
  context = etree.iterparse(osm_infile)

  for action, elem in context:
    items = dict(elem.items())
    if "id" in items:
      ID = int(items["id"])
    if elem.tag == "node":
      if ID in interesting["node"]:
        interesting["node"].discard(ID)
        if ID not in addr["node"]:
          addr["node"][ID] = {}
        addr["node"][ID].update(tags)
        addr["node"][ID][CENTER] = (float(items["lon"]),float(items["lat"]))
      tags = {}
    elif elem.tag == "tag":
      tags[items["k"]] = items["v"]
    elif elem.tag == "way":
       if ID in interesting["way"]:
         interesting["way"].discard(ID)
         if ID not in addr["way"]:
           addr["way"][ID] = {}
         addr["way"][ID].update(tags)
         addr["way"][ID][LINE] = curway
         for node in curway:
           interesting["node"].add(node)
       curway = []
       tags = {}
    elif elem.tag == "nd":
      curway.append(int(items["ref"]))
    elem.clear()

  print """
  Pass 3. Looking for nodes of ways.
  """
  ID = 0
  osm_infile = BZ2File(sys.argv[1])
  tags = {}
  members = set()
  context = etree.iterparse(osm_infile)

  for action, elem in context:
    items = dict(elem.items())
    if "id" in items:
      ID = int(items["id"])
    if elem.tag == "node":
      if ID in interesting["node"]:
        interesting["node"].discard(ID)
        if ID not in addr["node"]:
          addr["node"][ID] = {}
        addr["node"][ID].update(tags)
        addr["node"][ID][CENTER] = (float(items["lon"]),float(items["lat"]))
      tags = {}
    elif elem.tag == "tag":
      tags[items["k"]] = items["v"]
    elem.clear()
  print """
  Pass 4. Sorting tree"""

  print """
   - making centers and bboxes for ways"""
  to_delete = set()
  for k,way in addr["way"].iteritems():
    for node in way[LINE]:
      ll = []
      if node in addr["node"]:
        print addr["node"][node]
        ll.append(addr["node"][node][CENTER])
    if ll:
      box = [ll[0][0],ll[0][1],ll[0][0],ll[0][1]]
      box = twms.bbox.expand_to_point(box, ll)
      way[BBOX] = box
      way[CENTER] = ((box[0]+box[2])/2, (box[1]+box[3])/2)
    else:
      to_delete.add(k)
  for k in to_delete:
    interesting["way"].add(k)
    del addr["way"][k]
  print "Empty and useless ways: %s"% len(to_delete)
  print """
  - making centers and bboxes for relations"""
  def recurse_bbox(rel):
    if rel not in addr["relation"]:
      return False
    if BBOX in addr["relation"][rel]:
      return addr["relation"][rel][BBOX]
    if PASSED in addr["relation"][rel]:
      return False
    to_pass.discard(rel)
    addr["relation"][rel][PASSED] = True
    if not addr["relation"][rel][CHILDREN]:
      del addr["relation"][rel]
      return False
    box = False
    for t,i,r in addr["relation"][rel][CHILDREN]:
      if i in addr[t]:
        if t == "node":
          if not box:
            box = [addr[t][i][CENTER][0],addr[t][i][CENTER][1],addr[t][i][CENTER][0],addr[t][i][CENTER][1]]
          else:
            box = twms.bbox.expand_to_point(box, [addr[t][i][CENTER]])
        if t == "way":
          if not box:
            box = addr[t][i][BBOX]
          else:
            box = twms.bbox.add(box, addr[t][i][BBOX])
        if t == "relation":
          bbox = recurse_bbox(i)
          if bbox:
            if not box:
              box = bbox
            else:
              box = twms.bbox.add(box, bbox)
    addr["relation"][rel][BBOX] = box
    print box
    
    if not box:
      print addr["relation"][rel]
      del addr["relation"][rel]
    return box
  to_pass = set(addr["relation"].keys())

  while to_pass:
    top = to_pass.pop()
    recurse_bbox(top)
  tops = set(addr["relation"].keys())
  for rel in addr["relation"].keys():
    tops.difference_update(set([i[1] for i in addr["relation"][rel][CHILDREN] if i[0] == "relation"]))
  print "Address tree tops: %s"% repr(tops)
  print """
   - killing unused nodes"""
  nodes = set(addr["node"].keys())
  for rel in addr["relation"].keys():
    nodes.difference_update(set([i[1] for i in addr["relation"][rel][CHILDREN] if i[0] == "node"]))
  for node in nodes:
    if node in addr["node"]:
      del addr["node"][node]
  
  print "Dropped nodes: %s"% len(nodes)

  f = open("tree.py", "w")
  f.write("tree = %s\n"%repr(addr))
  f.write("tops = %s\n"%repr(tops))
  print len(addr["node"])
  print len(addr["way"])
  print len(addr["relation"])
main()
