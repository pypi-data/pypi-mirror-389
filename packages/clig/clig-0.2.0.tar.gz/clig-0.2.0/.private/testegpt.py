import re


def extract_descriptions_with_known_params(docstring_template, param_names):
    """
    Extract function and parameter descriptions from a templated docstring,
    using known parameter names without specific placeholders for each parameter.

    Parameters
    ----------
    docstring_template : str
        The full docstring with generic placeholders like {{param_name}}: {{param_description}}.
    param_names : list
        A list of known parameter names.

    Returns
    -------
    dict
        A dictionary with 'description' for the function and 'parameters' with each parameter's description.
    """
    # Split lines to process each line individually
    lines = docstring_template.strip().splitlines()

    # Initialize the dictionary to store extracted information
    parsed_descriptions = {"description": "", "parameters": {}}

    # Locate the start of the Parameters section
    param_section_start = -1
    for i, line in enumerate(lines):
        if re.match(r"^\s*Parameters\s*$", line):
            param_section_start = i + 1
            break

    # Extract the function description (everything before the Parameters section)
    if param_section_start > 0:
        parsed_descriptions["description"] = "\n".join(lines[: param_section_start - 1]).strip()
    else:
        parsed_descriptions["description"] = docstring_template.strip()  # No Parameters section found, treat entire docstring as description

    # If there is a Parameters section, extract each parameter's description
    if param_section_start > 0:
        # Prepare to capture descriptions by flagging each known parameter
        param_pattern = r"^\s*({})\s*:\s*.*$".format("|".join(re.escape(p) for p in param_names))

        # Current parameter we’re capturing the description for
        current_param = None
        for line in lines[param_section_start:]:
            # Check if line matches a parameter start
            match = re.match(param_pattern, line)
            if match:
                # If we’re switching parameters, reset the current_param
                current_param = match.group(1)
                parsed_descriptions["parameters"][current_param] = ""
            elif current_param and line.startswith(" " * 4):  # Indented description continuation
                # Continue adding to the current parameter's description
                parsed_descriptions["parameters"][current_param] += line.strip() + " "
            else:
                # End capturing if we hit a non-indented line (end of current param description)
                current_param = None

    # Clean up extra whitespace
    for param in parsed_descriptions["parameters"]:
        parsed_descriptions["parameters"][param] = parsed_descriptions["parameters"][param].strip()

    return parsed_descriptions


# Example usage
docstring_template = """
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

param_names = ["x", "y", "z"]

parsed = extract_descriptions_with_known_params(docstring_template, param_names)
print(parsed)
