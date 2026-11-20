def rgba(value, alpha=1.0):
    value = value.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return [r, g, b, alpha]


PALETTES = {
    "light": {
        "bg": "#F4F6FB", "surface": "#FFFFFF", "fg": "#161A2B", "sub": "#7B8197",
        "line_c": "#E6E9F2", "chip": "#EBEEF8", "accent": "#5468FF",
        "accent_soft": "#E7EAFF", "danger": "#E5484D",
    },
    "dark": {
        "bg": "#0F111A", "surface": "#181B27", "fg": "#EEF0FA", "sub": "#8B91A8",
        "line_c": "#262A3A", "chip": "#222637", "accent": "#7C8DFF",
        "accent_soft": "#262C55", "danger": "#FF6B70",
    },
}

FOLDERS = [
    ("Личное", "#F5A524"),
    ("Работа", "#2FBF71"),
    ("Другое", "#3B82F6"),
    ("Без папки", "#EF5B5B"),
]

NOTE_PAPER = {
    "light": [None, "#FFF3D6", "#E3F6E8", "#E1ECFF", "#FDE4E4", "#EDE5FF"],
    "dark": [None, "#3A3220", "#1F3328", "#1F2C45", "#40262A", "#32284A"],
}
NOTE_STRIP = ["#5468FF", "#FFB703", "#2FBF71", "#3B82F6", "#EF5B5B", "#8B5CF6"]
LESSON_COLORS = NOTE_STRIP
FONT_SIZES = ["16sp", "19sp", "23sp"]


def paper(index, dark):
    table = NOTE_PAPER["dark" if dark else "light"]
    value = table[index % len(table)]
    return rgba(value) if value else None
