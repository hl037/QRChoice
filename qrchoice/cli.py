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
@click.option('--layout', '-y', type=click.Choice(list(layouts.keys()), case_sensitive=False), help='Layout to use. "grid" is the default which arrange as a grid of the largest element size. "brute" tries to find the optimal layout without rotation except 90° ones, but it is slow if many small images. "rectpack" uses the rectpack library, it is fast, similare to "brute", but will unlikely find the optimal solution. Then "pynest" is experimental.')
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
@click.option('--layout', '-y', type=click.Choice(list(layouts.keys()), case_sensitive=False), help='Layout to use. "grid" is the default which arrange as a grid of the largest element size. "brute" tries to find the optimal layout without rotation except 90° ones, but it is slow if many small images. "rectpack" uses the rectpack library, it is fast, similare to "brute", but will unlikely find the optimal solution. Then "pynest" is experimental.')
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

if __name__ == "__main__" :
  main()

