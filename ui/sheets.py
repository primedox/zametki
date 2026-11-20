from datetime import date

from kivy.app import App
from kivy.factory import Factory
from kivy.metrics import dp

from core import dates
from .widgets import MonthGrid, PillBtn, Sheet, SheetBody, SheetRow, Tile


def _title(body, title):
    label = Factory.Label(text=title, bold=True, font_size="19sp", halign="left", valign="middle",
                          size_hint_y=None, height=dp(46), padding=(dp(24), 0))
    label.bind(size=lambda w, s: setattr(w, "text_size", s))
    body.add_widget(label)


def _shell(title):
    sheet = Sheet()
    body = SheetBody()
    if title:
        _title(body, title)
    sheet.add_widget(body)
    return sheet, body


def rows_sheet(title, rows):
    """rows: dicts with text, icon, danger, selected, cb  |  {'section': 'name'}"""
    sheet, body = _shell(title)
    for spec in rows:
        if "section" in spec:
            body.add_widget(Factory.Section(text=spec["section"], padding=(dp(24), 0),
                                            color=App.get_running_app().accent))
            continue
        row = SheetRow(text=spec["text"], icon=spec.get("icon", ""),
                       danger=spec.get("danger", False), selected=spec.get("selected", False),
                       height=dp(spec.get("height", 52)))

        def fire(_w, cb=spec.get("cb")):
            sheet.dismiss()
            if cb:
                cb()

        row.bind(on_release=fire)
        body.add_widget(row)
    sheet.open()
    return sheet


def confirm_sheet(title, message, ok_text, callback, danger=True):
    sheet, body = _shell(title)
    pad = Factory.Pad(padding=(dp(24), 0, dp(24), dp(16)))
    pad.add_widget(Factory.Txt(text=message, font_size="15sp", color=App.get_running_app().sub))
    body.add_widget(pad)
    row = Factory.BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12), padding=(dp(24), 0))
    cancel = PillBtn(text="Отмена", soft=True)
    cancel.bind(on_release=lambda *_: sheet.dismiss())
    ok = PillBtn(text=ok_text)
    if danger:
        ok.bg = App.get_running_app().danger
    ok.bind(on_release=lambda *_: (sheet.dismiss(), callback()))
    row.add_widget(cancel)
    row.add_widget(ok)
    body.add_widget(row)
    sheet.open()
    return sheet


def new_note_sheet(on_pick):
    sheet, body = _shell("Новая заметка")
    row = Factory.BoxLayout(size_hint_y=None, height=dp(116), spacing=dp(12), padding=(dp(20), dp(6)))
    for kind, text, icon in (("text", "Текст", "notes"), ("list", "Список", "checklist")):
        tile = Tile(text=text, icon=icon)
        tile.bind(on_release=lambda _w, k=kind: (sheet.dismiss(), on_pick(k)))
        row.add_widget(tile)
    body.add_widget(row)
    sheet.open()
    return sheet


def date_sheet(current, on_done):
    """current: date or None. on_done receives an ISO string or '' when cleared."""
    sheet, body = _shell("Дата")
    grid = MonthGrid()
    grid.selected = current
    grid.show(current or date.today())
    wrap = Factory.BoxLayout(size_hint_y=None, height=dp(346), padding=(dp(12), 0))
    wrap.add_widget(grid)
    body.add_widget(wrap)
    row = Factory.BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(12),
                            padding=(dp(24), dp(8), dp(24), 0))
    clear = PillBtn(text="Без даты", soft=True)
    clear.bind(on_release=lambda *_: (sheet.dismiss(), on_done("")))
    done = PillBtn(text="Готово")
    done.bind(on_release=lambda *_: (
        sheet.dismiss(), on_done(grid.selected.isoformat() if grid.selected else "")))
    row.add_widget(clear)
    row.add_widget(done)
    body.add_widget(row)
    sheet.open()
    return sheet


SORT_OPTIONS = (
    ("Общие", (("folder", "Папка"), ("name_asc", "Имя (А–Я)"), ("name_desc", "Имя (Я–А)"))),
    ("Время", (
        ("remind", "Дата в заметке"),
        ("updated_desc", "Изменения: сначала новые"),
        ("updated_asc", "Изменения: сначала старые"),
        ("created_desc", "Создание: сначала новые"),
        ("created_asc", "Создание: сначала старые"),
    )),
)


def sort_sheet(current, on_pick):
    rows = []
    for group, options in SORT_OPTIONS:
        rows.append({"section": group})
        for key, label in options:
            rows.append({"text": label, "selected": key == current, "height": 46,
                         "cb": lambda k=key: on_pick(k)})
    return rows_sheet("Сортировать по", rows)


def folder_sheet(folders, current, on_pick):
    rows = [{"text": name, "selected": i == current, "cb": lambda i=i: on_pick(i)}
            for i, (name, _hex) in enumerate(folders)]
    return rows_sheet("Папка", rows)


def weekday_name(index):
    return dates.WD_FULL[index]
