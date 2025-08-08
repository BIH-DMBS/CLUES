import numpy as np
from scipy.ndimage import convolve, generic_filter
import rasterio
from pyproj import Geod
import json
import os
from datetime import datetime
import re

import xarray as xr
from scipy.ndimage import uniform_filter
from math import radians, sin, cos, sqrt, atan2

try:
    from .config import download_folder, configs_assets_folder, area, config_folder, secrets_folder
except:
    from config import download_folder, configs_assets_folder, area, config_folder, secrets_folder


def zevenbergen_thorne(input_tiff, output_slope_tiff, output_aspect_tiff):
    infoTxt = """
        ## Zevenbergen-Thorne Algorithm

        ### Function: ZevenbergenThorne(DEM)

        1. **Get the dimensions of the DEM**
            - `rows = number of rows in DEM`
            - `cols = number of columns in DEM`

        2. **Initialize Slope and Aspect arrays with the same dimensions as DEM**
            - `Slope = array of size (rows, cols)`
            - `Aspect = array of size (rows, cols)`

        3. **Loop through each cell in the DEM (excluding the border cells)**
            - `for i from 1 to rows-2:`
                - `for j from 1 to cols-2:`
                    - **Get the elevation values of the 3x3 neighborhood**
                        - `z1 = DEM[i-1][j-1]`
                        - `z2 = DEM[i-1][j]`
                        - `z3 = DEM[i-1][j+1]`
                        - `z4 = DEM[i][j-1]`
                        - `z5 = DEM[i][j]`  (Center cell)
                        - `z6 = DEM[i][j+1]`
                        - `z7 = DEM[i+1][j-1]`
                        - `z8 = DEM[i+1][j]`
                        - `z9 = DEM[i+1][j+1]`

                    - **Calculate the partial derivatives**
                        - `dzdx = ((z3 + 2*z6 + z9) - (z1 + 2*z4 + z7)) / (8 * cell_size)`
                        - `dzdy = ((z1 + 2*z2 + z3) - (z7 + 2*z8 + z9)) / (8 * cell_size)`

                    - **Calculate the slope**
                        - `Slope[i][j] = sqrt(dzdx^2 + dzdy^2)`

                    - **Calculate the aspect**
                        - `Aspect[i][j] = atan2(dzdy, -dzdx)`
                        - `if Aspect[i][j] < 0:`
                            - `Aspect[i][j] += 2 * PI`

        4. **Return Slope and Aspect**
            - `return Slope, Aspect`
    """
    try:
        with rasterio.open(input_tiff) as src:
            elevation = src.read(1)
            transform = src.transform
            profile = src.profile

            # Calculate the partial derivatives
            dzdx = (np.roll(elevation, -1, axis=1) - np.roll(elevation, 1, axis=1)) / (2 * transform.a)
            dzdy = (np.roll(elevation, -1, axis=0) - np.roll(elevation, 1, axis=0)) / (2 * transform.e)

            # Calculate the slope
            slope = np.sqrt(dzdx**2 + dzdy**2)

            # Calculate the aspect
            aspect = np.arctan2(dzdy, -dzdx)
            aspect = np.where(aspect < 0, aspect + 2 * np.pi, aspect)

            # Update profile for slope and aspect
            profile.update(dtype=rasterio.float32, count=1, compress='lzw')

            # Write the slope to a new GeoTIFF
            with rasterio.open(output_slope_tiff, 'w', **profile) as dst:
                dst.write(slope.astype(rasterio.float32), 1)

            # Write the aspect to a new GeoTIFF
            with rasterio.open(output_aspect_tiff, 'w', **profile) as dst:
                dst.write(aspect.astype(rasterio.float32), 1)
    except Exception as e:
        print(f"Error processing {input_tiff}: {e}")
        raise e


def zevenbergen_thorne_folder(file_list, in_path, out_path):
    for tiff in file_list:
        input_tiff = os.path.join(in_path,tiff)
        output_slope_tiff = os.path.join(out_path,f"slope_{tiff}")
        output_aspect_tiff = os.path.join(out_path,f"aspect_{tiff}")
        zevenbergen_thorne(input_tiff, output_slope_tiff, output_aspect_tiff)


def circular_kernel(radius):
    """Create a circular kernel with the given radius."""
    L = np.arange(-radius, radius+1)
    X, Y = np.meshgrid(L, L)
    kernel = (X**2 + Y**2) <= radius**2
    return kernel / kernel.sum()


def mean_filter_geotiff(input_tiff, output_tiff, radius):
    try:
        # Open the input GeoTIFF file
        with rasterio.open(input_tiff) as src:
            # Read the input data
            image = src.read(1)
            profile = src.profile

            # Create a circular kernel
            kernel = circular_kernel(radius)

            # Apply mean filter using convolve from scipy
            filtered_image = convolve(image, kernel, mode='reflect')

            # Update profile for the output GeoTIFF
            profile.update(dtype=rasterio.float32, count=1, compress='lzw')

            # Write the filtered image to a new GeoTIFF file
            with rasterio.open(output_tiff, 'w', **profile) as dst:
                dst.write(filtered_image.astype(rasterio.float32), 1)
    except Exception as e:
        print(f"Error processing {input_tiff}: {e}")
        raise e


def calculate_pixel_size_geographic(geo_tiff_path):
    try:
        # compute the average width/height of a pixel in meters given geotiff with CRS geographic(degrees) 
        with rasterio.open(geo_tiff_path) as src:
            # Get transform and resolution in degrees
            transform = src.transform
            pixel_width_deg = transform.a  # Pixel size in degrees (longitude)
            pixel_height_deg = abs(transform.e)  # Pixel size in degrees (latitude)


            # Get the latitude of the raster's center
            center_lat = (src.bounds.top + src.bounds.bottom) / 2
            # Get the longitzude of the raster's center
            center_lon = (src.bounds.left + src.bounds.right) / 2

            # Approximate conversion from degrees to meters at the center latitude
            geod = Geod(ellps="WGS84")
            _, width_meters, _ = geod.inv(src.bounds.left, center_lat, src.bounds.left + pixel_width_deg, center_lat)
            _, height_meters, _ = geod.inv(src.bounds.left, center_lon, src.bounds.left + pixel_height_deg, center_lon)
            
            return np.abs(width_meters+height_meters)/2
    except Exception as e:
        print(f"Error calculating pixel size for {geo_tiff_path}: {e}")
        raise e


def getFilterRadiusPixel(geo_tiff_path, radius_in_meter):
    resolution = calculate_pixel_size_geographic(geo_tiff_path)
    radius_in_pixel = np.ceil((radius_in_meter-resolution/2)/resolution)
    return int(radius_in_pixel)


def list_tif_files(folder_path):
    # List to store the names of .tif files
    tif_files = []

    # Iterate over all the files in the given folder
    for file_name in os.listdir(folder_path):
        # Check if the file ends with .tif
        if file_name.endswith('.tif'):
            tif_files.append(file_name)
    return tif_files


def extract_coordinates(filename):
    match = re.search(r'N(\d+)_00_E(\d+)_00', filename)
    if match:
        lat = int(match.group(1))
        lon = int(match.group(2))
        return lon, lat
    match = re.search(r'N(\d+)_00_W(\d+)_00', filename)
    if match:
        lat = int(match.group(1))
        lon = -int(match.group(2))
        return lon, lat
    match = re.search(r'S(\d+)_00_E(\d+)_00', filename)
    if match:
        lat = -int(match.group(1))
        lon = int(match.group(2))
        return lon, lat
    match = re.search(r'S(\d+)_00_W(\d+)_00', filename)
    if match:
        lat = -int(match.group(1))
        lon = -int(match.group(2))
        return lon, lat
    return None


def nan_convolve(image, kernel):
    # Create mask of valid (non-NaN) values
    nan_mask = np.isnan(image)
    valid_mask = (~nan_mask).astype(float)

    image = np.nan_to_num(image, nan=0.0)

    convolved = convolve(image, kernel, mode='reflect')
    normalization = convolve(valid_mask, kernel, mode='reflect')

    # Avoid division by zero
    with np.errstate(invalid='ignore', divide='ignore'):
        result = convolved / normalization
        result[normalization == 0] = np.nan

    return result


def apply_filter_with_adjacent_images(file_list, in_path, out_path, radius, mode, radius_in_meter):
    # Read all images and store them in a dictionary with their coordinates as keys
    images = {}
    profiles = {}
    files = {}
    for file in file_list:
        coords = extract_coordinates(file)
        print('...')
        print(coords)
        print('..')
        with rasterio.open(os.path.join(in_path, file)) as src:
            images[coords] = src.read(1)
            profiles[coords] = src.profile
            files[coords] = file
    
    # Get the unique coordinates
    unique_coords = list(images.keys())
    kernel = circular_kernel(radius)
    # Apply mean filter to each image using adjacent images at the margins
    for coords in unique_coords:
        img = images[coords]
        profile = profiles[coords]
        # Get the window size for the mean filter
        window_size = 2 * radius + 1
        # Create an empty array to store the enlarged image
        enlarged_img = np.empty((img.shape[0] + 2 * radius, img.shape[1] + 2 * radius))
        # Copy the original image to the center of the enlarged image
        enlarged_img[radius:-radius, radius:-radius] = img

        # Get adjacent images and copy their margins to the enlarged image
        for adj_coords in [x for x in unique_coords if x != coords]:
            adj_img = images[adj_coords]
            print(adj_img.shape)
            print(enlarged_img.shape)
            if adj_coords[0] == coords[0]:  # Same x coordinate
                if adj_coords[1] == coords[1]+1:  # Bottom adjacent image
                    enlarged_img[radius:-radius,:radius] = adj_img[:,-radius:]
                elif adj_coords[1] == coords[1]-1:  # Bottom adjacent image
                    enlarged_img[radius:-radius, -radius:] = adj_img[:,:radius]
            elif adj_coords[1] == coords[1]:  # Same y coordinate
                if adj_coords[0] == coords[0]-1:  # Left adjacent image
                    enlarged_img[:radius, radius:-radius] = adj_img[-radius:,:]
                elif adj_coords[0] == coords[0]+1:  # Right adjacent image
                    enlarged_img[-radius:, radius:-radius] = adj_img[:radius, :]
                    
        if mode == 'mean':
            # Apply mean filter using convolve from scipy
            filtered_image = nan_convolve(enlarged_img, kernel)
        elif mode == 'std':
            # Mean of x
            mean = nan_convolve(enlarged_img, kernel)
            # Mean of x^2
            mean_of_square = nan_convolve(enlarged_img**2, kernel)
            # std = sqrt(E[x^2] - (E[x])^2)
            filtered_image = np.sqrt(mean_of_square - mean**2)
        
        # Crop the filtered image to the original size
        filtered_image = filtered_image[radius:-radius, radius:-radius]
        
        # Save the filtered image
        output_tif = os.path.join(out_path,f"{mode}_{files[coords]}_{radius_in_meter}.tif")
        try:
            # Update profile for the output GeoTIFF
            profile.update(dtype=rasterio.float32, count=1, compress='lzw')
            print(profile)
            # Write the filtered image to a new GeoTIFF file
            with rasterio.open(output_tif, 'w', **profile) as dst:
                dst.write(filtered_image.astype(rasterio.float32), 1)
        except Exception as e:
            print(f"Error writing {output_tif}: {e}")
            raise e


def extract_radius(s):
    match = re.search(r'_radius_(\d+)', s)
    if match:
        return int(match.group(1))
    return None


def compute_neighborhood(json_file, variableOI, mode):
    try:
        # Load JSON file as a dictionary
        with open(json_file, 'r') as file:
            parameters = json.load(file)

        for v in parameters['variables']:
            print(v['name'])
            if v['name']==variableOI:
                variable = v
                break
    except Exception as e:
        print(f"Error reading JSON file {json_file}: {e}")
        raise e

    in_path = os.path.join(download_folder, parameters['type'], v['name'])
    out_path = os.path.join(download_folder, 'neigborhoods', parameters['type'], v['name'],mode)
    # List of .tif files in the folder
    tif_files = list_tif_files(in_path)
    print('files to process:')
    print(tif_files)
    
    radius_in_meter = extract_radius(mode)
    if 'mean' in mode:
        radius_in_pxl = getFilterRadiusPixel(os.path.join(in_path,tif_files[0]), radius_in_meter)
        apply_filter_with_adjacent_images(tif_files, in_path, out_path, radius_in_pxl, 'mean', radius_in_meter)
    elif 'std' in mode:
        radius_in_pxl = getFilterRadiusPixel(os.path.join(in_path,tif_files[0]), radius_in_meter)
        apply_filter_with_adjacent_images(tif_files, in_path, out_path, radius_in_pxl, 'std', radius_in_meter)
    elif 'zevenbergen_thorne':
        zevenbergen_thorne_folder(tif_files, in_path, out_path)
    else:
        print('filter mode ' + mode + 'not available')
    
    # Get the current timestamp
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        flag_filename = os.path.join(out_path, "done.txt")
        # Write the timestamp to a text file
        with open(flag_filename, "w") as file:
            file.write("Data was downloaded: ")
            file.write(current_timestamp)
    except Exception as e:
        print(f"Error writing flag file {flag_filename}: {e}")
        raise e

###########################
# Define Haversine distance function (meters)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def nanmean_filter(data, size):
    # Create mask of valid (non-NaN) values
    valid_mask = np.isfinite(data).astype(float)
    data_filled = np.nan_to_num(data, nan=0.0)

    # Apply uniform filter to both data and mask
    filtered_sum = uniform_filter(data_filled, size=size, mode='nearest')
    count_valid = uniform_filter(valid_mask, size=size, mode='nearest')

    # Avoid division by zero
    with np.errstate(invalid='ignore', divide='ignore'):
        filtered = filtered_sum / count_valid
        filtered[count_valid == 0] = np.nan

    return filtered


def nanstd_filter(data, size):
    # Create mask of valid values
    valid_mask = np.isfinite(data).astype(float)
    data_filled = np.nan_to_num(data, nan=0.0)

    # First moment (mean)
    mean = uniform_filter(data_filled, size=size, mode='nearest') / \
           uniform_filter(valid_mask, size=size, mode='nearest')

    # Second moment (mean of squares)
    mean_sq = uniform_filter(data_filled**2, size=size, mode='nearest') / \
              uniform_filter(valid_mask, size=size, mode='nearest')

    # Compute std = sqrt(E[x^2] - (E[x])^2)
    std = np.sqrt(mean_sq - mean**2)

    # Set std to NaN where there are no valid pixels
    count_valid = uniform_filter(valid_mask, size=size, mode='nearest')
    std[count_valid == 0] = np.nan

    return std


def compute_neighborhood_modis_vi(json_file, typ, name, fltr, rds_m, year):
    file_path = os.path.join(download_folder, typ, name, f"{year}.nc")
    print(file_path)
    ds = xr.open_dataset(file_path)
    data_array = ds[name].values
    Latitude   = ds['Latitude'].values  # (YDim, XDim) float32
    Longitude  = ds['Longitude'].values  # (YDim, XDim) float32
    # Pick center of the grid for estimating pixel size
    center_y = Latitude.shape[0] // 2
    center_x = Latitude.shape[1] // 2

    # Estimate pixel size in meters using neighboring pixels
    lat_center = Latitude[center_y, center_x]
    lon_center = Longitude[center_y, center_x]

    lat_dx = Latitude[center_y, center_x + 1]
    lon_dx = Longitude[center_y, center_x + 1]

    lat_dy = Latitude[center_y + 1, center_x]
    lon_dy = Longitude[center_y + 1, center_x]

    # Distance per pixel in X and Y direction
    dx_m = haversine(lat_center, lon_center, lat_dx, lon_dx)
    #dy_m = haversine(lat_center, lon_center, lat_dy, lon_dy)

    # Convert radius in meters to pixels (average for isotropic filter)
    radius_pixels_x = int(int(rds_m) / dx_m)
    #radius_pixels_y = int(rds_m / dy_m)
    #radius_pixels_avg = int(rds_m / ((dx_m + dy_m) / 2))

    print(f"Pixel size (dx, ...): ({dx_m:.2f} m, ... m)")
    print(f"Radius in pixels (x, ...): ({radius_pixels_x}, ... )")

    # create empty array with same shape as data_array
    filtered_data = np.empty_like(data_array, dtype=np.float32)
    filter_size = (radius_pixels_x, radius_pixels_x)
    for t in range(data_array.shape[0]):
        if fltr == 'mean':    
            filtered_data[t] = nanmean_filter(data_array[t], size=filter_size)
        elif fltr == 'std': 
            filtered_data[t] = nanstd_filter(data_array[t], size=filter_size)
    # Now add the 3D filtered data to dataset with correct dimensions
    ds[name + '_filtered'] = (('time', 'YDim', 'XDim'), filtered_data)
    # remove original data from dataset
    ds = ds.drop_vars(name)
    # save the modified dataset to a new file
    result_file = os.path.join(download_folder,'neigborhoods', f'{typ}',f'{name}',f'{fltr}_radius_{rds_m}_{year}.nc')
    ds.to_netcdf(result_file)
