import sqlalchemy as sa
import sqlalchemy.orm
from pathlib import Path
from io import StringIO

from .config import Config


def engineFromPath(path):
  return sa.create_engine('sqlite:///' + str(path))


_InternalRegistery = sa.orm.registry()

@_InternalRegistery.mapped
class _Internal(object):
  """
  Internal Key/value registry for storing configuration and information in the db...
  """
  __tablename__ = '_qrchoice'
  key = sa.Column(sa.String(26), primary_key=True)
  value = sa.Column(sa.Text)
    


class DB(object):
  """
  A Database abstraction around sqlalchemy
  """
  def __init__(self, config:Config, engine: sa.engine.Engine):
    self.config = config
    self.engine = engine

  def createIfNeeded(self):
    self.config.sa_model.create_all(self.engine)
    _InternalRegistery.metadata.create_all(self.engine)
    with sa.orm.Session(self.engine) as s :
      s.add(_Internal(key='config', value=str(self.config)))
      s.commit()

  def fill(self):
    with self.engine.connect() as conn :
      for t in self.config.tables :
        if t in self.config.values :
          V = self.config.values[t]
          T = self.config.sa_model.tables[t] #type: sa.Table
          ins = T.insert().values(**{ col: sa.bindparam(str(i)) for i, col in enumerate(V.template) })
          l = [ { str(i): v for i, v in enumerate(row) } for row in V.generator ]
          #conn.execute(ins, *( { str(i): v for i, v in enumerate(row) } for row in V.generator ))
          conn.execute(ins, *l)

  def getObjects(self, table):
    T = self.config.sa_model.tables[table]
    with self.engine.connect() as conn :
      yield from conn.execute(sa.select(T))

  def getPK(self, table):
    T = self.config.sa_model.tables[table]
    return [ c.name for c in T.primary_key ]

  @staticmethod
  def fromDB(engine: sa.engine):
    from .config import parse
    with sa.orm.Session(engine) as s :
      _c = s.get(_Internal, 'config')
      return DB(parse(Path(),StringIO(_c.value)), engine)
    
    

  
