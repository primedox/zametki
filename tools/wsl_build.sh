#!/usr/bin/env bash
set -euo pipefail
SRC="$1"
MODE="${2:-apk}"
WORK="$HOME/zametki_build"

mkdir -p "$WORK"
cp -r "$SRC"/. "$WORK"/
cd "$WORK"
rm -rf bin
PROFILE=3
if [ ! -f ".profile_$PROFILE" ]; then
  rm -rf .venv .profile_* .buildozer/android/platform/python-for-android \
    .buildozer/android/platform/build-* .buildozer/android/app
  touch ".profile_$PROFILE"
fi
find . -type f \( -name '*.sh' -o -name '*.py' -o -name '*.kv' -o -name '*.spec' -o -name '*.yml' \) \
  -exec sed -i 's/\r$//' {} +

bash build.sh "$MODE"

mkdir -p "$SRC/bin"
cp -f bin/* "$SRC/bin/"
cp -f release.keystore release.keystore.pass "$SRC/" 2>/dev/null || true
