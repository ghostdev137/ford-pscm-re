// Hunt for compare-heavy Transit functions that touch the request/state bytes and
// use signed small immediates that could hide an 8-bit frame counter threshold.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.scalar.Scalar;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class TransitLkaCounterHunt extends GhidraScript {
    private static class Hit {
        Function fn;
        int score;
        Set<String> tags = new LinkedHashSet<>();
        List<String> lines = new ArrayList<>();
        boolean has30;
        boolean has7c;
        boolean has7d;
    }

    @Override
    public void run() throws Exception {
        Path out = Paths.get(System.getProperty(
            "transit.lkacounter.out",
            "/tmp/pscm/transit_lka_counter_hunt.txt"));

        Map<Long, Hit> hits = new LinkedHashMap<>();
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext() && !monitor.isCancelled()) {
            Function fn = fit.next();
            Hit hit = null;
            boolean has30 = false;
            boolean has7c = false;
            boolean has7d = false;
            List<String> localLines = new ArrayList<>();
            int localScore = 0;

            InstructionIterator it = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String text = ins.toString().toLowerCase();
                boolean mentionsEp = false;
                long compareImm = Long.MIN_VALUE;

                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Register && ((Register) o).getName().equalsIgnoreCase("ep")) {
                            mentionsEp = true;
                        } else if (o instanceof Scalar && ins.getMnemonicString().toLowerCase().startsWith("cmp")) {
                            compareImm = ((Scalar) o).getSignedValue();
                        }
                    }
                }

                if (text.contains("0x30[ep]")) {
                    has30 = true;
                    localScore += 8;
                    localLines.add(fmt(ins));
                }
                if (text.contains("0x7c[ep]")) {
                    has7c = true;
                    localScore += 7;
                    localLines.add(fmt(ins));
                }
                if (text.contains("0x7d[ep]")) {
                    has7d = true;
                    localScore += 10;
                    localLines.add(fmt(ins));
                }

                String mnem = ins.getMnemonicString().toLowerCase();
                if (mnem.startsWith("cmp") && compareImm != Long.MIN_VALUE) {
                    if ((compareImm >= -0x40 && compareImm <= 0x40) ||
                        compareImm == 0xea || compareImm == 0x2bc || compareImm == 0x1b58) {
                        localScore += 3;
                        localLines.add(fmt(ins));
                    }
                } else if (mentionsEp &&
                    (mnem.startsWith("add") || mnem.startsWith("sub") || mnem.startsWith("satadd") ||
                     mnem.startsWith("satsub") || mnem.startsWith("movea"))) {
                    localLines.add(fmt(ins));
                }
            }

            int offsetCount = (has30 ? 1 : 0) + (has7c ? 1 : 0) + (has7d ? 1 : 0);
            if (offsetCount < 2) {
                continue;
            }

            hit = new Hit();
            hit.fn = fn;
            hit.score = localScore + offsetCount * 10;
            hit.has30 = has30;
            hit.has7c = has7c;
            hit.has7d = has7d;
            if (has30) hit.tags.add("off_30");
            if (has7c) hit.tags.add("off_7c");
            if (has7d) hit.tags.add("off_7d");
            hit.lines.addAll(localLines);
            hits.put(fn.getEntryPoint().getOffset(), hit);
        }

        List<Hit> ranked = new ArrayList<>(hits.values());
        ranked.sort(Comparator
            .comparingInt((Hit h) -> h.score).reversed()
            .thenComparingLong(h -> h.fn.getEntryPoint().getOffset()));

        StringBuilder sb = new StringBuilder();
        sb.append("Transit LKA counter hunt\n\n");
        for (int i = 0; i < ranked.size() && i < 60; i++) {
            Hit h = ranked.get(i);
            sb.append(String.format("0x%08x  %s  size=%d  score=%d  tags=%s\n",
                h.fn.getEntryPoint().getOffset(),
                h.fn.getName(),
                h.fn.getBody().getNumAddresses(),
                h.score,
                String.join(",", h.tags)));
            int shown = 0;
            for (String line : h.lines) {
                sb.append("  ").append(line).append("\n");
                shown++;
                if (shown >= 50) {
                    sb.append("  ...\n");
                    break;
                }
            }
            sb.append("\n");
        }

        Files.writeString(out, sb.toString());
        println("wrote counter hunt to " + out);
    }

    private String fmt(Instruction ins) {
        return String.format("0x%08x  %-8s  %s",
            ins.getAddress().getOffset(),
            ins.getMnemonicString(),
            ins.toString());
    }
}
