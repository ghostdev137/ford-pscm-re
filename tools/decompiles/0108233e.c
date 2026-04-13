
void FUN_0108233e(uint param_1)

{
  undefined1 in_r12;
  uint in_r23;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  uint in_r29;
  ushort *in_ep;
  ushort *in_CTBP;
  
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(param_1 ^ in_r23);
  *(undefined1 *)(in_r25 + 0x200) = in_r12;
  __nop();
                    /* WARNING: Could not recover jumptable at 0x0108236e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(*in_ep,*in_ep & in_r29);
  return;
}

