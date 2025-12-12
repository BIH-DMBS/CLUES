# Adaptive KDE Raster

## Overview
The `adaptive_kde_raster.py` module implements adaptive kernel density estimation (KDE) for raster data processing.

## Purpose
Generates density raster maps using adaptive kernel density estimation techniques, allowing for variable bandwidth based on local data density.

## Key Features
- **Adaptive Bandwidth**: Adjusts kernel bandwidth based on local point density
- **Raster Output**: Produces gridded density estimates
- **Flexible Kernels**: Supports various kernel functions for density computation

## Usage
```python
from adaptive_kernel_filter.adaptive_kde_raster import AdaptiveKDERaster

kde = AdaptiveKDERaster(points, grid_resolution=100)
density_raster = kde.compute()
```

## Parameters
- `points`: Input point geometry
- `grid_resolution`: Output raster cell size
- `bandwidth`: Adaptive bandwidth calculation method

## Output
Returns a raster grid containing kernel density values at each cell location.
