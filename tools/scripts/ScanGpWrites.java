// Read-only scan for instructions that write to r4 (gp) anywhere in the
// current program. V850 C-runtime initializes gp once at boot; this
// script finds every such initialization candidate so we can pick the
// right value to apply via ProgramContext.
//
// Matches three patterns:
//   movhi <hi>, r0, r4  followed by  movea/addi <lo>, r4, r4
//   mov   <imm32>, r4   (single 6-byte instruction)
//   ld.w  <disp>[r0], r4  (absolute load into r4 — rare)
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class ScanGpWrites extends GhidraScript {

    private boolean opRefersToGpOrR4(Instruction ins, int opIndex) {
        if (ins.getNumOperands() <= opIndex) return false;
        String rep = ins.getDefaultOperandRepresentation(opIndex);
        return rep != null && (rep.equals("gp") || rep.equals("r4"));
    }

    private long scalarAt(Instruction ins, int opIndex) {
        for (Object o : ins.getOpObjects(opIndex)) {
            if (o instanceof Scalar) return ((Scalar) o).getSignedValue();
        }
        return Long.MIN_VALUE;
    }

    @Override
    public void run() throws Exception {
        String outDir = System.getenv().getOrDefault("GP_OUT_DIR", "/tmp/pscm/scan_gp");
        Files.createDirectories(Paths.get(outDir));

        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();

        StringBuilder pairs = new StringBuilder();
        StringBuilder movs = new StringBuilder();
        StringBuilder lds = new StringBuilder();

        Instruction prev = null;
        int nPairs = 0, nMovs = 0, nLds = 0;

        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            String mn = ins.getMnemonicString().toLowerCase();

            // Pattern 1: movhi ..., r0, r4 followed by movea/addi ..., r4, r4
            if ("movhi".equalsIgnoreCase(mn)
                && ins.getNumOperands() == 3
                && opRefersToGpOrR4(ins, 2)) {
                // reg1 should be r0 for absolute-value loads (PIC-style)
                String src = ins.getDefaultOperandRepresentation(1);
                if (src != null && src.equals("r0")) {
                    prev = ins;
                    continue;
                }
            }
            if (prev != null) {
                if (("movea".equalsIgnoreCase(mn) || "addi".equalsIgnoreCase(mn))
                    && ins.getNumOperands() == 3
                    && opRefersToGpOrR4(ins, 1)
                    && opRefersToGpOrR4(ins, 2)) {
                    long hi = scalarAt(prev, 0);
                    long lo = scalarAt(ins, 0);
                    if (hi != Long.MIN_VALUE && lo != Long.MIN_VALUE) {
                        long gp = ((hi & 0xFFFFL) << 16) + (short) (lo & 0xFFFFL);
                        gp &= 0xFFFFFFFFL;
                        Function f = fm.getFunctionContaining(prev.getAddress());
                        pairs.append(String.format("  va=0x%08x  %s | %s  -> gp=0x%08x  fn=%s\n",
                            prev.getAddress().getOffset(), prev.toString(), ins.toString(), gp,
                            f != null ? f.getName() + "@0x" + Long.toHexString(f.getEntryPoint().getOffset()) : "<none>"));
                        nPairs++;
                    }
                }
                prev = null;
            }

            // Pattern 2: mov imm32, r4 (6-byte)
            if ("mov".equalsIgnoreCase(mn)
                && ins.getLength() == 6
                && ins.getNumOperands() == 2
                && opRefersToGpOrR4(ins, 1)) {
                long imm = scalarAt(ins, 0);
                Function f = fm.getFunctionContaining(ins.getAddress());
                movs.append(String.format("  va=0x%08x  %s  -> gp=0x%08x  fn=%s\n",
                    ins.getAddress().getOffset(), ins.toString(), imm & 0xFFFFFFFFL,
                    f != null ? f.getName() + "@0x" + Long.toHexString(f.getEntryPoint().getOffset()) : "<none>"));
                nMovs++;
            }

            // Pattern 3: ld.w disp[r0], r4 (absolute load — for completeness)
            if (("ld.w".equalsIgnoreCase(mn) || "ld.hu".equalsIgnoreCase(mn))
                && ins.getNumOperands() == 2
                && opRefersToGpOrR4(ins, 1)) {
                String srcRep = ins.getDefaultOperandRepresentation(0);
                if (srcRep != null && srcRep.contains("[r0]")) {
                    Function f = fm.getFunctionContaining(ins.getAddress());
                    lds.append(String.format("  va=0x%08x  %s  fn=%s\n",
                        ins.getAddress().getOffset(), ins.toString(),
                        f != null ? f.getName() + "@0x" + Long.toHexString(f.getEntryPoint().getOffset()) : "<none>"));
                    nLds++;
                }
            }
        }

        StringBuilder out = new StringBuilder();
        out.append("=== gp/r4 initialization candidates ===\n\n");
        out.append("-- movhi + movea/addi pairs (" + nPairs + ") --\n").append(pairs).append('\n');
        out.append("-- mov imm32 (" + nMovs + ") --\n").append(movs).append('\n');
        out.append("-- ld.w/ld.hu disp[r0] (" + nLds + ") --\n").append(lds).append('\n');

        Files.writeString(Paths.get(outDir, "gp_writes.txt"), out.toString());
        println(String.format("Found: %d movhi-pair, %d mov-imm32, %d ld-abs -> %s",
            nPairs, nMovs, nLds, outDir + "/gp_writes.txt"));
    }
}
