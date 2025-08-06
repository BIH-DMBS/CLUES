import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import os
import json
import glob
import zipfile
import shutil
from rasterio.merge import merge
import rasterio
import yaml
import time

try:
    from .config import download_folder, configs_assets_folder, area, config_folder, secrets_folder, tmp_folder
except:
    from config import download_folder, configs_assets_folder, area, config_folder, secrets_folder, tmp_folder


def extract_tif_from_nested_folder(zip_file_path, extract_to_path):
    # this extracts the tif of interest from a zip (folder target_folder at depth 3)
    # this is directly how the tif file of interst is located in the raw zip file downloaded from odata copernicus
    # tif file of interst is saved to extract_to_path
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            # Check if the member path matches the target folder pattern
            if '/DEM/' in member and member.endswith('.tif'):
                source = zip_ref.open(member)
                target = os.path.join(extract_to_path, os.path.basename(member))
                with open(target, "wb") as f:
                    f.write(source.read())
                source.close()


# to download data access token from copernicus a needed
def get_copernicus_odata_token():
    # The function retrieves an access token from the Copernicus Data Space Ecosystem (CDSE).
    # It extracts the access token from the response and returns it.
    url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Create a client for the CDS API
    credential_file = os.path.join(secrets_folder, 'copernicus_credential.sct')

    with open(credential_file, 'r') as f:
            credentials = yaml.safe_load(f)

    response = requests.post(url, headers=headers, data=credentials)

    # Access the generated access token
    access_token = response.json().get('access_token')
    return access_token


def generate_bboxes(bbox_str):
    # imput a bounding box
    # returns a set of bounding box of size 1° latitude and longitude
    # the tiles start only at a coordinate without decimal places 
    # that cover the input bounding box
    # Parse the bbox string to extract coordinates
    coords = bbox_str.strip('()').split(', ')
    coords = [tuple(map(float, coord.split())) for coord in coords]
    # Get min and max longitude (x) and latitude (y)
    min_x = np.floor(min(coord[0] for coord in coords))
    max_x = np.ceil(max(coord[0] for coord in coords))
    min_y = np.floor(min(coord[1] for coord in coords))
    max_y = np.ceil(max(coord[1] for coord in coords))

    # Generate bboxes of size 1°
    bboxes = []
    x = min_x
    while x < max_x:
        y = min_y
        while y < max_y:
            bbox = [
                (x, y + 1),
                (x + 1, y + 1),
                (x + 1, y),
                (x, y),
                (x, y + 1)
            ]
            bbox_str = ', '.join(f"{coord[0]} {coord[1]}" for coord in bbox)
            bboxes.append(f"({bbox_str})")
            y += 1
        x += 1
    
    return bboxes


def prepare_path(path):
    # check if path exists 
    #   if not create path 
    #   if remove folder content
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        shutil.rmtree(path)
        os.makedirs(path)


def downloadDEM_zip(df_links, parameters):
    # download raw zip file
    # extract file of interest
    # remove downloaded zip file
    
    # Specify the file names
    result_path = os.path.join(download_folder, parameters['type'], parameters['variables'][0]['name'])

    # set temporary folders for download the raw data and extracting the zip files
    tmp_folder = os.path.join(result_path,'tmp')
    
    prepare_path(result_path)
    prepare_path(tmp_folder)

    access_token = get_copernicus_odata_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    # Create a session and update headers
    session = requests.Session()

    session.headers.update(headers)

    url = 'https://download.dataspace.copernicus.eu/odata/v1/Products'

    for id in df_links['Id']:
        url_download = f"{url}({id})/$value"

        # Perform the GET request
        response = session.get(url_download, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            with open(os.path.join(tmp_folder,f"{id}.zip"), "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        file.write(chunk)
                print(f"{id}.zip downloaded")
        else:
            # try with new token
            access_token = get_copernicus_odata_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            # Create a session and update headers
            session = requests.Session()
            session.headers.update(headers)
            # Perform the GET request
            response = session.get(url_download, stream=True)

            if response.status_code == 200:
                with open(os.path.join(tmp_folder,f"{id}.zip"), "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            file.write(chunk)
                    print(f"{id}.zip downloaded with new access token")
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
                print(response.text)
    
    zip_files = glob.glob(os.path.join(tmp_folder, '*.zip'))
    for zip_file in zip_files:
        # extract tif files
        extract_tif_from_nested_folder(zip_file, result_path)

    shutil.rmtree(tmp_folder)

    # create the flag file that tells snakemake the download is done
    file_path = os.path.join(result_path, 'done.txt')
    with open(file_path, 'w') as f:
        pass  # Create an empty file


# Function to transpose bounding box format
def transpose_bounding_box(bbox):
    # the format of the bounding box from the confog is not the same as expected by the odata copernicus service
    # input the bbox in the format of the config returns int the format odata expects
    lat1, lon1, lat2, lon2 = bbox
    return f"({lon1:.1f} {lat1:.0f}, {lon2:.1f} {lat1:.0f}, {lon2:.1f} {lat2:.0f}, {lon1:.1f} {lat2:.0f}, {lon1:.1f} {lat1:.0f})"


def getInfoCopenicusDEM(parameters_jsonfile, vOI):

    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
        parameters = json.load(file)

    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)

    parameters['variables'] = [y for y in parameters['variables'] if y['name']==vOI] 
    parameters["bbox"] = bbox[area]

    bbox = transpose_bounding_box(parameters["bbox"])
    
    # using the full bbox does not proper work (requesting the url 
    # leads to 'holes' in the aera o interest)
    # request each patch seperatly (one degree latitude and longitude)
    coords = generate_bboxes(bbox)
    
    df_links = pd.DataFrame()# = pd.DataFrame.from_dict(json['value'])
    collection = 'COP-DEM'
    url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
    max_retries = 20
    for c in coords:
        filt=f"((Collection/Name eq '{collection}' and\
            OData.CSC.Intersects(area=geography'SRID=4326;POLYGON ({c})')) )"
        url_filt=f"{url}?$filter={filt}"
        for i in range(1000):
            retry_count = 0
            while retry_count < max_retries:
                response = requests.get(url_filt)
                if response.status_code != 200:
                    print('response.status_code')
                    print(response.status_code)
                    retry_count += 1
                    time.sleep(1)  # Wait for 1 second before retrying
                    print('retry')
                else:
                    json_lnks = requests.get(url_filt)
                    json_lnks = json_lnks.json()
                    df_tmp = pd.DataFrame.from_dict(json_lnks['value'])
                    df_links = pd.concat([df_links, df_tmp])
                    break
            try:
                url_filt = json_lnks["@odata.nextLink"]
                print(url_filt)
            except:
                print(f'done at iter: {i}')
                break
    
    df_links = df_links.drop_duplicates(subset=['Name'])
    # Convert the 'GeoFootprint' column to shapely geometries
    df_links['geometry'] = df_links['GeoFootprint'].apply(lambda x: shape(x))
    # Create a GeoDataFrame
    df_links = gpd.GeoDataFrame(df_links, geometry='geometry')

    # Filter the DataFrame for asset of interest
    df_links = df_links[df_links['Name'].str.contains(parameters['variables'][0]['resolution'], case=False, na=False)]
    df_links = df_links.drop_duplicates(subset=['geometry'])
    downloadDEM_zip(df_links, parameters)
