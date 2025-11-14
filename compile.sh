#!/bin/sh
# compile.sh - Compile toy language source to executable binary
# Usage: ./compile.sh <source_file> [output_name] [--run] [--test]
#
# This script:
# 1. Compiles toy source to assembly using compiler.py
# 2. Assembles the .asm file to object file using NASM
# 3. Links the object file to executable using ld
# 4. Optionally runs the executable if --run flag is provided
# 5. Optionally tests output against .expected file if --test flag is provided

set -e  # Exit on error

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <source_file> [output_name] [--run] [--test]"
    echo "Example: $0 examples/test.toy program"
    echo "Example: $0 examples/test.toy program --run"
    echo "Example: $0 examples/test.toy program --test"
    exit 1
fi

SOURCE_FILE="$1"
OUTPUT_NAME="${2:-program}"
RUN_FLAG=""
TEST_FLAG=""

# Check for --run and --test flags in any position
for arg in "$@"; do
    if [ "$arg" = "--run" ]; then
        RUN_FLAG="yes"
    fi
    if [ "$arg" = "--test" ]; then
        TEST_FLAG="yes"
    fi
done

# Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: Source file '$SOURCE_FILE' not found"
    exit 1
fi

# Create build directory if it doesn't exist
mkdir -p build

ASM_FILE="build/${OUTPUT_NAME}.asm"
OBJ_FILE="build/${OUTPUT_NAME}.o"
EXEC_FILE="build/${OUTPUT_NAME}"

echo "==> Step 1: Compiling toy source to assembly..."
python3 src/cli.py "$SOURCE_FILE" "$ASM_FILE"

echo "==> Step 2: Assembling with NASM..."
nasm -f elf64 "$ASM_FILE" -o "$OBJ_FILE"
echo "Generated: $OBJ_FILE"

# Assemble printf library if it exists
PRINTF_OBJ=""
if [ -f "lib/printf.asm" ]; then
    echo "==> Step 2b: Assembling lib/printf.asm..."
    nasm -f elf64 lib/printf.asm -o build/printf.o
    echo "Generated: build/printf.o"
    PRINTF_OBJ="build/printf.o"
fi

echo "==> Step 3: Linking with ld..."
ld "$OBJ_FILE" $PRINTF_OBJ -o "$EXEC_FILE"
echo "Generated: $EXEC_FILE"

echo ""
echo "Success! Executable created at: $EXEC_FILE"

# Run the executable if --run or --test flag was provided
if [ -n "$RUN_FLAG" ] || [ -n "$TEST_FLAG" ]; then
    echo ""
    echo "==> Running $EXEC_FILE..."
    set +e  # Disable exit on error to capture exit code
    ACTUAL_OUTPUT=$($EXEC_FILE)
    EXIT_CODE=$?
    set -e  # Re-enable exit on error

    # Print output
    echo "$ACTUAL_OUTPUT"
    echo "Exit code: $EXIT_CODE"

    # If --test flag was provided, compare with expected output
    if [ -n "$TEST_FLAG" ]; then
        # Derive expected file from source file
        EXPECTED_FILE="${SOURCE_FILE%.toy}.expected"

        if [ ! -f "$EXPECTED_FILE" ]; then
            echo ""
            echo "WARNING: Expected output file not found: $EXPECTED_FILE"
            echo "Create this file with the expected output to enable testing."
            exit 1
        fi

        echo ""
        echo "==> Testing output..."
        EXPECTED_OUTPUT=$(cat "$EXPECTED_FILE")

        if [ "$ACTUAL_OUTPUT" = "$EXPECTED_OUTPUT" ]; then
            echo "✓ TEST PASSED: Output matches expected"
            exit 0
        else
            echo "✗ TEST FAILED: Output does not match expected"
            echo ""
            echo "Expected:"
            echo "$EXPECTED_OUTPUT"
            echo ""
            echo "Actual:"
            echo "$ACTUAL_OUTPUT"
            exit 1
        fi
    fi
else
    echo "Run with: $EXEC_FILE"
    echo "Or in Docker: docker run --rm -v \$(pwd):/workspace toy-compiler $EXEC_FILE"
fi
