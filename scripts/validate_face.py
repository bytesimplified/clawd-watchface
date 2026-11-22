"""Validate the editable face against the vendored Google WFF v1 schema."""
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile
import xmlschema

ROOT = Path(__file__).resolve().parents[1]
with TemporaryDirectory() as directory:
    with zipfile.ZipFile(ROOT / 'vendor/wff-v1-schema.zip') as archive:
        archive.extractall(directory)
    xmlschema.XMLSchema11(Path(directory) / 'watchface.xsd').validate(
        ROOT / 'watchface/src/main/res/raw/watchface.xml'
    )
print('PASS: Watch Face Format v1 schema')
