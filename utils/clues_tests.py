import os
import yaml
import cdsapi
import cloudscraper
import requests
import time
import pandas as pd
import geopandas as gpd
from owslib.wms import WebMapService
from shapely.geometry import shape
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

# to download data access token from copernicus a needed
def get_copernicus_odata_token():
    # The function retrieves an access token from the Copernicus Data Space Ecosystem (CDSE).
    # It extracts the access token from the response and returns it.
    url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Create a client for the CDS API
    credential_file = os.path.join(secrets_folder, 'copernicus_credential.sct')

    with open(credential_file, 'r') as f:
            credentials = yaml.safe_load(f)

    response = requests.post(url, headers=headers, data=credentials)

    # Access the generated access token
    access_token = response.json().get('access_token')
    return access_token


def get_simple_download_zip(url):

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://figshare.com/",
    })

    # Step 1 — follow the full redirect chain manually to get the real CDN url
    print(f"Resolving redirect chain for: {url}")
    try:
        head = session.head(url, allow_redirects=True, timeout=30)
        final_url = head.url
        content_type = head.headers.get("Content-Type", "")
        content_length = int(head.headers.get("Content-Length", 0))
        print(f"Final URL     : {final_url}")
        print(f"Content-Type  : {content_type}")
        print(f"Content-Length: {content_length}")
    except Exception as e:
        print(f"HEAD request failed: {e}")
        return

    # If HEAD doesn't give a file, fall back to a GET with stream
    if content_length < 1_000_000 or "zip" not in content_type and "octet" not in content_type:
        print("HEAD didn't resolve to a binary — trying GET redirect follow...")
        try:
            probe = session.get(url, allow_redirects=True, timeout=30, stream=True)
            final_url = probe.url
            content_type = probe.headers.get("Content-Type", "")
            content_length = int(probe.headers.get("Content-Length", 0))
            print(f"Final URL     : {final_url}")
            print(f"Content-Type  : {content_type}")
            print(f"Content-Length: {content_length}")
        except Exception as e:
            print(f"GET probe failed: {e}")
            return

        if content_length < 1_000_000:
            # Print a snippet to see if it's an HTML error/login page
            snippet = b""
            for chunk in probe.iter_content(1024):
                snippet += chunk
                if len(snippet) >= 2048:
                    break
            print(f"Response snippet:\n{snippet[:2048]}")
            print("Could not resolve a binary zip URL — see snippet above.")
            return

        # Stream from the already-open response
        total = content_length
        downloaded = 0
        chunks = []
        for chunk in probe.iter_content(chunk_size=4 * 1024 * 1024):
            if chunk:
                print('Download available')
                break
    else:
        # Step 2 — download from the resolved CDN URL directly
        print("Downloading from resolved CDN URL...")
        r = session.get(final_url, stream=True, timeout=60)
        total = content_length
        downloaded = 0
        chunks = []
        for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
           if chunk:
                print('Download available')
                break


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
        access_token = get_copernicus_odata_token()

        if access_token:
            print("Copernicus DEM: Authentication successful, access token obtained.")
        else:
            print("Copernicus DEM: Authentication failed, no access token obtained.")
        
        c = '(10 51, 11 51, 11 50, 10 50, 10 51)'
        url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
        collection = 'COP-DEM'
        filt=f"((Collection/Name eq '{collection}' and\
            OData.CSC.Intersects(area=geography'SRID=4326;POLYGON ({c})')) )"
        url_filt=f"{url}?$filter={filt}"
        
        max_retries = 20
        retry_count = 0
        while retry_count < max_retries:
            response = requests.get(url_filt)
            if response.status_code == 200:
                print('Copernicus DEM: Data available and accessible.')
                json_lnks = requests.get(url_filt)
                json_lnks = json_lnks.json()
                json_lnks = pd.DataFrame.from_dict(json_lnks['value'])
                break
        json_lnks = json_lnks.drop_duplicates(subset=['Name'])
        # Convert the 'GeoFootprint' column to shapely geometries
        json_lnks['geometry'] = json_lnks['GeoFootprint'].apply(lambda x: shape(x))
        # Create a GeoDataFrame
        json_lnks = gpd.GeoDataFrame(json_lnks, geometry='geometry')
        # Filter the DataFrame for asset of interest
        json_lnks = json_lnks[json_lnks['Name'].str.contains("DEM1_SAR_DGE_90", case=False, na=False)]
        json_lnks = json_lnks.drop_duplicates(subset=['geometry'])

        headers = {"Authorization": f"Bearer {access_token}"}
        # Create a session and update headers
        session = requests.Session()
        session.headers.update(headers)
        url = 'https://download.dataspace.copernicus.eu/odata/v1/Products'
        json_lnks = json_lnks.head(1)
        for id in json_lnks['Id']:
            url_download = f"{url}({id})/$value"

            # Perform the GET request
            response = session.get(url_download, stream=True)

            # Check if the request was successful
            if response.status_code == 200:
                with open(os.path.join("test.zip"), "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            file.write(chunk)
            else:
                # try with new token
                access_token = get_copernicus_odata_token()
                headers = {"Authorization": f"Bearer {access_token}"}
                # Create a session and update headers
                session = requests.Session()
                session.headers.update(headers)
                # Perform the GET request
                response = session.get(url_download, stream=True)

                if response.status_code == 200:
                    with open(os.path.join("test.zip"), "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # filter out keep-alive new chunks
                                file.write(chunk)
                else:
                    print(f"Failed to download file. Status code: {response.status_code}")
                    print(response.text)
        if os.path.exists('test.zip'):
            print("DEM (Copernicus): Available and downloaded successfully.")
            os.remove('test.zip')
        print("--------------------------------")
    elif item == 'ntl':
        url = "https://figshare.com/ndownloader/articles/9828827/versions/10"
        get_simple_download_zip(url)
        print("NTL: Available and downloaded successfully.")
        print("--------------------------------")
    elif item == 'glwd':
        url = "https://figshare.com/ndownloader/articles/9828827/versions/10"
        get_simple_download_zip(url)
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