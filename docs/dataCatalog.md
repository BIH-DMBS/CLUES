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

## ERA5
- Description: Global climate reanalysis by ECMWF using data assimilation.
- Years: 1940–present
- Resolution: 0.25° × 0.25°, hourly
- Format: NetCDF
- Config: `reanalysis-era5-single-levels.json`
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)

## ESPON
- Description: Socioeconomic data at NUTS level for EU policy benchmarking. NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical system developed by the European Union to divide its member states into standardized territorial units for collecting and analyzing regional statistics. It consists of three levels—NUTS 1 (major regions), NUTS 2 (basic regions for policy implementation), and NUTS 3 (small regions for detailed analysis)—with additional subdivisions at the LAU (Local Administrative Unit) level for finer granularity.
- Resolution: Varies by NUTS level
- Format: CSV + shapefile
- Config: `espon.json` via `espon.generate_espon_json()`
- [More Info](https://database.espon.eu)

**ask marcel: about format and that i used different link, check Config**

## EOC Map & Coverage Services (DLR)
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

**ask marcel: which are these data to add resolution and coverage, are they global, needs maybe a more informative link?**

## Copernicus DEM (Global and European Digital Elevation model)
- Description: Digital surface model (DSM) based on TanDEM-X mission that represents the surface of the Earth including buildings, infrastructure and vegetation. 
- Resolution:
  - European coverage: 10m × 10m ,
  - Global coverage: GLO-30 and GLO-90, 3-yearly for the 2012, 2015, 2018 reference years 
- Format: GeoTIFF
- Config: `copernicus_dem.json`
- [More Info](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

**ask marcel about resolution**

## CORINE Land Cover
- Description: European land cover classification and monitoring
- Resolution: 100m
- Format: GeoTIFF
- Config: `corine_copernicus.json`
- [More Info[(https://land.copernicus.eu/en/products/corine-land-cover)
**ask marcel about the resolution**

Land Copernicus (Tree Cover Density)

Description: Tree cover density at high spatial resolution

Config: land_copernicus.json

More Info

SPEI (Standardized Precipitation-Evapotranspiration Index)

Description: Climate drought index based on precipitation and evapotranspiration

Years: 1901–present

Resolution: 0.5° × 0.5°

Format: NetCDF

Config: spei.json

More Info

Hydrosheds GLWD v2

Description: Global Lakes and Wetlands Database v2

Resolution: ~500m (15 arc-seconds)

Format: GeoTIFF

More Info

Night-Time Lights (DMSP–VIIRS Harmonized)

Description: Global nighttime light intensity from satellites, harmonized across sensors

Years: 1992–2023

Resolution: ~1km

More Info

Download
