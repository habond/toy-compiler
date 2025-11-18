"""Convert AST nodes back to source code representation."""

from src.ast_nodes import *


class CodePrinter:
    """Converts AST back to source code.

    This class provides a clean separation between AST data structures
    and their textual representation. Unlike __str__ methods on AST nodes,
    this allows multiple representations (pretty-printed, minified, etc.)
    without polluting the AST node classes.

    Example:
        printer = CodePrinter()
        code = printer.print(ast)
    """

    def print(self, node: ASTNode, indent: int = 0) -> str:
        """Convert an AST node to source code.

        Args:
            node: The AST node to convert
            indent: Current indentation level (for nested blocks)

        Returns:
            String representation of the node as source code
        """
        indent_str = "    " * indent

        match node:
            case Program(top_level):
                return "\n\n".join(self.print(item, indent) for item in top_level)

            case SubroutineDef(name, params, body):
                params_str = ", ".join(params)
                if body:
                    body_lines = [self.print(stmt, indent + 1) for stmt in body]
                    body_str = "\n".join(body_lines)
                    return f"{indent_str}sub {name}({params_str}) {{\n{body_str}\n{indent_str}}}"
                else:
                    return f"{indent_str}sub {name}({params_str}) {{}}"

            case Assignment(name, value):
                return f"{indent_str}{name} = {self.print(value)};"

            case Print(value):
                return f"{indent_str}print {self.print(value)};"

            case Println(value):
                return f"{indent_str}println {self.print(value)};"

            case IfStmt(condition, then_body, else_body):
                result = f"{indent_str}if {self.print(condition)} {{\n"
                result += "\n".join(self.print(stmt, indent + 1) for stmt in then_body)
                result += f"\n{indent_str}}}"
                if else_body:
                    result += " else {\n"
                    result += "\n".join(self.print(stmt, indent + 1) for stmt in else_body)
                    result += f"\n{indent_str}}}"
                return result

            case WhileLoop(condition, body):
                result = f"{indent_str}while {self.print(condition)} {{\n"
                result += "\n".join(self.print(stmt, indent + 1) for stmt in body)
                result += f"\n{indent_str}}}"
                return result

            case ReturnStmt(expr):
                return f"{indent_str}return {self.print(expr)};"

            case Break():
                return f"{indent_str}break;"

            case Continue():
                return f"{indent_str}continue;"

            case CallStmt(call):
                return f"{indent_str}{self.print(call)};"

            case Number(value):
                return str(value)

            case String(value):
                return f'"{value}"'

            case Var(name):
                return name

            case BinOp(op, left, right):
                return f"({self.print(left)} {op.value} {self.print(right)})"

            case UnaryOp(op, operand):
                return f"{op.value}{self.print(operand)}"

            case Call(name, args):
                args_str = ", ".join(self.print(arg) for arg in args)
                return f"{name}({args_str})"

            case _:
                raise ValueError(f"Unknown node type: {type(node).__name__}")
