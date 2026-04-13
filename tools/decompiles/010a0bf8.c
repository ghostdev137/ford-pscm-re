
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Removing unreachable block (ram,0x010a0c2c) */
/* WARNING: Removing unreachable block (ram,0x010a0c12) */
/* WARNING: Removing unreachable block (ram,0x010a0c06) */
/* WARNING: Removing unreachable block (ram,0x010a8f20) */

void FUN_010a0bf8(void)

{
  byte bVar1;
  undefined1 unaff_gp;
  int in_r23;
  int in_r25;
  int in_ep;
  
  bVar1 = *(byte *)(in_ep + 0x67);
  (&DAT_0000287d)[*(ushort *)(in_ep + 0x1e)] = unaff_gp;
  *(uint *)(in_r25 + -0x3466) = (uint)bVar1;
  *(ushort *)(in_r23 + 0x3ffc) = (ushort)bVar1;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

