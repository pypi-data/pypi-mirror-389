""" helper module to simplify notation in scripts """
import re
from datetime import datetime


def dt(datetime_shorthand: str) -> datetime:
    """ factory function for datetime objects that can interpret various shorthand notations """
    if re.match(r'^\d\d\d\d$', datetime_shorthand):
        # just the year
        return datetime.fromisoformat(f'{datetime_shorthand}-01-01')
    if re.match(r'^\d\d\d\d-\d\d$', datetime_shorthand):
        # year and month
        return datetime.fromisoformat(f'{datetime_shorthand}-01')
    if re.match(r'^\d\d\d\d-\d\d-\d\d$', datetime_shorthand):
        # iso date
        return datetime.fromisoformat(datetime_shorthand)
    if re.match(r'^\d\d\d\d-\d\d-\d\dT\d\d$', datetime_shorthand):
        # iso date + hour
        return datetime.fromisoformat(f'{datetime_shorthand}:00:00')
    if re.match(r'^\d\d\d\d-\d\d-\d\dT\d\d:\d\d$', datetime_shorthand):
        # iso date + hour:minute
        return datetime.fromisoformat(f'{datetime_shorthand}:00')
    if re.match(r'^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d$', datetime_shorthand):
        # iso date + time
        return datetime.fromisoformat(datetime_shorthand)
    # default to today
    year = datetime.today().year
    month = datetime.today().month
    day = datetime.today().day
    if re.match(r'^\d\d:\d\d$', datetime_shorthand):
        # hour and minutes
        hour, minutes = [int(part) for part in datetime_shorthand.split(':')]
        return datetime(year, month, day, hour, minutes)
    if re.match(r'^\d\d:\d\d:\d\d$', datetime_shorthand):
        # hour, minutes and seconds
        hour, minutes, seconds = [int(part) for part in datetime_shorthand.split(':')]
        return datetime(year, month, day, hour, minutes, seconds)
    raise ValueError(f"No known shorthand pattern matches '{datetime_shorthand}'")
