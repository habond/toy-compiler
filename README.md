# Toy Compiler

A simple toy programming language with a lexer/parser built using [Lark](https://lark-parser.readthedocs.io/).

## Features

The language supports:

- **Variables**: Assignment and usage
- **Arithmetic**: `+`, `-`, `*`, `/` with proper operator precedence
- **Comparisons**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Control Flow**: `if` statements with optional `else` blocks, `while` loops
- **Output**: `print` statement
- **Comments**: Single-line comments with `//`

## Syntax

### Comments
```
// Single-line comments are supported
x = 42;  // Inline comments too
```

### Variables and Arithmetic
```
x = 10;
y = 20;
z = x + y * 2;  // Supports operator precedence
```

### Comparisons
```
// All comparison operators return 1 (true) or 0 (false)
result = x == y;   // Equal to
result = x != y;   // Not equal to
result = x < y;    // Less than
result = x <= y;   // Less than or equal
result = x > y;    // Greater than
result = x >= y;   // Greater than or equal

// Comparisons work with expressions
result = x + 1 < y * 2;
```

### Conditionals
```
// Conditions support both truthy/falsy and comparisons
if x > 5 {
    print 100;
} else {
    print 200;
}

// Truthy/falsy evaluation (non-zero/zero)
if x {
    print 999;
}

// Else block is optional
if y == 0 {
    print 0;
}
```

### Loops
```
// While loops with comparisons
counter = 5;
while counter > 0 {
    print counter;
    counter = counter - 1;
}

// Truthy/falsy also works
x = 5;
while x {
    print x;
    x = x - 1;
}
```

## Project Structure

```
toy-compiler/
├── src/
│   ├── grammar.lark      # Lark grammar definition
│   ├── ast_nodes.py      # AST node class definitions
│   ├── ast_walker.py     # AST walker utilities
│   ├── parser.py         # Parser and AST builder
│   ├── compiler.py       # Compiler (AST -> x86-64 assembly)
│   └── cli.py            # Command-line interface
├── lib/
│   └── printf.asm        # Assembly helper for printing
├── examples/             # Example programs with expected outputs
│   ├── hello.toy
│   ├── hello.expected
│   ├── arithmetic.toy
│   ├── arithmetic.expected
│   ├── test.toy
│   ├── test.expected
│   ├── conditional.toy
│   ├── conditional.expected
│   ├── loop.toy
│   ├── loop.expected
│   ├── comparisons.toy
│   ├── comparisons.expected
│   ├── comprehensive.toy
│   └── comprehensive.expected
├── build/                # Build outputs (assembly, objects, executables)
├── Dockerfile            # Docker image for NASM + ld
├── compile.sh            # Build script (compile -> assemble -> link -> test)
├── Makefile              # Convenient build commands
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

The CLI provides separate error reporting for parsing and compilation:

```bash
# Using the CLI directly
python3 src/cli.py examples/hello.toy build/hello.asm
```

### Programmatic Usage

```python
from parser import Parser
from compiler import Compiler

parser = Parser()
compiler = Compiler()

code = """
// Simple program
x = 42;
print x;
"""

# Parse to AST
ast = parser.parse(code)
print(ast)

# Compile to assembly
asm = compiler.compile(ast)
print(asm)
```

## Compiling and Running

The compiler generates x86-64 Linux assembly that can be assembled and linked using Docker.

### Quick Start

1. **Build the Docker image:**
```bash
make build-docker
```

2. **Compile and assemble an example:**
```bash
make build              # Compiles examples/arithmetic.toy
```

3. **Run the executable:**
```bash
make run                # Runs build/arithmetic
```

### Detailed Workflow

**Option 1: Using Makefile (Recommended)**

```bash
# Compile a specific file
make compile FILE=examples/hello.toy NAME=hello

# Run the compiled program
make run NAME=hello

# Clean build artifacts
make clean

# Open interactive Docker shell for debugging
make shell
```

**Option 2: Using compile.sh directly**

```bash
# Build Docker image first
docker build -t toy-compiler .

# Compile only
docker run --rm -v $(pwd):/workspace toy-compiler \
  ./compile.sh examples/arithmetic.toy arithmetic

# Compile and run
docker run --rm -v $(pwd):/workspace toy-compiler \
  ./compile.sh examples/arithmetic.toy arithmetic --run

# Compile, run, and test against expected output
docker run --rm -v $(pwd):/workspace toy-compiler \
  ./compile.sh examples/arithmetic.toy arithmetic --test
```

**Option 3: Manual steps**

```bash
# 1. Generate assembly from toy source
python3 -c "
from src.parser import Parser
from src.compiler import Compiler

with open('examples/arithmetic.toy', 'r') as f:
    source = f.read()

ast = Parser().parse(source)
asm = Compiler().compile(ast)

with open('build/program.asm', 'w') as f:
    f.write(asm)
"

# 2. Assemble with NASM (in Docker)
docker run --rm -v $(pwd):/workspace toy-compiler \
  nasm -f elf64 build/program.asm -o build/program.o

# 3. Link with ld (in Docker)
docker run --rm -v $(pwd):/workspace toy-compiler \
  ld build/program.o -o build/program

# 4. Run the executable (in Docker)
docker run --rm -v $(pwd):/workspace toy-compiler \
  build/program
```

### Understanding the Build Process

1. **Compile**: Python reads `.toy` source → generates `.asm` assembly
2. **Assemble**: NASM converts `.asm` → `.o` object file (ELF64 format)
3. **Link**: ld links object file → executable binary
4. **Run**: Execute the binary in Linux environment (Docker)

## Testing

The project includes automated testing support via `.expected` files that contain the expected output for each example program.

### Running Tests

```bash
# Test a single example
docker run --rm -v $(pwd):/workspace toy-compiler \
  ./compile.sh examples/hello.toy hello --test

# Test all examples (you can create a script for this)
for example in examples/*.toy; do
  name=$(basename "$example" .toy)
  docker run --rm -v $(pwd):/workspace toy-compiler \
    ./compile.sh "$example" "$name" --test
done
```

### How Testing Works

1. The `--test` flag compiles and runs the program
2. Captures the actual output
3. Compares it with the corresponding `.expected` file
4. Reports `✓ TEST PASSED` or `✗ TEST FAILED` with a diff

### Adding New Test Cases

To add a new test case:

1. Create your `.toy` source file in `examples/`
2. Run the program and verify the output is correct
3. Save the expected output to `examples/yourfile.expected`
4. Run with `--test` flag to validate

Example:
```bash
# Create the expected output file
echo "42" > examples/mynew.expected

# Test it
./compile.sh examples/mynew.toy mynew --test
```

## Example Programs

The `examples/` directory contains several programs demonstrating language features:

- **hello.toy**: Simple variable assignment and print
- **arithmetic.toy**: Arithmetic operations with operator precedence
- **test.toy**: Variable reassignment
- **conditional.toy**: If/else statements with truthy/falsy conditions
- **loop.toy**: While loops including nested loops
- **comparisons.toy**: All comparison operators (`==`, `!=`, `<`, `<=`, `>`, `>=`)
- **comprehensive.toy**: Complete feature showcase with nested loops, conditionals, comparisons, and arithmetic

Each example has a corresponding `.expected` file for automated testing.

## Requirements

- **Docker**: Required for assembly and linking (NASM + binutils)
- **Python 3.10+**: For the compiler itself (uses match/case syntax)
- **Make**: Optional, for convenient commands

The generated assembly targets **Linux x86-64** with direct syscalls, so it must run in a Linux environment (provided by Docker).
