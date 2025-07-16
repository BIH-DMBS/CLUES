import json
import xarray as xr
import netCDF4
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, Point, box, Polygon
import os
import pickle
import concurrent.futures
import gc
import numpy
#import moba_netCDF as netCDF
from pathlib import Path

from sys import exit

'''
This script will create Apache Parquet storage file format
install
pip install pyarrow    # Recommended

pip install fastparquet
to read the results use:
df = pd.read_parquet("data.parquet", engine="pyarrow")
'''
######################################################
# grunnkretser code stuff
# Define pkl file path
pkl_file = 'grunnkretser.pkl'

# Check if pickle file exists
if os.path.exists(pkl_file):
    # Load data from pickle
    gdf_grunnkretser = pd.read_pickle(pkl_file)
    print("Loaded data from pickle.")
else:
    # Remove size limit on GeoJSON objects
    os.environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"

    file_path = "Basisdata_0000_Norge_3035_Grunnkretser_GeoJSON.geojson"

    # Load the file as a dictionary
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract the "Grunnkrets" FeatureCollection
    grunnkrets_fc = data["Grunnkrets"]

    # Load the feature collection into a GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(
        grunnkrets_fc["features"],
        crs=grunnkrets_fc["crs"]["properties"]["name"]
    )

    # Keep only the columns of interest
    gdf_grunnkretser = gdf[["geometry", "grunnkretsnavn", "grunnkretsnummer"]]
    # Optional: Reproject to a projected CRS for accurate area (e.g., EPSG:3857 or UTM)
    #gdf_grunnkretser = gdf_grunnkretser.to_crs("EPSG:3857")

    # Add area column (units will be in square meters if CRS is meters)
    #gdf_grunnkretser['area_grunnkrets'] = gdf.geometry.area / 1_000_000 # im km^2
    gdf_grunnkretser = gdf_grunnkretser.to_crs("EPSG:4326")
    gdf_grunnkretser['area_grunnkrets'] = gdf_grunnkretser.geometry.area
    gdf_grunnkretser.to_pickle(pkl_file)

# Get the CRS
print(gdf_grunnkretser.crs)
print(gdf_grunnkretser.head)


# linking stuff 

def linkVariable(dataset, name, value, lang, breit, asset_name):

    if value == ('lat', 'lon'):
        print('a' + '...' + name)
        ddOI = [dataset.variables[name]]
        ddOI = np.array(ddOI).flatten()
    elif value == ('days', 'lat', 'lon'): 
        print('b' + '...' + name)
        ddOI = dataset.variables[name][:]
        a, x, y = ddOI.shape
        ddOI = ddOI.reshape(a, x, y)
        ddOI = ddOI.reshape(a, x * y)
        ddOI = ddOI.transpose().tolist()
    elif value == ('days', 'hours', 'lat', 'lon'):
        print('c' + '...' + name)
        ddOI = dataset.variables[name][:]
        a, b, x, y = ddOI.shape
        ddOI = ddOI.reshape(a * b, x, y)
        ddOI = ddOI.reshape(a * b, x * y)
        ddOI = ddOI.transpose().tolist()
    elif value == ('lat', 'lon', 'days'):
        print('d' + '...' + name)
        ddOI = dataset.variables[name][:]
        ddOI = ddOI.transpose(2, 0, 1)
        a, x, y = ddOI.shape
        ddOI = ddOI.reshape(a, x, y)
        ddOI = ddOI.reshape(a, x * y)
        ddOI = ddOI.transpose().tolist()
    elif value == ('months', 'lat', 'lon'):
        print('e' + '...' + name)
        ddOI = dataset.variables[name][:]
        a, x, y = ddOI.shape
        ddOI = ddOI.reshape(a, x, y)
        ddOI = ddOI.reshape(a, x * y)
        ddOI = ddOI.transpose().tolist()
    elif value == ('valid_time', 'latitude', 'longitude'):
        print('____________')
        ddOI = dataset.variables[name][:]
        a, x, y = ddOI.shape
        ddOI = ddOI.reshape(a, x, y)
        ddOI = ddOI.reshape(a, x * y)
        ddOI = ddOI.transpose().tolist()
    elif value == ('valid_time', 'model_level', 'latitude', 'longitude'):
        print('____________')
        ddOI = dataset.variables[name][:]
        ddOI = ddOI.squeeze(1)
        a, x, y = ddOI.shape
        ddOI = ddOI.reshape(a, x, y)
        ddOI = ddOI.reshape(a, x * y)
        ddOI = ddOI.transpose().tolist()
    else:
        print('netCDF variable pattern not covered')

    name = asset_name +'_'+name
    name = name.replace('.nc','_')

    gdf = pd.DataFrame({
        'longitude': np.array(lang).flatten(),
        'latitude': np.array(breit).flatten(),
        name: ddOI
    })
    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(
        gdf, geometry=gpd.points_from_xy(gdf.longitude, gdf.latitude)
    )
    # Apply the make_tile function to the geometry column
    return gdf, name


def getOI(dataset, lang, breit, asset_name):
    result_tmp = pd.DataFrame()

    variablesOI = {var_name:var.dimensions for var_name, var in dataset.variables.items() if var_name not in ['longitude','latitude','valid_time','expver','number','model_level','crs']}             
    variablesOI = dict(list(variablesOI.items()))
    for name, value in variablesOI.items():
        gdf, name_variable = linkVariable(dataset, name, value, lang, breit, asset_name)   
        if result_tmp.empty:
            result_tmp = gdf
        else:
            result_tmp = pd.concat([result_tmp, gdf[name_variable]], axis=1)  #checked this keeps the order

    result_gdf = gpd.GeoDataFrame(result_tmp, geometry='geometry', crs=gdf.crs)  
    return result_tmp

######################################################


def worker(folderOI, exclude_flag, result_folder):
    # get netCDF filelist
    folder = Path(folderOI)
    filesOI = list(folder.glob('**/**/*.nc'))

    # filter netCDF filelist with respect to exclude_flag
    filesOI = [
        path for path in filesOI if not any(sub in str(path) for sub in exclude_flag)
    ]

    last_folder = folder.name or folder.parent.name
    filename = folderOI[20:].replace("/", "_")  + '.parquet'
    filename = filename.replace("\\", "_")
    
    filename = result_folder + filename
    result = pd.DataFrame()
    weight = []
    geometries = []

    if os.path.exists(filename):
            print('result already exists ' + filename)
    else:
        for file_path in filesOI:
            # define meshrid of netcdf file locations in this folder
            #file_path = k+'/'+v[0]
            dataset = netCDF4.Dataset(file_path, mode = "r")
            lang = dataset.variables['longitude'][:]
            breit = dataset.variables['latitude'][:]
            
            lang, breit = np.meshgrid(lang, breit)

            asset_name = os.path.basename(file_path)
            
            print('#############################')
            print(file_path)
            gdf = getOI(dataset, lang, breit, asset_name)

            columns_of_interest =  list(gdf.columns.difference(['geometry', 'latitude', 'longitude']))

            if result.empty:
                b = np.abs(breit[0,0]-breit[1,0])
                l = np.abs(lang[0,0]-lang[0,1])
                x = gdf.geometry.x
                y = gdf.geometry.y

                # make tiles
                geometries = [box(x0, y0, x0 + b, y0 + l) for x0, y0 in zip(x, y)]
                gdf['geometry'] = geometries
                gdf = gpd.overlay(gdf_grunnkretser[['grunnkretsnummer', 'area_grunnkrets','geometry']], gdf, how='intersection')
                #sys.exit()
                # Compute the area of each intersection
                gdf['intersection_area'] = gdf.geometry.area
                #gdf[['grunnkretsnummer', 'area_grunnkrets','intersection_area','geometry']].to_csv('y.csv')
                # Merge the intersection areas back to gdf
                gdf = gdf.merge(gdf_grunnkretser[['grunnkretsnummer']], on='grunnkretsnummer')
                # Compute the weight based on the area of intersection
                gdf['weight'] = gdf['intersection_area'] / gdf['area_grunnkrets']
                weight = gdf['weight']
                # Filter rows where 'weight' is 1
                filtered_df = gdf[gdf['weight'] == 1]

                agg_dict = {col: 'first' for col in columns_of_interest}
                agg_dict['grunnkretsnummer'] = lambda x: ','.join(x)
                agg_dict['weight'] = 'first' 
                # Group by 'latitude' and 'longitude' and concatenate 'code' entries
                result = filtered_df.groupby(['latitude', 'longitude']).agg(
                    agg_dict
                ).reset_index()
                filtered_df = gdf[gdf['weight'] != 1]

                # Concatenate dataframes vertically
                result = pd.concat([result, filtered_df[['latitude', 'longitude','grunnkretsnummer','weight']+columns_of_interest]], axis=0)
                result = result[columns_of_interest+['grunnkretsnummer','weight', 'longitude','latitude']]
                print('#####21121212#######')
                print(result.empty)
            else:
                gdf['geometry'] = geometries
                # apply results from first iteration
                gdf = gpd.overlay(gdf_grunnkretser[['grunnkretsnummer', 'area_grunnkrets','geometry']], gdf, how='intersection')
                gdf['weight'] = weight
                # Filter rows where 'weight' is 1
                filtered_df = gdf[gdf['weight'] == 1]

                agg_dict = {col: 'first' for col in columns_of_interest}
                agg_dict['grunnkretsnummer'] = lambda x: ','.join(x)
                agg_dict['weight'] = 'first' 
                # Group by 'latitude' and 'longitude' and concatenate 'code' entries
                tmp = filtered_df.groupby(['latitude', 'longitude']).agg(
                    agg_dict
                ).reset_index()

                filtered_df = gdf[gdf['weight'] != 1]

                # Concatenate dataframes vertically
                tmp = pd.concat([tmp, filtered_df[['latitude', 'longitude','grunnkretsnummer','weight']+columns_of_interest]], axis=0)

                # Merge the DataFrames on the 'postcode' column
                #result = pd.merge(result, tmp, on='index')
                tmp = tmp[columns_of_interest]
                result = pd.concat([result, tmp], axis=1)

            gc.collect()

        columns_of_interest =  list(result.columns.difference(['grunnkretsnummer','geometry', 'latitude', 'longitude','weight']))

        agg_dict = {col: 'sum' for col in columns_of_interest}
        agg_dict['latitude'] = 'first'
        agg_dict['longitude'] = 'first'
        agg_dict['weight'] = 'first'
        print('sum_fold: start')
        result = result.groupby('grunnkretsnummer').agg(agg_dict).reset_index()
        print('sum_fold: done')

        print('plz_fold: start')
        agg_dict2 = {'grunnkretsnummer': lambda x: ','.join(x)}
        for c in columns_of_interest:
            agg_dict2[c] = 'first'
        # Group by 'longitude', 'latitude', and 'weight' and concatenate 'code'
        result = result.groupby(['longitude', 'latitude', 'weight']).agg(
            agg_dict2
        ).reset_index()
        print('plz_fold: done')
        result.to_parquet(filename, engine="pyarrow", compression="gzip")
        print('to_parquet: done')
    
    return 1



from concurrent.futures import ThreadPoolExecutor


with ThreadPoolExecutor() as executor:
    foldersOI = [
        'C:\\code\\CLUES\\scripts\\black_carbon_aerosol_optical_depth_550nm'
    ]

    exclude_flag = [
        "China",
        "Germany",
        "UK",
    ]
    result_folder = 'res\\'
    results = list(executor.map(lambda f: worker(f, exclude_flag, result_folder), foldersOI))

print('done')
