from pathlib import Path
import click
from functools import wraps

from . import config as C


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
@click.option('--config', '-c', type=str)
@click.argument('dbpath')
@dbg_wrap
def create_db(config, dbpath):
  from . import database
  
  dbp = Path(dbpath)
  if dbp.exists() :
    click.confirm('The database already exists, and will be overwritten, are you sure to continue?', abort=True)
    dbp.unlink()
  with open(config, 'r') as f :
    cwd = Path(config)
    conf = C.parse(cwd, f)
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
  from .qrcodes import generator as qr_gen
  
  db = database.DB.fromDB(database.engineFromPath(dbpath))
  for t, text, dest in output :
    fmt_text = qr_gen.RowFormatter(text)
    fmt_dest = qr_gen.RowFormatter(dest)
    for r, im in qr_gen.qrcodeGenerator(db, t) :
      p = Path(fmt_dest(r))
      p.parent.mkdir(parents=True, exist_ok=True)
      im_t = qr_gen.addText(im, fmt_text(r))
      im_t.save(p)


if __name__ == "__main__" :
  main()

