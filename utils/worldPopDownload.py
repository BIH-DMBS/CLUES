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
    # -------------------------------------------------------
    # 1. Load bounding box for the region of interest (ROI)
    # -------------------------------------------------------
    try:
        bbox = utils.get_bbox('bbox.json')['bbox']
    except Exception as e:        
        print(f"An error occurred: {e} ")
    
    '''
    Bounding boxes can be represented in different conventions depending on the software or library. In our framework, 
    we follow the (max_lat, min_lon, min_lat, max_lon) style commonly used in some geospatial datasets and GIS tools. In 
    contrast, the WorldPop Python library (worldpoppy) expects bounding boxes in the more conventional order (min_lon, min_lat, max_lon, max_lat)
    '''
    bbox = [ 
        bbox[1], #min_lon
        bbox[2], #min_lat
        bbox[3], #max_lon
        bbox[0]  #max_lat
    ]

    # -------------------------------------------------------
    # 2. Read the config file and find the variable to download
    # -------------------------------------------------------
    with open(json_file, 'r') as f:
        parameters = json.load(f)
    product_name = next(
        (v['product_name'] for v in parameters['variables'] if v['name'] == vOI),
        None
    )
    print(product_name)

    # -------------------------------------------------------
    # 3. Download the WorldPop raster for the ROI
    # -------------------------------------------------------
    # Note: 'masked=True' will set missing areas to NaN
    
    data = wp_raster(
        product_name=product_name, 
        aoi=bbox,  # pass bbox
        years=[int(year)],
        masked=True,
        skip_download_if_exists=False  # ensures it downloads fresh
    )

     # -------------------------------------------------------
    # 4. Save to GeoTIFF
    # -------------------------------------------------------
    output_path = os.path.join(
        download_folder,parameters['type'], 
        vOI, 
        f"{year}.tif")
    
    data.rio.to_raster(output_path)
    print(f"Raster saved to: {output_path}")

