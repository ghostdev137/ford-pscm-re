// Apply a fixed value for the V850 gp (r4) register to the program
// context so Ghidra's decompiler / const-propagator can resolve
// gp-relative loads and stores to their absolute targets.
//
// Without this, every rodata / RAM-workspace access renders as
//   *(type *)(unaff_gp + -0xNNNN)
// instead of a named DAT_XXXXXXXX reference, and
// ReferenceManager.getReferencesTo returns zero for those targets.
//
// Usage:
//   analyzeHeadless PROJ NAME -process X.elf \
//     -scriptPath tools/scripts -postScript ApplyGpContext.java 0xfec01984
//
// Default value is the F-150 PSCM gp — pass an explicit arg for other
// platforms. Idempotent: running twice with the same value is a no-op.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.ProgramContext;
import ghidra.program.model.mem.MemoryBlock;
import java.math.BigInteger;

public class ApplyGpContext extends GhidraScript {
    // F-150 PSCM AM firmware: gp = 0xfec01984 (derived from _start at
    // 0x10040000: movhi/movea build 0xfebf9984, then zeroed, then
    // 0xfec01984 accumulated via `mov 0xfec01984,r10; add r10,gp`).
    private static final long DEFAULT_GP = 0xfec01984L;

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        long gpValue = DEFAULT_GP;
        if (args.length > 0 && !args[0].isBlank()) {
            gpValue = Long.decode(args[0]) & 0xFFFFFFFFL;
        }

        ProgramContext ctx = currentProgram.getProgramContext();
        Register gp = currentProgram.getLanguage().getRegister("gp");
        if (gp == null) gp = currentProgram.getLanguage().getRegister("r4");
        if (gp == null) {
            printerr("no gp/r4 register in language");
            return;
        }

        BigInteger gpBig = BigInteger.valueOf(gpValue);
        int applied = 0;
        for (MemoryBlock blk : currentProgram.getMemory().getBlocks()) {
            if (!blk.isExecute()) continue;
            Address s = blk.getStart();
            Address e = blk.getEnd();
            try {
                ctx.setValue(gp, s, e, gpBig);
                applied++;
                println(String.format("  gp=0x%08x  applied to %s [0x%08x..0x%08x]",
                    gpValue, blk.getName(), s.getOffset(), e.getOffset()));
            } catch (Exception ex) {
                printerr("  failed on " + blk.getName() + ": " + ex.getMessage());
            }
        }
        println(String.format("gp=0x%08x applied to %d executable blocks",
            gpValue, applied));
    }
}
