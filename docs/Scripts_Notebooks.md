## Scripts and Notebooks

To facilitate working with CLUES users are provided with scripts and notebooks that can be uesed to get a better understanding on how to link research data with geospatial features.

### Scripts

A collection of handy [Scripts](https://bih-dmbs.github.io/CLUES/Scripts_Notebooks/)** can be found here.

#### Linking

There are two ways of linking geospatial data, either with point locations or with areas.

##### Locations

For [area point](https://github.com/BIH-DMBS/CLUES/tree/main/scripts/link_locations) scripts can be found here. There are two scripts, one for geoTIFF data and another for netCDF files.

##### Area

For [area linking](https://github.com/BIH-DMBS/CLUES/tree/main/scripts/link_areas) scripts can be found here. There are two scripts, one for geoTIFF data and another for netCDF files.

##### [ESPON Scripts Documentation](https://github.com/BIH-DMBS/CLUES/tree/main/scripts/espon/)

Scripts for processing ESPON (European Spatial Planning Observation Network) geospatial data.

**espon_to_gpkg.py**
Converts ESPON data formats to GeoPackage (.gpkg) format.

Purpose: Transform ESPON datasets into a standard GeoPackage database for easier integration and analysis.

Key Features:
- Reads ESPON source files
- Validates geospatial data
- Exports to GeoPackage format

Usage:
```bash
python espon_to_gpkg.py [input_file] [output_file.gpkg]
```

---

**geolocation_to_espon.py**

Links geolocation data to ESPON-csv data.

Purpose: Linking standard geolocation datasets to align with ESPON data structures and requirements.

**Usage:**

```bash
python geolocation_to_espon.py [input_file] [output_file]
```

---


####  [Climate Change Indices](https://github.com/BIH-DMBS/CLUES/tree/main/scripts/climate_Change_indices/)

This module provides functionality for calculating and analyzing climate change indices. It contains tools for processing climate data and computing various indicators used to measure changes in climate patterns, temperature trends, precipitation anomalies, and other climate-related metrics.

**Features**
- Climate index calculation
- Data processing and analysis
- Climate change trend assessment
- Statistical analysis of climate variables

**Usage**
Import this module to access climate change index calculations and analysis functions.

#### Tools

#### [Adaptive Kernel](https://github.com/BIH-DMBS/CLUES/tree/main/scripts/adaptive_kernel_filter/)

The `adaptive_kde_raster.py` module implements adaptive kernel density estimation (KDE) for raster data processing.

**Purpose**

Generates density raster maps using adaptive kernel density estimation techniques, allowing for variable bandwidth based on local data density.

**Key Features**
- **Adaptive Bandwidth**: Adjusts kernel bandwidth based on local point density
- **Raster Output**: Produces gridded density estimates
- **Flexible Kernels**: Supports various kernel functions for density computation

**Usage**
```python
from adaptive_kernel_filter.adaptive_kde_raster import AdaptiveKDERaster

kde = AdaptiveKDERaster(points, grid_resolution=100)
density_raster = kde.compute()
```

**Parameters**
- `points`: Input point geometry
- `grid_resolution`: Output raster cell size
- `bandwidth`: Adaptive bandwidth calculation method

**Output**
Returns a raster grid containing kernel density values at each cell location.

#### Address to coordinates

Script for converting addresses to geographic coordinates.

**Usage**

```bash
python geocode_addresses.py <input_file> <output_file>
```

**Features**

- Batch geocoding of addresses
- Multiple geocoding provider support
- Error handling and logging
- CSV input/output support

**Example**

```python
from geocode_addresses import geocode_batch

results = geocode_batch('addresses.csv')
results.to_csv('coordinates.csv')
```

#### [Blur Locations](https://bih-dmbs.github.io/CLUES/Scripts_Notebooks/)**

This module provides functionality to blur geographic point locations by adding buffers around them. It's useful for privacy protection when working with sensitive location data.

**`blur_locations(csv_path, output_path, buffer_meters=100, wsg_epsg=4326, metric_epsg=3857)`**
Blurs point locations by creating a buffer zone around each point and calculating the centroid within that buffer.

**Parameters:**
- `csv_path` (str): Path to input CSV file containing columns: ID, x, y
- `output_path` (str): Path where the output CSV will be saved
- `buffer_meters` (int): Buffer radius in meters (default: 100)
- `wsg_epsg` (int): EPSG code for original geographic projection (default: 4326 for WGS84)
- `metric_epsg` (int): EPSG code for metric projection used in calculations (default: 3857 for Web Mercator)

**Returns:**
None. Writes results to CSV file with columns: ID, blurred_x, blurred_y

**Process:**
1. Reads input CSV and creates GeoDataFrame with point geometries
2. Reprojects to metric CRS for accurate distance-based buffering
3. Creates circular buffer around each point
4. Calculates centroid of buffer as blurred location
5. Reprojects back to original coordinate system
6. Exports results to CSV

** `create_example_csv(output_path="example_locations.csv")`
Generates a sample CSV file with random geographic coordinates for testing purposes.

**Parameters:**
- `output_path` (str): Path where example CSV will be saved (default: "example_locations.csv")


### Notebooks

There a several notebooks that can be used as tutorials. They can be found [here](https://github.com/BIH-DMBS/CLUES/tree/main/notebooks). There are notebooks that demonstrate how to work with: GeoTiff, NetCDF or Espon.

#### Analysis Demo

For the environMENTAL Summer school 2025 in Marseile we have created a small demo on how to use CLUES on dummy data. There is a collection of notebooks that create dummy data and apply random forest as an example on the dummy data. The notebooks can be found [here](https://github.com/BIH-DMBS/CLUES/tree/main/notebooks/random_forest_demo)