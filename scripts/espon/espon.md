# ESPON Scripts Documentation

## Overview
This directory contains scripts for processing ESPON (European Spatial Planning Observation Network) geospatial data.

## Scripts

### espon_to_gpkg.py
Converts ESPON data formats to GeoPackage (.gpkg) format.

**Purpose:** Transform ESPON datasets into a standard GeoPackage database for easier integration and analysis.

**Key Features:**
- Reads ESPON source files
- Validates geospatial data
- Exports to GeoPackage format

**Usage:**
```bash
python espon_to_gpkg.py [input_file] [output_file.gpkg]
```

---

### geolocation_to_espon.py
Converts geolocation data into ESPON-compatible format.

**Purpose:** Transform standard geolocation datasets to align with ESPON data structures and requirements.

**Key Features:**
- Parses geolocation inputs
- Normalizes to ESPON schema
- Outputs ESPON-formatted data

**Usage:**
```bash
python geolocation_to_espon.py [input_file] [output_file]
```

---

## Requirements
Refer to `requirements.txt` for dependencies.

## Output Formats
- GeoPackage (.gpkg)
- ESPON standard formats