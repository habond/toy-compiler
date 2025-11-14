; lib/printf.asm - Minimal printf implementation for toy compiler
; Exports: print_int, print_newline

section .data
    newline db 10           ; newline character

section .bss
    digit_buffer resb 20    ; buffer for converting integer to string

section .text
    global print_int
    global print_newline

; print_int - Print a signed integer to stdout
; Arguments:
;   rdi = integer to print
; Returns: nothing
; Clobbers: rax, rcx, rdx, rsi, rdi, r8, r9
print_int:
    push rbp
    mov rbp, rsp

    ; Handle negative numbers
    mov rax, rdi            ; rax = number to print
    test rax, rax
    jns .positive           ; if non-negative, skip

    ; Print minus sign
    push rax                ; save number
    mov rax, 1              ; sys_write
    mov rdi, 1              ; stdout
    mov rsi, minus_sign
    mov rdx, 1              ; length
    syscall
    pop rax                 ; restore number
    neg rax                 ; make positive

.positive:
    ; Convert integer to string (in reverse)
    mov rcx, 0              ; digit counter
    mov r8, 10              ; divisor
    lea r9, [rel digit_buffer]

    ; Special case: if number is 0
    test rax, rax
    jnz .convert_loop
    mov byte [r9], '0'
    inc rcx
    jmp .print_digits

.convert_loop:
    test rax, rax
    jz .print_digits

    xor rdx, rdx            ; clear rdx for division
    div r8                  ; rax = rax / 10, rdx = rax % 10

    add dl, '0'             ; convert digit to ASCII
    mov [r9 + rcx], dl      ; store digit
    inc rcx

    jmp .convert_loop

.print_digits:
    ; Print digits in reverse order
    test rcx, rcx
    jz .done

.print_loop:
    dec rcx
    lea rsi, [r9 + rcx]     ; pointer to current digit

    push rcx                ; save counter (syscall clobbers rcx)
    mov rax, 1              ; sys_write
    mov rdi, 1              ; stdout
    mov rdx, 1              ; length = 1
    syscall
    pop rcx                 ; restore counter

    test rcx, rcx           ; check if more digits
    jnz .print_loop

.done:
    pop rbp
    ret

; print_newline - Print a newline character to stdout
; Arguments: none
; Returns: nothing
; Clobbers: rax, rdi, rsi, rdx
print_newline:
    mov rax, 1              ; sys_write
    mov rdi, 1              ; stdout
    lea rsi, [rel newline]
    mov rdx, 1              ; length = 1
    syscall
    ret

section .data
    minus_sign db '-'
