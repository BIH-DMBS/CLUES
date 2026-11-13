"""
Tests for the ESPON download (utils/espon.py) and the names of its files (utils/espon_targets.py).

No network access is needed. The packages of the ESPON database are replaced by synthetic ones
with the same structure: a zip file that contains zip files, each with one shapefile.
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

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import espon  # noqa: E402
from espon_targets import espon_targets, find_target, sanitize_filename  # noqa: E402

BERLIN = box(13.1, 52.3, 13.8, 52.7)
BRANDENBURG = box(11.3, 51.4, 14.8, 53.6)
GERMANY = box(5.9, 47.3, 15.0, 55.1)

CONFIG = {
    "type": "espon", "source": "espon",
    "variables": [
        {"dimension": ["Deaths by age groups"],
         "features": [
             {"id": 40, "name": "Deaths - age group 0-4", "shape": "https://espon.invalid/40_shp.zip", "csv": "https://espon.invalid/40_csv.zip", "years_string": "2014-2016, 2017"},
             {"id": 97, "name": "Deaths - age group 0-4", "shape": "https://espon.invalid/97_shp.zip", "csv": "https://espon.invalid/97_csv.zip", "years_string": "2017"},
             {"id": 41, "name": "Deaths - age group 5-9 (total)", "shape": "https://espon.invalid/41_shp.zip", "csv": "https://espon.invalid/41_csv.zip", "years_string": "2017"},
         ]},
    ],
}


def shapefile_zip(folder, name, rows, crs='EPSG:4326'):
    # a zip file with one shapefile; rows: list of (tunit_code, level, geometry, value)
    gdf = gpd.GeoDataFrame({
        'tunit_code': [r[0] for r in rows],
        'level': [r[1] for r in rows],
        'version': [2016] * len(rows),
        'y_2014-201': [r[3] for r in rows],   # 'y_2014-2016', cut to the 10 characters a shapefile allows
        'y_2017': [r[3] + 1 for r in rows],
    }, geometry=[r[2] for r in rows], crs='EPSG:4326').to_crs(crs)
    shp_folder = os.path.join(folder, name)
    os.makedirs(shp_folder)
    gdf.to_file(os.path.join(shp_folder, name + '.shp'))
    zip_path = os.path.join(folder, name + '.zip')
    with zipfile.ZipFile(zip_path, 'w') as z:
        for file in os.listdir(shp_folder):
            z.write(os.path.join(shp_folder, file), file)
    return zip_path


def package(folder, inner_zips, name='package.zip'):
    path = os.path.join(folder, name)
    with zipfile.ZipFile(path, 'w') as z:
        for inner in inner_zips:
            z.write(inner, os.path.basename(inner))
    return path


class TestEsponTargets(unittest.TestCase):
    def test_names_are_made_from_dimension_and_indicator(self):
        targets = espon_targets(CONFIG, 80)
        self.assertEqual(targets[0]['folder'], 'Deaths_by_age_groups')
        self.assertEqual(targets[0]['name'], 'Deaths_-_age_group_0-4')
        self.assertEqual(targets[2]['name'], 'Deaths_-_age_group_5-9_total')
        self.assertEqual(sanitize_filename("a/b: c's (d)"), 'ab_cs_d')

    def test_second_indicator_with_the_same_name_gets_its_id(self):
        targets = espon_targets(CONFIG, 80)
        self.assertEqual([t['name'] for t in targets[:2]], ['Deaths_-_age_group_0-4', 'Deaths_-_age_group_0-4_id97'])
        self.assertEqual(find_target(CONFIG, 80, 'Deaths_by_age_groups', 'Deaths_-_age_group_0-4')['feature']['id'], 40)
        self.assertEqual(find_target(CONFIG, 80, 'Deaths_by_age_groups', 'Deaths_-_age_group_0-4_id97')['feature']['id'], 97)
        self.assertIsNone(find_target(CONFIG, 80, 'Deaths_by_age_groups', 'no_such_file'))

    def test_names_stay_within_the_length_limit(self):
        targets = espon_targets(CONFIG, 12)
        self.assertEqual(targets[0]['folder'], 'Deaths_by_ag')
        self.assertEqual([t['name'] for t in targets], ['Deaths_-_age', 'Deaths__id97', 'Deaths__id41'])
        self.assertTrue(all(len(t['name']) <= 12 for t in targets))

    def test_default_configuration_has_no_two_indicators_with_the_same_file(self):
        with open(os.path.join(REPO, 'configs_sources', 'espon.json'), encoding='utf-8') as f:
            parameters = json.load(f)
        targets = espon_targets(parameters, 80)
        self.assertEqual(len(targets), 1275)
        self.assertEqual(len({(t['folder'], t['name']) for t in targets}), 1275)
        self.assertEqual(len({t['feature']['id'] for t in targets}), 1275)
        # 55 names are used by two or three indicators, 56 indicators get their id appended
        self.assertEqual(sum(t['name'].endswith(f"_id{t['feature']['id']}") for t in targets), 56)
        self.assertTrue(all(len(t['name']) <= 80 and len(t['folder']) <= 80 for t in targets))


class EsponDownloadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fixtures = os.path.join(self.tmp.name, 'fixtures')
        os.makedirs(self.fixtures)
        self.data = os.path.join(self.tmp.name, 'data')
        self.work = os.path.join(self.tmp.name, 'tmp')
        self.served = {}   # url -> file that the fake server delivers
        self.requested = []
        self.config = os.path.join(self.tmp.name, 'espon.json')
        with open(self.config, 'w') as f:
            json.dump(CONFIG, f)

        def fake_download(url, target):
            self.requested.append(url)
            if url not in self.served:
                raise RuntimeError(f"Failed to download {url}. Status code: 404")
            with open(self.served[url], 'rb') as src, open(target, 'wb') as dst:
                dst.write(src.read())

        for obj, name, value in ((espon, 'download_folder', self.data), (espon, 'tmp_folder', self.work),
                                 (espon, 'espon_filename_length', 80), (espon, 'download', fake_download),
                                 (espon.utils, 'config_folder', os.path.join(REPO, 'config')), (espon.utils, 'area', 'Berlin')):
            patcher = mock.patch.object(obj, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def serve_shapes(self, indicator_id, levels):
        # levels: {name: rows}, one shapefile per NUTS level as in the ESPON packages
        inner = [shapefile_zip(self.fixtures, f'{indicator_id}_{name}', rows) for name, rows in levels.items()]
        self.served[f'https://espon.invalid/{indicator_id}_shp.zip'] = package(self.fixtures, inner, f'{indicator_id}_shp.zip')

    def csv_path(self, name):
        return os.path.join(self.data, 'espon', 'Deaths_by_age_groups', name + '.csv')

    def geometry(self):
        return pd.read_csv(os.path.join(self.data, 'espon', 'geometry.csv'))


class TestGetAssetEspon(EsponDownloadTest):
    def test_regions_with_the_same_geometry_at_several_levels_are_all_kept(self):
        # Berlin is one region at the NUTS levels 1 and 2 (DE3, DE30) with the same geometry
        self.serve_shapes(40, {'nuts0': [('DE', 0, GERMANY, 100)],
                               'nuts1': [('DE3', 1, BERLIN, 10), ('DE4', 1, BRANDENBURG, 20)],
                               'nuts2': [('DE30', 2, BERLIN, 10), ('DE40', 2, BRANDENBURG, 20)]})
        espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        data = pd.read_csv(self.csv_path('Deaths_-_age_group_0-4'))
        self.assertEqual(sorted(data['tunit_code']), ['DE', 'DE3', 'DE30', 'DE4', 'DE40'])
        self.assertNotIn('geometry', data.columns)
        # the column name that was cut by the shapefile format is restored
        self.assertIn('y_2014-2016', data.columns)
        self.assertEqual(data.set_index('tunit_code').loc['DE4', 'y_2014-2016'], 20)
        # one geometry per region code
        geometry = self.geometry()
        self.assertEqual(list(geometry.columns), ['geometry', 'tunit_code'])
        self.assertEqual(sorted(geometry['tunit_code']), ['DE', 'DE3', 'DE30', 'DE4', 'DE40'])
        self.assertTrue(geometry['geometry'].str.startswith('POLYGON').all())

    def test_geometries_are_added_once_only(self):
        rows = {'nuts1': [('DE3', 1, BERLIN, 10), ('DE4', 1, BRANDENBURG, 20)]}
        self.serve_shapes(40, rows)
        self.serve_shapes(97, {'nuts1': rows['nuts1'] + [('DE', 0, GERMANY, 5)]})
        espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        first = self.geometry()
        espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4_id97', 'Deaths_by_age_groups')
        second = self.geometry()
        self.assertEqual(len(first), 2)
        self.assertEqual(sorted(second['tunit_code']), ['DE', 'DE3', 'DE4'])
        pd.testing.assert_frame_equal(second.iloc[:2], first)  # existing rows are untouched
        # both indicators with the same name have their own file
        self.assertTrue(os.path.exists(self.csv_path('Deaths_-_age_group_0-4')))
        self.assertEqual(len(pd.read_csv(self.csv_path('Deaths_-_age_group_0-4_id97'))), 3)
        self.assertEqual(self.requested, ['https://espon.invalid/40_shp.zip', 'https://espon.invalid/97_shp.zip'])

    def test_geometries_are_stored_in_geographic_coordinates(self):
        inner = [shapefile_zip(self.fixtures, '40_laea', [('DE3', 1, BERLIN, 10)], crs='EPSG:3035')]
        self.served['https://espon.invalid/40_shp.zip'] = package(self.fixtures, inner, '40_shp.zip')
        espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        from shapely import wkt
        bounds = wkt.loads(self.geometry()['geometry'][0]).bounds
        self.assertAlmostEqual(bounds[0], 13.1, delta=0.05)
        self.assertAlmostEqual(bounds[3], 52.7, delta=0.05)

    def test_damaged_shape_package_falls_back_to_the_csv_package(self):
        bad = os.path.join(self.fixtures, 'bad.zip')
        with open(bad, 'wb') as f:
            f.write(b'this is not a zip file')
        csv_file = os.path.join(self.fixtures, 'ind.csv')
        with open(csv_file, 'w') as f:
            f.write('tunit_code,y_2017\nDE3,11\n')
        csv_zip = os.path.join(self.fixtures, '40_csv.zip')
        with zipfile.ZipFile(csv_zip, 'w') as z:
            z.write(csv_file, 'ind_40.csv')
        self.served['https://espon.invalid/40_shp.zip'] = bad
        self.served['https://espon.invalid/40_csv.zip'] = csv_zip
        espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        self.assertEqual(pd.read_csv(self.csv_path('Deaths_-_age_group_0-4')).values.tolist(), [['DE3', 11]])
        self.assertFalse(os.path.exists(os.path.join(self.data, 'espon', 'geometry.csv')))

    def test_failed_download_is_an_error_and_leaves_no_file(self):
        with self.assertRaises(RuntimeError):
            espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        self.assertEqual(os.listdir(os.path.join(self.data, 'espon', 'Deaths_by_age_groups')), [])
        self.assertEqual(os.listdir(self.work), [])  # the temporary folder of the indicator is removed

    def test_csv_package_without_csv_is_an_error(self):
        empty_package = package(self.fixtures, [], '40_shp.zip')  # a package without shapefiles
        empty_csv = os.path.join(self.fixtures, '40_csv.zip')
        with zipfile.ZipFile(empty_csv, 'w') as z:
            z.writestr('readme.txt', 'nothing')
        self.served['https://espon.invalid/40_shp.zip'] = empty_package
        self.served['https://espon.invalid/40_csv.zip'] = empty_csv
        with self.assertRaises(RuntimeError):
            espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        self.assertEqual(os.listdir(os.path.join(self.data, 'espon', 'Deaths_by_age_groups')), [])

    def test_unknown_file_name_is_an_error(self):
        with self.assertRaises(ValueError):
            espon.get_asset_espon(self.config, 'no_such_indicator', 'Deaths_by_age_groups')
        self.assertEqual(self.requested, [])

    def test_temporary_files_do_not_touch_the_data_folder(self):
        self.serve_shapes(40, {'nuts1': [('DE3', 1, BERLIN, 10)]})
        espon.get_asset_espon(self.config, 'Deaths_-_age_group_0-4', 'Deaths_by_age_groups')
        self.assertEqual(os.listdir(os.path.join(self.data, 'espon', 'Deaths_by_age_groups')), ['Deaths_-_age_group_0-4.csv'])
        self.assertEqual(os.listdir(self.work), [])


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class FakeScraper:
    """Serves a list of indicators page by page, like the ESPON interface."""

    def __init__(self, indicators, fail_at_offset=None, count=None):
        self.indicators = indicators
        self.fail_at_offset = fail_at_offset
        self.count = len({i['id'] for i in indicators}) if count is None else count

    def get(self, url, params=None, timeout=None):
        offset, limit = params['offset'], params['limit']
        if offset == self.fail_at_offset:
            return FakeResponse(403)
        page = self.indicators[offset:offset + limit]
        more = offset + limit < len(self.indicators)
        return FakeResponse(200, {'count': self.count, 'next': 'more' if more else None, 'results': page})


def api_indicator(item_id, name, parents=(), packages=('csv', 'shape')):
    categories = {'csv': 'Indicator package (CSV+XLS)', 'shape': 'Indicator package (SHAPE)', 'other': 'Metadata'}
    return {'id': item_id, 'name': name, 'years_string': '2020, 2021',
            'parents': [{'parent_name': p} for p in parents],
            'package': [{'category': categories[k], 'url': f'https://example.org/{item_id}_{k}.zip'} for k in packages]}


class TestEsponConfigGenerator(unittest.TestCase):
    def indicators(self):
        return [
            api_indicator(7, 'Seven', parents=('B theme', 'A theme')),
            api_indicator(2, 'Two', parents=('A theme', 'B theme')),
            api_indicator(5, 'Five'),
            api_indicator(9, 'Only csv', packages=('csv',)),
            api_indicator(4, 'No package', packages=()),
            api_indicator(3, 'Three packages', parents=('A theme',), packages=('other', 'shape', 'csv')),
            api_indicator(2, 'Two', parents=('A theme', 'B theme')),
        ]

    def test_grouping_order_and_skipped(self):
        config, skipped = espon.build_espon_config(self.indicators())
        self.assertEqual([v['dimension'] for v in config['variables']],
                         [['A theme', 'B theme'], ['A theme'], ['no parent']])
        self.assertEqual([[f['id'] for f in v['features']] for v in config['variables']], [[2, 7], [3], [5]])
        self.assertEqual(sorted(config['variables'][0]['features'][0]), ['csv', 'id', 'name', 'shape', 'years_string'])
        self.assertEqual(config['variables'][1]['features'][0]['shape'], 'https://example.org/3_shape.zip')
        self.assertEqual([(i, reason) for i, _, reason in skipped],
                         [(4, 'no csv and no shape package'), (9, 'no shape package')])

    def test_result_does_not_depend_on_the_order_of_the_input(self):
        indicators = self.indicators()
        expected = espon.build_espon_config(indicators)
        for parents_reversed in (False, True):
            shuffled = list(reversed(indicators))
            if parents_reversed:
                for item in shuffled:
                    item['parents'] = list(reversed(item['parents']))
            self.assertEqual(espon.build_espon_config(shuffled), expected)

    def test_generated_config_works_with_the_targets(self):
        config, _ = espon.build_espon_config(self.indicators())
        targets = espon_targets(config, 80)
        self.assertEqual(len(targets), 4)
        self.assertEqual(len({(t['folder'], t['name']) for t in targets}), 4)

    def test_fetch_reads_all_pages(self):
        indicators = [api_indicator(i, f'I{i}') for i in range(1, 8)]
        self.assertEqual(espon.fetch_espon_indicators(FakeScraper(indicators), page_size=3), indicators)

    def test_fetch_fails_on_a_failed_page(self):
        indicators = [api_indicator(i, f'I{i}') for i in range(1, 8)]
        with self.assertRaises(RuntimeError):
            espon.fetch_espon_indicators(FakeScraper(indicators, fail_at_offset=3), page_size=3)

    def test_fetch_fails_on_an_incomplete_list(self):
        indicators = [api_indicator(i, f'I{i}') for i in range(1, 8)]
        with self.assertRaises(RuntimeError):
            espon.fetch_espon_indicators(FakeScraper(indicators, count=9), page_size=3)

    def test_generate_writes_the_file(self):
        indicators = self.indicators()
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, 'espon.json')
            with mock.patch.object(espon, 'fetch_espon_indicators', return_value=indicators):
                espon.generate_espon_json(target)
            with open(target, encoding='utf-8') as f:
                self.assertEqual(json.load(f), espon.build_espon_config(indicators)[0])
            self.assertEqual(os.listdir(tmp), ['espon.json'])


if __name__ == '__main__':
    unittest.main()
