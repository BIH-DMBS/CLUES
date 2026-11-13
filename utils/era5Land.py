import calendar
import os
import shutil
from time import sleep

import cdsapi
import netCDF4
import numpy as np
import xarray as xr
import yaml

import utils

try:
    from .config import download_folder, tmp_folder, secrets_folder
except ImportError:
    from config import download_folder, tmp_folder, secrets_folder


# ERA5-Land hourly data from the Climate Data Store (CDS).
#
# A request to the CDS for this data set waits a long time in the queue (about 20 minutes and more),
# and the waiting time does not depend much on the size of the request. Therefore one variable is
# requested for a complete year at once. This is only possible in the GRIB format (the size limit
# of the CDS is reached with half a year in the netCDF format). The GRIB file is converted to a
# netCDF file with the dimensions (valid_time, latitude, longitude), day by day, so that also a
# large area does not have to fit into memory.
#
# In the GRIB file the hours are stored per forecast day: 'time' is the day and 'step' the hours
# 1 to 24 after 00 UTC of that day. Hour 00 UTC of a day is therefore step 24 of the day before.

DATASET = "reanalysis-era5-land"
EPOCH = np.datetime64("1970-01-01T00:00:00")


def hours_of_year(year):
    return (366 if calendar.isleap(int(year)) else 365) * 24


def retrieve_with_retries(client, request, target, attempts=3, pause=60):
    for attempt in range(1, attempts + 1):
        try:
            client.retrieve(DATASET, request, target)
            return
        except Exception as e:
            print(f"Download try {attempt}/{attempts} failed: {e}")
            if os.path.exists(target):
                os.remove(target)
            if attempt == attempts:
                raise
            sleep(pause)


def grib_dataset_to_netcdf(ds, year, target):
    """
    Write the hours of `year` of a data set read from an ERA5-Land GRIB file to a netCDF file with
    the dimensions (valid_time, latitude, longitude).

    ds: data set as opened with xarray and the cfgrib engine, with exactly one data variable with the
        dimensions (time, step, latitude, longitude) or (time, latitude, longitude)
    Returns the number of hours written. Raises an error if hours are missing inside the range of
    hours that was delivered, or if an hour is delivered twice.
    """
    data_vars = list(ds.data_vars)
    if len(data_vars) != 1:
        raise ValueError(f"Expected exactly 1 data variable, found: {data_vars}")
    var_name = data_vars[0]
    variable = ds[var_name]
    if variable.dims not in (("time", "step", "latitude", "longitude"), ("time", "latitude", "longitude")):
        raise ValueError(f"Unexpected dimensions of {var_name}: {variable.dims}")
    has_step = "step" in variable.dims
    times = np.atleast_1d(ds["time"].values).astype("datetime64[ns]")
    steps = np.atleast_1d(ds["step"].values).astype("timedelta64[ns]") if has_step else np.array([0], dtype="timedelta64[ns]")
    year_start = np.datetime64(f"{int(year)}-01-01T00:00:00")
    year_end = np.datetime64(f"{int(year) + 1}-01-01T00:00:00")

    with netCDF4.Dataset(target, "w", format="NETCDF4") as nc:
        nc.createDimension("valid_time", None)
        nc.createDimension("latitude", ds.sizes["latitude"])
        nc.createDimension("longitude", ds.sizes["longitude"])
        nc_time = nc.createVariable("valid_time", "i8", ("valid_time",))
        nc_time.standard_name = "time"
        nc_time.units = "seconds since 1970-01-01"
        nc_time.calendar = "proleptic_gregorian"
        nc_lat = nc.createVariable("latitude", "f8", ("latitude",))
        nc_lat.standard_name = "latitude"
        nc_lat.units = "degrees_north"
        nc_lat[:] = ds["latitude"].values
        nc_lon = nc.createVariable("longitude", "f8", ("longitude",))
        nc_lon.standard_name = "longitude"
        nc_lon.units = "degrees_east"
        nc_lon[:] = ds["longitude"].values
        nc_var = nc.createVariable(var_name, "f4", ("valid_time", "latitude", "longitude"), zlib=True, complevel=4,
                                   fill_value=np.float32(np.nan),
                                   chunksizes=(24, ds.sizes["latitude"], ds.sizes["longitude"]))
        nc_var.long_name = variable.attrs.get("long_name", var_name)
        nc_var.units = variable.attrs.get("units", "")
        nc.source = "ERA5-Land hourly data, Copernicus Climate Change Service (C3S) Climate Data Store"

        written = 0
        last_valid_time = None
        # one forecast day (24 hours) at a time
        for i, day in enumerate(times):
            block = variable.isel(time=i).values
            if not has_step:
                block = block[np.newaxis, ...]
            valid_times = day + steps
            # an hour is there if it has a value somewhere (hours outside of the request are empty)
            keep = (valid_times >= year_start) & (valid_times < year_end) & np.isfinite(block).any(axis=(1, 2))
            if not keep.any():
                continue
            valid_times, block = valid_times[keep], block[keep]
            if last_valid_time is not None and valid_times[0] <= last_valid_time:
                raise RuntimeError(f"The hours of {var_name} are not in order or delivered twice at {valid_times[0]}")
            if not (np.diff(valid_times) > np.timedelta64(0, "s")).all():
                raise RuntimeError(f"The hours of {var_name} are not in order within the day {day}")
            last_valid_time = valid_times[-1]
            n = len(valid_times)
            nc_time[written:written + n] = ((valid_times - EPOCH) / np.timedelta64(1, "s")).astype("int64")
            nc_var[written:written + n, :, :] = block.astype("float32")
            written += n

        if written == 0:
            raise RuntimeError(f"No data of the year {year} in the GRIB file")
        first, last = nc_time[0], nc_time[written - 1]
        if int(last - first) // 3600 + 1 != written:
            raise RuntimeError(f"Hours are missing in {var_name} {year}: {written} hours between the first and the last "
                               f"hour, {int(last - first) // 3600 + 1} expected")
    return written


def getEra5Land(json_file, year, vOI):
    # Errors are not caught here: a failed download must end the script with an error,
    # so that snakemake marks the job as failed.
    print(f"Getting ERA5 Land data for {json_file}, year {year}, variable {vOI}")
    parameters = utils.get_parameter(json_file, 'bbox.json')
    if parameters is None:
        raise RuntimeError(f"Could not read the configuration '{json_file}' (see message above)")
    if vOI not in [variable["name"] for variable in parameters["variables"]]:
        raise ValueError(f"Variable '{vOI}' is not listed in '{json_file}'")
    year = str(year)

    result_folder = os.path.join(download_folder, DATASET, vOI)
    file_path = os.path.join(result_folder, f'{year}.nc')
    os.makedirs(result_folder, exist_ok=True)
    if os.path.exists(file_path):
        print(f"The file {file_path} exists.")
        return

    with open(os.path.join(secrets_folder, 'cdsapirc_climate.sct'), 'r') as f:
        credentials = yaml.safe_load(f)
    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

    # widen the area by one grid step, see utils.pad_bbox
    area = utils.pad_bbox(parameters['bbox'], float(parameters.get('grid_resolution_deg', 0)))
    request = {
        "variable": [vOI],
        "year": year,
        "month": [f"{month:02d}" for month in range(1, 13)],
        "day": [f"{day:02d}" for day in range(1, 32)],
        "time": [f"{hour:02d}:00" for hour in range(24)],
        "data_format": "grib",
        "download_format": "unarchived",
        "area": area,
    }

    # the GRIB file and the helper files of the GRIB reader are kept in a temporary folder
    work_dir = os.path.join(tmp_folder, f"era5_land_{vOI}_{year}")
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir)
    part = file_path + '.part'
    try:
        grib_file = os.path.join(work_dir, f'{year}.grib')
        retrieve_with_retries(c, request, grib_file)

        ds = xr.open_dataset(grib_file, engine="cfgrib")
        try:
            n_hours = grib_dataset_to_netcdf(ds, year, part)
        finally:
            ds.close()
        if n_hours != hours_of_year(year):
            # happens for a year that is not completely published yet
            print(f"WARNING: {vOI} {year} has {n_hours} of {hours_of_year(year)} hours")
        os.replace(part, file_path)
        print(f"Saved {file_path} with {n_hours} hours")
    finally:
        if os.path.exists(part):
            os.remove(part)
        shutil.rmtree(work_dir, ignore_errors=True)
