from pprint import pprint
import re

# Example usage
docstring_template = r"""
(.*)

Parameters
----------
(.*) : (.*)
    (.*)
(.*) : (.*)
    (.*)
(.*) : (.*)
    (.*)

Returns
-------
float
    The square root of the given number.
"""

# Example usage
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

docstring_temp = """
{{description}}

Parameters
----------
{{parameter_name}} : {{parameter_type}}
    {{parameter_description}}
"""

place_holders: dict[str, int | None | str] = {
    "description": None,
    "parameter_name": None,
    "parameter_type": None,
    "parameter_description": None,
}

list_indexes = []
for place_holder in place_holders:
    place = f"{{{place_holder}}}"
    if place in docstring_temp:
        index = docstring_temp.index(place)
        place_holders[place_holder] = index
        list_indexes.append(index)
list_indexes.sort()

for place_holder in place_holders:
    place_holders[place_holder] = list_indexes.index(place_holders[place_holder])

PARAMETER_NUMBER = 3

place = "{{parameter_name}}"
if place in docstring_temp:
    index = docstring_temp.index(place)
    substring = docstring_temp[index:]

regex_string = docstring_temp
for i in range(PARAMETER_NUMBER - 1):
    regex_string += substring

for place_holder in place_holders:
    place = f"{{{{{place_holder}}}}}"
    regex_string = regex_string.replace(place, "(.*)")

# pprint(substring)

# pprint(regex_string)


# current_param = None

match = re.match(regex_string, docstring)
if match:
    params = match.groups()
    # for place_holder in place_holders:
    #     place_holders[place_holder] = params[place_holders[place_holder]]
    #     pprint(place_holders)

# pprint(place_holders)
