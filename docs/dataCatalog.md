# CLUES Geospatial Data Catalog
This page describes the geospatial data sources and datasets integrated into the CLUES workflow. For each data source, a short description, source-specific configuration file (config), spatial and temporal resolution, download format and reference link are provided. A summary table with all geospatial datasets is provided below the Geospatial Data Sources section. 

## Geospatial Data Sources

### Copernicus Atmosphere Monitoring Service (CAMS) Global Reanalysis (EAC4)
- Description: Global atmospheric composition reanalysis implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 2003–present  
- Resolution: 0.75°×0.75°, 3-hourly  
- Format: NetCDF  
- Config: `cams-global-reanalysis-eac4.json`  
- [More Info](https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview)  

### Copernicus Climate Change Service (C3S)
- Description: Global climate reanalysis (ERA5) implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 1940–present  
- Resolution: 0.25°×0.25°, hourly  
- Format: NetCDF  
- Config: `reanalysis-era5-single-levels.json`  
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)  

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
    - Description: A global dataset of the average height, total volume, total area and the fraction of buildings, capturing 3D urban structure  
    - Years: Static  
    - Resolution: 90m×90m  
    - Format: GeoTIFF  
    - Config: `EOC_WSF3D.json`  
    - [More info](https://geoservice.dlr.de/web/datasets/wsf_3d)  

>> need to fix: At atmosphere: height 1000, width 1000 what is the spatial resolutiom?

### Copernicus Global Digital Elevation model (DEM) 
- Description: Digital surface model (DSM) based on TanDEM-X mission that represents the surface of the Earth including buildings, infrastructure and vegetation.  
- Resolution: 30m×30m and 90m×90m, static for years 2011 - 2015  
- Format: GeoTIFF  
- Config: `copernicus_dem.json`  
- [More Info](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)  

### Copernicus Land Monitoring Service - CORINE Land Cover dataset
- Description: European land cover classification and monitoring with 44 thematic classes, ranging from broad forested areas to individual vineyards.  
- Years: 1990, 2000, 2006, 2012, and 2018  
- Resolution: 100m×100m, yearly  
- Format: GeoTIFF  
- Config: `corine_copernicus.json`  
- [More Info](https://land.copernicus.eu/en/products/corine-land-cover)  

### Land Copernicus - Tree Cover Density
- Description: Global tree cover density  
- Years: 2012, 2015, and 2018  
- Resolution: 100m×100m, yearly  
- Config: `treecover_copernicus.json`  
- [More Info](https://land.copernicus.eu/en/products/high-resolution-layer-tree-cover-density)

### Moderate Resolution Imagining Spectroradiometer (MODIS)
- Description: Global Vegetation Index Products - NDVI and EVI  
- Years: 2000-2023  
- Resolution: 250m×250m, 16-day; 1km×1km, montly  
- Config: `modis_vegetation.json`  
- [More Info](https://modis.gsfc.nasa.gov/data/dataprod/mod13.php)  

### SPEI (Standardized Precipitation-Evapotranspiration Index)
- Description: Global drought index based on precipitation and evapotranspiration  
- Years: 1901–present  
- Resolution: 0.5°×0.5°, monthly  
- Format: NetCDF  
- Config: `spei.json`  
- [More Info](https://spei.csic.es)  

### Hydrosheds - Global Lakes and Wetlands Database (GLWD) version 2
- Description: Global inland surface waters distinguished into 33 waterbody and wetland types  
- Years: Static  
- Resolution: 500m×500m  
- Format: GeoTIFF  
- Config: `hydrosheds_GLWD.json`  
- [More Info](https://www.hydrosheds.org/products/glwd)  

### DMSP–VIIRS - Harmonized Night-Time Lights
- Description: Global nighttime light intensity from satellites, harmonized across sensors  
- Years: 1992–2021  
- Resolution: 1km×1km, yearly  
- Format: GeoTIFF  
- Config: `ntl.json`  
- [More Info](https://figshare.com/articles/dataset/Harmonization_of_DMSP_and_VIIRS_nighttime_light_data_from_1992-2018_at_the_global_scale/9828827/8)  

>> **Configuration file not added here: copernicus_dynamic_land_cover.json, **

## Summary Table
This table provides an overview of all geospatial datasets integrated into the CLUES framework. It reflects the datasets retrieved using the default workflow settings.  
> Note: The default CLUES configuration downloads data for 2000–2025, though some sources offer longer coverage.   
> Last update: July 2025  

| Source | Feature | Spatial Resolution | Area Covered | Temporal Coverage | Temporal Resolution | Format |
| --- | --- | --- | --- | --- | --- | --- |
| **CAMS global reanalysis (EAC4)** | black_carbon_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | organic_matter_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sulphate_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_carbon_monoxide | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_formaldehyde | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_ozone | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_methane | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | dust_aerosol_0.03-0.55um_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | dust_aerosol_0.55-0.9um_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | dust_aerosol_0.9-20um_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophilic_black_carbon_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophilic_organic_matter_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophobic_black_carbon_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophobic_organic_matter_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_0.03-0.5um_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_0.5-5um_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_5-20um_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sulphate_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sulphur_dioxide | 0.75°x0.75° | Global | 2003 - 2024 | 3-hourly | NetCDF |
| **Copernicus DEM - Global Digital Elevation Model** | Digital_Geospatial_Elevation_Data_30m | 30mx30m | Global | Static | NA | GeoTIFF |
| **Copernicus DEM - Global Digital Elevation Model** | Digital_Geospatial_Elevation_Data_90m | 90mx90m | Global | Static | NA | GeoTIFF |
| **Copernicus Global Dynamic Land Cover** | ??? | 100mx100m | Global | 2015 - 2019 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | corine_landcover | 100mx100m | Europe | 2000, 2006, 2012, 2018 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | Tree Cover Density | 100mx100m | Global | 2012, 2015, 2018 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | ??? HRL_Forest_Type ??? | 100mx100m | Global | 2012, 2015, 2018 | yearly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Cloud Fraction (CF) Total Column Composite Layer (ERS-2) |  | Global | 2000-2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Cloud Optical Thickness (COT) Total Column Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Cloud Top Pressure (CTP) Total Column Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Total Column Nitrogen Dioxide (NO2) Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Total Column Ozone (O3) Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Offline (OL) Monthly GOME-2 Total Column Tropospheric Ozone Composite Layer (MetOp-A) |  | Global | 2007 - 2020 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2012 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Offline (OL) Monthly GOME-2 Total Column Tropospheric Ozone Composite Layer (MetOp-B) |  | Global | 2013 - 2019 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2019 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2013 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2013 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2013 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2013 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L3 data of radiometric cloud fraction |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Cloud Optical Thickness (COT) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Cloud Top Height (CTH) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Formaldehyde (HCHO) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L3 data of ozone total column |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Sulphur Dioxid (SO2) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L4 data of Surface NO2 concentration at 15:00 UTC |  | Global | 2023 - 2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | This data set contains monthly mean surface PM2.5 concentrations for Germany and parts of the surrounding countries derived from Aqua/MODIS and Sentinel-3A/SLSTR data. |  | Global | 2018 - 2019 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. Cloud Fraction - Orbit |  | Global | 2018 - 2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Cloud Fraction - Orbit |  | Global | 2018 - 2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. NO2 - Orbit |  | Global | 2018 - 2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. NO2 - Monthly |  | Global | 2018 - 2020 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Trop. NO2 column - Orbit |  | Global | 2018 - 2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Trop. NO2 column - Monthly |  | Global | 2018 - 2020 | monthly | GeoTIFF |
| **Hydrosheds** | Global_Lakes_and_Wetlands_Database_(GLWD) |  | Global |  |  |  |
| **MODIS Vegetation Index Products** | normalized difference vegetation index (NDVI) | 1kmx1km | Global | 2000 - 2025 | 16-day |  |
| **MODIS Vegetation Index Products** | normalized difference vegetation index (NDVI) | 250mx250m | Global | 2000 - 2025 | monthly |  |
| **MODIS Vegetation Index Products** | enhanced vegetation index (EVI) | 1kmx1km | Global | 2000 - 2025 | 16-day |  |
| **MODIS Vegetation Index Products** | enhanced vegetation index (EVI) | 250mx250m | Global | 2000 - 2025 | monthly |  |
| **Harmonization of DMSP and VIIRS nighttime light data from 1992-2021** | Night_Time_Lights_(NTL) | 1kmx1km | Global | 1992 - 2021 | yearly |  |
| **Copernicus ERA5** | 2m_dewpoint_temperature | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | 2m_temperature | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | high_vegetation_cover | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | low_vegetation_cover | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | snowfall | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | soil_temperature_level_1 | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | total_cloud_cover | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | total_precipitation | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | type_of_high_vegetation | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | type_of_low_vegetation | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | surface_pressure | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | 10m_u_component_of_wind | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | 10m_v_component_of_wind | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | 100m_u_component_of_wind | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | 100m_v_component_of_wind | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | downward_uv_radiation_at_the_surface | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | total_cloud_cover | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5** | snow_depth | 0.25° x 0.25° | Global | 1940-present | hourly | NetCDF |
| **Global SPEI database** | spei_drought_index | 0.5° x 0.5° | Global | 1901-present | monthly | NetCDF |
| **ESPON** | Deaths by age groups and gender | NUTS0-NUTS3 | Europe | 2013-2015 | yearly | CSV |
| **ESPON** | Deaths by age groups | NUTS0-NUTS2 | Europe | 1990-2017 | yearly | CSV |
| **ESPON** | Life expectancy by age and sex | NUTS | Europe | 2002-2017 | yearly | CSV |
| **ESPON** | Life expectancy by age | NUTS0-NUTS2 | Europe | 2002-2017 | yearly | CSV |
| **ESPON** | Population (total) by gender and broad age group | -- | Europe | -- | yearly | CSV |
| **ESPON** | Population on 1 January (total) by age group and sex | NUTS0-NUTS2 | Europe | 1990-2020 | yearly | CSV |
| **ESPON** | Population on 1 January (total) by age group | NUTS0-NUTS2 | Europe | 1990-2020 | yearly | CSV |
| **ESPON** | No parent | -- | Europe | -- | yearly | CSV |
| **ESPON** | Ageing index by gender | NUTS0-NUTS2 | Europe | 1990-2018 | yearly | CSV |
| **ESPON** | Proportion of gender groups in the total population by gender | -- | Europe | -- | yearly | CSV |
| **ESPON** | Old-age-dependency ratio by sex | NUTS0-NUTS3 | Europe | 1990-2018 | yearly | CSV |
| **ESPON** | Unemployment (total) by sex, age group | NUTS0-NUTS2 | Europe | 1999-2020 | yearly | CSV |
| **ESPON** | Unemployment (total) by age group | NUTS0-NUTS2 | Europe | 1999-2020 | yearly | CSV |
| **ESPON** | Employment rate by age and gender (%) | NUTS0-NUTS2 | Europe | 1990-2018 | yearly | CSV |
| **ESPON** | Employment rate by age group (%) | NUTS0-NUTS2 | Europe | 1990-2018 | yearly | CSV |
| **ESPON** | Employment (total) by gender and broad age group | NUTS0-NUTS2 | Europe | 2005-2020 | yearly | CSV |
| **ESPON** | Employment (total) by broad age groups | NUTS0-NUTS2 | Europe | 2005-2020 | yearly | CSV |
| **ESPON** | Employment (total) by NACE rev.2 economic section (Labour Force Survey) | NUTS0-NUTS2 | Europe | 2005-2020 | yearly | CSV |
| **ESPON** | Educational attainment level by age group and sex | NUTS0-NUTS2 | Europe | 2000-2020 | yearly | CSV |
| **ESPON** | Educational attainment level by age group | NUTS0-NUTS2 | Europe | 2000-2020 | yearly | CSV |
| **ESPON** | Participation rate in education and training (last 4 weeks) by sex | NUTS0-NUTS2 | Europe | 2000-2020 | yearly | CSV |
| **ESPON** | Early leavers from education and training by sex | NUTS0-NUTS2 | Europe | 2000-2020 | yearly | CSV |
| **ESPON** | Unemployment (rate) by sex | NUTS0-NUTS2 | Europe | 1999-2020 | yearly | CSV |
| **ESPON** | FDI projects (total deal value) by origin | NUTS3 | Europe | 2003-2015 | yearly | CSV |
| **ESPON** | FDI projects (total deal value) by type | NUTS3 | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total deal value) by sector | NUTS3 | Europe | 2003-2015 | yearly | CSV |
| **ESPON** | FDI projects (total number) by origin | NUTS3 | Europe | 2003-2015 | yearly | CSV |
| **ESPON** | FDI projects (total number) by type | NUTS3 | Europe | 2003-2015 | yearly | CSV |
| **ESPON** | FDI projects (total number) by period | NUTS3 | Europe | 2003-2015 | yearly | CSV |
| **ESPON** | FDI projects (total number) by sector | NUTS3 | Europe | 2003-2015 | yearly | CSV |
| **ESPON** | Domestic material consumption (DMC) | NUTS0 | Europe | 2014 | yearly | CSV |
| **ESPON** | Gender gap by age group | NUTS2 | Europe |  | yearly | CSV |
| **ESPON** | Employment by economic sector | NUTS | Europe | 2009 | yearly | CSV |
| **ESPON** | Sex ratio by age group | NUTS2, NUTS3 | Europe | 2008 | yearly | CSV |
| **ESPON** | Presence of North Sea Region Programme energy projects | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Energy projects (total) - by theme | NUTS2 | Europe | 2013 | yearly | CSV |
| **ESPON** | Energy projects (total) - by cluster class | NUTS2 | Europe | 2013 | yearly | CSV |
| **ESPON** | Economic resilience by type of resilience | NUTS0, NUTS2, NUTS3 | Europe | 1985-2011 | yearly | CSV |
| **ESPON** | Photovoltaic energy | -- | Europe | -- | yearly | CSV |
| **ESPON** | Aggregate impact of climate change on regions | NUTS3 | Europe | 2071-2100 | yearly | CSV |
| **ESPON** | Potential economic impact of climate change | NUTS3 | Europe | 2071-2100 | yearly | CSV |
| **ESPON** | Potential physical impact of climate change | NUTS3 | Europe | 2071-2100 | yearly | CSV |
| **ESPON** | Potential social impact of climate change | NUTS3 | Europe | 2071-2100 | yearly | CSV |
| **ESPON** | Potential cultural impact of climate change | NUTS3 | Europe | 2071-2100 | yearly | CSV |
| **ESPON** | Potential environmental impact of climate change | NUTS3 | Europe | 2071-2100 | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 1st level (share) by use | 100m and 250m | Europe | -- | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 2nd level (share) by use | 100m and 250m | Europe | -- | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 3rd level (total) by use | 100m and 250m | Europe | -- | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 1st level (share) by use | 100m and 250m | Europe | -- | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 1st level (total) by use | 100m and 250m | Europe | -- | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 2nd level (total) by use | 100m and 250m | Europe | -- | yearly | CSV |
| **ESPON** | Territorial impact of Common Agricultural Policy (CAP) by type of impact | NUTS2 | Europe | 2009 | yearly | CSV |
| **ESPON** | Employment (total) by NACE rev.2 economic section (Structural Business Statistics) | -- | Europe | -- | yearly | CSV |
| **ESPON** | Employment by economic sections C, F and I and divisions for sections C and F at NUTS2 | NUTS2 | Europe | 2005-2017 | yearly | CSV |
| **ESPON** | Protected areas (total surface) | NUTS3 | Europe | 2017 | yearly | CSV |
| **ESPON** | Natura 2000 sites | NUTS3 | Europe | 2015 | yearly | CSV |
| **ESPON** | Renewable energy input for district heat production (share of) | -- | Europe | -- | yearly | CSV |
| **ESPON** | Employment (total) by size of enterprises | NUTS2, NUTS3 | Europe | 2008, 2014 | yearly | CSV |
| **ESPON** | Population on 1 January (total) by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Final energy consumption of petroleum products in the road transport sector | -- | Europe | -- | yearly | CSV |
| **ESPON** | Share of regions overlaid by Inner Peripheries (IP) according to high travel times to regional centres | NUTS3 | Europe | 2017 | yearly | CSV |
| **ESPON** | Inner Peripheries according to high travel times to regional centres (grid) | NUTS3 | Europe | 2017 | yearly | CSV |
| **ESPON** | Share of regions overlaid by Inner Peripheries (IP) according to access to Services of General Interest (SGIs) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Delineations by SGI | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Share of regions overlaid IP by SGI | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Unemployment (rate) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Gross Domestic Product (GDP) per capita - disintegration scenario 2031 | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Rejected asylum applications per country (%) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Country location index for rejected asylum applications (index) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Country of previous residence of immigrants - by country | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Area of statistical regions | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Electricity generation by wind onshore technology | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Foreign residents (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population change (%) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Green infrastructure - spatial distribution (grid data) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Green infrastructure - multifunctionality (grid data) | NUTS | Europe |  | yearly |  |
| **ESPON** | [Forecast] GDP in M€ prediction scenario 1: Stable recovery from the crisis scenario | NUTS | Europe |  | yearly | CSV |
| **ESPON** | [Forecast] Population prediction 2 : Economically integrated scenario | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Tabulated data on FEIs situation 170331 | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Project categorisation data by five dimensions | NUTS | Europe |  | yearly | CSV |
| **ESPON** | loan investment for energy in buildings | NUTS | Europe |  | yearly | CSV |
| **ESPON** | loan investment for energy in buildings | NUTS | Europe |  | yearly | CSV |
| **ESPON** | OP contributions EU amount committed to FIs 2007-2013 | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population (total) by broad age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (share) by broad economic sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Housing survey: is it easy to find good housing in your city? - by answer | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Total number of material cultural heritage objects | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Trademark applications in the relevant sectors | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Inversed annual seasonality of tourism | NUTS | Europe |  | yearly | CSV |
| **ESPON** | People employed in highly knowledge intensive sectors | NUTS | Europe |  | yearly | CSV |
| **ESPON** | SMEs innovating in-house | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Difficulties in accessing financing for circular economy activities | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Potential accessibility by main transport modes | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Live births (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Death (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population - age group 25-64 - with educational attainment level 5-8 (%) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Long-term unemployment (12 months and more) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | People at risk of poverty or social exclusion (% of total population) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | 4.0 patents by sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Regional specialisation by groups of sectors | NUTS | Europe |  | yearly | CSV |
| **ESPON** | 4.0 patents | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population using online services by type of services | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Risk of job automation | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Robot adoption by sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Online sales adoption by sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Specialisation in induced manufacturing sectors | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Taxonomy of technological transformations | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Regional creation and displacement of low-skill jobs | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population on 1 January (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Quality of Life indicators | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Territorial Quality of Life Index - Life Flourishing dimension | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Territorial susceptibility to natural hazards | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Economic damage due to earthquakes, average of yearly impacts | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Economic damage due to four natural hazard types (yearly impacts) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Landslide susceptibility | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Simulated scenario-based GDP - by type of scenario | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Untapped potentials for economic growth in Central Europe - by type | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Project partnership (total number) - by type | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population living in vulnerable territories | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population living in vulnerable territories (share of) - by level of vulnerability | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Flows in Central Europe - cluster analyses - by sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Digital maturity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Innovative technologies | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Scaling up | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Proneness to change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Innovation governance | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Context empowerment | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Societal engagement | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Open Data | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Social Media Presence | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Skills | NUTS | Europe |  | yearly |CSV  |
| **ESPON** | Trade of goods regional connectivity | NUTS | Europe |  | yearly |CSV  |
| **ESPON** | Climate change aggregated risk - by climate scenario and by exposure type | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Road freight regional send-receive balance | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Migration regional balance | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Tourism regional weighted intensity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Labour regional intensity (inflows) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Rail passenger regional intensity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Maritime passenger regional connectivity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Air passenger regional external Influence | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI regional send-receive balance (incoming) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI regional network selectivity (outgoing) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Remittances regional weighted intensity (incoming) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Remittances regional intensity (outgoing) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Erasmus regional external Influence (inflows) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | H2020 regional external Influence (outflows) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Patents regional network selectivity (outflows) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Trade of services regional intensity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Goods, services and capital Balance Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | People Balance  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Knowledge Balance  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | All flows Balance Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Goods, services and capital Concentration Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | People Concentration  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Knowledge Concentration  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | All flows Weighted intensity  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Goods, services and capital Average Distance Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | People Average Distance  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Knowledge Average Distance  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | All flows Average Distance Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | All flows Weighted intensity  Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | All flows Concentration Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | All flows Balance Index | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Rail freight regional connectivity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Maritime freight regional external Influence | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Air freight regional connectivity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Climate change risk - by impact chain, by climate scenario and by exposur | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Climate change vulnerability - by impact chain | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Climate change sensitivity - by impact chain | NUTS | Europe |  | yearly |  |
| **ESPON** | Climate change exposure - by impact chain and by exposure type | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Climate change hazard - by impact chain and by climate scenario | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Tourism regional weighted intensity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Tourism regional weighted intensity | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Migration regional concentration per area | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Migration regional average distance | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Gross Value Added (GVA) by economic sectors at basic prices | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment by economic sectors | NUTS | Europe |  | yearly | CSV |
| **ESPON** | COVID19 cases daily (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Excess Mortality weekly (total) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Broadband access rate (% households) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Crude rate of natural change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Renewable energy input for district heat production (share of) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Renewable energy input for electricity production (share of) | NUTS | Europe | varries | yearly | CSV |

