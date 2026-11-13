"""
Tests for the CORINE Land Cover download (utils/corine.py).

No network access is needed, the map service is replaced by a fake.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import csv
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import rasterio
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import corine  # noqa: E402

CONFIG_NAME = 'corine_copernicus.json'
LEGEND = corine.load_legend()
COLOUR = {c['code']: c['rgb'] for c in LEGEND}


def picture_of(codes):
    # picture as the map service would deliver it for an array of class codes (0 = transparent)
    picture = np.zeros(codes.shape + (4,), dtype=np.uint8)
    for code in np.unique(codes):
        if code != 0:
            picture[codes == code] = COLOUR[int(code)] + [255]
    return picture


def expected_codes(west, north, columns, rows, resolution):
    # a synthetic land cover that depends on the position only: stripes of 0.02 degree
    lons = west + (np.arange(columns) + 0.5) * resolution
    lats = north - (np.arange(rows) + 0.5) * resolution
    lon, lat = np.meshgrid(lons, lats)
    classes = np.array([112, 211, 311, 512], dtype=np.uint16)
    return classes[(np.floor(lon / 0.02).astype(int) + np.floor(lat / 0.02).astype(int)) % 4]


class TestLegend(unittest.TestCase):
    def test_44_classes_with_distinct_colours(self):
        self.assertEqual(len(LEGEND), 44)
        self.assertEqual(len({tuple(c['rgb']) for c in LEGEND}), 44)
        self.assertEqual(LEGEND[0]['code'], 111)
        self.assertEqual(LEGEND[-1]['code'], 523)
        self.assertNotIn(corine.NODATA, [c['code'] for c in LEGEND])
        self.assertNotIn(list(corine.NODATA_COLOUR), [c['rgb'] for c in LEGEND])


class TestDecodeColours(unittest.TestCase):
    def test_colours_become_class_codes(self):
        codes = np.array([[111, 112, 211], [311, 512, 523]], dtype=np.uint16)
        np.testing.assert_array_equal(corine.decode_colours(picture_of(codes), LEGEND), codes)

    def test_transparent_and_white_pixels_are_no_data(self):
        picture = picture_of(np.array([[112, 112, 112]]))
        picture[0, 0] = [0, 0, 0, 0]            # nothing drawn by the map service
        picture[0, 1] = [255, 255, 255, 255]    # 'no data' colour of the legend
        np.testing.assert_array_equal(corine.decode_colours(picture, LEGEND), [[0, 0, 112]])

    def test_unknown_colour_is_an_error(self):
        picture = picture_of(np.array([[112, 112]]))
        picture[0, 1] = [254, 0, 0, 255]  # almost the red of class 112, e.g. after smoothing
        with self.assertRaises(RuntimeError):
            corine.decode_colours(picture, LEGEND)

    def test_half_transparent_pixel_is_an_error(self):
        picture = picture_of(np.array([[112, 112]]))
        picture[0, 1, 3] = 128
        with self.assertRaises(RuntimeError):
            corine.decode_colours(picture, LEGEND)


class TestOutputGrid(unittest.TestCase):
    def test_grid_lines_are_multiples_of_the_resolution(self):
        west, north, columns, rows = corine.output_grid([53.5587, 11.2682, 51.3618, 14.7636], 0.001)
        self.assertAlmostEqual(west, 11.268)
        self.assertAlmostEqual(north, 53.559)
        self.assertEqual((columns, rows), (3496, 2198))

    def test_bbox_on_grid_lines_is_not_enlarged(self):
        west, north, columns, rows = corine.output_grid([53.0, 13.0, 52.0, 14.0], 0.001)
        self.assertAlmostEqual(west, 13.0)
        self.assertAlmostEqual(north, 53.0)
        self.assertEqual((columns, rows), (1000, 1000))


class FakeResponse:
    def __init__(self, content, content_type='image/png', status_code=200):
        self.content = content
        self.text = content.decode('utf-8', errors='replace')[:300]
        self.headers = {'Content-Type': content_type}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise corine.requests.HTTPError(f"status {self.status_code}")


def png_bytes(picture):
    buffer = io.BytesIO()
    Image.fromarray(picture, 'RGBA').save(buffer, format='PNG')
    return buffer.getvalue()


class TestRequestPicture(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(corine, 'sleep', lambda seconds: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.calls = []

    def request(self, responses, **kwargs):
        def fake_get(url, params=None, timeout=None):
            self.calls.append((url, params))
            return responses[min(len(self.calls), len(responses)) - 1]
        with mock.patch.object(corine.requests, 'get', fake_get):
            return corine.request_picture('https://example.invalid/MapServer', '1', 13.0, 52.0, 13.003, 52.002, 3, 2, **kwargs)

    def test_picture_is_returned_and_request_is_exact(self):
        picture = picture_of(np.array([[111, 112, 211], [311, 512, 523]]))
        result = self.request([FakeResponse(png_bytes(picture))])
        np.testing.assert_array_equal(result, picture)
        url, params = self.calls[0]
        self.assertEqual(url, 'https://example.invalid/MapServer/export')
        self.assertEqual(params['bbox'], '13.000000,52.000000,13.003000,52.002000')
        self.assertEqual(params['size'], '3,2')
        self.assertEqual(params['layers'], 'show:1')
        self.assertEqual((params['bboxSR'], params['imageSR'], params['format']), (4326, 4326, 'png32'))

    def test_error_document_of_the_service_is_retried_and_then_an_error(self):
        error = FakeResponse(b'{"error":{"code":500,"message":"Error exporting map"}}', 'application/json')
        with self.assertRaises(RuntimeError):
            self.request([error], max_retries=3)
        self.assertEqual(len(self.calls), 3)

    def test_second_attempt_succeeds(self):
        picture = picture_of(np.array([[111, 112, 211], [311, 512, 523]]))
        result = self.request([FakeResponse(b'', status_code=503), FakeResponse(png_bytes(picture))])
        np.testing.assert_array_equal(result, picture)

    def test_picture_of_wrong_size_is_an_error(self):
        with self.assertRaises(RuntimeError):
            self.request([FakeResponse(png_bytes(picture_of(np.array([[111, 112]]))))], max_retries=2)


class TestGetCorine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        self.folder = os.path.join(self.tmp.name, 'land_use')
        self.requests = []
        self.mode = 'ok'
        for name, value in {'download_folder': self.tmp.name, 'area': 'Berlin', 'TILE_SIZE': 300,
                            'config_folder': os.path.join(REPO, 'config'), 'request_picture': self.fake_picture}.items():
            patcher = mock.patch.object(corine, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_picture(self, url, layer, west, south, east, north, columns, rows, max_retries=4):
        self.requests.append((url, layer, columns, rows))
        if self.mode == 'fail' and len(self.requests) == 3:
            raise RuntimeError('service not reachable')
        if self.mode == 'empty':
            return np.zeros((rows, columns, 4), dtype=np.uint8)
        return picture_of(expected_codes(west, north, columns, rows, (east - west) / columns))

    def test_result_is_one_band_of_class_codes_without_seams(self):
        corine.get_corine(self.config, 'corine_landcover_2018')
        self.assertEqual(sorted(os.listdir(self.folder)), ['corine_landcover_2018.tif', 'corine_legend.csv'])
        # Berlin [52.7136, 12.9673, 52.2839, 13.816] at 0.001 degree: 849 x 431 pixels, 3 x 2 requests of 300 pixels
        self.assertEqual(len(self.requests), 6)
        self.assertTrue(all(r[0].endswith('/Corine/CLC2018_LAEA/MapServer') and r[1] == '1' for r in self.requests))
        with rasterio.open(os.path.join(self.folder, 'corine_landcover_2018.tif')) as src:
            self.assertEqual((src.count, src.dtypes[0], src.nodata, src.crs.to_epsg()), (1, 'uint16', 0, 4326))
            self.assertEqual((src.width, src.height), (849, 431))
            self.assertAlmostEqual(src.transform.c, 12.967)
            self.assertAlmostEqual(src.transform.f, 52.714)
            self.assertAlmostEqual(src.transform.a, 0.001)
            self.assertEqual(src.tags()['year'], '2018')
            data = src.read(1)
        np.testing.assert_array_equal(data, expected_codes(12.967, 52.714, 849, 431, 0.001))

    def test_legend_is_written_next_to_the_data(self):
        corine.get_corine(self.config, 'corine_landcover_2018')
        with open(os.path.join(self.folder, 'corine_legend.csv'), newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 45)
        self.assertEqual(rows[1]['code'], '112')
        self.assertEqual(rows[1]['level3'], 'Discontinuous urban fabric')
        self.assertEqual(rows[-1]['code'], '0')

    def test_area_without_corine_data_is_an_error_and_leaves_no_file(self):
        self.mode = 'empty'
        with self.assertRaises(RuntimeError) as context:
            corine.get_corine(self.config, 'corine_landcover_2018')
        self.assertIn('Europe only', str(context.exception))
        self.assertEqual(os.listdir(self.folder), [])

    def test_failed_request_leaves_no_file(self):
        self.mode = 'fail'
        with self.assertRaises(RuntimeError):
            corine.get_corine(self.config, 'corine_landcover_2018')
        self.assertEqual(os.listdir(self.folder), [])

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            corine.get_corine(self.config, 'no_such_variable')


class TestCorineConfig(unittest.TestCase):
    def load(self, folder):
        with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
            return json.load(f)

    def test_default_config_has_the_five_status_layers(self):
        variables = self.load('configs_sources')['variables']
        self.assertEqual(sorted(v['year'] for v in variables), ['1990', '2000', '2006', '2012', '2018'])
        for v in variables:
            self.assertEqual(v['name'], 'corine_landcover_' + v['year'])
            self.assertTrue(v['url'].endswith('/MapServer'), v['url'])
            self.assertIn('/Corine/CLC' + v['year'], v['url'])

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
