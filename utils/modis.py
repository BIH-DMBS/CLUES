import glob
import os
import shutil
from collections import defaultdict
from time import sleep

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr
from pyproj import CRS, Transformer

import utils

# The MODIS files are HDF4 files. pyhdf reads them on Linux. Where pyhdf is not usable (on Windows
# its library often cannot be loaded) the netCDF4 library is used, which can read HDF4 as well.
try:
    from pyhdf.SD import SD, SDC
    HDF_READER = 'pyhdf'
except (ImportError, OSError):
    from netCDF4 import Dataset
    HDF_READER = 'netCDF4'

try:
    from .config import download_folder, tmp_folder
except ImportError:
    from config import download_folder, tmp_folder


# MODIS vegetation indices (MOD13A3: monthly, 1 km) from NASA Earthdata.
#
# The data comes in tiles of the MODIS sinusoidal grid (tile h18v03 etc.). The tiles of the area are
# put together, cut to the area and stored per year as netCDF file with the dimensions
# (time, YDim, XDim). The grid is not a regular longitude/latitude grid, therefore the longitude and
# latitude of every pixel centre are stored as two-dimensional variables 'Longitude' and 'Latitude'.
#
# Values: the index (NDVI, EVI) as a number between -0.2 and 1, NaN where the product has no value.

# width of a tile of the MODIS sinusoidal grid in metres (36 tiles around the globe)
TILE_SIZE_M = 1111950.5196666666
MODIS_SINUSOIDAL = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext"


def read_sds(hdf_file, name):
    """
    Read one data set of a MODIS HDF4 file without any conversion.
    Returns (array of the stored integers, attributes of the data set as dictionary).
    """
    if HDF_READER == 'pyhdf':
        sd = SD(hdf_file, SDC.READ)
        try:
            sds = sd.select(name)
            return np.array(sds[:]), dict(sds.attributes())
        finally:
            sd.end()
    with Dataset(hdf_file, 'r') as ds:
        variable = ds.variables[name]
        # no automatic conversion: the library would multiply with 'scale_factor',
        # but in the MODIS products the stored numbers have to be divided by it
        variable.set_auto_maskandscale(False)
        return np.array(variable[:]), {key: variable.getncattr(key) for key in variable.ncattrs()}


def to_index(raw, attributes):
    """
    Convert the stored integers of a vegetation index to the index itself.
    MODIS convention: value = stored number / scale_factor. Pixels with the fill value or outside
    of the valid range become NaN.
    """
    values = raw.astype(np.float32) / np.float32(attributes.get('scale_factor', 10000.0))
    invalid = np.zeros(raw.shape, dtype=bool)
    if attributes.get('_FillValue') is not None:
        invalid |= raw == attributes['_FillValue']
    if attributes.get('valid_range') is not None:
        low, high = attributes['valid_range']
        invalid |= (raw < low) | (raw > high)
    values[invalid] = np.nan
    return values


def tile_of(hdf_file):
    # (h, v) of the tile from the file name, e.g. MOD13A3.A2020001.h18v03.061.2020328134341.hdf -> (18, 3)
    tile = os.path.basename(hdf_file).split(".")[2]
    return int(tile[1:3]), int(tile[4:6])


def date_of(hdf_file):
    # date from the file name, A2020032 is day 32 of 2020
    day = os.path.basename(hdf_file).split(".")[1]
    return pd.Timestamp(year=int(day[1:5]), month=1, day=1) + pd.Timedelta(days=int(day[5:]) - 1)


def grid_coordinates(h_min, h_max, v_min, v_max, tile_pixels):
    """
    Longitude and latitude of the pixel centres of the tiles h_min..h_max, v_min..v_max
    (two arrays of the shape (rows, columns), row 0 is north).
    """
    pixel_size = TILE_SIZE_M / tile_pixels
    ncols = (h_max - h_min + 1) * tile_pixels
    nrows = (v_max - v_min + 1) * tile_pixels
    # upper left corner of the tile (h_min, v_min); tile h18 starts at x = 0, tile v09 at y = 0
    ulx = (h_min - 18) * TILE_SIZE_M
    uly = (9 - v_min) * TILE_SIZE_M
    x = ulx + (np.arange(ncols) + 0.5) * pixel_size
    y = uly - (np.arange(nrows) + 0.5) * pixel_size
    xs, ys = np.meshgrid(x, y)
    transformer = Transformer.from_crs(CRS.from_proj4(MODIS_SINUSOIDAL), CRS.from_epsg(4326), always_xy=True)
    lons, lats = transformer.transform(xs, ys)
    return lons, lats


def rows_and_columns_of_bbox(lons, lats, bbox, margin_in_pixel=5):
    """
    Part of the grid that contains the bbox [lat_max, lon_min, lat_min, lon_max]:
    (row_start, row_stop, col_start, col_stop). Raises an error if no pixel lies in the bbox.
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    with np.errstate(invalid='ignore'):
        inside = (lats >= lat_min) & (lats <= lat_max) & (lons >= lon_min) & (lons <= lon_max)
    if not inside.any():
        raise RuntimeError(f"The downloaded MODIS tiles do not contain the area {bbox}")
    rows = np.where(inside.any(axis=1))[0]
    cols = np.where(inside.any(axis=0))[0]
    return (max(rows[0] - margin_in_pixel, 0), min(rows[-1] + 1 + margin_in_pixel, lats.shape[0]),
            max(cols[0] - margin_in_pixel, 0), min(cols[-1] + 1 + margin_in_pixel, lats.shape[1]))


def with_retries(action, label, attempts=4, pause=30):
    # the Earthdata login service sometimes does not answer in time, try again before giving up
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception as e:
            print(f"{label} failed: {e} (attempt {attempt}/{attempts})")
            if attempt == attempts:
                raise
            sleep(pause)


def get_modis_vi(json_file, name, vars_name, year):
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    parameter = utils.get_parameter(json_file, 'bbox.json')
    if parameter is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")
    bbox = parameter['bbox']
    lat_max, lon_min, lat_min, lon_max = bbox
    typ = parameter['type']
    variable = next((v for v in parameter['variables'] if v['name'] == name), None)
    if variable is None:
        raise ValueError(f"Variable '{name}' is not listed in '{json_file}'")
    if vars_name not in variable['vars_name']:
        raise ValueError(f"'{vars_name}' is not one of {variable['vars_name']} of '{name}' in '{json_file}'")
    tile_pixels = variable['tile_pixels']  # e.g. 1200 for 1km
    year = str(year)

    # Create temp directory, without files of an earlier, interrupted run
    tmp_fold = os.path.join(tmp_folder, name, year)
    shutil.rmtree(tmp_fold, ignore_errors=True)
    os.makedirs(tmp_fold)
    try:
        # download MODIS data using Earthdata Login
        with_retries(lambda: earthaccess.login(strategy="netrc"), 'Earthdata login')
        granules = with_retries(lambda: earthaccess.search_data(
            short_name=name,
            temporal=(f"{year}-01-01", f"{year}-12-31"),
            bounding_box=(lon_min, lat_min, lon_max, lat_max)
        ), 'Earthdata search')
        if len(granules) == 0:
            raise RuntimeError(f"No {name} data found for {year} and the area {bbox}")
        earthaccess.download(granules, local_path=tmp_fold)
        hdf_files = sorted(glob.glob(os.path.join(tmp_fold, "*.hdf")))
        if len(hdf_files) != len(granules):
            raise RuntimeError(f"{len(granules)} files found at Earthdata, but {len(hdf_files)} downloaded")

        # group the tiles by date
        tiles_by_date = defaultdict(list)
        for f in hdf_files:
            if date_of(f).year != int(year):
                raise RuntimeError(f"{os.path.basename(f)} is not a file of the year {year}")
            tiles_by_date[date_of(f)].append(f)
        dates = sorted(tiles_by_date)

        # grid of all tiles together and the part of it that covers the area
        tiles = [tile_of(f) for f in hdf_files]
        h_min, h_max = min(t[0] for t in tiles), max(t[0] for t in tiles)
        v_min, v_max = min(t[1] for t in tiles), max(t[1] for t in tiles)
        lons, lats = grid_coordinates(h_min, h_max, v_min, v_max, tile_pixels)
        row_start, row_stop, col_start, col_stop = rows_and_columns_of_bbox(lons, lats, bbox)
        lons = lons[row_start:row_stop, col_start:col_stop]
        lats = lats[row_start:row_stop, col_start:col_stop]
        print(f"{len(hdf_files)} files, {len(dates)} dates, tiles h{h_min}-{h_max} v{v_min}-{v_max}, "
              f"{lats.shape[1]} x {lats.shape[0]} pixels in the area")

        # one netCDF file per vegetation index
        for asset, asset_name in zip(variable['vars'], variable['vars_name']):
            stack = np.full((len(dates),) + lats.shape, np.nan, dtype=np.float32)
            for i, date in enumerate(dates):
                merged = np.full(((v_max - v_min + 1) * tile_pixels, (h_max - h_min + 1) * tile_pixels), np.nan, dtype=np.float32)
                for tile_file in tiles_by_date[date]:
                    h, v = tile_of(tile_file)
                    raw, attributes = read_sds(tile_file, asset)
                    row, col = (v - v_min) * tile_pixels, (h - h_min) * tile_pixels
                    merged[row:row + tile_pixels, col:col + tile_pixels] = to_index(raw, attributes)
                stack[i] = merged[row_start:row_stop, col_start:col_stop]

            xr_ds = xr.Dataset(
                {
                    asset: (['time', 'YDim', 'XDim'], stack),
                    'Latitude': (['YDim', 'XDim'], lats),
                    'Longitude': (['YDim', 'XDim'], lons)
                },
                coords={'time': dates}
            )
            xr_ds[asset].attrs['long_name'] = f"MODIS Terra {asset}"
            xr_ds[asset].attrs['units'] = '1'
            xr_ds[asset].attrs['valid_range'] = '-0.2 to 1, NaN = no value'
            xr_ds.attrs['source'] = f"{name} (MODIS sinusoidal grid), NASA Earthdata"
            xr_ds.attrs['grid'] = 'Latitude and Longitude are the centres of the pixels'

            data_dir = os.path.join(download_folder, typ, name, asset_name)
            os.makedirs(data_dir, exist_ok=True)
            output_path = os.path.join(data_dir, year + '.nc')
            # write under a temporary name, the final file only appears once it is complete
            part = output_path + '.part'
            try:
                xr_ds.to_netcdf(part, engine='netcdf4', encoding={
                    asset: {'dtype': 'float32', 'zlib': True},
                    'Latitude': {'dtype': 'float32'},
                    'Longitude': {'dtype': 'float32'}
                })
                xr_ds.close()
                os.replace(part, output_path)
            finally:
                if os.path.exists(part):
                    os.remove(part)
            print(f"{asset} saved as {output_path}")
    finally:
        # Cleanup temporary files
        shutil.rmtree(tmp_fold, ignore_errors=True)
