import os
import sys
import glob

from shutil import rmtree

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

import fiona
from pprint import pprint
from rasterio.features import Window
from rasterio.windows import bounds
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon, box
from PIL import Image
from rasterio.features import Window
from subprocess import call
# from IPython import display

in_rst_folder = '../../data/orig'
in_rst_file_list = glob.glob(os.path.join(in_rst_folder, '*.tif'))

in_vec = "../../data/orig/kv-1-epsg5899.geojson"

EPSG = 5899

for in_rst in in_rst_file_list:
    all_bldgs = gpd.read_file(in_vec)

    ################################################################
    with rasterio.open(in_rst) as src:
        img_bounds = src.bounds

    # left, bottom, right, top
    l, b, r, t = img_bounds
    img_bbox = Polygon([(l, b), (l, t), (r, t), (r, b)])
    bbox_gdf = gpd.GeoDataFrame({'geometry': [img_bbox]}, crs = EPSG)
    #################################################################

    bldgs = gpd.overlay(all_bldgs, bbox_gdf, how='intersection')

    #################################################################

    rst_att = os.path.basename(in_rst).split('_')[0]
    out_folder = f"../../data/rst_dl_512/{rst_att}"
    if not os.path.isdir(out_folder):
#         rmtree(out_folder)
        os.makedirs(f'{out_folder}/true')
        os.makedirs(f'{out_folder}/false')
        os.makedirs(f'{out_folder}/mask')
        os.makedirs(f'{out_folder}/mask_vec')


    mp = MultiPolygon(bldgs['geometry'].values)

    # specify the png image size (in pixels) 
    png_size = 512

    with rasterio.open(in_rst) as src:
        # gather width and height of input image
        width = src.width
        height = src.height
        data = src.read(1)

        # iterate over the image in a grid of 1200x1200 pixel squares
        for w in range(0, width, png_size):
            for h in range(0, height, png_size):
              # Read the input raster's data and metadata
              window = (w, h, w + png_size, h + png_size)

              # construct Window object using row/col and size
              win = Window(w, h, png_size, png_size)

              # find the corresponding spatial coordinates
              trans = src.window_transform(win)

              # read the window portion in as a numpy array
              a = src.read(window=win)

              # create shapely object that represents the bounds of the window
              p = src.profile.copy()
              p['width'] = win.width
              p['height'] = win.height
              p['transform'] = src.window_transform(win)
              with rasterio.open('/tmp/tmp.tif', 'w', **p) as dst:
                  bnds = dst.bounds

              x = Polygon(box(*bnds))

              # check whether the window intersects with any buildings
              has_bldg = x.intersects(mp)

              if has_bldg is True:
                  label = 'true'
                  label_1 = 'mask'

                  win_bldgs = gpd.clip(bldgs, x)

                  # save the image off as a png
                  fp_geojson = f'{out_folder}/{label_1}_vec/{w}-{h}.geojson'
                  fp_png = f'{out_folder}/{label_1}/{w}-{h}.tif'

                  win_bldgs.to_file(fp_geojson, driver='GeoJSON')

                  # Open example raster
                  with fiona.open(fp_geojson, "r") as shapefile:
                      shapes = [feature["geometry"] for feature in shapefile]

                  # Rasterize vector using the shape and coordinate system of the raster
                  rasterized = rasterio.features.rasterize(shapes,
                                                  out_shape = [png_size, png_size],
                                                  fill = 0,
                                                  out = None,
                                                  transform = src.window_transform(win),
                                                  all_touched = False,
                                                  default_value = 1,
                                                  dtype = None)

                  with rasterio.open(fp_png, "w",
                          driver = "GTiff",
                          transform = src.window_transform(win),
                          dtype = rasterio.uint8,
                          count = 1,
                          width = png_size,
                          height = png_size,
                          crs=CRS.from_epsg(EPSG)) as dst:
                      dst.write(rasterized, indexes = 1)

                  fp = f'{out_folder}/{label}/{w}-{h}.tif'
                  # Create the output profile
                  out_meta = src.meta.copy()
                  out_meta.update({"driver": "GTiff",
                                   "height": png_size,
                                   "width": png_size,
                                   "transform": src.window_transform(win)
                                   })

                  # Write the clipped raster to the output file
                  with rasterio.open(fp, "w", **out_meta) as dest_1:
                    dest_1.write(a)
