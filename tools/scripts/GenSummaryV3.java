// GenSummaryV3: Two-pass classify to skip spurious baddata functions.
// Pass 1: decompile all functions, store raw status.
// Pass 2: for each baddata function, check if any CALL caller's address falls in
//         an ok/small/warning function. If no real caller: skipped_nocaller.
// Also uses updated SLEIGH with MULH/SAT* r0 constraints removed.
// Output: /tmp/pscm/decompiles_v3/_summary.txt + per-function .c files
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class GenSummaryV3 extends GhidraScript {

    /** Classify decompile output into a raw status string. */
    private String classify(String code) {
        if (code == null) return "baddata";
        if (code.contains("halt_baddata") || code.contains("WARNING: Bad instruction")) return "baddata";
        if (code.contains("WARNING:")) return "warning";
        if (code.length() < 100) return "small";
        return "ok";
    }

    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();

        // Rebase if needed
        long loadBase = mem.getBlocks()[0].getStart().getOffset();
        long DESIRED_BASE = 0x01000000L;
        if (loadBase != DESIRED_BASE) {
            println("Rebasing from 0x" + Long.toHexString(loadBase) + " to 0x" + Long.toHexString(DESIRED_BASE));
            currentProgram.setImageBase(space.getAddress(DESIRED_BASE), true);
        }

        MemoryBlock[] blocks = mem.getBlocks();
        long FLASH_START = blocks[0].getStart().getOffset();
        long FLASH_END = blocks[0].getEnd().getOffset();
        println("Flash range: 0x" + Long.toHexString(FLASH_START) + " - 0x" + Long.toHexString(FLASH_END));

        // Add uninit stubs for neighbouring flash banks
        try { mem.createUninitializedBlock("bank_f",  space.getAddress(0x00F00000L), 0x00100000L, false); } catch (Exception e) {}
        try { mem.createUninitializedBlock("bank_11", space.getAddress(0x01100000L), 0x00100000L, false); } catch (Exception e) {}

        // Seed + analyze
        AddressSet seeds = new AddressSet();
        for (long off = FLASH_START; off < FLASH_END; off += 2) {
            Address a = space.getAddress(off);
            try {
                byte b0 = mem.getByte(a), b1 = mem.getByte(a.add(1));
                if ((b0 == (byte)0xFF && b1 == (byte)0xFF) || (b0 == 0 && b1 == 0)) continue;
                seeds.addRange(a, a);
            } catch (MemoryAccessException e) {}
        }
        new DisassembleCommand(seeds, null, true).applyTo(currentProgram, monitor);
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null);
        mgr.startAnalysis(monitor);

        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        // --- PASS 1: Decompile all functions in flash range, store results ---
        // Map from function entry Address -> { rawStatus, code, bodySize }
        Map<Address, String> funcStatus = new HashMap<>();    // entry -> raw status
        Map<Address, String> funcCode   = new HashMap<>();    // entry -> C code (for saving)
        Map<Address, Long>   funcSize   = new HashMap<>();    // entry -> body size
        Map<Address, Boolean> funcFFFF  = new HashMap<>();    // entry -> starts with 0xFFFF

        List<Function> flashFuncs = new ArrayList<>();
        for (Function f : fm.getFunctions(true)) {
            long faddr = f.getEntryPoint().getOffset();
            if (faddr < FLASH_START || faddr > FLASH_END) continue;
            flashFuncs.add(f);
        }
        println("Functions in flash: " + flashFuncs.size());

        for (Function f : flashFuncs) {
            Address ep = f.getEntryPoint();
            long bodySize = f.getBody().getNumAddresses();
            funcSize.put(ep, bodySize);

            // Check 0xFFFF prefix
            boolean isFFFF = false;
            try {
                byte b0 = mem.getByte(ep);
                byte b1 = mem.getByte(ep.add(1));
                isFFFF = (b0 == (byte)0xFF && b1 == (byte)0xFF);
            } catch (Exception e) {}
            funcFFFF.put(ep, isFFFF);

            if (isFFFF) {
                funcStatus.put(ep, "skipped_ffff");
                continue;
            }

            DecompileResults r = di.decompileFunction(f, 30, monitor);
            String code = (r != null && r.getDecompiledFunction() != null)
                ? r.getDecompiledFunction().getC() : null;
            String status = classify(code);
            funcStatus.put(ep, status);
            if (code != null) funcCode.put(ep, code);
        }

        // --- PASS 2: setup --- nothing extra needed; use fm.getFunctionContaining() below.

        // --- PASS 2: Reclassify baddata functions ---
        Path outDir = Paths.get("/tmp/pscm/decompiles_v3");
        Files.createDirectories(outDir);

        int total = 0, ok = 0, small = 0, warning = 0, baddata = 0;
        int skipped_ffff = 0, skipped_nocaller = 0;
        List<String> summaryLines = new ArrayList<>();

        for (Function f : flashFuncs) {
            Address ep = f.getEntryPoint();
            total++;
            long bodySize = funcSize.getOrDefault(ep, 0L);
            String addr = String.format("%08x", ep.getOffset());
            String status = funcStatus.getOrDefault(ep, "baddata");

            if (status.equals("skipped_ffff")) {
                skipped_ffff++;
                summaryLines.add(addr + " " + bodySize + " skipped_ffff");
                continue;
            }

            if (status.equals("baddata")) {
                // Check if any CALL caller is in an ok/small/warning function.
                // Use getFunctionContaining() for exact containment check.
                boolean hasGoodCaller = false;
                ReferenceIterator refs = refMgr.getReferencesTo(ep);
                while (refs.hasNext()) {
                    Reference ref = refs.next();
                    if (!ref.getReferenceType().isCall()) continue;
                    Function callerFn = fm.getFunctionContaining(ref.getFromAddress());
                    if (callerFn == null) continue;  // caller not in any function -> spurious
                    String callerStatus = funcStatus.getOrDefault(callerFn.getEntryPoint(), "baddata");
                    if (callerStatus.equals("ok") || callerStatus.equals("small") || callerStatus.equals("warning")) {
                        hasGoodCaller = true;
                        break;
                    }
                }
                if (!hasGoodCaller) {
                    skipped_nocaller++;
                    summaryLines.add(addr + " " + bodySize + " skipped_nocaller");
                    continue;
                }
                baddata++;
                summaryLines.add(addr + " " + bodySize + " baddata");
                String code = funcCode.get(ep);
                if (code != null) {
                    Files.writeString(outDir.resolve(addr + "_baddata.c"), code);
                }
                continue;
            }

            // ok/small/warning
            summaryLines.add(addr + " " + bodySize + " " + status);
            String code = funcCode.get(ep);
            if (code != null) {
                Files.writeString(outDir.resolve(addr + "_" + status + ".c"), code);
            }
            if (status.equals("ok")) ok++;
            else if (status.equals("small")) small++;
            else if (status.equals("warning")) warning++;
        }

        String header = "total=" + total + " ok=" + ok + " small=" + small
            + " warning=" + warning + " baddata=" + baddata
            + " skipped_ffff=" + skipped_ffff + " skipped_nocaller=" + skipped_nocaller;
        List<String> all = new ArrayList<>();
        all.add(header);
        all.addAll(summaryLines);
        Files.writeString(outDir.resolve("_summary.txt"), String.join("\n", all) + "\n");
        println("SUMMARY: " + header);
        println("Output: " + outDir);
    }
}
