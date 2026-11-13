import glob
import json
import os
import re
from datetime import datetime

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge
from scipy.signal import oaconvolve

try:
    from .config import download_folder
except ImportError:
    from config import download_folder


# Neighbourhood filters for the tiles of the Copernicus DEM.
#
# The tiles are 1 degree x 1 degree GeoTIFFs in geographic coordinates (EPSG:4326). A pixel is
# therefore not a square in metres, and its width in degrees changes with the latitude zone of the
# tile (e.g. 90 m product: 3 arcsec up to 50 N, 4.5 arcsec from 50 N to 60 N, 6 arcsec from 60 N).
# All distances used by the filters are computed in metres from the latitude of the pixels.
#
# Every tile is processed together with a margin taken from its (up to 8) neighbouring tiles, so
# that the results are seamless across tile borders. Where no neighbouring tile exists (border of
# the downloaded area, sea), the filters use the available pixels only.

# WGS84 ellipsoid
WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3


def pixel_size_m(latitude, xres_deg, yres_deg):
    """
    Size of a pixel in metres at the given latitude(s).
    Returns (width east-west, height north-south).
    """
    phi = np.radians(latitude)
    w = 1.0 - WGS84_E2 * np.sin(phi) ** 2
    radius_meridian = WGS84_A * (1.0 - WGS84_E2) / w ** 1.5
    radius_parallel = WGS84_A / np.sqrt(w) * np.cos(phi)
    return np.radians(xres_deg) * radius_parallel, np.radians(yres_deg) * radius_meridian


def list_tif_files(folder_path):
    return sorted(f for f in os.listdir(folder_path) if f.endswith('.tif'))


def extract_coordinates(filename):
    # lower left corner (lon, lat) of a tile from its name, e.g. ..._N53_00_E013_00_DEM.tif -> (13, 53)
    match = re.search(r'([NS])(\d+)_00_([EW])(\d+)_00', filename)
    if not match:
        return None
    lat = int(match.group(2)) * (1 if match.group(1) == 'N' else -1)
    lon = int(match.group(4)) * (1 if match.group(3) == 'E' else -1)
    return lon, lat


def extract_radius(s):
    match = re.search(r'_radius_(\d+)', s)
    if match:
        return int(match.group(1))
    return None


def index_tiles(file_list, in_path):
    # {(lon, lat): path} for all tiles of the folder
    tiles = {}
    for file in file_list:
        coords = extract_coordinates(file)
        if coords is None:
            raise ValueError(f"Cannot read the tile position from the file name '{file}'")
        tiles[coords] = os.path.join(in_path, file)
    return tiles


def read_with_margin(tiles, coords, margin_x, margin_y):
    """
    Read the tile at `coords` (lon, lat) with a margin of margin_x / margin_y pixels on every side.

    The margin is filled from the neighbouring tiles. Neighbours in another latitude zone have a
    different pixel width, they are resampled (bilinear) to the pixel grid of the tile. Pixels of
    the margin without data are NaN. The pixels of the tile itself are returned unchanged.

    Returns (array of shape (rows + 2*margin_y, columns + 2*margin_x), dataset profile of the tile).
    """
    lon, lat = coords
    paths = [tiles[coords]]  # the tile itself first, its pixels have priority
    for dlat in (1, 0, -1):
        for dlon in (-1, 0, 1):
            neighbour = (lon + dlon, lat + dlat)
            if neighbour != coords and neighbour in tiles:
                paths.append(tiles[neighbour])

    sources = [rasterio.open(p) for p in paths]
    try:
        src = sources[0]
        profile = src.profile.copy()
        xres, yres = src.res
        bounds = (
            src.bounds.left - margin_x * xres,
            src.bounds.bottom - margin_y * yres,
            src.bounds.right + margin_x * xres,
            src.bounds.top + margin_y * yres,
        )
        data, _ = merge(sources, bounds=bounds, res=(xres, yres), nodata=np.nan, dtype='float32',
                        indexes=[1], resampling=Resampling.bilinear, method='first')
        data = data[0]
        expected = (src.height + 2 * margin_y, src.width + 2 * margin_x)
        if data.shape != expected:
            raise RuntimeError(f"Unexpected shape {data.shape} instead of {expected} for {paths[0]}")
        # make sure the tile itself is exactly the original data
        data[margin_y:margin_y + src.height, margin_x:margin_x + src.width] = src.read(1)
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    finally:
        for s in sources:
            s.close()
    return data, profile


def elliptical_kernel(radius_in_meter, dx, dy):
    """
    Kernel (1 inside, 0 outside) of all pixels whose centre is at most radius_in_meter away from the
    centre pixel. dx, dy: pixel width and height in metres. Because the pixels are not square in
    metres the circle is an ellipse in pixels.
    """
    rx = int(radius_in_meter // dx)
    ry = int(radius_in_meter // dy)
    jj, ii = np.meshgrid(np.arange(-rx, rx + 1), np.arange(-ry, ry + 1))
    return ((jj * dx) ** 2 + (ii * dy) ** 2 <= radius_in_meter ** 2).astype(float)


def neighbourhood_mean_std(data, kernel):
    """
    Mean and standard deviation of all valid (non NaN) pixels under the kernel, for every pixel.
    Returns (mean, std), NaN where no valid pixel lies under the kernel.
    """
    valid = np.isfinite(data)
    if not valid.any():
        nan = np.full(data.shape, np.nan)
        return nan, nan.copy()
    # remove the overall level first, this keeps the sums of squares small and the result precise
    offset = float(data[valid].mean())
    x = np.where(valid, data.astype(float) - offset, 0.0)

    count = np.rint(oaconvolve(valid.astype(float), kernel, mode='same'))
    sum_x = oaconvolve(x, kernel, mode='same')
    sum_xx = oaconvolve(x * x, kernel, mode='same')

    with np.errstate(invalid='ignore', divide='ignore'):
        mean = sum_x / count
        variance = sum_xx / count - mean ** 2
    std = np.sqrt(np.clip(variance, 0.0, None))
    std[count == 1] = 0.0  # a single value has no spread, avoid rounding noise
    mean = mean + offset
    mean[count == 0] = np.nan
    std[count == 0] = np.nan
    return mean, std


def slope_aspect(data, dx, dy):
    """
    Slope and aspect with the method of Zevenbergen and Thorne (1987): central differences of the
    four direct neighbours.

    data: elevation in metres including a margin of one pixel on every side (NaN where unknown)
    dx:   pixel width in metres, one value per row of the tile (array of shape (rows, 1)) or a scalar
    dy:   pixel height in metres

    Returns (slope, aspect) for the tile without the margin:
      slope   steepness in degrees, 0 (flat) to 90 (vertical)
      aspect  direction the slope faces (downhill direction) in degrees clockwise from north,
              0 = north, 90 = east, 180 = south, 270 = west, NaN for flat pixels
    At the border of the data a one-sided difference is used.
    """
    data = data.astype(float)
    centre = data[1:-1, 1:-1]
    north, south = data[:-2, 1:-1], data[2:, 1:-1]
    west, east = data[1:-1, :-2], data[1:-1, 2:]

    def difference(plus, minus, step):
        # derivative in the direction from `minus` to `plus`
        both = np.isfinite(plus) & np.isfinite(minus)
        only_plus = np.isfinite(plus) & ~np.isfinite(minus)
        only_minus = ~np.isfinite(plus) & np.isfinite(minus)
        result = np.full(centre.shape, np.nan)
        with np.errstate(invalid='ignore'):
            result = np.where(both, (plus - minus) / (2.0 * step), result)
            result = np.where(only_plus, (plus - centre) / step, result)
            result = np.where(only_minus, (centre - minus) / step, result)
        return result

    dz_east = difference(east, west, dx)      # rise towards east per metre
    dz_north = difference(north, south, dy)   # rise towards north per metre

    slope = np.degrees(np.arctan(np.hypot(dz_east, dz_north)))
    aspect = np.degrees(np.arctan2(-dz_east, -dz_north)) % 360.0
    aspect[(dz_east == 0) & (dz_north == 0)] = np.nan
    return slope, aspect


def write_result(path, array, profile, tags):
    profile = profile.copy()
    profile.update(dtype=rasterio.float32, count=1, compress='lzw', nodata=np.nan)
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(array.astype(rasterio.float32), 1)
        dst.update_tags(**tags)


def tile_geometry(profile):
    # latitude of the centre of every row and of the tile centre, pixel size in degrees
    transform = profile['transform']
    xres, yres = transform.a, abs(transform.e)
    row_latitudes = transform.f - (np.arange(profile['height']) + 0.5) * yres
    return row_latitudes, float(row_latitudes.mean()), xres, yres


def zevenbergen_thorne_folder(file_list, in_path, out_path):
    tiles = index_tiles(file_list, in_path)
    for coords in sorted(tiles):
        tiff = os.path.basename(tiles[coords])
        data, profile = read_with_margin(tiles, coords, 1, 1)
        row_latitudes, _, xres, yres = tile_geometry(profile)
        dx, dy = pixel_size_m(row_latitudes, xres, yres)
        slope, aspect = slope_aspect(data, dx.reshape(-1, 1), float(np.mean(dy)))
        write_result(os.path.join(out_path, f"slope_{tiff}"), slope, profile,
                     {'units': 'degrees', 'method': 'Zevenbergen and Thorne (1987)'})
        write_result(os.path.join(out_path, f"aspect_{tiff}"), aspect, profile,
                     {'units': 'degrees clockwise from north, direction the slope faces',
                      'method': 'Zevenbergen and Thorne (1987)'})
        print(f"slope and aspect written for {tiff}")


def apply_filter_with_adjacent_images(file_list, in_path, out_path, mode, radius_in_meter):
    # mean or standard deviation of the elevation within radius_in_meter around every pixel
    if mode not in ('mean', 'std'):
        raise ValueError(f"filter mode '{mode}' not available")
    tiles = index_tiles(file_list, in_path)
    for coords in sorted(tiles):
        tiff = os.path.basename(tiles[coords])
        with rasterio.open(tiles[coords]) as src:
            profile = src.profile.copy()
        _, centre_latitude, xres, yres = tile_geometry(profile)
        dx, dy = pixel_size_m(centre_latitude, xres, yres)
        kernel = elliptical_kernel(radius_in_meter, float(dx), float(dy))
        margin_y, margin_x = kernel.shape[0] // 2, kernel.shape[1] // 2

        data, profile = read_with_margin(tiles, coords, margin_x, margin_y)
        mean, std = neighbourhood_mean_std(data, kernel)
        result = mean if mode == 'mean' else std
        result = result[margin_y:result.shape[0] - margin_y, margin_x:result.shape[1] - margin_x]

        output_tif = os.path.join(out_path, f"{mode}_{tiff}_{radius_in_meter}.tif")
        write_result(output_tif, result, profile,
                     {'units': 'metres', 'filter': mode, 'radius_in_meter': str(radius_in_meter)})
        print(f"{mode} within {radius_in_meter} m written for {tiff}")


def compute_neighborhood(json_file, variableOI, mode):
    with open(json_file, 'r') as file:
        parameters = json.load(file)

    variable = next((v for v in parameters['variables'] if v['name'] == variableOI), None)
    if variable is None:
        raise ValueError(f"Variable '{variableOI}' is not listed in '{json_file}'")

    in_path = os.path.join(download_folder, parameters['type'], variable['name'])
    out_path = os.path.join(download_folder, 'neigborhoods', parameters['type'], variable['name'], mode)
    os.makedirs(out_path, exist_ok=True)
    # results of an earlier run (maybe for another area) must not remain in the folder
    for old_file in glob.glob(os.path.join(out_path, '*.tif')):
        os.remove(old_file)

    tif_files = list_tif_files(in_path)
    if not tif_files:
        raise RuntimeError(f"No .tif files found in {in_path}")
    print(f"{len(tif_files)} files to process")

    if mode == 'zevenbergen_thorne':
        zevenbergen_thorne_folder(tif_files, in_path, out_path)
    elif mode.startswith(('mean_radius_', 'std_radius_')):
        radius_in_meter = extract_radius(mode)
        apply_filter_with_adjacent_images(tif_files, in_path, out_path, mode.split('_')[0], radius_in_meter)
    else:
        raise ValueError(f"filter mode '{mode}' not available")

    # flag file that tells snakemake the computation is done
    with open(os.path.join(out_path, "done.txt"), "w") as file:
        file.write("Neighbourhood was computed: ")
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
