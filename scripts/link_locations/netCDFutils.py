import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
import netCDF4
import numpy as np
import re
import pprint
import json
from shapely.geometry import Point


# Define Read GeoTIFFs to list
def getNetCDFList(netCDFdir):
    tiff_files = []
    for root, _, files in os.walk(netCDFdir):
        for file in files:
            if file.endswith('.nc'):
                tiff_files.append(os.path.join(root, file))
    return tiff_files

# Define Read CSV of Subjects
def getsubj(subjectfile):
    df = gpd.read_file(subjectfile)
    df = df[(df['latitude'] != '') & (df['longitude'] != '')]
    # Create a GeoDataFrame with Point geometry from latitude and longitude columns
    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')  # Assuming WGS 84 coordinate reference system
    gdf = gdf[['subjectid', 'geometry']]
    return gdf
    

# Helper functions
# get idx in netCDF asset in acordance with geoLocation
def getIdx(lat, lon, fh, delta=None):
    # for later: keep attention that where is always a argin no matter how far away
    lat_d = np.abs(fh['latitude'][:] - lat)
    lon_d = np.abs(fh['longitude'][:] - lon)
    if not delta: # if no delta select the closest
        return [int(lat_d.argmin()), int(lon_d.argmin())]
    elif (lat_d.min() < delta) & (lon_d.min() <delta):
        return [int(lat_d.argmin()), int(lon_d.argmin())]
    else:
        #print('no data for this location')
        return([np.inf, np.inf])


def convert_numpy_types(obj):
    """Recursively convert NumPy data types to native Python types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert arrays to lists
    elif isinstance(obj, np.generic):
        return obj.item()  # Convert NumPy scalars (float32, int64, etc.)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}  # Convert dict
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]  # Convert lists
    return obj  # Return normal types unchanged


def netCDF_Link(subjects, netCDFList, pntcoord):

    dataOI = {}

    # Extract coords from DataFrame only once
    subject_ids = subjects["subjectid"].values
    lats = subjects[pntcoord].apply(lambda p: p.y).values
    lons = subjects[pntcoord].apply(lambda p: p.x).values

    for idx_asset, asset in enumerate(netCDFList):
        ds = xr.open_dataset(asset)
        dOI = {}

        # Compute delta (grid spacing)
        delta = float(ds.longitude[1] - ds.longitude[0])

        # Vectorized lat/lon to index conversion
        lat0 = float(ds.latitude[0])
        lon0 = float(ds.longitude[0])

        lat_idx = np.floor((lats - lat0) / delta).astype(int)
        lon_idx = np.floor((lons - lon0) / delta).astype(int)

        # Build subject grouping by grid cell
        locIDSubID = {}
        for sid, xi, yi in zip(subject_ids, lat_idx, lon_idx):
            if np.isinf(xi) or np.isinf(yi):
                continue
            key = f"{xi},{yi}"
            locIDSubID.setdefault(key, []).append(sid)

        # Select variables (skip coordinates)
        variablesOI = {
            name: var.dims
            for name, var in ds.variables.items()
            if name not in ['longitude', 'latitude', 'valid_time', 'crs', 'time']
        }

        # Process each variable
        for name, dims in variablesOI.items():

            # Load entire variable once = huge speedup
            var = ds[name].load()
            data = var.data  # NumPy array

            ddOI = {}
            for key in locIDSubID:
                x, y = map(int, key.split(','))
                
                # dimension dispatch
                if dims == ("lat", "lon"):
                    ddOI[key] = [data[x, y].item()]

                elif dims == ("days", "lat", "lon"):
                    ddOI[key] = data[:, x, y].tolist()

                elif dims == ("days", "hours", "lat", "lon"):
                    ddOI[key] = data[:, :, x, y].reshape(-1).tolist()

                elif dims == ("lat", "lon", "days"):
                    ddOI[key] = data[x, y, :].tolist()

                elif dims == ("months", "lat", "lon"):
                    ddOI[key] = data[:, x, y].tolist()

                elif dims == ("valid_time", "latitude", "longitude"):
                    ddOI[key] = data[:, x, y].tolist()
                elif dims == ('valid_time', 'model_level', 'latitude', 'longitude'):
                    ddOI[key] = data[:, :, x, y].reshape(-1).tolist()
                elif dims == ('model_level',):
                    ddOI[key] = 'nan'
                else:
                    # Generic fallback using xarray
                    ddOI[key] = var.isel(lat=x, lon=y).values.tolist()

            dOI[name] = ddOI

        # Add subject → grid mapping
        tmp = str(asset)
        dataOI[tmp] = dOI
        dataOI[tmp]["subjects"] = locIDSubID

        if (idx_asset + 1) % 50 == 0:
            print(f"{idx_asset+1} > {(idx_asset+1)/len(netCDFList)*100:.1f}% : {asset}")

        ds.close()

    # Convert numpy types so json.dumps won't fail
    return json.dumps(convert_numpy_types(dataOI), indent=4)

