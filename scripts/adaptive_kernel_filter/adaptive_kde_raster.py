'''
Adaptive KDE Raster Script

Generates an adaptive kernel density estimate (KDE) from point data using scikit-learn.
If no input GeoTIFF is provided, a random point raster is created and saved.
Adaptive bandwidths are computed per point based on local density (k-nearest neighbors).
The resulting KDE is saved as a GeoTIFF.

Usage:

# Generate random raster, save it, and compute adaptive KDE
python adaptive_kde_raster.py

# Use an existing point raster
python adaptive_kde_raster.py --input my_points.tif --output kde_result.tif
'''

import numpy as np
import rasterio
from rasterio.transform import from_origin
from sklearn.neighbors import NearestNeighbors, KernelDensity
import argparse
import os

def generate_random_points_raster(width=100, height=100, num_points=200):
    """Generate a raster with random point occurrences (1 = point, 0 = background)"""
    raster = np.zeros((height, width), dtype=np.float32)
    ys = np.random.randint(0, height, num_points)
    xs = np.random.randint(0, width, num_points)
    raster[ys, xs] = 1
    return raster

def compute_adaptive_bandwidths(points, k=5):
    """Compute adaptive bandwidths based on distance to k-th nearest neighbor."""
    nbrs = NearestNeighbors(n_neighbors=k).fit(points)
    distances, _ = nbrs.kneighbors(points)
    bandwidths = distances[:, -1]  # Distance to k-th neighbor
    return bandwidths

def adaptive_kde(points, bandwidths, grid_size=(100,100), xlim=(0,100), ylim=(0,100)):
    """Perform adaptive KDE using scikit-learn."""
    X, Y = np.meshgrid(np.linspace(xlim[0], xlim[1], grid_size[0]),
                       np.linspace(ylim[0], ylim[1], grid_size[1]))
    grid_coords = np.vstack([X.ravel(), Y.ravel()]).T

    kde_sum = np.zeros(grid_coords.shape[0])
    for i, bw in enumerate(bandwidths):
        kde = KernelDensity(bandwidth=bw, kernel='gaussian')
        kde.fit(points[i:i+1])
        log_density = kde.score_samples(grid_coords)
        kde_sum += np.exp(log_density)

    return kde_sum.reshape(grid_size)

def save_raster(array, output_path, transform, crs='+proj=latlong', nodata=0):
    """Save a raster as GeoTIFF."""
    height, width = array.shape
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': 'float32',
        'crs': crs,
        'transform': transform,
        'nodata': nodata
    }
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(array.astype(np.float32), 1)
    print(f"Saved raster to {output_path}")

def main(input_tiff=None, output_tiff="adaptive_kde.tif"):
    # Step 1: Load raster or generate random points
    if input_tiff:
        with rasterio.open(input_tiff) as src:
            arr = src.read(1)
            transform = src.transform
            height, width = arr.shape
            xlim = (0, width)
            ylim = (0, height)
    else:
        arr = generate_random_points_raster()
        height, width = arr.shape
        transform = from_origin(0, height, 1, 1)  # arbitrary transform
        xlim = (0, width)
        ylim = (0, height)
        # Save the generated raster as GeoTIFF
        save_raster(arr, "random_points_input.tif", transform)

    # Step 2: Extract point coordinates
    ys, xs = np.where(arr > 0)
    points = np.vstack([xs, ys]).T

    # Step 3: Compute adaptive bandwidths
    bandwidths = compute_adaptive_bandwidths(points, k=5)

    # Step 4: Compute adaptive KDE
    kde_raster = adaptive_kde(points, bandwidths, grid_size=(height, width), xlim=xlim, ylim=ylim)

    # Step 5: Save adaptive KDE result as GeoTIFF
    save_raster(kde_raster, output_tiff, transform)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive KDE on raster points")
    parser.add_argument("--input", type=str, default=None, help="Input point raster GeoTIFF")
    parser.add_argument("--output", type=str, default="adaptive_kde.tif", help="Output KDE GeoTIFF")
    args = parser.parse_args()

    main(input_tiff=args.input, output_tiff=args.output)
