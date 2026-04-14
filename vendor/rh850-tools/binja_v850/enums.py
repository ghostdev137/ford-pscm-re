from enum import IntEnum, Enum

REG = IntEnum("REG", [("SP", 3), ("GP", 4), ("TP", 5), ("EP", 30), ("LP", 31), ("PC", 32)] + [("R%d" % i, i) for i in
                                                                                              range(0, 32)])

user_flag = [("Z", 0), ("S", 1), ("OV", 2), ("CY", 3), ("SAT", 4)]
USER_FLAG = IntEnum("USER_FLAG", user_flag)
system_flag = user_flag + [("ID", 5), ("EP", 6), ("NP", 7), ("IMP", 16), ("DMP", 17), ("NPV", 18)]
FLAG = IntEnum("FLAG", system_flag)

sreg_V850 =  [("EIPC", 0), ("EIPSW", 1), ("FEPC", 2), ("FEPSW", 3), ("ECR", 4), ("PSW", 5)]
sreg_exc = [("EIIC", 13), ("FEIC", 14), ("CTPC", 16),
             ("CTPSW", 17), ("CTBP", 20)]

sreg_V850ES = sreg_V850  + sreg_exc + [("SCCFG", 11), ("SCBP", 12), ("DBIC", 15),
                            ("DBPC", 18), ("DBPSW", 19),  ("DIR", 21)]

sreg_fp = [("FPSR", 6), ("FPEPC", 7), ("FPST", 8), ("FPCC", 9), ("FPCFG", 10)]
sreg_common = [("EIWR", 28), ("FEWR", 29), ("DBWR", 30), ("BSEL", 31)]
sreg_V850E2 = sreg_V850ES + sreg_common + \
              [("SW_CTL", 0x001000), ("SW_CFG", 0x001001), ("SW_BASE", 0x001003)] + \
              [("EH_CFG", 0x001101), ("EH_RESET", 0x001102), ("EH_BASE", 0x001103)]

sreg_V850E2M = sreg_V850E2 + [(n, 0x200000 + v) for n, v in sreg_fp] + [("FPEC", 0x20000b)]
sreg_RH850 = sreg_V850 + sreg_fp + sreg_exc + sreg_common + \
             [("MCFG0", 0x0100), ("RBASE", 0x0102), ("EBASE", 0x0103), ("INTBP", 0x0104),
              ("MCTL", 0x0105), ("PID", 0x0106), ("SCCFG", 0x010b), ("SCBP", 0x010b)] + \
             [("HTCFG0", 0x0200), ("MEA", 0x0206), ("ASID", 0x0207), ("MEI", 0x0208)]

SREG_V850 = IntEnum("SREG_V850", sreg_V850)
SREG_V850ES = IntEnum("SREG_V850ES", sreg_V850ES)
SREG_V850E2 = IntEnum("SREG_V850E2", sreg_V850E2)
SREG_V850E2M = IntEnum("SREG_V850E2M", sreg_V850E2M)
SREG_RH850 = IntEnum("SREG_RH850", sreg_RH850)

# Instructions

v850_mnem = ["INVALID_CODE", "UNDEF_CODE", "ADD", "ADDI", "AND", "ANDI", "B",
             "CMP", "DI", "DIVH", "EI", "HALT",
             "JARL", "JMP", "JR", "LD_B", "LD_H", "LD_W", "LDSR",
             "MOV", "MOVEA", "MOVHI", "MULH", "MULHI",
             "NOP", "NOT", "OR", "ORI", "RETI",
             "SAR", "SATADD", "SATSUB", "SATSUBI", "SATSUBR",
             "SETF", "SHL", "SHR", "SLD_B", "SLD_H", "SLD_W",
             "SST_B", "SST_H", "SST_W", "ST_B", "ST_H", "ST_W", "STSR",
             "SUB", "SUBR", "TRAP", "TST", "XOR", "XORI",
             ]

v850e1_mnem = v850_mnem + ["BSH", "BSW", "CALLT", "CLR1", "CMOV", "CTRET", "DISPOSE", "DIV", "DIVHU", "DIVU",
                           "HSW", "LD_BU", "LD_HU", "NOT1", "MUL", "MULU", "PREPARE", "SASF", "SET1", "SLD_BU",
                           "SLD_HU",
                           "SWITCH", "SXB", "SXH", "TST1", "ZXB", "ZXH"
                           ]
v850es_mnem = v850e1_mnem + ["DBRET", "DBTRAP"]
v850e2_mnem = v850es_mnem + ["ADF", "HSH", "MAC", "MACU", "SBF", "SCH0L", "SCH0R", "SCH1L", "SCH1R"]
v850e2s_mnem = v850e2_mnem + ["CAXI", "DIVQ", "DIVQU", "EIRET", "FERET", "FETRAP", "RIE", "SYNCE", "SYNCM", "SYNCP",
                              "SYSCALL"]
v850e2m_mnem = v850e2s_mnem + ["ABSF_D", "ABSF_S", "ADDF_D", "ADDF_S",
                               "CEILF_DL", "CEILF_DUL", "CEILF_DUW", "CEILF_DW",
                               "CEILF_SL", "CEILF_SUL", "CEILF_SUW", "CEILF_SW",
                               "CMOVF_D", "CMOVF_S", "CMPF_D", "CMPF_S",
                               "CVTF_DL", "CVTF_DS", "CVTF_DUL", "CVTF_DUW",
                               "CVTF_DW", "CVTF_LD", "CVTF_LS", "CVTF_SD",
                               "CVTF_SL", "CVTF_SUL", "CVTF_SUW", "CVTF_SW",
                               "CVTF_ULD", "CVTF_ULS", "CVTF_UWD", "CVTF_UWS",
                               "CVTF_WD", "CVTF_WS", "DIVF_D", "DIVF_S",
                               "FLOORF_DL", "FLOORF_DUL", "FLOORF_DUW", "FLOORF_DW",
                               "FLOORF_SL", "FLOORF_SUL", "FLOORF_SUW", "FLOORF_SW",
                               "MADDF_S",
                               "MAXF_D", "MAXF_S", "MINF_D", "MINF_S",
                               "MSUBF_S", "MULF_D", "MULF_S", "NEGF_D", "NEGF_S",
                               "NMADDF_S", "NMSUBF_S", "RECIPF_D", "RECIPF_S",
                               "RSQRTF_D", "RSQRTF_S", "SQRTF_D", "SQRTF_S",
                               "TRFSR",
                               "TRNCF_DL", "TRNCF_DUL", "TRNCF_DUW", "TRNCF_DW",
                               "TRNCF_SL", "TRNCF_SUL", "TRNCF_SUW", "TRNCF_SW",
                               ]
rh850g3m_mnem = v850e2m_mnem + ["FMAF_S", "FMSF_S", "FNMAF_S", "FNMSF_S", "CVTF_HS", "CVTF_SH"] \
                + ["BINS", "ROTL", "LOOP", "CLL", "PUSHSP", "POPSP", "SNOOZE", "LDL_W", "STC_W", "SYNCI",
                   "CACHE", "PREF"]
V850 = IntEnum("V850", [(n, i) for i, n in enumerate(v850_mnem)])
V850E = IntEnum("V850E", [(n, i) for i, n in enumerate(v850es_mnem)])
V850E2 = IntEnum("V850E2", [(n, i) for i, n in enumerate(v850e2_mnem)])
V850E2S = IntEnum("V850E2S", [(n, i) for i, n in enumerate(v850e2s_mnem)])
V850E2M = IntEnum("V850E2M", [(n, i) for i, n in enumerate(v850e2m_mnem)])
RH850G3M = IntEnum("RH850G2M", [(n, i) for i, n in enumerate(rh850g3m_mnem)])


class Subarch(Enum):
    Unknown = 0
    V850 = 1
    V850E = 2
    V850ES = 3
    V850E2 = 4
    V850E2S = 5
    V850E2M = 6
    RH850 = 8


MNEM = RH850G3M


def guess_subarch(mnem: MNEM):
    if MNEM.ADD.value <= mnem.value <= MNEM.XORI.value:
        return Subarch.V850
    elif MNEM.BSH.value <= mnem.value <= MNEM.ZXH.value:
        return Subarch.V850E
    elif mnem in [MNEM.DBRET, MNEM.DBTRAP]:
        return Subarch.V850ES
    elif MNEM.ADF.value <= mnem.value <= MNEM.SCH1R.value:
        return Subarch.V850E2
    elif MNEM.CAXI.value <= mnem.value <= MNEM.SYSCALL.value:
        return Subarch.V850E2S
    elif MNEM.ABSF_D.value <= mnem.value <= MNEM.TRNCF_SW.value:
        return Subarch.V850E2S
    elif MNEM.FMAF_S.value <= mnem.value <= MNEM.PREF.value:
        return Subarch.RH850
    return Subarch.Unknown


def check_subarch(subarch: Subarch, mnem: MNEM):
    assert subarch != Subarch.Unknown
    guess = guess_subarch(mnem)
    if guess == Subarch.Unknown:
        return False
    if guess.value <= subarch.value:
        if Subarch.V850E2.value <= subarch.value:
            return guess.value != Subarch.V850ES
        else:
            return True
    return False


COND = IntEnum("COND", zip(["V", "L", "Z", "NH", "N", "R", "LT", "LE",
                            "NV", "NL", "NZ", "H", "P", "SA", "GE", "GT"],
                           range(16)))

FCOND = IntEnum("FCOND", zip(["F", "UN", "EQ", "UEQ", "OLT", "ULT", "OLE", "ULE",
                              "SF", "NGLE", "SEQ", "NGL", "LT", "NGE", "LE", "NGT"],
                             range(16)))

CACHEOP = IntEnum("CACHEOP", ["INVALID", "CHBII", "CIBII", "CFALI", "CISTI", "CILDI", "CLL"])
PREFOP = IntEnum("PREFOP", ["INVALID", "PREFI"])
