"""
Tests for the SPEI drought index download (utils.spei_download).

No network access is needed, the download is replaced by a fake.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import utils  # noqa: E402

CONFIG_NAME = 'spei.json'


def write_spei_like_file(path, variable='spei'):
    # small file with the names and the time axis of the SPEI database
    months = np.arange(np.datetime64('1901-01'), np.datetime64('1903-01')).astype('datetime64[D]') + np.timedelta64(15, 'D')
    data = np.arange(months.size * 4 * 6, dtype='float32').reshape(months.size, 4, 6) / 100 - 3
    data[:, 0, 0] = np.nan  # a grid cell over the sea
    ds = xr.Dataset({variable: (['time', 'lat', 'lon'], data, {'units': '1'})},
                    coords={'time': months.astype('datetime64[ns]'), 'lat': [-0.75, -0.25, 0.25, 0.75],
                            'lon': [10.25, 10.75, 11.25, 11.75, 12.25, 12.75]}, attrs={'version': '2.10.0'})
    ds.to_netcdf(path, encoding={'time': {'units': 'days since 1900-1-1', 'calendar': 'gregorian'}})
    ds.close()
    return data


class TestSpeiDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = os.path.join(self.tmp.name, 'data', 'spei_drought_index')
        self.work = os.path.join(self.tmp.name, 'tmp')
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        self.urls = []
        self.mode = 'ok'

        def fake_download(url, target, max_retries=3):
            self.urls.append(url)
            if self.mode == 'fails':
                raise RuntimeError(f"Failed to download {url}")
            if self.mode == 'error page':
                with open(target, 'w') as f:
                    f.write('<html>not found</html>')
                return
            self.data = write_spei_like_file(target, 'other' if self.mode == 'other content' else 'spei')

        for name, value in {'download_folder': os.path.join(self.tmp.name, 'data'), 'tmp_folder': self.work,
                            'area': 'Berlin', 'config_folder': os.path.join(REPO, 'config'),
                            'download_file': fake_download}.items():
            patcher = mock.patch.object(utils, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_names_are_changed_and_everything_else_is_kept(self):
        utils.spei_download(self.config, '12')
        self.assertEqual(self.urls, ['https://digital.csic.es/bitstream/10261/364137/12/spei12.nc'])
        self.assertEqual(os.listdir(self.folder), ['12.nc'])
        self.assertEqual(os.listdir(self.work), [])  # the downloaded file is removed
        with xr.open_dataset(os.path.join(self.folder, '12.nc')) as ds:
            self.assertEqual(set(ds.coords), {'valid_time', 'latitude', 'longitude'})
            np.testing.assert_array_equal(ds['spei'].values, self.data)
            np.testing.assert_array_equal(ds['latitude'].values, [-0.75, -0.25, 0.25, 0.75])
            np.testing.assert_array_equal(ds['longitude'].values, [10.25, 10.75, 11.25, 11.75, 12.25, 12.75])
            self.assertEqual((str(ds['valid_time'].values[0])[:10], str(ds['valid_time'].values[-1])[:10]), ('1901-01-16', '1902-12-16'))
            self.assertEqual(ds.attrs['version'], '2.10.0')
            self.assertEqual(ds['spei'].attrs['units'], '1')

    def test_time_scale_38_uses_the_address_of_the_configuration(self):
        # on the server the file spei38.nc is in the folder 48, the address must come from the configuration
        utils.spei_download(self.config, '38')
        self.assertEqual(self.urls, ['https://digital.csic.es/bitstream/10261/364137/48/spei38.nc'])

    def test_time_scale_1_does_not_take_the_file_of_another_time_scale(self):
        utils.spei_download(self.config, '1')
        self.assertTrue(self.urls[0].endswith('/spei01.nc'))

    def test_unknown_time_scale_is_an_error(self):
        with self.assertRaises(ValueError):
            utils.spei_download(self.config, '99')
        self.assertEqual(self.urls, [])

    def assert_failure_leaves_nothing(self, mode, error):
        self.mode = mode
        with self.assertRaises(error):
            utils.spei_download(self.config, '12')
        self.assertEqual(os.listdir(self.folder), [])
        self.assertEqual(os.listdir(self.work), [])

    def test_failed_download_leaves_no_file(self):
        self.assert_failure_leaves_nothing('fails', RuntimeError)

    def test_error_page_instead_of_a_netcdf_file_leaves_no_file(self):
        self.assert_failure_leaves_nothing('error page', Exception)

    def test_file_without_the_index_leaves_no_file(self):
        self.assert_failure_leaves_nothing('other content', RuntimeError)


class TestSpeiConfig(unittest.TestCase):
    def load(self, folder):
        with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
            return json.load(f)

    def test_one_address_per_time_scale(self):
        config = self.load('configs_sources')
        urls = config['variables'][0]['urls']
        scales = [int(re.search(r'/spei(\d+)\.nc$', url).group(1)) for url in urls]
        self.assertEqual(sorted(scales), list(range(1, 49)))
        for time_scale in config['time_scales']:
            self.assertIn(time_scale, scales)

    def test_the_three_config_copies_agree_except_for_the_time_scales(self):
        configs = [self.load(folder) for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources'))]
        for config in configs:
            config.pop('time_scales')
        self.assertEqual(configs[0], configs[1])
        self.assertEqual(configs[0], configs[2])


if __name__ == '__main__':
    unittest.main()
