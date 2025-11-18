"""Tests for AST node definitions."""

from typing import cast

from src.ast_nodes import *


class TestSourceLocation:
    """Tests for SourceLocation."""

    def test_full_location(self):
        """Test location with all fields."""
        loc = SourceLocation(file="test.toy", line=10, column=5, end_line=10, end_column=15)
        assert str(loc) == "test.toy:10:5"

    def test_location_without_file(self):
        """Test location without filename."""
        loc = SourceLocation(line=10, column=5)
        assert str(loc) == "line 10, column 5"

    def test_empty_location(self):
        """Test location with no information."""
        loc = SourceLocation()
        assert str(loc) == "unknown location"


class TestASTNodeLocation:
    """Tests for AST node location tracking."""

    def test_node_with_location(self):
        """Test that nodes can store location."""
        loc = SourceLocation(file="test.toy", line=5, column=3)
        node = Number(value=42, location=loc)
        assert node.location == loc
        assert node.location_str() == "test.toy:5:3"

    def test_node_without_location(self):
        """Test node without location."""
        node = Number(value=42)
        assert node.location is None
        assert node.location_str() == "unknown location"


class TestStatements:
    """Tests for statement node creation."""

    def test_assignment(self):
        """Test assignment node creation."""
        value = Number(value=42)
        stmt = Assignment(name="x", value=value)
        assert stmt.name == "x"
        assert stmt.value == value

    def test_print(self):
        """Test print statement node."""
        value = String(value="hello")
        stmt = Print(value=value)
        assert stmt.value == value

    def test_println(self):
        """Test println statement node."""
        value = Number(value=10)
        stmt = Println(value=value)
        assert stmt.value == value

    def test_if_stmt_without_else(self):
        """Test if statement without else clause."""
        cond = Number(value=1)
        then_body = cast(list[Statement], [Assignment(name="x", value=Number(value=1))])
        stmt = IfStmt(condition=cond, then_body=then_body)
        assert stmt.condition == cond
        assert stmt.then_body == then_body
        assert stmt.else_body is None

    def test_if_stmt_with_else(self):
        """Test if statement with else clause."""
        cond = Number(value=1)
        then_body = cast(list[Statement], [Assignment(name="x", value=Number(value=1))])
        else_body = cast(list[Statement], [Assignment(name="x", value=Number(value=2))])
        stmt = IfStmt(condition=cond, then_body=then_body, else_body=else_body)
        assert stmt.condition == cond
        assert stmt.then_body == then_body
        assert stmt.else_body == else_body

    def test_while_loop(self):
        """Test while loop node."""
        cond = BinOp(op=BinOpType.LT, left=Var(name="x"), right=Number(value=10))
        body = cast(list[Statement], [Assignment(name="x", value=Number(value=1))])
        stmt = WhileLoop(condition=cond, body=body)
        assert stmt.condition == cond
        assert stmt.body == body

    def test_return_stmt(self):
        """Test return statement node."""
        expr = Number(value=42)
        stmt = ReturnStmt(expr=expr)
        assert stmt.expr == expr

    def test_break(self):
        """Test break statement node."""
        stmt = Break()
        assert isinstance(stmt, Break)

    def test_continue(self):
        """Test continue statement node."""
        stmt = Continue()
        assert isinstance(stmt, Continue)

    def test_call_stmt(self):
        """Test call statement node."""
        call = Call(name="foo", args=[])
        stmt = CallStmt(call=call)
        assert stmt.call == call


class TestExpressions:
    """Tests for expression node creation."""

    def test_number(self):
        """Test number literal node."""
        node = Number(value=42)
        assert node.value == 42

    def test_string(self):
        """Test string literal node."""
        node = String(value="hello")
        assert node.value == "hello"

    def test_var(self):
        """Test variable reference node."""
        node = Var(name="x")
        assert node.name == "x"

    def test_binop(self):
        """Test binary operation node."""
        left = Number(value=1)
        right = Number(value=2)
        node = BinOp(op=BinOpType.ADD, left=left, right=right)
        assert node.op == BinOpType.ADD
        assert node.left == left
        assert node.right == right

    def test_unaryop(self):
        """Test unary operation node."""
        operand = Number(value=5)
        node = UnaryOp(op=UnaryOpType.NEGATE, operand=operand)
        assert node.op == UnaryOpType.NEGATE
        assert node.operand == operand

    def test_call(self):
        """Test function call node."""
        args = cast(list[Expr], [Number(value=1), Number(value=2)])
        node = Call(name="foo", args=args)
        assert node.name == "foo"
        assert node.args == args


class TestBinOpType:
    """Tests for binary operator types."""

    def test_arithmetic_operators(self):
        """Test arithmetic operator values."""
        assert BinOpType.ADD.value == "+"
        assert BinOpType.SUB.value == "-"
        assert BinOpType.MUL.value == "*"
        assert BinOpType.DIV.value == "/"

    def test_comparison_operators(self):
        """Test comparison operator values."""
        assert BinOpType.EQ.value == "=="
        assert BinOpType.NE.value == "!="
        assert BinOpType.LT.value == "<"
        assert BinOpType.LE.value == "<="
        assert BinOpType.GT.value == ">"
        assert BinOpType.GE.value == ">="

    def test_logical_operators(self):
        """Test logical operator values."""
        assert BinOpType.AND.value == "&&"
        assert BinOpType.OR.value == "||"


class TestUnaryOpType:
    """Tests for unary operator types."""

    def test_operator_values(self):
        """Test unary operator values."""
        assert UnaryOpType.NEGATE.value == "-"
        assert UnaryOpType.NOT.value == "!"


class TestSubroutineDef:
    """Tests for subroutine definition."""

    def test_no_params(self):
        """Test subroutine with no parameters."""
        body = cast(list[Statement], [ReturnStmt(expr=Number(value=42))])
        sub = SubroutineDef(name="foo", params=[], body=body)
        assert sub.name == "foo"
        assert sub.params == []
        assert sub.body == body

    def test_with_params(self):
        """Test subroutine with parameters."""
        params = ["a", "b"]
        body = cast(list[Statement], [ReturnStmt(expr=Var(name="a"))])
        sub = SubroutineDef(name="add", params=params, body=body)
        assert sub.name == "add"
        assert sub.params == params
        assert sub.body == body


class TestProgram:
    """Tests for program node."""

    def test_empty_program(self):
        """Test empty program."""
        prog = Program(top_level=[])
        assert prog.top_level == []

    def test_program_with_statements(self):
        """Test program with statements."""
        stmts = cast(
            list[ASTNode],
            [
                Assignment(name="x", value=Number(value=1)),
                Print(value=Var(name="x")),
            ],
        )
        prog = Program(top_level=stmts)
        assert prog.top_level == stmts

    def test_program_with_subroutines(self):
        """Test program with subroutine definitions."""
        sub = SubroutineDef(name="foo", params=[], body=[])
        prog = Program(top_level=[sub])
        assert len(prog.top_level) == 1
        assert prog.top_level[0] == sub
