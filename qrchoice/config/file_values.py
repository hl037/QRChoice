from itertools import chain

from . import common
from . import values
import csv

def generator(path, count):
  with open(path, 'r') as f :
    r = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC, skipinitialspace=True)
    yield from ( val for val in r if len(val) == count )

def tableHandler(c: common.Config, lines):
  kv = {}
  files = []
  for k, v in common.parseKeyValues(lines):
    if k == 'file' :
      files.extend( (c.cwd.parent / s.strip()) for s in v.split(',') )
    else :
      kv[k] = v
  
  template = next(csv.reader([kv['template']], skipinitialspace=True))

  count = len(template)
  return common.TableValues(template, chain(*( generator(path, count) for path in files)))

def handler(c: common.Config, f):
  return values.genericHandler(tableHandler, c, f)
