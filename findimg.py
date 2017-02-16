#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from file_finder import FileFinder, FileInfo
import argparse
import multiprocessing
import os
import subprocess
import sys
import tempfile
import threading

StandardImageSize = (608, 392)
num_cpus = max(1, multiprocessing.cpu_count())
stdout_lock = threading.Lock()

class InvalidOutputException(Exception):
  pass

class Options(object):
  def __init__(self):
    self.island_symbol = None
    self.image = None

  def Parse(self):
    desc = "Find the best matching game image to the one specified."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-i', '--island',
                        help='Only look for image in the specified island.')
    parser.add_argument('image', metavar='IMAGE', type=str,
                        help="The input image to find the best match to")
    args = parser.parse_args()
    self.image = args.image
    if args.island:
      self.island_symbol = args.island.upper()

class ImageMatcher(object):
  def __init__(self, top_dir, island_symbol):
    self.top_dir = top_dir
    self.island_symbol = island_symbol

  @staticmethod
  def Compare(img, exemplar):
    """Compare |img| to |exemplar| and return a tuple of (RMSE, img)."""

    cmd = ['compare', '-metric', 'RMSE', '-fuzz', '3%', img, exemplar, 'null']
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    out = p.communicate()
    for line in iter(out):
      if not line:
        continue
      line = line.decode("utf-8")
      items = line.split()
      try:
        rmse = float(items[0])
        return (rmse, exemplar)
      except ValueError as e:
        with stdout_lock:
          print('XXXXXXX Got error')
          print(line)
    raise InvalidOutputException()

  @staticmethod
  def TrimScreenshot(inname, outname):
    """Trims the margin of a screenshot.

    This includes the window border, and black margin.

    to disable the screenshot shadow.
    http://apple.stackexchange.com/questions/50860/how-do-i-take-a-screenshot-without-the-shadow-behind-it
    defaults write com.apple.screencapture disable-shadow -bool TRUE

    Numbers currently hard-coded for macOS with retina screen."""
    crop = {'left': 144, 'width': 1216, 'top': 184, 'height': 784}
    with Image.open(inname) as im:
      cropped = im.crop((crop['left'], crop['top'],
                         crop['left'] + crop['width'],
                         crop['top'] + crop['height']))
      scaledimg = cropped.resize(StandardImageSize, Image.BICUBIC)
      scaledimg.save(outname)

  def FilterImage(self, info):
    if self.island_symbol and self.island_symbol != info.island:
      return True
    if info.friendly_name() == 'black':
      return True
    with Image.open(info.file_path) as im:
      return im.size != StandardImageSize

  def LoadFiles(self, suffix):
    images = []
    finder = FileFinder()
    for filename in finder.GetFiles(self.top_dir, suffix):
      # Thumbnails are created by this program.
      if 'thumbnail' in filename:
        continue
      dir_name = os.path.basename(os.path.dirname(filename))
      if dir_name == 'b2_data-MHK' or dir_name == 'Extras-MHK':
        continue
      info = finder.ParseFilename(os.path.basename(filename))
      info.file_path = filename
      if self.FilterImage(info):
        continue
      images.append(info)
    return images

  def FindMatches(self, fname):
    executor = ThreadPoolExecutor(max_workers=num_cpus)
    futures = []
    count = 0
    for image in self.LoadFiles('png'):
      count += 1
      if count >= 10000:
        break
      futures.append(executor.submit(ImageMatcher.Compare,
                                     fname, image.file_path))
    results = []
    for f in futures:
      results.append(f.result())
      with stdout_lock:
        print('Analyzing image %d/%d (%.1f%%)' %
            (len(results),
             len(futures),
             (len(results) * 100 / len(futures))), end='\r')
    print()
    results.sort(key=lambda result: result[0])
    print('Top five maches')
    for result in results[:5]:
      print('%f: %s' % result)
    print('Examined %d images using %d cores' % (count, num_cpus))

if __name__ == '__main__':
  options = Options()
  options.Parse()
  tmp_name = 'Trimmed.png'
  try:
    os.unlink(tmp_name)
  except:
    pass
  ImageMatcher.TrimScreenshot(options.image, tmp_name)
  matcher = ImageMatcher(os.path.join('browser', 'protected', 'DVD'),
                         options.island_symbol)
  matcher.FindMatches(tmp_name)
  try:
    os.unlink(tmp_name)
  except:
    pass
