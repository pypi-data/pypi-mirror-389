from pprint import pprint

import numpy as np

from clig import NUMPY_DOCSTRING, get_docstring_data

np.array

if __name__ == "__main__":
    # Example usage
    docstring = """
            Compute the square root of a number.
            
            Teste

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

    pprint(get_docstring_data(3, docstring, NUMPY_DOCSTRING))
