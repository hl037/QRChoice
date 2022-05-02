from functools import reduce
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence as Seq

import sqlalchemy as sa

from ...database import DB, _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter
from ...config.tables import EntrySet

from icecream import ic

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
    self.default_values = { k: {k2: v2 for k2, v2 in v} for k, v in self.run.data }

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
    # DO NOT SORT DATA (the order or tables is needed for qrchoice matching
    with db.session() as S :
      res = S.query(R).filter(R.data == data).all()
      assert len(res) <= 1
      if len(res) == 1 :
        return cls(db, res[0])
      run = R(data=data)
      S.add(run)
      S.commit()
      S.refresh(run)
      return cls(db, run)

  def update_imgs(self, S:sa.orm.Session, img_paths:Seq[Path], data:Seq[QRCDetection], progress_cb=lambda i, j:None):
    """
    Add or update the image bounding box. Only add boxes, don't remove.
    """
    rid = self.run.id
    im_ids = [] # type: list[tuple[int, bool] # pk, is new
    stmt_im_sel = sa.select(I).where((I.image_name == sa.bindparam('im_name')) & (I.run_id == rid))
    stmt_im_ins = sa.insert(I)
    for i, p in enumerate(img_paths) :
      p_s = str(p)
      name = p.name
      imgs = S.scalars(stmt_im_sel, {'im_name': name}).all()
      assert len(imgs) <= 1
      if len(imgs) == 1 :
        im_ids.append((imgs[0].id, False))
      else :
        im_ids.append((
          S.execute(stmt_im_ins, {'run_id': rid, 'image': p_s, 'image_name': name}).inserted_primary_key[0],
          True
        ))
      progress_cb(0, i)
    S.flush()
    stmt_qrc_data_sel = sa.select(C.data).where(C.img_id == sa.bindparam('im'))
    stmt_qrc_ins = sa.insert(C)
    to_dispatch = []
    for i, ((im_id, is_new), detect) in enumerate(zip(im_ids, data)) :
      #get existing box data
      qrcs = set(S.scalars(stmt_qrc_data_sel, {'im': im_id}))
      to_insert = [ {'img_id': im_id, 'data':d, 'box': box} for (d, box) in detect if d not in qrcs ]
      progress_cb(1, i)
      if is_new or to_insert :
        to_dispatch.append(im_id)
      S.execute(stmt_qrc_ins, to_insert)
      S.flush()
    self.dispatch(S, to_dispatch)

  def dispatch(self, S:sa.orm.Session, im_ids:list[int]):
    """
    Dispatch the images among the result table (assign target and target_id)
    """
    stmt_qrcdata_sel = sa.select(C.data).where((C.img_id == sa.bindparam('im_id')) & (C.data != None))
    stmt_target_sel = sa.select(I.target, I.target_id).where(I.id == sa.bindparam('im_id'))
    stmt_update_im = (
      sa.update(I)
      .where(I.id == sa.bindparam('im_id'))
      .values(target=sa.bindparam('target'), target_id=sa.bindparam('target_id'))
    )
    to_update = set()
    for im_id in im_ids :
      target, target_id = S.execute(stmt_target_sel, {'im_id': im_id}).one()
      data = S.scalars(stmt_qrcdata_sel, {'im_id': im_id}).all()
      filtered = dict()
      for table, id in ( v for v in (d.split(':') for d in data) if len(v) == 2 ) :
        filtered.setdefault(table, []).append(id)
      # match target
      new_target = None
      for table_name, _ in self.run.data :
        table, qrchoice = self.qrchoices[table_name]
        if all( (min_ <= len(filtered.get(k, [])) <= max_) for k, (min_, max_) in qrchoice.items() ) :
          new_target = table_name
          break
      if new_target is not None :
        # create new object
        obj_dict = dict(self.default_values[new_target])
        for k, v in filtered.items() :
          if k not in table.sets :
            if not k in table.c :
              k = next(iter(table.fks[k].columns.values())).name # change for supporting composite pk
            v, = v
            obj_dict[k] = v
        
        # match target_id
        # cond = (uc1.c1 == o[uc1.c1] & uc1.col2 == o[uc1.c2] & ...) | (uc2.c1 == o[uc2.c1] & uc2.c2 == o[uc2.c2] & ...) | ...
        cond = reduce(lambda x, y: x | y, (
            reduce(lambda x, y: x & y, (
                col == obj_dict[col.name]
              for col in uc 
            ))
          for uc in ( c for c in table.constraints if isinstance(c, sa.UniqueConstraint) )
        ))
        res = S.execute(sa.select(table).where(cond)).all()
        assert len(res) <= 1
        if len(res) != 0 :
          res = res[0]
          new_target_id = res['id']
        else :
          new_target_id = S.execute(sa.insert(table), obj_dict).inserted_primary_key[0]
          S.flush()
        to_update.add((new_target, new_target_id))
      if target is not None and target_id is not None :
        to_update.add((target, target_id))
      S.execute(stmt_update_im, {'im_id': im_id, 'target':new_target, 'target_id':new_target_id})
      S.flush()
    self.update_res(S, to_update)

  def update_res(self, S:sa.orm.Session, targets: Seq[tuple[str, int]]):
    """
    Update result tables records based on all image referring them...
    """
    stmt_sel_qrcdata = sa.select(C.data).where(
      (I.target == sa.bindparam('target')) &
      (I.target_id == sa.bindparam('target_id')) &
      (C.img_id == I.id)
    )
    for target, target_id in targets :
      table, qrchoice = self.qrchoices[target]
      data = set(S.scalars(stmt_sel_qrcdata, {'target':target, 'target_id': target_id}).all())
      filtered = dict()
      for field_name, id in ( v for v in (d.split(':') for d in data) if len(v) == 2) :
        filtered.setdefault(field_name, []).append(id)
      obj_dict = dict(self.default_values[target])
      sets = [] # type: list[tuple[EntrySet, list[int]]]
      do_update = True
      for k, v in filtered.items() :
        if k not in table.sets :
          if not k in table.c :
            k = next(iter(table.fks[k].columns.values())).name # change for supporting composite pk
          if len(v) == 1 :
            v, = v
            obj_dict[k] = v
        else :
          sets.append((table.sets[k],  v))
      # Update main object
      S.execute(sa.update(table).where(table.c.id == target_id).values(obj_dict))
      S.flush()
      # Update sets
      for s, vals in sets :
        S.execute(sa.delete(s.mid).where(s.src_pk_cond(target_id)))
        S.flush()
        S.execute(sa.insert(s.mid).values([
            s.populate_target(s.populate_src(dict(), target_id), v)
          for v in vals
        ]))
        S.flush()

  @property
  def qrchoices(self):
    return self.db.config.qrchoices
      







