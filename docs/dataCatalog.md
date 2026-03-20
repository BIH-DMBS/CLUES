# CLUES Geospatial Data Catalog
This page describes the geospatial data sources and datasets integrated into the CLUES workflow. For each data source, a short description, source-specific configuration file (config), spatial and temporal resolution, download format and reference link are provided. 

A summary table with all geospatial datasets is provided below the Geospatial Data Sources section. 


## Geospatial Data Sources

### Copernicus Atmosphere Monitoring Service (CAMS) Global Reanalysis (EAC4)
- Description: Global atmospheric composition reanalysis implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 2003–present  
- Resolution: 0.75°×0.75°, 3-hourly  
- Format: NetCDF  
- Config: `cams-global-reanalysis-eac4.json`  
- [More Info](https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview)
- DOI: 10.24381/d58bbf47
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

### Copernicus Climate Change Service (C3S) Reanalysis ERA5 on single levels
- Description: Global climate reanalysis (ERA5) implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 1940–present  
- Resolution: 0.25°×0.25°, hourly  
- Format: NetCDF  
- Config: `reanalysis-era5-single-levels.json`  
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)
- DOI: 10.24381/cds.adbb2d47
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- Note: Default CLUES dataset includes years 2000-2025


### Copernicus Climate Change Service (C3S) reanalysis-land
- Description: Global climate reanalysis (ERA5) implemented by ECMWF, using data assimilation of satellite and in-situ observations.  
- Years: 1950–present  
- Resolution: 0.1°×0.1°, hourly  
- Format: NetCDF  
- Config: `reanalysis-era5-land.json`  
- [More Info](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land)
- DOI: 10.24381/cds.e2161bac
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- Note: Default CLUES dataset includes years 2000-2025


### ESPON
- Description: European socioeconomic data at NUTS (Nomenclature of Territorial Units for Statistics) level. NUTS is a hierarchical system developed by the European Union to divide its member states into standardized territorial units for collecting and analyzing regional statistics. It consists of three levels — NUTS 1 (major regions), NUTS 2 (basic regions for policy implementation), and NUTS 3 (small regions for detailed analysis) — with additional subdivisions at the LAU (Local Administrative Unit) level for finer granularity.  
- Years: Varies by product  
- Resolution: Varies by product  
- Format: CSV  
- Config: `espon.json`  
- [More Info](https://database.espon.eu)
- License: [Custom ESPON Reuse Policy](https://www.espon.eu/legal-notice). Reproduction allowed with mandatory attribution (“© ESPON” and “Origin of information/data: ESPON EGTC”), mandatory disclaimer for results, and restrictions on map design reuse.

### DLR Earth Observation Center (EOC) Geoservice
- Atmosphere:  
    - Description: A collection of satellite-derived global atmospheric composition and cloud property layers provided as composite images via WMS, covering global daily or monthly observations from missions like GOME, GOME-2, and Sentinel-5/TROPOMI.  
    - Years: Varies by product  
    - Resolution: Varies by product   
    - Format: GeoTIFF  
    - Config: `EOC_Atmosphere_Coverage_Service.json`  
    - More Info [here](https://atmos.caf.dlr.de/app/missions/gome) and [here](https://geoservice.dlr.de/web/datasets?t=atmosphere)
    - License:
        - For GOME datasets:  
        - For GOME-2 datasets: [EUMETSAT AC-SAF User Licence](https://geoservice.dlr.de/resources/licenses/ac_saf/AC-SAF_User_License.pdf). Free-to-use with mandatory attribution (“copyright ©     EUMETSAT ”). Intellectual property rights belong to EUMETSAT; products may be reused and redistributed provided the copyright notice is displayed.
        - For Sentinel-5/TROPOMI datasets: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- World Settlement Footprint (WSF):  
    - Description: Global maps outlining the extent of human settlements. Includes static products for specific years and the WSF Evolution (WSF-Evo) dataset showing annual changes.  
    - Years: 2015, 2019 (WSF); 1985–2015 (WSF-Evo)    
    - Resolution: 10m×10m (WSF), yearly; 30m×30m (WSF-Evo), yearly  
    - Format: GeoTIFF  
    - Config: `EOC_WSF.json`  
    - [More info](https://www.dlr.de/en/eoc/research-transfer/projects-missions/world-settlement-footprint-wsf-r)
    - DOI: [WSF-2015](https://doi.org/10.15489/rlyibn8gjc58); [WSF-2019](https://doi.org/10.15489/twg5xsnquw84)
    - License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- WSF3D:  
    - Description: A global dataset of the average height, total volume, total area and the fraction of buildings, capturing 3D urban structure.  
    - Years: Static  
    - Resolution: 90m×90m  
    - Format: GeoTIFF  
    - Config: `EOC_WSF3D.json`  
    - [More info](https://geoservice.dlr.de/web/datasets/wsf_3d)
    - License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)


### Copernicus Global Digital Elevation model (DEM) 
- Description: Global elevation data representing Earth's surface. 
- Resolution: 30m×30m and 90m×90m, static for years 2011 - 2015  
- Format: GeoTIFF  
- Config: `copernicus_dem.json`  
- [More Info](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)
- DOI: 10.5270/ESA-c5d3d65
- Licence: [Copernicus Data Licence](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) Free use permitted with mandatory attribution (“© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved”) and required notices for adapted data (“produced using Copernicus WorldDEM-30…” / “produced using Copernicus WorldDEM-90…”).

### Copernicus Global Land Service
- Description: Global land cover classification with 23 classes aligned with UN-FAO's Land Cover Classification.  
- Years: 2015-2019
- Resolution: 100m×100m, yearly  
- Format: GeoTIFF  
- Config: `copernicus_dynamic_land_cover.json`  
- [More Info](https://land.copernicus.eu/en/products/global-dynamic-land-cover/copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-2019-globe)
- [DOI](https://doi.org/10.2909/c6377c6e-76cc-4d03-8330-628a03693042)
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

### Copernicus Land Monitoring Service
- Corine Land Cover dataset  
    - Description: European land cover classification and monitoring with 44 thematic classes, ranging from broad forested areas to individual vineyards.  
    - Years: 1990, 2000, 2006, 2012, and 2018  
    - Resolution: 100m×100m, yearly  
    - Format: GeoTIFF  
    - Config: `corine_copernicus.json`  
    - [More Info](https://land.copernicus.eu/en/products/corine-land-cover)
    - DOI: [1990](https://doi.org/10.2909/c89324ef-7729-4477-9f1b-623f5f88eaa1), [2000](https://doi.org/10.2909/ddacbd5e-068f-4e52-a596-d606e8de7f40), [2006](https://doi.org/10.2909/08560441-2fd5-4eb9-bf4c-9ef16725726a), [2012](https://doi.org/10.2909/a84ae124-c5c5-4577-8e10-511bfe55cc0d), [2018](https://doi.org/10.2909/960998c1-1870-4e82-8051-6485205ebbac)
    - Note: Default CLUES dataset includes years 2000, 2006, 2012, and 2018  
- Tree Cover Density  
    - Description: European tree cover density.  
    - Years: 2012, 2015, and annually from 2018 to 2023  
    - Resolution: 100m×100m, yearly  
    - Format: GeoTIFF  
    - Config: `treecover_copernicus.json`  
    - [More Info](https://land.copernicus.eu/en/products/high-resolution-layer-tree-cover-density)
    - DOI: [2012](https://doi.org/10.2909/299ad2d6-f2b8-4716-b169-1d621250fc3c), [2015](https://doi.org/10.2909/264d4e20-de6d-4f88-b1be-b592303452af), [2018](https://doi.org/10.2909/4dc35722-09ce-427f-9a1b-775a8640da27), [2019](https://doi.org/10.2909/4dc35722-09ce-427f-9a1b-775a8640da27), [2020](https://doi.org/10.2909/4dc35722-09ce-427f-9a1b-775a8640da27), [2021](https://doi.org/10.2909/4dc35722-09ce-427f-9a1b-775a8640da27), [2022](https://doi.org/10.2909/4dc35722-09ce-427f-9a1b-775a8640da27), [2023](https://doi.org/10.2909/4dc35722-09ce-427f-9a1b-775a8640da27)
    - Note: Default CLUES dataset includes years 2012, 2015, and 2018  
- Forest type
    - Description: The European Forest Type layers provide information on the presence of forest and its dominant leaf type.  
    - Years: 2012, 2015, 2018, 2021  
    - Resolution: 100m×100m, yearly  
    - Format: GeoTIFF  
    - Config: `treecover_copernicus.json`  
    - [More Info](https://land.copernicus.eu/en/products/high-resolution-layer-tree-cover-density)
    - DOI: [2012](https://doi.org/10.2909/8367f5f3-5eb1-4d89-ae8d-13a70fc834e0), [2015](https://doi.org/10.2909/8111fc53-934b-4e6a-afc7-d11664c5ebc3), [2018](https://doi.org/10.2909/bcc329c2-0676-40f5-bb62-91d36f956355), [2021](https://doi.org/10.2909/bcc329c2-0676-40f5-bb62-91d36f956355)
    - Note: Default CLUES dataset includes years 2012, 2015, and 2018
- Licence: [Copernicus Land Monitoring Service Data Policy](https://land.copernicus.eu/en/data-policy). Free, full, and open access; use permitted with mandatory attribution (“European Union’s Copernicus Land Monitoring Service information”), clear indication when data are modified, and no implied EU endorsement of derived products.

### Moderate Resolution Imagining Spectroradiometer (MODIS)
- Description: Global Vegetation Index Products - NDVI (Normalized Difference Vegetation Index) and EVI (Enhanced Vegetation Index).  
- Years: 2000-2025  
- Resolution: 250m×250m, 16-day; 1km×1km, monthly  
- Format: GeoTIFF  
- Config: `modis_vegetation.json`  
- [More Info](https://modis.gsfc.nasa.gov/data/dataprod/mod13.php)
- DOI: [250m×250m](HTTPS://DOI.ORG/10.5067/MODIS/MOD13Q1.061), [1km×1km](HTTPS://DOI.ORG/10.5067/MODIS/MOD13A3.061)
- License: [NASA ESDIS Data Use Policy](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance). NASA Earth science datasets are generally released under Creative Commons Zero ([CC0](https://creativecommons.org/public-domain/cc0/)), with attribution encouraged and no endorsement permitted.

### SPEI (Standardized Precipitation-Evapotranspiration Index)
- Description: Global drought index based on precipitation and evapotranspiration.  
- Years: 1901–present  
- Resolution: 0.5°×0.5°, monthly  
- Format: NetCDF  
- Config: `spei.json`  
- [More Info](https://spei.csic.es)
- DOI: 10.5281/zenodo.834461
- License: [Open Database License (ODbL 1.0)](https://opendatacommons.org/licenses/odbl/1-0/). Free to share, use, adapt, and create derivatives, provided that attribution is given (cite the recommended publications), the licence remains clear upon redistribution, and any publicly released adapted versions must be shared under the same ODbL (Share-Alike).
- Note: Default CLUES dataset includes years 2000-2025

### Hydrosheds - Global Lakes and Wetlands Database (GLWD) version 2
- Description: Global inland surface waters distinguished into 33 waterbody and wetland types.  
- Years: Static  
- Resolution: 500m×500m  
- Format: GeoTIFF  
- Config: `hydrosheds_GLWD.json`  
- [More Info](https://www.hydrosheds.org/products/glwd)
- DOI: 10.6084/m9.figshare.28519994
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

### DMSP–VIIRS - Harmonized Night-Time Lights
- Description: Global nighttime light intensity from satellites, harmonized across sensors.  
- Years: 1992–2021  
- Resolution: 1km×1km, yearly  
- Format: GeoTIFF  
- Config: `ntl.json`  
- [More Info](https://doi.org/10.3390/rs9060637)
- DOI: 10.6084/m9.figshare.9828827
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- Note: Default CLUES dataset includes years 2000-2020

### WorldPop - Population counts
- Description: WorldPop provides population distributions and demographic datasets. Here, the configuration file enables downloading and processing of the estimated total number of people per grid cell (People-per-Pixel, PPP) product.
- Years: 2000-2020
- Resolution: 1km×1km, yearly
- Format: GeoTIFF
- Config: `worldPop.json`
- [More info](https://hub.worldpop.org/geodata/summary?id=24777)
- DOI: 10.5258/SOTON/WP00647
- License: Creative Commons Attribution 4.0 International [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

---- 
## Summary Table
This table provides an overview of all geospatial datasets integrated into the CLUES framework. It reflects the list of datasets retrieved using the default workflow settings. 
> Last update: July 2025  
> Note: The default CLUES configuration downloads data for 2000–2025, though some sources offer longer coverage.   

| Source | Feature | Spatial Resolution | Area Covered | Temporal Coverage | Temporal Resolution | Format |
| --- | --- | --- | --- | --- | --- | --- |
| **CAMS global reanalysis (EAC4)** | black_carbon_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | organic_matter_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sulphate_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_aerosol_optical_depth_550nm | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_carbon_monoxide | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_formaldehyde | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_ozone | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | total_column_methane | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | dust_aerosol_0.03-0.55um_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | dust_aerosol_0.55-0.9um_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | dust_aerosol_0.9-20um_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophilic_black_carbon_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophilic_organic_matter_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophobic_black_carbon_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | hydrophobic_organic_matter_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_0.03-0.5um_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_0.5-5um_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sea_salt_aerosol_5-20um_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sulphate_aerosol_mixing_ratio | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **CAMS global reanalysis (EAC4)** | sulphur_dioxide | 0.75°x0.75° | Global | 2003-2024 | 3-hourly | NetCDF |
| **Copernicus DEM** | Elevation | 30mx30m | Global | Static | NA | GeoTIFF |
| **Copernicus DEM** | Elevation | 90mx90m | Global | Static | NA | GeoTIFF |
| **Copernicus Global Land Service** | Landcover | 100mx100m | Global | 2015-2019 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | Corine landcover | 100mx100m | Europe | 1990, 2000, 2006, 2012, 2018 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | Tree Cover Density | 100mx100m | Europe | 2012, 2015, 2018-2021 | yearly | GeoTIFF |
| **Copernicus Land Monitoring Service (CLMS)** | HRL Forest_Type | 100mx100m | Europe | 2012, 2015, 2018 | yearly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-1 Cloud Fraction (CF) Total Column Composite Layer (ERS-2) |  | Global | 1995-2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-1 Cloud Optical Thickness (COT) Total Column Composite Layer (ERS-2) |  | Global | 1995-2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-1 Cloud Top Pressure (CTP) Total Column Composite Layer (ERS-2) |  | Global | 1995-2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-1 Total Column Nitrogen Dioxide (NO2) Composite Layer (ERS-2) |  | Global | 1995-2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-1 Total Column Ozone (O3) Composite Layer (ERS-2) |  | Global | 1995-2011 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-2 Total Column Tropospheric Ozone Composite Layer (MetOp-A) |  | Global | 2007-2020 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-B GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2012-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | GOME-2 Total Column Tropospheric Ozone Composite Layer (MetOp-B) |  | Global | 2013-2019 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp-C GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2019-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Bromine Monoxide (BrO) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Fraction (CF) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Optical Thickness (COT) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Cloud Top Pressure (CTP) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Water Vapour (H2O) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Formaldehyde (HCHO) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Nitrogen Dioxide (NO2) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Tropospheric Nitrogen Dioxide (NO2Tropo) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Ozone (O3) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | MetOp GOME-2 Total Column Sulfur Dioxide (SO2) Composite Layer |  | Global | 2013-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L3 data of radiometric cloud fraction | 5.5kmx3.5km | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Cloud Optical Thickness (COT) Composite Layer (S5P) |  | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Cloud Top Height (CTH) Composite Layer (S5P) |  | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Formaldehyde (HCHO) Composite Layer (S5P) |  | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L3 data of ozone total column | 5.5kmx3.5km | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Sulphur Dioxid (SO2) Composite Layer (S5P) |  | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | TROPOMI/S5P L4 data of Surface NO2 concentration | 5.5kmx3.5km | Global | 2023-2024 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | Surface PM2.5 concentrations for Germany and parts of the surrounding countries from Aqua/MODIS and Sentinel-3A/SLSTR |  | Global | 2018-2019 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. Cloud Fraction |  | Global | 2018-2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Cloud Fraction |  | Global | 2018-2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. NO2 |  | Global | 2018-2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Surf. NO2 |  | Global | 2018-2020 | monthly | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Trop. NO2 column |  | Global | 2018-2020 | daily | GeoTIFF |
| **EOC-Atmosphere-Coverage-Service** | S-VELD S5P Trop. NO2 column |  | Global | 2018-2020 | monthly | GeoTIFF |
| **Hydrosheds** | Global_Lakes_and_Wetlands_Database_(GLWD) | 500mx500m | Global | Static | NA | GeoTIFF |
| **MODIS Vegetation Index Products** | normalized difference vegetation index (NDVI) | 1kmx1km | Global | 2000-2023 | monthly | GeoTIFF |
| **MODIS Vegetation Index Products** | normalized difference vegetation index (NDVI) | 250mx250m | Global | 2000-2023 | 16-day | GeoTIFF |
| **MODIS Vegetation Index Products** | enhanced vegetation index (EVI) | 1kmx1km | Global | 2000-2023 | monthly | GeoTIFF |
| **MODIS Vegetation Index Products** | enhanced vegetation index (EVI) | 250mx250m | Global | 2000-2023 | 16-day | GeoTIFF |
| **DMSP and VIIRS** | Night_Time_Lights_(NTL) | 1kmx1km | Global | 1992-2021 | yearly | GeoTIFF |
| **Copernicus ERA5 single level** | 2m_dewpoint_temperature | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | 2m_temperature | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | high_vegetation_cover | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | low_vegetation_cover | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | snowfall | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | soil_temperature_level_1 | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | total_cloud_cover | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | total_precipitation | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | type_of_high_vegetation | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | type_of_low_vegetation | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | surface_pressure | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | 10m_u_component_of_wind | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | 10m_v_component_of_wind | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | 100m_u_component_of_wind | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | 100m_v_component_of_wind | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | downward_uv_radiation_at_the_surface | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | total_cloud_cover | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 single level** | snow_depth | 0.25°x0.25° | Global | 1940-present | hourly | NetCDF |
| **Copernicus ERA5 land** | 2m_dewpoint_temperature | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | 2m_temperature | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | snow_cover | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | snow_density | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | snow_depth | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | snowfall | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | volumetric_soil_water_layer_1 | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | volumetric_soil_water_layer_2 | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | surface_net_thermal_radiation | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | 10m_u_component_of_wind | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | 10m_v_component_of_wind | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | surface_pressure | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | total_precipitation | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | leaf_area_index_high_vegetation | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | leaf_area_index_low_vegetation | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | high_vegetation_cover | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Copernicus ERA5 land** | low_vegetation_cover | 0.1°x0.1° | Global | 1950-present | hourly | NetCDF |
| **Global SPEI database** | spei_drought_index | 0.5°x0.5° | Global | 1901-present | monthly | NetCDF |
| **ESPON** | Deaths by age groups and gender | NUTS0-NUTS3 | Europe | 2013-2015 | yearly | CSV |
| **ESPON** | Deaths by age groups | NUTS0-NUTS2 | Europe | 1990-2017 | yearly | CSV |
| **ESPON** | Life expectancy by age and sex | NUTS0-NUTS2 | Europe | 2002-2017 | yearly | CSV |
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

