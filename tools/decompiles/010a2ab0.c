
/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Removing unreachable block (ram,0x010a2ae8) */
/* WARNING: Removing unreachable block (ram,0x010a29f4) */

void FUN_010a2ab0(int param_1)

{
  undefined1 in_r1;
  int in_r2;
  int in_r24;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  undefined2 *puVar1;
  undefined4 in_lp;
  
  *(undefined1 *)(param_1 + -0x6fe) = in_r1;
  puVar1 = (undefined2 *)(uint)*(ushort *)((char)(&DAT_ffff8349)[in_r2] + 0x1a);
  *(ushort *)(in_r25 + -0x3426) = *(ushort *)((char)(&DAT_ffff8349)[in_r2] + 0x1a);
  *(undefined4 *)(in_r25 + 0x13e8) = in_lp;
  UNRECOVERED_JUMPTABLE = (code *)(in_r24 + 0x4081);
  func_0x850b3320();
  *puVar1 = (short)&stack0x00000000;
                    /* WARNING: Could not recover jumptable at 0x010a2b00. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

