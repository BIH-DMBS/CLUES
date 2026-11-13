"""
Tests for the Copernicus tree cover density and forest type download (utils/treecover.py).

No network access is needed, the services are replaced by fakes.
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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import treecover  # noqa: E402

CONFIG_NAME = 'treecover_copernicus.json'
with open(os.path.join(REPO, 'configs_sources', CONFIG_NAME), encoding='utf-8') as f:
    CONFIG = json.load(f)
VARIABLES = {v['name']: v for v in CONFIG['variables']}


class TestAggregate(unittest.TestCase):
    def test_mean_of_the_valid_values(self):
        values = np.array([[10, 20, 100, 100],
                           [30, 40, 100, 255],
                           [255, 255, 0, 0],
                           [255, 255, 0, 1]], dtype=np.uint8)
        result = treecover.aggregate(values, 2, 'mean', max_valid=100)
        # 25 = mean of 10, 20, 30, 40; 100 = mean of the three valid values; 255 = no valid value; 0 = 0.25 rounded
        np.testing.assert_array_equal(result, [[25, 100], [255, 0]])
        self.assertEqual(result.dtype, np.uint8)

    def test_most_frequent_class(self):
        values = np.array([[1, 1, 2, 2],
                           [1, 0, 2, 255],
                           [0, 0, 255, 255],
                           [2, 1, 255, 255]], dtype=np.uint8)
        result = treecover.aggregate(values, 2, 'mode', max_valid=2)
        np.testing.assert_array_equal(result, [[1, 2], [0, 255]])

    def test_mean_is_exact_for_a_block_of_ten(self):
        rng = np.random.default_rng(0)
        values = rng.integers(0, 101, size=(30, 40)).astype(np.uint8)
        result = treecover.aggregate(values, 10, 'mean', max_valid=100)
        expected = np.rint(values.reshape(3, 10, 4, 10).mean(axis=(1, 3)))
        np.testing.assert_array_equal(result, expected)

    def test_unknown_method_is_an_error(self):
        with self.assertRaises(ValueError):
            treecover.aggregate(np.zeros((2, 2), dtype=np.uint8), 2, 'median', 100)


class TestReadTile(unittest.TestCase):
    def test_image_service_is_read_ten_times_finer_and_averaged(self):
        calls = []

        def fake_values(url, west, south, east, north, columns, rows, max_retries=4):
            calls.append((url, round(west, 4), round(south, 4), round(east, 4), round(north, 4), columns, rows))
            # 30 % everywhere, the western half of the tile 70 %
            values = np.full((rows, columns), 30, dtype=np.uint8)
            values[:, :columns // 2] = 70
            return values

        with mock.patch.object(treecover, 'request_values', fake_values):
            result = treecover.read_tile(VARIABLES['HRL_TreeCoverDensity_2018'], 13.0, 53.0, 100, 200, 4, 3, 0.001)
        self.assertEqual(calls, [(VARIABLES['HRL_TreeCoverDensity_2018']['url'], 13.1, 52.797, 13.104, 52.8, 40, 30)])
        np.testing.assert_array_equal(result, [[70, 70, 30, 30]] * 3)

    def test_map_service_colours_become_class_numbers(self):
        variable = VARIABLES['Tree_Cover_Density_classes_2015']
        colours = {entry['value']: entry['rgb'] for entry in variable['legend']}

        def fake_picture(url, layer, west, south, east, north, columns, rows, max_retries=4):
            self.assertEqual((url, layer), (variable['url'], '1'))
            picture = np.zeros((rows, columns, 4), dtype=np.uint8)   # transparent: no trees
            picture[0, 0] = colours[1] + [255]
            picture[0, 1] = colours[5] + [255]
            picture[1, 0] = colours[254] + [255]
            return picture

        with mock.patch.object(treecover.corine, 'request_picture', fake_picture):
            result = treecover.read_tile(variable, 13.0, 53.0, 0, 0, 3, 2, 0.001)
        np.testing.assert_array_equal(result, [[1, 5, 0], [254, 0, 0]])
        self.assertEqual(result.dtype, np.uint8)

    def test_colour_outside_of_the_legend_is_an_error(self):
        def fake_picture(url, layer, west, south, east, north, columns, rows, max_retries=4):
            picture = np.zeros((rows, columns, 4), dtype=np.uint8)
            picture[0, 0] = [1, 2, 3, 255]
            return picture

        with mock.patch.object(treecover.corine, 'request_picture', fake_picture):
            with self.assertRaises(RuntimeError):
                treecover.read_tile(VARIABLES['HRL_Forest_Type_2015_100m18936'], 13.0, 53.0, 0, 0, 3, 2, 0.001)


class TestGetTreecover(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        self.folder = os.path.join(self.tmp.name, 'treecover')
        self.requests = []
        self.fail = False

        def fake_values(url, west, south, east, north, columns, rows, max_retries=4):
            self.requests.append((columns, rows))
            if self.fail and len(self.requests) == 2:
                raise RuntimeError('service not reachable')
            # the density depends on the longitude only: 0 % at 12.9 E, rising by 1 % per 0.01 degree
            lons = west + (np.arange(columns) + 0.5) * (east - west) / columns
            return np.tile(np.clip(np.floor((lons - 12.9) * 100), 0, 100).astype(np.uint8), (rows, 1))

        for obj, name, value in ((treecover, 'download_folder', self.tmp.name), (treecover, 'area', 'Berlin'),
                                 (treecover, 'config_folder', os.path.join(REPO, 'config')),
                                 (treecover, 'request_values', fake_values)):
            patcher = mock.patch.object(obj, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_result_is_one_seamless_raster(self):
        treecover.get_treecover(self.config, 'HRL_TreeCoverDensity_2018')
        self.assertEqual(os.listdir(self.folder), ['HRL_TreeCoverDensity_2018.tif'])
        # Berlin at 0.001 degree: 849 x 431 pixels; 400 pixels per request (4000 values of the 10 m data)
        self.assertEqual(self.requests, [(4000, 4000), (4000, 4000), (490, 4000), (4000, 310), (4000, 310), (490, 310)])
        with rasterio.open(os.path.join(self.folder, 'HRL_TreeCoverDensity_2018.tif')) as src:
            self.assertEqual((src.count, src.dtypes[0], src.nodata, src.crs.to_epsg()), (1, 'uint8', 255, 4326))
            self.assertEqual((src.width, src.height), (849, 431))
            self.assertAlmostEqual(src.transform.c, 12.967)
            self.assertIn('percent', src.tags()['content'])
            data = src.read(1)
        lons = 12.967 + (np.arange(849) + 0.5) * 0.001
        np.testing.assert_array_equal(data[0], np.floor((lons - 12.9) * 100))
        self.assertTrue((data == data[0]).all())   # the same in every row, no seam between the requests

    def test_failed_request_leaves_no_file(self):
        self.fail = True
        with self.assertRaises(RuntimeError):
            treecover.get_treecover(self.config, 'HRL_TreeCoverDensity_2018')
        self.assertEqual(os.listdir(self.folder), [])

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            treecover.get_treecover(self.config, 'no_such_variable')


class TestTreecoverConfig(unittest.TestCase):
    def test_every_variable_says_how_it_is_read(self):
        self.assertEqual(len(VARIABLES), 6)
        for name, variable in VARIABLES.items():
            self.assertIn(variable['service_type'], ('ImageServer', 'MapServer'), name)
            self.assertTrue(variable['url'].endswith('/' + variable['service_type']), name)
            self.assertIn(variable['year'], name)
            if variable['service_type'] == 'ImageServer':
                self.assertIn(variable['aggregation'], ('mean', 'mode'), name)
            else:
                colours = [tuple(entry['rgb']) for entry in variable['legend']]
                self.assertEqual(len(colours), len(set(colours)), name)
                self.assertNotIn(0, [entry['value'] for entry in variable['legend']], name)

    def test_density_in_classes_is_named_as_classes(self):
        for name, variable in VARIABLES.items():
            if 'Density' in name and variable['service_type'] == 'MapServer':
                self.assertIn('classes', name)

    def test_the_three_config_copies_agree_except_for_the_variables(self):
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
                config = json.load(f)
            config.pop('variables')
            headers.append(config)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])


if __name__ == '__main__':
    unittest.main()
