import requests
import json
import os
import geopandas as gpd
import pandas as pd
import zipfile
import re
from shapely import wkt
from filelock import FileLock, Timeout
import utils

try:
    from .config import download_folder, espon_filename_length
except:
    from config import download_folder, espon_filename_length


def sanitize_filename(filename):
    # Define the valid characters for a filename with whitespace
    valid_chars = re.compile(r'[^a-zA-Z0-9. _-]')
    # Remove invalid characters
    sanitized_filename = valid_chars.sub('', filename)
    # Define the valid characters for a filename withou whitespace
    valid_chars = re.compile(r'[^a-zA-Z0-9._-]')
    # Replace whitespaces with an underscore
    sanitized_filename = valid_chars.sub('_', sanitized_filename)  
    return sanitized_filename


def get_feature_id(data, dimension, name):
    # from the data given in the config espon file get the mapping between group/dimension
    # and the several features assoiated with the dimension, check the following example:
    '''
     {
            "dimension": [
                "Deaths by age groups and gender"
            ],
            "features": [
                {
                    "csv": "https://database.espon.eu/private-media/object/3/ind_3_d_f_0-4_csv.zip",
                    "shape": "https://database.espon.eu/private-media/object/3/ind_3_d_f_0-4_shp.zip",
                    "id": 3,
                    "name": "Deaths - female - age group 0-4"
                },
                {
                    "csv": "https://database.espon.eu/private-media/object/4/ind_4_d_f_5-9_csv_CdWt3ba.zip",
                    "shape": "https://database.espon.eu/private-media/object/4/ind_4_d_f_5-9_shp_QMUjEgM.zip",
                    "id": 4,
                    "name": "Deaths - female - age group 5-9"
                },
    '''
    for variable in data.get("variables", []):
        if dimension == sanitize_filename(str(variable["dimension"]))[0:espon_filename_length]:
            for feature in variable.get("features", []):
                if sanitize_filename(feature["name"])[0:espon_filename_length] == name:
                    return [ feature.get("id"), variable["dimension"]]
    return None


def generate_espon_json():
    # the espon.json should not created by hand
    # use this fuvtion to generate this file from the data available online
    # use avaible metadata from espon to create the json that covers data avaible on espon 
    # can be used and modified as the espon.json given in the config_sources folder
    
    # URL of the web source
    base_url = "https://database.espon.eu/api/select/indicators/"
    params = {
        "limit": 50,
        "offset": 0
    }

    all_results = []

    while True:
        # Make an HTTP GET request to the web source with pagination parameters
        response = requests.get(base_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Append current page results to all_results
            all_results.extend(data.get("results", []))

            # Check if there are more pages
            next_url = data.get("next")
            if next_url:
                # Update offset parameter for the next page
                params["offset"] += params["limit"]
            else:
                break  # Exit loop if there are no more pages
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            break
        
    # soret dict by id
    all_results_sorted = sorted(all_results, key=lambda x: x['id'])

    # remove double entries in the dict
    seen_ids = {}
    unique_results_sorted = []
    for item in all_results_sorted:
        if item['id'] not in seen_ids:
            unique_results_sorted.append(item)
            seen_ids[item['id']] = True

    # unique_dict_list now contains only dictionaries with unique 'id's

    keys = ['id','name']

    erg = []
    for d in unique_results_sorted:
        tmp = {}
        if d['package']:
            if len(d['package'])==2:
                if d['parents']:
                    tmp['dimension'] = set([p['parent_name'] for p in d['parents']])
                else: 
                    tmp['dimension'] = {'no parent'}
                for x in d['package']: # always two (shape and csv)
                    if x['category'] == 'Indicator package (CSV+XLS)':
                        tmp['csv'] = x['url'] 
                    if x['category'] == 'Indicator package (SHAPE)':
                        tmp['shape'] = x['url']
                for k in keys:
                    tmp[k] = d[k]
                erg.append(tmp)
                
    # Create an empty dictionary to keep track of merged results
    merged_dict = {}

    # Iterate over the list of dictionaries
    for item in erg:
        # Extract the id and the other key-value pairs
        id_value = frozenset(item['dimension'])  # Convert set to frozenset to make it hashable
        features = {k: v for k, v in item.items() if k != 'dimension'}
        
        # Check if the id is already in the merged_dict
        if id_value not in merged_dict:
            # If not, create a new entry with the 'features' list
            merged_dict[id_value] = {'dimension': list(item['dimension']), 'features': [features]}
        else:
            # If it is, append the features to the existing 'features' list
            merged_dict[id_value]['features'].append(features)

    # Convert the merged_dict to a list of dictionaries
    result = list(merged_dict.values())

    result = {"type":"espon",
        "source":"espon",
        "link": "https://database.espon.eu/api/",
        "citation":"...",
        "format": "geopandas dataframe with shape",
        "variables":result}

    # Save the result to a JSON file
    with open('espon.json', 'w') as json_file:
        json.dump(result, json_file, indent=4)   


def clear_folder(folder_path, name, shp_zip_file):
    # Iterate over all files in the specified folder
    for filename in os.listdir(folder_path):
        # Construct full file path
        file_path = os.path.join(folder_path, filename)
        
        # Check if it is a file and has a .zip extension
        if os.path.isfile(file_path) and not filename.endswith('.csv') and name in file_path:
            os.remove(file_path)
    # Iterate over the list and delete each file
    for file_path in shp_zip_file:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            else:
                print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print("Tempoary files removed.")


def get_asset_espon(json_file, vOI, dim):
    # main method tp download data 
    # stores the the csv of the data in a folder taht is named aftre the dimension in the downloadfolder
    # im addition a second csv file is create(maintained that stores the shapes of the differnt NUTS areas associated with the data
    parameter = utils.get_parameter(json_file,'bbox.json')
    [id, dimension] = get_feature_id(parameter, dim, vOI)

    items = next((p for p in parameter['variables'] if p['dimension'] == dimension), None)
    item = next((i for i in items['features'] if i['id'] == id), None)
    # use asset information to create filepaths
    dimension = sanitize_filename(str(items['dimension']))
    dimension = dimension[0:espon_filename_length] #max folder length names
    name = sanitize_filename(item['name'])
    name = name[0:espon_filename_length]
    
    file_path_csv = os.path.join(download_folder, 'espon', dimension , name  + '.csv')
    file_path_shp = os.path.join(download_folder, 'espon', dimension, name  + '.zip')
    file_path_geometry = os.path.join(download_folder, 'espon', 'geometry.csv')

    # Extract the directory path from the file path
    directory_path = os.path.dirname(file_path_csv)
    print(directory_path)

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # return if result file already exists
    if os.path.exists(file_path_csv):
        print('csv exists')
        return

    # URL of the file to be downloaded
    url = item['shape']
    # Send a HTTP GET request to the URL
    response = requests.get(url, stream=True)
    # Check if the request was successful
    if response.status_code == 200:
        # (1) Save downloaded zipped file with shapes and data with write-binary mode
        with open(file_path_shp, 'wb') as file:
            # Iterate over the response data (stream)
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        # (2) unzip the downloaded file: it contains 1 or more zipped shape files 
        shp_zip_list = []
        with zipfile.ZipFile(file_path_shp, 'r') as zip_ref:
            # find zip files in the zip archive
            for file in zip_ref.namelist():
                if file.endswith('.zip'):
                    # Extract and keep track of the avaible shape files for the asset of interest
                    shp_zip_list.append(os.path.join(directory_path,file))
                    zip_ref.extract(file, directory_path)
        # (3.1) If shape files exist
        if shp_zip_list:
            shp_list = []
            i = 0
            # some of the zip files are bad, if use the csv 
            try: 
                for shp_zip_file in shp_zip_list:
                    with zipfile.ZipFile(shp_zip_file, 'r') as zip_ref:
                        # List all files in the zip archive
                        for file in zip_ref.namelist():
                            if file.endswith('.shp'):
                                print('unzip: ' + file)
                                print('file_path_shp: ' + file_path_shp)
                                print('name: ' + name)
                                with zip_ref.open(file) as source, open(os.path.splitext(file_path_shp)[0]  + '-' + str(i) + '.shp', 'wb') as target:
                                    target.write(source.read())
                                    shp_list.append(os.path.splitext(file_path_shp)[0]  + '-' + str(i) + '.shp')
                                    print(shp_list)
                            elif file.endswith('.shx'):
                                with zip_ref.open(file) as source, open(os.path.splitext(file_path_shp)[0]  + '-' + str(i) + '.shx', 'wb') as target:
                                    target.write(source.read())
                            elif file.endswith('.dbf'):
                                with zip_ref.open(file) as source, open(os.path.splitext(file_path_shp)[0]  + '-' + str(i) + '.dbf', 'wb') as target:
                                    target.write(source.read())
                            elif file.endswith('.prj'):
                                with zip_ref.open(file) as source, open(os.path.splitext(file_path_shp)[0]  + '-' + str(i) + '.prj', 'wb') as target:
                                    target.write(source.read())
                    i = i+1
                shape2csv_lock(shp_list, file_path_csv, file_path_geometry)
            except zipfile.BadZipFile:
                print('----Bad Zip streamline-----')
                # URL of the file to be downloaded
                download_csv(item['csv'], file_path_csv)

        # (3.2) If no shape file download the csv file that does not have geometries
        # if the geometries are not present that's not a problem tunit_code is given so it can be 
        # linked to the geomtries of the other assets                      
        else:
            print('-----only csv, no spape----')
            # URL of the file to be downloaded
            download_csv(item['csv'], file_path_csv)
        clear_folder(directory_path, name, shp_zip_list)
    else:
        print(f"Failed to download the shp file. Status code: {response.status_code}")
    return 'done'


def download_csv(url, file_path_csv):
    # Send a HTTP GET request to the URL
    response = requests.get(url, stream=True)
    fp_csv = file_path_csv + '.zip'
    # Check if the request was successful
    if response.status_code == 200:
        # Open a local file with write-binary mode
        with open(fp_csv, 'wb') as file:
            # Iterate over the response data (stream)
            for chunk in response.iter_content(chunk_size=1024):
                # Write data to the file
                file.write(chunk)
        # Unzip the downloaded file
        with zipfile.ZipFile(fp_csv, 'r') as zip_ref:
            # List all files in the zip archive
            for file in zip_ref.namelist():
                if file.endswith('.csv'):
                    # Extract the CSV file
                    with zip_ref.open(file) as source, open(file_path_csv, 'wb') as target:
                        target.write(source.read())
                    # remove the zip file downloaded
                    return 'result csv written done'
        # if no csv in zip create emty file
        with open(file_path_csv, 'w') as file:
            print('its empty')
            pass
    else:
        print(f"Failed to download the csv file. Status code: {response.status_code}")


def shape2csv_lock(shape_files, file_path, file_path_geometry):
    # lock guratees that no other parallel snakemake process tries
    # to use the file with the geometry at the same time
    lock_path = f"{file_path_geometry}.lock"
    lock = FileLock(lock_path, timeout=100)  # Wait up to 10 seconds for the lock 
    try:
        with lock:
            shape2csv(shape_files, file_path, file_path_geometry)
    except Timeout:
        print(f"Could not acquire lock on {file_path} within the timeout period.")
    except Exception as e:
        print(f"An error occurred: {e}")


def shape2csv(shape_files, file_path, file_path_geometry):
    # shapefiles downloaded from espon are splitted up in a csv file that holds specific the data
    # and one csv file for all assets that contains the geometries. 
    # The csv file with the geometries and the data csvs can be joined on 'tunit_code'   
    gdf = []
    crs_ori = ''
    # data may come in different resolutions each in a specific shape file.
    for f in shape_files:
        tmp = gpd.read_file(f)
        crs_ori = tmp.crs
        print(tmp.crs)
        gdf.append(tmp)
    print('---------')
    # Concatenate the GeoDataFrames
    gdf = gpd.GeoDataFrame(pd.concat(gdf, ignore_index=True))
    # Drop duplicate geometries, keeping the first occurrence
    gdf = gdf.drop_duplicates(subset='geometry', keep='first')
    # Create a new GeoDataFrame with only 'geometry' and 'tunit_code'
    gdf_geometry_and_tunit = gdf[['geometry', 'tunit_code']]
    gdf_geometry_and_tunit.set_crs(crs_ori, inplace=True)
    gdf_geometry_and_tunit.to_crs(epsg=4326, inplace=True)
    # Create a new GeoDataFrame without 'geometry'
    gdf = gdf.drop(columns='geometry')
    # save data csv
    gdf.to_csv(file_path, index=False)

    # update the existing geometry csv
    if os.path.exists(file_path_geometry):
        # Read the CSV file using pandas
        df = pd.read_csv(file_path_geometry)
        # Convert the 'geometry' column from WKT to shapely geometries
        df['geometry'] = df['geometry'].apply(wkt.loads)
        # Create a GeoDataFrame
        gdf_existing = gpd.GeoDataFrame(df, geometry='geometry')
        gdf_existing.set_crs(epsg=4326, inplace=True)
        # Concatenate (append) gdf_geometry_and_tunit to gdf_existing
        gdf_geometry_and_tunit = gpd.GeoDataFrame(pd.concat([gdf_existing, gdf_geometry_and_tunit], ignore_index=True))
        gdf_geometry_and_tunit = gdf_geometry_and_tunit.drop_duplicates(subset=['geometry', 'tunit_code'])

    print(gdf_geometry_and_tunit.shape[0])
    gdf_geometry_and_tunit.to_csv(file_path_geometry, index=False)
