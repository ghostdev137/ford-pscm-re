
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Instruction at (ram,0x010c6e9a) overlaps instruction at (ram,0x010c6e98)
    */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_010c6e78(char param_1)

{
  int5 unaff_0001fa00;
  undefined2 uVar1;
  int in_r10;
  undefined1 in_r14;
  int in_r17;
  undefined1 in_r20;
  uint in_r24;
  int in_r25;
  int in_r28;
  int in_r29;
  undefined2 *in_ep;
  int in_lp;
  
  if ((in_r24 & 0x918) != 0) {
    *(BADSPACEBASE **)(in_lp + -0x5128) = register0x0000000c;
    unaff_0001fa00 = (int5)in_r25 + -0x1b2f;
    if (unaff_0001fa00 < 0x80000000) {
      if (unaff_0001fa00 < -0x80000000) {
        unaff_0001fa00 = -0x80000000;
      }
    }
    else {
      unaff_0001fa00 = 0x7fffffff;
    }
  }
  *(undefined1 *)(in_r17 + 0xc00) = in_r14;
  uVar1 = in_ep[0x10];
  *(short *)(in_r28 + -0x5120) = (short)&stack0x00000000;
  if (in_r10 != -1) {
    *(BADSPACEBASE **)((int)unaff_0001fa00 + -0x5120) = register0x0000000c;
    uVar1 = in_ep[0x48];
  }
  func_0x011923e4(*(undefined1 *)(in_ep + 0x10),(int)param_1);
  *in_ep = 0;
  *(undefined1 *)(in_ep + 0x31) = in_r20;
  in_ep[0x61] = uVar1;
  *(short *)(in_r29 + -0x5158) = (short)&stack0x00000000;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

