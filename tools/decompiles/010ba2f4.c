
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010ba2f4(void)

{
  undefined2 in_r11;
  undefined2 in_r14;
  undefined2 in_r28;
  undefined2 *in_ep;
  
  in_ep[0x41] = in_r14;
  in_ep[0x52] = (short)DAT_00005c55;
  in_ep[0x42] = *in_ep;
  in_ep[0x66] = in_r28;
  in_ep[0x42] = in_r11;
  in_ep[0x43] = in_r11;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

