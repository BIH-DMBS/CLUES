"""
Tests for the download of single GeoTIFF files (utils.get_simple_download_tif), used for the
Copernicus dynamic land cover (built-up cover fraction) and the World Settlement Footprint 3D.

No network access is needed, the web server is replaced by a fake.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import io
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
import utils  # noqa: E402

CONFIG_NAME = 'copernicus_dynamic_land_cover.json'


def geotiff_bytes():
    data = np.arange(200, dtype='uint8').reshape(10, 20)
    with rasterio.MemoryFile() as memory_file:
        with memory_file.open(driver='GTiff', height=10, width=20, count=1, dtype='uint8', crs='EPSG:4326',
                              transform=from_origin(-180, 80, 18, 16), nodata=255) as dst:
            dst.write(data, 1)
        return memory_file.read()


class FakeResponse:
    def __init__(self, status_code=200, content=b'', announced_size=None):
        self.status_code = status_code
        self.content = content
        self.headers = {'Content-Length': str(len(content) if announced_size is None else announced_size)}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise utils.requests.HTTPError(f"status {self.status_code}")

    def iter_content(self, chunk_size):
        stream = io.BytesIO(self.content)
        while True:
            chunk = stream.read(1000)
            if not chunk:
                return
            yield chunk


class TestSimpleDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        self.folder = os.path.join(self.tmp.name, 'Copernicus_dynamic_land_cover')
        self.responses = []
        self.urls = []
        for name, value in {'download_folder': self.tmp.name, 'area': 'Berlin',
                            'config_folder': os.path.join(REPO, 'config')}.items():
            patcher = mock.patch.object(utils, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        def fake_get(url, stream=True, timeout=None):
            self.urls.append(url)
            return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]

        for target, replacement in ((utils.requests, 'get'), (utils, 'sleep')):
            patcher = mock.patch.object(target, replacement, fake_get if replacement == 'get' else lambda s: None)
            patcher.start()
            self.addCleanup(patcher.stop)

    def download(self, name='BuildUp_CoverFraction_2016'):
        utils.get_simple_download_tif(self.config, name)

    def test_file_is_saved_under_the_name_of_the_variable(self):
        content = geotiff_bytes()
        self.responses = [FakeResponse(200, content)]
        self.download()
        self.assertEqual(os.listdir(self.folder), ['BuildUp_CoverFraction_2016.tif'])  # no temporary file left
        with open(os.path.join(self.folder, 'BuildUp_CoverFraction_2016.tif'), 'rb') as f:
            self.assertEqual(f.read(), content)
        self.assertIn('2016-conso_BuiltUp-CoverFraction', self.urls[0])

    def test_server_error_is_an_error_and_leaves_no_file(self):
        self.responses = [FakeResponse(503)]
        with self.assertRaises(RuntimeError):
            self.download()
        self.assertEqual(len(self.urls), 3)  # tried three times
        self.assertEqual(os.listdir(self.folder), [])

    def test_incomplete_download_is_an_error_and_leaves_no_file(self):
        content = geotiff_bytes()
        self.responses = [FakeResponse(200, content[:500], announced_size=len(content))]
        with self.assertRaises(RuntimeError):
            self.download()
        self.assertEqual(os.listdir(self.folder), [])

    def test_second_attempt_succeeds(self):
        content = geotiff_bytes()
        self.responses = [FakeResponse(503), FakeResponse(200, content)]
        self.download()
        self.assertEqual(os.listdir(self.folder), ['BuildUp_CoverFraction_2016.tif'])

    def test_error_page_instead_of_geotiff_is_an_error_and_leaves_no_file(self):
        self.responses = [FakeResponse(200, b'<html><body>403 Forbidden</body></html>')]
        with self.assertRaises(Exception):
            self.download()
        self.assertEqual(os.listdir(self.folder), [])

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            self.download('no_such_variable')
        self.assertEqual(self.urls, [])


def write_global_tif(path, crs='EPSG:4326'):
    # a small "global" raster: 360 x 180 pixels of 1 degree, value = column + 1000 * row
    cols, rows = np.meshgrid(np.arange(360), np.arange(180))
    data = (cols + 1000 * rows).astype('int32')
    with rasterio.open(path, 'w', driver='GTiff', height=180, width=360, count=1, dtype='int32', crs=crs,
                       transform=from_origin(-180, 90, 1, 1), nodata=-32767) as dst:
        dst.write(data, 1)
        dst.scales = (0.1,)
        dst.update_tags(contact='someone')
        dst.set_band_description(1, 'BuildingHeight')
    return data


class TestCropGeotiff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = os.path.join(self.tmp.name, 'global.tif')
        self.target = os.path.join(self.tmp.name, 'area.tif')
        self.data = write_global_tif(self.source)

    def test_pixels_grid_and_metadata_are_kept(self):
        # bbox [lat_max, lon_min, lat_min, lon_max]
        utils.crop_geotiff_to_bbox(self.source, self.target, [53.6, 11.3, 51.4, 14.8], margin_in_pixel=2)
        with rasterio.open(self.target) as src:
            # columns 191..194 and rows 36..38 contain the box, plus 2 pixels on every side
            self.assertEqual((src.width, src.height), (8, 7))
            self.assertEqual((src.bounds.left, src.bounds.top), (9.0, 56.0))
            np.testing.assert_array_equal(src.read(1), self.data[34:41, 189:197])
            self.assertEqual((src.dtypes[0], src.nodata, src.scales, src.crs.to_epsg()), ('int32', -32767, (0.1,), 4326))
            self.assertEqual(src.tags()['contact'], 'someone')
            self.assertEqual(src.descriptions[0], 'BuildingHeight')

    def test_area_at_the_edge_of_the_raster_is_clipped(self):
        utils.crop_geotiff_to_bbox(self.source, self.target, [89.5, 178.5, 88.5, 179.5], margin_in_pixel=5)
        with rasterio.open(self.target) as src:
            self.assertEqual((src.bounds.right, src.bounds.top), (180.0, 90.0))
            np.testing.assert_array_equal(src.read(1), self.data[0:7, 353:360])

    def test_large_area_is_copied_in_steps(self):
        utils.crop_geotiff_to_bbox(self.source, self.target, [60, -100, -60, 100], margin_in_pixel=0, rows_per_step=7)
        with rasterio.open(self.target) as src:
            np.testing.assert_array_equal(src.read(1), self.data[30:150, 80:280])

    def test_area_outside_of_the_raster_is_an_error(self):
        source = os.path.join(self.tmp.name, 'small.tif')
        with rasterio.open(source, 'w', driver='GTiff', height=10, width=10, count=1, dtype='uint8', crs='EPSG:4326',
                           transform=from_origin(0, 10, 1, 1)) as dst:
            dst.write(np.zeros((10, 10), dtype='uint8'), 1)
        with self.assertRaises(RuntimeError):
            utils.crop_geotiff_to_bbox(source, self.target, [53.6, 11.3, 51.4, 14.8])


class TestCutToArea(unittest.TestCase):
    """EOC_WSF3D.json has "cut_to_area": true, only the configured area is saved."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', 'EOC_WSF3D.json')
        self.folder = os.path.join(self.tmp.name, 'data', 'WordSettlementFootprint3D')
        self.tmp_folder = os.path.join(self.tmp.name, 'tmp')
        self.server = 'partial reads'
        self.cropped_from = []
        self.downloaded = []
        self.global_file = os.path.join(self.tmp.name, 'server_file.tif')
        self.data = write_global_tif(self.global_file)
        real_crop = utils.crop_geotiff_to_bbox

        def fake_crop(source, target, bbox, **kwargs):
            # a file on a web server is replaced by the local copy of it
            self.cropped_from.append(source)
            real_crop(self.global_file if source.startswith('/vsicurl/') else source, target, bbox, **kwargs)

        def fake_download(url, target, max_retries=3):
            self.downloaded.append(url)
            if self.server == 'broken':
                raise RuntimeError(f"Failed to download {url}")
            with open(self.global_file, 'rb') as src, open(target, 'wb') as dst:
                dst.write(src.read())

        for name, value in {'download_folder': os.path.join(self.tmp.name, 'data'), 'tmp_folder': self.tmp_folder,
                            'area': 'Brandenburg', 'config_folder': os.path.join(REPO, 'config'),
                            'supports_range_requests': lambda url: self.server == 'partial reads',
                            'crop_geotiff_to_bbox': fake_crop, 'download_file': fake_download}.items():
            patcher = mock.patch.object(utils, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def check_result(self):
        self.assertEqual(os.listdir(self.folder), ['WSF3D_V02_BuildingHeight.tif'])
        with rasterio.open(os.path.join(self.folder, 'WSF3D_V02_BuildingHeight.tif')) as src:
            # Brandenburg [53.5587, 11.2682, 51.3618, 14.7636] with a margin of 10 pixels of 1 degree
            self.assertEqual((src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top), (1.0, 25.0, 41.0, 64.0))
            np.testing.assert_array_equal(src.read(1), self.data[26:49, 181:205])

    def test_only_the_area_is_read_from_the_server(self):
        utils.get_simple_download_tif(self.config, 'WSF3D_V02_BuildingHeight')
        self.check_result()
        self.assertEqual(self.cropped_from, ['/vsicurl/https://download.geoservice.dlr.de/WSF3D/files/global/WSF3D_V02_BuildingHeight.tif'])
        self.assertEqual(self.downloaded, [])

    def test_server_without_partial_reads_download_then_cut(self):
        self.server = 'complete files only'
        utils.get_simple_download_tif(self.config, 'WSF3D_V02_BuildingHeight')
        self.check_result()
        self.assertEqual(len(self.downloaded), 1)
        self.assertEqual(os.listdir(self.tmp_folder), [])  # the complete file is removed again

    def test_failed_download_leaves_no_file(self):
        self.server = 'broken'
        with self.assertRaises(RuntimeError):
            utils.get_simple_download_tif(self.config, 'WSF3D_V02_BuildingHeight')
        self.assertEqual(os.listdir(self.folder), [])

    def test_land_cover_config_still_downloads_the_complete_file(self):
        with open(os.path.join(REPO, 'configs_sources', CONFIG_NAME), encoding='utf-8') as f:
            self.assertFalse(json.load(f).get('cut_to_area', False))
        with open(self.config, encoding='utf-8') as f:
            self.assertTrue(json.load(f)['cut_to_area'])


class TestLandCoverConfig(unittest.TestCase):
    def load(self, folder):
        with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
            return json.load(f)

    def test_every_url_is_the_built_up_layer_of_its_year(self):
        for folder in ('configs_sources', os.path.join('docker', 'configs_sources')):
            for variable in self.load(folder)['variables']:
                file_name = variable['url'].split('/files/')[-1]
                self.assertIn('BuiltUp-CoverFraction-layer', file_name, variable['name'])
                self.assertIn(f"_{variable['year']}-", file_name, variable['name'])
                self.assertTrue(variable['name'].endswith(variable['year']), variable['name'])

    def test_default_config_covers_2015_to_2019(self):
        years = [v['year'] for v in self.load('configs_sources')['variables']]
        self.assertEqual(years, ['2015', '2016', '2017', '2018', '2019'])

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
