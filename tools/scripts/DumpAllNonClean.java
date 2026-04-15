// Dump every function (regardless of warnings/size) plus a summary of why each was dropped from clean set.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.nio.file.*;

public class DumpAllNonClean extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path outDir = Paths.get("/tmp/pscm/decompiles_all");
        Files.createDirectories(outDir);
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder summary = new StringBuilder();
        int total = 0, baddata = 0, warning = 0, small = 0, ok = 0;
        for (Function f : fm.getFunctions(true)) {
            total++;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) continue;
            String code = r.getDecompiledFunction().getC();
            String addr = String.format("%08x", f.getEntryPoint().getOffset());
            long size = f.getBody().getNumAddresses();
            String tag = "ok";
            if (code.contains("halt_baddata")) { baddata++; tag = "baddata"; }
            else if (code.contains("WARNING")) { warning++; tag = "warning"; }
            else if (size < 40) { small++; tag = "small"; }
            else ok++;
            summary.append(addr).append(' ').append(size).append(' ').append(tag).append('\n');
            Files.writeString(outDir.resolve(addr + "_" + tag + ".c"), code);
        }
        Files.writeString(outDir.resolve("_summary.txt"),
            "total="+total+" ok="+ok+" small="+small+" warning="+warning+" baddata="+baddata+"\n\n"+summary);
        println("total="+total+" ok="+ok+" small="+small+" warning="+warning+" baddata="+baddata);
    }
}
