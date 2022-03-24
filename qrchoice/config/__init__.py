import re

from . import common
from . import tables
from . import qr_choices
from . import values
from . import file_values

handlers = {
  'tables' : tables.handler,
  'values' : values.handler,
  'filevalues' : file_values.handler,
  'qrchoices' : qr_choices.handler,
}


class UnknownSection(RuntimeError):
  pass



def parse(cwd, f):
  c = Config(cwd)
  for sec, lines in common.parseConfig(f) :
    sec = sec.lower()
    if sec not in handlers :
      raise UnknownSection(sec)
    handlers[sec](c, lines)
  c.do_after_hooks()
  return c

Config = common.Config


