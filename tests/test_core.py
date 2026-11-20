import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import dates
from core.store import Store, display_title, note_is_empty, preview_text


class DatesTest(unittest.TestCase):
    def test_parse_hhmm(self):
        self.assertEqual(dates.parse_hhmm("08:30"), 510)
        self.assertEqual(dates.parse_hhmm("830"), 510)
        self.assertEqual(dates.parse_hhmm("8.30"), 510)
        self.assertEqual(dates.parse_hhmm("0830"), 510)
        self.assertIsNone(dates.parse_hhmm("24:00"))
        self.assertIsNone(dates.parse_hhmm("8:5"))
        self.assertIsNone(dates.parse_hhmm(""))
        self.assertIsNone(dates.parse_hhmm("абв"))

    def test_fmt(self):
        self.assertEqual(dates.fmt_hhmm(510), "08:30")
        self.assertEqual(dates.fmt_hhmm(99999), "23:59")

    def test_plural(self):
        self.assertEqual(dates.plural(1, "урок", "урока", "уроков"), "урок")
        self.assertEqual(dates.plural(3, "урок", "урока", "уроков"), "урока")
        self.assertEqual(dates.plural(11, "урок", "урока", "уроков"), "уроков")
        self.assertEqual(dates.plural(21, "урок", "урока", "уроков"), "урок")

    def test_labels(self):
        self.assertEqual(dates.day_label(date(2026, 11, 19)), "19 ноября, чт")
        self.assertEqual(dates.short_date(date(2026, 11, 19), date(2026, 1, 1)), "19 ноя")
        self.assertEqual(dates.short_date(date(2025, 11, 19), date(2026, 1, 1)), "19 ноя 2025")


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "data.json")
        self.store = Store(self.path)

    def tearDown(self):
        self.dir.cleanup()

    def test_roundtrip(self):
        note = self.store.new_note("text", folder=1, date="2026-11-19")
        note["title"] = "Привет"
        note["body"] = "Текст заметки"
        self.store.upsert_note(note)
        again = Store(self.path)
        self.assertEqual(len(again.notes), 1)
        self.assertEqual(again.notes[0]["title"], "Привет")
        self.assertEqual(again.notes[0]["folder"], 1)

    def test_empty_detection(self):
        note = self.store.new_note("text")
        self.assertTrue(note_is_empty(note))
        note["body"] = "  x "
        self.assertFalse(note_is_empty(note))
        lst = self.store.new_note("list")
        self.assertTrue(note_is_empty(lst))
        lst["items"][0]["t"] = "молоко"
        self.assertFalse(note_is_empty(lst))

    def test_titles_and_preview(self):
        note = self.store.new_note("text")
        note["body"] = "Первая строка\nвторая\nтретья"
        self.assertEqual(display_title(note), "Первая строка")
        self.assertEqual(preview_text(note), "вторая третья")
        note["title"] = "Заголовок"
        self.assertEqual(preview_text(note), "Первая строка вторая третья")

    def test_query_and_sort(self):
        a = self.store.new_note("text", folder=0)
        a.update(title="Бета", updated=100, created=1)
        b = self.store.new_note("text", folder=1)
        b.update(title="Альфа", updated=200, created=2, pinned=True)
        c = self.store.new_note("text", folder=1)
        c.update(title="Гамма", updated=300, created=3, date="2026-11-20")
        for n in (a, b, c):
            self.store.upsert_note(n)
        titles = lambda **kw: [n["title"] for n in self.store.query_notes(**kw)]
        self.assertEqual(titles(sort="updated_desc"), ["Альфа", "Гамма", "Бета"])
        self.assertEqual(titles(sort="name_asc"), ["Альфа", "Бета", "Гамма"])
        self.assertEqual(titles(folder=1, sort="name_desc"), ["Альфа", "Гамма"])
        self.assertEqual(titles(text="гам"), ["Гамма"])
        self.assertEqual(titles(sort="remind")[0], "Альфа")
        self.assertEqual(self.store.marked_dates(), {"2026-11-20"})
        self.assertEqual(len(self.store.notes_for_date("2026-11-20")), 1)

    def test_lessons(self):
        for start, end, name in (("10:00", "10:45", "Б"), ("08:30", "09:15", "А")):
            lesson = self.store.new_lesson(0)
            lesson.update(start=start, end=end, subject=name)
            self.store.upsert_lesson(lesson)
        self.assertEqual([x["subject"] for x in self.store.lessons_for_day(0)], ["А", "Б"])
        self.assertEqual(self.store.lessons_for_day(1), [])
        self.store.delete_lesson(self.store.lessons_for_day(0)[0]["id"])
        self.assertEqual(len(self.store.lessons), 1)

    def test_backup(self):
        note = self.store.new_note("text")
        note["body"] = "данные"
        self.store.upsert_note(note)
        dump = self.store.export_json()
        self.store.clear()
        self.assertEqual(self.store.notes, [])
        self.assertTrue(self.store.import_json(dump))
        self.assertEqual(self.store.notes[0]["body"], "данные")
        self.assertFalse(self.store.import_json("not json"))
        self.assertFalse(self.store.import_json("[1, 2]"))

    def test_corrupt_file_falls_back(self):
        note = self.store.new_note("text")
        note["body"] = "x"
        self.store.upsert_note(note)
        self.store.upsert_note(dict(note, body="y"))
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{broken")
        self.assertEqual(len(Store(self.path).notes), 1)

    def test_listeners(self):
        calls = []
        self.store.subscribe(lambda: calls.append(1))
        self.store.upsert_note(self.store.new_note("text"))
        self.assertEqual(calls, [1])


if __name__ == "__main__":
    unittest.main()
