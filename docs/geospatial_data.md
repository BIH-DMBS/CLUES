## Geospatial Data Sources sdhasjhaskjfh
This page describes the geospatial data sources and datasets integrated into the CLUES workflow. For each data source, a short description, source-specific configuration file (config), spatial and temporal resolution, download format and reference link are provided

### Copernicus Atmosphere Monitoring Service (CAMS) Global Reanalysis (EAC4)
- Description: Global atmospheric composition reanalysis implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 2003–present  
- Resolution: 0.75°×0.75°, 3-hourly  
- Format: NetCDF  
- Config: `cams-global-reanalysis-eac4.json`  
- [More Info](https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview)  

### Copernicus Climate Change Service (C3S) reanalysis-era5-single-levels
- Description: Global climate reanalysis (ERA5) implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 1940–present  
- Resolution: 0.25°×0.25°, hourly  
- Format: NetCDF  
- Config: `reanalysis-era5-single-levels.json`  
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)
- Note: Default CLUES dataset includes years 2000-2025


### Copernicus Climate Change Service (C3S) reanalysis-era5-single-levels
- Description: Global climate reanalysis (ERA5) implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 1950–present  
- Resolution: 0.1°×0.1°, hourly  
- Format: NetCDF  
- Config: `reanalysis-era5-land.json`  
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land)
- Note: Default CLUES dataset includes years 2000-2025


### ESPON
- Description: European socioeconomic data at NUTS (Nomenclature of Territorial Units for Statistics) level. NUTS is a hierarchical system developed by the European Union to divide its member states into standardized territorial units for collecting and analyzing regional statistics. It consists of three levels — NUTS 1 (major regions), NUTS 2 (basic regions for policy implementation), and NUTS 3 (small regions for detailed analysis) — with additional subdivisions at the LAU (Local Administrative Unit) level for finer granularity.  
- Years: Varies by product  
- Resolution: Varies by product  
- Format: CSV  
- Config: `espon.json`  
- [More Info](https://database.espon.eu)

### DLR Earth Observation Center (EOC) Geoservice
- Atmosphere:  
    - Description: A collection of satellite-derived global atmospheric composition and cloud property layers provided as composite images via WMS, covering global daily or monthly observations from missions like GOME, GOME-2, and TROPOMI.  
    - Years: Varies by product  
    - Resolution: Varies by product   
    - Format: GeoTIFF  
    - Config: `EOC_Atmosphere_Coverage_Service.json`  
    - More Info [here](https://atmos.caf.dlr.de/app/missions/gome) and [here](https://geoservice.dlr.de/web/datasets?t=atmosphere)  
- World Settlement Footprint (WSF):  
    - Description: Global maps outlining the extent of human settlements. Includes static products for specific years and the WSF Evolution (WSF-Evo) dataset showing annual changes.  
    - Years: 2015, 2019 (WSF); 1985–2015 (WSF-Evo)    
    - Resolution: 10m×10m (WSF), yearly; 30m×30m (WSF-Evo), yearly  
    - Format: GeoTIFF  
    - Config: `EOC_WSF.json`  
    - [More info](https://www.dlr.de/en/eoc/research-transfer/projects-missions/world-settlement-footprint-wsf-r)
- WSF3D:  
    - Description: A global dataset of the average height, total volume, total area and the fraction of buildings, capturing 3D urban structure.  
    - Years: Static  
    - Resolution: 90m×90m  
    - Format: GeoTIFF  
    - Config: `EOC_WSF3D.json`  
    - [More info](https://geoservice.dlr.de/web/datasets/wsf_3d)  

### Copernicus Global Digital Elevation model (DEM) 
- Description: Global elevation data representing Earth's surface. 
- Resolution: 30m×30m and 90m×90m, static for years 2011 - 2015  
- Format: GeoTIFF  
- Config: `copernicus_dem.json`  
- [More Info](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)  

### Copernicus Global Land Service
- Description: Global land cover classification with 23 classes aligned with UN-FAO's Land Cover Classification.  
- Years: 2015-2019
- Resolution: 100m×100m, yearly  
- Format: GeoTIFF  
- Config: `copernicus_dynamic_land_cover.json`  
- [More Info](https://zenodo.org/records/4723924)  

### Copernicus Land Monitoring Service
- Corine Land Cover dataset  
    - Description: European land cover classification and monitoring with 44 thematic classes, ranging from broad forested areas to individual vineyards.  
    - Years: 1990, 2000, 2006, 2012, and 2018  
    - Resolution: 100m×100m, yearly  
    - Format: GeoTIFF  
    - Config: `corine_copernicus.json`  
    - [More Info](https://land.copernicus.eu/en/products/corine-land-cover)  
    - Note: Default CLUES dataset includes years 2000, 2006, 2012, and 2018  
- Tree Cover Density  
    - Description: European tree cover density.  
    - Years: 2012, 2015, and annually from 2018 to 2021  
    - Resolution: 100m×100m, yearly  
    - Format: GeoTIFF  
    - Config: `treecover_copernicus.json`  
    - [More Info](https://land.copernicus.eu/en/products/high-resolution-layer-tree-cover-density)  
    - Note: Default CLUES dataset includes years 2012, 2015, and 2018  
- Forest type
    - Description: The European Forest Type layers provide information on the presence of forest and its dominant leaf type.  
    - Years: 2012, 2015, 2018, 2021  
    - Resolution: 100m×100m, yearly  
    - Format: GeoTIFF  
    - Config: `treecover_copernicus.json`  
    - [More Info](https://land.copernicus.eu/en/products/high-resolution-layer-tree-cover-density)  
    - Note: Default CLUES dataset includes years 2012, 2015, and 2018  
  
### Moderate Resolution Imagining Spectroradiometer (MODIS)
- Description: Global Vegetation Index Products - NDVI (Normalized Difference Vegetation Index) and EVI (Enhanced Vegetation Index).  
- Years: 2000-2025  
- Resolution: 250m×250m, 16-day; 1km×1km, monthly  
- Format: GeoTIFF  
- Config: `modis_vegetation.json`  
- [More Info](https://modis.gsfc.nasa.gov/data/dataprod/mod13.php)  

### SPEI (Standardized Precipitation-Evapotranspiration Index)
- Description: Global drought index based on precipitation and evapotranspiration.  
- Years: 1901–present  
- Resolution: 0.5°×0.5°, monthly  
- Format: NetCDF  
- Config: `spei.json`  
- [More Info](https://spei.csic.es)
- Note: Default CLUES dataset includes years 2000-2025

### Hydrosheds - Global Lakes and Wetlands Database (GLWD) version 2
- Description: Global inland surface waters distinguished into 33 waterbody and wetland types.  
- Years: Static  
- Resolution: 500m×500m  
- Format: GeoTIFF  
- Config: `hydrosheds_GLWD.json`  
- [More Info](https://www.hydrosheds.org/products/glwd)  

### DMSP–VIIRS - Harmonized Night-Time Lights
- Description: Global nighttime light intensity from satellites, harmonized across sensors.  
- Years: 1992–2021  
- Resolution: 1km×1km, yearly  
- Format: GeoTIFF  
- Config: `ntl.json`  
- [More Info](https://figshare.com/articles/dataset/Harmonization_of_DMSP_and_VIIRS_nighttime_light_data_from_1992-2018_at_the_global_scale/9828827/8)
- Note: Default CLUES dataset includes years 2000-2025

