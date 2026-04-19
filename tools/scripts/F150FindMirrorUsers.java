// Find reader/writer functions for selected F-150 calibration RAM mirrors.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
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
import java.util.TreeMap;

public class F150FindMirrorUsers extends GhidraScript {
    private static final class Target {
        final long ramAddr;
        final String label;

        Target(long ramAddr, String label) {
            this.ramAddr = ramAddr;
            this.label = label;
        }
    }

    private static List<Target> buildTargets() {
        return Arrays.asList(
            // Dense feature-envelope block cal+0x0100..0x015c
            new Target(0xfef20100L, "cal+0x0100 (40.0)"),
            new Target(0xfef20104L, "cal+0x0104 (40.0)"),
            new Target(0xfef20108L, "cal+0x0108 (250.0)"),
            new Target(0xfef2010cL, "cal+0x010c (40.0)"),
            new Target(0xfef20110L, "cal+0x0110 (40.0)"),
            new Target(0xfef20114L, "cal+0x0114 (10.0 LKA min speed)"),
            new Target(0xfef20118L, "cal+0x0118 (1.0)"),
            new Target(0xfef2011cL, "cal+0x011c (200.0)"),
            new Target(0xfef20120L, "cal+0x0120 (10.0 LCA min speed)"),
            new Target(0xfef20124L, "cal+0x0124 (1.0)"),
            new Target(0xfef20128L, "cal+0x0128 (66.0)"),
            new Target(0xfef2012cL, "cal+0x012c (50.0)"),
            new Target(0xfef20130L, "cal+0x0130 (0.004)"),
            new Target(0xfef20134L, "cal+0x0134 (1.0)"),
            new Target(0xfef20138L, "cal+0x0138 (1.0)"),
            new Target(0xfef2013cL, "cal+0x013c (0.3)"),
            new Target(0xfef20140L, "cal+0x0140 (0.5 APA min speed)"),
            new Target(0xfef20144L, "cal+0x0144 (8.0 APA max speed)"),
            new Target(0xfef20148L, "cal+0x0148 (0.05)"),
            new Target(0xfef2014cL, "cal+0x014c (20.0)"),
            new Target(0xfef20150L, "cal+0x0150 (20.0)"),
            new Target(0xfef20154L, "cal+0x0154 (40.0)"),
            new Target(0xfef20158L, "cal+0x0158 (100.0)"),
            new Target(0xfef2015cL, "cal+0x015c (85.0)"),

            // Fixed-point axis and step-table family
            new Target(0xfef206baL, "cal+0x06ba axis [0,640,...,19200]"),
            new Target(0xfef2080cL, "cal+0x080c steps [10,20,30,80,100,...]"),
            new Target(0xfef2081eL, "cal+0x081e steps [10,20,30,80,100,...]"),
            new Target(0xfef20830L, "cal+0x0830 steps [10,20,30,80,100,...]"),
            new Target(0xfef20854L, "cal+0x0854 steps [5,10,15,60,80,...]"),
            new Target(0xfef20866L, "cal+0x0866 steps [0,5,10,30,40,...]"),
            new Target(0xfef20878L, "cal+0x0878 steps [0,5,10,20,30,...]")
        );
    }

    @Override
    public void run() throws Exception {
        Path out = Path.of(System.getenv().getOrDefault(
            "F150_MIRROR_USERS_OUT", "/tmp/pscm/f150_lka/_mirror_users.txt"));
        Files.createDirectories(out.getParent());

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();

        StringBuilder sb = new StringBuilder();
        Map<Function, Set<String>> groupedReads = new LinkedHashMap<>();
        Map<Function, Set<String>> groupedWrites = new LinkedHashMap<>();
        Map<String, Integer> readHitCounts = new TreeMap<>();

        for (Target target : buildTargets()) {
            Address a = asp.getAddress(target.ramAddr);
            ReferenceIterator refs = rm.getReferencesTo(a);
            Set<String> readers = new LinkedHashSet<>();
            Set<String> writers = new LinkedHashSet<>();
            List<String> rawRefs = new ArrayList<>();

            while (refs.hasNext()) {
                Reference ref = refs.next();
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                String fn = f == null
                    ? String.format("<none>@0x%08x", ref.getFromAddress().getOffset())
                    : String.format("%s @0x%08x", f.getName(), f.getEntryPoint().getOffset());
                if (ref.getReferenceType().isRead()) {
                    readers.add(fn);
                    if (f != null) {
                        groupedReads.computeIfAbsent(f, __ -> new LinkedHashSet<>()).add(target.label);
                    }
                    readHitCounts.merge(fn, 1, Integer::sum);
                    rawRefs.add(String.format("  READ  from %s at 0x%08x", fn, ref.getFromAddress().getOffset()));
                } else if (ref.getReferenceType().isWrite()) {
                    writers.add(fn);
                    if (f != null) {
                        groupedWrites.computeIfAbsent(f, __ -> new LinkedHashSet<>()).add(target.label);
                    }
                    rawRefs.add(String.format("  WRITE from %s at 0x%08x", fn, ref.getFromAddress().getOffset()));
                }
            }

            sb.append(String.format("=== %s / 0x%08x ===\n", target.label, target.ramAddr));
            sb.append(String.format("readers=%d writers=%d\n", readers.size(), writers.size()));
            for (String line : rawRefs) {
                sb.append(line).append('\n');
            }
            sb.append('\n');
        }

        sb.append("=== Functions grouped by READ coverage ===\n");
        groupedReads.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .forEach(entry -> {
                Function f = entry.getKey();
                sb.append(String.format("%s @0x%08x size=%d reads=%d tags=%s\n",
                    f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses(),
                    entry.getValue().size(), entry.getValue()));
            });

        sb.append("\n=== Functions grouped by WRITE coverage ===\n");
        groupedWrites.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .forEach(entry -> {
                Function f = entry.getKey();
                sb.append(String.format("%s @0x%08x size=%d writes=%d tags=%s\n",
                    f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses(),
                    entry.getValue().size(), entry.getValue()));
            });

        sb.append("\n=== Reader frequency ===\n");
        readHitCounts.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .forEach(entry -> sb.append(String.format("%s count=%d\n", entry.getKey(), entry.getValue())));

        Files.writeString(out, sb.toString());
        println("wrote " + out);
    }
}
