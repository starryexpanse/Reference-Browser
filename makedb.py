#!/usr/bin/env python3

from file_finder import FileFinder, FileInfo
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import json
import multiprocessing
import os
import shutil
import sqlite3
import subprocess
import sys

num_cpus = multiprocessing.cpu_count()
NumImagePixels = 238336

class InvalidPathException(Exception):
  pass

class Island(object):
  # name, AKA, Suffix, icon
  info = {
    'A': ['Always Loaded', '', '', 'all_icon.png'],
    'B': ['Boiler', 'Book Assembly', 'Island', 'boiler_icon.png'],
    'G': ['Garden', 'Survey', 'Island', 'garden_icon.png'],
    'J': ['Jungle', '', 'Island', 'jungle_icon.png'],
    'K': ["K'veer", '', 'Age', 'kveer_icon.png'],
    'O': ["Gehn's Office", '233', 'Age', '233_icon.png'],
    'P': ['Prison', '', 'Island', 'prison_icon.png'],
    'R': ['Rebel', 'Tay', 'Island', 'rebel_icon.png'],
    'T': ['Temple', '', 'Island', 'temple_icon.png'],
  }

  def __init__(self, symbol):
    self.id = ord(symbol)
    self.symbol = symbol
    self.name = Island.info[symbol][0]
    self.aka = Island.info[symbol][1]
    self.suffix = Island.info[symbol][2]
    if Island.info[symbol][3]:
      self.icon = 'images/' + Island.info[symbol][3]
    else:
      self.icon = ''

  def sqlrow(self):
    return [self.id, self.symbol, self.name, self.aka, self.suffix, self.icon]

  @staticmethod
  def insert():
    return '(?,?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE islands
             (island_id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT, name TEXT, aka TEXT, suffix TEXT, icon TEXT)''')
    conn.commit()

class Position(object):
  def __init__(self, island_id, pos_id):
    self.pos_id = pos_id
    self.thumbnail = None
    self.island_id = island_id
    self.viewpoint_names = []

  def sqlrow(self):
    return [self.pos_id, self.island_id, self.thumbnail]

  @staticmethod
  def insert():
    return '(?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE positions
              (position_id INTEGER PRIMARY KEY AUTOINCREMENT,
              island INTEGER,
              thumbnail TEXT,
              FOREIGN KEY(island) REFERENCES islands(island_id))''')
    conn.commit()

class Viewpoint(object):
  def __init__(self, id, island_id, position_id, name):
    self.id = id
    self.island_id = island_id
    self.position_id = position_id
    self.name = name
    self.thumbnail = None
    self.thumbnail2x = None

  def sqlrow(self):
    return [self.id, self.island_id, self.position_id, self.name, self.thumbnail,
            self.thumbnail2x]

  @staticmethod
  def insert():
    return '(?,?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE viewpoints
             (viewpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
              island INTEGER,
              position INTEGER,
              name INTEGER,
              thumbnail TEXT,
              thumbnail2x TEXT,
              FOREIGN KEY(island) REFERENCES islands(island_id),
              FOREIGN KEY(position) REFERENCES positions(position_id))''')

    conn.commit()

class RivenImg(object):
  def __init__(self, id, viewpoint_id, filename, friendly, file_path):
    self.id = id
    self.viewpoint_id = viewpoint_id
    self.filename = filename
    self.friendly = friendly
    self.file_path = file_path

  def sqlrow(self):
    return [self.id, self.viewpoint_id, self.filename, self.friendly,
            self.file_path]

  @staticmethod
  def insert():
    return '(?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE rivenimgs
             (image_id INTEGER PRIMARY KEY AUTOINCREMENT,
              viewpoint INTEGER,
              filename TEXT,
              friendly TEXT,
              file_path TEXT,
              FOREIGN KEY(viewpoint) REFERENCES viewpoints(viewpoint_id))''')
    conn.commit()

class RivenMovie(object):
  def __init__(self, id, viewpoint_id, filename, friendly, file_path, gif_path,
               h264_path):
    self.id = id
    self.viewpoint_id = viewpoint_id
    self.filename = filename
    self.friendly = friendly
    self.file_path = file_path
    self.anim_gif_path = gif_path
    self.h264_path = h264_path

  def sqlrow(self):
    return [self.id, self.viewpoint_id, self.filename, self.friendly,
            self.file_path, self.anim_gif_path, self.h264_path]

  @staticmethod
  def insert():
    return '(?,?,?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE rivenmovs
             (movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
              viewpoint INTEGER,
              filename TEXT,
              friendly TEXT,
              file_path TEXT,
              anim_gif_path TEXT,
              h264_path TEXT,
              FOREIGN KEY(viewpoint) REFERENCES viewpoints(viewpoint_id))''')
    conn.commit()

class Loader(object):
  protected_dir = 'protected'

  def __init__(self, top_dir):
    self.top_dir = top_dir
    self.db_path = 'riven.sqlite'

  @staticmethod
  def ProtectPath(path):
    """Add the protected directory as the parent.

    >>> Loader.ProtectPath(os.path.join('foo', 'bar.txt'))
    'protected/foo/bar.txt'
    """
    if Loader.protected_dir in path:
      raise InvalidPathException()
    return os.path.join(Loader.protected_dir, path)

  @staticmethod
  def UnprotectPath(path):
    """Strip the protected parent directory from the path.

    >>> Loader.UnprotectPath(os.path.join(Loader.protected_dir, 'foo', 'bar.txt'))
    'foo/bar.txt'
    """
    if not Loader.protected_dir in path:
      raise InvalidPathException()
    return path.replace(Loader.protected_dir + '/', '')

  def CreateTables(self, conn):

    c = conn.cursor()
    c.execute('''CREATE TABLE users
              (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT, name TEXT)''')
    conn.commit()

    Island.CreateTable(conn)
    Position.CreateTable(conn)
    Viewpoint.CreateTable(conn)
    RivenImg.CreateTable(conn)
    RivenMovie.CreateTable(conn)

    conn.commit()

  @staticmethod
  def LoadPositions(fname):
    pos_id = 1
    positions = dict()
    island_symbol = None
    with open('positions.txt') as f:
      for line in f.readlines():
        if not line or line[0] == '#':
          continue
        line = line.strip()
        if not len(line) > 1:
          continue
        if line[1] == ':':
          island_symbol = line[0]
        else:
          assert(island_symbol)
          position = Position(ord(island_symbol), pos_id)
          pos_id += 1
          position.viewpoint_names = [vpt for vpt in line.split()]
          if island_symbol not in positions:
            positions[island_symbol] = []
          positions[island_symbol].append(position)
    return positions

  @staticmethod
  def SwapExtension(fname, newextn):
    """Swap a file extension.

    >>> Loader.SwapExtension('foo/bar.txt', 'png')
    'foo/bar.png'
    """
    bname, oldext = os.path.splitext(fname)
    return '%s.%s' % (bname, newextn)

  @staticmethod
  def TranscodeMovie(mov, outpath):
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', mov, outpath]
    print(' '.join(cmd))
    subprocess.check_call(cmd)

  @staticmethod
  def MakeH264(mov, outpath):
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', mov, '-an', '-b', '200k',
            '-bt', '240k', '-vcodec', 'libx264', '-crf', '23', outpath]
    print(' '.join(cmd))
    subprocess.check_call(cmd)

  def CreateUsers(self, conn):
    c = conn.cursor()
    users = []
    users = [[1, 'admin', 'Administrator']]
    c.executemany('INSERT INTO users VALUES (?,?,?)', users)
    conn.commit()

  @staticmethod
  def GetMovieSize(movie):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height',
           '-of', 'default=noprint_wrappers=1', movie]
    width = None
    height = None
    output = subprocess.check_output(cmd)
    for line in output.splitlines():
      items = line.decode("utf-8").split('=')
      if items[0] == 'width':
        width = int(items[1])
      elif items[0] == 'height':
        height = int(items[1])
    return(width, height)

  @staticmethod
  def GetMovieThumbnailSource(movies):
    biggest_movie = None
    biggest_movie_size = 0
    for movie in movies:
      (width, height) = Loader.GetMovieSize(movie.file_path)
      num_pixels = width * height
      if num_pixels > biggest_movie_size:
        biggest_movie_size = num_pixels
        biggest_movie = movie
    return biggest_movie.file_path

  @staticmethod
  def ExtractMovieImage(moviefile, outfile):
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', moviefile, '-ss',
           '00:00:01.000', '-vframes', '1', outfile]
    subprocess.check_call(cmd)

  @staticmethod
  def GetImageThumbnailSource(images):
    for image in images:
      filename = Loader.ProtectPath(image.file_path)
      with Image.open(filename) as im:
        width, height = im.size
        num_pixels = width * height
        if num_pixels == NumImagePixels:
          return filename
    return None

  @staticmethod
  def ScaleImage(infile, outfile, scale_factor):
    print('%s -> %s' % (infile, outfile))
    with Image.open(infile) as im:
      width, height = im.size
      thumb = im.resize((int(width*scale_factor), int(height*scale_factor)),
                        Image.BICUBIC)
      thumb.save(outfile)

  @staticmethod
  def CreateMovieThumbnail(moviefile, outfile, scale_factor):
    if os.path.exists(outfile):
      return
    large_size = outfile + 'thumbnail-large.png'
    Loader.ExtractMovieImage(moviefile, large_size)
    Loader.ScaleImage(large_size, outfile, scale_factor)
    os.remove(large_size)

  @staticmethod
  def CreateAnimatedGif(image_list, outfile):
    if os.path.exists(outfile):
      return
    cmd = ['convert', '-delay', '80', '-loop', '0']
    cmd.extend(image_list)
    cmd.append(outfile)
    print(' '.join(cmd))
    subprocess.check_call(cmd)

  @staticmethod
  def CreatePositionImageThumbnail(position, viewpoints, executor):
    futures = []

    anim_images = []
    for viewpoint in viewpoints:
      if position.island_id == viewpoint.island_id and \
         viewpoint.name in position.viewpoint_names:
        anim_images.append(Loader.ProtectPath(viewpoint.thumbnail))

    if not len(anim_images):
      return futures

    if len(anim_images) == 1:
      outfile = anim_images[0]
    else:
      outfile = os.path.join(os.path.dirname(anim_images[0]),
          'position_%d_thumbnail.gif' % position.pos_id)
      futures.append(executor.submit(Loader.CreateAnimatedGif,
                                     anim_images, outfile))
    position.thumbnail = Loader.UnprotectPath(outfile)
    return futures

  @staticmethod
  def CreateAllPositionImageThumbnails(positions, viewpoints, executor):
    futures = []
    for position in positions:
      futures.append(executor.submit(Loader.CreatePositionImageThumbnail,
                                     position,
                                     viewpoints,
                                     executor))
    return futures

  @staticmethod
  def CreateViewpointImageThumbnails(viewpoint, thumbnail_src, executor):
    futures = []

    # Standard resolution
    fname = '%s_thumbnail.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    if not os.path.exists(outfile):
      futures.append(executor.submit(Loader.ScaleImage,
                                     thumbnail_src, outfile, 0.18))
    viewpoint.thumbnail = Loader.UnprotectPath(outfile)
    # Retina resolution
    fname = '%s_thumbnail2x.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    if not os.path.exists(outfile):
      futures.append(executor.submit(Loader.ScaleImage,
                                     thumbnail_src, outfile, 0.36))
    viewpoint.thumbnail2x = Loader.UnprotectPath(outfile)

    return futures

  @staticmethod
  def CreateViewpointMovieThumbnails(viewpoint, thumbnail_src, executor):
    futures = []

    # Standard resolution
    fname = '%s_thumbnail.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    futures.append(executor.submit(Loader.CreateMovieThumbnail,
                                   thumbnail_src, outfile, 0.18))
    viewpoint.thumbnail = Loader.UnprotectPath(outfile)
    # Retina resolution
    fname = '%s_thumbnail2x.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    futures.append(executor.submit(Loader.CreateMovieThumbnail,
                                   thumbnail_src, outfile, 0.36))
    viewpoint.thumbnail2x = Loader.UnprotectPath(outfile)

    return futures

  @staticmethod
  def CreateViewpointThumbnails(viewpoints, images, movies):
    view2img = dict()
    for image in images:
      if image.viewpoint_id not in view2img:
        view2img[image.viewpoint_id] = []
      view2img[image.viewpoint_id].append(image)

    view2mov = dict()
    for movie in movies:
      if movie.viewpoint_id not in view2mov:
        view2mov[movie.viewpoint_id] = []
      view2mov[movie.viewpoint_id].append(movie)

    executor = ThreadPoolExecutor(max_workers=num_cpus)
    futures = []
    for viewpoint in viewpoints:
      if viewpoint.id in view2img:
        thumbnail_src = Loader.GetImageThumbnailSource(view2img[viewpoint.id])
        if not thumbnail_src:
          continue
        futures.extend(Loader.CreateViewpointImageThumbnails(viewpoint,
                                                             thumbnail_src,
                                                             executor))
      elif viewpoint.id in view2mov:
        thumbnail_src = Loader.GetMovieThumbnailSource(view2mov[viewpoint.id])
        if not thumbnail_src:
          continue

        futures.extend(Loader.CreateViewpointMovieThumbnails(viewpoint,
                                                             thumbnail_src,
                                                             executor))
    if (len(futures)):
      print('Waiting for file viewpoint thumbnail generation to finish...')
      for f in futures:
        f.result()

  @staticmethod
  def FindPositionID(positions, viewpoint_name):
    if not positions:
      return None
    for position in positions:
      if viewpoint_name in position.viewpoint_names:
        return position.pos_id
    return None

  def LoadData(self, conn):
    island_to_imgvpt = self.LoadFiles('png')
    island_to_movvpt = self.LoadFiles('mov')
    c = conn.cursor()

    islands = []
    for island_symbol in island_to_imgvpt.keys():
      islands.append(Island(island_symbol).sqlrow())
    c.executemany('INSERT INTO islands VALUES %s' % Island.insert(), islands)

    island_to_posns = Loader.LoadPositions('positions.txt')

    viewpoints = []
    vpt_id = 1
    images = []
    movies = []
    img_id = 1
    island_vpt_to_vpt_id = dict()
    for island_symbol in island_to_imgvpt.keys():
      island_posns = None
      if island_symbol in island_to_posns:
        island_posns = island_to_posns[island_symbol]
      for vpt in island_to_imgvpt[island_symbol]:
        pos_id = Loader.FindPositionID(island_posns, vpt)
        viewpoints.append(Viewpoint(vpt_id, ord(island_symbol), pos_id, vpt))
        viewpoint_to_info = island_to_imgvpt[island_symbol]
        for info in viewpoint_to_info[vpt]:
          island_vpt_to_vpt_id[(island_symbol, vpt)] = vpt_id
          file_path = Loader.UnprotectPath(info.file_path)
          images.append(RivenImg(img_id, vpt_id, info.filename(),
                        info.friendly_name(), file_path))
          img_id += 1
        vpt_id += 1
    mov_id = 1
    executor = ThreadPoolExecutor(max_workers=num_cpus)
    futures = []
    all_positions = []
    for island_symbol in island_to_movvpt.keys():
      island_posns = None
      if island_symbol in island_to_posns:
        island_posns = island_to_posns[island_symbol]
        all_positions.extend(island_posns)
      for vpt in island_to_movvpt[island_symbol]:
        pos_id = Loader.FindPositionID(island_posns, vpt)
        viewpoint_to_info = island_to_movvpt[island_symbol]
        for info in viewpoint_to_info[vpt]:
          gif_path = Loader.SwapExtension(info.file_path, 'gif')
          if not os.path.exists(gif_path):
            futures.append(executor.submit(Loader.TranscodeMovie,
                                           info.file_path, gif_path))
          h264_path = Loader.SwapExtension(info.file_path, 'm4v')
          if not os.path.exists(h264_path):
            futures.append(executor.submit(Loader.MakeH264,
                                           info.file_path, h264_path))
          key = (island_symbol, vpt)
          if not key in island_vpt_to_vpt_id:
            # If not present, then there was not an image here, the movie is the
            # first file.
            viewpoints.append(Viewpoint(vpt_id, ord(island_symbol), pos_id, vpt))
            island_vpt_to_vpt_id[(island_symbol, vpt)] = vpt_id
            vpt_id += 1
          mov_vpt_id = island_vpt_to_vpt_id[key]
          gif_path = Loader.UnprotectPath(gif_path);
          h264_path = Loader.UnprotectPath(h264_path);
          movies.append(RivenMovie(mov_id, mov_vpt_id, info.filename(),
                         info.friendly_name(),
                         info.file_path, gif_path, h264_path))
          mov_id += 1
    Loader.CreateViewpointThumbnails(viewpoints, images, movies)
    futures.extend(Loader.CreateAllPositionImageThumbnails(all_positions,
                                                           viewpoints,
                                                           executor))
    if (len(futures)):
      print('Waiting for file transcoding to finish...')
      for f in futures:
        f.result()
    c.executemany('INSERT INTO viewpoints VALUES %s' % Viewpoint.insert(),
                  [v.sqlrow() for v in viewpoints])
    c.executemany('INSERT INTO positions VALUES %s' % Position.insert(),
                  [p.sqlrow() for p in all_positions])
    c.executemany('INSERT INTO rivenimgs VALUES %s' % RivenImg.insert(),
                  [i.sqlrow() for i in images])
    c.executemany('INSERT INTO rivenmovs VALUES %s' % RivenMovie.insert(),
                  [m.sqlrow() for m in movies])
    conn.commit()


  def CreateDB(self):
    try:
      os.remove(self.db_path)
    except FileNotFoundError:
      pass
    conn = sqlite3.connect(self.db_path)
    self.CreateTables(conn)
    self.CreateUsers(conn)
    self.LoadData(conn)
    conn.close()

  @staticmethod
  def FilterImage(info):
    if info.friendly_name() == 'black':
      return True
    return False

  def LoadFiles(self, suffix):
    island_to_vpt = dict()
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
      if Loader.FilterImage(info):
        continue
      if info.island in island_to_vpt:
        vpts = island_to_vpt[info.island]
      else:
        vpts = dict()
        island_to_vpt[info.island] = vpts
      if not info.viewpoint in vpts:
        vpts[info.viewpoint] = set()
      vpts[info.viewpoint].add(info)
    return island_to_vpt

  @staticmethod
  def ExtractGameImagesForWebsite():
    with open('extraction_data.json') as data_file:
      data = json.load(data_file)
      for image in data:
        d = os.path.dirname(image['outfile'])
        if not os.path.exists(d):
          os.mkdir(d)
        Loader.ScaleImage(image['infile'], image['outfile'], image['scale'])

if __name__ == '__main__':
  import doctest
  doctest.testmod()
  Loader.ExtractGameImagesForWebsite()
  loader = Loader(Loader.ProtectPath('DVD'))
  loader.CreateDB()
