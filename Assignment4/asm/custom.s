#==========================================================================
#
#   Project #4: Extending a 5-stage Pipelined RISC-V Processor
#
#   November 28, 2022
# 
#   Seongyeop Jeong (seongyeop.jeong@snu.ac.kr)
#   Jaehoon Shim (mattjs@snu.ac.kr)
#   IlKueon Kang (kangilkueon@snu.ac.kr)
#   Wookje Han (gksdnrwp@snu.ac.kr)
#   Jinsol Park (jinsolpark@snu.ac.kr)
#
#   Systems Software & Architecture Laboratory
#   Dept. of Computer Science and Engineering
#   Seoul National University
#
#==========================================================================

# Custom: For test push and pop without forwarding

    .text
    .align  2
    .globl  _start
_start:                         # code entry point
    lui     sp, 0x80020
    addi    t0, x0, 1
    addi    t1, x0, 2
    addi    t2, x0, 3
    addi    t3, t2, 4
    add     t4, t3, t2
    ebreak
    


