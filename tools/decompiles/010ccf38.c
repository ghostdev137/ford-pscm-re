
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010ccf38(void)

{
  int in_ep;
  ushort *in_CTBP;
  
  __nop();
  *(undefined4 *)(in_ep + 0xf8) = 0;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

