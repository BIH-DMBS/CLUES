import requests
import os
import json
import glob


try:
    from .config import download_folder, configs_assets_folder, area, config_folder, secrets_folder, tmp_folder
except:
    from config import download_folder, configs_assets_folder, area, config_folder, secrets_folder, tmp_folder


def get_all_tile_urls_hansen(base_url):
    urls = []

    lat_tiles = list(range(80, -60, -10))  # N80 to S50
    lon_tiles = list(range(-180, 180, 10)) # W180 to E170

    for lat_deg in lat_tiles:
        lat_label = f"{abs(lat_deg):02d}{'N' if lat_deg >= 0 else 'S'}"

        for lon_deg in lon_tiles:
            lon_label = f"{abs(lon_deg):03d}{'W' if lon_deg < 0 else 'E'}"

            url = f"{base_url}Hansen_GFC-2022-v1.10_treecover2000_{lat_label}_{lon_label}.tif"

            tile_bbox = [
                lat_deg,              # tile north
                lon_deg,              # tile west
                lat_deg - 10,         # tile south
                lon_deg + 10          # tile east
            ]

            urls.append({
                'url': url,
                'bbox': tile_bbox,
                'lat_label': lat_label,
                'lon_label': lon_label
            })

    return urls

# --- 2. Filter URLs intersecting with bbox ---
def filter_urls_by_bbox_hansen(urls, bbox):
    lat_max, lon_min, lat_min, lon_max = bbox
    filtered_urls = []

    for tile in urls:
        tile_bbox = tile['bbox']
        tile_north, tile_west, tile_south, tile_east = tile_bbox

        lat_overlap = not (tile_south >= lat_max or tile_north <= lat_min)
        lon_overlap = not (tile_east <= lon_min or tile_west >= lon_max)

        if lat_overlap and lon_overlap:
            filtered_urls.append(tile)

    return filtered_urls

# --- 3. Check if URL Exists (HEAD request) ---
def url_exists(url, timeout=10):
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def download_tile(tile, dest_folder):
    url = tile['url']
    filename = f"GFC_{tile['lat_label']}_{tile['lon_label']}.tif"
    file_path = os.path.join(dest_folder, filename)

    if os.path.exists(file_path):
        print(f"Already downloaded: {filename}")
        return

    try:
        response = requests.get(url, stream=True, timeout=60)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024*1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download {filename} (Status {response.status_code})")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")


def getHansen(parameters):
    base_url = parameters['variables'][0]['url']
    all_tile_data = get_all_tile_urls_hansen(base_url)
    tilesOI = filter_urls_by_bbox_hansen(all_tile_data, parameters["bbox"])
    download_path = os.path.join(download_folder, parameters['type'],parameters['variables'][0]['name'])
    for tile in tilesOI:
        print(tile)
        download_tile_hansen(tile, download_path)
    # Flag downloads are complete
    done_flag_path = os.path.join(download_path, 'done.flag')
    with open(done_flag_path, 'w') as f:
        pass  # Just create an empty file
    

def get_all_tile_urls_2020(base_url):
    urls = []

    lat_tiles = list(range(80, -60, -10))  # N80 to S50
    lon_tiles = list(range(-180, 180, 10)) # W180 to E170

    lat_tiles = list(range(80, -60, -10))  # 80N to 50S
    lon_tiles = list(range(-180, 180, 10)) # 180W to 170E

    for lat_deg in lat_tiles:
        lat_label = f"{'N' if lat_deg >= 0 else 'S'}{abs(lat_deg):01d}"

        for lon_deg in lon_tiles:
            lon_label = f"{'W' if lon_deg < 0 else 'E'}{abs(lon_deg):01d}"

            url = f"{base_url}&lat={lat_label}&lon={lon_label}"

            # Include tile bounding box metadata for filtering
            tile_bbox = [
                lat_deg,              # tile north
                lon_deg,              # tile west
                lat_deg - 10,         # tile south
                lon_deg + 10          # tile east
            ]

            urls.append({
                'url': url,
                'bbox': tile_bbox,
                'lat_label': lat_label,
                'lon_label': lon_label
            })

    return urls

def filter_urls_by_bbox2020(urls, bbox):
    """
    Filters tile URLs whose bounding boxes intersect with the given bbox.
    bbox = [north, west, south, east]  # Format: [lat_max, lon_min, lat_min, lon_max]
    """
    lat_max, lon_min, lat_min, lon_max = bbox
    filtered_urls = []

    for tile in urls:
        tile_bbox = tile['bbox']
        tile_north, tile_west, tile_south, tile_east = tile_bbox

        # Check for bbox intersection
        lat_overlap = not (tile_south >= lat_max or tile_north <= lat_min)
        lon_overlap = not (tile_east <= lon_min or tile_west >= lon_max)

        if lat_overlap and lon_overlap:
            filtered_urls.append(tile)

    return filtered_urls

def filter_existing_tiles(tiles, timeout=10):
    """
    Takes a list of URLs and returns only those that actually exist (HTTP 200).
    Uses HEAD requests for efficiency.
    """
    existing_urls = []

    for tile in tiles:
        try:
            response = requests.head(tile['url'], timeout=timeout)
            if response.status_code == 200:
                existing_urls.append(tile)
                print(f"Exists: {tile}")
            else:
                print(f"Missing ({response.status_code}): {tile}")
        except requests.RequestException as e:
            print(f"Error checking {tile}: {e}")

    return existing_urls


def getTC2020(parameters):
    base_url = parameters['variables'][0]['url']
    all_tile_data = get_all_tile_urls_2020(base_url)
    tilesOI = filter_urls_by_bbox2020(all_tile_data, parameters["bbox"])
    tilesOI = filter_existing_tiles(tilesOI)
    download_path = os.path.join(download_folder, parameters['type'],parameters['variables'][0]['name'])
    for tile in tilesOI:
        print(tile)
        download_tile(tile, download_path)
    # Flag downloads are complete
    done_flag_path = os.path.join(download_path, 'done.flag')
    with open(done_flag_path, 'w') as f:
        pass  # Just create an empty file


def getTC_global(parameters_jsonfile, vOI):
    with open(os.path.join(configs_assets_folder, parameters_jsonfile), 'r') as file:
        parameters = json.load(file)

    with open(os.path.join(config_folder, 'bbox.json'), 'r') as file:
        bbox = json.load(file)

    parameters['variables'] = [y for y in parameters['variables'] if y['name']==vOI] 
    parameters["bbox"] = bbox[area]
    print(parameters)
    if parameters['variables'][0]['name'] == 'global_tree_cover_hansen_2000':
        getHansen(parameters)
    elif parameters['variables'][0]['name'] == 'Global_forest_cover_2020':
        getTC2020(parameters)

    return 0