
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Instruction at (ram,0x01014e42) overlaps instruction at (ram,0x01014e40)
    */
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x01014e10) */
/* WARNING: Removing unreachable block (ram,0x01014ed0) */
/* WARNING: Removing unreachable block (ram,0x01014ed4) */
/* WARNING: Removing unreachable block (ram,0x01014ee2) */
/* WARNING: Removing unreachable block (ram,0x01014e8e) */
/* WARNING: Removing unreachable block (ram,0x01014ef8) */
/* WARNING: Removing unreachable block (ram,0x01014efc) */
/* WARNING: Removing unreachable block (ram,0x01014f0a) */
/* WARNING: Removing unreachable block (ram,0x01014f2e) */
/* WARNING: Removing unreachable block (ram,0x01014f32) */
/* WARNING: Removing unreachable block (ram,0x01014f44) */
/* WARNING: Removing unreachable block (ram,0x01014f46) */
/* WARNING: Removing unreachable block (ram,0x01014f56) */
/* WARNING: Removing unreachable block (ram,0x01014f58) */
/* WARNING: Removing unreachable block (ram,0x0100909a) */
/* WARNING: Removing unreachable block (ram,0x01014f62) */
/* WARNING: Removing unreachable block (ram,0x01014f8c) */
/* WARNING: Removing unreachable block (ram,0x01014f98) */
/* WARNING: Removing unreachable block (ram,0x01014f9c) */
/* WARNING: Removing unreachable block (ram,0x01014f9e) */
/* WARNING: Removing unreachable block (ram,0x01014fb0) */
/* WARNING: Removing unreachable block (ram,0x01014ffc) */
/* WARNING: Removing unreachable block (ram,0x01015014) */
/* WARNING: Removing unreachable block (ram,0x01015040) */
/* WARNING: Removing unreachable block (ram,0x0101504c) */
/* WARNING: Removing unreachable block (ram,0x01015066) */
/* WARNING: Removing unreachable block (ram,0x01014e92) */
/* WARNING: Removing unreachable block (ram,0x01014e2a) */
/* WARNING: Removing unreachable block (ram,0x01014e94) */
/* WARNING: Removing unreachable block (ram,0x01014e2e) */
/* WARNING: Removing unreachable block (ram,0x01014e30) */
/* WARNING: Removing unreachable block (ram,0x01014e34) */
/* WARNING: Removing unreachable block (ram,0x01014e98) */
/* WARNING: Removing unreachable block (ram,0x01014d10) */
/* WARNING: Removing unreachable block (ram,0x01014d14) */
/* WARNING: Removing unreachable block (ram,0x01014d18) */
/* WARNING: Removing unreachable block (ram,0x01014d1c) */
/* WARNING: Removing unreachable block (ram,0x01014d20) */
/* WARNING: Removing unreachable block (ram,0x01014d48) */
/* WARNING: Removing unreachable block (ram,0x01014da6) */
/* WARNING: Removing unreachable block (ram,0x01014d5e) */
/* WARNING: Removing unreachable block (ram,0x01014dc8) */
/* WARNING: Removing unreachable block (ram,0x01014e5c) */
/* WARNING: Removing unreachable block (ram,0x01014e58) */
/* WARNING: Removing unreachable block (ram,0x01014df2) */
/* WARNING: Removing unreachable block (ram,0x01014dfa) */
/* WARNING: Removing unreachable block (ram,0x01014e64) */
/* WARNING: Removing unreachable block (ram,0x01014e68) */
/* WARNING: Removing unreachable block (ram,0x01014d3c) */
/* WARNING: Removing unreachable block (ram,0x01014d30) */
/* WARNING: Removing unreachable block (ram,0x01014d28) */
/* WARNING: Removing unreachable block (ram,0x01014e40) */
/* WARNING: Removing unreachable block (ram,0x01014de0) */
/* WARNING: Removing unreachable block (ram,0x01014dea) */
/* WARNING: Removing unreachable block (ram,0x01014e42) */
/* WARNING: Removing unreachable block (ram,0x01014e46) */
/* WARNING: Removing unreachable block (ram,0x01014e4a) */
/* WARNING: Removing unreachable block (ram,0x01014dee) */
/* WARNING: Removing unreachable block (ram,0x01014df0) */
/* WARNING: Removing unreachable block (ram,0x01014d24) */
/* WARNING: Removing unreachable block (ram,0x01014d2c) */
/* WARNING: Removing unreachable block (ram,0x01014d34) */
/* WARNING: Removing unreachable block (ram,0x01014d40) */

void FUN_01014e9a(void)

{
  int in_r1;
  int in_r2;
  int in_ep;
  int in_lp;
  
  __nop();
  __nop();
  __nop();
  if (in_r1 << 0x17 < 0) {
    *(int *)(in_ep + 0x78) = in_ep;
    *(byte *)(in_r2 + 0x4c3e) = *(byte *)(in_r2 + 0x4c3e) & 0xfd;
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  __nop();
  __nop();
  __nop();
  __nop();
  if (in_lp < 0) {
    do {
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
      __nop();
    } while( true );
  }
  __nop();
  (*(code *)&LAB_00000030)();
  return;
}

