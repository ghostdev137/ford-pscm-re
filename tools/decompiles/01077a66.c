
void FUN_01077a66(void)

{
  byte bVar1;
  undefined4 in_r13;
  int in_r17;
  undefined1 in_r20;
  undefined4 in_r23;
  int in_ep;
  
  __nop();
  *(undefined4 *)(in_ep + 0x40) = in_r23;
  *(undefined4 *)(in_ep + 0xa0) = 0;
  __nop();
  __nop();
  *(undefined4 *)(in_ep + 0xa8) = 0;
  __nop();
  *(undefined4 *)(in_ep + 0xa8) = in_r13;
  __nop();
  __nop();
  __nop();
  (&DAT_00002855)[*(ushort *)(in_ep + 0xa6)] = in_r20;
  bVar1 = *(byte *)(in_ep + 0x48);
  __nop();
  __nop();
  *(undefined1 *)(bVar1 + 0x77c) = 0;
  *(byte *)(in_ep + 0x62) = bVar1;
                    /* WARNING: Could not recover jumptable at 0x01077af8. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_01077afa + *(short *)(&LAB_01077afa + in_r17 * 2) * 2))(0,0xfffffff9);
  return;
}

