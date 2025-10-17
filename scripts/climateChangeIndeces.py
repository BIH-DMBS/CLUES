import numpy as np
import pandas as pd
from netCDF4 import Dataset, date2num
import glob
import os
import operator

"""
This script processes sub-daily temperature data from NetCDF files to compute various climate indices.
It includes functions to read data, compute reference percentiles, yearly extremes, special days, monthly statistics,
and spell duration indices. The results are saved back to NetCDF files.

to change the parameters, modify the folder_path, ref_start, ref_end, and result_folder variables in the main script section.
"""

def save_to_netcdf(filename, dataOI, valid_time, latitude, longitude, var_name="dataOI", var_units="Kelvin"):
    """
    Save a 3D dataset to NetCDF format using netCDF4.

    Parameters
    ----------
    filename : str
        Path to the output NetCDF file.
    dataOI : np.ndarray
        3D data array of shape (time, lat, lon)
    valid_time : array-like
        1D array of times corresponding to the first dimension of dataOI
        Can be datetime objects or pandas Timestamps
    latitude : array-like
        1D array of latitude values
    longitude : array-like
        1D array of longitude values
    var_name : str
        Name of the variable to store in NetCDF
    var_units : str
        Units of the variable
    """
    
    # Open NetCDF file for writing
    ncfile = Dataset(filename, mode='w', format='NETCDF4')
    
    # Create dimensions
    ncfile.createDimension('time', len(valid_time))
    ncfile.createDimension('lat', len(latitude))
    ncfile.createDimension('lon', len(longitude))
    
    # Create coordinate variables
    times = ncfile.createVariable('time', 'f8', ('time',))
    lats = ncfile.createVariable('lat', 'f4', ('lat',))
    lons = ncfile.createVariable('lon', 'f4', ('lon',))
    
    # Assign coordinate data
    lats[:] = latitude
    lons[:] = longitude
    
    # Convert valid_time to numeric time (days since 2000-01-01)
    times.units = "days since 2000-01-01 00:00:00"
    times.calendar = "standard"
    times[:] = date2num(pd.to_datetime(valid_time).to_pydatetime(), units=times.units, calendar=times.calendar)
    
    # Create the main variable
    var = ncfile.createVariable(var_name, 'f4', ('time', 'lat', 'lon'), zlib=True)
    var.units = var_units
    var.long_name = var_name
    var[:, :, :] = dataOI
    
    # Close the NetCDF file
    ncfile.close()
    
    print(f"Data saved to {filename}")


def getDataOI(folder_path):
    # Example: get all .nc files in a folder
    nc_files = sorted(glob.glob(f"{folder_path}/*.nc"))

    t2m = None  # Initialize
    t = None

    for f in nc_files:
        with Dataset(f, 'r') as nc:
            data = nc.variables['d2m'][:]   # Read variable as numpy array
            time_data = nc.variables['valid_time'][:]   # Read variable as numpy array
            if t2m is None:
                t2m = data
                t = time_data
                latitude = nc.variables['latitude'][:]
                longitude = nc.variables['longitude'][:]
            else:
                t2m = np.concatenate([t2m, data], axis=0)
                t = np.concatenate([t, time_data], axis=0)
    return t2m, t, latitude, longitude


import numpy as np
import pandas as pd

def get_reference(tempData, resolution_in_h, start_date, end_date):
    """
    Compute the calendar-day 10th and 90th percentiles of daily min/max temperature
    using a 5-day centered window within a reference period.

    Parameters
    ----------
    tempData : np.ndarray
        Temperature data of shape (hours, lat, lon)
    resolution_in_h : int
        Temporal resolution of the input data in hours
    start_date : str
        Start date of the reference period (format 'YYYY-MM-DD HH:MM:SS')
    end_date : str
        End date of the reference period (format 'YYYY-MM-DD HH:MM:SS')

    Returns
    -------
    TNin10, TNin90, TXin10, TXin90 : np.ndarray
        Arrays of shape (366, lat, lon) containing the calendar day
        10th and 90th percentiles of daily minima and maxima
    day_vector : np.ndarray of datetime64
        Array of length 366 with datetime objects for each calendar day in the reference period year
    """
    hours, nlat, nlon = tempData.shape
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Create hourly time index for the entire dataset
    time_index = pd.date_range(start=start, end=end, freq=f'{resolution_in_h}h')
    
    # Flatten spatial dimensions for vectorized processing
    flat_data = tempData.reshape(hours, nlat * nlon)
    df = pd.DataFrame(flat_data, index=pd.date_range(start=pd.to_datetime(start_date), periods=hours, freq=f'{resolution_in_h}h'))

    # Restrict to reference period
    df = df.loc[(df.index >= start) & (df.index <= end)]

    # Compute daily min and max
    daily_min = df.resample('D').min()
    daily_max = df.resample('D').max()

    # Initialize output arrays
    TNin10 = np.zeros((366, nlat * nlon))
    TNin90 = np.zeros((366, nlat * nlon))
    TXin10 = np.zeros((366, nlat * nlon))
    TXin90 = np.zeros((366, nlat * nlon))

    # Compute percentiles for each day of the year using 5-day centered window
    for day in range(1, 367):  # 1 to 366
        window_days = [(day + i - 3) % 366 + 1 for i in range(5)]  # centered window with wrap-around

        mask = daily_min.index.dayofyear.isin(window_days)
        Tmin_window = daily_min[mask]
        Tmax_window = daily_max[mask]

        if len(Tmin_window) > 0:
            TNin10[day - 1, :] = np.percentile(Tmin_window.values, 10, axis=0)
            TNin90[day - 1, :] = np.percentile(Tmin_window.values, 90, axis=0)
            TXin10[day - 1, :] = np.percentile(Tmax_window.values, 10, axis=0)
            TXin90[day - 1, :] = np.percentile(Tmax_window.values, 90, axis=0)
        else:
            TNin10[day - 1, :] = np.nan
            TNin90[day - 1, :] = np.nan
            TXin10[day - 1, :] = np.nan
            TXin90[day - 1, :] = np.nan

    # Reshape back to (366, lat, lon)
    TNin10 = TNin10.reshape(366, nlat, nlon)
    TNin90 = TNin90.reshape(366, nlat, nlon)
    TXin10 = TXin10.reshape(366, nlat, nlon)
    TXin90 = TXin90.reshape(366, nlat, nlon)

    # Create day vector with the reference start year
    year_ref = start.year
    day_vector = pd.date_range(f"{year_ref}-01-01", periods=366, freq="D").to_numpy()

    return TNin10, TNin90, TXin10, TXin90, day_vector



def compute_yearly_temperature_extremes(tempData, resolution_in_h, start_date,
                                        TNin10, TXin10, TNin90, TXin90):
    """
    Compute yearly TN10p, TX10p, TN90p, TX90p from sub-daily temperature data.

    Parameters
    ----------
    tempData : np.ndarray
        Sub-daily temperature data (hours, nlat, nlon)
    resolution_in_h : int
        Temporal resolution in hours
    start_date : str
        Start date of the time series (e.g., '1961-01-01 00:00:00')
    TNin10, TXin10, TNin90, TXin90 : np.ndarray
        Calendar-day percentiles (shape: 366, nlat, nlon)

    Returns
    -------
    TN10p_yearly, TX10p_yearly, TN90p_yearly, TX90p_yearly : np.ndarray
        Yearly percentage of extreme days (nyears, nlat, nlon)
    years : np.ndarray
        Array of years corresponding to the first dimension
    """
    hours, nlat, nlon = tempData.shape
    time_index = pd.date_range(start=start_date, periods=hours, freq=f'{resolution_in_h}h')

    # Flatten spatial dimensions
    flat_data = tempData.reshape(hours, nlat * nlon)
    df = pd.DataFrame(flat_data, index=time_index)

    # Compute daily min and max
    daily_min = df.resample('D').min()
    daily_max = df.resample('D').max()
    dates = daily_min.index
    doy = dates.dayofyear - 1  # 0-based

    daily_min = daily_min.values.reshape(len(dates), nlat, nlon)
    daily_max = daily_max.values.reshape(len(dates), nlat, nlon)

    # Get unique years
    years = np.unique(dates.year)
    nyears = len(years)

    # Initialize output arrays
    TN10p_yearly = np.zeros((nyears, nlat, nlon))
    TX10p_yearly = np.zeros((nyears, nlat, nlon))
    TN90p_yearly = np.zeros((nyears, nlat, nlon))
    TX90p_yearly = np.zeros((nyears, nlat, nlon))

    # Loop over years
    for y_idx, year in enumerate(years):
        mask = dates.year == year
        daily_min_year = daily_min[mask]
        daily_max_year = daily_max[mask]
        doy_year = doy[mask]

        # Compute boolean masks
        TN10_mask = np.array([daily_min_year[i] < TNin10[doy_year[i]] for i in range(len(doy_year))])
        TX10_mask = np.array([daily_max_year[i] < TXin10[doy_year[i]] for i in range(len(doy_year))])
        TN90_mask = np.array([daily_min_year[i] > TNin90[doy_year[i]] for i in range(len(doy_year))])
        TX90_mask = np.array([daily_max_year[i] > TXin90[doy_year[i]] for i in range(len(doy_year))])

        # Compute percentages for this year
        TN10p_yearly[y_idx] = 100 * TN10_mask.sum(axis=0) / len(doy_year)
        TX10p_yearly[y_idx] = 100 * TX10_mask.sum(axis=0) / len(doy_year)
        TN90p_yearly[y_idx] = 100 * TN90_mask.sum(axis=0) / len(doy_year)
        TX90p_yearly[y_idx] = 100 * TX90_mask.sum(axis=0) / len(doy_year)
    
    years = pd.to_datetime([f"{y}-01-01" for y in years])
    return TN10p_yearly, TX10p_yearly, TN90p_yearly, TX90p_yearly, years


def number_of_special_days(tempData, resolution_in_h, start_date, stat = 'min', relation_operator='<', threshold=273.15):
    """
    Compute number of frost days (daily min < 0°C) per year per grid cell.

    Parameters
    ----------
    tempData : np.ndarray
        3D array of temperature data with shape (hours, nlat, nlon)
    resolution_in_h : int
        Time step in hours between consecutive data points
    start_date : str or pd.Timestamp
        Start date of the time series

    Returns
    -------
    fd : np.ndarray
        3D array (nyears, nlat, nlon) = frost days per year per grid cell
    """

    ops = {
        '<': operator.lt,
        '>': operator.gt
    }
    if relation_operator not in ops:
        raise ValueError("Operator must be '<' or '>'")
        
    hours, nlat, nlon = tempData.shape
    start = pd.to_datetime(start_date)
    time_index = pd.date_range(start=start, periods=hours, freq=f'{resolution_in_h}h')

    # Flatten spatial dimensions for vectorized resampling
    df = pd.DataFrame(tempData.reshape(hours, -1), index=time_index)

    # Compute daily minima
    if stat == 'min':
        daily_m = df.resample('D').min()
    else:
        daily_m = df.resample('D').max()
    daily_m['year'] = daily_m.index.year

    # Group by year and count frost days (min temp < 0°C)
    oi_days_per_year = daily_m.groupby('year').apply(lambda x: ( ops[relation_operator](x.iloc[:, :-1],threshold)).sum())

    # Convert to numpy and reshape
    return oi_days_per_year.to_numpy().reshape(-1, nlat, nlon)


def monthly_temp_stats(tempData, resolution_in_h, start_date):
    """
    Compute monthly temperature statistics from sub-daily data.

    Parameters
    ----------
    tempData : np.ndarray
        3D array (time, nlat, nlon)
    resolution_in_h : int
        Temporal resolution in hours
    start_date : str
        Start date of the time series

    Returns
    -------
    monthly_max : np.ndarray
        Monthly maximum temperature (months, nlat, nlon)
    monthly_max_daily_min : np.ndarray
        Monthly maximum of daily minima (months, nlat, nlon)
    monthly_min : np.ndarray
        Monthly minimum temperature (months, nlat, nlon)
    monthly_min_daily_max : np.ndarray
        Monthly minimum of daily maxima (months, nlat, nlon)
    month_vector : np.ndarray of datetime64
        Vector of representative dates for each month (first day of month)
    """
    hours, nlat, nlon = tempData.shape
    time_index = pd.date_range(start=start_date, periods=hours, freq=f'{resolution_in_h}h')

    # Flatten spatial dimensions for vectorized processing
    df = pd.DataFrame(tempData.reshape(hours, -1), index=time_index)

    # --- Daily min and max ---
    daily_min = df.resample('D').min()
    daily_max = df.resample('D').max()

    # --- Monthly max and min of all data ---
    monthly_max = df.resample('MS').max().to_numpy().reshape(-1, nlat, nlon)
    monthly_min = df.resample('MS').min().to_numpy().reshape(-1, nlat, nlon)

    # --- Monthly max of daily minima ---
    monthly_max_daily_min = daily_min.resample('MS').max().to_numpy().reshape(-1, nlat, nlon)
    # --- Monthly min of daily maxima ---
    monthly_min_daily_max = daily_max.resample('MS').min().to_numpy().reshape(-1, nlat, nlon)

    # --- Month vector: first day of each month ---
    month_vector = df.resample('MS').mean().index.to_numpy()

    return monthly_max, monthly_max_daily_min, monthly_min, monthly_min_daily_max, month_vector


def compute_spell_duration_indices(tempData, resolution_in_h, start_date,
                                   TNin10, TXin90, min_duration=6):
    """
    Compute WSDI and CSDI from sub-daily temperature data (per year).

    Parameters
    ----------
    tempData : np.ndarray
        Sub-daily temperature data (hours, nlat, nlon)
    resolution_in_h : int
        Temporal resolution in hours
    start_date : str
        Start date of the time series
    TNin10 : np.ndarray
        Calendar-day 10th percentile of daily minima (366, nlat, nlon)
    TXin90 : np.ndarray
        Calendar-day 90th percentile of daily maxima (366, nlat, nlon)
    min_duration : int
        Minimum consecutive days for a spell (default 6)

    Returns
    -------
    WSDI_yearly, CSDI_yearly : np.ndarray
        Annual warm and cold spell duration indices (nyears, nlat, nlon)
    years : np.ndarray
        Array of years corresponding to the first dimension
    """
    hours, nlat, nlon = tempData.shape
    time_index = pd.date_range(start=start_date, periods=hours, freq=f'{resolution_in_h}h')

    # Flatten spatial dimensions
    flat_data = tempData.reshape(hours, nlat * nlon)
    df = pd.DataFrame(flat_data, index=time_index)

    # Compute daily min and max
    daily_min = df.resample('D').min()
    daily_max = df.resample('D').max()
    dates = daily_min.index
    doy = dates.dayofyear - 1  # 0-based

    daily_min = daily_min.values.reshape(len(dates), nlat * nlon)
    daily_max = daily_max.values.reshape(len(dates), nlat * nlon)

    # Flatten percentile references
    TXin90_flat = TXin90.reshape(366, -1)
    TNin10_flat = TNin10.reshape(366, -1)

    # Get unique years
    years = np.unique(dates.year)
    nyears = len(years)

    # Initialize output arrays
    WSDI_yearly = np.zeros((nyears, nlat, nlon))
    CSDI_yearly = np.zeros((nyears, nlat, nlon))

    # Function to count days in consecutive sequences >= min_duration
    def count_consecutive_days(mask, min_len):
        total = np.zeros(mask.shape[1], dtype=int)
        for idx in range(mask.shape[1]):  # loop over flattened spatial dimension
            arr = mask[:, idx]
            count = 0
            i = 0
            while i < len(arr):
                if arr[i]:
                    run = 0
                    while i < len(arr) and arr[i]:
                        run += 1
                        i += 1
                    if run >= min_len:
                        count += run
                else:
                    i += 1
            total[idx] = count
        return total

    # Loop over years
    for y_idx, year in enumerate(years):
        mask = dates.year == year
        daily_max_year = daily_max[mask]
        daily_min_year = daily_min[mask]
        doy_year = doy[mask]

        # Boolean masks
        ws_mask = np.array([daily_max_year[i] > TXin90_flat[doy_year[i]] for i in range(len(doy_year))])
        cs_mask = np.array([daily_min_year[i] < TNin10_flat[doy_year[i]] for i in range(len(doy_year))])

        # Count consecutive sequences
        WSDI_yearly[y_idx] = count_consecutive_days(ws_mask, min_duration).reshape(nlat, nlon)
        CSDI_yearly[y_idx] = count_consecutive_days(cs_mask, min_duration).reshape(nlat, nlon)

    years = pd.to_datetime([f"{y}-01-01" for y in years])
    return WSDI_yearly, CSDI_yearly, years

###################################################

# Main script
folder_path = "C:\\code\\CLUES\data\\reanalysis-era5-single-levels\\2m_dewpoint_temperature"
ref_start = '2000-01-01 00:00:00'
ref_end = '2019-12-31 23:00:00'

result_folder = "C:\\code\\CLUES\\data\\climate_indices\\"
# Check if folder exists, if not, create it
if not os.path.exists(result_folder):
    os.makedirs(result_folder)

[t2m, t, latitude, longitude] = getDataOI(folder_path)
t = pd.to_datetime(t, unit='s', origin='1970-01-01')
data_start_date = t[0].strftime('%Y-%m-%d %H:%M:%S')
resolution_in_h = (t[1] - t[0]) / pd.Timedelta(hours=1)

[TNin10, TNin90, TXin10, TXin90, time_index] = get_reference(t2m, resolution_in_h, ref_start, ref_end)

save_to_netcdf(result_folder + "TNin10.nc", TNin10, time_index, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "TNin90.nc", TNin90, time_index, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "TXin10.nc", TXin10, time_index, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "TXin90.nc", TXin90, time_index, latitude, longitude, var_name="t2m", var_units="Kelvin")


[TN10p, TX10p, TN90p, TX90p, years] = compute_yearly_temperature_extremes(t2m, resolution_in_h, data_start_date, TNin10, TXin10, TNin90, TXin90)
save_to_netcdf(result_folder + "TN10p.nc", TN10p, years, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "TX10p.nc", TX10p, years, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "TN90p.nc", TN90p, years, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "TX90p.nc", TX90p, years, latitude, longitude, var_name="t2m", var_units="Kelvin")


fd = number_of_special_days(t2m, resolution_in_h, data_start_date,'min','<', 273.15) #frost days
su = number_of_special_days(t2m, resolution_in_h, data_start_date,'max','>', 290)#298.15) # hot days
ice_d = number_of_special_days(t2m, resolution_in_h, data_start_date,'max','<', 273.15)# # icing days
tn = number_of_special_days(t2m, resolution_in_h, data_start_date,'min','>', 290)# # tropical nights
save_to_netcdf(result_folder + "fd.nc", fd, years, latitude, longitude, var_name="days_per_year", var_units="days")
save_to_netcdf(result_folder + "su.nc", su, years, latitude, longitude, var_name="days_per_year", var_units="days")
save_to_netcdf(result_folder + "id.nc", ice_d, years, latitude, longitude, var_name="days_per_year", var_units="days")
save_to_netcdf(result_folder + "tn.nc", tn, years, latitude, longitude, var_name="days_per_year", var_units="days")


[monthly_max, monthly_max_daily_min, monthly_min, monthly_min_daily_max, month_vector] = monthly_temp_stats(t2m, resolution_in_h, data_start_date)
save_to_netcdf(result_folder + "monthly_max.nc", monthly_max, month_vector, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "monthly_max_daily_min.nc", monthly_max_daily_min, month_vector, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "monthly_min.nc", monthly_min, month_vector, latitude, longitude, var_name="t2m", var_units="Kelvin")
save_to_netcdf(result_folder + "monthly_min_daily_max.nc", monthly_min_daily_max, month_vector, latitude, longitude, var_name="t2m", var_units="Kelvin")


[WSDI_yearly, CSDI_yearly, years] = compute_spell_duration_indices(t2m, resolution_in_h, data_start_date, TNin10, TXin90, 6)
save_to_netcdf(result_folder + "WSDI_yearly.nc", WSDI_yearly, years, latitude, longitude, var_name="days", var_units="days")
save_to_netcdf(result_folder + "CSDI_yearly.nc", CSDI_yearly, years, latitude, longitude, var_name="days", var_units="days")

###################################################