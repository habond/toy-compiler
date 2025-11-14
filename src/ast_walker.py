"""Simple AST walker that yields all nodes in the tree."""

from ast_nodes import *
from typing import Iterator


def walk(node: ASTNode) -> Iterator[ASTNode]:
    """
    Walk an AST and yield every node in pre-order.

    This is a simple iterator pattern - no callbacks, no visitor methods.
    You iterate over nodes and decide what to do with each one.

    Example:
        for node in walk(program):
            if isinstance(node, Var):
                print(f"Found variable: {node.name}")
    """
    # Yield the current node
    yield node

    # Then yield all children
    match node:
        case Program(statements=stmts):
            for stmt in stmts:
                yield from walk(stmt)

        case Assignment(value=value):
            yield from walk(value)

        case Print(expr=expr):
            yield from walk(expr)

        case IfStmt(condition=condition, then_body=then_body, else_body=else_body):
            yield from walk(condition)
            for stmt in then_body:
                yield from walk(stmt)
            if else_body:
                for stmt in else_body:
                    yield from walk(stmt)

        case WhileLoop(condition=condition, body=body):
            yield from walk(condition)
            for stmt in body:
                yield from walk(stmt)

        case BinOp(left=left, right=right):
            yield from walk(left)
            yield from walk(right)

        case Var() | Number():
            # Leaf nodes - no children
            pass


def collect_variables(program: Program) -> set[str]:
    """Example: collect all unique variables using the walker."""
    variables = set()
    for node in walk(program):
        match node:
            case Assignment(name=name):
                variables.add(name)
            case Var(name=name):
                variables.add(name)
    return variables
