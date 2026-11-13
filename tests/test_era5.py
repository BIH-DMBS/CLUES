"""
Tests for the ERA5 single levels download (utils.get_asset_climate).

No network access and no credentials are needed, the cdsapi client is replaced by a fake.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import collections
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

import numpy as np
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import utils  # noqa: E402

CONFIG_NAME = 'reanalysis-era5-single-levels.json'


def write_year_nc(path, year, n_steps=None):
    # small netCDF file that looks like an hourly file from the CDS
    valid_time = np.arange(np.datetime64(f'{year}-01-01T00:00'), np.datetime64(f'{int(year) + 1}-01-01T00:00'), np.timedelta64(1, 'h'))
    if n_steps is not None:
        valid_time = valid_time[:n_steps]
    ds = xr.Dataset(
        {'t2m': (['valid_time', 'latitude', 'longitude'], np.zeros((valid_time.size, 2, 2), dtype='float32'))},
        coords={'valid_time': valid_time, 'latitude': [52.5, 52.25], 'longitude': [13.0, 13.25]},
    )
    ds.to_netcdf(path)
    ds.close()


class FakeClient:
    """Stands in for cdsapi.Client, records the request and writes a file like the CDS does."""
    requests = []
    mode = 'ok'

    def __init__(self, url=None, key=None):
        pass

    def retrieve(self, dataset, request, target):
        FakeClient.requests.append((dataset, request, target))
        if FakeClient.mode == 'fail_before_write':
            raise RuntimeError('request rejected')
        year = request['year'][0]
        if FakeClient.mode == 'zip':
            with tempfile.TemporaryDirectory() as tmp:
                nc = os.path.join(tmp, 'data_stream-oper_stepType-instant.nc')
                write_year_nc(nc, year)
                with zipfile.ZipFile(target, 'w') as z:
                    z.write(nc, 'data_stream-oper_stepType-instant.nc')
            return
        write_year_nc(target, '1999' if FakeClient.mode == 'wrong_year' else year,
                      n_steps=100 if FakeClient.mode == 'incomplete' else None)
        if FakeClient.mode == 'fail_after_write':
            raise RuntimeError('connection lost')


class TestGetAssetClimate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.download = os.path.join(self.tmp.name, 'data')
        secrets = os.path.join(self.tmp.name, 'secrets')
        os.makedirs(secrets)
        with open(os.path.join(secrets, 'cdsapirc_climate.sct'), 'w') as f:
            f.write('url: https://example.invalid/api\nkey: not-a-real-key\n')
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        FakeClient.requests = []
        FakeClient.mode = 'ok'
        for name, value in {'download_folder': self.download, 'secrets_folder': secrets,
                            'config_folder': os.path.join(REPO, 'config'), 'area': 'Brandenburg'}.items():
            patcher = mock.patch.object(utils, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(utils.cdsapi, 'Client', FakeClient)
        patcher.start()
        self.addCleanup(patcher.stop)

    def folder(self, variable='2m_temperature'):
        return os.path.join(self.download, 'reanalysis-era5-single-levels', variable)

    def test_request_and_result(self):
        utils.get_asset_climate(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), ['2020.nc'])  # no temporary files left
        dataset, request, _ = FakeClient.requests[0]
        self.assertEqual(dataset, 'reanalysis-era5-single-levels')
        self.assertEqual(request['product_type'], ['reanalysis'])
        self.assertEqual(request['variable'], ['2m_temperature'])
        self.assertEqual(request['year'], ['2020'])
        self.assertEqual(request['month'], ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])
        self.assertEqual((request['day'][0], request['day'][-1], len(request['day'])), ('01', '31', 31))
        self.assertEqual((request['time'][0], request['time'][-1], len(request['time'])), ('00:00', '23:00', 24))
        self.assertEqual((request['data_format'], request['download_format']), ('netcdf', 'unarchived'))
        # Brandenburg [53.5587, 11.2682, 51.3618, 14.7636] widened by one grid step of 0.25 degree
        self.assertEqual(request['area'], [53.8087, 11.0182, 51.1118, 15.0136])
        self.assertNotIn('format', request)

    def test_result_delivered_as_zip_archive_is_unpacked(self):
        FakeClient.mode = 'zip'
        utils.get_asset_climate(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), ['2020.nc'])
        with xr.open_dataset(os.path.join(self.folder(), '2020.nc')) as ds:
            self.assertEqual(ds.sizes['valid_time'], 8784)

    def test_incomplete_year_is_kept_with_a_warning(self):
        FakeClient.mode = 'incomplete'
        utils.get_asset_climate(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), ['2020.nc'])

    def test_existing_file_is_not_downloaded_again(self):
        utils.get_asset_climate(self.config, '2020', '2m_temperature')
        utils.get_asset_climate(self.config, '2020', '2m_temperature')
        self.assertEqual(len(FakeClient.requests), 1)

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            utils.get_asset_climate(self.config, '2020', 'no_such_variable')
        self.assertEqual(FakeClient.requests, [])

    def assert_failure_leaves_nothing(self, mode):
        FakeClient.mode = mode
        with self.assertRaises(RuntimeError):
            utils.get_asset_climate(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), [])

    def test_rejected_request_leaves_no_file(self):
        self.assert_failure_leaves_nothing('fail_before_write')

    def test_interrupted_download_leaves_no_file(self):
        self.assert_failure_leaves_nothing('fail_after_write')

    def test_data_of_another_year_leaves_no_file(self):
        self.assert_failure_leaves_nothing('wrong_year')


class TestEra5Config(unittest.TestCase):
    def load(self, folder):
        with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
            return json.load(f)

    def test_no_variable_is_listed_twice(self):
        for folder in ('configs_sources', os.path.join('docker', 'configs_sources')):
            names = [v['name'] for v in self.load(folder)['variables']]
            self.assertEqual([name for name, n in collections.Counter(names).items() if n > 1], [], folder)

    def test_the_three_config_copies_agree_except_for_the_variables(self):
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            config = self.load(folder)
            config.pop('variables')
            headers.append(config)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])
        self.assertEqual(headers[0]['grid_resolution_deg'], 0.25)


if __name__ == '__main__':
    unittest.main()
