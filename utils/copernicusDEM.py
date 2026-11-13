import glob
import json
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

try:
    from .config import download_folder, configs_assets_folder, area, config_folder
except ImportError:
    from config import download_folder, configs_assets_folder, area, config_folder


# The Copernicus DEM (GLO-30 / GLO-90) is downloaded from the public AWS Open Data registry
# (https://registry.opendata.aws/copernicus-dem/). No account or token is needed.
# The download via the Copernicus Data Space Ecosystem (odata, collection 'CCM') is restricted
# for most accounts (403, DAT-ZIP-608 'Access forbidden').
# Each tile covers 1° latitude x 1° longitude and is a cloud optimized GeoTIFF.

# resolution (last two characters of 'resolution' in the config) -> code in the file name (arc seconds)
RESOLUTION_CODE = {'30': '10', '90': '30'}

# number of tiles downloaded at the same time
N_PARALLEL = 8

_thread_local = threading.local()


def get_session():
    # one session per thread, requests sessions are not safe to share between threads
    if not hasattr(_thread_local, 'session'):
        _thread_local.session = requests.Session()
    return _thread_local.session


def pad_bbox_m(bbox, margin_in_meter):
    """
    Widen the bbox [lat_max, lon_min, lat_min, lon_max] by a margin given in metres.
    The neighbourhood filters need the elevation up to their radius around every location,
    also for locations at the border of the area.
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    if margin_in_meter <= 0:
        return list(bbox)
    margin_lat = margin_in_meter / 111000.0
    # a degree of longitude gets shorter towards the poles
    cos_lat = max(math.cos(math.radians(min(89.0, max(abs(lat_max), abs(lat_min)) + margin_lat))), 0.01)
    margin_lon = margin_lat / cos_lat
    return [
        min(90.0, lat_max + margin_lat),
        max(-180.0, lon_min - margin_lon),
        max(-90.0, lat_min - margin_lat),
        min(180.0, lon_max + margin_lon),
    ]


def max_neighborhood_radius(variable):
    # largest radius (in metres) of the neighbourhood filters configured for the variable
    radii = [0]
    for fltr, value in variable.get('neighborhood', {}).items():
        if fltr in ('mean', 'std'):
            radii.extend(value)
    return max(radii)


def generate_tiles(bbox):
    # input the bbox in the format of the config [lat_max, lon_min, lat_min, lon_max]
    # returns the lower left corners (lat, lon) of all 1° tiles covering the bbox
    lat1, lon1, lat2, lon2 = bbox
    lat_from, lat_to = math.floor(min(lat1, lat2)), math.ceil(max(lat1, lat2))
    lon_from, lon_to = math.floor(min(lon1, lon2)), math.ceil(max(lon1, lon2))
    lat_from, lat_to = max(lat_from, -90), min(lat_to, 90)
    lon_from, lon_to = max(lon_from, -180), min(lon_to, 180)
    return [(lat, lon) for lat in range(lat_from, lat_to) for lon in range(lon_from, lon_to)]


def tile_url(lat, lon, resolution, bucket):
    # e.g. .../Copernicus_DSM_COG_10_N53_00_E013_00_DEM/Copernicus_DSM_COG_10_N53_00_E013_00_DEM.tif
    code = RESOLUTION_CODE[resolution]
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    name = f"Copernicus_DSM_COG_{code}_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    return f"{bucket.rstrip('/')}/{name}/{name}.tif", f"{name}.tif"


def download_tile(url, target, max_retries=5):
    """
    Download one tile.
    Returns 'downloaded', 'kept' (a complete file was already there) or
    'missing' (the tile does not exist, e.g. tiles without land).
    """
    for retry in range(max_retries):
        try:
            with get_session().get(url, stream=True, timeout=120) as response:
                if response.status_code == 404:
                    return 'missing'
                response.raise_for_status()
                size = int(response.headers.get('Content-Length', -1))
                if os.path.exists(target) and os.path.getsize(target) == size:
                    return 'kept'
                # write to a temporary file first, so no incomplete tif remains on errors
                with open(target + '.part', 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
            if size >= 0 and os.path.getsize(target + '.part') != size:
                raise requests.RequestException(
                    f"incomplete download, {os.path.getsize(target + '.part')} of {size} bytes")
            os.replace(target + '.part', target)
            return 'downloaded'
        except requests.RequestException as e:
            print(f"{url}: {e}, retry {retry + 1}/{max_retries}")
            time.sleep(5)
    raise RuntimeError(f"Failed to download {url}")


def getInfoCopenicusDEM(parameters_jsonfile, vOI):

    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
        parameters = json.load(file)

    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)

    variable = next((v for v in parameters['variables'] if v['name'] == vOI), None)
    if variable is None:
        raise ValueError(f"Variable '{vOI}' is not listed in '{parameters_jsonfile}'")

    # 'resolution' in the config is e.g. DEM1_SAR_DGE_30 or DEM1_SAR_DGE_90
    resolution = variable['resolution'][-2:]
    if resolution not in RESOLUTION_CODE:
        raise ValueError(f"Unknown resolution '{variable['resolution']}', it must end with 30 or 90")

    result_path = os.path.join(download_folder, parameters['type'], variable['name'])
    os.makedirs(result_path, exist_ok=True)

    tiles = generate_tiles(pad_bbox_m(bbox[area], max_neighborhood_radius(variable)))
    print(f"{len(tiles)} tiles to check")
    jobs = [tile_url(lat, lon, resolution, variable['url']) for lat, lon in tiles]

    # remove what does not belong to the requested area (tiles of an earlier run for another area,
    # leftovers of an interrupted download). Complete tiles of the area are kept and not downloaded again.
    wanted = {file_name for _, file_name in jobs}
    for old_file in glob.glob(os.path.join(result_path, '*.tif')) + glob.glob(os.path.join(result_path, '*.part')):
        if os.path.basename(old_file) not in wanted:
            os.remove(old_file)

    def run(job):
        url, file_name = job
        return file_name, download_tile(url, os.path.join(result_path, file_name))

    with ThreadPoolExecutor(max_workers=N_PARALLEL) as executor:
        results = list(executor.map(run, jobs))

    counts = {'downloaded': 0, 'kept': 0, 'missing': 0}
    for file_name, status in results:
        counts[status] += 1
    available = sorted(file_name for file_name, status in results if status != 'missing')
    print(f"{counts['downloaded']} tiles downloaded, {counts['kept']} already there, "
          f"{counts['missing']} not available (no land)")

    if not available:
        raise RuntimeError(f"No DEM tiles available for area '{area}'")

    # create the flag file that tells snakemake the download is done
    with open(os.path.join(result_path, 'done.txt'), 'w') as f:
        f.write(f"Data was downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"area: {area} {bbox[area]}\n")
        f.write(f"{len(available)} tiles:\n")
        f.write('\n'.join(available) + '\n')
