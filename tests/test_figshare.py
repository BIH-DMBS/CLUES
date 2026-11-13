"""
Tests for the download of Figshare records (utils.download_ntl_glwd), used for the
Global Lakes and Wetlands Database (GLWD) and the night time lights.

No network access is needed, Figshare is replaced by a fake.
Run from the repository root:

    python -m unittest discover -s tests -v
"""
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

import numpy as np
import rasterio
from rasterio.transform import from_origin

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'utils'))
import utils  # noqa: E402

CONFIG_NAME = 'hydrosheds_GLWD.json'
ZIP_NAME = 'GLWD_v2_0_area_by_class_pct_tif.zip'
PDF_NAME = 'GLWD_TechDoc_v2_0.pdf'


def global_tif_bytes(offset):
    # a small "global" raster: 360 x 180 pixels of 1 degree
    cols, rows = np.meshgrid(np.arange(360), np.arange(180))
    data = ((cols + rows + offset) % 101).astype('uint8')
    with rasterio.MemoryFile() as memory_file:
        with memory_file.open(driver='GTiff', height=180, width=360, count=1, dtype='uint8', crs='EPSG:4326',
                              transform=from_origin(-180, 90, 1, 1), nodata=255) as dst:
            dst.write(data, 1)
        return memory_file.read(), data


def zip_bytes(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for name, content in members.items():
            z.writestr(name, content)
    return buffer.getvalue()


class FigshareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = os.path.join(self.tmp.name, 'data', 'Global_Lakes_and_Wetlands_Database_(GLWD)')
        self.work = os.path.join(self.tmp.name, 'tmp')
        tif1, self.data1 = global_tif_bytes(0)
        tif2, self.data2 = global_tif_bytes(7)
        self.content = {
            PDF_NAME: b'%PDF-1.4 technical documentation',
            ZIP_NAME: zip_bytes({'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tif': tif1,
                                 'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_02.tif': tif2,
                                 'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tif.ovr': b'overviews of the complete raster',
                                 'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tfw': b'extent of the complete raster',
                                 'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tif.vat.dbf': b'attribute table',
                                 'GLWD_v2_0_area_pct/legend.txt': b'class names'}),
            'GLWD_v2_0_combined_classes_tif.zip': zip_bytes({'other.tif': tif1}),
        }
        self.record = [{'name': name, 'size': len(content), 'download_url': 'https://figshare.invalid/' + name,
                        'computed_md5': hashlib.md5(content).hexdigest()} for name, content in self.content.items()]
        self.downloads = []
        self.versions = []
        self.broken = None
        self.config = self.write_config()

        def fake_download(url, target, max_retries=3):
            name = url.split('/')[-1]
            self.downloads.append(name)
            if self.broken == 'fails' and name == ZIP_NAME:
                raise RuntimeError(f"Failed to download {url}")
            content = self.content[name]
            if self.broken == 'corrupted' and name == ZIP_NAME:
                content = content[:-1] + b'x'
            with open(target, 'wb') as f:
                f.write(content)

        for name, value in {'download_folder': os.path.join(self.tmp.name, 'data'), 'tmp_folder': self.work,
                            'area': 'Brandenburg', 'config_folder': os.path.join(REPO, 'config'),
                            'get_all_files': self.fake_listing,
                            'download_file': fake_download}.items():
            patcher = mock.patch.object(utils, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_listing(self, article_id, version=None):
        self.versions.append((article_id, version))
        return [dict(f) for f in self.record]

    def write_config(self, **changes):
        with open(os.path.join(REPO, 'configs_sources', CONFIG_NAME), encoding='utf-8') as f:
            config = json.load(f)
        header = {k: changes.pop(k) for k in list(changes) if k == 'cut_to_area'}
        config.update(header)
        config['variables'][0].update(changes)
        for key, value in list(config['variables'][0].items()):
            if value is None:
                del config['variables'][0][key]
        path = os.path.join(self.tmp.name, CONFIG_NAME)
        with open(path, 'w') as f:
            json.dump(config, f)
        return path

    def listing(self):
        return sorted(os.path.relpath(os.path.join(root, name), self.folder).replace(os.sep, '/')
                      for root, _, names in os.walk(self.folder) for name in names)


class TestDownloadFigshare(FigshareTest):
    def test_default_config_stores_the_class_layers_cut_to_the_area(self):
        utils.download_ntl_glwd(self.config)
        # the overviews (.ovr) and the world file (.tfw) of the complete raster are not kept next to the cut raster
        self.assertEqual(self.listing(), ['GLWD_TechDoc_v2_0.pdf', 'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tif',
                                          'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tif.vat.dbf',
                                          'GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_02.tif', 'GLWD_v2_0_area_pct/legend.txt'])
        # only the configured files are downloaded, the flag file (pdf) last
        self.assertEqual(self.downloads, [ZIP_NAME, PDF_NAME])
        with rasterio.open(os.path.join(self.folder, 'GLWD_v2_0_area_pct', 'GLWD_v2_0_area_pct_02.tif')) as src:
            # Brandenburg [53.5587, 11.2682, 51.3618, 14.7636] with a margin of 10 pixels of 1 degree
            self.assertEqual((src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top), (1.0, 25.0, 41.0, 64.0))
            np.testing.assert_array_equal(src.read(1), self.data2[26:49, 181:205])
            self.assertEqual(src.nodata, 255)
        self.assertEqual(os.listdir(self.work), [])  # nothing left in the temporary folder

    def test_without_cut_to_area_the_complete_files_are_stored(self):
        utils.download_ntl_glwd(self.write_config(cut_to_area=False))
        with rasterio.open(os.path.join(self.folder, 'GLWD_v2_0_area_pct', 'GLWD_v2_0_area_pct_01.tif')) as src:
            self.assertEqual((src.width, src.height), (360, 180))
            np.testing.assert_array_equal(src.read(1), self.data1)
        self.assertIn('GLWD_v2_0_area_pct/GLWD_v2_0_area_pct_01.tif.ovr', self.listing())  # complete files keep their helper files

    def test_all_files_of_the_record(self):
        utils.download_ntl_glwd(self.write_config(files_oi='all'))
        self.assertEqual(len(self.downloads), 3)
        self.assertEqual(self.downloads[-1], PDF_NAME)
        self.assertIn('other.tif', self.listing())

    def test_wrong_checksum_is_an_error_and_writes_no_flag_file(self):
        self.broken = 'corrupted'
        with self.assertRaises(RuntimeError) as context:
            utils.download_ntl_glwd(self.config)
        self.assertIn('Checksum', str(context.exception))
        self.assertEqual(self.listing(), [])
        self.assertEqual(os.listdir(self.work), [])

    def test_failed_download_is_an_error_and_writes_no_flag_file(self):
        self.broken = 'fails'
        with self.assertRaises(RuntimeError):
            utils.download_ntl_glwd(self.config)
        self.assertNotIn(PDF_NAME, self.listing())

    def test_file_name_that_is_not_in_the_record_is_an_error(self):
        with self.assertRaises(RuntimeError) as context:
            utils.download_ntl_glwd(self.write_config(files_oi=['renamed_file.zip', PDF_NAME]))
        self.assertIn('renamed_file.zip', str(context.exception))
        self.assertEqual(self.downloads, [])

    def test_config_without_article_id_is_a_clear_error(self):
        with self.assertRaises(KeyError) as context:
            utils.download_ntl_glwd(self.write_config(article_id=None))
        self.assertIn('article_id', str(context.exception))

    def test_flag_file_that_is_not_downloaded_is_an_error(self):
        with self.assertRaises(RuntimeError) as context:
            utils.download_ntl_glwd(self.write_config(files_oi=[ZIP_NAME]))
        self.assertIn('flag file', str(context.exception))


class TestNightTimeLights(FigshareTest):
    """ntl.json: all files of a fixed version of the record, stored completely."""

    def setUp(self):
        super().setUp()
        self.folder = os.path.join(self.tmp.name, 'data', 'Night_Time_Lights_(NTL)')
        tif_1992, self.data_1992 = global_tif_bytes(1)
        tif_1993, _ = global_tif_bytes(2)
        self.content = {'Harmonized_DN_NTL_1992_calDMSP.tif': tif_1992, 'Harmonized_DN_NTL_1993_calDMSP.tif': tif_1993}
        self.record = [{'name': name, 'size': len(content), 'download_url': 'https://figshare.invalid/' + name,
                        'computed_md5': hashlib.md5(content).hexdigest()} for name, content in self.content.items()]
        self.config = os.path.join(REPO, 'configs_sources', 'ntl.json')

    def test_all_files_of_the_configured_version_are_stored_completely(self):
        utils.download_ntl_glwd(self.config)
        self.assertEqual(self.versions, [(9828827, 10)])
        self.assertEqual(self.listing(), ['Harmonized_DN_NTL_1992_calDMSP.tif', 'Harmonized_DN_NTL_1993_calDMSP.tif'])
        # the flag file (1992) is stored last
        self.assertEqual(self.downloads, ['Harmonized_DN_NTL_1993_calDMSP.tif', 'Harmonized_DN_NTL_1992_calDMSP.tif'])
        with rasterio.open(os.path.join(self.folder, 'Harmonized_DN_NTL_1992_calDMSP.tif')) as src:
            self.assertEqual((src.width, src.height), (360, 180))
            np.testing.assert_array_equal(src.read(1), self.data_1992)

    def test_complete_files_of_an_interrupted_run_are_not_downloaded_again(self):
        os.makedirs(self.folder)
        with open(os.path.join(self.folder, 'Harmonized_DN_NTL_1993_calDMSP.tif'), 'wb') as f:
            f.write(self.content['Harmonized_DN_NTL_1993_calDMSP.tif'])
        utils.download_ntl_glwd(self.config)
        self.assertEqual(self.downloads, ['Harmonized_DN_NTL_1992_calDMSP.tif'])

    def test_damaged_file_of_an_interrupted_run_is_downloaded_again(self):
        os.makedirs(self.folder)
        content = self.content['Harmonized_DN_NTL_1993_calDMSP.tif']
        with open(os.path.join(self.folder, 'Harmonized_DN_NTL_1993_calDMSP.tif'), 'wb') as f:
            f.write(content[:-1] + b'x')  # same size, other content
        utils.download_ntl_glwd(self.config)
        self.assertEqual(len(self.downloads), 2)
        with open(os.path.join(self.folder, 'Harmonized_DN_NTL_1993_calDMSP.tif'), 'rb') as f:
            self.assertEqual(f.read(), content)

    def test_ntl_config(self):
        with open(self.config, encoding='utf-8') as f:
            config = json.load(f)
        variable = config['variables'][0]
        self.assertEqual((variable['article_id'], variable['version'], variable['files_oi']), (9828827, 10, 'all'))
        self.assertFalse(config.get('cut_to_area', False))
        self.assertTrue(variable['flagFile'].endswith('.tif'))  # the snakemake rule waits for a .tif file
        headers = []
        for folder in ('configs_sources', 'configs_sources_test', os.path.join('docker', 'configs_sources')):
            with open(os.path.join(REPO, folder, 'ntl.json'), encoding='utf-8') as f:
                other = json.load(f)
            other.pop('variables')
            headers.append(other)
        self.assertEqual(headers[0], headers[1])
        self.assertEqual(headers[0], headers[2])


class TestGlwdConfig(unittest.TestCase):
    def load(self, folder):
        with open(os.path.join(REPO, folder, CONFIG_NAME), encoding='utf-8') as f:
            return json.load(f)

    def test_default_config_has_what_the_download_needs(self):
        variable = self.load('configs_sources')['variables'][0]
        self.assertEqual(variable['article_id'], 28519994)
        self.assertIn(variable['flagFile'], variable['files_oi'])
        self.assertTrue(variable['flagFile'].endswith('.pdf'))  # the snakemake rule waits for a .pdf file

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
