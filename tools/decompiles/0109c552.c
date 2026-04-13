
void FUN_0109c552(undefined2 param_1)

{
  undefined2 in_r17;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  int in_ep;
  undefined2 in_lp;
  
  *(undefined2 *)(in_ep + 0x8c) = param_1;
  *(undefined2 *)(in_ep + 0x8c) = param_1;
  *(undefined2 *)(in_ep + 0x8c) = in_r17;
  *(undefined2 *)(in_r25 + 0x39de) = in_lp;
                    /* WARNING: Could not recover jumptable at 0x0109c580. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

