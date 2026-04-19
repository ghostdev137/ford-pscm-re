// Trace F-150 CAN descriptor/data entry xrefs and dump containing functions.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.Set;

public class F150CanDescriptorTrace extends GhidraScript {
    private static final class Target {
        final String label;
        final long addr;

        Target(String label, long addr) {
            this.label = label;
            this.addr = addr;
        }
    }

    @Override
    public void run() throws Exception {
        Target[] targets = new Target[] {
            new Target("3D7_RX_ID", 0x10041144L),
            new Target("3D6_RX_ID", 0x1004114cL),
            new Target("3CA_RX_ID", 0x10041154L),
            new Target("3A8_RX_ID", 0x1004116cL),
            new Target("082_TX_ID", 0x100416e0L),
            new Target("3CC_TX_ID", 0x100416eaL),
            new Target("417_TX_ID", 0x100416f4L),
            new Target("3CC_TX_NEAR", 0x100416e8L),
        };

        Path outDir = Path.of(System.getenv().getOrDefault(
            "F150_CAN_DESC_OUT", "/tmp/pscm/f150_can_desc"));
        Files.createDirectories(outDir);

        StringBuilder report = new StringBuilder();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing listing = currentProgram.getListing();
        Memory mem = currentProgram.getMemory();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        Set<Long> dumped = new LinkedHashSet<>();

        for (Target target : targets) {
            Address addr = toAddr(target.addr);
            report.append(String.format("=== %s @ 0x%08x ===\n", target.label, target.addr));

            byte[] bytes = new byte[24];
            int count = mem.getBytes(addr.subtract(8), bytes);
            report.append("BYTES[-8:+16]:");
            for (int i = 0; i < count; i++) {
                report.append(String.format(" %02x", bytes[i] & 0xff));
            }
            report.append('\n');

            Data data = listing.getDefinedDataContaining(addr);
            if (data != null) {
                report.append(String.format(
                    "DATA: %s @ 0x%08x len=%d value=%s\n",
                    data.getDataType().getName(),
                    data.getAddress().getOffset(),
                    data.getLength(),
                    data.getDefaultValueRepresentation()));
            } else {
                report.append("DATA: <none>\n");
            }

            ReferenceIterator refs = rm.getReferencesTo(addr);
            boolean anyRef = false;
            while (refs.hasNext()) {
                anyRef = true;
                Reference ref = refs.next();
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                Instruction ins = listing.getInstructionContaining(ref.getFromAddress());
                report.append(String.format(
                    "REF: from 0x%08x type=%s func=%s insn=%s\n",
                    ref.getFromAddress().getOffset(),
                    ref.getReferenceType(),
                    f != null ? String.format("%s @ 0x%08x", f.getName(), f.getEntryPoint().getOffset()) : "<no function>",
                    ins != null ? ins.toString() : "<no instruction>"));
                if (f != null && dumped.add(f.getEntryPoint().getOffset())) {
                    dumpFunction(outDir, di, f);
                }
            }
            if (!anyRef) {
                report.append("REF: <none>\n");
            }
            report.append('\n');
        }

        Files.writeString(outDir.resolve("_report.txt"), report.toString());
        println("wrote " + outDir.resolve("_report.txt"));
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
