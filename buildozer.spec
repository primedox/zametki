[app]
title = Заметки
package.name = zametki
package.domain = app.zametki
source.dir = .
source.include_exts = py,kv,png
source.exclude_dirs = tests,tools,.github,bin,.buildozer,__pycache__
version = 1.0.3
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/assets/icon_fg.png
icon.adaptive_background.filename = %(source.dir)s/assets/icon_bg.png
presplash.filename = %(source.dir)s/assets/presplash.png
presplash.color = #F4F6FB

android.api = 33
android.minapi = 24
android.ndk = 25b
p4a.branch = v2024.01.21
android.archs = arm64-v8a, armeabi-v7a
android.permissions =
android.accept_sdk_license = True
android.ant_path = /usr/share/ant
android.release_artifact = aab
android.debug_artifact = apk
android.allow_backup = False

[buildozer]
log_level = 2
warn_on_root = 1
