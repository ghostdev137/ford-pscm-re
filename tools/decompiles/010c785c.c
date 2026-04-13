
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010c785c(void)

{
  int in_r16;
  undefined1 in_r23;
  undefined2 in_r25;
  int in_ep;
  
  *(undefined2 *)(in_ep + 0xc4) = in_r25;
  *(undefined1 *)(in_r16 + 0x285e) = in_r23;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

