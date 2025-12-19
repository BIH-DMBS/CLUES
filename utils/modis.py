import utils
import os
import earthaccess
import glob
import numpy as np
import pandas as pd
import xarray as xr
from netCDF4 import Dataset
from pyproj import CRS, Transformer
from collections import defaultdict
import shutil

try:
    from .config import download_folder, tmp_folder, secrets_folder
except:
    from config import download_folder, tmp_folder, secrets_folder

def get_modis_vi(json_file, name, vars_name, year):
    parameter = utils.get_parameter(json_file,'bbox.json')
    bbox = parameter['bbox']
    lat_max, lon_min, lat_min, lon_max = bbox
    typ = parameter['type']
    for v in parameter['variables']:
        if v['name'] == name:
            url = v['url']
            parameter = v
            break
    
    # Create temp directory if it doesn't exist
    tmp_fold = os.path.join(tmp_folder, name, year)    
    os.makedirs(tmp_fold, exist_ok=True)

    # download MODIS data using Earthdata Login
    earthaccess.login(strategy="netrc")
    # MODIS/Terra Vegetation Indices Monthly L3 Global 1km SIN Grid V061
    granules = earthaccess.search_data(
        short_name="MOD13A3",
        temporal=(f"{year}-01-01", f"{year}-12-31"),
        bounding_box=(lon_min, lat_min, lon_max, lat_max)
    )

    earthaccess.download(granules, local_path=tmp_fold)
    
    # -------------------------
    # 1. Find all HDF tiles
    # -------------------------
    hdf_files = glob.glob(os.path.join(tmp_fold, "*.hdf"))

    # -------------------------
    # 2. Group tiles by DOY
    # -------------------------
    tiles_by_doy = defaultdict(list)
    for f in hdf_files:
        doy = f.split(".")[1]  # e.g., 'A2021001'
        tiles_by_doy[doy].append(f)

    # -------------------------
    # 3. MODIS constants
    # -------------------------
    tile_pixels = parameter['tile_pixels']  # e.g., 1200 for 1km
    pixel_size = parameter['pixel_size_in_m']  # MODIS Sinusoidal pixel size in meters

    print(hdf_files)
    print('-----------')

    # -------------------------
    # 4. Determine merged grid size
    # -------------------------
    h_all = [int(f.split(".")[2][1:3]) for f in hdf_files]
    v_all = [int(f.split(".")[2][4:6]) for f in hdf_files]
    h_min, h_max = min(h_all), max(h_all)
    v_min, v_max = min(v_all), max(v_all)

    ncols = (h_max - h_min + 1) * tile_pixels
    nrows = (v_max - v_min + 1) * tile_pixels

    # -------------------------
    # 5. Initialize merged lat/lon arrays
    # -------------------------
    X = np.full((nrows, ncols), np.nan, dtype=np.float64)
    Y = np.full((nrows, ncols), np.nan, dtype=np.float64)

    # -------------------------
    # 6. Prepare transformer (MODIS Sinusoidal → WGS84)
    # -------------------------
    modis_sinu = CRS.from_proj4("+proj=sinu +R=6371007.181 +nadgrids=@null +wktext")
    wgs84 = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(modis_sinu, wgs84, always_xy=True)

    # -------------------------
    # 7. Precompute merged lat/lon grid
    # -------------------------
    for tile_file in hdf_files:
        base = tile_file.split(".")[2]  # e.g., 'h17v03'
        h = int(base[1:3])
        v = int(base[4:6])

        # Tile upper-left corner in Sinusoidal meters
        ulx = (h - 18) * tile_pixels * pixel_size
        uly = (9 - v) * tile_pixels * pixel_size

        # Pixel coordinates in Sinusoidal
        x = ulx + (np.arange(tile_pixels) + 0.5) * pixel_size
        y = uly - (np.arange(tile_pixels) + 0.5) * pixel_size
        xs, ys = np.meshgrid(x, y)

        # Convert to WGS84
        lons, lats = transformer.transform(xs, ys)

        # Row/column start indices (north at top)
        row_start = (v - v_min) * tile_pixels
        col_start = (h - h_min) * tile_pixels

        X[row_start:row_start+tile_pixels, col_start:col_start+tile_pixels] = lons
        Y[row_start:row_start+tile_pixels, col_start:col_start+tile_pixels] = lats

    # -------------------------
    # 8. Merge NDVI tiles per DOY
    # -------------------------
    i = 0
    for asset in parameter['vars']:
        merged_arrays = []
        time_list = []

        for doy, tiles in sorted(tiles_by_doy.items()):
            merged_ndvi = np.full((nrows, ncols), np.nan, dtype=np.float32)

            for tile in tiles:
                ds = Dataset(tile, 'r')
                ndvi = ds.variables[asset][:].astype(np.float32) / 10000.0
                ndvi[ndvi < -1] = np.nan  # mask invalid values

                base = tile.split(".")[2]
                h = int(base[1:3])
                v = int(base[4:6])

                # Use same row/col indices as lat/lon to preserve correct alignment
                row_start = (v - v_min) * tile_pixels
                col_start = (h - h_min) * tile_pixels
                merged_ndvi[row_start:row_start+tile_pixels, col_start:col_start+tile_pixels] = ndvi
                ds.close()

            merged_arrays.append(merged_ndvi)

            # Convert DOY to datetime
            year = int(doy[1:5])
            day_of_year = int(doy[5:])
            dt = pd.Timestamp(year=year, month=1, day=1) + pd.Timedelta(days=day_of_year-1)
            time_list.append(dt)

        # -------------------------
        # 9. Stack NDVI arrays
        # -------------------------
        ndvi_stack = np.stack(merged_arrays, axis=0)

        # -------------------------
        # 10. Create xarray Dataset
        # -------------------------
        xr_ds = xr.Dataset(
            {
                asset: (['time','YDim','XDim'], ndvi_stack),
                'Latitude': (['YDim','XDim'], Y),
                'Longitude': (['YDim','XDim'], X)
            },
            coords={'time': time_list}
        )

        xr_ds[asset].attrs['long_name'] = 'MODIS Terra NDVI'
        xr_ds[asset].attrs['units'] = '1'

        # -------------------------
        # 11. Save NetCDF
        # -------------------------
        data_dir = os.path.join(download_folder, typ, name, parameter['vars_name'][i])
        output_path = os.path.join(data_dir, str(year) + '.nc')
        print(output_path)
        os.makedirs(data_dir, exist_ok=True)
        xr_ds.to_netcdf(output_path, encoding={
            asset: {'dtype':'float32', 'zlib':True},
            'Latitude': {'dtype':'float32'},
            'Longitude': {'dtype':'float32'}
        })
        i += 1
        print(f"{asset} NetCDF successfully created with precise lat/lon (Sinusoidal projection)")
    # -------------------------
    # Cleanup temporary files   
    shutil.rmtree(tmp_fold)
    print(f"Folder '{tmp_fold}' and all files inside have been deleted.")
 