# CLUES Geospatial Data Catalog
This page describes the geospatial data sources and datasets integrated into the CLUES workflow. For each data source, we provide a short description, configuration details, spatial/temporal resolution, and download format.

## Summary Table
A full list of data sources and datasets that are included in the default source-specific configuration files is provided below.

## Data Source Details
Each section below provides a brief overview of the data source, key specifications, source-specific configuration file, and reference link.

### CAMS Global Reanalysis (EAC4)
- Description: Global atmospheric composition reanalysis by ECMWF using data assimilation.
- Years: 2003–present
- Resolution: 0.75° × 0.75°, 3-hourly
- Format: NetCDF
- Config: `cams-global-reanalysis-eac4.json`
- [More Info](https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview)

### ERA5
- Description: Global climate reanalysis by ECMWF using data assimilation.
- Years: 1940–present
- Resolution: 0.25° × 0.25°, hourly
- Format: NetCDF
- Config: `reanalysis-era5-single-levels.json`
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)

### ESPON
- Description: European socioeconomic data at NUTS level. NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical system developed by the European Union to divide its member states into standardized territorial units for collecting and analyzing regional statistics. It consists of three levels—NUTS 1 (major regions), NUTS 2 (basic regions for policy implementation), and NUTS 3 (small regions for detailed analysis)—with additional subdivisions at the LAU (Local Administrative Unit) level for finer granularity.
- Years: Varies by product
- Resolution: Varies by NUTS level
- Format: CSV + shapefile
- Config: `espon.json` via `espon.generate_espon_json()`
- [More Info](https://database.espon.eu)

>> **ask marcel: about format and that i used different link, check Config, resolution and years**

### EOC Map & Coverage Services (DLR)
- Atmosphere:
    - Config: `EOC_Atmosphere_Coverage_Service.json`
    - Format: NetCDF
- Elevation:
    - Config: `EOC_Elevation_Map_Service.json`
    - Format: `GeoTIFF`
- Land:
    - Config: `EOC_Land_Map_Service.json`
    - Format: `(GeoTIFF)`
- Access: [DLR GeoServices](https://geoservice.dlr.de/web/services)

>> **ask marcel: which are these data to add resolution and coverage, are they global, needs maybe a more informative link? also config files for elvation and land dont exist in the configs_sources**

### Copernicus DEM (Global and European Digital Elevation model)
- Description: Digital surface model (DSM) based on TanDEM-X mission that represents the surface of the Earth including buildings, infrastructure and vegetation. 
- Resolution:
  - European coverage: 10m × 10m , average for years 2011 - 2015
  - Global coverage: 30m × 30m and 90m × 90m, average for years 2011 - 2015 
- Format: GeoTIFF
- Config: `copernicus_dem.json`
- [More Info](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

>> **ask marcel about resolution and DTED DGED**

### CORINE Land Cover
- Description: European land cover classification and monitoring with 44 thematic classes, ranging from broad forested areas to individual vineyards.
- Years: 2000, 2006, 2012, and 2018
- Resolution: 100m × 100m, yearly
- Format: GeoTIFF
- Config: `corine_copernicus.json`
- [More Info](https://land.copernicus.eu/en/products/corine-land-cover)

>> **ask marcel about the resolution**

### Land Copernicus (Tree Cover Density)
- Description: Global tree cover density
- Years: 2012, 2015, and annually from 2018 - 2021
- Resolution: 100m × 100m, yearly
- Config: `treecover_copernicus.json`
- [More Info]([https://land.copernicus.eu/en/products/high-resolution-layer-tree-cover-density)

>> **ask marcel about the temporal coverage and if they are global, i changed the configuration file name because the one that was there before doesnt exist**

### SPEI (Standardized Precipitation-Evapotranspiration Index)
- Description: Global drought index based on precipitation and evapotranspiration
- Years: 1901–present
- Resolution: 0.5° × 0.5°, monthly
- Format: NetCDF
- Config: `spei.json`
- [More Info](https://spei.csic.es)

>> **ask marcel about the temporal resoltution**

### Hydrosheds GLWD version 2
- Description: Global inland surface waters distinguished into 33 waterbody and wetland types
- Resolution: ~500m × 500m (15 arc-seconds)
- Format: GeoTIFF
- Config: `hydrosheds_GLWD.json`
- [More Info](https://www.hydrosheds.org/products/glwd)

>> **ask marcel: temporal coverage and resolution**

### Night-Time Lights (DMSP–VIIRS Harmonized)
- Description: Global nighttime light intensity from satellites, harmonized across sensors
- Years: 1992–2021
- Resolution: ~1km × 1km (30 arc-seconds), yearly
- Format: GeoTIFF
- Config: `ntl.json`
- [More Info](https://figshare.com/articles/dataset/Harmonization_of_DMSP_and_VIIRS_nighttime_light_data_from_1992-2018_at_the_global_scale/9828827/8)

>> **Configuration files not added here: EOC_WSF.json, EOC_WSF3D.json, copernicus_dynamic_land_cover.json, modis_vegetation.json**
