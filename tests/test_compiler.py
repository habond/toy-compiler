"""Tests for the compiler module."""

import pytest

from src.ast_nodes import *
from src.compiler import Compiler, FrameMetadata
from src.parser import Parser


@pytest.fixture
def compiler():
    """Create a compiler instance for testing."""
    return Compiler()


@pytest.fixture
def parser():
    """Create a parser instance for testing."""
    return Parser()


def compile_code(code: str) -> str:
    """Helper function to parse and compile code."""
    parser = Parser()
    compiler = Compiler()
    ast = parser.parse(code, "test.toy")
    return compiler.compile(ast)


class TestBasicCompilation:
    """Tests for basic compilation functionality."""

    def test_empty_program(self, compiler):
        """Test compiling an empty program."""
        program = Program([])
        asm = compiler.compile(program)

        # Should contain section headers and exit code
        assert "section .text" in asm
        assert "global _start" in asm
        assert "_start:" in asm
        assert "syscall" in asm  # Exit syscall

    def test_simple_assignment(self):
        """Test compiling a simple assignment."""
        code = "x = 42;"
        asm = compile_code(code)

        # Should push number and pop to variable location
        assert "push qword 42" in asm
        assert "pop rax" in asm
        assert "mov qword [rbp" in asm

    def test_print_number(self):
        """Test compiling a print statement with a number."""
        code = "print(42);"
        asm = compile_code(code)

        assert "push qword 42" in asm
        assert "pop rdi" in asm
        assert "call print_int" in asm

    def test_println_number(self):
        """Test compiling a println statement with a number."""
        code = "println(42);"
        asm = compile_code(code)

        assert "push qword 42" in asm
        assert "call print_int" in asm
        assert "call print_newline" in asm

    def test_print_string(self):
        """Test compiling a print statement with a string."""
        code = 'print "hello";'
        asm = compile_code(code)

        assert "section .data" in asm
        assert 'db "hello"' in asm
        assert "mov rax, 1" in asm  # write syscall
        assert "syscall" in asm

    def test_println_string(self):
        """Test compiling a println statement with a string."""
        code = 'println "world";'
        asm = compile_code(code)

        assert "section .data" in asm
        assert 'db "world"' in asm
        assert "call print_newline" in asm

    def test_empty_string_print(self):
        """Test that empty strings are optimized away."""
        code = 'print "";'
        asm = compile_code(code)

        # Empty string should not generate data section or print code
        assert 'db ""' not in asm

    def test_empty_string_println(self):
        """Test that empty string println only prints newline."""
        code = 'println "";'
        asm = compile_code(code)

        # Should only have newline call, no data section for empty string
        assert "call print_newline" in asm
        assert 'db ""' not in asm


class TestArithmeticOperations:
    """Tests for arithmetic operation compilation."""

    def test_addition(self):
        """Test compiling addition."""
        code = "x = 1 + 2;"
        asm = compile_code(code)

        assert "push qword 1" in asm
        assert "push qword 2" in asm
        assert "add rax, rbx" in asm

    def test_subtraction(self):
        """Test compiling subtraction."""
        code = "x = 5 - 3;"
        asm = compile_code(code)

        assert "push qword 5" in asm
        assert "push qword 3" in asm
        assert "sub rax, rbx" in asm

    def test_multiplication(self):
        """Test compiling multiplication."""
        code = "x = 4 * 3;"
        asm = compile_code(code)

        assert "push qword 4" in asm
        assert "push qword 3" in asm
        assert "imul rax, rbx" in asm

    def test_division(self):
        """Test compiling division."""
        code = "x = 10 / 2;"
        asm = compile_code(code)

        assert "push qword 10" in asm
        assert "push qword 2" in asm
        assert "cqo" in asm  # Sign-extend
        assert "idiv rbx" in asm

    def test_unary_negation(self):
        """Test compiling unary negation."""
        code = "x = -5;"
        asm = compile_code(code)

        assert "push qword 5" in asm
        assert "neg rax" in asm


class TestLogicalOperations:
    """Tests for logical operation compilation."""

    def test_logical_and(self):
        """Test compiling logical AND."""
        code = "x = 1 && 2;"
        asm = compile_code(code)

        assert "push qword 1" in asm
        assert "push qword 2" in asm
        assert "and rax, rbx" in asm

    def test_logical_or(self):
        """Test compiling logical OR."""
        code = "x = 1 || 0;"
        asm = compile_code(code)

        assert "push qword 1" in asm
        assert "push qword 0" in asm
        assert "or rax, rbx" in asm

    def test_logical_not(self):
        """Test compiling logical NOT."""
        code = "x = !y;"
        asm = compile_code(code)

        assert "test rax, rax" in asm
        assert "sete al" in asm
        assert "movzx rax, al" in asm


class TestComparisonOperations:
    """Tests for comparison operation compilation."""

    def test_equality(self):
        """Test compiling equality comparison."""
        code = "x = a == b;"
        asm = compile_code(code)

        assert "cmp rax, rbx" in asm
        assert "sete al" in asm

    def test_inequality(self):
        """Test compiling inequality comparison."""
        code = "x = a != b;"
        asm = compile_code(code)

        assert "cmp rax, rbx" in asm
        assert "setne al" in asm

    def test_less_than(self):
        """Test compiling less than comparison."""
        code = "x = a < b;"
        asm = compile_code(code)

        assert "cmp rax, rbx" in asm
        assert "setl al" in asm

    def test_less_equal(self):
        """Test compiling less than or equal comparison."""
        code = "x = a <= b;"
        asm = compile_code(code)

        assert "cmp rax, rbx" in asm
        assert "setle al" in asm

    def test_greater_than(self):
        """Test compiling greater than comparison."""
        code = "x = a > b;"
        asm = compile_code(code)

        assert "cmp rax, rbx" in asm
        assert "setg al" in asm

    def test_greater_equal(self):
        """Test compiling greater than or equal comparison."""
        code = "x = a >= b;"
        asm = compile_code(code)

        assert "cmp rax, rbx" in asm
        assert "setge al" in asm


class TestControlFlow:
    """Tests for control flow compilation."""

    def test_if_statement(self):
        """Test compiling an if statement."""
        code = "if x > 0 { y = 1; }"
        asm = compile_code(code)

        # Should have condition check and conditional jump
        assert "cmp rax, 0" in asm
        assert "je fi." in asm  # Jump to end if false
        assert "fi." in asm  # End label

    def test_if_else_statement(self):
        """Test compiling an if-else statement."""
        code = "if x > 0 { y = 1; } else { y = 2; }"
        asm = compile_code(code)

        # Should have labels for if, else, and fi
        assert "je else." in asm
        assert "jmp fi." in asm
        assert "else." in asm
        assert "fi." in asm

    def test_while_loop(self):
        """Test compiling a while loop."""
        code = "while x < 10 { x = x + 1; }"
        asm = compile_code(code)

        # Should have loop labels and jumps
        assert "while." in asm  # Loop start
        assert "done." in asm  # Loop end
        assert "je done." in asm  # Exit if condition false
        assert "jmp while." in asm  # Jump back to start

    def test_break_statement(self):
        """Test compiling a break statement."""
        code = "while x < 10 { break; }"
        asm = compile_code(code)

        # Break should jump to loop end
        assert "jmp done." in asm

    def test_continue_statement(self):
        """Test compiling a continue statement."""
        code = "while x < 10 { continue; }"
        asm = compile_code(code)

        # Continue should jump to loop start
        assert "jmp while." in asm

    def test_for_loop(self):
        """Test compiling a for loop."""
        code = "for i = 0; i < 10; i = i + 1 { println i; }"
        asm = compile_code(code)

        # Should have loop initialization
        assert "push qword 0" in asm

        # Should have loop labels
        assert "for." in asm  # Loop condition check
        assert "update." in asm  # Update section
        assert "done." in asm  # Loop end

        # Should have condition check and conditional jump
        assert "cmp rax, 0" in asm
        assert "je done." in asm  # Exit if condition false

        # Should jump back to condition check
        assert "jmp for." in asm

    def test_for_loop_with_break(self):
        """Test compiling a for loop with break statement."""
        code = "for i = 0; i < 10; i = i + 1 { if i == 5 { break; } }"
        asm = compile_code(code)

        # Break should jump to loop end (done label)
        assert "done." in asm
        # Should have at least one jump to done (the break)
        assert asm.count("jmp done.") >= 1

    def test_for_loop_with_continue(self):
        """Test compiling a for loop with continue statement."""
        code = "for i = 0; i < 10; i = i + 1 { if i == 5 { continue; } }"
        asm = compile_code(code)

        # Continue should jump to update section
        assert "update." in asm
        # Should have at least one jump to update (the continue)
        assert asm.count("jmp update.") >= 1

    def test_nested_for_loops(self):
        """Test compiling nested for loops."""
        code = """
        for x = 0; x < 3; x = x + 1 {
            for y = 0; y < 2; y = y + 1 {
                println y;
            }
        }
        """
        asm = compile_code(code)

        # Should have two sets of loop labels
        assert asm.count("for.") >= 2  # Two for loops
        assert asm.count("update.") >= 2  # Two update sections
        assert asm.count("done.") >= 2  # Two done labels


class TestSubroutines:
    """Tests for subroutine compilation."""

    def test_subroutine_definition(self):
        """Test compiling a subroutine definition."""
        code = "sub foo() { x = 1; }"
        asm = compile_code(code)

        assert "sub_foo.start:" in asm
        assert "push rbp" in asm
        assert "mov rbp, rsp" in asm
        assert "mov rsp, rbp" in asm
        assert "pop rbp" in asm
        assert "ret" in asm

    def test_subroutine_with_params(self):
        """Test compiling a subroutine with parameters."""
        code = "sub add(a, b) { return a + b; }"
        asm = compile_code(code)

        assert "sub_add.start:" in asm
        # Parameters should be accessed with positive offsets
        assert "[rbp+16]" in asm  # First parameter
        assert "[rbp+24]" in asm  # Second parameter

    def test_subroutine_with_local_vars(self):
        """Test compiling a subroutine with local variables."""
        code = "sub test() { x = 1; y = 2; }"
        asm = compile_code(code)

        # Local variables should be allocated on stack
        assert "sub rsp," in asm  # Space allocation
        # Local vars should have negative offsets
        assert "[rbp-8]" in asm or "[rbp-16]" in asm

    def test_subroutine_return(self):
        """Test compiling a return statement."""
        code = "sub get_five() { return 5; }"
        asm = compile_code(code)

        assert "push qword 5" in asm
        assert "pop rax" in asm  # Return value in rax
        assert "ret" in asm

    def test_subroutine_call(self):
        """Test compiling a subroutine call."""
        code = """
        sub foo() { return 42; }
        foo();
        """
        asm = compile_code(code)

        assert "call sub_foo.start" in asm
        # Should clean up stack after call
        assert "add rsp," in asm
        # Should discard return value for call statement
        assert "pop rax" in asm

    def test_subroutine_call_with_args(self):
        """Test compiling a subroutine call with arguments."""
        code = """
        sub add(a, b) { return a + b; }
        result = add(1, 2);
        """
        asm = compile_code(code)

        # Arguments should be pushed in reverse order
        assert "push qword 2" in asm
        assert "push qword 1" in asm
        assert "call sub_add.start" in asm
        # Clean up 16 bytes (2 args * 8 bytes)
        assert "add rsp, 16" in asm


class TestVariableManagement:
    """Tests for variable offset calculation and management."""

    def test_single_variable(self):
        """Test that a single variable is allocated correctly."""
        code = "x = 5;"
        asm = compile_code(code)

        # Should allocate 8 bytes for one variable
        assert "sub rsp, 8" in asm
        assert "[rbp-8]" in asm

    def test_multiple_variables(self):
        """Test that multiple variables are allocated correctly."""
        code = "x = 1; y = 2; z = 3;"
        asm = compile_code(code)

        # Should allocate 24 bytes for three variables
        assert "sub rsp, 24" in asm
        # Variables should have different offsets
        assert "[rbp-8]" in asm
        assert "[rbp-16]" in asm
        assert "[rbp-24]" in asm

    def test_variable_comments(self):
        """Test that variable layout comments are generated."""
        code = "x = 1; y = 2;"
        asm = compile_code(code)

        # Should have comments showing variable layout
        assert "; Variable layout" in asm
        assert "[rbp-8]" in asm
        assert "[rbp-16]" in asm


class TestLabelGeneration:
    """Tests for unique label generation."""

    def test_unique_labels(self):
        """Test that multiple if statements get unique labels."""
        code = """
        if x > 0 { y = 1; }
        if z > 0 { w = 2; }
        """
        asm = compile_code(code)

        # Should have different label numbers
        assert "fi.0" in asm
        assert "fi.1" in asm

    def test_nested_loops(self):
        """Test unique labels for nested loops."""
        code = """
        while x < 10 {
            while y < 5 {
                y = y + 1;
            }
            x = x + 1;
        }
        """
        asm = compile_code(code)

        # Should have different label numbers for each loop
        assert "while.0" in asm
        assert "while.1" in asm
        assert "done.0" in asm
        assert "done.1" in asm


class TestEmitMethods:
    """Tests for the emit method functionality."""

    def test_emit_to_text_section(self, compiler):
        """Test emitting to text section."""
        Program([])
        compiler.frame_metadata_stack.append(FrameMetadata({}))

        compiler.emit("test code", section="text")
        output = compiler.text_top.get_output()

        assert "test code" in output

    def test_emit_to_data_section(self, compiler):
        """Test emitting to data section."""
        Program([])
        compiler.frame_metadata_stack.append(FrameMetadata({}))

        compiler.emit("test_label: db 'hello'", section="data")
        output = compiler.data.get_output()

        assert "test_label" in output

    def test_emit_invalid_section(self, compiler):
        """Test that invalid section raises error."""
        Program([])
        compiler.frame_metadata_stack.append(FrameMetadata({}))

        with pytest.raises(ValueError, match="Invalid section"):
            compiler.emit("code", section="invalid")

    def test_emit_invalid_mode(self, compiler):
        """Test that invalid mode raises error."""
        Program([])
        compiler.frame_metadata_stack.append(FrameMetadata({}))

        with pytest.raises(ValueError, match="Invalid mode"):
            compiler.emit("code", mode="invalid")


class TestComplexPrograms:
    """Tests for compiling complex programs."""

    def test_fibonacci(self):
        """Test compiling a fibonacci function."""
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
        asm = compile_code(code)

        # Should have subroutine definition
        assert "sub_fibonacci.start:" in asm
        # Should have recursive calls
        assert "call sub_fibonacci.start" in asm
        # Should have main program code
        assert "push qword 10" in asm

    def test_factorial(self):
        """Test compiling a factorial function."""
        code = """
        sub factorial(n) {
            result = 1;
            while n > 1 {
                result = result * n;
                n = n - 1;
            }
            return result;
        }

        println(factorial(5));
        """
        asm = compile_code(code)

        assert "sub_factorial.start:" in asm
        assert "while." in asm
        assert "imul rax, rbx" in asm
        assert "call sub_factorial.start" in asm

    def test_multiple_subroutines(self):
        """Test compiling multiple subroutines."""
        code = """
        sub add(a, b) { return a + b; }
        sub mul(a, b) { return a * b; }

        x = add(2, 3);
        y = mul(4, 5);
        """
        asm = compile_code(code)

        assert "sub_add.start:" in asm
        assert "sub_mul.start:" in asm
        assert "call sub_add.start" in asm
        assert "call sub_mul.start" in asm


class TestFrameMetadata:
    """Tests for frame metadata management."""

    def test_frame_metadata_stack(self, compiler):
        """Test that frame metadata is pushed and popped correctly."""
        assert len(compiler.frame_metadata_stack) == 0

        frame1 = FrameMetadata({"x": -8})
        compiler.frame_metadata_stack.append(frame1)

        assert len(compiler.frame_metadata_stack) == 1
        assert compiler.get_current_frame() == frame1

        frame2 = FrameMetadata({"a": 16, "b": 24})
        compiler.frame_metadata_stack.append(frame2)

        assert len(compiler.frame_metadata_stack) == 2
        assert compiler.get_current_frame() == frame2

        compiler.frame_metadata_stack.pop()
        assert compiler.get_current_frame() == frame1

    def test_get_var_offset(self, compiler):
        """Test getting variable offsets."""
        frame = FrameMetadata({"x": -8, "y": -16, "z": -24})
        compiler.frame_metadata_stack.append(frame)

        assert compiler.get_var_offset("x") == -8
        assert compiler.get_var_offset("y") == -16
        assert compiler.get_var_offset("z") == -24

    def test_loop_labels_stack(self, compiler):
        """Test loop label stack management."""
        frame = FrameMetadata({})
        compiler.frame_metadata_stack.append(frame)

        compiler.push_loop_labels("loop1", "end1")
        assert len(compiler.get_current_frame().loop_label_stack) == 1

        compiler.push_loop_labels("loop2", "end2")
        assert len(compiler.get_current_frame().loop_label_stack) == 2

        labels = compiler.get_current_loop_labels()
        assert labels.start == "loop2"
        assert labels.end == "end2"

        compiler.pop_loop_labels()
        assert len(compiler.get_current_frame().loop_label_stack) == 1

        labels = compiler.get_current_loop_labels()
        assert labels.start == "loop1"
        assert labels.end == "end1"
