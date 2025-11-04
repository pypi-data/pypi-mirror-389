""" basic geometry classes to describe canvas points """
import math

# tolerance on coordinates within which two points are considered equal
COORD_TOLERANCE = 0.000_001


class Vector:
    """ a vector (or point) within a canvas """
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def __eq__(self, other) -> bool:
        """ two points are equal, if their coordinates are equal within COORD_TOLERANCE """
        if not isinstance(other, Vector):
            raise TypeError("Can only compare with another CanvasPoint instance")
        return (math.fabs(self.x - other.x) < COORD_TOLERANCE and
                math.fabs(self.y - other.y) < COORD_TOLERANCE)

    def __add__(self, other) -> 'Vector':
        """ component-wise addition with another vector """
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other) -> 'Vector':
        """ component-wise subtraction with another vector """
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other) -> 'Vector':
        """ scalar multiplication with an integer or float value """
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Vector(other * self.x, other * self.y)

    def __rmul__(self, other) -> 'Vector':
        """ (see __mul__)"""
        return self.__mul__(other=other)

    def __truediv__(self, other) -> 'Vector':
        """ (see __mul__)"""
        factor = 1/other
        return self.__mul__(other=factor)

    def __rtruediv__(self, other) -> 'Vector':
        """ dividing a value by a vector is not possible """
        return NotImplemented

    @property
    def mag(self) -> float:
        """ the vector magnitude (length) according to the euclidian norm """
        norm = math.sqrt(self.x**2 + self.y**2)
        return norm

    def normalized(self) -> 'Vector':
        """ return a normalized version of the vector
        the initial_point will be the origin (0, 0) and the magnitude will be 1
        :raises ZeroDivisionError if the vector has magnitude zero
        """
        if self.mag == 0:
            raise ZeroDivisionError("Can not normalize a vector of magnitude 0")
        return self / self.mag

    def orthogonal(self, ccw: bool = False) -> 'Vector':
        """ return a normalized vector that points in the (counter)clockwise
        orthogonal direction from this vector
        :argument ccw if True rotate counterclockwise, otherwise clockwise
        :raises ZeroDivisionError if the vector has magnitude zero
        """
        if self.mag == 0:
            raise ZeroDivisionError("Can not normalize a vector of magnitude 0")
        norm = self.normalized()
        if ccw:
            return Vector(norm.y, -norm.x)
        return Vector(-norm.y, norm.x)
