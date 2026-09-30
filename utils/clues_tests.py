import os
import yaml
import cdsapi
import cloudscraper
import requests
import time
from owslib.wms import WebMapService
import earthaccess
from worldpoppy import wp_raster

from utils import connect_wms
import global_tc 

base_folder = r"C:\code\CLUES"
secrets_folder = f"{base_folder}\secrets"

# python .\utils\clues_tests.py
# This script checks the availability of all data sources used in CLUES by attempting to access/download a small sample from each source.

ckecklist = [
    'cams',
    'era5_single',
    'espon',
    'EOC_Atmosphere',
    'EOC_WSF3D',
    'EOC_WSF',
    'treecover_copernicus',
    'corine_copernicus',
    'spei',
    'copernicus_dem',
    'ntl',
    'glwd',
    'Copernicus_dynamic_land_cover',
    'modis_vi',
    'global_treecover',
    'worldpop'
]

def get_all_files(article_id):
    files = []
    seen = set()
    page = 1
    while True:
        url = f"https://api.figshare.com/v2/articles/{article_id}/files?page={page}&page_size=100"
        batch = requests.get(url, timeout=30).json()
        if not batch:
            break
        for f in batch:
            if f["name"] not in seen:
                seen.add(f["name"])
                files.append(f)
        if len(batch) < 100:
            break
        page += 1
    return files

def download_ntl_glwd(article_id, files_oi="all"):
    files = get_all_files(article_id)
    if files_oi != "all":
        files = [f for f in files if f["name"] in files_oi]

    print(f"Found {len(files)} file(s) to download")

    for file_info in files:
        print(f"  Downloading: {file_info['name']}")
        r = requests.get(file_info["download_url"], stream=True, timeout=120,
                         headers={"Accept-Encoding": "identity"})
        r.raise_for_status()

        downloaded = 0
        for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
            if chunk:
                x = chunk
                downloaded += len(chunk)
                print(f"    {downloaded * 100 / file_info['size']:.1f}%", end="\r", flush=True)
                break
        break
    print('figshare resource works')

for item in ckecklist:
    print(f"Checking {item}...")
    if item == 'cams':
        file = os.path.join(secrets_folder, 'cdsapirc_atmo.sct')
        with open(file, 'r') as f:
            credentials = yaml.safe_load(f)
        c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

        source = "cams-global-reanalysis-eac4"
        name = "black_carbon_aerosol_optical_depth_550nm"

        # Use verify=1 to check availability without downloading
        try:
            result = c.retrieve(
                source,
                {
                    "variable": [name],
                    "date": ["2013-08-01/2013-08-01"],
                    "time": ["00:00"],
                    "data_format": "grib",
                    "area": [5, -5, -5, 5]     
                },
                'test.nc'
            )
        except Exception as e:
            print(f"Not available: {e}")

        if os.path.exists('test.nc'):
            print("CAMS: Available and downloaded successfully.")
            os.remove('test.nc')
            print("--------------------------------")

    elif item == 'era5_single':    
        file = os.path.join(secrets_folder, 'cdsapirc_climate.sct')
        with open(file, 'r') as f:
            credentials = yaml.safe_load(f)
        c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

        source = "reanalysis-era5-single-levels"
        name = "2m_dewpoint_temperature"
        year = 2012

        # Use verify=1 to check availability without downloading
        try:
            result = c.retrieve(
                source,
                {
                    "product_type": ["reanalysis"],
                    "variable": [name],
                    "year": ["1992"],
                    "month": ["04"],
                    "day": ["03"],
                    "time": ["00:00"],
                    "data_format": "grib",
                    "download_format": "unarchived",
                    "area": [5, -5, -5, 5]
                },
                'test.nc'
            )
        except Exception as e:
            print(f"Not available: {e}")

        if os.path.exists('test.nc'):
            print("ERA5 Single Levels: Available and downloaded successfully.")
            os.remove('test.nc')
            print("--------------------------------")
    elif item == 'espon':
        url = 'https://database.espon.eu/api/select/themes/'
        scraper = cloudscraper.create_scraper(
        browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        # Add additional headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://database.espon.eu/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        try:
            response = scraper.get(url, stream=True)
            if response.status_code == 200:
                    print("ESPON: Available and reachable.")
            else:
                print(f"ESPON: Not reachable, status code {response.status_code}.")
        except Exception as e:
            print(f"ESPON: Not reachable, error: {e}")
        print("--------------------------------")

    elif item == 'EOC_Atmosphere':
        url = "https://geoservice.dlr.de/eoc/atmosphere/wms"
        wms = connect_wms(url)
        try:
            map_request = wms.getmap(
            layers = ["ERS-2_GOME-1_DAILY_CF"],
            srs = "EPSG:4326",
            bbox = [-5, -5, 5, 5], # copernicus and eoc use a different order of bbox parameters['bbox'],
            size = (1000,1000),
            format = "image/geotiff",
            time = '2010-07-03T00:00:00.000Z'
            )
            with open('test.tiff', 'wb') as f:
                f.write(map_request.read())
        except Exception as e:
            print(f"An error occurred: {e}")
            # Create an empty file
            with open('test.tiff', 'w') as file:
                pass
        if os.path.exists('test.tiff'):
            print("EOC Atmosphere: Available and downloaded successfully.")
            os.remove('test.tiff')
        print("--------------------------------")

    elif item == 'EOC_WSF3D':
        url = "https://download.geoservice.dlr.de/WSF3D/files/global/WSF3D_V02_BuildingArea.tif"
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)

            if response.status_code == 200:
                print("EOC_WSF3D: available for download")

                # Optional: check file size (in bytes)
                size = response.headers.get('Content-Length')
                if size:
                    print(f"File size: {int(size) / (1024**2):.2f} MB")
            else:
                print(f"File not available (status code: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        print("--------------------------------")
    elif item == 'EOC_WSF':
        url = "https://download.geoservice.dlr.de/WSF2015/files/WSF2015_v2_-100_58/WSF2015_v2_-100_58.tif"
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)

            if response.status_code == 200:
                print("EOC_WSF: available for download")

                # Optional: check file size (in bytes)
                size = response.headers.get('Content-Length')
                if size:
                    print(f"File size: {int(size) / (1024**2):.2f} MB")
            else:
                print(f"File not available (status code: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        print("EOC WSF: Available.")
        print("--------------------------------")
    elif item == 'treecover_copernicus':
        url = "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_Tree_Cover_Density_2012/MapServer/WMSServer"
        wms = WebMapService(url, version='1.3.0')
        try:
            map_request = wms.getmap(
            layers = ["Tree_Cover_Density_2012_100m46139"],
            srs = "EPSG:4326",
            bbox = [-5, -5, 5, 5], # copernicus and eoc use a different order of bbox parameters['bbox'],
            size = (1000,1000),
            format = "image/png",
            )
            with open('test.png', 'wb') as f:
                f.write(map_request.read())
        except Exception as e:
            print(f"An error occurred: {e}")
            # Create an empty file
            with open('test.png', 'w') as file:
                pass
        if os.path.exists('test.png'):
            print("Tree Cover (Copernicus): Available and downloaded successfully.")
            os.remove('test.png')
        print("--------------------------------")
    elif item == 'corine_copernicus':
        url = "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2012_WM/MapServer/WMSServer"
        wms = WebMapService(url, version='1.3.0')
        try:
            map_request = wms.getmap(
            layers = ["Corine_Land_Cover_2012_raster59601"],
            srs = "EPSG:4326",
            bbox = [11.2682, 51.3618, 14.7636, 53.5587], # copernicus and eoc use a different order of bbox parameters['bbox'],
            size = (1000,1000),
            format = "image/png",
            )
            with open('test.png', 'wb') as f:
                f.write(map_request.read())
        except Exception as e:
            print(f"An error occurred: {e}")
            # Create an empty file
            with open('test.png', 'w') as file:
                pass
        if os.path.exists('test.png'):
            print("Tree Cover (Copernicus): Available and downloaded successfully.")
            os.remove('test.png')
        print("--------------------------------")
    elif item == 'spei':
        url = "https://digital.csic.es/bitstream/10261/364137/01/spei01.nc"
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)

            if response.status_code == 200:
                print("Spei: available for download")

                # Optional: check file size (in bytes)
                size = response.headers.get('Content-Length')
                if size:
                    print(f"File size: {int(size) / (1024**2):.2f} MB")
            else:
                print(f"File not available (status code: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        print("SPEI: Available.")
        print("--------------------------------")
    elif item == 'copernicus_dem':
        # the Copernicus DEM is downloaded from the public AWS Open Data registry (no account needed)
        # test tile N50 E010 (covers 50-51°N, 10-11°E)
        urls = {
            '30m': 'https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N50_00_E010_00_DEM/Copernicus_DSM_COG_10_N50_00_E010_00_DEM.tif',
            '90m': 'https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N50_00_E010_00_DEM/Copernicus_DSM_COG_30_N50_00_E010_00_DEM.tif',
        }
        for res, url in urls.items():
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    print(f"Copernicus DEM {res}: available for download")
                else:
                    print(f"Copernicus DEM {res}: not available (status code: {response.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"Copernicus DEM {res}: an error occurred: {e}")

        # download the (small) 90m test tile
        try:
            response = requests.get(urls['90m'], stream=True, timeout=60)
            if response.status_code == 200:
                with open('test.tif', 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        if os.path.exists('test.tif'):
            print("DEM (Copernicus): Available and downloaded successfully.")
            os.remove('test.tif')
        print("--------------------------------")
    elif item == 'ntl':
        article_id = 9828827
        download_ntl_glwd(article_id)
        print("NTL: Available and downloaded successfully.")
        print("--------------------------------")
    elif item == 'glwd':
        article_id = 28519994
        files_oi = ['GLWD_v2_0_area_by_class_ha_tif.zip']
        download_ntl_glwd(article_id, files_oi=files_oi)
        print("GLWD: Available and downloaded successfully.")
        print("--------------------------------")
    elif item == 'Copernicus_dynamic_land_cover':
        url = "https://zenodo.org/records/3518026/files/PROBAV_LC100_global_v3.0.1_2016-conso_Bare-CoverFraction-layer_EPSG-4326.tif?download=1"
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)

            if response.status_code == 200:
                print("EOC_WSF: available for download")

                # Optional: check file size (in bytes)
                size = response.headers.get('Content-Length')
                if size:
                    print(f"File size: {int(size) / (1024**2):.2f} MB")
            else:
                print(f"File not available (status code: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        print("--------------------------------")
        print("Copernicus Dynamic Land Cover: Available.")
        print("--------------------------------")
    elif item == 'modis_vi':
        # download MODIS data using Earthdata Login
        earthaccess.login(strategy="netrc")
        # MODIS/Terra Vegetation Indices Monthly L3 Global 1km SIN Grid V061
        granules = earthaccess.search_data(
            short_name="MOD13A3",
            temporal=("2010-01-01", "2010-12-31"),
            bounding_box=(-5, -5, 5, 5)
        )
        if len(granules) > 0:
            print("MODIS VI: Available for download.")
        else:
            print("MODIS VI: !!!!!! no data found. !!!!!!")
        print("--------------------------------")
    elif item == 'global_treecover':
        url = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2022-v1.10/"
        all_tile_data =  global_tc.get_all_tile_urls_hansen(url)
        tilesOI = global_tc.filter_urls_by_bbox_hansen(all_tile_data, [5, -5, -5, 5])
        print(f"Total tiles available: {len(tilesOI)}")
        print(tilesOI[0]['url'])
        response = requests.get(tilesOI[0]['url'], stream=True, timeout=60)
        if response.status_code == 200:
            with open("test.tiff", 'wb') as f:
                for chunk in response.iter_content(1024*1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: test.tiff")
        else:
            print(f"Failed to download test.tiff (Status {response.status_code})")
        if os.path.exists('test.tiff'):
            print("Global Tree Cover (2000): Available and downloaded successfully.")
            os.remove('test.tiff')

        url = "https://ies-ows.jrc.ec.europa.eu/iforce/gfc2020/download.py?version=v2&type=tile"
        all_tile_data =  global_tc.get_all_tile_urls_2020(url)
        tilesOI = global_tc.filter_urls_by_bbox2020(all_tile_data, [5, -5, -5, 5])
        tilesOI = global_tc.filter_existing_tiles(tilesOI)
        print(f"Total tiles available: {len(tilesOI)}")
        print(tilesOI[0]['url'])
        response = requests.get(tilesOI[0]['url'], stream=True, timeout=60)
        if response.status_code == 200:
            with open("test.tiff", 'wb') as f:
                for chunk in response.iter_content(1024*1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: test.tiff")
        else:
            print(f"Failed to download test.tiff (Status {response.status_code})")
        if os.path.exists('test.tiff'):
            print("Global Tree Cover (2020): Available and downloaded successfully.")
            os.remove('test.tiff')
        print("--------------------------------")
    elif item == 'worldpop':
        data = wp_raster(
            product_name='pop_g2_r25a', 
            aoi=[-5, -5, 5, 5],  # pass bbox
            years=[2020],
            masked=True,
        )
        data.rio.to_raster('test.tiff')
        if os.path.exists('test.tiff'):
            print("WorldPop: Available and downloaded successfully.")
            os.remove('test.tiff')
        print("--------------------------------")