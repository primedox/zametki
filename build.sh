#!/usr/bin/env bash
# Usage: ./build.sh [apk|aab]
#   apk - debug APK, installs on any phone (default)
#   aab - signed release bundle for Google Play
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-apk}"
case "$MODE" in apk|aab) ;; *) echo "Usage: ./build.sh [apk|aab]"; exit 1 ;; esac

if [ "$(uname -s)" != "Linux" ]; then
  echo "Нужен Linux (или WSL на Windows). На Windows запускайте build.bat"; exit 1
fi

need_apt=0
for tool in git zip unzip python3 pip3 javac ant autoconf libtool; do
  command -v "$tool" >/dev/null 2>&1 || need_apt=1
done
python3 -c "import venv" 2>/dev/null || need_apt=1

if [ "$need_apt" = "1" ]; then
  echo "==> Устанавливаю системные пакеты (потребуется пароль sudo)"
  sudo apt-get update
  sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip python3-venv python3-dev \
    autoconf automake libtool pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev \
    build-essential ccache libltdl-dev
  sudo apt-get install -y --no-install-recommends ant
fi

if [ -d /usr/lib/jvm/java-17-openjdk-amd64 ]; then
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export PATH="$JAVA_HOME/bin:$PATH"
fi

if [ ! -d .venv ]; then
  python3 -m venv .uvtool
  .uvtool/bin/pip install -q uv
  .uvtool/bin/uv venv --seed --python 3.11 .venv || python3 -m venv .venv
  rm -rf .uvtool
fi
. .venv/bin/activate
echo "==> Python для сборки: $(python --version)"
pip install --upgrade pip wheel "setuptools<81" >/dev/null
pip install --upgrade buildozer "cython==0.29.37" >/dev/null

python3 -I -m unittest discover -s tests >/dev/null && echo "==> Тесты пройдены"

if [ "$MODE" = "apk" ]; then
  echo "==> Сборка APK (первый запуск 20-40 минут: скачивается Android SDK/NDK)"
  buildozer android debug
else
  if [ ! -f release.keystore ]; then
    PASS="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
    keytool -genkeypair -v -keystore release.keystore -alias zametki -keyalg RSA -keysize 2048 \
      -validity 10000 -storepass "$PASS" -keypass "$PASS" -dname "CN=Zametki, O=Zametki, C=RU"
    printf '%s' "$PASS" > release.keystore.pass
    chmod 600 release.keystore.pass
    echo "==> Ключ создан: release.keystore (пароль в release.keystore.pass). Сохраните оба файла!"
  fi
  PASS="$(cat release.keystore.pass)"
  export P4A_RELEASE_KEYSTORE="$PWD/release.keystore"
  export P4A_RELEASE_KEYALIAS="zametki"
  export P4A_RELEASE_KEYSTORE_PASSWD="$PASS"
  export P4A_RELEASE_KEYALIAS_PASSWD="$PASS"
  buildozer android release
fi

echo
echo "==> Готово. Файлы в папке bin/:"
ls -1 bin/*.apk bin/*.aab 2>/dev/null || true
