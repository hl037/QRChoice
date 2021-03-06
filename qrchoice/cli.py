from pathlib import Path
import click
from functools import wraps

from .layout import layouts


def dbg_wrap(f):
  @wraps(f)
  def wrapper(*args, **kwargs):
    try :
      return f(*args, **kwargs)
    except click.Abort:
      pass
    except :
      import pdb
      if hasattr(pdb, 'xpm') :
        pdb.xpm()
      else :
        pdb.pm()
  return wrapper


@click.group()
def main():
  pass

@main.command(name="create-db")
@click.option('--config', '-c', 'conf', type=str)
@click.argument('dbpath')
@dbg_wrap
def create_db(conf, dbpath):
  from . import database
  from . import config
  
  dbp = Path(dbpath)
  if dbp.exists() :
    click.confirm('The database already exists, and will be overwritten, are you sure to continue?', abort=True)
    dbp.unlink()
  with open(conf, 'r') as f :
    cwd = Path(conf)
    conf = config.parse(cwd, f)
    db = database.DB(conf, database.engineFromPath(dbpath))
    db.createIfNeeded()
    db.fill()

@main.command(name='gen-qrc')
@click.argument('dbpath')
@click.option('--output', '-o', type=(str, str, str), multiple=True, default = [],
    help="A triplet of `-o TABLE TEXT DEST` where TEXT and DEST are patterns for each qrcode output path. It can contain %{field} where field is a column in the table."
)
@dbg_wrap
def gen_qrc(dbpath, output):
  """
  Generate images of qr-codes for items in the database
  """
  from . import database
  from .qrcodes.generator import qrcodeGenerator, RowFormatter, addText
  
  db = database.DB.fromDB(database.engineFromPath(dbpath))
  for t, text, dest in output :
    fmt_text = RowFormatter(text)
    fmt_dest = RowFormatter(dest)
    for r, im in qrcodeGenerator(db, t) :
      p = Path(fmt_dest(r))
      p.parent.mkdir(parents=True, exist_ok=True)
      im_t = addText(im, fmt_text(r))
      im_t.save(p)


a4 = (2480, 3508)
#a4 = (2480, 3600)

@main.command(name='layout-img')
@click.argument('imgs', nargs=-1)
@click.option('--output', '-o', type=str)
@click.option('--layout', '-y', type=click.Choice(list(layouts.keys()), case_sensitive=False), help='Layout to use. "grid" is the default which arrange as a grid of the largest element size. "brute" tries to find the optimal layout without rotation except 90?? ones, but it is slow if many small images. "rectpack" uses the rectpack library, it is fast, similare to "brute", but will unlikely find the optimal solution. Then "pynest" is experimental.')
@dbg_wrap
def layoutImg(imgs, output, layout):
  from .layout import openImage, nestImages, saveAsPDF
  images = [ openImage(im) for im in imgs ]
  pages, _ = nestImages(images, a4, layout=layout)
  saveAsPDF(output, pages)


@main.command(name='layout-img-qrc')
@click.argument('dbpath')
@click.option('--table', '-t', type=(str, str, str), multiple=True, default = [],
    help="A triplet of `-t TABLE TEXT IMG_IN` where TEXT, IMG_IN are patterns for each qrcode output path. It can contain %{field} where field is a column in the table."
)
@click.option('--output', '-o', type=str, help="PDF output file path")
@click.option('--longside/--shortside', '-l/-s', help="Long side / short side turn")
@click.option('--layout', '-y', type=click.Choice(list(layouts.keys()), case_sensitive=False), help='Layout to use. "grid" is the default which arrange as a grid of the largest element size. "brute" tries to find the optimal layout without rotation except 90?? ones, but it is slow if many small images. "rectpack" uses the rectpack library, it is fast, similare to "brute", but will unlikely find the optimal solution. Then "pynest" is experimental.')
@dbg_wrap
def layoutImg(dbpath, table, output, longside, layout):

  from . import database
  from .layout import openImage, nestImages, saveAsPDF, layoutImagesAndQRCodes
  from .qrcodes.generator import qrcodeGenerator, RowFormatter, addText

  images = []
  qrcodes = []
  
  db = database.DB.fromDB(database.engineFromPath(dbpath))
  for t, text, im_p in table :
    fmt_text = RowFormatter(text)
    fmt_im_p = RowFormatter(im_p)
    for r, im in qrcodeGenerator(db, t) :
      im_t = addText(im, fmt_text(r))
      qrcodes.append(im_t)
      images.append(openImage(fmt_im_p(r)))

  pages = layoutImagesAndQRCodes(images, qrcodes, a4, long_side_turn=longside, layout=layout)
  saveAsPDF(output, pages)


@main.command(name='read-qrc')
@click.argument('dbpath', type=str, nargs=1)
@click.argument('paths', type=str, nargs=-1)
@click.option('--table', '-t', type=str, multiple=True, help="passed as : --table=table:column=value:...")
@click.option('--id', '-i', type=str, default=None)
@dbg_wrap
def readQrc(dbpath, paths, table, id):
  from . import database
  from .qrcodes.reader import parseTable, zbarReader, QRChoiceRun
  from .images import imGenerator

  db = database.DB.fromDB(database.engineFromPath(dbpath))
  tables = [ parseTable(t) for t in table ]
  qrc_run = QRChoiceRun.createOrGetRun(db, tables)
  im_gen = imGenerator(paths)
  len_paths = len(paths)
  print()
  def progress(i, j):
    click.echo(f'{50*(i+j/len_paths):>2.2f}%\r', nl=False)
  with db.session() as S :
    qrc_run.update_imgs(S, map(Path, paths), map(zbarReader.readQRCodes, im_gen), progress_cb=progress)
    S.commit()
  print()

@main.command(name='browse-db')
@click.argument('dbpath', type=str, nargs=1)
@dbg_wrap
def browseDb(dbpath):
  from . import database
  from .qrcodes.reader.gui import QRCTreeModel
  from PySide6.QtWidgets import QTreeView, QApplication
  
  db = database.DB.fromDB(database.engineFromPath(dbpath))
  model = QRCTreeModel(db)
  app = QApplication([])
  tv = QTreeView()
  tv.setModel(model)
  tv.show()
  app.exec()
  return
  

@main.command(name='qrc-gui')
@click.argument('dbpath', type=str, nargs=1)
@dbg_wrap
def testGui(dbpath):
  from . import database
  from .database import _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter
  from .qrcodes.reader.gui import QRCFixer
  import sqlalchemy as sa

  db = database.DB.fromDB(database.engineFromPath(dbpath))
  gui = QRCFixer(db)
  gui.exec()

@main.command(name='redispatch-all')
@click.argument('dbpath', type=str, nargs=1)
@dbg_wrap
def redispatchAll(dbpath):
  import sqlalchemy as sa
  from . import database
  from .database import _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter
  from .qrcodes.reader import QRChoiceRun
  db = database.DB.fromDB(database.engineFromPath(dbpath))
  with db.session() as S :
    res = S.scalars(sa.select(R)).all()
    for r in res:
      run = QRChoiceRun(db, r)
      imgs = list(S.scalars(sa.select(I.id).where(I.run_id == r.id)).all())
      run.dispatch(S, imgs)
      S.commit()

@main.command(name='im-enhance')
@click.option('--filters', '-f', type=str)
@click.option('--output', '-o', type=click.Path( file_okay=False, dir_okay=True, resolve_path=True))
@click.argument('paths', type=str, nargs=-1)
def imEnhance(filters, output:Path, paths):
  """
  Apply filters to images to enhane them
  """
  from . import im_enhancer as ih
  f = { _f.short_name : _f for _f in ih.imfilters }
  im_filter = ih.FilterQueue( f[k] for k in filters.split() )
  from .images import imGenerator
  im_gen = imGenerator(paths)
  def progress(i, j):
    click.echo(f'{100*(i/j):>2.2f}%\r', nl=False)

  output = Path(output)
  output.mkdir(parents=True, exist_ok=True)
  for i, (im, p) in enumerate(zip(im_gen, map(Path, paths))) :
    im_ = im_filter.cb(im)
    im_.save(output / p.name)
    progress(i, len(paths))
  
@main.command(name='py')
@click.argument('dbpath', type=str, nargs=1)
@click.option('--debug', '-g', is_flag=True, help='enable debugger on exception in module')
@click.option('-i', type=Path, multiple=True)
@click.option('-e', is_flag=True, help="Exit immediately")
def py(dbpath, debug, i, e):
  """
  Embed ipython with the table in the namespace
  """
  import sys
  from importlib.machinery import ModuleSpec, SourceFileLoader
  from importlib.util import module_from_spec
  from . import database
  from .database import _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter
  import sqlalchemy as sa
  db = database.DB.fromDB(database.engineFromPath(dbpath))
  user_module = module_from_spec((ModuleSpec('qrc', None)))
  sys.modules['qrc'] = user_module
  ns = user_module.__dict__
  ns |= {'R': R, 'I':I, 'Q': C}
  ns['db'] = db
  ns['engine'] = db.engine
  registery = sa.orm.registry()
  for name, table in db.t.items() :
    t = type(name, (object,), {})
    registery.map_imperatively(t, table)
    ns[name] = t

  user_module.__all__ = list(ns.keys())

  for p in i :
    p = Path(p)
    spec = ModuleSpec(p.stem, SourceFileLoader(p.stem, str(p)))
    m = module_from_spec(spec)
    sys.modules[p.stem] = m
    if debug :
      try :
        spec.loader.exec_module(m)
      except :
        import pdb; pdb.xpm()
    else :
      spec.loader.exec_module(m)
    ns |= m.__dict__
    ns[p.stem] = m


  db_table_list = '\n  '.join(db.t.keys())
  if e :
    return
  
  from IPython import embed
  from traitlets.config import get_config

  c = get_config()
  c.InteractiveShellEmbed.colors = "Neutral"
  c.InteractiveShell.banner2 = f'''Available objects :
Builtin : 
  R : Run table
  I : image table
  Q : QRC table

In this database :
  {db_table_list}

A session 'S' has been created, and sqlalchemy is available with `sa` module.
'''
  c.TerminalInteractiveShell.confirm_exit = False
  c.InteractiveShell.confirm_exit = False
  with db.session() as S :
    ns['S'] = S
    ns['sa'] = sa
    ns['e'] = S.execute
    ns['s'] = S.scalars
    ns['s1'] = S.scalar
    ns['sel'] = sa.select
    ns['count'] = sa.func.count
    embed(config=c, user_module=user_module)
    




if __name__ == "__main__" :
  main()

