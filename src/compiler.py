"""Compiler for the toy language.

This module provides a compiler that translates toy language AST nodes into x86-64 assembly.
The compiler uses a stack-based approach for expression evaluation and maintains frame
pointers for variable management across nested scopes (main program and subroutines).

The generated assembly follows the System V AMD64 ABI calling convention.
"""

from textwrap import dedent
from src.ast_nodes import *
from src.var_utils import collect_program_variables, collect_subroutine_local_variables


# Assembly Templates
# These templates are formatted strings that generate x86-64 assembly code
ASM_HEADER = """
section .text
global _start
extern print_int
extern print_newline

_start:
"""

ASM_FRAME_SETUP = """
; Set up stack frame
push rbp            ; Save caller's frame pointer
mov rbp, rsp        ; Establish new frame pointer
"""

ASM_VAR_ALLOC = """
; Allocate space for variables: {vars}
sub rsp, {byte_count}         ; Reserve {byte_count} bytes ({var_count} qwords) on stack
"""

ASM_VAR_DEALLOC = """
; Clean up and exit program
mov rsp, rbp        ; Restore stack pointer to frame base
pop rbp             ; Restore base pointer

; Exit program
mov rdi, 0          ; Exit status 0 (success)
mov rax, 60         ; System call number for exit
syscall             ; Invoke kernel to exit
"""

ASM_ASSIGNMENT = """
pop rax
mov qword [rbp{offset:+d}], rax
"""

ASM_PRINT = """
pop rdi
call print_int
call print_newline
"""

ASM_PUSH_NUMBER = "push qword {num}"

ASM_PUSH_VAR = "push qword [rbp{offset:+d}]"

ASM_BINOP_ADD = """
; Addition operation
pop rbx             ; Second operand
pop rax             ; First operand
add rax, rbx        ; rax = rax + rbx
push qword rax      ; Push result
"""

ASM_BINOP_SUB = """
; Subtraction operation
pop rbx             ; Second operand (subtrahend)
pop rax             ; First operand (minuend)
sub rax, rbx        ; rax = rax - rbx
push qword rax      ; Push result
"""

ASM_BINOP_MUL = """
; Multiplication operation
pop rbx             ; Second operand
pop rax             ; First operand
imul rax, rbx       ; rax = rax * rbx (signed multiply)
push qword rax      ; Push result
"""

ASM_BINOP_DIV = """
; Division operation
pop rbx             ; Divisor
pop rax             ; Dividend
cqo                 ; Sign-extend rax into rdx:rax
idiv rbx            ; rax = rdx:rax / rbx (signed divide), rdx = remainder
push qword rax      ; Push quotient
"""

ASM_BINOP_CMP = """
; Comparison operation
pop rbx             ; Second operand
pop rax             ; First operand
cmp rax, rbx        ; Compare rax with rbx (sets flags)
set{condition} al   ; Set al to 1 if condition true, 0 otherwise
movzx rax, al       ; Zero-extend al to rax (result is 0 or 1)
push qword rax      ; Push boolean result as integer
"""

ASM_CONDITION_CHECK = """
; Conditional branch
pop rax             ; Get condition value
cmp rax, 0          ; Test if false (zero)
je {label}          ; Jump if zero (false condition)
"""

ASM_RETURN = """
; Return from subroutine with value
pop rax             ; Get return value into rax register
mov rsp, rbp        ; Restore stack pointer
pop rbp             ; Restore caller's frame pointer
ret                 ; Return to caller
"""

ASM_IMPLICIT_RETURN = """
; Implicit return (no explicit return statement)
mov rsp, rbp        ; Restore stack pointer
pop rbp             ; Restore caller's frame pointer
ret                 ; Return to caller
"""

ASM_CALL_SUB = """
call sub_{name}.start       ; Call subroutine
add rsp, {byte_count}       ; Clean up {byte_count} bytes of arguments from stack
push qword rax              ; Save return value on stack
"""

ASM_DISCARD_RETURN = "pop rax             ; Discard unused return value"

ASM_JMP = "jmp {label}"

ASM_LABEL = "{label}:"

# Constants for stack layout
BYTES_PER_QWORD = 8  # Each 64-bit value occupies 8 bytes on the stack
PARAM_OFFSET_START = 2  # Parameter indexing starts at 2 qwords (16 bytes) above rbp
                        # This skips: saved rbp (at rbp+0) and return address (at rbp+8)

# Mapping from comparison operators to x86 condition codes
# These are used with the SETcc instruction to convert comparison results to boolean values
COMPARISON_CONDITIONS = {
    '<=': 'le',  # Less than or Equal (signed)
    '<': 'l',    # Less than (signed)
    '==': 'e',   # Equal
    '!=': 'ne',  # Not Equal
    '>': 'g',    # Greater than (signed)
    '>=': 'ge'   # Greater than or Equal (signed)
}

@dataclass
class FrameMetadata:
    """Metadata for a single stack frame.

    Stores the mapping from variable names to their offsets from the frame pointer (rbp).
    Positive offsets indicate parameters (above rbp), while negative offsets indicate
    local variables (below rbp).
    """
    var_offsets: dict[str, int]  # Maps variable name to its rbp-relative offset


class Compiler:
    """Main compiler class for generating x86-64 assembly from toy language AST.

    The compiler maintains a stack of frame metadata to handle nested scopes (main program
    and subroutines), generates unique labels for control flow, and emits assembly code
    using a stack-based evaluation model.

    Attributes:
        code: List of assembly code lines generated during compilation
        label_counter: Counter for generating unique labels for branches and loops
        frame_metadata_stack: Stack of FrameMetadata for the current compilation context
    """
    code: list[str]
    label_counter: int
    frame_metadata_stack: list[FrameMetadata]

    def __init__(self):
        """Initialize the compiler with empty state."""
        self.code = []
        self.label_counter = 0
        self.frame_metadata_stack = []

    def get_current_frame(self) -> FrameMetadata:
        """Get the current stack frame metadata.

        Returns:
            The FrameMetadata for the innermost active scope (top of stack).
        """
        return self.frame_metadata_stack[-1]

    def get_var_offset(self, name: str) -> int:
        """Get the rbp-relative offset of a variable from the current frame.

        Args:
            name: The variable name to look up.

        Returns:
            The offset in bytes from rbp (negative for locals, positive for parameters).
        """
        return self.get_current_frame().var_offsets[name]

    def fresh_label_group(self, *prefixes: str) -> tuple[str, ...]:
        """Generate a group of unique labels with the given prefixes.

        Args:
            *prefixes: Variable number of label prefix strings.

        Returns:
            A tuple of unique labels, one for each prefix, sharing a counter value.

        Example:
            if_label, else_label, fi_label = self.fresh_label_group("if", "else", "fi")
            # Might produce: ("if.0", "else.0", "fi.0")
        """
        counter = self.label_counter
        self.label_counter += 1
        return tuple(f"{prefix}.{counter}" for prefix in prefixes)

    def compile(self, program: Program) -> str:
        """Compile a Program AST node into x86-64 assembly code.

        Args:
            program: The root AST node representing the entire program.

        Returns:
            A string containing the complete assembly program.
        """
        self.program(program)
        return '\n'.join(self.code)

    def emit(self, code: str, indent_level: int = 1) -> None:
        """Emit assembly code with automatic indentation.

        Args:
            code: The assembly code to emit (may be multiline).
            indent_level: Number of tab characters to prepend to each line.
        """
        for line in dedent(code).strip().split('\n'):
            if line.strip():  # Non-empty lines get indented
                self.code.append('\t' * indent_level + line)
            else:  # Empty lines stay empty
                self.code.append('')

    def emit_raw(self, code: str) -> None:
        """Emit assembly code without any indentation.

        Used for labels that must appear at column 0.

        Args:
            code: The assembly code to emit (labels, directives, etc.).
        """
        self.code.append(dedent(code).strip())

    def program(self, program: Program) -> None:
        """Compile the main program (entry point).

        This method:
        1. Collects all variables used in the main program scope
        2. Sets up the stack frame with variable storage
        3. Compiles all top-level items (statements and subroutine definitions)
        4. Generates cleanup code and program exit

        Args:
            program: The Program AST node containing top-level items.
        """
        # Collect all variables that will be used in the main program scope
        vars = collect_program_variables(program)
        var_count = len(vars)
        byte_count = var_count * BYTES_PER_QWORD

        # Calculate stack offsets for each variable (negative offsets = below rbp)
        # Variables are indexed: rbp-8, rbp-16, rbp-24, etc.
        var_offsets = {var:(-((idx+1)*BYTES_PER_QWORD)) for (idx, var) in enumerate(vars)}

        # Create frame metadata and push onto stack (this is the main program's frame)
        frame_metadata = FrameMetadata(var_offsets)
        self.frame_metadata_stack.append(frame_metadata)

        # Emit program header (section declaration, entry point, external references)
        self.emit_raw(ASM_HEADER)
        self.emit("")

        # Set up stack frame pointer for the main program
        self.emit(ASM_FRAME_SETUP)
        self.emit("")

        # Emit variable layout comments for debugging and clarity
        self.emit("; Variable layout (fixed offsets from rbp):")
        for var, offset in var_offsets.items():
            self.emit(f"; [rbp{offset:+d}] = {var}")
        self.emit("")

        # Allocate stack space for all main program variables
        self.emit(ASM_VAR_ALLOC.format(
            vars=", ".join(vars),
            byte_count=byte_count,
            var_count=var_count
        ))
        self.emit("")

        # Emit statements and subroutines
        # Subroutine definitions are compiled inline (with jump-over logic)
        # Statements are executed in the main program flow
        for item in program.top_level:
            match item:
                case SubroutineDef():
                    self.compile_subroutine(item)
                case Statement():
                    self.statement(item)
                    self.emit("")

        # Emit cleanup and exit: restore stack and terminate process
        self.emit(ASM_VAR_DEALLOC.format(byte_count=byte_count))

    def compile_subroutine(self, subroutine: SubroutineDef) -> None:
        """Compile a subroutine definition.

        Subroutines are compiled inline but with a jump-over wrapper so they don't
        execute during normal program flow. They're only executed when called.

        Stack layout for subroutines:
            [rbp+24] - third parameter
            [rbp+16] - second parameter
            [rbp+8]  - return address (pushed by CALL)
            [rbp+0]  - saved rbp (pushed by this function)
            [rbp-8]  - first local variable
            [rbp-16] - second local variable
            ...

        Args:
            subroutine: The SubroutineDef AST node to compile.
        """
        name = subroutine.name
        params = subroutine.params
        body = subroutine.body

        # Generate labels for subroutine entry and skip-over jump
        sub_start, sub_end = f"sub_{name}.start", f"sub_{name}.end"

        # Collect local variables declared within the subroutine (parameters excluded)
        body_vars = collect_subroutine_local_variables(subroutine)

        # Calculate offsets for parameters (positive offsets, above rbp)
        # First parameter is at rbp+16, second at rbp+24, etc.
        param_offsets = {var:((idx+PARAM_OFFSET_START)*BYTES_PER_QWORD) for (idx, var) in enumerate(params)}

        # Calculate offsets for local variables (negative offsets, below rbp)
        # First local at rbp-8, second at rbp-16, etc.
        local_offsets = {var:(-((idx+1)*BYTES_PER_QWORD)) for (idx, var) in enumerate(body_vars)}
        local_var_count = len(local_offsets)
        local_byte_count = local_var_count * BYTES_PER_QWORD

        # Combine parameter and local variable offsets into one mapping
        subroutine_var_offsets = param_offsets | local_offsets

        # Push new frame metadata onto stack (subroutine has its own scope)
        frame_metadata = FrameMetadata(subroutine_var_offsets)
        self.frame_metadata_stack.append(frame_metadata)

        # Emit subroutine header with jump-over to prevent inline execution
        self.emit("")
        self.emit(f"; ===== Subroutine: {name} =====")
        self.emit(ASM_JMP.format(label=sub_end))  # Skip over subroutine during main flow
        self.emit_raw(ASM_LABEL.format(label=sub_start))  # Entry point for CALL instruction

        # Set up stack frame (save caller's rbp, establish new frame)
        self.emit(ASM_FRAME_SETUP)
        self.emit("")

        # Emit variable layout comments for debugging
        self.emit("; Subroutine stack layout (from high to low addresses):")

        # Show parameters (positive offsets)
        if params:
            for var, offset in sorted([(v, o) for v, o in param_offsets.items()], key=lambda x: -x[1]):
                self.emit(f";   [rbp{offset:+d}] = {var}")

        # Show call frame (fixed locations)
        self.emit(";   [rbp+8] = return address (pushed by CALL)")
        self.emit(";   [rbp+0] = saved caller's rbp")

        # Show local variables (negative offsets)
        if body_vars:
            for var, offset in sorted([(v, o) for v, o in local_offsets.items()], key=lambda x: -x[1]):
                self.emit(f";   [rbp{offset:+d}] = {var}")

        # Allocate stack space for local variables only (parameters already on stack)
        self.emit(ASM_VAR_ALLOC.format(
            vars=", ".join(body_vars),
            byte_count=local_byte_count,
            var_count=local_var_count
        ))
        self.emit("")

        # Compile subroutine body statements
        for statement in body:
            self.statement(statement)

        # Add implicit return for subroutines that don't have explicit return statement
        # This ensures proper cleanup even if control reaches end of subroutine
        self.emit(ASM_IMPLICIT_RETURN)

        # Emit subroutine footer and skip-over target label
        self.emit("")
        self.emit(f"; ===== End of {name} =====")
        self.emit_raw(ASM_LABEL.format(label=sub_end))  # Jump target for skip-over

        # Pop frame metadata (return to caller's scope)
        self.frame_metadata_stack.pop()
        self.emit("")

    def statement(self, statement: Statement) -> None:
        """Compile a statement.

        Statements are compiled based on their type using pattern matching.
        Each statement type generates appropriate assembly code.

        Args:
            statement: The Statement AST node to compile.

        Raises:
            ValueError: If an unknown statement type is encountered.
        """
        self.emit("")
        self.emit(f"; {statement}")  # Emit source statement as comment for readability

        match statement:
            case Assignment(name, expr):
                # Evaluate expression (result left on stack)
                self.expr(expr)
                # Pop result and store in variable's memory location
                offset = self.get_var_offset(name)
                self.emit(ASM_ASSIGNMENT.format(offset=offset))
                self.emit("")

            case IfStmt(condition, then_body, else_body):
                # Generate unique labels for if/else/fi branches
                if_label, else_label, fi_label = self.fresh_label_group("if", "else", "fi")
                self.emit("; If statement")
                self.emit_raw(ASM_LABEL.format(label=if_label))

                # Evaluate condition (result left on stack as 0 or 1)
                self.expr(condition)
                self.emit("")

                if else_body:
                    # If-else: jump to else if condition is false
                    self.emit(ASM_CONDITION_CHECK.format(label=else_label))
                    # Compile then branch
                    for statement in then_body:
                        self.statement(statement)
                    # Jump past else branch after completing then branch
                    self.emit(ASM_JMP.format(label=fi_label))
                    # Compile else branch
                    self.emit("; Else branch")
                    self.emit_raw(ASM_LABEL.format(label=else_label))
                    for statement in else_body:
                        self.statement(statement)
                else:
                    # If-only: jump to end if condition is false
                    self.emit(ASM_CONDITION_CHECK.format(label=fi_label))
                    # Compile then branch
                    for statement in then_body:
                        self.statement(statement)

                # End of if statement
                self.emit("; End if")
                self.emit_raw(ASM_LABEL.format(label=fi_label))

            case WhileLoop(condition, body):
                # Generate unique labels for loop start and exit
                while_label, done_label = self.fresh_label_group("while", "done")
                self.emit("; While loop")

                # Loop entry point (condition check)
                self.emit_raw(ASM_LABEL.format(label=while_label))
                self.expr(condition)
                self.emit("")

                # Exit loop if condition is false
                self.emit(ASM_CONDITION_CHECK.format(label=done_label))

                # Compile loop body
                for statement in body:
                    self.statement(statement)

                # Jump back to condition check
                self.emit(ASM_JMP.format(label=while_label))

                # Loop exit point
                self.emit("; End while")
                self.emit_raw(ASM_LABEL.format(label=done_label))

            case Print(expr):
                # Evaluate expression and print result
                self.expr(expr)
                self.emit(ASM_PRINT)

            case ReturnStmt(expr):
                # Evaluate return expression and return from subroutine
                self.expr(expr)
                self.emit(ASM_RETURN)

            case CallStmt(expr):
                # Call subroutine expression (result pushed to stack)
                self.expr(expr)
                # Discard the return value since this is a statement, not expression
                self.emit(ASM_DISCARD_RETURN)

            case other:
                raise ValueError(f"Unexpected statement '{type(other).__name__}'")
    
    def expr(self, expr: Expr) -> None:
        """Compile an expression.

        Expressions are compiled using a stack-based approach: operands are pushed
        onto the stack, operators consume operands and push results. The final
        result is always left on top of the stack.

        Args:
            expr: The Expr AST node to compile.

        Raises:
            ValueError: If an unknown expression or operator type is encountered.
        """
        match expr:
            case Number(num):
                # Push literal number onto stack
                self.emit(ASM_PUSH_NUMBER.format(num=num))

            case Var(name):
                # Look up variable's offset and push its value onto stack
                offset = self.get_var_offset(name)
                self.emit(ASM_PUSH_VAR.format(offset=offset))

            case BinOp(op, left, right):
                # Evaluate left operand (result on stack)
                self.expr(left)
                # Evaluate right operand (result on stack)
                self.expr(right)

                # Apply operator: pops operands, pushes result
                match op:
                    case '+':
                        self.emit(ASM_BINOP_ADD)
                    case '-':
                        self.emit(ASM_BINOP_SUB)
                    case '*':
                        self.emit(ASM_BINOP_MUL)
                    case '/':
                        self.emit(ASM_BINOP_DIV)
                    case _ if op in COMPARISON_CONDITIONS:
                        # Comparison operators produce boolean results (0 or 1)
                        self.emit(ASM_BINOP_CMP.format(condition=COMPARISON_CONDITIONS[op]))
                    case other:
                        raise ValueError(f"Unexpected operator '{other}'")

            case Call(name, args):
                # Push arguments in reverse order (rightmost first)
                # This ensures correct left-to-right parameter ordering on stack
                for arg in reversed(args):
                    self.expr(arg)

                # Call subroutine and clean up arguments from stack
                # Result is placed in rax and then pushed onto stack
                self.emit(ASM_CALL_SUB.format(name=name, byte_count=len(args) * 8))

            case other:
                raise ValueError(f"Unexpected expr '{type(other).__name__}'")
