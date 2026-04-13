
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Removing unreachable block (ram,0x0107b33c) */

void FUN_0107b31a(char param_1,uint param_2)

{
  uint uVar1;
  undefined2 in_r10;
  undefined1 in_r12;
  int in_r17;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  *(undefined2 *)(in_ep + 0x22) = in_r10;
  *(undefined1 *)(in_ep + 0x41) = in_r12;
  uVar1 = (uint)*(short *)(in_ep + 0xfa);
  if (param_2 / uVar1 == 0) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  if (param_2 == 0x80000000 && uVar1 == 0xffffffff || uVar1 == 0) {
    __nop();
    *(char *)(in_r17 + 0x400) = param_1 * 'Q';
    *(undefined2 *)(in_ep + 0xc2) = 0;
    *(char *)(in_r17 + 0xc00) = param_1 * 'Q';
    (*(code *)&LAB_0180c808)();
    return;
  }
  *(char *)(in_ep + 1) = (char)in_r10;
  *(undefined1 *)(in_ep + 0x41) = in_r12;
  *(undefined2 *)(in_ep + 0x22) = in_r10;
  *(undefined1 *)(in_ep + 0x62) = 0;
                    /* WARNING: Could not recover jumptable at 0x0107b35a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

