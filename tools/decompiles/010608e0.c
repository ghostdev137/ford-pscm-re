
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010608e0(void)

{
  uint unaff_tp;
  uint in_r25;
  int in_ep;
  
  *(uint *)(in_ep + 0xa8) = unaff_tp | in_r25;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

