import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import sys
import numpy as np

def blur_locations(csv_path, output_path, buffer_meters=100, wsg_epsg=4326, metric_epsg=3857):
    """
    Blur point locations by adding a buffer around them.
    
    Args:
        csv_path: Path to input CSV with columns: ID, x, y
        output_path: Path to output CSV
        buffer_meters: Buffer radius in meters
        wsg_epsg: Original projection EPSG code (default: 4326 for WGS84)
        metric_epsg: Metric projection EPSG code (default: 3857 for Web Mercator)
    """
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create GeoDataFrame with original projection
    geometry = [Point(xy) for xy in zip(df['x'], df['y'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=f"EPSG:{wsg_epsg}")
    
    # Reproject to metric projection for accurate buffer
    gdf = gdf.to_crs(f"EPSG:{metric_epsg}")
    
    # Create buffer around each point
    gdf['geometry'] = gdf.geometry.buffer(buffer_meters)
    
    # Get centroid for blurred location (within buffer)
    gdf['blurred_x'] = gdf.geometry.centroid.x
    gdf['blurred_y'] = gdf.geometry.centroid.y
    
    # Reproject back to original projection
    gdf = gdf.to_crs(f"EPSG:{wsg_epsg}")
    
    # Extract coordinates after reprojection
    gdf['blurred_x'] = gdf.geometry.centroid.x
    gdf['blurred_y'] = gdf.geometry.centroid.y
    
    # Save result
    result = gdf[['ID', 'blurred_x', 'blurred_y']].copy()
    result.to_csv(output_path, index=False)
    print(f"Blurred locations saved to {output_path}")

def create_example_csv(output_path="example_locations.csv"):
    """Generate example CSV with random points."""
    np.random.seed(42)
    n_points = 10
    df = pd.DataFrame({
        'ID': range(1, n_points + 1),
        'x': np.random.uniform(-180, 180, n_points),
        'y': np.random.uniform(-90, 90, n_points)
    })
    df.to_csv(output_path, index=False)
    print(f"Example CSV created: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python blurr_locations.py <input_csv> [output_csv] [buffer_meters]")
        print("       python blurr_locations.py --example")
        sys.exit(1)
    
    if sys.argv[1] == "--example":
        input_file = create_example_csv()
        output_file = "blurred_example.csv"
        blur_locations(input_file, output_file, 100)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "blurred_locations.csv"
        buffer = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        blur_locations(input_file, output_file, buffer)