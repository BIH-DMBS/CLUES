import geopandas as gpd
from shapely.geometry import box
from worldpoppy import wp_raster
import rioxarray as rxr
import json

import utils


try:
    from .config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder
except:
    from config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder

import logging
import os

def getWorldPop(json_file, year, vOI):

    try:
        bbox = utils.get_bbox('bbox.json')['bbox']
    except Exception as e:        
        print(f"An error occurred: {e} ")
    
    '''
    Bounding boxes can be represented in different conventions depending on the software or library. In our framework, 
    we follow the (max_lat, min_lon, min_lat, max_lon) style commonly used in some geospatial datasets and GIS tools. In 
    contrast, the WorldPop Python library (worldpoppy) expects bounding boxes in the more conventional order (min_lon, min_lat, max_lon, max_lat)
    '''
    bbox = [ bbox[1], bbox[2], bbox[3],bbox[0] ]

    with open(json_file, 'r') as f:
        parameters = json.load(f)
    product_name = next(
        (v['product_name'] for v in parameters['variables'] if v['name'] == vOI),
        None
    )
    print(product_name)
   
    # --- Step 1: Fetch WorldPop raster for the ROI ---
    # Note: 'masked=True' will set missing areas to NaN
    data = wp_raster(
        product_name=product_name, 
        aoi=bbox,  # pass bbox
        years=[int(year)],
        masked=True,
        skip_download_if_exists=False  # ensures it downloads fresh
    )

    # --- Step 2: Save raster to GeoTIFF ---
    output_path = download_folder_er5_land = os.path.join(download_folder,parameters['type'], vOI, f"{year}.tif")
    data.rio.to_raster(output_path)
    print(f"Raster saved to: {output_path}")

