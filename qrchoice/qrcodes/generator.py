from math import ceil
import re
from PIL import Image, ImageDraw, ImageFont
import qrcode

from ..database import DB


def qrcodeGenerator(db:DB, table):
  pk = db.getPK(table)
  return ( (row, qrcode.make(f'{table}:{",".join( str(row[c]) for c in pk )}')) for row in db.getObjects(table) )

  
class RowFormatter(object):
  """
  Format a row according to a pattern
  """
  variable_re = re.compile(r'%\{([^)]+?)\}')
  def __init__(self, pattern):
    self._parts = []
    i = 0
    while (m := RowFormatter.variable_re.search(pattern, i)) is not None :
      j = m.start()
      if i != j :
        self._parts.append((0, pattern[i:j]))
      self._parts.append((1, m[1]))
      i = m.end()
    if i < len(pattern) :
      self._parts.append((0, pattern[i:]))

  def __call__(self, row):
    return ''.join( (v if t == 0 else str(row[v])) for t, v in self._parts )

font = ImageFont.truetype('DejaVuSans', 25)

def fontBaseHeight(font):
  _, h = font.getsize('A')
  return h

def addText(qrc_im:Image.Image, t):
  wq, hq = qrc_im.size
  a, d = font.getmetrics()
  spacing = (.4) * fontBaseHeight(font)
  
  wt, ht = font.getsize_multiline(t, spacing=spacing)
  im_res = Image.new('L', (wq, hq + int(ceil(ht))), 0xFF)
  im_res.paste(qrc_im, (0, int(ceil(ht))))
  imd = ImageDraw.Draw(im_res)
  imd.multiline_text((wq / 2, a), t, fill=0, font=font, anchor='ms', spacing=spacing, align="center")
  return im_res

  
