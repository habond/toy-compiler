#!/usr/bin/env python3
"""Command-line interface for the toy compiler."""

import argparse
import sys
import traceback
from pathlib import Path

from src.compiler import Compiler
from src.parser import Parser


def compile_file(input_file: str, output_file: str) -> None:
    """Compile a toy source file to assembly.

    Args:
        input_file: Path to the .toy source file
        output_file: Path to write the .asm assembly file
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    # Check if input file exists
    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)

    # Read source code
    try:
        source = input_path.read_text()
    except Exception as e:
        print(f"Error reading '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    # Parse
    try:
        parser = Parser()
        ast = parser.parse(source, filename=str(input_path))
    except Exception as e:
        print(f"Parse error in '{input_file}':", file=sys.stderr)
        print(f"  {type(e).__name__}: {e}", file=sys.stderr)
        # Print traceback for detailed debugging
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Compile
    try:
        compiler = Compiler()
        asm = compiler.compile(ast)
    except Exception as e:
        print(f"Compilation error in '{input_file}':", file=sys.stderr)
        print(f"  {type(e).__name__}: {e}", file=sys.stderr)
        # Print traceback for detailed debugging
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write assembly output
    try:
        output_path.write_text(asm)
        print(f"Generated: {output_file}")
    except Exception as e:
        print(f"Error writing '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Compile toy language source to x86-64 assembly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.toy output.asm
  %(prog)s examples/arithmetic.toy build/arithmetic.asm
        """,
    )

    parser.add_argument("input", help="Input .toy source file")

    parser.add_argument("output", help="Output .asm assembly file")

    args = parser.parse_args()
    compile_file(args.input, args.output)


if __name__ == "__main__":
    main()
