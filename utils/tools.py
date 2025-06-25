
import netCDF4 as nc
import numpy as np
import os
import rasterio
import rioxarray
import xarray as xr


def netCDF2GeoTiff(source, variable, year):
    # netCDF -> geoTIFF... not used 
    file = os.path.join(download_foldern, source, variable, str(year)+'.nc')
    ds = xr.open_dataset(file)
    # Get the variable name in the file
    var_name_in_file = list(ds.data_vars)[0]

    # Select the variable and convert to a rioxarray object
    data_var = ds[var_name_in_file].rio.set_spatial_dims(x_dim='latitude', y_dim='latitude')
    # Set the CRS (coordinate reference system) if not already set
    data_var = data_var.rio.write_crs("EPSG:4326")

    # Prepare the metadata for the output file
    n_times = len(data_var.time)
    transform = from_origin(data_var.longitude.min(), data_var.latitude.max(), data_var.longitude[1] - data_var.longitude[0], data_var.latitude[1] - data_var.latitude[0])
    meta = {
        'driver': 'GTiff',
        'count': n_times,
        'dtype': 'float32',
        'width': data_var.sizes['longitude'],
        'height': data_var.sizes['latitude'],
        'crs': 'EPSG:4326',
        'transform': transform
    }
    # Define the output file name
    output_file = os.path.join(wd, 'data', source, variable, str(year)+'.tif')

    # Write the data to a single GeoTIFF file
    with rasterio.open(output_file, 'w', **meta) as dst:
        for i in range(n_times):
            # Select data for the current time step
            data = data_var.isel(time=i).values
            # Get the name for the current time step
            time_value = data_var.time[i].values.astype('datetime64[ms]').astype('O')  # Convert to Python datetime object
            name = time_value.strftime('%Y-%m-%d_%H:%M:%S')  # Format the datetime object
            # Write the data to the corresponding band in the GeoTIFF file
            dst.write(data, i + 1)
            # Set the band name
            dst.set_band_description(i + 1, name)

    print(f"Saved {output_file}")

