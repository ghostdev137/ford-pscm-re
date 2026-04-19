// Dump instruction context around one or more addresses.
// @category Transit
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.CodeUnit;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;

public class ProbeAddrs extends GhidraScript {
    @Override
    public void run() throws Exception {
        if (getScriptArgs().length == 0) {
            println("usage: ProbeAddrs <addr> [addr...]");
            return;
        }

        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();

        for (String raw : getScriptArgs()) {
            long value = Long.decode(raw);
            Address addr = toAddr(value);
            println("");
            println("============================================================");
            println(String.format("ADDR %s", addr));

            Instruction at = listing.getInstructionAt(addr);
            if (at == null) {
                disassemble(addr);
                at = listing.getInstructionAt(addr);
            }

            CodeUnit cu = listing.getCodeUnitContaining(addr);
            if (cu != null) {
                println(String.format("codeunit %s bytes=%s text=%s",
                    cu.getMinAddress(),
                    bytesHex(cu.getBytes()),
                    cu.toString()));
            } else {
                println("no code unit containing address");
            }

            Function fn = fm.getFunctionContaining(addr);
            if (fn != null) {
                println(String.format("function %s @ %s size=%d",
                    fn.getName(),
                    fn.getEntryPoint(),
                    fn.getBody().getNumAddresses()));
                InstructionIterator it = listing.getInstructions(fn.getBody(), true);
                int shown = 0;
                while (it.hasNext() && shown < 80) {
                    Instruction ins = it.next();
                    if (ins.getAddress().compareTo(addr.subtract(0x20)) < 0) {
                        continue;
                    }
                    if (ins.getAddress().compareTo(addr.add(0x40)) > 0) {
                        break;
                    }
                    println(String.format("  %s  %-20s  %s",
                        ins.getAddress(),
                        bytesHex(ins.getBytes()),
                        ins.toString()));
                    shown++;
                }
            } else {
                println("no containing function");
                InstructionIterator it = listing.getInstructions(addr.subtract(0x20), true);
                int shown = 0;
                while (it.hasNext() && shown < 80) {
                    Instruction ins = it.next();
                    if (ins.getAddress().compareTo(addr.add(0x40)) > 0) {
                        break;
                    }
                    println(String.format("  %s  %-20s  %s",
                        ins.getAddress(),
                        bytesHex(ins.getBytes()),
                        ins.toString()));
                    shown++;
                }
            }
        }
    }

    private String bytesHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b & 0xff));
        }
        return sb.toString();
    }
}
