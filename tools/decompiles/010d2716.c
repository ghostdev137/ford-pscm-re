
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010d2716(undefined2 param_1)

{
  int5 iVar1;
  int in_r18;
  int in_r21;
  int in_ep;
  uint in_PSW;
  ushort *in_CTBP;
  
  if ((bool)((byte)(in_PSW >> 3) & 1)) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  __nop();
  __nop();
  *(char *)(in_ep + 0x66) = (char)param_1;
  *(undefined2 *)(in_ep + 0xd0) = param_1;
  iVar1 = (int5)in_r18 + (int5)in_r21;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  iVar1 = (int5)(int)(uint)*(ushort *)(in_ep + 2) + (int5)(int)iVar1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(short *)(in_ep + 0xa4) = (short)iVar1;
  __nop();
  *(short *)(in_ep + 0xa4) = (short)iVar1;
  __nop();
  __nop();
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

