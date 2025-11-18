"""Tests for the assembly writer module."""

from src.asm_writer import SectionWriter


class TestSectionWriter:
    """Tests for SectionWriter class."""

    def test_init_with_section_name(self):
        """Test initialization with section name."""
        writer = SectionWriter("data")
        assert writer.section_name == "data"
        assert writer.code == []

    def test_init_without_section_name(self):
        """Test initialization without section name."""
        writer = SectionWriter()
        assert writer.section_name is None
        assert writer.code == []

    def test_emit_single_line(self):
        """Test emitting a single line of code."""
        writer = SectionWriter()
        writer.emit("mov rax, 0")
        assert writer.code == ["\tmov rax, 0"]

    def test_emit_multiple_lines(self):
        """Test emitting multiple lines of code."""
        writer = SectionWriter()
        writer.emit("mov rax, 0\nmov rbx, 1")
        assert writer.code == ["\tmov rax, 0", "\tmov rbx, 1"]

    def test_emit_with_custom_indent(self):
        """Test emitting with custom indentation level."""
        writer = SectionWriter()
        writer.emit("instruction", indent_level=2)
        assert writer.code == ["\t\tinstruction"]

    def test_emit_with_leading_whitespace(self):
        """Test that leading whitespace is stripped."""
        writer = SectionWriter()
        writer.emit("   mov rax, 0")
        assert writer.code == ["\tmov rax, 0"]

    def test_emit_empty_lines(self):
        """Test that empty lines are preserved."""
        writer = SectionWriter()
        writer.emit("mov rax, 0\n\nmov rbx, 1")
        assert writer.code == ["\tmov rax, 0", "", "\tmov rbx, 1"]

    def test_emit_with_dedent(self):
        """Test that dedent works correctly."""
        writer = SectionWriter()
        writer.emit("""
            mov rax, 0
            mov rbx, 1
        """)
        assert writer.code == ["\tmov rax, 0", "\tmov rbx, 1"]

    def test_emit_raw_single_line(self):
        """Test emitting raw code without indentation."""
        writer = SectionWriter()
        writer.emit_raw("label:")
        assert writer.code == ["label:"]

    def test_emit_raw_with_whitespace(self):
        """Test that raw emit strips leading/trailing whitespace."""
        writer = SectionWriter()
        writer.emit_raw("   label:   ")
        assert writer.code == ["label:"]

    def test_emit_raw_multiline(self):
        """Test emitting raw multiline code."""
        writer = SectionWriter()
        writer.emit_raw("""
            section .text
            global _start
        """)
        expected = "section .text\nglobal _start"
        assert writer.code == [expected]

    def test_get_output_empty(self):
        """Test get_output with no code."""
        writer = SectionWriter("data")
        assert writer.get_output() == ""

    def test_get_output_without_section(self):
        """Test get_output without section name."""
        writer = SectionWriter()
        writer.emit("mov rax, 0")
        writer.emit("mov rbx, 1")
        expected = "\tmov rax, 0\n\tmov rbx, 1"
        assert writer.get_output() == expected

    def test_get_output_with_section(self):
        """Test get_output with section name."""
        writer = SectionWriter("data")
        writer.emit("db 'hello'")
        expected = "section .data\n\tdb 'hello'"
        assert writer.get_output() == expected

    def test_mixed_emit_and_emit_raw(self):
        """Test mixing emit and emit_raw calls."""
        writer = SectionWriter()
        writer.emit_raw("_start:")
        writer.emit("mov rax, 0")
        writer.emit_raw("done:")
        writer.emit("ret")

        expected = "_start:\n\tmov rax, 0\ndone:\n\tret"
        assert writer.get_output() == expected

    def test_multiple_sections(self):
        """Test creating multiple section writers."""
        data = SectionWriter("data")
        text = SectionWriter("text")

        data.emit('msg: db "hello"')
        text.emit("mov rax, 1")

        assert data.get_output() == 'section .data\n\tmsg: db "hello"'
        assert text.get_output() == "section .text\n\tmov rax, 1"

    def test_empty_string_emit(self):
        """Test emitting empty string."""
        writer = SectionWriter()
        writer.emit("")
        # Empty string results in empty line
        assert writer.code == [""]

    def test_whitespace_only_emit(self):
        """Test emitting whitespace-only string."""
        writer = SectionWriter()
        writer.emit("   \n   ")
        # Whitespace-only results in single empty line (dedent strips the whitespace)
        assert writer.code == [""]

    def test_zero_indent_level(self):
        """Test emitting with zero indentation."""
        writer = SectionWriter()
        writer.emit("instruction", indent_level=0)
        assert writer.code == ["instruction"]

    def test_assembly_comment(self):
        """Test emitting assembly comments."""
        writer = SectionWriter()
        writer.emit("; This is a comment")
        assert writer.code == ["\t; This is a comment"]

    def test_complex_assembly_block(self):
        """Test emitting a complex assembly block."""
        writer = SectionWriter("text")
        writer.emit_raw("_start:")
        writer.emit("""
            ; Set up frame
            push rbp
            mov rbp, rsp
        """)
        writer.emit("")  # Empty line
        writer.emit("mov rax, 60")
        writer.emit("syscall")

        expected = (
            "section .text\n_start:\n\t; Set up frame\n\tpush rbp\n\t"
            "mov rbp, rsp\n\n\tmov rax, 60\n\tsyscall"
        )
        assert writer.get_output() == expected
