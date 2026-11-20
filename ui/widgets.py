from datetime import date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (BooleanProperty, ColorProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.stencilview import StencilView

from core.dates import MONTHS


class Clip(StencilView, BoxLayout):
    """A box that clips both drawing and touches to its own bounds.

    Used for rows that collapse to zero height (e.g. while the keyboard is
    open): plain zero-height boxes let their fixed-size children overflow and
    silently swallow taps meant for neighbouring widgets.
    """


class Card(BoxLayout):
    bg = ColorProperty([1, 1, 1, 1])
    radius = NumericProperty("18dp")


class IconBtn(ButtonBehavior, FloatLayout):
    icon = StringProperty("plus")
    tint = ObjectProperty(None, allownone=True)
    isize = NumericProperty("24dp")


class PillBtn(ButtonBehavior, Label):
    bg = ObjectProperty(None, allownone=True)
    fg = ObjectProperty(None, allownone=True)
    soft = BooleanProperty(False)


class Chip(ButtonBehavior, Label):
    tone = ObjectProperty(None, allownone=True)
    active = BooleanProperty(False)


class DayTab(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    sub = StringProperty("")
    active = BooleanProperty(False)
    today = BooleanProperty(False)


class Fab(ButtonBehavior, FloatLayout):
    icon = StringProperty("plus")


class NavItem(ButtonBehavior, BoxLayout):
    icon = StringProperty("notes")
    text = StringProperty("")
    active = BooleanProperty(False)


class ColorDot(ButtonBehavior, FloatLayout):
    fill = ColorProperty([1, 1, 1, 1])
    active = BooleanProperty(False)


class Dot(FloatLayout):
    tone = ColorProperty([1, 1, 1, 1])


class Field(Card):
    text = StringProperty("")
    hint = StringProperty("")
    filt = ObjectProperty(None, allownone=True)

    def focus(self):
        self.ids.ti.focus = True


class Toast(Card):
    text = StringProperty("")


class SheetBody(BoxLayout):
    pass


class SheetRow(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    icon = StringProperty("")
    tint = ObjectProperty(None, allownone=True)
    danger = BooleanProperty(False)
    selected = BooleanProperty(False)


class Tile(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    icon = StringProperty("notes")


class Sheet(ModalView):
    """Bottom sheet: a full-window dimmer with the body anchored to the bottom edge."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (1, 1))
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("overlay_color", (0, 0, 0, 0.5))
        kwargs.setdefault("anchor_y", "bottom")
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.children and not self.children[0].collide_point(*touch.pos):
            self.dismiss()
            return True
        return super().on_touch_down(touch)


class NoteCard(ButtonBehavior, Card):
    note_id = StringProperty("")
    title = StringProperty("")
    preview = StringProperty("")
    folder_name = StringProperty("")
    folder_color = ColorProperty([1, 1, 1, 1])
    stamp = StringProperty("")
    date_text = StringProperty("")
    strip = ColorProperty([1, 1, 1, 1])
    pinned = BooleanProperty(False)

    _timer = None
    _fired = False

    def on_press(self):
        self._fired = False
        self._timer = Clock.schedule_once(self._long_press, 0.5)

    def _long_press(self, _dt):
        self._timer = None
        self._fired = True
        App.get_running_app().note_actions(self.note_id)

    def on_state(self, _inst, value):
        if value == "normal" and self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def on_release(self):
        if not self._fired:
            App.get_running_app().open_note(self.note_id)


class LessonCard(ButtonBehavior, Card):
    lesson_id = StringProperty("")
    time_start = StringProperty("")
    time_end = StringProperty("")
    subject = StringProperty("")
    meta = StringProperty("")
    strip = ColorProperty([1, 1, 1, 1])
    live = BooleanProperty(False)

    def on_release(self):
        App.get_running_app().edit_lesson(self.lesson_id)


class ListRow(BoxLayout):
    text = StringProperty("")
    done = BooleanProperty(False)

    __events__ = ("on_enter", "on_remove")

    def on_enter(self):
        pass

    def on_remove(self):
        pass

    def toggle(self):
        self.done = not self.done


class ListEditor(ScrollView):
    __events__ = ("on_change",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items = []
        self._rows = {}

    def on_change(self):
        pass

    def set_items(self, items):
        self.items = [dict(i) for i in items] or [{"t": "", "d": False}]
        box = self.ids.box
        box.clear_widgets()
        self._rows = {}
        for it in self.items:
            box.add_widget(self._make(it))
        self._add_button(box)

    def _add_button(self, box):
        wrap = BoxLayout(size_hint_y=None, height=dp(64), padding=(dp(12), dp(12), dp(12), 0))
        btn = PillBtn(text="Добавить пункт", soft=True)
        btn.bind(on_release=lambda *_: self._insert_after(self.items[-1]))
        wrap.add_widget(btn)
        box.add_widget(wrap, index=0)

    def get_items(self):
        return [dict(i) for i in self.items]

    def _make(self, item):
        row = ListRow(text=item["t"], done=item["d"])
        row.bind(
            text=lambda _w, v, it=item: self._edit(it, "t", v),
            done=lambda _w, v, it=item: self._edit(it, "d", v),
            on_enter=lambda _w, it=item: self._insert_after(it),
            on_remove=lambda _w, it=item: self._remove(it),
        )
        self._rows[id(item)] = row
        return row

    def _edit(self, item, key, value):
        item[key] = value
        self.dispatch("on_change")

    def _insert_after(self, item):
        idx = self.items.index(item)
        fresh = {"t": "", "d": False}
        count = len(self.items)
        self.items.insert(idx + 1, fresh)
        row = self._make(fresh)
        self.ids.box.add_widget(row, index=count - idx)
        Clock.schedule_once(lambda _dt: setattr(row.ids.ti, "focus", True), 0.05)
        self.dispatch("on_change")

    def _remove(self, item):
        if len(self.items) == 1:
            self._rows[id(item)].text = ""
            self._rows[id(item)].done = False
            return
        row = self._rows.pop(id(item))
        self.items.remove(item)
        self.ids.box.remove_widget(row)
        self.dispatch("on_change")


class DayCell(ButtonBehavior, FloatLayout):
    day = ObjectProperty(None, allownone=True)
    label = StringProperty("")
    selected = BooleanProperty(False)
    today = BooleanProperty(False)
    other = BooleanProperty(False)
    marked = BooleanProperty(False)


class MonthGrid(BoxLayout):
    year = NumericProperty(date.today().year)
    month = NumericProperty(date.today().month)
    selected = ObjectProperty(None, allownone=True)
    marks = ObjectProperty(frozenset())

    __events__ = ("on_pick",)

    def __init__(self, **kwargs):
        self._cells = []
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        grid = self.ids.grid
        for _ in range(42):
            cell = DayCell()
            cell.bind(on_release=self._cell_released)
            grid.add_widget(cell)
            self._cells.append(cell)
        for prop in ("year", "month", "selected", "marks"):
            self.fbind(prop, self.refresh)
        self.refresh()

    def on_pick(self, _day):
        pass

    def _cell_released(self, cell):
        self.pick(cell.day)

    def pick(self, day):
        self.selected = day
        if day.month != self.month or day.year != self.year:
            self.year, self.month = day.year, day.month
        self.dispatch("on_pick", day)

    def shift(self, delta):
        index = self.year * 12 + (self.month - 1) + delta
        self.year, self.month = divmod(index, 12)
        self.month += 1

    def show(self, day):
        self.year, self.month = day.year, day.month

    def refresh(self, *_):
        if not self._cells:
            return
        first = date(int(self.year), int(self.month), 1)
        start = first - timedelta(days=first.weekday())
        today = date.today()
        marks = self.marks or ()
        for i, cell in enumerate(self._cells):
            d = start + timedelta(days=i)
            cell.day = d
            cell.label = str(d.day)
            cell.other = d.month != self.month
            cell.today = d == today
            cell.selected = d == self.selected
            cell.marked = d.isoformat() in marks
        self.ids.title.text = "%s %d" % (MONTHS[int(self.month) - 1].capitalize(), self.year)

