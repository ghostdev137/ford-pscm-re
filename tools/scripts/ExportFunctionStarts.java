// Headless: export function entrypoints in a given address range to a text file.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import java.io.File;
import java.io.PrintWriter;

public class ExportFunctionStarts extends GhidraScript {
    private long parseLongArg(String value) {
        String s = value.trim().toLowerCase();
        if (s.startsWith("0x")) {
            return Long.parseUnsignedLong(s.substring(2), 16);
        }
        return Long.parseLong(s);
    }

    @Override
    public void run() throws Exception {
        String outPath = System.getenv("FUNCTION_STARTS_OUT");
        if (outPath == null || outPath.trim().isEmpty()) {
            throw new IllegalArgumentException("FUNCTION_STARTS_OUT is required");
        }

        String[] args = getScriptArgs();
        long startOff = args.length > 0 ? parseLongArg(args[0]) : Long.MIN_VALUE;
        long endOff = args.length > 1 ? parseLongArg(args[1]) : Long.MAX_VALUE;

        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Address startAddr = space.getAddress(startOff);
        Address endAddr = space.getAddress(endOff);
        FunctionManager fm = currentProgram.getFunctionManager();

        int exported = 0;
        try (PrintWriter pw = new PrintWriter(new File(outPath), "UTF-8")) {
            for (Function f : fm.getFunctions(true)) {
                Address entry = f.getEntryPoint();
                if (entry.compareTo(startAddr) < 0 || entry.compareTo(endAddr) > 0) {
                    continue;
                }
                pw.println(entry.toString());
                exported++;
            }
        }

        println("EXPORTED function_starts=" + exported + " out=" + outPath);
    }
}
