import glob
import os
import json
import xarray as xr
import netCDF4
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle
import concurrent.futures
import gc
from shapely.geometry import shape, Point, box, Polygon

import multiprocessing

import warnings
# Suppress only PerformanceWarning from pandas
from pandas.errors import PerformanceWarning

warnings.simplefilter(action='ignore', category=PerformanceWarning)

def create_grid_gdf(ds, var_name):
    # extract coordinates
    lons = ds['longitude'][:]
    lats = ds['latitude'][:]

    # compute lon and lat edges
    lon_edges = np.concatenate([
        [lons[0] - (lons[1] - lons[0]) / 2],
        (lons[:-1] + lons[1:]) / 2,
        [lons[-1] + (lons[-1] - lons[-2]) / 2]
    ])

    lat_edges = np.concatenate([
        [lats[0] - (lats[1] - lats[0]) / 2],
        (lats[:-1] + lats[1:]) / 2,
        [lats[-1] + (lats[-1] - lats[-2]) / 2]
    ])

    # extract variable data (e.g. for one time step)
    data = ds[var_name][:, :, :]   # assuming 'valid_time' is first dimension

    polygons = []
    values = []

    for j in range(len(lats)):
        for i in range(len(lons)):
            poly = Polygon([
                (lon_edges[i], lat_edges[j]),
                (lon_edges[i+1], lat_edges[j]),
                (lon_edges[i+1], lat_edges[j+1]),
                (lon_edges[i], lat_edges[j+1])
            ])
            polygons.append(poly)
            values.append(data[:,j, i])
    gdf_grid = gpd.GeoDataFrame(
        {var_name: values},
        geometry=polygons,
        crs="EPSG:4326"
    )
    return gdf_grid

def area_intersection(gdf_grid, gdf_grunnkretser):
    # assume:
    # gdf_grid  : GeoDataFrame of grid rectangles (one row per cell) with index == grid cell id
    #             and a variable column (e.g. 'bcaod550')
    # gdf_grunnkretser: GeoDataFrame of polygons, with column 'id' (region id)
    # both currently in EPSG:4326

    # 1) Reproject both to a suitable equal-area CRS (choose one that suits your area; here I use World Cyl. Equal Area)
    ea_crs = "EPSG:6933"   # or choose a local equal-area projection for better accuracy
    g_grid_ea = gdf_grid.to_crs(ea_crs)
    g_regions_ea = gdf_grunnkretser.to_crs(ea_crs)

    # 2) Compute polygon areas (region areas) in m^2
    g_regions_ea = g_regions_ea.copy()
    g_regions_ea['poly_area_m2'] = g_regions_ea.geometry.area

    # 3) Overlay intersections (each row = grid cell ∩ polygon)
    inter = gpd.overlay(g_grid_ea.reset_index().rename(columns={'index':'grid_idx'}),
                        g_regions_ea.reset_index().rename(columns={'index':'region_idx'}),
                        how='intersection')

    # inter now has: geometry (intersection), grid attributes, region attributes.
    # 4) compute intersection area
    inter['intersect_area_m2'] = inter.geometry.area

    # 5) Map region total area into intersections (so denominator is polygon area)
    #    if you kept region index/ID in inter, use that to map; here assume 'id' is region id column
    inter = inter.merge(
        g_regions_ea[['grunnkretsnummer','poly_area_m2']],
        on='grunnkretsnummer',
        how='left',
        validate='m:1'
    )

    # 6) fraction of polygon area contributed by each intersection
    inter['frac_of_polygon'] = inter['intersect_area_m2'] / inter['poly_area_m2_y']
    return inter


def aggregate_timeseries(ds, inter, var_name, dates):
    # list of grunnkretsnummer
    grunnkrets_list = inter['grunnkretsnummer'].unique()

    # initialize result DataFrame
    result = pd.DataFrame({'grunnkretsnummer': grunnkrets_list})

    # loop over time steps
    daily_values = []

    for t_idx, date in enumerate(dates):
        # flatten grid variable for this time step
        data_t = ds[var_name][t_idx, :, :]
        data_flat = data_t.flatten()
        
        # assign values to inter (by grid index)
        inter[var_name] = data_flat[inter['grid_idx']]
        
        # area-weighted contribution
        inter['weighted'] = inter[var_name] * inter['frac_of_polygon']
        
        # sum contributions per polygon
        weighted_sum = inter.groupby('grunnkretsnummer')['weighted'].sum()
        
        # add as a new column
        daily_values.append(weighted_sum.rename(str(date)+'sum'))

    # combine all days into one DataFrame
    daily_df = pd.concat(daily_values, axis=1).reset_index()

    # Separate the ID column
    id_col = 'grunnkretsnummer'
    ids = daily_df[id_col]

    # Group columns by date
    date_cols = daily_df.columns.drop(id_col)

    # Extract unique dates from the column names
    # assuming columns are strings like '2023-01-01'
    unique_dates = sorted(set([col.split()[0] for col in date_cols]))

    # Create a new DataFrame to store aggregated results
    agg_df = pd.DataFrame({id_col: ids})

    for date in unique_dates:
        # select all columns for this date
        cols = [c for c in daily_df.columns if c.startswith(date)]
        
        # compute aggregations row-wise
        agg_df[f'{date}_sum'] = daily_df[cols].sum(axis=1)
        agg_df[f'{date}_mean'] = daily_df[cols].mean(axis=1)
        agg_df[f'{date}_min'] = daily_df[cols].min(axis=1)
        agg_df[f'{date}_max'] = daily_df[cols].max(axis=1)
        agg_df[f'{date}_median'] = daily_df[cols].median(axis=1)
        agg_df[f'{date}_std'] = daily_df[cols].std(axis=1)

    return daily_df, agg_df

def worker(input_tuple):
    fileList, resultfolder, gdf_grunnkretser = input_tuple
    for file in fileList:
        resultfile = resultfolder + concat_lowest_folder_and_filename(file) + ".csv"
        resultfile_agg = resultfolder + "agg_" + concat_lowest_folder_and_filename(file) + ".csv"
        if os.path.exists(resultfile):
            print(f"File exists: {resultfile}")
            return

        print(f"Processing: {file}")

        ds = netCDF4.Dataset(file)
        variablesOI = {var_name:var.dimensions for var_name, var in ds.variables.items() if var_name not in ['longitude','latitude','valid_time','expver','number']}             

        var_name = list(variablesOI.keys())[0]
        print(variablesOI)
        gdf_grid = create_grid_gdf(ds, var_name)
        gdf_grid.head()

        inter = area_intersection(gdf_grid, gdf_grunnkretser)

        # extract time variable
        time_var = ds['valid_time']  # e.g., hours since 2000-01-01
        time_units = time_var.units
        # convert numeric time to cftime objects
        times_cftime = netCDF4.num2date(time_var[:], units=time_units)
        # convert cftime objects to standard Python datetime.date
        dates = [pd.Timestamp(str(t)).date() for t in times_cftime]

        daily_df, agg_df = aggregate_timeseries(ds, inter, var_name, dates)
        # clean up
        ds.close()

        # Save as CSV
        daily_df.to_csv(resultfile, index=False)
        agg_df.to_csv(resultfile_agg, index=False)
        print(f"Saved results to {resultfile}")

def concat_lowest_folder_and_filename(path):
    lowest_folder = os.path.basename(os.path.dirname(path))
    filename = os.path.basename(path)
    return lowest_folder + '_' + filename

if __name__ == "__main__":
    # load area definitions
    pkl_file = 'dummy_areas.pkl'

    gdf_grunnkretser = pd.read_pickle(pkl_file)
    print(gdf_grunnkretser.shape)
    print(gdf_grunnkretser.crs)

    fileList = []

    netCDF_folders = [
        'C:\\code\\CLUES\\data\\cams-global-reanalysis-eac4'
    ]

    result_folder = 'C:\\code\\CLUES\\scripts\\link_areas\\result\\'

    for folder in netCDF_folders:
        # '**/*.tif' matches .tif files in folder and all subfolders
        files = glob.glob(os.path.join(folder, '**', '*.nc'), recursive=True)
        print(files)
        fileList.extend(files)
    
    print(fileList)

    print(concat_lowest_folder_and_filename(fileList[0]))
    
    
    # number of jobs
    chunks = 10
    fileList_chunk_size = len(fileList) // chunks

    fileList = [fileList[i:i+fileList_chunk_size] for i in range(0, len(fileList), fileList_chunk_size)]
    print(fileList)
    
    print("Create a Pool of worker processes")
    pool = multiprocessing.Pool(processes=8)  # You can specify the number of processes you want to run in parallel

    print('Create a list of input tuples')
    inpt = []
    for i in range(0,chunks):
        inpt.append((fileList[i], result_folder, gdf_grunnkretser))
    
    print('Link')
    print('Map the worker function to the input tuples in parallel')
    pool.map(worker, inpt)

    print('Close the pool and wait for the worker processes to finish')
    pool.close()
    pool.join()
    
    