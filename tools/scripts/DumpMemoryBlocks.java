// List memory blocks with their initialization state.
// @category F150
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.MemoryBlock;

public class DumpMemoryBlocks extends GhidraScript {
    @Override
    public void run() {
        for (MemoryBlock blk : currentProgram.getMemory().getBlocks()) {
            println(String.format("%-20s 0x%08x..0x%08x  init=%s  r=%s w=%s x=%s  size=0x%x",
                blk.getName(),
                blk.getStart().getOffset(),
                blk.getEnd().getOffset(),
                blk.isInitialized(),
                blk.isRead(), blk.isWrite(), blk.isExecute(),
                blk.getSize()));
        }
    }
}
