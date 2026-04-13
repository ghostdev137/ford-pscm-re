
void FUN_0109ac76(undefined4 param_1)

{
  int in_r1;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  *(undefined4 *)(&stack0x00000000 + in_ep) = param_1;
                    /* WARNING: Could not recover jumptable at 0x0109aca2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(*(undefined2 *)((int)(&stack0x00000000 + in_ep) + 4),in_r1 + -0xe29);
  return;
}

