import requests
import numpy as np
import os
import json
import shutil
import time

try:
    from .config import download_folder, configs_assets_folder, area, config_folder
except:
    from config import download_folder, configs_assets_folder, area, config_folder


# The Copernicus DEM (GLO-30 / GLO-90) is downloaded from the public AWS Open Data registry
# (https://registry.opendata.aws/copernicus-dem/). No account or token is needed.
# The download via the Copernicus Data Space Ecosystem (odata, collection 'CCM') is restricted
# for most accounts (403, DAT-ZIP-608 'Access forbidden').
# Each tile covers 1° latitude x 1° longitude and is a cloud optimized GeoTIFF.
AWS_DEM = {
    # resolution (from the config) -> (bucket url, code in the file name)
    '30': ('https://copernicus-dem-30m.s3.amazonaws.com', '10'),
    '90': ('https://copernicus-dem-90m.s3.amazonaws.com', '30'),
}


def prepare_path(path):
    # check if path exists
    #   if not create path
    #   if remove folder content
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        shutil.rmtree(path)
        os.makedirs(path)


def generate_tiles(bbox):
    # input the bbox in the format of the config [lat_max, lon_min, lat_min, lon_max]
    # returns the lower left corners (lat, lon) of all 1° tiles covering the bbox
    lat1, lon1, lat2, lon2 = bbox
    lats = np.arange(np.floor(min(lat1, lat2)), np.ceil(max(lat1, lat2)))
    lons = np.arange(np.floor(min(lon1, lon2)), np.ceil(max(lon1, lon2)))
    return [(int(lat), int(lon)) for lat in lats for lon in lons]


def tile_url(lat, lon, resolution):
    # e.g. .../Copernicus_DSM_COG_10_N53_00_E013_00_DEM/Copernicus_DSM_COG_10_N53_00_E013_00_DEM.tif
    bucket, code = AWS_DEM[resolution]
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    name = f"Copernicus_DSM_COG_{code}_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    return f"{bucket}/{name}/{name}.tif", f"{name}.tif"


def download_tile(session, url, target, max_retries=5):
    # returns True if downloaded, False if the tile does not exist (e.g. ocean tiles)
    for retry in range(max_retries):
        try:
            with session.get(url, stream=True, timeout=120) as response:
                if response.status_code == 404:
                    return False
                response.raise_for_status()
                # write to a temporary file first, so no incomplete tif remains on errors
                with open(target + '.part', 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
            os.replace(target + '.part', target)
            return True
        except requests.RequestException as e:
            print(f"{url}: {e}, retry {retry + 1}/{max_retries}")
            time.sleep(5)
    raise RuntimeError(f"Failed to download {url}")


def getInfoCopenicusDEM(parameters_jsonfile, vOI):

    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
        parameters = json.load(file)

    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)

    parameters['variables'] = [y for y in parameters['variables'] if y['name']==vOI]
    parameters["bbox"] = bbox[area]

    # 'resolution' in the config is e.g. DEM1_SAR_DGE_30 or DEM1_SAR_DGE_90
    resolution = parameters['variables'][0]['resolution'][-2:]

    result_path = os.path.join(download_folder, parameters['type'], parameters['variables'][0]['name'])
    prepare_path(result_path)

    tiles = generate_tiles(parameters["bbox"])
    print(f"{len(tiles)} tiles to check")

    n_downloaded = 0
    with requests.Session() as session:
        for lat, lon in tiles:
            url, file_name = tile_url(lat, lon, resolution)
            if download_tile(session, url, os.path.join(result_path, file_name)):
                n_downloaded += 1
                print(f"{file_name} downloaded")
            else:
                print(f"{file_name} not available (no land)")

    if n_downloaded == 0:
        raise RuntimeError(f"No DEM tiles downloaded for area '{area}'")
    print(f"{n_downloaded} of {len(tiles)} tiles downloaded")

    # create the flag file that tells snakemake the download is done
    file_path = os.path.join(result_path, 'done.txt')
    with open(file_path, 'w') as f:
        pass  # Create an empty file
