"""
Tests for the World Settlement Footprint download (utils/wsf.py).

No network access is needed, the tiles are small synthetic rasters.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import rasterio
from rasterio.transform import from_origin

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import wsf  # noqa: E402

CONFIG_NAME = 'EOC_WSF.json'
RES = 0.01        # pixel size of the synthetic tiles in degree
OVERLAP = 2       # pixels a tile reaches into its neighbours, as the real tiles do


def value_at(lon, lat):
    # synthetic content that depends on the position only, never 0
    # lon, lat are pixel centres (k + 0.5 pixels), floor gives the pixel index k without rounding trouble
    return (np.floor(lon / RES).astype(int) * 7 + np.floor(lat / RES).astype(int) * 3) % 200 + 1


def write_tile(folder, lon, lat):
    size = int(round(wsf.TILE_SIZE_DEG / RES)) + 2 * OVERLAP
    west, north = lon - OVERLAP * RES, lat + wsf.TILE_SIZE_DEG + OVERLAP * RES
    lons = west + (np.arange(size) + 0.5) * RES
    lats = north - (np.arange(size) + 0.5) * RES
    data = value_at(*np.meshgrid(lons, lats)).astype('uint8')
    path = os.path.join(folder, f'tile_{lon}_{lat}.tif')
    with rasterio.open(path, 'w', driver='GTiff', width=size, height=size, count=1, dtype='uint8',
                       crs='EPSG:4326', transform=from_origin(west, north, RES, RES)) as dst:
        dst.write(data, 1)
    return path


class TestTilesOfBbox(unittest.TestCase):
    def test_brandenburg_needs_six_tiles(self):
        # [lat_max, lon_min, lat_min, lon_max]; the tiles reach 2 degree to the east and north of their corner
        self.assertEqual(wsf.tiles_of_bbox([53.5587, 11.2682, 51.3618, 14.7636]),
                         [(10, 50), (12, 50), (14, 50), (10, 52), (12, 52), (14, 52)])

    def test_berlin_lies_in_one_tile(self):
        self.assertEqual(wsf.tiles_of_bbox([52.7136, 12.9673, 52.2839, 13.816]), [(12, 52)])

    def test_box_on_tile_borders_needs_that_tile_only(self):
        self.assertEqual(wsf.tiles_of_bbox([54, 12, 52, 14]), [(12, 52)])

    def test_western_and_southern_hemisphere(self):
        self.assertEqual(wsf.tiles_of_bbox([-1.5, -58.1, -3.5, -55.9]),
                         [(-60, -4), (-58, -4), (-56, -4), (-60, -2), (-58, -2), (-56, -2)])

    def test_every_point_of_the_box_is_covered(self):
        rng = np.random.default_rng(0)
        for _ in range(200):
            lon_min, lat_min = rng.uniform(-170, 160), rng.uniform(-55, 60)
            lon_max, lat_max = lon_min + rng.uniform(0.01, 9), lat_min + rng.uniform(0.01, 9)
            tiles = wsf.tiles_of_bbox([lat_max, lon_min, lat_min, lon_max])
            for lon, lat in ((lon_min, lat_min), (lon_max, lat_max), (lon_min, lat_max), (lon_max, lat_min)):
                self.assertTrue(any(t[0] <= lon <= t[0] + 2 and t[1] <= lat <= t[1] + 2 for t in tiles))
            # no tile that lies completely outside of the box
            for t in tiles:
                self.assertTrue(t[0] < lon_max and t[0] + 2 > lon_min and t[1] < lat_max and t[1] + 2 > lat_min)


class TestTileUrl(unittest.TestCase):
    def test_placeholders_are_filled(self):
        variable = {'url': 'https://example.invalid/WSF2015/files/', 'tile': 'WSF2015_v2_{lon}_{lat}/WSF2015_v2_{lon}_{lat}.tif'}
        self.assertEqual(wsf.tile_url(variable, -100, 16),
                         ('https://example.invalid/WSF2015/files/WSF2015_v2_-100_16/WSF2015_v2_-100_16.tif', 'WSF2015_v2_-100_16.tif'))


class TestMergeTiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def merge(self, corners, bbox):
        tiles = [write_tile(self.tmp.name, lon, lat) for lon, lat in corners]
        target = os.path.join(self.tmp.name, 'merged.tif')
        wsf.merge_tiles(tiles, bbox, target, margin_in_pixel=3)
        with rasterio.open(target) as src:
            data = src.read(1)
            lons = src.bounds.left + (np.arange(src.width) + 0.5) * src.res[0]
            lats = src.bounds.top - (np.arange(src.height) + 0.5) * src.res[1]
            return data, lons, lats, src.bounds

    def test_pixels_are_copied_unchanged_across_four_tiles(self):
        bbox = [52.9, 11.3, 51.2, 12.8]  # around the common corner (12, 52) of four tiles
        data, lons, lats, bounds = self.merge([(10, 50), (12, 50), (10, 52), (12, 52)], bbox)
        np.testing.assert_array_equal(data, value_at(*np.meshgrid(lons, lats)))
        # the result covers the box, with a small margin and not the complete tiles
        self.assertLessEqual(bounds.left, 11.3)
        self.assertGreaterEqual(bounds.right, 12.8)
        self.assertLessEqual(bounds.bottom, 51.2)
        self.assertGreaterEqual(bounds.top, 52.9)
        self.assertGreater(bounds.left, 11.2)
        self.assertLess(bounds.top, 53.0)

    def test_missing_tile_is_zero(self):
        bbox = [52.9, 11.3, 51.2, 12.8]
        data, lons, lats, _ = self.merge([(10, 50), (12, 50), (10, 52)], bbox)  # no tile (12, 52)
        lon, lat = np.meshgrid(lons, lats)
        inside_missing = (lon > 12 + OVERLAP * RES) & (lat > 52 + OVERLAP * RES)
        self.assertTrue((data[inside_missing] == 0).all())
        np.testing.assert_array_equal(data[~inside_missing & ((lon < 12) | (lat < 52))],
                                      value_at(lon, lat)[~inside_missing & ((lon < 12) | (lat < 52))])


class TestDownloadWsf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        self.out = os.path.join(self.tmp.name, 'data', 'WordSettlementFootprint')
        self.tiles_tmp = os.path.join(self.tmp.name, 'tmp')
        self.urls = []
        self.missing = set()
        self.fail = False
        for name, value in {'download_folder': os.path.join(self.tmp.name, 'data'), 'tmp_folder': self.tiles_tmp,
                            'area': 'Brandenburg', 'config_folder': os.path.join(REPO, 'config'),
                            'download_tile': self.fake_download}.items():
            patcher = mock.patch.object(wsf, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_download(self, url, target):
        self.urls.append(url)
        if self.fail:
            raise RuntimeError(f"Failed to download {url}")
        lon, lat = [int(x) for x in os.path.basename(url)[:-4].split('_')[-2:]]
        if (lon, lat) in self.missing:
            return 'missing'
        shutil.move(write_tile(os.path.dirname(target), lon, lat), target)
        return 'downloaded'

    def test_wsf_2019_is_built_from_the_2019_tiles_of_the_area(self):
        wsf.download_wsf(self.config, 'WSF_2019')
        self.assertEqual(os.listdir(self.out), ['WSF_2019.tif'])
        self.assertEqual(len(self.urls), 6)
        self.assertIn('https://download.geoservice.dlr.de/WSF2019/files/WSF2019_v1_10_50.tif', self.urls)
        self.assertTrue(all('/WSF2019/' in u for u in self.urls))
        with rasterio.open(os.path.join(self.out, 'WSF_2019.tif')) as src:
            self.assertLessEqual(src.bounds.left, 11.2682)
            self.assertGreaterEqual(src.bounds.right, 14.7636)
            self.assertLessEqual(src.bounds.bottom, 51.3618)
            self.assertGreaterEqual(src.bounds.top, 53.5587)
            self.assertTrue((src.read(1) != 0).all())  # no gap anywhere in the area
        self.assertFalse(os.path.exists(os.path.join(self.tiles_tmp, 'wsf_WSF_2019')))  # tiles removed

    def test_each_product_uses_its_own_address(self):
        wsf.download_wsf(self.config, 'WSF_2015')
        self.assertIn('https://download.geoservice.dlr.de/WSF2015/files/WSF2015_v2_12_52/WSF2015_v2_12_52.tif', self.urls)
        self.urls.clear()
        wsf.download_wsf(self.config, 'WSF_Evo_1985_2015')
        self.assertIn('https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_v1_12_52.tif', self.urls)

    def test_tiles_without_settlement_are_skipped(self):
        self.missing = {(10, 50), (14, 52)}
        wsf.download_wsf(self.config, 'WSF_2019')
        self.assertEqual(os.listdir(self.out), ['WSF_2019.tif'])

    def test_no_tile_at_all_is_an_error_and_leaves_no_file(self):
        self.missing = {(lon, lat) for lon in (10, 12, 14) for lat in (50, 52)}
        with self.assertRaises(RuntimeError):
            wsf.download_wsf(self.config, 'WSF_2019')
        self.assertEqual(os.listdir(self.out), [])

    def test_failed_download_is_an_error_and_leaves_no_file(self):
        self.fail = True
        with self.assertRaises(RuntimeError):
            wsf.download_wsf(self.config, 'WSF_2019')
        self.assertEqual(os.listdir(self.out), [])

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            wsf.download_wsf(self.config, 'no_such_variable')


class TestWsfConfig(unittest.TestCase):
    def load(self, folder):
        with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
            return json.load(f)

    def test_every_product_has_its_own_address(self):
        variables = self.load('configs_sources')['variables']
        self.assertEqual([v['name'] for v in variables], ['WSF_2015', 'WSF_2019', 'WSF_Evo_1985_2015'])
        self.assertEqual(len({v['url'] for v in variables}), 3)
        for v, product in zip(variables, ('WSF2015', 'WSF2019', 'WSF_EVO')):
            self.assertIn(f'/{product}/files/', v['url'])
            self.assertIn('{lon}', v['tile'])
            self.assertIn('{lat}', v['tile'])
            self.assertEqual(v['flagFile'], v['name'] + '.tif')

    def test_the_three_config_copies_agree_except_for_the_variables(self):
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            config = self.load(folder)
            config.pop('variables')
            headers.append(config)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])


if __name__ == '__main__':
    unittest.main()
