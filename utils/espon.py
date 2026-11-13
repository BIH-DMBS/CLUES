import requests
import json
import os
import shutil
import geopandas as gpd
import pandas as pd
import zipfile
from filelock import FileLock
import cloudscraper
import utils
from espon_targets import sanitize_filename, find_target

try:
    from .config import download_folder, tmp_folder, espon_filename_length
except ImportError:
    from config import download_folder, tmp_folder, espon_filename_length


API_INDICATORS = "https://database.espon.eu/api/select/indicators/"
PACKAGE_CATEGORIES = {'Indicator package (CSV+XLS)': 'csv', 'Indicator package (SHAPE)': 'shape'}


def fetch_espon_indicators(scraper=None, page_size=50):
    """
    Read the descriptions of all indicators from the interface of the ESPON database, page by page.
    Any failed page is an error: an incomplete list must never become a configuration.
    """
    if scraper is None:
        scraper = cloudscraper.create_scraper()
    indicators = []
    offset = 0
    while True:
        response = scraper.get(API_INDICATORS, params={"format": "json", "limit": page_size, "offset": offset}, timeout=120)
        if response.status_code != 200:
            raise RuntimeError(f"ESPON interface answered with status code {response.status_code} at offset {offset}")
        data = response.json()
        indicators.extend(data.get("results", []))
        if not data.get("next"):
            break
        offset += page_size
    expected = data.get("count")
    n_ids = len({item['id'] for item in indicators})
    if expected is not None and n_ids != expected:
        raise RuntimeError(f"ESPON interface announced {expected} indicators, {n_ids} were delivered")
    return indicators


def build_espon_config(indicators):
    """
    Make the content of espon.json from the indicator descriptions of the ESPON interface.

    An indicator is taken if it offers both packages (shapefiles and csv). Indicators are grouped by
    the set of their parent indicators ('dimension', this becomes the folder name). The result depends
    only on the content of the list: indicators are ordered by id and the parents by name.
    Returns the configuration and the list of the indicators that were left out, as (id, name, reason).
    """
    unique = {}
    for item in indicators:
        unique.setdefault(item['id'], item)

    groups = {}
    skipped = []
    for item_id in sorted(unique):
        item = unique[item_id]
        urls = {}
        for package in item.get('package') or []:
            key = PACKAGE_CATEGORIES.get(package.get('category'))
            if key and package.get('url'):
                urls[key] = package['url']
        missing = [key for key in ('csv', 'shape') if key not in urls]
        if missing:
            skipped.append((item_id, item.get('name'), f"no {' and no '.join(missing)} package"))
            continue
        parents = sorted({parent['parent_name'] for parent in item.get('parents') or []}) or ['no parent']
        feature = {'csv': urls['csv'], 'shape': urls['shape'], 'id': item_id, 'name': item['name'],
                   'years_string': item.get('years_string')}
        groups.setdefault(tuple(parents), []).append(feature)

    config = {"type": "espon",
              "source": "espon",
              "link": "https://database.espon.eu/api/",
              "citation": "...",
              "format": "geopandas dataframe with shape",
              "variables": [{'dimension': list(parents), 'features': features} for parents, features in groups.items()]}
    return config, skipped


def generate_espon_json(target='espon.json'):
    # The espon.json should not be created by hand. This function makes it from the descriptions that
    # the ESPON database offers online. The result can be used (or shortened) as espon.json in the
    # folder configs_sources.
    # Note: the folder of an indicator is named after its dimension. If ESPON changes the parents of
    # an indicator, its folder name changes and the workflow downloads it again under the new name.
    config, skipped = build_espon_config(fetch_espon_indicators())
    part = target + '.part'
    with open(part, 'w', encoding='utf-8') as json_file:
        json.dump(config, json_file, indent=4)
    os.replace(part, target)
    n = sum(len(variable['features']) for variable in config['variables'])
    print(f"{target}: {n} indicators in {len(config['variables'])} dimensions")
    for item_id, name, reason in skipped:
        print(f"left out: {item_id} '{name}' ({reason})")
    return config, skipped


def download(url, target):
    """
    Download a file of the ESPON database to `target`.
    The data is written to a temporary file first, only a complete file gets the final name.
    """
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    part = target + '.part'
    try:
        response = scraper.get(url, stream=True, timeout=300)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download {url}. Status code: {response.status_code}")
        with open(part, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                file.write(chunk)
        os.replace(part, target)
    finally:
        if os.path.exists(part):
            os.remove(part)


def read_shapes_from_package(package_zip, work_dir):
    """
    The shape package of an indicator is a zip file that contains one or more zip files, each with
    one shapefile (the data may come in different resolutions, each in its own shapefile).
    Returns the list of the shapefiles as GeoDataFrames (empty if the package holds no shapefile).
    Raises zipfile.BadZipFile if the package or one of the zip files in it is damaged.
    """
    frames = []
    with zipfile.ZipFile(package_zip, 'r') as package:
        inner_zips = [name for name in package.namelist() if name.endswith('.zip')]
        for i, inner in enumerate(inner_zips):
            folder = os.path.join(work_dir, str(i))
            os.makedirs(folder)
            inner_path = os.path.join(folder, 'shape.zip')
            with package.open(inner) as source, open(inner_path, 'wb') as target:
                shutil.copyfileobj(source, target)
            with zipfile.ZipFile(inner_path, 'r') as shape_zip:
                shape_zip.extractall(folder)
            for root, _, files in os.walk(folder):
                for file in sorted(files):
                    if file.endswith('.shp'):
                        print('read: ' + file)
                        frames.append(gpd.read_file(os.path.join(root, file)))
    return frames


def get_asset_espon(json_file, vOI, dim):
    # main method to download the data of one indicator
    # stores the csv of the data in a folder that is named after the dimension in the download folder
    # in addition a second csv file is maintained that stores the shapes of the different NUTS areas
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    parameter = utils.get_parameter(json_file, 'bbox.json')
    if parameter is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")

    # the folder (dim) and file name (vOI) were made by the snakefile with the same function
    target = find_target(parameter, espon_filename_length, dim, vOI)
    if target is None:
        raise ValueError(f"No indicator with the folder '{dim}' and the file name '{vOI}' in '{json_file}'")
    item = target['feature']

    directory_path = os.path.join(download_folder, 'espon', dim)
    file_path_csv = os.path.join(directory_path, vOI + '.csv')
    file_path_geometry = os.path.join(download_folder, 'espon', 'geometry.csv')
    os.makedirs(directory_path, exist_ok=True)

    # return if result file already exists
    if os.path.exists(file_path_csv):
        print('csv exists')
        return

    # every indicator works in its own temporary folder, so jobs that run at the same time cannot
    # touch each other's files
    work_dir = os.path.join(tmp_folder, f"espon_{item['id']}")
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir)
    try:
        package_zip = os.path.join(work_dir, 'package.zip')
        download(item['shape'], package_zip)
        try:
            frames = read_shapes_from_package(package_zip, work_dir)
        except zipfile.BadZipFile:
            # some of the shape packages are damaged, then the csv package is used
            print('----Bad Zip streamline-----')
            frames = []

        if frames:
            shape2csv_lock(frames, file_path_csv, file_path_geometry, years_string=item.get('years_string', None))
        else:
            # the csv package has no geometries, that is not a problem: tunit_code is given,
            # so the data can be linked to the geometries of the other indicators
            print('-----only csv, no shape----')
            download_csv(item['csv'], file_path_csv, work_dir)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    return 'done'


def download_csv(url, file_path_csv, work_dir):
    # download the csv package of an indicator (a zip file) and store the csv file of it
    csv_zip = os.path.join(work_dir, 'csv_package.zip')
    download(url, csv_zip)
    with zipfile.ZipFile(csv_zip, 'r') as zip_ref:
        csv_files = [file for file in zip_ref.namelist() if file.endswith('.csv')]
        if not csv_files:
            raise RuntimeError(f"No csv file in {url}")
        part = file_path_csv + '.part'
        try:
            with zip_ref.open(csv_files[0]) as source, open(part, 'wb') as target:
                shutil.copyfileobj(source, target)
            os.replace(part, file_path_csv)
        finally:
            if os.path.exists(part):
                os.remove(part)
    return 'result csv written done'


def shape2csv_lock(frames, file_path, file_path_geometry, years_string=None):
    # the lock guarantees that no other parallel snakemake process
    # uses the file with the geometries at the same time
    lock = FileLock(f"{file_path_geometry}.lock", timeout=900)
    with lock:
        shape2csv(frames, file_path, file_path_geometry, years_string=years_string)


def shape2csv(frames, file_path, file_path_geometry, years_string=None):
    # the shapefiles of an indicator are split up into a csv file that holds the data of the indicator
    # and one csv file for all indicators that contains the geometries.
    # The csv file with the geometries and the data csvs can be joined on 'tunit_code'

    # geometries in geographic coordinates, each shapefile can have its own coordinate system
    geometry_frames = []
    for frame in frames:
        print(frame.crs)
        geo = frame[['geometry', 'tunit_code']]
        if frame.crs is not None:
            geo = geo.to_crs(epsg=4326)
        geometry_frames.append(pd.DataFrame({
            'geometry': geo.geometry.apply(lambda g: None if g is None else g.wkt),
            'tunit_code': geo['tunit_code'],
        }))
    new_geometries = pd.concat(geometry_frames, ignore_index=True).dropna(subset=['geometry'])
    new_geometries = new_geometries.drop_duplicates(subset=['geometry', 'tunit_code'])

    # the data without the geometries. Every row of the shapefiles is kept: regions of different levels
    # can have the same geometry (e.g. Berlin is one region at the NUTS levels 1, 2 and 3), these are
    # different rows of the data.
    data = pd.concat([pd.DataFrame(frame.drop(columns='geometry')) for frame in frames], ignore_index=True)
    data = data.drop_duplicates()
    # fix truncated year column name using API metadata (column names of shapefiles have at most 10 characters)
    if years_string:
        for token in years_string.split(','):
            token = token.strip()
            if '-' in token:
                full_col = f"y_{token}"   # e.g. y_2014-2016
                trunc_col = full_col[:10]  # e.g. y_2014-201
                if len(full_col) > 10 and trunc_col in data.columns:
                    data.rename(columns={trunc_col: full_col}, inplace=True)
                    print(f"renamed: {trunc_col} -> {full_col}")

    # add the geometries that are not in the geometry csv yet. Only new rows are appended,
    # the existing file is neither parsed as geometries nor written again.
    if os.path.exists(file_path_geometry):
        existing = pd.read_csv(file_path_geometry, dtype=str)
        known = set(zip(existing['tunit_code'], existing['geometry']))
        is_new = [(code, wkt_text) not in known
                  for code, wkt_text in zip(new_geometries['tunit_code'].astype(str), new_geometries['geometry'])]
        new_geometries = new_geometries[is_new]
        if len(new_geometries) > 0:
            new_geometries.to_csv(file_path_geometry, mode='a', header=False, index=False)
    else:
        os.makedirs(os.path.dirname(file_path_geometry), exist_ok=True)
        new_geometries.to_csv(file_path_geometry, index=False)
    print(f"{len(new_geometries)} new geometries")

    # save the data csv last and under a temporary name first: the csv is the file snakemake waits for,
    # it only appears when everything else is done
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    part = file_path + '.part'
    try:
        data.to_csv(part, index=False)
        os.replace(part, file_path)
    finally:
        if os.path.exists(part):
            os.remove(part)
