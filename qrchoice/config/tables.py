from . import common
import sqlalchemy as sa

class TableOrKeyNotDefinedYet(RuntimeError):
  pass

class UnknownType(RuntimeError):
  pass

class UnknownColumnAttributesc(RuntimeError):
  pass

types = {
  'int': sa.Integer,
  'string' : sa.String(256),
}

sa_col_args = {
  'pk' : ('primary_key', True),
  'au' : ('autoincrement', True),
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
      raise UnknownColumnAttributesc(a)
    _sa_col_args[k] = v
  return sa.Column(name, type, **_sa_col_args)

def handler(c: common.Config, lines):
  mt = sa.MetaData()
  if not hasattr(c, '_table_fields') :
    c._table_fields = {}
  for t, entries in common.parseSection(lines):
    fields = []
    for k, v in common.parseKeyValues(entries) :
      if k == 'fields':
        fields.extend([ f.strip() for f in v.split(',') ])
    cols = [ parseColumn(t, c) for c in fields ]
    sa.Table(t, mt, *cols)
    c.tables.append(t)
    c._table_fields[t] = fields
  c.sa_model = mt

def to_file(c: common.Config, f):
  for t in c.tables :
    f.write(f'[{t}]\n')
    fields = ','.join(c._table_fields[t])
    f.write(f'fields = {fields}\n\n')
