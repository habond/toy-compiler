"""Simple AST walker that yields all nodes in the tree."""

from collections.abc import Iterator

from src.ast_nodes import *


def walk(node: ASTNode, skip: list[type[ASTNode]] | None = None) -> Iterator[ASTNode]:
    """
    Walk an AST and yield every node in pre-order.

    This is a simple iterator pattern - no callbacks, no visitor methods.
    You iterate over nodes and decide what to do with each one.

    Args:
        node: The root node to start walking from
        skip: Optional list of node types to skip exploring. If a node matches any of these types,
              it won't be yielded and its children won't be visited.

    Example:
        for node in walk(program):
            if isinstance(node, Var):
                print(f"Found variable: {node.name}")

        # Skip exploring subroutines and return statements
        for node in walk(program, skip=[SubroutineDef, ReturnStmt]):
            print(type(node).__name__)
    """
    # Initialize skip list if not provided
    if skip is None:
        skip = []

    # Skip this node and its children if it matches the skip types
    if skip and type(node) in skip:
        return

    # Yield the current node
    yield node

    # Then yield all children
    match node:
        case Program(top_level=items):
            for item in items:
                yield from walk(item, skip)

        case SubroutineDef(body=body):
            for stmt in body:
                yield from walk(stmt, skip)

        case Assignment(value=value):
            yield from walk(value, skip)

        case Print(value=value):
            yield from walk(value, skip)

        case Println(value=value):
            yield from walk(value, skip)

        case ReturnStmt(expr=expr):
            if expr:
                yield from walk(expr, skip)

        case Break() | Continue():
            # Leaf nodes - no children to traverse
            pass

        case CallStmt(call=call):
            yield from walk(call, skip)

        case IfStmt(condition=condition, then_body=then_body, else_body=else_body):
            yield from walk(condition, skip)
            for stmt in then_body:
                yield from walk(stmt, skip)
            if else_body:
                for stmt in else_body:
                    yield from walk(stmt, skip)

        case WhileLoop(condition=condition, body=body):
            yield from walk(condition, skip)
            for stmt in body:
                yield from walk(stmt, skip)

        case ForLoop(
            init_value=init_value, condition=condition, update_value=update_value, body=body
        ):
            yield from walk(init_value, skip)
            yield from walk(condition, skip)
            yield from walk(update_value, skip)
            for stmt in body:
                yield from walk(stmt, skip)

        case BinOp(left=left, right=right):
            yield from walk(left, skip)
            yield from walk(right, skip)

        case UnaryOp(operand=operand):
            yield from walk(operand, skip)

        case Call(args=args):
            for arg in args:
                yield from walk(arg, skip)

        case Var() | Number() | String():
            # Leaf nodes - no children
            pass
