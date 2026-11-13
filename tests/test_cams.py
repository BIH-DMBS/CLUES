"""
Tests for the CAMS (cams-global-reanalysis-eac4) download in utils/utils.py.

No network access and no credentials are needed, the cdsapi client is replaced by a fake.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
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

BRANDENBURG = [53.5587, 11.2682, 51.3618, 14.7636]


def write_year_nc(path, year, n_steps=None, step_h=3):
    # small netCDF file that looks like a file from the ADS
    start = np.datetime64(f'{year}-01-01T00:00')
    end = np.datetime64(f'{int(year) + 1}-01-01T00:00')
    valid_time = np.arange(start, end, np.timedelta64(step_h, 'h'))
    if n_steps is not None:
        valid_time = valid_time[:n_steps]
    data = np.zeros((valid_time.size, 2, 2), dtype='float32')
    ds = xr.Dataset(
        {'gtco3': (['valid_time', 'latitude', 'longitude'], data)},
        coords={'valid_time': valid_time, 'latitude': [52.5, 51.75], 'longitude': [12.0, 12.75]},
    )
    ds.to_netcdf(path)
    ds.close()


class FakeClient:
    """Stands in for cdsapi.Client, records the request and writes a zip like the ADS does."""
    requests = []
    mode = 'ok'

    def __init__(self, url=None, key=None):
        pass

    def retrieve(self, dataset, request, target):
        FakeClient.requests.append((dataset, request, target))
        if FakeClient.mode == 'fail_before_write':
            raise RuntimeError('request rejected')
        if FakeClient.mode == 'broken_zip':
            with open(target, 'wb') as f:
                f.write(b'PK\x03\x04 this is not a complete zip file')
            return
        year = request['date'][0][:4]
        with tempfile.TemporaryDirectory() as tmp:
            nc = os.path.join(tmp, 'data_sfc.nc')
            write_year_nc(nc, '1999' if FakeClient.mode == 'wrong_year' else year)
            with zipfile.ZipFile(target, 'w') as z:
                z.write(nc, 'data_sfc.nc')
        if FakeClient.mode == 'fail_after_write':
            raise RuntimeError('connection lost')


class TestPadBbox(unittest.TestCase):
    def test_margin_is_added_on_every_side(self):
        self.assertEqual(utils.pad_bbox(BRANDENBURG, 0.75), [54.3087, 10.5182, 50.6118, 15.5136])

    def test_zero_margin_changes_nothing(self):
        self.assertEqual(utils.pad_bbox(BRANDENBURG, 0), BRANDENBURG)

    def test_clipped_at_the_limits_of_the_globe(self):
        self.assertEqual(utils.pad_bbox([89.9, -179.9, -89.9, 179.9], 0.75), [90.0, -180.0, -90.0, 180.0])

    def test_grid_column_west_of_brandenburg_is_inside_after_padding(self):
        # the 0.75 degree grid has a column at 11.25, just west of the box (11.2682)
        lon_min = utils.pad_bbox(BRANDENBURG, 0.75)[1]
        self.assertLessEqual(lon_min, 11.25)


class TestExtractSingleNetcdf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def make_zip(self, members):
        path = os.path.join(self.tmp.name, 'in.zip')
        with zipfile.ZipFile(path, 'w') as z:
            for name, content in members.items():
                z.writestr(name, content)
        return path

    def test_one_member_is_extracted(self):
        target = os.path.join(self.tmp.name, 'out.nc')
        utils.extract_single_netcdf(self.make_zip({'data_sfc.nc': b'abc'}), target)
        with open(target, 'rb') as f:
            self.assertEqual(f.read(), b'abc')

    def test_two_members_are_an_error(self):
        with self.assertRaises(RuntimeError):
            utils.extract_single_netcdf(self.make_zip({'a.nc': b'1', 'b.nc': b'2'}), os.path.join(self.tmp.name, 'o.nc'))

    def test_no_netcdf_member_is_an_error(self):
        with self.assertRaises(RuntimeError):
            utils.extract_single_netcdf(self.make_zip({'readme.txt': b'1'}), os.path.join(self.tmp.name, 'o.nc'))


class TestCheckTimeAxis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.nc = os.path.join(self.tmp.name, 'y.nc')

    def test_complete_leap_year(self):
        write_year_nc(self.nc, '2020')
        self.assertEqual(utils.check_time_axis(self.nc, '2020', '3'), (2928, 2928))

    def test_complete_normal_year(self):
        write_year_nc(self.nc, '2021')
        self.assertEqual(utils.check_time_axis(self.nc, '2021', '3'), (2920, 2920))

    def test_incomplete_year_is_reported(self):
        write_year_nc(self.nc, '2021', n_steps=100)
        self.assertEqual(utils.check_time_axis(self.nc, '2021', '3'), (100, 2920))

    def test_wrong_year_is_an_error(self):
        write_year_nc(self.nc, '2019')
        with self.assertRaises(RuntimeError):
            utils.check_time_axis(self.nc, '2020', '3')

    def test_empty_file_is_an_error(self):
        write_year_nc(self.nc, '2020', n_steps=0)
        with self.assertRaises(RuntimeError):
            utils.check_time_axis(self.nc, '2020', '3')


class TestGetAssetAtmosphere(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.download = os.path.join(self.tmp.name, 'data')
        secrets = os.path.join(self.tmp.name, 'secrets')
        os.makedirs(secrets)
        with open(os.path.join(secrets, 'cdsapirc_atmo.sct'), 'w') as f:
            f.write('url: https://example.invalid/api\nkey: not-a-real-key\n')
        self.config = os.path.join(REPO, 'configs_sources', 'cams-global-reanalysis-eac4.json')
        FakeClient.requests = []
        FakeClient.mode = 'ok'
        for name, value in {
            'download_folder': self.download,
            'secrets_folder': secrets,
            'config_folder': os.path.join(REPO, 'config'),
            'area': 'Brandenburg',
        }.items():
            patcher = mock.patch.object(utils, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(utils.cdsapi, 'Client', FakeClient)
        patcher.start()
        self.addCleanup(patcher.stop)

    def folder(self, variable):
        return os.path.join(self.download, 'cams-global-reanalysis-eac4', variable)

    def test_single_level_variable(self):
        utils.get_asset_atmosphere(self.config, '2020', 'total_column_ozone')
        folder = self.folder('total_column_ozone')
        self.assertEqual(os.listdir(folder), ['2020.nc'])  # no temporary files left
        dataset, request, _ = FakeClient.requests[0]
        self.assertEqual(dataset, 'cams-global-reanalysis-eac4')
        self.assertEqual(request['data_format'], 'netcdf_zip')
        self.assertEqual(request['variable'], ['total_column_ozone'])
        self.assertEqual(request['date'], ['2020-01-01/2020-12-31'])
        self.assertEqual(len(request['time']), 8)
        self.assertEqual(request['area'], [54.3087, 10.5182, 50.6118, 15.5136])
        self.assertNotIn('model_level', request)
        self.assertNotIn('format', request)

    def test_multi_level_variable_requests_its_model_level(self):
        utils.get_asset_atmosphere(self.config, '2020', 'sulphur_dioxide')
        self.assertEqual(FakeClient.requests[0][1]['model_level'], ['60'])

    def test_existing_file_is_not_downloaded_again(self):
        utils.get_asset_atmosphere(self.config, '2020', 'total_column_ozone')
        utils.get_asset_atmosphere(self.config, '2020', 'total_column_ozone')
        self.assertEqual(len(FakeClient.requests), 1)

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            utils.get_asset_atmosphere(self.config, '2020', 'no_such_variable')
        self.assertEqual(FakeClient.requests, [])

    def assert_failure_leaves_nothing(self, mode, error):
        FakeClient.mode = mode
        with self.assertRaises(error):
            utils.get_asset_atmosphere(self.config, '2020', 'total_column_ozone')
        self.assertEqual(os.listdir(self.folder('total_column_ozone')), [])

    def test_rejected_request_leaves_no_file(self):
        self.assert_failure_leaves_nothing('fail_before_write', RuntimeError)

    def test_interrupted_download_leaves_no_file(self):
        self.assert_failure_leaves_nothing('fail_after_write', RuntimeError)

    def test_broken_zip_leaves_no_file(self):
        self.assert_failure_leaves_nothing('broken_zip', zipfile.BadZipFile)

    def test_data_of_another_year_leaves_no_file(self):
        self.assert_failure_leaves_nothing('wrong_year', RuntimeError)


class TestCamsConfig(unittest.TestCase):
    def test_the_three_config_copies_agree_except_for_the_variables(self):
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            with open(os.path.join(REPO, folder, 'cams-global-reanalysis-eac4.json')) as f:
                config = json.load(f)
            config.pop('variables')
            headers.append(config)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])

    def test_multi_level_variables_have_a_model_level(self):
        with open(os.path.join(REPO, 'configs_sources', 'cams-global-reanalysis-eac4.json')) as f:
            config = json.load(f)
        for variable in config['variables']:
            if variable['name'].endswith('mixing_ratio') or variable['name'] == 'sulphur_dioxide':
                self.assertEqual(variable.get('model_level'), '60', variable['name'])
            else:
                self.assertNotIn('model_level', variable, variable['name'])


if __name__ == '__main__':
    unittest.main()
