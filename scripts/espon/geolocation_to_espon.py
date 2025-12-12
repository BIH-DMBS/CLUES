#!/usr/bin/env python

import os
import glob
import re
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point

def sanitize_filename(filename):
    # Replace each whitespace with an underscore
    filename = filename.replace(' ', '_')
    # Remove characters not allowed in file names
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename

result_folder = 'output_espon'
subject_path = 'GeoLocation.csv'
folder_path = 'espon'

os.system("mkdir -p %s" % result_folder)

sub_df = pd.read_csv(subject_path)
sub_df['geometry'] = [Point(xy) for xy in zip(sub_df['longitude'], sub_df['latitude'])]
sub_df = gpd.GeoDataFrame(sub_df, geometry='geometry')
sub_df = sub_df.drop(['latitude','longitude'],axis = 1)
sub_df.set_crs(epsg=4326, inplace=True)

csv_files = glob.glob(os.path.join(folder_path, '**', '*.csv'), recursive=True)
espon_data_files = [file for file in csv_files if os.path.dirname(file) != folder_path]

# load geometries
geometries_path = os.path.join(folder_path, 'geometry.csv')
# Load the CSV file into a pandas DataFrame
gdf = pd.read_csv(geometries_path)

# Convert the 'geometry' column to actual geometrical data using shapely
gdf['geometry'] = gdf['geometry'].apply(wkt.loads)

# Convert the pandas DataFrame to a GeoPandas GeoDataFrame
gdf = gpd.GeoDataFrame(gdf, geometry='geometry')

# Set the current coordinate reference system (CRS)
gdf.set_crs(epsg=4326, inplace=True)

for c, csv in enumerate(espon_data_files):
    try:
        # load dataOI
        df = pd.read_csv(csv)
        # Merging data and geometries on the 'tunit_code' column
        data_gdf = pd.merge(gdf, df, on='tunit_code')
        # Select columns to keep
        columns_to_keep = ['PSC2','name','level'] + [col for col in data_gdf.columns if col.startswith('y_')]
        joined_gdf = gpd.sjoin(sub_df, data_gdf, how='inner', predicate='within')
        joined_gdf = joined_gdf[columns_to_keep]
        csv_file_name = joined_gdf.iloc[0, joined_gdf.columns.get_loc('name')]
        csv_file_name = os.path.join(result_folder, sanitize_filename(csv_file_name)+'.csv')
        joined_gdf.to_csv(csv_file_name, index=False)
        print('saved: ' + csv_file_name)
    except:
        print('no result table or empty raw data file')
        print(csv)
    if c % 100 == 0:
        print(c)

