# %%
from __future__ import annotations
from numbers import Number
from typing import Iterable, SupportsAbs, Tuple, SupportsFloat as Numeric, Callable
from numpy import arctan, cumsum, float32, interp, isnan, linspace, ndarray, tan, pi as M_PI, asarray, all, tanh
from datetime import datetime

"""
iri20py.utils
================

This module provides utility functions for the iri20py package.
"""


def glowdate(t: datetime) -> Tuple[int, int, Numeric]:
    """## Convert datetime to GLOW date and UT seconds.

    ### Args:
        - `t (datetime)`: Datetime object.

    ### Returns:
        - `Tuple[int, int, Numeric]`: year, day of year, and UT seconds.
    """
    year = int(f'{t.year:04}')
    idate = int(f'{t:%j}')
    utsec = (t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6)

    return (year, idate, utsec)


def nan_helper(y: ndarray) -> Tuple[ndarray, Callable[[ndarray], ndarray]]:
    """## Helper function to return NaN indices and a function to return non-NaN indices.

    ### Args:
        - `y (ndarray)`: Input 1-D array with NaNs.

    ### Returns:
        - `Tuple[ndarray, Callable[[ndarray], ndarray]]`: Tuple of NaN indices and a function to return non-NaN indices.

    ### Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return isnan(y), lambda z: z.nonzero()[0]


def interpolate_nan(y: ndarray, *, inplace: bool = True, left: SupportsAbs = None, right: SupportsAbs = None, period: Numeric = None) -> ndarray:
    """## Interpolate NaNs in a 1-D array.

    ### Args:
        - `y (ndarray)`: 1-D Array.
        - `inplace (bool, optional)`: Change input array in place. Defaults to True.
        - `left (Numeric, optional)`: Left boundary value. Defaults to 0.
        - `right (Numeric, optional)`: Right boundary value. Defaults to None.
        - `period (Numeric, optional)`: Period of the array. Defaults to None.

    ### Returns:
        - `ndarray`: Interpolated array.
    """
    if not inplace:
        y = y.copy()
    nans, x = nan_helper(y)
    y[nans] = interp(x(nans), x(~nans), y[~nans], left=left, right=right, period=period)
    return y


def alt_grid(num: int = 250, minalt: Numeric = 60, dmin: Numeric = 0.5, dmax: Numeric = 4) -> ndarray:
    """## Generate a non-linear altitude grid.
    The altitude grid uses the hyperbolic tangent function to create a non-linear grid.
    The grid, due to the hyperbolic tangent, is denser at lower altitudes and sparser at higher altitudes.

    ### Args:
        - `num (int, optional)`: Number of points. Defaults to 250.
        - `minalt (Numeric, optional)`: Minimum altitude (km). Defaults to 60.
        - `dmin (Numeric, optional)`: Minimum grid spacing at minimum altitude (km). Defaults to 0.5.
        - `dmax (Numeric, optional)`: Maximum grid spacing at maximum altitude (km). Defaults to 4.

    ### Returns:
        - `ndarray`: Altitude grid (km)
    """
    out = linspace(0, 3.14, num, dtype=float32, endpoint=False)  # tanh gets to 99% of asymptote
    tanh(out, out=out, order='F')
    out *= dmax
    out += dmin
    cumsum(out, out=out)
    out += minalt - dmin
    return out

class Singleton(object):
    """
    ## A non-thread-safe helper class to ease implementing singletons.
    The class that should be a singleton should inherit from this class.

    If the class requires initialization,
    1. Do NOT provide an `__init__` method.
    2. Instead, provide a `_init` method that will be called only once.
    3. Classes that inherit from a class inheriting from `Singleton` will NOT
    have its `_init` method called.
    """
    def __new__(cls):
        try:
            return cls.__instance
        except AttributeError:
            pass
        cls.__instance = super(Singleton, cls).__new__(cls)
        try:
            cls.__instance._init()
        except AttributeError:
            pass
        return cls.__instance


class singleton:
    """
    ## A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def __call__(self, *args, **kwargs):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        # https://stackoverflow.com/a/903238/5214809
        # The try except method is faster on the happy path by about 2x than hasattr
        # But it may capture AttributeError from the instantiation which is not
        # the intended behavior. To avoid this, the instantiation is done outside
        # the try except block.
        try:
            return self._instance
        except AttributeError:
            pass
        self._instance = self._decorated(*args, **kwargs)
        return self._instance


# %% Test functions
if __name__ == '__main__':
    import numpy as np
    y = np.array([0, 1, np.nan, np.nan, 4, 5, 6, np.nan, 8, 9])
    assert np.allclose(interpolate_nan(y),  [0., 1., 2., 3., 4., 5., 6., 7., 8., 9.])
    y = np.array([1, 1, 1, np.nan, np.nan, 2, 2, np.nan, 0])
    assert np.allclose(np.round(interpolate_nan(y), 2), [1., 1., 1., 1.33, 1.67, 2., 2., 1., 0.])
    lats = np.arange(-80, 80, 20)
    glats = geocent_to_geodet(lats)
    gglats = list(map(geocent_to_geodet, lats))
    assert np.allclose(glats, gglats)

# %%
