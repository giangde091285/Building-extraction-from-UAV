import os
import glob

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


def create_label_mask(in_rst, in_vec, EPSG, png_size, out_folder):
    gpd_df = gpd.read_file(in_vec)
    ################################################################
    with rasterio.open(in_rst) as src:
        img_bounds = src.bounds

    # left, bottom, right, top
    l, b, r, t = img_bounds
    img_bbox = Polygon([(l, b), (l, t), (r, t), (r, b)])
    bbox_gdf = gpd.GeoDataFrame({'geometry': [img_bbox]}, crs=EPSG)
    #################################################################

    bbox_gdf_intersect = gpd.overlay(gpd_df, bbox_gdf, how='intersection')

    #################################################################

    rst_att = os.path.basename(in_rst).split('.')[0]
    out_rst_folder = os.path.join(out_folder, rst_att)
    if not os.path.isdir(out_rst_folder):
        os.makedirs(os.path.join(out_rst_folder, 'true'))
        os.makedirs(os.path.join(out_rst_folder, 'false'))
        os.makedirs(os.path.join(out_rst_folder, 'mask'))
        os.makedirs(os.path.join(out_rst_folder, 'mask_vec'))

    mp = MultiPolygon(bbox_gdf_intersect['geometry'].values)

    with rasterio.open(in_rst) as src:
        width = src.width
        height = src.height
        data = src.read(1)

        for w in range(0, width, png_size):
            for h in range(0, height, png_size):
                window = (w, h, w + png_size, h + png_size)
                win = Window(w, h, png_size, png_size)
                trans = src.window_transform(win)
                a = src.read(window=win)
                p = src.profile.copy()
                p['width'] = win.width
                p['height'] = win.height
                p['transform'] = src.window_transform(win)
                with rasterio.open('./tmp/tmp.tif', 'w', **p) as dst:
                    bnds = dst.bounds

                x = Polygon(box(*bnds))

                has_bldg = x.intersects(mp)

                if has_bldg is True:
                  label = 'true'
                  label_1 = 'mask'

                  win_bldgs = gpd.clip(bbox_gdf_intersect, x)

                  # save the image off as a png
                  fp_geojson = f'{out_rst_folder}/{label_1}_vec/{w}-{h}.geojson'
                  fp_png = f'{out_rst_folder}/{label_1}/{w}-{h}.tif'

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

                  fp = f'{out_rst_folder}/{label}/{w}-{h}.tif'
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
                                    
                                    
class RasterProcessor:
    def __init__(self, in_rst_folder, out_folder, epsg=5899, png_size=512, in_rst=None, in_vec=None):
        self.in_rst_folder = in_rst_folder
        self.out_folder = out_folder
        self.epsg = epsg
        self.png_size = png_size
        self.in_rst = in_rst
        self.in_vec = in_vec

    def process_rasters(self):
        if self.in_rst and self.in_vec:
            in_rst = os.path.join(self.in_rst_folder, os.path.basename(self.in_rst))
            in_vec = os.path.join(self.in_rst_folder, os.path.basename(self.in_vec))
            if os.path.isfile(in_rst) and os.path.isfile(in_vec):
                create_label_mask(in_rst, in_vec, self.epsg, self.png_size, self.out_folder)
            else:
                print (f"The input files: {in_rst} and {in_vec} do not exist!")
        elif self.in_rst and self.in_vec is None:
                in_vec = os.path.join(self.in_rst_folder, os.path.basename(self.in_rst)[:-4]  + ".geojson")
                in_rst = os.path.join(self.in_rst_folder, os.path.basename(self.in_rst))
                if os.path.isfile(in_vec) and os.path.isfile(in_rst):
                    create_label_mask(in_rst, in_vec, self.epsg, self.png_size, self.out_folder)
                else:
                    print (f"The input files: {in_rst} and {in_vec} do not exist!")
        elif self.in_rst is None and self.in_vec is None:                    
            in_rst_file_list = glob.glob(os.path.join(self.in_rst_folder, '*.tif'))
            if len(in_rst_file_list) > 0:
                for in_rst in in_rst_file_list:
                    in_vec = os.path.join(self.in_rst_folder, os.path.basename(in_rst)[:-4]  + ".geojson")
                    if os.path.isfile(in_vec):
                        create_label_mask(in_rst, in_vec, self.epsg, self.png_size, self.out_folder)
                    else:
                        print (f"The input file {in_vec} does not exist!")
            else:
                print (f"The folder {self.in_rst_folder} has no GEOTIFF raster file")

# specify the input and output directories
input_dir = '../data/orig'
output_dir = '../data/preprocessed'

# create an instance of the RasterProcessor class
processor = RasterProcessor(input_dir, output_dir)

# process the rasters
processor.process_rasters()