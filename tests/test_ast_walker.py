"""Tests for the AST walker module."""

from src.ast_nodes import *
from src.ast_walker import walk


class TestBasicWalking:
    """Tests for basic AST walking."""

    def test_walk_single_node(self):
        """Test walking a single node."""
        node = Number(value=42)
        nodes = list(walk(node))
        assert len(nodes) == 1
        assert nodes[0] == node

    def test_walk_assignment(self):
        """Test walking an assignment statement."""
        node = Assignment(name="x", value=Number(value=42))
        nodes = list(walk(node))

        assert len(nodes) == 2
        assert isinstance(nodes[0], Assignment)
        assert isinstance(nodes[1], Number)

    def test_walk_binary_operation(self):
        """Test walking a binary operation."""
        node = BinOp(op=BinOpType.ADD, left=Number(value=1), right=Number(value=2))
        nodes = list(walk(node))

        assert len(nodes) == 3
        assert isinstance(nodes[0], BinOp)
        assert isinstance(nodes[1], Number)
        assert isinstance(nodes[2], Number)

    def test_walk_unary_operation(self):
        """Test walking a unary operation."""
        node = UnaryOp(op=UnaryOpType.NEGATE, operand=Number(value=5))
        nodes = list(walk(node))

        assert len(nodes) == 2
        assert isinstance(nodes[0], UnaryOp)
        assert isinstance(nodes[1], Number)

    def test_walk_function_call(self):
        """Test walking a function call."""
        node = Call(name="foo", args=[Number(value=1), Number(value=2)])
        nodes = list(walk(node))

        assert len(nodes) == 3
        assert isinstance(nodes[0], Call)
        assert isinstance(nodes[1], Number)
        assert isinstance(nodes[2], Number)


class TestStatementWalking:
    """Tests for walking statement nodes."""

    def test_walk_print(self):
        """Test walking print statement."""
        node = Print(value=Var(name="x"))
        nodes = list(walk(node))

        assert len(nodes) == 2
        assert isinstance(nodes[0], Print)
        assert isinstance(nodes[1], Var)

    def test_walk_println(self):
        """Test walking println statement."""
        node = Println(value=String(value="hello"))
        nodes = list(walk(node))

        assert len(nodes) == 2
        assert isinstance(nodes[0], Println)
        assert isinstance(nodes[1], String)

    def test_walk_return(self):
        """Test walking return statement."""
        node = ReturnStmt(expr=Number(value=42))
        nodes = list(walk(node))

        assert len(nodes) == 2
        assert isinstance(nodes[0], ReturnStmt)
        assert isinstance(nodes[1], Number)

    def test_walk_break(self):
        """Test walking break statement."""
        node = Break()
        nodes = list(walk(node))

        assert len(nodes) == 1
        assert isinstance(nodes[0], Break)

    def test_walk_continue(self):
        """Test walking continue statement."""
        node = Continue()
        nodes = list(walk(node))

        assert len(nodes) == 1
        assert isinstance(nodes[0], Continue)

    def test_walk_call_stmt(self):
        """Test walking call statement."""
        call = Call(name="foo", args=[Number(value=1)])
        node = CallStmt(call=call)
        nodes = list(walk(node))

        assert len(nodes) == 3
        assert isinstance(nodes[0], CallStmt)
        assert isinstance(nodes[1], Call)
        assert isinstance(nodes[2], Number)


class TestControlFlowWalking:
    """Tests for walking control flow structures."""

    def test_walk_if_without_else(self):
        """Test walking if statement without else."""
        node = IfStmt(
            condition=Var(name="x"),
            then_body=[Assignment(name="y", value=Number(value=1))],
        )
        nodes = list(walk(node))

        # IfStmt, Var (condition), Assignment, Number (value)
        assert len(nodes) == 4
        assert isinstance(nodes[0], IfStmt)
        assert isinstance(nodes[1], Var)
        assert isinstance(nodes[2], Assignment)
        assert isinstance(nodes[3], Number)

    def test_walk_if_with_else(self):
        """Test walking if statement with else."""
        node = IfStmt(
            condition=Var(name="x"),
            then_body=[Assignment(name="y", value=Number(value=1))],
            else_body=[Assignment(name="z", value=Number(value=2))],
        )
        nodes = list(walk(node))

        # IfStmt, Var, Assignment (then), Number, Assignment (else), Number
        assert len(nodes) == 6
        assert isinstance(nodes[0], IfStmt)
        assert isinstance(nodes[1], Var)
        assert isinstance(nodes[2], Assignment)
        assert isinstance(nodes[3], Number)
        assert isinstance(nodes[4], Assignment)
        assert isinstance(nodes[5], Number)

    def test_walk_while_loop(self):
        """Test walking while loop."""
        node = WhileLoop(
            condition=BinOp(op=BinOpType.LT, left=Var(name="x"), right=Number(value=10)),
            body=[
                Assignment(
                    name="x",
                    value=BinOp(op=BinOpType.ADD, left=Var(name="x"), right=Number(value=1)),
                )
            ],
        )
        nodes = list(walk(node))

        # WhileLoop, BinOp (condition), Var, Number, Assignment, BinOp (value), Var, Number
        assert len(nodes) == 8
        assert isinstance(nodes[0], WhileLoop)
        assert isinstance(nodes[1], BinOp)  # condition
        assert isinstance(nodes[5], BinOp)  # assignment value

    def test_walk_for_loop(self):
        """Test walking for loop."""
        node = ForLoop(
            init_var="i",
            init_value=Number(value=0),
            condition=BinOp(op=BinOpType.LT, left=Var(name="i"), right=Number(value=10)),
            update_var="i",
            update_value=BinOp(op=BinOpType.ADD, left=Var(name="i"), right=Number(value=1)),
            body=[Println(value=Var(name="i"))],
        )
        nodes = list(walk(node))

        # ForLoop, Number (init), BinOp (condition), Var, Number,
        # BinOp (update), Var, Number, Println, Var
        assert len(nodes) == 10
        assert isinstance(nodes[0], ForLoop)
        assert isinstance(nodes[1], Number)  # init_value
        assert isinstance(nodes[2], BinOp)  # condition
        assert isinstance(nodes[5], BinOp)  # update_value
        assert isinstance(nodes[8], Println)  # body


class TestProgramWalking:
    """Tests for walking program structures."""

    def test_walk_empty_program(self):
        """Test walking empty program."""
        prog = Program(top_level=[])
        nodes = list(walk(prog))

        assert len(nodes) == 1
        assert isinstance(nodes[0], Program)

    def test_walk_program_with_statements(self):
        """Test walking program with statements."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=1)),
                Print(value=Var(name="x")),
            ]
        )
        nodes = list(walk(prog))

        # Program, Assignment, Number, Print, Var
        assert len(nodes) == 5
        assert isinstance(nodes[0], Program)
        assert isinstance(nodes[1], Assignment)
        assert isinstance(nodes[2], Number)
        assert isinstance(nodes[3], Print)
        assert isinstance(nodes[4], Var)

    def test_walk_subroutine_def(self):
        """Test walking subroutine definition."""
        sub = SubroutineDef(
            name="foo",
            params=["a", "b"],
            body=[ReturnStmt(expr=Var(name="a"))],
        )
        nodes = list(walk(sub))

        # SubroutineDef, ReturnStmt, Var
        assert len(nodes) == 3
        assert isinstance(nodes[0], SubroutineDef)
        assert isinstance(nodes[1], ReturnStmt)
        assert isinstance(nodes[2], Var)

    def test_walk_program_with_subroutine(self):
        """Test walking program with subroutine."""
        prog = Program(
            top_level=[
                SubroutineDef(name="foo", params=[], body=[ReturnStmt(expr=Number(value=42))]),
                CallStmt(call=Call(name="foo", args=[])),
            ]
        )
        nodes = list(walk(prog))

        # Program, SubroutineDef, ReturnStmt, Number, CallStmt, Call
        assert len(nodes) == 6
        assert isinstance(nodes[0], Program)
        assert isinstance(nodes[1], SubroutineDef)
        assert isinstance(nodes[4], CallStmt)
        assert isinstance(nodes[5], Call)


class TestNestedStructures:
    """Tests for walking nested structures."""

    def test_walk_nested_expressions(self):
        """Test walking nested binary operations."""
        # (1 + (2 * 3))
        inner = BinOp(op=BinOpType.MUL, left=Number(value=2), right=Number(value=3))
        outer = BinOp(op=BinOpType.ADD, left=Number(value=1), right=inner)

        nodes = list(walk(outer))

        # Outer BinOp, Number(1), Inner BinOp, Number(2), Number(3)
        assert len(nodes) == 5
        assert isinstance(nodes[0], BinOp)
        assert nodes[0].op == BinOpType.ADD
        assert isinstance(nodes[2], BinOp)
        assert nodes[2].op == BinOpType.MUL

    def test_walk_nested_if_statements(self):
        """Test walking nested if statements."""
        inner_if = IfStmt(
            condition=Var(name="y"),
            then_body=[Break()],
        )
        outer_if = IfStmt(
            condition=Var(name="x"),
            then_body=[inner_if],
        )

        nodes = list(walk(outer_if))

        # Outer IfStmt, Var(x), Inner IfStmt, Var(y), Break
        assert len(nodes) == 5
        assert isinstance(nodes[0], IfStmt)
        assert isinstance(nodes[2], IfStmt)
        assert isinstance(nodes[4], Break)


class TestSkipParameter:
    """Tests for the skip parameter."""

    def test_skip_single_type(self):
        """Test skipping a single node type."""
        node = Assignment(name="x", value=Number(value=42))
        nodes = list(walk(node, skip=[Number]))

        # Should only get Assignment, Number is skipped
        assert len(nodes) == 1
        assert isinstance(nodes[0], Assignment)

    def test_skip_multiple_types(self):
        """Test skipping multiple node types."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=1)),
                Print(value=Var(name="x")),
            ]
        )
        nodes = list(walk(prog, skip=[Number, Var]))

        # Should get Program, Assignment, Print (Number and Var skipped)
        assert len(nodes) == 3
        assert isinstance(nodes[0], Program)
        assert isinstance(nodes[1], Assignment)
        assert isinstance(nodes[2], Print)

    def test_skip_subroutine_def(self):
        """Test skipping subroutine definitions."""
        prog = Program(
            top_level=[
                SubroutineDef(name="foo", params=[], body=[ReturnStmt(expr=Number(value=42))]),
                Assignment(name="x", value=Number(value=1)),
            ]
        )
        nodes = list(walk(prog, skip=[SubroutineDef]))

        # Should get Program, Assignment, Number (SubroutineDef and its children skipped)
        assert len(nodes) == 3
        assert isinstance(nodes[0], Program)
        assert isinstance(nodes[1], Assignment)
        assert isinstance(nodes[2], Number)
        # Make sure subroutine and its body weren't visited
        assert not any(isinstance(n, ReturnStmt) for n in nodes)

    def test_skip_control_flow(self):
        """Test skipping control flow structures."""
        prog = Program(
            top_level=[
                WhileLoop(
                    condition=Var(name="x"),
                    body=[Break()],
                ),
                Assignment(name="y", value=Number(value=1)),
            ]
        )
        nodes = list(walk(prog, skip=[WhileLoop]))

        # Should get Program, Assignment, Number (WhileLoop and its children skipped)
        assert len(nodes) == 3
        assert isinstance(nodes[0], Program)
        assert isinstance(nodes[1], Assignment)
        assert isinstance(nodes[2], Number)
        # Make sure while loop wasn't visited
        assert not any(isinstance(n, WhileLoop) for n in nodes)
        assert not any(isinstance(n, Break) for n in nodes)


class TestNodeCounting:
    """Tests for counting specific node types."""

    def test_count_variables(self):
        """Test counting variable references."""
        # x = y + z
        node = Assignment(
            name="x",
            value=BinOp(op=BinOpType.ADD, left=Var(name="y"), right=Var(name="z")),
        )
        variables = [n for n in walk(node) if isinstance(n, Var)]

        assert len(variables) == 2
        assert variables[0].name == "y"
        assert variables[1].name == "z"

    def test_count_function_calls(self):
        """Test counting function calls."""
        prog = Program(
            top_level=[
                CallStmt(call=Call(name="foo", args=[])),
                Assignment(name="x", value=Call(name="bar", args=[Number(value=1)])),
            ]
        )
        calls = [n for n in walk(prog) if isinstance(n, Call)]

        assert len(calls) == 2
        assert calls[0].name == "foo"
        assert calls[1].name == "bar"

    def test_count_numbers(self):
        """Test counting number literals."""
        # x = 1 + 2 + 3
        node = Assignment(
            name="x",
            value=BinOp(
                op=BinOpType.ADD,
                left=BinOp(op=BinOpType.ADD, left=Number(value=1), right=Number(value=2)),
                right=Number(value=3),
            ),
        )
        numbers = [n for n in walk(node) if isinstance(n, Number)]

        assert len(numbers) == 3
        assert [n.value for n in numbers] == [1, 2, 3]
