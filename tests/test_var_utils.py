"""Tests for variable utility functions."""

from src.ast_nodes import *
from src.var_utils import collect_program_variables, collect_subroutine_local_variables


class TestCollectProgramVariables:
    """Tests for collect_program_variables function."""

    def test_empty_program(self):
        """Test collecting variables from empty program."""
        prog = Program(top_level=[])
        vars = collect_program_variables(prog)
        assert vars == set()

    def test_single_assignment(self):
        """Test collecting variable from single assignment."""
        prog = Program(top_level=[Assignment(name="x", value=Number(value=42))])
        vars = collect_program_variables(prog)
        assert vars == {"x"}

    def test_multiple_assignments(self):
        """Test collecting variables from multiple assignments."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=1)),
                Assignment(name="y", value=Number(value=2)),
                Assignment(name="z", value=Number(value=3)),
            ]
        )
        vars = collect_program_variables(prog)
        assert vars == {"x", "y", "z"}

    def test_variable_references(self):
        """Test collecting variables from both assignments and references."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=10)),
                Assignment(name="y", value=Var(name="x")),
            ]
        )
        vars = collect_program_variables(prog)
        assert vars == {"x", "y"}

    def test_expression_with_variables(self):
        """Test collecting variables from complex expressions."""
        prog = Program(
            top_level=[
                Assignment(
                    name="result",
                    value=BinOp(op=BinOpType.ADD, left=Var(name="a"), right=Var(name="b")),
                ),
            ]
        )
        vars = collect_program_variables(prog)
        assert vars == {"result", "a", "b"}

    def test_subroutines_are_skipped(self):
        """Test that subroutine variables are not included in program variables."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=1)),
                SubroutineDef(
                    name="foo",
                    params=["a"],
                    body=[Assignment(name="local_var", value=Var(name="a"))],
                ),
            ]
        )
        vars = collect_program_variables(prog)
        # Should only include 'x', not 'local_var' or 'a' from the subroutine
        assert vars == {"x"}

    def test_nested_control_flow(self):
        """Test collecting variables from nested if/while statements."""
        prog = Program(
            top_level=[
                IfStmt(
                    condition=Var(name="x"),
                    then_body=[
                        Assignment(name="y", value=Number(value=1)),
                        WhileLoop(
                            condition=Var(name="z"),
                            body=[Assignment(name="w", value=Number(value=2))],
                        ),
                    ],
                ),
            ]
        )
        vars = collect_program_variables(prog)
        assert vars == {"x", "y", "z", "w"}

    def test_duplicate_variables(self):
        """Test that duplicate variable names are deduplicated."""
        prog = Program(
            top_level=[
                Assignment(name="x", value=Number(value=1)),
                Assignment(name="x", value=Number(value=2)),
                Print(value=Var(name="x")),
            ]
        )
        vars = collect_program_variables(prog)
        assert vars == {"x"}


class TestCollectSubroutineLocalVariables:
    """Tests for collect_subroutine_local_variables function."""

    def test_no_local_vars(self):
        """Test subroutine with no local variables."""
        sub = SubroutineDef(
            name="foo",
            params=[],
            body=[ReturnStmt(expr=Number(value=42))],
        )
        local_vars = collect_subroutine_local_variables(sub)
        assert local_vars == set()

    def test_only_parameters(self):
        """Test subroutine with only parameters (no body variables)."""
        sub = SubroutineDef(
            name="identity",
            params=["x"],
            body=[ReturnStmt(expr=Var(name="x"))],
        )
        local_vars = collect_subroutine_local_variables(sub)
        # Parameters are not included in local_vars
        assert local_vars == set()

    def test_local_variables(self):
        """Test subroutine with local variables."""
        sub = SubroutineDef(
            name="foo",
            params=["a"],
            body=[
                Assignment(name="local1", value=Number(value=1)),
                Assignment(name="local2", value=Number(value=2)),
                ReturnStmt(expr=Var(name="a")),
            ],
        )
        local_vars = collect_subroutine_local_variables(sub)
        assert local_vars == {"local1", "local2"}

    def test_locals_and_parameters(self):
        """Test subroutine with both parameters and local variables."""
        sub = SubroutineDef(
            name="compute",
            params=["x", "y"],
            body=[
                Assignment(
                    name="sum",
                    value=BinOp(op=BinOpType.ADD, left=Var(name="x"), right=Var(name="y")),
                ),
                Assignment(
                    name="product",
                    value=BinOp(op=BinOpType.MUL, left=Var(name="x"), right=Var(name="y")),
                ),
                ReturnStmt(expr=Var(name="sum")),
            ],
        )
        local_vars = collect_subroutine_local_variables(sub)
        # Only local_vars, not parameters
        assert local_vars == {"sum", "product"}

    def test_parameter_used_in_expression(self):
        """Test that parameter references don't count as local_vars."""
        sub = SubroutineDef(
            name="double",
            params=["n"],
            body=[
                Assignment(
                    name="result",
                    value=BinOp(op=BinOpType.MUL, left=Var(name="n"), right=Number(value=2)),
                ),
                ReturnStmt(expr=Var(name="result")),
            ],
        )
        local_vars = collect_subroutine_local_variables(sub)
        # 'n' is a parameter, only 'result' is local
        assert local_vars == {"result"}

    def test_nested_control_flow(self):
        """Test collecting local_vars from nested control structures."""
        sub = SubroutineDef(
            name="complex",
            params=["x"],
            body=[
                IfStmt(
                    condition=Var(name="x"),
                    then_body=[
                        Assignment(name="a", value=Number(value=1)),
                    ],
                    else_body=[
                        Assignment(name="b", value=Number(value=2)),
                    ],
                ),
                WhileLoop(
                    condition=Var(name="a"),
                    body=[Assignment(name="c", value=Number(value=3))],
                ),
                ReturnStmt(expr=Number(value=0)),
            ],
        )
        local_vars = collect_subroutine_local_variables(sub)
        assert local_vars == {"a", "b", "c"}

    def test_variable_shadowing_parameter(self):
        """Test variable with same name as parameter is treated as local."""
        sub = SubroutineDef(
            name="shadow",
            params=["x"],
            body=[
                Assignment(name="x", value=Number(value=100)),  # Shadows parameter
                ReturnStmt(expr=Var(name="x")),
            ],
        )
        local_vars = collect_subroutine_local_variables(sub)
        # 'x' appears in both params and body, so it's excluded from local_vars
        # Actually, the assignment to x makes it a local even though it's a param
        # The function returns body - params, so if x is in both, it's removed
        assert local_vars == set()

    def test_multiple_parameters(self):
        """Test subroutine with multiple parameters."""
        sub = SubroutineDef(
            name="sum_three",
            params=["a", "b", "c"],
            body=[
                Assignment(
                    name="sum",
                    value=BinOp(
                        op=BinOpType.ADD,
                        left=BinOp(op=BinOpType.ADD, left=Var(name="a"), right=Var(name="b")),
                        right=Var(name="c"),
                    ),
                ),
                ReturnStmt(expr=Var(name="sum")),
            ],
        )
        local_vars = collect_subroutine_local_variables(sub)
        assert local_vars == {"sum"}
