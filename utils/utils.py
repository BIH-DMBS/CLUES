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
import hashlib
import math
import calendar

from time import sleep
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from rasterio.transform import from_origin
from owslib.wms import WebMapService
from PIL import Image
from rasterio.merge import merge
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds


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
    

def pad_bbox(bbox, margin):
    """
    Widen a bounding box [lat_max, lon_min, lat_min, lon_max] by `margin` degrees on every side.

    Gridded sources only deliver the grid cells that lie inside the requested area. Without a margin,
    a location close to the border of the area is linked to a cell further inside, although its true
    nearest cell lies just outside. A margin of one grid step avoids this.
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    return [
        round(min(90.0, lat_max + margin), 4),
        round(max(-180.0, lon_min - margin), 4),
        round(max(-90.0, lat_min - margin), 4),
        round(min(180.0, lon_max + margin), 4),
    ]


def extract_single_netcdf(zip_path, target_path):
    # the data stores deliver netCDF as a zip archive, here exactly one netCDF file is expected in it
    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.namelist() if m.endswith('.nc')]
        if len(members) != 1:
            raise RuntimeError(f"Expected exactly one netCDF file in {zip_path}, found: {z.namelist()}")
        with z.open(members[0]) as src, open(target_path, 'wb') as dst:
            shutil.copyfileobj(src, dst)


def check_time_axis(nc_file, year, delta_t_in_h):
    """
    Check the time axis of a downloaded yearly netCDF file.

    Raises an error if the file holds no time steps or time steps of another year.
    Returns (number of time steps found, number of time steps of a complete year).
    """
    with xr.open_dataset(nc_file) as ds:
        valid_time = ds['valid_time'].values
    if valid_time.size == 0:
        raise RuntimeError(f"{nc_file} contains no time steps")
    years_found = sorted(set((valid_time.astype('datetime64[Y]').astype(int) + 1970).tolist()))
    if years_found != [int(year)]:
        raise RuntimeError(f"{nc_file} should contain {year} only, but contains {years_found}")
    n_expected = (366 if calendar.isleap(int(year)) else 365) * 24 // int(delta_t_in_h)
    return int(valid_time.size), n_expected


def get_asset_atmosphere(json_file, year, variable):
    # download one variable for one year from the Atmosphere Data Store (ADS) using the cdsapi
    # check: https://ads.atmosphere.copernicus.eu/how-to-api
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    parameters = get_parameter(json_file, 'bbox.json')
    if parameters is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")

    variable_dict = next((var for var in parameters["variables"] if var["name"] == variable), None)
    if variable_dict is None:
        raise ValueError(f"Variable '{variable}' is not listed in '{json_file}'")

    file_path = os.path.join(download_folder, parameters['source'], variable, year + '.nc')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # return if result file already exists
    if os.path.exists(file_path):
        print('file:' + file_path + ' already exists')
        return

    with open(os.path.join(secrets_folder, 'cdsapirc_atmo.sct'), 'r') as f:
        credentials = yaml.safe_load(f)
    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

    # widen the area by one grid step, see pad_bbox
    area = pad_bbox(parameters['bbox'], float(parameters.get('grid_resolution_deg', 0)))

    request = {
        'data_format': 'netcdf_zip',
        'variable': [variable],
        'date': [year + '-01-01/' + year + '-12-31'],
        'time': parameters['times'],
        'area': area,
    }
    # model_level is present for assets that can be monitored at different altitudes
    if 'model_level' in variable_dict:
        request['model_level'] = [str(variable_dict['model_level'])]

    # download and unzip under temporary names, the final file only appears once it is complete
    zip_part = file_path + '.zip.part'
    nc_part = file_path + '.part'
    try:
        c.retrieve(parameters['source'], request, zip_part)
        extract_single_netcdf(zip_part, nc_part)
        n_found, n_expected = check_time_axis(nc_part, year, parameters['delta_t_in_h'])
        if n_found != n_expected:
            # happens for a year that is not completely published yet
            print(f"WARNING: {variable} {year} has {n_found} of {n_expected} time steps")
        os.replace(nc_part, file_path)
    finally:
        for part in (zip_part, nc_part):
            if os.path.exists(part):
                os.remove(part)

    print('file:' + file_path + ' saved')



def get_asset_climate(json_file, year, variable):
    # download one variable for one year from the Climate Data Store (CDS) using the cdsapi
    # check: https://cds.climate.copernicus.eu/how-to-api
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    parameters = get_parameter(json_file, 'bbox.json')
    if parameters is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")
    if variable not in [var["name"] for var in parameters["variables"]]:
        raise ValueError(f"Variable '{variable}' is not listed in '{json_file}'")

    file_path = os.path.join(download_folder, parameters['source'], variable, year + '.nc')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # return if result file already exists
    if os.path.exists(file_path):
        print('file:' + file_path + ' already exists')
        return

    with open(os.path.join(secrets_folder, 'cdsapirc_climate.sct'), 'r') as f:
        credentials = yaml.safe_load(f)
    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

    # widen the area by one grid step, see pad_bbox
    area = pad_bbox(parameters['bbox'], float(parameters.get('grid_resolution_deg', 0)))

    request = {
        'product_type': [parameters.get('product_type', 'reanalysis')],
        'variable': [variable],
        'year': [year],
        'month': [f'{month:02d}' for month in range(1, 13)],
        'day': [f'{day:02d}' for day in range(1, 32)],
        'time': parameters['times'],
        'area': area,
        'data_format': 'netcdf',
        'download_format': 'unarchived',
    }

    # download under temporary names, the final file only appears once it is complete
    download_part = file_path + '.download.part'
    nc_part = file_path + '.part'
    try:
        c.retrieve(parameters['source'], request, download_part)
        if zipfile.is_zipfile(download_part):
            # the data store packs the result into a zip archive if it consists of several files
            extract_single_netcdf(download_part, nc_part)
        else:
            os.replace(download_part, nc_part)
        n_found, n_expected = check_time_axis(nc_part, year, parameters['delta_t_in_h'])
        if n_found != n_expected:
            # happens for a year that is not completely published yet
            print(f"WARNING: {variable} {year} has {n_found} of {n_expected} time steps")
        os.replace(nc_part, file_path)
    finally:
        for part in (download_part, nc_part):
            if os.path.exists(part):
                os.remove(part)

    print('file:' + file_path + ' saved')


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


def spei_download(json_file, variableOI):
    # download the SPEI drought index for one time scale (number of months, e.g. 12 for spei12.nc)
    # The file is global. Its content is stored unchanged, only the names of time, latitude and
    # longitude are changed to the names used in CLUES (valid_time, latitude, longitude).
    # The names cannot be changed inside of the downloaded file: renaming coordinates in place
    # destroys their values (an error of the netCDF library), so the file is written again.
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    parameter = get_parameter(json_file, 'bbox.json')
    if parameter is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")
    time_scale = int(variableOI)
    urls = [url for url in parameter['variables'][0]['urls'] if url.endswith(f"/spei{time_scale:02}.nc")]
    if len(urls) != 1:
        raise ValueError(f"Expected exactly one address for the time scale {time_scale} in '{json_file}', found {len(urls)}")

    file_path = os.path.join(download_folder, parameter['type'], str(time_scale) + '.nc')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    os.makedirs(tmp_folder, exist_ok=True)

    downloaded = os.path.join(tmp_folder, f'spei{time_scale:02}_download.nc')
    # the final file only appears once it is complete
    part = file_path + '.part'
    try:
        download_file(urls[0], downloaded)
        # read and write in pieces of 120 months, the complete file does not have to fit into memory
        with xr.open_dataset(downloaded, chunks={'time': 120}) as ds:
            if 'spei' not in ds.data_vars:
                raise RuntimeError(f"Unexpected content of {urls[0]}: variables {list(ds.data_vars)}")
            harmonized = rename_coords(ds)
            missing = [name for name in ('valid_time', 'latitude', 'longitude') if name not in harmonized.coords]
            if missing:
                raise RuntimeError(f"Unexpected content of {urls[0]}: coordinates {list(ds.coords)}")
            n_lat, n_lon = harmonized.sizes['latitude'], harmonized.sizes['longitude']
            harmonized.to_netcdf(part, encoding={'spei': {'zlib': True, 'complevel': 4, 'chunksizes': (1, n_lat, n_lon)}})
            print(f"spei{time_scale:02}: {dict(harmonized.sizes)}, "
                  f"{str(harmonized['valid_time'].values[0])[:10]} to {str(harmonized['valid_time'].values[-1])[:10]}")
        os.replace(part, file_path)
    finally:
        for leftover in (part, downloaded):
            if os.path.exists(leftover):
                os.remove(leftover)
    print(f"File downloaded and saved as {file_path}")


def download_file(url, target, max_retries=3):
    """
    Download a file to `target`.

    The data is written in pieces to a temporary file (never the whole file in memory), the size is
    compared with the size announced by the server and only a complete file gets the final name.
    """
    part = target + '.part'
    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                size = int(response.headers.get('Content-Length', -1))
                with open(part, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=4 * 1024 * 1024):
                        f.write(chunk)
            if size >= 0 and os.path.getsize(part) != size:
                raise requests.RequestException(f"incomplete download, {os.path.getsize(part)} of {size} bytes")
            os.replace(part, target)
            return
        except requests.RequestException as e:
            print(f"{url}: {e} (attempt {attempt}/{max_retries})")
            if os.path.exists(part):
                os.remove(part)
            if attempt == max_retries:
                raise RuntimeError(f"Failed to download {url}") from e
            sleep(30)


def supports_range_requests(url):
    # True if the server delivers parts of a file, then only the area of interest has to be read
    with requests.get(url, headers={'Range': 'bytes=0-1023'}, stream=True, timeout=60) as response:
        return response.status_code == 206


def crop_geotiff_to_bbox(source, target, bbox, margin_in_pixel=10, rows_per_step=2048):
    """
    Write the part of a GeoTIFF that covers the bbox [lat_max, lon_min, lat_min, lon_max] to `target`.

    source: a local file or a file on a web server ('/vsicurl/' + url). From a web server only the
            needed parts of the file are read.
    The pixels are copied unchanged (same pixel grid, values, data type, nodata value, scale factor),
    a margin of some pixels is added around the bbox. The data is copied in steps of some rows,
    so large areas do not have to fit into memory.
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    with rasterio.open(source) as src:
        left, bottom, right, top = lon_min, lat_min, lon_max, lat_max
        if src.crs is not None and src.crs.to_epsg() != 4326:
            left, bottom, right, top = transform_bounds('EPSG:4326', src.crs, left, bottom, right, top, densify_pts=21)
        window = from_bounds(left, bottom, right, top, src.transform)
        col_start = max(0, math.floor(window.col_off) - margin_in_pixel)
        row_start = max(0, math.floor(window.row_off) - margin_in_pixel)
        col_stop = min(src.width, math.ceil(window.col_off + window.width) + margin_in_pixel)
        row_stop = min(src.height, math.ceil(window.row_off + window.height) + margin_in_pixel)
        width, height = col_stop - col_start, row_stop - row_start
        if width <= 0 or height <= 0:
            raise RuntimeError(f"The area {bbox} does not overlap with {source}")

        profile = src.profile.copy()
        profile.update(driver='GTiff', width=width, height=height,
                       transform=src.window_transform(Window(col_start, row_start, width, height)),
                       compress='deflate', tiled=True, blockxsize=256, blockysize=256, BIGTIFF='IF_SAFER')
        with rasterio.open(target, 'w', **profile) as dst:
            dst.update_tags(**src.tags())
            dst.scales = src.scales
            dst.offsets = src.offsets
            dst.units = src.units
            for band in src.indexes:
                dst.update_tags(band, **src.tags(band))
                if src.descriptions[band - 1]:
                    dst.set_band_description(band, src.descriptions[band - 1])
            for row in range(0, height, rows_per_step):
                rows = min(rows_per_step, height - row)
                data = src.read(window=Window(col_start, row_start + row, width, rows))
                dst.write(data, window=Window(0, row, width, rows))
    print(f"{width} x {height} pixels written to {target}")


def get_simple_download_tif(json_file, vOI):
    # get a GeoTIFF file that is offered as one (global) file directly from the source
    # With "cut_to_area": true in the configuration only the configured area is saved,
    # otherwise the complete file.
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    parameters = get_parameter(json_file, 'bbox.json')
    if parameters is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")
    variable = next((v for v in parameters['variables'] if v['name'] == vOI), None)
    if variable is None:
        raise ValueError(f"Variable '{vOI}' is not listed in '{json_file}'")

    url = variable['url']
    file_path = os.path.join(download_folder, parameters['type'], variable['name'] + '.tif')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if parameters.get('cut_to_area', False):
        # write under a temporary name, the final file only appears once it is complete
        part = file_path + '.part'
        complete_file = os.path.join(tmp_folder, variable['name'] + '_complete.tif')
        try:
            if supports_range_requests(url):
                # read only the area of interest from the server
                with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_TIMEOUT='120',
                                  GDAL_HTTP_MAX_RETRY='5', GDAL_HTTP_RETRY_DELAY='30'):
                    crop_geotiff_to_bbox('/vsicurl/' + url, part, parameters['bbox'])
            else:
                # the server only delivers complete files: download, cut out the area, remove the complete file
                os.makedirs(tmp_folder, exist_ok=True)
                download_file(url, complete_file)
                crop_geotiff_to_bbox(complete_file, part, parameters['bbox'])
            os.replace(part, file_path)
        finally:
            for leftover in (part, complete_file):
                if os.path.exists(leftover):
                    os.remove(leftover)
    else:
        download_file(url, file_path)

    # make sure the file really is a GeoTIFF (and not e.g. an error page of the server)
    try:
        with rasterio.open(file_path) as src:
            print(f"{src.width} x {src.height} pixels, {src.count} band(s), {src.dtypes[0]}, {src.crs}")
    except Exception:
        os.remove(file_path)
        raise

    print("The GeoTIFF file has been saved as '" + variable['name'] + '.tif' + "'.")

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


def get_all_files(article_id, version=None):
    # list of all files of a Figshare record (name, size, download_url, computed_md5, ...)
    # version: number of the version of the record, None for the latest version
    if version is not None:
        response = requests.get(f"https://api.figshare.com/v2/articles/{article_id}/versions/{version}", timeout=30)
        response.raise_for_status()
        return response.json()["files"]
    files = []
    seen = set()
    page = 1
    while True:
        url = f"https://api.figshare.com/v2/articles/{article_id}/files?page={page}&page_size=100"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        for f in batch:
            if f["name"] not in seen:
                seen.add(f["name"])
                files.append(f)
        if len(batch) < 100:
            break
        page += 1
    return files


def md5_of_file(path):
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            md5.update(chunk)
    return md5.hexdigest()


def download_figshare_file(file_info, target):
    # download one file of a Figshare record and compare it with the checksum of the record
    download_file(file_info["download_url"], target)
    expected = file_info.get("computed_md5") or file_info.get("supplied_md5")
    if expected and md5_of_file(target) != expected:
        os.remove(target)
        raise RuntimeError(f"Checksum of {file_info['name']} does not match the Figshare record")


def download_ntl_glwd(json_file):
    """
    Download files of a Figshare record (used for the Global Lakes and Wetlands Database and the
    night time lights).

    Configuration of the variable:
        article_id   number of the Figshare record
        version      version of the record (optional, default: the latest version)
        files_oi     list of the file names to download, or "all"
        flagFile     one of these files, snakemake waits for it; it is written last
    Zip files are unpacked. With "cut_to_area": true in the configuration the GeoTIFF files are cut
    to the configured area (pixels unchanged), otherwise they are stored completely.
    Errors are not caught here: a failed download must end the script with an error,
    so that snakemake marks the job as failed.
    """
    parameter = get_parameter(json_file, 'bbox.json')
    if parameter is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")
    variable = parameter['variables'][0]
    for key in ('article_id', 'files_oi', 'flagFile'):
        if key not in variable:
            raise KeyError(f"'{key}' is missing for the variable '{variable.get('name')}' in '{json_file}'")
    files_oi = variable['files_oi']
    flag_file = variable['flagFile']
    cut_to_area = parameter.get('cut_to_area', False)

    folder = os.path.join(download_folder, parameter['type'])
    os.makedirs(folder, exist_ok=True)

    files = get_all_files(variable['article_id'], variable.get('version'))
    if files_oi != "all":
        missing = [name for name in files_oi if name not in [f["name"] for f in files]]
        if missing:
            raise RuntimeError(f"Not part of the Figshare record {variable['article_id']}: {missing}")
        files = [f for f in files if f["name"] in files_oi]
    # the flag file last: it only appears when everything else is there
    files.sort(key=lambda f: f["name"] == flag_file)
    print(f"Found {len(files)} file(s) to download")

    work_dir = os.path.join(tmp_folder, 'figshare_' + str(variable['article_id']))
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir)
    try:
        for file_info in files:
            name = file_info["name"]
            # a complete file of an earlier, interrupted run is not downloaded again
            existing = os.path.join(folder, name)
            if (not cut_to_area and not name.endswith(".zip") and name != flag_file and os.path.exists(existing)
                    and os.path.getsize(existing) == file_info["size"]
                    and md5_of_file(existing) == (file_info.get("computed_md5") or file_info.get("supplied_md5"))):
                print(f"  Skip (done): {name}")
                continue
            print(f"  Downloading: {name} ({file_info['size'] / 1e6:.1f} MB)")
            downloaded = os.path.join(work_dir, name)
            download_figshare_file(file_info, downloaded)

            if name.endswith(".zip"):
                print(f"  Extracting: {name}")
                extract_dir = os.path.join(work_dir, 'extracted')
                with zipfile.ZipFile(downloaded) as zf:
                    zf.extractall(extract_dir)
                os.remove(downloaded)
                store_folder(extract_dir, folder, parameter['bbox'] if cut_to_area else None)
                shutil.rmtree(extract_dir)
            else:
                store_file(downloaded, os.path.join(folder, name), parameter['bbox'] if cut_to_area else None)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    if not os.path.exists(os.path.join(folder, flag_file)):
        raise RuntimeError(f"The flag file '{flag_file}' is not among the downloaded files, check 'files_oi' and 'flagFile'")
    print(f"  Done {folder}")


def store_file(source, target, bbox=None):
    # move a downloaded file to its final place; a GeoTIFF is cut to the bbox if one is given
    os.makedirs(os.path.dirname(target), exist_ok=True)
    part = target + '.part'
    try:
        if bbox is not None and target.lower().endswith(('.tif', '.tiff')):
            crop_geotiff_to_bbox(source, part, bbox)
        else:
            shutil.move(source, part)
        os.replace(part, target)
    finally:
        if os.path.exists(part):
            os.remove(part)


# helper files that describe the extent or hold reduced copies of a complete raster (world file,
# overviews, statistics). Next to a raster that was cut to an area they would be wrong.
RASTER_HELPER_FILES = ('.tfw', '.tifw', '.ovr', '.aux.xml')


def store_folder(source_folder, target_folder, bbox=None):
    # store all files of an unpacked zip file, the folders inside of the zip file are kept
    for root, _, names in os.walk(source_folder):
        for name in sorted(names):
            if bbox is not None and name.lower().endswith(RASTER_HELPER_FILES):
                continue
            source = os.path.join(root, name)
            relative = os.path.relpath(source, source_folder)
            store_file(source, os.path.join(target_folder, relative), bbox)
