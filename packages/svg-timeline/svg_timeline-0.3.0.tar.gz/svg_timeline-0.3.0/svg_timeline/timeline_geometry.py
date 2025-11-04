""" classes that define the geometry of the timeline plot """
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from svg_timeline.vectors import Vector
from svg_timeline.notation import dt


@dataclass
class GeometrySettings:
    """ geometry settings related to the canvas """
    canvas_height: int = 800
    canvas_width: int = 1000
    canvas_x_padding: float = 0.03
    lane_zero_rel_y_position: float = 0.9
    lane_height: float = 30


class TimeLineGeometry:
    """ class for the transfer of dates and lanes to canvas coordinates """
    def __init__(
            self,
            start_date: datetime | str,
            end_date: datetime | str,
            settings: Optional[GeometrySettings] = None,
    ):
        """
        :param start_date: the lower boundary of the timeline
        :param end_date: the upper boundary of the timeline
        """
        self._settings = settings or GeometrySettings()
        self._first = start_date if isinstance(start_date, datetime) else dt(start_date)
        self._last = end_date if isinstance(end_date, datetime) else dt(end_date)
        y = self._settings.lane_zero_rel_y_position * self._settings.canvas_height
        x1 = self._settings.canvas_x_padding * self._settings.canvas_width
        x2 = (1 - self._settings.canvas_x_padding) * self._settings.canvas_width
        self._gradient = TimeGradient(source=Vector(x1, y), target=Vector(x2, y),
                                      start_date=start_date, end_date=end_date)

    @property
    def settings(self) -> GeometrySettings:
        """ styling information for the timeline """
        return self._settings

    @property
    def first(self) -> datetime:
        """ first date of the timeline """
        return self._first

    @property
    def last(self) -> datetime:
        """ last date of the timeline """
        return self._last

    @property
    def width(self) -> int:
        """ full width of the canvas """
        return self._settings.canvas_width

    @property
    def height(self) -> int:
        """ full height of the canvas """
        return self._settings.canvas_height

    @property
    def lane_normal(self) -> Vector:
        """ Normal vector orthogonal to the timeline direction
        This vector is used to calculate the positions of the different lanes.
        """
        return (self._gradient.target - self._gradient.source).orthogonal(ccw=True)

    def as_coord(self, date: datetime | str, lane: float = 0) -> Vector:
        """ return the coordinates responding to this date on a given lane
        (default: on the time arrow)
        """
        date_coord = self._gradient.date_to_coord(date)
        lane_point = date_coord + lane * self._settings.lane_height * self.lane_normal
        return lane_point


class TimeGradient:
    """ class for the transfer of dates to canvas coordinates and back """
    def __init__(
            self,
            source: Vector,
            target: Vector,
            start_date: datetime | str,
            end_date: datetime | str,
    ):
        """
        :param source: the point on the canvas that correspond to the start of the gradient
        :param target: the point on the canvas that correspond to the end of the gradient
        :param start_date: the datetime that corresponds to the start of the canvas_vector
        :param end_date: the datetime that corresponds to the end of the canvas_vector
        """
        self._source = source
        self._target = target
        self._start_date = start_date if isinstance(start_date, datetime) else dt(start_date)
        self._end_date = end_date if isinstance(end_date, datetime) else dt(end_date)

    @property
    def source(self) -> Vector:
        """ the point on the canvas that correspond to the start of the gradient """
        return self._source

    @property
    def target(self) -> Vector:
        """ the point on the canvas that correspond to the end of the gradient """
        return self._target

    @property
    def start_date(self) -> datetime:
        """ the datetime that corresponds to the start of the canvas_vector """
        return self._start_date

    @property
    def end_date(self) -> datetime:
        """ the datetime that corresponds to the end of the canvas_vector """
        return self._end_date

    def coord_to_date(self, coord: Vector) -> datetime:
        """ transform an absolute position on the canvas into a date """
        return self.relative_to_date(self.coord_to_relative(coord=coord))

    def coord_to_relative(self, coord: Vector) -> float:
        """ transform an absolute position on the canvas
        into a relative position on the timeline
        """
        # Transform coordinates so that the timeline start is at (0, 0).
        # (simplifies the following calculations)
        coord_x = coord.x - self._source.x
        coord_y = coord.y - self._source.y
        end_x = self._target.x - self._source.x
        end_y = self._target.y - self._source.y
        # Given a scalar factor 'a', minimize the length of vector 'coord - a * end'.
        # 'a' then describes the relative position on this timeline with the
        # shortest distance to the given coordinates.
        # Solved analytically, this gives:
        numerator = coord_x * end_x + coord_y * end_y
        denominator = end_x**2 + end_y**2
        a = numerator / denominator
        return a

    def date_to_coord(self, date: datetime | str) -> Vector:
        """ transform a date into a position on the canvas """
        return self.relative_to_coord(self.date_to_relative(date=date))

    def date_to_relative(self, date: datetime | str) -> float:
        """ transform a date into a relative position on the timeline """
        if isinstance(date, str):
            date = dt(date)
        self_delta = self._end_date - self._start_date
        date_delta = date - self.start_date
        return date_delta / self_delta

    def relative_to_coord(self, relative_position: float) -> Vector:
        """ transform a relative position on the timeline
        into an absolute position on the canvas
        """
        delta = self._target - self._source
        scaled_vector = self._source + (relative_position * delta)
        return scaled_vector

    def relative_to_date(self, relative_position: float) -> datetime:
        """ transform a relative position on the timeline into a date """
        delta = self._end_date - self._start_date
        return self._start_date + relative_position * delta
