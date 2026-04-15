// Spot-check representative clean and warning-lifted F-150 functions.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import java.util.ArrayList;
import java.util.List;

public class F150SpotCheck extends GhidraScript {
    private static final int MIN_FUNC_SIZE = 80;
    private static final int CLEAN_LIMIT = 3;
    private static final int WARNING_LIMIT = 3;
    private static final int BADDATA_LIMIT = 2;

    private static class Sample {
        final Function function;
        final String tag;
        final String code;

        Sample(Function function, String tag, String code) {
            this.function = function;
            this.tag = tag;
            this.code = code;
        }
    }

    private static String classify(String code) {
        if (code.contains("halt_baddata")) {
            return "baddata";
        }
        if (code.contains("WARNING")) {
            return "warning";
        }
        return "clean";
    }

    private static String trimCode(String code, int maxLines) {
        String[] lines = code.split("\\R");
        StringBuilder out = new StringBuilder();
        int n = Math.min(lines.length, maxLines);
        for (int i = 0; i < n; i++) {
            out.append(lines[i]).append('\n');
        }
        if (lines.length > maxLines) {
            out.append("// ... ").append(lines.length - maxLines).append(" more lines\n");
        }
        return out.toString();
    }

    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        List<Sample> clean = new ArrayList<>();
        List<Sample> warning = new ArrayList<>();
        List<Sample> baddata = new ArrayList<>();

        for (Function f : fm.getFunctions(true)) {
            if (f.getBody().getNumAddresses() < MIN_FUNC_SIZE) {
                continue;
            }

            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || !r.decompileCompleted() || r.getDecompiledFunction() == null) {
                continue;
            }

            String code = r.getDecompiledFunction().getC();
            String tag = classify(code);
            if (tag.equals("clean") && clean.size() < CLEAN_LIMIT) {
                clean.add(new Sample(f, tag, code));
            } else if (tag.equals("warning") && warning.size() < WARNING_LIMIT) {
                warning.add(new Sample(f, tag, code));
            } else if (tag.equals("baddata") && baddata.size() < BADDATA_LIMIT) {
                baddata.add(new Sample(f, tag, code));
            }

            if (clean.size() >= CLEAN_LIMIT &&
                warning.size() >= WARNING_LIMIT &&
                baddata.size() >= BADDATA_LIMIT) {
                break;
            }
        }

        println("SPOTCHECK clean=" + clean.size() + " warning=" + warning.size() + " baddata=" + baddata.size());
        printSamples("CLEAN", clean, listing);
        printSamples("WARNING", warning, listing);
        printSamples("BADDATA", baddata, listing);
    }

    private void printSamples(String label, List<Sample> samples, Listing listing) {
        println("\n===== " + label + " SAMPLES =====");
        for (Sample s : samples) {
            Function f = s.function;
            println(String.format(
                "\n--- %s @ 0x%08X size=%d ---",
                f.getName(),
                f.getEntryPoint().getOffset(),
                f.getBody().getNumAddresses()
            ));

            println("Disassembly:");
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            int shown = 0;
            while (it.hasNext() && shown < 12) {
                Instruction ins = it.next();
                println("  " + ins.getAddressString(false, true) + "  " + ins);
                shown++;
            }

            println("\nDecompile:");
            println(trimCode(s.code, 40));
        }
    }
}
