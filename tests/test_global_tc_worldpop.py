"""
Tests for the global tree cover download (utils/global_tc.py) and the WorldPop download
(utils/worldPopDownload.py).

No network access is needed, the downloads are replaced by fakes.
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
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import global_tc  # noqa: E402
import worldPopDownload  # noqa: E402

BRANDENBURG = [53.5587, 11.2682, 51.3618, 14.7636]


class TestGlobalTreeCoverTiles(unittest.TestCase):
    def test_tiles_are_named_after_their_upper_left_corner(self):
        # Brandenburg lies in the tile that reaches from 60 N down to 50 N and from 10 E to 20 E
        self.assertEqual(global_tc.tiles_of_bbox(BRANDENBURG), [(60, 10)])

    def test_area_across_tile_borders(self):
        self.assertEqual(global_tc.tiles_of_bbox([5, -5, -5, 5]), [(10, -10), (10, 0), (0, -10), (0, 0)])

    def test_area_on_tile_borders_needs_that_tile_only(self):
        self.assertEqual(global_tc.tiles_of_bbox([60, 10, 50, 20]), [(60, 10)])

    def test_addresses(self):
        self.assertEqual(global_tc.tile_url_hansen('https://h/', 60, 10),
                         ('https://h/Hansen_GFC-2022-v1.10_treecover2000_60N_010E.tif', 'GFC_60N_010E.tif'))
        self.assertEqual(global_tc.tile_url_hansen('https://h/', -10, -70)[1], 'GFC_10S_070W.tif')
        self.assertEqual(global_tc.tile_url_2020('https://j/download.py?version=v2&type=tile', 60, 10),
                         ('https://j/download.py?version=v2&type=tile&lat=N60&lon=E10', 'GFC_N60_E10.tif'))
        self.assertEqual(global_tc.tile_url_2020('https://j/x', 0, -10)[0], 'https://j/x&lat=N0&lon=W10')


class TestGetTCGlobal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', 'treecover_global.json')
        self.folder = os.path.join(self.tmp.name, 'treecover_global', 'global_tree_cover_hansen_2000')
        self.urls = []
        self.status = 'downloaded'

        def fake_download(url, target):
            self.urls.append(url)
            if self.status == 'fails':
                raise RuntimeError(f"Failed to download {url}")
            if self.status == 'missing':
                return 'missing'
            with open(target, 'wb') as f:
                f.write(b'tile')
            return 'downloaded'

        for name, value in {'download_folder': self.tmp.name, 'area': 'Brandenburg',
                            'config_folder': os.path.join(REPO, 'config'), 'download_tile': fake_download}.items():
            patcher = mock.patch.object(global_tc, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_tiles_and_flag_file(self):
        global_tc.getTC_global(self.config, 'global_tree_cover_hansen_2000')
        self.assertEqual(self.urls, ['https://storage.googleapis.com/earthenginepartners-hansen/GFC-2022-v1.10/'
                                     'Hansen_GFC-2022-v1.10_treecover2000_60N_010E.tif'])
        self.assertEqual(sorted(os.listdir(self.folder)), ['GFC_60N_010E.tif', 'done.flag'])
        with open(os.path.join(self.folder, 'done.flag')) as f:
            self.assertIn('GFC_60N_010E.tif', f.read())

    def test_files_of_another_area_are_removed(self):
        os.makedirs(self.folder)
        for name in ('GFC_10N_000E.tif', 'GFC_60N_010E.tif.part'):
            with open(os.path.join(self.folder, name), 'wb') as f:
                f.write(b'old')
        global_tc.getTC_global(self.config, 'global_tree_cover_hansen_2000')
        self.assertEqual(sorted(os.listdir(self.folder)), ['GFC_60N_010E.tif', 'done.flag'])

    def test_failed_download_is_an_error_and_writes_no_flag(self):
        self.status = 'fails'
        with self.assertRaises(RuntimeError):
            global_tc.getTC_global(self.config, 'global_tree_cover_hansen_2000')
        self.assertNotIn('done.flag', os.listdir(self.folder))

    def test_no_tile_available_is_an_error_and_writes_no_flag(self):
        self.status = 'missing'
        with self.assertRaises(RuntimeError):
            global_tc.getTC_global(self.config, 'global_tree_cover_hansen_2000')
        self.assertNotIn('done.flag', os.listdir(self.folder))

    def test_forest_cover_2020_uses_its_own_addresses(self):
        global_tc.getTC_global(self.config, 'Global_forest_cover_2020')
        self.assertEqual(self.urls, ['https://ies-ows.jrc.ec.europa.eu/iforce/gfc2020/download.py?version=v2&type=tile&lat=N60&lon=E10'])

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            global_tc.getTC_global(self.config, 'no_such_variable')


class TestWorldPop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', 'worldPop.json')
        self.name = 'Est_total_people_per_gridcell_2025_alpha_release'
        self.folder = os.path.join(self.tmp.name, 'WordPop', self.name)
        self.calls = []
        self.empty = False

        def fake_wp_raster(product_name=None, aoi=None, years=None, masked=None):
            # the library is told to keep its downloads in a folder of the job, not in the home folder of the user
            self.calls.append({'product_name': product_name, 'aoi': aoi, 'years': years,
                               'cache_in_tmp': os.environ.get('WORLDPOPPY_CACHE_DIR', '').startswith(self.tmp.name)})
            data = np.full((1, 3, 4), np.nan if self.empty else 12.5, dtype='float32')
            array = xr.DataArray(data, dims=['year', 'y', 'x'],
                                 coords={'year': years, 'y': [52.75, 52.65, 52.55], 'x': [13.05, 13.15, 13.25, 13.35]})
            return array.rio.write_crs('EPSG:4326')

        for obj, name, value in ((worldPopDownload, 'download_folder', self.tmp.name), (worldPopDownload, 'wp_raster', fake_wp_raster),
                                 (worldPopDownload, 'tmp_folder', os.path.join(self.tmp.name, 'tmp')),
                                 (worldPopDownload.utils, 'config_folder', os.path.join(REPO, 'config')),
                                 (worldPopDownload.utils, 'area', 'Brandenburg')):
            patcher = mock.patch.object(obj, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_area_is_passed_west_south_east_north_and_result_is_saved(self):
        worldPopDownload.getWorldPop(self.config, '2020', self.name)
        self.assertEqual(self.calls, [{'product_name': 'pop_g2_r25a', 'aoi': [11.2682, 51.3618, 14.7636, 53.5587],
                                       'years': [2020], 'cache_in_tmp': True}])
        self.assertEqual(os.listdir(os.path.join(self.tmp.name, 'tmp')), [])  # the cache of the job is removed
        self.assertEqual(os.listdir(self.folder), ['2020.tif'])
        with rasterio.open(os.path.join(self.folder, '2020.tif')) as src:
            self.assertEqual((src.count, src.width, src.height, src.crs.to_epsg()), (1, 4, 3, 4326))
            np.testing.assert_allclose(src.read(1), 12.5)

    def test_year_outside_of_the_product_is_an_error(self):
        with self.assertRaises(ValueError):
            worldPopDownload.getWorldPop(self.config, '2010', self.name)
        self.assertEqual(self.calls, [])

    def test_area_without_data_is_an_error_and_leaves_no_file(self):
        self.empty = True
        with self.assertRaises(RuntimeError):
            worldPopDownload.getWorldPop(self.config, '2020', self.name)
        self.assertFalse(os.path.exists(os.path.join(self.folder, '2020.tif')))

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            worldPopDownload.getWorldPop(self.config, '2020', 'no_such_variable')


class TestConfigs(unittest.TestCase):
    def test_config_copies_agree_except_for_the_variables(self):
        for name in ('treecover_global.json', 'worldPop.json'):
            headers = []
            for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
                with open(os.path.join(REPO, folder, name), encoding='utf-8') as f:
                    config = json.load(f)
                config.pop('variables')
                headers.append(config)
            self.assertEqual(headers[0], headers[1], name)
            self.assertEqual(headers[0], headers[2], name)

    def test_every_global_tree_cover_variable_has_a_download(self):
        with open(os.path.join(REPO, 'configs_sources', 'treecover_global.json'), encoding='utf-8') as f:
            for variable in json.load(f)['variables']:
                self.assertIn(variable['name'], global_tc.TILE_URL)


if __name__ == '__main__':
    unittest.main()
