"""Parser for the toy language using Lark."""

from pathlib import Path
from lark import Lark, Transformer
from ast_nodes import *


class ASTBuilder(Transformer):
    """Transforms Lark parse tree into our custom AST."""

    def start(self, items):
        return Program(statements=items)

    # Statements
    def assignment(self, items):
        name = str(items[0])
        value = items[1]
        return Assignment(name=name, value=value)

    def print_stmt(self, items):
        return Print(expr=items[0])

    def if_stmt(self, items):
        condition = items[0]
        then_body = items[1]  # This will be from then_block
        else_body = items[2] if len(items) > 2 else None  # This will be from else_block if present
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body)

    def then_block(self, items):
        return list(items)

    def else_block(self, items):
        return list(items)

    def while_stmt(self, items):
        condition = items[0]
        body = list(items[1:])
        return WhileLoop(condition=condition, body=body)

    # Expressions
    def number(self, items):
        return Number(value=int(items[0]))

    def var(self, items):
        return Var(name=str(items[0]))

    # Binary operations
    def add(self, items):
        return BinOp(op="+", left=items[0], right=items[1])

    def sub(self, items):
        return BinOp(op="-", left=items[0], right=items[1])

    def mul(self, items):
        return BinOp(op="*", left=items[0], right=items[1])

    def div(self, items):
        return BinOp(op="/", left=items[0], right=items[1])


class Parser:
    """Main parser class."""

    def __init__(self, grammar_path: str = "src/grammar.lark"):
        grammar_file = Path(grammar_path)
        with open(grammar_file, "r") as f:
            grammar = f.read()

        self.parser = Lark(grammar, parser="lalr")
        self.transformer = ASTBuilder()

    def parse(self, code: str) -> Program:
        """Parse source code and return AST."""
        parse_tree = self.parser.parse(code)
        return self.transformer.transform(parse_tree)