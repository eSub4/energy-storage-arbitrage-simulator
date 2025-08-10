# utils/localization.py

"""
Hilfsfunktionen für die deutsche Lokalisierung.
"""
import locale
from datetime import datetime

# Deutsche Wochentage
DE_WEEKDAYS = {
    "Monday": "Montag",
    "Tuesday": "Dienstag",
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag",
}

# Deutsche Monate
DE_MONTHS = {
    "January": "Januar",
    "February": "Februar",
    "March": "März",
    "April": "April",
    "May": "Mai",
    "June": "Juni",
    "July": "Juli",
    "August": "August",
    "September": "September",
    "October": "Oktober",
    "November": "November",
    "December": "Dezember",
}

# Abgekürzte deutsche Monate für Diagramme
DE_MONTHS_SHORT = {
    "Jan": "Jan",
    "Feb": "Feb",
    "Mar": "Mär",
    "Apr": "Apr",
    "May": "Mai",
    "Jun": "Jun",
    "Jul": "Jul",
    "Aug": "Aug",
    "Sep": "Sep",
    "Oct": "Okt",
    "Nov": "Nov",
    "Dec": "Dez",
}


def setup_german_locale():
    """Versucht, die deutsche Lokalisierung zu setzen"""
    try:
        locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
        return True
    except:
        try:
            locale.setlocale(locale.LC_TIME, "German")
            return True
        except:
            return False


def format_date_german(date, format_str="%d.%m.%Y"):
    """Formatiert ein Datum auf Deutsch"""
    return date.strftime(format_str)


def get_german_weekday(date):
    """Gibt den deutschen Wochentag zurück"""
    english_weekday = date.strftime("%A")
    return DE_WEEKDAYS.get(english_weekday, english_weekday)


def get_german_month(date):
    """Gibt den deutschen Monatsnamen zurück"""
    english_month = date.strftime("%B")
    return DE_MONTHS.get(english_month, english_month)


def get_german_month_short(date):
    """Gibt den abgekürzten deutschen Monatsnamen zurück (für Diagramme)"""
    english_month = date.strftime("%b")
    return DE_MONTHS_SHORT.get(english_month, english_month)


def format_datetime_german(datetime_obj, include_time=False):
    """
    Formatiert ein Datetime-Objekt auf Deutsch.

    Args:
        datetime_obj: Das zu formatierende Datetime-Objekt
        include_time: Ob die Zeit auch formatiert werden soll

    Returns:
        Formatierter String im Format "DD. Monatsname YYYY [HH:MM]"
    """
    if include_time:
        return f"{datetime_obj.day}. {get_german_month(datetime_obj)} {datetime_obj.year} {datetime_obj.hour:02d}:{datetime_obj.minute:02d}"
    else:
        return (
            f"{datetime_obj.day}. {get_german_month(datetime_obj)} {datetime_obj.year}"
        )
