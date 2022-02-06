from PIL import Image, ImageDraw, ImageFont
import numpy as np
import brutepack
from icecream import ic

dpi = 300

def pasteTransform(dst:Image.Image, src:Image.Image, *args, **kwargs):
  mask = Image.new('L', src.size, 255)
  src_t = src.transform(dst.size, *args, **kwargs)
  mask_t = mask.transform(dst.size, *args, **kwargs)
  dst.paste(src_t, mask_t)


def findAffineCoefs(dst, src):
  A = np.matrix([
      l
    for (x1, y1), (x2, y2) in zip(dst, src)
    for l in (
      [x1, y1, 1, 0, 0, 0, -x2 * x1, -x2 * y1],
      [0, 0, 0, x1, y1, 1, -y2 * x1, -y2 * y1],
    )
  ], dtype=np.float)

  B = np.reshape(src, 8)

  return np.linalg.solve(A, B).reshape(8)

def transformQuad(dst, src, quad_dst, quad_src):
  coefs = findAffineCoefs(quad_dst, quad_src)
  pasteTransform(dst, src, Image.PERSPECTIVE, data=coefs, resample=Image.BICUBIC)

def nestRects_pynest(sizes, page_size):
  try :
    import pynest2d as nest
  except :
    RuntimeError('Please install python-pynest2d https://github.com/Ultimaker/pynest2d (not available on pip) to use this feature')
  w_p, h_p = page_size
  ox = w_p / 2
  oy = h_p / 2
  bin = nest.Box(*page_size)
  items = [
      nest.Item([
        nest.Point(0, 0),
        nest.Point(w, 0),
        nest.Point(w, h),
        nest.Point(0, h),
      ])
    for w, h in sizes
  ]
  bin_count = nest.nest(items, bin)
  return bin_count, [
      (
        binId,
        [ (-it_t.vertex(i).x() + ox, it_t.vertex(i).y() + oy) for i in range(4) ],
      )
    for binId, it_t in ( (it.binId(), it.transformedShape()) for it in items )
  ]
  
def nestRects_rectpack(sizes, page_size):
  from rectpack import newPacker
  packer = newPacker()
  for i, s in enumerate(sizes) :
    packer.add_rect(*s, i)

  #for i in range(len(sizes)) :
  #  packer.add_bin(*page_size)
  packer.add_bin(*page_size)
  
  packer.pack()
  packed = packer.rect_list()
  if len(packed) != len(sizes) :
    raise RuntimeError('An image is bigger than the page size')

  res = [None] * len(sizes)
  for binId, x, y, w, h, rid in packed :
    if (w, h) == sizes[rid] :
      res[rid] = (binId, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    elif (h, w) == sizes[rid] :
      res[rid] = (binId, [(x + w, y), (x + w, y + h), (x, y + h), (x, y)])
  return max( binId for binId, _ in res ) + 1, res

def nestRects_brutepack(sizes, page_size):
  sizes = list(sizes)
  ic(sizes)
  ic(page_size)
  size_dict = {}
  for i, (w, h) in enumerate(sizes) :
    if w < h :
      size_dict.setdefault((h, w), []).append((i, True))
    else :
      size_dict.setdefault((w, h), []).append((i, False))
  ic(size_dict)
  in_sizes = sorted(( ((w, h), len(l)) for (w, h), l in size_dict.items() ), key=lambda el: el[0][0] * el[0][1], reverse=True)
  ic(in_sizes)
  from brutepack import pack
  ic('!!!   BEFORE PACK')
  count, _res, miss = pack(in_sizes, [page_size]*len(sizes))
  ic('!!!   AFTER PACK')
  res = [None] * len(sizes)
  for rid, binId, orient, x, y in _res :
    ic(rid, binId, orient, x, y)
    w, h = in_sizes[rid][0]
    i, swap = l = size_dict[(w, h)].pop()
    if orient :
      w, h = h, w
    ic(w, h, i, swap)
    if swap ^ orient :
      res[i] = (binId, [(x + w, y), (x + w, y + h), (x, y + h), (x, y)])
    else :
      res[i] = (binId, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
  return count, res

def rectAt(x, y, w, h):
  return [
    (x + 0, y + 0),
    (x + w, y + 0),
    (x + w, y + h),
    (x + 0, y + h),
  ]
  
def rectAt_r(x, y, w, h):
  return [
    (x + w, y + 0),
    (x + w, y + h),
    (x + 0, y + h),
    (x + 0, y + 0),
  ]


def nestRects_grid(sizes, page_size):
  sizes = [
      (w, h, False) if w > h else
      (h, w, True)
    for w, h in sizes
  ]
  w_m, h_m = max(w for w, _, _ in sizes), max(h for _, h, _ in sizes)
  w_p, h_p = page_size
  count_x = w_p // w_m, w_p // h_m
  count_y = h_p // h_m, h_p // w_m
  if count_x[0] * count_y[0] < count_x[1] * count_y[1] :
    cx, cy = x_count[1], y_count[1]
    orient = True
  else :
    cx, cy = count_x[0], count_y[0]
    orient = False
  return (
    1 + (len(sizes) - 1) // (cx * cy),
    [
      (
        (i // (cx * cy)),
        (
          rectAt_r( (i % cx) * w_m, ((i // cx) % cy) * h_m, w, h) if swap ^ orient else
          rectAt(   (i % cx) * w_m, ((i // cx) % cy) * h_m, w, h)
        )
      )
      for i, (w, h, swap) in enumerate(sizes)
    ]
  )

layouts = {
  'brute': nestRects_brutepack,
  'grid': nestRects_grid,
  'rectpack': nestRects_rectpack,
  'pynest': nestRects_pynest,
}

def nestRects(sizes, page_size, layout='grid'):
  return layouts[layout](sizes, page_size)
  

def imageToRect(im):
  w, h = im.size
  return [
    (0, 0),
    (w, 0),
    (w, h),
    (0, h),
  ]

def nestImages(images, page_size, margin=(0,0), layout='grid'):
  w_m, h_m = margin
  w_p, h_p = page_size
  page_count, nested = nestRects(( im.size for im in images ), (w_p - 2 * w_m, h_p - 2 * h_m), layout=layout)
  pages = [ Image.new('RGB', page_size, (255,255,255)) for i in range(page_count) ]
  nested = [
      (binId, [ (x + w_m, y + h_m) for x, y in points ])
    for binId, points in nested
  ]
  for im, (binId, points) in zip(images, nested) :
    transformQuad(pages[binId], im, points, imageToRect(im))
  return pages, nested

  
def openImage(path):
  im = Image.open(path) #type: Image.Image
  if 'dpi' in im.info :
    try :
      im_dpi_x, im_dpi_y = im.info['dpi']
    except :
      im_dpi_x = im_dpi_y = im.info['dpi']
    w, h = im.size
    im = im.resize((w * dpi / im_dpi_x, h * dpi / im_dpi_y))
  return im

def openRowImages(self, rows, fmt):
  return [
      openImage(fmt(row))
    for row in rows
  ]

def ensureImageAtLeastSize(im:Image.Image, size):
  w_im, h_im = im.size
  w_s, h_s = size
  if w_s <= w_im and h_s <= h_im :
    return im
  w_im_n = max(w_im, w_s)
  h_im_n = max(h_im, h_s)
  im_n = Image.new(im.mode, (w_im_n, h_im_n), color='white') #type: Image.Image
  im_n.paste(im, (0,0))
  imd = ImageDraw.Draw(im_n)
  color = 'silver'
  if w_im < w_s :
    imd.line([(w_im + 1, 0), (w_im_n, 0), (w_im_n, h_im_n)], fill=color)
  else :
    imd.line([(w_im_n, h_im + 1), (w_im_n, h_im_n)], fill=color)
    
  if h_im < h_s :
    imd.line([(0, h_im + 1), (0, h_s), (w_im_n, h_im_n)], fill=color)
  else :
    imd.line([(w_im + 1, h_im_n), (w_im_n, h_im_n)], fill=color)
  return im_n


def layoutImagesAndQRCodes(images, qrcodes, page_size, margin=(0,0), long_side_turn=True, layout='grid'):
  qrcodes = list(qrcodes)
  images = [
    ensureImageAtLeastSize(im, qrc.size)
    for im, qrc in zip(images, qrcodes)
  ]
  pages, nested = nestImages(images, page_size, layout=layout)
  pages_qr = [ Image.new('L', page_size, 0xFF) for _ in range(len(pages)) ]
  w_p, h_p = page_size
  for qrc, (binId, points) in zip(qrcodes, nested) :
    if long_side_turn :
      points = [ (w_p - x, y) for x, y in points ]
    else :
      points = [ (x, h_p - y) for x, y in points ]
    points = np.array([ points[i] for i in (1, 0, 3, 2) ], dtype=np.float)
    
    w_qrc, h_qrc = qrc.size
    
    dx = points[1] - points[0] #type: np.ndarray
    dy = points[3] - points[0] #type: np.ndarray
    dx *= w_qrc / (np.sqrt(np.sum(dx * dx)))
    dy *= h_qrc / (np.sqrt(np.sum(dy * dy)))

    points[1,:] = points[0] + dx
    points[3,:] = points[0] + dy
    points[2,:] = points[1] + dy
    points = points.tolist()

    transformQuad(pages_qr[binId], qrc, points, imageToRect(qrc))
  res = [
      p
    for p_img, p_qr in zip(pages, pages_qr)
    for p in (p_img, p_qr)
  ]
  for r in res :
    r.info['dpi'] = (300, 300)
  return res

def saveAsPDF(path,  pages:list[Image.Image]):
  pages[0].save(path, format='PDF', save_all=True, append_images=pages[1:])

