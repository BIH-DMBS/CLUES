import cdsapi
import os
import yaml
import zipfile
import xarray as xr
import glob
import yaml
import json

import utils
import numpy as np
from pathlib import Path
import shutil

try:
    from .config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder
except:
    from config import download_folder, configs_assets_folder, tmp_folder, area, config_folder, secrets_folder


def getEra5Land(json_file, year, vOI):

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
        parameters = utils.get_bbox('bbox.json')
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

        file_path = os.path.join(tmp_folder, f'{month}.grib')
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
                "data_format": "grib",
                "download_format": "zip",
                "area": parameters['bbox']
            }
            try:
                c.retrieve(dataset, request, file_path_zip)
                print("Data is available for this month.")
                # Open the zip file
                with zipfile.ZipFile(file_path_zip, 'r') as z:
                    # List contents (usually there should be one .nc file)
                    namelist = z.namelist()
                    print("Files in zip:", namelist)

                    # Extract the first .grib file and save as file_path
                    for name in namelist:
                        if name.endswith('.grib'):
                            with z.open(name) as src, open(file_path, 'wb') as dst:
                                dst.write(src.read())
                            print(f"Saved {name} as {file_path}")
                            break
                    # Delete the zip file after successful extraction
                os.remove(file_path_zip)
            except Exception as e:
                print("Data is NOT available:", e)


    # raw grib file to monthly netcdf file 
    files = sorted(glob.glob(tmp_folder + "/*.grib"))
    # anchor for time conversion
    epoch = np.datetime64("1970-01-01T00:00:00")
    for f in files:
        ds = xr.open_dataset(f, engine="cfgrib")
        mnth = Path(f).stem            # e.g. "01", "02", ..., "12"
        target_month = int(mnth)

        # 1️. get the variable of interest (skip coords)
        data_vars = [v for v in ds.data_vars]
        if len(data_vars) != 1:
            raise ValueError(f"Expected exactly 1 data variable in {f}, found: {data_vars}")
        var_name = data_vars[0]

        var_units = ds[var_name].attrs.get("units", "")
        var_long_name = ds[var_name].attrs.get("long_name", var_name)

        # 2️. extract raw data
        x = ds[var_name].values  # (time, step, lat, lon)

        # 3️. flatten first two dimensions into hours
        x_flat = x.reshape(-1, x.shape[2], x.shape[3])

        # 4️. compute valid_time for each hour
        valid_time_dt = ds.time.values[:, None] + ds.step.values[None, :]
        valid_time_flat = valid_time_dt.ravel()
        valid_time_int = ((valid_time_flat - epoch) / np.timedelta64(1, "s")).astype("int64")

        # 5. MONTH FILTER (using only mnth)
        valid_time_dt64 = epoch + valid_time_int.astype("timedelta64[s]")
        months = valid_time_dt64.astype("datetime64[M]")
        mask = (months.astype(int) % 12 + 1 == target_month)

        x_flat = x_flat[mask]
        valid_time_int = valid_time_int[mask]

        # 6. create new Dataset
        ds_new = xr.Dataset(
            data_vars={
                var_name: (["valid_time", "latitude", "longitude"], x_flat)
            },
            coords={
                "valid_time": ("valid_time", valid_time_int),
                "latitude": ("latitude", ds.latitude.values),
                "longitude": ("longitude", ds.longitude.values)
            }
        )

        # 7. CF attributes
        ds_new[var_name].attrs["long_name"] = var_long_name
        ds_new[var_name].attrs["units"] = var_units
        ds_new["valid_time"].attrs["standard_name"] = "time"
        ds_new["valid_time"].attrs["units"] = "seconds since 1970-01-01"
        ds_new["latitude"].attrs["standard_name"] = "latitude"
        ds_new["longitude"].attrs["standard_name"] = "longitude"

        # 8. write NetCDF
        ds_new.to_netcdf(Path(tmp_folder) / (mnth + ".nc"), engine="netcdf4")

        print(f"Saved {mnth}.nc with shape {ds_new[var_name].shape}")
        ds.close()

    files = sorted(glob.glob(tmp_folder + "/*.nc"))
    print(files)

    # Open without combining yet
    datasets = [xr.open_dataset(f) for f in files]

    # Concatenate along valid_time
    ds = xr.concat(datasets, dim="valid_time")

    # Sort by valid_time (guaranteed monotonic)
    ds = ds.sortby("valid_time")

    # Save final yearly NetCDF
    ds.to_netcdf(os.path.join(download_folder_er5_land, f'{year}.nc'))
    ds.close()

    # Close monthly datasets to free file handles
    for d in datasets:
        d.close()

    # remove temporary folder
    shutil.rmtree(tmp_folder)