import gc
import json
import os
import shutil

import xarray as xr
from worldpoppy import wp_raster

import utils

# Import CLUES configuration
try:
    from .config import download_folder, tmp_folder
except ImportError:
    from config import download_folder, tmp_folder


def getWorldPop(json_file, year, vOI):
    """
    Download a WorldPop raster for one variable and one year, cut to the area of interest,
    and save it as GeoTIFF inside the CLUES download folder.

    WorldPop offers its data per country. The library worldpoppy downloads the rasters of all
    countries that touch the area, puts them together and cuts out the area.
    Errors are not caught here: a failed download must end the script with an error,
    so that snakemake marks the job as failed.
    """
    # -------------------------------------------------------
    # 1. Load bounding box for the region of interest (ROI)
    # -------------------------------------------------------
    parameters_bbox = utils.get_bbox('bbox.json')
    if parameters_bbox is None:
        raise RuntimeError("Could not read the bounding box of the area (see message above)")
    bbox = parameters_bbox['bbox']

    '''
    Bounding boxes can be represented in different conventions depending on the software or library. In our framework,
    we follow the (max_lat, min_lon, min_lat, max_lon) style commonly used in some geospatial datasets and GIS tools. In
    contrast, the WorldPop Python library (worldpoppy) expects bounding boxes in the more conventional order (min_lon, min_lat, max_lon, max_lat)
    '''
    bbox = [
        bbox[1],  # min_lon
        bbox[2],  # min_lat
        bbox[3],  # max_lon
        bbox[0]   # max_lat
    ]

    # -------------------------------------------------------
    # 2. Read the config file and find the variable to download
    # -------------------------------------------------------
    with open(json_file, 'r') as f:
        parameters = json.load(f)
    variable = next((v for v in parameters['variables'] if v['name'] == vOI), None)
    if variable is None:
        raise ValueError(f"Variable '{vOI}' is not listed in '{json_file}'")
    if not int(variable['start_year']) <= int(year) <= int(variable['end_year']):
        raise ValueError(f"'{vOI}' is available from {variable['start_year']} to {variable['end_year']}, not for {year}")
    product_name = variable['product_name']
    print(product_name)

    # -------------------------------------------------------
    # 3. Download the WorldPop raster for the ROI
    # -------------------------------------------------------
    # Note: 'masked=True' will set missing areas to NaN
    # worldpoppy keeps the rasters of the complete countries in a cache folder, by default in the
    # home folder of the user, where they pile up unnoticed. Here every job gets its own cache
    # folder in the temporary folder of CLUES, which is removed when the area is saved.
    # (Switching the cache off with cache_downloads=False fails on Windows.)
    cache_dir = os.path.join(tmp_folder, f"worldpop_{vOI}_{year}")
    shutil.rmtree(cache_dir, ignore_errors=True)
    os.makedirs(cache_dir)
    os.environ["WORLDPOPPY_CACHE_DIR"] = cache_dir

    output_path = os.path.join(download_folder, parameters['type'], vOI, f"{year}.tif")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # write under a temporary name, the final file only appears once it is complete
    part = output_path + '.part'
    try:
        source = wp_raster(
            product_name=product_name,
            aoi=bbox,  # pass bbox
            years=[int(year)],
            masked=True,
        )
        data = source.isel(year=0, drop=True) if 'year' in source.dims else source
        # read the area into memory and let go of the files of the countries
        data = data.load()
        source.close()
        if int(data.notnull().sum()) == 0:
            raise RuntimeError(f"No WorldPop data of '{product_name}' in the area {bbox} for {year}")

        # -------------------------------------------------------
        # 4. Save to GeoTIFF
        # -------------------------------------------------------
        data.rio.to_raster(part, driver='GTiff', compress='deflate', tiled=True)
        data.close()
        os.replace(part, output_path)
    finally:
        if os.path.exists(part):
            os.remove(part)
        # the files of the countries can only be removed once nothing holds them open any more
        xr.backends.file_manager.FILE_CACHE.clear()
        gc.collect()
        shutil.rmtree(cache_dir, ignore_errors=True)
        if os.path.exists(cache_dir):
            print(f"Note: the temporary folder {cache_dir} could not be removed completely")
    print(f"Raster saved to: {output_path}")
