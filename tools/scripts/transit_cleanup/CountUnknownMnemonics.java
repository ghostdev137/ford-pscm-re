// Count unknown/stub mnemonics that appear inside defined functions.
// @category Transit
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class CountUnknownMnemonics extends GhidraScript {
    private static class Stats {
        int count;
        final List<String> examples = new ArrayList<>();
    }

    @Override
    public void run() throws Exception {
        Listing listing = currentProgram.getListing();
        Map<String, Stats> counts = new HashMap<>();
        int total = 0;

        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext()) {
            Function fn = fit.next();
            InstructionIterator it = listing.getInstructions(fn.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String mnem = ins.getMnemonicString();
                if (!isUnknownMnemonic(mnem)) {
                    continue;
                }
                Stats stats = counts.computeIfAbsent(mnem, k -> new Stats());
                stats.count++;
                total++;
                if (stats.examples.size() < 8) {
                    stats.examples.add(String.format("%s in %s", ins.getAddress(), fn.getEntryPoint()));
                }
            }
        }

        println("unknown mnemonic hits in defined functions: " + total);
        List<Map.Entry<String, Stats>> entries = new ArrayList<>(counts.entrySet());
        Collections.sort(entries, (a, b) -> Integer.compare(b.getValue().count, a.getValue().count));
        for (Map.Entry<String, Stats> entry : entries) {
            println(String.format("%-24s count=%d", entry.getKey(), entry.getValue().count));
            for (String example : entry.getValue().examples) {
                println("  " + example);
            }
        }
    }

    private boolean isUnknownMnemonic(String mnem) {
        if (mnem == null) {
            return false;
        }
        return mnem.startsWith("unk_") || mnem.startsWith("??");
    }
}
