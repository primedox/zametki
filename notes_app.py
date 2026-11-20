import copy
import os

from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.graphics import Color, Rectangle  # noqa: E402
from kivy.core.clipboard import Clipboard  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.lang import Builder  # noqa: E402
from kivy.properties import BooleanProperty, ColorProperty, StringProperty  # noqa: E402
from kivy.uix.floatlayout import FloatLayout  # noqa: E402
from kivy.utils import platform  # noqa: E402

from core import dates, theme  # noqa: E402
from core.store import Store, display_title, note_as_text, preview_text  # noqa: E402
from ui import insets, screens, sheets, widgets  # noqa: E402,F401
from ui.helpers import BASE  # noqa: E402

if platform not in ("android", "ios"):
    Window.size = (400, 820)


class NotesApp(App):
    tab = StringProperty("notes")
    kb_open = BooleanProperty(False)
    inset_info = StringProperty("")
    dark = BooleanProperty(False)
    bg = ColorProperty([1, 1, 1, 1])
    surface = ColorProperty([1, 1, 1, 1])
    fg = ColorProperty([0, 0, 0, 1])
    sub = ColorProperty([.5, .5, .5, 1])
    line_c = ColorProperty([.9, .9, .9, 1])
    chip = ColorProperty([.9, .9, .9, 1])
    accent = ColorProperty([.3, .4, 1, 1])
    accent_soft = ColorProperty([.9, .92, 1, 1])
    danger = ColorProperty([.9, .3, .3, 1])

    booted = False

    def build(self):
        self.title = "Заметки"
        self.icon = os.path.join(BASE, "assets", "icon.png")
        Window.clearcolor = screens.Splash.BG
        Window.softinput_mode = "resize"
        self.shell = FloatLayout()
        with self.shell.canvas.before:
            self._shell_color = Color(*screens.Splash.BG)
            self._shell_rect = Rectangle(pos=self.shell.pos, size=self.shell.size)
        self.shell.bind(pos=self._shell_sync, size=self._shell_sync)
        self.splash = screens.Splash()
        self.shell.add_widget(self.splash)
        # let the splash animation start, then build the real UI underneath it
        Clock.schedule_once(self._boot, 0.55)
        return self.shell

    def _boot(self, _dt):
        self.store = Store(os.path.join(self.user_data_dir, "data.json"))
        self.apply_theme(self.store.prefs.get("theme", "light"))

        Builder.load_file(os.path.join(BASE, "ui", "widgets.kv"))
        Builder.load_file(os.path.join(BASE, "ui", "screens.kv"))

        self._dirty = False
        self._refresh = Clock.create_trigger(lambda _dt: self.refresh_all())
        self.store.subscribe(self._store_changed)

        root = screens.Root()
        self.ui = root
        self.sm = root.ids.sm
        self.editor = root.ids.editor
        self.lesson_screen = root.ids.lesson
        main = root.ids.main
        self.tabs = main.ids.tabs
        self.notes_screen = main.ids.notes
        self.calendar_screen = main.ids.calendar
        self.schedule_screen = main.ids.schedule
        self.more_screen = main.ids.more

        self._max_height = Window.height
        self._kb_trigger = Clock.create_trigger(self._apply_keyboard, 0.12)
        Window.bind(on_keyboard=self._on_key, height=self._on_height)

        # keep clear of the status bar / camera cut-out if the surface is drawn under them
        self._pad_top, self._pad_bottom, note = ((0, 0, "desktop") if platform != "android"
                                                 else insets.measure())
        self.inset_info = "Отступы: %d/%d px  ·  %s" % (self._pad_top, self._pad_bottom, note)
        root.size_hint = (1, None)
        self.shell.add_widget(root, index=1)  # under the splash
        Window.bind(height=self._place_root)
        self.bind(kb_open=self._place_root, bg=self._tint_shell)
        self._tint_shell()
        self._place_root()
        self.booted = True
        Clock.schedule_once(self.splash.finish, 0.1)

    # ---- layout ---------------------------------------------------------
    def _shell_sync(self, *_):
        self._shell_rect.pos = self.shell.pos
        self._shell_rect.size = self.shell.size

    def _tint_shell(self, *_):
        self._shell_color.rgba = self.bg

    def _place_root(self, *_):
        bottom = 0 if self.kb_open else self._pad_bottom
        self.ui.x = 0
        self.ui.y = bottom
        self.ui.width = Window.width
        self.ui.height = max(Window.height - self._pad_top - bottom, 100)

    # ---- keyboard -------------------------------------------------------
    def _on_height(self, _window, height):
        # the window shrinks when the soft keyboard opens; debounce the animation
        self._max_height = max(self._max_height, height)
        self._kb_trigger.cancel()
        self._kb_trigger()

    def _apply_keyboard(self, _dt):
        self.kb_open = Window.height < self._max_height * 0.8

    def on_start(self):
        if self.booted:
            self.style_bars()

    def on_pause(self):
        if self.booted:
            self.editor.flush()
        return True

    def on_stop(self):
        if self.booted:
            self.editor.flush()

    # ---- theme ----------------------------------------------------------
    def apply_theme(self, name):
        name = name if name in theme.PALETTES else "light"
        self.dark = name == "dark"
        for key, value in theme.PALETTES[name].items():
            setattr(self, key, theme.rgba(value))
        Window.clearcolor = self.bg
        self.style_bars()

    def set_theme(self, name):
        if (name == "dark") == self.dark:
            return
        self.store.set_pref("theme", name)
        self.apply_theme(name)
        self.refresh_all()

    def style_bars(self):
        if platform != "android":
            return
        try:
            from android.runnable import run_on_ui_thread
            from jnius import autoclass
        except ImportError:
            return

        def argb(color):
            r, g, b = (int(round(c * 255)) for c in color[:3])
            value = 0xFF000000 | (r << 16) | (g << 8) | b
            return value - (1 << 32) if value >= (1 << 31) else value

        status, nav, light = argb(self.bg), argb(self.surface), not self.dark

        @run_on_ui_thread
        def apply():
            try:
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                window = activity.getWindow()
                window.clearFlags(0x04000000)
                window.addFlags(-2147483648)
                window.setStatusBarColor(status)
                window.setNavigationBarColor(nav)
                decor = window.getDecorView()
                flags = decor.getSystemUiVisibility()
                mask = 0x2000 | 0x10
                decor.setSystemUiVisibility((flags | mask) if light else (flags & ~mask))
            except Exception:
                pass

        apply()

    # ---- refresh --------------------------------------------------------
    def _store_changed(self):
        self._dirty = True
        if self.sm.current == "main":
            self._refresh()

    def refresh_all(self):
        self._dirty = False
        for screen in (self.notes_screen, self.calendar_screen, self.schedule_screen, self.more_screen):
            screen.refresh()

    # ---- navigation -----------------------------------------------------
    def open_tab(self, name):
        self.tab = name
        self.tabs.current = name
        if self._dirty:
            self.refresh_all()

    def show_main(self):
        self.sm.current = "main"
        if self._dirty:
            self.refresh_all()

    def _on_key(self, _window, key, *_args):
        if key != 27 or not self.booted:
            return False
        if self.sm.current == "editor":
            self.editor.close()
            return True
        if self.sm.current == "lesson":
            self.show_main()
            return True
        if self.tab == "notes" and self.notes_screen.clear_search():
            return True
        if self.tab != "notes":
            self.open_tab("notes")
            return True
        return False

    def toast(self, text):
        self.ui.toast(text)

    # ---- notes ----------------------------------------------------------
    def folder_info(self, index):
        folders = theme.FOLDERS
        return folders[index] if 0 <= index < len(folders) else folders[-1]

    def note_row(self, note):
        name, color = self.folder_info(note["folder"])
        paper = theme.paper(note["color"], self.dark)
        strip = theme.NOTE_STRIP[note["color"] % len(theme.NOTE_STRIP)] if note["color"] else color
        day = dates.parse_iso(note["date"])
        return {
            "note_id": note["id"],
            "title": display_title(note),
            "preview": preview_text(note),
            "folder_name": name,
            "folder_color": theme.rgba(color),
            "stamp": dates.stamp(note["updated"]),
            "date_text": dates.short_date(day) if day else "",
            "strip": theme.rgba(strip),
            "bg": paper or self.surface,
            "pinned": note["pinned"],
        }

    def new_note_sheet(self, date=""):
        sheets.new_note_sheet(lambda kind: self.compose(kind, date))

    def compose(self, kind, date=""):
        folder = max(self.notes_screen.folder, 0)
        self.editor.load(self.store.new_note(kind, folder, date), True)
        self.sm.current = "editor"
        Clock.schedule_once(lambda _dt: self.editor.focus_body(), 0.3)

    def open_note(self, note_id):
        note = self.store.get_note(note_id)
        if note is None:
            return
        self.editor.load(copy.deepcopy(note), False)
        self.sm.current = "editor"

    def note_actions(self, note_id):
        note = self.store.get_note(note_id)
        if note is None:
            return

        def copy_text():
            Clipboard.copy(note_as_text(note))
            self.toast("Скопировано")

        sheets.rows_sheet(display_title(note), [
            {"text": "Открепить" if note["pinned"] else "Закрепить", "icon": "pin",
             "cb": lambda: self.store.toggle_pin(note_id)},
            {"text": "Копировать текст", "icon": "copy", "cb": copy_text},
            {"text": "Удалить", "icon": "trash", "danger": True,
             "cb": lambda: sheets.confirm_sheet("Удалить заметку?", "Это действие нельзя отменить.",
                                                "Удалить", lambda: self.store.delete_note(note_id))},
        ])

    # ---- lessons --------------------------------------------------------
    def lesson_row(self, lesson, live=False):
        parts = []
        if lesson["room"]:
            parts.append("каб. " + lesson["room"])
        if lesson["teacher"]:
            parts.append(lesson["teacher"])
        color = theme.LESSON_COLORS[lesson["color"] % len(theme.LESSON_COLORS)]
        return {
            "lesson_id": lesson["id"],
            "time_start": lesson["start"],
            "time_end": lesson["end"],
            "subject": lesson["subject"] or "Без названия",
            "meta": "  ·  ".join(parts),
            "strip": theme.rgba(color),
            "bg": self.accent_soft if live else self.surface,
            "live": live,
        }

    def new_lesson(self, day):
        self.lesson_screen.open(self.store.new_lesson(day), False)
        self.sm.current = "lesson"

    def edit_lesson(self, lesson_id):
        lesson = self.store.get_lesson(lesson_id)
        if lesson is None:
            return
        self.lesson_screen.open(lesson, True)
        self.sm.current = "lesson"

    def after_lesson(self, day):
        self.schedule_screen.day = day
        self.show_main()
        self.open_tab("schedule")
        self.schedule_screen.refresh()


if __name__ == "__main__":
    NotesApp().run()
