// Dump selected Transit functions plus xrefs to DID/CAN table anchors.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
import java.util.*;

public class TransitDumpTargets extends GhidraScript {
    private static final long[] TARGETS = {
        0x0108BF42L, // UDS diag request handler (repo map)
        0x0108D684L, // 0x3CA RX handler
        0x01090A78L, // 0x3CC TX task chain
        0x01090C60L,
        0x01090CE4L,
    };

    private static final long[] ANCHORS = {
        0x01002B78L, // 0x3CC PDU entry
        0x01002C20L, // 0x730 diag PDU entry
        0x0100DB80L, // DID list start
        0x0100DBE0L, // F10A/F188 cluster
        0x0100DC10L, // backend/descriptor map start
        0x0100DDBAL, // post-descriptor table
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get("/tmp/pscm/transit_targets");
        Files.createDirectories(outDir);

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace space = af.getDefaultAddressSpace();
        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        // Force a bit of local disassembly around targets so the dump is not empty if autoanalysis missed them.
        for (long t : TARGETS) {
            Address a = space.getAddress(t);
            Address b = a.add(0x400);
            new DisassembleCommand(new AddressSet(a, b), null, true).applyTo(currentProgram, monitor);
            if (fm.getFunctionAt(a) == null) {
                try {
                    createFunction(a, null);
                } catch (Exception ignored) {
                }
            }
        }

        StringBuilder refs = new StringBuilder();
        refs.append("// Transit anchor cross references\n");
        for (long anchorVal : ANCHORS) {
            Address anchor = space.getAddress(anchorVal);
            refs.append(String.format("\n== REFS TO 0x%08x ==\n", anchorVal));
            ReferenceIterator it = rm.getReferencesTo(anchor);
            int count = 0;
            while (it.hasNext()) {
                Reference r = it.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                refs.append(String.format("0x%08x  %-8s  %s\n",
                    r.getFromAddress().getOffset(),
                    r.getReferenceType().toString(),
                    f != null ? f.getName() : "?"));
                count++;
            }
            if (count == 0) {
                refs.append("(no references)\n");
            }
        }
        Files.writeString(outDir.resolve("_anchor_refs.txt"), refs.toString());

        DecompInterface di = new DecompInterface();
        DecompileOptions opts = new DecompileOptions();
        di.setOptions(opts);
        di.toggleCCode(true);
        di.toggleSyntaxTree(true);
        di.setSimplificationStyle("decompile");
        di.openProgram(currentProgram);

        for (long t : TARGETS) {
            Address a = space.getAddress(t);
            Function f = fm.getFunctionContaining(a);
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("// target=0x%08x\n", t));
            if (f == null) {
                sb.append("// no function recovered here\n");
                InstructionIterator ii = listing.getInstructions(new AddressSet(a, a.add(0x80)), true);
                while (ii.hasNext()) {
                    Instruction ins = ii.next();
                    sb.append(String.format("0x%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
                }
                Files.writeString(outDir.resolve(String.format("%08x.txt", t)), sb.toString());
                continue;
            }

            sb.append(String.format("// function=%s entry=0x%08x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));

            sb.append("// callers:\n");
            ReferenceIterator refsToFunc = rm.getReferencesTo(f.getEntryPoint());
            int callerCount = 0;
            while (refsToFunc.hasNext()) {
                Reference r = refsToFunc.next();
                if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) {
                    continue;
                }
                Function caller = fm.getFunctionContaining(r.getFromAddress());
                sb.append(String.format("//   0x%08x  %s\n",
                    r.getFromAddress().getOffset(),
                    caller != null ? caller.getName() : "?"));
                callerCount++;
            }
            if (callerCount == 0) {
                sb.append("//   (no call/jump refs)\n");
            }

            sb.append("// references from function body into anchor regions:\n");
            int bodyRefs = 0;
            AddressIterator bodyIt = f.getBody().getAddresses(true);
            while (bodyIt.hasNext()) {
                Address bodyAddr = bodyIt.next();
                Reference[] fromRefs = rm.getReferencesFrom(bodyAddr);
                for (Reference r : fromRefs) {
                    Address to = r.getToAddress();
                    if (to == null) {
                        continue;
                    }
                    long off = to.getOffset();
                    if ((0x01002B50L <= off && off < 0x01002C40L) ||
                        (0x0100DB80L <= off && off < 0x0100DF00L)) {
                        sb.append(String.format("//   0x%08x -> 0x%08x  %s\n",
                            bodyAddr.getOffset(), off, r.getReferenceType().toString()));
                        bodyRefs++;
                    }
                }
            }
            if (bodyRefs == 0) {
                sb.append("//   (none)\n");
            }

            try {
                DecompileResults dr = di.decompileFunction(f, 60, monitor);
                if (dr != null && dr.decompileCompleted() && dr.getDecompiledFunction() != null) {
                    sb.append("\n");
                    sb.append(dr.getDecompiledFunction().getC());
                } else if (dr != null) {
                    sb.append("\n// decompile failed: ");
                    sb.append(dr.getErrorMessage());
                    sb.append("\n");
                } else {
                    sb.append("\n// decompile returned null\n");
                }
            } catch (Exception e) {
                sb.append("\n// exception during decompile: ");
                sb.append(e.toString());
                sb.append("\n");
            }

            Files.writeString(outDir.resolve(String.format("%08x.c", t)), sb.toString());
        }

        println("wrote Transit target dumps to " + outDir);
    }
}
