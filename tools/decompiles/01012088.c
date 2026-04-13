
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_01012088(undefined4 param_1)

{
  int5 iVar1;
  byte bVar2;
  int in_r1;
  byte *in_r2;
  int in_ep;
  int in_lp;
  
  __nop();
  bVar2 = *(byte *)(in_ep + 0x1c);
  iVar1 = (int5)in_r1 - (int5)in_lp;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(int *)(in_ep + 0x78) = in_ep;
  *in_r2 = *in_r2 & 0xfd;
  *(undefined4 *)(in_ep + 0x80) = 0;
  *(uint *)(in_ep + 0xa8) = (uint)bVar2;
  if (-1 < (int)iVar1 << 0x17) {
    *(undefined4 *)(in_ep + 0xdc) = param_1;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  (*(code *)0x0)(0);
  return;
}

