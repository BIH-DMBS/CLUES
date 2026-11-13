import io
import json
import math
import os
from time import sleep

import numpy as np
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from rasterio.windows import Window

import corine

try:
    from .config import download_folder, configs_assets_folder, area, config_folder
except ImportError:
    from config import download_folder, configs_assets_folder, area, config_folder


# Tree cover density and forest type of the Copernicus High Resolution Layers (HRL), taken from the
# services of the European Environment Agency (EEA).
#
# There are two kinds of services, the configuration says for every variable which one it is:
#
# "ImageServer"  delivers the values of the pixels (tree cover density in percent, forest type as
#                number). The data has a resolution of 10 m. It is read at a finer grid than the
#                result ('oversampling' x 'oversampling' values per pixel of the result) and
#                combined: the mean for a density ("aggregation": "mean"), the most frequent value
#                for classes ("aggregation": "mode").
# "MapServer"    only delivers a picture in the colours of the map legend. The colours are converted
#                to numbers with the 'legend' of the variable in the configuration. A colour that is
#                not in the legend is an error. For the tree cover density of 2012 and 2015 the map
#                has five classes only (1-20 %, ..., 81-100 %), the percent values are not available.
#
# The result is one GeoTIFF per variable in geographic coordinates (EPSG:4326), one band, 255 = no data.

NODATA = 255
# the services deliver at most 4096 pixels per side in one request
MAX_REQUEST_PIXELS = 4000


def request_values(url, west, south, east, north, columns, rows, max_retries=4):
    # values of the pixels from an ArcGIS image service as array (rows x columns)
    parameters = {
        'bbox': f'{west:.7f},{south:.7f},{east:.7f},{north:.7f}',
        'bboxSR': 4326,
        'imageSR': 4326,
        'size': f'{columns},{rows}',
        'format': 'tiff',
        'pixelType': 'U8',
        'interpolation': 'RSP_NearestNeighbor',
        'f': 'image',
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url.rstrip('/') + '/exportImage', params=parameters, timeout=300)
            response.raise_for_status()
            # the service reports errors as a json document with status code 200
            if not response.headers.get('Content-Type', '').startswith('image/tiff'):
                raise requests.RequestException(f"no data delivered: {response.text[:300]}")
            with MemoryFile(response.content) as memory_file, memory_file.open() as src:
                values = src.read(1)
            if values.shape != (rows, columns):
                raise requests.RequestException(f"data has the shape {values.shape}, expected {(rows, columns)}")
            return values
        except (requests.RequestException, rasterio.errors.RasterioError) as e:
            print(f"{url}: {e} (attempt {attempt}/{max_retries})")
            if attempt == max_retries:
                raise RuntimeError(f"Failed to get data from {url}") from e
            sleep(20)


def aggregate(values, factor, method, max_valid):
    """
    Combine factor x factor values to one value.

    values: array (rows * factor, columns * factor); numbers above max_valid are 'no data'
    method: 'mean' (rounded mean of the valid values) or 'mode' (most frequent valid value)
    Returns a uint8 array (rows, columns), NODATA where none of the values is valid.
    """
    rows, columns = values.shape[0] // factor, values.shape[1] // factor
    blocks = values.reshape(rows, factor, columns, factor).swapaxes(1, 2).reshape(rows, columns, factor * factor)
    valid = blocks <= max_valid
    n_valid = valid.sum(axis=2)
    result = np.full((rows, columns), NODATA, dtype=np.uint8)
    if method == 'mean':
        sums = np.where(valid, blocks, 0).sum(axis=2, dtype=np.float64)
        with np.errstate(invalid='ignore', divide='ignore'):
            mean = np.rint(sums / n_valid)
        result[n_valid > 0] = mean[n_valid > 0].astype(np.uint8)
    elif method == 'mode':
        best_count = np.zeros((rows, columns), dtype=np.int32)
        for value in np.unique(blocks[valid]):
            count = (blocks == value).sum(axis=2)
            better = count > best_count
            result[better] = value
            best_count[better] = count[better]
    else:
        raise ValueError(f"Unknown aggregation '{method}', use 'mean' or 'mode'")
    return result


def read_tile(variable, west, north, col, row, n_cols, n_rows, resolution):
    # values of one part of the result (n_rows x n_cols pixels, upper left pixel at col, row)
    tile_west, tile_north = west + col * resolution, north - row * resolution
    tile_east, tile_south = tile_west + n_cols * resolution, tile_north - n_rows * resolution
    if variable['service_type'] == 'ImageServer':
        factor = int(variable.get('oversampling', 1))
        values = request_values(variable['url'], tile_west, tile_south, tile_east, tile_north, n_cols * factor, n_rows * factor)
        return aggregate(values, factor, variable['aggregation'], int(variable.get('max_valid', 254)))
    if variable['service_type'] == 'MapServer':
        picture = corine.request_picture(variable['url'], variable['layer'], tile_west, tile_south, tile_east, tile_north, n_cols, n_rows)
        legend = [{'code': entry['value'], 'rgb': entry['rgb']} for entry in variable['legend']]
        return corine.decode_colours(picture, legend).astype(np.uint8)
    raise ValueError(f"Unknown service_type '{variable['service_type']}' of '{variable['name']}'")


def get_treecover(parameters_jsonfile, vOI):
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r', encoding='utf-8') as file:
        parameters = json.load(file)
    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)[area]

    variable = next((v for v in parameters['variables'] if v['name'] == vOI), None)
    if variable is None:
        raise ValueError(f"Variable '{vOI}' is not listed in '{parameters_jsonfile}'")

    resolution = float(parameters.get('resolution_deg', 0.001))
    west, north, columns, rows = corine.output_grid(bbox, resolution)
    # size of one request in pixels of the result
    tile_size = MAX_REQUEST_PIXELS // int(variable.get('oversampling', 1)) if variable['service_type'] == 'ImageServer' else MAX_REQUEST_PIXELS
    print(f"{vOI}: {columns} x {rows} pixels of {resolution} degree, {variable['service_type']}")

    folder = os.path.join(download_folder, parameters['type'])
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, variable['name'] + '.tif')
    part = file_path + '.part'

    profile = {
        'driver': 'GTiff', 'dtype': 'uint8', 'count': 1, 'width': columns, 'height': rows,
        'crs': 'EPSG:4326', 'transform': from_origin(west, north, resolution, resolution),
        'nodata': NODATA, 'compress': 'deflate', 'tiled': True, 'blockxsize': 256, 'blockysize': 256,
        'BIGTIFF': 'IF_SAFER',
    }
    try:
        with rasterio.open(part, 'w', **profile) as dst:
            dst.update_tags(content=variable.get('content', ''), year=str(variable.get('year', '')), source=variable['url'])
            for row in range(0, rows, tile_size):
                for col in range(0, columns, tile_size):
                    n_rows, n_cols = min(tile_size, rows - row), min(tile_size, columns - col)
                    values = read_tile(variable, west, north, col, row, n_cols, n_rows, resolution)
                    dst.write(values, 1, window=Window(col, row, n_cols, n_rows))
        os.replace(part, file_path)
    finally:
        if os.path.exists(part):
            os.remove(part)
    print(f"saved as {file_path}")
