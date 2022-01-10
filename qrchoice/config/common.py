from pathlib import Path
from io import StringIO
import re

section = re.compile(r'\[\[(\w+)\]\]')
subsection = re.compile(r'\[(\w+)\]')

class ConfigSyntaxError(RuntimeError):
  pass

def parse(rx, f):
  current = None
  lines = []
  for l in f :
    if (m := rx.match(l)) :
      if current :
        yield current, lines
        lines = []
      current = m[1]
    else:
      lines.append(l)
  yield current, lines

def parseSection(f):
  yield from parse(subsection, f)

def parseConfig(f):
  yield from parse(section, f)

def getKeyValue(l):
  return ( s.strip() for s in l.split('=') ) 

def parseKeyValues(f):
  yield from ( getKeyValue(l)  for l in f if '=' in l )
  
  

class TableValues(object):
  """
  A generator for the values of a table.
  """
  def __init__(self, template, generator):
    self.template = template
    self.generator = generator


class Config(object):
  """
  Hold a configuration
  """
  def __init__(self, cwd:Path):
    self.cwd = cwd
    self.sa_model = None
    self.values = {} # type: dict[str, TableValues]
    self.qrchoices = None
    self.tables = []

  def to_file(self, f):
    from . import tables
    f.write('[[Tables]]\n')
    tables.to_file(self, f)

  def __str__(self):
    res = StringIO()
    self.to_file(res)
    return res.getvalue()

