# pava.py

import sys
import os
import re

def prepare_string(value: str) -> str:
    # Remove quotes if it's a string
    if (value.startswith('"') and value.endswith('"') or value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    else:
        raise ValueError(f"Invalid string format: {value}")


SUPPORTED_TYPES = {
    'String' : prepare_string
}

SUPPORTED_FUNCTIONS = {
    'print' : print
}


def run_pava_code(filepath: os.PathLike) -> None:
    variables = {}

    with open(filepath, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()

        # Ignore empty lines or comments
        if not line or line.startswith('#'):
            continue

        # Match variable creation: Type var_name = value
        match = re.match(r'(\w+)\s+(\w+)\s*=\s*(.*)', line)
        if match:
            var_type, var_name, value = match.groups()

            if var_type in SUPPORTED_TYPES:
                # Call the appropriate function to prepare the value
                value = SUPPORTED_TYPES[var_type](value)

            # Save it
            variables[var_name] = value
            continue

        # Match function call: func(var_name)
        match = re.match(r'(\w+)\s*\((.*?)\)', line)
        if match:
            func_name, args = match.groups()

            if func_name in SUPPORTED_FUNCTIONS:
                # Split arguments by comma and strip whitespace
                args = [arg.strip() for arg in args.split(',')]

                # Check if all arguments are variables
                for arg in args:
                    if arg not in variables:
                        print(f"Error: variable '{arg}' is not defined.")
                        break
                else:
                    # Call the function with the variables as arguments
                    SUPPORTED_FUNCTIONS[func_name](*[variables[arg] for arg in args])
            else:
                print(f"Error: unknown function '{func_name}'")

            continue

        print(f"Error: invalid line '{line}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pava.py <filename.pava>")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"Error: file '{filepath}' does not exist.")
        sys.exit(1)

    run_pava_code(filepath)
