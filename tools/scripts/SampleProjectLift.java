// Headless: sample decompile quality from the current function set without reseeding.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import java.io.FileWriter;
import java.io.PrintWriter;

public class SampleProjectLift extends GhidraScript {
    private long parseLongArg(String value) {
        String s = value.trim().toLowerCase();
        if (s.startsWith("0x")) {
            return Long.parseUnsignedLong(s.substring(2), 16);
        }
        return Long.parseLong(s);
    }

    private static String sanitize(String value) {
        if (value == null) {
            return "";
        }
        return value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ').trim();
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        long startOff = args.length > 0 ? parseLongArg(args[0]) : Long.MIN_VALUE;
        long endOff = args.length > 1 ? parseLongArg(args[1]) : Long.MAX_VALUE;
        int sampleLimit = args.length > 2 ? Integer.parseInt(args[2]) : 100;
        long minBodySize = args.length > 3 ? parseLongArg(args[3]) : 40L;
        String sampleOut = System.getenv("SAMPLE_LIFT_OUT");

        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Address startAddr = space.getAddress(startOff);
        Address endAddr = space.getAddress(endOff);

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        PrintWriter sampleWriter = null;
        if (sampleOut != null && !sampleOut.isBlank()) {
            sampleWriter = new PrintWriter(new FileWriter(sampleOut));
            sampleWriter.println("addr\tsize\tstatus\tdetail");
        }

        int totalFns = fm.getFunctionCount();
        int sampled = 0;
        int clean = 0;
        int warnings = 0;
        int baddata = 0;
        int failed = 0;

        for (Function f : fm.getFunctions(true)) {
            if (sampled >= sampleLimit) {
                break;
            }
            Address entry = f.getEntryPoint();
            if (entry.compareTo(startAddr) < 0 || entry.compareTo(endAddr) > 0) {
                continue;
            }
            if (f.getBody().getNumAddresses() < minBodySize) {
                continue;
            }

            sampled++;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || !r.decompileCompleted() || r.getDecompiledFunction() == null) {
                failed++;
                if (sampleWriter != null) {
                    String detail = r == null ? "null result" : sanitize(r.getErrorMessage());
                    if (detail.isEmpty()) {
                        detail = "decompile did not complete";
                    }
                    sampleWriter.println(String.format("%08x\t%d\tfailed\t%s",
                        entry.getOffset(), f.getBody().getNumAddresses(), detail));
                }
                continue;
            }

            String code = r.getDecompiledFunction().getC();
            String status;
            String detail = "";
            if (code.contains("halt_baddata")) {
                baddata++;
                status = "baddata";
                detail = "contains halt_baddata";
            }
            else if (code.contains("WARNING")) {
                warnings++;
                status = "warning";
                detail = "contains WARNING";
            }
            else {
                clean++;
                status = "clean";
            }

            if (sampleWriter != null) {
                sampleWriter.println(String.format("%08x\t%d\t%s\t%s",
                    entry.getOffset(), f.getBody().getNumAddresses(), status, sanitize(detail)));
            }
        }

        if (sampleWriter != null) {
            sampleWriter.close();
        }
        di.dispose();

        println("RESULT total_fns=" + totalFns
            + " sampled=" + sampled
            + " clean=" + clean
            + " warnings=" + warnings
            + " baddata=" + baddata
            + " failed=" + failed);
    }
}
