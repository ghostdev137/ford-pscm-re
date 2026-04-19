// Hunt Transit full-ELF functions that look like the residual LKA suppress timer path.
// Focuses on EP-relative request/state bytes and nearby compare/increment immediates.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
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

public class TransitLkaTimerHunt extends GhidraScript {
    private static final long[] KEY_IMMEDIATES = {
        0, 1, 2, 3, 4,
        0xe8, 0xe9, 0xea, 0xeb, 0xec, 0xed, 0xee,
        0x2bc, 0x2bd,
        0x1b58, 0x1b59
    };

    private static final long[] KEY_OFFSETS = {
        0x30, 0x3c, 0x48, 0x55, 0x60, 0x62, 0x66, 0x70, 0x7c, 0x7d, 0xfa, 0x2444
    };

    private static class Hit {
        Function fn;
        int score;
        Set<String> tags = new LinkedHashSet<>();
        List<String> lines = new ArrayList<>();
    }

    @Override
    public void run() throws Exception {
        Path out = Paths.get(System.getProperty(
            "transit.lkatimer.out",
            "/tmp/pscm/transit_lka_timer_hunt.txt"));

        Map<Long, Hit> hits = new LinkedHashMap<>();
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext() && !monitor.isCancelled()) {
            Function fn = fit.next();
            Hit hit = null;
            InstructionIterator it = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String text = ins.toString().toLowerCase();
                boolean mentionsEp = false;
                Set<Long> offsetsHere = new LinkedHashSet<>();
                Set<Long> immediatesHere = new LinkedHashSet<>();

                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Register) {
                            if (((Register) o).getName().equalsIgnoreCase("ep")) {
                                mentionsEp = true;
                            }
                        } else if (o instanceof Scalar) {
                            Scalar s = (Scalar) o;
                            long sv = s.getSignedValue();
                            long uv = s.getUnsignedValue();
                            for (long off : KEY_OFFSETS) {
                                if (sv == off || uv == off) {
                                    offsetsHere.add(off);
                                }
                            }
                            for (long imm : KEY_IMMEDIATES) {
                                if (sv == imm || uv == imm) {
                                    immediatesHere.add(imm);
                                }
                            }
                        }
                    }
                }

                for (long off : KEY_OFFSETS) {
                    String hex = Long.toHexString(off);
                    if (text.contains("0x" + hex + "[ep]") || text.contains(hex + "[ep]")) {
                        offsetsHere.add(off);
                        mentionsEp = true;
                    }
                }

                boolean interesting = false;
                int score = 0;

                if (offsetsHere.contains(0x30L) && mentionsEp) {
                    interesting = true;
                    score += 8;
                }
                if (offsetsHere.contains(0x7cL) && mentionsEp) {
                    interesting = true;
                    score += 7;
                }
                if (offsetsHere.contains(0x7dL) && mentionsEp) {
                    interesting = true;
                    score += 10;
                }
                if (offsetsHere.contains(0xfaL) && mentionsEp) {
                    interesting = true;
                    score += 4;
                }
                if (offsetsHere.contains(0x2444L)) {
                    interesting = true;
                    score += 3;
                }

                String mnem = ins.getMnemonicString().toLowerCase();
                boolean looksCompare = mnem.startsWith("cmp") || mnem.startsWith("tst") || mnem.startsWith("set");
                boolean looksMath = mnem.startsWith("add") || mnem.startsWith("sub") || mnem.startsWith("satadd")
                    || mnem.startsWith("satsub") || mnem.startsWith("movea");

                if (!immediatesHere.isEmpty() && (looksCompare || looksMath || mentionsEp)) {
                    interesting = true;
                    score += 2 * immediatesHere.size();
                }

                if (!interesting) {
                    continue;
                }

                if (hit == null) {
                    hit = new Hit();
                    hit.fn = fn;
                    hits.put(fn.getEntryPoint().getOffset(), hit);
                }
                hit.score += score;

                for (long off : offsetsHere) {
                    hit.tags.add(String.format("off_%x", off));
                }
                for (long imm : immediatesHere) {
                    hit.tags.add(String.format("imm_%x", imm));
                }
                if (looksCompare) {
                    hit.tags.add("compare");
                }
                if (looksMath) {
                    hit.tags.add("math");
                }

                hit.lines.add(String.format("0x%08x  %-8s  %s",
                    ins.getAddress().getOffset(),
                    ins.getMnemonicString(),
                    ins.toString()));
            }
        }

        List<Hit> ranked = new ArrayList<>(hits.values());
        ranked.sort(Comparator
            .comparingInt((Hit h) -> h.score).reversed()
            .thenComparingLong(h -> h.fn.getEntryPoint().getOffset()));

        StringBuilder sb = new StringBuilder();
        sb.append("Transit LKA timer hunt\n\n");
        int shown = 0;
        for (Hit h : ranked) {
            if (shown >= 80) {
                break;
            }
            sb.append(String.format("0x%08x  %s  size=%d  score=%d  tags=%s\n",
                h.fn.getEntryPoint().getOffset(),
                h.fn.getName(),
                h.fn.getBody().getNumAddresses(),
                h.score,
                String.join(",", h.tags)));
            int lineCount = 0;
            for (String line : h.lines) {
                sb.append("  ").append(line).append("\n");
                lineCount++;
                if (lineCount >= 40) {
                    sb.append("  ...\n");
                    break;
                }
            }
            sb.append("\n");
            shown++;
        }

        Files.writeString(out, sb.toString());
        println("wrote LKA timer hunt to " + out);
    }
}
