# pava.py

from typing import Callable

import sys
import os
import re

class String:
    __slots__ = ('__value', )
    def __init__(self, value: str, passed: bool = False):
        # Remove quotes if it's a string
        if (value.startswith('"') and value.endswith('"') or value.startswith("'") and value.endswith("'")):
            self.__value = value[1:-1]
        elif passed:
            self.__value = value
        else:
            raise ValueError(f"Invalid string format: {value}")

    def __add__(self, other):
        return self.__value + other.__value

    def __sub__(self, other):
        for char in other.__value:
            self.__value = self.__value.replace(char, '', 1)
        return self.__value

    def __str__(self):
        return self.__value

class Int:
    __slots__ = ('__value', )
    def __init__(self, value: str, passed: bool = False):
        if not passed:
            # Check if the value is a valid integer
            if re.match(r'\D+', value) is not None:
                raise ValueError(f"Invalid integer format: {value}")
            
        self.__value = int(value)

    def __add__(self, other):
        return self.__value + other.__value

    def __sub__(self, other):
        return self.__value - other.__value

    def __str__(self):
        return str(self.__value)

SUPPORTED_TYPES = {
    'String' : String,
    'Int' : Int
}

SUPPORTED_FUNCTIONS = {
    'print' : print,
}

SUPPORTED_OPERATORS = {
    '+' : lambda x, y: x + y,
    '-' : lambda x, y: x - y
}


def run_pava_code(filepath: os.PathLike) -> None:
    variables: dict[str, object] = {}
    functions: dict[str, Callable] = SUPPORTED_FUNCTIONS.copy()
    operators: dict[str, Callable] = SUPPORTED_OPERATORS.copy()

    with open(filepath, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()

        # Ignore empty lines or comments
        if not line or line.startswith('#'):
            continue

        '''
        VARIABLE CREATION
        '''
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

        '''
        MATH
        '''
        # Match math operation: var_name = var_name1 operator var_name2
        match = re.match(rf'(\w+)\s*=\s*(\w+)\s*({"|".join(re.escape(op) for op in operators.keys())})\s*(\w+)', line)
        if match:
            var_name, var_name1, operator, var_name2 = match.groups()
            if isinstance(variables[var_name1], var_type := type(variables[var_name2])) and operator in operators:
                variables[var_name] = var_type(operators[operator](variables[var_name1], variables[var_name2]), passed=True)
            else:
                raise TypeError(f"Cannot use the {operator} operator on {type(variables[var_name1])} and {type(variables[var_name2])}")
            
            continue

        '''
        FUNCTION CALLS
        '''
        # Match function call: func(var_name)
        match = re.match(r'(\w+)\s*\((.*?)\)', line)
        if match:
            func_name, args = match.groups()

            if func_name in functions:
                # Split arguments by comma and strip whitespace
                args = [arg.strip() for arg in args.split(',')]

                # Check if all arguments are variables
                for arg in args:
                    if arg not in variables:
                        print(f"Error: variable '{arg}' is not defined.")
                        break
                else:
                    # Call the function with the variables as arguments
                    functions[func_name](*[variables[arg] for arg in args])
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