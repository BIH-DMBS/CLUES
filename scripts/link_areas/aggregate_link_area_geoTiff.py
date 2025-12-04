import glob
import os
import rasterio
import pickle
import geopandas as gpd
import pandas as pd
import numpy as np
from rasterstats import zonal_stats
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
import multiprocessing

def link_regions(raster_path, result_folder):
    filename = os.path.basename(raster_path.replace(".tif","").replace(".vrt",""))
    resultfile = result_folder + f"{filename}.csv"
    if os.path.exists(resultfile):
        print(f"File exists: {resultfile}")
        return

    print(f"Processing: {raster_path}")

    # load area definitions
    pkl_file = 'grunnkretser.pkl'

    gdf_grunnkretser = pd.read_pickle(pkl_file)
    print(gdf_grunnkretser.shape)
    print(gdf_grunnkretser.crs)

    # Read nodata value from raster metadata
    with rasterio.open(raster_path) as src:
        nodata = src.nodata

    stats = zonal_stats(
        gdf_grunnkretser,
        raster_path,
        stats=["mean","median","std"],
        raster_out=True,
        nodata=nodata,
        exact=False
    )
    gdf_grunnkretser["mean_value"] = [s["mean"] for s in stats]
    gdf_grunnkretser["median_value"] = [s["median"] for s in stats]
    gdf_grunnkretser["std_value"] = [s["std"] for s in stats]

    print("Zonal statistics calculated for"+ raster_path)

    nodata_count, valid_pixels_count = [], []
    for row in gdf_grunnkretser.itertuples():
        geometry = row.geometry
            
        with rasterio.open(raster_path) as src:
            # Get the bounding box of the polygon
            minx, miny, maxx, maxy = geometry.bounds

            # Convert bbox to raster window
            window = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
            
            # Read only that window
            data = src.read(1, window=window)
            
            # Create a transform for the window
            window_transform = src.window_transform(window)
            
            try:
                # Create mask: True for pixels inside the polygon
                mask_inside = geometry_mask([geometry], invert=True, transform=window_transform, out_shape=data.shape)
                
                # Extract pixels inside polygon
                pixels_inside_polygon = data[mask_inside]
                
                # Count nodata pixels inside polygon
                nodata_count.append(np.sum(pixels_inside_polygon == src.nodata))
                
                # Optional: get valid pixels
                valid_pixels_count.append(len(pixels_inside_polygon[pixels_inside_polygon != src.nodata]))
            except Exception as e:
                print(f"Error processing geometry {row.Index}: {e} in {filename}")
                nodata_count.append(np.nan)
                valid_pixels_count.append(np.nan)

    gdf_grunnkretser["nodata_count"] = nodata_count
    gdf_grunnkretser["valid_pixels_count"] = valid_pixels_count
    # Drop geometry column
    gdf_grunnkretser = gdf_grunnkretser.drop(columns="geometry")

    # Save as CSV
    gdf_grunnkretser.to_csv(resultfile, index=False)
    print(f"Saved results to {filename}.csv")

def worker(rester_paths):
    for raster_path in rester_paths:
        link_regions(raster_path)

if __name__ == "__main__":
    raster_paths = []

    tiff_folders = [
        "/Treecover/",
        "/NDVI/",
        "WSF"
    ]

    result_folder = '/results/'

    for folder in tiff_folders:
        # '**/*.tif' matches .tif files in folder and all subfolders
        files = glob.glob(os.path.join(folder, '**', '*.tif'), recursive=True)
        print(files)
        raster_paths.extend(files)
        files = glob.glob(os.path.join(folder, '**', '*.vrt'), recursive=True)
        print(files)
        raster_paths.extend(files)

    print(f"Found {len(raster_paths)} TIFF files in total.")

    filename = os.path.basename(raster_paths[0])

    print(filename)  
    
    # number of jobs
    chunks = 10
    raster_chunk_size = len(raster_paths) // chunks

    raster_paths = [raster_paths[i:i+raster_chunk_size] for i in range(0, len(raster_paths), raster_chunk_size)]
    print(raster_paths)

    print("Create a Pool of worker processes")
    pool = multiprocessing.Pool(processes=8)  # You can specify the number of processes you want to run in parallel

    print('Create a list of input tuples')
    inpt = []
    for i in range(0,chunks):
        inpt.append(raster_paths[i],result_folder)
    
    print('Link')
    print('Map the worker function to the input tuples in parallel')
    pool.map(worker, inpt)

    print('Close the pool and wait for the worker processes to finish')
    pool.close()
    pool.join()
    