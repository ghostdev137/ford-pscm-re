
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0102f686(uint param_1)

{
  short sVar1;
  uint in_r1;
  undefined4 unaff_tp;
  undefined4 in_r10;
  undefined4 in_r13;
  undefined2 in_r15;
  uint in_r17;
  short in_r18;
  uint in_r25;
  undefined4 uVar2;
  int in_ep;
  undefined2 in_lp;
  
  *(undefined2 *)(in_ep + 0x28) = in_r15;
  *(undefined4 *)(in_ep + 0xbc) = in_r13;
  *(undefined2 *)(in_r25 / (uint)(int)in_r18 - 0x3058) = in_lp;
  *(uint *)(in_ep + 0x60) = in_r1 >> 0x13;
  *(undefined4 *)(in_ep + 0x94) = in_r10;
  uVar2 = *(undefined4 *)(in_ep + 0xa0);
  *(undefined2 *)(in_ep + 0x28) = in_lp;
  *(undefined4 *)(in_ep + 0x68) = unaff_tp;
  *(undefined4 *)(in_ep + 0x94) = in_r10;
  *(uint *)(in_ep + 0xbc) = ~param_1 >> 0x11;
  *(undefined2 *)(in_ep + 0xfe) = 0;
  sVar1 = *(short *)(in_ep + 0xba);
  __nop();
  *(undefined2 *)(*(int *)(in_ep + 0xa0) + -0x7058) = 0;
  *(undefined4 *)(in_ep + 0xbc) = uVar2;
  *(uint *)(in_ep + 0xa8) = in_r17 / (uint)(int)sVar1;
  *(short *)(in_ep + 0x60) = (short)~param_1;
  *(undefined2 *)(in_ep + 0xfe) = 0;
  *(uint *)(in_ep + 0xbc) = ~param_1;
  *(undefined4 *)(in_ep + 0x6c) = uVar2;
  *(undefined2 *)(*(ushort *)(in_ep + 0xa2) + 0x4fa8) = 0;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

