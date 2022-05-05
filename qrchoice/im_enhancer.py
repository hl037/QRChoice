from functools import reduce
import typing as th

import PIL
from PIL import Image, ImageOps, ImageEnhance

imfilters = [] # type: list[ImFilter]

def registerImFilter(C):
  imfilters.append(C())
  return C

class ImFilter(object):
  """
  Image filter
  """
  name = ''
  short_name = None

  def cb(self, im:Image):
    raise NotImplementedError()

  def combine(self, oth):
    return self, oth

class BasicFilter(object):
  """
  Handle an amont variable
  """
  def __init__(self, amount=None):
    if amount :
      self.amount = amount

  def combine(self, oth):
    if isinstance(oth, self.__class__) :
      return [self.__class__(self.amount * oth.amount)]
    else :
      return [self, oth]

class Contrast(BasicFilter):
  """
  Contrast filter
  """

  def cb(self, im:Image):
    en = ImageEnhance.Contrast(im)
    return en.enhance(self.amount)
      

@registerImFilter
class ContrastMore(Contrast):
  """
  Add contrast
  """

  name = 'contrast *= 1.2'
  short_name = 'c+'
  amount = 1.2
  
@registerImFilter
class ContrastLess(Contrast):
  """
  Decrease contrast
  """

  name = 'contrast *= 0.8'
  short_name = 'c-'
  amount = 0.8
  
class Brightness(BasicFilter):
  """
  Brightness filter
  """

  def cb(self, im:Image):
    en = ImageEnhance.Brightness(im)
    return en.enhance(self.amount)
    
@registerImFilter
class BrightnessMore(Brightness):
  """
  Increase brightness
  """

  name = 'brightness *= 1.2'
  short_name = 'b+'
  amount = 1.2
  
@registerImFilter
class BrightnessLess(Brightness):
  """
  Add brightness
  """

  name = 'brightness *= 0.8'
  short_name = 'b-'
  amount = 0.8
  
class Sharpness(BasicFilter):
  """
  Sharpness filter
  """

  def cb(self, im:Image):
    en = ImageEnhance.Sharpness(im)
    return en.enhance(self.amount)
      
  
@registerImFilter
class SharpnessMore(Sharpness):
  """
  Decrease sharpness
  """

  name = 'sharpness *= 1.2'
  short_name = 's+'
  amount = 1.2
  
@registerImFilter
class SharpnessLess(Sharpness):
  """
  Decrease sharpness
  """

  name = 'sharpness *= 0.8'
  short_name = 's-'
  amount = 0.8


class FilterQueue(ImFilter):
  """
  Filter queue
  """
  def __init__(self, filters:th.Sequence[ImFilter]):
    self.filters = list(filters)

  def cb(self, im:Image):
    return self.reduce(self.filters, im)

  @classmethod
  def reduce(cls, filters, im):
    if filters :
      return reduce(lambda x, f: f.cb(x), reduce(lambda a, b: a[:-1] + a[-1].combine(b), filters[1:], [filters[0]]), im)
    else :
      return im
    
    
    
