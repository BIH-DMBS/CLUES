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
    z = 0
    dataOI = {} # -> container for all results
    for asset in netCDFList:
        dOI = {} # -> asset results
        fh = netCDF4.Dataset(asset, mode = "r")
        #fh = netCDF4.Dataset(netCDFList[asset], mode = "r")
        
        # the grit has to be equidistant in degree
        delta = fh.variables['longitude'][1]-fh.variables['longitude'][0]

        # create mapping of subjects that fall into same area in the grid
        # {'locID1':['subID1',...'subID3'], ..., 'locIDn':['subIDn',...'subIDn']}
        locIDSubID = {}
        for i, row in subjects.iterrows():
            lon = row[pntcoord].x
            lat = row[pntcoord].y
            idx = getIdx(lat, lon, fh, delta)
            key = str(idx[0])+','+str(idx[1])
            if key in locIDSubID:
                locIDSubID[key].append(row['subjectid'])
            else:
                locIDSubID[key] = [row['subjectid']]

        variablesOI = {var_name:var.dimensions for var_name, var in fh.variables.items() if var_name not in ['longitude','latitude','valid_time','crs','time']}
        for name, value in variablesOI.items():
            # extract thetime series fof each position there we have a subject
            # {'locID1':['t1',...'tn'], ..., 'locIDn':['t1',...'tn']}
            ddOI = {}
            for k in locIDSubID:
                split_string = k.split(',')
                if(split_string[0]=='inf'):
                    dOI[k]='nan'
                else:
                    x = int(split_string[0])
                    y = int(split_string[1])
                    if value == ('lat', 'lon'):
                        ddOI[k] = [fh.variables[name][x,y].item()]
                    elif value == ('days', 'lat', 'lon'): 
                        ddOI[k] = fh.variables[name][:,x,y]
                    elif value == ('days', 'hours', 'lat', 'lon'):
                        series = fh.variables[name][:,:,x,y]
                        ddOI[k] = [num for row in series for num in row]
                    elif value == ('lat', 'lon', 'days'):
                        ddOI[k] = fh.variables[name][x,y,:]
                    elif value == ('months', 'lat', 'lon'):
                        ddOI[k] = fh.variables[name][:,x,y]
                    elif value == ('valid_time', 'latitude', 'longitude'): 
                        ddOI[k] = fh.variables[name][:,x,y]
                    #elif value == ('time', 'latitude', 'longitude'):
                    #    ddOI[k] = fh.variables[name][:,x,y]
                    try:
                        if not isinstance(ddOI[k],list):
                            if isinstance(ddOI[k].mask,np.ndarray):
                                ddOI[k] = [item if not ddOI[k].mask[index] else None for index, item in enumerate(ddOI[k])]
                            else:
                                ddOI[k] = ddOI[k].tolist()
                    except:
                        print('##############')
                        print(asset)
                        print(value)
                        print(name)
                        print(k)
                        ddOI[k] = []
            dOI[name] = ddOI
        dataOI[asset] = dOI
        dataOI[asset]['subjects'] = locIDSubID
        z = z+1
        if z%50==0:
            print(str(z) + ' > '+ str(z/len(netCDFList)*100)+'% : ' + str(asset))
    return(json.dumps(convert_numpy_types(dataOI), indent=4))

