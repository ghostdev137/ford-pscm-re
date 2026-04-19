// Resolve Transit LCA/TJA/ESA candidate addresses to containing functions,
// dump callers, decompilation, and nearby gp/ep byte-store patterns.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashSet;
import java.util.Set;

public class TransitLcaAddrToFunc extends GhidraScript {
    private static final long[] TARGETS = {
        0x01002ad8L, // CAN_Stack_Init / near NvM string region
        0x01002b50L, // PDU descriptor table
        0x01002b78L, // 0x3CC descriptor entry
        0x0103d36eL, // prior 0x3D6 raw-hit region
        0x0103bb5bL,
        0x01041e95L,
        0x01042532L,
        0x01043c03L,
        0x01043cdfL,
        0x01043cf9L,
        0x01043d17L,
        0x01043e6dL,
        0x01043e83L,
        0x01043e9fL,
        0x0105c07cL,
        0x0108d684L, // archived 0x3CA handler
        0x0108f094L, // archived 0x213 handler
        0x01090a78L, // CAN_TX_Task_20ms
        0x01090c60L, // CAN_TX_Dispatch_A
        0x01090ce4L, // CAN_TX_Dispatch_B
        0x0109adbaL,
        0x0109ade2L,
        0x010d172cL,
        0x010d1822L,
        0x010d5eb4L,
        0x010d5f14L,
        0x010e1639L,
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get("/tmp/pscm/transit_lca_map");
        Files.createDirectories(outDir);

        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing listing = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        StringBuilder summary = new StringBuilder();
        Set<Long> dumped = new LinkedHashSet<>();

        for (long raw : TARGETS) {
            Address a = af.getDefaultAddressSpace().getAddress(raw);
            Function f = fm.getFunctionContaining(a);
            if (f == null) {
                try {
                    disassemble(a);
                    f = createFunction(a, null);
                } catch (Exception e) {
                    // Keep going; some targets are data or middle-of-function hits.
                }
                if (f == null) {
                    f = fm.getFunctionContaining(a);
                }
            }

            summary.append(String.format("TARGET 0x%08x\n", raw));
            if (f == null) {
                summary.append("  no containing function\n\n");
                continue;
            }

            long entry = f.getEntryPoint().getOffset();
            summary.append(String.format(
                "  in %s @ 0x%08x size=%d\n",
                f.getName(), entry, f.getBody().getNumAddresses()));

            if (!dumped.add(entry)) {
                summary.append("  already dumped via earlier target\n\n");
                continue;
            }

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("// %s @ 0x%08x size=%d\n",
                f.getName(), entry, f.getBody().getNumAddresses()));
            sb.append(String.format("// triggered by raw target 0x%08x\n", raw));
            sb.append("// callers:\n");
            ReferenceIterator refs = rm.getReferencesTo(f.getEntryPoint());
            int refCount = 0;
            while (refs.hasNext() && refCount < 24) {
                Reference r = refs.next();
                if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) {
                    continue;
                }
                Function caller = fm.getFunctionContaining(r.getFromAddress());
                sb.append(String.format("//   0x%08x  %s\n",
                    r.getFromAddress().getOffset(),
                    caller != null ? caller.getName() : "?"));
                refCount++;
            }

            sb.append("// gp/ep byte stores:\n");
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String m = ins.getMnemonicString().toLowerCase();
                if (!m.equals("st.b") && !m.equals("sst.b")) {
                    continue;
                }
                Object[] ops0 = ins.getOpObjects(0);
                Object[] ops1 = ins.getOpObjects(1);
                String src = "?";
                String base = "";
                long disp = 0;
                for (Object o : ops0) {
                    if (o instanceof Register) {
                        src = ((Register)o).getName();
                    }
                }
                for (Object o : ops1) {
                    if (o instanceof Register) {
                        base = ((Register)o).getName();
                    } else if (o instanceof Scalar) {
                        disp = ((Scalar)o).getSignedValue();
                    }
                }
                if (base.equals("gp") || base.equals("ep")) {
                    sb.append(String.format("//   0x%08x  %s  src=%s base=%s disp=%d (0x%x)\n",
                        ins.getAddress().getOffset(), ins.toString(), src, base, disp, disp));
                }
            }

            sb.append("// decompile:\n");
            DecompileResults res = di.decompileFunction(f, 60, monitor);
            if (res != null && res.getDecompiledFunction() != null) {
                sb.append(res.getDecompiledFunction().getC());
            } else {
                sb.append("// decompile failed\n");
            }

            Files.writeString(outDir.resolve(String.format("%08x.c", entry)), sb.toString());
            summary.append(String.format("  dumped %08x.c\n\n", entry));
        }

        Files.writeString(outDir.resolve("_summary.txt"), summary.toString());
        println(summary.toString());
    }
}
