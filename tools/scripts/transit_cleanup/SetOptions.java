// Set Transit-friendly analyzer defaults before analysis.
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

public class SetOptions extends GhidraScript {
    private Boolean parseEnvBool(String envName) {
        String raw = System.getenv(envName);
        if (raw == null || raw.isBlank()) {
            return null;
        }
        String value = raw.trim().toLowerCase();
        if (value.equals("1") || value.equals("true") || value.equals("yes") || value.equals("on")) {
            return Boolean.TRUE;
        }
        if (value.equals("0") || value.equals("false") || value.equals("no") || value.equals("off")) {
            return Boolean.FALSE;
        }
        return null;
    }

    private void setOptionIfPresent(Map<String, String> options, String name, boolean enabled) {
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

    private void loadBlockIfPresent(String envName, String blockName, long baseAddr, boolean executable, boolean writable) {
        try {
            String raw = System.getenv(envName);
            if (raw == null || raw.isBlank()) {
                return;
            }

            Path path = Path.of(raw);
            if (!Files.isRegularFile(path)) {
                println("skip " + envName + ": not a file: " + path);
                return;
            }

            Memory mem = currentProgram.getMemory();
            AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
            Address start = space.getAddress(baseAddr);
            if (mem.getBlock(start) != null) {
                println("block already loaded at 0x" + Long.toHexString(baseAddr) + ": " + blockName);
                return;
            }

            byte[] data = Files.readAllBytes(path);
            int tx = currentProgram.startTransaction("load " + blockName);
            boolean commit = false;
            try {
                MemoryBlock blk = mem.createInitializedBlock(blockName, start, data.length, (byte) 0, monitor, false);
                mem.setBytes(start, data);
                blk.setRead(true);
                blk.setWrite(writable);
                blk.setExecute(executable);
                commit = true;
                println("loaded " + blockName + " at 0x" + Long.toHexString(baseAddr) + " (" + data.length + " bytes)");
            } finally {
                currentProgram.endTransaction(tx, commit);
            }
        } catch (Exception e) {
            println("skip " + envName + ": " + e);
        }
    }

    @Override
    public void run() throws Exception {
        Map<String, String> options = getCurrentAnalysisOptionsAndValues(currentProgram);
        String[] disableNames = {
            "Aggressive Instruction Finder",
            "Aggressive Instruction Finder.Create Analysis Bookmarks",
            // Transit seeding recovers switch/state flow better than the generic
            // decompiler analyzers, and disabling these keeps imports faster and quieter.
            "Decompiler Parameter ID",
            "Call Convention ID"
        };
        for (String n : disableNames) {
            try {
                if (options.containsKey(n)) {
                    setAnalysisOption(currentProgram, n, "false");
                    println("disabled: " + n);
                } else {
                    println("missing option: " + n);
                }
            } catch (Exception e) {
                println("skip " + n + ": " + e);
            }
        }
        Boolean nonReturning = parseEnvBool("TRANSIT_NONRETURN_DISCOVERY");
        Boolean functionStartSearch = parseEnvBool("TRANSIT_FUNCTION_START_SEARCH");
        Boolean fssSearchDataBlocks = parseEnvBool("TRANSIT_FSS_SEARCH_DATABLOCKS");
        if (nonReturning == null) {
            nonReturning = Boolean.TRUE;
        }
        if (functionStartSearch == null) {
            functionStartSearch = Boolean.TRUE;
        }
        setOptionIfPresent(options, "Non-Returning Functions - Discovered", nonReturning.booleanValue());
        setOptionIfPresent(options, "Function Start Search", functionStartSearch.booleanValue());
        if (fssSearchDataBlocks != null) {
            setOptionIfPresent(options, "Function Start Search.Search Data Blocks", fssSearchDataBlocks.booleanValue());
            setOptionIfPresent(options, "Function Start Search After Code.Search Data Blocks", fssSearchDataBlocks.booleanValue());
            setOptionIfPresent(options, "Function Start Search After Data.Search Data Blocks", fssSearchDataBlocks.booleanValue());
        }

        try {
            AutoAnalysisManager.getAnalysisManager(currentProgram).initializeOptions();
            println("reloaded analyzer scheduler options");
        } catch (Exception e) {
            println("skip analyzer scheduler reload: " + e);
        }

        loadBlockIfPresent("TRANSIT_BLOCK1_PATH", "transit_block1_ram", 0x10000400L, false, true);
        loadBlockIfPresent("TRANSIT_BLOCK2_PATH", "transit_block2_ext", 0x20FF0000L, true, false);
        loadBlockIfPresent("TRANSIT_CAL_PATH", "transit_cal", 0x00FD0000L, false, false);
    }
}
