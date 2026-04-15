import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.WordDataType;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.listing.CodeUnit;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.lang.OperandType;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.pcode.JumpTable;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.SourceType;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/* Pre-script: seeds known-call-targets as function starts before auto-analysis.
 * Reads a file of hex addresses (one per line), disassembles each, then
 * creates a function. It also resolves V850 `switch` instruction tables and
 * promotes their case targets into functions before the analyzers run. */
public class SeedFromJarls extends GhidraScript {
    private static final int MIN_SWITCH_CASES = 3;
    private static final int MAX_SWITCH_CASES = 512;
    private static final int MAX_SWITCH_LOOKBACK = 8;
    private static final long DEFAULT_TARGET_WINDOW = 0x10000;
    private static final long MAX_RELATIVE_OFFSET = 0x20000;

    @Override
    public void run() throws Exception {
        Set<Long> forcedStarts = loadAddressSet(getSeedPaths());
        int seeded = 0;
        int failed = 0;
        for (String path : getSeedPaths()) {
            File f = new File(path);
            if (!f.isFile()) {
                continue;
            }
            int[] counts = seedAddressFile(f);
            seeded += counts[0];
            failed += counts[1];
            println("SeedFromJarls: loaded seeds from " + path +
                " seeded=" + counts[0] + " failed=" + counts[1]);
        }

        Set<Long> processedSwitches = new LinkedHashSet<>();
        int switchFunctions = 0;
        int switchTables = 0;
        for (int round = 1; round <= 8; round++) {
            int[] counts = seedSwitchTargets(processedSwitches, forcedStarts);
            switchTables += counts[0];
            switchFunctions += counts[1];
            println("SeedFromJarls: switch round=" + round +
                " tables=" + counts[0] + " newFunctions=" + counts[1]);
            if (counts[1] == 0) {
                break;
            }
        }

        int forcedFixed = 0;
        for (long forcedOffset : forcedStarts) {
            if (ensureExactFunctionAt(toAddr(forcedOffset))) {
                forcedFixed++;
            }
        }

        println("SeedFromJarls: seeded=" + seeded + " failed=" + failed +
            " switchTables=" + switchTables + " switchFunctions=" + switchFunctions +
            " forcedExact=" + forcedFixed);
    }

    private List<String> getSeedPaths() {
        List<String> paths = new ArrayList<>();
        paths.add("/tmp/transit_decode_stats/jarl_targets_valid.txt");
        paths.add("/Users/rossfisher/ford-pscm-re/tools/ghidra_v850_patched/seeds/transit_AM_jarl_targets.txt");
        return paths;
    }

    private List<String> getJumpSitePaths() {
        List<String> paths = new ArrayList<>();
        paths.add("/Users/rossfisher/ford-pscm-re/tools/ghidra_v850_patched/seeds/transit_jumptable_warning_sites.txt");
        return paths;
    }

    private int[] seedAddressFile(File file) throws Exception {
        int seeded = 0;
        int failed = 0;
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) {
                    continue;
                }
                try {
                    long n = Long.parseLong(line, 16);
                    if (seedFunctionAt(toAddr(n))) {
                        seeded++;
                    }
                    else {
                        failed++;
                    }
                }
                catch (Exception e) {
                    failed++;
                }
            }
        }
        return new int[] { seeded, failed };
    }

    private Set<Long> loadAddressSet(List<String> paths) throws Exception {
        Set<Long> values = new LinkedHashSet<>();
        for (String path : paths) {
            File f = new File(path);
            if (!f.isFile()) {
                continue;
            }
            try (BufferedReader br = new BufferedReader(new FileReader(f))) {
                String line;
                while ((line = br.readLine()) != null) {
                    line = line.trim();
                    if (line.isEmpty()) {
                        continue;
                    }
                    try {
                        values.add(Long.parseLong(line, 16));
                    }
                    catch (NumberFormatException e) {
                        // Ignore malformed lines in supplemental lists.
                    }
                }
            }
        }
        return values;
    }

    private boolean seedFunctionAt(Address addr) {
        if (!isExecutable(addr)) {
            return false;
        }

        try {
            new DisassembleCommand(addr, null, true).applyTo(currentProgram, monitor);
        }
        catch (Exception e) {
            return false;
        }

        if (getFunctionAt(addr) != null) {
            return true;
        }

        try {
            return new CreateFunctionCmd(addr).applyTo(currentProgram, monitor);
        }
        catch (Exception e) {
            return false;
        }
    }

    private boolean ensureExactFunctionAt(Address addr) {
        if (!isExecutable(addr)) {
            return false;
        }

        CodeUnit containing = currentProgram.getListing().getCodeUnitContaining(addr);
        if (containing != null && !containing.getMinAddress().equals(addr)) {
            try {
                currentProgram.getListing().clearCodeUnits(
                    containing.getMinAddress(), containing.getMaxAddress(), false);
            }
            catch (Exception e) {
                return false;
            }
        }

        try {
            new DisassembleCommand(addr, null, true).applyTo(currentProgram, monitor);
        }
        catch (Exception e) {
            return false;
        }

        Function owner = getFunctionContaining(addr);
        if (owner == null) {
            return seedFunctionAt(addr);
        }
        if (owner.getEntryPoint().equals(addr)) {
            return true;
        }

        Address ownerEntry = owner.getEntryPoint();
        try {
            removeFunction(owner);
        }
        catch (Exception e) {
            return false;
        }

        boolean exactCreated = seedFunctionAt(addr);
        if (!ownerEntry.equals(addr)) {
            seedFunctionAt(ownerEntry);
        }
        return exactCreated && getFunctionAt(addr) != null;
    }

    private int[] seedSwitchTargets(Set<Long> processedSwitches, Set<Long> forcedStarts)
            throws Exception {
        Listing listing = currentProgram.getListing();
        Set<Long> candidateSites = new LinkedHashSet<>();
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction insn = it.next();
            if (isIndirectJump(insn)) {
                candidateSites.add(insn.getAddress().getOffset());
            }
        }
        candidateSites.addAll(loadAddressSet(getJumpSitePaths()));

        Set<Long> targets = new LinkedHashSet<>();
        int tables = 0;

        for (long siteOffset : candidateSites) {
            if (monitor.isCancelled()) {
                break;
            }
            if (processedSwitches.contains(siteOffset)) {
                continue;
            }

            Address site = toAddr(siteOffset);
            Instruction insn = ensureIndirectJumpAt(site);
            if (insn == null || !isIndirectJump(insn)) {
                continue;
            }

            TableResult result = detectJumpTable(insn);
            if (result == null || result.targets.size() < MIN_SWITCH_CASES) {
                continue;
            }

            materializeJumpTable(insn, listing, result);
            for (Address target : result.targets) {
                targets.add(target.getOffset());
            }
            processedSwitches.add(siteOffset);
            tables++;
        }

        int created = 0;
        Map<Long, Set<Long>> splitTargets = new LinkedHashMap<>();
        for (long targetOffset : targets) {
            Address target = toAddr(targetOffset);
            Function owner = getFunctionContaining(target);
            if (owner != null && owner.getEntryPoint().getOffset() != targetOffset) {
                long ownerOffset = owner.getEntryPoint().getOffset();
                Set<Long> ownedTargets = splitTargets.get(ownerOffset);
                if (ownedTargets == null) {
                    ownedTargets = new LinkedHashSet<>();
                    splitTargets.put(ownerOffset, ownedTargets);
                }
                ownedTargets.add(targetOffset);
            }
        }

        for (long forcedOffset : forcedStarts) {
            Address target = toAddr(forcedOffset);
            Function owner = getFunctionContaining(target);
            if (owner == null || owner.getEntryPoint().getOffset() == forcedOffset) {
                continue;
            }

            long ownerOffset = owner.getEntryPoint().getOffset();
            Set<Long> ownedTargets = splitTargets.get(ownerOffset);
            if (ownedTargets == null) {
                ownedTargets = new LinkedHashSet<>();
                splitTargets.put(ownerOffset, ownedTargets);
            }
            ownedTargets.add(forcedOffset);
        }

        for (long ownerOffset : splitTargets.keySet()) {
            Function owner = getFunctionAt(toAddr(ownerOffset));
            if (owner == null) {
                continue;
            }
            try {
                removeFunction(owner);
            }
            catch (Exception e) {
                // If the original function can't be removed, keep the old body.
            }
        }

        for (Map.Entry<Long, Set<Long>> entry : splitTargets.entrySet()) {
            for (long splitTarget : entry.getValue()) {
                if (seedFunctionAt(toAddr(splitTarget))) {
                    created++;
                }
            }
            seedFunctionAt(toAddr(entry.getKey()));
        }

        for (long targetOffset : targets) {
            Address target = toAddr(targetOffset);
            if (getFunctionContaining(target) != null) {
                continue;
            }
            if (seedFunctionAt(target)) {
                created++;
            }
        }

        return new int[] { tables, created };
    }

    private Instruction ensureIndirectJumpAt(Address addr) {
        try {
            new DisassembleCommand(addr, null, true).applyTo(currentProgram, monitor);
        }
        catch (Exception e) {
            // Ignore and fall through to whatever is already present.
        }

        Instruction insn = currentProgram.getListing().getInstructionAt(addr);
        if (isIndirectJump(insn)) {
            return insn;
        }

        Instruction before = currentProgram.getListing().getInstructionBefore(addr);
        if (before != null && before.getMaxAddress().compareTo(addr) >= 0 && isIndirectJump(before)) {
            return before;
        }
        return null;
    }

    private boolean isIndirectJump(Instruction insn) {
        if (insn == null || insn.getNumOperands() <= 0) {
            return false;
        }

        String mnemonic = insn.getMnemonicString().toLowerCase();
        if (!"jmp".equals(mnemonic) && !"switch".equals(mnemonic)) {
            return false;
        }

        int operandType = insn.getOperandType(0);
        boolean hasReg = (operandType & OperandType.REGISTER) != 0;
        boolean hasAddr = (operandType & OperandType.ADDRESS) != 0;
        return !(hasAddr && !hasReg);
    }

    private Integer findSwitchCaseCount(Instruction branchInsn) {
        Instruction cursor = branchInsn;
        for (int i = 0; i < MAX_SWITCH_LOOKBACK; i++) {
            cursor = currentProgram.getListing().getInstructionBefore(cursor.getAddress());
            if (cursor == null) {
                break;
            }
            if (!"cmp".equalsIgnoreCase(cursor.getMnemonicString())) {
                continue;
            }
            Integer imm = extractImmediate(cursor);
            if (imm != null && imm >= 0 && imm < MAX_SWITCH_CASES) {
                return imm + 1;
            }
        }
        return null;
    }

    private Address[] getTargetBounds(Instruction insn) {
        Function enclosing = getFunctionContaining(insn.getAddress());
        if (enclosing != null) {
            return new Address[] {
                enclosing.getBody().getMinAddress(),
                enclosing.getBody().getMaxAddress()
            };
        }

        Address min = insn.getAddress();
        Address max = insn.getAddress();
        try {
            Function prev = getFunctionBefore(insn.getAddress());
            if (prev != null) {
                min = prev.getEntryPoint();
            }
            else {
                min = insn.getAddress().subtract(DEFAULT_TARGET_WINDOW);
            }
        }
        catch (Exception e) {
            min = insn.getAddress();
        }
        try {
            Function next = getFunctionAfter(insn.getAddress());
            if (next != null) {
                max = next.getEntryPoint();
            }
            else {
                max = insn.getAddress().add(DEFAULT_TARGET_WINDOW);
            }
        }
        catch (Exception e) {
            max = insn.getAddress();
        }
        return new Address[] { min, max };
    }

    private TableResult detectJumpTable(Instruction insn) throws Exception {
        Address tableBase = insn.getMaxAddress().add(1);
        Integer entryCount = findSwitchCaseCount(insn);
        Address[] strictBounds = entryCount == null ? getTargetBounds(insn) : null;

        TableResult result = tryDetectRelativeTable(tableBase, tableBase, entryCount, strictBounds);
        if (result != null) {
            return result;
        }

        Address aligned = tableBase;
        if ((aligned.getOffset() & 0x3) != 0 && isNopPadding(aligned)) {
            aligned = aligned.add(2);
        }
        if ((aligned.getOffset() & 0x3) != 0) {
            aligned = aligned.add(4 - (aligned.getOffset() & 0x3));
        }
        return tryDetectAbsoluteTable(aligned, entryCount, strictBounds);
    }

    private boolean isNopPadding(Address addr) {
        Integer value = readUnsignedShort(addr);
        return value != null && value.intValue() == 0;
    }

    private TableResult tryDetectRelativeTable(Address tableBase, Address baseAddr, Integer entryCount,
            Address[] bounds) throws Exception {
        TableResult best = null;
        for (boolean signed : new boolean[] { true, false }) {
            for (int scale : new int[] { 2, 1 }) {
                List<Address> targets = new ArrayList<>();
                for (int i = 0; i < MAX_SWITCH_CASES; i++) {
                    Address entry = tableBase.add(i * 2L);
                    Integer raw = readUnsignedShort(entry);
                    if (raw == null) {
                        break;
                    }

                    long rel = signed ? (short) raw.intValue() : raw.longValue();
                    rel *= scale;
                    if (Math.abs(rel) > MAX_RELATIVE_OFFSET) {
                        break;
                    }

                    Address target;
                    try {
                        target = baseAddr.add(rel);
                    }
                    catch (Exception e) {
                        break;
                    }

                    if (!isValidJumpTarget(target, bounds)) {
                        break;
                    }

                    targets.add(target);
                    if (entryCount != null && targets.size() >= entryCount.intValue() + 1) {
                        break;
                    }
                }

                if (targets.size() < MIN_SWITCH_CASES) {
                    continue;
                }

                TableResult result = new TableResult(tableBase, targets, 2, scale,
                    signed ? "rel16s" : "rel16u");
                if (best == null || result.targets.size() > best.targets.size()) {
                    best = result;
                }
            }
        }
        return best;
    }

    private TableResult tryDetectAbsoluteTable(Address tableBase, Integer entryCount, Address[] bounds)
            throws Exception {
        List<Address> targets = new ArrayList<>();
        for (int i = 0; i < MAX_SWITCH_CASES; i++) {
            Address entry = tableBase.add(i * 4L);
            Long raw = readUnsignedInt(entry);
            if (raw == null) {
                break;
            }

            Address target;
            try {
                target = toAddr(raw.longValue());
            }
            catch (Exception e) {
                break;
            }

            if (!isValidJumpTarget(target, bounds)) {
                break;
            }

            targets.add(target);
            if (entryCount != null && targets.size() >= entryCount.intValue() + 1) {
                break;
            }
        }

        if (targets.size() < MIN_SWITCH_CASES) {
            return null;
        }
        return new TableResult(tableBase, targets, 4, 1, "abs32");
    }

    private Integer extractImmediate(Instruction insn) {
        Integer best = null;
        for (int op = 0; op < insn.getNumOperands(); op++) {
            Scalar scalar = insn.getScalar(op);
            if (scalar == null) {
                continue;
            }

            long signed = scalar.getSignedValue();
            long value = signed;
            if (value < 0 && Math.abs(value) < MAX_SWITCH_CASES) {
                value = Math.abs(value);
            }
            if (value < 0 || value >= MAX_SWITCH_CASES) {
                continue;
            }

            int candidate = (int) value;
            if (best == null || candidate < best.intValue()) {
                best = candidate;
            }
        }
        return best;
    }

    private Integer readUnsignedShort(Address addr) {
        try {
            return currentProgram.getMemory().getShort(addr) & 0xffff;
        }
        catch (Exception e) {
            return null;
        }
    }

    private Long readUnsignedInt(Address addr) {
        try {
            return currentProgram.getMemory().getInt(addr) & 0xffffffffL;
        }
        catch (Exception e) {
            return null;
        }
    }

    private boolean isValidJumpTarget(Address target, Address[] bounds) {
        if (!isExecutable(target)) {
            return false;
        }
        if ((target.getOffset() & 1) != 0) {
            return false;
        }
        if (bounds != null) {
            if (target.compareTo(bounds[0]) < 0) {
                return false;
            }
            Address upper = bounds[1];
            try {
                upper = upper.add(0x1000);
            }
            catch (Exception e) {
                // Keep the natural upper bound if the extension overflows.
            }
            if (target.compareTo(upper) > 0) {
                return false;
            }
        }
        return true;
    }

    private void materializeJumpTable(Instruction branchInsn, Listing listing, TableResult result) {
        for (int i = 0; i < result.targets.size(); i++) {
            try {
                Address entry = result.tableBase.add(i * (long) result.entrySize);
                CodeUnit cu = listing.getCodeUnitAt(entry);
                if (cu != null) {
                    listing.clearCodeUnits(entry, entry.add(result.entrySize - 1), false);
                }
                if (result.entrySize == 2) {
                    listing.createData(entry, new WordDataType());
                }
                else {
                    listing.createData(entry, new DWordDataType());
                }
            }
            catch (Exception e) {
                // Keep going; a partial table is still better than none.
            }
        }

        println("SeedFromJarls: table @" + branchInsn.getAddress() +
            " base=" + result.tableBase +
            " entries=" + result.targets.size() +
            " mode=" + result.mode +
            " scale=" + result.scale +
            " firstTarget=" + result.targets.get(0));

        try {
            Function f = getFunctionContaining(branchInsn.getAddress());
            if (f != null) {
                for (Address target : result.targets) {
                    branchInsn.addOperandReference(0, target, RefType.COMPUTED_JUMP,
                        SourceType.ANALYSIS);
                }
                new JumpTable(branchInsn.getAddress(), new ArrayList<>(result.targets), true)
                    .writeOverride(f);
                CreateFunctionCmd.fixupFunctionBody(currentProgram, f, monitor);
            }
        }
        catch (Exception e) {
            // The table data is still useful even if the override fails.
        }
    }

    private boolean isExecutable(Address addr) {
        MemoryBlock block = currentProgram.getMemory().getBlock(addr);
        return block != null && block.isExecute();
    }

    private static final class TableResult {
        final Address tableBase;
        final List<Address> targets;
        final int entrySize;
        final int scale;
        final String mode;

        TableResult(Address tableBase, List<Address> targets, int entrySize, int scale, String mode) {
            this.tableBase = tableBase;
            this.targets = targets;
            this.entrySize = entrySize;
            this.scale = scale;
            this.mode = mode;
        }
    }
}
