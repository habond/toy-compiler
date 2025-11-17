"""Parser for the toy language using Lark."""

from functools import wraps
from pathlib import Path
from typing import Callable

from lark import Lark, Token, Transformer, v_args
from lark.tree import Meta

from src.ast_nodes import *


def with_location(inline: bool = True) -> Callable:
    """Decorator factory that wraps a transformer method to automatically add location info.

    Args:
        inline: Whether to use inline=True for v_args (default: True)

    The decorated method should return an AST node. This decorator will:
    1. Apply v_args(inline=inline, meta=True) to get the meta parameter
    2. Extract the meta parameter from the arguments
    3. Call the original function
    4. Add location info to the returned AST node

    Usage:
        @with_location()
        def add(self, left: Expr, right: Expr) -> BinOp:
            return BinOp(op=BinOpType.ADD, left=left, right=right)

        @with_location(inline=False)
        def if_stmt(self, items: list) -> IfStmt:
            return IfStmt(condition=items[0], then_body=items[1], ...)
    """

    def decorator(node_factory: Callable) -> Callable:
        @wraps(node_factory)
        @v_args(inline=inline, meta=True)
        def wrapper(self: "ASTBuilder", meta: Meta, *args, **kwargs) -> ASTNode:
            node = node_factory(self, *args, **kwargs)
            # Extract location from meta and add to node
            if hasattr(meta, "line"):
                node.location = SourceLocation(
                    file=self.filename,
                    line=meta.line,
                    column=meta.column,
                    end_line=getattr(meta, "end_line", None),
                    end_column=getattr(meta, "end_column", None),
                )
            return node

        return wrapper

    return decorator


class ASTBuilder(Transformer):
    """Transforms Lark parse tree into our custom AST with source location tracking."""

    def __init__(self) -> None:
        super().__init__()
        self.filename: str | None = None

    def start(self, items: list[ASTNode]) -> Program:
        return Program(top_level=items)

    # Statements
    @with_location()
    def assignment(self, name: Token, value: Expr) -> Assignment:
        return Assignment(name=str(name), value=value)

    @with_location()
    def print_stmt(self, value: Expr) -> Print:
        return Print(value=value)

    @with_location()
    def println_stmt(self, value: Expr) -> Println:
        return Println(value=value)

    @with_location(inline=False)
    def if_stmt(self, items: list) -> IfStmt:
        condition = items[0]
        then_body = items[1]
        else_body = items[2] if len(items) > 2 else None
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body)

    def then_block(self, items: list) -> list:
        return list(items)

    def else_block(self, items: list) -> list:
        return list(items)

    @with_location()
    def while_stmt(self, condition: Expr, *body: Statement) -> WhileLoop:
        return WhileLoop(condition=condition, body=list(body))

    @with_location()
    def return_stmt(self, expr: Expr) -> ReturnStmt:
        return ReturnStmt(expr=expr)

    @with_location()
    def break_stmt(self) -> Break:
        return Break()

    @with_location()
    def continue_stmt(self) -> Continue:
        return Continue()

    @with_location()
    def call_stmt(self, name: Token, args: list) -> CallStmt:
        # Wrap the Call expression in a CallStmt statement
        # Note: We need to create the Call node separately to also give it location
        call = Call(name=str(name), args=args)
        call.location = None  # Call gets location from parent CallStmt for now
        return CallStmt(call=call)

    @with_location()
    def subroutine_def(self, name: Token, params: list, body: list) -> SubroutineDef:
        return SubroutineDef(name=str(name), params=params, body=body)

    def param_list(self, items: list) -> list[str]:
        return [str(name) for name in items]

    def sub_body(self, items: list) -> list:
        return list(items)

    def arg_list(self, items: list) -> list:
        return list(items)

    # Expressions
    @with_location()
    def number(self, value: Token) -> Number:
        return Number(value=int(value))

    def STRING(self, token: Token) -> String:
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

    @with_location()
    def var(self, name: Token) -> Var:
        return Var(name=str(name))

    @with_location()
    def call(self, name: Token, args: list) -> Call:
        return Call(name=str(name), args=args)

    # Binary operations - Arithmetic
    @with_location()
    def add(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.ADD, left=left, right=right)

    @with_location()
    def sub(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.SUB, left=left, right=right)

    @with_location()
    def mul(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.MUL, left=left, right=right)

    @with_location()
    def div(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.DIV, left=left, right=right)

    # Binary operations - Comparisons
    @with_location()
    def eq(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.EQ, left=left, right=right)

    @with_location()
    def ne(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.NE, left=left, right=right)

    @with_location()
    def lt(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.LT, left=left, right=right)

    @with_location()
    def le(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.LE, left=left, right=right)

    @with_location()
    def gt(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.GT, left=left, right=right)

    @with_location()
    def ge(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.GE, left=left, right=right)

    # Binary operations - Logical (short-circuit)
    @with_location()
    def and_op(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.AND, left=left, right=right)

    @with_location()
    def or_op(self, left: Expr, right: Expr) -> BinOp:
        return BinOp(op=BinOpType.OR, left=left, right=right)

    # Unary operations
    @with_location()
    def negate(self, operand: Expr) -> UnaryOp:
        return UnaryOp(op=UnaryOpType.NEGATE, operand=operand)

    @with_location()
    def not_op(self, operand: Expr) -> UnaryOp:
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
