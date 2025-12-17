import rasterio
import rasterio.mask
import geopandas as gpd
import numpy as np
from shapely.geometry import box
import multiprocessing
import pandas as pd

def weighted_median(values, weights):
    """Compute weighted median of 1D arrays"""
    sorter = np.argsort(values)
    values_sorted = values[sorter]
    weights_sorted = weights[sorter]
    cumsum = np.cumsum(weights_sorted)
    cutoff = 0.5 * np.sum(weights_sorted)
    return values_sorted[np.searchsorted(cumsum, cutoff)]

def compute_stats_for_aoi(args):
    """Compute area-weighted stats for a single AOI"""
    file_path, aoi_geojson, aoi_name = args
    src = rasterio.open(file_path)

    # Mask raster (keep original nodata)
    out_image, out_transform = rasterio.mask.mask(src, aoi_geojson, crop=True)
    masked_data = out_image[0]

    # Pixel size in degrees
    pixel_width_deg = out_transform.a
    pixel_height_deg = -out_transform.e

    # Latitude of each pixel
    nrows, ncols = masked_data.shape
    lat_start = out_transform.f + pixel_height_deg / 2
    lat_array = lat_start + np.arange(nrows) * pixel_height_deg
    lat_grid = np.repeat(lat_array[:, np.newaxis], ncols, axis=1)

    # Pixel area in km²
    pixel_area = (pixel_width_deg * 111.32) * (pixel_height_deg * 110.57 * np.cos(np.deg2rad(lat_grid)))

    # Valid pixels
    valid_mask = masked_data != src.nodata
    vals = masked_data[valid_mask].flatten()
    areas = pixel_area[valid_mask].flatten()

    if len(vals) == 0:
        return (aoi_name, np.nan, np.nan, np.nan)

    # Weighted statistics
    weighted_sum = np.sum(vals * areas)
    total_area = np.sum(areas)
    area_weighted_mean = weighted_sum / total_area
    w_median = weighted_median(vals, areas)
    weighted_var = np.sum(areas * (vals - area_weighted_mean)**2) / np.sum(areas)
    weighted_std = np.sqrt(weighted_var)

    return (aoi_name, area_weighted_mean, w_median, weighted_std)

if __name__ == "__main__":
    file_path = r'C:\code\CLUES\data\Night_Time_Lights_(NTL)\Harmonized_DN_NTL_2002_calDMSP.tif'

    # Define multiple AOIs as tuples (name, geometry)
    aoi_list = [
        ("AOI_1", box(-10, 35, 0, 45)),
        ("AOI_2", box(0, 35, 10, 45)),
        ("AOI_3", box(-10, 45, 0, 55)),
        # Add more AOIs here...
    ]

    # Prepare input for multiprocessing
    input_list = []
    for name, geom in aoi_list:
        aoi_geojson = [gpd.GeoSeries([geom], crs="EPSG:4326").__geo_interface__['features'][0]['geometry']]
        input_list.append((file_path, aoi_geojson, name))

    # Run in parallel
    pool = multiprocessing.Pool(processes=16)
    results = pool.map(compute_stats_for_aoi, input_list)
    pool.close()
    pool.join()

    # Convert results to a table
    df = pd.DataFrame(results, columns=["AOI", "Mean", "Median", "StdDev"])
    print(df)
