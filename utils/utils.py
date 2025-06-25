import cdsapi
import glob
import json
import netCDF4 as nc
import numpy as np
import os
import rasterio
import rioxarray
import shutil
import xarray as xr
import yaml
import requests
import zipfile
import io
import math

from time import sleep
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from rasterio.transform import from_origin
from owslib.wms import WebMapService
from PIL import Image
from rasterio.merge import merge


try:
    from .config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder
except:
    from config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder



# Function to rename coordinates
def rename_coords(ds):
    rename_dict = {}

    # Time coordinate
    if "time" in ds.coords:
        rename_dict["time"] = "valid_time"

    # Latitude coordinate
    if "lat" in ds.coords:
        rename_dict["lat"] = "latitude"
    elif "Latitude" in ds.coords:
        rename_dict["Latitude"] = "latitude"

    # Longitude coordinate
    if "lon" in ds.coords:
        rename_dict["lon"] = "longitude"
    elif "Longitude" in ds.coords:
        rename_dict["Longitude"] = "longitude"

    # Rename and return
    return ds.rename(rename_dict)


def create_netcdf_from_geotiffs(tiff_directory, output_nc_file):
    # given a folder that contains geoTiff files merge them all together in one netCDF file
    # List all GeoTIFF files in the directory
    tiff_files = glob.glob(os.path.join(tiff_directory, '*.tif'))

    # Initialize lists to store data, times, and coordinates
    data_arrays = []
    times = []
    lat = None
    lon = None
    time_units = 'hours since 2000-01-01 00:00:00'
    calendar = 'standard'

    # Read each GeoTIFF file
    for tiff_file in tiff_files:
        try:
            with rasterio.open(tiff_file) as src:
                # Extract data
                data = src.read(1)  # Assuming the data is in the first band
                # Extract coordinates
                if lat is None or lon is None:
                    lat, lon = src.read(1).shape
                    lat = np.linspace(src.bounds.top, src.bounds.bottom, lat)
                    lon = np.linspace(src.bounds.left, src.bounds.right, lon)
                # Extract time from filename or metadata
                date_to_convert = os.path.basename(tiff_file).split('.')[0]  # Adjust as needed to extract time
                date_to_convert = datetime.strptime(date_to_convert, '%Y-%m-%dT%H-%M-%SZ')
                reference_date = datetime(1900, 1, 1, 0, 0, 0)
                # Calculate the difference in hours
                difference = date_to_convert - reference_date
                hours_since_reference = difference.total_seconds() / 3600
                times.append(hours_since_reference)
                # Append the data array
                data_arrays.append(data)
        except:
            pass

    # Stack the data arrays along a new time dimension
    try:
        data_stack = np.stack(data_arrays, axis=0)
    except ValueError as e: #if all tiffs are empty
        if str(e) == 'need at least one array to stack':
            # Write an empty .nc file
            with nc.Dataset(output_nc_file, 'w', format='NETCDF4') as ds:
                pass  # Creating an empty netCDF file
            # Write a .txt file with the message
            with open(output_nc_file+'txt', 'w') as txt_file:
                txt_file.write('no data available from source')
            return

    # Create an xarray DataArray
    data_array = xr.DataArray(data_stack, coords=[times, lat, lon], dims=['valid_time', 'latitude', 'longitude'])
    # Set the time unit attribute
    data_array.coords['valid_time'].attrs['units'] = 'hours since 1900-01-01 00:00:00.0'
    # Create an xarray Dataset
    dataset = xr.Dataset({'variable': data_array})
    # Save the Dataset to a NetCDF file
    dataset.to_netcdf(output_nc_file)


def get_parameter(parameters_jsonfile, bbox_jsonfile):
    # read json file that describes a geospatial datasource and parse the content so that it can be used 
    # to init the downloads 
     
    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
        parameters = json.load(file)
    if "start_year" in parameters:
        #if (parameters['type'] != 'MODIS Vegetation Index Products') and (parameters['type'] != 'spei_drought_index') and (parameters['type'] != 'Night_Time_Lights_(NTL)') and (parameters['type'] != 'Global_Lakes_and_Wetlands_Database_(GLWD)'): #cdsapi sources (if not wms or wcs is used)
        if parameters['type'] not in ['MODIS Vegetation Index Products','spei_drought_index','Night_Time_Lights_(NTL)', 'Global_Lakes_and_Wetlands_Database_(GLWD)','WordSettlementFootprint3D']: #cdsapi sources (if not wms or wcs is used)
            parameters["start_year"] = datetime.fromisoformat(parameters["start_year"] + "-01-01")
            if parameters["end_year"] == "ongoing":
                parameters["end_year"] = datetime.now() - timedelta(1)
            else:
                parameters["end_year"] = datetime.fromisoformat(parameters["end_year"] + "-12-31")
            
            times = [time(i, 0).strftime('%H:%M') for i in range(0, 24, int(parameters["delta_t_in_h"]))]
            days =  [str(i) for i in range(1,31)]
            months = [str(i) for i in range(1,13)]
            years = [str(i) for i in range(parameters["start_year"].year,parameters["end_year"].year)]

            parameters["times"] = times
            parameters["days"] = days
            parameters["months"] = months
            parameters["years"] = years

    for v in parameters['variables']:
        if 'temporal_dimension' in v.keys():
            # Parse the interval string
            start_str, end_str, period_str = v['temporal_dimension'].split('/')

            # Convert start and end strings to datetime objects
            start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))

            # Calculate the interval
            if period_str == 'P1D':
                delta = timedelta(days=1)
            elif period_str == 'P1M':
                delta = relativedelta(months=1)
            else:
                raise ValueError("Unsupported period format")

            # Generate the list of dates
            current_date = start_date
            date_list = []

            while current_date <= end_date:
                date_list.append(current_date.isoformat().replace('+00:00', 'Z'))
                current_date += delta 
            v['date_list'] = date_list

    with open(os.path.join(config_folder, bbox_jsonfile), 'r') as file:
        bbox = json.load(file)

    parameters["bbox"] = bbox[area]

    return parameters


def get_asset_atmosphere(json_file, year, variable):
    # use cdsapi to download data
    # check: https://ads.atmosphere.copernicus.eu/api-how-to
    parameters = get_parameter(json_file,'bbox.json')
    file_path = os.path.join(download_folder, parameters['source'], variable, year + '.nc')

    # Extract the directory path from the file path
    directory_path = os.path.dirname(file_path)

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # return if result file already exists
    if os.path.exists(file_path):
        return

    # Create a client for the CDS API
    file = os.path.join(secrets_folder, 'cdsapirc_atmo.sct')

    with open(file, 'r') as f:
            credentials = yaml.safe_load(f)

    # get the credentials
    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])
    date = year+'-01-01/'+year+'-12-31'
    variable_dict = next((var for var in parameters["variables"] if var["name"] == variable), None)
    # model_level is present for assets that can be monitored at different altitudes
    try:
        if 'model_level' in variable_dict:
            c.retrieve(
                parameters['source'],
                {
                    'format': parameters['format'],
                    'variable':variable,
                    'model_level': variable_dict['model_level'],
                    'date': date,
                    'time': parameters['times'],
                    'area': parameters['bbox'],
                },
                file_path)
        else:
            c.retrieve(
                parameters['source'],
                {
                    'format': parameters['format'],
                    'variable':variable,
                    'date': date,
                    'time': parameters['times'],
                    'area': parameters['bbox'],
                },
                file_path)
    except Exception as e:
        # Print the exception
        if "Request has not produced a valid combination of values, please check your selection." in str(e):            
            with open(file_path, 'a') as file:
                file.write(f"An error occurred: {e}\n")
            
            file_path_err = file_path+'.error'
            with open(file_path_err, 'a') as file:
                file.write(f"An error occurred: {e}\n")


        print(f"An error occurred: {e}")

    print('file:' + file_path + ' saved')
    
    sleep(10)
    print('10 seconds passed!!!!!!!!!')



def get_asset_climate(json_file, year, variable):
    parameters = get_parameter(json_file,'bbox.json')
    file_path = os.path.join(download_folder, parameters['source'], variable, year + '.nc')

    # Extract the directory path from the file path
    directory_path = os.path.dirname(file_path)

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # return if result file already exists
    if os.path.exists(file_path):
        return
    
    # Create a client for the CDS API
    file = os.path.join(secrets_folder, 'cdsapirc_climate.sct')

    with open(file, 'r') as f:
            credentials = yaml.safe_load(f)

    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

    c.retrieve(
        parameters['source'],
        {
            'product_type': 'reanalysis',
            'format': parameters['format'],
            'year': year,
            'month': parameters['months'],
            'day': parameters['days'],
            'time': parameters['times'],
            'area': parameters['bbox'],
            'variable': [variable],
        },
        file_path)


def connect_wms(url, version='1.3.0', retries=3, delay=5):
    """
    Tries to connect to a WMS server, with retries if the connection fails.

    :param url: The WMS URL
    :param version: WMS version to use (default: 1.3.0)
    :param retries: Number of times to retry
    :param delay: Delay between retries in seconds
    :return: WebMapService object if successful, None otherwise
    """
    attempt = 0
    while attempt < retries:
        try:
            print(f"Connecting to WMS (Attempt {attempt + 1})...")
            wms = WebMapService(url, version=version)
            print("Connection successful.")
            return wms
        except Exception as e:
            print(f"Connection failed: {e}")
            attempt += 1
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                sleep(delay)
            else:
                print("All connection attempts failed.")
    return None


def get_asset_wms_year(json_file, variableOI, year):
    # download time resolved data via WebMapService (currently for geoservice.dlr.de)
    # and save as netcdf
    parameters = get_parameter(json_file,'bbox.json')
    for v in parameters['variables']:
        if v['name']==variableOI:
            variable = v
            break
    url = parameters["link"]
    wms = connect_wms(url)#wms = WebMapService(url, version='1.3.0')
    
    data_folder = os.path.join(download_folder, parameters['source'], variable['name'],str(year))
    datesOI = [date for date in variable['date_list'] if datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').year == year]
    for date in datesOI:
        # download tiff for date and store in temp folder
        variable['dateOI'] = date
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        file_path = os.path.join(data_folder, variable['dateOI'].replace(':', '-') +'.tif')
        # continue if result file already exists
        if os.path.exists(file_path):
            print('tif exists:' + file_path)
            continue
        try:
            map_request = wms.getmap(
            layers = [variable['name']],
            srs = parameters['crs'],
            bbox = [parameters['bbox'][i] for i in [1,2,3,0]], # copernicus and eoc use a different order of bbox parameters['bbox'],
            size = (variable['width'],variable['height']),
            format = parameters['format'],
            time = variable['dateOI']
            )
            with open(file_path, 'wb') as f:
                f.write(map_request.read())
        except:
            # Create an empty file
            with open(file_path, 'w') as file:
                pass

    print('transform into netCDF'+variable['name']+ ' for year '+str(year))
    file_path = os.path.join(download_folder, parameters['source'], variable['name'],str(year)+'.nc')
    #file_path_tmp = os.path.join(download_folder, parameters['source'], variable['name'],str(year)+'_tmp.nc')
    create_netcdf_from_geotiffs(data_folder,file_path)
    shutil.rmtree(data_folder) # delete tiffs by removing tmp folder 
    print('download '+variable['name']+ ' for year '+str(year)+' completed')

    #with xr.open_dataset(file_path_tmp) as ds:
    #    ds_eoc_harmonized = rename_coords(ds)  # Rename coordinates
    #    ds_eoc_harmonized.to_netcdf(file_path)  # Save final dataset

    #os.remove(file_path_tmp)


'''
def get_asset_wms(json_file, vOI):
    parameters = get_parameter(json_file,'bbox.json')
    for v in parameters['variables']:
        if v['name']==vOI:
            variable = v
            break
    
    if parameters['type'] == 'wms_multiserver': 
        # download copernicus land else: eoc_land_map
        url = variable['url']
        name = variable['name']
    elif parameters['type'] == 'wms':
        url = parameters["link"] 
        name = [variable['name']]
    

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(os.path.join(download_folder, parameters['source'])):
        os.makedirs(os.path.join(download_folder, parameters['source']))
    file_path = os.path.join(download_folder, parameters['source'], variable['name'] +'.tif')
    if os.path.exists(file_path):
        print('tif exists')
        return
    wms = WebMapService(url, version='1.3.0')
    map_request = wms.getmap(
        layers=[variable['name']],
        srs=parameters['crs'],
        bbox = [parameters['bbox'][i] for i in [1,2,3,0]], # copernicus and eoc use a different order of bbox parameters['bbox'],
        size = (4000,4000),
        #size = (variable['width'],variable['height']),
        format=parameters['format'],
    )
    
    with open(file_path, 'wb') as f:
        f.write(map_request.read())
'''

def get_resolution(wms, bbox):
    # Calculate the bounding box width and height in degrees
    bbox_width_degrees = bbox[2] - bbox[0]
    bbox_height_degrees = bbox[3] - bbox[1]

    # Convert degrees to meters (approximate)
    bbox_width_meters = bbox_width_degrees * 111320  # 1 degree ≈ 111320 meters
    bbox_height_meters = bbox_height_degrees * 111320

    # Get the MinScaleDenominator from WMS, use default if not found
    try:
        min_scale_denominator_element = wms[variable['name']].min_scale_denominator
        min_scale_denominator = float(min_scale_denominator_element.text)
    except:
        min_scale_denominator = 236235.119048  # Default value

    # Calculate resolution in meters per pixel
    resolution = min_scale_denominator * 0.00028  # Common WMS value

    return bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution


def get_resolution_rescale(wms, bbox, max_tile_size):
    bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution = get_resolution(wms, bbox)

    # Compute original image size in pixels
    width_pixels = bbox_width_meters / resolution
    height_pixels = bbox_height_meters / resolution

    # Round up to the nearest multiple of max_tile_size
    new_width_pixels = math.ceil(width_pixels / max_tile_size) * max_tile_size
    new_height_pixels = math.ceil(height_pixels / max_tile_size) * max_tile_size

    # Convert back to meters
    new_bbox_width_meters = new_width_pixels * resolution
    new_bbox_height_meters = new_height_pixels * resolution

    # Convert back to degrees
    new_bbox_width_degrees = new_bbox_width_meters / 111320
    new_bbox_height_degrees = new_bbox_height_meters / 111320

    return bbox_width_degrees, bbox_height_degrees, new_bbox_width_degrees, new_bbox_height_degrees

def resize_bbox(wms, bbox, max_tile_size):
    
    bbox_width_degrees, bbox_height_degrees, new_bbox_width_degrees, new_bbox_height_degrees = get_resolution_rescale(wms, bbox, max_tile_size)

    # Adjust the bounding box by expanding equally in all directions
    expand_x = (new_bbox_width_degrees - bbox_width_degrees) / 2
    expand_y = (new_bbox_height_degrees - bbox_height_degrees) / 2

    new_bbox = [
        bbox[0] - expand_x,  # minX
        bbox[1] - expand_y,  # minY
        bbox[2] + expand_x,  # maxX
        bbox[3] + expand_y   # maxY
    ]
    return new_bbox


def merge_neighborhood(num_rows, num_cols, input_dir ,output_dir, name):
    # Define input directory and output directory
    os.makedirs(output_dir, exist_ok=True)

    # Function to get neighboring files
    def get_neighbors(i, j):
        neighbors = [
            f"{i+di}_{j+dj}_result.tif" for di in range(3) for dj in range(3)
            if 0 <= i+di < num_rows and 0 <= j+dj < num_cols  # Ensure valid indices
        ]
        return [os.path.join(input_dir, f) for f in neighbors]

    # Iterate through the grid with a step of 3 (to avoid overlap)
    for i in range(0, num_rows, 3):
        for j in range(0, num_cols, 3):
            files_to_merge = get_neighbors(i, j)

            # Open the raster files
            src_files_to_mosaic = []
            for fp in files_to_merge:
                if os.path.exists(fp):  # Check if file exists
                    src = rasterio.open(fp)
                    src_files_to_mosaic.append(src)

            if src_files_to_mosaic:
                # Merge the rasters
                mosaic, out_trans = merge(src_files_to_mosaic)

                # Copy metadata from one of the source files
                out_meta = src_files_to_mosaic[0].meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans
                })

                # Extract raster properties
                min_x = out_trans.c  # Top-left x (same as min_x)
                max_y = out_trans.f  # Top-left y
                pixel_height = out_trans.e  # Should be negative

                # Calculate the lower-left y coordinate
                min_y = max_y + (mosaic.shape[1] * pixel_height)

                # Format and update filename
                output_filename = os.path.join(output_dir, f"{min_x:.2f}_{min_y:.2f}_{name}.tif")

                print("Lower-left coordinates:", min_x, min_y)

                # Save merged raster
                with rasterio.open(output_filename, "w", **out_meta) as dest:
                    dest.write(mosaic)

                print(f"Merged {len(src_files_to_mosaic)} files into {output_filename}")

                # Close all source files
                for src in src_files_to_mosaic:
                    src.close()
    from datetime import datetime

    # Get the current timestamp
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flag_filename = os.path.join(output_dir, "done.txt")
    # Write the timestamp to a text file
    with open(flag_filename, "w") as file:
        file.write("Data was downloaded: ")
        file.write(current_timestamp)


def get_asset_wms(json_file, vOI):
    
    parameters = get_parameter(json_file,'bbox.json')
    print(vOI)
    for v in parameters['variables']:
        if v['name']==vOI:
            variable = v
            break
    print(parameters)
    print(variable)

    if parameters['type'] == 'wms_multiserver': 
        # download copernicus land else: eoc_land_map
        url = variable['url']
        name = variable['name']
    elif parameters['type'] == 'wms':
        url = parameters["link"] 
        name = [variable['name']]
    
    output_dir = os.path.join(download_folder, parameters['source'], variable['name'])
    
    wms = WebMapService(url, version='1.3.0')
    
    # Define the maximum tile size: toDo shift to config source file
    max_tile_size = 4000

    bbox = [parameters['bbox'][i] for i in [1,2,3,0]] # copernicus and eoc use a different order of bbox parameters['bbox'],
    print(bbox)
    bbox = resize_bbox(wms, bbox, max_tile_size)
    print(bbox)

    bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution = get_resolution(wms, bbox, max_tile_size)
  
    # Calculate the image width and height in pixels
    width = int(bbox_width_meters / resolution)
    height = int(bbox_height_meters / resolution)

    # Calculate the number of tiles needed
    num_tiles_x = int(np.ceil(width / max_tile_size))
    num_tiles_y = int(np.ceil(height / max_tile_size))
    # **end max resolution download defintion

    # Create an empty image to hold the final result
    final_image = Image.new('RGB', (width, height))
    geotiff_files = []
    max_retries = 20

    tmp_dir = f'tmp_{name}'
    os.makedirs(tmp_dir, exist_ok=True)
    # Download each tile and paste it into the final image
    
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            tile_bbox = [
                bbox[0] + i * (bbox_width_degrees / num_tiles_x),
                bbox[1] + j * (bbox_height_degrees / num_tiles_y),
                bbox[0] + (i + 1) * (bbox_width_degrees / num_tiles_x),
                bbox[1] + (j + 1) * (bbox_height_degrees / num_tiles_y)
            ]
            # Calculate the bounding box width in meter
            bbox_width_meters = (tile_bbox[2] - tile_bbox[0]) * 111320 
            bbox_height_meters = (tile_bbox[3] - tile_bbox[1]) * 111320 
            tile_width = int(bbox_width_meters / resolution)
            tile_height = int(bbox_height_meters / resolution)
            print(tile_bbox)
            retry_count = 0
            while retry_count < max_retries:
                map_request = wms.getmap(
                    layers=[variable['name']],
                    srs=parameters['crs'],
                    bbox=tile_bbox,
                    size=(tile_width, tile_height),
                    format=parameters['format'],
                )
                if map_request._response.status_code != 200:
                    print('response.status_code')
                    print(map_request._response.status_code)
                    retry_count += 1
                    sleep(1)  # Wait for 1 second before retrying
                    print('retry')
                else:
                    print(map_request._response.status_code)
                    geotiff_file = os.path.join(tmp_dir, f"{i}_{j}_result.tif")
                    geotiff_files.append(geotiff_file)
                    with open(geotiff_file, 'wb') as f:
                        f.write(map_request.read())
                    break
    
    merge_neighborhood(num_tiles_x, num_tiles_y, tmp_dir , output_dir, variable['name'])
    shutil.rmtree(tmp_dir)


def copenicus_corine(json_file, vOI):
    # download coperbnicus corine
    parameters = get_parameter(json_file,'bbox.json')
    for v in parameters['variables']:
        if v['name']==vOI:
            wms_url = v['url']
            layer = v['layer']
            layer_name = v['name']
            break

    wms = WebMapService(wms_url, version='1.3.0')
    # the bbox must be reordered for this service
    bbox = [parameters['bbox'][i] for i in [1,2,3,0]] # copernicus and eoc use a different order of bbox parameters['bbox'],
    
    bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution = get_resolution(wms, bbox)

    # Calculate the image width and height in pixels
    width = int(bbox_width_meters / resolution)
    height = int(bbox_height_meters / resolution)

    # Define the maximum tile size: toDo shift to config source file
    max_tile_size = 4000

    # Calculate the number of tiles needed
    num_tiles_x = int(np.ceil(width / max_tile_size))
    num_tiles_y = int(np.ceil(height / max_tile_size))
    # **end max resolution download defintion

    # Create an empty image to hold the final result
    final_image = Image.new('RGB', (width, height))
    geotiff_files = []
    max_retries = 20
    tmp_dir = os.path.join(tmp_folder,f'tmp_{vOI}')
    png_file = os.path.join(tmp_dir,'result.png')
    os.makedirs(tmp_dir, exist_ok=True)
    # Download each tile and paste it into the final image
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            tile_bbox = [
                bbox[0] + i * (bbox_width_degrees / num_tiles_x),
                bbox[1] + j * (bbox_height_degrees / num_tiles_y),
                bbox[0] + (i + 1) * (bbox_width_degrees / num_tiles_x),
                bbox[1] + (j + 1) * (bbox_height_degrees / num_tiles_y)
            ]
            # Calculate the bounding box width in meter
            bbox_width_meters = (tile_bbox[2] - tile_bbox[0]) * 111320 
            bbox_height_meters = (tile_bbox[3] - tile_bbox[1]) * 111320 
            tile_width = bbox_width_meters / resolution
            tile_height = bbox_height_meters / resolution
            print(tile_bbox)
            retry_count = 0
            while retry_count < max_retries:
                map_request = wms.getmap(
                    layers=[layer],
                    srs="EPSG:4326",
                    bbox=tile_bbox,
                    size=(tile_width, tile_height),
                    format="image/png",
                )
                if map_request._response.status_code != 200:
                    print('response.status_code')
                    print(map_request._response.status_code)
                    retry_count += 1
                    sleep(1)  # Wait for 1 second before retrying
                    print('retry')
                else:
                    with open(png_file, 'wb') as f:
                        f.write(map_request.read())
                    # Open the PNG file
                    with Image.open(png_file) as img:
                        img_array = np.array(img)       
                    transform = rasterio.transform.from_bounds(
                            *tile_bbox, width=tile_width, height=tile_height
                        )
                    # Save as GeoTIFF
                    geotiff_file = os.path.join(tmp_dir, f"{i}_{j}_result.tif")
                    geotiff_files.append(geotiff_file)
                    with rasterio.open(
                        geotiff_file, 'w', driver='GTiff',
                        height=tile_height, width=tile_width,
                        count=3, dtype=img_array.dtype,
                        crs='EPSG:4326', transform=transform
                    ) as dst:
                        for k in range(1, 4):
                            dst.write(img_array[:, :, k-1], k)
                    os.remove(png_file)
                break

    # Open all GeoTIFF files
    src_files_to_mosaic = []
    for fp in geotiff_files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(rasterio.open(fp))

    # Merge the GeoTIFF files
    mosaic, out_trans = merge(src_files_to_mosaic)

    # Update the metadata
    out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": src.crs
    })

    # Save the merged GeoTIFF
    file_path = os.path.join(download_folder, parameters['type'], layer_name +'.tif')
    with rasterio.open(file_path, "w", **out_meta) as dest:
        dest.write(mosaic)

    # Close all source files
    for src in src_files_to_mosaic:
        src.close()
    
    for geotiff_file in geotiff_files:
        os.remove(geotiff_file)
         #print(f"Merged GeoTIFF saved as {output_file}")


def spei_download(json_file,variableOI):
    # download drougth data
    parameter = get_parameter(json_file,'bbox.json')
    variableOI = int(variableOI)
    urls = parameter['variables'][0]['urls']
    url = [url for url in urls if f"spei{variableOI:02}.nc" in url]
    response = requests.get(url[0])
    file_path_tmp = os.path.join(download_folder, parameter['type'], str(variableOI) +'_tmp.nc')
    file_path = os.path.join(download_folder, parameter['type'], str(variableOI) +'.nc')
    if response.status_code == 200:
        with open(file_path_tmp, 'wb') as file:
            file.write(response.content)

        # Open, process, and close the dataset using `with` to ensure closure
        with xr.open_dataset(file_path_tmp) as ds:
            ds_spei_harmonized = rename_coords(ds)  # Rename coordinates
            ds_spei_harmonized.to_netcdf(file_path)  # Save final dataset
        # Save harmonized datasets
        os.remove(file_path_tmp)


def get_simple_download_zip(json_file):
    # simple download of a zip file as for night time lights
    # after download extract the zip file content
    parameter = get_parameter(json_file,'bbox.json')
    # URL of the zip file
    url = parameter['variables'][0]['url']

    # Download the zip file
    file_path = os.path.join(download_folder, parameter['type'])
    response = requests.get(url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    # Extract the contents of the zip file
    zip_file.extractall(file_path)
    print('NTL down')


def get_simple_download_tif(json_file, vOI):
    # download directly ti files of interst from source
    parameters = get_parameter(json_file,'bbox.json')
    print(parameters)
    for v in parameters['variables']:
        if v['name']==vOI:
            parameters['variables'] = v
            break
    print(parameters['variables'])
    # Send a HTTP request to the URL
    url = parameters['variables']['url']
    response = requests.get(url)
    
    # Save the content of the response as a file
    file_path = os.path.join(download_folder, parameters['type'],parameters['variables']['name']+'.tif')
    with open(file_path, 'wb') as f:
        f.write(response.content)

    print("The GeoTIFF file has been downloaded and saved as '" + parameters['variables']['name']+'.tif' +"'.")