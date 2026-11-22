import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('verify_apk', Path(__file__).resolve().parents[1] / 'scripts/verify_apk.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PackagingTests(unittest.TestCase):
    def make_archive(self, directory, compression, aligned):
        path = Path(directory) / 'test.apk'
        info = zipfile.ZipInfo('resources.arsc')
        info.compress_type = compression
        # Local header 30 + name 14 = 44; valid extra-field header+payload adds 5.
        if not aligned:
            info.extra = b'\xfe\xca\x01\x00x'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(info, b'resource table fixture')
        return path

    def test_reject_compressed_resource_table(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'uncompressed'):
                module.verify(self.make_archive(d, zipfile.ZIP_DEFLATED, True))

    def test_reject_misaligned_resource_table(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'aligned'):
                module.verify(self.make_archive(d, zipfile.ZIP_STORED, False))

    def test_accept_stored_aligned_resource_table(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(module.verify(self.make_archive(d, zipfile.ZIP_STORED, True)), 44)
