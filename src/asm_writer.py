"""Assembly code writer for generating formatted x86-64 assembly output."""

from textwrap import dedent


class SectionWriter:
    """Writer for generating formatted assembly code within a section.

    Handles proper indentation and formatting of assembly instructions,
    labels, and directives within a specific section (e.g., .data, .text).

    Attributes:
        section_name: Optional name of the assembly section (e.g., "data", "text").
        code: List of assembly code lines being generated.
    """

    section_name: str | None
    code: list[str]

    def __init__(self, section_name: str | None = None):
        """Initialize the writer with an optional section name and empty code buffer.

        Args:
            section_name: Optional name of the assembly section (without the dot prefix).
                         If None, no section header will be emitted.
        """
        self.section_name = section_name
        self.code = []

    def emit(self, code: str, indent_level: int = 1) -> None:
        """Emit assembly code with automatic indentation.

        Args:
            code: The assembly code to emit (may be multiline).
            indent_level: Number of tab characters to prepend to each line.
        """
        for line in dedent(code).strip().split("\n"):
            if line.strip():  # Non-empty lines get indented
                self.code.append("\t" * indent_level + line)
            else:  # Empty lines stay empty
                self.code.append("")

    def emit_raw(self, code: str) -> None:
        """Emit assembly code without any indentation.

        Used for labels that must appear at column 0.

        Args:
            code: The assembly code to emit (labels, directives, etc.).
        """
        self.code.append(dedent(code).strip())

    def get_output(self) -> str:
        """Get the complete generated assembly code with optional section header.

        Returns:
            A string containing the section directive (if section_name is set)
            followed by all emitted assembly code joined by newlines.
            Returns empty string if no code has been emitted.
        """
        if not self.code:
            return ""

        if self.section_name:
            section_header = f"section .{self.section_name}"
            return section_header + "\n" + "\n".join(self.code)
        return "\n".join(self.code)
