Bounded Numbers
===============

Bounded numbers were first conceptualized by Chris Crawford, and
introduced in his book, `Chris Crawford on Interactive Storytelling`_.

.. _Chris Crawford on Interactive Storytelling: https://www.amazon.com/Chris-Crawford-Interactive-Storytelling-ebook/dp/B00AU3JRTC

The basic idea of bounded numbers is to force the real number range
into the bounded range of ``-1.0 < b < 1.0``, with limits at -1.0 and 1.0,
with the whole range observing a bell curve distribution.

A real number can be converted to a bounded number like so::

  def _bind(unbounded_number: Union[float, int]) -> float:
      """Transform an unbounded number into an bounded number."""
      if unbounded_number > 0.0:
          return 1.0 - (1.0 / (1.0 + unbounded_number))
      else:
          return (1.0 / (1.0 - unbounded_number)) - 1.0

A bounded number may be transformed back to an unbounded number (with
rounding errors) like so::

  def _unbind(bounded_number: float) -> float:
    """Transform a bounded number into an unbounded number."""
    if bounded_number > 0.0:
        return (1.0 / (1.0 - bounded_number)) - 1.0
    else:
        return 1.0 - (1.0 / (1.0 + bounded_number))


Note that in the world of bounded numbers, from ten on up, the number
of places beyond 1 *roughly* corresponds to the number of nines.  That
is:

- 10 ~= 0.9
- 100 ~= 0.99
- 1000 ~= 0.999
- etc.

Note also that the journey from unbounded to bounded will result in
rounding errors.  The larger the unbounded number, the larger the
round-trip deviation.

Instantiating
-------------

Use the ``bnum(x)`` constructor (or its alias, ``b(x)``) to make a
bounded number from a float in the range ``-1.0 < x < 1.0``.

Use ``bind(x)`` to bind an arbitrary real number.


Blending, Amplifying, Suppressing
---------------------------------

Bounded numbers may be manipulated using the unique ``blend()``
function, which combines two bounded numbers with an optional
weight. Without a weight, ``blend(x, y)`` finds the midpoint between
``x`` and ``y``. A non-zero weight pushes the midpoint up or down
accordingly.

The ``bnum`` type also has three blending shortcuts:

- ``x.blend(y, weight=0.0)``: equivalent of ``blend(x, y, weight)``.

- ``x.amplify(weight=0.0)``: scale ``x`` away from 0.

- ``x.suppress(weight=0.0)``: scale ``x`` towards 0.
