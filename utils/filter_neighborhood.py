import numpy as np
from scipy.ndimage import convolve, generic_filter
import rasterio
from pyproj import Geod
import json
import os
from datetime import datetime
import re

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


def calculate_pixel_size_geographic(geo_tiff_path):
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
        # Update profile for the output GeoTIFF
        profile.update(dtype=rasterio.float32, count=1, compress='lzw')
        print(profile)
        # Write the filtered image to a new GeoTIFF file
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_image.astype(rasterio.float32), 1)


def extract_radius(s):
    match = re.search(r'_radius_(\d+)', s)
    if match:
        return int(match.group(1))
    return None


def compute_neighborhood(json_file, variableOI, mode):
    # Load JSON file as a dictionary
    with open(json_file, 'r') as file:
        parameters = json.load(file)

    for v in parameters['variables']:
        print(v['name'])
        if v['name']==variableOI:
            variable = v
            break

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

    flag_filename = os.path.join(out_path, "done.txt")
    # Write the timestamp to a text file
    with open(flag_filename, "w") as file:
        file.write("Data was downloaded: ")
        file.write(current_timestamp)