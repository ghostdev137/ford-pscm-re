// Hunt Transit config/DID handling around the local DID table cluster.
// Targets the table containing F10A/F188 and hunts by:
//  - DID immediates
//  - service immediates (0x22 / 0x2e)
//  - movhi+movea/addi pointer construction into the DID table region
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class TransitDidHunt extends GhidraScript {
    private static final long TABLE_START = 0x0100db80L;
    private static final long TABLE_END = 0x0100dc60L;

    private static final long[] TARGET_DIDS = {
        0xf10aL, 0xf188L, 0x0730L
    };

    private static final long[] TARGET_SERVICES = {
        0x22L, 0x2eL
    };

    private boolean contains(long[] arr, long v) {
        for (long x : arr) {
            if (x == v) {
                return true;
            }
        }
        return false;
    }

    private long findScalar(Instruction ins, int op) {
        for (Object o : ins.getOpObjects(op)) {
            if (o instanceof Scalar) {
                return ((Scalar)o).getUnsignedValue();
            }
        }
        return Long.MIN_VALUE;
    }

    private void appendContext(StringBuilder out, Listing listing, Function f) {
        InstructionIterator it = listing.getInstructions(f.getBody(), true);
        int shown = 0;
        while (it.hasNext() && shown < 120) {
            Instruction ins = it.next();
            out.append(String.format("  %08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
            shown++;
        }
        if (it.hasNext()) {
            out.append("  ...\n");
        }
    }

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get("/tmp/pscm/transit_lca_map");
        Files.createDirectories(outDir);

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        Map<Function, List<String>> didHits = new LinkedHashMap<>();
        Map<Function, List<String>> tablePtrHits = new LinkedHashMap<>();
        Map<Function, List<String>> serviceHits = new LinkedHashMap<>();

        for (Function f : fm.getFunctions(true)) {
            List<String> didNotes = new ArrayList<>();
            List<String> ptrNotes = new ArrayList<>();
            List<String> svcNotes = new ArrayList<>();

            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            Instruction prev = null;
            while (it.hasNext() && !monitor.isCancelled()) {
                Instruction ins = it.next();

                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Scalar) {
                            long v = ((Scalar)o).getUnsignedValue() & 0xffffffffL;
                            if (contains(TARGET_DIDS, v)) {
                                didNotes.add(String.format("%s  %s  [imm=0x%04x]",
                                    ins.getAddress(), ins, v));
                            } else if (contains(TARGET_SERVICES, v)) {
                                svcNotes.add(String.format("%s  %s  [svc=0x%02x]",
                                    ins.getAddress(), ins, v));
                            }
                        }
                    }
                }

                if (prev != null &&
                    "movhi".equalsIgnoreCase(prev.getMnemonicString()) &&
                    ("movea".equalsIgnoreCase(ins.getMnemonicString()) || "addi".equalsIgnoreCase(ins.getMnemonicString()))) {
                    if (prev.getNumOperands() >= 3 && ins.getNumOperands() >= 3) {
                        String prevDst = prev.getDefaultOperandRepresentation(2);
                        String insSrc = ins.getDefaultOperandRepresentation(1);
                        if (prevDst.equals(insSrc)) {
                            long hi = findScalar(prev, 0);
                            long lo = findScalar(ins, 0);
                            if (hi != Long.MIN_VALUE && lo != Long.MIN_VALUE) {
                                long addr = ((hi & 0xffffL) << 16) + (short)(lo & 0xffffL);
                                addr &= 0xffffffffL;
                                if (addr >= TABLE_START && addr < TABLE_END) {
                                    ptrNotes.add(String.format("%s / %s  => 0x%08x",
                                        prev, ins, addr));
                                }
                            }
                        }
                    }
                }
                prev = ins;
            }

            if (!didNotes.isEmpty()) {
                didHits.put(f, didNotes);
            }
            if (!ptrNotes.isEmpty()) {
                tablePtrHits.put(f, ptrNotes);
            }
            if (!svcNotes.isEmpty()) {
                serviceHits.put(f, svcNotes);
            }
        }

        StringBuilder summary = new StringBuilder();

        summary.append("=== DID immediate hits ===\n");
        didHits.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .forEach(e -> {
                Function f = e.getKey();
                summary.append(String.format("\n%s @ 0x%08x  did_hits=%d  size=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), e.getValue().size(), f.getBody().getNumAddresses()));
                for (String note : e.getValue()) {
                    summary.append("  ").append(note).append('\n');
                }
                List<String> ptrs = tablePtrHits.get(f);
                if (ptrs != null) {
                    for (String note : ptrs) {
                        summary.append("  PTR ").append(note).append('\n');
                    }
                }
                List<String> svcs = serviceHits.get(f);
                if (svcs != null) {
                    for (String note : svcs) {
                        summary.append("  SVC ").append(note).append('\n');
                    }
                }
            });

        summary.append("\n=== Table pointer builders without DID immediates ===\n");
        tablePtrHits.entrySet().stream()
            .filter(e -> !didHits.containsKey(e.getKey()))
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .forEach(e -> {
                Function f = e.getKey();
                summary.append(String.format("\n%s @ 0x%08x  ptr_hits=%d  size=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), e.getValue().size(), f.getBody().getNumAddresses()));
                for (String note : e.getValue()) {
                    summary.append("  PTR ").append(note).append('\n');
                }
                List<String> svcs = serviceHits.get(f);
                if (svcs != null) {
                    for (String note : svcs) {
                        summary.append("  SVC ").append(note).append('\n');
                    }
                }
            });

        summary.append("\n=== Service 0x22 / 0x2E hits without DID or table-pointer hits ===\n");
        serviceHits.entrySet().stream()
            .filter(e -> !didHits.containsKey(e.getKey()) && !tablePtrHits.containsKey(e.getKey()))
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .limit(40)
            .forEach(e -> {
                Function f = e.getKey();
                summary.append(String.format("\n%s @ 0x%08x  svc_hits=%d  size=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), e.getValue().size(), f.getBody().getNumAddresses()));
                for (String note : e.getValue()) {
                    summary.append("  ").append(note).append('\n');
                }
            });

        Files.writeString(outDir.resolve("transit_did_hunt.txt"), summary.toString());

        for (Function f : didHits.keySet()) {
            StringBuilder ctx = new StringBuilder();
            ctx.append(String.format("// %s @ 0x%08x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            appendContext(ctx, listing, f);
            Files.writeString(outDir.resolve(String.format("%08x.did.txt", f.getEntryPoint().getOffset())), ctx.toString());
        }

        for (Function f : tablePtrHits.keySet()) {
            if (didHits.containsKey(f)) {
                continue;
            }
            StringBuilder ctx = new StringBuilder();
            ctx.append(String.format("// %s @ 0x%08x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            appendContext(ctx, listing, f);
            Files.writeString(outDir.resolve(String.format("%08x.ptr.txt", f.getEntryPoint().getOffset())), ctx.toString());
        }

        println(summary.toString());
    }
}
