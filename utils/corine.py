import csv
import io
import json
import math
import os
from time import sleep

import numpy as np
import rasterio
import requests
from PIL import Image
from rasterio.transform import from_origin
from rasterio.windows import Window

try:
    from .config import download_folder, configs_assets_folder, area, config_folder
except ImportError:
    from config import download_folder, configs_assets_folder, area, config_folder


# CORINE Land Cover (status layers 1990, 2000, 2006, 2012, 2018) of the Copernicus Land Monitoring
# Service, taken from the map services of the European Environment Agency (EEA).
#
# The map services deliver pictures, in which every land cover class has the colour of the official
# CORINE legend. The pictures are requested on a fixed grid without any smoothing, so every pixel has
# exactly the colour of one class. The colours are converted back to the class codes (111 ... 523)
# with the legend in corine_legend.json. A colour that is not part of the legend is an error, the
# result is never guessed.
#
# The result is one GeoTIFF per year with one band of class codes (level 3 of the CORINE
# nomenclature) in geographic coordinates (EPSG:4326), 0 = no data (outside of the CORINE coverage).

LEGEND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corine_legend.json')
NODATA = 0
# colour of the entry 'no data' (code 999) of the official legend, no land cover class has this colour
NODATA_COLOUR = (255, 255, 255)
# the map services deliver at most 4096 x 4096 pixels per request
TILE_SIZE = 4000


def load_legend():
    with open(LEGEND_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)['classes']


def pack_rgb(red, green, blue):
    # one number per colour
    return (np.asarray(red, dtype=np.uint32) << 16) | (np.asarray(green, dtype=np.uint32) << 8) | np.asarray(blue, dtype=np.uint32)


def decode_colours(rgba, legend):
    """
    Convert a picture (array rows x columns x 4: red, green, blue, alpha) to CORINE class codes.

    Transparent pixels (no data at the map service) and pixels in the 'no data' colour of the legend
    become NODATA.
    Raises an error if a pixel has a colour that is not part of the legend.
    """
    codes_by_colour = {int(pack_rgb(*c['rgb'])): c['code'] for c in legend}
    codes_by_colour[int(pack_rgb(*NODATA_COLOUR))] = NODATA
    colours = pack_rgb(rgba[..., 0], rgba[..., 1], rgba[..., 2])
    alpha = rgba[..., 3]

    result = np.full(colours.shape, NODATA, dtype=np.uint16)
    opaque = alpha == 255
    unknown = {}
    half_transparent = int(((alpha != 0) & ~opaque).sum())
    for colour in np.unique(colours[opaque]):
        mask = opaque & (colours == colour)
        if int(colour) in codes_by_colour:
            result[mask] = codes_by_colour[int(colour)]
        else:
            unknown[(int(colour) >> 16, (int(colour) >> 8) & 255, int(colour) & 255)] = int(mask.sum())
    if unknown or half_transparent:
        raise RuntimeError(
            f"The map service delivered colours that are not part of the CORINE legend: {unknown} "
            f"(colour: number of pixels), {half_transparent} half transparent pixels. "
            "The picture cannot be converted to class codes.")
    return result


def output_grid(bbox, resolution):
    """
    Pixel grid of the result for the bbox [lat_max, lon_min, lat_min, lon_max].
    The grid lines are multiples of the resolution, so results of different areas fit together.
    Returns (west, north, columns, rows).
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    west = math.floor(round(lon_min / resolution, 6)) * resolution
    north = math.ceil(round(lat_max / resolution, 6)) * resolution
    columns = math.ceil(round((lon_max - west) / resolution, 6))
    rows = math.ceil(round((north - lat_min) / resolution, 6))
    return west, north, columns, rows


def request_picture(url, layer, west, south, east, north, columns, rows, max_retries=4):
    # one picture of the raster layer of an ArcGIS map service as array (rows x columns x 4)
    parameters = {
        'bbox': f'{west:.6f},{south:.6f},{east:.6f},{north:.6f}',
        'bboxSR': 4326,
        'imageSR': 4326,
        'size': f'{columns},{rows}',
        'format': 'png32',
        'layers': f'show:{layer}',
        'transparent': 'true',
        'dpi': 96,
        'f': 'image',
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url.rstrip('/') + '/export', params=parameters, timeout=300)
            response.raise_for_status()
            # the service reports errors as a json document with status code 200
            if not response.headers.get('Content-Type', '').startswith('image/png'):
                raise requests.RequestException(f"no picture delivered: {response.text[:300]}")
            picture = np.array(Image.open(io.BytesIO(response.content)).convert('RGBA'))
            if picture.shape != (rows, columns, 4):
                raise requests.RequestException(f"picture has the shape {picture.shape}, expected {(rows, columns, 4)}")
            return picture
        except (requests.RequestException, OSError) as e:
            print(f"{url}: {e} (attempt {attempt}/{max_retries})")
            if attempt == max_retries:
                raise RuntimeError(f"Failed to get data from {url}") from e
            sleep(20)


def write_legend_csv(folder, legend):
    # the class codes need their names, put the legend next to the data
    path = os.path.join(folder, 'corine_legend.csv')
    part = path + f'.{os.getpid()}.part'
    with open(part, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['code', 'level1', 'level2', 'level3', 'red', 'green', 'blue'])
        for c in legend:
            writer.writerow([c['code'], c['level1'], c['level2'], c['level3']] + c['rgb'])
        writer.writerow([NODATA, 'No data', 'No data', 'No data', '', '', ''])
    os.replace(part, path)


def get_corine(parameters_jsonfile, vOI):
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
    legend = load_legend()
    west, north, columns, rows = output_grid(bbox, resolution)
    print(f"{vOI}: {columns} x {rows} pixels of {resolution} degree")

    folder = os.path.join(download_folder, parameters['type'])
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, variable['name'] + '.tif')
    part = file_path + '.part'

    profile = {
        'driver': 'GTiff', 'dtype': 'uint16', 'count': 1, 'width': columns, 'height': rows,
        'crs': 'EPSG:4326', 'transform': from_origin(west, north, resolution, resolution),
        'nodata': NODATA, 'compress': 'deflate', 'tiled': True, 'blockxsize': 256, 'blockysize': 256,
        'BIGTIFF': 'IF_SAFER',
    }
    n_data = 0
    try:
        with rasterio.open(part, 'w', **profile) as dst:
            dst.update_tags(
                content='CORINE Land Cover class codes (level 3), 0 = no data',
                legend='corine_legend.csv',
                year=str(variable.get('year', '')),
                source=variable['url'],
            )
            for row in range(0, rows, TILE_SIZE):
                for col in range(0, columns, TILE_SIZE):
                    n_rows, n_cols = min(TILE_SIZE, rows - row), min(TILE_SIZE, columns - col)
                    picture = request_picture(
                        variable['url'], variable['layer'],
                        west + col * resolution, north - (row + n_rows) * resolution,
                        west + (col + n_cols) * resolution, north - row * resolution,
                        n_cols, n_rows)
                    codes = decode_colours(picture, legend)
                    n_data += int((codes != NODATA).sum())
                    dst.write(codes, 1, window=Window(col, row, n_cols, n_rows))
        if n_data == 0:
            raise RuntimeError(
                f"No CORINE data in the area '{area}' {bbox}. CORINE Land Cover covers Europe only. "
                f"For areas outside of Europe remove the variables from '{parameters_jsonfile}'.")
        os.replace(part, file_path)
    finally:
        if os.path.exists(part):
            os.remove(part)

    write_legend_csv(folder, legend)
    print(f"{n_data} of {columns * rows} pixels with data, saved as {file_path}")
