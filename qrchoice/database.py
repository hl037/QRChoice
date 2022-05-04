import sqlalchemy as sa
import sqlalchemy.orm
from pathlib import Path
from io import StringIO

from .config import Config


def engineFromPath(path):
  return sa.create_engine('sqlite:///' + str(path))


_InternalRegistery = sa.orm.registry()

class ReprMixin(object):
  def __repr__(self):
    fields = ','.join(f'{name}={repr(getattr(self, name))}' for name in self.__mapper__.column_attrs.keys())
    return f'{self.__mapper__.class_.__name__}({fields})'
    

@_InternalRegistery.mapped
class _Internal(ReprMixin):
  """
  Internal Key/value registry for storing configuration and information in the db...
  """
  __tablename__ = '_qrchoice'
  key = sa.Column(sa.String(26), primary_key=True)
  value = sa.Column(sa.Text)
  
@_InternalRegistery.mapped
class _QRCDetectionRun(ReprMixin):
  __tablename__ = '_qrc_detection_run'
  
  id = sa.Column(sa.Integer, primary_key=True)
  data = sa.Column(sa.JSON, index=True) # [(table_name, [(field, value)...].ordered), ...]

@_InternalRegistery.mapped
class _QRCDetectionImg(ReprMixin):
  __tablename__ = '_qrc_detection_img'
  id = sa.Column(sa.Integer, primary_key=True)
  run_id = sa.Column(sa.ForeignKey(_QRCDetectionRun.id), index=True)
  image = sa.Column(sa.String(256))
  image_name = sa.Column(sa.String(256), unique=True)
  target = sa.Column(sa.String(128))
  target_id = sa.Column(sa.Integer)
  ignore = sa.Column(sa.Boolean)
  
@_InternalRegistery.mapped
class _QRCDetectionQRC(ReprMixin):
  __tablename__ = '_qrc_detection_qrc'
  id = sa.Column(sa.Integer, primary_key=True)
  img_id = sa.Column(sa.ForeignKey(_QRCDetectionImg.id), index=True)
  data = sa.Column(sa.String(256))
  box = sa.Column(sa.JSON)

  


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
    with self.session() as s :
      s.add(_Internal(key='config', value=str(self.config)))
      s.commit()

  def session(self):
    return sa.orm.Session(self.engine)

  def fill(self):
    with self.engine.connect() as conn :
      for t in self.config.tables :
        if t in self.config.values :
          V = self.config.values[t]
          T = self.t[t] #type: sa.Table
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

  @property
  def t(self) -> dict[str, sa.Table]:
    return self.config.sa_model.tables

  @staticmethod
  def fromDB(engine: sa.engine):
    from .config import parse
    with sa.orm.Session(engine) as s :
      _c = s.get(_Internal, 'config')
      return DB(parse(Path(),StringIO(_c.value)), engine)

def getConverter(col: sa.Column):
  if isinstance(col.type, sa.Integer) :
    return int
  elif isinstance(col.type, sa.String) :
    return str
  
