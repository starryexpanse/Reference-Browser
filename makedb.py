#!/usr/bin/env python3

from file_finder import FileFinder, FileInfo
from concurrent.futures import ThreadPoolExecutor
from graphviz import Digraph
from PIL import Image
import json5
import multiprocessing
import os
import shutil
import sqlite3
import subprocess
import sys

num_cpus = multiprocessing.cpu_count()
NumImagePixels = 238336
StandardImageSize = [608, 392]

class InvalidPathException(Exception):
  pass

class InvalidReferenceException(Exception):
  pass

class Globals(object):
  def __init__(self):
    self.global_id = 1
    self.thumbnail_size = [int(v * Loader.thumbnail_sf) for v in
                           StandardImageSize]
    self.thumbnail2x_size = [int(v * Loader.thumbnail2x_sf) for v in
                             StandardImageSize]

  def sqlrow(self):
    row = [self.global_id]
    row.extend(self.thumbnail_size)
    row.extend(self.thumbnail2x_size)
    return row

  @staticmethod
  def insert():
    return '(?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE globals
              (global_id INTEGER PRIMARY KEY AUTOINCREMENT,
              thumbnail_width INTEGER,
              thumbnail_height INTEGER,
              thumbnail2x_width INTEGER,
              thumbnail2x_height INTEGER)''')
    conn.commit()

class Map(object):
  def __init__(self):
    self.islands = dict()

  def WriteGraphViz(self, fname):
    with open(fname, 'w') as f:
      dot = Digraph(comment='Riven', node_attr={'margin': '0.0'})
      dot.engine = 'fdp'
      for island_symbol in self.islands:
        self.islands[island_symbol].AddGraphVizData(dot)
      f.write(dot.source)
      dot.render(fname)

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
    self.positions = dict()  # Position.name -> Position
    self.viewpoints = dict() # Viewpoint.name -> Viewpoint

  def GetViewpoint(self, viewpoint_name):
    """Get (or create) a Viewpoint"""
    if viewpoint_name in self.viewpoints:
      return self.viewpoints[viewpoint_name]
    viewpoint = Viewpoint(viewpoint_name, self)
    self.viewpoints[viewpoint.name] = viewpoint
    return viewpoint

  def FindPosition(self, viewpoint_name):
    if viewpoint_name in self.viewpoints:
      return self.viewpoints[viewpoint_name]
    else:
      return None

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

  @property
  def graphviz_name(self):
    return 'I%d' % self.id

  @property
  def graphviz_title(self):
    return self.name

  def AddGraphVizData(self, map_graph):
    island_graph = Digraph(name=self.graphviz_name)
    for position_name in self.positions:
      self.positions[position_name].AddGraphVizData(island_graph)
    map_graph.subgraph(island_graph)

class Position(object):
  next_id = 1

  def __init__(self, name, island):
    self.id = Position.next_id
    Position.next_id += 1
    self.name = name
    self.thumbnail = None
    self.island = island
    self.viewpoints = dict() # Viewpoint.name => viewpoint

  def sqlrow(self):
    return [self.id, self.name, self.island.id, self.thumbnail]

  @staticmethod
  def insert():
    return '(?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE positions
              (position_id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              island INTEGER,
              thumbnail TEXT,
              FOREIGN KEY(island) REFERENCES islands(island_id))''')
    conn.commit()

  @property
  def graphviz_name(self):
    return 'P%d' % self.id

  @property
  def graphviz_title(self):
    return 'P%s' % self.name

  def AddGraphVizData(self, island_graph):
    position_graph = Digraph(name=self.graphviz_name)
    for viewpoint_name in self.viewpoints:
      self.viewpoints[viewpoint_name].AddGraphVizData(position_graph)
    island_graph.subgraph(position_graph)

class Object(object):
  next_id = 1

  def __init__(self, name, title):
    self.id = Object.next_id
    Object.next_id += 1
    self.name = name
    self.title = title
    self.thumbnail = 'missing.png'
    self.thumbnail2x = 'missing.png'
    self.images = []
    self.movies = []

  def sqlrow(self):
    return [self.id, self.name, self.title, self.thumbnail, self.thumbnail2x]

  @staticmethod
  def insert():
    return '(?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE objects
              (object_id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              title TEXT,
              thumbnail TEXT,
              thumbnail2x TEXT)''')
    conn.commit()

class ObjectImageAssocation(object):
  def __init__(self, obj, img):
    self.obj = obj
    self.img = img

  def sqlrow(self):
    return [self.obj.id, self.img.id]

  @staticmethod
  def insert():
    return '(?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE object_images
              (object INTEGER,
              image INTEGER,
              FOREIGN KEY(object) REFERENCES objects(object_id),
              FOREIGN KEY(image) REFERENCES rivenimgs(image_id))''')
    conn.commit()

  @staticmethod
  def InsertAll(cursor, items):
    cursor.executemany('INSERT INTO object_images VALUES %s' % \
        ObjectImageAssocation.insert(),
        [i.sqlrow() for i in items])

class ObjectMovieAssocation(object):
  def __init__(self, obj, movie):
    self.obj = obj
    self.movie = movie

  def sqlrow(self):
    return [self.obj.id, self.movie.id]

  @staticmethod
  def insert():
    return '(?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE object_movies
              (object INTEGER,
              movie INTEGER,
              FOREIGN KEY(object) REFERENCES objects(object_id),
              FOREIGN KEY(movie) REFERENCES rivenmovs(movie_id))''')
    conn.commit()

  @staticmethod
  def InsertAll(cursor, items):
    cursor.executemany('INSERT INTO object_movies VALUES %s' % \
        ObjectMovieAssocation.insert(),
        [i.sqlrow() for i in items])

class Viewpoint(object):
  next_id = 1

  def __init__(self, name, island):
    self.id = Viewpoint.next_id
    Viewpoint.next_id += 1
    self.name = name
    self.island = island
    self.position = None
    self.left_viewpoint = None
    self.right_viewpoint = None
    self.up_viewpoint = None
    self.down_viewpoint = None
    self.forward_viewpoint = None
    self.backward_viewpoint = None
    self.thumbnail = None
    self.thumbnail2x = None

  def sqlrow(self):
    pos_id = self.position.id if self.position else None
    left_vpt_id = self.left_viewpoint.id if self.left_viewpoint else None
    right_vpt_id = self.right_viewpoint.id if self.right_viewpoint else None
    up_vpt_id = self.up_viewpoint.id if self.up_viewpoint else None
    down_vpt_id = self.down_viewpoint.id if self.down_viewpoint else None
    forward_vpt_id = self.forward_viewpoint.id if self.forward_viewpoint else None
    backward_vpt_id = self.backward_viewpoint.id if self.backward_viewpoint else None
    return [self.id, self.island.id, pos_id, self.name,
            self.thumbnail, self.thumbnail2x, left_vpt_id, right_vpt_id,
            up_vpt_id, down_vpt_id, forward_vpt_id, backward_vpt_id]

  @staticmethod
  def insert():
    return '(?,?,?,?,?,?,?,?,?,?,?,?)'

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
              left_viewpoint INTEGER,
              right_viewpoint INTEGER,
              up_viewpoint INTEGER,
              down_viewpoint INTEGER,
              forward_viewpoint INTEGER,
              backward_viewpoint INTEGER,
              FOREIGN KEY(island) REFERENCES islands(island_id),
              FOREIGN KEY(left_viewpoint) REFERENCES viewpoints(viewpoint_id),
              FOREIGN KEY(right_viewpoint) REFERENCES viewpoints(viewpoint_id),
              FOREIGN KEY(up_viewpoint) REFERENCES viewpoints(viewpoint_id),
              FOREIGN KEY(down_viewpoint) REFERENCES viewpoints(viewpoint_id),
              FOREIGN KEY(forward_viewpoint) REFERENCES viewpoints(viewpoint_id),
              FOREIGN KEY(backward_viewpoint) REFERENCES viewpoints(viewpoint_id),
              FOREIGN KEY(position) REFERENCES positions(position_id))''')

    conn.commit()

  @property
  def graphviz_name(self):
    return 'V%d' % self.id

  @property
  def graphviz_title(self):
    return 'V%s' % self.name

  def AddGraphVizData(self, position_graph):
    position_graph.node(name=self.graphviz_name, title=self.graphviz_title,
                        shape='rect',
                        image=Loader.ProtectPath(self.thumbnail2x))
    if self.left_viewpoint:
      position_graph.edge(self.graphviz_name, self.left_viewpoint.graphviz_name, 'L')
    if self.right_viewpoint:
      position_graph.edge(self.graphviz_name, self.right_viewpoint.graphviz_name, 'R')
    if self.up_viewpoint:
      position_graph.edge(self.graphviz_name, self.up_viewpoint.graphviz_name, 'U')
    if self.down_viewpoint:
      position_graph.edge(self.graphviz_name, self.down_viewpoint.graphviz_name, 'D')
    if self.forward_viewpoint:
      position_graph.edge(self.graphviz_name, self.forward_viewpoint.graphviz_name, 'F')
    if self.backward_viewpoint:
      position_graph.edge(self.graphviz_name, self.backward_viewpoint.graphviz_name, 'B')

class RivenImg(object):
  next_id = 1

  def __init__(self, viewpoint, filename, friendly, file_path, image_width,
               image_height):
    self.id = RivenImg.next_id
    RivenImg.next_id += 1
    self.viewpoint = viewpoint
    self.filename = filename
    self.friendly = friendly
    self.file_path = file_path
    self.image_width = image_width
    self.image_height = image_height

  def IsFullSize(self):
    return self.image_width == StandardImageSize[0] and \
           self.image_height == StandardImageSize[1]

  def sqlrow(self):
    return [self.id, self.viewpoint.id, self.filename, self.friendly,
            self.file_path, self.image_width, self.image_height]

  @staticmethod
  def insert():
    return '(?,?,?,?,?,?,?)'

  @staticmethod
  def CreateTable(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE rivenimgs
             (image_id INTEGER PRIMARY KEY AUTOINCREMENT,
              viewpoint INTEGER,
              filename TEXT,
              friendly TEXT,
              file_path TEXT,
              image_width INTEGER,
              image_height INTEGER,
              FOREIGN KEY(viewpoint) REFERENCES viewpoints(viewpoint_id))''')
    conn.commit()

class RivenMovie(object):
  next_id = 1

  def __init__(self, viewpoint, filename, friendly, file_path, gif_path,
               h264_path, movie_width, movie_height):
    self.id = RivenMovie.next_id
    RivenMovie.next_id += 1
    self.viewpoint = viewpoint
    self.filename = filename
    self.friendly = friendly
    self.file_path = file_path
    self.anim_gif_path = gif_path
    self.h264_path = h264_path
    self.movie_width = movie_width
    self.movie_height = movie_height

  def sqlrow(self):
    return [self.id, self.viewpoint.id, self.filename, self.friendly,
            self.file_path, self.anim_gif_path, self.h264_path,
            self.movie_width, self.movie_height]

  @staticmethod
  def insert():
    return '(?,?,?,?,?,?,?,?,?)'

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
              movie_width INTEGER,
              movie_height INTEGER,
              FOREIGN KEY(viewpoint) REFERENCES viewpoints(viewpoint_id))''')
    conn.commit()

class Loader(object):
  protected_dir = os.path.join('browser', 'protected')
  thumbnail_sf = 0.18
  thumbnail2x_sf = thumbnail_sf * 2

  def __init__(self, top_dir):
    self.top_dir = top_dir
    self.db_path = 'riven.sqlite'

  @staticmethod
  def ProtectPath(path):
    """Add the protected directory as the parent.

    >>> Loader.ProtectPath(os.path.join('foo', 'bar.txt'))
    'browser/protected/foo/bar.txt'
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

    Globals.CreateTable(conn)
    Island.CreateTable(conn)
    Position.CreateTable(conn)
    Viewpoint.CreateTable(conn)
    RivenImg.CreateTable(conn)
    RivenMovie.CreateTable(conn)
    Object.CreateTable(conn)
    ObjectImageAssocation.CreateTable(conn)
    ObjectMovieAssocation.CreateTable(conn)

    g = Globals()
    c.executemany('INSERT INTO globals VALUES %s' % Globals.insert(),
                  [g.sqlrow()])

    conn.commit()

  @staticmethod
  def ParseIslandViewpoint(current_island, viewpoint_name):
    items = viewpoint_name.split(',')
    if len(items) > 1:
      print("WARN: Don't currently support multiple forward links")
      viewpoint_name = items[0]
    items = viewpoint_name.split('/')
    if len(items) == 2:
      return (items[0], items[1])
    else:
      return (current_island, viewpoint_name)

  @staticmethod
  def LoadMap(fname):
    """Load the Riven node map from the given file."""
    riven_map = Map()
    pos_count = 0
    vpt_count = 0
    viewpoint_references = [] # (Viewpoint, island_symbol, pos, viewpoint_name)
    with open(os.path.join(fname)) as data_file:
      json_islands = json5.load(data_file)
      for json_island in json_islands:
        island_symbol = json_island['symbol']
        island = Island(island_symbol)
        riven_map.islands[island_symbol] = island
        for json_position in json_island['positions']:
          pos_count += 1
          position = Position(json_position['name'], island)
          for json_viewpoint in json_position['viewpoints']:
            viewpoint = island.GetViewpoint(json_viewpoint['name'])
            viewpoint.position = position
            vpt_count += 1
            position.viewpoints[viewpoint.name] = viewpoint
            for pos_name in ['left', 'right', 'up', 'down', 'forward', 'backward']:
              if pos_name in json_viewpoint:
                (isle_sym, vpt_name) = \
                   Loader.ParseIslandViewpoint(island_symbol,
                                               json_viewpoint[pos_name])
                viewpoint_references.append((viewpoint, isle_sym, pos_name,
                                             vpt_name))
          island.positions[position.name] = position
      # Now connect the viewpoints.
      for vpt, island_symbol, pos, vpt_name in viewpoint_references:
        island = riven_map.islands[island_symbol]
        if pos == 'left':
          vpt.left_viewpoint = island.viewpoints[vpt_name]
        elif pos == 'right':
          vpt.right_viewpoint = island.viewpoints[vpt_name]
        elif pos == 'up':
          vpt.up_viewpoint = island.viewpoints[vpt_name]
        elif pos == 'down':
          vpt.down_viewpoint = island.viewpoints[vpt_name]
        elif pos == 'forward':
          vpt.forward_viewpoint = island.viewpoints[vpt_name]
        elif pos == 'backward':
          vpt.backward_viewpoint = island.viewpoints[vpt_name]
      print('# Positions:%d, # Viewpoints:%d' % (pos_count, vpt_count))
    return riven_map

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
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', mov, '-b', '200k',
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
      if position.island.id == viewpoint.island.id and \
         viewpoint.name in position.viewpoints:
        anim_images.append(Loader.ProtectPath(viewpoint.thumbnail))

    if not len(anim_images):
      return futures

    if len(anim_images) == 1:
      outfile = anim_images[0]
    else:
      outfile = os.path.join(os.path.dirname(anim_images[0]),
          'position_%d_thumbnail.gif' % position.id)
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
                                     thumbnail_src, outfile, Loader.thumbnail_sf))
    viewpoint.thumbnail = Loader.UnprotectPath(outfile)
    # Retina resolution
    fname = '%s_thumbnail2x.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    if not os.path.exists(outfile):
      futures.append(executor.submit(Loader.ScaleImage,
                                     thumbnail_src, outfile, Loader.thumbnail2x_sf))
    viewpoint.thumbnail2x = Loader.UnprotectPath(outfile)

    return futures

  @staticmethod
  def CreateViewpointMovieThumbnails(viewpoint, thumbnail_src, executor):
    futures = []

    # Standard resolution
    fname = '%s_thumbnail.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    futures.append(executor.submit(Loader.CreateMovieThumbnail,
                                   thumbnail_src, outfile, Loader.thumbnail_sf))
    viewpoint.thumbnail = Loader.UnprotectPath(outfile)
    # Retina resolution
    fname = '%s_thumbnail2x.png' % viewpoint.name
    outfile = os.path.join(os.path.dirname(thumbnail_src), fname)
    futures.append(executor.submit(Loader.CreateMovieThumbnail,
                                   thumbnail_src, outfile, Loader.thumbnail2x_sf))
    viewpoint.thumbnail2x = Loader.UnprotectPath(outfile)

    return futures

  @staticmethod
  def SetImageSize(info, image):
    with Image.open(info.file_path) as im:
      image.image_width, image.image_height = im.size

  @staticmethod
  def SetMovieSize(info, movie):
    movie.movie_width, movie.movie_height = Loader.GetMovieSize(info.file_path)

  @staticmethod
  def CreateViewpointThumbnails(viewpoints, images, movies):
    view2img = dict()
    for image in images:
      if image.viewpoint.id not in view2img:
        view2img[image.viewpoint.id] = []
      view2img[image.viewpoint.id].append(image)

    view2mov = dict()
    for movie in movies:
      if movie.viewpoint.id not in view2mov:
        view2mov[movie.viewpoint.id] = []
      view2mov[movie.viewpoint.id].append(movie)

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
  def FindViewpointImage(viewpoint, all_images, image_name):
    for image in all_images:
      if image.viewpoint != viewpoint:
        continue
      if image.friendly == image_name:
        return image
    return None

  @staticmethod
  def FindViewpointMovie(viewpoint, all_movies, movie_name):
    for movie in all_movies:
      if movie.viewpoint != viewpoint:
        continue
      if movie.friendly == movie_name:
        return movie
    return None

  @staticmethod
  def FindAssets(ref, riven_map, all_images, all_movies):
    """Parse an image reference to a list of images.

    A reference in the form of <island_symbol>/<viewpoint_name>, find all full
    size images in that viewpoint and return them."""
    items = ref.split('/')
    if len(items) < 2:
      raise InvalidReferenceException(ref)

    if items[0] not in riven_map.islands:
      raise InvalidReferenceException(ref)
    island = riven_map.islands[items[0]]

    if items[1] not in island.viewpoints:
      raise InvalidReferenceException(ref)
    viewpoint = island.viewpoints[items[1]]

    images = []
    movies = []

    if len(items) == 3:
      # Only add the specified image
      image = Loader.FindViewpointImage(viewpoint, all_images, items[2])
      if image:
        images.append(image)
      else:
        movie = Loader.FindViewpointMovie(viewpoint, all_movies, items[2])
        if not movie:
          raise InvalidReferenceException(ref)
        movies.append(movie)
    else:
      # Add all full sized images in the given viewpoint.
      for image in all_images:
        if image.viewpoint == viewpoint and image.IsFullSize():
          images.append(image)
      # Don't load all viewpoint movies. There are too many small movies that
      # clutter the object page.
    return (images, movies)

  def LoadObjects(self, riven_map, all_images, all_movies):
    obj_names = set()
    objects = []
    with open(os.path.join('objects.json5')) as f:
      json_objects = json5.load(f)
      for json_object in json_objects:
        name = json_object['name']
        if name in obj_names:
          print('Duplicate object name: "%s"' % name)
          sys.exit(1)
        obj_names.add(name)
        obj = Object(name, json_object['title'])
        for json_ref in json_object['refs']:
          obj_images, obj_movies = Loader.FindAssets(json_ref, riven_map,
                                                     all_images, all_movies)
          obj.images.extend(obj_images)
          obj.movies.extend(obj_movies)
        if len(obj.images):
          viewpoint = obj.images[0].viewpoint
          obj.thumbnail = viewpoint.thumbnail
          obj.thumbnail2x = viewpoint.thumbnail2x
        objects.append(obj)
    return objects

  def LoadData(self, conn):
    """Create the rest of the Riven map based on the image/movie data."""
    island_to_imgvpt = self.LoadFiles('png')
    island_to_movvpt = self.LoadFiles('mov')
    c = conn.cursor()

    riven = Loader.LoadMap('map.json')

    executor = ThreadPoolExecutor(max_workers=num_cpus)
    futures = []

    images = []
    for island_symbol in island_to_imgvpt:
      if island_symbol in riven.islands:
        island = riven.islands[island_symbol]
      else:
        island = Island(island_symbol)
        riven.islands[island_symbol] = island
      for viewpoint_name in island_to_imgvpt[island_symbol]:
        viewpoint = island.GetViewpoint(viewpoint_name)
        viewpoint.position = island.FindPosition(viewpoint_name)
        viewpoint_to_info = island_to_imgvpt[island_symbol]
        for info in viewpoint_to_info[viewpoint_name]:
          file_path = Loader.UnprotectPath(info.file_path)
          image = RivenImg(viewpoint, info.filename(), info.friendly_name(),
                           file_path, 0, 0)
          images.append(image)
          futures.append(executor.submit(Loader.SetImageSize, info, image))

    movies = []
    for island_symbol in island_to_movvpt:
      if island_symbol in riven.islands:
        island = riven.islands[island_symbol]
      else:
        island = Island(island_symbol)
        riven[island_symbol] = island
      for viewpoint_name in island_to_movvpt[island_symbol]:
        viewpoint_to_info = island_to_movvpt[island_symbol]
        for info in viewpoint_to_info[viewpoint_name]:
          gif_path = Loader.SwapExtension(info.file_path, 'gif')
          if not os.path.exists(gif_path):
            futures.append(executor.submit(Loader.TranscodeMovie,
                                           info.file_path, gif_path))
          h264_path = Loader.SwapExtension(info.file_path, 'm4v')
          if not os.path.exists(h264_path):
            futures.append(executor.submit(Loader.MakeH264,
                                           info.file_path, h264_path))
          viewpoint = island.GetViewpoint(viewpoint_name)
          gif_path = Loader.UnprotectPath(gif_path);
          h264_path = Loader.UnprotectPath(h264_path);
          movie = RivenMovie(viewpoint, info.filename(), info.friendly_name(),
                             info.file_path, gif_path, h264_path, 0, 0)
          movies.append(movie)
          futures.append(executor.submit(Loader.SetMovieSize, info, movie))

    all_islands = []
    all_viewpoints = []
    all_positions = []
    for island_symbol in riven.islands:
      all_islands.append(riven.islands[island_symbol])
      viewpoints = riven.islands[island_symbol].viewpoints
      for viewpoint_name in viewpoints:
        all_viewpoints.append(viewpoints[viewpoint_name])
      positions = riven.islands[island_symbol].positions
      for position_name in positions:
        all_positions.append(positions[position_name])
    Loader.CreateViewpointThumbnails(all_viewpoints, images, movies)
    futures.extend(Loader.CreateAllPositionImageThumbnails(all_positions,
                                                           all_viewpoints,
                                                           executor))
    if (len(futures)):
      print('Waiting for file transcoding to finish...')
      for f in futures:
        f.result()

    # Need thumbnails to be finished.
    all_objects = self.LoadObjects(riven, images, movies)

    riven.WriteGraphViz('riven.dot')

    c.executemany('INSERT INTO islands VALUES %s' % Island.insert(),
                  [i.sqlrow() for i in all_islands])
    c.executemany('INSERT INTO viewpoints VALUES %s' % Viewpoint.insert(),
                  [v.sqlrow() for v in all_viewpoints])
    c.executemany('INSERT INTO positions VALUES %s' % Position.insert(),
                  [p.sqlrow() for p in all_positions])
    c.executemany('INSERT INTO rivenimgs VALUES %s' % RivenImg.insert(),
                  [i.sqlrow() for i in images])
    c.executemany('INSERT INTO rivenmovs VALUES %s' % RivenMovie.insert(),
                  [m.sqlrow() for m in movies])
    c.executemany('INSERT INTO objects VALUES %s' % Object.insert(),
                  [o.sqlrow() for o in all_objects])
    obj_to_img = []
    obj_to_mov = []
    for obj in all_objects:
      for img in obj.images:
        obj_to_img.append(ObjectImageAssocation(obj, img))
      for movie in obj.movies:
        obj_to_mov.append(ObjectMovieAssocation(obj, movie))
    ObjectImageAssocation.InsertAll(c, obj_to_img)
    ObjectMovieAssocation.InsertAll(c, obj_to_mov)

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
      data = json5.load(data_file)
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
