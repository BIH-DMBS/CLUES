import cdsapi
import os
import yaml
import zipfile
import xarray as xr
import glob
import yaml
import json

try:
    from .config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder
except:
    from config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder


def get_parameter(bbox_jsonfile):
    parameters = {}

    try:
        with open(os.path.join(config_folder, bbox_jsonfile), 'r') as file:
            bbox = json.load(file)
    except FileNotFoundError:
        print(f"Error: The configuration file '{bbox_jsonfile}' was not found.")
        return None
    except PermissionError:
        print(f"Error: Insufficient permissions to access the file '{bbox_jsonfile}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{bbox_jsonfile}' contains invalid JSON.")
        return None

    if area not in bbox:
        print(f"Error: Missing required key '{area}' in bbox.")
        return None

    parameters["bbox"] = bbox[area]

    return parameters


def getEra5Land(json_file, year, vOI):
    """
    Placeholder function for getting ERA5 Land data.
    """
    print(f"Getting ERA5 Land data for {json_file}, year {year}, variable {vOI}")

    dataset = "reanalysis-era5-land"

    months = ["01","02","03","04","05","06","07","08","09","10","11","12"]

    days = [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09",
        "10", "11", "12",
        "13", "14", "15",
        "16", "17", "18",
        "19", "20", "21",
        "22", "23", "24",
        "25", "26", "27",
        "28", "29", "30",
        "31"
    ]

    times = [
        "00:00", "01:00", "02:00",
        "03:00", "04:00", "05:00",
        "06:00", "07:00", "08:00",
        "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00",
        "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00",
        "21:00", "22:00", "23:00"
    ]

    try:
        parameters = get_parameter('bbox.json')
    except Exception as e:        
        print(f"An error occurred: {e} ")

    try:
        # Create a client for the CDS API
        file = os.path.join(secrets_folder, 'cdsapirc_climate.sct')
        with open(file, 'r') as f:
            credentials = yaml.safe_load(f)
    except Exception as e:
            print(f"An error occurred: {e}")

    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

    download_folder_er5_land = os.path.join(download_folder,'reanalysis-era5-land', vOI)
    print(download_folder_er5_land)

    for month in months:
        tmp_folder = os.path.join(download_folder_er5_land, 'tmp',year) 

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
            print(f"Folder created: {tmp_folder}")
        else:
            print(f"Folder already exists: {tmp_folder}")

        file_path = os.path.join(tmp_folder, f'{month}.nc')
        file_path_zip = os.path.join(tmp_folder, f'{month}.zip')
        
        if os.path.exists(file_path):
            print(f"The file {file_path} exists.")
        else:
            request = {
                "variable": vOI,
                "year": year,
                "month": month,
                "day": days,
                "time": times,
                "data_format": "netcdf",
                "download_format": "zip",
                "area":  parameters['bbox']
            }

            try:
                c.retrieve(dataset, request, file_path_zip)
                print("Data is available for this month.")
                # Open the zip file
                with zipfile.ZipFile(file_path_zip, 'r') as z:
                    # List contents (usually there should be one .nc file)
                    namelist = z.namelist()
                    print("Files in zip:", namelist)

                    # Extract the first .nc file and save as nc_path
                    for name in namelist:
                        if name.endswith('.nc'):
                            with z.open(name) as src, open(file_path, 'wb') as dst:
                                dst.write(src.read())
                            print(f"Saved {name} as {file_path}")
                            break
                    # Delete the zip file after successful extraction
                os.remove(file_path_zip)
            except Exception as e:
                print("Data is NOT available:", e)
    # List all monthly files in order
    files = sorted(glob.glob(tmp_folder+'/*.nc'))
    print(files)
    # Open all files as a single xarray dataset along the 'time' dimension
    #ds = xr.open_mfdataset(files, combine='by_coords', chunks=None)

    # Optional: inspect
    #print(ds)

    # Save to a new NetCDF file
    # Open, merge, and save safely
    with xr.open_mfdataset(files, combine='by_coords', chunks=None) as ds:
        ds.load()  # Load all data into memory, freeing file handles
        ds.to_netcdf(os.path.join(download_folder_er5_land, f'{year}.nc'))

    # Delete individual monthly files
    for f in files:
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")