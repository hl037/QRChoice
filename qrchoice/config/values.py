from . import common
import csv

def tableHandler(c: common.Config, lines):
  it = iter(lines)
  template = []
  for l in it :
    if '=' in l :
      k, v = common.getKeyValue(l)
      if k == 'template' :
        template = next(csv.reader([v], skipinitialspace=True))
        break
    if l.strip() != '' :
      raise common.ConfigSyntaxError(l)

  r = csv.reader(it, quoting=csv.QUOTE_NONNUMERIC, skipinitialspace=True)
  count = len(template)

  return common.TableValues(template, ( val for val in r if len(val) == count ))
    
  
def genericHandler(tableHandler, c: common.Config, f):
  for sec, lines in common.parseSection(f) :
    c.values[sec] = tableHandler(c, lines)


def handler(c: common.Config, f):
  return genericHandler(tableHandler, c, f)
