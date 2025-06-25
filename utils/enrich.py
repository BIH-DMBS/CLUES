import rasterio as rio
from rasterio.transform import rowcol
from rasterio.warp import transform_bounds
from rasterio.transform import from_origin
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def generate_random_geocoordinates(n, bounding_box):
    min_lat, min_lon, max_lat, max_lon = bounding_box
    latitudes = np.random.uniform(low=min_lat, high=max_lat, size=n)
    longitudes = np.random.uniform(low=min_lon, high=max_lon, size=n)
    
    # Create a DataFrame
    df = pd.DataFrame({
        'latitude': latitudes,
        'longitude': longitudes
    })
    
    # Create a GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry)
    
    return gdf


def link_coordinates(geocoordinates_gdf, file_path):
    # link coordiantes to geoTiff
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
        # maybe later cluster the points and set different bounding boxes
        data = src.read(window=((row_start, row_stop+1), (col_start, col_stop+1)))
        for k,v in rowcol_dict.items():
            result_dict[tuple(v)] = data[:, k[0]-row_start, k[1]-col_start].flatten()
    return result_dict
