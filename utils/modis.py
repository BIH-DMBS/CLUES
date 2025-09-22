import requests
import time
import os
from datetime import datetime, timedelta
import xarray as xr
import numpy as np
import os
import re
import glob
import gc
import yaml
import utils

try:
    from .config import download_folder, tmp_folder, secrets_folder
except:
    from config import download_folder, tmp_folder, secrets_folder

def download_modis(url, headers, file_path):
    print('############################')
    print(url)
    print(headers)
    print(file_path)

    # Send the request with streaming enabled
    try:
        response = requests.get(url,  headers=headers, stream=True)
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")
        return

    if response.status_code == 200:
        total_size = response.headers.get('Content-Length')
        total_size = int(total_size) if total_size and total_size.isdigit() else None

        chunk_size = 8192
        downloaded = 0
        start_time = time.time()

        try:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        elapsed = time.time() - start_time
                        speed = downloaded / 1024 / 1024 / max(elapsed, 1e-6)

                        if total_size:
                            print(f"\rDownloaded: {downloaded / 1024 / 1024:.2f} MB "
                                f"of {total_size / 1024 / 1024:.2f} MB "
                                f"({speed:.2f} MB/s)", end='')
                        else:
                            print(f"\rDownloaded: {downloaded / 1024 / 1024:.2f} MB "
                                f"(Unknown total size, {speed:.2f} MB/s)", end='')
            print()  # New line after download progress
        except IOError as e:
            print(f"Error writing to file {file_path}: {e}")
            return
        print('\nDownload completed successfully.')
    else:
        print(f'Failed to download file. Status code: {response.status_code}')

    return response


def get_dates(yearOI, url, headers, start_date):
    print(url)
    print(headers)
    print('############################')
        # Send the request  with streaming enabled

    try:
        response = requests.get(url,  headers=headers)
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return
    if response.status_code == 200:
        lines = response.content.decode('utf-8').splitlines()

        # Find the line that starts with 'time'
        time_values = next((line for line in lines if line.startswith('/time')), None).split(',')[1:]
        lenY = len(next((line for line in lines if line.startswith('/YDim')), None).split(',')[1:])
        lenX = len(next((line for line in lines if line.startswith('/XDim')), None).split(',')[1:])

        time_values = [int(val.strip()) for val in time_values]
        # Generate corresponding dates
        date_vector = [start_date + timedelta(days=d) for d in time_values]
        time_values = [(i,d) for i, d in enumerate(date_vector) if d.year == yearOI]
        print(time_values)
        idxs= [x[0] for x in time_values]
        time_values = [x[1] for x in time_values]
        return lenX, lenY, idxs, time_values
    else:
        print(f'Failed to download file. Status code: {response.status_code}')


def modis_tiles_for_regions(bbox):
    """
    Given a bounding boxes in the format:
        [lat_max, lon_min, lat_min, lon_max]
    returns list of (h, v) MODIS tiles that cover them.
    """
    result = {}

    lat_max, lon_min, lat_min, lon_max = bbox
    
    # Clamp bounds
    lat_min = max(-90, min(90, lat_min))
    lat_max = max(-90, min(90, lat_max))
    lon_min = max(-180, min(180, lon_min))
    lon_max = max(-180, min(180, lon_max))

    # Convert lat/lon to MODIS tile indices
    h_min = int((lon_min + 180) // 10)
    h_max = int((lon_max + 180) // 10)
    v_min = int((90 - lat_max) // 10)
    v_max = int((90 - lat_min) // 10)

    # Clamp to MODIS grid size
    h_min = max(0, min(35, h_min))
    h_max = max(0, min(35, h_max))
    v_min = max(0, min(17, v_min))
    v_max = max(0, min(17, v_max))

    return [f"h{h:02d}v{v:02d}" for h in range(h_min, h_max + 1) for v in range(v_min, v_max + 1)]


def mergeNetCDFModis(name, typ, year, file_list, lenX, lenY):
    data_dir = os.path.join(download_folder, typ, name)
    # Parameters
    tile_regex = re.compile(r'h(\d{2})v(\d{2})')

    print(file_list)
    # Parse tile indices
    tiles = {}
    for f in file_list:
        match = tile_regex.search(f)
        if not match:
            continue
        h, v = int(match.group(1)), int(match.group(2))
        tiles[(h, v)] = f

    # Determine overall tile grid
    hs = sorted(set(h for h, v in tiles.keys()))
    vs = sorted(set(v for h, v in tiles.keys()))
    min_h, min_v = min(hs), min(vs)

    grid_width = len(hs) * lenX
    grid_height = len(vs) * lenY

    # Load one file to get variable names and time
    sample_ds = xr.open_dataset(next(iter(tiles.values())))
    time_dim = sample_ds['time']
    sample_var = sample_ds[name]
    dtype = sample_var.dtype
    fill_value = sample_var.attrs.get('_FillValue', np.nan)

    # Preallocate arrays
    ndvi_mosaic = np.full((len(time_dim), grid_height, grid_width), fill_value, dtype=dtype)
    lat_mosaic = np.full((grid_height, grid_width), np.nan, dtype=np.float64)
    lon_mosaic = np.full((grid_height, grid_width), np.nan, dtype=np.float64)

    # Fill the mosaic
    for (h, v), f in tiles.items():
        ds = xr.open_dataset(f)
        
        y_off = (v - min(vs)) * lenY
        x_off = (h - min(hs)) * lenX

        ndvi_mosaic[:, y_off:y_off+lenY, x_off:x_off+lenX] = ds[name].values
        lat_mosaic[y_off:y_off+lenY, x_off:x_off+lenX] = ds['Latitude'].values
        lon_mosaic[y_off:y_off+lenY, x_off:x_off+lenX] = ds['Longitude'].values
    # Create the new dataset
    merged_ds = xr.Dataset(
        {
            name: (("time", "YDim", "XDim"), ndvi_mosaic),
            "Latitude": (("YDim", "XDim"), lat_mosaic),
            "Longitude": (("YDim", "XDim"), lon_mosaic)
        },
        coords={
            "time": time_dim
        }
    )
    encoding_dict = {
        name: {'zlib': True, 'complevel': 5},
        'Latitude': {'zlib': True, 'complevel': 5, 'dtype': 'float32'},
        'Longitude': {'zlib': True, 'complevel': 5, 'dtype': 'float32'}
    }

    print('Start saving result')
    # Save result with encoding
    output_path = os.path.join(data_dir, f"{year}.nc")
    # Pass the encoding dictionary to to_netcdf()
    try:
        merged_ds.to_netcdf(output_path, encoding=encoding_dict)
    except Exception as e:
        print(f"Error saving dataset: {e}")
        return

    print(f"Merged and compressed dataset saved as: {output_path}")

    # remove files that are not needed anymore
    for file_path in file_list:
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")
            print(f"Deleted: {file_path}")
        else:
            print(f"File not found (skipped): {file_path}")


def get_evi_ndvi_modis(data_url, headers, typ, name, yearOI, start_date, tiles):
    print('###-----------------########')
    downoad_path = os.path.join(download_folder, typ, name)
    os.makedirs(downoad_path, exist_ok=True)

    s_time = set()
    for t in tiles:
        url = data_url + t + ".ncml.dap.csv?dap4.ce=/YDim;/XDim;/time"
        print(url)
        print('###############')
        lenX, lenY, idxs, time_values = get_dates(yearOI, url, headers, start_date)
        print('#########fffd######')
        s_time = s_time|set(time_values)
        
    s_time = sorted(list(s_time))

    file_list = []
    print('sfeffeefe')
    print(tiles)
    for t in tiles:
        print(t)
        print('fiwhfioqefiqjefih')
        netCDF_file = f'{yearOI}_{t}.nc'
        netCDF_file_path = os.path.join(downoad_path, netCDF_file)
        file_list.append(netCDF_file_path)
        print(netCDF_file_path)
        if not os.path.exists(netCDF_file_path):
            url = data_url + t + ".ncml.dap.csv?dap4.ce=/YDim;/XDim;/time"
            print(url)
            lenX, lenY, idxs, time_values = get_dates(yearOI, url, headers, start_date)
            print(lenX)
            print(lenY)
            print(time_values)
            print('----------------------------------------')
            #netCDF_file = f'{yearOI}_{t}.nc'

            #file_path = os.path.join(name, netCDF_file)
            temp_path = netCDF_file_path + ".tmp"
            print(f"{lenX, lenY, idxs, time_values}")
            url = data_url + t + f".ncml.dap.nc4?dap4.ce=/Latitude[0:1:{lenX-1}][0:1:{lenY-1}];/Longitude[0:1:{lenX-1}][0:1:{lenY-1}];/{name}[{idxs[0]}:1:{idxs[-1]}][0:1:{lenX-1}][0:1:{lenY-1}];/time[{idxs[0]}:1:{idxs[-1]}]"
            download_modis(url, headers, netCDF_file_path)
            
            temp_path = netCDF_file_path + ".tmp"
            ds_reindexed = None

            try:
                # not all netcdf files from origin have the same temporal dimension
                with xr.open_dataset(netCDF_file_path) as ds:
                    if len(ds['time']) < len(s_time):
                        ds = ds.load()  # <- Load everything into memory NOW
                        ds.close()      # <- Fully close the backing file
                        ds_reindexed = ds.reindex(time=s_time)

                # Save safely
                if ds_reindexed is not None:
                    ds_reindexed.to_netcdf(temp_path, engine='netcdf4')  # or use 'netcdf4'
                    ds_reindexed.close()
                    gc.collect()
                    os.replace(temp_path, netCDF_file_path)
            except Exception as e:
                print(f"Error processing {netCDF_file_path}: {e}")
        else:
            print(f"{netCDF_file} exists")
    print('###########')
    print(file_list)
    print(f"lenX: {lenX}, lenY: {lenY}")
    return file_list, lenX, lenY


def get_modis_vi(json_file, name, year):
    parameter = utils.get_parameter(json_file,'bbox.json')
    typ = parameter['type']
    tiles = modis_tiles_for_regions(parameter['bbox'])
    for v in parameter['variables']:
        if v['name'] == name:
            url = v['url']
            parameter = v
            break

    # Create a client for the CDS API
    file = os.path.join(secrets_folder, 'nasa.sct')

    with open(file, 'r') as f:
            credentials = yaml.safe_load(f)
    token = credentials['token']
    headers = {
        'Authorization': f'Bearer {token}'
    }
    print(url)
    print(headers)
    print(typ)
    print(name)
    print(year)
    print(parameter['start'])
    print(tiles)
    print('ssssssssssssssssssssssssss')
    file_list, lenX, lenY = get_evi_ndvi_modis(url, headers, typ, name, int(year), datetime.strptime(parameter['start'], '%Y-%m-%d'), tiles)
    mergeNetCDFModis(name, typ, year, file_list, lenX, lenY)
