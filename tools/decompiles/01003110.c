
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_01003110(void)

{
  int in_CTBP;
  
  (*(code *)(in_CTBP + (uint)*(ushort *)(in_CTBP + 10)))();
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

