"""Tests for the CLI module."""

import argparse
import sys
from pathlib import Path

import pytest

from src.cli import compile_file, main


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


class TestCompileFile:
    """Tests for the compile_file function."""

    def test_compile_simple_file(self, temp_dir):
        """Test compiling a simple toy file."""
        # Create input file
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 42;\nprintln(x);")

        output_file = temp_dir / "test.asm"

        # Compile
        compile_file(str(input_file), str(output_file))

        # Check output exists and has content
        assert output_file.exists()
        asm_content = output_file.read_text()
        assert "section .text" in asm_content
        assert "push qword 42" in asm_content

    def test_compile_with_subroutine(self, temp_dir):
        """Test compiling a file with a subroutine."""
        input_file = temp_dir / "sub.toy"
        input_file.write_text("sub add(a, b) { return a + b; }\nx = add(1, 2);")

        output_file = temp_dir / "sub.asm"

        compile_file(str(input_file), str(output_file))

        assert output_file.exists()
        asm_content = output_file.read_text()
        assert "sub_add.start:" in asm_content

    def test_input_file_not_found(self, temp_dir, capsys):
        """Test error when input file doesn't exist."""
        input_file = temp_dir / "nonexistent.toy"
        output_file = temp_dir / "output.asm"

        with pytest.raises(SystemExit) as exc_info:
            compile_file(str(input_file), str(output_file))

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_parse_error(self, temp_dir, capsys):
        """Test error handling for parse errors."""
        input_file = temp_dir / "bad_syntax.toy"
        # Invalid syntax: missing semicolon
        input_file.write_text("x = 42")

        output_file = temp_dir / "output.asm"

        with pytest.raises(SystemExit) as exc_info:
            compile_file(str(input_file), str(output_file))

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Parse error" in captured.err or "error" in captured.err.lower()

    def test_output_directory_created(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 1;")

        # Output in nested directory that doesn't exist
        output_file = temp_dir / "build" / "output" / "test.asm"

        compile_file(str(input_file), str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_read_error(self, temp_dir, capsys, monkeypatch):
        """Test error handling when file read fails."""
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 1;")

        output_file = temp_dir / "output.asm"

        # Mock Path.read_text to raise an exception
        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if self.name == "test.toy":
                raise PermissionError("Permission denied")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        with pytest.raises(SystemExit) as exc_info:
            compile_file(str(input_file), str(output_file))

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error reading" in captured.err

    def test_write_error(self, temp_dir, capsys, monkeypatch):
        """Test error handling when file write fails."""
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 1;")

        output_file = temp_dir / "output.asm"

        # Mock Path.write_text to raise an exception
        original_write_text = Path.write_text

        def mock_write_text(self, *args, **kwargs):
            if self.name == "output.asm":
                raise PermissionError("Permission denied")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(SystemExit) as exc_info:
            compile_file(str(input_file), str(output_file))

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error writing" in captured.err

    def test_success_message(self, temp_dir, capsys):
        """Test that success message is printed."""
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 1;")

        output_file = temp_dir / "test.asm"

        compile_file(str(input_file), str(output_file))

        captured = capsys.readouterr()
        assert "Generated:" in captured.out
        assert "test.asm" in captured.out


class TestMain:
    """Tests for the main CLI function."""

    def test_main_with_valid_args(self, temp_dir, monkeypatch):
        """Test main function with valid arguments."""
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 1;")

        output_file = temp_dir / "test.asm"

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["toy-compiler", str(input_file), str(output_file)])

        # Run main
        main()

        # Check output was created
        assert output_file.exists()

    def test_main_missing_arguments(self, monkeypatch, capsys):
        """Test main function with missing arguments."""
        # Mock sys.argv with missing output argument
        monkeypatch.setattr(sys, "argv", ["toy-compiler", "input.toy"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with code 2 for usage errors
        assert exc_info.value.code == 2

    def test_main_help(self, monkeypatch, capsys):
        """Test main function with help flag."""
        monkeypatch.setattr(sys, "argv", ["toy-compiler", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Help exits with code 0
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()
        assert "input" in captured.out.lower()
        assert "output" in captured.out.lower()

    def test_main_examples_in_help(self, monkeypatch, capsys):
        """Test that help includes examples."""
        monkeypatch.setattr(sys, "argv", ["toy-compiler", "--help"])

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "Examples:" in captured.out or "examples" in captured.out.lower()


class TestEndToEnd:
    """End-to-end tests for the CLI."""

    def test_compile_arithmetic(self, temp_dir):
        """Test compiling a program with arithmetic."""
        source = """
        x = 10;
        y = 20;
        z = x + y;
        println(z);
        """

        input_file = temp_dir / "arithmetic.toy"
        input_file.write_text(source)

        output_file = temp_dir / "arithmetic.asm"

        compile_file(str(input_file), str(output_file))

        asm = output_file.read_text()
        assert "push qword 10" in asm
        assert "push qword 20" in asm
        assert "add rax, rbx" in asm
        assert "call print_int" in asm

    def test_compile_control_flow(self, temp_dir):
        """Test compiling a program with control flow."""
        source = """
        x = 5;
        if x > 0 {
            println(x);
        }
        """

        input_file = temp_dir / "control.toy"
        input_file.write_text(source)

        output_file = temp_dir / "control.asm"

        compile_file(str(input_file), str(output_file))

        asm = output_file.read_text()
        assert "cmp rax, rbx" in asm
        assert "je fi." in asm
        assert "call print_int" in asm

    def test_compile_loop(self, temp_dir):
        """Test compiling a program with a loop."""
        source = """
        i = 0;
        while i < 10 {
            i = i + 1;
        }
        println(i);
        """

        input_file = temp_dir / "loop.toy"
        input_file.write_text(source)

        output_file = temp_dir / "loop.asm"

        compile_file(str(input_file), str(output_file))

        asm = output_file.read_text()
        assert "while." in asm
        assert "done." in asm
        assert "jmp while." in asm

    def test_compile_function(self, temp_dir):
        """Test compiling a program with a function."""
        source = """
        sub double(n) {
            return n * 2;
        }

        x = 21;
        result = double(x);
        println(result);
        """

        input_file = temp_dir / "function.toy"
        input_file.write_text(source)

        output_file = temp_dir / "function.asm"

        compile_file(str(input_file), str(output_file))

        asm = output_file.read_text()
        assert "sub_double.start:" in asm
        assert "call sub_double.start" in asm
        assert "imul rax, rbx" in asm

    def test_compile_string_output(self, temp_dir):
        """Test compiling a program with string output."""
        source = """
        println "Hello, World!";
        """

        input_file = temp_dir / "hello.toy"
        input_file.write_text(source)

        output_file = temp_dir / "hello.asm"

        compile_file(str(input_file), str(output_file))

        asm = output_file.read_text()
        assert "section .data" in asm
        assert 'db "Hello, World!"' in asm
        assert "call print_newline" in asm

    def test_compile_complex_program(self, temp_dir):
        """Test compiling a complex program with multiple features."""
        source = """
        sub factorial(n) {
            if n <= 1 {
                return 1;
            }
            return n * factorial(n - 1);
        }

        i = 1;
        while i <= 5 {
            result = factorial(i);
            print "factorial(";
            print(i);
            print ") = ";
            println(result);
            i = i + 1;
        }
        """

        input_file = temp_dir / "factorial.toy"
        input_file.write_text(source)

        output_file = temp_dir / "factorial.asm"

        compile_file(str(input_file), str(output_file))

        asm = output_file.read_text()

        # Check for subroutine
        assert "sub_factorial.start:" in asm

        # Check for loop
        assert "while." in asm
        assert "done." in asm

        # Check for if statement
        assert "if." in asm
        assert "fi." in asm

        # Check for string data
        assert "section .data" in asm
        assert 'db "factorial("' in asm
        assert 'db ") = "' in asm

        # Check for recursive call
        assert "call sub_factorial.start" in asm


class TestArgparse:
    """Tests for argument parsing."""

    def test_parser_description(self):
        """Test that parser has a proper description."""
        parser = argparse.ArgumentParser(
            description="Compile toy language source to x86-64 assembly"
        )
        assert parser.description is not None
        assert "toy language" in parser.description.lower()
        assert "assembly" in parser.description.lower()

    def test_positional_arguments(self, temp_dir, monkeypatch):
        """Test that positional arguments are required."""
        input_file = temp_dir / "test.toy"
        input_file.write_text("x = 1;")
        output_file = temp_dir / "test.asm"

        # Test with both arguments
        monkeypatch.setattr(sys, "argv", ["toy-compiler", str(input_file), str(output_file)])
        main()  # Should succeed

        assert output_file.exists()
