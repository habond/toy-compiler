"""AST Node definitions for the toy language."""

from dataclasses import dataclass, field
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
class SourceLocation:
    """Source code location information for an AST node.

    Tracks the file, line, and column where a construct appears in source code.
    Used for error messages and debugging.
    """

    file: str | None = None
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __str__(self) -> str:
        """Format source location as a string for error messages.

        Returns:
            String like "file.toy:10:5" or "unknown location" if not available
        """
        if self.file and self.line and self.column:
            return f"{self.file}:{self.line}:{self.column}"
        elif self.line and self.column:
            return f"line {self.line}, column {self.column}"
        return "unknown location"


@dataclass
class ASTNode:
    """Base class for all AST nodes.

    All AST nodes track their source location for better error messages
    and debugging. Location is optional and populated during parsing.
    """

    location: SourceLocation | None = field(default=None, kw_only=True)

    def location_str(self) -> str:
        """Format source location as a string for error messages.

        Returns:
            String like "file.toy:10:5" or "unknown location" if not available
        """
        return str(self.location) if self.location else "unknown location"


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
class ForLoop(Statement):
    """For loop statement.

    Executes initialization once, then repeatedly evaluates condition and
    executes body followed by update while condition is true (non-zero).

    Equivalent to:
        init;
        while (condition) {
            body;
            update;
        }
    """

    init_var: str
    init_value: "Expr"
    condition: "Expr"
    update_var: str
    update_value: "Expr"
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
