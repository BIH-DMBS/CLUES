#!/usr/bin/env python3
"""Convert an ESPON indicator CSV + geometry.csv into a GeoPackage and metadata.json.

Usage example:
    python scripts/espon_to_gpkg.py \
        --indicator data/espon/Population_total_by_broad_age_group/Population_total_-_age_group_65.csv \
        --geometry data/espon/geometry.csv \
        --out Population_total_age65.gpkg \
        --metadata Population_total_age65.metadata.json

The script will:
 - read the attribute CSV and the geometry CSV (WKT in a `geometry` column),
 - merge them by `tunit_code`,
 - attempt to infer simple types for fields,
 - write a GeoPackage layer, and
 - write a small `metadata.json` sidecar with column types, CRS and provenance.

"""

from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Dict, Any


def infer_simple_type(series) -> str:
    """Map pandas dtype/values to simple types: integer, number, boolean, string."""
    try:
        import numpy as np
    except Exception:
        np = None

    # If the series is all nulls, call it string
    if series.dropna().shape[0] == 0:
        return "string"

    # Try integer
    try:
        coerced = series.dropna().astype(int)
        # If no exception, check that coercion round-trips
        return "integer"
    except Exception:
        pass

    # Try numeric
    try:
        import pandas as pd

        coerced = pd.to_numeric(series.dropna(), errors="coerce")
        if coerced.notna().all():
            return "number"
    except Exception:
        pass

    # Boolean detection
    vals = set([str(v).lower() for v in series.dropna().unique()])
    if vals.issubset({"true", "false", "0", "1", "t", "f"}):
        return "boolean"

    return "string"


def build_metadata(df, geometry_source: str, crs: str = "EPSG:4326", encoding: str = "utf-8") -> Dict[str, Any]:
    cols = []
    for col in df.columns:
        if col == "geometry":
            dtype = "geometry"
        else:
            dtype = infer_simple_type(df[col])
        cols.append({"name": col, "type": dtype})

    metadata = {
        "title": os.path.splitext(os.path.basename(geometry_source))[0],
        "crs": crs,
        "encoding": encoding,
        "columns": cols,
        "provenance": {"geometry_source": geometry_source},
    }
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert ESPON CSV + geometry to GeoPackage + metadata.json")
    parser.add_argument("--indicator", required=True, help="Path to indicator CSV file")
    parser.add_argument("--geometry", default="data/espon/geometry.csv", help="Path to geometry CSV with WKT in `geometry` column")
    parser.add_argument("--out", default=None, help="Output GeoPackage path (default: <indicator_basename>.gpkg)")
    parser.add_argument("--layer", default=None, help="Layer name inside GeoPackage (default: indicator code or filename)")
    parser.add_argument("--metadata", default=None, help="Output metadata.json path (default: <indicator_basename>.metadata.json)")
    parser.add_argument("--encoding", default="utf-8", help="File encoding for CSVs")
    parser.add_argument("--crs", default="EPSG:4326", help="CRS for geometries (default EPSG:4326)")
    args = parser.parse_args()

    # Import heavy/geospatial libs here so --help remains lightweight
    try:
        import pandas as pd
        import geopandas as gpd
        from shapely import wkt
    except Exception as e:
        logging.error("Missing dependency: %s", e)
        logging.error("Please install pandas, geopandas and shapely in your environment.")
        raise

    ind_path = args.indicator
    geom_path = args.geometry
    encoding = args.encoding

    df_attrs = pd.read_csv(ind_path, encoding=encoding)

    if "tunit_code" not in df_attrs.columns:
        logging.error("Indicator CSV does not contain `tunit_code` column. Found: %s", df_attrs.columns.tolist())
        raise SystemExit(1)

    df_geom = pd.read_csv(geom_path, encoding=encoding)
    if "geometry" not in df_geom.columns:
        logging.error("Geometry CSV must include a `geometry` column with WKT.")
        raise SystemExit(1)

    # Parse WKT into geometries
    df_geom["geometry"] = df_geom["geometry"].apply(lambda s: wkt.loads(s) if pd.notnull(s) else None)
    gdf_geom = gpd.GeoDataFrame(df_geom, geometry="geometry", crs=args.crs)

    merged = df_attrs.merge(gdf_geom[["tunit_code", "geometry"]], on="tunit_code", how="left")
    gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs=args.crs)

    # Try to coerce numeric columns where appropriate
    for col in list(gdf.columns):
        if col == "geometry":
            continue
        try:
            coerced = pd.to_numeric(gdf[col], errors="coerce")
            # if at least one non-null value and coerced is not all NaN, adopt numeric
            if coerced.notna().sum() > 0 and coerced.isna().sum() < gdf.shape[0]:
                gdf[col] = coerced
        except Exception:
            pass

    # Output paths default
    base = os.path.splitext(os.path.basename(ind_path))[0]
    out_gpkg = args.out or f"{base}.gpkg"
    layer = args.layer or base
    metadata_path = args.metadata or f"{base}.metadata.json"

    # Ensure output directory exists
    out_dir = os.path.dirname(out_gpkg) or "."
    os.makedirs(out_dir, exist_ok=True)

    # Write GeoPackage
    logging.info("Writing GeoPackage to %s (layer: %s)", out_gpkg, layer)
    gdf.to_file(out_gpkg, layer=layer, driver="GPKG")

    # Build metadata and write
    metadata = build_metadata(gdf, geometry_source=geom_path, crs=args.crs, encoding=encoding)
    metadata["title"] = base
    metadata["source_files"] = {"indicator": ind_path, "geometry": geom_path}

    with open(metadata_path, "w", encoding=encoding) as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False)

    logging.info("Wrote metadata to %s", metadata_path)
    print(f"Wrote: {out_gpkg}\nWrote: {metadata_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
