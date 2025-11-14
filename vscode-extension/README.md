# Toy Language Extension for VSCode

Provides syntax highlighting and language support for the Toy programming language.

## Features

- **Syntax Highlighting** for:
  - Keywords: `if`, `else`, `while`, `print`
  - Operators: `+`, `-`, `*`, `/`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `=`
  - Comments: `//`
  - Numbers
  - Variables

- **Editor Features**:
  - Auto-closing brackets and parentheses
  - Comment toggling (Cmd/Ctrl + /)
  - Code folding with region markers

## Usage

Install the extension and open any `.toy` file to see syntax highlighting in action.

## Example

```toy
// Fibonacci sequence
a = 0;
b = 1;
i = 10;

while i > 0 {
    print a;
    temp = a + b;
    a = b;
    b = temp;
    i = i - 1;
}
```

## Language Features

The Toy language supports:
- Variables and arithmetic operations
- Comparison operators
- Control flow (if/else, while loops)
- Print statements
- Single-line comments

## Repository

[https://github.com/habond/toy-compiler](https://github.com/habond/toy-compiler)

## License

MIT
