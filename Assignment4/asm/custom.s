#==========================================================================
#
#   The PyRISC Project
#
#   fib.s: Computes fibonacci numbers recursively
#
#   Jin-Soo Kim
#   Systems Software and Architecture Laboratory
#   Seoul National University
#   http://csl.snu.ac.kr
#
#==========================================================================


# The following sample code computes the Fibonnaci number given by:
#   fib(n) = fib(n-1) + fib(n-2)        (if n > 1)
#          = 1                          (if n <= 1)
# After completing the execution of this program, the a0 register should
# have the value fib(3) = 3.
# 1 1 2 3 5 8


    .text
    .align  2
    .globl  _start
_start:                         # code entry point
    lui     sp, 0x80020         # set the stack pointer to 0x80020000
    #li      a0, 1             # set the argument
    #push    a0                # 1
    #li      a1, 2
    #push    a1                # 1 2
    #li      a2, 3
    #push    a2                # 1 2 3
    #lw      t0, 0(sp)         # 3
    #addi    t1, t0, 5         # 8
    #push    t1                # 1 2 3 8
    #pop     t2                # 8
    #addi    t3, t2, 1         # 9
    push     sp
    push     sp
    push     sp
    push     sp
    #pop      a0
    ebreak


