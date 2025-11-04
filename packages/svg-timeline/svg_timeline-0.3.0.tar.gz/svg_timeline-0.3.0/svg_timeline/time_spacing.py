""" classes to create evenly spaced datetime objects within a range """
import calendar
from calendar import weekday
from collections.abc import Iterable
from datetime import datetime

from svg_timeline.notation import dt


class TimeSpacing:
    """ base class for semantic datetime spacing within a given range """
    def __init__(
            self,
            start_date: datetime | str,
            end_date: datetime | str,
    ):
        self._start_date = start_date if isinstance(start_date, datetime) else dt(start_date)
        self._end_date = end_date if isinstance(end_date, datetime) else dt(end_date)
        if not self._start_date < self._end_date:
            raise ValueError("start date needs to be smaller than end date")

    @property
    def start_date(self) -> datetime:
        """ the datetime that corresponds to the start of the time range """
        return self._start_date

    @property
    def end_date(self) -> datetime:
        """ the datetime that corresponds to the end of the time range """
        return self._end_date

    @property
    def labels(self) -> list[str]:
        """ Tic labels
        :return list of tic labels as strings
        """
        raise NotImplementedError

    @property
    def dates(self) -> list[datetime]:
        """ Positions of the tics
        :return list of tic positions as datetime objects
        """
        raise NotImplementedError


def _normalize_month(year: int, month: int = 1) -> tuple[int, int, int]:
    """ Helper function to normalize a date after the months have been manually counted up or down
    Note: Does NOT correct the day
    :returns (normalized year, normalized month, n_days in month)
    """
    year += (month - 1) // 12
    month = ((month - 1) % 12) + 1
    _, n_days = calendar.monthrange(year, month)
    return year, month, n_days


def _normalize_date(year: int, month: int = 1, day: int = 1) -> tuple[int, int, int]:
    """ Helper function to normalize a date
    after the days or months have been manually counted up or down
    :returns (normalized year, normalized month, normalized day)
    """
    year, month, n_days = _normalize_month(year=year, month=month)
    while day > n_days:
        month += 1
        day -= n_days
        year, month, n_days = _normalize_month(year=year, month=month)
    while day < 1:
        month -= 1
        year, month, n_days = _normalize_month(year=year, month=month)
        day += n_days
    return year, month, day


def _normalize_time(hour: int = 0, minute: int = 0, second: int = 0) -> tuple[int, int, int, int]:
    """ Helper function to normalize a time
    after the hours, minutes or seconds have been manually counted up or down
    Note: might lead to a day overflow that this function does not handle
    :returns (day overflow, normalized hour, normalized minute, normalized second)
    """
    # normalize seconds
    minute += second // 60
    second = second % 60
    # normalize minutes
    hour += minute // 60
    minute = minute % 60
    # normalize hours
    day_overflow = hour // 24
    hour = hour % 24
    return day_overflow, hour, minute, second


class YearBasedTimeSpacing(TimeSpacing):
    """ base class to return one entry per X years """
    _base = 1

    @property
    def _range(self) -> Iterable:
        first = (self._start_date.year // self._base + 1) * self._base
        last = (self._end_date.year // self._base) * self._base
        return range(first, last + self._base, self._base)

    @property
    def dates(self) -> list[datetime]:
        dates = [datetime(year=year, month=1, day=1)
                 for year in self._range]
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [str(value) for value in self._range]
        return labels


class TimeSpacingPerMillennia(YearBasedTimeSpacing):
    """ return one entry per 1000 years
    Note: ISO 8601 only allows years between 0000 and 9999
    """
    _base = 1000


class TimeSpacingPerCentury(YearBasedTimeSpacing):
    """ return one entry per 100 years """
    _base = 100


class TimeSpacingPerDecade(YearBasedTimeSpacing):
    """ return one entry per 10 years """
    _base = 10


class TimeSpacingPerYear(YearBasedTimeSpacing):
    """ return one entry per year """
    _base = 1


class TimeSpacingPerMonth(TimeSpacing):
    """ return one entry per month """
    @property
    def dates(self) -> list[datetime]:
        year, month, _ = _normalize_month(year=self.start_date.year,
                                          month=self.start_date.month + 1)
        date = datetime(year=year, month=month, day=1)
        dates = []
        while date <= self.end_date:
            dates.append(date)
            year, month, _ = _normalize_month(year=year, month=month + 1)
            date = datetime(year=year, month=month, day=1)
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [calendar.month_abbr[date.month] for date in self.dates]
        return labels


class TimeSpacingPerWeek(TimeSpacing):
    """ return one entry per week """
    @property
    def dates(self) -> list[datetime]:
        year, month, day = self.start_date.year, self.start_date.month, self.start_date.day
        year, month, day = _normalize_date(year=year, month=month, day=day + 1)
        while weekday(year, month, day) != 0:
            year, month, day = _normalize_date(year=year, month=month, day=day + 1)
        dates = []
        date = datetime(year=year, month=month, day=day)
        while date <= self.end_date:
            dates.append(date)
            year, month, day = _normalize_date(year=year, month=month, day=day + 7)
            date = datetime(year=year, month=month, day=day)
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [f"{date.isocalendar().week:02}" for date in self.dates]
        return labels


class TimeSpacingPerDay(TimeSpacing):
    """ return one entry per day """
    @property
    def dates(self) -> list[datetime]:
        date_tuple = _normalize_date(year=self.start_date.year,
                                     month=self.start_date.month,
                                     day=self.start_date.day + 1)
        date = datetime(*date_tuple)
        dates = []
        while date <= self.end_date:
            dates.append(date)
            date_tuple = _normalize_date(year=date.year, month=date.month, day=date.day + 1)
            date = datetime(*date_tuple)
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [str(date.day) for date in self.dates]
        return labels


class TimeSpacingPerHour(TimeSpacing):
    """ return one entry per hour """
    @property
    def dates(self) -> list[datetime]:
        day_overflow, hour, _, _ = _normalize_time(hour=self.start_date.hour + 1)
        date_tuple = _normalize_date(year=self.start_date.year,
                                     month=self.start_date.month,
                                     day=self.start_date.day + day_overflow)
        date = datetime(*date_tuple, hour=hour)
        dates = []
        while date <= self.end_date:
            dates.append(date)
            day_overflow, hour, _, _ = _normalize_time(hour=date.hour + 1)
            date_tuple = _normalize_date(year=date.year,
                                         month=date.month,
                                         day=date.day + day_overflow)
            date = datetime(*date_tuple, hour=hour)
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [f"{date.hour:02}:00" for date in self.dates]
        return labels


class TimeSpacingPerMinute(TimeSpacing):
    """ return one entry per minute """
    @property
    def dates(self) -> list[datetime]:
        day_overflow, hour, minute, _ = _normalize_time(hour=self.start_date.hour,
                                                        minute=self.start_date.minute + 1)
        date_tuple = _normalize_date(year=self.start_date.year,
                                     month=self.start_date.month,
                                     day=self.start_date.day + day_overflow)
        date = datetime(*date_tuple, hour=hour, minute=minute)
        dates = []
        while date <= self.end_date:
            dates.append(date)
            day_overflow, hour, minute, _ = _normalize_time(hour=date.hour, minute=date.minute + 1)
            date_tuple = _normalize_date(year=date.year,
                                         month=date.month,
                                         day=date.day + day_overflow)
            date = datetime(*date_tuple, hour=hour, minute=minute)
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [f"{date.hour:02}:{date.minute:02}" for date in self.dates]
        return labels


class TimeSpacingPerSecond(TimeSpacing):
    """ return one entry per second """
    @property
    def dates(self) -> list[datetime]:
        day_overflow, hour, minute, second = _normalize_time(hour=self.start_date.hour,
                                                             minute=self.start_date.minute,
                                                             second=self.start_date.second + 1)
        date_tuple = _normalize_date(year=self.start_date.year,
                                     month=self.start_date.month,
                                     day=self.start_date.day + day_overflow)
        date = datetime(*date_tuple, hour=hour, minute=minute, second=second)
        dates = []
        while date <= self.end_date:
            dates.append(date)
            day_overflow, hour, minute, second = _normalize_time(hour=date.hour,
                                                                 minute=date.minute,
                                                                 second=date.second + 1)
            date_tuple = _normalize_date(year=date.year,
                                         month=date.month,
                                         day=date.day + day_overflow)
            date = datetime(*date_tuple, hour=hour, minute=minute, second=second)
        return dates

    @property
    def labels(self) -> list[str]:
        labels = [f"{date.hour:02}:{date.minute:02}:{date.second:02}" for date in self.dates]
        return labels
