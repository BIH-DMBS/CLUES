# CLUES: A Comprehensive Workflow for Integrating Geospatial Data in Health Research

## About

CLUES (Climate, Urbanicity, Environment and Society) is a modular workflow that enables researchers to systematically integrate open-access geospatial environmental data with health research datasets at the individual-level. It automates the download, harmonisation, and management of data across climate, built/natural environment, air pollution, and regional socioeconomic conditions.

**Key Features**
- Automated data retrieval from multiple open-access geospatial sources
- Standardised harmonisation of spatial/temporal coverage, projections, and file types
- Modular integration with health cohort datasets at the individual level
- Extensible architecture for adding new environmental variables over time
- Adherence to FAIR (Findable, Accessible, Interoperable, Reusable) and data protection principles
  

![Diagram](docs/CLUES_schema.png)


## Getting started
- To understand the scientific foundation of CLUES, please read our publication (**link**).
- To get an overview of the geospatial data (assets) and data sources used in CLUES, see the [Data List](datalist.md). For more infomation, visit the [Geospatial Data Guide](geospatial_data.md).
- To learn how to use the CLUES framework, follow the [User Guide](gettingStarted.md) and explore the Examples (**link**).
- All scripts are available as python notebooks [here](notebooks) 

## Citation
When using CLUES in your work, please cite our paper

Jentsch M., et al., CLUES: A Comprehensive Workflow for Integrating Geospatial Data in Biomedical Research. Best Journal on Earth, 2025. **6**(44). 


## Maintainers

The CLUES maintainers are:
- Marcel Jentsch (lead maintainer)
- Sven Twardziok

## Software resources
[Rasterio](https://rasterio.readthedocs.io/en/latest/index.html)

Rasterio provides a NumPy-based Python API to read and write GeoTIFF and similar formats.

[NumPy](https://numpy.org)

NumPy is a Python library that provides fast, efficient support for numerical computing with powerful multi-dimensional array and matrix operations.

[Geojson](https://pypi.org/project/geojson/)

A Python package for working with data in the GeoJSON format, which is used to represent geographic features such as points, lines, and polygons.

[Pandas](https://pandas.pydata.org)

A Python library for data manipulation and analysis, offering powerful tools for working with structured data like tables and time series.

[Geopandas](https://geopandas.org/en/stable/getting_started/introduction.html)

A Python library that extends pandas to support spatial data, making it easy to work with geographic datasets like shapefiles and GeoJSON.

[Shapely](https://shapely.readthedocs.io/en/stable/manual.html)

A Python library for creating, analyzing, and manipulating geometric objects such as points, lines, and polygons.

[Cdsapi](https://pypi.org/project/cdsapi/)

A Python client library for accessing and downloading data from the Copernicus Climate Data Store (CDS) via its API.

[xarray](https://pypi.org/project/xarray/)

A Python library for working with labeled multi-dimensional arrays, designed for analyzing and processing structured data such as NetCDF files.

[rioxarray](https://pypi.org/project/rioxarray/)

A Python library that extends xarray with geospatial features powered by [rasterio](https://rasterio.readthedocs.io/en/latest/index.html)

[NetCDF4](https://pypi.org/project/netCDF4/)

A Python library for reading and writing NetCDF files, commonly used for storing multi-dimensional scientific data such as climate and weather variables.

[OWSLib](https://pypi.org/project/OWSLib/)

A Python library for accessing and interacting with Open Geospatial Consortium (OGC) web services such as WMS, WFS, and WCS.

[IPykernel](https://pypi.org/project/ipykernel/)

A Python library that provides the Jupyter kernel for executing Python code in Jupyter notebooks and other interactive environments.

[ipywidgets](https://pypi.org/project/ipywidgets/) 

A Python library that enables interactive widgets in Jupyter notebook and the IPython kernel.

[Matplotlib](https://matplotlib.org/stable/index.html)

A Python library for creating static, animated, and interactive visualizations.

[Django Rest Framework](https://pypi.org/project/djangorestframework/)

A Python toolkit for building Web APIs.

filelock
seaborn
scikit-image
beautifulsoup4
h5netcdf
rasterstats
glob2
bs4
snakemake

## Usage policies

All data integrated by CLUES are open-access and publicly available. However, users must comply with the usage terms of each primary data source. Each dataset is subject to its own licensing and access policies. Please ensure you review and follow these terms before using the data in research.

## License
MIT License

Copyright (c) 2025 BIH-DMBS 
