# Data Formats Used in CLUES

## Introduction  
CLUES integrates a variety of open‑access geospatial and environmental data for epidemiological and health research. To accommodate diverse data types (gridded climate data, raster imagery, socioeconomic indicators, etc.) while preserving interoperability, readability, and reproducibility, CLUES supports multiple standard data formats. This document describes the main formats used: netCDF, GeoTIFF, and the ESPON‑derived CSV structure.

---

## netCDF files  
We use netCDF (Network Common Data Format) — typically with the “classic” or NetCDF‑4/HDF5 model — for multidimensional scientific data cubes (e.g. time × latitude × longitude, possibly with additional dimensions like vertical levels or variables).  

**Why netCDF?**  
- netCDF is a **self‑describing, machine‑independent** format: each file contains metadata describing its dimensions, variables, units, and attributes. 
- It is widely used in climate, environmental, and Earth-system sciences (e.g. modelling, remote sensing products), which makes it ideal for climate or environmental layers integrated into CLUES.  
- netCDF supports efficient slicing, subsetting, compression, and remote/partial reading — useful for large spatio‑temporal datasets. 

Usage within CLUES: netCDF files store gridded data (e.g. time series of temperature, precipitation, air pollution) in a way that preserves full dimensionality and metadata, facilitating reproducible analyses, time‑series extraction, and subsetting by time or space.

---

## GeoTIFF files  
For raster data (e.g. satellite imagery, land‑cover maps, digital elevation models, other spatial rasters), CLUES uses GeoTIFF format — the georeferenced extension of the standard TIFF image format.

**Strengths:**  
- GeoTIFF embeds geographic metadata (coordinate reference system, georeferencing, projection info), making it directly compatible with GIS software. 
- It is a widely supported, open, and interoperable standard. Many GIS and remote‑sensing tools (open-source and commercial) can read/write GeoTIFF. 
- Suitable for raster layers that do not need multidimensional time-series structure (or where each raster corresponds to a single timestamp or scenario). 

Usage within CLUES: GeoTIFF is used for spatial raster datasets where a simple 2D (or multi-band) grid suffices — for example land cover, elevation, or fixed raster surfaces. Users can load these directly into GIS or raster‑processing tools for mapping or spatial analyses.

---

## ESPON (socioeconomic / indicator) data  

The ESPON repository provides one folder per indicator or theme and a top-level geometry.csv. Indicator CSVs include metadata columns (id, name, code, nomenclature, version, tunit_code, tunit_name, sources, etc.) along with value columns (e.g., y_2015). Spatial geometry is stored once in geometry.csv as WKT keyed by tunit_code. The indicators themselves are retrieved via the ESPON API, which means they are programmatically queried from ESPON’s database.

CSV was chosen for portability, human readability, and tooling support. CSV files are universally readable, easily diff-able and version-controlled, and embedding metadata in each row ensures that the data is self-describing for non-GIS users. Using CSV also avoids limitations of shapefiles/DBF (restricted field names, limited types, poor Unicode support) and allows geometry reuse across multiple indicators without duplicating large geometry blobs. A single geometry.csv avoids duplicating large geometry blobs across many indicator files — smaller repo, simpler geometry updates.

**Data**

- Layout: espon contains one folder per indicator/theme and a top-level geometry.csv.
- Data model: Indicator CSVs (e.g., Population_total_-_age_group_65.csv) include metadata columns (id, name, code, nomenclature, version, tunit_code, tunit_name, sources, etc.) and one or more value columns (y_2015 …). Spatial geometry is stored once in geometry.csv as WKT keyed by tunit_code.

**Why CSV**

- Portability & tooling: CSV is readable by nearly every data tool, scripting language (Pandas, R), CLI utilities and is trivial to diff/version-control. That makes automated ETL and reproducible scripts simpler.
- Human readable / small metadata-per-row: Embedding metadata columns in every row (sources, id, version) makes each CSV self-describing for non-GIS users.
- Avoid DBF/shapefile limitations: Shapefile (DBF) imposes limits (10-character field names in older DBF implementations, restricted types, poor Unicode support). Using CSV avoids silent name truncation and encoding issues.
- Geometry reuse: A single geometry.csv avoids duplicating large geometry blobs across many indicator files — smaller repo, simpler geometry updates.

**Conversion example**

Python (GeoPandas) example to merge a CSV and geometry.csv and write a GeoPackage:
```bash
import pandas as pd
import geopandas as gpd
from shapely import wkt

attrs = pd.read_csv("data/espon/Population_total_by_broad_age_group/Population_total_-_age_group_65.csv", encoding="utf-8")
geom = pd.read_csv("data/espon/geometry.csv", encoding="utf-8")
geom["geometry"] = geom["geometry"].apply(wkt.loads)
gdf_geom = gpd.GeoDataFrame(geom, geometry="geometry", crs="EPSG:4326")
# join on tunit_code
merged = attrs.merge(gdf_geom[["tunit_code","geometry"]], on="tunit_code", how="left")
gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")
# convert types explicitly if needed, then
gdf.to_file("Population_total_age65.gpkg", layer="Pp65sp", driver="GPKG")
```
The merged result can be stored as GeoPackage (.gpkg).

**Conversion script into a GeoPackage and a metadata.json**

CLUES provides a [conversion script](https://github.com/BIH-DMBS/CLUES/blob/main/scripts/espon_to_gpkg.py) that converts an ESPON indicator CSV together with geometry.csv into a fully geospatial GeoPackage and an accompanying metadata.json. It merges the attribute and geometry data by tunit_code, attempts to infer simple column types, and outputs a GIS-ready layer with CRS and provenance information. This provides a reproducible, interoperable format for use in GIS software while preserving the simplicity and portability of the original CSV structure. 

---

## Why this combination of formats  

By supporting netCDF for multidimensional gridded data, GeoTIFF for raster layers, and a tabular-plus-geometry CSV structure for socioeconomic indicators, CLUES achieves:  

- **Flexibility:** different data types (time series, rasters, tabular indicators) are stored in the most appropriate, standards-compliant format.  
- **Interoperability:** netCDF and GeoTIFF are widely supported in scientific and GIS workflows; the CSV approach for indicators remains simple and easily usable by non‑GIS users, while conversion to full GIS‑ready formats remains possible.  
- **Reproducibility and version control:** formats are open and text/binary standards (netCDF, GeoTIFF, CSV), making data easier to share, diff, and manage in code-based workflows.  

---

