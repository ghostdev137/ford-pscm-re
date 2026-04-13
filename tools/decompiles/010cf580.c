
void FUN_010cf580(void)

{
  undefined2 in_r2;
  undefined2 unaff_tp;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  int in_ep;
  undefined4 in_lp;
  
  *(undefined2 *)(in_ep + 0xc4) = unaff_tp;
  *(undefined2 *)(in_ep + 0xc4) = in_r2;
  *(undefined4 *)(in_r25 + -0x6002) = in_lp;
  *(undefined2 *)(in_ep + 0xd0) = 0;
                    /* WARNING: Could not recover jumptable at 0x010cf5b2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(*(undefined2 *)(in_ep + 10));
  return;
}

