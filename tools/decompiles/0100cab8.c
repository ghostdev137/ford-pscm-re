
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0100cab8(void)

{
  int *piVar1;
  ushort uVar2;
  int in_r11;
  int in_ep;
  int *in_lp;
  
  uVar2 = *(ushort *)(in_ep + 2);
  __nop();
  __nop();
  piVar1 = (int *)*in_lp;
  *in_lp = (int)piVar1 * (uint)(in_lp != piVar1) + in_r11 * (uint)(in_lp == piVar1);
  __nop();
  __nop();
  __nop();
  *(short *)(uVar2 + 0x9c) = (short)in_lp;
  __nop();
  __nop();
  __nop();
  __nop();
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

