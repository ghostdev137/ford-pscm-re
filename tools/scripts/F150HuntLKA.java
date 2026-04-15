// Hunt LKA-relevant functions in F150 strategy.
// Criteria:
//  1. Float constants near LKA values: 10.0 (min speed), 0.05 (scale), 8.0, 0.5
//  2. Raw int constants: 2047, 4095, 2048 (12-bit field limits), 10000 (timer)
//  3. References to suspected cal offsets 0x114, 0x120, 0x140, 0x144, 0x07ADC
//  4. Functions containing BOTH a speed-float-compare AND a torque-looking multiply
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.address.*;
import java.util.*;

public class F150HuntLKA extends GhidraScript {
    @Override
    public void run() throws Exception {
        Listing L = currentProgram.getListing();
        // Float bit patterns (IEEE 754 single)
        int f10_0 = Float.floatToIntBits(10.0f);    // 0x41200000
        int f0_05 = Float.floatToIntBits(0.05f);    // 0x3D4CCCCD
        int f8_0  = Float.floatToIntBits(8.0f);     // 0x41000000
        int f0_5  = Float.floatToIntBits(0.5f);     // 0x3F000000

        // Immediate int values
        int[] lkaInts = {2047, 4095, 2048, 10000, -102, -2048};

        Map<Long, Integer> scoreByFunc = new HashMap<>();
        Map<Long, Set<String>> tagsByFunc = new HashMap<>();

        FunctionManager fm = currentProgram.getFunctionManager();
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            long addr = f.getEntryPoint().getOffset();
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            int score = 0;
            Set<String> tags = new HashSet<>();
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object obj : ins.getOpObjects(op)) {
                        if (obj instanceof Scalar) {
                            long v = ((Scalar)obj).getSignedValue();
                            int vi = (int)v;
                            if (vi == f10_0) { score+=3; tags.add("10.0f"); }
                            else if (vi == f0_05) { score+=5; tags.add("0.05f"); }
                            else if (vi == f8_0)  { score+=2; tags.add("8.0f"); }
                            else if (vi == f0_5)  { score+=1; tags.add("0.5f"); }
                            for (int li : lkaInts) {
                                if (vi == li) { score+=1; tags.add("i:"+li); }
                            }
                        }
                    }
                }
            }
            if (score >= 4) {
                scoreByFunc.put(addr, score);
                tagsByFunc.put(addr, tags);
            }
        }

        // Top 30 by score
        List<Map.Entry<Long,Integer>> sorted = new ArrayList<>(scoreByFunc.entrySet());
        sorted.sort((a,b)->b.getValue()-a.getValue());
        println("Top LKA-candidate functions (score >= 4):");
        for (int i = 0; i < Math.min(30, sorted.size()); i++) {
            Map.Entry<Long,Integer> e = sorted.get(i);
            Function f = fm.getFunctionAt(currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(e.getKey()));
            String name = f != null ? f.getName() : "?";
            println(String.format("  0x%08x  score=%2d  %s  tags=%s",
                e.getKey(), e.getValue(), name, tagsByFunc.get(e.getKey())));
        }
        println("Total matches: " + sorted.size());
    }
}
