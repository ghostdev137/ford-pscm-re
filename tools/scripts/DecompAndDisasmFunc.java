// Decompile + disasm dump of one or more function addresses supplied
// via env TRANSIT_TARGETS (comma-separated hex).
// @category Transit
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import java.nio.file.Files;
import java.nio.file.Paths;

public class DecompAndDisasmFunc extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = System.getenv().getOrDefault("TRANSIT_OUT_DIR", "/tmp/pscm/targeted_decomp");
        Files.createDirectories(Paths.get(outDir));
        String env = System.getenv("TRANSIT_TARGETS");
        if (env == null) { println("Set TRANSIT_TARGETS=hexcsv"); return; }
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (String tok : env.split(",")) {
            String t = tok.trim();
            if (t.isEmpty()) continue;
            long va = Long.parseLong(t.replace("0x",""), 16);
            Address a = sp.getAddress(va);
            Function f = fm.getFunctionAt(a);
            if (f == null) f = fm.getFunctionContaining(a);
            String base = String.format("%08x", va);
            if (f == null) {
                println("no function at/containing 0x" + base);
                continue;
            }
            // Disasm
            StringBuilder dis = new StringBuilder();
            dis.append(String.format("// %s @ 0x%08x  body=%d\n",
                f.getName(), f.getEntryPoint().getOffset(),
                f.getBody().getNumAddresses()));
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                dis.append(String.format("  0x%08x  %s\n",
                    ins.getAddress().getOffset(), ins.toString()));
            }
            Files.writeString(Paths.get(outDir, base + ".asm"), dis.toString());
            // Decomp
            DecompileResults res = di.decompileFunction(f, 60, monitor);
            String c = res.getDecompiledFunction() != null
                ? res.getDecompiledFunction().getC() : "/* failed */";
            Files.writeString(Paths.get(outDir, base + ".c"), c);
            println("wrote " + base + ".asm + .c");
        }
        di.dispose();
    }
}
