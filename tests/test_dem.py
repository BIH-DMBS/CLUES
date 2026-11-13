"""
Tests for the Copernicus DEM download (utils/copernicusDEM.py) and the neighbourhood
filters (utils/filter_neighborhood.py).

No network access is needed, the tiles are small synthetic rasters.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import rasterio
from rasterio.transform import from_origin

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import copernicusDEM  # noqa: E402
import filter_neighborhood as fn  # noqa: E402


def tile_name(lon, lat):
    ns, ew = ('N' if lat >= 0 else 'S'), ('E' if lon >= 0 else 'W')
    return f"Copernicus_DSM_COG_30_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM.tif"


def write_tile(folder, lon, lat, columns, rows, elevation):
    """
    Write a synthetic 1 degree tile with its lower left corner at (lon, lat).
    elevation: function (longitude, latitude) -> metres, evaluated at the pixel centres.
    """
    xres, yres = 1.0 / columns, 1.0 / rows
    lons = lon + (np.arange(columns) + 0.5) * xres
    lats = lat + 1 - (np.arange(rows) + 0.5) * yres
    data = elevation(*np.meshgrid(lons, lats)).astype('float32')
    path = os.path.join(folder, tile_name(lon, lat))
    with rasterio.open(path, 'w', driver='GTiff', height=rows, width=columns, count=1, dtype='float32',
                       crs='EPSG:4326', transform=from_origin(lon, lat + 1, xres, yres)) as dst:
        dst.write(data, 1)
    return path, data


def read(path):
    with rasterio.open(path) as src:
        return src.read(1)


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name


class TestGeometry(unittest.TestCase):
    def test_pixel_size_of_one_degree(self):
        dx, dy = fn.pixel_size_m(0.0, 1.0, 1.0)
        self.assertAlmostEqual(dx, 111319.5, delta=1)
        self.assertAlmostEqual(dy, 110574.3, delta=1)
        dx60, _ = fn.pixel_size_m(60.0, 1.0, 1.0)
        self.assertAlmostEqual(dx60, 55800.0, delta=10)

    def test_tile_position_from_file_name(self):
        self.assertEqual(fn.extract_coordinates(tile_name(13, 53)), (13, 53))
        self.assertEqual(fn.extract_coordinates(tile_name(-58, 5)), (-58, 5))
        self.assertEqual(fn.extract_coordinates(tile_name(13, -4)), (13, -4))
        self.assertEqual(fn.extract_coordinates(tile_name(-70, -33)), (-70, -33))
        self.assertIsNone(fn.extract_coordinates('something_else.tif'))

    def test_kernel_is_a_circle_in_metres(self):
        kernel = fn.elliptical_kernel(250, 100, 100)
        self.assertEqual(kernel.shape, (5, 5))
        self.assertEqual(int(kernel.sum()), 21)  # all 5x5 pixels except the four corners
        # pixels half as wide: twice as many columns are needed for the same distance
        self.assertEqual(fn.elliptical_kernel(250, 50, 100).shape, (5, 11))


class TestSlopeAspect(unittest.TestCase):
    def plane(self, rise_east, rise_north, size=6, step=100.0):
        # elevation including the margin of one pixel, row 0 is north
        jj, ii = np.meshgrid(np.arange(size + 2), np.arange(size + 2))
        return rise_east * step * jj - rise_north * step * ii

    def test_plane_rising_to_the_east_faces_west(self):
        slope, aspect = fn.slope_aspect(self.plane(0.1, 0.0), 100.0, 100.0)
        np.testing.assert_allclose(slope, np.degrees(np.arctan(0.1)))
        np.testing.assert_allclose(aspect, 270.0)

    def test_plane_rising_to_the_north_faces_south(self):
        slope, aspect = fn.slope_aspect(self.plane(0.0, 1.0), 100.0, 100.0)
        np.testing.assert_allclose(slope, 45.0)
        np.testing.assert_allclose(aspect, 180.0)

    def test_plane_rising_to_the_south_west_faces_north_east(self):
        _, aspect = fn.slope_aspect(self.plane(-0.2, -0.2), 100.0, 100.0)
        np.testing.assert_allclose(aspect, 45.0)

    def test_flat_area_has_no_aspect(self):
        slope, aspect = fn.slope_aspect(np.full((8, 8), 12.0), 100.0, 100.0)
        np.testing.assert_allclose(slope, 0.0)
        self.assertTrue(np.isnan(aspect).all())

    def test_pixel_size_in_metres_is_used(self):
        # same elevations, pixels twice as wide: half the slope in east-west direction
        slope, _ = fn.slope_aspect(self.plane(0.1, 0.0, step=100.0), 200.0, 100.0)
        np.testing.assert_allclose(slope, np.degrees(np.arctan(0.05)))

    def test_missing_margin_gives_the_same_result_for_a_plane(self):
        data = self.plane(0.1, 0.3)
        expected = fn.slope_aspect(data, 100.0, 100.0)
        data[0, :] = data[-1, :] = data[:, 0] = data[:, -1] = np.nan
        slope, aspect = fn.slope_aspect(data, 100.0, 100.0)
        np.testing.assert_allclose(slope, expected[0])
        np.testing.assert_allclose(aspect, expected[1])


class TestMeanStd(unittest.TestCase):
    def brute_force(self, data, kernel, i, j):
        ry, rx = kernel.shape[0] // 2, kernel.shape[1] // 2
        values = []
        for di in range(-ry, ry + 1):
            for dj in range(-rx, rx + 1):
                if kernel[di + ry, dj + rx] and 0 <= i + di < data.shape[0] and 0 <= j + dj < data.shape[1]:
                    if np.isfinite(data[i + di, j + dj]):
                        values.append(data[i + di, j + dj])
        return (np.mean(values), np.std(values)) if values else (np.nan, np.nan)

    def test_against_brute_force_with_missing_values(self):
        rng = np.random.default_rng(1)
        data = rng.normal(1500, 300, (40, 50))
        data[rng.random(data.shape) < 0.2] = np.nan
        data[:6, :9] = np.nan  # a larger hole, some pixels have no valid neighbour at all
        kernel = fn.elliptical_kernel(250, 80, 100)
        mean, std = fn.neighbourhood_mean_std(data, kernel)
        for i in range(0, 40, 3):
            for j in range(0, 50, 3):
                expected_mean, expected_std = self.brute_force(data, kernel, i, j)
                np.testing.assert_allclose(mean[i, j], expected_mean, rtol=1e-9, atol=1e-6, equal_nan=True)
                np.testing.assert_allclose(std[i, j], expected_std, rtol=1e-6, atol=1e-4, equal_nan=True)
        self.assertTrue(np.isnan(mean[0, 0]) and np.isnan(std[0, 0]))

    def test_constant_elevation_has_zero_standard_deviation(self):
        mean, std = fn.neighbourhood_mean_std(np.full((30, 30), 2345.678), fn.elliptical_kernel(500, 90, 90))
        np.testing.assert_allclose(mean, 2345.678)
        self.assertFalse(np.isnan(std).any())
        np.testing.assert_allclose(std, 0.0, atol=1e-6)


class TestTilesWithNeighbours(TempDirTest):
    @staticmethod
    def elevation(lon, lat):
        return 100.0 * lon + 250.0 * lat  # a plane, so resampled values can be predicted exactly

    def setUp(self):
        super().setUp()
        # centre tile and its neighbours in the same latitude zone (40 columns) ...
        self.centre_path, self.centre = write_tile(self.dir, 13, 52, 40, 60, self.elevation)
        _, self.north = write_tile(self.dir, 13, 53, 40, 60, self.elevation)
        _, self.west = write_tile(self.dir, 12, 52, 40, 60, self.elevation)
        # ... and a southern neighbour of another zone with wider tiles (60 columns)
        write_tile(self.dir, 13, 51, 60, 60, self.elevation)
        self.tiles = fn.index_tiles(fn.list_tif_files(self.dir), self.dir)

    def test_margin_comes_from_the_right_neighbours(self):
        data, _ = fn.read_with_margin(self.tiles, (13, 52), 5, 7)
        self.assertEqual(data.shape, (60 + 14, 40 + 10))
        np.testing.assert_array_equal(data[7:-7, 5:-5], self.centre)
        np.testing.assert_allclose(data[:7, 5:-5], self.north[-7:, :], atol=1e-2)   # north: its bottom rows
        np.testing.assert_allclose(data[7:-7, :5], self.west[:, -5:], atol=1e-2)    # west: its right columns
        self.assertTrue(np.isnan(data[7:-7, -5:]).all())                              # east: no tile

    def test_neighbour_with_other_pixel_width_is_resampled(self):
        data, _ = fn.read_with_margin(self.tiles, (13, 52), 5, 7)
        lons = 13 + (np.arange(40) + 0.5) / 40
        lats = 52 - (np.arange(7) + 0.5) / 60
        expected = self.elevation(*np.meshgrid(lons, lats))
        # compare away from the left/right end, where the plane cannot be interpolated
        np.testing.assert_allclose(data[-7:, 5:-5][:, 2:-2], expected[:, 2:-2], atol=0.5)

    def test_results_have_no_seam_at_the_tile_border(self):
        # a field that is not a plane, as two tiles and as one piece
        def hills(lon, lat):
            return 500 + 200 * np.sin(lon * 40) * np.cos(lat * 55)
        folder = os.path.join(self.dir, 'seam')
        os.makedirs(folder)
        _, left = write_tile(folder, 10, 52, 40, 60, hills)
        _, right = write_tile(folder, 11, 52, 40, 60, hills)
        whole = np.hstack([left, right])
        tiles = fn.index_tiles(fn.list_tif_files(folder), folder)

        kernel = fn.elliptical_kernel(9000, *[float(v) for v in fn.pixel_size_m(52.5, 1 / 40, 1 / 60)])
        margin_y, margin_x = kernel.shape[0] // 2, kernel.shape[1] // 2
        self.assertGreater(margin_x, 2)
        expected_mean, expected_std = fn.neighbourhood_mean_std(whole, kernel)

        data, _ = fn.read_with_margin(tiles, (10, 52), margin_x, margin_y)
        mean, std = fn.neighbourhood_mean_std(data, kernel)
        mean = mean[margin_y:-margin_y, margin_x:-margin_x]
        std = std[margin_y:-margin_y, margin_x:-margin_x]
        # all columns of the left tile next to the border agree with the computation in one piece
        np.testing.assert_allclose(mean[:, -margin_x:], expected_mean[:, 40 - margin_x:40], atol=1e-3)
        np.testing.assert_allclose(std[:, -margin_x:], expected_std[:, 40 - margin_x:40], atol=1e-3)

    def run_filter(self, mode):
        out = os.path.join(self.dir, 'out_' + mode)
        with mock.patch.object(fn, 'download_folder', self.dir):
            config = os.path.join(self.dir, 'dem.json')
            os.makedirs(os.path.join(self.dir, 'DEM', 'dem_test'), exist_ok=True)
            for f in fn.list_tif_files(self.dir):
                os.replace(os.path.join(self.dir, f), os.path.join(self.dir, 'DEM', 'dem_test', f))
            with open(config, 'w') as f:
                json.dump({'type': 'DEM', 'variables': [{'name': 'dem_test'}]}, f)
            fn.compute_neighborhood(config, 'dem_test', mode)
        return os.path.join(self.dir, 'neigborhoods', 'DEM', 'dem_test', mode)

    def test_compute_neighborhood_writes_slope_and_aspect(self):
        out = self.run_filter('zevenbergen_thorne')
        files = sorted(os.listdir(out))
        self.assertEqual(len(files), 4 * 2 + 1)
        self.assertIn('done.txt', files)
        slope = read(os.path.join(out, 'slope_' + tile_name(13, 52)))
        aspect = read(os.path.join(out, 'aspect_' + tile_name(13, 52)))
        # plane rising 100 m per degree east and 250 m per degree north: gentle slope facing south-south-west
        dx, dy = fn.pixel_size_m(52.5, 1.0, 1.0)
        expected_slope = np.degrees(np.arctan(np.hypot(100 / dx, 250 / dy)))
        expected_aspect = np.degrees(np.arctan2(-100 / dx, -250 / dy)) % 360
        np.testing.assert_allclose(slope[30, 20], expected_slope, rtol=1e-3)
        np.testing.assert_allclose(aspect[30, 20], expected_aspect, atol=0.1)
        self.assertTrue(180 < expected_aspect < 270)
        # no jump at the border to the northern neighbour and at the border without neighbour
        np.testing.assert_allclose(slope[0, 20], slope[30, 20], rtol=2e-2)
        np.testing.assert_allclose(slope[30, -1], slope[30, 20], rtol=2e-2)

    def test_compute_neighborhood_writes_mean(self):
        out = self.run_filter('mean_radius_5000')
        name = f"mean_{tile_name(13, 52)}_5000.tif"
        self.assertIn(name, os.listdir(out))
        mean = read(os.path.join(out, name))
        # the mean of a plane over a symmetric neighbourhood is the value at the centre
        np.testing.assert_allclose(mean[30, 20], self.centre[30, 20], atol=0.05)
        np.testing.assert_allclose(mean[0, 20], self.centre[0, 20], atol=0.05)  # at the border to the north

    def test_unknown_filter_is_an_error(self):
        with self.assertRaises(ValueError):
            self.run_filter('median_radius_500')


class FakeResponse:
    def __init__(self, status_code, content=b''):
        self.status_code = status_code
        self.content = content
        self.headers = {'Content-Length': str(len(content))}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise copernicusDEM.requests.HTTPError(f"status {self.status_code}")

    def iter_content(self, chunk_size):
        yield self.content


class FakeSession:
    """Tiles east of 13 E do not exist (sea), all others have 100 bytes."""
    def __init__(self, fail=False):
        self.fail = fail
        self.urls = []

    def get(self, url, stream=True, timeout=None):
        self.urls.append(url)
        if self.fail:
            return FakeResponse(500)
        lon = int(url.split('_E')[-1][:3])
        return FakeResponse(404) if lon > 13 else FakeResponse(200, b'x' * 100)


class TestDownload(TempDirTest):
    def setUp(self):
        super().setUp()
        self.config = os.path.join(REPO, 'configs_sources', 'copernicus_dem.json')
        self.folder = os.path.join(self.dir, 'DEM', 'Digital_Geospatial_Elevation_Data_90m')
        self.session = FakeSession()
        for name, value in {'download_folder': self.dir, 'area': 'Berlin',
                            'config_folder': os.path.join(REPO, 'config')}.items():
            patcher = mock.patch.object(copernicusDEM, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(copernicusDEM, 'get_session', lambda: self.session)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(copernicusDEM.time, 'sleep', lambda seconds: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def download(self):
        copernicusDEM.getInfoCopenicusDEM(self.config, 'Digital_Geospatial_Elevation_Data_90m')

    def test_tiles_of_a_bbox(self):
        # Berlin [52.7136, 12.9673, 52.2839, 13.816] lies in two tiles
        self.assertEqual(copernicusDEM.generate_tiles([52.7136, 12.9673, 52.2839, 13.816]), [(52, 12), (52, 13)])
        self.assertEqual(copernicusDEM.generate_tiles([1.5, -1.5, -1.5, 1.5]),
                         [(-2, -2), (-2, -1), (-2, 0), (-2, 1), (-1, -2), (-1, -1), (-1, 0), (-1, 1),
                          (0, -2), (0, -1), (0, 0), (0, 1), (1, -2), (1, -1), (1, 0), (1, 1)])

    def test_tile_url(self):
        url, name = copernicusDEM.tile_url(53, 13, '30', 'https://copernicus-dem-30m.s3.amazonaws.com')
        self.assertEqual(name, 'Copernicus_DSM_COG_10_N53_00_E013_00_DEM.tif')
        self.assertEqual(url, 'https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N53_00_E013_00_DEM/'
                              'Copernicus_DSM_COG_10_N53_00_E013_00_DEM.tif')
        self.assertEqual(copernicusDEM.tile_url(-4, -58, '90', 'https://b/')[1],
                         'Copernicus_DSM_COG_30_S04_00_W058_00_DEM.tif')

    def test_area_is_widened_by_the_largest_filter_radius(self):
        self.assertEqual(copernicusDEM.max_neighborhood_radius({'neighborhood': {'mean': [500, 1000], 'std': [2000],
                                                                                 'zevenbergen_thorne': 'yes'}}), 2000)
        self.assertEqual(copernicusDEM.max_neighborhood_radius({}), 0)
        bbox = [53.0, 13.0, 52.5, 13.5]
        self.assertEqual(copernicusDEM.pad_bbox_m(bbox, 0), bbox)
        padded = copernicusDEM.pad_bbox_m(bbox, 1000)
        self.assertAlmostEqual(padded[0], 53.009, places=3)
        self.assertAlmostEqual(padded[1], 13.0 - 0.009 / np.cos(np.radians(53.009)), places=3)
        # the bbox ends exactly at a tile border, with the margin the tiles beyond are included
        self.assertEqual(len(copernicusDEM.generate_tiles(bbox)), 1)
        self.assertEqual(len(copernicusDEM.generate_tiles(padded)), 4)

    def test_download_keeps_available_tiles_only(self):
        self.download()
        self.assertEqual(sorted(os.listdir(self.folder)), [
            'Copernicus_DSM_COG_30_N52_00_E012_00_DEM.tif', 'Copernicus_DSM_COG_30_N52_00_E013_00_DEM.tif', 'done.txt'])
        with open(os.path.join(self.folder, 'done.txt')) as f:
            self.assertIn('2 tiles', f.read())

    def test_second_run_keeps_complete_tiles_and_removes_foreign_files(self):
        self.download()
        kept = os.path.join(self.folder, 'Copernicus_DSM_COG_30_N52_00_E013_00_DEM.tif')
        modified = os.path.getmtime(kept)
        broken = os.path.join(self.folder, 'Copernicus_DSM_COG_30_N52_00_E012_00_DEM.tif')
        with open(broken, 'wb') as f:
            f.write(b'x' * 10)  # an incomplete tile
        for foreign in ('Copernicus_DSM_COG_30_N10_00_E010_00_DEM.tif', 'leftover.tif.part'):
            with open(os.path.join(self.folder, foreign), 'wb') as f:
                f.write(b'old')
        self.download()
        self.assertEqual(len(os.listdir(self.folder)), 3)
        self.assertEqual(os.path.getmtime(kept), modified)
        self.assertEqual(os.path.getsize(broken), 100)

    def test_failed_download_is_an_error_and_writes_no_flag(self):
        self.session.fail = True
        with self.assertRaises(RuntimeError):
            self.download()
        self.assertEqual(os.listdir(self.folder), [])

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            copernicusDEM.getInfoCopenicusDEM(self.config, 'no_such_variable')


if __name__ == '__main__':
    unittest.main()
