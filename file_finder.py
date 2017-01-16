#!/usr/bin/env python3

import glob
import os
import re
import sys

class InvalidFilenameException(Exception):
  pass

class FileInfo(object):
  def __init__(self):
    self.viewpoint = None
    self.island = None
    self.parts = None
    self.extension = None

  # Riven filenames are of the form *_*.ext where the first glob is the
  # viewpoint, and the second glob are the "parts". Parts are first '.'
  # delimited, and then '_' delimited. So the filename:
  #   508_text_foo.4500_s1_odo_lu.png
  # will be parsed to:
  #   {viewpoint:'508'
  #    island:'T'
  #    parts:[['ext', 'foo'], ['4500', 's1', 'odo', 'lu']]
  #    extension: 'png'}
  #  Note: the 't' prefix is removed when parsing as this is the island.
  def JoinParts(self):
    return '.'.join(['_'.join(part) for part in self.parts])

  def friendly_name(self):
    return self.JoinParts()

  def filename(self):
    return '%s_%s%s.%s' % (self.viewpoint,
                           self.island.lower(),
                           self.JoinParts(),
                           self.extension)
  def __str__(self):
    return '%s-%s: %s.%s' % (self.island,
                             self.viewpoint,
                             self.JoinParts(),
                             self.extension)

  def __lt__(self, other):
    return int(self.viewpoint) < int(other.viewpoint)

class FileFinder(object):
  def __init__(self):
    self.file_re = re.compile(r'^([^_]+)_(.+)\.([^\.]+)$')
    self.kveer_files = set()
    with open('kveer-files.txt') as f:
      for line in f.readlines():
        self.kveer_files.add(line.strip())

  # Returns an iterator
  def GetFiles(self, top_dir, extension):
    g = '%s/**/*.%s' % (top_dir, extension)
    return glob.iglob(g, recursive=True)

  def ParseFilename(self, fname):
    m = self.file_re.match(os.path.basename(fname))
    if m:
      info = FileInfo()
      info.viewpoint = m.group(1)
      if fname in self.kveer_files:
        info.island = 'K'
      else:
        info.island = m.group(2)[0].upper()
      parts = m.group(2)[1:].split('.')
      info.parts = []
      for part in parts:
        info.parts.append(part.split('_'))
      info.extension = m.group(3)
      return info
    else:
      raise InvalidFilenameException(fname)
