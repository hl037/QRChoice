from PIL import Image

def imGenerator(paths):
  """
  This image generator closes the file after each read
  """
  for p in paths :
    with Image.open(p) as im :
      yield im
    
  
