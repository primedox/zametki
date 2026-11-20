from datetime import date, datetime

MONTHS = ["январь", "февраль", "март", "апрель", "май", "июнь",
          "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
MONTHS_SHORT = ["янв", "фев", "мар", "апр", "мая", "июн",
                "июл", "авг", "сен", "окт", "ноя", "дек"]
WD_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WD_FULL = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


def parse_iso(text):
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def day_label(d):
    return "%d %s, %s" % (d.day, MONTHS_GEN[d.month - 1], WD_SHORT[d.weekday()].lower())


def short_date(d, today=None):
    today = today or date.today()
    base = "%d %s" % (d.day, MONTHS_SHORT[d.month - 1])
    return base if d.year == today.year else "%s %d" % (base, d.year)


def stamp(ts, now=None):
    moment = datetime.fromtimestamp(ts)
    now = now or datetime.now()
    if moment.date() == now.date():
        return moment.strftime("%H:%M")
    return short_date(moment.date(), now.date())


def full_stamp(ts):
    moment = datetime.fromtimestamp(ts)
    return "%s, %s" % (short_date(moment.date()), moment.strftime("%H:%M"))


def parse_hhmm(text):
    raw = (text or "").strip().replace(".", ":").replace(" ", "")
    if ":" in raw:
        hours, _, minutes = raw.partition(":")
    elif raw.isdigit() and len(raw) in (3, 4):
        hours, minutes = raw[:-2], raw[-2:]
    else:
        return None
    if not (hours.isdigit() and minutes.isdigit()) or len(minutes) != 2:
        return None
    h, m = int(hours), int(minutes)
    if h > 23 or m > 59:
        return None
    return h * 60 + m


def fmt_hhmm(minutes):
    minutes = max(0, min(int(minutes), 24 * 60 - 1))
    return "%02d:%02d" % divmod(minutes, 60)


def plural(n, one, few, many):
    n = abs(int(n))
    if n % 100 in (11, 12, 13, 14):
        return many
    if n % 10 == 1:
        return one
    if n % 10 in (2, 3, 4):
        return few
    return many
