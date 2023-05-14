#!/bin/bash

# Define input folder name
input_folder=./data/rst/2019

# Define output folder name
output_folder=./data/rst/2019_out

# Create the output folder if it does not exist
mkdir -p $output_folder

# Loop through all the files in the input folder
for file in $input_folder/*.tif; do
    # Get the filename without the path
    filename=$(basename "$file")
    # Multiply the image by 10000 using gdal_calc.py
    gdal_calc.py -A $file --outfile=$output_folder/temp.tif --calc="A*10000" --NoDataValue=0
    # Reproject and convert the data type using gdalwarp
    gdalwarp -t_srs EPSG:32648 -r average -tr 10 10 -of GTiff -ot UInt16 -co TILED=YES -co COMPRESS=DEFLATE $output_folder/temp.tif $output_folder/$filename
    #remove the temp file
    rm $output_folder/temp.tif
done
