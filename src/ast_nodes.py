"""AST Node definitions for the toy language."""

from dataclasses import dataclass
from typing import List, Optional


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
    then_body: List[Statement]
    else_body: Optional[List[Statement]] = None

    def __str__(self) -> str:
        return f"if {self.condition}"


@dataclass
class WhileLoop(Statement):
    condition: "Expr"
    body: List[Statement]

    def __str__(self) -> str:
        return f"while {self.condition}"


@dataclass
class ReturnStmt(Statement):
    expr: "Expr"

    def __str__(self) -> str:
        return f"return {self.expr};"


@dataclass
class CallStmt(Statement):
    call: "Call"

    def __str__(self) -> str:
        return f"{self.call};"


@dataclass
class SubroutineDef(ASTNode):
    name: str
    params: List[str]
    body: List[Statement]

    def __str__(self) -> str:
        params_str = ", ".join(self.params)
        return f"sub {self.name}({params_str})"


@dataclass
class Program(ASTNode):
    top_level: List[ASTNode]  # Can be SubroutineDef or Statement

    def __str__(self) -> str:
        return '\n'.join([str(item) for item in self.top_level])


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
    op: str
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass
class Call(Expr):
    name: str
    args: List[Expr]

    def __str__(self) -> str:
        args_str = ", ".join([str(arg) for arg in self.args])
        return f"{self.name}({args_str})"
