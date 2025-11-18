"""Tests for the code printer module."""

import pytest

from src.ast_nodes import *
from src.code_printer import CodePrinter


@pytest.fixture
def printer():
    """Create a CodePrinter instance for testing."""
    return CodePrinter()


class TestExpressionPrinting:
    """Tests for printing expressions."""

    def test_number(self, printer):
        """Test printing a number literal."""
        node = Number(value=42)
        assert printer.print(node) == "42"

    def test_string(self, printer):
        """Test printing a string literal."""
        node = String(value="hello")
        assert printer.print(node) == '"hello"'

    def test_variable(self, printer):
        """Test printing a variable reference."""
        node = Var(name="x")
        assert printer.print(node) == "x"

    def test_binary_op_addition(self, printer):
        """Test printing binary addition."""
        node = BinOp(op=BinOpType.ADD, left=Number(value=1), right=Number(value=2))
        assert printer.print(node) == "(1 + 2)"

    def test_binary_op_subtraction(self, printer):
        """Test printing binary subtraction."""
        node = BinOp(op=BinOpType.SUB, left=Number(value=5), right=Number(value=3))
        assert printer.print(node) == "(5 - 3)"

    def test_binary_op_multiplication(self, printer):
        """Test printing binary multiplication."""
        node = BinOp(op=BinOpType.MUL, left=Number(value=4), right=Number(value=3))
        assert printer.print(node) == "(4 * 3)"

    def test_binary_op_division(self, printer):
        """Test printing binary division."""
        node = BinOp(op=BinOpType.DIV, left=Number(value=10), right=Number(value=2))
        assert printer.print(node) == "(10 / 2)"

    def test_comparison_operators(self, printer):
        """Test printing comparison operators."""
        tests = [
            (BinOpType.EQ, "(a == b)"),
            (BinOpType.NE, "(a != b)"),
            (BinOpType.LT, "(a < b)"),
            (BinOpType.LE, "(a <= b)"),
            (BinOpType.GT, "(a > b)"),
            (BinOpType.GE, "(a >= b)"),
        ]
        for op, expected in tests:
            node = BinOp(op=op, left=Var(name="a"), right=Var(name="b"))
            assert printer.print(node) == expected

    def test_logical_operators(self, printer):
        """Test printing logical operators."""
        # AND
        node = BinOp(op=BinOpType.AND, left=Var(name="a"), right=Var(name="b"))
        assert printer.print(node) == "(a && b)"

        # OR
        node = BinOp(op=BinOpType.OR, left=Var(name="a"), right=Var(name="b"))
        assert printer.print(node) == "(a || b)"

    def test_unary_negate(self, printer):
        """Test printing unary negation."""
        node = UnaryOp(op=UnaryOpType.NEGATE, operand=Number(value=5))
        assert printer.print(node) == "-5"

    def test_unary_not(self, printer):
        """Test printing logical NOT."""
        node = UnaryOp(op=UnaryOpType.NOT, operand=Var(name="x"))
        assert printer.print(node) == "!x"

    def test_function_call_no_args(self, printer):
        """Test printing function call with no arguments."""
        node = Call(name="foo", args=[])
        assert printer.print(node) == "foo()"

    def test_function_call_with_args(self, printer):
        """Test printing function call with arguments."""
        node = Call(name="add", args=[Number(value=1), Number(value=2)])
        assert printer.print(node) == "add(1, 2)"

    def test_nested_expressions(self, printer):
        """Test printing nested expressions."""
        # (1 + (2 * 3))
        inner = BinOp(op=BinOpType.MUL, left=Number(value=2), right=Number(value=3))
        outer = BinOp(op=BinOpType.ADD, left=Number(value=1), right=inner)
        assert printer.print(outer) == "(1 + (2 * 3))"


class TestStatementPrinting:
    """Tests for printing statements."""

    def test_assignment(self, printer):
        """Test printing assignment statement."""
        stmt = Assignment(name="x", value=Number(value=42))
        assert printer.print(stmt) == "x = 42;"

    def test_print_statement(self, printer):
        """Test printing print statement."""
        stmt = Print(value=Number(value=42))
        assert printer.print(stmt) == "print 42;"

    def test_println_statement(self, printer):
        """Test printing println statement."""
        stmt = Println(value=String(value="hello"))
        assert printer.print(stmt) == 'println "hello";'

    def test_return_statement(self, printer):
        """Test printing return statement."""
        stmt = ReturnStmt(expr=Number(value=42))
        assert printer.print(stmt) == "return 42;"

    def test_break_statement(self, printer):
        """Test printing break statement."""
        stmt = Break()
        assert printer.print(stmt) == "break;"

    def test_continue_statement(self, printer):
        """Test printing continue statement."""
        stmt = Continue()
        assert printer.print(stmt) == "continue;"

    def test_call_statement(self, printer):
        """Test printing call statement."""
        call = Call(name="foo", args=[Number(value=1)])
        stmt = CallStmt(call=call)
        assert printer.print(stmt) == "foo(1);"


class TestControlFlowPrinting:
    """Tests for printing control flow structures."""

    def test_if_without_else(self, printer):
        """Test printing if statement without else."""
        stmt = IfStmt(
            condition=BinOp(op=BinOpType.GT, left=Var(name="x"), right=Number(value=0)),
            then_body=[Assignment(name="y", value=Number(value=1))],
        )
        expected = "if (x > 0) {\n    y = 1;\n}"
        assert printer.print(stmt) == expected

    def test_if_with_else(self, printer):
        """Test printing if statement with else."""
        stmt = IfStmt(
            condition=BinOp(op=BinOpType.GT, left=Var(name="x"), right=Number(value=0)),
            then_body=[Assignment(name="y", value=Number(value=1))],
            else_body=[Assignment(name="y", value=Number(value=2))],
        )
        expected = "if (x > 0) {\n    y = 1;\n} else {\n    y = 2;\n}"
        assert printer.print(stmt) == expected

    def test_while_loop(self, printer):
        """Test printing while loop."""
        stmt = WhileLoop(
            condition=BinOp(op=BinOpType.LT, left=Var(name="x"), right=Number(value=10)),
            body=[
                Assignment(
                    name="x",
                    value=BinOp(op=BinOpType.ADD, left=Var(name="x"), right=Number(value=1)),
                )
            ],
        )
        expected = "while (x < 10) {\n    x = (x + 1);\n}"
        assert printer.print(stmt) == expected

    def test_nested_if_statements(self, printer):
        """Test printing nested if statements."""
        inner_if = IfStmt(
            condition=BinOp(op=BinOpType.GT, left=Var(name="y"), right=Number(value=0)),
            then_body=[Break()],
        )
        outer_if = IfStmt(
            condition=BinOp(op=BinOpType.EQ, left=Var(name="x"), right=Number(value=5)),
            then_body=[inner_if],
        )
        expected = "if (x == 5) {\n    if (y > 0) {\n        break;\n    }\n}"
        assert printer.print(outer_if) == expected


class TestSubroutinePrinting:
    """Tests for printing subroutine definitions."""

    def test_subroutine_no_params_empty_body(self, printer):
        """Test printing subroutine with no parameters and empty body."""
        sub = SubroutineDef(name="foo", params=[], body=[])
        assert printer.print(sub) == "sub foo() {}"

    def test_subroutine_no_params_with_body(self, printer):
        """Test printing subroutine with no parameters and body."""
        sub = SubroutineDef(
            name="foo",
            params=[],
            body=[ReturnStmt(expr=Number(value=42))],
        )
        expected = "sub foo() {\n    return 42;\n}"
        assert printer.print(sub) == expected

    def test_subroutine_with_params(self, printer):
        """Test printing subroutine with parameters."""
        sub = SubroutineDef(
            name="add",
            params=["a", "b"],
            body=[
                ReturnStmt(expr=BinOp(op=BinOpType.ADD, left=Var(name="a"), right=Var(name="b")))
            ],
        )
        expected = "sub add(a, b) {\n    return (a + b);\n}"
        assert printer.print(sub) == expected

    def test_subroutine_with_multiple_statements(self, printer):
        """Test printing subroutine with multiple statements."""
        sub = SubroutineDef(
            name="complex",
            params=["x"],
            body=[
                Assignment(
                    name="y",
                    value=BinOp(op=BinOpType.ADD, left=Var(name="x"), right=Number(value=1)),
                ),
                Assignment(
                    name="z",
                    value=BinOp(op=BinOpType.MUL, left=Var(name="y"), right=Number(value=2)),
                ),
                ReturnStmt(expr=Var(name="z")),
            ],
        )
        expected = "sub complex(x) {\n    y = (x + 1);\n    z = (y * 2);\n    return z;\n}"
        assert printer.print(sub) == expected


class TestProgramPrinting:
    """Tests for printing entire programs."""

    def test_empty_program(self, printer):
        """Test printing empty program."""
        prog = Program(top_level=[])
        assert printer.print(prog) == ""

    def test_program_with_single_statement(self, printer):
        """Test printing program with single statement."""
        prog = Program(top_level=[Assignment(name="x", value=Number(value=42))])
        assert printer.print(prog) == "x = 42;"

    def test_program_with_multiple_statements(self, printer):
        """Test printing program with multiple statements."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=1)),
                Assignment(name="y", value=Number(value=2)),
                Print(value=BinOp(op=BinOpType.ADD, left=Var(name="x"), right=Var(name="y"))),
            ]
        )
        expected = "x = 1;\n\ny = 2;\n\nprint (x + y);"
        assert printer.print(prog) == expected

    def test_program_with_subroutine(self, printer):
        """Test printing program with subroutine."""
        prog = Program(
            top_level=[
                SubroutineDef(name="foo", params=[], body=[ReturnStmt(expr=Number(value=42))]),
                CallStmt(call=Call(name="foo", args=[])),
            ]
        )
        expected = "sub foo() {\n    return 42;\n}\n\nfoo();"
        assert printer.print(prog) == expected


class TestIndentation:
    """Tests for proper indentation."""

    def test_nested_blocks_indentation(self, printer):
        """Test that nested blocks are properly indented."""
        # Create a while loop with an if statement inside
        inner_if = IfStmt(
            condition=BinOp(op=BinOpType.EQ, left=Var(name="x"), right=Number(value=5)),
            then_body=[Break()],
        )
        while_loop = WhileLoop(
            condition=BinOp(op=BinOpType.LT, left=Var(name="x"), right=Number(value=10)),
            body=[
                inner_if,
                Assignment(
                    name="x",
                    value=BinOp(op=BinOpType.ADD, left=Var(name="x"), right=Number(value=1)),
                ),
            ],
        )

        result = printer.print(while_loop)
        lines = result.split("\n")

        # Check indentation levels
        assert lines[0].startswith("while")  # No indentation
        assert lines[1].startswith("    if")  # 1 level
        assert lines[2].startswith("        break")  # 2 levels
        assert lines[3].startswith("    }")  # 1 level
        assert lines[4].startswith("    x =")  # 1 level
        assert lines[5].startswith("}")  # No indentation
