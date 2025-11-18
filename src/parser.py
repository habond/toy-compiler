"""Parser for the toy language using Lark."""

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import TypeVar

from lark import Lark, Token, Transformer, v_args

from src.ast_nodes import *

# TypeVar for preserving the return type in decorators
T = TypeVar("T", bound=ASTNode)


def with_location(node_factory: Callable[..., T]) -> Callable[..., T]:
    """Decorator that wraps a transformer method to automatically add location info.

    The decorated method can optionally accept children list and return an AST node.
    This decorator will:
    1. Use v_args(meta=True) to receive meta as first param and children as second
    2. Call the original function with children only if it accepts them
    3. Add location info to the returned AST node using meta

    Usage:
        @with_location
        def add(self, children: list) -> BinOp:
            left, right = children
            return BinOp(op=BinOpType.ADD, left=left, right=right)

        @with_location
        def break_stmt(self) -> Break:
            return Break()
    """

    @wraps(node_factory)
    @v_args(meta=True)
    def wrapper(self: "ASTBuilder", meta, children: list) -> T:
        # Check if the node_factory accepts a children parameter
        import inspect

        sig = inspect.signature(node_factory)
        params = list(sig.parameters.keys())

        # Call with children only if the function accepts it (has a second parameter after self)
        node = node_factory(self, children) if len(params) > 1 else node_factory(self)

        # Extract location from meta and add to node
        if meta and hasattr(meta, "line"):
            node.location = SourceLocation(
                file=self.filename,
                line=meta.line,
                column=meta.column,
                end_line=getattr(meta, "end_line", None),
                end_column=getattr(meta, "end_column", None),
            )
        return node

    return wrapper


class ASTBuilder(Transformer):
    """Transforms Lark parse tree into our custom AST with source location tracking."""

    def __init__(self) -> None:
        super().__init__()
        self.filename: str | None = None

    def start(self, items: list[ASTNode]) -> Program:
        return Program(top_level=items)

    # Statements
    @with_location
    def assignment(self, children: list) -> Assignment:
        name: str
        value: Expr
        name, value = children
        return Assignment(name=name, value=value)

    @with_location
    def print_stmt(self, children: list) -> Print:
        value: Expr | String = children[0]
        return Print(value=value)

    @with_location
    def println_stmt(self, children: list) -> Println:
        value: Expr | String = children[0]
        return Println(value=value)

    @with_location
    def if_stmt(self, children: list) -> IfStmt:
        condition: Expr = children[0]
        then_body: list = children[1]
        else_body: list | None = children[2] if len(children) > 2 else None
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body)

    def then_block(self, items: list) -> list:
        return list(items)

    def else_block(self, items: list) -> list:
        return list(items)

    @with_location
    def while_stmt(self, children: list) -> WhileLoop:
        condition: Expr = children[0]
        body: list = children[1:]
        return WhileLoop(condition=condition, body=list(body))

    @with_location
    def return_stmt(self, children: list) -> ReturnStmt:
        expr: Expr = children[0]
        return ReturnStmt(expr=expr)

    @with_location
    def break_stmt(self) -> Break:
        return Break()

    @with_location
    def continue_stmt(self) -> Continue:
        return Continue()

    @with_location
    def call_stmt(self, children: list) -> CallStmt:
        name: str
        args: list
        name, args = children
        # Wrap the Call expression in a CallStmt statement
        # Note: We need to create the Call node separately to also give it location
        call = Call(name=name, args=args)
        call.location = None  # Call gets location from parent CallStmt for now
        return CallStmt(call=call)

    @with_location
    def subroutine_def(self, children: list) -> SubroutineDef:
        name: str
        params: list
        body: list
        name, params, body = children
        return SubroutineDef(name=name, params=params, body=body)

    def param_list(self, items: list[str]) -> list[str]:
        return items

    def sub_body(self, items: list) -> list:
        return list(items)

    def arg_list(self, items: list) -> list:
        return list(items)

    # Expressions
    @with_location
    def number(self, children: list) -> Number:
        value: int = children[0]
        return Number(value=value)

    def NAME(self, token: Token) -> str:  # noqa: N802
        # Transform NAME tokens into strings automatically
        return str(token)

    def NUMBER(self, token: Token) -> int:  # noqa: N802
        # Transform NUMBER tokens into integers automatically
        return int(token)

    def STRING(self, token: Token) -> String:  # noqa: N802
        # Transform STRING tokens into String AST nodes automatically
        # This handles raw STRING tokens used in print/println statements
        # Note: Token transformers don't get meta, so we extract location from the token itself
        loc = SourceLocation(
            file=self.filename,
            line=token.line,
            column=token.column,
            end_line=token.end_line,
            end_column=token.end_column,
        )
        return String(value=str(token).strip('"'), location=loc)

    @with_location
    def var(self, children: list) -> Var:
        name: str = children[0]
        return Var(name=name)

    @with_location
    def call(self, children: list) -> Call:
        name: str
        args: list
        name, args = children
        return Call(name=name, args=args)

    # Binary operations - Arithmetic
    @with_location
    def add(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.ADD, left=left, right=right)

    @with_location
    def sub(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.SUB, left=left, right=right)

    @with_location
    def mul(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.MUL, left=left, right=right)

    @with_location
    def div(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.DIV, left=left, right=right)

    # Binary operations - Comparisons
    @with_location
    def eq(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.EQ, left=left, right=right)

    @with_location
    def ne(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.NE, left=left, right=right)

    @with_location
    def lt(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.LT, left=left, right=right)

    @with_location
    def le(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.LE, left=left, right=right)

    @with_location
    def gt(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.GT, left=left, right=right)

    @with_location
    def ge(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.GE, left=left, right=right)

    # Binary operations - Logical (short-circuit)
    @with_location
    def and_op(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.AND, left=left, right=right)

    @with_location
    def or_op(self, children: list) -> BinOp:
        left: Expr
        right: Expr
        left, right = children
        return BinOp(op=BinOpType.OR, left=left, right=right)

    # Unary operations
    @with_location
    def negate(self, children: list) -> UnaryOp:
        operand: Expr = children[0]
        return UnaryOp(op=UnaryOpType.NEGATE, operand=operand)

    @with_location
    def not_op(self, children: list) -> UnaryOp:
        operand: Expr = children[0]
        return UnaryOp(op=UnaryOpType.NOT, operand=operand)


class Parser:
    """Main parser class."""

    def __init__(self, grammar_path: str = "src/grammar.lark"):
        grammar_file = Path(grammar_path)
        with open(grammar_file) as f:
            grammar = f.read()

        self.parser = Lark(grammar, parser="lalr", propagate_positions=True)
        self.transformer = ASTBuilder()

    def parse(self, code: str, filename: str | None = None) -> Program:
        """Parse source code and return AST with location information.

        Args:
            code: Source code to parse
            filename: Optional filename for error messages and location tracking

        Returns:
            Program AST with location info populated in all nodes
        """
        self.transformer.filename = filename
        parse_tree = self.parser.parse(code)
        result = self.transformer.transform(parse_tree)
        assert isinstance(result, Program)
        return result
