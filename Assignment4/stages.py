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

import sys

from consts import *
from isa import *
from program import *
from pipe import *


#--------------------------------------------------------------------------
#   BTB: For Project #4
#--------------------------------------------------------------------------

class BTB(object):

    def __init__(self, k): # initialize your BTB here
        self.k = k # size = 2**k
        self.N = 2**k
        self.buffer = np.zeros((self.N, 3), int)
        # [Valid, Tag, Target Address]
        # N = 2**k entries

    # Lookup the entry corresponding to the pc
    # It will return the target address if there is a matching entry
    def lookup(self, pc):
        index = (pc>>2) % self.N
        tag = pc >> (self.k + 2)
        if self.buffer[index, 0] == 1 and self.buffer[index, 1] == tag:
            return self.buffer[index, 2]
        return False

    # Add an entry
    def add(self, pc, target):
        index = (pc >> 2) % self.N
        tag = pc >> (self.k + 2)
        self.buffer[index, 0] = 1 # valid
        self.buffer[index, 1] = tag
        self.buffer[index, 2] = target
        return

    # Make the corresponding entry invalid
    def remove(self, pc):
        index = (pc >> 2) % self.N
        tag = pc >> (self.k + 2)
        if self.buffer[index, 1] == tag: # entry exists
            self.buffer[index, 0] = 0 # make it invalid
        return



#--------------------------------------------------------------------------
#   Control signal table
#--------------------------------------------------------------------------

#--------------------------------------------------------------------------
# constants for additional control signals
SP_RF_INDEX = 2           # sp = RegisterFile[2]

OP1_SP = 3                # sp (stack pointer) as ALU operand 1
OP2_4 = 6                 # Immediate 4 as ALU operand 2
WB_POP = 3                # WriteBack ALU result and memory value both, only for POP instruction
WB_SP = 4                 # WriteBack sp, not rd
M_XPC = 2                 # memory load / address: sp, not alu result

CS_MAD_SEL = 12           # new control signal index: select DMEM address (alu result or sp)
MAD_ALU = 0
MAD_SP = 1                # only for POP instruction

CS_SP_OEN = 13            # SP enable signal : for forward detection

# TODO: add some control signals and make them work
#--------------------------------------------------------------------------

csignals = {
    LW     : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_ADD  , WB_MEM, REN_1, MEN_1, M_XRD, MT_W, MAD_ALU, OEN_0,],
    SW     : [ Y, BR_N  , OP1_RS1, OP2_IMS, OEN_1, OEN_1, ALU_ADD  , WB_X  , REN_0, MEN_1, M_XWR, MT_W, MAD_ALU, OEN_0,],
    AUIPC  : [ Y, BR_N  , OP1_PC,  OP2_IMU, OEN_0, OEN_0, ALU_ADD  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    LUI    : [ Y, BR_N  , OP1_X,   OP2_IMU, OEN_0, OEN_0, ALU_COPY2, WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    ADDI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_ADD  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    SLLI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SLL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SLTI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SLT  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SLTIU  : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SLTU , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    XORI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_XOR  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SRLI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SRL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    SRAI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SRA  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    ORI    : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_OR   , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    ANDI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_AND  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    ADD    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_ADD  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SUB    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SUB  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    SLL    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SLL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SLT    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SLT  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SLTU   : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SLTU , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    XOR    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_XOR  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    SRL    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SRL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    SRA    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SRA  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    OR     : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_OR   , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    AND    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_AND  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    JALR   : [ Y, BR_JR , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_ADD  , WB_PC4, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    JAL    : [ Y, BR_J  , OP1_X  , OP2_IMJ, OEN_0, OEN_0, ALU_X    , WB_PC4, REN_1, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    BEQ    : [ Y, BR_EQ , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SEQ  , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    BNE    : [ Y, BR_NE , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SEQ  , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    BLT    : [ Y, BR_LT , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLT  , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    BGE    : [ Y, BR_GE , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLT  , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    BLTU   : [ Y, BR_LTU, OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLTU , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    BGEU   : [ Y, BR_GEU, OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLTU , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    ECALL  : [ Y, BR_N  , OP1_X  , OP2_X  , OEN_0, OEN_0, ALU_X    , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],
    EBREAK : [ Y, BR_N  , OP1_X  , OP2_X  , OEN_0, OEN_0, ALU_X    , WB_X  , REN_0, MEN_0, M_X  , MT_X, MAD_ALU, OEN_0,],

    PUSH   : [ Y, BR_N  , OP1_SP , OP2_4  , OEN_0, OEN_1, ALU_SUB  , WB_SP , REN_1, MEN_1, M_XWR, MT_W, MAD_ALU, OEN_1,],
    POP    : [ Y, BR_N  , OP1_SP , OP2_4  , OEN_0, OEN_0, ALU_ADD  , WB_POP, REN_1, MEN_1, M_XRD, MT_W, MAD_SP,  OEN_1,],

    # Add entries for PUSH and POP instructions


}


#--------------------------------------------------------------------------
#   IF: Instruction fetch stage
#--------------------------------------------------------------------------

class IF(Pipe):

    # TODO: IF에 branch가 올 경우 predict한 값을 pipe reg로 가지고 있도록 수

    # Pipeline registers ------------------------------

    reg_pc          = WORD(0)       # IF.reg_pc
    reg_sp          = WORD(0)       # IF.reg_sp

    reg_br_pred_addr = WORD(0)

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.IF.pc
        #   self.inst               # Pipe.IF.inst
        #   self.exception          # Pipe.IF.exception
        #   self.pc_next            # Pipe.IF.pc_next
        #   self.pcplus4            # Pipe.IF.pcplus4
        #
        #   self.br_pred_addr
        #----------------------------------------------

    def compute(self):
        # Readout pipeline register values
        #if not Pipe.CTL.EX_mispredicted:
        self.pc = IF.reg_pc
        #else:
            #self.pc = Pipe.EX.br_true_addr


        # Fetch an instruction from instruction memory (imem)
        self.inst, status = Pipe.cpu.imem.access(Pipe.CTL.imem_en, self.pc, 0, Pipe.CTL.imem_rw)

        # Handle exception during imem access
        if not status:
            self.exception = EXC_IMEM_ERROR
            self.inst = BUBBLE
        else:
            self.exception = EXC_NONE

        # Compute PC + 4 using an adder
        self.pcplus4 = Pipe.cpu.adder_pcplus4.op(self.pc, 4)

        # Select next PC
        # TODO: jalr -> next fetching problematic

        if not Pipe.cpu.btb.lookup(self.pc):
            # IF stage instruction is not a branch instruction
            # or BTB predicts not-taken
            # this must be executed after update BTB in EX stage
            self.pc_next =  self.pcplus4            if Pipe.CTL.pc_sel == PC_4      else \
                            Pipe.EX.brjmp_target    if Pipe.CTL.pc_sel == PC_BRJMP  else \
                            Pipe.EX.jump_reg_target if Pipe.CTL.pc_sel == PC_JALR   else \
                            WORD(0)
            self.br_pred_addr = None
            # Pipe.CTL.pc_sel == PC_BRJMP, Pipe.CTL.pc_sel == PC_JAL
            # when branch is in EX stage, next pc will become computed (from EX) branch target
            # and makes bubble IF->ID, ID->EX instructions: Control() does

        else: # when branch is in IF stage, and BTB matches
            # TODO: mis-fetched
            self.pc_next = Pipe.cpu.btb.lookup(self.pc)
            self.br_pred_addr = self.pc_next
            # this may change in EX.update() if mis-predicted

            #self.pc_next =  Pipe.cpu.btb.lookup(self.pc) if Pipe.CTL.pc_sel == Pipe.cpu.btb.lookup(self.pc)      else \
            #                self.pcplus4                 if Pipe.CTL.pc_sel == PC_4                              else \
            #                Pipe.EX.brjmp_target         if Pipe.CTL.pc_sel == PC_BRJMP                          else \
            #                Pipe.EX.jump_reg_target      if Pipe.CTL.pc_sel == PC_JALR                           else \
            #                WORD(0)
            #Pipe.EX.brjmp_target         if Pipe.CTL.pc_sel == PC_BRJMP  else \
                           #Pipe.EX.jump_reg_target      if Pipe.CTL.pc_sel == PC_JALR   else \
                           #Pipe.cpu.btb.lookup(self.pc) if Pipe.CTL.pc_sel == Pipe.cpu.btb.lookup(Pipe.EX.pc) else \
                           #self.pcplus4                 #if Pipe.CTL.pc_sel == PC_4 else \
                           #WORD(0)



            #if (Pipe.EX.c_br_type == BR_N):
            #    EX_brjmp = False
            #elif not Pipe.cpu.btb.lookup(Pipe.EX.pc):  # btb entry empty
             #   EX_brjmp = self.pc_sel != PC_4
            #else:  # predicted something else
             #   EX_brjmp = self.pc_sel != Pipe.cpu.btb.lookup(Pipe.EX.pc)



                # Control() makes bubble misfetched instructions

    def update(self):

        if not Pipe.CTL.IF_stall:
            IF.reg_pc           = self.pc_next
            ID.reg_br_pred_addr     = self.br_pred_addr

        if (Pipe.CTL.ID_bubble and Pipe.CTL.ID_stall):
            sys.exit(1)

        if Pipe.CTL.ID_bubble:
            ID.reg_pc           = self.pc
            ID.reg_inst         = WORD(BUBBLE)
            ID.reg_exception    = WORD(EXC_NONE)
            ID.reg_pcplus4      = WORD(0)
        elif not Pipe.CTL.ID_stall:
            ID.reg_pc           = self.pc
            ID.reg_inst         = self.inst
            ID.reg_exception    = self.exception
            ID.reg_pcplus4      = self.pcplus4
        else:               # Pipe.CTL.ID_stall
            pass            # Do not update

        Pipe.log(S_IF, self.pc, self.inst, self.log())

    def log(self):
        return ("# inst=0x%08x, pc_next=0x%08x" % (self.inst, self.pc_next))


#--------------------------------------------------------------------------
#   ID: Instruction decode stage
#--------------------------------------------------------------------------

class ID(Pipe):


    # Pipeline registers ------------------------------

    reg_pc          = WORD(0)           # ID.reg_pc
    reg_inst        = WORD(BUBBLE)      # ID.reg_inst
    reg_exception   = WORD(EXC_NONE)    # ID.reg_exception
    reg_pcplus4     = WORD(0)           # ID.reg_pcplus4
    reg_br_pred_addr = WORD(0)

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.ID.pc
        #   self.inst               # Pipe.ID.inst
        #   self.exception          # Pipe.ID.exception
        #   self.pcplus4            # Pipe.ID.pcplus4
        #
        #   self.rs1                # Pipe.ID.rs1
        #   self.rs2                # Pipe.ID.rs2
        #   self.rd                 # Pipe.ID.rd
        #   self.op1_data           # Pipe.ID.op1_data
        #   self.op2_data           # Pipe.ID.op2_data
        #   self.rs2_data           # Pipe.ID.rs2_data
        #
        #   self.sp
        #----------------------------------------------


    def compute(self):

        # Readout pipeline register values
        self.pc         = ID.reg_pc
        self.inst       = ID.reg_inst
        self.exception  = ID.reg_exception
        self.pcplus4    = ID.reg_pcplus4

        self.br_pred_addr = ID.reg_br_pred_addr

        self.rs1        = RISCV.rs1(self.inst)          # for CTL (forwarding check)
        self.rs2        = RISCV.rs2(self.inst)          # for CTL (forwarding check)
        self.rd         = RISCV.rd(self.inst)

        rf_rs1_data, rf_rs2_data = Pipe.cpu.rf.read(self.rs1, self.rs2)


        #self.sp, dummy  = Pipe.cpu.rf.read(2, 1) # TODO: structural hazard?




        imm_i           = RISCV.imm_i(self.inst)
        imm_s           = RISCV.imm_s(self.inst)
        imm_b           = RISCV.imm_b(self.inst)
        imm_u           = RISCV.imm_u(self.inst)
        imm_j           = RISCV.imm_j(self.inst)

        # Generate control signals
        # CTL.gen() should be called after getting register numbers to detect forwarding condition

        if not Pipe.CTL.gen(self.inst):
            self.inst = BUBBLE

        # TODO: forward sp
        # TODO: forwarding logic is problematic with lw
        # push -> lw forwarding does not working

        # The order matters: EX -> MM -> WB (forwarding from the closest stage)
        self.sp = Pipe.EX.alu_out if Pipe.CTL.fwd_sp == FWD_EX       else \
                  Pipe.MM.wbdata  if Pipe.CTL.fwd_sp == FWD_MM       else \
                  Pipe.WB.wbdata  if Pipe.CTL.fwd_sp == FWD_WB       else \
                  Pipe.cpu.rf.read(2, 2)[0]

        # Determine ALU operand 2: R[rs2] or immediate values
        alu_op2 =       rf_rs2_data     if Pipe.CTL.op2_sel == OP2_RS2      else \
                        imm_i           if Pipe.CTL.op2_sel == OP2_IMI      else \
                        imm_s           if Pipe.CTL.op2_sel == OP2_IMS      else \
                        imm_b           if Pipe.CTL.op2_sel == OP2_IMB      else \
                        imm_u           if Pipe.CTL.op2_sel == OP2_IMU      else \
                        imm_j           if Pipe.CTL.op2_sel == OP2_IMJ      else \
                        4               if Pipe.CTL.op2_sel == OP2_4        else \
                        WORD(0)

        # Determine ALU operand 1: PC or R[rs1]
        # Get forwarded value for rs1 if necessary
        # The order matters: EX -> MM -> WB (forwarding from the closest stage)

        # self.rs1 == SP_RF_INDEX : forward sp to lw/sw
        # Pipe.CTL.op1_sel == OP1_SP : forward sp to push/pop
        self.op1_data = self.pc         if Pipe.CTL.op1_sel == OP1_PC       else \
                        self.sp         if Pipe.CTL.op1_sel == OP1_SP       else \
                        self.sp         if self.rs1 == SP_RF_INDEX and Pipe.CTL.op1_sel == OP1_RS1 else \
                        Pipe.EX.alu_out if Pipe.CTL.fwd_op1 == FWD_EX       else \
                        Pipe.MM.wbdata2 if Pipe.CTL.fwd_op1 == FWD_MM       else \
                        Pipe.WB.wbdata2 if Pipe.CTL.fwd_op1 == FWD_WB       else \
                        rf_rs1_data
        # cannot distinguish rs1 = sp(index 2) and imm 2 without Pipe.CTL.op1_sel == OP1_RS1

        # Get forwarded value for rs2 if necessary
        # The order matters: EX -> MM -> WB (forwarding from the closest stage)
        self.op2_data = self.sp         if self.rs2 == SP_RF_INDEX and Pipe.CTL.op2_sel == OP2_RS2 else \
                        Pipe.EX.alu_out if Pipe.CTL.fwd_op2 == FWD_EX       else \
                        Pipe.MM.wbdata2 if Pipe.CTL.fwd_op2 == FWD_MM       else \
                        Pipe.WB.wbdata2 if Pipe.CTL.fwd_op2 == FWD_WB       else \
                        alu_op2

        # Get forwarded value for rs2 if necessary
        # The order matters: EX -> MM -> WB (forwarding from the closest stage)
        # For sw and branch instructions, we need to carry R[rs2] as well
        # -- in these instructions, op2_data will hold an immediate value
        self.rs2_data = Pipe.EX.alu_out if Pipe.CTL.fwd_rs2 == FWD_EX       else \
                        Pipe.MM.wbdata2  if Pipe.CTL.fwd_rs2 == FWD_MM       else \
                        Pipe.WB.wbdata2  if Pipe.CTL.fwd_rs2 == FWD_WB       else \
                        rf_rs2_data

        # new hazard
        # forward wbdata2 instead of wbdata
        # wbdata is sp, and wbdata2 is the real rs2 value when MM or WB is POP instruction
        # otherwise, wbdata == wbdata2

        # however, we should forward wbdata for sp
        # TODO: how about op1 or op2?


    def update(self):

        EX.reg_pc                   = self.pc


        if Pipe.CTL.EX_bubble:
            EX.reg_inst             = WORD(BUBBLE)
            EX.reg_exception        = WORD(EXC_NONE)
            EX.reg_c_br_type        = WORD(BR_N)
            EX.reg_c_rf_wen         = False
            EX.reg_c_dmem_en        = False
        else:
            EX.reg_inst             = self.inst
            EX.reg_exception        = self.exception
            EX.reg_rd               = self.rd
            EX.reg_op1_data         = self.op1_data
            EX.reg_op2_data         = self.op2_data
            EX.reg_rs2_data         = self.rs2_data
            EX.reg_c_br_type        = Pipe.CTL.br_type
            EX.reg_c_alu_fun        = Pipe.CTL.alu_fun
            EX.reg_c_wb_sel         = Pipe.CTL.wb_sel
            EX.reg_c_rf_wen         = Pipe.CTL.rf_wen
            EX.reg_c_dmem_en        = Pipe.CTL.dmem_en
            EX.reg_c_dmem_rw        = Pipe.CTL.dmem_rw
            EX.reg_pcplus4          = self.pcplus4

            EX.reg_sp               = self.sp
            EX.reg_c_dmem_addr_sel  = Pipe.CTL.dmem_addr_sel
            EX.reg_br_pred_addr     = self.br_pred_addr

        Pipe.log(S_ID, self.pc, self.inst, self.log())

    def log(self):
        if self.inst in [ BUBBLE, ILLEGAL ]:
            return('# -')
        else:
            return("# rd=%d rs1=%d rs2=%d op1=0x%08x op2=0x%08x" % (self.rd, self.rs1, self.rs2, self.op1_data, self.op2_data))


#--------------------------------------------------------------------------
#   EX: Execution stage
#--------------------------------------------------------------------------

class EX(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # EX.reg_pc
    reg_inst            = WORD(BUBBLE)      # EX.reg_inst
    reg_exception       = WORD(EXC_NONE)    # EX.exception
    reg_rd              = WORD(0)           # EX.reg_rd
    reg_c_rf_wen        = False             # EX.reg_c_rf_wen
    reg_c_wb_sel        = WORD(WB_X)        # EX.reg_c_wb_sel
    reg_c_dmem_en       = False             # EX.reg_c_dmem_en
    reg_c_dmem_rw       = WORD(M_X)         # EX.reg_c_dmem_rw
    reg_c_br_type       = WORD(BR_N)        # EX.reg_c_br_type
    reg_c_alu_fun       = WORD(ALU_X)       # EX.reg_c_alu_fun
    reg_op1_data        = WORD(0)           # EX.reg_op1_data
    reg_op2_data        = WORD(0)           # EX.reg_op2_data
    reg_rs2_data        = WORD(0)           # EX.reg_rs2_data
    reg_pcplus4         = WORD(0)           # EX.reg_pcplus4

    reg_sp              = WORD(0)
    reg_c_dmem_addr_sel = WORD(MAD_ALU)
    reg_br_pred_addr    = WORD(0)
    reg_br_true_addr    = WORD(0)

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.EX.pc
        #   self.inst               # Pipe.EX.inst
        #   self.exception          # Pipe.EX.exception
        #   self.rd                 # Pipe.EX.rd
        #   self.c_rf_wen           # Pipe.EX.c_rf_wen
        #   self.c_wb_sel           # Pipe.EX.c_wb_sel
        #   self.c_dmem_en          # Pipe.EX.c_dmem_en
        #   self.c_dmem_rw          # Pipe.EX.c_dmem_fcn
        #   self.c_br_type          # Pipe.EX.c_br_type
        #   self.c_alu_fun          # Pipe.EX.c_alu_fun
        #   self.op1_data           # Pipe.EX.op1_data
        #   self.op2_data           # Pipe.EX.op2_data
        #   self.rs2_data           # Pipe.EX.rs2_data
        #   self.pcplus4            # Pipe.EX.pcplus4
        #
        #   self.alu2_data          # Pipe.EX.alu2_data
        #   self.alu_out            # Pipe.EX.alu_out
        #   self.brjmp_target       # Pipe.EX.brjmp_target
        #   self.jump_reg_target    # Pipe.EX.jump_reg_target
        #
        #   self.sp
        #
        #----------------------------------------------


    def compute(self):

        # Readout pipeline register values
        self.pc                 = EX.reg_pc
        self.inst               = EX.reg_inst
        self.exception          = EX.reg_exception
        self.rd                 = EX.reg_rd
        self.c_rf_wen           = EX.reg_c_rf_wen
        self.c_wb_sel           = EX.reg_c_wb_sel
        self.c_dmem_en          = EX.reg_c_dmem_en
        self.c_dmem_rw          = EX.reg_c_dmem_rw
        self.c_br_type          = EX.reg_c_br_type
        self.c_alu_fun          = EX.reg_c_alu_fun
        self.op1_data           = EX.reg_op1_data
        self.op2_data           = EX.reg_op2_data
        self.rs2_data           = EX.reg_rs2_data
        self.pcplus4            = EX.reg_pcplus4

        self.sp                 = EX.reg_sp
        self.c_dmem_addr_sel    = EX.reg_c_dmem_addr_sel
        self.br_pred_addr   = EX.reg_br_pred_addr



        # For branch instructions, we use ALU to make comparisons between rs1 and rs2.
        # Since op2_data has an immediate value (offset) for branch instructions,
        # we change the input of ALU to rs2_data.
        self.alu2_data  = self.rs2_data     if self.c_br_type in [ BR_NE, BR_EQ, BR_GE, BR_GEU, BR_LT, BR_LTU ] else \
                          self.op2_data

        # Perform ALU operation
        self.alu_out = Pipe.cpu.alu.op(self.c_alu_fun, self.op1_data, self.alu2_data)

        # Adjust the output for jalr instruction (forwarded to IF)
        self.jump_reg_target    = self.alu_out & WORD(0xfffffffe)

        # Calculate the branch/jump target address using an adder (forwarded to IF)
        self.brjmp_target       = Pipe.cpu.adder_brtarget.op(self.pc, self.op2_data)

        # For jal and jalr instructions, pc+4 should be written to the rd
        if self.c_wb_sel == WB_PC4:
            self.alu_out        = self.pcplus4

    def update(self):

        # TODO: update BTB
        self.br_true_addr = self.pcplus4 # dummy when well-predicted or none-branch inst.
        if self.c_br_type != BR_N and Pipe.CTL.EX_mispredicted:
            #if (true_address) != self.br_pred_addr  :
            # wrong prediction

            if Pipe.CTL.pc_sel == PC_BRJMP and self.br_pred_addr != self.brjmp_target: # update if branch taken
                Pipe.cpu.btb.add(self.pc, self.brjmp_target)
                #self.br_true_addr = self.brjmp_target
                IF.reg_pc = self.brjmp_target
                #Pipe.IF.pc_next = self.brjmp_target
            #elif Pipe.CTL.pc_sel == PC_JALR and self.br_pred_addr != self.jump_reg_target:
            #    Pipe.cpu.btb.add(self.pc, self.jump_reg_target)
            #    #self.br_true_addr = self.jump_reg_target
            #    IF.reg_pc = self.jump_reg_target
                #Pipe.IF.pc_next = self.jump_reg_target
            elif Pipe.CTL.pc_sel == PC_4 and self.br_pred_addr != self.pcplus4: # branch not taken
                Pipe.cpu.btb.remove(self.pc)
                #self.br_true_addr = self.pcplus4
                IF.reg_pc = self.pcplus4


        # TODO: change next fetch target in IF stage when mispredicted


        MM.reg_pc                   = self.pc
        # Exception should not be cleared in MM even if MM_bubble is enabled.
        # Otherwise we will lose any exception status.
        # For cancelled instructions, exception has been cleared already
        # as they enter ID or EX stage.
        MM.reg_exception            = self.exception

        if Pipe.CTL.MM_bubble:
            MM.reg_inst             = WORD(BUBBLE)
            MM.reg_c_rf_wen         = False
            MM.reg_c_dmem_en        = False
        else:
            MM.reg_inst             = self.inst
            MM.reg_rd               = self.rd
            MM.reg_c_rf_wen         = self.c_rf_wen
            MM.reg_c_wb_sel         = self.c_wb_sel
            MM.reg_c_dmem_en        = self.c_dmem_en
            MM.reg_c_dmem_rw        = self.c_dmem_rw
            MM.reg_alu_out          = self.alu_out
            MM.reg_rs2_data         = self.rs2_data
            MM.reg_sp               = self.sp
            MM.reg_c_dmem_addr_sel  = self.c_dmem_addr_sel
            #MM.reg_br_pred_addr     = self.br_pred_addr

        Pipe.log(S_EX, self.pc, self.inst, self.log())


    def log(self):

        ALU_OPS = {
            ALU_X       : f'# -',
            ALU_ADD     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} + {self.alu2_data:#010x}',
            ALU_SUB     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} - {self.alu2_data:#010x}',
            ALU_AND     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} & {self.alu2_data:#010x}',
            ALU_OR      : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} | {self.alu2_data:#010x}',
            ALU_XOR     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} ^ {self.alu2_data:#010x}',
            ALU_SLT     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} < {self.alu2_data:#010x} (signed)',
            ALU_SLTU    : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} < {self.alu2_data:#010x} (unsigned)',
            ALU_SLL     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} << {self.alu2_data & 0x1f}',
            ALU_SRL     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} >> {self.alu2_data & 0x1f} (logical)',
            ALU_SRA     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} >> {self.alu2_data & 0x1f} (arithmetic)',
            ALU_COPY1   : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} (pass 1)',
            ALU_COPY2   : f'# {self.alu_out:#010x} <- {self.alu2_data:#010x} (pass 2)',
            ALU_SEQ     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} == {self.alu2_data:#010x}',
        }
        return('# -' if self.inst == BUBBLE else ALU_OPS[self.c_alu_fun]);


#--------------------------------------------------------------------------
#   MM: Memory access stage
#--------------------------------------------------------------------------

class MM(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # MM.reg_pc
    reg_inst            = WORD(BUBBLE)      # MM.reg_inst
    reg_exception       = WORD(EXC_NONE)    # MM.reg_exception
    reg_rd              = WORD(0)           # MM.reg_rd
    reg_c_rf_wen        = False             # MM.reg_c_rf_wen
    reg_c_wb_sel        = WORD(WB_X)        # MM.reg_c_wb_sel
    reg_c_dmem_en       = False             # MM.reg_c_dmem_en
    reg_c_dmem_rw       = WORD(M_X)         # MM.reg_c_dmem_rw
    reg_alu_out         = WORD(0)           # MM.reg_alu_out
    reg_rs2_data        = WORD(0)           # MM.reg_rs2_data

    reg_sp              = WORD(0)
    reg_c_dmem_addr_sel = WORD(MAD_ALU)
    #reg_br_pred_addr    = WORD(0)

    #--------------------------------------------------

    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.MM.pc
        #   self.inst               # Pipe.MM.inst
        #   self.exception          # Pipe.MM.exception
        #   self.rd                 # Pipe.MM.rd
        #   self.c_rf_wen           # Pipe.MM.c_rf_wen
        #   self.c_wb_sel           # Pipe.MM.c_rf_wen
        #   self.c_dmem_en          # Pipe.MM.c_dmem_en
        #   self.c_dmem_rw          # Pipe.MM.c_dmem_rw
        #   self.alu_out            # Pipe.MM.alu_out
        #   self.rs2_data           # Pipe.MM.rs2_data
        #
        #   self.wbdata             # Pipe.MM.wbdata
        #
        #   self.sp
        #   self.wbdata2            # Pipe.MM.wbdata2 for POP
        #   self.c_dmem_addr_sel
        #----------------------------------------------

    def compute(self):

        self.pc             = MM.reg_pc
        self.inst           = MM.reg_inst
        self.exception      = MM.reg_exception
        self.rd             = MM.reg_rd
        self.c_rf_wen       = MM.reg_c_rf_wen
        self.c_wb_sel       = MM.reg_c_wb_sel
        self.c_dmem_en      = MM.reg_c_dmem_en
        self.c_dmem_rw      = MM.reg_c_dmem_rw
        self.alu_out        = MM.reg_alu_out
        self.rs2_data       = MM.reg_rs2_data

        self.sp             = MM.reg_sp
        self.c_dmem_addr_sel= MM.reg_c_dmem_addr_sel
        #self.br_pred_addr   = MM.reg_br_pred_addr

        # Access data memory (dmem) if needed
        mem_data, status = Pipe.cpu.dmem.access(self.c_dmem_en, self.alu_out, self.rs2_data, self.c_dmem_rw) if self.c_dmem_addr_sel == MAD_ALU   else \
                           Pipe.cpu.dmem.access(self.c_dmem_en, self.sp, self.rs2_data, self.c_dmem_rw)    # if self.c_dmem_addr_sel == MAD_SP


        # TODO: POP causes DMEM err here => sp not forwarded

        # Handle exception during dmem access
        if not status:
            self.exception |= EXC_DMEM_ERROR
            self.c_rf_wen   = False

        # For load instruction, we need to store the value read from dmem
        if (self.c_wb_sel == WB_MEM):
            self.wbdata = mem_data
            self.wbdata2 = mem_data # dummy
        elif (self.c_wb_sel == WB_POP): # modified for POP
            #self.wbdata = mem_data      # loaded from memory -> rd
            #self.wbdata2 = self.alu_out # sp+4               -> sp
            # TODO
            self.wbdata = self.alu_out
            self.wbdata2 = mem_data
        else:
            self.wbdata = self.alu_out
            self.wbdata2 = self.alu_out # dummy

        # self.wbdata         = mem_data          if self.c_wb_sel == WB_MEM  else \
        #                      self.alu_out


    def update(self):

        WB.reg_pc           = self.pc
        WB.reg_inst         = self.inst
        WB.reg_exception    = self.exception
        WB.reg_rd           = self.rd
        WB.reg_c_rf_wen     = self.c_rf_wen
        WB.reg_wbdata       = self.wbdata

        WB.reg_wbdata2      = self.wbdata2
        WB.reg_sp           = self.sp
        WB.reg_c_wb_sel     = self.c_wb_sel

        Pipe.log(S_MM, self.pc, self.inst, self.log())


    def log(self):
        if not self.c_dmem_en:
            return('# -')
        elif self.c_dmem_rw == M_XRD:
            return('# 0x%08x <- M[0x%08x]' % (self.wbdata, self.alu_out))
        else:
            return('# M[0x%08x] <- 0x%08x' % (self.alu_out, self.rs2_data))


#--------------------------------------------------------------------------
#   WB: Write back stage
#--------------------------------------------------------------------------

class WB(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # WB.reg_pc
    reg_inst            = WORD(BUBBLE)      # WB.reg_inst
    reg_exception       = WORD(EXC_NONE)    # WB.reg_exception
    reg_rd              = WORD(0)           # WB.reg_rd
    reg_c_rf_wen        = False             # WB.reg_c_rf_wen
    reg_wbdata          = WORD(0)           # WB.reg_wbdata

    reg_sp              = WORD(0)
    reg_wbdata2         = WORD(0)
    reg_c_wb_sel        = WORD(WB_X)

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

    def compute(self):

        # Readout pipeline register values
        self.pc                 = WB.reg_pc
        self.inst               = WB.reg_inst
        self.exception          = WB.reg_exception
        self.rd                 = WB.reg_rd
        self.c_rf_wen           = WB.reg_c_rf_wen
        self.wbdata             = WB.reg_wbdata

        self.sp                 = WB.reg_sp
        self.wbdata2            = WB.reg_wbdata2
        self.c_wb_sel           = WB.reg_c_wb_sel

    def update(self):

        if self.c_rf_wen:
            if self.c_wb_sel == WB_POP:
                Pipe.cpu.rf.write(SP_RF_INDEX, self.wbdata, self.rd, self.wbdata2)
                #TODO
            elif self.c_wb_sel == WB_SP: # TODO: Problematic at custom.s
                Pipe.cpu.rf.write(SP_RF_INDEX, self.wbdata)
            else:
                Pipe.cpu.rf.write(self.rd, self.wbdata)


        Pipe.log(S_WB, self.pc, self.inst, self.log())

        if (self.exception):
            return False
        else:
            return True

    def log(self): # TODO
        #if self.inst == BUBBLE or (not self.c_rf_wen):
        #    return('# -')
        if self.inst == BUBBLE:
            return('# BUBBLE')
        elif not self.c_rf_wen:
            return ('# -')
        else:
            return('# R[%d] <- 0x%08x' % (self.rd, self.wbdata))



#--------------------------------------------------------------------------
#   Control: Control logic (executed in ID stage)
#--------------------------------------------------------------------------

class Control(object):

    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc_sel             # Pipe.CTL.pc_sel
        #   self.br_type            # Pipe.CTL.br_type
        #   self.op1_sel            # Pipe.CTL.op1_sel
        #   self.op2_sel            # Pipe.CTL.op2_sel
        #   self.alu_fun            # Pipe.CTL.alu_fun
        #   self.wb_sel             # Pipe.CTL.wb_sel
        #   self.rf_wen             # Pipe.CTL.rf_wen
        #   self.fwd_op1            # Pipe.CTL.fwd_op1
        #   self.fwd_op2            # Pipe.CTL.fwd_op2
        #   self.imem_en            # Pipe.CTL.imem_en
        #   self.imem_rw            # Pipe.CTL.imem_rw
        #   self.dmem_en            # Pipe.CTL.dmem_en
        #   self.dmem_rw            # Pipe.CTL.dmem_rw
        #   self.IF_stall           # Pipe.CTL.IF_stall
        #   self.ID_stall           # Pipe.CTL.ID_stall
        #   self.ID_bubble          # Pipe.CTL.ID_bubble
        #   self.EX_bubble          # Pipe.CTL.EX_bubble
        #   self.MM_bubble          # Pipe.CTL.MM_bubble
        #
        #   self.dmem_addr_sel      # Pipe.CTL.dmem_addr_sel
        #   self.fwd_sp             # Pipe.CTL.fwd_sp
        #----------------------------------------------


        # These signals are used before gen() is called
        self.imem_en        = True
        self.imem_rw        = M_XRD
        self.dmem_addr_sel  = MAD_ALU # TODO: used after gen() but why doesn't works
        #self.fwd_sp         = FWD_NONE


    def gen(self, inst):

        opcode = RISCV.opcode(inst)
        if opcode in [ EBREAK, ECALL ]:
            Pipe.ID.exception |= EXC_EBREAK
        elif opcode == ILLEGAL:
            Pipe.ID.exception |= EXC_ILLEGAL_INST
            inst = BUBBLE
            opcode = RISCV.opcode(inst)

        self.IF_stall       = False
        self.ID_stall       = False
        self.ID_bubble      = False
        self.EX_bubble      = False
        self.MM_bubble      = False

        cs = csignals[opcode]

        self.br_type        = cs[CS_BR_TYPE]
        self.op1_sel        = cs[CS_OP1_SEL]
        self.op2_sel        = cs[CS_OP2_SEL]
        self.alu_fun        = cs[CS_ALU_FUN]
        self.wb_sel         = cs[CS_WB_SEL]
        self.rf_wen         = cs[CS_RF_WEN]

        rs1_oen             = cs[CS_RS1_OEN]
        rs2_oen             = cs[CS_RS2_OEN]

        self.dmem_en        = cs[CS_MEM_EN]
        self.dmem_rw        = cs[CS_MEM_FCN]

        self.dmem_addr_sel  = cs[CS_MAD_SEL]
        sp_oen              = cs[CS_SP_OEN]

        # Control signal to select the next PC
        self.pc_sel         =   PC_BRJMP    if (EX.reg_c_br_type == BR_NE  and (not Pipe.EX.alu_out)) or    \
                                               (EX.reg_c_br_type == BR_EQ  and Pipe.EX.alu_out) or          \
                                               (EX.reg_c_br_type == BR_GE  and (not Pipe.EX.alu_out)) or    \
                                               (EX.reg_c_br_type == BR_GEU and (not Pipe.EX.alu_out)) or    \
                                               (EX.reg_c_br_type == BR_LT  and Pipe.EX.alu_out) or          \
                                               (EX.reg_c_br_type == BR_LTU and Pipe.EX.alu_out) or          \
                                               (EX.reg_c_br_type == BR_J) else                              \
                                PC_JALR     if  EX.reg_c_br_type == BR_JR else                              \
                                PC_4

        # Control signal for forwarding rs1 value to op1_data
        # The c_rf_wen signal can be disabled when we have an exception during dmem access,
        # so Pipe.MM.c_rf_wen should be used instead of MM.reg_c_rf_wen.
        # TODO: make forward sp (push pop -> lw sw)
        self.fwd_op1        =   FWD_EX      if (EX.reg_rd == Pipe.ID.rs1) and rs1_oen and   \
                                               (EX.reg_rd != 0) and EX.reg_c_rf_wen else    \
                                FWD_MM      if (MM.reg_rd == Pipe.ID.rs1) and rs1_oen and   \
                                               (MM.reg_rd != 0) and Pipe.MM.c_rf_wen else   \
                                FWD_WB      if (WB.reg_rd == Pipe.ID.rs1) and rs1_oen and   \
                                               (WB.reg_rd != 0) and WB.reg_c_rf_wen else    \
                                FWD_NONE

        # Control signal for forwarding rs2 value to op2_data
        self.fwd_op2        =   FWD_EX      if (EX.reg_rd == Pipe.ID.rs2) and               \
                                               (EX.reg_rd != 0) and EX.reg_c_rf_wen and     \
                                               self.op2_sel == OP2_RS2 else                 \
                                FWD_MM      if (MM.reg_rd == Pipe.ID.rs2) and               \
                                               (MM.reg_rd != 0) and Pipe.MM.c_rf_wen and    \
                                               self.op2_sel == OP2_RS2 else                 \
                                FWD_WB      if (WB.reg_rd == Pipe.ID.rs2) and               \
                                               (WB.reg_rd != 0) and WB.reg_c_rf_wen and     \
                                               self.op2_sel == OP2_RS2 else                 \
                                FWD_NONE

        # Control signal for forwarding rs2 value to rs2_data
        self.fwd_rs2        =   FWD_EX      if (EX.reg_rd == Pipe.ID.rs2) and rs2_oen and   \
                                               (EX.reg_rd != 0) and EX.reg_c_rf_wen  else   \
                                FWD_MM      if (MM.reg_rd == Pipe.ID.rs2) and rs2_oen and   \
                                               (MM.reg_rd != 0) and Pipe.MM.c_rf_wen else   \
                                FWD_WB      if (WB.reg_rd == Pipe.ID.rs2) and rs2_oen and   \
                                               (WB.reg_rd != 0) and WB.reg_c_rf_wen  else   \
                                FWD_NONE

        # TODO

        self.fwd_sp         =   FWD_EX      if (EX.reg_c_wb_sel == WB_POP or EX.reg_c_wb_sel == WB_SP) and   \
                                               EX.reg_c_rf_wen  else   \
                                FWD_EX      if (EX.reg_rd == SP_RF_INDEX) and \
                                               (EX.reg_rd != 0) and EX.reg_c_rf_wen else \
                                FWD_MM      if (MM.reg_c_wb_sel == WB_POP or MM.reg_c_wb_sel == WB_SP) and   \
                                               Pipe.MM.c_rf_wen else   \
                                FWD_MM      if (MM.reg_rd == SP_RF_INDEX) and   \
                                               (MM.reg_rd != 0) and Pipe.MM.c_rf_wen else   \
                                FWD_WB      if (WB.reg_c_wb_sel == WB_POP or WB.reg_c_wb_sel == WB_SP) and   \
                                               WB.reg_c_rf_wen  else \
                                FWD_WB      if (WB.reg_rd == SP_RF_INDEX) and \
                                               (WB.reg_rd != 0) and WB.reg_c_rf_wen  else   \
                                FWD_NONE
        # removed sp_oen, because of lw/sw sp forwarding
        #self.fwd_sp         =   FWD_EX      if (EX.reg_c_wb_sel == WB_POP or EX.reg_c_wb_sel == WB_SP) and sp_oen and   \
        #                                       EX.reg_c_rf_wen  else   \
        #                        FWD_EX      if (EX.reg_rd == SP_RF_INDEX) and sp_oen and \
        #                                       (EX.reg_rd != 0) and EX.reg_c_rf_wen else \
        #                        FWD_MM      if (MM.reg_c_wb_sel == WB_POP or MM.reg_c_wb_sel == WB_SP) and sp_oen and   \
        #                                       Pipe.MM.c_rf_wen else   \
        #                        FWD_MM      if (MM.reg_rd == SP_RF_INDEX) and sp_oen and   \
        #                                       (MM.reg_rd != 0) and Pipe.MM.c_rf_wen else   \
        #                        FWD_WB      if (WB.reg_c_wb_sel == WB_POP or WB.reg_c_wb_sel == WB_SP) and sp_oen and   \
        #                                       WB.reg_c_rf_wen  else \
         #                       FWD_WB      if (WB.reg_rd == SP_RF_INDEX) and sp_oen and \
         #                                      (WB.reg_rd != 0) and WB.reg_c_rf_wen  else   \
         #                       FWD_NONE
        # first - sp forwarded from PUSH/POP
        # check if EX/MM/WB stage instruction is POP or PUSH, instead of considering rd
        # because we do not use rd as save address of ALU output

        # second - sp forwarded from other instructions such as LUI
        # just consider rd just like rs1/rs2 forwarding



        # Check for load-use data hazard
        EX_load_inst = EX.reg_c_dmem_en and EX.reg_c_dmem_rw == M_XRD # check if EX is load instruction or not
        load_use_hazard     = ((EX_load_inst and EX.reg_rd != 0) and             \
                              ((EX.reg_rd == Pipe.ID.rs1 and rs1_oen) or         \
                               (EX.reg_rd == Pipe.ID.rs2 and rs2_oen)))
        # pop : load, rd
        # push : use, rs2

        # Check for mispredicted branch/jump
        # TODO: mispredict logic
        # this executed before update BTB
        #EX_brjmp            = self.pc_sel != PC_4
        if (Pipe.EX.c_br_type == BR_N):
            EX_brjmp = False
        elif not Pipe.cpu.btb.lookup(Pipe.EX.pc): # btb entry empty
            EX_brjmp = self.pc_sel != PC_4
        else: # predicted something else
            # EX_brjmp = (true_address) != EX.reg_br_pred_addr
            if (self.pc_sel == PC_BRJMP):
                EX_brjmp = Pipe.EX.brjmp_target != EX.reg_br_pred_addr
            #elif (self.pc_sel == PC_JALR):
            #    EX_brjmp = Pipe.EX.jump_reg_target != EX.reg_br_pred_addr
            else:
                EX_brjmp = Pipe.EX.pcplus4 != EX.reg_br_pred_addr
        self.EX_mispredicted = EX_brjmp

                       #Pipe.cpu.btb.lookup(Pipe.EX.pc)

        # self.pc_sel: branch outcome
        # PC_4: predicted branch outcome (Always-not-Taken)

        # For load-use hazard, ID and IF are stalled for one cycle (and EX bubbled)
        # For mispredicted branches, instructions in ID and IF should be cancelled (become BUBBLE)
        self.IF_stall       = load_use_hazard
        self.ID_stall       = load_use_hazard
        self.ID_bubble      = EX_brjmp
        self.EX_bubble      = load_use_hazard or EX_brjmp

        # Any instruction with an exception becomes BUBBLE as it enters the MM stage.
        # This is because the instruction can be cancelled while it is in IF and ID due to mispredicted
        # branch/jump, in which case it should not cause any exception. We just keep track of the exception
        # state with the instruction along the pipeline until EX. If the instruction survives EX, it is
        # safe to make the instruction and any following instructions bubble (except for EBREAK)
        self.MM_bubble = (Pipe.EX.exception and (Pipe.EX.exception != EXC_EBREAK)) or (Pipe.MM.exception)

        if inst == BUBBLE:
            return False
        else:
            return True

