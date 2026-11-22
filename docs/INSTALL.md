# Build and install

## GitHub Actions → S25 Ultra → Watch4

1. Open **Actions → Build watch face** and choose a successful run for the intended branch/commit.
2. Download its `clawd-preview-<commit>` artifact and extract the ZIP in Samsung My Files.
3. In Wear Installer 2 on the phone, connect to the watch's current Wireless debugging IP and connection port. The pairing port is different and only used for initial pairing.
4. Choose **Custom APK**, select `clawd-preview.apk`, and install.
5. Select **Clawd Preview** in the watch-face picker. Keep the phone and watch on the same Wi-Fi during installation.

Preview builds install alongside Clawd Charged. Each clean CI run generates a new test signing key. To install a preview from a different run, uninstall the previous **Clawd Preview** first; this does not require removing **Clawd Charged**. Local preview builds reuse `.signing/preview.keystore` until you remove it.

## Local build on macOS or Linux

Install Java 17 and Android SDK command-line tools, then:

```sh
export ANDROID_HOME="$HOME/Library/Android/sdk"  # adjust for your SDK location
sdkmanager 'platforms;android-35' 'build-tools;35.0.0'
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_face.py
python3 -m unittest discover -s tests -v
python3 scripts/build_apk.py
```

The output is `dist/clawd-preview.apk` with a SHA-256 checksum. The build uses `aapt2`, `zipalign`, and `apksigner`; it does not modify a prebuilt APK. For custom SDK layouts, `SDK_BUILD_TOOLS` and `ANDROID_JAR` override those two locations.

## Update an existing Clawd Charged installation

Use the **same private signing key** that signed the installed app. The original Clawd Minimal key was lost; Clawd Charged v0.5.x and v0.6.0 use the newer key saved in the private development backup. That key is deliberately not in this public repo.

```sh
# Set CLAWD_STORE_PASSWORD and, if different, CLAWD_KEY_PASSWORD privately.
python3 scripts/build_apk.py --keystore /private/path/dev-only.keystore --key-alias androiddebugkey
```

Install `dist/clawd-charged.apk` over Clawd Charged. A different key cannot update the existing package. No release signing credentials are provided to pull-request workflows. Back up your keystore separately; don't commit it.

## Physical-device checks

- Unplugged: coffee, one-second poses, and five-second words.
- Charging: coffee disappears; cable, pack, real battery percentage and bar appear.
- Awake while charging: sleepy blink and travelling spark.
- Full charge: check and completion message, no spark.
- Ambient: static mascot, no spark; brightness remains OS-controlled.
- Unplug again: normal face returns. Watch for the system charging overlay obscuring the face.

Schema and state tests do not validate actual Wear OS rendering, battery consumption, or sensor update timing. Those checks remain on-device work.

## Reviewing the PR stack

Merge PR 1 into `main`, retarget PR 2 to `main` and merge it, then retarget PR 3 to `main` and merge it. Prefer merge commits for the stack; squash/rebase changes ancestry and may require restacking dependent branches. Nothing is automatically merged or published to Play.
