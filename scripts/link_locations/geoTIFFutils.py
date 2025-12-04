# environMENTAL GeoLink
# Linking App for Subjects (ID and Point Coordinats) to Geodata as GeoTIFFs 
# Extraction to a single CSV file with ID and extracted information
# Authors: Marcel Jentsch, Paul Renner, Elli Polemiti, James Richard Banks
# Version 1: Developed during the environMENTAL Hackathon (03.-05. May 2023)
# Version 2: Jentsch October 2023
####################################
# Import Packages

import rasterio as rio
import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
import rasterstats
import functools as ft
from pathlib import Path 
import json
import numpy as np

# Define Read GeoTIFFs to list
def getTiffList(TIFFdir):
    tiff_files = []
    for root, _, files in os.walk(TIFFdir):
        for file in files:
            if file.endswith('.tif') or file.endswith('.tiff'):
                tiff_files.append(os.path.join(root, file))
    return tiff_files


# Define prepare parameter
def getparam(geoTIFF_Filelist):
    interpolmeth='nearest' #'bilinear'
    parameter=[]
    print('Loading the following files:')
    for asset in geoTIFF_Filelist:
        parameter.append({'interpolate':interpolmeth, 'asset':asset})
    return parameter

# Define Read CSV of Subjects
def getsubj(subjectfile, pntcoord):
    subjects = pd.read_csv(subjectfile)
    subjects[pntcoord] = subjects[pntcoord].apply(wkt.loads)
    subjects = gpd.GeoDataFrame(subjects, geometry = pntcoord, crs='epsg:4326')
    return subjects

# Define Linking function to append results to the result object
def makeLinkage(subjects, src, parameter):
    pntcoord='geometry'
    subjectid='subjectid'#'subjectID
    res = []
    for index, row in subjects.iterrows():
        pixel_x, pixel_y = src.index(row[pntcoord].x,row[pntcoord].y)
        pixel_value = src.read(1, window=((int(pixel_x), int(pixel_x) + 1), (int(pixel_y), int(pixel_y) + 1)))
        if pixel_value.size==0:
            res.append('nan')
        else:
            res.append(pixel_value[0][0])
    result = pd.DataFrame({subjectid:subjects[subjectid], parameter['asset']:res}) 
    return result


def link_coordinates(geocoordinates_gdf, file_path):
    # Initialize an empty dictionary to store the results
    rowcol_dict = {}
    result_dict = {}
    bbox = geocoordinates_gdf.geometry.total_bounds
    with rio.open(file_path) as src:
        for index, row in geocoordinates_gdf.iterrows():
            point = row.geometry
            row_idx, col_idx = rowcol(src.transform, point.x, point.y)
            # Use the row_idx and col_idx as a key
            key = (row_idx, col_idx)     
            # Append the index to the list corresponding to the key
            if key not in rowcol_dict:
                rowcol_dict[key] = []
            rowcol_dict[key].append(index)
        row_start, col_start = rowcol(src.transform, bbox[0], bbox[1])
        row_stop, col_stop = rowcol(src.transform, bbox[2], bbox[3])
        # I tried also to load all or only the loactaion of interest
        # using the bounding box seems was the fastest
        # mybe later cluster the points and set different bounding boxes
        data = src.read(window=((row_start, row_stop+1), (col_start, col_stop+1)))
        for k,v in rowcol_dict.items():
            result_dict[tuple(v)] = data[:, k[0]-row_start, k[1]-col_start].flatten()
    return result_dict

# Define GeoLink for subject list file and geoTIFFs
def geoTiffLinker(subjects, geoTIFF_Filelist, parameter):
    subjectid='subjectid'#'subjectID
    res = []
    for idx, f in enumerate(geoTIFF_Filelist):
        src = rio.open(f)
        res.append(makeLinkage(subjects, src, parameter[idx]))
        print(src,f'Done reading {src.name} and extracting values.')
        src.close()
    print('Combining extracted values.')
    res = ft.reduce(lambda left, right: left.join(right.set_index(subjectid), on=subjectid), res)
        
    return res

