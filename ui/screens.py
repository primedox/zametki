import copy
import os
import time
from datetime import date, datetime

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (BooleanProperty, ColorProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from core import APP_VERSION, dates, theme
from core.store import note_as_text, note_is_empty
from . import sheets
from .helpers import BASE
from .widgets import Chip, ColorDot, DayTab, LessonCard, NoteCard, Toast  # noqa: F401  (NoteCard: RecycleView viewclass)


def _app():
    return App.get_running_app()


class Splash(FloatLayout):
    """Short animated start screen drawn over the app while it settles."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = _app()
        with self.canvas.before:
            Color(*app.bg)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)
        self.logo = Image(source=os.path.join(BASE, "assets", "icon.png"),
                          size_hint=(None, None), size=(dp(70), dp(70)),
                          pos_hint={"center_x": .5, "center_y": .56}, opacity=0)
        self.name = Label(text="Заметки", bold=True, font_size="24sp", color=app.fg,
                          size_hint=(None, None), size=(dp(220), dp(40)),
                          pos_hint={"center_x": .5, "center_y": .44}, opacity=0)
        self.add_widget(self.logo)
        self.add_widget(self.name)
        Animation(opacity=1, size=(dp(104), dp(104)), duration=.5, t="out_back").start(self.logo)
        (Animation(duration=.2) + Animation(opacity=1, duration=.4)).start(self.name)
        Clock.schedule_once(self._leave, 1.2)

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _leave(self, _dt):
        anim = Animation(opacity=0, duration=.3)
        anim.bind(on_complete=lambda *_: self.parent and self.parent.remove_widget(self))
        anim.start(self)

    def on_touch_down(self, touch):
        return True

    def on_touch_move(self, touch):
        return True

    def on_touch_up(self, touch):
        return True


class Root(FloatLayout):
    def show_splash(self):
        self.add_widget(Splash())

    def toast(self, text):
        bubble = Toast(text=text)
        self.add_widget(bubble)
        anim = (Animation(opacity=1, duration=0.15) + Animation(opacity=1, duration=1.6)
                + Animation(opacity=0, duration=0.25))
        anim.bind(on_complete=lambda *_: self.remove_widget(bubble))
        anim.start(bubble)


class MainScreen(Screen):
    pass


class NotesScreen(Screen):
    searching = BooleanProperty(False)
    folder = NumericProperty(-1)
    query = StringProperty("")
    empty_title = StringProperty("")
    empty_hint = StringProperty("")

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._chips = []
        specs = [("Все", None, -1)] + [(n, theme.rgba(c), i) for i, (n, c) in enumerate(theme.FOLDERS)]
        for name, tone, index in specs:
            chip = Chip(text=name, tone=tone)
            chip.bind(on_release=lambda _w, i=index: self.set_folder(i))
            self.ids.chips.add_widget(chip)
            self._chips.append((index, chip))
        self.refresh()

    def set_folder(self, index):
        self.folder = -1 if index == self.folder else index
        self.refresh()

    def toggle_search(self):
        self.searching = not self.searching
        if self.searching:
            Clock.schedule_once(lambda _dt: self.ids.search.focus(), 0.05)
        else:
            self.ids.search.text = ""
            self.query = ""
            Window.release_all_keyboards()
            self.refresh()

    def on_query(self, text):
        self.query = text
        self.refresh()

    def open_sort(self):
        app = _app()
        sheets.sort_sheet(app.store.prefs.get("sort", "updated_desc"), self._set_sort)

    def _set_sort(self, key):
        _app().store.set_pref("sort", key)
        self.refresh()

    def refresh(self):
        app = _app()
        for index, chip in self._chips:
            chip.active = index == self.folder
        notes = app.store.query_notes(
            folder=None if self.folder < 0 else self.folder,
            text=self.query,
            sort=app.store.prefs.get("sort", "updated_desc"),
        )
        self.ids.rv.data = [app.note_row(n) for n in notes]
        if self.query or self.folder >= 0:
            self.empty_title = "Ничего не найдено"
            self.empty_hint = "Попробуйте другой запрос или папку"
        else:
            self.empty_title = "Пока здесь пусто"
            self.empty_hint = "Нажмите на карандаш,\nчтобы создать первую заметку"


class CalendarScreen(Screen):
    heading = StringProperty("")
    selected = ObjectProperty(None, allownone=True)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.selected = date.today()
        grid = self.ids.month
        grid.selected = self.selected
        grid.bind(on_pick=self._picked)
        self.refresh()

    def _picked(self, _grid, day):
        self.selected = day
        self.refresh_agenda()

    def go_today(self):
        today = date.today()
        grid = self.ids.month
        grid.show(today)
        grid.pick(today)

    def add_note(self):
        _app().new_note_sheet(date=self.selected.isoformat())

    def refresh(self):
        self.ids.month.marks = frozenset(_app().store.marked_dates())
        self.refresh_agenda()

    def refresh_agenda(self):
        from kivy.factory import Factory
        app = _app()
        day = self.selected or date.today()
        self.heading = dates.day_label(day)
        box = self.ids.agenda
        box.clear_widgets()
        lessons = app.store.lessons_for_day(day.weekday()) if day.weekday() < 6 else []
        notes = app.store.notes_for_date(day.isoformat())
        if lessons:
            box.add_widget(Factory.Section(text="Расписание", padding=(6, 0)))
            live = day == date.today()
            for lesson in lessons:
                box.add_widget(LessonCard(**app.lesson_row(lesson, live)))
        if notes:
            box.add_widget(Factory.Section(text="Заметки", padding=(6, 0)))
            for note in notes:
                box.add_widget(NoteCard(**app.note_row(note)))
        if not lessons and not notes:
            box.add_widget(Factory.Txt(text="На этот день ничего не запланировано",
                                       color=app.sub, font_size="14sp", padding=(6, 0)))


class ScheduleScreen(Screen):
    day = NumericProperty(0)
    summary = StringProperty("")
    empty = BooleanProperty(False)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        today = date.today().weekday()
        self.day = today if today < 6 else 0
        self._tabs = []
        for i in range(6):
            tab = DayTab(text=dates.WD_SHORT[i])
            tab.bind(on_release=lambda _w, i=i: self.select(i))
            self.ids.days.add_widget(tab)
            self._tabs.append(tab)
        self.refresh()

    def select(self, index):
        self.day = index
        self.refresh()

    def add_lesson(self):
        _app().new_lesson(self.day)

    def refresh(self):
        app = _app()
        today = date.today().weekday()
        for i, tab in enumerate(self._tabs):
            count = len(app.store.lessons_for_day(i))
            tab.sub = str(count) if count else "–"
            tab.active = i == self.day
            tab.today = i == today
        lessons = app.store.lessons_for_day(self.day)
        box = self.ids.lessons
        box.clear_widgets()
        now = datetime.now()
        minutes = now.hour * 60 + now.minute
        for lesson in lessons:
            live = False
            if self.day == today:
                start, end = dates.parse_hhmm(lesson["start"]), dates.parse_hhmm(lesson["end"])
                live = start <= minutes < end
            box.add_widget(LessonCard(**app.lesson_row(lesson, live)))
        self.empty = not lessons
        head = dates.WD_FULL[self.day]
        if lessons:
            count = len(lessons)
            word = dates.plural(count, "урок", "урока", "уроков")
            self.summary = "%s  ·  %d %s  ·  %s–%s" % (head, count, word, lessons[0]["start"], lessons[-1]["end"])
        else:
            self.summary = head


class MoreScreen(Screen):
    stats = StringProperty("")
    version = StringProperty(APP_VERSION)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.refresh()

    def refresh(self):
        store = _app().store
        n, k = len(store.notes), len(store.lessons)
        self.stats = "%d %s  ·  %d %s в расписании" % (
            n, dates.plural(n, "заметка", "заметки", "заметок"),
            k, dates.plural(k, "урок", "урока", "уроков"))

    def backup(self):
        Clipboard.copy(_app().store.export_json())
        _app().toast("Резервная копия в буфере обмена")

    def restore(self):
        text = Clipboard.paste() or ""

        def run():
            if _app().store.import_json(text):
                _app().toast("Данные восстановлены")
            else:
                _app().toast("В буфере нет резервной копии")

        sheets.confirm_sheet("Восстановить данные?",
                             "Текущие заметки и расписание будут заменены данными из буфера обмена.",
                             "Восстановить", run, danger=False)

    def wipe(self):
        sheets.confirm_sheet("Удалить все данные?", "Заметки и расписание будут удалены без возможности восстановления.",
                             "Удалить", lambda: (_app().store.clear(), _app().toast("Данные удалены")))


class EditorScreen(Screen):
    kind = StringProperty("text")
    paper = ColorProperty([1, 1, 1, 1])
    pinned = BooleanProperty(False)
    stamp_text = StringProperty("")
    folder_name = StringProperty("")
    folder_color = ColorProperty([1, 1, 1, 1])
    date_text = StringProperty("Без даты")
    has_date = BooleanProperty(False)
    fsize = StringProperty("16sp")

    note = None
    saved = False
    _loading = False
    _touched = False

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._trigger = Clock.create_trigger(lambda _dt: self._commit(), 0.6)
        self._dots = []
        for i in range(len(theme.NOTE_STRIP)):
            dot = ColorDot()
            dot.bind(on_release=lambda _w, i=i: self.set_color(i))
            self.ids.dots.add_widget(dot)
            self._dots.append(dot)
        self.ids.todo.bind(on_change=lambda *_: self.changed())

    # -- lifecycle ---------------------------------------------------------
    def load(self, note, is_new):
        self._loading = True
        self._touched = is_new
        self.note = note
        self.saved = not is_new
        self.kind = note["kind"]
        self.ids.title.text = note["title"]
        self.ids.body.text = note["body"]
        if note["kind"] == "list":
            self.ids.todo.set_items(note["items"])
        self._sync()
        Clock.schedule_once(lambda _dt: setattr(self, "_loading", False), 0)

    def focus_body(self):
        if self.kind == "text":
            self.ids.body.focus = True
        else:
            rows = self.ids.todo.ids.box.children
            for row in reversed(rows):
                if hasattr(row, "ids") and "ti" in row.ids:
                    row.ids.ti.focus = True
                    break

    def flush(self):
        if self.note is not None:
            self._trigger.cancel()
            self._commit()

    def close(self):
        self.flush()
        self.note = None
        Window.release_all_keyboards()
        _app().show_main()

    # -- state -------------------------------------------------------------
    def _sync(self):
        app = _app()
        note = self.note
        self.pinned = note["pinned"]
        self.paper = theme.paper(note["color"], app.dark) or app.bg
        name, color = app.folder_info(note["folder"])
        self.folder_name = name
        self.folder_color = theme.rgba(color)
        day = dates.parse_iso(note["date"])
        self.has_date = bool(day)
        self.date_text = dates.short_date(day) if day else "Без даты"
        self.fsize = theme.FONT_SIZES[note["font"] % len(theme.FONT_SIZES)]
        self.stamp_text = ("Изменено: " + dates.full_stamp(note["updated"])) if self.saved else "Новая заметка"
        for i, dot in enumerate(self._dots):
            dot.fill = theme.paper(i, app.dark) or app.surface
            dot.active = i == note["color"]

    def changed(self):
        if self._loading or self.note is None:
            return
        self._touched = True
        self._trigger()

    def _collect(self):
        note = self.note
        note["title"] = self.ids.title.text
        if self.kind == "list":
            note["items"] = self.ids.todo.get_items()
        else:
            note["body"] = self.ids.body.text

    def _commit(self):
        if self.note is None or not self._touched:
            return
        self._collect()
        if note_is_empty(self.note):
            return
        self._touched = False
        self.note["updated"] = int(time.time())
        self.saved = True
        _app().store.upsert_note(copy.deepcopy(self.note))
        self.stamp_text = "Изменено: " + dates.full_stamp(self.note["updated"])

    # -- actions -----------------------------------------------------------
    def toggle_pin(self):
        self.note["pinned"] = not self.note["pinned"]
        self._sync()
        self.changed()

    def set_color(self, index):
        self.note["color"] = index
        self._sync()
        self.changed()

    def cycle_font(self):
        self.note["font"] = (self.note["font"] + 1) % len(theme.FONT_SIZES)
        self._sync()
        self.changed()

    def pick_folder(self):
        def chosen(index):
            self.note["folder"] = index
            self._sync()
            self.changed()
        sheets.folder_sheet(theme.FOLDERS, self.note["folder"], chosen)

    def pick_date(self):
        def chosen(iso):
            self.note["date"] = iso
            self._sync()
            self.changed()
        sheets.date_sheet(dates.parse_iso(self.note["date"]), chosen)

    def as_text(self):
        self._collect()
        return note_as_text(self.note)

    def more(self):
        def copy_text():
            Clipboard.copy(self.as_text())
            _app().toast("Скопировано")

        sheets.rows_sheet("", [
            {"text": "Копировать текст", "icon": "copy", "cb": copy_text},
            {"text": "Удалить заметку", "icon": "trash", "danger": True, "cb": self.ask_delete},
        ])

    def ask_delete(self):
        sheets.confirm_sheet("Удалить заметку?", "Это действие нельзя отменить.", "Удалить", self._delete)

    def _delete(self):
        note, self.note = self.note, None
        self._trigger.cancel()
        if note is not None:
            _app().store.delete_note(note["id"])
        Window.release_all_keyboards()
        _app().show_main()


class LessonScreen(Screen):
    heading = StringProperty("Новый урок")
    error = StringProperty("")
    exists = BooleanProperty(False)
    day = NumericProperty(0)
    color_idx = NumericProperty(0)

    lesson = None

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        digits = lambda text, _undo: "".join(c for c in text if c.isdigit() or c in ":.")
        self.ids.t_start.filt = digits
        self.ids.t_end.filt = digits
        self._tabs = []
        for i in range(6):
            tab = DayTab(text=dates.WD_SHORT[i], height=dp(50))
            tab.bind(on_release=lambda _w, i=i: self._set_day(i))
            self.ids.days.add_widget(tab)
            self._tabs.append(tab)
        self._dots = []
        for i, hex_color in enumerate(theme.LESSON_COLORS):
            dot = ColorDot(fill=theme.rgba(hex_color))
            dot.bind(on_release=lambda _w, i=i: self._set_color(i))
            self.ids.colors.add_widget(dot)
            self._dots.append(dot)

    def _set_day(self, index):
        self.day = index
        self._paint()

    def _set_color(self, index):
        self.color_idx = index
        self._paint()

    def _paint(self):
        for i, tab in enumerate(self._tabs):
            tab.active = i == self.day
        for i, dot in enumerate(self._dots):
            dot.active = i == self.color_idx

    def open(self, lesson, exists):
        self.lesson = copy.deepcopy(lesson)
        self.exists = exists
        self.error = ""
        self.heading = "Урок" if exists else "Новый урок"
        ids = self.ids
        ids.subject.text = lesson["subject"]
        ids.room.text = lesson["room"]
        ids.teacher.text = lesson["teacher"]
        start, end = lesson["start"], lesson["end"]
        if not exists:
            start, end = self._suggest(lesson["day"])
        ids.t_start.text, ids.t_end.text = start, end
        self.day = lesson["day"]
        self.color_idx = lesson["color"]
        self._paint()

    def _suggest(self, day):
        existing = _app().store.lessons_for_day(day)
        if existing:
            start = dates.parse_hhmm(existing[-1]["end"]) + 10
        else:
            start = 8 * 60 + 30
        return dates.fmt_hhmm(start), dates.fmt_hhmm(start + 45)

    def save(self):
        ids = self.ids
        subject = ids.subject.text.strip()
        start = dates.parse_hhmm(ids.t_start.text)
        end = dates.parse_hhmm(ids.t_end.text)
        if not subject:
            self.error = "Укажите название предмета"
        elif start is None or end is None:
            self.error = "Время нужно вводить так: 08:30"
        elif end <= start:
            self.error = "Конец урока должен быть позже начала"
        else:
            self.lesson.update(
                subject=subject, start=dates.fmt_hhmm(start), end=dates.fmt_hhmm(end),
                room=ids.room.text.strip(), teacher=ids.teacher.text.strip(),
                day=int(self.day), color=int(self.color_idx),
            )
            Window.release_all_keyboards()
            _app().store.upsert_lesson(self.lesson)
            _app().after_lesson(int(self.day))

    def ask_delete(self):
        def run():
            _app().store.delete_lesson(self.lesson["id"])
            _app().show_main()
        sheets.confirm_sheet("Удалить урок?", "Урок исчезнет из расписания.", "Удалить", run)
