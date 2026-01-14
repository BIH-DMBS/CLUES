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
    try:
        tiff_files = glob.glob(os.path.join(tiff_directory, '*.tif'))
    except Exception as e:
        print(f"An error occurred: {e}")
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
        except rasterio.errors.RasterioError as e:
            print(f"Rasterio error occurred while processing {tiff_file}: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    # Stack the data arrays along a new time dimension
    try:
        data_stack = np.stack(data_arrays, axis=0)
    except ValueError as e:
        if str(e) == 'need at least one array to stack':
            # Write an empty .nc file
            with nc.Dataset(output_nc_file, 'w', format='NETCDF4') as ds:
                pass  # Creating an empty netCDF file
            # Write a .txt file with the message
            with open(output_nc_file + 'txt', 'w') as txt_file:
                txt_file.write('no data available from source')
            return
        elif str(e) == 'all input arrays must have the same shape':
            print("Error: All input arrays must have the same shape.")
            return
        else:
            print(f"Unexpected error while stacking data arrays: {e}")
            return

    # Create an xarray DataArray
    try:
        data_array = xr.DataArray(data_stack, coords=[times, lat, lon], dims=['valid_time', 'latitude', 'longitude'])
    except Exception as e:
        print(f"An error occurred: {e}")
    # Set the time unit attribute
    data_array.coords['valid_time'].attrs['units'] = 'hours since 1900-01-01 00:00:00.0'
    # Create an xarray Dataset
    dataset = xr.Dataset({'variable': data_array})
    # Save the Dataset to a NetCDF file
    try:
        dataset.to_netcdf(output_nc_file)
    except Exception as e:
        print(f"An error occurred: {e}")


def get_parameter(parameters_jsonfile, bbox_jsonfile):
    # read json file that describes a geospatial datasource and parse the content so that it can be used 
    # to init the downloads 
    
    try:
        with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
            parameters = json.load(file)
    except FileNotFoundError:
        print(f"Error: The configuration file '{parameters_jsonfile}' was not found.")
        return None
    except PermissionError:
        print(f"Error: Insufficient permissions to access the file '{parameters_jsonfile}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{parameters_jsonfile}' contains invalid JSON.")
        return None

    if "start_year" in parameters:

        if parameters['type'] not in ['MODIS_Vegetation_Index_Products', 'spei_drought_index', 'Night_Time_Lights_(NTL)', 'Global_Lakes_and_Wetlands_Database_(GLWD)', 'WordSettlementFootprint3D']:
            parameters["start_year"] = datetime.fromisoformat(parameters["start_year"] + "-01-01")
            if parameters["end_year"] == "ongoing":
                parameters["end_year"] = datetime.now() - timedelta(1)
            else:
                parameters["end_year"] = datetime.fromisoformat(parameters["end_year"] + "-12-31")

            times = [time(i, 0).strftime('%H:%M') for i in range(0, 24, int(parameters["delta_t_in_h"]))]
            days = [str(i) for i in range(1, 32)]
            months = [str(i) for i in range(1, 13)]
            years = [str(i) for i in range(parameters["start_year"].year, parameters["end_year"].year)]

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

    try:
        with open(os.path.join(config_folder, bbox_jsonfile), 'r') as file:
            bbox = json.load(file)
    except FileNotFoundError:
        print(f"Error: The configuration file '{bbox_jsonfile}' was not found.")
        return None
    except PermissionError:
        print(f"Error: Insufficient permissions to access the file '{bbox_jsonfile}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{bbox_jsonfile}' contains invalid JSON.")
        return None

    if area not in bbox:
        print(f"Error: Missing required key '{area}' in bbox.")
        return None

    parameters["bbox"] = bbox[area]

    return parameters
    

def get_asset_atmosphere(json_file, year, variable):
    # use cdsapi to download data
    # check: https://ads.atmosphere.copernicus.eu/api-how-to
    print('----')
    try:
        parameters = get_parameter(json_file,'bbox.json')
        file_path = os.path.join(download_folder, parameters['source'], variable, year + '.nc')
    except Exception as e:        
        print(f"An error occurred: {e} (get_asset_atmosphere, get_parameter)")

    # Extract the directory path from the file path
    directory_path = os.path.dirname(file_path)

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # return if result file already exists
    if os.path.exists(file_path):
        return

    try:
        # Create a client for the CDS API
        file = os.path.join(secrets_folder, 'cdsapirc_atmo.sct')
        with open(file, 'r') as f:
                credentials = yaml.safe_load(f)
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        # get the client
        c = cdsapi.Client(url=credentials['url'], key=credentials['key'])
    except Exception as e:
        print(f"An error occurred: {e}")

    date = year+'-01-01/'+year+'-12-31'
    try:
        variable_dict = next((var for var in parameters["variables"] if var["name"] == variable), None)
    except Exception as e:
        print(f"An error occurred: {e}")
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
        print(f"An error occurred: {e}")

    print('file:' + file_path + ' saved')
    
    # sleep for 10 seconds to ensure that there are no conflicts with another download 
    sleep(10)



def get_asset_climate(json_file, year, variable):
    try:
        parameters = get_parameter(json_file,'bbox.json')
        file_path = os.path.join(download_folder, parameters['source'], variable, year + '.nc')
    except Exception as e:
        print(f"An error occurred: {e}")

    # Extract the directory path from the file path
    directory_path = os.path.dirname(file_path)

    if not os.path.exists(directory_path):
        try:
        # Check if the directory exists, and create it if it doesn't
            os.makedirs(directory_path)
        except Exception as e:
            print(f"An error occurred: {e}")

    # return if result file already exists
    if os.path.exists(file_path):
        return

    try:
        # Create a client for the CDS API
        file = os.path.join(secrets_folder, 'cdsapirc_climate.sct')
        with open(file, 'r') as f:
            credentials = yaml.safe_load(f)
    except Exception as e:
            print(f"An error occurred: {e}")

    try:
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
    except Exception as e:
            print(f"An error occurred: {e}")


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
        except Exception as e:
            print(f"An error occurred: {e}")
            # Create an empty file
            with open(file_path, 'w') as file:
                pass

    print('transform into netCDF'+variable['name']+ ' for year '+str(year))
    file_path = os.path.join(download_folder, parameters['source'], variable['name'],str(year)+'.nc')
    try:
        create_netcdf_from_geotiffs(data_folder,file_path)    
    except Exception as e:
            print(f"An error occurred: {e}")
    try:
        shutil.rmtree(data_folder) # delete tiffs by removing tmp folder 
    except Exception as e:
            print(f"An error occurred: {e}")
    print('download '+variable['name']+ ' for year '+str(year)+' completed')


def get_resolution(wms, layer, bbox):
    # Calculate the bounding box width and height in degrees
    bbox_width_degrees = bbox[2] - bbox[0]
    bbox_height_degrees = bbox[3] - bbox[1]

    # Convert degrees to meters (approximate)
    bbox_width_meters = bbox_width_degrees * 111320  # 1 degree ≈ 111320 meters
    bbox_height_meters = bbox_height_degrees * 111320

    # Get the MinScaleDenominator from WMS, use default if not found
    try:
        min_scale_denominator_element = wms[layer].min_scale_denominator
        min_scale_denominator = float(min_scale_denominator_element.text)
    except Exception as e:
        print(f"An error occurred: {e}")
        min_scale_denominator = 236235.119048  # Default value

    # Calculate resolution in meters per pixel
    resolution = min_scale_denominator * 0.00028  # Common WMS value

    return bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution


def get_resolution_rescale(wms, layer, bbox, max_tile_size):
    bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution = get_resolution(wms, layer, bbox)

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
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"An error occurred: {e}")

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
                try:
                    if os.path.exists(fp):  # Check if file exists
                        src = rasterio.open(fp)
                        src_files_to_mosaic.append(src)
                except Exception as e:
                    print(f"An error occurred: {e}")

            if src_files_to_mosaic:
                # Merge the rasters
                try:
                    mosaic, out_trans = merge(src_files_to_mosaic)
                except Exception as e:
                    print(f"An error occurred: {e}")
                # Copy metadata from one of the source files
                try:
                    out_meta = src_files_to_mosaic[0].meta.copy()
                    out_meta.update({
                        "driver": "GTiff",
                        "height": mosaic.shape[1],
                        "width": mosaic.shape[2],
                        "transform": out_trans
                    })
                except Exception as e:
                    print(f"An error occurred: {e}")

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
                try:
                    with rasterio.open(output_filename, "w", **out_meta) as dest:
                        dest.write(mosaic)

                    print(f"Merged {len(src_files_to_mosaic)} files into {output_filename}")
                except Exception as e:
                    print(f"An error occurred while saving the merged raster: {e}")
                # Close all source files
                try:
                    for src in src_files_to_mosaic:
                        src.close()
                except Exception as e:
                    print(f"An error occurred while closing source files: {e}")
    
    # Get the current timestamp
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flag_filename = os.path.join(output_dir, "done.txt")
    # Write the timestamp to a text file
    try:
        with open(flag_filename, "w") as file:
            file.write("Data was downloaded: ")
            file.write(current_timestamp)
    except Exception as e:
        print(f"An error occurred while writing the flag file: {e}")
        

def get_asset_wms(json_file, vOI):
    try:
        parameters = get_parameter(json_file,'bbox.json')
    except Exception as e:
        print(f"An error occurred: {e}")
    try:
        for v in parameters['variables']:
            if v['name']==vOI:
                variable = v
                layer = v['layer']
                break
    except Exception as e:
        print(f"An error occurred: {e}")
    
    if parameters['type'] == 'wms_multiserver': 
        # download copernicus land else: eoc_land_map
        url = variable['url']
        name = variable['name']
    elif parameters['type'] == 'wms':
        url = parameters["link"] 
        name = [variable['name']]
    
    output_dir = os.path.join(download_folder, parameters['source'], variable['name'])
    
    try:
        wms = WebMapService(url, version='1.3.0')
    except Exception as e:
        print(f"An error occurred while connecting to WMS: {e}")
        return
    
    # Define the maximum tile size: toDo shift to config source file
    max_tile_size = 4000

    bbox = [parameters['bbox'][i] for i in [1,2,3,0]] # copernicus and eoc use a different order of bbox parameters['bbox'],
    print(bbox)
    bbox = resize_bbox(wms, bbox, max_tile_size)
    print(bbox)

    bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution = get_resolution(wms, layer, bbox, max_tile_size)
  
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
    try:
        merge_neighborhood(num_tiles_x, num_tiles_y, tmp_dir , output_dir, variable['name'])
    except Exception as e:
        print(f"An error occurred while merging neighborhood: {e}")
    try:
        shutil.rmtree(tmp_dir)
    except Exception as e:
        print(f"An error occurred while removing temporary directory: {e}")


def copenicus_corine(json_file, vOI):
    # download coperbnicus corine
    try:
        parameters = get_parameter(json_file,'bbox.json')
    except Exception as e:
        print(f"An error occurred: {e}")
    # check if vOI is in parameters
    if vOI not in [v['name'] for v in parameters['variables']]:
        print(f"Variable {vOI} not found in parameters.")
        return
    for v in parameters['variables']:
        if v['name']==vOI:
            wms_url = v['url']
            layer = v['layer']
            layer_name = v['name']
            break

    # Define the WMS URL and layer name
    try:
        wms = WebMapService(wms_url, version='1.3.0')
    except Exception as e:
        print(f"An error occurred while connecting to WMS: {e}")
        return
    # the bbox must be reordered for this service
    bbox = [parameters['bbox'][i] for i in [1,2,3,0]] # copernicus and eoc use a different order of bbox parameters['bbox'],
    
    try:
        bbox_width_degrees, bbox_height_degrees, bbox_width_meters, bbox_height_meters, resolution = get_resolution(wms, layer, bbox)
    except Exception as e:
        print(f"An error occurred while getting resolution: {e}")
        return

    # Calculate the image width and height in pixels
    width = int(bbox_width_meters / resolution)
    height = int(bbox_height_meters / resolution)

    # Define the maximum tile size: toDo shift to config source file
    max_tile_size = 1024

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
    try:
        os.makedirs(tmp_dir, exist_ok=True)
    except Exception as e:
        print(f"An error occurred while creating temporary directory: {e}")
        return
    # Download each tile and paste it into the final image
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            png_file = os.path.join(tmp_dir,f'result{i,j}.png')
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
            tile_height =int( bbox_height_meters / resolution)
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
                    try:
                        with open(png_file, 'wb') as f:
                            f.write(map_request.read())
                    except Exception as e:
                        print(f"An error occurred while writing PNG file: {e}")
                        return    
                    # Open the PNG file
                    with Image.open(png_file) as img:
                        img_array = np.array(img)
                    try:
                        transform = rasterio.transform.from_bounds(
                            *tile_bbox, width=tile_width, height=tile_height
                            )
                    except Exception as e:
                        print(f"An error occurred while creating transform: {e}")
                        return
                    # Save as GeoTIFF
                    geotiff_file = os.path.join(tmp_dir, f"{i}_{j}_result.tif")
                    geotiff_files.append(geotiff_file)
                    try:
                        with rasterio.open(
                            geotiff_file, 'w', driver='GTiff',
                            height=tile_height, width=tile_width,
                            count=3, dtype=img_array.dtype,
                            crs='EPSG:4326', transform=transform
                        ) as dst:
                            try:
                                if img_array.ndim == 2:
                                    # Write the same band 3 times
                                    for k in range(1, 4):
                                        dst.write(img_array, k)
                                else:
                                    # RGB image
                                    for k in range(1, 4):
                                        dst.write(img_array[:, :, k-1], k)
                            except Exception as e:
                                print(f"An error occurred: {e}")
                    except Exception as e:
                        print(f"An error occurred while writing GeoTIFF file: {e}")
                        return
                    try:
                        os.remove(png_file)
                    except Exception as e:
                        print(f"An error occurred while removing PNG file: {e}")
                        return
                break

    # Open all GeoTIFF files
    try:
        src_files_to_mosaic = []
        for fp in geotiff_files:
            src = rasterio.open(fp)
            src_files_to_mosaic.append(rasterio.open(fp))
    except Exception as e:
        print(f"An error occurred while opening GeoTIFF files: {e}")
        return

    try:
        # Merge the GeoTIFF files
        mosaic, out_trans = merge(src_files_to_mosaic)
    except Exception as e:
        print(f"An error occurred while merging GeoTIFF files: {e}")
        return

    try:
        # Update the metadata
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "crs": src.crs
        })
    except Exception as e:
        print(f"An error occurred while updating metadata: {e}")
        return

    try:
        # Save the merged GeoTIFF
        file_path = os.path.join(download_folder, parameters['type'], layer_name +'.tif')
        with rasterio.open(file_path, "w", **out_meta) as dest:
            dest.write(mosaic)
            print(f"Merged GeoTIFF saved as {file_path}")
    except Exception as e:
        print(f"An error occurred while saving the merged GeoTIFF: {e}")
        return
    try:
        # Close all source files
        for src in src_files_to_mosaic:
            src.close()
    except Exception as e:
        print(f"An error occurred while closing source files: {e}")
        return
    try:   
        for geotiff_file in geotiff_files:
            os.remove(geotiff_file)
            print(f"Temporary file {geotiff_file} removed.")
    except Exception as e:
        print(f"An error occurred while removing temporary files: {e}")
        return


def spei_download(json_file,variableOI):
    # download drougth data
    try:
        parameter = get_parameter(json_file,'bbox.json')
        variableOI = int(variableOI)
        urls = parameter['variables'][0]['urls']
        url = [url for url in urls if f"spei{variableOI:02}.nc" in url]
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    try:
        response = requests.get(url[0])
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the file: {e}")
        return
    file_path_tmp = os.path.join(download_folder, parameter['type'], str(variableOI) +'_tmp.nc')
    file_path = os.path.join(download_folder, parameter['type'], str(variableOI) +'.nc')
    
    if response.status_code == 200:
        try:
            with open(file_path_tmp, 'wb') as file:
                file.write(response.content)

            # Open, process, and close the dataset using `with` to ensure closure
            with xr.open_dataset(file_path_tmp) as ds:
                ds_spei_harmonized = rename_coords(ds)  # Rename coordinates
                ds_spei_harmonized.to_netcdf(file_path)  # Save final dataset
            # Save harmonized datasets
            os.remove(file_path_tmp)
            print(f"File downloaded and saved as {file_path}")
        except Exception as e:
            print(f"An error occurred while processing the file: {e}")


def get_simple_download_zip(json_file):
    # simple download of a zip file as for night time lights
    # after download extract the zip file content
    try:
        parameter = get_parameter(json_file,'bbox.json')
        url = parameter['variables'][0]['url']
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    # URL of the zip file

    # Download the zip file
    file_path = os.path.join(download_folder, parameter['type'])
    # Create the directory if it does not exist
    try:
        os.makedirs(file_path, exist_ok=True)
    except Exception as e:
        print(f"An error occurred while creating the directory: {e}")
        return

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    })

    for _ in range(60):
        r = session.get(url, stream=True)
        
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("application"):
            print("Download ready!")
            break
        
        print("Waiting for Figshare to prepare file...")
        time.sleep(1)
    else:
        raise TimeoutError("Figshare did not provide the file")

    # Step 2: Stream the actual file with progress
    total = int(r.headers.get("Content-Length", 0))
    downloaded = 0
    chunks = []

    for i, chunk in enumerate(r.iter_content(chunk_size=16*1024*1024)):
        if chunk:
            chunks.append(chunk)
            downloaded += len(chunk)
            percent = downloaded * 100 / total if total else 0
            if i % 5 == 0:  # print every 5 chunks
                downloaded_mb = (i+1)*16
                print(f"\rDownloaded ~{downloaded_mb} MB", end="")

    try:
        content = b"".join(chunks)
        zip_file = zipfile.ZipFile(io.BytesIO(content))
        print("\nZIP opened successfully")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the zip file: {e}")
        return
    except zipfile.BadZipFile as e:
        print(f"An error occurred while reading the zip file: {e}")
        return

    try:
        # Extract the contents of the zip file
        zip_file.extractall(file_path)
        print(f"Zip file downloaded and extracted to {file_path}")
    except Exception as e:
        print(f"An error occurred while extracting the zip file: {e}")
        return

    print('NTL download done.')


def get_simple_download_tif(json_file, vOI):
    # download directly the files of interst from source
    try:
        parameters = get_parameter(json_file,'bbox.json')
        for v in parameters['variables']:
            if v['name']==vOI:
                parameters['variables'] = v
                break
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    try:
        # Send a HTTP request to the URL
        url = parameters['variables']['url']
        response = requests.get(url)
    except Exception as e:
        print(f"An error occurred: {e}")
        return
        
    # Save the content of the response as a file
    file_path = os.path.join(download_folder, parameters['type'],parameters['variables']['name']+'.tif')
    try:
        with open(file_path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")
        return

    print("The GeoTIFF file has been downloaded and saved as '" + parameters['variables']['name']+'.tif' +"'.")

def get_bbox(bbox_jsonfile):
    parameters = {}

    try:
        with open(os.path.join(config_folder, bbox_jsonfile), 'r') as file:
            bbox = json.load(file)
    except FileNotFoundError:
        print(f"Error: The configuration file '{bbox_jsonfile}' was not found.")
        return None
    except PermissionError:
        print(f"Error: Insufficient permissions to access the file '{bbox_jsonfile}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{bbox_jsonfile}' contains invalid JSON.")
        return None

    if area not in bbox:
        print(f"Error: Missing required key '{area}' in bbox.")
        return None

    parameters["bbox"] = bbox[area]

    return parameters