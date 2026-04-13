
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010c072a(void)

{
  int in_ep;
  undefined4 in_lp;
  
  __nop();
  *(undefined4 *)(in_ep + 0xf0) = in_lp;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

