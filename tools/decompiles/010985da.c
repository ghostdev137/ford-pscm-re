
/* WARNING: This function may have set the stack pointer */

void FUN_010985da(undefined1 param_1)

{
  undefined1 unaff_gp;
  int in_r17;
  int in_r25;
  code *UNRECOVERED_JUMPTABLE;
  undefined2 *in_ep;
  
  *in_ep = 0;
  *(undefined1 *)(in_r25 + 0x600) = param_1;
  *(undefined1 *)(in_r17 + 0x1000) = unaff_gp;
  __nop();
                    /* WARNING: Could not recover jumptable at 0x01098606. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(in_ep[0x59]);
  return;
}

