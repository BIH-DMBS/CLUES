from pathlib import Path
import pandas as pd
import os
from shapely.geometry import mapping
import rasterio

def link_area_geoTIFFs(folderOI, gdf_areas, result_folder):
    folderOI = Path(folderOI)
    tiffList = folderOI.glob('**/*.tif')
    for tif in tiffList:
        filename = str(tif).split('/')[-1].replace('.tif', '')
        print(filename)  
        if os.path.exists(result_folder + filename + '.csv.gz'):
            print('result already exists ' + result_folder + filename + '.csv.gz')
        else:
            with rasterio.open(tif) as src:
                values_list = []
                i = 0
                a = 0
                x = 0
                for geom in gdf_areas.geometry:
                    geom_mapping = [mapping(geom)]  # mask expects a list of GeoJSON-like geometries
                    try:
                        out_image, _ = mask(src, geom_mapping, crop=True)
                        band1 = out_image[0]  # First band
                        flattened = band1.flatten()
                        values_list.append(flattened)
                    except Exception as e:
                        # Handle geometry outside raster or other errors
                        values_list.append(None)
                        print(f"Warning: Geometry failed - {e}")
                        x = x+1
                        print(x)
                    i = i+1

                    percent = 100 * i // len(gdf_areas.geometry)
                    if percent % 2 == 0: 
                        if percent > a:
                            a = percent
                            print(f"{percent}% complete")
            gdf = gdf_areas
            gdf["values"] = values_list
            print(filename)
            gdf.to_csv(result_folder + 'tiff_' + filename + '.csv.gz', compression='gzip', index=False)


folderOI = 'C:/code/DEGDB/degdb_utils/data/WordSettlementFootprint'

# Define pkl file path
pkl_file = 'dummy_areas.pkl'
gdf_areas = pd.read_pickle(pkl_file)
print(gdf_areas)
result_folder = 'results/'

link_area_geoTIFFs(folderOI, gdf_areas, result_folder)