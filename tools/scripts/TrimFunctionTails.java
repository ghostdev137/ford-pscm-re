// Trim function bodies to only instructions reachable from the entry
// point. Ghidra's auto-disassembly often walks linearly past a function's
// real end (past `jr` tail-call, `jmp [lp]` return, `dispose` pop+jump,
// `halt_baddata`) and attributes the resulting garbage to the previous
// function. That pollutes decompiles with halt_baddata() calls and
// phantom logic.
//
// Algorithm:
//   1. For each function, BFS from the entry following fall-through and
//      branch flows. Stop at every terminator (return, indirect jmp,
//      reti, unconditional jr to outside body, halt).
//   2. Collect the reachable instruction set.
//   3. If the function's current body contains addresses NOT in that
//      set, clip the body to exactly the reachable instructions.
//   4. Optionally also clear the listing at the trimmed-away range so
//      the decompiler doesn't try to decode them on re-analysis.
//
// Only runs in dry-run mode unless TRIM_APPLY=1 is set in the env, so
// the first pass is a report.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.CodeUnit;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.FlowType;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;

public class TrimFunctionTails extends GhidraScript {
    private static boolean isTerminator(Instruction ins) {
        FlowType ft = ins.getFlowType();
        // True terminators: return, halt, or unconditional jump with no fallthrough
        if (ft.isTerminal()) return true;
        if (ft.isJump() && !ft.isConditional() && !ft.isCall()) {
            // unconditional jump — ends flow locally. if the target is inside our
            // function we should follow it, otherwise it's a tail call / end.
            return true;  // caller decides; we also add target to frontier
        }
        String mn = ins.getMnemonicString().toLowerCase();
        if (mn.contains("halt") || mn.contains("baddata")) return true;
        if (mn.equals("dispose") || mn.startsWith("dispose ")) {
            // dispose can pop+jump-to-lp (terminator) or pop-only (falls through)
            // Heuristic: if it has a register operand that includes lp, it's terminal
            String s = ins.toString().toLowerCase();
            if (s.contains("lp") || s.contains("[lp]")) return true;
        }
        return false;
    }

    private Set<Address> reachableFromEntry(Function f, Listing listing) {
        Set<Address> seen = new HashSet<>();
        Deque<Address> stack = new ArrayDeque<>();
        stack.push(f.getEntryPoint());
        AddressSetView body = f.getBody();
        while (!stack.isEmpty()) {
            Address a = stack.pop();
            if (seen.contains(a)) continue;
            if (!body.contains(a)) continue;
            Instruction ins = listing.getInstructionAt(a);
            if (ins == null) continue;
            seen.add(a);

            FlowType ft = ins.getFlowType();
            boolean terminal = isTerminator(ins);

            // Fall-through
            if (!terminal && ft.hasFallthrough()) {
                Address next = ins.getMaxAddress().add(1);
                if (body.contains(next)) stack.push(next);
            }
            // Explicit flow targets (branch/jump)
            Address[] targets = ins.getFlows();
            if (targets != null) {
                for (Address t : targets) {
                    if (t != null && body.contains(t)) stack.push(t);
                }
            }
        }
        return seen;
    }

    @Override
    public void run() throws Exception {
        boolean apply = "1".equals(System.getenv("TRIM_APPLY"));
        String outDir = System.getenv().getOrDefault("TRIM_OUT_DIR", "/tmp/pscm/trim_tails");
        Files.createDirectories(Paths.get(outDir));

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        int inspected = 0, trimmed = 0;
        long totalBytesTrimmed = 0;
        StringBuilder log = new StringBuilder();

        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            inspected++;
            Set<Address> reach = reachableFromEntry(f, listing);
            if (reach.isEmpty()) continue;

            AddressSetView body = f.getBody();
            // Compute reachable byte-extent as the union of [addr, maxAddr] of each reachable ins
            AddressSet reachSet = new AddressSet();
            for (Address a : reach) {
                Instruction ins = listing.getInstructionAt(a);
                if (ins != null) {
                    reachSet.addRange(ins.getAddress(), ins.getMaxAddress());
                }
            }
            // Difference: body minus reachable
            AddressSet extra = new AddressSet(body);
            extra.delete(reachSet);
            if (extra.isEmpty()) continue;

            long extraBytes = extra.getNumAddresses();
            // Only act on cases where the "extra" region is contiguous and at the tail
            // (common walked-past-end case). Skip if the extra overlaps internal gaps.
            Address firstExtra = extra.getMinAddress();
            Address lastExtra = extra.getMaxAddress();
            if (firstExtra.compareTo(reachSet.getMaxAddress()) < 0) {
                // Not a tail — skip to avoid misattributing legit internal code
                continue;
            }

            trimmed++;
            totalBytesTrimmed += extraBytes;
            log.append(String.format("%s @ 0x%08x  body=%d  reach=%d  trim=[0x%08x..0x%08x] (%d bytes)\n",
                f.getName(), f.getEntryPoint().getOffset(),
                body.getNumAddresses(), reachSet.getNumAddresses(),
                firstExtra.getOffset(), lastExtra.getOffset(), extraBytes));

            if (apply) {
                try {
                    f.setBody(reachSet);
                    // Clear garbage instructions so re-analysis doesn't re-claim them
                    try { clearListing(extra); } catch (Exception ignored) {}
                } catch (Exception ex) {
                    log.append("  APPLY FAILED: ").append(ex.getMessage()).append('\n');
                }
            }
        }

        String summary = String.format(
            "Inspected %d functions; %d have walked-past-end tails (%d bytes total).%s\n",
            inspected, trimmed, totalBytesTrimmed,
            apply ? " APPLIED." : " DRY-RUN (set TRIM_APPLY=1 to apply).");
        println(summary);
        Files.writeString(Paths.get(outDir, "trim_report.txt"), summary + "\n" + log.toString());
    }
}
