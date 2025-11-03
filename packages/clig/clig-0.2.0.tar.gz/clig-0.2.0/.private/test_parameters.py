import sys, os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from clig import get_parameter_descriptions


def test_get_parameter_descriptions():
    docstring = """
    Compute the square root of a number.

    Parameters
    ----------
    x : float
        The number for which to compute the square root.
    y : float, optional
        An additional number to adjust the result.
    z : int
        A parameter affecting the rounding.

    Returns
    -------
    float
        The square root of the given number.
    """
    result = get_parameter_descriptions(["x", "y", "z"], docstring)
    assert result["x"] == "The number for which to compute the square root."
