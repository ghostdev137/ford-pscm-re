// Count unaff_gp references and resolved DAT_ references across all
// decompilations to measure gp-context impact.
// @category Transit
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.address.AddressSpace;

public class CountGpRefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        // Count xrefs to sample target addresses, pre/post impact check
        long[] samples = {
            0x101d7a5cL, 0x101d7a60L,           // cal -0.8 / -0.5 singleton
            0xfef26382L, 0xfef263deL,           // quiet-gate RAM thresholds
            0xfebec408L, 0xfebf334cL,           // newly-resolved DAT from FUN_100b3e56
            0xfef388caL, 0xfec01984L,           // gp-related markers
        };
        for (long a : samples) {
            int n = 0;
            for (Reference r : rm.getReferencesTo(sp.getAddress(a))) n++;
            println(String.format("  xrefs to 0x%08x: %d", a, n));
        }

        // Overall decompile scan — sample 50 random functions, count unaff_gp
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        int funcsScanned = 0;
        int unaffHits = 0;
        int datFeHits = 0;
        int datHits = 0;
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            if (funcsScanned++ >= 50) break;
            try {
                DecompileResults res = di.decompileFunction(f, 30, monitor);
                if (res.getDecompiledFunction() == null) continue;
                String c = res.getDecompiledFunction().getC();
                int u = 0, df = 0, d = 0;
                int idx = 0;
                while ((idx = c.indexOf("unaff_gp", idx)) >= 0) { u++; idx += 8; }
                idx = 0;
                while ((idx = c.indexOf("DAT_fe", idx)) >= 0) { df++; idx += 6; }
                idx = 0;
                while ((idx = c.indexOf("DAT_", idx)) >= 0) { d++; idx += 4; }
                unaffHits += u; datFeHits += df; datHits += d;
            } catch (Exception e) {}
        }
        di.dispose();
        println(String.format("\nFirst-50-funcs sample: unaff_gp=%d  DAT_fe=%d  DAT_total=%d",
            unaffHits, datFeHits, datHits));
    }
}
