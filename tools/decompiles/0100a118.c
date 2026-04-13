
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0100a118(void)

{
  int in_ep;
  undefined2 in_lp;
  
  *(undefined4 *)(in_ep + 8) = 0;
  __nop();
  __nop();
  __nop();
  *(undefined2 *)(in_ep + 0xb4) = in_lp;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

