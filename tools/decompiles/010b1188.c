
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010b1188(void)

{
  int5 iVar1;
  uint in_r1;
  int in_r23;
  uint in_r25;
  uint in_ep;
  
  iVar1 = (int5)(int)(in_r25 / (uint)(int)*(short *)((in_ep ^ in_r1) + in_r23 + 2)) + 0x260d;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined4 *)((int)iVar1 + 0x18) = *(undefined4 *)((int)iVar1 + 0x90);
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

