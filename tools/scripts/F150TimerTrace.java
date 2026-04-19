// Trace readers of F-150 LKA/ESA timer-related calibration mirrors and dump decompilations.
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class F150TimerTrace extends GhidraScript {
    private static final class Target {
        final long addr;
        final String label;

        Target(long addr, String label) {
            this.addr = addr;
            this.label = label;
        }
    }

    private static final List<Target> TARGETS = Arrays.asList(
        new Target(0xfef27adcL, "LKA arm timer"),
        new Target(0xfef27adeL, "LKA re-arm timer"),
        new Target(0xfef27ae0L, "LKA hysteresis/settle A"),
        new Target(0xfef27ae2L, "LKA hysteresis/settle B"),
        new Target(0xfef27e64L, "ESA/TJA timer"),
        new Target(0xfef27e66L, "ESA/TJA hysteresis/settle B"),
        new Target(0xfef27e68L, "ESA/TJA hysteresis/settle A")
    );

    @Override
    public void run() throws Exception {
        Path out = Path.of(System.getenv().getOrDefault("F150_TIMER_TRACE_OUT", "/tmp/pscm/f150_timer_trace"));
        Files.createDirectories(out);

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace sp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        StringBuilder summary = new StringBuilder();
        Map<Function, Set<String>> funcTags = new LinkedHashMap<>();

        for (Target target : TARGETS) {
            Address a = sp.getAddress(target.addr);
            summary.append(String.format("\n=== %s @ 0x%08x ===\n", target.label, target.addr));
            ReferenceIterator refs = rm.getReferencesTo(a);
            int readCount = 0;
            int writeCount = 0;
            while (refs.hasNext()) {
                Reference ref = refs.next();
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                if (f == null) {
                    continue;
                }
                if (ref.getReferenceType().isRead()) {
                    readCount++;
                    funcTags.computeIfAbsent(f, __ -> new LinkedHashSet<>()).add(target.label);
                    summary.append(String.format("  READ  %s  fn=%s @0x%08x\n",
                        ref.getFromAddress(), f.getName(), f.getEntryPoint().getOffset()));
                } else if (ref.getReferenceType().isWrite()) {
                    writeCount++;
                    summary.append(String.format("  WRITE %s  fn=%s @0x%08x\n",
                        ref.getFromAddress(), f.getName(), f.getEntryPoint().getOffset()));
                }
            }
            summary.append(String.format("  totals: reads=%d writes=%d\n", readCount, writeCount));
        }

        summary.append("\n=== Consumer Functions ===\n");
        for (Map.Entry<Function, Set<String>> entry : funcTags.entrySet()) {
            Function f = entry.getKey();
            Set<String> tags = entry.getValue();
            summary.append(String.format("\n--- %s @0x%08x size=%d tags=%s ---\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses(), tags));
            appendInstructions(summary, listing, f, TARGETS);
            appendDecomp(out, di, f);
        }

        Files.writeString(out.resolve("summary.txt"), summary.toString());
        println("wrote " + out.resolve("summary.txt"));
        di.dispose();
    }

    private void appendInstructions(StringBuilder sb, Listing listing, Function f, List<Target> targets) {
        InstructionIterator it = listing.getInstructions(f.getBody(), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            Reference[] refs = ins.getReferencesFrom();
            if (refs.length == 0) {
                continue;
            }
            List<String> hits = new ArrayList<>();
            for (Reference ref : refs) {
                long to = ref.getToAddress().getOffset();
                for (Target target : targets) {
                    if (to == target.addr) {
                        hits.add(String.format("%s/%s", target.label, ref.getReferenceType()));
                    }
                }
            }
            if (!hits.isEmpty()) {
                sb.append(String.format("  %s  %s  refs=%s\n",
                    ins.getAddress(), ins, hits));
            }
        }
    }

    private void appendDecomp(Path out, DecompInterface di, Function f) throws Exception {
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        String code = "// decompile failed\n";
        if (r != null && r.decompileCompleted() && r.getDecompiledFunction() != null) {
            code = r.getDecompiledFunction().getC();
        }
        String safeName = String.format("%08x_%s.c", f.getEntryPoint().getOffset(), f.getName());
        Files.writeString(out.resolve(safeName), code);
    }
}
