from pathlib import Path
from io import StringIO
import re
from dataclasses import dataclass

section = re.compile(r'\[\[(\w+)\]\]')
subsection = re.compile(r'\[(\w+)\]')

class ConfigSyntaxError(RuntimeError):
  pass

class ConfigMissingKey(ConfigSyntaxError):
  pass

class ConfigUnknownKey(ConfigSyntaxError):
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
    self.qrchoices = {}
    self._after_hooks = []

  @property
  def tables(self):
    return self.sa_model.tables

  def do_after_hooks(self):
    for h in self._after_hooks :
      h(self)

  def to_file(self, f):
    from . import tables
    from . import qr_choices
    f.write('[[Tables]]\n')
    tables.to_file(self, f)
    f.write('[[QRChoices]]\n')
    qr_choices.to_file(self, f)

  def __str__(self):
    res = StringIO()
    self.to_file(res)
    return res.getvalue()

class LetterAfterGroup(RuntimeError):
  pass

class NotMatchingEndGroup(RuntimeError):
  pass

from dataclasses import dataclass

class ExpressionParser(object):
  """
  Parser capable of handling parenthesis and square brackets...

  The automaton builds a Tree.
  """
  LT = 0
  DL = 1
  BG = 2
  EG = 3
  IG = -1

  List = 0
  Group = 1
  Call = 2

  @dataclass
  class List(object):
    """
    List with a separator
    """
    dl:str
    d:list['ExpressionParser.Tree']

  @dataclass
  class Group(object):
    """
    Group (inside group delimiter)
    """
    bg:str
    eg:str
    d:'ExpressionParser.Tree'

  @dataclass
  class Call(object):
    """
    Call (group with a name before)
    """
    name:str
    bg:str
    eg:str
    d:'ExpressionParser.Tree'

  Tree = str | tuple[str, 'Tree'] | tuple[str, list['Tree']]
  Stack = list[Tree]

  list_delimiters = [] # type: list[tuple[str, int]]
  group_delimiters = [] # type: list[tuple[str, str]]
  ignored = [] # type: list[str]

  def get_token(self, s:str):
    if rv := next(( ig for ig in self.ignored if s.startswith(ig) ), None) :
      return self.IG, rv
    elif rv := next(( eg for _, eg in self.group_delimiters if s.startswith(eg) ), None) :
      return self.EG, rv
    elif rv := next(( (bg, eg) for bg, eg in self.group_delimiters if s.startswith(bg) ), None) :
      return self.BG, rv
    elif rv := next(( (dl, p) for dl, p in self.list_delimiters if s.startswith(dl) ), None) :
      return self.DL, rv
    else :
      return self.LT, s[0]

  def end_group(self, eg):
    if len(self.L[-1]) :
      self.end_list(self.L[-1][0])
      s_ = self.S.pop()
    else :
      s_ = self.m
      if s_ is None :
        s_ = self.S.pop()
    s__ = self.S[-1]
    if eg != s__.eg :
      raise NotMatchingEndGroup(f'Group begins with `{s__.bg}` and should end with `{s__.eg}` but `{eg}` found')
    self.S[-1].d = s_
    self.L.pop()
    self.m = None
    return

  def end_list(self, tok):
    t, p = tok
    if self.m is not None :
      s_ = self.m
    else :
      s_ = self.S.pop()
    self.m = ""
    if self.L[-1] :
      ct, cp = self.L[-1][-1]
      while cp <= p :
        self.S[-1].d.append(s_)
        if cp == p and ct == t:
          return
        s_ = self.S.pop()
        self.L[-1].pop()
        if not self.L[-1] :
          break
        ct, cp = self.L[-1][-1]
    self.S.append(self.List(t, [s_]))
    self.L[-1].append(tok)

  def parse(self, s):
    List = self.List
    Group = self.Group
    Call = self.Call
    
    self.S = []
    self.L = [[]]
    self.m = ""
    i = 0
    len_s = len(s)
    while i < len_s :
      T, tok = self.get_token(s[i:])
      match T:
        case self.LT:
          if self.m is None :
            raise LetterAfterGroup(f'{tok} occured just after a call or a group')
          self.m += tok
        case self.BG:
          if self.m == "" :
            self.S.append(Group(*tok, None))
          else :
            self.S.append(Call(self.m, *tok, None))
            self.m = ""
          tok = tok[0]
          self.L.append([])
        case self.EG:
          self.end_group(tok)
        case self.DL:
          self.end_list(tok)
          tok = tok[0]
        case self.IG:
          pass
      i += len(tok)
    if len(self.L) > 1 :
      raise NotMatchingEndGroup('End of line found before encontering group end')
    if len(self.S) == 0:
      return self.m
    if len(self.L[0]) >= 1 :
      self.end_list(self.L[0][0])
    return self.S[0]
  
  
