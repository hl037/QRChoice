from contextlib import contextmanager
from pathlib import Path

from ..database import DB, _QRCDetectionRun as R, _QRCDetection as D, getConverter

class UnknownTable(RuntimeError):
  pass

class NoEntryMatchingQRCDetectionConstrainsts(RuntimeError):
  pass
    

class MissingTableFields(RuntimeError):
  def __init__(self, entry, d1, d2):
    super().__init__(
      f'In entry {entry}, ' + 
      ('' if not d1 else ('Missing [' + ','.join(d1) + '] fields; ')) + 
      ('' if not d2 else ('Not expecting [' + ','.join(d2) + '] fields; '))
    )
    self.entry = entry
    self.d1 = d1
    self.d2 = d2

class QRChoiceRun(object):
  """
  Class to store data for a QRChoice run on a se of images
  entries is a dict `entry -> ( field -> value )`
  """
  def __init__(self, db: DB, entries:dict[str, dict[str, str]], id=None):
    self.db = db
    self.entries = entries
    self.id = id
    self._model = None
    self._session = None
    
    #check all entries correspond to a qrchoice table
    if id is None :
      for entry, fields in entries :
        if entry not in self.qrchoices :
          raise UnknownTable(entry)
        T, v = self.qrchoices[entry]
        table_fields = set(self.db.t[entry].keys())
        provided_fields = { a[0] for a in v } | set(fields.keys())
        d1 = table_fields - provided_fields
        d2 = provided_fields - table_fields
        if d1 != d2 :
          raise MissingTableFields(entry, d1, d2)
      self._cache_converters()

  def _cache_converters(self):
    self._converters = {
        entry: {
            col_name: getConverter(col)
          for col_name, col in self.db.t[entry].c.getitems()
        }
      for entry in self.entries.keys()
    }
    # self._pk_converters = {
    #     entry: [
    #         getConverter(col)
    #       for col in self.db.t[entry].primary_key
    #     ]
    #   for entry in self.entries.keys()
    # }

  
  def replaceDetection(self, image:Path, values:list[str, list]):
    """
    Add or replace a detection.
    values is a list of tuples (qrc_data, [<Polygon>])
    """
    assert self._session
    # Get first entry matching
    img = str(image)
    d = self._session.get(D, (self.id, img))
    todelete = set()
    if d is not None :
      # Flag element potentially to delete
      todelete = set(d.data['created'])
    # Detect qrchoice...
    detected = {}
    for qrc_data, rect in values :
      key, v = qrc_data.split()
      if (l := detected.get(key)) is None :
        l = []
        detected[key] = l
      l.append(v)
    try :
      entry = next( entry for entry in self.entries.keys() if (
        set( detected.keys()) == set(qrc[0] for qrc in (qrce := self.qrchoices[entry])) and
        all( (min_ <= len(detected[field]) <= max_) for field, (min_, max_), *_ in qrce )
      ))
    except :
      raise NoEntryMatchingQRCDetectionConstrainsts(detected)
      


  def _fromModel(self):
    self.entries = self._model.data['entries']
    self.id = self._model.id
    self._cache_converters()

  def _toModel(self):
    self._model.data = {
      'entries' : self.entries
    }
    
  @contextmanager
  def session(self):
    with self.db.session() as s:
      if self.id is not None :
        self._model = s.get(R, self.id)
        self._fromModel()
      else :
        self._model = R(entry=self.entry, data={})
        self._toModel()
        s.add(self._model)
        s.flush()
        self.id = self._model.id
      self._session = s
      yield
      self._session = None

  @property
  def qrchoices(self):
    return self.db.config.qrchoices
      







class BaseReader(object):
  """
  Multi QRcode reader
  """
  def __init__(self):
    pass

  def readQRCodes(self, img):
    """
    Read qr codes in img, and return a list of tuple (data, [(x0, y0), ..., (x3, y3)]) of the polygon of the read qrcode.
    """
    raise NotImplementedError()


    

class ZLibReader(BaseReader):
  """
  
  """
  def __init__(self):
    
