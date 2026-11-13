"""
Tests for the MODIS vegetation index download (utils/modis.py).

No network access and no Earthdata login are needed: the Earthdata library and the reading of the
HDF files are replaced by fakes.
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
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import modis  # noqa: E402

CONFIG_NAME = 'modis_vegetation_indices.json'
ATTRIBUTES = {'_FillValue': -3000, 'valid_range': [-2000, 10000], 'scale_factor': 10000.0}
BRANDENBURG = [53.5587, 11.2682, 51.3618, 14.7636]


class TestToIndex(unittest.TestCase):
    def test_stored_numbers_are_divided_by_the_scale_factor(self):
        raw = np.array([[10000, 5340, 0, -500, -2000]], dtype='>i2')
        np.testing.assert_allclose(modis.to_index(raw, ATTRIBUTES), [[1.0, 0.534, 0.0, -0.05, -0.2]], rtol=1e-6)

    def test_fill_value_and_numbers_outside_the_valid_range_are_nan(self):
        raw = np.array([[-3000, -2001, 10001, 7000]], dtype='>i2')
        result = modis.to_index(raw, ATTRIBUTES)
        self.assertTrue(np.isnan(result[0, :3]).all())
        self.assertAlmostEqual(float(result[0, 3]), 0.7, places=6)

    def test_negative_index_values_are_kept(self):
        # water and snow have a negative NDVI, these are values and not missing data
        result = modis.to_index(np.array([[-800]], dtype='>i2'), ATTRIBUTES)
        self.assertAlmostEqual(float(result[0, 0]), -0.08, places=6)


class TestFileNames(unittest.TestCase):
    def test_tile_and_date(self):
        name = os.path.join('some.folder', 'MOD13A3.A2020032.h18v03.061.2020328134341.hdf')
        self.assertEqual(modis.tile_of(name), (18, 3))
        self.assertEqual(str(modis.date_of(name).date()), '2020-02-01')
        self.assertEqual(str(modis.date_of('MOD13A3.A2020336.h17v04.061.x.hdf').date()), '2020-12-01')


class TestGrid(unittest.TestCase):
    def test_tile_h18v03_lies_where_the_product_says(self):
        # the tile reaches from the Greenwich meridian (at its upper left corner) and 60 N to 50 N
        lons, lats = modis.grid_coordinates(18, 18, 3, 3, 1200)
        self.assertEqual(lats.shape, (1200, 1200))
        self.assertAlmostEqual(lats[0, 0], 60 - 10 / 1200 / 2, places=3)
        self.assertAlmostEqual(lats[-1, 0], 50 + 10 / 1200 / 2, places=3)
        self.assertGreater(lons[0, 0], 0)
        self.assertLess(lons[0, 0], 0.01)
        # the tile is 10 degree wide at the equator; further north the same width in metres spans more longitude
        self.assertAlmostEqual(lons[0, -1], 10 / np.cos(np.radians(60)), delta=0.05)    # 20 E at 60 N
        self.assertAlmostEqual(lons[-1, -1], 10 / np.cos(np.radians(50)), delta=0.05)   # 15.6 E at 50 N
        # rows are lines of equal latitude in the sinusoidal grid
        np.testing.assert_allclose(lats[100, :], lats[100, 0], rtol=0, atol=1e-9)

    def test_two_tiles_side_by_side_are_one_grid(self):
        lons, lats = modis.grid_coordinates(17, 18, 3, 3, 10)
        left, _ = modis.grid_coordinates(17, 17, 3, 3, 10)
        right, _ = modis.grid_coordinates(18, 18, 3, 3, 10)
        np.testing.assert_allclose(lons, np.hstack([left, right]))

    def test_part_of_the_grid_for_the_area(self):
        lons, lats = modis.grid_coordinates(18, 18, 3, 3, 1200)
        row_start, row_stop, col_start, col_stop = modis.rows_and_columns_of_bbox(lons, lats, BRANDENBURG, margin_in_pixel=0)
        part_lats, part_lons = lats[row_start:row_stop, col_start:col_stop], lons[row_start:row_stop, col_start:col_stop]
        self.assertLessEqual(part_lats.min(), 51.3618 + 0.01)
        self.assertGreaterEqual(part_lats.max(), 53.5587 - 0.01)
        self.assertLessEqual(part_lons.min(), 11.2682)
        self.assertGreaterEqual(part_lons.max(), 14.7636)
        self.assertLess((row_stop - row_start) * (col_stop - col_start), 1200 * 1200 / 10)  # far less than the tile

    def test_area_outside_of_the_tiles_is_an_error(self):
        lons, lats = modis.grid_coordinates(18, 18, 3, 3, 120)
        with self.assertRaises(RuntimeError):
            modis.rows_and_columns_of_bbox(lons, lats, [10, -60, 5, -55])


class TestGetModisVi(unittest.TestCase):
    """One tile (h18v03, 120 x 120 pixels instead of 1200 x 1200), two months."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = os.path.join(self.tmp.name, 'data')
        self.work = os.path.join(self.tmp.name, 'tmp')
        with open(os.path.join(REPO, 'configs_sources', CONFIG_NAME), encoding='utf-8') as f:
            config = json.load(f)
        config['variables'][0]['tile_pixels'] = 120
        self.config = os.path.join(self.tmp.name, CONFIG_NAME)
        with open(self.config, 'w') as f:
            json.dump(config, f)
        self.file_names = ['MOD13A3.A2020001.h18v03.061.1.hdf', 'MOD13A3.A2020032.h18v03.061.1.hdf']
        self.searches = []
        self.login_failures = 0

        def fake_login(strategy=None):
            if self.login_failures > 0:
                self.login_failures -= 1
                raise TimeoutError('Read timed out')

        def fake_search(short_name=None, temporal=None, bounding_box=None):
            self.searches.append((short_name, temporal, bounding_box))
            return list(self.file_names)

        def fake_download(granules, local_path=None):
            for name in granules:
                with open(os.path.join(local_path, name), 'w') as f:
                    f.write('hdf')

        def fake_read(hdf_file, name):
            # stored numbers: January 2000 everywhere, February 4000; EVI is half of it; first row is fill
            month = 1 if '.A2020001.' in hdf_file else 2
            raw = np.full((120, 120), 2000 * month // (2 if 'EVI' in name else 1), dtype='>i2')
            raw[0, :] = -3000
            raw[60, 60] = -500
            return raw, dict(ATTRIBUTES)

        for obj, name, value in ((modis, 'download_folder', self.data), (modis, 'tmp_folder', self.work),
                                 (modis, 'read_sds', fake_read), (modis, 'sleep', lambda seconds: None),
                                 (modis.earthaccess, 'login', fake_login), (modis.earthaccess, 'search_data', fake_search),
                                 (modis.earthaccess, 'download', fake_download),
                                 (modis.utils, 'config_folder', os.path.join(REPO, 'config')), (modis.utils, 'area', 'Brandenburg')):
            patcher = mock.patch.object(obj, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def output(self, index):
        return os.path.join(self.data, 'MODIS_Vegetation_Index_Products', 'MOD13A3', index, '2020.nc')

    def test_both_indices_are_written_with_correct_values(self):
        modis.get_modis_vi(self.config, 'MOD13A3', '1_km_monthly_NDVI', '2020')
        self.assertEqual(self.searches, [('MOD13A3', ('2020-01-01', '2020-12-31'), (11.2682, 51.3618, 14.7636, 53.5587))])
        with xr.open_dataset(self.output('1_km_monthly_NDVI')) as ds:
            self.assertEqual([str(t)[:10] for t in ds.time.values], ['2020-01-01', '2020-02-01'])
            ndvi = ds['1 km monthly NDVI'].values
            self.assertEqual(ndvi.dtype, np.float32)
            self.assertAlmostEqual(float(np.nanmax(ndvi[0])), 0.2, places=6)
            self.assertAlmostEqual(float(np.nanmax(ndvi[1])), 0.4, places=6)
            self.assertEqual(ds['Latitude'].shape, ndvi.shape[1:])
            # the file holds the area only, not the complete tile
            self.assertLess(ndvi.shape[1] * ndvi.shape[2], 120 * 120 / 5)
            self.assertLessEqual(float(ds['Latitude'].min()), 51.3618 + 0.1)
            self.assertGreaterEqual(float(ds['Latitude'].max()), 53.5587 - 0.1)
        with xr.open_dataset(self.output('1_km_monthly_EVI')) as ds:
            self.assertAlmostEqual(float(np.nanmax(ds['1 km monthly EVI'].values[1])), 0.2, places=6)
            self.assertIn('EVI', ds['1 km monthly EVI'].attrs['long_name'])
        self.assertFalse(os.path.exists(os.path.join(self.work, 'MOD13A3', '2020')))  # temporary files removed

    def test_login_is_tried_again_after_a_time_out(self):
        self.login_failures = 2
        modis.get_modis_vi(self.config, 'MOD13A3', '1_km_monthly_NDVI', '2020')
        self.assertTrue(os.path.exists(self.output('1_km_monthly_NDVI')))

    def test_login_that_keeps_failing_is_an_error_and_leaves_no_file(self):
        self.login_failures = 10
        with self.assertRaises(TimeoutError):
            modis.get_modis_vi(self.config, 'MOD13A3', '1_km_monthly_NDVI', '2020')
        self.assertFalse(os.path.exists(self.output('1_km_monthly_NDVI')))

    def test_no_data_for_the_year_is_an_error(self):
        self.file_names = []
        with self.assertRaises(RuntimeError):
            modis.get_modis_vi(self.config, 'MOD13A3', '1_km_monthly_NDVI', '2020')

    def test_file_of_another_year_is_an_error(self):
        self.file_names = ['MOD13A3.A2019335.h18v03.061.1.hdf']
        with self.assertRaises(RuntimeError):
            modis.get_modis_vi(self.config, 'MOD13A3', '1_km_monthly_NDVI', '2020')
        self.assertFalse(os.path.exists(self.output('1_km_monthly_NDVI')))

    def test_unknown_product_or_index_is_an_error(self):
        with self.assertRaises(ValueError):
            modis.get_modis_vi(self.config, 'MOD13Q1', '1_km_monthly_NDVI', '2020')
        with self.assertRaises(ValueError):
            modis.get_modis_vi(self.config, 'MOD13A3', 'no_such_index', '2020')
        self.assertEqual(self.searches, [])


class TestModisConfig(unittest.TestCase):
    def test_the_three_config_copies_agree_except_for_the_variables(self):
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
                config = json.load(f)
            config.pop('variables')
            headers.append(config)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])
        self.assertEqual(headers[0]['format'], 'netcdf')


if __name__ == '__main__':
    unittest.main()
