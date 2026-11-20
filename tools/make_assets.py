"""Generates icons and launcher artwork into ./assets (run once, results are committed)."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, "assets", "icons")
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ICONS, exist_ok=True)

GRID = 24
SS = 16          # supersampling: 24 units -> 384 px
OUT = 96
STROKE = 2.0
WHITE = (255, 255, 255, 255)


class Pen:
    def __init__(self):
        self.img = Image.new("RGBA", (GRID * SS, GRID * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    @staticmethod
    def p(pt):
        return (pt[0] * SS, pt[1] * SS)

    def dot(self, pt, r):
        x, y = self.p(pt)
        self.d.ellipse((x - r * SS, y - r * SS, x + r * SS, y + r * SS), fill=WHITE)

    def line(self, a, b, w=STROKE):
        self.d.line((self.p(a), self.p(b)), fill=WHITE, width=int(w * SS))
        self.dot(a, w / 2)
        self.dot(b, w / 2)

    def poly(self, pts, w=STROKE, closed=False):
        pts = list(pts) + ([pts[0]] if closed else [])
        for a, b in zip(pts, pts[1:]):
            self.line(a, b, w)

    def rrect(self, box, r, w=STROKE, fill=False):
        x0, y0, x1, y1 = [v * SS for v in box]
        if fill:
            self.d.rounded_rectangle((x0, y0, x1, y1), r * SS, fill=WHITE)
        else:
            self.d.rounded_rectangle((x0, y0, x1, y1), r * SS, outline=WHITE, width=int(w * SS))

    def circle(self, c, r, w=STROKE, fill=False):
        x, y = self.p(c)
        box = (x - r * SS, y - r * SS, x + r * SS, y + r * SS)
        if fill:
            self.d.ellipse(box, fill=WHITE)
        else:
            self.d.ellipse(box, outline=WHITE, width=int(w * SS))

    def erase(self, fn):
        mask = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        saved = self.img, self.d
        self.img, self.d = mask, ImageDraw.Draw(mask)
        fn(self)
        mask_img = self.img
        self.img, self.d = saved
        alpha = np.array(self.img)[:, :, 3].astype(int)
        cut = np.array(mask_img)[:, :, 3].astype(int)
        arr = np.array(self.img)
        arr[:, :, 3] = np.clip(alpha - cut, 0, 255).astype("uint8")
        self.img = Image.fromarray(arr, "RGBA")

    def save(self, name):
        self.img.resize((OUT, OUT), Image.LANCZOS).save(os.path.join(ICONS, name + ".png"))


def icon(name):
    def wrap(fn):
        pen = Pen()
        fn(pen)
        pen.save(name)
        return fn
    return wrap


@icon("back")
def _(p):
    p.line((20, 12), (5, 12))
    p.poly([(11, 6), (5, 12), (11, 18)])


@icon("chevron_left")
def _(p):
    p.poly([(15, 5), (8, 12), (15, 19)])


@icon("chevron_right")
def _(p):
    p.poly([(9, 5), (16, 12), (9, 19)])


@icon("plus")
def _(p):
    p.line((12, 5), (12, 19), 2.4)
    p.line((5, 12), (19, 12), 2.4)


@icon("close")
def _(p):
    p.line((6, 6), (18, 18))
    p.line((18, 6), (6, 18))


@icon("check")
def _(p):
    p.poly([(5, 12.5), (10, 17.5), (19, 7)], 2.4)


@icon("search")
def _(p):
    p.circle((10.5, 10.5), 6)
    p.line((15, 15), (20, 20))


@icon("sort")
def _(p):
    p.line((4, 7), (20, 7))
    p.line((4, 12), (14, 12))
    p.line((4, 17), (9, 17))


@icon("more")
def _(p):
    for x in (5, 12, 19):
        p.dot((x, 12), 1.8)


@icon("notes")
def _(p):
    p.rrect((5, 3, 19, 21), 3.5)
    p.line((9, 9), (15, 9))
    p.line((9, 13), (15, 13))
    p.line((9, 17), (12, 17))


@icon("calendar")
def _(p):
    p.rrect((4, 5, 20, 20), 3.5)
    p.line((4, 10), (20, 10))
    p.line((8, 3), (8, 7))
    p.line((16, 3), (16, 7))


@icon("clock")
def _(p):
    p.circle((12, 12), 8.5)
    p.poly([(12, 7), (12, 12), (15.5, 14)])


@icon("tune")
def _(p):
    p.line((4, 8), (20, 8))
    p.line((4, 16), (20, 16))
    p.circle((9, 8), 2.8, fill=True)
    p.circle((15, 16), 2.8, fill=True)


@icon("pin")
def _(p):
    p.poly([(9, 4), (15, 4), (14, 10), (18, 13.5), (6, 13.5), (10, 10)], 1.9, closed=True)
    p.line((12, 14), (12, 21))


@icon("trash")
def _(p):
    p.line((4, 7), (20, 7))
    p.poly([(9, 7), (9, 4), (15, 4), (15, 7)])
    p.poly([(6, 7), (7, 20), (17, 20), (18, 7)])
    p.line((10, 11), (10, 16))
    p.line((14, 11), (14, 16))


@icon("copy")
def _(p):
    p.rrect((9, 9, 20, 21), 2.5)
    p.poly([(6, 15), (5, 15), (5, 4), (15, 4), (15, 6)])


@icon("checklist")
def _(p):
    p.poly([(4, 6.5), (6, 8.5), (9, 5)], 1.8)
    p.line((12, 7), (20, 7))
    p.poly([(4, 16.5), (6, 18.5), (9, 15)], 1.8)
    p.line((12, 17), (20, 17))


@icon("box")
def _(p):
    p.rrect((4, 4, 20, 20), 5, 2.0)


@icon("box_on")
def _(p):
    p.rrect((4, 4, 20, 20), 5, fill=True)
    p.erase(lambda q: q.poly([(8, 12.3), (11, 15.3), (16.3, 9.2)], 2.2))


@icon("edit")
def _(p):
    p.poly([(15, 5), (19, 9), (8, 20), (4, 20), (4, 16)], 1.9, closed=True)
    p.line((13, 7), (17, 11))


@icon("palette")
def _(p):
    p.circle((12, 12), 8.5)
    for pt in ((8.5, 10), (12, 7.5), (15.5, 10)):
        p.dot(pt, 1.3)


@icon("share")
def _(p):
    p.circle((6, 12), 2.4, fill=True)
    p.circle((18, 6), 2.4, fill=True)
    p.circle((18, 18), 2.4, fill=True)
    p.line((6, 12), (18, 6), 1.6)
    p.line((6, 12), (18, 18), 1.6)


def find_font():
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return path
    return None


def font_icon():
    img = Image.new("RGBA", (OUT * 4, OUT * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    path = find_font()
    font = ImageFont.truetype(path, 250) if path else ImageFont.load_default()
    box = d.textbbox((0, 0), "Aa", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((OUT * 4 - w) / 2 - box[0], (OUT * 4 - h) / 2 - box[1]), "Aa", font=font, fill=WHITE)
    img.resize((OUT, OUT), Image.LANCZOS).save(os.path.join(ICONS, "font.png"))


font_icon()


# ---------- launcher artwork ----------
SIZE = 1024


def gradient(size):
    ys, xs = np.mgrid[0:size, 0:size].astype("float32") / (size - 1)
    t = (xs * 0.55 + ys * 0.75) / 1.3
    top = np.array([122, 138, 255], dtype="float32")
    bottom = np.array([72, 58, 226], dtype="float32")
    rgb = top[None, None, :] * (1 - t[..., None]) + bottom[None, None, :] * t[..., None]
    alpha = np.full((size, size, 1), 255, dtype="float32")
    return Image.fromarray(np.concatenate([rgb, alpha], axis=2).astype("uint8"), "RGBA")


def page_glyph(size, scale):
    """White sheet with a folded corner and two lines, centred; scale = share of canvas."""
    layer = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s2 = size * 2
    w = s2 * scale * 0.72
    h = s2 * scale
    x0, y0 = (s2 - w) / 2, (s2 - h) / 2
    x1, y1 = x0 + w, y0 + h
    fold = w * 0.34
    r = w * 0.14
    d.rounded_rectangle((x0, y0, x1, y1), r, fill=(255, 255, 255, 255))
    # folded corner cut
    cut = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(cut)
    cd.polygon([(x1 - fold, y0 - 2), (x1 + 2, y0 - 2), (x1 + 2, y0 + fold)], fill=(255, 255, 255, 255))
    arr = np.array(layer)
    arr[:, :, 3] = np.clip(arr[:, :, 3].astype(int) - np.array(cut)[:, :, 3].astype(int), 0, 255)
    layer = Image.fromarray(arr.astype("uint8"), "RGBA")
    d = ImageDraw.Draw(layer)
    d.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold - r * 0.2), (x1, y0 + fold)],
              fill=(255, 255, 255, 150))
    d.polygon([(x1 - fold, y0), (x1, y0 + fold), (x1 - fold, y0 + fold)], fill=(255, 255, 255, 150))
    # lines in accent tone
    lx0 = x0 + w * 0.2
    lh = h * 0.045
    for i, frac in enumerate((0.52, 0.68)):
        ly = y0 + h * frac
        lx1 = x1 - w * (0.2 if i == 0 else 0.42)
        d.rounded_rectangle((lx0, ly, lx1, ly + lh), lh / 2, fill=(84, 104, 255, 255))
    return layer.resize((size, size), Image.LANCZOS)


def build_icons():
    bg = gradient(SIZE)
    glyph = page_glyph(SIZE, 0.54)

    full = bg.copy()
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), SIZE * 0.225, fill=255)
    full.putalpha(mask)
    full.alpha_composite(glyph)
    full.resize((512, 512), Image.LANCZOS).save(os.path.join(ASSETS, "icon.png"))

    bg.resize((512, 512), Image.LANCZOS).save(os.path.join(ASSETS, "icon_bg.png"))
    page_glyph(SIZE, 0.40).resize((512, 512), Image.LANCZOS).save(os.path.join(ASSETS, "icon_fg.png"))

    splash = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    splash.alpha_composite(full.resize((512, 512), Image.LANCZOS))
    splash.save(os.path.join(ASSETS, "presplash.png"))


build_icons()
print("assets ready:", len(os.listdir(ICONS)), "icons")
