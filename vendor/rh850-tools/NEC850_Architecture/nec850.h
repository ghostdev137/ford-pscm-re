// MIT License
// 
// Copyright (c) 2015-2024 Vector 35 Inc
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions 
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

#ifndef TESTPLUGIN_LIBRARY_H
#define TESTPLUGIN_LIBRARY_H

#include "binaryninjaapi.h"

#endif //TESTPLUGIN_LIBRARY_H
#define NEC_REG_R0  0
#define NEC_REG_R1  1
#define NEC_REG_R2  2
#define NEC_REG_SP  3
#define NEC_REG_R4  4
#define NEC_REG_R5  5
#define NEC_REG_R6  6
#define NEC_REG_R7  7
#define NEC_REG_R8  8
#define NEC_REG_R9  9
#define NEC_REG_R10 10
#define NEC_REG_R11 11
#define NEC_REG_R12 12
#define NEC_REG_R13 13
#define NEC_REG_R14 14
#define NEC_REG_R15 15
#define NEC_REG_R16 16
#define NEC_REG_R17 17
#define NEC_REG_R18 18
#define NEC_REG_R19 19
#define NEC_REG_R20 20
#define NEC_REG_R21 21
#define NEC_REG_R22 22
#define NEC_REG_R23 23
#define NEC_REG_R24 24
#define NEC_REG_R25 25
#define NEC_REG_R26 26
#define NEC_REG_R27 27
#define NEC_REG_R28 28
#define NEC_REG_R29 29
#define NEC_REG_EP  30
#define NEC_REG_LP  31
#define NEC_REG_PC  32


// regId + 40 * sellID
#define NEC_SYSREG_EIPC  100
#define NEC_SYSREG_EIPSW  101
#define NEC_SYSREG_FEPC  102
#define NEC_SYSREG_FEPSW  103
#define NEC_SYSREG_PSW  105
#define NEC_SYSREG_FPSR  106
#define NEC_SYSREG_FPEPC  107
#define NEC_SYSREG_FPST  108
#define NEC_SYSREG_FPCC  109
#define NEC_SYSREG_FPCFG  110
#define NEC_SYSREG_FPEC  111
#define NEC_SYSREG_EIIC  113
#define NEC_SYSREG_FEIC  114
#define NEC_SYSREG_CTPC  116
#define NEC_SYSREG_CTPSW  117
#define NEC_SYSREG_DBPC  118
#define NEC_SYSREG_DBPSW  119
#define NEC_SYSREG_CTBP  120
#define NEC_SYSREG_EIWR  128
#define NEC_SYSREG_FEWR  129
#define NEC_SYSREG_BSEL  131
#define NEC_SYSREG_MCFG0  140
#define NEC_SYSREG_RBASE  142
#define NEC_SYSREG_EBASE  143
#define NEC_SYSREG_INTBP  144
#define NEC_SYSREG_MCTL  145
#define NEC_SYSREG_PID  146
#define NEC_SYSREG_SCCFG  151
#define NEC_SYSREG_SCBP  152
#define NEC_SYSREG_HTCFG0  180
#define NEC_SYSREG_MEA  186
#define NEC_SYSREG_ASID  187
#define NEC_SYSREG_MEI  188


#define FLAG_SAT 0
#define FLAG_CY  1
#define FLAG_OV  2
#define FLAG_S   3
#define FLAG_Z   4

#define FLAG_WRITE_NONE 5
#define FLAG_WRITE_ALL 6
#define FLAG_WRITE_OVSZ 7
#define FLAG_WRITE_CYOVSZ 8
#define FLAG_WRITE_Z 9
#define FLAG_WRITE_SZ 10
#define FLAG_WRITE_CYSZ 11

enum cond {
    NEC850_CCCC_V = 0,
    NEC850_CCCC_NV = 8,
    NEC850_CCCC_CL = 1,
    NEC850_CCCC_NCNL = 9,
    NEC850_CCCC_Z = 2,
    NEC850_CCCC_NZ = 10,
    NEC850_CCCC_NH = 3,
    NEC850_CCCC_H = 11,
    NEC850_CCCC_SN = 4,
    NEC850_CCCC_NSP = 12,
    NEC850_CCCC_T = 5,
    NEC850_CCCC_LT = 6,
    NEC850_CCCC_GE = 14,
    NEC850_CCCC_LE = 7,
    NEC850_CCCC_GT = 15,

};

enum VLEIntrinsics{
    SCH1L_INTRINSIC,
    SCH1R_INTRINSIC,
    SCH0L_INTRINSIC,
    SCH0R_INTRINSIC,
    SYNC_MEMORY_ACCESS,
    SYNC_PIPELINE,
    SYNC_INSN_FETCHER,
    SYNC_EXCEPTIONS,
    CLL_INTRINSIC,
    SNOOZE_INTRINSIC,
    DI_INTRINSIC,
    EI_INTRINSIC,
    HALT_INTRINSIC,
    RIE_INTRINSIC
};
