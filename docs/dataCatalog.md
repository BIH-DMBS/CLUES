# CLUES Geospatial Data Catalog
This page describes the geospatial data sources and datasets integrated into the CLUES workflow. For each data source, we provide a short description, source-specific configuration files, spatial/temporal resolution, and download format. A summary table is provided below the Data Source Details section. 

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

## Summary Table

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
| **Copernicus DEM - Global and European Digital Elevation Model** | Digital_Geospatial_Elevation_Data_30m | 30mx30m | Global |  |  | GeoTIFF |
| **Copernicus DEM - Global and European Digital Elevation Model** | Digital_Geospatial_Elevation_Data_90m | 90mx90m | Global |  |  | GeoTIFF |
| **Copernicus Global Dynamic Land Cover** | BuildUp_CoverFraction_2015 | 100mx100m | Global | 2015 - 2019 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | corine_landcover_2018 | 100mx100m | Europe | 1990, 2000, 2006, 2012, 2018 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | Tree Cover Density 2012 | 100mx100m | Global | 2012, 2015, 2018 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | HRL_Forest_Type_2012_100m | 100mx100m | Global | 2012, 2015, 2018 | yearly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Cloud Fraction (CF) Total Column Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Cloud Optical Thickness (COT) Total Column Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Cloud Top Pressure (CTP) Total Column Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Total Column Nitrogen Dioxide (NO2) Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Daily GOME-1 Total Column Ozone (O3) Composite Layer (ERS-2) |  | Global | 1995 - 2011 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Offline (OL) Monthly GOME-2 Total Column Tropospheric Ozone Composite Layer (MetOp-A) |  | Global | 2007 - 2020 | monthly |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2012 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Offline (OL) Monthly GOME-2 Total Column Tropospheric Ozone Composite Layer (MetOp-B) |  | Global | 2013 - 2019 | monthly |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2019 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2013 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L3 data of radiometric cloud fraction |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Cloud Optical Thickness (COT) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Cloud Top Height (CTH) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Formaldehyde (HCHO) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L3 data of ozone total column |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | Sulphur Dioxid (SO2) Composite Layer (S5P) |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L4 data of Surface NO2 concentration at 15:00 UTC |  | Global | 2023 - 2024 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | This data set contains monthly mean surface PM2.5 concentrations for Germany and parts of the surrounding countries derived from Aqua/MODIS and Sentinel-3A/SLSTR data. |  | Global | 2018 - 2019 | monthly |  |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. Cloud Fraction - Orbit |  | Global | 2018 - 2020 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Cloud Fraction - Orbit |  | Global | 2018 - 2020 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. NO2 - Orbit |  | Global | 2018 - 2020 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. NO2 - Monthly |  | Global | 2018 - 2020 | monthly |  |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Trop. NO2 column - Orbit |  | Global | 2018 - 2020 | daily |  |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Trop. NO2 column - Monthly |  | Global | 2018 - 2020 | monthly |  |
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
| **ESPON** | Deaths by age groups and gender | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Deaths by age groups | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Life expectancy by age and sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Life expectancy by age | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population (total) by gender and broad age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population on 1 January (total) by age group and sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population on 1 January (total) by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | no parent | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Ageing index by gender | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Proportion of gender groups in the total population by gender | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Old-age-dependency ratio by sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Unemployment (total) by sex, age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Unemployment (total) by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment rate by age and gender (%) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment rate by age group (%) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) by gender and broad age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) by broad age groups | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) by NACE rev.2 economic section (Labour Force Survey) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Educational attainment level by age group and sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Educational attainment level by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Participation rate in education and training (last 4 weeks) by sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Early leavers from education and training by sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Unemployment (rate) by sex | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total deal value) by origin | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total deal value) by type | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total deal value) by sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total number) by origin | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total number) by type | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total number) by period | NUTS | Europe |  | yearly | CSV |
| **ESPON** | FDI projects (total number) by sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Domestic material consumption (DMC) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Gender gap by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment by economic sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Sex ratio by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Presence of North Sea Region Programme energy projects | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Energy projects (total) - by theme | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Energy projects (total) - by cluster class | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Economic resilience by type of resilience | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Photovoltaic energy | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Aggregate impact of climate change on regions | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Potential economic impact of climate change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Potential physical impact of climate change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Potential social impact of climate change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Potential cultural impact of climate change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Potential environmental impact of climate change | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 1st level (share) by use | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 2nd level (share) by use | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 3rd level (total) by use | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 1st level (share) by use | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 1st level (total) by use | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Corine Land Cover 2006 - 2nd level (total) by use | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Territorial impact of Common Agricultural Policy (CAP) by type of impact | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) by NACE rev.2 economic section (Structural Business Statistics) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment by economic sections C, F and I and divisions for sections C and F at NUTS2 | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Protected areas (total surface) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Natura 2000 sites | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Renewable energy input for district heat production (share of) | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Employment (total) by size of enterprises | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Population on 1 January (total) by age group | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Final energy consumption of petroleum products in the road transport sector | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Share of regions overlaid by Inner Peripheries (IP) according to high travel times to regional centres | NUTS | Europe |  | yearly | CSV |
| **ESPON** | Inner Peripheries according to high travel times to regional centres (grid) | NUTS | Europe |  | yearly | CSV |
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

