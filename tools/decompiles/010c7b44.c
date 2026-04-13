
/* WARNING: Removing unreachable block (ram,0x010c7b46) */

void FUN_010c7b44(uint param_1)

{
  undefined1 in_r10;
  short in_r16;
  code *UNRECOVERED_JUMPTABLE;
  int in_r29;
  int in_ep;
  
  *(short *)(in_r29 + -0x5118) = (short)&stack0x00000000;
  *(undefined4 *)(in_ep + 0xf8) = 0;
  *(undefined2 *)(in_ep + 0xcc) = 0;
  *(undefined1 *)(in_ep + 9) = 0;
  *(undefined1 *)(in_ep + 10) = in_r10;
                    /* WARNING: Could not recover jumptable at 0x010c7bb4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(param_1 / (uint)(int)in_r16);
  return;
}

