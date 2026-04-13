
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_01009d86(void)

{
  undefined2 in_r14;
  int in_ep;
  
  __nop();
  __nop();
  *(undefined2 *)(in_ep + 0x78) = in_r14;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

