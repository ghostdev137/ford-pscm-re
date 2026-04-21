// Aggressive analyzer configuration for Transit PSCM imports.
//
// Difference from SetOptions.java:
//   - Keeps "Aggressive Instruction Finder" ENABLED (default behavior) so
//     additional function starts are discovered from raw code bytes.
//   - Leaves Decompiler Parameter ID + Call Convention ID on (default).
//   - Still exposes Non-Returning-Functions + Function Start Search knobs
//     via TRANSIT_* env vars, defaulting both to on.
//
// Produces more functions than SetOptions.java at the cost of some
// false-positive function starts that CleanupBoundaries later trims. For
// environments where the cleanup pass is tuned down or skipped, this
// configuration recovers more LKA-relevant entry points.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public class SetOptionsAggressive extends GhidraScript {
    private Boolean parseEnvBool(String envName) {
        String raw = System.getenv(envName);
        if (raw == null || raw.isBlank()) return null;
        String v = raw.trim().toLowerCase();
        if (v.equals("1") || v.equals("true") || v.equals("yes") || v.equals("on")) return Boolean.TRUE;
        if (v.equals("0") || v.equals("false") || v.equals("no") || v.equals("off")) return Boolean.FALSE;
        return null;
    }

    private void setIfPresent(Map<String, String> options, String name, boolean enabled) {
        try {
            if (options.containsKey(name)) {
                setAnalysisOption(currentProgram, name, enabled ? "true" : "false");
                println((enabled ? "enabled: " : "disabled: ") + name);
            } else {
                println("missing option: " + name);
            }
        } catch (Exception e) {
            println("skip " + name + ": " + e);
        }
    }

    private void loadBlockIfPresent(String env, String name, long base, boolean x, boolean w) {
        try {
            String raw = System.getenv(env);
            if (raw == null || raw.isBlank()) return;
            Path p = Path.of(raw);
            if (!Files.isRegularFile(p)) { println("skip " + env + ": not a file: " + p); return; }
            Memory mem = currentProgram.getMemory();
            AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
            Address start = sp.getAddress(base);
            if (mem.getBlock(start) != null) { println("block already loaded: " + name); return; }
            byte[] data = Files.readAllBytes(p);
            int tx = currentProgram.startTransaction("load " + name);
            try {
                MemoryBlock blk = mem.createInitializedBlock(name, start, data.length, (byte) 0, monitor, false);
                mem.setBytes(start, data);
                blk.setRead(true); blk.setWrite(w); blk.setExecute(x);
                currentProgram.endTransaction(tx, true);
                println("loaded " + name + " at 0x" + Long.toHexString(base) + " (" + data.length + " bytes)");
            } catch (Exception e) {
                currentProgram.endTransaction(tx, false);
                throw e;
            }
        } catch (Exception e) {
            println("skip " + env + ": " + e);
        }
    }

    @Override
    public void run() throws Exception {
        Map<String, String> options = getCurrentAnalysisOptionsAndValues(currentProgram);

        // Explicitly ENABLE aggressive discovery knobs.
        setIfPresent(options, "Aggressive Instruction Finder", true);
        setIfPresent(options, "Aggressive Instruction Finder.Create Analysis Bookmarks", false);

        // Keep the signature analyzers on — they help leaf-handler labeling.
        setIfPresent(options, "Decompiler Parameter ID", true);
        setIfPresent(options, "Call Convention ID", true);

        Boolean nonReturning = parseEnvBool("TRANSIT_NONRETURN_DISCOVERY");
        Boolean fss = parseEnvBool("TRANSIT_FUNCTION_START_SEARCH");
        Boolean fssData = parseEnvBool("TRANSIT_FSS_SEARCH_DATABLOCKS");
        if (nonReturning == null) nonReturning = Boolean.TRUE;
        if (fss == null)          fss = Boolean.TRUE;
        if (fssData == null)      fssData = Boolean.TRUE;

        setIfPresent(options, "Non-Returning Functions - Discovered", nonReturning);
        setIfPresent(options, "Function Start Search", fss);
        setIfPresent(options, "Function Start Search.Search Data Blocks", fssData);
        setIfPresent(options, "Function Start Search After Code.Search Data Blocks", fssData);
        setIfPresent(options, "Function Start Search After Data.Search Data Blocks", fssData);

        try {
            AutoAnalysisManager.getAnalysisManager(currentProgram).initializeOptions();
            println("reloaded analyzer scheduler options");
        } catch (Exception e) {
            println("skip analyzer scheduler reload: " + e);
        }

        loadBlockIfPresent("TRANSIT_BLOCK1_PATH", "transit_block1_ram", 0x10000400L, false, true);
        loadBlockIfPresent("TRANSIT_BLOCK2_PATH", "transit_block2_ext", 0x20FF0000L, true, false);
        loadBlockIfPresent("TRANSIT_CAL_PATH",    "transit_cal",        0x00FD0000L, false, false);
    }
}
