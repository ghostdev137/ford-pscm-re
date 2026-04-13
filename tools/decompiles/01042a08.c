
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_01042a08(void)

{
  int5 iVar1;
  uint in_r16;
  uint in_r17;
  uint in_r26;
  undefined4 *in_ep;
  
  *(uint *)(&DAT_ffff80e6 + in_r17) = in_r16;
  iVar1 = (int5)(int)~in_r26 + 10;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *in_ep = (int)iVar1;
  in_ep[0x2a] = in_r17 | in_r16;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

