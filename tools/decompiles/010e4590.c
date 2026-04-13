
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010e4590(void)

{
  ushort uVar1;
  undefined1 in_r11;
  int in_r17;
  int in_r20;
  int in_r21;
  undefined1 in_r23;
  int in_ep;
  undefined1 in_lp;
  
  uVar1 = *(ushort *)(in_ep + 0x32);
  *(undefined1 *)(in_r20 + -0x1fe7) = in_r23;
  *(undefined1 *)(in_r17 + -0x17e7) = in_r11;
  *(uint *)(uVar1 + 0x7842) = (uint)uVar1;
  *(undefined1 *)(in_r20 + -0x1be7) = in_lp;
  *(undefined1 *)(in_ep + 0x4a) = 0;
  *(undefined1 *)(in_r21 + -0x17e7) = in_r11;
  *(short *)(in_ep + 0xb2) = (short)in_r20;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

