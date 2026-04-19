// Hunt Transit functions that reference interesting constants and optionally
// anchor addresses. Prints compact instruction windows around each hit.
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
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class TransitConstHunt extends GhidraScript {
    private static final long[] CONSTANTS = {
        0xEAL,   // 234 frames
        0xEBL,
        0xECL,
        0xE8L,
        0x2BCL,  // 700
        0x1B58L, // 7000 ms
        0x3CAL,
        0x3CCL,
        0x730L
    };

    private static final long[] ANCHORS = {
        0x0108D684L, // prior 0x3CA handler anchor
        0x01090A78L, // 0x3CC TX task
        0x01090C60L,
        0x01090CE4L,
        0x01002B78L  // 0x3CC PDU descriptor
    };

    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();

        Map<Long, List<String>> hitsByConst = new LinkedHashMap<>();
        for (long c : CONSTANTS) {
            hitsByConst.put(c, new ArrayList<>());
        }

        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) {
                break;
            }
            List<String> localHits = new ArrayList<>();
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (long target : CONSTANTS) {
                    if (insnHasScalar(ins, target)) {
                        localHits.add(String.format("0x%08x  %-8s %s",
                            ins.getAddress().getOffset(), ins.getMnemonicString(), ins.toString()));
                    }
                }
            }
            if (localHits.isEmpty()) {
                continue;
            }
            for (String hit : localHits) {
                for (long target : CONSTANTS) {
                    if (hit.contains(String.format("0x%x", target)) ||
                        hit.contains(String.format(", %d", target)) ||
                        hit.contains(String.format(" %d", target))) {
                        hitsByConst.get(target).add(formatHit(f, hit));
                    }
                }
            }
        }

        println("== Constant hits ==");
        for (long c : CONSTANTS) {
            println(String.format("\nCONST 0x%x (%d)", c, c));
            List<String> hits = hitsByConst.get(c);
            if (hits == null || hits.isEmpty()) {
                println("  (none)");
                continue;
            }
            int shown = 0;
            for (String hit : hits) {
                println(hit);
                shown++;
                if (shown >= 25) {
                    break;
                }
            }
        }

        println("\n== Anchor references ==");
        for (long anchorVal : ANCHORS) {
            Address anchor = toAddr(anchorVal);
            println(String.format("\nANCHOR 0x%08x", anchorVal));
            int count = 0;
            ReferenceIterator rit = rm.getReferencesTo(anchor);
            while (rit.hasNext()) {
                Reference ref = rit.next();
                Function f = getFunctionContaining(ref.getFromAddress());
                println(String.format("  from 0x%08x type=%s func=%s",
                    ref.getFromAddress().getOffset(),
                    ref.getReferenceType(),
                    f == null ? "(none)" :
                        String.format("%s@0x%08x", f.getName(), f.getEntryPoint().getOffset())));
                count++;
                if (count >= 25) {
                    break;
                }
            }
            if (count == 0) {
                println("  (none)");
            }
        }
    }

    private boolean insnHasScalar(Instruction ins, long target) {
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object obj : ins.getOpObjects(op)) {
                if (obj instanceof Scalar) {
                    Scalar s = (Scalar) obj;
                    if (s.getUnsignedValue() == target || s.getSignedValue() == target) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    private String formatHit(Function f, String hit) {
        return String.format("  %s@0x%08x size=%d  %s",
            f.getName(),
            f.getEntryPoint().getOffset(),
            f.getBody().getNumAddresses(),
            hit);
    }
}
