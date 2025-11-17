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

    pass


# Statements
@dataclass
class Statement(ASTNode):
    """Base class for all statement nodes."""

    pass


@dataclass
class Assignment(Statement):
    name: str
    value: "Expr"

    def __str__(self) -> str:
        return f"{self.name} = {self.value};"


@dataclass
class Print(Statement):
    expr: "Expr"

    def __str__(self) -> str:
        return f"print {self.expr};"


@dataclass
class IfStmt(Statement):
    condition: "Expr"
    then_body: list[Statement]
    else_body: list[Statement] | None = None

    def __str__(self) -> str:
        return f"if {self.condition}"


@dataclass
class WhileLoop(Statement):
    condition: "Expr"
    body: list[Statement]

    def __str__(self) -> str:
        return f"while {self.condition}"


@dataclass
class ReturnStmt(Statement):
    expr: "Expr"

    def __str__(self) -> str:
        return f"return {self.expr};"


@dataclass
class Break(Statement):
    """Break statement - exits the innermost loop."""

    def __str__(self) -> str:
        return "break;"


@dataclass
class Continue(Statement):
    """Continue statement - skips to next iteration of innermost loop."""

    def __str__(self) -> str:
        return "continue;"


@dataclass
class CallStmt(Statement):
    call: "Call"

    def __str__(self) -> str:
        return f"{self.call};"


@dataclass
class SubroutineDef(ASTNode):
    name: str
    params: list[str]
    body: list[Statement]

    def __str__(self) -> str:
        params_str = ", ".join(self.params)
        return f"sub {self.name}({params_str})"


@dataclass
class Program(ASTNode):
    top_level: list[ASTNode]  # Can be SubroutineDef or Statement

    def __str__(self) -> str:
        return "\n".join([str(item) for item in self.top_level])


# Expressions
@dataclass
class Expr(ASTNode):
    """Base class for expressions."""

    pass


@dataclass
class Number(Expr):
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Var(Expr):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class BinOp(Expr):
    """Binary operation expression.

    Supports arithmetic (+, -, *, /), comparison (==, !=, <, <=, >, >=),
    and logical operators (&&, ||).

    Note: Logical operators (&&, ||) use short-circuit evaluation:
    - &&: If left is false (0), returns 0 without evaluating right
    - ||: If left is true (non-zero), returns 1 without evaluating right
    """

    op: BinOpType
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"({self.left} {self.op.value} {self.right})"


@dataclass
class UnaryOp(Expr):
    """Unary operation expression.

    Supports:
    - Arithmetic negation (-): Returns the negative of the operand
    - Logical NOT (!): Returns 1 if operand is 0, otherwise returns 0
    """

    op: UnaryOpType
    operand: Expr

    def __str__(self) -> str:
        return f"({self.op.value}{self.operand})"


@dataclass
class Call(Expr):
    name: str
    args: list[Expr]

    def __str__(self) -> str:
        args_str = ", ".join([str(arg) for arg in self.args])
        return f"{self.name}({args_str})"
