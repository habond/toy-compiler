"""Tests for the parser module."""

import pytest

from src.ast_nodes import *
from src.parser import Parser


@pytest.fixture
def parser():
    """Create a parser instance for testing."""
    return Parser()


class TestBasicStatements:
    """Tests for basic statement parsing."""

    def test_assignment(self, parser):
        """Test parsing a simple assignment statement."""
        code = "x = 5;"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        stmt = ast.top_level[0]
        assert isinstance(stmt, Assignment)
        assert stmt.name == "x"
        assert isinstance(stmt.value, Number)
        assert stmt.value.value == 5

    def test_print_statement(self, parser):
        """Test parsing a print statement."""
        code = "print(42);"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        stmt = ast.top_level[0]
        assert isinstance(stmt, Print)
        assert isinstance(stmt.value, Number)
        assert stmt.value.value == 42

    def test_println_statement(self, parser):
        """Test parsing a println statement."""
        code = 'println "hello";'
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        stmt = ast.top_level[0]
        assert isinstance(stmt, Println)
        assert isinstance(stmt.value, String)
        assert stmt.value.value == "hello"

    def test_return_statement(self, parser):
        """Test parsing a return statement."""
        code = "sub foo() { return 42; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        sub = ast.top_level[0]
        assert isinstance(sub, SubroutineDef)
        assert len(sub.body) == 1
        ret = sub.body[0]
        assert isinstance(ret, ReturnStmt)
        assert isinstance(ret.expr, Number)
        assert ret.expr.value == 42

    def test_break_statement(self, parser):
        """Test parsing a break statement."""
        code = "while x < 10 { break; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        while_loop = ast.top_level[0]
        assert isinstance(while_loop, WhileLoop)
        assert len(while_loop.body) == 1
        assert isinstance(while_loop.body[0], Break)

    def test_continue_statement(self, parser):
        """Test parsing a continue statement."""
        code = "while x < 10 { continue; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        while_loop = ast.top_level[0]
        assert isinstance(while_loop, WhileLoop)
        assert len(while_loop.body) == 1
        assert isinstance(while_loop.body[0], Continue)


class TestControlFlow:
    """Tests for control flow statement parsing."""

    def test_if_statement(self, parser):
        """Test parsing an if statement."""
        code = "if x > 0 { y = 1; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        if_stmt = ast.top_level[0]
        assert isinstance(if_stmt, IfStmt)
        assert isinstance(if_stmt.condition, BinOp)
        assert if_stmt.condition.op == BinOpType.GT
        assert len(if_stmt.then_body) == 1
        assert if_stmt.else_body is None

    def test_if_else_statement(self, parser):
        """Test parsing an if-else statement."""
        code = "if x > 0 { y = 1; } else { y = 2; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        if_stmt = ast.top_level[0]
        assert isinstance(if_stmt, IfStmt)
        assert len(if_stmt.then_body) == 1
        assert if_stmt.else_body is not None
        assert len(if_stmt.else_body) == 1

    def test_while_loop(self, parser):
        """Test parsing a while loop."""
        code = "while x < 10 { x = x + 1; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        while_loop = ast.top_level[0]
        assert isinstance(while_loop, WhileLoop)
        assert isinstance(while_loop.condition, BinOp)
        assert while_loop.condition.op == BinOpType.LT
        assert len(while_loop.body) == 1


class TestExpressions:
    """Tests for expression parsing."""

    def test_number_literal(self, parser):
        """Test parsing a number literal."""
        code = "x = 42;"
        ast = parser.parse(code, "test.toy")

        value = ast.top_level[0].value
        assert isinstance(value, Number)
        assert value.value == 42

    def test_variable_reference(self, parser):
        """Test parsing a variable reference."""
        code = "x = y;"
        ast = parser.parse(code, "test.toy")

        value = ast.top_level[0].value
        assert isinstance(value, Var)
        assert value.name == "y"

    def test_string_literal(self, parser):
        """Test parsing a string literal."""
        # Note: Strings are only supported in print/println statements, not expressions
        # This tests string in print context
        code = 'print "hello world";'
        ast = parser.parse(code, "test.toy")

        value = ast.top_level[0].value
        assert isinstance(value, String)
        assert value.value == "hello world"

    def test_arithmetic_operations(self, parser):
        """Test parsing arithmetic operations."""
        # Addition
        code = "x = 1 + 2;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert isinstance(expr, BinOp)
        assert expr.op == BinOpType.ADD
        assert isinstance(expr.left, Number)
        assert isinstance(expr.right, Number)

        # Subtraction
        code = "x = 5 - 3;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert expr.op == BinOpType.SUB

        # Multiplication
        code = "x = 4 * 3;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert expr.op == BinOpType.MUL

        # Division
        code = "x = 10 / 2;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert expr.op == BinOpType.DIV

    def test_comparison_operations(self, parser):
        """Test parsing comparison operations."""
        tests = [
            ("x = a == b;", BinOpType.EQ),
            ("x = a != b;", BinOpType.NE),
            ("x = a < b;", BinOpType.LT),
            ("x = a <= b;", BinOpType.LE),
            ("x = a > b;", BinOpType.GT),
            ("x = a >= b;", BinOpType.GE),
        ]

        for code, expected_op in tests:
            ast = parser.parse(code, "test.toy")
            expr = ast.top_level[0].value
            assert isinstance(expr, BinOp)
            assert expr.op == expected_op

    def test_logical_operations(self, parser):
        """Test parsing logical operations."""
        # AND
        code = "x = a && b;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert isinstance(expr, BinOp)
        assert expr.op == BinOpType.AND

        # OR
        code = "x = a || b;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert expr.op == BinOpType.OR

    def test_unary_operations(self, parser):
        """Test parsing unary operations."""
        # Negation
        code = "x = -5;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert isinstance(expr, UnaryOp)
        assert expr.op == UnaryOpType.NEGATE
        assert isinstance(expr.operand, Number)

        # NOT
        code = "x = !y;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert isinstance(expr, UnaryOp)
        assert expr.op == UnaryOpType.NOT

    def test_operator_precedence(self, parser):
        """Test that operator precedence is correct."""
        # Multiplication before addition
        code = "x = 1 + 2 * 3;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert isinstance(expr, BinOp)
        assert expr.op == BinOpType.ADD
        assert isinstance(expr.left, Number)
        assert isinstance(expr.right, BinOp)
        assert expr.right.op == BinOpType.MUL

        # Parentheses override precedence
        code = "x = (1 + 2) * 3;"
        ast = parser.parse(code, "test.toy")
        expr = ast.top_level[0].value
        assert isinstance(expr, BinOp)
        assert expr.op == BinOpType.MUL
        assert isinstance(expr.left, BinOp)
        assert expr.left.op == BinOpType.ADD


class TestFunctionCalls:
    """Tests for function call parsing."""

    def test_function_call_no_args(self, parser):
        """Test parsing a function call with no arguments."""
        code = "foo();"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        call_stmt = ast.top_level[0]
        assert isinstance(call_stmt, CallStmt)
        assert call_stmt.call.name == "foo"
        assert len(call_stmt.call.args) == 0

    def test_function_call_with_args(self, parser):
        """Test parsing a function call with arguments."""
        code = "foo(1, 2, 3);"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        call_stmt = ast.top_level[0]
        assert isinstance(call_stmt, CallStmt)
        assert call_stmt.call.name == "foo"
        assert len(call_stmt.call.args) == 3

    def test_function_call_in_expression(self, parser):
        """Test parsing a function call used in an expression."""
        code = "x = foo(5) + 10;"
        ast = parser.parse(code, "test.toy")

        expr = ast.top_level[0].value
        assert isinstance(expr, BinOp)
        assert expr.op == BinOpType.ADD
        assert isinstance(expr.left, Call)
        assert expr.left.name == "foo"
        assert isinstance(expr.right, Number)


class TestSubroutines:
    """Tests for subroutine definition parsing."""

    def test_subroutine_no_params(self, parser):
        """Test parsing a subroutine with no parameters."""
        code = "sub foo() { x = 1; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        sub = ast.top_level[0]
        assert isinstance(sub, SubroutineDef)
        assert sub.name == "foo"
        assert len(sub.params) == 0
        assert len(sub.body) == 1

    def test_subroutine_with_params(self, parser):
        """Test parsing a subroutine with parameters."""
        code = "sub add(a, b) { return a + b; }"
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        sub = ast.top_level[0]
        assert isinstance(sub, SubroutineDef)
        assert sub.name == "add"
        assert sub.params == ["a", "b"]
        assert len(sub.body) == 1

    def test_subroutine_with_multiple_statements(self, parser):
        """Test parsing a subroutine with multiple statements."""
        code = """
        sub complex(x) {
            y = x + 1;
            z = y * 2;
            return z;
        }
        """
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 1
        sub = ast.top_level[0]
        assert isinstance(sub, SubroutineDef)
        assert len(sub.body) == 3


class TestLocationTracking:
    """Tests for source location tracking."""

    def test_statement_location(self, parser):
        """Test that statements have location information."""
        code = "x = 5;"
        ast = parser.parse(code, "test.toy")

        stmt = ast.top_level[0]
        assert stmt.location is not None
        assert stmt.location.file == "test.toy"
        assert stmt.location.line == 1
        assert stmt.location.column == 1

    def test_multiline_location(self, parser):
        """Test location tracking for multiple lines."""
        code = """x = 1;
y = 2;
z = 3;"""
        ast = parser.parse(code, "test.toy")

        assert len(ast.top_level) == 3
        assert ast.top_level[0].location.line == 1
        assert ast.top_level[1].location.line == 2
        assert ast.top_level[2].location.line == 3

    def test_nested_location(self, parser):
        """Test location tracking for nested structures."""
        code = """sub foo() {
    x = 1;
    return x;
}"""
        ast = parser.parse(code, "test.toy")

        sub = ast.top_level[0]
        assert sub.location.line == 1
        assert sub.body[0].location.line == 2
        assert sub.body[1].location.line == 3


class TestComplexPrograms:
    """Tests for complex program parsing."""

    def test_fibonacci(self, parser):
        """Test parsing a fibonacci function."""
        code = """
sub fibonacci(n) {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

x = 10;
result = fibonacci(x);
println(result);
"""
        ast = parser.parse(code, "fib.toy")

        assert len(ast.top_level) == 4
        assert isinstance(ast.top_level[0], SubroutineDef)
        assert isinstance(ast.top_level[1], Assignment)
        assert isinstance(ast.top_level[2], Assignment)
        assert isinstance(ast.top_level[3], Println)

    def test_factorial(self, parser):
        """Test parsing a factorial function."""
        code = """
sub factorial(n) {
    result = 1;
    while n > 1 {
        result = result * n;
        n = n - 1;
    }
    return result;
}
"""
        ast = parser.parse(code, "factorial.toy")

        assert len(ast.top_level) == 1
        sub = ast.top_level[0]
        assert isinstance(sub, SubroutineDef)
        assert sub.name == "factorial"
        assert len(sub.body) == 3

    def test_nested_control_flow(self, parser):
        """Test parsing nested if statements and loops."""
        code = """
while x < 10 {
    if x == 5 {
        if y > 0 {
            break;
        }
    }
    x = x + 1;
}
"""
        ast = parser.parse(code, "nested.toy")

        assert len(ast.top_level) == 1
        while_loop = ast.top_level[0]
        assert isinstance(while_loop, WhileLoop)
        assert len(while_loop.body) == 2

        outer_if = while_loop.body[0]
        assert isinstance(outer_if, IfStmt)
        assert len(outer_if.then_body) == 1

        inner_if = outer_if.then_body[0]
        assert isinstance(inner_if, IfStmt)
