"""Compiler for the toy language."""

from textwrap import dedent
from src.ast_nodes import *
from src.var_utils import collect_program_variables, collect_subroutine_local_variables


# Assembly Templates
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
BYTES_PER_QWORD = 8
PARAM_OFFSET_START = 2  # Skip saved rbp (at rbp+0) and return address (at rbp+8)

# Mapping from comparison operators to x86 condition codes
COMPARISON_CONDITIONS = {
    '<=': 'le',
    '<': 'l',
    '==': 'e',
    '!=': 'ne',
    '>': 'g',
    '>=': 'ge'
}

@dataclass
class FrameMetadata:
    var_offsets: dict[str, int]


class Compiler:
    code: list[str]
    label_counter: int
    frame_metadata_stack: list[FrameMetadata]

    def __init__(self):
        self.code = []
        self.label_counter = 0
        self.frame_metadata_stack = []

    def get_current_frame(self) -> FrameMetadata:
        """Get the current stack frame metadata."""
        return self.frame_metadata_stack[-1]

    def get_var_offset(self, name: str) -> int:
        """Get the offset of a variable from the current frame."""
        return self.get_current_frame().var_offsets[name]

    def fresh_label_group(self, *prefixes: str) -> tuple[str, ...]:
        """Generate a group of unique labels with the given prefixes."""
        counter = self.label_counter
        self.label_counter += 1
        return tuple(f"{prefix}.{counter}" for prefix in prefixes)

    def compile(self, program: Program) -> str:
        self.program(program)
        return '\n'.join(self.code)

    def emit(self, code: str, indent_level: int = 1) -> None:
        for line in dedent(code).strip().split('\n'):
            if line.strip():  # Non-empty lines get indented
                self.code.append('\t' * indent_level + line)
            else:  # Empty lines stay empty
                self.code.append('')

    def emit_raw(self, code: str) -> None:
        self.code.append(dedent(code).strip())

    def program(self, program: Program) -> None:
        vars = collect_program_variables(program)
        var_count = len(vars)
        byte_count = var_count * BYTES_PER_QWORD
        var_offsets = {var:(-((idx+1)*BYTES_PER_QWORD)) for (idx, var) in enumerate(vars)}
        frame_metadata = FrameMetadata(var_offsets)
        self.frame_metadata_stack.append(frame_metadata)

        # Emit program header
        self.emit_raw(ASM_HEADER)
        self.emit("")

        # Set up frame pointer
        self.emit(ASM_FRAME_SETUP)
        self.emit("")

        # Emit variable layout comments
        self.emit("; Variable layout (fixed offsets from rbp):")
        for var, offset in var_offsets.items():
            self.emit(f"; [rbp{offset:+d}] = {var}")
        self.emit("")

        # Emit variable allocation
        self.emit(ASM_VAR_ALLOC.format(
            vars=", ".join(vars),
            byte_count=byte_count,
            var_count=var_count
        ))
        self.emit("")

        # Emit statements and subroutines
        for item in program.top_level:
            match item:
                case SubroutineDef():
                    self.compile_subroutine(item)
                case Statement():
                    self.statement(item)
                    self.emit("")

        # Emit cleanup and exit
        self.emit(ASM_VAR_DEALLOC.format(byte_count=byte_count))

    def compile_subroutine(self, subroutine: SubroutineDef) -> None:
        """Compile a subroutine definition."""
        name = subroutine.name
        params = subroutine.params
        body = subroutine.body

        sub_start, sub_end = f"sub_{name}.start", f"sub_{name}.end"

        # Collect local variables (excluding parameters)
        body_vars = collect_subroutine_local_variables(subroutine)

        # Calculate offsets for parameters (positive, starting at rbp+16)
        param_offsets = {var:((idx+PARAM_OFFSET_START)*BYTES_PER_QWORD) for (idx, var) in enumerate(params)}
        # Calculate offsets for local variables (negative, starting at rbp-8)
        local_offsets = {var:(-((idx+1)*BYTES_PER_QWORD)) for (idx, var) in enumerate(body_vars)}
        local_var_count = len(local_offsets)
        local_byte_count = local_var_count * BYTES_PER_QWORD
        # Combine parameter and local variable offsets
        subroutine_var_offsets = param_offsets | local_offsets

        # Push new frame metadata onto stack
        frame_metadata = FrameMetadata(subroutine_var_offsets)
        self.frame_metadata_stack.append(frame_metadata)

        # Emit subroutine header and skip jump
        self.emit("")
        self.emit(f"; ===== Subroutine: {name} =====")
        self.emit(ASM_JMP.format(label=sub_end))
        self.emit_raw(ASM_LABEL.format(label=sub_start))

        # Set up stack frame
        self.emit(ASM_FRAME_SETUP)
        self.emit("")

        # Emit variable layout comments
        self.emit("; Subroutine variable layout (fixed offsets from rbp):")
        for var, offset in subroutine_var_offsets.items():
            self.emit(f"; [rbp{offset:+d}] = {var}")

        # Allocate space for local variables
        self.emit(ASM_VAR_ALLOC.format(
            vars=", ".join(body_vars),
            byte_count=local_byte_count,
            var_count=local_var_count
        ))
        self.emit("")

        # Compile subroutine body
        for statement in body:
            self.statement(statement)

        # Add implicit return for subroutines without explicit return
        self.emit(ASM_IMPLICIT_RETURN)

        # Emit subroutine footer
        self.emit("")
        self.emit(f"; ===== End of {name} =====")
        self.emit_raw(ASM_LABEL.format(label=sub_end))

        # Pop frame metadata
        self.frame_metadata_stack.pop()
        self.emit("")

    def statement(self, statement: Statement) -> None:
        self.emit("")
        self.emit(f"; {statement}")
        match statement:
            case Assignment(name, expr):
                self.expr(expr)
                offset = self.get_var_offset(name)
                self.emit(ASM_ASSIGNMENT.format(offset=offset))

            case IfStmt(condition, then_body, else_body):
                if_label, else_label, fi_label = self.fresh_label_group("if", "else", "fi")
                self.emit("; If statement")
                self.emit_raw(ASM_LABEL.format(label=if_label))
                self.expr(condition)
                self.emit("")

                if else_body:
                    self.emit(ASM_CONDITION_CHECK.format(label=else_label))
                    for statement in then_body:
                        self.statement(statement)
                    self.emit(ASM_JMP.format(label=fi_label))
                    self.emit("; Else branch")
                    self.emit_raw(ASM_LABEL.format(label=else_label))
                    for statement in else_body:
                        self.statement(statement)
                else:
                    self.emit(ASM_CONDITION_CHECK.format(label=fi_label))
                    for statement in then_body:
                        self.statement(statement)

                self.emit("; End if")
                self.emit_raw(ASM_LABEL.format(label=fi_label))

            case WhileLoop(condition, body):
                while_label, done_label = self.fresh_label_group("while", "done")
                self.emit("; While loop")
                self.emit_raw(ASM_LABEL.format(label=while_label))
                self.expr(condition)
                self.emit("")
                self.emit(ASM_CONDITION_CHECK.format(label=done_label))
                for statement in body:
                    self.statement(statement)
                self.emit(ASM_JMP.format(label=while_label))
                self.emit("; End while")
                self.emit_raw(ASM_LABEL.format(label=done_label))
            
            case Print(expr):
                self.expr(expr)
                self.emit(ASM_PRINT)

            case ReturnStmt(expr):
                self.expr(expr)
                self.emit(ASM_RETURN)

            case CallStmt(expr):
                self.expr(expr)
                self.emit(ASM_DISCARD_RETURN)  # Discard the pushed return value

            case other:
                raise ValueError(f"Unexpected statement '{type(other).__name__}'")
    
    def expr(self, expr: Expr) -> None:
        match expr:
            case Number(num):
                self.emit(ASM_PUSH_NUMBER.format(num=num))

            case Var(name):
                offset = self.get_var_offset(name)
                self.emit(ASM_PUSH_VAR.format(offset=offset))

            case BinOp(op, left, right):
                self.expr(left)
                self.expr(right)
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
                        self.emit(ASM_BINOP_CMP.format(condition=COMPARISON_CONDITIONS[op]))
                    case other:
                        raise ValueError(f"Unexpected operator '{other}'")

            case Call(name, args):
                for arg in reversed(args):
                    self.expr(arg)

                self.emit(ASM_CALL_SUB.format(name=name, byte_count=len(args) * 8))


            case other:
                raise ValueError(f"Unexpected expr '{type(other).__name__}'")
