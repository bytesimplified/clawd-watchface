"""Build the resource-only WFF APK directly with Android SDK Build Tools 35.0.0.

No APK patching, Gradle, private key in source, or Java compilation is needed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET
from verify_apk import verify

ROOT = Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'

def run(*args, env=None):
    subprocess.run([str(arg) for arg in args], check=True, env=env)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keystore', type=Path, help='Persistent private keystore; omit for a separate preview package')
    parser.add_argument('--key-alias', default='androiddebugkey')
    args = parser.parse_args()
    sdk = Path(os.environ.get('ANDROID_HOME', os.environ.get('ANDROID_SDK_ROOT', '')))
    tools = Path(os.environ.get('SDK_BUILD_TOOLS', str(sdk / 'build-tools/35.0.0')))
    platform = Path(os.environ.get('ANDROID_JAR', str(sdk / 'platforms/android-35/android.jar')))
    if not platform.is_file() or not (tools / 'aapt2').is_file():
        parser.error('Install platforms;android-35 and build-tools;35.0.0 and set ANDROID_HOME')
    output = ROOT / 'build'
    dist = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)
    manifest = ET.parse(ROOT / 'watchface/src/main/AndroidManifest.xml')
    env = os.environ.copy()
    alias = args.key_alias
    if args.keystore:
        keystore = args.keystore.resolve()
        if not keystore.is_file() or not env.get('CLAWD_STORE_PASSWORD'):
            parser.error('--keystore requires an existing file and CLAWD_STORE_PASSWORD')
        env.setdefault('CLAWD_KEY_PASSWORD', env['CLAWD_STORE_PASSWORD'])
        filename = 'clawd-charged.apk'
    else:
        # Preview installs beside the personal build. Local previews reuse a local key;
        # clean CI runners intentionally make a new test key, never a release identity.
        manifest.getroot().set('package', 'dev.clawd.terminal.preview')
        manifest.getroot().find('application').set(ANDROID + 'label', 'Clawd Preview')
        manifest.getroot().find('application').set(ANDROID + 'debuggable', 'true')
        keys = ROOT / '.signing'
        keys.mkdir(exist_ok=True)
        keystore = keys / 'preview.keystore'
        alias = 'androiddebugkey'
        env['CLAWD_STORE_PASSWORD'] = env['CLAWD_KEY_PASSWORD'] = 'android'
        if not keystore.exists():
            run('keytool', '-genkeypair', '-keystore', keystore,
                '-storepass:env', 'CLAWD_STORE_PASSWORD', '-keypass:env', 'CLAWD_KEY_PASSWORD',
                '-alias', alias, '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
                '-dname', 'CN=Clawd Preview', '-noprompt', env=env)
        filename = 'clawd-preview.apk'
    ET.register_namespace('android', ANDROID[1:-1])
    manifest_path = output / 'AndroidManifest.xml'
    manifest.write(manifest_path, encoding='utf-8', xml_declaration=True)
    run(tools / 'aapt2', 'compile', '--dir', ROOT / 'watchface/src/main/res', '-o', output / 'resources.zip')
    run(tools / 'aapt2', 'link', '-I', platform, '--manifest', manifest_path,
        '-o', output / 'unsigned.apk', output / 'resources.zip')
    run(tools / 'zipalign', '-f', '4', output / 'unsigned.apk', output / 'aligned.apk')
    apk = dist / filename
    run(tools / 'apksigner', 'sign', '--ks', keystore, '--ks-key-alias', alias,
        '--ks-pass', 'env:CLAWD_STORE_PASSWORD', '--key-pass', 'env:CLAWD_KEY_PASSWORD',
        '--out', apk, output / 'aligned.apk', env=env)
    run(tools / 'apksigner', 'verify', '--verbose', apk)
    run(tools / 'zipalign', '-c', '4', apk)
    verify(apk)
    (dist / (filename + '.sha256')).write_text(hashlib.sha256(apk.read_bytes()).hexdigest() + '  ' + filename + '\n')
    print('Built and verified:', apk)

if __name__ == '__main__':
    main()
