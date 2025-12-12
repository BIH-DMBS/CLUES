## Scripts and Notebooks

To facilitate working with CLUES users are provided with …

### Scripts

#### Linking

##### Locations

##### Area

##### Espon

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

### Notebooks

#### Analysis Demo

#### GeoTiff

#### NetCDF

#### Espon
 