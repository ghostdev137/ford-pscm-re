// Dump every Transit FPU instruction (cmpf.s etc.) with surrounding
// context: the function it's in, the preceding 20 instructions (which
// feed the FP register), and any nearby RAM/cal references.
// Also search for any instruction that reads the cal+0x29D4..29E4 band
// via ANY addressing mode (not just movhi+movea).
// @category Transit
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
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class TransitFindCmpfSites extends GhidraScript {
    private static final long BAND_LO = 0x00FD2900L;  // widen around 29D4/29E0
    private static final long BAND_HI = 0x00FD2A20L;
    private static final String OUT = "/tmp/pscm/transit_cmpf_sites";

    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get(OUT));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();

        StringBuilder sites = new StringBuilder();
        sites.append("=== All Transit FPU instructions (cmpf.*, subf.*, addf.*, mulf.*, divf.*, etc.) ===\n");
        int nFp = 0;
        List<Instruction> fpInsns = new ArrayList<>();
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            String mn = ins.getMnemonicString().toLowerCase();
            if (mn.startsWith("cmpf") || mn.startsWith("subf") || mn.startsWith("addf")
                || mn.startsWith("mulf") || mn.startsWith("divf") || mn.startsWith("sqrtf")
                || mn.startsWith("trnc") || mn.startsWith("floorf") || mn.startsWith("ceilf")
                || mn.startsWith("cvtf") || mn.startsWith("maxf") || mn.startsWith("minf")) {
                fpInsns.add(ins);
                nFp++;
                Function f = fm.getFunctionContaining(ins.getAddress());
                sites.append(String.format("\n#%d @ 0x%08x  %s  fn=%s @ 0x%08x\n",
                    nFp, ins.getAddress().getOffset(), ins.toString(),
                    f != null ? f.getName() : "<none>",
                    f != null ? f.getEntryPoint().getOffset() : 0));
                // Show preceding 20 instructions
                sites.append("  preceding context:\n");
                Address a = ins.getAddress();
                for (int i = 0; i < 20; i++) {
                    Instruction p = listing.getInstructionBefore(a);
                    if (p == null) break;
                    sites.append(String.format("    0x%08x  %s\n",
                        p.getAddress().getOffset(), p.toString()));
                    a = p.getAddress();
                }
                // Show following 10 instructions
                sites.append("  following context:\n");
                Address b = ins.getMaxAddress().add(1);
                for (int i = 0; i < 10; i++) {
                    Instruction n = listing.getInstructionAt(b);
                    if (n == null) break;
                    sites.append(String.format("    0x%08x  %s\n",
                        n.getAddress().getOffset(), n.toString()));
                    b = n.getMaxAddress().add(1);
                }
            }
        }
        sites.insert(0, "TOTAL FPU instructions: " + nFp + "\n");
        Files.writeString(Paths.get(OUT, "fpu_sites.txt"), sites.toString());

        // --- Part 2: any reference (READ or WRITE or DATA) into the band ---
        StringBuilder band = new StringBuilder();
        band.append("=== ALL references into cal+0x2900..0x2A20 band (runtime 0x00FD2900..0x00FD2A20) ===\n");
        int nRef = 0;
        for (long a = BAND_LO; a < BAND_HI; a += 4) {
            Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(a);
            for (Reference r : rm.getReferencesTo(addr)) {
                Function f = fm.getFunctionContaining(r.getFromAddress());
                band.append(String.format("  to=0x%08x  from=0x%08x  %s  fn=%s @0x%08x\n",
                    a, r.getFromAddress().getOffset(),
                    r.getReferenceType(),
                    f != null ? f.getName() : "<none>",
                    f != null ? f.getEntryPoint().getOffset() : 0));
                nRef++;
            }
        }
        band.insert(0, "total references: " + nRef + "\n");
        Files.writeString(Paths.get(OUT, "band_refs.txt"), band.toString());

        println(String.format("FPU sites: %d | band xrefs: %d | outputs in %s",
            nFp, nRef, OUT));
    }
}
