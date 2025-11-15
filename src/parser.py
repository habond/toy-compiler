"""Parser for the toy language using Lark."""

from pathlib import Path
from lark import Lark, Transformer, v_args
from src.ast_nodes import *


class ASTBuilder(Transformer):
    """Transforms Lark parse tree into our custom AST."""

    def start(self, items):
        return Program(top_level=items)

    # Statements
    @v_args(inline=True)
    def assignment(self, name, value):
        return Assignment(name=str(name), value=value)

    @v_args(inline=True)
    def print_stmt(self, expr):
        return Print(expr=expr)

    def if_stmt(self, items):
        condition = items[0]
        then_body = items[1]
        else_body = items[2] if len(items) > 2 else None
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body)

    def then_block(self, items):
        return list(items)

    def else_block(self, items):
        return list(items)

    @v_args(inline=True)
    def while_stmt(self, condition, *body):
        return WhileLoop(condition=condition, body=list(body))

    @v_args(inline=True)
    def return_stmt(self, expr):
        return ReturnStmt(expr=expr)

    @v_args(inline=True)
    def call_stmt(self, name, args):
        # Wrap the Call expression in a CallStmt statement
        return CallStmt(call=Call(name=str(name), args=args))

    @v_args(inline=True)
    def subroutine_def(self, name, params, body):
        return SubroutineDef(name=str(name), params=params, body=body)

    def param_list(self, items):
        return [str(name) for name in items]

    def sub_body(self, items):
        return list(items)

    def arg_list(self, items):
        return list(items)

    # Expressions
    @v_args(inline=True)
    def number(self, value):
        return Number(value=int(value))

    @v_args(inline=True)
    def var(self, name):
        return Var(name=str(name))

    @v_args(inline=True)
    def call(self, name, args):
        return Call(name=str(name), args=args)

    # Binary operations - Arithmetic
    @v_args(inline=True)
    def add(self, left, right):
        return BinOp(op="+", left=left, right=right)

    @v_args(inline=True)
    def sub(self, left, right):
        return BinOp(op="-", left=left, right=right)

    @v_args(inline=True)
    def mul(self, left, right):
        return BinOp(op="*", left=left, right=right)

    @v_args(inline=True)
    def div(self, left, right):
        return BinOp(op="/", left=left, right=right)

    # Binary operations - Comparisons
    @v_args(inline=True)
    def eq(self, left, right):
        return BinOp(op="==", left=left, right=right)

    @v_args(inline=True)
    def ne(self, left, right):
        return BinOp(op="!=", left=left, right=right)

    @v_args(inline=True)
    def lt(self, left, right):
        return BinOp(op="<", left=left, right=right)

    @v_args(inline=True)
    def le(self, left, right):
        return BinOp(op="<=", left=left, right=right)

    @v_args(inline=True)
    def gt(self, left, right):
        return BinOp(op=">", left=left, right=right)

    @v_args(inline=True)
    def ge(self, left, right):
        return BinOp(op=">=", left=left, right=right)


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