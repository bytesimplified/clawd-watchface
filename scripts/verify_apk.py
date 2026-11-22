"""Catch Android's uncompressed, four-byte-aligned resource-table requirement."""
import argparse
from pathlib import Path
import struct
import zipfile

def verify(path):
    with zipfile.ZipFile(path) as archive, open(path, 'rb') as stream:
        info = archive.getinfo('resources.arsc')
        if info.compress_type != zipfile.ZIP_STORED:
            raise ValueError('resources.arsc must be stored uncompressed')
        stream.seek(info.header_offset)
        header = stream.read(30)
        name_len, extra_len = struct.unpack_from('<HH', header, 26)
        offset = info.header_offset + 30 + name_len + extra_len
        if offset % 4:
            raise ValueError(f'resources.arsc is not four-byte aligned: {offset}')
        if archive.testzip() is not None:
            raise ValueError('APK contains a corrupt ZIP entry')
    return offset

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    print('PASS: uncompressed/aligned resource table at', verify(parser.parse_args().apk))
