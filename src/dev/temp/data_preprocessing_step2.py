import os
import glob


in_folder = '/home/duy/local/study/deep_learning/DL_2023/data/rst_dl_512'
out_folder = '/home/duy/local/study/deep_learning/DL_2023/data/rst_final_512_v1'

in_file_list = glob.glob(os.path.join(in_folder, '*/true/*.tif'))
print (len(in_file_list))

widths = []
heights = []

for in_rst in set(in_file_list):
    [width, height] = os.path.basename(in_file_list[0])[:-4].split('-')
    widths.append(int(width))
    heights.append(int(height))

# width, height = np.array(widths).max(), np.array(heights).max()

bands = ['aerosols', 'blue', 'green', 'red', 'rege1', 'rege2', 'rege3', 'nir', 'swir1', 'swir2']

for fn in set(in_file_list):
    fn = os.path.basename(fn)
    print (fn)
    fns = []
    for band in bands:
#             print (band, glob.glob(os.path.join(in_folder, f'{band}/true/*{fn}*')))
        fns.append(glob.glob(os.path.join(in_folder, f'{band}/true/*{fn}*'))[0])

#     print (fns)
    if len(fns) == 10:
        in_files = " ".join(fns)
        # print (in_files)
        # import pdb; pdb.set_trace()
        out_file = os.path.basename(fns[0])[:-4] + '.vrt'
        cmd = f'gdalbuildvrt -separate ./{out_file} {in_files}'
        os.system(cmd)
        cmd = f'gdal_translate ./{out_file} {out_folder}/tra_scene/{fn}'
        os.system(cmd)
#         cmd = 'rm -rf ./temp.vrt'
#         os.system(cmd)
