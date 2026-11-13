"""
Availability check of the data sources used in CLUES.

For every source the script goes the same way as the workflow (same addresses, same request form,
same code where possible) with a small sample, and reports whether the source answers as expected.
It does not test the complete download of a source.

Run from the repository root (the folder that contains 'config'):

    python utils/clues_tests.py                  all sources
    python utils/clues_tests.py cams spei        only the named sources
    python utils/clues_tests.py --list           names of the sources

The checks read the default configuration files in 'configs_sources' and the credentials from the
secrets folder named in 'config/config.json'.

Notes
- The sources are checked one after the other. The Copernicus data stores (CAMS, ERA5) ask their
  users to send requests sequentially, not in parallel:
  https://forum.ecmwf.int/t/data-stores-service-protection-measures-affecting-data-downloads-and-account-access-cds-ads-ewds-ecds/15481
- ERA5-Land is checked without a download request, because any request for this data set waits
  about 20 minutes or more in the queue of the data store.
"""
import gc
import json
import os
import shutil
import sys
import tempfile

import cdsapi
import cloudscraper
import earthaccess
import rasterio
import requests
import xarray as xr
import yaml
from owslib.wms import WebMapService

import copernicusDEM
import corine
import global_tc
import modis
import treecover
import wsf
from config import secrets_folder
from utils import check_time_axis, extract_single_netcdf, pad_bbox, supports_range_requests
from utils import get_all_files as figshare_files

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(REPO, 'configs_sources')
# small test area around the crossing of the equator and the Greenwich meridian: [lat_max, lon_min, lat_min, lon_max]
TEST_BBOX = [5, -5, -5, 5]


def load_config(name):
    with open(os.path.join(CONFIGS, name), 'r', encoding='utf-8') as f:
        return json.load(f)


def data_store_client(secret_file):
    with open(os.path.join(secrets_folder, secret_file), 'r') as f:
        credentials = yaml.safe_load(f)
    return cdsapi.Client(url=credentials['url'], key=credentials['key'])


def check_data_store_catalogue(api_url, config):
    """
    Compare a configuration with the public description of the data set at a Copernicus data store
    (no account needed, no download request): all variables must be known to the data store and the
    data must reach the last year of the configuration. Returns True if everything fits.
    """
    dataset = config['source']
    process = requests.get(f"{api_url}/retrieve/v1/processes/{dataset}", timeout=60)
    process.raise_for_status()
    known = set(process.json()['inputs']['variable']['schema']['items']['enum'])
    unknown = [v['name'] for v in config['variables'] if v['name'] not in known]
    collection = requests.get(f"{api_url}/catalogue/v1/collections/{dataset}", timeout=60)
    collection.raise_for_status()
    last_date = collection.json()['extent']['temporal']['interval'][0][1][:10]
    fine = True
    if unknown:
        fine = False
        print(f"  !!!!!! variables of the configuration that the data store does not know: {unknown} !!!!!!")
    if int(last_date[:4]) < int(config['end_year']):
        fine = False
        print(f"  !!!!!! the configuration ends {config['end_year']}, the data store has data until {last_date} !!!!!!")
    print(f"  {len(config['variables'])} configured variables known to the data store, data available until {last_date}")
    return fine


def check_cams():
    # catalogue, then the same request form as utils.get_asset_atmosphere:
    # netCDF delivered as zip, area widened by one grid step, here for a single day only
    config = load_config('cams-global-reanalysis-eac4.json')
    fine = check_data_store_catalogue('https://ads.atmosphere.copernicus.eu/api', config)
    times = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
    with tempfile.TemporaryDirectory() as tmp:
        zip_file, nc_file = os.path.join(tmp, 'test_cams.zip'), os.path.join(tmp, 'test_cams.nc')
        data_store_client('cdsapirc_atmo.sct').retrieve(
            config['source'],
            {
                "data_format": "netcdf_zip",
                "variable": [config['variables'][0]['name']],
                "date": ["2013-08-01/2013-08-01"],
                "time": times,
                "area": pad_bbox(TEST_BBOX, float(config['grid_resolution_deg'])),
            },
            zip_file)
        extract_single_netcdf(zip_file, nc_file)
        n_found, _ = check_time_axis(nc_file, '2013', config['delta_t_in_h'])
    if n_found != len(times):
        print(f"  !!!!!! downloaded, but {n_found} of {len(times)} time steps found !!!!!!")
        return False
    print(f"  one day of '{config['variables'][0]['name']}' downloaded, {n_found} time steps")
    return fine


def check_era5_single():
    # catalogue, then the same request form as utils.get_asset_climate:
    # netCDF, area widened by one grid step, here for a single day only
    config = load_config('reanalysis-era5-single-levels.json')
    fine = check_data_store_catalogue('https://cds.climate.copernicus.eu/api', config)
    hours = [f"{hour:02d}:00" for hour in range(24)]
    with tempfile.TemporaryDirectory() as tmp:
        nc_file = os.path.join(tmp, 'test_era5.nc')
        data_store_client('cdsapirc_climate.sct').retrieve(
            config['source'],
            {
                "product_type": [config.get('product_type', 'reanalysis')],
                "variable": [config['variables'][0]['name']],
                "year": ["1992"],
                "month": ["04"],
                "day": ["03"],
                "time": hours,
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": pad_bbox(TEST_BBOX, float(config['grid_resolution_deg'])),
            },
            nc_file)
        n_found, _ = check_time_axis(nc_file, '1992', config['delta_t_in_h'])
    if n_found != len(hours):
        print(f"  !!!!!! downloaded, but {n_found} of {len(hours)} time steps found !!!!!!")
        return False
    print(f"  one day of '{config['variables'][0]['name']}' downloaded, {n_found} time steps")
    return fine


def check_era5_land():
    # catalogue only, and that the credentials file is there; no download request (see the notes at the top)
    config = load_config('reanalysis-era5-land.json')
    fine = check_data_store_catalogue('https://cds.climate.copernicus.eu/api', config)
    data_store_client('cdsapirc_climate.sct')
    print("  no download request sent: a request for ERA5-Land waits about 20 minutes or more at the data store")
    return fine


def check_espon():
    # The ESPON database only answers clients that look like a web browser. The workflow uses the
    # library cloudscraper for this (utils/espon.py), and so does this check. It asks the interface of
    # the database for one indicator and then for the first bytes of the first configured package.
    config = load_config('espon.json')
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    response = scraper.get('https://database.espon.eu/api/select/indicators/', params={'format': 'json', 'limit': 1, 'offset': 0}, timeout=60)
    if response.status_code != 200:
        print(f"  !!!!!! the interface of the database is not reachable, status code {response.status_code} !!!!!!")
        return False
    print(f"  the interface of the database answers, {response.json().get('count')} indicators listed "
          f"(the configuration has {sum(len(v['features']) for v in config['variables'])})")
    feature = config['variables'][0]['features'][0]
    package = scraper.get(feature['shape'], stream=True, timeout=60)
    if package.status_code != 200:
        print(f"  !!!!!! the package of the indicator '{feature['name']}' is not available, status code {package.status_code} !!!!!!")
        return False
    first = next(package.iter_content(chunk_size=4))
    package.close()
    if first[:2] != b'PK':
        print(f"  !!!!!! the package of the indicator '{feature['name']}' is not a zip file !!!!!!")
        return False
    print(f"  the package of the indicator '{feature['name']}' is delivered as zip file")
    return True


def check_eoc_atmosphere():
    # The download of this source is under revision. Checked here: the service answers and the
    # layers of the configuration still exist, with data up to the end date of the configuration.
    config = load_config('EOC_Atmosphere_Coverage_Service.json')
    wms = WebMapService(config['link'], version='1.3.0')
    missing = [v['name'] for v in config['variables'] if v['name'] not in wms.contents]
    newer = []
    for variable in config['variables']:
        if variable['name'] in wms.contents and 'time' in wms[variable['name']].dimensions:
            at_service = wms[variable['name']].dimensions['time']['values'][0]
            if at_service.split('/')[1][:10] > variable['temporal_dimension'].split('/')[1][:10]:
                newer.append(variable['name'])
    print(f"  the service answers with {len(wms.contents)} layers; {len(config['variables']) - len(missing)} of "
          f"{len(config['variables'])} configured layers exist")
    if newer:
        print(f"  note: {len(newer)} layers have newer data at the service than the configuration says")
    if missing:
        print(f"  !!!!!! configured layers that do not exist any more: {missing} !!!!!!")
        return False
    return True


def check_wsf3d():
    # every configured file must be there, and the server must deliver parts of a file,
    # because the workflow reads only the configured area (utils.get_simple_download_tif)
    fine = True
    for variable in load_config('EOC_WSF3D.json')['variables']:
        response = requests.head(variable['url'], allow_redirects=True, timeout=30)
        size = int(response.headers.get('Content-Length', 0)) / (1024 ** 3)
        if response.status_code != 200:
            fine = False
            print(f"  {variable['name']}: !!!!!! not available (status code: {response.status_code}) !!!!!!")
        elif not supports_range_requests(variable['url']):
            print(f"  {variable['name']}: available ({size:.1f} GB), but the server does not deliver parts of a file: "
                  "the complete file will be downloaded")
        else:
            print(f"  {variable['name']}: available ({size:.1f} GB, partial reads possible)")
    return fine


def check_wsf():
    # same addresses as the workflow (utils/wsf.py): the tile that covers Berlin (12-14°E, 52-54°N) must be
    # there for every configured product, and a tile in the open sea must be reported as missing
    fine = True
    for variable in load_config('EOC_WSF.json')['variables']:
        url, file_name = wsf.tile_url(variable, 12, 52)
        response = requests.head(url, allow_redirects=True, timeout=30)
        sea_url, _ = wsf.tile_url(variable, -30, 0)
        sea = requests.head(sea_url, allow_redirects=True, timeout=30)
        if response.status_code == 200 and sea.status_code == 404:
            print(f"  {variable['name']}: available ({file_name}, {int(response.headers.get('Content-Length', 0)) / (1024 ** 2):.1f} MB)")
        else:
            fine = False
            print(f"  {variable['name']}: !!!!!! test tile status {response.status_code}, sea tile status {sea.status_code} "
                  "(expected 200 and 404) !!!!!!")
    return fine


def check_treecover_copernicus():
    # same code as the workflow (utils/treecover.py): a small area south-east of Berlin (forest)
    # from the service of every configured variable
    fine = True
    for variable in load_config('treecover_copernicus.json')['variables']:
        try:
            values = treecover.read_tile(variable, 13.60, 52.42, 0, 0, 40, 40, 0.001)
            found = sorted(set(values.ravel().tolist()) - {treecover.NODATA})
            if len(found) >= 2:
                print(f"  {variable['name']}: available, values {found[0]} to {found[-1]} in the test area")
            else:
                fine = False
                print(f"  {variable['name']}: !!!!!! unexpected content, values found: {found} !!!!!!")
        except Exception as e:
            fine = False
            print(f"  {variable['name']}: !!!!!! not available: {e} !!!!!!")
    return fine


def check_corine():
    # same code as the workflow (utils/corine.py): a small picture around Berlin from the map
    # service of every configured year, converted from the legend colours to class codes
    legend = corine.load_legend()
    fine = True
    for variable in load_config('corine_copernicus.json')['variables']:
        try:
            picture = corine.request_picture(variable['url'], variable['layer'], 13.3, 52.4, 13.5, 52.6, 200, 200, max_retries=2)
            classes = sorted(set(corine.decode_colours(picture, legend).ravel().tolist()) - {corine.NODATA})
            if len(classes) >= 5 and 112 in classes:
                print(f"  {variable['name']}: available, {len(classes)} land cover classes in the test area")
            else:
                fine = False
                print(f"  {variable['name']}: !!!!!! unexpected content, classes found: {classes} !!!!!!")
        except Exception as e:
            fine = False
            print(f"  {variable['name']}: !!!!!! not available: {e} !!!!!!")
    return fine


def check_spei():
    # the file of every configured time scale must be there
    config = load_config('spei.json')
    fine = True
    for time_scale in config['time_scales']:
        urls = [u for u in config['variables'][0]['urls'] if u.endswith(f"/spei{time_scale:02}.nc")]
        response = requests.head(urls[0], allow_redirects=True, timeout=30) if len(urls) == 1 else None
        if response is not None and response.status_code == 200:
            print(f"  spei{time_scale:02}: available ({int(response.headers.get('Content-Length', 0)) / (1024 ** 2):.0f} MB)")
        else:
            fine = False
            print(f"  spei{time_scale:02}: !!!!!! not available ({len(urls)} address(es) in the configuration, "
                  f"status code {response.status_code if response is not None else '-'}) !!!!!!")
    return fine


def check_copernicus_dem():
    # same code as the workflow (utils/copernicusDEM.py): 1 degree tiles from the public
    # AWS Open Data registry, no account needed. Test tile N50 E010 (covers 50-51°N, 10-11°E).
    fine = True
    with tempfile.TemporaryDirectory() as tmp:
        for variable in load_config('copernicus_dem.json')['variables']:
            resolution = variable['resolution'][-2:]
            url, _ = copernicusDEM.tile_url(50, 10, resolution, variable['url'])
            if resolution == '90':
                # the 90 m tile is small (a few MB): download it and read it
                tile = os.path.join(tmp, 'test_dem.tif')
                status = copernicusDEM.download_tile(url, tile, max_retries=2)
                if status != 'downloaded':
                    fine = False
                    print(f"  {resolution} m: !!!!!! test tile not available ({status}) !!!!!!")
                    continue
                with rasterio.open(tile) as src:
                    content_fine = src.crs.to_epsg() == 4326 and src.height == 1200 and float(src.read(1).max()) > 0
                # tiles without land do not exist, the workflow relies on the answer 404 for them
                sea_url, _ = copernicusDEM.tile_url(0, -30, resolution, variable['url'])
                sea_fine = copernicusDEM.download_tile(sea_url, os.path.join(tmp, 'test_dem_sea.tif'), max_retries=2) == 'missing'
                if content_fine and sea_fine:
                    print(f"  {resolution} m: test tile downloaded and read, a tile without land is reported as missing")
                else:
                    fine = False
                    print(f"  {resolution} m: !!!!!! content of the test tile as expected: {content_fine}, "
                          f"tile without land reported as missing: {sea_fine} !!!!!!")
            else:
                # the 30 m tile is larger (about 30 MB): only check that it is there
                response = requests.head(url, timeout=30)
                if response.status_code == 200:
                    print(f"  {resolution} m: test tile available")
                else:
                    fine = False
                    print(f"  {resolution} m: !!!!!! test tile not available (status code: {response.status_code}) !!!!!!")
    return fine


def start_of_download(url):
    # first megabyte of a file, to see that the download really starts
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    first = next(response.iter_content(chunk_size=1024 * 1024))
    response.close()
    return len(first)


def check_ntl():
    # the configured version of the Figshare record must hold the flag file and one file per year,
    # and the download must start (same listing as the workflow, utils.get_all_files)
    config = load_config('ntl.json')
    variable = config['variables'][0]
    record = {f['name']: f for f in figshare_files(variable['article_id'], variable.get('version'))}
    years = sorted({name.split('_')[3] for name in record if name.startswith('Harmonized_DN_NTL_')})
    if variable['flagFile'] not in record:
        print(f"  !!!!!! the flag file {variable['flagFile']} is not part of the Figshare record !!!!!!")
        return False
    n = start_of_download(record[variable['flagFile']]['download_url'])
    print(f"  {len(record)} files, years {years[0]} to {years[-1]}, download starts (first {n} bytes read)")
    if years[-1] != config['end_year']:
        print(f"  !!!!!! the record ends {years[-1]}, the configuration says {config['end_year']} !!!!!!")
        return False
    return True


def check_glwd():
    # the files named in the default configuration must be part of the Figshare record
    # and the download must start (same listing as the workflow, utils.get_all_files)
    variable = load_config('hydrosheds_GLWD.json')['variables'][0]
    record = {f['name']: f for f in figshare_files(variable['article_id'], variable.get('version'))}
    missing = [name for name in variable['files_oi'] if name not in record]
    if missing:
        print(f"  !!!!!! not part of the Figshare record: {missing} !!!!!!")
        return False
    for name in variable['files_oi']:
        n = start_of_download(record[name]['download_url'])
        print(f"  {name}: download starts ({record[name]['size'] / (1024 ** 2):.0f} MB, first {n} bytes read)")
    return True


def check_dynamic_land_cover():
    # every file of the default configuration must be there, be a GeoTIFF
    # and be the built-up cover fraction layer of the year it is configured for
    fine = True
    for variable in load_config('copernicus_dynamic_land_cover.json')['variables']:
        file_name = variable['url'].split('/files/')[-1].split('?')[0]
        response = requests.head(variable['url'], allow_redirects=True, timeout=30)
        problems = []
        if response.status_code != 200:
            problems.append(f"status code {response.status_code}")
        elif 'tiff' not in response.headers.get('Content-Type', ''):
            problems.append(f"not a GeoTIFF ({response.headers.get('Content-Type')})")
        if 'BuiltUp-CoverFraction' not in file_name:
            problems.append("the url is not a built-up cover fraction layer")
        if f"_{variable['year']}-" not in file_name:
            problems.append(f"the url is not a file of the year {variable['year']}")
        if problems:
            fine = False
            print(f"  {variable['name']}: !!!!!! {', '.join(problems)} !!!!!!")
        else:
            print(f"  {variable['name']}: available ({int(response.headers.get('Content-Length', 0)) / (1024 ** 2):.0f} MB)")
    return fine


def check_modis():
    # same code as the workflow (utils/modis.py): Earthdata login, search of one year, then one file is
    # downloaded and read with the reader and the conversion of the workflow
    variable = load_config('modis_vegetation_indices.json')['variables'][0]
    modis.with_retries(lambda: earthaccess.login(strategy="netrc"), 'Earthdata login', attempts=3, pause=20)
    granules = modis.with_retries(lambda: earthaccess.search_data(
        short_name=variable['name'], temporal=("2020-01-01", "2020-12-31"),
        bounding_box=(TEST_BBOX[1], TEST_BBOX[2], TEST_BBOX[3], TEST_BBOX[0])), 'Earthdata search', attempts=3, pause=20)
    if len(granules) == 0:
        print("  !!!!!! no data found !!!!!!")
        return False
    with tempfile.TemporaryDirectory() as tmp:
        earthaccess.download(granules[:1], local_path=tmp)
        hdf_file = [os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith('.hdf')][0]
        raw, attributes = modis.read_sds(hdf_file, variable['vars'][0])
        values = modis.to_index(raw, attributes)
    low, high = float(values[values == values].min()), float(values[values == values].max())
    if raw.shape != (variable['tile_pixels'], variable['tile_pixels']) or low < -0.2001 or high > 1.0001:
        print(f"  !!!!!! unexpected content: shape {raw.shape}, values {low:.3f} to {high:.3f} !!!!!!")
        return False
    print(f"  {len(granules)} files found for 2020 in the test area; one file downloaded and read with the reader "
          f"'{modis.HDF_READER}', {variable['vars'][0]} from {low:.3f} to {high:.3f}")
    return True


def check_global_treecover():
    # same tile selection and addresses as the workflow (utils/global_tc.py):
    # the first tile of the test area must be there for every configured product
    fine = True
    for variable in load_config('treecover_global.json')['variables']:
        tiles = global_tc.tiles_of_bbox(TEST_BBOX)
        url, _ = global_tc.TILE_URL[variable['name']](variable['url'], *tiles[0])
        response = requests.head(url, allow_redirects=True, timeout=60)
        if response.status_code == 200:
            print(f"  {variable['name']}: {len(tiles)} tiles for the test area, first tile available "
                  f"({int(response.headers.get('Content-Length', 0)) / (1024 ** 2):.0f} MB)")
        else:
            fine = False
            print(f"  {variable['name']}: !!!!!! first tile not available (status code: {response.status_code}) !!!!!!")
    return fine


def check_worldpop():
    # the configured product for a small country (Luxembourg) and one year, with the library the workflow
    # uses. As in the workflow (utils/worldPopDownload.py) the files of the library are kept in a
    # temporary folder and removed afterwards.
    from worldpoppy import wp_raster
    variable = load_config('worldPop.json')['variables'][0]
    cache_dir = tempfile.mkdtemp(prefix='worldpop_check_')
    os.environ["WORLDPOPPY_CACHE_DIR"] = cache_dir
    try:
        source = wp_raster(product_name=variable['product_name'], aoi='LUX', years=[int(variable['start_year'])], masked=True)
        data = source.load()
        source.close()
        people = float(data.sum())
    finally:
        xr.backends.file_manager.FILE_CACHE.clear()
        gc.collect()
        shutil.rmtree(cache_dir, ignore_errors=True)
    if not 300000 < people < 1000000:
        print(f"  !!!!!! unexpected content: {people:.0f} people in Luxembourg in {variable['start_year']} !!!!!!")
        return False
    print(f"  product '{variable['product_name']}' downloaded for Luxembourg, {variable['start_year']}: {people / 1000:.0f} thousand people")
    return True


CHECKS = {
    'cams': check_cams,
    'era5_single': check_era5_single,
    'era5_land': check_era5_land,
    'espon': check_espon,
    'EOC_Atmosphere': check_eoc_atmosphere,
    'EOC_WSF3D': check_wsf3d,
    'EOC_WSF': check_wsf,
    'treecover_copernicus': check_treecover_copernicus,
    'corine_copernicus': check_corine,
    'spei': check_spei,
    'copernicus_dem': check_copernicus_dem,
    'ntl': check_ntl,
    'glwd': check_glwd,
    'Copernicus_dynamic_land_cover': check_dynamic_land_cover,
    'modis_vi': check_modis,
    'global_treecover': check_global_treecover,
    'worldpop': check_worldpop,
}


def main(arguments):
    if '--list' in arguments:
        print('\n'.join(CHECKS))
        return 0
    unknown = [name for name in arguments if name not in CHECKS]
    if unknown:
        print(f"Unknown source(s): {unknown}. Known: {', '.join(CHECKS)}")
        return 2
    results = {}
    for name in (arguments or list(CHECKS)):
        print(f"Checking {name}...")
        try:
            results[name] = 'available' if CHECKS[name]() else 'PROBLEM'
        except Exception as e:
            print(f"  !!!!!! not available: {type(e).__name__}: {e} !!!!!!")
            results[name] = 'NOT AVAILABLE'
        print(f"{name}: {results[name]}")
        print("--------------------------------")
    print("Summary")
    for name, result in results.items():
        print(f"  {name:32s} {result}")
    return 0 if all(result == 'available' for result in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
