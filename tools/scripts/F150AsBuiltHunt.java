// Hunt F-150 AS-BUILT reader/writer code by DID immediates and table-pointer composition.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class F150AsBuiltHunt extends GhidraScript {
    private static final long TABLE_START = 0x10044b80L;
    private static final long TABLE_END = 0x1004bd20L;

    private static final long[] TARGET_DIDS = {
        0x3003L, 0x301aL, 0x301fL, 0x3020L, 0xde00L, 0xde01L, 0xde02L, 0xde03L, 0xde04L, 0xde05L
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
                return ((Scalar) o).getUnsignedValue();
            }
        }
        return Long.MIN_VALUE;
    }

    @Override
    public void run() throws Exception {
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
                            long v = ((Scalar) o).getUnsignedValue() & 0xffffffffL;
                            if (contains(TARGET_DIDS, v)) {
                                didNotes.add(String.format("%s  %s  [imm=0x%04x]", ins.getAddress(), ins, v));
                            }
                            else if (contains(TARGET_SERVICES, v)) {
                                svcNotes.add(String.format("%s  %s  [svc=0x%02x]", ins.getAddress(), ins, v));
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
                                long addr = ((hi & 0xffffL) << 16) + (short) (lo & 0xffffL);
                                addr &= 0xffffffffL;
                                if (addr >= TABLE_START && addr < TABLE_END) {
                                    ptrNotes.add(String.format(
                                        "%s / %s  => 0x%08x",
                                        prev,
                                        ins,
                                        addr));
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

        println("=== DID immediate hits ===");
        didHits.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .forEach(e -> {
                Function f = e.getKey();
                println(String.format("\n%s @ 0x%08x  did_hits=%d  size=%d",
                    f.getName(), f.getEntryPoint().getOffset(), e.getValue().size(), f.getBody().getNumAddresses()));
                for (String note : e.getValue()) {
                    println("  " + note);
                }
                List<String> ptrs = tablePtrHits.get(f);
                if (ptrs != null) {
                    for (String note : ptrs) {
                        println("  PTR " + note);
                    }
                }
                List<String> svcs = serviceHits.get(f);
                if (svcs != null) {
                    for (String note : svcs) {
                        println("  SVC " + note);
                    }
                }
            });

        println("\n=== Table pointer builders without DID immediates ===");
        tablePtrHits.entrySet().stream()
            .filter(e -> !didHits.containsKey(e.getKey()))
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .forEach(e -> {
                Function f = e.getKey();
                println(String.format("\n%s @ 0x%08x  ptr_hits=%d  size=%d",
                    f.getName(), f.getEntryPoint().getOffset(), e.getValue().size(), f.getBody().getNumAddresses()));
                for (String note : e.getValue()) {
                    println("  PTR " + note);
                }
                List<String> svcs = serviceHits.get(f);
                if (svcs != null) {
                    for (String note : svcs) {
                        println("  SVC " + note);
                    }
                }
            });

        println("\n=== Service 0x22 / 0x2E hits without DID or table-pointer hits ===");
        serviceHits.entrySet().stream()
            .filter(e -> !didHits.containsKey(e.getKey()) && !tablePtrHits.containsKey(e.getKey()))
            .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
            .limit(30)
            .forEach(e -> {
                Function f = e.getKey();
                println(String.format("\n%s @ 0x%08x  svc_hits=%d  size=%d",
                    f.getName(), f.getEntryPoint().getOffset(), e.getValue().size(), f.getBody().getNumAddresses()));
                for (String note : e.getValue()) {
                    println("  " + note);
                }
            });

        println("\n=== Global movhi/movea pointer builds into DID-table region ===");
        InstructionIterator global = listing.getInstructions(true);
        Instruction prev = null;
        while (global.hasNext() && !monitor.isCancelled()) {
            Instruction ins = global.next();
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
                            long addr = ((hi & 0xffffL) << 16) + (short) (lo & 0xffffL);
                            addr &= 0xffffffffL;
                            if (addr >= TABLE_START && addr < TABLE_END) {
                                Function f = getFunctionContaining(prev.getAddress());
                                String where = f != null
                                    ? String.format("%s @ 0x%08x", f.getName(), f.getEntryPoint().getOffset())
                                    : "<no function>";
                                println(String.format("  %s / %s  => 0x%08x  in %s",
                                    prev, ins, addr, where));
                            }
                        }
                    }
                }
            }
            prev = ins;
        }
    }
}
