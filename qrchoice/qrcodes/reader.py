import json
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence as Seq
from PIL import Image

import sqlalchemy as sa

from ..database import DB, _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter

class UnknownTable(RuntimeError):
  pass

class UnknownTableColumn(RuntimeError):
  pass

class IncompatibleValue(RuntimeError):
  pass

class NoEntryMatchingQRCDetectionConstrainsts(RuntimeError):
  pass
    

TableRunFieldValues = list[tuple[str ,str]]

def parseTable(s:str) -> tuple[str, TableRunFieldValues]:
  table, *fields = map(str.strip, s.split(':'))
  return table, [ tuple(map(str.strip, _s.split('='))) for _s in fields ]

def imGenerator(paths):
  """
  This image generator closes the file after each read
  """
  for p in paths :
    with Image.open(p) as im :
      yield im
    
  

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

QRCDetection = list[tuple[str, list[tuple[int, int]]]]

class BaseReader(object):
  """
  Multi QRcode reader
  """
  def __init__(self):
    pass

  def readQRCodes(self, img) -> QRCDetection:
    """
    Read qr codes in img, and return a list of tuple (data, [(x0, y0), ..., (x3, y3)]) of the polygon of the read qrcode.
    """
    raise NotImplementedError()
  

from pyzbar.pyzbar import decode as pyzbar_decode
class ZBarReader(BaseReader):
  """
  
  """
  def readQRCodes(self, im):
    return [
        (
          d.data.decode('utf8'),
          [ [p.x, p.y] for p in d.polygon ] 
        )
      for d in pyzbar_decode(im)
    ]


zbarReader = ZBarReader()
    

class QRChoiceRun(object):
  """
  Class to store data for a QRChoice run on a set of images
  entries is a dict `entry -> ( field -> value )`
  """
  def __init__(self, db: DB, run: R):
    self.db = db
    self.run = run

  @classmethod
  def createOrGetRun(cls, db:DB, entries:list[tuple[str, TableRunFieldValues]]):
    # check entries
    data = []
    for tname, fields in entries :
      try :
        t = db.t[tname]
      except :
        raise UnknownTable(tname)
      out_fields = []
      for k, v in fields :
        if k not in t.columns :
          raise UnknownTableColumn(f'{tname}.{k}')
        col = t.columns[k]
        conv = getConverter(col)
        try :
          val = conv(v)
        except :
          raise IncompatibleValue(f'Expected : {conv.__name__}, got "{v}"')
        out_fields.append([k, val])
      out_fields.sort()
      data.append([tname, out_fields])
    data.sort()
    d = json.dumps(data)
    with db.session() as S :
      res = S.query(R).filter(R.data == d).all()
      assert len(res) <= 1
      if len(res) == 1 :
        return cls(db, res[0])
      run = R(data=d)
      S.add(run)
      S.commit()
      S.refresh(run)
      return cls(db, run)

  def update_imgs(self, S:sa.orm.Session, img_paths:Seq[Path], data:Seq[QRCDetection], progress_cb=lambda i, j:None):
    #TODO : update
    rid = self.run.id
    im_ids = []
    stmt_im_sel = sa.select(I).where(I.image == sa.bindparam('im'))
    stmt_im_ins = sa.insert(I)
    for i, p in enumerate(img_paths) :
      p_s = str(p)
      imgs = S.scalars(stmt_im_sel, {'im': p_s}).all()
      assert len(imgs) <= 1
      if len(imgs) == 1 :
        #TODO: Maybe simply remove everything related to this image ?
        raise NotImplementedError('updating is not supported yet')
      else :
        im_ids.append(
          S.execute(stmt_im_ins, {'run_id': rid, 'image': p_s}).inserted_primary_key[0]
        )
      progress_cb(0, i)
    S.flush()
    stmt_qrc_ins = sa.insert(C)
    detected = [
        {'img_id': im_id, 'data': d, 'box': box}
      for i, (im_id, detect) in enumerate(zip(im_ids, data)) for (d, box) in (detect, progress_cb(1, i))[0]
    ]
    S.execute(stmt_qrc_ins, detected)
    S.flush()

  @property
  def qrchoices(self):
    return self.db.config.qrchoices
      







