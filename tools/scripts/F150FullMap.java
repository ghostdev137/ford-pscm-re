// Full map: all writers/readers for fef21xxx and fef23xxx RAM areas,
// plus BlueCruise controller chunking (too big to decompile whole).
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150FullMap extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        StringBuilder report = new StringBuilder();

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();

        // 1. For each RAM global in LKA (fef21a60-80) and LCA (fef23b00-c00, fef238f0-fef23d00),
        //    find unique writer functions and reader count.
        long[][] ranges = {
            {0xfef21a60L, 0xfef21a80L},
            {0xfef238f0L, 0xfef23d00L},
        };
        String[] labels = {"LKA globals (fef21a60-80)", "LCA globals (fef238f0-fef23d00)"};
        for (int ri = 0; ri < ranges.length; ri++) {
            long[] rng = ranges[ri];
            report.append(String.format("\n=== %s ===\n", labels[ri]));
            Map<Function,Integer> writeCounts = new LinkedHashMap<>();
            Map<Function,Integer> readCounts = new LinkedHashMap<>();
            for (long a = rng[0]; a < rng[1]; a += 2) {
                Address addr = asp.getAddress(a);
                ReferenceIterator refs = rm.getReferencesTo(addr);
                while (refs.hasNext()) {
                    Reference r = refs.next();
                    Function f = fm.getFunctionContaining(r.getFromAddress());
                    if (f == null) continue;
                    if (r.getReferenceType().isWrite()) writeCounts.merge(f, 1, Integer::sum);
                    else if (r.getReferenceType().isRead()) readCounts.merge(f, 1, Integer::sum);
                }
            }
            report.append("WRITERS:\n");
            writeCounts.entrySet().stream()
                .sorted((a,b)->b.getValue()-a.getValue())
                .limit(10)
                .forEach(e -> report.append(String.format("  %s @0x%x  writes=%d  size=%d\n",
                    e.getKey().getName(), e.getKey().getEntryPoint().getOffset(), e.getValue(),
                    e.getKey().getBody().getNumAddresses())));
            report.append("READERS:\n");
            readCounts.entrySet().stream()
                .sorted((a,b)->b.getValue()-a.getValue())
                .limit(10)
                .forEach(e -> report.append(String.format("  %s @0x%x  reads=%d  size=%d\n",
                    e.getKey().getName(), e.getKey().getEntryPoint().getOffset(), e.getValue(),
                    e.getKey().getBody().getNumAddresses())));
        }

        // 2. Scan BlueCruise 0x10186afa disasm for clamp constants
        report.append("\n=== 0x10186afa clamp-constant scan ===\n");
        Address start = asp.getAddress(0x10186afaL);
        Function f = fm.getFunctionAt(start);
        if (f != null) {
            Listing L = currentProgram.getListing();
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            Map<Long,Integer> immCount = new TreeMap<>();
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof ghidra.program.model.scalar.Scalar) {
                            long v = ((ghidra.program.model.scalar.Scalar)o).getSignedValue();
                            // interesting: torque/angle authority values
                            if (Math.abs(v) >= 0x200 && Math.abs(v) <= 0x10000) {
                                immCount.merge(v, 1, Integer::sum);
                            }
                        }
                    }
                }
            }
            // Print top by count
            immCount.entrySet().stream()
                .sorted((a,b)->b.getValue()-a.getValue())
                .limit(25)
                .forEach(e -> report.append(String.format("  imm 0x%x (%d dec): %d times\n",
                    e.getKey(), e.getKey(), e.getValue())));

            // Also count writes to fef2xxxx in this function
            Set<Long> writtenAddrs = new TreeSet<>();
            InstructionIterator it2 = L.getInstructions(f.getBody(), true);
            while (it2.hasNext()) {
                Instruction ins = it2.next();
                Reference[] refs = ins.getReferencesFrom();
                for (Reference r : refs) {
                    if (r.getReferenceType().isWrite()) {
                        long a = r.getToAddress().getOffset();
                        if (a >= 0xfef20000L && a < 0xfef30000L) writtenAddrs.add(a);
                    }
                }
            }
            report.append(String.format("\nBlueCruise func writes to %d distinct fef2xxxx globals:\n", writtenAddrs.size()));
            int n=0; for (long a : writtenAddrs) {
                report.append(String.format("  0x%x\n", a));
                if (++n >= 40) { report.append("  ... more\n"); break; }
            }
        }

        Files.writeString(out.resolve("_fullmap.txt"), report.toString());
        println("wrote _fullmap.txt (" + report.length() + " bytes)");
    }
}
