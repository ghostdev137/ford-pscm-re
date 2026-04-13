
void FUN_010c1da4(void)

{
  undefined2 in_r1;
  undefined1 in_r14;
  int in_r17;
  undefined2 *in_ep;
  ushort *in_CTBP;
  
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  __nop();
  *in_ep = in_r1;
  *(undefined1 *)(in_ep + 0x33) = in_r14;
                    /* WARNING: Could not recover jumptable at 0x010c1d88. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)(ushort)in_ep[1])(in_r17 + 0x40000000);
  return;
}

