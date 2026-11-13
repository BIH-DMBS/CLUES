"""
Tests for the ERA5-Land download (utils/era5Land.py).

No network access and no credentials are needed: the cdsapi client and the reading of the GRIB
file are replaced by fakes. The fake GRIB data has the structure the GRIB reader (cfgrib) delivers.
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
import era5Land  # noqa: E402

CONFIG_NAME = 'reanalysis-era5-land.json'


def value_of(valid_time):
    # a value that identifies the hour: hours since 2000
    return ((valid_time - np.datetime64('2000-01-01T00:00')) / np.timedelta64(1, 'h')).astype('float32')


def grib_like_dataset(first_hour, last_hour, name='t2m', missing_hours=()):
    """
    Data set as cfgrib delivers it for ERA5-Land: 'time' is the forecast day, 'step' the hours 1..24
    after 00 UTC. Hour 00 UTC of a day is step 24 of the day before. Hours outside of the range
    first_hour..last_hour are empty (NaN).
    """
    first_hour, last_hour = np.datetime64(first_hour), np.datetime64(last_hour)
    days = np.arange((first_hour - np.timedelta64(1, 'h')).astype('datetime64[D]'), last_hour.astype('datetime64[D]') + 1)
    days = days.astype('datetime64[ns]')
    steps = (np.arange(1, 25) * np.timedelta64(1, 'h')).astype('timedelta64[ns]')
    valid_time = days[:, None] + steps[None, :]
    data = np.repeat(value_of(valid_time)[:, :, None, None], 2, axis=2).repeat(3, axis=3)
    outside = (valid_time < first_hour) | (valid_time > last_hour)
    for hour in missing_hours:
        outside |= valid_time == np.datetime64(hour)
    data[outside] = np.nan
    ds = xr.Dataset(
        {name: (['time', 'step', 'latitude', 'longitude'], data, {'units': 'K', 'long_name': '2 metre temperature'})},
        coords={'time': days, 'step': steps, 'latitude': [52.6, 52.5], 'longitude': [13.3, 13.4, 13.5],
                'valid_time': (['time', 'step'], valid_time)},
    )
    return ds


class TestGribToNetcdf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = os.path.join(self.tmp.name, 'out.nc')

    def test_complete_leap_year(self):
        ds = grib_like_dataset('2020-01-01T00:00', '2020-12-31T23:00')
        self.assertEqual(era5Land.grib_dataset_to_netcdf(ds, '2020', self.target), 8784)
        with xr.open_dataset(self.target) as result:
            self.assertEqual(dict(result.sizes), {'valid_time': 8784, 'latitude': 2, 'longitude': 3})
            times = result['valid_time'].values
            self.assertEqual((str(times[0])[:16], str(times[-1])[:16]), ('2020-01-01T00:00', '2020-12-31T23:00'))
            self.assertTrue((np.diff(times) == np.timedelta64(1, 'h')).all())
            # every hour has the value that belongs to it: nothing shifted, nothing mixed up
            np.testing.assert_array_equal(result['t2m'].values[:, 0, 0], value_of(times))
            self.assertEqual(result['t2m'].attrs['units'], 'K')
            np.testing.assert_allclose(result['latitude'].values, [52.6, 52.5])

    def test_hours_of_the_neighbouring_years_are_not_taken(self):
        # the GRIB file of a year also holds 00 UTC of the first of January of the next year
        ds = grib_like_dataset('2020-12-30T00:00', '2021-01-02T23:00')
        self.assertEqual(era5Land.grib_dataset_to_netcdf(ds, '2021', self.target), 48)
        with xr.open_dataset(self.target) as result:
            self.assertEqual(str(result['valid_time'].values[0])[:16], '2021-01-01T00:00')

    def test_year_that_is_not_complete_yet(self):
        ds = grib_like_dataset('2020-01-01T00:00', '2020-03-10T23:00')
        self.assertEqual(era5Land.grib_dataset_to_netcdf(ds, '2020', self.target), (31 + 29 + 10) * 24)

    def test_missing_hours_in_between_are_an_error(self):
        ds = grib_like_dataset('2020-01-01T00:00', '2020-01-31T23:00', missing_hours=('2020-01-15T07:00',))
        with self.assertRaises(RuntimeError) as context:
            era5Land.grib_dataset_to_netcdf(ds, '2020', self.target)
        self.assertIn('missing', str(context.exception))

    def test_no_data_of_the_year_is_an_error(self):
        ds = grib_like_dataset('2019-01-01T00:00', '2019-01-05T23:00')
        with self.assertRaises(RuntimeError):
            era5Land.grib_dataset_to_netcdf(ds, '2020', self.target)

    def test_data_without_step_dimension(self):
        hours = np.arange(np.datetime64('2020-01-01T00:00'), np.datetime64('2020-01-03T00:00'), np.timedelta64(1, 'h')).astype('datetime64[ns]')
        data = np.repeat(value_of(hours)[:, None, None], 2, axis=1).repeat(3, axis=2)
        ds = xr.Dataset({'t2m': (['time', 'latitude', 'longitude'], data)},
                        coords={'time': hours, 'latitude': [52.6, 52.5], 'longitude': [13.3, 13.4, 13.5]})
        self.assertEqual(era5Land.grib_dataset_to_netcdf(ds, '2020', self.target), 48)

    def test_two_variables_in_one_file_are_an_error(self):
        ds = grib_like_dataset('2020-01-01T00:00', '2020-01-02T23:00')
        ds['d2m'] = ds['t2m']
        with self.assertRaises(ValueError):
            era5Land.grib_dataset_to_netcdf(ds, '2020', self.target)


class FakeClient:
    requests = []
    failures = 0

    def __init__(self, url=None, key=None):
        pass

    def retrieve(self, dataset, request, target):
        FakeClient.requests.append((dataset, request, target))
        if FakeClient.failures > 0:
            FakeClient.failures -= 1
            raise RuntimeError('the request failed')
        with open(target, 'w') as f:
            f.write('GRIB')


class TestGetEra5Land(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = os.path.join(self.tmp.name, 'data')
        self.work = os.path.join(self.tmp.name, 'tmp')
        secrets = os.path.join(self.tmp.name, 'secrets')
        os.makedirs(secrets)
        with open(os.path.join(secrets, 'cdsapirc_climate.sct'), 'w') as f:
            f.write('url: https://example.invalid/api\nkey: not-a-real-key\n')
        self.config = os.path.join(REPO, 'configs_sources', CONFIG_NAME)
        FakeClient.requests = []
        FakeClient.failures = 0
        self.grib_content = grib_like_dataset('2020-01-01T00:00', '2020-12-31T23:00')

        def fake_open(path, engine=None):
            assert engine == 'cfgrib' and os.path.exists(path)
            return self.grib_content

        for obj, name, value in ((era5Land, 'download_folder', self.data), (era5Land, 'tmp_folder', self.work),
                                 (era5Land, 'secrets_folder', secrets), (era5Land, 'sleep', lambda seconds: None),
                                 (era5Land.cdsapi, 'Client', FakeClient), (era5Land.xr, 'open_dataset', fake_open),
                                 (era5Land.utils, 'config_folder', os.path.join(REPO, 'config')), (era5Land.utils, 'area', 'Brandenburg')):
            patcher = mock.patch.object(obj, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def folder(self):
        return os.path.join(self.data, 'reanalysis-era5-land', '2m_temperature')

    def test_one_request_for_the_complete_year(self):
        era5Land.getEra5Land(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), ['2020.nc'])
        self.assertEqual(len(FakeClient.requests), 1)
        dataset, request, _ = FakeClient.requests[0]
        self.assertEqual(dataset, 'reanalysis-era5-land')
        self.assertEqual(request['variable'], ['2m_temperature'])
        self.assertEqual(request['year'], '2020')
        self.assertEqual((len(request['month']), len(request['day']), len(request['time'])), (12, 31, 24))
        self.assertEqual((request['data_format'], request['download_format']), ('grib', 'unarchived'))
        # Brandenburg [53.5587, 11.2682, 51.3618, 14.7636] widened by one grid step of 0.1 degree
        self.assertEqual(request['area'], [53.6587, 11.1682, 51.2618, 14.8636])
        self.assertEqual(os.listdir(self.work), [])  # the GRIB file is removed
        self.assertEqual(os.listdir(os.path.join(self.data, 'reanalysis-era5-land')), ['2m_temperature'])  # nothing temporary in the data folder

    def test_failed_request_is_tried_again(self):
        FakeClient.failures = 2
        era5Land.getEra5Land(self.config, '2020', '2m_temperature')
        self.assertEqual(len(FakeClient.requests), 3)
        self.assertEqual(os.listdir(self.folder()), ['2020.nc'])

    def test_request_that_keeps_failing_is_an_error_and_leaves_no_file(self):
        FakeClient.failures = 10
        with self.assertRaises(RuntimeError):
            era5Land.getEra5Land(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), [])
        self.assertEqual(os.listdir(self.work), [])

    def test_missing_hours_are_an_error_and_leave_no_file(self):
        self.grib_content = grib_like_dataset('2020-01-01T00:00', '2020-12-31T23:00', missing_hours=('2020-06-01T12:00',))
        with self.assertRaises(RuntimeError):
            era5Land.getEra5Land(self.config, '2020', '2m_temperature')
        self.assertEqual(os.listdir(self.folder()), [])

    def test_existing_file_is_not_downloaded_again(self):
        era5Land.getEra5Land(self.config, '2020', '2m_temperature')
        era5Land.getEra5Land(self.config, '2020', '2m_temperature')
        self.assertEqual(len(FakeClient.requests), 1)

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(ValueError):
            era5Land.getEra5Land(self.config, '2020', 'no_such_variable')
        self.assertEqual(FakeClient.requests, [])


class TestEra5LandConfig(unittest.TestCase):
    def test_the_three_config_copies_agree_except_for_the_variables(self):
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
                config = json.load(f)
            config.pop('variables')
            headers.append(config)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])
        self.assertEqual(headers[0]['grid_resolution_deg'], 0.1)


if __name__ == '__main__':
    unittest.main()
