// Headless: seed aligned instruction starts over a range, analyze, then sample decompile quality.
// @category Probe
// @runtime Java

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.script.GhidraScript;
import ghidra.framework.options.Options;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.listing.Program;

public class SeededLiftReport extends GhidraScript {
    private long parseLongArg(String value) {
        String s = value.trim().toLowerCase();
        if (s.startsWith("0x")) {
            return Long.parseUnsignedLong(s.substring(2), 16);
        }
        return Long.parseLong(s);
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        long startOff = args.length > 0 ? parseLongArg(args[0]) : 0x01000000L;
        long endOff = args.length > 1 ? parseLongArg(args[1]) : 0x010FFFEFL;
        long align = args.length > 2 ? parseLongArg(args[2]) : 2L;
        int sampleLimit = args.length > 3 ? Integer.parseInt(args[3]) : 100;
        long minBodySize = args.length > 4 ? parseLongArg(args[4]) : 40L;

        Memory mem = currentProgram.getMemory();
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Options opts = currentProgram.getOptions(Program.ANALYSIS_PROPERTIES);

        for (String n : new String[] {
                "Aggressive Instruction Finder",
                "Aggressive Instruction Finder.Create Analysis Bookmarks",
                "Decompiler Parameter ID",
                "Call Convention ID",
                "Decompiler Switch Analysis"
        }) {
            try {
                opts.setBoolean(n, false);
            } catch (Exception e) {
                // Best effort only; option names vary across builds.
            }
        }

        AddressSet seeds = new AddressSet();
        long seeded = 0;
        for (long off = startOff; off < endOff; off += align) {
            Address a = space.getAddress(off);
            try {
                byte b0 = mem.getByte(a);
                byte b1 = mem.getByte(a.add(1));
                if ((b0 == (byte) 0xff && b1 == (byte) 0xff) || (b0 == 0 && b1 == 0)) {
                    continue;
                }
                seeds.addRange(a, a);
                seeded++;
            } catch (MemoryAccessException e) {
                // Skip gaps or addresses outside loaded memory.
            }
        }

        println("CONFIG language=" + currentProgram.getLanguage().getLanguageID()
            + " start=0x" + Long.toHexString(startOff)
            + " end=0x" + Long.toHexString(endOff)
            + " align=" + align
            + " sample_limit=" + sampleLimit
            + " min_body=" + minBodySize
            + " seeded=" + seeded);

        new DisassembleCommand(seeds, null, true).applyTo(currentProgram, monitor);
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null);
        mgr.startAnalysis(monitor);

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int totalFns = fm.getFunctionCount();
        int sampled = 0;
        int clean = 0;
        int warnings = 0;
        int baddata = 0;
        int failed = 0;

        for (Function f : fm.getFunctions(true)) {
            if (sampled >= sampleLimit) {
                break;
            }
            if (f.getBody().getNumAddresses() < minBodySize) {
                continue;
            }

            sampled++;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || !r.decompileCompleted() || r.getDecompiledFunction() == null) {
                failed++;
                continue;
            }

            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata")) {
                baddata++;
            } else if (code.contains("WARNING")) {
                warnings++;
            } else {
                clean++;
            }
        }

        println("RESULT total_fns=" + totalFns
            + " sampled=" + sampled
            + " clean=" + clean
            + " warnings=" + warnings
            + " baddata=" + baddata
            + " failed=" + failed);
    }
}
