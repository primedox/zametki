import json
import os
import shutil
import time
import uuid

from .dates import parse_hhmm

SCHEMA = 1

SORT_KEYS = (
    "folder", "name_asc", "name_desc", "remind",
    "updated_desc", "updated_asc", "created_desc", "created_asc",
)


def _now():
    return int(time.time())


def _uid():
    return uuid.uuid4().hex[:12]


def display_title(note):
    title = (note.get("title") or "").strip()
    if title:
        return title
    if note.get("kind") == "list":
        for item in note.get("items", []):
            if item.get("t", "").strip():
                return item["t"].strip()
    else:
        for line in (note.get("body") or "").splitlines():
            if line.strip():
                return line.strip()
    return "Без названия"


def note_is_empty(note):
    if (note.get("title") or "").strip():
        return False
    if note.get("kind") == "list":
        return not any(i.get("t", "").strip() for i in note.get("items", []))
    return not (note.get("body") or "").strip()


def preview_text(note):
    if note.get("kind") == "list":
        items = [i for i in note.get("items", []) if i.get("t", "").strip()]
        if not items:
            return ""
        done = sum(1 for i in items if i.get("d"))
        head = "  ·  ".join(i["t"].strip() for i in items[:3])
        return "%d/%d  %s" % (done, len(items), head)
    lines = [ln.strip() for ln in (note.get("body") or "").splitlines() if ln.strip()]
    if (note.get("title") or "").strip():
        return " ".join(lines[:3])
    return " ".join(lines[1:4])


def note_as_text(note):
    parts = [(note.get("title") or "").strip()]
    if note.get("kind") == "list":
        parts += [("[x] " if i.get("d") else "[ ] ") + i.get("t", "")
                  for i in note.get("items", []) if i.get("t", "").strip()]
    else:
        parts.append((note.get("body") or "").strip())
    return "\n".join(part for part in parts if part)


def _clean_note(raw):
    if not isinstance(raw, dict):
        return None
    kind = "list" if raw.get("kind") == "list" else "text"
    items = []
    for it in raw.get("items") or []:
        if isinstance(it, dict):
            items.append({"t": str(it.get("t", "")), "d": bool(it.get("d"))})
    ts = _now()
    return {
        "id": str(raw.get("id") or _uid()),
        "kind": kind,
        "title": str(raw.get("title") or ""),
        "body": str(raw.get("body") or ""),
        "items": items,
        "folder": int(raw.get("folder", 0)) if str(raw.get("folder", 0)).lstrip("-").isdigit() else 0,
        "color": int(raw.get("color", 0)) if str(raw.get("color", 0)).isdigit() else 0,
        "pinned": bool(raw.get("pinned")),
        "font": int(raw.get("font", 0)) if str(raw.get("font", 0)).isdigit() else 0,
        "date": str(raw.get("date") or ""),
        "created": int(raw.get("created") or ts),
        "updated": int(raw.get("updated") or ts),
    }


def _clean_lesson(raw):
    if not isinstance(raw, dict):
        return None
    start = parse_hhmm(raw.get("start"))
    end = parse_hhmm(raw.get("end"))
    try:
        day = int(raw.get("day"))
    except (TypeError, ValueError):
        return None
    if start is None or end is None or not 0 <= day <= 5:
        return None
    return {
        "id": str(raw.get("id") or _uid()),
        "day": day,
        "start": "%02d:%02d" % divmod(start, 60),
        "end": "%02d:%02d" % divmod(end, 60),
        "subject": str(raw.get("subject") or "").strip(),
        "room": str(raw.get("room") or "").strip(),
        "teacher": str(raw.get("teacher") or "").strip(),
        "color": int(raw.get("color", 0)) if str(raw.get("color", 0)).isdigit() else 0,
    }


class Store:
    def __init__(self, path):
        self.path = path
        self.notes = []
        self.lessons = []
        self.prefs = {"theme": "light", "sort": "updated_desc"}
        self._listeners = []
        self.load()

    def subscribe(self, callback):
        self._listeners.append(callback)

    def _emit(self):
        for callback in list(self._listeners):
            callback()

    def _read(self, path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)

    def load(self):
        raw = None
        for candidate in (self.path, self.path + ".bak"):
            try:
                raw = self._read(candidate)
                break
            except (OSError, ValueError):
                continue
        if isinstance(raw, dict):
            self._apply(raw)

    def _apply(self, raw):
        notes = [_clean_note(n) for n in raw.get("notes", [])]
        lessons = [_clean_lesson(x) for x in raw.get("lessons", [])]
        self.notes = [n for n in notes if n]
        self.lessons = [x for x in lessons if x]
        prefs = raw.get("prefs")
        if isinstance(prefs, dict):
            if prefs.get("theme") in ("light", "dark"):
                self.prefs["theme"] = prefs["theme"]
            if prefs.get("sort") in SORT_KEYS:
                self.prefs["sort"] = prefs["sort"]

    def _payload(self):
        return {"schema": SCHEMA, "notes": self.notes, "lessons": self.lessons, "prefs": self.prefs}

    def save(self):
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self._payload(), handle, ensure_ascii=False)
        if os.path.exists(self.path):
            shutil.copyfile(self.path, self.path + ".bak")
        os.replace(tmp, self.path)

    def set_pref(self, key, value):
        self.prefs[key] = value
        self.save()

    def new_note(self, kind="text", folder=0, date=""):
        ts = _now()
        return {
            "id": _uid(), "kind": kind, "title": "", "body": "",
            "items": [{"t": "", "d": False}] if kind == "list" else [],
            "folder": folder, "color": 0, "pinned": False, "font": 0,
            "date": date, "created": ts, "updated": ts,
        }

    def get_note(self, note_id):
        for note in self.notes:
            if note["id"] == note_id:
                return note
        return None

    def upsert_note(self, note):
        for i, existing in enumerate(self.notes):
            if existing["id"] == note["id"]:
                self.notes[i] = note
                break
        else:
            self.notes.append(note)
        self.save()
        self._emit()

    def delete_note(self, note_id):
        self.notes = [n for n in self.notes if n["id"] != note_id]
        self.save()
        self._emit()

    def toggle_pin(self, note_id):
        note = self.get_note(note_id)
        if note:
            note["pinned"] = not note["pinned"]
            self.save()
            self._emit()

    def query_notes(self, folder=None, text="", sort="updated_desc"):
        needle = text.strip().casefold()
        result = []
        for note in self.notes:
            if folder is not None and note["folder"] != folder:
                continue
            if needle:
                haystack = " ".join([
                    note["title"], note["body"],
                    " ".join(i["t"] for i in note["items"]),
                ]).casefold()
                if needle not in haystack:
                    continue
            result.append(note)

        def name(n):
            return display_title(n).casefold()

        if sort == "folder":
            result.sort(key=lambda n: (n["folder"], -n["updated"]))
        elif sort == "name_asc":
            result.sort(key=name)
        elif sort == "name_desc":
            result.sort(key=name, reverse=True)
        elif sort == "remind":
            result.sort(key=lambda n: (n["date"] == "", n["date"], -n["updated"]))
        elif sort == "updated_asc":
            result.sort(key=lambda n: n["updated"])
        elif sort == "created_desc":
            result.sort(key=lambda n: -n["created"])
        elif sort == "created_asc":
            result.sort(key=lambda n: n["created"])
        else:
            result.sort(key=lambda n: -n["updated"])
        result.sort(key=lambda n: not n["pinned"])
        return result

    def notes_for_date(self, iso):
        return sorted((n for n in self.notes if n["date"] == iso), key=lambda n: -n["updated"])

    def marked_dates(self):
        return {n["date"] for n in self.notes if n["date"]}

    def lessons_for_day(self, day):
        items = [x for x in self.lessons if x["day"] == day]
        items.sort(key=lambda x: parse_hhmm(x["start"]))
        return items

    def get_lesson(self, lesson_id):
        for lesson in self.lessons:
            if lesson["id"] == lesson_id:
                return lesson
        return None

    def upsert_lesson(self, lesson):
        for i, existing in enumerate(self.lessons):
            if existing["id"] == lesson["id"]:
                self.lessons[i] = lesson
                break
        else:
            self.lessons.append(lesson)
        self.save()
        self._emit()

    def delete_lesson(self, lesson_id):
        self.lessons = [x for x in self.lessons if x["id"] != lesson_id]
        self.save()
        self._emit()

    def new_lesson(self, day):
        return {"id": _uid(), "day": day, "start": "", "end": "",
                "subject": "", "room": "", "teacher": "", "color": 0}

    def export_json(self):
        return json.dumps(self._payload(), ensure_ascii=False)

    def import_json(self, text):
        try:
            raw = json.loads(text)
        except (TypeError, ValueError):
            return False
        if not isinstance(raw, dict) or ("notes" not in raw and "lessons" not in raw):
            return False
        self._apply(raw)
        self.save()
        self._emit()
        return True

    def clear(self):
        self.notes = []
        self.lessons = []
        self.save()
        self._emit()
