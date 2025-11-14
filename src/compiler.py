"""Compiler for the toy language."""

from textwrap import dedent
from ast_nodes import *
from ast_walker import collect_variables


# Assembly Templates
ASM_HEADER = """
section .text
global _start
extern print_int
extern print_newline

_start:
"""

ASM_VAR_ALLOC = """
; Allocate space for variables: {vars}
sub rsp, {byte_count}         ; Allocate {byte_count} bytes ({var_count} qwords)
mov rbp, rsp        ; rbp = base pointer to variable area (fixed)
"""

ASM_VAR_DEALLOC = """
; Clean up stack
add rsp, {byte_count}         ; Deallocate stack space

; Exit
mov rdi, 0          ; exit status 0
mov rax, 60         ; sys_exit
syscall
"""

ASM_ASSIGNMENT = """
pop rax
mov qword [rbp+{offset}], rax
"""

ASM_PRINT = """
pop rdi
call print_int
call print_newline
"""

ASM_PUSH_NUMBER = "push qword {num}"

ASM_PUSH_VAR = "push qword [rbp+{offset}]"

ASM_BINOP_ADD = """
pop rbx
pop rax
add rax, rbx
push qword rax
"""

ASM_BINOP_SUB = """
pop rbx
pop rax
sub rax, rbx
push qword rax
"""

ASM_BINOP_MUL = """
pop rbx
pop rax
imul rax, rbx
push qword rax
"""

ASM_BINOP_DIV = """
pop rbx
pop rax
cqo
idiv rbx
push qword rax
"""

ASM_IF = """
pop rax
cmp rax, 0
je {else_label}
"""

ASM_WHILE = """
pop rax
cmp rax, 0
je {done_label}
"""

class Compiler:
    code: list[str]
    label_counter: int

    def __init__(self):
        self.code = []
        self.label_counter = 0

    def fresh_label(self, prefix: str = "L") -> str:
        label = f"{prefix}.{self.label_counter}"
        self.label_counter += 1
        return label

    def fresh_label_group(self, *prefixes: str) -> tuple[str, ...]:
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
        vars = collect_variables(program)
        var_count = len(vars)
        byte_count = var_count * 8
        var_offsets = {var:(idx*8) for (idx, var) in enumerate(vars)}

        # Emit program header
        self.emit_raw(ASM_HEADER)
        self.emit("")

        # Emit variable layout comments
        self.emit("; Variable layout (fixed offsets from rbp):")
        for var, offset in var_offsets.items():
            self.emit(f"; [rbp+{offset}] = {var}")
        self.emit("")

        # Emit variable allocation
        self.emit(ASM_VAR_ALLOC.format(
            vars=", ".join(vars),
            byte_count=byte_count,
            var_count=var_count
        ))
        self.emit("")

        # Emit statements
        for statement in program.statements:
            self.statement(statement, var_offsets)
            self.emit("")

        # Emit cleanup and exit
        self.emit(ASM_VAR_DEALLOC.format(byte_count=byte_count))

    def statement(self, statement: Statement, var_offsets: dict[str, int]) -> None:
        self.emit(f"; {statement}")
        match statement:
            case Assignment(name, expr):
                self.expr(expr, var_offsets)
                offset = var_offsets[name]
                self.emit(ASM_ASSIGNMENT.format(offset=offset))

            case IfStmt(condition, then_body, else_body):
                if_label, else_label, fi_label = self.fresh_label_group("if", "else", "fi")
                self.emit_raw(f"{if_label}:")
                self.expr(condition, var_offsets)

                if else_body:
                    self.emit(ASM_IF.format(else_label=else_label))
                    for statement in then_body:
                        self.statement(statement, var_offsets)
                    self.emit(f"jmp {fi_label}")
                    self.emit_raw(f"{else_label}:")
                    for statement in else_body:
                        self.statement(statement, var_offsets)
                else:
                    self.emit(ASM_IF.format(else_label=fi_label))
                    for statement in then_body:
                        self.statement(statement, var_offsets)
                    
                self.emit_raw(f"{fi_label}:")

            case WhileLoop(condition, body):
                while_label, done_label = self.fresh_label_group("while", "done")
                self.emit_raw(f"{while_label}:")
                self.expr(condition, var_offsets)
                self.emit(ASM_WHILE.format(done_label=done_label))
                for statement in body:
                    self.statement(statement, var_offsets)
                self.emit(f"jmp {while_label}")
                self.emit_raw(f"{done_label}:")
            
            case Print(expr):
                self.expr(expr, var_offsets)
                self.emit(ASM_PRINT)

            case other:
                raise ValueError(f"Unexpected statement '{type(other).__name__}'")
    
    def expr(self, expr: Expr, var_offsets: dict[str, int]) -> None:
        match expr:
            case Number(num):
                self.emit(ASM_PUSH_NUMBER.format(num=num))

            case Var(name):
                offset = var_offsets[name]
                self.emit(ASM_PUSH_VAR.format(offset=offset))

            case BinOp(op, left, right):
                self.expr(left, var_offsets)
                self.expr(right, var_offsets)
                match op:
                    case '+':
                        self.emit(ASM_BINOP_ADD)
                    case '-':
                        self.emit(ASM_BINOP_SUB)
                    case '*':
                        self.emit(ASM_BINOP_MUL)
                    case '/':
                        self.emit(ASM_BINOP_DIV)
                    case other:
                        raise ValueError(f"Unexpected operator '{other}'")
            
            case other:
                raise ValueError(f"Unexpected expr '{type(other).__name__}'")
