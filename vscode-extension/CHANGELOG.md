# Change Log

All notable changes to the "toy-language" extension will be documented in this file.

## [0.2.0] - 2025-01-14

### Added
- Subroutine support:
  - `sub` keyword for subroutine definitions
  - `return` keyword for return statements
  - Function name highlighting in definitions and calls
  - Comma separator for parameter and argument lists
- Enhanced syntax highlighting for function calls with proper scoping

## [0.1.0] - 2025-01-14

### Added
- Initial release of Toy Language extension
- Syntax highlighting for all Toy language constructs:
  - Keywords: `if`, `else`, `while`, `print`
  - Operators: arithmetic (`+`, `-`, `*`, `/`), comparison (`==`, `!=`, `<`, `<=`, `>`, `>=`), assignment (`=`)
  - Comments: single-line `//`
  - Numbers: integer literals
  - Variables: identifiers
- Language configuration features:
  - Auto-closing brackets and parentheses
  - Comment toggling
  - Code folding with region markers
  - Proper bracket matching
