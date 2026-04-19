// Trace read/write/call references for one or more absolute addresses and dump
// the containing functions for the most relevant refs.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

public class F150GlobalRefTrace extends GhidraScript {
    @Override
    public void run() throws Exception {
        if (getScriptArgs().length == 0) {
            println("usage: F150GlobalRefTrace <addr> [addr...]");
            return;
        }

        Path outDir = Path.of(System.getenv().getOrDefault(
            "F150_GLOBAL_TRACE_OUT", "/tmp/pscm/f150_global_trace"));
        Files.createDirectories(outDir);

        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing listing = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        StringBuilder report = new StringBuilder();
        Set<Long> dumped = new LinkedHashSet<>();

        for (String raw : getScriptArgs()) {
            long target = Long.decode(raw);
            Address addr = toAddr(target);
            report.append(String.format("=== 0x%08x ===\n", target));

            ReferenceIterator refs = rm.getReferencesTo(addr);
            Map<String, Integer> counts = new LinkedHashMap<>();
            boolean any = false;
            while (refs.hasNext()) {
                any = true;
                Reference ref = refs.next();
                Instruction ins = listing.getInstructionContaining(ref.getFromAddress());
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                String kind;
                if (ref.getReferenceType().isWrite()) {
                    kind = "WRITE";
                } else if (ref.getReferenceType().isRead()) {
                    kind = "READ";
                } else {
                    kind = ref.getReferenceType().toString();
                }
                counts.put(kind, counts.getOrDefault(kind, 0) + 1);
                report.append(String.format(
                    "%s from 0x%08x func=%s insn=%s\n",
                    kind,
                    ref.getFromAddress().getOffset(),
                    f != null ? String.format("%s @ 0x%08x", f.getName(), f.getEntryPoint().getOffset()) : "<no function>",
                    ins != null ? ins.toString() : "<no instruction>"));
                if (f != null && dumped.add(f.getEntryPoint().getOffset())) {
                    dumpFunction(outDir, di, f);
                }
            }

            if (!any) {
                report.append("<no references>\n");
            } else {
                report.append("counts:");
                for (Map.Entry<String, Integer> e : counts.entrySet()) {
                    report.append(String.format(" %s=%d", e.getKey(), e.getValue()));
                }
                report.append('\n');
            }
            report.append('\n');
        }

        Files.writeString(outDir.resolve("_report.txt"), report.toString());
        println("wrote " + outDir.resolve("_report.txt"));
        di.dispose();
    }

    private void dumpFunction(Path outDir, DecompInterface di, Function f) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("// %s @ 0x%08x size=%d\n",
            f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
        DecompileResults res = di.decompileFunction(f, 60, monitor);
        if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
            sb.append(res.getDecompiledFunction().getC());
        } else {
            sb.append("// decompile failed\n");
        }
        Files.writeString(outDir.resolve(String.format("%08x_%s.c",
            f.getEntryPoint().getOffset(), f.getName())), sb.toString());
    }
}
