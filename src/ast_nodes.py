"""AST Node definitions for the toy language."""

from dataclasses import dataclass
from enum import Enum


class BinOpType(Enum):
    """Binary operator types."""

    # Arithmetic operators
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"

    # Comparison operators
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="

    # Logical operators (short-circuit evaluation)
    AND = "&&"
    OR = "||"


class UnaryOpType(Enum):
    """Unary operator types."""

    NEGATE = "-"  # Arithmetic negation
    NOT = "!"  # Logical NOT


@dataclass
class ASTNode:
    """Base class for all AST nodes."""


# Statements
@dataclass
class Statement(ASTNode):
    """Base class for all statement nodes."""


@dataclass
class Assignment(Statement):
    """Variable assignment statement.

    Assigns the result of an expression to a variable name.
    """

    name: str
    value: "Expr"


@dataclass
class Print(Statement):
    """Print statement without newline.

    Outputs the value of an expression to stdout without adding a newline.
    """

    value: "Expr"


@dataclass
class Println(Statement):
    """Print statement with newline.

    Outputs the value of an expression to stdout followed by a newline.
    """

    value: "Expr"


@dataclass
class IfStmt(Statement):
    """Conditional if/else statement.

    Evaluates condition and executes then_body if true (non-zero),
    otherwise executes else_body if present.
    """

    condition: "Expr"
    then_body: list[Statement]
    else_body: list[Statement] | None = None


@dataclass
class WhileLoop(Statement):
    """While loop statement.

    Repeatedly evaluates condition and executes body while condition
    is true (non-zero).
    """

    condition: "Expr"
    body: list[Statement]


@dataclass
class ReturnStmt(Statement):
    """Return statement.

    Returns a value from a subroutine and exits the subroutine.
    """

    expr: "Expr"


@dataclass
class Break(Statement):
    """Break statement - exits the innermost loop."""


@dataclass
class Continue(Statement):
    """Continue statement - skips to next iteration of innermost loop."""


@dataclass
class CallStmt(Statement):
    """Statement wrapper for a function call expression."""

    call: "Call"


@dataclass
class SubroutineDef(ASTNode):
    """Function/subroutine definition.

    Defines a callable subroutine with parameters and a body of statements.
    """

    name: str
    params: list[str]
    body: list[Statement]


@dataclass
class Program(ASTNode):
    """Root node of the AST representing the entire program.

    Contains a list of top-level items which can be either subroutine
    definitions or statements (executed in the main program scope).
    """

    top_level: list[ASTNode]  # Can be SubroutineDef or Statement


# Expressions
@dataclass
class Expr(ASTNode):
    """Base class for expressions."""


@dataclass
class Number(Expr):
    """Integer literal expression."""

    value: int


@dataclass
class String(Expr):
    """String literal expression."""

    value: str


@dataclass
class Var(Expr):
    """Variable reference expression."""

    name: str


@dataclass
class BinOp(Expr):
    """Binary operation expression.

    Represents operations on two operands with an operator in between.

    Supported operators:
    - Arithmetic: +, -, *, /
    - Comparison: ==, !=, <, <=, >, >=
    - Logical: &&, ||

    Note: Logical operators (&&, ||) use short-circuit evaluation:
    - &&: If left is false (0), returns 0 without evaluating right
    - ||: If left is true (non-zero), returns 1 without evaluating right
    """

    op: BinOpType
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    """Unary operation expression.

    Represents operations on a single operand with an operator prefix.

    Supported operators:
    - Arithmetic negation (-): Returns the negative of the operand
    - Logical NOT (!): Returns 1 if operand is 0, otherwise returns 0
    """

    op: UnaryOpType
    operand: Expr


@dataclass
class Call(Expr):
    """Function/subroutine call expression.

    Represents calling a subroutine with a list of argument expressions.
    """

    name: str
    args: list[Expr]
