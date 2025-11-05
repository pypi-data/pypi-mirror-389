"""bnum -- bounded numbers"""

from __future__ import annotations

import math

try:
    from . import _version

    __version__ = _version.VERSION
except (ImportError, AttributeError):  # pragma: no cover
    import importlib.metadata

    try:
        __version__ = importlib.metadata.version(__name__)
    except importlib.metadata.PackageNotFoundError:
        __version__ = '0.0.0'


class InvalidRangeError(ValueError):
    """Raised when a number is out of range for a bnum."""


def _bind(unbounded_number: float) -> float:
    """Transform an unbounded number into an bounded number."""
    if unbounded_number > 0.0:
        result = 1.0 - (1.0 / (1.0 + unbounded_number))
        # Ensure result is strictly less than 1.0 to maintain invariant
        if result >= 1.0:
            return math.nextafter(1.0, 0.0)
        return result
    result = (1.0 / (1.0 - unbounded_number)) - 1.0
    # Ensure result is strictly greater than -1.0 to maintain invariant
    if result <= -1.0:
        return math.nextafter(-1.0, 0.0)
    return result


def _unbind(bounded_number: float) -> float:
    """Transform a bounded number into an unbounded number."""
    if bounded_number > 0.0:
        return (1.0 / (1.0 - bounded_number)) - 1.0
    return 1.0 - (1.0 / (1.0 + bounded_number))


def bind(x: float) -> bnum:
    """Bind an unbounded number to a bnum value between -1 and 1.

    Note that in the world of bounded numbers, from ten on up, the
    number of places beyond 1 *roughly* corresponds to the number of
    nines.  That is:
        10 ~= 0.9
       100 ~= 0.99
      1000 ~= 0.999
       ...

    Note also that the journey from unbounded to bounded will result
    in rounding errors.  The larger the unbounded number, the larger
    the round-trip deviation.
    """
    return bnum(_bind(float(x)))


def unbounded(x: floatish) -> float:
    """Return an unbounded number."""
    if isinstance(x, bnum):
        return x.unbounded
    return x


def blend(
    x: floatish,
    y: floatish,
    weight: floatish = 0.0,
) -> bnum:
    """Combine two bounded numbers with an optional weight.

    With a weight of 0, blend() finds the midpoint between the two
    numbers. Otherwise, the weight pushes the midpoint up or down
    accordingly.
    """
    weighting_factor = 1 - ((1.0 - unbounded(weight)) / 2.0)
    return bind(unbounded(y) * weighting_factor + unbounded(x) * (1 - weighting_factor))


class bnum:
    """bnum(x) -> bounded floating point number

    Convert a string or number to a bounded floating point number, if possible.

    Don't try and get all devious and exact with bnums, or the
    rounding errors will eat your lunch.
    """

    __slots__ = ('value',)

    value: float

    def __hash__(self) -> int:
        return hash(self.value)

    @property
    def unbounded(self) -> float:
        """Return the unbounded value.

        Note the journey from bounded to unbounded will result in
        rounding errors.  The larger the unbounded number, the larger
        the round-trip deviation.
        """
        return _unbind(self.value)

    @classmethod
    def _check_range(cls, x: floatish) -> float:
        if isinstance(x, cls):
            return x.value

        if x <= -1.0 or x >= 1.0:
            raise InvalidRangeError('Invalid value for bnum: must be between -1.0 and 1.0', x)

        return float(x)

    def __init__(self, value: floatish) -> None:
        self.value = self._check_range(value)

    def __str__(self) -> str:
        """x.__str__() <==> str(x)"""
        return str(self.value)

    def __repr__(self) -> str:
        """x.__repr__() <==> repr(x)"""
        return f'bnum({self.value})'

    def blend(self, y: floatish, weight: floatish) -> bnum:
        """Combine with another bounded number, with an optional weight.

        With a weight of 0, blend() finds the midpoint between the two
        numbers. Otherwise, the weight pushes the midpoint up or down
        accordingly.
        """
        return blend(self, y, weight)

    def amplify(self, weight: floatish = 0.0) -> bnum:
        """Scale out away from zero, with an optional weight."""
        if self.value > 0.0:
            return blend(self, 1.0, weight)
        return blend(self, -1.0, weight)

    def suppress(self, weight: floatish = 0.0) -> bnum:
        """Scale in towards zero, with an optional weight."""
        return blend(self, 0.0, weight)

    def __add__(self, y: floatish) -> bnum:
        """x.__add__(y) <==> x+y"""
        y_ub = unbounded(y)
        return bind(self.unbounded + y_ub)

    def __truediv__(self, y: floatish) -> bnum:
        """x.__div__(y) <==> x/y"""
        y_ub = unbounded(y)
        return bind(self.unbounded / y_ub)

    def __float__(self) -> float:
        """x.__float__() <==> float(x)"""
        return float(self.value)

    def __mul__(self, y: floatish) -> bnum:
        """x.__mul__(y) <==> x*y"""
        y_ub = unbounded(y)
        return bind(self.unbounded * y_ub)

    def __pow__(self, y: floatish, mod: floatish | None = None) -> bnum:
        """x.__pow__(y[, z]) <==> pow(x, y[, z])"""
        y_ub = unbounded(y)
        mod_ub = unbounded(mod) if mod is not None else None
        return bind(pow(self.unbounded, y_ub, mod_ub))  # type: ignore[arg-type]

    def __sub__(self, y: floatish) -> bnum:
        """x.__sub__(y) <==> x-y"""
        y_ub = unbounded(y)
        return bind(self.unbounded - y_ub)

    def __reduce__(self) -> tuple[type[bnum], tuple[float]]:
        return (bnum, (self.value,))

    def __eq__(self, y: object) -> bool:
        """X == y"""
        if isinstance(y, bnum):
            return self.value == y.value
        raise TypeError("Can't compare bounded number with unbounded number.")

    def __ne__(self, y: object) -> bool:
        """X != y"""
        if isinstance(y, bnum):
            return self.value != y.value
        raise TypeError("Can't compare bounded number with unbounded number.")

    def __ge__(self, y: object) -> bool:
        """X >= y"""
        if isinstance(y, bnum):
            return self.value >= y.value
        raise TypeError("Can't compare bounded number with unbounded number.")

    def __gt__(self, y: object) -> bool:
        """X > y"""
        if isinstance(y, bnum):
            return self.value > y.value
        raise TypeError("Can't compare bounded number with unbounded number.")

    def __le__(self, y: object) -> bool:
        """X <= y"""
        if isinstance(y, bnum):
            return self.value <= y.value
        raise TypeError("Can't compare bounded number with unbounded number.")

    def __lt__(self, y: object) -> bool:
        """X < y"""
        if isinstance(y, bnum):
            return self.value < y.value
        raise TypeError("Can't compare bounded number with unbounded number.")


b = bnum


floatish = float | int | bnum
