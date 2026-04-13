
void FUN_01081a80(void)

{
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  ushort *in_CTBP;
  
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(*(undefined2 *)(in_ep + 0xfa));
                    /* WARNING: Could not recover jumptable at 0x01081ac0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(*(undefined2 *)(in_ep + 0xfa));
  return;
}

