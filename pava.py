# pava.py

from typing import Callable

import sys
import os
import re

TOKEN_TYPES = {
    'NUMBER': r'\d+',
    'STRING': r'"[^"]*"|\'[^\']*\'',
    'IDENTIFIER': r'[a-zA-Z_]\w*',
    'OPERATOR': r'[+\-*/=]',
    'PARENTHESIS': r'[()]',
    'WHITESPACE': r'\s+',
    'COMMENT': r'#.*'
}


class ASTNode:
    def __init__(
        self,
        type_: str,
        value: str,
        children: list['ASTNode'] = None
    ) -> None:
        self.type: str = type_
        self.value: str = value
        self.children: list['ASTNode'] = children if children is not None else []

    def __repr__(self) -> str:
        return f"{self.type}({self.value})"


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
        return String(self.__value + other.__value, passed=True)

    def __sub__(self, other):
        for char in other.__value:
            self.__value = self.__value.replace(char, '', 1)
        return String(self.__value, passed=True)

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
        return Int(self.__value + other.__value, passed=True)

    def __sub__(self, other):
        return Int(self.__value - other.__value, passed=True)

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


def tokenize(code: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    position: int = 0
    
    while position < len(code):
        matched: bool = False

        for token_type, pattern in TOKEN_TYPES.items():
            match = re.match(pattern, code[position:])

            if match:
                value = match.group(0)
                if token_type != 'WHITESPACE' and token_type != 'COMMENT':
                    tokens.append((token_type, value))

                position += len(value)
                matched = True
                break

        if not matched:
            raise ValueError(f"Unexpected character: {code[position]}")
        
    return tokens


def parse(tokens: list[tuple[str, str]]):
    def parse_expression(tokens: list[tuple[str, str]]) -> ASTNode:
        node: ASTNode = parse_term(tokens)
        
        while tokens and tokens[0][1] in ('+', '-'):
            operator = tokens.pop(0)
            node = ASTNode("OPERATOR", operator[1], [node, parse_term(tokens)])

        return node
    
    def parse_term(tokens: list[tuple[str, str]]) -> ASTNode:
        node: ASTNode = parse_factor(tokens)
        
        while tokens and tokens[0][1] in ('*', '/'):
            operator = tokens.pop(0)
            node = ASTNode("OPERATOR", operator[1], [node, parse_factor(tokens)])

        return node

    def parse_factor(tokens: list[tuple[str, str]]) -> ASTNode:
        token: tuple[str, str] = tokens.pop(0)

        if token[0] == 'PARENTHESIS' and token[1] == '(':
            expression: ASTNode = parse_expression(tokens)
            if tokens.pop(0)[1] != ')':
                raise ValueError("Expected closing parenthesis")
            else:
                return expression
        elif token[0] == 'IDENTIFIER' and token[1] in SUPPORTED_TYPES:
            type_name: str = token[1]
            var_name: str = tokens.pop(0)[1]

            if tokens.pop(0)[1] != '=':
                raise SyntaxError(f"Expected '=' after variable name, found {tokens[0]}")
            
            expression_node: ASTNode = parse_expression(tokens)

            return ASTNode("ASSIGNMENT", var_name, [expression_node])
        elif (name := token[0]) in TOKEN_TYPES and name != 'WHITESPACE' and name != 'COMMENT':
            return ASTNode(name, token[1])
        else:
            raise SyntaxError(f"Unexpected token: {token}")
        
    # Actual parse(...) code

    if len(tokens) >= 2 and tokens[0][0] == 'IDENTIFIER' and tokens[1][0] == 'PARENTHESIS' and tokens[1][1] == '(':
        # Function call
        func_name: str = tokens.pop(0)[1]
        tokens.pop(0) # Remove '('

        args: list[ASTNode] = []
        while tokens and not (tokens[0][0] == 'PARENTHESIS' and tokens[0][1] == ')'):
            args.append(parse_expression(tokens))

        if not tokens or tokens[0][1] != ')':
            raise SyntaxError("Expected ')' at end of function call")
        
        tokens.pop(0) # Remove ')'

        return ASTNode('FUNCTION_CALL', func_name, args)

    if len(tokens) >= 3 and tokens[0][0] == 'IDENTIFIER' and tokens[1][1] == '=':
        # Variable assignment
        var_name: str = tokens.pop(0)[1]
        tokens.pop(0) # Remove '='
        expression = parse_expression(tokens)

        return ASTNode('ASSIGNMENT', var_name, [expression])
    else:
        return parse_expression(tokens)


def evaluate_ast(ast: ASTNode, variables: dict[str, object], operators: dict[str, Callable]) -> object:
    if ast.type == 'NUMBER':
        return Int(ast.value, passed=True)
    elif ast.type == 'STRING':
        return String(ast.value, passed=True)
    elif ast.type == 'IDENTIFIER':
        if ast.value not in variables:
            raise NameError(f"Variable '{ast.value}' is not defined")
        else:
            return variables[ast.value]
    elif ast.type == 'OPERATOR' and ast.value in operators:
        left_value = evaluate_ast(ast.children[0], variables, operators)
        right_value = evaluate_ast(ast.children[1], variables, operators)

        return operators[ast.value](left_value, right_value)

    elif ast.type == 'ASSIGNMENT':
        var_name: str = ast.value
        var_value: object = evaluate_ast(ast.children[0], variables, operators)
        variables[var_name] = var_value
        return var_value

    else:
        raise ValueError(f"Unknown AST node type: {ast.type}")


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

        tokens: list[tuple[str, str]] = tokenize(line)

        abstract_syntax_tree: ASTNode = parse(tokens)

        if abstract_syntax_tree.type == 'ASSIGNMENT':
            evaluate_ast(abstract_syntax_tree, variables, operators)

        elif abstract_syntax_tree.type == 'FUNCTION_CALL':
            if abstract_syntax_tree.value in functions:
                args: list[object] = [evaluate_ast(arg, variables, operators) for arg in abstract_syntax_tree.children]
                functions[abstract_syntax_tree.value](*args)
            else:
                raise NameError(f"Function '{abstract_syntax_tree.value}' is not defined")

        elif abstract_syntax_tree.type == 'IDENTIFIER':
            if abstract_syntax_tree.value in variables:
                evalueation: object = evaluate_ast(abstract_syntax_tree, variables, operators)
                if type(evalueation) == type(variables[abstract_syntax_tree.value]):
                    variables[abstract_syntax_tree.value] = evalueation                    
            else:
                raise NameError(f"Variable '{abstract_syntax_tree.value}' is not defined")
        
        else:
            raise SyntaxError(f"Invalid top-level statement: {abstract_syntax_tree}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pava.py <filename.pava>")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"Error: file '{filepath}' does not exist.")
        sys.exit(1)

    run_pava_code(filepath)