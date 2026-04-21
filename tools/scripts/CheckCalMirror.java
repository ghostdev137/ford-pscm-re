import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.Reference;
public class CheckCalMirror extends GhidraScript {
    @Override public void run() throws Exception {
        long[] addrs = { 0xfef27a5cL, 0xfef27a60L, 0xfef27a70L };
        var rm = currentProgram.getReferenceManager();
        var sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        for (long a : addrs) {
            int n = 0;
            for (Reference r : rm.getReferencesTo(sp.getAddress(a))) n++;
            println(String.format("xrefs to 0x%08x: %d", a, n));
        }
    }
}
