import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE, "assets", "icons")


def ipath(name):
    return os.path.join(ICON_DIR, name + ".png") if name else ""


def alpha(color, value):
    return [color[0], color[1], color[2], value]
