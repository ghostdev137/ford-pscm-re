
#include "nec850.h"
#include "binaryninjaapi.h"
#include <vector>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include "disass.h"
#include "binaryninjaapi.h"
#include "binaryninjacore.h"
#include "lowlevelilinstruction.h"

using namespace BinaryNinja;
using namespace std;

static const char *reg_name[] = {
	"r0",
	"r1",
	"r2",
	"sp",
	"gp",
	"tp",
	"r6",
	"r7",
	"r8",
	"r9",
	"r10",
	"r11",
	"r12",
	"r13",
	"r14",
	"r15",
	"r16",
	"r17",
	"r18",
	"r19",
	"r20",
	"r21",
	"r22",
	"r23",
	"r24",
	"r25",
	"r26",
	"r27",
	"r28",
	"r29",
	"ep",
	"lp",
	"pc"};

static const char *cccc_name[] = {
	"v",
	"c/l",
	"z",
	"nh",
	"s/n",
	"t",
	"lt",
	"le",
	"nv",
	"nc/nl",
	"nz",
	"h",
	"ns/p",
	"INVALID",
	"ge",
	"gt"};

static const char *cond_name[] = {
	"f",
	"un",
	"eq",
	"ueq",
	"olt",
	"ult",
	"ole",
	"ule",
	"sf",
	"ngle",
	"seq",
	"ngl",
	"lt",
	"nge",
	"le",
	"ngt"};

static const char *reg_list_names[] = {
	"r24",
	"r25",
	"r26",
	"r27",
	"r20",
	"r21",
	"r22",
	"r23",
	"r28",
	"r29",
	"lp",
	"ep",
};

static const int reg_list_regs[] = {
	NEC_REG_R24,
	NEC_REG_R25,
	NEC_REG_R26,
	NEC_REG_R27,
	NEC_REG_R20,
	NEC_REG_R21,
	NEC_REG_R22,
	NEC_REG_R23,
	NEC_REG_R28,
	NEC_REG_R29,
	NEC_REG_LP,
	NEC_REG_EP
};

class NEC850 : public Architecture
{
private:
	BNEndianness endian;

	/* this can maybe be moved to the API later */
	BNRegisterInfo RegisterInfo(uint32_t fullWidthReg, size_t offset, size_t size, bool zeroExtend = false)
	{
		BNRegisterInfo result;
		result.fullWidthRegister = fullWidthReg;
		result.offset = offset;
		result.size = size;
		result.extend = zeroExtend ? ZeroExtendToFullWidth : NoExtend;
		return result;
	}

public:
	/* initialization list */
	NEC850(const char *name) : Architecture(name)
	{
	}

	/*************************************************************************/

	std::string GetSysregName(int sysreg_id)
	{
		switch (sysreg_id)
		{
		case NEC_SYSREG_EIPC:
			return "eipc";
		case NEC_SYSREG_EIPSW:
			return "eipsw";
		case NEC_SYSREG_FEPC:
			return "fepc";
		case NEC_SYSREG_FEPSW:
			return "fepsw";
		case NEC_SYSREG_PSW:
			return "psw";
		case NEC_SYSREG_FPSR:
			return "fpsr";
		case NEC_SYSREG_FPEPC:
			return "fpepc";
		case NEC_SYSREG_FPST:
			return "fpst";
		case NEC_SYSREG_FPCC:
			return "fpcc";
		case NEC_SYSREG_FPCFG:
			return "fpcfg";
		case NEC_SYSREG_FPEC:
			return "fpec";
		case NEC_SYSREG_EIIC:
			return "eiic";
		case NEC_SYSREG_FEIC:
			return "feic";
		case NEC_SYSREG_CTPC:
			return "ctpc";
		case NEC_SYSREG_CTPSW:
			return "ctpsw";
		case NEC_SYSREG_CTBP:
			return "ctbp";
		case NEC_SYSREG_EIWR:
			return "eiwr";
		case NEC_SYSREG_FEWR:
			return "fewr";
		case NEC_SYSREG_BSEL:
			return "bsel";
		case NEC_SYSREG_MCFG0:
			return "mcfg0";
		case NEC_SYSREG_RBASE:
			return "rbase";
		case NEC_SYSREG_EBASE:
			return "ebase";
		case NEC_SYSREG_INTBP:
			return "intbp";
		case NEC_SYSREG_MCTL:
			return "mctl";
		case NEC_SYSREG_PID:
			return "pid";
		case NEC_SYSREG_SCCFG:
			return "sccfg";
		case NEC_SYSREG_SCBP:
			return "scbp";
		case NEC_SYSREG_HTCFG0:
			return "htcfg0";
		case NEC_SYSREG_MEA:
			return "mea";
		case NEC_SYSREG_ASID:
			return "asid";
		case NEC_SYSREG_MEI:
			return "mei";
		default:
			return "INVALID";
		}
	}

	virtual BNEndianness GetEndianness() const override
	{
		// MYLOG("%s()\n", __func__);
		return LittleEndian;
	}

	virtual size_t GetAddressSize() const override
	{
		// MYLOG("%s()\n", __func__);
		return 4;
	}

	virtual size_t GetDefaultIntegerSize() const override
	{
		return 4;
	}

	virtual size_t GetInstructionAlignment() const override
	{
		return 2;
	}

	virtual size_t GetMaxInstructionLength() const override
	{
		return 8;
	}

	virtual vector<uint32_t> GetAllFlags() override
	{
		return vector<uint32_t>{
			FLAG_SAT,
			FLAG_CY,
			FLAG_OV,
			FLAG_S,
			FLAG_Z};
	}

	virtual string GetFlagName(uint32_t flag) override
	{
		switch (flag)
		{
		case FLAG_SAT:
			return "sat";
		case FLAG_CY:
			return "cy";
		case FLAG_OV:
			return "ov";
		case FLAG_S:
			return "s";
		case FLAG_Z:
			return "z";
		default:
			return "ERR_FLAG_NAME";
		}
	}

	virtual vector<uint32_t> GetAllFlagWriteTypes() override
	{
		return vector<uint32_t>{
			FLAG_WRITE_NONE,
			FLAG_WRITE_ALL,
			FLAG_WRITE_OVSZ,
			FLAG_WRITE_Z,
			FLAG_WRITE_SZ,
			FLAG_WRITE_CYSZ};
	}

	virtual string GetFlagWriteTypeName(uint32_t writeType) override
	{
		switch (writeType)
		{
		case FLAG_WRITE_CYSZ:
			return "cysz";
		case FLAG_WRITE_SZ:
			return "sz";
		case FLAG_WRITE_OVSZ:
			return "ovsz";
		case FLAG_WRITE_CYOVSZ:
			return "cyovsz";
		case FLAG_WRITE_Z:
			return "z";
		case FLAG_WRITE_ALL:
			return "*";
		default:
			return "none";
		}
	}

	virtual vector<uint32_t> GetFlagsWrittenByFlagWriteType(uint32_t writeType) override
	{
		switch (writeType)
		{
		case FLAG_WRITE_CYSZ:
			return vector<uint32_t>{
				FLAG_CY, FLAG_Z, FLAG_S};
		case FLAG_WRITE_SZ:
			return vector<uint32_t>{
				FLAG_Z, FLAG_S};
		case FLAG_WRITE_OVSZ:
			return vector<uint32_t>{
				FLAG_Z, FLAG_S, FLAG_OV};
		case FLAG_WRITE_CYOVSZ:
			return vector<uint32_t>{
				FLAG_Z, FLAG_S, FLAG_OV, FLAG_CY};
		case FLAG_WRITE_ALL:
			return vector<uint32_t>{
				FLAG_CY, FLAG_Z, FLAG_OV, FLAG_S};
		case FLAG_WRITE_Z:
			return vector<uint32_t>{
				FLAG_Z};
		default:
			return vector<uint32_t>();
		}
	}

	virtual BNFlagRole GetFlagRole(uint32_t flag, uint32_t semClass) override
	{
		bool signedClass = true;

		switch (flag)
		{
		case FLAG_SAT:
			return SpecialFlagRole;
		case FLAG_CY:
			return CarryFlagRole;
		case FLAG_Z:
			return ZeroFlagRole;
		case FLAG_OV:
			return OverflowFlagRole;
		case FLAG_S:
			return NegativeSignFlagRole;
		default:
			return SpecialFlagRole;
		}
	}

	virtual vector<uint32_t> GetFlagsRequiredForFlagCondition(BNLowLevelILFlagCondition cond, uint32_t) override
	{

		switch (cond)
		{
		case LLFC_E:  /* equal */
		case LLFC_NE: /* not equal */
			return vector<uint32_t>{FLAG_Z};

		case LLFC_ULT: /* (unsigned) less than == LT */
		case LLFC_UGE: /* (unsigned) greater-or-equal == !LT */
			return vector<uint32_t>{FLAG_CY};

		case LLFC_UGT: /* (unsigned) greater-than == GT */
		case LLFC_ULE: /* (unsigned) less-or-equal == !GT */
			return vector<uint32_t>{FLAG_CY, FLAG_Z};

		case LLFC_SLT: /* (signed) less than == LT */
		case LLFC_SGE: /* (signed) greater-or-equal == !LT */
			return vector<uint32_t>{FLAG_S, FLAG_OV};

		case LLFC_SGT: /* (signed) greater-than == GT */
		case LLFC_SLE: /* (signed) lesser-or-equal == !GT */
			return vector<uint32_t>{FLAG_S, FLAG_OV, FLAG_Z};

		case LLFC_NEG:
		case LLFC_POS:
			return vector<uint32_t>{FLAG_S};

		case LLFC_O:
		case LLFC_NO:
			return vector<uint32_t>{
				FLAG_OV};

		default:
			return vector<uint32_t>();
		}
	}

	virtual vector<uint32_t> GetFullWidthRegisters() override
	{

		return vector<uint32_t>{
			NEC_REG_R0, NEC_REG_R1, NEC_REG_R2, NEC_REG_SP, NEC_REG_R4, NEC_REG_R5, NEC_REG_R6, NEC_REG_R7,
			NEC_REG_R8, NEC_REG_R9, NEC_REG_R10, NEC_REG_R11, NEC_REG_R12, NEC_REG_R13, NEC_REG_R14, NEC_REG_R15,
			NEC_REG_R16, NEC_REG_R17, NEC_REG_R18, NEC_REG_R19, NEC_REG_R20, NEC_REG_R21, NEC_REG_R22, NEC_REG_R23,
			NEC_REG_R24, NEC_REG_R25, NEC_REG_R26, NEC_REG_R27, NEC_REG_R28, NEC_REG_R29, NEC_REG_EP, NEC_REG_LP, NEC_REG_PC};
	}

	virtual vector<uint32_t> GetAllRegisters() override
	{
		vector<uint32_t> result = {
			NEC_REG_R0, NEC_REG_R1, NEC_REG_R2, NEC_REG_SP, NEC_REG_R4, NEC_REG_R5, NEC_REG_R6, NEC_REG_R7,
			NEC_REG_R8, NEC_REG_R9, NEC_REG_R10, NEC_REG_R11, NEC_REG_R12, NEC_REG_R13, NEC_REG_R14, NEC_REG_R15,
			NEC_REG_R16, NEC_REG_R17, NEC_REG_R18, NEC_REG_R19, NEC_REG_R20, NEC_REG_R21, NEC_REG_R22, NEC_REG_R23,
			NEC_REG_R24, NEC_REG_R25, NEC_REG_R26, NEC_REG_R27, NEC_REG_R28, NEC_REG_R29, NEC_REG_EP, NEC_REG_LP, NEC_REG_PC,
			// system registers
			NEC_SYSREG_EIPC,
			NEC_SYSREG_EIPSW,
			NEC_SYSREG_FEPC,
			NEC_SYSREG_FEPSW,
			NEC_SYSREG_PSW,
			NEC_SYSREG_FPSR,
			NEC_SYSREG_FPEPC,
			NEC_SYSREG_FPST,
			NEC_SYSREG_FPCC,
			NEC_SYSREG_FPCFG,
			NEC_SYSREG_FPEC,
			NEC_SYSREG_EIIC,
			NEC_SYSREG_FEIC,
			NEC_SYSREG_CTPC,
			NEC_SYSREG_CTPSW,
			NEC_SYSREG_CTBP,
			NEC_SYSREG_EIWR,
			NEC_SYSREG_FEWR,
			NEC_SYSREG_BSEL,
			NEC_SYSREG_MCFG0,
			NEC_SYSREG_RBASE,
			NEC_SYSREG_EBASE,
			NEC_SYSREG_INTBP,
			NEC_SYSREG_MCTL,
			NEC_SYSREG_PID,
			NEC_SYSREG_SCCFG,
			NEC_SYSREG_SCBP,
			NEC_SYSREG_HTCFG0,
			NEC_SYSREG_MEA,
			NEC_SYSREG_ASID,
			NEC_SYSREG_MEI};

		return result;
	}

	virtual vector<uint32_t> GetSystemRegisters() override
	{
		vector<uint32_t> result = {
			NEC_SYSREG_EIPC,
			NEC_SYSREG_EIPSW,
			NEC_SYSREG_FEPC,
			NEC_SYSREG_FEPSW,
			NEC_SYSREG_PSW,
			NEC_SYSREG_FPSR,
			NEC_SYSREG_FPEPC,
			NEC_SYSREG_FPST,
			NEC_SYSREG_FPCC,
			NEC_SYSREG_FPCFG,
			NEC_SYSREG_FPEC,
			NEC_SYSREG_EIIC,
			NEC_SYSREG_FEIC,
			NEC_SYSREG_CTPC,
			NEC_SYSREG_CTPSW,
			NEC_SYSREG_CTBP,
			NEC_SYSREG_EIWR,
			NEC_SYSREG_FEWR,
			NEC_SYSREG_BSEL,
			NEC_SYSREG_MCFG0,
			NEC_SYSREG_RBASE,
			NEC_SYSREG_EBASE,
			NEC_SYSREG_INTBP,
			NEC_SYSREG_MCTL,
			NEC_SYSREG_PID,
			NEC_SYSREG_SCCFG,
			NEC_SYSREG_SCBP,
			NEC_SYSREG_HTCFG0,
			NEC_SYSREG_MEA,
			NEC_SYSREG_ASID,
			NEC_SYSREG_MEI

		};

		return result;
	}

	virtual std::vector<uint32_t> GetGlobalRegisters() override
	{
		return vector<uint32_t>{NEC_REG_PC};
	}

	virtual string GetRegisterName(uint32_t regId) override
	{
		const char *result;

		if (regId >= NEC_REG_R0 && regId <= NEC_REG_PC)
			result = reg_name[regId];
		else if (regId >= NEC_SYSREG_EIPC && regId <= NEC_SYSREG_MEI)
			return GetSysregName(regId);
		else
			result = "";
		return result;
	}

	ExprId get_reg(LowLevelILFunction &il, int reg_id, int size) {
		if (reg_id == 0)
			return il.Const(size, 0);
		else
			return il.Register(size, reg_id);
	}

	virtual BNRegisterInfo GetRegisterInfo(uint32_t regId) override
	{
		switch (regId)
		{
			// BNRegisterInfo RegisterInfo(uint32_t fullWidthReg, size_t offset,
			//   size_t size, bool zeroExtend = false)

		case NEC_REG_R0:
			return RegisterInfo(NEC_REG_R0, 0, 4);
		case NEC_REG_R1:
			return RegisterInfo(NEC_REG_R1, 0, 4);
		case NEC_REG_R2:
			return RegisterInfo(NEC_REG_R2, 0, 4);
		case NEC_REG_SP:
			return RegisterInfo(NEC_REG_SP, 0, 4);
		case NEC_REG_R4:
			return RegisterInfo(NEC_REG_R4, 0, 4);
		case NEC_REG_R5:
			return RegisterInfo(NEC_REG_R5, 0, 4);
		case NEC_REG_R6:
			return RegisterInfo(NEC_REG_R6, 0, 4);
		case NEC_REG_R7:
			return RegisterInfo(NEC_REG_R7, 0, 4);
		case NEC_REG_R8:
			return RegisterInfo(NEC_REG_R8, 0, 4);
		case NEC_REG_R9:
			return RegisterInfo(NEC_REG_R9, 0, 4);
		case NEC_REG_R10:
			return RegisterInfo(NEC_REG_R10, 0, 4);
		case NEC_REG_R11:
			return RegisterInfo(NEC_REG_R11, 0, 4);
		case NEC_REG_R12:
			return RegisterInfo(NEC_REG_R12, 0, 4);
		case NEC_REG_R13:
			return RegisterInfo(NEC_REG_R13, 0, 4);
		case NEC_REG_R14:
			return RegisterInfo(NEC_REG_R14, 0, 4);
		case NEC_REG_R15:
			return RegisterInfo(NEC_REG_R15, 0, 4);
		case NEC_REG_R16:
			return RegisterInfo(NEC_REG_R16, 0, 4);
		case NEC_REG_R17:
			return RegisterInfo(NEC_REG_R17, 0, 4);
		case NEC_REG_R18:
			return RegisterInfo(NEC_REG_R18, 0, 4);
		case NEC_REG_R19:
			return RegisterInfo(NEC_REG_R19, 0, 4);
		case NEC_REG_R20:
			return RegisterInfo(NEC_REG_R20, 0, 4);
		case NEC_REG_R21:
			return RegisterInfo(NEC_REG_R21, 0, 4);
		case NEC_REG_R22:
			return RegisterInfo(NEC_REG_R22, 0, 4);
		case NEC_REG_R23:
			return RegisterInfo(NEC_REG_R23, 0, 4);
		case NEC_REG_R24:
			return RegisterInfo(NEC_REG_R24, 0, 4);
		case NEC_REG_R25:
			return RegisterInfo(NEC_REG_R25, 0, 4);
		case NEC_REG_R26:
			return RegisterInfo(NEC_REG_R26, 0, 4);
		case NEC_REG_R27:
			return RegisterInfo(NEC_REG_R27, 0, 4);
		case NEC_REG_R28:
			return RegisterInfo(NEC_REG_R28, 0, 4);
		case NEC_REG_R29:
			return RegisterInfo(NEC_REG_R29, 0, 4);
		case NEC_REG_EP:
			return RegisterInfo(NEC_REG_EP, 0, 4);
		case NEC_REG_LP:
			return RegisterInfo(NEC_REG_LP, 0, 4);
		case NEC_REG_PC:
			return RegisterInfo(NEC_REG_PC, 0, 4);
		case NEC_SYSREG_EIPC:
			return RegisterInfo(NEC_SYSREG_EIPC, 0, 4);
		case NEC_SYSREG_EIPSW:
			return RegisterInfo(NEC_SYSREG_EIPSW, 0, 4);
		case NEC_SYSREG_FEPC:
			return RegisterInfo(NEC_SYSREG_FEPC, 0, 4);
		case NEC_SYSREG_FEPSW:
			return RegisterInfo(NEC_SYSREG_FEPSW, 0, 4);
		case NEC_SYSREG_PSW:
			return RegisterInfo(NEC_SYSREG_PSW, 0, 4);
		case NEC_SYSREG_FPSR:
			return RegisterInfo(NEC_SYSREG_FPSR, 0, 4);
		case NEC_SYSREG_FPEPC:
			return RegisterInfo(NEC_SYSREG_FPEPC, 0, 4);
		case NEC_SYSREG_FPST:
			return RegisterInfo(NEC_SYSREG_FPST, 0, 4);
		case NEC_SYSREG_FPCC:
			return RegisterInfo(NEC_SYSREG_FPCC, 0, 4);
		case NEC_SYSREG_FPCFG:
			return RegisterInfo(NEC_SYSREG_FPCFG, 0, 4);
		case NEC_SYSREG_FPEC:
			return RegisterInfo(NEC_SYSREG_FPEC, 0, 4);
		case NEC_SYSREG_EIIC:
			return RegisterInfo(NEC_SYSREG_EIIC, 0, 4);
		case NEC_SYSREG_FEIC:
			return RegisterInfo(NEC_SYSREG_FEIC, 0, 4);
		case NEC_SYSREG_CTPC:
			return RegisterInfo(NEC_SYSREG_CTPC, 0, 4);
		case NEC_SYSREG_CTPSW:
			return RegisterInfo(NEC_SYSREG_CTPSW, 0, 4);
		case NEC_SYSREG_CTBP:
			return RegisterInfo(NEC_SYSREG_CTBP, 0, 4);
		case NEC_SYSREG_EIWR:
			return RegisterInfo(NEC_SYSREG_EIWR, 0, 4);
		case NEC_SYSREG_FEWR:
			return RegisterInfo(NEC_SYSREG_FEWR, 0, 4);
		case NEC_SYSREG_BSEL:
			return RegisterInfo(NEC_SYSREG_BSEL, 0, 4);
		case NEC_SYSREG_MCFG0:
			return RegisterInfo(NEC_SYSREG_MCFG0, 0, 4);
		case NEC_SYSREG_RBASE:
			return RegisterInfo(NEC_SYSREG_RBASE, 0, 4);
		case NEC_SYSREG_EBASE:
			return RegisterInfo(NEC_SYSREG_EBASE, 0, 4);
		case NEC_SYSREG_INTBP:
			return RegisterInfo(NEC_SYSREG_INTBP, 0, 4);
		case NEC_SYSREG_MCTL:
			return RegisterInfo(NEC_SYSREG_MCTL, 0, 4);
		case NEC_SYSREG_PID:
			return RegisterInfo(NEC_SYSREG_PID, 0, 4);
		case NEC_SYSREG_SCCFG:
			return RegisterInfo(NEC_SYSREG_SCCFG, 0, 4);
		case NEC_SYSREG_SCBP:
			return RegisterInfo(NEC_SYSREG_SCBP, 0, 4);
		case NEC_SYSREG_HTCFG0:
			return RegisterInfo(NEC_SYSREG_HTCFG0, 0, 4);
		case NEC_SYSREG_MEA:
			return RegisterInfo(NEC_SYSREG_MEA, 0, 4);
		case NEC_SYSREG_ASID:
			return RegisterInfo(NEC_SYSREG_ASID, 0, 4);
		case NEC_SYSREG_MEI:
			return RegisterInfo(NEC_SYSREG_MEI, 0, 4);
		default:
			// LogError("%s(%d == \"%s\") invalid argument", __func__,
			//   regId, powerpc_reg_to_str(regId));
			return RegisterInfo(0, 0, 0);
		}
	}

	virtual uint32_t GetStackPointerRegister() override
	{
		return NEC_REG_SP;
	}

	virtual uint32_t GetLinkRegister() override
	{
		return NEC_REG_LP;
	}


virtual std::string GetIntrinsicName (uint32_t intrinsic) override {
         switch (intrinsic)  {
            case SCH1L_INTRINSIC:
                return "_CountLeadingZeros";
            case SCH1R_INTRINSIC:
                return "_CountTrailingZeros";
            case SCH0L_INTRINSIC:
                return "_CountLeadingOnes";
			case SCH0R_INTRINSIC:
                return "_CountTrailingOnes";
			case SYNC_MEMORY_ACCESS:
                return "_SynchornizeMemoryAccess";
			case SYNC_PIPELINE:
                return "_SynchornizePipeline";
			case SYNC_INSN_FETCHER:
                return "_SynchornizeInstructionFetcher";
			case SYNC_EXCEPTIONS:
                return "_SynchornizeExceptions";
			case CLL_INTRINSIC:
                return "_ClearAtomicManipulationLink";
			case SNOOZE_INTRINSIC:
                return "_ClearAtomicManipulationLink";
			case DI_INTRINSIC:
                return "_DisableEILevelMaskableInterrupt";
			case EI_INTRINSIC:
                return "_EnableEILevelMaskableException";
			case HALT_INTRINSIC:
                return "_HaltCPU";
			case RIE_INTRINSIC:
                return "_ReservedInstructionException";
            default:
                return "";
            }
    }

    virtual std::vector<uint32_t> GetAllIntrinsics() override {
        return vector<uint32_t> {
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
    }

    virtual std::vector<NameAndType> GetIntrinsicInputs (uint32_t intrinsic) override {
        switch (intrinsic)
            {
                case SCH1L_INTRINSIC:
                    return {
                        NameAndType("WORD", Type::IntegerType(4, false))
                    };
                case SCH1R_INTRINSIC:
                    return {
                        NameAndType("WORD", Type::IntegerType(4, false))
                    };
                case SCH0L_INTRINSIC:
                    return {
                        NameAndType("WORD", Type::IntegerType(4, false))
                    };
				case SCH0R_INTRINSIC:
                    return {
                        NameAndType("WORD", Type::IntegerType(4, false))
                    };
				case SYNC_MEMORY_ACCESS:
                    return {  };
				case SYNC_PIPELINE:
                    return {  };
				case SYNC_INSN_FETCHER:
                    return {  };
				case SYNC_EXCEPTIONS:
                    return {  };
				case CLL_INTRINSIC:
                    return { };
				case SNOOZE_INTRINSIC:
                    return { };
				case DI_INTRINSIC:
                    return {  };
				case EI_INTRINSIC:
                    return {  };
				case HALT_INTRINSIC:
                    return {  };
				case RIE_INTRINSIC:
                    return {  };
                default:
                    return vector<NameAndType>();
            }
    }

    virtual std::vector<Confidence<Ref<Type>>> GetIntrinsicOutputs (uint32_t intrinsic) override {
        switch (intrinsic)
            {
                case SCH1L_INTRINSIC:
                    return { Type::IntegerType(4, false) };
                case SCH1R_INTRINSIC:
                    return { Type::IntegerType(4, false) };
				case SCH0L_INTRINSIC:
                    return { Type::IntegerType(4, false) };
				case SCH0R_INTRINSIC:
                    return { Type::IntegerType(4, false) };
				case SYNC_MEMORY_ACCESS:
                    return { };
				case SYNC_PIPELINE:
                    return { };
				case SYNC_INSN_FETCHER:
                    return { };
				case SYNC_EXCEPTIONS:
                    return { };
				case CLL_INTRINSIC:
                    return { };
				case SNOOZE_INTRINSIC:
                    return { };
				case DI_INTRINSIC:
                    return {  };
				case EI_INTRINSIC:
                    return {  };
				case HALT_INTRINSIC:
                    return {  };
				case RIE_INTRINSIC:
                    return {  };
                default:
                    return vector<Confidence<Ref<Type>>>();
            }
    }

	virtual bool GetInstructionLowLevelIL(const uint8_t *data, uint64_t addr, size_t &len, LowLevelILFunction &il) override
	{
		insn_t *insn;
		if ((insn = disassemble(data)))
		{
			len = insn->size;
			BNLowLevelILLabel *true_label = NULL;
			BNLowLevelILLabel *false_label = NULL;
			LowLevelILLabel true_tag;
			LowLevelILLabel false_tag;
			LowLevelILLabel end_tag;
			ExprId condition;
			switch (insn->insn_id)
			{
			case N850_ABSFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatAbs(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_ADD:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_ADD_IMM:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								il.Const(
									1,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_ADDFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatAdd(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_ADF:
			{
				if (insn->fields[0].value == 5) {
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.Add(
								4,
								il.Add(
									4,
									this->get_reg(il,insn->fields[2].value,4),
									this->get_reg(il,insn->fields[1].value,4)
								),
								il.Const(
									4,
									1
								),
								FLAG_WRITE_CYOVSZ

							)
							
						)
					);
				} else {
					switch (insn->fields[0].value)
					{
					case 2:
						condition = il.FlagCondition(LLFC_E);
						break;
					case 10:
						condition = il.FlagCondition(LLFC_NE);
						break;
					case 11:
						condition = il.FlagCondition(LLFC_UGT);
						break;
					case 3:
						condition = il.FlagCondition(LLFC_ULE);
						break;
					case 0:
						condition = il.FlagCondition(LLFC_O);
						break;
					case 8:
						condition = il.FlagCondition(LLFC_NO);
						break;
					case 1:
						condition = il.FlagCondition(LLFC_ULT);
						break;
					case 9:
						condition = il.FlagCondition(LLFC_UGE);
						break;
					case 6:
						condition = il.FlagCondition(LLFC_SLT);
						break;
					case 14:
						condition = il.FlagCondition(LLFC_SGE);
						break;
					case 7:
						condition = il.FlagCondition(LLFC_SLE);
						break;
					case 15:
						condition = il.FlagCondition(LLFC_SGT);
						break;
					case 4:
						condition = il.FlagCondition(LLFC_NEG);
						break;
					case 12:
						condition = il.FlagCondition(LLFC_POS);
						break;
					default:
						break;
					}
					
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
						il.AddInstruction(
							il.SetRegister(
								4,
								insn->fields[3].value,
								il.Add(
									4,
									il.Add(
										4,
										this->get_reg(il,insn->fields[2].value,4),
										this->get_reg(il,insn->fields[1].value,4)
									),
									il.Const(
										4,
										1
									),
									FLAG_WRITE_CYOVSZ

								)
								
							)
						);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.Add(
								4,
								this->get_reg(il,insn->fields[2].value,4),
								this->get_reg(il,insn->fields[1].value,4),
								FLAG_WRITE_CYOVSZ
							)
						)
					);
					il.MarkLabel(end_tag);

				}
				
			}
			break;
			case N850_ADDI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_AND:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.And(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_ANDI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.And(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_BGE:
			case N850_BGE_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_SGE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BGT:
			case N850_BGT_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_SGT);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BLE:
			case N850_BLE_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_SLE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BLT:
			case N850_BLT_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_SLT);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BH:
			case N850_BH_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_UGT);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BL:
			case N850_BL_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_ULT);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BNH:
			case N850_BNH_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_ULE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BNL:
			case N850_BNL_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_UGE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BE:
			case N850_BE_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_E);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));


				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BNE:
			case N850_BNE_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_NE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BC:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_ULT);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BN:
			case N850_BN_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_NEG);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BNC:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_UGE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BNV:
			case N850_BNV_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_NO);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BNZ:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_NE);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BP:
			case N850_BP_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_POS);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BR:
			case N850_BR_L:
			{
				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));
			}
			break;
			case N850_BSA:
			case N850_BSA_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.Flag(FLAG_SAT);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));
			
				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BV:
			case N850_BV_L:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_O);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));
				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BZ:
			{
				// True branch
				true_label = il.GetLabelForAddress(this, insn->fields[0].value);
				// False Branch
				false_label = il.GetLabelForAddress(this, ((uint32_t) addr + insn->size));
				condition = il.FlagCondition(LLFC_E);
				if (true_label && false_label)
					il.AddInstruction(il.If(condition,*true_label,*false_label));            
				else if (true_label)
					il.AddInstruction(il.If(condition,*true_label,false_tag));
				else if (false_label)
					il.AddInstruction(il.If(condition,true_tag,*false_label));
				else
					il.AddInstruction(il.If(condition,true_tag,false_tag));

				if (!true_label) {
					il.MarkLabel(true_tag);
				}

				il.AddInstruction(il.Jump(il.ConstPointer(4,(insn->fields[0].value + addr) & 0xFFFFFFFF)));

				if (!false_label) {
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_BSH:
			{
				// TODO test
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Or(
							4,
							il.Or(
								4,
								il.ShiftLeft(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff
										)
									),
									il.Const(
										4,
										8
									)
								),
								il.LogicalShiftRight(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff00
										)
									),
									il.Const(
										4,
										8
									)
								)

							),
							il.Or(
								4,
								il.LogicalShiftRight(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff000000
										)
									),
									il.Const(
										4,
										8
									)
								),
								il.ShiftLeft(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff0000
										)
									),
									il.Const(
										4,
										8
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_BINS:
			{
				// TODO check disassembly again
				// 🚫001ac798  bins          r29, 0x10, 0x8, r8
				// 🚫001ac798  bins          r29, 0x10, 0x7, r8
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[3].value,
						il.Or(
							4,
							il.And(
								4,
								this->get_reg(il,insn->fields[3].value,4),
								il.Const(
									4,
									((0xffffffff << (insn->fields[1].value + insn->fields[2].value)) & 0xffffffff | (0xffffffff >> (32 - insn->fields[1].value))) & 0xffffffff
								)
							),
							il.And(
								4,
								this->get_reg(il,insn->fields[0].value,4),
								il.Const(
									4,
									(0xffffffff >> (32 - insn->fields[2].value) << insn->fields[1].value) & 0xffffffff
								)
							)
						)
					)
				);
			}
			break;
			case N850_BINS2:
			{
				// 🚫0012ab84  bins          r2, 0xf, 0x3, r1
				// 🚫0012ab84  bins          r2, 0xf, 0x1, r1 - RAW
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[3].value,
						il.Or(
							4,
							il.And(
								4,
								this->get_reg(il,insn->fields[3].value,4),
								il.Const(
									4,
									//(0xffffffff << (insn->fields[1].value + insn->fields[2].value - 1)) & 0xffffffff | (0xffffffff >> (31 - insn->fields[1].value))
									((0xffffffff << (insn->fields[1].value + insn->fields[2].value)) & 0xffffffff | (0xffffffff >> (32 - insn->fields[1].value))) & 0xffffffff
								)
							),
							il.And(
								4,
								this->get_reg(il,insn->fields[0].value,4),
								il.Const(
									4,
									//(0xffffffff >> (32 - insn->fields[2].value)) & 0xffffffff
									(0xffffffff >> (32 - insn->fields[2].value) << insn->fields[1].value) & 0xffffffff
								)
							)
						)
					)
				);
			}
			break;
			case N850_BINS3:
			{
				// 🚫0012a8b8  bins          r2, 0x0, 0x4, r1
				// 🚫0012a8b8  bins          r2, 0x0, 0x3, r1 - RAW
				/*
					pos = 1
					width = 2
					msb = pos + width - 1
					lsb = pos
				*/
				//LogInfo("BINS AT %x",addr); //  , 
				// 00152dd2: 
					//00152dd2  bins          r1, 0x2, 0x7, r2 - > RAW
					//00152dd2  bins          r1, 0x2, 0x6, r2

				// 008536ba:
					//008536ba  bins          r23, 0x8, 0xf, r15 -> RAW
					//008536ba  bins          r23, 0x8, 0x8, r15
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[3].value,
						il.Or(
							4,
							il.And(
								4,
								this->get_reg(il,insn->fields[3].value,4),
								il.Const(
									4,
									//(0xffffffff << (insn->fields[1].value + insn->fields[2].value - 1)) & 0xffffffff | (0xffffffff >> (31 - insn->fields[1].value))
									((0xffffffff << (insn->fields[1].value + insn->fields[2].value)) & 0xffffffff | (0xffffffff >> (32 - insn->fields[1].value))) & 0xffffffff
								)
							),
							il.And(
								4,
								this->get_reg(il,insn->fields[0].value,4),
								il.Const(
									4,
									//(0xffffffff >> (32 - insn->fields[2].value)) & 0xffffffff
									(0xffffffff >> (32 - insn->fields[2].value) << insn->fields[1].value) & 0xffffffff
								)
							)
						)
					)
				);
			}
			break;
			case N850_BSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Or(
							4,
							il.Or(
								4,
								il.ShiftLeft(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff
										)
									),
									il.Const(
										4,
										24
									)
								),
								il.ShiftLeft(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff00
										)
									),
									il.Const(
										4,
										8
									)
								)

							),
							il.Or(
								4,
								il.LogicalShiftRight(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff000000
										)
									),
									il.Const(
										4,
										24
									)
								),
								il.LogicalShiftRight(
									4,
									il.And(
										4,
										this->get_reg(il,insn->fields[0].value,4),
										il.Const(
											4,
											0xff0000
										)
									),
									il.Const(
										4,
										8
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_CALLT:
			{
				il.AddInstruction(
					il.Call(
						il.Load(
							4,
							il.Add(
								4,
								il.Register(
									4,
									NEC_SYSREG_CTBP
								),
								il.ZeroExtend(
									4,
									il.Const(
										1,
										insn->fields[0].value
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_CAXI:
			{
				// TODO not checked
				il.AddInstruction(
					il.If(
						il.CompareEqual(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.Load(
								4,
								this->get_reg(il,insn->fields[0].value,4)
							)
						),
						true_tag,
						false_tag
					)
				);
				il.MarkLabel(true_tag);
				il.AddInstruction(
					il.Store(
						4,
						this->get_reg(il,insn->fields[0].value,4),
						this->get_reg(il,insn->fields[2].value,4)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Load(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
				il.AddInstruction(il.Goto(end_tag));
				il.MarkLabel(false_tag);
				il.AddInstruction(
					il.Store(
						4,
						this->get_reg(il,insn->fields[0].value,4),
						il.Load(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Load(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
				il.MarkLabel(end_tag);
			}
			break;
			case N850_CEILFSL:
			{
				// TODO none of the CEILs are checked
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.Ceil(
							8,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CEILFSUL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.Ceil(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_CEILFSUW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Ceil(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CEILFSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Ceil(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CLL:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						CLL_INTRINSIC,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_CLR1:
			{
				il.AddInstruction(
					il.Store(
						1,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[1].value
								)
							)
						),
						il.And(
							1,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[2].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[1].value
										)
									)
								)
							),
							il.Const(
								1,
								~(1 << insn->fields[0].value) & 0xff
								//((1 << (instr->fields[4].value - instr->fields[3].value + 1)) - 1) << (31 - instr->fields[4].value)
							),
							FLAG_WRITE_Z
						)
						
					)
				);
			}
			break;
			case N850_CLR1R:
			{
				il.AddInstruction(
					il.Store(
						1,
						this->get_reg(il,insn->fields[1].value,4),
						il.And(
							1,
							il.Load(
								1,
								this->get_reg(il,insn->fields[1].value,4)
							),
							il.ShiftLeft(
								1,
								il.Const(
									1,
									1
								),
								this->get_reg(il,insn->fields[0].value,1)
							),
							FLAG_WRITE_Z
						)
					)
				);
			}
			break;
			case N850_CMOV:
			{
				if (insn->fields[0].value == 5) {
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							this->get_reg(il,insn->fields[1].value,4)
						)
					);
				} else {
					switch (insn->fields[0].value)
					{
					case 2:
						condition = il.FlagCondition(LLFC_E);
						break;
					case 10:
						condition = il.FlagCondition(LLFC_NE);
						break;
					case 11:
						condition = il.FlagCondition(LLFC_UGT);
						break;
					case 3:
						condition = il.FlagCondition(LLFC_ULE);
						break;
					case 0:
						condition = il.FlagCondition(LLFC_O);
						break;
					case 8:
						condition = il.FlagCondition(LLFC_NO);
						break;
					case 1:
						condition = il.FlagCondition(LLFC_ULT);
						break;
					case 9:
						condition = il.FlagCondition(LLFC_UGE);
						break;
					case 6:
						condition = il.FlagCondition(LLFC_SLT);
						break;
					case 14:
						condition = il.FlagCondition(LLFC_SGE);
						break;
					case 7:
						condition = il.FlagCondition(LLFC_SLE);
						break;
					case 15:
						condition = il.FlagCondition(LLFC_SGT);
						break;
					case 4:
						condition = il.FlagCondition(LLFC_NEG);
						break;
					case 12:
						condition = il.FlagCondition(LLFC_POS);
						break;
					case 13:
						condition = il.CompareEqual(
							4,
							il.Flag(
								FLAG_SAT
							),
							il.Const(
								4,
								1
							)
						);
						break;
					default:
						break;
					}
					
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							this->get_reg(il,insn->fields[1].value,4)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							this->get_reg(il,insn->fields[2].value,4)
						)
					);
					il.MarkLabel(end_tag);
				}
				
			}
			break;
			case N850_CMOVFS:
			{
				condition = il.CompareEqual(
					1,
					il.Register(4,NEC_SYSREG_FPSR),
					il.Const(
						1,
						insn->fields[0].value
					)
					
				);
				il.AddInstruction(il.If(condition,true_tag,false_tag));
				il.MarkLabel(true_tag);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[3].value,
						this->get_reg(il,insn->fields[1].value,4)
					)
				);
				il.AddInstruction(il.Goto(end_tag));
				il.MarkLabel(false_tag);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[3].value,
						this->get_reg(il,insn->fields[2].value,4)
					)
				);
				il.MarkLabel(end_tag);
			}
			break;
			case N850_CMOVI:
			{
				if (insn->fields[0].value == 5) {
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.SignExtend(
								4,
								il.Const(
									1,
									insn->fields[1].value
								)
							)
						)
					);
				} else {
					switch (insn->fields[0].value)
					{
					case 2:
						condition = il.FlagCondition(LLFC_E);
						break;
					case 10:
						condition = il.FlagCondition(LLFC_NE);
						break;
					case 11:
						condition = il.FlagCondition(LLFC_UGT);
						break;
					case 3:
						condition = il.FlagCondition(LLFC_ULE);
						break;
					case 0:
						condition = il.FlagCondition(LLFC_O);
						break;
					case 8:
						condition = il.FlagCondition(LLFC_NO);
						break;
					case 1:
						condition = il.FlagCondition(LLFC_ULT);
						break;
					case 9:
						condition = il.FlagCondition(LLFC_UGE);
						break;
					case 6:
						condition = il.FlagCondition(LLFC_SLT);
						break;
					case 14:
						condition = il.FlagCondition(LLFC_SGE);
						break;
					case 7:
						condition = il.FlagCondition(LLFC_SLE);
						break;
					case 15:
						condition = il.FlagCondition(LLFC_SGT);
						break;
					case 4:
						condition = il.FlagCondition(LLFC_NEG);
						break;
					case 12:
						condition = il.FlagCondition(LLFC_POS);
						break;
					case 13:
						condition = il.CompareEqual(
							4,
							il.Flag(
								FLAG_SAT
							),
							il.Const(
								4,
								1
							)
						);
						break;
					default:
						break;
					}
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.SignExtend(
								4,
								il.Const(
									1,
									insn->fields[1].value
								)
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							this->get_reg(il,insn->fields[2].value,4)
						)
					);
					il.MarkLabel(end_tag);
				}
			}
			break;
			case N850_CMP:
			{
				il.AddInstruction(
					il.Sub(
						4,
						this->get_reg(il,insn->fields[1].value,4),
						this->get_reg(il,insn->fields[0].value,4),
						FLAG_WRITE_CYOVSZ

					)
				);
			}
			break;
			case N850_CMPFS:
			{
				// TODO bit field specifications???
				switch (insn->fields[0].value)
				{
				case 0: // F
				case 8: // SF
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								0
							)
						)
					);
					break;
				case 2: // EQ
				case 3: // UQE
				case 10: // SEQ
				case 11: // NGL
					condition = il.FloatCompareEqual(
						4,
						this->get_reg(il,insn->fields[2].value,4),
						this->get_reg(il,insn->fields[1].value,4)
					);
					
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								1
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								0
							)
						)
					);
					il.MarkLabel(end_tag);
					break;
				case 4: // OLT
				case 5: // ULT
				case 12: // LT
				case 13: // NGE
					condition = il.FloatCompareLessThan(
						4,
						this->get_reg(il,insn->fields[2].value,4),
						this->get_reg(il,insn->fields[1].value,4)
					);
					
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								1
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								0
							)
						)
					);
					il.MarkLabel(end_tag);
					break;
				case 6: // OLE
				case 7: // ULE
				case 14: // LE
				case 15: // NGT
					condition = il.FloatCompareLessEqual(
						4,
						this->get_reg(il,insn->fields[2].value,4),
						this->get_reg(il,insn->fields[1].value,4)
					);
					
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								1
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							NEC_SYSREG_FPSR,
							il.Const(
								4,
								0
							)
						)
					);
					il.MarkLabel(end_tag);
					break;
				default:
					il.AddInstruction(il.Unimplemented());
					break;
				}
			}
			break;
			case N850_CMPI:
			{
				il.AddInstruction(
					il.Sub(
						4,
						this->get_reg(il,insn->fields[1].value,4),
						il.SignExtend(
							4,
							il.Const(
								1,
								insn->fields[0].value
							)
						),
						FLAG_WRITE_CYOVSZ

					)
				);
			}
			break;
			case N850_CTRET:
			{
				il.AddInstruction(il.Return(NEC_SYSREG_CTPC));
			}
			break;
			case N850_CVTFHS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFLS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFSL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.FloatConvert(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_CVTFSH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFSUL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						4,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_CVTFSUW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFULS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFUWS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_CVTFWS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatConvert(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_DBRET:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_SYSREG_PSW,
						il.Register(
							4,
							NEC_SYSREG_DBPSW
						)
					)
				);
				il.AddInstruction(il.Return(NEC_SYSREG_DBPC));
			}
			break;
			case N850_DBTRAP:
			{
				il.AddInstruction(
					il.Trap(
						insn->fields[0].value
					)
				);
			}
			break;
			case N850_DI:
			{
				// Intrinsics candidate
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SYNC_EXCEPTIONS,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_DISPOSE:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_REG_SP,
						il.Add(
							4,
							il.Register(4, NEC_REG_SP),
							il.Const(
								4,
								insn->fields[0].value * 4
							)
						)
						
					)
				);
				for (int i = 0; i < 12; i++)
				{
					if (((0x800 >> i) & insn->fields[1].value) == (0x800 >> i)) {
						il.AddInstruction(
							il.SetRegister(
								4,
								reg_list_regs[i],
								il.Pop(
									4
								)
							)
						);
					}
				}
				
				
			}
			break;
			case N850_DISPOSER:
			{
				
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_REG_SP,
						il.Add(
							4,
							il.Register(4, NEC_REG_SP),
							il.Const(
								4,
								insn->fields[0].value * 4
							)
						)
						
					)
				);
				for (int i = 11; i >= 0; i--)
				{
					if (((0x800 >> i) & insn->fields[1].value) == (0x800 >> i)) {
						il.AddInstruction(
							il.SetRegister(
								4,
								reg_list_regs[i],
								il.Pop(
									4
								)
							)
						);
					}
				}
				
				il.AddInstruction(
					il.Return(
						this->get_reg(il,insn->fields[2].value,4)
					)
				);
			}
			break;
			case N850_DIV:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ModSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_DIVFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatDiv(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_DIVH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								this->get_reg(il,insn->fields[0].value,2)
							),
							FLAG_WRITE_SZ
						)
					)
				);
			}
			break;
			case N850_DIVHR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								this->get_reg(il,insn->fields[0].value,2)
							),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ModSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								this->get_reg(il,insn->fields[0].value,2)
							)
						)
					)
				);
			}
			break;
			case N850_DIVHU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivUnsigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								this->get_reg(il,insn->fields[0].value,2)
							),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ModUnsigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								this->get_reg(il,insn->fields[0].value,2)
							)
						)
					)
				);
			}
			break;
			case N850_DIVQ:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ModSigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_DIVQU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivUnsigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ModUnsigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_DIVU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.DivUnsigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ModUnsigned(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_EI:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						EI_INTRINSIC,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_EIRET:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_SYSREG_PSW,
						il.Register(
							4,
							NEC_SYSREG_EIPSW
						)
					)
				);
				il.AddInstruction(il.Return(il.Register(4,NEC_SYSREG_EIPC)));

			}
			break;
			case N850_FERET:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_SYSREG_PSW,
						il.Register(
							4,
							NEC_SYSREG_FEPSW
						)
					)
				);
				il.AddInstruction(il.Return(il.Register(4,NEC_SYSREG_FEPC)));

			}
			break;
			case N850_FETRAP:
			{
				il.AddInstruction(
					il.Trap(
						insn->fields[0].value
					)
				);
			}
			break;
			case N850_FLOORFSL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.Floor(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_FLOORFSUL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.Floor(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_FLOORFSUW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Floor(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_FLOORFSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Floor(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_FMAFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatAdd(
							4,
							il.FloatMult(
								4,
								this->get_reg(il,insn->fields[1].value,4),
								this->get_reg(il,insn->fields[0].value,4)
							),
							this->get_reg(il,insn->fields[2].value,4)
						)
					)
				);
			}
			break;
			case N850_FMSFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatSub(
							4,
							il.FloatMult(
								4,
								this->get_reg(il,insn->fields[1].value,4),
								this->get_reg(il,insn->fields[0].value,4)
							),
							this->get_reg(il,insn->fields[2].value,4)
						)
					)
				);
			}
			break;
			case N850_FNMAFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatNeg(
							4,
							il.FloatAdd(
								4,
								il.FloatMult(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									this->get_reg(il,insn->fields[0].value,4)
								),
								this->get_reg(il,insn->fields[2].value,4)
							)
						)
					)
				);
			}
			break;
			case N850_FNMSFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatNeg(
							4,
							il.FloatSub(
								4,
								il.FloatMult(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									this->get_reg(il,insn->fields[0].value,4)
								),
								this->get_reg(il,insn->fields[2].value,4)
							)
						)
					)
				);
			}
			break;
			case N850_HALT:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SYNC_EXCEPTIONS,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_HSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Or(
							4,
							il.ShiftLeft(
								4,
								this->get_reg(il,insn->fields[0].value,4),
								il.Const(
									4,
									16
								)
							),
							il.LogicalShiftRight(
								4,
								this->get_reg(il,insn->fields[0].value,4),
								il.Const(
									4,
									16
								)
							)
						),
						FLAG_WRITE_CYOVSZ
					)
				);
			}
			break;
			case N850_HSH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						this->get_reg(il,insn->fields[0].value,4),
						FLAG_WRITE_CYOVSZ
					)
				);
			}
			break;
			case N850_JARL:
			{
				// TODO check
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,NEC_REG_PC,4),
							il.Const(
								4,
								4
							)
						)
						
					)
				);
				il.AddInstruction(
					il.Call(
						il.ConstPointer(
							4,
							addr + insn->fields[0].value
						)
					)
				);
			}
			break;
			case N850_JARL2:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,NEC_REG_PC,4),
							il.Const(
								4,
								6
							)
						)
						
					)
				);
				il.AddInstruction(
					il.Call(
						il.ConstPointer(
							4,
							addr + insn->fields[0].value
						)
					)
				);
			}
			break;
			case N850_JARL3:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,NEC_REG_PC,4),
							il.Const(
								4,
								4
							)
						)
						
					)
				);
				il.AddInstruction(
					il.Call(
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_JMP:
			{
				if (insn->fields[0].value == NEC_REG_LP) {
					il.AddInstruction(il.Return(il.Register(4,NEC_REG_LP)));
				} else {
					il.AddInstruction(il.Jump(il.Register(4, insn->fields[0].value)));
					il.MarkLabel(false_tag);
				}
			}
			break;
			case N850_JMPI:
			{
				il.AddInstruction(
					il.Jump(
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.Const(
								4,
								insn->fields[0].value
							)
						)
					)
				);
			}
			break;
			case N850_JR:
			{
				// TODO check
				il.AddInstruction(
					il.Jump(
						il.Add(
							4,
							il.Const(
								4,
								addr
							),
							il.SignExtend(
								4,
								il.Const(
									3,
									insn->fields[0].value
								)
							)
						)
					)
				);
			}
			break;
			case N850_JRL:
			{
				il.AddInstruction(
					il.Jump(
						il.Add(
							4,
							il.Const(
								4,
								addr
							),
							il.Const(
								4,
								insn->fields[0].value
							)
						)
					)
				);
			}
			break;
			case N850_LDBL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.SignExtend(
							4,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											3,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDBUL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ZeroExtend(
							4,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											3,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDDW:
			{
				// TODO check 
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value + 1,
						il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											3,
											insn->fields[0].value
										)
									)
								)
							)
					)
				);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											3,
											insn->fields[0].value + 4
										)
									)
								)
							)
					)
				);
			}
			break;
			case N850_LDB:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.SignExtend(
							4,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDBU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ZeroExtend(
							4,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.SignExtend(
							4,
							il.Load(
								2,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDHU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ZeroExtend(
							4,
							il.Load(
								2,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Load(
							4,
							il.Add(
								4,
								this->get_reg(il,insn->fields[1].value,4),
								il.SignExtend(
									4,
									il.Const(
										2,
										insn->fields[0].value
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDSR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_MOV:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_MOVI5:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.SignExtend(
							4,
							il.Const(
								1,
								insn->fields[0].value
							)
						)
					)
				);
			}
			break;
			case N850_MOVI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Const(
							4,
							insn->fields[0].value
						)
					)
				);
			}
			break;
			case N850_MOVEA:
			{
				// 002106a2
				
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
							)
						)
					)
				);
				
			}
			break;
			case N850_MOVHI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ShiftLeft(
								4,
								il.Const(
									2,
									insn->fields[0].value
								),
								il.Const(
									4,
									16
								)
							)
						)
					)
				);
			}
			break;
			case N850_MAXFS:
			{
				condition = il.FloatCompareGreaterThan(
					4,

					this->get_reg(il,insn->fields[0].value,4),
					this->get_reg(il,insn->fields[1].value,4)
				);
				il.AddInstruction(il.If(condition,true_tag,false_tag));
				il.MarkLabel(true_tag);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
				il.AddInstruction(il.Goto(end_tag));
				il.MarkLabel(false_tag);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						this->get_reg(il,insn->fields[1].value,4)
					)
				);
				il.MarkLabel(end_tag);
			}
			break;
			case N850_MINFS:
			{
				condition = il.FloatCompareLessThan(
					4,
					this->get_reg(il,insn->fields[0].value,4),
					this->get_reg(il,insn->fields[1].value,4)
				);
				il.AddInstruction(il.If(condition,true_tag,false_tag));
				il.MarkLabel(true_tag);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
				il.AddInstruction(il.Goto(end_tag));
				il.MarkLabel(false_tag);
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						this->get_reg(il,insn->fields[1].value,4)
					)
				);
				il.MarkLabel(end_tag);
			}
			break;
			case N850_MULFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatMult(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_NEGFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatNeg(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_RECIPFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatDiv(
							4,
							il.Const(
								4,
								1
							),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_ROUNDFSL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.RoundToInt(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_ROUNDFSUL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value,
						il.RoundToInt(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_ROUNDFSUW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.RoundToInt(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_ROUNDFSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.RoundToInt(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_RSQRTFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatDiv(
							4,
							il.Const(
								4,
								1
							),
							il.FloatSqrt(
								4,
								this->get_reg(il,insn->fields[0].value,4)
							)
						)
					)
				);
			}
			break;
			case N850_SQRTFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatSqrt(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_MUL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						4,
						insn->fields[2].value,
						insn->fields[1].value,
						il.Mult(
							8,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_MULI:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						4,
						insn->fields[2].value,
						insn->fields[1].value,
						il.Mult(
							8,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
								
							)
						)
					)
				);
			}
			break;
			case N850_MULH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Mult(
							4,
							this->get_reg(il,insn->fields[1].value,2),
							this->get_reg(il,insn->fields[0].value,2)
						)
					)
				);
			}
			break;
			case N850_MULHIMM:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Mult(
							4,
							this->get_reg(il,insn->fields[1].value,2),
							il.SignExtend(
								2,
								il.Const(
									2,
									insn->fields[0].value
								)
							)
						)
					)
				);
			}
			break;
			case N850_MULHI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Mult(
							4,
							this->get_reg(il,insn->fields[1].value,2),
							il.Const(
								2,
								insn->fields[0].value
							)
						)
					)
				);
			}
			break;
			case N850_MULU:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						4,
						insn->fields[2].value,
						insn->fields[1].value,
						il.Mult(
							8,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_MULUI:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						4,
						insn->fields[2].value,
						insn->fields[1].value,
						il.Mult(
							8,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
								
							)
						)
					)
				);
			}
			break;
			case N850_NOP:
			{
				il.AddInstruction(il.Nop());
			}
			break;
			case N850_NOT:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Not(
							4,
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_NOT1:
			{
				il.AddInstruction(
					il.Store(
						1,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[1].value
								)
							)
						),
						il.Xor(
							1,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[2].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[1].value
										)
									)
								)
							),
							il.Const(
								1,
								(1 << insn->fields[0].value) & 0xff
							),
							FLAG_WRITE_Z
						)
					)
				);
			}
			break;
			case N850_NOT1R:
			{
				il.AddInstruction(
					il.Store(
						1,
						this->get_reg(il,insn->fields[1].value,4),
						il.Xor(
							1,
							il.Load(
								1,
								this->get_reg(il,insn->fields[1].value,4)
							),
							il.ShiftLeft(
								1,
								il.Const(
									1,
									1
								),
								this->get_reg(il,insn->fields[0].value,1)
							),
							FLAG_WRITE_Z
						)
					)
				);
			}
			break;
			case N850_OR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Or(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_ORI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Or(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_PREPARE:
			{
				for (int i = 0; i < 12; i++)
				{
					if (((0x800 >> i) & insn->fields[0].value) == (0x800 >> i)) {
						il.AddInstruction(
							il.Push(
								4,
								this->get_reg(il,reg_list_regs[i],4)
							)
						);
					}
				}
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_REG_SP,
						il.Sub(
							4,
							il.Register(4, NEC_REG_SP),
							il.Const(
								4,
								insn->fields[1].value * 4
							)
						)
						
					)
				);
				
				// TODO need some example to verify
			}
			break;
			case N850_RETI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						NEC_SYSREG_PSW,
						il.Register(
							4,
							NEC_SYSREG_EIPSW
						)
					)
				);
				il.AddInstruction(
					il.Return(
						il.Register(
							4,
							NEC_SYSREG_EIPC
						)
					)
				);
			}
			break;
			case N850_SAR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.ArithShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SARI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.ArithShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SARR:
			{
				// TODO test disassembly
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ArithShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SASF:
			{
				if (insn->fields[0].value == 5) {
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[1].value,
							il.Or(
								4,
								il.ShiftLeft(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.Const(
										4,
										1
									)
								),
								il.Const(
									4,
									1
								)
							)
						)
					);
				} else {
					switch (insn->fields[0].value)
					{
					case 2:
						condition = il.FlagCondition(LLFC_E);
						break;
					case 10:
						condition = il.FlagCondition(LLFC_NE);
						break;
					case 11:
						condition = il.FlagCondition(LLFC_UGT);
						break;
					case 3:
						condition = il.FlagCondition(LLFC_ULE);
						break;
					case 0:
						condition = il.FlagCondition(LLFC_O);
						break;
					case 8:
						condition = il.FlagCondition(LLFC_NO);
						break;
					case 1:
						condition = il.FlagCondition(LLFC_ULT);
						break;
					case 9:
						condition = il.FlagCondition(LLFC_UGE);
						break;
					case 6:
						condition = il.FlagCondition(LLFC_SLT);
						break;
					case 14:
						condition = il.FlagCondition(LLFC_SGE);
						break;
					case 7:
						condition = il.FlagCondition(LLFC_SLE);
						break;
					case 15:
						condition = il.FlagCondition(LLFC_SGT);
						break;
					case 4:
						condition = il.FlagCondition(LLFC_NEG);
						break;
					case 12:
						condition = il.FlagCondition(LLFC_POS);
						break;
					case 13:
						condition = il.CompareEqual(
							4,
							il.Flag(
								FLAG_SAT
							),
							il.Const(
								4,
								1
							)
						);
						break;
					default:
						break;
					}
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[1].value,
							il.Or(
								4,
								il.ShiftLeft(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.Const(
										4,
										1
									)
								),
								il.Const(
									4,
									1
								)
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[1].value,
							il.ShiftLeft(
								4,
								this->get_reg(il,insn->fields[1].value,4),
								il.Const(
									4,
									1
								)
							)
						)
					);
					il.MarkLabel(end_tag);
				}
				
			}
			break;
			case N850_SATADD:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SATADDI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								il.Const(
									1,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SATSUB:
			// TODO handle the saturation?
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SATSUBI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SATSUBR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[0].value,4),
							this->get_reg(il,insn->fields[1].value,4),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SET1:
			{
				il.AddInstruction(
					il.Store(
						1,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[1].value
								)
							)
						),
						il.Or(
							1,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[2].value,4),
									il.SignExtend(
										4,
										il.Const(
											2,
											insn->fields[1].value
										)
									)
								)
							),
							il.Const(
								1,
								(1 << insn->fields[0].value) & 0xff
							),
							FLAG_WRITE_Z
						)
					)
				);
			}
			break;
			case N850_SET1R:
			{
				il.AddInstruction(
					il.Store(
						1,
						this->get_reg(il,insn->fields[1].value,4),
						il.Or(
							1,
							il.Load(
								1,
								this->get_reg(il,insn->fields[1].value,4)
							),
							il.ShiftLeft(
								1,
								il.Const(
									1,
									1
								),
								this->get_reg(il,insn->fields[0].value,4)
							),
							FLAG_WRITE_Z
						)
					)
				);
			}
			break;
			case N850_SETF:
			{
				if (insn->fields[0].value == 5) {
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[1].value,
							il.Const(
								4,
								1
							)
						)
					);
				} else {
					switch (insn->fields[0].value)
					{
					case 2:
						condition = il.FlagCondition(LLFC_E);
						break;
					case 10:
						condition = il.FlagCondition(LLFC_NE);
						break;
					case 11:
						condition = il.FlagCondition(LLFC_UGT);
						break;
					case 3:
						condition = il.FlagCondition(LLFC_ULE);
						break;
					case 0:
						condition = il.FlagCondition(LLFC_O);
						break;
					case 8:
						condition = il.FlagCondition(LLFC_NO);
						break;
					case 1:
						condition = il.FlagCondition(LLFC_ULT);
						break;
					case 9:
						condition = il.FlagCondition(LLFC_UGE);
						break;
					case 6:
						condition = il.FlagCondition(LLFC_SLT);
						break;
					case 14:
						condition = il.FlagCondition(LLFC_SGE);
						break;
					case 7:
						condition = il.FlagCondition(LLFC_SLE);
						break;
					case 15:
						condition = il.FlagCondition(LLFC_SGT);
						break;
					case 4:
						condition = il.FlagCondition(LLFC_NEG);
						break;
					case 12:
						condition = il.FlagCondition(LLFC_POS);
						break;
					case 13:
						condition = il.CompareEqual(
							4,
							il.Flag(
								FLAG_SAT
							),
							il.Const(
								4,
								1
							)
						);
						break;
					default:
						break;
					}
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[1].value,
							il.Const(
								4,
								1
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[1].value,
							il.Const(
								4,
								0
							)
						)
					);
					il.MarkLabel(end_tag);
				}
			}
			break;
			case N850_SHL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.ShiftLeft(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SHLI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.ShiftLeft(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_CY,
						il.And(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.Const(
								4,
								(0x80000000 >> (insn->fields[0].value - 1))
							)
							
						)
					)
				);
			}
			break;
			case N850_SHR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.LogicalShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SHRI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.LogicalShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_CY,
						il.And(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.Const(
								4,
								(1 << (insn->fields[0].value - 1))
							)
							
						)
					)
				);
			}
			break;
			case N850_SLDB:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.SignExtend(
							4,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.ZeroExtend(
										4,
										il.Const(
											1,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_SLDBU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ZeroExtend(
							4,
							il.Load(
								1,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.ZeroExtend(
										4,
										il.Const(
											1,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_SLDH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.SignExtend(
							4,
							il.Load(
								2,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.ZeroExtend(
										4,
										il.Const(
											1,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_SLDHU:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ZeroExtend(
							4,
							il.Load(
								2,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.ZeroExtend(
										4,
										il.Const(
											1,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_SLDW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Load(
							4,
							il.Add(
								4,
								this->get_reg(il,insn->fields[1].value,4),
								il.ZeroExtend(
									4,
									il.Const(
										1,
										insn->fields[0].value
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_SSTB:
			{
				il.AddInstruction(
					il.Store(
						1,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_SSTH:
			{
				il.AddInstruction(
					il.Store(
						2,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_SSTW:
			{
				il.AddInstruction(
					il.Store(
						4,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_STB:
			{
				il.AddInstruction(
					il.Store(
						1,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_STH:
			{
				il.AddInstruction(
					il.Store(
						2,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_STW:
			{
				il.AddInstruction(
					il.Store(
						4,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									2,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_STSR:
			{
				// TODO test disass
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_SUB:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_SUBR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[0].value,4),
							this->get_reg(il,insn->fields[1].value,4),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_SWITCH:
			{
				il.AddInstruction(
					il.Jump(
						il.Add(
							4,
							il.Const(
								4,
								addr + 2
							),
							il.SignExtend(
								4,
								il.ShiftLeft(
									2,
									il.Load(
										2,
										il.Add(
											4,
											il.Const(
												4,
												addr + 2
											),
											il.ShiftLeft(
												4,
												this->get_reg(il,insn->fields[0].value,4),
												il.Const(
													4,
													1
												)
											)
										)
									),
									il.Const(
										4,
										1
									)
								)
							)
						)
					)
				);
				il.MarkLabel(end_tag);
			}
			break;
			case N850_SXB:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[0].value,
						il.SignExtend(
							4,
							this->get_reg(il,insn->fields[0].value,1)
						)
					)
				);
			}
			break;
			case N850_SXH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[0].value,
						il.SignExtend(
							4,
							this->get_reg(il,insn->fields[0].value,2)
						)
					)
				);
			}
			break;
			case N850_SYNCE:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SYNC_EXCEPTIONS,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_SYNCI:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SYNC_INSN_FETCHER,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_SYNCM:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SYNC_MEMORY_ACCESS,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_SYNCP:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SYNC_PIPELINE,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_SYSCALL:
			{
				il.AddInstruction(il.SystemCall());
			}
			break;
			case N850_TRAP:
			{
				il.AddInstruction(
					il.Trap(
						insn->fields[0].value
					)
				);
			}
			break;
			case N850_TST:
			{
				il.AddInstruction(
					il.And(
						4,
						this->get_reg(il,insn->fields[1].value,4),
						this->get_reg(il,insn->fields[0].value,4),
						FLAG_WRITE_SZ
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_TST1:
			{
				il.AddInstruction(
					
					il.Add(
						1,
						il.Load(
							1,
							il.Add(
								4,
								this->get_reg(il,insn->fields[2].value,4),
								il.SignExtend(
									4,
									il.Const(
										2,
										insn->fields[1].value
									)
								)
							)
						),
						il.Const(
							1,
							(1 << insn->fields[0].value) & 0xff
						),
						FLAG_WRITE_Z
					)
					
				);
			}
			break;
			case N850_TST1R:
			{
				il.AddInstruction(
					il.Or(
						1,
						il.Load(
							1,
							this->get_reg(il,insn->fields[1].value,4)
						),
						il.ShiftLeft(
							1,
							il.Const(
								1,
								1
							),
							this->get_reg(il,insn->fields[0].value,1)
						),
						FLAG_WRITE_Z
					)
				);
			}
			break;
			case N850_SUBFS:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.FloatSub(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4)

						)
					)
				);
			}
			break;
			case N850_TRFSR:
			{
				il.AddInstruction(
					il.SetFlag(
						FLAG_Z,
						il.Register(
							4,
							NEC_SYSREG_FPSR
						)
					)
				);
			}
			break;
			case N850_TRNCFSL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value ,
						il.FloatTrunc(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_TRNCFSUL:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[1].value + 1,
						insn->fields[1].value ,
						il.FloatTrunc(
							8,
							this->get_reg(il,insn->fields[0].value,8)
						)
					)
				);
			}
			break;
			case N850_TRNCFSUW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatTrunc(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_TRNCFSW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.FloatTrunc(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)
					)
				);
			}
			break;
			case N850_XOR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Xor(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_XORI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Xor(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									2,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_SZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_ZXB:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[0].value,
						il.ZeroExtend(
							4,
							this->get_reg(il,insn->fields[0].value,1)
						)
					)
				);
			}
			break;
			case N850_ZXH:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[0].value,
						il.ZeroExtend(
							4,
							this->get_reg(il,insn->fields[0].value,2)
						)
					)
				);
			}
			break;
			case N850_LDLW:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[1].value,
						il.Load(
							4,
							this->get_reg(il,insn->fields[0].value,4)
						)

					)
				);
			}
			break;
			case N850_LOOP:
			{
				
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[0].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[0].value,4),
							il.Const(
								4,
								1
							),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
				condition = il.CompareNotEqual(
					4,
					this->get_reg(il,insn->fields[0].value,4),
					il.Const(
						4,
						0
					)
				);
				il.AddInstruction(il.If(condition,true_tag,false_tag));
				il.MarkLabel(true_tag);
				il.AddInstruction(
					il.Jump(
						il.ConstPointer(
							4,
							addr - insn->fields[1].value
						)
					)
				);
				il.MarkLabel(false_tag);

			}
			break;
			case N850_MAC:
			// TODO register splits verify
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[3].value + 1,
						insn->fields[3].value,
						il.Add(
							8,
							il.Mult(
								8,
								this->get_reg(il,insn->fields[1].value,4),
								this->get_reg(il,insn->fields[0].value,4)
							),
							il.RegisterSplit(
								8,
								insn->fields[2].value + 1,
								insn->fields[2].value
							)
						)
					)
				);
			}
			break;
			case N850_MACU:
			{
				il.AddInstruction(
					il.SetRegisterSplit(
						8,
						insn->fields[3].value + 1,
						insn->fields[3].value,
						il.Add(
							8,
							il.Mult(
								8,
								this->get_reg(il,insn->fields[1].value,4),
								this->get_reg(il,insn->fields[0].value,4)
							),
							il.RegisterSplit(
								8,
								insn->fields[2].value + 1,
								insn->fields[2].value
							)
						)
					)
				);
			}
			break;
			case N850_POPSP:
			// TODO check
			{
				for (size_t i = insn->fields[1].value; i >= insn->fields[0].value; i--)
				{
					il.AddInstruction(
						il.SetRegister(
							4,
							i,
							il.Pop(
								4
							)
						)
					);
				}
				
			}
			break;
			case N850_PUSHSP:
			{
				for (size_t i = insn->fields[1].value; i >= insn->fields[0].value; i--)
				{
					il.AddInstruction(
						il.Push(
							4,
							this->get_reg(il,i,4)
						)
					);
				}
			}
			break;
			case N850_RIEI:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						RIE_INTRINSIC,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_ROTL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.RotateLeft(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_ROTLI:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.RotateLeft(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							il.ZeroExtend(
								4,
								il.Const(
									1,
									insn->fields[0].value
								)
							),
							FLAG_WRITE_CYOVSZ
						)
					)
				);
			}
			break;
			case N850_SATADDR:
			{
				// TODO saturation is not actually handled here 
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Add(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SATSUBL:
			{
				// TODO saturation is not actually handled here 
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Sub(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_ALL
						)
					)
				);
			}
			break;
			case N850_SBF:
			{
				if (insn->fields[0].value == 5) {
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.Sub(
								4,
								il.Sub(
									4,
									this->get_reg(il,insn->fields[2].value,4),
									this->get_reg(il,insn->fields[1].value,4)
								),
								il.Const(
									4,
									1
								),
								FLAG_WRITE_CYOVSZ
							)
						)
					);
				} else {
					switch (insn->fields[0].value)
					{
					case 2:
						condition = il.FlagCondition(LLFC_E);
						break;
					case 10:
						condition = il.FlagCondition(LLFC_NE);
						break;
					case 11:
						condition = il.FlagCondition(LLFC_UGT);
						break;
					case 3:
						condition = il.FlagCondition(LLFC_ULE);
						break;
					case 0:
						condition = il.FlagCondition(LLFC_O);
						break;
					case 8:
						condition = il.FlagCondition(LLFC_NO);
						break;
					case 1:
						condition = il.FlagCondition(LLFC_ULT);
						break;
					case 9:
						condition = il.FlagCondition(LLFC_UGE);
						break;
					case 6:
						condition = il.FlagCondition(LLFC_SLT);
						break;
					case 14:
						condition = il.FlagCondition(LLFC_SGE);
						break;
					case 7:
						condition = il.FlagCondition(LLFC_SLE);
						break;
					case 15:
						condition = il.FlagCondition(LLFC_SGT);
						break;
					case 4:
						condition = il.FlagCondition(LLFC_NEG);
						break;
					case 12:
						condition = il.FlagCondition(LLFC_POS);
						break;
					case 13:
						condition = il.Unimplemented();
						break;
					default:
						break;
					}
					il.AddInstruction(il.If(condition,true_tag,false_tag));
					il.MarkLabel(true_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.Sub(
								4,
								il.Sub(
									4,
									this->get_reg(il,insn->fields[2].value,4),
									this->get_reg(il,insn->fields[1].value,4)
								),
								il.Const(
									4,
									1
								),
								FLAG_WRITE_CYOVSZ
							)
						)
					);
					il.AddInstruction(il.Goto(end_tag));
					il.MarkLabel(false_tag);
					il.AddInstruction(
						il.SetRegister(
							4,
							insn->fields[3].value,
							il.Sub(
								4,
								this->get_reg(il,insn->fields[2].value,4),
								this->get_reg(il,insn->fields[1].value,4),
								FLAG_WRITE_CYOVSZ
							)
						)
					);
					il.MarkLabel(end_tag);
				}
			}
			break;
			case N850_SCH0L:
			{
				// Count leading ones, candiadte for intrinsic
				il.AddInstruction(
					il.Intrinsic(
						{ RegisterOrFlag::Register(insn->fields[1].value) }, // Outputs
						SCH0L_INTRINSIC,
						{ il.Register(4, insn->fields[0].value) } // Inputs
					)
				);
			}
			break;
			case N850_SCH0R:
			{
				// Count trailing ones, candiadte for intrinsic
				il.AddInstruction(
					il.Intrinsic(
						{ RegisterOrFlag::Register(insn->fields[1].value) }, // Outputs
						SCH0R_INTRINSIC,
						{ il.Register(4, insn->fields[0].value) } // Inputs
					)
				);
			}
			break;
			case N850_SCH1L:
			{
				// Count leading zeros, candiadte for intrinsic
				il.AddInstruction(
					il.Intrinsic(
						{ RegisterOrFlag::Register(insn->fields[1].value) }, // Outputs
						SCH1L_INTRINSIC,
						{ il.Register(4, insn->fields[0].value) } // Inputs
					)
				);
			}
			break;
			case N850_SCH1R:
			{
				// Count trailing zeros, candiadte for intrinsic
				il.AddInstruction(
					il.Intrinsic(
						{ RegisterOrFlag::Register(insn->fields[1].value) }, // Outputs
						SCH1R_INTRINSIC,
						{ il.Register(4, insn->fields[0].value) } // Inputs
					)
				);
			}
			break;
			case N850_SHLL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ShiftLeft(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SHRL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.LogicalShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;
			case N850_SNOOZE:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						SNOOZE_INTRINSIC,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_STCW:
			{
				// TODO atomic operation not handled
				il.AddInstruction(
					il.Store(
						4,
						this->get_reg(il,insn->fields[1].value,4),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_LDHL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.SignExtend(
							4,
							il.Load(
								2,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											3,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDHUL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.ZeroExtend(
							4,
							il.Load(
								2,
								il.Add(
									4,
									this->get_reg(il,insn->fields[1].value,4),
									il.SignExtend(
										4,
										il.Const(
											3,
											insn->fields[0].value
										)
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_LDWL:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.Load(
							4,
							il.Add(
								4,
								this->get_reg(il,insn->fields[1].value,4),
								il.SignExtend(
									4,
									il.Const(
										3,
										insn->fields[0].value
									)
								)
							)
						)
					)
				);
			}
			break;
			case N850_STDL:
			{
				il.AddInstruction(
					il.Store(
						1,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									3,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,1)
					)
				);
			}
			break;
			case N850_STDW:
			{
				il.AddInstruction(
					il.Store(
						8,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									3,
									insn->fields[1].value
								)
							)
						),
						il.RegisterSplit(
							8,
							insn->fields[0].value + 1,
							insn->fields[0].value
						)
					)
				);
			}
			break;
			case N850_STHL:
			{
				il.AddInstruction(
					il.Store(
						2,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									3,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,2)
					)
				);
			}
			break;
			case N850_STWL:
			{
				il.AddInstruction(
					il.Store(
						4,
						il.Add(
							4,
							this->get_reg(il,insn->fields[2].value,4),
							il.SignExtend(
								4,
								il.Const(
									3,
									insn->fields[1].value
								)
							)
						),
						this->get_reg(il,insn->fields[0].value,4)
					)
				);
			}
			break;
			case N850_RIE:
			{
				il.AddInstruction(
					il.Intrinsic(
						{ }, // Outputs
						RIE_INTRINSIC,
						{ } // Inputs
					)
				);
			}
			break;
			case N850_SHRR:
			{
				il.AddInstruction(
					il.SetRegister(
						4,
						insn->fields[2].value,
						il.LogicalShiftRight(
							4,
							this->get_reg(il,insn->fields[1].value,4),
							this->get_reg(il,insn->fields[0].value,4),
							FLAG_WRITE_CYSZ
						)
					)
				);
				il.AddInstruction(
					il.SetFlag(
						FLAG_OV,
						il.Const(
							4,
							0
						)
					)
				);
			}
			break;

			default:
				il.AddInstruction(il.Unimplemented());
			}

			free(insn);
			return true;
		}
		free(insn);
		return false;
		/*if (addr == 0x000d0d0c) {
			LogInfo("%s AT 0x%x: N: %d", insn->name, (uint32_t)addr,insn->n);
			LogInfo("%s OP[0] type: %d: value: %d", insn->name, insn->fields[0].type,insn->fields[0].value);
			LogInfo("%s OP[1] type: %d: value: %d", insn->name, insn->fields[1].type,insn->fields[1].value);
			LogInfo("%s OP[2] type: %d: value: %d", insn->name, insn->fields[2].type,insn->fields[2].value);
		}*/
	}

	virtual bool GetInstructionInfo(const uint8_t *data, uint64_t addr, size_t maxLen, InstructionInfo &result) override
	{
		insn_t *insn;
		if ((insn = disassemble(data)))
		{
			result.length = insn->size;
			uint32_t target;
			switch (insn->op_type)
			{
			case OP_TYPE_JMP:
				result.AddBranch(UnconditionalBranch, (insn->fields[0].value + (uint32_t)addr) & 0xffffffff);
				break;
			case OP_TYPE_LOOP:
				target = ((uint32_t)addr - insn->fields[1].value) & 0xffffffff;
				result.AddBranch(TrueBranch, target); // + (uint32_t) addr) & 0xffffffff);
				result.AddBranch(FalseBranch, (insn->size + addr) & 0xffffffff);
				break;
			case OP_TYPE_CJMP:
				target = (insn->fields[0].value + (uint32_t)addr) & 0xffffffff;
				if (insn->fields[0].type == TYPE_JMP)
				{
					result.AddBranch(TrueBranch, target); // + (uint32_t) addr) & 0xffffffff);
					result.AddBranch(FalseBranch, (insn->size + addr) & 0xffffffff);
				}
				else
				{
					// LogInfo("CJMP WENT WRONG AT 0x%x", addr);
					free(insn);
					return false;
				}
				break;
			case OP_TYPE_CALL:
				target = (insn->fields[0].value + (uint32_t)addr) & 0xffffffff;
				if (target != ((uint32_t)addr + insn->size))
					result.AddBranch(CallDestination, target); // + (uint32_t) addr) & 0xffffffff);
				break;
			case OP_TYPE_RCALL:
				result.AddBranch(IndirectBranch);
				break;
			case OP_TYPE_RJMP:
				result.AddBranch(IndirectBranch);
				break;
			case OP_TYPE_RET:
				result.AddBranch(FunctionReturn);
				break;
			case OP_TYPE_TRAP:
				result.AddBranch(FunctionReturn);
				break;
			default:
				break;
			}
			free(insn);
			return true;
		}
		free(insn);
		return false;
	}

	virtual bool GetInstructionText(const uint8_t *data, uint64_t addr, size_t &len, std::vector<InstructionTextToken> &result) override
	{
		insn_t *insn;
		char tmp[256] = {0};
		if ((insn = disassemble(data)))
		{

			int name_len = strlen(insn->name);
			for (int i = name_len; i < 14; i++)
			{
				tmp[i - name_len] = ' ';
			}
			len = insn->size;
			tmp[14 - name_len] = 0;
			result.emplace_back(InstructionToken, insn->name);
			result.emplace_back(TextToken, tmp);
			char hex_val[20] = {0};
			char reg_str[10] = {0};
			for (int op_index = 0; op_index < insn->n; op_index++)
			{
				switch (insn->fields[op_index].type)
				{
				case TYPE_REG:
					result.emplace_back(RegisterToken, reg_name[insn->fields[op_index].value]);
					break;
				case TYPE_REG_MEM:
					if (op_index > 0)
						result.pop_back();
					snprintf(reg_str, 10, "[%s]", reg_name[insn->fields[op_index].value]);
					result.emplace_back(RegisterToken, reg_str);
					break;
				case TYPE_MEM:
					if (insn->fields[op_index].value == 0)
						break;
					if (insn->fields[op_index].sign)
						snprintf(hex_val, 20, "%s0x%x", ((int32_t)insn->fields[op_index].value < 0) ? "-" : "", ((int32_t)insn->fields[op_index].value < 0) ? -(int32_t)insn->fields[op_index].value : (int32_t)insn->fields[op_index].value);
					else
						snprintf(hex_val, 20, "0x%x", (uint32_t)insn->fields[op_index].value);
					result.emplace_back(IntegerToken, hex_val, insn->fields[op_index].value);
					break;
				case TYPE_IMM:
					if (insn->fields[op_index].sign)
						snprintf(hex_val, 20, "%s0x%x", ((int32_t)insn->fields[op_index].value < 0) ? "-" : "", ((int32_t)insn->fields[op_index].value < 0) ? -(int32_t)insn->fields[op_index].value : (int32_t)insn->fields[op_index].value);
					else
						snprintf(hex_val, 20, "0x%x", (uint32_t)insn->fields[op_index].value);
					result.emplace_back(IntegerToken, hex_val, insn->fields[op_index].value);
					break;
				case TYPE_JMP:
					snprintf(hex_val, 20, "0x%x", (uint32_t)(insn->fields[op_index].value) + (uint32_t)addr); // + (uint32_t) addr));
					result.emplace_back(IntegerToken, hex_val, insn->fields[op_index].value + addr);
					break;
				case TYPE_LOOP:
					snprintf(hex_val, 20, "0x%x", (uint32_t)addr - (uint32_t)(insn->fields[op_index].value)); // + (uint32_t) addr));
					result.emplace_back(IntegerToken, hex_val, addr - insn->fields[op_index].value);
					break;
				case TYPE_CCCC:
					result.emplace_back(RegisterToken, cccc_name[insn->fields[op_index].value]);
					break;
				case TYPE_COND:
					result.emplace_back(RegisterToken, cond_name[insn->fields[op_index].value]);
					break;
				case TYPE_SYSREG:
					result.emplace_back(RegisterToken, this->GetSysregName(insn->fields[op_index].value));
					break;
				case TYPE_LIST:
					result.emplace_back(OperandSeparatorToken, "{");
					for (int i = 0; i < 12; i++)
					{
						if (((0x800 >> i) & insn->fields[op_index].value) == (0x800 >> i)) {
							result.emplace_back(RegisterToken, reg_list_names[i]);
							result.emplace_back(OperandSeparatorToken, ", ");
						}
					}
					result.pop_back();
					result.emplace_back(OperandSeparatorToken, "}");
				default:
					break;
				}
				result.emplace_back(OperandSeparatorToken, ", ");
			}
			result.pop_back();
			free(insn);
			return true;
		}
		free(insn);
		return false;
	}
};

class Nec850CallingConvention : public CallingConvention
{
public:
	Nec850CallingConvention(Architecture *arch) : CallingConvention(arch, "default")
	{
	}

	virtual vector<uint32_t> GetIntegerArgumentRegisters() override
	{
		return vector<uint32_t>{
			NEC_REG_R6, NEC_REG_R7, NEC_REG_R8, NEC_REG_R9};
	}

	virtual uint32_t GetIntegerReturnValueRegister() override
	{
		return NEC_REG_R10;
	}

	virtual vector<uint32_t> GetCallerSavedRegisters() override
	{
		return vector<uint32_t>{
			NEC_REG_R10, NEC_REG_R11, NEC_REG_R12, NEC_REG_R13, NEC_REG_R14, NEC_REG_R15, NEC_REG_R16, NEC_REG_R17, NEC_REG_R18, NEC_REG_R19};
	}

	virtual vector<uint32_t> GetCalleeSavedRegisters() override
	{
		return vector<uint32_t>{
			NEC_REG_R20, NEC_REG_R21, NEC_REG_R22, NEC_REG_R23, NEC_REG_R24, NEC_REG_R25, NEC_REG_R26, NEC_REG_R27, NEC_REG_R28, NEC_REG_R29, NEC_REG_EP, NEC_REG_LP};
	}
};
extern "C"
{
	BN_DECLARE_CORE_ABI_VERSION

	BINARYNINJAPLUGIN void CorePluginDependencies()
	{
		AddOptionalPluginDependency("view_elf");
		AddOptionalPluginDependency("view_macho");
		AddOptionalPluginDependency("view_pe");
	}

	BINARYNINJAPLUGIN bool CorePluginInit()
	{

		/* create, register arch in global list of available architectures */
		Architecture *nec850 = new NEC850("nec850");
		Architecture::Register(nec850);
		Ref<CallingConvention> conv;
		conv = new Nec850CallingConvention(nec850);
		nec850->RegisterCallingConvention(conv);
		nec850->SetDefaultCallingConvention(conv);

#define EM_NEC850 87
		BinaryViewType::RegisterArchitecture(
			"ELF",
			EM_NEC850,
			LittleEndian,
			nec850);
#define EM_NECV850 36
		BinaryViewType::RegisterArchitecture(
			"ELF",
			EM_NECV850,
			LittleEndian,
			nec850);

		return true;
	}
}
/*
extern "C"
{
	BN_DECLARE_CORE_ABI_VERSION

	BINARYNINJAPLUGIN bool CorePluginInit()
	{
		PluginCommand::Register("Test Plugin\\Test", "It's a test action!", [](BinaryView* view) {
			for (auto& symbol: view->GetSymbols())
			{
				LogInfo("%s", symbol->GetFullName().c_str());
			}
		});
		return true;
	}

	BINARYNINJAPLUGIN void CorePluginDependencies()
	{
	}
}
*/
