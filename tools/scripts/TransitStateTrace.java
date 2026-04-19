// Focused Transit PSCM runtime-state trace.
// Hunts:
//  - selector reads/writes at ep+0xfa
//  - state writers at +0x2444 / +0x2e20 / +0x2efe
//  - known dispatcher anchor containment
// Dumps a ranked summary plus per-function detail files.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

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

public class TransitStateTrace extends GhidraScript {
    private static final long DISP_SELECTOR = 0xFA;
    private static final long DISP_STATE_BYTE = 0x2444;
    private static final long DISP_STATE_WORD = 0x2E20;
    private static final long DISP_STATE_COMPANION = 0x2EFE;

    private static final long[] KNOWN_ANCHORS = {
        0x0100DB80L, 0x0100DC10L, 0x0100DC76L, 0x0100DD30L,
        0x01002B78L, 0x01090C60L, 0x01090CE4L,
        0x010B4AD4L, 0x010BF258L, 0x010B4C56L, 0x010B4C98L, 0x010B4CAAL,
        0x010CE604L, 0x010CE636L, 0x0107B6DCL
    };

    private static class FuncInfo {
        Function f;
        Set<String> tags = new LinkedHashSet<>();
        List<String> notes = new ArrayList<>();
        int score = 0;
    }

    private boolean mnemonicIsStore(String m) {
        m = m.toLowerCase();
        return m.startsWith("st") || m.startsWith("sst");
    }

    private boolean mnemonicIsLoad(String m) {
        m = m.toLowerCase();
        return m.startsWith("ld") || m.startsWith("sld");
    }

    private boolean operandHasBaseDisp(Instruction ins, String baseReg, long disp) {
        for (int op = 0; op < ins.getNumOperands(); op++) {
            boolean sawBase = false;
            boolean sawDisp = false;
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Register) {
                    if (((Register) o).getName().equalsIgnoreCase(baseReg)) {
                        sawBase = true;
                    }
                }
                else if (o instanceof Scalar) {
                    long v = ((Scalar) o).getSignedValue();
                    if (v == disp) {
                        sawDisp = true;
                    }
                }
            }
            if (sawBase && sawDisp) {
                return true;
            }
        }
        return false;
    }

    private boolean operandHasDisp(Instruction ins, long disp) {
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Scalar) {
                    long signed = ((Scalar) o).getSignedValue();
                    long unsigned = ((Scalar) o).getUnsignedValue();
                    if (signed == disp || unsigned == disp) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    private boolean operandTextHasDisp(Instruction ins, long disp) {
        String text = ins.toString().toLowerCase();
        String hex = Long.toHexString(disp).toLowerCase();
        return text.contains("0x" + hex) || text.contains(hex + "[");
    }

    private boolean instructionMentionsDisp(Instruction ins, long disp) {
        return operandHasDisp(ins, disp) || operandTextHasDisp(ins, disp);
    }

    private String registerList(Instruction ins) {
        Set<String> regs = new LinkedHashSet<>();
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Register) {
                    regs.add(((Register) o).getName());
                }
            }
        }
        return String.join(",", regs);
    }

    private FuncInfo getInfo(Map<Function, FuncInfo> infos, Function f) {
        FuncInfo info = infos.get(f);
        if (info == null) {
            info = new FuncInfo();
            info.f = f;
            infos.put(f, info);
        }
        return info;
    }

    @Override
    public void run() throws Exception {
        String outRoot = System.getenv().getOrDefault("TRANSIT_STATE_TRACE_OUT",
            "/tmp/pscm/transit_state_trace");
        Path outDir = Paths.get(outRoot);
        Files.createDirectories(outDir);

        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        Map<Function, FuncInfo> infos = new LinkedHashMap<>();

        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext() && !monitor.isCancelled()) {
            Function f = fit.next();
            FuncInfo info = null;
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String m = ins.getMnemonicString();

                if (operandHasBaseDisp(ins, "ep", DISP_SELECTOR) || instructionMentionsDisp(ins, DISP_SELECTOR)) {
                    info = getInfo(infos, f);
                    if (mnemonicIsLoad(m)) {
                        info.tags.add("selector_read_ep_fa");
                        info.score += 2;
                    }
                    if (mnemonicIsStore(m)) {
                        info.tags.add("selector_write_ep_fa");
                        info.score += 4;
                    }
                    info.notes.add(String.format("0x%08x  %s  regs=[%s]",
                        ins.getAddress().getOffset(), ins, registerList(ins)));
                }

                if (mnemonicIsStore(m) && instructionMentionsDisp(ins, DISP_STATE_BYTE)) {
                    info = getInfo(infos, f);
                    info.tags.add("write_2444");
                    info.score += 6;
                    info.notes.add(String.format("0x%08x  %s  regs=[%s]",
                        ins.getAddress().getOffset(), ins, registerList(ins)));
                }

                if (mnemonicIsStore(m) && instructionMentionsDisp(ins, DISP_STATE_WORD)) {
                    info = getInfo(infos, f);
                    info.tags.add("write_2e20");
                    info.score += 8;
                    info.notes.add(String.format("0x%08x  %s  regs=[%s]",
                        ins.getAddress().getOffset(), ins, registerList(ins)));
                }

                if (mnemonicIsStore(m) && instructionMentionsDisp(ins, DISP_STATE_COMPANION)) {
                    info = getInfo(infos, f);
                    info.tags.add("write_2efe");
                    info.score += 7;
                    info.notes.add(String.format("0x%08x  %s  regs=[%s]",
                        ins.getAddress().getOffset(), ins, registerList(ins)));
                }
            }

            for (long anchor : KNOWN_ANCHORS) {
                Address a = toAddr(anchor);
                if (f.getBody().contains(a)) {
                    info = getInfo(infos, f);
                    info.tags.add(String.format("contains_%08x", anchor));
                    info.score += 5;
                }
            }
        }

        List<FuncInfo> ranked = new ArrayList<>(infos.values());
        ranked.sort(Comparator
            .comparingInt((FuncInfo fi) -> fi.score).reversed()
            .thenComparingLong(fi -> fi.f.getEntryPoint().getOffset()));

        StringBuilder summary = new StringBuilder();
        summary.append("Transit AM runtime state trace\n\n");
        summary.append("Top functions by selector/state activity:\n\n");
        for (FuncInfo info : ranked) {
            summary.append(String.format("0x%08x  %s  score=%d  size=%d  tags=%s\n",
                info.f.getEntryPoint().getOffset(),
                info.f.getName(),
                info.score,
                info.f.getBody().getNumAddresses(),
                String.join(",", info.tags)));
            for (String note : info.notes) {
                summary.append("  ").append(note).append("\n");
            }
            summary.append("\n");
        }
        Files.writeString(outDir.resolve("summary.txt"), summary.toString());

        int dumped = 0;
        for (FuncInfo info : ranked) {
            if (dumped >= 32) {
                break;
            }
            StringBuilder sb = new StringBuilder();
            Function f = info.f;
            sb.append(String.format("// %s @ 0x%08x size=%d score=%d tags=%s\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses(),
                info.score, String.join(",", info.tags)));
            sb.append("// notes:\n");
            for (String note : info.notes) {
                sb.append("//   ").append(note).append("\n");
            }

            sb.append("// callers:\n");
            for (Function caller : f.getCallingFunctions(monitor)) {
                sb.append(String.format("//   0x%08x %s size=%d\n",
                    caller.getEntryPoint().getOffset(), caller.getName(), caller.getBody().getNumAddresses()));
            }

            sb.append("// refs-to-entry:\n");
            ReferenceIterator refs = rm.getReferencesTo(f.getEntryPoint());
            while (refs.hasNext()) {
                Reference r = refs.next();
                sb.append(String.format("//   %s -> %s type=%s\n",
                    r.getFromAddress(), r.getToAddress(), r.getReferenceType()));
            }

            sb.append("// decompile:\n");
            DecompileResults res = ifc.decompileFunction(f, 60, monitor);
            if (res != null && res.getDecompiledFunction() != null) {
                sb.append(res.getDecompiledFunction().getC());
            }
            else if (res != null) {
                sb.append("// decompile failed: ").append(res.getErrorMessage()).append("\n");
            }
            else {
                sb.append("// decompile returned null\n");
            }
            Files.writeString(outDir.resolve(String.format("%08x.trace.c", f.getEntryPoint().getOffset())), sb.toString());
            dumped++;
        }

        println(summary.toString());
    }
}
