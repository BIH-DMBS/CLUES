import json
import math
import os
import shutil

import rasterio
from rasterio.windows import Window, from_bounds

from copernicusDEM import download_tile

try:
    from .config import download_folder, configs_assets_folder, tmp_folder, area, config_folder
except ImportError:
    from config import download_folder, configs_assets_folder, tmp_folder, area, config_folder


# World Settlement Footprint (WSF 2015, WSF 2019, WSF Evolution) of the German Aerospace Center (DLR).
#
# The data is offered as tiles of 2 degree x 2 degree on https://download.geoservice.dlr.de.
# A tile is named after its lower left corner (longitude, latitude, both even numbers), e.g.
# WSF2019_v1_12_52.tif covers 12 E - 14 E and 52 N - 54 N (plus a small overlap to its neighbours).
# Tiles without any settlement (sea) do not exist.
#
# All tiles that overlap the area of interest are downloaded and the part inside the area is
# written to one GeoTIFF. The pixels are copied unchanged:
#   WSF 2015 / 2019:  255 = settlement, 0 = no settlement
#   WSF Evolution:    year (1985 - 2015) in which the pixel became settlement, 0 = no settlement

TILE_SIZE_DEG = 2


def tiles_of_bbox(bbox):
    """
    Lower left corners (lon, lat) of all tiles that overlap the bbox [lat_max, lon_min, lat_min, lon_max].
    """
    lat_max, lon_min, lat_min, lon_max = bbox

    def first_corner(value):
        return math.floor(value / TILE_SIZE_DEG) * TILE_SIZE_DEG

    lons = range(first_corner(lon_min), math.ceil(lon_max / TILE_SIZE_DEG) * TILE_SIZE_DEG, TILE_SIZE_DEG)
    lats = range(first_corner(lat_min), math.ceil(lat_max / TILE_SIZE_DEG) * TILE_SIZE_DEG, TILE_SIZE_DEG)
    return [(lon, lat) for lat in lats for lon in lons]


def tile_url(variable, lon, lat):
    # 'tile' in the config is the path of a tile below 'url', with the placeholders {lon} and {lat}
    path = variable['tile'].format(lon=lon, lat=lat)
    return variable['url'].rstrip('/') + '/' + path, os.path.basename(path)


def merge_tiles(tile_files, bbox, output_file_path, margin_in_pixel=10):
    """
    Write the part of the tiles that lies inside the bbox [lat_max, lon_min, lat_min, lon_max] to one GeoTIFF.

    The pixel grid of the first tile is used for the result. The tiles are copied one after the other,
    so only one tile is in memory. Where no tile exists (sea) the result is 0 (no settlement).
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    with rasterio.open(tile_files[0]) as first:
        profile = first.profile.copy()
        xres, yres = first.res
        # origin of the result: a pixel corner of the first tile, so the pixels are not shifted
        west = first.bounds.left + math.floor((lon_min - first.bounds.left) / xres - margin_in_pixel) * xres
        north = first.bounds.top - math.floor((first.bounds.top - lat_max) / yres - margin_in_pixel) * yres
    width = math.ceil((lon_max - west) / xres) + margin_in_pixel
    height = math.ceil((north - lat_min) / yres) + margin_in_pixel
    transform = rasterio.transform.from_origin(west, north, xres, yres)

    profile.update(driver='GTiff', width=width, height=height, transform=transform, compress='lzw',
                   tiled=True, blockxsize=512, blockysize=512, BIGTIFF='IF_SAFER')
    with rasterio.open(output_file_path, 'w', **profile) as dst:
        for tile_file in tile_files:
            with rasterio.open(tile_file) as src:
                if abs(src.res[0] - xres) > 1e-12 or abs(src.res[1] - yres) > 1e-12:
                    raise RuntimeError(f"{tile_file} has another pixel size than {tile_files[0]}")
                # position of the tile in the result, in whole pixels
                window = from_bounds(*src.bounds, transform=transform)
                col_off, row_off = round(window.col_off), round(window.row_off)
                # part of the tile that lies inside the result
                col_start, row_start = max(col_off, 0), max(row_off, 0)
                col_stop, row_stop = min(col_off + src.width, width), min(row_off + src.height, height)
                if col_stop <= col_start or row_stop <= row_start:
                    continue
                data = src.read(window=Window(col_start - col_off, row_start - row_off,
                                              col_stop - col_start, row_stop - row_start))
                dst.write(data, window=Window(col_start, row_start, col_stop - col_start, row_stop - row_start))
    print(f"{len(tile_files)} tiles merged, {width} x {height} pixels")


def download_wsf(json_file, vOI):
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    with open(os.path.join(configs_assets_folder, json_file), 'r', encoding='utf-8') as file:
        parameters = json.load(file)
    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)[area]

    variable = next((v for v in parameters['variables'] if v['name'] == vOI), None)
    if variable is None:
        raise ValueError(f"Variable '{vOI}' is not listed in '{json_file}'")

    output_folder = os.path.join(download_folder, parameters['type'])
    output_file_path = os.path.join(output_folder, variable['flagFile'])
    tiles_folder = os.path.join(tmp_folder, 'wsf_' + variable['name'])
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(tiles_folder, exist_ok=True)

    part = output_file_path + '.part'
    try:
        tile_files = []
        missing = 0
        for lon, lat in tiles_of_bbox(bbox):
            url, file_name = tile_url(variable, lon, lat)
            target = os.path.join(tiles_folder, file_name)
            status = download_tile(url, target)
            if status == 'missing':
                missing += 1
                print(f"{file_name} not available (no settlement in this tile)")
            else:
                tile_files.append(target)
                print(f"{file_name} {status}")
        if not tile_files:
            raise RuntimeError(f"No tiles of {vOI} available for area '{area}' {bbox}")
        print(f"{len(tile_files)} tiles available, {missing} not available")

        merge_tiles(tile_files, bbox, part)
        os.replace(part, output_file_path)
    finally:
        if os.path.exists(part):
            os.remove(part)

    # the tiles are only needed for the merge
    shutil.rmtree(tiles_folder, ignore_errors=True)
    print('download successfull: ' + output_file_path)
