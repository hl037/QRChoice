

from functools import cached_property, wraps
import traceback


from icecream import ic

import sockpdb

base_prefix = 'ic> '
ic.prefix = base_prefix
ic_indent_level = 0

def ic_indent(f):
  @wraps(f)
  def _f(*args, **kwargs):
    global ic_indent_level
    old = ic.prefix
    ic(f.__name__)
    ic_indent_level += 1
    ic.prefix = '|  ' * ic_indent_level + ic.prefix
    try :
      return f(*args, **kwargs)
    finally :
      ic_indent_level -= 1
      ic.prefix = old
      print(ic.prefix[:-len(base_prefix)])
      
  @wraps(f)
  def __f(*args, **kwargs):
    try :
      return f(*args, **kwargs)
    except :
      ic('An error occured, remote debugger launched')
      traceback.print_exc()
      sockpdb.pm()

  #return f
  #return _f
  return __f
