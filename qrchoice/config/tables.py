from functools import reduce
from dataclasses import dataclass
from collections import defaultdict
from . import common
import sqlalchemy as sa
    
class ColumnParserError(RuntimeError):
  pass

class TableOrKeyNotDefinedYet(ColumnParserError):
  pass

class UnknownType(ColumnParserError):
  pass

class UnknownColumnAttributes(ColumnParserError):
  pass

List = common.ExpressionParser.List
Group = common.ExpressionParser.Group
Call = common.ExpressionParser.Call

types = {
  'int': sa.Integer,
  'string' : sa.String(256),
}

sa_col_args = {
  'pk' : ('primary_key', True),
  'au' : ('autoincrement', True),
  'u' : ('unique', True),
}

def parseColumn(t, c):
  name, type, *attrs = c.split(':')
  if '.' in type :
    type = sa.ForeignKey(type)
  else :
    try :
      type = types[type]
    except KeyError:
      raise UnknownType(type)
  _sa_col_args = {}
  for a in attrs :
    try :
      k, v = sa_col_args[a]
    except :
      raise UnknownColumnAttributes(a)
    _sa_col_args[k] = v
  return sa.Column(name, type, **_sa_col_args)

class ColumnParser(common.ExpressionParser):
  """
  Parse table column definitions
  """
  ignored = [' ', '\t']
  list_delimiters = [('.', 0), (':', 10), (',', 20)]
  group_delimiters = [('(', ')')]

  def parse(self, s:str):
    res = super().parse(s)
    match res:
      case List(',', cols) | (List(':', _) as cols) :
        return cols
      case _ :
        raise ColumnParserError('Syntax error')

@dataclass
class EntrySet(object):
  """
  Represent a table property that is a set using an mid table as join.
  """
  name: str
  src_name: str
  target_name: str
  src: sa.Table = None
  target: sa.Table = None
  mid: sa.Table = None

  def target_col_names(self):
    t = self.target
    return [ (f'{t.name}_{col.name}', col.name) for col in t.primary_key ]
    
  def src_col_names(self):
    t = self.src
    return [ (f'{t.name}_{col.name}', col.name) for col in t.primary_key ]

  @property
  def mid_name(self):
    return f'_{self.src_name}_x_{self.target_name}'

  @property
  def src_fk_name(self):
    return f'fk_{self.src_name}'
  
  @property
  def target_fk_name(self):
    return f'fk_{self.target_name}'

  def src_fk_cols(self):
    return tuple( self.mid.c[col_name] for col_name, _ in self.src_col_names() )
  
  def target_fk_cols(self):
    return tuple( self.mid.c[col_name] for col_name, _ in self.target_col_names() )

  def src_pk_cond(self, *values):
    t = self.src
    return reduce(lambda x, y: x & y, ( c == v for c, v in zip(self.src_fk_cols(), values) ))
  
  def target_pk_cond(self, *values):
    t = self.target
    return reduce(lambda x, y: x & y, ( c == v for c, v in zip(self.target_fk_cols(), values) ))

  def populate_src(self, obj, *values):
    for (col_name, _), v in zip(self.src_col_names(), values) :
      obj[col_name] = v
    return obj
      
  def populate_target(self, obj, *values):
    for (col_name, _), v in zip(self.target_col_names(), values) :
      obj[col_name] = v
    return obj


def parseColumn(c, fks, uniques, sets):
  """
  tables: dict[tablename, (table, constaints, relations)]
  """
  extra = {}
  delayed = False
  match c :
    case  List(':', [name, type, *args]) :
      pass
    case _ :
      raise ColumnParserError('Syntax error')
  match type :
    case str() :
      type = types[type]
    case  List('.', ( str() as target, str() as fk )) :
      type = sa.ForeignKey(f'{target}.{fk}')
    case  Call('fk', '(', ')',
            List(',', (
              str() as fk_id,
              List('.', ( str() as target, str() as fk )))
            )
          ) :
      immediate, _target, l = fks.setdefault(fk_id, (True, target, []))
      if immediate and _target != target :
        raise ColumnParseError(f'Composite foreign key with different target tables : `{_target}` and `{target}`')
      l.append((name, f'{target}.{fk}'))
    case  Call('fk', '(', ')', (
              ((str() as fk_id) as target) |
              List(',', str() as fk_id, str() as target)
            )
          ):
      if fk_id in fks :
        raise ColumnParserError(f'A same generated foreign key may only appear once per table : `{fk_id}`')
      fks[fk_id] = (False, target, None)
      delayed = True
      name = fk_id
    case  Call('set', '(', ')', str() as target) :
      sets[name] = EntrySet(name, None, target)
      return None
    case _ :
      raise UnknownType()
  for a in args :
    match a :
      case str() :
        k, v = sa_col_args[a]
        extra[k] = v
      case  Call('u', '(', ')', str() as u_id):
        l = uniques.setdefault(u_id, [])
        l.append(name)
      case _ :
        raise ColumnParserError('Unknown extra argument')
  if delayed :
    return None
  return sa.Column(name, type, **extra)
  

def addTable(c: common.Config, table_name:str, col_defs:str):
  if c.sa_model is None :
    c.sa_model = sa.MetaData()
  if not hasattr(c, '_explicit_tables') :
    c._explicit_tables = []
    c._after_hooks.append(postProcessTable)
  parser = ColumnParser()
  cols = parser.parse(col_defs)
  fks = {}
  uniques = {}
  sets = {} # type: dict[str, EntrySet]
  args = [ col for cdef in cols if (col := parseColumn(cdef, fks, uniques, sets)) is not None ]
  if not any( col.primary_key for col in args ) :
    args.insert(0, sa.Column('id', sa.Integer, primary_key=True))
  t = sa.Table(
      table_name,
      c.sa_model,
      *args,
      *( sa.ForeignKeyConstraint(*zip(*fk), name) for fk_id, (im, target, _) in fks.items() if im ),
  )
  t.sets = sets # type: dict[str, EntrySet]
  t.delayed_fks = [ (fk_id, target) for fk_id, (im, target, _) in fks.items() if not im ]
  t.delayed_uniques = uniques
  c._explicit_tables.append(table_name)
  return t


def postProcessTable(c: common.Config):
  for t1name in c._explicit_tables :
    t1 = c.tables[t1name] # type: sa.Table
    for S in t1.sets.values() : # type: EntrySet
      t2name = S.target_name
      S.src_name = t1name
      S.src = t1
      t2 = c.tables[t2name]
      S.target = t2
      S.mid = sa.Table(
        S.mid_name,
        c.sa_model,
        *(
          sa.Column(colname, None, primary_key=True)
          for colname, _ in S.src_col_names()
        ),
        *(
          sa.Column(colname, None, primary_key=True)
          for colname, _ in S.target_col_names()
        ),
        sa.ForeignKeyConstraint(
          [ colname for colname, _ in S.src_col_names() ],
          [ f'{S.src_name}.{src_colname}' for _, src_colname in S.src_col_names() ],
          name = S.src_fk_name
        ),
        sa.ForeignKeyConstraint(
          [ colname for colname, _ in S.target_col_names() ],
          [ f'{S.target_name}.{target_colname}' for _, target_colname in S.target_col_names() ],
          name = S.target_fk_name
        ),
      )
    for fk_id, target in t1.delayed_fks :
      t2 = c.tables[target] # type: sa.Table
      foreign_cols = list(t2.primary_key)
      local_cols = [ sa.Column(f'{fk_id}_{col.name}') for col in foreign_cols ]
      for col in local_cols :
        t1.append_column(col)
      t1.append_constraint(sa.ForeignKeyConstraint(local_cols, foreign_cols, name=fk_id))
    del t1.delayed_fks
    
    t1.fks = { fk.name : fk for fk in t1.foreign_key_constraints if fk.name is not None }
    
    for name, cols in t1.delayed_uniques.items() :
      ucols = []
      for col in cols :
        if col in t1.columns.keys() :
          ucols.append(col)
        else :
          fk = t1.fks[col]
          ucols.extend(fk.columns)
      t1.append_constraint(sa.UniqueConstraint(*ucols, name=name))
    del t1.delayed_uniques
            
        

def handler(c: common.Config, lines):
  for t, entries in common.parseSection(lines):
    fields = []
    for k, v in common.parseKeyValues(entries) :
      if k == 'fields':
        fields.append(v)
    col_defs = ','.join(fields)
    table = addTable(c, t, col_defs)
    table._fields = col_defs
    table.section = 'Tables'

def to_file(c: common.Config, f):
  for tname in c._explicit_tables :
    table = c.tables[tname]
    if table.section == 'Tables' :
      f.write(f'[{tname}]\n')
      f.write(f'fields = {table._fields}\n\n')



