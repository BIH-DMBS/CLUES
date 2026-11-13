import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from copernicusDEM import download_tile

try:
    from .config import download_folder, configs_assets_folder, area, config_folder
except ImportError:
    from config import download_folder, configs_assets_folder, area, config_folder


# Global tree cover in tiles of 10 degree x 10 degree:
#   global_tree_cover_hansen_2000   tree cover in the year 2000 in percent, Hansen et al.
#                                   (Global Forest Change), about 30 m
#   Global_forest_cover_2020        forest (1) / no forest (0) in 2020, Joint Research Centre (JRC), about 10 m
#
# In both products a tile is named after its upper left corner: the tile '60N_010E' (Hansen) or
# 'N60', 'E10' (JRC) covers 50 N - 60 N and 10 E - 20 E. All tiles that overlap the area of
# interest are downloaded completely (a few hundred MB each) and stored as they are.

# number of tiles downloaded at the same time
N_PARALLEL = 4


def tiles_of_bbox(bbox):
    """
    Upper left corners (lat, lon) of all 10 degree tiles that overlap the bbox
    [lat_max, lon_min, lat_min, lon_max]. The tiles exist between 80 N and 60 S.
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    tiles = []
    for lat in range(80, -60, -10):            # top edge of the tile: 80 N ... 50 S
        for lon in range(-180, 180, 10):       # left edge of the tile: 180 W ... 170 E
            tile_north, tile_west, tile_south, tile_east = lat, lon, lat - 10, lon + 10
            lat_overlap = not (tile_south >= lat_max or tile_north <= lat_min)
            lon_overlap = not (tile_east <= lon_min or tile_west >= lon_max)
            if lat_overlap and lon_overlap:
                tiles.append((lat, lon))
    return tiles


def tile_url_hansen(base_url, lat, lon):
    lat_label = f"{abs(lat):02d}{'N' if lat >= 0 else 'S'}"
    lon_label = f"{abs(lon):03d}{'W' if lon < 0 else 'E'}"
    return f"{base_url}Hansen_GFC-2022-v1.10_treecover2000_{lat_label}_{lon_label}.tif", f"GFC_{lat_label}_{lon_label}.tif"


def tile_url_2020(base_url, lat, lon):
    lat_label = f"{'N' if lat >= 0 else 'S'}{abs(lat):01d}"
    lon_label = f"{'W' if lon < 0 else 'E'}{abs(lon):01d}"
    return f"{base_url}&lat={lat_label}&lon={lon_label}", f"GFC_{lat_label}_{lon_label}.tif"


TILE_URL = {
    'global_tree_cover_hansen_2000': tile_url_hansen,
    'Global_forest_cover_2020': tile_url_2020,
}


def getTC_global(parameters_jsonfile, vOI):
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
        parameters = json.load(file)
    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)[area]

    variable = next((v for v in parameters['variables'] if v['name'] == vOI), None)
    if variable is None:
        raise ValueError(f"Variable '{vOI}' is not listed in '{parameters_jsonfile}'")
    if vOI not in TILE_URL:
        raise ValueError(f"No download defined for '{vOI}', known: {sorted(TILE_URL)}")

    download_path = os.path.join(download_folder, parameters['type'], variable['name'])
    os.makedirs(download_path, exist_ok=True)

    jobs = [TILE_URL[vOI](variable['url'], lat, lon) for lat, lon in tiles_of_bbox(bbox)]
    print(f"{len(jobs)} tiles to check")

    # remove what does not belong to the requested area (tiles of an earlier run for another area,
    # leftovers of an interrupted download). Complete tiles of the area are kept and not downloaded again.
    wanted = {file_name for _, file_name in jobs}
    for old_file in glob.glob(os.path.join(download_path, '*.tif')) + glob.glob(os.path.join(download_path, '*.part')):
        if os.path.basename(old_file) not in wanted:
            os.remove(old_file)

    def run(job):
        url, file_name = job
        return file_name, download_tile(url, os.path.join(download_path, file_name))

    with ThreadPoolExecutor(max_workers=N_PARALLEL) as executor:
        results = list(executor.map(run, jobs))

    for file_name, status in results:
        print(f"{file_name}: {status}")
    available = sorted(file_name for file_name, status in results if status != 'missing')
    if not available:
        raise RuntimeError(f"No tiles of {vOI} available for area '{area}' {bbox}")

    # flag file that tells snakemake the download is complete
    with open(os.path.join(download_path, 'done.flag'), 'w') as f:
        f.write(f"Data was downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"area: {area} {bbox}\n")
        f.write(f"{len(available)} tiles:\n")
        f.write('\n'.join(available) + '\n')
    return 0
