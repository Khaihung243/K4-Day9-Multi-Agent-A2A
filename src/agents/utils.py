from datetime import datetime

def parse_datetime(dt_str):
    if not dt_str or not isinstance(dt_str, str) or dt_str.strip() == "":
        return None
    try:
        return datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def calc_hours_diff(dt1, dt2):
    if not dt1 or not dt2:
        return None
    seconds = (dt1 - dt2).total_seconds()
    return round(seconds / 3600.0, 2)
