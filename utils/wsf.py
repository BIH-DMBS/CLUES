import requests
import math
from bs4 import BeautifulSoup
import os
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from glob import glob
import re
import shutil

import utils

try:
    from .config import download_folder
except:
    from config import download_folder


def get_inbox(file_coordinate_dict, bbox):
    in_box = {}
    latitude = list(range(math.floor(bbox[2]), math.ceil(bbox[0]) + 1))
    longitude = list(range(math.floor(bbox[1]), math.ceil(bbox[3]) + 1))
    for fileOI, coordinate in file_coordinate_dict.items():
        lat, lon = coordinate
        if lon in longitude and lat in latitude:
            in_box[fileOI] = coordinate
    return in_box


def merge_geotiffs_(input_folder, output_file_path):
    """
    Merge all GeoTIFF files in a folder into a single compressed GeoTIFF.

    Args:
        input_folder (str): Path to folder containing GeoTIFFs.
        output_file_path (str): Full path for the output file.
    """
    tiff_files = glob(os.path.join(input_folder, "*.tif"))

    if not tiff_files:
        raise FileNotFoundError(f"No .tif files found in folder: {input_folder}")

    src_files_to_mosaic = [rasterio.open(fp) for fp in tiff_files]
    mosaic, out_transform = merge(src_files_to_mosaic)

    out_meta = src_files_to_mosaic[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_transform,
        "compress": "lzw",  # Use compression (can also try 'deflate')
        "tiled": True,      # Enables internal tiling for better access performance
        "blockxsize": 512,  # Tile width (can be tuned)
        "blockysize": 512,  # Tile height
        "BIGTIFF": "IF_SAFER"  # Create BigTIFF only if needed
    })

    with rasterio.open(output_file_path, "w", **out_meta) as dest:
        dest.write(mosaic)

    for src in src_files_to_mosaic:
        src.close()

    print(f"Compressed merged GeoTIFF saved to: {output_file_path}")


def merge_geotiffs(input_folder, output_file_path):
    tiff_files = glob(os.path.join(input_folder, "*.tif"))
    if not tiff_files:
        raise FileNotFoundError(f"No .tif files found in folder: {input_folder}")

    sources = [rasterio.open(fp) for fp in tiff_files]

    # Compute total bounds manually
    min_x, min_y, max_x, max_y = sources[0].bounds
    for src in sources[1:]:
        left, bottom, right, top = src.bounds
        min_x = min(min_x, left)
        min_y = min(min_y, bottom)
        max_x = max(max_x, right)
        max_y = max(max_y, top)

    dst_crs = sources[0].crs
    dst_res = sources[0].res
    dst_dtype = sources[0].dtypes[0]
    dst_count = sources[0].count

    out_width = int((max_x - min_x) / dst_res[0])
    out_height = int((max_y - min_y) / dst_res[1])
    transform = from_bounds(min_x, min_y, max_x, max_y, out_width, out_height)

    out_meta = {
        "driver": "GTiff",
        "height": out_height,
        "width": out_width,
        "count": dst_count,
        "dtype": dst_dtype,
        "crs": dst_crs,
        "transform": transform,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512
    }
    i = 0
    with rasterio.open(output_file_path, "w", **out_meta) as dest:
        for src in sources:
            print(src)
            print(i)
            i=i+1
            # Get destination window where this src should go
            window = rasterio.windows.from_bounds(*src.bounds, transform=transform)
            window = window.round_offsets().round_lengths()

            data = src.read()  # Read with native shape, no resampling
            dest.write(data, window=window)

    for src in sources:
        src.close()

def mkfloder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def download_wsf(json_file, vOI):
    print(json_file)
    print(vOI)
    parameter = utils.get_parameter(json_file,'bbox.json')
    bbox = parameter['bbox']
    for v in parameter['variables']:
        if v['name'] == vOI:
            url = v['url']
            res_file = v['flagFile']
            break
    print(url)
    print(res_file)
    print(parameter['type'])
    print(download_folder)
    output_folder =  os.path.join(download_folder,  parameter['type'])
    output_folder_tmp =  os.path.join(download_folder,  parameter['type'], vOI)
    output_filepath =  os.path.join(output_folder, res_file)
    print(output_folder)
    mkfloder(output_folder)
    mkfloder(output_folder_tmp)
    get_wsf(url, bbox, output_folder, output_filepath, output_folder_tmp)

def get_wsf(url, bbox, output_folder, output_file_path, output_folder_tmp):

    if url == "https://download.geoservice.dlr.de/WSF2019/files/":
        response = requests.get(url)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all links on the page
        links = soup.find_all('a')

        # Extract the file names
        links = [link.get('href') for link in links if link.get('href').endswith('.tif')]

        # Extract content between 'WSF2015_v2_' and '/'
        file_coord_dict = {}
        for name in links:
            try:
                tmp = name.strip('.tif').split('_')
                tmp = (int(tmp[3]),int(tmp[2]))
                file_coord_dict[name] = tmp
            except:
                pass

        inbox_file_coordinate_dict = get_inbox(file_coord_dict, bbox)
        print(inbox_file_coordinate_dict)

        # download tiles of interest
        for lnk, v in inbox_file_coordinate_dict.items():
            link = url + lnk
            download = requests.get(link)
            # Check if the request was successful
            if download.status_code == 200:
                # Save the content to a file
                with open(os.path.join(output_folder_tmp, lnk), 'wb') as file:
                    file.write(download.content)
                print('Download completed successfully.')
            else:
                print(f'Failed to download file. Status code: {response.status_code}')

    else:
        response = requests.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        wsf_folders = [row.find_all('td')[0].text for row in table.find_all('tr')[1:]]  # Adjust index if needed

        # Filter folder names that start with '******_**_' and end with '/'
        wsf_folders = [folder for folder in wsf_folders if re.match(r'^[^/]+_[^/]+_.*\/$', folder)]

        # Extract content between 'WSF2015_v2_' and '/'
        folder_coord_dict = {}
        for name in wsf_folders:
            tmp = name.strip('/').split('_')
            tmp = (int(tmp[3]),int(tmp[2]))
            folder_coord_dict[name] = tmp
        
        #print(folder_coord_dict)
        #{'WSFevolution_v1_-100_16/': (16, -100), 'WSFevolution_v1_-100_18/': (18, -100), 'WSFevolution_v1_-100_20/': (20, -100), 'WSFevolution_v1_-100_22/': (22, -100), 
        inbox_file_coordinate_dict = get_inbox(folder_coord_dict, bbox)
        print(inbox_file_coordinate_dict)

        link_dict = {}
        for fileOI, coordinate in inbox_file_coordinate_dict.items():
            x = url+fileOI
            response = requests.get(x)
            # Find all links on the page
            html_content = response.content

            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all links on the page
            links = soup.find_all('a')

            # Extract the file names
            link_dict[fileOI] = [link.get('href') for link in links if link.get('href').endswith('.tif')][0]
    
        # download tiles of interest
        for k,v in link_dict.items():
            link = url + k + link_dict[k]
            download = requests.get(link)
            # Check if the request was successful
            if download.status_code == 200:
                # Save the content to a file
                with open(os.path.join(output_folder_tmp, link_dict[k]), 'wb') as file:
                    file.write(download.content)
                print('Download completed successfully.')
            else:
                print(f'Failed to download file. Status code: {response.status_code}')

    merge_geotiffs(output_folder_tmp, output_file_path)
    shutil.rmtree(output_folder_tmp)
    print('download successfull: ' + output_file_path)