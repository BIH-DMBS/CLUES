import os
import json
import requests
import shutil
import yaml
from netCDF4 import Dataset
import re
import numpy as np
from shapely.geometry import Polygon
from bs4 import BeautifulSoup
from shapely.geometry import Polygon
from netCDF4 import Dataset
import rasterio
from rasterio.transform import from_origin
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask

from datetime import datetime
from shapely.geometry import box

import utils

try:
    from .config import download_folder, secrets_folder
except:
    from config import download_folder, secrets_folder


def get_links(url):
    # Regular expression pattern for dates in YYYY.MM.DD/ format
    date_pattern = re.compile(r"(\d{4}\.\d{2}\.\d{2})/$")

    # Send a GET request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all links in the page
        links = [a["href"] for a in soup.find_all("a", href=True)]
        
        # Create a dictionary with date objects as keys and full URLs as values
        date_links_dict = {
            datetime.strptime(match.group(1), "%Y.%m.%d").date(): url + link
            for link in links if (match := date_pattern.match(link))
        }

    else:
        print(f"Failed to retrieve page, status code: {response.status_code}")

    return date_links_dict


def get_filelinks(url):
    # Fetch the HTML content
    response = requests.get(url)
    html_content = response.content

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all links on the page
    links = soup.find_all('a')

    # Extract the file names
    return [link.get('href') for link in links if link.get('href').endswith('.hdf')]


def latlon_to_modis_tile(lat, lon):
    """
    Convert WGS84 (lat, lon) to MODIS tile numbers (h, v).
    Approximate method without GDAL.
    """
    # MODIS grid parameters
    tile_size = 10  # Approximate degrees per tile
    h = int((lon + 180) / tile_size)  # Horizontal tile number
    v = int((90 - lat) / tile_size)   # Vertical tile number
    return v,h


def get_deltas(files):
    lat = []
    lon = []
    for file_name in files:
        # Extract h and v values from the file name using regex
        match = re.search(r'h(\d{2})v(\d{2})', file_name)
        if match:
            lon.append(int(match.group(1)))
            lat.append(int(match.group(2)))
    lon = np.array(sorted(set(lon)))
    lat = np.array(sorted(set(lat)))
    lon = set(lon[1:]-lon[:-1])
    lat = set(lat[1:]-lat[:-1])
    if len(lat) == 1 and len(lon) == 1:
        return {'delta_lon': next(iter(lon)), 'delta_lat': next(iter(lat))}
    else:
        print('not equidistant grid')


def bounding_box_to_polygon(bbox):
    """
    Convert a bounding box to a polygon.
    
    Parameters:
    bbox: Bounding box defined as [max_lat, min_lon, min_lat, max_lon]
    
    Returns:
    Polygon object representing the bounding box.
    """
    max_lat, min_lon, min_lat, max_lon = bbox
    # Define the coordinates of the polygon
    coordinates = [
        (min_lon, min_lat),  # Bottom-left
        (min_lon, max_lat),  # Top-left
        (max_lon, max_lat),  # Top-right
        (max_lon, min_lat),  # Bottom-right
        (min_lon, min_lat)   # Closing the polygon
    ]
    
    # Create a polygon from the coordinates
    polygon = Polygon(coordinates)
    
    return polygon    
            

def is_within_bounding_box(files, bbox):
    bbox = bounding_box_to_polygon(bbox)
    deltas = get_deltas(files)
    file_in_bbox = []
    for file_name in files:
        # Extract h and v values from the file name using regex
        match = re.search(r'h(\d{2})v(\d{2})', file_name)
        if match:
            lon = int(match.group(1))
            lat = int(match.group(2))
            coordinates = [
                (lon, lat),  # Bottom-left
                (lon, lat + deltas['delta_lat']),  # Top-left
                (lon + deltas['delta_lon'], lat + deltas['delta_lat']),  # Top-right
                (lon + deltas['delta_lon'], lat),  # Bottom-right
                (lon, lat)   # Closing the polygon
            ]
            polygon = Polygon(coordinates)
            if bbox.intersects(polygon):
                file_in_bbox.append(file_name)

    return file_in_bbox


def mkfloder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def download_modis_nasa(hdf_file, folder, url, token):
    # Set up the headers with the token
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Make the request with the headers
    response = requests.get(url+hdf_file, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content to a file
        with open(os.path.join(folder,hdf_file), 'wb') as file:
            file.write(response.content)
        print('Download completed successfully.')
    else:
        print(f'Failed to download file. Status code: {response.status_code}')


def to_tiff(hdf_file, folder, elements):
    # Open the HDF file
    dataset = Dataset(os.path.join(folder,hdf_file), 'r')

    # Close the dataset
    ndvi_data = dataset.variables[elements[0]][:] #dataset.variables['1 km monthly NDVI'][:]
    evi_data = dataset.variables[elements[1]][:] #dataset.variables['1 km monthly EVI'][:]
    struct_metadata = dataset.getncattr('StructMetadata.0')
    dataset.close()

    grid_structure_info = re.search(r'GROUP=GridStructure(.*?)END_GROUP=GridStructure', struct_metadata, re.DOTALL).group(1)

    # Convert the parsed string into a dictionary
    grid_structure_dict = {}
    for line in grid_structure_info.split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"')
            if 'YDim' in value:
                pass
            elif ',' in value:
                value = tuple(map(float, value.strip('()').split(',')))
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit():
                value = float(value)
            if key in grid_structure_dict:
                grid_structure_dict[key].append(value)
            else:
                grid_structure_dict[key] = [value] 

    # Get the dimensions and metadata
    x_dim = grid_structure_dict['XDim'][0]
    y_dim = grid_structure_dict['YDim'][0]
    upper_left_x, upper_left_y = grid_structure_dict['UpperLeftPointMtrs'][0]
    lower_right_x, lower_right_y = grid_structure_dict['LowerRightMtrs'][0]

    # Calculate the pixel size
    pixel_size_x = (lower_right_x - upper_left_x) / x_dim
    pixel_size_y = (upper_left_y - lower_right_y) / y_dim

    # Define the transform
    transform = from_origin(upper_left_x, upper_left_y, pixel_size_x, pixel_size_y)

    # Define the CRS (Coordinate Reference System) for Sinusoidal projection
    crs = {
        'proj': 'sinu',
        'lon_0': 0,
        'x_0': 0,
        'y_0': 0,
        'a': 6371007.181,
        'b': 6371007.181,
        'units': 'm',
        'no_defs': True
    }

    # Save as GeoTIFF
    output_tiff_NDVI = os.path.join(folder,hdf_file + '_NDVI.tif')
    with rasterio.open(
        output_tiff_NDVI, 'w', driver='GTiff', height=y_dim, width=x_dim,
        count=1, dtype=ndvi_data.dtype, crs=crs, transform=transform
    ) as dst:
        dst.write(ndvi_data, 1)
    
    # Save as GeoTIFF
    output_tiff_EVI = os.path.join(folder,hdf_file + '_EVI.tif')
    with rasterio.open(
        output_tiff_EVI, 'w', driver='GTiff', height=y_dim, width=x_dim,
        count=1, dtype=evi_data.dtype, crs=crs, transform=transform
    ) as dst:
        dst.write(evi_data, 1)

    return [output_tiff_NDVI, output_tiff_EVI]


def reproject_and_crop(bbox,file_path_result, file_path_tmp, outputFolder, date):
    bounding_box = (bbox[1], bbox[2], bbox[3], bbox[0])

    # Open the source GeoTIFF file
    with rasterio.open(file_path_tmp) as src:
        # Define the target CRS (WGS84)
        dst_crs = 'EPSG:4326'

        # Compute the transformation, width, and height for the new projection
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        # Ensure width and height are valid
        if width <= 0 or height <= 0:
            raise ValueError("Invalid width/height computed. Check source data.")

        # Update metadata for the reprojected raster
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height,
            'dtype': src.dtypes[0],  # Preserve data type
            'count': src.count  # Preserve band count
        })

        # Save the reprojected raster to a temporary file
        temp_file = os.path.join(outputFolder,str(date) + '_reprojected.tif')
        with rasterio.open(temp_file, 'w', **kwargs) as temp_dst:
            for i in range(1, src.count + 1):
                data = np.zeros((height, width), dtype=src.dtypes[0])  # Initialize empty array
                reproject(
                    source=rasterio.band(src, i),
                    destination=data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.cubic  # Higher quality interpolation
                )
                temp_dst.write(data, i)

    # Open the reprojected raster and crop it to the bounding box
    with rasterio.open(temp_file) as reprojected:
        # Convert bounding box to a GeoJSON polygon
        bbox_geom = [box(*bounding_box)]
        bbox_geojson = [json.loads(json.dumps(bbox_geom[0].__geo_interface__))]

        # Crop the raster to the bounding box
        cropped_image, cropped_transform = mask(reprojected, bbox_geojson, crop=True)

        # Update metadata for the cropped output
        cropped_meta = reprojected.meta.copy()
        cropped_meta.update({
            'transform': cropped_transform,
            'width': cropped_image.shape[2],  # (bands, height, width)
            'height': cropped_image.shape[1],
            'dtype': cropped_image.dtype  # Ensure correct dtype
        })

        # Save the final cropped raster
        with rasterio.open(file_path_result, 'w', **cropped_meta) as dst:
            dst.write(cropped_image)

    print(f"Reprojection and cropping complete! Output saved as '{file_path_result}'.")


def merge_tiffs(tiffs, file_path):
    # Open all GeoTIFF files
    src_files_to_mosaic = []
    for fp in tiffs:
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
    with rasterio.open(file_path, "w", **out_meta) as dest:
        dest.write(mosaic)

    # Close all source files
    for src in src_files_to_mosaic:
        src.close()


def download_fileset(result_filepath_evi, result_filepath_ndvi, filesOI, folder_tmp, url, token, bbox, date, elements):
    mkfloder(folder_tmp)
    #folder_tmp = folder_tmp + '\\'
    output_tiffs_ndvi = []
    output_tiffs_evi = []
    for f in filesOI:
        if not os.path.isfile(os.path.join(folder_tmp,f)):
            # download hdf file
            download_modis_nasa(f,folder_tmp,url, token)

    for f in filesOI:
        # to tiff
        output_tiff = to_tiff(f, folder_tmp, elements)
        print(f"GeoTIFF saved to {output_tiff}")
        output_tiffs_ndvi.append(output_tiff[0])
        output_tiffs_evi.append(output_tiff[1])
    
    file_merger_tmp = os.path.join(folder_tmp, str(date) + '_ndvi.tif')
    merge_tiffs(output_tiffs_ndvi, file_merger_tmp)
    reproject_and_crop(bbox, result_filepath_ndvi, file_merger_tmp, folder_tmp, date)

    file_merger_tmp = os.path.join(folder_tmp,str(date) + '_evi.tif')
    merge_tiffs(output_tiffs_evi, file_merger_tmp)
    reproject_and_crop(bbox, result_filepath_evi, file_merger_tmp, folder_tmp, date)
    shutil.rmtree(folder_tmp)


def get_modis_vi(json_file, name, datum):
    parameter = utils.get_parameter(json_file,'bbox.json')
    bbox = parameter['bbox']
    for v in parameter['variables']:
        if v['name'] == name:
            url = v['url']
            elements = v['elements']
            break

    # Create a client for the CDS API
    file = os.path.join(secrets_folder, 'nasa.sct')

    with open(file, 'r') as f:
            credentials = yaml.safe_load(f)
    token = credentials['token']
    
    file_dict = get_links(url)
    # Convert string to date
    date = datetime.strptime(datum, '%Y-%m-%d').date()
    url = file_dict[date]

    files = get_filelinks(url)
    
    x = latlon_to_modis_tile(bbox[0], bbox[1])
    y = latlon_to_modis_tile(bbox[2], bbox[3])
    modis_bbox = list(x+y)

    filesOI = is_within_bounding_box(files, modis_bbox)
    
    folder_tmp = os.path.join(download_folder, parameter['type'], name, 'tmp', str(date))
    evi_folder = os.path.join(download_folder, parameter['type'], name, 'evi' ,str(date.year))
    ndvi_folder = os.path.join(download_folder, parameter['type'], name, 'ndvi' ,str(date.year))
    mkfloder(evi_folder)
    mkfloder(ndvi_folder)
    result_filepath_evi = os.path.join(evi_folder, str(date) + '.tif')
    result_filepath_ndvi = os.path.join(ndvi_folder, str(date) + '.tif')
    download_fileset(result_filepath_evi, result_filepath_ndvi, filesOI, folder_tmp, url, token, bbox, date, elements)
    
    